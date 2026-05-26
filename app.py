"""nblane · Web UI entry point.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
import os
from pathlib import Path
import re
import time
from urllib.parse import quote
import urllib.request

import yaml
import streamlit as st

from nblane.core import git_backup
from nblane.core import codex_adapter
from nblane.core.home_dashboard import (
    dashboard_payload as _dashboard_payload,
    dashboard_health_summary as _dashboard_health_summary,
    dashboard_kanban_summary as _dashboard_kanban_summary,
    dashboard_pending_evidence_summary as _dashboard_pending_evidence_summary,
    dashboard_public_summary as _dashboard_public_summary,
    dashboard_skill_summary as _dashboard_skill_summary,
)
from nblane.core.evidence_review import EVIDENCE_REVIEW_PAGE
from nblane.core import llm as llm_client
from nblane.core.web_preferences import (
    AI_ACTION_DEFAULT_BACKENDS,
    load_web_preferences,
    update_web_preferences,
)
from nblane.core.goals import (
    GOAL_STATUSES,
    GOAL_UI_VISIBILITIES,
    Goal,
    GoalBook,
    GoalSkillLink,
    goal_for_ui,
    save_goal_book,
)
from nblane.core.goal_alignment import (
    ai_match_goal_to_skills,
    manual_goal_skill_link,
    merge_goal_skill_candidates,
    rule_match_goal_to_skills,
)
from nblane.core.io import (
    profile_dir,
)
from nblane.core.profile_ingest import (
    ingest_preview_delta,
    merge_ingest_patch,
    run_ingest_patch,
    schema_node_labels,
)
from nblane.core.profile_ingest_llm import ingest_resume_json
from nblane.core.research_sources import (
    add_research_source,
    save_research_sources,
)
from nblane.core.profile_context import (
    GENERATED_BLOCKS,
    IDENTITY_FIELDS,
    LONG_NARRATIVE_SECTIONS,
    NORTH_STAR_VISIBILITIES,
    apply_profile_context_structured_edits,
    extract_generated_blocks,
    normalize_north_star_visibility,
    north_star_context_from_identity,
    parse_identity_fields,
    parse_skill_md_sections,
    rejoin_sections,
    section_body,
)
from nblane.web_cache import (
    clear_web_cache,
    load_evidence_pool_raw,
    load_goal_book_raw,
    load_research_sources,
    load_skill_md,
    load_skill_tree_raw,
)
from nblane.home_dashboard_component import st_home_dashboard
from nblane.web_i18n import home_ui
from nblane.web_shared import (
    apply_ui_language_from_session,
    assert_files_current,
    drop_streamlit_widget_keys,
    ensure_file_snapshot,
    remember_allow_and_drop_yaml_preview_keys,
    refresh_file_snapshots,
    render_git_backup_notices,
    render_llm_unavailable,
    render_page_help,
    select_profile,
    stash_git_backup_results,
)
from nblane.web_auth import require_login

ui: dict[str, str] = {}

_DASHBOARD_AI_ACTIONS: tuple[tuple[str, str, str], ...] = (
    (
        "dashboard.goal_skill_match",
        "dashboard_ai_action_goal_skill_match",
        "dashboard_ai_action_goal_skill_match_help",
    ),
    (
        "dashboard.graph_insights",
        "dashboard_ai_action_graph_insights",
        "dashboard_ai_action_graph_insights_help",
    ),
)
_DASHBOARD_MODEL_DEFAULT = "__default__"
_DASHBOARD_MODEL_CUSTOM = "__custom__"
_DASHBOARD_BACKEND_DEFAULT = "__default__"
_DASHBOARD_LLM_MODEL_SUGGESTIONS = (
    "qwen3.6-plus",
    "qwen-plus",
    "qwen-max",
    "deepseek-chat",
    "deepseek-reasoner",
    "gpt-4o",
    "gpt-4o-mini",
)
_DASHBOARD_CODEX_MODEL_SUGGESTIONS = (
    "gpt-5.5",
    "gpt-5.1-codex",
    "gpt-5-codex",
)


def _sync_home_ui() -> None:
    """Refresh Home copy from the current session UI language."""
    global ui
    apply_ui_language_from_session()
    ui = home_ui()


_sync_home_ui()

st.set_page_config(
    page_title=ui["app_page_title"],
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

selected = ""
_skill_md_path = Path()
_tree_path = Path()
_pool_path = Path()
_goals_path = Path()
_research_sources_path = Path()


def _prepare_home_state() -> None:
    """Initialize auth, profile selection, and Home file snapshots."""
    global selected
    global _skill_md_path, _tree_path, _pool_path, _goals_path
    global _research_sources_path

    require_login()
    selected = select_profile()
    _sync_home_ui()
    render_git_backup_notices()

    _skill_md_path = profile_dir(selected) / "SKILL.md"
    _tree_path = profile_dir(selected) / "skill-tree.yaml"
    _pool_path = profile_dir(selected) / "evidence-pool.yaml"
    _goals_path = profile_dir(selected) / "goals.yaml"
    _research_sources_path = profile_dir(selected) / "research" / "sources.yaml"
    for path in (
        _skill_md_path,
        _tree_path,
        _pool_path,
        _goals_path,
        _research_sources_path,
    ):
        ensure_file_snapshot(path)


def _goal_lines_text(items: list[str]) -> str:
    """Render list fields as one item per line."""
    return "\n".join(items or [])


def _goal_text_lines(value: str) -> list[str]:
    """Parse one-item-per-line goal fields."""
    return [
        line.strip()
        for line in value.splitlines()
        if line.strip()
    ]


def _dashboard_goal_lines(value: object) -> list[str]:
    """Parse dashboard event values as clean goal line lists."""
    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]
    return _goal_text_lines(str(value or ""))


def _goal_status_label(status: str) -> str:
    return ui.get(f"goal_status_{status}", status)


def _goal_visibility_label(visibility: str) -> str:
    return ui.get(f"goal_visibility_{visibility}", visibility)


def _goal_book_for_home(profile: str) -> GoalBook:
    """Load the current goal book through the Streamlit cache."""
    return GoalBook.from_dict(
        load_goal_book_raw(profile),
        profile=profile,
    )


def _goal_skill_candidate_state_key(profile: str) -> str:
    """Session-state key for unconfirmed goal-skill candidates."""
    return f"_home_goal_skill_candidates_{profile}"


def _goal_skill_candidates_for_home(
    profile: str,
) -> dict[str, list[dict[str, object]]]:
    """Return pending alignment candidates for the dashboard payload."""
    raw = st.session_state.get(_goal_skill_candidate_state_key(profile), {})
    return raw if isinstance(raw, dict) else {}


def _set_goal_skill_candidates(
    profile: str,
    goal_id: str,
    candidates: list[GoalSkillLink],
) -> None:
    """Store unconfirmed candidates in session state."""
    key = _goal_skill_candidate_state_key(profile)
    raw = st.session_state.get(key, {})
    state = raw if isinstance(raw, dict) else {}
    state[goal_id] = [candidate.to_dict() for candidate in candidates]
    st.session_state[key] = state


def _save_goal_book_for_home(
    profile: str,
    book: GoalBook,
    success_message: str,
) -> None:
    """Persist goals.yaml and refresh Home caches/snapshots."""
    assert_files_current([_goals_path])
    book.profile = profile
    save_goal_book(profile, book)
    refresh_file_snapshots([_goals_path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(success_message)
    st.rerun()


def _home_capture_text(payload: dict, *keys: str) -> str:
    """Return the first non-empty text value from a dashboard payload."""
    for key in keys:
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return ""


def _capture_kind(raw_kind: str) -> str:
    """Map dashboard capture types to research source kinds."""
    return {
        "note": "note",
        "link": "web",
        "resource": "other",
        "idea": "note",
    }.get(raw_kind, "other")


def _capture_home_research_source(profile: str, payload: dict) -> None:
    """Capture one Home dashboard source into Research Source Inbox."""
    title = _home_capture_text(payload, "title")
    if not title:
        st.warning(ui["dashboard_capture_title_required"])
        return

    source_url = _home_capture_text(payload, "source_url", "sourceUrl", "url")
    source = _home_capture_text(payload, "source") or source_url
    goal_id = _home_capture_text(payload, "goal_id", "goalId")
    metadata: dict[str, object] = {
        "source_surface": "home_capture",
        "graph_layer": "source",
        "capture_event": "capture_inbox_submit",
    }
    if source_url:
        metadata["source_url"] = source_url

    assert_files_current([_research_sources_path])
    inbox = load_research_sources(profile)
    item = add_research_source(
        inbox,
        title,
        kind=_capture_kind(_home_capture_text(payload, "type") or "note"),
        url=source_url or source,
        status="inbox",
        notes=_home_capture_text(payload, "raw_text", "rawText", "note"),
        visibility="private",
        origin="home_capture",
        tags=payload.get("tags"),
        goal_refs=[goal_id] if goal_id else [],
        metadata=metadata,
    )
    save_research_sources(profile, inbox)
    refresh_file_snapshots([_research_sources_path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(ui["dashboard_capture_saved"].format(id=item.id))
    st.rerun()


def _goal_form_key(profile: str, field: str, goal_id: str = "") -> str:
    """Stable widget key for the Home goal form scoped to one goal."""
    scope = str(goal_id or "__current__").strip() or "__current__"
    return f"home_goal_{profile}_{scope}_{field}"


def _goal_default_id() -> str:
    """Return a stable id shape for the first current goal."""
    return f"goal_{date.today().strftime('%Y%m%d')}_current"


def _goal_id_slug(value: str) -> str:
    """Return a short id-safe slug for a goal title."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return slug[:32] or "active"


def _unique_goal_id(book: GoalBook, title: str) -> str:
    """Return a non-conflicting active goal id."""
    base = f"goal_{date.today().strftime('%Y%m%d')}_{_goal_id_slug(title)}"
    existing = set(book.by_id())
    if base not in existing:
        return base
    idx = 2
    while f"{base}_{idx}" in existing:
        idx += 1
    return f"{base}_{idx}"


def dashboard_kanban_summary(profile: str) -> dict:
    """Dashboard read model for kanban.md."""
    return _dashboard_kanban_summary(profile)


def dashboard_skill_summary(profile: str) -> dict:
    """Dashboard read model for skill-tree.yaml and goals.yaml."""
    return _dashboard_skill_summary(profile)


def dashboard_pending_evidence_summary(profile: str) -> dict:
    """Dashboard read model for pending evidence review."""
    return _dashboard_pending_evidence_summary(profile)


def dashboard_health_summary(profile: str) -> dict:
    """Dashboard read model for profile health."""
    return _dashboard_health_summary(profile)


def dashboard_public_summary(profile: str) -> dict:
    """Dashboard read model for the public layer."""
    return _dashboard_public_summary(profile)


def dashboard_payload(profile: str) -> dict:
    """React Home dashboard payload."""
    ai_payload = {
        "configured": llm_client.is_configured(),
        "label": llm_client.model_label() if llm_client.is_configured() else "",
        "actions": _dashboard_ai_action_payload(profile),
    }
    payload = _dashboard_payload(
        profile,
        ui=ui,
        ai=ai_payload,
        skill_alignment_candidates=_goal_skill_candidates_for_home(profile),
    )
    canvas_base = _dashboard_canvas_base()
    canvas_ok, _canvas_message = _dashboard_canvas_status(canvas_base, profile)
    if canvas_base and canvas_ok is not False:
        encoded_profile = quote(profile, safe="")
        payload["canvas_embed"] = {
            "url": f"{canvas_base}/dashboard?profile={encoded_profile}&embed=1&view=focus",
            "standalone_url": f"{canvas_base}/dashboard?profile={encoded_profile}",
        }
    return payload


def _dashboard_canvas_base() -> str:
    """Return the 8502 Dashboard Canvas base URL used for embedded graph mode."""
    raw = (
        os.getenv("NBLANE_DASHBOARD_CANVAS_BASE", "").strip()
        or os.getenv("NBLANE_READER_API_BASE", "").strip()
        or "http://127.0.0.1:8502"
    )
    if raw.lower() in {"0", "false", "off", "none"}:
        return ""
    return raw.rstrip("/")


def _dashboard_canvas_url(canvas_base: str, profile: str, *, embed: bool = False) -> str:
    """Return the 8502 Dashboard Canvas URL for one profile."""
    encoded_profile = quote(profile, safe="")
    suffix = f"/dashboard?profile={encoded_profile}"
    if embed:
        suffix += "&embed=1&view=focus"
    return f"{canvas_base.rstrip('/')}{suffix}"


def _dashboard_canvas_status(
    canvas_base: str,
    profile: str,
) -> tuple[bool | None, str]:
    """Check whether the browser-facing 8502 Dashboard Canvas is reachable."""
    if not canvas_base:
        return None, ""
    canvas_url = _dashboard_canvas_url(canvas_base, profile, embed=True)
    try:
        timeout = max(0.1, float(os.getenv("NBLANE_DASHBOARD_CANVAS_HEALTH_TIMEOUT", "2.0")))
    except ValueError:
        timeout = 2.0
    cache_key = f"_dashboard_canvas_status:{canvas_url}"
    now = time.time()
    cached = st.session_state.get(cache_key)
    if isinstance(cached, dict) and now - float(cached.get("checked_at", 0)) < 15:
        return bool(cached.get("ok")), str(cached.get("message") or "")
    try:
        request = urllib.request.Request(
            canvas_url,
            method="GET",
            headers={"User-Agent": "nblane-dashboard-canvas-check/1.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            ok = 200 <= int(getattr(response, "status", 200)) < 400
            message = "" if ok else f"HTTP {getattr(response, 'status', '')}".strip()
    except Exception as exc:
        ok = False
        message = str(exc)
    st.session_state[cache_key] = {"checked_at": now, "ok": ok, "message": message}
    return ok, message


def _dashboard_ai_action_prefs(profile: str) -> dict[str, dict[str, str]]:
    """Return Dashboard action AI preferences for one profile."""
    prefs = load_web_preferences(profile)
    ai = prefs.get("ai") if isinstance(prefs.get("ai"), dict) else {}
    actions = ai.get("actions") if isinstance(ai.get("actions"), dict) else {}
    out: dict[str, dict[str, str]] = {}
    for action_name, _label_key, _help_key in _DASHBOARD_AI_ACTIONS:
        action = actions.get(action_name) if isinstance(actions.get(action_name), dict) else {}
        out[action_name] = {
            "backend": str(action.get("backend") or "").strip(),
            "llm_model": str(action.get("llm_model") or "").strip(),
            "codex_model": str(action.get("codex_model") or "").strip(),
        }
    return out


def _dashboard_default_backend(action_name: str) -> str:
    backend = AI_ACTION_DEFAULT_BACKENDS.get(action_name, "llm")
    return backend if backend in {"llm", "codex"} else "llm"


def _dashboard_backend_name(backend: str) -> str:
    return "Codex" if backend == "codex" else "LLM"


def _dashboard_effective_backend(action_name: str, config: dict[str, str]) -> str:
    configured = str(config.get("backend") or "").strip()
    return configured if configured in {"llm", "codex"} else _dashboard_default_backend(action_name)


def _dashboard_effective_model(
    action_name: str,
    config: dict[str, str],
    *,
    llm_default: str,
    codex_default: str,
) -> str:
    backend = _dashboard_effective_backend(action_name, config)
    if backend == "codex":
        return str(config.get("codex_model") or codex_default or "").strip()
    return str(config.get("llm_model") or llm_default or "").strip()


def _dashboard_effective_ai_config(profile: str, action_name: str) -> dict[str, str]:
    """Return effective backend/model for one Dashboard AI action."""
    prefs = _dashboard_ai_action_prefs(profile).get(action_name, {})
    llm_default = str(llm_client.current_config(mask_key=True).get("model") or "").strip()
    codex_default = str(codex_adapter.current_config(profile=profile).model or "").strip()
    backend = _dashboard_effective_backend(action_name, prefs)
    model = _dashboard_effective_model(
        action_name,
        prefs,
        llm_default=llm_default,
        codex_default=codex_default,
    )
    return {"backend": backend, "model": model}


def _dashboard_ai_action_payload(profile: str) -> dict[str, dict[str, str]]:
    """Return effective Dashboard AI config for React display/debugging."""
    return {
        action_name: {
            **_dashboard_ai_action_prefs(profile).get(action_name, {}),
            **{
                f"effective_{key}": value
                for key, value in _dashboard_effective_ai_config(profile, action_name).items()
            },
        }
        for action_name, _label_key, _help_key in _DASHBOARD_AI_ACTIONS
    }


def _dashboard_ai_backend_label(value: str) -> str:
    if value == "codex":
        return _dashboard_backend_name(value)
    if value == "llm":
        return _dashboard_backend_name(value)
    return ui["dashboard_ai_use_default"]


def _dashboard_model_picker(
    *,
    label: str,
    profile: str,
    pref_name: str,
    current: str,
    default_model: str,
    suggestions: tuple[str, ...],
) -> str:
    model_suggestions: list[str] = []
    for value in (default_model, *suggestions):
        clean = str(value or "").strip()
        if clean and clean not in model_suggestions:
            model_suggestions.append(clean)
    current = str(current or "").strip()
    options = [_DASHBOARD_MODEL_DEFAULT, *model_suggestions, _DASHBOARD_MODEL_CUSTOM]
    if current and current not in model_suggestions:
        initial = _DASHBOARD_MODEL_CUSTOM
    elif current:
        initial = current
    else:
        initial = _DASHBOARD_MODEL_DEFAULT
    choice = st.selectbox(
        label,
        options,
        index=options.index(initial),
        format_func=lambda value: (
            ui["dashboard_ai_use_default"]
            if value == _DASHBOARD_MODEL_DEFAULT
            else ui["dashboard_ai_custom_model"]
            if value == _DASHBOARD_MODEL_CUSTOM
            else value
        ),
        key=f"dashboard_ai:{profile}:{pref_name}:choice",
    )
    if choice == _DASHBOARD_MODEL_DEFAULT:
        return ""
    if choice == _DASHBOARD_MODEL_CUSTOM:
        return st.text_input(
            ui["dashboard_ai_custom_model"],
            value=current if current and current not in model_suggestions else "",
            key=f"dashboard_ai:{profile}:{pref_name}:custom",
        ).strip()
    return str(choice).strip()


def _dashboard_backend_picker(
    *,
    label: str,
    profile: str,
    pref_name: str,
    current: str,
    default_backend: str,
) -> str:
    options = [_DASHBOARD_BACKEND_DEFAULT, "llm", "codex"]
    current = str(current or "").strip()
    initial = current if current in {"llm", "codex"} else _DASHBOARD_BACKEND_DEFAULT
    choice = st.selectbox(
        label,
        options,
        index=options.index(initial),
        format_func=lambda value: (
            f"{ui['dashboard_ai_use_default']} ({_dashboard_backend_name(default_backend)})"
            if value == _DASHBOARD_BACKEND_DEFAULT
            else _dashboard_backend_name(value)
        ),
        key=f"dashboard_ai:{profile}:{pref_name}:choice",
    )
    return "" if choice == _DASHBOARD_BACKEND_DEFAULT else str(choice).strip()


def _dashboard_model_test_key(profile: str, backend: str, model: str, *, action_name: str) -> str:
    safe_profile = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(profile or "profile")).strip("_")
    safe_model = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(model or "default")).strip("_")
    safe_action = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(action_name or "global")).strip("_")
    return f"dashboard_ai:{safe_profile}:test:{safe_action or 'global'}:{backend}:{safe_model or 'default'}"


def _dashboard_record_model_test(
    profile: str,
    backend: str,
    model: str,
    ok: bool,
    latency: float,
    message: str,
    *,
    action_name: str,
) -> None:
    st.session_state[_dashboard_model_test_key(profile, backend, model, action_name=action_name)] = {
        "ok": bool(ok),
        "latency": float(latency),
        "message": str(message or "").strip()[:240],
    }


def _dashboard_model_test_summary(profile: str, backend: str, model: str, *, action_name: str) -> str:
    result = st.session_state.get(
        _dashboard_model_test_key(profile, backend, model, action_name=action_name)
    )
    if not isinstance(result, dict):
        return ""
    status = ui["dashboard_ai_available"] if result.get("ok") else ui["dashboard_ai_unavailable"]
    latency = float(result.get("latency") or 0.0)
    return f"{status}, {latency:.1f}s"


def _dashboard_effective_action_caption(
    profile: str,
    action_name: str,
    config: dict[str, str],
    *,
    llm_default: str,
    codex_default: str,
) -> str:
    backend = _dashboard_effective_backend(action_name, config)
    model = _dashboard_effective_model(
        action_name,
        config,
        llm_default=llm_default,
        codex_default=codex_default,
    )
    model_label = model or (
        ui["dashboard_ai_codex_default"] if backend == "codex" else ui["dashboard_ai_missing"]
    )
    bits = [
        ui["dashboard_ai_effective_backend"].format(backend=_dashboard_backend_name(backend)),
        ui["dashboard_ai_effective_model"].format(model=model_label),
    ]
    test = _dashboard_model_test_summary(profile, backend, model, action_name=action_name)
    if test:
        bits.append(test)
    return " · ".join(bits)


def _dashboard_run_llm_availability_test(
    profile: str,
    model: str,
    *,
    action_name: str,
) -> None:
    started = time.perf_counter()
    if not llm_client.is_configured():
        message = ui["dashboard_ai_llm_unconfigured"]
        _dashboard_record_model_test(
            profile,
            "llm",
            model,
            False,
            time.perf_counter() - started,
            message,
            action_name=action_name,
        )
        st.warning(message)
        return
    reply = llm_client.chat(
        "Return exactly OK. No prose.",
        "OK",
        temperature=0,
        model=str(model or "").strip() or None,
    )
    latency = time.perf_counter() - started
    if reply.startswith("LLM error:") or reply.startswith("AI features not configured"):
        _dashboard_record_model_test(profile, "llm", model, False, latency, reply, action_name=action_name)
        st.warning(reply)
    else:
        _dashboard_record_model_test(profile, "llm", model, True, latency, reply or "OK", action_name=action_name)
        st.success(ui["dashboard_ai_model_available"].format(seconds=f"{latency:.1f}"))


def _dashboard_run_codex_availability_test(
    profile: str,
    model: str,
    *,
    action_name: str,
) -> None:
    started = time.perf_counter()
    codex_config = codex_adapter.current_config(profile=profile)
    if str(model or "").strip():
        codex_config = replace(codex_config, model=str(model or "").strip())
    result = codex_adapter.run_readonly_codex_prompt(
        profile,
        "Return exactly OK. Do not edit files.",
        config=codex_config,
        timeout_seconds=min(float(codex_config.timeout_seconds or 30.0), 30.0),
    )
    latency = time.perf_counter() - started
    if result.ok:
        _dashboard_record_model_test(profile, "codex", model, True, latency, result.output or "OK", action_name=action_name)
        st.success(ui["dashboard_ai_model_available"].format(seconds=f"{latency:.1f}"))
    else:
        message = codex_adapter.readable_codex_error(
            result.error,
            result.stderr,
            result.output,
            result.stdout,
        )
        _dashboard_record_model_test(profile, "codex", model, False, latency, message, action_name=action_name)
        st.warning(message)


def _dashboard_run_action_availability_test(
    profile: str,
    action_name: str,
    config: dict[str, str],
    *,
    llm_default: str,
    codex_default: str,
) -> None:
    backend = _dashboard_effective_backend(action_name, config)
    model = _dashboard_effective_model(
        action_name,
        config,
        llm_default=llm_default,
        codex_default=codex_default,
    )
    if backend == "codex":
        _dashboard_run_codex_availability_test(profile, model, action_name=action_name)
    else:
        _dashboard_run_llm_availability_test(profile, model, action_name=action_name)


def _render_dashboard_action_config_row(
    profile: str,
    action_name: str,
    label: str,
    help_text: str,
    current: dict[str, str],
    *,
    llm_default: str,
    codex_default: str,
) -> dict[str, str]:
    default_backend = _dashboard_default_backend(action_name)
    st.markdown(f"**{label}**")
    st.caption(help_text)
    cols = st.columns([1.05, 1.25, 1.25, 0.85], gap="small")
    with cols[0]:
        backend = _dashboard_backend_picker(
            label=ui["dashboard_ai_backend"],
            profile=profile,
            pref_name=f"{action_name}:backend",
            current=current.get("backend", ""),
            default_backend=default_backend,
        )
    with cols[1]:
        llm_model = _dashboard_model_picker(
            label=ui["dashboard_ai_llm_model"],
            profile=profile,
            pref_name=f"{action_name}:llm_model",
            current=current.get("llm_model", ""),
            default_model=llm_default,
            suggestions=_DASHBOARD_LLM_MODEL_SUGGESTIONS,
        )
    with cols[2]:
        codex_model = _dashboard_model_picker(
            label=ui["dashboard_ai_codex_model"],
            profile=profile,
            pref_name=f"{action_name}:codex_model",
            current=current.get("codex_model", ""),
            default_model=codex_default,
            suggestions=_DASHBOARD_CODEX_MODEL_SUGGESTIONS,
        )
    with cols[3]:
        st.caption(ui["dashboard_ai_test"])
        test_clicked = st.form_submit_button(
            ui["dashboard_ai_test_model"],
            key=f"dashboard_ai:{profile}:{action_name}:test_model",
            width="stretch",
        )
    next_config = {
        "backend": backend,
        "llm_model": llm_model,
        "codex_model": codex_model,
    }
    st.caption(
        _dashboard_effective_action_caption(
            profile,
            action_name,
            next_config,
            llm_default=llm_default,
            codex_default=codex_default,
        )
    )
    if test_clicked:
        _dashboard_run_action_availability_test(
            profile,
            action_name,
            next_config,
            llm_default=llm_default,
            codex_default=codex_default,
        )
    return next_config


def _render_dashboard_ai_settings(profile: str) -> None:
    """Render profile-scoped Dashboard AI preferences."""
    prefs = _dashboard_ai_action_prefs(profile)
    llm_cfg = llm_client.current_config(mask_key=True)
    llm_default = str(llm_cfg.get("model") or "").strip()
    codex_cfg = codex_adapter.current_config(profile=profile)
    codex_default = str(codex_cfg.model or "").strip()
    codex_status = codex_adapter.codex_status(
        replace(
            codex_cfg,
            timeout_seconds=min(float(codex_cfg.timeout_seconds or 8.0), 8.0),
        )
    )
    next_actions: dict[str, dict[str, str]] = {}

    st.caption(ui["dashboard_ai_settings_caption"])
    runtime_cols = st.columns(2)
    with runtime_cols[0]:
        st.caption(
            ui["dashboard_ai_llm_status"].format(
                status=ui["dashboard_ai_configured"]
                if llm_cfg.get("configured")
                else ui["dashboard_ai_missing_key"],
                model=llm_default or ui["dashboard_ai_missing"],
            )
        )
    with runtime_cols[1]:
        codex_bits = [
            ui["dashboard_ai_installed"] if codex_status.installed else ui["dashboard_ai_missing"],
            ui["dashboard_ai_logged_in"] if codex_status.logged_in else ui["dashboard_ai_login_unknown"],
            codex_default or ui["dashboard_ai_codex_default"],
        ]
        st.caption(ui["dashboard_ai_codex_status"].format(status=" · ".join(codex_bits)))
        if codex_status.error:
            st.caption(codex_status.error)

    with st.form(f"dashboard_ai_settings_{profile}", border=False):
        for action_name, label_key, help_key in _DASHBOARD_AI_ACTIONS:
            current = prefs.get(action_name, {})
            next_actions[action_name] = _render_dashboard_action_config_row(
                profile,
                action_name,
                ui[label_key],
                ui[help_key],
                current,
                llm_default=llm_default,
                codex_default=codex_default,
            )

        if st.form_submit_button(ui["dashboard_ai_save"], type="primary", width="stretch"):
            update_web_preferences(profile, {"ai": {"actions": next_actions}})
            clear_web_cache()
            st.success(ui["dashboard_ai_saved"])
            st.rerun()


def _test_dashboard_ai_action(profile: str, action_name: str) -> None:
    """Run a tiny availability test for one Dashboard AI action."""
    config = _dashboard_effective_ai_config(profile, action_name)
    backend = config["backend"]
    model = config["model"]
    started = time.perf_counter()
    if backend == "codex":
        codex_config = codex_adapter.current_config(profile=profile)
        if model:
            codex_config = replace(codex_config, model=model)
        result = codex_adapter.run_readonly_codex_prompt(
            profile,
            "Return exactly OK. Do not edit files.",
            config=codex_config,
            timeout_seconds=min(float(codex_config.timeout_seconds or 30.0), 30.0),
        )
        latency = time.perf_counter() - started
        if result.ok:
            st.success(ui["dashboard_ai_test_ok"].format(seconds=f"{latency:.1f}"))
        else:
            st.warning(
                codex_adapter.readable_codex_error(
                    result.error,
                    result.stderr,
                    result.output,
                    result.stdout,
                )
            )
        return

    if not llm_client.is_configured():
        render_llm_unavailable(ui)
        return
    reply = llm_client.chat(
        "Return exactly OK. No prose.",
        "OK",
        temperature=0,
        model=model or None,
    )
    latency = time.perf_counter() - started
    if reply.startswith("LLM error:") or reply.startswith("AI features not configured"):
        st.warning(reply)
    else:
        st.success(ui["dashboard_ai_test_ok"].format(seconds=f"{latency:.1f}"))


def _render_goal_preview(goal: Goal) -> None:
    """Render the Home module's privacy-safe current goal preview."""
    payload = goal_for_ui(goal)
    st.caption(ui["goal_preview"])
    if payload is None:
        st.info(ui["goal_private_locked"])
        return
    visibility = str(payload.get("visibility") or "")
    if visibility == "hidden":
        st.markdown(f"**{ui['goal_strip_hidden']}**")
        return
    if visibility == "discreet":
        label = str(
            payload.get("label") or ui["goal_strip_default_label"]
        )
        status = _goal_status_label(str(payload.get("status") or ""))
        target = str(payload.get("target") or "")
        text = f"**{label}** · {ui['goal_strip_status']}: {status}"
        if target:
            text += f" · {ui['goal_strip_target']}: {target}"
        st.markdown(text)
        return
    title = str(payload.get("title") or payload.get("label") or "")
    status = _goal_status_label(str(payload.get("status") or ""))
    target = str(payload.get("target") or "")
    text = f"**{title or ui['goal_strip_default_label']}**"
    if status:
        text += f" · {ui['goal_strip_status']}: {status}"
    if target:
        text += f" · {ui['goal_strip_target']}: {target}"
    st.markdown(text)
    summary = str(payload.get("summary") or "")
    if summary:
        st.caption(summary)
    focus = payload.get("focus")
    if isinstance(focus, list) and focus:
        st.caption(
            f"{ui['goal_strip_focus']}: "
            + " · ".join(str(item) for item in focus[:3] if item)
        )


def _render_current_goal_module(profile: str) -> None:
    """Render the lightweight Current Goal editor on Home."""
    book = _goal_book_for_home(profile)
    goal = book.current()
    goal_key_id = goal.id if goal is not None else _goal_default_id()

    with st.container():
        st.subheader(ui["goal_module_title"])
        st.caption(ui["goal_module_caption"])

        reveal_private = True
        if goal is None:
            st.info(ui["goal_no_current"])
        elif goal.ui_visibility == "private":
            reveal_private = st.checkbox(
                ui["goal_reveal_private"],
                value=False,
                key=_goal_form_key(profile, "reveal_private", goal_key_id),
            )
            if not reveal_private:
                st.info(ui["goal_private_locked"])
        else:
            _render_goal_preview(goal)

        if goal is not None and goal.ui_visibility == "private" and not reveal_private:
            return

        form_title = (
            ui["goal_edit_title"]
            if goal is not None
            else ui["goal_create_title"]
        )
        with st.expander(form_title, expanded=goal is None):
            existing = goal or Goal(
                id=_goal_default_id(),
                title="",
                label="",
            )
            form_goal_id = existing.id or _goal_default_id()
            with st.form(_goal_form_key(profile, "form", form_goal_id)):
                title = st.text_input(
                    ui["goal_field_title"],
                    value=existing.title,
                    key=_goal_form_key(profile, "title", form_goal_id),
                )
                label = st.text_input(
                    ui["goal_field_label"],
                    value=existing.label,
                    key=_goal_form_key(profile, "label", form_goal_id),
                )
                c1, c2, c3 = st.columns(3)
                with c1:
                    status = st.selectbox(
                        ui["goal_field_status"],
                        GOAL_STATUSES,
                        index=GOAL_STATUSES.index(existing.status)
                        if existing.status in GOAL_STATUSES
                        else 0,
                        format_func=_goal_status_label,
                        key=_goal_form_key(profile, "status", form_goal_id),
                    )
                with c2:
                    start = st.text_input(
                        ui["goal_field_start"],
                        value=existing.start,
                        key=_goal_form_key(profile, "start", form_goal_id),
                    )
                with c3:
                    target = st.text_input(
                        ui["goal_field_target"],
                        value=existing.target,
                        key=_goal_form_key(profile, "target", form_goal_id),
                    )
                ui_visibility = st.selectbox(
                    ui["goal_field_ui_visibility"],
                    GOAL_UI_VISIBILITIES,
                    index=GOAL_UI_VISIBILITIES.index(
                        existing.ui_visibility
                    )
                    if existing.ui_visibility in GOAL_UI_VISIBILITIES
                    else 1,
                    format_func=_goal_visibility_label,
                    key=_goal_form_key(profile, "ui_visibility", form_goal_id),
                )
                include_agent = st.checkbox(
                    ui["goal_field_agent_context"],
                    value=(
                        existing.include_in_agent_context
                        and ui_visibility != "private"
                    ),
                    disabled=ui_visibility == "private",
                    key=_goal_form_key(profile, "agent_context", form_goal_id),
                )
                _include_public = st.checkbox(
                    ui["goal_field_public_output"],
                    value=False,
                    disabled=True,
                    key=_goal_form_key(profile, "public_output", form_goal_id),
                )
                st.caption(ui["goal_public_disabled_caption"])
                summary = st.text_area(
                    ui["goal_field_summary"],
                    value=existing.summary,
                    key=_goal_form_key(profile, "summary", form_goal_id),
                )
                alignment = st.text_area(
                    ui["goal_field_alignment"],
                    value=existing.alignment,
                    key=_goal_form_key(profile, "alignment", form_goal_id),
                )
                target_skills = st.text_area(
                    ui["goal_field_target_skills"],
                    value=_goal_lines_text(existing.target_skills),
                    key=_goal_form_key(profile, "target_skills", form_goal_id),
                )
                success_criteria = st.text_area(
                    ui["goal_field_success_criteria"],
                    value=_goal_lines_text(existing.success_criteria),
                    key=_goal_form_key(profile, "success_criteria", form_goal_id),
                )
                focus = st.text_area(
                    ui["goal_field_focus"],
                    value=_goal_lines_text(existing.focus),
                    key=_goal_form_key(profile, "focus", form_goal_id),
                )
                evidence_refs = st.text_area(
                    ui["goal_field_evidence_refs"],
                    value=_goal_lines_text(existing.evidence_refs),
                    key=_goal_form_key(profile, "evidence_refs", form_goal_id),
                )
                task_refs = st.text_area(
                    ui["goal_field_task_refs"],
                    value=_goal_lines_text(existing.task_refs),
                    key=_goal_form_key(profile, "task_refs", form_goal_id),
                )
                output_refs = st.text_area(
                    ui["goal_field_output_refs"],
                    value=_goal_lines_text(existing.output_refs),
                    key=_goal_form_key(profile, "output_refs", form_goal_id),
                )
                notes = st.text_area(
                    ui["goal_field_notes"],
                    value=existing.notes,
                    key=_goal_form_key(profile, "notes", form_goal_id),
                )
                submitted = st.form_submit_button(
                    ui["goal_save"],
                    type="primary",
                )
            if submitted:
                if not title.strip():
                    st.warning(ui["goal_title_required"])
                    st.stop()
                assert_files_current([_goals_path])
                next_goal = Goal(
                    id=existing.id or _goal_default_id(),
                    title=title.strip(),
                    label=label.strip(),
                    status=status,
                    start=start.strip(),
                    target=target.strip(),
                    ui_visibility=ui_visibility,
                    include_in_agent_context=include_agent,
                    include_in_public_output=False,
                    summary=summary.strip(),
                    alignment=alignment.strip(),
                    target_skills=_goal_text_lines(target_skills),
                    skill_links=list(existing.skill_links),
                    success_criteria=_goal_text_lines(success_criteria),
                    focus=_goal_text_lines(focus),
                    evidence_refs=_goal_text_lines(evidence_refs),
                    task_refs=_goal_text_lines(task_refs),
                    output_refs=_goal_text_lines(output_refs),
                    notes=notes.strip(),
                )
                by_id = book.by_id()
                by_id[next_goal.id] = next_goal
                book.goals = list(by_id.values())
                book.current_goal_id = next_goal.id
                book.profile = profile
                save_goal_book(profile, book)
                refresh_file_snapshots([_goals_path])
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["goal_saved"])
                st.rerun()

def _parse_skill_md_sections(
    text: str,
) -> list[tuple[str, str]]:
    """Split SKILL.md into (heading, body) pairs.

    Returns a list of tuples: first element is the section
    heading (e.g. '## Identity'), second is the body text
    under that heading. Content before the first heading
    is captured as '(header)'.
    """
    return parse_skill_md_sections(text)


def _rejoin_sections(
    sections: list[tuple[str, str]],
) -> str:
    """Reassemble sections back into a single string."""
    return rejoin_sections(sections)


def _save_skill_md(
    path: Path,
    content: str,
    success_message: str,
) -> None:
    """Persist SKILL.md edits and refresh cached web reads."""
    assert_files_current([path])
    path.write_text(content, encoding="utf-8")
    git_backup.record_change(
        [path],
        action=f"update {path.parent.name}/SKILL.md",
    )
    refresh_file_snapshots([path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(success_message)
    st.rerun()


def _dashboard_goal_bool(
    payload: dict,
    key: str,
    default: bool,
) -> bool:
    """Normalize dashboard event booleans."""
    if key not in payload:
        return default
    value = payload.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _dashboard_goal_lines_or_existing(
    payload: dict,
    key: str,
    existing: list[str],
) -> list[str]:
    """Parse list fields while preserving existing values when omitted."""
    if key not in payload:
        return list(existing)
    return _dashboard_goal_lines(payload.get(key))


def _dashboard_goal_text_or_existing(
    payload: dict,
    key: str,
    existing: str,
) -> str:
    """Parse text fields while preserving existing values when omitted."""
    if key not in payload:
        return existing
    return str(payload.get(key) or "").strip()


def _dashboard_goal_from_payload(
    *,
    existing: Goal,
    payload: dict,
    goal_id: str,
) -> Goal:
    """Build a normalized Goal from dashboard form payload."""
    title = str(payload.get("title") or "").strip()
    if not title:
        st.warning(ui["goal_title_required"])
        st.stop()
    status = str(payload.get("status") or existing.status).strip()
    if status not in GOAL_STATUSES:
        status = existing.status
    ui_visibility = str(
        payload.get("ui_visibility") or existing.ui_visibility
    ).strip()
    if ui_visibility not in GOAL_UI_VISIBILITIES:
        ui_visibility = existing.ui_visibility
    include_agent = _dashboard_goal_bool(
        payload,
        "include_in_agent_context",
        existing.include_in_agent_context,
    )
    if ui_visibility == "private":
        include_agent = False

    return Goal(
        id=goal_id,
        title=title,
        label=_dashboard_goal_text_or_existing(
            payload,
            "label",
            existing.label,
        ),
        status=status,
        start=_dashboard_goal_text_or_existing(
            payload,
            "start",
            existing.start,
        ),
        target=_dashboard_goal_text_or_existing(
            payload,
            "target",
            existing.target,
        ),
        ui_visibility=ui_visibility,
        include_in_agent_context=include_agent,
        include_in_public_output=False,
        summary=_dashboard_goal_text_or_existing(
            payload,
            "summary",
            existing.summary,
        ),
        alignment=_dashboard_goal_text_or_existing(
            payload,
            "alignment",
            existing.alignment,
        ),
        target_skills=_dashboard_goal_lines_or_existing(
            payload,
            "target_skills",
            existing.target_skills,
        ),
        skill_links=list(existing.skill_links),
        success_criteria=_dashboard_goal_lines_or_existing(
            payload,
            "success_criteria",
            existing.success_criteria,
        ),
        focus=_dashboard_goal_lines_or_existing(
            payload,
            "focus",
            existing.focus,
        ),
        evidence_refs=_dashboard_goal_lines_or_existing(
            payload,
            "evidence_refs",
            existing.evidence_refs,
        ),
        task_refs=_dashboard_goal_lines_or_existing(
            payload,
            "task_refs",
            existing.task_refs,
        ),
        output_refs=_dashboard_goal_lines_or_existing(
            payload,
            "output_refs",
            existing.output_refs,
        ),
        notes=_dashboard_goal_text_or_existing(
            payload,
            "notes",
            existing.notes,
        ),
    )


def _create_dashboard_goal(profile: str, payload: dict) -> None:
    """Create a new active goal without overwriting the primary by default."""
    book = _goal_book_for_home(profile)
    title = str(payload.get("title") or "").strip()
    goal_id = str(payload.get("id") or "").strip() or _unique_goal_id(book, title)
    existing = Goal(id=goal_id, title="", label="")
    next_goal = _dashboard_goal_from_payload(
        existing=existing,
        payload={**payload, "status": payload.get("status") or "active"},
        goal_id=goal_id,
    )
    by_id = book.by_id()
    by_id[next_goal.id] = next_goal
    book.goals = list(by_id.values())
    if (
        not book.primary()
        or _dashboard_goal_bool(payload, "set_as_primary", False)
    ):
        book.current_goal_id = next_goal.id
    _save_goal_book_for_home(profile, book, ui["goal_saved"])


def _edit_dashboard_goal(profile: str, payload: dict) -> None:
    """Edit an existing goal without changing the primary pointer."""
    book = _goal_book_for_home(profile)
    by_id = book.by_id()
    goal_id = str(payload.get("goal_id") or payload.get("id") or "").strip()
    existing = by_id.get(goal_id)
    if existing is None:
        st.warning(ui["goal_alignment_goal_missing"])
        return
    next_goal = _dashboard_goal_from_payload(
        existing=existing,
        payload=payload,
        goal_id=existing.id,
    )
    by_id[next_goal.id] = next_goal
    book.goals = list(by_id.values())
    _save_goal_book_for_home(profile, book, ui["goal_saved"])


def _archive_dashboard_goal(profile: str, payload: dict) -> None:
    """Archive a goal and move primary to the next active goal if needed."""
    book = _goal_book_for_home(profile)
    by_id = book.by_id()
    goal_id = str(payload.get("goal_id") or payload.get("id") or "").strip()
    goal = by_id.get(goal_id)
    if goal is None:
        st.warning(ui["goal_alignment_goal_missing"])
        return
    goal.status = "archived"
    by_id[goal.id] = goal
    book.goals = list(by_id.values())
    if book.current_goal_id == goal.id:
        next_primary = next(
            (item for item in book.goals if item.status == "active"),
            None,
        )
        book.current_goal_id = next_primary.id if next_primary is not None else ""
    state = _goal_skill_candidates_for_home(profile)
    if goal.id in state:
        del state[goal.id]
        st.session_state[_goal_skill_candidate_state_key(profile)] = state
    _save_goal_book_for_home(profile, book, ui["goal_archived"])


def _save_dashboard_goal(profile: str, payload: dict) -> None:
    """Compatibility wrapper for older dashboard goal-submit events."""
    book = _goal_book_for_home(profile)
    goal_id = str(payload.get("goal_id") or payload.get("id") or "").strip()
    if goal_id and goal_id in book.by_id():
        _edit_dashboard_goal(profile, payload)
        return
    _create_dashboard_goal(
        profile,
        {**payload, "set_as_primary": not bool(book.primary())},
    )


def _goal_for_alignment_event(
    profile: str,
    payload: dict,
) -> tuple[GoalBook, Goal | None]:
    """Resolve the goal addressed by a dashboard alignment event."""
    book = _goal_book_for_home(profile)
    goal_id = str(payload.get("goal_id") or payload.get("id") or "").strip()
    goal = book.by_id().get(goal_id) if goal_id else book.current()
    if goal is not None and goal.status == "archived":
        goal = None
    return book, goal


def _north_star_context_for_alignment(profile: str) -> str:
    """Return the privacy-safe North Star context for matching."""
    skill_content = load_skill_md(profile)
    identity = parse_identity_fields(skill_content)
    return north_star_context_from_identity(identity)


def _run_goal_skill_rule_match(profile: str, payload: dict) -> None:
    """Generate rule candidates and keep them pending in session state."""
    _book, goal = _goal_for_alignment_event(profile, payload)
    if goal is None:
        st.warning(ui["goal_alignment_goal_missing"])
        return
    candidates = rule_match_goal_to_skills(
        profile,
        goal,
        _north_star_context_for_alignment(profile),
    )
    _set_goal_skill_candidates(profile, goal.id, candidates)
    st.success(
        ui["goal_alignment_candidates_ready"].format(n=len(candidates))
    )
    st.rerun()


def _run_goal_skill_ai_match(profile: str, payload: dict) -> None:
    """Generate AI candidates and merge with pending rule candidates."""
    ai_config = _dashboard_effective_ai_config(profile, "dashboard.goal_skill_match")
    if ai_config["backend"] != "codex" and not llm_client.is_configured():
        render_llm_unavailable(ui)
        return
    _book, goal = _goal_for_alignment_event(profile, payload)
    if goal is None:
        st.warning(ui["goal_alignment_goal_missing"])
        return
    existing = _goal_skill_candidates_for_home(profile).get(goal.id, [])
    rule_candidates = [
        link
        for link in (GoalSkillLink.from_dict(item) for item in existing)
        if link is not None and link.source in ("rule", "rule+ai")
    ]
    ai_candidates = ai_match_goal_to_skills(
        profile,
        goal,
        _north_star_context_for_alignment(profile),
        backend=ai_config["backend"],
        model=ai_config["model"],
    )
    merged = merge_goal_skill_candidates(rule_candidates, ai_candidates)
    _set_goal_skill_candidates(profile, goal.id, merged)
    st.success(
        ui["goal_alignment_candidates_ready"].format(n=len(merged))
    )
    st.rerun()


def _normalize_confirmed_links(payload: dict) -> list[GoalSkillLink]:
    """Parse confirmed links sent by the React dashboard."""
    raw_links = payload.get("links")
    if not isinstance(raw_links, list):
        return []
    links: list[GoalSkillLink] = []
    seen: set[str] = set()
    for item in raw_links:
        link = GoalSkillLink.from_dict(item)
        if link is None or link.node_id in seen:
            continue
        seen.add(link.node_id)
        links.append(link)
    return links


def _confirm_goal_skill_links(profile: str, payload: dict) -> None:
    """Persist selected goal-skill links to goals.yaml."""
    book, goal = _goal_for_alignment_event(profile, payload)
    if goal is None:
        st.warning(ui["goal_alignment_goal_missing"])
        return
    links = _normalize_confirmed_links(payload)
    if not links:
        pending = _goal_skill_candidates_for_home(profile).get(goal.id, [])
        links = [
            link
            for link in (GoalSkillLink.from_dict(item) for item in pending)
            if link is not None
        ]
    goal.skill_links = links
    by_id = book.by_id()
    by_id[goal.id] = goal
    book.goals = list(by_id.values())
    state = _goal_skill_candidates_for_home(profile)
    if goal.id in state:
        del state[goal.id]
        st.session_state[_goal_skill_candidate_state_key(profile)] = state
    _save_goal_book_for_home(
        profile,
        book,
        ui["goal_alignment_links_saved"],
    )


def _manual_goal_skill_link(profile: str, payload: dict) -> None:
    """Append or replace one manual goal-skill link."""
    book, goal = _goal_for_alignment_event(profile, payload)
    if goal is None:
        st.warning(ui["goal_alignment_goal_missing"])
        return
    link = manual_goal_skill_link(
        profile,
        str(payload.get("node_id") or "").strip(),
    )
    if link is None:
        st.warning(ui["goal_alignment_node_missing"])
        return
    kept = [item for item in goal.skill_links if item.node_id != link.node_id]
    goal.skill_links = [*kept, link]
    by_id = book.by_id()
    by_id[goal.id] = goal
    book.goals = list(by_id.values())
    _save_goal_book_for_home(
        profile,
        book,
        ui["goal_alignment_links_saved"],
    )


def _set_primary_goal(profile: str, payload: dict) -> None:
    """Move the primary goal pointer to an existing goal."""
    book = _goal_book_for_home(profile)
    goal_id = str(payload.get("goal_id") or payload.get("id") or "").strip()
    if not book.set_primary(goal_id):
        st.warning(ui["goal_alignment_goal_missing"])
        return
    _save_goal_book_for_home(profile, book, ui["goal_primary_saved"])


def _handle_home_dashboard_event(event: dict | None, profile: str) -> bool:
    """Handle one new event emitted by the React Home dashboard."""
    if not isinstance(event, dict):
        return False
    action = str(event.get("action") or "").strip()
    if not action:
        return False
    event_id = str(event.get("event_id") or "").strip()
    dedupe_key = f"_home_dashboard_event_{profile}"
    if event_id and st.session_state.get(dedupe_key) == event_id:
        return False
    if event_id:
        st.session_state[dedupe_key] = event_id
    payload = event.get("payload")
    payload = payload if isinstance(payload, dict) else {}

    if action == "capture_inbox_submit":
        _capture_home_research_source(profile, payload)
        return True
    if action == "edit_goal_submit":
        _edit_dashboard_goal(profile, payload)
        return True
    if action == "create_goal_submit":
        _create_dashboard_goal(profile, payload)
        return True
    if action == "archive_goal":
        _archive_dashboard_goal(profile, payload)
        return True
    if action == "request_goal_skill_rule_match":
        _run_goal_skill_rule_match(profile, payload)
        return True
    if action == "request_goal_skill_ai_match":
        _run_goal_skill_ai_match(profile, payload)
        return True
    if action == "confirm_goal_skill_links":
        _confirm_goal_skill_links(profile, payload)
        return True
    if action == "manual_goal_skill_link":
        _manual_goal_skill_link(profile, payload)
        return True
    if action == "set_primary_goal":
        _set_primary_goal(profile, payload)
        return True
    if action == "set_north_star_display_open_profile_context":
        st.session_state[f"_open_profile_context_{profile}"] = True
        st.rerun()
        return True
    if action == "navigate":
        path = str(payload.get("path") or "").strip()
        if path:
            st.switch_page(path)
            return True
        return False
    if action == "open_section":
        section = str(payload.get("section") or "").strip()
        if section == "evidence":
            st.switch_page(EVIDENCE_REVIEW_PAGE)
            return True
        return False
    return False


def _page_link(path: str, label: str, *, help_text: str = "") -> None:
    """Render a Streamlit page link with a Markdown fallback."""
    try:
        st.page_link(path, label=label, help=help_text or None)
    except Exception:
        suffix = f" — {help_text}" if help_text else ""
        st.markdown(f"- **{label}** `{path}`{suffix}")


def _section_label(title: str) -> str:
    key_by_title = {
        "Research Fingerprint": "profile_section_research_fingerprint",
        "Thinking & Communication Style": "profile_section_thinking_style",
        "Growth Log": "profile_section_growth_log",
        "Influence & Output": "profile_section_influence_output",
    }
    return ui.get(key_by_title.get(title, ""), title)


def _identity_label(field: str) -> str:
    key_by_field = {
        "Name": "identity_name",
        "Domain": "identity_domain",
        "Journey": "identity_journey",
        "Current Role": "identity_current_role",
        "North Star": "identity_north_star",
        "North Star Brief": "identity_north_star_brief",
        "North Star Visibility": "identity_north_star_visibility",
    }
    return ui.get(key_by_field.get(field, ""), field)


def _render_dashboard_status_overview(
    kanban_summary: dict,
    skill_summary: dict,
    pending_summary: dict,
    health_summary: dict,
    public_summary: dict,
) -> None:
    st.subheader(ui["dashboard_status_overview"])
    cols = st.columns(5)
    lit = skill_summary.get("lit", 0)
    total = skill_summary.get("total", 0)
    health_counts = health_summary.get("counts") or {}
    health_value = (
        f"{health_counts.get('error', 0)} / "
        f"{health_counts.get('warning', 0)} / "
        f"{health_counts.get('info', 0)}"
    )
    cols[0].metric(
        ui["dashboard_metric_goal"],
        (
            ui["dashboard_goal_set"]
            if _goal_book_for_home(selected).current() is not None
            else ui["dashboard_goal_missing"]
        ),
    )
    cols[1].metric(
        ui["dashboard_metric_skill_lit"],
        f"{lit}/{total}" if total else "—",
    )
    cols[2].metric(
        ui["dashboard_metric_doing"],
        kanban_summary.get("doing_total", 0),
    )
    cols[3].metric(
        ui["dashboard_metric_pending_evidence"],
        (
            pending_summary.get("done_uncrystallized_count", 0)
            + pending_summary.get("unlinked_count", 0)
            + pending_summary.get("needs_review_count", 0)
            + pending_summary.get("status_risk_count", 0)
        ),
    )
    cols[4].metric(
        ui["dashboard_metric_health"],
        health_value,
        help=ui["dashboard_metric_health_help"],
    )

    if total:
        st.progress(
            float(skill_summary.get("lit_rate", 0.0)),
            text=ui["progress_overall"].format(
                pct=float(skill_summary.get("lit_rate", 0.0)),
            ),
        )
    if not public_summary.get("initialized"):
        st.caption(ui["dashboard_public_not_initialized"])


def _render_dashboard_doing(kanban_summary: dict) -> None:
    st.subheader(ui["dashboard_doing_title"])
    if kanban_summary.get("error"):
        st.warning(kanban_summary["error"])
        return
    doing = kanban_summary.get("doing") or []
    if not doing:
        st.info(ui["dashboard_doing_empty"])
        _page_link(
            "pages/3_Kanban.py",
            ui["quick_kanban"],
            help_text=ui["quick_kanban_help"],
        )
        return

    for item in doing:
        with st.container(border=True):
            st.markdown(f"**{item.get('title', '')}**")
            meta: list[str] = []
            if item.get("started_on"):
                meta.append(
                    ui["dashboard_doing_started"].format(
                        date=item["started_on"],
                    )
                )
            if item.get("tags"):
                meta.append(str(item["tags"]))
            if meta:
                st.caption(" · ".join(meta))
            if item.get("blocked_by"):
                st.warning(
                    ui["dashboard_doing_blocked"].format(
                        blocked=item["blocked_by"],
                    )
                )
    if kanban_summary.get("doing_total", 0) > len(doing):
        st.caption(
            ui["dashboard_doing_more"].format(
                n=kanban_summary["doing_total"] - len(doing),
            )
        )


def _render_dashboard_pending_evidence(pending_summary: dict) -> None:
    st.subheader(ui["dashboard_pending_evidence_title"])
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            ui["dashboard_done_uncrystallized"],
            pending_summary.get("done_uncrystallized_count", 0),
        )
        for item in pending_summary.get("done_uncrystallized") or []:
            st.caption(f"- {item.get('title', '')}")
    with c2:
        st.metric(
            ui["dashboard_unlinked_evidence"],
            pending_summary.get("unlinked_count", 0),
        )
        for item in pending_summary.get("unlinked") or []:
            st.caption(
                f"- `{item.get('id', '')}` · {item.get('title', '')}"
            )
    with c3:
        st.metric(
            ui["dashboard_needs_review_evidence"],
            pending_summary.get("needs_review_count", 0),
        )
        for item in pending_summary.get("needs_review") or []:
            st.caption(
                f"- `{item.get('id', '')}` · {item.get('title', '')}"
            )
    with c4:
        st.metric(
            ui["dashboard_status_risk_evidence"],
            pending_summary.get("status_risk_count", 0),
        )
        for item in pending_summary.get("status_risks") or []:
            st.caption(
                f"- `{item.get('id', '')}` · {item.get('label', '')}"
            )
    if (
        pending_summary.get("done_uncrystallized_count", 0) == 0
        and pending_summary.get("unlinked_count", 0) == 0
        and pending_summary.get("needs_review_count", 0) == 0
        and pending_summary.get("status_risk_count", 0) == 0
    ):
        st.success(ui["dashboard_pending_evidence_empty"])
    _page_link(
        EVIDENCE_REVIEW_PAGE,
        ui["quick_evidence_review"],
        help_text=ui["quick_evidence_review_help"],
    )


def _render_dashboard_health(health_summary: dict) -> None:
    st.subheader(ui["dashboard_health_title"])
    counts = health_summary.get("counts") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(ui["dashboard_health_errors"], counts.get("error", 0))
    c2.metric(ui["dashboard_health_warnings"], counts.get("warning", 0))
    c3.metric(ui["dashboard_health_info"], counts.get("info", 0))
    c4.metric(
        ui["dashboard_health_context_ready"],
        (
            ui["dashboard_yes"]
            if health_summary.get("context_ready")
            else ui["dashboard_no"]
        ),
    )
    issues = health_summary.get("issues") or []
    if not issues:
        st.success(ui["dashboard_health_empty"])
    else:
        for issue in issues[:3]:
            st.caption(
                f"{issue.get('severity', '').upper()} · "
                f"{issue.get('category', '')} · {issue.get('title', '')}"
            )
    _page_link(
        "pages/5_Profile_Health.py",
        ui["quick_profile_health"],
        help_text=ui["quick_profile_health_help"],
    )


def _render_dashboard_public(public_summary: dict) -> None:
    st.subheader(ui["dashboard_output_title"])
    if not public_summary.get("initialized"):
        st.info(ui["dashboard_output_empty"])
        _page_link(
            "pages/6_Output_Studio.py",
            ui["quick_public_site"],
            help_text=ui["quick_public_site_help"],
        )
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(ui["dashboard_public_drafts"], public_summary["draft_total"])
    c2.metric(
        ui["dashboard_public_published"],
        public_summary["published_total"],
    )
    c3.metric(
        ui["dashboard_public_visibility"],
        public_summary.get("visibility", "private"),
    )
    c4.metric(
        ui["dashboard_public_build"],
        (
            ui["dashboard_public_build_exists"]
            if public_summary.get("build_exists")
            else ui["dashboard_public_build_missing"]
        ),
    )
    st.caption(
        ui["dashboard_public_build_detail"].format(
            pages=public_summary.get("build_pages", 0),
            path=public_summary.get("build_output_dir", ""),
        )
    )
    _page_link(
        "pages/6_Output_Studio.py",
        ui["quick_public_site"],
        help_text=ui["quick_public_site_help"],
    )


def _render_quick_entries() -> None:
    st.subheader(ui["dashboard_quick_title"])
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        _page_link(
            "pages/3_Kanban.py",
            ui["quick_kanban"],
            help_text=ui["quick_kanban_help"],
        )
    with c2:
        _page_link(
            EVIDENCE_REVIEW_PAGE,
            ui["quick_evidence_review"],
            help_text=ui["quick_evidence_review_help"],
        )
    with c3:
        _page_link(
            "pages/7_Research.py",
            ui["quick_research"],
            help_text=ui["quick_research_help"],
        )
    with c4:
        _page_link(
            "pages/1_Skill_Tree.py",
            ui["quick_skill_tree"],
            help_text=ui["quick_skill_tree_help"],
        )
    with c5:
        _page_link(
            "pages/2_Gap_Analysis.py",
            ui["quick_gap"],
            help_text=ui["quick_gap_help"],
        )
    with c6:
        _page_link(
            "pages/6_Output_Studio.py",
            ui["quick_public_site"],
            help_text=ui["quick_public_site_help"],
        )


def _goal_summary_text(goal_payload: dict) -> str:
    projection = goal_payload.get("projection") if isinstance(goal_payload, dict) else None
    if isinstance(projection, dict):
        title = str(projection.get("title") or projection.get("label") or "").strip()
        if title:
            return title
    if isinstance(goal_payload, dict) and goal_payload.get("is_set"):
        return ui["goal_strip_hidden"]
    return ui["goal_no_current"]


def _pending_evidence_total(pending_summary: dict) -> int:
    return (
        int(pending_summary.get("done_uncrystallized_count", 0) or 0)
        + int(pending_summary.get("unlinked_count", 0) or 0)
        + int(pending_summary.get("needs_review_count", 0) or 0)
        + int(pending_summary.get("status_risk_count", 0) or 0)
    )


def _health_summary_text(health_summary: dict) -> str:
    counts = health_summary.get("counts") or {}
    return (
        f"{int(counts.get('error', 0) or 0)} / "
        f"{int(counts.get('warning', 0) or 0)} / "
        f"{int(counts.get('info', 0) or 0)}"
    )


def _render_home_scope_strip(payload: dict) -> None:
    st.subheader(ui["dashboard_scope_title"])
    goal_text = _goal_summary_text(payload.get("primary_goal") or payload.get("goal") or {})
    health_summary = payload.get("health") or {}
    ai_payload = payload.get("ai") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(ui["dashboard_scope_profile"], payload.get("profile", selected))
    c2.metric(ui["dashboard_scope_goal"], goal_text)
    c3.metric(
        ui["dashboard_scope_ai"],
        ui["dashboard_ai_ready"] if ai_payload.get("configured") else ui["dashboard_ai_not_ready"],
    )
    c4.metric(ui["dashboard_scope_health"], _health_summary_text(health_summary))


def _render_home_priority_cards(payload: dict) -> None:
    goal_payload = payload.get("primary_goal") or payload.get("goal") or {}
    kanban_summary = payload.get("kanban") or {}
    pending_summary = payload.get("pending_evidence") or {}
    goal_col, work_col, evidence_col = st.columns(3)
    with goal_col:
        with st.container(border=True):
            st.markdown(f"**{ui['dashboard_priority_goal_title']}**")
            st.write(_goal_summary_text(goal_payload))
            projection = goal_payload.get("projection") if isinstance(goal_payload, dict) else None
            if isinstance(projection, dict) and projection.get("summary"):
                st.caption(str(projection.get("summary")))
            _page_link("app.py", ui["dashboard_goal_edit_inline"])
    with work_col:
        with st.container(border=True):
            st.markdown(f"**{ui['dashboard_priority_work_title']}**")
            st.metric(ui["dashboard_metric_doing"], kanban_summary.get("doing_total", 0))
            doing = kanban_summary.get("doing") or []
            if doing:
                for item in doing[:3]:
                    st.caption(f"- {item.get('title', '')}")
            else:
                st.caption(ui["dashboard_doing_empty"])
            _page_link("pages/3_Kanban.py", ui["quick_kanban"], help_text=ui["quick_kanban_help"])
    with evidence_col:
        with st.container(border=True):
            st.markdown(f"**{ui['dashboard_priority_evidence_title']}**")
            st.metric(ui["dashboard_metric_pending_evidence"], _pending_evidence_total(pending_summary))
            st.caption(
                f"{ui['dashboard_done_uncrystallized']}: "
                f"{pending_summary.get('done_uncrystallized_count', 0)} · "
                f"{ui['dashboard_needs_review_evidence']}: "
                f"{pending_summary.get('needs_review_count', 0)}"
            )
            _page_link(
                EVIDENCE_REVIEW_PAGE,
                ui["quick_evidence_review"],
                help_text=ui["quick_evidence_review_help"],
            )


def _render_home_primary_actions() -> None:
    st.subheader(ui["dashboard_primary_actions_title"])
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _page_link(
            "pages/7_Research.py",
            ui["dashboard_action_capture"],
            help_text=ui["dashboard_action_capture_help"],
        )
    with c2:
        _page_link("pages/3_Kanban.py", ui["dashboard_action_kanban"])
    with c3:
        _page_link(EVIDENCE_REVIEW_PAGE, ui["dashboard_action_evidence"])
    with c4:
        _page_link("pages/6_Output_Studio.py", ui["dashboard_action_output"])


def _render_home_native_fallback(payload: dict) -> None:
    """Render the native Streamlit Home summary when React is unavailable."""
    kanban_summary = payload.get("kanban") or {}
    skill_summary = payload.get("skills") or {}
    pending_summary = payload.get("pending_evidence") or {}
    health_summary = payload.get("health") or {}
    public_summary = payload.get("public") or {}

    _render_home_scope_strip(payload)
    st.divider()

    _render_home_priority_cards(payload)
    st.divider()

    _render_home_primary_actions()
    st.divider()

    with st.expander(ui["goal_module_title"], expanded=False):
        _render_current_goal_module(selected)

    st.divider()
    _render_dashboard_status_overview(
        kanban_summary,
        skill_summary,
        pending_summary,
        health_summary,
        public_summary,
    )
    st.divider()

    _render_dashboard_doing(kanban_summary)
    st.divider()

    _render_dashboard_pending_evidence(pending_summary)
    st.divider()

    _render_dashboard_health(health_summary)
    st.divider()

    _render_dashboard_public(public_summary)
    st.divider()

    _render_quick_entries()


def _render_resume_ingest(profile: str) -> None:
    with st.expander(ui["profile_evidence_import_expander"], expanded=False):
        st.caption(ui["profile_evidence_import_caption"])
        resume_text = st.text_area(
            ui["resume_placeholder"],
            height=140,
            key=f"resume_txt_{profile}",
        )
        allow_resume = st.checkbox(
            ui["resume_allow_status"],
            value=False,
            key=f"resume_allow_{profile}",
        )
        st.caption(ui["resume_allow_status_help"])
        rgen = st.button(
            ui["resume_generate"],
            key=f"resume_gen_{profile}",
        )
        if rgen and resume_text.strip():
            if not llm_client.is_configured():
                render_llm_unavailable(ui)
            else:
                with st.spinner(ui["resume_spinner"]):
                    patch, err = ingest_resume_json(
                        profile,
                        resume_text,
                    )
                if err is not None:
                    st.error(ui["resume_err"].format(msg=err))
                elif patch is not None:
                    drop_streamlit_widget_keys(
                        [
                            f"rp_pool_{profile}",
                            f"rp_tree_{profile}",
                        ]
                    )
                    st.session_state[
                        f"resume_ingest_patch_{profile}"
                    ] = patch
                    st.rerun()

        rkey = f"resume_ingest_patch_{profile}"
        if rkey not in st.session_state:
            return

        remember_allow_and_drop_yaml_preview_keys(
            allow_resume,
            prev_state_key=f"_resume_allow_prev_{profile}",
            pool_key=f"rp_pool_{profile}",
            tree_key=f"rp_tree_{profile}",
        )
        patch = st.session_state[rkey]
        pool_r = load_evidence_pool_raw(profile)
        tree_r = load_skill_tree_raw(profile)
        st.caption(
            ui["merge_preview_llm_status_line"].format(
                mode=(
                    ui["merge_llm_status_applied"]
                    if allow_resume
                    else ui["merge_llm_status_ignored"]
                ),
            )
        )
        rmerge = merge_ingest_patch(
            profile,
            pool_r,
            tree_r,
            patch,
            allow_status_change=allow_resume,
            bump_locked_with_evidence=True,
        )
        if rmerge.warnings:
            st.caption(ui["resume_warn"])
            for w in rmerge.warnings:
                st.caption(f"- {w}")
        if rmerge.ok and (
            rmerge.merged_pool is not None
            or rmerge.merged_tree is not None
        ):
            lab = schema_node_labels(tree_r)
            new_ev, tree_delta = ingest_preview_delta(
                pool_r,
                tree_r,
                rmerge.merged_pool,
                rmerge.merged_tree,
                lab,
            )
            with st.expander(
                ui["merge_preview_delta_title"],
                expanded=True,
            ):
                if new_ev:
                    st.markdown(
                        f"**{ui['merge_preview_delta_new_evidence']}**"
                    )
                    for line in new_ev:
                        st.markdown(f"- {line}")
                if tree_delta:
                    st.markdown(
                        f"**{ui['merge_preview_delta_tree']}**"
                    )
                    for line in tree_delta:
                        st.markdown(f"- {line}")
                if not new_ev and not tree_delta:
                    st.caption(ui["merge_preview_delta_none"])
        if rmerge.ok and (
            rmerge.merged_pool is not None
            or rmerge.merged_tree is not None
        ):
            st.caption(ui["merge_preview_yaml_readonly_caption"])
        if rmerge.ok and rmerge.merged_pool:
            st.markdown(f"**{ui['resume_preview_pool']}**")
            st.code(
                yaml.dump(
                    rmerge.merged_pool,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                language="yaml",
            )
        if rmerge.ok and rmerge.merged_tree:
            st.markdown(f"**{ui['resume_preview_tree']}**")
            st.code(
                yaml.dump(
                    rmerge.merged_tree,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                language="yaml",
            )
        if not rmerge.ok:
            for e in rmerge.errors:
                st.error(e)
            return
        if st.button(
            ui["resume_apply"],
            key=f"resume_apply_{profile}",
            type="primary",
        ):
            assert_files_current(
                [_pool_path, _tree_path, _skill_md_path]
            )
            _, apply_r = run_ingest_patch(
                profile,
                patch,
                allow_status_change=allow_resume,
                bump_locked_with_evidence=True,
                dry_run=False,
            )
            if apply_r.ok:
                clear_web_cache()
                refresh_file_snapshots(
                    [_pool_path, _tree_path, _skill_md_path]
                )
                stash_git_backup_results()
                st.success(ui["resume_applied"])
                del st.session_state[rkey]
                render_git_backup_notices()
            else:
                for e in apply_r.errors:
                    st.error(e)
                for w in apply_r.warnings:
                    st.warning(w)


def _render_profile_context(profile: str) -> None:
    skill_path = profile_dir(profile) / "SKILL.md"
    skill_content = load_skill_md(profile)
    open_key = f"_open_profile_context_{profile}"
    expanded = bool(st.session_state.pop(open_key, False))

    with st.expander(ui["profile_context_expander"], expanded=expanded):
        st.caption(ui["profile_context_caption"])
        if not skill_content:
            st.warning(ui["warning_no_skill_md"])
            return

        identity = parse_identity_fields(skill_content)
        with st.form(f"profile_context_form_{profile}"):
            st.markdown(f"**{ui['profile_context_structured_title']}**")
            identity_updates: dict[str, str] = {}
            field_cols = st.columns(2)
            for idx, field in enumerate(IDENTITY_FIELDS):
                target = field_cols[idx % 2]
                with target:
                    if field == "North Star":
                        identity_updates[field] = st.text_area(
                            _identity_label(field),
                            value=identity.get(field, ""),
                            height=90,
                            key=f"profile_identity_{profile}_{field}",
                        )
                    elif field == "North Star Visibility":
                        current_visibility = normalize_north_star_visibility(
                            identity.get(field, "")
                        )
                        identity_updates[field] = st.selectbox(
                            _identity_label(field),
                            NORTH_STAR_VISIBILITIES,
                            index=NORTH_STAR_VISIBILITIES.index(
                                current_visibility
                            ),
                            format_func=lambda value: ui.get(
                                f"north_star_visibility_{value}",
                                value,
                            ),
                            key=f"profile_identity_{profile}_{field}",
                        )
                    elif field == "North Star Brief":
                        identity_updates[field] = st.text_input(
                            _identity_label(field),
                            value=identity.get(field, ""),
                            key=f"profile_identity_{profile}_{field}",
                        )
                    else:
                        identity_updates[field] = st.text_input(
                            _identity_label(field),
                            value=identity.get(field, ""),
                            key=f"profile_identity_{profile}_{field}",
                        )

            st.markdown(f"**{ui['profile_context_narrative_title']}**")
            st.caption(ui["profile_context_narrative_caption"])
            narrative_updates: dict[str, str] = {}
            for title in LONG_NARRATIVE_SECTIONS:
                body = section_body(skill_content, title)
                narrative_updates[title] = st.text_area(
                    _section_label(title),
                    value=body,
                    height=max(150, min(360, body.count("\n") * 20 + 80)),
                    key=f"profile_narrative_{profile}_{title}",
                )

            submitted = st.form_submit_button(
                ui["save_profile_context"],
                type="primary",
            )

        if submitted:
            updated = apply_profile_context_structured_edits(
                skill_content,
                identity_fields=identity_updates,
                narrative_sections=narrative_updates,
            )
            _save_skill_md(skill_path, updated, ui["home_saved"])

        st.markdown(f"**{ui['generated_block_preview_title']}**")
        st.caption(ui["generated_block_owner_hint"])
        blocks = extract_generated_blocks(skill_content)
        for block in GENERATED_BLOCKS:
            with st.expander(
                ui["generated_block_expander"].format(block=block),
                expanded=False,
            ):
                if block == "skill_tree":
                    _page_link(
                        "pages/1_Skill_Tree.py",
                        ui["quick_skill_tree"],
                        help_text=ui["generated_block_skill_tree_help"],
                    )
                elif block == "current_focus":
                    _page_link(
                        "pages/3_Kanban.py",
                        ui["quick_kanban"],
                        help_text=ui["generated_block_kanban_help"],
                    )
                st.caption(ui["generated_block_sync_hint"])
                st.code(
                    blocks.get(block, ui["generated_block_missing"]),
                    language="markdown",
                )

        with st.expander(ui["raw_markdown_expander"], expanded=False):
            st.warning(ui["raw_drift_warning"])
            edited_raw = st.text_area(
                ui["raw_label"],
                value=skill_content,
                height=500,
                key=f"skill_md_raw_{profile}",
            )
            col_save2, col_hint2 = st.columns([1, 4])
            with col_save2:
                if st.button(
                    ui["save_skill_md"],
                    type="primary",
                    key=f"save_raw_{profile}",
                ):
                    _save_skill_md(
                        skill_path,
                        edited_raw,
                        ui["home_saved"],
                    )
            with col_hint2:
                st.caption(
                    ui["hint_after_save"].format(
                        profile=profile,
                    )
                )


def _profile_context_open_requested(profile: str) -> bool:
    """Return whether the dashboard asked to reveal Profile Context."""
    return bool(st.session_state.get(f"_open_profile_context_{profile}", False))


def _render_dashboard_help() -> None:
    """Render the Dashboard usage guide in a compact top-right surface."""
    render_page_help(
        ui,
        body_key="dashboard_help_body",
        label_key="dashboard_help_title",
        key="dashboard_help",
        docs_path="docs/zh/guides/dashboard.md",
    )


def _render_dashboard_top_actions(profile: str) -> None:
    """Render Dashboard help and AI settings controls."""
    help_col, ai_col = st.columns(2, gap="small", vertical_alignment="top")
    with help_col:
        _render_dashboard_help()
    with ai_col:
        if hasattr(st, "popover"):
            with st.popover(ui["dashboard_ai_settings_title"], width="stretch"):
                _render_dashboard_ai_settings(profile)
        else:
            with st.expander(ui["dashboard_ai_settings_title"], expanded=False):
                _render_dashboard_ai_settings(profile)
    canvas_base = _dashboard_canvas_base()
    if canvas_base:
        canvas_ok, canvas_message = _dashboard_canvas_status(canvas_base, profile)
        canvas_url = _dashboard_canvas_url(canvas_base, profile)
        if canvas_ok is False:
            st.button(
                ui["dashboard_open_8502_canvas"],
                width="stretch",
                disabled=True,
                help=(
                    ui["dashboard_canvas_sidecar_link_disabled_help"]
                    + (f" {canvas_message}" if canvas_message else "")
                ),
            )
            st.caption(ui["dashboard_canvas_sidecar_unavailable"].format(base=canvas_base))
        else:
            st.link_button(
                ui["dashboard_open_8502_canvas"],
                canvas_url,
                width="stretch",
            )


def _render_home_page() -> None:
    """Render the Daily Dashboard page."""
    _prepare_home_state()

    title_col, action_col = st.columns([1, 0.34], vertical_alignment="top")
    with title_col:
        st.title(ui["app_page_title"])
        st.caption(ui["app_caption"].format(profile=selected))
        st.caption(ui["page_context_line"])
    with action_col:
        _render_dashboard_top_actions(selected)

    profile_context_requested = _profile_context_open_requested(selected)
    if profile_context_requested:
        _render_profile_context(selected)
        st.divider()

    home_dashboard_payload = dashboard_payload(selected)
    home_dashboard_event = st_home_dashboard(
        payload=home_dashboard_payload,
        key=f"home_dashboard_{selected}",
        height=900,
    )
    if home_dashboard_event is None:
        _render_home_native_fallback(home_dashboard_payload)
    elif home_dashboard_event.get("action"):
        if _handle_home_dashboard_event(home_dashboard_event, selected):
            return

    _render_resume_ingest(selected)

    if not profile_context_requested:
        st.divider()
        _render_profile_context(selected)


def _navigation_pages() -> dict[str, list[st.Page]]:
    """Return the grouped sidebar navigation."""
    return {
        ui["sidebar_nav_home_group"]: [
            st.Page(
                _render_home_page,
                title=ui["sidebar_nav_dashboard"],
                icon=":material/dashboard:",
                default=True,
            ),
        ],
        ui["sidebar_nav_work_group"]: [
            st.Page(
                "pages/11_Project_Board.py",
                title=ui["sidebar_nav_project_board"],
                icon=":material/account_tree:",
            ),
            st.Page(
                "pages/3_Kanban.py",
                title=ui["sidebar_nav_kanban"],
                icon=":material/view_kanban:",
            ),
            st.Page(
                "pages/2_Gap_Analysis.py",
                title=ui["sidebar_nav_gap"],
                icon=":material/troubleshoot:",
            ),
            st.Page(
                "pages/7_Research.py",
                title=ui["sidebar_nav_research"],
                icon=":material/travel_explore:",
            ),
            st.Page(
                EVIDENCE_REVIEW_PAGE,
                title=ui["sidebar_nav_evidence_review"],
                icon=":material/fact_check:",
            ),
        ],
        ui["sidebar_nav_growth_group"]: [
            st.Page(
                "pages/1_Skill_Tree.py",
                title=ui["sidebar_nav_skill_map"],
                icon=":material/account_tree:",
            ),
            st.Page(
                "pages/8_Review.py",
                title=ui["sidebar_nav_review"],
                icon=":material/rate_review:",
            ),
            st.Page(
                "pages/5_Profile_Health.py",
                title=ui["sidebar_nav_health"],
                icon=":material/health_and_safety:",
            ),
            st.Page(
                "pages/9_Agent_Activity.py",
                title=ui["sidebar_nav_agent_activity"],
                icon=":material/history:",
            ),
        ],
        ui["sidebar_nav_output_group"]: [
            st.Page(
                "pages/6_Output_Studio.py",
                title=ui["sidebar_nav_public"],
                icon=":material/edit_note:",
            ),
            st.Page(
                "pages/10_Public_Build.py",
                title=ui["sidebar_nav_public_build"],
                icon=":material/rocket_launch:",
            ),
        ],
        ui["sidebar_nav_team_group"]: [
            st.Page(
                "pages/4_Team_View.py",
                title=ui["sidebar_nav_team"],
                icon=":material/groups:",
            ),
        ],
    }


def main() -> None:
    """Run the Streamlit app with product-level navigation."""
    st.session_state["_nblane_native_navigation"] = True
    _sync_home_ui()
    page = st.navigation(_navigation_pages(), expanded=True)
    page.run()


if __name__ == "__main__":
    main()
