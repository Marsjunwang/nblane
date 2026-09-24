"""nblane FastAPI backend (frontend SPA migration).

M1: cookie-based auth via ``nblane.web_api.auth`` — all v1 routes require a
session except ``GET /api/v1/health`` and ``/api/v1/auth/*``.

One process serves both the JSON API and the built SPA: ``mount_spa`` (see
``nblane.web_api.spa``) serves ``web_ui/static`` with a client-route
fallback to ``index.html``.

Uvicorn entry point: ``nblane.web_api:app``.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from nblane.web_api.assistant import router as assistant_router
from nblane.web_api.auth import GitActorMiddleware, LoginRateLimiter
from nblane.web_api.auth import router as auth_router
from nblane.web_api.routes_v1 import (
    ApiError,
    api_error_handler,
    app_version,
    router,
    validation_error_handler,
)
from nblane.web_api.spa import mount_spa
from nblane.web_api.workshop import router as workshop_router


def create_app(
    *,
    login_rate_limiter: LoginRateLimiter | None = None,
    spa_static_dir: Path | None = None,
) -> FastAPI:
    """Build the nblane API application (API + built SPA in one process)."""
    app = FastAPI(title="nblane API", version=app_version())
    app.add_middleware(GitActorMiddleware)
    app.state.login_rate_limiter = login_rate_limiter or LoginRateLimiter()
    app.add_exception_handler(ApiError, api_error_handler)
    # Unify 422 bodies: pydantic validation failures get the same
    # ErrorResponse{code, message} shape as ApiError (code validation_error).
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.include_router(auth_router)
    app.include_router(router)
    app.include_router(assistant_router)
    app.include_router(workshop_router)
    # Mounted last so API routes win over the SPA catch-all fallback.
    mount_spa(app, static_dir=spa_static_dir)
    return app


app = create_app()
