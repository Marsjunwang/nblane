"""Profile Health -- read-only growth review."""

from __future__ import annotations

import streamlit as st

from nblane.core.profile_health import analyze_profile_health
from nblane.web_auth import require_login
from nblane.web_shared import render_git_backup_notices, select_profile


st.set_page_config(
    page_title="Profile Health",
    layout="wide",
)

require_login()
selected = select_profile()
render_git_backup_notices()
report = analyze_profile_health(selected)
counts = report.summary_counts

st.title("Profile Health")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Errors", counts["error"])
m2.metric("Warnings", counts["warning"])
m3.metric("Info", counts["info"])
m4.metric(
    "Context ready",
    "Yes" if report.can_publish_context else "No",
)

st.divider()

if not report.issues:
    st.success("No health issues found.")
    st.stop()

severity_icon = {
    "error": "ERROR",
    "warning": "WARN",
    "info": "INFO",
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
