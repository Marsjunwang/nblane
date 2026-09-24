"""Tests for kanban three-way merge (external modification handling)."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from nblane.core.file_state import snapshot_file
from nblane.core.kanban_io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
    parse_kanban,
    save_kanban,
)
from nblane.core.kanban_merge import (
    CHANGE_ADD,
    CHANGE_MOVE,
    CHANGE_REMOVE,
    CHANGE_UPDATE,
    apply_kanban_changes,
    copy_kanban_sections,
    diff_kanban_sections,
    save_kanban_with_merge,
)
from nblane.core.models import KanbanTask, KanbanTodo


def _sections(*, queue=(), doing=(), done=(), someday=()):
    return {
        KANBAN_DOING: list(doing),
        KANBAN_DONE: list(done),
        KANBAN_QUEUE: list(queue),
        KANBAN_SOMEDAY: list(someday),
    }


class TestDiffKanbanSections(unittest.TestCase):
    """The base -> ours delta is captured task by task."""

    def test_detects_add_remove_update_move(self) -> None:
        base = _sections(
            queue=[
                KanbanTask(title="keep", id="k1"),
                KanbanTask(title="drop", id="d1"),
            ],
            doing=[KanbanTask(title="move me", id="m1")],
        )
        ours = _sections(
            queue=[
                KanbanTask(title="keep", id="k1", context="edited"),
                KanbanTask(title="move me", id="m1"),
                KanbanTask(title="brand new", id="n1"),
            ],
        )
        changes = diff_kanban_sections(base, ours)
        by_kind = {}
        for change in changes:
            by_kind.setdefault(change.kind, []).append(change)

        self.assertEqual([c.task_id for c in by_kind[CHANGE_REMOVE]], ["d1"])
        self.assertEqual(
            [(c.task_id, c.to_section, c.to_index) for c in by_kind[CHANGE_ADD]],
            [("n1", KANBAN_QUEUE, 2)],
        )
        self.assertEqual([c.task_id for c in by_kind[CHANGE_UPDATE]], ["k1"])
        self.assertEqual(by_kind[CHANGE_UPDATE][0].task.context, "edited")
        self.assertEqual(
            [(c.task_id, c.to_section, c.to_index) for c in by_kind[CHANGE_MOVE]],
            [("m1", KANBAN_QUEUE, 1)],
        )

    def test_ignores_idless_tasks(self) -> None:
        base = _sections(queue=[KanbanTask(title="a", id="a")])
        ours = _sections(
            queue=[KanbanTask(title="a", id="a"), KanbanTask(title="no id")]
        )
        self.assertEqual(diff_kanban_sections(base, ours), [])

    def test_empty_delta(self) -> None:
        base = _sections(queue=[KanbanTask(title="a", id="a")])
        self.assertEqual(diff_kanban_sections(base, copy_kanban_sections(base)), [])


class TestApplyKanbanChanges(unittest.TestCase):
    """Replay semantics onto a possibly diverged disk state."""

    def test_add_update_move_replayed_external_edits_kept(self) -> None:
        base = _sections(
            queue=[KanbanTask(title="A", id="a")],
            doing=[KanbanTask(title="B", id="b")],
        )
        theirs = copy_kanban_sections(base)
        # External writer edited B and added X.
        theirs[KANBAN_DOING][0] = replace(
            theirs[KANBAN_DOING][0], context="external ctx"
        )
        theirs[KANBAN_QUEUE].append(KanbanTask(title="X", id="x"))
        changes = diff_kanban_sections(
            base,
            _sections(
                queue=[
                    KanbanTask(title="A edited", id="a"),
                    KanbanTask(title="B", id="b"),
                    KanbanTask(title="N", id="n"),
                ],
            ),
        )
        merged, dropped = apply_kanban_changes(theirs, changes)
        self.assertEqual(dropped, [])
        queue_titles = [t.title for t in merged[KANBAN_QUEUE]]
        # Our add lands at its in-memory index, shifting the external add.
        self.assertEqual(queue_titles, ["A edited", "B", "N", "X"])
        # External edit to B survived the move.
        moved_b = merged[KANBAN_QUEUE][1]
        self.assertEqual(moved_b.context, "external ctx")

    def test_update_and_move_drop_when_task_deleted_externally(self) -> None:
        theirs = _sections(queue=[KanbanTask(title="B", id="b")])
        changes = [
            _change(
                CHANGE_UPDATE,
                "gone",
                KanbanTask(title="G", id="gone"),
                fields={"title": "G"},
            ),
            _change(CHANGE_MOVE, "also-gone", None, KANBAN_DONE, 0),
        ]
        merged, dropped = apply_kanban_changes(theirs, changes)
        self.assertEqual([c.task_id for c in dropped], ["gone", "also-gone"])
        self.assertEqual([t.id for t in merged[KANBAN_QUEUE]], ["b"])

    def test_update_merges_field_level_and_keeps_external_fields(self) -> None:
        theirs = _sections(
            queue=[KanbanTask(title="A", id="a", context="external ctx")],
        )
        merged, dropped = apply_kanban_changes(
            theirs,
            [
                _change(
                    CHANGE_UPDATE,
                    "a",
                    KanbanTask(title="A", id="a", why="our why"),
                    fields={"why": "our why"},
                )
            ],
        )
        self.assertEqual(dropped, [])
        task = merged[KANBAN_QUEUE][0]
        self.assertEqual(task.why, "our why")
        self.assertEqual(task.context, "external ctx")

    def test_update_carries_todos_and_keeps_external_todos(self) -> None:
        """The todos list diffs/replays like any other list field."""
        base = _sections(
            queue=[KanbanTask(title="A", id="a", todos=[KanbanTodo(text="old")])],
        )
        ours = _sections(
            queue=[
                KanbanTask(
                    title="A",
                    id="a",
                    todos=[KanbanTodo(text="old", done=True), KanbanTodo(text="new")],
                )
            ],
        )
        changes = diff_kanban_sections(base, ours)
        updates = [c for c in changes if c.kind == CHANGE_UPDATE]
        self.assertEqual(len(updates), 1)
        self.assertEqual(
            updates[0].fields,
            {"todos": [KanbanTodo(text="old", done=True), KanbanTodo(text="new")]},
        )
        # Our todos replay onto a disk state where someone else edited why.
        theirs = _sections(
            queue=[KanbanTask(title="A", id="a", why="external", todos=[KanbanTodo(text="old")])],
        )
        merged, dropped = apply_kanban_changes(theirs, changes)
        self.assertEqual(dropped, [])
        task = merged[KANBAN_QUEUE][0]
        self.assertEqual(
            task.todos,
            [KanbanTodo(text="old", done=True), KanbanTodo(text="new")],
        )
        self.assertEqual(task.why, "external")

    def test_remove_of_missing_task_is_silent_noop(self) -> None:
        theirs = _sections(queue=[KanbanTask(title="B", id="b")])
        merged, dropped = apply_kanban_changes(
            theirs, [_change(CHANGE_REMOVE, "missing")]
        )
        self.assertEqual(dropped, [])
        self.assertEqual([t.id for t in merged[KANBAN_QUEUE]], ["b"])

    def test_add_with_existing_id_updates_in_place(self) -> None:
        theirs = _sections(queue=[KanbanTask(title="old", id="a")])
        merged, dropped = apply_kanban_changes(
            theirs,
            [_change(CHANGE_ADD, "a", KanbanTask(title="new", id="a"), KANBAN_DONE, 0)],
        )
        self.assertEqual(dropped, [])
        self.assertEqual([t.title for t in merged[KANBAN_QUEUE]], ["new"])
        self.assertEqual(merged[KANBAN_DONE], [])

    def test_inputs_not_mutated(self) -> None:
        theirs = _sections(queue=[KanbanTask(title="B", id="b")])
        apply_kanban_changes(
            theirs, [_change(CHANGE_REMOVE, "b")]
        )
        self.assertEqual([t.id for t in theirs[KANBAN_QUEUE]], ["b"])


def _change(kind, task_id, task=None, to_section="", to_index=-1, fields=None):
    from nblane.core.kanban_merge import KanbanChange

    return KanbanChange(
        kind=kind,
        task_id=task_id,
        task=task,
        to_section=to_section,
        to_index=to_index,
        fields=fields,
    )


class TestSaveKanbanWithMerge(unittest.TestCase):
    """External modification is detected and both sides survive."""

    def _profile(self, tmp: str) -> Path:
        prof = Path(tmp) / "p"
        prof.mkdir()
        save_kanban(
            prof,
            _sections(
                queue=[KanbanTask(title="A")],
                doing=[KanbanTask(title="B")],
            ),
        )
        return prof

    def test_external_change_detected_and_merged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prof = self._profile(tmp)
            base = parse_kanban(prof)
            snap = snapshot_file(prof / "kanban.md")

            # Our in-memory change: edit A, quick-add N (id-less), move B to Done.
            ours = copy_kanban_sections(base)
            a_id = ours[KANBAN_QUEUE][0].id
            b_id = ours[KANBAN_DOING][0].id
            ours[KANBAN_QUEUE][0] = replace(
                ours[KANBAN_QUEUE][0], title="A edited by board"
            )
            ours[KANBAN_QUEUE].append(KanbanTask(title="N quick add"))
            moved = replace(ours[KANBAN_DOING].pop(0), done=True)
            ours[KANBAN_DONE].append(moved)

            # External writer (CLI/home quick add): add X, retitle B.
            external = parse_kanban(prof)
            external[KANBAN_QUEUE].append(KanbanTask(title="X from CLI"))
            external[KANBAN_DOING][0] = replace(
                external[KANBAN_DOING][0], context="external note"
            )
            save_kanban(prof, external)
            x_id = parse_kanban(prof)[KANBAN_QUEUE][-1].id

            result = save_kanban_with_merge(
                prof, ours, base, expected_snapshot=snap
            )

            self.assertTrue(result.merged_external)
            self.assertEqual(result.dropped_changes, ())
            final = parse_kanban(prof)
            flat = {
                task.id: (section, task)
                for section, tasks in final.items()
                for task in tasks
            }
            # Our edits: A retitled, quick-added N present with a fresh id.
            self.assertEqual(flat[a_id][1].title, "A edited by board")
            new_ids = [
                tid
                for tid, (section, task) in flat.items()
                if task.title == "N quick add"
            ]
            self.assertEqual(len(new_ids), 1)
            self.assertTrue(new_ids[0].startswith("kb_"))
            # Our move: B in Done; external edit to B preserved.
            self.assertEqual(flat[b_id][0], KANBAN_DONE)
            self.assertEqual(flat[b_id][1].context, "external note")
            self.assertTrue(flat[b_id][1].done)
            # External addition preserved.
            self.assertIn(x_id, flat)

    def test_change_to_externally_deleted_task_is_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prof = self._profile(tmp)
            base = parse_kanban(prof)
            snap = snapshot_file(prof / "kanban.md")
            a_id = base[KANBAN_QUEUE][0].id
            b_id = base[KANBAN_DOING][0].id

            # We edit A; the external writer deletes A and edits B.
            ours = copy_kanban_sections(base)
            ours[KANBAN_QUEUE][0] = replace(
                ours[KANBAN_QUEUE][0], title="A edited"
            )
            external = parse_kanban(prof)
            external[KANBAN_QUEUE] = []
            external[KANBAN_DOING][0] = replace(
                external[KANBAN_DOING][0], context="external note"
            )
            save_kanban(prof, external)

            result = save_kanban_with_merge(
                prof, ours, base, expected_snapshot=snap
            )

            self.assertTrue(result.merged_external)
            self.assertEqual(
                [change.task_id for change in result.dropped_changes],
                [a_id],
            )
            final = parse_kanban(prof)
            # External deletion stands; external edit to B survives.
            self.assertEqual(final[KANBAN_QUEUE], [])
            self.assertEqual(
                final[KANBAN_DOING][0].context, "external note"
            )
            self.assertEqual(final[KANBAN_DOING][0].id, b_id)

    def test_no_external_change_saves_as_is(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prof = self._profile(tmp)
            base = parse_kanban(prof)
            snap = snapshot_file(prof / "kanban.md")
            ours = copy_kanban_sections(base)
            ours[KANBAN_QUEUE][0] = replace(
                ours[KANBAN_QUEUE][0], title="A edited"
            )
            result = save_kanban_with_merge(
                prof, ours, base, expected_snapshot=snap
            )
            self.assertFalse(result.merged_external)
            final = parse_kanban(prof)
            self.assertEqual(final[KANBAN_QUEUE][0].title, "A edited")

    def test_missing_base_falls_back_to_union_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prof = self._profile(tmp)
            snap = snapshot_file(prof / "kanban.md")
            ours = parse_kanban(prof)
            ours[KANBAN_QUEUE].append(KanbanTask(title="N"))

            external = parse_kanban(prof)
            external[KANBAN_QUEUE].append(KanbanTask(title="X"))
            save_kanban(prof, external)

            result = save_kanban_with_merge(
                prof, ours, None, expected_snapshot=snap
            )
            self.assertTrue(result.merged_external)
            titles = [
                task.title
                for task in parse_kanban(prof)[KANBAN_QUEUE]
            ]
            self.assertEqual(titles, ["A", "N", "X"])

    def test_no_snapshot_means_plain_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prof = self._profile(tmp)
            ours = parse_kanban(prof)
            ours[KANBAN_QUEUE][0] = replace(
                ours[KANBAN_QUEUE][0], title="A edited"
            )
            # External change happens but no snapshot was supplied.
            save_kanban(
                prof,
                _sections(queue=[KanbanTask(title="external only")]),
            )
            result = save_kanban_with_merge(prof, ours, None)
            self.assertFalse(result.merged_external)
            self.assertEqual(
                parse_kanban(prof)[KANBAN_QUEUE][0].title, "A edited"
            )


if __name__ == "__main__":
    unittest.main()
