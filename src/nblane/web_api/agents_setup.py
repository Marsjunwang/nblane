"""Admin routes for data backup targets and the local personal agent.

Deployment-wide like the LLM connection, so every route requires an admin.
Backup writes are short git/ssh calls run inline; OpenClaw install /
connect / migrate run in a background thread (``core/openclaw_setup``) and
the SPA polls ``GET /settings/agents/openclaw`` for the log.

Only registered target ids reach ``core/backup_targets`` — the browser never
sends a filesystem path. See docs/zh/guides/agent-setup.md.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from nblane.core import backup_targets, openclaw_setup
from nblane.web_api.auth import CurrentUser
from nblane.web_api.routes_v1 import ApiError, require_admin
from nblane.web_api.schemas import (
    BackupKeyResponse,
    BackupRemoteRequest,
    BackupRemoteTestResponse,
    BackupRunResponse,
    BackupStatusResponse,
    BackupTimerRequest,
    ErrorResponse,
    OpenClawGatewayRequest,
    OpenClawJobRequest,
    OpenClawStatusResponse,
)

router = APIRouter(prefix="/api/v1")
_RESPONSES = {400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}


def _backup_status() -> BackupStatusResponse:
    return BackupStatusResponse(**backup_targets.status())


def _target(target_id: str) -> backup_targets.BackupTarget:
    try:
        return backup_targets.get_target(target_id)
    except backup_targets.BackupError as exc:
        raise ApiError(404, "backup_target_not_found", str(exc)) from exc


def _backup(call, code: str):
    try:
        return call()
    except backup_targets.BackupError as exc:
        raise ApiError(400, code, str(exc)) from exc


@router.get("/settings/backup", response_model=BackupStatusResponse, responses=_RESPONSES)
def get_backup(_user: CurrentUser = Depends(require_admin)) -> BackupStatusResponse:
    """Return every backup target with remote/push freshness and the timer."""
    return _backup_status()


@router.post("/settings/backup/targets/{target_id}/init", response_model=BackupStatusResponse, responses=_RESPONSES)
def init_backup_target(target_id: str, _user: CurrentUser = Depends(require_admin)) -> BackupStatusResponse:
    """Make the target a git repository (with a .gitignore) if it is not one."""
    _backup(lambda: backup_targets.init_target(_target(target_id).id), "backup_init_failed")
    return _backup_status()


@router.post("/settings/backup/targets/{target_id}/key", response_model=BackupKeyResponse, responses=_RESPONSES)
def generate_backup_key(target_id: str, _user: CurrentUser = Depends(require_admin)) -> BackupKeyResponse:
    """Create the target's deploy key once and return its public half."""
    target = _target(target_id)
    public_key = _backup(lambda: backup_targets.generate_key(target.id), "backup_key_failed")
    return BackupKeyResponse(public_key=public_key, key_path=str(backup_targets.key_path(target)))


@router.post(
    "/settings/backup/targets/{target_id}/remote/test",
    response_model=BackupRemoteTestResponse,
    responses=_RESPONSES,
)
def test_backup_remote(
    target_id: str, body: BackupRemoteRequest, _user: CurrentUser = Depends(require_admin)
) -> BackupRemoteTestResponse:
    """Check URL shape, privacy, read and write access without saving."""
    target = _target(target_id)
    return BackupRemoteTestResponse(**_backup(lambda: backup_targets.test_remote(target.id, body.url), "backup_test_failed"))


@router.put("/settings/backup/targets/{target_id}/remote", response_model=BackupStatusResponse, responses=_RESPONSES)
def save_backup_remote(
    target_id: str, body: BackupRemoteRequest, _user: CurrentUser = Depends(require_admin)
) -> BackupStatusResponse:
    """Re-test, save the remote and push the existing history."""
    target = _target(target_id)
    _backup(lambda: backup_targets.connect_remote(target.id, body.url), "backup_remote_failed")
    return _backup_status()


@router.post("/settings/backup/run", response_model=BackupRunResponse, responses=_RESPONSES)
def run_backup_now(target_id: str = "", _user: CurrentUser = Depends(require_admin)) -> BackupRunResponse:
    """Snapshot and push one target (``?target_id=``) or all of them now."""
    if target_id:
        _target(target_id)
    results = _backup(lambda: backup_targets.run_backup(target_id or None), "backup_run_failed")
    return BackupRunResponse(results=results, status=_backup_status())


@router.put("/settings/backup/timer", response_model=BackupStatusResponse, responses=_RESPONSES)
def set_backup_timer(body: BackupTimerRequest, _user: CurrentUser = Depends(require_admin)) -> BackupStatusResponse:
    """Install/enable or disable the daily systemd --user backup timer."""
    _backup(lambda: backup_targets.set_timer(body.enabled), "backup_timer_failed")
    return _backup_status()


# ------------------------------------------------------------------ agent


def _openclaw_status() -> OpenClawStatusResponse:
    return OpenClawStatusResponse(**openclaw_setup.status())


@router.get("/settings/agents/openclaw", response_model=OpenClawStatusResponse, responses=_RESPONSES)
def get_openclaw_setup(_user: CurrentUser = Depends(require_admin)) -> OpenClawStatusResponse:
    """Return install state, wiring and the running setup job."""
    return _openclaw_status()


@router.post("/settings/agents/openclaw/{kind}", response_model=OpenClawStatusResponse, responses=_RESPONSES)
def start_openclaw_job(
    kind: str, body: OpenClawJobRequest, _user: CurrentUser = Depends(require_admin)
) -> OpenClawStatusResponse:
    """Start ``install`` / ``connect`` / ``migrate`` / ``weixin`` in the background."""
    if kind not in openclaw_setup.JOB_KINDS:
        raise ApiError(404, "agent_job_not_found", "未知的操作。")
    try:
        openclaw_setup.start_job(kind, body.model_dump())
    except openclaw_setup.OpenClawSetupError as exc:
        raise ApiError(400, "agent_job_blocked", str(exc)) from exc
    return _openclaw_status()


@router.post("/settings/agents/openclaw-gateway", response_model=OpenClawStatusResponse, responses=_RESPONSES)
def openclaw_gateway_action(
    body: OpenClawGatewayRequest, _user: CurrentUser = Depends(require_admin)
) -> OpenClawStatusResponse:
    """Start, stop or restart the gateway service."""
    try:
        openclaw_setup.gateway_action(body.action)
    except openclaw_setup.OpenClawSetupError as exc:
        raise ApiError(400, "agent_gateway_failed", str(exc)) from exc
    return _openclaw_status()
