"""Link evidence rows back to the kanban tasks they came from.

Evidence generated from Done tasks carries ``kanban_refs`` like ``kanban:<id>``.
The task id is deterministic (content + section hashed) and preserved through
archiving, so a ref captured at ingest still resolves after the task moves to
kanban-archive.md. These helpers attach refs at ingest and resolve them back to
the live ``KanbanTask`` (from kanban.md or kanban-archive.md) for display.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from nblane.core.kanban_io import (
    KANBAN_ARCHIVE_FILENAME,
    KANBAN_DONE,
    parse_kanban,
    parse_kanban_text,
)
from nblane.core.models import KanbanTask
from nblane.core.profile_io import profile_dir

KANBAN_REF_PREFIX = "kanban:"

# Archive groups tasks under "## Archived · DATE" headings, which parse_kanban_text
# does not recognize as a section. Rewrite them to the Done section so the shared
# parser can read archived tasks back into KanbanTask records.
_ARCHIVE_HEADING_RE = re.compile(r"^##\s+Archived\b.*$", re.MULTILINE)


def kanban_ref(task_id: str) -> str:
    """Build a kanban ref string from a task id."""
    return f"{KANBAN_REF_PREFIX}{str(task_id).strip()}"


def kanban_ref_id(ref: str) -> str:
    """Return the bare task id from a ``kanban:<id>`` ref (or "" if not one)."""
    text = str(ref or "").strip()
    if text.startswith(KANBAN_REF_PREFIX):
        return text[len(KANBAN_REF_PREFIX):].strip()
    return ""


def kanban_refs_for_tasks(tasks: Iterable[KanbanTask]) -> list[str]:
    """Return unique kanban refs for tasks that carry an id."""
    out: list[str] = []
    seen: set[str] = set()
    for task in tasks:
        task_id = str(getattr(task, "id", "") or "").strip()
        if not task_id:
            continue
        ref = kanban_ref(task_id)
        if ref not in seen:
            seen.add(ref)
            out.append(ref)
    return out


def add_kanban_refs_to_ingest_patch(
    patch: dict,
    kanban_refs: Iterable[str],
) -> dict:
    """Return an ingest patch whose evidence rows include kanban refs."""
    refs = [str(r).strip() for r in kanban_refs if str(r).strip()]
    if not refs:
        return dict(patch or {})
    out = dict(patch or {})
    rows = []
    for row in out.get("evidence_entries") or []:
        if not isinstance(row, dict):
            continue
        updated = dict(row)
        existing = [
            str(r).strip()
            for r in (updated.get("kanban_refs") or [])
            if str(r).strip()
        ]
        merged = list(existing)
        for ref in refs:
            if ref not in merged:
                merged.append(ref)
        updated["kanban_refs"] = merged
        rows.append(updated)
    out["evidence_entries"] = rows
    return out


def _archive_tasks(profile: str) -> list[KanbanTask]:
    """Parse kanban-archive.md into Done tasks (best effort)."""
    path = profile_dir(profile) / KANBAN_ARCHIVE_FILENAME
    if not isinstance(path, Path) or not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    normalized = _ARCHIVE_HEADING_RE.sub(f"## {KANBAN_DONE}", text)
    sections = parse_kanban_text(normalized, profile)
    return list(sections.get(KANBAN_DONE) or [])


def _all_lookup_tasks(profile: str) -> list[KanbanTask]:
    """Live kanban tasks (all sections) plus archived tasks."""
    tasks: list[KanbanTask] = []
    try:
        sections = parse_kanban(profile)
    except Exception:
        sections = {}
    for section_tasks in sections.values():
        tasks.extend(section_tasks)
    tasks.extend(_archive_tasks(profile))
    return tasks


def find_kanban_tasks_by_ref(
    profile: str,
    refs: Iterable[str],
) -> list[KanbanTask]:
    """Resolve kanban refs to KanbanTask records (id match, title fallback).

    Searches kanban.md (all sections) and kanban-archive.md. Returns one task
    per ref where a match is found, preserving ref order and de-duplicating.
    """
    wanted_ids: list[str] = []
    for ref in refs:
        rid = kanban_ref_id(ref)
        if rid and rid not in wanted_ids:
            wanted_ids.append(rid)
    if not wanted_ids:
        return []

    tasks = _all_lookup_tasks(profile)
    by_id: dict[str, KanbanTask] = {}
    for task in tasks:
        tid = str(getattr(task, "id", "") or "").strip()
        if tid and tid not in by_id:
            by_id[tid] = task

    found: list[KanbanTask] = []
    for rid in wanted_ids:
        task = by_id.get(rid)
        if task is not None:
            found.append(task)
    return found


__all__ = [
    "KANBAN_REF_PREFIX",
    "add_kanban_refs_to_ingest_patch",
    "find_kanban_tasks_by_ref",
    "kanban_ref",
    "kanban_ref_id",
    "kanban_refs_for_tasks",
]
