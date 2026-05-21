"""Paper Reading Studio -- search, read, annotate, and cite papers."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import streamlit as st
import yaml

from nblane.core.auth import mint_reader_token
from nblane.core.ai import (
    answer_paper_question,
    explain_paper_selection,
    extract_paper_claims,
    generate_paper_review_card,
    generate_paper_source_guide,
    search_papers_codex,
    translate_paper_segments,
)
from nblane.core.io import profile_dir
from nblane.core.reader_actions import ReaderActionContext, handle_reader_action
from nblane.core.research_papers import (
    PAPER_SEARCH_PROVIDERS,
    PaperSearchResult,
    _paper_search_imported_refs,
    _paper_search_library_tree_hint,
    _paper_search_result_has_import_ref,
    auto_chunk_paper,
    build_reader_payload,
    create_chunk_from_annotation,
    create_paper_annotation,
    create_reading_note_markdown,
    ensure_paper_reading_artifacts,
    extract_paper_pages,
    extract_paper_segments,
    format_research_citations,
    grobid_readiness,
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
    normalize_translation_row,
    paper_library_paths,
    paper_citation_diagnostics,
    paper_overview,
    paper_rows,
    save_paper_analysis,
    save_paper_annotations,
    save_paper_note,
    save_research_export,
    search_papers,
    text_hash,
    translate_full_paper,
    translation_text_from_row,
    translation_rows_for_segments,
    upsert_paper_library_node,
    upsert_paper_translations,
    validate_paper_library,
)
from nblane.research_paper_reader_component.events import (
    ANNOTATION_CREATE,
    ANNOTATION_DELETE,
    ANNOTATION_UPDATE,
    ASK_PAPER,
    CODEX_DEEP_READ,
    CREATE_CHUNK_FROM_SELECTION,
    CREATE_CITATION,
    EXPLAIN_SELECTION,
    READER_STATE_CHANGED,
    REQUEST_PAGE_PREVIEW,
    REQUEST_PAGE_PREVIEWS,
    REQUEST_READER_CONTEXT,
    RETRY_TRANSLATION_SCOPE,
    SAVE_PROGRESS,
    TRANSLATE_FULL_PAPER,
    TRANSLATE_SELECTION,
    TRANSLATE_VISIBLE_PAGES,
    clean_page_list,
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
user = require_login()
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


def _marked_search_results(results: list[object]) -> list[PaperSearchResult]:
    return mark_imported_paper_results(_pdir, results)


def _unique_text(values: list[str]) -> list[str]:
    out = []
    seen = set()
    for value in values:
        clean = str(value or "").strip()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _normalized_title(value: str) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _search_result_warnings(result: PaperSearchResult, inbox) -> list[str]:
    warnings = list(result.warnings)
    if result.imported_source_id:
        warnings.append(f"Duplicate import: already stored as {result.imported_source_id}.")
    link_status = str((result.link_check or {}).get("status") or "").strip()
    if result.needs_link_check:
        warnings.append("Needs link check before automatic PDF download.")
    if link_status and link_status not in {"ok", "200"}:
        warnings.append(f"Link check: {link_status}.")
    if not result.open_access_pdf:
        warnings.append("No open-access PDF URL; import metadata first or upload a local PDF.")

    title_key = _normalized_title(result.title)
    for source in _paper_sources(inbox):
        if source.id == result.imported_source_id:
            continue
        same_title = title_key and title_key == _normalized_title(source.title)
        same_year = not result.year or not source.published or result.year == str(source.published)[:4]
        if not (same_title and same_year):
            continue
        source_meta = source.metadata or {}
        source_doi = str(source_meta.get("doi") or "").lower()
        result_doi = result.doi.lower()
        source_arxiv = str(source_meta.get("arxiv_id") or "").lower()
        result_arxiv = result.arxiv_id.lower()
        if result_doi and source_doi and result_doi != source_doi:
            warnings.append(f"Metadata conflict with {source.id}: DOI differs.")
        elif result_arxiv and source_arxiv and result_arxiv != source_arxiv:
            warnings.append(f"Metadata conflict with {source.id}: arXiv id differs.")
        elif not result.imported_source_id:
            warnings.append(f"Possible duplicate: similar title/year to {source.id}.")
    return _unique_text(warnings)


def _render_search_result_details(results: list[PaperSearchResult], inbox) -> None:
    st.markdown(f"**{_l('result_details', 'Result details')}**")
    for result in results:
        title = result.title or result.candidate_id
        with st.expander(f"{title} · {result.year or 'n.d.'}", expanded=False):
            warnings = _search_result_warnings(result, inbox)
            for warning in warnings:
                st.warning(warning)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{_l('metadata', 'Metadata')}**")
                st.write(
                    {
                        "candidate_id": result.candidate_id,
                        "authors": result.authors,
                        "year": result.year,
                        "venue": result.venue,
                        "citations": result.citation_count,
                        "providers": result.provider_refs,
                    }
                )
                st.markdown(f"**{_l('identifiers', 'Identifiers')}**")
                st.write(
                    {
                        "doi": result.doi,
                        "arxiv_id": result.arxiv_id,
                        "semantic_scholar_id": result.semantic_scholar_id,
                        "canonical_url": result.canonical_url,
                        "pdf_url": result.pdf_url,
                    }
                )
            with c2:
                st.markdown(f"**{_l('import_hints', 'Import hints')}**")
                st.write(
                    {
                        "imported": result.imported_source_id,
                        "oa_pdf": bool(result.open_access_pdf),
                        "tags": result.tags,
                        "fields_of_study": result.fields_of_study,
                        "suggested_library_nodes": result.suggested_library_nodes,
                    }
                )
                st.markdown(f"**{_l('link_check', 'Link check')}**")
                st.code(
                    yaml.dump(
                        result.link_check or {"status": "needs check"},
                        allow_unicode=True,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            if result.why_relevant:
                st.markdown(f"**{_l('relevance', 'Relevance')}**")
                st.caption(result.why_relevant)
            if result.abstract:
                st.markdown(f"**{_l('abstract', 'Abstract')}**")
                st.write(result.abstract)


def _result_rows(results: list[object]) -> list[dict[str, object]]:
    marked = _marked_search_results(results)
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
            "warnings": " · ".join(_search_result_warnings(row, load_research_sources(selected))),
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
    prepare_notice_key = f"paper_reader_prepare_notice:{selected}"
    prepare_notice = st.session_state.pop(prepare_notice_key, "")
    if prepare_notice:
        st.info(str(prepare_notice))
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
                    payload={
                        "filters": filters,
                        "providers": providers,
                        "project_refs": _text_lines(project_refs),
                        "goal_refs": _text_lines(goal_refs),
                        "already_imported": _paper_search_imported_refs(_pdir),
                        "library_tree_hint": _paper_search_library_tree_hint(_pdir),
                    },
                )
                raw = result.structured if isinstance(result.structured, dict) else {}
                candidates = []
                for row in raw.get("results", []):
                    item = PaperSearchResult.from_dict(row)
                    if item is None or not _paper_search_result_has_import_ref(item):
                        continue
                    candidates.append(item.to_dict())
                if not candidates:
                    if result.error:
                        st.warning(
                            f"{result.backend or 'local_codex_readonly'} failed "
                            f"({result.error}); using provider search fallback."
                        )
                    else:
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
            marked_results = _marked_search_results(results)
            result_dicts = [row.to_dict() for row in marked_results]
            st.dataframe(_result_rows(result_dicts), use_container_width=True, hide_index=True)
            _render_search_result_details(marked_results, inbox)
            selected_ids = st.multiselect(
                _l("select_to_import", "Select to import"),
                options=[row.candidate_id for row in marked_results],
                format_func=lambda cid: next(
                    (row.title or cid for row in marked_results if row.candidate_id == cid),
                    cid,
                ),
            )
            with st.expander(_l("selected_yaml_preview", "Selected YAML preview"), expanded=bool(selected_ids)):
                st.code(
                    yaml.dump(
                        [row.to_dict() for row in marked_results if row.candidate_id in set(selected_ids)],
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
                visibility = st.selectbox(ui["visibility"], ["private", "public"], index=0)
                status = st.selectbox(ui["status"], SOURCE_STATUSES, index=SOURCE_STATUSES.index("inbox"))
                pdf_strategy = st.radio(
                    _l("pdf_strategy", "PDF strategy"),
                    [
                        _l("pdf_strategy_metadata_only", "Metadata only"),
                        _l("download_open_access_pdf", "Download open-access PDF"),
                        _l("pdf_strategy_upload_later", "Upload local PDF after import"),
                    ],
                    horizontal=True,
                    key=f"pdf_strategy:{selected}",
                )
                confirmed = st.form_submit_button(_l("import_selected", "Import selected"), type="primary")
            selected_results = [row for row in marked_results if row.candidate_id in set(selected_ids)]
            if pdf_strategy == _l("download_open_access_pdf", "Download open-access PDF"):
                for row in selected_results:
                    if row.needs_link_check:
                        st.warning(f"{row.title}: needs link check before PDF download.")
                    if not row.open_access_pdf:
                        st.warning(f"{row.title}: no open-access PDF URL to download.")
            elif pdf_strategy == _l("pdf_strategy_upload_later", "Upload local PDF after import") and selected_ids:
                st.info(
                    _l(
                        "upload_pdf_after_import_hint",
                        "Import will create private inbox metadata; attach the local PDF from Upload PDF after import.",
                    )
                )
            if confirmed:
                try:
                    assert_files_current([_sources_path])
                    imported = import_paper_search_results(
                        _pdir,
                        result_dicts,
                        selected_ids,
                        {
                            "library_node_refs": [node_ref] if node_ref else [],
                            "tags": _tags(tags),
                            "visibility": visibility,
                            "status": status,
                            "goal_refs": _text_lines(goal_refs),
                            "project_refs": _text_lines(project_refs),
                            "download_pdf": pdf_strategy == _l("download_open_access_pdf", "Download open-access PDF"),
                        },
                    )
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(_l("imported_papers", "Imported papers: {ids}").format(ids=", ".join(imported) or "0"))
                    refreshed = load_research_sources(selected).by_id()
                    imported_pdf_assets = [
                        source_id
                        for source_id in imported
                        if (
                            (refreshed.get(source_id).metadata if refreshed.get(source_id) is not None else {}).get(
                                "pdf_asset_ref"
                            )
                        )
                    ]
                    if (
                        pdf_strategy == _l("download_open_access_pdf", "Download open-access PDF")
                        and imported_pdf_assets
                    ):
                        st.session_state[prepare_notice_key] = _l(
                            "reader_background_prepare_hint",
                            "PDF assets are saved now; Reader will prepare text in the background when opened.",
                        )
                    for source_id in imported:
                        source = refreshed.get(source_id)
                        metadata = source.metadata if source is not None else {}
                        if metadata.get("pdf_download_status") not in ("", None, "downloaded"):
                            st.warning(
                                f"{source_id}: {metadata.get('pdf_download_status')} · "
                                f"{metadata.get('pdf_download_error', '')}"
                            )
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
            visibility = st.selectbox(ui["visibility"], ["private", "public"], index=0)
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
            visibility = st.selectbox(ui["visibility"], ["private", "public"], index=0)
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
                st.session_state[prepare_notice_key] = _l(
                    "reader_background_prepare_hint",
                    "PDF assets are saved now; Reader will prepare text in the background when opened.",
                )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _render_grobid_status_block(source=None) -> None:
    configured = bool(os.getenv("NBLANE_GROBID_URL", "").strip())
    with st.expander(_l("grobid_readiness", "GROBID readiness"), expanded=False):
        if not configured:
            st.info(
                _l(
                    "grobid_not_configured",
                    "NBLANE_GROBID_URL is not configured; structured extraction will use PyMuPDF fallback.",
                )
            )
            if source is not None:
                metadata = source.metadata or {}
                warnings = metadata.get("structured_extraction_warnings") or []
                for warning in warnings:
                    st.warning(str(warning))
                st.caption(
                    " · ".join(
                        [
                            f"structure_backend={metadata.get('structure_backend', '') or 'missing'}",
                            f"structured_extracted_at={metadata.get('structured_extracted_at', '') or 'never'}",
                        ]
                    )
                )
            return
        try:
            status = grobid_readiness()
            if status.get("available"):
                st.success(str(status.get("message") or "GROBID available."))
            else:
                st.warning(str(status.get("message") or "GROBID unavailable."))
            st.code(
                yaml.dump(status, allow_unicode=True, default_flow_style=False, sort_keys=False),
                language="yaml",
            )
        except Exception as exc:
            st.warning(str(exc))
        if source is not None:
            metadata = source.metadata or {}
            warnings = metadata.get("structured_extraction_warnings") or []
            if warnings:
                for warning in warnings:
                    st.warning(str(warning))
            st.caption(
                " · ".join(
                    [
                        f"structure_backend={metadata.get('structure_backend', '') or 'missing'}",
                        f"structured_extracted_at={metadata.get('structured_extracted_at', '') or 'never'}",
                    ]
                )
            )


def _render_paper_library(inbox) -> None:
    st.subheader(_l("paper_library", "Paper Library"))
    st.caption(
        _l(
            "paper_library_caption",
            "Tree nodes describe where papers belong; status, tags, PDF assets, and reading artifacts are paper properties.",
        )
    )
    _render_grobid_status_block()
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
    display_rows = []
    for row in rows:
        display_row = {
            key: value
            for key, value in row.items()
            if key not in {"source"}
        }
        display_row["badges"] = ", ".join(str(item) for item in row.get("badges", []) if str(item).strip())
        display_rows.append(display_row)
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
            detail_row = next((row for row in rows if str(row.get("id")) == detail_id), {})
            annotations = load_paper_annotations(_pdir, source.id)
            translations = load_paper_translations(_pdir, source.id)
            pages_count = len(load_paper_pages(_pdir, source.id))
            segments_count = len(load_paper_segments(_pdir, source.id))
            source_chunks = load_chunks(_pdir, source.id)
            with st.expander(_l("detail_drawer", "Detail drawer"), expanded=True):
                metadata_tab, storage_tab, workflow_tab = st.tabs(
                    [
                        _l("metadata", "Metadata"),
                        _l("storage", "Storage"),
                        _l("workflow", "Workflow"),
                    ]
                )
                with metadata_tab:
                    st.markdown(f"**{source.title}**")
                    st.caption(source.id)
                    st.code(
                        yaml.dump(
                            {
                                "metadata": source.metadata,
                                "library_node_refs": source.library_node_refs,
                                "tags": source.tags,
                                "authors": source.authors,
                                "published": source.published,
                                "url": source.url,
                                "project_refs": source.project_refs,
                                "goal_refs": source.goal_refs,
                                "summary": source.summary,
                            },
                            allow_unicode=True,
                            default_flow_style=False,
                            sort_keys=False,
                        ),
                        language="yaml",
                    )
                with storage_tab:
                    s1, s2, s3, s4 = st.columns(4)
                    s1.metric("PDF", "yes" if source.metadata.get("pdf_asset_ref") else "missing")
                    s2.metric(_l("pages", "Pages"), source.metadata.get("page_count", "") or pages_count)
                    s3.metric(_l("segments", "Segments"), segments_count)
                    s4.metric(_l("translations", "Translations"), len(translations))
                    st.code(
                        yaml.dump(
                            {
                                "pdf_asset_ref": source.metadata.get("pdf_asset_ref", ""),
                                "pdf_sha256": source.metadata.get("pdf_sha256", ""),
                                "pdf_byte_size": source.metadata.get("pdf_byte_size", ""),
                                "page_count": source.metadata.get("page_count", ""),
                                "pdf_imported_at": source.metadata.get("pdf_imported_at", ""),
                                "pdf_warnings": source.metadata.get("pdf_warnings", []),
                                "text_extraction_backend": source.metadata.get("text_extraction_backend")
                                or source.metadata.get("local_pdf_backend", ""),
                                "local_pdf_backend": source.metadata.get("local_pdf_backend", ""),
                                "text_extracted_at": source.metadata.get("text_extracted_at", ""),
                                "text_extraction_warnings": source.metadata.get("text_extraction_warnings", []),
                                "structure_backend": source.metadata.get("structure_backend", ""),
                                "structured_extracted_at": source.metadata.get("structured_extracted_at", ""),
                                "structured_extraction_warnings": source.metadata.get("structured_extraction_warnings", []),
                                "grobid_status": source.metadata.get("grobid_status", ""),
                            },
                            allow_unicode=True,
                            default_flow_style=False,
                            sort_keys=False,
                        ),
                        language="yaml",
                    )
                with workflow_tab:
                    badges = [str(item) for item in detail_row.get("badges", []) if str(item).strip()]
                    if badges:
                        st.caption(" · ".join(badges))
                    w1, w2, w3, w4 = st.columns(4)
                    w1.metric(_l("annotations", "Annotations"), len(annotations))
                    w2.metric(ui["chunk_refs"], len(source_chunks))
                    w3.metric(ui["research_claims"], detail_row.get("claims_count", 0))
                    w4.metric(ui["research_citations"], detail_row.get("citations_count", 0))
                    st.code(
                        yaml.dump(
                            {
                                "status": source.status,
                                "visibility": source.visibility,
                                "last_read": detail_row.get("last_read", ""),
                                "evidence_refs": source.evidence_refs,
                                "reading": source.reading.to_dict(),
                            },
                            allow_unicode=True,
                            default_flow_style=False,
                            sort_keys=False,
                        ),
                        language="yaml",
                    )
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


def _reader_key(source_id: str, name: str) -> str:
    return f"paper_reader:{selected}:{source_id}:{name}"


def _set_reader_action_status(source_id: str, action: str, phase: str, message: str) -> None:
    st.session_state[_reader_key(source_id, "last_action_status")] = {
        "action": action,
        "phase": phase,
        "message": message,
    }


def _payload_text(payload: dict, *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _payload_list(payload: dict, *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            values.extend(_tags(value))
        elif isinstance(value, (list, tuple, set)):
            values.extend(str(item).strip() for item in value if str(item).strip())
        elif value is not None and str(value).strip():
            values.append(str(value).strip())
    return _unique_text(values)


def _payload_int(payload: dict, key: str, default: int = 0) -> int:
    try:
        return int(payload.get(key) or default)
    except (TypeError, ValueError):
        return default


def _reader_requested_pages(source_id: str) -> set[int]:
    store = st.session_state.setdefault("reader_requested_pages", {})
    if not isinstance(store, dict):
        store = {}
        st.session_state["reader_requested_pages"] = store
    values = store.setdefault(source_id, set())
    if isinstance(values, set):
        return values
    if isinstance(values, list):
        cleaned = {int(item) for item in values if str(item).strip().isdigit()}
        store[source_id] = cleaned
        return cleaned
    store[source_id] = set()
    return store[source_id]


def _reader_event_identity(event: dict) -> str:
    explicit = event.get("event_id") or event.get("id")
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    explicit = explicit or payload.get("event_id") or payload.get("idempotency_key")
    if explicit:
        return str(explicit)
    return yaml.dump(event, allow_unicode=True, sort_keys=True)


def _save_reader_progress(source_id: str, page: int) -> None:
    page = max(1, int(page or 1))
    saved_key = _reader_key(source_id, "saved_progress_page")
    if st.session_state.get(saved_key) == page:
        return
    current = load_research_sources(selected)
    src = current.by_id().get(source_id)
    if src is None:
        return
    metadata = dict(src.metadata or {})
    metadata["last_read_page"] = page
    metadata["last_read_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    assert_files_current([_sources_path])
    update_research_source(current, source_id, metadata=metadata, status="reading")
    save_research_sources(selected, current)
    refresh_file_snapshots([_sources_path])
    stash_git_backup_results()
    clear_web_cache()
    st.session_state[saved_key] = page


def _save_reader_state(source_id: str, payload: dict) -> None:
    page = max(1, _payload_int(payload, "page", _payload_int(payload, "primary_page", 1)))
    visible_pages = clean_page_list(
        payload.get("visible_pages") if isinstance(payload.get("visible_pages"), list) else payload.get("last_visible_pages")
    )
    metadata: dict[str, object] = {
        "last_read_page": page,
        "last_read_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    for key in (
        "reader_mode",
        "scale_mode",
        "active_tab",
        "target_lang",
        "focused_annotation_id",
        "focused_chunk_id",
        "active_left_tab",
        "active_translation_anchor",
    ):
        value = _payload_text(payload, key)
        if value:
            metadata[key] = value
    for key in ("compare_split_ratio", "panel_width"):
        if key in payload:
            metadata[key] = _payload_int(payload, key, int(metadata.get(key) or (50 if key == "compare_split_ratio" else 340)))
    if "side_panel_collapsed" in payload:
        metadata["side_panel_collapsed"] = bool(payload.get("side_panel_collapsed"))
    if "left_rail_collapsed" in payload:
        metadata["left_rail_collapsed"] = bool(payload.get("left_rail_collapsed"))
    if "translation_source_visible" in payload:
        metadata["translation_source_visible"] = bool(payload.get("translation_source_visible"))
    if visible_pages:
        metadata["last_visible_pages"] = visible_pages
    current = load_research_sources(selected)
    if current.by_id().get(source_id) is None:
        return
    assert_files_current([_sources_path])
    update_research_source(current, source_id, metadata={**dict(current.by_id()[source_id].metadata or {}), **metadata}, status="reading")
    save_research_sources(selected, current)
    refresh_file_snapshots([_sources_path])
    stash_git_backup_results()
    clear_web_cache()


def _translation_counts_for_segments(source_id: str, target_lang: str = "zh") -> dict[str, int]:
    segments = load_paper_segments(_pdir, source_id)
    translations = {
        row.segment_id: row
        for row in load_paper_translations(_pdir, source_id)
        if row.segment_id and row.target_lang == target_lang
    }
    counts = {"translated": 0, "missing": 0, "stale": 0, "failed": 0}
    for segment in segments:
        row = translations.get(segment.segment_id)
        if row is None:
            counts["missing"] += 1
        elif row.status == "failed":
            counts["failed"] += 1
        elif row.status == "stale" or row.source_hash != segment.text_hash:
            counts["stale"] += 1
        elif row.translated_text:
            counts["translated"] += 1
        else:
            counts["missing"] += 1
    return counts


def _selection_segments(payload: dict, segment_rows) -> list[dict[str, object]]:
    refs = set(
        _payload_list(
            payload,
            "segment_refs",
            "segment_ids",
            "segment_id",
            "scope_refs",
            "scope_ref",
        )
    )
    if refs:
        return [segment.to_dict() for segment in segment_rows if segment.segment_id in refs]
    selected_text = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
    if not selected_text:
        return []
    selected_hash = _payload_text(payload, "selected_text_hash", "text_hash", "source_hash")
    if not selected_hash:
        selected_hash = text_hash(selected_text)
    synthetic_id = f"selection:{selected_hash.rsplit(':', 1)[-1][:16]}"
    page = _payload_int(payload, "page")
    locator = _payload_text(payload, "locator") or (f"p. {page}" if page else "")
    return [
        {
            "segment_id": _payload_text(payload, "segment_id") or synthetic_id,
            "source_id": payload.get("source_id", ""),
            "scope_type": "selection",
            "scope_ref": selected_hash,
            "page": page,
            "order": 0,
            "section_path": [],
            "kind": "selection",
            "text": selected_text,
            "text_hash": selected_hash,
            "locator": locator,
            "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
        }
    ]


def _selection_payload(payload: dict, segment_rows) -> dict[str, object]:
    selected_text = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
    if not selected_text:
        refs = set(_payload_list(payload, "segment_refs", "segment_ids", "segment_id"))
        selected_text = "\n\n".join(segment.text for segment in segment_rows if segment.segment_id in refs)
    page = _payload_int(payload, "page")
    locator = _payload_text(payload, "locator") or (f"p. {page}" if page else "")
    return {
        "source_id": _payload_text(payload, "source_id") or "",
        "page": page,
        "selected_text": selected_text,
        "selected_text_hash": _payload_text(payload, "selected_text_hash")
        or (text_hash(selected_text) if selected_text else ""),
        "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
        "segment_refs": _payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
        "locator": locator,
        "event_id": _payload_text(payload, "event_id"),
    }


def _update_or_delete_paper_annotation(source_id: str, payload: dict, *, delete: bool = False) -> str:
    annotation_id = _payload_text(payload, "annotation_id", "id")
    if not annotation_id:
        raise ValueError("Reader annotation update needs annotation_id.")
    annotations = load_paper_annotations(_pdir, source_id)
    updated = ""
    for ann in annotations:
        if ann.id != annotation_id:
            continue
        if delete:
            ann.status = "deleted"
        else:
            selected_text = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
            if selected_text:
                ann.selected_text = selected_text
                ann.selected_text_hash = _payload_text(payload, "selected_text_hash") or text_hash(selected_text)
            if "note" in payload:
                ann.note = str(payload.get("note") or "").strip()
            color = _payload_text(payload, "color")
            if color:
                ann.color = color
            locator = _payload_text(payload, "locator")
            if locator:
                ann.locator = locator
            page = _payload_int(payload, "page", ann.page)
            ann.page = page
            tags = _payload_list(payload, "tags")
            if tags:
                ann.tags = tags
            segment_refs = _payload_list(payload, "segment_refs", "segment_ids", "segment_id")
            if segment_refs:
                ann.segment_refs = segment_refs
            if isinstance(payload.get("rects"), list):
                ann.rects = payload["rects"]
        ann.updated = datetime.now().astimezone().isoformat(timespec="seconds")
        updated = ann.id
        break
    if not updated:
        raise ValueError(f"Unknown paper annotation: {annotation_id}")
    save_paper_annotations(_pdir, source_id, annotations)
    return updated


def _private_source_refs_for_citations(citation_ids: list[str]) -> list[str]:
    source_map = load_research_sources(selected).by_id()
    citations = {
        citation.id: citation
        for citation in load_research_citations(_pdir)
    }
    selected_citations = [
        citations[ref]
        for ref in citation_ids
        if ref in citations
    ] if citation_ids else list(citations.values())
    refs = [
        citation.source_id
        for citation in selected_citations
        if citation.source_id
        and source_map.get(citation.source_id) is not None
        and source_map[citation.source_id].visibility == "private"
    ]
    return _unique_text(refs)


def _context_segments(payload: dict, segment_rows, *, limit: int = 30) -> list[dict[str, object]]:
    picked = _selection_segments(payload, segment_rows)
    if picked:
        return picked
    return [segment.to_dict() for segment in segment_rows[:limit]]


def _selection_text(payload: dict, segment_rows) -> str:
    text = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
    if text:
        return text
    refs = {
        row.get("segment_id")
        for row in _selection_segments(payload, segment_rows)
        if row.get("segment_id")
    }
    if not refs:
        return ""
    return "\n\n".join(segment.text for segment in segment_rows if segment.segment_id in refs)


def _store_reader_ai_result(source_id: str, action: str, result) -> None:
    st.session_state[_reader_key(source_id, "ai_result")] = {
        "action": action,
        "structured": result.structured or {},
        "warnings": list(result.warnings),
    }


def _render_reader_ai_result(source_id: str) -> None:
    result = st.session_state.get(_reader_key(source_id, "ai_result"))
    if not isinstance(result, dict):
        return
    with st.expander(_l("reader_ai_result", "Reader AI result"), expanded=False):
        st.caption(str(result.get("action") or "AI"))
        for warning in result.get("warnings") or []:
            st.warning(str(warning))
        st.code(
            yaml.dump(result.get("structured") or {}, allow_unicode=True, sort_keys=False),
            language="yaml",
        )


def _render_reader_translation_summary(source_id: str) -> None:
    summary = st.session_state.get(_reader_key(source_id, "translation_summary"))
    if not isinstance(summary, dict):
        return
    with st.expander(_l("translation_summary", "Translation summary"), expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(_l("translated", "Translated"), summary.get("translated", 0))
        c2.metric(_l("missing", "Missing"), summary.get("missing", 0))
        c3.metric(_l("stale", "Stale"), summary.get("stale", 0))
        c4.metric(_l("failed", "Failed"), summary.get("failed", 0))
        if summary.get("warnings"):
            for warning in summary.get("warnings") or []:
                st.warning(str(warning))


def _handle_reader_component_event(
    source_id: str,
    event: object,
    *,
    segment_rows,
    annotation_rows,
    chunk_rows,
) -> bool:
    if not isinstance(event, dict):
        return False
    action = str(event.get("action") or event.get("type") or "").strip()
    if not action:
        return False
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    payload_source = str(payload.get("source_id") or event.get("source_id") or source_id).strip()
    if payload_source and payload_source != source_id:
        st.warning(f"Ignored reader event for {payload_source}; current source is {source_id}.")
        return True

    identity = _reader_event_identity(event)
    last_key = _reader_key(source_id, "last_event")
    if st.session_state.get(last_key) == identity:
        return True
    st.session_state[last_key] = identity

    try:
        if action == "selection_created":
            st.session_state[_reader_key(source_id, "selection")] = _selection_payload(payload, segment_rows)
            return True

        if action == "page_changed":
            page = _payload_int(payload, "page", 1)
            st.session_state[_reader_key(source_id, "page")] = max(1, page)
            return True

        if action == SAVE_PROGRESS:
            page = _payload_int(payload, "page", _payload_int(payload, "primary_page", 1))
            st.session_state[_reader_key(source_id, "page")] = max(1, page)
            _save_reader_progress(source_id, max(1, page))
            st.success(ui["saved"])
            return True

        if action == READER_STATE_CHANGED:
            page = _payload_int(payload, "page", _payload_int(payload, "primary_page", 1))
            visible = clean_page_list(payload.get("visible_pages"))
            st.session_state[_reader_key(source_id, "page")] = max(1, page)
            st.session_state[_reader_key(source_id, "visible_pages")] = visible
            _reader_requested_pages(source_id).update(visible or [max(1, page)])
            _save_reader_state(source_id, payload)
            return True

        if action == "viewport_changed":
            page = _payload_int(payload, "primary_page", _payload_int(payload, "page", 1))
            visible = clean_page_list(payload.get("visible_pages"))
            st.session_state[_reader_key(source_id, "page")] = max(1, page)
            st.session_state[_reader_key(source_id, "visible_pages")] = visible
            return True

        if action in {REQUEST_READER_CONTEXT, REQUEST_PAGE_PREVIEWS}:
            pages = clean_page_list(payload.get("pages") or payload.get("visible_pages"))
            if not pages:
                page = _payload_int(payload, "page", 1)
                pages = [max(1, page)]
            _reader_requested_pages(source_id).update(pages)
            st.session_state[_reader_key(source_id, "preview_page")] = pages[0]
            return True

        if action == REQUEST_PAGE_PREVIEW:
            page = _payload_int(payload, "page", 1)
            st.session_state[_reader_key(source_id, "preview_page")] = max(1, page)
            _reader_requested_pages(source_id).add(max(1, page))
            return True

        if action == "generate_review_card":
            source = load_research_sources(selected).by_id().get(source_id)
            result = generate_paper_review_card(
                selected,
                source_id,
                source=source.to_dict() if source is not None else {"id": source_id},
                segments=[row.to_dict() for row in segment_rows],
                chunks=[row.to_dict() for row in chunk_rows],
                annotations=[row.to_dict() for row in annotation_rows],
                require_review=False,
            )
            _store_reader_ai_result(source_id, action, result)
            if isinstance(result.structured, dict):
                save_paper_analysis(_pdir, source_id, result.structured)
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
                _set_reader_action_status(source_id, action, "done", ui["saved"])
            for warning in result.warnings:
                st.warning(str(warning))
            if result.warnings and not isinstance(result.structured, dict):
                _set_reader_action_status(source_id, action, "error", str(result.warnings[0]))
            return True

        if action == CODEX_DEEP_READ:
            ctx = ReaderActionContext(
                profile_name=selected,
                profile_path=_pdir,
                user_id=getattr(user, "id", "local"),
                source_id=source_id,
            )
            result = handle_reader_action(ctx, action, payload)
            st.session_state[_reader_key(source_id, "ai_result")] = {
                "action": action,
                "structured": result.data.get("structured") if isinstance(result.data, dict) else {},
                "warnings": list(result.warnings),
            }
            if result.ok:
                stash_git_backup_results()
                clear_web_cache()
                st.success(result.message or ui["saved"])
                _set_reader_action_status(source_id, action, "done", result.message or ui["saved"])
            else:
                st.warning(result.message or "Deep read did not return a candidate.")
                _set_reader_action_status(source_id, action, "error", result.message or "Deep read failed")
            for warning in result.warnings:
                st.warning(str(warning))
            return True

        if action in {ANNOTATION_CREATE, "create_annotation"}:
            ann = create_paper_annotation(
                _pdir,
                source_id,
                _payload_text(payload, "selected_text", "selection_text", "text", "quote"),
                kind=_payload_text(payload, "kind") or "highlight",
                page=_payload_int(payload, "page"),
                locator=_payload_text(payload, "locator"),
                note=_payload_text(payload, "note"),
                color=_payload_text(payload, "color") or "yellow",
                tags=_payload_list(payload, "tags"),
                segment_refs=_payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
                rects=payload.get("rects") if isinstance(payload.get("rects"), list) else [],
            )
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["created"].format(id=ann.id))
            st.session_state[_reader_key(source_id, "focus_annotation_id")] = ann.id
            return True

        if action == ANNOTATION_UPDATE:
            annotation_id = _update_or_delete_paper_annotation(source_id, payload)
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["saved"])
            st.session_state[_reader_key(source_id, "focus_annotation_id")] = annotation_id
            return True

        if action == ANNOTATION_DELETE:
            annotation_id = _update_or_delete_paper_annotation(source_id, payload, delete=True)
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["saved"])
            st.session_state[_reader_key(source_id, "focus_annotation_id")] = annotation_id
            return True

        if action in {CREATE_CHUNK_FROM_SELECTION, "create_chunk"}:
            text = _selection_text(payload, segment_rows)
            chunk = create_chunk(
                _pdir,
                source_id,
                text,
                kind=_payload_text(payload, "kind") or "excerpt",
                title=_payload_text(payload, "title"),
                locator=_payload_text(payload, "locator"),
                metadata={
                    "page": _payload_int(payload, "page"),
                    "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
                    "segment_refs": _payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
                    "annotation_id": _payload_text(payload, "annotation_id"),
                    "source": "reader_component",
                },
            )
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["created"].format(id=chunk.id))
            st.session_state[_reader_key(source_id, "focus_chunk_id")] = chunk.id
            return True

        if action == TRANSLATE_FULL_PAPER:
            summary = translate_full_paper(
                _pdir,
                source_id,
                target_lang=_payload_text(payload, "target_lang", "language") or "zh",
                mode=_payload_text(payload, "mode") or "missing_or_stale",
                scope_strategy=_payload_text(payload, "scope_strategy") or "auto",
                ai_profile=selected,
                require_review=False,
            )
            st.session_state[_reader_key(source_id, "translation_summary")] = summary
            stash_git_backup_results()
            clear_web_cache()
            st.success(
                _l("translation_full_saved", "Full-paper translation updated: {count} row(s).").format(
                    count=summary.get("updated", 0)
                )
            )
            _set_reader_action_status(
                source_id,
                action,
                "done",
                _l("translation_full_saved", "Full-paper translation updated: {count} row(s).").format(
                    count=summary.get("updated", 0)
                ),
            )
            for warning in summary.get("warnings") or []:
                st.warning(str(warning))
            return True

        if action in {TRANSLATE_VISIBLE_PAGES, RETRY_TRANSLATION_SCOPE}:
            ctx = ReaderActionContext(
                profile_name=selected,
                profile_path=_pdir,
                user_id=getattr(user, "id", "local"),
                source_id=source_id,
            )
            result = handle_reader_action(ctx, action, payload)
            summary = result.data.get("summary") if isinstance(result.data, dict) else {}
            if not isinstance(summary, dict):
                summary = {}
            saved = int(summary.get("saved") or 0)
            if result.ok and saved:
                stash_git_backup_results()
                clear_web_cache()
                message = _l("visible_pages_translation_saved", "Visible pages translated: saved {count} row(s).").format(
                    count=saved
                )
                st.success(message)
                _set_reader_action_status(source_id, action, "done", message)
            elif result.ok:
                message = result.message or _l(
                    "visible_pages_translation_saved_none",
                    "No visible-page translations were saved. AI returned {count} valid row(s).",
                ).format(count=summary.get("ai_rows", 0))
                st.info(message)
                _set_reader_action_status(source_id, action, "done", message)
            else:
                message = result.message or _l(
                    "visible_page_translation_no_text",
                    "No extracted text is available for the visible page yet. Try Extract pages in Reader diagnostics.",
                )
                st.warning(message)
                _set_reader_action_status(source_id, action, "error", message)
            st.caption(
                " · ".join(
                    [
                        f"pages={','.join(str(page) for page in summary.get('requested_pages', []) or []) or '-'}",
                        f"scope={summary.get('scope') or '-'}",
                        f"segments={summary.get('segments_selected', 0)}",
                        f"ai_rows={summary.get('ai_rows', 0)}",
                        f"saved={summary.get('saved', 0)}",
                        f"skipped={summary.get('skipped', 0)}",
                    ]
                )
            )
            for warning in result.warnings:
                st.warning(str(warning))
            return True

        if action in {TRANSLATE_SELECTION, "translate_segment"}:
            selected_text = _selection_text(payload, segment_rows)
            target_lang = _payload_text(payload, "target_lang", "language") or "zh"
            translation_payload = dict(payload)
            if action == "translate_selection" and selected_text:
                for key in ("segment_refs", "segment_ids", "segment_id", "scope_refs", "scope_ref"):
                    translation_payload.pop(key, None)
            segment_refs = set(_payload_list(translation_payload, "segment_refs", "segment_ids", "segment_id"))
            segments = _selection_segments(translation_payload, segment_rows)
            if not segments:
                raise ValueError("Reader translation needs selected text or segment refs.")
            result = translate_paper_segments(
                selected,
                source_id,
                segments,
                target_lang=target_lang,
                require_review=False,
            )
            _store_reader_ai_result(source_id, action, result)
            translations = []
            if isinstance(result.structured, dict):
                translations = [
                    normalize_translation_row(row, source_id=source_id, target_lang=target_lang)
                    for row in result.structured.get("translations", [])
                    if isinstance(row, dict)
                ]
            if segment_refs:
                segment_ids = {segment.segment_id for segment in segment_rows}
                savable = [
                    {
                        **row,
                        "scope_type": "segment",
                        "scope_ref": str(row.get("segment_id") or row.get("scope_ref") or ""),
                    }
                    for row in translations
                    if str(row.get("segment_id") or row.get("scope_ref") or "") in segment_ids
                ]
            else:
                selected_hash = _payload_text(payload, "selected_text_hash", "text_hash", "source_hash")
                if not selected_hash and selected_text:
                    selected_hash = text_hash(selected_text)
                synthetic_ids = {
                    str(segment.get("segment_id") or "")
                    for segment in segments
                    if isinstance(segment, dict)
                }
                savable = []
                for row in translations:
                    row_ref = str(row.get("segment_id") or row.get("scope_ref") or "")
                    if synthetic_ids and row_ref and row_ref not in synthetic_ids:
                        continue
                    savable.append(
                        {
                            **row,
                            "scope_type": "selection",
                            "scope_ref": selected_hash,
                            "segment_id": "",
                            "source_hash": selected_hash,
                            "source_text": selected_text,
                            "target_lang": target_lang,
                        }
                    )
            if savable:
                upsert_paper_translations(_pdir, source_id, savable)
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
            for warning in result.warnings:
                st.warning(str(warning))
            return True

        if action == CREATE_CITATION:
            selected_text = _selection_text(payload, segment_rows)
            chunk_id = _payload_text(payload, "chunk_id", "chunk_ref")
            if not chunk_id and selected_text:
                chunk = create_chunk(
                    _pdir,
                    source_id,
                    selected_text,
                    kind="excerpt",
                    locator=_payload_text(payload, "locator"),
                    metadata={
                        "page": _payload_int(payload, "page"),
                        "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
                        "segment_refs": _payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
                        "annotation_id": _payload_text(payload, "annotation_id"),
                        "source": "reader_component",
                    },
                )
                chunk_id = chunk.id
            claim_id = _payload_text(payload, "claim_id", "research_claim_id")
            if not claim_id:
                claim_text = _payload_text(payload, "claim_text", "text") or selected_text
                if not claim_text:
                    raise ValueError("Reader citation needs a claim id, selected text, or claim text.")
                claim = upsert_research_claim(
                    _pdir,
                    claim_text,
                    status="draft",
                    type=_payload_text(payload, "claim_type") or "finding",
                    source_refs=[source_id],
                    chunk_refs=[chunk_id] if chunk_id else [],
                    confidence="medium",
                    rationale=_l("reader_citation_candidate", "Created from Reader selection; review before promotion."),
                    generated_by="reader_component",
                )
                claim_id = claim.id
            citation = create_citation(
                _pdir,
                claim_id,
                source_id=source_id,
                chunk_id=chunk_id,
                locator=_payload_text(payload, "locator"),
                quote=_payload_text(payload, "quote", "selected_text", "selection_text", "text"),
                bibliography=_payload_text(payload, "bibliography"),
                note=_payload_text(payload, "note"),
            )
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["created"].format(id=citation.id))
            return True

        if action == EXPLAIN_SELECTION:
            selected_text = _selection_text(payload, segment_rows)
            if not selected_text:
                raise ValueError("Reader explanation needs selected text or segment refs.")
            result = explain_paper_selection(
                selected,
                source_id,
                selected_text,
                payload={
                    "page": _payload_int(payload, "page"),
                    "locator": _payload_text(payload, "locator"),
                    "segments": _context_segments(payload, segment_rows, limit=8),
                    "annotations": [row.to_dict() for row in annotation_rows[:20]],
                },
            )
            _store_reader_ai_result(source_id, action, result)
            for warning in result.warnings:
                st.warning(str(warning))
            return True

        if action == ASK_PAPER:
            question = _payload_text(payload, "question", "prompt", "text")
            if not question:
                raise ValueError("Reader question cannot be blank.")
            result = answer_paper_question(
                selected,
                source_id,
                question,
                payload={
                    "segments": _context_segments(payload, segment_rows, limit=30),
                    "annotations": [row.to_dict() for row in annotation_rows[:30]],
                    "chunks": [row.to_dict() for row in chunk_rows[:30]],
                },
            )
            _store_reader_ai_result(source_id, action, result)
            for warning in result.warnings:
                st.warning(str(warning))
            return True

        if action == "jump_to_annotation":
            annotation_id = _payload_text(payload, "annotation_id", "id")
            if not annotation_id:
                raise ValueError("Reader jump needs annotation_id.")
            st.session_state[_reader_key(source_id, "focus_annotation_id")] = annotation_id
            return True

        if action == "jump_to_chunk":
            chunk_id = _payload_text(payload, "chunk_id", "id")
            if not chunk_id:
                raise ValueError("Reader jump needs chunk_id.")
            st.session_state[_reader_key(source_id, "focus_chunk_id")] = chunk_id
            return True

        st.warning(f"Unsupported reader action: {action or event}")
        return True
    except Exception as exc:
        st.error(str(exc))
        return True


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
    artifact_status: dict[str, object] = {}
    existing_pages = load_paper_pages(_pdir, source_id)
    existing_segments = load_paper_segments(_pdir, source_id)
    if source.metadata.get("pdf_asset_ref") and (not existing_pages or not existing_segments):
        st.info(
            _l(
                "reader_artifacts_missing",
                "Reader text artifacts are not extracted yet. The PDF can open now; extract when you need search, translation, and segment-aware notes.",
            )
        )
        if st.button(_l("extract_reader_artifacts", "Extract reader text"), type="primary"):
            try:
                artifact_status = ensure_paper_reading_artifacts(_pdir, source_id)
                inbox = load_research_sources(selected)
                source = inbox.by_id().get(source_id) or source
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
                st.rerun()
            except Exception as exc:
                st.warning(_l("reading_artifacts_failed", "Reading artifacts could not be prepared: {error}").format(error=exc))
        if not existing_pages:
            artifact_status = {
                "ready": False,
                "status": "missing",
                "pages": 0,
                "segments": len(existing_segments),
            }
    status_bits = [
        f"PDF: {'yes' if source.metadata.get('pdf_asset_ref') else 'missing'}",
        f"{_l('pages', 'Pages')}: {source.metadata.get('page_count', '') or '?'}",
        f"{_l('annotations', 'Annotations')}: {len(load_paper_annotations(_pdir, source_id))}",
        f"{_l('segments', 'Segments')}: {len(load_paper_segments(_pdir, source_id))}",
        f"{_l('structured_extraction', 'Structure')}: "
        f"{source.metadata.get('reading_artifacts_status') or source.metadata.get('structure_backend', '') or _l('missing', 'missing')}",
    ]
    st.markdown(f"**{source.title}**")
    st.caption(" · ".join(status_bits))
    st.caption(
        _l(
            "reader_caption",
            "PDF Reader is the primary surface when a PDF asset is attached; diagnostics and text fallback stay out of the reading path.",
        )
    )
    if artifact_status.get("warnings"):
        with st.expander(_l("reader_artifact_warnings", "Reader preparation warnings"), expanded=False):
            for warning in artifact_status.get("warnings") or []:
                st.warning(str(warning))

    with st.expander(_l("reader_diagnostics", "Reader diagnostics"), expanded=False):
        _render_grobid_status_block(source)
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
            if st.button(_l("extract_segments", "Extract segments"), disabled=not source.metadata.get("pdf_asset_ref")):
                try:
                    extract_paper_segments(_pdir, source_id)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with actions[2]:
            if st.button(
                _l("run_structured_extraction", "Run structured extraction"),
                disabled=not source.metadata.get("pdf_asset_ref"),
            ):
                try:
                    extract_paper_segments(_pdir, source_id, backend="grobid")
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with actions[3]:
            if st.button(_l("auto_chunk", "Auto chunk")):
                try:
                    chunks = auto_chunk_paper(_pdir, source_id)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(_l("created_chunks", "Created chunks: {count}").format(count=len(chunks)))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    if source.metadata.get("pdf_asset_ref"):
        try:
            token = mint_reader_token(user.id, selected, source_id)
        except Exception as exc:
            st.error(str(exc))
            return
        base = os.getenv("NBLANE_READER_API_BASE", "").strip().rstrip("/")
        encoded_source = quote(source_id, safe="")
        encoded_token = quote(token, safe="")
        iframe_src = f"{base}/reader/view/{encoded_source}?token={encoded_token}" if base else f"/reader/view/{encoded_source}?token={encoded_token}"
        st.components.v1.iframe(iframe_src, height=1200, scrolling=False)
        return
    st.info(_l("pdf_missing", "No PDF asset is attached; using text-mode Reader."))

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
        counts = _translation_counts_for_segments(source_id)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(_l("translated", "Translated"), counts["translated"])
        c2.metric(_l("missing", "Missing"), counts["missing"])
        c3.metric(_l("stale", "Stale"), counts["stale"])
        c4.metric(_l("failed", "Failed"), counts["failed"])
        if st.button(
            _l("translate_missing_stale", "Translate missing/stale"),
            disabled=not segment_rows or (counts["missing"] + counts["stale"] == 0),
        ):
            try:
                summary = translate_full_paper(
                    _pdir,
                    source_id,
                    target_lang="zh",
                    mode="missing_or_stale",
                    ai_profile=selected,
                    require_review=False,
                )
                st.session_state[_reader_key(source_id, "translation_summary")] = summary
                stash_git_backup_results()
                clear_web_cache()
                st.success(
                    _l("translation_full_saved", "Full-paper translation updated: {count} row(s).").format(
                        count=summary.get("updated", 0)
                    )
                )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
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
                    upsert_paper_translations(
                        _pdir,
                        source_id,
                        [
                            normalize_translation_row(row, source_id=source_id, target_lang="zh")
                            for row in list(candidate.get("translations") or [])
                            if isinstance(row, dict)
                        ],
                    )
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
    chunks = load_chunks(_pdir)
    source_chunks = [chunk for chunk in chunks if chunk.source_id == source_id]
    chunk_ids = [chunk.id for chunk in chunks]
    claim_rows = load_research_claims(_pdir)
    claim_ids = [claim.id for claim in claim_rows]
    citation_rows = load_research_citations(_pdir)
    chunk_tab, claim_tab, citation_tab = st.tabs(
        [
            _l("chunks", "Chunks"),
            ui["research_claims"],
            ui["research_citations"],
        ]
    )

    with chunk_tab:
        with st.expander(ui["create_chunk"], expanded=not source_chunks):
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
        if source_chunks:
            for chunk in source_chunks:
                related_claims = [claim.id for claim in claim_rows if chunk.id in claim.chunk_refs]
                related_citations = [citation.id for citation in citation_rows if citation.chunk_id == chunk.id]
                with st.container(border=True):
                    st.markdown(f"**{chunk.title or chunk.id}**")
                    st.caption(f"{chunk.kind} · {chunk.locator or source_id}")
                    if related_claims or related_citations:
                        st.caption(
                            " · ".join(
                                [
                                    f"{ui['research_claims']}: {', '.join(related_claims) or '0'}",
                                    f"{ui['research_citations']}: {', '.join(related_citations) or '0'}",
                                ]
                            )
                        )
                    st.write(chunk.text)
                    if chunk.metadata:
                        with st.expander(_l("metadata", "Metadata"), expanded=False):
                            st.code(yaml.dump(chunk.metadata, allow_unicode=True, sort_keys=False), language="yaml")
        else:
            st.caption(ui["chunks_empty"])

    with claim_tab:
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
        source_claims = [
            claim
            for claim in claim_rows
            if source_id in claim.source_refs
            or any(chunk.id in claim.chunk_refs for chunk in source_chunks)
        ]
        if source_claims:
            for claim in source_claims:
                with st.container(border=True):
                    st.markdown(f"**{claim.id}**")
                    st.caption(
                        " · ".join(
                            [
                                claim.status,
                                claim.type,
                                f"confidence={claim.confidence}",
                            ]
                        )
                    )
                    st.write(claim.text)
                    st.caption(
                        " · ".join(
                            [
                                f"sources: {', '.join(claim.source_refs) or '0'}",
                                f"chunks: {', '.join(claim.chunk_refs) or '0'}",
                                f"citations: {', '.join(claim.citation_refs) or '0'}",
                            ]
                        )
                    )
                    for warning in claim.warnings:
                        st.warning(str(warning))
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

    with citation_tab:
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
        source_citations = [
            citation
            for citation in citation_rows
            if citation.source_id == source_id
            or any(chunk.id == citation.chunk_id for chunk in source_chunks)
        ]
        citation_warnings = paper_citation_diagnostics(_pdir, source_id)
        for warning in citation_warnings:
            st.warning(str(warning))
        if source_citations:
            chunk_map = {chunk.id: chunk for chunk in chunks}
            for citation in source_citations:
                chunk = chunk_map.get(citation.chunk_id)
                quote_ok = ""
                if citation.quote and chunk is not None:
                    quote_ok = "quote ok" if citation.quote.strip().casefold() in chunk.text.casefold() else "quote warning"
                with st.container(border=True):
                    st.markdown(f"**{citation.id}**")
                    st.caption(
                        " · ".join(
                            [
                                f"claim={citation.claim_id}",
                                f"source={citation.source_id or source_id}",
                                f"chunk={citation.chunk_id or 'none'}",
                                quote_ok,
                            ]
                        )
                    )
                    if citation.quote:
                        st.write(citation.quote)
                    if citation.locator or citation.bibliography:
                        st.caption(f"{citation.locator} · {citation.bibliography}")
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
        private_refs = _private_source_refs_for_citations(citation_refs)
        if private_refs:
            st.warning(
                _l(
                    "private_export_warning",
                    "This export includes private paper sources; keep it private or remove them before public use: {refs}",
                ).format(refs=", ".join(private_refs))
            )
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
            save_private_export = not private_refs or st.checkbox(
                _l("confirm_private_export_save", "Confirm saving export with private sources"),
                value=False,
            )
            if st.button(_l("save_export", "Save export"), disabled=not save_private_export):
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
