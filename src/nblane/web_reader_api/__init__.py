"""FastAPI sidecar for the Paper Research Reader."""

from __future__ import annotations

import base64
import binascii
import asyncio
import hashlib
import json
import mimetypes
import os
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from urllib.parse import quote, urlparse

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates

from nblane.core import auth as auth_core
from nblane.core import llm as llm_client
from nblane.core.auth import mint_reader_token
from nblane.core.home_dashboard import dashboard_payload
from nblane.core.paper_library_workspace import (
    build_paper_library_payload,
    handle_paper_library_event,
)
from nblane.core.profile_io import list_profiles, profile_dir
from nblane.core import ai_stream_tasks
from nblane.core.blog_workspace import (
    build_blog_workspace_payload,
    handle_blog_workspace_event,
)
from nblane.core.public_site import (
    PublicSiteError,
    build_public_site,
    load_blog_post,
    publish_blog_text,
)
from nblane.core.reader_actions import ReaderActionContext, handle_reader_action
from nblane.core import reader_tasks
from nblane.core.research_papers import (
    PAPER_SEARCH_PROVIDERS,
    PaperImportError,
    _paper_search_result_has_downloadable_pdf,
    build_reader_payload,
    ensure_paper_pdf_downloaded,
    extract_paper_page_text_layer,
    import_paper_pdf,
    import_paper_search_results,
    import_paper_url,
    load_paper_pages,
    mark_imported_paper_results,
    paper_pdf_asset_path,
    paper_translations_bulk,
    render_paper_page_preview,
    search_papers,
    search_papers_with_codex,
    upload_paper_library_pdf,
)
from nblane.core.research_sources import add_research_source, load_research_sources, save_research_sources
from nblane.core.web_preferences import load_web_preferences
from nblane.research_paper_reader_component.events import ANNOTATION_UPDATE
from nblane.web_i18n import home_ui

COOKIE_NAME = "nblane_reader_session"
READER_PREFIX = "/reader"
PAPER_LIBRARY_CODEX_SEARCH_TIMEOUT_SECONDS = 120.0
PAPER_LIBRARY_CODEX_DEEP_SEARCH_TIMEOUT_SECONDS = 180.0
PAPER_LIBRARY_CODEX_DEEP_MIN_TIMEOUT_SECONDS = 180.0
PAPER_LIBRARY_CODEX_QUICK_BASE_SECONDS = 120.0
PAPER_LIBRARY_CODEX_DEEP_BASE_SECONDS = 180.0
PAPER_LIBRARY_CODEX_QUICK_MAX_SECONDS = 240.0
PAPER_LIBRARY_CODEX_DEEP_MAX_SECONDS = 420.0
PAPER_LIBRARY_CODEX_QUICK_IDLE_SECONDS = 60.0
PAPER_LIBRARY_CODEX_DEEP_IDLE_SECONDS = 90.0
PAPER_LIBRARY_MODEL_SEARCH_TIMEOUT_SECONDS = 18.0
PAPER_LIBRARY_PROVIDER_SEARCH_TIMEOUT_SECONDS = 4.0
PAPER_LIBRARY_WEB_SEARCH_TIMEOUT_SECONDS = 8.0
PAPER_LIBRARY_PROVIDER_SEARCH_BUDGET_SECONDS = 18.0
PAPER_LIBRARY_SEARCH_JOB_TTL_SECONDS = 900.0
PAPER_LIBRARY_EVENT_JOB_TTL_SECONDS = 900.0
PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
STATIC_DIR = PACKAGE_DIR / "static"
ASSET_DIR = STATIC_DIR / "assets"
PAPER_LIBRARY_FRONTEND_DIR = PACKAGE_DIR.parent / "paper_library_component" / "frontend" / "static"
PAPER_LIBRARY_ASSET_DIR = PAPER_LIBRARY_FRONTEND_DIR / "assets"
HOME_DASHBOARD_FRONTEND_DIR = PACKAGE_DIR.parent / "home_dashboard_component" / "frontend" / "static"
HOME_DASHBOARD_ASSET_DIR = HOME_DASHBOARD_FRONTEND_DIR / "assets"
BLOG_EDITOR_FRONTEND_DIR = PACKAGE_DIR.parent / "public_blog_editor_component" / "frontend" / "static"
BLOG_EDITOR_ASSET_DIR = BLOG_EDITOR_FRONTEND_DIR / "assets"
_PAPER_LIBRARY_SEARCH_JOBS: dict[str, dict[str, object]] = {}
_PAPER_LIBRARY_SEARCH_JOBS_LOCK = threading.Lock()
_PAPER_LIBRARY_EVENT_JOBS: dict[str, dict[str, object]] = {}
_PAPER_LIBRARY_EVENT_JOBS_LOCK = threading.Lock()

app = FastAPI(title="nblane Paper Reader API")


def _is_local_paper_library_embed(request: Request) -> bool:
    """Return True for Streamlit sandbox iframe calls into local Paper Library APIs."""

    if auth_core.auth_configured():
        return False
    if (request.headers.get("origin") or "").strip().lower() != "null":
        return False
    path = str(request.url.path or "")
    return path.startswith("/api/research/") and "/paper-library" in path


def _paper_library_embed_cors_headers(request: Request) -> dict[str, str]:
    if not _is_local_paper_library_embed(request):
        return {}
    requested_headers = request.headers.get("access-control-request-headers") or "content-type"
    return {
        "Access-Control-Allow-Origin": "null",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": requested_headers,
        "Access-Control-Allow-Credentials": "true",
        "Vary": "Origin",
    }


@app.middleware("http")
async def paper_library_embed_cors(request: Request, call_next):
    """Allow the 8503 Streamlit iframe to call the local 8502 Paper Library API."""

    cors_headers = _paper_library_embed_cors_headers(request)
    if cors_headers and request.method.upper() == "OPTIONS":
        return Response(status_code=204, headers=cors_headers)
    response = await call_next(request)
    for key, value in cors_headers.items():
        response.headers[key] = value
    return response


def _local_user() -> auth_core.User:
    return auth_core.User(
        id="local",
        display_name="Local",
        password_hash="",
        role="admin",
        teams=("*",),
    )


def _truthy_env(name: str) -> bool | None:
    raw = os.getenv(name, "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off", "none"}:
        return False
    return None


def _auth_cookie_secure(request: Request) -> bool:
    explicit = _truthy_env("NBLANE_AUTH_COOKIE_SECURE")
    if explicit is not None:
        return explicit
    return False


def _auth_cookie_max_age(exp: int) -> int:
    return max(0, int(exp) - int(time.time()))


def _set_auth_session_cookie(
    response: Response,
    request: Request,
    user_id: str,
    *,
    ttl_seconds: int = 12 * 3600,
) -> None:
    token = auth_core.mint_auth_session_token(user_id, ttl_seconds=ttl_seconds)
    claims = auth_core.verify_auth_session_token(token)
    max_age = _auth_cookie_max_age(claims.exp) if claims else ttl_seconds
    response.set_cookie(
        auth_core.AUTH_SESSION_COOKIE_NAME,
        token,
        max_age=max_age,
        path="/",
        httponly=True,
        secure=_auth_cookie_secure(request),
        samesite="lax",
    )


def _delete_auth_session_cookie(response: Response, request: Request) -> None:
    response.delete_cookie(
        auth_core.AUTH_SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=_auth_cookie_secure(request),
        samesite="lax",
    )


def _load_auth_user(user_id: str) -> auth_core.User:
    if not auth_core.auth_configured():
        if user_id and user_id != "local":
            return auth_core.User(
                id=user_id,
                display_name=user_id,
                password_hash="",
                role="admin",
                teams=("*",),
            )
        return _local_user()
    try:
        users = auth_core.load_users()
    except auth_core.AuthConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    user = users.get(str(user_id or "").strip())
    if user is None:
        raise HTTPException(status_code=401, detail="invalid auth session")
    return user


def _verify_auth_token(token: str, *, expected_kind: str) -> auth_core.AuthSessionClaims | None:
    try:
        return auth_core.verify_auth_session_token(token, expected_kind=expected_kind)
    except auth_core.AuthConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _auth_user_from_request(request: Request) -> auth_core.User:
    if not auth_core.auth_configured():
        return _local_user()
    cookie = request.cookies.get(auth_core.AUTH_SESSION_COOKIE_NAME, "")
    if cookie:
        claims = _verify_auth_token(cookie, expected_kind=auth_core.AUTH_SESSION_KIND)
        if claims is not None:
            return _load_auth_user(claims.user_id)
    handoff = (
        request.query_params.get("auth_handoff", "")
        or request.query_params.get("handoff", "")
    )
    if handoff:
        claims = _verify_auth_token(handoff, expected_kind=auth_core.AUTH_HANDOFF_KIND)
        if claims is not None:
            user = _load_auth_user(claims.user_id)
            request.state.nblane_auth_handoff_user_id = user.id
            return user
    raise HTTPException(status_code=401, detail="auth session required")


def _apply_handoff_cookie(response: Response, request: Request) -> None:
    user_id = str(getattr(request.state, "nblane_auth_handoff_user_id", "") or "").strip()
    if user_id:
        _set_auth_session_cookie(response, request, user_id)


def _safe_auth_next(next_url: str) -> str:
    clean = str(next_url or "").strip()
    if not clean:
        return "/auth/session-ok"
    if clean.startswith("/") and not clean.startswith("//"):
        return clean
    return "/auth/session-ok"


@app.get("/auth/session")
async def auth_session(request: Request, token: str = "", next: str = ""):
    return _auth_session_response(request, token, next)


@app.post("/auth/session")
async def auth_session_post(request: Request, token: str = Form(""), next: str = Form("")):
    return _auth_session_response(request, token, next)


def _auth_session_response(request: Request, token: str, next: str = "") -> Response:
    claims = _verify_auth_token(token, expected_kind=auth_core.AUTH_HANDOFF_KIND)
    if claims is None:
        raise HTTPException(status_code=401, detail="invalid auth handoff")
    user = _load_auth_user(claims.user_id)
    if next:
        response: Response = RedirectResponse(_safe_auth_next(next), status_code=303)
    else:
        response = Response(
            "<!doctype html><html><body>ok</body></html>",
            media_type="text/html",
        )
    _set_auth_session_cookie(response, request, user.id)
    return response


@app.get("/auth/session-ok")
async def auth_session_ok():
    return Response(
        "<!doctype html><html><body>nblane sidecar ok</body></html>",
        media_type="text/html",
        headers={"X-Nblane-Sidecar": "reader-api"},
    )


@app.get("/auth/logout")
async def auth_logout(request: Request):
    response = Response("<!doctype html><html><body>signed out</body></html>", media_type="text/html")
    _delete_auth_session_cookie(response, request)
    return response


def _paper_library_user(profile: str, request: Request) -> auth_core.User:
    clean = str(profile or "").strip()
    if not clean:
        raise HTTPException(status_code=400, detail="profile is required")
    user = _auth_user_from_request(request)
    if not auth_core.can_access_profile(user, clean):
        raise HTTPException(status_code=403, detail="profile forbidden")
    return user


def _paper_library_profile_dir(profile: str, request: Request) -> Path:
    try:
        path = profile_dir(profile)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="profile not found") from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail="profile not found")
    _paper_library_user(profile, request)
    return path


def _default_profile_name() -> str:
    profiles = list_profiles()
    return profiles[0] if profiles else ""


def _dashboard_profile_dir(profile: str, request: Request) -> Path:
    clean = str(profile or "").strip()
    if not clean:
        raise HTTPException(status_code=400, detail="profile is required")
    try:
        path = profile_dir(clean)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="profile not found") from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail="profile not found")
    _paper_library_user(clean, request)
    return path


def _paper_library_assets() -> dict[str, list[str]]:
    if not PAPER_LIBRARY_ASSET_DIR.exists():
        return {"scripts": [], "styles": []}
    scripts = sorted(
        f"/paper-library/assets/{path.name}"
        for path in PAPER_LIBRARY_ASSET_DIR.glob("*.js")
        if path.is_file()
    )
    styles = sorted(
        f"/paper-library/assets/{path.name}"
        for path in PAPER_LIBRARY_ASSET_DIR.glob("*.css")
        if path.is_file()
    )
    return {"scripts": scripts, "styles": styles}


def _home_dashboard_assets() -> dict[str, list[str]]:
    if not HOME_DASHBOARD_ASSET_DIR.exists():
        return {"scripts": [], "styles": []}
    scripts = sorted(
        f"/dashboard/assets/{path.name}"
        for path in HOME_DASHBOARD_ASSET_DIR.glob("*.js")
        if path.is_file()
    )
    styles = sorted(
        f"/dashboard/assets/{path.name}"
        for path in HOME_DASHBOARD_ASSET_DIR.glob("*.css")
        if path.is_file()
    )
    return {"scripts": scripts, "styles": styles}


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
    if _is_local_paper_library_embed(request):
        return
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
    raw_bytes = await request.body()
    if not raw_bytes:
        return {}
    try:
        body = json.loads(raw_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid request body")
    return body if isinstance(body, dict) else {}


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _reader_ui() -> dict[str, str]:
    """Return Reader UI copy for the current deployment language."""

    if llm_client.ui_language() != "zh":
        return {
            "reader_workflow_hint": (
                "Reader writes stay candidate-first: translate, annotate, cite, then review before promotion."
            ),
            "translate_full_paper_help": (
                "Translate missing or stale structure/layout units for the whole paper. "
                "Existing current translations are reused."
            ),
            "connector_scope_hint": (
                "Connectors live in Research > Inbox & Connectors; Reader consumes imported sources."
            ),
        }
    return {
        "annotations": "标注",
        "notes": "笔记",
        "translation": "翻译",
        "review": "审阅",
        "figures": "图表",
        "ai": "审阅",
        "claims": "断言",
        "create_annotation": "高亮",
        "create_note": "笔记",
        "create_chunk": "保存引文",
        "create_citation": "引用此处",
        "delete_annotation": "删除标注",
        "translate_selection": "翻译选区",
        "translate_full_paper": "全文翻译",
        "translate_full_paper_help": (
            "为整篇论文缺失或过期的结构/版面单元生成译文，已是最新的译文会复用。"
        ),
        "translate_visible_pages": "翻译可见页",
        "explain_selection": "解释",
        "ask_paper": "提问",
        "ask_followup": "追问",
        "clear_chat": "清空",
        "qa_context": "上下文",
        "qa_context_pages": "页码",
        "qa_context_segments": "段落数",
        "qa_thinking": "思考中...",
        "save_progress": "保存进度",
        "review_card": "分析论文",
        "analyze_paper": "分析论文",
        "deep_read": "深读",
        "deep_read_empty": "暂无可靠深读发现。",
        "deep_section_takeaway": "一句话结论",
        "deep_section_findings": "关键发现",
        "deep_section_problem": "问题与动机",
        "deep_section_context": "背景与缺口",
        "deep_section_contributions": "核心贡献",
        "deep_section_method": "方法与机制",
        "deep_section_metrics": "指标与公式",
        "deep_section_experiments": "实验与结果",
        "deep_section_limitations": "局限",
        "deep_section_project_relevance": "项目相关性",
        "deep_section_open_questions": "开放问题",
        "deep_section_section_summaries": "分节摘要",
        "deep_section_terms": "关键术语",
        "deep_section_reading_plan": "阅读计划",
        "warnings": "警告",
        "searching": "正在搜索...",
        "no_match": "未找到匹配",
        "fullscreen": "全屏",
        "exit_fullscreen": "退出全屏",
        "mode_pdf": "PDF",
        "mode_compare": "对照",
        "mode_translation": "仅译文",
        "search": "搜索",
        "page": "页",
        "previous_page": "上一页",
        "next_page": "下一页",
        "zoom_out": "缩小",
        "zoom_in": "放大",
        "pdf_loading": "正在加载 PDF...",
        "pdf_ready": "PDF 就绪",
        "pdf_missing": "没有可用的 PDF 页面预览。",
        "pdf_preview_mode": "正在使用页面预览",
        "pdf_error": "PDF.js 无法渲染这篇论文。",
        "extracting_page_text": "正在抽取页面文本",
        "running_grobid": "正在运行 GROBID",
        "structured_text_ready": "结构化文本就绪",
        "fallback_text_ready": "备用文本就绪",
        "preparation_failed": "准备失败",
        "selected_text": "已选文本",
        "note": "笔记",
        "question": "问题",
        "jump": "跳转",
        "empty": "暂无内容",
        "fit_width": "适应宽度",
        "fit_page": "适应页面",
        "actual_size": "1:1",
        "panel": "面板",
        "outline": "大纲",
        "pages": "页码",
        "debug": "调试",
        "overlay_debug": "叠层调试",
        "show_source": "显示原文",
        "hide_source": "隐藏原文",
        "translated": "已翻译",
        "translating": "正在翻译...",
        "translating_visible_pages": "正在翻译可见页...",
        "translating_full_paper": "正在翻译全文...",
        "reviewing_paper": "正在分析论文...",
        "deep_reading": "正在深读论文...",
        "answering": "正在回答...",
        "answered": "已回答。",
        "missing": "缺失",
        "stale": "过期",
        "failed": "失败",
        "saved_pending": "已保存，等待同步",
        "saved": "已保存",
        "ask_selection": "带选区提问",
        "retry": "重试",
        "edit": "编辑",
        "cancel": "取消",
        "close": "关闭",
        "pin": "固定",
        "unpin": "取消固定",
        "reset": "重置",
        "dock_bottom": "底部",
        "all": "全部",
        "current_page": "当前页",
        "translate": "翻译",
        "selection_single_page": "多页选区暂时只捕获第一页。",
        "reader_workflow_hint": (
            "Reader 写入保持候选优先：先翻译、标注、引用，再审阅后推进。"
        ),
        "connector_scope_hint": (
            "连接器在研究工作台的「收件箱与连接器」中配置；Reader 只消费已导入的来源。"
        ),
        "translation_sync_failed": "翻译数据同步失败，正在重新拉取...",
        "page_load_failed": "页面加载失败",
    }


def _default_research_overview_url() -> str:
    explicit = os.getenv("NBLANE_RESEARCH_OVERVIEW_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    base = os.getenv("NBLANE_STREAMLIT_BASE_URL", "").strip().rstrip("/")
    return f"{base}/Research" if base else ""


def _paper_library_return_url(return_to: object, return_url: object) -> str:
    clean = _clean_text(return_url)
    if clean:
        return clean
    if _clean_text(return_to) == "overview":
        return _default_research_overview_url()
    return ""


def _clean_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = [part for line in value.splitlines() for part in line.split(",")]
    elif isinstance(value, (list, tuple, set)):
        raw = list(value)
    else:
        raw = [value]
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        clean = _clean_text(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _clean_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    clean = _clean_text(value).lower()
    if clean in {"1", "true", "yes", "on"}:
        return True
    if clean in {"0", "false", "no", "off"}:
        return False
    return default


def _positive_float(value: object) -> float | None:
    try:
        clean = float(value)
    except (TypeError, ValueError):
        return None
    return clean if clean > 0 else None


def _nonnegative_int(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _paper_library_codex_search_depth(body: dict[str, object]) -> str:
    clean = _clean_text(
        body.get("codex_search_depth")
        or body.get("search_depth")
        or body.get("codex_depth")
    ).lower()
    if clean in {"deep", "xhigh", "thorough", "careful"}:
        return "deep"
    return "quick"


def _paper_library_codex_reasoning_effort(body: dict[str, object]) -> str:
    explicit = _clean_text(
        body.get("codex_reasoning_effort")
        or body.get("reasoning_effort")
    ).lower()
    if explicit in {"low", "medium", "high", "xhigh"}:
        return explicit
    deep_requested = _paper_library_codex_search_depth(body) == "deep" or any(
        _clean_bool(body.get(key), False)
        for key in ("codex_deep_search", "deep_search")
    )
    return "xhigh" if deep_requested else "medium"


def _paper_library_codex_timeout_seconds(
    body: dict[str, object],
    reasoning_effort: str,
    *,
    limit: int = 10,
) -> float:
    explicit = _positive_float(body.get("codex_timeout_seconds")) or _positive_float(
        body.get("timeout_seconds")
    )
    if explicit is not None:
        return explicit
    clean_limit = max(1, min(int(limit or 10), 50))
    if reasoning_effort == "xhigh":
        base = (
            _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_CODEX_DEEP_BASE_SECONDS"))
            or PAPER_LIBRARY_CODEX_DEEP_BASE_SECONDS
        )
        hard_max = (
            _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_CODEX_DEEP_MAX_SECONDS"))
            or _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_CODEX_DEEP_SEARCH_TIMEOUT_SECONDS"))
            or PAPER_LIBRARY_CODEX_DEEP_MAX_SECONDS
        )
        return min(hard_max, base + min(clean_limit, 25) * 8.0)
    base = (
        _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_CODEX_QUICK_BASE_SECONDS"))
        or PAPER_LIBRARY_CODEX_QUICK_BASE_SECONDS
    )
    hard_max = (
        _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_CODEX_QUICK_MAX_SECONDS"))
        or _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_CODEX_SEARCH_TIMEOUT_SECONDS"))
        or PAPER_LIBRARY_CODEX_QUICK_MAX_SECONDS
    )
    return min(hard_max, base + min(clean_limit, 20) * 6.0)


def _paper_library_codex_budget_mode(body: dict[str, object]) -> str:
    explicit = _positive_float(body.get("codex_timeout_seconds")) or _positive_float(
        body.get("timeout_seconds")
    )
    return "manual" if explicit is not None else "auto"


def _paper_library_codex_home_policy(body: dict[str, object]) -> str:
    clean = _clean_text(
        body.get("codex_home_policy")
        or body.get("codex_home_mode")
        or os.getenv("NBLANE_CODEX_HOME_POLICY")
        or os.getenv("NBLANE_PAPER_SEARCH_CODEX_HOME_POLICY")
    ).lower()
    if clean in {"profile", "isolated", "profile_isolated", "web_profile"}:
        return "profile"
    if clean in {"default", "global", "terminal", "terminal_default", "shared"}:
        return "default"
    return "default"


def _paper_library_codex_idle_timeout_seconds(body: dict[str, object], reasoning_effort: str) -> float:
    explicit = _positive_float(body.get("codex_idle_timeout_seconds")) or _positive_float(
        body.get("idle_timeout_seconds")
    )
    if explicit is not None:
        return explicit
    if reasoning_effort == "xhigh":
        return (
            _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_CODEX_DEEP_IDLE_SECONDS"))
            or PAPER_LIBRARY_CODEX_DEEP_IDLE_SECONDS
        )
    return (
        _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_CODEX_QUICK_IDLE_SECONDS"))
        or PAPER_LIBRARY_CODEX_QUICK_IDLE_SECONDS
    )


def _paper_library_reply_language(profile_path: Path, body: dict[str, object], query: str) -> str:
    clean = _clean_text(body.get("reply_language") or body.get("reply_lang")).lower()
    if clean in {"en", "zh"}:
        return clean
    try:
        preferences = load_web_preferences(profile_path)
    except Exception:
        preferences = {}
    ai = preferences.get("ai") if isinstance(preferences.get("ai"), dict) else {}
    llm = ai.get("llm") if isinstance(ai.get("llm"), dict) else {}
    clean = _clean_text(llm.get("reply_lang")).lower()
    if clean in {"en", "zh"}:
        return clean
    return "zh" if any("\u4e00" <= char <= "\u9fff" for char in query) else ""


def _reader_settings(payload: dict[str, object], page: int, target_lang: str) -> dict[str, object]:
    reader_state = payload.get("reader_state") if isinstance(payload.get("reader_state"), dict) else {}
    context_window = payload.get("context_window") if isinstance(payload.get("context_window"), dict) else {}
    overscan_pages = os.getenv("NBLANE_READER_OVERSCAN_PAGES", "auto").strip() or "auto"
    render_cache_max_pages = os.getenv("NBLANE_READER_RENDER_CACHE_MAX_PAGES", "auto").strip() or "auto"
    translation_layout = os.getenv("NBLANE_READER_TRANSLATION_LAYOUT", "overlay").strip().lower() or "overlay"
    if translation_layout not in {"flow", "overlay"}:
        translation_layout = "overlay"
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
        "overscan_pages": overscan_pages,
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
        "render_cache_max_pages": render_cache_max_pages,
        "translation_layout": translation_layout,
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
    full_translation: bool = False,
    full_document: bool | None = None,
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
    if full_document is None:
        full_document = _payload_full_document_default()
    context_requested_pages = set(requested_pages or set())
    if full_translation or full_document:
        context_requested_pages.update(range(1, total_pages + 1))
    payload = build_reader_payload(
        ctx.profile_path,
        ctx.source_id,
        page=current_page,
        requested_pages=context_requested_pages,
        target_lang=target_lang,
        include_page_previews=False,
        pdf_url_override=f"{READER_PREFIX}/api/{quote(ctx.source_id, safe='')}/pdf",
    )
    payload["page_previews"] = []
    payload["pdf_base64"] = ""
    payload["ui"] = _reader_ui()
    payload["settings"] = _reader_settings(payload, current_page, target_lang)
    payload["settings"]["full_translation_context"] = bool(full_translation)
    payload["settings"]["full_document_payload"] = bool(full_document)
    payload["events_contract_version"] = 1
    return payload


def _payload_full_document_default() -> bool:
    raw = os.getenv("NBLANE_READER_FULL_DOCUMENT_PAYLOAD", "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    return True


def _payload_etag(payload: dict[str, object], *, target_lang: str) -> str:
    """Stable ETag for /payload responses.

    Mixes PDF fingerprint, total pages, segment/translation/annotation counts,
    and a coarse 'last touched' marker so any meaningful change busts the cache.
    """

    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
    fingerprint = str(metadata.get("pdf_sha256") or metadata.get("pdf_asset_ref") or source.get("id") or "")
    counters = (
        len(payload.get("segments") or []),
        len(payload.get("translations") or []),
        len(payload.get("translation_units") or []),
        len(payload.get("annotations") or []),
        len(payload.get("page_models") or []),
        int((payload.get("settings") or {}).get("page_count") or 0),
    )
    last_touched = ""
    for row in payload.get("translations") or []:
        if isinstance(row, dict):
            value = str(row.get("created") or row.get("updated") or "")
            if value > last_touched:
                last_touched = value
    analysis = payload.get("analysis") if isinstance(payload.get("analysis"), dict) else {}
    try:
        analysis_marker = hashlib.sha1(
            json.dumps(analysis, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
    except Exception:
        analysis_marker = "|".join(
            str(analysis.get(key) or "")
            for key in ("updated", "codex_deep_read_updated")
        )
    fingerprint_parts = [fingerprint, target_lang, last_touched, analysis_marker, *map(str, counters)]
    digest = hashlib.sha1("|".join(fingerprint_parts).encode("utf-8")).hexdigest()[:16]
    return f'W/"{digest}"'


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


@app.get("/paper-library")
async def paper_library_view(request: Request, profile: str = ""):
    clean_profile = str(profile or "").strip()
    if not clean_profile:
        clean_profile = _default_profile_name()
    if clean_profile:
        _paper_library_profile_dir(clean_profile, request)
    assets = _paper_library_assets()
    response = TEMPLATES.TemplateResponse(
        request,
        "paper_library.html",
        {
            "profile_json": json.dumps(clean_profile, ensure_ascii=False),
            "scripts": assets["scripts"],
            "styles": assets["styles"],
        },
    )
    _apply_handoff_cookie(response, request)
    return response


@app.get("/dashboard")
async def dashboard_view(request: Request, profile: str = "", embed: str = ""):
    clean_profile = str(profile or "").strip() or _default_profile_name()
    if clean_profile:
        _dashboard_profile_dir(clean_profile, request)
    assets = _home_dashboard_assets()
    response = TEMPLATES.TemplateResponse(
        request,
        "dashboard.html",
        {
            "profile_json": json.dumps(clean_profile, ensure_ascii=False),
            "scripts": assets["scripts"],
            "styles": assets["styles"],
            "streamlit_base_json": json.dumps(
                os.getenv("NBLANE_STREAMLIT_BASE_URL", "http://127.0.0.1:8503").strip()
                or "http://127.0.0.1:8503",
                ensure_ascii=False,
            ),
            "embed_json": json.dumps(str(embed or "").strip().lower() in {"1", "true", "yes"}, ensure_ascii=False),
        },
    )
    _apply_handoff_cookie(response, request)
    return response


@app.get("/api/dashboard/payload")
async def dashboard_payload_endpoint(request: Request, profile: str = ""):
    clean_profile = str(profile or "").strip() or _default_profile_name()
    _dashboard_profile_dir(clean_profile, request)
    ai_payload = {
        "configured": llm_client.is_configured(),
        "label": llm_client.model_label() if llm_client.is_configured() else "",
    }
    return JSONResponse(
        {
            "ok": True,
            "payload": dashboard_payload(
                clean_profile,
                ui=home_ui(),
                ai=ai_payload,
            ),
        }
    )


@app.get("/dashboard/assets/{file_name}")
async def dashboard_asset(file_name: str):
    if "/" in file_name or "\\" in file_name:
        raise HTTPException(status_code=404, detail="asset not found")
    path = HOME_DASHBOARD_ASSET_DIR / file_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="asset not found")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})


@app.get("/paper-library/assets/{file_name}")
async def paper_library_asset(file_name: str):
    if "/" in file_name or "\\" in file_name:
        raise HTTPException(status_code=404, detail="asset not found")
    path = PAPER_LIBRARY_ASSET_DIR / file_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="asset not found")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})


@app.post("/api/blog/{profile}/posts/{slug}/publish")
async def blog_publish(request: Request, profile: str, slug: str):
    """Publish one blog post after full publish-time validation.

    Accepts an optional ``{meta, body, blocks_json}`` body to publish unsaved
    structured text; otherwise publishes the post as already stored on disk.
    """
    _same_origin_mutation(request)
    _paper_library_profile_dir(profile, request)
    clean_slug = _clean_text(slug)
    if not clean_slug:
        raise HTTPException(status_code=400, detail="slug is required")
    body = await _json_body(request)
    has_inline_text = isinstance(body.get("meta"), dict) and isinstance(body.get("body"), str)
    try:
        if has_inline_text:
            blocks = body.get("blocks_json")
            path = await asyncio.to_thread(
                publish_blog_text,
                profile,
                clean_slug,
                dict(body["meta"]),
                str(body["body"]),
                blocks_json=blocks if isinstance(blocks, list) else None,
            )
        else:
            post = await asyncio.to_thread(load_blog_post, profile, clean_slug)
            path = await asyncio.to_thread(
                publish_blog_text,
                profile,
                clean_slug,
                dict(post.meta),
                post.body,
                blocks_json=post.blocks_json,
            )
    except PublicSiteError as exc:
        return JSONResponse(
            {"ok": False, "errors": str(exc).split("\n")},
            status_code=422,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse({"ok": True, "slug": clean_slug, "path": str(path), "status": "published"})


@app.post("/api/site/{profile}/build")
async def site_build(request: Request, profile: str):
    """Build the static public site for a profile.

    Optional body fields: ``include_drafts`` (bool), ``base_url`` (str).
    """
    _same_origin_mutation(request)
    _paper_library_profile_dir(profile, request)
    body = await _json_body(request)
    include_drafts = _clean_bool(body.get("include_drafts"), default=False)
    base_url = _clean_text(body.get("base_url"))
    try:
        result = await asyncio.to_thread(
            build_public_site,
            profile,
            include_drafts=include_drafts,
            base_url=base_url,
        )
    except PublicSiteError as exc:
        return JSONResponse(
            {"ok": False, "errors": str(exc).split("\n")},
            status_code=422,
        )
    return JSONResponse(
        {
            "ok": True,
            "output_dir": str(result.output_dir),
            "page_count": len(result.pages),
            "pages": [str(page) for page in result.pages],
        }
    )


def _blog_editor_index_html(config: dict[str, object]) -> str:
    """Return the built blog editor index.html, host-adapted for standalone use.

    Rewrites the vite-relative ``./assets/`` references to the served
    ``/blog-editor/assets/`` path and injects the standalone bootstrap config.
    """
    index_path = BLOG_EDITOR_FRONTEND_DIR / "index.html"
    html = index_path.read_text(encoding="utf-8")
    html = html.replace('"./assets/', '"/blog-editor/assets/')
    bootstrap = (
        "<script>window.__NBLANE_BLOG_STANDALONE__ = "
        + json.dumps(config, ensure_ascii=False)
        + ";</script>"
    )
    return html.replace("</head>", bootstrap + "</head>", 1)


@app.get("/blog-editor")
async def blog_editor_view(request: Request, profile: str = "", slug: str = ""):
    clean_profile = str(profile or "").strip() or _default_profile_name()
    if clean_profile:
        _paper_library_profile_dir(clean_profile, request)
    if not (BLOG_EDITOR_FRONTEND_DIR / "index.html").is_file():
        raise HTTPException(status_code=404, detail="blog editor build not found")
    streamlit_base = (
        os.getenv("NBLANE_STREAMLIT_BASE_URL", "http://127.0.0.1:8503").strip()
        or "http://127.0.0.1:8503"
    )
    config = {
        "profile": clean_profile,
        "slug": str(slug or "").strip(),
        "apiBase": "",
        "streamlitBase": streamlit_base,
        "standalone": True,
    }
    response = Response(content=_blog_editor_index_html(config), media_type="text/html")
    _apply_handoff_cookie(response, request)
    return response


@app.get("/blog-editor/assets/{file_name}")
async def blog_editor_asset(file_name: str):
    if "/" in file_name or "\\" in file_name:
        raise HTTPException(status_code=404, detail="asset not found")
    path = BLOG_EDITOR_ASSET_DIR / file_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="asset not found")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/blog/{profile}/workspace")
async def blog_workspace_payload(
    request: Request,
    profile: str,
    slug: str = "",
    status: str = "all",
):
    """Return the standalone blog editor's initial payload from disk."""
    _paper_library_profile_dir(profile, request)
    try:
        payload = await asyncio.to_thread(
            build_blog_workspace_payload,
            profile,
            active_slug=slug,
            status_filter=status,
        )
    except PublicSiteError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse({"ok": True, "payload": payload})


@app.post("/api/blog/{profile}/events")
async def blog_events(request: Request, profile: str):
    """Dispatch one React Blog Editor event against the public layer.

    Returns ``{ok, handled, ...}``. When ``handled`` is False the action is
    outside this host's scope (e.g. AI generation) and the client should fall
    back to the Streamlit editor for that operation.
    """
    _same_origin_mutation(request)
    _paper_library_profile_dir(profile, request)
    body = await _json_body(request)
    event = body.get("event") if isinstance(body.get("event"), dict) else body
    try:
        result = await asyncio.to_thread(handle_blog_workspace_event, profile, event)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result.handled:
        # Action is outside this host's scope (e.g. AI generation).
        return JSONResponse(result.to_dict(), status_code=422)
    # ``run_check`` is read-only validation: ``ok=False`` reports findings, not a
    # request failure, so it returns 200. Mutating actions that fail return 422.
    if not result.ok and result.action != "run_check":
        return JSONResponse(result.to_dict(), status_code=422)
    return JSONResponse(result.to_dict())


@app.post("/api/blog/{profile}/ai/start")
async def blog_ai_start(request: Request, profile: str):
    """Start an inline AI patch stream and return its initial snapshot.

    Backed by the same in-memory ``ai_stream_tasks`` registry used by the
    Streamlit host, so the lifecycle (start/poll/cancel) is identical.
    """
    _same_origin_mutation(request)
    _paper_library_profile_dir(profile, request)
    body = await _json_body(request)
    payload = body.get("payload") if isinstance(body.get("payload"), dict) else body
    slug = _clean_text(payload.get("slug"))
    if not slug:
        raise HTTPException(status_code=400, detail="slug is required")
    selected_block = payload.get("selected_block")
    if not isinstance(selected_block, dict):
        selected_block = {}
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    task_id = _clean_text(payload.get("stream_id") or payload.get("event_id")) or (
        f"ai-stream-{uuid.uuid4().hex[:12]}"
    )
    ai_stream_tasks.cleanup()
    snapshot = await asyncio.to_thread(
        ai_stream_tasks.start_ai_patch_stream,
        task_id=task_id,
        profile=profile,
        slug=slug,
        meta=meta,
        markdown=_clean_text(payload.get("markdown")) if isinstance(payload.get("markdown"), str) else str(payload.get("markdown") or ""),
        selected_block=selected_block,
        operation=_clean_text(payload.get("operation")) or "polish",
        prompt=str(payload.get("prompt") or ""),
        visual_kind=_clean_text(payload.get("visual_kind")),
    )
    return JSONResponse({"ok": True, "stream": snapshot, "stream_id": task_id})


@app.get("/api/blog/{profile}/ai/poll")
async def blog_ai_poll(request: Request, profile: str, stream_id: str = ""):
    """Return the current snapshot for an inline AI patch stream."""
    _paper_library_profile_dir(profile, request)
    clean_id = _clean_text(stream_id)
    if not clean_id:
        raise HTTPException(status_code=400, detail="stream_id is required")
    snapshot = await asyncio.to_thread(ai_stream_tasks.snapshot, clean_id)
    return JSONResponse({"ok": True, "stream": snapshot})


@app.post("/api/blog/{profile}/ai/cancel")
async def blog_ai_cancel(request: Request, profile: str):
    """Request cancellation of an inline AI patch stream."""
    _same_origin_mutation(request)
    _paper_library_profile_dir(profile, request)
    body = await _json_body(request)
    payload = body.get("payload") if isinstance(body.get("payload"), dict) else body
    clean_id = _clean_text(payload.get("stream_id"))
    if not clean_id:
        raise HTTPException(status_code=400, detail="stream_id is required")
    snapshot = await asyncio.to_thread(ai_stream_tasks.cancel, clean_id)
    return JSONResponse({"ok": True, "stream": snapshot})


@app.get("/api/research/{profile}/paper-library")
async def paper_library_payload(
    request: Request,
    profile: str,
    view: str = "all",
    node_id: str = "",
    query: str = "",
    sort: str = "recent",
    detail_id: str = "",
    focus: str = "",
    action: str = "",
    return_to: str = "",
    return_url: str = "",
):
    profile_path = _paper_library_profile_dir(profile, request)
    user = _paper_library_user(profile, request)
    payload = await asyncio.to_thread(
        build_paper_library_payload,
        profile_path,
        current_view=view,
        current_node=node_id,
        query=query,
        sort_mode=sort,
        detail_id=detail_id,
        focus=focus,
        action=action,
        return_to=return_to,
        return_url=_paper_library_return_url(return_to, return_url),
        user_id=user.id,
        reader_base="",
    )
    return JSONResponse({"ok": True, "payload": payload})


def _paper_library_event_response(
    profile_path: Path,
    body: dict[str, object],
    result: object,
    user_id: str,
) -> dict[str, object]:
    state = body.get("state") if isinstance(body.get("state"), dict) else {}
    next_state = result.next
    view = str(next_state.get("view") or state.get("view") or "all")
    node_id = str(next_state.get("node_id") if "node_id" in next_state else state.get("node_id") or "")
    detail_id = str(next_state.get("detail_id") if "detail_id" in next_state else state.get("detail_id") or "")
    focus = str(next_state.get("focus") if "focus" in next_state else state.get("focus") or "")
    action = str(next_state.get("action") if "action" in next_state else state.get("action") or "")
    return_to = str(next_state.get("return_to") if "return_to" in next_state else state.get("return_to") or "")
    return_url = str(next_state.get("return_url") if "return_url" in next_state else state.get("return_url") or "")
    payload = build_paper_library_payload(
        profile_path,
        current_view=view,
        current_node=node_id,
        query=str(state.get("query") or ""),
        sort_mode=str(state.get("sort_mode") or state.get("sort") or "recent"),
        detail_id=detail_id,
        focus=focus,
        action=action,
        return_to=return_to,
        return_url=_paper_library_return_url(return_to, return_url),
        user_id=user_id,
        reader_base="",
    )
    return {"ok": True, "result": result.to_dict(), "payload": payload}


@app.post("/api/research/{profile}/paper-library/events")
async def paper_library_events(request: Request, profile: str):
    _same_origin_mutation(request)
    profile_path = _paper_library_profile_dir(profile, request)
    user = _paper_library_user(profile, request)
    body = await _json_body(request)
    try:
        result = await asyncio.to_thread(handle_paper_library_event, profile_path, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result.ok:
        return JSONResponse(result.to_dict(), status_code=400)
    response = await asyncio.to_thread(_paper_library_event_response, profile_path, body, result, user.id)
    return JSONResponse(response)


def _prune_paper_library_event_jobs() -> None:
    cutoff = time.time() - PAPER_LIBRARY_EVENT_JOB_TTL_SECONDS
    with _PAPER_LIBRARY_EVENT_JOBS_LOCK:
        stale = [
            job_id
            for job_id, job in _PAPER_LIBRARY_EVENT_JOBS.items()
            if float(job.get("created_at") or 0) < cutoff
        ]
        for job_id in stale:
            _PAPER_LIBRARY_EVENT_JOBS.pop(job_id, None)


def _paper_library_event_job_snapshot(job: dict[str, object]) -> dict[str, object]:
    snapshot = {
        key: value
        for key, value in job.items()
        if not key.startswith("_") and key not in {"result"}
    }
    started = job.get("_started_monotonic")
    finished = job.get("_finished_monotonic")
    if isinstance(started, (int, float)):
        end = (
            float(finished)
            if isinstance(finished, (int, float)) and float(finished) > 0
            else time.monotonic()
        )
        snapshot["elapsed_ms"] = max(0, int((end - float(started)) * 1000))
    return snapshot


def _update_paper_library_event_job(job_id: str, **updates: object) -> None:
    with _PAPER_LIBRARY_EVENT_JOBS_LOCK:
        job = _PAPER_LIBRARY_EVENT_JOBS.get(job_id)
        if not job:
            return
        if "warning" in updates and updates["warning"]:
            warnings = job.setdefault("warnings", [])
            if isinstance(warnings, list):
                warnings.append(_clean_text(updates["warning"]))
        for key, value in updates.items():
            if key == "warning":
                continue
            job[key] = value


def _paper_library_event_progress_callback(job_id: str) -> Callable[[dict[str, object]], None]:
    def progress(event: dict[str, object]) -> None:
        if not isinstance(event, dict):
            return
        phase = _clean_text(event.get("phase")) or "translation"
        batches = _nonnegative_int(event.get("batches"))
        batches_completed = _nonnegative_int(event.get("batches_completed"))
        segments_selected = _nonnegative_int(event.get("segments_selected"))
        segments_processed = _nonnegative_int(event.get("segments_processed"))
        step_current = _nonnegative_int(event.get("current"))
        step_total = _nonnegative_int(event.get("total"))
        message = _clean_text(event.get("message") or event.get("label"))
        if not message and batches:
            message = f"Translating batch {min(batches_completed, batches)}/{batches}."
        if not message and step_total:
            message = f"Running step {min(step_current, step_total)}/{step_total}."
        if not message:
            message = "Running Paper Library action."
        _update_paper_library_event_job(
            job_id,
            status="running",
            phase=phase,
            message=message,
            source_id=_clean_text(event.get("source_id")),
            target_lang=_clean_text(event.get("target_lang")),
            mode=_clean_text(event.get("mode")),
            scope=_clean_text(event.get("scope")),
            step_current=step_current,
            step_total=step_total,
            batches=batches,
            batches_completed=batches_completed,
            segments_selected=segments_selected,
            segments_processed=segments_processed,
            updated=_nonnegative_int(event.get("updated")),
            saved=_nonnegative_int(event.get("saved")),
            warning_count=_nonnegative_int(event.get("warnings")),
        )

    return progress


@app.post("/api/research/{profile}/paper-library/events/jobs")
async def paper_library_event_start_job(request: Request, profile: str):
    _same_origin_mutation(request)
    profile_path = _paper_library_profile_dir(profile, request)
    user = _paper_library_user(profile, request)
    body = await _json_body(request)
    action = _clean_text(body.get("action"))
    if not action:
        raise HTTPException(status_code=400, detail="action is required")
    _prune_paper_library_event_jobs()
    job_id = uuid.uuid4().hex
    now = time.time()
    job: dict[str, object] = {
        "job_id": job_id,
        "profile": profile,
        "event_action": action,
        "status": "queued",
        "phase": "queued",
        "message": "Queued Paper Library action.",
        "created_at": now,
        "started_at": 0.0,
        "finished_at": 0.0,
        "source_id": "",
        "target_lang": "",
        "mode": "",
        "scope": "",
        "step_current": 0,
        "step_total": 0,
        "batches": 0,
        "batches_completed": 0,
        "segments_selected": 0,
        "segments_processed": 0,
        "updated": 0,
        "saved": 0,
        "warning_count": 0,
        "warnings": [],
        "error": "",
        "_started_monotonic": 0.0,
        "_finished_monotonic": 0.0,
    }
    with _PAPER_LIBRARY_EVENT_JOBS_LOCK:
        _PAPER_LIBRARY_EVENT_JOBS[job_id] = job

    def worker() -> None:
        started = time.monotonic()
        _update_paper_library_event_job(
            job_id,
            status="running",
            phase="starting",
            message="Starting Paper Library action.",
            started_at=time.time(),
            _started_monotonic=started,
        )
        try:
            result = handle_paper_library_event(
                profile_path,
                dict(body),
                progress_callback=_paper_library_event_progress_callback(job_id),
            )
            if not result.ok:
                _update_paper_library_event_job(
                    job_id,
                    status="failed",
                    phase="failed",
                    message=result.message or "Paper Library action failed.",
                    error=result.message or "Paper Library action failed.",
                    result=result.to_dict(),
                    finished_at=time.time(),
                    _finished_monotonic=time.monotonic(),
                )
                return
            response = _paper_library_event_response(profile_path, dict(body), result, user.id)
        except Exception as exc:
            _update_paper_library_event_job(
                job_id,
                status="failed",
                phase="failed",
                message=str(exc),
                error=str(exc),
                finished_at=time.time(),
                _finished_monotonic=time.monotonic(),
            )
            return
        warnings = response.get("result", {}).get("warnings", []) if isinstance(response.get("result"), dict) else []
        warning_rows = warnings if isinstance(warnings, list) else []
        warning_updates: dict[str, object] = {"warnings": warning_rows}
        if warning_rows:
            warning_updates["warning_count"] = len(warning_rows)
        _update_paper_library_event_job(
            job_id,
            status="done",
            phase="done",
            message=response.get("result", {}).get("message") if isinstance(response.get("result"), dict) else "Done.",
            result=response,
            finished_at=time.time(),
            _finished_monotonic=time.monotonic(),
            **warning_updates,
        )

    threading.Thread(target=worker, name=f"paper-event-{job_id[:8]}", daemon=True).start()
    with _PAPER_LIBRARY_EVENT_JOBS_LOCK:
        snapshot = _paper_library_event_job_snapshot(_PAPER_LIBRARY_EVENT_JOBS[job_id])
    return JSONResponse({"ok": True, "job": snapshot, "job_id": job_id})


@app.get("/api/research/{profile}/paper-library/events/jobs/{job_id}")
async def paper_library_event_job_status(request: Request, profile: str, job_id: str):
    _paper_library_profile_dir(profile, request)
    with _PAPER_LIBRARY_EVENT_JOBS_LOCK:
        job = _PAPER_LIBRARY_EVENT_JOBS.get(job_id)
        if not job or job.get("profile") != profile:
            raise HTTPException(status_code=404, detail="event job not found")
        snapshot = _paper_library_event_job_snapshot(job)
        result = job.get("result") if job.get("status") in {"done", "failed"} else None
    return JSONResponse({"ok": True, "job": snapshot, "result": result})


def _paper_library_search_response(
    profile_path: Path,
    body: dict[str, object],
    *,
    progress: Callable[[dict[str, object]], None] | None = None,
    cancel_event: threading.Event | None = None,
) -> dict[str, object]:
    query = _clean_text(body.get("query"))
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    mode = _clean_text(body.get("mode")).lower() or "codex"
    try:
        limit = max(1, min(int(body.get("limit") or 10), 50))
    except (TypeError, ValueError):
        limit = 10
    providers = _clean_list(body.get("providers"))
    require_pdf = body.get("require_pdf")
    if require_pdf is None:
        require_pdf = True
    codex_reasoning_effort = _paper_library_codex_reasoning_effort(body)
    codex_search_depth = "deep" if codex_reasoning_effort == "xhigh" else "quick"
    codex_timeout = _paper_library_codex_timeout_seconds(body, codex_reasoning_effort, limit=limit)
    codex_budget_mode = _paper_library_codex_budget_mode(body)
    codex_home_policy = _paper_library_codex_home_policy(body)
    codex_idle_timeout = _paper_library_codex_idle_timeout_seconds(body, codex_reasoning_effort)
    reply_language = _paper_library_reply_language(profile_path, body, query)
    provider_timeout = (
        _positive_float(body.get("provider_timeout_seconds"))
        or _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_PROVIDER_SEARCH_TIMEOUT_SECONDS"))
        or PAPER_LIBRARY_PROVIDER_SEARCH_TIMEOUT_SECONDS
    )
    model_timeout = (
        _positive_float(body.get("model_timeout_seconds"))
        or _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_MODEL_SEARCH_TIMEOUT_SECONDS"))
        or PAPER_LIBRARY_MODEL_SEARCH_TIMEOUT_SECONDS
    )
    web_timeout = (
        _positive_float(body.get("web_timeout_seconds"))
        or _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_WEB_SEARCH_TIMEOUT_SECONDS"))
        or PAPER_LIBRARY_WEB_SEARCH_TIMEOUT_SECONDS
    )
    provider_budget = (
        _positive_float(body.get("provider_budget_seconds"))
        or _positive_float(os.getenv("NBLANE_PAPER_LIBRARY_PROVIDER_SEARCH_BUDGET_SECONDS"))
        or PAPER_LIBRARY_PROVIDER_SEARCH_BUDGET_SECONDS
    )
    use_profile_context = _clean_bool(
        body.get("use_profile_context")
        or body.get("include_profile_context")
        or body.get("personalize_with_profile"),
        False,
    )
    filters = {
        "providers": providers,
        "limit": limit,
        "year_from": _clean_text(body.get("year_from")),
        "year_to": _clean_text(body.get("year_to")),
        "has_open_access_pdf": bool(require_pdf),
        "codex_timeout_seconds": codex_timeout,
        "codex_idle_timeout_seconds": codex_idle_timeout,
        "codex_budget_mode": codex_budget_mode,
        "model_timeout_seconds": model_timeout,
        "provider_timeout_seconds": provider_timeout,
        "web_timeout_seconds": web_timeout,
        "provider_budget_seconds": provider_budget,
        "use_profile_context": use_profile_context,
        "codex_reasoning_effort": codex_reasoning_effort,
        "codex_search_depth": codex_search_depth,
        "codex_home_policy": codex_home_policy,
        "reply_language": reply_language,
    }
    if mode in {"model", "llm"}:
        filters["ai_backend"] = "direct_llm"
    elif mode in {"codex", ""}:
        filters["ai_backend"] = "local_codex_readonly"
    debug: dict[str, object] = {
        "mode": "provider" if mode == "provider" else "model" if mode in {"model", "llm"} else "codex",
        "query": query,
        "limit": limit,
        "require_pdf": bool(require_pdf),
        "profile_context_used": use_profile_context,
        "codex_reasoning_effort": codex_reasoning_effort,
        "codex_search_depth": codex_search_depth,
        "codex_home_policy": codex_home_policy,
        "reply_language": reply_language,
        "codex_timeout_seconds": codex_timeout,
        "codex_idle_timeout_seconds": codex_idle_timeout,
        "codex_budget_mode": codex_budget_mode,
    }
    if cancel_event is not None:
        filters["_cancel_check"] = cancel_event.is_set
        debug["_cancel_check"] = cancel_event.is_set
    if progress is not None:
        debug["_progress_callback"] = progress
        phase = "provider" if mode == "provider" else "model" if mode in {"model", "llm"} else "codex"
        progress(
            {
                "event": "phase",
                "phase": phase,
                "message": (
                    (
                        "Codex web search + "
                        f"{codex_reasoning_effort} "
                        f"{codex_search_depth} search, {codex_home_policy} Codex home, {codex_budget_mode} budget."
                    )
                    if phase == "codex"
                    else f"{phase.title()} search is running."
                ),
                "timeout_seconds": codex_timeout if phase == "codex" else model_timeout if phase == "model" else provider_budget,
                "idle_timeout_seconds": codex_idle_timeout if phase == "codex" else 0,
                "budget_mode": codex_budget_mode if phase == "codex" else "",
                "codex_reasoning_effort": codex_reasoning_effort if phase == "codex" else "",
                "codex_search_depth": codex_search_depth if phase == "codex" else "",
                "codex_home_policy": codex_home_policy if phase == "codex" else "",
                "reply_language": reply_language if phase == "codex" else "",
            }
        )
    if mode == "provider":
        rows = search_papers(
            query,
            tuple(providers or PAPER_SEARCH_PROVIDERS),
            limit,
            filters,
            debug=debug,
        )
    else:
        rows = search_papers_with_codex(
            profile_path,
            query,
            filters=filters,
            context_refs={
                "project_refs": _clean_list(body.get("project_refs")),
                "goal_refs": _clean_list(body.get("goal_refs")),
            },
            debug=debug,
        )
    debug.pop("_progress_callback", None)
    debug.pop("_cancel_check", None)
    if bool(require_pdf):
        rows = [row for row in rows if _paper_search_result_has_downloadable_pdf(row)]
    marked = mark_imported_paper_results(profile_path, [row.to_dict() for row in rows])
    candidates = [row.to_dict() for row in marked[:limit]]
    debug["final_count"] = len(candidates)
    debug["returned_titles"] = [row.get("title") for row in candidates if row.get("title")]
    return {
        "ok": True,
        "query": query,
        "mode": debug["mode"],
        "codex_reasoning_effort": codex_reasoning_effort if debug["mode"] == "codex" else "",
        "codex_search_depth": codex_search_depth if debug["mode"] == "codex" else "",
        "codex_home_policy": codex_home_policy if debug["mode"] == "codex" else "",
        "reply_language": reply_language if debug["mode"] == "codex" else "",
        "codex_timeout_seconds": codex_timeout if debug["mode"] == "codex" else 0,
        "codex_idle_timeout_seconds": codex_idle_timeout if debug["mode"] == "codex" else 0,
        "codex_budget_mode": codex_budget_mode if debug["mode"] == "codex" else "",
        "candidates": candidates,
        "count": len(candidates),
        "warnings": _clean_list(debug.get("warnings")),
        "search_trace": debug.get("steps") or [],
        "query_variants": debug.get("query_variants") or [],
        "debug": debug,
    }


def _prune_paper_library_search_jobs() -> None:
    cutoff = time.time() - PAPER_LIBRARY_SEARCH_JOB_TTL_SECONDS
    with _PAPER_LIBRARY_SEARCH_JOBS_LOCK:
        stale = [
            job_id
            for job_id, job in _PAPER_LIBRARY_SEARCH_JOBS.items()
            if float(job.get("created_at") or 0) < cutoff
        ]
        for job_id in stale:
            _PAPER_LIBRARY_SEARCH_JOBS.pop(job_id, None)


def _paper_library_search_job_snapshot(job: dict[str, object]) -> dict[str, object]:
    snapshot = {
        key: value
        for key, value in job.items()
        if not key.startswith("_") and key not in {"result"}
    }
    started = job.get("_started_monotonic")
    finished = job.get("_finished_monotonic")
    if isinstance(started, (int, float)):
        end = (
            float(finished)
            if isinstance(finished, (int, float)) and float(finished) > 0
            else time.monotonic()
        )
        snapshot["elapsed_ms"] = max(0, int((end - float(started)) * 1000))
    return snapshot


def _sse_event(event: str, data: dict[str, object]) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


def _append_paper_library_search_job_event(job_id: str, event: dict[str, object]) -> None:
    with _PAPER_LIBRARY_SEARCH_JOBS_LOCK:
        job = _PAPER_LIBRARY_SEARCH_JOBS.get(job_id)
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
            payload.setdefault("elapsed_ms", max(0, int((time.monotonic() - float(started)) * 1000)))
        events = job.setdefault("events", [])
        if isinstance(events, list):
            events.append(payload)
            if len(events) > 200:
                del events[:-200]


def _update_paper_library_search_job(job_id: str, **updates: object) -> None:
    with _PAPER_LIBRARY_SEARCH_JOBS_LOCK:
        job = _PAPER_LIBRARY_SEARCH_JOBS.get(job_id)
        if not job:
            return
        if "step" in updates and isinstance(updates["step"], dict):
            trace = job.setdefault("trace", [])
            if isinstance(trace, list):
                trace.append(updates["step"])
            step = updates["step"]
            stage = _clean_text(step.get("stage"))
            if stage:
                job["message"] = f"Completed {stage} stage."
        if "warning" in updates and updates["warning"]:
            warnings = job.setdefault("warnings", [])
            if isinstance(warnings, list):
                warnings.append(_clean_text(updates["warning"]))
        for key, value in updates.items():
            if key not in {"step", "warning"}:
                job[key] = value


def _paper_library_search_progress_callback(job_id: str) -> Callable[[dict[str, object]], None]:
    def progress(event: dict[str, object]) -> None:
        _append_paper_library_search_job_event(job_id, event)
        if event.get("event") == "step" and isinstance(event.get("step"), dict):
            _update_paper_library_search_job(job_id, step=event["step"])
            return
        event_name = _clean_text(event.get("event"))
        suppressed = {"event"}
        if event_name in {"command_started", "output", "command_finished", "timeout", "idle_timeout", "cancelled"}:
            suppressed.update({"status", "returncode", "stream"})
        if event_name == "output" and event.get("visible") is False:
            suppressed.update({"message", "phase", "output_kind", "detail", "visible"})
        updates = {key: value for key, value in event.items() if key not in suppressed}
        _update_paper_library_search_job(job_id, **updates)

    return progress


@app.post("/api/research/{profile}/paper-library/search")
async def paper_library_search(request: Request, profile: str):
    _same_origin_mutation(request)
    profile_path = _paper_library_profile_dir(profile, request)
    body = await _json_body(request)
    result = await asyncio.to_thread(_paper_library_search_response, profile_path, body)
    return JSONResponse(result)


@app.post("/api/research/{profile}/paper-library/search/jobs")
async def paper_library_search_start_job(request: Request, profile: str):
    _same_origin_mutation(request)
    profile_path = _paper_library_profile_dir(profile, request)
    body = await _json_body(request)
    if not _clean_text(body.get("query")):
        raise HTTPException(status_code=400, detail="query is required")
    _prune_paper_library_search_jobs()
    job_id = uuid.uuid4().hex
    now = time.time()
    cancel_event = threading.Event()
    job: dict[str, object] = {
        "job_id": job_id,
        "profile": profile,
        "status": "queued",
        "phase": "queued",
        "message": "Queued paper search.",
        "created_at": now,
        "started_at": 0.0,
        "finished_at": 0.0,
        "trace": [],
        "events": [],
        "warnings": [],
        "error": "",
        "cancel_requested": False,
        "_cancel_event": cancel_event,
        "_event_seq": 0,
        "_started_monotonic": 0.0,
        "_finished_monotonic": 0.0,
    }
    with _PAPER_LIBRARY_SEARCH_JOBS_LOCK:
        _PAPER_LIBRARY_SEARCH_JOBS[job_id] = job

    def worker() -> None:
        started = time.monotonic()
        _update_paper_library_search_job(
            job_id,
            status="running",
            phase="starting",
            message="Starting paper search.",
            started_at=time.time(),
            _started_monotonic=started,
        )
        _append_paper_library_search_job_event(
            job_id,
            {"event": "started", "phase": "starting", "message": "Starting paper search."},
        )
        try:
            result = _paper_library_search_response(
                profile_path,
                dict(body),
                progress=_paper_library_search_progress_callback(job_id),
                cancel_event=cancel_event,
            )
        except Exception as exc:
            if cancel_event.is_set():
                _update_paper_library_search_job(
                    job_id,
                    status="cancelled",
                    phase="cancelled",
                    message="Search cancelled.",
                    error="",
                    finished_at=time.time(),
                    _finished_monotonic=time.monotonic(),
                )
                _append_paper_library_search_job_event(
                    job_id,
                    {"event": "cancelled", "phase": "cancelled", "message": "Search cancelled."},
                )
                return
            _update_paper_library_search_job(
                job_id,
                status="failed",
                phase="failed",
                message=str(exc),
                error=str(exc),
                finished_at=time.time(),
                _finished_monotonic=time.monotonic(),
            )
            return
        if cancel_event.is_set():
            _update_paper_library_search_job(
                job_id,
                status="cancelled",
                phase="cancelled",
                message="Search cancelled.",
                result=result,
                finished_at=time.time(),
                _finished_monotonic=time.monotonic(),
            )
            _append_paper_library_search_job_event(
                job_id,
                {"event": "cancelled", "phase": "cancelled", "message": "Search cancelled."},
            )
            return
        _update_paper_library_search_job(
            job_id,
            status="done",
            phase="done",
            message=f"{result.get('count', 0)} PDF-ready candidates found.",
            result=result,
            trace=result.get("search_trace") or [],
            warnings=result.get("warnings") or [],
            finished_at=time.time(),
            _finished_monotonic=time.monotonic(),
        )
        _append_paper_library_search_job_event(
            job_id,
            {
                "event": "done",
                "phase": "done",
                "message": f"{result.get('count', 0)} PDF-ready candidates found.",
                "count": result.get("count", 0),
            },
        )

    threading.Thread(target=worker, name=f"paper-search-{job_id[:8]}", daemon=True).start()
    with _PAPER_LIBRARY_SEARCH_JOBS_LOCK:
        snapshot = _paper_library_search_job_snapshot(_PAPER_LIBRARY_SEARCH_JOBS[job_id])
    return JSONResponse({"ok": True, "job": snapshot, "job_id": job_id})


@app.get("/api/research/{profile}/paper-library/search/jobs/{job_id}")
async def paper_library_search_job_status(request: Request, profile: str, job_id: str):
    _paper_library_profile_dir(profile, request)
    with _PAPER_LIBRARY_SEARCH_JOBS_LOCK:
        job = _PAPER_LIBRARY_SEARCH_JOBS.get(job_id)
        if not job or job.get("profile") != profile:
            raise HTTPException(status_code=404, detail="search job not found")
        snapshot = _paper_library_search_job_snapshot(job)
        result = job.get("result") if job.get("status") == "done" else None
    return JSONResponse({"ok": True, "job": snapshot, "result": result})


@app.get("/api/research/{profile}/paper-library/search/jobs/{job_id}/stream")
async def paper_library_search_job_stream(request: Request, profile: str, job_id: str):
    _paper_library_profile_dir(profile, request)
    with _PAPER_LIBRARY_SEARCH_JOBS_LOCK:
        job = _PAPER_LIBRARY_SEARCH_JOBS.get(job_id)
        if not job or job.get("profile") != profile:
            raise HTTPException(status_code=404, detail="search job not found")

    async def event_generator():
        last_seq = 0
        sent_initial = False
        while True:
            with _PAPER_LIBRARY_SEARCH_JOBS_LOCK:
                current = _PAPER_LIBRARY_SEARCH_JOBS.get(job_id)
                if not current or current.get("profile") != profile:
                    yield _sse_event("error", {"ok": False, "error": "search job not found"})
                    break
                snapshot = _paper_library_search_job_snapshot(current)
                result = current.get("result") if current.get("status") == "done" else None
                events = list(snapshot.get("events") or [])

            if not sent_initial:
                yield _sse_event("job", {"ok": True, "job": snapshot, "result": result})
                sent_initial = True

            for event in events:
                if not isinstance(event, dict):
                    continue
                seq = _nonnegative_int(event.get("seq"))
                if seq <= last_seq:
                    continue
                payload = {"ok": True, "job": snapshot, "event": event}
                if result is not None:
                    payload["result"] = result
                yield _sse_event("progress", payload)
                last_seq = max(last_seq, seq)

            status = _clean_text(snapshot.get("status"))
            if status in {"done", "failed", "cancelled"}:
                yield _sse_event(
                    "result",
                    {
                        "ok": status != "failed",
                        "job": snapshot,
                        "result": result,
                    },
                )
                break
            if await request.is_disconnected():
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/research/{profile}/paper-library/search/jobs/{job_id}/cancel")
async def paper_library_search_job_cancel(request: Request, profile: str, job_id: str):
    _same_origin_mutation(request)
    _paper_library_profile_dir(profile, request)
    with _PAPER_LIBRARY_SEARCH_JOBS_LOCK:
        job = _PAPER_LIBRARY_SEARCH_JOBS.get(job_id)
        if not job or job.get("profile") != profile:
            raise HTTPException(status_code=404, detail="search job not found")
        status = _clean_text(job.get("status"))
        if status in {"done", "failed", "cancelled"}:
            snapshot = _paper_library_search_job_snapshot(job)
            return JSONResponse({"ok": True, "job": snapshot, "job_id": job_id})
        job["cancel_requested"] = True
        job["status"] = "cancelling"
        job["phase"] = "cancelling"
        job["message"] = "Cancelling paper search."
        cancel_event = job.get("_cancel_event")
        if hasattr(cancel_event, "set") and callable(cancel_event.set):
            cancel_event.set()
    _append_paper_library_search_job_event(
        job_id,
        {"event": "cancel_requested", "phase": "cancelling", "message": "Cancelling paper search."},
    )
    with _PAPER_LIBRARY_SEARCH_JOBS_LOCK:
        snapshot = _paper_library_search_job_snapshot(_PAPER_LIBRARY_SEARCH_JOBS[job_id])
    return JSONResponse({"ok": True, "job": snapshot, "job_id": job_id})


def _paper_library_pdf_download_warnings(profile_path: Path, source_ids: list[str]) -> list[str]:
    sources = load_research_sources(profile_path).by_id()
    warnings: list[str] = []
    for source_id in source_ids:
        source = sources.get(source_id)
        if source is None:
            continue
        metadata = source.metadata or {}
        status = _clean_text(metadata.get("pdf_download_status"))
        if status in {"failed", "skipped_needs_link_check", "skipped_no_pdf_url"}:
            error = _clean_text(metadata.get("pdf_download_error"))
            title = _clean_text(source.title) or source_id
            warnings.append(f"{title}: {error or status.replace('_', ' ')}")
    return warnings


def _paper_library_import_upload_pdf(
    profile_path: Path,
    payload: bytes,
    filename: str,
    options: dict[str, object],
) -> dict[str, object]:
    return upload_paper_library_pdf(profile_path, payload, filename, options)


@app.post("/api/research/{profile}/paper-library/import")
async def paper_library_import(request: Request, profile: str):
    _same_origin_mutation(request)
    profile_path = _paper_library_profile_dir(profile, request)
    user = _paper_library_user(profile, request)
    body = await _json_body(request)
    candidates = body.get("candidates") or body.get("results") or []
    if not isinstance(candidates, list):
        raise HTTPException(status_code=400, detail="candidates must be a list")
    selected_ids = _clean_list(body.get("selected_ids") or body.get("candidate_ids"))
    if not selected_ids:
        raise HTTPException(status_code=400, detail="selected_ids is required")
    node_id = _clean_text(body.get("node_id") or body.get("library_node_ref"))
    status = _clean_text(body.get("status")) or "inbox"
    visibility = _clean_text(body.get("visibility")) or "private"
    selected_set = set(selected_ids)
    selected_existing_ids = {
        _clean_text(item.get("imported_source_id"))
        for item in candidates
        if isinstance(item, dict)
        and (
            _clean_text(item.get("candidate_id")) in selected_set
            or _clean_text(item.get("title")) in selected_set
        )
        and _clean_text(item.get("imported_source_id"))
    }
    try:
        imported = await asyncio.to_thread(
            import_paper_search_results,
            profile_path,
            [item for item in candidates if isinstance(item, dict)],
            selected_ids,
            {
                "library_node_refs": [node_id] if node_id else [],
                "tags": _clean_list(body.get("tags")),
                "visibility": visibility,
                "status": status,
                "goal_refs": _clean_list(body.get("goal_refs")),
                "project_refs": _clean_list(body.get("project_refs")),
                "download_pdf": bool(body.get("download_pdf", True)),
                "replace_existing": _clean_bool(body.get("replace_existing"), True),
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"message": str(exc), "code": "import_failed", "retryable": False},
        ) from exc
    detail_id = imported[0] if imported else ""
    updated = [source_id for source_id in imported if source_id in selected_existing_ids]
    created = [source_id for source_id in imported if source_id not in set(updated)]
    pdf_warnings = await asyncio.to_thread(_paper_library_pdf_download_warnings, profile_path, imported)
    if created and updated:
        message = f"Imported {len(created)} and updated {len(updated)} paper{'s' if len(imported) != 1 else ''}."
    elif updated:
        message = f"Updated {len(updated)} local paper{'s' if len(updated) != 1 else ''}."
    elif created:
        message = f"Imported {len(created)} paper{'s' if len(created) != 1 else ''}."
    else:
        message = "No selected papers changed."
    if pdf_warnings:
        message = f"{message} PDF needs attention: {pdf_warnings[0]}"
    payload = await asyncio.to_thread(
        build_paper_library_payload,
        profile_path,
        current_view="all",
        current_node=node_id,
        sort_mode="recent",
        detail_id=detail_id,
        user_id=user.id,
        reader_base="",
    )
    return JSONResponse(
        {
            "ok": True,
            "imported": imported,
            "updated": updated,
            "message": message,
            "warnings": pdf_warnings,
            "payload": payload,
        }
    )


@app.post("/api/research/{profile}/paper-library/import-url")
async def paper_library_import_url(request: Request, profile: str):
    _same_origin_mutation(request)
    profile_path = _paper_library_profile_dir(profile, request)
    user = _paper_library_user(profile, request)
    body = await _json_body(request)
    url = _clean_text(body.get("url") or body.get("paper_url"))
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    node_id = _clean_text(body.get("node_id") or body.get("library_node_ref"))
    status = _clean_text(body.get("status")) or "inbox"
    visibility = _clean_text(body.get("visibility")) or "private"
    try:
        source_id = await asyncio.to_thread(
            import_paper_url,
            profile_path,
            url,
            {
                "title": _clean_text(body.get("title") or body.get("title_hint")),
                "library_node_refs": [node_id] if node_id else [],
                "tags": _clean_list(body.get("tags")),
                "visibility": visibility,
                "status": status,
                "goal_refs": _clean_list(body.get("goal_refs")),
                "project_refs": _clean_list(body.get("project_refs")),
                "download_pdf": bool(body.get("download_pdf", True)),
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"message": str(exc), "code": "url_import_failed", "retryable": False},
        ) from exc
    imported = [source_id] if source_id else []
    pdf_warnings = await asyncio.to_thread(_paper_library_pdf_download_warnings, profile_path, imported)
    message = "Imported paper from URL."
    if pdf_warnings:
        message = f"{message} PDF needs attention: {pdf_warnings[0]}"
    payload = await asyncio.to_thread(
        build_paper_library_payload,
        profile_path,
        current_view="all",
        current_node=node_id,
        sort_mode="recent",
        detail_id=source_id,
        user_id=user.id,
        reader_base="",
    )
    return JSONResponse(
        {
            "ok": True,
            "imported": imported,
            "source_id": source_id,
            "message": message,
            "warnings": pdf_warnings,
            "payload": payload,
        }
    )


@app.post("/api/research/{profile}/papers/{source_id}/pdf-retry")
async def paper_library_pdf_retry(request: Request, profile: str, source_id: str):
    """Re-attempt the open-access PDF download for a previously-failed source."""

    _same_origin_mutation(request)
    profile_path = _paper_library_profile_dir(profile, request)
    user = _paper_library_user(profile, request)
    body = await _json_body(request)
    override_url = _clean_text(body.get("pdf_url"))
    try:
        outcome = await asyncio.to_thread(
            ensure_paper_pdf_downloaded,
            profile_path,
            source_id,
            pdf_url=override_url,
            error_prefix="PDF retry failed",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail={"message": str(exc), "code": "source_not_found", "retryable": False},
        ) from exc
    library_payload = await asyncio.to_thread(
        build_paper_library_payload,
        profile_path,
        current_view="all",
        detail_id=source_id,
        focus="artifacts",
        user_id=user.id,
        reader_base="",
    )
    status = _clean_text(outcome.get("status"))
    ok = status == "downloaded"
    return JSONResponse(
        {
            "ok": ok,
            "status": status,
            "source_id": source_id,
            "error": _clean_text(outcome.get("error")),
            "asset_ref": _clean_text(outcome.get("asset_ref")),
            "byte_size": outcome.get("byte_size", 0),
            "payload": library_payload,
        }
    )


@app.get("/api/research/{profile}/papers/{source_id}")
async def paper_library_paper(request: Request, profile: str, source_id: str):
    profile_path = _paper_library_profile_dir(profile, request)
    user = _paper_library_user(profile, request)
    payload = build_paper_library_payload(
        profile_path,
        detail_id=source_id,
        user_id=user.id,
        reader_base="",
    )
    detail = payload.get("detail") if isinstance(payload.get("detail"), dict) else {}
    if detail.get("source_id") != source_id and detail.get("id") != source_id:
        raise HTTPException(status_code=404, detail="source not found")
    return JSONResponse({"ok": True, "paper": detail})


@app.post("/api/research/{profile}/papers/{source_id}/reader-token")
async def paper_library_reader_token(request: Request, profile: str, source_id: str):
    _paper_library_profile_dir(profile, request)
    user = _paper_library_user(profile, request)
    token = mint_reader_token(user.id, profile, source_id)
    return JSONResponse(
        {
            "ok": True,
            "token": token,
            "reader_url": f"/reader/view/{quote(source_id, safe='')}?token={quote(token, safe='')}",
        }
    )


@app.post("/api/research/{profile}/paper-library/upload")
async def paper_library_upload_pdf(
    request: Request,
    profile: str,
    file: UploadFile = File(...),
    title: str = Form(""),
    node_id: str = Form(""),
    status: str = Form("reading"),
    visibility: str = Form("private"),
    tags: str = Form(""),
    allow_duplicates: str = Form(""),
):
    _same_origin_mutation(request)
    profile_path = _paper_library_profile_dir(profile, request)
    user = _paper_library_user(profile, request)
    filename = _clean_text(file.filename) or "paper.pdf"
    try:
        payload = await file.read()
    finally:
        await file.close()
    try:
        outcome = await asyncio.to_thread(
            _paper_library_import_upload_pdf,
            profile_path,
            payload,
            filename,
            {
                "title": title,
                "library_node_refs": [node_id] if _clean_text(node_id) else [],
                "tags": tags,
                "visibility": visibility,
                "status": status,
                "allow_duplicates": _clean_text(allow_duplicates).lower() in {"1", "true", "yes"},
            },
        )
    except PaperImportError as exc:
        raise HTTPException(
            status_code=400,
            detail={"message": str(exc), "code": exc.code, "retryable": exc.retryable},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"message": str(exc), "code": "import_failed", "retryable": False},
        ) from exc
    source_id = _clean_text(outcome.get("source_id"))
    duplicate = bool(outcome.get("duplicate"))
    library_payload = await asyncio.to_thread(
        build_paper_library_payload,
        profile_path,
        current_view="all",
        current_node=_clean_text(node_id),
        sort_mode="recent",
        detail_id=source_id,
        focus="artifacts",
        user_id=user.id,
        reader_base="",
    )
    message = (
        "Already imported. Reusing the existing paper."
        if duplicate
        else "Uploaded and imported PDF."
    )
    return JSONResponse(
        {
            "ok": True,
            "imported": [source_id],
            "source_id": source_id,
            "duplicate": duplicate,
            "message": message,
            "payload": library_payload,
        }
    )


@app.post("/api/research/{profile}/papers/{source_id}/pdf-upload")
async def paper_library_pdf_upload(
    request: Request,
    profile: str,
    source_id: str,
    file: UploadFile = File(...),
):
    _same_origin_mutation(request)
    profile_path = _paper_library_profile_dir(profile, request)
    user = _paper_library_user(profile, request)
    filename = _clean_text(file.filename) or "paper.pdf"
    try:
        payload = await file.read()
    finally:
        await file.close()
    try:
        await asyncio.to_thread(
            import_paper_pdf,
            profile_path,
            source_id,
            payload,
            filename,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"message": str(exc), "code": "source_not_found", "retryable": False},
        ) from exc
    except PaperImportError as exc:
        raise HTTPException(
            status_code=400,
            detail={"message": str(exc), "code": exc.code, "retryable": exc.retryable},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"message": str(exc), "code": "invalid_pdf", "retryable": False},
        ) from exc
    library_payload = await asyncio.to_thread(
        build_paper_library_payload,
        profile_path,
        current_view="all",
        detail_id=source_id,
        focus="artifacts",
        user_id=user.id,
        reader_base="",
    )
    return JSONResponse(
        {
            "ok": True,
            "source_id": source_id,
            "message": "Uploaded PDF.",
            "payload": library_payload,
        }
    )


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
        "Cache-Control": "private, max-age=86400",
        "ETag": f'W/"{path.stat().st_mtime_ns:x}-{size:x}"',
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
            "Cache-Control": "private, max-age=86400",
            "ETag": f'W/"{path.stat().st_mtime_ns:x}-{path.stat().st_size:x}"',
            "Content-Length": str(path.stat().st_size),
        },
    )


@app.get(f"{READER_PREFIX}/api/{{source_id}}/payload")
async def reader_payload(request: Request, source_id: str, page: int | None = None):
    ctx = _request_context(request, source_id)
    full_translation = _clean_bool(request.query_params.get("full_translation"), False)
    full_document_param = request.query_params.get("full_document")
    full_document: bool | None
    if full_document_param is None:
        full_document = None  # default = honor env / always full
    else:
        full_document = _clean_bool(full_document_param, True)
    payload = _payload_for_context(
        ctx,
        page=page,
        requested_pages=_query_pages(request),
        full_translation=full_translation,
        full_document=full_document,
    )
    target_lang = str((payload.get("settings") or {}).get("target_lang") or "zh")
    etag = _payload_etag(payload, target_lang=target_lang)
    headers = {
        "ETag": etag,
        "Cache-Control": "private, max-age=0, must-revalidate",
    }
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return JSONResponse(payload, headers=headers)


@app.get(f"{READER_PREFIX}/api/{{source_id}}/page-preview/{{page}}")
async def reader_page_preview(request: Request, source_id: str, page: int):
    ctx = _request_context(request, source_id)
    return JSONResponse(
        render_paper_page_preview(ctx.profile_path, source_id, max(1, page), max_width=1100),
        headers={"Cache-Control": "private, max-age=86400"},
    )


@app.get(f"{READER_PREFIX}/api/{{source_id}}/page-text-layer/{{page}}")
async def reader_page_text_layer(request: Request, source_id: str, page: int):
    ctx = _request_context(request, source_id)
    return JSONResponse(
        _paper_page_text_layer(ctx.profile_path, source_id, max(1, page)),
        headers={"Cache-Control": "private, max-age=86400"},
    )


@app.get(f"{READER_PREFIX}/api/{{source_id}}/translations/bulk")
async def reader_translations_bulk(request: Request, source_id: str):
    ctx = _request_context(request, source_id)
    target_lang = (request.query_params.get("target_lang") or "zh").strip() or "zh"
    inbox = load_research_sources(ctx.profile_path)
    source = inbox.by_id().get(ctx.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")
    metadata = dict(source.metadata or {})
    if not target_lang or target_lang == "zh":
        target_lang = str(metadata.get("target_lang") or target_lang or "zh")
    body, etag = paper_translations_bulk(ctx.profile_path, ctx.source_id, target_lang=target_lang)
    headers = {
        "ETag": etag,
        "Cache-Control": "private, max-age=30",
    }
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return JSONResponse(body, headers=headers)


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
