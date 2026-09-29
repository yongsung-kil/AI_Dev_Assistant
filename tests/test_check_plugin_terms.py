import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_checks"))
import check_plugin_terms  # noqa: E402


def test_scan_is_case_insensitive_and_skips_results(tmp_path):
    (tmp_path / "a.md").write_text("여기에 Ldpc 가 있다\n", encoding="utf-8")
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "r.md").write_text("LDPC\n", encoding="utf-8")
    hits = check_plugin_terms.scan(str(tmp_path), ["LDPC"])
    assert [(os.path.basename(h[0]), h[1], h[2]) for h in hits] == [("a.md", 1, "LDPC")]


def test_main_exit_codes(tmp_path, capsys):
    terms = tmp_path / "terms.txt"
    terms.write_text("# 주석\nLDPC\n", encoding="utf-8")
    root = tmp_path / "plugin"
    root.mkdir()
    (root / "ok.md").write_text("깨끗함\n", encoding="utf-8")
    assert check_plugin_terms.main([str(root), str(terms)]) == 0
    (root / "bad.md").write_text("ldpc\n", encoding="utf-8")
    assert check_plugin_terms.main([str(root), str(terms)]) == 1
    assert check_plugin_terms.main([str(root), str(tmp_path / "없음.txt")]) == 2
