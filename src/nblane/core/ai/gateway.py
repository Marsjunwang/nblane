"""Unified AI Action Gateway."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from nblane.core import llm
from nblane.core.ai.actions import AIActionRequest, AIActionResult
from nblane.core.ai.backends import default_backends
from nblane.core.ai.router import choose_backend, get_action_spec
from nblane.core.ai.runs import (
    append_ai_run,
    new_run_id,
    record_activity_item,
)


def run_ai_action(
    action_name: str,
    payload: dict[str, Any] | None = None,
    *,
    context: Mapping[str, Any] | str | None = None,
    profile: str | None = None,
    context_refs: list[str] | None = None,
    preferred_backend: str | None = None,
    require_review: bool | None = None,
    backends: dict[str, Any] | None = None,
) -> AIActionResult:
    """Run a registered AI Action through the selected backend.

    Business code should call this instead of ``llm.chat`` or an external
    harness directly.
    """

    resolved_context = _normalize_context(context)
    resolved_profile = (
        profile
        if profile is not None
        else str(resolved_context.get("profile") or "")
    ).strip()
    refs = list(context_refs or resolved_context.get("context_refs") or [])
    preferred = (
        preferred_backend
        if preferred_backend is not None
        else resolved_context.get("preferred_backend")
    )
    review = (
        bool(require_review)
        if require_review is not None
        else bool(resolved_context.get("require_review", True))
    )
    request = AIActionRequest(
        action=str(action_name or "").strip(),
        profile=resolved_profile,
        payload=dict(payload or {}),
        context_refs=refs,
        preferred_backend=str(preferred).strip() if preferred else None,
        require_review=review,
    )
    spec = get_action_spec(request.action)
    if spec is None:
        return AIActionResult(
            ok=False,
            action=request.action,
            backend="",
            run_id=new_run_id(request.action or "unknown"),
            error=f"unknown_action: {request.action}",
        )
    registry = backends or default_backends()
    backend_name, route_error = choose_backend(request, spec, registry)
    if route_error:
        result = AIActionResult(
            ok=False,
            action=request.action,
            backend=backend_name,
            run_id=new_run_id(request.action),
            error=f"routing_error: {route_error}",
        )
        _record_if_profile(request, spec, result)
        return result
    backend = registry[backend_name]
    try:
        result = backend.run(request, spec)
    except Exception as exc:
        result = AIActionResult(
            ok=False,
            action=request.action,
            backend=backend_name,
            run_id=new_run_id(request.action),
            error=f"backend_error: {exc}",
        )
    if (
        not result.ok
        and request.preferred_backend is None
        and not result.error.startswith("validation_error")
        and spec.fallback_backend
        and spec.fallback_backend != result.backend
        and spec.fallback_backend in registry
    ):
        failed_backend = result.backend
        failed_error = result.error
        fallback = registry[spec.fallback_backend]
        result = fallback.run(request, spec)
        result.warnings.insert(
            0,
            f"{failed_backend} failed ({failed_error}); used {result.backend}.",
        )
    _record_if_profile(request, spec, result)
    return result


def run_text(
    action_name: str,
    payload: dict[str, Any] | None = None,
    *,
    context: Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> AIActionResult:
    """Run an action and return a normalized result for text consumers."""

    return run_ai_action(action_name, payload, context=context, **kwargs)


def run_json(
    action_name: str,
    payload: dict[str, Any] | None = None,
    *,
    context: Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> AIActionResult:
    """Run an action and return a normalized result for JSON consumers."""

    return run_ai_action(action_name, payload, context=context, **kwargs)


def draft_resume_for_job(
    profile: str,
    job_text: str,
    *,
    target: str = "",
    evidence: list[dict[str, Any]] | None = None,
    claims: list[dict[str, Any]] | None = None,
    projects: list[dict[str, Any]] | None = None,
    context_refs: list[str] | None = None,
) -> AIActionResult:
    """Typed helper for ``resume.target_for_job``."""

    return run_ai_action(
        "resume.target_for_job",
        {
            "job_text": job_text,
            "target": target,
            "evidence": evidence or [],
            "claims": claims or [],
            "projects": projects or [],
        },
        profile=profile,
        context_refs=context_refs or [],
    )


def recommend_research_sources(
    profile: str,
    goal: str,
    sources: list[dict[str, Any]],
    *,
    context_refs: list[str] | None = None,
) -> AIActionResult:
    """Typed helper for ``research.recommend_sources``."""

    return run_ai_action(
        "research.recommend_sources",
        {"goal": goal, "sources": sources},
        profile=profile,
        context_refs=context_refs or [],
    )


def generate_reading_draft(
    profile: str,
    source: dict[str, Any],
    *,
    excerpt: str = "",
    mode: str = "summary",
    context_refs: list[str] | None = None,
) -> AIActionResult:
    """Typed helper for ``research.reading_draft``."""

    return run_ai_action(
        "research.reading_draft",
        {"source": source, "excerpt": excerpt, "mode": mode},
        profile=profile,
        context_refs=context_refs or [],
    )


def search_papers_codex(
    profile: str,
    query: str,
    *,
    context_refs: list[str] | None = None,
    require_review: bool = True,
    payload: dict[str, Any] | None = None,
) -> AIActionResult:
    """Typed helper for ``research.paper_search_codex``."""

    body = dict(payload or {})
    body["query"] = query
    return run_ai_action(
        "research.paper_search_codex",
        body,
        profile=profile,
        context_refs=context_refs or [],
        require_review=require_review,
    )


def translate_paper_segments(
    profile: str,
    source_id: str,
    segments: list[dict[str, Any]],
    *,
    target_lang: str = "zh",
    context_refs: list[str] | None = None,
    require_review: bool = True,
) -> AIActionResult:
    """Typed helper for ``research.paper_translate``."""

    return run_ai_action(
        "research.paper_translate",
        {
            "source_id": source_id,
            "segments": segments,
            "target_lang": target_lang,
        },
        profile=profile,
        context_refs=context_refs or [source_id],
        require_review=require_review,
    )


def explain_paper_selection(
    profile: str,
    source_id: str,
    selected_text: str,
    *,
    context_refs: list[str] | None = None,
    payload: dict[str, Any] | None = None,
    require_review: bool = True,
) -> AIActionResult:
    """Typed helper for ``research.paper_explain_selection``."""

    body = dict(payload or {})
    body.update({"source_id": source_id, "selected_text": selected_text})
    return run_ai_action(
        "research.paper_explain_selection",
        body,
        profile=profile,
        context_refs=context_refs or [source_id],
        require_review=require_review,
    )


def generate_paper_source_guide(
    profile: str,
    source_id: str,
    *,
    segments: list[dict[str, Any]] | None = None,
    chunks: list[dict[str, Any]] | None = None,
    annotations: list[dict[str, Any]] | None = None,
    source: dict[str, Any] | None = None,
    context_refs: list[str] | None = None,
    require_review: bool = True,
) -> AIActionResult:
    """Typed helper for ``research.paper_source_guide``."""

    return run_ai_action(
        "research.paper_source_guide",
        {
            "source_id": source_id,
            "source": source or {},
            "segments": segments or [],
            "chunks": chunks or [],
            "annotations": annotations or [],
        },
        profile=profile,
        context_refs=context_refs or [source_id],
        require_review=require_review,
    )


def generate_paper_review_card(
    profile: str,
    source_id: str,
    *,
    source: dict[str, Any] | None = None,
    segments: list[dict[str, Any]] | None = None,
    chunks: list[dict[str, Any]] | None = None,
    annotations: list[dict[str, Any]] | None = None,
    context_refs: list[str] | None = None,
    require_review: bool = True,
) -> AIActionResult:
    """Typed helper for ``research.paper_review_card``."""

    return run_ai_action(
        "research.paper_review_card",
        {
            "source_id": source_id,
            "source": source or {},
            "segments": segments or [],
            "chunks": chunks or [],
            "annotations": annotations or [],
        },
        profile=profile,
        context_refs=context_refs or [source_id],
        require_review=require_review,
    )


def answer_paper_question(
    profile: str,
    source_id: str,
    question: str,
    *,
    context_refs: list[str] | None = None,
    payload: dict[str, Any] | None = None,
    require_review: bool = True,
) -> AIActionResult:
    """Typed helper for ``research.paper_qa``."""

    body = dict(payload or {})
    body.update({"source_id": source_id, "question": question})
    return run_ai_action(
        "research.paper_qa",
        body,
        profile=profile,
        context_refs=context_refs or [source_id],
        require_review=require_review,
    )


def extract_paper_claims(
    profile: str,
    source_id: str,
    *,
    segments: list[dict[str, Any]] | None = None,
    chunks: list[dict[str, Any]] | None = None,
    context_refs: list[str] | None = None,
    require_review: bool = True,
) -> AIActionResult:
    """Typed helper for ``research.paper_claim_extract``."""

    return run_ai_action(
        "research.paper_claim_extract",
        {"source_id": source_id, "segments": segments or [], "chunks": chunks or []},
        profile=profile,
        context_refs=context_refs or [source_id],
        require_review=require_review,
    )


def deep_read_paper_codex(
    profile: str,
    source_id: str,
    *,
    context_refs: list[str] | None = None,
    payload: dict[str, Any] | None = None,
    require_review: bool = True,
) -> AIActionResult:
    """Typed helper for ``research.paper_deep_read_codex``."""

    body = dict(payload or {})
    body["source_id"] = source_id
    return run_ai_action(
        "research.paper_deep_read_codex",
        body,
        profile=profile,
        context_refs=context_refs or [source_id],
        require_review=require_review,
    )


def compare_papers_codex(
    profile: str,
    source_ids: list[str],
    *,
    context_refs: list[str] | None = None,
    payload: dict[str, Any] | None = None,
    require_review: bool = True,
) -> AIActionResult:
    """Typed helper for ``research.paper_compare_codex``."""

    body = dict(payload or {})
    body["source_ids"] = source_ids
    return run_ai_action(
        "research.paper_compare_codex",
        body,
        profile=profile,
        context_refs=context_refs or source_ids,
        require_review=require_review,
    )


def draft_kanban_task_alignment(
    profile: str,
    *,
    task_id: str,
    task_title: str,
    task_text: str,
    ai_context: str = "",
    reply_language: str | None = None,
    context_refs: list[str] | None = None,
    require_review: bool = False,
) -> AIActionResult:
    """Typed helper for ``kanban.task_alignment``."""

    return run_ai_action(
        "kanban.task_alignment",
        {
            "task_id": task_id,
            "task_title": task_title,
            "task_text": task_text,
            "ai_context": ai_context,
            "reply_language": _reply_language_value(reply_language),
        },
        profile=profile if require_review else "",
        context_refs=context_refs or [],
        require_review=require_review,
    )


def draft_kanban_subtasks(
    profile: str,
    *,
    task_id: str,
    task_title: str,
    task_text: str,
    existing_subtasks: str,
    gap_analysis: str,
    allowed_gap_ids: list[str],
    alignment_context: str = "",
    ai_context: str = "",
    granularity: str = "milestone",
    subtask_style_hint: str = "",
    reply_language: str | None = None,
    context_refs: list[str] | None = None,
    require_review: bool = False,
) -> AIActionResult:
    """Typed helper for ``kanban.subtasks``."""

    return run_ai_action(
        "kanban.subtasks",
        {
            "task_id": task_id,
            "task_title": task_title,
            "task_text": task_text,
            "existing_subtasks": existing_subtasks,
            "gap_analysis": gap_analysis,
            "allowed_gap_ids": allowed_gap_ids,
            "alignment_context": alignment_context,
            "ai_context": ai_context,
            "granularity": granularity,
            "subtask_style_hint": subtask_style_hint,
            "reply_language": _reply_language_value(reply_language),
        },
        profile=profile if require_review else "",
        context_refs=context_refs or [],
        require_review=require_review,
    )


def create_remote_dev_task(
    profile: str,
    title: str,
    *,
    target_harness: str = "codex",
    input_refs: list[str] | None = None,
    expected_outputs: list[str] | None = None,
    related: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> AIActionResult:
    """Typed helper for ``work.remote_dev_task``."""

    body = dict(payload or {})
    body.update(
        {
            "title": title,
            "target_harness": target_harness,
            "input_refs": input_refs or [],
            "expected_outputs": expected_outputs or [],
            "related": related or {},
        }
    )
    return run_ai_action(
        "work.remote_dev_task",
        body,
        profile=profile,
        context_refs=input_refs or [],
    )


def _normalize_context(
    context: Mapping[str, Any] | str | None,
) -> dict[str, Any]:
    if isinstance(context, str):
        return {"profile": context}
    if isinstance(context, Mapping):
        return dict(context)
    return {}


def _reply_language_value(value: str | None) -> str:
    """Return the action payload reply language."""

    clean = str(value or "").strip().lower()
    if clean in ("en", "zh"):
        return clean
    return llm.reply_language()


def _record_if_profile(
    request: AIActionRequest,
    spec: Any,
    result: AIActionResult,
) -> None:
    if not request.profile:
        return
    activity_id = record_activity_item(
        request.profile,
        request,
        spec,
        result,
    )
    if activity_id:
        result.activity_item_id = activity_id
    append_ai_run(
        request.profile,
        request,
        spec,
        result,
        activity_item_id=activity_id,
    )


__all__ = [
    "answer_paper_question",
    "compare_papers_codex",
    "create_remote_dev_task",
    "deep_read_paper_codex",
    "draft_kanban_subtasks",
    "draft_kanban_task_alignment",
    "draft_resume_for_job",
    "explain_paper_selection",
    "extract_paper_claims",
    "generate_paper_review_card",
    "generate_reading_draft",
    "generate_paper_source_guide",
    "recommend_research_sources",
    "run_ai_action",
    "run_json",
    "run_text",
    "search_papers_codex",
    "translate_paper_segments",
]
