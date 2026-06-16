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
from nblane.core import visual_candidate_store
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


def _estimate_tokens(text: str) -> int:
    """Rough output-token estimate for *text*.

    CJK characters are ~1 token each; Latin/whitespace runs ~1 token per ~3.5
    chars. Overestimating slightly is fine — it only decides whether to chunk.
    """

    clean = _clean_text(text)
    if not clean:
        return 0
    cjk = sum(1 for ch in clean if "㐀" <= ch <= "鿿" or "豈" <= ch <= "﫿")
    other = len(clean) - cjk
    return cjk + (other + 2) // 3


def _split_markdown_atomic_blocks(markdown: str) -> list[str]:
    """Split *markdown* into atomic blocks on blank lines.

    Fenced code blocks (```` ``` ````) and display-math blocks (``$$``) are kept
    whole even when they contain blank lines, so chunking never severs a code or
    formula block down the middle.
    """

    lines = _clean_text(markdown).split("\n")
    blocks: list[str] = []
    current: list[str] = []
    fence = ""  # active code fence marker, "" when outside a fence
    in_math = False

    def _flush() -> None:
        if current:
            chunk = "\n".join(current).strip("\n")
            if chunk.strip():
                blocks.append(chunk)
            current.clear()

    for line in lines:
        stripped = line.strip()
        fence_match = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence:
            current.append(line)
            if fence_match and stripped.startswith(fence[0] * 3):
                fence = ""
            continue
        if fence_match:
            _flush()
            fence = fence_match.group(1)
            current.append(line)
            continue
        # Display-math block delimited by lines that are exactly ``$$``.
        if stripped == "$$":
            if in_math:
                current.append(line)
                in_math = False
                continue
            _flush()
            in_math = True
            current.append(line)
            continue
        if in_math:
            current.append(line)
            continue
        if not stripped:
            _flush()
            continue
        current.append(line)
    if fence or in_math:
        # Unterminated fence/math: keep the trailing content as one block.
        pass
    _flush()
    return blocks


def _split_oversized_block(block: str, max_chars: int) -> list[str]:
    """Split a single block that exceeds *max_chars* into smaller pieces.

    Code fences (```` ``` ````) and display-math (``$$``) blocks are returned
    whole — splitting them would corrupt syntax, so they rely on the per-call
    token ceiling instead. Plain prose is split progressively: first on newlines,
    then on sentence boundaries, then on a hard character cut as a last resort.
    Reorganize is format-only, so an imperfect split boundary is harmless once
    the reorganized pieces are concatenated.
    """

    if len(block) <= max_chars:
        return [block]
    stripped = block.lstrip()
    if stripped.startswith("```") or stripped.startswith("~~~") or stripped.startswith("$$"):
        return [block]

    # Build candidate fragments by newline, then sentence boundaries, so we never
    # cut mid-line/mid-sentence unless a single sentence already exceeds the cap.
    units = block.split("\n")
    pieces: list[str] = []
    for unit in units:
        if len(unit) <= max_chars:
            pieces.append(unit)
            continue
        # Split long line on sentence enders (CJK 。！？ and ASCII .!?).
        parts = re.split(r"(?<=[。！？!?\.])\s*", unit)
        buffer = ""
        for part in parts:
            if not part:
                continue
            if len(part) > max_chars:
                # A single sentence still too long: hard character cut.
                if buffer:
                    pieces.append(buffer)
                    buffer = ""
                for i in range(0, len(part), max_chars):
                    pieces.append(part[i : i + max_chars])
                continue
            if not buffer:
                buffer = part
            elif len(buffer) + len(part) <= max_chars:
                buffer = f"{buffer}{part}"
            else:
                pieces.append(buffer)
                buffer = part
        if buffer:
            pieces.append(buffer)

    # Greedily repack the pieces (joined by newlines) up to the limit.
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if not current:
            current = piece
        elif len(current) + 1 + len(piece) <= max_chars:
            current = f"{current}\n{piece}"
        else:
            chunks.append(current)
            current = piece
    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if chunk.strip()] or [block]


def _chunk_markdown(markdown: str, max_chars: int) -> list[str]:
    """Greedily pack atomic blocks into chunks of at most *max_chars*.

    Atomic blocks (split on blank lines) are packed together; any block that on
    its own exceeds *max_chars* is first broken down by :func:`_split_oversized_block`
    so a document with little/no blank-line structure (e.g. a few very long
    paragraphs) still chunks instead of degenerating into one giant segment.
    """

    raw_blocks = _split_markdown_atomic_blocks(markdown)
    if not raw_blocks:
        return []
    blocks: list[str] = []
    for block in raw_blocks:
        if len(block) > max_chars:
            blocks.extend(_split_oversized_block(block, max_chars))
        else:
            blocks.append(block)
    chunks: list[str] = []
    current = ""
    for block in blocks:
        if not current:
            current = block
            continue
        if len(current) + 2 + len(block) <= max_chars:
            current = f"{current}\n\n{block}"
        else:
            chunks.append(current)
            current = block
    if current:
        chunks.append(current)
    return chunks



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
        return _normalize_mermaid_source(clean)
    label = re.sub(r"[\[\]{}<>|`\"']", " ", clean)
    label = re.sub(r"\s+", " ", label).strip()[:120] or "Diagram draft"
    return f'flowchart TD\n  A["{label}"]'


def _normalize_mermaid_source(value: str) -> str:
    """Normalize common LLM Mermaid output without changing graph semantics."""

    source = (
        _clean_text(value)
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\u002d", "-")
        .strip()
        .rstrip("，。")
    )
    if "\n" in source:
        return source
    match = re.match(r"^(?P<header>(?:flowchart|graph)\s+(?:TB|TD|BT|LR|RL))\s+(?P<body>.+)$", source, re.I)
    if not match:
        return source
    body = match.group("body").strip()
    statements = _split_one_line_mermaid_flowchart(body)
    if not statements:
        return source
    return "\n".join([match.group("header"), *(f"  {statement}" for statement in statements)])


def _split_one_line_mermaid_flowchart(body: str) -> list[str]:
    statements: list[str] = []
    start = 0
    quote = ""
    square = curly = paren = 0
    for index, char in enumerate(body):
        if quote:
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"', "`"}:
            quote = char
            continue
        if char == "[":
            square += 1
            continue
        if char == "]" and square:
            square -= 1
            continue
        if char == "{":
            curly += 1
            continue
        if char == "}" and curly:
            curly -= 1
            continue
        if char == "(":
            paren += 1
            continue
        if char == ")" and paren:
            paren -= 1
            continue
        if not char.isspace() or square or curly or paren:
            continue
        previous = body[index - 1] if index > 0 else ""
        if not re.match(r"[\w\]\}\)]", previous, re.I):
            continue
        rest = body[index:].lstrip()
        if re.match(
            r"^[A-Za-z_][\w-]*(?:\s*(?:\[[^\]]*\]|\{[^}]*\}|\([^)]*\)))?\s*(?:-->|---|--|==>|-\.\->|-\.)",
            rest,
        ):
            statement = body[start:index].strip().rstrip(";")
            if statement:
                statements.append(statement)
            start = len(body) - len(rest)
    tail = body[start:].strip().rstrip(";")
    if tail:
        statements.append(tail)
    if len(statements) == 1 and ";" in statements[0]:
        statements = [part.strip() for part in statements[0].split(";") if part.strip()]
    return statements


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
        "reorganize",
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


def _visual_kind_for_diagram(value: str) -> str:
    clean = _clean_text(value).strip().lower()
    if clean in {"diagram", "mermaid", "flowchart"}:
        return "flowchart"
    return clean or "flowchart"


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
    # Whole-document operations need the full body, not a truncated excerpt.
    article_excerpt = markdown if operation == "reorganize" else _trim(markdown, 2200)
    payload = {
        "operation": operation,
        "instruction": instruction,
        "user_prompt": prompt,
        "visual_kind": visual_kind,
        "title": _clean_text(meta.get("title")).strip(),
        "summary": _clean_text(meta.get("summary")).strip(),
        "abstract": _clean_text(meta.get("abstract")).strip(),
        "tags": meta.get("tags") if isinstance(meta.get("tags"), list) else [],
        "target_text": context,
        "surrounding_blocks": surrounding,
        "article_excerpt": article_excerpt,
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


def _reorganize_document(
    *,
    system: str,
    instruction: str,
    meta: dict[str, Any],
    markdown: str,
    target: AIPatchTarget,
    prompt: str,
    model: str | None,
    stream_callback: Callable[[str], None] | None,
) -> tuple[str, bool]:
    """Reorganize the WHOLE document, chunking long bodies to dodge truncation.

    Reorganize is a *format-only* transform (heading levels, paragraphs, code
    fences, math, tables, punctuation) — a per-block change that never rewrites
    across block boundaries — so a long document can be split into independent
    chunks, each reorganized, then concatenated, without altering meaning.

    Returns ``(reorganized_markdown, truncated)`` where *truncated* is True if
    any chunk hit the model output ceiling.
    """

    ceiling = llm_client.max_tokens_default()
    estimated_out = _estimate_tokens(markdown) + 256
    # If the whole rewrite comfortably fits the model's output ceiling, do it in
    # one pass (preserves the simplest behaviour for short/medium articles).
    if estimated_out <= int(ceiling * 0.85):
        user = _build_user_prompt(
            operation="reorganize",
            instruction=instruction,
            meta=meta,
            markdown=markdown,
            target=target,
            prompt=prompt,
            visual_kind="",
        )
        chat_meta: dict[str, Any] = {}
        raw = llm_client.chat(
            system,
            user,
            temperature=0.25,
            stream=stream_callback is not None,
            stream_callback=stream_callback,
            model=model,
            max_tokens=max(ceiling, estimated_out + 256),
            meta_out=chat_meta,
        )
        if raw.startswith("LLM error:") or raw.startswith("AI features not configured."):
            raise RuntimeError(raw)
        truncated = _clean_text(chat_meta.get("finish_reason")).strip().lower() == "length"
        return _strip_code_fence(raw).strip(), truncated

    # Long document: chunk so each call stays well under the output ceiling.
    # ~3 chars/token for mixed text; target ~40% of the ceiling per chunk so each
    # reorganized fragment generates quickly (well under the client timeout) and
    # never risks hitting the model output cap.
    max_chars = max(1200, int(ceiling * 3 * 0.40))
    chunks = _chunk_markdown(markdown, max_chars)
    if len(chunks) <= 1:
        chunks = [markdown]
    total = len(chunks)
    # Each fragment generates independently; give it a generous timeout so a
    # multi-chunk document does not trip the client/stream watchdog mid-run.
    chunk_timeout = max(llm_client.timeout_seconds(), 180.0)
    fragment_note = (
        " This is ONE FRAGMENT of a larger document being reorganized in order. "
        "Reorganize only this fragment's formatting. Do NOT add a document title, "
        "introduction, or conclusion, do NOT repeat content, and continue the "
        "existing heading hierarchy. Output only the reorganized fragment."
    )
    results: list[str] = []
    truncated_any = False
    for index, chunk in enumerate(chunks):
        if stream_callback is not None:
            stream_callback(f"\n\n[reorganizing part {index + 1}/{total}]\n\n")
        chunk_instruction = instruction if index == 0 else instruction + fragment_note
        user = _build_user_prompt(
            operation="reorganize",
            instruction=chunk_instruction,
            meta=meta if index == 0 else {},
            markdown=chunk,
            target=target,
            prompt=prompt,
            visual_kind="",
        )
        chunk_estimate = _estimate_tokens(chunk) + 256
        chat_meta = {}
        raw = llm_client.chat(
            system,
            user,
            temperature=0.25,
            stream=stream_callback is not None,
            stream_callback=stream_callback,
            model=model,
            max_tokens=min(ceiling, chunk_estimate + 512),
            timeout=chunk_timeout,
            meta_out=chat_meta,
        )
        if raw.startswith("LLM error:") or raw.startswith("AI features not configured."):
            raise RuntimeError(raw)
        if _clean_text(chat_meta.get("finish_reason")).strip().lower() == "length":
            truncated_any = True
        results.append(_strip_code_fence(raw).strip())
    combined = "\n\n".join(part for part in results if part).strip()
    return combined, truncated_any


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
    model: str = "",
    stream_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Generate an AI patch candidate without mutating the document."""

    lang = llm_client.reply_language()
    clean_visual_kind = _clean_text(visual_kind).strip().lower()
    requested_visual_kind = clean_visual_kind
    if clean_visual_kind in {"diagram", "mermaid", "flowchart", "sequence", "state", "class", "mindmap"}:
        clean_visual_kind = "diagram"
    clean_operation = _operation(operation, clean_visual_kind)
    clean_model = _clean_text(model).strip()
    target = _target_from_selection(selected_block)
    if (
        clean_operation in {"formula", "visual"}
        and not _clean_text(prompt).strip()
        and not target.selection_text.strip()
    ):
        raise RuntimeError("请先选中文本或在 slash 后输入描述")
    system, instruction = _prompt_for_operation(
        clean_operation,
        lang,
        clean_visual_kind,
    )
    patch_id = f"ai-{uuid.uuid4().hex[:12]}"
    ai_source_id = _clean_text(source_event_id).strip() or patch_id
    ai_model = llm_client.model_label()
    warnings: list[str] = []
    assets: list[AIAsset] = []
    block_patches: list[AIBlockPatch] = []
    visual_payload: dict[str, Any] | None = None

    if clean_operation == "reorganize":
        # Reorganize handles its own chunking for long documents; produce the
        # full reorganized body and skip the generic single-call path below.
        reorganized, truncated = _reorganize_document(
            system=system,
            instruction=instruction,
            meta=meta,
            markdown=markdown,
            target=target,
            prompt=prompt,
            model=clean_model or None,
            stream_callback=stream_callback,
        )
        raw = reorganized
        raw_text = reorganized
        if truncated:
            warnings.append(
                "Part of the AI output was cut off at the model's token limit; "
                "the result may be incomplete. Try again or raise LLM_MAX_TOKENS."
            )
    else:
        user = _build_user_prompt(
            operation=clean_operation,
            instruction=instruction,
            meta=meta,
            markdown=markdown,
            target=target,
            prompt=prompt,
            visual_kind=clean_visual_kind,
        )
        chat_meta: dict[str, Any] = {}
        raw = llm_client.chat(
            system,
            user,
            temperature=0.25,
            stream=stream_callback is not None,
            stream_callback=stream_callback,
            model=clean_model or None,
            meta_out=chat_meta,
        )
        if raw.startswith("LLM error:") or raw.startswith("AI features not configured."):
            raise RuntimeError(raw)
        raw_text = _strip_code_fence(raw).strip()

    def _emit_progress(message: str) -> None:
        if stream_callback is not None:
            stream_callback(f"\n\n{message}\n")

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
            "visual_kind": _visual_kind_for_diagram(requested_visual_kind),
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
        _emit_progress("Generating visual asset candidate...")
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
        candidate_path = ""
        preview_src = ""
        saved_model = _clean_text(caption_intent.get("model"))
        saved_provider = _clean_text(caption_intent.get("provider") or "dashscope_wan")
        if not generated_assets:
            detail = "; ".join(warnings) or "Visual generation did not return an image candidate."
            raise RuntimeError(detail)
        try:
            _emit_progress("Staging visual asset preview...")
            first = generated_assets[0]
            extension = _clean_text(getattr(first, "extension", "png") or "png")
            filename = visual_generation.generated_filename(
                "example",
                getattr(first, "data"),
                extension,
            )
            candidate = visual_candidate_store.write_candidate(
                profile,
                slug,
                data=getattr(first, "data"),
                filename=filename,
                kind="image",
                alt=_clean_text(caption_intent.get("alt")),
                caption=_clean_text(caption_intent.get("caption")),
                patch_id=patch_id,
                provider=saved_provider,
                model=saved_model,
                prompt=_clean_text(caption_intent.get("prompt") or raw_text),
            )
            candidate_path = candidate.relative_path
            preview_src = visual_candidate_store.candidate_preview_src(
                profile,
                candidate_path,
                kind="image",
            )
        except Exception as exc:
            raise RuntimeError(f"Generated visual could not be staged: {exc}") from exc
        visual_payload = {
            "asset_type": "image",
            "visual_kind": "example",
            "src": "",
            "candidate_path": candidate_path,
            "preview_src": preview_src,
            "mermaid": "",
            "prompt": _clean_text(caption_intent.get("prompt") or raw_text),
            "status": "candidate",
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
                src="",
                candidate_path=candidate_path,
                preview_src=preview_src,
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
    # ``reorganize`` rewrites the WHOLE document: keep block_patches empty so the
    # editor applies markdown_fallback as a full-document replacement rather than
    # touching a single block.
    if not block_patches and clean_operation != "reorganize":
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
        ai_source_id=ai_source_id,
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
