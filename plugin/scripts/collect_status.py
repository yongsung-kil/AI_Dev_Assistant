"""프로젝트 현황을 훑어 dashboard/status.json을 만든다.

사용: python collect_status.py [프로젝트 폴더]
읽는 것: _pm/TODO.md(작업 목록), _pm/DONE.md(완료), _pm/tasks/**/판정요청*.md(결정), 아이디어 현황표(README의 표),
실험로그.md(절), 문서(docs, _wiki, _pm, 루트 README와 CLAUDE.md)의 제목과 태그와 링크, docs/profile/ 유무.
설정 파일 dashboard/config.json이 있으면 ideas_files, experiment_logs, doc_dirs, root_docs를 덮어쓴다.
"""
import io
import json
import os
import re
import sys
from datetime import datetime
from urllib.parse import unquote

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md_to_html  # noqa: E402

SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", "env", "build", "dist",
             "Sim_Output", ".superpowers", ".pytest_cache", ".idea", ".vscode", "dashboard", "testbed"}
DEFAULT_CONFIG = {"ideas_files": None, "experiment_logs": None,
                  "doc_dirs": ["docs", "_wiki", "_pm"], "root_docs": ["README.md", "CLAUDE.md"]}
TODO_ITEM = re.compile(r"^- \[( |x|X)\] (.*)$")
DONE_HEAD = re.compile(r"^### (\d{4}-\d{2}-\d{2})\s+(.*)$")
QUESTION = re.compile(r"^## 물음 (\d+)\.\s*(.*)$")


def read_text(path):
    try:
        with io.open(path, encoding="utf-8", newline="") as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        return ""


def rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def section(text, heading):
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip().startswith(heading)
            continue
        if inside:
            out.append(line)
    return out


def parse_todo(text):
    items = []
    for line in section(text, "작업 목록"):
        m = TODO_ITEM.match(line)
        if m:
            items.append({"title": m.group(2).strip(), "done": m.group(1) != " ", "detail": None,
                          "subtasks": [], "notes": []})
            continue
        if not items or not line.startswith("  "):
            continue
        sub = line.strip()
        m2 = TODO_ITEM.match(sub)
        if m2:
            items[-1]["subtasks"].append({"title": m2.group(2).strip(), "done": m2.group(1) != " "})
        elif sub.startswith("- 상세:"):
            items[-1]["detail"] = sub[len("- 상세:"):].strip().strip("`")
        elif sub.startswith("- "):
            items[-1]["notes"].append(sub[2:].strip())
    return items


def parse_done(text):
    entries, current = [], None
    for line in text.splitlines():
        m = DONE_HEAD.match(line)
        if m:
            current = {"date": m.group(1), "title": m.group(2).strip(), "summary": ""}
            entries.append(current)
            continue
        if current is not None and not current["summary"]:
            stripped = line.strip()
            if stripped and not stripped.startswith(("-", "#", ">")):
                current["summary"] = stripped
    return entries


def parse_decisions(root):
    decisions = []
    tasks_dir = os.path.join(root, "_pm", "tasks")
    if not os.path.isdir(tasks_dir):
        return decisions
    for r, dirs, files in os.walk(tasks_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if not (name.startswith("판정요청") and name.endswith(".md")):
                continue
            text = read_text(os.path.join(r, name))
            lines = text.splitlines()
            title = next((l[2:].strip() for l in lines if l.startswith("# ")), name)
            questions = []
            for i, line in enumerate(lines):
                q = QUESTION.match(line)
                if not q:
                    continue
                answered = False
                for later in lines[i + 1:]:
                    if later.startswith("## "):
                        break
                    if later.startswith("%"):
                        answered = len(later.strip()) > 1
                        break
                questions.append({"no": int(q.group(1)), "title": q.group(2).strip(), "answered": answered})
            decisions.append({"file": rel(root, os.path.join(r, name)), "title": title, "questions": questions})
    return decisions


def _tables(text):
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and md_to_html.TABLE_SEP.match(lines[i + 1]):
            header = md_to_html._split_row(lines[i])
            i += 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(md_to_html._split_row(lines[i]))
                i += 1
            yield header, rows
            continue
        i += 1


def default_ideas_files(root):
    files = []
    if os.path.isfile(os.path.join(root, "README.md")):
        files.append("README.md")
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d, "README.md")
        if d not in SKIP_DIRS and os.path.isfile(p):
            files.append(f"{d}/README.md")
    return files


def parse_ideas(root, files):
    keys = {"#": "no", "제목": "title", "출처": "source", "상태": "status", "디렉토리": "dir"}
    ideas = []
    for f in files:
        for header, rows in _tables(read_text(os.path.join(root, f))):
            if not {"#", "제목", "상태"} <= set(header):
                continue
            for row in rows:
                if not any(row):
                    continue
                item = {v: "" for v in keys.values()}
                for name, cell in zip(header, row):
                    if name in keys:
                        item[keys[name]] = cell.strip().strip("`")
                ideas.append(item)
    return ideas


def default_experiment_logs(root):
    found = []
    for r, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if name == "실험로그.md":
                found.append(rel(root, os.path.join(r, name)))
    return found


def parse_experiments(root, files):
    out = []
    for f in files:
        for level, title, _id in md_to_html.extract_headings(read_text(os.path.join(root, f))):
            if level == 2:
                out.append({"file": f, "title": title})
    return out


def collect_docs(root, config):
    paths = []
    for name in config["root_docs"]:
        if os.path.isfile(os.path.join(root, name)):
            paths.append(os.path.join(root, name))
    for d in config["doc_dirs"]:
        base = os.path.join(root, d)
        if not os.path.isdir(base):
            continue
        for r, dirs, files in os.walk(base):
            dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
            for name in sorted(files):
                if name.endswith(".md"):
                    paths.append(os.path.join(r, name))
    docs = {}
    for path in paths:
        text = read_text(path)
        meta, body = md_to_html.parse_frontmatter(text)
        title = meta.get("title") or next((l[2:].strip() for l in body.splitlines() if l.startswith("# ")), None)
        title = title or os.path.splitext(os.path.basename(path))[0]
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags] if tags else []
        links = set()
        for _text, href in md_to_html.LINK.findall(body):
            if re.match(r"[a-z]+:", href) or href.startswith("#"):
                continue
            target = unquote(href.split("#")[0])
            if not target.endswith(".md"):
                continue
            full = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if os.path.isfile(full):
                links.add(rel(root, full))
        docs[rel(root, path)] = {"path": rel(root, path), "title": title, "tags": tags,
                                 "links_out": sorted(links), "links_in": []}
    for src, d in docs.items():
        for dst in d["links_out"]:
            if dst in docs:
                docs[dst]["links_in"].append(src)
    for d in docs.values():
        d["links_in"] = sorted(d["links_in"])
    return [docs[k] for k in sorted(docs)]


def load_config(root):
    config = dict(DEFAULT_CONFIG)
    path = os.path.join(root, "dashboard", "config.json")
    if os.path.isfile(path):
        try:
            with io.open(path, encoding="utf-8") as f:
                config.update(json.load(f))
        except (ValueError, OSError):
            pass
    return config


def collect(root, config=None):
    root = os.path.abspath(root)
    config = config or load_config(root)
    ideas_files = config.get("ideas_files") or default_ideas_files(root)
    logs = config.get("experiment_logs") or default_experiment_logs(root)
    profile_dir = os.path.join(root, "docs", "profile")
    profile_files = sorted(f for f in os.listdir(profile_dir) if f.endswith(".md")) if os.path.isdir(profile_dir) else []
    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project": os.path.basename(root),
        "todo": parse_todo(read_text(os.path.join(root, "_pm", "TODO.md"))),
        "done": parse_done(read_text(os.path.join(root, "_pm", "DONE.md"))),
        "decisions": parse_decisions(root),
        "ideas": parse_ideas(root, ideas_files),
        "experiments": parse_experiments(root, logs),
        "docs": collect_docs(root, config),
        "profile": {"exists": os.path.isdir(profile_dir), "files": profile_files},
    }


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = os.path.abspath(argv[0]) if argv else os.getcwd()
    data = collect(root)
    out_dir = os.path.join(root, "dashboard")
    os.makedirs(out_dir, exist_ok=True)
    with io.open(os.path.join(out_dir, "status.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"status.json: 작업 {len(data['todo'])}, 완료 {len(data['done'])}, 결정 {len(data['decisions'])}, "
          f"아이디어 {len(data['ideas'])}, 실험 {len(data['experiments'])}, 문서 {len(data['docs'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
