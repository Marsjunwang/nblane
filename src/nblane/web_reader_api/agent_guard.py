"""Agent policy guard for Paper Library and Reader sidecar mutations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import Request
from starlette.concurrency import run_in_threadpool
from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse, Response

from nblane.core import agent_journal, agent_ops, agent_policy, reader_ops


MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
JOB_RESERVATION_SCOPE = "nblane.reader_agent_job_reservation"
SYNC_WRITE_SCOPE = "nblane.reader_agent_sync_write"
P = "/api/research/{profile}"
R = "/reader/api/{source_id}"
_AUTH_ROUTES = frozenset({"/auth/session", "/auth/logout"})
_EVENT = "dynamic:paper-library-event"
_TASK = "dynamic:reader-task"
_ANNOTATION = "dynamic:reader-annotation"
_TRANSLATE = "dynamic:reader-translate"
_GENERIC = "dynamic:reader-generic"

# Every mutating Reader route is listed, including the two auth exemptions.
ROUTE_ACTIONS: dict[tuple[str, str], str] = {
    ("POST", "/auth/session"): "reader.auth",
    ("POST", "/auth/logout"): "reader.auth",
    ("POST", f"{P}/paper-library/events"): _EVENT,
    ("POST", f"{P}/paper-library/events/jobs"): _EVENT,
    ("POST", f"{P}/paper-library/events/jobs/{{job_id}}/cancel"): "reader.job.control",
    ("POST", f"{P}/paper-library/search"): "reader.search",
    ("POST", f"{P}/paper-library/search/jobs"): "reader.search",
    ("POST", f"{P}/paper-library/search/jobs/{{job_id}}/cancel"): "reader.job.control",
    ("POST", f"{P}/paper-library/import"): "research.import",
    ("POST", f"{P}/paper-library/import-url"): "research.import",
    ("POST", f"{P}/papers/{{source_id}}/pdf-retry"): "reader.pdf.save",
    ("POST", f"{P}/paper-library/export"): "reader.citation.export",
    ("POST", f"{P}/papers/{{source_id}}/reader-token"): "reader.token",
    ("POST", f"{P}/paper-library/upload"): "reader.pdf.save",
    ("POST", f"{P}/papers/{{source_id}}/pdf-upload"): "reader.pdf.save",
    ("POST", f"{R}/tasks"): _TASK,
    ("DELETE", f"{R}/tasks/{{task_id}}"): "reader.job.control",
    ("POST", f"{R}/annotation"): _ANNOTATION,
    ("DELETE", f"{R}/annotation/{{annotation_id}}"): "reader.annotation.delete",
    ("POST", f"{R}/translate"): _TRANSLATE,
    ("POST", f"{R}/explain"): "reader.ai.explain",
    ("POST", f"{R}/ask"): "reader.ai.ask",
    ("POST", f"{R}/chunk"): "reader.chunk.create",
    ("POST", f"{R}/citation"): "reader.citation.create",
    ("POST", f"{R}/progress"): "reader.progress",
    ("POST", f"{R}/review"): "reader.analysis",
    ("POST", f"{R}/analyze"): "reader.analysis",
    ("POST", f"{R}/action/{{action}}"): _GENERIC,
}
ASYNC_JOB_TEMPLATES = frozenset({
    f"{P}/paper-library/events/jobs",
    f"{R}/tasks",
})


class ReaderAgentError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        confirmation: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.confirmation = confirmation


async def reader_agent_error_handler(_request: Request, exc: ReaderAgentError) -> JSONResponse:
    content: dict[str, Any] = {"code": exc.code, "message": exc.message}
    if exc.confirmation is not None:
        content["confirmation"] = exc.confirmation
    return JSONResponse(content, status_code=exc.status_code)


async def _read_body(request: Request) -> Any:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type or "x-www-form-urlencoded" in content_type:
        form = await request.form()
        return {
            key: str(getattr(value, "filename", "") or value)
            for key, value in form.items()
        }
    raw = await request.body()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return raw.decode("utf-8", errors="replace")


def action_for(
    method: str,
    template: str,
    path_params: dict[str, Any],
    body: Any,
) -> str:
    mapped = ROUTE_ACTIONS.get((method, template), "reader.unsupported")
    data = body if isinstance(body, dict) else {}
    if mapped == _EVENT:
        return agent_policy.paper_library_event_action(data)
    if mapped == _TASK:
        raw = str(data.get("action") or "").strip()
        return agent_policy.READER_ACTIONS.get(raw, "reader.unsupported")
    if mapped == _ANNOTATION:
        raw = str(data.get("action") or "").strip()
        if not raw:
            raw = "annotation_update" if data.get("annotation_id") or data.get("id") else "annotation_create"
        return agent_policy.READER_ACTIONS.get(raw, "reader.unsupported")
    if mapped == _TRANSLATE:
        raw = str(data.get("action") or "translate_selection").strip()
        return agent_policy.READER_ACTIONS.get(raw, "reader.unsupported")
    if mapped == _GENERIC:
        raw = str(path_params.get("action") or "").strip()
        return agent_policy.READER_ACTIONS.get(raw, "reader.unsupported")
    return mapped


def _payload(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {}
    nested = body.get("payload")
    return nested if isinstance(nested, dict) else body


def _batch_count(body: Any) -> int:
    data = _payload(body)
    keys = (
        "paper_ids",
        "source_ids",
        "selected_ids",
        "candidate_ids",
        "ids",
        "items",
        "segment_refs",
        "segment_ids",
        "scope_refs",
        "visible_pages",
    )
    sizes = [len(data[key]) for key in keys if isinstance(data.get(key), list)]
    return max([1, *sizes])


def _source_ids(body: Any, path_params: dict[str, Any], pdir: Path, action: str) -> list[str]:
    data = _payload(body)
    values: list[str] = []
    direct = path_params.get("source_id")
    if direct:
        values.append(str(direct))
    for key in ("paper_ids", "source_ids", "source_id"):
        value = data.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif value:
            values.append(str(value))
    if isinstance(body, dict) and isinstance(body.get("candidates"), list):
        values.extend(
            str(item.get("imported_source_id"))
            for item in body["candidates"]
            if isinstance(item, dict) and item.get("imported_source_id")
        )
    if action == "reader.paper.purge" and not values:
        from nblane.core.research_sources import load_research_sources

        values.extend(
            source.id
            for source in load_research_sources(pdir).sources
            if source.kind == "paper" and source.status == "discarded"
        )
    return list(dict.fromkeys(value for value in values if value))


def _file(relative: str) -> str:
    return agent_journal.file_kind(relative)


def _jsonl(relative: str) -> str:
    return agent_journal.jsonl_kind(relative)


def _asset(ref: str) -> str:
    return agent_journal.asset_kind(ref)


def _asset_kinds(pdir: Path, source_ids: list[str]) -> tuple[str, ...]:
    if not source_ids:
        return ()
    from nblane.core.research_sources import load_research_sources

    wanted = set(source_ids)
    refs = [
        str((source.metadata or {}).get("pdf_asset_ref") or "").strip()
        for source in load_research_sources(pdir).sources
        if source.id in wanted
    ]
    return tuple(_asset(ref) for ref in dict.fromkeys(refs) if ref)


def _artifact_kinds(source_id: str, *, source: bool = True) -> tuple[str, ...]:
    from nblane.core.research_workspace import source_slug

    slug = source_slug(source_id)
    kinds = [
        _jsonl(f"research/paper-pages/{slug}.jsonl"),
        _jsonl(f"research/paper-segments/{slug}.jsonl"),
        _jsonl(f"research/paper-structure/{slug}.jsonl"),
        _jsonl(f"research/annotations/{slug}.jsonl"),
        _jsonl(f"research/translations/{slug}.jsonl"),
        _jsonl(f"research/chunks/{slug}.jsonl"),
        _file(f"research/analysis/{slug}.yaml"),
        _file(f"research/notes/{slug}.md"),
    ]
    return (("research_source",) if source else ()) + tuple(kinds)


def journal_kinds(
    action: str,
    pdir: Path,
    body: Any,
    path_params: dict[str, Any],
) -> tuple[str, ...]:
    source_ids = _source_ids(body, path_params, pdir, action)
    assets = _asset_kinds(pdir, source_ids)
    if action == "reader.progress" or action == "reader.citation.export":
        return ("research_source",)
    if action in {"reader.annotation.create", "reader.annotation.update", "reader.annotation.delete"}:
        return tuple(dict.fromkeys(("research_source", *(
            kind for source_id in source_ids for kind in _artifact_kinds(source_id, source=False)
            if "/annotations/" in kind
        ))))
    if action == "reader.chunk.create":
        return tuple(
            _jsonl(f"research/chunks/{__import__('nblane.core.research_workspace', fromlist=['source_slug']).source_slug(source_id)}.jsonl")
            for source_id in source_ids
        )
    if action == "reader.citation.create":
        return (
            _file("research/claims.yaml"),
            _file("research/citations.yaml"),
            *(_jsonl(f"research/chunks/{__import__('nblane.core.research_workspace', fromlist=['source_slug']).source_slug(source_id)}.jsonl") for source_id in source_ids),
        )
    if action in {"reader.translation", "reader.artifacts.prepare"}:
        return tuple(dict.fromkeys((
            "research_source",
            *(kind for source_id in source_ids for kind in _artifact_kinds(source_id, source=False)
              if any(part in kind for part in ("/paper-pages/", "/paper-segments/", "/paper-structure/", "/translations/"))),
        )))
    if action == "reader.analysis":
        return tuple(dict.fromkeys((
            "research_source",
            *(kind for source_id in source_ids for kind in _artifact_kinds(source_id, source=False)
              if any(part in kind for part in ("/paper-pages/", "/paper-segments/", "/paper-structure/", "/translations/", "/analysis/"))),
        )))
    if action in {"reader.collection.edit", "reader.collection.trash", "reader.collection.purge", "reader.source.edit", "reader.source.discard"}:
        return ("research_source", _file("research/library-tree.yaml"))
    if action == "reader.pdf.save":
        return ("research_source", *assets)
    if action == "reader.pdf.delete":
        return ("research_source", *assets)
    if action in {"reader.paper.delete", "reader.paper.purge"}:
        return tuple(dict.fromkeys((
            "research_source",
            *assets,
            *(kind for source_id in source_ids for kind in _artifact_kinds(source_id, source=False)),
        )))
    if action == "reader.artifacts.delete":
        return tuple(dict.fromkeys(
            kind for source_id in source_ids for kind in _artifact_kinds(source_id, source=False)
        ))
    if action == "research.import":
        return ("research_source", *assets)
    return ()


def _describe(
    action: str,
    path_params: dict[str, Any],
    body: Any,
    count: int,
    before: agent_journal.Snapshot,
) -> str:
    label = agent_policy.ACTION_LABELS.get(action, action)
    data = _payload(body)
    source_id = str(path_params.get("source_id") or data.get("source_id") or "").strip()
    state = before.get("research_source", {}).get(source_id) if source_id else None
    title = agent_ops.entity_title(state) if state else ""
    title = title or str(data.get("title") or data.get("node_id") or source_id or "").strip()
    text = f"{label}「{title}」" if title else label
    if count > 1:
        text += f"（{count} 条）"
    return text


def _agent_user(request: Request, template: str):
    from nblane import web_reader_api as reader

    try:
        if template.startswith("/api/research/"):
            return reader._auth_user_from_request(request)
        source_id = str(request.path_params.get("source_id") or "")
        token = (
            request.cookies.get(reader.COOKIE_NAME, "")
            or request.headers.get("x-reader-token", "")
            or request.query_params.get("reader_token", "")
            or request.query_params.get("token", "")
        )
        claims = reader._claims_from_token(token, source_id)
        return reader._user_for_claims(claims)
    except Exception:
        return None


def _profile_dir(request: Request, template: str) -> Path:
    from nblane import web_reader_api as reader

    if template.startswith("/api/research/"):
        return reader._paper_library_profile_dir(str(request.path_params.get("profile") or ""), request)
    ctx = reader._request_context(request, str(request.path_params.get("source_id") or ""))
    return ctx.profile_path


def job_reservation(request: Request, template: str) -> agent_ops.AgentWrite | None:
    reservation = request.scope.get(JOB_RESERVATION_SCOPE)
    if not isinstance(reservation, dict) or reservation.get("template") != template:
        return None
    write = reservation.get("write")
    return write if isinstance(write, agent_ops.AgentWrite) else None


def consume_job_reservation(request: Request, write: agent_ops.AgentWrite | None) -> None:
    if write is None:
        return
    reservation = request.scope.get(JOB_RESERVATION_SCOPE)
    if isinstance(reservation, dict) and reservation.get("write") is write:
        request.scope.pop(JOB_RESERVATION_SCOPE, None)


def sync_commit(request: Request):
    write = request.scope.get(SYNC_WRITE_SCOPE)
    if isinstance(write, agent_ops.AgentWrite):
        cached = request.scope.get("nblane.reader_agent_sync_commit")
        if cached is None:
            cached = reader_ops.synchronous_commit(write)
            request.scope["nblane.reader_agent_sync_commit"] = cached
        return cached
    return reader_ops.direct_commit


def _take_sync_write(request: Request) -> agent_ops.AgentWrite | None:
    request.scope.pop("nblane.reader_agent_sync_commit", None)
    write = request.scope.pop(SYNC_WRITE_SCOPE, None)
    return write if isinstance(write, agent_ops.AgentWrite) else None


async def finish_sync_response(request: Request, response: Response) -> Response:
    """Finish strict sync journaling before the HTTP response leaves the app."""
    write = _take_sync_write(request)
    if write is None:
        return response
    try:
        await run_in_threadpool(agent_ops.finish, write)
    except agent_ops.AgentJournalError as exc:
        return await reader_agent_error_handler(
            request,
            ReaderAgentError(500, "agent_journal_failed", str(exc)),
        )
    return response


async def _finish_sync_exception(request: Request) -> None:
    write = _take_sync_write(request)
    if write is None:
        return
    try:
        await run_in_threadpool(agent_ops.finish, write)
    except agent_ops.AgentJournalError as exc:
        raise ReaderAgentError(500, "agent_journal_failed", str(exc)) from exc


def _abort_request_reservation(request: Request) -> None:
    reservation = request.scope.pop(JOB_RESERVATION_SCOPE, None)
    if isinstance(reservation, dict):
        write = reservation.get("write")
        if isinstance(write, agent_ops.AgentWrite):
            agent_ops.abort(write)


async def agent_write_guard(connection: HTTPConnection) -> AsyncIterator[None]:
    if not isinstance(connection, Request) or connection.method not in MUTATING_METHODS:
        yield
        return
    request = connection
    route = request.scope.get("route")
    template = str(getattr(route, "path", "") or "")
    if template in _AUTH_ROUTES or not (
        template.startswith("/api/research/") or template.startswith("/reader/api/")
    ):
        yield
        return
    user = _agent_user(request, template)
    if user is None or not agent_policy.is_agent(user):
        yield
        return
    body = await _read_body(request)
    path_params = dict(request.path_params)
    action = action_for(request.method, template, path_params, body)
    count = _batch_count(body)
    tier = agent_policy.tier_for(action, count)
    if tier == agent_policy.T0:
        yield
        return
    if tier == agent_policy.T3 or action == "reader.unsupported":
        raise ReaderAgentError(
            403,
            "agent_forbidden",
            "这个 Reader 操作只能由用户完成，或尚未登记助手权限，助手不能代办。",
        )
    pdir = _profile_dir(request, template)
    kinds = journal_kinds(action, pdir, body, path_params)
    fingerprint = agent_policy.fingerprint(request.method, request.url.path, body)
    operation = agent_ops.reserve if template in ASYNC_JOB_TEMPLATES else agent_ops.begin
    try:
        write = await run_in_threadpool(
            lambda: operation(
                pdir,
                actor=user.id,
                action=action,
                kinds=kinds,
                fingerprint=fingerprint,
                describe=lambda before: _describe(action, path_params, body, count, before),
                count=count,
                confirm_id=request.headers.get(agent_policy.CONFIRM_HEADER, ""),
            )
        )
    except agent_ops.ConfirmationRequired as exc:
        pending = exc.pending
        prefix = "确认码无效或已过期，请重新确认。" if exc.invalid else ""
        raise ReaderAgentError(
            428,
            "confirmation_invalid" if exc.invalid else "confirmation_required",
            (
                prefix
                + f"这一步需要用户在聊天里确认：{pending.summary}。用户同意后，在同一请求上加 "
                f"{agent_policy.CONFIRM_HEADER}: {pending.confirm_id} 重发（10 分钟内有效）。"
            ),
            confirmation=pending.public(),
        ) from None
    except agent_ops.AgentJournalError as exc:
        raise ReaderAgentError(500, "agent_journal_failed", str(exc)) from exc

    asynchronous = template in ASYNC_JOB_TEMPLATES
    if asynchronous:
        request.scope[JOB_RESERVATION_SCOPE] = {"template": template, "write": write}
    else:
        request.scope[SYNC_WRITE_SCOPE] = write
    try:
        yield
    except Exception:
        if asynchronous:
            _abort_request_reservation(request)
        else:
            await _finish_sync_exception(request)
        raise
    if asynchronous:
        _abort_request_reservation(request)


__all__ = [
    "ASYNC_JOB_TEMPLATES",
    "MUTATING_METHODS",
    "ROUTE_ACTIONS",
    "ReaderAgentError",
    "action_for",
    "agent_write_guard",
    "consume_job_reservation",
    "finish_sync_response",
    "job_reservation",
    "journal_kinds",
    "reader_agent_error_handler",
    "sync_commit",
]
