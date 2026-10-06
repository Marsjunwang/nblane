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
router), ``studio-jd-match`` (Output Studio JD match analysis),
``project-suggest-refs`` (Project Board AI ref suggestion) and
``evidence-crystallize`` (LLM Done-task -> evidence draft). Records are
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
from pathlib import Path
from typing import Any

from nblane.core import content_ai, gap
from nblane.core import career_ai, jd_match
from nblane.core import llm as llm_client
from nblane.core import profile_io, project_suggest
from nblane.core.project_board import load_project_board

KIND_GAP_ANALYSIS = "gap-analysis"
KIND_STUDIO_JD_MATCH = "studio-jd-match"
KIND_PROJECT_SUGGEST_REFS = "project-suggest-refs"
KIND_EVIDENCE_CRYSTALLIZE = "evidence-crystallize"
KIND_CONTENT_REWRITE = "content-rewrite"
KIND_CONTENT_META = "content-meta"
KIND_CONTENT_COVER = "content-cover"
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
    """One registered async-job kind.

    ``timeout_seconds`` overrides the global watchdog for kinds whose work
    is known to be short (e.g. a single LLM call the user is waiting on in
    a wizard); 0/None falls back to ``_JOB_TIMEOUT_SECONDS``.
    """

    name: str
    validate: Callable[[dict[str, Any]], dict[str, Any]]
    run: Callable[[str, dict[str, Any], Callable[..., None]], Any]
    queued_message: str = "Queued job."
    timeout_seconds: float = 0.0
    timeout_message: str = ""


_KINDS: dict[str, JobKind] = {}


def register_kind(spec: JobKind) -> None:
    """Register (or replace) one job kind from another router module."""
    _KINDS[spec.name] = spec


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
        ]
    rows.sort(key=lambda item: float(item.get("finished_at") or item.get("created_at") or 0), reverse=True)
    return rows[: max(1, min(int(limit), 200))]


def create_job(
    profile: str,
    kind: str,
    job_input: dict[str, Any],
    *,
    profile_scope: str | Path | None = None,
) -> dict[str, Any]:
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
        # Keep the data-root identity internal. Profile names are not globally
        # unique across test/dev roots, while the worker payload still uses
        # the public profile name expected by existing runners.
        "_profile_scope": _scope_key(profile_scope),
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


def _job_timeout(job: dict[str, Any]) -> float:
    """Effective timeout for a job: kind override, else the global default."""
    spec = _KINDS.get(str(job.get("kind") or ""))
    if spec and spec.timeout_seconds and spec.timeout_seconds > 0:
        return float(spec.timeout_seconds)
    return float(_JOB_TIMEOUT_SECONDS)


def _mark_timeout_locked(job_id: str, now: float) -> None:
    """Mark a stale running job failed; caller must hold ``_LOCK``."""
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
        raise JobFailedError(exc.code, exc.message) from exc


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
        "context": str(job_input.get("context") or "")[:4000],
        "instruction": _clean(job_input.get("instruction"))[:500],
    }


def _run_content_rewrite(profile: str, job_input: dict[str, Any], report: Callable[..., None]) -> Any:
    report(phase="generating", message="AI 正在改写选中内容。")
    return _content_ai_call(lambda: content_ai.rewrite_selection(**job_input))


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
    return _content_ai_call(lambda: content_ai.suggest_meta(**job_input))


def _validate_content_cover_input(job_input: dict[str, Any]) -> dict[str, Any]:
    slug = _validate_content_slug(job_input)
    tags = job_input.get("tags") if isinstance(job_input.get("tags"), list) else None
    return {
        "slug": slug,
        "brief": _clean(job_input.get("brief"))[:500],
        "style": _clean(job_input.get("style"))[:200],
        "title": _clean(job_input.get("title"))[:300] if "title" in job_input else None,
        "summary": _clean(job_input.get("summary"))[:1000] if "summary" in job_input else None,
        "tags": [_clean(tag)[:40] for tag in tags if _clean(tag)][:12] if tags is not None else None,
        "body": str(job_input.get("body") or "")[:200_000] if "body" in job_input else None,
    }


def _run_content_cover(profile: str, job_input: dict[str, Any], report: Callable[..., None]) -> Any:
    report(phase="generating", message="正在生成封面（约 30–90 秒）。")
    slug = job_input.pop("slug")
    rows = _content_ai_call(
        lambda: content_ai.generate_cover_candidates(profile, slug, **job_input)
    )
    return {"slug": slug, "candidates": rows}


_KINDS[KIND_CONTENT_REWRITE] = JobKind(
    name=KIND_CONTENT_REWRITE,
    validate=_validate_content_rewrite_input,
    run=_run_content_rewrite,
    queued_message="Queued selection rewrite.",
    timeout_seconds=120,
    timeout_message="AI 改写超时（120 秒），请重试或缩短选中内容。",
)

_KINDS[KIND_CONTENT_META] = JobKind(
    name=KIND_CONTENT_META,
    validate=_validate_content_meta_input,
    run=_run_content_meta,
    queued_message="Queued title/summary suggestions.",
    timeout_seconds=120,
    timeout_message="AI 建议超时（120 秒），请重试。",
)

_KINDS[KIND_CONTENT_COVER] = JobKind(
    name=KIND_CONTENT_COVER,
    validate=_validate_content_cover_input,
    run=_run_content_cover,
    queued_message="Queued cover generation.",
    timeout_seconds=300,
    timeout_message="封面生成超时（5 分钟），请重试。",
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
        raise JobFailedError(exc.code, exc.message) from exc


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
