"""Tests for goal-to-skill alignment helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.gap_llm_router import RouterOutcome
from nblane.core.goal_alignment import (
    ai_match_goal_to_skills,
    manual_goal_skill_link,
    merge_goal_skill_candidates,
    rule_match_goal_to_skills,
)
from nblane.core.goals import Goal, GoalSkillLink


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


class TestGoalAlignment(unittest.TestCase):
    """Alignment candidates reuse Gap Analysis matching primitives."""

    def _profile(self, tmp: Path) -> Path:
        profile = tmp / "alice"
        profile.mkdir()
        _write_yaml(
            profile / "skill-tree.yaml",
            {
                "profile": "alice",
                "schema": "robotics-engineer",
                "nodes": [],
            },
        )
        return profile

    def test_rule_match_returns_schema_candidates(self) -> None:
        """Rule matching scores goal text against schema nodes."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            goal = Goal(
                id="g1",
                title="Build a ROS 2 manipulation demo",
                summary="Use ROS2 nodes, topics, launch files and MoveIt.",
                target_skills=["ros2_basics", "moveit2"],
            )
            candidates = rule_match_goal_to_skills(profile, goal)

        self.assertGreaterEqual(len(candidates), 1)
        ids = {candidate.node_id for candidate in candidates}
        self.assertIn("ros2_basics", ids)
        self.assertTrue(all(candidate.source == "rule" for candidate in candidates))

    def test_ai_match_filters_to_allowed_schema_nodes(self) -> None:
        """AI routing only returns nodes present in the schema index."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            goal = Goal(id="g1", title="Plan a MoveIt manipulation stack")
            with patch(
                "nblane.core.gap_llm_router.route_task_to_nodes",
                return_value=RouterOutcome(
                    ok=True,
                    node_ids=["moveit2", "not_real"],
                    keywords={"moveit2": ["planning/规划"]},
                ),
            ):
                candidates = ai_match_goal_to_skills(profile, goal)

        self.assertEqual([candidate.node_id for candidate in candidates], ["moveit2"])
        self.assertEqual(candidates[0].source, "ai")
        self.assertIn("planning", candidates[0].rationale)

    def test_merge_prefers_ai_order_and_combines_sources(self) -> None:
        """Same node from rule and AI becomes rule+ai."""
        rule = [
            GoalSkillLink("ros2_basics", "ROS 2 Basics", "rule", 3, "rule"),
            GoalSkillLink("moveit2", "MoveIt2", "rule", 2, "rule"),
        ]
        ai = [
            GoalSkillLink("moveit2", "MoveIt2", "ai", 5, "ai"),
            GoalSkillLink("pose_estimation", "Pose", "ai", 4, "ai"),
        ]

        merged = merge_goal_skill_candidates(rule, ai)

        self.assertEqual(
            [candidate.node_id for candidate in merged],
            ["moveit2", "pose_estimation", "ros2_basics"],
        )
        self.assertEqual(merged[0].source, "rule+ai")
        self.assertEqual(merged[0].score, 5)

    def test_manual_link_validates_schema_node(self) -> None:
        """Manual links are only created for real skill nodes."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            link = manual_goal_skill_link(profile, "ros2_basics")
            missing = manual_goal_skill_link(profile, "missing")

        self.assertIsNotNone(link)
        assert link is not None
        self.assertEqual(link.source, "manual")
        self.assertIsNone(missing)


if __name__ == "__main__":
    unittest.main()
