"""Shared helpers for the Kanban board UI."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from nblane.core.kanban_io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
    save_kanban,
)
from nblane.core.models import KanbanTask
from nblane.core.profile_io import profile_dir
from nblane.web_shared import (
    assert_files_current,
    refresh_file_snapshots,
    stash_git_backup_results,
)

_BOARD_ORDER = (
    KANBAN_DOING,
    KANBAN_QUEUE,
    KANBAN_DONE,
    KANBAN_SOMEDAY,
)
_COL_WEIGHTS = [2.2, 1.0, 1.0, 1.0]
_WIP_HINT_THRESHOLD = 5

_SECTION_COLOR = {
    KANBAN_DOING: "#fbbc04",
    KANBAN_QUEUE: "#1a73e8",
    KANBAN_DONE: "#34a853",
    KANBAN_SOMEDAY: "#9aa0a6",
}

def _auto_save(
    profile: str,
    sections: dict[str, list[KanbanTask]],
) -> None:
    """Persist kanban to disk."""
    path = profile_dir(profile) / "kanban.md"
    assert_files_current([path])
    save_kanban(profile, sections)
    refresh_file_snapshots([path])
    stash_git_backup_results()


def _apply_column_move(
    task: KanbanTask,
    from_sec: str,
    to_sec: str,
    auto_dates: bool,
) -> KanbanTask:
    """Adjust done flag and optional dates when moving between columns."""
    t = task
    if to_sec == KANBAN_DONE:
        t = replace(t, done=True)
        if auto_dates:
            co = (t.completed_on or "").strip() if t.completed_on else ""
            if not co:
                t = replace(
                    t,
                    completed_on=date.today().isoformat(),
                )
    elif from_sec == KANBAN_DONE:
        t = replace(t, done=False)
        if auto_dates:
            t = replace(t, completed_on=None)
    if to_sec == KANBAN_DOING and from_sec != KANBAN_DOING:
        if auto_dates:
            so = (t.started_on or "").strip() if t.started_on else ""
            if not so:
                t = replace(
                    t,
                    started_on=date.today().isoformat(),
                )
    return t


def _kb_more_expanded(section: str, task: KanbanTask) -> bool:
    """Open legacy 'more fields' when folded slots hold data (Done / Queue)."""
    if section == KANBAN_QUEUE:
        return bool(
            task.context.strip()
            or (task.started_on or "").strip()
            or (task.completed_on or "").strip()
        )
    if section == KANBAN_DONE:
        return bool(
            (task.started_on or "").strip()
            or (task.completed_on or "").strip()
            or task.why.strip()
            or task.blocked_by.strip()
        )
    return False


def _doing_body_expanded(task: KanbanTask) -> bool:
    """Expand Doing task body when it already has content."""
    return bool(
        task.context.strip()
        or (task.started_on or "").strip()
        or task.why.strip()
        or task.blocked_by.strip()
        or (task.completed_on or "").strip()
        or task.subtasks
        or task.details
    )


def _queue_compact_body_expanded(task: KanbanTask) -> bool:
    """Expand Queue compact body when secondary fields exist."""
    return bool(
        task.context.strip()
        or (task.started_on or "").strip()
        or (task.completed_on or "").strip()
        or task.subtasks
        or task.details
    )


def _someday_body_expanded(task: KanbanTask) -> bool:
    """Expand Someday card when subtasks or details exist."""
    return bool(task.subtasks or task.details)


def _task_editing_key(profile: str, section: str, idx: int) -> str:
    """Session state flag: task card shows form widgets vs compact read view."""
    return f"kanban_editing_{profile}_{section}_{idx}"


def _read_title_label(full: str, max_len: int = 72) -> str:
    """Truncate title for the tertiary title button."""
    t = (full or "").strip()
    if not t:
        return "·"
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"
