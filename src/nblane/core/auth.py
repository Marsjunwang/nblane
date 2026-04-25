"""Small-team auth config and password hashing helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

HASH_SCHEME = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 600_000


class AuthConfigError(RuntimeError):
    """Raised when the auth config cannot be loaded safely."""


@dataclass(frozen=True)
class User:
    """One authenticated nblane user."""

    id: str
    display_name: str
    password_hash: str
    role: str
    profile: str | None = None
    profiles: tuple[str, ...] = ()
    teams: tuple[str, ...] = ()

    @property
    def is_admin(self) -> bool:
        """Whether this user can access every profile and team."""
        return self.role == "admin"


def auth_file_path() -> Path | None:
    """Return configured auth file path, if auth is enabled."""
    raw = os.getenv("NBLANE_AUTH_FILE", "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def auth_configured() -> bool:
    """True when an auth file is explicitly configured."""
    return auth_file_path() is not None


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode((text + pad).encode("ascii"))


def hash_password(
    password: str,
    *,
    iterations: int = DEFAULT_ITERATIONS,
    salt: bytes | None = None,
) -> str:
    """Return a PBKDF2-SHA256 password hash string."""
    if iterations < 100_000:
        raise ValueError("iterations must be at least 100000")
    salt_bytes = salt if salt is not None else os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        iterations,
    )
    return (
        f"{HASH_SCHEME}${iterations}${_b64(salt_bytes)}"
        f"${_b64(digest)}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify *password* against a stored PBKDF2 hash."""
    try:
        scheme, iter_s, salt_s, digest_s = stored_hash.split("$", 3)
        if scheme != HASH_SCHEME:
            return False
        iterations = int(iter_s)
        salt = _unb64(salt_s)
        expected = _unb64(digest_s)
    except Exception:
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected)


def _as_str_tuple(raw: Any) -> tuple[str, ...]:
    """Normalize YAML scalar/list fields into a string tuple."""
    if raw is None:
        return ()
    if isinstance(raw, str):
        val = raw.strip()
        return (val,) if val else ()
    if isinstance(raw, list):
        vals: list[str] = []
        for item in raw:
            val = str(item).strip()
            if val:
                vals.append(val)
        return tuple(vals)
    return ()


def _user_from_mapping(user_id: str, raw: dict[str, Any]) -> User:
    """Build a validated User from one YAML mapping."""
    password_hash = str(raw.get("password_hash", "") or "").strip()
    if not password_hash:
        raise AuthConfigError(f"user {user_id!r} is missing password_hash")
    role = str(raw.get("role", "member") or "member").strip().lower()
    if role not in ("admin", "member"):
        raise AuthConfigError(
            f"user {user_id!r} has invalid role {role!r}"
        )
    profile = str(raw.get("profile", "") or "").strip() or None
    profiles = set(_as_str_tuple(raw.get("profiles")))
    if profile:
        profiles.add(profile)
    return User(
        id=user_id,
        display_name=str(raw.get("display_name", user_id) or user_id),
        password_hash=password_hash,
        role=role,
        profile=profile,
        profiles=tuple(sorted(profiles)),
        teams=_as_str_tuple(raw.get("teams")),
    )


def load_users(path: Path | None = None) -> dict[str, User]:
    """Load users from ``auth/users.yaml`` style config."""
    cfg_path = path if path is not None else auth_file_path()
    if cfg_path is None:
        return {}
    if not cfg_path.exists():
        raise AuthConfigError(f"auth file not found: {cfg_path}")
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AuthConfigError("auth file must be a YAML mapping")
    users_raw = raw.get("users")
    if isinstance(users_raw, dict):
        items = users_raw.items()
    elif isinstance(users_raw, list):
        normalized: list[tuple[str, dict[str, Any]]] = []
        for row in users_raw:
            if not isinstance(row, dict):
                raise AuthConfigError("users list entries must be mappings")
            user_id = str(row.get("id", "") or "").strip()
            if not user_id:
                raise AuthConfigError("users list entry missing id")
            normalized.append((user_id, row))
        items = normalized
    else:
        raise AuthConfigError("auth file must contain users mapping or list")
    users: dict[str, User] = {}
    for user_id_raw, user_raw in items:
        user_id = str(user_id_raw).strip()
        if not user_id:
            raise AuthConfigError("user id cannot be empty")
        if not isinstance(user_raw, dict):
            raise AuthConfigError(f"user {user_id!r} must be a mapping")
        users[user_id] = _user_from_mapping(user_id, user_raw)
    return users
