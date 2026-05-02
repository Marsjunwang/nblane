"""Thin AI action dispatcher for editor inline patch candidates."""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Callable
from typing import Any

from nblane.core import ai_blog_outline
from nblane.core import llm as llm_client
from nblane.core import visual_generation
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


def _json_for_comment(value: dict[str, Any]) -> str:
    """Return a JSON payload that is safe inside an HTML comment."""

    return json.dumps(value, ensure_ascii=False).replace("--", "\\u002d\\u002d")


def _visual_block_comment(payload: dict[str, Any]) -> str:
    return f"<!-- nblane:visual_block {_json_for_comment(payload)} -->"


def _math_block_comment(payload: dict[str, Any]) -> str:
    return f"<!-- nblane:math_block {_json_for_comment(payload)} -->"


def _strip_wrapping_math_delimiters(value: str) -> str:
    text = _strip_code_fence(value).strip()
    display_patterns = (
        r"^\$\$\s*(?P<body>.*?)\s*\$\$$",
        r"^\\\[\s*(?P<body>.*?)\s*\\\]$",
    )
    for pattern in display_patterns:
        match = re.fullmatch(pattern, text, re.S)
        if match:
            return match.group("body").strip()
    inline_match = re.fullmatch(r"^\$(?P<body>.*?)\$$", text, re.S)
    if inline_match:
        return inline_match.group("body").strip()
    lines = [line.strip() for line in text.splitlines()]
    while lines and re.match(r"^(latex|公式|answer)\s*[:：]\s*$", lines[0], re.I):
        lines.pop(0)
    text = "\n".join(lines).strip()
    return text.strip("$").strip()


def _extract_mermaid(value: str) -> str:
    text = _clean_text(value).strip()
    fence = re.search(r"```(?:mermaid)?\s*(.*?)\s*```", text, re.S | re.I)
    if fence:
        return fence.group(1).strip()
    clean = _strip_code_fence(text)
    mermaid_starts = (
        "flowchart ",
        "graph ",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram",
        "erDiagram",
        "journey",
        "gantt",
        "pie ",
        "mindmap",
        "timeline",
    )
    if clean.startswith(mermaid_starts):
        return clean
    label = re.sub(r"[\[\]{}<>|`\"']", " ", clean)
    label = re.sub(r"\s+", " ", label).strip()[:120] or "Diagram draft"
    return f'flowchart TD\n  A["{label}"]'


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
        "expand_section": "expand",
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


def _block_patch(
    operation: str,
    target: AIPatchTarget,
    markdown: str,
    *,
    ai_source_id: str = "",
    ai_model: str = "",
    visual_kind: str = "",
) -> AIBlockPatch:
    block_id = target.block_ids[0] if target.block_ids else target.block_id
    op = "replace" if operation in _REPLACE_OPERATIONS or operation == "expand_section" else "insert"
    if operation == "formula":
        block = {
            "type": "math_block",
            "props": {
                "latex": markdown,
                "ai_generated": True,
                "ai_source_id": ai_source_id,
                "ai_model": ai_model,
                "accepted": False,
            },
        }
    elif operation == "visual":
        mermaid = _extract_mermaid(markdown) if visual_kind == "diagram" else ""
        block = {
            "type": "visual_block",
            "props": {
                "asset_type": "diagram" if visual_kind == "diagram" else "image",
                "visual_kind": "flowchart" if visual_kind == "diagram" else "example",
                "mermaid": mermaid,
                "prompt": markdown,
                "status": "candidate",
                "ai_generated": True,
                "ai_source_id": ai_source_id,
                "ai_model": ai_model,
                "accepted": False,
            },
        }
    else:
        block = {"type": "paragraph", "content": markdown}
    return AIBlockPatch(op=op, block_id=block_id, block=block)


def _markdown_for_operation(
    operation: str,
    raw: str,
    visual_kind: str = "",
    *,
    ai_source_id: str = "",
    ai_model: str = "",
    visual_payload: dict[str, Any] | None = None,
) -> str:
    text = _strip_code_fence(raw)
    if operation == "formula":
        latex = _strip_wrapping_math_delimiters(text)
        return _math_block_comment(
            {
                "latex": latex,
                "ai_generated": True,
                "ai_source_id": ai_source_id,
                "ai_model": ai_model,
                "accepted": False,
            }
        )
    if operation == "visual":
        if visual_payload:
            return _visual_block_comment(visual_payload)
        asset_type = "diagram" if visual_kind == "diagram" else "image"
        mermaid = _extract_mermaid(text) if visual_kind == "diagram" else ""
        payload = {
            "asset_type": asset_type,
            "visual_kind": "flowchart" if visual_kind == "diagram" else "example",
            "mermaid": mermaid,
            "prompt": text.strip(),
            "status": "candidate",
            "caption": "",
            "alt": "",
            "ai_generated": True,
            "ai_source_id": ai_source_id,
            "ai_model": ai_model,
            "accepted": False,
        }
        return _visual_block_comment(payload)
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
    if clean_visual_kind in {"flowchart", "mermaid"}:
        clean_visual_kind = "diagram"
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

    patch_id = f"ai-{uuid.uuid4().hex[:12]}"
    ai_source_id = _clean_text(source_event_id).strip() or patch_id
    ai_model = llm_client.model_label()
    raw_text = _strip_code_fence(raw).strip()
    warnings: list[str] = []
    assets: list[AIAsset] = []
    block_patches: list[AIBlockPatch] = []
    visual_payload: dict[str, Any] | None = None

    if clean_operation == "formula":
        latex = _strip_wrapping_math_delimiters(raw)
        block_patches = [
            _block_patch(
                clean_operation,
                target,
                latex,
                ai_source_id=ai_source_id,
                ai_model=ai_model,
            )
        ]
    elif clean_operation in {"outline", "expand_section"}:
        section_title = _clean_text(prompt).strip()
        if not section_title:
            section_title = _clean_text(target.selection_text).strip().splitlines()[0:1]
            section_title = section_title[0] if section_title else ""
        outline_source = raw
        if clean_operation == "expand_section" and section_title:
            if not re.match(r"^\s*#{1,6}\s+", raw):
                outline_source = f"## {section_title}\n\n{raw}"
        outline_blocks = ai_blog_outline.parse_outline_markdown_to_blocks(outline_source)
        if not outline_blocks:
            outline_blocks = ai_blog_outline.generate_outline_blocks(
                title=_clean_text(meta.get("title") or prompt),
                context=_context_text(target, markdown),
                lang=lang,
                chat_func=lambda *_args, **_kwargs: raw,
            )
        for index, block in enumerate(outline_blocks):
            block_patches.append(
                AIBlockPatch(
                    op="replace" if clean_operation == "expand_section" and index == 0 else "insert",
                    block_id=target.block_ids[0] if target.block_ids else target.block_id,
                    block=block,
                )
            )
        raw_text = ai_blog_outline.blocks_to_outline_markdown(outline_blocks) or raw_text
    elif clean_operation == "visual" and clean_visual_kind == "diagram":
        mermaid = _extract_mermaid(raw)
        visual_payload = {
            "asset_type": "diagram",
            "visual_kind": "flowchart",
            "src": "",
            "mermaid": mermaid,
            "prompt": raw_text,
            "status": "candidate",
            "caption": "",
            "alt": "",
            "ai_generated": True,
            "ai_source_id": ai_source_id,
            "ai_model": ai_model,
            "accepted": False,
        }
        block_patches = [
            AIBlockPatch(
                op="insert",
                block_id=target.block_ids[0] if target.block_ids else target.block_id,
                block={"type": "visual_block", "props": dict(visual_payload)},
            )
        ]
        assets.append(
            AIAsset(
                kind="diagram",
                prompt=mermaid,
                provider="mermaid",
                model="",
            )
        )
    elif clean_operation == "visual":
        caption_intent = visual_generation.from_caption_intent(
            _context_text(target, markdown),
            lang,
            llm_response=raw,
            title=_clean_text(meta.get("title")),
            summary=_clean_text(meta.get("summary")),
            tags=meta.get("tags") if isinstance(meta.get("tags"), list) else [],
            body=markdown,
        )
        warnings.extend(
            _clean_text(warning)
            for warning in _as_list(caption_intent.get("warnings"))
            if _clean_text(warning).strip()
        )
        generated_assets = _as_list(caption_intent.get("generated_assets"))
        saved_src = ""
        saved_model = _clean_text(caption_intent.get("model"))
        saved_provider = _clean_text(caption_intent.get("provider") or "dashscope_wan")
        if generated_assets:
            try:
                from nblane.core import public_site

                first = generated_assets[0]
                extension = _clean_text(getattr(first, "extension", "png") or "png")
                filename = visual_generation.generated_filename(
                    "example",
                    getattr(first, "data"),
                    extension,
                )
                saved = public_site.add_blog_media_bytes(
                    profile,
                    slug,
                    data=getattr(first, "data"),
                    filename=filename,
                    kind="image",
                    alt=_clean_text(caption_intent.get("alt")),
                    caption=_clean_text(caption_intent.get("caption")),
                    append=False,
                )
                saved_src = saved.relative_path
            except Exception as exc:
                warnings.append(f"Generated visual could not be saved: {exc}")
        visual_payload = {
            "asset_type": "image",
            "visual_kind": "example",
            "src": saved_src,
            "mermaid": "",
            "prompt": _clean_text(caption_intent.get("prompt") or raw_text),
            "status": "generated" if saved_src else "candidate",
            "caption": _clean_text(caption_intent.get("caption")),
            "alt": _clean_text(caption_intent.get("alt")),
            "ai_generated": True,
            "ai_source_id": ai_source_id,
            "ai_model": ai_model,
            "accepted": False,
        }
        block_patches = [
            AIBlockPatch(
                op="insert",
                block_id=target.block_ids[0] if target.block_ids else target.block_id,
                block={"type": "visual_block", "props": dict(visual_payload)},
            )
        ]
        assets.append(
            AIAsset(
                kind="image",
                src=saved_src,
                prompt=_clean_text(visual_payload.get("prompt")),
                provider=saved_provider,
                model=saved_model,
            )
        )

    markdown_fallback = _markdown_for_operation(
        clean_operation,
        raw_text,
        clean_visual_kind,
        ai_source_id=ai_source_id,
        ai_model=ai_model,
        visual_payload=visual_payload,
    ).strip()
    if not block_patches:
        block_patches = [
            _block_patch(
                clean_operation,
                target,
                raw_text,
                ai_source_id=ai_source_id,
                ai_model=ai_model,
                visual_kind=clean_visual_kind,
            )
        ]
    citations = [
        AICitation(evidence_id=_clean_text(ref), snippet="")
        for ref in _as_list(meta.get("related_evidence"))
        if _clean_text(ref).strip()
    ]
    patch = AIPatch(
        patch_id=patch_id,
        operation=clean_operation,  # type: ignore[arg-type]
        target=target,
        block_patches=block_patches,
        markdown_fallback=markdown_fallback,
        assets=assets,
        warnings=warnings,
        citations=citations,
        provenance=AIProvenance(
            model=ai_model,
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
