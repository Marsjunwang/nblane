"""Claims, citations, and synthesis drafts UI."""
from __future__ import annotations

from pathlib import Path

import streamlit as st
import yaml

from nblane.core.public_site import create_blog_draft
from nblane.core.research_papers import (
    create_reading_note_markdown,
    create_reading_note_pack_markdown,
    format_research_citations,
    paper_citation_diagnostics,
    save_paper_note,
    save_research_export,
)
from nblane.core.research_sources import (
    SOURCE_STATUSES,
    load_research_sources,
)
from nblane.core.research_workspace import (
    RESEARCH_CHUNK_KINDS,
    RESEARCH_CLAIM_TYPES,
    build_research_claim_review_payload,
    build_research_export_manifest,
    build_research_export_payload,
    build_synthesis_draft_review,
    create_chunk,
    create_citation,
    create_citation_from_chunk,
    draft_synthesis_from_claims,
    load_chunks,
    load_research_citations,
    load_research_claims,
    load_research_drafts,
    merge_duplicate_research_claims,
    patch_research_claim,
    research_claim_to_evidence_candidate,
    research_draft_to_blog_candidate,
    research_draft_to_project_update_candidate,
    research_draft_to_resume_bullet_candidates,
    research_output_project_options,
    request_citation_for_claim,
    update_research_claim_links,
    update_research_claim_status,
    upsert_research_claim,
    verify_research_citations,
)
from nblane.core.research_sources import apply_research_evidence_candidate
from nblane.web_cache import clear_web_cache
from nblane.web_shared import (
    assert_files_current,
    refresh_file_snapshots,
    stash_git_backup_results,
)

from .context import ResearchContext
from ._helpers import (
    _applied_state,
    _commit_applied_state,
    _l,
    _node_options,
    _paper_library_workspace_url,
    _render_sidecar_link_button,
    _short_text,
    _source_label,
)


def _render_claims_citations(ctx, inbox) -> None:
    selected = ctx.selected
    _pdir = ctx.pdir
    ui = ctx.ui
    _sources_path = ctx.sources_path
    _research_claims_path = ctx.research_claims_path
    _research_citations_path = ctx.research_citations_path
    st.subheader(ui["claims_citations"])
    st.caption(ui["claim_boundary_hint"])
    if not inbox.sources:
        st.caption(ui["empty_status"])
        return
    source_options = [source.id for source in inbox.sources]
    source_key = f"research_cc_source:{selected}"
    status_options = ["", "draft", "ready", "promoted", "dismissed"]
    status_key = f"research_claim_status_filter:{selected}"
    queue_options = ["", "missing_citation", "quote_warning", "ready", "promoted"]
    queue_key = f"research_claim_queue_filter:{selected}"

    if str(st.session_state.get(source_key) or "") not in source_options:
        st.session_state.pop(source_key, None)
        st.session_state.pop(f"{source_key}__applied", None)
    if str(st.session_state.get(status_key) or "") not in status_options:
        st.session_state.pop(status_key, None)
        st.session_state.pop(f"{status_key}__applied", None)
    if str(st.session_state.get(queue_key) or "") not in queue_options:
        st.session_state.pop(queue_key, None)
        st.session_state.pop(f"{queue_key}__applied", None)

    if not _applied_state(source_key) and source_options:
        st.session_state[f"{source_key}__applied"] = source_options[0]

    with st.form(f"research_cc_filter_form:{selected}", clear_on_submit=False):
        f1, f2, f3 = st.columns([2, 1, 1])
        with f1:
            st.selectbox(
                ui["source_id"],
                options=source_options,
                format_func=lambda sid: next(
                    (source.title or source.id for source in inbox.sources if source.id == sid),
                    sid,
                ),
                key=source_key,
            )
        with f2:
            st.selectbox(
                _l(ui, "claim_status_filter", "Claim status filter"),
                options=status_options,
                format_func=lambda value: _l(ui, "all_statuses", "All statuses") if not value else value,
                key=status_key,
            )
        with f3:
            st.selectbox(
                _l(ui, "claim_queue_filter", "Review queue"),
                options=queue_options,
                format_func=lambda value: {
                    "": _l(ui, "all_queues", "All queues"),
                    "missing_citation": _l(ui, "missing_citation", "Missing citation"),
                    "quote_warning": _l(ui, "quote_warning", "Quote warning"),
                    "ready": _l(ui, "ready_claims", "Ready claims"),
                    "promoted": _l(ui, "promoted_claims", "Promoted claims"),
                }.get(value, value),
                key=queue_key,
            )
        applied = st.form_submit_button(_l(ui, "apply_filters", "Apply filters"))
        if applied:
            _commit_applied_state(source_key, status_key, queue_key)

    source_id = _applied_state(source_key, source_options[0] if source_options else "")
    if source_id not in source_options:
        source_id = source_options[0] if source_options else ""
    source = inbox.by_id().get(source_id)
    if source is None:
        st.caption(_l(ui, "claim_filter_pick_source", "Pick a source and click Apply to load claims."))
        return
    chunks = load_chunks(_pdir)
    source_chunks = [chunk for chunk in chunks if chunk.source_id == source_id]
    chunk_ids = [chunk.id for chunk in chunks]
    claim_rows = load_research_claims(_pdir)
    claim_ids = [claim.id for claim in claim_rows]
    citation_rows = load_research_citations(_pdir)
    status_filter = _applied_state(status_key)
    queue_filter = _applied_state(queue_key)
    review = build_research_claim_review_payload(
        _pdir,
        source_id=source_id,
        status=status_filter,
        queue=queue_filter,
    )
    summary = review.get("summary") or {}
    st.subheader(_l(ui, "claim_review_board", "Claim review board"))
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(_l(ui, "chunks", "Chunks"), summary.get("chunks", 0))
    m2.metric(ui["research_claims"], summary.get("claims", 0))
    m3.metric(ui["research_citations"], summary.get("citations", 0))
    m4.metric(_l(ui, "missing_citation", "Missing citation"), summary.get("missing_citation_claims", 0))
    m5.metric(_l(ui, "quote_warnings", "Quote warnings"), summary.get("quote_warnings", 0))

    claim_cards = list(review.get("claim_cards") or [])
    ready_batch_options = [
        str(card.get("id") or "")
        for card in claim_cards
        if card.get("status") in {"draft", "ready"}
    ]
    if ready_batch_options:
        with st.expander(_l(ui, "claim_bulk_review", "Bulk claim review"), expanded=False):
            bulk_claims = st.multiselect(
                _l(ui, "selected_claims", "Selected claims"),
                options=ready_batch_options,
                default=[str(card.get("id") or "") for card in claim_cards if card.get("status") == "ready"],
                format_func=lambda cid: next(
                    (
                        f"{cid} - {str(card.get('text') or '')[:90]}"
                        for card in claim_cards
                        if str(card.get("id") or "") == cid
                    ),
                    cid,
                ),
                key=f"research_claim_bulk:{selected}:{source_id}:{status_filter}:{queue_filter}",
            )
            bulk_citation_refs = []
            for card in claim_cards:
                if str(card.get("id") or "") in set(bulk_claims):
                    bulk_citation_refs.extend(str(ref) for ref in card.get("citation_refs") or [] if str(ref))
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button(
                    _l(ui, "verify_selected_quotes", "Verify selected quotes"),
                    disabled=not bulk_citation_refs,
                    key=f"research_claim_bulk_verify:{selected}:{source_id}",
                    use_container_width=True,
                ):
                    checks = verify_research_citations(_pdir, bulk_citation_refs)
                    st.session_state[f"research_claim_bulk_checks:{selected}:{source_id}"] = checks
            with b2:
                if st.button(
                    _l(ui, "mark_selected_ready", "Mark selected ready"),
                    disabled=not bulk_claims,
                    key=f"research_claim_bulk_ready:{selected}:{source_id}",
                    use_container_width=True,
                ):
                    try:
                        assert_files_current([_research_claims_path])
                        for claim_id in bulk_claims:
                            update_research_claim_status(_pdir, claim_id, "ready")
                        refresh_file_snapshots([_research_claims_path])
                        stash_git_backup_results()
                        clear_web_cache()
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with b3:
                preview_rows = []
                for claim_id in bulk_claims:
                    try:
                        preview_rows.append(
                            {
                                "claim_id": claim_id,
                                "candidate": research_claim_to_evidence_candidate(_pdir, claim_id),
                            }
                        )
                    except Exception as exc:
                        preview_rows.append({"claim_id": claim_id, "warning": str(exc)})
                if preview_rows:
                    with st.popover(_l(ui, "bulk_promote_preview", "Promote preview"), use_container_width=True):
                        st.code(
                            yaml.dump(preview_rows, allow_unicode=True, default_flow_style=False, sort_keys=False),
                            language="yaml",
                        )
            checks = st.session_state.get(f"research_claim_bulk_checks:{selected}:{source_id}")
            if isinstance(checks, dict):
                st.caption(
                    _l(ui, 
                        "bulk_quote_check_summary",
                        "{ok}/{total} selected citation quote check(s) passed.",
                    ).format(ok=checks.get("ok", 0), total=checks.get("total", 0))
                )
                for check in checks.get("checks") or []:
                    if check.get("ok"):
                        st.success(str(check.get("message") or check.get("citation_id")))
                    else:
                        st.warning(str(check.get("message") or check.get("citation_id")))

    duplicate_groups = list(review.get("duplicate_claim_groups") or [])
    if duplicate_groups:
        with st.expander(_l(ui, "duplicate_claims", "Duplicate claims"), expanded=True):
            st.warning(
                _l(ui, 
                    "duplicate_claims_hint",
                    "These claims have the same normalized text. Merge refs before promotion.",
                )
            )
            for index, group in enumerate(duplicate_groups):
                refs = [str(ref) for ref in group.get("claim_refs") or [] if str(ref)]
                if len(refs) < 2:
                    continue
                with st.form(f"research_merge_duplicate:{selected}:{source_id}:{index}"):
                    st.write(str(group.get("text") or ""))
                    primary_ref = st.selectbox(
                        _l(ui, "primary_claim", "Primary claim"),
                        refs,
                        key=f"research_duplicate_primary:{selected}:{source_id}:{index}",
                    )
                    duplicate_refs = st.multiselect(
                        _l(ui, "duplicates_to_merge", "Duplicates to merge"),
                        [ref for ref in refs if ref != primary_ref],
                        default=[ref for ref in refs if ref != primary_ref],
                        key=f"research_duplicate_refs:{selected}:{source_id}:{index}",
                    )
                    merge_note = st.text_input(
                        _l(ui, "merge_rationale", "Merge rationale"),
                        value=_l(ui, "duplicate_merge_default", "Merged during source claim review."),
                        key=f"research_duplicate_note:{selected}:{source_id}:{index}",
                    )
                    merge_submitted = st.form_submit_button(
                        _l(ui, "merge_duplicate_claims", "Merge duplicate claims"),
                        disabled=not duplicate_refs or not merge_note.strip(),
                    )
                if merge_submitted:
                    try:
                        assert_files_current([_research_claims_path])
                        merge_duplicate_research_claims(
                            _pdir,
                            primary_ref,
                            duplicate_refs,
                            rationale=merge_note,
                        )
                        refresh_file_snapshots([_research_claims_path])
                        stash_git_backup_results()
                        clear_web_cache()
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    evidence_col, claim_col, citation_col = st.columns([1.15, 1.9, 1.35], gap="medium")
    with evidence_col:
        st.markdown(f"**{_l(ui, 'source_evidence', 'Source evidence')}**")
        chunk_cards = list(review.get("chunk_cards") or [])
        if chunk_cards:
            for chunk in chunk_cards[:8]:
                with st.container(border=True):
                    st.markdown(f"**{chunk.get('title') or chunk.get('id')}**")
                    st.caption(" · ".join(str(item) for item in [chunk.get("kind"), chunk.get("locator")] if item))
                    linked = []
                    if chunk.get("linked_claims"):
                        linked.append(f"{ui['research_claims']}: {', '.join(chunk.get('linked_claims') or [])}")
                    if chunk.get("linked_citations"):
                        linked.append(f"{ui['research_citations']}: {', '.join(chunk.get('linked_citations') or [])}")
                    if linked:
                        st.caption(" · ".join(linked))
                    st.write(_short_text(chunk.get("text"), 360))
            if len(chunk_cards) > 8:
                st.caption(_l(ui, "more_chunks_hidden", "{count} more chunk(s) hidden by this compact view.").format(count=len(chunk_cards) - 8))
        else:
            st.caption(ui["chunks_empty"])

    with claim_col:
        st.markdown(f"**{_l(ui, 'research_claim_review', 'Research claim review')}**")
        if claim_cards:
            for claim_card in claim_cards:
                claim_id = str(claim_card.get("id") or "")
                with st.container(border=True):
                    st.markdown(f"**{claim_id}**")
                    st.caption(
                        " · ".join(
                            str(item)
                            for item in [
                                claim_card.get("status"),
                                claim_card.get("type"),
                                f"confidence={claim_card.get('confidence')}",
                                f"citation={claim_card.get('citation_status')}",
                                f"quote={claim_card.get('quote_status')}",
                            ]
                            if item
                        )
                    )
                    st.write(claim_card.get("text") or "")
                    refs_line = " · ".join(
                        [
                            f"sources: {', '.join(claim_card.get('source_refs') or []) or '0'}",
                            f"chunks: {', '.join(claim_card.get('chunk_refs') or []) or '0'}",
                            f"citations: {', '.join(claim_card.get('citation_refs') or []) or '0'}",
                        ]
                    )
                    st.caption(refs_line)
                    with st.expander(_l(ui, "edit_claim_card", "Edit claim and links"), expanded=False):
                        claim_type_options = list(RESEARCH_CLAIM_TYPES)
                        claim_confidence_options = ["low", "medium", "high"]
                        with st.form(f"research_claim_patch:{selected}:{claim_id}"):
                            patch_text = st.text_area(
                                ui["research_claim_text"],
                                value=str(claim_card.get("text") or ""),
                                height=90,
                                key=f"research_claim_patch_text:{selected}:{claim_id}",
                            )
                            p1, p2, p3 = st.columns(3)
                            with p1:
                                patch_type = st.selectbox(
                                    ui["research_claim_type"],
                                    claim_type_options,
                                    index=claim_type_options.index(str(claim_card.get("type") or "learning"))
                                    if str(claim_card.get("type") or "learning") in claim_type_options
                                    else claim_type_options.index("learning"),
                                    key=f"research_claim_patch_type:{selected}:{claim_id}",
                                )
                            with p2:
                                patch_confidence = st.selectbox(
                                    _l(ui, "confidence", "Confidence"),
                                    claim_confidence_options,
                                    index=claim_confidence_options.index(str(claim_card.get("confidence") or "medium"))
                                    if str(claim_card.get("confidence") or "medium") in claim_confidence_options
                                    else claim_confidence_options.index("medium"),
                                    key=f"research_claim_patch_confidence:{selected}:{claim_id}",
                                )
                            with p3:
                                patch_human_note = st.checkbox(
                                    ui["human_note"],
                                    value=bool(claim_card.get("human_note")),
                                    key=f"research_claim_patch_human:{selected}:{claim_id}",
                                )
                            patch_warnings = st.text_area(
                                _l(ui, "warnings", "Warnings"),
                                value="\n".join(str(item) for item in claim_card.get("warnings") or []),
                                height=64,
                                key=f"research_claim_patch_warnings:{selected}:{claim_id}",
                            )
                            patch_rationale = st.text_area(
                                ui["rationale"],
                                value=str(claim_card.get("rationale") or ""),
                                height=72,
                                key=f"research_claim_patch_rationale:{selected}:{claim_id}",
                            )
                            patch_submitted = st.form_submit_button(ui["save"], type="primary")
                        if patch_submitted:
                            try:
                                assert_files_current([_research_claims_path])
                                patch_research_claim(
                                    _pdir,
                                    claim_id,
                                    text=patch_text,
                                    type=patch_type,
                                    confidence=patch_confidence,
                                    warnings=patch_warnings,
                                    rationale=patch_rationale,
                                    human_note=patch_human_note,
                                )
                                refresh_file_snapshots([_research_claims_path])
                                stash_git_backup_results()
                                clear_web_cache()
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))

                        with st.form(f"research_claim_links:{selected}:{claim_id}"):
                            next_chunk_refs = st.multiselect(
                                _l(ui, "link_chunk", "Linked chunks"),
                                options=chunk_ids,
                                default=[str(ref) for ref in claim_card.get("chunk_refs") or [] if str(ref) in chunk_ids],
                                key=f"research_claim_links_chunks:{selected}:{claim_id}",
                            )
                            next_citation_refs = st.multiselect(
                                _l(ui, "link_citation", "Linked citations"),
                                options=[citation.id for citation in citation_rows],
                                default=[
                                    str(ref)
                                    for ref in claim_card.get("citation_refs") or []
                                    if str(ref) in {citation.id for citation in citation_rows}
                                ],
                                key=f"research_claim_links_citations:{selected}:{claim_id}",
                            )
                            links_submitted = st.form_submit_button(
                                _l(ui, "save_claim_links", "Save links"),
                                help=_l(ui, 
                                    "save_claim_links_help",
                                    "Removing a selection unlinks it from this claim.",
                                ),
                            )
                        if links_submitted:
                            try:
                                assert_files_current([_research_claims_path])
                                update_research_claim_links(
                                    _pdir,
                                    claim_id,
                                    chunk_refs=next_chunk_refs,
                                    citation_refs=next_citation_refs,
                                    mode="replace",
                                )
                                refresh_file_snapshots([_research_claims_path])
                                stash_git_backup_results()
                                clear_web_cache()
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))

                        chunk_choices = [chunk.id for chunk in source_chunks]
                        if chunk_choices:
                            with st.form(f"research_claim_citation_chunk:{selected}:{claim_id}"):
                                cite_chunk = st.selectbox(
                                    _l(ui, "citation_chunk", "Citation chunk"),
                                    options=chunk_choices,
                                    index=chunk_choices.index(str((claim_card.get("chunk_refs") or [""])[0]))
                                    if str((claim_card.get("chunk_refs") or [""])[0]) in chunk_choices
                                    else 0,
                                    key=f"research_claim_cite_chunk:{selected}:{claim_id}",
                                )
                                cite_quote = st.text_area(
                                    ui["citation_quote"],
                                    height=62,
                                    help=_l(ui, 
                                        "citation_quote_default",
                                        "Leave blank to use the selected chunk text as the quote.",
                                    ),
                                    key=f"research_claim_cite_quote:{selected}:{claim_id}",
                                )
                                create_from_chunk = st.form_submit_button(
                                    _l(ui, "create_citation_from_chunk", "Create citation from chunk"),
                                )
                            if create_from_chunk:
                                try:
                                    assert_files_current([_research_claims_path, _research_citations_path])
                                    create_citation_from_chunk(
                                        _pdir,
                                        claim_id,
                                        cite_chunk,
                                        quote=cite_quote,
                                    )
                                    refresh_file_snapshots([_research_claims_path, _research_citations_path])
                                    stash_git_backup_results()
                                    clear_web_cache()
                                    st.rerun()
                                except Exception as exc:
                                    st.error(str(exc))
                        with st.form(f"research_claim_request_citation:{selected}:{claim_id}"):
                            request_note = st.text_input(
                                _l(ui, "citation_request_note", "Citation request note"),
                                value=_l(ui, "citation_request_default", "Bind a stronger citation before public use."),
                                key=f"research_claim_request_note:{selected}:{claim_id}",
                            )
                            request_submitted = st.form_submit_button(
                                _l(ui, "request_citation", "Request citation"),
                            )
                        if request_submitted:
                            try:
                                assert_files_current([_research_claims_path])
                                request_citation_for_claim(_pdir, claim_id, note=request_note)
                                refresh_file_snapshots([_research_claims_path])
                                stash_git_backup_results()
                                clear_web_cache()
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
                    if claim_card.get("citation_status") == "missing":
                        st.warning(_l(ui, "claim_missing_citation_warning", "This claim has no citation yet. Bind a citation before public use."))
                    elif claim_card.get("quote_status") == "warning":
                        st.warning(_l(ui, "claim_quote_warning", "At least one linked citation needs quote review."))
                    for warning in claim_card.get("warnings") or []:
                        st.warning(str(warning))
                    try:
                        patch = research_claim_to_evidence_candidate(_pdir, claim_id)
                    except Exception as exc:
                        patch = None
                        st.warning(str(exc))
                    with st.expander(_l(ui, "evidence_candidate_preview", "Evidence candidate preview"), expanded=False):
                        if patch is not None:
                            st.code(
                                yaml.dump(patch, allow_unicode=True, default_flow_style=False, sort_keys=False),
                                language="yaml",
                            )
                        else:
                            st.caption(_l(ui, "no_candidate_preview", "No candidate preview is available for this claim."))
                    a1, a2, a3 = st.columns(3)
                    with a1:
                        if st.button(
                            _l(ui, "mark_ready", "Mark ready"),
                            key=f"research_claim_mark_ready:{selected}:{claim_id}",
                            disabled=claim_card.get("status") in {"ready", "promoted", "dismissed"},
                            icon=":material/check_circle:",
                            use_container_width=True,
                        ):
                            try:
                                assert_files_current([_research_claims_path])
                                update_research_claim_status(_pdir, claim_id, "ready")
                                refresh_file_snapshots([_research_claims_path])
                                stash_git_backup_results()
                                clear_web_cache()
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
                    with a2:
                        source_refs = [str(ref) for ref in claim_card.get("source_refs") or []]
                        if st.button(
                            _l(ui, "promote_to_evidence", "Promote"),
                            key=f"research_claim_promote:{selected}:{claim_id}",
                            disabled=patch is None or not source_refs or claim_card.get("status") == "promoted",
                            icon=":material/upgrade:",
                            use_container_width=True,
                        ):
                            try:
                                assert_files_current([_sources_path, _research_claims_path, _pdir / "evidence-pool.yaml"])
                                result = apply_research_evidence_candidate(selected, source_refs[0], patch or {})
                                matched_claim = next((item for item in claim_rows if item.id == claim_id), None)
                                if matched_claim is not None:
                                    upsert_research_claim(
                                        _pdir,
                                        matched_claim.text,
                                        claim_id=matched_claim.id,
                                        status="promoted",
                                        type=matched_claim.type,
                                        source_refs=matched_claim.source_refs,
                                        chunk_refs=matched_claim.chunk_refs,
                                        citation_refs=matched_claim.citation_refs,
                                        evidence_refs=[*matched_claim.evidence_refs, result["evidence_id"]],
                                        rationale=matched_claim.rationale,
                                        human_note=matched_claim.human_note,
                                        warnings=matched_claim.warnings,
                                        generated_by=matched_claim.generated_by or "research_workspace",
                                    )
                                refresh_file_snapshots(
                                    [
                                        _sources_path,
                                        _research_claims_path,
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
                    with a3:
                        dismiss_note = st.text_input(
                            _l(ui, "dismiss_rationale", "Dismiss rationale"),
                            key=f"research_claim_dismiss_note:{selected}:{claim_id}",
                            placeholder=_l(ui, "dismiss_rationale_placeholder", "Why is this claim dismissed?"),
                            label_visibility="collapsed",
                        )
                        if st.button(
                            _l(ui, "dismiss", "Dismiss"),
                            key=f"research_claim_dismiss:{selected}:{claim_id}",
                            disabled=claim_card.get("status") == "dismissed" or not dismiss_note.strip(),
                            icon=":material/do_not_disturb_on:",
                            use_container_width=True,
                        ):
                            try:
                                assert_files_current([_research_claims_path])
                                update_research_claim_status(
                                    _pdir,
                                    claim_id,
                                    "dismissed",
                                    note=dismiss_note,
                                )
                                refresh_file_snapshots([_research_claims_path])
                                stash_git_backup_results()
                                clear_web_cache()
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
        else:
            st.caption(ui["claims_empty"])

    with citation_col:
        st.markdown(f"**{_l(ui, 'citation_inspector', 'Citation inspector')}**")
        citation_cards = list(review.get("citation_cards") or [])
        if citation_cards:
            for citation in citation_cards[:10]:
                check = citation.get("quote_check") if isinstance(citation.get("quote_check"), dict) else {}
                with st.container(border=True):
                    st.markdown(f"**{citation.get('id')}**")
                    st.caption(
                        " · ".join(
                            str(item)
                            for item in [
                                f"claim={citation.get('claim_id')}",
                                f"source={citation.get('source_id')}",
                                f"chunk={citation.get('chunk_id') or 'none'}",
                                check.get("level"),
                            ]
                            if item
                        )
                    )
                    message = str(check.get("message") or "")
                    if check.get("ok"):
                        st.success(message)
                    else:
                        st.warning(message)
                    if citation.get("quote"):
                        st.write(citation.get("quote"))
                    if citation.get("locator") or citation.get("bibliography"):
                        st.caption(f"{citation.get('locator') or ''} · {citation.get('bibliography') or ''}")
                    locate_source = str(citation.get("source_id") or "")
                    locate_chunk = str(citation.get("chunk_id") or "")
                    locate_cols = st.columns(2)
                    with locate_cols[0]:
                        if locate_source:
                            _render_sidecar_link_button(ctx, 
                                _l(ui, "locate_source", "Locate source"),
                                _paper_library_workspace_url(ctx, 
                                    detail_id=locate_source,
                                    focus="claims",
                                    action="fix_citation",
                                    return_to="overview",
                                ),
                                key=f"citation_locate_source:{selected}:{locate_source}:{locate_chunk}",
                                use_container_width=True,
                            )
                    with locate_cols[1]:
                        st.caption(
                            _l(ui, "locator_label", "Locator")
                            + f": {citation.get('locator') or locate_chunk or '-'}"
                        )
            if len(citation_cards) > 10:
                st.caption(_l(ui, "more_citations_hidden", "{count} more citation(s) hidden by this compact view.").format(count=len(citation_cards) - 10))
        else:
            st.caption(ui["citations_empty"])

    st.divider()
    st.caption(_l(ui, "manual_research_editing_hint", "Manual source/chunk/claim/citation editors remain below as fallback tools."))

    chunk_tab, claim_tab, citation_tab = st.tabs(
        [
            _l(ui, "chunks", "Chunks"),
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
                        with st.expander(_l(ui, "metadata", "Metadata"), expanded=False):
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


def _research_candidate_manifest(profile: Path, candidate: dict) -> dict:
    return build_research_export_manifest(
        profile,
        source_refs=list(candidate.get("related_sources") or []),
        claim_refs=list(candidate.get("related_research_claims") or []),
        citation_refs=list(candidate.get("related_citations") or []),
    )


def _render_research_candidate_manifest(ctx, profile: Path, candidate: dict, key_prefix: str) -> tuple[dict, list[dict]]:
    selected = ctx.selected
    ui = ctx.ui
    try:
        manifest = _research_candidate_manifest(profile, candidate)
    except Exception as exc:
        st.warning(str(exc))
        return {}, [{"kind": "manifest_error", "ref": str(exc)}]
    blockers = list(manifest.get("blockers") or [])
    with st.expander(_l(ui, "candidate_manifest", "Candidate manifest"), expanded=bool(blockers)):
        if blockers:
            for blocker in blockers:
                kind = str(blocker.get("kind") or "")
                ref = str(blocker.get("ref") or "")
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.warning(f"{kind}: {ref}")
                with c2:
                    if kind == "private_source" and ref:
                        _render_sidecar_link_button(ctx, 
                            _l(ui, "review_visibility", "Review visibility"),
                            _paper_library_workspace_url(ctx, 
                                detail_id=ref,
                                focus="safety",
                                action="review_visibility",
                                return_to="overview",
                            ),
                            key=f"{key_prefix}:review_visibility:{selected}:{ref}",
                            use_container_width=True,
                        )
                    elif kind == "broken_citation":
                        if st.button(
                            _l(ui, "fix_citation", "Fix citation"),
                            key=f"{key_prefix}:fix_citation:{ref}",
                            use_container_width=True,
                        ):
                            st.session_state[f"research_claim_queue_filter:{selected}"] = "quote_warning"
                            st.info(_l(ui, "fix_citation_hint", "Open Claims & Citations to review quote warnings."))
                    elif kind == "unpromoted_research_claim":
                        if st.button(
                            _l(ui, "promote_claim", "Promote claim"),
                            key=f"{key_prefix}:promote_claim:{ref}",
                            use_container_width=True,
                        ):
                            st.session_state[f"research_claim_status_filter:{selected}"] = "ready"
                            st.info(_l(ui, "promote_claim_hint", "Open Claims & Citations to preview and promote claims."))
        else:
            st.success(_l(ui, "candidate_manifest_clear", "No provenance blockers for this candidate."))
        if st.checkbox(
            _l(ui, "show_manifest_yaml", "Show manifest YAML"),
            value=False,
            key=f"{key_prefix}:manifest_yaml",
        ):
            st.code(
                yaml.dump(
                    {
                        key: value
                        for key, value in manifest.items()
                        if key not in {"sources", "claims", "citations"}
                    },
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                language="yaml",
            )
    return manifest, blockers


def _render_synthesis_drafts(ctx) -> None:
    selected = ctx.selected
    _pdir = ctx.pdir
    ui = ctx.ui
    st.subheader(_l(ui, "synthesis_export", "Synthesis / Export"))
    citation_rows = load_research_citations(_pdir)
    chunk_rows = load_chunks(_pdir)
    claim_rows_all = load_research_claims(_pdir)
    source_book = load_research_sources(selected)
    source_ids = [source.id for source in source_book.sources]
    node_options = _node_options(ctx, include_unsorted=False)
    goal_options = sorted({ref for source in source_book.sources for ref in source.goal_refs})
    tag_options = sorted({tag for source in source_book.sources for tag in source.tags})

    with st.expander(_l(ui, "export_scope", "Export scope"), expanded=False):
        s1, s2, s3 = st.columns(3)
        with s1:
            scope_node = st.selectbox(
                _l(ui, "collection", "Collection"),
                options=["", *node_options],
                format_func=lambda ref: _l(ui, "all_collections", "All collections") if not ref else node_options.get(ref, ref),
                key=f"research_export_scope_node:{selected}",
            )
            scope_goals = st.multiselect(
                _l(ui, "goal_refs", "Goal refs"),
                options=goal_options,
                key=f"research_export_scope_goals:{selected}",
            )
        with s2:
            scope_source_statuses = st.multiselect(
                _l(ui, "source_statuses", "Source statuses"),
                options=list(SOURCE_STATUSES),
                key=f"research_export_scope_source_status:{selected}",
            )
            scope_claim_statuses = st.multiselect(
                _l(ui, "claim_statuses", "Claim statuses"),
                options=["draft", "ready", "promoted", "dismissed"],
                key=f"research_export_scope_claim_status:{selected}",
            )
        with s3:
            scope_tags = st.multiselect(
                _l(ui, "tags_label", "Tags"),
                options=tag_options,
                key=f"research_export_scope_tags:{selected}",
            )
            scope_sources = st.multiselect(
                _l(ui, "manual_sources", "Manual sources"),
                options=source_ids,
                format_func=lambda sid: _source_label(source_book, sid),
                key=f"research_export_scope_sources:{selected}",
            )
    export_scope = {
        "library_node_refs": [scope_node] if scope_node else [],
        "goal_refs": scope_goals,
        "source_statuses": scope_source_statuses,
        "claim_statuses": scope_claim_statuses,
        "tags": scope_tags,
        "source_refs": scope_sources,
    }
    scope_active = any(value for value in export_scope.values())
    scoped_export = build_research_export_payload(_pdir, scope=export_scope)
    scoped_selection = scoped_export.get("selection") if isinstance(scoped_export.get("selection"), dict) else {}
    if scope_active:
        st.caption(
            _l(ui, 
                "export_scope_summary",
                "Scope selected {sources} source(s), {claims} claim(s), and {citations} citation(s).",
            ).format(
                sources=len(scoped_selection.get("source_refs") or []),
                claims=len(scoped_selection.get("claim_refs") or []),
                citations=len(scoped_selection.get("citation_refs") or []),
            )
        )
    with st.expander(_l(ui, "export_citations", "Export citations"), expanded=False):
        citation_refs = st.multiselect(
            ui["research_citations"],
            options=[citation.id for citation in citation_rows],
            default=list(scoped_selection.get("citation_refs") or []) if scope_active else [],
            format_func=lambda cid: next(
                (
                    f"{cid} · {citation.locator or citation.source_id}"
                    for citation in citation_rows
                    if citation.id == cid
                ),
                cid,
            ),
        )
        export_format = st.radio("Format", ["markdown", "bibtex", "ris", "csl-json"], horizontal=True)
        export_citation_refs = citation_refs or (
            list(scoped_selection.get("citation_refs") or [])
            if scope_active
            else []
        )
        try:
            export_body = (
                ""
                if scope_active and not export_citation_refs
                else format_research_citations(
                    _pdir,
                    export_citation_refs,
                    format=export_format,
                )
            )
            export_manifest = build_research_export_manifest(
                _pdir,
                citation_refs=export_citation_refs,
                claim_refs=list(scoped_selection.get("claim_refs") or []) if scope_active else [],
                source_refs=list(scoped_selection.get("source_refs") or []) if scope_active else [],
            )
        except Exception as exc:
            export_body = ""
            export_manifest = {}
            st.warning(str(exc))
        private_refs = list(export_manifest.get("private_source_refs") or [])
        if private_refs:
            st.warning(
                _l(ui, 
                    "private_export_warning",
                    "This export includes private paper sources; keep it private or remove them before public use: {refs}",
                ).format(refs=", ".join(private_refs))
            )
        blockers = list(export_manifest.get("blockers") or [])
        if export_manifest:
            with st.expander(_l(ui, "export_manifest", "Export manifest"), expanded=bool(blockers)):
                e1, e2, e3, e4 = st.columns(4)
                e1.metric(_l(ui, "sources_total", "Sources"), len(export_manifest.get("source_refs") or []))
                e2.metric(ui["research_claims"], len(export_manifest.get("claim_refs") or []))
                e3.metric(ui["research_citations"], len(export_manifest.get("citation_refs") or []))
                e4.metric(_l(ui, "publish_blockers", "Publish blockers"), len(blockers))
                if blockers:
                    for blocker in blockers:
                        kind = str(blocker.get("kind") or "")
                        ref = str(blocker.get("ref") or "")
                        warning_col, action_col = st.columns([3, 1])
                        with warning_col:
                            st.warning(f"{kind}: {ref}")
                        with action_col:
                            if kind == "private_source" and ref:
                                _render_sidecar_link_button(ctx, 
                                    _l(ui, "review_visibility", "Review visibility"),
                                    _paper_library_workspace_url(ctx, 
                                        detail_id=ref,
                                        focus="safety",
                                        action="review_visibility",
                                        return_to="overview",
                                    ),
                                    key=f"export_review_visibility:{selected}:{ref}",
                                    use_container_width=True,
                                )
                            elif kind == "broken_citation":
                                if st.button(
                                    _l(ui, "fix_citation", "Fix citation"),
                                    key=f"export_fix_citation:{selected}:{ref}",
                                    use_container_width=True,
                                ):
                                    st.session_state[f"research_claim_queue_filter:{selected}"] = "quote_warning"
                                    st.info(_l(ui, "fix_citation_hint", "Open Claims & Citations to review quote warnings."))
                            elif kind == "unpromoted_research_claim":
                                if st.button(
                                    _l(ui, "promote_claim", "Promote claim"),
                                    key=f"export_promote_claim:{selected}:{ref}",
                                    use_container_width=True,
                                ):
                                    st.session_state[f"research_claim_status_filter:{selected}"] = "ready"
                                    st.info(_l(ui, "promote_claim_hint", "Open Claims & Citations to preview and promote claims."))
                provenance_tabs = st.tabs(
                    [
                        _l(ui, "sources", "Sources"),
                        ui["research_claims"],
                        ui["research_citations"],
                        _l(ui, "manifest_yaml", "Manifest YAML"),
                    ]
                )
                with provenance_tabs[0]:
                    source_rows = list(export_manifest.get("sources") or [])
                    if source_rows:
                        st.dataframe(source_rows, use_container_width=True, hide_index=True)
                    else:
                        st.caption(_l(ui, "sources_empty", "No sources selected."))
                with provenance_tabs[1]:
                    claim_rows_manifest = list(export_manifest.get("claims") or [])
                    if claim_rows_manifest:
                        st.dataframe(claim_rows_manifest, use_container_width=True, hide_index=True)
                    else:
                        st.caption(ui["claims_empty"])
                with provenance_tabs[2]:
                    citation_rows_manifest = list(export_manifest.get("citations") or [])
                    if citation_rows_manifest:
                        st.dataframe(citation_rows_manifest, use_container_width=True, hide_index=True)
                    else:
                        st.caption(ui["citations_empty"])
                with provenance_tabs[3]:
                    st.code(
                        yaml.dump(
                            {
                                key: value
                                for key, value in export_manifest.items()
                                if key not in {"sources", "claims", "citations"}
                            },
                            allow_unicode=True,
                            default_flow_style=False,
                            sort_keys=False,
                        ),
                        language="yaml",
                    )
        if export_body:
            st.text_area(
                _l(ui, "export_preview", "Export preview"),
                value=export_body,
                height=220,
                key=f"export_preview:{selected}:{export_format}",
            )
            st.download_button(
                _l(ui, "download_export", "Download export"),
                data=export_body,
                file_name=f"research-citations.{ {'bibtex': 'bib', 'ris': 'ris', 'csl-json': 'json'}.get(export_format, 'md') }",
            )
            save_private_export = not private_refs or st.checkbox(
                _l(ui, "confirm_private_export_save", "Confirm saving export with private sources"),
                value=False,
            )
            if st.button(_l(ui, "save_export", "Save export"), disabled=not save_private_export):
                try:
                    path = save_research_export(
                        _pdir,
                        export_body,
                        format=export_format,
                        manifest=export_manifest,
                    )
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(str(path))
                except Exception as exc:
                    st.error(str(exc))

    with st.expander(_l(ui, "reading_note_export", "Reading note export"), expanded=False):
        scoped_note_defaults = [
            ref for ref in scoped_selection.get("source_refs") or []
            if ref in source_ids
        ] if scope_active else []
        note_sources = st.multiselect(
            _l(ui, "note_sources", "Note sources"),
            options=source_ids,
            default=scoped_note_defaults,
            format_func=lambda sid: _source_label(source_book, sid),
            key=f"reading_note_sources:{selected}",
        ) if source_ids else []
        note_source_set = set(note_sources)
        note_claims = st.multiselect(
            ui["research_claims"],
            options=[claim.id for claim in claim_rows_all],
            default=[
                claim.id
                for claim in claim_rows_all
                if claim.id in set(scoped_selection.get("claim_refs") or [])
            ] if scope_active else [],
            key=f"reading_note_claims:{selected}",
        )
        note_chunks = st.multiselect(
            ui["chunk_refs"],
            options=[chunk.id for chunk in chunk_rows if not note_source_set or chunk.source_id in note_source_set],
            key=f"reading_note_chunks:{selected}",
        )
        note_citations = st.multiselect(
            ui["citations"],
            options=[citation.id for citation in citation_rows if not note_source_set or citation.source_id in note_source_set],
            default=[
                citation.id
                for citation in citation_rows
                if citation.id in set(scoped_selection.get("citation_refs") or [])
                and (not note_source_set or citation.source_id in note_source_set)
            ] if scope_active else [],
            key=f"reading_note_citations:{selected}",
        )
        if note_sources:
            if len(note_sources) == 1:
                note_body = create_reading_note_markdown(
                    _pdir,
                    note_sources[0],
                    claim_refs=note_claims,
                    chunk_refs=note_chunks,
                    citation_refs=note_citations,
                )
            else:
                note_body = create_reading_note_pack_markdown(
                    _pdir,
                    note_sources,
                    claim_refs=note_claims,
                    chunk_refs=note_chunks,
                    citation_refs=note_citations,
                )
            note_manifest = build_research_export_manifest(
                _pdir,
                source_refs=note_sources,
                claim_refs=note_claims,
                citation_refs=note_citations,
            )
            st.text_area(
                ui["body"],
                value=note_body,
                height=240,
                key=f"reading_note_body:{selected}:{'-'.join(note_sources)}",
            )
            n1, n2 = st.columns(2)
            with n1:
                st.download_button(
                    _l(ui, "download_note", "Download note"),
                    data=note_body,
                    file_name=(
                        f"{note_sources[0].replace(':', '-')}-reading-note.md"
                        if len(note_sources) == 1
                        else "research-reading-note-pack.md"
                    ),
                )
            with n2:
                if st.button(_l(ui, "save_note", "Save note")):
                    try:
                        if len(note_sources) == 1:
                            path = save_paper_note(
                                _pdir,
                                note_sources[0],
                                note_body,
                                metadata={
                                    "claim_refs": note_claims,
                                    "chunk_refs": note_chunks,
                                    "citation_refs": note_citations,
                                },
                            )
                        else:
                            path = save_research_export(
                                _pdir,
                                note_body,
                                format="markdown",
                                prefix="reading-note-pack",
                                manifest={
                                    **note_manifest,
                                    "chunk_refs": note_chunks,
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
        draft_review = build_synthesis_draft_review(_pdir, draft_id)
        with st.expander(_l(ui, "synthesis_review", "Synthesis coverage review"), expanded=True):
            coverage = draft_review.get("coverage") or {}
            c1, c2, c3 = st.columns(3)
            c1.metric(ui["research_claims"], coverage.get("claims", 0))
            c2.metric(_l(ui, "sources_total", "Sources"), coverage.get("sources", 0))
            c3.metric(ui["research_citations"], coverage.get("citations", 0))
            argument_map = list(draft_review.get("argument_map") or [])
            if argument_map:
                st.dataframe(argument_map, use_container_width=True, hide_index=True)
            warnings = draft_review.get("warnings") if isinstance(draft_review.get("warnings"), dict) else {}
            for claim_ref in warnings.get("missing_citation_claim_refs") or []:
                st.warning(
                    _l(ui, 
                        "synthesis_missing_claim_citation",
                        "Claim {claim_id} is in this draft without a linked citation.",
                    ).format(claim_id=claim_ref)
                )
            for citation_ref in warnings.get("broken_citation_refs") or []:
                st.warning(
                    _l(ui, 
                        "synthesis_broken_citation",
                        "Citation {citation_id} needs quote review before public use.",
                    ).format(citation_id=citation_ref)
                )
    except Exception as exc:
        st.warning(str(exc))
    st.subheader(_l(ui, "output_candidates", "Output Candidates"))
    blog_tab, project_tab, resume_tab = st.tabs(
        [
            _l(ui, "blog_candidate", "Blog Draft"),
            _l(ui, "project_update_candidate", "Project Update"),
            _l(ui, "resume_bullet_candidate", "Resume Bullet"),
        ]
    )
    with blog_tab:
        try:
            candidate = research_draft_to_blog_candidate(_pdir, draft_id)
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
            _, blog_blockers = _render_research_candidate_manifest(ctx, 
                _pdir,
                candidate,
                f"blog_candidate:{selected}:{draft_id}",
            )
        except Exception as exc:
            candidate = None
            blog_blockers = []
            st.warning(str(exc))
        confirm_candidate_blockers = not blog_blockers or st.checkbox(
            _l(ui, 
                "confirm_blog_candidate_blockers",
                "Create draft anyway; I will fix private, unpromoted, or broken refs before public use.",
            ),
            value=False,
            key=f"research_blog_candidate_blockers:{selected}:{draft_id}",
        )
        if st.button(
            ui["create_blog_draft"],
            disabled=candidate is None or not confirm_candidate_blockers,
            key=f"create_blog_draft:{selected}:{draft_id}",
        ):
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
    with project_tab:
        try:
            project_options = research_output_project_options(_pdir)
            project_labels = {
                row["id"]: f"{row.get('title') or row['id']} ({row['id']})"
                for row in project_options
            }
            project_id = st.selectbox(
                _l(ui, "project_update_project", "Project"),
                options=["", *project_labels],
                format_func=lambda ref: _l(ui, "project_update_no_project", "No project selected") if not ref else project_labels.get(ref, ref),
                key=f"project_update_candidate_project:{selected}:{draft_id}",
            )
            project_candidate = research_draft_to_project_update_candidate(
                _pdir,
                draft_id,
                project_id=project_id,
            )
            st.code(
                yaml.dump(
                    {key: value for key, value in project_candidate.items() if key != "body"},
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                language="yaml",
            )
            st.text_area(
                ui["body"],
                value=str(project_candidate.get("body") or ""),
                height=220,
                disabled=True,
                key=f"project_update_candidate_body:{selected}:{draft_id}:{project_id}",
            )
            _render_research_candidate_manifest(ctx, 
                _pdir,
                project_candidate,
                f"project_update_candidate:{selected}:{draft_id}:{project_id or 'none'}",
            )
        except Exception as exc:
            st.warning(str(exc))
    with resume_tab:
        try:
            bullets = research_draft_to_resume_bullet_candidates(_pdir, draft_id)
            for index, bullet in enumerate(bullets, start=1):
                st.markdown(f"**{index}.** {bullet.get('text') or ''}")
                st.code(
                    yaml.dump(
                        {key: value for key, value in bullet.items() if key != "text"},
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
                _render_research_candidate_manifest(ctx, 
                    _pdir,
                    bullet,
                    f"resume_bullet_candidate:{selected}:{draft_id}:{index}",
                )
        except Exception as exc:
            st.warning(str(exc))


