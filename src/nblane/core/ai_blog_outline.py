"""Outline generation and Markdown-to-editor block helpers."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Sequence
from typing import Any

from nblane.core import llm as llm_client
from nblane.core.ai_blog_prompts import get_prompt


ChatFn = Callable[..., str]


def _clean_text(value: object) -> str:
    return "" if value is None else str(value)


def _trim(value: object, limit: int = 1600) -> str:
    text = re.sub(r"\s+", " ", _clean_text(value)).strip()
    return text[:limit]


def _strip_code_fence(value: str) -> str:
    text = _clean_text(value).strip()
    fence = re.fullmatch(r"```(?:[a-zA-Z0-9_-]+)?\s*(.*?)\s*```", text, re.S)
    if fence:
        return fence.group(1).strip()
    return text


def _plain_content(value: str) -> str:
    text = _clean_text(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _indent_level(indent: str) -> int:
    expanded = indent.replace("\t", "    ")
    return max(0, len(expanded) // 2)


def _block(block_type: str, content: str = "", props: dict[str, Any] | None = None) -> dict[str, Any]:
    block: dict[str, Any] = {"type": block_type, "content": content}
    if props:
        block["props"] = props
    return block


def _append_section_placeholder(
    blocks: list[dict[str, Any]],
    *,
    section_open: bool,
    section_has_paragraph: bool,
) -> None:
    if section_open and not section_has_paragraph:
        blocks.append(_block("paragraph", ""))


def parse_outline_markdown_to_blocks(markdown: str) -> list[dict[str, Any]]:
    """Parse a compact Markdown outline into BlockNote-like blocks.

    The parser intentionally supports the small subset expected from outline
    prompts: headings, bullet/numbered list items, and plain paragraphs.  When
    a heading section only contains list items, an empty paragraph block is
    appended as a draft placeholder for that section.
    """
    text = _strip_code_fence(markdown)
    blocks: list[dict[str, Any]] = []
    paragraph_lines: list[str] = []
    section_open = False
    section_has_paragraph = False

    def flush_paragraph() -> None:
        nonlocal paragraph_lines, section_has_paragraph
        content = _plain_content(" ".join(paragraph_lines))
        paragraph_lines = []
        if content:
            blocks.append(_block("paragraph", content))
            if section_open:
                section_has_paragraph = True

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if heading:
            flush_paragraph()
            _append_section_placeholder(
                blocks,
                section_open=section_open,
                section_has_paragraph=section_has_paragraph,
            )
            level = len(heading.group(1))
            blocks.append(
                _block(
                    "heading",
                    _plain_content(heading.group(2).strip("#").strip()),
                    {"level": level},
                )
            )
            section_open = True
            section_has_paragraph = False
            continue

        bullet = re.match(r"^(?P<indent>\s*)[-*+]\s+(?P<text>.+?)\s*$", line)
        if bullet:
            flush_paragraph()
            level = _indent_level(bullet.group("indent"))
            props = {"level": level} if level else None
            blocks.append(_block("bulletListItem", _plain_content(bullet.group("text")), props))
            continue

        numbered = re.match(r"^(?P<indent>\s*)(?P<number>\d+)[.)]\s+(?P<text>.+?)\s*$", line)
        if numbered:
            flush_paragraph()
            level = _indent_level(numbered.group("indent"))
            props: dict[str, Any] = {"number": int(numbered.group("number"))}
            if level:
                props["level"] = level
            blocks.append(_block("numberedListItem", _plain_content(numbered.group("text")), props))
            continue

        paragraph_lines.append(stripped)

    flush_paragraph()
    _append_section_placeholder(
        blocks,
        section_open=section_open,
        section_has_paragraph=section_has_paragraph,
    )
    return blocks


def blocks_to_outline_markdown(blocks: Sequence[dict[str, Any]]) -> str:
    """Serialize parsed outline blocks back to simple Markdown."""
    lines: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = _clean_text(block.get("type"))
        content = _clean_text(block.get("content")).strip()
        props = block.get("props") if isinstance(block.get("props"), dict) else {}
        if block_type == "heading":
            level = props.get("level", 2)
            try:
                level_int = min(6, max(1, int(level)))
            except (TypeError, ValueError):
                level_int = 2
            if content:
                lines.append(f"{'#' * level_int} {content}")
        elif block_type == "bulletListItem":
            if content:
                lines.append(f"- {content}")
        elif block_type == "numberedListItem":
            if content:
                number = props.get("number", 1)
                try:
                    number_int = max(1, int(number))
                except (TypeError, ValueError):
                    number_int = 1
                lines.append(f"{number_int}. {content}")
        elif block_type == "paragraph" and content:
            lines.append(content)
    return "\n\n".join(lines).strip()


def fallback_outline_markdown(
    *,
    title: str = "",
    points: Sequence[str] | None = None,
    context: str = "",
) -> str:
    """Build a deterministic outline when no model output is available."""
    clean_title = _clean_text(title).strip() or "Draft outline"
    point_lines = [
        _clean_text(point).strip()
        for point in (points or [])
        if _clean_text(point).strip()
    ]
    if not point_lines and context.strip():
        sentences = re.split(r"(?<=[.!?。！？])\s+", context.strip())
        point_lines = [_trim(sentence, 140) for sentence in sentences if _trim(sentence, 140)][:4]
    if not point_lines:
        point_lines = [
            "Clarify the reader problem",
            "Explain the key idea",
            "Show an example or workflow",
            "Summarize tradeoffs and next steps",
        ]
    lines = [f"# {clean_title}", "## Context"]
    lines.extend(f"- {point}" for point in point_lines[:4])
    lines.extend(
        [
            "## Main argument",
            "- State the claim cautiously",
            "- Connect the claim to the provided context",
            "## Example",
            "- Add one concrete scenario",
            "- Explain what the reader should notice",
            "## Wrap-up",
            "- Recap the decision or takeaway",
        ]
    )
    return "\n".join(lines)


def _outline_user_payload(
    *,
    operation: str,
    title: str,
    points: Sequence[str] | None,
    context: str,
    extra: dict[str, Any] | None = None,
) -> str:
    payload = {
        "operation": operation,
        "title": _clean_text(title).strip(),
        "points": [
            _clean_text(point).strip()
            for point in (points or [])
            if _clean_text(point).strip()
        ],
        "context": _trim(context, 2400),
    }
    if extra:
        payload.update(extra)
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _chat_or_fallback(
    *,
    system: str,
    user: str,
    fallback: str,
    chat_func: ChatFn | None,
    temperature: float = 0.25,
) -> str:
    chat = chat_func or llm_client.chat
    try:
        raw = chat(system, user, temperature=temperature)
    except Exception:
        return fallback
    clean = _clean_text(raw).strip()
    if not clean or clean.startswith("LLM error:") or clean.startswith("AI features not configured."):
        return fallback
    return clean


def generate_outline_blocks(
    *,
    title: str = "",
    points: Sequence[str] | None = None,
    context: str = "",
    lang: str | None = None,
    chat_func: ChatFn | None = None,
) -> list[dict[str, Any]]:
    """Generate article outline blocks, falling back to deterministic blocks."""
    prompt_lang = "zh" if str(lang or llm_client.reply_language()).strip().lower() == "zh" else "en"
    fallback = fallback_outline_markdown(title=title, points=points, context=context)
    raw = _chat_or_fallback(
        system=get_prompt("inline_system", prompt_lang),
        user=_outline_user_payload(
            operation="outline",
            title=title,
            points=points,
            context=context,
        ),
        fallback=fallback,
        chat_func=chat_func,
    )
    return parse_outline_markdown_to_blocks(raw)


def expand_section_blocks(
    *,
    section_title: str = "",
    section_text: str = "",
    context: str = "",
    lang: str | None = None,
    chat_func: ChatFn | None = None,
) -> list[dict[str, Any]]:
    """Expand one section into editor blocks without requiring a live model."""
    prompt_lang = "zh" if str(lang or llm_client.reply_language()).strip().lower() == "zh" else "en"
    fallback = "\n\n".join(
        part
        for part in (
            f"## {_clean_text(section_title).strip()}" if _clean_text(section_title).strip() else "",
            _clean_text(section_text).strip() or _trim(context, 800),
        )
        if part
    ).strip()
    if not fallback:
        fallback = "Add the expanded section draft here."
    raw = _chat_or_fallback(
        system=get_prompt("inline_system", prompt_lang),
        user=_outline_user_payload(
            operation="expand_section",
            title=section_title,
            points=None,
            context=section_text or context,
            extra={"instruction": get_prompt("expand", prompt_lang)},
        ),
        fallback=fallback,
        chat_func=chat_func,
    )
    return parse_outline_markdown_to_blocks(raw)
