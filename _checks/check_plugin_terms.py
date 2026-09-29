"""plugin/ 폴더에 금지 표현이 없는지 검사한다.

사용: python _checks/check_plugin_terms.py [검사 폴더] [목록 파일]
기본: plugin/ 과 _checks/forbidden_terms.local.txt. 목록은 한 줄에 하나, # 은 주석, 대소문자 구분 없음.
종료 코드: 0 없음, 1 발견, 2 목록 파일 없음.
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔 기본 인코딩과 무관하게 UTF-8로 낸다
except Exception:
    pass

SKIP_DIRS = {"results", "__pycache__", ".git"}


def scan(root, terms):
    hits = []
    lowered = [(t, t.lower()) for t in terms]
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = os.path.join(r, name)
            try:
                with io.open(path, encoding="utf-8") as f:
                    text = f.read()
            except (UnicodeDecodeError, OSError):
                continue
            for no, line in enumerate(text.splitlines(), 1):
                low = line.lower()
                for term, term_low in lowered:
                    if term_low in low:
                        hits.append((path, no, term))
    return hits


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = argv[0] if argv else "plugin"
    terms_file = argv[1] if len(argv) > 1 else os.path.join("_checks", "forbidden_terms.local.txt")
    if not os.path.isfile(terms_file):
        print(f"목록 파일 없음: {terms_file} (forbidden_terms.example.txt를 복사해 만들 것)")
        return 2
    with io.open(terms_file, encoding="utf-8") as f:
        terms = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    hits = scan(root, terms)
    for path, no, term in hits:
        print(f"{path}:{no}: '{term}'")
    print(f"발견 {len(hits)}건")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
