"""React Evidence Editor Streamlit component wrapper.

Mirrors project_timeline_component: a Vite-built React bundle lives in
``frontend/static`` and is served via declare_component. The component emits
event dicts ``{"action", "payload", "event_id"}``; all persistence, validation,
migration, and AI calls stay on the Python side (see pages/2_Evidence_Review).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "frontend" / "static"

_component_func = None


def evidence_editor_component_available() -> bool:
    """Return True when the built frontend bundle is present."""
    return (_FRONTEND_DIR / "index.html").exists()


def _get_component_func():
    """Declare the Streamlit component lazily."""
    global _component_func
    if _component_func is None and evidence_editor_component_available():
        _component_func = components.declare_component(
            "nblane_evidence_editor",
            path=str(_FRONTEND_DIR),
        )
    return _component_func


def st_evidence_editor(
    *,
    payload: dict[str, Any],
    labels: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
    key: str,
    height: int = 820,
) -> dict[str, Any] | None:
    """Render the evidence editor and return the latest UI event.

    Returns ``{"action", "payload", "event_id"}`` or ``None`` when the built
    bundle is unavailable (caller falls back to the Python tabs).
    """
    component_func = _get_component_func()
    if component_func is None:
        return None
    default = {"action": None, "event_id": "", "payload": {}}
    # Pack labels/settings into the single payload the frontend reads.
    merged_payload = dict(payload or {})
    merged_payload["labels"] = dict(labels or {})
    merged_payload["settings"] = dict(settings or {})
    result: Any = component_func(
        payload=merged_payload,
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
