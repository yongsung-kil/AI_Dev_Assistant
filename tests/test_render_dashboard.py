import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
sys.path.insert(0, os.path.dirname(__file__))
import collect_status  # noqa: E402
import render_dashboard as rd  # noqa: E402
from test_collect_status import make_project  # noqa: E402


def build(tmp_path):
    make_project(tmp_path)
    status = collect_status.collect(str(tmp_path))
    return rd.render(str(tmp_path), status), status


def test_index_has_cards_for_open_todo_with_progress_and_detail_link(tmp_path):
    build(tmp_path)
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert "첫 작업" in index and "1/3" in index
    assert 'href="docs/_pm/tasks/20260930_first/20260930_first.html"' in index
    assert "결정 대기" in index and "둘째 완료" in index and "아이디어 하나" in index and "실험 2" in index


def test_docs_rendered_with_percent_encoded_hrefs(tmp_path):
    build(tmp_path)
    assert (tmp_path / "dashboard" / "docs" / "docs" / "한글 문서.html").is_file()
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert 'href="docs/docs/%ED%95%9C%EA%B8%80%20%EB%AC%B8%EC%84%9C.html"' in index
    page = (tmp_path / "dashboard" / "docs" / "docs" / "한글 문서.html").read_text(encoding="utf-8")
    assert 'href="b.html"' in page and 'href="https://x.y"' in page


def test_sidebar_groups_and_toc_present(tmp_path):
    build(tmp_path)
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert index.count("<details") >= 5 and "이 페이지의 차례" in index
    page = (tmp_path / "dashboard" / "docs" / "docs" / "실험로그.html").read_text(encoding="utf-8")
    assert 'id="실험-1"' in page and 'href="#실험-1"' in page and "../../assets/style.css" in page


def test_check_links_reports_missing_target_only(tmp_path):
    build(tmp_path)
    assert rd.check_links(str(tmp_path)) == []
    (tmp_path / "dashboard" / "broken.html").write_text('<a href="nope.html">x</a> <a href="#절">y</a>', encoding="utf-8")
    assert rd.check_links(str(tmp_path)) == [("dashboard/broken.html", "nope.html")]


def test_render_is_deterministic_except_generated_line(tmp_path):
    make_project(tmp_path)
    s1 = collect_status.collect(str(tmp_path))
    rd.render(str(tmp_path), s1)
    first = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    s2 = dict(s1, generated="2099-01-01 00:00:00")
    rd.render(str(tmp_path), s2)
    second = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    strip = lambda t: "\n".join(l for l in t.splitlines() if "생성" not in l)  # noqa: E731
    assert strip(first) == strip(second) and first != second


def test_empty_project_renders_empty_dashboard(tmp_path):
    files = rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert "진행 중인 작업 없음" in index and any(f.endswith("index.html") for f in files)


def test_main_returns_zero_without_broken_links(tmp_path):
    make_project(tmp_path)
    assert rd.main([str(tmp_path)]) == 0
    assert (tmp_path / "dashboard" / "status.json").is_file()
