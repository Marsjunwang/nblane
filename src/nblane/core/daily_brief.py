"""Daily Brief for the Home dashboard.

Two layers:

- :func:`build_daily_brief` — a heuristic, structured brief derived purely
  from an assembled dashboard payload (no extra file I/O, no prose strings;
  renderers resolve copy through i18n keys).
- :func:`ai_daily_brief_summary` — an optional AI-enhanced one-paragraph
  brief grounded on the heuristic snapshot, routed through the AI gateway
  and cached by payload revision + date + backend/model. Any failure,
  missing configuration, or ``NBLANE_DISABLE_NETWORK_LOOKUPS`` falls back
  silently to the heuristic-only brief.
"""

from __future__ import annotations

import os
from collections import OrderedDict
from collections.abc import Callable
from datetime import date
from typing import Any

KANBAN_PAGE = "pages/3_Kanban.py"
EVIDENCE_REVIEW_PAGE = "pages/2_Evidence_Review.py"
AGENT_ACTIVITY_PAGE = "pages/9_Agent_Activity.py"
PROFILE_HEALTH_PAGE = "pages/5_Profile_Health.py"
RESEARCH_PAGE = "pages/7_Research.py"

AI_DAILY_BRIEF_ACTION = "dashboard.daily_brief"

# Days a Doing task can sit without movement before the brief flags it.
DOING_STALL_DAYS = 14

_MAX_STALLED_ROWS = 3
_MAX_AI_SUMMARY_CHARS = 600


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _as_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _parse_iso_date(value: object) -> "date | None":
    text = _clean_text(value)
    if len(text) < 10:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _goal_focus(primary_goal: dict) -> dict[str, object]:
    """Privacy-safe goal focus: labels only when the projection exposes them."""
    goal = _as_dict(primary_goal)
    projection = _as_dict(goal.get("projection"))
    locked = bool(goal.get("locked")) or (
        bool(goal.get("is_set")) and not projection
    )
    label = ""
    if projection:
        label = _clean_text(projection.get("title")) or _clean_text(
            projection.get("label")
        )
    return {
        "goal_id": _clean_text(projection.get("id")),
        "goal_label": label,
        "goal_set": bool(goal.get("is_set")),
        "goal_locked": locked,
    }


def _stalled_doing(kanban: dict, *, today: date) -> list[dict[str, object]]:
    """Doing tasks whose ``started_on`` is older than the stall threshold."""
    stalled: list[dict[str, object]] = []
    items = kanban.get("doing_items")
    if not isinstance(items, list):
        items = kanban.get("doing") if isinstance(kanban.get("doing"), list) else []
    for item in items:
        row = _as_dict(item)
        started = _parse_iso_date(row.get("started_on"))
        if started is None:
            continue
        days = (today - started).days
        if days < DOING_STALL_DAYS:
            continue
        stalled.append(
            {
                "id": _clean_text(row.get("id")),
                "title": _clean_text(row.get("title")),
                "days": days,
            }
        )
    stalled.sort(key=lambda row: -_as_int(row.get("days")))
    return stalled


def build_daily_brief(payload: dict, *, today: "date | None" = None) -> dict:
    """Return the structured heuristic brief for an assembled payload.

    Every field is data (ids, counts, privacy-safe labels, page paths) — the
    React banner and the native fallback both resolve actual copy via i18n.
    """
    day = today or date.today()
    source = _as_dict(payload)
    kanban = _as_dict(source.get("kanban"))
    pending = _as_dict(source.get("pending_evidence"))
    agent = _as_dict(source.get("agent_activity"))
    health = _as_dict(source.get("health"))
    sources = _as_dict(source.get("sources"))

    doing_items = kanban.get("doing_items")
    if not isinstance(doing_items, list):
        doing_items = kanban.get("doing") if isinstance(kanban.get("doing"), list) else []
    top_task = _as_dict(doing_items[0]) if doing_items else {}
    stalled = _stalled_doing(kanban, today=day)

    evidence_pending = (
        _as_int(pending.get("done_uncrystallized_count"))
        + _as_int(pending.get("unlinked_count"))
        + _as_int(pending.get("needs_review_count"))
        + _as_int(pending.get("status_risk_count"))
    )
    agent_pending = _as_int(agent.get("pending_total"))
    health_counts = _as_dict(health.get("counts"))

    focus = {
        **_goal_focus(source.get("primary_goal") or source.get("goal")),
        "task_title": _clean_text(top_task.get("title")),
        "task_blocked_by": _clean_text(top_task.get("blocked_by")),
        "doing_total": _as_int(kanban.get("doing_total")) or len(doing_items),
        "path": KANBAN_PAGE,
    }
    decisions = {
        "evidence_pending": evidence_pending,
        "agent_pending": agent_pending,
        "total": evidence_pending + agent_pending,
        "evidence_path": EVIDENCE_REVIEW_PAGE,
        "agent_path": AGENT_ACTIVITY_PAGE,
    }
    risks = {
        "health_errors": _as_int(health_counts.get("error")),
        "health_warnings": _as_int(health_counts.get("warning")),
        "stalled_doing": stalled[:_MAX_STALLED_ROWS],
        "stalled_doing_count": len(stalled),
        "health_path": PROFILE_HEALTH_PAGE,
        "kanban_path": KANBAN_PAGE,
    }
    research = {
        "inbox": _as_int(sources.get("source_inbox_total"))
        or _as_int(sources.get("inbox_total")),
        "active": _as_int(sources.get("active_total")),
        "path": RESEARCH_PAGE,
    }
    return {
        "date": day.isoformat(),
        "focus": focus,
        "decisions": decisions,
        "risks": risks,
        "research": research,
    }


# --- AI-enhanced brief (gateway, cached, silent heuristic fallback) ---------

_DAILY_BRIEF_AI_CACHE: "OrderedDict[tuple, dict[str, str]]" = OrderedDict()
_DAILY_BRIEF_AI_CACHE_LIMIT = 16

BriefRunner = Callable[[str, dict, str, str], dict[str, str]]


def daily_brief_ai_cache_key(
    profile: str,
    revision: str,
    backend: str,
    model: str,
    lang: str,
    *,
    today: "date | None" = None,
) -> tuple:
    """Cache key for the AI brief: payload revision + date + routing + language."""
    day = (today or date.today()).isoformat()
    return (
        _clean_text(profile),
        _clean_text(revision),
        day,
        _clean_text(backend),
        _clean_text(model),
        _clean_text(lang),
    )


def clear_daily_brief_ai_cache() -> None:
    """Drop all cached AI briefs (tests and preference changes)."""
    _DAILY_BRIEF_AI_CACHE.clear()


def _ai_grounding(brief: dict, *, lang: str) -> dict[str, Any]:
    """Compact JSON-safe grounding: the heuristic snapshot, nothing else."""
    source = _as_dict(brief)
    return {
        "date": _clean_text(source.get("date")),
        "reply_language": _clean_text(lang),
        "focus": _as_dict(source.get("focus")),
        "decisions": _as_dict(source.get("decisions")),
        "risks": _as_dict(source.get("risks")),
        "research": _as_dict(source.get("research")),
    }


def _default_brief_runner(
    profile: str,
    grounding: dict,
    backend: str,
    model: str,
) -> dict[str, str]:
    """Run the brief through the AI gateway; empty summary on any failure.

    This is the single network-touching path — it refuses to run when tests
    or offline deployments set ``NBLANE_DISABLE_NETWORK_LOOKUPS``.
    """
    if os.environ.get("NBLANE_DISABLE_NETWORK_LOOKUPS"):
        return {"summary": "", "backend": ""}
    from nblane.core import llm as llm_client
    from nblane.core.ai import run_json

    if backend != "codex" and not llm_client.is_configured():
        return {"summary": "", "backend": ""}
    payload = dict(grounding)
    payload["ai_model"] = model
    payload["llm_model"] = model
    payload["codex_model"] = model
    preferred = "local_codex_readonly" if backend == "codex" else None
    try:
        result = run_json(
            AI_DAILY_BRIEF_ACTION,
            payload,
            profile=profile,
            preferred_backend=preferred,
            require_review=False,
        )
    except Exception:
        return {"summary": "", "backend": ""}
    if not getattr(result, "ok", False):
        return {"summary": "", "backend": ""}
    structured = result.structured if isinstance(result.structured, dict) else {}
    summary = _clean_text(structured.get("brief"))[:_MAX_AI_SUMMARY_CHARS]
    if not summary:
        return {"summary": "", "backend": ""}
    return {"summary": summary, "backend": backend}


def ai_daily_brief_summary(
    profile: str,
    brief: dict,
    *,
    backend: str,
    model: str,
    revision: str = "",
    lang: str = "",
    runner: BriefRunner | None = None,
) -> dict[str, str]:
    """Return ``{"summary": str, "backend": str}`` for the AI brief.

    Cached per (profile, payload revision, date, backend, model, language);
    failures are cached too so a broken provider is not re-called on every
    Streamlit rerun. An empty ``summary`` means "use the heuristic brief".
    """
    key = daily_brief_ai_cache_key(
        profile,
        revision,
        backend,
        model,
        lang,
    )
    hit = _DAILY_BRIEF_AI_CACHE.get(key)
    if hit is not None:
        _DAILY_BRIEF_AI_CACHE.move_to_end(key)
        return dict(hit)
    run = runner if runner is not None else _default_brief_runner
    try:
        value = run(profile, _ai_grounding(brief, lang=lang), backend, model)
    except Exception:
        value = {"summary": "", "backend": ""}
    if not isinstance(value, dict):
        value = {"summary": "", "backend": ""}
    value = {
        "summary": _clean_text(value.get("summary"))[:_MAX_AI_SUMMARY_CHARS],
        "backend": _clean_text(value.get("backend")),
    }
    _DAILY_BRIEF_AI_CACHE[key] = value
    if len(_DAILY_BRIEF_AI_CACHE) > _DAILY_BRIEF_AI_CACHE_LIMIT:
        _DAILY_BRIEF_AI_CACHE.popitem(last=False)
    return dict(value)


__all__ = [
    "AGENT_ACTIVITY_PAGE",
    "AI_DAILY_BRIEF_ACTION",
    "DOING_STALL_DAYS",
    "EVIDENCE_REVIEW_PAGE",
    "KANBAN_PAGE",
    "PROFILE_HEALTH_PAGE",
    "RESEARCH_PAGE",
    "ai_daily_brief_summary",
    "build_daily_brief",
    "clear_daily_brief_ai_cache",
    "daily_brief_ai_cache_key",
]
