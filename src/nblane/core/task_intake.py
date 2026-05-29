"""Task intake helpers — create kanban tasks from other workflows.

This is a thin leaf module so callers (Gap Analysis, Research, etc.) can
turn an insight into a tracked task without duplicating the
parse -> append -> save -> sync dance. It deliberately imports from
``nblane.core.io`` and ``nblane.core.project_board_sync`` (never the
reverse) to stay out of the import cycle around ``core.io``.
"""

from __future__ import annotations

from nblane.core.io import parse_kanban, save_kanban
from nblane.core.models import KanbanTask
from nblane.core.project_board_sync import sync_project_board_from_kanban

_VALID_SECTIONS = {"Queue", "Doing", "Done", "Someday / Maybe"}


def _normalize_tags(tags: str | list[str] | tuple[str, ...] | None) -> str:
    """Return a comma-joined tag string from a str or iterable."""
    if not tags:
        return ""
    if isinstance(tags, str):
        return tags.strip()
    seen: list[str] = []
    for tag in tags:
        clean = str(tag).strip()
        if clean and clean not in seen:
            seen.append(clean)
    return ", ".join(seen)


def create_learning_task(
    profile: str,
    *,
    title: str,
    context: str = "",
    why: str = "",
    outcome: str = "",
    tags: str | list[str] | tuple[str, ...] | None = None,
    section: str = "Queue",
    project_id: str = "",
    milestone_id: str = "",
) -> KanbanTask:
    """Append a task to ``profile``'s kanban board and sync the project board.

    Returns the created :class:`KanbanTask`. ``section`` defaults to
    ``Queue`` so new tasks land in the backlog rather than in-progress.
    Raises ``ValueError`` on an empty title or unknown section.
    """
    clean_title = (title or "").strip()
    if not clean_title:
        raise ValueError("title is required")
    if section not in _VALID_SECTIONS:
        raise ValueError(f"unknown kanban section: {section!r}")

    task = KanbanTask(
        title=clean_title,
        context=(context or "").strip(),
        why=(why or "").strip(),
        outcome=(outcome or "").strip(),
        tags=_normalize_tags(tags),
        project_id=project_id,
        milestone_id=milestone_id,
    )
    sections = parse_kanban(profile)
    sections.setdefault(section, []).append(task)
    save_kanban(profile, sections)
    sync_project_board_from_kanban(profile, parse_kanban(profile))
    return task
