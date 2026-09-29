"""전문 분석의 대상 목록, 분석 md의 JSON 기록, 카탈로그.

사용:
  python paper_analyze.py [--root .] list [-n 10]     status가 in이고 분석이 없는 논문과 전문 파일 위치
  python paper_analyze.py [--root .] apply            papers/analysis/*.md 의 마지막 json 블록을 db에 기록
  python paper_analyze.py [--root .] catalog          papers/catalogs/analysis.md 생성
"""
import io
import json
import os
import re
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import papers_db  # noqa: E402

JSON_BLOCK = re.compile(r"```json\s*\n(.*?)```", re.S)
PORT_ORDER = {"상": 0, "중": 1, "하": 2}


def safe_name(pid):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", pid)


def targets(conn, root, limit=10):
    """status가 in이고 analysis가 없는 논문. 전문 파일이 있으면 text_path를 붙인다."""
    pdf_dir = os.path.join(os.path.abspath(root), "papers", "pdfs")
    rows = conn.execute(
        "SELECT p.* FROM papers p LEFT JOIN analysis a ON a.id = p.id"
        " WHERE p.status='in' AND a.id IS NULL ORDER BY p.year DESC, p.id LIMIT ?", (limit,))
    out = []
    for r in rows:
        item = {"id": r["id"], "title": r["title"], "year": r["year"], "venue": r["venue"], "url": r["url"],
                "pdf_url": r["pdf_url"], "text_path": None,
                "expected_path": os.path.join(pdf_dir, safe_name(r["id"]) + ".pdf")}
        for ext in (".pdf", ".txt"):
            candidate = os.path.join(pdf_dir, safe_name(r["id"]) + ext)
            if os.path.isfile(candidate):
                item["text_path"] = candidate
                break
        out.append(item)
    return out


def extract_json_block(md_text):
    blocks = JSON_BLOCK.findall(md_text)
    if not blocks:
        return None
    try:
        data = json.loads(blocks[-1])
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def record(conn, pid, data, md_path):
    conn.execute("INSERT OR REPLACE INTO analysis (id, json, md_path, at) VALUES (?, ?, ?, ?)",
                 (pid, json.dumps(data, ensure_ascii=False), md_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.execute("UPDATE papers SET status='analyzed' WHERE id=?", (pid,))
    conn.commit()


def apply(conn, analysis_dir):
    applied, skipped = 0, []
    for name in sorted(os.listdir(analysis_dir)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(analysis_dir, name)
        with io.open(path, encoding="utf-8", errors="replace") as f:
            data = extract_json_block(f.read())
        if not data or not data.get("id"):
            skipped.append(name)
            continue
        if not conn.execute("SELECT 1 FROM papers WHERE id=?", (data["id"],)).fetchone():
            skipped.append(name)
            continue
        record(conn, data["id"], data, path)
        applied += 1
    return {"applied": applied, "skipped": skipped}


def catalog(conn, out_path):
    rows = []
    for r in conn.execute("SELECT a.id, a.json, a.md_path, p.title, p.year FROM analysis a JOIN papers p ON p.id = a.id"):
        try:
            data = json.loads(r["json"])
        except ValueError:
            data = {}
        rows.append((r["id"], r["title"], r["year"], data, r["md_path"]))
    rows.sort(key=lambda x: (PORT_ORDER.get(x[3].get("portability"), 9), PORT_ORDER.get(x[3].get("recommendation"), 9),
                             -(x[2] or 0), x[0]))
    lines = ["# 전문 분석 카탈로그", "", f"분석 {len(rows)}편. 이식성과 추천도 순.", "",
             "| id | 제목 | 연도 | 이식성 | 대상 부품 | 추천도 | 핵심기여 | 분석 |", "|---|---|---|---|---|---|---|---|"]
    for pid, title, year, data, md_path in rows:
        link = f"[md](../analysis/{os.path.basename(md_path)})" if md_path else ""
        lines.append(f"| {pid} | {title} | {year or ''} | {data.get('portability', '')} | {data.get('target', '')} | "
                     f"{data.get('recommendation', '')} | {data.get('key_contribution', '')} | {link} |")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return len(rows)


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
    conn = papers_db.connect(papers_db.default_db_path(root))
    cmd = argv[0]
    if cmd == "list":
        n = int(argv[argv.index("-n") + 1]) if "-n" in argv else 10
        items = targets(conn, root, n)
        print(json.dumps(items, ensure_ascii=False, indent=1))
        print(f"대상 {len(items)}편 (전문 있음 {sum(1 for i in items if i['text_path'])})")
        return 0
    if cmd == "apply":
        result = apply(conn, os.path.join(root, "papers", "analysis"))
        print(f"기록 {result['applied']}편, 건너뜀 {len(result['skipped'])}: {', '.join(result['skipped'])}")
        return 0
    if cmd == "catalog":
        n = catalog(conn, os.path.join(root, "papers", "catalogs", "analysis.md"))
        print(f"카탈로그 {n}편: papers/catalogs/analysis.md")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
