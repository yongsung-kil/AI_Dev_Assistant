"""문서 검사: md 파일에서 줄표, 가운뎃점, 깨진 상대 링크, 금지 낱말을 찾는다.

사용: python doc_check.py <파일 또는 폴더>... [--terms 목록파일]
출력: 경로:줄: [규칙] 설명. 발견이 있으면 종료 코드 1, 없으면 0.
코드 울타리(```)와 인라인 코드(`...`) 안은 검사하지 않는다.
"""
import argparse
import io
import os
import re
import sys
from urllib.parse import unquote

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔 기본 인코딩과 무관하게 UTF-8로 낸다
except Exception:
    pass

BANNED_CHARS = {"—": "줄표", "·": "가운뎃점"}
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
INLINE_CODE = re.compile(r"`[^`]*`")


def iter_prose(text):
    """(줄 번호, 본문 줄)을 낸다. 코드 울타리 안은 건너뛴다."""
    fenced = False
    for no, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            yield no, line


def check_text(text, path, base_dir, terms=()):
    findings = []
    for no, raw in iter_prose(text):
        line = INLINE_CODE.sub("", raw)
        for ch, name in BANNED_CHARS.items():
            if ch in line:
                findings.append((path, no, "글자", f"{name}({ch}) 사용"))
        for term in terms:
            if term and term in line:
                findings.append((path, no, "낱말", f"금지 낱말 '{term}'"))
        for target in LINK.findall(raw):
            if re.match(r"[a-z]+:", target) or target.startswith("#"):
                continue
            rel = unquote(target.split("#")[0])
            if rel and not os.path.exists(os.path.join(base_dir, rel)):
                findings.append((path, no, "링크", f"없는 파일 '{rel}'"))
    return findings


def check_file(path, terms=()):
    with io.open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    return check_text(text, path, os.path.dirname(os.path.abspath(path)), terms)


def collect(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
                for name in files:
                    if name.endswith(".md"):
                        yield os.path.join(root, name)
        elif p.endswith(".md"):
            yield p


def load_terms(path):
    if not path:
        return []
    with io.open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def main(argv=None):
    ap = argparse.ArgumentParser(description="md 문서 검사")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--terms", help="금지 낱말 목록 파일 (한 줄에 하나)")
    a = ap.parse_args(argv)
    terms = load_terms(a.terms)
    found = []
    for f in collect(a.paths):
        found += check_file(f, terms)
    for path, no, rule, msg in found:
        print(f"{path}:{no}: [{rule}] {msg}")
    print(f"발견 {len(found)}건")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
