"""Assistant (OpenClaw) status endpoint — L4 step 2: status card + deep link.

Read-only probes only; nothing here mutates the live gateway:

- ``shutil.which("openclaw")`` — binary presence
- ``openclaw --version`` — installed version
- ``GET http://127.0.0.1:<port>/readyz`` — gateway readiness + uptime
- the OpenClaw config file — whether the nblane MCP server is registered
  (read directly; ``openclaw mcp list`` takes >5s and is only a fallback
  for non-JSON configs)
- ``openclaw automations list --all --json`` — automation counts
- the OpenClaw workspace — whether the nblane skill (``skills/nblane/SKILL.md``)
  and the HTTP client (``skills/bin/nblane_api*``) match this nblane version

Every subprocess/HTTP/config call goes through injectable seams (``which`` /
``runner`` / ``http_get`` / ``read_config``, overridable per-app via ``app.state``) so tests
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
from pathlib import Path
from typing import Any, Callable, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from nblane.core import openclaw_setup
from nblane.web_api.auth import require_user

PROBE_TIMEOUT_SECONDS = 5.0
MCP_LIST_TIMEOUT_SECONDS = 15.0
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


SyncState = Literal["synced", "outdated", "missing"]


class AssistantChannelsStatus(BaseModel):
    """How the assistant reaches nblane: the skill (rules) and the HTTP client.

    ``synced`` = the workspace copy equals this nblane version; ``outdated``
    = present but older (re-run 「接入 nblane」); ``missing`` = not installed.
    """

    skill: SyncState | None = None
    http_client: SyncState | None = None


class AssistantStatusResponse(BaseModel):
    """GET /api/v1/system/assistant payload."""

    available: bool
    version: str | None = None
    gateway: AssistantGatewayStatus | None = None
    mcp_nblane_registered: bool | None = None
    automations: AssistantAutomationsStatus | None = None
    channels: AssistantChannelsStatus | None = None
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
        # OpenClaw 2026.9 answers camelCase ``uptimeMs``.
        raw = body.get("uptimeMs", body.get("uptime_ms"))
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            uptime_ms = int(raw)
    return AssistantGatewayStatus(ready=ready, uptime_ms=uptime_ms)


def _probe_mcp_registered(
    runner: RunnerFn,
    read_config: Callable[[], dict[str, Any] | None] = openclaw_setup.read_config,
    prefix: list[str] | None = None,
) -> bool | None:
    """Whether the nblane MCP server is registered with OpenClaw.

    Reads ``mcp.servers.nblane`` from the config file; only when the file
    is not plain JSON does it fall back to ``openclaw mcp list``.
    """
    try:
        config = read_config()
    except Exception:
        config = None
    if config is not None:
        return openclaw_setup._mcp_entry(config) is not None
    try:
        proc = runner(
            [*(prefix or ["openclaw"]), "mcp", "list"],
            timeout=MCP_LIST_TIMEOUT_SECONDS,
        )
    except Exception:
        return None
    if getattr(proc, "returncode", 1) != 0:
        return None
    stdout = getattr(proc, "stdout", "") or ""
    return any("nblane" in line for line in stdout.splitlines())


def _probe_automations(
    runner: RunnerFn, prefix: list[str] | None = None
) -> AssistantAutomationsStatus | None:
    """Automation counts, or None when the CLI/JSON output is unusable."""
    try:
        proc = runner(
            [*(prefix or ["openclaw"]), "automations", "list", "--all", "--json"],
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
        # 2026.9 wraps the list in "jobs"; older builds used automations/items.
        items = data.get("automations") or data.get("items") or data.get("jobs") or []
    elif isinstance(data, list):
        items = data
    else:
        return None
    enabled = sum(
        1 for item in items if isinstance(item, dict) and item.get("enabled")
    )
    return AssistantAutomationsStatus(total=len(items), enabled=enabled)


def _default_workspace(read_config: Callable[[], dict[str, Any] | None]) -> Path | None:
    """OpenClaw workspace from the JSON config (no CLI call), else the default."""
    try:
        config = read_config()
    except Exception:
        config = None
    found = openclaw_setup._workspace_from_config(config) if config else None
    if found is not None:
        return found
    default = openclaw_setup.state_dir() / "workspace"
    return default if default.is_dir() else None


def _sync_state(installed: list[Path], shipped: list[Path]) -> SyncState:
    if not all(path.is_file() for path in installed):
        return "missing"
    same = all(
        dst.read_bytes() == src.read_bytes()
        for dst, src in zip(installed, shipped)
        if src.is_file()
    )
    return "synced" if same else "outdated"


def _probe_channels(workspace: Path | None) -> AssistantChannelsStatus:
    """Compare the workspace's nblane skill + HTTP client with this release."""
    if workspace is None:
        return AssistantChannelsStatus()
    skills = workspace / "skills"
    shipped = openclaw_setup.REPO_SCRIPTS / "skills"
    try:
        skill = _sync_state([skills / "nblane" / "SKILL.md"], [shipped / "nblane" / "SKILL.md"])
        client = _sync_state(
            [skills / "bin" / "nblane_api.py", skills / "bin" / "nblane_api"],
            [shipped / "bin" / "nblane_api.py"],
        )
    except OSError:
        return AssistantChannelsStatus()
    return AssistantChannelsStatus(skill=skill, http_client=client)


def collect_assistant_status(
    *,
    which: Callable[[str], str | None] = shutil.which,
    runner: RunnerFn = _default_runner,
    http_get: HttpGetFn = _default_http_get,
    read_config: Callable[[], dict[str, Any] | None] = openclaw_setup.read_config,
    gateway_base: str | None = None,
    console_url: str | None = None,
    workspace: Callable[[], Path | None] | None = None,
) -> AssistantStatusResponse:
    """Run all probes (each guarded) and assemble the status payload.

    CLI calls, gateway port and config honour ``NBLANE_OPENCLAW_PROFILE``
    so the isolated dev stack never reports the production gateway.
    """
    prefix = openclaw_setup.cli_prefix()
    if gateway_base is None:
        gateway_base = f"http://127.0.0.1:{openclaw_setup.gateway_port()}"
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
        mcp_nblane_registered=_probe_mcp_registered(runner, read_config, prefix),
        automations=_probe_automations(runner, prefix),
        channels=_probe_channels(
            (workspace or (lambda: _default_workspace(read_config)))()
        ),
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
        "read_config": getattr(state, "assistant_read_config", openclaw_setup.read_config),
        "workspace": getattr(state, "assistant_workspace", None),
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
