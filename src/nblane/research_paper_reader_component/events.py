"""Shared event contract for the Paper Reader component boundary."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

ANNOTATION_CREATE = "annotation_create"
ANNOTATION_UPDATE = "annotation_update"
ANNOTATION_DELETE = "annotation_delete"
TRANSLATE_SELECTION = "translate_selection"
TRANSLATE_VISIBLE_PAGES = "translate_visible_pages"
TRANSLATE_FULL_PAPER = "translate_full_paper"
EXPLAIN_SELECTION = "explain_selection"
ASK_PAPER = "ask_paper"
CREATE_CHUNK_FROM_SELECTION = "create_chunk_from_selection"
CREATE_CITATION = "create_citation"
SAVE_PROGRESS = "save_progress"
CODEX_DEEP_READ = "codex_deep_read"
READER_STATE_CHANGED = "reader_state_changed"
REQUEST_READER_CONTEXT = "request_reader_context"
REQUEST_PAGE_PREVIEWS = "request_page_previews"
REQUEST_PAGE_PREVIEW = "request_page_preview"
RETRY_TRANSLATION_SCOPE = "retry_translation_scope"
PREPARE_READER_ARTIFACTS = "prepare_reader_artifacts"

ReaderEventName = Literal[
    "annotation_create",
    "annotation_update",
    "annotation_delete",
    "translate_selection",
    "translate_visible_pages",
    "translate_full_paper",
    "explain_selection",
    "ask_paper",
    "create_chunk_from_selection",
    "create_citation",
    "save_progress",
    "codex_deep_read",
    "reader_state_changed",
    "request_reader_context",
    "request_page_previews",
    "request_page_preview",
    "retry_translation_scope",
    "prepare_reader_artifacts",
]

EVENT_NAMES: tuple[str, ...] = (
    ANNOTATION_CREATE,
    ANNOTATION_UPDATE,
    ANNOTATION_DELETE,
    TRANSLATE_SELECTION,
    TRANSLATE_VISIBLE_PAGES,
    TRANSLATE_FULL_PAPER,
    EXPLAIN_SELECTION,
    ASK_PAPER,
    CREATE_CHUNK_FROM_SELECTION,
    CREATE_CITATION,
    SAVE_PROGRESS,
    CODEX_DEEP_READ,
    READER_STATE_CHANGED,
    REQUEST_READER_CONTEXT,
    REQUEST_PAGE_PREVIEWS,
    REQUEST_PAGE_PREVIEW,
    RETRY_TRANSLATION_SCOPE,
    PREPARE_READER_ARTIFACTS,
)


class ReaderBasePayload(TypedDict, total=False):
    """Fields every frontend-to-backend reader event may carry."""

    event_id: str
    source_id: str
    page: int
    primary_page: int
    visible_pages: list[int]
    locator: str


class ReaderSelectionPayload(ReaderBasePayload, total=False):
    selected_text: str
    selected_text_hash: str
    rects: list[dict[str, Any]]
    segment_refs: list[str]
    note: str
    color: str
    tags: list[str]
    target_lang: str


class ReaderContextPayload(ReaderBasePayload, total=False):
    pages: list[int]


class ReaderStatePayload(ReaderBasePayload, total=False):
    reader_mode: str
    scale_mode: str
    active_tab: str
    target_lang: str
    side_panel_collapsed: bool
    focused_annotation_id: str
    focused_chunk_id: str
    last_visible_pages: list[int]
    compare_split_ratio: int
    panel_width: int


class ReaderEvent(TypedDict):
    action: ReaderEventName | str
    event_id: str
    payload: ReaderBasePayload


MAX_BATCH_PAGES = 20


def clean_page_list(value: object, *, max_pages: int = MAX_BATCH_PAGES) -> list[int]:
    """Normalize, deduplicate, and cap page lists from component events."""

    if not isinstance(value, list):
        return []
    pages: list[int] = []
    seen: set[int] = set()
    for item in value:
        try:
            page = int(item)
        except (TypeError, ValueError):
            continue
        if page < 1 or page in seen:
            continue
        seen.add(page)
        pages.append(page)
        if len(pages) >= max_pages:
            break
    return pages


__all__ = [
    "ANNOTATION_CREATE",
    "ANNOTATION_DELETE",
    "ANNOTATION_UPDATE",
    "ASK_PAPER",
    "CREATE_CHUNK_FROM_SELECTION",
    "CREATE_CITATION",
    "EVENT_NAMES",
    "EXPLAIN_SELECTION",
    "MAX_BATCH_PAGES",
    "PREPARE_READER_ARTIFACTS",
    "READER_STATE_CHANGED",
    "REQUEST_PAGE_PREVIEW",
    "REQUEST_PAGE_PREVIEWS",
    "REQUEST_READER_CONTEXT",
    "RETRY_TRANSLATION_SCOPE",
    "ReaderBasePayload",
    "ReaderContextPayload",
    "ReaderEvent",
    "ReaderEventName",
    "ReaderSelectionPayload",
    "ReaderStatePayload",
    "SAVE_PROGRESS",
    "TRANSLATE_FULL_PAPER",
    "TRANSLATE_SELECTION",
    "TRANSLATE_VISIBLE_PAGES",
    "clean_page_list",
]
