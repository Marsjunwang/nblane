"""AI patch protocol shared by the public blog editor and backend."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AIOperation = Literal[
    "polish",
    "rewrite",
    "shorten",
    "expand",
    "continue",
    "translate",
    "tone",
    "outline",
    "expand_section",
    "formula",
    "visual",
    "meta",
    "check",
]


class AIPatchTarget(BaseModel):
    """Target selection or block context for a patch."""

    model_config = ConfigDict(extra="allow")

    block_ids: list[str] = Field(default_factory=list)
    selection_text: str = ""
    range: dict[str, Any] | None = None
    block_id: str = ""
    cursor_block_id: str = ""
    surrounding_blocks: list[dict[str, Any]] = Field(default_factory=list)


class AIBlockPatch(BaseModel):
    """One block-level mutation proposed by AI."""

    model_config = ConfigDict(extra="allow")

    op: Literal["replace", "insert", "delete"]
    block_id: str = ""
    block: dict[str, Any] = Field(default_factory=dict)


class AIAsset(BaseModel):
    """Asset generated or proposed by an AI operation."""

    model_config = ConfigDict(extra="allow")

    kind: Literal["image", "video", "diagram"]
    src: str = ""
    prompt: str = ""
    provider: str = ""
    model: str = ""
    candidate_path: str = ""
    preview_src: str = ""


class AICitation(BaseModel):
    """Evidence citation attached to an AI output."""

    model_config = ConfigDict(extra="allow")

    evidence_id: str = ""
    snippet: str = ""


class AIProvenance(BaseModel):
    """Model and prompt metadata for auditability."""

    model_config = ConfigDict(extra="allow")

    model: str = ""
    prompt_id: str = ""
    lang: Literal["zh", "en"] = "en"
    source_refs: list[str] = Field(default_factory=list)


class AIPatch(BaseModel):
    """Candidate patch returned by an AI operation."""

    model_config = ConfigDict(extra="allow")

    patch_id: str = ""
    ai_source_id: str = ""
    operation: AIOperation
    target: AIPatchTarget = Field(default_factory=AIPatchTarget)
    meta_patch: dict[str, Any] = Field(default_factory=dict)
    block_patches: list[AIBlockPatch] = Field(default_factory=list)
    markdown_fallback: str = ""
    assets: list[AIAsset] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    citations: list[AICitation] = Field(default_factory=list)
    provenance: AIProvenance = Field(default_factory=AIProvenance)


def patch_to_dict(patch: AIPatch) -> dict[str, Any]:
    """Return JSON-safe patch payload for Streamlit component props."""

    return patch.model_dump(mode="json", exclude_none=True)
