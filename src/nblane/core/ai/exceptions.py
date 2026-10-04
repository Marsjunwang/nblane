"""Read-only aggregation of AI failures that need owner attention."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from nblane.core.agent_activity import load_agent_activity
from nblane.core.agent_tasks import load_agent_tasks
from nblane.core.ai.runs import load_ai_runs


def _text(value: object) -> str:
    return str(value or "").strip()


def _timestamp(value: object) -> str:
    if isinstance(value, (int, float)) and value > 0:
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    text = _text(value)
    if text:
        return text
    return datetime.now(timezone.utc).isoformat()


def _href(profile: str, action: str, source: str) -> str:
    """Return the closest owner page for an exception."""

    clean = f"{action} {source}".casefold()
    profile_path = quote(profile, safe="")
    if "research" in clean or "paper" in clean:
        return f"/p/{profile_path}/research"
    if "studio" in clean or "output" in clean or "resume" in clean:
        return f"/p/{profile_path}/studio"
    if "project" in clean or "kanban" in clean or "agent" in clean:
        return f"/p/{profile_path}/projects"
    if "evidence" in clean or "crystall" in clean:
        return f"/p/{profile_path}/evidence"
    return f"/p/{profile_path}/home"


def _base_item(
    *,
    item_id: str,
    source: str,
    title: str,
    message: str,
    action: str,
    created: object,
    source_ref: str = "",
    retryable: bool = True,
    href: str = "",
) -> dict[str, Any]:
    return {
        "id": item_id,
        "source": source,
        "title": title or "AI 执行失败",
        "message": message or "AI 动作失败，请打开来源页面检查。",
        "action": action,
        "source_ref": source_ref,
        "created": _timestamp(created),
        "retryable": retryable,
        "href": href,
        "severity": "error",
    }


def collect_profile_exceptions(
    profile: str | Path,
    *,
    jobs: Iterable[dict[str, Any]] = (),
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Collect unresolved failures from every profile-scoped AI surface.

    ``agent-activity.yaml`` remains the source for writeback failures. AI
    gateway runs and external-agent tasks are included when they do not
    already point at the same failed activity item. In-process web jobs are
    supplied by :mod:`nblane.web_api.jobs` so this core module stays unaware
    of the web server.
    """

    profile_name = profile.name if isinstance(profile, Path) else str(profile)
    activity = load_agent_activity(profile)
    activity_items = [
        item
        for item in activity.get("items") or []
        if isinstance(item, dict) and _text(item.get("status")) == "failed"
    ]
    failed_activity_ids = {_text(item.get("id")) for item in activity_items}
    failed_activity_refs = {
        _text(item.get("source_ref"))
        for item in activity_items
        if _text(item.get("source_ref"))
    }
    output: list[dict[str, Any]] = []

    for item in activity_items:
        action = _text(item.get("action_name") or item.get("candidate_type"))
        output.append(
            _base_item(
                item_id=f"activity:{_text(item.get('id'))}",
                source="AI 写回",
                title=_text(item.get("title")) or "AI 写回失败",
                message=_text(item.get("error") or item.get("summary")),
                action=action,
                created=item.get("updated") or item.get("created"),
                source_ref=_text(item.get("id")),
                retryable=True,
                href=_href(profile_name, action, _text(item.get("source_page"))),
            )
        )

    runs = load_ai_runs(profile).get("runs") or []
    for run in runs:
        if not isinstance(run, dict) or run.get("ok") is not False:
            continue
        run_id = _text(run.get("id"))
        activity_id = _text(run.get("activity_item_id"))
        if activity_id in failed_activity_ids or run_id in failed_activity_refs:
            continue
        action = _text(run.get("action"))
        output.append(
            _base_item(
                item_id=f"run:{run_id}",
                source="AI 调用",
                title=action or "AI 调用失败",
                message=_text(run.get("error")),
                action=action,
                created=run.get("created"),
                source_ref=run_id,
                retryable=True,
                href=_href(profile_name, action, "AI Gateway"),
            )
        )

    tasks = load_agent_tasks(profile).get("tasks") or []
    for task in tasks:
        if not isinstance(task, dict) or _text(task.get("status")) != "failed":
            continue
        activity_id = _text(task.get("activity_item_id"))
        if activity_id in failed_activity_ids:
            continue
        task_id = _text(task.get("id"))
        action = _text(task.get("action_name") or task.get("target_harness"))
        output.append(
            _base_item(
                item_id=f"agent-task:{task_id}",
                source="外部 Agent",
                title=_text(task.get("title")) or "外部 Agent 任务失败",
                message=_text(task.get("error") or task.get("result_summary")),
                action=action,
                created=task.get("updated") or task.get("created"),
                source_ref=task_id,
                retryable=True,
                href=_href(profile_name, action, "external-agent"),
            )
        )

    for job in jobs:
        if not isinstance(job, dict) or _text(job.get("status")) != "failed":
            continue
        job_id = _text(job.get("job_id"))
        error = job.get("error") if isinstance(job.get("error"), dict) else {}
        action = _text(job.get("kind"))
        output.append(
            _base_item(
                item_id=f"job:{job_id}",
                source="异步 AI 任务",
                title=action or "异步 AI 任务失败",
                message=_text(error.get("message") or job.get("message")),
                action=action,
                created=job.get("finished_at") or job.get("created_at"),
                source_ref=job_id,
                retryable=True,
                href=_href(profile_name, action, "web-job"),
            )
        )

    output.sort(key=lambda item: _text(item.get("created")), reverse=True)
    return output[: max(1, min(int(limit), 200))]


__all__ = ["collect_profile_exceptions"]
