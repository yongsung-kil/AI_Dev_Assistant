"""초록 기준 1차 선별의 배치 분할, 판정 검증, 기록.

사용:
  python paper_screen.py [--root .] batch [-n 100] [--per 10] [--year 2024] [--tag A]   -> RUN_DIR=... 에이전트 N개
  python paper_screen.py [--root .] verify RUN_DIR         RUN_DIR/judgments.json 무결성 검사
  python paper_screen.py [--root .] apply RUN_DIR/judgments.json
  python paper_screen.py [--root .] stats
판정 파일 꼴: [{"id": "...", "decision": "in|out", "reason": "한 줄"}]
"""
import io
import json
import os
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import papers_db  # noqa: E402


def make_batches(conn, run_root, n=100, per=10, year=None, tag=None):
    """new이고 초록이 있는 논문을 에이전트별 파일로 나눈다. (run_dir, 에이전트 수)"""
    papers = papers_db.pending_for_screen(conn, n, year)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(os.path.abspath(run_root), f"{tag + '_' if tag else ''}{stamp}")
    os.makedirs(run_dir, exist_ok=True)
    chunks = [papers[i:i + per] for i in range(0, len(papers), per)]
    for idx, chunk in enumerate(chunks):
        items = [{"id": p["id"], "title": p["title"], "year": p["year"], "venue": p["venue"], "abstract": p["abstract"]}
                 for p in chunk]
        with io.open(os.path.join(run_dir, f"agent_{idx:02d}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(items, f, ensure_ascii=False, indent=1)
    with io.open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"ids": [p["id"] for p in papers], "n_agents": len(chunks)}, f, ensure_ascii=False, indent=1)
    return run_dir, len(chunks)


def _load_judgments(path):
    with io.open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "judgments" in data:
        data = data["judgments"]
    return data


def verify(conn, run_dir):
    """judgments.json을 검사한다. errors가 비어 있어야 기록할 수 있다."""
    path = os.path.join(run_dir, "judgments.json")
    if not os.path.isfile(path):
        return {"ok": False, "errors": [f"판정 파일 없음: {path}"], "warnings": [], "counts": {}}
    try:
        judgments = _load_judgments(path)
    except ValueError as e:
        return {"ok": False, "errors": [f"JSON 오류: {e}"], "warnings": [], "counts": {}}
    manifest_path = os.path.join(run_dir, "manifest.json")
    if not os.path.isfile(manifest_path):
        return {"ok": False, "errors": [f"배치 목록 없음: {manifest_path} (batch 명령이 만든 폴더인지 확인)"], "warnings": [], "counts": {}}
    with io.open(manifest_path, encoding="utf-8") as f:
        batch_ids = set(json.load(f)["ids"])
    errors, seen, counts = [], set(), {"in": 0, "out": 0}
    for j in judgments:
        if not isinstance(j, dict):
            errors.append(f"판정 항목이 객체가 아님: {j!r}")
            continue
        pid, decision = j.get("id"), j.get("decision")
        if pid in seen:
            errors.append(f"중복 id: {pid}")
        seen.add(pid)
        if not conn.execute("SELECT 1 FROM papers WHERE id=?", (pid,)).fetchone():
            errors.append(f"없는 id: {pid}")
        elif pid not in batch_ids:
            errors.append(f"배치 밖 id: {pid}")
        if decision not in ("in", "out"):
            errors.append(f"decision 값 오류 ({pid}): {decision}")
        else:
            counts[decision] += 1
    missing = batch_ids - seen
    warnings = [f"누락 {len(missing)}건 (다음 배치에서 다시 나온다)"] if missing else []
    return {"ok": not errors, "errors": errors, "warnings": warnings, "counts": counts}


def apply(conn, judgments_path, run_dir):
    judgments = _load_judgments(judgments_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    counts, done = {"in": 0, "out": 0}, set()
    for j in judgments:
        pid, decision = j.get("id"), j.get("decision")
        if pid in done or decision not in ("in", "out"):
            continue
        done.add(pid)
        cur = conn.execute("UPDATE papers SET status=? WHERE id=? AND status='new'", (decision, pid))
        if cur.rowcount:
            conn.execute("INSERT INTO judgments (id, decision, reason, run_dir, at) VALUES (?, ?, ?, ?, ?)",
                         (pid, decision, j.get("reason", ""), run_dir, now))
            counts[decision] += 1
    conn.commit()
    return counts


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
    if cmd == "batch":
        n = int(argv[argv.index("-n") + 1]) if "-n" in argv else 100
        per = int(argv[argv.index("--per") + 1]) if "--per" in argv else 10
        year = int(argv[argv.index("--year") + 1]) if "--year" in argv else None
        tag = argv[argv.index("--tag") + 1] if "--tag" in argv else None
        run_dir, agents = make_batches(conn, os.path.join(root, "papers", "_work"), n, per, year, tag)
        print(f"RUN_DIR={run_dir}")
        print(f"에이전트 {agents}개 (논문 {sum(1 for _ in papers_db.pending_for_screen(conn, n, year))}편)")
        return 0
    if cmd == "verify":
        result = verify(conn, argv[1])
        for e in result["errors"]:
            print(f"오류: {e}")
        for w in result["warnings"]:
            print(f"경고: {w}")
        print(f"{'통과' if result['ok'] else '실패'} | in {result['counts'].get('in', 0)} out {result['counts'].get('out', 0)}")
        return 0 if result["ok"] else 1
    if cmd == "apply":
        counts = apply(conn, argv[1], os.path.dirname(os.path.abspath(argv[1])))
        print(f"기록: in {counts['in']} out {counts['out']}")
        return 0
    if cmd == "stats":
        s = papers_db.stats(conn)
        print(f"전체 {s['total']} | 상태 {s['by_status']} | 초록 없음 {s['without_abstract']}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
