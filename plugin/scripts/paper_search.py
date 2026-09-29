"""논문과 특허 검색과 들여오기.

사용:
  python paper_search.py [--root .] init                          papers/ 폴더, 기준서 양식, db 만들기
  python paper_search.py [--root .] search arxiv "질의" [--max 100] [--since 2023]
  python paper_search.py [--root .] import 파일.csv --source ieee|patent|other   (사이트의 내보내기 CSV)
  python paper_search.py [--root .] stats
arXiv는 공개 API를 부른다. IEEE Xplore와 Google Patents는 브라우저에서 검색해 내보낸 CSV를 들여온다.
"""
import csv
import io
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import papers_db  # noqa: E402

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "papers")
ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
COLUMN_ALIASES = {
    "title": ["documenttitle", "title", "documenttitles"],
    "abstract": ["abstract", "summary"],
    "year": ["publicationyear", "year", "publicationdate", "grantdate", "date"],
    "doi": ["doi"],
    "url": ["resultlink", "url", "link", "documentlink"],
    "pdf_url": ["pdflink", "pdfurl", "pdf"],
    "venue": ["publicationtitle", "journal", "venue", "source"],
    "native_id": ["id", "documentidentifier", "patentnumber", "publicationnumber"],
}


def _clean(text):
    return " ".join((text or "").split())


def parse_arxiv_atom(text):
    root = ET.fromstring(text)
    rows = []
    for entry in root.findall("a:entry", ATOM):
        url = _clean(entry.findtext("a:id", default="", namespaces=ATOM))
        m = re.search(r"/abs/([0-9]+\.[0-9]+|[a-z\-]+/[0-9]+)(v[0-9]+)?$", url)
        if not m:
            continue
        pdf_url = ""
        for link in entry.findall("a:link", ATOM):
            if link.get("title") == "pdf":
                pdf_url = link.get("href", "")
        published = entry.findtext("a:published", default="", namespaces=ATOM)
        rows.append({"id": f"arxiv:{m.group(1)}", "arxiv_id": m.group(1), "source": "arxiv",
                     "title": _clean(entry.findtext("a:title", default="", namespaces=ATOM)),
                     "abstract": _clean(entry.findtext("a:summary", default="", namespaces=ATOM)),
                     "year": int(published[:4]) if published[:4].isdigit() else None,
                     "venue": _clean(entry.findtext("arxiv:journal_ref", default="", namespaces=ATOM)) or "arXiv",
                     "doi": _clean(entry.findtext("arxiv:doi", default="", namespaces=ATOM)),
                     "url": url, "pdf_url": pdf_url})
    return rows


def arxiv_query(query, max_results=100, since_year=None):
    params = {"search_query": f"all:{query}", "start": 0, "max_results": max_results,
              "sortBy": "submittedDate", "sortOrder": "descending"}
    with urlopen("https://export.arxiv.org/api/query?" + urlencode(params), timeout=60) as resp:
        rows = parse_arxiv_atom(resp.read().decode("utf-8"))
    if since_year:
        rows = [r for r in rows if r["year"] and r["year"] >= since_year]
    return rows


def normalize_header(name):
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _pick(record, field):
    for alias in COLUMN_ALIASES[field]:
        if alias in record and record[alias]:
            return record[alias].strip()
    return ""


def _header_start(lines):
    """제목 열 이름이 든 줄을 머리 줄로 본다 (Google Patents 내보내기는 첫 줄이 'search URL:,...'이다)."""
    for idx, line in enumerate(lines[:5]):
        if not line.strip():
            continue
        cells = [normalize_header(c) for c in next(csv.reader([line]))]
        if any(c in COLUMN_ALIASES["title"] for c in cells):
            return idx
    return 0


def import_csv(path, source):
    rows = []
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        lines = f.read().splitlines(keepends=True)
    if True:
        for raw in csv.DictReader(lines[_header_start(lines):]):
            record = {normalize_header(k): (v or "") for k, v in raw.items() if k is not None}
            title = _clean(_pick(record, "title"))
            if not title:
                continue
            year_text = _pick(record, "year")
            year_match = re.search(r"(19|20)[0-9]{2}", year_text)
            rows.append({"source": source, "title": title, "abstract": _clean(_pick(record, "abstract")),
                         "year": int(year_match.group(0)) if year_match else None,
                         "venue": _pick(record, "venue"), "doi": _pick(record, "doi"), "url": _pick(record, "url"),
                         "pdf_url": _pick(record, "pdf_url"), "native_id": _pick(record, "native_id")})
    return rows


def init_papers_dir(root):
    base = os.path.join(os.path.abspath(root), "papers")
    for sub in ("criteria", "pdfs", "analysis", "catalogs", "_work"):
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    copied = 0
    for name, dest in (("README.md", base), ("selection_criteria.md", os.path.join(base, "criteria")),
                       ("categories.md", os.path.join(base, "criteria")), ("analysis_prompt.md", os.path.join(base, "criteria"))):
        target = os.path.join(dest, name)
        if not os.path.exists(target):
            shutil.copyfile(os.path.join(TEMPLATE_DIR, name), target)
            copied += 1
    papers_db.connect(papers_db.default_db_path(root)).close()
    return copied


def insert_rows(conn, rows):
    added = 0
    for row in rows:
        if papers_db.insert_paper(conn, row):
            added += 1
    return added, len(rows) - added


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    root = "."
    if "--root" in argv:
        i = argv.index("--root")
        root = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "init":
        n = init_papers_dir(root)
        print(f"papers/ 준비: 새로 복사 {n}개")
        return 0
    conn = papers_db.connect(papers_db.default_db_path(root))
    if cmd == "stats":
        s = papers_db.stats(conn)
        print(f"전체 {s['total']} | 상태 {s['by_status']} | 초록 없음 {s['without_abstract']}")
        return 0
    if cmd == "search":
        if len(argv) < 3 or argv[1] != "arxiv":
            print("사용법: search arxiv \"질의\" [--max N] [--since 연도]")
            return 2
        max_results = int(argv[argv.index("--max") + 1]) if "--max" in argv else 100
        since = int(argv[argv.index("--since") + 1]) if "--since" in argv else None
        rows = arxiv_query(argv[2], max_results, since)
        added, dup = insert_rows(conn, rows)
        print(f"arxiv 검색 {len(rows)}편: 들여옴 {added} (중복 {dup})")
        return 0
    if cmd == "import":
        if len(argv) < 2:
            print("사용법: import 파일.csv --source ieee|patent|other")
            return 2
        source = argv[argv.index("--source") + 1] if "--source" in argv else "other"
        rows = import_csv(argv[1], source)
        added, dup = insert_rows(conn, rows)
        print(f"{source} CSV {len(rows)}편: 들여옴 {added} (중복 {dup})")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
