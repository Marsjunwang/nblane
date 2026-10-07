"""Authenticated reverse proxy for the workshop terminal (``/terminal/``).

The browser loads ttyd through this app instead of a Caddy basic_auth route,
so the nblane session cookie is the only gate (Phase 0.5 Step 3). A shell is
deployment-wide power, so every request requires an **admin**.

- ``GET /terminal/<path>`` → ttyd ``/<path>`` (index page, ``/token``).
- ``WS /terminal/ws`` → ttyd ``/ws`` (subprotocol ``tty``), frames relayed
  verbatim in both directions.

ttyd derives its WebSocket and token URLs from ``location.pathname``, so the
page works under the ``/terminal/`` prefix without any rewriting. The
WebSocket additionally rejects cross-origin handshakes (cookie-bearing
cross-site WebSocket hijacking).
"""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request, Response, WebSocket
from fastapi.responses import RedirectResponse
from starlette.websockets import WebSocketDisconnect, WebSocketState

from nblane.core import workshop_service
from nblane.web_api.auth import CurrentUser, _resolve_request_user
from nblane.web_api.routes_v1 import require_admin

router = APIRouter(include_in_schema=False)

_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te",
    "trailers", "transfer-encoding", "upgrade", "content-length", "content-encoding",
}
_POLICY_VIOLATION = 1008
_UPSTREAM_DOWN = 1013  # "try again later": ttyd's client then reconnects


def _ws_upstream_url() -> str:
    parsed = urlparse(workshop_service.upstream_url())
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return f"{scheme}://{parsed.netloc}/ws"


def _http_get(url: str, headers: dict[str, str]) -> Any:
    import httpx

    # trust_env=False: the service's https_proxy must never see loopback traffic.
    with httpx.Client(trust_env=False, timeout=15.0) as client:
        return client.get(url, headers=headers)


@router.get("/terminal")
def terminal_slash() -> RedirectResponse:
    return RedirectResponse("/terminal/", status_code=308)


@router.get("/terminal/{path:path}")
def terminal_http(path: str, request: Request, _user: CurrentUser = Depends(require_admin)) -> Response:
    """Relay one ttyd HTTP request (the page itself and ``/token``)."""

    query = request.url.query
    url = f"{workshop_service.upstream_url()}/{path}" + (f"?{query}" if query else "")
    forward = {key: value for key, value in request.headers.items() if key.lower() in {"accept", "accept-language", "if-none-match", "if-modified-since"}}
    http_get = getattr(request.app.state, "workshop_proxy_http_get", _http_get)
    try:
        upstream = http_get(url, forward)
    except Exception:
        return Response("车间终端未运行。", status_code=502, media_type="text/plain; charset=utf-8")
    headers = {key: value for key, value in upstream.headers.items() if key.lower() not in _HOP_BY_HOP}
    # Always revalidate: a cached page from before a restart breaks reconnects.
    headers["Cache-Control"] = "no-store"
    return Response(upstream.content, status_code=upstream.status_code, headers=headers)


def _same_origin(websocket: WebSocket) -> bool:
    origin = websocket.headers.get("origin", "")
    if not origin:
        return True  # non-browser clients send none; the cookie still gates them
    # Port forwards / tunnels may rewrite Host but keep the public name in
    # X-Forwarded-Host. A cross-site page cannot set that header on a browser
    # WebSocket, so accepting it does not reopen cross-site hijacking.
    hosts = {websocket.headers.get("host", "").lower()}
    hosts.update(part.strip().lower() for part in websocket.headers.get("x-forwarded-host", "").split(",") if part.strip())
    return urlparse(origin).netloc.lower() in hosts


@router.websocket("/terminal/ws")
async def terminal_ws(websocket: WebSocket) -> None:
    """Relay the ttyd terminal WebSocket after the admin/origin checks."""

    user = _resolve_request_user(websocket)  # type: ignore[arg-type]
    if user is None or user.role != "admin" or not _same_origin(websocket):
        await websocket.close(code=_POLICY_VIOLATION)
        return
    from websockets.asyncio.client import connect
    from websockets.exceptions import ConnectionClosed

    offered = list(websocket.scope.get("subprotocols") or [])
    try:
        upstream = await connect(
            _ws_upstream_url(),
            subprotocols=["tty"],  # type: ignore[list-item]
            proxy=None,
            compression=None,
            max_size=None,
            open_timeout=10,
            ping_interval=20,
        )
    except Exception:
        await websocket.close(code=_UPSTREAM_DOWN)
        return
    await websocket.accept(subprotocol="tty" if "tty" in offered else None)

    async def browser_to_ttyd() -> None:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                return
            if message.get("bytes") is not None:
                await upstream.send(message["bytes"])
            elif message.get("text") is not None:
                await upstream.send(message["text"])

    async def ttyd_to_browser() -> None:
        async for frame in upstream:
            if isinstance(frame, bytes):
                await websocket.send_bytes(frame)
            else:
                await websocket.send_text(frame)

    tasks = [asyncio.create_task(browser_to_ttyd()), asyncio.create_task(ttyd_to_browser())]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            try:
                await task
            except (asyncio.CancelledError, ConnectionClosed, WebSocketDisconnect, RuntimeError):
                pass
        await upstream.close()
        if websocket.application_state == WebSocketState.CONNECTED:
            code = upstream.close_code or 1000
            try:
                await websocket.close(code=code if code != 1006 else 1011)
            except RuntimeError:
                pass
