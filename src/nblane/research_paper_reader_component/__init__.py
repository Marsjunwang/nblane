"""Deprecated Streamlit component boundary for historical Reader events.

The PDF Reader runtime now lives in the FastAPI sidecar
``nblane.web_reader_api``.  This module intentionally keeps only a tiny
compatibility shim so older imports do not fail; event constants remain in
``events.py``.
"""

from __future__ import annotations

from typing import Any


def research_paper_reader_component_available() -> bool:
    """Return False because the static Streamlit reader runtime is retired."""

    return False


def _get_component_func():
    """Return no Streamlit component; Reader rendering is sidecar-only."""

    return None


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
    translation_units: list[dict[str, Any]] | None = None,
    translation_summary: dict[str, Any] | None = None,
    translation_revision: str = "",
    compare_split_ratio: int | float | None = None,
    panel_width: int | float | None = None,
    chunks: list[dict[str, Any]] | None = None,
    analysis: dict[str, Any] | None = None,
    ui: dict[str, str] | None = None,
    settings: dict[str, Any] | None = None,
    key: str | None = None,
    height: int = 820,
) -> dict[str, Any] | None:
    """Compatibility no-op for the retired static component runtime."""

    labels = ui or {}
    source_payload = dict(source or {})
    default = {
        "action": None,
        "event_id": "",
        "payload": {},
    }
    try:
        import streamlit as st
    except Exception:  # pragma: no cover - optional web dependency
        return None

    st.info(
        labels.get(
            "reader_component_retired",
            "The Streamlit PDF reader component is retired; open the FastAPI Reader sidecar instead.",
        )
    )
    st.caption(str(source_payload.get("title") or source_payload.get("id") or key or "paper"))
    if not pdf_url and not pdf_base64 and not page_previews:
        st.caption(labels.get("pdf_missing", "No PDF payload was provided to the component."))
    return None


__all__ = ["research_paper_reader_component_available", "st_research_paper_reader"]
