import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import idea_init  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts", "idea_init.py")


def test_create_folder_readme_and_table_row(tmp_path):
    r = idea_init.create(str(tmp_path), "ideas", 1, "dual_clip", "논문 x")
    folder = tmp_path / "ideas" / "001_dual_clip"
    assert folder.is_dir() and (folder / "README.md").is_file()
    readme = (folder / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# dual_clip") and "논문 x" in readme
    table = (tmp_path / "ideas" / "README.md").read_text(encoding="utf-8")
    assert "| 1 | dual_clip | 논문 x | 대기 | `001_dual_clip/` |" in table
    assert (tmp_path / "ideas" / "실험로그.md").is_file()
    assert r["row_added"] is True


def test_same_number_not_added_twice(tmp_path):
    idea_init.create(str(tmp_path), "ideas", 1, "a", "s")
    r = idea_init.create(str(tmp_path), "ideas", 1, "a", "s")
    table = (tmp_path / "ideas" / "README.md").read_text(encoding="utf-8")
    assert table.count("| 1 |") == 1 and r["row_added"] is False


def test_cli_korean_name(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    env["PYTHONUTF8"] = "0"
    r = subprocess.run([sys.executable, SCRIPT, "--root", str(tmp_path), "--dir", "ideas", "2", "동적정규화", "제안"],
                       capture_output=True, env=env)
    assert r.returncode == 0
    assert (tmp_path / "ideas" / "002_동적정규화" / "README.md").is_file()
    assert "동적정규화" in r.stdout.decode("utf-8")
