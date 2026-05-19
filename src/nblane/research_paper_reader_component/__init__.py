"""Streamlit component wrapper for the Paper Reading PDF reader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import streamlit.components.v1 as components
except Exception:  # pragma: no cover - optional web dependency
    components = None

_FRONTEND_DIR = Path(__file__).parent / "frontend" / "static"
_component_func = None


def research_paper_reader_component_available() -> bool:
    """Return True when the static reader frontend is present."""
    return (_FRONTEND_DIR / "index.html").is_file()


def _get_component_func():
    """Declare the component lazily to keep non-Streamlit imports quiet."""
    global _component_func
    if components is None:
        return None
    if _component_func is None and research_paper_reader_component_available():
        _component_func = components.declare_component(
            "nblane_research_paper_reader_v2",
            path=str(_FRONTEND_DIR),
        )
    return _component_func


def st_research_paper_reader(
    *,
    source: dict[str, Any],
    pdf_url: str = "",
    pdf_base64: str = "",
    page_previews: list[dict[str, Any]] | None = None,
    pages: list[dict[str, Any]] | None = None,
    segments: list[dict[str, Any]] | None = None,
    annotations: list[dict[str, Any]] | None = None,
    translations: list[dict[str, Any]] | None = None,
    chunks: list[dict[str, Any]] | None = None,
    analysis: dict[str, Any] | None = None,
    ui: dict[str, str] | None = None,
    settings: dict[str, Any] | None = None,
    key: str | None = None,
    height: int = 820,
) -> dict[str, Any] | None:
    """Render the PDF.js reader boundary and return the latest UI event.

    The component intentionally only returns event dictionaries. Streamlit page
    code remains responsible for validation, persistence, and AI calls.
    ``pdf_url`` is preferred for normal reading because it lets PDF.js fetch the
    document through Streamlit's media endpoint instead of embedding large PDFs
    in component arguments.
    """

    labels = ui or {}
    source_payload = dict(source or {})
    default = {
        "action": None,
        "event_id": "",
        "payload": {},
    }
    component_func = _get_component_func()
    if component_func is not None:
        result: Any = component_func(
            source=source_payload,
            pdf_url=pdf_url or "",
            pdf_base64=pdf_base64 or "",
            page_previews=list(page_previews or []),
            pages=list(pages or []),
            segments=list(segments or []),
            annotations=list(annotations or []),
            translations=list(translations or []),
            chunks=list(chunks or []),
            analysis=dict(analysis or {}),
            ui=dict(labels),
            settings=dict(settings or {}),
            height=height,
            key=key,
            default=default,
        )
        if isinstance(result, dict):
            merged = {**default, **result}
            if not isinstance(merged.get("payload"), dict):
                merged["payload"] = {}
            if not merged.get("action"):
                return None
            return merged
        return None

    try:
        import streamlit as st
    except Exception:  # pragma: no cover - optional web dependency
        return None

    st.info(
        labels.get(
            "reader_component_fallback",
            "PDF reader component is not built in this environment; using the text-mode Reader fallback.",
        )
    )
    st.caption(str(source_payload.get("title") or source_payload.get("id") or key or "paper"))
    if not pdf_url and not pdf_base64 and not page_previews:
        st.caption(labels.get("pdf_missing", "No PDF payload was provided to the component."))
    return None


__all__ = ["research_paper_reader_component_available", "st_research_paper_reader"]
