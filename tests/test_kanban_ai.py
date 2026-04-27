"""Tests for kanban AI service helpers."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from nblane.core.kanban_ai import (
    KanbanSubtaskProposal,
    analyze_kanban_task_gap,
    apply_kanban_subtask_proposals,
    format_kanban_task_for_ai,
    generate_kanban_subtask_proposals,
)
from nblane.core.models import GapResult, KanbanSubtask, KanbanTask


class TestKanbanAi(unittest.TestCase):
    """Kanban AI helpers stay pure until apply."""

    def test_format_kanban_task_for_ai_includes_context(self) -> None:
        """Task fields, subtasks, and details are rendered for prompts."""
        task = KanbanTask(
            title="Ship VLA demo",
            id="task-1",
            context="robot arm",
            why="portfolio evidence",
            outcome="repeatable demo",
            blocked_by="dataset",
            subtasks=[
                KanbanSubtask("Collect episodes", done=True),
                KanbanSubtask("Train policy"),
            ],
            details=["Use OpenVLA baseline"],
        )

        out = format_kanban_task_for_ai(task)

        self.assertIn("Title: Ship VLA demo", out)
        self.assertIn("Task id: task-1", out)
        self.assertIn("Context: robot arm", out)
        self.assertIn("- [x] Collect episodes", out)
        self.assertIn("- [ ] Train policy", out)
        self.assertIn("- Use OpenVLA baseline", out)

    @patch("nblane.core.kanban_ai.gap.analyze")
    def test_analyze_locates_by_task_id_and_disables_persist(
        self, mock_analyze
    ) -> None:
        """Gap analysis uses stable task ids and default no persistence."""
        mock_analyze.return_value = GapResult(task="ok")
        sections = {
            "Doing": [
                KanbanTask(title="Wrong", id="task-a"),
                KanbanTask(title="Right", id="task-b"),
            ]
        }

        result = analyze_kanban_task_gap("template", sections, "task-b")

        self.assertEqual(result.task, "ok")
        mock_analyze.assert_called_once()
        args, kwargs = mock_analyze.call_args
        self.assertEqual(args[0], "template")
        self.assertIn("Title: Right", args[1])
        self.assertEqual(args[2], None)
        self.assertFalse(kwargs["persist_router_keywords"])

    def test_analyze_missing_task_returns_gap_error(self) -> None:
        """Missing ids produce a structured GapResult error."""
        result = analyze_kanban_task_gap(
            "template",
            {"Doing": [KanbanTask(title="A", id="a")]},
            "missing",
        )

        self.assertEqual(result.error_key, "task_not_found")
        self.assertIn("missing", result.error or "")

    @patch("nblane.core.kanban_ai.llm.chat")
    @patch("nblane.core.kanban_ai.gap.analyze")
    def test_generate_returns_drafts_without_mutating_board(
        self, mock_analyze, mock_chat
    ) -> None:
        """Generation parses JSON proposals but does not append subtasks."""
        mock_analyze.return_value = GapResult(
            task="task",
            closure=[
                {
                    "id": "linux_basics",
                    "label": "Linux",
                    "status": "learning",
                    "is_gap": True,
                }
            ],
            gaps=["linux_basics"],
            next_steps=["Advance linux"],
        )
        mock_chat.return_value = """
```json
{
  "subtasks": [
    {
      "title": "Write reproduction notes",
      "reason": "Creates evidence",
      "gap_node_id": "linux_basics"
    },
    {
      "title": "Ignore unknown node",
      "reason": "Bad id",
      "gap_node_id": "made_up"
    }
  ]
}
```
"""
        sections = {
            "Doing": [
                KanbanTask(
                    title="Reproduce baseline",
                    id="task-1",
                    subtasks=[KanbanSubtask("Keep existing")],
                )
            ]
        }

        proposals = generate_kanban_subtask_proposals(
            "template",
            sections,
            "task-1",
        )

        self.assertEqual(
            [proposal.title for proposal in proposals],
            ["Write reproduction notes", "Ignore unknown node"],
        )
        self.assertEqual(proposals[0].gap_node_id, "linux_basics")
        self.assertEqual(proposals[1].gap_node_id, "")
        self.assertEqual(
            [st.title for st in sections["Doing"][0].subtasks],
            ["Keep existing"],
        )
        mock_chat.assert_called_once()
        _, kwargs = mock_analyze.call_args
        self.assertFalse(kwargs["persist_router_keywords"])

    def test_apply_appends_without_overwriting_or_mutating(self) -> None:
        """Apply copies the board, preserves existing state, and dedupes."""
        sections = {
            "Doing": [
                KanbanTask(
                    title="Task",
                    id="task-1",
                    subtasks=[
                        KanbanSubtask("Keep existing", done=True),
                    ],
                )
            ],
            "Queue": [KanbanTask(title="Other", id="task-2")],
        }
        proposals = [
            KanbanSubtaskProposal(
                title="Keep existing",
                task_id="task-1",
            ),
            KanbanSubtaskProposal(
                title="New evidence note",
                task_id="task-1",
            ),
            KanbanSubtaskProposal(
                title="Wrong task",
                task_id="task-2",
            ),
            KanbanSubtaskProposal(
                title="Global suggestion",
            ),
        ]

        out = apply_kanban_subtask_proposals(
            sections,
            "task-1",
            proposals,
        )

        original_task = sections["Doing"][0]
        updated_task = out["Doing"][0]
        self.assertIsNot(original_task, updated_task)
        self.assertEqual(
            [st.title for st in original_task.subtasks],
            ["Keep existing"],
        )
        self.assertEqual(
            [(st.title, st.done) for st in updated_task.subtasks],
            [
                ("Keep existing", True),
                ("New evidence note", False),
                ("Global suggestion", False),
            ],
        )
        self.assertEqual(out["Queue"][0].subtasks, [])


if __name__ == "__main__":
    unittest.main()
