"""React Paper Library tree Streamlit component wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import streamlit.components.v1 as components
except Exception:  # pragma: no cover - Streamlit is optional for non-web imports.
    components = None

_FRONTEND_DIR = Path(__file__).parent / "frontend" / "static"

_component_func = None


def paper_library_component_available() -> bool:
    """Return True when the built Paper Library tree frontend is present."""
    return (_FRONTEND_DIR / "index.html").exists()


def _get_component_func():
    """Declare the Streamlit component lazily."""
    global _component_func
    if components is None:
        return None
    if _component_func is None and paper_library_component_available():
        _component_func = components.declare_component(
            "nblane_paper_library_tree",
            path=str(_FRONTEND_DIR),
        )
    return _component_func


def st_paper_library_tree(
    *,
    payload: dict[str, Any],
    key: str,
    height: int = 760,
) -> dict[str, Any] | None:
    """Render the Paper Library tree and return the latest UI event."""
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


__all__ = ["paper_library_component_available", "st_paper_library_tree"]
