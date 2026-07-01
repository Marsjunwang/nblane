"""Tests for AI-backed profile ingest prompts."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from nblane.core.models import KanbanTask
from nblane.core.profile_ingest_llm import (
    _system_prompt_kanban_en,
    _system_prompt_kanban_zh,
    ingest_kanban_done_json,
)


class TestKanbanPromptGrading(unittest.TestCase):
    """Kanban Done prompt asks the model to pre-grade evidence."""

    def test_prompt_requests_strength_and_confidence(self) -> None:
        for prompt in (_system_prompt_kanban_zh(), _system_prompt_kanban_en()):
            self.assertIn("strength", prompt)
            self.assertIn("confidence", prompt)
            # Strength value domain must be spelled out so the model stays
            # inside the parser's whitelist.
            self.assertIn("high_trust", prompt)

    def test_prompt_forbids_kanban_ids_in_evidence_refs(self) -> None:
        """Kanban task ids must be steered to kanban_refs, not evidence_refs."""
        for prompt in (_system_prompt_kanban_zh(), _system_prompt_kanban_en()):
            self.assertIn("kb_", prompt)
            self.assertIn("kanban:", prompt)
            self.assertIn("kanban_refs", prompt)


class TestProfileIngestLlm(unittest.TestCase):
    """Kanban Done ingest can swap AI backends."""

    def test_kanban_done_ingest_uses_preview_llm_budget(self) -> None:
        """Done AI preview gets a longer timeout and bounded output budget."""

        with (
            patch(
                "nblane.core.profile_ingest_llm.llm_client.is_configured",
                return_value=True,
            ),
            patch(
                "nblane.core.profile_ingest_llm._load_schema_index_for_profile",
                return_value=("robotics", {"vla": {"label": "VLA"}}),
            ),
            patch(
                "nblane.core.profile_ingest_llm.load_evidence_pool_raw",
                return_value={},
            ),
            patch(
                "nblane.core.profile_ingest_llm.load_skill_tree_raw",
                return_value={},
            ),
            patch(
                "nblane.core.profile_ingest_llm.pool_tree_summaries_for_prompt",
                return_value=("(empty)", "(empty)"),
            ),
            patch(
                "nblane.core.profile_ingest_llm._kanban_done_llm_timeout_seconds",
                return_value=222.0,
            ),
            patch(
                "nblane.core.profile_ingest_llm._kanban_done_llm_max_tokens",
                return_value=333,
            ) as max_tokens,
            patch(
                "nblane.core.profile_ingest_llm.llm_client.chat",
                return_value='{"evidence_entries": [], "node_updates": []}',
            ) as chat,
        ):
            patch_json, error = ingest_kanban_done_json(
                "alice",
                [KanbanTask(title="Finish VLA memory review", id="task-1")],
                goal_context="Robotics demo",
                ai_backend="llm",
            )

        self.assertIsNone(error)
        self.assertEqual(patch_json, {"evidence_entries": [], "node_updates": []})
        self.assertEqual(chat.call_args.kwargs["timeout"], 222.0)
        self.assertEqual(chat.call_args.kwargs["max_tokens"], 333)
        max_tokens.assert_called_once_with(1)

    def test_kanban_done_ingest_can_use_codex_without_llm_config(self) -> None:
        """Codex backend bypasses LLM config and returns parsed JSON."""

        result = SimpleNamespace(
            ok=True,
            output='{"evidence_entries": [], "node_updates": []}',
            error="",
        )
        with (
            patch(
                "nblane.core.profile_ingest_llm.llm_client.is_configured",
                return_value=False,
            ),
            patch(
                "nblane.core.profile_ingest_llm._load_schema_index_for_profile",
                return_value=("robotics", {"vla": {"label": "VLA"}}),
            ),
            patch(
                "nblane.core.profile_ingest_llm.load_evidence_pool_raw",
                return_value={},
            ),
            patch(
                "nblane.core.profile_ingest_llm.load_skill_tree_raw",
                return_value={},
            ),
            patch(
                "nblane.core.profile_ingest_llm.pool_tree_summaries_for_prompt",
                return_value=("(empty)", "(empty)"),
            ),
            patch(
                "nblane.core.codex_adapter.run_readonly_codex_prompt",
                return_value=result,
            ) as run,
        ):
            patch_json, error = ingest_kanban_done_json(
                "alice",
                [KanbanTask(title="Finish VLA memory review", id="task-1")],
                goal_context="Robotics demo",
                ai_backend="codex",
            )

        self.assertIsNone(error)
        self.assertEqual(patch_json, {"evidence_entries": [], "node_updates": []})
        prompt = run.call_args.args[1]
        self.assertIn("read-only AI backend", prompt)
        self.assertIn("Finish VLA memory review", prompt)
        self.assertIn("Robotics demo", prompt)


if __name__ == "__main__":
    unittest.main()
