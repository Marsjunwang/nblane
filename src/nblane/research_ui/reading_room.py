"""Reading room form helpers."""
from __future__ import annotations

import streamlit as st
import yaml

from nblane.core.research_sources import (
    ResearchReading,
    apply_research_evidence_candidate,
    generate_reading_draft,
    research_evidence_patch,
    update_research_source,
)
from nblane.web_cache import clear_web_cache
from nblane.web_shared import (
    assert_files_current,
    refresh_file_snapshots,
    stash_git_backup_results,
)

from .context import ResearchContext
from ._helpers import _l, _text_lines
from .source_inbox import _save_sources


def _reading_key(ctx, name: str) -> str:
    selected = ctx.selected
    return f"research_reading:{selected}:{name}"


def _reading_from_form(ctx, source) -> ResearchReading:
    claims_raw = st.session_state.get(_reading_key(ctx, "claim_candidates"), "")
    citations_raw = st.session_state.get(_reading_key(ctx, "citations"), "")
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
        excerpt=str(st.session_state.get(_reading_key(ctx, "excerpt"), "") or "").strip(),
        translation=str(st.session_state.get(_reading_key(ctx, "translation"), "") or "").strip(),
        summary=str(st.session_state.get(_reading_key(ctx, "summary"), "") or "").strip(),
        key_points=_text_lines(str(st.session_state.get(_reading_key(ctx, "key_points"), "") or "")),
        claim_candidates=[item for item in claim_candidates if isinstance(item, dict)],
        citations=[item for item in citations if isinstance(item, dict)],
        synthesis_notes=str(st.session_state.get(_reading_key(ctx, "synthesis_notes"), "") or "").strip(),
        generated_by=str(
            st.session_state.get(_reading_key(ctx, "generated_by"), source.reading.generated_by) or ""
        ).strip(),
        updated_at=str(
            st.session_state.get(_reading_key(ctx, "updated_at"), source.reading.updated_at) or ""
        ).strip(),
    )


def _seed_reading_state(ctx, source) -> None:
    seed_key = _reading_key(ctx, "seed_source")
    if st.session_state.get(seed_key) == source.id:
        return
    reading = source.reading
    st.session_state[seed_key] = source.id
    st.session_state[_reading_key(ctx, "excerpt")] = reading.excerpt
    st.session_state[_reading_key(ctx, "translation")] = reading.translation
    st.session_state[_reading_key(ctx, "summary")] = reading.summary
    st.session_state[_reading_key(ctx, "key_points")] = "\n".join(reading.key_points)
    st.session_state[_reading_key(ctx, "claim_candidates")] = yaml.dump(
        reading.claim_candidates,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ) if reading.claim_candidates else ""
    st.session_state[_reading_key(ctx, "citations")] = yaml.dump(
        reading.citations,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ) if reading.citations else ""
    st.session_state[_reading_key(ctx, "synthesis_notes")] = reading.synthesis_notes
    st.session_state[_reading_key(ctx, "generated_by")] = reading.generated_by
    st.session_state[_reading_key(ctx, "updated_at")] = reading.updated_at


def _store_reading_state(ctx, reading: ResearchReading) -> None:
    st.session_state[_reading_key(ctx, "excerpt")] = reading.excerpt
    st.session_state[_reading_key(ctx, "translation")] = reading.translation
    st.session_state[_reading_key(ctx, "summary")] = reading.summary
    st.session_state[_reading_key(ctx, "key_points")] = "\n".join(reading.key_points)
    st.session_state[_reading_key(ctx, "claim_candidates")] = yaml.dump(
        reading.claim_candidates,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    st.session_state[_reading_key(ctx, "citations")] = yaml.dump(
        reading.citations,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    st.session_state[_reading_key(ctx, "synthesis_notes")] = reading.synthesis_notes
    st.session_state[_reading_key(ctx, "generated_by")] = reading.generated_by
    st.session_state[_reading_key(ctx, "updated_at")] = reading.updated_at


def _render_reading_room(ctx, inbox) -> None:
    selected = ctx.selected
    _pdir = ctx.pdir
    ui = ctx.ui
    _sources_path = ctx.sources_path
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
    _seed_reading_state(ctx, source)

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
        key=_reading_key(ctx, "excerpt"),
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
            _store_reading_state(ctx, reading)
            st.session_state[_reading_key(ctx, "warnings")] = warnings
            st.rerun()
    with b2:
        if st.button(ui["save_reading_annotations"]):
            reading = _reading_from_form(ctx, source)
            reading.updated_at = reading.updated_at or ""
            update_research_source(inbox, source.id, reading=reading)
            _save_sources(ctx, inbox, ui["saved"])
            st.rerun()
    warnings = st.session_state.get(_reading_key(ctx, "warnings"), [])
    if isinstance(warnings, list):
        for warning in warnings:
            st.warning(str(warning))

    st.text_area(ui["translation"], height=140, key=_reading_key(ctx, "translation"))
    st.text_area(ui["summary"], height=100, key=_reading_key(ctx, "summary"))
    st.text_area(ui["key_points"], height=100, key=_reading_key(ctx, "key_points"))
    st.text_area(ui["claim_candidates"], height=170, key=_reading_key(ctx, "claim_candidates"))
    st.text_area(ui["citations"], height=150, key=_reading_key(ctx, "citations"))
    st.text_area(ui["synthesis_notes"], height=130, key=_reading_key(ctx, "synthesis_notes"))

    reading = _reading_from_form(ctx, source)
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
            key=f"reading_room_create_evidence:{selected}:{source.id}",
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


