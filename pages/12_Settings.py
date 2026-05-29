"""Settings -- app-wide AI / LLM / Codex / language preferences.

These controls used to live in the sidebar on every page. They now have a
dedicated home so the sidebar stays focused on profile + navigation. The
runtime config is still applied on every page via ``ensure_llm_session`` in
``select_profile``; this page only renders the editing widgets.
"""

from __future__ import annotations

import streamlit as st

from nblane.web_auth import require_login
from nblane.web_i18n import common_ui
from nblane.web_shared import (
    apply_ui_language_from_session,
    render_codex_settings,
    render_git_backup_notices,
    render_llm_settings,
    select_profile,
)

apply_ui_language_from_session()

ui = common_ui()
require_login()
selected = select_profile()
ui = common_ui()
render_git_backup_notices()

st.title(ui.get("sidebar_nav_settings", "Settings"))
st.caption(ui.get("llm_session_only", ""))

render_llm_settings(selected, expanded=True)
render_codex_settings(selected)
