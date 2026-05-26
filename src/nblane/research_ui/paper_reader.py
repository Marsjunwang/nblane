"""Reader frame, annotation handlers, and AI result store."""
from __future__ import annotations

import os
from datetime import datetime
from urllib.parse import quote

import streamlit as st
import yaml

from nblane.core.ai import (
    answer_paper_question,
    explain_paper_selection,
    extract_paper_claims,
    generate_paper_review_card,
    generate_paper_source_guide,
    translate_paper_segments,
)
from nblane.core.auth import mint_reader_token
from nblane.core.reader_actions import ReaderActionContext, handle_reader_action
from nblane.core.research_papers import (
    create_chunk_from_annotation,
    create_paper_annotation,
    load_paper_analysis,
    normalize_translation_row,
    paper_rows,
    save_paper_analysis,
    save_paper_annotations,
    text_hash,
    translate_full_paper,
    upsert_paper_translations,
)
from nblane.core.research_sources import (
    save_research_sources,
    update_research_source,
)
from nblane.core.research_workspace import (
    create_chunk,
    create_citation,
    upsert_research_claim,
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
from nblane.web_cache import (
    clear_web_cache,
    load_chunks,
    load_paper_annotations,
    load_paper_pages,
    load_paper_segments,
    load_paper_translations,
    load_research_citations,
    load_research_sources,
)
from nblane.web_shared import (
    assert_files_current,
    refresh_file_snapshots,
    stash_git_backup_results,
)

from .context import ResearchContext
from ._helpers import (
    _l,
    _paper_library_sidecar_unavailable,
    _paper_library_workspace_url,
    _paper_sources,
    _payload_int,
    _payload_list,
    _payload_text,
    _reader_api_base,
    _render_iframe,
    _render_sidecar_link_button,
    _source_label,
    _tags,
    _unique_text,
)


def _segment_dicts(ctx, source_id: str, limit: int = 20) -> list[dict[str, object]]:
    _pdir = ctx.pdir
    return [segment.to_dict() for segment in load_paper_segments(_pdir, source_id)[:limit]]


def _reader_key(ctx, source_id: str, name: str) -> str:
    selected = ctx.selected
    return f"paper_reader:{selected}:{source_id}:{name}"


def _set_reader_action_status(ctx, source_id: str, action: str, phase: str, message: str) -> None:
    st.session_state[_reader_key(ctx, source_id, "last_action_status")] = {
        "action": action,
        "phase": phase,
        "message": message,
    }


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


def _save_reader_progress(ctx, source_id: str, page: int) -> None:
    selected = ctx.selected
    _sources_path = ctx.sources_path
    page = max(1, int(page or 1))
    saved_key = _reader_key(ctx, source_id, "saved_progress_page")
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


def _save_reader_state(ctx, source_id: str, payload: dict) -> None:
    selected = ctx.selected
    _sources_path = ctx.sources_path
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


def _translation_counts_for_segments(ctx, source_id: str, target_lang: str = "zh") -> dict[str, int]:
    _pdir = ctx.pdir
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


def _update_or_delete_paper_annotation(ctx, source_id: str, payload: dict, *, delete: bool = False) -> str:
    _pdir = ctx.pdir
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


def _private_source_refs_for_citations(ctx, citation_ids: list[str]) -> list[str]:
    selected = ctx.selected
    _pdir = ctx.pdir
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


def _store_reader_ai_result(ctx, source_id: str, action: str, result) -> None:
    st.session_state[_reader_key(ctx, source_id, "ai_result")] = {
        "action": action,
        "structured": result.structured or {},
        "warnings": list(result.warnings),
    }


def _render_reader_ai_result(ctx, source_id: str) -> None:
    ui = ctx.ui
    result = st.session_state.get(_reader_key(ctx, source_id, "ai_result"))
    if not isinstance(result, dict):
        return
    with st.expander(_l(ui, "reader_ai_result", "Reader AI result"), expanded=False):
        st.caption(str(result.get("action") or "AI"))
        for warning in result.get("warnings") or []:
            st.warning(str(warning))
        st.code(
            yaml.dump(result.get("structured") or {}, allow_unicode=True, sort_keys=False),
            language="yaml",
        )


def _render_reader_translation_summary(ctx, source_id: str) -> None:
    ui = ctx.ui
    summary = st.session_state.get(_reader_key(ctx, source_id, "translation_summary"))
    if not isinstance(summary, dict):
        return
    with st.expander(_l(ui, "translation_summary", "Translation summary"), expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(_l(ui, "translated", "Translated"), summary.get("translated", 0))
        c2.metric(_l(ui, "missing", "Missing"), summary.get("missing", 0))
        c3.metric(_l(ui, "stale", "Stale"), summary.get("stale", 0))
        c4.metric(_l(ui, "failed", "Failed"), summary.get("failed", 0))
        if summary.get("warnings"):
            for warning in summary.get("warnings") or []:
                st.warning(str(warning))


def _handle_reader_component_event(ctx, 
    source_id: str,
    event: object,
    *,
    segment_rows,
    annotation_rows,
    chunk_rows,
) -> bool:
    selected = ctx.selected
    _pdir = ctx.pdir
    ui = ctx.ui
    user = ctx.user
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
    last_key = _reader_key(ctx, source_id, "last_event")
    if st.session_state.get(last_key) == identity:
        return True
    st.session_state[last_key] = identity

    try:
        if action == "selection_created":
            st.session_state[_reader_key(ctx, source_id, "selection")] = _selection_payload(payload, segment_rows)
            return True

        if action == "page_changed":
            page = _payload_int(payload, "page", 1)
            st.session_state[_reader_key(ctx, source_id, "page")] = max(1, page)
            return True

        if action == SAVE_PROGRESS:
            page = _payload_int(payload, "page", _payload_int(payload, "primary_page", 1))
            st.session_state[_reader_key(ctx, source_id, "page")] = max(1, page)
            _save_reader_progress(ctx, source_id, max(1, page))
            st.success(ui["saved"])
            return True

        if action == READER_STATE_CHANGED:
            page = _payload_int(payload, "page", _payload_int(payload, "primary_page", 1))
            visible = clean_page_list(payload.get("visible_pages"))
            st.session_state[_reader_key(ctx, source_id, "page")] = max(1, page)
            st.session_state[_reader_key(ctx, source_id, "visible_pages")] = visible
            _reader_requested_pages(source_id).update(visible or [max(1, page)])
            _save_reader_state(ctx, source_id, payload)
            return True

        if action == "viewport_changed":
            page = _payload_int(payload, "primary_page", _payload_int(payload, "page", 1))
            visible = clean_page_list(payload.get("visible_pages"))
            st.session_state[_reader_key(ctx, source_id, "page")] = max(1, page)
            st.session_state[_reader_key(ctx, source_id, "visible_pages")] = visible
            return True

        if action in {REQUEST_READER_CONTEXT, REQUEST_PAGE_PREVIEWS}:
            pages = clean_page_list(payload.get("pages") or payload.get("visible_pages"))
            if not pages:
                page = _payload_int(payload, "page", 1)
                pages = [max(1, page)]
            _reader_requested_pages(source_id).update(pages)
            st.session_state[_reader_key(ctx, source_id, "preview_page")] = pages[0]
            return True

        if action == REQUEST_PAGE_PREVIEW:
            page = _payload_int(payload, "page", 1)
            st.session_state[_reader_key(ctx, source_id, "preview_page")] = max(1, page)
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
            _store_reader_ai_result(ctx, source_id, action, result)
            if isinstance(result.structured, dict):
                save_paper_analysis(_pdir, source_id, result.structured)
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
                _set_reader_action_status(ctx, source_id, action, "done", ui["saved"])
            for warning in result.warnings:
                st.warning(str(warning))
            if result.warnings and not isinstance(result.structured, dict):
                _set_reader_action_status(ctx, source_id, action, "error", str(result.warnings[0]))
            return True

        if action == CODEX_DEEP_READ:
            ctx = ReaderActionContext(
                profile_name=selected,
                profile_path=_pdir,
                user_id=getattr(user, "id", "local"),
                source_id=source_id,
            )
            result = handle_reader_action(ctx, action, payload)
            st.session_state[_reader_key(ctx, source_id, "ai_result")] = {
                "action": action,
                "structured": result.data.get("structured") if isinstance(result.data, dict) else {},
                "warnings": list(result.warnings),
            }
            if result.ok:
                stash_git_backup_results()
                clear_web_cache()
                st.success(result.message or ui["saved"])
                _set_reader_action_status(ctx, source_id, action, "done", result.message or ui["saved"])
            else:
                st.warning(result.message or "Deep read did not return a candidate.")
                _set_reader_action_status(ctx, source_id, action, "error", result.message or "Deep read failed")
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
            st.session_state[_reader_key(ctx, source_id, "focus_annotation_id")] = ann.id
            return True

        if action == ANNOTATION_UPDATE:
            annotation_id = _update_or_delete_paper_annotation(ctx, source_id, payload)
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["saved"])
            st.session_state[_reader_key(ctx, source_id, "focus_annotation_id")] = annotation_id
            return True

        if action == ANNOTATION_DELETE:
            annotation_id = _update_or_delete_paper_annotation(ctx, source_id, payload, delete=True)
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["saved"])
            st.session_state[_reader_key(ctx, source_id, "focus_annotation_id")] = annotation_id
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
            st.session_state[_reader_key(ctx, source_id, "focus_chunk_id")] = chunk.id
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
            st.session_state[_reader_key(ctx, source_id, "translation_summary")] = summary
            stash_git_backup_results()
            clear_web_cache()
            st.success(
                _l(ui, "translation_full_saved", "Full-paper translation updated: {count} row(s).").format(
                    count=summary.get("updated", 0)
                )
            )
            _set_reader_action_status(ctx, 
                source_id,
                action,
                "done",
                _l(ui, "translation_full_saved", "Full-paper translation updated: {count} row(s).").format(
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
                message = _l(ui, "visible_pages_translation_saved", "Visible pages translated: saved {count} row(s).").format(
                    count=saved
                )
                st.success(message)
                _set_reader_action_status(ctx, source_id, action, "done", message)
            elif result.ok:
                message = result.message or _l(ui, 
                    "visible_pages_translation_saved_none",
                    "No visible-page translations were saved. AI returned {count} valid row(s).",
                ).format(count=summary.get("ai_rows", 0))
                st.info(message)
                _set_reader_action_status(ctx, source_id, action, "done", message)
            else:
                message = result.message or _l(ui, 
                    "visible_page_translation_no_text",
                    "No extracted text is available for the visible page yet. Use Paper Library > Artifacts to run extraction.",
                )
                st.warning(message)
                _set_reader_action_status(ctx, source_id, action, "error", message)
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
            _store_reader_ai_result(ctx, source_id, action, result)
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
                    rationale=_l(ui, "reader_citation_candidate", "Created from Reader selection; review before promotion."),
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
            _store_reader_ai_result(ctx, source_id, action, result)
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
            _store_reader_ai_result(ctx, source_id, action, result)
            for warning in result.warnings:
                st.warning(str(warning))
            return True

        if action == "jump_to_annotation":
            annotation_id = _payload_text(payload, "annotation_id", "id")
            if not annotation_id:
                raise ValueError("Reader jump needs annotation_id.")
            st.session_state[_reader_key(ctx, source_id, "focus_annotation_id")] = annotation_id
            return True

        if action == "jump_to_chunk":
            chunk_id = _payload_text(payload, "chunk_id", "id")
            if not chunk_id:
                raise ValueError("Reader jump needs chunk_id.")
            st.session_state[_reader_key(ctx, source_id, "focus_chunk_id")] = chunk_id
            return True

        st.warning(f"Unsupported reader action: {action or event}")
        return True
    except Exception as exc:
        st.error(str(exc))
        return True


def _render_paper_reader(ctx, inbox) -> None:
    selected = ctx.selected
    _pdir = ctx.pdir
    ui = ctx.ui
    user = ctx.user
    st.subheader(_l(ui, "reader", "Reader"))
    papers = _paper_sources(inbox)
    if not papers:
        st.caption(_l(ui, "no_papers", "No paper sources yet."))
        return
    reader_source_key = f"paper_reader_source:{selected}"
    paper_ids = [source.id for source in papers]
    remembered_source_id = str(st.session_state.get(reader_source_key, "") or "")
    if remembered_source_id not in paper_ids:
        st.session_state.pop(reader_source_key, None)
        remembered_source_id = ""

    if not remembered_source_id:
        st.info(_l(ui, "reader_no_paper_selected", "No paper selected. Open Paper Library to choose a paper to read."))
        actions = st.columns([1.2, 1.2, 3])
        with actions[0]:
            _render_sidecar_link_button(ctx, 
                _l(ui, "open_paper_library", "Open Paper Library"),
                _paper_library_workspace_url(ctx),
                key=f"paper_reader_open_library:{selected}",
                icon=":material/library_books:",
                type="primary",
                use_container_width=True,
            )
        recent_rows = sorted(
            paper_rows(_pdir, view="recent"),
            key=lambda row: str(row.get("last_read") or ""),
            reverse=True,
        )
        recent_source_id = str((recent_rows[0] if recent_rows else {}).get("id") or "")
        if recent_source_id:
            with actions[1]:
                if st.button(
                    _l(ui, "continue_recent_paper", "Continue recent paper"),
                    key=f"paper_reader_continue_recent:{selected}:{recent_source_id}",
                    icon=":material/history:",
                    use_container_width=True,
                ):
                    st.session_state[reader_source_key] = recent_source_id
                    st.rerun()
            st.caption(
                f"{_l(ui, 'recent_papers', 'Recent papers')}: "
                f"{_source_label(inbox, recent_source_id)}"
            )
        return

    source_id = remembered_source_id
    source = inbox.by_id().get(source_id)
    if source is None:
        st.session_state.pop(reader_source_key, None)
        return
    existing_pages = load_paper_pages(_pdir, source_id)
    existing_segments = load_paper_segments(_pdir, source_id)
    if source.metadata.get("pdf_asset_ref") and (not existing_pages or not existing_segments):
        st.info(
            _l(ui, 
                "reader_artifacts_missing",
                "Reader text artifacts are not extracted yet. The PDF can open now; Reader will prepare them automatically, or use Paper Library > Artifacts to run extraction manually.",
            )
        )
    status_bits = [
        f"PDF: {'yes' if source.metadata.get('pdf_asset_ref') else 'missing'}",
        f"{_l(ui, 'pages', 'Pages')}: {source.metadata.get('page_count', '') or '?'}",
        f"{_l(ui, 'annotations', 'Annotations')}: {len(load_paper_annotations(_pdir, source_id))}",
        f"{_l(ui, 'segments', 'Segments')}: {len(load_paper_segments(_pdir, source_id))}",
        f"{_l(ui, 'structured_extraction', 'Structure')}: "
        f"{source.metadata.get('reading_artifacts_status') or source.metadata.get('structure_backend', '') or _l(ui, 'missing', 'missing')}",
    ]
    heading, library_action = st.columns([4, 1.2], vertical_alignment="top")
    with heading:
        st.markdown(f"**{source.title}**")
        st.caption(f"`{source_id}`")
    with library_action:
        _render_sidecar_link_button(ctx, 
            _l(ui, "open_in_library", "Open in Library"),
            _paper_library_workspace_url(ctx, detail_id=source_id),
            key=f"paper_reader_open_source_library:{selected}:{source_id}",
            icon=":material/library_books:",
            use_container_width=True,
        )
    st.caption(" · ".join(status_bits))
    st.caption(
        _l(ui, 
            "reader_caption",
            "PDF Reader is the primary surface when a PDF asset is attached; diagnostics and text fallback stay out of the reading path.",
        )
    )
    artifact_warnings = source.metadata.get("structured_extraction_warnings") or source.metadata.get("text_extraction_warnings") or []
    artifact_notices = source.metadata.get("structured_extraction_notices") or source.metadata.get("reading_artifacts_notices") or []
    if artifact_warnings or artifact_notices:
        with st.expander(_l(ui, "reader_artifact_warnings", "Reader preparation warnings"), expanded=False):
            for notice in artifact_notices:
                st.info(str(notice))
            for warning in artifact_warnings:
                st.warning(str(warning))
    sidecar_unavailable, sidecar_message = _paper_library_sidecar_unavailable(ctx)
    if source.metadata.get("pdf_asset_ref") and not sidecar_unavailable:
        try:
            token = mint_reader_token(user.id, selected, source_id)
        except Exception as exc:
            st.error(str(exc))
            return
        base = _reader_api_base()
        encoded_source = quote(source_id, safe="")
        encoded_token = quote(token, safe="")
        iframe_src = f"{base}/reader/view/{encoded_source}?token={encoded_token}" if base else f"/reader/view/{encoded_source}?token={encoded_token}"
        try:
            iframe_height = max(640, int(os.getenv("NBLANE_READER_IFRAME_HEIGHT", "1200")))
        except (TypeError, ValueError):
            iframe_height = 1200
        _render_iframe(ctx, iframe_src, height=iframe_height, scrolling=False)
        return
    if source.metadata.get("pdf_asset_ref"):
        st.warning(
            _l(ui, 
                "reader_sidecar_unavailable_fallback",
                "PDF Reader is temporarily unavailable because the 8502 sidecar cannot be reached. Showing text-mode Reader fallback.",
            )
            + (f" `{sidecar_message}`" if sidecar_message else "")
        )
    else:
        st.info(_l(ui, "pdf_missing", "No PDF asset is attached; using text-mode Reader."))

    pages, segments, annotations, translations_tab, ai_tab, claims_tab = st.tabs(
        [
            _l(ui, "pages", "Pages"),
            _l(ui, "segments", "Segments"),
            _l(ui, "annotations", "Annotations"),
            _l(ui, "translation", "Translation"),
            "AI",
            ui["claims_citations"],
        ]
    )
    with pages:
        rows = load_paper_pages(_pdir, source_id)
        if rows:
            for page in rows[:20]:
                with st.expander(f"p. {page.page} · {page.char_count} chars"):
                    st.text(page.text or _l(ui, "page_text_empty", "No extracted text for this page."))
        else:
            st.caption(_l(ui, "pages_empty", "No extracted pages yet."))
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
            st.caption(_l(ui, "segments_empty", "No paper segments yet."))
    with annotations:
        segment_ids = [segment.segment_id for segment in load_paper_segments(_pdir, source_id)]
        with st.form(f"paper_annotation:{selected}:{source_id}"):
            page = st.number_input(_l(ui, "page", "Page"), min_value=0, value=0)
            selected_text = st.text_area(_l(ui, "selected_text", "Selected text"), height=110)
            note = st.text_area(ui["notes"], height=80)
            picked_segments = st.multiselect(_l(ui, "segment_refs", "Segment refs"), segment_ids)
            tags = st.text_input(ui["tags"])
            submitted = st.form_submit_button(_l(ui, "create_annotation", "Create annotation"), type="primary")
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
                _l(ui, "annotation_to_chunk", "Annotation to chunk"),
                options=[ann.id for ann in anns],
            )
            if st.button(_l(ui, "create_chunk_from_annotation", "Create chunk from annotation")):
                try:
                    chunk = create_chunk_from_annotation(_pdir, ann_id)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["created"].format(id=chunk.id))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.caption(_l(ui, "annotations_empty", "No annotations yet."))
    with translations_tab:
        segment_rows = load_paper_segments(_pdir, source_id)
        segment_ids = [segment.segment_id for segment in segment_rows]
        counts = _translation_counts_for_segments(ctx, source_id)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(_l(ui, "translated", "Translated"), counts["translated"])
        c2.metric(_l(ui, "missing", "Missing"), counts["missing"])
        c3.metric(_l(ui, "stale", "Stale"), counts["stale"])
        c4.metric(_l(ui, "failed", "Failed"), counts["failed"])
        if st.button(
            _l(ui, "translate_missing_stale", "Translate missing/stale"),
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
                st.session_state[_reader_key(ctx, source_id, "translation_summary")] = summary
                stash_git_backup_results()
                clear_web_cache()
                st.success(
                    _l(ui, "translation_full_saved", "Full-paper translation updated: {count} row(s).").format(
                        count=summary.get("updated", 0)
                    )
                )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        picked = st.multiselect(_l(ui, "translate_segments", "Translate segments"), segment_ids[:100])
        if st.button(_l(ui, "generate_translation_candidate", "Generate translation candidate"), disabled=not picked):
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
            if st.button(_l(ui, "accept_translation_candidate", "Accept translation candidate")):
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
            st.caption(_l(ui, "translations_empty", "No translations yet."))
    with ai_tab:
        segment_payload = _segment_dicts(ctx, source_id, limit=30)
        if st.button(_l(ui, "run_source_guide", "Run Source Guide")):
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
            if st.button(_l(ui, "accept_as_analysis", "Accept as analysis")):
                try:
                    save_paper_analysis(_pdir, source_id, guide)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                except Exception as exc:
                    st.error(str(exc))
        question = st.text_input(_l(ui, "ask_paper", "Ask paper"))
        if st.button(_l(ui, "ask_paper", "Ask paper"), disabled=not question):
            result = answer_paper_question(
                selected,
                source_id,
                question,
                payload={"segments": segment_payload},
            )
            st.code(yaml.dump(result.structured or {}, allow_unicode=True, sort_keys=False), language="yaml")
            for warning in result.warnings:
                st.warning(str(warning))
        if st.button(_l(ui, "extract_claim_candidates", "Extract claim candidates")):
            result = extract_paper_claims(selected, source_id, segments=segment_payload)
            st.code(yaml.dump(result.structured or {}, allow_unicode=True, sort_keys=False), language="yaml")
            for warning in result.warnings:
                st.warning(str(warning))
        analysis = load_paper_analysis(_pdir, source_id)
        if analysis:
            with st.expander(_l(ui, "saved_analysis", "Saved analysis")):
                st.code(yaml.dump(analysis, allow_unicode=True, sort_keys=False), language="yaml")
    with claims_tab:
        st.caption(_l(ui, "reader_claims_hint", "Use the Claims & Citations tab for durable claim/citation editing."))
        source_chunks = load_chunks(_pdir, source_id)
        st.dataframe(
            [
                {"id": chunk.id, "locator": chunk.locator, "text": chunk.text[:220]}
                for chunk in source_chunks
            ],
            use_container_width=True,
            hide_index=True,
        )


