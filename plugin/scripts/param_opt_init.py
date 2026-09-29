"""파라미터 최적화기 뼈대(templates/param_opt/)를 프로젝트의 optim/에 복사한다. 있는 파일은 건너뛴다.

사용: python param_opt_init.py [프로젝트 폴더] [--dir optim]
"""
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "param_opt")


def init(root, dir_name="optim"):
    dst = os.path.join(os.path.abspath(root), dir_name)
    os.makedirs(dst, exist_ok=True)
    copied = 0
    for name in sorted(os.listdir(TEMPLATE_DIR)):
        source = os.path.join(TEMPLATE_DIR, name)
        if not os.path.isfile(source):
            continue  # __pycache__ 같은 폴더는 뼈대가 아니다
        target = os.path.join(dst, name)
        if not os.path.exists(target):
            shutil.copyfile(os.path.join(TEMPLATE_DIR, name), target)
            copied += 1
    return copied


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    dir_name = "optim"
    if "--dir" in argv:
        i = argv.index("--dir")
        dir_name = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    root = argv[0] if argv else os.getcwd()
    n = init(root, dir_name)
    print(f"{dir_name}/ 준비: 새로 복사 {n}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
