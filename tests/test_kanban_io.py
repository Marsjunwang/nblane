"""Tests for kanban.md parse/render."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from nblane.core.kanban_io import (
    KANBAN_BOARD_SECTIONS,
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
    apply_kanban_reorder,
    ensure_kanban_task_ids,
    kanban_snapshot_to_moves,
)
from nblane.core.io import (
    append_kanban_archive,
    parse_kanban,
    render_kanban,
    save_kanban,
)
from nblane.core.models import KanbanSubtask, KanbanTask


class _FixedDate(date):
    """Stable date for auto-date tests."""

    @classmethod
    def today(cls) -> "_FixedDate":
        return cls(2026, 4, 27)


class TestKanbanParseRender(unittest.TestCase):
    """Round-trip structured kanban tasks."""

    def _parse_markdown(
        self,
        profile: str,
        markdown: str,
    ) -> dict[str, list[KanbanTask]]:
        """Parse a temporary kanban.md body."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / profile
            prof.mkdir()
            (prof / "kanban.md").write_text(
                markdown,
                encoding="utf-8",
            )
            with patch(
                "nblane.core.io.profile_dir",
                lambda _n: prof,
            ):
                return parse_kanban(profile)

    def test_meta_subtasks_roundtrip(self) -> None:
        """context, subtasks, and notes survive parse/render."""
        sections = {
            KANBAN_DOING: [
                KanbanTask(
                    title="Main",
                    done=False,
                    context="ctx",
                    started_on="2026-03-01",
                    tags="narwal",
                    subtasks=[
                        KanbanSubtask(title="a", done=False),
                        KanbanSubtask(title="b", done=True),
                    ],
                    details=["free note"],
                )
            ],
            KANBAN_DONE: [],
            KANBAN_QUEUE: [],
            KANBAN_SOMEDAY: [],
        }
        text = render_kanban("u1", sections)
        self.assertIn("  - id: kb_", text)
        self.assertIn("  - tags: narwal", text)
        back = self._parse_markdown("u1", text)
        t = back[KANBAN_DOING][0]
        self.assertEqual(t.title, "Main")
        self.assertTrue(t.id.startswith("kb_"))
        self.assertEqual(t.context, "ctx")
        self.assertEqual(t.started_on, "2026-03-01")
        self.assertEqual(t.tags, "narwal")
        self.assertEqual(len(t.subtasks), 2)
        self.assertFalse(t.subtasks[0].done)
        self.assertTrue(t.subtasks[1].done)
        self.assertEqual(t.details, ["free note"])

    def test_existing_tags_line_parses_as_structured_meta(self) -> None:
        """Existing `tags:` lines no longer fall through to free-form details."""
        md = """# x · Kanban

> Updated: 2026-01-01

---

## Doing

- [ ] Tagged task
  - id: kb_demo
  - tags: GAC
  - plain line

---
"""
        parsed = self._parse_markdown("p", md)
        task = parsed[KANBAN_DOING][0]
        self.assertEqual(task.tags, "GAC")
        self.assertEqual(task.details, ["plain line"])

    def test_legacy_tasks_get_deterministic_ids(self) -> None:
        """Old files without id meta receive stable generated ids."""
        md = """# x · Kanban

> Updated: 2026-01-01

---

## Doing

- [ ] T1
  - plain line

---
"""
        first = self._parse_markdown("p", md)
        second = self._parse_markdown("p", md)
        task = first[KANBAN_DOING][0]
        self.assertEqual(task.details, ["plain line"])
        self.assertTrue(task.id.startswith("kb_"))
        self.assertEqual(task.id, second[KANBAN_DOING][0].id)
        rendered = render_kanban("p", first)
        self.assertIn(f"  - id: {task.id}", rendered)
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "p"
            prof.mkdir()
            (prof / "kanban.md").write_text(md, encoding="utf-8")
            with patch(
                "nblane.core.io.profile_dir",
                lambda _n: prof,
            ):
                parsed = parse_kanban("p")
                save_kanban("p", parsed)
            saved = (prof / "kanban.md").read_text(encoding="utf-8")
        self.assertIn(f"  - id: {task.id}", saved)

    def test_existing_id_stays_stable(self) -> None:
        """Existing id meta parses and renders unchanged."""
        md = """# x · Kanban

> Updated: 2026-01-01

---

## Queue

- [ ] Keep identity
  - id: task-alpha
  - why: trace across moves

---
"""
        back = self._parse_markdown("p", md)
        task = back[KANBAN_QUEUE][0]
        self.assertEqual(task.id, "task-alpha")
        rendered = render_kanban("p", back)
        self.assertIn("  - id: task-alpha", rendered)
        again = self._parse_markdown("p", rendered)
        self.assertEqual(again[KANBAN_QUEUE][0].id, "task-alpha")

    def test_someday_subtasks_details_roundtrip(self) -> None:
        """Someday tasks keep id, subtasks, and details."""
        sections = {
            KANBAN_DOING: [],
            KANBAN_DONE: [],
            KANBAN_QUEUE: [],
            KANBAN_SOMEDAY: [
                KanbanTask(
                    title="Later project",
                    id="someday-1",
                    subtasks=[
                        KanbanSubtask(title="Sketch", done=False),
                        KanbanSubtask(title="Decide", done=True),
                    ],
                    details=["keep this note"],
                )
            ],
        }
        text = render_kanban("p", sections)
        self.assertIn("- Later project", text)
        self.assertIn("  - id: someday-1", text)
        self.assertIn("  - [ ] Sketch", text)
        self.assertIn("  - keep this note", text)
        back = self._parse_markdown("p", text)
        task = back[KANBAN_SOMEDAY][0]
        self.assertEqual(task.id, "someday-1")
        self.assertEqual(
            [st.title for st in task.subtasks],
            ["Sketch", "Decide"],
        )
        self.assertFalse(task.subtasks[0].done)
        self.assertTrue(task.subtasks[1].done)
        self.assertEqual(task.details, ["keep this note"])

    def test_ensure_kanban_task_ids_is_pure_and_unique(self) -> None:
        """ensure_kanban_task_ids returns copies with deterministic ids."""
        sections = {
            KANBAN_DOING: [
                KanbanTask(title="Same"),
                KanbanTask(title="Same"),
            ],
            KANBAN_DONE: [],
            KANBAN_QUEUE: [],
            KANBAN_SOMEDAY: [],
        }
        ensured = ensure_kanban_task_ids(sections, "p")
        ensured_again = ensure_kanban_task_ids(sections, "p")
        ids = [task.id for task in ensured[KANBAN_DOING]]
        self.assertEqual(
            ids,
            [task.id for task in ensured_again[KANBAN_DOING]],
        )
        self.assertEqual(len(set(ids)), 2)
        self.assertEqual(sections[KANBAN_DOING][0].id, "")

    def test_apply_kanban_reorder_moves_by_id(self) -> None:
        """Reorder/move operations preserve task ids and input sections."""
        sections = {
            KANBAN_DOING: [KanbanTask(title="Doing", id="doing")],
            KANBAN_QUEUE: [
                KanbanTask(title="First", id="q1"),
                KanbanTask(title="Second", id="q2"),
            ],
            KANBAN_DONE: [],
            KANBAN_SOMEDAY: [],
        }
        result = apply_kanban_reorder(
            sections,
            [
                {
                    "id": "q1",
                    "to_section": KANBAN_QUEUE,
                    "to_index": 1,
                },
                {
                    "id": "q2",
                    "to_section": KANBAN_DOING,
                    "to_index": 0,
                },
            ],
            auto_dates=False,
        )
        self.assertEqual(
            [t.id for t in result[KANBAN_DOING]],
            ["q2", "doing"],
        )
        self.assertEqual([t.id for t in result[KANBAN_QUEUE]], ["q1"])
        self.assertEqual(
            [t.id for t in sections[KANBAN_QUEUE]],
            ["q1", "q2"],
        )

    def test_apply_kanban_reorder_auto_dates(self) -> None:
        """Column moves apply started/completed dates when requested."""
        sections = {
            KANBAN_DOING: [],
            KANBAN_QUEUE: [
                KanbanTask(title="Start", id="start"),
                KanbanTask(title="Finish", id="finish"),
            ],
            KANBAN_DONE: [
                KanbanTask(
                    title="Reopen",
                    id="reopen",
                    done=True,
                    completed_on="2026-04-01",
                )
            ],
            KANBAN_SOMEDAY: [],
        }
        with patch("nblane.core.kanban_io.date", _FixedDate):
            result = apply_kanban_reorder(
                sections,
                [
                    {"id": "start", "to_section": KANBAN_DOING},
                    {"id": "finish", "to_section": KANBAN_DONE},
                    {"id": "reopen", "to_section": KANBAN_QUEUE},
                ],
                auto_dates=True,
            )

        started = result[KANBAN_DOING][0]
        finished = result[KANBAN_DONE][0]
        reopened = result[KANBAN_QUEUE][0]
        self.assertEqual(started.started_on, "2026-04-27")
        self.assertFalse(started.done)
        self.assertEqual(finished.completed_on, "2026-04-27")
        self.assertTrue(finished.done)
        self.assertIsNone(reopened.completed_on)
        self.assertFalse(reopened.done)

    def test_apply_kanban_reorder_ignores_unknown_section(self) -> None:
        """Core reorder helper does not create unrendered sections."""
        sections = {
            KANBAN_DOING: [KanbanTask(title="Do", id="do")],
            KANBAN_QUEUE: [],
            KANBAN_DONE: [],
            KANBAN_SOMEDAY: [],
        }
        result = apply_kanban_reorder(
            sections,
            [{"id": "do", "to_section": "Review", "to_index": 0}],
            auto_dates=False,
        )
        self.assertEqual([t.id for t in result[KANBAN_DOING]], ["do"])
        self.assertNotIn("Review", result)

    def test_kanban_snapshot_to_moves_reorders_full_snapshot(self) -> None:
        """Drag-board snapshots can describe full final order."""
        sections = {
            KANBAN_DOING: [KanbanTask(title="Doing", id="doing")],
            KANBAN_QUEUE: [
                KanbanTask(title="First", id="q1"),
                KanbanTask(title="Second", id="q2"),
            ],
            KANBAN_DONE: [],
            KANBAN_SOMEDAY: [],
        }
        snapshot = {
            "columns": [
                {"section": KANBAN_DOING, "task_ids": ["q2", "doing"]},
                {"section": KANBAN_QUEUE, "task_ids": ["q1"]},
                {"section": KANBAN_DONE, "task_ids": []},
                {"section": KANBAN_SOMEDAY, "task_ids": []},
            ],
        }
        moves = kanban_snapshot_to_moves(
            snapshot,
            sections,
            section_order=KANBAN_BOARD_SECTIONS,
        )
        self.assertIsInstance(moves, list)
        result = apply_kanban_reorder(sections, moves or [], auto_dates=False)
        self.assertEqual([t.id for t in result[KANBAN_DOING]], ["q2", "doing"])
        self.assertEqual([t.id for t in result[KANBAN_QUEUE]], ["q1"])

    def test_kanban_snapshot_to_moves_rejects_incomplete_or_duplicate_ids(self) -> None:
        """Drag-board snapshots must include each known id exactly once."""
        sections = {
            KANBAN_DOING: [KanbanTask(title="Doing", id="doing")],
            KANBAN_QUEUE: [KanbanTask(title="Queued", id="q1")],
            KANBAN_DONE: [],
            KANBAN_SOMEDAY: [],
        }
        missing = {
            "columns": [
                {"section": KANBAN_DOING, "task_ids": ["doing"]},
                {"section": KANBAN_QUEUE, "task_ids": []},
                {"section": KANBAN_DONE, "task_ids": []},
                {"section": KANBAN_SOMEDAY, "task_ids": []},
            ],
        }
        duplicate = {
            "columns": [
                {"section": KANBAN_DOING, "task_ids": ["doing", "doing"]},
                {"section": KANBAN_QUEUE, "task_ids": ["q1"]},
                {"section": KANBAN_DONE, "task_ids": []},
                {"section": KANBAN_SOMEDAY, "task_ids": []},
            ],
        }
        duplicate_section = {
            "columns": [
                {"section": KANBAN_DOING, "task_ids": ["doing"]},
                {"section": KANBAN_DOING, "task_ids": ["q1"]},
                {"section": KANBAN_DONE, "task_ids": []},
                {"section": KANBAN_SOMEDAY, "task_ids": []},
            ],
        }
        self.assertIsNone(
            kanban_snapshot_to_moves(
                missing,
                sections,
                section_order=KANBAN_BOARD_SECTIONS,
            )
        )
        self.assertIsNone(
            kanban_snapshot_to_moves(
                duplicate,
                sections,
                section_order=KANBAN_BOARD_SECTIONS,
            )
        )
        self.assertIsNone(
            kanban_snapshot_to_moves(
                duplicate_section,
                sections,
                section_order=KANBAN_BOARD_SECTIONS,
            )
        )

    def test_kanban_snapshot_to_moves_returns_empty_when_unchanged(self) -> None:
        """No-change snapshots are valid but do not produce moves."""
        sections = {
            KANBAN_DOING: [KanbanTask(title="Doing", id="doing")],
            KANBAN_QUEUE: [KanbanTask(title="Queued", id="q1")],
            KANBAN_DONE: [],
            KANBAN_SOMEDAY: [],
        }
        snapshot = {
            "columns": [
                {"section": KANBAN_DOING, "task_ids": ["doing"]},
                {"section": KANBAN_QUEUE, "task_ids": ["q1"]},
                {"section": KANBAN_DONE, "task_ids": []},
                {"section": KANBAN_SOMEDAY, "task_ids": []},
            ],
        }
        self.assertEqual(
            kanban_snapshot_to_moves(
                snapshot,
                sections,
                section_order=KANBAN_BOARD_SECTIONS,
            ),
            [],
        )

    def test_append_kanban_archive_creates_file(self) -> None:
        """Archive append writes kanban-archive.md."""
        tasks = [
            KanbanTask(
                title="Old done",
                done=True,
                outcome="shipped",
            )
        ]
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "p2"
            prof.mkdir()
            with patch(
                "nblane.core.io.profile_dir",
                lambda _n: prof,
            ):
                append_kanban_archive("p2", tasks)
                append_kanban_archive("p2", tasks)
            arc = prof / "kanban-archive.md"
            self.assertTrue(arc.exists())
            body = arc.read_text(encoding="utf-8")
            self.assertIn("Old done", body)
            self.assertIn("  - id: kb_", body)
            self.assertIn("Archived", body)


if __name__ == "__main__":
    unittest.main()
