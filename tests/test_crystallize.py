"""Tests for method draft crystallization (atomic write + backup)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.crystallize import write_method_draft


class TestCrystallize(unittest.TestCase):
    """Method drafts are written atomically and backed up."""

    def test_write_method_draft_records_backup(self) -> None:
        """The draft write is followed by git_backup.record_change."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            with patch(
                "nblane.core.crystallize.profile_dir",
                lambda _name: prof,
            ), patch(
                "nblane.core.crystallize.git_backup.record_change"
            ) as record:
                path = write_method_draft(
                    "demo",
                    "Weekly Review",
                    "Body text",
                )

            record.assert_called_once()
            self.assertEqual(record.call_args[0][0], [path])
            self.assertEqual(path, prof / "methods" / "weekly-review_draft.md")
            content = path.read_text(encoding="utf-8")
            self.assertIn("# Method draft: Weekly Review", content)
            self.assertIn("Body text", content)


if __name__ == "__main__":
    unittest.main()
