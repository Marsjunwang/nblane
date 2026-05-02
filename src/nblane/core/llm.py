"""Thin wrapper around any OpenAI-compatible chat API.

Default configuration via environment variables (or .env at repo root):

    LLM_BASE_URL    API base URL  (default: DashScope compatible API)
    LLM_API_KEY     API key       (required for AI features)
    LLM_MODEL       Model name    (default: qwen3.6-plus)
    UI_LANG         UI language: "en" (default) or "zh"
    LLM_REPLY_LANG  Reply language: "en" (default) or "zh"

Streamlit pages may also call ``configure`` to override these values
for the current Python process/session.
"""

from __future__ import annotations

import os
from collections.abc import Callable

from nblane.core.paths import REPO_ROOT

_ENV_FILE = REPO_ROOT / ".env"

try:
    from dotenv import load_dotenv

    load_dotenv(_ENV_FILE, override=False)
except ImportError:
    pass

_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_DEFAULT_MODEL = "qwen3.6-plus"
_DEFAULT_UI_LANG = "en"
_DEFAULT_REPLY_LANG = "en"
_DEFAULT_TIMEOUT_SECONDS = 90.0

_BASE_URL: str = os.getenv("LLM_BASE_URL", _DEFAULT_BASE_URL)
_API_KEY: str = os.getenv("LLM_API_KEY", "")
_MODEL: str = os.getenv("LLM_MODEL", _DEFAULT_MODEL)
_UI_LANG: str = os.getenv(
    "UI_LANG",
    os.getenv("LLM_REPLY_LANG", _DEFAULT_UI_LANG),
).strip().lower()
_REPLY_LANG: str = os.getenv(
    "LLM_REPLY_LANG", _DEFAULT_REPLY_LANG
).strip().lower()


def configure(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    ui_lang: str | None = None,
    reply_lang: str | None = None,
) -> None:
    """Override LLM settings at runtime.

    ``None`` means "leave the current value unchanged". Empty strings
    for ``base_url`` and ``model`` fall back to the module defaults;
    an empty ``api_key`` intentionally clears the key.
    """
    global _API_KEY, _BASE_URL, _MODEL, _REPLY_LANG, _UI_LANG

    if base_url is not None:
        _BASE_URL = base_url.strip() or _DEFAULT_BASE_URL
    if api_key is not None:
        _API_KEY = api_key.strip()
    if model is not None:
        _MODEL = model.strip() or _DEFAULT_MODEL
    if ui_lang is not None:
        _UI_LANG = ui_lang.strip().lower()
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
        "ui_lang": ui_language(),
        "reply_lang": reply_language(),
        "configured": is_configured(),
    }


def api_key_unmasked() -> str:
    """Return the raw runtime API key for modules that reuse LLM credentials."""
    return _API_KEY


def base_url() -> str:
    """Return the runtime API base URL."""
    return _BASE_URL


def is_dashscope_base_url(url: str) -> bool:
    """Return True when *url* points at a DashScope / Bailian endpoint."""
    clean = str(url or "").strip().lower()
    return any(
        marker in clean
        for marker in (
            "dashscope.aliyuncs.com",
            "dashscope-intl.aliyuncs.com",
            "bailian.aliyuncs.com",
            "bailian.console.aliyun.com",
        )
    )


def is_configured() -> bool:
    """Return True if an API key is set."""
    return bool(_API_KEY)


def model_label() -> str:
    """Return a human-readable label for the current model."""
    return f"{_MODEL} @ {_BASE_URL}"


def timeout_seconds() -> float:
    """Return the OpenAI-compatible client timeout in seconds."""

    try:
        value = float(os.getenv("LLM_TIMEOUT_SECONDS", str(_DEFAULT_TIMEOUT_SECONDS)))
    except ValueError:
        value = _DEFAULT_TIMEOUT_SECONDS
    return max(5.0, value)


def reply_language() -> str:
    """Return the configured reply language code ('en' or 'zh').

    Reads ``LLM_REPLY_LANG`` from the environment.  Any value
    other than ``'zh'`` falls back to ``'en'``.
    """
    return "zh" if _REPLY_LANG == "zh" else "en"


def ui_language() -> str:
    """Return the configured UI language code ('en' or 'zh').

    ``UI_LANG`` controls Streamlit interface text independently from model
    reply language. When ``UI_LANG`` is absent, module initialization falls
    back to ``LLM_REPLY_LANG`` for compatibility with older deployments.
    """
    return "zh" if _UI_LANG == "zh" else "en"


def chat(
    system: str,
    user: str,
    temperature: float = 0.3,
    stream: bool = False,
    *,
    stream_callback: Callable[[str], None] | None = None,
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
            base_url=_BASE_URL,
            api_key=_API_KEY,
            timeout=timeout_seconds(),
        )
        use_stream = stream or stream_callback is not None
        response = client.chat.completions.create(
            model=_MODEL,
            temperature=temperature,
            stream=use_stream,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        if use_stream:
            return _collect_stream_text(response, stream_callback)
        content = response.choices[0].message.content
        return content if content is not None else ""
    except Exception as exc:
        return f"LLM error: {exc}"


def chat_messages(
    system: str,
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    *,
    stream: bool = False,
    stream_callback: Callable[[str], None] | None = None,
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
            base_url=_BASE_URL,
            api_key=_API_KEY,
            timeout=timeout_seconds(),
        )
        use_stream = stream or stream_callback is not None
        response = client.chat.completions.create(
            model=_MODEL,
            temperature=temperature,
            stream=use_stream,
            messages=api_messages,
        )
        if use_stream:
            return _collect_stream_text(response, stream_callback)
        out = response.choices[0].message.content
        return out if out is not None else ""
    except Exception as exc:
        return f"LLM error: {exc}"


def _collect_stream_text(
    response: object,
    stream_callback: Callable[[str], None] | None,
) -> str:
    """Collect OpenAI-compatible streaming chunks into final text."""
    chunks: list[str] = []
    for chunk in response:  # type: ignore[operator]
        choices = getattr(chunk, "choices", None)
        if not choices:
            continue
        delta = getattr(choices[0], "delta", None)
        content = getattr(delta, "content", None)
        if content is None and isinstance(delta, dict):
            content = delta.get("content")
        if not content:
            continue
        text = str(content)
        chunks.append(text)
        if stream_callback is not None:
            stream_callback(text)
    return "".join(chunks)
