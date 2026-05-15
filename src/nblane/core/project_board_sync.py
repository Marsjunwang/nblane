"""Workspace sync helpers for internal Project Board links."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable

from nblane.core.io import (
    KANBAN_SECTIONS,
    KanbanTask,
    load_evidence_pool_raw,
    parse_kanban,
    profile_dir,
    save_evidence_pool,
    save_kanban,
)
from nblane.core.project_board import (
    ProjectBoard,
    ProjectCase,
    load_project_board,
    save_project_board,
)
from nblane.core.research_sources import (
    load_research_sources,
    save_research_sources,
)


@dataclass
class ProjectSyncResult:
    """Files changed and non-fatal sync warnings."""

    changed_paths: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _clean_list(values: object) -> list[str]:
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes)):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = _clean_text(value)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _merge_unique(*groups: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            clean = _clean_text(item)
            if clean and clean not in seen:
                seen.add(clean)
                out.append(clean)
    return out


def _iter_tasks(
    sections: dict[str, list[KanbanTask]],
) -> Iterable[tuple[str, int, KanbanTask]]:
    for section in KANBAN_SECTIONS:
        for index, task in enumerate(sections.get(section, [])):
            yield section, index, task


def _set_project_ref(refs: object, project_id: str, selected: bool) -> list[str]:
    existing = _clean_list(refs)
    if selected:
        return _merge_unique(existing, [project_id])
    return [ref for ref in existing if ref != project_id]


def _milestone_by_task(case: ProjectCase) -> dict[str, str]:
    out: dict[str, str] = {}
    for milestone in case.milestones:
        if not milestone.id:
            continue
        for task_id in milestone.task_refs:
            out.setdefault(task_id, milestone.id)
    return out


def _desired_task_refs(case: ProjectCase) -> list[str]:
    groups: list[Iterable[str]] = [case.task_refs]
    groups.extend(milestone.task_refs for milestone in case.milestones)
    return _merge_unique(*groups)


def _desired_evidence_refs(case: ProjectCase) -> list[str]:
    groups: list[Iterable[str]] = [case.evidence_refs]
    groups.extend(milestone.evidence_refs for milestone in case.milestones)
    return _merge_unique(*groups)


def _desired_source_refs(case: ProjectCase) -> list[str]:
    groups: list[Iterable[str]] = [case.source_refs]
    groups.extend(milestone.source_refs for milestone in case.milestones)
    return _merge_unique(*groups)


def _desired_output_refs(case: ProjectCase) -> list[str]:
    groups: list[Iterable[str]] = [case.output_refs]
    groups.extend(milestone.output_refs for milestone in case.milestones)
    return _merge_unique(*groups)


def _case_by_id(board: ProjectBoard, project_id: str) -> ProjectCase | None:
    for case in board.project_cases:
        if case.id == project_id:
            return case
    return None


def _same_pool_refs(a: dict, b: dict) -> bool:
    return (a.get("evidence_entries") or []) == (b.get("evidence_entries") or [])


def sync_project_case_workspace(
    profile: str,
    board: ProjectBoard,
    project_id: str,
) -> ProjectSyncResult:
    """Sync one project case into Kanban, evidence pool, and research sources.

    The project board is the source of truth for refs in this flow. Tasks that
    already belong to another project are not stolen; they are dropped from this
    project's task refs and reported as warnings.
    """

    result = ProjectSyncResult()
    case = _case_by_id(board, project_id)
    if case is None:
        result.warnings.append(f"Unknown project: {project_id}")
        return result

    pdir = profile_dir(profile)
    desired_tasks = _desired_task_refs(case)
    milestone_for_task = _milestone_by_task(case)
    accepted_tasks: list[str] = []
    accepted_by_milestone: dict[str, list[str]] = {
        milestone.id: []
        for milestone in case.milestones
        if milestone.id
    }

    sections = parse_kanban(profile)
    kanban_changed = False
    desired_set = set(desired_tasks)
    for section, index, task in _iter_tasks(sections):
        if not task.id:
            continue
        wants_task = task.id in desired_set
        current_project = _clean_text(task.project_id)
        next_task = task
        if wants_task:
            if current_project and current_project != project_id:
                result.warnings.append(
                    f"{task.id} already belongs to {current_project}; "
                    f"not linked to {project_id}."
                )
                continue
            milestone_id = _clean_text(milestone_for_task.get(task.id))
            next_task = replace(
                task,
                project_id=project_id,
                milestone_id=milestone_id,
            )
            accepted_tasks.append(task.id)
            if milestone_id:
                accepted_by_milestone.setdefault(milestone_id, []).append(task.id)
        elif current_project == project_id:
            next_task = replace(task, project_id="", milestone_id="")
        if next_task != task:
            sections[section][index] = next_task
            kanban_changed = True

    case.task_refs = [task_id for task_id in desired_tasks if task_id in set(accepted_tasks)]
    for milestone in case.milestones:
        milestone.task_refs = accepted_by_milestone.get(milestone.id, [])

    case.evidence_refs = _desired_evidence_refs(case)
    case.source_refs = _desired_source_refs(case)
    case.output_refs = _desired_output_refs(case)

    pool_raw = load_evidence_pool_raw(profile) or {
        "profile": profile,
        "evidence_entries": [],
    }
    pool_before = dict(pool_raw)
    entries = []
    desired_evidence = set(case.evidence_refs)
    for row in pool_raw.get("evidence_entries") or []:
        if not isinstance(row, dict):
            continue
        updated = dict(row)
        row_id = _clean_text(updated.get("id"))
        updated["project_refs"] = _set_project_ref(
            updated.get("project_refs"),
            project_id,
            row_id in desired_evidence,
        )
        if not updated["project_refs"]:
            updated.pop("project_refs", None)
        entries.append(updated)
    pool_raw["profile"] = profile
    pool_raw["evidence_entries"] = entries

    sources = load_research_sources(profile)
    sources_before = sources.to_dict()
    desired_sources = set(case.source_refs)
    for source in sources.sources:
        source.project_refs = _set_project_ref(
            source.project_refs,
            project_id,
            source.id in desired_sources,
        )

    save_project_board(profile, board)
    result.changed_paths.append(pdir / "project-board.yaml")
    if kanban_changed:
        save_kanban(profile, sections)
        result.changed_paths.append(pdir / "kanban.md")
    if not _same_pool_refs(pool_before, pool_raw):
        save_evidence_pool(profile, pool_raw)
        result.changed_paths.append(pdir / "evidence-pool.yaml")
    if sources_before != sources.to_dict():
        save_research_sources(profile, sources)
        result.changed_paths.append(pdir / "research" / "sources.yaml")

    return result


def sync_project_board_from_kanban(
    profile: str,
    sections: dict[str, list[KanbanTask]],
) -> ProjectSyncResult:
    """Treat Kanban task project metadata as source of truth for task refs."""

    board = load_project_board(profile)
    project_task_refs: dict[str, list[str]] = {}
    milestone_task_refs: dict[tuple[str, str], list[str]] = {}
    project_ids = set(board.by_id())
    result = ProjectSyncResult()

    for _section, _index, task in _iter_tasks(sections):
        project_id = _clean_text(task.project_id)
        task_id = _clean_text(task.id)
        if not project_id or not task_id:
            continue
        if project_id not in project_ids:
            result.warnings.append(f"{task_id}: unknown project {project_id}")
            continue
        project_task_refs.setdefault(project_id, []).append(task_id)
        milestone_id = _clean_text(task.milestone_id)
        if milestone_id:
            milestone_task_refs.setdefault((project_id, milestone_id), []).append(task_id)

    changed = False
    for case in board.project_cases:
        next_refs = _clean_list(project_task_refs.get(case.id, []))
        if case.task_refs != next_refs:
            case.task_refs = next_refs
            changed = True
        known_milestones = {milestone.id for milestone in case.milestones}
        for milestone in case.milestones:
            next_m_refs = _clean_list(
                milestone_task_refs.get((case.id, milestone.id), [])
            )
            if milestone.task_refs != next_m_refs:
                milestone.task_refs = next_m_refs
                changed = True
        for (project_id, milestone_id), task_refs in milestone_task_refs.items():
            if project_id == case.id and milestone_id not in known_milestones:
                result.warnings.append(
                    f"{', '.join(task_refs)}: unknown milestone {milestone_id}"
                )

    if changed:
        save_project_board(profile, board)
        result.changed_paths.append(profile_dir(profile) / "project-board.yaml")
    return result


def project_refs_for_tasks(tasks: Iterable[KanbanTask]) -> list[str]:
    """Return unique project ids from Kanban tasks."""

    return _merge_unique(
        [_clean_text(task.project_id) for task in tasks if _clean_text(task.project_id)]
    )


def add_project_refs_to_ingest_patch(
    patch: dict,
    project_refs: Iterable[str],
) -> dict:
    """Return an ingest patch whose evidence rows include project refs."""

    refs = _clean_list(list(project_refs))
    if not refs:
        return dict(patch or {})
    out = dict(patch or {})
    rows = []
    for row in out.get("evidence_entries") or []:
        if not isinstance(row, dict):
            continue
        updated = dict(row)
        updated["project_refs"] = _merge_unique(
            _clean_list(updated.get("project_refs") or []),
            refs,
        )
        rows.append(updated)
    out["evidence_entries"] = rows
    return out


__all__ = [
    "ProjectSyncResult",
    "add_project_refs_to_ingest_patch",
    "project_refs_for_tasks",
    "sync_project_board_from_kanban",
    "sync_project_case_workspace",
]
