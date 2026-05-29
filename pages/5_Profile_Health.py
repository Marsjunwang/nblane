"""Profile Health -- read-only growth review."""

from __future__ import annotations

import streamlit as st

from nblane.core.profile_health import analyze_profile_health
from nblane.web_auth import require_login
from nblane.web_i18n import profile_health_ui
from nblane.web_shared import (
    apply_ui_language_from_session,
    render_current_goal_strip,
    render_git_backup_notices,
    render_page_help,
    select_profile,
)

apply_ui_language_from_session()


ui = profile_health_ui()

require_login()
selected = select_profile()
ui = profile_health_ui()
render_git_backup_notices()

report = analyze_profile_health(selected)
counts = report.summary_counts

_head_l, _head_goal = st.columns(
    [5, 2],
    gap="medium",
    vertical_alignment="top",
)
with _head_l:
    st.title(ui["title"])
    st.caption(ui["page_context_line"])
with _head_goal:
    render_current_goal_strip(selected, compact=True, align="right")
render_page_help(
    ui,
    key=f"profile_health_help:{selected}",
    docs_path="docs/zh/guides/profile-health.md",
)

st.info(ui["review_link_help"])
st.page_link("pages/8_Review.py", label=ui["review_link"])

m1, m2, m3, m4 = st.columns(4)
m1.metric(ui["errors"], counts["error"])
m2.metric(ui["warnings"], counts["warning"])
m3.metric(ui["info"], counts["info"])
m4.metric(
    ui["context_ready"],
    ui["yes"] if report.can_publish_context else ui["no"],
)

st.divider()

if not report.issues:
    st.success(ui["no_issues"])
    st.stop()

severity_icon = {
    "error": ui["severity_error"],
    "warning": ui["severity_warning"],
    "info": ui["severity_info"],
}

for issue in report.issues:
    with st.container(border=True):
        c1, c2 = st.columns([1, 5])
        with c1:
            st.markdown(f"**{severity_icon.get(issue.severity, 'INFO')}**")
            st.caption(issue.category)
        with c2:
            st.markdown(f"**{issue.title}**")
            if issue.detail:
                st.caption(issue.detail)
            if issue.action:
                st.info(issue.action)
