"""Tests for modular AI Action / Gateway behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.ai import (
    create_remote_dev_task,
    draft_resume_for_job,
    recommend_research_sources,
    run_ai_action,
)
from nblane.core.ai.actions import AIActionRequest
from nblane.core.ai.backends import DirectLLMBackend, RuleFallbackBackend
from nblane.core.ai.router import get_action_spec, registered_actions


class TestAIGateway(unittest.TestCase):
    """AI Gateway keeps business code off raw provider and harness APIs."""

    def test_mvp_actions_are_registered(self) -> None:
        """First AI Action batch is present in the registry."""

        self.assertEqual(
            set(registered_actions()),
            {
                "research.reading_draft",
                "research.recommend_sources",
                "resume.bullets_from_claims",
                "resume.target_for_job",
                "output.blog_candidate",
                "output.inline_patch",
                "kanban.task_alignment",
                "kanban.subtasks",
                "work.remote_dev_task",
            },
        )

    def test_direct_backend_missing_key_returns_typed_error(self) -> None:
        """Direct LLM backend does not raise when the provider is unconfigured."""

        spec = get_action_spec("research.reading_draft")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="research.reading_draft",
            profile="alice",
            payload={"source": {"id": "src_1", "title": "Paper"}},
        )
        with patch("nblane.core.llm._API_KEY", ""):
            result = DirectLLMBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertFalse(result.ok)
        self.assertEqual(result.backend, "direct_llm")
        self.assertIn("ai_not_configured", result.error)

    def test_rule_fallback_returns_deterministic_result(self) -> None:
        """Rule fallback can provide a usable empty/candidate state."""

        spec = get_action_spec("research.recommend_sources")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="research.recommend_sources",
            profile="alice",
            payload={
                "sources": [
                    {"id": "src_a", "title": "A"},
                    {"id": "src_b", "title": "B"},
                ]
            },
        )
        result = RuleFallbackBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "rule_fallback")
        self.assertEqual(
            result.structured["recommendations"][0]["source_ref"],  # type: ignore[index]
            "src_a",
        )

    def test_gateway_uses_action_default_backend(self) -> None:
        """run_ai_action routes through the action spec backend."""

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
                patch("nblane.core.ai.runs.profile_dir", lambda _name: profile),
            ):
                result = recommend_research_sources(
                    "alice",
                    "robotics",
                    [{"id": "src_1", "title": "OpenVLA"}],
                )

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "workflow_agent")
        self.assertEqual(result.activity_item_id.startswith("act:ai:"), True)

    def test_preferred_backend_unknown_is_explicit_error(self) -> None:
        """Invalid overrides fail clearly instead of silently picking a model."""

        result = run_ai_action(
            "research.recommend_sources",
            {"sources": []},
            profile="",
            preferred_backend="missing_backend",
            require_review=False,
        )

        self.assertFalse(result.ok)
        self.assertIn("routing_error", result.error)
        self.assertIn("missing_backend", result.error)

    def test_json_action_bad_output_returns_validation_error(self) -> None:
        """Business callers never have to parse malformed raw JSON."""

        with (
            patch("nblane.core.llm._API_KEY", "test-key"),
            patch("nblane.core.llm.chat", return_value="not json"),
        ):
            result = run_ai_action(
                "resume.bullets_from_claims",
                {"claims": []},
                profile="",
                require_review=False,
            )

        self.assertFalse(result.ok)
        self.assertEqual(result.backend, "direct_llm")
        self.assertIn("validation_error", result.error)

    def test_typed_resume_helper_returns_traceable_candidate(self) -> None:
        """Typed helpers expose action results without provider details."""

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
                patch("nblane.core.ai.runs.profile_dir", lambda _name: profile),
            ):
                result = draft_resume_for_job(
                    "alice",
                    "Need robotics engineer",
                    claims=[{"id": "claim_1", "text": "Built ROS demo"}],
                    evidence=[{"id": "ev_1"}],
                    projects=[{"id": "proj_1"}],
                )

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "workflow_agent")
        self.assertEqual(result.structured["claim_refs"], ["claim_1"])  # type: ignore[index]
        self.assertEqual(result.structured["evidence_refs"], ["ev_1"])  # type: ignore[index]
        self.assertEqual(result.structured["project_refs"], ["proj_1"])  # type: ignore[index]

    def test_remote_dev_task_creates_candidate_not_code_changes(self) -> None:
        """External agent action creates a task and Activity item only."""

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_tasks.profile_dir", lambda _name: profile),
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
                patch("nblane.core.ai.runs.profile_dir", lambda _name: profile),
            ):
                result = create_remote_dev_task(
                    "alice",
                    "Implement gateway tests",
                    target_harness="opencode",
                    input_refs=["kanban:task_1"],
                )

                from nblane.core.agent_activity import activity_items_for_page
                from nblane.core.agent_tasks import load_agent_tasks

                tasks = load_agent_tasks("alice")["tasks"]
                activity = activity_items_for_page(
                    "alice",
                    {"target_owner": "work"},
                )

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "external_agent")
        self.assertEqual(result.structured["target_harness"], "opencode")  # type: ignore[index]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["activity_item_id"], result.activity_item_id)
        self.assertEqual(activity[0]["kind"], "patch")
        self.assertEqual(activity[0]["changed_paths"], [])


if __name__ == "__main__":
    unittest.main()
