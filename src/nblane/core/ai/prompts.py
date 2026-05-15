"""Prompt registry for AI Actions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from nblane.core.ai.actions import AIActionRequest, AIActionSpec


@dataclass(frozen=True)
class PromptBundle:
    """Resolved provider prompt for one action run."""

    system: str
    user: str
    prompt_id: str
    prompt_version: str


_ACTION_INSTRUCTIONS: dict[str, str] = {
    "research.reading_draft": (
        "Turn research source metadata and excerpts into source-scoped reading "
        "annotations. Do not invent facts. Any claims must remain candidates."
    ),
    "research.recommend_sources": (
        "Recommend which research inbox sources are worth reading or saving. "
        "Rank by relevance to the goal and explain uncertainty."
    ),
    "resume.bullets_from_claims": (
        "Draft resume bullets only from provided claims, evidence, projects, "
        "skills, and outputs. Keep unsupported material out."
    ),
    "resume.target_for_job": (
        "Create a target-specific resume candidate for the provided job text. "
        "Every suggested bullet should carry traceable refs."
    ),
    "output.blog_candidate": (
        "Draft a public-output candidate from supplied private materials. "
        "Avoid exposing private refs or unsupported claims."
    ),
    "output.inline_patch": (
        "Return a small candidate patch for the requested output edit. Keep it "
        "reviewable and do not publish."
    ),
    "work.remote_dev_task": (
        "Prepare a remote development handoff for an external coding harness. "
        "Return a candidate task, not code changes."
    ),
}


def prompt_for_action(
    request: AIActionRequest,
    spec: AIActionSpec,
) -> PromptBundle:
    """Return the system and user prompt for a registered AI Action."""

    prompt_id = spec.prompt_id or spec.name
    system = "\n".join(
        [
            "You are the nblane AI Gateway.",
            "You receive business payloads, not free-form user prompts.",
            "Return only the requested output contract.",
            "All writebacks are review-first candidates unless stated otherwise.",
            _ACTION_INSTRUCTIONS.get(
                spec.name,
                "Complete the action using only the provided payload.",
            ),
        ]
    )
    output_contract = {
        "mode": spec.output_mode,
        "schema": spec.schema or {},
        "activity_policy": spec.activity_policy,
    }
    user = json.dumps(
        {
            "action": spec.name,
            "profile": request.profile,
            "context_refs": request.context_refs,
            "require_review": request.require_review,
            "payload": request.payload,
            "output_contract": output_contract,
        },
        ensure_ascii=False,
        indent=2,
    )
    return PromptBundle(
        system=system,
        user=user,
        prompt_id=prompt_id,
        prompt_version=spec.prompt_version,
    )


def role_prompt(role: str) -> str:
    """Return a stable role prompt for generated external harness configs."""

    role_key = str(role or "").strip() or "researcher"
    prompts = {
        "researcher": (
            "Read nblane context and research sources, then produce source-scoped "
            "claim candidates, open questions, and synthesis notes. Never write "
            "accepted facts directly."
        ),
        "resume_strategist": (
            "Map job requirements to evidence, projects, claims, skills, and "
            "outputs. Produce resume candidates with refs for human review."
        ),
        "remote_dev": (
            "Work from the handed-off task, create patches for review, run "
            "relevant checks, and summarize changed paths. Do not silently change "
            "nblane profile facts or publish outputs."
        ),
        "reviewer": (
            "Review candidates for privacy, unsupported claims, permission drift, "
            "and schema fit. Return findings and safe next actions."
        ),
    }
    return prompts.get(role_key, prompts["researcher"])


__all__ = ["PromptBundle", "prompt_for_action", "role_prompt"]
