"""Tests for Review candidate writeback helpers."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.agent_activity import load_agent_activity
from nblane.core.kanban_io import parse_kanban
from nblane.core.review_actions import (
    apply_review_activity_item,
    apply_review_evidence_candidate,
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


if __name__ == "__main__":
    unittest.main()
