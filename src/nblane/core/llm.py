"""Thin wrapper around any OpenAI-compatible chat API.

Default configuration via environment variables (or .env at repo root):

    LLM_BASE_URL    API base URL  (default: DashScope compatible API)
    LLM_API_KEY     API key       (required for AI features)
    LLM_MODEL       Model name    (default: qwen3.6-plus)
    LLM_REPLY_LANG  Reply language: "en" (default) or "zh"

Streamlit pages may also call ``configure`` to override these values
for the current Python process/session.
"""

from __future__ import annotations

import os

from nblane.core.paths import REPO_ROOT

_ENV_FILE = REPO_ROOT / ".env"

try:
    from dotenv import load_dotenv

    load_dotenv(_ENV_FILE, override=False)
except ImportError:
    pass

_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_DEFAULT_MODEL = "qwen3.6-plus"
_DEFAULT_REPLY_LANG = "en"

_BASE_URL: str = os.getenv("LLM_BASE_URL", _DEFAULT_BASE_URL)
_API_KEY: str = os.getenv("LLM_API_KEY", "")
_MODEL: str = os.getenv("LLM_MODEL", _DEFAULT_MODEL)
_REPLY_LANG: str = os.getenv(
    "LLM_REPLY_LANG", "en"
).strip().lower()


def configure(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    reply_lang: str | None = None,
) -> None:
    """Override LLM settings at runtime.

    ``None`` means "leave the current value unchanged". Empty strings
    for ``base_url`` and ``model`` fall back to the module defaults;
    an empty ``api_key`` intentionally clears the key.
    """
    global _API_KEY, _BASE_URL, _MODEL, _REPLY_LANG

    if base_url is not None:
        _BASE_URL = base_url.strip() or _DEFAULT_BASE_URL
    if api_key is not None:
        _API_KEY = api_key.strip()
    if model is not None:
        _MODEL = model.strip() or _DEFAULT_MODEL
    if reply_lang is not None:
        _REPLY_LANG = reply_lang.strip().lower()


def _masked_api_key(value: str) -> str:
    """Return a display-safe representation of an API key."""
    if not value:
        return ""
    if len(value) <= 8:
        return "set"
    return f"{value[:4]}...{value[-4:]}"


def current_config(
    *, mask_key: bool = True
) -> dict[str, str | bool]:
    """Return the current runtime LLM configuration."""
    key = _masked_api_key(_API_KEY) if mask_key else _API_KEY
    return {
        "base_url": _BASE_URL,
        "api_key": key,
        "model": _MODEL,
        "reply_lang": reply_language(),
        "configured": is_configured(),
    }


def is_configured() -> bool:
    """Return True if an API key is set."""
    return bool(_API_KEY)


def model_label() -> str:
    """Return a human-readable label for the current model."""
    return f"{_MODEL} @ {_BASE_URL}"


def reply_language() -> str:
    """Return the configured reply language code ('en' or 'zh').

    Reads ``LLM_REPLY_LANG`` from the environment.  Any value
    other than ``'zh'`` falls back to ``'en'``.
    """
    return "zh" if _REPLY_LANG == "zh" else "en"


def chat(
    system: str,
    user: str,
    temperature: float = 0.3,
    stream: bool = False,
) -> str:
    """Send a single-turn chat and return the reply text.

    Returns an error string (not raises) on failure so
    callers can display it gracefully in the UI.
    """
    if not is_configured():
        return (
            "AI features not configured. "
            "Set an API key in the sidebar AI / LLM settings "
            "or add LLM_API_KEY to the .env file."
        )
    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=_BASE_URL, api_key=_API_KEY
        )
        response = client.chat.completions.create(
            model=_MODEL,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content
        return content if content is not None else ""
    except Exception as exc:
        return f"LLM error: {exc}"


def chat_messages(
    system: str,
    messages: list[dict[str, str]],
    temperature: float = 0.3,
) -> str:
    """Multi-turn chat: *system* plus *messages* (user/assistant only).

    Each item must have ``role`` ``user`` or ``assistant`` and
    ``content`` text. Returns assistant text or an error string on failure.
    """
    if not is_configured():
        return (
            "AI features not configured. "
            "Set an API key in the sidebar AI / LLM settings "
            "or add LLM_API_KEY to the .env file."
        )
    api_messages: list[dict[str, str]] = [
        {"role": "system", "content": system},
    ]
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if role not in ("user", "assistant"):
            continue
        if not isinstance(content, str):
            content = str(content)
        api_messages.append({"role": role, "content": content})
    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=_BASE_URL, api_key=_API_KEY
        )
        response = client.chat.completions.create(
            model=_MODEL,
            temperature=temperature,
            messages=api_messages,
        )
        out = response.choices[0].message.content
        return out if out is not None else ""
    except Exception as exc:
        return f"LLM error: {exc}"
