"""Settings -- app-wide AI / LLM / Codex / language preferences.

These controls used to live in the sidebar on every page. They now have a
dedicated home so the sidebar stays focused on profile + navigation. The
runtime config is still applied on every page via ``ensure_llm_session`` in
``select_profile``; this page only renders the editing widgets.

Laid out as three flat, common-first sections: Connection (the
deployment-wide LLM connection, set once and shared by every profile),
Language (per-profile, applies live), and Advanced (the full per-action
backend/model matrix plus Codex, tucked away since most people never touch
it).
"""

from __future__ import annotations

import streamlit as st

from nblane.core.web_preferences import AI_ACTION_DEFAULT_BACKENDS
from nblane.web_auth import require_login
from nblane.web_i18n import common_ui
from nblane.web_shared import (
    apply_ui_language_from_session,
    render_action_ai_settings,
    render_codex_settings,
    render_connection_settings,
    render_git_backup_notices,
    render_language_settings,
    select_profile,
)

apply_ui_language_from_session()

ui = common_ui()
require_login()
selected = select_profile()
ui = common_ui()
render_git_backup_notices()

st.title(ui.get("sidebar_nav_settings", "Settings"))

st.markdown(f"### {ui.get('llm_connection_title', 'Connection')}")
render_connection_settings(selected)

st.divider()
st.markdown(f"### {ui.get('llm_language_title', 'Language')}")
render_language_settings(selected)

st.divider()
with st.expander(ui.get("llm_advanced_title", "Advanced"), expanded=False):
    render_action_ai_settings(
        selected,
        tuple(AI_ACTION_DEFAULT_BACKENDS),
        ui=ui,
        key_prefix="settings",
    )
    st.divider()
    render_codex_settings(selected)
