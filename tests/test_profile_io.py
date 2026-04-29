"""Tests for safe profile path resolution."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nblane.core.profile_io import (
    safe_profile_dir,
    validate_profile_name,
)


class TestProfileNameSafety(unittest.TestCase):
    """Profile names allow display text but never path traversal."""

    def test_validate_profile_name_allows_chinese_and_plain_names(self) -> None:
        """Chinese, spaces, and ordinary punctuation remain valid."""
        self.assertEqual(validate_profile_name("王军"), "王军")
        self.assertEqual(
            validate_profile_name(" alice-smith_01 "),
            "alice-smith_01",
        )
        self.assertEqual(validate_profile_name("Alice Smith"), "Alice Smith")

    def test_validate_profile_name_rejects_path_shapes(self) -> None:
        """Empty names, path separators, and controls are rejected."""
        for name in (
            "",
            "   ",
            ".",
            "..",
            "alice/bob",
            "alice\\bob",
            "bad\nname",
            "bad\x00name",
        ):
            with self.subTest(name=repr(name)):
                with self.assertRaises(ValueError):
                    validate_profile_name(name)

    def test_safe_profile_dir_enforces_resolved_containment(self) -> None:
        """A symlinked profile directory may not escape profiles/."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            outside = Path(tmp) / "outside"
            root.mkdir()
            outside.mkdir()

            self.assertEqual(
                safe_profile_dir("王军", root),
                (root / "王军").resolve(strict=False),
            )

            (root / "escape").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                safe_profile_dir("escape", root)


if __name__ == "__main__":
    unittest.main()
