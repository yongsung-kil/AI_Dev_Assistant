import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import wiki_init  # noqa: E402


def test_init_creates_skeleton_with_tech_branch(tmp_path):
    assert wiki_init.main(str(tmp_path)) == 0
    w = tmp_path / "_wiki"
    for rel in ["manual.md", "MOC.md", "_tracker.md", "decisions/MOC-decisions.md", "trials/MOC-trials.md",
                "assets/MOC-assets.md", "tech/MOC-tech.md", "_templates/tech.md", "_inbox/.gitkeep"]:
        assert (w / rel).is_file(), rel


def test_init_never_overwrites(tmp_path):
    wiki_init.main(str(tmp_path))
    (tmp_path / "_wiki" / "_tracker.md").write_text("last_scan: 2026-01-01 00:00:00\n", encoding="utf-8")
    assert wiki_init.main(str(tmp_path)) == 0
    assert (tmp_path / "_wiki" / "_tracker.md").read_text(encoding="utf-8").startswith("last_scan: 2026-01-01")
