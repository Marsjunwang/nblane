"""Paper Library workspace payloads and events shared by Streamlit and FastAPI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote, urlparse
from typing import Any

from nblane.core.auth import mint_reader_token
from nblane.core.profile_io import profile_dir
from nblane.core.research_papers import (
    auto_chunk_paper,
    build_paper_delete_preview,
    create_paper_library_node,
    delete_paper_pdf_asset,
    delete_paper_reader_artifacts,
    delete_paper_record,
    ensure_paper_pdf_downloaded,
    ensure_paper_reading_artifacts,
    load_paper_annotations,
    load_paper_library_tree,
    load_paper_pages,
    load_paper_segments,
    load_paper_translations,
    move_papers_to_node,
    paper_library_paths,
    paper_rows,
    position_paper_library_node,
    purge_discarded_papers,
    purge_paper_library_node,
    remove_papers_from_node,
    rename_paper_library_node,
    reorder_paper_library_node,
    restore_paper_library_node,
    trash_paper_library_node,
    translate_full_paper,
    validate_paper_library,
)
from nblane.core.research_sources import (
    SOURCE_STATUSES,
    load_research_sources,
    save_research_sources,
    update_research_source,
)
from nblane.core.research_workspace import load_chunks


LIBRARY_VIEW_LABELS: dict[str, str] = {
    "all": "All Papers",
    "unsorted": "Unsorted Inbox",
    "recent": "Recently Read",
    "reading": "Reading",
    "no_pdf": "PDF Missing",
    "needs_extraction": "Needs Extraction",
    "claims_need_review": "Claims Need Review",
    "duplicate_risk": "Duplicate Risk",
    "stale_translation": "Stale Translation",
    "private": "Private Sources",
    "reviewed": "Reviewed",
    "archived": "Archived",
    "discarded": "Discarded",
}

LIBRARY_VIEW_GROUPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("library", "Library", ("all", "unsorted", "recent")),
    (
        "work_queue",
        "Work Queue",
        (
            "reading",
            "no_pdf",
            "needs_extraction",
            "claims_need_review",
            "duplicate_risk",
            "stale_translation",
        ),
    ),
    ("system", "System", ("private", "reviewed", "archived", "discarded")),
)

TECHNICAL_TAXONOMY_LABELS: tuple[tuple[str, str], ...] = (
    ("topics", "Topics"),
    ("methods", "Methods"),
    ("datasets", "Datasets"),
    ("benchmarks", "Benchmarks"),
)

PAPER_LIBRARY_RUNTIME_ENV = "NBLANE_PAPER_LIBRARY_RUNTIME"
PAPER_LIBRARY_RUNTIME_DEFAULT = "fastapi_iframe"
PAPER_LIBRARY_RUNTIMES = ("streamlit_component", "fastapi_link", "fastapi_iframe")
_PAPER_LIBRARY_RUNTIME_ALIASES = {
    "streamlit": "streamlit_component",
    "component": "streamlit_component",
    "streamlit_component": "streamlit_component",
    "fastapi": "fastapi_iframe",
    "link": "fastapi_link",
    "fastapi_link": "fastapi_link",
    "iframe": "fastapi_iframe",
    "fastapi_iframe": "fastapi_iframe",
}


@dataclass
class PaperLibraryEventResult:
    """Structured response for Paper Library mutations and navigation events."""

    ok: bool = True
    message: str = "Saved"
    changed: dict[str, list[str]] = field(default_factory=dict)
    next: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": bool(self.ok),
            "message": self.message,
            "changed": {key: list(value) for key, value in self.changed.items()},
            "next": dict(self.next),
            "warnings": list(self.warnings),
            "data": dict(self.data),
        }


def _profile_root(profile: str | Path) -> Path:
    if isinstance(profile, Path):
        return profile
    raw = str(profile or "").strip()
    candidate = Path(raw)
    if raw and ("/" in raw or raw.startswith(".") or candidate.exists()):
        return candidate
    return profile_dir(raw)


def _profile_name(profile: str | Path) -> str:
    if isinstance(profile, Path):
        return profile.name
    raw = str(profile or "").strip()
    return Path(raw).name if "/" in raw else raw


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _clean_return_url(value: object) -> str:
    clean = _clean_text(value)
    if not clean:
        return ""
    if clean.startswith("/") and not clean.startswith("//"):
        return clean
    parsed = urlparse(clean)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return clean
    return ""


def resolve_paper_library_runtime(value: object | None = None) -> tuple[str, str]:
    """Return the selected Paper Library runtime and the invalid raw value, if any."""

    raw = _clean_text(os.getenv(PAPER_LIBRARY_RUNTIME_ENV) if value is None else value)
    if not raw:
        return PAPER_LIBRARY_RUNTIME_DEFAULT, ""
    normalized = raw.lower().replace("-", "_").strip()
    runtime = _PAPER_LIBRARY_RUNTIME_ALIASES.get(normalized)
    if runtime:
        return runtime, ""
    return PAPER_LIBRARY_RUNTIME_DEFAULT, raw


def _clean_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.replace("\n", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        raw = []
        for item in value:
            if isinstance(item, str):
                raw.extend(item.replace("\n", ",").split(","))
            else:
                raw.append(str(item))
    else:
        raw = [str(value)]
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        clean = _clean_text(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _int_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _bool_value(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    clean = _clean_text(value).lower()
    if clean in {"1", "true", "yes", "on"}:
        return True
    if clean in {"0", "false", "no", "off"}:
        return False
    return default


def _summarize_extraction_result(summaries: list[dict[str, object]]) -> str:
    if not summaries:
        return "No papers selected for extraction."
    ready_count = sum(1 for item in summaries if bool(item.get("ready")))
    warning_count = sum(len(item.get("warnings") or []) for item in summaries)
    if len(summaries) == 1:
        summary = summaries[0]
        pages = _int_value(summary.get("pages"))
        segments = _int_value(summary.get("segments"))
        if summary.get("ready"):
            status = _clean_text(summary.get("status"))
            backend = _clean_text(summary.get("structure_backend"))
            if status == "fallback" or (backend and backend != "grobid"):
                message = f"Fallback text ready: {pages} page(s), {segments} segment(s)."
            else:
                message = f"Extraction ready: {pages} page(s), {segments} segment(s)."
        else:
            status = _clean_text(summary.get("status")) or "failed"
            message = f"Extraction did not complete: {status.replace('_', ' ')}."
    else:
        message = f"Extraction finished for {len(summaries)} papers: {ready_count} ready."
    if warning_count:
        message += f" {warning_count} warning(s) need attention."
    return message


def _summarize_translation_result(summaries: list[dict[str, object]]) -> str:
    if not summaries:
        return "No papers selected for translation."
    updated = sum(_int_value(item.get("updated")) for item in summaries)
    stale = sum(_int_value(item.get("stale")) for item in summaries)
    missing = sum(_int_value(item.get("missing")) for item in summaries)
    failed = sum(_int_value(item.get("failed")) for item in summaries)
    warning_count = sum(len(item.get("warnings") or []) for item in summaries)
    message = f"Translation retry finished: updated {updated} row(s); {stale} stale remaining."
    if missing:
        message += f" {missing} missing."
    if failed:
        message += f" {failed} failed."
    if warning_count:
        message += f" {warning_count} warning(s) need attention."
    return message


def _short_text(value: object, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _status_label(value: object) -> str:
    clean = _clean_text(value)
    return clean.replace("_", " ").title() if clean else ""


def _reader_view_url(
    profile: str | Path,
    source_id: str,
    *,
    user_id: str = "local",
    reader_base: str = "",
) -> str:
    token = mint_reader_token(user_id, _profile_name(profile), source_id)
    encoded_source = quote(source_id, safe="")
    encoded_token = quote(token, safe="")
    base = (reader_base or os.getenv("NBLANE_READER_API_BASE", "")).strip().rstrip("/")
    path = f"/reader/view/{encoded_source}?token={encoded_token}"
    return f"{base}{path}" if base else path


def _metadata_abstract(metadata: dict[str, object]) -> str:
    for key in ("abstract", "abstract_text", "paper_abstract", "description"):
        clean = _clean_text(metadata.get(key))
        if clean:
            return clean
    return ""


def _paper_reading_card(source: Any, row: dict[str, object], metadata: dict[str, object]) -> dict[str, object]:
    reading = getattr(source, "reading", None)
    candidates = [
        ("abstract", "Abstract", _metadata_abstract(metadata)),
        ("summary", "Summary", _clean_text(getattr(source, "summary", "")) or _clean_text(row.get("summary"))),
        ("reading_summary", "Reading summary", _clean_text(getattr(reading, "summary", ""))),
        ("notes", "Notes", _clean_text(getattr(source, "notes", "")) or _clean_text(row.get("notes"))),
    ]
    source_key = ""
    source_label = ""
    body = ""
    for key, label, value in candidates:
        clean = _clean_text(value)
        if clean:
            source_key = key
            source_label = label
            body = clean
            break
    why_relevant = _clean_text(
        metadata.get("why_relevant")
        or metadata.get("relevance_reason")
        or metadata.get("import_reason")
        or metadata.get("paper_search_reason")
    )
    return {
        "title": "Abstract Preview",
        "source": source_key,
        "source_label": source_label,
        "body": body,
        "why_relevant": why_relevant,
        "empty": not bool(body),
        "empty_message": "No abstract or summary yet.",
    }


def _paper_primary_meta(row: dict[str, object]) -> str:
    parts = [
        _clean_text(row.get("authors")),
        _clean_text(row.get("published")),
        _clean_text(row.get("tree_path")),
    ]
    return " · ".join(part for part in parts if part)


def _library_row_matches_view(row: dict[str, object], view: str) -> bool:
    source = row.get("source")
    badges = {str(item) for item in row.get("badges", [])}
    status = _clean_text(row.get("status"))
    visibility = _clean_text(row.get("visibility"))
    if view == "all":
        return True
    if view == "unsorted":
        return _clean_text(row.get("tree_path")) == "Unsorted" or "Unsorted" in badges
    if view in {"reading", "archived", "discarded"}:
        return status == view
    if view == "candidate_ready":
        return status == "candidate_ready" or "AI candidates" in badges
    if view == "no_pdf":
        return not bool(row.get("has_pdf"))
    if view == "needs_extraction":
        return bool(row.get("has_pdf")) and (
            "Needs structured extraction" in badges
        )
    if view == "claims_need_review":
        return status == "candidate_ready" or "AI candidates" in badges
    if view == "duplicate_risk":
        return "Duplicate risk" in badges
    if view == "stale_translation":
        return "Stale translation" in badges
    if view == "recent":
        return bool(row.get("last_read"))
    if view == "private":
        return visibility == "private"
    if view == "reviewed":
        return status == "summarized" or bool(getattr(source, "evidence_refs", []))
    return True


def _library_view_count(rows: list[dict[str, object]], view: str) -> int:
    return sum(1 for row in rows if _library_row_matches_view(row, view))


def _paper_node_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        source = row.get("source")
        for ref in getattr(source, "library_node_refs", []) or []:
            clean = _clean_text(ref)
            if clean:
                counts[clean] = counts.get(clean, 0) + 1
    return counts


def _paper_collection_tree_items(profile: str | Path, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    tree = load_paper_library_tree(profile)
    counts = _paper_node_counts(rows)
    paths = paper_library_paths(profile)
    children: dict[str, list[Any]] = {}
    trash_children: dict[str, list[Any]] = {}
    trashed_ids = {node.id for node in tree.nodes if node.status == "trashed"}
    for node in tree.nodes:
        if node.status == "trashed":
            parent_id = node.parent_id if node.parent_id in trashed_ids else ""
            trash_children.setdefault(parent_id, []).append(node)
            continue
        children.setdefault(node.parent_id or "", []).append(node)

    def walk(parent_id: str = "", *, source: dict[str, list[Any]] | None = None, item_type: str = "collection") -> list[dict[str, object]]:
        source = source or children
        out: list[dict[str, object]] = []
        for node in sorted(source.get(parent_id, []), key=lambda item: (item.order, item.title.lower(), item.id)):
            out.append(
                {
                    "id": node.id,
                    "type": item_type,
                    "title": node.title,
                    "path": paths.get(node.id, node.title),
                    "description": node.description,
                    "count": counts.get(node.id, 0),
                    "parent_id": node.parent_id,
                    "color": node.color,
                    "icon": node.icon,
                    "status": node.status,
                    "trashed_at": node.trashed_at,
                    "children": walk(node.id, source=source, item_type=item_type),
                }
            )
        return out

    items: list[dict[str, object]] = [
        {
            "id": "collections:all",
            "type": "collection_root",
            "node_id": "",
            "title": "All collections",
            "count": len(rows),
            "children": walk(""),
        }
    ]
    if trashed_ids:
        items.append(
            {
                "id": "collections:trash",
                "type": "collection_trash_root",
                "node_id": "",
                "title": "Trash",
                "count": len(trashed_ids),
                "children": walk("", source=trash_children, item_type="collection_trash"),
            }
        )
    return items


def filter_paper_library_rows(
    rows: list[dict[str, object]],
    *,
    query: str = "",
    sort_mode: str = "recent",
) -> list[dict[str, object]]:
    """Filter and sort display-ready paper rows for the Library workbench."""

    clean_query = _clean_text(query).lower()
    if clean_query:
        rows = [
            row
            for row in rows
            if clean_query
            in " ".join(
                [
                    _clean_text(row.get("title")),
                    _clean_text(row.get("authors")),
                    _clean_text(row.get("published")),
                    _clean_text(row.get("venue")),
                    _clean_text(row.get("tree_path")),
                    _clean_text(row.get("summary")),
                    _clean_text(row.get("notes")),
                    " ".join(str(tag) for tag in row.get("tags", [])),
                    " ".join(str(badge) for badge in row.get("badges", [])),
                ]
            ).lower()
        ]
    if sort_mode == "title":
        return sorted(rows, key=lambda row: _clean_text(row.get("title")).lower())
    if sort_mode == "status":
        return sorted(rows, key=lambda row: (_clean_text(row.get("status")), _clean_text(row.get("title")).lower()))
    if sort_mode == "claims":
        return sorted(rows, key=lambda row: int(row.get("claims_count") or 0), reverse=True)
    if sort_mode == "added":
        return sorted(rows, key=lambda row: _clean_text(getattr(row.get("source"), "captured_at", "")), reverse=True)
    return sorted(rows, key=lambda row: _clean_text(row.get("last_read")), reverse=True)


def _paper_component_rows(
    profile: str | Path,
    rows: list[dict[str, object]],
    *,
    user_id: str,
    reader_base: str,
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in rows:
        source_id = _clean_text(row.get("id"))
        if not source_id:
            continue
        status = _clean_text(row.get("status"))
        has_pdf = bool(row.get("has_pdf"))
        out.append(
            {
                "id": source_id,
                "title": _clean_text(row.get("title")) or source_id,
                "status": status,
                "status_label": _status_label(status),
                "tree_path": _clean_text(row.get("tree_path")) or "Unsorted",
                "meta": _paper_primary_meta(row),
                "summary": _short_text(row.get("summary") or row.get("notes"), 220),
                "badges": [str(item) for item in row.get("badges", []) if _clean_text(item)],
                "tags": [str(item) for item in row.get("tags", []) if _clean_text(item)],
                "reader_url": _reader_view_url(profile, source_id, user_id=user_id, reader_base=reader_base) if has_pdf else "",
                "has_pdf": has_pdf,
                "open_access_pdf_url": _clean_text(row.get("open_access_pdf_url")),
                "pdf_download_status": _clean_text(row.get("pdf_download_status")),
                "pdf_download_error": _clean_text(row.get("pdf_download_error")),
                "metrics": " · ".join(
                    [
                        f"Annotations: {row.get('annotations_count', 0)}",
                        f"Chunk refs: {row.get('chunks_count', 0)}",
                        f"Research claims: {row.get('claims_count', 0)}",
                        f"Research citations: {row.get('citations_count', 0)}",
                    ]
                ),
            }
        )
    return out


def _paper_detail_payload(
    profile: str | Path,
    detail_id: str,
    rows: list[dict[str, object]],
    all_rows: list[dict[str, object]],
    *,
    user_id: str,
    reader_base: str,
) -> dict[str, object]:
    candidates = rows or all_rows
    clean_detail = _clean_text(detail_id)
    row = next((item for item in candidates if _clean_text(item.get("id")) == clean_detail), None)
    if row is None:
        row = next((item for item in all_rows if _clean_text(item.get("id")) == clean_detail), None)
    if row is None and candidates:
        row = candidates[0]
    if row is None:
        return {}

    source = row.get("source")
    source_id = _clean_text(row.get("id"))
    source_metadata = dict(getattr(source, "metadata", {}) or {})
    annotations = load_paper_annotations(profile, source_id)
    translations = load_paper_translations(profile, source_id)
    pages = load_paper_pages(profile, source_id)
    segments = load_paper_segments(profile, source_id)
    chunks = load_chunks(_profile_root(profile), source_id)
    has_pdf = bool(source_metadata.get("pdf_asset_ref"))
    reader_url = _reader_view_url(profile, source_id, user_id=user_id, reader_base=reader_base) if has_pdf else ""
    open_access_pdf_url = _clean_text(
        source_metadata.get("open_access_pdf_url")
        or source_metadata.get("pdf_url")
        or row.get("open_access_pdf_url")
    )
    pdf_download_status = _clean_text(source_metadata.get("pdf_download_status") or row.get("pdf_download_status"))
    pdf_download_error = _clean_text(source_metadata.get("pdf_download_error") or row.get("pdf_download_error"))
    collection_refs = list(getattr(source, "library_node_refs", []) or [])

    return {
        "id": source_id,
        "source_id": source_id,
        "title": _clean_text(getattr(source, "title", "")) or _clean_text(row.get("title")) or source_id,
        "meta": _paper_primary_meta(row),
        "summary": _clean_text(getattr(source, "summary", "")) or _clean_text(row.get("summary")),
        "notes": _clean_text(getattr(source, "notes", "")) or _clean_text(row.get("notes")),
        "abstract": _metadata_abstract(source_metadata),
        "reading_card": _paper_reading_card(source, row, source_metadata),
        "url": _clean_text(getattr(source, "url", "")) or _clean_text(row.get("url")),
        "status": _clean_text(getattr(source, "status", "")) or _clean_text(row.get("status")),
        "status_label": _status_label(getattr(source, "status", "") or row.get("status")),
        "visibility": _clean_text(getattr(source, "visibility", "")) or _clean_text(row.get("visibility")),
        "tags": list(getattr(source, "tags", []) or row.get("tags", []) or []),
        "badges": [str(item) for item in row.get("badges", []) if _clean_text(item)],
        "reader_url": reader_url,
        "has_pdf": has_pdf,
        "open_access_pdf_url": open_access_pdf_url,
        "pdf_download": {
            "status": pdf_download_status,
            "error": pdf_download_error,
            "attempted_at": _clean_text(source_metadata.get("pdf_download_attempted_at")),
            "url": open_access_pdf_url,
        },
        "primary_node_id": collection_refs[0] if collection_refs else "",
        "collection_refs": collection_refs,
        "tree_path": _clean_text(row.get("tree_path")) or "Unsorted",
        "metrics": [
            {"label": "PDF", "value": "ready" if has_pdf else "missing"},
            {"label": "Last page", "value": _clean_text(source_metadata.get("last_read_page")) or "-"},
            {"label": "Segments", "value": len(segments)},
            {"label": "Annotations", "value": len([ann for ann in annotations if ann.status == "active"])},
            {"label": "Research claims", "value": int(row.get("claims_count") or 0)},
            {"label": "Research citations", "value": int(row.get("citations_count") or 0)},
        ],
        "artifacts": {
            "pdf_asset_ref": _clean_text(source_metadata.get("pdf_asset_ref")),
            "open_access_pdf_url": open_access_pdf_url,
            "pdf_download_status": pdf_download_status,
            "pdf_download_error": pdf_download_error,
            "pdf_download_attempted_at": _clean_text(source_metadata.get("pdf_download_attempted_at")),
            "pages": _clean_text(source_metadata.get("page_count")) or len(pages),
            "segments": len(segments),
            "chunks": len(chunks),
            "translations": len(translations),
            "structure_backend": _clean_text(source_metadata.get("structure_backend")),
            "grobid_service": (
                "available"
                if source_metadata.get("grobid_available") is True
                else _clean_text(source_metadata.get("grobid_status"))
            ),
            "grobid_last_error": _clean_text(source_metadata.get("grobid_last_error")),
            "grobid_last_failed_at": _clean_text(source_metadata.get("grobid_last_failed_at")),
            "structured_extracted_at": _clean_text(source_metadata.get("structured_extracted_at")),
        },
    }


def _labels() -> dict[str, str]:
    return {
        "add_selected_here": "Add selected papers here",
        "add_to_collection": "Add to collection",
        "archive": "Archive",
        "auto_chunk": "Auto chunk",
        "attach_pdf": "Attach PDF",
        "back_to_overview": "Back to Overview",
        "cancel": "Cancel",
        "collapse": "Collapse",
        "collapse_all": "Collapse all",
        "collection_actions": "Collection actions",
        "collection_title": "Collection title",
        "delete_collection": "Delete collection",
        "discard": "Mark as discarded",
        "danger_zone": "Danger zone",
        "delete_paper": "Delete paper...",
        "delete_paper_confirm": "Type the source id to confirm deletion.",
        "delete_pdf_asset": "Delete PDF asset",
        "delete_reader_artifacts": "Delete extracted reader artifacts",
        "delete_paper_blocked": "Deletion blocked by references.",
        "download_pdf": "Download PDF",
        "downloading_pdf": "Downloading PDF...",
        "expand": "Expand",
        "expand_all": "Expand all",
        "mark_as_reading": "Mark as reading",
        "move_collection": "Move collection",
        "move_down": "Move down",
        "move_papers_to_collection": "Move papers to collection",
        "move_papers_to_parent": "Move papers to parent collection",
        "move_papers_to_unsorted": "Move papers to Unsorted Inbox",
        "move_selected_here": "Move selected papers here",
        "move_to_collection": "Move to collection",
        "move_up": "Move up",
        "new_collection": "New collection",
        "new_subcollection": "New subcollection",
        "abstract_preview": "Abstract Preview",
        "no_abstract_preview": "No abstract or summary yet.",
        "preview_source": "From {source}",
        "why_relevant": "Why it matters",
        "open_reader": "Open Reader",
        "open_remote_pdf": "Open remote PDF",
        "paper_policy": "Paper policy",
        "parent_collection": "Parent collection",
        "purge_collection": "Purge forever",
        "quick_actions": "Quick actions",
        "reader_tab": "Reader tab (fallback)",
        "remove_from_current_collection": "Remove from current collection",
        "rename": "Rename",
        "rename_paper": "Rename paper...",
        "paper_title": "Paper title",
        "force_grobid_upgrade": "Force GROBID upgrade",
        "force_grobid_upgrade_hint": "Retry GROBID even when a recent timeout is cooling down.",
        "restore_collection": "Restore collection",
        "run_extraction": "Run extraction",
        "run_extraction_hint": "Prepare reader artifacts and reuse fallback text after recent GROBID timeouts.",
        "running_grobid_upgrade": "Upgrading with GROBID...",
        "running_extraction": "Running extraction...",
        "save": "Save",
        "search_collections": "Search collections",
        "selected_papers": "{count} papers selected",
        "bulk_select": "Bulk select",
        "select_all": "Select all",
        "clear_selection": "Clear",
        "select_paper": "Select paper",
        "show_details": "Show details",
        "library_empty": "No papers match this view.",
        "library_result_count": "{count} papers",
        "overview_suggested_action": "Suggested from Overview",
        "claims_focus": "Claims",
        "claims_focus_hint": "Review AI candidates and promoted evidence for this paper.",
        "dedupe": "Review duplicates",
        "fix_citations": "Fix citations",
        "metadata_focus": "Metadata",
        "metadata_focus_hint": "Check title, collection placement, duplicate risk, and source metadata.",
        "review_claims": "Review claims",
        "review_metadata": "Review metadata",
        "review_visibility": "Review visibility",
        "artifact_pdf_asset_ref": "PDF asset",
        "artifact_pages": "Pages",
        "artifact_segments": "Segments",
        "artifact_chunks": "Research chunks",
        "artifact_translations": "Translations",
        "artifact_structure_backend": "Structure backend",
        "artifact_grobid_service": "GROBID service",
        "artifact_grobid_last_error": "Last GROBID error",
        "artifact_grobid_last_failed_at": "Last GROBID failure",
        "artifact_structured_extracted_at": "Structured extracted at",
        "retry_translation": "Retry translation",
        "retry_pdf_download": "Retry PDF",
        "retrying_translation": "Retrying translation...",
        "translate_full_paper": "Translate full paper",
        "translate_grobid_text": "GROBID paragraphs",
        "translation_mode": "Translation mode",
        "translation_mode_fast_body": "Fast body",
        "translation_mode_full_paper": "Full paper",
        "translation_mode_grobid_text": "GROBID paragraphs",
        "upload_pdf": "Upload PDF",
        "safety_focus": "Publish safety",
        "safety_focus_hint": "Check visibility and private-source blockers before export.",
        "translations_focus": "Translations",
        "translations_focus_hint": "Refresh stale translation rows after extraction or segment changes.",
        "target_collection": "Target collection",
        "top_level": "Top level",
    }


def build_paper_library_payload(
    profile: str | Path,
    *,
    current_view: str = "all",
    current_node: str = "",
    query: str = "",
    sort_mode: str = "recent",
    selected_paper_ids: list[str] | None = None,
    detail_id: str = "",
    focus: str = "",
    action: str = "",
    return_to: str = "",
    return_url: str = "",
    user_id: str = "local",
    reader_base: str = "",
) -> dict[str, object]:
    """Build the complete Paper Library workbench payload."""

    all_rows = paper_rows(profile, view="all")
    tree = load_paper_library_tree(profile)
    active_node_ids = {node.id for node in tree.nodes if node.status != "trashed"}
    if current_view not in LIBRARY_VIEW_LABELS:
        current_view = "all"
    if current_node and current_node not in active_node_ids:
        current_node = ""

    view_rows = (
        all_rows
        if current_view == "all" and not current_node
        else paper_rows(profile, view=current_view, node_id=current_node)
    )
    rows = filter_paper_library_rows(
        view_rows,
        query=query,
        sort_mode=sort_mode,
    )
    paper_ids = [_clean_text(row.get("id")) for row in rows if _clean_text(row.get("id"))]
    clean_detail = _clean_text(detail_id)
    if clean_detail not in paper_ids and paper_ids:
        clean_detail = paper_ids[0]
    clean_focus = _clean_text(focus)
    clean_action = _clean_text(action)
    clean_return_to = _clean_text(return_to)
    clean_return_url = _clean_return_url(return_url)

    paths = paper_library_paths(profile)
    active_label = LIBRARY_VIEW_LABELS.get(current_view, current_view)
    if current_node:
        active_label = paths.get(current_node, current_node)

    def view_items(view_ids: tuple[str, ...]) -> list[dict[str, object]]:
        return [
            {
                "id": view_id,
                "type": "view",
                "title": LIBRARY_VIEW_LABELS.get(view_id, view_id),
                "count": _library_view_count(all_rows, view_id),
            }
            for view_id in view_ids
        ]

    return {
        "profile": _profile_name(profile),
        "active_view": current_view,
        "active_node_id": current_node,
        "active_label": active_label,
        "query": query,
        "sort_mode": sort_mode,
        "detail_id": clean_detail,
        "focus": clean_focus,
        "action": clean_action,
        "return_to": clean_return_to,
        "return_url": clean_return_url,
        "deep_link": {
            "focus": clean_focus,
            "action": clean_action,
            "return_to": clean_return_to,
            "return_url": clean_return_url,
        },
        "selected_paper_ids": list(selected_paper_ids or []),
        "metrics": {
            "papers": len(all_rows),
            "reading": _library_view_count(all_rows, "reading"),
            "no_pdf": _library_view_count(all_rows, "no_pdf"),
            "needs_extraction": _library_view_count(all_rows, "needs_extraction"),
            "claims_need_review": _library_view_count(all_rows, "claims_need_review"),
        },
        "papers": _paper_component_rows(profile, rows, user_id=user_id, reader_base=reader_base),
        "detail": _paper_detail_payload(
            profile,
            clean_detail,
            rows,
            all_rows,
            user_id=user_id,
            reader_base=reader_base,
        ),
        "sections": [
            {
                "id": "library",
                "title": "Library",
                "items": view_items(LIBRARY_VIEW_GROUPS[0][2]),
            },
            {
                "id": "collections",
                "title": "Collections",
                "items": _paper_collection_tree_items(profile, all_rows),
            },
            {
                "id": "technical_taxonomy",
                "title": "Technical Taxonomy",
                "items": [
                    {
                        "id": f"technical:{taxonomy_id}",
                        "type": "taxonomy",
                        "title": fallback,
                        "count": 0,
                    }
                    for taxonomy_id, fallback in TECHNICAL_TAXONOMY_LABELS
                ],
            },
            {
                "id": "work_queue",
                "title": "Work Queue",
                "items": view_items(LIBRARY_VIEW_GROUPS[1][2]),
            },
            {
                "id": "system",
                "title": "System",
                "items": view_items(LIBRARY_VIEW_GROUPS[2][2]),
            },
        ],
        "capabilities": {
            "create_collection": True,
            "rename_collection": True,
            "rename_papers": True,
            "move_collection": True,
            "delete_collection": True,
            "restore_collection": True,
            "purge_collection": True,
            "drop_papers": True,
            "delete_papers": True,
        },
        "diagnostics": validate_paper_library(profile),
        "labels": _labels(),
    }


def handle_paper_library_event(
    profile: str | Path,
    event: dict[str, object],
    *,
    selected_paper_ids: list[str] | None = None,
    progress_callback: Any | None = None,
) -> PaperLibraryEventResult:
    """Apply one Paper Library UI event and return a structured result."""

    if not isinstance(event, dict):
        return PaperLibraryEventResult(ok=False, message="Invalid Paper Library event.")
    action = _clean_text(event.get("action"))
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    state = event.get("state") if isinstance(event.get("state"), dict) else {}

    def event_paper_ids() -> list[str]:
        return _clean_list(payload.get("paper_ids")) or list(selected_paper_ids or [])

    changed: dict[str, list[str]] = {}
    next_state: dict[str, str] = {}
    message = "Saved"
    warnings: list[str] = []
    data: dict[str, Any] = {}

    def emit_progress(update: dict[str, object]) -> None:
        if progress_callback is None:
            return
        try:
            progress_callback(update)
        except Exception:
            return

    if action == "paper_library_select_view":
        next_state = {
            "view": _clean_text(payload.get("view_id")) or "all",
            "node_id": "",
            "detail_id": "",
        }
        return PaperLibraryEventResult(message="", changed=changed, next=next_state)
    if action == "paper_library_select_collection":
        next_state = {
            "view": "all",
            "node_id": _clean_text(payload.get("node_id")),
            "detail_id": "",
        }
        return PaperLibraryEventResult(message="", changed=changed, next=next_state)
    if action == "paper_library_select_paper":
        next_state = {"detail_id": _clean_text(payload.get("source_id"))}
        return PaperLibraryEventResult(message="", changed=changed, next=next_state)
    if action == "paper_library_sync_reader_tab":
        source_id = _clean_text(payload.get("source_id"))
        next_state = {"reader_source_id": source_id, "detail_id": source_id}
        return PaperLibraryEventResult(message="Selected for the Reader tab.", next=next_state)
    if action == "paper_library_delete_paper_preview":
        preview = build_paper_delete_preview(_profile_root(profile), event_paper_ids())
        return PaperLibraryEventResult(message="", data={"delete_preview": preview})

    if action == "paper_library_create_collection":
        node = create_paper_library_node(
            profile,
            _clean_text(payload.get("title")),
            parent_id=_clean_text(payload.get("parent_id")),
        )
        changed["nodes"] = [node.id]
    elif action == "paper_library_rename_collection":
        node = rename_paper_library_node(
            profile,
            _clean_text(payload.get("node_id")),
            _clean_text(payload.get("title")),
        )
        changed["nodes"] = [node.id]
    elif action == "paper_library_move_collection":
        node = position_paper_library_node(
            profile,
            _clean_text(payload.get("node_id")),
            parent_id=_clean_text(payload.get("parent_id")),
            before_node_id=_clean_text(payload.get("before_node_id")),
            after_node_id=_clean_text(payload.get("after_node_id")),
        )
        changed["nodes"] = [node.id]
    elif action == "paper_library_reorder_collection":
        node = reorder_paper_library_node(
            profile,
            _clean_text(payload.get("node_id")),
            _clean_text(payload.get("direction")) or "down",
        )
        changed["nodes"] = [node.id]
    elif action == "paper_library_trash_collection":
        node = trash_paper_library_node(
            profile,
            _clean_text(payload.get("node_id")),
            paper_policy=_clean_text(payload.get("paper_policy")) or "move_to_parent",
        )
        changed["nodes"] = [node.id]
    elif action == "paper_library_purge_collection":
        node = purge_paper_library_node(
            profile,
            _clean_text(payload.get("node_id")),
            paper_policy=_clean_text(payload.get("paper_policy")) or "move_to_unsorted",
        )
        changed["nodes"] = [node.id]
    elif action == "paper_library_restore_collection":
        node = restore_paper_library_node(profile, _clean_text(payload.get("node_id")))
        changed["nodes"] = [node.id]
    elif action in {
        "paper_library_add_selected_papers_to_collection",
        "paper_library_move_selected_papers_to_collection",
        "paper_library_drop_papers_to_collection",
    }:
        source_ids = event_paper_ids()
        changed["sources"] = move_papers_to_node(
            profile,
            source_ids,
            _clean_text(payload.get("node_id")),
            append=action == "paper_library_add_selected_papers_to_collection" or bool(payload.get("append")),
        )
    elif action == "paper_library_remove_papers_from_collection":
        changed["sources"] = remove_papers_from_node(
            profile,
            event_paper_ids(),
            _clean_text(payload.get("node_id")),
        )
    elif action == "paper_library_update_papers_status":
        next_status = _clean_text(payload.get("status"))
        if next_status not in SOURCE_STATUSES:
            raise ValueError(f"Unknown source status: {next_status}")
        inbox = load_research_sources(_profile_root(profile))
        changed_sources: list[str] = []
        for source_id in event_paper_ids():
            update_research_source(inbox, source_id, status=next_status)
            changed_sources.append(source_id)
        if changed_sources:
            save_research_sources(_profile_root(profile), inbox)
        changed["sources"] = changed_sources
        verb = {
            "reading": "Marked as reading",
            "archived": "Archived",
            "discarded": "Discarded",
        }.get(next_status, f"Updated to {_status_label(next_status) or next_status}")
        noun = "paper" if len(changed_sources) == 1 else "papers"
        message = f"{verb} {len(changed_sources)} {noun}."
    elif action == "paper_library_rename_paper":
        source_id = _clean_text(payload.get("source_id")) or (event_paper_ids()[0] if event_paper_ids() else "")
        title = _clean_text(payload.get("title"))
        if not source_id:
            raise ValueError("source_id is required")
        if not title:
            raise ValueError("Paper title cannot be blank.")
        inbox = load_research_sources(_profile_root(profile))
        update_research_source(inbox, source_id, title=title)
        save_research_sources(_profile_root(profile), inbox)
        changed["sources"] = [source_id]
        next_state["detail_id"] = source_id
        message = "Renamed paper."
    elif action == "paper_library_download_pdf":
        changed_sources = []
        download_summaries: list[dict[str, object]] = []
        warnings = []
        for source_id in event_paper_ids():
            emit_progress(
                {
                    "phase": "pdf_download",
                    "source_id": source_id,
                    "message": "Downloading PDF.",
                }
            )
            summary = ensure_paper_pdf_downloaded(
                profile,
                source_id,
                error_prefix="PDF download failed",
            )
            download_summaries.append(summary)
            changed_sources.append(source_id)
            if _clean_text(summary.get("status")) != "downloaded":
                warning = _clean_text(summary.get("error")) or "PDF download did not complete."
                warnings.append(f"{source_id}: {warning}")
        changed["sources"] = changed_sources
        downloaded = sum(1 for summary in download_summaries if _clean_text(summary.get("status")) == "downloaded")
        failed = len(download_summaries) - downloaded
        if downloaded and failed:
            message = f"Downloaded {downloaded} PDF{'s' if downloaded != 1 else ''}; {failed} need attention."
        elif downloaded:
            message = f"Downloaded {downloaded} PDF{'s' if downloaded != 1 else ''}."
        else:
            message = "PDF download did not complete."
        if len(changed_sources) == 1:
            next_state["detail_id"] = changed_sources[0]
            next_state["focus"] = "artifacts"
            next_state["action"] = "" if downloaded else "attach_pdf"
        data = {"pdf_download_summaries": download_summaries}
    elif action == "paper_library_run_extraction":
        changed_sources: list[str] = []
        extraction_summaries: list[dict[str, object]] = []
        warnings: list[str] = []
        for source_id in event_paper_ids():
            emit_progress(
                {
                    "phase": "extraction",
                    "source_id": source_id,
                    "message": "Extracting reader artifacts.",
                }
            )
            summary = ensure_paper_reading_artifacts(
                _profile_root(profile),
                source_id,
                force_grobid=bool(payload.get("force_grobid")),
                progress_callback=progress_callback,
            )
            extraction_summaries.append(summary)
            changed_sources.append(source_id)
            warnings.extend(f"{source_id}: {warning}" for warning in summary.get("warnings", []) or [])
        changed["sources"] = changed_sources
        message = _summarize_extraction_result(extraction_summaries)
        if len(changed_sources) == 1:
            next_state["detail_id"] = changed_sources[0]
            stale_rows = [
                row
                for row in load_paper_translations(_profile_root(profile), changed_sources[0])
                if row.status == "stale"
            ]
            if stale_rows:
                next_state["focus"] = "translations"
                next_state["action"] = "retry_translation"
            elif _clean_text(state.get("action")) == "run_extraction":
                next_state["focus"] = "artifacts"
                next_state["action"] = ""
        data = {"extraction_summaries": extraction_summaries}
    elif action == "paper_library_retry_translation":
        changed_sources = []
        extraction_summaries = []
        translation_summaries: list[dict[str, object]] = []
        warnings: list[str] = []
        target_lang = _clean_text(payload.get("target_lang")) or "zh"
        mode = _clean_text(payload.get("mode")) or "missing_or_stale"
        scope_strategy = _clean_text(payload.get("scope_strategy")) or "structure"
        include_references = _bool_value(payload.get("include_references"), default=False)
        translation_variant = _clean_text(payload.get("translation_variant")) or (
            "full_paper" if include_references else "fast_body"
        )
        for source_id in event_paper_ids():
            emit_progress(
                {
                    "phase": "extraction",
                    "source_id": source_id,
                    "target_lang": target_lang,
                    "mode": mode,
                    "scope": scope_strategy,
                    "translation_variant": translation_variant,
                    "include_references": include_references,
                    "message": "Preparing reader artifacts before translation.",
                }
            )
            extraction_summary = ensure_paper_reading_artifacts(
                _profile_root(profile),
                source_id,
                target_lang=target_lang,
                force_grobid=bool(payload.get("force_grobid")),
                progress_callback=progress_callback,
            )
            extraction_summaries.append(extraction_summary)
            try:
                emit_progress(
                    {
                        "phase": "translation",
                        "source_id": source_id,
                        "target_lang": target_lang,
                        "mode": mode,
                        "scope": scope_strategy,
                        "translation_variant": translation_variant,
                        "include_references": include_references,
                        "message": "Starting full-paper translation.",
                    }
                )
                translation_summary = translate_full_paper(
                    _profile_root(profile),
                    source_id,
                    target_lang=target_lang,
                    mode=mode,
                    scope_strategy=scope_strategy,
                    include_references=include_references,
                    require_review=False,
                    progress_callback=progress_callback,
                )
            except Exception as exc:
                translation_summary = {
                    "source_id": source_id,
                    "target_lang": target_lang,
                    "mode": mode,
                    "scope": scope_strategy,
                    "translation_variant": translation_variant,
                    "include_references": include_references,
                    "updated": 0,
                    "translated": 0,
                    "missing": 0,
                    "stale": len(
                        [
                            row
                            for row in load_paper_translations(_profile_root(profile), source_id)
                            if row.status == "stale"
                        ]
                    ),
                    "failed": 1,
                    "warnings": [str(exc)],
                }
            translation_summaries.append(translation_summary)
            changed_sources.append(source_id)
            warnings.extend(f"{source_id}: {warning}" for warning in extraction_summary.get("warnings", []) or [])
            warnings.extend(f"{source_id}: {warning}" for warning in translation_summary.get("warnings", []) or [])
        changed["sources"] = changed_sources
        changed["translations"] = changed_sources
        message = _summarize_translation_result(translation_summaries)
        if len(changed_sources) == 1:
            next_state["detail_id"] = changed_sources[0]
            next_state["focus"] = "translations"
            if any(_int_value(summary.get("stale")) for summary in translation_summaries):
                next_state["action"] = "retry_translation"
            else:
                next_state["action"] = ""
        data = {
            "extraction_summaries": extraction_summaries,
            "translation_summaries": translation_summaries,
        }
    elif action == "paper_library_auto_chunk":
        changed_chunks: list[str] = []
        changed_sources = []
        for source_id in event_paper_ids():
            chunks = auto_chunk_paper(_profile_root(profile), source_id)
            changed_sources.append(source_id)
            changed_chunks.extend(chunk.id for chunk in chunks)
        changed["sources"] = changed_sources
        changed["chunks"] = changed_chunks
    elif action == "paper_library_delete_paper_record":
        source_ids = event_paper_ids()
        confirm = _clean_text(payload.get("confirm"))
        if len(source_ids) == 1 and confirm != source_ids[0]:
            raise ValueError("Type the source id to confirm paper deletion.")
        result = delete_paper_record(
            _profile_root(profile),
            source_ids,
            delete_pdf_asset=bool(payload.get("delete_pdf_asset")),
            delete_reader_artifacts=bool(payload.get("delete_reader_artifacts")),
        )
        changed["sources"] = [str(item) for item in result.get("deleted_sources", [])]
        changed["pdf_assets"] = [str(item) for item in result.get("deleted_pdf_assets", [])]
        changed["artifacts"] = [str(item) for item in result.get("deleted_artifacts", [])]
        next_state = {"detail_id": ""}
        count = len(changed["sources"])
        noun = "paper" if count == 1 else "papers"
        message = f"Deleted {count} {noun}."
    elif action == "paper_library_delete_paper_asset":
        changed_assets: list[str] = []
        for source_id in event_paper_ids():
            result = delete_paper_pdf_asset(_profile_root(profile), source_id)
            changed_assets.extend(str(item) for item in result.get("deleted_pdf_assets", []))
        changed["pdf_assets"] = changed_assets
        message = f"Deleted {len(changed_assets)} PDF asset{'s' if len(changed_assets) != 1 else ''}."
    elif action == "paper_library_delete_paper_artifacts":
        changed_artifacts: list[str] = []
        for source_id in event_paper_ids():
            result = delete_paper_reader_artifacts(_profile_root(profile), source_id)
            changed_artifacts.extend(str(item) for item in result.get("deleted_artifacts", []))
        changed["artifacts"] = changed_artifacts
        message = f"Deleted {len(changed_artifacts)} artifact file{'s' if len(changed_artifacts) != 1 else ''}."
    elif action == "paper_library_purge_discarded_papers":
        result = purge_discarded_papers(
            _profile_root(profile),
            delete_pdf_asset=bool(payload.get("delete_pdf_asset")),
            delete_reader_artifacts=bool(payload.get("delete_reader_artifacts")),
        )
        changed["sources"] = [str(item) for item in result.get("deleted_sources", [])]
        changed["pdf_assets"] = [str(item) for item in result.get("deleted_pdf_assets", [])]
        changed["artifacts"] = [str(item) for item in result.get("deleted_artifacts", [])]
        next_state = {"view": "discarded", "node_id": "", "detail_id": ""}
        count = len(changed["sources"])
        message = f"Purged {count} discarded paper{'s' if count != 1 else ''}."
    else:
        return PaperLibraryEventResult(ok=False, message=f"Unknown Paper Library event: {action}")

    return PaperLibraryEventResult(
        message=message,
        changed=changed,
        next=next_state,
        warnings=warnings,
        data=data,
    )


__all__ = [
    "LIBRARY_VIEW_GROUPS",
    "LIBRARY_VIEW_LABELS",
    "PAPER_LIBRARY_RUNTIME_DEFAULT",
    "PAPER_LIBRARY_RUNTIME_ENV",
    "PAPER_LIBRARY_RUNTIMES",
    "PaperLibraryEventResult",
    "build_paper_library_payload",
    "filter_paper_library_rows",
    "handle_paper_library_event",
    "resolve_paper_library_runtime",
]
