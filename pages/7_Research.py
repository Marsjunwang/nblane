"""Paper Reading Studio -- search, read, annotate, and cite papers."""

from __future__ import annotations

from datetime import datetime

import streamlit as st
import yaml

from nblane.core.ai import (
    answer_paper_question,
    extract_paper_claims,
    generate_paper_source_guide,
    search_papers_codex,
    translate_paper_segments,
)
from nblane.core.io import profile_dir
from nblane.core.research_papers import (
    PAPER_SEARCH_PROVIDERS,
    PaperSearchResult,
    auto_chunk_paper,
    create_chunk_from_annotation,
    create_paper_annotation,
    create_reading_note_markdown,
    extract_paper_pages,
    extract_paper_segments,
    format_research_citations,
    import_paper_pdf,
    import_paper_search_results,
    import_paper_url,
    load_paper_analysis,
    load_paper_annotations,
    load_paper_library_tree,
    load_paper_pages,
    load_paper_segments,
    load_paper_translations,
    mark_imported_paper_results,
    move_papers_to_node,
    paper_library_paths,
    paper_overview,
    paper_rows,
    save_paper_analysis,
    save_paper_note,
    save_research_export,
    search_papers,
    translation_rows_for_segments,
    upsert_paper_library_node,
    upsert_paper_translations,
    validate_paper_library,
)
from nblane.core.research_sources import (
    SOURCE_KINDS,
    SOURCE_STATUSES,
    SOURCE_VISIBILITIES,
    ResearchReading,
    add_research_source,
    apply_research_evidence_candidate,
    generate_reading_draft,
    load_research_sources,
    research_evidence_patch,
    save_research_sources,
    update_research_source,
)
from nblane.core.research_connectors import (
    CONNECTOR_PROVIDERS,
    load_connectors,
    sync_connector,
    upsert_connector,
)
from nblane.core.research_workspace import (
    RESEARCH_CHUNK_KINDS,
    create_chunk,
    create_citation,
    draft_synthesis_from_claims,
    load_chunks,
    load_research_citations,
    load_research_claims,
    load_research_drafts,
    research_claim_to_evidence_candidate,
    research_draft_to_blog_candidate,
    upsert_research_claim,
)
from nblane.core.public_site import create_blog_draft
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
ui = research_ui()
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


def _l(key: str, default: str) -> str:
    return ui.get(key, default)


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
        library_node_refs = st.text_area(
            _l("library_node_refs", "Library node refs"),
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
                library_node_refs=_text_lines(library_node_refs),
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


def _render_workspace_overview(inbox) -> None:
    overview = paper_overview(_pdir)
    connector_rows = list(load_connectors(_pdir).get("connectors") or [])
    enabled_connectors = [row for row in connector_rows if bool(row.get("enabled", True))]

    st.subheader(_l("paper_reading_pipeline", "Reading Pipeline"))
    p1, p2, p3, p4, p5, p6 = st.columns(6)
    p1.metric(_l("papers_total", "Papers total"), overview["papers_total"])
    p2.metric(_l("papers_reading", "Reading"), overview["reading"])
    p3.metric(_l("papers_annotated", "Annotated"), overview["annotated"])
    p4.metric(_l("papers_candidate_ready", "Candidate ready"), overview["candidate_ready"])
    p5.metric(_l("papers_archived", "Archived"), overview["archived"])
    p6.metric(ui["connectors_enabled"], len(enabled_connectors))

    st.subheader(_l("review_queue", "Review Queue"))
    r1, r2, r3 = st.columns(3)
    r1.metric(_l("ready_research_claims", "Ready research claims"), overview["ready_research_claims"])
    r2.metric(_l("promoted_research_claims", "Promoted research claims"), overview["promoted_research_claims"])
    r3.metric(_l("ai_candidates", "AI candidates"), overview["ai_candidates"])

    st.subheader(_l("integrity_publish_safety", "Integrity & Publish Safety"))
    s1, s2, s3, s4 = st.columns(4)
    s1.metric(_l("private_public_sources", "Private / public"), f"{overview['private_sources']} / {overview['public_sources']}")
    s2.metric(_l("citation_broken", "Citation broken"), overview["citation_broken"])
    s3.metric(_l("private_publish_risk", "Private publish risk"), overview["private_publish_risk"])
    s4.metric(_l("stale_translation_warning", "Stale translations"), overview["stale_translation_warning"])

    st.caption(
        _l(
            "paper_evidence_boundary",
            "Paper-reading evidence proves reading, quoting, and understanding; project or goal claims still need real project evidence before public use.",
        )
    )
    st.caption(ui["claim_boundary_hint"])

    recent = overview.get("recent_papers") or []
    if recent:
        st.markdown(f"**{_l('recent_papers', 'Recent papers')}**")
        st.dataframe(
            [
                {
                    "title": row.get("title"),
                    "status": row.get("status"),
                    "tree_path": row.get("tree_path"),
                    "last_read": row.get("last_read"),
                }
                for row in recent
            ],
            use_container_width=True,
            hide_index=True,
        )

    diagnostics = []
    diagnostics.extend(overview.get("citation_diagnostics") or [])
    diagnostics.extend(overview.get("private_publish_risk_refs") or [])
    if diagnostics:
        with st.expander(_l("integrity_details", "Integrity details")):
            for item in diagnostics:
                st.warning(str(item))

    st.markdown(f"**{ui['research_primary_actions']}**")
    a1, a2, a3, a4, a5 = st.columns(5)
    with a1:
        st.page_link("pages/7_Research.py", label=_l("search_papers", "Search papers"))
    with a2:
        st.page_link("pages/7_Research.py", label=_l("open_library", "Open Library"))
    with a3:
        st.page_link("pages/7_Research.py", label=_l("continue_reading", "Continue reading"))
    with a4:
        st.page_link("pages/7_Research.py", label=_l("review_claims", "Review claims"))
    with a5:
        st.page_link("pages/7_Research.py", label=_l("export_citations", "Export citations"))


def _paper_sources(inbox) -> list:
    return [source for source in inbox.sources if source.kind == "paper"]


def _source_label(inbox, source_id: str) -> str:
    return next(
        (source.title or source.id for source in inbox.sources if source.id == source_id),
        source_id,
    )


def _node_options() -> dict[str, str]:
    paths = paper_library_paths(_pdir)
    return {"": _l("unsorted_inbox", "Unsorted Inbox"), **paths}


def _result_rows(results: list[dict]) -> list[dict[str, object]]:
    marked = mark_imported_paper_results(_pdir, results)
    return [
        {
            "select_id": row.candidate_id,
            "title": row.title,
            "year": row.year,
            "venue": row.venue,
            "authors": ", ".join(row.authors[:3]),
            "provider": ", ".join(row.provider_refs),
            "citations": row.citation_count if row.citation_count is not None else "",
            "oa_pdf": bool(row.open_access_pdf),
            "link": (row.link_check or {}).get("status", "needs check"),
            "imported": row.imported_source_id,
            "relevance": row.why_relevant,
            "tags": ", ".join(row.tags),
        }
        for row in marked
    ]


def _search_state_key(name: str) -> str:
    return f"paper_search:{selected}:{name}"


def _render_paper_search(inbox) -> None:
    st.subheader(_l("paper_search", "Paper Search"))
    st.caption(
        _l(
            "paper_search_caption",
            "Search and import candidates. Results stay preview-only until you confirm import.",
        )
    )
    mode = st.radio(
        _l("search_mode", "Search mode"),
        [
            "Codex Search",
            "Provider Search",
            "Manual URL",
            "Upload PDF",
        ],
        horizontal=True,
        key=f"paper_search_mode:{selected}",
    )

    if mode in {"Codex Search", "Provider Search"}:
        with st.form(f"paper_search_form:{selected}"):
            query = st.text_input(_l("query", "Query"), placeholder="VLA memory")
            providers = st.multiselect(
                _l("providers", "Providers"),
                options=list(PAPER_SEARCH_PROVIDERS),
                default=list(PAPER_SEARCH_PROVIDERS),
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                limit = st.number_input(_l("limit", "Limit"), min_value=1, max_value=50, value=10)
            with c2:
                year_from = st.text_input(_l("year_from", "Year from"))
            with c3:
                year_to = st.text_input(_l("year_to", "Year to"))
            only_pdf = st.checkbox(_l("has_open_access_pdf", "Has open-access PDF"), value=False)
            exclude_imported = st.checkbox(_l("exclude_imported", "Exclude already imported"), value=True)
            project_refs = st.text_area(ui["project_refs"], height=68)
            goal_refs = st.text_area(ui["goal_refs"], height=68)
            submitted = st.form_submit_button(_l("search_papers", "Search papers"), type="primary")
        if submitted:
            filters = {
                "providers": providers,
                "limit": limit,
                "year_from": year_from,
                "year_to": year_to,
                "has_open_access_pdf": only_pdf,
            }
            if mode == "Codex Search":
                result = search_papers_codex(
                    selected,
                    query,
                    payload={"filters": filters, "project_refs": _text_lines(project_refs), "goal_refs": _text_lines(goal_refs)},
                )
                raw = result.structured if isinstance(result.structured, dict) else {}
                candidates = [
                    item.to_dict()
                    for item in (
                        PaperSearchResult.from_dict(row)
                        for row in raw.get("results", [])
                    )
                    if item is not None
                ]
                if not candidates:
                    st.warning(
                        _l(
                            "codex_search_fallback",
                            "Codex returned no structured papers; using provider search fallback.",
                        )
                    )
                    candidates = [row.to_dict() for row in search_papers(query, tuple(providers), int(limit), filters)]
                for warning in result.warnings:
                    st.warning(str(warning))
            else:
                candidates = [row.to_dict() for row in search_papers(query, tuple(providers), int(limit), filters)]
            if exclude_imported:
                candidates = [
                    row.to_dict()
                    for row in mark_imported_paper_results(_pdir, candidates)
                    if not row.imported_source_id
                ]
            st.session_state[_search_state_key("results")] = candidates
            st.rerun()

        results = list(st.session_state.get(_search_state_key("results"), []) or [])
        if results:
            st.dataframe(_result_rows(results), use_container_width=True, hide_index=True)
            selected_ids = st.multiselect(
                _l("select_to_import", "Select to import"),
                options=[str(row.get("candidate_id")) for row in results],
                format_func=lambda cid: next(
                    (str(row.get("title") or cid) for row in results if str(row.get("candidate_id")) == cid),
                    cid,
                ),
            )
            with st.expander(_l("selected_yaml_preview", "Selected YAML preview"), expanded=bool(selected_ids)):
                st.code(
                    yaml.dump(
                        [row for row in results if str(row.get("candidate_id")) in set(selected_ids)],
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            with st.form(f"paper_import_options:{selected}"):
                node_options = _node_options()
                node_ref = st.selectbox(
                    _l("library_location", "Library location"),
                    options=list(node_options),
                    format_func=lambda ref: node_options.get(ref, ref),
                )
                tags = st.text_input(ui["tags"])
                visibility = st.selectbox(ui["visibility"], ["private", "public"])
                status = st.selectbox(ui["status"], SOURCE_STATUSES, index=SOURCE_STATUSES.index("inbox"))
                download_pdf = st.checkbox(_l("download_open_access_pdf", "Download open-access PDF"), value=False)
                confirmed = st.form_submit_button(_l("import_selected", "Import selected"), type="primary")
            if confirmed:
                try:
                    assert_files_current([_sources_path])
                    imported = import_paper_search_results(
                        _pdir,
                        results,
                        selected_ids,
                        {
                            "library_node_refs": [node_ref] if node_ref else [],
                            "tags": _tags(tags),
                            "visibility": visibility,
                            "status": status,
                            "goal_refs": _text_lines(goal_refs),
                            "project_refs": _text_lines(project_refs),
                            "download_pdf": download_pdf,
                        },
                    )
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(_l("imported_papers", "Imported papers: {ids}").format(ids=", ".join(imported) or "0"))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.caption(_l("search_results_empty", "No paper candidates yet."))

    elif mode == "Manual URL":
        with st.form(f"paper_manual_url:{selected}"):
            url = st.text_input(_l("url_or_doi", "URL / DOI / arXiv / PDF URL"))
            title_hint = st.text_input(_l("title_hint", "Title hint"))
            node_options = _node_options()
            node_ref = st.selectbox(
                _l("library_location", "Library location"),
                options=list(node_options),
                format_func=lambda ref: node_options.get(ref, ref),
            )
            tags = st.text_input(ui["tags"])
            visibility = st.selectbox(ui["visibility"], ["private", "public"])
            status = st.selectbox(ui["status"], SOURCE_STATUSES, index=SOURCE_STATUSES.index("inbox"))
            submitted = st.form_submit_button(_l("import_url", "Import URL"), type="primary")
        if submitted:
            try:
                assert_files_current([_sources_path])
                source_id = import_paper_url(
                    _pdir,
                    url,
                    {
                        "title": title_hint,
                        "library_node_refs": [node_ref] if node_ref else [],
                        "tags": _tags(tags),
                        "visibility": visibility,
                        "status": status,
                    },
                )
                refresh_file_snapshots([_sources_path])
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=source_id))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    else:
        st.caption(_l("upload_pdf_caption", "Upload a local PDF and bind it to a private paper source."))
        with st.form(f"paper_upload:{selected}"):
            title = st.text_input(ui["title_label"])
            uploaded = st.file_uploader("PDF", type=["pdf"])
            node_options = _node_options()
            node_ref = st.selectbox(
                _l("library_location", "Library location"),
                options=list(node_options),
                format_func=lambda ref: node_options.get(ref, ref),
            )
            tags = st.text_input(ui["tags"])
            visibility = st.selectbox(ui["visibility"], ["private", "public"])
            submitted = st.form_submit_button(_l("upload_pdf", "Upload PDF"), type="primary")
        if submitted:
            try:
                if uploaded is None:
                    raise ValueError("Select a PDF first.")
                assert_files_current([_sources_path])
                inbox = load_research_sources(selected)
                source = add_research_source(
                    inbox,
                    title or uploaded.name,
                    kind="paper",
                    status="reading",
                    tags=_tags(tags),
                    visibility=visibility,
                    origin="manual",
                    library_node_refs=[node_ref] if node_ref else [],
                )
                save_research_sources(selected, inbox)
                import_paper_pdf(_pdir, source.id, uploaded.getvalue(), uploaded.name)
                refresh_file_snapshots([_sources_path])
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=source.id))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _render_paper_library(inbox) -> None:
    st.subheader(_l("paper_library", "Paper Library"))
    st.caption(
        _l(
            "paper_library_caption",
            "Tree nodes describe where papers belong; status, tags, PDF assets, and reading artifacts are paper properties.",
        )
    )
    with st.expander(_l("library_tree", "Library Tree"), expanded=False):
        tree = load_paper_library_tree(_pdir)
        if tree.nodes:
            st.dataframe(
                [
                    {
                        "id": node.id,
                        "title": node.title,
                        "parent_id": node.parent_id,
                        "description": node.description,
                        "status": node.status,
                    }
                    for node in tree.nodes
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption(_l("tree_empty", "No library nodes yet."))
        with st.form(f"paper_library_node:{selected}"):
            node_options = _node_options()
            title = st.text_input(_l("node_title", "Node title"))
            node_id = st.text_input(_l("node_id", "Node id"))
            parent_id = st.selectbox(
                _l("parent_node", "Parent node"),
                options=list(node_options),
                format_func=lambda ref: node_options.get(ref, ref),
            )
            description = st.text_area(ui["notes"], height=80)
            submitted = st.form_submit_button(_l("save_node", "Save node"), type="primary")
        if submitted:
            try:
                upsert_paper_library_node(
                    _pdir,
                    title,
                    node_id=node_id,
                    parent_id=parent_id,
                    description=description,
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        diagnostics = validate_paper_library(_pdir)
        for item in diagnostics:
            st.warning(str(item))

    c1, c2 = st.columns([1, 2])
    with c1:
        view = st.selectbox(
            _l("smart_view", "Smart View"),
            [
                "all",
                "unsorted",
                "reading",
                "annotated",
                "candidate_ready",
                "archived",
                "discarded",
                "other",
            ],
            format_func=lambda item: {
                "all": "All Papers",
                "unsorted": "Unsorted Inbox",
                "reading": "Reading",
                "annotated": "Annotated",
                "candidate_ready": "Candidate Ready",
                "archived": "Archived",
                "discarded": "Discarded",
                "other": "Other Sources",
            }.get(item, item),
        )
    with c2:
        node_options = _node_options()
        node_filter = st.selectbox(
            _l("tree_filter", "Tree filter"),
            options=list(node_options),
            format_func=lambda ref: node_options.get(ref, ref),
        )
    rows = paper_rows(_pdir, view=view, node_id=node_filter)
    display_rows = [
        {
            key: value
            for key, value in row.items()
            if key not in {"source"}
        }
        for row in rows
    ]
    if display_rows:
        st.dataframe(display_rows, use_container_width=True, hide_index=True)
    else:
        st.caption(_l("library_empty", "No papers match this view."))

    paper_ids = [str(row.get("id")) for row in rows]
    selected_rows = st.multiselect(
        _l("select_papers", "Select papers"),
        options=paper_ids,
        format_func=lambda sid: _source_label(inbox, sid),
    )
    with st.expander(_l("bulk_actions", "Bulk actions"), expanded=bool(selected_rows)):
        b1, b2, b3 = st.columns(3)
        with b1:
            bulk_node = st.selectbox(
                _l("move_to_node", "Move to node"),
                options=list(node_options),
                format_func=lambda ref: node_options.get(ref, ref),
                key=f"bulk_node:{selected}",
            )
            if st.button(_l("move_to_node", "Move to node"), disabled=not selected_rows):
                try:
                    assert_files_current([_sources_path])
                    move_papers_to_node(_pdir, selected_rows, bulk_node)
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with b2:
            bulk_status = st.selectbox(
                _l("set_status", "Set status"),
                SOURCE_STATUSES,
                key=f"bulk_status:{selected}",
            )
            if st.button(_l("set_status", "Set status"), disabled=not selected_rows):
                try:
                    assert_files_current([_sources_path])
                    current = load_research_sources(selected)
                    for source_id in selected_rows:
                        update_research_source(current, source_id, status=bulk_status)
                    _save_sources(current, ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with b3:
            tag_text = st.text_input(_l("add_tags", "Add tags"), key=f"bulk_tags:{selected}")
            if st.button(_l("add_tags", "Add tags"), disabled=not selected_rows):
                try:
                    assert_files_current([_sources_path])
                    current = load_research_sources(selected)
                    by_id = current.by_id()
                    for source_id in selected_rows:
                        source = by_id.get(source_id)
                        if source is not None:
                            update_research_source(current, source_id, tags=[*source.tags, *_tags(tag_text)])
                    _save_sources(current, ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    if paper_ids:
        detail_id = st.selectbox(
            _l("detail_paper", "Detail paper"),
            options=paper_ids,
            format_func=lambda sid: _source_label(inbox, sid),
            key=f"paper_library_detail:{selected}",
        )
        source = inbox.by_id().get(detail_id)
        if source is not None:
            with st.expander(_l("detail_drawer", "Detail drawer"), expanded=True):
                left, right = st.columns(2)
                with left:
                    st.markdown(f"**{source.title}**")
                    st.caption(source.id)
                    st.code(
                        yaml.dump(
                            {
                                "metadata": source.metadata,
                                "library_node_refs": source.library_node_refs,
                                "tags": source.tags,
                                "project_refs": source.project_refs,
                                "goal_refs": source.goal_refs,
                            },
                            allow_unicode=True,
                            default_flow_style=False,
                            sort_keys=False,
                        ),
                        language="yaml",
                    )
                with right:
                    annotations = load_paper_annotations(_pdir, source.id)
                    translations = load_paper_translations(_pdir, source.id)
                    st.metric(_l("annotations", "Annotations"), len(annotations))
                    st.metric(_l("translations", "Translations"), len(translations))
                    if st.button(ui["archive"], key=f"archive:{source.id}"):
                        try:
                            assert_files_current([_sources_path])
                            current = load_research_sources(selected)
                            update_research_source(current, source.id, status="archived")
                            _save_sources(current, ui["saved"])
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                    if st.button(ui["discard"], key=f"discard:{source.id}"):
                        try:
                            assert_files_current([_sources_path])
                            current = load_research_sources(selected)
                            update_research_source(current, source.id, status="discarded")
                            _save_sources(current, ui["saved"])
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))


def _segment_dicts(source_id: str, limit: int = 20) -> list[dict[str, object]]:
    return [segment.to_dict() for segment in load_paper_segments(_pdir, source_id)[:limit]]


def _render_paper_reader(inbox) -> None:
    st.subheader(_l("reader", "Reader"))
    papers = _paper_sources(inbox)
    if not papers:
        st.caption(_l("no_papers", "No paper sources yet."))
        return
    source_id = st.selectbox(
        ui["source_id"],
        options=[source.id for source in papers],
        format_func=lambda sid: _source_label(inbox, sid),
        key=f"paper_reader_source:{selected}",
    )
    source = inbox.by_id().get(source_id)
    if source is None:
        return
    st.markdown(f"**{source.title}**")
    st.caption(
        _l(
            "reader_fallback_caption",
            "Text-mode Reader fallback: PDF.js can replace this surface later, but annotations, chunks, translations, and citations already persist.",
        )
    )
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PDF", "yes" if source.metadata.get("pdf_asset_ref") else "missing")
    m2.metric(_l("pages", "Pages"), source.metadata.get("page_count", ""))
    m3.metric(_l("annotations", "Annotations"), len(load_paper_annotations(_pdir, source_id)))
    m4.metric(_l("segments", "Segments"), len(load_paper_segments(_pdir, source_id)))

    actions = st.columns(4)
    with actions[0]:
        if st.button(_l("extract_pages", "Extract pages"), disabled=not source.metadata.get("pdf_asset_ref")):
            try:
                extract_paper_pages(_pdir, source_id)
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with actions[1]:
        if st.button(_l("extract_segments", "Extract segments")):
            try:
                extract_paper_segments(_pdir, source_id)
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with actions[2]:
        if st.button(_l("auto_chunk", "Auto chunk")):
            try:
                chunks = auto_chunk_paper(_pdir, source_id)
                stash_git_backup_results()
                clear_web_cache()
                st.success(_l("created_chunks", "Created chunks: {count}").format(count=len(chunks)))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with actions[3]:
        if st.button(_l("save_last_read", "Save last read")):
            try:
                current = load_research_sources(selected)
                src = current.by_id().get(source_id)
                if src is None:
                    raise ValueError(source_id)
                metadata = dict(src.metadata)
                metadata["last_read_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
                update_research_source(current, source_id, metadata=metadata, status="reading")
                _save_sources(current, ui["saved"])
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    pages, segments, annotations, translations_tab, ai_tab, claims_tab = st.tabs(
        [
            _l("pages", "Pages"),
            _l("segments", "Segments"),
            _l("annotations", "Annotations"),
            _l("translation", "Translation"),
            "AI",
            ui["claims_citations"],
        ]
    )
    with pages:
        rows = load_paper_pages(_pdir, source_id)
        if rows:
            for page in rows[:20]:
                with st.expander(f"p. {page.page} · {page.char_count} chars"):
                    st.text(page.text or _l("page_text_empty", "No extracted text for this page."))
        else:
            st.caption(_l("pages_empty", "No extracted pages yet."))
    with segments:
        segment_rows = load_paper_segments(_pdir, source_id)
        if segment_rows:
            st.dataframe(
                [
                    {
                        "segment_id": segment.segment_id,
                        "page": segment.page,
                        "locator": segment.locator,
                        "text": segment.text[:260],
                        "text_hash": segment.text_hash,
                    }
                    for segment in segment_rows
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption(_l("segments_empty", "No paper segments yet."))
    with annotations:
        segment_ids = [segment.segment_id for segment in load_paper_segments(_pdir, source_id)]
        with st.form(f"paper_annotation:{selected}:{source_id}"):
            page = st.number_input(_l("page", "Page"), min_value=0, value=0)
            selected_text = st.text_area(_l("selected_text", "Selected text"), height=110)
            note = st.text_area(ui["notes"], height=80)
            picked_segments = st.multiselect(_l("segment_refs", "Segment refs"), segment_ids)
            tags = st.text_input(ui["tags"])
            submitted = st.form_submit_button(_l("create_annotation", "Create annotation"), type="primary")
        if submitted:
            try:
                ann = create_paper_annotation(
                    _pdir,
                    source_id,
                    selected_text,
                    page=int(page),
                    note=note,
                    tags=_tags(tags),
                    segment_refs=picked_segments,
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=ann.id))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        anns = load_paper_annotations(_pdir, source_id)
        if anns:
            st.dataframe([ann.to_dict() for ann in anns], use_container_width=True, hide_index=True)
            ann_id = st.selectbox(
                _l("annotation_to_chunk", "Annotation to chunk"),
                options=[ann.id for ann in anns],
            )
            if st.button(_l("create_chunk_from_annotation", "Create chunk from annotation")):
                try:
                    chunk = create_chunk_from_annotation(_pdir, ann_id)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["created"].format(id=chunk.id))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.caption(_l("annotations_empty", "No annotations yet."))
    with translations_tab:
        segment_rows = load_paper_segments(_pdir, source_id)
        segment_ids = [segment.segment_id for segment in segment_rows]
        picked = st.multiselect(_l("translate_segments", "Translate segments"), segment_ids[:100])
        if st.button(_l("generate_translation_candidate", "Generate translation candidate"), disabled=not picked):
            result = translate_paper_segments(
                selected,
                source_id,
                [segment.to_dict() for segment in segment_rows if segment.segment_id in set(picked)],
            )
            st.session_state[f"paper_translation_candidate:{selected}:{source_id}"] = result.structured or {}
            for warning in result.warnings:
                st.warning(str(warning))
        candidate = st.session_state.get(f"paper_translation_candidate:{selected}:{source_id}", {})
        if isinstance(candidate, dict) and candidate.get("translations"):
            st.code(yaml.dump(candidate, allow_unicode=True, sort_keys=False), language="yaml")
            if st.button(_l("accept_translation_candidate", "Accept translation candidate")):
                try:
                    upsert_paper_translations(_pdir, source_id, list(candidate.get("translations") or []))
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        translations = load_paper_translations(_pdir, source_id)
        if translations:
            st.dataframe([row.to_dict() for row in translations], use_container_width=True, hide_index=True)
        else:
            st.caption(_l("translations_empty", "No translations yet."))
    with ai_tab:
        segment_payload = _segment_dicts(source_id, limit=30)
        if st.button(_l("run_source_guide", "Run Source Guide")):
            result = generate_paper_source_guide(
                selected,
                source_id,
                source=source.to_dict(),
                segments=segment_payload,
            )
            st.session_state[f"paper_guide:{selected}:{source_id}"] = result.structured or {}
            for warning in result.warnings:
                st.warning(str(warning))
        guide = st.session_state.get(f"paper_guide:{selected}:{source_id}", {})
        if guide:
            st.code(yaml.dump(guide, allow_unicode=True, sort_keys=False), language="yaml")
            if st.button(_l("accept_as_analysis", "Accept as analysis")):
                try:
                    save_paper_analysis(_pdir, source_id, guide)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                except Exception as exc:
                    st.error(str(exc))
        question = st.text_input(_l("ask_paper", "Ask paper"))
        if st.button(_l("ask_paper", "Ask paper"), disabled=not question):
            result = answer_paper_question(
                selected,
                source_id,
                question,
                payload={"segments": segment_payload},
            )
            st.code(yaml.dump(result.structured or {}, allow_unicode=True, sort_keys=False), language="yaml")
            for warning in result.warnings:
                st.warning(str(warning))
        if st.button(_l("extract_claim_candidates", "Extract claim candidates")):
            result = extract_paper_claims(selected, source_id, segments=segment_payload)
            st.code(yaml.dump(result.structured or {}, allow_unicode=True, sort_keys=False), language="yaml")
            for warning in result.warnings:
                st.warning(str(warning))
        analysis = load_paper_analysis(_pdir, source_id)
        if analysis:
            with st.expander(_l("saved_analysis", "Saved analysis")):
                st.code(yaml.dump(analysis, allow_unicode=True, sort_keys=False), language="yaml")
    with claims_tab:
        st.caption(_l("reader_claims_hint", "Use the Claims & Citations tab for durable claim/citation editing."))
        source_chunks = load_chunks(_pdir, source_id)
        st.dataframe(
            [
                {"id": chunk.id, "locator": chunk.locator, "text": chunk.text[:220]}
                for chunk in source_chunks
            ],
            use_container_width=True,
            hide_index=True,
        )


def _reading_key(name: str) -> str:
    return f"research_reading:{selected}:{name}"


def _reading_from_form(source) -> ResearchReading:
    claims_raw = st.session_state.get(_reading_key("claim_candidates"), "")
    citations_raw = st.session_state.get(_reading_key("citations"), "")
    try:
        claim_candidates = yaml.safe_load(str(claims_raw or "")) or []
    except yaml.YAMLError:
        claim_candidates = []
    try:
        citations = yaml.safe_load(str(citations_raw or "")) or []
    except yaml.YAMLError:
        citations = []
    if not isinstance(claim_candidates, list):
        claim_candidates = []
    if not isinstance(citations, list):
        citations = []
    return ResearchReading(
        excerpt=str(st.session_state.get(_reading_key("excerpt"), "") or "").strip(),
        translation=str(st.session_state.get(_reading_key("translation"), "") or "").strip(),
        summary=str(st.session_state.get(_reading_key("summary"), "") or "").strip(),
        key_points=_text_lines(str(st.session_state.get(_reading_key("key_points"), "") or "")),
        claim_candidates=[item for item in claim_candidates if isinstance(item, dict)],
        citations=[item for item in citations if isinstance(item, dict)],
        synthesis_notes=str(st.session_state.get(_reading_key("synthesis_notes"), "") or "").strip(),
        generated_by=str(
            st.session_state.get(_reading_key("generated_by"), source.reading.generated_by) or ""
        ).strip(),
        updated_at=str(
            st.session_state.get(_reading_key("updated_at"), source.reading.updated_at) or ""
        ).strip(),
    )


def _seed_reading_state(source) -> None:
    seed_key = _reading_key("seed_source")
    if st.session_state.get(seed_key) == source.id:
        return
    reading = source.reading
    st.session_state[seed_key] = source.id
    st.session_state[_reading_key("excerpt")] = reading.excerpt
    st.session_state[_reading_key("translation")] = reading.translation
    st.session_state[_reading_key("summary")] = reading.summary
    st.session_state[_reading_key("key_points")] = "\n".join(reading.key_points)
    st.session_state[_reading_key("claim_candidates")] = yaml.dump(
        reading.claim_candidates,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ) if reading.claim_candidates else ""
    st.session_state[_reading_key("citations")] = yaml.dump(
        reading.citations,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ) if reading.citations else ""
    st.session_state[_reading_key("synthesis_notes")] = reading.synthesis_notes
    st.session_state[_reading_key("generated_by")] = reading.generated_by
    st.session_state[_reading_key("updated_at")] = reading.updated_at


def _store_reading_state(reading: ResearchReading) -> None:
    st.session_state[_reading_key("excerpt")] = reading.excerpt
    st.session_state[_reading_key("translation")] = reading.translation
    st.session_state[_reading_key("summary")] = reading.summary
    st.session_state[_reading_key("key_points")] = "\n".join(reading.key_points)
    st.session_state[_reading_key("claim_candidates")] = yaml.dump(
        reading.claim_candidates,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    st.session_state[_reading_key("citations")] = yaml.dump(
        reading.citations,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    st.session_state[_reading_key("synthesis_notes")] = reading.synthesis_notes
    st.session_state[_reading_key("generated_by")] = reading.generated_by
    st.session_state[_reading_key("updated_at")] = reading.updated_at


def _render_reading_room(inbox) -> None:
    st.subheader(ui["reading_room"])
    st.caption(ui["reading_flow_hint"])
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
        key=f"reading_source:{selected}",
    )
    source = inbox.by_id().get(source_id)
    if source is None:
        return
    _seed_reading_state(source)

    meta = {
        "id": source.id,
        "kind": source.kind,
        "status": source.status,
        "url": source.url,
        "evidence_refs": list(source.evidence_refs),
    }
    st.code(
        yaml.dump(meta, allow_unicode=True, default_flow_style=False, sort_keys=False),
        language="yaml",
    )

    mode = st.selectbox(
        ui["reading_mode"],
        ["summary", "translate", "claims", "synthesis"],
        key=f"reading_mode:{selected}",
    )
    excerpt = st.text_area(
        ui["excerpt"],
        height=180,
        key=_reading_key("excerpt"),
    )
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button(ui["generate_reading_draft"], type="primary"):
            reading, warnings = generate_reading_draft(
                source,
                excerpt,
                mode,
                profile=selected,
            )
            _store_reading_state(reading)
            st.session_state[_reading_key("warnings")] = warnings
            st.rerun()
    with b2:
        if st.button(ui["save_reading_annotations"]):
            reading = _reading_from_form(source)
            reading.updated_at = reading.updated_at or ""
            update_research_source(inbox, source.id, reading=reading)
            _save_sources(inbox, ui["saved"])
            st.rerun()
    warnings = st.session_state.get(_reading_key("warnings"), [])
    if isinstance(warnings, list):
        for warning in warnings:
            st.warning(str(warning))

    st.text_area(ui["translation"], height=140, key=_reading_key("translation"))
    st.text_area(ui["summary"], height=100, key=_reading_key("summary"))
    st.text_area(ui["key_points"], height=100, key=_reading_key("key_points"))
    st.text_area(ui["claim_candidates"], height=170, key=_reading_key("claim_candidates"))
    st.text_area(ui["citations"], height=150, key=_reading_key("citations"))
    st.text_area(ui["synthesis_notes"], height=130, key=_reading_key("synthesis_notes"))

    reading = _reading_from_form(source)
    try:
        patch = research_evidence_patch(source, reading)
        st.subheader(ui["evidence_candidate_preview"])
        st.code(
            yaml.dump(
                patch,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
            language="yaml",
        )
    except Exception as exc:
        patch = None
        st.warning(str(exc))
    with b3:
        if st.button(
            ui["create_evidence_candidate"],
            disabled=patch is None,
        ):
            try:
                assert_files_current([_sources_path, _pdir / "evidence-pool.yaml"])
                result = apply_research_evidence_candidate(
                    selected,
                    source.id,
                    patch or {},
                )
                refresh_file_snapshots(
                    [
                        _sources_path,
                        _pdir / "evidence-pool.yaml",
                        _pdir / "agent-activity.yaml",
                    ]
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=result["evidence_id"]))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _render_claims_citations(inbox) -> None:
    st.subheader(ui["claims_citations"])
    st.caption(ui["claim_boundary_hint"])
    if not inbox.sources:
        st.caption(ui["empty_status"])
        return
    source_id = st.selectbox(
        ui["source_id"],
        options=[source.id for source in inbox.sources],
        format_func=lambda sid: next(
            (source.title or source.id for source in inbox.sources if source.id == sid),
            sid,
        ),
        key=f"research_cc_source:{selected}",
    )
    source = inbox.by_id().get(source_id)
    if source is None:
        return

    with st.expander(ui["create_chunk"], expanded=not load_chunks(_pdir, source_id)):
        with st.form(f"research_create_chunk:{selected}"):
            chunk_kind = st.selectbox(ui["chunk_kind"], list(RESEARCH_CHUNK_KINDS))
            chunk_title = st.text_input(ui["chunk_title"])
            chunk_locator = st.text_input(ui["chunk_locator"])
            chunk_text = st.text_area(ui["chunk_text"], height=140)
            submitted = st.form_submit_button(ui["create"], type="primary")
        if submitted:
            try:
                chunk = create_chunk(
                    _pdir,
                    source_id,
                    chunk_text,
                    kind=chunk_kind,
                    title=chunk_title,
                    locator=chunk_locator,
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=chunk.id))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    source_chunks = load_chunks(_pdir, source_id)
    if source_chunks:
        st.dataframe(
            [
                {
                    "id": chunk.id,
                    "kind": chunk.kind,
                    "title": chunk.title,
                    "locator": chunk.locator,
                    "text": chunk.text[:180],
                }
                for chunk in source_chunks
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption(ui["chunks_empty"])

    chunks = load_chunks(_pdir)
    chunk_ids = [chunk.id for chunk in chunks]
    claim_rows = load_research_claims(_pdir)
    claim_ids = [claim.id for claim in claim_rows]
    citation_rows = load_research_citations(_pdir)

    left, right = st.columns(2)
    with left:
        with st.expander(ui["create_research_claim"], expanded=bool(source_chunks) and not claim_rows):
            with st.form(f"research_create_claim:{selected}"):
                claim_id = st.text_input(ui["research_claim_id"])
                claim_type = st.selectbox(
                    ui["research_claim_type"],
                    ["learning", "finding", "hypothesis", "project", "skill", "impact"],
                )
                claim_status = st.selectbox(
                    ui["research_claim_status"],
                    ["draft", "ready", "promoted", "dismissed"],
                )
                claim_text = st.text_area(ui["research_claim_text"], height=110)
                claim_chunks = st.multiselect(
                    ui["chunk_refs"],
                    options=chunk_ids,
                    default=[chunk.id for chunk in source_chunks[:1]],
                )
                human_note = st.checkbox(ui["human_note"])
                rationale = st.text_area(ui["rationale"], height=80)
                submitted_claim = st.form_submit_button(ui["save"], type="primary")
            if submitted_claim:
                try:
                    claim = upsert_research_claim(
                        _pdir,
                        claim_text,
                        claim_id=claim_id,
                        type=claim_type,
                        status=claim_status,
                        source_refs=[source_id],
                        chunk_refs=claim_chunks,
                        rationale=rationale,
                        human_note=human_note,
                    )
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["created"].format(id=claim.id))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with right:
        with st.expander(ui["create_citation"], expanded=bool(claim_ids) and not citation_rows):
            with st.form(f"research_create_citation:{selected}"):
                citation_claim = st.selectbox(
                    ui["research_claim_id"],
                    options=claim_ids,
                    key=f"research_citation_claim:{selected}",
                ) if claim_ids else ""
                citation_chunk = st.selectbox(
                    ui["chunk_refs"],
                    options=["", *chunk_ids],
                    key=f"research_citation_chunk:{selected}",
                )
                locator = st.text_input(ui["chunk_locator"], key=f"citation_locator:{selected}")
                quote = st.text_area(ui["citation_quote"], height=90)
                bibliography = st.text_area(ui["bibliography"], height=70)
                submitted_citation = st.form_submit_button(ui["create"], type="primary")
            if submitted_citation:
                try:
                    citation = create_citation(
                        _pdir,
                        citation_claim,
                        source_id=source_id,
                        chunk_id=citation_chunk,
                        locator=locator,
                        quote=quote,
                        bibliography=bibliography,
                        url=getattr(source, "url", ""),
                    )
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["created"].format(id=citation.id))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    st.subheader(ui["research_claims"])
    if claim_rows:
        st.dataframe(
            [
                {
                    "id": claim.id,
                    "status": claim.status,
                    "type": claim.type,
                    "sources": ", ".join(claim.source_refs),
                    "chunks": ", ".join(claim.chunk_refs),
                    "citations": ", ".join(claim.citation_refs),
                    "text": claim.text,
                }
                for claim in claim_rows
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption(ui["claims_empty"])

    if claim_ids:
        selected_claim_id = st.selectbox(
            ui["research_claim_id"],
            options=claim_ids,
            key=f"research_evidence_candidate_claim:{selected}",
        )
        try:
            patch = research_claim_to_evidence_candidate(_pdir, selected_claim_id)
            st.code(
                yaml.dump(patch, allow_unicode=True, default_flow_style=False, sort_keys=False),
                language="yaml",
            )
        except Exception as exc:
            patch = None
            st.warning(str(exc))
        if st.button(ui["create_evidence_candidate"], disabled=patch is None):
            claim = next((item for item in claim_rows if item.id == selected_claim_id), None)
            source_ref = (claim.source_refs[0] if claim and claim.source_refs else source_id)
            try:
                assert_files_current([_sources_path, _pdir / "evidence-pool.yaml"])
                result = apply_research_evidence_candidate(selected, source_ref, patch or {})
                if claim is not None:
                    upsert_research_claim(
                        _pdir,
                        claim.text,
                        claim_id=claim.id,
                        status="promoted",
                        type=claim.type,
                        source_refs=claim.source_refs,
                        chunk_refs=claim.chunk_refs,
                        citation_refs=claim.citation_refs,
                        evidence_refs=[*claim.evidence_refs, result["evidence_id"]],
                        rationale=claim.rationale,
                        human_note=claim.human_note,
                        warnings=claim.warnings,
                        generated_by=claim.generated_by or "research_workspace",
                    )
                refresh_file_snapshots(
                    [
                        _sources_path,
                        _pdir / "evidence-pool.yaml",
                        _pdir / "agent-activity.yaml",
                    ]
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=result["evidence_id"]))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    st.subheader(ui["research_citations"])
    if citation_rows:
        st.dataframe(
            [
                {
                    "id": citation.id,
                    "claim": citation.claim_id,
                    "source": citation.source_id,
                    "chunk": citation.chunk_id,
                    "locator": citation.locator,
                    "quote": citation.quote[:140],
                }
                for citation in citation_rows
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption(ui["citations_empty"])


def _render_synthesis_drafts() -> None:
    st.subheader(_l("synthesis_export", "Synthesis / Export"))
    citation_rows = load_research_citations(_pdir)
    chunk_rows = load_chunks(_pdir)
    claim_rows_all = load_research_claims(_pdir)
    paper_ids = [source.id for source in _paper_sources(load_research_sources(selected))]
    with st.expander(_l("export_citations", "Export citations"), expanded=False):
        citation_refs = st.multiselect(
            ui["research_citations"],
            options=[citation.id for citation in citation_rows],
            format_func=lambda cid: next(
                (
                    f"{cid} · {citation.locator or citation.source_id}"
                    for citation in citation_rows
                    if citation.id == cid
                ),
                cid,
            ),
        )
        export_format = st.radio("Format", ["markdown", "bibtex"], horizontal=True)
        try:
            export_body = format_research_citations(
                _pdir,
                citation_refs,
                format=export_format,
            )
        except Exception as exc:
            export_body = ""
            st.warning(str(exc))
        if export_body:
            st.text_area(
                _l("export_preview", "Export preview"),
                value=export_body,
                height=220,
                key=f"export_preview:{selected}:{export_format}",
            )
            st.download_button(
                _l("download_export", "Download export"),
                data=export_body,
                file_name=f"research-citations.{ 'bib' if export_format == 'bibtex' else 'md' }",
            )
            if st.button(_l("save_export", "Save export")):
                try:
                    path = save_research_export(_pdir, export_body, format=export_format)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(str(path))
                except Exception as exc:
                    st.error(str(exc))

    with st.expander(_l("reading_note_export", "Reading note export"), expanded=False):
        note_source = st.selectbox(
            ui["source_id"],
            options=paper_ids,
            format_func=lambda sid: _source_label(load_research_sources(selected), sid),
            key=f"reading_note_source:{selected}",
        ) if paper_ids else ""
        note_claims = st.multiselect(
            ui["research_claims"],
            options=[claim.id for claim in claim_rows_all],
            key=f"reading_note_claims:{selected}",
        )
        note_chunks = st.multiselect(
            ui["chunk_refs"],
            options=[chunk.id for chunk in chunk_rows if not note_source or chunk.source_id == note_source],
            key=f"reading_note_chunks:{selected}",
        )
        note_citations = st.multiselect(
            ui["citations"],
            options=[citation.id for citation in citation_rows if not note_source or citation.source_id == note_source],
            key=f"reading_note_citations:{selected}",
        )
        if note_source:
            note_body = create_reading_note_markdown(
                _pdir,
                note_source,
                claim_refs=note_claims,
                chunk_refs=note_chunks,
                citation_refs=note_citations,
            )
            st.text_area(
                ui["body"],
                value=note_body,
                height=240,
                key=f"reading_note_body:{selected}:{note_source}",
            )
            n1, n2 = st.columns(2)
            with n1:
                st.download_button(
                    _l("download_note", "Download note"),
                    data=note_body,
                    file_name=f"{note_source.replace(':', '-')}-reading-note.md",
                )
            with n2:
                if st.button(_l("save_note", "Save note")):
                    try:
                        path = save_paper_note(
                            _pdir,
                            note_source,
                            note_body,
                            metadata={
                                "claim_refs": note_claims,
                                "chunk_refs": note_chunks,
                                "citation_refs": note_citations,
                            },
                        )
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(str(path))
                    except Exception as exc:
                        st.error(str(exc))

    st.subheader(ui["synthesis_drafts"])
    claim_rows = load_research_claims(_pdir)
    claim_ids = [claim.id for claim in claim_rows]
    with st.expander(ui["create_synthesis_draft"], expanded=not load_research_drafts(_pdir)):
        with st.form(f"research_synthesis_create:{selected}"):
            title = st.text_input(ui["title_label"], key=f"research_synthesis_title:{selected}")
            selected_claims = st.multiselect(
                ui["research_claims"],
                options=claim_ids,
                format_func=lambda cid: next(
                    (f"{cid} - {claim.text[:80]}" for claim in claim_rows if claim.id == cid),
                    cid,
                ),
            )
            body = st.text_area(
                ui["body"],
                height=180,
                key=f"research_synthesis_body:{selected}",
            )
            submitted = st.form_submit_button(ui["create"], type="primary")
        if submitted:
            try:
                draft = draft_synthesis_from_claims(
                    _pdir,
                    title,
                    selected_claims,
                    body=body,
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=draft["id"]))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    drafts = load_research_drafts(_pdir)
    if not drafts:
        st.caption(ui["drafts_empty"])
        return
    st.dataframe(
        [
            {
                "id": draft.get("id"),
                "status": draft.get("status"),
                "title": draft.get("title"),
                "claims": ", ".join(draft.get("claim_refs") or []),
                "sources": ", ".join(draft.get("source_refs") or []),
                "citations": ", ".join(draft.get("citation_refs") or []),
            }
            for draft in drafts
        ],
        use_container_width=True,
        hide_index=True,
    )
    draft_id = st.selectbox(
        ui["synthesis_draft_id"],
        options=[str(draft.get("id")) for draft in drafts],
        key=f"research_blog_draft:{selected}",
    )
    try:
        candidate = research_draft_to_blog_candidate(_pdir, draft_id)
        st.subheader(ui["blog_candidate_preview"])
        st.code(
            yaml.dump(
                {key: value for key, value in candidate.items() if key != "body"},
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
            language="yaml",
        )
        st.text_area(
            ui["body"],
            value=str(candidate.get("body") or ""),
            height=240,
            disabled=True,
            key=f"blog_candidate_body:{selected}:{draft_id}",
        )
    except Exception as exc:
        candidate = None
        st.warning(str(exc))
    if st.button(ui["create_blog_draft"], disabled=candidate is None):
        try:
            path = create_blog_draft(
                selected,
                title=str(candidate.get("title") or draft_id),
                body=str(candidate.get("body") or ""),
                tags=list(candidate.get("tags") or []),
                summary=str(candidate.get("summary") or ""),
                related_evidence=list(candidate.get("related_evidence") or []),
                related_kanban=list(candidate.get("related_kanban") or []),
                related_claims=list(candidate.get("related_claims") or []),
                related_sources=list(candidate.get("related_sources") or []),
                related_research_claims=list(candidate.get("related_research_claims") or []),
                related_citations=list(candidate.get("related_citations") or []),
            )
            stash_git_backup_results()
            clear_web_cache()
            st.success(str(path))
        except Exception as exc:
            st.error(str(exc))


def _render_connectors() -> None:
    st.subheader(ui["connectors"])
    st.caption(ui["connectors_caption"])
    book = load_connectors(_pdir)
    rows = list(book.get("connectors") or [])
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.caption(ui["connectors_empty"])

    with st.expander(ui["configure_connector"], expanded=not rows):
        with st.form(f"research_connector_config:{selected}"):
            provider = st.selectbox(ui["connector_provider"], CONNECTOR_PROVIDERS)
            connector_id = st.text_input(ui["connector_id"])
            query = st.text_input(ui["connector_query"])
            enabled = st.checkbox(ui["connector_enabled"], value=True)
            privacy_default = st.selectbox(ui["privacy_default"], ["private", "public"])
            options_raw = st.text_area(ui["connector_options"], height=90)
            submitted = st.form_submit_button(ui["save"], type="primary")
        if submitted:
            try:
                options = yaml.safe_load(options_raw) if options_raw.strip() else {}
                if options is None:
                    options = {}
                if not isinstance(options, dict):
                    raise ValueError("Connector options must be a YAML mapping.")
                row = upsert_connector(
                    _pdir,
                    provider=provider,
                    connector_id=connector_id,
                    query=query,
                    enabled=enabled,
                    privacy_default=privacy_default,
                    options=options,
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=row["id"]))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    rows = list(load_connectors(_pdir).get("connectors") or [])
    if not rows:
        return
    picked = st.selectbox(
        ui["connector_id"],
        options=[str(row.get("id")) for row in rows],
        key=f"research_connector_run:{selected}",
    )
    dry_col, run_col = st.columns(2)
    with dry_col:
        if st.button(ui["connector_dry_run"]):
            try:
                result = sync_connector(_pdir, picked, dry_run=True)
                st.code(
                    yaml.dump(result.to_dict(), allow_unicode=True, default_flow_style=False, sort_keys=False),
                    language="yaml",
                )
            except Exception as exc:
                st.error(str(exc))
    with run_col:
        if st.button(ui["connector_run_now"], type="primary"):
            try:
                assert_files_current([_sources_path])
                result = sync_connector(_pdir, picked, dry_run=False)
                refresh_file_snapshots([_sources_path, _pdir / "research" / "connectors.yaml"])
                stash_git_backup_results()
                clear_web_cache()
                st.code(
                    yaml.dump(result.to_dict(), allow_unicode=True, default_flow_style=False, sort_keys=False),
                    language="yaml",
                )
            except Exception as exc:
                st.error(str(exc))


_head_l, _head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
with _head_l:
    st.title(ui["title"])
    st.caption(ui["page_context_line"])
with _head_goal:
    render_current_goal_strip(selected, compact=True, align="right")

inbox = load_research_sources(selected)

tab_overview, tab_search, tab_library, tab_reader, tab_claims, tab_export, tab_advanced = st.tabs(
    [
        _l("overview", "Overview"),
        _l("paper_search", "Paper Search"),
        _l("paper_library", "Paper Library"),
        _l("reader", "Reader"),
        ui["claims_citations"],
        _l("synthesis_export", "Synthesis / Export"),
        _l("advanced_connectors", "Advanced Connectors"),
    ]
)

with tab_overview:
    _render_workspace_overview(inbox)

with tab_search:
    _render_paper_search(inbox)

with tab_library:
    _render_paper_library(inbox)

with tab_reader:
    _render_paper_reader(inbox)

with tab_claims:
    _render_claims_citations(inbox)

with tab_export:
    _render_synthesis_drafts()

with tab_advanced:
    st.subheader(ui["source_inbox"])
    _render_source_queue(inbox)
    st.divider()
    with st.expander(ui["add_source"], expanded=not inbox.sources):
        _render_source_form(
            inbox,
            prefix=f"research_source_add_{selected}",
        )
    st.divider()
    _render_candidate_preview(inbox)
    st.divider()
    st.subheader(ui["reading_room"])
    _render_reading_room(inbox)
    st.divider()
    _render_connectors()
