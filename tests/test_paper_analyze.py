import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import paper_analyze  # noqa: E402
import papers_db  # noqa: E402


def seed(tmp_path):
    conn = papers_db.connect(str(tmp_path / "papers" / "papers.db"))
    ids = []
    for title in ["alpha", "beta", "gamma"]:
        row = {"source": "s", "title": title, "abstract": "x", "year": 2024, "doi": f"10.1/{title}"}
        papers_db.insert_paper(conn, row)
        ids.append(papers_db.make_id(row))
    conn.execute("UPDATE papers SET status='in' WHERE title IN ('alpha', 'beta')")
    conn.commit()
    return conn, ids


def test_targets_pick_in_without_analysis_and_attach_text_path(tmp_path):
    conn, ids = seed(tmp_path)
    pdfs = tmp_path / "papers" / "pdfs"
    pdfs.mkdir(parents=True)
    (pdfs / (paper_analyze.safe_name(ids[0]) + ".pdf")).write_bytes(b"%PDF")
    targets = paper_analyze.targets(conn, str(tmp_path), limit=10)
    assert [t["id"] for t in targets] == [ids[0], ids[1]]
    assert targets[0]["text_path"].endswith(".pdf") and targets[1]["text_path"] is None


def test_extract_json_block_last_block_and_broken_returns_none():
    md = "text\n```json\n{\"a\": 1}\n```\nmore\n```json\n{\"b\": 2}\n```\n"
    assert paper_analyze.extract_json_block(md) == {"b": 2}
    assert paper_analyze.extract_json_block("```json\n{broken\n```\n") is None
    assert paper_analyze.extract_json_block("no block") is None


def test_apply_records_and_skips_broken(tmp_path):
    conn, ids = seed(tmp_path)
    analysis = tmp_path / "papers" / "analysis"
    analysis.mkdir(parents=True)
    (analysis / "a.md").write_text("# a\n```json\n" + json.dumps({"id": ids[0], "portability": "상", "recommendation": "상",
                                                                     "key_contribution": "k"}) + "\n```\n", encoding="utf-8")
    (analysis / "b.md").write_text("# b\n```json\n{broken\n```\n", encoding="utf-8")
    result = paper_analyze.apply(conn, str(analysis))
    assert result["applied"] == 1 and result["skipped"] == ["b.md"]
    assert conn.execute("SELECT status FROM papers WHERE id=?", (ids[0],)).fetchone()[0] == "analyzed"


def test_catalog_table_sorted_by_portability(tmp_path):
    conn, ids = seed(tmp_path)
    for pid, port in [(ids[0], "하"), (ids[1], "상")]:
        paper_analyze.record(conn, pid, {"id": pid, "portability": port, "recommendation": "중", "key_contribution": "k"}, "x.md")
    out = tmp_path / "papers" / "catalogs" / "analysis.md"
    paper_analyze.catalog(conn, str(out))
    text = out.read_text(encoding="utf-8")
    assert text.index("beta") < text.index("alpha") and "| 이식성 |" in text
