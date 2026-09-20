"""Assistant (OpenClaw) status endpoint — L4 step 2: status card + deep link.

Read-only probes only; nothing here mutates the live gateway:

- ``shutil.which("openclaw")`` — binary presence
- ``openclaw --version`` — installed version
- ``GET http://127.0.0.1:18789/readyz`` — gateway readiness + uptime
- ``openclaw mcp list`` — whether the nblane MCP server is registered
- ``openclaw automations list --all --json`` — automation counts

Every subprocess/HTTP call goes through injectable seams (``which`` /
``runner`` / ``http_get``, overridable per-app via ``app.state``) so tests
never touch the real system. Each probe is individually guarded (5s
timeout; failure yields a null field, never a 5xx). When the binary is
absent the endpoint answers 200 with ``available=false`` and all probe
fields null. Results are cached for 60s in ``app.state`` (single-process
uvicorn).

``console_url`` comes from ``NBLANE_OPENCLAW_CONSOLE_URL`` (default
``http://127.0.0.1:18789/``). In production this becomes the Caddy
subpath reverse proxy (``https://<domain>/openclaw/``) once L4 step 1
lands — see docs/zh/architecture/openclaw-deep-integration.md §6.2.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from nblane.web_api.auth import require_user

PROBE_TIMEOUT_SECONDS = 5.0
CACHE_TTL_SECONDS = 60.0

DEFAULT_GATEWAY_BASE = "http://127.0.0.1:18789"
DEFAULT_CONSOLE_URL = "http://127.0.0.1:18789/"
CONSOLE_URL_ENV = "NBLANE_OPENCLAW_CONSOLE_URL"

router = APIRouter(prefix="/api/v1")


class AssistantGatewayStatus(BaseModel):
    """Gateway readiness probe (GET /readyz)."""

    ready: bool = False
    uptime_ms: int | None = None


class AssistantAutomationsStatus(BaseModel):
    """Automation counts from ``openclaw automations list --all --json``."""

    total: int = 0
    enabled: int = 0


class AssistantStatusResponse(BaseModel):
    """GET /api/v1/system/assistant payload."""

    available: bool
    version: str | None = None
    gateway: AssistantGatewayStatus | None = None
    mcp_nblane_registered: bool | None = None
    automations: AssistantAutomationsStatus | None = None
    console_url: str = DEFAULT_CONSOLE_URL
    checked_at: str = ""


RunnerFn = Callable[..., subprocess.CompletedProcess]
HttpGetFn = Callable[..., Any]


def _default_runner(argv: list[str], timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def _default_http_get(url: str, timeout: float) -> Any:
    import httpx

    return httpx.get(url, timeout=timeout)


def _probe_version(runner: RunnerFn) -> str | None:
    """Installed openclaw version, or None on any failure."""
    try:
        proc = runner(["openclaw", "--version"], timeout=PROBE_TIMEOUT_SECONDS)
    except Exception:
        return None
    if getattr(proc, "returncode", 1) != 0:
        return None
    text = (getattr(proc, "stdout", "") or "").strip()
    return text or None


def _probe_gateway(http_get: HttpGetFn, gateway_base: str) -> AssistantGatewayStatus:
    """Gateway readiness; unreachable/timeout yields ready=false."""
    try:
        resp = http_get(f"{gateway_base}/readyz", timeout=PROBE_TIMEOUT_SECONDS)
    except Exception:
        return AssistantGatewayStatus(ready=False, uptime_ms=None)
    ready = getattr(resp, "status_code", 0) == 200
    uptime_ms: int | None = None
    body: Any = None
    try:
        body = resp.json()
    except Exception:
        body = None
    if isinstance(body, dict):
        raw = body.get("uptime_ms")
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            uptime_ms = int(raw)
    return AssistantGatewayStatus(ready=ready, uptime_ms=uptime_ms)


def _probe_mcp_registered(runner: RunnerFn) -> bool | None:
    """Whether the nblane MCP server shows up in ``openclaw mcp list``."""
    try:
        proc = runner(["openclaw", "mcp", "list"], timeout=PROBE_TIMEOUT_SECONDS)
    except Exception:
        return None
    if getattr(proc, "returncode", 1) != 0:
        return None
    stdout = getattr(proc, "stdout", "") or ""
    return any("nblane" in line for line in stdout.splitlines())


def _probe_automations(runner: RunnerFn) -> AssistantAutomationsStatus | None:
    """Automation counts, or None when the CLI/JSON output is unusable."""
    try:
        proc = runner(
            ["openclaw", "automations", "list", "--all", "--json"],
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except Exception:
        return None
    if getattr(proc, "returncode", 1) != 0:
        return None
    try:
        data = json.loads(getattr(proc, "stdout", "") or "")
    except ValueError:
        return None
    if isinstance(data, dict):
        items = data.get("automations") or data.get("items") or []
    elif isinstance(data, list):
        items = data
    else:
        return None
    enabled = sum(
        1 for item in items if isinstance(item, dict) and item.get("enabled")
    )
    return AssistantAutomationsStatus(total=len(items), enabled=enabled)


def collect_assistant_status(
    *,
    which: Callable[[str], str | None] = shutil.which,
    runner: RunnerFn = _default_runner,
    http_get: HttpGetFn = _default_http_get,
    gateway_base: str = DEFAULT_GATEWAY_BASE,
    console_url: str | None = None,
) -> AssistantStatusResponse:
    """Run all probes (each guarded) and assemble the status payload."""
    checked_at = datetime.now(timezone.utc).isoformat()
    console = (
        console_url
        if console_url is not None
        else os.getenv(CONSOLE_URL_ENV, "").strip() or DEFAULT_CONSOLE_URL
    )
    if which("openclaw") is None:
        return AssistantStatusResponse(
            available=False,
            console_url=console,
            checked_at=checked_at,
        )
    return AssistantStatusResponse(
        available=True,
        version=_probe_version(runner),
        gateway=_probe_gateway(http_get, gateway_base),
        mcp_nblane_registered=_probe_mcp_registered(runner),
        automations=_probe_automations(runner),
        console_url=console,
        checked_at=checked_at,
    )


def _seams(request: Request) -> dict[str, Any]:
    """Probe seams, overridable per-app via ``app.state.assistant_*``."""
    state = request.app.state
    return {
        "which": getattr(state, "assistant_which", shutil.which),
        "runner": getattr(state, "assistant_runner", _default_runner),
        "http_get": getattr(state, "assistant_http_get", _default_http_get),
    }


@router.get(
    "/system/assistant",
    response_model=AssistantStatusResponse,
    dependencies=[Depends(require_user)],
)
def get_assistant_status(request: Request) -> AssistantStatusResponse:
    """Assistant status card payload (cached 60s in app.state)."""
    cached = getattr(request.app.state, "assistant_status_cache", None)
    now = time.monotonic()
    if cached is not None and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]
    status = collect_assistant_status(**_seams(request))
    request.app.state.assistant_status_cache = (now, status)
    return status
