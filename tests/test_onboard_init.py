import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import onboard_init  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts", "onboard_init.py")


def make_project(root):
    (root / "a").mkdir()
    (root / "a" / "x.py").write_text("print(1)\n", encoding="utf-8")
    (root / "a" / "run.py").write_text("print(2)\n", encoding="utf-8")
    (root / "b").mkdir()
    (root / "b" / "y.cpp").write_text("int main(){}\n", encoding="utf-8")
    (root / "c").mkdir()
    (root / "c" / "top.v").write_text("module top; endmodule\n", encoding="utf-8")
    (root / "README.md").write_text("# p\n", encoding="utf-8")
    (root / "requirements.txt").write_text("numpy\n", encoding="utf-8")
    (root / ".git").mkdir()
    (root / ".git" / "junk.py").write_text("x\n", encoding="utf-8")
    (root / "a" / "__pycache__").mkdir()
    (root / "a" / "__pycache__" / "x.cpython-311.pyc").write_bytes(b"\x00")


def test_scan_counts_languages_entries_builds_and_skips_junk(tmp_path):
    make_project(tmp_path)
    s = onboard_init.scan(str(tmp_path))
    assert s["languages"] == {"cpp": 1, "python": 2, "verilog": 1}
    assert s["top_dirs"] == ["a", "b", "c"]
    assert s["entry_candidates"] == ["a/run.py", "c/top.v"]
    assert s["build_files"] == ["requirements.txt"]
    assert s["readme"] == "README.md"
    assert s["file_count"] == 6


def test_init_docs_copies_templates_once(tmp_path):
    n = onboard_init.init_docs(str(tmp_path))
    assert n >= 8
    assert (tmp_path / "docs" / "profile" / "overview.md").is_file()
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / "docs" / "adr" / "README.md").is_file()
    (tmp_path / "docs" / "profile" / "overview.md").write_text("채움", encoding="utf-8")
    assert onboard_init.init_docs(str(tmp_path)) == 0
    assert (tmp_path / "docs" / "profile" / "overview.md").read_text(encoding="utf-8") == "채움"


def test_cli_prints_utf8_json_with_korean_dirs(tmp_path):
    (tmp_path / "한글폴더").mkdir()
    (tmp_path / "한글폴더" / "m.py").write_text("x\n", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    env["PYTHONUTF8"] = "0"
    r = subprocess.run([sys.executable, SCRIPT, str(tmp_path), "--summary-only"], capture_output=True, env=env)
    data = json.loads(r.stdout.decode("utf-8"))
    assert data["top_dirs"] == ["한글폴더"] and data["languages"] == {"python": 1}
    assert not (tmp_path / "docs").exists()
