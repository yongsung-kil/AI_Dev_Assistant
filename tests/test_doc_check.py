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
