"""Tests for external agent task handoff records."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.agent_tasks import (
    create_agent_task,
    link_activity_item,
    load_agent_tasks,
    render_agent_handoff,
    submit_agent_task_candidate,
    sync_agent_harness_snippet,
    update_agent_task_status,
)


class TestAgentTasks(unittest.TestCase):
    """Codex/OpenCode task handoff stays candidate-first."""

    def test_create_and_link_agent_task(self) -> None:
        """Agent task records persist harness, role, refs, and Activity link."""

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with patch("nblane.core.agent_tasks.profile_dir", lambda _name: profile):
                task = create_agent_task(
                    "alice",
                    target_harness="codex",
                    role="remote_dev",
                    title="Patch the gateway",
                    input_refs=["kanban:task_1"],
                    expected_outputs=["patch_review"],
                    related={"kanban_task_id": "task_1"},
                    action_name="work.remote_dev_task",
                    run_id="airun_1",
                )
                linked = link_activity_item(
                    "alice",
                    task["id"],
                    "act:ai:airun_1",
                )
                loaded = load_agent_tasks("alice")

        self.assertIsNotNone(linked)
        self.assertEqual(len(loaded["tasks"]), 1)
        self.assertEqual(loaded["tasks"][0]["target_harness"], "codex")
        self.assertEqual(loaded["tasks"][0]["role"], "remote_dev")
        self.assertEqual(loaded["tasks"][0]["activity_item_id"], "act:ai:airun_1")

    def test_handoff_renders_review_rules(self) -> None:
        """Rendered handoff is executable context, not silent writeback."""

        task = {
            "id": "agenttask_1",
            "target_harness": "opencode",
            "role": "researcher",
            "title": "Summarize sources",
            "input_refs": ["research:src_1"],
            "expected_outputs": ["source_candidates"],
            "status": "ready",
        }

        body = render_agent_handoff(task, profile="alice")

        self.assertIn("nblane Agent Task Handoff", body)
        self.assertIn("Target harness: opencode", body)
        self.assertIn("research:src_1", body)
        self.assertIn("Produce candidate, patch, or writeback-review artifacts only", body)
        self.assertIn("agent://task/agenttask_1", body)
        self.assertIn("submit_agent_task_candidate", body)

    def test_sync_harness_snippet_mentions_permissions(self) -> None:
        """Harness snippets borrow roles and allow/ask/deny permission framing."""

        body = sync_agent_harness_snippet("codex")

        self.assertIn("nblane Codex Harness", body)
        self.assertIn("remote_dev", body)
        self.assertIn("allow:", body)
        self.assertIn("ask:", body)
        self.assertIn("deny:", body)
        self.assertIn("agent://tasks", body)
        self.assertIn("submit_agent_task_candidate", body)

    def test_invalid_harness_snippet_target_is_rejected(self) -> None:
        """Unknown harness names do not create ambiguous config."""

        with self.assertRaises(ValueError):
            sync_agent_harness_snippet("unknown")

    def test_submit_candidate_updates_task_and_activity(self) -> None:
        """External agent output stays as a reviewable Activity patch."""

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_tasks.profile_dir", lambda _name: profile),
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
            ):
                task = create_agent_task(
                    "alice",
                    target_harness="codex",
                    role="remote_dev",
                    title="Patch the gateway",
                    input_refs=["kanban:task_1"],
                    expected_outputs=["patch_review"],
                    action_name="work.remote_dev_task",
                    run_id="airun_1",
                )
                from nblane.core.agent_activity import (
                    activity_items_for_page,
                    append_activity_item,
                )

                append_activity_item(
                    "alice",
                    {
                        "id": "act:ai:airun_1",
                        "kind": "patch",
                        "candidate_type": "work_remote_dev_task",
                        "source_page": "AI Gateway",
                        "target_owner": "work",
                        "status": "pending",
                        "title": "Patch the gateway",
                        "payload": {"action_result": {"task_id": task["id"]}},
                    },
                )
                link_activity_item("alice", task["id"], "act:ai:airun_1")

                updated = submit_agent_task_candidate(
                    "alice",
                    task["id"],
                    summary="Implemented candidate patch.",
                    changed_paths=["src/nblane/core/ai/gateway.py"],
                    warnings=["Needs review."],
                    result_payload={"tests": "passed"},
                )
                loaded = load_agent_tasks("alice")["tasks"][0]
                activity = activity_items_for_page(
                    "alice",
                    {"target_owner": "work"},
                )[0]

        self.assertIsNotNone(updated)
        self.assertEqual(loaded["status"], "candidate_ready")
        self.assertEqual(loaded["result_summary"], "Implemented candidate patch.")
        self.assertEqual(activity["status"], "pending")
        self.assertEqual(activity["changed_paths"], ["src/nblane/core/ai/gateway.py"])
        self.assertEqual(
            activity["payload"]["agent_task_result"]["result_payload"],
            {"tests": "passed"},
        )

    def test_failed_status_syncs_to_activity(self) -> None:
        """Failed external runs are visible in Agent Activity."""

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_tasks.profile_dir", lambda _name: profile),
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
            ):
                task = create_agent_task(
                    "alice",
                    target_harness="codex",
                    role="remote_dev",
                    title="Patch the gateway",
                    input_refs=["kanban:task_1"],
                    expected_outputs=["patch_review"],
                )
                from nblane.core.agent_activity import (
                    activity_items_for_page,
                    append_activity_item,
                )

                append_activity_item(
                    "alice",
                    {
                        "id": "act:ai:airun_1",
                        "kind": "patch",
                        "candidate_type": "work_remote_dev_task",
                        "source_page": "AI Gateway",
                        "target_owner": "work",
                        "status": "pending",
                        "title": "Patch the gateway",
                    },
                )
                link_activity_item("alice", task["id"], "act:ai:airun_1")

                update_agent_task_status(
                    "alice",
                    task["id"],
                    "failed",
                    error="tests failed",
                    warnings=["Check logs."],
                )
                activity = activity_items_for_page(
                    "alice",
                    {"target_owner": "work"},
                )[0]

        self.assertEqual(activity["status"], "failed")
        self.assertEqual(activity["error"], "tests failed")
        self.assertEqual(activity["warnings"], ["Check logs."])


if __name__ == "__main__":
    unittest.main()
