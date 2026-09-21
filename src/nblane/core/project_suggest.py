"""AI ref-suggestion for project cases (shared by sync route and async job).

The computation lives in core so the web_api sync endpoint
(``POST .../project-board/cases/{id}/suggest-refs``) and the async-job
runner (``nblane.web_api.jobs``, kind ``project-suggest-refs``) share one
implementation: build the candidate option maps from the profile files,
run the ``project.suggest_refs`` gateway action (``require_review=True``
records the run to Agent Activity), and filter the model's picks against
the real option ids. Nothing is persisted — suggestions are confirm-not-fill.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from nblane.core import llm as llm_client
from nblane.core import profile_io
from nblane.core.ai.gateway import run_ai_action
from nblane.core.goals import load_goal_book
from nblane.core.kanban_io import parse_kanban
from nblane.core.project_board import ProjectCase
from nblane.core.project_board_events import clean_ref_list
from nblane.core.research_sources import load_research_sources
from nblane.core.yaml_io import _load_yaml_dict

SUGGEST_REF_FIELDS = (
    "goal_refs",
    "task_refs",
    "evidence_refs",
    "source_refs",
    "output_refs",
)

# Cap on candidates per field sent to the model (prompt-size guard).
_CANDIDATE_LIMIT = 80


class SuggestRefsError(RuntimeError):
    """Structured failure of one suggest-refs run (carries the API code)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class SuggestRefsResult:
    """Confirm-not-fill payload: suggestions filtered to real option ids."""

    backend: str = ""
    suggestions: dict[str, list[str]] = field(default_factory=dict)
    rationale: str = ""
    warnings: list[str] = field(default_factory=list)


def goal_ref_options(pdir: Path) -> dict[str, str]:
    book = load_goal_book(pdir)
    return {
        goal.id: f"{goal.title or goal.label or goal.id} · {goal.status}"
        for goal in book.goals
        if goal.id
    }


def task_ref_options(pdir: Path, case_id: str = "") -> dict[str, str]:
    """Task id -> label; tasks owned by another project are excluded.

    Used by the suggest-refs candidates where only claimable tasks make
    sense. The board GET keeps every task and exposes the owner for
    client-side filtering instead.
    """
    out: dict[str, str] = {}
    for section, tasks in parse_kanban(pdir).items():
        for task in tasks:
            if not task.id:
                continue
            owner = task.project_id
            if owner and owner != case_id:
                continue
            out[task.id] = f"[{section}] {task.title} · {task.id}"
    return out


def evidence_ref_options(pdir: Path) -> dict[str, str]:
    raw = profile_io.load_evidence_pool_raw(pdir) or {}
    out: dict[str, str] = {}
    for row in raw.get("evidence_entries") or []:
        if not isinstance(row, dict):
            continue
        eid = str(row.get("id", "") or "").strip()
        if not eid:
            continue
        title = str(row.get("title", "") or eid)
        status = str(row.get("review_status", "") or "")
        out[eid] = f"{title} · {status}" if status else title
    return out


def source_ref_options(pdir: Path) -> dict[str, str]:
    inbox_sources = load_research_sources(pdir)
    return {
        source.id: f"{source.title or source.id} · {source.status}"
        for source in inbox_sources.sources
        if source.id
    }


def output_ref_options(pdir: Path) -> dict[str, str]:
    raw = _load_yaml_dict(pdir / "outputs.yaml") or {}
    out: dict[str, str] = {}
    for item in raw.get("outputs") or []:
        if not isinstance(item, dict):
            continue
        oid = str(item.get("id", "") or "").strip()
        if oid:
            out[oid] = str(item.get("title", "") or oid)
    return out


def build_option_maps(pdir: Path, case: ProjectCase) -> dict[str, dict[str, str]]:
    """Candidate id -> label maps for the five suggestable ref fields."""
    return {
        "goal_refs": goal_ref_options(pdir),
        "task_refs": task_ref_options(pdir, case.id),
        "evidence_refs": evidence_ref_options(pdir),
        "source_refs": source_ref_options(pdir),
        "output_refs": output_ref_options(pdir),
    }


def suggest_case_refs(
    pdir: Path,
    case: ProjectCase,
    *,
    progress_callback: Callable[[str], None] | None = None,
) -> SuggestRefsResult:
    """Run the ``project.suggest_refs`` action for one case.

    Raises :class:`SuggestRefsError` (``project_suggest_refs_failed``) when
    the gateway run fails or no backend is available.
    ``progress_callback(stage)`` receives the real stages ``collecting``
    (candidate maps assembled) and ``suggesting`` (gateway call in flight)
    so async callers can report phases without inventing progress.
    """

    def report(stage: str) -> None:
        if progress_callback is not None:
            progress_callback(stage)

    report("collecting")
    option_maps = build_option_maps(pdir, case)
    payload = {
        "reply_language": llm_client.reply_language(),
        "project": {
            "id": case.id,
            "title": case.title,
            "status": case.status,
            "kind": case.kind,
            "summary": case.summary,
            "notes": case.notes,
        },
        "current_refs": {
            field: list(getattr(case, field)) for field in SUGGEST_REF_FIELDS
        },
        "candidates": {
            field: [
                {"id": ref, "label": label}
                for ref, label in list(options.items())[:_CANDIDATE_LIMIT]
            ]
            for field, options in option_maps.items()
        },
    }
    report("suggesting")
    result = run_ai_action(
        "project.suggest_refs",
        payload,
        profile=pdir.name,
        context_refs=[case.id],
        require_review=True,
    )
    if not result.ok:
        raise SuggestRefsError(
            "project_suggest_refs_failed",
            result.error or result.content or "AI ref suggestion failed.",
        )
    data = result.structured if isinstance(result.structured, dict) else {}
    suggestions = {
        field: [
            ref
            for ref in clean_ref_list(data.get(field))
            if ref in option_maps.get(field, {})
        ]
        for field in SUGGEST_REF_FIELDS
    }
    return SuggestRefsResult(
        backend=result.backend,
        suggestions=suggestions,
        rationale=str(data.get("rationale") or "").strip(),
        warnings=clean_ref_list(data.get("warnings")) + list(result.warnings),
    )
