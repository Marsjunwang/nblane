"""Streamlit wrapper boundary for the Paper Reading PDF reader.

The Paper Reading Studio v1 ships with a fully functional Streamlit text-mode
Reader in ``pages/7_Research.py``. This wrapper reserves the PDF.js component
contract so the richer canvas/text-layer reader can replace the fallback
without changing the page/core write boundaries.
"""

from __future__ import annotations

from typing import Any


def st_research_paper_reader(
    *,
    source: dict[str, Any],
    pdf_base64: str = "",
    pages: list[dict[str, Any]] | None = None,
    segments: list[dict[str, Any]] | None = None,
    annotations: list[dict[str, Any]] | None = None,
    translations: list[dict[str, Any]] | None = None,
    chunks: list[dict[str, Any]] | None = None,
    ui: dict[str, str] | None = None,
    settings: dict[str, Any] | None = None,
    key: str | None = None,
) -> dict[str, Any] | None:
    """Render the future PDF.js reader boundary and return one event.

    The fallback intentionally does not write files or call AI. Streamlit page
    code remains responsible for validating events and invoking core helpers.
    """

    import streamlit as st

    labels = ui or {}
    st.info(
        labels.get(
            "reader_component_fallback",
            "PDF reader component is not built in this environment; using the text-mode Reader fallback.",
        )
    )
    st.caption(str(source.get("title") or source.get("id") or key or "paper"))
    if not pdf_base64:
        st.caption(labels.get("pdf_missing", "No PDF payload was provided to the component."))
    return None


__all__ = ["st_research_paper_reader"]
