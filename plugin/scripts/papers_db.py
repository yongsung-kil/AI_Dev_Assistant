"""논문과 특허 메타데이터 db (SQLite 하나). 표: papers, judgments, analysis.

id 규칙: arxiv:{번호} > doi:{DOI} > {출처}:{출처 고유 id} > {출처}:{제목 해시 12자}.
중복: 같은 DOI(대소문자 무시)나 같은 제목(소문자, 기호 제거, 공백 정리)이 있으면 넣지 않는다.
"""
import hashlib
import os
import re
import sqlite3
from datetime import datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
  id TEXT PRIMARY KEY, source TEXT, title TEXT, title_key TEXT, abstract TEXT, year INTEGER, venue TEXT,
  doi TEXT, url TEXT, pdf_url TEXT, status TEXT DEFAULT 'new', added_at TEXT);
CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_title_key ON papers(title_key);
CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(status);
CREATE TABLE IF NOT EXISTS judgments (id TEXT, decision TEXT, reason TEXT, run_dir TEXT, at TEXT);
CREATE TABLE IF NOT EXISTS analysis (id TEXT PRIMARY KEY, json TEXT, md_path TEXT, at TEXT);
"""


def default_db_path(root):
    return os.path.join(os.path.abspath(root), "papers", "papers.db")


def connect(path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def connect_readonly(path):
    """읽기 전용 연결. 스키마를 만들지 않으므로 다른 프로세스가 쓰는 중이어도 열린다 (잠금은 30초까지 기다린다)."""
    uri = "file:" + os.path.abspath(path).replace(os.sep, "/") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_title(title):
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", (title or "").lower())).strip()


def normalize_doi(doi):
    d = (doi or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if d.startswith(prefix):
            d = d[len(prefix):]
    return d


def make_id(row):
    if row.get("arxiv_id"):
        return f"arxiv:{row['arxiv_id']}"
    if row.get("doi"):
        return f"doi:{row['doi'].strip()}"
    if row.get("native_id"):
        return f"{row.get('source', 'other')}:{row['native_id'].strip()}"
    digest = hashlib.sha1(normalize_title(row.get("title")).encode("utf-8")).hexdigest()[:12]
    return f"{row.get('source', 'other')}:{digest}"


def insert_paper(conn, row):
    """중복이 아니면 넣고 True. 중복(같은 DOI, 같은 제목, 같은 id)이면 False."""
    doi = normalize_doi(row.get("doi"))
    key = normalize_title(row.get("title"))
    if doi and conn.execute("SELECT 1 FROM papers WHERE doi=?", (doi,)).fetchone():
        return False
    if key and conn.execute("SELECT 1 FROM papers WHERE title_key=?", (key,)).fetchone():
        return False
    pid = make_id(row)
    if conn.execute("SELECT 1 FROM papers WHERE id=?", (pid,)).fetchone():
        return False
    conn.execute(
        "INSERT INTO papers (id, source, title, title_key, abstract, year, venue, doi, url, pdf_url, status, added_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)",
        (pid, row.get("source", "other"), (row.get("title") or "").strip(), key, (row.get("abstract") or "").strip(),
         row.get("year"), row.get("venue") or "", doi, row.get("url") or "", row.get("pdf_url") or "",
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    return True


def stats(conn):
    total = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    by_status = {r[0]: r[1] for r in conn.execute("SELECT status, COUNT(*) FROM papers GROUP BY status ORDER BY status")}
    return {"total": total, "by_status": by_status, "without_abstract": count_without_abstract(conn)}


def count_without_abstract(conn):
    return conn.execute("SELECT COUNT(*) FROM papers WHERE abstract IS NULL OR abstract=''").fetchone()[0]


def pending_for_screen(conn, limit, year=None):
    """status가 new이고 초록이 있는 논문 (최신 연도부터)."""
    sql = "SELECT * FROM papers WHERE status='new' AND abstract<>''"
    args = []
    if year:
        sql += " AND year=?"
        args.append(year)
    sql += " ORDER BY year DESC, id LIMIT ?"
    args.append(limit)
    return [dict(r) for r in conn.execute(sql, args)]
