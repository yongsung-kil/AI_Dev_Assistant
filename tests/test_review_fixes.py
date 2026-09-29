"""2단계부터 8단계 라이트 리뷰에서 나온 결함의 재현 테스트."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "templates", "param_opt"))
sys.path.insert(0, os.path.dirname(__file__))
import collect_status  # noqa: E402
import idea_init  # noqa: E402
import optimizer  # noqa: E402
import paper_analyze  # noqa: E402
import paper_search  # noqa: E402
import papers_db  # noqa: E402
import pm_init  # noqa: E402
import render_dashboard as rd  # noqa: E402
from test_collect_status import make_project  # noqa: E402


def test_idea_then_dashboard_has_no_broken_links(tmp_path):
    pm_init.main(str(tmp_path))
    idea_init.create(str(tmp_path), "ideas", 1, "a", "s")
    status = collect_status.collect(str(tmp_path))
    assert "ideas/실험로그.md" in [d["path"] for d in status["docs"]]
    rd.render(str(tmp_path), status)
    assert rd.check_links(str(tmp_path)) == []


def test_stale_html_removed_on_rerender(tmp_path):
    make_project(tmp_path)
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    stale = tmp_path / "dashboard" / "docs" / "docs" / "b.html"
    assert stale.is_file()
    (tmp_path / "docs" / "b.md").unlink()
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    assert not stale.exists()


def test_folder_links_are_not_broken(tmp_path):
    make_project(tmp_path)
    (tmp_path / "docs" / "sub").mkdir()
    (tmp_path / "docs" / "c.md").write_text("# c [폴더](sub/) [상위](../_pm/)\n", encoding="utf-8")
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    assert rd.check_links(str(tmp_path)) == []


def test_recent_experiments_keep_file_order_and_skip_placeholder(tmp_path):
    make_project(tmp_path)
    (tmp_path / "docs" / "실험로그.md").write_text(
        "# 실험 로그\n\n## YYYY-MM-DD {아이디어}: {한 줄 결론}\n\n## 2026-09-30 newest\n\n## 2026-09-29 older\n",
        encoding="utf-8")
    status = collect_status.collect(str(tmp_path))
    assert [e["title"] for e in status["experiments"]] == ["2026-09-30 newest", "2026-09-29 older"]
    rd.render(str(tmp_path), status)
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert index.index("2026-09-30 newest") < index.index("2026-09-29 older")


def test_card_without_subtasks_shows_no_progress(tmp_path):
    pm_init.main(str(tmp_path))
    (tmp_path / "_pm" / "TODO.md").write_text("# TODO\n\n## 작업 목록\n\n- [ ] 단독 작업\n\n## 새 작업 추가\n", encoding="utf-8")
    rd.render(str(tmp_path), collect_status.collect(str(tmp_path)))
    index = (tmp_path / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert "하위 단계 없음" in index and "0/0" not in index


def test_optimizer_timeout_kills_process_tree(tmp_path):
    sim = tmp_path / "slow.py"
    sim.write_text("import time\ntime.sleep(8)\nprint('score=1')\n", encoding="utf-8")
    cfg = {"evaluate": {"command": f'"{sys.executable}" "{sim}" {{x}}', "metric_regex": "score=([0-9.]+)",
                        "minimize": True, "timeout_seconds": 1}}
    started = time.time()
    assert optimizer.evaluate(cfg, {"x": 0.1}) is None
    assert time.time() - started < 5


def test_targets_include_expected_path(tmp_path):
    conn = papers_db.connect(str(tmp_path / "papers" / "papers.db"))
    papers_db.insert_paper(conn, {"source": "s", "title": "t", "abstract": "x", "year": 2024, "doi": "10.1/t"})
    conn.execute("UPDATE papers SET status='in'")
    conn.commit()
    t = paper_analyze.targets(conn, str(tmp_path), 5)[0]
    assert t["expected_path"].endswith(paper_analyze.safe_name(t["id"]) + ".pdf") and t["text_path"] is None


def test_import_patent_csv_with_search_url_line(tmp_path):
    p = tmp_path / "patents.csv"
    p.write_text("search URL:,https://patents.google.com/?q=x\n"
                 "id,title,assignee,publication date,result link\n"
                 "US-1-A,Thing,Corp,2021-02-03,https://patents.google.com/patent/US1A\n", encoding="utf-8")
    rows = paper_search.import_csv(str(p), "patent")
    assert len(rows) == 1 and rows[0]["title"] == "Thing" and rows[0]["year"] == 2021
