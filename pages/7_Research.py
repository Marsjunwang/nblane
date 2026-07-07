"""Paper Reading Studio -- search, read, annotate, and cite papers."""

from __future__ import annotations

import streamlit as st

from nblane.core.io import profile_dir
from nblane.research_ui import (
    ResearchContext,
    _render_candidate_preview,
    _render_claims_citations,
    _render_connectors,
    _render_paper_library,
    _render_pdf_import_warnings,
    _render_reading_room,
    _render_research_help,
    _render_research_sidecar_status,
    _render_source_form,
    _render_source_queue,
    _render_synthesis_drafts,
    _render_workspace_overview,
)
from nblane.web_auth import require_login
from nblane.web_cache import load_research_sources
from nblane.web_i18n import research_ui
from nblane.web_shared import (
    apply_ui_language_from_session,
    ensure_file_snapshot,
    render_action_ai_settings,
    render_current_goal_strip,
    render_git_backup_notices,
    select_profile,
)

_RESEARCH_AI_ACTIONS = (
    "research.paper_search_codex",
    "research.paper_translate",
    "research.paper_explain_selection",
    "research.paper_source_guide",
    "research.paper_review_card",
    "research.paper_qa",
    "research.paper_claim_extract",
    "research.paper_deep_read_codex",
    "research.paper_compare_codex",
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


def _l(key: str, default: str) -> str:
    return ui.get(key, default)


ctx = ResearchContext(
    selected=selected,
    pdir=_pdir,
    ui=ui,
    user=user,
    sources_path=_sources_path,
    research_claims_path=_research_claims_path,
    research_citations_path=_research_citations_path,
    research_connectors_path=_research_connectors_path,
)


_head_l, _head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
with _head_l:
    st.title(ui["title"])
    st.caption(ui["page_context_line"])
    _render_research_sidecar_status(ctx)
    _render_pdf_import_warnings(ctx, _pdir)
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
            _render_research_help(ctx)
    with _ai_col:
        with st.popover(
            _l("ai_config_short", "AI"),
            key=f"research_ai_config_popover:{selected}",
            use_container_width=False,
        ):
            render_action_ai_settings(
                selected,
                _RESEARCH_AI_ACTIONS,
                ui=ui,
                key_prefix="research",
            )

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
    _render_workspace_overview(ctx, inbox)

with tab_library:
    _render_paper_library(ctx, inbox)

with tab_claims:
    _render_claims_citations(ctx, inbox)

with tab_export:
    _render_synthesis_drafts(ctx)

with tab_advanced:
    st.subheader(ui["source_inbox"])
    _render_source_queue(ctx, inbox)
    st.divider()
    with st.expander(ui["add_source"], expanded=not inbox.sources):
        _render_source_form(
            ctx,
            inbox,
            prefix=f"research_source_add_{selected}",
        )
    st.divider()
    _render_candidate_preview(ctx, inbox)
    st.divider()
    st.subheader(ui["reading_room"])
    _render_reading_room(ctx, inbox)
    st.divider()
    _render_connectors(ctx)
