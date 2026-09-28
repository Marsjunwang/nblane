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
    all_done = parse_kanban(profile).get(KANBAN_DONE) or []
    for title in wanted_titles:
        if sum(_clean(task.title) == title for task in all_done) > 1:
            raise ValueError(f"Ambiguous task title: {title}; select by id.")
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
    *,
    strict: bool = False,
) -> dict[str, Any]:
    """Attach only the snapshots explicitly attributed to each evidence row.

    Existing kanban_refs are the wire contract; source_task_ids is accepted
    as a draft-only alias. A single selected task is an unambiguous fallback.
    Ambiguous multi-task drafts fail before any evidence is written.
    """
    from nblane.core.ingest_merge import task_source_refs

    by_ref = {s["kanban_ref"]: s for s in snapshots if s.get("kanban_ref")}
    for row in patch.get("evidence_entries") or []:
        if not isinstance(row, dict):
            continue
        refs = task_source_refs(row)
        refs.update(kanban_ref(_clean(t)) for t in row.pop("source_task_ids", []) if _clean(t))
        if not refs and len(by_ref) == 1:
            refs = set(by_ref)
        selected_refs = refs & by_ref.keys()
        if strict and (not selected_refs or not refs <= by_ref.keys()):
            raise ValueError("Evidence source tasks are missing or outside the selection.")
        if not strict:
            selected_refs = set(by_ref)
        selected = [snap for ref, snap in by_ref.items() if ref in selected_refs]
        row["kanban_refs"] = list(dict.fromkeys([*(row.get("kanban_refs") or []), *[snap["kanban_ref"] for snap in selected]]))
        row["project_refs"] = list(dict.fromkeys([*(row.get("project_refs") or []), *[snap["project_id"] for snap in selected if snap.get("project_id")]]))
        row["origin"] = "kanban_task"
        if len(selected) == 1:
            row["origin_ref"] = selected[0]["kanban_ref"]
        else:
            row.pop("origin_ref", None)
        # The host owns provenance; model-supplied text is not a source snapshot.
        original = "\n\n---\n\n".join(snap["original_content"] for snap in selected)
        if not _clean(row.get("original_content")):
            row["original_content"] = original
            row["original_content_hash"] = content_hash(original)
            row["original_language"] = detect_language(original)
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
    """Apply selected source evidence and task flags as one recoverable write.

    Only success/failure is exposed. Normal errors restore all four files;
    a retry after interruption reuses evidence by stable task provenance.
    """
    from nblane.core import profile_io
    from nblane.core.evidence_review import confidence_for_origin, internal_project_goal_index
    from nblane.core.file_write import rollback_profile_files
    from nblane.core.goals import load_goal_book
    from nblane.core.ingest_apply import run_ingest_patch
    from nblane.core.ingest_merge import task_source_refs
    from nblane.core.ingest_parse import filter_ingest_patch

    profile_name = profile.name if isinstance(profile, Path) else str(profile)
    pdir = profile_io.profile_dir(profile_name)
    warnings: list[str] = []
    try:
        with git_backup.defer_changes(f"crystallize {profile_name}"), rollback_profile_files(pdir, (
            "evidence-pool.yaml", "skill-tree.yaml", "SKILL.md", "kanban.md",
        )):
            tasks, missing = resolve_done_tasks(profile_name, task_ids, titles)
            if missing or not tasks:
                raise ValueError(f"Selected Done tasks cannot be resolved: {missing}")
            # Title-only fallback must never mark multiple same-title tasks.
            if any(not _clean(task.id) for task in tasks):
                raise ValueError("Source tasks need stable ids; refresh candidates first.")
            filtered, warnings = filter_ingest_patch(
                patch, include_evidence=include_evidence, include_nodes=include_nodes,
            )
            if not filtered.evidence_entries:
                return {"ok": True, "errors": [], "warnings": list(warnings),
                        "new_evidence_ids": [], "crystallized_count": 0, "items": []}
            # Preserve the legacy no-op behavior for a patch consisting only
            # of blank evidence rows. Mixed patches remain invalid below.
            if all(not _clean(row.get("title")) for row in filtered.evidence_entries):
                return {"ok": True, "errors": [], "warnings": list(warnings),
                        "new_evidence_ids": [], "crystallized_count": 0, "items": []}
            if any(not _clean(row.get("title")) for row in filtered.evidence_entries):
                raise ValueError("Select at least one evidence row with a non-empty title.")
            attach_task_snapshots(
                {"evidence_entries": filtered.evidence_entries},
                [task_snapshot(task) for task in tasks], strict=True,
            )
            covered = set().union(*(task_source_refs(row) for row in filtered.evidence_entries))
            selected_tasks = [task for task in tasks if kanban_ref(task.id) in covered]
            projects = internal_project_goal_index(pdir)
            goal_ids = {goal.id for goal in load_goal_book(pdir).goals}
            for task in selected_tasks:
                pid = _clean(task.project_id)
                if not pid:
                    warnings.append(f"{task.id}: no project assigned; goal linkage remains incomplete.")
                    continue
                project = projects.get(pid)
                if (pdir / "project-board.yaml").exists() and (
                    not project or not project["goal_refs"] or not set(project["goal_refs"]) <= goal_ids
                ):
                    raise ValueError(f"{task.id}: project {pid} must exist and reference valid goals.")
            for row in filtered.evidence_entries:
                if not _clean(row.get("confidence")):
                    row["confidence"] = confidence_for_origin(row.get("origin"))
            before = profile_io.load_evidence_pool_raw(profile_name) or {}
            before_ids = {row.get("id") for row in before.get("evidence_entries", [])}
            merge, outcome = run_ingest_patch(
                profile_name, filtered, allow_status_change=allow_status_change,
                match_task_sources=True,
            )
            warnings.extend(outcome.warnings)
            if not outcome.ok:
                raise ValueError("; ".join([*merge.errors, *outcome.errors]))
            rows = (merge.merged_pool or {}).get("evidence_entries", [])
            if not all(any(ref in task_source_refs(row) for row in rows) for ref in covered):
                raise ValueError("Evidence does not cover every selected source task.")
            crystallized = mark_done_crystallized(
                profile_name, [task.id for task in selected_tasks],
            )
            current, missing = resolve_done_tasks(profile_name, [task.id for task in selected_tasks])
            if missing or any(not task.crystallized for task in current):
                raise ValueError("Could not mark all source tasks crystallized.")
            return {
                "ok": True, "errors": [], "warnings": list(dict.fromkeys(warnings)),
                "new_evidence_ids": [row["id"] for row in rows if row.get("id") not in before_ids],
                "crystallized_count": crystallized,
                "items": [{"task_id": task.id, "evidence_ids": [
                    row["id"] for row in rows if kanban_ref(task.id) in task_source_refs(row)
                ]} for task in selected_tasks],
            }
    except Exception as exc:
        return {
            "ok": False, "errors": [str(exc)], "warnings": warnings,
            "new_evidence_ids": [], "crystallized_count": 0, "items": [],
        }
