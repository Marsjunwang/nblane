"""Pure payload<->dataclass mapping for the custom project board component.

The Streamlit page (`pages/11_Project_Board.py`) owns persistence, validation
messaging, and reruns. This module holds only the side-effect-free mapping
between component event payloads and project-board dataclasses, so it can be
unit-tested without importing the page or Streamlit.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
import re

from nblane.core.models import KanbanTask
from nblane.core.project_board import ProjectCase, ProjectMilestone

CASE_SIMPLE_FIELDS = (
    "title",
    "status",
    "kind",
    "visibility",
    "time_range",
    "summary",
    "notes",
)
CASE_REF_FIELDS = (
    "goal_refs",
    "task_refs",
    "evidence_refs",
    "source_refs",
    "experience_refs",
    "output_refs",
)
MILESTONE_SIMPLE_FIELDS = ("title", "status", "target", "date", "summary")
MILESTONE_REF_FIELDS = ("task_refs", "evidence_refs", "source_refs", "output_refs")
ISO_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def clean_ref_list(values: object) -> list[str]:
    """Strip, de-dupe (order-preserving), and drop empties from a ref list."""
    if not isinstance(values, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = str(value or "").strip()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def clean_iso_date(value: object) -> str:
    """Return the leading YYYY-MM-DD date, or blank when absent."""
    match = ISO_DATE_RE.match(str(value or "").strip())
    if not match:
        return ""
    clean = match.group(1)
    try:
        date.fromisoformat(clean)
    except ValueError:
        return ""
    return clean


def format_date_range(start: str, end: str) -> str:
    """Format a compact project date range for project-board payloads."""
    clean_start = clean_iso_date(start)
    clean_end = clean_iso_date(end)
    if clean_start and clean_end and clean_end < clean_start:
        clean_start, clean_end = clean_end, clean_start
    if clean_start and clean_end:
        return clean_start if clean_start == clean_end else f"{clean_start}/{clean_end}"
    return clean_start or clean_end


def timeline_date_range(rows: list[dict]) -> str:
    """Infer a project's date range from its timeline task rows.

    The range uses the earliest and latest available task dates, considering
    started_on, completed_on, and anchor so a long-running task contributes both
    ends when both dates are present.
    """
    dates: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in ("started_on", "completed_on", "anchor"):
            clean = clean_iso_date(row.get(key))
            if clean:
                dates.append(clean)
    if not dates:
        return ""
    return format_date_range(min(dates), max(dates))


def case_payload(case: ProjectCase) -> dict:
    """Serialize a ProjectCase into the component's `case` payload."""
    out: dict[str, object] = {"id": case.id}
    for field in CASE_SIMPLE_FIELDS:
        out[field] = getattr(case, field)
    for field in CASE_REF_FIELDS:
        out[field] = list(getattr(case, field))
    return out


def milestone_payload(milestone: ProjectMilestone, *, done: int = 0, total: int = 0) -> dict:
    """Serialize a ProjectMilestone (plus completion counts) for the component."""
    out: dict[str, object] = {"id": milestone.id}
    for field in MILESTONE_SIMPLE_FIELDS:
        out[field] = getattr(milestone, field)
    for field in MILESTONE_REF_FIELDS:
        out[field] = list(getattr(milestone, field))
    out["done_count"] = int(done)
    out["total_count"] = int(total)
    return out


def case_from_event(original: ProjectCase, fields: dict) -> ProjectCase:
    """Build the submitted ProjectCase from an event payload's `fields`.

    Raises ValueError when the title is blank. Simple fields fall back to the
    original value when missing; ref fields are cleaned lists.
    """
    fields = fields if isinstance(fields, dict) else {}
    title = str(fields.get("title", "") or "").strip()
    if not title:
        raise ValueError("title_required")
    changes: dict[str, object] = {"title": title}
    for field in ("status", "kind", "visibility"):
        changes[field] = str(fields.get(field) or getattr(original, field))
    for field in ("time_range", "summary", "notes"):
        changes[field] = str(fields.get(field, "") or "").strip()
    for field in CASE_REF_FIELDS:
        changes[field] = clean_ref_list(fields.get(field))
    return replace(original, **changes)


def milestone_from_event(original: ProjectMilestone, fields: dict) -> ProjectMilestone:
    """Build the submitted ProjectMilestone from an event payload's `fields`."""
    fields = fields if isinstance(fields, dict) else {}
    title = str(fields.get("title", "") or "").strip()
    if not title:
        raise ValueError("title_required")
    changes: dict[str, object] = {
        "title": title,
        "status": str(fields.get("status") or original.status),
        "target": str(fields.get("target", "") or "").strip(),
        "date": str(fields.get("date", "") or "").strip(),
        "summary": str(fields.get("summary", "") or "").strip(),
    }
    for field in MILESTONE_REF_FIELDS:
        changes[field] = clean_ref_list(fields.get(field))
    return replace(original, **changes)


def task_anchor(task: KanbanTask) -> str:
    """Pick the timeline anchor date for a task: completed first, else started.

    Returns an ISO date string, or "" when the task has neither date.
    """
    completed = str(getattr(task, "completed_on", "") or "").strip()
    if completed:
        return completed
    return str(getattr(task, "started_on", "") or "").strip()


def task_owned_by_case(task: KanbanTask, case: ProjectCase) -> bool:
    """True when a task belongs to a project (via project_id or the case refs)."""
    task_id = str(getattr(task, "id", "") or "").strip()
    if getattr(task, "project_id", "") == case.id:
        return True
    return bool(task_id) and task_id in set(case.task_refs)


def timeline_tasks(
    case: ProjectCase,
    section_tasks: list[tuple[str, KanbanTask]],
    archived_tasks: list[KanbanTask],
    *,
    archived_section: str = "Done",
) -> list[dict]:
    """Build timeline task rows for one project, dropping tasks with no anchor.

    ``section_tasks`` is ``[(section_name, task)]`` from the live board;
    ``archived_tasks`` is the archived KanbanTask list. Tasks are kept only when
    they belong to ``case`` and have an anchor date (completed_on or started_on).
    De-duped by task id (live wins over archive). Returns rows sorted by anchor.
    """
    rows: list[dict] = []
    seen: set[str] = set()

    def add(task: KanbanTask, section: str, archived: bool) -> None:
        if not task_owned_by_case(task, case):
            return
        anchor = task_anchor(task)
        if not anchor:
            return
        task_id = str(getattr(task, "id", "") or "").strip()
        if task_id and task_id in seen:
            return
        if task_id:
            seen.add(task_id)
        rows.append(
            {
                "id": task_id,
                "title": getattr(task, "title", "") or "",
                "section": section,
                "anchor": anchor,
                "done": bool(getattr(task, "done", False)),
                "milestone_id": getattr(task, "milestone_id", "") or "",
                "archived": archived,
                "context": getattr(task, "context", "") or "",
                "why": getattr(task, "why", "") or "",
                "outcome": getattr(task, "outcome", "") or "",
                "started_on": str(getattr(task, "started_on", "") or ""),
                "completed_on": str(getattr(task, "completed_on", "") or ""),
                "tags": list(getattr(task, "tags", []) or []),
                "subtasks": [
                    {
                        "title": getattr(sub, "title", "") or "",
                        "done": bool(getattr(sub, "done", False)),
                    }
                    for sub in (getattr(task, "subtasks", []) or [])
                ],
                "subtask_count": len(getattr(task, "subtasks", []) or []),
            }
        )

    for section, task in section_tasks:
        add(task, section, False)
    for task in archived_tasks:
        add(task, archived_section, True)

    rows.sort(key=lambda row: row["anchor"])
    return rows


def count_no_anchor_tasks(
    case: ProjectCase,
    section_tasks: list[tuple[str, KanbanTask]],
) -> int:
    """Count project tasks (live) that have no anchor date -- not shown on axis."""
    total = 0
    for _section, task in section_tasks:
        if task_owned_by_case(task, case) and not task_anchor(task):
            total += 1
    return total
