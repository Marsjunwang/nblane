"""Unified AI Action Gateway."""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
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
from nblane.core.web_preferences import (
    AI_ACTION_DEFAULT_BACKENDS,
    LOCAL_TRANSLATION_SCOPE_DEFAULTS,
    codex_effort_value,
    load_web_preferences,
)
from nblane.core.ai.local_translation import LOCAL_TRANSLATION_BACKEND, is_available as local_translation_available


PAPER_TRANSLATION_MODEL_TIMEOUT_SECONDS_DEFAULT = 180.0
# Whole-paper analysis streams its reply; this bounds the gap between chunks
# and the connection, not the total generation time.
PAPER_ANALYSIS_MODEL_TIMEOUT_SECONDS_DEFAULT = 300.0


def run_ai_action(
    action_name: str,
    payload: dict[str, Any] | None = None,
    *,
    context: Mapping[str, Any] | str | None = None,
    profile: str | None = None,
    runtime_profile: str | None = None,
    context_refs: list[str] | None = None,
    preferred_backend: str | None = None,
    require_review: bool | None = None,
    backends: dict[str, Any] | None = None,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
    cancel_callback: Callable[[], bool] | None = None,
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
        runtime_profile=(runtime_profile if runtime_profile is not None else resolved_profile).strip(),
        progress_callback=progress_callback,
        cancel_callback=cancel_callback,
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
    started = time.monotonic()
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
        and result.backend == LOCAL_TRANSLATION_BACKEND
        and request.action == "research.paper_translate"
    ):
        # Local translation is an acceleration path. Keep the existing LLM as
        # the quality fallback when a model is missing or cannot handle input.
        fallback = registry.get("direct_llm")
        if fallback is not None:
            local_error = result.error
            result = fallback.run(request, spec)
            result.warnings.insert(0, f"Local translation unavailable ({local_error}); used {result.backend}.")
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
        primary_ms = _elapsed_ms(started)
        # Keep the failed run's diagnostics (e.g. Codex reconnects / last
        # output before a timeout) so the job shows why it failed.
        failed_notes = [
            str(item)
            for item in result.warnings or []
            if str(item) and str(item) != failed_error
        ]
        fallback = registry[spec.fallback_backend]
        result = fallback.run(request, spec)
        result.warnings[0:0] = [
            f"{failed_backend} failed ({failed_error}); used {result.backend}.",
            *failed_notes,
        ]
        result.primary_duration_ms = primary_ms
    result.duration_ms = _elapsed_ms(started)
    _record_if_profile(request, spec, result)
    return result


def _elapsed_ms(started: float) -> int:
    return max(0, int(round((time.monotonic() - started) * 1000)))


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
    body, preferred_backend = _with_action_ai_preferences(
        profile,
        "research.paper_search_codex",
        body,
    )
    return run_ai_action(
        "research.paper_search_codex",
        body,
        profile=profile,
        context_refs=context_refs or [],
        preferred_backend=preferred_backend,
        require_review=require_review,
    )


def translate_paper_segments(
    profile: str,
    source_id: str,
    segments: list[dict[str, Any]],
    *,
    target_lang: str = "zh",
    model: str | None = None,
    model_timeout_seconds: float | None = None,
    context_refs: list[str] | None = None,
    require_review: bool = True,
    scope: str = "",
) -> AIActionResult:
    """Typed helper for ``research.paper_translate``.

    ``scope`` is ``selection``, ``visible`` or ``full``. When a local model is
    installed, the profile's ``ai.local_translation`` routing decides per
    scope whether it runs locally (falling back to the LLM on failure) or on
    the configured AI backend. Without a scope the local model is used only
    when no backend preference is set (legacy behavior).
    """

    body, preferred_backend = _with_action_ai_preferences(
        profile,
        "research.paper_translate",
        {
            "source_id": source_id,
            "segments": segments,
            "target_lang": target_lang,
            "model_timeout_seconds": (
                model_timeout_seconds
                if model_timeout_seconds is not None
                else _paper_translation_model_timeout_seconds()
            ),
        },
        model=model,
    )
    clean_scope = str(scope or "").strip().lower()
    if clean_scope in LOCAL_TRANSLATION_SCOPE_DEFAULTS:
        if (
            _local_translation_route(profile, clean_scope) == "local"
            and local_translation_available()
        ):
            preferred_backend = LOCAL_TRANSLATION_BACKEND
    elif not preferred_backend and local_translation_available():
        preferred_backend = LOCAL_TRANSLATION_BACKEND
    return run_ai_action(
        "research.paper_translate",
        body,
        profile=profile,
        context_refs=context_refs or [source_id],
        preferred_backend=preferred_backend or None,
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
    body, preferred_backend = _with_action_ai_preferences(
        profile,
        "research.paper_explain_selection",
        body,
    )
    return run_ai_action(
        "research.paper_explain_selection",
        body,
        profile=profile,
        context_refs=context_refs or [source_id],
        preferred_backend=preferred_backend,
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

    body, preferred_backend = _with_action_ai_preferences(
        profile,
        "research.paper_source_guide",
        {
            "source_id": source_id,
            "source": source or {},
            "segments": segments or [],
            "chunks": chunks or [],
            "annotations": annotations or [],
        },
    )
    return run_ai_action(
        "research.paper_source_guide",
        body,
        profile=profile,
        context_refs=context_refs or [source_id],
        preferred_backend=preferred_backend,
        require_review=require_review,
    )


def generate_paper_review_card(
    profile: str,
    source_id: str,
    *,
    source: dict[str, Any] | None = None,
    paper_markdown: str = "",
    segments: list[dict[str, Any]] | None = None,
    chunks: list[dict[str, Any]] | None = None,
    annotations: list[dict[str, Any]] | None = None,
    paper_context: dict[str, Any] | None = None,
    model: str | None = None,
    context_refs: list[str] | None = None,
    require_review: bool = True,
) -> AIActionResult:
    """Typed helper for ``research.paper_review_card``.

    Reader callers pass the full paper as ``paper_markdown``; ``segments``
    stays for callers that only have a few passages.
    """

    body_in: dict[str, Any] = {
        "source_id": source_id,
        "source": source or {},
        "chunks": chunks or [],
        "annotations": annotations or [],
        "model_timeout_seconds": _paper_analysis_model_timeout_seconds(),
        # A timed-out whole-paper call should not silently run twice more.
        "llm_max_retries": 1,
        "llm_max_tokens": llm.analysis_max_tokens_default(),
    }
    if paper_markdown:
        body_in["paper_markdown"] = paper_markdown
    else:
        body_in["segments"] = segments or []
    if paper_context:
        body_in["paper_context"] = paper_context
    body, preferred_backend = _with_action_ai_preferences(
        profile,
        "research.paper_review_card",
        body_in,
        model=model,
    )
    return run_ai_action(
        "research.paper_review_card",
        body,
        profile=profile,
        context_refs=context_refs or [source_id],
        preferred_backend=preferred_backend,
        require_review=require_review,
    )


def answer_paper_question(
    profile: str,
    source_id: str,
    question: str,
    *,
    history: list[dict[str, Any]] | None = None,
    context_refs: list[str] | None = None,
    payload: dict[str, Any] | None = None,
    require_review: bool = True,
) -> AIActionResult:
    """Typed helper for ``research.paper_qa``."""

    body = dict(payload or {})
    body.update({"source_id": source_id, "question": question})
    if history:
        body["history"] = history
    body, preferred_backend = _with_action_ai_preferences(
        profile,
        "research.paper_qa",
        body,
    )
    return run_ai_action(
        "research.paper_qa",
        body,
        profile=profile,
        context_refs=context_refs or [source_id],
        preferred_backend=preferred_backend,
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

    body, preferred_backend = _with_action_ai_preferences(
        profile,
        "research.paper_claim_extract",
        {"source_id": source_id, "segments": segments or [], "chunks": chunks or []},
    )
    return run_ai_action(
        "research.paper_claim_extract",
        body,
        profile=profile,
        context_refs=context_refs or [source_id],
        preferred_backend=preferred_backend,
        require_review=require_review,
    )


def deep_read_paper_codex(
    profile: str,
    source_id: str,
    *,
    model: str | None = None,
    context_refs: list[str] | None = None,
    payload: dict[str, Any] | None = None,
    require_review: bool = True,
    cancel_callback: Callable[[], bool] | None = None,
) -> AIActionResult:
    """Typed helper for ``research.paper_deep_read_codex``."""

    body = dict(payload or {})
    body["source_id"] = source_id
    body, preferred_backend = _with_action_ai_preferences(
        profile,
        "research.paper_deep_read_codex",
        body,
        model=model,
    )
    return run_ai_action(
        "research.paper_deep_read_codex",
        body,
        profile=profile,
        context_refs=context_refs or [source_id],
        preferred_backend=preferred_backend,
        require_review=require_review,
        cancel_callback=cancel_callback,
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
    body, preferred_backend = _with_action_ai_preferences(
        profile,
        "research.paper_compare_codex",
        body,
    )
    return run_ai_action(
        "research.paper_compare_codex",
        body,
        profile=profile,
        context_refs=context_refs or source_ids,
        preferred_backend=preferred_backend,
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

    body, preferred_backend = _with_action_ai_preferences(
        profile,
        "kanban.task_alignment",
        {
            "task_id": task_id,
            "task_title": task_title,
            "task_text": task_text,
            "ai_context": ai_context,
            "reply_language": _reply_language_value(reply_language),
        },
    )
    return run_ai_action(
        "kanban.task_alignment",
        body,
        profile=profile if require_review else "",
        context_refs=context_refs or [],
        preferred_backend=preferred_backend,
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

    body, preferred_backend = _with_action_ai_preferences(
        profile,
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
    )
    return run_ai_action(
        "kanban.subtasks",
        body,
        profile=profile if require_review else "",
        context_refs=context_refs or [],
        preferred_backend=preferred_backend,
        require_review=require_review,
    )


def crystallize_done_tasks(
    profile: str,
    done_tasks: list[Any],
    *,
    goal_context: str = "",
    timeout_seconds: float = 90.0,
    context_refs: list[str] | None = None,
) -> AIActionResult:
    """Generate a reviewable evidence patch from selected Done tasks."""

    body, preferred_backend = _with_action_ai_preferences(
        profile,
        "evidence.crystallize",
        {
            "done_tasks": done_tasks,
            "goal_context": goal_context,
            "timeout_seconds": timeout_seconds,
        },
    )
    return run_ai_action(
        "evidence.crystallize",
        body,
        profile=profile,
        context_refs=context_refs or [],
        preferred_backend=preferred_backend,
        require_review=False,
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


def _with_action_ai_preferences(
    profile: str,
    action_name: str,
    payload: dict[str, Any] | None = None,
    *,
    model: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Apply profile-scoped backend/model preferences to one action payload."""

    body = dict(payload or {})
    config = _action_ai_config(profile, action_name)
    user_backend = config.get("backend") or _default_user_backend(action_name)
    preferred_backend = _gateway_backend(config.get("backend"))
    model_override = _clean_model(model) or str(config.get("model") or "").strip()
    if model_override:
        if user_backend == "codex":
            body["codex_model"] = model_override
        else:
            body["ai_model"] = model_override
    # Settings effort beats the per-action default (backends) but not an
    # effort the caller put in the payload explicitly.
    effort = str(config.get("codex_effort") or "").strip()
    if (
        effort
        and user_backend == "codex"
        and not body.get("codex_reasoning_effort")
        and not body.get("reasoning_effort")
    ):
        body["codex_reasoning_effort"] = effort
    return body, preferred_backend


def _local_translation_route(profile: str, scope: str) -> str:
    """Return ``local`` or ``ai`` for one translation scope of a profile."""

    default = LOCAL_TRANSLATION_SCOPE_DEFAULTS.get(scope, "ai")
    clean_profile = str(profile or "").strip()
    if not clean_profile:
        return default
    try:
        prefs = load_web_preferences(clean_profile)
    except Exception:
        return default
    ai = prefs.get("ai") if isinstance(prefs.get("ai"), dict) else {}
    routes = ai.get("local_translation") if isinstance(ai.get("local_translation"), dict) else {}
    value = str(routes.get(scope) or "").strip()
    return value if value in {"local", "ai"} else default


def _action_ai_config(profile: str, action_name: str) -> dict[str, str]:
    """Return the effective user-facing backend/model preference for an action."""

    clean_profile = str(profile or "").strip()
    if not clean_profile:
        return {"backend": "", "model": ""}
    try:
        prefs = load_web_preferences(clean_profile)
    except Exception:
        return {"backend": "", "model": ""}
    ai = prefs.get("ai") if isinstance(prefs.get("ai"), dict) else {}
    actions = ai.get("actions") if isinstance(ai.get("actions"), dict) else {}
    action = actions.get(action_name) if isinstance(actions.get(action_name), dict) else {}
    backend = _user_backend_value(action.get("backend"))
    if not action:
        backend = _legacy_action_backend(ai, action_name)
    effective_backend = backend or _default_user_backend(action_name)
    model_key = "codex_model" if effective_backend == "codex" else "llm_model"
    model = _clean_model(action.get(model_key))
    if not model and not action:
        model = _legacy_action_model(ai, action_name, effective_backend)
    return {"backend": backend, "model": model, "codex_effort": codex_effort_value(action.get("codex_effort"))}


def _legacy_action_backend(ai: dict[str, Any], action_name: str) -> str:
    """Read old pre-matrix backend fields when tests or profiles supply them."""

    if action_name == "research.paper_translate":
        paper = ai.get("paper") if isinstance(ai.get("paper"), dict) else {}
        return _user_backend_value(paper.get("translation_backend"))
    if action_name in {"kanban.task_alignment", "kanban.subtasks"}:
        return _user_backend_value(ai.get("kanban_backend"))
    return ""


def _legacy_action_model(
    ai: dict[str, Any],
    action_name: str,
    effective_backend: str,
) -> str:
    """Read old pre-matrix model fields when tests or profiles supply them."""

    paper = ai.get("paper") if isinstance(ai.get("paper"), dict) else {}
    if action_name == "research.paper_translate":
        return _clean_model(paper.get("translation_model"))
    if (
        effective_backend == "codex"
        and action_name
        in {
            "research.paper_search_codex",
            "research.paper_deep_read_codex",
            "research.paper_compare_codex",
        }
    ):
        return _clean_model(paper.get("deep_read_model"))
    return ""


def _default_user_backend(action_name: str) -> str:
    """Return the user-facing default backend for an action."""

    value = AI_ACTION_DEFAULT_BACKENDS.get(action_name, "llm")
    return value if value in {"llm", "codex"} else "llm"


def _gateway_backend(user_backend: object) -> str:
    """Map a user-facing backend value to an AI Gateway backend name."""

    backend = _user_backend_value(user_backend)
    if backend == "codex":
        return "local_codex_readonly"
    if backend == "llm":
        return "direct_llm"
    return ""


def _user_backend_value(value: object) -> str:
    clean = str(value or "").strip()
    return clean if clean in {"llm", "codex"} else ""


def _normalize_context(
    context: Mapping[str, Any] | str | None,
) -> dict[str, Any]:
    if isinstance(context, str):
        return {"profile": context}
    if isinstance(context, Mapping):
        return dict(context)
    return {}


def _clean_model(value: str | None) -> str:
    return str(value or "").strip()


def _positive_float(value: object) -> float | None:
    try:
        clean = float(value)
    except (TypeError, ValueError):
        return None
    return clean if clean > 0 else None


def _paper_translation_model_timeout_seconds() -> float:
    configured = _positive_float(os.getenv("NBLANE_PAPER_TRANSLATION_MODEL_TIMEOUT_SECONDS"))
    if configured is not None:
        return configured
    return PAPER_TRANSLATION_MODEL_TIMEOUT_SECONDS_DEFAULT


def _paper_analysis_model_timeout_seconds() -> float:
    configured = _positive_float(os.getenv("NBLANE_PAPER_ANALYSIS_MODEL_TIMEOUT_SECONDS"))
    if configured is not None:
        return configured
    return PAPER_ANALYSIS_MODEL_TIMEOUT_SECONDS_DEFAULT


def _paper_ai_model(profile: str, key: str) -> str:
    """Return a profile-scoped paper AI model preference, when configured."""

    clean_profile = str(profile or "").strip()
    if not clean_profile:
        return ""
    try:
        prefs = load_web_preferences(clean_profile)
    except Exception:
        return ""
    ai = prefs.get("ai") if isinstance(prefs.get("ai"), dict) else {}
    paper = ai.get("paper") if isinstance(ai.get("paper"), dict) else {}
    return str(paper.get(key) or "").strip()


def _paper_ai_backend(profile: str, key: str) -> str:
    """Return the AI Action backend name for a profile-scoped paper preference."""

    clean_profile = str(profile or "").strip()
    if not clean_profile:
        return ""
    try:
        prefs = load_web_preferences(clean_profile)
    except Exception:
        return ""
    ai = prefs.get("ai") if isinstance(prefs.get("ai"), dict) else {}
    paper = ai.get("paper") if isinstance(ai.get("paper"), dict) else {}
    backend = str(paper.get(key) or "").strip()
    if backend == "codex":
        return "local_codex_readonly"
    if backend == "llm":
        return "direct_llm"
    return ""


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
    "ingest_kanban_done",
    "ingest_resume_text",
    "recommend_research_sources",
    "route_task_to_skill_nodes",
    "run_ai_action",
    "run_json",
    "run_text",
    "run_skill_coach",
    "run_visual_caption",
    "search_papers_codex",
    "translate_paper_segments",
]


def run_skill_coach(
    profile: str,
    task: str,
    *,
    nodes: list[dict[str, Any]] | None = None,
    history: list[dict[str, Any]] | None = None,
    context_refs: list[str] | None = None,
) -> AIActionResult:
    """Typed helper for ``gap.skill_coach`` (text-mode coach reply)."""

    return run_ai_action(
        "gap.skill_coach",
        {
            "task": task,
            "nodes": nodes or [],
            "history": history or [],
        },
        profile=profile,
        context_refs=context_refs or [],
    )


def route_task_to_skill_nodes(
    profile: str,
    task: str,
    *,
    schema_nodes: list[dict[str, Any]] | None = None,
    context_refs: list[str] | None = None,
) -> AIActionResult:
    """Typed helper for ``gap.task_routing``."""

    return run_ai_action(
        "gap.task_routing",
        {"task": task, "schema_nodes": schema_nodes or []},
        profile=profile,
        context_refs=context_refs or [],
    )


def ingest_resume_text(
    profile: str,
    resume_text: str,
    *,
    allow_status_change: bool = False,
    context_refs: list[str] | None = None,
) -> AIActionResult:
    """Typed helper for ``profile.resume_ingest``."""

    return run_ai_action(
        "profile.resume_ingest",
        {
            "resume_text": resume_text,
            "allow_status_change": allow_status_change,
        },
        profile=profile,
        context_refs=context_refs or [],
    )


def ingest_kanban_done(
    profile: str,
    done_tasks: list[dict[str, Any]],
    *,
    allow_status_change: bool = False,
    context_refs: list[str] | None = None,
) -> AIActionResult:
    """Typed helper for ``profile.kanban_ingest``."""

    return run_ai_action(
        "profile.kanban_ingest",
        {
            "done_tasks": done_tasks,
            "allow_status_change": allow_status_change,
        },
        profile=profile,
        context_refs=context_refs or [],
    )


def run_visual_caption(
    profile: str,
    intent: str,
    *,
    image_ref: str = "",
    context_refs: list[str] | None = None,
) -> AIActionResult:
    """Typed helper for ``output.visual_caption``."""

    return run_ai_action(
        "output.visual_caption",
        {"intent": intent, "image_ref": image_ref},
        profile=profile,
        context_refs=context_refs or [],
    )
