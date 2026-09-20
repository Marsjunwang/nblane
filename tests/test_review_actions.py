"""Tests for Review candidate writeback helpers."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.agent_activity import append_activity_item, load_agent_activity
from nblane.core.kanban_io import parse_kanban
from nblane.core.review_actions import (
    activity_item_from_kanban_candidate,
    apply_review_activity_item,
    apply_review_evidence_candidate,
    apply_review_kanban_candidate,
    apply_review_next_action_candidate,
    apply_review_public_draft_candidate,
    save_review_candidates_to_activity,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"


def _template_profile(tmp: Path, name: str = "alice") -> Path:
    profile = tmp / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            text = text.replace("{YYYY-MM-DD}", "2026-05-14")
            file_path.write_text(text, encoding="utf-8")
    return profile


class TestReviewActions(unittest.TestCase):
    """Review applies selected candidates without widening write scope."""

    def test_evidence_apply_only_changes_pool_and_optional_kanban(self) -> None:
        """Evidence writeback does not change skill status."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = _template_profile(Path(tmp_s))
            (profile / "kanban.md").write_text(
                """# alice · Kanban

## Doing

- (empty)

---

## Done

- [x] Ship demo
  - id: done-demo
  - outcome: demo shipped

---

## Queue

- (empty)

---

## Someday / Maybe

- (empty)

---
""",
                encoding="utf-8",
            )
            tree_before = yaml.safe_load((profile / "skill-tree.yaml").read_text(encoding="utf-8"))

            with patch("nblane.core.profile_io.PROFILES_DIR", profile.parent), patch(
                "nblane.core.review_actions.profile_dir",
                lambda _name: profile,
            ), patch(
                "nblane.core.agent_activity.profile_dir",
                lambda _name: profile,
            ), patch(
                "nblane.core.kanban_io.profile_dir",
                lambda _name: profile,
            ):
                result = apply_review_evidence_candidate(
                    "alice",
                    "2026-05-11",
                    "2026-05-14",
                    {
                        "source": "kanban_done",
                        "task_id": "done-demo",
                        "title": "Ship demo",
                        "summary": "demo shipped",
                    },
                    mark_crystallized=True,
                )
                pool = yaml.safe_load((profile / "evidence-pool.yaml").read_text(encoding="utf-8"))
                tree_after = yaml.safe_load((profile / "skill-tree.yaml").read_text(encoding="utf-8"))
                sections = parse_kanban("alice")
                activity = load_agent_activity("alice")

        self.assertTrue(result.ok)
        self.assertTrue(
            any(row.get("title") == "Ship demo" for row in pool.get("evidence_entries", []))
        )
        self.assertEqual(tree_before.get("nodes"), tree_after.get("nodes"))
        self.assertTrue(sections["Done"][0].crystallized)
        self.assertEqual(activity["items"][0]["status"], "applied")

    def test_next_action_apply_appends_queue(self) -> None:
        """Next action candidates become Queue tasks."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = _template_profile(Path(tmp_s))
            with patch("nblane.core.review_actions.profile_dir", lambda _name: profile), patch(
                "nblane.core.agent_activity.profile_dir",
                lambda _name: profile,
            ), patch(
                "nblane.core.kanban_io.profile_dir",
                lambda _name: profile,
            ):
                result = apply_review_next_action_candidate(
                    "alice",
                    "2026-05-11",
                    "2026-05-14",
                    {
                        "source": "learning",
                        "resource_id": "learn_1",
                        "title": "Reproduce setup",
                    },
                )
                sections = parse_kanban("alice")

        self.assertTrue(result.ok)
        self.assertTrue(
            any(task.title == "Reproduce setup" for task in sections["Queue"])
        )

    def test_public_draft_apply_creates_draft_blog(self) -> None:
        """Public Review candidates create draft posts only."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = _template_profile(Path(tmp_s))
            with patch(
                "nblane.core.public_site.profile_dir",
                lambda _name: profile,
            ), patch(
                "nblane.core.review_actions.profile_dir",
                lambda _name: profile,
            ), patch(
                "nblane.core.agent_activity.profile_dir",
                lambda _name: profile,
            ):
                result = apply_review_public_draft_candidate(
                    "alice",
                    "2026-05-11",
                    "2026-05-14",
                    {
                        "source": "kanban_done",
                        "task_id": "done-public",
                        "title": "Ship public demo",
                        "summary": "demo shipped",
                    },
                )
                self.assertTrue(result.ok)
                self.assertIsNotNone(result.output_path)
                assert result.output_path is not None
                content = result.output_path.read_text(encoding="utf-8")

        self.assertIn("status: draft", content)

    def test_activity_item_can_apply_review_candidate(self) -> None:
        """Agent Activity can apply pending Review-origin items."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = _template_profile(Path(tmp_s))
            with patch("nblane.core.review_actions.profile_dir", lambda _name: profile), patch(
                "nblane.core.agent_activity.profile_dir",
                lambda _name: profile,
            ), patch(
                "nblane.core.kanban_io.profile_dir",
                lambda _name: profile,
            ):
                stored = save_review_candidates_to_activity(
                    "alice",
                    "2026-05-11",
                    "2026-05-14",
                    "next_action",
                    [{"source": "learning", "resource_id": "learn_1", "title": "Queue me"}],
                )[0]
                result = apply_review_activity_item("alice", stored["id"])
                activity = load_agent_activity("alice")

        self.assertTrue(result.ok)
        self.assertEqual(activity["items"][0]["status"], "applied")


KANBAN_FIXTURE = """# alice · Kanban

## Doing

- [ ] Write VLA survey
  - id: kb_doing1

---

## Done

- (empty)

---

## Queue

- [ ] Fix bug A
  - id: kb_queue_a
- [ ] Fix bug B
  - id: kb_queue_b

---

## Someday / Maybe

- (empty)

---
"""


class TestReviewKanbanCandidate(unittest.TestCase):
    """Kanban move candidates apply through the review queue."""

    def _profile_with_kanban(self, tmp_s: str) -> Path:
        profile = _template_profile(Path(tmp_s))
        (profile / "kanban.md").write_text(KANBAN_FIXTURE, encoding="utf-8")
        return profile

    def _patches(self, profile: Path):
        return (
            patch(
                "nblane.core.review_actions.profile_dir",
                lambda _name: profile,
            ),
            patch(
                "nblane.core.agent_activity.profile_dir",
                lambda _name: profile,
            ),
            patch(
                "nblane.core.kanban_io.profile_dir",
                lambda _name: profile,
            ),
        )

    def test_kanban_move_applies_exact_title_match(self) -> None:
        """A move relocates the card and auto-stamps Done metadata."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile_with_kanban(tmp_s)
            patches = self._patches(profile)
            with patches[0], patches[1], patches[2]:
                result = apply_review_kanban_candidate(
                    "alice",
                    {
                        "action": "move",
                        "card_ref": "Write VLA survey",
                        "target_section": "Done",
                        "note": "shipped",
                    },
                )
                sections = parse_kanban("alice")
                activity = load_agent_activity("alice")

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.changed_paths, [profile / "kanban.md"])
        self.assertEqual([t.title for t in sections["Done"]], ["Write VLA survey"])
        self.assertTrue(sections["Done"][0].done)
        self.assertTrue(sections["Done"][0].completed_on)
        self.assertEqual(sections["Doing"], [])
        self.assertEqual(len(sections["Queue"]), 2)
        self.assertEqual(result.activity_item["status"], "applied")
        self.assertEqual(activity["items"][0]["candidate_type"], "kanban_move")

    def test_kanban_move_accepts_unique_substring(self) -> None:
        """A unique substring of the card title resolves the card."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile_with_kanban(tmp_s)
            patches = self._patches(profile)
            with patches[0], patches[1], patches[2]:
                result = apply_review_kanban_candidate(
                    "alice",
                    {
                        "action": "move",
                        "card_ref": "vla survey",
                        "target_section": "Queue",
                    },
                )
                sections = parse_kanban("alice")

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(
            [t.title for t in sections["Queue"]],
            ["Fix bug A", "Fix bug B", "Write VLA survey"],
        )
        self.assertEqual(sections["Doing"], [])

    def test_kanban_move_ambiguous_ref_marks_failed(self) -> None:
        """Ambiguous card_ref fails the item and leaves the board untouched."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile_with_kanban(tmp_s)
            patches = self._patches(profile)
            with patches[0], patches[1], patches[2]:
                result = apply_review_kanban_candidate(
                    "alice",
                    {
                        "action": "move",
                        "card_ref": "Fix bug",
                        "target_section": "Doing",
                    },
                )
                sections = parse_kanban("alice")
                activity = load_agent_activity("alice")

        self.assertFalse(result.ok)
        self.assertIn("ambiguous", result.errors[0])
        self.assertEqual(result.activity_item["status"], "failed")
        self.assertIn("ambiguous", result.activity_item["error"])
        self.assertEqual(len(sections["Queue"]), 2)
        self.assertEqual(sections["Doing"][0].title, "Write VLA survey")
        self.assertEqual(activity["items"][0]["status"], "failed")

    def test_kanban_move_unknown_card_marks_failed(self) -> None:
        """A card_ref with no matches fails the item with a clear error."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile_with_kanban(tmp_s)
            patches = self._patches(profile)
            with patches[0], patches[1], patches[2]:
                result = apply_review_kanban_candidate(
                    "alice",
                    {
                        "action": "move",
                        "card_ref": "No such card",
                        "target_section": "Doing",
                    },
                )

        self.assertFalse(result.ok)
        self.assertIn("no kanban card matches", result.errors[0])
        self.assertEqual(result.activity_item["status"], "failed")

    def test_kanban_move_unknown_section_marks_failed(self) -> None:
        """An unknown target section fails the item with valid choices."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile_with_kanban(tmp_s)
            patches = self._patches(profile)
            with patches[0], patches[1], patches[2]:
                result = apply_review_kanban_candidate(
                    "alice",
                    {
                        "action": "move",
                        "card_ref": "Write VLA survey",
                        "target_section": "Later",
                    },
                )
                sections = parse_kanban("alice")

        self.assertFalse(result.ok)
        self.assertIn("unknown kanban section", result.errors[0])
        self.assertIn("Doing", result.errors[0])
        self.assertEqual(result.activity_item["status"], "failed")
        self.assertEqual(sections["Doing"][0].title, "Write VLA survey")

    def test_kanban_move_same_section_is_noop_apply(self) -> None:
        """Moving to the current section applies with a warning, no write."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile_with_kanban(tmp_s)
            patches = self._patches(profile)
            with patches[0], patches[1], patches[2]:
                result = apply_review_kanban_candidate(
                    "alice",
                    {
                        "action": "move",
                        "card_ref": "Write VLA survey",
                        "target_section": "doing",
                    },
                )

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.changed_paths, [])
        self.assertTrue(any("already in" in w for w in result.warnings))
        self.assertEqual(result.activity_item["status"], "applied")

    def test_kanban_move_dispatches_from_activity_item(self) -> None:
        """apply_review_activity_item routes kanban_move items to the applier."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile_with_kanban(tmp_s)
            patches = self._patches(profile)
            with patches[0], patches[1], patches[2]:
                item = activity_item_from_kanban_candidate(
                    "alice",
                    {
                        "action": "move",
                        "card_ref": "Write VLA survey",
                        "target_section": "Queue",
                    },
                )
                stored = append_activity_item("alice", item)
                result = apply_review_activity_item("alice", stored["id"])
                sections = parse_kanban("alice")
                activity = load_agent_activity("alice")

        self.assertTrue(result.ok, result.errors)
        self.assertIn(
            "Write VLA survey", [t.title for t in sections["Queue"]]
        )
        self.assertEqual(sections["Doing"], [])
        self.assertEqual(activity["items"][0]["status"], "applied")
        self.assertEqual(activity["items"][0]["target_owner"], "kanban")


if __name__ == "__main__":
    unittest.main()
