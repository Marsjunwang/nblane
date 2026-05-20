"""AI run metadata and Agent Activity bridge."""

from __future__ import annotations

import copy
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from nblane.core import git_backup
from nblane.core.agent_activity import append_activity_item
from nblane.core.agent_tasks import link_activity_item
from nblane.core.ai.actions import (
    AIActionRequest,
    AIActionResult,
    AIActionSpec,
)
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_io import profile_dir
from nblane.core.yaml_io import _load_yaml_dict

AI_RUNS_FILENAME = "ai-runs.yaml"
AI_RUNS_SCHEMA_VERSION = "1.0"


def now_iso() -> str:
    """Return a UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def new_run_id(action: str) -> str:
    """Create a stable-looking run id for one action execution."""

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    digest = hashlib.sha1(
        f"{stamp}|{action}|{datetime.now(timezone.utc).isoformat()}".encode(
            "utf-8"
        )
    ).hexdigest()[:8]
    return f"airun_{stamp}_{digest}"


def _runs_path(profile: str | Path) -> Path:
    if isinstance(profile, Path):
        return profile / AI_RUNS_FILENAME
    return profile_dir(profile) / AI_RUNS_FILENAME


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _clean_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, tuple):
        raw_items = list(value)
    elif isinstance(value, str):
        raw_items = [
            item
            for chunk in value.splitlines()
            for item in chunk.split(",")
        ]
    else:
        raw_items = []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        text = _clean_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def normalize_ai_runs(
    raw: dict[str, Any] | None,
    *,
    profile: str = "",
) -> dict[str, Any]:
    """Normalize an ``ai-runs.yaml`` document."""

    source = raw if isinstance(raw, dict) else {}
    runs: list[dict[str, Any]] = []
    for item in source.get("runs") or []:
        if not isinstance(item, dict):
            continue
        run_id = _clean_text(item.get("id") or item.get("run_id"))
        if not run_id:
            continue
        runs.append(
            {
                **copy.deepcopy(item),
                "id": run_id,
                "action": _clean_text(item.get("action")),
                "backend": _clean_text(item.get("backend")),
                "ok": bool(item.get("ok")),
                "activity_item_id": _clean_text(
                    item.get("activity_item_id")
                ),
                "warnings": _clean_string_list(item.get("warnings")),
                "error": _clean_text(item.get("error")),
                "created": _clean_text(item.get("created")) or now_iso(),
            }
        )
    return {
        "schema_version": _clean_text(source.get("schema_version"))
        or AI_RUNS_SCHEMA_VERSION,
        "profile": _clean_text(source.get("profile")) or profile,
        "updated": _clean_text(source.get("updated")),
        "runs": runs,
    }


def load_ai_runs(profile: str | Path) -> dict[str, Any]:
    """Load ``ai-runs.yaml``; missing files read as an empty run list."""

    path = _runs_path(profile)
    raw = _load_yaml_dict(path)
    profile_name = profile.name if isinstance(profile, Path) else str(profile)
    return normalize_ai_runs(raw, profile=profile_name)


def save_ai_runs(profile: str, runs_doc: dict[str, Any]) -> Path:
    """Persist AI run metadata."""

    normalized = normalize_ai_runs(runs_doc, profile=profile)
    normalized["updated"] = now_iso()
    path = _runs_path(profile)
    body = yaml.dump(
        normalized,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    header = (
        f"# AI runs for {profile}\n"
        "# Metadata only. Full private prompts are intentionally not stored here.\n\n"
    )
    atomic_write_text(path, header + body)
    git_backup.record_change([path], action=f"update {profile}/ai-runs.yaml")
    return path


def append_ai_run(
    profile: str,
    request: AIActionRequest,
    spec: AIActionSpec,
    result: AIActionResult,
    *,
    activity_item_id: str = "",
) -> dict[str, Any]:
    """Append one run metadata row and return it."""

    item = {
        "id": result.run_id,
        "action": request.action,
        "backend": result.backend,
        "owner": spec.owner,
        "ok": result.ok,
        "output_mode": spec.output_mode,
        "activity_policy": spec.activity_policy,
        "activity_item_id": activity_item_id or result.activity_item_id,
        "context_refs": list(request.context_refs),
        "warnings": list(result.warnings),
        "error": result.error,
        "created": now_iso(),
    }
    doc = load_ai_runs(profile)
    runs = list(doc.get("runs") or [])
    runs.append(item)
    doc["runs"] = runs
    save_ai_runs(profile, doc)
    return item


def record_activity_item(
    profile: str,
    request: AIActionRequest,
    spec: AIActionSpec,
    result: AIActionResult,
) -> str:
    """Create an Agent Activity review item for a run when policy requires it."""

    if not request.require_review or spec.activity_policy == "none":
        return ""
    kind = spec.activity_policy
    if kind not in ("candidate", "patch", "writeback"):
        kind = "candidate"
    if _is_paper_action(request.action):
        return _record_paper_activity_item(profile, request, spec, result, kind)
    structured = result.structured
    payload: dict[str, Any] = {
        "action_result": structured,
        "content": result.content,
    }
    if isinstance(structured, dict):
        changed_paths = _clean_string_list(structured.get("changed_paths"))
        title = _clean_text(
            structured.get("title")
            or structured.get("target")
            or structured.get("task_id")
        )
        summary = _clean_text(
            structured.get("summary")
            or structured.get("status")
            or result.error
        )
    else:
        changed_paths = []
        title = ""
        summary = result.error
    if not title:
        title = request.action
    if not summary:
        summary = (result.content or "").strip()[:240]
    item = append_activity_item(
        profile,
        {
            "id": f"act:ai:{result.run_id}",
            "kind": kind,
            "candidate_type": request.action.replace(".", "_"),
            "source_page": "AI Gateway",
            "source_ref": result.run_id,
            "target_owner": spec.owner,
            "status": "pending" if result.ok else "failed",
            "title": title,
            "summary": summary,
            "preview": result.content[:500],
            "refs": {"input": list(request.context_refs)},
            "payload": payload,
            "warnings": list(result.warnings),
            "error": result.error,
            "changed_paths": changed_paths,
            "action_name": request.action,
            "backend": result.backend,
            "run_id": result.run_id,
            "input_refs": list(request.context_refs),
        },
    )
    activity_id = _clean_text(item.get("id"))
    if isinstance(structured, dict):
        task_id = _clean_text(structured.get("task_id"))
        if task_id:
            link_activity_item(profile, task_id, activity_id)
    return activity_id


def _record_paper_activity_item(
    profile: str,
    request: AIActionRequest,
    spec: AIActionSpec,
    result: AIActionResult,
    kind: str,
) -> str:
    """Record a privacy-thin Agent Activity item for Paper AI actions."""

    structured = result.structured if isinstance(result.structured, dict) else {}
    payload = request.payload if isinstance(request.payload, dict) else {}
    source_id = _paper_source_id(request, structured)
    source_ids = _paper_source_ids(request, structured, source_id=source_id)
    query = _short_activity_text(payload.get("query") or payload.get("goal"), 120)
    output_refs = _paper_output_refs(structured)
    task_id = _clean_text(structured.get("task_id"))
    summary = _paper_activity_summary(request, result, structured, query=query)
    warnings = _short_string_list(
        list(result.warnings) + _clean_string_list(structured.get("warnings")),
        limit=240,
        max_items=8,
    )
    activity_payload: dict[str, Any] = {
        "action": request.action,
        "backend": result.backend,
        "provider": result.backend,
        "run_id": result.run_id,
        "context_refs": list(request.context_refs),
        "output_refs": output_refs,
        "warnings": warnings,
    }
    if source_id:
        activity_payload["source_id"] = source_id
    if source_ids:
        activity_payload["source_ids"] = source_ids
    if query:
        activity_payload["query"] = query
    if task_id:
        activity_payload["task_id"] = task_id

    refs = {"input": list(request.context_refs)}
    if source_ids:
        refs["sources"] = source_ids
    item = append_activity_item(
        profile,
        {
            "id": f"act:ai:{result.run_id}",
            "kind": kind,
            "candidate_type": request.action.replace(".", "_"),
            "source_page": "AI Gateway",
            "source_ref": result.run_id,
            "target_owner": spec.owner,
            "status": "pending" if result.ok else "failed",
            "title": _paper_activity_title(request, result, source_id, query),
            "summary": summary,
            "preview": _short_activity_text(summary, 300),
            "refs": refs,
            "payload": activity_payload,
            "warnings": warnings,
            "error": _short_activity_text(result.error, 240),
            "changed_paths": [],
            "action_name": request.action,
            "backend": result.backend,
            "run_id": result.run_id,
            "input_refs": list(request.context_refs),
        },
    )
    activity_id = _clean_text(item.get("id"))
    if task_id:
        link_activity_item(profile, task_id, activity_id)
    return activity_id


def _is_paper_action(action: str) -> bool:
    return str(action or "").startswith("research.paper_")


def _short_activity_text(value: object, limit: int = 240) -> str:
    text = " ".join(_clean_text(value).split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def _short_string_list(
    values: object,
    *,
    limit: int,
    max_items: int,
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in _clean_string_list(values):
        short = _short_activity_text(value, limit)
        if not short or short in seen:
            continue
        seen.add(short)
        out.append(short)
        if len(out) >= max_items:
            break
    return out


def _paper_source_id(
    request: AIActionRequest,
    structured: dict[str, Any],
) -> str:
    payload = request.payload if isinstance(request.payload, dict) else {}
    for value in (
        payload.get("source_id"),
        payload.get("research_source_id"),
        structured.get("source_id"),
        structured.get("ref"),
    ):
        clean = _clean_text(value)
        if clean.startswith("source:"):
            return clean
    for ref in request.context_refs:
        clean = _clean_text(ref)
        if clean.startswith("source:"):
            return clean
    return _clean_text(payload.get("source_id") or structured.get("source_id"))


def _paper_source_ids(
    request: AIActionRequest,
    structured: dict[str, Any],
    *,
    source_id: str,
) -> list[str]:
    payload = request.payload if isinstance(request.payload, dict) else {}
    values = _clean_string_list(payload.get("source_ids"))
    values.extend(_clean_string_list(structured.get("source_ids")))
    values.extend(
        ref for ref in _clean_string_list(request.context_refs) if ref.startswith("source:")
    )
    if source_id:
        values.insert(0, source_id)
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out[:12]


def _paper_output_refs(structured: dict[str, Any]) -> dict[str, Any]:
    refs: dict[str, Any] = {}
    for key in (
        "ref",
        "cited_segment_refs",
        "cited_chunk_refs",
        "cited_annotation_refs",
        "input_refs",
        "expected_outputs",
    ):
        value = structured.get(key)
        if isinstance(value, str):
            clean = _clean_text(value)
            if clean:
                refs[key] = clean
        else:
            cleaned = _clean_string_list(value)
            if cleaned:
                refs[key] = cleaned[:20]
    for key in ("results", "translations", "findings", "comparisons", "reading_plan"):
        value = structured.get(key)
        if isinstance(value, list):
            refs[f"{key}_count"] = len(value)
    task_id = _clean_text(structured.get("task_id"))
    if task_id:
        refs["task_id"] = task_id
    return refs


def _paper_activity_summary(
    request: AIActionRequest,
    result: AIActionResult,
    structured: dict[str, Any],
    *,
    query: str,
) -> str:
    if not result.ok:
        return _short_activity_text(result.error or "Paper AI action failed.", 240)
    action = request.action
    if action == "research.paper_search_codex":
        count = len(structured.get("results") or [])
        suffix = f" for {query}" if query else ""
        return _short_activity_text(f"Paper search returned {count} candidate(s){suffix}.", 240)
    if action == "research.paper_deep_read_codex":
        count = len(structured.get("findings") or [])
        return f"Codex deep-read candidate ready with {count} finding(s)."
    if action == "research.paper_compare_codex":
        count = len(structured.get("comparisons") or [])
        return f"Codex paper comparison candidate ready with {count} comparison row(s)."
    if "translations" in structured:
        count = len(structured.get("translations") or [])
        return f"Paper translation candidate returned {count} row(s)."
    return _short_activity_text(f"Paper AI candidate ready for {action}.", 240)


def _paper_activity_title(
    request: AIActionRequest,
    result: AIActionResult,
    source_id: str,
    query: str,
) -> str:
    if request.action == "research.paper_search_codex":
        return _short_activity_text(
            f"Paper search: {query or result.run_id}",
            160,
        )
    if source_id:
        return _short_activity_text(f"{request.action}: {source_id}", 160)
    return _short_activity_text(request.action, 160)


__all__ = [
    "AI_RUNS_FILENAME",
    "append_ai_run",
    "load_ai_runs",
    "new_run_id",
    "normalize_ai_runs",
    "now_iso",
    "record_activity_item",
    "save_ai_runs",
]
