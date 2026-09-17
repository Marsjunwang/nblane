"""In-process background task registry for Kanban board AI actions.

Same registry/lock/cancel/watchdog idioms as ``core/ai_stream_tasks``, but
for the Kanban board's non-streaming LLM jobs (gap analysis, task-alignment
options, subtask drafts). Streamlit event handlers only *start* jobs; a
``st.fragment`` poller later moves finished results into the session keys
the board already consumes. Worker threads never touch Streamlit state —
they only write this registry (plus, when ``record_activity`` applies, the
profile activity files, whose snapshots the page-side collector refreshes).
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from collections.abc import Callable
from typing import Any

KIND_GAP = "gap"
KIND_ALIGNMENTS = "alignments"
KIND_SUBTASKS = "subtasks"
KANBAN_AI_KINDS = (KIND_GAP, KIND_ALIGNMENTS, KIND_SUBTASKS)

FINAL_STATUSES = ("done", "failed", "cancelled")

_TASKS: dict[str, dict[str, Any]] = {}
_LOCK = threading.RLock()
_TTL_SECONDS = 20 * 60
_TIMEOUT_SECONDS = max(
    30,
    int(os.getenv("NBLANE_KANBAN_AI_TIMEOUT_SECONDS", "600") or "600"),
)


def _clean(value: object) -> str:
    return str(value or "").strip()


def new_job_id() -> str:
    """Return a fresh registry job id."""
    return f"kbai-{uuid.uuid4().hex[:12]}"


def snapshot(job_id: str) -> dict[str, Any]:
    """Return a copy of one job record.

    Unknown ids report a synthetic failed record so a poller holding a stale
    job id (server restart, registry cleanup) fails visibly instead of
    polling forever. The internal cancel event is never exposed.
    """
    clean_id = _clean(job_id)
    if not clean_id:
        return {}
    now = time.time()
    with _LOCK:
        task = _TASKS.get(clean_id)
        if not isinstance(task, dict):
            return {
                "job_id": clean_id,
                "profile": "",
                "kanban_task_id": "",
                "kind": "",
                "status": "failed",
                "result": None,
                "error": "AI task was lost. Run it again.",
                "started_at": 0.0,
                "updated_at": now,
            }
        _mark_timeout_locked(clean_id, task, now)
        return {
            key: value
            for key, value in task.items()
            if key != "cancel_event"
        }


def cleanup(now: float | None = None) -> None:
    """Drop old completed job records."""
    current = time.time() if now is None else now
    with _LOCK:
        for job_id, task in list(_TASKS.items()):
            _mark_timeout_locked(job_id, task, current)
            updated = float(task.get("updated_at", 0.0) or 0.0)
            status = _clean(task.get("status"))
            if status in FINAL_STATUSES and current - updated > _TTL_SECONDS:
                _TASKS.pop(job_id, None)


def start_job(
    *,
    profile: str,
    kanban_task_id: str,
    kind: str,
    runner: Callable[[], Any],
    job_id: str = "",
) -> dict[str, Any]:
    """Start a background Kanban AI job and return its initial snapshot.

    *runner* executes in a daemon thread and must return the result payload
    (any Python object). It must not touch Streamlit state. Cancellation is
    cooperative: a cancelled job's late result is discarded.
    """
    clean_id = _clean(job_id) or new_job_id()
    clean_kind = _clean(kind)
    if clean_kind not in KANBAN_AI_KINDS:
        raise ValueError(f"unknown kanban AI job kind: {kind!r}")
    cancel_event = threading.Event()
    started_at = time.time()
    with _LOCK:
        _TASKS[clean_id] = {
            "job_id": clean_id,
            "profile": _clean(profile),
            "kanban_task_id": _clean(kanban_task_id),
            "kind": clean_kind,
            "status": "running",
            "result": None,
            "error": "",
            "started_at": started_at,
            "updated_at": started_at,
            "cancel_event": cancel_event,
        }

    def run() -> None:
        try:
            result = runner()
            with _LOCK:
                task = _TASKS.get(clean_id)
                if not isinstance(task, dict):
                    return
                # Already final (user cancel, timeout) — late result loses.
                if _clean(task.get("status")) != "running":
                    return
                if cancel_event.is_set():
                    task["status"] = "cancelled"
                else:
                    task["status"] = "done"
                    task["result"] = result
                task["updated_at"] = time.time()
        except Exception as exc:
            with _LOCK:
                task = _TASKS.get(clean_id)
                if not isinstance(task, dict):
                    return
                if _clean(task.get("status")) != "running":
                    return
                task["status"] = (
                    "cancelled" if cancel_event.is_set() else "failed"
                )
                task["error"] = str(exc)
                task["updated_at"] = time.time()

    thread = threading.Thread(
        target=run,
        name=f"nblane-kanban-ai-{clean_id}",
        daemon=True,
    )
    thread.start()
    watchdog = threading.Thread(
        target=_watchdog_timeout,
        args=(clean_id,),
        name=f"nblane-kanban-ai-timeout-{clean_id}",
        daemon=True,
    )
    watchdog.start()
    cleanup(started_at)
    return snapshot(clean_id)


def cancel_job(job_id: str) -> dict[str, Any]:
    """Request cancellation for a running job."""
    clean_id = _clean(job_id)
    if not clean_id:
        return {}
    with _LOCK:
        task = _TASKS.get(clean_id)
        if not isinstance(task, dict):
            return {}
        cancel_event = task.get("cancel_event")
        if isinstance(cancel_event, threading.Event):
            cancel_event.set()
        task["status"] = "cancelled"
        task["updated_at"] = time.time()
    return snapshot(clean_id)


def cancel_jobs_for_kanban_task(profile: str, kanban_task_id: str) -> int:
    """Cancel every non-final job for one kanban card. Returns the count."""
    clean_profile = _clean(profile)
    clean_task = _clean(kanban_task_id)
    cancelled = 0
    with _LOCK:
        for job_id, task in list(_TASKS.items()):
            if _clean(task.get("profile")) != clean_profile:
                continue
            if _clean(task.get("kanban_task_id")) != clean_task:
                continue
            if _clean(task.get("status")) in FINAL_STATUSES:
                continue
            cancel_event = task.get("cancel_event")
            if isinstance(cancel_event, threading.Event):
                cancel_event.set()
            task["status"] = "cancelled"
            task["updated_at"] = time.time()
            cancelled += 1
    return cancelled


def drop_job(job_id: str) -> None:
    """Remove one job record after its final result was consumed."""
    clean_id = _clean(job_id)
    if not clean_id:
        return
    with _LOCK:
        task = _TASKS.get(clean_id)
        if not isinstance(task, dict):
            return
        if _clean(task.get("status")) in FINAL_STATUSES:
            _TASKS.pop(clean_id, None)


def _mark_timeout_locked(job_id: str, task: dict[str, Any], now: float) -> None:
    """Mark stale running jobs as failed while holding ``_LOCK``."""
    if _clean(task.get("status")) != "running":
        return
    started = float(task.get("started_at", 0.0) or 0.0)
    if not started or now - started <= _TIMEOUT_SECONDS:
        return
    cancel_event = task.get("cancel_event")
    if isinstance(cancel_event, threading.Event):
        cancel_event.set()
    task["status"] = "failed"
    task["error"] = (
        f"AI task timed out after {_TIMEOUT_SECONDS} seconds. "
        "Retry or check the LLM provider connection."
    )
    task["updated_at"] = now


def _watchdog_timeout(job_id: str) -> None:
    """Mark a running job as failed even if no poller arrives."""

    time.sleep(_TIMEOUT_SECONDS)
    clean_id = _clean(job_id)
    if not clean_id:
        return
    with _LOCK:
        task = _TASKS.get(clean_id)
        if isinstance(task, dict):
            _mark_timeout_locked(clean_id, task, time.time())
