"""플러그인의 templates/_pm/ 을 프로젝트 폴더에 복사한다. 이미 있는 파일은 건너뛴다.

사용: python pm_init.py [프로젝트 폴더]   (기본: 현재 폴더)
"""
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔 기본 인코딩과 무관하게 UTF-8로 낸다
except Exception:
    pass

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "_pm")


def main(dest=None):
    dest = os.path.abspath(dest or os.getcwd())
    target = os.path.join(dest, "_pm")
    copied = 0
    for root, _dirs, files in os.walk(TEMPLATE_DIR):
        rel = os.path.relpath(root, TEMPLATE_DIR)
        out_dir = os.path.join(target, rel) if rel != "." else target
        os.makedirs(out_dir, exist_ok=True)
        for name in files:
            dst = os.path.join(out_dir, name)
            if not os.path.exists(dst):
                shutil.copyfile(os.path.join(root, name), dst)
                copied += 1
    print(f"_pm 준비: 새로 복사 {copied}개 ({target})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
