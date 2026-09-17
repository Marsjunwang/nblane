"""Three-way merge helpers for kanban.md auto-save conflict handling.

Pure functions, no Streamlit. The Kanban board auto-saves on every
interaction, so a second writer (home-page quick add, MCP, CLI, another
page) can change kanban.md after the board last loaded or saved it. When
that happens the board must not silently overwrite the external change:
the delta the user just made (base -> current in-memory sections) is
replayed onto the freshly parsed disk state, task by task, keyed by the
stable task id.

Replay is best effort per change: additions always apply; updates, moves,
and removals target a task id and are dropped (and reported) when that
task no longer exists on disk — the external deletion wins and the user
is told their change was discarded. Updates apply field by field, so an
external edit to a field the user did not touch survives the merge; when
both sides changed the same field, the in-memory (board) value wins.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from pathlib import Path

from nblane.core.file_state import FileSnapshot, snapshot_matches
from nblane.core.kanban_io import (
    _copy_kanban_task,
    ensure_kanban_task_ids,
    kanban_path,
    parse_kanban,
    save_kanban,
)
from nblane.core.models import KanbanTask

CHANGE_ADD = "add"
CHANGE_REMOVE = "remove"
CHANGE_UPDATE = "update"
CHANGE_MOVE = "move"


@dataclass(frozen=True)
class KanbanChange:
    """One task-level change between two kanban states."""

    kind: str
    task_id: str
    task: KanbanTask | None = None
    to_section: str = ""
    to_index: int = -1
    fields: dict | None = None

    @property
    def label(self) -> str:
        """Short human-readable description for UI warnings."""
        title = ""
        if self.task is not None:
            title = str(getattr(self.task, "title", "") or "").strip()
        return title or self.task_id


def copy_kanban_sections(
    sections: dict[str, list[KanbanTask]],
) -> dict[str, list[KanbanTask]]:
    """Return a deep-enough copy for storing as a merge base snapshot."""
    return {
        section: [_copy_kanban_task(task) for task in tasks]
        for section, tasks in sections.items()
    }


def _index_by_id(
    sections: dict[str, list[KanbanTask]],
) -> dict[str, tuple[str, int, KanbanTask]]:
    out: dict[str, tuple[str, int, KanbanTask]] = {}
    for section, tasks in sections.items():
        for idx, task in enumerate(tasks):
            task_id = str(getattr(task, "id", "") or "").strip()
            if task_id and task_id not in out:
                out[task_id] = (section, idx, task)
    return out


def _task_field_changes(
    base_task: KanbanTask,
    our_task: KanbanTask,
) -> dict:
    """Return the dataclass fields that differ between two task versions.

    Field-level (not whole-task) diffs let a replay keep external edits to
    fields the user did not touch. List fields are compared and carried
    whole; the ``id`` field never changes by construction.
    """
    changes: dict = {}
    for field in fields(KanbanTask):
        if field.name == "id":
            continue
        base_value = getattr(base_task, field.name)
        our_value = getattr(our_task, field.name)
        if base_value != our_value:
            changes[field.name] = (
                list(our_value) if isinstance(our_value, list) else our_value
            )
    return changes


def diff_kanban_sections(
    base: dict[str, list[KanbanTask]],
    ours: dict[str, list[KanbanTask]],
) -> list[KanbanChange]:
    """Return the task-level delta from *base* to *ours*.

    Both inputs are expected to carry unique non-empty task ids (run them
    through ``ensure_kanban_task_ids`` first). Id-less tasks cannot be
    tracked and are ignored.
    """
    changes: list[KanbanChange] = []
    base_index = _index_by_id(base)
    ours_index = _index_by_id(ours)

    for task_id in base_index:
        if task_id not in ours_index:
            changes.append(KanbanChange(kind=CHANGE_REMOVE, task_id=task_id))

    for tid in ours_index:
        if tid in base_index:
            continue
        section, idx, task = ours_index[tid]
        changes.append(
            KanbanChange(
                kind=CHANGE_ADD,
                task_id=tid,
                task=task,
                to_section=section,
                to_index=idx,
            )
        )

    for task_id in ours_index:
        if task_id not in base_index:
            continue
        base_section, base_idx, base_task = base_index[task_id]
        our_section, our_idx, our_task = ours_index[task_id]
        if (base_section, base_idx) != (our_section, our_idx):
            changes.append(
                KanbanChange(
                    kind=CHANGE_MOVE,
                    task_id=task_id,
                    to_section=our_section,
                    to_index=our_idx,
                )
            )
        if base_task != our_task:
            field_changes = _task_field_changes(base_task, our_task)
            if field_changes:
                changes.append(
                    KanbanChange(
                        kind=CHANGE_UPDATE,
                        task_id=task_id,
                        task=our_task,
                        fields=field_changes,
                    )
                )

    # Deterministic replay order: removals, updates, moves, additions.
    order = {
        CHANGE_REMOVE: 0,
        CHANGE_UPDATE: 1,
        CHANGE_MOVE: 2,
        CHANGE_ADD: 3,
    }
    changes.sort(key=lambda change: order.get(change.kind, 9))
    return changes


def apply_kanban_changes(
    theirs: dict[str, list[KanbanTask]],
    changes: list[KanbanChange],
) -> tuple[dict[str, list[KanbanTask]], list[KanbanChange]]:
    """Replay *changes* onto a copy of *theirs*.

    Returns ``(merged, dropped)``. A change is dropped when its target task
    no longer exists in *theirs* (updates/moves) — the external state wins.
    A remove whose task is already gone is a silent no-op. An add whose id
    already exists in *theirs* degenerates to an in-place update so a merge
    without a base snapshot never duplicates cards.
    """
    out = copy_kanban_sections(theirs)
    dropped: list[KanbanChange] = []

    def _locate(task_id: str) -> tuple[str, int] | None:
        found = _index_by_id(out).get(task_id)
        if found is None:
            return None
        return found[0], found[1]

    for change in changes:
        if change.kind == CHANGE_REMOVE:
            found = _locate(change.task_id)
            if found is not None:
                section, idx = found
                out[section].pop(idx)
            continue

        if change.kind == CHANGE_UPDATE:
            found = _locate(change.task_id)
            if found is None:
                dropped.append(change)
                continue
            if not change.fields:
                continue
            section, idx = found
            field_changes = {
                name: (list(value) if isinstance(value, list) else value)
                for name, value in change.fields.items()
                if name != "id" and hasattr(out[section][idx], name)
            }
            if field_changes:
                out[section][idx] = replace(
                    out[section][idx],
                    **field_changes,
                )
            continue

        if change.kind == CHANGE_MOVE:
            found = _locate(change.task_id)
            if found is None:
                dropped.append(change)
                continue
            from_section, from_idx = found
            to_section = change.to_section
            if to_section not in out:
                to_section = from_section
            moved = out[from_section].pop(from_idx)
            to_tasks = out[to_section]
            to_index = max(0, min(change.to_index, len(to_tasks)))
            to_tasks.insert(to_index, moved)
            continue

        if change.kind == CHANGE_ADD:
            if change.task is None:
                continue
            found = _locate(change.task_id)
            if found is not None:
                section, idx = found
                out[section][idx] = _copy_kanban_task(change.task)
                continue
            to_section = (
                change.to_section
                if change.to_section in out
                else next(iter(out), "")
            )
            if not to_section:
                continue
            to_tasks = out.setdefault(to_section, [])
            to_index = max(0, min(change.to_index, len(to_tasks)))
            to_tasks.insert(to_index, _copy_kanban_task(change.task))
            continue

    return out, dropped


@dataclass(frozen=True)
class KanbanSaveResult:
    """Outcome of a conflict-aware kanban save."""

    sections: dict[str, list[KanbanTask]]
    merged_external: bool
    dropped_changes: tuple[KanbanChange, ...] = ()


def save_kanban_with_merge(
    profile: str | Path,
    sections: dict[str, list[KanbanTask]],
    base_sections: dict[str, list[KanbanTask]] | None,
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> KanbanSaveResult:
    """Save kanban.md, merging external on-disk changes when detected.

    When *expected_snapshot* is given and kanban.md no longer matches it,
    the file is re-parsed and the caller's delta (*base_sections* ->
    *sections*) is replayed onto the latest disk state instead of blindly
    overwriting it. Without a base snapshot the replay degenerates to a
    union merge (every in-memory task is treated as an addition), which
    preserves both sides at the cost of resurrecting tasks the external
    writer deleted. The returned sections are the persisted state; callers
    should adopt them.
    """
    profile_name = profile.name if isinstance(profile, Path) else profile
    ensured = ensure_kanban_task_ids(sections, profile_name)
    merged = ensured
    merged_external = False
    dropped: list[KanbanChange] = []
    if expected_snapshot is not None and not snapshot_matches(
        kanban_path(profile),
        expected_snapshot,
    ):
        merged_external = True
        theirs = parse_kanban(profile)
        base = (
            base_sections
            if base_sections is not None
            else {section: [] for section in theirs}
        )
        changes = diff_kanban_sections(base, ensured)
        merged, dropped = apply_kanban_changes(theirs, changes)
    save_kanban(profile, merged)
    return KanbanSaveResult(
        sections=merged,
        merged_external=merged_external,
        dropped_changes=tuple(dropped),
    )
