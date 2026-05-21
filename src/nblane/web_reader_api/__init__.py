"""FastAPI sidecar for the Paper Research Reader."""

from __future__ import annotations

import json
import mimetypes
import os
import time
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import quote, urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates

from nblane.core import auth as auth_core
from nblane.core.profile_io import profile_dir
from nblane.core.reader_actions import ReaderActionContext, handle_reader_action
from nblane.core import reader_tasks
from nblane.core.research_papers import (
    build_reader_payload,
    extract_paper_page_text_layer,
    load_paper_pages,
    paper_pdf_asset_path,
    render_paper_page_preview,
)
from nblane.core.research_sources import load_research_sources
from nblane.research_paper_reader_component.events import ANNOTATION_UPDATE

COOKIE_NAME = "nblane_reader_session"
READER_PREFIX = "/reader"
PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
STATIC_DIR = PACKAGE_DIR / "static"
ASSET_DIR = STATIC_DIR / "assets"

app = FastAPI(title="nblane Paper Reader API")


def _local_user() -> auth_core.User:
    return auth_core.User(
        id="local",
        display_name="Local",
        password_hash="",
        role="admin",
        teams=("*",),
    )


def _user_for_claims(claims: auth_core.ReaderTokenClaims) -> auth_core.User:
    if not auth_core.auth_configured():
        if claims.user_id != "local":
            raise HTTPException(status_code=401, detail="invalid reader session")
        return _local_user()
    try:
        users = auth_core.load_users()
    except auth_core.AuthConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    user = users.get(claims.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid reader session")
    if not auth_core.can_access_profile(user, claims.profile):
        raise HTTPException(status_code=403, detail="profile forbidden")
    return user


def _claims_from_token(token: str, source_id: str) -> auth_core.ReaderTokenClaims:
    try:
        claims = auth_core.verify_reader_token(token, expected_source_id=source_id)
    except auth_core.AuthConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if claims is None:
        raise HTTPException(status_code=401, detail="invalid reader session")
    _user_for_claims(claims)
    return claims


def _request_context(request: Request, source_id: str) -> ReaderActionContext:
    token = (
        request.cookies.get(COOKIE_NAME, "")
        or request.headers.get("x-reader-token", "")
        or request.query_params.get("reader_token", "")
        or request.query_params.get("token", "")
    )
    claims = _claims_from_token(token, source_id)
    profile_path = profile_dir(claims.profile)
    return ReaderActionContext(
        profile_name=claims.profile,
        profile_path=profile_path,
        user_id=claims.user_id,
        source_id=source_id,
    )


def _same_origin_mutation(request: Request) -> None:
    host = (request.headers.get("host") or "").split("@")[-1].lower()
    for header in ("origin", "referer"):
        raw = request.headers.get(header)
        if not raw:
            continue
        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != host:
            raise HTTPException(status_code=403, detail="cross-origin reader mutation rejected")
        return


async def _json_body(request: Request) -> dict[str, object]:
    try:
        body = await request.json()
    except Exception:
        raw = (await request.body()).decode("utf-8", errors="ignore").strip()
        if not raw:
            return {}
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return body if isinstance(body, dict) else {}


def _reader_settings(payload: dict[str, object], page: int, target_lang: str) -> dict[str, object]:
    reader_state = payload.get("reader_state") if isinstance(payload.get("reader_state"), dict) else {}
    context_window = payload.get("context_window") if isinstance(payload.get("context_window"), dict) else {}
    return {
        "page": reader_state.get("last_read_page") or page,
        "initial_page": reader_state.get("last_read_page") or page,
        "page_count": context_window.get("total_pages") or 1,
        "context_window": context_window,
        "view_mode": "continuous",
        "reader_mode": reader_state.get("reader_mode") or "pdf",
        "scale_mode": reader_state.get("scale_mode") or "fit-width",
        "active_tab": reader_state.get("active_tab") or "notes",
        "target_lang": reader_state.get("target_lang") or target_lang or "zh",
        "compare_split_ratio": reader_state.get("compare_split_ratio") or payload.get("compare_split_ratio") or 50,
        "panel_width": reader_state.get("panel_width") or payload.get("panel_width") or 340,
        "overscan_pages": 3,
        "auto_save_progress": False,
        "emit_passive_events": False,
        "side_panel_default": "collapsed" if reader_state.get("side_panel_collapsed", True) else "open",
        "side_panel_collapsed": reader_state.get("side_panel_collapsed", True),
        "focus_annotation_id": reader_state.get("focused_annotation_id") or "",
        "focus_chunk_id": reader_state.get("focused_chunk_id") or "",
        "left_rail_collapsed": reader_state.get("left_rail_collapsed", False),
        "active_left_tab": reader_state.get("active_left_tab") or "outline",
        "translation_source_visible": reader_state.get("translation_source_visible", True),
        "active_translation_anchor": reader_state.get("active_translation_anchor") or "",
        "height_mode": "viewport",
        "render_cache": True,
        "render_cache_max_pages": 36,
        "translation_layout": "flow",
        "translation_overflow_policy": "fixed-expand",
        "debug_overlay_enabled": os.getenv("NBLANE_READER_DEBUG_OVERLAY", "").strip().lower() in {"1", "true", "yes", "on"},
        "translation_dock_default": "selection",
        "pdf_load_timeout_ms": 30000,
        "pdf_page_render_timeout_ms": 12000,
        "pdf_text_layer_timeout_ms": 12000,
    }


def _query_pages(request: Request) -> set[int]:
    pages: set[int] = set()
    for key in ("pages", "requested_pages"):
        for raw in request.query_params.getlist(key):
            for part in str(raw or "").split(","):
                try:
                    page = int(part)
                except (TypeError, ValueError):
                    continue
                if page > 0:
                    pages.add(page)
    return pages


def _payload_for_context(
    ctx: ReaderActionContext,
    page: int | None = None,
    *,
    requested_pages: set[int] | None = None,
) -> dict[str, object]:
    inbox = load_research_sources(ctx.profile_path)
    source = inbox.by_id().get(ctx.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")
    metadata = dict(source.metadata or {})
    target_lang = str(metadata.get("target_lang") or "zh")
    current_page = max(1, int(page or metadata.get("last_read_page") or 1))
    page_rows = load_paper_pages(ctx.profile_path, ctx.source_id)
    total_pages = max(
        [
            int(metadata.get("page_count") or 0),
            int(metadata.get("reading_artifacts_page_count") or 0),
            *[row.page for row in page_rows],
            current_page,
            1,
        ]
    )
    payload = build_reader_payload(
        ctx.profile_path,
        ctx.source_id,
        page=current_page,
        requested_pages=set(requested_pages or set()),
        target_lang=target_lang,
        include_page_previews=False,
        pdf_url_override=f"{READER_PREFIX}/api/{quote(ctx.source_id, safe='')}/pdf",
    )
    payload["page_previews"] = []
    payload["pdf_base64"] = ""
    payload["ui"] = {}
    payload["settings"] = _reader_settings(payload, current_page, target_lang)
    payload["events_contract_version"] = 1
    return payload


def _paper_page_text_layer(profile_path: Path, source_id: str, page: int) -> dict[str, object]:
    try:
        return extract_paper_page_text_layer(profile_path, source_id, page)
    except RuntimeError as exc:  # pragma: no cover - optional dependency guard
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"failed to extract page text layer: {exc}") from exc


def _iter_file_range(path: Path, start: int, end: int, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
    with path.open("rb") as handle:
        handle.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            data = handle.read(min(chunk_size, remaining))
            if not data:
                break
            remaining -= len(data)
            yield data


def _range_response(path: Path, range_header: str | None) -> Response:
    size = path.stat().st_size
    headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "private, max-age=300",
    }
    media_type = "application/pdf"
    if not range_header:
        return FileResponse(path, media_type=media_type, filename=path.name, headers=headers)
    if not range_header.startswith("bytes=") or "," in range_header:
        raise HTTPException(status_code=416, detail="unsupported range")
    spec = range_header.removeprefix("bytes=").strip()
    start_text, _, end_text = spec.partition("-")
    try:
        if start_text:
            start = int(start_text)
            end = int(end_text) if end_text else size - 1
        else:
            suffix = int(end_text)
            start = max(0, size - suffix)
            end = size - 1
    except ValueError as exc:
        raise HTTPException(status_code=416, detail="invalid range") from exc
    if start < 0 or end < start or start >= size:
        raise HTTPException(status_code=416, detail="range not satisfiable")
    end = min(end, size - 1)
    headers.update(
        {
            "Content-Range": f"bytes {start}-{end}/{size}",
            "Content-Length": str(end - start + 1),
        }
    )
    return StreamingResponse(
        _iter_file_range(path, start, end),
        status_code=206,
        media_type=media_type,
        headers=headers,
    )


@app.get(f"{READER_PREFIX}/view/{{source_id}}")
async def reader_view(request: Request, source_id: str, token: str = ""):
    if token:
        claims = _claims_from_token(token, source_id)
        response = TEMPLATES.TemplateResponse(
            request,
            "index.html",
            {
                "source_id_json": json.dumps(source_id, ensure_ascii=False),
                "reader_prefix_json": json.dumps(READER_PREFIX),
                "reader_token_json": json.dumps(token),
            },
        )
        response.set_cookie(
            COOKIE_NAME,
            token,
            max_age=max(0, claims.exp - int(time.time())),
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https",
            path=READER_PREFIX,
        )
        return response
    _request_context(request, source_id)
    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "source_id_json": json.dumps(source_id, ensure_ascii=False),
            "reader_prefix_json": json.dumps(READER_PREFIX),
            "reader_token_json": json.dumps(""),
        },
    )


@app.get(f"{READER_PREFIX}/assets/{{file_name}}")
async def reader_asset(file_name: str):
    if "/" in file_name or "\\" in file_name:
        raise HTTPException(status_code=404, detail="asset not found")
    path = ASSET_DIR / file_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="asset not found")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})


@app.get(f"{READER_PREFIX}/api/{{source_id}}/pdf")
async def reader_pdf(request: Request, source_id: str):
    ctx = _request_context(request, source_id)
    try:
        path = paper_pdf_asset_path(ctx.profile_path, source_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _range_response(path, request.headers.get("range"))


@app.head(f"{READER_PREFIX}/api/{{source_id}}/pdf")
async def reader_pdf_head(request: Request, source_id: str):
    ctx = _request_context(request, source_id)
    try:
        path = paper_pdf_asset_path(ctx.profile_path, source_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        status_code=200,
        media_type="application/pdf",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "private, max-age=300",
            "Content-Length": str(path.stat().st_size),
        },
    )


@app.get(f"{READER_PREFIX}/api/{{source_id}}/payload")
async def reader_payload(request: Request, source_id: str, page: int | None = None):
    ctx = _request_context(request, source_id)
    return JSONResponse(_payload_for_context(ctx, page=page, requested_pages=_query_pages(request)))


@app.get(f"{READER_PREFIX}/api/{{source_id}}/page-preview/{{page}}")
async def reader_page_preview(request: Request, source_id: str, page: int):
    ctx = _request_context(request, source_id)
    return JSONResponse(render_paper_page_preview(ctx.profile_path, source_id, max(1, page), max_width=1100))


@app.get(f"{READER_PREFIX}/api/{{source_id}}/page-text-layer/{{page}}")
async def reader_page_text_layer(request: Request, source_id: str, page: int):
    ctx = _request_context(request, source_id)
    return JSONResponse(_paper_page_text_layer(ctx.profile_path, source_id, max(1, page)))


async def _run_action_endpoint(
    request: Request,
    source_id: str,
    action: str,
    body: dict[str, object] | None = None,
) -> JSONResponse:
    _same_origin_mutation(request)
    ctx = _request_context(request, source_id)
    try:
        result = handle_reader_action(ctx, action, body if body is not None else await _json_body(request))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(result.to_dict())


def _validate_reader_task_body(ctx: ReaderActionContext, body: dict[str, object]) -> None:
    payload_obj = body.get("payload")
    payload = payload_obj if isinstance(payload_obj, dict) else {}
    payload_source = str(body.get("source_id") or "").strip()
    nested_source = str(payload.get("source_id") or "").strip()
    if payload_source and payload_source != ctx.source_id:
        raise HTTPException(status_code=400, detail="reader task source mismatch")
    if nested_source and nested_source != ctx.source_id:
        raise HTTPException(status_code=400, detail="reader task source mismatch")
    payload_profile = str(body.get("profile") or body.get("profile_name") or "").strip()
    nested_profile = str(payload.get("profile") or payload.get("profile_name") or "").strip()
    if payload_profile and payload_profile != ctx.profile_name:
        raise HTTPException(status_code=403, detail="reader task profile mismatch")
    if nested_profile and nested_profile != ctx.profile_name:
        raise HTTPException(status_code=403, detail="reader task profile mismatch")
    payload_user = str(body.get("user_id") or "").strip()
    nested_user = str(payload.get("user_id") or "").strip()
    if payload_user and payload_user != ctx.user_id:
        raise HTTPException(status_code=403, detail="reader task user mismatch")
    if nested_user and nested_user != ctx.user_id:
        raise HTTPException(status_code=403, detail="reader task user mismatch")


def _reader_task_snapshot(task_id: str, ctx: ReaderActionContext) -> dict[str, object]:
    try:
        return reader_tasks.snapshot(task_id, ctx=ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _reader_task_cancel(task_id: str, ctx: ReaderActionContext) -> dict[str, object]:
    try:
        return reader_tasks.cancel(task_id, ctx=ctx)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _reader_task_sse(task_id: str, ctx: ReaderActionContext) -> Iterator[str]:
    try:
        for snap in reader_tasks.iter_snapshots(task_id, ctx=ctx):
            yield f"event: snapshot\ndata: {json.dumps(snap, ensure_ascii=False)}\n\n"
    except PermissionError as exc:
        payload = {
            "task_id": task_id,
            "action": "",
            "event_id": "",
            "status": "failed",
            "source_id": ctx.source_id,
            "profile": ctx.profile_name,
            "user_id": ctx.user_id,
            "result": {},
            "error": str(exc),
            "message": "",
            "warnings": [],
            "changed_ids": {},
            "progress": {
                "phase": "failed",
                "label": str(exc),
                "current": 0,
                "total": 0,
                "saved": 0,
            },
            "refresh": {"payload": False, "pages": [], "target_lang": ""},
            "started_at": 0.0,
            "updated_at": time.time(),
            "finished_at": time.time(),
        }
        yield f"event: snapshot\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post(f"{READER_PREFIX}/api/{{source_id}}/tasks")
async def reader_task_start(request: Request, source_id: str):
    _same_origin_mutation(request)
    ctx = _request_context(request, source_id)
    body = await _json_body(request)
    _validate_reader_task_body(ctx, body)
    action = str(body.get("action") or "").strip()
    payload_obj = body.get("payload")
    if isinstance(payload_obj, dict):
        payload = dict(payload_obj)
    else:
        payload = {
            key: value
            for key, value in body.items()
            if key not in {"action", "task_id", "profile", "profile_name", "user_id"}
        }
    payload.setdefault("source_id", source_id)
    try:
        snap = reader_tasks.start(
            ctx,
            action,
            payload,
            task_id=str(body.get("task_id") or ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse({"ok": True, "task": snap}, status_code=202)


@app.get(f"{READER_PREFIX}/api/{{source_id}}/tasks/{{task_id}}")
async def reader_task_get(request: Request, source_id: str, task_id: str):
    ctx = _request_context(request, source_id)
    return JSONResponse(_reader_task_snapshot(task_id, ctx))


@app.get(f"{READER_PREFIX}/api/{{source_id}}/tasks/{{task_id}}/events")
async def reader_task_events(request: Request, source_id: str, task_id: str):
    ctx = _request_context(request, source_id)
    return StreamingResponse(
        _reader_task_sse(task_id, ctx),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.delete(f"{READER_PREFIX}/api/{{source_id}}/tasks/{{task_id}}")
async def reader_task_delete(request: Request, source_id: str, task_id: str):
    _same_origin_mutation(request)
    ctx = _request_context(request, source_id)
    return JSONResponse({"ok": True, "task": _reader_task_cancel(task_id, ctx)})


@app.post(f"{READER_PREFIX}/api/{{source_id}}/annotation")
async def reader_annotation(request: Request, source_id: str):
    body = await _json_body(request)
    action = str(body.get("action") or "").strip()
    if not action:
        action = ANNOTATION_UPDATE if (body.get("annotation_id") or body.get("id")) else "annotation_create"
    return await _run_action_endpoint(request, source_id, action, body)


@app.delete(f"{READER_PREFIX}/api/{{source_id}}/annotation/{{annotation_id}}")
async def reader_annotation_delete(request: Request, source_id: str, annotation_id: str):
    body = await _json_body(request)
    body["annotation_id"] = annotation_id
    return await _run_action_endpoint(request, source_id, "annotation_delete", body)


@app.post(f"{READER_PREFIX}/api/{{source_id}}/translate")
async def reader_translate(request: Request, source_id: str):
    body = await _json_body(request)
    return await _run_action_endpoint(request, source_id, str(body.get("action") or "translate_selection"), body)


@app.post(f"{READER_PREFIX}/api/{{source_id}}/explain")
async def reader_explain(request: Request, source_id: str):
    return await _run_action_endpoint(request, source_id, "explain_selection")


@app.post(f"{READER_PREFIX}/api/{{source_id}}/ask")
async def reader_ask(request: Request, source_id: str):
    return await _run_action_endpoint(request, source_id, "ask_paper")


@app.post(f"{READER_PREFIX}/api/{{source_id}}/chunk")
async def reader_chunk(request: Request, source_id: str):
    return await _run_action_endpoint(request, source_id, "create_chunk_from_selection")


@app.post(f"{READER_PREFIX}/api/{{source_id}}/citation")
async def reader_citation(request: Request, source_id: str):
    return await _run_action_endpoint(request, source_id, "create_citation")


@app.post(f"{READER_PREFIX}/api/{{source_id}}/progress")
async def reader_progress(request: Request, source_id: str):
    return await _run_action_endpoint(request, source_id, "save_progress")


@app.post(f"{READER_PREFIX}/api/{{source_id}}/review")
async def reader_review(request: Request, source_id: str):
    return await _run_action_endpoint(request, source_id, "generate_review_card")


@app.post(f"{READER_PREFIX}/api/{{source_id}}/analyze")
async def reader_analyze(request: Request, source_id: str):
    return await _run_action_endpoint(request, source_id, "analyze_paper")


@app.post(f"{READER_PREFIX}/api/{{source_id}}/action/{{action}}")
async def reader_generic_action(request: Request, source_id: str, action: str):
    return await _run_action_endpoint(request, source_id, action)


__all__ = ["app"]
