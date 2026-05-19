"""AI backend implementations hidden behind AI Actions."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from nblane.core import llm
from nblane.core.agent_tasks import (
    AGENT_HARNESSES,
    AGENT_ROLES,
    create_agent_task,
)
from nblane.core.ai.actions import (
    AIActionRequest,
    AIActionResult,
    AIActionSpec,
)
from nblane.core.ai.prompts import prompt_for_action
from nblane.core.ai.runs import new_run_id
from nblane.core.ai.structured import validate_json_response


class DirectLLMBackend:
    """Direct OpenAI-compatible LLM backend."""

    name = "direct_llm"

    def run(
        self,
        request: AIActionRequest,
        spec: AIActionSpec,
    ) -> AIActionResult:
        """Run one action through ``nblane.core.llm``."""

        run_id = new_run_id(request.action)
        if not llm.is_configured():
            return AIActionResult(
                ok=False,
                action=request.action,
                backend=self.name,
                run_id=run_id,
                error="ai_not_configured: LLM_API_KEY is not configured",
            )
        prompt = prompt_for_action(request, spec)
        raw = llm.chat(
            prompt.system,
            prompt.user,
            temperature=spec.temperature,
        )
        if raw.startswith("LLM error:") or raw.startswith(
            "AI features not configured"
        ):
            return AIActionResult(
                ok=False,
                action=request.action,
                backend=self.name,
                run_id=run_id,
                content=raw,
                error=f"provider_error: {raw}",
            )
        if spec.output_mode == "json":
            validation = validate_json_response(raw, spec.schema)
            if not validation.ok:
                return AIActionResult(
                    ok=False,
                    action=request.action,
                    backend=self.name,
                    run_id=run_id,
                    content=raw,
                    structured=validation.data,
                    error=validation.error,
                )
            return AIActionResult(
                ok=True,
                action=request.action,
                backend=self.name,
                run_id=run_id,
                content=raw,
                structured=validation.data,
            )
        return AIActionResult(
            ok=True,
            action=request.action,
            backend=self.name,
            run_id=run_id,
            content=raw,
        )


class RuleFallbackBackend:
    """Deterministic fallback backend for unconfigured AI or low-risk flows."""

    name = "rule_fallback"

    def run(
        self,
        request: AIActionRequest,
        spec: AIActionSpec,
    ) -> AIActionResult:
        """Return a deterministic candidate matching the action contract."""

        run_id = new_run_id(request.action)
        structured, warnings = fallback_structured(request, spec)
        return AIActionResult(
            ok=True,
            action=request.action,
            backend=self.name,
            run_id=run_id,
            content=json.dumps(structured, ensure_ascii=False, indent=2),
            structured=structured,
            warnings=warnings,
        )


class WorkflowAgentBackend:
    """Minimal nblane workflow-agent skeleton.

    The MVP workflow reads the business payload and returns deterministic
    candidates. It deliberately avoids tool loops and direct writeback until the
    runtime grows a real permission model.
    """

    name = "workflow_agent"

    def run(
        self,
        request: AIActionRequest,
        spec: AIActionSpec,
    ) -> AIActionResult:
        """Run the local workflow skeleton for one action."""

        run_id = new_run_id(request.action)
        structured, warnings = fallback_structured(request, spec)
        warnings = [
            "WorkflowAgentBackend MVP used deterministic local workflow.",
            *warnings,
        ]
        return AIActionResult(
            ok=True,
            action=request.action,
            backend=self.name,
            run_id=run_id,
            content=json.dumps(structured, ensure_ascii=False, indent=2),
            structured=structured,
            warnings=warnings,
        )


class ExternalAgentBackend:
    """Codex/OpenCode adapter that creates reviewable handoff tasks."""

    name = "external_agent"

    def run(
        self,
        request: AIActionRequest,
        spec: AIActionSpec,
    ) -> AIActionResult:
        """Create an external harness task, but do not execute it."""

        run_id = new_run_id(request.action)
        payload = request.payload if isinstance(request.payload, dict) else {}
        target = _target_harness(payload)
        role = _role_for_action(request.action, payload)
        input_refs = _merge_refs(
            request.context_refs,
            payload.get("input_refs"),
            payload.get("source_refs"),
        )
        expected_outputs = _expected_outputs(request.action, payload)
        title = (
            _clean_text(payload.get("title"))
            or _clean_text(payload.get("task_title"))
            or _clean_text(payload.get("kanban_task_title"))
            or request.action
        )
        related = payload.get("related") if isinstance(payload.get("related"), dict) else {}
        for key in (
            "kanban_task_id",
            "goal_id",
            "research_source_id",
            "project_id",
        ):
            value = _clean_text(payload.get(key))
            if value:
                related[key] = value
        task = create_agent_task(
            request.profile,
            target_harness=target,
            role=role,
            title=title,
            input_refs=input_refs,
            expected_outputs=expected_outputs,
            related=related,
            payload=payload,
            action_name=request.action,
            run_id=run_id,
            status="ready",
        )
        structured = {
            "task_id": task["id"],
            "target_harness": target,
            "role": role,
            "status": task["status"],
            "input_refs": input_refs,
            "expected_outputs": expected_outputs,
            "related": related,
        }
        content = (
            f"Created {target} handoff task {task['id']} for {role}. "
            "Run `nblane agent handoff "
            f"{task['id']} --target {target} --profile {request.profile}` "
            "to generate the external harness instructions."
        )
        return AIActionResult(
            ok=True,
            action=request.action,
            backend=self.name,
            run_id=run_id,
            content=content,
            structured=structured,
            warnings=[
                "External harness was not executed; task is ready for reviewable handoff.",
            ],
        )


def default_backends() -> dict[str, object]:
    """Return the standard backend registry."""

    backends = [
        DirectLLMBackend(),
        WorkflowAgentBackend(),
        ExternalAgentBackend(),
        RuleFallbackBackend(),
    ]
    return {backend.name: backend for backend in backends}


def fallback_structured(
    request: AIActionRequest,
    spec: AIActionSpec,
) -> tuple[dict[str, Any], list[str]]:
    """Return deterministic action-shaped data and warnings."""

    payload = request.payload if isinstance(request.payload, dict) else {}
    warning = "AI fallback used deterministic candidate generation."
    action = spec.name
    if action == "research.reading_draft":
        source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
        excerpt = _clean_text(payload.get("excerpt") or source.get("excerpt"))
        summary_source = (
            excerpt
            or _clean_text(source.get("summary"))
            or _clean_text(source.get("notes"))
            or _clean_text(source.get("title"))
        )
        summary = " ".join(summary_source.split()[:80]).strip()
        return (
            {
                "excerpt": excerpt,
                "translation": "",
                "summary": summary,
                "key_points": [],
                "claim_candidates": [],
                "citations": [],
                "synthesis_notes": "",
                "generated_by": "rule_fallback",
            },
            [warning],
        )
    if action == "research.recommend_sources":
        sources = _list_payload(payload, "sources", "source_inbox", "items")
        recommendations = []
        for source in sources[:5]:
            if not isinstance(source, dict):
                continue
            ref = _clean_text(source.get("id") or source.get("ref"))
            title = _clean_text(source.get("title") or ref)
            if not ref and not title:
                continue
            recommendations.append(
                {
                    "source_ref": ref,
                    "title": title,
                    "priority": "review",
                    "reason": "Available source candidate from deterministic workflow.",
                }
            )
        return (
            {
                "recommendations": recommendations,
                "source_candidates": recommendations,
                "notes": [warning],
            },
            [warning],
        )
    if action == "research.paper_search_codex":
        query = _clean_text(payload.get("query") or payload.get("goal"))
        manual_results = _list_payload(payload, "results", "items", "sources")
        results = []
        for item in manual_results[:10]:
            if not isinstance(item, dict):
                continue
            url = _clean_text(item.get("url") or item.get("pdf_url"))
            doi = _clean_text(item.get("doi"))
            ref = _clean_text(item.get("id") or item.get("ref") or doi or url)
            title = _clean_text(item.get("title") or ref)
            if not (title or url or doi):
                continue
            results.append(
                {
                    "title": title,
                    "url": url,
                    "doi": doi,
                    "provider_refs": _merge_refs(item.get("provider_refs"), ref),
                    "reason": "Provided search candidate; verify URL/DOI before import.",
                }
            )
        warnings = [warning]
        if not results:
            warnings.append(
                "No provider-backed paper search was executed; supply verified URL/DOI refs before import."
            )
        return (
            {
                "query": query,
                "results": results,
                "warnings": warnings,
                "ref": _paper_ref(request, payload),
            },
            warnings,
        )
    if action == "research.paper_translate":
        segments = _list_payload(payload, "segments", "chunks", "items")
        target_lang = _clean_text(payload.get("target_lang")) or _reply_language(payload)
        translations = []
        warnings = [warning]
        for index, segment in enumerate(segments[:50], start=1):
            if not isinstance(segment, dict):
                continue
            text = _clean_text(segment.get("text") or segment.get("source_text"))
            segment_id = _clean_text(
                segment.get("segment_id")
                or segment.get("id")
                or segment.get("ref")
                or f"segment:{index:04d}"
            )
            source_hash = _clean_text(
                segment.get("source_hash")
                or segment.get("text_hash")
                or _hash_text(text)
            )
            translations.append(
                {
                    "segment_id": segment_id,
                    "source_hash": source_hash,
                    "source_text": text,
                    "target_lang": target_lang,
                    "translated_text": "",
                    "glossary": {},
                    "cited_segment_refs": [segment_id] if segment_id else [],
                    "generated_by": "rule_fallback",
                }
            )
        if not translations:
            warnings.append("No segments were provided for translation.")
        return (
            {
                "translations": translations,
                "warnings": warnings,
                "ref": _paper_ref(request, payload),
            },
            warnings,
        )
    if action == "research.paper_explain_selection":
        refs = _paper_refs(request, payload)
        selected = _clean_text(
            payload.get("selected_text")
            or payload.get("selection")
            or payload.get("excerpt")
        )
        warnings = [warning]
        if not any(refs.values()):
            warnings.append("No cited refs were provided; explanation is limited to the selected text.")
        return (
            {
                "explanation": _first_sentence(selected),
                **refs,
                "warnings": warnings,
                "ref": _paper_ref(request, payload),
            },
            warnings,
        )
    if action == "research.paper_source_guide":
        refs = _paper_refs(request, payload)
        segments = _list_payload(payload, "segments", "chunks", "items")
        tldr = _paper_summary(payload, segments)
        return (
            {
                "tldr": tldr,
                "contributions": [],
                "methods": [],
                "datasets": [],
                "results": [],
                "limitations": [],
                "open_questions": [],
                "key_terms": [],
                "section_summaries": _section_summaries(segments),
                **refs,
                "warnings": [warning],
                "ref": _paper_ref(request, payload),
            },
            [warning],
        )
    if action == "research.paper_qa":
        refs = _paper_refs(request, payload)
        warnings = [warning]
        if not any(refs.values()):
            warnings.append(
                "No input refs were provided; fallback cannot answer without paper evidence."
            )
        question = _clean_text(payload.get("question") or payload.get("query"))
        answer = "" if not any(refs.values()) else _paper_summary(payload, [])
        return (
            {
                "question": question,
                "answer": answer,
                **refs,
                "warnings": warnings,
                "ref": _paper_ref(request, payload),
            },
            warnings,
        )
    if action == "research.paper_claim_extract":
        refs = _paper_refs(request, payload)
        claims = []
        for item in _list_payload(payload, "claim_candidates", "claims")[:20]:
            if not isinstance(item, dict):
                continue
            text = _clean_text(item.get("text") or item.get("claim") or item.get("summary"))
            if not text:
                continue
            claims.append(
                {
                    "text": text,
                    "status": "candidate",
                    "cited_segment_refs": refs["cited_segment_refs"],
                    "cited_chunk_refs": refs["cited_chunk_refs"],
                    "cited_annotation_refs": refs["cited_annotation_refs"],
                }
            )
        return (
            {
                "claim_candidates": claims,
                **refs,
                "warnings": [warning],
                "ref": _paper_ref(request, payload),
            },
            [warning],
        )
    if action == "research.paper_deep_read_codex":
        refs = _paper_refs(request, payload)
        warnings = [warning]
        if not any(refs.values()):
            warnings.append("No cited refs were provided for deep reading.")
        return (
            {
                "reading_plan": [
                    "Review supplied metadata, segments, chunks, and annotations.",
                    "Extract candidate findings with cited refs only.",
                    "Return uncertainties and follow-up questions for human review.",
                ],
                "findings": [],
                **refs,
                "warnings": warnings,
                "ref": _paper_ref(request, payload),
            },
            warnings,
        )
    if action == "research.paper_compare_codex":
        refs = _paper_refs(request, payload)
        warnings = [warning]
        if not any(refs.values()):
            warnings.append("No cited refs were provided for paper comparison.")
        return (
            {
                "comparisons": [],
                **refs,
                "warnings": warnings,
                "ref": _paper_ref(request, payload),
            },
            warnings,
        )
    if action == "resume.bullets_from_claims":
        claims = _list_payload(payload, "claims", "claim_candidates")
        bullets = []
        for claim in claims[:6]:
            if not isinstance(claim, dict):
                continue
            text = _clean_text(claim.get("text") or claim.get("summary"))
            if not text:
                continue
            refs = _merge_refs(
                [],
                claim.get("evidence_refs"),
                claim.get("source_refs"),
            )
            bullets.append({"text": text, "refs": refs})
        return {"bullets": bullets, "warnings": [warning]}, [warning]
    if action == "resume.target_for_job":
        target = _clean_text(payload.get("target") or payload.get("role")) or "target role"
        claim_refs = _ids_from_payload(payload, "claims", "claim_refs")
        evidence_refs = _ids_from_payload(payload, "evidence", "evidence_refs")
        project_refs = _ids_from_payload(payload, "projects", "project_refs")
        bullets = [
            {"text": _clean_text(item.get("text")), "refs": _merge_refs([], item.get("refs"))}
            for item in _list_payload(payload, "claims")[:4]
            if isinstance(item, dict) and _clean_text(item.get("text"))
        ]
        return (
            {
                "target": target,
                "summary": "",
                "bullets": bullets,
                "evidence_refs": evidence_refs,
                "claim_refs": claim_refs,
                "project_refs": project_refs,
                "warnings": [warning],
            },
            [warning],
        )
    if action == "output.blog_candidate":
        title = _clean_text(payload.get("title")) or "Draft candidate"
        return (
            {
                "title": title,
                "summary": _clean_text(payload.get("summary")),
                "outline": [],
                "source_refs": _merge_refs(
                    request.context_refs,
                    payload.get("source_refs"),
                    payload.get("evidence_refs"),
                ),
                "warnings": [warning],
            },
            [warning],
        )
    if action == "output.inline_patch":
        return {"patches": [], "warnings": [warning]}, [warning]
    if action == "kanban.task_alignment":
        title = _clean_text(payload.get("task_title")) or "this task"
        task_id = _clean_text(payload.get("task_id"))
        if _reply_language(payload) == "zh":
            return (
                {
                    "alignments": [
                        {
                            "label": "里程碑拆解",
                            "goal": f"把 {title} 拆成几个高层、可审阅的里程碑。",
                            "assumptions": [
                                "任务应保持在实现文件细节之上的粒度。"
                            ],
                            "subtask_style": "带证据或验证点的里程碑级子任务",
                            "task_id": task_id,
                        },
                        {
                            "label": "执行清单",
                            "goal": f"把 {title} 拆成具体但不过细的可跟踪步骤。",
                            "assumptions": [
                                "用户需要一组不乱编文件名的执行清单。"
                            ],
                            "subtask_style": "中等粒度、带产物的 checklist",
                            "task_id": task_id,
                        },
                        {
                            "label": "实现细节",
                            "goal": f"为 {title} 草拟更低层的执行步骤。",
                            "assumptions": [
                                "只有在用户确认时才进入文件或脚本级细节。"
                            ],
                            "subtask_style": "偏实现的步骤",
                            "task_id": task_id,
                        },
                    ],
                    "warnings": [warning],
                },
                [warning],
            )
        return (
            {
                "alignments": [
                    {
                        "label": "Milestone pass",
                        "goal": (
                            f"Turn {title} into a few high-level, "
                            "reviewable milestones."
                        ),
                        "assumptions": [
                            "The task should stay above implementation-file detail."
                        ],
                        "subtask_style": (
                            "milestone-level subtasks with evidence or validation"
                        ),
                        "task_id": task_id,
                    },
                    {
                        "label": "Execution checklist",
                        "goal": (
                            f"Break {title} into concrete but still "
                            "non-microscopic steps."
                        ),
                        "assumptions": [
                            "The user wants a trackable checklist without invented files."
                        ],
                        "subtask_style": "medium-grain checklist with artifacts",
                        "task_id": task_id,
                    },
                    {
                        "label": "Implementation detail",
                        "goal": f"Draft lower-level execution steps for {title}.",
                        "assumptions": [
                            "Only use file or script-level detail if the user confirms it."
                        ],
                        "subtask_style": "implementation-oriented steps",
                        "task_id": task_id,
                    },
                ],
                "warnings": [warning],
            },
            [warning],
        )
    if action == "kanban.subtasks":
        task_id = _clean_text(payload.get("task_id"))
        allowed_gap_ids = _merge_refs(payload.get("allowed_gap_ids"))
        gap_node_id = allowed_gap_ids[0] if allowed_gap_ids else ""
        if _reply_language(payload) == "zh":
            return (
                {
                    "subtasks": [
                        {
                            "title": "明确完成证据",
                            "reason": "先固定这个任务完成时应该留下什么可审阅材料。",
                            "gap_node_id": gap_node_id,
                            "artifact": "任务说明",
                            "verification": "卡片上写清完成证据。",
                        },
                        {
                            "title": "跑一轮可审阅的工作闭环",
                            "reason": "先产出一个可以检查的候选结果。",
                            "gap_node_id": gap_node_id,
                            "artifact": "候选输出",
                            "verification": "结果已附在任务中或被简要总结。",
                        },
                        {
                            "title": "记录结果和下一个阻塞点",
                            "reason": "让首轮工作后的下一步继续可执行。",
                            "gap_node_id": gap_node_id,
                            "artifact": "review note",
                            "verification": "记录包含结果、阻塞点和下一步动作。",
                        },
                    ],
                    "task_id": task_id,
                    "warnings": [warning],
                },
                [warning],
            )
        return (
            {
                "subtasks": [
                    {
                        "title": "Define completion evidence",
                        "reason": "Pins the expected artifact before execution.",
                        "gap_node_id": gap_node_id,
                        "artifact": "task note",
                        "verification": "Completion evidence is written on the card.",
                    },
                    {
                        "title": "Run one reviewable work pass",
                        "reason": "Creates a concrete candidate result for review.",
                        "gap_node_id": gap_node_id,
                        "artifact": "candidate output",
                        "verification": "Result is attached or summarized for review.",
                    },
                    {
                        "title": "Record result and next blocker",
                        "reason": "Keeps the task actionable after the first pass.",
                        "gap_node_id": gap_node_id,
                        "artifact": "review note",
                        "verification": "Note includes result, blocker, and next action.",
                    },
                ],
                "task_id": task_id,
                "warnings": [warning],
            },
            [warning],
        )
    if action == "work.remote_dev_task":
        return (
            {
                "task_id": "",
                "target_harness": _target_harness(payload),
                "role": _role_for_action(action, payload),
                "status": "blocked",
                "input_refs": _merge_refs(request.context_refs, payload.get("input_refs")),
                "expected_outputs": _expected_outputs(action, payload),
            },
            [warning],
        )
    return {"content": "", "warnings": [warning]}, [warning]


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _hash_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _first_sentence(value: str) -> str:
    text = " ".join(value.split())
    if not text:
        return ""
    for marker in (". ", "? ", "! ", "。", "？", "！"):
        pos = text.find(marker)
        if pos >= 0:
            return text[: pos + len(marker)].strip()
    return text[:240].strip()


def _paper_ref(request: AIActionRequest, payload: dict[str, Any]) -> str:
    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    refs = _merge_refs(
        payload.get("ref"),
        payload.get("source_id"),
        source.get("id"),
        source.get("ref"),
        request.context_refs,
    )
    return refs[0] if refs else ""


def _paper_refs(
    request: AIActionRequest,
    payload: dict[str, Any],
) -> dict[str, list[str]]:
    segment_refs = _merge_refs(
        payload.get("cited_segment_refs"),
        payload.get("segment_refs"),
        payload.get("segment_id"),
    )
    chunk_refs = _merge_refs(payload.get("cited_chunk_refs"), payload.get("chunk_refs"))
    annotation_refs = _merge_refs(
        payload.get("cited_annotation_refs"),
        payload.get("annotation_refs"),
        payload.get("annotation_id"),
    )
    for item in _list_payload(payload, "segments"):
        if isinstance(item, dict):
            segment_refs = _merge_refs(
                segment_refs,
                item.get("segment_id"),
                item.get("id"),
                item.get("ref"),
            )
    for item in _list_payload(payload, "chunks"):
        if isinstance(item, dict):
            chunk_refs = _merge_refs(chunk_refs, item.get("chunk_id"), item.get("id"), item.get("ref"))
    return {
        "cited_segment_refs": segment_refs,
        "cited_chunk_refs": chunk_refs,
        "cited_annotation_refs": annotation_refs,
    }


def _paper_summary(payload: dict[str, Any], segments: list[Any]) -> str:
    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    text = (
        _clean_text(payload.get("summary"))
        or _clean_text(source.get("summary"))
        or _clean_text(payload.get("abstract"))
        or _clean_text(source.get("abstract"))
    )
    if not text:
        for segment in segments:
            if isinstance(segment, dict):
                text = _clean_text(segment.get("text"))
                if text:
                    break
    return " ".join(text.split()[:80]).strip()


def _section_summaries(segments: list[Any]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for segment in segments[:8]:
        if not isinstance(segment, dict):
            continue
        text = _clean_text(segment.get("text"))
        if not text:
            continue
        segment_id = _clean_text(segment.get("segment_id") or segment.get("id") or segment.get("ref"))
        section_path = segment.get("section_path")
        if isinstance(section_path, list):
            section = " / ".join(_clean_text(item) for item in section_path if _clean_text(item))
        else:
            section = _clean_text(section_path or segment.get("section") or segment.get("locator"))
        summaries.append(
            {
                "section": section,
                "summary": " ".join(text.split()[:40]).strip(),
                "cited_segment_refs": [segment_id] if segment_id else [],
            }
        )
    return summaries


def _reply_language(payload: dict[str, Any]) -> str:
    clean = _clean_text(payload.get("reply_language")).lower()
    if clean in ("en", "zh"):
        return clean
    return llm.reply_language()


def _list_payload(payload: dict[str, Any], *keys: str) -> list[Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _merge_refs(*values: object) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        raw_items: list[object]
        if isinstance(value, list):
            raw_items = value
        elif isinstance(value, tuple):
            raw_items = list(value)
        elif isinstance(value, str):
            raw_items = [value]
        else:
            raw_items = []
        for item in raw_items:
            text = _clean_text(item)
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)
    return out


def _ids_from_payload(payload: dict[str, Any], list_key: str, refs_key: str) -> list[str]:
    refs = _merge_refs(payload.get(refs_key))
    if refs:
        return refs
    out: list[str] = []
    for item in _list_payload(payload, list_key):
        if not isinstance(item, dict):
            continue
        ref = _clean_text(item.get("id") or item.get("ref"))
        if ref:
            out.append(ref)
    return _merge_refs(out)


def _target_harness(payload: dict[str, Any]) -> str:
    target = _clean_text(
        payload.get("target_harness")
        or payload.get("harness")
        or payload.get("target")
    ).lower()
    return target if target in AGENT_HARNESSES else "codex"


def _role_for_action(action: str, payload: dict[str, Any]) -> str:
    role = _clean_text(payload.get("role")).lower()
    if role in AGENT_ROLES:
        return role
    if action.startswith("resume."):
        return "resume_strategist"
    if action.startswith("work."):
        return "remote_dev"
    if action.startswith("output."):
        return "reviewer"
    return "researcher"


def _expected_outputs(action: str, payload: dict[str, Any]) -> list[str]:
    explicit = _merge_refs(payload.get("expected_outputs"))
    if explicit:
        return explicit
    defaults = {
        "research.reading_draft": ["research_candidate", "claim_candidates"],
        "research.recommend_sources": ["source_candidates"],
        "resume.bullets_from_claims": ["resume_bullet_candidates"],
        "resume.target_for_job": ["resume_candidate", "traceable_refs"],
        "output.blog_candidate": ["blog_candidate"],
        "output.inline_patch": ["patch_candidate"],
        "kanban.task_alignment": ["alignment_candidates"],
        "kanban.subtasks": ["subtask_candidates"],
        "work.remote_dev_task": ["patch_review", "test_summary", "changed_paths"],
    }
    return defaults.get(action, ["candidate"])


__all__ = [
    "DirectLLMBackend",
    "ExternalAgentBackend",
    "RuleFallbackBackend",
    "WorkflowAgentBackend",
    "default_backends",
    "fallback_structured",
]
