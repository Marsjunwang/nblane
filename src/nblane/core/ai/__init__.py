"""Modular AI Action / AI Gateway public surface."""

from __future__ import annotations

from nblane.core.ai.actions import (
    AIActionRequest,
    AIActionResult,
    AIActionSpec,
    AIBackend,
)

_LAZY_EXPORTS = {
    "create_remote_dev_task": ("nblane.core.ai.gateway", "create_remote_dev_task"),
    "draft_resume_for_job": ("nblane.core.ai.gateway", "draft_resume_for_job"),
    "generate_reading_draft": ("nblane.core.ai.gateway", "generate_reading_draft"),
    "get_action_spec": ("nblane.core.ai.router", "get_action_spec"),
    "recommend_research_sources": (
        "nblane.core.ai.gateway",
        "recommend_research_sources",
    ),
    "registered_actions": ("nblane.core.ai.router", "registered_actions"),
    "run_ai_action": ("nblane.core.ai.gateway", "run_ai_action"),
    "run_json": ("nblane.core.ai.gateway", "run_json"),
    "run_text": ("nblane.core.ai.gateway", "run_text"),
}


def __getattr__(name: str):
    """Lazily expose gateway helpers without forcing backend imports."""

    if name not in _LAZY_EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _LAZY_EXPORTS[name]
    from importlib import import_module

    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value

__all__ = [
    "AIActionRequest",
    "AIActionResult",
    "AIActionSpec",
    "AIBackend",
    "create_remote_dev_task",
    "draft_resume_for_job",
    "generate_reading_draft",
    "get_action_spec",
    "recommend_research_sources",
    "registered_actions",
    "run_ai_action",
    "run_json",
    "run_text",
]
