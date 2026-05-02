"""Editor event protocol shared by Streamlit and the React shell."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


EditorAction = Literal[
    "markdown_changed",
    "layout_state_changed",
    "insert_media",
    "delete_media",
    "convert_media_video",
    "insert_candidate",
    "apply_candidate_meta",
    "select_post",
    "filter_posts",
    "create_post",
    "draft_from_evidence",
    "draft_from_done",
    "generate_ai_candidate",
    "ai_inline_action",
    "ai_stream_poll",
    "cancel_ai_stream",
    "apply_ai_patch",
    "reject_ai_patch",
    "upload_media",
    "generate_visual_asset",
    "generate_cover_image",
    "save_visual_candidate",
    "discard_visual_candidate",
    "load_media_preview_detail",
    "preview_post",
    "run_check",
    "request_reviewer_repair",
    "save_post",
    "publish_request",
]


class EditorEventPayload(BaseModel):
    """Payload emitted by the editor component."""

    model_config = ConfigDict(extra="allow")

    slug: str = ""
    document_id: str = ""
    markdown: str = ""
    blocks_json: list[dict[str, Any]] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
    layout_state: dict[str, Any] = Field(default_factory=dict)
    dirty: bool = False
    selected_block: dict[str, Any] | None = None
    patch_id: str = ""
    patch: dict[str, Any] = Field(default_factory=dict)
    finding_id: str = ""
    finding: dict[str, Any] = Field(default_factory=dict)
    event_id: str = ""


class EditorEvent(BaseModel):
    """Top-level event returned by ``st_public_blog_editor``."""

    model_config = ConfigDict(extra="allow")

    action: EditorAction | None = None
    event_id: str = ""
    payload: EditorEventPayload = Field(default_factory=EditorEventPayload)
    markdown: str = ""
    blocks_json: list[dict[str, Any]] = Field(default_factory=list)
    dirty: bool = False
    layout_state: dict[str, Any] = Field(default_factory=dict)
    selected_block: dict[str, Any] | None = None
    insert_event: dict[str, Any] | None = None


def validate_editor_event(event: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize one editor event dictionary."""

    try:
        return EditorEvent.model_validate(event).model_dump(mode="json", exclude_none=True)
    except ValidationError as exc:
        raise ValueError(f"Invalid editor event: {exc}") from exc
