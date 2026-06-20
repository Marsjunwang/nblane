"""Custom Project Board editor Streamlit component wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "frontend" / "static"

_component_func = None


def project_board_component_available() -> bool:
    """Return True when the built frontend bundle is present."""
    return (_FRONTEND_DIR / "index.html").exists()


def _get_component_func():
    """Declare the Streamlit component lazily to keep non-web imports quiet."""
    global _component_func
    if _component_func is None and project_board_component_available():
        _component_func = components.declare_component(
            "nblane_project_board",
            path=str(_FRONTEND_DIR),
        )
    return _component_func


def st_project_board(
    *,
    case: dict[str, Any],
    option_maps: dict[str, list[dict[str, str]]] | None = None,
    milestones: list[dict[str, Any]] | None = None,
    labels: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
    key: str,
    height: int = 720,
) -> dict[str, Any] | None:
    """Render the custom project editor and return the latest UI event.

    The frontend renders the project Basics panel and milestone cards, and
    emits event dictionaries such as ``{"action": "save_basics", ...}``.
    Persistence, validation, and YAML updates stay on the Streamlit/Python
    side -- this component only renders and reports user intent.
    """
    component_func = _get_component_func()
    if component_func is None:
        return None

    default = {"action": None, "payload": {}, "event_id": ""}
    result: Any = component_func(
        case=dict(case or {}),
        option_maps=dict(option_maps or {}),
        milestones=list(milestones or []),
        labels=dict(labels or {}),
        settings=dict(settings or {}),
        height=height,
        key=key,
        default=default,
    )
    if isinstance(result, dict):
        merged = {**default, **result}
        if not isinstance(merged.get("payload"), dict):
            merged["payload"] = {}
        return merged
    return default
