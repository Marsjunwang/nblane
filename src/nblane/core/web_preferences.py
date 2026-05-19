"""Profile-scoped Web UI preferences without secrets."""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from nblane.core import git_backup
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_io import profile_dir
from nblane.core.yaml_io import _load_yaml_dict

WEB_PREFERENCES_FILENAME = "web-preferences.yaml"
WEB_PREFERENCES_SCHEMA_VERSION = "1.0"
_SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|access[_-]?token|token|secret|password|authorization|cookie)",
    re.IGNORECASE,
)
_AI_BACKENDS = {"llm", "codex"}
_LANGUAGES = {"en", "zh"}
_GRANULARITIES = {"milestone", "checklist", "implementation"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def web_preferences_path(profile: str | Path) -> Path:
    """Return the profile Web preferences path."""

    if isinstance(profile, Path):
        return profile / WEB_PREFERENCES_FILENAME
    return profile_dir(profile) / WEB_PREFERENCES_FILENAME


def load_web_preferences(profile: str | Path) -> dict[str, Any]:
    """Load normalized Web preferences; missing files read as defaults."""

    path = web_preferences_path(profile)
    raw = _load_yaml_dict(path)
    profile_name = profile.name if isinstance(profile, Path) else str(profile)
    return normalize_web_preferences(raw, profile=profile_name)


def save_web_preferences(profile: str, preferences: dict[str, Any]) -> Path:
    """Persist normalized Web preferences."""

    normalized = normalize_web_preferences(preferences, profile=profile)
    normalized["updated"] = _now()
    path = web_preferences_path(profile)
    body = yaml.dump(
        normalized,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    header = (
        f"# Web preferences for {profile}\n"
        "# Non-secret UI and AI usage preferences only. Do not store API keys.\n\n"
    )
    atomic_write_text(path, header + body)
    git_backup.record_change([path], action=f"update {profile}/web-preferences.yaml")
    return path


def update_web_preferences(profile: str, patch: dict[str, Any]) -> bool:
    """Merge a partial non-secret preferences patch and persist when changed."""

    current = load_web_preferences(profile)
    merged = _deep_merge(current, _strip_secret_keys(copy.deepcopy(patch)))
    normalized = normalize_web_preferences(merged, profile=profile)
    comparable_current = copy.deepcopy(current)
    comparable_current.pop("updated", None)
    comparable_next = copy.deepcopy(normalized)
    comparable_next.pop("updated", None)
    if comparable_current == comparable_next:
        return False
    save_web_preferences(profile, normalized)
    return True


def normalize_web_preferences(
    raw: dict[str, Any] | None,
    *,
    profile: str = "",
) -> dict[str, Any]:
    """Return a safe, white-listed Web preferences document."""

    source = _strip_secret_keys(raw if isinstance(raw, dict) else {})
    ai = source.get("ai") if isinstance(source.get("ai"), dict) else {}
    llm = ai.get("llm") if isinstance(ai.get("llm"), dict) else {}
    kanban = source.get("kanban") if isinstance(source.get("kanban"), dict) else {}
    backend = _clean_text(ai.get("kanban_backend"))
    ui_lang = _language(llm.get("ui_lang"))
    reply_lang = _language(llm.get("reply_lang"))
    granularity = _clean_text(kanban.get("subtask_granularity"))
    if granularity not in _GRANULARITIES:
        granularity = ""
    return {
        "schema_version": _clean_text(source.get("schema_version"))
        or WEB_PREFERENCES_SCHEMA_VERSION,
        "profile": profile or _clean_text(source.get("profile")),
        "updated": _clean_text(source.get("updated")),
        "ai": {
            "llm": {
                "provider": _clean_text(llm.get("provider")),
                "base_url": _clean_text(llm.get("base_url")),
                "model": _clean_text(llm.get("model")),
                "custom_model": _clean_text(llm.get("custom_model")),
                "ui_lang": ui_lang,
                "reply_lang": reply_lang,
            },
            "kanban_backend": backend if backend in _AI_BACKENDS else "",
        },
        "kanban": {
            "subtask_granularity": granularity,
            "subtask_style_hint": _clean_text(kanban.get("subtask_style_hint")),
        },
    }


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in patch.items():
        if (
            isinstance(value, dict)
            and isinstance(out.get(key), dict)
        ):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _strip_secret_keys(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, child in value.items():
            if _SECRET_KEY_RE.search(str(key)):
                continue
            out[key] = _strip_secret_keys(child)
        return out
    if isinstance(value, list):
        return [_strip_secret_keys(item) for item in value]
    return value


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _language(value: object) -> str:
    clean = _clean_text(value).lower()
    return clean if clean in _LANGUAGES else ""


__all__ = [
    "WEB_PREFERENCES_FILENAME",
    "WEB_PREFERENCES_SCHEMA_VERSION",
    "load_web_preferences",
    "normalize_web_preferences",
    "save_web_preferences",
    "update_web_preferences",
    "web_preferences_path",
]
