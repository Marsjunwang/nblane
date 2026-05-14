"""Research Source Inbox -- capture and triage external sources."""

from __future__ import annotations

import streamlit as st
import yaml

from nblane.core.io import profile_dir
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


def _render_workspace_overview(inbox) -> None:
    claim_rows = load_research_claims(_pdir)
    draft_rows = load_research_drafts(_pdir)
    connector_rows = list(load_connectors(_pdir).get("connectors") or [])
    private_sources = [
        source for source in inbox.sources if source.visibility == "private"
    ]
    public_sources = [
        source for source in inbox.sources if source.visibility == "public"
    ]
    ready_claims = [
        claim for claim in claim_rows if claim.status in {"ready", "promoted"}
    ]
    enabled_connectors = [
        row for row in connector_rows if bool(row.get("enabled", True))
    ]

    st.subheader(ui["workspace_overview"])
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric(ui["sources_total"], len(inbox.sources))
    m2.metric(ui["sources_private"], len(private_sources))
    m3.metric(ui["sources_public"], len(public_sources))
    m4.metric(ui["ready_claims"], len(ready_claims))
    m5.metric(ui["drafts_total"], len(draft_rows))
    m6.metric(ui["connectors_enabled"], len(enabled_connectors))

    st.caption(ui["reading_flow_hint"])
    st.caption(ui["claim_boundary_hint"])

    st.markdown(f"**{ui['research_primary_actions']}**")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.page_link("pages/7_Research.py", label=ui["action_add_source"])
    with a2:
        st.page_link("pages/7_Research.py", label=ui["action_open_reading"])
    with a3:
        st.page_link("pages/7_Research.py", label=ui["action_create_synthesis"])


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
            reading, warnings = generate_reading_draft(source, excerpt, mode)
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
            body = st.text_area(ui["body"], height=180)
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
        st.text_area(ui["body"], value=str(candidate.get("body") or ""), height=240, disabled=True)
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

_render_workspace_overview(inbox)
st.divider()

tab_inbox, tab_reading, tab_claims, tab_drafts, tab_connectors = st.tabs(
    [
        ui["source_inbox"],
        ui["reading_room"],
        ui["claims_citations"],
        ui["synthesis_drafts"],
        ui["connectors"],
    ]
)

with tab_inbox:
    _render_source_queue(inbox)
    st.divider()
    with st.expander(ui["add_source"], expanded=not inbox.sources):
        _render_source_form(
            inbox,
            prefix=f"research_source_add_{selected}",
        )
    st.divider()
    _render_candidate_preview(inbox)

with tab_reading:
    _render_reading_room(inbox)

with tab_claims:
    _render_claims_citations(inbox)

with tab_drafts:
    _render_synthesis_drafts()

with tab_connectors:
    _render_connectors()
