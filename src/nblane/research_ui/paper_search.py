"""Paper search panel and result cards."""
from __future__ import annotations

import html
from urllib.parse import urlparse

import streamlit as st
import yaml

from nblane.core.ai import search_papers_codex
from nblane.core.research_papers import (
    PAPER_SEARCH_PROVIDERS,
    PaperSearchResult,
    _paper_search_imported_refs,
    _paper_search_library_tree_hint,
    _paper_search_result_has_downloadable_pdf,
    add_research_source,
    create_paper_library_node,
    import_paper_pdf,
    import_paper_search_results,
    import_paper_url,
    mark_imported_paper_results,
    save_research_sources,
    search_papers,
)
from nblane.core.research_sources import (
    SOURCE_STATUSES,
    add_research_source as _add_research_source,
    save_research_sources as _save_research_sources,
)
from nblane.web_cache import clear_web_cache, load_research_sources
from nblane.web_shared import (
    refresh_file_snapshots,
    stash_git_backup_results,
)

from .context import ResearchContext
from ._helpers import (
    _cached_paper_rows,
    _l,
    _node_options,
    _node_select_index,
    _paper_library_key,
    _paper_sources,
    _short_text,
    _normalized_title,
    _tags,
    _text_lines,
    _unique_text,
)


def _marked_search_results(ctx, results: list[object]) -> list[PaperSearchResult]:
    _pdir = ctx.pdir
    return mark_imported_paper_results(_pdir, results)


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
        warnings.append("No downloadable PDF URL; import metadata first or upload a local PDF.")

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


def _render_search_result_details(ctx, results: list[PaperSearchResult], inbox) -> None:
    ui = ctx.ui
    st.markdown(f"**{_l(ui, 'result_details', 'Result details')}**")
    for result in results:
        title = result.title or result.candidate_id
        with st.expander(f"{title} · {result.year or 'n.d.'}", expanded=False):
            warnings = _search_result_warnings(result, inbox)
            for warning in warnings:
                st.warning(warning)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{_l(ui, 'metadata', 'Metadata')}**")
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
                st.markdown(f"**{_l(ui, 'identifiers', 'Identifiers')}**")
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
                st.markdown(f"**{_l(ui, 'import_hints', 'Import hints')}**")
                st.write(
                    {
                        "imported": result.imported_source_id,
                        "oa_pdf": bool(result.open_access_pdf),
                        "tags": result.tags,
                        "fields_of_study": result.fields_of_study,
                        "suggested_library_nodes": result.suggested_library_nodes,
                    }
                )
                st.markdown(f"**{_l(ui, 'link_check', 'Link check')}**")
                st.code(
                    yaml.dump(
                        result.link_check or {"status": "needs check"},
                        allow_unicode=True,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            if result.why_relevant:
                st.markdown(f"**{_l(ui, 'relevance', 'Relevance')}**")
                st.caption(result.why_relevant)
            if result.abstract:
                st.markdown(f"**{_l(ui, 'abstract', 'Abstract')}**")
                st.write(result.abstract)


def _search_result_meta_line(ctx, result: PaperSearchResult) -> str:
    ui = ctx.ui
    parts = []
    if result.year:
        parts.append(result.year)
    if result.venue:
        parts.append(result.venue)
    if result.authors:
        parts.append(_short_text(", ".join(result.authors[:4]), 140))
    if result.provider_refs:
        parts.append(_short_text(", ".join(result.provider_refs), 120))
    if result.citation_count is not None:
        parts.append(f"{_l(ui, 'citations', 'Citations')}: {result.citation_count}")
    return " · ".join(parts)


def _search_result_external_links(ctx, result: PaperSearchResult) -> list[tuple[str, str]]:
    ui = ctx.ui
    links: list[tuple[str, str]] = []
    if result.canonical_url:
        links.append((_l(ui, "paper_page", "Paper page"), result.canonical_url))
    if result.pdf_url:
        links.append(("PDF", result.pdf_url))
    if result.doi:
        links.append(("DOI", f"https://doi.org/{result.doi}"))
    if result.arxiv_id:
        links.append(("arXiv", f"https://arxiv.org/abs/{result.arxiv_id}"))
    return links


def _search_result_link_html(title: str, url: str, *, source: str = "", summary: str = "") -> str:
    parsed = urlparse(str(url or ""))
    if parsed.scheme not in {"http", "https"}:
        return ""
    clean_title = html.escape(str(title or url))
    clean_url = html.escape(str(url or ""))
    clean_source = html.escape(str(source or ""))
    clean_summary = html.escape(_short_text(summary, 180))
    source_part = f'<span style="color:#6b7280;"> · {clean_source}</span>' if clean_source else ""
    summary_part = f'<div style="color:#4b5563;font-size:.86rem;line-height:1.4;margin-top:2px;">{clean_summary}</div>' if clean_summary else ""
    return (
        '<div style="margin:4px 0;">'
        f'<a href="{clean_url}" target="_blank" rel="noreferrer">{clean_title}</a>'
        f"{source_part}{summary_part}</div>"
    )


def _render_search_result_cards(ctx, 
    results: list[PaperSearchResult],
    inbox,
    *,
    mode: str,
) -> list[str]:
    ui = ctx.ui
    selected_ids: list[str] = []
    st.markdown(f"**{_l(ui, 'search_triage_results', 'Triage candidates')}**")
    st.caption(
        _l(ui, 
            "search_triage_hint",
            "Read the abstract, AI overview, and explainer links first; select only the papers you want to import.",
        )
    )
    for index, result in enumerate(results, start=1):
        warnings = _search_result_warnings(result, inbox)
        imported = bool(result.imported_source_id)
        key = _search_state_key(ctx, f"select:{result.candidate_id}")
        with st.container(border=True):
            select_col, body_col = st.columns([0.18, 1.82], gap="medium")
            with select_col:
                picked = st.checkbox(
                    _l(ui, "select_to_import_short", "Import"),
                    key=key,
                    disabled=imported,
                )
                if picked and not imported:
                    selected_ids.append(result.candidate_id)
            with body_col:
                st.markdown(f"**{index}. {result.title or result.candidate_id}**")
                meta_line = _search_result_meta_line(ctx, result)
                if meta_line:
                    st.caption(meta_line)
                badge_bits = []
                if result.open_access_pdf:
                    badge_bits.append("PDF ready")
                if imported:
                    badge_bits.append(f"Imported: {result.imported_source_id}")
                if result.tags:
                    badge_bits.extend(result.tags[:4])
                if result.fields_of_study:
                    badge_bits.extend(result.fields_of_study[:3])
                if badge_bits:
                    st.caption(" · ".join(str(item) for item in badge_bits if str(item).strip()))

                if result.ai_summary:
                    st.markdown(f"**{_l(ui, 'ai_summary', 'AI overview')}**")
                    st.write(result.ai_summary)
                if result.why_relevant:
                    st.markdown(f"**{_l(ui, 'why_relevant', 'Why it matters')}**")
                    st.write(result.why_relevant)
                if result.abstract:
                    st.markdown(f"**{_l(ui, 'abstract', 'Abstract')}**")
                    st.write(_short_text(result.abstract, 900))
                    if len(result.abstract) > 900:
                        with st.expander(_l(ui, "full_abstract", "Full abstract"), expanded=False):
                            st.write(result.abstract)

                if result.explanation_links:
                    st.markdown(f"**{_l(ui, 'explainer_links', 'Explainer links')}**")
                    rendered_links = [
                        _search_result_link_html(
                            str(link.get("title") or link.get("url") or ""),
                            str(link.get("url") or ""),
                            source=str(link.get("source") or ""),
                            summary=str(link.get("summary") or ""),
                        )
                        for link in result.explanation_links
                        if str(link.get("url") or "").strip()
                    ]
                    st.markdown(
                        "\n".join(item for item in rendered_links if item),
                        unsafe_allow_html=True,
                    )
                elif mode == "Codex Search":
                    st.caption(_l(ui, "explainer_links_empty", "No verified explainer links returned for this candidate."))

                external_links = _search_result_external_links(ctx, result)
                if external_links:
                    link_cols = st.columns(min(4, len(external_links)))
                    for offset, (title, url) in enumerate(external_links[:4]):
                        with link_cols[offset]:
                            try:
                                st.link_button(title, url, use_container_width=True)
                            except Exception:
                                st.caption(f"{title}: {url}")
                if warnings:
                    with st.expander(_l(ui, "search_result_warnings", "Warnings and raw metadata"), expanded=False):
                        for warning in warnings:
                            st.warning(warning)
                        st.code(
                            yaml.dump(
                                result.to_dict(),
                                allow_unicode=True,
                                default_flow_style=False,
                                sort_keys=False,
                            ),
                            language="yaml",
                        )
    return selected_ids


def _result_rows(ctx, results: list[object]) -> list[dict[str, object]]:
    selected = ctx.selected
    marked = _marked_search_results(ctx, results)
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
            "abstract": _short_text(row.abstract, 260),
            "ai_summary": _short_text(row.ai_summary, 220),
            "relevance": row.why_relevant,
            "explainers": len(row.explanation_links),
            "tags": ", ".join(row.tags),
        }
        for row in marked
    ]


def _search_state_key(ctx, name: str) -> str:
    selected = ctx.selected
    return f"paper_search:{selected}:{name}"


def _focus_library_import(ctx, imported_ids: list[str], node_ref: str) -> None:
    clean_node = str(node_ref or "").strip()
    st.session_state[_paper_library_key(ctx, "view")] = "all" if clean_node else "unsorted"
    st.session_state[_paper_library_key(ctx, "node")] = clean_node
    if imported_ids:
        st.session_state[_paper_library_key(ctx, "detail")] = imported_ids[0]
        st.session_state[_search_state_key(ctx, "results")] = []


def _render_paper_search(ctx, inbox, *, embedded: bool = False) -> None:
    selected = ctx.selected
    _pdir = ctx.pdir
    ui = ctx.ui
    _sources_path = ctx.sources_path
    node_options = _node_options(ctx)
    current_node = str(st.session_state.get(_paper_library_key(ctx, "node"), "") or "")
    default_location = node_options.get(current_node, _l(ui, "unsorted_inbox", "Unsorted Inbox"))
    if not embedded:
        st.subheader(_l(ui, "paper_search", "Paper Search"))
    st.caption(
        _l(ui, 
            "paper_search_caption",
            "Search results stay preview-only, show abstracts first, and import into the selected Library location only after confirmation.",
        )
    )
    if embedded:
        st.caption(
            _l(ui, "paper_search_library_default", "Default import location: {location}").format(
                location=default_location
            )
        )
    prepare_notice_key = f"paper_reader_prepare_notice:{selected}"
    prepare_notice = st.session_state.pop(prepare_notice_key, "")
    if prepare_notice:
        st.info(str(prepare_notice))
    mode = st.radio(
        _l(ui, "search_mode", "Search mode"),
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
            query = st.text_input(_l(ui, "query", "Query"), placeholder="VLA memory")
            if mode == "Provider Search":
                providers = st.multiselect(
                    _l(ui, "providers", "Providers"),
                    options=list(PAPER_SEARCH_PROVIDERS),
                    default=list(PAPER_SEARCH_PROVIDERS),
                )
            else:
                providers = []
                st.caption(
                    _l(ui, 
                        "codex_search_pdf_policy",
                        "Codex can use any source/provider; only candidates with a downloadable PDF URL are shown.",
                    )
                )
            c1, c2, c3 = st.columns(3)
            with c1:
                limit = st.number_input(_l(ui, "limit", "Limit"), min_value=1, max_value=50, value=10)
            with c2:
                year_from = st.text_input(_l(ui, "year_from", "Year from"))
            with c3:
                year_to = st.text_input(_l(ui, "year_to", "Year to"))
            only_pdf = st.checkbox(
                _l(ui, "has_open_access_pdf", "Has downloadable PDF"),
                value=mode == "Codex Search",
                disabled=mode == "Codex Search",
            )
            exclude_imported = st.checkbox(_l(ui, "exclude_imported", "Exclude already imported"), value=True)
            project_refs = st.text_area(ui["project_refs"], height=68)
            goal_refs = st.text_area(ui["goal_refs"], height=68)
            submitted = st.form_submit_button(_l(ui, "search_papers", "Search papers"), type="primary")
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
                        "triage_fields": [
                            "abstract",
                            "ai_summary",
                            "why_relevant",
                            "explanation_links",
                        ],
                        "explanation_link_sources": [
                            "Zhihu",
                            "Xiaohongshu",
                            "blog",
                            "video",
                            "project page",
                            "author page",
                        ],
                        "instructions": (
                            "Return paper candidates for coarse reading from any reputable source/provider. "
                            "Only include results with a direct downloadable PDF URL in pdf_url or open_access_pdf_url. "
                            "For each result, include abstract if available, a concise AI overview in the user's language, "
                            "why it matters for the query, and verified explainer links when available. Do not invent explainer links."
                        ),
                    },
                )
                raw = result.structured if isinstance(result.structured, dict) else {}
                candidates = []
                for row in raw.get("results", []):
                    item = PaperSearchResult.from_dict(row)
                    if item is None or not _paper_search_result_has_downloadable_pdf(item):
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
                            _l(ui, 
                                "codex_search_fallback",
                                "Codex returned no structured papers; using provider search fallback.",
                            )
                        )
                    candidates = [row.to_dict() for row in search_papers(query, tuple(providers or PAPER_SEARCH_PROVIDERS), int(limit), filters)]
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
            st.session_state[_search_state_key(ctx, "results")] = candidates
            st.rerun()

        results = list(st.session_state.get(_search_state_key(ctx, "results"), []) or [])
        if results:
            marked_results = _marked_search_results(ctx, results)
            result_dicts = [row.to_dict() for row in marked_results]
            selected_ids = _render_search_result_cards(ctx, marked_results, inbox, mode=mode)
            with st.expander(_l(ui, "compact_table", "Compact table"), expanded=False):
                st.dataframe(_result_rows(ctx, result_dicts), use_container_width=True, hide_index=True)
            if selected_ids:
                with st.expander(_l(ui, "selected_metadata_preview", "Selected metadata preview"), expanded=False):
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
                node_options = _node_options(ctx)
                default_node = str(st.session_state.get(_paper_library_key(ctx, "node"), "") or "")
                node_ref = st.selectbox(
                    _l(ui, "library_location", "Library location"),
                    options=list(node_options),
                    index=_node_select_index(node_options, default_node),
                    format_func=lambda ref: node_options.get(ref, ref),
                )
                child_collection = st.text_input(_l(ui, "new_child_collection", "New child collection"))
                tags = st.text_input(ui["tags"])
                visibility = st.selectbox(ui["visibility"], ["private", "public"], index=0)
                status = st.selectbox(ui["status"], SOURCE_STATUSES, index=SOURCE_STATUSES.index("inbox"))
                pdf_strategy = st.radio(
                    _l(ui, "pdf_strategy", "PDF strategy"),
                    [
                        _l(ui, "pdf_strategy_metadata_only", "Metadata only"),
                        _l(ui, "download_open_access_pdf", "Download open-access PDF"),
                        _l(ui, "pdf_strategy_upload_later", "Upload local PDF after import"),
                    ],
                    horizontal=True,
                    key=f"pdf_strategy:{selected}",
                )
                prepare_reader = st.checkbox(
                    _l(ui, "prepare_reader_after_import", "Prepare Reader text after import"),
                    value=True,
                    disabled=pdf_strategy != _l(ui, "download_open_access_pdf", "Download open-access PDF"),
                )
                confirmed = st.form_submit_button(_l(ui, "import_selected", "Import selected"), type="primary")
            selected_results = [row for row in marked_results if row.candidate_id in set(selected_ids)]
            if pdf_strategy == _l(ui, "download_open_access_pdf", "Download open-access PDF"):
                for row in selected_results:
                    if row.needs_link_check:
                        st.warning(f"{row.title}: needs link check before PDF download.")
                    if not row.open_access_pdf:
                        st.warning(f"{row.title}: no open-access PDF URL to download.")
            elif pdf_strategy == _l(ui, "pdf_strategy_upload_later", "Upload local PDF after import") and selected_ids:
                st.info(
                    _l(ui, 
                        "upload_pdf_after_import_hint",
                        "Import will create private inbox metadata; attach the local PDF from Upload PDF after import.",
                    )
                )
            if confirmed:
                try:
                    _accept_latest_sources_for_additive_write(ctx)
                    import_node_ref = node_ref
                    if selected_ids and str(child_collection or "").strip():
                        import_node_ref = create_paper_library_node(
                            _pdir,
                            child_collection,
                            parent_id=node_ref,
                        ).id
                    imported = import_paper_search_results(
                        _pdir,
                        result_dicts,
                        selected_ids,
                        {
                            "library_node_refs": [import_node_ref] if import_node_ref else [],
                            "tags": _tags(tags),
                            "visibility": visibility,
                            "status": status,
                            "goal_refs": _text_lines(goal_refs),
                            "project_refs": _text_lines(project_refs),
                            "download_pdf": pdf_strategy == _l(ui, "download_open_access_pdf", "Download open-access PDF"),
                        },
                    )
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    _focus_library_import(ctx, imported, import_node_ref)
                    st.success(_l(ui, "imported_papers", "Imported papers: {ids}").format(ids=", ".join(imported) or "0"))
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
                        pdf_strategy == _l(ui, "download_open_access_pdf", "Download open-access PDF")
                        and imported_pdf_assets
                    ):
                        if prepare_reader:
                            with st.spinner(_l(ui, "prepare_reader_after_import", "Prepare Reader text after import")):
                                prepare_summary = _prepare_reader_artifacts_for_sources(ctx, imported_pdf_assets)
                            if prepare_summary["prepared"]:
                                st.success(
                                    _l(ui, "reader_artifacts_prepared", "Reader text prepared: {ids}").format(
                                        ids=", ".join(prepare_summary["prepared"])
                                    )
                                )
                            for warning in prepare_summary["warnings"]:
                                st.warning(str(warning))
                        else:
                            st.session_state[prepare_notice_key] = _l(ui, 
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
                    _queue_pdf_import_warnings(list(imported), key_prefix="search_import")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.caption(_l(ui, "search_results_empty", "No paper candidates yet."))

    elif mode == "Manual URL":
        with st.form(f"paper_manual_url:{selected}"):
            url = st.text_input(_l(ui, "url_or_doi", "URL / DOI / arXiv / PDF URL"))
            title_hint = st.text_input(_l(ui, "title_hint", "Title hint"))
            node_options = _node_options(ctx)
            default_node = str(st.session_state.get(_paper_library_key(ctx, "node"), "") or "")
            node_ref = st.selectbox(
                _l(ui, "library_location", "Library location"),
                options=list(node_options),
                index=_node_select_index(node_options, default_node),
                format_func=lambda ref: node_options.get(ref, ref),
            )
            child_collection = st.text_input(_l(ui, "new_child_collection", "New child collection"))
            tags = st.text_input(ui["tags"])
            visibility = st.selectbox(ui["visibility"], ["private", "public"], index=0)
            status = st.selectbox(ui["status"], SOURCE_STATUSES, index=SOURCE_STATUSES.index("inbox"))
            download_pdf = st.checkbox(_l(ui, "download_open_access_pdf", "Download open-access PDF"), value=True)
            prepare_reader = st.checkbox(
                _l(ui, "prepare_reader_after_import", "Prepare Reader text after import"),
                value=True,
                disabled=not download_pdf,
            )
            submitted = st.form_submit_button(_l(ui, "import_url", "Import URL"), type="primary")
        if submitted:
            try:
                _accept_latest_sources_for_additive_write(ctx)
                import_node_ref = node_ref
                if str(child_collection or "").strip():
                    import_node_ref = create_paper_library_node(
                        _pdir,
                        child_collection,
                        parent_id=node_ref,
                    ).id
                source_id = import_paper_url(
                    _pdir,
                    url,
                    {
                        "title": title_hint,
                        "library_node_refs": [import_node_ref] if import_node_ref else [],
                        "tags": _tags(tags),
                        "visibility": visibility,
                        "status": status,
                        "download_pdf": download_pdf,
                    },
                )
                if download_pdf and prepare_reader:
                    with st.spinner(_l(ui, "prepare_reader_after_import", "Prepare Reader text after import")):
                        prepare_summary = _prepare_reader_artifacts_for_sources(ctx, [source_id])
                    for warning in prepare_summary["warnings"]:
                        st.warning(str(warning))
                refresh_file_snapshots([_sources_path])
                stash_git_backup_results()
                clear_web_cache()
                _focus_library_import(ctx, [source_id], import_node_ref)
                st.success(ui["created"].format(id=source_id))
                _queue_pdf_import_warnings([source_id], key_prefix="url_import")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    else:
        st.caption(_l(ui, "upload_pdf_caption", "Upload a local PDF and bind it to a private paper source."))
        with st.form(f"paper_upload:{selected}"):
            title = st.text_input(ui["title_label"])
            uploaded = st.file_uploader("PDF", type=["pdf"])
            node_options = _node_options(ctx)
            default_node = str(st.session_state.get(_paper_library_key(ctx, "node"), "") or "")
            node_ref = st.selectbox(
                _l(ui, "library_location", "Library location"),
                options=list(node_options),
                index=_node_select_index(node_options, default_node),
                format_func=lambda ref: node_options.get(ref, ref),
            )
            child_collection = st.text_input(_l(ui, "new_child_collection", "New child collection"))
            tags = st.text_input(ui["tags"])
            visibility = st.selectbox(ui["visibility"], ["private", "public"], index=0)
            prepare_reader = st.checkbox(
                _l(ui, "prepare_reader_after_import", "Prepare Reader text after import"),
                value=True,
            )
            submitted = st.form_submit_button(_l(ui, "upload_pdf", "Upload PDF"), type="primary")
        if submitted:
            try:
                if uploaded is None:
                    raise ValueError("Select a PDF first.")
                _accept_latest_sources_for_additive_write(ctx)
                import_node_ref = node_ref
                if str(child_collection or "").strip():
                    import_node_ref = create_paper_library_node(
                        _pdir,
                        child_collection,
                        parent_id=node_ref,
                    ).id
                inbox = load_research_sources(selected)
                source = add_research_source(
                    inbox,
                    title or uploaded.name,
                    kind="paper",
                    status="reading",
                    tags=_tags(tags),
                    visibility=visibility,
                    origin="manual",
                    library_node_refs=[import_node_ref] if import_node_ref else [],
                )
                save_research_sources(selected, inbox)
                import_paper_pdf(_pdir, source.id, uploaded.getvalue(), uploaded.name)
                if prepare_reader:
                    with st.spinner(_l(ui, "prepare_reader_after_import", "Prepare Reader text after import")):
                        prepare_summary = _prepare_reader_artifacts_for_sources(ctx, [source.id])
                    for warning in prepare_summary["warnings"]:
                        st.warning(str(warning))
                refresh_file_snapshots([_sources_path])
                stash_git_backup_results()
                clear_web_cache()
                _focus_library_import(ctx, [source.id], import_node_ref)
                st.success(ui["created"].format(id=source.id))
                if not prepare_reader:
                    st.session_state[prepare_notice_key] = _l(ui, 
                        "reader_background_prepare_hint",
                        "PDF assets are saved now; Reader will prepare text in the background when opened.",
                    )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


