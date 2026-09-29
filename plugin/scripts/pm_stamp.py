"""세션 시작 자동 실행: 프로젝트의 _pm/TODO.md 확인 시각을 적고 미완 작업 요약을 Claude 문맥에 넣는다.

프로젝트 폴더는 CLAUDE_PROJECT_DIR, 없으면 표준 입력 JSON의 cwd, 없으면 현재 폴더다.
_pm/TODO.md가 없으면 아무것도 출력하지 않고 0으로 끝난다.
"""
import io
import json
import os
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔 기본 인코딩과 무관하게 UTF-8로 낸다
except Exception:
    pass

STAMP_PREFIX = "> Claude 마지막 확인:"


def stamp(text, now):
    """확인 시각 줄을 now로 바꾼다. 없으면 첫 제목 줄 다음에 넣는다. 줄 끝 문자는 유지한다."""
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    for i, line in enumerate(lines):
        if line.startswith(STAMP_PREFIX):
            lines[i] = f"{STAMP_PREFIX} {now}"
            return nl.join(lines)
    for i, line in enumerate(lines):
        if line.startswith("# "):
            lines[i + 1:i + 1] = ["", f"{STAMP_PREFIX} {now}"]
            return nl.join(lines)
    return f"{STAMP_PREFIX} {now}{nl}{text}"


def section(text, heading):
    """'## heading' 절의 줄들을 돌려준다 (다음 '## ' 앞까지)."""
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip().startswith(heading)
            continue
        if inside:
            out.append(line)
    return out


def summarize(text):
    open_items = [l[6:].strip() for l in section(text, "작업 목록") if l.startswith("- [ ]")]
    new_items = [l.strip() for l in section(text, "새 작업 추가")
                 if l.strip() and not l.strip().startswith("(")]
    parts = [f"_pm/TODO.md 확인: 미완 작업 {len(open_items)}건"]
    parts += [f"  - {t}" for t in open_items[:10]]
    if new_items:
        parts.append(f"'새 작업 추가' 절에 {len(new_items)}건이 있다. 작업 목록으로 옮기고 "
                     "시작 여부를 사용자에게 확인할 것 (pm 스킬)")
    return "\n".join(parts)


def project_dir(payload):
    return os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    todo = os.path.join(project_dir(payload), "_pm", "TODO.md")
    if not os.path.isfile(todo):
        return 0
    with io.open(todo, encoding="utf-8", newline="") as f:
        text = f.read()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with io.open(todo, "w", encoding="utf-8", newline="") as f:
        f.write(stamp(text, now))
    out = {"hookSpecificOutput": {"hookEventName": "SessionStart",
                                  "additionalContext": summarize(text)}}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
