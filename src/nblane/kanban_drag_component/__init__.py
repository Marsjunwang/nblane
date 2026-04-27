"""Drag-capable Kanban board Streamlit component.

The component is intentionally tiny and dependency-free: the static frontend
uses plain browser drag/drop plus Streamlit's component postMessage protocol.
It returns a full column order snapshot, and Python applies the domain rules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

from nblane.core.kanban_io import KANBAN_BOARD_SECTIONS
from nblane.core.models import KanbanTask

_FRONTEND_DIR = Path(__file__).parent / "frontend" / "static"

_component_func = None


def _get_component_func():
    """Declare the component lazily."""
    global _component_func
    if _component_func is None:
        _component_func = components.declare_component(
            "nblane_kanban_drag_board",
            path=str(_FRONTEND_DIR),
        )
    return _component_func


def _task_payload(task: KanbanTask) -> dict[str, Any]:
    """Return the compact card data the drag component needs."""
    subtitle_bits: list[str] = []
    for value in (
        task.context,
        task.outcome,
        task.why,
        task.blocked_by,
    ):
        text = str(value or "").strip()
        if text:
            subtitle_bits.append(text)
            break
    dates = " -> ".join(
        value
        for value in (
            task.started_on or "",
            task.completed_on or "",
        )
        if value
    )
    if dates:
        subtitle_bits.append(dates)
    if task.subtasks:
        done = sum(1 for item in task.subtasks if item.done)
        subtitle_bits.append(f"{done}/{len(task.subtasks)} subtasks")
    return {
        "id": task.id,
        "title": task.title,
        "subtitle": " · ".join(subtitle_bits),
        "crystallized": task.crystallized,
    }


def render_kanban_drag_board(
    *,
    sections: dict[str, list[KanbanTask]],
    labels: dict[str, str],
    key: str,
    height: int = 430,
) -> dict[str, Any] | None:
    """Render a drag board and return the latest order snapshot.

    The return value is ``{"columns": [{"section": str, "task_ids": [...]}, ...]}``
    when the user clicks Apply after dragging.
    """
    component_func = _get_component_func()
    payload = {
        "sections": [
            {
                "key": section,
                "label": labels.get(section, section),
                "tasks": [
                    _task_payload(task)
                    for task in sections.get(section, [])
                    if task.id
                ],
            }
            for section in KANBAN_BOARD_SECTIONS
        ],
        "height": height,
    }
    result: Any = component_func(
        board=payload,
        key=key,
        default=None,
    )
    return result if isinstance(result, dict) else None
