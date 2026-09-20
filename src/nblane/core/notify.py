"""Reverse push channel: nblane -> OpenClaw webhook -> WeChat.

MVP for docs/zh/architecture/openclaw-deep-integration.md section 3.4
(option 1, webhook automation). A ``webhooks`` mapping in ``openclaw.json``
routes ``/hooks/<name>`` to a gateway automation; nblane only POSTs to the
hook URL and never talks to WeChat directly.

Configuration (environment or ``.env``):

    NBLANE_OPENCLAW_HOOK_URL    Hook URL (default: http://127.0.0.1:18789/hooks/agent)
    NBLANE_OPENCLAW_HOOK_TOKEN  Bearer token (required; same value as the
                                gateway's ``cron.webhookToken``)

NOTE: the gateway-side payload contract is not fully verified yet. The
conservative shape ``{"text": ..., "source": "nblane"}`` must be confirmed
against the live OpenClaw gateway before first real use.

Security: the token is read only from env / ``.env`` and is never logged,
printed, or included in returned error strings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from nblane.core.paths import REPO_ROOT

HOOK_URL_ENV = "NBLANE_OPENCLAW_HOOK_URL"
HOOK_TOKEN_ENV = "NBLANE_OPENCLAW_HOOK_TOKEN"
DEFAULT_HOOK_URL = "http://127.0.0.1:18789/hooks/agent"
DEFAULT_TIMEOUT_SECONDS = 10.0
SOURCE_LABEL = "nblane"

_env_file_override = os.getenv("NBLANE_ENV_FILE", "").strip()
_ENV_FILE = Path(_env_file_override) if _env_file_override else REPO_ROOT / ".env"

# ``http_post`` callable signature used by ``send_notification``; the response
# only needs a ``status_code`` attribute (httpx.Response qualifies).
HttpPost = Callable[..., Any]


class NotifyConfigError(RuntimeError):
    """Raised when the webhook configuration is missing or invalid."""


def _load_dotenv() -> None:
    """Best-effort load of the repo ``.env`` (does not override real env)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(_ENV_FILE, override=False)


def resolve_hook_url() -> str:
    """Return the configured hook URL, falling back to the default."""
    _load_dotenv()
    return os.environ.get(HOOK_URL_ENV, "").strip() or DEFAULT_HOOK_URL


def resolve_hook_token() -> str:
    """Return the configured hook token (``""`` when unset)."""
    _load_dotenv()
    return os.environ.get(HOOK_TOKEN_ENV, "").strip()


@dataclass(frozen=True)
class NotifyConfig:
    """Resolved webhook configuration."""

    hook_url: str
    hook_token: str
    timeout: float = DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> "NotifyConfig":
        """Resolve config from env / ``.env``; raise when the token is unset."""
        token = resolve_hook_token()
        if not token:
            raise NotifyConfigError(
                f"未设置 {HOOK_TOKEN_ENV}。请在 .env 或环境变量中配置该值"
                "（与 OpenClaw openclaw.json 的 cron.webhookToken 一致），"
                "再重试 nblane notify。"
            )
        return cls(hook_url=resolve_hook_url(), hook_token=token)


def build_payload(text: str) -> dict[str, str]:
    """Build the webhook request payload (contract pending verification)."""
    return {"text": text, "source": SOURCE_LABEL}


def _default_http_post(
    url: str, *, json: dict, headers: dict[str, str], timeout: float
) -> Any:
    import httpx

    return httpx.post(url, json=json, headers=headers, timeout=timeout)


def _safe_error(exc: Exception) -> str:
    """Return a bounded, token-free error string."""
    return str(exc)[:300]


def send_notification(
    text: str,
    *,
    config: NotifyConfig | None = None,
    http_post: HttpPost | None = None,
) -> dict[str, Any]:
    """POST *text* to the OpenClaw webhook; return a result dict.

    Returns ``{"ok": bool, "status": int | None, "error": str | None}``.
    Never raises for network/HTTP failures; ``NotifyConfig.from_env`` may
    raise :class:`NotifyConfigError` when no token is configured.
    """
    config = config or NotifyConfig.from_env()
    payload = build_payload(text)
    headers = {
        "Authorization": f"Bearer {config.hook_token}",
        "Content-Type": "application/json",
    }
    poster = http_post or _default_http_post
    try:
        response = poster(
            config.hook_url,
            json=payload,
            headers=headers,
            timeout=config.timeout,
        )
    except Exception as exc:
        return {"ok": False, "status": None, "error": _safe_error(exc)}
    status = getattr(response, "status_code", None)
    ok = isinstance(status, int) and 200 <= status < 300
    error = None if ok else f"HTTP {status}"
    return {"ok": ok, "status": status, "error": error}


__all__ = [
    "DEFAULT_HOOK_URL",
    "DEFAULT_TIMEOUT_SECONDS",
    "HOOK_TOKEN_ENV",
    "HOOK_URL_ENV",
    "NotifyConfig",
    "NotifyConfigError",
    "build_payload",
    "resolve_hook_token",
    "resolve_hook_url",
    "send_notification",
]
