"""Cookie-based auth for the nblane FastAPI backend (M1 slice).

Reuses the HMAC session-token and PBKDF2 password machinery from
``nblane.core.auth`` so one login serves both this API and the legacy
Streamlit/Reader processes. When ``NBLANE_AUTH_FILE`` is unset, auth is
OFF and every request runs as a synthetic local admin.
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from nblane.core import auth as auth_core
from nblane.core import auth_store
from nblane.core import git_backup

SESSION_TTL_SECONDS = 12 * 3600

GENERIC_LOGIN_ERROR = "Invalid username or password"

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Credentials submitted to the login endpoint."""

    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    """Self-service password change."""

    current_password: str
    new_password: str


class CurrentUser(BaseModel):
    """The authenticated principal for one request."""

    id: str
    display_name: str
    role: str
    auth_enabled: bool = False
    profiles: list[str] = Field(default_factory=list)
    agent: bool = False
    must_change_password: bool = False

    @classmethod
    def from_user(cls, user: auth_core.User, *, auth_enabled: bool) -> "CurrentUser":
        """Build the API-facing view of a core ``User``."""
        return cls(
            id=user.id,
            display_name=user.display_name,
            role=user.role,
            auth_enabled=auth_enabled,
            profiles=list(user.profiles),
            agent=user.agent,
            must_change_password=user.must_change_password,
        )


class OkResponse(BaseModel):
    """Generic success acknowledgement."""

    ok: bool = True


class LoginRateLimiter:
    """Per-client in-memory failed-login throttle (single-process, workers=1).

    After ``max_failures`` failures inside ``window_seconds`` the client is
    blocked (429) until the oldest failure ages out. A successful login
    clears the client's failure bucket.
    """

    def __init__(self, max_failures: int = 5, window_seconds: float = 60.0) -> None:
        self.max_failures = max(1, int(max_failures))
        self.window_seconds = float(window_seconds)
        self._failures: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _prune(bucket: deque[float], now: float, window_seconds: float) -> None:
        cutoff = now - window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

    def blocked(self, key: str) -> bool:
        """Whether *key* has exhausted its failure budget for this window."""
        with self._lock:
            bucket = self._failures.get(key)
            if not bucket:
                return False
            self._prune(bucket, time.monotonic(), self.window_seconds)
            return len(bucket) >= self.max_failures

    def record_failure(self, key: str) -> None:
        """Record one failed login attempt for *key*."""
        with self._lock:
            bucket = self._failures.setdefault(key, deque())
            now = time.monotonic()
            self._prune(bucket, now, self.window_seconds)
            bucket.append(now)

    def record_success(self, key: str) -> None:
        """Clear the failure bucket for *key* after a successful login."""
        with self._lock:
            self._failures.pop(key, None)

    def reset(self) -> None:
        """Drop all recorded failures (test helper)."""
        with self._lock:
            self._failures.clear()


def _local_user() -> auth_core.User:
    """Synthetic admin used when no auth file is configured."""
    return auth_core.User(
        id="local",
        display_name="Local",
        password_hash="",
        role="admin",
    )


def _cookie_secure() -> bool:
    raw = os.getenv("NBLANE_AUTH_COOKIE_SECURE", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _set_session_cookie(
    response: Response,
    user_id: str,
    *,
    session_version: int = 0,
    ttl_seconds: int = SESSION_TTL_SECONDS,
) -> None:
    token = auth_core.mint_auth_session_token(
        user_id, ttl_seconds=ttl_seconds, session_version=session_version
    )
    claims = auth_core.verify_auth_session_token(token)
    max_age = max(0, claims.exp - int(time.time())) if claims else ttl_seconds
    response.set_cookie(
        auth_core.AUTH_SESSION_COOKIE_NAME,
        token,
        max_age=max_age,
        path="/",
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
    )


def _delete_session_cookie(response: Response) -> None:
    response.delete_cookie(
        auth_core.AUTH_SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
    )


def _rate_limiter(request: Request) -> LoginRateLimiter:
    limiter = getattr(request.app.state, "login_rate_limiter", None)
    if limiter is None:
        limiter = LoginRateLimiter()
        request.app.state.login_rate_limiter = limiter
    return limiter


def _trust_proxy_headers() -> bool:
    """Whether ``X-Forwarded-For`` from the direct peer may be trusted.

    Only enable (``NBLANE_TRUST_PROXY_HEADERS=1``) when the app sits behind a
    known reverse proxy (e.g. Caddy) that sets/overwrites the header and the
    app is not directly reachable; otherwise clients could spoof their
    rate-limit identity with a forged header.
    """
    raw = os.getenv("NBLANE_TRUST_PROXY_HEADERS", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _client_ip(request: Request) -> str:
    """Client IP used for rate limiting (first XFF hop when proxies are trusted)."""
    if _trust_proxy_headers():
        forwarded = request.headers.get("x-forwarded-for", "")
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


def _client_key(request: Request, username: str) -> str:
    """Rate-limit bucket key: client IP + attempted username.

    The username dimension stops one client from exhausting a shared IP
    bucket (e.g. the single proxy egress address) and locking every other
    account out of login.
    """
    return f"{_client_ip(request)}\n{username.strip()}"


_dummy_hash: str | None = None
_dummy_hash_lock = threading.Lock()


def _dummy_hash_value() -> str:
    """Lazily computed stand-in hash so unknown users cost the same as real ones."""
    global _dummy_hash
    with _dummy_hash_lock:
        if _dummy_hash is None:
            _dummy_hash = auth_core.hash_password("dummy-password")
        return _dummy_hash


def _verify_token(token: str) -> auth_core.AuthSessionClaims | None:
    try:
        return auth_core.verify_auth_session_token(
            token, expected_kind=auth_core.AUTH_SESSION_KIND
        )
    except auth_core.AuthConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _load_users_or_500() -> dict[str, auth_core.User]:
    try:
        return auth_core.load_users()
    except auth_core.AuthConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _resolve_request_user(request: Request) -> CurrentUser | None:
    """Resolve the request's user without enforcing authentication.

    Auth off (no ``NBLANE_AUTH_FILE``) yields the synthetic local admin;
    auth on yields the cookie's user or ``None`` when the session is
    missing/invalid. Shared by ``require_user`` (which turns ``None`` into
    401) and the git-actor middleware (which treats ``None`` as anonymous).
    """
    if not auth_core.auth_configured():
        return CurrentUser.from_user(_local_user(), auth_enabled=False)
    bearer = _bearer_token(request)
    if bearer:
        # An explicit API token never falls back to the cookie.
        user = auth_core.user_for_api_token(bearer, _load_users_or_500())
        return CurrentUser.from_user(user, auth_enabled=True) if user else None
    cookie = request.cookies.get(auth_core.AUTH_SESSION_COOKIE_NAME, "")
    if cookie:
        claims = _verify_token(cookie)
        if claims is not None:
            user = auth_core.resolve_session_user(claims, _load_users_or_500())
            if user is not None:
                return CurrentUser.from_user(user, auth_enabled=True)
    return None


def _bearer_token(request: Request) -> str:
    """``nbl_…`` token from ``Authorization: Bearer``, else empty."""
    header = request.headers.get("authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "bearer":
        return ""
    value = value.strip()
    return value if value.startswith(auth_core.API_TOKEN_PREFIX) else ""


def require_user(request: Request) -> CurrentUser:
    """FastAPI dependency: resolve the current user or reject with 401.

    Auth off (no ``NBLANE_AUTH_FILE``) yields the synthetic local admin;
    auth on requires a valid ``nblane_auth_session`` cookie.
    """
    user = _resolve_request_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


class GitActorMiddleware:
    """Pure-ASGI middleware: per-request git actor + backup result scope.

    Starts a ``git_backup`` operation scoped to the authenticated user id
    (the synthetic local admin when auth is off) so web-API mutations
    commit as the caller instead of the default ``cli`` actor, keeping the
    git history and the agent-activity writeback trace cross-checkable.
    Pure ASGI (not ``BaseHTTPMiddleware``) so the contextvar set here
    propagates into the threadpool contexts that run sync route handlers.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            user = _resolve_request_user(Request(scope))
            git_backup.start_operation(user.id if user is not None else None)
        await self.app(scope, receive, send)


@router.post("/login", response_model=CurrentUser)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
) -> CurrentUser:
    """Verify credentials and set the shared session cookie."""
    if not auth_core.auth_configured():
        raise HTTPException(status_code=400, detail="Auth is not configured")
    limiter = _rate_limiter(request)
    key = _client_key(request, payload.username)
    if limiter.blocked(key):
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts; try again later",
        )
    user = _load_users_or_500().get(payload.username.strip())
    stored_hash = user.password_hash if user is not None else _dummy_hash_value()
    password_ok = auth_core.verify_password(payload.password, stored_hash)
    if user is None or not password_ok or user.disabled:
        limiter.record_failure(key)
        raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)
    limiter.record_success(key)
    _set_session_cookie(response, user.id, session_version=user.session_version)
    return CurrentUser.from_user(user, auth_enabled=True)


@router.post("/logout", response_model=OkResponse)
def logout(response: Response) -> OkResponse:
    """Clear the session cookie."""
    _delete_session_cookie(response)
    return OkResponse()


@router.get("/me", response_model=CurrentUser)
def me(user: CurrentUser = Depends(require_user)) -> CurrentUser:
    """Return the current user (or the synthetic local admin when auth is off)."""
    return user


def _account_error(exc: auth_store.AccountError) -> Exception:
    from nblane.web_api.routes_v1 import ApiError

    status = 400 if exc.code == "auth_not_configured" else 422
    return ApiError(status, exc.code, exc.message)


@router.post("/password", response_model=CurrentUser)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    user: CurrentUser = Depends(require_user),
) -> CurrentUser:
    """Change your own password; every other session is signed out."""
    from nblane.web_api.routes_v1 import ApiError

    if not auth_core.auth_configured():
        raise ApiError(400, "auth_not_configured", "Auth is not configured.")
    limiter = _rate_limiter(request)
    key = _client_key(request, user.id)
    if limiter.blocked(key):
        raise ApiError(429, "rate_limited", "Too many failed attempts; try again later.")
    record = _load_users_or_500().get(user.id)
    stored_hash = record.password_hash if record is not None else _dummy_hash_value()
    if record is None or not auth_core.verify_password(payload.current_password, stored_hash):
        limiter.record_failure(key)
        raise ApiError(401, "invalid_current_password", "Current password is incorrect.")
    limiter.record_success(key)
    try:
        auth_store.set_password(user.id, payload.new_password, must_change=False)
    except auth_store.AccountError as exc:
        raise _account_error(exc) from exc
    updated = _load_users_or_500().get(user.id)
    if updated is None:
        raise ApiError(401, "user_not_found", "Authentication required")
    _set_session_cookie(response, updated.id, session_version=updated.session_version)
    return CurrentUser.from_user(updated, auth_enabled=True)


@router.post("/logout-all", response_model=OkResponse)
def logout_all(
    response: Response,
    user: CurrentUser = Depends(require_user),
) -> OkResponse:
    """Sign out every session of the current user (this one included)."""
    from nblane.web_api.routes_v1 import ApiError

    if not auth_core.auth_configured():
        raise ApiError(400, "auth_not_configured", "Auth is not configured.")
    try:
        auth_store.bump_session_version(user.id)
    except auth_store.AccountError as exc:
        raise _account_error(exc) from exc
    _delete_session_cookie(response)
    return OkResponse()
