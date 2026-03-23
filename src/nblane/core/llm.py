"""Thin wrapper around any OpenAI-compatible chat API.

Configuration via environment variables (or .env at repo root):

    LLM_BASE_URL    API base URL  (default: https://api.openai.com/v1)
    LLM_API_KEY     API key       (required for AI features)
    LLM_MODEL       Model name    (default: gpt-4o)
    LLM_REPLY_LANG  Reply language: "en" (default) or "zh"
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

_BASE_URL: str = os.getenv(
    "LLM_BASE_URL", "https://api.openai.com/v1"
)
_API_KEY: str = os.getenv("LLM_API_KEY", "")
_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
_REPLY_LANG: str = os.getenv(
    "LLM_REPLY_LANG", "en"
).strip().lower()


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
            "Add LLM_API_KEY to the .env file."
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
            "Add LLM_API_KEY to the .env file."
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
