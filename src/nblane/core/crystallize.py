"""Crystallization: method drafts + the Done-task -> evidence state machine.

The Done-task crystallization flow used to live in two Streamlit pages
(``pages/2_Evidence_Review.py`` and ``pages/3_Kanban.py``) with divergent
mark-crystallized implementations. This module is the single home for that
state machine; both the SPA API (``web_api/routes_v1.py``) and the legacy
pages are expected to call here.

Rules (Phase 1 design, docs/zh/dev/phase1-evidence-page-design.md):

- Crystallize = snapshot: the task原文 (title/context/why and friends, via
  ``evidence_migrate.render_kanban_task_source``) is written into the
  evidence row's ``original_content`` + ``original_content_hash``, so the
  evidence is self-sufficient.
- ``kanban_refs`` stay as the provenance chain; dead refs (archived tasks)
  are tombstones in the UI, never hard validation errors.
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

from nblane.core import git_backup
from nblane.core.evidence_migrate import (
    content_hash,
    detect_language,
    render_kanban_task_source,
)
from nblane.core.file_write import atomic_write_text
from nblane.core.io import profile_dir
from nblane.core.kanban_archive import kanban_ref
from nblane.core.kanban_io import (
    KANBAN_DONE,
    materialize_kanban_task_ids,
    parse_kanban,
    save_kanban,
)
from nblane.core.models import KanbanTask


def _slug(s: str) -> str:
    """Return a filesystem-safe slug."""
    x = re.sub(r"[^a-zA-Z0-9._-]+", "-", s.strip().lower())
    return x.strip("-") or "session"


def write_method_draft(
    profile: str,
    project: str,
    body: str,
) -> Path:
    """Write ``profiles/{profile}/methods/{project}_draft.md``."""
    pdir = profile_dir(profile)
    mdir = pdir / "methods"
    mdir.mkdir(parents=True, exist_ok=True)
    slug = _slug(project)
    path = mdir / f"{slug}_draft.md"
    header = (
        f"# Method draft: {project}\n\n"
        "_Edit freely; this file is not overwritten "
        "automatically._\n\n"
    )
    atomic_write_text(path, header + body.strip() + "\n")
    git_backup.record_change(
        [path],
        action=f"write method draft for {profile}",
    )
    return path


# --- Done-task crystallization state machine --------------------------------


def _clean(value: object) -> str:
    return str(value or "").strip()


def done_tasks_by_id(
    profile: str | Path,
) -> tuple[dict[str, KanbanTask], dict[str, KanbanTask]]:
    """Return (by_id, by_title) indexes of the Done section tasks."""
    sections = parse_kanban(profile)
    by_id: dict[str, KanbanTask] = {}
    by_title: dict[str, KanbanTask] = {}
    for task in sections.get(KANBAN_DONE) or []:
        tid = _clean(getattr(task, "id", ""))
        title = _clean(getattr(task, "title", ""))
        if tid and tid not in by_id:
            by_id[tid] = task
        if title and title not in by_title:
            by_title[title] = task
    return by_id, by_title


def resolve_done_tasks(
    profile: str | Path,
    task_ids: Iterable[str],
    titles: Iterable[str] | None = None,
) -> tuple[list[KanbanTask], list[str]]:
    """Resolve Done tasks by id, falling back to exact title match.

    Returns (tasks, missing) where ``missing`` lists the requested ids /
    titles that no Done task matches (e.g. already archived).
    """
    wanted_ids = [_clean(t) for t in task_ids if _clean(t)]
    wanted_titles = [_clean(t) for t in (titles or []) if _clean(t)]
    by_id, by_title = done_tasks_by_id(profile)
    tasks: list[KanbanTask] = []
    missing: list[str] = []
    seen: set[int] = set()
    for tid in wanted_ids:
        task = by_id.get(tid)
        if task is None:
            missing.append(tid)
        elif id(task) not in seen:
            seen.add(id(task))
            tasks.append(task)
    for title in wanted_titles:
        task = by_title.get(title)
        if task is None:
            missing.append(title)
        elif id(task) not in seen:
            seen.add(id(task))
            tasks.append(task)
    return tasks, missing


def mark_done_crystallized(
    profile: str | Path,
    task_ids: Iterable[str],
    titles: Iterable[str] | None = None,
) -> int:
    """Set ``crystallized: true`` on matching Done tasks; returns the count.

    A task matches when its id is in *task_ids* or its title is in *titles*
    (title is the fallback for tasks that had no stable id at capture time).
    No-op (returns 0) when nothing matches; kanban.md is only written when at
    least one task actually flips.
    """
    wanted_ids = {_clean(t) for t in task_ids if _clean(t)}
    wanted_titles = {_clean(t) for t in (titles or []) if _clean(t)}
    if not wanted_ids and not wanted_titles:
        return 0
    sections = parse_kanban(profile)
    done_list = list(sections.get(KANBAN_DONE) or [])
    changed = 0
    for index, task in enumerate(done_list):
        if getattr(task, "crystallized", False):
            continue
        tid = _clean(getattr(task, "id", ""))
        title = _clean(getattr(task, "title", ""))
        if (tid and tid in wanted_ids) or (title and title in wanted_titles):
            done_list[index] = replace(task, crystallized=True)
            changed += 1
    if changed:
        sections[KANBAN_DONE] = done_list
        save_kanban(profile, sections)
    return changed


def task_snapshot(task: KanbanTask) -> dict[str, Any]:
    """Snapshot one Done task's原文 for embedding into an evidence row."""
    original = render_kanban_task_source(task)
    tid = _clean(getattr(task, "id", ""))
    project_id = _clean(getattr(task, "project_id", ""))
    return {
        "task_id": tid,
        "title": _clean(getattr(task, "title", "")),
        "completed_on": _clean(getattr(task, "completed_on", "") or ""),
        "project_id": project_id,
        "kanban_ref": kanban_ref(tid) if tid else "",
        "original_content": original,
        "original_content_hash": content_hash(original),
        "original_language": detect_language(original),
    }


def attach_task_snapshots(
    patch: dict[str, Any],
    snapshots: list[dict[str, Any]],
) -> dict[str, Any]:
    """Fill missing provenance/snapshot fields on patch evidence rows.

    Every evidence row gets the source kanban refs (union, de-duped) and the
    project refs of the source tasks. ``original_content`` / hash / language
    are only filled when the row does not carry them (LLM drafts may already
    have distilled content); the snapshot then joins all source tasks'原文 so
    the row stays auditable even when the task→row mapping is not 1:1.
    """
    entries = patch.get("evidence_entries")
    if not isinstance(entries, list) or not snapshots:
        return patch
    refs = [s["kanban_ref"] for s in snapshots if s.get("kanban_ref")]
    projects: list[str] = []
    for snap in snapshots:
        pid = _clean(snap.get("project_id"))
        if pid and pid not in projects:
            projects.append(pid)
    combined_original = "\n\n---\n\n".join(
        snap["original_content"]
        for snap in snapshots
        if _clean(snap.get("original_content"))
    )
    for row in entries:
        if not isinstance(row, dict):
            continue
        existing_refs = [
            _clean(r) for r in (row.get("kanban_refs") or []) if _clean(r)
        ]
        merged_refs = list(dict.fromkeys([*existing_refs, *refs]))
        if merged_refs:
            row["kanban_refs"] = merged_refs
        existing_projects = [
            _clean(p) for p in (row.get("project_refs") or []) if _clean(p)
        ]
        merged_projects = list(dict.fromkeys([*existing_projects, *projects]))
        if merged_projects:
            row["project_refs"] = merged_projects
        if not _clean(row.get("origin")):
            row["origin"] = "kanban_task"
        if not _clean(row.get("origin_ref")) and len(refs) == 1:
            row["origin_ref"] = refs[0]
        if not _clean(row.get("original_content")) and combined_original:
            row["original_content"] = combined_original
            row["original_content_hash"] = content_hash(combined_original)
            row.setdefault("original_language", detect_language(combined_original))
    return patch


def rule_crystallize_patch(tasks: list[KanbanTask]) -> dict[str, Any]:
    """Deterministic no-LLM draft: one毛坯 evidence row per Done task."""
    entries: list[dict[str, Any]] = []
    for task in tasks:
        snap = task_snapshot(task)
        if not snap["title"]:
            continue
        row: dict[str, Any] = {
            "type": "practice",
            "title": snap["title"],
            "review_status": "needs_review",
            "origin": "kanban_task",
            "original_content": snap["original_content"],
            "original_content_hash": snap["original_content_hash"],
            "original_language": snap["original_language"],
        }
        if snap["completed_on"]:
            row["date"] = snap["completed_on"]
        if snap["kanban_ref"]:
            row["origin_ref"] = snap["kanban_ref"]
            row["kanban_refs"] = [snap["kanban_ref"]]
        if snap["project_id"]:
            row["project_refs"] = [snap["project_id"]]
        entries.append(row)
    return {"evidence_entries": entries, "node_updates": []}


def apply_crystallization(
    profile: str | Path,
    patch: dict[str, Any],
    *,
    task_ids: Iterable[str] = (),
    titles: Iterable[str] | None = None,
    include_evidence: list[bool] | None = None,
    include_nodes: list[bool] | None = None,
    allow_status_change: bool = False,
) -> dict[str, Any]:
    """Apply a confirmed crystallization patch and mark the tasks crystallized.

    Runs the canonical ingest merge (validate + SKILL.md sync + rollback) via
    ``run_ingest_patch``; only when the apply succeeds are the source Done
    tasks marked ``crystallized``. Returns a summary dict with ``ok``,
    ``errors``, ``warnings``, ``new_evidence_ids`` and ``crystallized_count``.
    """
    from nblane.core import profile_io
    from nblane.core.ingest_apply import run_ingest_patch
    from nblane.core.ingest_parse import filter_ingest_patch

    profile_name = profile.name if isinstance(profile, Path) else str(profile)
    filtered, filter_warnings = filter_ingest_patch(
        patch,
        include_evidence=include_evidence,
        include_nodes=include_nodes,
    )
    # 置信度按 origin 自动推导(评审只留「分量」单维度);草稿已带的保留。
    from nblane.core.evidence_review import confidence_for_origin

    for row in filtered.evidence_entries:
        if isinstance(row, dict) and not _clean(row.get("confidence")):
            row["confidence"] = confidence_for_origin(row.get("origin"))
    before_raw = profile_io.load_evidence_pool_raw(profile_name) or {}
    before_ids = {
        _clean(row.get("id"))
        for row in (before_raw.get("evidence_entries") or [])
        if isinstance(row, dict) and _clean(row.get("id"))
    }
    merge, apply = run_ingest_patch(
        profile_name,
        filtered,
        allow_status_change=allow_status_change,
    )
    warnings = [*filter_warnings, *merge.warnings, *apply.warnings]
    errors = [*merge.errors, *apply.errors]
    if not apply.ok:
        return {
            "ok": False,
            "errors": errors,
            "warnings": warnings,
            "new_evidence_ids": [],
            "crystallized_count": 0,
        }
    after_raw = profile_io.load_evidence_pool_raw(profile_name) or {}
    new_ids = [
        _clean(row.get("id"))
        for row in (after_raw.get("evidence_entries") or [])
        if isinstance(row, dict)
        and _clean(row.get("id"))
        and _clean(row.get("id")) not in before_ids
    ]
    crystallized = mark_done_crystallized(profile_name, task_ids, titles)
    return {
        "ok": True,
        "errors": [],
        "warnings": warnings,
        "new_evidence_ids": new_ids,
        "crystallized_count": crystallized,
    }
