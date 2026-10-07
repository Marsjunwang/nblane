"""Writeback trace helper: record an applied owner-page write in agent-activity.yaml.

The pending review queue (candidates applied/dismissed by a human) was
removed; agent writes now apply directly and are undoable via the agent
journal. This module only keeps the provenance trace used by agent writes.
"""

from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from typing import Any

from nblane.core import agent_activity


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def record_writeback_activity(
    profile: str,
    *,
    source_page: str,
    target_owner: str,
    title: str,
    summary: str = "",
    candidate_type: str = "unknown",
    source_ref: str = "",
    refs: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    error: str = "",
    changed_paths: list[str | Path] | None = None,
    status: str = "applied",
) -> dict[str, Any]:
    """Append a writeback Activity item from an owner page."""
    seed = "|".join(
        [
            _clean_text(source_page),
            _clean_text(target_owner),
            _clean_text(candidate_type),
            _clean_text(source_ref),
            _clean_text(title),
            _clean_text(status),
            date.today().isoformat(),
        ]
    )
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:14]
    item = {
        "id": f"act:writeback:{digest}",
        "kind": "writeback",
        "candidate_type": candidate_type,
        "source_page": source_page,
        "source_ref": source_ref,
        "target_owner": target_owner,
        "status": status,
        "title": title,
        "summary": summary,
        "refs": refs or {},
        "payload": payload or {},
        "warnings": list(warnings or []),
        "error": error,
        "changed_paths": [str(path) for path in changed_paths or []],
        "applied_at": date.today().isoformat() if status == "applied" else "",
    }
    return agent_activity.append_activity_item(profile, item)


__all__ = ["record_writeback_activity"]
