"""PostToolUse 자동 실행: Edit나 Write로 고친 파일이 md면 doc_check를 돌려 경고를 문맥에 넣는다.

발견이 없거나 md가 아니거나 입력이 JSON이 아니면 아무것도 출력하지 않는다. 막지는 않는다 (경고만).
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔 기본 인코딩과 무관하게 UTF-8로 낸다
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doc_check  # noqa: E402


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    path = (payload.get("tool_input") or {}).get("file_path", "") if isinstance(payload, dict) else ""
    if not path.endswith(".md") or not os.path.isfile(path):
        return 0
    findings = doc_check.check_file(path)
    if not findings:
        return 0
    lines = [f"{os.path.basename(p)}:{no}: [{rule}] {msg}" for p, no, rule, msg in findings[:20]]
    context = f"문서 검사 경고 {len(findings)}건 (doc-check 스킬로 다시 쓸 것):\n" + "\n".join(lines)
    out = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
