import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import paper_screen  # noqa: E402
import papers_db  # noqa: E402


def seed(tmp_path):
    conn = papers_db.connect(str(tmp_path / "papers.db"))
    ids = []
    for title, abstract, year in [("one", "a", 2024), ("two", "b", 2023), ("three", "c", 2024), ("four", "", 2024)]:
        row = {"source": "s", "title": title, "abstract": abstract, "year": year}
        papers_db.insert_paper(conn, row)
        ids.append(papers_db.make_id(row))
    conn.execute("UPDATE papers SET status='in' WHERE title='three'")
    conn.commit()
    return conn, ids


def test_batches_split_only_new_with_abstract(tmp_path):
    conn, ids = seed(tmp_path)
    run_dir, n = paper_screen.make_batches(conn, str(tmp_path / "_work"), n=10, per=1)
    assert n == 2 and os.path.isdir(run_dir)
    files = sorted(f for f in os.listdir(run_dir) if f.startswith("agent_"))
    assert files == ["agent_00.json", "agent_01.json"]
    got = [json.loads(open(os.path.join(run_dir, f), encoding="utf-8").read())[0]["id"] for f in files]
    assert set(got) == {ids[0], ids[1]}


def test_verify_catches_unknown_duplicate_and_bad_decision(tmp_path):
    conn, ids = seed(tmp_path)
    run_dir, _n = paper_screen.make_batches(conn, str(tmp_path / "_work"), n=10, per=10)
    judgments = [{"id": ids[0], "decision": "in", "reason": "r"}, {"id": ids[0], "decision": "out", "reason": "dup"},
                 {"id": "nope", "decision": "in", "reason": ""}, {"id": ids[1], "decision": "maybe", "reason": ""}]
    with open(os.path.join(run_dir, "judgments.json"), "w", encoding="utf-8") as f:
        json.dump(judgments, f, ensure_ascii=False)
    result = paper_screen.verify(conn, run_dir)
    text = " ".join(result["errors"])
    assert "없는 id" in text and "중복" in text and "decision" in text
    assert result["ok"] is False


def test_apply_updates_status_and_records_reason(tmp_path):
    conn, ids = seed(tmp_path)
    run_dir, _n = paper_screen.make_batches(conn, str(tmp_path / "_work"), n=10, per=10)
    path = os.path.join(run_dir, "judgments.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump([{"id": ids[0], "decision": "in", "reason": "good"}, {"id": ids[1], "decision": "out", "reason": "bad"}], f)
    assert paper_screen.verify(conn, run_dir)["ok"] is True
    result = paper_screen.apply(conn, path, run_dir)
    assert result == {"in": 1, "out": 1}
    assert papers_db.stats(conn)["by_status"] == {"in": 2, "new": 1, "out": 1}
    assert conn.execute("SELECT reason FROM judgments WHERE id=?", (ids[1],)).fetchone()[0] == "bad"
