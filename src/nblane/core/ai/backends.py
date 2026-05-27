"""AI backend implementations hidden behind AI Actions."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import replace
from datetime import date
from typing import Any

from nblane.core import llm
from nblane.core.jsonutil import extract_json_object
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
from nblane.core.ai.structured import validate_json_response, validate_schema


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
        use_stream = _stream_llm_action(request)
        raw = llm.chat(
            prompt.system,
            prompt.user,
            temperature=spec.temperature,
            stream=use_stream,
            model=_model_override(request.payload),
            timeout=_positive_float_override(
                request.payload,
                "model_timeout_seconds",
                "llm_timeout_seconds",
                "timeout_seconds",
            ),
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


class LocalReadonlyCodexBackend:
    """Run Codex locally as a read-only advanced LLM for JSON AI Actions."""

    name = "local_codex_readonly"

    def run(
        self,
        request: AIActionRequest,
        spec: AIActionSpec,
    ) -> AIActionResult:
        """Run one action through ``codex exec --sandbox read-only``."""

        run_id = new_run_id(request.action)
        prompt = prompt_for_action(request, spec)
        codex_prompt = _readonly_codex_prompt(request, spec, prompt.system, prompt.user)
        from nblane.core import codex_adapter

        codex_profile = request.runtime_profile or request.profile
        enable_search = request.action == "research.paper_search_codex"
        codex_home_policy = _codex_home_policy(request.payload)
        config = codex_adapter.current_config(
            profile=codex_profile or None,
            codex_home_policy=codex_home_policy,
        )
        model = _model_override(request.payload, "codex_model", "deep_read_model", "ai_model")
        timeout_seconds = _positive_float_override(
            request.payload,
            "codex_timeout_seconds",
            "timeout_seconds",
        )
        if model:
            config = replace(config, model=model)
        reasoning_effort = _codex_reasoning_effort_override(request.payload) if enable_search else ""
        result = codex_adapter.run_readonly_codex_prompt(
            codex_profile,
            codex_prompt,
            config=config,
            timeout_seconds=timeout_seconds,
            enable_search=enable_search,
            reasoning_effort=reasoning_effort,
            progress_callback=request.progress_callback,
            cancel_check=request.cancel_callback,
            idle_timeout_seconds=_positive_float_override(
                request.payload,
                "codex_idle_timeout_seconds",
                "idle_timeout_seconds",
            ),
        )
        raw = result.output
        warnings = _merge_warning_texts(getattr(result, "warnings", []) or [])
        if not result.ok:
            error = codex_adapter.readable_codex_error(
                getattr(result, "error", ""),
                getattr(result, "stderr", ""),
                raw,
                getattr(result, "stdout", ""),
            )
            return AIActionResult(
                ok=False,
                action=request.action,
                backend=self.name,
                run_id=run_id,
                warnings=_merge_warning_texts(warnings, error),
                error=error,
            )

        data = extract_json_object(raw)
        if not isinstance(data, dict):
            error = "codex_json_error: response did not contain a JSON object"
            return AIActionResult(
                ok=False,
                action=request.action,
                backend=self.name,
                run_id=run_id,
                warnings=_merge_warning_texts(warnings, error),
                error=error,
            )

        validation_error = validate_schema(data, spec.schema or {})
        if validation_error:
            error = f"codex_schema_error: {validation_error}"
            return AIActionResult(
                ok=False,
                action=request.action,
                backend=self.name,
                run_id=run_id,
                structured=data,
                warnings=_merge_warning_texts(warnings, error),
                error=error,
            )

        warnings = _merge_warning_texts(warnings, data.get("warnings"))
        return AIActionResult(
            ok=True,
            action=request.action,
            backend=self.name,
            run_id=run_id,
            content=json.dumps(data, ensure_ascii=False, indent=2),
            structured=data,
            warnings=warnings,
        )


def _readonly_codex_prompt(
    request: AIActionRequest,
    spec: AIActionSpec,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Combine an AI Action prompt with Codex read-only operating bounds."""

    if request.action == "research.paper_search_codex":
        return _readonly_codex_paper_search_prompt(request, system_prompt)

    schema = json.dumps(spec.schema or {}, ensure_ascii=False, indent=2)
    return "\n\n".join(
        [
            (
                "You are Codex used inside nblane Paper Reading Studio through "
                "the AI Gateway as a local read-only advanced LLM."
            ),
            "\n".join(
                [
                    "Boundaries:",
                    "- Codex is read-only.",
                    "- Do not edit files.",
                    "- Do not generate patches.",
                    "- Do not run code-changing commands.",
                    "- Do not write profile facts.",
                    "- Do not create or submit agent-task candidates.",
                    "- Return one JSON object only, no markdown.",
                    "- If search/network is unavailable, put that in warnings.",
                ]
            ),
            (
                "All outputs are reviewable candidates. For paper search, return "
                "only candidates with a checkable URL, DOI, arXiv id, Semantic "
                "Scholar id, or provider_refs. Do not write research/sources.yaml "
                "or import papers."
            ),
            f"Action: {request.action}",
            f"Profile: {request.profile}",
            "Required JSON schema:\n" + schema,
            "System prompt from AI Gateway:\n" + str(system_prompt or "").strip(),
            "Business payload JSON:\n" + str(user_prompt or "").strip(),
        ]
    )


def _readonly_codex_paper_search_prompt(request: AIActionRequest, system_prompt: str) -> str:
    """Build a compact live-search prompt for PDF-ready paper discovery."""

    payload = request.payload if isinstance(request.payload, dict) else {}
    filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}
    try:
        limit = max(1, min(int(payload.get("limit") or filters.get("limit") or 5), 10))
    except (TypeError, ValueError):
        limit = 5
    query = _clean_text(payload.get("query"))
    query_variants = _list_payload(payload, "query_variants")
    compact_payload = {
        "query": query,
        "query_variants": query_variants,
        "limit": limit,
        "year_from": _clean_text(filters.get("year_from")),
        "year_to": _clean_text(filters.get("year_to")),
        "require_pdf": True,
        "current_date": date.today().isoformat(),
        "codex_reasoning_effort": _codex_reasoning_effort_override(payload),
        "codex_search_depth": _clean_text(payload.get("codex_search_depth")) or "quick",
        "profile_context_policy": _clean_text(payload.get("profile_context_policy")) or "not_sent_for_discovery",
    }
    return "\n\n".join(
        [
            (
                "You are Codex used inside nblane Paper Reading Studio as a "
                "local read-only advanced LLM with live web search."
            ),
            "\n".join(
                [
                    "Boundaries:",
                    "- Codex is read-only.",
                    "- Do not edit files.",
                    "- Do not generate patches.",
                    "- Do not run code-changing commands.",
                    "- You may run read-only commands such as python/curl to query arXiv APIs, search pages, and inspect web results.",
                    "- Do not write profile facts.",
                    "- Return one JSON object only, no markdown.",
                ]
            ),
            (
                "Task: use web search immediately to find PDF-ready paper candidates. "
                f"Stop as soon as you have up to {limit} strong candidates. Do not do an exhaustive survey."
            ),
            (
                "Search behavior: start with query_variants. If the query contains Chinese intent "
                "words such as 最新论文, translate the intent before searching. For latest/recent "
                "requests, search arXiv/OpenReview/project pages by submission date when possible, "
                "then verify that candidates are robotics/embodied-AI papers. "
                "If VLA is ambiguous, robotics VLA normally means Vision-Language-Action; avoid "
                "astronomy Very Large Array unless the user asks for astronomy."
            ),
            (
                "Acceptance rules: include only papers with a direct downloadable pdf_url. "
                "Do not limit discovery to a fixed provider. Prefer arXiv, OpenReview, "
                "publisher PDFs, author project pages, and verified paper pages."
            ),
            (
                "For each result, include title, year when known, canonical_url, pdf_url, "
                "why_relevant, ai_summary, and explanation_links. Write ai_summary and "
                "why_relevant in the user's query language. explanation_links may include "
                "verified project pages, blogs, videos, Zhihu, Xiaohongshu, or other "
                "trustworthy explainers; use an empty list rather than inventing links."
            ),
            "Return this strict JSON shape only:",
            (
                '{"query":"","results":[{"title":"","year":"","canonical_url":"","pdf_url":"",'
                '"doi":"","arxiv_id":"","provider_refs":[],"abstract":"","ai_summary":"",'
                '"why_relevant":"","explanation_links":[{"title":"","url":"","source":""}]}],'
                '"warnings":[],"ref":"paper_search"}'
            ),
            "Compact search payload:\n" + json.dumps(compact_payload, ensure_ascii=False, indent=2),
            "System instruction summary:\n" + _clean_text(system_prompt),
        ]
    )


def _merge_warning_texts(*values: object) -> list[str]:
    """Normalize warnings without retaining duplicate long blobs."""

    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        raw_items = value if isinstance(value, (list, tuple, set)) else [value]
        for item in raw_items:
            text = _clean_text(item)
            if not text:
                continue
            if len(text) > 500:
                text = text[:499].rstrip() + "..."
            if text in seen:
                continue
            seen.add(text)
            out.append(text)
    return out


def _model_override(payload: dict[str, Any], *keys: str) -> str:
    """Return an optional per-action model override from a business payload."""

    for key in keys or ("ai_model", "llm_model", "model_override"):
        value = _clean_text(payload.get(key))
        if value:
            return value
    return ""


def _positive_float_override(payload: dict[str, Any], *keys: str) -> float | None:
    """Return an optional positive float override from a business payload."""

    for key in keys:
        value = payload.get(key)
        if value in (None, ""):
            continue
        try:
            clean = float(value)
        except (TypeError, ValueError):
            continue
        if clean > 0:
            return clean
    return None


def _stream_llm_action(request: AIActionRequest) -> bool:
    """Return True for long JSON actions that are safer over streaming HTTP."""

    if request.action != "research.paper_translate":
        return False
    configured = (
        str(os.getenv("NBLANE_STREAM_PAPER_TRANSLATION", "1") or "")
        .strip()
        .lower()
    )
    return configured not in {"0", "false", "no", "off"}


def _codex_reasoning_effort_override(payload: dict[str, Any]) -> str:
    """Return the requested Codex reasoning effort for paper search."""

    clean = _clean_text(
        payload.get("codex_reasoning_effort")
        or payload.get("reasoning_effort")
    ).lower()
    if clean in {"low", "medium", "high", "xhigh"}:
        return clean
    depth = _clean_text(
        payload.get("codex_search_depth")
        or payload.get("search_depth")
        or payload.get("codex_depth")
    ).lower()
    if depth in {"deep", "xhigh", "thorough", "careful"}:
        return "xhigh"
    for key in ("codex_deep_search", "deep_search"):
        value = payload.get(key)
        if isinstance(value, bool) and value:
            return "xhigh"
        if _clean_text(value).lower() in {"1", "true", "yes", "on"}:
            return "xhigh"
    return "medium"


def _codex_home_policy(payload: dict[str, Any]) -> str:
    """Return which Codex home read-only live search should use."""

    clean = _clean_text(
        payload.get("codex_home_policy")
        or payload.get("codex_home_mode")
        or payload.get("code_home_policy")
    ).lower()
    if not clean:
        import os

        clean = _clean_text(
            os.getenv("NBLANE_CODEX_HOME_POLICY")
            or os.getenv("NBLANE_PAPER_SEARCH_CODEX_HOME_POLICY")
        ).lower()
    if clean in {"profile", "isolated", "profile_isolated", "web_profile"}:
        return "profile"
    if clean in {"default", "global", "terminal", "terminal_default", "shared"}:
        return "default"
    return "default"


def default_backends() -> dict[str, object]:
    """Return the standard backend registry."""

    backends = [
        DirectLLMBackend(),
        WorkflowAgentBackend(),
        ExternalAgentBackend(),
        LocalReadonlyCodexBackend(),
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
                    "abstract": _clean_text(item.get("abstract") or item.get("summary")),
                    "ai_summary": _clean_text(item.get("ai_summary") or item.get("plain_language_summary")),
                    "explanation_links": item.get("explanation_links") if isinstance(item.get("explanation_links"), list) else [],
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
                    "scope_type": _clean_text(segment.get("scope_type")),
                    "scope_ref": _clean_text(segment.get("scope_ref")),
                    "page": segment.get("page"),
                    "order": segment.get("order"),
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
    if action == "research.paper_review_card":
        refs = _paper_refs(request, payload)
        segments = _list_payload(payload, "segments", "chunks", "items")
        tldr = _paper_summary(payload, segments)
        warnings = [warning]
        if not any(refs.values()):
            warnings.append(
                "No cited refs were provided; review card scores are conservative defaults."
            )
        return (
            {
                "tldr": tldr,
                "key_points": [],
                "innovations": [],
                "method": [],
                "experiments": [],
                "limitations": [],
                "usefulness": "",
                "scores": _default_review_scores(),
                "score_rationale": [
                    {
                        "metric": "overall",
                        "reason": (
                            "Fallback could not evaluate the paper beyond "
                            "provided refs; human review is required."
                        ),
                        "refs": _merge_refs(
                            refs["cited_segment_refs"],
                            refs["cited_chunk_refs"],
                            refs["cited_annotation_refs"],
                        ),
                    }
                ],
                **refs,
                "warnings": warnings,
                "ref": _paper_ref(request, payload),
            },
            warnings,
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
        return _deep_read_fallback_structured(request, payload, warning)
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
    if action == "project.suggest_refs":
        suggestions = {
            field: _project_candidate_refs(payload, field)
            for field in (
                "goal_refs",
                "task_refs",
                "evidence_refs",
                "source_refs",
                "output_refs",
            )
        }
        rationale = (
            "按项目标题、摘要、备注与候选项标签的关键词重合生成候选关联。"
            if _reply_language(payload) == "zh"
            else "Suggested from keyword overlap between the project text and candidate labels."
        )
        return (
            {
                **suggestions,
                "rationale": rationale,
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


def _deep_read_fallback_structured(
    request: AIActionRequest,
    payload: dict[str, Any],
    warning: str,
) -> tuple[dict[str, Any], list[str]]:
    refs = _paper_refs(request, payload)
    segments = [item for item in _list_payload(payload, "segments", "items") if isinstance(item, dict)]
    warnings = [warning]
    if not segments:
        warnings.append("No supplied paper segments were available for fallback deep reading.")
        return (
            {
                "takeaway": "",
                "reading_plan": [
                    "重新准备 Reader 结构化文本后再运行深读。",
                    "确保 payload 中包含 Abstract/Introduction/Method/Results 等可追溯 segments。",
                    "在 Codex 可用时重新生成完整 Moonlight 风格解读。",
                ],
                "findings": [],
                **refs,
                "warnings": warnings,
                "ref": _paper_ref(request, payload),
            },
            warnings,
        )

    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    title = _clean_text(source.get("title") or payload.get("title") or _paper_ref(request, payload))
    all_segment_refs = _merge_refs(refs["cited_segment_refs"])
    if not all_segment_refs:
        all_segment_refs = _merge_refs(*[_deep_segment_ref(segment) for segment in segments])
        refs["cited_segment_refs"] = all_segment_refs

    abstract = _deep_pick_segment(segments, ["abstract"])
    intro = _deep_pick_segment(segments, ["introduction", "intro", "background"]) or abstract or segments[0]
    method = _deep_pick_segment(
        segments,
        ["method", "model", "architecture", "approach", "attention", "algorithm"],
    )
    metric = _deep_pick_segment(
        segments,
        ["metric", "bleu", "accuracy", "perplexity", "loss", "formula", "equation", "score"],
    )
    experiment = _deep_pick_segment(
        segments,
        ["experiment", "evaluation", "result", "benchmark", "dataset", "table"],
    )
    conclusion = _deep_pick_segment(
        segments,
        ["conclusion", "discussion", "limitation", "future", "ablation"],
    )

    takeaway_source = abstract or intro or segments[0]
    takeaway_sentence = _deep_sentence(takeaway_source)
    takeaway = (
        f"从提供片段看，{title or '这篇论文'}的核心线索是：{takeaway_sentence}"
        if takeaway_sentence
        else f"从提供片段看，{title or '这篇论文'}需要结合原文继续核对核心贡献。"
    )

    problem = []
    motivation = []
    context = []
    contributions = []
    method_rows = []
    mechanism = []
    metrics = []
    experiments = []
    results = []
    limitations = []
    project_relevance = []
    open_questions = []
    findings = []

    intro_item = _deep_item(
        f"问题定义/研究入口：{_deep_sentence(intro)}",
        [_deep_segment_ref(intro)],
    )
    if intro_item:
        problem.append(intro_item)
        findings.append(intro_item)

    if abstract and abstract is not intro:
        motivation.append(
            _deep_item(
                f"动机与重要性需要从摘要开始核对：{_deep_sentence(abstract)}",
                [_deep_segment_ref(abstract)],
            )
        )

    context.append(
        _deep_item(
            "fallback 只能基于 Reader 已供应的结构化片段组织阅读报告；未覆盖的章节需要回到原文核对。",
            all_segment_refs[:3],
        )
    )

    if method:
        item = _deep_item(
            f"方法线索：{_deep_sentence(method)}",
            [_deep_segment_ref(method)],
        )
        method_rows.append(item)
        mechanism.append(
            _deep_item(
                f"机制/实现细节应从该段继续向前后文追踪：{_deep_sentence(method)}",
                [_deep_segment_ref(method)],
            )
        )
        findings.append(item)

    if metric:
        metrics.append(
            _deep_item(
                f"指标或公式线索：{_deep_sentence(metric)}",
                [_deep_segment_ref(metric)],
            )
        )

    if experiment:
        exp_item = _deep_item(
            f"实验设置或结果线索：{_deep_sentence(experiment)}",
            [_deep_segment_ref(experiment)],
        )
        experiments.append(exp_item)
        results.append(
            _deep_item(
                f"结果解读需要围绕该证据继续核对表格、指标和对比对象：{_deep_sentence(experiment)}",
                [_deep_segment_ref(experiment)],
            )
        )
        findings.append(exp_item)

    if conclusion:
        limitations.append(
            _deep_item(
                f"局限/结论线索：{_deep_sentence(conclusion)}",
                [_deep_segment_ref(conclusion)],
            )
        )
    else:
        open_questions.append(
            _deep_item(
                "提供片段中没有清晰的局限或未来工作证据；需要检查 Discussion/Conclusion。",
                all_segment_refs[:3],
            )
        )

    contributions.append(
        _deep_item(
            "核心贡献需要以摘要、引言和方法段的交叉证据为准；fallback 已列出可追踪起点。",
            _merge_refs(
                _deep_segment_ref(abstract),
                _deep_segment_ref(intro),
                _deep_segment_ref(method),
            )[:3],
        )
    )
    project_relevance.append(
        _deep_item(
            "项目相关性暂不做外推；请把方法和实验段与当前项目目标逐条比对。",
            _merge_refs(_deep_segment_ref(method), _deep_segment_ref(experiment))[:2],
        )
    )
    open_questions.append(
        _deep_item(
            "哪些结论依赖特定数据集、指标或消融实验？需要回到实验表格和设置逐项核对。",
            _merge_refs(_deep_segment_ref(metric), _deep_segment_ref(experiment))[:2] or all_segment_refs[:2],
        )
    )

    reading_plan = [
        _deep_item("先读 Abstract/Introduction，确认问题定义、任务边界和论文声称的贡献。", [_deep_segment_ref(intro)]),
        _deep_item("再读 Method/Architecture，画出模块和信息流，区分论文声称与实现机制。", [_deep_segment_ref(method)]),
        _deep_item("随后读 Experiments/Results，核对数据集、指标、baseline、消融和真实验证。", [_deep_segment_ref(experiment)]),
        _deep_item(
            "最后读 Limitations/Conclusion，把不确定点写成后续问题。",
            [_deep_segment_ref(conclusion)] if _deep_segment_ref(conclusion) else all_segment_refs[-2:],
        ),
    ]
    reading_plan = [item for item in reading_plan if item]

    warnings.append(
        "Codex 未返回完整深读时已使用 deterministic fallback；以下内容是可追溯阅读骨架，不替代人工核对。"
    )

    structured = {
        "takeaway": takeaway,
        "problem": [item for item in problem if item],
        "motivation": [item for item in motivation if item],
        "context": [item for item in context if item],
        "contributions": [item for item in contributions if item],
        "method": [item for item in method_rows if item],
        "mechanism": [item for item in mechanism if item],
        "metrics": [item for item in metrics if item],
        "experiments": [item for item in experiments if item],
        "results": [item for item in results if item],
        "limitations": [item for item in limitations if item],
        "project_relevance": [item for item in project_relevance if item],
        "open_questions": [item for item in open_questions if item],
        "section_summaries": _section_summaries(segments),
        "terms": _deep_terms(title, segments),
        "reading_plan": reading_plan,
        "findings": [item for item in findings if item],
        **refs,
        "warnings": warnings,
        "ref": _paper_ref(request, payload),
    }
    return structured, warnings


def _deep_segment_ref(segment: Any) -> str:
    if not isinstance(segment, dict):
        return ""
    return _clean_text(
        segment.get("segment_id")
        or segment.get("id")
        or segment.get("ref")
        or segment.get("scope_ref")
    )


def _deep_section_text(segment: dict[str, Any]) -> str:
    path = segment.get("section_path")
    if isinstance(path, list):
        return " ".join(_clean_text(item) for item in path if _clean_text(item))
    return _clean_text(path or segment.get("section") or segment.get("locator"))


def _deep_pick_segment(segments: list[dict[str, Any]], terms: list[str]) -> dict[str, Any] | None:
    lowered_terms = [term.lower() for term in terms if term]
    for segment in segments:
        haystack = f"{_deep_section_text(segment)} {_clean_text(segment.get('kind'))} {_clean_text(segment.get('text'))}".lower()
        if any(term in haystack for term in lowered_terms):
            return segment
    return None


def _deep_sentence(segment: dict[str, Any] | None) -> str:
    if not isinstance(segment, dict):
        return ""
    text = _clean_text(segment.get("text") or segment.get("source_text") or segment.get("summary"))
    return _first_sentence(text)


def _deep_item(text: str, refs: list[str] | tuple[str, ...] | None = None) -> dict[str, Any]:
    clean = _clean_text(text)
    if not clean:
        return {}
    merged_refs = _merge_refs(list(refs or []))[:4]
    item: dict[str, Any] = {"text": clean}
    if merged_refs:
        item["refs"] = merged_refs
    return item


def _deep_terms(title: str, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stop = {"THE", "AND", "FOR", "WITH", "FROM", "THIS", "THAT", "OF"}
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for segment in segments[:16]:
        text = f"{title} {_deep_section_text(segment)} {_clean_text(segment.get('text'))}"
        for token in re.findall(r"\b[A-Z][A-Za-z0-9/-]{2,}\b", text):
            if token.upper() in stop or token in seen:
                continue
            seen.add(token)
            found.append(
                {
                    "term": token,
                    "definition": "fallback 标记出的论文关键词；请结合原文定义核对。",
                    "refs": [_deep_segment_ref(segment)] if _deep_segment_ref(segment) else [],
                }
            )
            if len(found) >= 8:
                return found
    return found


def _default_review_scores() -> dict[str, float]:
    return {
        "novelty": 0,
        "technical_depth": 0,
        "evidence_quality": 0,
        "reproducibility": 0,
        "relevance": 0,
        "overall": 0,
    }


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


def _project_candidate_refs(payload: dict[str, Any], field: str) -> list[str]:
    current_refs = payload.get("current_refs") if isinstance(payload.get("current_refs"), dict) else {}
    existing = _merge_refs(current_refs.get(field))
    if existing:
        return existing[:8]
    candidates = payload.get("candidates") if isinstance(payload.get("candidates"), dict) else {}
    rows = candidates.get(field) if isinstance(candidates.get(field), list) else []
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    project_text = " ".join(
        _clean_text(project.get(key))
        for key in ("title", "summary", "notes", "kind", "status")
    )
    scored: list[tuple[int, int, str]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        ref = _clean_text(row.get("id") or row.get("ref"))
        label = _clean_text(row.get("label") or row.get("title") or ref)
        if not ref:
            continue
        score = _project_ref_overlap_score(project_text, label)
        if score:
            scored.append((score, -index, ref))
    scored.sort(reverse=True)
    return _merge_refs([ref for _, _, ref in scored[:5]])


def _project_ref_overlap_score(project_text: str, candidate_text: str) -> int:
    project_tokens = _project_ref_tokens(project_text)
    if not project_tokens:
        return 0
    candidate_tokens = _project_ref_tokens(candidate_text)
    if not candidate_tokens:
        return 0
    return len(project_tokens & candidate_tokens)


def _project_ref_tokens(value: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(
            r"[a-z0-9_\-]+|[\u4e00-\u9fff]{2,}",
            _clean_text(value).lower(),
        )
        if len(token) >= 2
    }
    stop = {
        "project",
        "task",
        "goal",
        "source",
        "evidence",
        "status",
        "active",
        "planned",
        "completed",
        "研究",
        "项目",
        "任务",
        "目标",
        "证据",
        "资料",
    }
    return tokens - stop


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
