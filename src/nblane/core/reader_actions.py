"""Side-effecting paper Reader actions shared by Streamlit fallback and FastAPI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from nblane.core import git_backup
from nblane.core.ai import (
    answer_paper_question,
    explain_paper_selection,
    generate_paper_review_card,
    translate_paper_segments,
)
from nblane.core.research_papers import (
    create_paper_annotation,
    load_paper_analysis,
    load_paper_annotations,
    load_paper_pages,
    load_paper_segments,
    load_paper_translations,
    save_paper_analysis,
    save_paper_annotations,
    text_hash,
    translate_full_paper,
    upsert_paper_translations,
)
from nblane.core.research_sources import (
    load_research_sources,
    save_research_sources,
    update_research_source,
)
from nblane.core.research_workspace import (
    create_chunk,
    create_citation,
    load_chunks,
    upsert_research_claim,
)
from nblane.research_paper_reader_component.events import (
    ANNOTATION_CREATE,
    ANNOTATION_DELETE,
    ANNOTATION_UPDATE,
    ASK_PAPER,
    CREATE_CHUNK_FROM_SELECTION,
    CREATE_CITATION,
    EXPLAIN_SELECTION,
    RETRY_TRANSLATION_SCOPE,
    SAVE_PROGRESS,
    TRANSLATE_FULL_PAPER,
    TRANSLATE_SELECTION,
    TRANSLATE_VISIBLE_PAGES,
    clean_page_list,
)


@dataclass(frozen=True)
class ReaderActionContext:
    """Context required to perform one Reader action."""

    profile_name: str
    profile_path: Path
    user_id: str
    source_id: str


@dataclass
class ReaderActionResult:
    """JSON-serializable Reader action result."""

    ok: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    changed_ids: dict[str, str] = field(default_factory=dict)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "data": dict(self.data),
            "warnings": list(self.warnings),
            "changed_ids": dict(self.changed_ids),
            "message": self.message,
        }


def _payload_text(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _payload_list(payload: dict[str, Any], *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            values.extend(part.strip() for part in value.split(",") if part.strip())
        elif isinstance(value, (list, tuple, set)):
            values.extend(str(item).strip() for item in value if str(item).strip())
        elif value is not None and str(value).strip():
            values.append(str(value).strip())
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _payload_int(payload: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(payload.get(key) or default)
    except (TypeError, ValueError):
        return default


def _backup_warnings() -> list[str]:
    warnings: list[str] = []
    for result in git_backup.consume_results():
        if result.error:
            warnings.append(f"Git backup failed: {result.error}")
        if result.push_error:
            warnings.append(f"Git backup committed but push failed: {result.push_error}")
    return warnings


def _selection_segments(payload: dict[str, Any], segment_rows) -> list[dict[str, Any]]:
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


def _context_segments(payload: dict[str, Any], segment_rows, *, limit: int = 30) -> list[dict[str, Any]]:
    picked = _selection_segments(payload, segment_rows)
    if picked:
        return picked
    return [segment.to_dict() for segment in segment_rows[:limit]]


def _selection_text(payload: dict[str, Any], segment_rows) -> str:
    selected = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
    if selected:
        return selected
    refs = {
        row.get("segment_id")
        for row in _selection_segments(payload, segment_rows)
        if row.get("segment_id")
    }
    if not refs:
        return ""
    return "\n\n".join(segment.text for segment in segment_rows if segment.segment_id in refs)


def _translation_row_current(row: Any, source_hash: str, target_lang: str) -> bool:
    return bool(
        row is not None
        and getattr(row, "target_lang", "") == target_lang
        and getattr(row, "source_hash", "") == source_hash
        and getattr(row, "status", "") == "translated"
        and str(getattr(row, "translated_text", "") or "").strip()
    )


def _visible_translation_summary(
    *,
    scope: str,
    requested_pages: list[int],
    segments_selected: int,
    ai_rows: int,
    saved: int,
    failed: int,
    skipped: int,
    target_lang: str,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "requested_pages": requested_pages,
        "segments_selected": segments_selected,
        "ai_rows": ai_rows,
        "saved": saved,
        "failed": failed,
        "skipped": skipped,
        "target_lang": target_lang,
    }


def _update_or_delete_paper_annotation(
    profile_path: Path,
    source_id: str,
    payload: dict[str, Any],
    *,
    delete: bool = False,
) -> str:
    annotation_id = _payload_text(payload, "annotation_id", "id")
    if not annotation_id:
        raise ValueError("Reader annotation update needs annotation_id.")
    annotations = load_paper_annotations(profile_path, source_id)
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
            note = _payload_text(payload, "note")
            if note:
                ann.note = note
            color = _payload_text(payload, "color")
            if color:
                ann.color = color
            locator = _payload_text(payload, "locator")
            if locator:
                ann.locator = locator
            ann.page = _payload_int(payload, "page", ann.page)
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
    save_paper_annotations(profile_path, source_id, annotations)
    return updated


def save_reader_progress(ctx: ReaderActionContext, payload: dict[str, Any]) -> ReaderActionResult:
    page = max(1, _payload_int(payload, "page", _payload_int(payload, "primary_page", 1)))
    inbox = load_research_sources(ctx.profile_path)
    src = inbox.by_id().get(ctx.source_id)
    if src is None:
        raise ValueError(f"Unknown research source: {ctx.source_id}")
    metadata = dict(src.metadata or {})
    metadata["last_read_page"] = page
    metadata["last_read_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    update_research_source(inbox, ctx.source_id, metadata=metadata, status="reading")
    save_research_sources(ctx.profile_path, inbox)
    return ReaderActionResult(
        data={"page": page},
        changed_ids={"source_id": ctx.source_id},
        message="Saved",
    )


def handle_reader_action(
    ctx: ReaderActionContext,
    action: str,
    payload: dict[str, Any] | None = None,
    *,
    progress_callback: Any | None = None,
) -> ReaderActionResult:
    """Run one Reader action and return a JSON-friendly result."""

    clean_action = str(action or "").strip()
    if not clean_action:
        raise ValueError("Reader action cannot be blank.")
    data = dict(payload or {})
    payload_source = _payload_text(data, "source_id")
    if payload_source and payload_source != ctx.source_id:
        raise ValueError(f"Reader action source mismatch: {payload_source}")

    git_backup.start_operation(ctx.user_id or "reader")
    result = _handle_reader_action_inner(ctx, clean_action, data, progress_callback=progress_callback)
    result.warnings.extend(_backup_warnings())
    return result


def _handle_reader_action_inner(
    ctx: ReaderActionContext,
    action: str,
    payload: dict[str, Any],
    *,
    progress_callback: Any | None = None,
) -> ReaderActionResult:
    profile = ctx.profile_path
    source_id = ctx.source_id
    segment_rows = load_paper_segments(profile, source_id)
    annotation_rows = load_paper_annotations(profile, source_id)
    chunk_rows = load_chunks(profile, source_id)

    if action == SAVE_PROGRESS:
        return save_reader_progress(ctx, payload)

    if action in {ANNOTATION_CREATE, "create_annotation"}:
        ann = create_paper_annotation(
            profile,
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
        return ReaderActionResult(
            data={"annotation": ann.to_dict()},
            changed_ids={"annotation_id": ann.id},
            message=f"Created {ann.id}",
        )

    if action == ANNOTATION_UPDATE:
        annotation_id = _update_or_delete_paper_annotation(profile, source_id, payload)
        return ReaderActionResult(changed_ids={"annotation_id": annotation_id}, message="Saved")

    if action == ANNOTATION_DELETE:
        annotation_id = _update_or_delete_paper_annotation(profile, source_id, payload, delete=True)
        return ReaderActionResult(changed_ids={"annotation_id": annotation_id}, message="Saved")

    if action in {CREATE_CHUNK_FROM_SELECTION, "create_chunk"}:
        selected_text = _selection_text(payload, segment_rows)
        chunk = create_chunk(
            profile,
            source_id,
            selected_text,
            kind=_payload_text(payload, "kind") or "excerpt",
            title=_payload_text(payload, "title"),
            locator=_payload_text(payload, "locator"),
            metadata={
                "page": _payload_int(payload, "page"),
                "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
                "segment_refs": _payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
                "annotation_id": _payload_text(payload, "annotation_id"),
                "source": "reader_sidecar",
            },
        )
        return ReaderActionResult(
            data={"chunk": chunk.to_dict()},
            changed_ids={"chunk_id": chunk.id},
            message=f"Created {chunk.id}",
        )

    if action == CREATE_CITATION:
        selected_text = _selection_text(payload, segment_rows)
        chunk_id = _payload_text(payload, "chunk_id", "chunk_ref")
        if not chunk_id and selected_text:
            chunk = create_chunk(
                profile,
                source_id,
                selected_text,
                kind="excerpt",
                locator=_payload_text(payload, "locator"),
                metadata={
                    "page": _payload_int(payload, "page"),
                    "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
                    "segment_refs": _payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
                    "annotation_id": _payload_text(payload, "annotation_id"),
                    "source": "reader_sidecar",
                },
            )
            chunk_id = chunk.id
        claim_id = _payload_text(payload, "claim_id", "research_claim_id")
        if not claim_id:
            claim_text = _payload_text(payload, "claim_text", "text") or selected_text
            if not claim_text:
                raise ValueError("Reader citation needs a claim id, selected text, or claim text.")
            claim = upsert_research_claim(
                profile,
                claim_text,
                status="draft",
                type=_payload_text(payload, "claim_type") or "finding",
                source_refs=[source_id],
                chunk_refs=[chunk_id] if chunk_id else [],
                confidence="medium",
                rationale="Created from Reader selection; review before promotion.",
                generated_by="reader_sidecar",
            )
            claim_id = claim.id
        citation = create_citation(
            profile,
            claim_id,
            source_id=source_id,
            chunk_id=chunk_id,
            locator=_payload_text(payload, "locator"),
            quote=_payload_text(payload, "quote", "selected_text", "selection_text", "text"),
            bibliography=_payload_text(payload, "bibliography"),
            note=_payload_text(payload, "note"),
        )
        return ReaderActionResult(
            data={"citation": citation.to_dict()},
            changed_ids={"citation_id": citation.id, "claim_id": claim_id, "chunk_id": chunk_id},
            message=f"Created {citation.id}",
        )

    if action == TRANSLATE_FULL_PAPER:
        summary = translate_full_paper(
            profile,
            source_id,
            target_lang=_payload_text(payload, "target_lang", "language") or "zh",
            mode=_payload_text(payload, "mode") or "missing_or_stale",
            ai_profile=ctx.profile_name,
            require_review=False,
            progress_callback=progress_callback,
        )
        return ReaderActionResult(
            data={"summary": summary},
            message=f"Full-paper translation updated: {summary.get('updated', 0)} row(s).",
        )

    if action in {TRANSLATE_VISIBLE_PAGES, RETRY_TRANSLATION_SCOPE}:
        target_lang = _payload_text(payload, "target_lang", "language") or "zh"
        refs = set(_payload_list(payload, "segment_refs", "segment_ids", "segment_id"))
        visible_pages = {
            int(item)
            for item in payload.get("visible_pages", [])
            if str(item).strip().isdigit()
        } if isinstance(payload.get("visible_pages"), list) else set()
        primary_page = _payload_int(payload, "primary_page", _payload_int(payload, "page", 0))
        if not visible_pages and primary_page:
            visible_pages = {primary_page}
        requested_pages = sorted(visible_pages)
        segments = [
            segment
            for segment in segment_rows
            if (refs and segment.segment_id in refs)
            or (visible_pages and segment.page in visible_pages)
        ]
        segment_payloads = [segment.to_dict() for segment in segments]
        page_scope_rows: dict[str, dict[str, Any]] = {}
        if not segment_payloads and visible_pages:
            for page in load_paper_pages(profile, source_id):
                if page.page not in visible_pages or not str(page.text or "").strip():
                    continue
                page_hash = page.text_hash or text_hash(page.text)
                synthetic_id = f"page:{page.page}"
                page_scope_rows[synthetic_id] = {
                    "segment_id": synthetic_id,
                    "source_id": source_id,
                    "scope_type": "page",
                    "scope_ref": f"page:{page.page}:{page_hash}",
                    "page": page.page,
                    "order": 0,
                    "section_path": [],
                    "kind": "page",
                    "text": page.text,
                    "text_hash": page_hash,
                    "locator": f"p. {page.page}",
                }
            segment_payloads = list(page_scope_rows.values())
        if not segment_payloads:
            summary = _visible_translation_summary(
                scope="page" if visible_pages else "segment",
                requested_pages=requested_pages,
                segments_selected=0,
                ai_rows=0,
                saved=0,
                failed=0,
                skipped=0,
                target_lang=target_lang,
            )
            return ReaderActionResult(
                ok=False,
                data={"summary": summary},
                message="No extracted text is available for the visible page yet.",
            )
        ai_result = translate_paper_segments(
            ctx.profile_name,
            source_id,
            segment_payloads,
            target_lang=target_lang,
            require_review=False,
        )
        translations = []
        if isinstance(ai_result.structured, dict):
            translations = [row for row in ai_result.structured.get("translations", []) if isinstance(row, dict)]
        warnings = list(ai_result.warnings)
        savable: list[dict[str, Any]] = []
        saved = 0
        failed = 0
        skipped = 0
        current_translations = load_paper_translations(profile, source_id)
        if page_scope_rows:
            scope = "page"
            page_index: dict[str, dict[str, Any]] = {}
            for page_row in page_scope_rows.values():
                page_index[str(page_row["segment_id"])] = page_row
                page_index[str(page_row["scope_ref"])] = page_row
            existing_by_scope = {
                row.scope_ref: row
                for row in current_translations
                if row.scope_type == "page" and row.target_lang == target_lang
            }
            for row in translations:
                row_ref = str(row.get("segment_id") or row.get("scope_ref") or "")
                if not row_ref:
                    warnings.append("Skipped translation row without segment_id or scope_ref.")
                    skipped += 1
                    continue
                page_row = page_index.get(row_ref)
                if page_row is None:
                    warnings.append(f"Skipped translation row for unknown page scope: {row_ref}.")
                    skipped += 1
                    continue
                source_hash = str(row.get("source_hash") or row.get("text_hash") or row.get("source_text_hash") or "").strip()
                if source_hash != page_row["text_hash"]:
                    warnings.append(f"Skipped translation for {row_ref}: source_hash mismatch.")
                    skipped += 1
                    continue
                translated_text = str(row.get("translated_text") or "").strip()
                if not translated_text:
                    warnings.append(f"Skipped translation for {row_ref}: translated_text is blank.")
                    existing = existing_by_scope.get(str(page_row["scope_ref"]))
                    if not _translation_row_current(existing, str(page_row["text_hash"]), target_lang):
                        savable.append(
                            {
                                **row,
                                "scope_type": "page",
                                "scope_ref": page_row["scope_ref"],
                                "segment_id": "",
                                "page": page_row["page"],
                                "source_hash": page_row["text_hash"],
                                "source_text": page_row["text"],
                                "target_lang": target_lang,
                                "translated_text": "",
                                "status": "failed",
                                "warnings": _payload_list(row, "warnings") + ["translated_text is blank."],
                            }
                        )
                        failed += 1
                    else:
                        skipped += 1
                    continue
                savable.append(
                    {
                        **row,
                        "scope_type": "page",
                        "scope_ref": page_row["scope_ref"],
                        "segment_id": "",
                        "page": page_row["page"],
                        "source_hash": page_row["text_hash"],
                        "source_text": page_row["text"],
                        "target_lang": target_lang,
                        "translated_text": translated_text,
                    }
                )
                saved += 1
        else:
            scope = "segment"
            segment_ids = {segment.segment_id for segment in segments}
            segment_by_id = {segment.segment_id: segment for segment in segments}
            existing_by_segment = {
                row.segment_id: row
                for row in current_translations
                if row.segment_id and row.target_lang == target_lang
            }
            for row in translations:
                row_ref = str(row.get("segment_id") or row.get("scope_ref") or "")
                if not row_ref:
                    warnings.append("Skipped translation row without segment_id or scope_ref.")
                    skipped += 1
                    continue
                if row_ref not in segment_ids:
                    warnings.append(f"Skipped translation row for unknown segment: {row_ref}.")
                    skipped += 1
                    continue
                segment = segment_by_id[row_ref]
                source_hash = str(row.get("source_hash") or row.get("text_hash") or row.get("source_text_hash") or "").strip()
                if source_hash != segment.text_hash:
                    warnings.append(f"Skipped translation for {row_ref}: source_hash mismatch.")
                    skipped += 1
                    continue
                translated_text = str(row.get("translated_text") or "").strip()
                if not translated_text:
                    warnings.append(f"Skipped translation for {row_ref}: translated_text is blank.")
                    existing = existing_by_segment.get(row_ref)
                    if not _translation_row_current(existing, segment.text_hash, target_lang):
                        savable.append(
                            {
                                **row,
                                "source_id": source_id,
                                "scope_type": "segment",
                                "scope_ref": segment.segment_id,
                                "segment_id": segment.segment_id,
                                "page": segment.page,
                                "source_hash": segment.text_hash,
                                "source_text": segment.text,
                                "target_lang": target_lang,
                                "translated_text": "",
                                "status": "failed",
                                "warnings": _payload_list(row, "warnings") + ["translated_text is blank."],
                            }
                        )
                        failed += 1
                    else:
                        skipped += 1
                    continue
                savable.append(
                    {
                        **row,
                        "source_id": source_id,
                        "scope_type": "segment",
                        "scope_ref": segment.segment_id,
                        "segment_id": segment.segment_id,
                        "page": segment.page,
                        "source_hash": segment.text_hash,
                        "source_text": segment.text,
                        "target_lang": target_lang,
                        "translated_text": translated_text,
                    }
                )
                saved += 1
        if savable:
            upsert_paper_translations(profile, source_id, savable)
        summary = _visible_translation_summary(
            scope=scope,
            requested_pages=requested_pages,
            segments_selected=len(segment_payloads),
            ai_rows=len(translations),
            saved=saved,
            failed=failed,
            skipped=skipped,
            target_lang=target_lang,
        )
        if saved:
            message = f"Saved {saved} translation row(s)."
        elif failed:
            message = f"Saved {failed} failed translation row(s)."
        else:
            message = "No translation rows were saved."
        return ReaderActionResult(
            data={"structured": ai_result.structured or {}, "summary": summary, "saved": saved},
            warnings=warnings,
            message=message,
        )

    if action in {TRANSLATE_SELECTION, "translate_segment"}:
        selected_text = _selection_text(payload, segment_rows)
        target_lang = _payload_text(payload, "target_lang", "language") or "zh"
        translation_payload = dict(payload)
        if action == TRANSLATE_SELECTION and selected_text:
            for key in ("segment_refs", "segment_ids", "segment_id", "scope_refs", "scope_ref"):
                translation_payload.pop(key, None)
        segment_refs = set(_payload_list(translation_payload, "segment_refs", "segment_ids", "segment_id"))
        segments = _selection_segments(translation_payload, segment_rows)
        if not segments:
            raise ValueError("Reader translation needs selected text or segment refs.")
        ai_result = translate_paper_segments(
            ctx.profile_name,
            source_id,
            segments,
            target_lang=target_lang,
            require_review=False,
        )
        translations = []
        if isinstance(ai_result.structured, dict):
            translations = [row for row in ai_result.structured.get("translations", []) if isinstance(row, dict)]
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
            upsert_paper_translations(profile, source_id, savable)
        return ReaderActionResult(
            data={"structured": ai_result.structured or {}, "saved": len(savable)},
            warnings=list(ai_result.warnings),
            message="Saved" if savable else "",
        )

    if action == EXPLAIN_SELECTION:
        selected_text = _selection_text(payload, segment_rows)
        if not selected_text:
            raise ValueError("Reader explanation needs selected text or segment refs.")
        ai_result = explain_paper_selection(
            ctx.profile_name,
            source_id,
            selected_text,
            payload={
                "page": _payload_int(payload, "page"),
                "locator": _payload_text(payload, "locator"),
                "segments": _context_segments(payload, segment_rows, limit=8),
                "annotations": [row.to_dict() for row in annotation_rows[:20]],
            },
        )
        return ReaderActionResult(
            data={"structured": ai_result.structured or {}},
            warnings=list(ai_result.warnings),
        )

    if action == ASK_PAPER:
        question = _payload_text(payload, "question", "prompt", "text")
        if not question:
            raise ValueError("Reader question cannot be blank.")
        ai_result = answer_paper_question(
            ctx.profile_name,
            source_id,
            question,
            payload={
                "segments": _context_segments(payload, segment_rows, limit=30),
                "annotations": [row.to_dict() for row in annotation_rows[:30]],
                "chunks": [row.to_dict() for row in chunk_rows[:30]],
            },
        )
        return ReaderActionResult(
            data={"structured": ai_result.structured or {}},
            warnings=list(ai_result.warnings),
        )

    if action == "generate_review_card":
        source = load_research_sources(profile).by_id().get(source_id)
        ai_result = generate_paper_review_card(
            ctx.profile_name,
            source_id,
            source=source.to_dict() if source is not None else {"id": source_id},
            segments=[row.to_dict() for row in segment_rows],
            chunks=[row.to_dict() for row in chunk_rows],
            annotations=[row.to_dict() for row in annotation_rows],
            require_review=False,
        )
        if isinstance(ai_result.structured, dict):
            save_paper_analysis(profile, source_id, ai_result.structured)
        return ReaderActionResult(
            data={
                "structured": ai_result.structured or {},
                "analysis": load_paper_analysis(profile, source_id),
            },
            warnings=list(ai_result.warnings),
            message="Saved" if isinstance(ai_result.structured, dict) else "",
        )

    if action == "request_page_previews":
        pages = clean_page_list(payload.get("pages") or payload.get("visible_pages"))
        return ReaderActionResult(data={"pages": pages})

    if action in {"selection_created", "page_changed", "viewport_changed", "reader_state_changed", "request_reader_context"}:
        return ReaderActionResult(data={"ignored": True})

    raise ValueError(f"Unsupported reader action: {action}")
