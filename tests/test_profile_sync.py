"""Tests for deterministic profile sync generated sections."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"


class TestProfileSync(unittest.TestCase):
    """Verify sync check/write flow using nblane.core.sync."""

    def _make_profile_copy(self, tmp_dir: Path) -> Path:
        """Copy template profile into a temporary directory."""
        profile_dir = tmp_dir / "test-user"
        shutil.copytree(TEMPLATE_DIR, profile_dir)
        for file_path in profile_dir.rglob("*"):
            if file_path.is_file():
                text = file_path.read_text(encoding="utf-8")
                text = text.replace("{Name}", "test-user")
                text = text.replace(
                    "{YYYY-MM-DD}", "2026-03-21"
                )
                file_path.write_text(text, encoding="utf-8")
        return profile_dir

    def test_sync_write_then_check(self) -> None:
        """write_generated_blocks then get_drifted_blocks should be clean."""
        from nblane.core.sync import (
            get_drifted_blocks,
            write_generated_blocks,
        )

        with tempfile.TemporaryDirectory() as tmp:
            profile_dir = self._make_profile_copy(Path(tmp))
            write_generated_blocks(profile_dir)
            drifted = get_drifted_blocks(profile_dir)
            self.assertEqual(drifted, [])

    def test_sync_detects_drift(self) -> None:
        """get_drifted_blocks should detect manual edits."""
        from nblane.core.sync import (
            get_drifted_blocks,
            write_generated_blocks,
        )

        with tempfile.TemporaryDirectory() as tmp:
            profile_dir = self._make_profile_copy(Path(tmp))
            write_generated_blocks(profile_dir)

            skill_md = profile_dir / "SKILL.md"
            content = skill_md.read_text(encoding="utf-8")
            content = content.replace(
                "<!-- BEGIN GENERATED:skill_tree -->\n",
                "<!-- BEGIN GENERATED:skill_tree -->\n"
                "- [x] manual drift line\n",
                1,
            )
            skill_md.write_text(content, encoding="utf-8")

            drifted = get_drifted_blocks(profile_dir)
            self.assertIn("skill_tree", drifted)

    def test_sync_preserves_manual_sections(self) -> None:
        """Sync rewrite should not modify text outside markers."""
        from nblane.core.sync import write_generated_blocks

        with tempfile.TemporaryDirectory() as tmp:
            profile_dir = self._make_profile_copy(Path(tmp))
            skill_md = profile_dir / "SKILL.md"
            original = skill_md.read_text(encoding="utf-8")
            manual_line = (
                "- **North Star**: build a durable "
                "embodied AI research craft"
            )
            updated = original.replace(
                "- **North Star**: "
                '{One sentence. What does "大佬" look '
                "like for you in 5 years?}",
                manual_line,
                1,
            )
            skill_md.write_text(updated, encoding="utf-8")

            write_generated_blocks(profile_dir)
            final_text = skill_md.read_text(encoding="utf-8")
            self.assertIn(manual_line, final_text)


if __name__ == "__main__":
    unittest.main()
