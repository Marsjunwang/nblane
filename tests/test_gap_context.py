"""Tests for Gap Analysis context-source options."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from nblane.core.gap_context import default_gap_context_key, gap_context_options


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


class TestGapContext(unittest.TestCase):
    """Goal privacy and kanban task context stay explicit."""

    def test_private_goal_is_not_an_option_and_task_body_is_rich(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            _write_yaml(
                profile / "goals.yaml",
                {
                    "current_goal_id": "g1",
                    "goals": [
                        {
                            "id": "g1",
                            "title": "Secret",
                            "ui_visibility": "private",
                            "include_in_agent_context": True,
                        }
                    ],
                },
            )
            (profile / "kanban.md").write_text(
                "# alice · Kanban\n\n"
                "## Doing\n\n"
                "- [ ] Ship demo\n"
                "  - id: task_demo\n"
                "  - context: robot eval\n"
                "  - outcome: metrics table\n"
                "  - [ ] Run baseline\n",
                encoding="utf-8",
            )

            options = gap_context_options(profile)

        self.assertNotIn("current_goal", {option.kind for option in options})
        task = next(option for option in options if option.kind == "kanban_task")
        self.assertIn("Context: robot eval", task.body)
        self.assertIn("Outcome: metrics table", task.body)
        self.assertIn("Run baseline", task.body)
        self.assertEqual(default_gap_context_key(options), task.key)

    def test_agent_context_goal_is_available_when_no_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            _write_yaml(
                profile / "goals.yaml",
                {
                    "current_goal_id": "g1",
                    "goals": [
                        {
                            "id": "g1",
                            "title": "OpenVLA demo",
                            "ui_visibility": "visible",
                            "include_in_agent_context": True,
                            "focus": ["Run eval"],
                        }
                    ],
                },
            )

            options = gap_context_options(profile)

        goal = next(option for option in options if option.kind == "current_goal")
        self.assertIn("OpenVLA demo", goal.body)
        self.assertEqual(default_gap_context_key(options), goal.key)


if __name__ == "__main__":
    unittest.main()

