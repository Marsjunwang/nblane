"""Review candidate preview and writeback helpers."""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from nblane.core import agent_activity
from nblane.core.file_state import FileConflictError, FileSnapshot
from nblane.core.ingest_merge import merge_ingest_patch
from nblane.core.kanban_io import (
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SECTIONS,
    apply_kanban_reorder,
    find_kanban_card,
    resolve_kanban_section,
    update_kanban,
)
from nblane.core.models import EVIDENCE_TYPES, KanbanTask
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
    """Build an ingest patch for one Review evidence candidate.

    Required candidate fields: ``title`` (``summary`` falls back to it).
    Optional fields honored when present: ``type`` (an evidence type),
    ``date``, ``url``, ``task_id`` (adds a ``kanban:<id>`` source ref and
    marks the Done task crystallized on apply), and ``skill_id`` (adds a
    ``skill:<id>`` source ref recording the suggested skill link; pool
    rows stay unlinked until a human links them in Evidence Review).
    """
    title = _clean_text(candidate.get("title"))
    summary = _clean_text(candidate.get("summary")) or title
    task_id = _clean_text(candidate.get("task_id"))
    evidence_type = _clean_text(candidate.get("type")) or "practice"
    if evidence_type not in EVIDENCE_TYPES:
        evidence_type = "practice"
    row: dict[str, Any] = {
        "type": evidence_type,
        "title": title,
        "summary": summary,
        "review_status": "needs_review",
        "public_readiness": "private",
    }
    date_text = _clean_text(candidate.get("date"))
    if date_text:
        row["date"] = date_text
    url = _clean_text(candidate.get("url"))
    if url:
        row["url"] = url
    source_refs: list[str] = []
    if task_id:
        source_refs.append(f"kanban:{task_id}")
    skill_id = _clean_text(candidate.get("skill_id"))
    if skill_id:
        source_refs.append(f"skill:{skill_id}")
    if source_refs:
        row["source_refs"] = source_refs
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
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> list[dict[str, Any]]:
    """Persist selected Review candidates as pending Activity items.

    *expected_snapshot* (request-start fingerprint of agent-activity.yaml)
    is checked inside the write lock on the first append; a mismatch raises
    ``file_state.FileConflictError`` so the caller can answer 412 instead
    of overwriting a concurrent queue edit.
    """
    stored: list[dict[str, Any]] = []
    snapshot = expected_snapshot
    for candidate in candidates:
        item = activity_item_from_review_candidate(
            profile,
            start,
            end,
            candidate_type,
            candidate,
        )
        stored.append(
            agent_activity.append_activity_item(
                profile, item, expected_snapshot=snapshot
            )
        )
        # The first append consumed the request-start snapshot; later
        # appends re-read under the lock and must not re-check it (the
        # file legitimately changed — by this loop's own writes).
        snapshot = None
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
            updated_done.append(replace(task, crystallized=True))
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
    activity_snapshot: FileSnapshot | None = None,
    pool_snapshot: FileSnapshot | None = None,
    kanban_snapshot: FileSnapshot | None = None,
) -> ReviewApplyResult:
    """Apply one Review evidence candidate via ingest writeback.

    The optional snapshots are request-start fingerprints re-checked
    inside each file's write lock; a mismatch raises
    ``file_state.FileConflictError`` (never swallowed into a failed
    item) so the caller can answer 412.
    """
    item = activity_item_from_review_candidate(profile, start, end, "evidence", candidate)
    if activity_item_id:
        item["id"] = activity_item_id
    agent_activity.append_activity_item(
        profile, item, expected_snapshot=activity_snapshot
    )
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
        save_evidence_pool(
            profile, merge.merged_pool, expected_snapshot=pool_snapshot
        )
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

                def _mark(sections: dict[str, list[KanbanTask]]) -> bool:
                    if KANBAN_DONE not in sections:
                        return False
                    return _mark_done_crystallized(sections, {task_id})

                if update_kanban(
                    profile, _mark, expected_snapshot=kanban_snapshot
                ):
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
    except FileConflictError:
        raise
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
    activity_snapshot: FileSnapshot | None = None,
    kanban_snapshot: FileSnapshot | None = None,
) -> ReviewApplyResult:
    """Append one Review next action candidate to Kanban Queue.

    The kanban append is a locked read-modify-write (``update_kanban``);
    *kanban_snapshot* is re-checked inside that lock and a mismatch raises
    ``file_state.FileConflictError`` so the caller can answer 412.
    """
    item = activity_item_from_review_candidate(profile, start, end, "next_action", candidate)
    if activity_item_id:
        item["id"] = activity_item_id
    agent_activity.append_activity_item(
        profile, item, expected_snapshot=activity_snapshot
    )
    pdir = profile_dir(profile)
    path = pdir / "kanban.md"
    try:
        task = review_kanban_task(candidate)

        def _append(sections: dict[str, list[KanbanTask]]) -> None:
            sections.setdefault(KANBAN_QUEUE, []).append(task)

        update_kanban(profile, _append, expected_snapshot=kanban_snapshot)
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
    except FileConflictError:
        raise
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
    activity_snapshot: FileSnapshot | None = None,
) -> ReviewApplyResult:
    """Create a draft blog post from one Review public candidate."""
    item = activity_item_from_review_candidate(profile, start, end, "public_draft", candidate)
    if activity_item_id:
        item["id"] = activity_item_id
    agent_activity.append_activity_item(
        profile, item, expected_snapshot=activity_snapshot
    )
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
    except FileConflictError:
        raise
    except Exception as exc:
        stored = agent_activity.update_activity_status(
            profile,
            item["id"],
            "failed",
            error=str(exc),
        )
        return ReviewApplyResult(ok=False, errors=[str(exc)], activity_item=stored)


KANBAN_MOVE_ACTIONS = ("move",)


def activity_item_from_kanban_candidate(
    profile: str,
    candidate: dict[str, Any],
    *,
    activity_item_id: str = "",
) -> dict[str, Any]:
    """Build the Activity item for one kanban move candidate.

    The item uses the Review source shape so it can be applied from the
    existing Agent Activity UI; ``payload`` carries the self-describing
    move request ``{action, card_ref, target_section, note}``.
    """
    card_ref = _clean_text(candidate.get("card_ref"))
    action = _clean_text(candidate.get("action")) or "move"
    target_section = _clean_text(candidate.get("target_section"))
    today = date.today().isoformat()
    item: dict[str, Any] = {
        "kind": "candidate",
        "candidate_type": "kanban_move",
        "source_page": "Review",
        "source_ref": f"review:{today}:{today}",
        "target_owner": "kanban",
        "status": "pending",
        "title": (
            f"Move kanban card: {card_ref}" if card_ref else "Kanban move"
        ),
        "summary": _clean_text(candidate.get("note")),
        "refs": {"files": [_relative(profile_dir(profile) / "kanban.md")]},
        "payload": copy.deepcopy(candidate),
        "preview": _preview_yaml(
            {
                "action": action,
                "card_ref": card_ref,
                "target_section": target_section,
            }
        ),
    }
    if activity_item_id:
        item["id"] = activity_item_id
    return item


def apply_review_kanban_candidate(
    profile: str,
    candidate: dict[str, Any],
    *,
    activity_item_id: str = "",
    activity_snapshot: FileSnapshot | None = None,
    kanban_snapshot: FileSnapshot | None = None,
) -> ReviewApplyResult:
    """Apply one kanban move candidate: relocate a card between sections.

    The parse → reorder → save cycle runs inside the kanban.md write lock
    (``update_kanban``), so a concurrent kanban write (MCP apply, board
    edit) can no longer be silently overwritten after the Activity item
    was marked ``applied``. Failures (unknown action/section, missing or
    ambiguous card_ref) mark the Activity item ``failed`` with a clear
    error instead of raising; a *kanban_snapshot* mismatch raises
    ``file_state.FileConflictError`` so the caller can answer 412.
    """
    item = activity_item_from_kanban_candidate(
        profile,
        candidate,
        activity_item_id=activity_item_id,
    )
    stored = agent_activity.append_activity_item(
        profile, item, expected_snapshot=activity_snapshot
    )
    item_id = _clean_text(stored.get("id"))
    path = profile_dir(profile) / "kanban.md"

    def _fail(message: str) -> ReviewApplyResult:
        failed = agent_activity.update_activity_status(
            profile,
            item_id,
            "failed",
            error=message,
        )
        return ReviewApplyResult(
            ok=False,
            errors=[message],
            activity_item=failed,
        )

    try:
        action = _clean_text(candidate.get("action")) or "move"
        if action not in KANBAN_MOVE_ACTIONS:
            return _fail(
                f"unsupported kanban action {action!r} "
                f"(expected one of: {', '.join(KANBAN_MOVE_ACTIONS)})"
            )
        card_ref = _clean_text(candidate.get("card_ref"))
        if not card_ref:
            return _fail("kanban move candidate is missing card_ref")
        target = resolve_kanban_section(
            candidate.get("target_section")
        )
        if target is None:
            return _fail(
                f"unknown kanban section "
                f"{_clean_text(candidate.get('target_section'))!r} "
                f"(expected one of: {', '.join(KANBAN_SECTIONS)})"
            )

        def _move(
            sections: dict[str, list[KanbanTask]],
        ) -> tuple[str, str]:
            hit, _match_kind, match_error = find_kanban_card(
                sections, card_ref
            )
            if hit is None:
                return ("error", match_error)
            from_section, _index, task = hit
            if from_section == target:
                return ("noop", task.title)
            moved = apply_kanban_reorder(
                sections,
                [{"id": task.id, "to_section": target}],
                auto_dates=True,
            )
            sections.clear()
            sections.update(moved)
            return ("moved", task.title)

        outcome, title = update_kanban(
            profile, _move, expected_snapshot=kanban_snapshot
        )
        if outcome == "error":
            return _fail(title)
        warnings: list[str] = []
        changed: list[Path] = []
        if outcome == "noop":
            warnings.append(
                f"card {title.strip()!r} is already in "
                f"{target!r}; no move needed"
            )
        else:
            changed = [path]
        applied = agent_activity.update_activity_status(
            profile,
            item_id,
            "applied",
            warnings=warnings,
            changed_paths=changed,
        )
        return ReviewApplyResult(
            ok=True,
            changed_paths=changed,
            warnings=warnings,
            activity_item=applied,
        )
    except FileConflictError:
        raise
    except Exception as exc:
        return _fail(str(exc))


def apply_review_activity_item(
    profile: str,
    item_id: str,
    *,
    activity_snapshot: FileSnapshot | None = None,
    pool_snapshot: FileSnapshot | None = None,
    kanban_snapshot: FileSnapshot | None = None,
) -> ReviewApplyResult:
    """Apply a pending Review-origin Activity item.

    The optional snapshots are request-start fingerprints threaded into
    the applier's first write per file; a mismatch raises
    ``file_state.FileConflictError`` so the web layer can answer 412.
    """
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
            activity_snapshot=activity_snapshot,
            pool_snapshot=pool_snapshot,
            kanban_snapshot=kanban_snapshot,
        )
    if candidate_type == "next_action":
        return apply_review_next_action_candidate(
            profile,
            parts[1],
            parts[2],
            payload,
            activity_item_id=item_id,
            activity_snapshot=activity_snapshot,
            kanban_snapshot=kanban_snapshot,
        )
    if candidate_type == "public_draft":
        return apply_review_public_draft_candidate(
            profile,
            parts[1],
            parts[2],
            payload,
            activity_item_id=item_id,
            activity_snapshot=activity_snapshot,
        )
    if candidate_type == "kanban_move":
        return apply_review_kanban_candidate(
            profile,
            payload,
            activity_item_id=item_id,
            activity_snapshot=activity_snapshot,
            kanban_snapshot=kanban_snapshot,
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
    "KANBAN_MOVE_ACTIONS",
    "ReviewApplyResult",
    "activity_item_from_kanban_candidate",
    "activity_item_from_review_candidate",
    "apply_review_activity_item",
    "apply_review_evidence_candidate",
    "apply_review_kanban_candidate",
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
