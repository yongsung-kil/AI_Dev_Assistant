import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import checklist_init  # noqa: E402


def test_init_speed_and_robustness_copy_once(tmp_path):
    assert checklist_init.init(str(tmp_path), "speed") == 3
    speed = tmp_path / "docs" / "speed_opt"
    assert (speed / "checklist.md").is_file() and (speed / "item_template.md").is_file() and (speed / "README.md").is_file()
    (speed / "checklist.md").write_text("채움", encoding="utf-8")
    assert checklist_init.init(str(tmp_path), "speed") == 0
    assert (speed / "checklist.md").read_text(encoding="utf-8") == "채움"
    assert checklist_init.init(str(tmp_path), "robustness") == 3
    assert "리셋" in (tmp_path / "docs" / "robustness" / "checklist.md").read_text(encoding="utf-8")


def test_unknown_kind_returns_error(tmp_path):
    assert checklist_init.main(["memory", str(tmp_path)]) == 2
