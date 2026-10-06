"""Admin routes for installable local translation models (llama.cpp).

Deployment-wide like the LLM connection, so every route requires an admin.
Installs run in a daemon thread of this process; the SPA polls
``GET /settings/local-models`` for progress.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from nblane.core.ai import local_models
from nblane.web_api.auth import CurrentUser
from nblane.web_api.routes_v1 import ApiError, require_admin
from nblane.web_api.schemas import (
    ErrorResponse,
    LocalModelActiveRequest,
    LocalModelsResponse,
    LocalModelTestRequest,
    LocalModelTestResponse,
)

router = APIRouter(prefix="/api/v1")
_RESPONSES = {
    400: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
}


def _status() -> LocalModelsResponse:
    return LocalModelsResponse(**local_models.catalog_status())


def _spec(model_id: str) -> local_models.LocalModelSpec:
    spec = local_models.get_spec(model_id)
    if spec is None:
        raise ApiError(404, "local_model_not_found", "未知的本地模型。")
    return spec


@router.get("/settings/local-models", response_model=LocalModelsResponse, responses=_RESPONSES)
def get_local_models(_user: CurrentUser = Depends(require_admin)) -> LocalModelsResponse:
    """Return the curated catalog, host resources and install progress."""
    return _status()


@router.post(
    "/settings/local-models/{model_id}/install",
    response_model=LocalModelsResponse,
    responses=_RESPONSES,
)
def install_local_model(
    model_id: str, _user: CurrentUser = Depends(require_admin)
) -> LocalModelsResponse:
    """Start downloading the runtime and model in the background."""
    spec = _spec(model_id)
    try:
        local_models.start_install(spec.id)
    except local_models.LocalModelError as exc:
        raise ApiError(400, "local_model_install_blocked", str(exc)) from exc
    return _status()


@router.post(
    "/settings/local-models/{model_id}/cancel",
    response_model=LocalModelsResponse,
    responses=_RESPONSES,
)
def cancel_local_model_install(
    model_id: str, _user: CurrentUser = Depends(require_admin)
) -> LocalModelsResponse:
    """Cancel a running install; the partial file is kept for resume."""
    local_models.cancel_install(_spec(model_id).id)
    return _status()


@router.delete(
    "/settings/local-models/{model_id}",
    response_model=LocalModelsResponse,
    responses=_RESPONSES,
)
def delete_local_model(
    model_id: str, _user: CurrentUser = Depends(require_admin)
) -> LocalModelsResponse:
    """Delete a model file (deactivating it first when active)."""
    try:
        local_models.delete_model(_spec(model_id).id)
    except local_models.LocalModelError as exc:
        raise ApiError(400, "local_model_delete_failed", str(exc)) from exc
    return _status()


@router.put("/settings/local-models/active", response_model=LocalModelsResponse, responses=_RESPONSES)
def set_active_local_model(
    body: LocalModelActiveRequest, _user: CurrentUser = Depends(require_admin)
) -> LocalModelsResponse:
    """Select which installed model translates; empty disables local use."""
    if body.model_id:
        _spec(body.model_id)
    try:
        local_models.set_active_model(body.model_id)
    except local_models.LocalModelError as exc:
        raise ApiError(400, "local_model_activate_failed", str(exc)) from exc
    return _status()


@router.post(
    "/settings/local-models/test",
    response_model=LocalModelTestResponse,
    responses=_RESPONSES,
)
def test_local_model(
    body: LocalModelTestRequest, _user: CurrentUser = Depends(require_admin)
) -> LocalModelTestResponse:
    """Translate a short passage to check speed and quality."""
    spec = _spec(body.model_id or local_models.active_model_id())
    text = body.text.strip()
    if not text:
        raise ApiError(400, "local_model_test_empty", "请输入要试译的文本。")
    if not local_models.is_installed(spec):
        raise ApiError(400, "local_model_not_installed", "模型尚未安装。")
    started = time.monotonic()
    try:
        translated = local_models.translate_text(spec, text, target_lang=body.target_lang or "zh")
    except local_models.LocalModelError as exc:
        raise ApiError(400, "local_model_test_failed", str(exc)) from exc
    return LocalModelTestResponse(
        model_id=spec.id,
        translated_text=translated,
        seconds=round(time.monotonic() - started, 2),
    )
