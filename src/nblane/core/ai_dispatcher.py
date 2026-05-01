"""Thin AI action dispatcher for editor inline patch candidates."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from nblane.core import llm as llm_client
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
    zh = lang == "zh"
    if zh:
        system = (
            "你是 nblane 博客编辑器里的内联写作助手。"
            "你只返回可以直接插入文章的 Markdown 或纯文本，不要解释过程。"
        )
        instructions = {
            "polish": "润色目标文本，保持事实和结构，提升清晰度。只返回润色后的 Markdown。",
            "rewrite": "改写目标文本，保持核心含义。只返回改写后的 Markdown。",
            "shorten": "压缩目标文本，删除冗余，保留关键信息。只返回压缩后的 Markdown。",
            "expand": "扩写目标文本，补充有用细节，但不要编造事实。只返回扩写后的 Markdown。",
            "continue": "基于光标附近上下文续写下一段。只返回新增 Markdown，不要重复原文。",
            "translate": "把目标文本翻译成自然、准确的中文或英文，按用户配置语言输出。只返回译文。",
            "tone": "把目标文本改成更专业、克制、适合公开博客的语气。只返回修改后的 Markdown。",
            "outline": "基于标题和上下文生成文章大纲。只返回 Markdown 标题和 bullet。",
            "formula": "把目标描述转换为 LaTeX 展示公式。只返回 LaTeX，不要包裹 $$。",
            "visual": (
                "为目标段落生成视觉素材 prompt。"
                "只返回一段可交给文生图或 diagram 生成器的 prompt。"
            ),
            "meta": "生成更好的标题、摘要或标签建议。只返回 Markdown。",
            "check": "指出文本的事实、隐私或表达风险。只返回简明 Markdown。",
        }
    else:
        system = (
            "You are an inline writing assistant inside the nblane blog editor. "
            "Return only Markdown or plain text that can be inserted directly. "
            "Do not explain your process."
        )
        instructions = {
            "polish": "Polish the target text for clarity while preserving facts and structure. Return only the polished Markdown.",
            "rewrite": "Rewrite the target text while preserving its core meaning. Return only rewritten Markdown.",
            "shorten": "Shorten the target text, remove redundancy, and keep the key information. Return only Markdown.",
            "expand": "Expand the target text with useful detail without inventing facts. Return only Markdown.",
            "continue": "Continue from the nearby cursor context. Return only new Markdown and do not repeat the original text.",
            "translate": "Translate the target text into the configured reply language. Return only the translation.",
            "tone": "Adjust the target text to a professional, restrained public-blog tone. Return only Markdown.",
            "outline": "Generate an article outline from the title and context. Return only Markdown headings and bullets.",
            "formula": "Convert the target description into a LaTeX display formula. Return only LaTeX, without $$ wrappers.",
            "visual": "Create a visual-generation prompt from the target paragraph. Return only one prompt.",
            "meta": "Suggest better title, summary, or tags. Return only Markdown.",
            "check": "Flag factual, privacy, or wording risks. Return concise Markdown only.",
        }
    instruction = instructions.get(operation, instructions["polish"])
    if operation == "visual" and visual_kind == "diagram":
        instruction += (
            " 输出应偏向清晰 diagram / mermaid / flowchart 描述。"
            if zh
            else " Prefer a clear diagram, Mermaid, or flowchart prompt."
        )
    return system, instruction


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
    raw = llm_client.chat(system, user, temperature=0.25)
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

