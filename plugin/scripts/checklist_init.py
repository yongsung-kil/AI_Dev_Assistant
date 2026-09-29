"""점검표와 항목 문서 양식을 프로젝트에 복사한다.

사용: python checklist_init.py <speed | robustness> [프로젝트 폴더]
speed는 docs/speed_opt/, robustness는 docs/robustness/에 checklist.md, item_template.md, README.md를 둔다.
있는 파일은 덮어쓰지 않는다.
"""
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "checklists")
KINDS = {"speed": "speed_opt", "robustness": "robustness"}


def init(root, kind):
    if kind not in KINDS:
        raise ValueError(f"kind는 {', '.join(KINDS)} 중 하나: {kind}")
    src = os.path.join(TEMPLATE_DIR, kind)
    dst = os.path.join(os.path.abspath(root), "docs", KINDS[kind])
    os.makedirs(dst, exist_ok=True)
    copied = 0
    for name in sorted(os.listdir(src)):
        if not os.path.isfile(os.path.join(src, name)):
            continue
        target = os.path.join(dst, name)
        if not os.path.exists(target):
            shutil.copyfile(os.path.join(src, name), target)
            copied += 1
    return copied


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    kind = argv[0] if argv else ""
    root = argv[1] if len(argv) > 1 else os.getcwd()
    if kind not in KINDS:
        print(f"사용법: checklist_init.py <{' | '.join(KINDS)}> [프로젝트 폴더]")
        return 2
    n = init(root, kind)
    print(f"docs/{KINDS[kind]}/ 준비: 새로 복사 {n}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
