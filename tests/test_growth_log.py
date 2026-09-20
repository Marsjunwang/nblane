"""Tests for Growth Log append hardening (atomic write + backup)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.growth_log import append_growth_log_row

SKILL_MD = """# Demo Profile

## Growth Log

| Date | Event | Why it matters |
|------|-------|----------------|
"""


class TestGrowthLog(unittest.TestCase):
    """Growth log rows are written atomically and backed up."""

    def test_append_uses_atomic_write_and_records_backup(self) -> None:
        """The write goes through atomic_write_text, then record_change."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            (prof / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
            with patch(
                "nblane.core.growth_log.atomic_write_text"
            ) as atomic, patch(
                "nblane.core.growth_log.git_backup.record_change"
            ) as record:
                append_growth_log_row(prof, "Shipped L0.3")

        atomic.assert_called_once()
        path, text = atomic.call_args[0][:2]
        self.assertEqual(path, prof / "SKILL.md")
        self.assertIn("Shipped L0.3", text)
        record.assert_called_once()

    def test_append_row_round_trip(self) -> None:
        """A new dated row lands under the Growth Log table header."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            (prof / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
            with patch("nblane.core.growth_log.git_backup.record_change"):
                append_growth_log_row(prof, "Wrote integration tests")
            content = (prof / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("| Wrote integration tests | — |", content)


if __name__ == "__main__":
    unittest.main()
