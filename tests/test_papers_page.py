"""논문 탐색기 페이지: papers/papers.db가 있을 때만 dashboard/papers.html과 assets/papers.js를 만든다."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
sys.path.insert(0, os.path.dirname(__file__))
import collect_status  # noqa: E402
import paper_analyze  # noqa: E402
import papers_db  # noqa: E402
import render_dashboard as rd  # noqa: E402
from test_collect_status import make_project  # noqa: E402


def make_papers(root):
    conn = papers_db.connect(papers_db.default_db_path(str(root)))
    papers_db.insert_paper(conn, {"source": "arxiv", "arxiv_id": "2601.00001", "title": "First paper", "abstract": "about decoding",
                                  "year": 2026, "venue": "arXiv", "url": "https://arxiv.org/abs/2601.00001"})
    papers_db.insert_paper(conn, {"source": "patent", "native_id": "US1", "title": "Second patent", "abstract": "", "year": 2024, "venue": "USPTO"})
    conn.execute("UPDATE papers SET status='in' WHERE id='arxiv:2601.00001'")
    (root / "papers" / "analysis").mkdir(parents=True, exist_ok=True)
    (root / "papers" / "analysis" / "arxiv_2601.00001.md").write_text("# First paper 분석\n\n## 핵심\n내용\n", encoding="utf-8")
    paper_analyze.record(conn, "arxiv:2601.00001",
                         {"portability": "상", "target": "cnu", "key_contribution": "빠른 갱신 규칙", "complexity": "O(n)"},
                         "papers/analysis/arxiv_2601.00001.md")
    conn.commit()
    conn.close()


def find(nodes, label):
    return next(n for n in nodes if n["label"] == label)


def test_status_has_papers_summary(tmp_path):
    make_project(tmp_path)
    make_papers(tmp_path)
    s = collect_status.collect(str(tmp_path))
    assert s["papers"]["total"] == 2 and s["papers"]["by_status"] == {"analyzed": 1, "new": 1}
    assert s["papers"]["sources"] == ["arxiv", "patent"] and s["papers"]["analyzed"] == 1


def test_papers_page_lists_entries_facets_and_analysis_links(tmp_path):
    make_project(tmp_path)
    make_papers(tmp_path)
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    page = (tmp_path / "dashboard" / "papers.html").read_text(encoding="utf-8")
    assert 'id="paper-search"' in page and 'id="year-min"' in page and 'id="year-max"' in page
    assert 'data-facet="source"' in page and 'data-facet="status"' in page and 'data-facet="portability"' in page
    assert 'data-facet="key_contribution"' not in page  # 자유 글은 갈래가 아니다
    assert '<h2 id="검색-도구">검색 도구</h2>' in page and 'style="--fc: var(--c1)"' in page and 'PAPER_FACET_COLORS' in page
    data = (tmp_path / "dashboard" / "assets" / "papers.js").read_text(encoding="utf-8")
    rows = json.loads(data.split("=", 1)[1].strip().rstrip(";"))
    first = next(r for r in rows if r["id"] == "arxiv:2601.00001")
    assert first["doc"] == "docs/papers/analysis/arxiv_2601.00001.html" and first["facets"]["portability"] == "상"
    assert first["desc"] == "빠른 갱신 규칙" and first["year"] == 2026 and first["url"] == "https://arxiv.org/abs/2601.00001"
    second = next(r for r in rows if r["id"].startswith("patent:"))
    assert second["doc"] is None and second["facets"]["source"] == "patent"
    assert rd.check_links(str(tmp_path)) == []


def test_sidebar_has_explorer_nodes_and_patent_entry(tmp_path):
    make_project(tmp_path)
    make_papers(tmp_path)
    status = collect_status.collect(str(tmp_path))
    nav = rd.build_nav(status, collect_status.load_config(str(tmp_path)))
    group = find(nav, "외부 기술문서")
    assert [c["label"] for c in group["children"][:2]] == ["논문 탐색기", "특허 탐색기"]
    assert group["children"][0]["target"] == "papers.html" and group["children"][1]["anchor"] == "source=patent"
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8") if False else None
    rd.render(str(tmp_path), status)
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert 'href="papers.html"' in index and 'href="papers.html#source=patent"' in index


def test_without_papers_db_no_page_and_no_explorer(tmp_path):
    make_project(tmp_path)
    status = collect_status.collect(str(tmp_path))
    rd.render(str(tmp_path), status)
    assert not (tmp_path / "dashboard" / "papers.html").exists() and status["papers"]["total"] == 0
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert "논문 탐색기" not in index


def test_analysis_docs_use_light_frame_and_stay_out_of_search_body(tmp_path):
    make_project(tmp_path)
    make_papers(tmp_path)
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    page = (tmp_path / "dashboard" / "docs" / "papers" / "analysis" / "arxiv_2601.00001.html").read_text(encoding="utf-8")
    assert '<nav class="sidebar">' not in page and 'href="../../../papers.html"' in page and "First paper 분석" in page
    search = (tmp_path / "dashboard" / "assets" / "search.js").read_text(encoding="utf-8")
    entry = next(e for e in json.loads(search.split("=", 1)[1].strip().rstrip(";")) if "arxiv_2601.00001" in e["path"])
    assert entry["text"] == ""


def test_big_folders_are_capped_in_sidebar(tmp_path):
    make_project(tmp_path)
    (tmp_path / "_wiki" / "tech").mkdir(parents=True)
    for i in range(45):
        (tmp_path / "_wiki" / "tech" / f"2026_{i:02d}.md").write_text(f"# 문서 {i:02d}\n", encoding="utf-8")
    status = collect_status.collect(str(tmp_path))
    nav = rd.build_nav(status, collect_status.load_config(str(tmp_path)))
    tech = find(find(nav, "내부 기술문서")["children"], "기술")
    assert len(tech["children"]) == rd.MAX_FOLDER_ITEMS + 1
    assert tech["children"][-1]["label"] == "외 5편 (검색으로 찾기)" and tech["children"][-1]["target"] is None

def test_facet_labels_from_config(tmp_path):
    make_project(tmp_path)
    make_papers(tmp_path)
    (tmp_path / "dashboard").mkdir(exist_ok=True)
    (tmp_path / "dashboard" / "config.json").write_text('{"facet_labels": {"portability": "이식성"}}', encoding="utf-8")
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    page = (tmp_path / "dashboard" / "papers.html").read_text(encoding="utf-8")
    assert "<legend>이식성</legend>" in page and "<legend>출처</legend>" in page

def test_analysis_docs_without_db_use_normal_frame_and_no_explorer_links(tmp_path):
    make_project(tmp_path)
    (tmp_path / "papers" / "analysis").mkdir(parents=True)
    (tmp_path / "papers" / "analysis" / "x.md").write_text("# 분석 x" + chr(10), encoding="utf-8")
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    page = (tmp_path / "dashboard" / "docs" / "papers" / "analysis" / "x.html").read_text(encoding="utf-8")
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert '<nav class="sidebar">' in page and "papers.html" not in index and rd.check_links(str(tmp_path)) == []
