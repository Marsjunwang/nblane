"""AI configuration panel for the Research Studio."""
from __future__ import annotations

import re
import time
from dataclasses import replace
from datetime import datetime

import streamlit as st

from nblane.core import codex_adapter
from nblane.core import llm as llm_client
from nblane.core.web_preferences import (
    AI_ACTION_DEFAULT_BACKENDS,
    load_web_preferences,
    update_web_preferences,
)

from .context import ResearchContext
from ._helpers import _l


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


def _ai_action_prefs(ctx) -> dict[str, dict[str, str]]:
    selected = ctx.selected
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


def _model_picker(ctx, 
    label: str,
    pref_name: str,
    current: str,
    default_model: str,
    suggestions: tuple[str, ...],
) -> str:
    selected = ctx.selected
    ui = ctx.ui
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
            _l(ui, "ai_config_use_default", "Use app default")
            if value == _MODEL_DEFAULT
            else _l(ui, "ai_config_custom_model", "Custom model")
            if value == _MODEL_CUSTOM
            else value
        ),
        key=f"ai_config:{selected}:{pref_name}:choice",
    )
    if choice == _MODEL_DEFAULT:
        return ""
    if choice == _MODEL_CUSTOM:
        return st.text_input(
            _l(ui, "ai_config_custom_model", "Custom model"),
            value=current if current and current not in model_suggestions else "",
            key=f"ai_config:{selected}:{pref_name}:custom",
        ).strip()
    return str(choice).strip()


def _backend_picker(ctx, label: str, pref_name: str, current: str, default_backend: str) -> str:
    selected = ctx.selected
    ui = ctx.ui
    options = [_BACKEND_DEFAULT, "llm", "codex"]
    current = str(current or "").strip()
    initial = current if current in {"llm", "codex"} else _BACKEND_DEFAULT
    choice = st.selectbox(
        label,
        options,
        index=options.index(initial),
        format_func=lambda value: (
            f"{_l(ui, 'ai_config_use_default', 'Use app default')} ({_backend_label(default_backend)})"
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


def _effective_action_caption(ctx, 
    action_name: str,
    config: dict[str, str],
    *,
    llm_default: str,
    codex_default: str,
) -> str:
    ui = ctx.ui
    backend = _effective_backend(action_name, config)
    model = _effective_model(
        action_name,
        config,
        llm_default=llm_default,
        codex_default=codex_default,
    )
    model_label = model or (
        _l(ui, "ai_config_codex_cli_default", "Codex CLI default")
        if backend == "codex"
        else _l(ui, "missing", "missing")
    )
    test = _model_test_summary(ctx, backend, model, action_name=action_name)
    bits = [
        f"{_l(ui, 'ai_config_effective_backend', 'Effective backend')}: {_backend_label(backend)}",
        f"{_l(ui, 'ai_config_effective_model', 'Effective model')}: {model_label}",
    ]
    if test:
        bits.append(test)
    return " · ".join(bits)


def _model_test_key(ctx, backend: str, model: str, *, action_name: str = "") -> str:
    selected = ctx.selected
    safe_model = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(model or "default")).strip("_")
    safe_action = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(action_name or "global")).strip("_")
    return f"ai_config:{selected}:test:{safe_action or 'global'}:{backend}:{safe_model or 'default'}"


def _record_model_test(ctx, 
    backend: str,
    model: str,
    ok: bool,
    latency: float,
    message: str,
    *,
    action_name: str = "",
) -> None:
    st.session_state[_model_test_key(ctx, backend, model, action_name=action_name)] = {
        "ok": bool(ok),
        "latency": float(latency),
        "message": str(message or "").strip()[:240],
        "tested_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def _model_test_summary(ctx, backend: str, model: str, *, action_name: str = "") -> str:
    ui = ctx.ui
    result = st.session_state.get(_model_test_key(ctx, backend, model, action_name=action_name))
    if not isinstance(result, dict):
        return ""
    status = (
        _l(ui, "ai_config_available", "available")
        if result.get("ok")
        else _l(ui, "ai_config_unavailable", "unavailable")
    )
    latency = float(result.get("latency") or 0.0)
    return f"{status}, {latency:.1f}s"


def _run_llm_availability_test(ctx, model: str, *, action_name: str = "") -> None:
    ui = ctx.ui
    started = time.perf_counter()
    if not llm_client.is_configured():
        message = _l(ui, "ai_config_llm_unconfigured", "LLM API key is not configured.")
        _record_model_test(ctx, "llm", model, False, time.perf_counter() - started, message, action_name=action_name)
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
        _record_model_test(ctx, "llm", model, False, latency, reply, action_name=action_name)
        st.warning(reply)
    else:
        _record_model_test(ctx, "llm", model, True, latency, reply or "OK", action_name=action_name)
        st.success(
            f"{_l(ui, 'ai_config_model_available', 'Model test succeeded.')} ({latency:.1f}s)"
        )


def _run_codex_availability_test(ctx, model: str, *, action_name: str = "") -> None:
    selected = ctx.selected
    ui = ctx.ui
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
        _record_model_test(ctx, "codex", model, True, latency, result.output or "OK", action_name=action_name)
        st.success(
            f"{_l(ui, 'ai_config_model_available', 'Model test succeeded.')} ({latency:.1f}s)"
        )
    else:
        message = codex_adapter.readable_codex_error(
            result.error,
            result.stderr,
            result.output,
            result.stdout,
        )
        _record_model_test(ctx, "codex", model, False, latency, message, action_name=action_name)
        st.warning(message)


def _run_action_availability_test(ctx, 
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
        _run_codex_availability_test(ctx, model, action_name=action_name)
    else:
        _run_llm_availability_test(ctx, model, action_name=action_name)


def _render_action_config_row(ctx, 
    action_name: str,
    label: str,
    help_text: str,
    current: dict[str, str],
    *,
    llm_default: str,
    codex_default: str,
) -> dict[str, str]:
    selected = ctx.selected
    ui = ctx.ui
    default_backend = _default_backend_for_action(action_name)
    st.markdown(f"**{label}**")
    st.caption(help_text)
    cols = st.columns([1.05, 1.25, 1.25, 0.85], gap="small")
    with cols[0]:
        backend = _backend_picker(ctx, 
            _l(ui, "ai_config_backend", "Backend"),
            f"{action_name}:backend",
            current.get("backend", ""),
            default_backend,
        )
    with cols[1]:
        llm_model = _model_picker(ctx, 
            _l(ui, "ai_config_llm_model", "LLM model"),
            f"{action_name}:llm_model",
            current.get("llm_model", ""),
            llm_default,
            _LLM_MODEL_SUGGESTIONS,
        )
    with cols[2]:
        codex_model = _model_picker(ctx, 
            _l(ui, "ai_config_codex_model", "Codex model"),
            f"{action_name}:codex_model",
            current.get("codex_model", ""),
            codex_default,
            _CODEX_MODEL_SUGGESTIONS,
        )
    test_clicked = False
    with cols[3]:
        st.caption(_l(ui, "ai_config_test", "Test"))
        test_clicked = st.form_submit_button(
            _l(ui, "ai_config_test_model", "Test model"),
            key=f"ai_config:{selected}:{action_name}:test_model",
            use_container_width=True,
        )
    next_config = {
        "backend": backend,
        "llm_model": llm_model,
        "codex_model": codex_model,
    }
    st.caption(
        _effective_action_caption(ctx, 
            action_name,
            next_config,
            llm_default=llm_default,
            codex_default=codex_default,
        )
    )
    if test_clicked:
        _run_action_availability_test(ctx, 
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


def _render_ai_config_panel(ctx) -> None:
    selected = ctx.selected
    ui = ctx.ui
    actions = _ai_action_prefs(ctx)
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
            f"{llm_cfg.get('model') or _l(ui, 'missing', 'missing')}"
        )
    with runtime_cols[1]:
        codex_bits = [
            "installed" if codex_status.installed else "missing",
            "logged in" if codex_status.logged_in else "login unknown",
            codex_cfg.model or _l(ui, "ai_config_codex_cli_default", "Codex CLI default"),
        ]
        st.caption("Codex: " + " · ".join(codex_bits))
        if codex_status.error:
            st.caption(codex_status.error)

    next_actions: dict[str, dict[str, str]] = {}
    with st.form(f"ai_config_form:{selected}", border=False):
        st.caption(
            _l(ui, 
                "ai_config_caption",
                "Choose the AI backend and model per feature. Leave fields on app default to follow the global sidebar/runtime configuration.",
            )
        )
        for group_key, group_label, rows in _AI_CONFIG_GROUPS:
            with st.expander(
                _l(ui, f"ai_config_group_{group_key}", group_label),
                expanded=group_key == "paper",
            ):
                for action_name, label, help_text in rows:
                    next_actions[action_name] = _render_action_config_row(ctx, 
                        action_name,
                        _l(ui, f"ai_config_label_{action_name}", label),
                        _l(ui, f"ai_config_help_{action_name}", help_text),
                        actions.get(action_name, {}),
                        llm_default=llm_default,
                        codex_default=codex_default,
                    )
        if st.form_submit_button(_l(ui, "save", "Save"), type="primary", use_container_width=True):
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
            st.success(_l(ui, "ai_config_saved", "AI preferences saved."))
            st.rerun()


