"""Streamlit glue for background Kanban AI jobs.

Thin session-state layer over ``core/kanban_ai_tasks``: the Kanban page's
event handler starts jobs here (never blocking on LLM calls), and a
``st.fragment`` poller moves finished results into the session keys the
board already consumes. The module-global ``st`` is patchable in tests,
mirroring ``evidence_editor_host``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

from nblane.core import kanban_ai_tasks
from nblane.core import llm as llm_client
from nblane.core.kanban_ai import (
    analyze_kanban_task_gap,
    generate_kanban_subtask_proposals_detailed,
    generate_kanban_task_alignment_options,
)
from nblane.core.kanban_merge import copy_kanban_sections
from nblane.core.models import KanbanTask
from nblane.core.profile_io import profile_dir
from nblane.web_shared import (
    refresh_file_snapshots,
    stash_git_backup_results,
)


def ai_jobs_key(profile: str, suffix: str) -> str:
    """Session key for in-flight background AI jobs of one profile/backend."""
    return f"kanban_ai_jobs_{profile}_{suffix}"


def _jobs(profile: str, suffix: str) -> dict[str, dict[str, str]]:
    jobs = st.session_state.setdefault(ai_jobs_key(profile, suffix), {})
    return jobs if isinstance(jobs, dict) else {}


def _start_tracked_job(
    profile: str,
    suffix: str,
    kanban_task_id: str,
    kind: str,
    runner: Callable[[], Any],
) -> dict[str, Any]:
    """Cancel the card's previous job, start *runner*, remember the job id."""
    jobs = _jobs(profile, suffix)
    previous = jobs.get(kanban_task_id)
    if isinstance(previous, dict) and previous.get("job_id"):
        kanban_ai_tasks.cancel_job(str(previous["job_id"]))
    snap = kanban_ai_tasks.start_job(
        profile=profile,
        kanban_task_id=kanban_task_id,
        kind=kind,
        runner=runner,
    )
    jobs[kanban_task_id] = {"job_id": str(snap.get("job_id") or ""), "kind": kind}
    return snap


def start_gap_job(
    profile: str,
    suffix: str,
    *,
    sections: dict[str, list[KanbanTask]],
    kanban_task_id: str,
    ai_backend: str,
    goal_context: str,
) -> dict[str, Any]:
    """Queue a background gap analysis for one kanban task."""
    sections_snapshot = copy_kanban_sections(sections)
    use_llm_router = ai_backend == "codex" or (
        ai_backend == "llm" and llm_client.is_configured()
    )

    def runner() -> Any:
        return analyze_kanban_task_gap(
            profile,
            sections_snapshot,
            kanban_task_id,
            use_rule_match=True,
            use_llm_router=use_llm_router,
            ai_backend=ai_backend,
            persist_router_keywords=False,
            goal_context=goal_context,
        )

    return _start_tracked_job(
        profile, suffix, kanban_task_id, kanban_ai_tasks.KIND_GAP, runner
    )


def start_alignment_job(
    profile: str,
    suffix: str,
    *,
    sections: dict[str, list[KanbanTask]],
    kanban_task_id: str,
    ai_backend: str,
    goal_context: str,
) -> dict[str, Any]:
    """Queue background task-understanding options for one kanban task."""
    sections_snapshot = copy_kanban_sections(sections)

    def runner() -> Any:
        return generate_kanban_task_alignment_options(
            sections_snapshot,
            kanban_task_id,
            profile_name=profile,
            record_activity=True,
            ai_backend=ai_backend,
            goal_context=goal_context,
        )

    return _start_tracked_job(
        profile,
        suffix,
        kanban_task_id,
        kanban_ai_tasks.KIND_ALIGNMENTS,
        runner,
    )


def start_subtasks_job(
    profile: str,
    suffix: str,
    *,
    sections: dict[str, list[KanbanTask]],
    kanban_task_id: str,
    ai_backend: str,
    goal_context: str,
    alignment_context: str,
    granularity: str,
    style_hint: str,
) -> dict[str, Any]:
    """Queue background AI subtask drafting for one kanban task."""
    sections_snapshot = copy_kanban_sections(sections)
    use_llm_router = ai_backend == "llm" and llm_client.is_configured()

    def runner() -> Any:
        return generate_kanban_subtask_proposals_detailed(
            profile,
            sections_snapshot,
            kanban_task_id,
            use_rule_match=True,
            use_llm_router=use_llm_router,
            persist_router_keywords=False,
            alignment_context=alignment_context,
            granularity=granularity,
            record_activity=ai_backend == "llm",
            ai_backend=ai_backend,
            goal_context=goal_context,
            subtask_style_hint=style_hint,
        )

    return _start_tracked_job(
        profile, suffix, kanban_task_id, kanban_ai_tasks.KIND_SUBTASKS, runner
    )


def cancel_tracked_job(profile: str, suffix: str, kanban_task_id: str) -> None:
    """Cancel any in-flight job for one card and forget it."""
    jobs = _jobs(profile, suffix)
    jobs.pop(kanban_task_id, None)
    kanban_ai_tasks.cancel_jobs_for_kanban_task(profile, kanban_task_id)


def pending_by_task(profile: str, suffix: str) -> dict[str, str]:
    """Return ``{kanban_task_id: job_kind}`` for cards with in-flight jobs."""
    out: dict[str, str] = {}
    for kanban_task_id, info in _jobs(profile, suffix).items():
        if not isinstance(info, dict):
            continue
        snap = kanban_ai_tasks.snapshot(str(info.get("job_id") or ""))
        if snap.get("status") == "running":
            out[str(kanban_task_id)] = str(info.get("kind") or "")
    return out


def collect_finished_jobs(
    profile: str,
    suffix: str,
    handle_result: Callable[[str, str, dict[str, Any]], None],
) -> bool:
    """Move finished job results to *handle_result*; True when any arrived.

    Runs in the Streamlit script (fragment), never in the worker thread, so
    it is the safe place to refresh file snapshots for the activity files
    the runners may have written (agent-activity.yaml / ai-runs.yaml) and to
    stash git-backup notices before the next save touches those files.
    """
    jobs = _jobs(profile, suffix)
    if not jobs:
        return False
    changed = False
    for kanban_task_id, info in list(jobs.items()):
        if not isinstance(info, dict):
            jobs.pop(kanban_task_id, None)
            continue
        job_id = str(info.get("job_id") or "")
        snap = kanban_ai_tasks.snapshot(job_id)
        if snap.get("status") not in kanban_ai_tasks.FINAL_STATUSES:
            continue
        jobs.pop(kanban_task_id, None)
        kanban_ai_tasks.drop_job(job_id)
        handle_result(
            str(kanban_task_id),
            str(info.get("kind") or ""),
            snap,
        )
        changed = True
    if changed:
        pdir = profile_dir(profile)
        refresh_file_snapshots(
            [
                pdir / "agent-activity.yaml",
                pdir / "ai-runs.yaml",
                pdir / "activity-log.yaml",
            ]
        )
        stash_git_backup_results()
    return changed
