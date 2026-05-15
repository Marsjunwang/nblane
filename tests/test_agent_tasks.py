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
    sync_agent_harness_snippet,
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

    def test_sync_harness_snippet_mentions_permissions(self) -> None:
        """Harness snippets borrow roles and allow/ask/deny permission framing."""

        body = sync_agent_harness_snippet("codex")

        self.assertIn("nblane Codex Harness", body)
        self.assertIn("remote_dev", body)
        self.assertIn("allow:", body)
        self.assertIn("ask:", body)
        self.assertIn("deny:", body)

    def test_invalid_harness_snippet_target_is_rejected(self) -> None:
        """Unknown harness names do not create ambiguous config."""

        with self.assertRaises(ValueError):
            sync_agent_harness_snippet("unknown")


if __name__ == "__main__":
    unittest.main()
