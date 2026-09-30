"""사이드바 묶음(config 기반 트리), 첫 화면 보드, 변경 이력 페이지."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
sys.path.insert(0, os.path.dirname(__file__))
import collect_status  # noqa: E402
import render_dashboard as rd  # noqa: E402
from test_collect_status import make_project  # noqa: E402


def make_wide_project(root):
    make_project(root)
    (root / "docs" / "profile").mkdir()
    (root / "docs" / "profile" / "overview.md").write_text("# 개요\n", encoding="utf-8")
    (root / "_wiki" / "tech").mkdir(parents=True)
    (root / "_wiki" / "manual.md").write_text("# 매뉴얼\n", encoding="utf-8")
    (root / "_wiki" / "tech" / "20260930_x.md").write_text("# 기술 x\n", encoding="utf-8")
    (root / "ideas" / "001_a").mkdir(parents=True)
    (root / "ideas" / "README.md").write_text("# 아이디어 현황\n", encoding="utf-8")
    (root / "ideas" / "001_a" / "README.md").write_text("# 아이디어 a\n", encoding="utf-8")
    (root / "papers").mkdir()
    (root / "papers" / "README.md").write_text("# 논문 조사\n", encoding="utf-8")
    (root / "docs" / "speed_opt").mkdir()
    (root / "docs" / "speed_opt" / "checklist.md").write_text("# 점검표\n", encoding="utf-8")


def find(nodes, label):
    return next(n for n in nodes if n["label"] == label)


def test_nav_groups_follow_default_order_and_nest_folders(tmp_path):
    make_wide_project(tmp_path)
    status = collect_status.collect(str(tmp_path))
    nav = rd.build_nav(status, collect_status.load_config(str(tmp_path)))
    labels = [g["label"] for g in nav]
    assert labels == ["온보딩", "작업 관리", "외부 기술문서", "아이디어 적용", "최적화", "내부 기술문서", "기타 문서"]
    profile = find(find(nav, "온보딩")["children"], "프로파일")
    assert profile["children"][0]["target"] == "docs/docs/profile/overview.html"
    pm = find(nav, "작업 관리")["children"]
    assert [c["label"] for c in pm[:2]] == ["TODO", "DONE"]
    first = find(find(pm, "진행 중 작업")["children"], "첫 작업")
    assert first["target"] == "docs/_pm/tasks/20260930_first/20260930_first.html"
    tech = find(find(nav, "내부 기술문서")["children"], "기술")
    assert tech["children"][0]["label"] == "기술 x"
    assert find(find(nav, "아이디어 적용")["children"], "아이디어 a")["target"] == "docs/ideas/001_a/README.html"
    other = find(nav, "기타 문서")["children"]
    assert find(other, "docs")["children"][0]["label"] == "비"


def test_nav_marks_pending_decisions_with_badge(tmp_path):
    make_project(tmp_path)
    status = collect_status.collect(str(tmp_path))
    nav = rd.build_nav(status, collect_status.load_config(str(tmp_path)))
    task = find(find(find(nav, "작업 관리")["children"], "진행 중 작업")["children"], "첫 작업")
    decision = find(task["children"], "판정요청: x")
    assert decision["badge"] == "미답 1"


def test_nav_uses_config_sidebar_when_given(tmp_path):
    make_project(tmp_path)
    (tmp_path / "dashboard").mkdir()
    (tmp_path / "dashboard" / "config.json").write_text(
        '{"sidebar": [{"name": "실험", "paths": ["docs"]}, {"name": "관리", "paths": ["_pm", "README.md"]}]}', encoding="utf-8")
    status = collect_status.collect(str(tmp_path))
    nav = rd.build_nav(status, collect_status.load_config(str(tmp_path)))
    assert [g["label"] for g in nav] == ["실험", "관리"]
    assert [c["label"] for c in find(nav, "실험")["children"]] == ["비", "실험로그", "한글 제목"]


def test_sidebar_html_has_levels_changelog_link_and_toggles(tmp_path):
    make_wide_project(tmp_path)
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert 'class="nav-l1"' in index and 'class="nav-l2"' in index and 'class="nav-l3"' in index
    assert 'href="changelog.html"' in index and 'id="nav-toggle"' in index and 'id="theme-toggle"' in index
    assert 'assets/search.js' in index  # 전역 검색 색인은 모든 보통 페이지가 싣는다
    page = (tmp_path / "dashboard" / "docs" / "_wiki" / "tech" / "20260930_x.html").read_text(encoding="utf-8")
    assert 'href="../../../changelog.html"' in page and 'href="20260930_x.html"' in page


def test_index_board_has_three_columns_and_review_rows(tmp_path):
    make_project(tmp_path)
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert index.count('class="col-head"') == 3
    doing = index.split('class="col col-doing"')[1].split('class="col col-done"')[0]
    assert "첫 작업" in doing and "1/3" in doing
    done = index.split('class="col col-done"')[1]
    assert "둘째 완료" in done and "2026-09-29" in done
    assert 'class="review"' in index and "미답 1" in index


def test_changelog_page_lists_done_entries_with_range_and_month_tabs(tmp_path):
    make_project(tmp_path)
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    page = (tmp_path / "dashboard" / "changelog.html").read_text(encoding="utf-8")
    assert '<select id="range-from"' in page and '<option value="2026-09-28"' in page
    assert 'data-month="2026-09"' in page and 'data-date="2026-09-29"' in page
    assert "둘째 완료" in page and "요약 둘" in page and "배경" in page
    assert rd.check_links(str(tmp_path)) == []


def test_default_doc_dirs_include_ideas_papers_optim(tmp_path):
    make_wide_project(tmp_path)
    (tmp_path / "optim").mkdir()
    (tmp_path / "optim" / "README.md").write_text("# 최적화기\n", encoding="utf-8")
    paths = {d["path"] for d in collect_status.collect(str(tmp_path))["docs"]}
    assert {"ideas/README.md", "papers/README.md", "optim/README.md"} <= paths


def test_folder_representative_prefers_folder_named_doc_over_readme(tmp_path):
    make_project(tmp_path)
    (tmp_path / "_pm" / "tasks" / "20260930_first" / "README.md").write_text("# 읽어보기" + chr(10), encoding="utf-8")
    status = collect_status.collect(str(tmp_path))
    nav = rd.build_nav(status, collect_status.load_config(str(tmp_path)))
    task = find(find(find(nav, "작업 관리")["children"], "진행 중 작업")["children"], "첫 작업")
    assert task["target"].endswith("20260930_first.html")
    assert [c["label"] for c in task["children"]] == ["읽어보기", "판정요청: x"]


def test_moc_rule_matches_only_moc_files(tmp_path):
    make_project(tmp_path)
    (tmp_path / "_wiki" / "tech").mkdir(parents=True)
    (tmp_path / "_wiki" / "tech" / "MOCK_data.md").write_text("# 가짜 자료" + chr(10), encoding="utf-8")
    (tmp_path / "_wiki" / "tech" / "MOC-tech.md").write_text("# 기술 문서 목록" + chr(10), encoding="utf-8")
    status = collect_status.collect(str(tmp_path))
    nav = rd.build_nav(status, collect_status.load_config(str(tmp_path)))
    tech = find(find(nav, "내부 기술문서")["children"], "기술")
    assert tech["target"].endswith("MOC-tech.html") and [c["label"] for c in tech["children"]] == ["가짜 자료"]


def test_same_basename_folders_stay_separate(tmp_path):
    make_project(tmp_path)
    for top in ("a", "b"):
        (tmp_path / top / "x").mkdir(parents=True)
        (tmp_path / top / "x" / "doc.md").write_text("# " + top + " 문서" + chr(10), encoding="utf-8")
    (tmp_path / "dashboard").mkdir()
    (tmp_path / "dashboard" / "config.json").write_text(
        '{"doc_dirs": ["a", "b"], "sidebar": [{"name": "둘", "paths": ["a/x", "b/x"]}]}', encoding="utf-8")
    status = collect_status.collect(str(tmp_path))
    nav = rd.build_nav(status, collect_status.load_config(str(tmp_path)))
    both = find(nav, "둘")["children"]
    assert [c["label"] for c in both] == ["a/x", "b/x"]
    assert [c["children"][0]["label"] for c in both] == ["a 문서", "b 문서"]


def test_changelog_details_render_bold_labels(tmp_path):
    make_project(tmp_path)
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    page = (tmp_path / "dashboard" / "changelog.html").read_text(encoding="utf-8")
    assert "<li><strong>배경</strong>: b</li>" in page

def test_onboarding_group_lists_usage_guide_first(tmp_path):
    make_project(tmp_path)
    (tmp_path / "docs" / "usage.md").write_text("# 이 프로젝트에서 플러그인 쓰는 법" + chr(10), encoding="utf-8")
    nav = rd.build_nav(collect_status.collect(str(tmp_path)), collect_status.load_config(str(tmp_path)))
    assert find(nav, "온보딩")["children"][0]["label"] == "이 프로젝트에서 플러그인 쓰는 법"
