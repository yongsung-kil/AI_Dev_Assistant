import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import papers_db  # noqa: E402


def test_insert_dedupes_by_doi_and_title(tmp_path):
    conn = papers_db.connect(str(tmp_path / "p.db"))
    assert papers_db.insert_paper(conn, {"source": "ieee", "title": "A Fast Decoder", "abstract": "x", "year": 2024,
                                         "doi": "10.1/abc"}) is True
    assert papers_db.insert_paper(conn, {"source": "arxiv", "title": "A fast  decoder", "abstract": "y", "year": 2024,
                                         "doi": "10.1/ABC"}) is False
    assert papers_db.insert_paper(conn, {"source": "arxiv", "title": "a FAST decoder", "abstract": "y", "year": 2024}) is False
    assert papers_db.insert_paper(conn, {"source": "arxiv", "title": "Other", "abstract": "", "year": 2023}) is True
    assert papers_db.stats(conn) == {"total": 2, "by_status": {"new": 2}, "without_abstract": 1}


def test_make_id_prefers_arxiv_then_doi_then_hash():
    assert papers_db.make_id({"source": "arxiv", "arxiv_id": "2301.00001", "title": "t"}) == "arxiv:2301.00001"
    assert papers_db.make_id({"source": "ieee", "doi": "10.1109/X.2024.1", "title": "t"}) == "doi:10.1109/X.2024.1"
    h = papers_db.make_id({"source": "patent", "title": "Some Title"})
    assert h.startswith("patent:") and len(h) == len("patent:") + 12


def test_pending_for_screen_filters_new_with_abstract_and_year(tmp_path):
    conn = papers_db.connect(str(tmp_path / "p.db"))
    papers_db.insert_paper(conn, {"source": "a", "title": "one", "abstract": "x", "year": 2024})
    papers_db.insert_paper(conn, {"source": "a", "title": "two", "abstract": "", "year": 2024})
    papers_db.insert_paper(conn, {"source": "a", "title": "three", "abstract": "x", "year": 2022})
    assert [p["title"] for p in papers_db.pending_for_screen(conn, 10)] == ["one", "three"]
    assert [p["title"] for p in papers_db.pending_for_screen(conn, 10, year=2022)] == ["three"]
    assert papers_db.count_without_abstract(conn) == 1
