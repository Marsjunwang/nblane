"""MCP write tools follow the agent write policy (direct + undo, chat confirm).

Uses a tmp profile; real profiles/ and the real agent state dir are never
touched (NBLANE_AGENT_STATE_DIR points into the tmp dir).
"""

from __future__ import annotations

import os
import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core import agent_policy
from nblane.core.kanban_io import parse_kanban, render_kanban
from nblane.core.models import KanbanTask
from tests.test_web_api_agent_writeback import _write_profile

_SKIP_NO_MCP = unittest.skipUnless(find_spec("mcp"), "mcp dependency is not installed")


def _titles(profile: Path) -> dict[str, list[str]]:
    return {section: [t.title for t in tasks] for section, tasks in parse_kanban(profile).items()}


@_SKIP_NO_MCP
class McpPolicyTestBase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.root = self.tmp / "profiles"
        self.profile = _write_profile(self.root)
        from nblane import mcp_server

        self.mcp = mcp_server
        patchers = [
            patch("nblane.core.profile_io.PROFILES_DIR", self.root),
            patch("nblane.core.io.PROFILES_DIR", self.root),
            patch("nblane.core.project_board.PROFILES_DIR", self.root),
            patch.object(mcp_server, "resolve_active_profile", lambda: ("alice", None)),
            patch("nblane.core.git_backup.record_change"),
            patch.dict(
                os.environ,
                {
                    "NBLANE_AGENT_STATE_DIR": str(self.tmp / "agent-state"),
                    "NBLANE_MCP_ACTOR": "muse",
                },
            ),
        ]
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def undo(self, journal_id: str) -> dict:
        result = self.mcp.tool_undo_action(journal_id)
        self.assertTrue(result["ok"], result)
        return result


class TestDirectWrites(McpPolicyTestBase):
    def test_add_card_is_direct_and_undoable(self) -> None:
        result = self.mcp.tool_add_kanban_card("Buy milk", section="doing")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["section"], "Doing")
        self.assertIn("Buy milk", _titles(self.profile)["Doing"])
        card = next(t for t in parse_kanban(self.profile)["Doing"] if t.title == "Buy milk")
        self.assertTrue(card.started_on)

        recent = self.mcp.tool_recent_actions()
        self.assertEqual(recent["entries"][0]["id"], result["journal_id"])
        self.assertEqual(recent["entries"][0]["actor"], "muse")
        self.assertEqual(recent["entries"][0]["status"], "undoable")
        self.undo(result["journal_id"])
        self.assertNotIn("Buy milk", _titles(self.profile).get("Doing", []))
        again = self.mcp.tool_undo_action(result["journal_id"])
        self.assertEqual(again["code"], "journal_entry_already_undone")

    def test_move_applies_directly_with_legacy_alias(self) -> None:
        moved = self.mcp.tool_submit_kanban_candidate("move", "Card One", target_section="Doing")
        self.assertTrue(moved["ok"], moved)
        self.assertEqual(moved["from_section"], "Queue")
        self.assertIn("Card One", _titles(self.profile)["Doing"])
        noop = self.mcp.tool_move_kanban_card("taskQ", "doing")
        self.assertTrue(noop["warnings"])
        self.assertEqual(noop["journal_id"], "")
        self.undo(moved["journal_id"])
        self.assertEqual(_titles(self.profile)["Queue"], ["Card One"])

    def test_move_errors_are_payloads(self) -> None:
        self.assertIn("unknown section", self.mcp.tool_move_kanban_card("Card One", "Someday")["error"])
        self.assertIn("target_section is required", self.mcp.tool_submit_kanban_candidate("move", "Card One")["error"])
        self.assertIn("unsupported action", self.mcp.tool_submit_kanban_candidate("delete", "Card One")["error"])
        self.assertIn("no kanban card", self.mcp.tool_move_kanban_card("nope", "Doing")["error"])
        self.assertEqual(self.mcp.tool_recent_actions()["entries"], [])

    def test_checkin_undo(self) -> None:
        result = self.mcp.tool_add_checkin("exercise", summary="swim")
        self.assertTrue(result["ok"], result)
        log = yaml.safe_load((self.profile / "activity-log.yaml").read_text(encoding="utf-8"))
        self.assertIn(result["checkin_id"], [c["id"] for c in log["checkins"]])
        self.undo(result["journal_id"])
        log = yaml.safe_load((self.profile / "activity-log.yaml").read_text(encoding="utf-8"))
        self.assertNotIn(result["checkin_id"], [c["id"] for c in log["checkins"]])

    def test_capture_inbox_is_journaled(self) -> None:
        result = self.mcp.tool_capture_inbox("Read the SLAM paper")
        self.assertTrue(result["ok"], result)
        self.undo(result["journal_id"])
        raw = yaml.safe_load((self.profile / "inbox.yaml").read_text(encoding="utf-8")) or {}
        self.assertNotIn("Read the SLAM paper", [i.get("title") for i in raw.get("items") or []])

    def test_growth_log_undo_restores_skill_md(self) -> None:
        before = (self.profile / "SKILL.md").read_text(encoding="utf-8")
        text = self.mcp.tool_append_growth_log("Shipped the arm demo")
        self.assertTrue(text.startswith("OK:"), text)
        self.assertIn("Shipped the arm demo", (self.profile / "SKILL.md").read_text(encoding="utf-8"))
        journal_id = text.split("undo_action('")[1].split("'")[0]
        self.undo(journal_id)
        self.assertEqual((self.profile / "SKILL.md").read_text(encoding="utf-8"), before)

    def test_method_draft_undo_removes_new_file(self) -> None:
        text = self.mcp.tool_crystallize_method_draft("Arm Demo", "steps")
        draft = self.profile / "methods" / "arm-demo_draft.md"
        self.assertTrue(draft.exists(), text)
        journal_id = text.split("undo_action('")[1].split("'")[0]
        self.undo(journal_id)
        self.assertFalse(draft.exists())

    def test_cards_without_ids_are_not_journaled_as_created(self) -> None:
        sections = {"Queue": [KanbanTask(title="Legacy card")]}
        (self.profile / "kanban.md").write_text(render_kanban("alice", sections), encoding="utf-8")
        result = self.mcp.tool_add_kanban_card("New card")
        self.undo(result["journal_id"])
        self.assertEqual(_titles(self.profile)["Queue"], ["Legacy card"])


class TestConfirmation(McpPolicyTestBase):
    def test_delete_needs_confirmation_shared_across_processes(self) -> None:
        first = self.mcp.tool_delete_kanban_card("Card One")
        self.assertFalse(first["ok"])
        self.assertTrue(first["confirmation_required"])
        self.assertEqual(first["summary"], "删除任务「Card One」")
        self.assertIn("Card One", _titles(self.profile)["Queue"])

        # A sibling MCP process sees the token: it lives in the shared file.
        store = agent_policy.FileConfirmStore(self.tmp / "agent-state" / "mcp-confirmations.json")
        with store.edit() as table:
            self.assertIn(first["confirm_id"], table)

        done = self.mcp.tool_delete_kanban_card("Card One", confirm_id=first["confirm_id"])
        self.assertTrue(done["ok"], done)
        self.assertNotIn("Card One", _titles(self.profile).get("Queue", []))
        self.assertEqual(self.mcp.tool_recent_actions()["entries"][0]["tier"], "T2")
        self.undo(done["journal_id"])
        self.assertEqual(_titles(self.profile)["Queue"], ["Card One"])

    def test_confirmation_is_bound_to_the_call(self) -> None:
        self.mcp.tool_add_kanban_card("Other")
        token = self.mcp.tool_delete_kanban_card("Card One")["confirm_id"]
        other = self.mcp.tool_delete_kanban_card("Other", confirm_id=token)
        self.assertTrue(other["confirmation_required"])
        self.assertTrue(other["invalid_confirm_id"])
        self.assertIn("Other", _titles(self.profile)["Queue"])

    def test_failed_confirmed_call_refunds_token(self) -> None:
        token = self.mcp.tool_delete_kanban_card("ghost")["confirm_id"]
        failed = self.mcp.tool_delete_kanban_card("ghost", confirm_id=token)
        self.assertFalse(failed["ok"])
        self.assertIn("no kanban card", failed["error"])
        store = agent_policy.FileConfirmStore(self.tmp / "agent-state" / "mcp-confirmations.json")
        with store.edit() as table:
            self.assertIn(token, table)

    def test_skill_evidence_needs_confirmation(self) -> None:
        first = self.mcp.tool_log_skill_evidence("slam_basics", "Ran ORB-SLAM3")
        self.assertTrue(first.startswith("CONFIRM REQUIRED"), first)
        tree = yaml.safe_load((self.profile / "skill-tree.yaml").read_text(encoding="utf-8"))
        node = next(n for n in tree["nodes"] if n["id"] == "slam_basics")
        self.assertFalse(node.get("evidence"))
        token = first.split("confirm_id=")[1].split()[0]
        done = self.mcp.tool_log_skill_evidence("slam_basics", "Ran ORB-SLAM3", confirm_id=token)
        self.assertTrue(done.startswith("OK:"), done)
        journal_id = done.split("undo_action('")[1].split("'")[0]
        self.undo(journal_id)
        tree = yaml.safe_load((self.profile / "skill-tree.yaml").read_text(encoding="utf-8"))
        node = next(n for n in tree["nodes"] if n["id"] == "slam_basics")
        self.assertFalse(node.get("evidence"))


class TestJournalFileKind(unittest.TestCase):
    def test_file_kind_stays_inside_profile(self) -> None:
        from nblane.core import agent_journal

        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "alice"
            pdir.mkdir()
            for bad in ("../escape.md", "", "/etc/passwd"):
                with self.assertRaises(ValueError):
                    agent_journal.snapshot(pdir, [agent_journal.file_kind(bad)])


if __name__ == "__main__":
    unittest.main()
