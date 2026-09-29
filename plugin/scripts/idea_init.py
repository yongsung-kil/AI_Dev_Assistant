"""아이디어 접수: 폴더와 README를 양식에서 만들고 현황표에 행을 더한다.

사용: python idea_init.py [--root 프로젝트폴더] [--dir ideas] 번호 이름 [출처]
만드는 것: {dir}/{번호 3자리}_{이름}/README.md, {dir}/README.md(현황표, 없으면 양식), {dir}/실험로그.md(없으면 양식).
같은 번호의 행이 이미 있으면 더하지 않는다. 있는 파일은 덮어쓰지 않는다.
"""
import argparse
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "idea")


def _read(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def add_row(table_text, row, number):
    """'## 전체' 절의 표 끝에 행을 넣는다. 같은 번호가 있으면 그대로 돌려준다."""
    if f"| {number} |" in table_text:
        return table_text, False
    lines = table_text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("## 전체"):
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("|---"):
                    k = j + 1
                    while k < len(lines) and lines[k].startswith("|"):
                        k += 1
                    lines.insert(k, row)
                    return "\n".join(lines), True
            break
    return table_text.rstrip("\n") + "\n" + row + "\n", True


def create(root, ideas_dir, number, name, source=""):
    root = os.path.abspath(root)
    base = os.path.join(root, ideas_dir)
    os.makedirs(base, exist_ok=True)
    folder_name = f"{int(number):03d}_{name}"
    folder = os.path.join(base, folder_name)
    os.makedirs(folder, exist_ok=True)
    readme = os.path.join(folder, "README.md")
    if not os.path.exists(readme):
        text = _read(os.path.join(TEMPLATE_DIR, "README.md"))
        _write(readme, text.replace("{name}", name).replace("{source}", source or "(출처)"))
    table = os.path.join(base, "README.md")
    if not os.path.exists(table):
        shutil.copyfile(os.path.join(TEMPLATE_DIR, "status_table.md"), table)
    log = os.path.join(base, "실험로그.md")
    if not os.path.exists(log):
        shutil.copyfile(os.path.join(TEMPLATE_DIR, "experiment_log.md"), log)
    row = f"| {int(number)} | {name} | {source} | 대기 | `{folder_name}/` |"
    new_text, added = add_row(_read(table), row, int(number))
    if added:
        _write(table, new_text)
    return {"folder": folder, "readme": readme, "table_file": table, "row_added": added}


def main(argv=None):
    ap = argparse.ArgumentParser(description="아이디어 접수")
    ap.add_argument("--root", default=".")
    ap.add_argument("--dir", default="ideas")
    ap.add_argument("number", type=int)
    ap.add_argument("name")
    ap.add_argument("source", nargs="?", default="")
    a = ap.parse_args(argv)
    r = create(a.root, a.dir, a.number, a.name, a.source)
    print(f"아이디어 폴더: {r['folder']} (현황표 행 {'추가' if r['row_added'] else '이미 있음'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
