"""Tests for MCP-facing agent task resources and tools."""

from __future__ import annotations

import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

from nblane.core.agent_tasks import create_agent_task, link_activity_item


class TestMcpAgentTasks(unittest.TestCase):
    """MCP exposes external-agent handoff and draft-first writeback."""

    @unittest.skipUnless(find_spec("mcp"), "mcp dependency is not installed")
    def test_agent_task_resources_render_handoff(self) -> None:
        """MCP helpers expose task lists and canonical handoff packets."""

        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with patch("nblane.core.agent_tasks.profile_dir", lambda _name: profile):
                task = create_agent_task(
                    "alice",
                    target_harness="codex",
                    role="remote_dev",
                    title="Patch gateway",
                    input_refs=["kanban:task_1"],
                    expected_outputs=["patch_review"],
                )
                listing = mcp_server.build_agent_tasks_text("alice")
                handoff = mcp_server.build_agent_task_handoff_text(
                    "alice",
                    task["id"],
                )

        self.assertIn(task["id"], listing)
        self.assertIn("agent://task/", listing)
        self.assertIn("nblane Agent Task Handoff", handoff)
        self.assertIn("submit_agent_task_candidate", handoff)
        self.assertIn("Agent Task YAML", handoff)

    @unittest.skipUnless(find_spec("mcp"), "mcp dependency is not installed")
    def test_submit_tool_updates_candidate_and_activity(self) -> None:
        """MCP tool writes result metadata to task and Activity only."""

        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_tasks.profile_dir", lambda _name: profile),
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
            ):
                task = create_agent_task(
                    "alice",
                    target_harness="codex",
                    role="remote_dev",
                    title="Patch gateway",
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
                        "title": "Patch gateway",
                    },
                )
                link_activity_item("alice", task["id"], "act:ai:airun_1")

                output = mcp_server.tool_submit_agent_task_candidate(
                    task["id"],
                    "Candidate patch ready.",
                    changed_paths=["src/nblane/mcp_server.py"],
                    warnings=["Review patch."],
                    result_payload={"tests": "ok"},
                )
                activity = activity_items_for_page(
                    "alice",
                    {"target_owner": "work"},
                )[0]

        self.assertIn("OK: candidate submitted", output)
        self.assertEqual(activity["status"], "pending")
        self.assertEqual(activity["changed_paths"], ["src/nblane/mcp_server.py"])
        self.assertEqual(
            activity["payload"]["agent_task_result"]["result_payload"],
            {"tests": "ok"},
        )


if __name__ == "__main__":
    unittest.main()
