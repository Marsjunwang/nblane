"""Shared sidebar profile selector for Streamlit pages."""

from __future__ import annotations

import os
import re
from pathlib import Path

import streamlit as st

from nblane.core.io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
    init_profile,
    list_profiles,
    profile_dir,
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


def _sync_to_persistent() -> None:
    """Copy widget value to a non-widget key that survives navigation."""
    st.session_state[_PERSIST_KEY] = (
        st.session_state["selected_profile"]
    )


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
    profiles = list_profiles()
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
                if not name:
                    st.warning(u["name_empty"])
                elif name in profiles:
                    st.warning(
                        u["name_exists"].format(name=name)
                    )
                else:
                    try:
                        init_profile(name)
                        st.session_state[
                            _PERSIST_KEY
                        ] = name
                        st.success(
                            u["profile_created"].format(
                                name=name
                            )
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

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
