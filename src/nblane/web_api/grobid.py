"""Admin routes for the self-hosted GROBID service (rootless Podman).

Deployment-wide like the LLM connection, so every route requires an admin.
Start/restart return immediately; the SPA polls ``GET /settings/grobid``
while the JVM loads (~45s).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from nblane.core import grobid_service
from nblane.web_api.auth import CurrentUser
from nblane.web_api.routes_v1 import ApiError, require_admin
from nblane.web_api.schemas import (
    ErrorResponse,
    GrobidBackendRequest,
    GrobidLogsResponse,
    GrobidStatusResponse,
)

router = APIRouter(prefix="/api/v1")
_RESPONSES = {400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}}


def _status() -> GrobidStatusResponse:
    return GrobidStatusResponse(**grobid_service.status())


def _act(action, code: str) -> GrobidStatusResponse:
    try:
        action()
    except grobid_service.GrobidServiceError as exc:
        raise ApiError(400, code, str(exc)) from exc
    return _status()


@router.get("/settings/grobid", response_model=GrobidStatusResponse, responses=_RESPONSES)
def get_grobid(_user: CurrentUser = Depends(require_admin)) -> GrobidStatusResponse:
    """Return GROBID health, managed-unit state and the PDF backend."""
    return _status()


@router.post("/settings/grobid/install", response_model=GrobidStatusResponse, responses=_RESPONSES)
def install_grobid(_user: CurrentUser = Depends(require_admin)) -> GrobidStatusResponse:
    """Pull the pinned image if needed, write the user unit and start it."""
    return _act(grobid_service.start_install, "grobid_install_failed")


@router.post("/settings/grobid/start", response_model=GrobidStatusResponse, responses=_RESPONSES)
def start_grobid(_user: CurrentUser = Depends(require_admin)) -> GrobidStatusResponse:
    return _act(grobid_service.start, "grobid_start_failed")


@router.post("/settings/grobid/stop", response_model=GrobidStatusResponse, responses=_RESPONSES)
def stop_grobid(_user: CurrentUser = Depends(require_admin)) -> GrobidStatusResponse:
    return _act(grobid_service.stop, "grobid_stop_failed")


@router.post("/settings/grobid/restart", response_model=GrobidStatusResponse, responses=_RESPONSES)
def restart_grobid(_user: CurrentUser = Depends(require_admin)) -> GrobidStatusResponse:
    return _act(grobid_service.restart, "grobid_restart_failed")


@router.delete("/settings/grobid", response_model=GrobidStatusResponse, responses=_RESPONSES)
def uninstall_grobid(_user: CurrentUser = Depends(require_admin)) -> GrobidStatusResponse:
    """Stop and remove the managed unit; the image stays for reinstall."""
    return _act(grobid_service.uninstall, "grobid_uninstall_failed")


@router.put("/settings/grobid/backend", response_model=GrobidStatusResponse, responses=_RESPONSES)
def set_grobid_backend(
    body: GrobidBackendRequest, _user: CurrentUser = Depends(require_admin)
) -> GrobidStatusResponse:
    """Choose how PDFs are structured (shared by Reader and SPA backend)."""
    return _act(lambda: grobid_service.set_backend(body.backend), "grobid_backend_failed")


@router.get("/settings/grobid/logs", response_model=GrobidLogsResponse, responses=_RESPONSES)
def grobid_logs(_user: CurrentUser = Depends(require_admin)) -> GrobidLogsResponse:
    return GrobidLogsResponse(text=grobid_service.logs())
