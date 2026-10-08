"""The only writer of ``auth/users.yaml`` (account management).

Every mutation takes the sidecar lock, re-reads the raw YAML, changes one
user's mapping in place (unknown keys and other users stay untouched),
and installs the result atomically. Nothing here calls
``git_backup.record_change`` (no per-click commit); the daily backup
commits ``auth/users.yaml`` to the private data repo
(``core/backup_targets.DATA_AUTH_FILE``).
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import yaml

from nblane.core import auth as auth_core
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_io import validate_profile_name

MIN_PASSWORD_LENGTH = 10
ROLES = ("admin", "member")
_TOKEN_NAME_MAX = 80


class AccountError(ValueError):
    """Account mutation refused; ``code`` is a stable machine-readable key."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# --------------------------------------------------------------------- helpers


def _auth_file() -> Path:
    path = auth_core.auth_file_path()
    if path is None:
        raise AccountError("auth_not_configured", "Auth is not configured.")
    return path


def _validate_user_id(user_id: str) -> str:
    try:
        clean = validate_profile_name(user_id)
    except ValueError as exc:
        raise AccountError("invalid_user_id", str(exc)) from exc
    if any(ch.isspace() for ch in clean):
        raise AccountError("invalid_user_id", "User id cannot contain whitespace.")
    return clean


def validate_password(password: str) -> str:
    """Return *password* or raise ``AccountError('weak_password')``."""
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise AccountError(
            "weak_password",
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
        )
    return password


def _validate_role(role: str) -> str:
    clean = str(role or "").strip().lower()
    if clean not in ROLES:
        raise AccountError("invalid_role", f"Role must be one of {', '.join(ROLES)}.")
    return clean


def _clean_profiles(profiles: Iterable[str]) -> list[str]:
    out: list[str] = []
    for item in profiles or ():
        try:
            clean = validate_profile_name(str(item))
        except ValueError as exc:
            raise AccountError("invalid_profile_name", str(exc)) from exc
        if clean not in out:
            out.append(clean)
    return out


def _read_raw(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"users": {}}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {"users": {}}
    if not isinstance(raw, dict):
        raise AccountError("auth_file_invalid", "Auth file must be a YAML mapping.")
    users = raw.get("users")
    if users is None:
        raw["users"] = {}
    elif not isinstance(users, (dict, list)):
        raise AccountError("auth_file_invalid", "Auth file users must be a mapping or list.")
    return raw


def _find(raw: dict[str, Any], user_id: str) -> dict[str, Any] | None:
    users = raw["users"]
    if isinstance(users, dict):
        for key, row in users.items():
            if str(key).strip() == user_id and isinstance(row, dict):
                return row
        return None
    for row in users:
        if isinstance(row, dict) and str(row.get("id", "") or "").strip() == user_id:
            return row
    return None


def _require(raw: dict[str, Any], user_id: str) -> dict[str, Any]:
    row = _find(raw, user_id)
    if row is None:
        raise AccountError("user_not_found", f"Unknown user: {user_id}")
    return row


def _iter_rows(raw: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    users = raw["users"]
    if isinstance(users, dict):
        for key, row in users.items():
            if isinstance(row, dict):
                yield str(key).strip(), row
    else:
        for row in users:
            if isinstance(row, dict):
                yield str(row.get("id", "") or "").strip(), row


def _is_login_admin(row: dict[str, Any]) -> bool:
    role = str(row.get("role", "member") or "member").strip().lower()
    return role == "admin" and row.get("disabled") is not True and row.get("agent") is not True


def _ensure_admin_left(raw: dict[str, Any]) -> None:
    if not any(_is_login_admin(row) for _, row in _iter_rows(raw)):
        raise AccountError(
            "last_admin",
            "At least one enabled administrator must remain.",
        )


def _bump(row: dict[str, Any]) -> None:
    current = row.get("session_version", 0)
    if isinstance(current, bool) or not isinstance(current, int) or current < 0:
        current = 0
    row["session_version"] = current + 1


def _mutate(fn: Callable[[dict[str, Any]], Any]) -> Any:
    """Locked read-modify-write of the auth file; returns ``fn``'s result."""
    path = _auth_file()
    with locked_profile_write(path.parent, path.name):
        existed = path.exists()
        raw = _read_raw(path)
        result = fn(raw)
        text = yaml.safe_dump(raw, allow_unicode=True, sort_keys=False)
        atomic_write_text(path, text)
        if not existed:
            os.chmod(path, 0o600)
    auth_core.clear_users_cache()
    return result


# ------------------------------------------------------------------ mutations


def create_user(
    user_id: str,
    *,
    display_name: str,
    role: str,
    password: str,
    profiles: Iterable[str] = (),
    must_change_password: bool = True,
) -> None:
    """Add a new (non-agent) user."""
    clean_id = _validate_user_id(user_id)
    clean_role = _validate_role(role)
    validate_password(password)
    clean_profiles = _clean_profiles(profiles)
    password_hash = auth_core.hash_password(password)

    def apply(raw: dict[str, Any]) -> None:
        if _find(raw, clean_id) is not None:
            raise AccountError("user_exists", f"User already exists: {clean_id}")
        row: dict[str, Any] = {
            "display_name": str(display_name or "").strip() or clean_id,
            "password_hash": password_hash,
            "role": clean_role,
        }
        if clean_profiles:
            row["profiles"] = clean_profiles
        if must_change_password:
            row["must_change_password"] = True
        row["session_version"] = 0
        if isinstance(raw["users"], dict):
            raw["users"][clean_id] = row
        else:
            raw["users"].append({"id": clean_id, **row})

    _mutate(apply)


def set_password(user_id: str, new_password: str, *, must_change: bool = False) -> None:
    """Replace the password hash and invalidate every session."""
    validate_password(new_password)
    password_hash = auth_core.hash_password(new_password)

    def apply(raw: dict[str, Any]) -> None:
        row = _require(raw, user_id)
        row["password_hash"] = password_hash
        if must_change:
            row["must_change_password"] = True
        else:
            row.pop("must_change_password", None)
        _bump(row)

    _mutate(apply)


def set_disabled(user_id: str, disabled: bool, *, actor_id: str) -> None:
    """Enable or disable *user_id*; disabling also ends its sessions."""

    def apply(raw: dict[str, Any]) -> None:
        row = _require(raw, user_id)
        if disabled:
            if user_id == actor_id:
                raise AccountError("cannot_disable_self", "You cannot disable your own account.")
            if row.get("disabled") is True:
                return
            row["disabled"] = True
            _bump(row)
            _ensure_admin_left(raw)
        else:
            row.pop("disabled", None)

    _mutate(apply)


def update_user(
    user_id: str,
    *,
    actor_id: str,
    display_name: str | None = None,
    role: str | None = None,
    profiles: Iterable[str] | None = None,
) -> None:
    """Change display name, role and/or accessible profiles."""
    clean_role = _validate_role(role) if role is not None else None
    clean_profiles = _clean_profiles(profiles) if profiles is not None else None

    def apply(raw: dict[str, Any]) -> None:
        row = _require(raw, user_id)
        if display_name is not None:
            row["display_name"] = str(display_name).strip() or user_id
        if clean_role is not None:
            current = str(row.get("role", "member") or "member").strip().lower()
            if clean_role != "admin" and current == "admin" and user_id == actor_id:
                raise AccountError("cannot_demote_self", "You cannot remove your own admin role.")
            row["role"] = clean_role
            _ensure_admin_left(raw)
        if clean_profiles is not None:
            # ``profile`` (legacy single field) folds into ``profiles``.
            row.pop("profile", None)
            row["profiles"] = clean_profiles

    _mutate(apply)


def bump_session_version(user_id: str) -> None:
    """Invalidate every session of *user_id* (logout everywhere)."""
    _mutate(lambda raw: _bump(_require(raw, user_id)))


def create_api_token(user_id: str, name: str) -> tuple[str, auth_core.ApiTokenRecord]:
    """Mint a token for *user_id*; returns ``(plaintext, record)`` (plaintext once)."""
    clean_name = re.sub(r"\s+", " ", str(name or "")).strip()[:_TOKEN_NAME_MAX]
    if not clean_name:
        raise AccountError("invalid_token_name", "Token name cannot be empty.")
    plaintext, record = auth_core.mint_api_token(clean_name)

    def apply(raw: dict[str, Any]) -> None:
        row = _require(raw, user_id)
        tokens = row.get("api_tokens")
        if not isinstance(tokens, list):
            tokens = []
        tokens.append(
            {
                "id": record.id,
                "name": record.name,
                "hash": record.hash,
                "created": record.created or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        row["api_tokens"] = tokens

    _mutate(apply)
    return plaintext, record


def revoke_api_token(user_id: str, token_id: str) -> None:
    """Remove one API token from *user_id*."""

    def apply(raw: dict[str, Any]) -> None:
        row = _require(raw, user_id)
        tokens = row.get("api_tokens")
        if not isinstance(tokens, list):
            tokens = []
        kept = [t for t in tokens if not (isinstance(t, dict) and str(t.get("id", "")) == token_id)]
        if len(kept) == len(tokens):
            raise AccountError("token_not_found", f"Unknown token: {token_id}")
        if kept:
            row["api_tokens"] = kept
        else:
            row.pop("api_tokens", None)

    _mutate(apply)


__all__ = [
    "AccountError",
    "MIN_PASSWORD_LENGTH",
    "bump_session_version",
    "create_api_token",
    "create_user",
    "revoke_api_token",
    "set_disabled",
    "set_password",
    "update_user",
    "validate_password",
]
