"""Research Source Inbox -- capture and triage external sources."""

from __future__ import annotations

import streamlit as st
import yaml

from nblane.core.io import profile_dir
from nblane.core.research_sources import (
    SOURCE_KINDS,
    SOURCE_STATUSES,
    SOURCE_VISIBILITIES,
    add_research_source,
    load_research_sources,
    save_research_sources,
    update_research_source,
)
from nblane.web_auth import require_login
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
require_login()
selected = select_profile()
render_git_backup_notices()

_pdir = profile_dir(selected)
_sources_path = _pdir / "research" / "sources.yaml"
ensure_file_snapshot(_sources_path)


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


def _status_label(status: str) -> str:
    return ui.get(f"status_{status}", status)


def _save_sources(inbox, message: str) -> None:
    assert_files_current([_sources_path])
    save_research_sources(selected, inbox)
    refresh_file_snapshots([_sources_path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(message)


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


_head_l, _head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
with _head_l:
    st.title(ui["title"])
    st.caption(ui["page_context_line"])
with _head_goal:
    render_current_goal_strip(selected, compact=True, align="right")

inbox = load_research_sources(selected)

with st.expander(ui["add_source"], expanded=not inbox.sources):
    _render_source_form(
        inbox,
        prefix=f"research_source_add_{selected}",
    )

st.divider()
_render_source_queue(inbox)
st.divider()
_render_candidate_preview(inbox)
