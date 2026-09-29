import json
import os
import sys

TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "plugin", "templates", "param_opt")
sys.path.insert(0, TEMPLATE)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import optimizer  # noqa: E402
import param_opt_init  # noqa: E402

SIM_OK = "import sys\nx = float(sys.argv[1])\nprint('score=%.6f' % ((x - 0.3) ** 2))\n"
SIM_FAIL_LOW = "import sys\nx = float(sys.argv[1])\nif x < 0.5:\n    sys.exit(3)\nprint('score=%.6f' % ((x - 0.3) ** 2))\n"
SIM_CP949 = "import sys" + chr(10) + "sys.stdout.buffer.write('결과 score=0.25'.encode('cp949'))" + chr(10)


def write_config(tmp_path, sim_code, budget=30, workers=1):
    sim = tmp_path / "sim.py"
    sim.write_text(sim_code, encoding="utf-8")
    cfg = {"params": [{"name": "x", "type": "float", "min": 0.0, "max": 1.0, "step": 0.01}],
           "evaluate": {"command": f'"{sys.executable}" "{sim}" {{x}}', "metric_regex": r"score=([0-9.eE+-]+)",
                        "minimize": True, "timeout_seconds": 60},
           "search": {"budget": budget, "workers": workers, "seed": 0, "local_ratio": 0.5}}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return str(path)


def test_validate_reports_missing_fields():
    errs = optimizer.validate({"params": [], "evaluate": {}, "search": {}})
    assert any("params" in e for e in errs) and any("command" in e for e in errs)
    assert optimizer.validate(json.loads(open(os.path.join(TEMPLATE, "config.json"), encoding="utf-8").read())) == []


def test_random_then_local_search_improves_best(tmp_path):
    result = optimizer.run(write_config(tmp_path, SIM_OK, budget=30))
    assert result["evaluated"] == 30 and result["failed"] == 0
    assert abs(result["best"]["point"]["x"] - 0.3) < 0.06
    assert (tmp_path / "best.json").is_file()
    assert (tmp_path / "log.jsonl").read_text(encoding="utf-8").count("\n") == 30


def test_failed_command_is_logged_as_null_and_run_continues(tmp_path):
    result = optimizer.run(write_config(tmp_path, SIM_FAIL_LOW, budget=10))
    assert result["evaluated"] == 10 and result["failed"] >= 1
    assert '"value": null' in (tmp_path / "log.jsonl").read_text(encoding="utf-8")
    assert result["best"]["point"]["x"] >= 0.5


def test_resume_skips_evaluated_points(tmp_path):
    cfg = write_config(tmp_path, SIM_OK, budget=5)
    optimizer.run(cfg)
    result = optimizer.run(cfg, budget=8)
    assert result["resumed"] == 5 and result["evaluated"] == 8
    assert (tmp_path / "log.jsonl").read_text(encoding="utf-8").count("\n") == 8


def test_metric_read_from_cp949_output(tmp_path):
    result = optimizer.run(write_config(tmp_path, SIM_CP949, budget=1))
    assert result["best"]["value"] == 0.25


def test_workers_parallel_gives_same_count(tmp_path):
    result = optimizer.run(write_config(tmp_path, SIM_OK, budget=6, workers=3))
    assert result["evaluated"] == 6 and result["failed"] == 0


def test_init_copies_scaffold_once(tmp_path):
    assert param_opt_init.init(str(tmp_path)) == 3
    assert (tmp_path / "optim" / "optimizer.py").is_file() and (tmp_path / "optim" / "config.json").is_file()
    assert param_opt_init.init(str(tmp_path)) == 0
