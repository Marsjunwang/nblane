"""Home command bar: intent routing and confirmed write application.

The command bar on the Home dashboard turns one line of natural language
into an :class:`~nblane.core.intent.IntentAction` via the offline heuristic
parser. This module owns the two decisions around that parse:

- :func:`resolve_command_text` — what happens on submit. Write intents
  (``kanban.add`` / ``evidence.capture``) become a pending-confirmation
  payload and write NOTHING; read-only intents (``navigate`` /
  ``review.weekly_summary``) resolve to a page; anything else resolves to
  the inline help hint.
- :func:`apply_kanban_add_intent` — the confirmed ``kanban.add`` write:
  re-read the board from disk, append one :class:`KanbanTask`, and persist
  through the conflict-safe merge save.

The Streamlit event handler in ``app.py`` stays a thin adapter over these
functions so the behavior is unit-testable without a runtime.
"""

from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from typing import Any

from nblane.core.intent import IntentAction, parse_intent
from nblane.core.kanban_io import (
    KANBAN_DOING,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
    ensure_kanban_task_ids,
    parse_kanban,
)
from nblane.core.kanban_merge import save_kanban_with_merge
from nblane.core.models import KanbanTask

KIND_KANBAN_ADD = "kanban.add"
KIND_EVIDENCE_CAPTURE = "evidence.capture"
KIND_REVIEW_WEEKLY = "review.weekly_summary"
KIND_NAVIGATE = "navigate"
KIND_UNKNOWN = "unknown"

# Kinds that mutate profile files and therefore require the confirmation card.
CONFIRM_KINDS = (KIND_KANBAN_ADD, KIND_EVIDENCE_CAPTURE)

REVIEW_PAGE = "pages/8_Review.py"

# Intent columns are the short display names; kanban.md sections differ.
_COLUMN_TO_SECTION = {
    "Doing": KANBAN_DOING,
    "Queue": KANBAN_QUEUE,
    "Someday": KANBAN_SOMEDAY,
}


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _clean_tags(value: object) -> list[str]:
    if isinstance(value, str):
        value = [part.strip() for part in value.split(",")]
    if not isinstance(value, (list, tuple)):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        tag = _clean_text(item).lstrip("#").strip()
        if tag and tag not in seen:
            seen.add(tag)
            out.append(tag)
    return out


def intent_needs_confirmation(kind: str) -> bool:
    """Return True for intent kinds that must be confirmed before writing."""
    return kind in CONFIRM_KINDS


def new_intent_id(intent: IntentAction, *, today: date | None = None) -> str:
    """Deterministic id for one pending intent (kind + raw text + day)."""
    day = (today or date.today()).isoformat()
    seed = f"{intent.kind}|{intent.raw}|{day}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    return f"intent:{intent.kind}:{digest}"


def pending_intent_payload(
    intent: IntentAction,
    *,
    intent_id: str = "",
    today: date | None = None,
) -> dict[str, Any]:
    """Stable JSON shape for the React confirmation card."""
    return {
        "id": intent_id or new_intent_id(intent, today=today),
        "kind": intent.kind,
        "title": intent.title,
        "column": intent.column,
        "due": intent.due,
        "tags": list(intent.tags),
        "raw": intent.raw,
        "confidence": float(intent.confidence),
    }


def resolve_command_text(text: str, *, today: date | None = None) -> dict[str, Any]:
    """Route one command-bar submission. Pure: never touches the disk.

    Outcomes: ``pending`` (write intent, carries the confirmation payload),
    ``navigate`` (read-only, carries the target page), or ``help``
    (unparseable — the UI shows the example commands hint).
    """
    intent = parse_intent(text, today=today)
    if intent_needs_confirmation(intent.kind):
        return {
            "outcome": "pending",
            "intent": pending_intent_payload(intent, today=today),
        }
    if intent.kind == KIND_NAVIGATE and intent.page:
        return {"outcome": "navigate", "page": intent.page}
    if intent.kind == KIND_REVIEW_WEEKLY:
        return {"outcome": "navigate", "page": REVIEW_PAGE}
    return {"outcome": "help", "raw": intent.raw}


def kanban_task_from_intent(
    fields: dict[str, Any],
    *,
    today: date | None = None,
) -> KanbanTask:
    """Project pending-intent fields onto one :class:`KanbanTask`.

    ``started_on`` is set only for Doing (the stall signal reads it); a due
    date rides in ``details`` as ``due: <iso>`` — KanbanTask has no due
    field, and details round-trip through kanban.md untouched.
    """
    day = (today or date.today()).isoformat()
    section = _COLUMN_TO_SECTION.get(
        _clean_text(fields.get("column")) or "Doing", KANBAN_DOING
    )
    details: list[str] = []
    due = _clean_text(fields.get("due"))
    if due:
        details.append(f"due: {due}")
    return KanbanTask(
        title=_clean_text(fields.get("title")),
        started_on=day if section == KANBAN_DOING else None,
        tags=", ".join(_clean_tags(fields.get("tags"))),
        details=details,
    )


def apply_kanban_add_intent(
    profile: str | Path,
    fields: dict[str, Any],
    *,
    today: date | None = None,
) -> KanbanTask | None:
    """Append one confirmed task to kanban.md and return it; None on blank.

    The board is re-parsed from disk at confirm time (the pending intent may
    be several reruns old), then saved through ``save_kanban_with_merge``
    with ``base=None`` so a concurrent external edit is union-merged rather
    than silently overwritten.
    """
    task = kanban_task_from_intent(fields, today=today)
    if not task.title:
        return None
    section = _COLUMN_TO_SECTION.get(
        _clean_text(fields.get("column")) or "Doing", KANBAN_DOING
    )
    sections = parse_kanban(profile)
    sections.setdefault(section, []).append(task)
    profile_name = profile.name if isinstance(profile, Path) else str(profile)
    ensured = ensure_kanban_task_ids(sections, profile_name)
    result = save_kanban_with_merge(profile, ensured, None)
    persisted = result.sections.get(section) or []
    return persisted[-1] if persisted else None


__all__ = [
    "CONFIRM_KINDS",
    "KIND_EVIDENCE_CAPTURE",
    "KIND_KANBAN_ADD",
    "KIND_NAVIGATE",
    "KIND_REVIEW_WEEKLY",
    "KIND_UNKNOWN",
    "REVIEW_PAGE",
    "apply_kanban_add_intent",
    "intent_needs_confirmation",
    "kanban_task_from_intent",
    "new_intent_id",
    "pending_intent_payload",
    "resolve_command_text",
]
