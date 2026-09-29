import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import doc_check  # noqa: E402


def test_banned_chars_found_only_outside_code(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("규칙 — 나열은 쉼표·괄호\n`코드 — 안`\n```\n울타리 — 안\n```\n", encoding="utf-8")
    rules = [f[2] for f in doc_check.check_file(str(p))]
    assert rules == ["글자", "글자"]


def test_relative_link_resolves_percent_encoding_and_anchor(tmp_path):
    (tmp_path / "새논문.md").write_text("x", encoding="utf-8")
    p = tmp_path / "a.md"
    p.write_text("[a](%EC%83%88%EB%85%BC%EB%AC%B8.md) [b](없음.md#절) [c](https://x.y) [d](#절)\n", encoding="utf-8")
    assert [f[3] for f in doc_check.check_file(str(p))] == ["없는 파일 '없음.md'"]


def test_forbidden_terms_reported(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("이 절차는 hook을 쓴다\n", encoding="utf-8")
    assert [f[3] for f in doc_check.check_file(str(p), terms=["hook"])] == ["금지 낱말 'hook'"]


def test_main_exit_code_and_summary(tmp_path, capsys):
    (tmp_path / "ok.md").write_text("깨끗한 문서\n", encoding="utf-8")
    assert doc_check.main([str(tmp_path)]) == 0
    assert capsys.readouterr().out.strip() == "발견 0건"
    (tmp_path / "bad.md").write_text("줄표 — 있음\n", encoding="utf-8")
    assert doc_check.main([str(tmp_path)]) == 1


import io  # noqa: E402
import json  # noqa: E402
import doc_check_hook  # noqa: E402


def test_hook_reports_findings_for_md_only(tmp_path, monkeypatch, capsys):
    bad = tmp_path / "bad.md"
    bad.write_text("줄표 — 있음\n", encoding="utf-8")
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(bad)}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert doc_check_hook.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert "줄표" in out["hookSpecificOutput"]["additionalContext"]
    py = tmp_path / "x.py"
    py.write_text("s = '—'\n", encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {"file_path": str(py)}})))
    assert doc_check_hook.main() == 0
    assert capsys.readouterr().out == ""


import subprocess  # noqa: E402

HOOK_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts", "doc_check_hook.py")


def test_hook_reads_utf8_stdin_regardless_of_console_encoding(tmp_path):
    folder = tmp_path / "한글폴더"
    folder.mkdir()
    bad = folder / "문서.md"
    bad.write_text("줄표 — 있음\n", encoding="utf-8")
    payload = json.dumps({"tool_input": {"file_path": str(bad)}}, ensure_ascii=False).encode("utf-8")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    env["PYTHONUTF8"] = "0"
    r = subprocess.run([sys.executable, HOOK_SCRIPT], input=payload, capture_output=True, env=env)
    assert r.returncode == 0
    assert "줄표" in r.stdout.decode("utf-8")


def test_check_file_reports_non_utf8_file_as_single_finding(tmp_path):
    p = tmp_path / "cp949.md"
    p.write_bytes("발견 있음\n".encode("cp949"))
    assert [f[2:] for f in doc_check.check_file(str(p))] == [("인코딩", "UTF-8 아님")]


def test_hook_returns_zero_on_non_utf8_file(tmp_path, monkeypatch, capsys):
    p = tmp_path / "cp949.md"
    p.write_bytes("발견\n".encode("cp949"))
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {"file_path": str(p)}})))
    assert doc_check_hook.main() == 0
    assert "인코딩" in capsys.readouterr().out


def test_inline_code_link_is_not_checked(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("규칙 문서는 `[x](없음.md)` 꼴을 인용한다. 진짜 링크 [y](진짜없음.md)\n", encoding="utf-8")
    assert [f[3] for f in doc_check.check_file(str(p))] == ["없는 파일 '진짜없음.md'"]


def test_tilde_and_long_backtick_fences_are_code(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("~~~\n줄표 — 안\n~~~\n````\n```\n줄표 — 안\n```\n````\n본문 — 밖\n", encoding="utf-8")
    assert [f[1] for f in doc_check.check_file(str(p))] == [9]


def test_link_targets_with_title_angle_brackets_and_parentheses(tmp_path):
    (tmp_path / "b.md").write_text("x", encoding="utf-8")
    (tmp_path / "b c.md").write_text("x", encoding="utf-8")
    (tmp_path / "a(1).md").write_text("x", encoding="utf-8")
    p = tmp_path / "a.md"
    p.write_text('[t](b.md "제목") [s](<b c.md>) [p](a(1).md) [m](없음(2).md)\n', encoding="utf-8")
    assert [f[3] for f in doc_check.check_file(str(p))] == ["없는 파일 '없음(2).md'"]


def test_hook_reports_only_character_and_encoding_findings(tmp_path, monkeypatch, capsys):
    p = tmp_path / "a.md"
    p.write_text("[y](없음.md)\n", encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {"file_path": str(p)}})))
    assert doc_check_hook.main() == 0
    assert capsys.readouterr().out == ""


def test_hook_does_not_write_bytecode(tmp_path):
    cache = os.path.join(os.path.dirname(HOOK_SCRIPT), "__pycache__")
    if os.path.isdir(cache):
        for name in os.listdir(cache):
            if name.startswith("doc_check"):
                os.remove(os.path.join(cache, name))
    p = tmp_path / "a.md"
    p.write_text("깨끗\n", encoding="utf-8")
    payload = json.dumps({"tool_input": {"file_path": str(p)}}).encode("utf-8")
    subprocess.run([sys.executable, HOOK_SCRIPT], input=payload, capture_output=True)
    assert not (os.path.isdir(cache) and any(n.startswith("doc_check") for n in os.listdir(cache)))
