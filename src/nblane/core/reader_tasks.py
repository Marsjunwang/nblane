"""In-process background task registry for Paper Reader actions."""

from __future__ import annotations

import os
import threading
import time
import uuid
from collections.abc import Iterator
from typing import Any

from nblane.core import agent_ops, agent_policy, reader_ops
from nblane.core.reader_actions import ReaderActionContext, handle_reader_action
from nblane.core.reader_events import (
    ANALYZE_PAPER,
    ASK_PAPER,
    EXPLAIN_SELECTION,
    PREPARE_READER_ARTIFACTS,
    RETRY_TRANSLATION_SCOPE,
    TRANSLATE_FULL_PAPER,
    TRANSLATE_SELECTION,
    TRANSLATE_VISIBLE_PAGES,
)

TERMINAL_STATUSES = {"done", "failed", "cancelled"}

ALLOWED_READER_TASK_ACTIONS: frozenset[str] = agent_policy.READER_TASK_ACTIONS

_TASKS: dict[str, dict[str, Any]] = {}
_LOCK = threading.RLock()
_COND = threading.Condition(_LOCK)
_TTL_SECONDS = 20 * 60
_TIMEOUT_SECONDS = max(
    30,
    int(os.getenv("NBLANE_READER_TASK_TIMEOUT_SECONDS", "600") or "600"),
)
_DEEP_READ_TASK_TIMEOUT_SECONDS = max(
    _TIMEOUT_SECONDS,
    7200,
    int(os.getenv("NBLANE_DEEP_READ_TASK_TIMEOUT_SECONDS", "7200") or "7200"),
)


def start(
    ctx: ReaderActionContext,
    action: str,
    payload: dict[str, Any] | None = None,
    *,
    task_id: str = "",
    reservation: agent_ops.AgentWrite | None = None,
) -> dict[str, Any]:
    """Start a background Reader action and return its initial snapshot."""

    clean_action = str(action or "").strip()
    if clean_action not in ALLOWED_READER_TASK_ACTIONS:
        raise ValueError(f"Unsupported reader task action: {clean_action}")
    if reservation is not None and (
        reservation.action != agent_policy.READER_ACTIONS[clean_action]
        or reservation.actor != ctx.user_id
        or reservation.pdir.resolve() != ctx.profile_path.resolve()
    ):
        raise ValueError("Reader task reservation identity mismatch")
    clean_task_id = str(task_id or "").strip() or f"reader-task-{uuid.uuid4().hex[:12]}"
    data = dict(payload or {})
    _validate_payload_identity(ctx, data)
    cancel_event = threading.Event()
    started_at = time.time()
    timeout_seconds = _task_timeout_seconds(clean_action, data)
    with _COND:
        existing = _TASKS.get(clean_task_id)
        if isinstance(existing, dict):
            _assert_context_allowed(existing, ctx)
            if str(existing.get("status") or "") not in TERMINAL_STATUSES:
                raise ValueError(f"Reader task already exists: {clean_task_id}")
        _TASKS[clean_task_id] = {
            "task_id": clean_task_id,
            "action": clean_action,
            "event_id": str(data.get("event_id") or ""),
            "status": "running",
            "source_id": ctx.source_id,
            "profile": ctx.profile_name,
            "user_id": ctx.user_id,
            "result": {},
            "error": "",
            "message": "",
            "warnings": [],
            "changed_ids": {},
            "progress": {
                "phase": "running",
                "label": _action_label(clean_action),
                "current": 0,
                "total": 0,
                "saved": 0,
            },
            "started_at": started_at,
            "updated_at": started_at,
            "finished_at": 0.0,
            "timeout_seconds": timeout_seconds,
            "cancel_event": cancel_event,
            "cancel_requested": False,
            "write_committed": False,
            "timed_out": False,
            "timeout_error": "",
        }
        _COND.notify_all()

    def set_committing(value: bool) -> None:
        with _COND:
            task = _TASKS.get(clean_task_id)
            if isinstance(task, dict):
                task["_committing"] = value
                _COND.notify_all()

    def run() -> None:
        commit = None
        if reservation is not None:
            base_commit = reader_ops.worker_commit(
                reservation,
                cancel_event.is_set,
                boundary_lock=_COND,
                set_committing=set_committing,
            )

            def tracked_commit(apply: Any, kinds: tuple[str, ...] | None = None) -> Any:
                try:
                    return base_commit(apply, kinds) if kinds is not None else base_commit(apply)
                finally:
                    with _COND:
                        task = _TASKS.get(clean_task_id)
                        if isinstance(task, dict) and reservation.write_committed:
                            task["write_committed"] = True
                            task["updated_at"] = time.time()
                            _COND.notify_all()

            commit = tracked_commit
        try:
            reader_ops.checkpoint(cancel_event.is_set)
            result = handle_reader_action(
                ctx,
                clean_action,
                data,
                progress_callback=_progress_callback(clean_task_id, clean_action),
                cancel_callback=cancel_event.is_set,
                commit=commit,
            )
            if cancel_event.is_set():
                _finish_stop(clean_task_id, "Reader action cancelled.")
                return
            with _COND:
                task = _TASKS.get(clean_task_id)
                if not isinstance(task, dict):
                    return
                if cancel_event.is_set():
                    _finish_stop_locked(task, "Reader action cancelled.")
                    return
                result_dict = result.to_dict()
                task["result"] = result_dict
                task["message"] = result.message
                task["warnings"] = list(result.warnings)
                task["changed_ids"] = dict(result.changed_ids)
                task["progress"] = _progress_for_result(clean_action, result_dict)
                if result.ok is False:
                    task["status"] = "failed"
                    task["error"] = result.message or "Reader action failed."
                else:
                    task["status"] = "done"
                    task["error"] = ""
                task["updated_at"] = time.time()
                task["finished_at"] = task["updated_at"]
                _COND.notify_all()
        except reader_ops.ReaderCancelled as exc:
            _finish_stop(clean_task_id, str(exc))
        except Exception as exc:
            _finish_stop(
                clean_task_id,
                str(exc),
                cancelled=cancel_event.is_set(),
            )
        finally:
            if reservation is not None:
                agent_ops.abort(reservation)

    thread = threading.Thread(
        target=run,
        name=f"nblane-reader-task-{clean_task_id}",
        daemon=True,
    )
    thread.start()
    watchdog = threading.Thread(
        target=_watchdog_timeout,
        args=(clean_task_id, timeout_seconds),
        name=f"nblane-reader-task-timeout-{clean_task_id}",
        daemon=True,
    )
    watchdog.start()
    cleanup(started_at)
    return snapshot(clean_task_id, ctx=ctx)


def _finish_stop(task_id: str, error: str, *, cancelled: bool = True) -> None:
    with _COND:
        task = _TASKS.get(task_id)
        if isinstance(task, dict):
            _finish_stop_locked(task, error, cancelled=cancelled)


def _finish_stop_locked(task: dict[str, Any], error: str, *, cancelled: bool = True) -> None:
    timed_out = bool(task.get("timed_out"))
    status = "failed" if timed_out or not cancelled else "cancelled"
    message = str(task.get("timeout_error") if timed_out else error or "Reader action cancelled.")
    if task.get("write_committed"):
        message += " Partial writes were committed and kept."
    task["status"] = status
    task["error"] = "" if status == "cancelled" else message
    task["message"] = message
    progress = dict(task.get("progress") or {})
    progress.update({"phase": status, "label": message})
    task["progress"] = progress
    task["updated_at"] = time.time()
    task["finished_at"] = task["updated_at"]
    _COND.notify_all()


def snapshot(task_id: str, *, ctx: ReaderActionContext | None = None) -> dict[str, Any]:
    """Return a JSON-safe task snapshot, or a failed/lost snapshot for unknown ids."""

    clean_id = str(task_id or "").strip()
    if not clean_id:
        return {}
    now = time.time()
    with _LOCK:
        task = _TASKS.get(clean_id)
        if not isinstance(task, dict):
            return _lost_snapshot(clean_id, ctx=ctx, now=now)
        _assert_context_allowed(task, ctx)
        _mark_timeout_locked(clean_id, task, now)
        return _snapshot_locked(task)


def cancel(task_id: str, *, ctx: ReaderActionContext | None = None) -> dict[str, Any]:
    """Request cancellation for a Reader task and return the latest snapshot."""

    clean_id = str(task_id or "").strip()
    if not clean_id:
        return {}
    with _COND:
        task = _TASKS.get(clean_id)
        if not isinstance(task, dict):
            return _lost_snapshot(clean_id, ctx=ctx, now=time.time())
        _assert_context_allowed(task, ctx)
        if str(task.get("status") or "") not in TERMINAL_STATUSES:
            cancel_event = task.get("cancel_event")
            if isinstance(cancel_event, threading.Event):
                cancel_event.set()
            task["cancel_requested"] = True
            task["status"] = "cancelling"
            progress = dict(task.get("progress") or {})
            progress.update({"phase": "cancelling", "label": "Cancelling; committed writes are kept."})
            task["progress"] = progress
            task["updated_at"] = time.time()
        _COND.notify_all()
        return _snapshot_locked(task)


def iter_snapshots(
    task_id: str,
    *,
    ctx: ReaderActionContext | None = None,
    poll_seconds: float = 0.25,
) -> Iterator[dict[str, Any]]:
    """Yield task snapshots until the task reaches a terminal status."""

    clean_id = str(task_id or "").strip()
    if not clean_id:
        return
    last_updated = -1.0
    last_status = ""
    while True:
        current: dict[str, Any] | None = None
        terminal = False
        with _COND:
            task = _TASKS.get(clean_id)
            now = time.time()
            if not isinstance(task, dict):
                current = _lost_snapshot(clean_id, ctx=ctx, now=now)
                terminal = True
            else:
                _assert_context_allowed(task, ctx)
                _mark_timeout_locked(clean_id, task, now)
                snapshot_row = _snapshot_locked(task)
                updated_at = float(snapshot_row.get("updated_at", 0.0) or 0.0)
                status = str(snapshot_row.get("status") or "")
                should_yield = updated_at != last_updated or status != last_status
                if should_yield:
                    last_updated = updated_at
                    last_status = status
                    current = snapshot_row
                terminal = status in TERMINAL_STATUSES
                if not should_yield and terminal:
                    return
                if not should_yield:
                    _COND.wait(timeout=max(0.05, poll_seconds))
                    continue
        if current is not None:
            yield current
        if terminal:
            return


def cleanup(now: float | None = None) -> None:
    """Drop old completed task records."""

    current = time.time() if now is None else now
    with _COND:
        for task_id, task in list(_TASKS.items()):
            _mark_timeout_locked(task_id, task, current)
            updated = float(task.get("updated_at", 0.0) or 0.0)
            status = str(task.get("status") or "")
            if status in TERMINAL_STATUSES and current - updated > _TTL_SECONDS:
                _TASKS.pop(task_id, None)
        _COND.notify_all()


def _progress_callback(task_id: str, action: str):
    def update(raw: dict[str, Any]) -> None:
        with _COND:
            task = _TASKS.get(task_id)
            if not isinstance(task, dict) or str(task.get("status") or "") != "running":
                return
            if action == TRANSLATE_FULL_PAPER:
                total = int(raw.get("segments_selected") or 0)
                current = int(raw.get("segments_processed") or 0)
                saved = int(raw.get("updated") or 0)
                batches = int(raw.get("batches") or 0)
                batches_completed = int(raw.get("batches_completed") or 0)
                label = "Translating paper..."
                if total > 0:
                    label = f"Translating paper... {min(current, total)}/{total}"
                task["progress"] = {
                    "phase": "running",
                    "label": label,
                    "current": min(current, total) if total > 0 else current,
                    "total": total,
                    "saved": saved,
                    "batches": batches,
                    "batches_completed": batches_completed,
                }
            elif action in {TRANSLATE_VISIBLE_PAGES, RETRY_TRANSLATION_SCOPE}:
                total = int(raw.get("total") or raw.get("segments_selected") or 0)
                current = int(raw.get("current") or 0)
                saved = int(raw.get("saved") or 0)
                label = str(raw.get("label") or "Translating visible pages...")
                task["progress"] = {
                    "phase": str(raw.get("phase") or "running"),
                    "label": label,
                    "current": min(current, total) if total > 0 else current,
                    "total": total,
                    "saved": saved,
                    "requested_pages": list(raw.get("requested_pages") or []),
                    "target_lang": str(raw.get("target_lang") or ""),
                    "scope": str(raw.get("scope") or ""),
                }
            elif action == PREPARE_READER_ARTIFACTS:
                task["progress"] = {
                    "phase": str(raw.get("phase") or "running"),
                    "label": str(raw.get("label") or "Preparing reader..."),
                    "current": int(raw.get("current") or 0),
                    "total": int(raw.get("total") or 0),
                    "saved": int(raw.get("saved") or 0),
                }
            elif action in {ANALYZE_PAPER, "codex_deep_read", "generate_review_card"}:
                default_label = {
                    ANALYZE_PAPER: "Analyzing paper...",
                    "codex_deep_read": "Deep read in progress...",
                    "generate_review_card": "Generating review...",
                }.get(action, "Working...")
                task["progress"] = {
                    "phase": str(raw.get("phase") or "running"),
                    "label": str(raw.get("label") or default_label),
                    "current": int(raw.get("current") or 0),
                    "total": int(raw.get("total") or 5),
                    "saved": int(raw.get("saved") or 0),
                }
            else:
                return
            task["updated_at"] = time.time()
            _COND.notify_all()

    return update


def _snapshot_locked(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": str(task.get("task_id") or ""),
        "action": str(task.get("action") or ""),
        "event_id": str(task.get("event_id") or ""),
        "status": str(task.get("status") or ""),
        "source_id": str(task.get("source_id") or ""),
        "profile": str(task.get("profile") or ""),
        "user_id": str(task.get("user_id") or ""),
        "result": task.get("result") if isinstance(task.get("result"), dict) else {},
        "error": str(task.get("error") or ""),
        "message": str(task.get("message") or ""),
        "warnings": list(task.get("warnings") or []),
        "changed_ids": dict(task.get("changed_ids") or {}),
        "cancel_requested": bool(task.get("cancel_requested")),
        "write_committed": bool(task.get("write_committed")),
        "progress": task.get("progress") if isinstance(task.get("progress"), dict) else _progress_for_result(
            str(task.get("action") or ""),
            task.get("result") if isinstance(task.get("result"), dict) else {},
        ),
        "refresh": _refresh_for_task(task),
        "started_at": float(task.get("started_at", 0.0) or 0.0),
        "updated_at": float(task.get("updated_at", 0.0) or 0.0),
        "finished_at": float(task.get("finished_at", 0.0) or 0.0),
    }


def _lost_snapshot(
    task_id: str,
    *,
    ctx: ReaderActionContext | None,
    now: float,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "action": "",
        "event_id": "",
        "status": "failed",
        "source_id": ctx.source_id if ctx is not None else "",
        "profile": ctx.profile_name if ctx is not None else "",
        "user_id": ctx.user_id if ctx is not None else "",
        "result": {},
        "error": "Reader task was lost. Start the action again.",
        "message": "",
        "warnings": [],
        "changed_ids": {},
        "cancel_requested": False,
        "write_committed": False,
        "progress": {
            "phase": "failed",
            "label": "Reader task was lost. Start the action again.",
            "current": 0,
            "total": 0,
            "saved": 0,
        },
        "refresh": {"payload": False, "pages": [], "target_lang": ""},
        "started_at": 0.0,
        "updated_at": now,
        "finished_at": now,
    }


def _action_label(action: str) -> str:
    if action in {TRANSLATE_SELECTION, "translate_segment"}:
        return "Translating selection..."
    if action in {TRANSLATE_VISIBLE_PAGES, RETRY_TRANSLATION_SCOPE}:
        return "Translating visible pages..."
    if action == TRANSLATE_FULL_PAPER:
        return "Translating paper..."
    if action in {ANALYZE_PAPER, "generate_review_card"}:
        return "Reviewing paper..."
    if action == "codex_deep_read":
        return "Analyzing paper..."
    if action == PREPARE_READER_ARTIFACTS:
        return "PDF ready"
    if action == ASK_PAPER:
        return "Answering..."
    return "Working..."


def _progress_for_result(action: str, result: dict[str, Any]) -> dict[str, Any]:
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    saved = int(summary.get("saved") or summary.get("updated") or data.get("saved") or 0)
    if action == PREPARE_READER_ARTIFACTS:
        status = str(summary.get("status") or "")
        label = {
            "ready": "Structured text ready",
            "fallback": "Fallback text ready",
            "failed": "Preparation failed",
            "missing_pdf": "Preparation failed",
        }.get(status, str(result.get("message") or "PDF ready"))
        return {
            "phase": "done" if result.get("ok", True) is not False else "failed",
            "label": label,
            "current": 3 if result.get("ok", True) is not False else 0,
            "total": 3,
            "saved": int(summary.get("segments") or 0),
        }
    if action == ANALYZE_PAPER:
        scores = data.get("analysis") if isinstance(data.get("analysis"), dict) else data.get("structured")
        score_count = len((scores or {}).get("scores") or {}) if isinstance(scores, dict) else 0
        return {
            "phase": "done" if result.get("ok", True) is not False else "failed",
            "label": str(result.get("message") or "Analysis saved"),
            "current": 1,
            "total": 1,
            "saved": score_count,
        }
    if action == ASK_PAPER:
        ok = result.get("ok", True) is not False
        warnings = result.get("warnings") if isinstance(result.get("warnings"), list) else []
        label = str(
            result.get("message")
            or ("Answered" if ok else (warnings[0] if warnings else "Answer failed"))
        )
        return {
            "phase": "done" if ok else "failed",
            "label": label,
            "current": 1 if ok else 0,
            "total": 1,
            "saved": 1 if ok else 0,
        }
    total = int(
        summary.get("segments_selected")
        or summary.get("segments_total")
        or summary.get("batches")
        or 0
    )
    current = total if str(result.get("ok", True)).lower() != "false" else 0
    return {
        "phase": "done" if result.get("ok", True) is not False else "failed",
        "label": str(result.get("message") or _action_label(action)),
        "current": current,
        "total": total,
        "saved": saved,
    }


def _refresh_for_task(task: dict[str, Any]) -> dict[str, Any]:
    result = task.get("result") if isinstance(task.get("result"), dict) else {}
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    action = str(task.get("action") or "")
    return {
        "payload": str(task.get("status") or "") == "done" or bool(task.get("write_committed")),
        "pages": list(summary.get("requested_pages") or []),
        "target_lang": str(summary.get("target_lang") or ""),
        "action": action,
    }


def _assert_context_allowed(task: dict[str, Any], ctx: ReaderActionContext | None) -> None:
    if ctx is None:
        return
    if (
        str(task.get("source_id") or "") != ctx.source_id
        or str(task.get("profile") or "") != ctx.profile_name
        or str(task.get("user_id") or "") != ctx.user_id
    ):
        raise PermissionError("reader task belongs to a different source, profile, or user")


def _validate_payload_identity(ctx: ReaderActionContext, payload: dict[str, Any]) -> None:
    payload_source = str(payload.get("source_id") or "").strip()
    if payload_source and payload_source != ctx.source_id:
        raise ValueError(f"Reader task source mismatch: {payload_source}")
    payload_profile = str(payload.get("profile") or payload.get("profile_name") or "").strip()
    if payload_profile and payload_profile != ctx.profile_name:
        raise ValueError(f"Reader task profile mismatch: {payload_profile}")
    payload_user = str(payload.get("user_id") or "").strip()
    if payload_user and payload_user != ctx.user_id:
        raise ValueError(f"Reader task user mismatch: {payload_user}")


def _positive_float(value: object) -> float | None:
    try:
        clean = float(value)
    except (TypeError, ValueError):
        return None
    return clean if clean > 0 else None


def _task_timeout_seconds(action: str, payload: dict[str, Any]) -> float:
    explicit = _positive_float(
        payload.get("reader_task_timeout_seconds")
        or payload.get("task_timeout_seconds")
    )
    if explicit is not None:
        return max(30.0, explicit)
    if action == "codex_deep_read":
        codex_timeout = _positive_float(
            payload.get("codex_timeout_seconds")
            or payload.get("timeout_seconds")
        )
        if codex_timeout is not None:
            # One Codex call over the full-paper export; the margin covers
            # building the export (PDF crops) before the call starts.
            return max(
                float(_TIMEOUT_SECONDS),
                float(_DEEP_READ_TASK_TIMEOUT_SECONDS),
                codex_timeout + 600.0,
            )
        return float(_DEEP_READ_TASK_TIMEOUT_SECONDS)
    return float(_TIMEOUT_SECONDS)


def _mark_timeout_locked(task_id: str, task: dict[str, Any], now: float) -> None:
    if str(task.get("status") or "") not in {"running", "cancelling"}:
        return
    started = float(task.get("started_at", 0.0) or 0.0)
    timeout_seconds = _positive_float(task.get("timeout_seconds")) or float(_TIMEOUT_SECONDS)
    if not started or now - started <= timeout_seconds:
        return
    cancel_event = task.get("cancel_event")
    if isinstance(cancel_event, threading.Event):
        cancel_event.set()
    task["cancel_requested"] = True
    task["timed_out"] = True
    task["timeout_error"] = f"Reader task timed out after {int(timeout_seconds)} seconds."
    task["status"] = "cancelling"
    progress = dict(task.get("progress") or {})
    progress.update({"phase": "cancelling", "label": task["timeout_error"]})
    task["progress"] = progress
    task["updated_at"] = now
    _COND.notify_all()


def _watchdog_timeout(task_id: str, timeout_seconds: float) -> None:
    time.sleep(max(0.1, timeout_seconds))
    clean_id = str(task_id or "").strip()
    if not clean_id:
        return
    with _COND:
        task = _TASKS.get(clean_id)
        if isinstance(task, dict):
            _mark_timeout_locked(clean_id, task, time.time())


__all__ = [
    "ALLOWED_READER_TASK_ACTIONS",
    "TERMINAL_STATUSES",
    "cancel",
    "cleanup",
    "iter_snapshots",
    "snapshot",
    "start",
]
