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
import re
from collections.abc import Callable
from pathlib import Path

from nblane.core.paths import REPO_ROOT

_env_file_override = os.getenv("NBLANE_ENV_FILE", "").strip()
_ENV_FILE = Path(_env_file_override) if _env_file_override else REPO_ROOT / ".env"

try:
    from dotenv import load_dotenv

    load_dotenv(_ENV_FILE, override=False)
except ImportError:
    pass

_CJK_RE = re.compile(r"[一-鿿]")


def _env_file_mtime() -> float:
    try:
        return _ENV_FILE.stat().st_mtime
    except OSError:
        return 0.0


_ENV_FILE_MTIME: float = _env_file_mtime()

_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_DEFAULT_MODEL = "qwen3.6-plus"
_DEFAULT_UI_LANG = "en"
_DEFAULT_REPLY_LANG = ""
_DEFAULT_TIMEOUT_SECONDS = 90.0
# OpenAI-compatible gateways (DashScope qwen in particular) cap the output at a
# low default (~2000 tokens) when ``max_tokens`` is omitted, which silently
# truncates long generations such as a whole-document reorganize. Send an
# explicit, generous ceiling instead. Override via ``LLM_MAX_TOKENS``.
_DEFAULT_MAX_TOKENS = 8192

_BASE_URL: str = os.getenv("LLM_BASE_URL", _DEFAULT_BASE_URL)
_API_KEY: str = os.getenv("LLM_API_KEY", "")
_MODEL: str = os.getenv("LLM_MODEL", _DEFAULT_MODEL)
_UI_LANG: str = os.getenv("UI_LANG", _DEFAULT_UI_LANG).strip().lower()
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


def set_env_connection(base_url: str, api_key: str, model: str) -> None:
    """Persist the deployment-wide LLM connection to ``.env`` and apply it live.

    Writes only ``LLM_BASE_URL``/``LLM_API_KEY``/``LLM_MODEL`` via
    ``dotenv.set_key``, which edits the file in place and preserves comments
    and unrelated variables. Raises ``RuntimeError`` if python-dotenv's
    ``set_key`` isn't available rather than risk a destructive rewrite.
    """
    try:
        from dotenv import set_key
    except ImportError as exc:
        raise RuntimeError(
            "python-dotenv is required to save LLM connection settings"
        ) from exc

    global _ENV_FILE_MTIME

    if not _ENV_FILE.exists():
        _ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        _ENV_FILE.touch(mode=0o600)
        os.chmod(_ENV_FILE, 0o600)

    clean_base_url = base_url.strip() or _DEFAULT_BASE_URL
    clean_api_key = api_key.strip()
    clean_model = model.strip() or _DEFAULT_MODEL

    set_key(str(_ENV_FILE), "LLM_BASE_URL", clean_base_url)
    set_key(str(_ENV_FILE), "LLM_API_KEY", clean_api_key)
    set_key(str(_ENV_FILE), "LLM_MODEL", clean_model)

    os.environ["LLM_BASE_URL"] = clean_base_url
    os.environ["LLM_API_KEY"] = clean_api_key
    os.environ["LLM_MODEL"] = clean_model

    configure(base_url=clean_base_url, api_key=clean_api_key, model=clean_model)
    _ENV_FILE_MTIME = _env_file_mtime()


def reload_env_if_changed() -> None:
    """Reload connection vars from ``.env`` if the file changed on disk.

    Lets a separate process (e.g. the Reader API sidecar) pick up a
    connection change made through the UI of another process, within one
    request, without a restart. Only ``LLM_BASE_URL``/``LLM_API_KEY``/
    ``LLM_MODEL`` are reloaded; language stays session/profile-scoped.
    """
    global _ENV_FILE_MTIME

    current_mtime = _env_file_mtime()
    if current_mtime <= _ENV_FILE_MTIME:
        return

    try:
        from dotenv import load_dotenv

        load_dotenv(_ENV_FILE, override=True)
    except ImportError:
        return

    configure(
        base_url=os.getenv("LLM_BASE_URL", ""),
        api_key=os.getenv("LLM_API_KEY", ""),
        model=os.getenv("LLM_MODEL", ""),
    )
    _ENV_FILE_MTIME = current_mtime


def verify_connection(*, timeout: float | None = None) -> dict[str, str | bool]:
    """Send a minimal ping to confirm the current connection actually works.

    Returns ``{"ok": bool, "detail": str}``. On failure, ``detail`` carries
    the raw exception text truncated to a bounded length so a wrong key or
    model is diagnosable without dumping an unbounded provider error body.
    """
    if not is_configured():
        return {"ok": False, "detail": "no api key configured"}
    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=_BASE_URL,
            api_key=_API_KEY,
            timeout=min(timeout or 15.0, timeout_seconds()),
        )
        client.chat.completions.create(
            model=_MODEL,
            temperature=0,
            max_tokens=5,
            messages=[{"role": "user", "content": "reply OK"}],
        )
        return {"ok": True, "detail": ""}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)[:300]}


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


def max_tokens_default() -> int:
    """Return the default output token ceiling for chat completions.

    Reads ``LLM_MAX_TOKENS`` from the environment; falls back to
    ``_DEFAULT_MAX_TOKENS``. Sending an explicit ceiling avoids the silent
    low-default truncation some gateways apply when ``max_tokens`` is omitted.
    """

    try:
        value = int(os.getenv("LLM_MAX_TOKENS", str(_DEFAULT_MAX_TOKENS)))
    except ValueError:
        value = _DEFAULT_MAX_TOKENS
    return max(256, value)


def reply_language(text: str | None = None) -> str:
    """Return the resolved reply language code ('en' or 'zh').

    ``LLM_REPLY_LANG`` is ``"zh"``/``"en"`` for a fixed reply language, or
    ``"auto"`` (also the default when unset) to follow the input: when
    *text* is given, detect Chinese vs. English from its characters; when no
    *text* is available, fall back to the UI language.
    """
    if _REPLY_LANG == "zh":
        return "zh"
    if _REPLY_LANG == "en":
        return "en"
    if text:
        return "zh" if _CJK_RE.search(text) else "en"
    return ui_language()


def reply_language_mode() -> str:
    """Return the raw configured reply-language mode ('zh'/'en'/'auto').

    Unlike :func:`reply_language`, this is not resolved against any input
    text — callers that need a stable cache key (rather than the language a
    specific request would resolve to) should use this instead.
    """
    if _REPLY_LANG in ("zh", "en"):
        return _REPLY_LANG
    return "auto"


def ui_language() -> str:
    """Return the configured UI language code ('en' or 'zh').

    ``UI_LANG`` controls Streamlit interface text independently from model
    reply language.
    """
    return "zh" if _UI_LANG == "zh" else "en"


def chat(
    system: str,
    user: str,
    temperature: float = 0.3,
    stream: bool = False,
    *,
    stream_callback: Callable[[str], None] | None = None,
    model: str | None = None,
    timeout: float | None = None,
    max_tokens: int | None = None,
    meta_out: dict | None = None,
) -> str:
    """Send a single-turn chat and return the reply text.

    Returns an error string (not raises) on failure so
    callers can display it gracefully in the UI.

    When *meta_out* is provided it is populated with response metadata such as
    ``finish_reason`` so callers can detect length-truncated output.
    """
    reload_env_if_changed()
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
            timeout=timeout or timeout_seconds(),
        )
        use_stream = stream or stream_callback is not None
        response = client.chat.completions.create(
            model=str(model or "").strip() or _MODEL,
            temperature=temperature,
            stream=use_stream,
            max_tokens=max_tokens if max_tokens is not None else max_tokens_default(),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        if use_stream:
            return _collect_stream_text(response, stream_callback, meta_out=meta_out)
        if meta_out is not None:
            meta_out["finish_reason"] = _clean_finish_reason(response)
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
    model: str | None = None,
    timeout: float | None = None,
    max_tokens: int | None = None,
    meta_out: dict | None = None,
) -> str:
    """Multi-turn chat: *system* plus *messages* (user/assistant only).

    Each item must have ``role`` ``user`` or ``assistant`` and
    ``content`` text. Returns assistant text or an error string on failure.
    """
    reload_env_if_changed()
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
            timeout=timeout or timeout_seconds(),
        )
        use_stream = stream or stream_callback is not None
        response = client.chat.completions.create(
            model=str(model or "").strip() or _MODEL,
            temperature=temperature,
            stream=use_stream,
            max_tokens=max_tokens if max_tokens is not None else max_tokens_default(),
            messages=api_messages,
        )
        if use_stream:
            return _collect_stream_text(response, stream_callback, meta_out=meta_out)
        if meta_out is not None:
            meta_out["finish_reason"] = _clean_finish_reason(response)
        out = response.choices[0].message.content
        return out if out is not None else ""
    except Exception as exc:
        return f"LLM error: {exc}"


def _clean_finish_reason(response: object) -> str:
    """Extract ``finish_reason`` from a non-streamed completion, if present."""

    try:
        choices = getattr(response, "choices", None)
        if not choices:
            return ""
        return str(getattr(choices[0], "finish_reason", "") or "")
    except Exception:
        return ""


def _collect_stream_text(
    response: object,
    stream_callback: Callable[[str], None] | None,
    *,
    meta_out: dict | None = None,
) -> str:
    """Collect OpenAI-compatible streaming chunks into final text.

    When *meta_out* is provided, records the final ``finish_reason`` so callers
    can detect length-truncated output (``finish_reason == "length"``).
    """
    chunks: list[str] = []
    finish_reason = ""
    for chunk in response:  # type: ignore[operator]
        choices = getattr(chunk, "choices", None)
        if not choices:
            continue
        reason = getattr(choices[0], "finish_reason", None)
        if reason:
            finish_reason = str(reason)
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
    if meta_out is not None:
        meta_out["finish_reason"] = finish_reason
    return "".join(chunks)
