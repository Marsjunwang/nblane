"""Tests for MCP-facing agent task resources and tools."""

from __future__ import annotations

import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

from nblane.core.agent_tasks import create_agent_task


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
        self.assertIn("update_agent_task_status", handoff)
        self.assertNotIn("submit_agent_task_candidate", handoff)
        self.assertIn("Agent Task YAML", handoff)


if __name__ == "__main__":
    unittest.main()
