"""Streamlit BlockNote Markdown editor component."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import streamlit.components.v1 as components
except Exception:  # pragma: no cover - optional web dependency
    components = None

_FRONTEND_DIR = Path(__file__).parent / "frontend" / "static"
_DISPLAY_MATH_RE = re.compile(
    r"(?m)^\s*(?:\$\$|\\\[)\s*(?:$|[^\s])|"
    r"\\begin\{(?:align\*?|equation\*?|gather\*?|multline\*?|split|aligned|matrix|pmatrix|bmatrix|cases)\}"
)


def blocknote_component_available() -> bool:
    """Return True when the built frontend bundle is present."""
    return (_FRONTEND_DIR / "index.html").exists()


_component_func = None


def _get_component_func():
    """Declare the Streamlit component lazily to keep CLI imports quiet."""
    global _component_func
    if components is None:
        return None
    if _component_func is None and blocknote_component_available():
        _component_func = components.declare_component(
            "nblane_blocknote_markdown",
            path=str(_FRONTEND_DIR),
        )
    return _component_func


def _markdown_needs_math_safe(markdown: str) -> bool:
    """Return True when Markdown contains display/complex LaTeX blocks."""
    return bool(_DISPLAY_MATH_RE.search(str(markdown or "")))


def st_blocknote_markdown(
    *,
    initial_markdown: str,
    document_id: str,
    key: str,
    height: int = 560,
    editable: bool = True,
    math_safe: bool = False,
    source_mode: bool = False,
) -> str | None:
    """Render BlockNote as a Markdown-in/Markdown-out editor.

    The component intentionally returns Markdown, not BlockNote JSON, so
    ``profiles/<name>/blog/*.md`` remains the content source of truth.
    """
    component_func = _get_component_func()
    if component_func is None:
        return None
    effective_source_mode = source_mode or (
        math_safe and _markdown_needs_math_safe(initial_markdown)
    )
    result: Any = component_func(
        mode="markdown",
        initial_markdown=initial_markdown,
        document_id=document_id,
        height=height,
        editable=editable,
        math_safe=math_safe,
        source_mode=effective_source_mode,
        key=key,
        default={"markdown": initial_markdown, "dirty": False},
    )
    if isinstance(result, dict) and isinstance(result.get("markdown"), str):
        return str(result["markdown"])
    return initial_markdown


def st_public_blog_editor(
    *,
    posts: list[dict[str, Any]],
    active_slug: str,
    initial_markdown: str,
    key: str,
    active_post_meta: dict[str, Any] | None = None,
    media_items: list[dict[str, Any]] | None = None,
    ai_candidates: list[dict[str, Any]] | None = None,
    validation_state: dict[str, Any] | None = None,
    visual_config: dict[str, Any] | None = None,
    visual_results: list[dict[str, Any]] | None = None,
    visual_guidance: dict[str, Any] | None = None,
    operation_notice: dict[str, Any] | None = None,
    preview_html: str = "",
    status_filter: str = "all",
    layout_state: dict[str, Any] | None = None,
    ui_labels: dict[str, str] | None = None,
    document_id: str | None = None,
    layout_storage_key: str | None = None,
    height: int = 720,
    editable: bool = True,
    math_safe: bool = False,
    source_mode: bool = False,
) -> dict[str, Any] | None:
    """Render the full public blog editor shell.

    React owns the editor chrome and returns event dictionaries such as
    ``{"action": "save_post", "payload": {...}}``. Streamlit remains
    responsible for persistence, uploads, AI calls, validation, and publish
    side effects.
    """
    component_func = _get_component_func()
    if component_func is None:
        return None
    effective_source_mode = source_mode or (
        math_safe and _markdown_needs_math_safe(initial_markdown)
    )

    clean_layout_state = dict(layout_state or {})
    default = {
        "action": None,
        "event_id": "",
        "payload": {},
        "markdown": initial_markdown,
        "dirty": False,
        "layout_state": clean_layout_state,
        "selected_block": None,
        "insert_event": None,
    }
    result: Any = component_func(
        mode="shell",
        posts=list(posts or []),
        active_slug=active_slug,
        initial_markdown=initial_markdown,
        active_post_meta=dict(active_post_meta or {}),
        media_items=list(media_items or []),
        ai_candidates=list(ai_candidates or []),
        validation_state=dict(validation_state or {}),
        visual_config=dict(visual_config or {}),
        visual_results=list(visual_results or []),
        visual_guidance=dict(visual_guidance or {}),
        operation_notice=dict(operation_notice or {}),
        preview_html=preview_html,
        status_filter=status_filter,
        layout_state=clean_layout_state,
        ui_labels=dict(ui_labels or {}),
        document_id=document_id or active_slug,
        layout_storage_key=layout_storage_key,
        height=height,
        editable=editable,
        math_safe=math_safe,
        source_mode=effective_source_mode,
        key=key,
        default=default,
    )
    if isinstance(result, dict):
        merged = {**default, **result}
        if not isinstance(merged.get("payload"), dict):
            merged["payload"] = {}
        return merged
    return default
