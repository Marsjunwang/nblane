"""Compact check-in calendar Streamlit component."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "frontend" / "static"

_component_func = None


def checkin_calendar_component_available() -> bool:
    """Return True when the static frontend is present."""
    return (_FRONTEND_DIR / "index.html").exists()


def _get_component_func():
    """Declare the component lazily."""
    global _component_func
    if _component_func is None and checkin_calendar_component_available():
        _component_func = components.declare_component(
            "nblane_checkin_calendar",
            path=str(_FRONTEND_DIR),
        )
    return _component_func


def st_checkin_calendar(
    *,
    payload: dict[str, Any],
    selected_day: str,
    today: str,
    ui: dict[str, Any] | None = None,
    key: str,
    height: int = 166,
) -> dict[str, Any] | None:
    """Render the compact check-in calendar and return the latest UI event."""
    component_func = _get_component_func()
    if component_func is None:
        return None
    result: Any = component_func(
        payload=payload,
        selected_day=selected_day,
        today=today,
        ui=dict(ui or {}),
        height=height,
        key=key,
        default=None,
    )
    return result if isinstance(result, dict) else None
