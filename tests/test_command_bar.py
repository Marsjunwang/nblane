"""Tests for the Home command bar: intent routing and confirmed writes."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import app as home_app

from nblane.core import command_bar
from nblane.core.command_bar import (
    apply_kanban_add_intent,
    intent_needs_confirmation,
    pending_intent_payload,
    resolve_command_text,
)
from nblane.core.intent import IntentAction
from nblane.core.kanban_io import parse_kanban
from nblane.core.models import KanbanTask


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

    def test_navigate_and_review_execute_directly(self) -> None:
        nav = resolve_command_text("打开看板")
        self.assertEqual(nav, {"outcome": "navigate", "page": "pages/3_Kanban.py"})
        weekly = resolve_command_text("这周做了什么")
        self.assertEqual(
            weekly, {"outcome": "navigate", "page": "pages/8_Review.py"}
        )

    def test_unknown_resolves_to_help(self) -> None:
        resolution = resolve_command_text("随便一句话")
        self.assertEqual(resolution["outcome"], "help")
        self.assertEqual(resolution["raw"], "随便一句话")

    def test_confirmation_flags_and_deterministic_ids(self) -> None:
        self.assertTrue(intent_needs_confirmation("kanban.add"))
        self.assertTrue(intent_needs_confirmation("evidence.capture"))
        for kind in ("navigate", "review.weekly_summary", "unknown"):
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


class TestCommandBarEventHandlers(unittest.TestCase):
    """app.py handler branches: stash/confirm/discard/navigate semantics."""

    def setUp(self) -> None:
        self.profile = "cmdbar_test_profile"
        self.pending_key = home_app._command_bar_pending_key(self.profile)
        self.help_key = home_app._command_bar_help_key(self.profile)
        self._event_seq = 0

    def tearDown(self) -> None:
        for key in (self.pending_key, self.help_key, f"_home_dashboard_event_{self.profile}"):
            home_app.st.session_state.pop(key, None)

    def _event(self, action: str, payload: dict) -> dict:
        self._event_seq += 1
        return {
            "action": action,
            "event_id": f"test-{self.profile}-{self._event_seq}",
            "payload": payload,
        }

    def test_submit_write_intent_stashes_pending_and_writes_nothing(self) -> None:
        pending = {
            "id": "intent:kanban.add:abc123",
            "kind": "kanban.add",
            "title": "X",
            "column": "Doing",
            "due": "",
            "tags": [],
            "raw": "add X",
        }
        with patch.object(
            home_app,
            "resolve_command_text",
            return_value={"outcome": "pending", "intent": pending},
        ), patch.object(home_app, "apply_kanban_add_intent") as apply_mock:
            handled = home_app._handle_home_dashboard_event(
                self._event("command_bar_submit", {"text": "add X"}),
                self.profile,
            )
        self.assertTrue(handled)
        self.assertEqual(home_app.st.session_state.get(self.pending_key), pending)
        apply_mock.assert_not_called()  # submit never writes

    def test_submit_navigate_switches_page_without_pending(self) -> None:
        with patch.object(
            home_app,
            "resolve_command_text",
            return_value={"outcome": "navigate", "page": "pages/3_Kanban.py"},
        ), patch.object(home_app.st, "switch_page") as nav_mock:
            handled = home_app._handle_home_dashboard_event(
                self._event("command_bar_submit", {"text": "打开看板"}),
                self.profile,
            )
        self.assertTrue(handled)
        nav_mock.assert_called_once_with("pages/3_Kanban.py")
        self.assertIsNone(home_app.st.session_state.get(self.pending_key))

    def test_submit_unknown_sets_one_shot_help_flag(self) -> None:
        with patch.object(
            home_app,
            "resolve_command_text",
            return_value={"outcome": "help", "raw": "???"},
        ):
            handled = home_app._handle_home_dashboard_event(
                self._event("command_bar_submit", {"text": "???"}),
                self.profile,
            )
        self.assertTrue(handled)
        self.assertTrue(home_app.st.session_state.get(self.help_key))
        self.assertIsNone(home_app.st.session_state.get(self.pending_key))

    def test_confirm_runs_merge_write_and_clears_pending(self) -> None:
        pending = {
            "id": "intent:kanban.add:abc123",
            "kind": "kanban.add",
            "title": "校准数据集",
            "column": "Doing",
            "due": "2026-09-17",
            "tags": ["robot"],
            "raw": "raw",
        }
        home_app.st.session_state[self.pending_key] = pending
        with patch.object(
            home_app,
            "apply_kanban_add_intent",
            return_value=KanbanTask(title="校准数据集", id="kb_new1"),
        ) as apply_mock, patch.object(
            home_app, "refresh_file_snapshots"
        ) as refresh_mock, patch.object(
            home_app, "stash_git_backup_results"
        ), patch.object(home_app, "clear_web_cache"), patch.object(
            home_app.st, "toast"
        ) as toast_mock:
            handled = home_app._handle_home_dashboard_event(
                self._event(
                    "command_bar_confirm", {"intent_id": "intent:kanban.add:abc123"}
                ),
                self.profile,
            )
        self.assertTrue(handled)
        apply_mock.assert_called_once_with(self.profile, pending)
        refresh_mock.assert_called_once()
        toast_mock.assert_called_once()
        self.assertIsNone(home_app.st.session_state.get(self.pending_key))

    def test_confirm_evidence_capture_reuses_capture_channel(self) -> None:
        pending = {
            "id": "intent:evidence.capture:def456",
            "kind": "evidence.capture",
            "title": "完成了 demo 联调",
            "column": "Doing",
            "due": "",
            "tags": [],
            "raw": "raw",
        }
        home_app.st.session_state[self.pending_key] = pending
        with patch.object(
            home_app, "_capture_home_research_source"
        ) as capture_mock:
            handled = home_app._handle_home_dashboard_event(
                self._event(
                    "command_bar_confirm",
                    {"intent_id": "intent:evidence.capture:def456"},
                ),
                self.profile,
            )
        self.assertTrue(handled)
        capture_mock.assert_called_once_with(
            self.profile,
            {"title": "完成了 demo 联调", "type": "note"},
            capture_event="command_bar",
        )
        self.assertIsNone(home_app.st.session_state.get(self.pending_key))

    def test_confirm_id_mismatch_keeps_pending(self) -> None:
        pending = {"id": "intent:kanban.add:abc123", "kind": "kanban.add", "title": "X"}
        home_app.st.session_state[self.pending_key] = pending
        with patch.object(home_app, "apply_kanban_add_intent") as apply_mock:
            handled = home_app._handle_home_dashboard_event(
                self._event("command_bar_confirm", {"intent_id": "intent:kanban.add:other"}),
                self.profile,
            )
        self.assertTrue(handled)
        apply_mock.assert_not_called()
        self.assertEqual(home_app.st.session_state.get(self.pending_key), pending)

    def test_discard_clears_pending_without_writing(self) -> None:
        home_app.st.session_state[self.pending_key] = {
            "id": "intent:kanban.add:abc123",
            "kind": "kanban.add",
            "title": "X",
        }
        with patch.object(home_app, "apply_kanban_add_intent") as apply_mock:
            handled = home_app._handle_home_dashboard_event(
                self._event("command_bar_discard", {"intent_id": "intent:kanban.add:abc123"}),
                self.profile,
            )
        self.assertTrue(handled)
        apply_mock.assert_not_called()
        self.assertIsNone(home_app.st.session_state.get(self.pending_key))


if __name__ == "__main__":
    unittest.main()
