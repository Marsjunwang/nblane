"""Shared sidebar profile selector for Streamlit pages."""

from __future__ import annotations

import os
import re
from pathlib import Path

import streamlit as st

from nblane.core import git_backup
from nblane.core import llm as llm_client
from nblane.core.file_state import (
    FileConflictError,
    FileSnapshot,
    assert_unchanged,
    snapshot_file,
)
from nblane.core.io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
    init_profile,
    list_profiles,
    profile_dir,
)
from nblane.web_auth import (
    allowed_profiles,
    can_create_profiles,
)
from nblane.web_i18n import common_ui


def _template_score(name: str) -> int:
    """Count template placeholders in SKILL.md (lower is better)."""
    skill_path = profile_dir(name) / "SKILL.md"
    if not skill_path.exists():
        return 0
    try:
        content = skill_path.read_text(encoding="utf-8")
    except OSError:
        return 0
    return len(re.findall(r"\{[^}]+\}", content))


def _latest_profile(profiles: list[str]) -> str:
    """Return the most recently modified profile name."""
    latest_name = profiles[0]
    latest_ts = -1.0
    for name in profiles:
        skill_path = profile_dir(name) / "SKILL.md"
        target: Path = skill_path
        if not target.exists():
            target = profile_dir(name)
        try:
            ts = target.stat().st_mtime
        except OSError:
            ts = -1.0
        if ts > latest_ts:
            latest_ts = ts
            latest_name = name
    return latest_name


_PERSIST_KEY = "_profile_choice"
_GIT_BACKUP_NOTICE_KEY = "_nblane_git_backup_notices"
_LLM_CUSTOM_MODEL_CHOICE = "__custom_model__"
_LLM_PROVIDER_KEY = "_nblane_llm_provider"
_LLM_LAST_PROVIDER_KEY = "_nblane_llm_last_provider"
_LLM_BASE_URL_KEY = "_nblane_llm_base_url"
_LLM_MODEL_CHOICE_KEY = "_nblane_llm_model_choice"
_LLM_CUSTOM_MODEL_KEY = "_nblane_llm_custom_model"
_LLM_API_KEY_KEY = "_nblane_llm_api_key"
_LLM_REPLY_LANG_KEY = "_nblane_llm_reply_lang"

_LLM_PROVIDER_PRESETS: dict[str, tuple[str, tuple[str, ...]]] = {
    "OpenAI": (
        "https://api.openai.com/v1",
        ("gpt-4o", "gpt-4o-mini"),
    ),
    "Qwen / DashScope": (
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ("qwen3.6-plus", "qwen-plus", "qwen-max", "qwen-turbo"),
    ),
    "DeepSeek": (
        "https://api.deepseek.com",
        ("deepseek-chat", "deepseek-reasoner"),
    ),
    "Ollama": (
        "http://localhost:11434/v1",
        ("llama3", "qwen2.5"),
    ),
    "Custom": ("", ()),
}


def _sync_to_persistent() -> None:
    """Copy widget value to a non-widget key that survives navigation."""
    st.session_state[_PERSIST_KEY] = (
        st.session_state["selected_profile"]
    )


def _llm_provider_for(base_url: str) -> str:
    """Infer the sidebar provider from a configured base URL."""
    normalized = base_url.rstrip("/")
    for provider, (preset_base, _models) in (
        _LLM_PROVIDER_PRESETS.items()
    ):
        if provider == "Custom":
            continue
        if normalized == preset_base.rstrip("/"):
            return provider
    return "Custom"


def _llm_model_options(provider: str) -> list[str]:
    """Return model choices for a provider plus a custom option."""
    _base_url, models = _LLM_PROVIDER_PRESETS.get(
        provider, _LLM_PROVIDER_PRESETS["Custom"]
    )
    return [*models, _LLM_CUSTOM_MODEL_CHOICE]


def _ensure_llm_session_defaults() -> None:
    """Seed sidebar LLM widgets from the current runtime config."""
    cfg = llm_client.current_config(mask_key=False)
    base_url = str(cfg.get("base_url") or "")
    model = str(cfg.get("model") or "")
    reply_lang = str(cfg.get("reply_lang") or "en")
    provider = _llm_provider_for(base_url)
    model_options = _llm_model_options(provider)

    st.session_state.setdefault(_LLM_PROVIDER_KEY, provider)
    st.session_state.setdefault(_LLM_LAST_PROVIDER_KEY, provider)
    st.session_state.setdefault(_LLM_BASE_URL_KEY, base_url)
    st.session_state.setdefault(_LLM_CUSTOM_MODEL_KEY, model)
    st.session_state.setdefault(
        _LLM_MODEL_CHOICE_KEY,
        model if model in model_options else _LLM_CUSTOM_MODEL_CHOICE,
    )
    st.session_state.setdefault(
        _LLM_REPLY_LANG_KEY,
        reply_lang if reply_lang in ("en", "zh") else "en",
    )


def _sync_llm_provider_preset() -> None:
    """When provider changes, load its default base URL and model."""
    provider = st.session_state.get(_LLM_PROVIDER_KEY, "Custom")
    previous = st.session_state.get(_LLM_LAST_PROVIDER_KEY)
    if provider == previous:
        return

    base_url, models = _LLM_PROVIDER_PRESETS.get(
        provider, _LLM_PROVIDER_PRESETS["Custom"]
    )
    if provider != "Custom":
        st.session_state[_LLM_BASE_URL_KEY] = base_url
        if models:
            st.session_state[_LLM_MODEL_CHOICE_KEY] = models[0]
            st.session_state[_LLM_CUSTOM_MODEL_KEY] = models[0]
    else:
        st.session_state[
            _LLM_MODEL_CHOICE_KEY
        ] = _LLM_CUSTOM_MODEL_CHOICE

    st.session_state[_LLM_LAST_PROVIDER_KEY] = provider


def _normalize_llm_model_choice(provider: str) -> None:
    """Keep the model selectbox value valid for the current provider."""
    options = _llm_model_options(provider)
    choice = st.session_state.get(_LLM_MODEL_CHOICE_KEY)
    if choice in options:
        return
    custom_model = st.session_state.get(_LLM_CUSTOM_MODEL_KEY, "")
    st.session_state[_LLM_MODEL_CHOICE_KEY] = (
        custom_model if custom_model in options else _LLM_CUSTOM_MODEL_CHOICE
    )


def _apply_llm_sidebar_config(
    *,
    base_url: str,
    model: str,
    api_key: str,
    reply_lang: str,
) -> None:
    """Apply sidebar values to the process-wide LLM client."""
    llm_client.configure(
        base_url=base_url,
        model=model,
        api_key=api_key or None,
        reply_lang=reply_lang,
    )


def render_llm_settings() -> None:
    """Render app-wide LLM settings in the Streamlit sidebar."""
    u = common_ui()
    _ensure_llm_session_defaults()

    with st.expander(u["llm_settings_title"]):
        provider_names = list(_LLM_PROVIDER_PRESETS)
        provider = st.selectbox(
            u["llm_provider"],
            provider_names,
            key=_LLM_PROVIDER_KEY,
        )
        _sync_llm_provider_preset()
        provider = st.session_state.get(_LLM_PROVIDER_KEY, provider)
        _normalize_llm_model_choice(provider)

        base_url = st.text_input(
            u["llm_base_url"],
            key=_LLM_BASE_URL_KEY,
        ).strip()

        model_options = _llm_model_options(provider)
        model_choice = st.selectbox(
            u["llm_model"],
            model_options,
            format_func=lambda value: (
                u["llm_custom_model_choice"]
                if value == _LLM_CUSTOM_MODEL_CHOICE
                else value
            ),
            key=_LLM_MODEL_CHOICE_KEY,
        )
        if model_choice == _LLM_CUSTOM_MODEL_CHOICE:
            model = st.text_input(
                u["llm_custom_model"],
                key=_LLM_CUSTOM_MODEL_KEY,
            ).strip()
        else:
            model = model_choice
            st.session_state[_LLM_CUSTOM_MODEL_KEY] = model_choice

        api_key = st.text_input(
            u["llm_api_key"],
            type="password",
            help=u["llm_api_key_help"],
            key=_LLM_API_KEY_KEY,
        ).strip()

        reply_lang = st.selectbox(
            u["llm_reply_lang"],
            ["zh", "en"],
            format_func=lambda value: (
                u["llm_reply_lang_zh"]
                if value == "zh"
                else u["llm_reply_lang_en"]
            ),
            key=_LLM_REPLY_LANG_KEY,
        )

        _apply_llm_sidebar_config(
            base_url=base_url,
            model=model,
            api_key=api_key,
            reply_lang=reply_lang,
        )

        if llm_client.is_configured():
            st.caption(
                u["llm_configured"].format(
                    label=llm_client.model_label()
                )
            )
        else:
            st.caption(u["llm_not_configured"])
        st.caption(u["llm_session_only"])


def ui_emoji_enabled() -> bool:
    """Return False when ``NBLANE_UI_EMOJI`` disables emoji prefixes."""
    raw = os.environ.get("NBLANE_UI_EMOJI", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


_SKILL_STATUS_EMOJI: dict[str, str] = {
    "expert": "🔵",
    "solid": "🟢",
    "learning": "🟡",
    "locked": "⬜",
}

_KANBAN_SECTION_EMOJI: dict[str, str] = {
    KANBAN_DOING: "🔄",
    KANBAN_DONE: "✅",
    KANBAN_QUEUE: "📋",
    KANBAN_SOMEDAY: "💡",
}


def skill_status_emoji(status: str) -> str:
    """Prefix char for skill status columns; empty when emoji disabled."""
    if not ui_emoji_enabled():
        return ""
    return _SKILL_STATUS_EMOJI.get(status, "⬜")


def kanban_section_emoji(section: str) -> str:
    """Prefix for kanban section headers; empty when emoji disabled."""
    if not ui_emoji_enabled():
        return ""
    return _KANBAN_SECTION_EMOJI.get(section, "")


def render_llm_unavailable(ui: dict[str, str]) -> None:
    """Standard Streamlit callout when the LLM client is not configured."""
    st.warning(ui["ai_not_configured"], icon="⚠️")
    st.caption(ui["ai_add_key_caption"])


def select_profile() -> str:
    """Render a sidebar profile selector and return the chosen name.

    Includes a "Create new profile" form. Uses a non-widget
    session-state key so the selection survives page navigation.
    """
    profiles = allowed_profiles()
    u = common_ui()

    with st.sidebar:
        st.markdown(u["profile_header"])

        if not profiles:
            st.info(u["no_profiles_yet"])
        else:
            scores = {
                name: _template_score(name)
                for name in profiles
            }
            min_score = min(scores.values())
            candidates = [
                name
                for name in profiles
                if scores[name] == min_score
            ]
            default_name = _latest_profile(candidates)
            default_idx = profiles.index(default_name)

            prev = st.session_state.get(_PERSIST_KEY)
            if prev is not None and prev in profiles:
                default_idx = profiles.index(prev)

            st.selectbox(
                u["select_profile_aria"],
                profiles,
                index=default_idx,
                key="selected_profile",
                on_change=_sync_to_persistent,
                label_visibility="collapsed",
            )

            st.session_state[_PERSIST_KEY] = (
                st.session_state["selected_profile"]
            )

        if can_create_profiles():
            with st.expander(u["expander_create"]):
                new_name = st.text_input(
                    u["profile_name_label"],
                    placeholder=u["profile_name_ph"],
                    key="_new_profile_name",
                )
                if st.button(
                    u["create"], key="_btn_create_profile"
                ):
                    name = new_name.strip()
                    all_profiles = list_profiles()
                    if not name:
                        st.warning(u["name_empty"])
                    elif name in all_profiles:
                        st.warning(
                            u["name_exists"].format(name=name)
                        )
                    else:
                        try:
                            init_profile(name)
                            st.session_state[
                                _PERSIST_KEY
                            ] = name
                            stash_git_backup_results()
                            st.success(
                                u["profile_created"].format(
                                    name=name
                                )
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

        render_llm_settings()

    if (
        not profiles
        and _PERSIST_KEY not in st.session_state
    ):
        st.warning(u["no_profiles_main"])
        st.stop()

    return st.session_state.get(
        _PERSIST_KEY,
        profiles[0] if profiles else "",
    )


def _file_state_key(path: Path) -> str:
    """Session key for one file snapshot."""
    return "nblane_file_snapshot:" + str(path.resolve())


def remember_file_snapshot(path: Path) -> FileSnapshot:
    """Capture and store the latest fingerprint for *path*."""
    snap = snapshot_file(path)
    st.session_state[_file_state_key(path)] = snap.to_dict()
    return snap


def ensure_file_snapshot(path: Path) -> FileSnapshot:
    """Store an initial fingerprint for *path* unless one already exists."""
    key = _file_state_key(path)
    raw = st.session_state.get(key)
    if isinstance(raw, dict):
        return FileSnapshot.from_dict(raw)
    return remember_file_snapshot(path)


def assert_file_snapshot_current(
    path: Path,
    *,
    label: str | None = None,
) -> None:
    """Stop the Streamlit run if *path* changed since it was loaded."""
    snap = ensure_file_snapshot(path)
    try:
        assert_unchanged(path, snap, label=label)
    except FileConflictError as exc:
        st.error(str(exc))
        st.stop()


def assert_files_current(paths: list[Path]) -> None:
    """Check multiple file snapshots before a multi-file write."""
    for path in paths:
        assert_file_snapshot_current(path, label=path.name)


def refresh_file_snapshots(paths: list[Path]) -> None:
    """Refresh stored fingerprints after a successful write."""
    for path in paths:
        remember_file_snapshot(path)


def stash_git_backup_results() -> None:
    """Persist Git backup warnings across Streamlit reruns."""
    notices = st.session_state.setdefault(
        _GIT_BACKUP_NOTICE_KEY,
        [],
    )
    for result in git_backup.consume_results():
        if result.has_warning:
            if result.error:
                notices.append(f"Git backup failed: {result.error}")
            if result.push_error:
                notices.append(
                    f"Git backup committed but push failed: "
                    f"{result.push_error}"
                )


def render_git_backup_notices() -> None:
    """Render and clear Git backup warnings for the current session."""
    notices = st.session_state.pop(_GIT_BACKUP_NOTICE_KEY, [])
    if not notices:
        return
    for msg in notices:
        st.warning(msg)


def drop_streamlit_widget_keys(keys: list[str]) -> None:
    """Delete session_state keys so widgets re-render with new values.

    Streamlit ``st.text_area`` with a ``key`` keeps its value in
    ``session_state``; when merged YAML changes, the old value
    persists unless the key is removed.
    """
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]


def remember_allow_and_drop_yaml_preview_keys(
    allow_current: bool,
    *,
    prev_state_key: str,
    pool_key: str,
    tree_key: str,
) -> None:
    """Clear legacy preview widget keys when allow-status checkbox changes.

    Merged previews used ``st.text_area`` with fixed keys; toggling
    ``allow_status_change`` without a new LLM call must drop those keys
    so the next render is not stale.
    """
    prev = st.session_state.get(prev_state_key)
    if prev is not None and prev != allow_current:
        drop_streamlit_widget_keys([pool_key, tree_key])
    st.session_state[prev_state_key] = allow_current
