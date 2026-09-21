"""In-process async-job registry for the SPA backend (LLM long tasks).

Mirrors the ``web_reader_api`` paper-library search-job design — an
in-memory dict guarded by a lock, a daemon worker thread per job, and a
seq-numbered event log replayed over SSE — so the single-worker uvicorn
process can run blocking LLM work (up to ~55s) off the request thread.

Contract:

- Statuses: ``queued`` -> ``running`` -> ``done`` | ``failed``
  (``FINAL_STATUSES``). A watchdog marks stale running jobs failed after
  ``NBLANE_WEB_API_JOB_TIMEOUT_SECONDS`` (default 600s).
- SSE frames (``GET .../jobs/{id}/stream``): ``job`` (initial snapshot,
  replay-safe for late subscribers), ``progress`` (one per logged phase
  event), ``done`` (terminal, carries ``result``), ``error`` (terminal,
  carries the structured ``{code, message}`` error).
- Job kinds register a validator (raw ``input`` dict -> cleaned input,
  raising :class:`JobInputError`) and a runner
  ``run(profile, input, report) -> result``; ``report(phase, message)``
  appends a progress event and updates the job's phase/message.

Registered kinds: ``gap-analysis`` (Gap deep analysis with the LLM
router), ``studio-jd-match`` (Output Studio JD match analysis) and
``project-suggest-refs`` (Project Board AI ref suggestion). Records are
process-local by design (single worker); results live only in memory and
are pruned after ``_JOB_TTL_SECONDS``.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from nblane.core import gap
from nblane.core import jd_match
from nblane.core import llm as llm_client
from nblane.core import profile_io, project_suggest
from nblane.core.project_board import load_project_board

KIND_GAP_ANALYSIS = "gap-analysis"
KIND_STUDIO_JD_MATCH = "studio-jd-match"
KIND_PROJECT_SUGGEST_REFS = "project-suggest-refs"

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


class JobInputError(ValueError):
    """Raised when a kind validator rejects the raw job input."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class JobFailedError(RuntimeError):
    """Structured job failure raised by runners; becomes the job error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class JobKind:
    """One registered async-job kind."""

    name: str
    validate: Callable[[dict[str, Any]], dict[str, Any]]
    run: Callable[[str, dict[str, Any], Callable[..., None]], Any]
    queued_message: str = "Queued job."


_KINDS: dict[str, JobKind] = {}


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


def create_job(profile: str, kind: str, job_input: dict[str, Any]) -> dict[str, Any]:
    """Validate, register, and start a job; return its initial snapshot.

    The worker runs in a daemon thread. Raises :class:`UnknownJobKindError`
    for unregistered kinds and :class:`JobInputError` for rejected input.
    """
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
    job: dict[str, Any] = {
        "job_id": job_id,
        "profile": _clean(profile),
        "kind": clean_kind,
        "status": "queued",
        "phase": "queued",
        "message": spec.queued_message,
        "created_at": now,
        "started_at": 0.0,
        "finished_at": 0.0,
        "error": None,
        "result": None,
        "events": [],
        "_event_seq": 0,
        "_started_monotonic": 0.0,
        "_finished_monotonic": 0.0,
    }
    with _LOCK:
        _JOBS[job_id] = job
    # Snapshot before the worker starts so the 202 answer deterministically
    # reports the queued state (the SSE stream re-reads live state anyway).
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
        report = _progress_reporter(job_id)
        try:
            result = spec.run(_clean(profile), clean_input, report)
        except JobFailedError as exc:
            _update_job(
                job_id,
                status="failed",
                phase="failed",
                message=exc.message,
                error={"code": exc.code, "message": exc.message},
                finished_at=time.time(),
                _finished_monotonic=time.monotonic(),
            )
            return
        except Exception as exc:  # noqa: BLE001 - surface any runner failure
            _update_job(
                job_id,
                status="failed",
                phase="failed",
                message=str(exc),
                error={"code": "job_failed", "message": str(exc)},
                finished_at=time.time(),
                _finished_monotonic=time.monotonic(),
            )
            return
        # A watchdog may have marked the job failed while the runner blocked;
        # the late result then loses so the stream stays terminal-consistent.
        with _LOCK:
            current = _JOBS.get(job_id)
            if not current or current.get("status") in FINAL_STATUSES:
                return
        _update_job(
            job_id,
            status="done",
            phase="done",
            message=f"{clean_kind} job finished.",
            result=result,
            finished_at=time.time(),
            _finished_monotonic=time.monotonic(),
        )

    threading.Thread(
        target=worker, name=f"web-api-job-{job_id}", daemon=True
    ).start()
    threading.Thread(
        target=_watchdog_timeout,
        args=(job_id,),
        name=f"web-api-job-timeout-{job_id}",
        daemon=True,
    ).start()
    return initial


def _prune_jobs() -> None:
    cutoff = time.time() - _JOB_TTL_SECONDS
    with _LOCK:
        stale = [
            job_id
            for job_id, job in _JOBS.items()
            if float(job.get("created_at") or 0) < cutoff
        ]
        for job_id in stale:
            _JOBS.pop(job_id, None)


def _mark_timeout_locked(job_id: str, now: float) -> None:
    """Mark a stale running job failed; caller must hold ``_LOCK``."""
    job = _JOBS.get(job_id)
    if not job or job.get("status") != "running":
        return
    started = float(job.get("started_at") or 0.0)
    if not started or now - started <= _JOB_TIMEOUT_SECONDS:
        return
    message = (
        f"Job timed out after {_JOB_TIMEOUT_SECONDS} seconds. "
        "Retry or check the LLM provider connection."
    )
    job["status"] = "failed"
    job["phase"] = "failed"
    job["message"] = message
    job["error"] = {"code": "job_timeout", "message": message}
    job["finished_at"] = now
    job["_finished_monotonic"] = time.monotonic()


def _watchdog_timeout(job_id: str) -> None:
    """Mark a hung running job failed even if nobody polls it."""
    time.sleep(_JOB_TIMEOUT_SECONDS)
    with _LOCK:
        _mark_timeout_locked(job_id, time.time())


def _validate_gap_analysis_input(job_input: dict[str, Any]) -> dict[str, Any]:
    task = _clean(job_input.get("task"))
    if not task:
        raise JobInputError("empty_task", "Empty task text.")
    if len(task) > 2000:
        raise JobInputError(
            "invalid_job_input", "Task text is too long (max 2000 characters)."
        )
    return {"task": task}


_GAP_STAGE_MESSAGES = {
    "routing": "LLM is routing the task to skill nodes.",
    "merging": "Merging rule and LLM matches; building the requires closure.",
}


def _run_gap_analysis(
    profile: str,
    job_input: dict[str, Any],
    report: Callable[..., None],
) -> dict[str, Any]:
    """Run the rule + LLM gap analysis; return the response projection."""

    def core_progress(stage: str) -> None:
        report(
            phase=_clean(stage) or "running",
            message=_GAP_STAGE_MESSAGES.get(_clean(stage), ""),
        )

    result = gap.analyze(
        profile,
        job_input["task"],
        use_llm_router=True,
        progress_callback=core_progress,
    )
    if result.error:
        raise JobFailedError(
            result.error_key or "gap_analysis_failed", result.error
        )
    return build_gap_analysis_payload(profile, result, analysis_mode="rule+llm")


def build_gap_analysis_payload(
    profile: str, result: gap.GapResult, *, analysis_mode: str
) -> dict[str, Any]:
    """Project a ``GapResult`` into the ``GapAnalysisResponse`` payload.

    Shared by the sync rule-only endpoint and the async LLM job so both
    surfaces return the identical shape (``analysis_mode`` records which
    matchers ran; ``llm_router_error`` carries the degradation reason when
    the LLM router failed but rule roots still produced an analysis).
    """
    closure = list(result.closure)
    coverage = round(1 - len(result.gaps) / len(closure), 4) if closure else 0.0
    return {
        "profile": profile,
        "task": result.task,
        "top_matches": list(result.top_matches),
        "closure": closure,
        "gaps": list(result.gaps),
        "strong": list(result.strong),
        "can_solve": result.can_solve,
        "coverage": coverage,
        "next_steps": list(result.next_steps),
        "roots_from_rule": list(result.roots_from_rule),
        "roots_from_llm": list(result.roots_from_llm),
        "learned_merged": result.learned_merged,
        "analysis_mode": analysis_mode,
        "llm_router_error": result.llm_router_error,
    }


_KINDS[KIND_GAP_ANALYSIS] = JobKind(
    name=KIND_GAP_ANALYSIS,
    validate=_validate_gap_analysis_input,
    run=_run_gap_analysis,
    queued_message="Queued gap deep analysis.",
)


_JD_MATCH_TEXT_MAX = 50_000

# Same unavailability contract as the sync studio/jd-match endpoint (422),
# surfaced here as the job's structured error so the SPA renders the same
# degradation card from the SSE error frame.
_JD_MATCH_UNAVAILABLE_MESSAGE = (
    "JD match analysis requires a configured LLM backend "
    "(set LLM_API_KEY / LLM_BASE_URL); the rest of the studio "
    "works without it."
)


def _validate_jd_match_input(job_input: dict[str, Any]) -> dict[str, Any]:
    resume_md = _clean(job_input.get("resume_md"))
    jd_text = _clean(job_input.get("jd_text"))
    if not resume_md or not jd_text:
        raise JobInputError(
            "invalid_jd_match_request", "Both resume_md and jd_text are required."
        )
    if len(resume_md) > _JD_MATCH_TEXT_MAX or len(jd_text) > _JD_MATCH_TEXT_MAX:
        raise JobInputError(
            "invalid_jd_match_request",
            f"resume_md and jd_text are capped at {_JD_MATCH_TEXT_MAX} characters.",
        )
    return {"resume_md": resume_md, "jd_text": jd_text}


def _run_studio_jd_match(
    profile: str,
    job_input: dict[str, Any],
    report: Callable[..., None],
) -> dict[str, Any]:
    """Run the JD match analysis; the result mirrors ``StudioJdMatchResponse``."""
    if not llm_client.is_configured():
        raise JobFailedError("studio_jd_match_unavailable", _JD_MATCH_UNAVAILABLE_MESSAGE)
    report(phase="analyzing", message="分析中:汇总档案证据与简历上下文。")
    # Real file-IO stage (evidence/claims/skills/SKILL.md); also warms the
    # memoized context cache analyze_jd reuses, so nothing is read twice.
    jd_match.gather_profile_context(profile)
    report(phase="generating", message="生成中:LLM 正在撰写匹配分析。")
    analysis = jd_match.analyze_jd(
        profile,
        resume_md=job_input["resume_md"],
        jd_text=job_input["jd_text"],
    )
    # core.llm returns an error string instead of raising — same failure
    # detection as the sync endpoint.
    if analysis.startswith(("LLM error:", "AI features")):
        raise JobFailedError("studio_jd_match_failed", analysis)
    return {"ok": True, "analysis": analysis}


_KINDS[KIND_STUDIO_JD_MATCH] = JobKind(
    name=KIND_STUDIO_JD_MATCH,
    validate=_validate_jd_match_input,
    run=_run_studio_jd_match,
    queued_message="Queued JD match analysis.",
)


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
