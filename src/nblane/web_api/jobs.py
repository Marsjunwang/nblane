"""In-process async-job registry for the SPA backend (LLM long tasks).

Mirrors the ``web_reader_api`` paper-library search-job design — an
in-memory dict guarded by a lock, a daemon worker thread per job, and a
seq-numbered event log replayed over SSE — so the single-worker uvicorn
process can run blocking LLM work (up to ~55s) off the request thread.

Contract:

- Statuses: ``queued`` -> ``running`` -> ``done`` | ``failed``
  (``FINAL_STATUSES``). Cancellation and the per-kind watchdog request a
  cooperative stop; the worker publishes the terminal state at a checkpoint
  or after the current short commit segment, including retained partial writes.
- SSE frames (``GET .../jobs/{id}/stream``): ``job`` (initial snapshot,
  replay-safe for late subscribers), ``progress`` (one per logged phase
  event), ``done`` (terminal, carries ``result``), ``error`` (terminal,
  carries the structured ``{code, message}`` error).
- Job kinds register a validator (raw ``input`` dict -> cleaned input,
  raising :class:`JobInputError`), explicit agent effect/action/journal
  policy, and a runner. Context runners also receive a
  ``JobExecutionContext`` for checkpoints and strict worker-local commits.

Registered kinds include ``project-suggest-refs`` (Project Board AI ref
suggestion), ``evidence-crystallize`` (LLM Done-task -> evidence draft),
the ``content-*`` editor jobs and the ``career-*`` workspace jobs. Records are
process-local by design (single worker); results live only in memory and
are pruned after ``_JOB_TTL_SECONDS``.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nblane.core import agent_ops, agent_policy, career_ai, content_ai, git_backup
from nblane.core import profile_io, project_suggest
from nblane.core.project_board import load_project_board

KIND_PROJECT_SUGGEST_REFS = "project-suggest-refs"
KIND_EVIDENCE_CRYSTALLIZE = "evidence-crystallize"
KIND_CONTENT_REWRITE = "content-rewrite"
KIND_CONTENT_META = "content-meta"
KIND_CONTENT_COVER = "content-cover"
KIND_CONTENT_SOCIAL = "content-social"
KIND_CAREER_MATCH = "career-match"
KIND_CAREER_TAILOR = "career-tailor"
KIND_CAREER_STRUCTURE = "career-structure"

FINAL_STATUSES = ("done", "failed")

_JOB_TTL_SECONDS = 20 * 60
_JOB_TIMEOUT_SECONDS = max(
    30,
    int(os.getenv("NBLANE_WEB_API_JOB_TIMEOUT_SECONDS", "600") or "600"),
)
_MAX_EVENTS = 200

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.RLock()


class UnknownJobKindError(ValueError):
    """Raised when ``create_job`` gets an unregistered job kind."""


class UnclassifiedJobKindError(ValueError):
    """Raised when an agent targets a kind without an explicit policy."""


class JobInputError(ValueError):
    """Raised when a kind validator rejects the raw job input."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class JobFailedError(RuntimeError):
    """Structured job failure raised by runners; becomes the job error.

    ``run_id`` names the AI gateway run that failed, when there is one; the
    AI exceptions panel then lists that run once instead of run + job.
    """

    def __init__(self, code: str, message: str, *, run_id: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.run_id = run_id


class JobCancelledError(JobFailedError):
    """The worker reached a commit/checkpoint boundary after stop was requested."""


@dataclass(frozen=True)
class JobPolicy:
    kind: str
    effect: str
    action: str
    tier: str
    journal: tuple[str, ...]


@dataclass
class JobKind:
    """One registered async-job kind, including its explicit agent policy.

    ``timeout_seconds`` overrides the global watchdog for kinds whose work
    is known to be short (e.g. a single LLM call the user is waiting on in
    a wizard); 0/None falls back to ``_JOB_TIMEOUT_SECONDS``. Runners that
    set ``context_runner`` receive a fourth ``JobExecutionContext`` argument.
    """

    name: str
    validate: Callable[[dict[str, Any]], dict[str, Any]]
    run: Callable[..., Any]
    queued_message: str = "Queued job."
    timeout_seconds: float = 0.0
    timeout_message: str = ""
    effect: str = ""
    action: str = ""
    journal: tuple[str, ...] = ()
    context_runner: bool = False

    def __post_init__(self) -> None:
        classification = _JOB_CLASSIFICATIONS.get(self.name)
        if classification is None:
            return
        effect, action, journal, context_runner = classification
        self.effect = self.effect or effect
        self.action = self.action or action
        self.journal = self.journal or journal
        self.context_runner = self.context_runner or context_runner


_JOB_CLASSIFICATIONS: dict[str, tuple[str, str, tuple[str, ...], bool]] = {
    "project-suggest-refs": ("draft", "ai.draft", (), False),
    "evidence-crystallize": ("draft", "ai.draft", (), False),
    "content-rewrite": ("draft", "ai.draft", (), False),
    "content-meta": ("draft", "ai.draft", (), False),
    "content-social": ("draft", "ai.draft", (), False),
    "content-cover": ("candidate", "ai.draft", (), True),
    "content-image": ("candidate", "ai.draft", (), True),
    "career-match": ("draft", "ai.draft", (), False),
    "career-tailor": ("draft", "ai.draft", (), False),
    "career-structure": ("draft", "ai.draft", (), False),
    "research-connector-preview": ("draft", "ai.draft", (), True),
    "research-connector-import": (
        "write",
        "research.import",
        ("research_source", "file:research/connectors.yaml"),
        True,
    ),
    "paper-quick-analysis": ("write", "research.paper_analysis", ("research_source",), True),
    "paper-deep-read": ("write", "research.paper_analysis", ("research_source",), True),
}


_KINDS: dict[str, JobKind] = {}


def register_kind(spec: JobKind) -> None:
    """Register (or replace) one job kind from another router module."""
    _KINDS[spec.name] = spec


def job_policy(kind: str) -> JobPolicy:
    """Resolve a kind's real effect/action/tier; unknown classifications fail closed."""
    clean_kind = _clean(kind)
    spec = _KINDS.get(clean_kind)
    if spec is None:
        known = ", ".join(sorted(_KINDS)) or "(none)"
        raise UnknownJobKindError(
            f"Unknown job kind: {clean_kind!r}. Registered kinds: {known}."
        )
    if not spec.effect or not spec.action:
        raise UnclassifiedJobKindError(clean_kind)
    return JobPolicy(
        kind=clean_kind,
        effect=spec.effect,
        action=spec.action,
        tier=agent_policy.tier_for(spec.action),
        journal=tuple(spec.journal),
    )


def _clean(value: object) -> str:
    return str(value or "").strip()


def sse_event(event: str, data: dict[str, Any]) -> str:
    """Serialize one SSE frame (same wire format as the reader sidecar)."""
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


def _append_event(job_id: str, event: dict[str, Any]) -> None:
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return
        seq = int(job.get("_event_seq") or 0) + 1
        job["_event_seq"] = seq
        started = job.get("_started_monotonic")
        payload = {
            key: value
            for key, value in event.items()
            if value not in ("", [], None) and not str(key).startswith("_")
        }
        payload["seq"] = seq
        payload["created_at"] = time.time()
        if isinstance(started, (int, float)) and float(started) > 0:
            payload.setdefault(
                "elapsed_ms",
                max(0, int((time.monotonic() - float(started)) * 1000)),
            )
        events = job.setdefault("events", [])
        if isinstance(events, list):
            events.append(payload)
            if len(events) > _MAX_EVENTS:
                del events[:-_MAX_EVENTS]


def _update_job(job_id: str, **updates: Any) -> None:
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return
        for key, value in updates.items():
            job[key] = value


def _progress_reporter(job_id: str) -> Callable[..., None]:
    def report(phase: str, message: str = "", **extra: Any) -> None:
        clean_phase = _clean(phase) or "running"
        clean_message = _clean(message)
        _append_event(
            job_id,
            {
                "event": "progress",
                "phase": clean_phase,
                "message": clean_message,
                **extra,
            },
        )
        updates: dict[str, Any] = {"phase": clean_phase}
        if clean_message:
            updates["message"] = clean_message
        _update_job(job_id, **updates)

    return report


def _snapshot(job: dict[str, Any]) -> dict[str, Any]:
    """Public view of one job record (no result, events, or internals)."""
    snapshot = {
        key: value
        for key, value in job.items()
        if not str(key).startswith("_") and key not in {"result", "events"}
    }
    started = job.get("_started_monotonic")
    finished = job.get("_finished_monotonic")
    if isinstance(started, (int, float)) and float(started) > 0:
        end = (
            float(finished)
            if isinstance(finished, (int, float)) and float(finished) > 0
            else time.monotonic()
        )
        snapshot["elapsed_ms"] = max(0, int((end - float(started)) * 1000))
    else:
        snapshot["elapsed_ms"] = 0
    return snapshot


def read_job(job_id: str) -> dict[str, Any] | None:
    """Return ``{"snapshot", "result", "events"}`` under one lock, or None.

    ``result`` is only populated once the job is done; ``events`` is a copy
    of the progress-event log (each entry carries a monotonically increasing
    ``seq`` for SSE replay).
    """
    clean_id = _clean(job_id)
    if not clean_id:
        return None
    with _LOCK:
        _mark_timeout_locked(clean_id, time.time())
        job = _JOBS.get(clean_id)
        if not job:
            return None
        events = job.get("events")
        return {
            "snapshot": _snapshot(job),
            "result": job.get("result") if job.get("status") == "done" else None,
            "events": list(events) if isinstance(events, list) else [],
        }


def _scope_key(value: str | Path | None) -> str:
    """Normalize a profile directory identity for process-local jobs."""

    if value is None:
        return ""
    try:
        return str(Path(value).resolve())
    except (OSError, RuntimeError, TypeError):
        return _clean(value)


def failed_jobs(
    profile: str,
    *,
    profile_scope: str | Path | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return recent failed jobs for one profile.

    Jobs are intentionally process-local, so this is a best-effort source for
    the profile's AI exception projection. Persistent AI run failures come
    from ``ai-runs.yaml`` instead.
    """

    clean_profile = _clean(profile)
    clean_scope = _scope_key(profile_scope)
    now = time.time()
    with _LOCK:
        _prune_jobs()
        for job_id in list(_JOBS):
            _mark_timeout_locked(job_id, now)
        rows = [
            _snapshot(job)
            for job in _JOBS.values()
            if _clean(job.get("profile")) == clean_profile
            and (
                not clean_scope
                or _clean(job.get("_profile_scope")) == clean_scope
            )
            and job.get("status") == "failed"
            # A user cancel is not an AI failure; keep it out of the panel.
            and (job.get("error") or {}).get("code") != "job_cancelled"
        ]
    rows.sort(key=lambda item: float(item.get("finished_at") or item.get("created_at") or 0), reverse=True)
    return rows[: max(1, min(int(limit), 200))]


CANCELLED_MESSAGE = "已取消。"


def _stop_message_locked(job: dict[str, Any], message: str) -> str:
    if not job.get("write_committed") or "已保留部分写入" in message:
        return message
    summary = _clean(job.get("commit_summary")) or "已完成的提交段"
    return f"{message.rstrip('。')}；已保留部分写入：{summary}。"


def _stop_error_locked(job: dict[str, Any]) -> JobCancelledError:
    code = _clean(job.get("_cancel_code")) or "job_cancelled"
    message = _clean(job.get("_cancel_message")) or CANCELLED_MESSAGE
    return JobCancelledError(code, _stop_message_locked(job, message))


def _request_stop_locked(job: dict[str, Any], code: str, message: str) -> None:
    if not job.get("_cancel_code"):
        job["_cancel_code"] = code
        job["_cancel_message"] = message
    job["cancel_requested"] = True
    event = job.get("_cancel_event")
    if isinstance(event, threading.Event):
        event.set()
    job["phase"] = "cancelling"
    job["message"] = (
        "正在停止；当前提交段会完成并记录，随后结束任务。"
        if job.get("_committing")
        else "正在停止；任务会在下一个检查点结束。"
    )


class JobExecutionContext:
    """Worker-local cancellation and strict commit boundary for one job."""

    def __init__(
        self,
        job_id: str,
        spec: JobKind,
        agent_write: agent_ops.AgentWrite | None,
    ) -> None:
        self.job_id = job_id
        self.spec = spec
        self.agent_write = agent_write

    def checkpoint(self) -> None:
        """Raise before more work when cancellation/timeout won the lock race."""
        with _LOCK:
            job = _JOBS.get(self.job_id)
            if not job or job.get("status") in FINAL_STATUSES:
                raise JobCancelledError("job_cancelled", CANCELLED_MESSAGE)
            if job.get("_cancel_code"):
                raise _stop_error_locked(job)

    def cancel_requested(self) -> bool:
        """Cooperative cancellation callback for Codex and other long runners."""
        with _LOCK:
            job = _JOBS.get(self.job_id)
            return bool(job and job.get("cancel_requested"))

    def _begin_commit(self) -> None:
        with _LOCK:
            job = _JOBS.get(self.job_id)
            if not job or job.get("status") in FINAL_STATUSES:
                raise JobCancelledError("job_cancelled", CANCELLED_MESSAGE)
            if job.get("_cancel_code"):
                raise _stop_error_locked(job)
            job["_committing"] = True

    def _end_commit(self) -> None:
        with _LOCK:
            job = _JOBS.get(self.job_id)
            if job:
                job["_committing"] = False

    def _mark_committed(self, summary: str) -> None:
        if self.agent_write is not None:
            self.agent_write.write_committed = True
        with _LOCK:
            job = _JOBS.get(self.job_id)
            if not job:
                return
            job["write_committed"] = True
            clean_summary = _clean(summary) or self.spec.action or self.spec.name
            summaries = job.setdefault("_commit_summaries", [])
            if clean_summary not in summaries:
                summaries.append(clean_summary)
            job["commit_summary"] = "；".join(summaries)

    def apply(
        self,
        fn: Callable[[], Any],
        *,
        kinds: tuple[str, ...] | None = None,
        summary: str = "",
    ) -> Any:
        """Run one short domain commit with worker-local before/after journaling."""
        self._begin_commit()
        write = self.agent_write
        prior_committed = bool(write and write.write_committed)
        try:
            if write is not None:
                agent_ops.capture_before(write, kinds)
            try:
                value = fn()
            except BaseException:
                if write is not None:
                    try:
                        entry = agent_ops.finish(write, refund_noop=False)
                    except agent_ops.AgentJournalError:
                        self._mark_committed(summary)
                        raise
                    if entry is not None:
                        self._mark_committed(summary)
                    else:
                        write.write_committed = prior_committed
                raise
            if write is not None:
                write.write_committed = True
                try:
                    entry = agent_ops.finish(write, refund_noop=False)
                except agent_ops.AgentJournalError:
                    self._mark_committed(summary)
                    raise
                if entry is not None:
                    self._mark_committed(summary)
                else:
                    write.write_committed = prior_committed
            elif self.spec.effect in {"write", "candidate"}:
                self._mark_committed(summary)
            return value
        except agent_ops.AgentJournalError as exc:
            raise JobFailedError("agent_journal_failed", str(exc)) from exc
        finally:
            self._end_commit()


def _finish_failure(
    job_id: str,
    code: str,
    message: str,
    *,
    run_id: str = "",
) -> None:
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job or job.get("status") in FINAL_STATUSES:
            return
        terminal_message = _stop_message_locked(job, message)
        job.update(
            status="failed",
            phase="failed",
            message=terminal_message,
            error={"code": code, "message": terminal_message},
            finished_at=time.time(),
            _finished_monotonic=time.monotonic(),
            **({"run_id": run_id} if run_id else {}),
        )
        event = job.get("_finished_event")
        if isinstance(event, threading.Event):
            event.set()


def _finish_done(job_id: str, kind: str, result: Any) -> None:
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job or job.get("status") in FINAL_STATUSES:
            return
        if job.get("_cancel_code"):
            raise _stop_error_locked(job)
        job.update(
            status="done",
            phase="done",
            message=f"{kind} job finished.",
            result=result,
            finished_at=time.time(),
            _finished_monotonic=time.monotonic(),
        )
        event = job.get("_finished_event")
        if isinstance(event, threading.Event):
            event.set()


def create_job(
    profile: str,
    kind: str,
    job_input: dict[str, Any],
    *,
    profile_scope: str | Path | None = None,
    agent_write: agent_ops.AgentWrite | None = None,
    actor: str = "",
) -> dict[str, Any]:
    """Validate, register, and start a job with an optional transferred reservation."""
    clean_kind = _clean(kind)
    spec = _KINDS.get(clean_kind)
    if spec is None:
        known = ", ".join(sorted(_KINDS)) or "(none)"
        raise UnknownJobKindError(
            f"Unknown job kind: {clean_kind!r}. Registered kinds: {known}."
        )
    if not isinstance(job_input, dict):
        raise JobInputError("invalid_job_input", "Job input must be an object.")
    clean_input = spec.validate(job_input)
    _prune_jobs()
    job_id = f"job-{uuid.uuid4().hex[:16]}"
    now = time.time()
    execution = JobExecutionContext(job_id, spec, agent_write)
    job: dict[str, Any] = {
        "job_id": job_id,
        "profile": _clean(profile),
        "_profile_scope": _scope_key(profile_scope),
        "kind": clean_kind,
        "status": "queued",
        "phase": "queued",
        "message": spec.queued_message,
        "created_at": now,
        "started_at": 0.0,
        "finished_at": 0.0,
        "cancel_requested": False,
        "write_committed": False,
        "commit_summary": "",
        "error": None,
        "result": None,
        "events": [],
        "_event_seq": 0,
        "_started_monotonic": 0.0,
        "_finished_monotonic": 0.0,
        "_cancel_event": threading.Event(),
        "_finished_event": threading.Event(),
        "_started_event": threading.Event(),
        "_cancel_code": "",
        "_cancel_message": "",
        "_committing": False,
        "_commit_summaries": [],
        "_execution": execution,
        "_agent_write": agent_write,
        "_actor": _clean(actor) or (agent_write.actor if agent_write else "web"),
    }
    with _LOCK:
        _JOBS[job_id] = job
    bundle = read_job(job_id)
    initial = bundle["snapshot"] if bundle else {}

    def worker() -> None:
        started = time.monotonic()
        _update_job(
            job_id,
            status="running",
            phase="starting",
            message=f"Starting {clean_kind} job.",
            started_at=time.time(),
            _started_monotonic=started,
        )
        started_event = job.get("_started_event")
        if isinstance(started_event, threading.Event):
            started_event.set()
        report = _progress_reporter(job_id)
        try:
            git_backup.start_operation(job["_actor"])
            execution.checkpoint()
            if spec.context_runner:
                result = spec.run(_clean(profile), clean_input, report, execution)
            else:
                result = spec.run(_clean(profile), clean_input, report)
            execution.checkpoint()
            _finish_done(job_id, clean_kind, result)
        except JobCancelledError as exc:
            _finish_failure(job_id, exc.code, exc.message, run_id=exc.run_id)
        except JobFailedError as exc:
            _finish_failure(job_id, exc.code, exc.message, run_id=exc.run_id)
        except Exception as exc:  # noqa: BLE001 - surface any runner failure
            _finish_failure(job_id, "job_failed", str(exc))
        finally:
            if agent_write is not None:
                agent_ops.abort(agent_write)

    worker_thread = threading.Thread(
        target=worker, name=f"web-api-job-{job_id}", daemon=True
    )
    watchdog_thread = threading.Thread(
        target=_watchdog_timeout,
        args=(job_id,),
        name=f"web-api-job-timeout-{job_id}",
        daemon=True,
    )
    try:
        watchdog_thread.start()
        worker_thread.start()
    except Exception:
        with _LOCK:
            _JOBS.pop(job_id, None)
        for event_name in ("_started_event", "_finished_event"):
            event = job.get(event_name)
            if isinstance(event, threading.Event):
                event.set()
        if agent_write is not None:
            agent_ops.abort(agent_write)
        raise
    return initial


def cancel_job(job_id: str) -> bool:
    """Request a cooperative stop; the worker publishes the real terminal state."""
    clean_id = _clean(job_id)
    with _LOCK:
        job = _JOBS.get(clean_id)
        if not job or job.get("status") in FINAL_STATUSES:
            return False
        _request_stop_locked(job, "job_cancelled", CANCELLED_MESSAGE)
    return True


def _prune_jobs() -> None:
    cutoff = time.time() - _JOB_TTL_SECONDS
    with _LOCK:
        stale = [
            job_id
            for job_id, job in _JOBS.items()
            if job.get("status") in FINAL_STATUSES
            and float(job.get("finished_at") or job.get("created_at") or 0) < cutoff
        ]
        for job_id in stale:
            _JOBS.pop(job_id, None)


def _job_timeout(job: dict[str, Any]) -> float:
    """Effective timeout for a job: kind override, else the global default."""
    spec = _KINDS.get(str(job.get("kind") or ""))
    if spec and spec.timeout_seconds and spec.timeout_seconds > 0:
        return float(spec.timeout_seconds)
    return float(_JOB_TIMEOUT_SECONDS)


def _mark_timeout_locked(job_id: str, now: float) -> None:
    """Request a timeout stop at the next boundary; caller must hold ``_LOCK``."""
    job = _JOBS.get(job_id)
    if not job or job.get("status") != "running":
        return
    started = float(job.get("started_at") or 0.0)
    timeout = _job_timeout(job)
    if not started or now - started <= timeout:
        return
    spec = _KINDS.get(str(job.get("kind") or ""))
    message = (spec.timeout_message if spec and spec.timeout_message else "") or (
        f"Job timed out after {int(timeout)} seconds. "
        "Retry or check the LLM provider connection."
    )
    _request_stop_locked(job, "job_timeout", message)


def _watchdog_timeout(job_id: str) -> None:
    """Use the registered kind's actual deadline without relying on status polls."""
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return
        started_event = job.get("_started_event")
        finished_event = job.get("_finished_event")
        timeout = _job_timeout(job)
    if not isinstance(started_event, threading.Event) or not isinstance(
        finished_event, threading.Event
    ):
        return
    started_event.wait()
    if finished_event.wait(timeout):
        return
    with _LOCK:
        _mark_timeout_locked(job_id, time.time())


def _validate_suggest_refs_input(job_input: dict[str, Any]) -> dict[str, Any]:
    case_id = _clean(job_input.get("case_id"))
    if not case_id:
        raise JobInputError("empty_case_id", "Empty project case id.")
    return {"case_id": case_id}


_SUGGEST_STAGE_MESSAGES = {
    "collecting": "收集目标/任务/证据/资料/输出候选。",
    "suggesting": "AI 正在生成引用建议。",
}


def _run_project_suggest_refs(
    profile: str,
    job_input: dict[str, Any],
    report: Callable[..., None],
) -> dict[str, Any]:
    """Run the suggest-refs action; mirrors ``ProjectSuggestRefsResponse``."""
    case_id = job_input["case_id"]
    pdir = profile_io.profile_dir(profile)
    case = load_project_board(pdir).by_id().get(case_id)
    if case is None:
        raise JobFailedError(
            "project_case_not_found", f"Unknown project case: {case_id}"
        )

    def core_progress(stage: str) -> None:
        report(
            phase=_clean(stage) or "running",
            message=_SUGGEST_STAGE_MESSAGES.get(_clean(stage), ""),
        )

    try:
        result = project_suggest.suggest_case_refs(
            pdir, case, progress_callback=core_progress
        )
    except project_suggest.SuggestRefsError as exc:
        raise JobFailedError(exc.code, exc.message) from exc
    return {
        "ok": True,
        "backend": result.backend,
        "suggestions": result.suggestions,
        "rationale": result.rationale,
        "warnings": result.warnings,
    }


_KINDS[KIND_PROJECT_SUGGEST_REFS] = JobKind(
    name=KIND_PROJECT_SUGGEST_REFS,
    validate=_validate_suggest_refs_input,
    run=_run_project_suggest_refs,
    queued_message="Queued AI ref suggestion.",
)


def _validate_crystallize_input(job_input: dict[str, Any]) -> dict[str, Any]:
    raw_ids = job_input.get("task_ids")
    task_ids = [
        _clean(item) for item in (raw_ids if isinstance(raw_ids, list) else [])
    ]
    task_ids = [item for item in task_ids if item]
    raw_titles = job_input.get("titles")
    titles = [
        _clean(item) for item in (raw_titles if isinstance(raw_titles, list) else [])
    ]
    titles = [item for item in titles if item]
    if not task_ids and not titles:
        raise JobInputError(
            "empty_selection", "At least one Done task id is required."
        )
    return {"task_ids": task_ids, "titles": titles}


_CRYSTALLIZE_LLM_TIMEOUT_SECONDS = 90.0
_CRYSTALLIZE_JOB_TIMEOUT_SECONDS = 120.0


def _crystallize_friendly_error(err: str) -> str:
    """Map raw LLM failure strings to actionable Chinese copy."""
    text = _clean(err)
    lowered = text.lower()
    if "timed out" in lowered or "timeout" in lowered:
        return "AI 生成超时(90 秒);可重试,或改用规则草稿。"
    if (
        "ai_not_configured" in lowered
        or "not configured" in lowered
        or "ai features" in lowered
        or "llm not configured" in lowered
    ):
        return "未配置 LLM/AI 后端(请在设置页配置兼容 API 或 Codex);可改用规则草稿。"
    missing_source = re.search(r"evidence_entries\[(\d+)\]\.source_task_id is required", text)
    if missing_source:
        index = int(missing_source.group(1)) + 1
        return (
            f"AI 草稿第 {index} 条证据没标明来自哪个任务;"
            "选了多个任务时容易出现,可重试,或少选几个任务,或改用规则草稿。"
        )
    if any(
        marker in lowered
        for marker in (
            "could not parse",
            "json_error",
            "schema_error",
            "validation_error",
            "response did not contain",
        )
    ):
        return "AI 返回格式不符合结晶协议，无法解析;可重试,或改用规则草稿。"
    if any(marker in lowered for marker in ("provider_error", "backend_error")):
        detail = text.split(":", 1)[1].strip() if ":" in text else text
        return f"AI 后端调用失败:{detail};可重试,或改用规则草稿。"
    if text.startswith("LLM error:"):
        return f"AI 后端调用失败:{text.removeprefix('LLM error:').strip()};可重试,或改用规则草稿。"
    return f"AI 草稿失败:{text or '未知原因'};可改用规则草稿。"


def _run_evidence_crystallize(
    profile: str,
    job_input: dict[str, Any],
    report: Callable[..., None],
) -> dict[str, Any]:
    """LLM crystallize draft; result mirrors ``CrystallizeDraftResponse``."""
    from nblane.core import crystallize as crystallize_core
    from nblane.core.ai.gateway import crystallize_done_tasks
    from nblane.core.kanban_io import materialize_kanban_task_ids
    report(phase="resolving", message="解析 Done 任务。")
    pdir = profile_io.profile_dir(profile)
    # Ids are random until persisted; materialize so refs resolve later.
    materialize_kanban_task_ids(pdir)
    tasks, missing = crystallize_core.resolve_done_tasks(
        pdir, job_input["task_ids"], job_input["titles"]
    )
    if not tasks:
        raise JobFailedError(
            "empty_selection",
            "所选 Done 任务都找不到了(可能已归档);请刷新后重选。",
        )
    report(phase="drafting", message="AI 正在生成证据草稿(最长约 90 秒)。")
    ai_result = crystallize_done_tasks(
        profile,
        tasks,
        timeout_seconds=_CRYSTALLIZE_LLM_TIMEOUT_SECONDS,
    )
    if not ai_result.ok or not isinstance(ai_result.structured, dict):
        raise JobFailedError(
            "crystallize_draft_failed",
            _crystallize_friendly_error(ai_result.error or ""),
        )
    patch = ai_result.structured
    snapshots = [crystallize_core.task_snapshot(task) for task in tasks]
    patch = crystallize_core.attach_task_snapshots(patch, snapshots)
    return {
        "ok": True,
        "profile": profile,
        "backend": (
            "codex"
            if ai_result.backend == "local_codex_readonly"
            else "llm"
        ),
        "patch": patch,
        "tasks": [
            {
                "id": snap["task_id"],
                "title": snap["title"],
                "kanban_ref": snap["kanban_ref"],
                "project_id": snap["project_id"],
                "completed_on": snap["completed_on"],
            }
            for snap in snapshots
        ],
        "missing": list(missing),
    }


_KINDS[KIND_EVIDENCE_CRYSTALLIZE] = JobKind(
    name=KIND_EVIDENCE_CRYSTALLIZE,
    validate=_validate_crystallize_input,
    run=_run_evidence_crystallize,
    queued_message="Queued evidence crystallize draft.",
    timeout_seconds=_CRYSTALLIZE_JOB_TIMEOUT_SECONDS,
    timeout_message=(
        "AI 草稿超时(120 秒未完成);请重试,或改用规则草稿(立等可取)。"
    ),
)


# --- Content workspace AI (blog editor; candidates only, never writes posts) --


def _content_ai_call(fn: Callable[[], Any]) -> Any:
    """Map ``ContentAIError`` onto the job error contract."""
    try:
        return fn()
    except content_ai.ContentAIError as exc:
        raise JobFailedError(exc.code, exc.message, run_id=exc.run_id) from exc


def _validate_content_slug(job_input: dict[str, Any]) -> str:
    slug = _clean(job_input.get("slug"))
    if not slug:
        raise JobInputError("invalid_content_ai_request", "slug is required.")
    return slug


def _validate_content_rewrite_input(job_input: dict[str, Any]) -> dict[str, Any]:
    operation = _clean(job_input.get("operation")).lower()
    if operation not in content_ai.REWRITE_OPERATIONS:
        raise JobInputError(
            "invalid_content_ai_request",
            f"operation must be one of: {', '.join(content_ai.REWRITE_OPERATIONS)}.",
        )
    selection = str(job_input.get("selection") or "")
    if not selection.strip():
        raise JobInputError("invalid_content_ai_request", "请先选中要改写的文字。")
    if len(selection) > content_ai.SELECTION_MAX_CHARS:
        raise JobInputError(
            "invalid_content_ai_request",
            f"选中内容过长（上限 {content_ai.SELECTION_MAX_CHARS} 字），请分段改写。",
        )
    return {
        "operation": operation,
        "selection": selection,
        "title": _clean(job_input.get("title"))[:300],
        # content_ai windows this around the selection; cutting the head here
        # would drop the paragraphs after it.
        "context": str(job_input.get("context") or "")[:20_000],
        "instruction": _clean(job_input.get("instruction"))[:500],
    }


def _run_content_rewrite(profile: str, job_input: dict[str, Any], report: Callable[..., None]) -> Any:
    report(phase="generating", message="AI 正在改写选中内容。")
    return _content_ai_call(lambda: content_ai.rewrite_selection(**job_input, profile=profile))


def _validate_content_meta_input(job_input: dict[str, Any]) -> dict[str, Any]:
    body = str(job_input.get("body") or "")
    tags = job_input.get("tags") if isinstance(job_input.get("tags"), list) else []
    return {
        "title": _clean(job_input.get("title"))[:300],
        "summary": _clean(job_input.get("summary"))[:1000],
        "tags": [_clean(tag)[:40] for tag in tags if _clean(tag)][:12],
        "body": body[:200_000],
    }


def _run_content_meta(profile: str, job_input: dict[str, Any], report: Callable[..., None]) -> Any:
    report(phase="generating", message="AI 正在阅读全文并生成建议。")
    return _content_ai_call(lambda: content_ai.suggest_meta(**job_input, profile=profile))


def _validate_content_cover_input(job_input: dict[str, Any]) -> dict[str, Any]:
    slug = _validate_content_slug(job_input)
    tags = job_input.get("tags") if isinstance(job_input.get("tags"), list) else None
    try:
        reference = content_ai.validate_reference_image(job_input.get("reference_image"))
    except content_ai.ContentAIError as exc:
        raise JobInputError(exc.code, exc.message) from exc
    return {
        "slug": slug,
        "brief": _clean(job_input.get("brief"))[:500],
        "style": _clean(job_input.get("style"))[:200],
        "title": _clean(job_input.get("title"))[:300] if "title" in job_input else None,
        "summary": _clean(job_input.get("summary"))[:1000] if "summary" in job_input else None,
        "tags": [_clean(tag)[:40] for tag in tags if _clean(tag)][:12] if tags is not None else None,
        "body": str(job_input.get("body") or "")[:200_000] if "body" in job_input else None,
        "reference_image": reference,
    }


def _run_content_cover(
    profile: str,
    job_input: dict[str, Any],
    report: Callable[..., None],
    ctx: JobExecutionContext,
) -> Any:
    from nblane.core import public_site, visual_candidate_store, visual_generation

    report(phase="generating", message="正在生成封面（约 30–90 秒）。")
    slug = str(job_input["slug"])

    def generate():
        if not content_ai.cover_available():
            raise content_ai.ContentAIError(
                "cover_unavailable",
                "封面生成需要配置图像服务（VISUAL_API_KEY / DASHSCOPE_API_KEY）。",
            )
        post = public_site.load_blog_post(profile, slug)
        try:
            assets = content_ai.generate_images(
                profile,
                "cover",
                _clean(job_input.get("brief")),
                style=_clean(job_input.get("style")),
                title=post.title if job_input.get("title") is None else _clean(job_input.get("title")),
                summary=post.summary if job_input.get("summary") is None else _clean(job_input.get("summary")),
                tags=(
                    [str(item) for item in (post.meta.get("tags") or [])]
                    if job_input.get("tags") is None
                    else list(job_input["tags"])
                ),
                body=post.body if job_input.get("body") is None else str(job_input.get("body") or ""),
                reference_image=_clean(job_input.get("reference_image")),
            )
        except visual_generation.VisualGenerationError as exc:
            raise content_ai.ContentAIError(
                "cover_generation_failed",
                str(exc),
                run_id=str(getattr(exc, "run_id", "") or ""),
            ) from exc
        return post, assets

    ctx.checkpoint()
    post, assets = _content_ai_call(generate)
    ctx.checkpoint()
    if not assets:
        raise JobFailedError("cover_generation_failed", "图像服务没有返回图片，请重试。")

    def commit() -> list[dict[str, Any]]:
        patch_id = f"cover-{uuid.uuid4().hex[:10]}"
        rows: list[dict[str, Any]] = []
        for asset in assets:
            candidate = visual_candidate_store.write_candidate(
                profile,
                post.slug,
                patch_id,
                data=asset.data,
                filename=visual_generation.generated_filename("cover", asset.data, asset.extension),
                kind="image",
                alt=post.title,
                provider=asset.provider,
                model=asset.model,
                prompt=asset.prompt.positive_prompt,
            )
            rows.append(
                {
                    "candidate_path": candidate.relative_path,
                    "filename": candidate.filename,
                    "provider": asset.provider,
                    "model": asset.model,
                }
            )
        return rows

    rows = ctx.apply(commit, summary="保存封面候选")
    return {"slug": slug, "candidates": rows}


def _validate_content_social_input(job_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": _clean(job_input.get("title"))[:300],
        "body": str(job_input.get("body") or "")[:200_000],
    }


def _run_content_social(profile: str, job_input: dict[str, Any], report: Callable[..., None]) -> Any:
    report(phase="generating", message="AI 正在读全文并写分享文案。")
    return _content_ai_call(lambda: content_ai.suggest_social_copy(**job_input, profile=profile))


_KINDS[KIND_CONTENT_REWRITE] = JobKind(
    name=KIND_CONTENT_REWRITE,
    validate=_validate_content_rewrite_input,
    run=_run_content_rewrite,
    queued_message="Queued selection rewrite.",
    # Expand runs with thinking on; content_ai.REWRITE_LLM_TIMEOUT_SECONDS
    # (135s) must stay below this.
    timeout_seconds=150,
    timeout_message="AI 改写超时（150 秒），请重试或缩短选中内容。",
)

_KINDS[KIND_CONTENT_META] = JobKind(
    name=KIND_CONTENT_META,
    validate=_validate_content_meta_input,
    run=_run_content_meta,
    queued_message="Queued title/summary suggestions.",
    timeout_seconds=120,
    timeout_message="AI 建议超时（120 秒），请重试。",
)

_KINDS[KIND_CONTENT_SOCIAL] = JobKind(
    name=KIND_CONTENT_SOCIAL,
    validate=_validate_content_social_input,
    run=_run_content_social,
    queued_message="Queued share copy suggestions.",
    timeout_seconds=150,
    timeout_message="AI 文案超时（150 秒），请重试。",
)

_KINDS[KIND_CONTENT_COVER] = JobKind(
    name=KIND_CONTENT_COVER,
    validate=_validate_content_cover_input,
    run=_run_content_cover,
    queued_message="Queued cover generation.",
    timeout_seconds=300,
    timeout_message="封面生成超时（5 分钟），请重试。",
)


def _validate_content_image_input(raw: dict[str, Any]) -> dict[str, Any]:
    mode = _clean(raw.get("mode"))
    instruction = _clean(raw.get("instruction"))
    reference = _clean(raw.get("reference"))
    if mode not in {"cover", "edit"}:
        raise JobInputError("invalid_image_request", "请选择生成封面或修改图片。")
    if len(instruction) > 4000 or (mode == "edit" and (not instruction or not reference)):
        raise JobInputError("invalid_image_request", "请选择原图并填写修改要求（最多 4000 字）。")
    if reference and (len(reference) > 500 or not reference.startswith(("media/", "blog/.candidates/"))):
        raise JobInputError("invalid_image_request", "请使用媒体库图片或上传参考图。")
    quality = _clean(raw.get("quality")) or "standard"
    aspect = _clean(raw.get("aspect")) or ("original" if mode == "edit" else "16:9")
    if quality not in {"standard", "high", "ultra"} or aspect not in {"original", "16:9", "1:1", "4:3", "3:4", "9:16"}:
        raise JobInputError("invalid_image_request", "请选择有效的清晰度和比例。")
    target = raw.get("target") or {}
    if not isinstance(target, dict) or target.get("kind", "media") not in {"block", "cover", "media"}:
        raise JobInputError("invalid_image_request", "无效的图片应用位置。")
    target = {key: _clean(target.get(key)) for key in ("kind", "block_id", "source", "fingerprint")}
    if any(len(value) > 10000 for value in target.values()):
        raise JobInputError("invalid_image_request", "图片属性过长，请从媒体库选择参考图。")
    target["kind"] = target["kind"] or "media"
    return {
        "slug": _validate_content_slug(raw), "mode": mode,
        "instruction": instruction, "reference": reference, "target": target,
        "quality": quality, "aspect": aspect,
        **_validate_content_meta_input(raw),
    }


def _run_content_image(
    profile: str,
    job_input: dict[str, Any],
    report: Callable[..., None],
    ctx: JobExecutionContext,
) -> Any:
    import base64

    from nblane.core import content_images, public_site, visual_candidate_store, visual_generation

    report(phase="generating", message="正在生成图片，关闭面板不影响任务。")
    post = public_site.load_blog_post(profile, job_input["slug"])
    row: dict[str, Any] = {
        "id": f"image-{uuid.uuid4().hex}",
        "slug": post.slug,
        "request": job_input.copy(),
        "status": "running",
        "created_at": time.time(),
        "process_id": content_images.PROCESS_ID,
        "candidates": [],
        "error": "",
        "reference": "",
    }
    assets = []
    reference_data = b""
    reference_mime = ""
    reference_data_url = ""
    try:
        if not content_ai.cover_available():
            raise ValueError("未配置图像服务。")
        dimensions = content_images.output_size(profile, job_input)
        row["output_size"] = dimensions["size"]
        source = str(job_input.get("reference") or "")
        if source:
            reference_data = content_images.reference_bytes(profile, post.slug, source)
            reference_mime, _ = content_images.image_info(reference_data)
            reference_data_url = (
                f"data:{reference_mime};base64,"
                + base64.b64encode(reference_data).decode("ascii")
            )
        if job_input["mode"] == "edit" and not reference_data_url:
            raise ValueError("请先选择要修改的图片。")
        ctx.checkpoint()
        assets = content_ai.generate_images(
            profile,
            "image_edit" if job_input["mode"] == "edit" else "cover",
            job_input["instruction"],
            reference_image=reference_data_url,
            size=dimensions["size"],
            title=job_input.get("title", ""),
            summary=job_input.get("summary", ""),
            tags=job_input.get("tags", []),
            body=job_input.get("body", ""),
        )
        ctx.checkpoint()
        if not assets:
            raise ValueError("图像服务没有返回图片，请重试。")
        for asset in assets:
            content_images.image_info(asset.data)
        row["status"] = "done"
    except JobCancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 - image runs report their own error row
        row["status"] = "failed"
        row["error"] = str(exc)

    def commit() -> dict[str, Any]:
        if reference_data:
            snapshot = visual_candidate_store.write_candidate(
                profile,
                post.slug,
                row["id"] + "-ref",
                data=reference_data,
                filename=f"reference.{reference_mime.split('/')[1]}",
                kind="reference",
            )
            row["reference"] = snapshot.relative_path
        for asset in assets:
            candidate = visual_candidate_store.write_candidate(
                profile,
                post.slug,
                row["id"],
                data=asset.data,
                filename=visual_generation.generated_filename(
                    "edited" if job_input["mode"] == "edit" else "cover",
                    asset.data,
                    asset.extension,
                ),
                kind="image",
                provider=asset.provider,
                model=asset.model,
                prompt=asset.prompt.positive_prompt,
            )
            row["candidates"].append(
                {
                    "candidate_path": candidate.relative_path,
                    "filename": candidate.filename,
                    "applied_path": "",
                }
            )
        content_images._write(profile, row)
        return row

    result = ctx.apply(commit, summary="保存图片候选")
    ctx.checkpoint()
    return result


_KINDS["content-image"] = JobKind(
    name="content-image", validate=_validate_content_image_input, run=_run_content_image,
    queued_message="Queued image generation.", timeout_seconds=360,
    timeout_message="图片生成超时，请检查候选列表后重试。",
)


# --- Career workspace AI -------------------------------------------------------
#
# Inputs: resume + JD + the user's notes, plus the evidence pool as an
# optional fact source. Results are candidates; nothing is written here.

_CAREER_TEXT_MAX = 50_000


def _career_ai_call(fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except career_ai.CareerAIError as exc:
        raise JobFailedError(exc.code, exc.message, run_id=exc.run_id) from exc


def _validate_career_pair(job_input: dict[str, Any]) -> dict[str, Any]:
    resume_md = str(job_input.get("resume_md") or "").strip()
    jd_text = str(job_input.get("jd_text") or "").strip()
    if not resume_md or not jd_text:
        raise JobInputError("invalid_career_match_request", "简历和 JD 都不能为空。")
    if len(resume_md) > _CAREER_TEXT_MAX or len(jd_text) > _CAREER_TEXT_MAX:
        raise JobInputError("invalid_career_match_request", f"简历和 JD 各不超过 {_CAREER_TEXT_MAX} 字。")
    return {
        "resume_md": resume_md,
        "jd_text": jd_text,
        "notes": str(job_input.get("notes") or "")[:5000],
        "use_evidence": job_input.get("use_evidence", True) is not False,
    }


def _run_career_match(profile: str, job_input: dict[str, Any], report: Callable[..., None]) -> Any:
    report(phase="generating", message="AI 正在逐条比对 JD 要求。")
    return _career_ai_call(lambda: career_ai.analyze_match(profile, **job_input))


def _validate_career_tailor_input(job_input: dict[str, Any]) -> dict[str, Any]:
    clean = _validate_career_pair(job_input)
    analysis = job_input.get("analysis")
    clean["analysis"] = analysis if isinstance(analysis, dict) else None
    clean["current_draft"] = str(job_input.get("current_draft") or "")[:_CAREER_TEXT_MAX]
    return clean


def _run_career_tailor(profile: str, job_input: dict[str, Any], report: Callable[..., None]) -> Any:
    report(phase="generating", message="AI 正在生成定制简历。")
    return _career_ai_call(lambda: career_ai.tailor_resume(profile, **job_input))


def _validate_career_structure_input(job_input: dict[str, Any]) -> dict[str, Any]:
    text = str(job_input.get("text") or "").strip()
    if not text:
        raise JobInputError("invalid_import", "简历文本为空。")
    return {"text": text[:_CAREER_TEXT_MAX]}


def _run_career_structure(profile: str, job_input: dict[str, Any], report: Callable[..., None]) -> Any:
    report(phase="generating", message="AI 正在识别简历字段。")
    resume = _career_ai_call(lambda: career_ai.structure_resume(profile, job_input["text"]))
    return {"resume": resume}


_KINDS[KIND_CAREER_MATCH] = JobKind(
    name=KIND_CAREER_MATCH,
    validate=_validate_career_pair,
    run=_run_career_match,
    queued_message="Queued JD match.",
    timeout_seconds=180,
    timeout_message="JD 匹配超时（3 分钟），请重试。",
)

_KINDS[KIND_CAREER_TAILOR] = JobKind(
    name=KIND_CAREER_TAILOR,
    validate=_validate_career_tailor_input,
    run=_run_career_tailor,
    queued_message="Queued tailored resume.",
    timeout_seconds=240,
    timeout_message="定制简历生成超时（4 分钟），请重试。",
)

_KINDS[KIND_CAREER_STRUCTURE] = JobKind(
    name=KIND_CAREER_STRUCTURE,
    validate=_validate_career_structure_input,
    run=_run_career_structure,
    queued_message="Queued resume field recognition.",
    timeout_seconds=180,
    timeout_message="简历识别超时（3 分钟），请重试。",
)
