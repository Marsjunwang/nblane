"""Streamlit BlockNote Markdown editor component."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "frontend" / "static"


def blocknote_component_available() -> bool:
    """Return True when the built frontend bundle is present."""
    return (_FRONTEND_DIR / "index.html").exists()


_component_func = None


def _get_component_func():
    """Declare the Streamlit component lazily to keep CLI imports quiet."""
    global _component_func
    if _component_func is None and blocknote_component_available():
        _component_func = components.declare_component(
            "nblane_blocknote_markdown",
            path=str(_FRONTEND_DIR),
        )
    return _component_func


def st_blocknote_markdown(
    *,
    initial_markdown: str,
    document_id: str,
    key: str,
    height: int = 560,
    editable: bool = True,
) -> str | None:
    """Render BlockNote as a Markdown-in/Markdown-out editor.

    The component intentionally returns Markdown, not BlockNote JSON, so
    ``profiles/<name>/blog/*.md`` remains the content source of truth.
    """
    component_func = _get_component_func()
    if component_func is None:
        return None
    result: Any = component_func(
        initial_markdown=initial_markdown,
        document_id=document_id,
        height=height,
        editable=editable,
        key=key,
        default={"markdown": initial_markdown, "dirty": False},
    )
    if isinstance(result, dict) and isinstance(result.get("markdown"), str):
        return str(result["markdown"])
    return initial_markdown
