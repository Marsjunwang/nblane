"""Modular AI Action / AI Gateway public surface."""

from __future__ import annotations

from nblane.core.ai.actions import (
    AIActionRequest,
    AIActionResult,
    AIActionSpec,
    AIBackend,
)

_LAZY_EXPORTS = {
    "answer_paper_question": ("nblane.core.ai.gateway", "answer_paper_question"),
    "compare_papers_codex": ("nblane.core.ai.gateway", "compare_papers_codex"),
    "create_remote_dev_task": ("nblane.core.ai.gateway", "create_remote_dev_task"),
    "deep_read_paper_codex": ("nblane.core.ai.gateway", "deep_read_paper_codex"),
    "draft_kanban_subtasks": ("nblane.core.ai.gateway", "draft_kanban_subtasks"),
    "draft_kanban_task_alignment": (
        "nblane.core.ai.gateway",
        "draft_kanban_task_alignment",
    ),
    "draft_resume_for_job": ("nblane.core.ai.gateway", "draft_resume_for_job"),
    "explain_paper_selection": ("nblane.core.ai.gateway", "explain_paper_selection"),
    "extract_paper_claims": ("nblane.core.ai.gateway", "extract_paper_claims"),
    "generate_paper_source_guide": (
        "nblane.core.ai.gateway",
        "generate_paper_source_guide",
    ),
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
    "search_papers_codex": ("nblane.core.ai.gateway", "search_papers_codex"),
    "translate_paper_segments": ("nblane.core.ai.gateway", "translate_paper_segments"),
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
    "answer_paper_question",
    "compare_papers_codex",
    "create_remote_dev_task",
    "deep_read_paper_codex",
    "draft_kanban_subtasks",
    "draft_kanban_task_alignment",
    "draft_resume_for_job",
    "explain_paper_selection",
    "extract_paper_claims",
    "generate_paper_source_guide",
    "generate_reading_draft",
    "get_action_spec",
    "recommend_research_sources",
    "registered_actions",
    "run_ai_action",
    "run_json",
    "run_text",
    "search_papers_codex",
    "translate_paper_segments",
]
