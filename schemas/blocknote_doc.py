"""BlockNote sidecar document protocol for nblane editors."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Block(BaseModel):
    """A permissive BlockNote block payload.

    BlockNote owns many block-specific fields and custom block props. The
    sidecar validates the envelope while intentionally allowing extra keys so
    frontend upgrades do not corrupt older documents.
    """

    model_config = ConfigDict(extra="allow")

    id: str = ""
    type: str
    props: dict[str, Any] = Field(default_factory=dict)
    content: Any = None
    children: list["Block"] = Field(default_factory=list)


class AIProvenance(BaseModel):
    """AI metadata attached to a document or generated block."""

    model_config = ConfigDict(extra="allow")

    model: str = ""
    prompt_id: str = ""
    lang: Literal["zh", "en"] = "en"
    source_refs: list[str] = Field(default_factory=list)


class Document(BaseModel):
    """Canonical editor-side representation stored in ``*.blocknote.json``."""

    model_config = ConfigDict(extra="allow")

    schema_version: Literal[1] = 1
    document_id: str = ""
    profile: str = ""
    slug: str
    meta: dict[str, Any] = Field(default_factory=dict)
    blocks: list[Block] = Field(default_factory=list)
    markdown: str = ""
    source_md_sha256: str = ""
    provenance: list[AIProvenance] = Field(default_factory=list)
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def document_to_dict(document: Document) -> dict[str, Any]:
    """Return a JSON-safe sidecar payload."""

    return document.model_dump(mode="json", exclude_none=True)


def coerce_blocks(blocks: object) -> list[dict[str, Any]]:
    """Return JSON-safe BlockNote blocks, dropping invalid entries."""

    if not isinstance(blocks, list):
        return []
    clean: list[dict[str, Any]] = []
    for item in blocks:
        if not isinstance(item, dict):
            continue
        block_type = str(item.get("type", "") or "").strip()
        if not block_type:
            continue
        clean.append(Block.model_validate(item).model_dump(mode="json", exclude_none=True))
    return clean
