"""Review candidate preview and writeback helpers."""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from nblane.core import agent_activity
from nblane.core.ingest_merge import merge_ingest_patch
from nblane.core.kanban_io import KANBAN_DONE, KANBAN_QUEUE, parse_kanban, save_kanban
from nblane.core.models import KanbanTask
from nblane.core.paths import REPO_ROOT
from nblane.core.profile_io import (
    load_evidence_pool_raw,
    load_skill_tree_raw,
    profile_dir,
    save_evidence_pool,
)
from nblane.core.public_site import create_blog_draft
from nblane.core.validate import validate_one


@dataclass
class ReviewApplyResult:
    """Result for one Review candidate writeback."""

    ok: bool
    changed_paths: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    activity_item: dict[str, Any] | None = None
    output_path: Path | None = None


def review_window_default(today: date | None = None) -> tuple[date, date]:
    """Return current natural week Monday -> today."""
    current = today or date.today()
    return current - timedelta(days=current.weekday()), current


def review_window_for_preset(
    preset: str,
    *,
    today: date | None = None,
) -> tuple[date, date]:
    """Return date range for a Review preset."""
    current = today or date.today()
    clean = str(preset or "").strip()
    if clean == "previous_week":
        this_monday = current - timedelta(days=current.weekday())
        start = this_monday - timedelta(days=7)
        return start, start + timedelta(days=6)
    if clean == "last_30_days":
        return current - timedelta(days=29), current
    return review_window_default(current)


def normalize_review_window(start: str | date, end: str | date) -> tuple[date, date]:
    """Normalize a start/end pair and swap reversed windows."""
    start_date = start if isinstance(start, date) else date.fromisoformat(str(start)[:10])
    end_date = end if isinstance(end, date) else date.fromisoformat(str(end)[:10])
    if start_date > end_date:
        return end_date, start_date
    return start_date, end_date


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


def _candidate_source_ref(start: str | date, end: str | date) -> str:
    s, e = normalize_review_window(start, end)
    return f"review:{s.isoformat()}:{e.isoformat()}"


def review_candidate_id(
    profile: str,
    start: str | date,
    end: str | date,
    candidate_type: str,
    source_ref: str,
    title: str,
) -> str:
    """Return a stable Activity id for a Review candidate."""
    seed = "|".join(
        [
            _clean_text(profile),
            _candidate_source_ref(start, end),
            _clean_text(candidate_type),
            _clean_text(source_ref),
            _clean_text(title),
        ]
    )
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:14]
    return f"act:review:{candidate_type}:{digest}"


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        return str(path)


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _restore_text(path: Path, previous: str | None) -> None:
    if previous is None:
        if path.exists():
            path.unlink()
        return
    path.write_text(previous, encoding="utf-8")


def _preview_yaml(data: object) -> str:
    return yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).strip()


def review_evidence_patch(candidate: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Build an ingest patch for one Review evidence candidate."""
    title = _clean_text(candidate.get("title"))
    summary = _clean_text(candidate.get("summary")) or title
    task_id = _clean_text(candidate.get("task_id"))
    row: dict[str, Any] = {
        "type": "practice",
        "title": title,
        "summary": summary,
        "review_status": "needs_review",
        "public_readiness": "private",
    }
    if task_id:
        row["source_refs"] = [f"kanban:{task_id}"]
    return {"evidence_entries": [row], "node_updates": []}


def review_kanban_task(candidate: dict[str, Any]) -> KanbanTask:
    """Build one Queue task from a Review next_action candidate."""
    title = _clean_text(candidate.get("title")) or "Review follow-up"
    source = _clean_text(candidate.get("source")) or "review"
    resource_id = _clean_text(candidate.get("resource_id"))
    details = []
    if resource_id:
        details.append(f"source_ref: learning:{resource_id}")
    task = KanbanTask(
        title=title,
        done=False,
        context="Generated from Review next action candidate.",
        tags=", ".join(
            tag
            for tag in ("source/review", f"source/{source}" if source != "review" else "")
            if tag
        ),
        details=details,
    )
    return task


def activity_item_from_review_candidate(
    profile: str,
    start: str | date,
    end: str | date,
    candidate_type: str,
    candidate: dict[str, Any],
    *,
    status: str = "pending",
    kind: str = "candidate",
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Map a Review candidate to an Agent Activity item."""
    source_ref = _candidate_source_ref(start, end)
    title = _clean_text(candidate.get("title")) or "Review candidate"
    source = _clean_text(candidate.get("source"))
    target_owner = {
        "evidence": "evidence_pool",
        "next_action": "kanban",
        "public_draft": "public_site",
        "method_note": "profile_context",
    }.get(candidate_type, "profile_context")
    item_source_ref = _clean_text(candidate.get("task_id")) or _clean_text(candidate.get("resource_id")) or source_ref
    activity_id = review_candidate_id(
        profile,
        start,
        end,
        candidate_type,
        item_source_ref,
        title,
    )
    refs: dict[str, Any] = {"files": []}
    pdir = profile_dir(profile)
    if candidate_type == "evidence":
        task_id = _clean_text(candidate.get("task_id"))
        refs["task_refs"] = [task_id] if task_id else []
        refs["files"] = [_relative(pdir / "evidence-pool.yaml")]
        preview = _preview_yaml(review_evidence_patch(candidate))
    elif candidate_type == "next_action":
        resource_id = _clean_text(candidate.get("resource_id"))
        refs["source_refs"] = [f"learning:{resource_id}"] if resource_id else []
        refs["files"] = [_relative(pdir / "kanban.md")]
        preview = _preview_yaml({"queue_task": _kanban_task_preview(review_kanban_task(candidate))})
    elif candidate_type == "public_draft":
        refs["files"] = [_relative(pdir / "blog")]
        preview = _preview_yaml(
            {
                "title": title,
                "summary": _clean_text(candidate.get("summary")) or title,
                "status": "draft",
            }
        )
    else:
        preview = _preview_yaml(candidate)
    return {
        "id": activity_id,
        "kind": kind,
        "candidate_type": candidate_type,
        "source_page": "Review",
        "source_ref": source_ref,
        "target_owner": target_owner,
        "status": status,
        "title": title,
        "summary": _clean_text(candidate.get("summary")) or _clean_text(candidate.get("notes")) or source,
        "refs": refs,
        "payload": copy.deepcopy(candidate),
        "preview": preview,
        "warnings": list(warnings or []),
    }


def save_review_candidates_to_activity(
    profile: str,
    start: str | date,
    end: str | date,
    candidate_type: str,
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Persist selected Review candidates as pending Activity items."""
    stored: list[dict[str, Any]] = []
    for candidate in candidates:
        item = activity_item_from_review_candidate(
            profile,
            start,
            end,
            candidate_type,
            candidate,
        )
        stored.append(agent_activity.append_activity_item(profile, item))
    return stored


def _mark_done_crystallized(
    sections: dict[str, list[KanbanTask]],
    task_ids: set[str],
) -> bool:
    changed = False
    updated_done: list[KanbanTask] = []
    for task in sections.get(KANBAN_DONE, []):
        task_id = _clean_text(task.id)
        if task_id and task_id in task_ids and not task.crystallized:
            updated_done.append(
                KanbanTask(
                    title=task.title,
                    done=task.done,
                    id=task.id,
                    context=task.context,
                    why=task.why,
                    blocked_by=task.blocked_by,
                    outcome=task.outcome,
                    started_on=task.started_on,
                    completed_on=task.completed_on,
                    crystallized=True,
                    tags=task.tags,
                    subtasks=list(task.subtasks),
                    details=list(task.details),
                )
            )
            changed = True
        else:
            updated_done.append(task)
    sections[KANBAN_DONE] = updated_done
    return changed


def _kanban_task_preview(task: KanbanTask) -> dict[str, Any]:
    out: dict[str, Any] = {
        "title": task.title,
        "context": task.context,
        "tags": task.tags,
    }
    if task.details:
        out["details"] = list(task.details)
    return out


def apply_review_evidence_candidate(
    profile: str,
    start: str | date,
    end: str | date,
    candidate: dict[str, Any],
    *,
    mark_crystallized: bool = True,
    activity_item_id: str = "",
) -> ReviewApplyResult:
    """Apply one Review evidence candidate via ingest writeback."""
    item = activity_item_from_review_candidate(profile, start, end, "evidence", candidate)
    if activity_item_id:
        item["id"] = activity_item_id
    agent_activity.append_activity_item(profile, item)
    pdir = profile_dir(profile)
    pool_path = pdir / "evidence-pool.yaml"
    changed_paths = [pool_path]
    try:
        patch = review_evidence_patch(candidate)
        previous_pool = _read_text(pool_path)
        merge = merge_ingest_patch(
            profile,
            load_evidence_pool_raw(profile),
            load_skill_tree_raw(profile),
            patch,
            allow_status_change=False,
            bump_locked_with_evidence=False,
        )
        warnings = list(merge.warnings)
        if not merge.ok or merge.merged_pool is None:
            stored = agent_activity.update_activity_status(
                profile,
                item["id"],
                "failed",
                error="; ".join(merge.errors),
                warnings=warnings,
            )
            return ReviewApplyResult(
                ok=False,
                warnings=warnings,
                errors=list(merge.errors),
                activity_item=stored,
            )
        save_evidence_pool(profile, merge.merged_pool)
        errors, validation_warnings = validate_one(pdir, check_sync=False)
        warnings.extend(validation_warnings)
        if errors:
            _restore_text(pool_path, previous_pool)
            stored = agent_activity.update_activity_status(
                profile,
                item["id"],
                "failed",
                error="; ".join(errors),
                warnings=warnings,
            )
            return ReviewApplyResult(
                ok=False,
                warnings=warnings,
                errors=list(errors),
                activity_item=stored,
            )
        if mark_crystallized:
            task_id = _clean_text(candidate.get("task_id"))
            if task_id:
                sections = parse_kanban(profile)
                if _mark_done_crystallized(sections, {task_id}):
                    save_kanban(profile, sections)
                    changed_paths.append(pdir / "kanban.md")
        stored = agent_activity.update_activity_status(
            profile,
            item["id"],
            "applied",
            warnings=warnings,
            changed_paths=changed_paths,
        )
        return ReviewApplyResult(
            ok=True,
            changed_paths=changed_paths,
            warnings=warnings,
            activity_item=stored,
        )
    except Exception as exc:
        stored = agent_activity.update_activity_status(
            profile,
            item["id"],
            "failed",
            error=str(exc),
        )
        return ReviewApplyResult(ok=False, errors=[str(exc)], activity_item=stored)


def apply_review_next_action_candidate(
    profile: str,
    start: str | date,
    end: str | date,
    candidate: dict[str, Any],
    *,
    activity_item_id: str = "",
) -> ReviewApplyResult:
    """Append one Review next action candidate to Kanban Queue."""
    item = activity_item_from_review_candidate(profile, start, end, "next_action", candidate)
    if activity_item_id:
        item["id"] = activity_item_id
    agent_activity.append_activity_item(profile, item)
    pdir = profile_dir(profile)
    path = pdir / "kanban.md"
    try:
        sections = parse_kanban(profile)
        task = review_kanban_task(candidate)
        sections.setdefault(KANBAN_QUEUE, []).append(task)
        save_kanban(profile, sections)
        stored = agent_activity.update_activity_status(
            profile,
            item["id"],
            "applied",
            changed_paths=[path],
        )
        return ReviewApplyResult(
            ok=True,
            changed_paths=[path],
            activity_item=stored,
        )
    except Exception as exc:
        stored = agent_activity.update_activity_status(
            profile,
            item["id"],
            "failed",
            error=str(exc),
        )
        return ReviewApplyResult(ok=False, errors=[str(exc)], activity_item=stored)


def apply_review_public_draft_candidate(
    profile: str,
    start: str | date,
    end: str | date,
    candidate: dict[str, Any],
    *,
    activity_item_id: str = "",
) -> ReviewApplyResult:
    """Create a draft blog post from one Review public candidate."""
    item = activity_item_from_review_candidate(profile, start, end, "public_draft", candidate)
    if activity_item_id:
        item["id"] = activity_item_id
    agent_activity.append_activity_item(profile, item)
    try:
        title = _clean_text(candidate.get("title")) or "Review public draft"
        summary = _clean_text(candidate.get("summary")) or _clean_text(candidate.get("source"))
        body = (
            f"## Review candidate\n\n{summary or title}\n\n"
            "## Public angle\n\n"
            "Turn this reviewed candidate into a publishable draft. Verify private details, links, and metrics before publishing.\n"
        )
        path = create_blog_draft(
            profile,
            title=title,
            body=body,
            tags=["review"],
            summary=summary,
            related_kanban=_clean_string_list(candidate.get("task_id")),
        )
        changed = [path, path.with_suffix(".blocknote.json")]
        stored = agent_activity.update_activity_status(
            profile,
            item["id"],
            "applied",
            changed_paths=changed,
        )
        return ReviewApplyResult(
            ok=True,
            changed_paths=changed,
            activity_item=stored,
            output_path=path,
        )
    except Exception as exc:
        stored = agent_activity.update_activity_status(
            profile,
            item["id"],
            "failed",
            error=str(exc),
        )
        return ReviewApplyResult(ok=False, errors=[str(exc)], activity_item=stored)


def apply_review_activity_item(profile: str, item_id: str) -> ReviewApplyResult:
    """Apply a pending Review-origin Activity item."""
    activity = agent_activity.load_agent_activity(profile)
    item = next(
        (
            row
            for row in activity.get("items") or []
            if _clean_text(row.get("id")) == item_id
        ),
        None,
    )
    if item is None:
        raise KeyError(f"Unknown activity item id: {item_id}")
    if item.get("source_page") != "Review":
        raise ValueError("Only Review-origin items can be applied from Activity.")
    source_ref = _clean_text(item.get("source_ref"))
    parts = source_ref.split(":")
    if len(parts) != 3 or parts[0] != "review":
        raise ValueError(f"Invalid Review source_ref: {source_ref}")
    candidate_type = _clean_text(item.get("candidate_type"))
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    if candidate_type == "evidence":
        return apply_review_evidence_candidate(
            profile,
            parts[1],
            parts[2],
            payload,
            activity_item_id=item_id,
        )
    if candidate_type == "next_action":
        return apply_review_next_action_candidate(
            profile,
            parts[1],
            parts[2],
            payload,
            activity_item_id=item_id,
        )
    if candidate_type == "public_draft":
        return apply_review_public_draft_candidate(
            profile,
            parts[1],
            parts[2],
            payload,
            activity_item_id=item_id,
        )
    raise ValueError(f"Unsupported Review candidate type: {candidate_type}")


def record_writeback_activity(
    profile: str,
    *,
    source_page: str,
    target_owner: str,
    title: str,
    summary: str = "",
    candidate_type: str = "unknown",
    source_ref: str = "",
    refs: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    error: str = "",
    changed_paths: list[str | Path] | None = None,
    status: str = "applied",
) -> dict[str, Any]:
    """Append a writeback Activity item from an owner page."""
    seed = "|".join(
        [
            _clean_text(source_page),
            _clean_text(target_owner),
            _clean_text(candidate_type),
            _clean_text(source_ref),
            _clean_text(title),
            _clean_text(status),
            date.today().isoformat(),
        ]
    )
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:14]
    item = {
        "id": f"act:writeback:{digest}",
        "kind": "writeback",
        "candidate_type": candidate_type,
        "source_page": source_page,
        "source_ref": source_ref,
        "target_owner": target_owner,
        "status": status,
        "title": title,
        "summary": summary,
        "refs": refs or {},
        "payload": payload or {},
        "warnings": list(warnings or []),
        "error": error,
        "changed_paths": [str(path) for path in changed_paths or []],
        "applied_at": date.today().isoformat() if status == "applied" else "",
    }
    return agent_activity.append_activity_item(profile, item)


__all__ = [
    "ReviewApplyResult",
    "activity_item_from_review_candidate",
    "apply_review_activity_item",
    "apply_review_evidence_candidate",
    "apply_review_next_action_candidate",
    "apply_review_public_draft_candidate",
    "record_writeback_activity",
    "review_candidate_id",
    "review_evidence_patch",
    "review_kanban_task",
    "review_window_default",
    "review_window_for_preset",
    "save_review_candidates_to_activity",
]
