"""React Project Timeline Streamlit component wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "frontend" / "static"

_component_func = None


def project_timeline_component_available() -> bool:
    """Return True when the built frontend bundle is present."""
    return (_FRONTEND_DIR / "index.html").exists()


def _get_component_func():
    """Declare the Streamlit component lazily."""
    global _component_func
    if _component_func is None and project_timeline_component_available():
        _component_func = components.declare_component(
            "nblane_project_timeline",
            path=str(_FRONTEND_DIR),
        )
    return _component_func


def st_project_timeline(
    *,
    payload: dict[str, Any],
    key: str,
    height: int = 640,
) -> dict[str, Any] | None:
    """Render the project timeline and return the latest UI event.

    The frontend draws a horizontal SVG timeline (tasks as points, milestones as
    markers) and emits event dicts like ``{"action": "add_task", "payload": {...}}``.
    Persistence, validation, and YAML/markdown updates stay on the Python side.
    """
    component_func = _get_component_func()
    if component_func is None:
        return None
    default = {"action": None, "event_id": "", "payload": {}}
    result: Any = component_func(
        payload=dict(payload or {}),
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
