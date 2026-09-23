"""Workshop (remote terminal) endpoint — Phase 0.5 Step 2.

Exposes the ttyd web terminal to the SPA「车间」page:

- ``url`` — the browser-facing iframe URL. From ``NBLANE_WORKSHOP_URL``;
  default ``/terminal/`` (same-origin, the production Caddy subpath proxy
  with basic_auth). Local dev has no such proxy, so set
  ``NBLANE_WORKSHOP_URL=http://127.0.0.1:7668/`` there (``.env`` is sourced
  by ``scripts/dev-web.sh``).
- ``reachable`` — server-side probe of the ttyd process itself, so the page
  can show start instructions instead of a dead iframe. Probe target comes
  from ``NBLANE_WORKSHOP_PROBE_URL`` (default ``http://127.0.0.1:7668``);
  ttyd only ever binds loopback, so probing it server-side works whether or
  not the browser-facing URL goes through Caddy.

The probe goes through an injectable ``http_get`` seam (overridable via
``app.state.workshop_http_get``) so tests never touch the network; any
failure yields ``reachable=false``, never a 5xx. Results are cached for 60s
in ``app.state`` (single-process uvicorn), same as ``system/assistant``.

See docs/zh/dev/phase0.5-remote-terminal.md.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from nblane.web_api.auth import require_user

PROBE_TIMEOUT_SECONDS = 5.0
CACHE_TTL_SECONDS = 60.0

DEFAULT_WORKSHOP_URL = "/terminal/"
DEFAULT_PROBE_URL = "http://127.0.0.1:7668"
WORKSHOP_URL_ENV = "NBLANE_WORKSHOP_URL"
PROBE_URL_ENV = "NBLANE_WORKSHOP_PROBE_URL"

router = APIRouter(prefix="/api/v1")


class WorkshopStatusResponse(BaseModel):
    """GET /api/v1/system/workshop payload."""

    url: str = DEFAULT_WORKSHOP_URL
    reachable: bool = False
    checked_at: str = ""


HttpGetFn = Callable[..., Any]


def _default_http_get(url: str, timeout: float) -> Any:
    import httpx

    return httpx.get(url, timeout=timeout)


def workshop_url() -> str:
    """Browser-facing terminal URL (env override, else same-origin path)."""
    return os.getenv(WORKSHOP_URL_ENV, "").strip() or DEFAULT_WORKSHOP_URL


def collect_workshop_status(
    *,
    http_get: HttpGetFn = _default_http_get,
    probe_url: str | None = None,
) -> WorkshopStatusResponse:
    """Probe ttyd (guarded) and assemble the status payload."""
    checked_at = datetime.now(timezone.utc).isoformat()
    probe = (
        probe_url
        if probe_url is not None
        else os.getenv(PROBE_URL_ENV, "").strip() or DEFAULT_PROBE_URL
    )
    reachable = False
    try:
        resp = http_get(probe, timeout=PROBE_TIMEOUT_SECONDS)
        # ttyd answers 200 on /; any HTTP response proves the process is up
        # (a 401/426 from a proxy in front of it still means "reachable").
        reachable = 100 <= getattr(resp, "status_code", 0) < 600
    except Exception:
        reachable = False
    return WorkshopStatusResponse(
        url=workshop_url(),
        reachable=reachable,
        checked_at=checked_at,
    )


@router.get(
    "/system/workshop",
    response_model=WorkshopStatusResponse,
    dependencies=[Depends(require_user)],
)
def get_workshop_status(request: Request) -> WorkshopStatusResponse:
    """Workshop terminal config + liveness (cached 60s in app.state)."""
    cached = getattr(request.app.state, "workshop_status_cache", None)
    now = time.monotonic()
    if cached is not None and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]
    http_get = getattr(request.app.state, "workshop_http_get", _default_http_get)
    status = collect_workshop_status(http_get=http_get)
    request.app.state.workshop_status_cache = (now, status)
    return status
