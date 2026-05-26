"""Source inbox form, queue, and candidate preview UI."""
from __future__ import annotations

import yaml

import streamlit as st

from nblane.core.research_papers import ensure_paper_reading_artifacts
from nblane.core.research_sources import (
    SOURCE_KINDS,
    SOURCE_STATUSES,
    SOURCE_VISIBILITIES,
    add_research_source,
    save_research_sources,
    update_research_source,
)
from nblane.web_cache import clear_web_cache, load_research_sources
from nblane.web_shared import (
    assert_files_current,
    refresh_file_snapshots,
    stash_git_backup_results,
)

from .context import ResearchContext
from ._helpers import (
    _l, _lines_text, _tags, _tags_text, _text_lines, _status_label,
)


def _save_sources(ctx, inbox, message: str) -> None:
    selected = ctx.selected
    _sources_path = ctx.sources_path
    assert_files_current([_sources_path])
    save_research_sources(selected, inbox)
    refresh_file_snapshots([_sources_path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(message)


def _accept_latest_sources_for_additive_write(ctx) -> None:
    """Let additive imports proceed after passive Reader progress writes."""
    _sources_path = ctx.sources_path
    refresh_file_snapshots([_sources_path])


def _prepare_reader_artifacts_for_sources(ctx, source_ids: list[str]) -> dict[str, object]:
    selected = ctx.selected
    _pdir = ctx.pdir
    _sources_path = ctx.sources_path
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


def _render_source_form(ctx, inbox, *, source=None, prefix: str) -> None:
    ui = ctx.ui
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
            _l(ui, "library_node_refs", "Library node refs"),
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
            _save_sources(ctx, inbox, ui["created"].format(id=item.id))
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
            _save_sources(ctx, inbox, ui["saved"])
    except ValueError as exc:
        st.error(str(exc))
        return
    st.rerun()


def _render_source_queue(ctx, inbox) -> None:
    selected = ctx.selected
    ui = ctx.ui
    st.subheader(ui["source_queue"])
    for status in SOURCE_STATUSES:
        sources = [source for source in inbox.sources if source.status == status]
        with st.expander(
            f"{_status_label(ctx, status)} · {len(sources)}",
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
                    _render_source_form(ctx, 
                        inbox,
                        source=source,
                        prefix=f"research_source_edit_{selected}_{source.id}",
                    )


def _render_candidate_preview(ctx, inbox) -> None:
    ui = ctx.ui
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


