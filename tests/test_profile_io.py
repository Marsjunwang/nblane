"""Tests for safe profile path resolution."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.profile_io import (
    init_profile,
    safe_profile_dir,
    validate_profile_name,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


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

    def test_init_profile_copies_internal_p1_fact_sources(self) -> None:
        """New profiles include project, experience, and research source files."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            root.mkdir()
            with patch("nblane.core.profile_io.PROFILES_DIR", root):
                profile = init_profile("alice")

            self.assertTrue((profile / "project-board.yaml").exists())
            self.assertTrue((profile / "experience.yaml").exists())
            self.assertTrue((profile / "research" / "sources.yaml").exists())

    def test_init_profile_seeds_every_schema_node_as_locked(self) -> None:
        """A new profile lists its whole domain tree, unlit, so the page is usable."""
        import yaml

        from nblane.core import schema_io

        for schema in (None, "autonomous-driving"):
            with self.subTest(schema=schema), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "profiles"
                root.mkdir()
                with patch("nblane.core.profile_io.PROFILES_DIR", root):
                    profile = init_profile("alice", schema)
                tree = yaml.safe_load((profile / "skill-tree.yaml").read_text(encoding="utf-8"))
                expected = [n.id for n in schema_io.load_schema(tree["schema"]).nodes]
                self.assertEqual([n["id"] for n in tree["nodes"]], expected)
                self.assertEqual({n["status"] for n in tree["nodes"]}, {"locked"})

    def test_init_profile_fills_name_and_date_placeholders(self) -> None:
        """No ``{Name}`` / ``{YYYY-MM-DD}`` placeholder survives in a new profile."""
        from datetime import date

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            root.mkdir()
            with patch("nblane.core.profile_io.PROFILES_DIR", root):
                profile = init_profile("alice")
            texts = [p.read_text(encoding="utf-8") for p in profile.rglob("*") if p.is_file()]
            self.assertFalse(any("{YYYY-MM-DD}" in t or "{Name}" in t for t in texts))
            self.assertIn(date.today().isoformat(), (profile / "skill-tree.yaml").read_text(encoding="utf-8"))

    def test_init_profile_with_schema_rewrites_tree_and_domain(self) -> None:
        """--schema points skill-tree.yaml and SKILL.md Domain at the domain."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            root.mkdir()
            with patch("nblane.core.profile_io.PROFILES_DIR", root):
                profile = init_profile("carol", schema="autonomous-driving")
            tree_text = (profile / "skill-tree.yaml").read_text(encoding="utf-8")
            tree = yaml.safe_load(tree_text)
            self.assertEqual(tree["schema"], "autonomous-driving")
            self.assertEqual(tree["profile"], "carol")
            # Seeding rewrites the file: header kept, template examples dropped.
            self.assertIn("# Skill tree for carol", tree_text)
            self.assertNotIn("{Name}", tree_text)
            skill = (profile / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("- **Domain**: Autonomous Driving Engineer / 自动驾驶工程师", skill)

    def test_init_profile_default_keeps_template_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            root.mkdir()
            with patch("nblane.core.profile_io.PROFILES_DIR", root):
                profile = init_profile("dave")
            tree = yaml.safe_load((profile / "skill-tree.yaml").read_text(encoding="utf-8"))
            self.assertEqual(tree["schema"], "robotics-engineer")

    def test_init_profile_unknown_schema_raises_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            root.mkdir()
            with patch("nblane.core.profile_io.PROFILES_DIR", root):
                for bad in ("no-such-domain", "../robotics-engineer"):
                    with self.assertRaises(ValueError):
                        init_profile("erin", schema=bad)
            self.assertFalse((root / "erin").exists())

    def test_template_dir_follows_code_checkout_not_data_root(self) -> None:
        """NBLANE_ROOT is the data dir in production; the template ships with code."""
        with tempfile.TemporaryDirectory() as data_root:
            result = subprocess.run(
                [sys.executable, "-c",
                 "from nblane.core import paths;print(paths.TEMPLATE_DIR);print(paths.PROFILES_DIR)"],
                capture_output=True, text=True, check=True,
                env={**os.environ, "NBLANE_ROOT": data_root},
            )
            template, profiles = result.stdout.splitlines()
            self.assertEqual(Path(template), REPO_ROOT / "profiles" / "template")
            self.assertEqual(Path(profiles), Path(data_root).resolve() / "profiles")

    def test_cli_init_with_schema_and_unknown_schema(self) -> None:
        with tempfile.TemporaryDirectory() as data_root:
            env = {**os.environ, "NBLANE_ROOT": data_root, "NBLANE_DATA_GIT_AUTOCOMMIT": "0", "NBLANE_DATA_GIT_AUTOPUSH": "0"}
            (Path(data_root) / "profiles").mkdir()
            bad = subprocess.run(
                [sys.executable, "-m", "nblane.cli", "init", "frank", "--schema", "nope"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(bad.returncode, 1)
            self.assertIn("autonomous-driving", bad.stderr)
            self.assertFalse((Path(data_root) / "profiles" / "frank").exists())
            ok = subprocess.run(
                [sys.executable, "-m", "nblane.cli", "init", "frank", "--schema", "autonomous-driving"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertIn("Next steps", ok.stdout)
            tree = yaml.safe_load(
                (Path(data_root) / "profiles" / "frank" / "skill-tree.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(tree["schema"], "autonomous-driving")


if __name__ == "__main__":
    unittest.main()
