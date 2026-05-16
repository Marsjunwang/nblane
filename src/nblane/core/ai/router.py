"""AI Action registry and backend routing."""

from __future__ import annotations

from typing import Any

from nblane.core.ai.actions import AIActionRequest, AIActionSpec
from nblane.core.ai.structured import schema_for_keys


ACTION_SPECS: dict[str, AIActionSpec] = {
    "research.reading_draft": AIActionSpec(
        name="research.reading_draft",
        owner="research",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            [
                "excerpt",
                "translation",
                "summary",
                "key_points",
                "claim_candidates",
                "citations",
                "synthesis_notes",
                "generated_by",
            ],
            properties={
                "key_points": {"type": "array"},
                "claim_candidates": {"type": "array"},
                "citations": {"type": "array"},
            },
        ),
    ),
    "research.recommend_sources": AIActionSpec(
        name="research.recommend_sources",
        owner="research",
        default_backend="workflow_agent",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            ["recommendations", "source_candidates", "notes"],
            properties={
                "recommendations": {"type": "array"},
                "source_candidates": {"type": "array"},
                "notes": {"type": "array"},
            },
        ),
    ),
    "resume.bullets_from_claims": AIActionSpec(
        name="resume.bullets_from_claims",
        owner="resume",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            ["bullets", "warnings"],
            properties={
                "bullets": {"type": "array"},
                "warnings": {"type": "array"},
            },
        ),
    ),
    "resume.target_for_job": AIActionSpec(
        name="resume.target_for_job",
        owner="resume",
        default_backend="workflow_agent",
        fallback_backend="direct_llm",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            [
                "target",
                "summary",
                "bullets",
                "evidence_refs",
                "claim_refs",
                "project_refs",
                "warnings",
            ],
            properties={
                "bullets": {"type": "array"},
                "evidence_refs": {"type": "array"},
                "claim_refs": {"type": "array"},
                "project_refs": {"type": "array"},
                "warnings": {"type": "array"},
            },
        ),
    ),
    "output.blog_candidate": AIActionSpec(
        name="output.blog_candidate",
        owner="output",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            ["title", "summary", "outline", "source_refs", "warnings"],
            properties={
                "outline": {"type": "array"},
                "source_refs": {"type": "array"},
                "warnings": {"type": "array"},
            },
        ),
    ),
    "output.inline_patch": AIActionSpec(
        name="output.inline_patch",
        owner="output",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="patch",
        schema=schema_for_keys(
            ["patches", "warnings"],
            properties={
                "patches": {"type": "array"},
                "warnings": {"type": "array"},
            },
        ),
    ),
    "kanban.task_alignment": AIActionSpec(
        name="kanban.task_alignment",
        owner="kanban",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            ["alignments"],
            properties={
                "alignments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["label", "goal"],
                        "properties": {
                            "label": {"type": "string"},
                            "goal": {"type": "string"},
                            "assumptions": {"type": "array"},
                            "subtask_style": {"type": "string"},
                        },
                    },
                },
            },
        ),
    ),
    "kanban.subtasks": AIActionSpec(
        name="kanban.subtasks",
        owner="kanban",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            ["subtasks"],
            properties={
                "subtasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["title"],
                        "properties": {
                            "title": {"type": "string"},
                            "reason": {"type": "string"},
                            "gap_node_id": {"type": "string"},
                            "artifact": {"type": "string"},
                            "verification": {"type": "string"},
                        },
                    },
                },
            },
        ),
    ),
    "work.remote_dev_task": AIActionSpec(
        name="work.remote_dev_task",
        owner="work",
        default_backend="external_agent",
        fallback_backend="workflow_agent",
        output_mode="json",
        activity_policy="patch",
        schema=schema_for_keys(
            [
                "task_id",
                "target_harness",
                "role",
                "status",
                "input_refs",
                "expected_outputs",
            ],
            properties={
                "input_refs": {"type": "array"},
                "expected_outputs": {"type": "array"},
            },
        ),
    ),
}


def get_action_spec(action_name: str) -> AIActionSpec | None:
    """Return a registered action spec by name."""

    return ACTION_SPECS.get(str(action_name or "").strip())


def registered_actions() -> list[str]:
    """Return registered action names in stable order."""

    return sorted(ACTION_SPECS)


def choose_backend(
    request: AIActionRequest,
    spec: AIActionSpec,
    available_backends: dict[str, Any],
) -> tuple[str, str]:
    """Return ``(backend_name, error)`` for a request."""

    preferred = (request.preferred_backend or "").strip()
    if preferred:
        if preferred in available_backends:
            return preferred, ""
        return "", f"Unknown preferred AI backend: {preferred}"

    default = spec.default_backend
    if default in available_backends:
        return default, ""
    fallback = spec.fallback_backend
    if fallback in available_backends:
        return fallback, ""
    return "", (
        f"No backend registered for action {spec.name}: "
        f"{default!r} or {fallback!r}"
    )


__all__ = [
    "ACTION_SPECS",
    "choose_backend",
    "get_action_spec",
    "registered_actions",
]
