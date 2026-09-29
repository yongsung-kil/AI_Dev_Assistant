import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import pm_stamp  # noqa: E402
import pm_init  # noqa: E402

NOW = "2026-09-30 10:00:00"


def test_stamp_replaces_existing_line():
    text = "# TODO\n\n> Claude 마지막 확인: 2026-01-01 00:00:00\n\n## 작업 목록\n"
    out = pm_stamp.stamp(text, NOW)
    assert f"> Claude 마지막 확인: {NOW}" in out and "2026-01-01" not in out


def test_stamp_inserts_after_title_and_keeps_crlf():
    text = "# TODO\r\n\r\n## 작업 목록\r\n"
    out = pm_stamp.stamp(text, NOW)
    assert out.split("\r\n")[1:3] == ["", f"> Claude 마지막 확인: {NOW}"]
    assert "\n" not in out.replace("\r\n", "")


def test_summarize_counts_top_level_open_items_and_new_section():
    text = ("# TODO\n\n## 작업 목록\n\n- [ ] 첫 작업\n  - [ ] 하위\n- [x] 끝난 작업\n\n"
            "## 새 작업 추가\n\n(비어 있음)\n")
    s = pm_stamp.summarize(text)
    assert "미완 작업 1건" in s and "첫 작업" in s and "새 작업 추가" not in s
    s2 = pm_stamp.summarize(text.replace("(비어 있음)", "- 새로 할 일"))
    assert "'새 작업 추가' 절에 1건" in s2


def test_main_is_silent_without_todo_or_with_bad_stdin(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setattr("sys.stdin", io.StringIO("이건 JSON이 아님"))
    assert pm_stamp.main() == 0
    assert capsys.readouterr().out == ""


def test_main_stamps_file_and_prints_context(tmp_path, monkeypatch, capsys):
    (tmp_path / "_pm").mkdir()
    todo = tmp_path / "_pm" / "TODO.md"
    todo.write_text("# TODO\n\n## 작업 목록\n\n- [ ] 첫 작업\n", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
    assert pm_stamp.main() == 0
    out = capsys.readouterr().out
    assert '"hookEventName": "SessionStart"' in out and "첫 작업" in out
    assert "> Claude 마지막 확인: 20" in todo.read_text(encoding="utf-8")


def test_pm_init_copies_templates_once(tmp_path):
    assert pm_init.main(str(tmp_path)) == 0
    assert (tmp_path / "_pm" / "TODO.md").is_file()
    assert (tmp_path / "_pm" / "tasks" / "_template" / "task.md").is_file()
    (tmp_path / "_pm" / "TODO.md").write_text("바뀐 내용", encoding="utf-8")
    assert pm_init.main(str(tmp_path)) == 0
    assert (tmp_path / "_pm" / "TODO.md").read_text(encoding="utf-8") == "바뀐 내용"


import subprocess  # noqa: E402

INIT_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts", "pm_init.py")


def test_pm_init_cli_output_is_utf8_regardless_of_console_encoding(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    env["PYTHONUTF8"] = "0"
    r = subprocess.run([sys.executable, INIT_SCRIPT, str(tmp_path)], capture_output=True, env=env)
    assert r.stdout.decode("utf-8").startswith("_pm 준비: 새로 복사 5개")


STAMP_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts", "pm_stamp.py")


def test_main_returns_zero_and_stays_silent_on_non_utf8_todo(tmp_path, monkeypatch, capsys):
    (tmp_path / "_pm").mkdir()
    (tmp_path / "_pm" / "TODO.md").write_bytes("# TODO\n\n## 작업 목록\n".encode("cp949"))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
    assert pm_stamp.main() == 0
    assert capsys.readouterr().out == ""


def test_main_reads_cwd_from_utf8_stdin_regardless_of_console_encoding(tmp_path):
    project = tmp_path / "한글프로젝트"
    (project / "_pm").mkdir(parents=True)
    todo = project / "_pm" / "TODO.md"
    todo.write_text("# TODO\n\n## 작업 목록\n\n- [ ] 첫 작업\n", encoding="utf-8")
    payload = json.dumps({"cwd": str(project)}, ensure_ascii=False).encode("utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "CLAUDE_PROJECT_DIR")}
    env["PYTHONUTF8"] = "0"
    r = subprocess.run([sys.executable, STAMP_SCRIPT], input=payload, capture_output=True, env=env)
    assert r.returncode == 0
    assert "첫 작업" in r.stdout.decode("utf-8")
    assert "> Claude 마지막 확인: 20" in todo.read_text(encoding="utf-8")
