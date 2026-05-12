"""React Home dashboard Streamlit component wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "frontend" / "static"

_component_func = None


def home_dashboard_component_available() -> bool:
    """Return True when the built frontend bundle is present."""
    return (_FRONTEND_DIR / "index.html").exists()


def _get_component_func():
    """Declare the Streamlit component lazily."""
    global _component_func
    if _component_func is None and home_dashboard_component_available():
        _component_func = components.declare_component(
            "nblane_home_dashboard",
            path=str(_FRONTEND_DIR),
        )
    return _component_func


def st_home_dashboard(
    *,
    payload: dict[str, Any],
    key: str,
    height: int = 860,
) -> dict[str, Any] | None:
    """Render the Daily Dashboard and return the latest UI event."""
    component_func = _get_component_func()
    if component_func is None:
        return None
    default = {
        "action": None,
        "event_id": "",
        "payload": {},
    }
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
