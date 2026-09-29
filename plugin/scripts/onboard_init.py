"""onboard 준비: 프로젝트를 훑어 요약(JSON)을 내고, 프로파일 양식과 CLAUDE.md, docs/ 뼈대를 복사한다.

사용: python onboard_init.py [프로젝트 폴더] [--summary-only]
출력: JSON 한 줄. languages(확장자로 센 언어별 파일 수), top_dirs, entry_candidates, build_files, readme, file_count, copied
이미 있는 파일은 덮어쓰지 않는다. 표준 라이브러리만 쓴다.
"""
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔 기본 인코딩과 무관하게 UTF-8로 낸다
except Exception:
    pass

TEMPLATE_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
EXT_LANG = {".py": "python", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".h": "cpp", ".hpp": "cpp", ".c": "c",
            ".v": "verilog", ".sv": "systemverilog", ".svh": "systemverilog", ".vhd": "vhdl", ".vhdl": "vhdl",
            ".m": "matlab", ".js": "javascript", ".ts": "typescript", ".rs": "rust", ".go": "go",
            ".java": "java", ".kt": "kotlin", ".cs": "csharp", ".jl": "julia"}
ENTRY_NAMES = {"main.py", "run.py", "app.py", "cli.py", "main.cpp", "main.c", "top.v", "top.sv", "main.rs", "main.go"}
BUILD_NAMES = {"Makefile", "CMakeLists.txt", "setup.py", "pyproject.toml", "requirements.txt", "package.json",
               "Cargo.toml", "build.gradle", "pom.xml", "meson.build", "SConstruct"}
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", "env", "build", "dist",
             "out", "obj", "third_party", "vendor", "external", "xcelium.d", ".Xil", "work",
             "Sim_Output", ".superpowers", ".pytest_cache", ".idea", ".vscode", "dashboard"}
COPIES = [("profile", os.path.join("docs", "profile")), ("docs", "docs"), ("CLAUDE.md", "CLAUDE.md")]


def scan(root):
    """언어별 파일 수, 최상위 폴더, 진입점 후보, 빌드 파일, README, 파일 수를 센다."""
    root = os.path.abspath(root)
    languages, entries, builds, readme, count = {}, [], [], None, 0
    for r, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        rel_dir = os.path.relpath(r, root).replace(os.sep, "/")
        for name in sorted(files):
            count += 1
            rel = name if rel_dir == "." else f"{rel_dir}/{name}"
            lang = EXT_LANG.get(os.path.splitext(name)[1].lower())
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            if name in ENTRY_NAMES:
                entries.append(rel)
            if name in BUILD_NAMES:
                builds.append(rel)
            if rel_dir == "." and name.lower().startswith("readme") and readme is None:
                readme = rel
    top_dirs = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and d not in SKIP_DIRS)
    return {"languages": dict(sorted(languages.items())), "top_dirs": top_dirs, "entry_candidates": entries,
            "build_files": builds, "readme": readme, "file_count": count}


def _copy_tree(src, dst):
    copied = 0
    for r, _dirs, files in os.walk(src):
        rel = os.path.relpath(r, src)
        out_dir = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(out_dir, exist_ok=True)
        for name in files:
            target = os.path.join(out_dir, name)
            if not os.path.exists(target):
                shutil.copyfile(os.path.join(r, name), target)
                copied += 1
    return copied


def init_docs(root):
    """프로파일 양식, docs 뼈대, CLAUDE.md를 복사한다. 있는 파일은 건너뛴다. 복사한 수를 돌려준다."""
    root = os.path.abspath(root)
    copied = 0
    for src_name, dst_rel in COPIES:
        src = os.path.join(TEMPLATE_ROOT, src_name)
        dst = os.path.join(root, dst_rel)
        if os.path.isdir(src):
            copied += _copy_tree(src, dst)
        elif os.path.isfile(src) and not os.path.exists(dst):
            shutil.copyfile(src, dst)
            copied += 1
    os.makedirs(os.path.join(root, "docs", "explore"), exist_ok=True)
    return copied


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    summary_only = "--summary-only" in argv
    paths = [a for a in argv if not a.startswith("--")]
    root = paths[0] if paths else os.getcwd()
    data = scan(root)
    data["copied"] = 0 if summary_only else init_docs(root)
    print(json.dumps(data, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
