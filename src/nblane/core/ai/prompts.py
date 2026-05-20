"""Prompt registry for AI Actions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from nblane.core import llm
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
    "research.paper_search_codex": (
        "Find paper candidates for import. Return only candidates with "
        "checkable URL, DOI, or provider refs, and include warnings for "
        "anything unverified."
    ),
    "research.paper_translate": (
        "Translate only the supplied paper segments. Preserve segment_id and "
        "source_hash for every translation row so stale cached translations "
        "can be rejected. Put the translated content in translated_text; do "
        "not use text for translated output."
    ),
    "research.paper_explain_selection": (
        "Explain only the supplied selection and cited paper context. Keep the "
        "answer source-scoped and cite segment, chunk, or annotation refs."
    ),
    "research.paper_source_guide": (
        "Produce a source-scoped reading guide from supplied metadata, "
        "segments, chunks, and annotations. Do not invent paper facts."
    ),
    "research.paper_review_card": (
        "Generate a fixed paper review scorecard using only the supplied "
        "source metadata, segments, chunks, and annotations. Cover key points, "
        "innovations, method, experiments, limitations, usefulness, and 0-5 "
        "scores. Every substantive claim and score rationale must cite "
        "segment, chunk, or annotation refs from the input. Do not invent "
        "claims, results, datasets, citations, or refs; add warnings when the "
        "provided evidence is insufficient."
    ),
    "research.paper_qa": (
        "Answer the question only from supplied paper refs. If no supporting "
        "refs are present, return a warning and do not guess."
    ),
    "research.paper_claim_extract": (
        "Extract claim candidates only from supplied paper context. Every "
        "candidate should remain review-first and carry cited refs."
    ),
    "research.paper_deep_read_codex": (
        "Prepare a deep-reading candidate from supplied paper material. Keep "
        "full text out of metadata and cite segment, chunk, or annotation refs."
    ),
    "research.paper_compare_codex": (
        "Compare supplied papers or paper contexts as a candidate analysis. "
        "Use cited refs and warnings instead of unsupported conclusions."
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
    "kanban.task_alignment": (
        "Offer candidate task understandings before drafting Kanban subtasks. "
        "Keep them grounded in the task and recent-work prior."
    ),
    "kanban.subtasks": (
        "Draft reviewable Kanban subtask candidates. Do not mutate the board "
        "or invent unrelated implementation detail."
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
    if spec.name == "kanban.task_alignment":
        return _kanban_alignment_prompt(request, spec, prompt_id)
    if spec.name == "kanban.subtasks":
        return _kanban_subtasks_prompt(request, spec, prompt_id)

    system = "\n".join(
        [
            "You are the nblane AI Gateway.",
            "You receive business payloads, not free-form user prompts.",
            "Return only the requested output contract.",
            _reply_language_instruction(),
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


def _kanban_alignment_prompt(
    request: AIActionRequest,
    spec: AIActionSpec,
    prompt_id: str,
) -> PromptBundle:
    """Return the provider prompt for Kanban task-scope alignment."""

    payload = request.payload
    task_text = _clean_text(payload.get("task_text"))
    ai_context = _clean_text(payload.get("ai_context"))
    prior_block = ""
    if ai_context:
        prior_block = (
            "Grounding prior from this profile and recent work:\n"
            f"{ai_context}\n\n"
        )
    system = (
        "You help a human confirm the intended scope and granularity of a "
        "kanban task before drafting subtasks. Reply with ONE JSON object "
        "only, no markdown. "
        f"{_reply_language_instruction(payload.get('reply_language'))} "
        'Schema: {"alignments": [{"label": "...", "goal": "...", '
        '"assumptions": ["..."], "subtask_style": "..."}]}. '
        "Return 2 or 3 distinct, plausible task understandings. The first "
        "option should be a high-level milestone understanding unless the "
        "task clearly asks for implementation details. Keep them concise and "
        "grounded in the task fields, existing subtasks, and recent-work "
        "prior. Do not invent dates, links, metrics, employers, or private "
        "facts."
    )
    user = (
        "Before drafting subtasks for the kanban task below, offer candidate "
        "understandings that the user can edit, combine, or replace with a "
        "personal clarification. Keep each candidate grounded in the task, "
        "existing subtasks, and prior; do not drift into unrelated domains. "
        "Prefer milestone-level decomposition by default.\n\n"
        f"{prior_block}"
        f"{task_text}\n"
    )
    return PromptBundle(
        system=system,
        user=user,
        prompt_id=prompt_id,
        prompt_version=spec.prompt_version,
    )


def _kanban_subtasks_prompt(
    request: AIActionRequest,
    spec: AIActionSpec,
    prompt_id: str,
) -> PromptBundle:
    """Return the provider prompt for Kanban subtask candidates."""

    payload = request.payload
    granularity = _clean_text(payload.get("granularity")) or "milestone"
    granularity = granularity.casefold()
    if granularity not in {"milestone", "checklist", "implementation"}:
        granularity = "milestone"
    detail_policy = {
        "milestone": (
            "Default granularity is milestone-level: each title should be a "
            "meaningful phase, outcome, checkpoint, or reviewable work slice. "
            "Do not decompose into tiny implementation files, helper scripts, "
            "environment checks, shell commands, directories, CSVs, or code "
            "artifacts unless the human explicitly requested implementation "
            "details. For reproduction, training, and evaluation tasks, prefer "
            "milestones such as complete one full training/evaluation run, "
            "align the evaluation protocol, compare baseline metrics and "
            "training time, record deltas, and decide follow-up fixes. For "
            "iup-pose reproduction, use the user's existing abstraction level "
            "as the guide: full training/evaluation and baseline effect/time "
            "alignment, not env_check.py, data_prep_4090.py, dataset_cache/, "
            "train_4090.sh, or hyperparam_mapping.csv."
        ),
        "checklist": (
            "Granularity is checklist-level: titles may be more concrete than "
            "milestones, but should still avoid invented filenames, scripts, "
            "directories, or one-off commands unless the task context already "
            "names them."
        ),
        "implementation": (
            "Granularity is implementation-level: detailed execution steps are "
            "allowed when useful, but do not invent irrelevant technology or "
            "unrelated domain framing."
        ),
    }[granularity]
    existing = _clean_text(payload.get("existing_subtasks"))
    if not existing:
        existing = "- (none)"
    alignment_context = _clean_text(payload.get("alignment_context"))
    alignment_block = ""
    if alignment_context:
        alignment_block = (
            "Confirmed task understanding:\n"
            f"{alignment_context}\n\n"
        )
    style_hint = _clean_text(payload.get("subtask_style_hint"))
    style_block = ""
    if style_hint:
        style_block = (
            "Preferred subtask style from this profile:\n"
            f"{style_hint}\n\n"
        )
    ai_context = _clean_text(payload.get("ai_context"))
    prior_block = ""
    if ai_context:
        prior_block = (
            "Grounding prior from this profile and recent work:\n"
            f"{ai_context}\n\n"
        )
    task_text = _clean_text(payload.get("task_text"))
    gap_analysis = _clean_text(payload.get("gap_analysis"))
    system = (
        "You draft kanban subtask drafts from the "
        "current task context and skill gap analysis. Reply with ONE JSON "
        "object only, no markdown. "
        f"{_reply_language_instruction(payload.get('reply_language'))} "
        'Schema: {"subtasks": [{"title": "...", "reason": "...", '
        '"gap_node_id": "...", "artifact": "...", '
        '"verification": "..."}]}. '
        "Return 3 to 5 subtasks. Do not replace, summarize, or repeat any "
        "existing subtask. Existing subtasks are evidence of the user's "
        "preferred abstraction level; use them as a granularity reference "
        "while still avoiding duplicates. "
        f"{detail_policy} "
        "Each item must be verifiable: put the expected evidence, review, "
        "metric, artifact, or observable result in verification. Artifact "
        "and verification are review metadata; do not force the title to be "
        "a file, command, or script. Keep each item tightly tied to the "
        "current task, outcome, blockers, details, and the listed gap. "
        "Do not output vague learning goals or generic items such as learn, "
        "study, research, improve, understand, explore, investigate, 学习, "
        "研究, 提升, or 了解. Prefer work slices that create evidence or unblock "
        "a specific gap. Use only gap_node_id values present in the "
        "analysis; use an empty string when no single node applies."
    )
    user = (
        "Kanban task:\n"
        f"{task_text}\n\n"
        f"{prior_block}"
        f"{alignment_block}"
        f"{style_block}"
        "Existing subtasks:\n"
        f"{existing}\n\n"
        "Gap analysis:\n"
        f"{gap_analysis}\n\n"
        "Drafting requirements:\n"
        f"- Output 3-5 new subtasks only at {granularity} granularity.\n"
        "- Do not duplicate or overwrite the existing subtasks above.\n"
        "- Default to outcome-level milestones unless the confirmed "
        "understanding explicitly asks for implementation details.\n"
        "- Do not invent file names, scripts, directories, CSVs, or commands "
        "when the task did not name them.\n"
        "- For reproduction/training/evaluation work, prefer full run, "
        "evaluation protocol alignment, baseline metric/time comparison, "
        "delta recording, and follow-up decision milestones.\n"
        "- Fill artifact and verification so a human can check completion.\n"
        "- Avoid generic learning/research/improvement wording.\n"
    )
    return PromptBundle(
        system=system,
        user=user,
        prompt_id=prompt_id,
        prompt_version=spec.prompt_version,
    )


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _reply_language_instruction(value: object = None) -> str:
    """Return a stable instruction for natural-language model fields."""

    reply_lang = _reply_language_value(value)
    if reply_lang == "zh":
        return (
            "Use Chinese for all natural-language field values, while keeping "
            "JSON keys, enum values, ids, file paths, and code identifiers "
            "unchanged."
        )
    return (
        "Use English for all natural-language field values, while keeping "
        "JSON keys, enum values, ids, file paths, and code identifiers "
        "unchanged."
    )


def _reply_language_value(value: object = None) -> str:
    """Return the requested reply language."""

    clean = _clean_text(value).lower()
    if clean in ("en", "zh"):
        return clean
    return llm.reply_language()


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
