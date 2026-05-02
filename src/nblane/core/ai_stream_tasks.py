"""Persistent in-process AI stream task registry for Streamlit reruns."""

from __future__ import annotations

import os
import threading
import time
import uuid
from typing import Any

from nblane.core import ai_dispatcher

_TASKS: dict[str, dict[str, Any]] = {}
_LOCK = threading.RLock()
_TTL_SECONDS = 20 * 60
_TIMEOUT_SECONDS = max(
    30,
    int(os.getenv("NBLANE_AI_STREAM_TIMEOUT_SECONDS", "240") or "240"),
)


def snapshot(task_id: str) -> dict[str, Any]:
    """Return a JSON-safe snapshot for one stream task."""
    clean_id = str(task_id or "").strip()
    if not clean_id:
        return {}
    now = time.time()
    with _LOCK:
        task = _TASKS.get(clean_id)
        if not isinstance(task, dict):
            return {
                "task_id": clean_id,
                "operation": "",
                "status": "failed",
                "text": "",
                "error": "AI generation task was lost. Regenerate the patch.",
                "patch": {},
                "started_at": 0.0,
                "updated_at": now,
            }
        _mark_timeout_locked(clean_id, task, now)
        return {
            "task_id": clean_id,
            "operation": str(task.get("operation", "") or ""),
            "status": str(task.get("status", "") or ""),
            "text": str(task.get("text", "") or ""),
            "error": str(task.get("error", "") or ""),
            "patch": task.get("patch") if isinstance(task.get("patch"), dict) else {},
            "started_at": float(task.get("started_at", 0.0) or 0.0),
            "updated_at": float(task.get("updated_at", 0.0) or 0.0),
        }


def cleanup(now: float | None = None) -> None:
    """Drop old completed task records."""
    current = time.time() if now is None else now
    with _LOCK:
        for task_id, task in list(_TASKS.items()):
            _mark_timeout_locked(task_id, task, current)
            updated = float(task.get("updated_at", 0.0) or 0.0)
            status = str(task.get("status", "") or "")
            if status in {"done", "failed", "cancelled"} and current - updated > _TTL_SECONDS:
                _TASKS.pop(task_id, None)


def start_ai_patch_stream(
    *,
    task_id: str,
    profile: str,
    slug: str,
    meta: dict[str, Any],
    markdown: str,
    selected_block: dict[str, Any],
    operation: str,
    prompt: str,
    visual_kind: str,
) -> dict[str, Any]:
    """Start an AI patch generation task and return its initial snapshot."""
    clean_task_id = str(task_id or "").strip() or f"ai-stream-{uuid.uuid4().hex[:12]}"
    cancel_event = threading.Event()
    started_at = time.time()
    with _LOCK:
        _TASKS[clean_task_id] = {
            "operation": operation,
            "status": "running",
            "text": "",
            "error": "",
            "patch": {},
            "started_at": started_at,
            "updated_at": started_at,
            "cancel_event": cancel_event,
        }

    def append_delta(delta: str) -> None:
        if cancel_event.is_set():
            raise RuntimeError("AI stream cancelled")
        if not delta:
            return
        with _LOCK:
            task = _TASKS.get(clean_task_id)
            if not isinstance(task, dict):
                return
            if str(task.get("status", "") or "") != "running":
                return
            task["text"] = str(task.get("text", "") or "") + str(delta)
            task["updated_at"] = time.time()

    def run() -> None:
        try:
            patch = ai_dispatcher.generate_ai_patch(
                profile=profile,
                slug=slug,
                meta=meta,
                markdown=markdown,
                selected_block=selected_block,
                operation=operation,
                prompt=prompt,
                visual_kind=visual_kind,
                source_event_id=clean_task_id,
                stream_callback=append_delta,
            )
            with _LOCK:
                task = _TASKS.get(clean_task_id)
                if not isinstance(task, dict):
                    return
                if cancel_event.is_set():
                    task["status"] = "cancelled"
                elif str(task.get("status", "") or "") == "running":
                    task["status"] = "done"
                    task["patch"] = patch
                    if not str(task.get("text", "") or "").strip():
                        task["text"] = str(patch.get("markdown_fallback", "") or "")
                task["updated_at"] = time.time()
        except Exception as exc:
            with _LOCK:
                task = _TASKS.get(clean_task_id)
                if not isinstance(task, dict):
                    return
                task["status"] = "cancelled" if cancel_event.is_set() else "failed"
                task["error"] = str(exc)
                task["updated_at"] = time.time()

    thread = threading.Thread(
        target=run,
        name=f"nblane-ai-stream-{clean_task_id}",
        daemon=True,
    )
    thread.start()
    watchdog = threading.Thread(
        target=_watchdog_timeout,
        args=(clean_task_id,),
        name=f"nblane-ai-stream-timeout-{clean_task_id}",
        daemon=True,
    )
    watchdog.start()
    cleanup(started_at)
    return snapshot(clean_task_id)


def cancel(task_id: str) -> dict[str, Any]:
    """Request cancellation for a running stream task."""
    clean_id = str(task_id or "").strip()
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


def _mark_timeout_locked(task_id: str, task: dict[str, Any], now: float) -> None:
    """Mark stale running tasks as failed while holding ``_LOCK``."""
    if str(task.get("status", "") or "") != "running":
        return
    started = float(task.get("started_at", 0.0) or 0.0)
    if not started or now - started <= _TIMEOUT_SECONDS:
        return
    cancel_event = task.get("cancel_event")
    if isinstance(cancel_event, threading.Event):
        cancel_event.set()
    task["status"] = "failed"
    task["error"] = (
        f"AI generation timed out after {_TIMEOUT_SECONDS} seconds. "
        "Regenerate or check the LLM provider connection."
    )
    task["updated_at"] = now


def _watchdog_timeout(task_id: str) -> None:
    """Mark a running task as failed even if no client poll arrives."""

    time.sleep(_TIMEOUT_SECONDS)
    clean_id = str(task_id or "").strip()
    if not clean_id:
        return
    with _LOCK:
        task = _TASKS.get(clean_id)
        if isinstance(task, dict):
            _mark_timeout_locked(clean_id, task, time.time())
