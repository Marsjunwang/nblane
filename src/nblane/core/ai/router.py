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
    "research.paper_search_codex": AIActionSpec(
        name="research.paper_search_codex",
        owner="research",
        default_backend="local_codex_readonly",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            ["query", "results", "warnings", "ref"],
            properties={
                "results": {"type": "array"},
                "warnings": {"type": "array"},
                "query": {"type": "string"},
                "ref": {"type": "string"},
            },
        ),
    ),
    "research.paper_translate": AIActionSpec(
        name="research.paper_translate",
        owner="research",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            ["translations", "warnings", "ref"],
            properties={
                "translations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["source_hash"],
                        "properties": {
                            "segment_id": {"type": "string"},
                            "scope_type": {"type": "string"},
                            "scope_ref": {"type": "string"},
                            "source_hash": {"type": "string"},
                            "translated_text": {"type": "string"},
                            "target_lang": {"type": "string"},
                        },
                    },
                },
                "warnings": {"type": "array"},
                "ref": {"type": "string"},
            },
        ),
    ),
    "research.paper_explain_selection": AIActionSpec(
        name="research.paper_explain_selection",
        owner="research",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            [
                "explanation",
                "cited_segment_refs",
                "cited_chunk_refs",
                "cited_annotation_refs",
                "warnings",
                "ref",
            ],
            properties={
                "cited_segment_refs": {"type": "array"},
                "cited_chunk_refs": {"type": "array"},
                "cited_annotation_refs": {"type": "array"},
                "warnings": {"type": "array"},
                "ref": {"type": "string"},
            },
        ),
    ),
    "research.paper_source_guide": AIActionSpec(
        name="research.paper_source_guide",
        owner="research",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            [
                "tldr",
                "contributions",
                "methods",
                "datasets",
                "results",
                "limitations",
                "open_questions",
                "key_terms",
                "section_summaries",
                "cited_segment_refs",
                "cited_chunk_refs",
                "cited_annotation_refs",
                "warnings",
                "ref",
            ],
            properties={
                "contributions": {"type": "array"},
                "methods": {"type": "array"},
                "datasets": {"type": "array"},
                "results": {"type": "array"},
                "limitations": {"type": "array"},
                "open_questions": {"type": "array"},
                "key_terms": {"type": "array"},
                "section_summaries": {"type": "array"},
                "cited_segment_refs": {"type": "array"},
                "cited_chunk_refs": {"type": "array"},
                "cited_annotation_refs": {"type": "array"},
                "warnings": {"type": "array"},
                "ref": {"type": "string"},
            },
        ),
    ),
    "research.paper_review_card": AIActionSpec(
        name="research.paper_review_card",
        owner="research",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            [
                "tldr",
                "key_points",
                "innovations",
                "method",
                "experiments",
                "limitations",
                "usefulness",
                "scores",
                "score_rationale",
                "cited_segment_refs",
                "cited_chunk_refs",
                "cited_annotation_refs",
                "warnings",
                "ref",
            ],
            properties={
                "key_points": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "refs": {"type": "array"},
                        },
                    },
                },
                "innovations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "refs": {"type": "array"},
                        },
                    },
                },
                "method": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "refs": {"type": "array"},
                        },
                    },
                },
                "experiments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "refs": {"type": "array"},
                        },
                    },
                },
                "limitations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "refs": {"type": "array"},
                        },
                    },
                },
                "score_rationale": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "metric": {"type": "string"},
                            "reason": {"type": "string"},
                            "refs": {"type": "array"},
                        },
                    },
                },
                "scores": {
                    "type": "object",
                    "required": [
                        "novelty",
                        "technical_depth",
                        "evidence_quality",
                        "reproducibility",
                        "relevance",
                        "overall",
                    ],
                    "properties": {
                        "novelty": {"type": "number"},
                        "technical_depth": {"type": "number"},
                        "evidence_quality": {"type": "number"},
                        "reproducibility": {"type": "number"},
                        "relevance": {"type": "number"},
                        "overall": {"type": "number"},
                    },
                },
                "cited_segment_refs": {"type": "array"},
                "cited_chunk_refs": {"type": "array"},
                "cited_annotation_refs": {"type": "array"},
                "warnings": {"type": "array"},
                "ref": {"type": "string"},
            },
        ),
    ),
    "research.paper_qa": AIActionSpec(
        name="research.paper_qa",
        owner="research",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            [
                "question",
                "answer",
                "cited_segment_refs",
                "cited_chunk_refs",
                "cited_annotation_refs",
                "warnings",
                "ref",
            ],
            properties={
                "cited_segment_refs": {"type": "array"},
                "cited_chunk_refs": {"type": "array"},
                "cited_annotation_refs": {"type": "array"},
                "warnings": {"type": "array"},
                "ref": {"type": "string"},
            },
        ),
    ),
    "research.paper_claim_extract": AIActionSpec(
        name="research.paper_claim_extract",
        owner="research",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            [
                "claim_candidates",
                "cited_segment_refs",
                "cited_chunk_refs",
                "cited_annotation_refs",
                "warnings",
                "ref",
            ],
            properties={
                "claim_candidates": {"type": "array"},
                "cited_segment_refs": {"type": "array"},
                "cited_chunk_refs": {"type": "array"},
                "cited_annotation_refs": {"type": "array"},
                "warnings": {"type": "array"},
                "ref": {"type": "string"},
            },
        ),
    ),
    "research.paper_deep_read_codex": AIActionSpec(
        name="research.paper_deep_read_codex",
        owner="research",
        default_backend="local_codex_readonly",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            [
                "reading_plan",
                "findings",
                "cited_segment_refs",
                "cited_chunk_refs",
                "cited_annotation_refs",
                "warnings",
                "ref",
            ],
            properties={
                "reading_plan": {"type": "array"},
                "findings": {"type": "array"},
                "cited_segment_refs": {"type": "array"},
                "cited_chunk_refs": {"type": "array"},
                "cited_annotation_refs": {"type": "array"},
                "warnings": {"type": "array"},
                "ref": {"type": "string"},
            },
        ),
    ),
    "research.paper_compare_codex": AIActionSpec(
        name="research.paper_compare_codex",
        owner="research",
        default_backend="local_codex_readonly",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            [
                "comparisons",
                "cited_segment_refs",
                "cited_chunk_refs",
                "cited_annotation_refs",
                "warnings",
                "ref",
            ],
            properties={
                "comparisons": {"type": "array"},
                "cited_segment_refs": {"type": "array"},
                "cited_chunk_refs": {"type": "array"},
                "cited_annotation_refs": {"type": "array"},
                "warnings": {"type": "array"},
                "ref": {"type": "string"},
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
    "project.suggest_refs": AIActionSpec(
        name="project.suggest_refs",
        owner="project",
        default_backend="direct_llm",
        fallback_backend="rule_fallback",
        output_mode="json",
        activity_policy="candidate",
        schema=schema_for_keys(
            [
                "goal_refs",
                "task_refs",
                "evidence_refs",
                "source_refs",
                "output_refs",
                "rationale",
                "warnings",
            ],
            properties={
                "goal_refs": {"type": "array"},
                "task_refs": {"type": "array"},
                "evidence_refs": {"type": "array"},
                "source_refs": {"type": "array"},
                "output_refs": {"type": "array"},
                "warnings": {"type": "array"},
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
