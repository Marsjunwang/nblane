"""React Current Goal presence Streamlit component wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from streamlit.components import v2 as components_v2
except Exception:  # pragma: no cover - optional Streamlit runtime.
    components_v2 = None  # type: ignore[assignment]

_COMPONENT_NAME = "nblane_goal_presence"
_FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"
_JS_ASSET = _FRONTEND_DIR / "assets" / "goal-presence.js"
_CSS_ASSET = _FRONTEND_DIR / "assets" / "goal-presence.css"

_component_func = None


def goal_presence_component_available() -> bool:
    """Return True when the built React bundle is present."""
    return _JS_ASSET.is_file() and _CSS_ASSET.is_file()


def _get_component_func():
    """Declare the v2 component lazily and fail closed when unavailable."""
    global _component_func
    if _component_func is not None:
        return _component_func
    if components_v2 is None or not goal_presence_component_available():
        return None

    try:
        _component_func = components_v2.component(
            _COMPONENT_NAME,
            css="assets/goal-presence.css",
            js="assets/goal-presence.js",
            isolate_styles=True,
        )
    except Exception:
        # Editable installs may not have refreshed the v2 manifest yet. Inline
        # assets keep local development working while pyproject still declares
        # the package-backed component for distribution.
        css_text = _CSS_ASSET.read_text(encoding="utf-8")
        if "\n" not in css_text.strip():
            css_text = css_text.replace("}", "}\n", 1)
        _component_func = components_v2.component(
            f"{_COMPONENT_NAME}_inline",
            css=css_text,
            js=_JS_ASSET.read_text(encoding="utf-8"),
            isolate_styles=True,
        )
    return _component_func


def st_goal_presence(
    *,
    payload: dict[str, Any],
    key: str,
    align: str = "left",
) -> Any | None:
    """Render the React goal presence chip."""
    component_func = _get_component_func()
    if component_func is None:
        return None
    clean_payload = dict(payload)
    clean_payload["align"] = align if align in {"left", "right"} else "left"
    return component_func(
        data=clean_payload,
        key=key,
        width="stretch",
        height="content",
    )
