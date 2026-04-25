"""Tests for file fingerprint conflict detection."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nblane.core.file_state import (
    FileConflictError,
    assert_unchanged,
    snapshot_file,
)


class TestFileState(unittest.TestCase):
    """File snapshots detect concurrent edits."""

    def test_snapshot_detects_changed_content(self) -> None:
        """Changing file content invalidates an old snapshot."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.txt"
            path.write_text("one", encoding="utf-8")
            snap = snapshot_file(path)
            path.write_text("two", encoding="utf-8")

            with self.assertRaises(FileConflictError):
                assert_unchanged(path, snap)

    def test_missing_file_snapshot_matches_missing_file(self) -> None:
        """Missing files can be snapshotted before creation."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.txt"
            snap = snapshot_file(path)
            assert_unchanged(path, snap)


if __name__ == "__main__":
    unittest.main()
