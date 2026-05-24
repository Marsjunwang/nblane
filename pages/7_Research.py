"""Paper Reading Studio -- search, read, annotate, and cite papers."""

from __future__ import annotations

import os
import html
import json
import re
import time
import urllib.request
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse

import streamlit as st
import yaml

from nblane.core import codex_adapter
from nblane.core import llm as llm_client
from nblane.core.auth import mint_reader_token
from nblane.core.ai import (
    answer_paper_question,
    explain_paper_selection,
    extract_paper_claims,
    generate_paper_review_card,
    generate_paper_source_guide,
    search_papers_codex,
    translate_paper_segments,
)
from nblane.core.io import profile_dir
from nblane.core.reader_actions import ReaderActionContext, handle_reader_action
from nblane.core.web_preferences import (
    AI_ACTION_DEFAULT_BACKENDS,
    load_web_preferences,
    update_web_preferences,
)
from nblane.core.paper_library_workspace import (
    build_paper_library_payload,
    handle_paper_library_event,
    resolve_paper_library_runtime,
)
from nblane.core.research_papers import (
    PAPER_SEARCH_PROVIDERS,
    PaperSearchResult,
    _paper_search_imported_refs,
    _paper_search_library_tree_hint,
    _paper_search_result_has_downloadable_pdf,
    auto_chunk_paper,
    build_reader_payload,
    create_chunk_from_annotation,
    create_paper_library_node,
    create_paper_annotation,
    create_reading_note_markdown,
    create_reading_note_pack_markdown,
    ensure_paper_reading_artifacts,
    extract_paper_pages,
    extract_paper_segments,
    format_research_citations,
    grobid_readiness,
    import_paper_pdf,
    import_paper_search_results,
    import_paper_url,
    load_paper_analysis,
    load_paper_annotations,
    load_paper_library_tree,
    load_paper_pages,
    load_paper_segments,
    load_paper_translations,
    mark_imported_paper_results,
    move_papers_to_node,
    normalize_translation_row,
    paper_library_paths,
    paper_citation_diagnostics,
    paper_overview,
    paper_rows,
    position_paper_library_node,
    purge_paper_library_node,
    remove_papers_from_node,
    rename_paper_library_node,
    reorder_paper_library_node,
    restore_paper_library_node,
    save_paper_analysis,
    save_paper_annotations,
    save_paper_note,
    save_research_export,
    search_papers,
    text_hash,
    trash_paper_library_node,
    translate_full_paper,
    translation_text_from_row,
    translation_rows_for_segments,
    upsert_paper_translations,
    validate_paper_library,
)
from nblane.paper_library_component import (
    paper_library_component_available,
    st_paper_library_tree,
)
from nblane.research_paper_reader_component.events import (
    ANNOTATION_CREATE,
    ANNOTATION_DELETE,
    ANNOTATION_UPDATE,
    ASK_PAPER,
    CODEX_DEEP_READ,
    CREATE_CHUNK_FROM_SELECTION,
    CREATE_CITATION,
    EXPLAIN_SELECTION,
    READER_STATE_CHANGED,
    REQUEST_PAGE_PREVIEW,
    REQUEST_PAGE_PREVIEWS,
    REQUEST_READER_CONTEXT,
    RETRY_TRANSLATION_SCOPE,
    SAVE_PROGRESS,
    TRANSLATE_FULL_PAPER,
    TRANSLATE_SELECTION,
    TRANSLATE_VISIBLE_PAGES,
    clean_page_list,
)
from nblane.core.research_sources import (
    SOURCE_KINDS,
    SOURCE_STATUSES,
    SOURCE_VISIBILITIES,
    ResearchReading,
    add_research_source,
    apply_research_evidence_candidate,
    generate_reading_draft,
    load_research_sources,
    research_evidence_patch,
    save_research_sources,
    update_research_source,
)
from nblane.core.research_connectors import (
    CONNECTOR_PROVIDERS,
    discover_connector_items,
    import_connector_items,
    import_manual_connector_items,
    load_connectors,
    preview_manual_connector_items,
    sync_connector,
    upsert_connector,
)
from nblane.core.research_workspace import (
    RESEARCH_CLAIM_TYPES,
    RESEARCH_CHUNK_KINDS,
    build_research_claim_review_payload,
    build_research_export_payload,
    build_research_export_manifest,
    build_research_overview_payload,
    build_synthesis_draft_review,
    create_chunk,
    create_citation,
    create_citation_from_chunk,
    draft_synthesis_from_claims,
    load_chunks,
    load_research_citations,
    load_research_claims,
    load_research_drafts,
    merge_duplicate_research_claims,
    patch_research_claim,
    research_claim_to_evidence_candidate,
    research_draft_to_blog_candidate,
    research_draft_to_project_update_candidate,
    research_draft_to_resume_bullet_candidates,
    research_output_project_options,
    request_citation_for_claim,
    update_research_claim_links,
    update_research_claim_status,
    upsert_research_claim,
    verify_research_citations,
)
from nblane.core.public_site import create_blog_draft
from nblane.web_auth import require_login, sidecar_auth_handoff_token
from nblane.web_cache import clear_web_cache
from nblane.web_i18n import research_ui
from nblane.web_shared import (
    apply_ui_language_from_session,
    assert_files_current,
    ensure_file_snapshot,
    refresh_file_snapshots,
    render_current_goal_strip,
    render_git_backup_notices,
    select_profile,
    stash_git_backup_results,
)

apply_ui_language_from_session()

ui = research_ui()
user = require_login()
selected = select_profile()
ui = research_ui()
render_git_backup_notices()

_pdir = profile_dir(selected)
_sources_path = _pdir / "research" / "sources.yaml"
_research_claims_path = _pdir / "research" / "claims.yaml"
_research_citations_path = _pdir / "research" / "citations.yaml"
_research_connectors_path = _pdir / "research" / "connectors.yaml"
ensure_file_snapshot(_sources_path)
ensure_file_snapshot(_research_claims_path)
ensure_file_snapshot(_research_citations_path)
ensure_file_snapshot(_research_connectors_path)


def _text_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _lines_text(values: object) -> str:
    if not isinstance(values, list):
        return ""
    return "\n".join(str(item).strip() for item in values if str(item).strip())


def _tags_text(values: object) -> str:
    if not isinstance(values, list):
        return ""
    return ", ".join(str(item).strip() for item in values if str(item).strip())


def _tags(value: str) -> list[str]:
    return [
        item.strip()
        for item in value.replace("\n", ",").split(",")
        if item.strip()
    ]


def _l(key: str, default: str) -> str:
    return ui.get(key, default)


_MODEL_DEFAULT = "__default__"
_MODEL_CUSTOM = "__custom__"
_BACKEND_DEFAULT = "__default__"
_LLM_MODEL_SUGGESTIONS = (
    "qwen3.6-plus",
    "qwen-plus",
    "qwen-max",
    "deepseek-chat",
    "deepseek-reasoner",
    "gpt-4o",
    "gpt-4o-mini",
)
_CODEX_MODEL_SUGGESTIONS = (
    "gpt-5.5",
    "gpt-5.1-codex",
    "gpt-5-codex",
)
_AI_CONFIG_GROUPS = (
    (
        "paper",
        "Paper",
        (
            (
                "research.paper_search_codex",
                "Paper search",
                "Search and candidate discovery.",
            ),
            (
                "research.paper_translate",
                "Paper translation",
                "Full paper, visible pages, and selection translation.",
            ),
            (
                "research.paper_review_card",
                "Paper review",
                "Analyze Paper / review card generation.",
            ),
            (
                "research.paper_source_guide",
                "Source guide",
                "Structured paper summary and reading guide.",
            ),
            (
                "research.paper_qa",
                "Paper Q&A",
                "Ask-paper answers from reader context.",
            ),
            (
                "research.paper_claim_extract",
                "Claim extraction",
                "Research claim candidates from paper text.",
            ),
            (
                "research.paper_deep_read_codex",
                "Deep read",
                "High-depth paper analysis candidate.",
            ),
            (
                "research.paper_compare_codex",
                "Paper compare",
                "Compare multiple imported papers.",
            ),
        ),
    ),
)


def _ai_action_prefs() -> dict[str, dict[str, str]]:
    prefs = load_web_preferences(selected)
    ai = prefs.get("ai") if isinstance(prefs.get("ai"), dict) else {}
    actions = ai.get("actions") if isinstance(ai.get("actions"), dict) else {}
    out: dict[str, dict[str, str]] = {}
    for action_name in AI_ACTION_DEFAULT_BACKENDS:
        action = actions.get(action_name) if isinstance(actions.get(action_name), dict) else {}
        out[action_name] = {
            "backend": str(action.get("backend") or "").strip(),
            "llm_model": str(action.get("llm_model") or "").strip(),
            "codex_model": str(action.get("codex_model") or "").strip(),
        }
    return out


def _model_picker(
    label: str,
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
    options = [_MODEL_DEFAULT, *model_suggestions, _MODEL_CUSTOM]
    if current and current not in model_suggestions:
        initial = _MODEL_CUSTOM
    elif current:
        initial = current
    else:
        initial = _MODEL_DEFAULT
    choice = st.selectbox(
        label,
        options,
        index=options.index(initial),
        format_func=lambda value: (
            _l("ai_config_use_default", "Use app default")
            if value == _MODEL_DEFAULT
            else _l("ai_config_custom_model", "Custom model")
            if value == _MODEL_CUSTOM
            else value
        ),
        key=f"ai_config:{selected}:{pref_name}:choice",
    )
    if choice == _MODEL_DEFAULT:
        return ""
    if choice == _MODEL_CUSTOM:
        return st.text_input(
            _l("ai_config_custom_model", "Custom model"),
            value=current if current and current not in model_suggestions else "",
            key=f"ai_config:{selected}:{pref_name}:custom",
        ).strip()
    return str(choice).strip()


def _backend_picker(label: str, pref_name: str, current: str, default_backend: str) -> str:
    options = [_BACKEND_DEFAULT, "llm", "codex"]
    current = str(current or "").strip()
    initial = current if current in {"llm", "codex"} else _BACKEND_DEFAULT
    choice = st.selectbox(
        label,
        options,
        index=options.index(initial),
        format_func=lambda value: (
            f"{_l('ai_config_use_default', 'Use app default')} ({_backend_label(default_backend)})"
            if value == _BACKEND_DEFAULT
            else "LLM"
            if value == "llm"
            else "Codex"
        ),
        key=f"ai_config:{selected}:{pref_name}:choice",
    )
    return "" if choice == _BACKEND_DEFAULT else str(choice).strip()


def _backend_label(backend: str) -> str:
    return "Codex" if backend == "codex" else "LLM"


def _default_backend_for_action(action_name: str) -> str:
    backend = AI_ACTION_DEFAULT_BACKENDS.get(action_name, "llm")
    return backend if backend in {"llm", "codex"} else "llm"


def _effective_backend(action_name: str, config: dict[str, str]) -> str:
    configured = str(config.get("backend") or "").strip()
    return configured if configured in {"llm", "codex"} else _default_backend_for_action(action_name)


def _effective_model(
    action_name: str,
    config: dict[str, str],
    *,
    llm_default: str,
    codex_default: str,
) -> str:
    backend = _effective_backend(action_name, config)
    if backend == "codex":
        return str(config.get("codex_model") or codex_default or "").strip()
    return str(config.get("llm_model") or llm_default or "").strip()


def _effective_action_caption(
    action_name: str,
    config: dict[str, str],
    *,
    llm_default: str,
    codex_default: str,
) -> str:
    backend = _effective_backend(action_name, config)
    model = _effective_model(
        action_name,
        config,
        llm_default=llm_default,
        codex_default=codex_default,
    )
    model_label = model or (
        _l("ai_config_codex_cli_default", "Codex CLI default")
        if backend == "codex"
        else _l("missing", "missing")
    )
    test = _model_test_summary(backend, model, action_name=action_name)
    bits = [
        f"{_l('ai_config_effective_backend', 'Effective backend')}: {_backend_label(backend)}",
        f"{_l('ai_config_effective_model', 'Effective model')}: {model_label}",
    ]
    if test:
        bits.append(test)
    return " · ".join(bits)


def _model_test_key(backend: str, model: str, *, action_name: str = "") -> str:
    safe_model = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(model or "default")).strip("_")
    safe_action = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(action_name or "global")).strip("_")
    return f"ai_config:{selected}:test:{safe_action or 'global'}:{backend}:{safe_model or 'default'}"


def _record_model_test(
    backend: str,
    model: str,
    ok: bool,
    latency: float,
    message: str,
    *,
    action_name: str = "",
) -> None:
    st.session_state[_model_test_key(backend, model, action_name=action_name)] = {
        "ok": bool(ok),
        "latency": float(latency),
        "message": str(message or "").strip()[:240],
        "tested_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def _model_test_summary(backend: str, model: str, *, action_name: str = "") -> str:
    result = st.session_state.get(_model_test_key(backend, model, action_name=action_name))
    if not isinstance(result, dict):
        return ""
    status = (
        _l("ai_config_available", "available")
        if result.get("ok")
        else _l("ai_config_unavailable", "unavailable")
    )
    latency = float(result.get("latency") or 0.0)
    return f"{status}, {latency:.1f}s"


def _run_llm_availability_test(model: str, *, action_name: str = "") -> None:
    started = time.perf_counter()
    if not llm_client.is_configured():
        message = _l("ai_config_llm_unconfigured", "LLM API key is not configured.")
        _record_model_test("llm", model, False, time.perf_counter() - started, message, action_name=action_name)
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
        _record_model_test("llm", model, False, latency, reply, action_name=action_name)
        st.warning(reply)
    else:
        _record_model_test("llm", model, True, latency, reply or "OK", action_name=action_name)
        st.success(
            f"{_l('ai_config_model_available', 'Model test succeeded.')} ({latency:.1f}s)"
        )


def _run_codex_availability_test(model: str, *, action_name: str = "") -> None:
    started = time.perf_counter()
    cfg = codex_adapter.current_config(profile=selected)
    if str(model or "").strip():
        cfg = replace(cfg, model=str(model or "").strip())
    result = codex_adapter.run_readonly_codex_prompt(
        selected,
        "Return exactly OK. Do not edit files.",
        config=cfg,
        timeout_seconds=min(float(cfg.timeout_seconds or 30.0), 30.0),
    )
    latency = time.perf_counter() - started
    if result.ok:
        _record_model_test("codex", model, True, latency, result.output or "OK", action_name=action_name)
        st.success(
            f"{_l('ai_config_model_available', 'Model test succeeded.')} ({latency:.1f}s)"
        )
    else:
        message = codex_adapter.readable_codex_error(
            result.error,
            result.stderr,
            result.output,
            result.stdout,
        )
        _record_model_test("codex", model, False, latency, message, action_name=action_name)
        st.warning(message)


def _run_action_availability_test(
    action_name: str,
    config: dict[str, str],
    *,
    llm_default: str,
    codex_default: str,
) -> None:
    backend = _effective_backend(action_name, config)
    model = _effective_model(
        action_name,
        config,
        llm_default=llm_default,
        codex_default=codex_default,
    )
    if backend == "codex":
        _run_codex_availability_test(model, action_name=action_name)
    else:
        _run_llm_availability_test(model, action_name=action_name)


def _render_action_config_row(
    action_name: str,
    label: str,
    help_text: str,
    current: dict[str, str],
    *,
    llm_default: str,
    codex_default: str,
) -> dict[str, str]:
    default_backend = _default_backend_for_action(action_name)
    st.markdown(f"**{label}**")
    st.caption(help_text)
    cols = st.columns([1.05, 1.25, 1.25, 0.85], gap="small")
    with cols[0]:
        backend = _backend_picker(
            _l("ai_config_backend", "Backend"),
            f"{action_name}:backend",
            current.get("backend", ""),
            default_backend,
        )
    with cols[1]:
        llm_model = _model_picker(
            _l("ai_config_llm_model", "LLM model"),
            f"{action_name}:llm_model",
            current.get("llm_model", ""),
            llm_default,
            _LLM_MODEL_SUGGESTIONS,
        )
    with cols[2]:
        codex_model = _model_picker(
            _l("ai_config_codex_model", "Codex model"),
            f"{action_name}:codex_model",
            current.get("codex_model", ""),
            codex_default,
            _CODEX_MODEL_SUGGESTIONS,
        )
    test_clicked = False
    with cols[3]:
        st.caption(_l("ai_config_test", "Test"))
        test_clicked = st.form_submit_button(
            _l("ai_config_test_model", "Test model"),
            key=f"ai_config:{selected}:{action_name}:test_model",
            use_container_width=True,
        )
    next_config = {
        "backend": backend,
        "llm_model": llm_model,
        "codex_model": codex_model,
    }
    st.caption(
        _effective_action_caption(
            action_name,
            next_config,
            llm_default=llm_default,
            codex_default=codex_default,
        )
    )
    if test_clicked:
        _run_action_availability_test(
            action_name,
            next_config,
            llm_default=llm_default,
            codex_default=codex_default,
        )
    return next_config


def _legacy_ai_patch(actions: dict[str, dict[str, str]]) -> dict[str, object]:
    translation = actions.get("research.paper_translate", {})
    translation_backend = str(translation.get("backend") or "").strip()
    translation_model = (
        str(translation.get("codex_model") or "").strip()
        if translation_backend == "codex"
        else str(translation.get("llm_model") or "").strip()
    )
    deep_read = actions.get("research.paper_deep_read_codex", {})
    search = actions.get("research.paper_search_codex", {})
    deep_read_model = (
        str(deep_read.get("codex_model") or "").strip()
        or str(search.get("codex_model") or "").strip()
    )
    return {
        "paper": {
            "translation_backend": translation_backend,
            "translation_model": translation_model,
            "deep_read_model": deep_read_model,
        },
    }


def _action_label_map() -> dict[str, str]:
    labels: dict[str, str] = {}
    for _group_key, _group_label, rows in _AI_CONFIG_GROUPS:
        for action_name, label, _help_text in rows:
            labels[action_name] = label
    return labels


def _render_ai_config_panel() -> None:
    actions = _ai_action_prefs()
    llm_default = str(llm_client.current_config(mask_key=True).get("model") or "").strip()
    codex_cfg = codex_adapter.current_config(profile=selected)
    codex_default = str(codex_cfg.model or "").strip()
    llm_cfg = llm_client.current_config(mask_key=True)
    codex_status = codex_adapter.codex_status(
        replace(
            codex_cfg,
            timeout_seconds=min(float(codex_cfg.timeout_seconds or 8.0), 8.0),
        )
    )
    runtime_cols = st.columns(2)
    with runtime_cols[0]:
        st.caption(
            f"LLM: {'configured' if llm_cfg.get('configured') else 'missing key'} · "
            f"{llm_cfg.get('model') or _l('missing', 'missing')}"
        )
    with runtime_cols[1]:
        codex_bits = [
            "installed" if codex_status.installed else "missing",
            "logged in" if codex_status.logged_in else "login unknown",
            codex_cfg.model or _l("ai_config_codex_cli_default", "Codex CLI default"),
        ]
        st.caption("Codex: " + " · ".join(codex_bits))
        if codex_status.error:
            st.caption(codex_status.error)

    next_actions: dict[str, dict[str, str]] = {}
    with st.form(f"ai_config_form:{selected}", border=False):
        st.caption(
            _l(
                "ai_config_caption",
                "Choose the AI backend and model per feature. Leave fields on app default to follow the global sidebar/runtime configuration.",
            )
        )
        for group_key, group_label, rows in _AI_CONFIG_GROUPS:
            with st.expander(
                _l(f"ai_config_group_{group_key}", group_label),
                expanded=group_key == "paper",
            ):
                for action_name, label, help_text in rows:
                    next_actions[action_name] = _render_action_config_row(
                        action_name,
                        _l(f"ai_config_label_{action_name}", label),
                        _l(f"ai_config_help_{action_name}", help_text),
                        actions.get(action_name, {}),
                        llm_default=llm_default,
                        codex_default=codex_default,
                    )
        if st.form_submit_button(_l("save", "Save"), type="primary", use_container_width=True):
            legacy_patch = _legacy_ai_patch(next_actions)
            update_web_preferences(
                selected,
                {
                    "ai": {
                        "actions": next_actions,
                        **legacy_patch,
                    }
                },
            )
            st.success(_l("ai_config_saved", "AI preferences saved."))
            st.rerun()


def _render_research_help() -> None:
    st.markdown(_l("research_help_body", ""))


def _status_label(status: str) -> str:
    return ui.get(f"status_{status}", status)


def _save_sources(inbox, message: str) -> None:
    assert_files_current([_sources_path])
    save_research_sources(selected, inbox)
    refresh_file_snapshots([_sources_path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(message)


def _accept_latest_sources_for_additive_write() -> None:
    """Let additive imports proceed after passive Reader progress writes."""
    refresh_file_snapshots([_sources_path])


def _prepare_reader_artifacts_for_sources(source_ids: list[str]) -> dict[str, object]:
    prepared: list[str] = []
    warnings: list[str] = []
    refreshed = load_research_sources(selected).by_id()
    for source_id in source_ids:
        source = refreshed.get(source_id)
        if source is None or not (source.metadata or {}).get("pdf_asset_ref"):
            continue
        try:
            ensure_paper_reading_artifacts(_pdir, source_id, prefer_grobid=True)
            prepared.append(source_id)
        except Exception as exc:
            warnings.append(f"{source_id}: {exc}")
    if prepared:
        refresh_file_snapshots([_sources_path])
        stash_git_backup_results()
        clear_web_cache()
    return {"prepared": prepared, "warnings": warnings}


def _render_source_form(inbox, *, source=None, prefix: str) -> None:
    existing = source
    with st.form(prefix):
        source_id = st.text_input(
            ui["source_id"],
            value=getattr(existing, "id", ""),
            disabled=existing is not None,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            current_kind = getattr(existing, "kind", "web")
            kind = st.selectbox(
                ui["kind"],
                SOURCE_KINDS,
                index=SOURCE_KINDS.index(current_kind)
                if current_kind in SOURCE_KINDS
                else 0,
            )
        with c2:
            current_status = getattr(existing, "status", "inbox")
            status = st.selectbox(
                ui["status"],
                SOURCE_STATUSES,
                index=SOURCE_STATUSES.index(current_status)
                if current_status in SOURCE_STATUSES
                else 0,
                format_func=_status_label,
            )
        with c3:
            current_visibility = getattr(existing, "visibility", "private")
            visibility = st.selectbox(
                ui["visibility"],
                SOURCE_VISIBILITIES,
                index=SOURCE_VISIBILITIES.index(current_visibility)
                if current_visibility in SOURCE_VISIBILITIES
                else 0,
            )
        title = st.text_input(
            ui["title_label"],
            value=getattr(existing, "title", ""),
        )
        url = st.text_input(ui["url"], value=getattr(existing, "url", ""))
        c4, c5 = st.columns(2)
        with c4:
            authors = st.text_input(
                ui["authors"],
                value=_tags_text(getattr(existing, "authors", [])),
            )
        with c5:
            published = st.text_input(
                ui["published"],
                value=getattr(existing, "published", ""),
            )
        tags = st.text_input(
            ui["tags"],
            value=_tags_text(getattr(existing, "tags", [])),
        )
        c6, c7, c8 = st.columns(3)
        with c6:
            goal_refs = st.text_area(
                ui["goal_refs"],
                value=_lines_text(getattr(existing, "goal_refs", [])),
                height=70,
            )
        with c7:
            project_refs = st.text_area(
                ui["project_refs"],
                value=_lines_text(getattr(existing, "project_refs", [])),
                height=70,
            )
        with c8:
            experience_refs = st.text_area(
                ui["experience_refs"],
                value=_lines_text(getattr(existing, "experience_refs", [])),
                height=70,
            )
        library_node_refs = st.text_area(
            _l("library_node_refs", "Library node refs"),
            value=_lines_text(getattr(existing, "library_node_refs", [])),
            height=70,
        )
        summary = st.text_area(
            ui["summary"],
            value=getattr(existing, "summary", ""),
            height=90,
        )
        notes = st.text_area(
            ui["notes"],
            value=getattr(existing, "notes", ""),
            height=90,
        )
        submitted = st.form_submit_button(
            ui["save"] if existing is not None else ui["create"],
            type="primary",
        )
    if not submitted:
        return
    try:
        if existing is None:
            item = add_research_source(
                inbox,
                title,
                source_id=source_id,
                kind=kind,
                url=url,
                status=status,
                authors=_tags(authors),
                published=published,
                tags=_tags(tags),
                goal_refs=_text_lines(goal_refs),
                project_refs=_text_lines(project_refs),
                experience_refs=_text_lines(experience_refs),
                library_node_refs=_text_lines(library_node_refs),
                summary=summary,
                notes=notes,
                visibility=visibility,
                origin="manual",
            )
            _save_sources(inbox, ui["created"].format(id=item.id))
        else:
            update_research_source(
                inbox,
                existing.id,
                title=title,
                kind=kind,
                url=url,
                status=status,
                authors=_tags(authors),
                published=published,
                tags=_tags(tags),
                goal_refs=_text_lines(goal_refs),
                project_refs=_text_lines(project_refs),
                experience_refs=_text_lines(experience_refs),
                library_node_refs=_text_lines(library_node_refs),
                summary=summary,
                notes=notes,
                visibility=visibility,
            )
            _save_sources(inbox, ui["saved"])
    except ValueError as exc:
        st.error(str(exc))
        return
    st.rerun()


def _render_source_queue(inbox) -> None:
    st.subheader(ui["source_queue"])
    for status in SOURCE_STATUSES:
        sources = [source for source in inbox.sources if source.status == status]
        with st.expander(
            f"{_status_label(status)} · {len(sources)}",
            expanded=status in {"inbox", "reading"} and bool(sources),
        ):
            if not sources:
                st.caption(ui["empty_status"])
                continue
            for source in sources:
                with st.container(border=True):
                    st.markdown(f"**{source.title or source.id}**")
                    st.caption(f"`{source.id}`")
                    if source.url:
                        st.caption(source.url)
                    if source.summary:
                        st.caption(source.summary)
                    _render_source_form(
                        inbox,
                        source=source,
                        prefix=f"research_source_edit_{selected}_{source.id}",
                    )


def _render_candidate_preview(inbox) -> None:
    st.subheader(ui["candidate_preview"])
    st.caption(ui["candidate_preview_help"])
    if not inbox.sources:
        st.caption(ui["empty_status"])
        return
    source_id = st.selectbox(
        ui["source_id"],
        options=[source.id for source in inbox.sources],
        format_func=lambda sid: next(
            (
                source.title or source.id
                for source in inbox.sources
                if source.id == sid
            ),
            sid,
        ),
    )
    source = inbox.by_id().get(source_id)
    if source is None:
        return
    draft = {
        "source": source.id,
        "title": source.title,
        "summary": source.summary or source.notes,
        "source_refs": [source.id],
        "draft": True,
    }
    st.code(
        yaml.dump(
            draft,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ),
        language="yaml",
    )


def _render_research_overview_styles() -> None:
    st.markdown(
        """
<style>
:root {
  --ro-ink: #12201d;
  --ro-muted: #435854;
  --ro-subtle: #647571;
  --ro-line: #c8d4cf;
  --ro-paper: #ffffff;
  --ro-soft: #f6f8f7;
  --ro-accent: #176b5c;
  --ro-accent-strong: #0f4f43;
  --ro-accent-soft: #ddf2ec;
  --ro-risk-soft: #fff4d8;
  --ro-risk-line: rgba(146, 64, 14, .38);
}
div[data-testid="stPopover"] button {
  min-width: 4.2rem;
}
div[data-testid="stPopover"] button p {
  white-space: nowrap;
}
div[data-testid="stButton"] button:disabled {
  opacity: 1;
  border-color: #d6dfdb;
  background: #f7f9f8;
  color: #657672;
}
div[data-testid="stButton"] button:disabled p {
  color: #657672;
}
.ro-command-strip {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, .9fr);
  gap: 12px;
  align-items: stretch;
  margin: 0 0 14px;
}
.ro-command-main,
.ro-safety-panel,
.ro-panel,
.ro-card {
  border: 1px solid var(--ro-line);
  border-radius: 8px;
  background: var(--ro-paper);
}
.ro-command-main,
.ro-safety-panel,
.ro-panel {
  padding: 13px 15px;
}
.ro-kicker {
  color: var(--ro-subtle);
  font-size: .74rem;
  font-weight: 820;
  text-transform: uppercase;
}
.ro-title {
  margin: 3px 0 6px;
  color: var(--ro-ink);
  font-size: 1.28rem;
  font-weight: 860;
  line-height: 1.2;
}
.ro-copy {
  margin: 0;
  color: var(--ro-muted);
  font-size: .86rem;
  line-height: 1.45;
}
.ro-flow {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 12px;
}
.ro-stage {
  min-width: 0;
  padding: 9px 10px;
  border: 1px solid var(--ro-line);
  border-radius: 8px;
  background: var(--ro-soft);
}
.ro-stage.is-hot {
  border-color: rgba(33, 104, 91, .35);
  background: var(--ro-accent-soft);
}
.ro-stage.is-warn {
  border-color: var(--ro-risk-line);
  background: var(--ro-risk-soft);
}
.ro-stage-label {
  overflow: hidden;
  color: var(--ro-subtle);
  font-size: .7rem;
  font-weight: 820;
  text-overflow: ellipsis;
  text-transform: uppercase;
  white-space: nowrap;
}
.ro-stage-value {
  margin-top: 4px;
  color: var(--ro-ink);
  font-size: 1.38rem;
  font-weight: 860;
  line-height: 1;
}
.ro-stage-note {
  min-height: 27px;
  margin-top: 6px;
  color: var(--ro-muted);
  font-size: .74rem;
  line-height: 1.25;
}
.ro-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin: 2px 0 9px;
  color: var(--ro-ink);
  font-size: .98rem;
  font-weight: 850;
}
.ro-section-title small {
  color: var(--ro-subtle);
  font-size: .74rem;
  font-weight: 730;
}
.ro-queue-grid,
.ro-queue-tiles {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.ro-queue-chip {
  min-width: 0;
  padding: 9px 10px;
  border: 1px solid var(--ro-line);
  border-radius: 8px;
  background: var(--ro-soft);
}
.ro-queue-chip.is-live {
  border-color: rgba(33, 104, 91, .28);
  background: #f3faf7;
}
.ro-queue-chip.is-risk {
  border-color: var(--ro-risk-line);
  background: var(--ro-risk-soft);
}
.ro-queue-chip strong {
  display: block;
  overflow: hidden;
  color: var(--ro-ink);
  font-size: .84rem;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ro-queue-chip span {
  display: block;
  margin-top: 5px;
  color: var(--ro-muted);
  font-size: .77rem;
}
.ro-queue-tile {
  display: grid;
  min-width: 0;
  min-height: 82px;
  padding: 10px 11px;
  border: 1px solid var(--ro-line);
  border-radius: 8px;
  background: var(--ro-paper);
  color: var(--ro-ink) !important;
  gap: 5px;
  text-decoration: none !important;
}
.ro-queue-tile:hover {
  border-color: rgba(23, 107, 92, .42);
  background: #f3faf7;
}
.ro-queue-tile.is-live {
  border-color: rgba(23, 107, 92, .36);
  background: #f3faf7;
}
.ro-queue-tile.is-risk {
  border-color: var(--ro-risk-line);
  background: var(--ro-risk-soft);
}
.ro-queue-tile.is-disabled {
  background: #f7f9f8;
  color: #586a66 !important;
  cursor: default;
}
.ro-queue-tile-title {
  overflow: hidden;
  color: inherit;
  font-size: .85rem;
  font-weight: 830;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ro-queue-tile-count {
  color: var(--ro-ink);
  font-size: 1.1rem;
  font-weight: 860;
  line-height: 1.05;
}
.ro-queue-tile-caption,
.ro-queue-tile-action {
  color: var(--ro-muted);
  font-size: .76rem;
  line-height: 1.25;
}
.ro-queue-tile-action {
  font-weight: 760;
}
.ro-queue-tile.is-disabled .ro-queue-tile-count,
.ro-queue-tile.is-disabled .ro-queue-tile-caption,
.ro-queue-tile.is-disabled .ro-queue-tile-action {
  color: #657672;
}
.ro-action,
.ro-card {
  display: grid;
  gap: 7px;
  margin-bottom: 9px;
}
.ro-action {
  padding: 0;
  margin-bottom: 6px;
  background: transparent;
}
.ro-card {
  padding: 11px 12px;
}
.ro-card-title {
  color: var(--ro-ink);
  font-size: .94rem;
  font-weight: 850;
  line-height: 1.35;
}
.ro-card-meta {
  color: var(--ro-muted);
  font-size: .78rem;
  line-height: 1.35;
  overflow-wrap: anywhere;
}
.ro-card-body {
  color: #2f403c;
  font-size: .84rem;
  line-height: 1.45;
}
.ro-badge {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  min-height: 20px;
  padding: 1px 7px;
  margin: 0 4px 4px 0;
  border: 1px solid rgba(49, 51, 63, .14);
  border-radius: 999px;
  background: rgba(49, 51, 63, .055);
  color: rgba(31, 41, 55, .86);
  font-size: .72rem;
  font-weight: 760;
  line-height: 1.25;
}
.ro-badge-ok {
  border-color: rgba(22, 163, 74, .22);
  background: rgba(22, 163, 74, .09);
  color: rgb(22, 101, 52);
}
.ro-badge-warn {
  border-color: rgba(245, 158, 11, .32);
  background: rgba(245, 158, 11, .12);
  color: rgb(146, 64, 14);
}
.ro-badge-alert {
  border-color: rgba(220, 38, 38, .24);
  background: rgba(220, 38, 38, .08);
  color: rgb(153, 27, 27);
}
.ro-empty {
  padding: 12px;
  border: 1px dashed var(--ro-line);
  border-radius: 8px;
  background: var(--ro-soft);
  color: var(--ro-muted);
  font-size: .86rem;
  line-height: 1.45;
}
.ro-empty strong {
  color: var(--ro-ink);
}
@media (max-width: 980px) {
  .ro-command-strip { grid-template-columns: minmax(0, 1fr); }
  .ro-flow { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ro-queue-grid,
  .ro-queue-tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 520px) {
  .ro-flow,
  .ro-queue-grid,
  .ro-queue-tiles { grid-template-columns: minmax(0, 1fr); }
}
</style>
""",
        unsafe_allow_html=True,
    )


def _overview_notice_key() -> str:
    return f"research_overview_notice:{selected}"


def _set_overview_notice(message: str) -> None:
    st.session_state[_overview_notice_key()] = str(message or "")


def _pop_overview_notice() -> str:
    return str(st.session_state.pop(_overview_notice_key(), "") or "")


def _overview_badge(label: object, tone: str = "neutral") -> str:
    clean = html.escape(str(label or "").strip())
    if not clean:
        return ""
    safe_tone = tone if tone in {"neutral", "ok", "warn", "alert"} else "neutral"
    return f'<span class="ro-badge ro-badge-{safe_tone}">{clean}</span>'


def _overview_badge_tone(label: object) -> str:
    text = str(label or "").casefold()
    if any(part in text for part in ("missing", "broken", "failed", "private", "risk", "缺失", "断裂", "失败", "私有", "风险")):
        return "alert"
    if any(part in text for part in ("warning", "stale", "duplicate", "needs", "警告", "过期", "重复", "需要")):
        return "warn"
    if any(part in text for part in ("ready", "pdf", "promoted", "reviewed", "就绪", "已推进", "已审阅")):
        return "ok"
    return "neutral"


def _overview_localized_badge(label: object) -> str:
    text = str(label or "").strip()
    if not text:
        return ""
    mapping = {
        "Unsorted": _l("badge_unsorted", "Unsorted"),
        "PDF ready": _l("badge_pdf_ready", "PDF ready"),
        "PDF missing": _l("pdf_missing", "PDF missing"),
        "Stale translation": _l("badge_stale_translation", "Stale translation"),
        "Private source": _l("badge_private_source", "Private source"),
        "Needs structured extraction": _l("badge_needs_structured_extraction", "Needs structured extraction"),
        "GROBID unavailable": _l("badge_grobid_unavailable", "GROBID unavailable"),
        "Fallback extraction": _l("badge_fallback_extraction", "Fallback extraction"),
        "Duplicate risk": _l("duplicate_risk", "Duplicate risk"),
        "AI candidates": _l("ai_candidates", "AI candidates"),
        "ready": _l("ready", "Ready"),
        "risk": _l("risk", "Risk"),
    }
    return mapping.get(text, text)


def _overview_badges(labels: list[object], *, limit: int = 5) -> str:
    clean_labels = [label for label in labels if str(label or "").strip()]
    rendered = [
        _overview_badge(_overview_localized_badge(label), _overview_badge_tone(label))
        for label in clean_labels[:limit]
    ]
    if len(clean_labels) > limit:
        rendered.append(_overview_badge(f"+{len(clean_labels) - limit}"))
    return " ".join(item for item in rendered if item)


def _overview_stage(label: str, value: object, note: str = "", tone: str = "") -> str:
    classes = ["ro-stage"]
    if tone:
        classes.append(f"is-{tone}")
    return (
        f'<div class="{" ".join(classes)}">'
        f'<div class="ro-stage-label">{html.escape(label)}</div>'
        f'<div class="ro-stage-value">{html.escape(str(value))}</div>'
        f'<div class="ro-stage-note">{html.escape(note)}</div>'
        "</div>"
    )


def _overview_queue_chip(label: str, count: object, detail: str = "", tone: str = "") -> str:
    classes = ["ro-queue-chip"]
    if tone:
        classes.append(f"is-{tone}")
    suffix = f" · {detail}" if detail else ""
    return (
        f'<div class="{" ".join(classes)}">'
        f"<strong>{html.escape(label)}</strong>"
        f"<span>{html.escape(str(count))}{html.escape(suffix)}</span>"
        "</div>"
    )


def _overview_queue_tile(
    *,
    label: str,
    count: int,
    caption: str,
    action: str,
    url: str,
    tone: str = "",
    view: str = "",
    disabled: bool = False,
) -> str:
    classes = ["ro-queue-tile"]
    if tone:
        classes.append(f"is-{tone}")
    if count <= 0 or disabled:
        classes.append("is-disabled")
    tag = "a" if count > 0 and url and not disabled else "div"
    href = f' href="{html.escape(url, quote=True)}" rel="noopener noreferrer"' if tag == "a" else ""
    data_view = html.escape(view or "", quote=True)
    return (
        f'<{tag} class="{" ".join(classes)}" data-overview-queue="{data_view}"{href}>'
        f'<div class="ro-queue-tile-title">{html.escape(label)}</div>'
        f'<div class="ro-queue-tile-count">{html.escape(str(count))}</div>'
        f'<div class="ro-queue-tile-caption">{html.escape(caption)}</div>'
        f'<div class="ro-queue-tile-action">{html.escape(action)}</div>'
        f"</{tag}>"
    )


def _overview_card_html(
    title: object,
    meta: object = "",
    body: object = "",
    badges: list[object] | None = None,
    *,
    action: bool = False,
) -> str:
    cls = "ro-action" if action else "ro-card"
    parts = [f'<div class="{cls}">']
    parts.append(f'<div class="ro-card-title">{html.escape(str(title or ""))}</div>')
    if meta:
        parts.append(f'<div class="ro-card-meta">{html.escape(str(meta))}</div>')
    if body:
        parts.append(f'<div class="ro-card-body">{html.escape(_short_text(body, 260))}</div>')
    if badges:
        parts.append(f"<div>{_overview_badges(list(badges))}</div>")
    parts.append("</div>")
    return "".join(parts)


def _overview_status_label(status: object) -> str:
    clean = str(status or "").strip()
    if not clean:
        return ""
    return _l(f"status_{clean}", clean.replace("_", " ").title())


def _overview_action_label(action: dict[str, object]) -> str:
    kind = str(action.get("kind") or "")
    source_count = len(action.get("source_refs") or [])
    claim_count = len(action.get("claim_refs") or [])
    citation_count = len(action.get("citation_refs") or [])
    draft_count = len(action.get("draft_refs") or [])
    action_count = action.get("count")
    if isinstance(action_count, int):
        source_count = claim_count = citation_count = draft_count = action_count
    if kind == "continue_reading":
        return _l("overview_action_continue_reading", "Continue reading {count} source(s)").format(count=source_count)
    if kind == "review_claims":
        return _l("overview_action_review_claims", "Review {count} ready research claim(s)").format(count=claim_count)
    if kind == "fix_citations":
        return _l("overview_action_fix_citations", "Fix {count} citation warning(s)").format(count=citation_count)
    if kind == "review_private_publish_risk":
        return _l("overview_action_private_risk", "Review {count} private source risk(s)").format(count=source_count)
    if kind == "review_drafts":
        return _l("overview_action_review_drafts", "Review {count} synthesis draft(s)").format(count=draft_count)
    if kind == "import_sources":
        return _l("overview_action_import_sources", "Import papers, repos, or web sources")
    return str(action.get("label") or kind or _l("next_action", "Next action"))


def _overview_risk_label(kind: object) -> str:
    clean = str(kind or "risk").strip()
    mapping = {
        "private_publish_risk": _l("risk_private_publish", "Private publish risk"),
        "broken_citations": _l("risk_broken_citations", "Broken citations"),
    }
    return mapping.get(clean, clean.replace("_", " ").title())


def _overview_risk_action_label(action: object) -> str:
    clean = str(action or "").strip()
    mapping = {
        "open_export_gate": _l("risk_open_export_gate", "Open export gate"),
        "open_citation_inspector": _l("risk_open_citation_inspector", "Open citation inspector"),
    }
    return mapping.get(clean, clean.replace("_", " ").title())


def _focus_paper_library_view(view: str, *, detail_id: str = "", node_id: str = "") -> None:
    st.session_state[_paper_library_key("view")] = view or "all"
    st.session_state[_paper_library_key("node")] = node_id
    if detail_id:
        st.session_state[_paper_library_key("detail")] = detail_id
    else:
        st.session_state.pop(_paper_library_key("detail"), None)


def _focus_claim_review(*, source_id: str = "", status: str = "", queue: str = "") -> None:
    if source_id:
        st.session_state[f"research_cc_source:{selected}"] = source_id
    st.session_state[f"research_claim_status_filter:{selected}"] = status
    st.session_state[f"research_claim_queue_filter:{selected}"] = queue


def _first_source_ref(action: dict[str, object], source_ids: set[str]) -> str:
    for ref in action.get("source_refs") or []:
        clean = str(ref or "").strip()
        if clean in source_ids:
            return clean
    return ""


def _render_overview_action_card(
    action: dict[str, object],
    *,
    source_ids: set[str],
    row_by_id: dict[str, dict[str, object]],
) -> None:
    kind = str(action.get("kind") or "")
    label = _overview_action_label(action)
    source_ref = _first_source_ref(action, source_ids)
    meta_bits = []
    if source_ref:
        meta_bits.append(source_ref)
    if action.get("claim_refs"):
        meta_bits.append(f"{ui['research_claims']}: {len(action.get('claim_refs') or [])}")
    if action.get("citation_refs"):
        meta_bits.append(f"{ui['research_citations']}: {len(action.get('citation_refs') or [])}")
    if action.get("draft_refs"):
        meta_bits.append(f"{ui['synthesis_drafts']}: {len(action.get('draft_refs') or [])}")
    target = action.get("target") if isinstance(action.get("target"), dict) else {}
    secondary_targets = [item for item in action.get("secondary_targets") or [] if isinstance(item, dict)]
    paper_target = next(
        (item for item in secondary_targets if str(item.get("surface") or "") == "paper_library"),
        target if str(target.get("surface") or "") == "paper_library" else {},
    )
    paper_url = _paper_library_target_url(paper_target, fallback_detail_id=source_ref)

    with st.container(border=True):
        st.markdown(
            _overview_card_html(label, " · ".join(meta_bits), action=True),
            unsafe_allow_html=True,
        )
        b1, b2, b3 = st.columns(3)
        if kind == "continue_reading":
            row = row_by_id.get(source_ref, {})
            with b1:
                if row.get("has_pdf") and source_ref:
                    _render_sidecar_link_button(
                        _l("open_reader", "Open Reader"),
                        _reader_view_url(source_ref),
                        key=f"overview_reader_link:{selected}:{source_ref}",
                        icon=":material/menu_book:",
                        type="primary",
                        use_container_width=True,
                    )
                else:
                    st.button(
                        _l("open_reader", "Open Reader"),
                        disabled=True,
                        key=f"overview_reader_link_disabled:{selected}:{source_ref}",
                        icon=":material/menu_book:",
                        use_container_width=True,
                    )
            with b2:
                _render_sidecar_link_button(
                    _l("open_in_paper_library", "Open in Library"),
                    paper_url or _paper_library_workspace_url(detail_id=source_ref, return_to="overview"),
                    key=f"overview_open_library:{selected}:{kind}:{source_ref}",
                    icon=":material/library_books:",
                    use_container_width=True,
                )
        elif kind == "review_claims":
            with b1:
                if st.button(
                    _l("focus_ready_claims", "Focus ready claims"),
                    key=f"overview_focus_ready_claims:{selected}",
                    icon=":material/rule:",
                    type="primary",
                    use_container_width=True,
                ):
                    _focus_claim_review(source_id=source_ref, status="ready", queue="ready")
                    _set_overview_notice(_l("claims_focus_saved", "Claims review is focused on ready claims."))
                    st.rerun()
            with b2:
                _render_sidecar_link_button(
                    _l("open_source_library", "Open source"),
                    paper_url or (
                        _paper_library_workspace_url(
                            view="claims_need_review",
                            detail_id=source_ref,
                            focus="claims",
                            action="review_claims",
                            return_to="overview",
                        )
                    ),
                    key=f"overview_review_claims_source:{selected}:{source_ref}",
                    icon=":material/library_books:",
                    use_container_width=True,
                )
        elif kind == "fix_citations":
            with b1:
                if st.button(
                    _l("focus_quote_warnings", "Focus quote warnings"),
                    key=f"overview_focus_quote_warning:{selected}",
                    icon=":material/plagiarism:",
                    type="primary",
                    use_container_width=True,
                ):
                    _focus_claim_review(source_id=source_ref, queue="quote_warning")
                    _set_overview_notice(_l("citations_focus_saved", "Citation inspector is focused on quote warnings."))
                    st.rerun()
            with b2:
                _render_sidecar_link_button(
                    _l("open_source_library", "Open source"),
                    paper_url or _paper_library_workspace_url(
                        detail_id=source_ref,
                        focus="claims",
                        action="fix_citations",
                        return_to="overview",
                    ),
                    key=f"overview_fix_citations_source:{selected}:{source_ref}",
                    icon=":material/library_books:",
                    use_container_width=True,
                )
        elif kind in {"review_private_publish_risk", "review_drafts"}:
            with b1:
                if st.button(
                    _l("focus_export_gate", "Focus export gate"),
                    key=f"overview_focus_export:{selected}:{kind}",
                    icon=":material/policy:",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state[f"research_export_focus:{selected}"] = kind
                    _set_overview_notice(_l("export_focus_saved", "Export gate focus updated."))
                    st.rerun()
            with b2:
                _render_sidecar_link_button(
                    _l("open_paper_library_workspace", "Open Paper Library"),
                    paper_url or _paper_library_workspace_url(
                        detail_id=source_ref,
                        focus="safety",
                        action="review_visibility",
                        return_to="overview",
                    ),
                    key=f"overview_export_library:{selected}:{kind}:{source_ref}",
                    icon=":material/library_books:",
                    use_container_width=True,
                )
        elif kind == "import_sources":
            with b1:
                _render_sidecar_link_button(
                    _l("open_paper_library_workspace", "Open Paper Library"),
                    paper_url or _paper_library_workspace_url(view="unsorted", return_to="overview"),
                    key=f"overview_import_sources_library:{selected}",
                    icon=":material/library_books:",
                    type="primary",
                    use_container_width=True,
                )
            with b2:
                if st.button(
                    _l("focus_connector_inbox", "Connector inbox"),
                    key=f"overview_focus_connectors:{selected}",
                    icon=":material/hub:",
                    use_container_width=True,
                ):
                    st.session_state[f"research_advanced_focus:{selected}"] = "connectors"
                    _set_overview_notice(_l("connector_focus_saved", "Connector inbox focus updated."))
                    st.rerun()


def _render_workspace_overview(inbox) -> None:
    _render_research_overview_styles()
    overview = paper_overview(_pdir)
    command = build_research_overview_payload(_pdir)
    connector_rows = list(load_connectors(_pdir).get("connectors") or [])
    enabled_connectors = [row for row in connector_rows if bool(row.get("enabled", True))]
    all_paper_rows = paper_rows(_pdir, view="all")
    row_by_id = {str(row.get("id") or ""): row for row in all_paper_rows}
    source_ids = {source.id for source in inbox.sources}
    funnel = command.get("funnel_counts") or {}
    action_rows = list(command.get("next_actions") or [])
    risk_rows = list(command.get("risks") or [])

    notice = _pop_overview_notice()
    if notice:
        st.success(notice)

    private_public = f"{overview['private_sources']} / {overview['public_sources']}"
    safety_badges = [
        _overview_badge(f"{_l('private_public_sources', 'Private / public')}: {private_public}", "warn" if overview["private_sources"] else "neutral"),
        _overview_badge(f"{_l('citation_broken', 'Citation broken')}: {overview['citation_broken']}", "alert" if overview["citation_broken"] else "ok"),
        _overview_badge(f"{_l('private_publish_risk', 'Private publish risk')}: {overview['private_publish_risk']}", "alert" if overview["private_publish_risk"] else "ok"),
        _overview_badge(f"{_l('stale_translation_warning', 'Stale translations')}: {overview['stale_translation_warning']}", "warn" if overview["stale_translation_warning"] else "ok"),
    ]
    st.markdown(
        "".join(
            [
                '<div class="ro-command-strip">',
                '<div class="ro-command-main">',
                f'<div class="ro-kicker">{html.escape(_l("research_workspace", "Research Workspace"))}</div>',
                f'<div class="ro-title">{html.escape(_l("research_command_center", "Research Command Center"))}</div>',
                f'<p class="ro-copy">{html.escape(_l("research_command_center_caption", "Sources, reading state, review queues, and export safety in one workspace."))}</p>',
                '<div class="ro-flow">',
                _overview_stage(_l("research_sources", "Sources"), funnel.get("sources", 0), _l("source_inbox", "Source Inbox")),
                _overview_stage(_l("papers_reading", "Reading"), funnel.get("reading", 0), _l("reader", "Reader"), "hot" if funnel.get("reading") else ""),
                _overview_stage(_l("extracted", "Extracted"), overview["annotated"], _l("chunks_annotations", "Chunks / annotations")),
                _overview_stage(_l("claims_ready", "Claims ready"), funnel.get("claims_ready", 0), _l("review_queue", "Review queue"), "hot" if funnel.get("claims_ready") else ""),
                _overview_stage(
                    _l("citations", "Citations"),
                    funnel.get("citations", 0),
                    _l("warnings_count", "{count} warnings").format(count=overview["citation_broken"]),
                    "warn" if overview["citation_broken"] else "",
                ),
                _overview_stage(_l("synthesis_drafts", "Drafts"), funnel.get("drafts", 0), _l("synthesis_export", "Synthesis / Export")),
                "</div>",
                "</div>",
                '<div class="ro-safety-panel">',
                f'<div class="ro-section-title">{html.escape(_l("integrity_publish_safety", "Integrity & Publish Safety"))}</div>',
                "<div>",
                " ".join(safety_badges),
                "</div>",
                f'<p class="ro-copy">{html.escape(ui["claim_boundary_hint"])}</p>',
                "</div>",
                "</div>",
            ]
        ),
        unsafe_allow_html=True,
    )

    q_reading = _library_view_count(all_paper_rows, "reading")
    q_missing_pdf = _library_view_count(all_paper_rows, "no_pdf")
    q_needs_extraction = _library_view_count(all_paper_rows, "needs_extraction")
    q_claims_need_review = _library_view_count(all_paper_rows, "claims_need_review")
    q_duplicate = _library_view_count(all_paper_rows, "duplicate_risk")
    q_stale = _library_view_count(all_paper_rows, "stale_translation")
    q_private = _library_view_count(all_paper_rows, "private")
    q_recent = _library_view_count(all_paper_rows, "recent")
    queue_fallback = {
        "reading": {
            "label": _l("reading", "Reading"),
            "count": q_reading,
            "caption": _l("reader", "Reader"),
            "action": _l("overview_queue_continue_reading", "Continue reading"),
            "tone": "live" if q_reading else "",
        },
        "needs_extraction": {
            "label": _l("needs_extraction", "Needs extraction"),
            "count": q_needs_extraction,
            "caption": _l("parser_status", "Parser status"),
            "action": _l("overview_queue_run_extraction", "Run extraction"),
            "tone": "risk" if q_needs_extraction else "",
        },
        "no_pdf": {
            "label": _l("pdf_missing", "PDF missing"),
            "count": q_missing_pdf,
            "caption": _l("paper_library", "Paper Library"),
            "action": _l("overview_queue_attach_pdf", "Attach PDF"),
            "tone": "risk" if q_missing_pdf else "",
        },
        "claims_need_review": {
            "label": _l("claims_need_review", "Claims review"),
            "count": q_claims_need_review,
            "caption": _l("ai_candidates", "AI candidates"),
            "action": _l("overview_queue_review_candidates", "Review candidates"),
            "tone": "live" if q_claims_need_review else "",
        },
        "duplicate_risk": {
            "label": _l("duplicate_risk", "Duplicate risk"),
            "count": q_duplicate,
            "caption": _l("metadata_review", "Metadata review"),
            "action": _l("overview_queue_deduplicate", "Deduplicate"),
            "tone": "risk" if q_duplicate else "",
        },
        "stale_translation": {
            "label": _l("stale_translation_warning", "Stale translations"),
            "count": q_stale,
            "caption": _l("translation", "Translation"),
            "action": _l("overview_queue_refresh_translations", "Refresh translations"),
            "tone": "risk" if q_stale else "",
        },
        "private": {
            "label": _l("private_sources", "Private sources"),
            "count": q_private,
            "caption": _l("visibility", "Visibility"),
            "action": _l("overview_queue_review_visibility", "Review visibility"),
            "tone": "risk" if q_private else "",
        },
        "recent": {
            "label": _l("recent_papers", "Recent"),
            "count": q_recent,
            "caption": _l("paper_library", "Paper Library"),
            "action": _l("overview_queue_open_recent", "Open recent"),
            "tone": "live" if q_recent else "",
        },
    }
    queue_rows = []
    for row in command.get("work_queues") or []:
        if not isinstance(row, dict):
            continue
        view = str(row.get("id") or "")
        fallback = queue_fallback.get(view, {})
        queue_rows.append(
            {
                "label": str(fallback.get("label") or row.get("label") or view),
                "view": view,
                "count": int(row.get("count") or fallback.get("count") or 0),
                "caption": str(fallback.get("caption") or row.get("caption") or ""),
                "action": str(fallback.get("action") or _l("open_in_paper_library", "Open in Library")),
                "tone": str(fallback.get("tone") or row.get("severity") or ""),
                "target": row.get("target") if isinstance(row.get("target"), dict) else {},
            }
        )
    if not queue_rows:
        queue_rows = [
            {"view": view, "target": {}, **values}
            for view, values in queue_fallback.items()
        ]
    sidecar_unavailable, _sidecar_message = _paper_library_sidecar_unavailable()
    queue_tiles = []
    for row in queue_rows:
        label = str(row.get("label") or "")
        view = str(row.get("view") or "")
        count = int(row.get("count") or 0)
        target = row.get("target") if isinstance(row.get("target"), dict) else {}
        target_url = _paper_library_target_url(target, fallback_detail_id="")
        queue_tiles.append(
            _overview_queue_tile(
                label=label,
                count=count,
                caption=str(row.get("caption") or ""),
                action=str(row.get("action") or ""),
                url=target_url or _paper_library_workspace_url(view=view, return_to="overview"),
                tone=str(row.get("tone") or ""),
                view=view,
                disabled=sidecar_unavailable,
            )
        )
    st.markdown(
        "".join(
            [
                '<div class="ro-panel">',
                f'<div class="ro-section-title">{html.escape(_l("work_queues", "Work queues"))}<small>{html.escape(_l("paper_library", "Paper Library"))} / {html.escape(ui["claims_citations"])}</small></div>',
                '<div class="ro-queue-tiles">',
                "".join(queue_tiles),
                "</div>",
                "</div>",
            ]
        ),
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1.05, 1.35, 1.1], gap="medium")
    with left:
        st.markdown(
            f'<div class="ro-section-title">{html.escape(_l("next_actions", "Next actions"))}<small>{len(action_rows)}</small></div>',
            unsafe_allow_html=True,
        )
        if action_rows:
            for action in action_rows[:5]:
                _render_overview_action_card(action, source_ids=source_ids, row_by_id=row_by_id)
        else:
            st.markdown(
                f'<div class="ro-empty">{html.escape(_l("no_research_actions", "No research actions need attention."))}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="ro-section-title">{html.escape(_l("discovery_updates", "Discovery updates"))}<small>{len(enabled_connectors)} {html.escape(ui["connectors_enabled"])}</small></div>',
            unsafe_allow_html=True,
        )
        provider_bits = []
        for provider in CONNECTOR_PROVIDERS:
            provider_rows = [row for row in connector_rows if str(row.get("provider") or "") == provider]
            last = max(provider_rows, key=lambda row: str(row.get("last_run") or ""), default={})
            last_result = last.get("last_result") if isinstance(last.get("last_result"), dict) else {}
            imported = int(last_result.get("imported") or 0)
            skipped = int(last_result.get("skipped") or 0)
            status = str(last.get("status") or "").strip()
            provider_bits.append(
                _overview_queue_chip(
                    provider,
                    _l("overview_imported_count", "{count} imported").format(count=imported),
                    (
                        _l("overview_skipped_count", "{count} skipped").format(count=skipped)
                        if skipped
                        else _l(f"connector_status_{status or 'idle'}", status or _l("connector_status_idle", "idle"))
                    ),
                    "live" if imported else "",
                )
            )
        st.markdown(
            '<div class="ro-queue-grid">' + "".join(provider_bits) + "</div>",
            unsafe_allow_html=True,
        )
        if st.button(
            _l("focus_connector_inbox", "Connector inbox"),
            key=f"overview_connectors_button:{selected}",
            icon=":material/hub:",
            use_container_width=True,
        ):
            st.session_state[f"research_advanced_focus:{selected}"] = "connectors"
            _set_overview_notice(_l("connector_focus_saved", "Connector inbox focus updated."))
            st.rerun()

    with center:
        st.markdown(
            f'<div class="ro-section-title">{html.escape(_l("recent_work", "Recent work"))}<small>{html.escape(_l("paper_library", "Paper Library"))}</small></div>',
            unsafe_allow_html=True,
        )
        recent = sorted(
            all_paper_rows,
            key=lambda row: str(row.get("last_read") or ""),
            reverse=True,
        )[:5]
        if recent:
            for row in recent:
                source_id = str(row.get("id") or "")
                meta = " · ".join(
                    str(part)
                    for part in [
                        _overview_status_label(row.get("status")),
                        row.get("tree_path"),
                        row.get("last_read"),
                    ]
                    if part
                )
                metrics = [
                    f"{_l('chunks', 'Chunks')}: {row.get('chunks_count', 0)}",
                    f"{ui['research_claims']}: {row.get('claims_count', 0)}",
                    f"{ui['research_citations']}: {row.get('citations_count', 0)}",
                ]
                st.markdown(
                    _overview_card_html(
                        row.get("title") or source_id,
                        meta,
                        " · ".join(metrics),
                        list(row.get("badges") or []),
                    ),
                    unsafe_allow_html=True,
                )
                actions = st.columns([1, 1, 1])
                with actions[0]:
                    if row.get("has_pdf"):
                        _render_sidecar_link_button(
                            _l("open_reader", "Open Reader"),
                            _reader_view_url(source_id),
                            key=f"overview_recent_reader:{selected}:{source_id}",
                            icon=":material/menu_book:",
                            use_container_width=True,
                        )
                    else:
                        st.button(
                            _l("open_reader", "Open Reader"),
                            key=f"overview_recent_reader_disabled:{selected}:{source_id}",
                            disabled=True,
                            icon=":material/menu_book:",
                            use_container_width=True,
                        )
                with actions[1]:
                    _render_sidecar_link_button(
                        _l("open_in_paper_library", "Open in Library"),
                        _paper_library_workspace_url(
                            detail_id=source_id,
                            focus="reading" if row.get("status") == "reading" else "metadata",
                            action="open_reader" if row.get("has_pdf") else "review_metadata",
                            return_to="overview",
                        ),
                        key=f"overview_recent_library:{selected}:{source_id}",
                        icon=":material/library_books:",
                        use_container_width=True,
                    )
                with actions[2]:
                    if st.button(
                        _l("focus_claims", "Claims"),
                        key=f"overview_recent_claims:{selected}:{source_id}",
                        disabled=not bool(row.get("claims_count") or row.get("citations_count")),
                        icon=":material/rule:",
                        use_container_width=True,
                    ):
                        _focus_claim_review(source_id=source_id)
                        _set_overview_notice(_l("claims_focus_saved", "Claims review focus updated."))
                        st.rerun()
        else:
            st.markdown(
                f'<div class="ro-empty">{html.escape(_l("recent_work_empty", "No recent paper reading yet."))}</div>',
                unsafe_allow_html=True,
            )

    with right:
        st.markdown(
            f'<div class="ro-section-title">{html.escape(_l("ready_to_review", "Ready to review"))}<small>{html.escape(ui["claims_citations"])}</small></div>',
            unsafe_allow_html=True,
        )
        claim_rows = load_research_claims(_pdir)
        ready_claims = [claim for claim in claim_rows if claim.status == "ready"]
        chunk_map = {chunk.id: chunk for chunk in load_chunks(_pdir)}
        if ready_claims:
            for claim in ready_claims[:4]:
                refs = []
                for ref in claim.source_refs:
                    if ref not in refs:
                        refs.append(ref)
                for chunk_ref in claim.chunk_refs:
                    chunk = chunk_map.get(chunk_ref)
                    if chunk is not None and chunk.source_id not in refs:
                        refs.append(chunk.source_id)
                st.markdown(
                    _overview_card_html(
                        claim.id,
                        " · ".join([claim.type, f"confidence={claim.confidence}", ", ".join(refs[:2])]),
                        claim.text,
                        ["ready", *claim.warnings[:2]],
                    ),
                    unsafe_allow_html=True,
                )
                if st.button(
                    _l("review_claim", "Review claim"),
                    key=f"overview_ready_claim:{selected}:{claim.id}",
                    icon=":material/rule:",
                    use_container_width=True,
                ):
                    _focus_claim_review(source_id=refs[0] if refs else "", status="ready", queue="ready")
                    _set_overview_notice(_l("claims_focus_saved", "Claims review is focused on ready claims."))
                    st.rerun()
            if len(ready_claims) > 4:
                st.caption(_l("more_claims_hidden", "{count} more claim(s) hidden by this compact view.").format(count=len(ready_claims) - 4))
        else:
            st.markdown(
                (
                    '<div class="ro-empty">'
                    f'<strong>{html.escape(_l("claims_empty", "No claims yet."))}</strong><br>'
                    f'{html.escape(_l("claims_empty_next_step", "Run extraction in Paper Library, then create claim candidates from the Reader."))}'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            seed_view = "needs_extraction" if q_needs_extraction else "all"
            seed_action = "run_extraction" if q_needs_extraction else "review_claims"
            if all_paper_rows:
                _render_sidecar_link_button(
                    _l("prepare_claim_candidates", "Prepare claim candidates"),
                    _paper_library_workspace_url(
                        view=seed_view,
                        focus="artifacts" if q_needs_extraction else "claims",
                        action=seed_action,
                        return_to="overview",
                    ),
                    key=f"overview_prepare_claim_candidates:{selected}:{seed_view}:{seed_action}",
                    icon=":material/auto_fix_high:",
                    use_container_width=True,
                )

        st.markdown(
            f'<div class="ro-section-title">{html.escape(_l("risk_queue", "Risk queue"))}<small>{len(risk_rows)}</small></div>',
            unsafe_allow_html=True,
        )
        if risk_rows:
            for risk in risk_rows:
                refs = [str(ref) for ref in risk.get("refs") or [] if str(ref)]
                st.markdown(
                    _overview_card_html(
                        _overview_risk_label(risk.get("kind") or "risk"),
                        ", ".join(refs[:4]),
                        _overview_risk_action_label(risk.get("action") or ""),
                        ["risk"],
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<div class="ro-empty">{html.escape(_l("risk_queue_empty", "No publish blockers in the current research queue."))}</div>',
                unsafe_allow_html=True,
            )
        if st.button(
            _l("focus_export_gate", "Focus export gate"),
            key=f"overview_export_gate_button:{selected}",
            icon=":material/policy:",
            disabled=not bool(risk_rows),
            use_container_width=True,
        ):
            st.session_state[f"research_export_focus:{selected}"] = "risk_queue"
            _set_overview_notice(_l("export_focus_saved", "Export gate focus updated."))
            st.rerun()


def _paper_sources(inbox) -> list:
    return [source for source in inbox.sources if source.kind == "paper"]


def _source_label(inbox, source_id: str) -> str:
    source = next((source for source in inbox.sources if source.id == source_id), None)
    if source is None:
        return source_id
    label = source.title or source.id
    duplicate_titles = sum(1 for row in inbox.sources if (row.title or row.id) == label)
    if duplicate_titles > 1:
        label = f"{label} · {source.id}"
    return label


def _node_options(*, include_unsorted: bool = True, include_trashed: bool = False) -> dict[str, str]:
    tree = load_paper_library_tree(_pdir)
    paths = paper_library_paths(_pdir)
    options: dict[str, str] = {}
    if include_unsorted:
        options[""] = _l("unsorted_inbox", "Unsorted Inbox")
    for node in sorted(tree.nodes, key=lambda item: (paths.get(item.id, item.title).lower(), item.order, item.id)):
        if node.status == "trashed" and not include_trashed:
            continue
        options[node.id] = paths.get(node.id, node.title)
    return options


def _node_select_index(options: dict[str, str], wanted: str) -> int:
    keys = list(options)
    clean = str(wanted or "").strip()
    return keys.index(clean) if clean in options else 0


_LIBRARY_VIEW_LABELS = {
    "all": "All Papers",
    "unsorted": "Unsorted Inbox",
    "reading": "Reading",
    "no_pdf": "PDF Missing",
    "needs_extraction": "Needs Extraction",
    "claims_need_review": "Claims Need Review",
    "duplicate_risk": "Duplicate Risk",
    "stale_translation": "Stale Translation",
    "recent": "Recently Read",
    "private": "Private Sources",
    "reviewed": "Reviewed",
    "archived": "Archived",
    "discarded": "Discarded",
}

_LIBRARY_VIEW_GROUPS = (
    ("library", "Library", ("all", "unsorted", "recent")),
    (
        "work_queue",
        "Work Queue",
        (
            "reading",
            "no_pdf",
            "needs_extraction",
            "claims_need_review",
            "duplicate_risk",
            "stale_translation",
        ),
    ),
    ("system", "System", ("private", "reviewed", "archived", "discarded")),
)

_TECHNICAL_TAXONOMY_LABELS = (
    ("topics", "Topics"),
    ("methods", "Methods"),
    ("datasets", "Datasets"),
    ("benchmarks", "Benchmarks"),
)


def _paper_library_key(name: str) -> str:
    return f"paper_library:{selected}:{name}"


def _sidecar_base_for_same_origin_mode() -> str:
    """Resolve ``NBLANE_READER_API_BASE=0`` into a browser-facing sidecar base."""

    try:
        current_url = str(getattr(st.context, "url", "") or "").strip()
    except Exception:
        current_url = ""
    if current_url:
        parsed = urlparse(current_url)
        host = (parsed.hostname or "").strip().lower()
        if parsed.scheme in {"http", "https"} and host in {"localhost", "127.0.0.1"}:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            sidecar_port = {8501: 8502, 8503: 8502, 18503: 18502}.get(port)
            if sidecar_port:
                return f"{parsed.scheme}://{parsed.hostname}:{sidecar_port}"
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return os.getenv("NBLANE_STREAMLIT_BASE_URL", "").strip().rstrip("/")


def _reader_api_base() -> str:
    """Return the sidecar base used for Paper Library and Reader links."""
    raw = (
        os.getenv("NBLANE_READER_API_BASE", "").strip()
        or os.getenv("NBLANE_PAPER_LIBRARY_BASE", "").strip()
        or "http://127.0.0.1:8502"
    )
    if raw.lower() in {"0", "false", "off", "none"}:
        return _sidecar_base_for_same_origin_mode()
    return raw.rstrip("/")


def _research_overview_url() -> str:
    """Return the browser-facing Research Overview URL for 8502 back links."""

    explicit = os.getenv("NBLANE_RESEARCH_OVERVIEW_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    try:
        current_url = str(getattr(st.context, "url", "") or "").strip()
    except Exception:
        current_url = ""
    if current_url:
        parsed = urlparse(current_url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            path = parsed.path if parsed.path.strip("/") else "/Research"
            return f"{parsed.scheme}://{parsed.netloc}{path}"
        if current_url.startswith("/") and not current_url.startswith("//"):
            return current_url.split("?", 1)[0].split("#", 1)[0] or "/Research"
    base = os.getenv("NBLANE_STREAMLIT_BASE_URL", "").strip().rstrip("/")
    if base:
        return f"{base}/Research"
    return "/Research"


def _reader_view_url(source_id: str) -> str:
    token = mint_reader_token(user.id, selected, source_id)
    base = _reader_api_base()
    encoded_source = quote(source_id, safe="")
    encoded_token = quote(token, safe="")
    path = f"/reader/view/{encoded_source}?token={encoded_token}"
    return f"{base}{path}" if base else path


def _paper_library_workspace_url(
    *,
    view: str = "",
    node_id: str = "",
    query: str = "",
    sort: str = "",
    detail_id: str = "",
    focus: str = "",
    action: str = "",
    return_to: str = "",
    return_url: str = "",
) -> str:
    base = _reader_api_base()
    params = {"profile": selected}
    clean_return_to = str(return_to or "").strip()
    clean_return_url = str(return_url or "").strip()
    if clean_return_to == "overview" and not clean_return_url:
        clean_return_url = _research_overview_url()
    optional = {
        "view": view,
        "node_id": node_id,
        "query": query,
        "sort": sort,
        "detail_id": detail_id,
        "focus": focus,
        "action": action,
        "return_to": clean_return_to,
        "return_url": clean_return_url,
    }
    params.update(
        {key: str(value).strip() for key, value in optional.items() if str(value or "").strip()}
    )
    path = f"/paper-library?{urlencode(params)}"
    return f"{base}{path}" if base else path


def _paper_library_target_url(target: dict[str, object], *, fallback_detail_id: str = "") -> str:
    if not isinstance(target, dict) or str(target.get("surface") or "") != "paper_library":
        return ""
    return _paper_library_workspace_url(
        view=str(target.get("view") or ""),
        node_id=str(target.get("node_id") or ""),
        query=str(target.get("query") or ""),
        sort=str(target.get("sort") or ""),
        detail_id=str(target.get("detail_id") or fallback_detail_id or ""),
        focus=str(target.get("focus") or ""),
        action=str(target.get("action") or ""),
        return_to=str(target.get("return_to") or "overview"),
        return_url=str(target.get("return_url") or ""),
    )


def _paper_library_workspace_status(workspace_url: str) -> tuple[bool | None, str]:
    parsed = urlparse(workspace_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None, ""
    try:
        timeout = max(0.1, float(os.getenv("NBLANE_PAPER_LIBRARY_HEALTH_TIMEOUT", "2.5")))
    except ValueError:
        timeout = 2.5
    cache_key = _paper_library_key(f"workspace_status:{workspace_url}")
    now = time.time()
    cached = st.session_state.get(cache_key)
    if isinstance(cached, dict) and now - float(cached.get("checked_at", 0)) < 15:
        return bool(cached.get("ok")), str(cached.get("message") or "")
    try:
        request = urllib.request.Request(
            workspace_url,
            method="GET",
            headers={"User-Agent": "nblane-paper-library-runtime-check/1.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(getattr(response, "status", 200))
            marker = str(response.headers.get("X-Nblane-Sidecar") or "").strip()
            body = response.read(256).decode("utf-8", errors="ignore")
            ok = 200 <= status < 400 and (
                marker == "reader-api" or "nblane sidecar ok" in body
            )
            message = "" if ok else f"unexpected sidecar health response: HTTP {status}".strip()
    except Exception as exc:
        ok = False
        message = str(exc)
    st.session_state[cache_key] = {"checked_at": now, "ok": ok, "message": message}
    return ok, message


def _paper_library_sidecar_status() -> tuple[bool | None, str]:
    base = _reader_api_base()
    if not base:
        return None, ""
    health_url = f"{base}/auth/session-ok"
    try:
        timeout = max(0.1, float(os.getenv("NBLANE_PAPER_LIBRARY_HEALTH_TIMEOUT", "2.5")))
    except ValueError:
        timeout = 2.5
    cache_key = _paper_library_key(f"sidecar_status:{health_url}")
    now = time.time()
    cached = st.session_state.get(cache_key)
    if isinstance(cached, dict) and now - float(cached.get("checked_at", 0)) < 15:
        return bool(cached.get("ok")), str(cached.get("message") or "")
    try:
        request = urllib.request.Request(
            health_url,
            method="GET",
            headers={"User-Agent": "nblane-paper-library-sidecar-check/1.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            ok = 200 <= int(getattr(response, "status", 200)) < 400
            message = "" if ok else f"HTTP {getattr(response, 'status', '')}".strip()
    except Exception as exc:
        ok = False
        message = str(exc)
    st.session_state[cache_key] = {"checked_at": now, "ok": ok, "message": message}
    return ok, message


def _paper_library_sidecar_unavailable() -> tuple[bool, str]:
    """Return whether browser-facing 8502 links should be paused."""
    ok, message = _paper_library_sidecar_status()
    return ok is False, message


def _paper_library_sidecar_disabled_help(message: str = "") -> str:
    help_text = _l(
        "paper_library_sidecar_link_disabled_help",
        "Start or forward the 8502 Paper Library sidecar to use this link.",
    )
    if message:
        help_text = f"{help_text} {message}"
    return help_text


def _render_sidecar_link_button(
    label: str,
    url: str,
    *,
    key: str | None = None,
    icon: str | None = None,
    type: str = "secondary",
    use_container_width: bool | None = None,
    width: str = "content",
    help: str | None = None,
    disabled: bool = False,
) -> None:
    unavailable, message = _paper_library_sidecar_unavailable()
    is_disabled = disabled or unavailable
    help_text = help or (_paper_library_sidecar_disabled_help(message) if unavailable else None)
    try:
        st.link_button(
            label,
            url,
            key=key,
            icon=icon,
            type=type,
            use_container_width=use_container_width,
            width=width,
            help=help_text,
            disabled=is_disabled,
        )
    except Exception:
        if is_disabled:
            st.button(
                label,
                key=key,
                icon=icon,
                type=type,
                use_container_width=use_container_width,
                width=width,
                help=help_text,
                disabled=True,
            )
        else:
            st.caption(f"{_l('paper_library_workspace_url', 'Workspace')}: `{url}`")


def _render_research_sidecar_status() -> None:
    base = _reader_api_base()
    if not base:
        st.warning(
            _l(
                "research_sidecar_disabled",
                "Paper Library sidecar links are disabled; Reader and 8502 workspace buttons will use relative URLs.",
            )
        )
        return
    ok, message = _paper_library_sidecar_status()
    env_base = os.getenv("NBLANE_READER_API_BASE", "").strip()
    origin = (
        _l("same_origin", "same-origin")
        if env_base.strip().lower() in {"0", "false", "off", "none"}
        else
        _l("configured", "configured")
        if env_base
        else _l("auto_detected", "auto-detected")
    )
    if ok is False:
        st.warning(
            _l(
                "research_sidecar_unavailable",
                "8502 Paper Library sidecar is not reachable; Reader and Paper Library links are temporarily disabled for {base}.",
            ).format(base=base)
            + (f" `{message}`" if message else "")
        )
        return
    st.caption(
        _l(
            "research_sidecar_connected",
            "Paper Library sidecar: {origin} · {base}",
        ).format(origin=origin, base=base)
    )


def _render_authenticated_iframe(src: str, *, token: str, height: int, scrolling: bool) -> None:
    base = _reader_api_base()
    auth_url = f"{base}/auth/session" if base else "/auth/session"
    escaped_auth_url = html.escape(auth_url, quote=True)
    src_json = json.dumps(src).replace("</", "<\\/")
    escaped_token = html.escape(token, quote=True)
    frame_height = max(100, int(height or 800) - 2)
    wrapper = f"""
<!doctype html>
<html>
  <body style="margin:0;overflow:hidden">
    <iframe name="nblaneAuthTarget" title="nblane auth" style="display:none;width:0;height:0;border:0"></iframe>
    <form id="nblaneAuthForm" action="{escaped_auth_url}" method="post" target="nblaneAuthTarget" style="display:none">
      <input type="hidden" name="token" value="{escaped_token}">
    </form>
    <iframe id="nblaneContentFrame" title="nblane" style="width:100%;height:{frame_height}px;border:0" loading="eager"></iframe>
    <script>
      const content = document.getElementById("nblaneContentFrame");
      const form = document.getElementById("nblaneAuthForm");
      let loaded = false;
      const loadContent = () => {{
        if (loaded || !content) return;
        loaded = true;
        content.src = {src_json};
      }};
      const target = document.querySelector('iframe[name="nblaneAuthTarget"]');
      if (target) target.addEventListener("load", loadContent, {{ once: true }});
      if (form) form.submit();
      window.setTimeout(loadContent, 1200);
    </script>
  </body>
</html>
"""
    st.components.v1.html(wrapper, height=height, scrolling=scrolling)


def _render_iframe(src: str, *, height: int, scrolling: bool) -> None:
    token = sidecar_auth_handoff_token(user)
    if token:
        _render_authenticated_iframe(src, token=token, height=height, scrolling=scrolling)
        return
    if hasattr(st, "iframe"):
        st.iframe(src, height=height)
    else:
        st.components.v1.iframe(src, height=height, scrolling=scrolling)


def _short_text(value: object, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _badge_html(label: object, *, tone: str = "neutral") -> str:
    clean = html.escape(str(label or "").strip())
    if not clean:
        return ""
    return f'<span class="paper-badge paper-badge-{tone}">{clean}</span>'


def _badge_tone(label: object) -> str:
    text = str(label or "").lower()
    if any(part in text for part in ("missing", "broken", "failed", "warning")):
        return "warn"
    if any(part in text for part in ("duplicate", "stale", "needs")):
        return "alert"
    if any(part in text for part in ("ready", "pdf", "reviewed")):
        return "ok"
    return "neutral"


def _paper_badges_html(row: dict[str, object], *, limit: int = 5) -> str:
    badges = [str(item) for item in row.get("badges", []) if str(item).strip()]
    if row.get("has_pdf") and "PDF ready" not in badges:
        badges.insert(0, "PDF ready")
    if not badges:
        return ""
    visible = badges[:limit]
    rendered = [_badge_html(label, tone=_badge_tone(label)) for label in visible]
    if len(badges) > limit:
        rendered.append(_badge_html(f"+{len(badges) - limit}", tone="neutral"))
    return " ".join(item for item in rendered if item)


def _paper_primary_meta(row: dict[str, object]) -> str:
    parts = []
    if row.get("authors"):
        parts.append(_short_text(row.get("authors"), 80))
    if row.get("published"):
        parts.append(str(row.get("published")))
    if row.get("venue"):
        parts.append(str(row.get("venue")))
    if row.get("tree_path"):
        parts.append(str(row.get("tree_path")))
    return " · ".join(part for part in parts if part)


def _paper_tag_line(row: dict[str, object]) -> str:
    tags = [str(tag) for tag in row.get("tags", []) if str(tag).strip()]
    return " ".join(_badge_html(tag, tone="tag") for tag in tags[:6])


def _library_badge_set(row: dict[str, object]) -> set[str]:
    return {str(item) for item in row.get("badges", []) if str(item).strip()}


def _library_row_matches_view(row: dict[str, object], view: str) -> bool:
    badges = _library_badge_set(row)
    source = row.get("source")
    status = str(row.get("status") or "")
    visibility = str(row.get("visibility") or "")
    if view == "all":
        return True
    if view == "unsorted":
        return str(row.get("tree_path") or "") == "Unsorted" or "Unsorted" in badges
    if view in {"reading", "archived", "discarded"}:
        return status == view
    if view == "candidate_ready":
        return status == "candidate_ready" or "AI candidates" in badges
    if view == "no_pdf":
        return not bool(row.get("has_pdf"))
    if view == "needs_extraction":
        return bool(row.get("has_pdf")) and (
            not int(row.get("chunks_count") or 0) or "Needs structured extraction" in badges
        )
    if view == "claims_need_review":
        return status == "candidate_ready" or "AI candidates" in badges
    if view == "duplicate_risk":
        return "Duplicate risk" in badges
    if view == "stale_translation":
        return "Stale translation" in badges
    if view == "recent":
        return bool(row.get("last_read"))
    if view == "private":
        return visibility == "private"
    if view == "reviewed":
        return status == "summarized" or bool(getattr(source, "evidence_refs", []))
    return True


def _library_view_count(rows: list[dict[str, object]], view: str) -> int:
    return sum(1 for row in rows if _library_row_matches_view(row, view))


def _paper_node_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        source = row.get("source")
        for ref in getattr(source, "library_node_refs", []) or []:
            counts[str(ref)] = counts.get(str(ref), 0) + 1
    return counts


def _paper_tree_buttons(tree, rows: list[dict[str, object]]) -> None:
    counts = _paper_node_counts(rows)
    nodes = {node.id: node for node in tree.nodes if node.status != "trashed"}
    children: dict[str, list] = {}
    for node in tree.nodes:
        if node.status == "trashed":
            continue
        children.setdefault(node.parent_id or "", []).append(node)

    current_node = str(st.session_state.get(_paper_library_key("node"), "") or "")

    def walk(parent_id: str = "", depth: int = 0, seen: set[str] | None = None) -> None:
        seen = seen or set()
        for node in sorted(children.get(parent_id, []), key=lambda item: (item.order, item.title)):
            if node.id in seen:
                continue
            prefix = "  " * depth + ("> " if depth else "")
            label = f"{prefix}{node.title} ({counts.get(node.id, 0)})"
            button_type = "primary" if current_node == node.id else "secondary"
            if st.button(label, key=_paper_library_key(f"node:{node.id}"), type=button_type, use_container_width=True):
                st.session_state[_paper_library_key("node")] = node.id
                st.session_state[_paper_library_key("view")] = "all"
                st.session_state.pop(_paper_library_key("detail"), None)
                st.rerun()
            walk(node.id, depth + 1, seen | {node.id})

    if not nodes:
        st.caption(_l("tree_empty", "No library nodes yet."))
        return
    walk()


def _render_library_view_button(
    view_id: str,
    fallback: str,
    rows: list[dict[str, object]],
    current_view: str,
    current_node: str,
) -> None:
    count = _library_view_count(rows, view_id)
    label = f"{_l(f'library_view_{view_id}', fallback)} ({count})"
    button_type = "primary" if current_view == view_id and not current_node else "secondary"
    if st.button(
        label,
        key=_paper_library_key(f"view:{view_id}"),
        type=button_type,
        use_container_width=True,
    ):
        st.session_state[_paper_library_key("view")] = view_id
        st.session_state[_paper_library_key("node")] = ""
        st.session_state.pop(_paper_library_key("detail"), None)
        st.rerun()


def _render_library_view_group(
    group_id: str,
    fallback: str,
    view_ids: tuple[str, ...],
    rows: list[dict[str, object]],
    current_view: str,
    current_node: str,
) -> None:
    st.markdown(f"**{_l(f'library_group_{group_id}', fallback)}**")
    for view_id in view_ids:
        _render_library_view_button(
            view_id,
            _LIBRARY_VIEW_LABELS.get(view_id, view_id),
            rows,
            current_view,
            current_node,
        )


def _paper_collection_tree_items(tree, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counts = _paper_node_counts(rows)
    paths = paper_library_paths(_pdir)
    children: dict[str, list] = {}
    for node in tree.nodes:
        if node.status == "trashed":
            continue
        children.setdefault(node.parent_id or "", []).append(node)

    def walk(parent_id: str = "") -> list[dict[str, object]]:
        out: list[dict[str, object]] = []
        for node in sorted(children.get(parent_id, []), key=lambda item: (item.order, item.title.lower(), item.id)):
            out.append(
                {
                    "id": node.id,
                    "type": "collection",
                    "title": node.title,
                    "path": paths.get(node.id, node.title),
                    "description": node.description,
                    "count": counts.get(node.id, 0),
                    "parent_id": node.parent_id,
                    "color": node.color,
                    "icon": node.icon,
                    "children": walk(node.id),
                }
            )
        return out

    return [
        {
            "id": "collections:all",
            "type": "collection_root",
            "node_id": "",
            "title": _l("clear_tree_filter", "All collections"),
            "count": len(rows),
            "children": walk(""),
        }
    ]


def _paper_library_component_payload(
    tree,
    rows: list[dict[str, object]],
    *,
    current_view: str,
    current_node: str,
    selected_paper_ids: list[str],
    papers: list[dict[str, object]] | None = None,
    active_label: str = "",
    detail_id: str = "",
) -> dict[str, object]:
    def view_items(view_ids: tuple[str, ...]) -> list[dict[str, object]]:
        return [
            {
                "id": view_id,
                "type": "view",
                "title": _l(f"library_view_{view_id}", _LIBRARY_VIEW_LABELS.get(view_id, view_id)),
                "count": _library_view_count(rows, view_id),
            }
            for view_id in view_ids
        ]

    return {
        "active_view": current_view,
        "active_node_id": current_node,
        "active_label": active_label,
        "detail_id": detail_id,
        "selected_paper_ids": list(selected_paper_ids),
        "papers": list(papers or []),
        "sections": [
            {
                "id": "library",
                "title": _l("library_group_library", "Library"),
                "items": view_items(_LIBRARY_VIEW_GROUPS[0][2]),
            },
            {
                "id": "collections",
                "title": _l("collections", "Collections"),
                "items": _paper_collection_tree_items(tree, rows),
            },
            {
                "id": "technical_taxonomy",
                "title": _l("technical_taxonomy", "Technical Taxonomy"),
                "items": [
                    {
                        "id": f"technical:{taxonomy_id}",
                        "type": "taxonomy",
                        "title": _l(f"technical_taxonomy_{taxonomy_id}", fallback),
                        "count": 0,
                    }
                    for taxonomy_id, fallback in _TECHNICAL_TAXONOMY_LABELS
                ],
            },
            {
                "id": "work_queue",
                "title": _l("library_group_work_queue", "Work Queue"),
                "items": view_items(_LIBRARY_VIEW_GROUPS[1][2]),
            },
            {
                "id": "system",
                "title": _l("library_group_system", "System"),
                "items": view_items(_LIBRARY_VIEW_GROUPS[2][2]),
            },
        ],
        "capabilities": {
            "create_collection": True,
            "rename_collection": True,
            "move_collection": True,
            "delete_collection": True,
            "drop_papers": True,
        },
        "labels": {
            "add_selected_here": _l("add_selected_here", "Add selected papers here"),
            "add_to_collection": _l("add_to_collection", "Add to collection"),
            "archive": _l("archive", "Archive"),
            "cancel": _l("cancel", "Cancel"),
            "collapse": _l("collapse", "Collapse"),
            "collapse_all": _l("collapse_all", "Collapse all"),
            "collection_actions": _l("collection_actions", "Collection actions"),
            "collection_title": _l("collection_title", "Collection title"),
            "delete_collection": _l("delete_collection", "Delete collection"),
            "discard": _l("discard", "Discard"),
            "expand": _l("expand", "Expand"),
            "expand_all": _l("expand_all", "Expand all"),
            "mark_as_reading": _l("mark_as_reading", "Mark as reading"),
            "move_collection": _l("move_collection", "Move collection"),
            "move_down": _l("move_down", "Move down"),
            "move_papers_to_collection": _l("move_papers_to_collection", "Move papers to collection"),
            "move_papers_to_parent": _l("move_papers_to_parent", "Move papers to parent collection"),
            "move_papers_to_unsorted": _l("move_papers_to_unsorted", "Move papers to Unsorted Inbox"),
            "move_selected_here": _l("move_selected_here", "Move selected papers here"),
            "move_to_collection": _l("move_to_collection", "Move to collection"),
            "move_up": _l("move_up", "Move up"),
            "new_collection": _l("new_collection", "New collection"),
            "new_subcollection": _l("new_subcollection", "New subcollection"),
            "open_reader": _l("open_reader", "Open Reader"),
            "paper_policy": _l("paper_policy", "Paper policy"),
            "parent_collection": _l("parent_collection", "Parent collection"),
            "remove_from_current_collection": _l("remove_from_current_collection", "Remove from current collection"),
            "rename": _l("rename", "Rename"),
            "run_extraction": _l("run_extraction", "Run extraction"),
            "save": _l("save", "Save"),
            "search_collections": _l("search_collections", "Search collections"),
            "selected_papers": _l("selected_papers", "{count} papers selected"),
            "select_all": _l("select_all", "Select all"),
            "clear_selection": _l("clear_selection", "Clear"),
            "select_paper": _l("select_paper", "Select paper"),
            "show_details": _l("show_details", "Show details"),
            "library_empty": _l("library_empty", "No papers match this view."),
            "library_result_count": _l("paper_list_result_count", "{count} papers"),
            "target_collection": _l("target_collection", "Target collection"),
            "top_level": _l("top_level", "Top level"),
        },
    }


def _handle_paper_library_component_event(event: dict[str, object] | None) -> None:
    if not isinstance(event, dict):
        return
    action = str(event.get("action") or "")
    if not action:
        return
    event_id = str(event.get("event_id") or "")
    dedupe_key = _paper_library_key("component_last_event")
    if event_id and st.session_state.get(dedupe_key) == event_id:
        return
    if event_id:
        st.session_state[dedupe_key] = event_id

    try:
        source_mutating_actions = {
            "paper_library_trash_collection",
            "paper_library_purge_collection",
            "paper_library_add_selected_papers_to_collection",
            "paper_library_move_selected_papers_to_collection",
            "paper_library_drop_papers_to_collection",
            "paper_library_remove_papers_from_collection",
            "paper_library_update_papers_status",
            "paper_library_run_extraction",
            "paper_library_auto_chunk",
            "paper_library_delete_paper_record",
            "paper_library_delete_paper_asset",
            "paper_library_delete_paper_artifacts",
            "paper_library_purge_discarded_papers",
        }
        if action in source_mutating_actions:
            assert_files_current([_sources_path])
        result = handle_paper_library_event(
            _pdir,
            event,
            selected_paper_ids=[
                str(item).strip()
                for item in st.session_state.get(_paper_library_key("bulk_select"), []) or []
                if str(item).strip()
            ],
        )
        if not result.ok:
            if result.message:
                st.error(result.message)
            return
        if action in source_mutating_actions:
            refresh_file_snapshots([_sources_path])

        next_state = result.next
        if "view" in next_state:
            st.session_state[_paper_library_key("view")] = next_state.get("view") or "all"
        if "node_id" in next_state:
            st.session_state[_paper_library_key("node")] = next_state.get("node_id") or ""
        if "detail_id" in next_state:
            detail_id = next_state.get("detail_id") or ""
            if detail_id:
                st.session_state[_paper_library_key("detail")] = detail_id
            else:
                st.session_state.pop(_paper_library_key("detail"), None)
        if "reader_source_id" in next_state and next_state["reader_source_id"]:
            st.session_state[f"paper_reader_source:{selected}"] = next_state["reader_source_id"]

        if result.changed:
            stash_git_backup_results()
            clear_web_cache()
        if result.message:
            st.success(result.message if result.changed else result.message)
        st.rerun()
    except Exception as exc:
        st.error(str(exc))


def _render_paper_library_styles() -> None:
    st.markdown(
        """
<style>
.paper-card {
  border: 1px solid rgba(49, 51, 63, 0.16);
  border-radius: 8px;
  padding: 0.8rem 0.9rem;
  margin: 0 0 0.75rem 0;
  background: rgba(255, 255, 255, 0.82);
}
.paper-card-active {
  border-color: rgba(33, 115, 220, 0.7);
  background: rgba(33, 115, 220, 0.06);
}
.paper-title {
  font-weight: 700;
  font-size: 1.02rem;
  line-height: 1.35;
  color: rgb(31, 41, 55);
  margin-bottom: 0.22rem;
}
.paper-meta {
  color: rgba(49, 51, 63, 0.68);
  font-size: 0.82rem;
  line-height: 1.35;
  margin-bottom: 0.45rem;
}
.paper-summary {
  color: rgba(49, 51, 63, 0.82);
  font-size: 0.88rem;
  line-height: 1.45;
  margin: 0.35rem 0 0.55rem 0;
}
.paper-badge {
  display: inline-block;
  border-radius: 999px;
  padding: 0.12rem 0.45rem;
  margin: 0.08rem 0.16rem 0.08rem 0;
  font-size: 0.72rem;
  line-height: 1.35;
  border: 1px solid rgba(49, 51, 63, 0.14);
  background: rgba(49, 51, 63, 0.055);
  color: rgba(31, 41, 55, 0.86);
}
.paper-badge-ok {
  border-color: rgba(22, 163, 74, 0.22);
  background: rgba(22, 163, 74, 0.09);
  color: rgb(22, 101, 52);
}
.paper-badge-warn {
  border-color: rgba(245, 158, 11, 0.32);
  background: rgba(245, 158, 11, 0.12);
  color: rgb(146, 64, 14);
}
.paper-badge-alert {
  border-color: rgba(220, 38, 38, 0.24);
  background: rgba(220, 38, 38, 0.08);
  color: rgb(153, 27, 27);
}
.paper-badge-tag {
  border-color: rgba(37, 99, 235, 0.18);
  background: rgba(37, 99, 235, 0.075);
  color: rgb(30, 64, 175);
}
.paper-detail-title {
  font-size: 1.05rem;
  font-weight: 750;
  line-height: 1.35;
  margin-bottom: 0.25rem;
}
.paper-muted {
  color: rgba(49, 51, 63, 0.65);
  font-size: 0.82rem;
}
</style>
""",
        unsafe_allow_html=True,
    )


def _marked_search_results(results: list[object]) -> list[PaperSearchResult]:
    return mark_imported_paper_results(_pdir, results)


def _unique_text(values: list[str]) -> list[str]:
    out = []
    seen = set()
    for value in values:
        clean = str(value or "").strip()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _normalized_title(value: str) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _search_result_warnings(result: PaperSearchResult, inbox) -> list[str]:
    warnings = list(result.warnings)
    if result.imported_source_id:
        warnings.append(f"Duplicate import: already stored as {result.imported_source_id}.")
    link_status = str((result.link_check or {}).get("status") or "").strip()
    if result.needs_link_check:
        warnings.append("Needs link check before automatic PDF download.")
    if link_status and link_status not in {"ok", "200"}:
        warnings.append(f"Link check: {link_status}.")
    if not result.open_access_pdf:
        warnings.append("No downloadable PDF URL; import metadata first or upload a local PDF.")

    title_key = _normalized_title(result.title)
    for source in _paper_sources(inbox):
        if source.id == result.imported_source_id:
            continue
        same_title = title_key and title_key == _normalized_title(source.title)
        same_year = not result.year or not source.published or result.year == str(source.published)[:4]
        if not (same_title and same_year):
            continue
        source_meta = source.metadata or {}
        source_doi = str(source_meta.get("doi") or "").lower()
        result_doi = result.doi.lower()
        source_arxiv = str(source_meta.get("arxiv_id") or "").lower()
        result_arxiv = result.arxiv_id.lower()
        if result_doi and source_doi and result_doi != source_doi:
            warnings.append(f"Metadata conflict with {source.id}: DOI differs.")
        elif result_arxiv and source_arxiv and result_arxiv != source_arxiv:
            warnings.append(f"Metadata conflict with {source.id}: arXiv id differs.")
        elif not result.imported_source_id:
            warnings.append(f"Possible duplicate: similar title/year to {source.id}.")
    return _unique_text(warnings)


def _render_search_result_details(results: list[PaperSearchResult], inbox) -> None:
    st.markdown(f"**{_l('result_details', 'Result details')}**")
    for result in results:
        title = result.title or result.candidate_id
        with st.expander(f"{title} · {result.year or 'n.d.'}", expanded=False):
            warnings = _search_result_warnings(result, inbox)
            for warning in warnings:
                st.warning(warning)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{_l('metadata', 'Metadata')}**")
                st.write(
                    {
                        "candidate_id": result.candidate_id,
                        "authors": result.authors,
                        "year": result.year,
                        "venue": result.venue,
                        "citations": result.citation_count,
                        "providers": result.provider_refs,
                    }
                )
                st.markdown(f"**{_l('identifiers', 'Identifiers')}**")
                st.write(
                    {
                        "doi": result.doi,
                        "arxiv_id": result.arxiv_id,
                        "semantic_scholar_id": result.semantic_scholar_id,
                        "canonical_url": result.canonical_url,
                        "pdf_url": result.pdf_url,
                    }
                )
            with c2:
                st.markdown(f"**{_l('import_hints', 'Import hints')}**")
                st.write(
                    {
                        "imported": result.imported_source_id,
                        "oa_pdf": bool(result.open_access_pdf),
                        "tags": result.tags,
                        "fields_of_study": result.fields_of_study,
                        "suggested_library_nodes": result.suggested_library_nodes,
                    }
                )
                st.markdown(f"**{_l('link_check', 'Link check')}**")
                st.code(
                    yaml.dump(
                        result.link_check or {"status": "needs check"},
                        allow_unicode=True,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            if result.why_relevant:
                st.markdown(f"**{_l('relevance', 'Relevance')}**")
                st.caption(result.why_relevant)
            if result.abstract:
                st.markdown(f"**{_l('abstract', 'Abstract')}**")
                st.write(result.abstract)


def _search_result_meta_line(result: PaperSearchResult) -> str:
    parts = []
    if result.year:
        parts.append(result.year)
    if result.venue:
        parts.append(result.venue)
    if result.authors:
        parts.append(_short_text(", ".join(result.authors[:4]), 140))
    if result.provider_refs:
        parts.append(_short_text(", ".join(result.provider_refs), 120))
    if result.citation_count is not None:
        parts.append(f"{_l('citations', 'Citations')}: {result.citation_count}")
    return " · ".join(parts)


def _search_result_external_links(result: PaperSearchResult) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    if result.canonical_url:
        links.append((_l("paper_page", "Paper page"), result.canonical_url))
    if result.pdf_url:
        links.append(("PDF", result.pdf_url))
    if result.doi:
        links.append(("DOI", f"https://doi.org/{result.doi}"))
    if result.arxiv_id:
        links.append(("arXiv", f"https://arxiv.org/abs/{result.arxiv_id}"))
    return links


def _search_result_link_html(title: str, url: str, *, source: str = "", summary: str = "") -> str:
    parsed = urlparse(str(url or ""))
    if parsed.scheme not in {"http", "https"}:
        return ""
    clean_title = html.escape(str(title or url))
    clean_url = html.escape(str(url or ""))
    clean_source = html.escape(str(source or ""))
    clean_summary = html.escape(_short_text(summary, 180))
    source_part = f'<span style="color:#6b7280;"> · {clean_source}</span>' if clean_source else ""
    summary_part = f'<div style="color:#4b5563;font-size:.86rem;line-height:1.4;margin-top:2px;">{clean_summary}</div>' if clean_summary else ""
    return (
        '<div style="margin:4px 0;">'
        f'<a href="{clean_url}" target="_blank" rel="noreferrer">{clean_title}</a>'
        f"{source_part}{summary_part}</div>"
    )


def _render_search_result_cards(
    results: list[PaperSearchResult],
    inbox,
    *,
    mode: str,
) -> list[str]:
    selected_ids: list[str] = []
    st.markdown(f"**{_l('search_triage_results', 'Triage candidates')}**")
    st.caption(
        _l(
            "search_triage_hint",
            "Read the abstract, AI overview, and explainer links first; select only the papers you want to import.",
        )
    )
    for index, result in enumerate(results, start=1):
        warnings = _search_result_warnings(result, inbox)
        imported = bool(result.imported_source_id)
        key = _search_state_key(f"select:{result.candidate_id}")
        with st.container(border=True):
            select_col, body_col = st.columns([0.18, 1.82], gap="medium")
            with select_col:
                picked = st.checkbox(
                    _l("select_to_import_short", "Import"),
                    key=key,
                    disabled=imported,
                )
                if picked and not imported:
                    selected_ids.append(result.candidate_id)
            with body_col:
                st.markdown(f"**{index}. {result.title or result.candidate_id}**")
                meta_line = _search_result_meta_line(result)
                if meta_line:
                    st.caption(meta_line)
                badge_bits = []
                if result.open_access_pdf:
                    badge_bits.append("PDF ready")
                if imported:
                    badge_bits.append(f"Imported: {result.imported_source_id}")
                if result.tags:
                    badge_bits.extend(result.tags[:4])
                if result.fields_of_study:
                    badge_bits.extend(result.fields_of_study[:3])
                if badge_bits:
                    st.caption(" · ".join(str(item) for item in badge_bits if str(item).strip()))

                if result.ai_summary:
                    st.markdown(f"**{_l('ai_summary', 'AI overview')}**")
                    st.write(result.ai_summary)
                if result.why_relevant:
                    st.markdown(f"**{_l('why_relevant', 'Why it matters')}**")
                    st.write(result.why_relevant)
                if result.abstract:
                    st.markdown(f"**{_l('abstract', 'Abstract')}**")
                    st.write(_short_text(result.abstract, 900))
                    if len(result.abstract) > 900:
                        with st.expander(_l("full_abstract", "Full abstract"), expanded=False):
                            st.write(result.abstract)

                if result.explanation_links:
                    st.markdown(f"**{_l('explainer_links', 'Explainer links')}**")
                    rendered_links = [
                        _search_result_link_html(
                            str(link.get("title") or link.get("url") or ""),
                            str(link.get("url") or ""),
                            source=str(link.get("source") or ""),
                            summary=str(link.get("summary") or ""),
                        )
                        for link in result.explanation_links
                        if str(link.get("url") or "").strip()
                    ]
                    st.markdown(
                        "\n".join(item for item in rendered_links if item),
                        unsafe_allow_html=True,
                    )
                elif mode == "Codex Search":
                    st.caption(_l("explainer_links_empty", "No verified explainer links returned for this candidate."))

                external_links = _search_result_external_links(result)
                if external_links:
                    link_cols = st.columns(min(4, len(external_links)))
                    for offset, (title, url) in enumerate(external_links[:4]):
                        with link_cols[offset]:
                            try:
                                st.link_button(title, url, use_container_width=True)
                            except Exception:
                                st.caption(f"{title}: {url}")
                if warnings:
                    with st.expander(_l("search_result_warnings", "Warnings and raw metadata"), expanded=False):
                        for warning in warnings:
                            st.warning(warning)
                        st.code(
                            yaml.dump(
                                result.to_dict(),
                                allow_unicode=True,
                                default_flow_style=False,
                                sort_keys=False,
                            ),
                            language="yaml",
                        )
    return selected_ids


def _result_rows(results: list[object]) -> list[dict[str, object]]:
    marked = _marked_search_results(results)
    return [
        {
            "select_id": row.candidate_id,
            "title": row.title,
            "year": row.year,
            "venue": row.venue,
            "authors": ", ".join(row.authors[:3]),
            "provider": ", ".join(row.provider_refs),
            "citations": row.citation_count if row.citation_count is not None else "",
            "oa_pdf": bool(row.open_access_pdf),
            "link": (row.link_check or {}).get("status", "needs check"),
            "imported": row.imported_source_id,
            "warnings": " · ".join(_search_result_warnings(row, load_research_sources(selected))),
            "abstract": _short_text(row.abstract, 260),
            "ai_summary": _short_text(row.ai_summary, 220),
            "relevance": row.why_relevant,
            "explainers": len(row.explanation_links),
            "tags": ", ".join(row.tags),
        }
        for row in marked
    ]


def _search_state_key(name: str) -> str:
    return f"paper_search:{selected}:{name}"


def _focus_library_import(imported_ids: list[str], node_ref: str) -> None:
    clean_node = str(node_ref or "").strip()
    st.session_state[_paper_library_key("view")] = "all" if clean_node else "unsorted"
    st.session_state[_paper_library_key("node")] = clean_node
    if imported_ids:
        st.session_state[_paper_library_key("detail")] = imported_ids[0]
        st.session_state[_search_state_key("results")] = []


def _render_paper_search(inbox, *, embedded: bool = False) -> None:
    node_options = _node_options()
    current_node = str(st.session_state.get(_paper_library_key("node"), "") or "")
    default_location = node_options.get(current_node, _l("unsorted_inbox", "Unsorted Inbox"))
    if not embedded:
        st.subheader(_l("paper_search", "Paper Search"))
    st.caption(
        _l(
            "paper_search_caption",
            "Search results stay preview-only, show abstracts first, and import into the selected Library location only after confirmation.",
        )
    )
    if embedded:
        st.caption(
            _l("paper_search_library_default", "Default import location: {location}").format(
                location=default_location
            )
        )
    prepare_notice_key = f"paper_reader_prepare_notice:{selected}"
    prepare_notice = st.session_state.pop(prepare_notice_key, "")
    if prepare_notice:
        st.info(str(prepare_notice))
    mode = st.radio(
        _l("search_mode", "Search mode"),
        [
            "Codex Search",
            "Provider Search",
            "Manual URL",
            "Upload PDF",
        ],
        horizontal=True,
        key=f"paper_search_mode:{selected}",
    )

    if mode in {"Codex Search", "Provider Search"}:
        with st.form(f"paper_search_form:{selected}"):
            query = st.text_input(_l("query", "Query"), placeholder="VLA memory")
            if mode == "Provider Search":
                providers = st.multiselect(
                    _l("providers", "Providers"),
                    options=list(PAPER_SEARCH_PROVIDERS),
                    default=list(PAPER_SEARCH_PROVIDERS),
                )
            else:
                providers = []
                st.caption(
                    _l(
                        "codex_search_pdf_policy",
                        "Codex can use any source/provider; only candidates with a downloadable PDF URL are shown.",
                    )
                )
            c1, c2, c3 = st.columns(3)
            with c1:
                limit = st.number_input(_l("limit", "Limit"), min_value=1, max_value=50, value=10)
            with c2:
                year_from = st.text_input(_l("year_from", "Year from"))
            with c3:
                year_to = st.text_input(_l("year_to", "Year to"))
            only_pdf = st.checkbox(
                _l("has_open_access_pdf", "Has downloadable PDF"),
                value=mode == "Codex Search",
                disabled=mode == "Codex Search",
            )
            exclude_imported = st.checkbox(_l("exclude_imported", "Exclude already imported"), value=True)
            project_refs = st.text_area(ui["project_refs"], height=68)
            goal_refs = st.text_area(ui["goal_refs"], height=68)
            submitted = st.form_submit_button(_l("search_papers", "Search papers"), type="primary")
        if submitted:
            filters = {
                "providers": providers,
                "limit": limit,
                "year_from": year_from,
                "year_to": year_to,
                "has_open_access_pdf": only_pdf,
            }
            if mode == "Codex Search":
                result = search_papers_codex(
                    selected,
                    query,
                    payload={
                        "filters": filters,
                        "providers": providers,
                        "project_refs": _text_lines(project_refs),
                        "goal_refs": _text_lines(goal_refs),
                        "already_imported": _paper_search_imported_refs(_pdir),
                        "library_tree_hint": _paper_search_library_tree_hint(_pdir),
                        "triage_fields": [
                            "abstract",
                            "ai_summary",
                            "why_relevant",
                            "explanation_links",
                        ],
                        "explanation_link_sources": [
                            "Zhihu",
                            "Xiaohongshu",
                            "blog",
                            "video",
                            "project page",
                            "author page",
                        ],
                        "instructions": (
                            "Return paper candidates for coarse reading from any reputable source/provider. "
                            "Only include results with a direct downloadable PDF URL in pdf_url or open_access_pdf_url. "
                            "For each result, include abstract if available, a concise AI overview in the user's language, "
                            "why it matters for the query, and verified explainer links when available. Do not invent explainer links."
                        ),
                    },
                )
                raw = result.structured if isinstance(result.structured, dict) else {}
                candidates = []
                for row in raw.get("results", []):
                    item = PaperSearchResult.from_dict(row)
                    if item is None or not _paper_search_result_has_downloadable_pdf(item):
                        continue
                    candidates.append(item.to_dict())
                if not candidates:
                    if result.error:
                        st.warning(
                            f"{result.backend or 'local_codex_readonly'} failed "
                            f"({result.error}); using provider search fallback."
                        )
                    else:
                        st.warning(
                            _l(
                                "codex_search_fallback",
                                "Codex returned no structured papers; using provider search fallback.",
                            )
                        )
                    candidates = [row.to_dict() for row in search_papers(query, tuple(providers or PAPER_SEARCH_PROVIDERS), int(limit), filters)]
                for warning in result.warnings:
                    st.warning(str(warning))
            else:
                candidates = [row.to_dict() for row in search_papers(query, tuple(providers), int(limit), filters)]
            if exclude_imported:
                candidates = [
                    row.to_dict()
                    for row in mark_imported_paper_results(_pdir, candidates)
                    if not row.imported_source_id
                ]
            st.session_state[_search_state_key("results")] = candidates
            st.rerun()

        results = list(st.session_state.get(_search_state_key("results"), []) or [])
        if results:
            marked_results = _marked_search_results(results)
            result_dicts = [row.to_dict() for row in marked_results]
            selected_ids = _render_search_result_cards(marked_results, inbox, mode=mode)
            with st.expander(_l("compact_table", "Compact table"), expanded=False):
                st.dataframe(_result_rows(result_dicts), use_container_width=True, hide_index=True)
            if selected_ids:
                with st.expander(_l("selected_metadata_preview", "Selected metadata preview"), expanded=False):
                    st.code(
                        yaml.dump(
                            [row.to_dict() for row in marked_results if row.candidate_id in set(selected_ids)],
                            allow_unicode=True,
                            default_flow_style=False,
                            sort_keys=False,
                        ),
                        language="yaml",
                    )
            with st.form(f"paper_import_options:{selected}"):
                node_options = _node_options()
                default_node = str(st.session_state.get(_paper_library_key("node"), "") or "")
                node_ref = st.selectbox(
                    _l("library_location", "Library location"),
                    options=list(node_options),
                    index=_node_select_index(node_options, default_node),
                    format_func=lambda ref: node_options.get(ref, ref),
                )
                child_collection = st.text_input(_l("new_child_collection", "New child collection"))
                tags = st.text_input(ui["tags"])
                visibility = st.selectbox(ui["visibility"], ["private", "public"], index=0)
                status = st.selectbox(ui["status"], SOURCE_STATUSES, index=SOURCE_STATUSES.index("inbox"))
                pdf_strategy = st.radio(
                    _l("pdf_strategy", "PDF strategy"),
                    [
                        _l("pdf_strategy_metadata_only", "Metadata only"),
                        _l("download_open_access_pdf", "Download open-access PDF"),
                        _l("pdf_strategy_upload_later", "Upload local PDF after import"),
                    ],
                    horizontal=True,
                    key=f"pdf_strategy:{selected}",
                )
                prepare_reader = st.checkbox(
                    _l("prepare_reader_after_import", "Prepare Reader text after import"),
                    value=True,
                    disabled=pdf_strategy != _l("download_open_access_pdf", "Download open-access PDF"),
                )
                confirmed = st.form_submit_button(_l("import_selected", "Import selected"), type="primary")
            selected_results = [row for row in marked_results if row.candidate_id in set(selected_ids)]
            if pdf_strategy == _l("download_open_access_pdf", "Download open-access PDF"):
                for row in selected_results:
                    if row.needs_link_check:
                        st.warning(f"{row.title}: needs link check before PDF download.")
                    if not row.open_access_pdf:
                        st.warning(f"{row.title}: no open-access PDF URL to download.")
            elif pdf_strategy == _l("pdf_strategy_upload_later", "Upload local PDF after import") and selected_ids:
                st.info(
                    _l(
                        "upload_pdf_after_import_hint",
                        "Import will create private inbox metadata; attach the local PDF from Upload PDF after import.",
                    )
                )
            if confirmed:
                try:
                    _accept_latest_sources_for_additive_write()
                    import_node_ref = node_ref
                    if selected_ids and str(child_collection or "").strip():
                        import_node_ref = create_paper_library_node(
                            _pdir,
                            child_collection,
                            parent_id=node_ref,
                        ).id
                    imported = import_paper_search_results(
                        _pdir,
                        result_dicts,
                        selected_ids,
                        {
                            "library_node_refs": [import_node_ref] if import_node_ref else [],
                            "tags": _tags(tags),
                            "visibility": visibility,
                            "status": status,
                            "goal_refs": _text_lines(goal_refs),
                            "project_refs": _text_lines(project_refs),
                            "download_pdf": pdf_strategy == _l("download_open_access_pdf", "Download open-access PDF"),
                        },
                    )
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    _focus_library_import(imported, import_node_ref)
                    st.success(_l("imported_papers", "Imported papers: {ids}").format(ids=", ".join(imported) or "0"))
                    refreshed = load_research_sources(selected).by_id()
                    imported_pdf_assets = [
                        source_id
                        for source_id in imported
                        if (
                            (refreshed.get(source_id).metadata if refreshed.get(source_id) is not None else {}).get(
                                "pdf_asset_ref"
                            )
                        )
                    ]
                    if (
                        pdf_strategy == _l("download_open_access_pdf", "Download open-access PDF")
                        and imported_pdf_assets
                    ):
                        if prepare_reader:
                            with st.spinner(_l("prepare_reader_after_import", "Prepare Reader text after import")):
                                prepare_summary = _prepare_reader_artifacts_for_sources(imported_pdf_assets)
                            if prepare_summary["prepared"]:
                                st.success(
                                    _l("reader_artifacts_prepared", "Reader text prepared: {ids}").format(
                                        ids=", ".join(prepare_summary["prepared"])
                                    )
                                )
                            for warning in prepare_summary["warnings"]:
                                st.warning(str(warning))
                        else:
                            st.session_state[prepare_notice_key] = _l(
                                "reader_background_prepare_hint",
                                "PDF assets are saved now; Reader will prepare text in the background when opened.",
                            )
                    for source_id in imported:
                        source = refreshed.get(source_id)
                        metadata = source.metadata if source is not None else {}
                        if metadata.get("pdf_download_status") not in ("", None, "downloaded"):
                            st.warning(
                                f"{source_id}: {metadata.get('pdf_download_status')} · "
                                f"{metadata.get('pdf_download_error', '')}"
                            )
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.caption(_l("search_results_empty", "No paper candidates yet."))

    elif mode == "Manual URL":
        with st.form(f"paper_manual_url:{selected}"):
            url = st.text_input(_l("url_or_doi", "URL / DOI / arXiv / PDF URL"))
            title_hint = st.text_input(_l("title_hint", "Title hint"))
            node_options = _node_options()
            default_node = str(st.session_state.get(_paper_library_key("node"), "") or "")
            node_ref = st.selectbox(
                _l("library_location", "Library location"),
                options=list(node_options),
                index=_node_select_index(node_options, default_node),
                format_func=lambda ref: node_options.get(ref, ref),
            )
            child_collection = st.text_input(_l("new_child_collection", "New child collection"))
            tags = st.text_input(ui["tags"])
            visibility = st.selectbox(ui["visibility"], ["private", "public"], index=0)
            status = st.selectbox(ui["status"], SOURCE_STATUSES, index=SOURCE_STATUSES.index("inbox"))
            download_pdf = st.checkbox(_l("download_open_access_pdf", "Download open-access PDF"), value=True)
            prepare_reader = st.checkbox(
                _l("prepare_reader_after_import", "Prepare Reader text after import"),
                value=True,
                disabled=not download_pdf,
            )
            submitted = st.form_submit_button(_l("import_url", "Import URL"), type="primary")
        if submitted:
            try:
                _accept_latest_sources_for_additive_write()
                import_node_ref = node_ref
                if str(child_collection or "").strip():
                    import_node_ref = create_paper_library_node(
                        _pdir,
                        child_collection,
                        parent_id=node_ref,
                    ).id
                source_id = import_paper_url(
                    _pdir,
                    url,
                    {
                        "title": title_hint,
                        "library_node_refs": [import_node_ref] if import_node_ref else [],
                        "tags": _tags(tags),
                        "visibility": visibility,
                        "status": status,
                        "download_pdf": download_pdf,
                    },
                )
                if download_pdf and prepare_reader:
                    with st.spinner(_l("prepare_reader_after_import", "Prepare Reader text after import")):
                        prepare_summary = _prepare_reader_artifacts_for_sources([source_id])
                    for warning in prepare_summary["warnings"]:
                        st.warning(str(warning))
                refresh_file_snapshots([_sources_path])
                stash_git_backup_results()
                clear_web_cache()
                _focus_library_import([source_id], import_node_ref)
                st.success(ui["created"].format(id=source_id))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    else:
        st.caption(_l("upload_pdf_caption", "Upload a local PDF and bind it to a private paper source."))
        with st.form(f"paper_upload:{selected}"):
            title = st.text_input(ui["title_label"])
            uploaded = st.file_uploader("PDF", type=["pdf"])
            node_options = _node_options()
            default_node = str(st.session_state.get(_paper_library_key("node"), "") or "")
            node_ref = st.selectbox(
                _l("library_location", "Library location"),
                options=list(node_options),
                index=_node_select_index(node_options, default_node),
                format_func=lambda ref: node_options.get(ref, ref),
            )
            child_collection = st.text_input(_l("new_child_collection", "New child collection"))
            tags = st.text_input(ui["tags"])
            visibility = st.selectbox(ui["visibility"], ["private", "public"], index=0)
            prepare_reader = st.checkbox(
                _l("prepare_reader_after_import", "Prepare Reader text after import"),
                value=True,
            )
            submitted = st.form_submit_button(_l("upload_pdf", "Upload PDF"), type="primary")
        if submitted:
            try:
                if uploaded is None:
                    raise ValueError("Select a PDF first.")
                _accept_latest_sources_for_additive_write()
                import_node_ref = node_ref
                if str(child_collection or "").strip():
                    import_node_ref = create_paper_library_node(
                        _pdir,
                        child_collection,
                        parent_id=node_ref,
                    ).id
                inbox = load_research_sources(selected)
                source = add_research_source(
                    inbox,
                    title or uploaded.name,
                    kind="paper",
                    status="reading",
                    tags=_tags(tags),
                    visibility=visibility,
                    origin="manual",
                    library_node_refs=[import_node_ref] if import_node_ref else [],
                )
                save_research_sources(selected, inbox)
                import_paper_pdf(_pdir, source.id, uploaded.getvalue(), uploaded.name)
                if prepare_reader:
                    with st.spinner(_l("prepare_reader_after_import", "Prepare Reader text after import")):
                        prepare_summary = _prepare_reader_artifacts_for_sources([source.id])
                    for warning in prepare_summary["warnings"]:
                        st.warning(str(warning))
                refresh_file_snapshots([_sources_path])
                stash_git_backup_results()
                clear_web_cache()
                _focus_library_import([source.id], import_node_ref)
                st.success(ui["created"].format(id=source.id))
                if not prepare_reader:
                    st.session_state[prepare_notice_key] = _l(
                        "reader_background_prepare_hint",
                        "PDF assets are saved now; Reader will prepare text in the background when opened.",
                    )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _render_grobid_status_block(source=None) -> None:
    configured = bool(os.getenv("NBLANE_GROBID_URL", "").strip())
    with st.expander(_l("grobid_readiness", "GROBID readiness"), expanded=False):
        if not configured:
            st.info(
                _l(
                    "grobid_not_configured",
                    "NBLANE_GROBID_URL is not configured; structured extraction will try the local GROBID default and fall back if unavailable.",
                )
            )
            if source is not None:
                metadata = source.metadata or {}
                warnings = metadata.get("structured_extraction_warnings") or []
                for warning in warnings:
                    st.warning(str(warning))
                st.caption(
                    " · ".join(
                        [
                            f"structure_backend={metadata.get('structure_backend', '') or 'missing'}",
                            f"structured_extracted_at={metadata.get('structured_extracted_at', '') or 'never'}",
                        ]
                    )
                )
            return
        try:
            status = grobid_readiness()
            if status.get("available"):
                st.success(str(status.get("message") or "GROBID available."))
            else:
                st.warning(str(status.get("message") or "GROBID unavailable."))
            st.code(
                yaml.dump(status, allow_unicode=True, default_flow_style=False, sort_keys=False),
                language="yaml",
            )
        except Exception as exc:
            st.warning(str(exc))
        if source is not None:
            metadata = source.metadata or {}
            warnings = metadata.get("structured_extraction_warnings") or []
            if warnings:
                for warning in warnings:
                    st.warning(str(warning))
            st.caption(
                " · ".join(
                    [
                        f"structure_backend={metadata.get('structure_backend', '') or 'missing'}",
                        f"structured_extracted_at={metadata.get('structured_extracted_at', '') or 'never'}",
                    ]
                )
            )


def _render_library_collection_manager(tree, node_options: dict[str, str]) -> None:
    with st.expander(_l("manage_collections", "Manage collections"), expanded=False):
        paths = paper_library_paths(_pdir)
        active_node_options = {node_id: label for node_id, label in node_options.items() if node_id}
        node_counts = _paper_node_counts(paper_rows(_pdir, view="all"))
        if tree.nodes:
            st.dataframe(
                [
                    {
                        "path": paths.get(node.id, node.title),
                        "description": node.description,
                        "status": node.status,
                        "papers": node_counts.get(node.id, 0),
                    }
                    for node in tree.nodes
                ],
                use_container_width=True,
                hide_index=True,
            )
        current_node = str(st.session_state.get(_paper_library_key("node"), "") or "")
        parent_options = {"": _l("top_level", "Top level"), **active_node_options}

        st.markdown(f"**{_l('new_collection', 'New collection')}**")
        with st.form(_paper_library_key("collection_create")):
            default_parent = current_node if current_node in parent_options else ""
            parent_id = st.selectbox(
                _l("parent_collection", "Parent collection"),
                options=list(parent_options),
                index=_node_select_index(parent_options, default_parent),
                format_func=lambda ref: parent_options.get(ref, ref),
            )
            title = st.text_input(_l("collection_title", "Collection title"))
            c1, c2 = st.columns(2)
            with c1:
                icon = st.text_input(_l("collection_icon", "Icon"))
            with c2:
                color = st.text_input(_l("collection_color", "Color"))
            description = st.text_area(ui["notes"], height=72)
            create_submitted = st.form_submit_button(_l("create", "Create"), type="primary")
        if create_submitted:
            try:
                create_paper_library_node(
                    _pdir,
                    title,
                    parent_id=parent_id,
                    description=description,
                    color=color,
                    icon=icon,
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(_l("created", "Created: {id}").format(id=title))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if active_node_options:
            st.markdown(f"**{_l('edit_collection', 'Edit collection')}**")
            selected_node_id = st.selectbox(
                _l("collection", "Collection"),
                options=list(active_node_options),
                index=_node_select_index(active_node_options, current_node),
                format_func=lambda ref: active_node_options.get(ref, ref),
                key=_paper_library_key("manage_selected_node"),
            )
            selected_node = tree.by_id().get(selected_node_id)
            if selected_node is not None:
                with st.form(_paper_library_key(f"collection_rename:{selected_node_id}")):
                    next_title = st.text_input(
                        _l("collection_title", "Collection title"),
                        value=selected_node.title,
                    )
                    rename_submitted = st.form_submit_button(_l("rename", "Rename"), type="primary")
                if rename_submitted:
                    try:
                        rename_paper_library_node(_pdir, selected_node_id, next_title)
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(ui["saved"])
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

                move_parent_options = {
                    key: value
                    for key, value in parent_options.items()
                    if key != selected_node_id
                }
                with st.form(_paper_library_key(f"collection_move:{selected_node_id}")):
                    next_parent = st.selectbox(
                        _l("move_under", "Move under"),
                        options=list(move_parent_options),
                        index=_node_select_index(move_parent_options, selected_node.parent_id),
                        format_func=lambda ref: move_parent_options.get(ref, ref),
                    )
                    move_submitted = st.form_submit_button(
                        _l("move_collection", "Move collection"),
                        type="secondary",
                    )
                if move_submitted:
                    try:
                        position_paper_library_node(_pdir, selected_node_id, parent_id=next_parent)
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(ui["saved"])
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

                r1, r2 = st.columns(2)
                with r1:
                    if st.button(
                        _l("move_up", "Move up"),
                        key=_paper_library_key(f"collection_up:{selected_node_id}"),
                        icon=":material/arrow_upward:",
                        use_container_width=True,
                    ):
                        try:
                            reorder_paper_library_node(_pdir, selected_node_id, "up")
                            stash_git_backup_results()
                            clear_web_cache()
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                with r2:
                    if st.button(
                        _l("move_down", "Move down"),
                        key=_paper_library_key(f"collection_down:{selected_node_id}"),
                        icon=":material/arrow_downward:",
                        use_container_width=True,
                    ):
                        try:
                            reorder_paper_library_node(_pdir, selected_node_id, "down")
                            stash_git_backup_results()
                            clear_web_cache()
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

                with st.form(_paper_library_key(f"collection_delete:{selected_node_id}")):
                    delete_policy = st.selectbox(
                        _l("paper_policy", "Paper policy"),
                        options=["move_to_parent", "move_to_unsorted", "move_to_collection"],
                        format_func=lambda value: {
                            "move_to_parent": _l("move_papers_to_parent", "Move papers to parent collection"),
                            "move_to_unsorted": _l("move_papers_to_unsorted", "Move papers to Unsorted Inbox"),
                            "move_to_collection": _l("move_papers_to_collection", "Move papers to collection"),
                        }.get(value, value),
                    )
                    policy_target = ""
                    if delete_policy == "move_to_collection":
                        target_options = {
                            key: value
                            for key, value in active_node_options.items()
                            if key != selected_node_id
                        }
                        if target_options:
                            policy_target = st.selectbox(
                                _l("target_collection", "Target collection"),
                                options=list(target_options),
                                format_func=lambda ref: target_options.get(ref, ref),
                            )
                        else:
                            st.caption(_l("no_target_collections", "No target collections."))
                    confirmed = st.checkbox(_l("confirm_delete", "Confirm delete"))
                    delete_submitted = st.form_submit_button(
                        _l("delete_collection", "Delete collection"),
                        type="secondary",
                    )
                if delete_submitted:
                    if not confirmed:
                        st.warning(_l("confirm_delete_required", "Confirm delete first."))
                    elif delete_policy == "move_to_collection" and not policy_target:
                        st.warning(_l("target_collection_required", "Choose a target collection first."))
                    else:
                        try:
                            assert_files_current([_sources_path])
                            policy = f"move_to:{policy_target}" if delete_policy == "move_to_collection" else delete_policy
                            trash_paper_library_node(_pdir, selected_node_id, paper_policy=policy)
                            refresh_file_snapshots([_sources_path])
                            stash_git_backup_results()
                            clear_web_cache()
                            st.success(ui["saved"])
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

        trashed_nodes = [node for node in tree.nodes if node.status == "trashed"]
        if trashed_nodes:
            st.markdown(f"**{_l('collection_trash', 'Trash')}**")
            trash_options = {node.id: paths.get(node.id, node.title) for node in trashed_nodes}
            trashed_id = st.selectbox(
                _l("collection", "Collection"),
                options=list(trash_options),
                format_func=lambda ref: trash_options.get(ref, ref),
                key=_paper_library_key("trashed_node"),
            )
            t1, t2 = st.columns(2)
            with t1:
                if st.button(
                    _l("restore", "Restore"),
                    key=_paper_library_key(f"restore:{trashed_id}"),
                    icon=":material/restore:",
                    use_container_width=True,
                ):
                    try:
                        restore_paper_library_node(_pdir, trashed_id)
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(ui["saved"])
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with t2:
                if st.button(
                    _l("purge", "Permanently delete"),
                    key=_paper_library_key(f"purge:{trashed_id}"),
                    icon=":material/delete_forever:",
                    use_container_width=True,
                ):
                    try:
                        assert_files_current([_sources_path])
                        purge_paper_library_node(_pdir, trashed_id, paper_policy="move_to_unsorted")
                        refresh_file_snapshots([_sources_path])
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(ui["saved"])
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

        diagnostics = validate_paper_library(_pdir)
        if diagnostics:
            st.markdown(f"**{_l('library_diagnostics', 'Library diagnostics')}**")
            for item in diagnostics:
                st.warning(str(item))


def _render_library_bulk_actions(selected_rows: list[str], node_options: dict[str, str]) -> None:
    if not selected_rows:
        return
    current_node = str(st.session_state.get(_paper_library_key("node"), "") or "")
    with st.container(border=True):
        st.markdown(
            _l("bulk_selected_count", "**{count} selected**").format(count=len(selected_rows)),
            unsafe_allow_html=True,
        )
        b1, b2, b3 = st.columns(3)
        with b1:
            bulk_node = st.selectbox(
                _l("move_to_node", "Move to node"),
                options=list(node_options),
                format_func=lambda ref: node_options.get(ref, ref),
                key=f"bulk_node:{selected}",
            )
            if st.button(
                _l("move_to_node", "Move to node"),
                disabled=not selected_rows,
                icon=":material/drive_file_move:",
                key=_paper_library_key("bulk_move_to_node"),
                use_container_width=True,
            ):
                try:
                    assert_files_current([_sources_path])
                    move_papers_to_node(_pdir, selected_rows, bulk_node)
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if st.button(
                _l("add_to_node", "Add to node"),
                disabled=not selected_rows or not bulk_node,
                icon=":material/create_new_folder:",
                key=_paper_library_key("bulk_add_to_node"),
                use_container_width=True,
            ):
                try:
                    assert_files_current([_sources_path])
                    move_papers_to_node(_pdir, selected_rows, bulk_node, append=True)
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if st.button(
                _l("remove_from_current_collection", "Remove from current collection"),
                disabled=not selected_rows or not current_node,
                icon=":material/remove_circle:",
                key=_paper_library_key("bulk_remove_from_current_node"),
                use_container_width=True,
            ):
                try:
                    assert_files_current([_sources_path])
                    remove_papers_from_node(_pdir, selected_rows, current_node)
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with b2:
            bulk_status = st.selectbox(
                _l("set_status", "Set status"),
                SOURCE_STATUSES,
                key=f"bulk_status:{selected}",
                format_func=_status_label,
            )
            if st.button(
                _l("set_status", "Set status"),
                disabled=not selected_rows,
                icon=":material/rule:",
                use_container_width=True,
            ):
                try:
                    assert_files_current([_sources_path])
                    current = load_research_sources(selected)
                    for source_id in selected_rows:
                        update_research_source(current, source_id, status=bulk_status)
                    _save_sources(current, ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with b3:
            tag_text = st.text_input(_l("add_tags", "Add tags"), key=f"bulk_tags:{selected}")
            if st.button(
                _l("add_tags", "Add tags"),
                disabled=not selected_rows,
                icon=":material/sell:",
                use_container_width=True,
            ):
                try:
                    assert_files_current([_sources_path])
                    current = load_research_sources(selected)
                    by_id = current.by_id()
                    for source_id in selected_rows:
                        source = by_id.get(source_id)
                        if source is not None:
                            update_research_source(
                                current,
                                source_id,
                                tags=_unique_text([*source.tags, *_tags(tag_text)]),
                            )
                    _save_sources(current, ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


def _filter_paper_library_rows(
    rows: list[dict[str, object]],
    *,
    query: str,
    sort_mode: str,
) -> list[dict[str, object]]:
    clean_query = str(query or "").strip().lower()
    if clean_query:
        rows = [
            row
            for row in rows
            if clean_query
            in " ".join(
                [
                    str(row.get("title") or ""),
                    str(row.get("authors") or ""),
                    str(row.get("published") or ""),
                    str(row.get("venue") or ""),
                    str(row.get("tree_path") or ""),
                    str(row.get("summary") or ""),
                    str(row.get("notes") or ""),
                    " ".join(str(tag) for tag in row.get("tags", [])),
                    " ".join(str(badge) for badge in row.get("badges", [])),
                ]
            ).lower()
        ]
    if sort_mode == "title":
        return sorted(rows, key=lambda row: str(row.get("title") or "").lower())
    if sort_mode == "status":
        return sorted(rows, key=lambda row: (str(row.get("status") or ""), str(row.get("title") or "").lower()))
    if sort_mode == "claims":
        return sorted(rows, key=lambda row: int(row.get("claims_count") or 0), reverse=True)
    if sort_mode == "added":
        return sorted(rows, key=lambda row: str(getattr(row.get("source"), "captured_at", "") or ""), reverse=True)
    return sorted(rows, key=lambda row: str(row.get("last_read") or ""), reverse=True)


def _paper_component_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    sidecar_unavailable, _sidecar_message = _paper_library_sidecar_unavailable()
    for row in rows:
        source_id = str(row.get("id") or "")
        if not source_id:
            continue
        has_pdf = bool(getattr(row.get("source"), "metadata", {}).get("pdf_asset_ref"))
        out.append(
            {
                "id": source_id,
                "title": str(row.get("title") or source_id),
                "meta": _paper_primary_meta(row),
                "summary": _short_text(row.get("summary") or row.get("notes"), 220),
                "badges": [str(item) for item in row.get("badges", []) if str(item).strip()],
                "tags": [str(item) for item in row.get("tags", []) if str(item).strip()],
                "reader_url": _reader_view_url(source_id) if has_pdf and not sidecar_unavailable else "",
                "metrics": " · ".join(
                    [
                        f"{_l('annotations', 'Annotations')}: {row.get('annotations_count', 0)}",
                        f"{ui['chunk_refs']}: {row.get('chunks_count', 0)}",
                        f"{ui['research_claims']}: {row.get('claims_count', 0)}",
                        f"{ui['research_citations']}: {row.get('citations_count', 0)}",
                    ]
                ),
            }
        )
    return out


def _render_paper_card(row: dict[str, object], *, active: bool) -> None:
    source = row.get("source")
    source_id = str(row.get("id") or "")
    classes = "paper-card paper-card-active" if active else "paper-card"
    title = html.escape(str(row.get("title") or source_id))
    meta = html.escape(_paper_primary_meta(row))
    summary = html.escape(_short_text(row.get("summary") or row.get("notes"), 220))
    badges = _paper_badges_html(row)
    tags = _paper_tag_line(row)
    metrics = html.escape(
        " · ".join(
            [
                f"{_l('annotations', 'Annotations')}: {row.get('annotations_count', 0)}",
                f"{ui['chunk_refs']}: {row.get('chunks_count', 0)}",
                f"{ui['research_claims']}: {row.get('claims_count', 0)}",
                f"{ui['research_citations']}: {row.get('citations_count', 0)}",
            ]
        )
    )
    st.markdown(
        f"""
<div class="{classes}">
  <div class="paper-title">{title}</div>
  <div class="paper-meta">{meta}</div>
  <div>{badges}</div>
  {f'<div class="paper-summary">{summary}</div>' if summary else ''}
  {f'<div>{tags}</div>' if tags else ''}
  <div class="paper-meta">{metrics}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    a1, a2 = st.columns(2)
    with a1:
        if st.button(
            _l("details", "Details"),
            key=_paper_library_key(f"detail_button:{source_id}"),
            type="primary" if active else "secondary",
            icon=":material/article:",
            use_container_width=True,
        ):
            st.session_state[_paper_library_key("detail")] = source_id
            st.rerun()
    with a2:
        if getattr(source, "metadata", {}).get("pdf_asset_ref"):
            _render_sidecar_link_button(
                _l("open_reader", "Open Reader"),
                _reader_view_url(source_id),
                key=_paper_library_key(f"reader_link:{source_id}"),
                icon=":material/menu_book:",
                use_container_width=True,
            )
        else:
            st.button(
                _l("open_reader", "Open Reader"),
                key=_paper_library_key(f"reader_disabled:{source_id}"),
                disabled=True,
                icon=":material/menu_book:",
                use_container_width=True,
            )


def _render_paper_detail_panel(
    inbox,
    source,
    detail_row: dict[str, object],
    node_options: dict[str, str],
) -> None:
    annotations = load_paper_annotations(_pdir, source.id)
    translations = load_paper_translations(_pdir, source.id)
    pages_count = len(load_paper_pages(_pdir, source.id))
    segments_count = len(load_paper_segments(_pdir, source.id))
    source_chunks = load_chunks(_pdir, source.id)
    title = html.escape(source.title or source.id)
    meta = html.escape(_paper_primary_meta(detail_row))
    st.markdown(
        f"""
<div class="paper-detail-title">{title}</div>
<div class="paper-muted">{meta}</div>
<div>{_paper_badges_html(detail_row, limit=8)}</div>
""",
        unsafe_allow_html=True,
    )
    st.caption(f"`{source.id}`")

    m1, m2 = st.columns(2)
    m1.metric("PDF", "ready" if source.metadata.get("pdf_asset_ref") else "missing")
    m2.metric(_l("last_read_page", "Last page"), source.metadata.get("last_read_page", "") or "-")
    m3, m4 = st.columns(2)
    m3.metric(_l("segments", "Segments"), segments_count)
    m4.metric(_l("annotations", "Annotations"), len([ann for ann in annotations if ann.status == "active"]))
    m5, m6 = st.columns(2)
    m5.metric(ui["research_claims"], detail_row.get("claims_count", 0))
    m6.metric(ui["research_citations"], detail_row.get("citations_count", 0))

    st.markdown(f"**{_l('quick_actions', 'Quick actions')}**")
    q1, q2 = st.columns(2)
    with q1:
        if source.metadata.get("pdf_asset_ref"):
            _render_sidecar_link_button(
                _l("open_reader", "Open Reader"),
                _reader_view_url(source.id),
                key=_paper_library_key(f"detail_reader_link:{source.id}"),
                icon=":material/menu_book:",
                type="primary",
                use_container_width=True,
            )
        else:
            st.button(
                _l("open_reader", "Open Reader"),
                disabled=True,
                icon=":material/menu_book:",
                use_container_width=True,
            )
    with q2:
        if st.button(
            _l("run_extraction", "Run extraction"),
            key=_paper_library_key(f"extract:{source.id}"),
            disabled=not source.metadata.get("pdf_asset_ref"),
            icon=":material/auto_fix_high:",
            use_container_width=True,
        ):
            try:
                ensure_paper_reading_artifacts(_pdir, source.id)
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    q3, _ = st.columns(2)
    with q3:
        if st.button(
            _l("auto_chunk", "Auto chunk"),
            key=_paper_library_key(f"auto_chunk:{source.id}"),
            icon=":material/content_cut:",
            use_container_width=True,
        ):
            try:
                chunks = auto_chunk_paper(_pdir, source.id)
                stash_git_backup_results()
                clear_web_cache()
                st.success(_l("created_chunks", "Created chunks: {count}").format(count=len(chunks)))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with st.expander(_l("organize_paper", "Organize paper"), expanded=False):
        first_ref = source.library_node_refs[0] if source.library_node_refs else ""
        status_index = SOURCE_STATUSES.index(source.status) if source.status in SOURCE_STATUSES else 0
        node_refs = list(node_options)
        node_index = node_refs.index(first_ref) if first_ref in node_refs else 0
        with st.form(_paper_library_key(f"organize_form:{source.id}")):
            next_status = st.selectbox(
                _l("set_status", "Set status"),
                SOURCE_STATUSES,
                index=status_index,
                format_func=_status_label,
            )
            next_node = st.selectbox(
                _l("move_to_node", "Move to node"),
                node_refs,
                index=node_index,
                format_func=lambda ref: node_options.get(ref, ref),
            )
            next_tags = st.text_input(ui["tags"], value=", ".join(source.tags))
            saved = st.form_submit_button(ui["save"], type="primary")
        if saved:
            try:
                assert_files_current([_sources_path])
                current = load_research_sources(selected)
                update_research_source(
                    current,
                    source.id,
                    status=next_status,
                    tags=_tags(next_tags),
                    library_node_refs=[next_node] if next_node else [],
                )
                _save_sources(current, ui["saved"])
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    detail_tabs = st.tabs(
        [
            _l("notes", "Notes"),
            _l("artifacts", "Artifacts"),
            _l("metadata", "Metadata"),
        ]
    )
    with detail_tabs[0]:
        if source.summary:
            st.markdown(f"**{ui['summary']}**")
            st.write(source.summary)
        if source.notes:
            st.markdown(f"**{ui['notes']}**")
            st.write(source.notes)
        if source.url:
            st.link_button(_l("open_source", "Open source"), source.url, icon=":material/open_in_new:")
        if not any([source.summary, source.notes, source.url]):
            st.caption(_l("paper_notes_empty", "No summary, notes, or source URL yet."))
    with detail_tabs[1]:
        st.write(
            {
                "pdf_asset_ref": source.metadata.get("pdf_asset_ref", ""),
                "pages": source.metadata.get("page_count", "") or pages_count,
                "segments": segments_count,
                "chunks": len(source_chunks),
                "translations": len(translations),
                "structure_backend": source.metadata.get("structure_backend", ""),
                "structured_extracted_at": source.metadata.get("structured_extracted_at", ""),
            }
        )
        artifact_actions = st.columns(3)
        with artifact_actions[0]:
            if st.button(
                _l("extract_pages", "Extract pages"),
                key=_paper_library_key(f"detail_extract_pages:{source.id}"),
                disabled=not source.metadata.get("pdf_asset_ref"),
                use_container_width=True,
            ):
                try:
                    extract_paper_pages(_pdir, source.id)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with artifact_actions[1]:
            if st.button(
                _l("extract_segments", "Extract segments"),
                key=_paper_library_key(f"detail_extract_segments:{source.id}"),
                disabled=not source.metadata.get("pdf_asset_ref"),
                use_container_width=True,
            ):
                try:
                    extract_paper_segments(_pdir, source.id)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with artifact_actions[2]:
            if st.button(
                _l("run_structured_extraction", "Run structured extraction"),
                key=_paper_library_key(f"detail_structured:{source.id}"),
                disabled=not source.metadata.get("pdf_asset_ref"),
                use_container_width=True,
            ):
                try:
                    extract_paper_segments(_pdir, source.id, backend="grobid")
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        warnings = source.metadata.get("structured_extraction_warnings") or source.metadata.get("text_extraction_warnings") or []
        for warning in warnings:
            st.warning(str(warning))
        _render_grobid_status_block(source)
    with detail_tabs[2]:
        st.code(
            yaml.dump(
                {
                    "metadata": source.metadata,
                    "library_node_refs": source.library_node_refs,
                    "tags": source.tags,
                    "authors": source.authors,
                    "published": source.published,
                    "project_refs": source.project_refs,
                    "goal_refs": source.goal_refs,
                    "reading": source.reading.to_dict(),
                },
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
            language="yaml",
        )


def _render_paper_library(inbox) -> None:
    st.subheader(_l("paper_library", "Paper Library"))
    st.caption(
        _l(
            "paper_library_caption",
            "Organize papers into collections, continue reading, and move each source through extraction, claims, and review.",
        )
    )
    current_view = str(st.session_state.get(_paper_library_key("view"), "all") or "all")
    current_node = str(st.session_state.get(_paper_library_key("node"), "") or "")
    query = str(st.session_state.get(_paper_library_key("query"), "") or "")
    sort_mode = str(st.session_state.get(_paper_library_key("sort"), "recent") or "recent")
    detail_id = str(st.session_state.get(_paper_library_key("detail"), "") or "")
    workspace_url = _paper_library_workspace_url(
        view=current_view if current_view != "all" else "",
        node_id=current_node,
        query=query,
        sort=sort_mode if sort_mode != "recent" else "",
        detail_id=detail_id,
    )
    runtime, invalid_runtime = resolve_paper_library_runtime()
    workspace_ok: bool | None = None
    workspace_message = ""
    if runtime != "streamlit_component":
        workspace_ok, workspace_message = _paper_library_sidecar_status()
    if invalid_runtime:
        st.warning(
            _l(
                "paper_library_runtime_invalid",
                "Unknown Paper Library runtime; using 8502 link mode.",
            )
            + f" `{invalid_runtime}`"
        )

    _render_sidecar_link_button(
        _l("open_paper_library_workspace", "Open Paper Library Workspace"),
        workspace_url,
        key=f"paper_library_open_workspace:{selected}",
        icon=":material/open_in_new:",
        disabled=workspace_ok is False,
    )

    if workspace_ok is False:
        st.warning(
            _l(
                "paper_library_workspace_unavailable",
                "8502 Paper Library is not reachable right now; using the Streamlit fallback below.",
            )
            + (f" `{workspace_message}`" if workspace_message else "")
        )

    if runtime == "fastapi_iframe" and workspace_ok is not False:
        _render_iframe(workspace_url, height=1100, scrolling=True)
        return

    if runtime == "streamlit_component":
        _render_paper_library_streamlit_component(inbox)
        return

    show_fallback = workspace_ok is False or st.toggle(
        _l("paper_library_fallback", "Show Streamlit Paper Library fallback"),
        value=False,
        key=_paper_library_key("show_streamlit_fallback"),
    )
    if show_fallback:
        try:
            with st.container(border=True):
                _render_paper_library_streamlit_component(inbox, include_import=True)
        except TypeError:
            _render_paper_library_streamlit_component(inbox, include_import=True)


def _render_paper_library_streamlit_component(inbox, *, include_import: bool = True) -> None:
    _render_paper_library_styles()

    all_rows = paper_rows(_pdir, view="all")
    tree = load_paper_library_tree(_pdir)
    node_options = _node_options()
    current_view = str(st.session_state.setdefault(_paper_library_key("view"), "all") or "all")
    current_node = str(st.session_state.setdefault(_paper_library_key("node"), "") or "")
    if current_view not in _LIBRARY_VIEW_LABELS:
        current_view = "all"
        st.session_state[_paper_library_key("view")] = current_view
    active_node_ids = {node.id for node in tree.nodes if node.status != "trashed"}
    if current_node and current_node not in active_node_ids:
        current_node = ""
        st.session_state[_paper_library_key("node")] = ""

    metric_cols = st.columns(5)
    metric_cols[0].metric(_l("papers_total", "Papers"), len(all_rows))
    metric_cols[1].metric(_l("reading", "Reading"), _library_view_count(all_rows, "reading"))
    metric_cols[2].metric(_l("pdf_missing", "PDF missing"), _library_view_count(all_rows, "no_pdf"))
    metric_cols[3].metric(_l("needs_extraction", "Needs extraction"), _library_view_count(all_rows, "needs_extraction"))
    metric_cols[4].metric(_l("claims_need_review", "Claims review"), _library_view_count(all_rows, "claims_need_review"))

    if include_import:
        search_results_open = bool(st.session_state.get(_search_state_key("results")) or [])
        with st.expander(
            _l("find_import_papers", "Find and import papers"),
            expanded=search_results_open,
        ):
            _render_paper_search(inbox, embedded=True)

    selected_paper_ids_for_tree = [
        str(item)
        for item in st.session_state.get(_paper_library_key("bulk_select"), []) or []
        if str(item).strip()
    ]
    if paper_library_component_available():
        toolbar = st.columns([2.2, 1])
        with toolbar[0]:
            query = st.text_input(
                _l("search_library", "Search title, author, tag, note..."),
                key=_paper_library_key("query"),
                label_visibility="collapsed",
                placeholder=_l("search_library", "Search title, author, tag, note..."),
            )
        with toolbar[1]:
            sort_mode = st.selectbox(
                _l("sort", "Sort"),
                ["recent", "added", "title", "status", "claims"],
                format_func=lambda item: {
                    "recent": _l("sort_recent", "Recently read"),
                    "added": _l("sort_added", "Recently added"),
                    "title": ui["title_label"],
                    "status": ui["status"],
                    "claims": ui["research_claims"],
                }.get(item, item),
                key=_paper_library_key("sort"),
                label_visibility="collapsed",
            )
        payload = build_paper_library_payload(
            _pdir,
            current_view=current_view,
            current_node=current_node,
            query=str(query or ""),
            sort_mode=str(sort_mode or "recent"),
            selected_paper_ids=selected_paper_ids_for_tree,
            detail_id=str(st.session_state.get(_paper_library_key("detail"), "") or ""),
            user_id=user.id,
            reader_base="" if _paper_library_sidecar_unavailable()[0] else _reader_api_base(),
        )
        if payload.get("detail_id"):
            st.session_state[_paper_library_key("detail")] = str(payload.get("detail_id") or "")
        component_event = st_paper_library_tree(
            payload=payload,
            key=_paper_library_key("workbench_component"),
            height=860,
        )
        _handle_paper_library_component_event(component_event)
        _render_library_collection_manager(tree, node_options)
        with st.expander(_l("parser_status", "Parser status"), expanded=False):
            _render_grobid_status_block()
        return

    left, middle, right = st.columns([0.23, 0.47, 0.30], gap="large")
    with left:
        if paper_library_component_available():
            component_event = st_paper_library_tree(
                payload=_paper_library_component_payload(
                    tree,
                    all_rows,
                    current_view=current_view,
                    current_node=current_node,
                    selected_paper_ids=selected_paper_ids_for_tree,
                ),
                key=_paper_library_key("tree_component"),
                height=760,
            )
            _handle_paper_library_component_event(component_event)
            _render_library_collection_manager(tree, node_options)
        else:
            _render_library_view_group(
                "library",
                "Library",
                _LIBRARY_VIEW_GROUPS[0][2],
                all_rows,
                current_view,
                current_node,
            )
            st.divider()
            st.markdown(f"**{_l('collections', 'Collections')}**")
            if st.button(
                _l("clear_tree_filter", "All collections"),
                key=_paper_library_key("clear_node"),
                type="primary" if not current_node else "secondary",
                use_container_width=True,
            ):
                st.session_state[_paper_library_key("view")] = "all"
                st.session_state[_paper_library_key("node")] = ""
                st.session_state.pop(_paper_library_key("detail"), None)
                st.rerun()
            _paper_tree_buttons(tree, all_rows)
            _render_library_collection_manager(tree, node_options)
            st.divider()
            st.markdown(f"**{_l('technical_taxonomy', 'Technical Taxonomy')}**")
            for taxonomy_id, fallback in _TECHNICAL_TAXONOMY_LABELS:
                st.button(
                    f"{_l(f'technical_taxonomy_{taxonomy_id}', fallback)} (0)",
                    key=_paper_library_key(f"taxonomy:{taxonomy_id}"),
                    disabled=True,
                    use_container_width=True,
                )
            st.divider()
            _render_library_view_group(
                "work_queue",
                "Work Queue",
                _LIBRARY_VIEW_GROUPS[1][2],
                all_rows,
                current_view,
                current_node,
            )
            st.divider()
            _render_library_view_group(
                "system",
                "System",
                _LIBRARY_VIEW_GROUPS[2][2],
                all_rows,
                current_view,
                current_node,
            )
        with st.expander(_l("parser_status", "Parser status"), expanded=False):
            _render_grobid_status_block()

    with middle:
        toolbar = st.columns([2.2, 1, 1])
        with toolbar[0]:
            query = st.text_input(
                _l("search_library", "Search title, author, tag, note..."),
                key=_paper_library_key("query"),
                label_visibility="collapsed",
                placeholder=_l("search_library", "Search title, author, tag, note..."),
            )
        with toolbar[1]:
            sort_mode = st.selectbox(
                _l("sort", "Sort"),
                ["recent", "added", "title", "status", "claims"],
                format_func=lambda item: {
                    "recent": _l("sort_recent", "Recently read"),
                    "added": _l("sort_added", "Recently added"),
                    "title": ui["title_label"],
                    "status": ui["status"],
                    "claims": ui["research_claims"],
                }.get(item, item),
                key=_paper_library_key("sort"),
                label_visibility="collapsed",
            )
        with toolbar[2]:
            show_table = st.toggle(
                _l("table_view", "Table"),
                value=False,
                key=_paper_library_key("table_view"),
            )

        rows = paper_rows(_pdir, view=current_view, node_id=current_node)
        clean_query = str(query or "").strip().lower()
        if clean_query:
            rows = [
                row
                for row in rows
                if clean_query
                in " ".join(
                    [
                        str(row.get("title") or ""),
                        str(row.get("authors") or ""),
                        str(row.get("published") or ""),
                        str(row.get("venue") or ""),
                        str(row.get("tree_path") or ""),
                        str(row.get("summary") or ""),
                        str(row.get("notes") or ""),
                        " ".join(str(tag) for tag in row.get("tags", [])),
                        " ".join(str(badge) for badge in row.get("badges", [])),
                    ]
                ).lower()
            ]
        if sort_mode == "title":
            rows = sorted(rows, key=lambda row: str(row.get("title") or "").lower())
        elif sort_mode == "status":
            rows = sorted(rows, key=lambda row: (str(row.get("status") or ""), str(row.get("title") or "").lower()))
        elif sort_mode == "claims":
            rows = sorted(rows, key=lambda row: int(row.get("claims_count") or 0), reverse=True)
        elif sort_mode == "added":
            rows = sorted(rows, key=lambda row: str(getattr(row.get("source"), "captured_at", "") or ""), reverse=True)
        else:
            rows = sorted(rows, key=lambda row: str(row.get("last_read") or ""), reverse=True)

        paper_ids = [str(row.get("id")) for row in rows]
        selected_rows = st.multiselect(
            _l("select_papers", "Select papers"),
            options=paper_ids,
            format_func=lambda sid: _source_label(inbox, sid),
            key=_paper_library_key("bulk_select"),
        )
        _render_library_bulk_actions(selected_rows, node_options)

        active_label = _LIBRARY_VIEW_LABELS.get(current_view, current_view)
        if current_node:
            active_label = node_options.get(current_node, current_node)
        st.caption(
            _l("library_result_count", "{count} papers in {view}").format(
                count=len(rows),
                view=active_label,
            )
        )
        if not rows:
            st.info(_l("library_empty", "No papers match this view."))
        elif show_table:
            display_rows = []
            for row in rows:
                display_row = {
                    key: value
                    for key, value in row.items()
                    if key not in {"source", "diagnostics"}
                }
                display_row["tags"] = ", ".join(str(item) for item in row.get("tags", []))
                display_row["badges"] = ", ".join(str(item) for item in row.get("badges", []) if str(item).strip())
                display_rows.append(display_row)
            st.dataframe(display_rows, use_container_width=True, hide_index=True)
        else:
            detail_id = str(st.session_state.get(_paper_library_key("detail"), "") or "")
            if detail_id not in paper_ids and paper_ids:
                detail_id = paper_ids[0]
                st.session_state[_paper_library_key("detail")] = detail_id
            for row in rows:
                _render_paper_card(row, active=str(row.get("id")) == detail_id)

    with right:
        detail_id = str(st.session_state.get(_paper_library_key("detail"), "") or "")
        by_id = inbox.by_id()
        if not detail_id and rows:
            detail_id = str(rows[0].get("id") or "")
            st.session_state[_paper_library_key("detail")] = detail_id
        source = by_id.get(detail_id)
        if source is None:
            st.info(_l("select_paper_detail_hint", "Select a paper to see details and actions."))
            return
        detail_row = next(
            (row for row in all_rows if str(row.get("id")) == detail_id),
            next((row for row in rows if str(row.get("id")) == detail_id), {}),
        )
        _render_paper_detail_panel(inbox, source, detail_row, node_options)


def _segment_dicts(source_id: str, limit: int = 20) -> list[dict[str, object]]:
    return [segment.to_dict() for segment in load_paper_segments(_pdir, source_id)[:limit]]


def _reader_key(source_id: str, name: str) -> str:
    return f"paper_reader:{selected}:{source_id}:{name}"


def _set_reader_action_status(source_id: str, action: str, phase: str, message: str) -> None:
    st.session_state[_reader_key(source_id, "last_action_status")] = {
        "action": action,
        "phase": phase,
        "message": message,
    }


def _payload_text(payload: dict, *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _payload_list(payload: dict, *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            values.extend(_tags(value))
        elif isinstance(value, (list, tuple, set)):
            values.extend(str(item).strip() for item in value if str(item).strip())
        elif value is not None and str(value).strip():
            values.append(str(value).strip())
    return _unique_text(values)


def _payload_int(payload: dict, key: str, default: int = 0) -> int:
    try:
        return int(payload.get(key) or default)
    except (TypeError, ValueError):
        return default


def _reader_requested_pages(source_id: str) -> set[int]:
    store = st.session_state.setdefault("reader_requested_pages", {})
    if not isinstance(store, dict):
        store = {}
        st.session_state["reader_requested_pages"] = store
    values = store.setdefault(source_id, set())
    if isinstance(values, set):
        return values
    if isinstance(values, list):
        cleaned = {int(item) for item in values if str(item).strip().isdigit()}
        store[source_id] = cleaned
        return cleaned
    store[source_id] = set()
    return store[source_id]


def _reader_event_identity(event: dict) -> str:
    explicit = event.get("event_id") or event.get("id")
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    explicit = explicit or payload.get("event_id") or payload.get("idempotency_key")
    if explicit:
        return str(explicit)
    return yaml.dump(event, allow_unicode=True, sort_keys=True)


def _save_reader_progress(source_id: str, page: int) -> None:
    page = max(1, int(page or 1))
    saved_key = _reader_key(source_id, "saved_progress_page")
    if st.session_state.get(saved_key) == page:
        return
    current = load_research_sources(selected)
    src = current.by_id().get(source_id)
    if src is None:
        return
    metadata = dict(src.metadata or {})
    metadata["last_read_page"] = page
    metadata["last_read_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    assert_files_current([_sources_path])
    update_research_source(current, source_id, metadata=metadata, status="reading")
    save_research_sources(selected, current)
    refresh_file_snapshots([_sources_path])
    stash_git_backup_results()
    clear_web_cache()
    st.session_state[saved_key] = page


def _save_reader_state(source_id: str, payload: dict) -> None:
    page = max(1, _payload_int(payload, "page", _payload_int(payload, "primary_page", 1)))
    visible_pages = clean_page_list(
        payload.get("visible_pages") if isinstance(payload.get("visible_pages"), list) else payload.get("last_visible_pages")
    )
    metadata: dict[str, object] = {
        "last_read_page": page,
        "last_read_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    for key in (
        "reader_mode",
        "scale_mode",
        "active_tab",
        "target_lang",
        "focused_annotation_id",
        "focused_chunk_id",
        "active_left_tab",
        "active_translation_anchor",
    ):
        value = _payload_text(payload, key)
        if value:
            metadata[key] = value
    for key in ("compare_split_ratio", "panel_width"):
        if key in payload:
            metadata[key] = _payload_int(payload, key, int(metadata.get(key) or (50 if key == "compare_split_ratio" else 340)))
    if "side_panel_collapsed" in payload:
        metadata["side_panel_collapsed"] = bool(payload.get("side_panel_collapsed"))
    if "left_rail_collapsed" in payload:
        metadata["left_rail_collapsed"] = bool(payload.get("left_rail_collapsed"))
    if "translation_source_visible" in payload:
        metadata["translation_source_visible"] = bool(payload.get("translation_source_visible"))
    if visible_pages:
        metadata["last_visible_pages"] = visible_pages
    current = load_research_sources(selected)
    if current.by_id().get(source_id) is None:
        return
    assert_files_current([_sources_path])
    update_research_source(current, source_id, metadata={**dict(current.by_id()[source_id].metadata or {}), **metadata}, status="reading")
    save_research_sources(selected, current)
    refresh_file_snapshots([_sources_path])
    stash_git_backup_results()
    clear_web_cache()


def _translation_counts_for_segments(source_id: str, target_lang: str = "zh") -> dict[str, int]:
    segments = load_paper_segments(_pdir, source_id)
    translations = {
        row.segment_id: row
        for row in load_paper_translations(_pdir, source_id)
        if row.segment_id and row.target_lang == target_lang
    }
    counts = {"translated": 0, "missing": 0, "stale": 0, "failed": 0}
    for segment in segments:
        row = translations.get(segment.segment_id)
        if row is None:
            counts["missing"] += 1
        elif row.status == "failed":
            counts["failed"] += 1
        elif row.status == "stale" or row.source_hash != segment.text_hash:
            counts["stale"] += 1
        elif row.translated_text:
            counts["translated"] += 1
        else:
            counts["missing"] += 1
    return counts


def _selection_segments(payload: dict, segment_rows) -> list[dict[str, object]]:
    refs = set(
        _payload_list(
            payload,
            "segment_refs",
            "segment_ids",
            "segment_id",
            "scope_refs",
            "scope_ref",
        )
    )
    if refs:
        return [segment.to_dict() for segment in segment_rows if segment.segment_id in refs]
    selected_text = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
    if not selected_text:
        return []
    selected_hash = _payload_text(payload, "selected_text_hash", "text_hash", "source_hash")
    if not selected_hash:
        selected_hash = text_hash(selected_text)
    synthetic_id = f"selection:{selected_hash.rsplit(':', 1)[-1][:16]}"
    page = _payload_int(payload, "page")
    locator = _payload_text(payload, "locator") or (f"p. {page}" if page else "")
    return [
        {
            "segment_id": _payload_text(payload, "segment_id") or synthetic_id,
            "source_id": payload.get("source_id", ""),
            "scope_type": "selection",
            "scope_ref": selected_hash,
            "page": page,
            "order": 0,
            "section_path": [],
            "kind": "selection",
            "text": selected_text,
            "text_hash": selected_hash,
            "locator": locator,
            "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
        }
    ]


def _selection_payload(payload: dict, segment_rows) -> dict[str, object]:
    selected_text = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
    if not selected_text:
        refs = set(_payload_list(payload, "segment_refs", "segment_ids", "segment_id"))
        selected_text = "\n\n".join(segment.text for segment in segment_rows if segment.segment_id in refs)
    page = _payload_int(payload, "page")
    locator = _payload_text(payload, "locator") or (f"p. {page}" if page else "")
    return {
        "source_id": _payload_text(payload, "source_id") or "",
        "page": page,
        "selected_text": selected_text,
        "selected_text_hash": _payload_text(payload, "selected_text_hash")
        or (text_hash(selected_text) if selected_text else ""),
        "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
        "segment_refs": _payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
        "locator": locator,
        "event_id": _payload_text(payload, "event_id"),
    }


def _update_or_delete_paper_annotation(source_id: str, payload: dict, *, delete: bool = False) -> str:
    annotation_id = _payload_text(payload, "annotation_id", "id")
    if not annotation_id:
        raise ValueError("Reader annotation update needs annotation_id.")
    annotations = load_paper_annotations(_pdir, source_id)
    updated = ""
    for ann in annotations:
        if ann.id != annotation_id:
            continue
        if delete:
            ann.status = "deleted"
        else:
            selected_text = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
            if selected_text:
                ann.selected_text = selected_text
                ann.selected_text_hash = _payload_text(payload, "selected_text_hash") or text_hash(selected_text)
            if "note" in payload:
                ann.note = str(payload.get("note") or "").strip()
            color = _payload_text(payload, "color")
            if color:
                ann.color = color
            locator = _payload_text(payload, "locator")
            if locator:
                ann.locator = locator
            page = _payload_int(payload, "page", ann.page)
            ann.page = page
            tags = _payload_list(payload, "tags")
            if tags:
                ann.tags = tags
            segment_refs = _payload_list(payload, "segment_refs", "segment_ids", "segment_id")
            if segment_refs:
                ann.segment_refs = segment_refs
            if isinstance(payload.get("rects"), list):
                ann.rects = payload["rects"]
        ann.updated = datetime.now().astimezone().isoformat(timespec="seconds")
        updated = ann.id
        break
    if not updated:
        raise ValueError(f"Unknown paper annotation: {annotation_id}")
    save_paper_annotations(_pdir, source_id, annotations)
    return updated


def _private_source_refs_for_citations(citation_ids: list[str]) -> list[str]:
    source_map = load_research_sources(selected).by_id()
    citations = {
        citation.id: citation
        for citation in load_research_citations(_pdir)
    }
    selected_citations = [
        citations[ref]
        for ref in citation_ids
        if ref in citations
    ] if citation_ids else list(citations.values())
    refs = [
        citation.source_id
        for citation in selected_citations
        if citation.source_id
        and source_map.get(citation.source_id) is not None
        and source_map[citation.source_id].visibility == "private"
    ]
    return _unique_text(refs)


def _context_segments(payload: dict, segment_rows, *, limit: int = 30) -> list[dict[str, object]]:
    picked = _selection_segments(payload, segment_rows)
    if picked:
        return picked
    return [segment.to_dict() for segment in segment_rows[:limit]]


def _selection_text(payload: dict, segment_rows) -> str:
    text = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
    if text:
        return text
    refs = {
        row.get("segment_id")
        for row in _selection_segments(payload, segment_rows)
        if row.get("segment_id")
    }
    if not refs:
        return ""
    return "\n\n".join(segment.text for segment in segment_rows if segment.segment_id in refs)


def _store_reader_ai_result(source_id: str, action: str, result) -> None:
    st.session_state[_reader_key(source_id, "ai_result")] = {
        "action": action,
        "structured": result.structured or {},
        "warnings": list(result.warnings),
    }


def _render_reader_ai_result(source_id: str) -> None:
    result = st.session_state.get(_reader_key(source_id, "ai_result"))
    if not isinstance(result, dict):
        return
    with st.expander(_l("reader_ai_result", "Reader AI result"), expanded=False):
        st.caption(str(result.get("action") or "AI"))
        for warning in result.get("warnings") or []:
            st.warning(str(warning))
        st.code(
            yaml.dump(result.get("structured") or {}, allow_unicode=True, sort_keys=False),
            language="yaml",
        )


def _render_reader_translation_summary(source_id: str) -> None:
    summary = st.session_state.get(_reader_key(source_id, "translation_summary"))
    if not isinstance(summary, dict):
        return
    with st.expander(_l("translation_summary", "Translation summary"), expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(_l("translated", "Translated"), summary.get("translated", 0))
        c2.metric(_l("missing", "Missing"), summary.get("missing", 0))
        c3.metric(_l("stale", "Stale"), summary.get("stale", 0))
        c4.metric(_l("failed", "Failed"), summary.get("failed", 0))
        if summary.get("warnings"):
            for warning in summary.get("warnings") or []:
                st.warning(str(warning))


def _handle_reader_component_event(
    source_id: str,
    event: object,
    *,
    segment_rows,
    annotation_rows,
    chunk_rows,
) -> bool:
    if not isinstance(event, dict):
        return False
    action = str(event.get("action") or event.get("type") or "").strip()
    if not action:
        return False
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    payload_source = str(payload.get("source_id") or event.get("source_id") or source_id).strip()
    if payload_source and payload_source != source_id:
        st.warning(f"Ignored reader event for {payload_source}; current source is {source_id}.")
        return True

    identity = _reader_event_identity(event)
    last_key = _reader_key(source_id, "last_event")
    if st.session_state.get(last_key) == identity:
        return True
    st.session_state[last_key] = identity

    try:
        if action == "selection_created":
            st.session_state[_reader_key(source_id, "selection")] = _selection_payload(payload, segment_rows)
            return True

        if action == "page_changed":
            page = _payload_int(payload, "page", 1)
            st.session_state[_reader_key(source_id, "page")] = max(1, page)
            return True

        if action == SAVE_PROGRESS:
            page = _payload_int(payload, "page", _payload_int(payload, "primary_page", 1))
            st.session_state[_reader_key(source_id, "page")] = max(1, page)
            _save_reader_progress(source_id, max(1, page))
            st.success(ui["saved"])
            return True

        if action == READER_STATE_CHANGED:
            page = _payload_int(payload, "page", _payload_int(payload, "primary_page", 1))
            visible = clean_page_list(payload.get("visible_pages"))
            st.session_state[_reader_key(source_id, "page")] = max(1, page)
            st.session_state[_reader_key(source_id, "visible_pages")] = visible
            _reader_requested_pages(source_id).update(visible or [max(1, page)])
            _save_reader_state(source_id, payload)
            return True

        if action == "viewport_changed":
            page = _payload_int(payload, "primary_page", _payload_int(payload, "page", 1))
            visible = clean_page_list(payload.get("visible_pages"))
            st.session_state[_reader_key(source_id, "page")] = max(1, page)
            st.session_state[_reader_key(source_id, "visible_pages")] = visible
            return True

        if action in {REQUEST_READER_CONTEXT, REQUEST_PAGE_PREVIEWS}:
            pages = clean_page_list(payload.get("pages") or payload.get("visible_pages"))
            if not pages:
                page = _payload_int(payload, "page", 1)
                pages = [max(1, page)]
            _reader_requested_pages(source_id).update(pages)
            st.session_state[_reader_key(source_id, "preview_page")] = pages[0]
            return True

        if action == REQUEST_PAGE_PREVIEW:
            page = _payload_int(payload, "page", 1)
            st.session_state[_reader_key(source_id, "preview_page")] = max(1, page)
            _reader_requested_pages(source_id).add(max(1, page))
            return True

        if action == "generate_review_card":
            source = load_research_sources(selected).by_id().get(source_id)
            result = generate_paper_review_card(
                selected,
                source_id,
                source=source.to_dict() if source is not None else {"id": source_id},
                segments=[row.to_dict() for row in segment_rows],
                chunks=[row.to_dict() for row in chunk_rows],
                annotations=[row.to_dict() for row in annotation_rows],
                require_review=False,
            )
            _store_reader_ai_result(source_id, action, result)
            if isinstance(result.structured, dict):
                save_paper_analysis(_pdir, source_id, result.structured)
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
                _set_reader_action_status(source_id, action, "done", ui["saved"])
            for warning in result.warnings:
                st.warning(str(warning))
            if result.warnings and not isinstance(result.structured, dict):
                _set_reader_action_status(source_id, action, "error", str(result.warnings[0]))
            return True

        if action == CODEX_DEEP_READ:
            ctx = ReaderActionContext(
                profile_name=selected,
                profile_path=_pdir,
                user_id=getattr(user, "id", "local"),
                source_id=source_id,
            )
            result = handle_reader_action(ctx, action, payload)
            st.session_state[_reader_key(source_id, "ai_result")] = {
                "action": action,
                "structured": result.data.get("structured") if isinstance(result.data, dict) else {},
                "warnings": list(result.warnings),
            }
            if result.ok:
                stash_git_backup_results()
                clear_web_cache()
                st.success(result.message or ui["saved"])
                _set_reader_action_status(source_id, action, "done", result.message or ui["saved"])
            else:
                st.warning(result.message or "Deep read did not return a candidate.")
                _set_reader_action_status(source_id, action, "error", result.message or "Deep read failed")
            for warning in result.warnings:
                st.warning(str(warning))
            return True

        if action in {ANNOTATION_CREATE, "create_annotation"}:
            ann = create_paper_annotation(
                _pdir,
                source_id,
                _payload_text(payload, "selected_text", "selection_text", "text", "quote"),
                kind=_payload_text(payload, "kind") or "highlight",
                page=_payload_int(payload, "page"),
                locator=_payload_text(payload, "locator"),
                note=_payload_text(payload, "note"),
                color=_payload_text(payload, "color") or "yellow",
                tags=_payload_list(payload, "tags"),
                segment_refs=_payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
                rects=payload.get("rects") if isinstance(payload.get("rects"), list) else [],
            )
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["created"].format(id=ann.id))
            st.session_state[_reader_key(source_id, "focus_annotation_id")] = ann.id
            return True

        if action == ANNOTATION_UPDATE:
            annotation_id = _update_or_delete_paper_annotation(source_id, payload)
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["saved"])
            st.session_state[_reader_key(source_id, "focus_annotation_id")] = annotation_id
            return True

        if action == ANNOTATION_DELETE:
            annotation_id = _update_or_delete_paper_annotation(source_id, payload, delete=True)
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["saved"])
            st.session_state[_reader_key(source_id, "focus_annotation_id")] = annotation_id
            return True

        if action in {CREATE_CHUNK_FROM_SELECTION, "create_chunk"}:
            text = _selection_text(payload, segment_rows)
            chunk = create_chunk(
                _pdir,
                source_id,
                text,
                kind=_payload_text(payload, "kind") or "excerpt",
                title=_payload_text(payload, "title"),
                locator=_payload_text(payload, "locator"),
                metadata={
                    "page": _payload_int(payload, "page"),
                    "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
                    "segment_refs": _payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
                    "annotation_id": _payload_text(payload, "annotation_id"),
                    "source": "reader_component",
                },
            )
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["created"].format(id=chunk.id))
            st.session_state[_reader_key(source_id, "focus_chunk_id")] = chunk.id
            return True

        if action == TRANSLATE_FULL_PAPER:
            summary = translate_full_paper(
                _pdir,
                source_id,
                target_lang=_payload_text(payload, "target_lang", "language") or "zh",
                mode=_payload_text(payload, "mode") or "missing_or_stale",
                scope_strategy=_payload_text(payload, "scope_strategy") or "auto",
                ai_profile=selected,
                require_review=False,
            )
            st.session_state[_reader_key(source_id, "translation_summary")] = summary
            stash_git_backup_results()
            clear_web_cache()
            st.success(
                _l("translation_full_saved", "Full-paper translation updated: {count} row(s).").format(
                    count=summary.get("updated", 0)
                )
            )
            _set_reader_action_status(
                source_id,
                action,
                "done",
                _l("translation_full_saved", "Full-paper translation updated: {count} row(s).").format(
                    count=summary.get("updated", 0)
                ),
            )
            for warning in summary.get("warnings") or []:
                st.warning(str(warning))
            return True

        if action in {TRANSLATE_VISIBLE_PAGES, RETRY_TRANSLATION_SCOPE}:
            ctx = ReaderActionContext(
                profile_name=selected,
                profile_path=_pdir,
                user_id=getattr(user, "id", "local"),
                source_id=source_id,
            )
            result = handle_reader_action(ctx, action, payload)
            summary = result.data.get("summary") if isinstance(result.data, dict) else {}
            if not isinstance(summary, dict):
                summary = {}
            saved = int(summary.get("saved") or 0)
            if result.ok and saved:
                stash_git_backup_results()
                clear_web_cache()
                message = _l("visible_pages_translation_saved", "Visible pages translated: saved {count} row(s).").format(
                    count=saved
                )
                st.success(message)
                _set_reader_action_status(source_id, action, "done", message)
            elif result.ok:
                message = result.message or _l(
                    "visible_pages_translation_saved_none",
                    "No visible-page translations were saved. AI returned {count} valid row(s).",
                ).format(count=summary.get("ai_rows", 0))
                st.info(message)
                _set_reader_action_status(source_id, action, "done", message)
            else:
                message = result.message or _l(
                    "visible_page_translation_no_text",
                    "No extracted text is available for the visible page yet. Use Paper Library > Artifacts to run extraction.",
                )
                st.warning(message)
                _set_reader_action_status(source_id, action, "error", message)
            st.caption(
                " · ".join(
                    [
                        f"pages={','.join(str(page) for page in summary.get('requested_pages', []) or []) or '-'}",
                        f"scope={summary.get('scope') or '-'}",
                        f"segments={summary.get('segments_selected', 0)}",
                        f"ai_rows={summary.get('ai_rows', 0)}",
                        f"saved={summary.get('saved', 0)}",
                        f"skipped={summary.get('skipped', 0)}",
                    ]
                )
            )
            for warning in result.warnings:
                st.warning(str(warning))
            return True

        if action in {TRANSLATE_SELECTION, "translate_segment"}:
            selected_text = _selection_text(payload, segment_rows)
            target_lang = _payload_text(payload, "target_lang", "language") or "zh"
            translation_payload = dict(payload)
            if action == "translate_selection" and selected_text:
                for key in ("segment_refs", "segment_ids", "segment_id", "scope_refs", "scope_ref"):
                    translation_payload.pop(key, None)
            segment_refs = set(_payload_list(translation_payload, "segment_refs", "segment_ids", "segment_id"))
            segments = _selection_segments(translation_payload, segment_rows)
            if not segments:
                raise ValueError("Reader translation needs selected text or segment refs.")
            result = translate_paper_segments(
                selected,
                source_id,
                segments,
                target_lang=target_lang,
                require_review=False,
            )
            _store_reader_ai_result(source_id, action, result)
            translations = []
            if isinstance(result.structured, dict):
                translations = [
                    normalize_translation_row(row, source_id=source_id, target_lang=target_lang)
                    for row in result.structured.get("translations", [])
                    if isinstance(row, dict)
                ]
            if segment_refs:
                segment_ids = {segment.segment_id for segment in segment_rows}
                savable = [
                    {
                        **row,
                        "scope_type": "segment",
                        "scope_ref": str(row.get("segment_id") or row.get("scope_ref") or ""),
                    }
                    for row in translations
                    if str(row.get("segment_id") or row.get("scope_ref") or "") in segment_ids
                ]
            else:
                selected_hash = _payload_text(payload, "selected_text_hash", "text_hash", "source_hash")
                if not selected_hash and selected_text:
                    selected_hash = text_hash(selected_text)
                synthetic_ids = {
                    str(segment.get("segment_id") or "")
                    for segment in segments
                    if isinstance(segment, dict)
                }
                savable = []
                for row in translations:
                    row_ref = str(row.get("segment_id") or row.get("scope_ref") or "")
                    if synthetic_ids and row_ref and row_ref not in synthetic_ids:
                        continue
                    savable.append(
                        {
                            **row,
                            "scope_type": "selection",
                            "scope_ref": selected_hash,
                            "segment_id": "",
                            "source_hash": selected_hash,
                            "source_text": selected_text,
                            "target_lang": target_lang,
                        }
                    )
            if savable:
                upsert_paper_translations(_pdir, source_id, savable)
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
            for warning in result.warnings:
                st.warning(str(warning))
            return True

        if action == CREATE_CITATION:
            selected_text = _selection_text(payload, segment_rows)
            chunk_id = _payload_text(payload, "chunk_id", "chunk_ref")
            if not chunk_id and selected_text:
                chunk = create_chunk(
                    _pdir,
                    source_id,
                    selected_text,
                    kind="excerpt",
                    locator=_payload_text(payload, "locator"),
                    metadata={
                        "page": _payload_int(payload, "page"),
                        "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
                        "segment_refs": _payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
                        "annotation_id": _payload_text(payload, "annotation_id"),
                        "source": "reader_component",
                    },
                )
                chunk_id = chunk.id
            claim_id = _payload_text(payload, "claim_id", "research_claim_id")
            if not claim_id:
                claim_text = _payload_text(payload, "claim_text", "text") or selected_text
                if not claim_text:
                    raise ValueError("Reader citation needs a claim id, selected text, or claim text.")
                claim = upsert_research_claim(
                    _pdir,
                    claim_text,
                    status="draft",
                    type=_payload_text(payload, "claim_type") or "finding",
                    source_refs=[source_id],
                    chunk_refs=[chunk_id] if chunk_id else [],
                    confidence="medium",
                    rationale=_l("reader_citation_candidate", "Created from Reader selection; review before promotion."),
                    generated_by="reader_component",
                )
                claim_id = claim.id
            citation = create_citation(
                _pdir,
                claim_id,
                source_id=source_id,
                chunk_id=chunk_id,
                locator=_payload_text(payload, "locator"),
                quote=_payload_text(payload, "quote", "selected_text", "selection_text", "text"),
                bibliography=_payload_text(payload, "bibliography"),
                note=_payload_text(payload, "note"),
            )
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["created"].format(id=citation.id))
            return True

        if action == EXPLAIN_SELECTION:
            selected_text = _selection_text(payload, segment_rows)
            if not selected_text:
                raise ValueError("Reader explanation needs selected text or segment refs.")
            result = explain_paper_selection(
                selected,
                source_id,
                selected_text,
                payload={
                    "page": _payload_int(payload, "page"),
                    "locator": _payload_text(payload, "locator"),
                    "segments": _context_segments(payload, segment_rows, limit=8),
                    "annotations": [row.to_dict() for row in annotation_rows[:20]],
                },
            )
            _store_reader_ai_result(source_id, action, result)
            for warning in result.warnings:
                st.warning(str(warning))
            return True

        if action == ASK_PAPER:
            question = _payload_text(payload, "question", "prompt", "text")
            if not question:
                raise ValueError("Reader question cannot be blank.")
            result = answer_paper_question(
                selected,
                source_id,
                question,
                payload={
                    "segments": _context_segments(payload, segment_rows, limit=30),
                    "annotations": [row.to_dict() for row in annotation_rows[:30]],
                    "chunks": [row.to_dict() for row in chunk_rows[:30]],
                },
            )
            _store_reader_ai_result(source_id, action, result)
            for warning in result.warnings:
                st.warning(str(warning))
            return True

        if action == "jump_to_annotation":
            annotation_id = _payload_text(payload, "annotation_id", "id")
            if not annotation_id:
                raise ValueError("Reader jump needs annotation_id.")
            st.session_state[_reader_key(source_id, "focus_annotation_id")] = annotation_id
            return True

        if action == "jump_to_chunk":
            chunk_id = _payload_text(payload, "chunk_id", "id")
            if not chunk_id:
                raise ValueError("Reader jump needs chunk_id.")
            st.session_state[_reader_key(source_id, "focus_chunk_id")] = chunk_id
            return True

        st.warning(f"Unsupported reader action: {action or event}")
        return True
    except Exception as exc:
        st.error(str(exc))
        return True


def _render_paper_reader(inbox) -> None:
    st.subheader(_l("reader", "Reader"))
    papers = _paper_sources(inbox)
    if not papers:
        st.caption(_l("no_papers", "No paper sources yet."))
        return
    reader_source_key = f"paper_reader_source:{selected}"
    paper_ids = [source.id for source in papers]
    remembered_source_id = str(st.session_state.get(reader_source_key, "") or "")
    if remembered_source_id not in paper_ids:
        st.session_state.pop(reader_source_key, None)
        remembered_source_id = ""

    if not remembered_source_id:
        st.info(_l("reader_no_paper_selected", "No paper selected. Open Paper Library to choose a paper to read."))
        actions = st.columns([1.2, 1.2, 3])
        with actions[0]:
            _render_sidecar_link_button(
                _l("open_paper_library", "Open Paper Library"),
                _paper_library_workspace_url(),
                key=f"paper_reader_open_library:{selected}",
                icon=":material/library_books:",
                type="primary",
                use_container_width=True,
            )
        recent_rows = sorted(
            paper_rows(_pdir, view="recent"),
            key=lambda row: str(row.get("last_read") or ""),
            reverse=True,
        )
        recent_source_id = str((recent_rows[0] if recent_rows else {}).get("id") or "")
        if recent_source_id:
            with actions[1]:
                if st.button(
                    _l("continue_recent_paper", "Continue recent paper"),
                    key=f"paper_reader_continue_recent:{selected}:{recent_source_id}",
                    icon=":material/history:",
                    use_container_width=True,
                ):
                    st.session_state[reader_source_key] = recent_source_id
                    st.rerun()
            st.caption(
                f"{_l('recent_papers', 'Recent papers')}: "
                f"{_source_label(inbox, recent_source_id)}"
            )
        return

    source_id = remembered_source_id
    source = inbox.by_id().get(source_id)
    if source is None:
        st.session_state.pop(reader_source_key, None)
        return
    existing_pages = load_paper_pages(_pdir, source_id)
    existing_segments = load_paper_segments(_pdir, source_id)
    if source.metadata.get("pdf_asset_ref") and (not existing_pages or not existing_segments):
        st.info(
            _l(
                "reader_artifacts_missing",
                "Reader text artifacts are not extracted yet. The PDF can open now; Reader will prepare them automatically, or use Paper Library > Artifacts to run extraction manually.",
            )
        )
    status_bits = [
        f"PDF: {'yes' if source.metadata.get('pdf_asset_ref') else 'missing'}",
        f"{_l('pages', 'Pages')}: {source.metadata.get('page_count', '') or '?'}",
        f"{_l('annotations', 'Annotations')}: {len(load_paper_annotations(_pdir, source_id))}",
        f"{_l('segments', 'Segments')}: {len(load_paper_segments(_pdir, source_id))}",
        f"{_l('structured_extraction', 'Structure')}: "
        f"{source.metadata.get('reading_artifacts_status') or source.metadata.get('structure_backend', '') or _l('missing', 'missing')}",
    ]
    heading, library_action = st.columns([4, 1.2], vertical_alignment="top")
    with heading:
        st.markdown(f"**{source.title}**")
        st.caption(f"`{source_id}`")
    with library_action:
        _render_sidecar_link_button(
            _l("open_in_library", "Open in Library"),
            _paper_library_workspace_url(detail_id=source_id),
            key=f"paper_reader_open_source_library:{selected}:{source_id}",
            icon=":material/library_books:",
            use_container_width=True,
        )
    st.caption(" · ".join(status_bits))
    st.caption(
        _l(
            "reader_caption",
            "PDF Reader is the primary surface when a PDF asset is attached; diagnostics and text fallback stay out of the reading path.",
        )
    )
    artifact_warnings = source.metadata.get("structured_extraction_warnings") or source.metadata.get("text_extraction_warnings") or []
    if artifact_warnings:
        with st.expander(_l("reader_artifact_warnings", "Reader preparation warnings"), expanded=False):
            for warning in artifact_warnings:
                st.warning(str(warning))
    sidecar_unavailable, sidecar_message = _paper_library_sidecar_unavailable()
    if source.metadata.get("pdf_asset_ref") and not sidecar_unavailable:
        try:
            token = mint_reader_token(user.id, selected, source_id)
        except Exception as exc:
            st.error(str(exc))
            return
        base = _reader_api_base()
        encoded_source = quote(source_id, safe="")
        encoded_token = quote(token, safe="")
        iframe_src = f"{base}/reader/view/{encoded_source}?token={encoded_token}" if base else f"/reader/view/{encoded_source}?token={encoded_token}"
        _render_iframe(iframe_src, height=1200, scrolling=False)
        return
    if source.metadata.get("pdf_asset_ref"):
        st.warning(
            _l(
                "reader_sidecar_unavailable_fallback",
                "PDF Reader is temporarily unavailable because the 8502 sidecar cannot be reached. Showing text-mode Reader fallback.",
            )
            + (f" `{sidecar_message}`" if sidecar_message else "")
        )
    else:
        st.info(_l("pdf_missing", "No PDF asset is attached; using text-mode Reader."))

    pages, segments, annotations, translations_tab, ai_tab, claims_tab = st.tabs(
        [
            _l("pages", "Pages"),
            _l("segments", "Segments"),
            _l("annotations", "Annotations"),
            _l("translation", "Translation"),
            "AI",
            ui["claims_citations"],
        ]
    )
    with pages:
        rows = load_paper_pages(_pdir, source_id)
        if rows:
            for page in rows[:20]:
                with st.expander(f"p. {page.page} · {page.char_count} chars"):
                    st.text(page.text or _l("page_text_empty", "No extracted text for this page."))
        else:
            st.caption(_l("pages_empty", "No extracted pages yet."))
    with segments:
        segment_rows = load_paper_segments(_pdir, source_id)
        if segment_rows:
            st.dataframe(
                [
                    {
                        "segment_id": segment.segment_id,
                        "page": segment.page,
                        "locator": segment.locator,
                        "text": segment.text[:260],
                        "text_hash": segment.text_hash,
                    }
                    for segment in segment_rows
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption(_l("segments_empty", "No paper segments yet."))
    with annotations:
        segment_ids = [segment.segment_id for segment in load_paper_segments(_pdir, source_id)]
        with st.form(f"paper_annotation:{selected}:{source_id}"):
            page = st.number_input(_l("page", "Page"), min_value=0, value=0)
            selected_text = st.text_area(_l("selected_text", "Selected text"), height=110)
            note = st.text_area(ui["notes"], height=80)
            picked_segments = st.multiselect(_l("segment_refs", "Segment refs"), segment_ids)
            tags = st.text_input(ui["tags"])
            submitted = st.form_submit_button(_l("create_annotation", "Create annotation"), type="primary")
        if submitted:
            try:
                ann = create_paper_annotation(
                    _pdir,
                    source_id,
                    selected_text,
                    page=int(page),
                    note=note,
                    tags=_tags(tags),
                    segment_refs=picked_segments,
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=ann.id))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        anns = load_paper_annotations(_pdir, source_id)
        if anns:
            st.dataframe([ann.to_dict() for ann in anns], use_container_width=True, hide_index=True)
            ann_id = st.selectbox(
                _l("annotation_to_chunk", "Annotation to chunk"),
                options=[ann.id for ann in anns],
            )
            if st.button(_l("create_chunk_from_annotation", "Create chunk from annotation")):
                try:
                    chunk = create_chunk_from_annotation(_pdir, ann_id)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["created"].format(id=chunk.id))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.caption(_l("annotations_empty", "No annotations yet."))
    with translations_tab:
        segment_rows = load_paper_segments(_pdir, source_id)
        segment_ids = [segment.segment_id for segment in segment_rows]
        counts = _translation_counts_for_segments(source_id)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(_l("translated", "Translated"), counts["translated"])
        c2.metric(_l("missing", "Missing"), counts["missing"])
        c3.metric(_l("stale", "Stale"), counts["stale"])
        c4.metric(_l("failed", "Failed"), counts["failed"])
        if st.button(
            _l("translate_missing_stale", "Translate missing/stale"),
            disabled=not segment_rows or (counts["missing"] + counts["stale"] == 0),
        ):
            try:
                summary = translate_full_paper(
                    _pdir,
                    source_id,
                    target_lang="zh",
                    mode="missing_or_stale",
                    ai_profile=selected,
                    require_review=False,
                )
                st.session_state[_reader_key(source_id, "translation_summary")] = summary
                stash_git_backup_results()
                clear_web_cache()
                st.success(
                    _l("translation_full_saved", "Full-paper translation updated: {count} row(s).").format(
                        count=summary.get("updated", 0)
                    )
                )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        picked = st.multiselect(_l("translate_segments", "Translate segments"), segment_ids[:100])
        if st.button(_l("generate_translation_candidate", "Generate translation candidate"), disabled=not picked):
            result = translate_paper_segments(
                selected,
                source_id,
                [segment.to_dict() for segment in segment_rows if segment.segment_id in set(picked)],
            )
            st.session_state[f"paper_translation_candidate:{selected}:{source_id}"] = result.structured or {}
            for warning in result.warnings:
                st.warning(str(warning))
        candidate = st.session_state.get(f"paper_translation_candidate:{selected}:{source_id}", {})
        if isinstance(candidate, dict) and candidate.get("translations"):
            st.code(yaml.dump(candidate, allow_unicode=True, sort_keys=False), language="yaml")
            if st.button(_l("accept_translation_candidate", "Accept translation candidate")):
                try:
                    upsert_paper_translations(
                        _pdir,
                        source_id,
                        [
                            normalize_translation_row(row, source_id=source_id, target_lang="zh")
                            for row in list(candidate.get("translations") or [])
                            if isinstance(row, dict)
                        ],
                    )
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        translations = load_paper_translations(_pdir, source_id)
        if translations:
            st.dataframe([row.to_dict() for row in translations], use_container_width=True, hide_index=True)
        else:
            st.caption(_l("translations_empty", "No translations yet."))
    with ai_tab:
        segment_payload = _segment_dicts(source_id, limit=30)
        if st.button(_l("run_source_guide", "Run Source Guide")):
            result = generate_paper_source_guide(
                selected,
                source_id,
                source=source.to_dict(),
                segments=segment_payload,
            )
            st.session_state[f"paper_guide:{selected}:{source_id}"] = result.structured or {}
            for warning in result.warnings:
                st.warning(str(warning))
        guide = st.session_state.get(f"paper_guide:{selected}:{source_id}", {})
        if guide:
            st.code(yaml.dump(guide, allow_unicode=True, sort_keys=False), language="yaml")
            if st.button(_l("accept_as_analysis", "Accept as analysis")):
                try:
                    save_paper_analysis(_pdir, source_id, guide)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                except Exception as exc:
                    st.error(str(exc))
        question = st.text_input(_l("ask_paper", "Ask paper"))
        if st.button(_l("ask_paper", "Ask paper"), disabled=not question):
            result = answer_paper_question(
                selected,
                source_id,
                question,
                payload={"segments": segment_payload},
            )
            st.code(yaml.dump(result.structured or {}, allow_unicode=True, sort_keys=False), language="yaml")
            for warning in result.warnings:
                st.warning(str(warning))
        if st.button(_l("extract_claim_candidates", "Extract claim candidates")):
            result = extract_paper_claims(selected, source_id, segments=segment_payload)
            st.code(yaml.dump(result.structured or {}, allow_unicode=True, sort_keys=False), language="yaml")
            for warning in result.warnings:
                st.warning(str(warning))
        analysis = load_paper_analysis(_pdir, source_id)
        if analysis:
            with st.expander(_l("saved_analysis", "Saved analysis")):
                st.code(yaml.dump(analysis, allow_unicode=True, sort_keys=False), language="yaml")
    with claims_tab:
        st.caption(_l("reader_claims_hint", "Use the Claims & Citations tab for durable claim/citation editing."))
        source_chunks = load_chunks(_pdir, source_id)
        st.dataframe(
            [
                {"id": chunk.id, "locator": chunk.locator, "text": chunk.text[:220]}
                for chunk in source_chunks
            ],
            use_container_width=True,
            hide_index=True,
        )


def _reading_key(name: str) -> str:
    return f"research_reading:{selected}:{name}"


def _reading_from_form(source) -> ResearchReading:
    claims_raw = st.session_state.get(_reading_key("claim_candidates"), "")
    citations_raw = st.session_state.get(_reading_key("citations"), "")
    try:
        claim_candidates = yaml.safe_load(str(claims_raw or "")) or []
    except yaml.YAMLError:
        claim_candidates = []
    try:
        citations = yaml.safe_load(str(citations_raw or "")) or []
    except yaml.YAMLError:
        citations = []
    if not isinstance(claim_candidates, list):
        claim_candidates = []
    if not isinstance(citations, list):
        citations = []
    return ResearchReading(
        excerpt=str(st.session_state.get(_reading_key("excerpt"), "") or "").strip(),
        translation=str(st.session_state.get(_reading_key("translation"), "") or "").strip(),
        summary=str(st.session_state.get(_reading_key("summary"), "") or "").strip(),
        key_points=_text_lines(str(st.session_state.get(_reading_key("key_points"), "") or "")),
        claim_candidates=[item for item in claim_candidates if isinstance(item, dict)],
        citations=[item for item in citations if isinstance(item, dict)],
        synthesis_notes=str(st.session_state.get(_reading_key("synthesis_notes"), "") or "").strip(),
        generated_by=str(
            st.session_state.get(_reading_key("generated_by"), source.reading.generated_by) or ""
        ).strip(),
        updated_at=str(
            st.session_state.get(_reading_key("updated_at"), source.reading.updated_at) or ""
        ).strip(),
    )


def _seed_reading_state(source) -> None:
    seed_key = _reading_key("seed_source")
    if st.session_state.get(seed_key) == source.id:
        return
    reading = source.reading
    st.session_state[seed_key] = source.id
    st.session_state[_reading_key("excerpt")] = reading.excerpt
    st.session_state[_reading_key("translation")] = reading.translation
    st.session_state[_reading_key("summary")] = reading.summary
    st.session_state[_reading_key("key_points")] = "\n".join(reading.key_points)
    st.session_state[_reading_key("claim_candidates")] = yaml.dump(
        reading.claim_candidates,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ) if reading.claim_candidates else ""
    st.session_state[_reading_key("citations")] = yaml.dump(
        reading.citations,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ) if reading.citations else ""
    st.session_state[_reading_key("synthesis_notes")] = reading.synthesis_notes
    st.session_state[_reading_key("generated_by")] = reading.generated_by
    st.session_state[_reading_key("updated_at")] = reading.updated_at


def _store_reading_state(reading: ResearchReading) -> None:
    st.session_state[_reading_key("excerpt")] = reading.excerpt
    st.session_state[_reading_key("translation")] = reading.translation
    st.session_state[_reading_key("summary")] = reading.summary
    st.session_state[_reading_key("key_points")] = "\n".join(reading.key_points)
    st.session_state[_reading_key("claim_candidates")] = yaml.dump(
        reading.claim_candidates,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    st.session_state[_reading_key("citations")] = yaml.dump(
        reading.citations,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    st.session_state[_reading_key("synthesis_notes")] = reading.synthesis_notes
    st.session_state[_reading_key("generated_by")] = reading.generated_by
    st.session_state[_reading_key("updated_at")] = reading.updated_at


def _render_reading_room(inbox) -> None:
    st.subheader(ui["reading_room"])
    st.caption(ui["reading_flow_hint"])
    if not inbox.sources:
        st.caption(ui["empty_status"])
        return
    source_id = st.selectbox(
        ui["source_id"],
        options=[source.id for source in inbox.sources],
        format_func=lambda sid: next(
            (
                source.title or source.id
                for source in inbox.sources
                if source.id == sid
            ),
            sid,
        ),
        key=f"reading_source:{selected}",
    )
    source = inbox.by_id().get(source_id)
    if source is None:
        return
    _seed_reading_state(source)

    meta = {
        "id": source.id,
        "kind": source.kind,
        "status": source.status,
        "url": source.url,
        "evidence_refs": list(source.evidence_refs),
    }
    st.code(
        yaml.dump(meta, allow_unicode=True, default_flow_style=False, sort_keys=False),
        language="yaml",
    )

    mode = st.selectbox(
        ui["reading_mode"],
        ["summary", "translate", "claims", "synthesis"],
        key=f"reading_mode:{selected}",
    )
    excerpt = st.text_area(
        ui["excerpt"],
        height=180,
        key=_reading_key("excerpt"),
    )
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button(ui["generate_reading_draft"], type="primary"):
            reading, warnings = generate_reading_draft(
                source,
                excerpt,
                mode,
                profile=selected,
            )
            _store_reading_state(reading)
            st.session_state[_reading_key("warnings")] = warnings
            st.rerun()
    with b2:
        if st.button(ui["save_reading_annotations"]):
            reading = _reading_from_form(source)
            reading.updated_at = reading.updated_at or ""
            update_research_source(inbox, source.id, reading=reading)
            _save_sources(inbox, ui["saved"])
            st.rerun()
    warnings = st.session_state.get(_reading_key("warnings"), [])
    if isinstance(warnings, list):
        for warning in warnings:
            st.warning(str(warning))

    st.text_area(ui["translation"], height=140, key=_reading_key("translation"))
    st.text_area(ui["summary"], height=100, key=_reading_key("summary"))
    st.text_area(ui["key_points"], height=100, key=_reading_key("key_points"))
    st.text_area(ui["claim_candidates"], height=170, key=_reading_key("claim_candidates"))
    st.text_area(ui["citations"], height=150, key=_reading_key("citations"))
    st.text_area(ui["synthesis_notes"], height=130, key=_reading_key("synthesis_notes"))

    reading = _reading_from_form(source)
    try:
        patch = research_evidence_patch(source, reading)
        st.subheader(ui["evidence_candidate_preview"])
        st.code(
            yaml.dump(
                patch,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
            language="yaml",
        )
    except Exception as exc:
        patch = None
        st.warning(str(exc))
    with b3:
        if st.button(
            ui["create_evidence_candidate"],
            disabled=patch is None,
            key=f"reading_room_create_evidence:{selected}:{source.id}",
        ):
            try:
                assert_files_current([_sources_path, _pdir / "evidence-pool.yaml"])
                result = apply_research_evidence_candidate(
                    selected,
                    source.id,
                    patch or {},
                )
                refresh_file_snapshots(
                    [
                        _sources_path,
                        _pdir / "evidence-pool.yaml",
                        _pdir / "agent-activity.yaml",
                    ]
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=result["evidence_id"]))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _render_claims_citations(inbox) -> None:
    st.subheader(ui["claims_citations"])
    st.caption(ui["claim_boundary_hint"])
    if not inbox.sources:
        st.caption(ui["empty_status"])
        return
    source_options = [source.id for source in inbox.sources]
    source_key = f"research_cc_source:{selected}"
    if str(st.session_state.get(source_key) or "") not in source_options:
        st.session_state.pop(source_key, None)
    source_id = st.selectbox(
        ui["source_id"],
        options=source_options,
        format_func=lambda sid: next(
            (source.title or source.id for source in inbox.sources if source.id == sid),
            sid,
        ),
        key=source_key,
    )
    source = inbox.by_id().get(source_id)
    if source is None:
        return
    chunks = load_chunks(_pdir)
    source_chunks = [chunk for chunk in chunks if chunk.source_id == source_id]
    chunk_ids = [chunk.id for chunk in chunks]
    claim_rows = load_research_claims(_pdir)
    claim_ids = [claim.id for claim in claim_rows]
    citation_rows = load_research_citations(_pdir)
    status_options = ["", "draft", "ready", "promoted", "dismissed"]
    status_key = f"research_claim_status_filter:{selected}"
    if str(st.session_state.get(status_key) or "") not in status_options:
        st.session_state.pop(status_key, None)
    status_filter = st.selectbox(
        _l("claim_status_filter", "Claim status filter"),
        options=status_options,
        format_func=lambda value: _l("all_statuses", "All statuses") if not value else value,
        key=status_key,
    )
    queue_options = ["", "missing_citation", "quote_warning", "ready", "promoted"]
    queue_key = f"research_claim_queue_filter:{selected}"
    if str(st.session_state.get(queue_key) or "") not in queue_options:
        st.session_state.pop(queue_key, None)
    queue_filter = st.selectbox(
        _l("claim_queue_filter", "Review queue"),
        options=queue_options,
        format_func=lambda value: {
            "": _l("all_queues", "All queues"),
            "missing_citation": _l("missing_citation", "Missing citation"),
            "quote_warning": _l("quote_warning", "Quote warning"),
            "ready": _l("ready_claims", "Ready claims"),
            "promoted": _l("promoted_claims", "Promoted claims"),
        }.get(value, value),
        key=queue_key,
    )
    review = build_research_claim_review_payload(
        _pdir,
        source_id=source_id,
        status=status_filter,
        queue=queue_filter,
    )
    summary = review.get("summary") or {}
    st.subheader(_l("claim_review_board", "Claim review board"))
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(_l("chunks", "Chunks"), summary.get("chunks", 0))
    m2.metric(ui["research_claims"], summary.get("claims", 0))
    m3.metric(ui["research_citations"], summary.get("citations", 0))
    m4.metric(_l("missing_citation", "Missing citation"), summary.get("missing_citation_claims", 0))
    m5.metric(_l("quote_warnings", "Quote warnings"), summary.get("quote_warnings", 0))

    claim_cards = list(review.get("claim_cards") or [])
    ready_batch_options = [
        str(card.get("id") or "")
        for card in claim_cards
        if card.get("status") in {"draft", "ready"}
    ]
    if ready_batch_options:
        with st.expander(_l("claim_bulk_review", "Bulk claim review"), expanded=False):
            bulk_claims = st.multiselect(
                _l("selected_claims", "Selected claims"),
                options=ready_batch_options,
                default=[str(card.get("id") or "") for card in claim_cards if card.get("status") == "ready"],
                format_func=lambda cid: next(
                    (
                        f"{cid} - {str(card.get('text') or '')[:90]}"
                        for card in claim_cards
                        if str(card.get("id") or "") == cid
                    ),
                    cid,
                ),
                key=f"research_claim_bulk:{selected}:{source_id}:{status_filter}:{queue_filter}",
            )
            bulk_citation_refs = []
            for card in claim_cards:
                if str(card.get("id") or "") in set(bulk_claims):
                    bulk_citation_refs.extend(str(ref) for ref in card.get("citation_refs") or [] if str(ref))
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button(
                    _l("verify_selected_quotes", "Verify selected quotes"),
                    disabled=not bulk_citation_refs,
                    key=f"research_claim_bulk_verify:{selected}:{source_id}",
                    use_container_width=True,
                ):
                    checks = verify_research_citations(_pdir, bulk_citation_refs)
                    st.session_state[f"research_claim_bulk_checks:{selected}:{source_id}"] = checks
            with b2:
                if st.button(
                    _l("mark_selected_ready", "Mark selected ready"),
                    disabled=not bulk_claims,
                    key=f"research_claim_bulk_ready:{selected}:{source_id}",
                    use_container_width=True,
                ):
                    try:
                        assert_files_current([_research_claims_path])
                        for claim_id in bulk_claims:
                            update_research_claim_status(_pdir, claim_id, "ready")
                        refresh_file_snapshots([_research_claims_path])
                        stash_git_backup_results()
                        clear_web_cache()
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with b3:
                preview_rows = []
                for claim_id in bulk_claims:
                    try:
                        preview_rows.append(
                            {
                                "claim_id": claim_id,
                                "candidate": research_claim_to_evidence_candidate(_pdir, claim_id),
                            }
                        )
                    except Exception as exc:
                        preview_rows.append({"claim_id": claim_id, "warning": str(exc)})
                if preview_rows:
                    with st.popover(_l("bulk_promote_preview", "Promote preview"), use_container_width=True):
                        st.code(
                            yaml.dump(preview_rows, allow_unicode=True, default_flow_style=False, sort_keys=False),
                            language="yaml",
                        )
            checks = st.session_state.get(f"research_claim_bulk_checks:{selected}:{source_id}")
            if isinstance(checks, dict):
                st.caption(
                    _l(
                        "bulk_quote_check_summary",
                        "{ok}/{total} selected citation quote check(s) passed.",
                    ).format(ok=checks.get("ok", 0), total=checks.get("total", 0))
                )
                for check in checks.get("checks") or []:
                    if check.get("ok"):
                        st.success(str(check.get("message") or check.get("citation_id")))
                    else:
                        st.warning(str(check.get("message") or check.get("citation_id")))

    duplicate_groups = list(review.get("duplicate_claim_groups") or [])
    if duplicate_groups:
        with st.expander(_l("duplicate_claims", "Duplicate claims"), expanded=True):
            st.warning(
                _l(
                    "duplicate_claims_hint",
                    "These claims have the same normalized text. Merge refs before promotion.",
                )
            )
            for index, group in enumerate(duplicate_groups):
                refs = [str(ref) for ref in group.get("claim_refs") or [] if str(ref)]
                if len(refs) < 2:
                    continue
                with st.form(f"research_merge_duplicate:{selected}:{source_id}:{index}"):
                    st.write(str(group.get("text") or ""))
                    primary_ref = st.selectbox(
                        _l("primary_claim", "Primary claim"),
                        refs,
                        key=f"research_duplicate_primary:{selected}:{source_id}:{index}",
                    )
                    duplicate_refs = st.multiselect(
                        _l("duplicates_to_merge", "Duplicates to merge"),
                        [ref for ref in refs if ref != primary_ref],
                        default=[ref for ref in refs if ref != primary_ref],
                        key=f"research_duplicate_refs:{selected}:{source_id}:{index}",
                    )
                    merge_note = st.text_input(
                        _l("merge_rationale", "Merge rationale"),
                        value=_l("duplicate_merge_default", "Merged during source claim review."),
                        key=f"research_duplicate_note:{selected}:{source_id}:{index}",
                    )
                    merge_submitted = st.form_submit_button(
                        _l("merge_duplicate_claims", "Merge duplicate claims"),
                        disabled=not duplicate_refs or not merge_note.strip(),
                    )
                if merge_submitted:
                    try:
                        assert_files_current([_research_claims_path])
                        merge_duplicate_research_claims(
                            _pdir,
                            primary_ref,
                            duplicate_refs,
                            rationale=merge_note,
                        )
                        refresh_file_snapshots([_research_claims_path])
                        stash_git_backup_results()
                        clear_web_cache()
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    evidence_col, claim_col, citation_col = st.columns([1.15, 1.9, 1.35], gap="medium")
    with evidence_col:
        st.markdown(f"**{_l('source_evidence', 'Source evidence')}**")
        chunk_cards = list(review.get("chunk_cards") or [])
        if chunk_cards:
            for chunk in chunk_cards[:8]:
                with st.container(border=True):
                    st.markdown(f"**{chunk.get('title') or chunk.get('id')}**")
                    st.caption(" · ".join(str(item) for item in [chunk.get("kind"), chunk.get("locator")] if item))
                    linked = []
                    if chunk.get("linked_claims"):
                        linked.append(f"{ui['research_claims']}: {', '.join(chunk.get('linked_claims') or [])}")
                    if chunk.get("linked_citations"):
                        linked.append(f"{ui['research_citations']}: {', '.join(chunk.get('linked_citations') or [])}")
                    if linked:
                        st.caption(" · ".join(linked))
                    st.write(_short_text(chunk.get("text"), 360))
            if len(chunk_cards) > 8:
                st.caption(_l("more_chunks_hidden", "{count} more chunk(s) hidden by this compact view.").format(count=len(chunk_cards) - 8))
        else:
            st.caption(ui["chunks_empty"])

    with claim_col:
        st.markdown(f"**{_l('research_claim_review', 'Research claim review')}**")
        if claim_cards:
            for claim_card in claim_cards:
                claim_id = str(claim_card.get("id") or "")
                with st.container(border=True):
                    st.markdown(f"**{claim_id}**")
                    st.caption(
                        " · ".join(
                            str(item)
                            for item in [
                                claim_card.get("status"),
                                claim_card.get("type"),
                                f"confidence={claim_card.get('confidence')}",
                                f"citation={claim_card.get('citation_status')}",
                                f"quote={claim_card.get('quote_status')}",
                            ]
                            if item
                        )
                    )
                    st.write(claim_card.get("text") or "")
                    refs_line = " · ".join(
                        [
                            f"sources: {', '.join(claim_card.get('source_refs') or []) or '0'}",
                            f"chunks: {', '.join(claim_card.get('chunk_refs') or []) or '0'}",
                            f"citations: {', '.join(claim_card.get('citation_refs') or []) or '0'}",
                        ]
                    )
                    st.caption(refs_line)
                    with st.expander(_l("edit_claim_card", "Edit claim and links"), expanded=False):
                        claim_type_options = list(RESEARCH_CLAIM_TYPES)
                        claim_confidence_options = ["low", "medium", "high"]
                        with st.form(f"research_claim_patch:{selected}:{claim_id}"):
                            patch_text = st.text_area(
                                ui["research_claim_text"],
                                value=str(claim_card.get("text") or ""),
                                height=90,
                                key=f"research_claim_patch_text:{selected}:{claim_id}",
                            )
                            p1, p2, p3 = st.columns(3)
                            with p1:
                                patch_type = st.selectbox(
                                    ui["research_claim_type"],
                                    claim_type_options,
                                    index=claim_type_options.index(str(claim_card.get("type") or "learning"))
                                    if str(claim_card.get("type") or "learning") in claim_type_options
                                    else claim_type_options.index("learning"),
                                    key=f"research_claim_patch_type:{selected}:{claim_id}",
                                )
                            with p2:
                                patch_confidence = st.selectbox(
                                    _l("confidence", "Confidence"),
                                    claim_confidence_options,
                                    index=claim_confidence_options.index(str(claim_card.get("confidence") or "medium"))
                                    if str(claim_card.get("confidence") or "medium") in claim_confidence_options
                                    else claim_confidence_options.index("medium"),
                                    key=f"research_claim_patch_confidence:{selected}:{claim_id}",
                                )
                            with p3:
                                patch_human_note = st.checkbox(
                                    ui["human_note"],
                                    value=bool(claim_card.get("human_note")),
                                    key=f"research_claim_patch_human:{selected}:{claim_id}",
                                )
                            patch_warnings = st.text_area(
                                _l("warnings", "Warnings"),
                                value="\n".join(str(item) for item in claim_card.get("warnings") or []),
                                height=64,
                                key=f"research_claim_patch_warnings:{selected}:{claim_id}",
                            )
                            patch_rationale = st.text_area(
                                ui["rationale"],
                                value=str(claim_card.get("rationale") or ""),
                                height=72,
                                key=f"research_claim_patch_rationale:{selected}:{claim_id}",
                            )
                            patch_submitted = st.form_submit_button(ui["save"], type="primary")
                        if patch_submitted:
                            try:
                                assert_files_current([_research_claims_path])
                                patch_research_claim(
                                    _pdir,
                                    claim_id,
                                    text=patch_text,
                                    type=patch_type,
                                    confidence=patch_confidence,
                                    warnings=patch_warnings,
                                    rationale=patch_rationale,
                                    human_note=patch_human_note,
                                )
                                refresh_file_snapshots([_research_claims_path])
                                stash_git_backup_results()
                                clear_web_cache()
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))

                        with st.form(f"research_claim_links:{selected}:{claim_id}"):
                            next_chunk_refs = st.multiselect(
                                _l("link_chunk", "Linked chunks"),
                                options=chunk_ids,
                                default=[str(ref) for ref in claim_card.get("chunk_refs") or [] if str(ref) in chunk_ids],
                                key=f"research_claim_links_chunks:{selected}:{claim_id}",
                            )
                            next_citation_refs = st.multiselect(
                                _l("link_citation", "Linked citations"),
                                options=[citation.id for citation in citation_rows],
                                default=[
                                    str(ref)
                                    for ref in claim_card.get("citation_refs") or []
                                    if str(ref) in {citation.id for citation in citation_rows}
                                ],
                                key=f"research_claim_links_citations:{selected}:{claim_id}",
                            )
                            links_submitted = st.form_submit_button(
                                _l("save_claim_links", "Save links"),
                                help=_l(
                                    "save_claim_links_help",
                                    "Removing a selection unlinks it from this claim.",
                                ),
                            )
                        if links_submitted:
                            try:
                                assert_files_current([_research_claims_path])
                                update_research_claim_links(
                                    _pdir,
                                    claim_id,
                                    chunk_refs=next_chunk_refs,
                                    citation_refs=next_citation_refs,
                                    mode="replace",
                                )
                                refresh_file_snapshots([_research_claims_path])
                                stash_git_backup_results()
                                clear_web_cache()
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))

                        chunk_choices = [chunk.id for chunk in source_chunks]
                        if chunk_choices:
                            with st.form(f"research_claim_citation_chunk:{selected}:{claim_id}"):
                                cite_chunk = st.selectbox(
                                    _l("citation_chunk", "Citation chunk"),
                                    options=chunk_choices,
                                    index=chunk_choices.index(str((claim_card.get("chunk_refs") or [""])[0]))
                                    if str((claim_card.get("chunk_refs") or [""])[0]) in chunk_choices
                                    else 0,
                                    key=f"research_claim_cite_chunk:{selected}:{claim_id}",
                                )
                                cite_quote = st.text_area(
                                    ui["citation_quote"],
                                    height=62,
                                    help=_l(
                                        "citation_quote_default",
                                        "Leave blank to use the selected chunk text as the quote.",
                                    ),
                                    key=f"research_claim_cite_quote:{selected}:{claim_id}",
                                )
                                create_from_chunk = st.form_submit_button(
                                    _l("create_citation_from_chunk", "Create citation from chunk"),
                                )
                            if create_from_chunk:
                                try:
                                    assert_files_current([_research_claims_path, _research_citations_path])
                                    create_citation_from_chunk(
                                        _pdir,
                                        claim_id,
                                        cite_chunk,
                                        quote=cite_quote,
                                    )
                                    refresh_file_snapshots([_research_claims_path, _research_citations_path])
                                    stash_git_backup_results()
                                    clear_web_cache()
                                    st.rerun()
                                except Exception as exc:
                                    st.error(str(exc))
                        with st.form(f"research_claim_request_citation:{selected}:{claim_id}"):
                            request_note = st.text_input(
                                _l("citation_request_note", "Citation request note"),
                                value=_l("citation_request_default", "Bind a stronger citation before public use."),
                                key=f"research_claim_request_note:{selected}:{claim_id}",
                            )
                            request_submitted = st.form_submit_button(
                                _l("request_citation", "Request citation"),
                            )
                        if request_submitted:
                            try:
                                assert_files_current([_research_claims_path])
                                request_citation_for_claim(_pdir, claim_id, note=request_note)
                                refresh_file_snapshots([_research_claims_path])
                                stash_git_backup_results()
                                clear_web_cache()
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
                    if claim_card.get("citation_status") == "missing":
                        st.warning(_l("claim_missing_citation_warning", "This claim has no citation yet. Bind a citation before public use."))
                    elif claim_card.get("quote_status") == "warning":
                        st.warning(_l("claim_quote_warning", "At least one linked citation needs quote review."))
                    for warning in claim_card.get("warnings") or []:
                        st.warning(str(warning))
                    try:
                        patch = research_claim_to_evidence_candidate(_pdir, claim_id)
                    except Exception as exc:
                        patch = None
                        st.warning(str(exc))
                    with st.expander(_l("evidence_candidate_preview", "Evidence candidate preview"), expanded=False):
                        if patch is not None:
                            st.code(
                                yaml.dump(patch, allow_unicode=True, default_flow_style=False, sort_keys=False),
                                language="yaml",
                            )
                        else:
                            st.caption(_l("no_candidate_preview", "No candidate preview is available for this claim."))
                    a1, a2, a3 = st.columns(3)
                    with a1:
                        if st.button(
                            _l("mark_ready", "Mark ready"),
                            key=f"research_claim_mark_ready:{selected}:{claim_id}",
                            disabled=claim_card.get("status") in {"ready", "promoted", "dismissed"},
                            icon=":material/check_circle:",
                            use_container_width=True,
                        ):
                            try:
                                assert_files_current([_research_claims_path])
                                update_research_claim_status(_pdir, claim_id, "ready")
                                refresh_file_snapshots([_research_claims_path])
                                stash_git_backup_results()
                                clear_web_cache()
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
                    with a2:
                        source_refs = [str(ref) for ref in claim_card.get("source_refs") or []]
                        if st.button(
                            _l("promote_to_evidence", "Promote"),
                            key=f"research_claim_promote:{selected}:{claim_id}",
                            disabled=patch is None or not source_refs or claim_card.get("status") == "promoted",
                            icon=":material/upgrade:",
                            use_container_width=True,
                        ):
                            try:
                                assert_files_current([_sources_path, _research_claims_path, _pdir / "evidence-pool.yaml"])
                                result = apply_research_evidence_candidate(selected, source_refs[0], patch or {})
                                matched_claim = next((item for item in claim_rows if item.id == claim_id), None)
                                if matched_claim is not None:
                                    upsert_research_claim(
                                        _pdir,
                                        matched_claim.text,
                                        claim_id=matched_claim.id,
                                        status="promoted",
                                        type=matched_claim.type,
                                        source_refs=matched_claim.source_refs,
                                        chunk_refs=matched_claim.chunk_refs,
                                        citation_refs=matched_claim.citation_refs,
                                        evidence_refs=[*matched_claim.evidence_refs, result["evidence_id"]],
                                        rationale=matched_claim.rationale,
                                        human_note=matched_claim.human_note,
                                        warnings=matched_claim.warnings,
                                        generated_by=matched_claim.generated_by or "research_workspace",
                                    )
                                refresh_file_snapshots(
                                    [
                                        _sources_path,
                                        _research_claims_path,
                                        _pdir / "evidence-pool.yaml",
                                        _pdir / "agent-activity.yaml",
                                    ]
                                )
                                stash_git_backup_results()
                                clear_web_cache()
                                st.success(ui["created"].format(id=result["evidence_id"]))
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
                    with a3:
                        dismiss_note = st.text_input(
                            _l("dismiss_rationale", "Dismiss rationale"),
                            key=f"research_claim_dismiss_note:{selected}:{claim_id}",
                            placeholder=_l("dismiss_rationale_placeholder", "Why is this claim dismissed?"),
                            label_visibility="collapsed",
                        )
                        if st.button(
                            _l("dismiss", "Dismiss"),
                            key=f"research_claim_dismiss:{selected}:{claim_id}",
                            disabled=claim_card.get("status") == "dismissed" or not dismiss_note.strip(),
                            icon=":material/do_not_disturb_on:",
                            use_container_width=True,
                        ):
                            try:
                                assert_files_current([_research_claims_path])
                                update_research_claim_status(
                                    _pdir,
                                    claim_id,
                                    "dismissed",
                                    note=dismiss_note,
                                )
                                refresh_file_snapshots([_research_claims_path])
                                stash_git_backup_results()
                                clear_web_cache()
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
        else:
            st.caption(ui["claims_empty"])

    with citation_col:
        st.markdown(f"**{_l('citation_inspector', 'Citation inspector')}**")
        citation_cards = list(review.get("citation_cards") or [])
        if citation_cards:
            for citation in citation_cards[:10]:
                check = citation.get("quote_check") if isinstance(citation.get("quote_check"), dict) else {}
                with st.container(border=True):
                    st.markdown(f"**{citation.get('id')}**")
                    st.caption(
                        " · ".join(
                            str(item)
                            for item in [
                                f"claim={citation.get('claim_id')}",
                                f"source={citation.get('source_id')}",
                                f"chunk={citation.get('chunk_id') or 'none'}",
                                check.get("level"),
                            ]
                            if item
                        )
                    )
                    message = str(check.get("message") or "")
                    if check.get("ok"):
                        st.success(message)
                    else:
                        st.warning(message)
                    if citation.get("quote"):
                        st.write(citation.get("quote"))
                    if citation.get("locator") or citation.get("bibliography"):
                        st.caption(f"{citation.get('locator') or ''} · {citation.get('bibliography') or ''}")
                    locate_source = str(citation.get("source_id") or "")
                    locate_chunk = str(citation.get("chunk_id") or "")
                    locate_cols = st.columns(2)
                    with locate_cols[0]:
                        if locate_source:
                            _render_sidecar_link_button(
                                _l("locate_source", "Locate source"),
                                _paper_library_workspace_url(
                                    detail_id=locate_source,
                                    focus="claims",
                                    action="fix_citation",
                                    return_to="overview",
                                ),
                                key=f"citation_locate_source:{selected}:{locate_source}:{locate_chunk}",
                                use_container_width=True,
                            )
                    with locate_cols[1]:
                        st.caption(
                            _l("locator_label", "Locator")
                            + f": {citation.get('locator') or locate_chunk or '-'}"
                        )
            if len(citation_cards) > 10:
                st.caption(_l("more_citations_hidden", "{count} more citation(s) hidden by this compact view.").format(count=len(citation_cards) - 10))
        else:
            st.caption(ui["citations_empty"])

    st.divider()
    st.caption(_l("manual_research_editing_hint", "Manual source/chunk/claim/citation editors remain below as fallback tools."))

    chunk_tab, claim_tab, citation_tab = st.tabs(
        [
            _l("chunks", "Chunks"),
            ui["research_claims"],
            ui["research_citations"],
        ]
    )

    with chunk_tab:
        with st.expander(ui["create_chunk"], expanded=not source_chunks):
            with st.form(f"research_create_chunk:{selected}"):
                chunk_kind = st.selectbox(ui["chunk_kind"], list(RESEARCH_CHUNK_KINDS))
                chunk_title = st.text_input(ui["chunk_title"])
                chunk_locator = st.text_input(ui["chunk_locator"])
                chunk_text = st.text_area(ui["chunk_text"], height=140)
                submitted = st.form_submit_button(ui["create"], type="primary")
            if submitted:
                try:
                    chunk = create_chunk(
                        _pdir,
                        source_id,
                        chunk_text,
                        kind=chunk_kind,
                        title=chunk_title,
                        locator=chunk_locator,
                    )
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["created"].format(id=chunk.id))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        if source_chunks:
            for chunk in source_chunks:
                related_claims = [claim.id for claim in claim_rows if chunk.id in claim.chunk_refs]
                related_citations = [citation.id for citation in citation_rows if citation.chunk_id == chunk.id]
                with st.container(border=True):
                    st.markdown(f"**{chunk.title or chunk.id}**")
                    st.caption(f"{chunk.kind} · {chunk.locator or source_id}")
                    if related_claims or related_citations:
                        st.caption(
                            " · ".join(
                                [
                                    f"{ui['research_claims']}: {', '.join(related_claims) or '0'}",
                                    f"{ui['research_citations']}: {', '.join(related_citations) or '0'}",
                                ]
                            )
                        )
                    st.write(chunk.text)
                    if chunk.metadata:
                        with st.expander(_l("metadata", "Metadata"), expanded=False):
                            st.code(yaml.dump(chunk.metadata, allow_unicode=True, sort_keys=False), language="yaml")
        else:
            st.caption(ui["chunks_empty"])

    with claim_tab:
        with st.expander(ui["create_research_claim"], expanded=bool(source_chunks) and not claim_rows):
            with st.form(f"research_create_claim:{selected}"):
                claim_id = st.text_input(ui["research_claim_id"])
                claim_type = st.selectbox(
                    ui["research_claim_type"],
                    ["learning", "finding", "hypothesis", "project", "skill", "impact"],
                )
                claim_status = st.selectbox(
                    ui["research_claim_status"],
                    ["draft", "ready", "promoted", "dismissed"],
                )
                claim_text = st.text_area(ui["research_claim_text"], height=110)
                claim_chunks = st.multiselect(
                    ui["chunk_refs"],
                    options=chunk_ids,
                    default=[chunk.id for chunk in source_chunks[:1]],
                )
                human_note = st.checkbox(ui["human_note"])
                rationale = st.text_area(ui["rationale"], height=80)
                submitted_claim = st.form_submit_button(ui["save"], type="primary")
            if submitted_claim:
                try:
                    claim = upsert_research_claim(
                        _pdir,
                        claim_text,
                        claim_id=claim_id,
                        type=claim_type,
                        status=claim_status,
                        source_refs=[source_id],
                        chunk_refs=claim_chunks,
                        rationale=rationale,
                        human_note=human_note,
                    )
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["created"].format(id=claim.id))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        source_claims = [
            claim
            for claim in claim_rows
            if source_id in claim.source_refs
            or any(chunk.id in claim.chunk_refs for chunk in source_chunks)
        ]
        if source_claims:
            for claim in source_claims:
                with st.container(border=True):
                    st.markdown(f"**{claim.id}**")
                    st.caption(
                        " · ".join(
                            [
                                claim.status,
                                claim.type,
                                f"confidence={claim.confidence}",
                            ]
                        )
                    )
                    st.write(claim.text)
                    st.caption(
                        " · ".join(
                            [
                                f"sources: {', '.join(claim.source_refs) or '0'}",
                                f"chunks: {', '.join(claim.chunk_refs) or '0'}",
                                f"citations: {', '.join(claim.citation_refs) or '0'}",
                            ]
                        )
                    )
                    for warning in claim.warnings:
                        st.warning(str(warning))
        else:
            st.caption(ui["claims_empty"])

        if claim_ids:
            selected_claim_id = st.selectbox(
                ui["research_claim_id"],
                options=claim_ids,
                key=f"research_evidence_candidate_claim:{selected}",
            )
            try:
                patch = research_claim_to_evidence_candidate(_pdir, selected_claim_id)
                st.code(
                    yaml.dump(patch, allow_unicode=True, default_flow_style=False, sort_keys=False),
                    language="yaml",
                )
            except Exception as exc:
                patch = None
                st.warning(str(exc))
            if st.button(ui["create_evidence_candidate"], disabled=patch is None):
                claim = next((item for item in claim_rows if item.id == selected_claim_id), None)
                source_ref = (claim.source_refs[0] if claim and claim.source_refs else source_id)
                try:
                    assert_files_current([_sources_path, _pdir / "evidence-pool.yaml"])
                    result = apply_research_evidence_candidate(selected, source_ref, patch or {})
                    if claim is not None:
                        upsert_research_claim(
                            _pdir,
                            claim.text,
                            claim_id=claim.id,
                            status="promoted",
                            type=claim.type,
                            source_refs=claim.source_refs,
                            chunk_refs=claim.chunk_refs,
                            citation_refs=claim.citation_refs,
                            evidence_refs=[*claim.evidence_refs, result["evidence_id"]],
                            rationale=claim.rationale,
                            human_note=claim.human_note,
                            warnings=claim.warnings,
                            generated_by=claim.generated_by or "research_workspace",
                        )
                    refresh_file_snapshots(
                        [
                            _sources_path,
                            _pdir / "evidence-pool.yaml",
                            _pdir / "agent-activity.yaml",
                        ]
                    )
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["created"].format(id=result["evidence_id"]))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with citation_tab:
        with st.expander(ui["create_citation"], expanded=bool(claim_ids) and not citation_rows):
            with st.form(f"research_create_citation:{selected}"):
                citation_claim = st.selectbox(
                    ui["research_claim_id"],
                    options=claim_ids,
                    key=f"research_citation_claim:{selected}",
                ) if claim_ids else ""
                citation_chunk = st.selectbox(
                    ui["chunk_refs"],
                    options=["", *chunk_ids],
                    key=f"research_citation_chunk:{selected}",
                )
                locator = st.text_input(ui["chunk_locator"], key=f"citation_locator:{selected}")
                quote = st.text_area(ui["citation_quote"], height=90)
                bibliography = st.text_area(ui["bibliography"], height=70)
                submitted_citation = st.form_submit_button(ui["create"], type="primary")
            if submitted_citation:
                try:
                    citation = create_citation(
                        _pdir,
                        citation_claim,
                        source_id=source_id,
                        chunk_id=citation_chunk,
                        locator=locator,
                        quote=quote,
                        bibliography=bibliography,
                        url=getattr(source, "url", ""),
                    )
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["created"].format(id=citation.id))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        source_citations = [
            citation
            for citation in citation_rows
            if citation.source_id == source_id
            or any(chunk.id == citation.chunk_id for chunk in source_chunks)
        ]
        citation_warnings = paper_citation_diagnostics(_pdir, source_id)
        for warning in citation_warnings:
            st.warning(str(warning))
        if source_citations:
            chunk_map = {chunk.id: chunk for chunk in chunks}
            for citation in source_citations:
                chunk = chunk_map.get(citation.chunk_id)
                quote_ok = ""
                if citation.quote and chunk is not None:
                    quote_ok = "quote ok" if citation.quote.strip().casefold() in chunk.text.casefold() else "quote warning"
                with st.container(border=True):
                    st.markdown(f"**{citation.id}**")
                    st.caption(
                        " · ".join(
                            [
                                f"claim={citation.claim_id}",
                                f"source={citation.source_id or source_id}",
                                f"chunk={citation.chunk_id or 'none'}",
                                quote_ok,
                            ]
                        )
                    )
                    if citation.quote:
                        st.write(citation.quote)
                    if citation.locator or citation.bibliography:
                        st.caption(f"{citation.locator} · {citation.bibliography}")
        else:
            st.caption(ui["citations_empty"])


def _research_candidate_manifest(profile: Path, candidate: dict) -> dict:
    return build_research_export_manifest(
        profile,
        source_refs=list(candidate.get("related_sources") or []),
        claim_refs=list(candidate.get("related_research_claims") or []),
        citation_refs=list(candidate.get("related_citations") or []),
    )


def _render_research_candidate_manifest(profile: Path, candidate: dict, key_prefix: str) -> tuple[dict, list[dict]]:
    try:
        manifest = _research_candidate_manifest(profile, candidate)
    except Exception as exc:
        st.warning(str(exc))
        return {}, [{"kind": "manifest_error", "ref": str(exc)}]
    blockers = list(manifest.get("blockers") or [])
    with st.expander(_l("candidate_manifest", "Candidate manifest"), expanded=bool(blockers)):
        if blockers:
            for blocker in blockers:
                kind = str(blocker.get("kind") or "")
                ref = str(blocker.get("ref") or "")
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.warning(f"{kind}: {ref}")
                with c2:
                    if kind == "private_source" and ref:
                        _render_sidecar_link_button(
                            _l("review_visibility", "Review visibility"),
                            _paper_library_workspace_url(
                                detail_id=ref,
                                focus="safety",
                                action="review_visibility",
                                return_to="overview",
                            ),
                            key=f"{key_prefix}:review_visibility:{selected}:{ref}",
                            use_container_width=True,
                        )
                    elif kind == "broken_citation":
                        if st.button(
                            _l("fix_citation", "Fix citation"),
                            key=f"{key_prefix}:fix_citation:{ref}",
                            use_container_width=True,
                        ):
                            st.session_state[f"research_claim_queue_filter:{selected}"] = "quote_warning"
                            st.info(_l("fix_citation_hint", "Open Claims & Citations to review quote warnings."))
                    elif kind == "unpromoted_research_claim":
                        if st.button(
                            _l("promote_claim", "Promote claim"),
                            key=f"{key_prefix}:promote_claim:{ref}",
                            use_container_width=True,
                        ):
                            st.session_state[f"research_claim_status_filter:{selected}"] = "ready"
                            st.info(_l("promote_claim_hint", "Open Claims & Citations to preview and promote claims."))
        else:
            st.success(_l("candidate_manifest_clear", "No provenance blockers for this candidate."))
        if st.checkbox(
            _l("show_manifest_yaml", "Show manifest YAML"),
            value=False,
            key=f"{key_prefix}:manifest_yaml",
        ):
            st.code(
                yaml.dump(
                    {
                        key: value
                        for key, value in manifest.items()
                        if key not in {"sources", "claims", "citations"}
                    },
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                language="yaml",
            )
    return manifest, blockers


def _render_synthesis_drafts() -> None:
    st.subheader(_l("synthesis_export", "Synthesis / Export"))
    citation_rows = load_research_citations(_pdir)
    chunk_rows = load_chunks(_pdir)
    claim_rows_all = load_research_claims(_pdir)
    source_book = load_research_sources(selected)
    source_ids = [source.id for source in source_book.sources]
    node_options = _node_options(include_unsorted=False)
    goal_options = sorted({ref for source in source_book.sources for ref in source.goal_refs})
    tag_options = sorted({tag for source in source_book.sources for tag in source.tags})

    with st.expander(_l("export_scope", "Export scope"), expanded=False):
        s1, s2, s3 = st.columns(3)
        with s1:
            scope_node = st.selectbox(
                _l("collection", "Collection"),
                options=["", *node_options],
                format_func=lambda ref: _l("all_collections", "All collections") if not ref else node_options.get(ref, ref),
                key=f"research_export_scope_node:{selected}",
            )
            scope_goals = st.multiselect(
                _l("goal_refs", "Goal refs"),
                options=goal_options,
                key=f"research_export_scope_goals:{selected}",
            )
        with s2:
            scope_source_statuses = st.multiselect(
                _l("source_statuses", "Source statuses"),
                options=list(SOURCE_STATUSES),
                key=f"research_export_scope_source_status:{selected}",
            )
            scope_claim_statuses = st.multiselect(
                _l("claim_statuses", "Claim statuses"),
                options=["draft", "ready", "promoted", "dismissed"],
                key=f"research_export_scope_claim_status:{selected}",
            )
        with s3:
            scope_tags = st.multiselect(
                _l("tags_label", "Tags"),
                options=tag_options,
                key=f"research_export_scope_tags:{selected}",
            )
            scope_sources = st.multiselect(
                _l("manual_sources", "Manual sources"),
                options=source_ids,
                format_func=lambda sid: _source_label(source_book, sid),
                key=f"research_export_scope_sources:{selected}",
            )
    export_scope = {
        "library_node_refs": [scope_node] if scope_node else [],
        "goal_refs": scope_goals,
        "source_statuses": scope_source_statuses,
        "claim_statuses": scope_claim_statuses,
        "tags": scope_tags,
        "source_refs": scope_sources,
    }
    scope_active = any(value for value in export_scope.values())
    scoped_export = build_research_export_payload(_pdir, scope=export_scope)
    scoped_selection = scoped_export.get("selection") if isinstance(scoped_export.get("selection"), dict) else {}
    if scope_active:
        st.caption(
            _l(
                "export_scope_summary",
                "Scope selected {sources} source(s), {claims} claim(s), and {citations} citation(s).",
            ).format(
                sources=len(scoped_selection.get("source_refs") or []),
                claims=len(scoped_selection.get("claim_refs") or []),
                citations=len(scoped_selection.get("citation_refs") or []),
            )
        )
    with st.expander(_l("export_citations", "Export citations"), expanded=False):
        citation_refs = st.multiselect(
            ui["research_citations"],
            options=[citation.id for citation in citation_rows],
            default=list(scoped_selection.get("citation_refs") or []) if scope_active else [],
            format_func=lambda cid: next(
                (
                    f"{cid} · {citation.locator or citation.source_id}"
                    for citation in citation_rows
                    if citation.id == cid
                ),
                cid,
            ),
        )
        export_format = st.radio("Format", ["markdown", "bibtex", "ris", "csl-json"], horizontal=True)
        export_citation_refs = citation_refs or (
            list(scoped_selection.get("citation_refs") or [])
            if scope_active
            else []
        )
        try:
            export_body = (
                ""
                if scope_active and not export_citation_refs
                else format_research_citations(
                    _pdir,
                    export_citation_refs,
                    format=export_format,
                )
            )
            export_manifest = build_research_export_manifest(
                _pdir,
                citation_refs=export_citation_refs,
                claim_refs=list(scoped_selection.get("claim_refs") or []) if scope_active else [],
                source_refs=list(scoped_selection.get("source_refs") or []) if scope_active else [],
            )
        except Exception as exc:
            export_body = ""
            export_manifest = {}
            st.warning(str(exc))
        private_refs = list(export_manifest.get("private_source_refs") or [])
        if private_refs:
            st.warning(
                _l(
                    "private_export_warning",
                    "This export includes private paper sources; keep it private or remove them before public use: {refs}",
                ).format(refs=", ".join(private_refs))
            )
        blockers = list(export_manifest.get("blockers") or [])
        if export_manifest:
            with st.expander(_l("export_manifest", "Export manifest"), expanded=bool(blockers)):
                e1, e2, e3, e4 = st.columns(4)
                e1.metric(_l("sources_total", "Sources"), len(export_manifest.get("source_refs") or []))
                e2.metric(ui["research_claims"], len(export_manifest.get("claim_refs") or []))
                e3.metric(ui["research_citations"], len(export_manifest.get("citation_refs") or []))
                e4.metric(_l("publish_blockers", "Publish blockers"), len(blockers))
                if blockers:
                    for blocker in blockers:
                        kind = str(blocker.get("kind") or "")
                        ref = str(blocker.get("ref") or "")
                        warning_col, action_col = st.columns([3, 1])
                        with warning_col:
                            st.warning(f"{kind}: {ref}")
                        with action_col:
                            if kind == "private_source" and ref:
                                _render_sidecar_link_button(
                                    _l("review_visibility", "Review visibility"),
                                    _paper_library_workspace_url(
                                        detail_id=ref,
                                        focus="safety",
                                        action="review_visibility",
                                        return_to="overview",
                                    ),
                                    key=f"export_review_visibility:{selected}:{ref}",
                                    use_container_width=True,
                                )
                            elif kind == "broken_citation":
                                if st.button(
                                    _l("fix_citation", "Fix citation"),
                                    key=f"export_fix_citation:{selected}:{ref}",
                                    use_container_width=True,
                                ):
                                    st.session_state[f"research_claim_queue_filter:{selected}"] = "quote_warning"
                                    st.info(_l("fix_citation_hint", "Open Claims & Citations to review quote warnings."))
                            elif kind == "unpromoted_research_claim":
                                if st.button(
                                    _l("promote_claim", "Promote claim"),
                                    key=f"export_promote_claim:{selected}:{ref}",
                                    use_container_width=True,
                                ):
                                    st.session_state[f"research_claim_status_filter:{selected}"] = "ready"
                                    st.info(_l("promote_claim_hint", "Open Claims & Citations to preview and promote claims."))
                provenance_tabs = st.tabs(
                    [
                        _l("sources", "Sources"),
                        ui["research_claims"],
                        ui["research_citations"],
                        _l("manifest_yaml", "Manifest YAML"),
                    ]
                )
                with provenance_tabs[0]:
                    source_rows = list(export_manifest.get("sources") or [])
                    if source_rows:
                        st.dataframe(source_rows, use_container_width=True, hide_index=True)
                    else:
                        st.caption(_l("sources_empty", "No sources selected."))
                with provenance_tabs[1]:
                    claim_rows_manifest = list(export_manifest.get("claims") or [])
                    if claim_rows_manifest:
                        st.dataframe(claim_rows_manifest, use_container_width=True, hide_index=True)
                    else:
                        st.caption(ui["claims_empty"])
                with provenance_tabs[2]:
                    citation_rows_manifest = list(export_manifest.get("citations") or [])
                    if citation_rows_manifest:
                        st.dataframe(citation_rows_manifest, use_container_width=True, hide_index=True)
                    else:
                        st.caption(ui["citations_empty"])
                with provenance_tabs[3]:
                    st.code(
                        yaml.dump(
                            {
                                key: value
                                for key, value in export_manifest.items()
                                if key not in {"sources", "claims", "citations"}
                            },
                            allow_unicode=True,
                            default_flow_style=False,
                            sort_keys=False,
                        ),
                        language="yaml",
                    )
        if export_body:
            st.text_area(
                _l("export_preview", "Export preview"),
                value=export_body,
                height=220,
                key=f"export_preview:{selected}:{export_format}",
            )
            st.download_button(
                _l("download_export", "Download export"),
                data=export_body,
                file_name=f"research-citations.{ {'bibtex': 'bib', 'ris': 'ris', 'csl-json': 'json'}.get(export_format, 'md') }",
            )
            save_private_export = not private_refs or st.checkbox(
                _l("confirm_private_export_save", "Confirm saving export with private sources"),
                value=False,
            )
            if st.button(_l("save_export", "Save export"), disabled=not save_private_export):
                try:
                    path = save_research_export(
                        _pdir,
                        export_body,
                        format=export_format,
                        manifest=export_manifest,
                    )
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(str(path))
                except Exception as exc:
                    st.error(str(exc))

    with st.expander(_l("reading_note_export", "Reading note export"), expanded=False):
        scoped_note_defaults = [
            ref for ref in scoped_selection.get("source_refs") or []
            if ref in source_ids
        ] if scope_active else []
        note_sources = st.multiselect(
            _l("note_sources", "Note sources"),
            options=source_ids,
            default=scoped_note_defaults,
            format_func=lambda sid: _source_label(source_book, sid),
            key=f"reading_note_sources:{selected}",
        ) if source_ids else []
        note_source_set = set(note_sources)
        note_claims = st.multiselect(
            ui["research_claims"],
            options=[claim.id for claim in claim_rows_all],
            default=[
                claim.id
                for claim in claim_rows_all
                if claim.id in set(scoped_selection.get("claim_refs") or [])
            ] if scope_active else [],
            key=f"reading_note_claims:{selected}",
        )
        note_chunks = st.multiselect(
            ui["chunk_refs"],
            options=[chunk.id for chunk in chunk_rows if not note_source_set or chunk.source_id in note_source_set],
            key=f"reading_note_chunks:{selected}",
        )
        note_citations = st.multiselect(
            ui["citations"],
            options=[citation.id for citation in citation_rows if not note_source_set or citation.source_id in note_source_set],
            default=[
                citation.id
                for citation in citation_rows
                if citation.id in set(scoped_selection.get("citation_refs") or [])
                and (not note_source_set or citation.source_id in note_source_set)
            ] if scope_active else [],
            key=f"reading_note_citations:{selected}",
        )
        if note_sources:
            if len(note_sources) == 1:
                note_body = create_reading_note_markdown(
                    _pdir,
                    note_sources[0],
                    claim_refs=note_claims,
                    chunk_refs=note_chunks,
                    citation_refs=note_citations,
                )
            else:
                note_body = create_reading_note_pack_markdown(
                    _pdir,
                    note_sources,
                    claim_refs=note_claims,
                    chunk_refs=note_chunks,
                    citation_refs=note_citations,
                )
            note_manifest = build_research_export_manifest(
                _pdir,
                source_refs=note_sources,
                claim_refs=note_claims,
                citation_refs=note_citations,
            )
            st.text_area(
                ui["body"],
                value=note_body,
                height=240,
                key=f"reading_note_body:{selected}:{'-'.join(note_sources)}",
            )
            n1, n2 = st.columns(2)
            with n1:
                st.download_button(
                    _l("download_note", "Download note"),
                    data=note_body,
                    file_name=(
                        f"{note_sources[0].replace(':', '-')}-reading-note.md"
                        if len(note_sources) == 1
                        else "research-reading-note-pack.md"
                    ),
                )
            with n2:
                if st.button(_l("save_note", "Save note")):
                    try:
                        if len(note_sources) == 1:
                            path = save_paper_note(
                                _pdir,
                                note_sources[0],
                                note_body,
                                metadata={
                                    "claim_refs": note_claims,
                                    "chunk_refs": note_chunks,
                                    "citation_refs": note_citations,
                                },
                            )
                        else:
                            path = save_research_export(
                                _pdir,
                                note_body,
                                format="markdown",
                                prefix="reading-note-pack",
                                manifest={
                                    **note_manifest,
                                    "chunk_refs": note_chunks,
                                },
                            )
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(str(path))
                    except Exception as exc:
                        st.error(str(exc))

    st.subheader(ui["synthesis_drafts"])
    claim_rows = load_research_claims(_pdir)
    claim_ids = [claim.id for claim in claim_rows]
    with st.expander(ui["create_synthesis_draft"], expanded=not load_research_drafts(_pdir)):
        with st.form(f"research_synthesis_create:{selected}"):
            title = st.text_input(ui["title_label"], key=f"research_synthesis_title:{selected}")
            selected_claims = st.multiselect(
                ui["research_claims"],
                options=claim_ids,
                format_func=lambda cid: next(
                    (f"{cid} - {claim.text[:80]}" for claim in claim_rows if claim.id == cid),
                    cid,
                ),
            )
            body = st.text_area(
                ui["body"],
                height=180,
                key=f"research_synthesis_body:{selected}",
            )
            submitted = st.form_submit_button(ui["create"], type="primary")
        if submitted:
            try:
                draft = draft_synthesis_from_claims(
                    _pdir,
                    title,
                    selected_claims,
                    body=body,
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=draft["id"]))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    drafts = load_research_drafts(_pdir)
    if not drafts:
        st.caption(ui["drafts_empty"])
        return
    st.dataframe(
        [
            {
                "id": draft.get("id"),
                "status": draft.get("status"),
                "title": draft.get("title"),
                "claims": ", ".join(draft.get("claim_refs") or []),
                "sources": ", ".join(draft.get("source_refs") or []),
                "citations": ", ".join(draft.get("citation_refs") or []),
            }
            for draft in drafts
        ],
        use_container_width=True,
        hide_index=True,
    )
    draft_id = st.selectbox(
        ui["synthesis_draft_id"],
        options=[str(draft.get("id")) for draft in drafts],
        key=f"research_blog_draft:{selected}",
    )
    try:
        draft_review = build_synthesis_draft_review(_pdir, draft_id)
        with st.expander(_l("synthesis_review", "Synthesis coverage review"), expanded=True):
            coverage = draft_review.get("coverage") or {}
            c1, c2, c3 = st.columns(3)
            c1.metric(ui["research_claims"], coverage.get("claims", 0))
            c2.metric(_l("sources_total", "Sources"), coverage.get("sources", 0))
            c3.metric(ui["research_citations"], coverage.get("citations", 0))
            argument_map = list(draft_review.get("argument_map") or [])
            if argument_map:
                st.dataframe(argument_map, use_container_width=True, hide_index=True)
            warnings = draft_review.get("warnings") if isinstance(draft_review.get("warnings"), dict) else {}
            for claim_ref in warnings.get("missing_citation_claim_refs") or []:
                st.warning(
                    _l(
                        "synthesis_missing_claim_citation",
                        "Claim {claim_id} is in this draft without a linked citation.",
                    ).format(claim_id=claim_ref)
                )
            for citation_ref in warnings.get("broken_citation_refs") or []:
                st.warning(
                    _l(
                        "synthesis_broken_citation",
                        "Citation {citation_id} needs quote review before public use.",
                    ).format(citation_id=citation_ref)
                )
    except Exception as exc:
        st.warning(str(exc))
    st.subheader(_l("output_candidates", "Output Candidates"))
    blog_tab, project_tab, resume_tab = st.tabs(
        [
            _l("blog_candidate", "Blog Draft"),
            _l("project_update_candidate", "Project Update"),
            _l("resume_bullet_candidate", "Resume Bullet"),
        ]
    )
    with blog_tab:
        try:
            candidate = research_draft_to_blog_candidate(_pdir, draft_id)
            st.code(
                yaml.dump(
                    {key: value for key, value in candidate.items() if key != "body"},
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                language="yaml",
            )
            st.text_area(
                ui["body"],
                value=str(candidate.get("body") or ""),
                height=240,
                disabled=True,
                key=f"blog_candidate_body:{selected}:{draft_id}",
            )
            _, blog_blockers = _render_research_candidate_manifest(
                _pdir,
                candidate,
                f"blog_candidate:{selected}:{draft_id}",
            )
        except Exception as exc:
            candidate = None
            blog_blockers = []
            st.warning(str(exc))
        confirm_candidate_blockers = not blog_blockers or st.checkbox(
            _l(
                "confirm_blog_candidate_blockers",
                "Create draft anyway; I will fix private, unpromoted, or broken refs before public use.",
            ),
            value=False,
            key=f"research_blog_candidate_blockers:{selected}:{draft_id}",
        )
        if st.button(
            ui["create_blog_draft"],
            disabled=candidate is None or not confirm_candidate_blockers,
            key=f"create_blog_draft:{selected}:{draft_id}",
        ):
            try:
                path = create_blog_draft(
                    selected,
                    title=str(candidate.get("title") or draft_id),
                    body=str(candidate.get("body") or ""),
                    tags=list(candidate.get("tags") or []),
                    summary=str(candidate.get("summary") or ""),
                    related_evidence=list(candidate.get("related_evidence") or []),
                    related_kanban=list(candidate.get("related_kanban") or []),
                    related_claims=list(candidate.get("related_claims") or []),
                    related_sources=list(candidate.get("related_sources") or []),
                    related_research_claims=list(candidate.get("related_research_claims") or []),
                    related_citations=list(candidate.get("related_citations") or []),
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(str(path))
            except Exception as exc:
                st.error(str(exc))
    with project_tab:
        try:
            project_options = research_output_project_options(_pdir)
            project_labels = {
                row["id"]: f"{row.get('title') or row['id']} ({row['id']})"
                for row in project_options
            }
            project_id = st.selectbox(
                _l("project_update_project", "Project"),
                options=["", *project_labels],
                format_func=lambda ref: _l("project_update_no_project", "No project selected") if not ref else project_labels.get(ref, ref),
                key=f"project_update_candidate_project:{selected}:{draft_id}",
            )
            project_candidate = research_draft_to_project_update_candidate(
                _pdir,
                draft_id,
                project_id=project_id,
            )
            st.code(
                yaml.dump(
                    {key: value for key, value in project_candidate.items() if key != "body"},
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                language="yaml",
            )
            st.text_area(
                ui["body"],
                value=str(project_candidate.get("body") or ""),
                height=220,
                disabled=True,
                key=f"project_update_candidate_body:{selected}:{draft_id}:{project_id}",
            )
            _render_research_candidate_manifest(
                _pdir,
                project_candidate,
                f"project_update_candidate:{selected}:{draft_id}:{project_id or 'none'}",
            )
        except Exception as exc:
            st.warning(str(exc))
    with resume_tab:
        try:
            bullets = research_draft_to_resume_bullet_candidates(_pdir, draft_id)
            for index, bullet in enumerate(bullets, start=1):
                st.markdown(f"**{index}.** {bullet.get('text') or ''}")
                st.code(
                    yaml.dump(
                        {key: value for key, value in bullet.items() if key != "text"},
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
                _render_research_candidate_manifest(
                    _pdir,
                    bullet,
                    f"resume_bullet_candidate:{selected}:{draft_id}:{index}",
                )
        except Exception as exc:
            st.warning(str(exc))


def _render_connector_candidate_picker(
    preview: dict[str, object],
    *,
    key_prefix: str,
) -> tuple[list[str], str, str]:
    st.subheader(_l("connector_inbox", "Connector Inbox"))
    p1, p2, p3 = st.columns(3)
    p1.metric(_l("discovered", "Discovered"), preview.get("discovered", 0))
    p2.metric(_l("importable", "Importable"), preview.get("importable", 0))
    p3.metric(_l("duplicates", "Duplicates"), preview.get("skipped", 0))
    for warning in preview.get("warnings") or []:
        st.warning(str(warning))

    node_options = _node_options(include_unsorted=False)
    metadata_only_ref = "__metadata_only__"
    target_options = {
        "": _l("source_inbox", "Source Inbox"),
        metadata_only_ref: _l("metadata_only", "Metadata only"),
        **node_options,
    }
    target_value = st.selectbox(
        _l("connector_import_target", "Import target"),
        options=list(target_options),
        format_func=lambda ref: target_options.get(ref, ref),
        key=f"{key_prefix}:target",
    )
    target_node = "" if target_value == metadata_only_ref else target_value
    target_kind = (
        "metadata_only"
        if target_value == metadata_only_ref
        else "collection"
        if target_node
        else "source_inbox"
    )
    selected_fingerprints: list[str] = []
    for index, candidate in enumerate(preview.get("candidates") or []):
        if not isinstance(candidate, dict):
            continue
        item = candidate.get("item") if isinstance(candidate.get("item"), dict) else {}
        duplicate = candidate.get("duplicate") if isinstance(candidate.get("duplicate"), dict) else {}
        fingerprint = str(candidate.get("fingerprint") or "")
        with st.container(border=True):
            head, pick = st.columns([4, 1], vertical_alignment="center")
            with head:
                st.markdown(f"**{item.get('title') or fingerprint}**")
                st.caption(
                    " · ".join(
                        str(value)
                        for value in [
                            item.get("provider"),
                            item.get("kind"),
                            item.get("published"),
                            item.get("url"),
                        ]
                        if value
                    )
                )
                if item.get("summary"):
                    st.write(_short_text(item.get("summary"), 320))
                if duplicate.get("is_duplicate"):
                    st.warning(
                        _l(
                            "connector_duplicate",
                            "Duplicate candidate: {reason} -> {source_id}",
                        ).format(
                            reason=duplicate.get("reason") or "duplicate",
                            source_id=duplicate.get("existing_source_id") or "",
                        )
                    )
            with pick:
                selected_candidate = st.checkbox(
                    _l("import_candidate", "Import"),
                    value=bool(candidate.get("selected")) and not bool(duplicate.get("is_duplicate")),
                    disabled=bool(duplicate.get("is_duplicate")) or not fingerprint,
                    key=f"{key_prefix}:candidate:{index}",
                )
            if selected_candidate and fingerprint:
                selected_fingerprints.append(fingerprint)
    return selected_fingerprints, target_node, target_kind


def _connector_import_result_key() -> str:
    return f"research_connector_import_result:{selected}"


def _remember_connector_import_result(
    result,
    *,
    provider: str,
    target_node: str,
    target_kind: str,
) -> None:
    if not result.imported_source_ids:
        return
    st.session_state[_connector_import_result_key()] = {
        "provider": provider,
        "target_node": target_node,
        "target_kind": target_kind,
        "imported": int(result.imported),
        "skipped": int(result.skipped),
        "source_ids": [str(source_id) for source_id in result.imported_source_ids if str(source_id)],
    }


def _render_connector_import_next_actions() -> None:
    state = st.session_state.get(_connector_import_result_key())
    if not isinstance(state, dict):
        return
    source_ids = [str(source_id) for source_id in state.get("source_ids") or [] if str(source_id)]
    source_map = load_research_sources(selected).by_id()
    imported = [source_map[source_id] for source_id in source_ids if source_id in source_map]
    if not imported:
        st.session_state.pop(_connector_import_result_key(), None)
        return

    papers = [source for source in imported if source.kind == "paper"]
    pdf_ready = [source for source in papers if (source.metadata or {}).get("pdf_asset_ref")]
    first_paper = papers[0] if papers else None
    first_pdf = pdf_ready[0] if pdf_ready else None
    target_node = str(state.get("target_node") or "")
    target_kind = str(state.get("target_kind") or ("collection" if target_node else "source_inbox"))
    review_url = (
        _paper_library_workspace_url(node_id=target_node, detail_id=first_paper.id)
        if target_node and first_paper
        else _paper_library_workspace_url(view="unsorted", detail_id=first_paper.id)
        if first_paper
        else ""
    )

    try:
        container = st.container(border=True)
    except TypeError:
        container = st.container()
    with container:
        st.success(
            _l(
                "connector_import_next_actions",
                "Imported {imported} source(s). Continue with the imported queue below.",
            ).format(imported=state.get("imported") or len(imported))
        )
        st.caption(
            " · ".join(
                part
                for part in [
                    str(state.get("provider") or ""),
                    (
                        _l("metadata_only", "Metadata only")
                        if target_kind == "metadata_only"
                        else _l("connector_target_collection", "Collection target")
                        if target_node
                        else _l("source_inbox", "Source Inbox")
                    ),
                    (
                        _l("connector_skipped_count", "Skipped {skipped}").format(skipped=state.get("skipped"))
                        if state.get("skipped")
                        else ""
                    ),
                ]
                if part
            )
        )
        for source in imported[:4]:
            st.write(f"- **{source.title or source.id}** `{source.id}`")
        if len(imported) > 4:
            st.caption(_l("connector_more_imports", "And {count} more imported source(s).").format(count=len(imported) - 4))

        a1, a2, a3, a4, a5 = st.columns(5)
        with a1:
            if first_paper:
                _render_sidecar_link_button(
                    _l("open_in_paper_library", "Open in Paper Library"),
                    _paper_library_workspace_url(node_id=target_node, detail_id=first_paper.id),
                    key=f"connector_open_library:{selected}:{first_paper.id}:{target_node}",
                    icon=":material/library_books:",
                    type="primary",
                    use_container_width=True,
                )
            else:
                st.button(
                    _l("open_in_paper_library", "Open in Paper Library"),
                    disabled=True,
                    key=f"connector_open_library_disabled:{selected}",
                    use_container_width=True,
                )
        with a2:
            if review_url:
                _render_sidecar_link_button(
                    _l("review_imported_sources", "Review imported"),
                    review_url,
                    key=f"connector_review_imported:{selected}:{first_paper.id if first_paper else ''}:{target_node}",
                    icon=":material/rule:",
                    use_container_width=True,
                )
            else:
                st.button(
                    _l("review_imported_sources", "Review imported"),
                    disabled=True,
                    key=f"connector_review_imported_disabled:{selected}",
                    use_container_width=True,
                )
        with a3:
            if first_pdf:
                _render_sidecar_link_button(
                    _l("open_reader", "Open Reader"),
                    _reader_view_url(first_pdf.id),
                    key=f"connector_open_reader:{selected}:{first_pdf.id}",
                    icon=":material/menu_book:",
                    use_container_width=True,
                )
            else:
                st.button(
                    _l("open_reader", "Open Reader"),
                    disabled=True,
                    key=f"connector_open_reader_disabled:{selected}",
                    use_container_width=True,
                )
        with a4:
            if st.button(
                _l("run_extraction", "Run extraction"),
                key=f"connector_prepare_reader:{selected}:{':'.join(source_ids[:3])}",
                disabled=not pdf_ready,
                icon=":material/auto_fix_high:",
                use_container_width=True,
            ):
                result = _prepare_reader_artifacts_for_sources([source.id for source in pdf_ready])
                st.success(
                    _l("connector_prepared_sources", "Prepared Reader artifacts for {count} source(s).").format(
                        count=len(result.get("prepared") or [])
                    )
                )
                for warning in result.get("warnings") or []:
                    st.warning(str(warning))
        with a5:
            if st.button(
                _l("dismiss", "Dismiss"),
                key=f"connector_import_next_actions_dismiss:{selected}",
                icon=":material/close:",
                use_container_width=True,
            ):
                st.session_state.pop(_connector_import_result_key(), None)
                st.rerun()
        if not papers:
            st.caption(
                _l(
                    "connector_non_paper_review_hint",
                    "Non-paper imports stay in the Source Inbox queue on the Inbox & Connectors tab.",
                )
            )
        elif not pdf_ready:
            st.caption(
                _l(
                    "connector_pdf_needed_hint",
                    "Reader and extraction actions appear after an imported paper has a local PDF asset.",
                )
            )


def _render_connector_provider_cards(rows: list[dict[str, object]]) -> None:
    st.markdown(f"**{_l('connector_provider_status', 'Provider status')}**")
    columns = st.columns(3)
    for index, provider in enumerate(CONNECTOR_PROVIDERS):
        provider_rows = [row for row in rows if str(row.get("provider") or "") == provider]
        latest = max(
            provider_rows,
            key=lambda row: str(row.get("last_run") or ""),
            default={},
        )
        last_result = latest.get("last_result") if isinstance(latest.get("last_result"), dict) else {}
        with columns[index % len(columns)]:
            with st.container(border=True):
                st.markdown(f"**{provider}**")
                if not provider_rows:
                    st.caption(_l("connector_provider_unconfigured", "No saved automation connector."))
                else:
                    enabled_count = sum(1 for row in provider_rows if bool(row.get("enabled", True)))
                    st.caption(
                        _l(
                            "connector_provider_configured",
                            "{configured} configured · {enabled} enabled",
                        ).format(configured=len(provider_rows), enabled=enabled_count)
                    )
                    s1, s2 = st.columns(2)
                    s1.metric(_l("status", "Status"), str(latest.get("status") or "idle"))
                    s2.metric(_l("last_imported", "Imported"), last_result.get("imported", 0))
                    st.caption(
                        " · ".join(
                            part
                            for part in [
                                f"{_l('last_run', 'Last run')}: {latest.get('last_run') or '-'}",
                                f"{_l('skipped', 'Skipped')}: {last_result.get('skipped', 0)}",
                            ]
                            if part
                        )
                    )
                    if last_result.get("error"):
                        st.warning(str(last_result.get("error")))
                if provider in {"x_twitter", "xiaohongshu"}:
                    st.caption(
                        _l(
                            "connector_manual_provider_hint",
                            "Manual import remains available when automation is unavailable.",
                        )
                    )


def _render_connector_run_history(rows: list[dict[str, object]]) -> None:
    history = []
    for row in rows:
        last_result = row.get("last_result") if isinstance(row.get("last_result"), dict) else {}
        history.append(
            {
                "id": row.get("id"),
                "provider": row.get("provider"),
                "status": row.get("status") or "idle",
                "last_run": row.get("last_run") or "",
                "discovered": last_result.get("discovered", 0),
                "imported": last_result.get("imported", 0),
                "skipped": last_result.get("skipped", 0),
                "selected": last_result.get("selected", ""),
                "warnings": "; ".join(str(item) for item in last_result.get("warnings") or []),
                "error": last_result.get("error") or "",
            }
        )
    if not history:
        return
    with st.expander(_l("connector_run_history", "Connector run history"), expanded=False):
        st.dataframe(history, use_container_width=True, hide_index=True)


def _render_connectors() -> None:
    st.subheader(ui["connectors"])
    st.caption(ui["connectors_caption"])
    rows = list(load_connectors(_pdir).get("connectors") or [])
    _render_connector_provider_cards(rows)
    _render_connector_run_history(rows)
    _render_connector_import_next_actions()
    manual_key = f"research_manual_connector_preview:{selected}"
    with st.expander(_l("manual_connector_import", "Manual connector import"), expanded=False):
        with st.form(f"research_manual_connector:{selected}"):
            manual_provider = st.selectbox(
                ui["connector_provider"],
                CONNECTOR_PROVIDERS,
                key=f"research_manual_connector_provider:{selected}",
            )
            manual_privacy = st.selectbox(
                ui["privacy_default"],
                ["private", "public"],
                key=f"research_manual_connector_privacy:{selected}",
            )
            manual_raw = st.text_area(
                _l("manual_connector_items", "Paste URLs, CSV, or JSON list"),
                height=120,
                key=f"research_manual_connector_raw:{selected}",
            )
            manual_preview = st.form_submit_button(_l("preview", "Preview"), type="primary")
        if manual_preview:
            try:
                st.session_state[manual_key] = {
                    "provider": manual_provider,
                    "privacy": manual_privacy,
                    "raw": manual_raw,
                    "preview": preview_manual_connector_items(_pdir, manual_provider, manual_raw),
                }
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        manual_state = st.session_state.get(manual_key)
        if isinstance(manual_state, dict) and isinstance(manual_state.get("preview"), dict):
            selected_manual, manual_target, manual_target_kind = _render_connector_candidate_picker(
                manual_state["preview"],
                key_prefix=f"research_manual_connector_picker:{selected}",
            )
            if st.button(
                _l("import_selected_connector_items", "Import selected"),
                type="primary",
                disabled=not selected_manual,
                key=f"research_manual_connector_import:{selected}",
            ):
                try:
                    assert_files_current([_sources_path])
                    result = import_manual_connector_items(
                        _pdir,
                        str(manual_state.get("provider") or manual_provider),
                        manual_state.get("raw") or "",
                        selected_manual,
                        privacy_default=str(manual_state.get("privacy") or "private"),
                        target={
                            "kind": manual_target_kind,
                            "node_id": manual_target,
                        },
                    )
                    _remember_connector_import_result(
                        result,
                        provider=str(manual_state.get("provider") or manual_provider),
                        target_node=manual_target,
                        target_kind=manual_target_kind,
                    )
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(
                        _l(
                            "connector_imported_count",
                            "Imported {imported} candidate(s); skipped {skipped}.",
                        ).format(imported=result.imported, skipped=result.skipped)
                    )
                    st.session_state.pop(manual_key, None)
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    rows = list(load_connectors(_pdir).get("connectors") or [])
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.caption(ui["connectors_empty"])

    with st.expander(ui["configure_connector"], expanded=not rows):
        with st.form(f"research_connector_config:{selected}"):
            provider = st.selectbox(ui["connector_provider"], CONNECTOR_PROVIDERS)
            connector_id = st.text_input(ui["connector_id"])
            query = st.text_input(ui["connector_query"])
            enabled = st.checkbox(ui["connector_enabled"], value=True)
            privacy_default = st.selectbox(ui["privacy_default"], ["private", "public"])
            options_raw = st.text_area(ui["connector_options"], height=90)
            submitted = st.form_submit_button(ui["save"], type="primary")
        if submitted:
            try:
                options = yaml.safe_load(options_raw) if options_raw.strip() else {}
                if options is None:
                    options = {}
                if not isinstance(options, dict):
                    raise ValueError("Connector options must be a YAML mapping.")
                row = upsert_connector(
                    _pdir,
                    provider=provider,
                    connector_id=connector_id,
                    query=query,
                    enabled=enabled,
                    privacy_default=privacy_default,
                    options=options,
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=row["id"]))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    rows = list(load_connectors(_pdir).get("connectors") or [])
    if not rows:
        return
    picked = st.selectbox(
        ui["connector_id"],
        options=[str(row.get("id")) for row in rows],
        key=f"research_connector_run:{selected}",
    )
    preview_key = f"research_connector_preview:{selected}:{picked}"
    dry_col, run_col = st.columns(2)
    with dry_col:
        if st.button(ui["connector_dry_run"]):
            try:
                st.session_state[preview_key] = discover_connector_items(_pdir, picked)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with run_col:
        if st.button(ui["connector_run_now"], type="primary"):
            try:
                assert_files_current([_sources_path, _research_connectors_path])
                result = sync_connector(_pdir, picked, dry_run=False)
                refresh_file_snapshots([_sources_path, _research_connectors_path])
                stash_git_backup_results()
                clear_web_cache()
                st.code(
                    yaml.dump(result.to_dict(), allow_unicode=True, default_flow_style=False, sort_keys=False),
                    language="yaml",
                )
            except Exception as exc:
                st.error(str(exc))

    preview = st.session_state.get(preview_key)
    if not isinstance(preview, dict):
        return
    selected_fingerprints, target_node, target_kind = _render_connector_candidate_picker(
        preview,
        key_prefix=f"research_connector_picker:{selected}:{picked}",
    )

    if st.button(
        _l("import_selected_connector_items", "Import selected"),
        type="primary",
        disabled=not selected_fingerprints,
        key=f"research_connector_import_selected:{selected}:{picked}",
    ):
        try:
            assert_files_current([_sources_path, _research_connectors_path])
            result = import_connector_items(
                _pdir,
                picked,
                selected_fingerprints,
                target={
                    "kind": target_kind,
                    "node_id": target_node,
                },
            )
            _remember_connector_import_result(
                result,
                provider=str(preview.get("provider") or picked),
                target_node=target_node,
                target_kind=target_kind,
            )
            refresh_file_snapshots([_sources_path, _research_connectors_path])
            stash_git_backup_results()
            clear_web_cache()
            st.success(
                _l(
                    "connector_imported_count",
                    "Imported {imported} candidate(s); skipped {skipped}.",
                ).format(imported=result.imported, skipped=result.skipped)
            )
            st.session_state.pop(preview_key, None)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


_head_l, _head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
with _head_l:
    st.title(ui["title"])
    st.caption(ui["page_context_line"])
    _render_research_sidecar_status()
with _head_goal:
    _goal_col, _help_col, _ai_col = st.columns(
        [4, 2, 2],
        gap="small",
        vertical_alignment="center",
    )
    with _goal_col:
        render_current_goal_strip(selected, compact=True, align="right")
    with _help_col:
        with st.popover(
            _l("page_help_short", "Guide"),
            key=f"research_help_popover:{selected}",
            use_container_width=False,
        ):
            _render_research_help()
    with _ai_col:
        with st.popover(
            _l("ai_config_short", "AI"),
            key=f"research_ai_config_popover:{selected}",
            use_container_width=False,
        ):
            _render_ai_config_panel()

inbox = load_research_sources(selected)

tab_overview, tab_library, tab_claims, tab_export, tab_advanced = st.tabs(
    [
        _l("overview", "Overview"),
        _l("paper_library", "Paper Library"),
        ui["claims_citations"],
        _l("synthesis_export", "Synthesis / Export"),
        _l("inbox_connectors", "Inbox & Connectors"),
    ]
)

with tab_overview:
    _render_workspace_overview(inbox)

with tab_library:
    _render_paper_library(inbox)

with tab_claims:
    _render_claims_citations(inbox)

with tab_export:
    _render_synthesis_drafts()

with tab_advanced:
    st.subheader(ui["source_inbox"])
    _render_source_queue(inbox)
    st.divider()
    with st.expander(ui["add_source"], expanded=not inbox.sources):
        _render_source_form(
            inbox,
            prefix=f"research_source_add_{selected}",
        )
    st.divider()
    _render_candidate_preview(inbox)
    st.divider()
    st.subheader(ui["reading_room"])
    _render_reading_room(inbox)
    st.divider()
    _render_connectors()
