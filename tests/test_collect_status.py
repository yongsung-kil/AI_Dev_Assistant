import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import collect_status  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts", "collect_status.py")


def make_project(root):
    (root / "_pm").mkdir()
    (root / "_pm" / "TODO.md").write_text(
        "# TODO\n\n> Claude 마지막 확인: 2026-09-30 10:00:00\n\n## 작업 목록\n\n"
        "- [ ] 첫 작업\n  - 상세: _pm/tasks/20260930_first/\n  - [x] 단계 1\n  - [ ] 단계 2\n  - [ ] 단계 3\n  - 메모 한 줄\n"
        "- [x] 끝난 작업\n\n## 새 작업 추가\n\n(비어 있음)\n", encoding="utf-8")
    (root / "_pm" / "DONE.md").write_text(
        "# DONE\n\n### 2026-09-29 둘째 완료\n요약 둘\n- **배경**: b\n\n### 2026-09-28 첫째 완료\n요약 하나\n", encoding="utf-8")
    (root / "_pm" / "tasks" / "20260930_first").mkdir(parents=True)
    (root / "_pm" / "tasks" / "20260930_first" / "20260930_first.md").write_text("# 첫 작업\n", encoding="utf-8")
    (root / "_pm" / "tasks" / "20260930_first" / "판정요청_x_260930.md").write_text(
        "# 판정요청: x\n\n## 물음 1. 하나\n\n- 예시\n%1\n\n## 물음 2. 둘\n\n- 예시\n%\n", encoding="utf-8")
    (root / "README.md").write_text(
        "# 프로젝트\n\n| # | 제목 | 출처 | 상태 | 디렉토리 |\n|---|---|---|---|---|\n"
        "| 1 | 아이디어 하나 | 논문 a | 실험중 | `001_a/` |\n| 2 | 아이디어 둘 | 제안 | 대기 | `002_b/` |\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "실험로그.md").write_text("# 실험로그\n\n## 실험 1\n내용\n\n## 실험 2\n내용\n", encoding="utf-8")
    (root / "docs" / "한글 문서.md").write_text("---\ntitle: 한글 제목\ntags: [t1, t2]\n---\n# 한글 제목\n[b](b.md) [외부](https://x.y)\n", encoding="utf-8")
    (root / "docs" / "b.md").write_text("# 비\n", encoding="utf-8")


def test_todo_items_with_subtasks_and_detail(tmp_path):
    make_project(tmp_path)
    s = collect_status.collect(str(tmp_path))
    assert [t["title"] for t in s["todo"]] == ["첫 작업", "끝난 작업"]
    first = s["todo"][0]
    assert first["done"] is False and first["detail"] == "_pm/tasks/20260930_first/"
    assert [(x["title"], x["done"]) for x in first["subtasks"]] == [("단계 1", True), ("단계 2", False), ("단계 3", False)]
    assert first["notes"] == ["메모 한 줄"]
    assert s["todo"][1]["done"] is True


def test_done_sections(tmp_path):
    make_project(tmp_path)
    s = collect_status.collect(str(tmp_path))
    assert s["done"] == [{"date": "2026-09-29", "title": "둘째 완료", "summary": "요약 둘"},
                         {"date": "2026-09-28", "title": "첫째 완료", "summary": "요약 하나"}]


def test_decision_questions_answered_flag(tmp_path):
    make_project(tmp_path)
    s = collect_status.collect(str(tmp_path))
    assert len(s["decisions"]) == 1
    d = s["decisions"][0]
    assert d["file"] == "_pm/tasks/20260930_first/판정요청_x_260930.md" and d["title"] == "판정요청: x"
    assert d["questions"] == [{"no": 1, "title": "하나", "answered": True}, {"no": 2, "title": "둘", "answered": False}]


def test_ideas_table_and_experiment_sections(tmp_path):
    make_project(tmp_path)
    s = collect_status.collect(str(tmp_path))
    assert s["ideas"] == [{"no": "1", "title": "아이디어 하나", "source": "논문 a", "status": "실험중", "dir": "001_a/"},
                          {"no": "2", "title": "아이디어 둘", "source": "제안", "status": "대기", "dir": "002_b/"}]
    assert s["experiments"] == [{"file": "docs/실험로그.md", "title": "실험 1"}, {"file": "docs/실험로그.md", "title": "실험 2"}]


def test_docs_links_out_and_in_with_korean_names(tmp_path):
    make_project(tmp_path)
    s = collect_status.collect(str(tmp_path))
    docs = {d["path"]: d for d in s["docs"]}
    assert docs["docs/한글 문서.md"]["title"] == "한글 제목" and docs["docs/한글 문서.md"]["tags"] == ["t1", "t2"]
    assert docs["docs/한글 문서.md"]["links_out"] == ["docs/b.md"]
    assert docs["docs/b.md"]["links_in"] == ["docs/한글 문서.md"]
    assert "README.md" in docs and "_pm/TODO.md" in docs


def test_empty_project_gives_empty_lists(tmp_path):
    s = collect_status.collect(str(tmp_path))
    assert s["todo"] == [] and s["done"] == [] and s["decisions"] == [] and s["ideas"] == []
    assert s["experiments"] == [] and s["docs"] == [] and s["profile"] == {"exists": False, "files": []}


def test_main_writes_status_json_utf8(tmp_path):
    make_project(tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    env["PYTHONUTF8"] = "0"
    r = subprocess.run([sys.executable, SCRIPT, str(tmp_path)], capture_output=True, env=env)
    assert r.returncode == 0
    data = json.loads((tmp_path / "dashboard" / "status.json").read_text(encoding="utf-8"))
    assert data["todo"][0]["title"] == "첫 작업" and "generated" in data
