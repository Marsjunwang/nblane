"""Profile-scoped external agent task handoff records."""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from nblane.core import git_backup
from nblane.core.ai.prompts import role_prompt
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_io import list_profiles, profile_dir
from nblane.core.yaml_io import _load_yaml_dict

AGENT_TASKS_FILENAME = "agent-tasks.yaml"
AGENT_TASKS_SCHEMA_VERSION = "1.0"
AGENT_HARNESSES = ("codex", "opencode")
AGENT_ROLES = (
    "researcher",
    "resume_strategist",
    "remote_dev",
    "reviewer",
)
AGENT_TASK_STATUSES = (
    "draft",
    "ready",
    "handed_off",
    "running",
    "candidate_ready",
    "applied",
    "failed",
    "cancelled",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _tasks_path(profile: str | Path) -> Path:
    if isinstance(profile, Path):
        return profile / AGENT_TASKS_FILENAME
    return profile_dir(profile) / AGENT_TASKS_FILENAME


def _new_task_id(seed: str = "") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    digest = hashlib.sha1(
        f"{stamp}|{seed}|{datetime.now(timezone.utc).isoformat()}".encode(
            "utf-8"
        )
    ).hexdigest()[:8]
    return f"agenttask_{stamp}_{digest}"


def normalize_agent_task(
    item: dict[str, Any],
    *,
    now: str | None = None,
) -> dict[str, Any] | None:
    """Return one normalized agent task, preserving extension keys."""

    if not isinstance(item, dict):
        return None
    current = now or _now()
    out = copy.deepcopy(item)
    target = _clean_text(
        out.get("target_harness") or out.get("harness")
    ).lower()
    if target not in AGENT_HARNESSES:
        target = "codex"
    role = _clean_text(out.get("role")).lower()
    if role not in AGENT_ROLES:
        role = "researcher"
    status = _clean_text(out.get("status")).lower()
    if status not in AGENT_TASK_STATUSES:
        status = "ready"
    title = _clean_text(out.get("title")) or "Untitled agent task"
    task_id = _clean_text(out.get("id")) or _new_task_id(title)
    related = out.get("related") if isinstance(out.get("related"), dict) else {}
    payload = out.get("payload") if isinstance(out.get("payload"), dict) else {}
    result_payload = (
        out.get("result_payload")
        if isinstance(out.get("result_payload"), dict)
        else {}
    )
    out.update(
        {
            "id": task_id,
            "target_harness": target,
            "role": role,
            "title": title,
            "input_refs": _clean_string_list(out.get("input_refs")),
            "expected_outputs": _clean_string_list(
                out.get("expected_outputs")
            ),
            "status": status,
            "related": related,
            "activity_item_id": _clean_text(out.get("activity_item_id")),
            "action_name": _clean_text(out.get("action_name")),
            "run_id": _clean_text(out.get("run_id")),
            "payload": payload,
            "result_summary": _clean_text(out.get("result_summary")),
            "changed_paths": _clean_string_list(out.get("changed_paths")),
            "result_payload": result_payload,
            "warnings": _clean_string_list(out.get("warnings")),
            "error": _clean_text(out.get("error")),
            "created": _clean_text(out.get("created")) or current,
            "updated": _clean_text(out.get("updated")) or current,
        }
    )
    return out


def normalize_agent_tasks(
    raw: dict[str, Any] | None,
    *,
    profile: str = "",
) -> dict[str, Any]:
    """Return a normalized agent task document."""

    source = raw if isinstance(raw, dict) else {}
    tasks: list[dict[str, Any]] = []
    for item in source.get("tasks") or []:
        if not isinstance(item, dict):
            continue
        normalized = normalize_agent_task(item)
        if normalized is not None:
            tasks.append(normalized)
    return {
        "schema_version": _clean_text(source.get("schema_version"))
        or AGENT_TASKS_SCHEMA_VERSION,
        "profile": _clean_text(source.get("profile")) or profile,
        "updated": _clean_text(source.get("updated")),
        "tasks": tasks,
    }


def load_agent_tasks(profile: str | Path) -> dict[str, Any]:
    """Load ``agent-tasks.yaml``; missing files read as an empty queue."""

    path = _tasks_path(profile)
    raw = _load_yaml_dict(path)
    profile_name = profile.name if isinstance(profile, Path) else str(profile)
    return normalize_agent_tasks(raw, profile=profile_name)


def save_agent_tasks(profile: str, tasks_doc: dict[str, Any]) -> Path:
    """Persist a normalized agent task queue."""

    normalized = normalize_agent_tasks(tasks_doc, profile=profile)
    normalized["updated"] = _now()
    path = _tasks_path(profile)
    body = yaml.dump(
        normalized,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    header = (
        f"# Agent Tasks for {profile}\n"
        "# External Codex/OpenCode handoff records; outputs must remain candidates.\n\n"
    )
    atomic_write_text(path, header + body)
    git_backup.record_change([path], action=f"update {profile}/agent-tasks.yaml")
    return path


def create_agent_task(
    profile: str,
    *,
    target_harness: str,
    role: str,
    title: str,
    input_refs: list[str] | tuple[str, ...] | None = None,
    expected_outputs: list[str] | tuple[str, ...] | None = None,
    related: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    action_name: str = "",
    run_id: str = "",
    status: str = "ready",
    task_id: str = "",
) -> dict[str, Any]:
    """Create or replace an external agent task by id."""

    current = _now()
    item = normalize_agent_task(
        {
            "id": task_id or _new_task_id(title),
            "target_harness": target_harness,
            "role": role,
            "title": title,
            "input_refs": list(input_refs or []),
            "expected_outputs": list(expected_outputs or []),
            "status": status,
            "related": related or {},
            "payload": payload or {},
            "action_name": action_name,
            "run_id": run_id,
            "created": current,
            "updated": current,
        },
        now=current,
    )
    if item is None:
        raise ValueError("Agent task must be a mapping")
    doc = load_agent_tasks(profile)
    tasks = list(doc.get("tasks") or [])
    for index, existing in enumerate(tasks):
        if _clean_text(existing.get("id")) != item["id"]:
            continue
        merged = copy.deepcopy(existing)
        merged.update(item)
        merged["created"] = existing.get("created") or item["created"]
        merged["updated"] = current
        tasks[index] = merged
        doc["tasks"] = tasks
        save_agent_tasks(profile, doc)
        return merged
    tasks.append(item)
    doc["tasks"] = tasks
    save_agent_tasks(profile, doc)
    return item


def get_agent_task(profile: str, task_id: str) -> dict[str, Any] | None:
    """Return one task by id for a profile."""

    clean = _clean_text(task_id)
    for task in load_agent_tasks(profile).get("tasks") or []:
        if _clean_text(task.get("id")) == clean:
            return task
    return None


def find_agent_task(
    task_id: str,
    *,
    profile: str | None = None,
) -> tuple[str, dict[str, Any]] | None:
    """Find a task in one profile or by scanning profiles."""

    if profile:
        task = get_agent_task(profile, task_id)
        return (profile, task) if task is not None else None
    for name in list_profiles():
        task = get_agent_task(name, task_id)
        if task is not None:
            return name, task
    return None


def link_activity_item(
    profile: str,
    task_id: str,
    activity_item_id: str,
) -> dict[str, Any] | None:
    """Attach an Activity item id to an agent task."""

    clean = _clean_text(task_id)
    doc = load_agent_tasks(profile)
    tasks = list(doc.get("tasks") or [])
    current = _now()
    for index, task in enumerate(tasks):
        if _clean_text(task.get("id")) != clean:
            continue
        updated = copy.deepcopy(task)
        updated["activity_item_id"] = _clean_text(activity_item_id)
        updated["updated"] = current
        tasks[index] = updated
        doc["tasks"] = tasks
        save_agent_tasks(profile, doc)
        return updated
    return None


def update_agent_task_status(
    profile: str,
    task_id: str,
    status: str,
    *,
    error: str = "",
    warnings: list[str] | tuple[str, ...] | str | None = None,
    changed_paths: list[str] | tuple[str, ...] | str | None = None,
    result_summary: str = "",
    result_payload: dict[str, Any] | None = None,
    sync_activity: bool = True,
) -> dict[str, Any] | None:
    """Update an agent task and mirror review status to Agent Activity."""

    clean_status = _clean_text(status).lower()
    if clean_status not in AGENT_TASK_STATUSES:
        raise ValueError(f"Unknown agent task status: {status}")

    def _mutate(task: dict[str, Any], current: str) -> None:
        task["status"] = clean_status
        task["updated"] = current
        if error or clean_status != "failed":
            task["error"] = _clean_text(error)
        if warnings is not None:
            task["warnings"] = _clean_string_list(warnings)
        if changed_paths is not None:
            task["changed_paths"] = _clean_string_list(changed_paths)
        if result_summary:
            task["result_summary"] = _clean_text(result_summary)
        if result_payload is not None:
            task["result_payload"] = (
                copy.deepcopy(result_payload)
                if isinstance(result_payload, dict)
                else {}
            )

    task = _update_agent_task(profile, task_id, _mutate)
    if task is not None and sync_activity:
        _sync_activity_for_task(profile, task)
    return task


def update_agent_task_remote(
    profile: str,
    task_id: str,
    remote_patch: dict[str, Any],
    *,
    status: str | None = None,
    error: str = "",
    warnings: list[str] | tuple[str, ...] | str | None = None,
    changed_paths: list[str] | tuple[str, ...] | str | None = None,
    result_summary: str = "",
    sync_activity: bool = True,
) -> dict[str, Any] | None:
    """Merge remote harness metadata onto one agent task."""

    clean_status = _clean_text(status).lower() if status is not None else ""
    if clean_status and clean_status not in AGENT_TASK_STATUSES:
        raise ValueError(f"Unknown agent task status: {status}")

    patch = copy.deepcopy(remote_patch) if isinstance(remote_patch, dict) else {}

    def _mutate(task: dict[str, Any], current: str) -> None:
        remote = (
            copy.deepcopy(task.get("remote"))
            if isinstance(task.get("remote"), dict)
            else {}
        )
        remote.update(patch)
        task["remote"] = remote
        task["updated"] = current
        if clean_status:
            task["status"] = clean_status
        if error or clean_status == "failed":
            task["error"] = _clean_text(error)
        if warnings is not None:
            task["warnings"] = _clean_string_list(warnings)
        if changed_paths is not None:
            task["changed_paths"] = _clean_string_list(changed_paths)
        if result_summary:
            task["result_summary"] = _clean_text(result_summary)

    task = _update_agent_task(profile, task_id, _mutate)
    if task is not None and sync_activity:
        _sync_activity_for_task(profile, task)
    return task


def submit_agent_task_candidate(
    profile: str,
    task_id: str,
    *,
    summary: str,
    changed_paths: list[str] | tuple[str, ...] | str | None = None,
    warnings: list[str] | tuple[str, ...] | str | None = None,
    result_payload: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Store an external-agent result as a reviewable candidate."""

    return update_agent_task_status(
        profile,
        task_id,
        "candidate_ready",
        result_summary=summary,
        changed_paths=changed_paths,
        warnings=warnings,
        result_payload=result_payload or {},
    )


def _update_agent_task(
    profile: str,
    task_id: str,
    mutator: Callable[[dict[str, Any], str], None],
) -> dict[str, Any] | None:
    """Apply a mutation to one normalized task and persist the queue."""

    clean = _clean_text(task_id)
    if not clean:
        return None
    doc = load_agent_tasks(profile)
    tasks = list(doc.get("tasks") or [])
    current = _now()
    for index, task in enumerate(tasks):
        if _clean_text(task.get("id")) != clean:
            continue
        updated = copy.deepcopy(task)
        mutator(updated, current)
        normalized = normalize_agent_task(updated, now=current)
        if normalized is None:
            raise ValueError("Agent task must be a mapping")
        normalized["created"] = task.get("created") or normalized["created"]
        normalized["updated"] = current
        tasks[index] = normalized
        doc["tasks"] = tasks
        save_agent_tasks(profile, doc)
        return normalized
    return None


def _sync_activity_for_task(profile: str, task: dict[str, Any]) -> None:
    """Best-effort sync of agent task result metadata to Agent Activity."""

    activity_item_id = _clean_text(task.get("activity_item_id"))
    if not activity_item_id:
        return
    try:
        from nblane.core.agent_activity import (
            load_agent_activity,
            update_activity_status,
        )
    except Exception:
        return

    existing_payload: dict[str, Any] = {}
    try:
        activity = load_agent_activity(profile)
        for item in activity.get("items") or []:
            if _clean_text(item.get("id")) != activity_item_id:
                continue
            payload = item.get("payload")
            if isinstance(payload, dict):
                existing_payload = copy.deepcopy(payload)
            break
    except Exception:
        existing_payload = {}

    status = _clean_text(task.get("status"))
    activity_status = {
        "applied": "applied",
        "cancelled": "dismissed",
        "failed": "failed",
    }.get(status, "pending")
    result = {
        "task_id": _clean_text(task.get("id")),
        "status": status,
        "target_harness": _clean_text(task.get("target_harness")),
        "role": _clean_text(task.get("role")),
        "summary": _clean_text(task.get("result_summary")),
        "changed_paths": _clean_string_list(task.get("changed_paths")),
        "warnings": _clean_string_list(task.get("warnings")),
        "error": _clean_text(task.get("error")),
        "result_payload": (
            copy.deepcopy(task.get("result_payload"))
            if isinstance(task.get("result_payload"), dict)
            else {}
        ),
        "remote": (
            copy.deepcopy(task.get("remote"))
            if isinstance(task.get("remote"), dict)
            else {}
        ),
    }
    payload = dict(existing_payload)
    payload["agent_task_result"] = result
    preview = yaml.dump(
        result,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).strip()
    summary = (
        result["summary"]
        or f"{task.get('title') or task.get('id')} ({status or 'ready'})"
    )
    try:
        update_activity_status(
            profile,
            activity_item_id,
            activity_status,
            error=result["error"] if activity_status == "failed" else "",
            warnings=result["warnings"],
            changed_paths=result["changed_paths"],
            extra={
                "summary": summary,
                "preview": preview,
                "payload": payload,
                "error": result["error"] if activity_status == "failed" else "",
            },
        )
    except Exception:
        return


def render_agent_handoff(
    task: dict[str, Any],
    *,
    profile: str,
    target: str | None = None,
) -> str:
    """Render a copy-paste handoff for Codex/OpenCode."""

    clean_target = _clean_text(target or task.get("target_harness")).lower()
    if clean_target not in AGENT_HARNESSES:
        clean_target = _clean_text(task.get("target_harness")).lower()
    if clean_target not in AGENT_HARNESSES:
        clean_target = "codex"
    role = _clean_text(task.get("role")) or "researcher"
    lines = [
        "# nblane Agent Task Handoff",
        "",
        f"- Profile: {profile}",
        f"- Task id: {_clean_text(task.get('id'))}",
        f"- Target harness: {clean_target}",
        f"- Role: {role}",
        f"- Status: {_clean_text(task.get('status')) or 'ready'}",
        f"- Activity item: {_clean_text(task.get('activity_item_id')) or '(pending)'}",
        "",
        "## Role Contract",
        role_prompt(role),
        "",
        "## Task",
        _clean_text(task.get("title")) or "Untitled agent task",
        "",
        "## Input Refs",
    ]
    input_refs = _clean_string_list(task.get("input_refs"))
    lines.extend([f"- {ref}" for ref in input_refs] or ["- (none)"])
    lines.extend(["", "## Expected Outputs"])
    expected = _clean_string_list(task.get("expected_outputs"))
    lines.extend([f"- {item}" for item in expected] or ["- candidate"])
    lines.extend(
        [
            "",
            "## Safety Rules",
            "- Produce candidate, patch, or writeback-review artifacts only.",
            "- Do not silently write accepted research facts, resume facts, or public posts.",
            "- Record changed paths and warnings in the final handoff summary.",
            "",
            "## MCP Workflow",
            "- Read `profile://context` and `profile://kanban` before working.",
            f"- Read `agent://task/{_clean_text(task.get('id'))}` for the canonical task packet.",
            "- When work is ready, call `submit_agent_task_candidate` with the task id, summary, changed_paths, warnings, and result_payload.",
            "- If work fails or blocks, call `update_agent_task_status` with status `failed` or `running` and include a short error or blocker.",
            "- MCP writes must stay draft-first: update agent task / Activity review metadata only.",
            "",
            "## Suggested Harness Start",
        ]
    )
    if clean_target == "opencode":
        lines.extend(
            [
                "OpenCode: start a session in this repository and paste this handoff.",
                "Use the role contract above as the active agent instruction.",
            ]
        )
    else:
        lines.extend(
            [
                "Codex: start a session in this repository and paste this handoff.",
                "Use the role contract above as the active agent instruction.",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def sync_agent_harness_snippet(target: str) -> str:
    """Return a provider-agnostic config snippet for an external harness."""

    clean_target = _clean_text(target).lower()
    if clean_target not in AGENT_HARNESSES:
        raise ValueError(f"Unknown agent harness target: {target}")
    heading = "Codex" if clean_target == "codex" else "OpenCode"
    lines = [
        f"# nblane {heading} Harness",
        "",
        "Use nblane as the source of profile context, long-term research data, "
        "project state, and review queues. The harness is an external executor, "
        "not a replacement for nblane business pages.",
        "",
        "## Global Writeback Rule",
        "All outputs must enter candidate, patch, or writeback review state first. "
        "Never silently write accepted facts or publish public content.",
        "",
        "## Roles",
    ]
    for role in AGENT_ROLES:
        lines.extend(
            [
                f"### {role}",
                role_prompt(role),
                "",
            ]
        )
    lines.extend(
        [
            "## Handoff Commands",
            "```bash",
            f"nblane sync-agent-harness --target {clean_target}",
            f"nblane agent handoff <task_id> --target {clean_target} --profile <name>",
            "```",
            "",
            "## MCP Resources",
            "- `profile://context`",
            "- `profile://kanban`",
            "- `agent://tasks`",
            "- `agent://task/{task_id}`",
            "",
            "## MCP Tools",
            "- `submit_agent_task_candidate(task_id, summary, changed_paths, warnings, result_payload)`",
            "- `update_agent_task_status(task_id, status, error, warnings)`",
            "",
            "## Permissions",
            "- allow: read repository files, run local checks requested by the task",
            "- ask: write profile data, create public drafts, apply patches",
            "- deny: publish, delete profile facts, bypass Agent Activity review",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "AGENT_HARNESSES",
    "AGENT_ROLES",
    "AGENT_TASKS_FILENAME",
    "AGENT_TASK_STATUSES",
    "create_agent_task",
    "find_agent_task",
    "get_agent_task",
    "link_activity_item",
    "load_agent_tasks",
    "normalize_agent_task",
    "normalize_agent_tasks",
    "render_agent_handoff",
    "save_agent_tasks",
    "submit_agent_task_candidate",
    "sync_agent_harness_snippet",
    "update_agent_task_remote",
    "update_agent_task_status",
]
