"""Tests for the OpenClaw memory corpus renderer."""

from __future__ import annotations

import re
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from nblane.core import openclaw_corpus
from nblane.core.openclaw_corpus import (
    CORPUS_FILES,
    check_corpus_drift,
    render_profile_corpus,
)

_HEADER_RE = re.compile(
    r"^<!-- source: nblane \| generated: .+ \| do-not-edit -->$"
)

SKILL_MD = """# Alice · nblane Profile

## Identity

- **Name**: Alice
- **Domain**: Robotics
- **North Star**: Become the secret robotics overlord
- **North Star Brief**: Robotics expert
- **North Star Visibility**: {visibility}

---

## Core Competencies

| Area | Status | Notes |
|------|--------|-------|
| Control | solid | shipped |
"""

SKILL_TREE_YAML = """profile: alice
updated: "2026-09-18"

nodes:
  - id: ros2_basics
    status: solid
    note: "completed 2025-09"
  - id: moveit2
    status: learning
"""

GOALS_YAML = """schema_version: "1.0"
profile: alice
updated: "2026-09-18"
current_goal_id: g1
goals:
  - id: g1
    title: Ship manipulation demo
    status: active
    summary: Get the arm stacking blocks.
  - id: g2
    title: Secret side quest
    status: active
    ui_visibility: private
"""

KANBAN_MD = """# Alice · Kanban

## Doing

- [ ] Tune the impedance controller

## Queue

- [ ] Write up sim2real results
"""

AGENT_PROFILE_YAML = """understanding_of_user:
  current_focus:
    - ship the demo
working_style:
  prefers:
    - concise plans
"""


def _make_profile(root: Path, *, north_star_visibility: str = "discreet") -> Path:
    """Create a minimal profile fixture under *root*."""
    profile = root / "alice"
    profile.mkdir()
    (profile / "SKILL.md").write_text(
        SKILL_MD.format(visibility=north_star_visibility),
        encoding="utf-8",
    )
    (profile / "skill-tree.yaml").write_text(SKILL_TREE_YAML, encoding="utf-8")
    (profile / "goals.yaml").write_text(GOALS_YAML, encoding="utf-8")
    (profile / "kanban.md").write_text(KANBAN_MD, encoding="utf-8")
    (profile / "agent-profile.yaml").write_text(
        AGENT_PROFILE_YAML, encoding="utf-8"
    )
    return profile


class TestRenderProfileCorpus(unittest.TestCase):
    """Corpus rendering writes all four files with the generated header."""

    def test_renders_all_four_files_with_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                result = render_profile_corpus(
                    "alice", out_dir, today=date(2026, 9, 18)
                )

            self.assertEqual(result.out_dir, out_dir)
            self.assertEqual(result.skipped, [])
            self.assertEqual(
                sorted(p.name for p in result.written),
                sorted(CORPUS_FILES),
            )
            for path in result.written:
                text = path.read_text(encoding="utf-8")
                first_line = text.splitlines()[0]
                self.assertRegex(first_line, _HEADER_RE)
                self.assertIn("2026-09-18", first_line)

            tree_text = (out_dir / "skill-tree.md").read_text(encoding="utf-8")
            self.assertIn("- [x] ros2_basics", tree_text)
            self.assertIn("- [ ] moveit2", tree_text)

            kanban_text = (out_dir / "kanban.md").read_text(encoding="utf-8")
            self.assertIn(KANBAN_MD.strip(), kanban_text)

            summary_text = (out_dir / "profile-summary.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("# Profile summary: alice", summary_text)
            self.assertIn("Tune the impedance controller", summary_text)

    def test_out_dir_defaults_to_openclaw_memory_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            with (
                patch(
                    "nblane.core.openclaw_corpus.profile_dir",
                    lambda _name: profile,
                ),
                patch.object(Path, "home", staticmethod(lambda: root)),
            ):
                result = render_profile_corpus("alice", today=date(2026, 9, 18))
            expected = root / ".openclaw" / "workspace" / "memory" / "nblane"
            self.assertEqual(result.out_dir, expected)
            self.assertTrue((expected / "skill-tree.md").exists())

    def test_missing_kanban_is_skipped_not_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            (profile / "kanban.md").unlink()
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                result = render_profile_corpus(
                    "alice", out_dir, today=date(2026, 9, 18)
                )

            self.assertFalse((out_dir / "kanban.md").exists())
            self.assertTrue((out_dir / "goals.md").exists())
            self.assertEqual(len(result.skipped), 1)
            self.assertIn("kanban.md", result.skipped[0])
            self.assertIn("kanban.md not found", result.skipped[0])

    def test_missing_goals_yaml_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            (profile / "goals.yaml").unlink()
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                result = render_profile_corpus(
                    "alice", out_dir, today=date(2026, 9, 18)
                )

            self.assertFalse((out_dir / "goals.md").exists())
            self.assertEqual(len(result.skipped), 1)
            self.assertIn("goals.md", result.skipped[0])


class TestCorpusPrivacy(unittest.TestCase):
    """Private goals never reach the corpus; the North Star always does."""

    def test_private_north_star_is_rendered_in_goals_md(self) -> None:
        """Binary visibility gates public artifacts only; openclaw sees all."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root, north_star_visibility="private")
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                render_profile_corpus("alice", out_dir, today=date(2026, 9, 18))

            goals_text = (out_dir / "goals.md").read_text(encoding="utf-8")
            self.assertIn("secret robotics overlord", goals_text)
            self.assertIn("Ship manipulation demo", goals_text)
            # Private goals are hidden from agent context as well.
            self.assertNotIn("Secret side quest", goals_text)

    def test_visible_north_star_is_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root, north_star_visibility="visible")
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                render_profile_corpus("alice", out_dir, today=date(2026, 9, 18))

            goals_text = (out_dir / "goals.md").read_text(encoding="utf-8")
            self.assertIn("Become the secret robotics overlord", goals_text)


class TestCorpusDrift(unittest.TestCase):
    """Drift detection flags hand edits and ignores the timestamp line."""

    def test_fresh_render_has_no_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                render_profile_corpus("alice", out_dir, today=date(2026, 9, 18))
                drift = check_corpus_drift("alice", out_dir)
            self.assertEqual(drift, [])

    def test_hand_edited_file_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                render_profile_corpus("alice", out_dir, today=date(2026, 9, 18))
                edited = out_dir / "skill-tree.md"
                edited.write_text(
                    edited.read_text(encoding="utf-8") + "\nhand edit\n",
                    encoding="utf-8",
                )
                drift = check_corpus_drift("alice", out_dir)
            self.assertEqual(drift, ["skill-tree.md"])

    def test_timestamp_only_difference_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                render_profile_corpus("alice", out_dir, today=date(2026, 1, 1))
                # A later render day must not count as drift.
                drift = check_corpus_drift("alice", out_dir)
            self.assertEqual(drift, [])

    def test_missing_rendered_file_counts_as_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                render_profile_corpus("alice", out_dir, today=date(2026, 9, 18))
                (out_dir / "goals.md").unlink()
                drift = check_corpus_drift("alice", out_dir)
            self.assertEqual(drift, ["goals.md"])

    def test_stale_artifact_from_removed_source_counts_as_drift(self) -> None:
        """A generated file whose source disappeared is reported, not ignored."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                render_profile_corpus("alice", out_dir, today=date(2026, 9, 18))
                (profile / "goals.yaml").unlink()
                drift = check_corpus_drift("alice", out_dir)
            # goals.md lost its source; profile-summary.md changed too (it
            # embeds goal-book content). kanban.md stays in sync.
            self.assertIn("goals.md", drift)
            self.assertNotIn("kanban.md", drift)

    def test_foreign_file_without_header_is_not_drift(self) -> None:
        """User files in the corpus dir are never reported or removed."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                render_profile_corpus("alice", out_dir, today=date(2026, 9, 18))
                (out_dir / "notes.md").write_text("# my own notes\n", encoding="utf-8")
                drift = check_corpus_drift("alice", out_dir)
            self.assertEqual(drift, [])
            self.assertTrue((out_dir / "notes.md").exists())


class TestCorpusStaleCleanup(unittest.TestCase):
    """Rendering removes stale own-artifacts whose sources are gone."""

    def test_removed_source_deletes_generated_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                render_profile_corpus("alice", out_dir, today=date(2026, 9, 18))
                self.assertTrue((out_dir / "goals.md").exists())
                (profile / "goals.yaml").unlink()
                result = render_profile_corpus(
                    "alice", out_dir, today=date(2026, 9, 19)
                )
            self.assertFalse((out_dir / "goals.md").exists())
            self.assertEqual([p.name for p in result.removed], ["goals.md"])
            self.assertTrue((out_dir / "skill-tree.md").exists())
            # A later drift check is clean again.
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                self.assertEqual(check_corpus_drift("alice", out_dir), [])

    def test_stale_non_corpus_name_with_header_is_removed(self) -> None:
        """Renamed/legacy artifacts carrying our header are cleaned too."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                result = render_profile_corpus(
                    "alice", out_dir, today=date(2026, 9, 18)
                )
                legacy = out_dir / "old-summary.md"
                legacy.write_text(
                    "<!-- source: nblane | generated: 2026-01-01 | do-not-edit -->\n\nstale\n",
                    encoding="utf-8",
                )
                result = render_profile_corpus(
                    "alice", out_dir, today=date(2026, 9, 19)
                )
            self.assertFalse(legacy.exists())
            self.assertIn(legacy, result.removed)

    def test_foreign_file_survives_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out_dir = root / "corpus"
            with patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ):
                render_profile_corpus("alice", out_dir, today=date(2026, 9, 18))
                foreign = out_dir / "notes.md"
                foreign.write_text("# my own notes\n", encoding="utf-8")
                result = render_profile_corpus(
                    "alice", out_dir, today=date(2026, 9, 19)
                )
            self.assertTrue(foreign.exists())
            self.assertEqual(result.removed, [])


if __name__ == "__main__":
    unittest.main()
