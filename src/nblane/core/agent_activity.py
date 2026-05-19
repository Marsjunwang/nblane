"""Profile-scoped Agent Activity / writeback review queue."""

from __future__ import annotations

import copy
import hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from nblane.core import git_backup
from nblane.core.file_write import atomic_write_text
from nblane.core.paths import REPO_ROOT
from nblane.core.profile_io import profile_dir
from nblane.core.yaml_io import _load_yaml_dict

AGENT_ACTIVITY_FILENAME = "agent-activity.yaml"
AGENT_ACTIVITY_SCHEMA_VERSION = "1.0"
ACTIVITY_KINDS = ("candidate", "patch", "writeback")
ACTIVITY_STATUSES = ("pending", "applied", "failed", "dismissed", "superseded")
ACTIVITY_TARGET_OWNERS = (
    "evidence_pool",
    "kanban",
    "public_site",
    "skill_tree",
    "research",
    "resume",
    "output",
    "work",
    "team",
    "profile_context",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _activity_path(profile: str | Path) -> Path:
    if isinstance(profile, Path):
        return profile / AGENT_ACTIVITY_FILENAME
    return profile_dir(profile) / AGENT_ACTIVITY_FILENAME


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _clean_string_list(value: object) -> list[str]:
    raw_items: list[object]
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, tuple):
        raw_items = list(value)
    elif isinstance(value, str):
        raw_items = [
            item
            for chunk in value.splitlines()
            for item in chunk.split(",")
        ]
    else:
        raw_items = []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        text = _clean_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _relative_file(path: str | Path) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        return str(path)


def normalize_activity_item(item: dict[str, Any], *, now: str | None = None) -> dict[str, Any] | None:
    """Return one normalized activity item, preserving extension keys."""
    if not isinstance(item, dict):
        return None
    current = now or _now()
    out = copy.deepcopy(item)
    title = _clean_text(out.get("title"))
    payload = out.get("payload") if isinstance(out.get("payload"), dict) else {}
    refs = out.get("refs") if isinstance(out.get("refs"), dict) else {}
    kind = _clean_text(out.get("kind")) or "candidate"
    if kind not in ACTIVITY_KINDS:
        kind = "candidate"
    status = _clean_text(out.get("status")) or "pending"
    if status not in ACTIVITY_STATUSES:
        status = "pending"
    target_owner = _clean_text(out.get("target_owner")) or "profile_context"
    if target_owner not in ACTIVITY_TARGET_OWNERS:
        target_owner = "profile_context"
    item_id = _clean_text(out.get("id"))
    if not item_id:
        seed = "|".join(
            [
                kind,
                _clean_text(out.get("candidate_type")) or "unknown",
                _clean_text(out.get("source_page")),
                _clean_text(out.get("source_ref")),
                target_owner,
                title,
            ]
        )
        digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
        item_id = f"act:{kind}:{digest}"
    out.update(
        {
            "id": item_id,
            "kind": kind,
            "candidate_type": _clean_text(out.get("candidate_type")) or "unknown",
            "source_page": _clean_text(out.get("source_page")),
            "source_ref": _clean_text(out.get("source_ref")),
            "target_owner": target_owner,
            "status": status,
            "title": title or item_id,
            "summary": _clean_text(out.get("summary")),
            "refs": refs,
            "payload": payload,
            "preview": _clean_text(out.get("preview")),
            "warnings": _clean_string_list(out.get("warnings")),
            "error": _clean_text(out.get("error")),
            "changed_paths": _clean_string_list(out.get("changed_paths")),
            "created": _clean_text(out.get("created")) or current,
            "updated": _clean_text(out.get("updated")) or current,
            "applied_at": _clean_text(out.get("applied_at")),
        }
    )
    files = refs.get("files")
    if files is not None:
        out["refs"]["files"] = [_relative_file(path) for path in _clean_string_list(files)]
    return out


def normalize_agent_activity(raw: dict[str, Any] | None, *, profile: str = "") -> dict[str, Any]:
    """Return a normalized activity document."""
    source = raw if isinstance(raw, dict) else {}
    items: list[dict[str, Any]] = []
    for item in source.get("items") or []:
        if not isinstance(item, dict):
            continue
        normalized = normalize_activity_item(item)
        if normalized is not None:
            items.append(normalized)
    return {
        "schema_version": _clean_text(source.get("schema_version")) or AGENT_ACTIVITY_SCHEMA_VERSION,
        "profile": _clean_text(source.get("profile")) or profile,
        "updated": _clean_text(source.get("updated")),
        "items": items,
    }


def load_agent_activity(profile: str | Path) -> dict[str, Any]:
    """Load agent-activity.yaml; missing files read as an empty queue."""
    path = _activity_path(profile)
    raw = _load_yaml_dict(path)
    profile_name = profile.name if isinstance(profile, Path) else str(profile)
    return normalize_agent_activity(raw, profile=profile_name)


def save_agent_activity(profile: str, activity: dict[str, Any]) -> Path:
    """Persist a normalized activity queue."""
    normalized = normalize_agent_activity(activity, profile=profile)
    normalized["updated"] = _now()
    path = _activity_path(profile)
    body = yaml.dump(
        normalized,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    header = (
        f"# Agent Activity for {profile}\n"
        "# Internal candidate, patch, and writeback review queue.\n\n"
    )
    atomic_write_text(path, header + body)
    git_backup.record_change([path], action=f"update {profile}/agent-activity.yaml")
    return path


def append_activity_item(profile: str, item: dict[str, Any]) -> dict[str, Any]:
    """Append or update one item by id and return the stored item."""
    current = _now()
    normalized = normalize_activity_item(item, now=current)
    if normalized is None:
        raise ValueError("Activity item must be a mapping")
    normalized["updated"] = current
    activity = load_agent_activity(profile)
    items = list(activity.get("items") or [])
    for index, existing in enumerate(items):
        if _clean_text(existing.get("id")) == normalized["id"]:
            merged = copy.deepcopy(existing)
            merged.update(normalized)
            if not normalized.get("created"):
                merged["created"] = existing.get("created") or current
            items[index] = merged
            activity["items"] = items
            save_agent_activity(profile, activity)
            return merged
    items.append(normalized)
    activity["items"] = items
    save_agent_activity(profile, activity)
    return normalized


def update_activity_status(
    profile: str,
    item_id: str,
    status: str,
    *,
    error: str = "",
    warnings: list[str] | None = None,
    changed_paths: list[str | Path] | None = None,
    applied_at: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update one item status and return the stored item."""
    clean_status = _clean_text(status)
    if clean_status not in ACTIVITY_STATUSES:
        raise ValueError(f"Unknown activity status: {status}")
    activity = load_agent_activity(profile)
    items = list(activity.get("items") or [])
    current = _now()
    for index, item in enumerate(items):
        if _clean_text(item.get("id")) != item_id:
            continue
        updated = copy.deepcopy(item)
        updated["status"] = clean_status
        updated["updated"] = current
        if error:
            updated["error"] = error
        if warnings is not None:
            updated["warnings"] = list(warnings)
        if changed_paths is not None:
            updated["changed_paths"] = [_relative_file(path) for path in changed_paths]
        if applied_at is not None:
            updated["applied_at"] = applied_at
        elif clean_status == "applied" and not _clean_text(updated.get("applied_at")):
            updated["applied_at"] = current
        if extra:
            updated.update(copy.deepcopy(extra))
        items[index] = updated
        activity["items"] = items
        save_agent_activity(profile, activity)
        return updated
    raise KeyError(f"Unknown activity item id: {item_id}")


def activity_summary(profile: str) -> dict[str, dict[str, int]]:
    """Return counters for the Activity page."""
    items = load_agent_activity(profile).get("items") or []
    return {
        "status": dict(Counter(_clean_text(item.get("status")) for item in items)),
        "kind": dict(Counter(_clean_text(item.get("kind")) for item in items)),
        "target_owner": dict(Counter(_clean_text(item.get("target_owner")) for item in items)),
        "candidate_type": dict(Counter(_clean_text(item.get("candidate_type")) for item in items)),
    }


def activity_items_for_page(
    profile: str,
    filters: dict[str, str] | None = None,
    *,
    sort: str = "updated_desc",
) -> list[dict[str, Any]]:
    """Return filtered items sorted for review or log-style display."""
    items = list(load_agent_activity(profile).get("items") or [])
    filters = filters or {}
    for key, value in filters.items():
        clean = _clean_text(value)
        if not clean or clean == "all":
            continue
        items = [item for item in items if _clean_text(item.get(key)) == clean]

    def status_rank(item: dict[str, Any]) -> int:
        return 0 if item.get("status") == "pending" else 1

    def updated_key(item: dict[str, Any]) -> str:
        return _clean_text(item.get("updated")) or _clean_text(item.get("created"))

    clean_sort = _clean_text(sort) or "updated_desc"
    if clean_sort == "updated_asc":
        return sorted(items, key=updated_key)
    items = sorted(items, key=updated_key, reverse=True)
    if clean_sort == "queue":
        return sorted(items, key=status_rank)
    return items


def delete_activity_items(profile: str, item_ids: list[str] | tuple[str, ...] | set[str]) -> int:
    """Delete activity items by id and return the number removed."""
    wanted = {_clean_text(item_id) for item_id in item_ids}
    wanted.discard("")
    if not wanted:
        return 0
    activity = load_agent_activity(profile)
    items = list(activity.get("items") or [])
    kept = [item for item in items if _clean_text(item.get("id")) not in wanted]
    removed = len(items) - len(kept)
    if not removed:
        return 0
    activity["items"] = kept
    save_agent_activity(profile, activity)
    return removed


def delete_activity_items_for_filters(
    profile: str,
    filters: dict[str, str] | None = None,
) -> int:
    """Delete all activity items matching simple field filters."""
    matches = activity_items_for_page(profile, filters or {}, sort="updated_desc")
    return delete_activity_items(
        profile,
        [_clean_text(item.get("id")) for item in matches],
    )


__all__ = [
    "ACTIVITY_KINDS",
    "ACTIVITY_STATUSES",
    "ACTIVITY_TARGET_OWNERS",
    "AGENT_ACTIVITY_FILENAME",
    "activity_items_for_page",
    "activity_summary",
    "append_activity_item",
    "delete_activity_items",
    "delete_activity_items_for_filters",
    "load_agent_activity",
    "normalize_activity_item",
    "save_agent_activity",
    "update_activity_status",
]
