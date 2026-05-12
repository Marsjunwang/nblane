"""Tests for current goal storage and privacy projections."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.goals import (
    Goal,
    GoalBook,
    current_goal,
    goal_for_agent_context,
    goal_for_public_output,
    goal_for_ui,
    load_goal_book,
    save_goal_book,
)


class TestGoals(unittest.TestCase):
    """Goal YAML round trips and privacy rules."""

    def test_missing_goals_yaml_loads_empty(self) -> None:
        """Old profiles without goals.yaml remain valid."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alice").mkdir()
            with patch("nblane.core.goals.PROFILES_DIR", root):
                book = load_goal_book("alice")

        self.assertEqual(book.profile, "alice")
        self.assertEqual(book.current_goal_id, "")
        self.assertEqual(book.goals, [])
        self.assertIsNone(book.current())

    def test_save_load_round_trip_preserves_fields(self) -> None:
        """Unicode and list fields survive a save/load cycle."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "王军").mkdir()
            book = GoalBook(
                profile="王军",
                current_goal_id="goal_1",
                goals=[
                    Goal(
                        id="goal_1",
                        title="8 周内完成 Agent 项目",
                        label="Agent 项目阶段目标",
                        target="2026-07-07",
                        focus=["写博客", "整理 evidence"],
                        success_criteria=["demo 可运行"],
                        target_skills=["vla", "agent"],
                    )
                ],
            )
            with patch("nblane.core.goals.PROFILES_DIR", root):
                save_goal_book("王军", book)
                loaded = load_goal_book("王军")

        self.assertEqual(loaded.profile, "王军")
        self.assertEqual(loaded.current_goal_id, "goal_1")
        goal = loaded.current()
        self.assertIsNotNone(goal)
        assert goal is not None
        self.assertEqual(goal.title, "8 周内完成 Agent 项目")
        self.assertEqual(goal.focus, ["写博客", "整理 evidence"])
        self.assertEqual(goal.ui_visibility, "discreet")
        self.assertTrue(goal.include_in_agent_context)
        self.assertFalse(goal.include_in_public_output)
        self.assertRegex(loaded.updated, r"^\d{4}-\d{2}-\d{2}$")

    def test_current_goal_missing_or_archived_is_none(self) -> None:
        """The current pointer must resolve to a non-archived goal."""
        missing = GoalBook(
            current_goal_id="missing",
            goals=[Goal(id="goal_1", title="x")],
        )
        archived = GoalBook(
            current_goal_id="goal_1",
            goals=[Goal(id="goal_1", title="x", status="archived")],
        )

        self.assertIsNone(missing.current())
        self.assertIsNone(archived.current())

    def test_invalid_raw_values_are_normalized(self) -> None:
        """Invalid enum and shape values use safe defaults."""
        book = GoalBook.from_dict(
            {
                "profile": "alice",
                "current_goal_id": "g",
                "goals": [
                    {
                        "id": "g",
                        "title": "Goal",
                        "status": "bad",
                        "ui_visibility": "bad",
                        "include_in_agent_context": "yes",
                        "include_in_public_output": "no",
                        "focus": "not-a-list",
                    }
                ],
            }
        )
        goal = book.current()
        self.assertIsNotNone(goal)
        assert goal is not None
        self.assertEqual(goal.status, "active")
        self.assertEqual(goal.ui_visibility, "discreet")
        self.assertEqual(goal.focus, [])
        self.assertTrue(goal.include_in_agent_context)
        self.assertFalse(goal.include_in_public_output)

    def test_ui_projection_respects_visibility(self) -> None:
        """UI projection redacts title/details according to visibility."""
        visible = Goal(
            id="g1",
            title="Sensitive title",
            label="Safe label",
            summary="summary",
            focus=["f1", "f2", "f3", "f4"],
            ui_visibility="visible",
        )
        discreet = Goal(
            id="g2",
            title="Sensitive title",
            label="Safe label",
            ui_visibility="discreet",
        )
        hidden = Goal(
            id="g3",
            title="Sensitive title",
            label="Safe label",
            ui_visibility="hidden",
        )
        private = Goal(
            id="g4",
            title="Sensitive title",
            ui_visibility="private",
        )

        self.assertEqual(goal_for_ui(visible)["title"], "Sensitive title")
        self.assertEqual(goal_for_ui(visible)["focus"], ["f1", "f2", "f3"])
        self.assertNotIn("title", goal_for_ui(discreet))
        self.assertEqual(goal_for_ui(discreet)["label"], "Safe label")
        self.assertNotIn("label", goal_for_ui(hidden))
        self.assertIsNone(goal_for_ui(private))

    def test_private_blocks_agent_and_public_context(self) -> None:
        """Private goals never leave the local editor projection."""
        goal = Goal.from_dict(
            {
                "id": "g",
                "title": "Do not leak",
                "ui_visibility": "private",
                "include_in_agent_context": True,
                "include_in_public_output": True,
            }
        )
        self.assertIsNotNone(goal)
        assert goal is not None
        self.assertFalse(goal.include_in_agent_context)
        self.assertFalse(goal.include_in_public_output)
        self.assertEqual(goal_for_agent_context(goal), "")
        self.assertEqual(goal_for_public_output(goal), "")

    def test_current_goal_loader_accepts_profile_path(self) -> None:
        """Core helpers accept a resolved profile path as well as a name."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "goals.yaml").write_text(
                """
schema_version: "1.0"
profile: alice
current_goal_id: g
goals:
  - id: g
    title: Path based goal
""",
                encoding="utf-8",
            )
            goal = current_goal(profile)

        self.assertIsNotNone(goal)
        assert goal is not None
        self.assertEqual(goal.title, "Path based goal")


if __name__ == "__main__":
    unittest.main()
