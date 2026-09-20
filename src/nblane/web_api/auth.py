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

SESSION_TTL_SECONDS = 12 * 3600

GENERIC_LOGIN_ERROR = "Invalid username or password"

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Credentials submitted to the login endpoint."""

    username: str
    password: str


class CurrentUser(BaseModel):
    """The authenticated principal for one request."""

    id: str
    display_name: str
    role: str
    auth_enabled: bool = False
    profiles: list[str] = Field(default_factory=list)
    teams: list[str] = Field(default_factory=list)

    @classmethod
    def from_user(cls, user: auth_core.User, *, auth_enabled: bool) -> "CurrentUser":
        """Build the API-facing view of a core ``User``."""
        return cls(
            id=user.id,
            display_name=user.display_name,
            role=user.role,
            auth_enabled=auth_enabled,
            profiles=list(user.profiles),
            teams=list(user.teams),
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
        teams=("*",),
    )


def _cookie_secure() -> bool:
    raw = os.getenv("NBLANE_AUTH_COOKIE_SECURE", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _set_session_cookie(
    response: Response,
    user_id: str,
    *,
    ttl_seconds: int = SESSION_TTL_SECONDS,
) -> None:
    token = auth_core.mint_auth_session_token(user_id, ttl_seconds=ttl_seconds)
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


def require_user(request: Request) -> CurrentUser:
    """FastAPI dependency: resolve the current user or reject with 401.

    Auth off (no ``NBLANE_AUTH_FILE``) yields the synthetic local admin;
    auth on requires a valid ``nblane_auth_session`` cookie.
    """
    if not auth_core.auth_configured():
        return CurrentUser.from_user(_local_user(), auth_enabled=False)
    cookie = request.cookies.get(auth_core.AUTH_SESSION_COOKIE_NAME, "")
    if cookie:
        claims = _verify_token(cookie)
        if claims is not None:
            user = _load_users_or_500().get(claims.user_id)
            if user is not None:
                return CurrentUser.from_user(user, auth_enabled=True)
    raise HTTPException(status_code=401, detail="Authentication required")


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
    if user is None or not auth_core.verify_password(payload.password, stored_hash):
        limiter.record_failure(key)
        raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)
    limiter.record_success(key)
    _set_session_cookie(response, user.id)
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
