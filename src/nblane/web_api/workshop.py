"""Workshop (remote terminal) endpoints.

``GET /system/workshop`` feeds the SPA「车间」page:

- ``url`` — the browser-facing terminal URL. From ``NBLANE_WORKSHOP_URL``;
  default ``/terminal/``, the authenticated same-origin proxy this app
  serves itself (``web_api/workshop_terminal.py``).
- ``reachable`` — server-side probe of ttyd on loopback
  (``NBLANE_WORKSHOP_PROBE_URL``, else ``http://127.0.0.1:<NBLANE_WORKSHOP_PORT|7668>``).
- ``admin`` — the terminal, key bar and input box are admin-only.

The probe goes through an injectable ``http_get`` seam (overridable via
``app.state.workshop_http_get``) so tests never touch the network; any
failure yields ``reachable=false``, never a 5xx. Results are cached for 60s
in ``app.state`` (single-process uvicorn); management actions clear it.

The mobile key bar and input box (``/system/workshop/keys|input``) inject
whitelisted keys / pasted text with tmux. Settings → 车间 manages the
service itself (``/settings/workshop*``, ``core/workshop_service.py``).

See docs/zh/dev/phase0.5-remote-terminal.md.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from nblane.core import workshop_service
from nblane.web_api.auth import CurrentUser, require_user
from nblane.web_api.routes_v1 import ApiError, require_admin
from nblane.web_api.schemas import ErrorResponse

PROBE_TIMEOUT_SECONDS = 5.0
CACHE_TTL_SECONDS = 60.0

DEFAULT_WORKSHOP_URL = "/terminal/"
WORKSHOP_URL_ENV = "NBLANE_WORKSHOP_URL"

router = APIRouter(prefix="/api/v1")
_RESPONSES = {400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}}


class WorkshopStatusResponse(BaseModel):
    """GET /api/v1/system/workshop payload."""

    url: str = DEFAULT_WORKSHOP_URL
    reachable: bool = False
    checked_at: str = ""
    admin: bool = False
    font_size_mobile: int = workshop_service.DEFAULTS["font_size_mobile"]
    font_size_desktop: int = workshop_service.DEFAULTS["font_size_desktop"]


class WorkshopKeysRequest(BaseModel):
    keys: list[str] = Field(min_length=1, max_length=20)


class WorkshopInputRequest(BaseModel):
    text: str = Field(default="", max_length=workshop_service.MAX_INPUT_CHARS)
    submit: bool = True


class WorkshopOkResponse(BaseModel):
    ok: bool = True


class WorkshopSettings(BaseModel):
    font_size_mobile: int
    font_size_desktop: int
    scrollback: int
    renderer: str
    rescale_glyphs: bool
    history_limit: int
    mouse: bool
    native_scroll: bool
    escape_time_ms: int
    status_bar: bool
    cwd: str


class WorkshopSettingsPatch(BaseModel):
    font_size_mobile: int | None = None
    font_size_desktop: int | None = None
    scrollback: int | None = None
    renderer: str | None = None
    rescale_glyphs: bool | None = None
    history_limit: int | None = None
    mouse: bool | None = None
    native_scroll: bool | None = None
    escape_time_ms: int | None = None
    status_bar: bool | None = None
    cwd: str | None = None


class WorkshopUnitState(BaseModel):
    installed: bool = False
    active_state: str = ""
    sub_state: str = ""
    since: str = ""
    restarts: int = 0


class WorkshopInstallState(BaseModel):
    status: str = ""
    phase: str = ""
    error: str = ""
    started_at: float = 0.0


class HappyStatus(BaseModel):
    installed: bool = False
    path: str = ""
    paired: bool = False
    daemon_running: bool = False


class WorkshopApplyResult(BaseModel):
    tmux_reloaded: bool = False
    ttyd_restarted: bool = False
    reattach_needed: bool = False


class WorkshopServiceStatus(BaseModel):
    """GET /api/v1/settings/workshop payload (admin)."""

    state: str
    reachable: bool
    managed: bool
    unit: str
    unit_state: WorkshopUnitState
    port: int
    upstream: str
    ttyd_version: str
    ttyd_installed: bool
    ttyd_path: str
    ttyd_download_url: str
    ttyd_sha256: str
    arch: str
    tmux_path: str
    tmux_version: str
    tmux_socket: str
    session: str
    session_alive: bool
    user_manager: bool
    autostart: bool
    service_dir: str
    caddy_legacy_route: bool
    settings: WorkshopSettings
    defaults: WorkshopSettings
    install: WorkshopInstallState
    blocker: str
    happy: HappyStatus
    applied: WorkshopApplyResult | None = None


class WorkshopLogsResponse(BaseModel):
    text: str = ""


HttpGetFn = Callable[..., Any]


def _default_http_get(url: str, timeout: float) -> Any:
    import httpx

    return httpx.get(url, timeout=timeout, trust_env=False)


def workshop_url() -> str:
    """Browser-facing terminal URL (env override, else the same-origin proxy)."""
    return os.getenv(WORKSHOP_URL_ENV, "").strip() or DEFAULT_WORKSHOP_URL


def collect_workshop_status(
    *,
    http_get: HttpGetFn = _default_http_get,
    probe_url: str | None = None,
) -> WorkshopStatusResponse:
    """Probe ttyd (guarded) and assemble the status payload."""
    checked_at = datetime.now(timezone.utc).isoformat()
    # upstream_url() honours NBLANE_WORKSHOP_PROBE_URL, then NBLANE_WORKSHOP_PORT.
    probe = probe_url if probe_url is not None else workshop_service.upstream_url()
    reachable = False
    try:
        resp = http_get(probe, timeout=PROBE_TIMEOUT_SECONDS)
        # ttyd answers 200 on /; any HTTP response proves the process is up.
        reachable = 100 <= getattr(resp, "status_code", 0) < 600
    except Exception:
        reachable = False
    values = workshop_service.settings()
    return WorkshopStatusResponse(
        url=workshop_url(),
        reachable=reachable,
        checked_at=checked_at,
        font_size_mobile=values["font_size_mobile"],
        font_size_desktop=values["font_size_desktop"],
    )


def _clear_cache(request: Request) -> None:
    request.app.state.workshop_status_cache = None


@router.get("/system/workshop", response_model=WorkshopStatusResponse)
def get_workshop_status(request: Request, user: CurrentUser = Depends(require_user)) -> WorkshopStatusResponse:
    """Workshop terminal config + liveness (cached 60s in app.state)."""
    cached = getattr(request.app.state, "workshop_status_cache", None)
    now = time.monotonic()
    if cached is not None and now - cached[0] < CACHE_TTL_SECONDS:
        status = cached[1]
    else:
        http_get = getattr(request.app.state, "workshop_http_get", _default_http_get)
        status = collect_workshop_status(http_get=http_get)
        request.app.state.workshop_status_cache = (now, status)
    return status.model_copy(update={"admin": user.role == "admin"})


def _act(action: Callable[[], Any], code: str) -> Any:
    try:
        return action()
    except workshop_service.WorkshopServiceError as exc:
        raise ApiError(400, code, str(exc)) from exc


@router.post("/system/workshop/keys", response_model=WorkshopOkResponse, responses=_RESPONSES)
def send_workshop_keys(body: WorkshopKeysRequest, _user: CurrentUser = Depends(require_admin)) -> WorkshopOkResponse:
    """Mobile key bar: send whitelisted keys (Esc, Ctrl-C, arrows…) to the terminal."""
    _act(lambda: workshop_service.send_keys(body.keys), "workshop_keys_failed")
    return WorkshopOkResponse()


@router.post("/system/workshop/input", response_model=WorkshopOkResponse, responses=_RESPONSES)
def send_workshop_input(body: WorkshopInputRequest, _user: CurrentUser = Depends(require_admin)) -> WorkshopOkResponse:
    """Mobile input box: paste text typed with the phone's own IME, optionally + Enter."""
    _act(lambda: workshop_service.send_text(body.text, submit=body.submit), "workshop_input_failed")
    return WorkshopOkResponse()


# ------------------------------------------------------------ Settings → 车间


def _service_status(applied: dict[str, bool] | None = None) -> WorkshopServiceStatus:
    return WorkshopServiceStatus(**workshop_service.status(), applied=applied)


@router.get("/settings/workshop", response_model=WorkshopServiceStatus, responses=_RESPONSES)
def get_workshop_service(_user: CurrentUser = Depends(require_admin)) -> WorkshopServiceStatus:
    """ttyd/tmux service state, terminal settings and Happy CLI presence."""
    return _service_status()


@router.put("/settings/workshop", response_model=WorkshopServiceStatus, responses=_RESPONSES)
def update_workshop_settings(
    body: WorkshopSettingsPatch, request: Request, _user: CurrentUser = Depends(require_admin)
) -> WorkshopServiceStatus:
    """Save terminal settings and apply them to the running service."""
    patch = body.model_dump(exclude_none=True)
    applied = _act(lambda: workshop_service.save_settings(patch), "workshop_settings_failed")
    _clear_cache(request)
    return _service_status(applied)


@router.post("/settings/workshop/{action}", response_model=WorkshopServiceStatus, responses={**_RESPONSES, 404: {"model": ErrorResponse}})
def workshop_service_action(action: str, request: Request, _user: CurrentUser = Depends(require_admin)) -> WorkshopServiceStatus:
    """install (also takes over a hand-written unit) / start / stop / restart."""
    actions: dict[str, Callable[[], Any]] = {
        "install": workshop_service.start_install,
        "start": workshop_service.start,
        "stop": workshop_service.stop,
        "restart": workshop_service.restart,
    }
    if action not in actions:
        raise ApiError(404, "unknown_action", f"Unknown workshop action: {action}")
    _act(actions[action], f"workshop_{action}_failed")
    _clear_cache(request)
    return _service_status()


@router.delete("/settings/workshop", response_model=WorkshopServiceStatus, responses=_RESPONSES)
def uninstall_workshop(
    request: Request, end_sessions: bool = False, _user: CurrentUser = Depends(require_admin)
) -> WorkshopServiceStatus:
    """Remove the unit; ``end_sessions`` also ends everything running in tmux."""
    _act(lambda: workshop_service.uninstall(end_running_sessions=end_sessions), "workshop_uninstall_failed")
    _clear_cache(request)
    return _service_status()


@router.get("/settings/workshop/logs", response_model=WorkshopLogsResponse, responses=_RESPONSES)
def workshop_logs(_user: CurrentUser = Depends(require_admin)) -> WorkshopLogsResponse:
    return WorkshopLogsResponse(text=workshop_service.logs())
