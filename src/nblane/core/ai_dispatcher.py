"""Thin AI action dispatcher for editor inline patch candidates."""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Callable
from typing import Any

from nblane.core import llm as llm_client
from nblane.core.ai_blog_prompts import get_prompt
from schemas.ai_patch import (
    AIAsset,
    AIBlockPatch,
    AICitation,
    AIPatch,
    AIPatchTarget,
    AIProvenance,
    patch_to_dict,
)


_REPLACE_OPERATIONS = {
    "polish",
    "rewrite",
    "shorten",
    "expand",
    "translate",
    "tone",
    "formula",
}


def _clean_text(value: object) -> str:
    return "" if value is None else str(value)


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def _trim(value: object, limit: int = 1800) -> str:
    text = re.sub(r"\s+", " ", _clean_text(value)).strip()
    return text[:limit]


def _strip_code_fence(value: str) -> str:
    text = _clean_text(value).strip()
    fence = re.fullmatch(r"```(?:[a-zA-Z0-9_-]+)?\s*(.*?)\s*```", text, re.S)
    if fence:
        return fence.group(1).strip()
    return text


def _operation(value: object, visual_kind: str = "") -> str:
    clean = _clean_text(value).strip().lower()
    if clean == "diagram":
        return "visual"
    allowed = {
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
    }
    if clean in allowed:
        return clean
    return "visual" if visual_kind == "diagram" else "polish"


def _target_from_selection(selected_block: dict[str, Any]) -> AIPatchTarget:
    range_payload = _as_dict(selected_block.get("range"))
    block_ids = [
        _clean_text(item).strip()
        for item in _as_list(range_payload.get("block_ids"))
        if _clean_text(item).strip()
    ]
    block_id = _clean_text(selected_block.get("block_id")).strip()
    if block_id and block_id not in block_ids:
        block_ids.insert(0, block_id)
    cursor_block_id = _clean_text(selected_block.get("cursor_block_id")).strip()
    return AIPatchTarget(
        block_ids=block_ids,
        block_id=block_id,
        cursor_block_id=cursor_block_id,
        selection_text=_clean_text(selected_block.get("selection_text")).strip(),
        range=range_payload or None,
        surrounding_blocks=[
            block
            for block in _as_list(selected_block.get("surrounding_blocks"))
            if isinstance(block, dict)
        ],
    )


def _context_text(target: AIPatchTarget, markdown: str) -> str:
    if target.selection_text.strip():
        return target.selection_text.strip()
    surrounding = [
        _clean_text(block.get("text")).strip()
        for block in target.surrounding_blocks
        if isinstance(block, dict) and _clean_text(block.get("text")).strip()
    ]
    if surrounding:
        return "\n\n".join(surrounding[:3])
    return _trim(markdown, 1600)


def _prompt_for_operation(operation: str, lang: str, visual_kind: str = "") -> tuple[str, str]:
    prompt_name = {
        "formula": "nl_to_latex",
        "visual": "diagram" if visual_kind == "diagram" else "visual",
    }.get(operation, operation)
    return get_prompt("inline_system", lang), get_prompt(prompt_name, lang)


def _build_user_prompt(
    *,
    operation: str,
    instruction: str,
    meta: dict[str, Any],
    markdown: str,
    target: AIPatchTarget,
    prompt: str,
    visual_kind: str,
) -> str:
    context = _context_text(target, markdown)
    surrounding = [
        {
            "type": _clean_text(block.get("type")),
            "text": _trim(block.get("text"), 420),
        }
        for block in target.surrounding_blocks
        if isinstance(block, dict)
    ]
    payload = {
        "operation": operation,
        "instruction": instruction,
        "user_prompt": prompt,
        "visual_kind": visual_kind,
        "title": _clean_text(meta.get("title")).strip(),
        "summary": _clean_text(meta.get("summary")).strip(),
        "tags": meta.get("tags") if isinstance(meta.get("tags"), list) else [],
        "target_text": context,
        "surrounding_blocks": surrounding,
        "article_excerpt": _trim(markdown, 2200),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _block_patch(operation: str, target: AIPatchTarget, markdown: str) -> AIBlockPatch:
    block_id = target.block_ids[0] if target.block_ids else target.block_id
    op = "replace" if operation in _REPLACE_OPERATIONS else "insert"
    if operation == "formula":
        block = {"type": "math_block", "props": {"latex": markdown, "ai_generated": True}}
    elif operation == "visual":
        block = {
            "type": "visual_block",
            "props": {
                "asset_type": "diagram" if "diagram" in markdown.lower() else "image",
                "prompt": markdown,
                "status": "candidate",
                "ai_generated": True,
            },
        }
    else:
        block = {"type": "paragraph", "content": markdown}
    return AIBlockPatch(op=op, block_id=block_id, block=block)


def _markdown_for_operation(operation: str, raw: str, visual_kind: str = "") -> str:
    text = _strip_code_fence(raw)
    if operation == "formula":
        latex = text.strip().strip("$").strip()
        return f"$$\n{latex}\n$$"
    if operation == "visual":
        asset_type = "diagram" if visual_kind == "diagram" else "image"
        payload = {
            "asset_type": asset_type,
            "visual_kind": "flowchart" if visual_kind == "diagram" else "example",
            "prompt": text.strip(),
            "status": "candidate",
            "caption": "",
            "alt": "",
            "ai_generated": True,
            "accepted": False,
        }
        return f"<!-- nblane:visual_block {json.dumps(payload, ensure_ascii=False)} -->"
    return text


def generate_ai_patch(
    *,
    profile: str,
    slug: str,
    meta: dict[str, Any],
    markdown: str,
    selected_block: dict[str, Any],
    operation: str,
    prompt: str = "",
    visual_kind: str = "",
    source_event_id: str = "",
    stream_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Generate an AI patch candidate without mutating the document."""

    lang = llm_client.reply_language()
    clean_visual_kind = _clean_text(visual_kind).strip().lower()
    clean_operation = _operation(operation, clean_visual_kind)
    target = _target_from_selection(selected_block)
    system, instruction = _prompt_for_operation(
        clean_operation,
        lang,
        clean_visual_kind,
    )
    user = _build_user_prompt(
        operation=clean_operation,
        instruction=instruction,
        meta=meta,
        markdown=markdown,
        target=target,
        prompt=prompt,
        visual_kind=clean_visual_kind,
    )
    raw = llm_client.chat(
        system,
        user,
        temperature=0.25,
        stream=stream_callback is not None,
        stream_callback=stream_callback,
    )
    if raw.startswith("LLM error:") or raw.startswith("AI features not configured."):
        raise RuntimeError(raw)

    markdown_fallback = _markdown_for_operation(
        clean_operation,
        raw,
        clean_visual_kind,
    ).strip()
    block_patch_markdown = _strip_code_fence(raw).strip()
    assets: list[AIAsset] = []
    if clean_operation == "visual":
        assets.append(
            AIAsset(
                kind="diagram" if clean_visual_kind == "diagram" else "image",
                prompt=block_patch_markdown,
                provider="dashscope_wan",
                model="",
            )
        )
    citations = [
        AICitation(evidence_id=_clean_text(ref), snippet="")
        for ref in _as_list(meta.get("related_evidence"))
        if _clean_text(ref).strip()
    ]
    patch = AIPatch(
        patch_id=f"ai-{uuid.uuid4().hex[:12]}",
        operation=clean_operation,  # type: ignore[arg-type]
        target=target,
        block_patches=[
            _block_patch(clean_operation, target, block_patch_markdown),
        ],
        markdown_fallback=markdown_fallback,
        assets=assets,
        warnings=[],
        citations=citations,
        provenance=AIProvenance(
            model=llm_client.model_label(),
            prompt_id=f"inline.{clean_operation}",
            lang=lang,  # type: ignore[arg-type]
            source_refs=[
                ref
                for ref in (profile, slug, source_event_id)
                if _clean_text(ref).strip()
            ],
        ),
    )
    return patch_to_dict(patch)
