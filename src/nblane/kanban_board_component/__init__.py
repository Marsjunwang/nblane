"""React Kanban board Streamlit component wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "frontend" / "static"

_component_func = None


def kanban_board_component_available() -> bool:
    """Return True when the built frontend bundle is present."""
    return (_FRONTEND_DIR / "index.html").exists()


def _get_component_func():
    """Declare the Streamlit component lazily to keep non-web imports quiet."""
    global _component_func
    if _component_func is None and kanban_board_component_available():
        _component_func = components.declare_component(
            "nblane_kanban_board",
            path=str(_FRONTEND_DIR),
        )
    return _component_func


def st_kanban_board(
    *,
    payload: dict[str, Any] | None = None,
    sections: dict[str, Any] | list[dict[str, Any]] | None = None,
    labels: dict[str, Any] | None = None,
    ui: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
    ai_state: dict[str, Any] | None = None,
    key: str,
    height: int = 760,
) -> dict[str, Any] | None:
    """Render the React Kanban board and return the latest UI event.

    The frontend accepts the complete board payload and returns event
    dictionaries such as ``{"action": "move_card", "payload": {...}}``.
    Persistence, validation, AI execution, and markdown/YAML updates remain
    owned by the Streamlit/Python side.
    """
    component_func = _get_component_func()
    if component_func is None:
        return None

    clean_payload = {
        "sections": sections,
        "labels": dict(labels or {}),
        "ui": dict(ui or {}),
        "settings": dict(settings or {}),
        "ai_state": dict(ai_state or {}),
    }
    if isinstance(payload, dict):
        clean_payload = {**clean_payload, **payload}

    default = {
        "action": None,
        "payload": {},
        "sections": clean_payload.get("sections"),
        "ui": dict(clean_payload.get("ui") or {}),
    }
    result: Any = component_func(
        payload=clean_payload,
        sections=clean_payload.get("sections"),
        labels=dict(clean_payload.get("labels") or {}),
        ui=dict(clean_payload.get("ui") or {}),
        settings=dict(clean_payload.get("settings") or {}),
        ai_state=dict(clean_payload.get("ai_state") or {}),
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
