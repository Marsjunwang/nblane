"""One-click API token for the personal agent's service account.

The assistant client (``scripts/openclaw/skills/bin/nblane_api.py``) reads
``NBLANE_OPENCLAW_API_TOKEN`` from its env or from ``api.env``
(``KEY=VALUE`` lines). The nblane web service runs as the same OS user as
OpenClaw, so it can mint a token for the agent account and write it into
that file directly: the plaintext never passes through the browser.

Only the token line is touched; every other line (password fallback,
comments) stays as it was. A new token is verified (file re-read + auth
lookup) before the previous one is revoked; on failure the old file is
restored and the new token revoked. See docs/zh/guides/openclaw-ops.md.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from nblane.core import auth as auth_core
from nblane.core import agent_policy, auth_store
from nblane.core.file_write import atomic_write_text

TOKEN_KEY = "NBLANE_OPENCLAW_API_TOKEN"
PASSWORD_KEY = "NBLANE_OPENCLAW_API_PASSWORD"
ENV_FILE_OVERRIDE = "NBLANE_OPENCLAW_API_ENV_FILE"
USERNAME_ENV = "NBLANE_OPENCLAW_API_USERNAME"
DEFAULT_ACCOUNT = "openclaw"
TOKEN_NAME = "assistant (auto)"

log = logging.getLogger(__name__)


class AgentCredentialsError(RuntimeError):
    """Token setup refused; ``code`` is a stable machine-readable key."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def api_env_path() -> Path:
    """Where the assistant client looks for its credentials file."""
    override = os.environ.get(ENV_FILE_OVERRIDE, "").strip()
    if override:
        return Path(override).expanduser()
    config_home = os.environ.get("XDG_CONFIG_HOME", "").strip()
    root = Path(config_home).expanduser() if config_home else Path.home() / ".config"
    return root / "nblane" / "api.env"


def agent_account_id() -> str:
    """The agent service account the assistant logs in as."""
    return os.environ.get(USERNAME_ENV, "").strip() or DEFAULT_ACCOUNT


def _parse_line(line: str) -> tuple[str, str] | None:
    """``(key, value)`` for a ``KEY=VALUE`` line, else ``None``."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, _, value = stripped.partition("=")
    key = key.strip()
    if key.startswith("export "):
        key = key[len("export "):].strip()
    value = value.strip()
    if value[:1] in ("'", '"'):
        quote = value[0]
        end = value.find(quote, 1)
        value = value[1:end] if end > 0 else value[1:]
    else:
        value = value.split(" #", 1)[0].strip()
    return key, value


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _read_key(text: str | None, key: str) -> str:
    for line in (text or "").splitlines():
        parsed = _parse_line(line)
        if parsed and parsed[0] == key:
            return parsed[1]
    return ""


def read_env_token(path: Path) -> str:
    """The ``NBLANE_OPENCLAW_API_TOKEN`` value in *path* (``""`` if none)."""
    return _read_key(_read_text(path), TOKEN_KEY)


def _token_id(token: str) -> str:
    return auth_core._api_token_id(token) or ""


def _load_users() -> dict[str, auth_core.User]:
    if not auth_core.auth_configured():
        return {}
    try:
        return auth_core.load_users()
    except Exception:  # noqa: BLE001 - status must not fail on a bad users file
        return {}


def status() -> dict[str, Any]:
    """Account + file state for the settings card (never any plaintext)."""
    account = agent_account_id()
    path = api_env_path()
    text = _read_text(path)
    token = _read_key(text, TOKEN_KEY)
    users = _load_users()
    user = users.get(account)
    token_id = _token_id(token)
    owner = auth_core.user_for_api_token(token, users) if token else None
    token_valid = owner is not None and owner.id == account
    created = ""
    if token_valid and user is not None:
        for record in user.api_tokens:
            if record.id == token_id:
                created = record.created
                break
    return {
        "account": account,
        "account_exists": user is not None,
        "account_is_agent": bool(user and agent_policy.is_agent(user)),
        "env_path": str(path),
        "configured": bool(token),
        "token_id": token_id,
        "token_valid": token_valid,
        "created": created,
        "password_fallback": bool(_read_key(text, PASSWORD_KEY)),
    }


def _with_token(text: str | None, token: str) -> str:
    """*text* with the token line replaced (or appended); rest untouched."""
    lines = (text or "").splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        parsed = _parse_line(line)
        if parsed and parsed[0] == TOKEN_KEY:
            if not replaced:
                out.append(f"{TOKEN_KEY}={token}")
                replaced = True
            continue  # drop duplicate token lines
        out.append(line)
    if not replaced:
        out.append(f"{TOKEN_KEY}={token}")
    return "\n".join(out) + "\n"


def _write_env(path: Path, text: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    atomic_write_text(path, text)
    os.chmod(path, 0o600)


def _restore(path: Path, previous: str | None) -> None:
    if previous is None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return
    _write_env(path, previous)


def _verify(path: Path, plaintext: str, account: str) -> bool:
    if read_env_token(path) != plaintext:
        return False
    auth_core.clear_users_cache()
    owner = auth_core.user_for_api_token(plaintext, auth_core.load_users())
    return owner is not None and owner.id == account


def configure_token() -> dict[str, Any]:
    """Mint a token for the agent account and install it into ``api.env``."""
    if not auth_core.auth_configured():
        raise AgentCredentialsError("auth_not_configured", "未开启登录，无需服务账号 token。")
    account = agent_account_id()
    user = auth_core.load_users().get(account)
    if user is None:
        raise AgentCredentialsError("agent_account_missing", f"账号 {account} 不存在。")
    if not agent_policy.is_agent(user):
        raise AgentCredentialsError("not_agent_account", f"账号 {account} 未标记为助手账号。")

    path = api_env_path()
    previous = _read_text(path)
    old_id = _token_id(_read_key(previous, TOKEN_KEY))

    plaintext, record = auth_store.create_api_token(account, TOKEN_NAME)
    try:
        _write_env(path, _with_token(previous, plaintext))
        ok = _verify(path, plaintext, account)
    except OSError:
        ok = False
    if not ok:
        try:
            _restore(path, previous)
        finally:
            try:
                auth_store.revoke_api_token(account, record.id)
            except auth_store.AccountError:
                pass
        log.warning("agent token setup failed for %s; new token %s revoked", account, record.id)
        raise AgentCredentialsError("token_verify_failed", "写入后校验失败，已恢复原文件并作废新 token。")

    rotated = False
    if old_id and old_id != record.id and any(t.id == old_id for t in user.api_tokens):
        try:
            auth_store.revoke_api_token(account, old_id)
            rotated = True
        except auth_store.AccountError:
            pass
    auth_core.clear_users_cache()
    log.info(
        "agent token configured: account=%s token_id=%s file=%s revoked=%s",
        account,
        record.id,
        path,
        old_id if rotated else "-",
    )
    return {**status(), "rotated": rotated}


__all__ = [
    "AgentCredentialsError",
    "agent_account_id",
    "api_env_path",
    "configure_token",
    "read_env_token",
    "status",
]
