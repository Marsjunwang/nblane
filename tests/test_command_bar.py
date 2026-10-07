"""Tests for the Home command bar: intent routing and confirmed writes."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from nblane.core import command_bar
from nblane.core.command_bar import (
    apply_kanban_add_intent,
    intent_needs_confirmation,
    pending_intent_payload,
    resolve_command_text,
)
from nblane.core.intent import IntentAction
from nblane.core.kanban_io import parse_kanban


def _profile(tmp: Path) -> Path:
    profile = tmp / "alice"
    profile.mkdir()
    (profile / "kanban.md").write_text(
        "# alice · Kanban\n\n"
        "## Doing\n\n"
        "- [ ] Existing task\n"
        "  - id: task_existing\n",
        encoding="utf-8",
    )
    return profile


class TestResolveCommandText(unittest.TestCase):
    """Submit-time routing is pure: write intents pend, never write."""

    def test_kanban_add_pends_without_touching_disk(self) -> None:
        intent = IntentAction(
            kind="kanban.add",
            raw="把X加到Doing 明天前 #robot",
            title="X",
            column="Doing",
            due="2026-09-17",
            tags=["robot"],
            confidence=0.9,
        )
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = _profile(Path(tmp_s))
            before = (profile / "kanban.md").read_text(encoding="utf-8")
            with patch.object(command_bar, "parse_intent", return_value=intent):
                resolution = resolve_command_text("把X加到Doing 明天前 #robot")
            after = (profile / "kanban.md").read_text(encoding="utf-8")

        self.assertEqual(resolution["outcome"], "pending")
        pending = resolution["intent"]
        self.assertEqual(pending["kind"], "kanban.add")
        self.assertEqual(pending["title"], "X")
        self.assertEqual(pending["column"], "Doing")
        self.assertEqual(pending["due"], "2026-09-17")
        self.assertEqual(pending["tags"], ["robot"])
        self.assertTrue(pending["id"].startswith("intent:kanban.add:"))
        # Submit alone must not mutate the board.
        self.assertEqual(before, after)

    def test_evidence_capture_pends(self) -> None:
        resolution = resolve_command_text("记一条证据：完成了 demo 联调")
        self.assertEqual(resolution["outcome"], "pending")
        self.assertEqual(resolution["intent"]["kind"], "evidence.capture")
        self.assertEqual(resolution["intent"]["title"], "完成了 demo 联调")

    def test_navigate_executes_directly(self) -> None:
        nav = resolve_command_text("打开看板")
        self.assertEqual(nav, {"outcome": "navigate", "page": "pages/3_Kanban.py"})

    def test_unknown_resolves_to_help(self) -> None:
        resolution = resolve_command_text("随便一句话")
        self.assertEqual(resolution["outcome"], "help")
        self.assertEqual(resolution["raw"], "随便一句话")

    def test_confirmation_flags_and_deterministic_ids(self) -> None:
        self.assertTrue(intent_needs_confirmation("kanban.add"))
        self.assertTrue(intent_needs_confirmation("evidence.capture"))
        for kind in ("navigate", "unknown"):
            self.assertFalse(intent_needs_confirmation(kind))
        intent = IntentAction(kind="kanban.add", raw="add X", title="X")
        day = date(2026, 9, 16)
        first = pending_intent_payload(intent, today=day)
        second = pending_intent_payload(intent, today=day)
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["id"], "intent:kanban.add:" + first["id"].rsplit(":", 1)[-1])


class TestApplyKanbanAddIntent(unittest.TestCase):
    """The confirmed write re-reads disk and saves through the merge path."""

    def test_confirm_writes_via_save_kanban_with_merge(self) -> None:
        calls: list[dict] = []
        real_save = command_bar.save_kanban_with_merge

        def spy(profile, sections, base_sections, **kwargs):
            calls.append({"base_sections": base_sections, "kwargs": kwargs})
            return real_save(profile, sections, base_sections, **kwargs)

        with tempfile.TemporaryDirectory() as tmp_s:
            profile = _profile(Path(tmp_s))
            with patch.object(command_bar, "save_kanban_with_merge", spy):
                task = apply_kanban_add_intent(
                    profile,
                    {
                        "kind": "kanban.add",
                        "title": "校准数据集",
                        "column": "Doing",
                        "due": "2026-09-17",
                        "tags": ["robot", "sim"],
                    },
                    today=date(2026, 9, 16),
                )
            sections = parse_kanban(profile)
            # Round-trip: the due detail survives re-parsing untouched.
            reread_details = parse_kanban(profile)["Doing"][-1].details

        self.assertEqual(len(calls), 1)
        self.assertIsNone(calls[0]["base_sections"])
        self.assertIsNotNone(task)
        assert task is not None
        self.assertEqual(task.title, "校准数据集")
        self.assertTrue(task.id.startswith("kb_"))
        doing_titles = [t.title for t in sections["Doing"]]
        self.assertEqual(doing_titles, ["Existing task", "校准数据集"])
        new_task = sections["Doing"][-1]
        self.assertEqual(new_task.started_on, "2026-09-16")
        self.assertEqual(new_task.tags, "robot, sim")
        self.assertIn("due: 2026-09-17", new_task.details)
        self.assertEqual(reread_details, ["due: 2026-09-17"])

    def test_column_mapping_and_started_on_only_for_doing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = _profile(Path(tmp_s))
            apply_kanban_add_intent(
                profile, {"title": "Queued task", "column": "Queue"}
            )
            apply_kanban_add_intent(
                profile, {"title": "Someday task", "column": "Someday"}
            )
            sections = parse_kanban(profile)

        self.assertEqual([t.title for t in sections["Queue"]], ["Queued task"])
        self.assertEqual(
            [t.title for t in sections["Someday / Maybe"]], ["Someday task"]
        )
        self.assertIsNone(sections["Queue"][0].started_on)
        self.assertIsNone(sections["Someday / Maybe"][0].started_on)
        self.assertEqual(len(sections["Doing"]), 1)  # only the pre-existing task

    def test_blank_title_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = _profile(Path(tmp_s))
            before = (profile / "kanban.md").read_text(encoding="utf-8")
            result = apply_kanban_add_intent(profile, {"title": "   "})
            after = (profile / "kanban.md").read_text(encoding="utf-8")
        self.assertIsNone(result)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
