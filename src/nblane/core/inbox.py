"""Typed YAML helpers, tags, and clarify flows for profile inbox items."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from nblane.core import git_backup
from nblane.core.file_write import atomic_write_text
from nblane.core.paths import PROFILES_DIR
from nblane.core.yaml_io import _load_yaml_dict

INBOX_FILENAME = "inbox.yaml"
INBOX_STATUSES = (
    "inbox",
    "captured",
    "clarified",
    "active",
    "archived",
    "discarded",
)
CLARIFY_ACTIONS = (
    "to_kanban_queue",
    "to_learning_resource",
    "to_activity_habit",
    "to_evidence_draft",
    "discard",
    "archive",
)


def profile_dir(name: str) -> Path:
    """Return path to ``profiles/{name}``."""
    return PROFILES_DIR / name


def _profile_file_path(
    name_or_dir: str | Path,
    filename: str,
) -> Path:
    """Resolve a profile-scoped file path from a name, directory, or file."""
    if isinstance(name_or_dir, Path):
        if name_or_dir.suffix in (".yaml", ".yml"):
            return name_or_dir
        return name_or_dir / filename
    raw = name_or_dir.strip()
    path = Path(raw)
    if (
        path.suffix in (".yaml", ".yml")
        or "/" in raw
        or raw.startswith(".")
        or path.exists()
    ):
        return path if path.suffix else path / filename
    return profile_dir(raw) / filename


def _profile_name(name_or_dir: str | Path) -> str:
    """Return the profile name portion of a profile path or name."""
    if name_or_dir is None:
        return ""
    if isinstance(name_or_dir, Path):
        return name_or_dir.stem if name_or_dir.suffix else name_or_dir.name
    return Path(name_or_dir).stem if "/" in name_or_dir else name_or_dir


def _clean_text(value: object) -> str:
    """Return a stripped string, tolerating ``None``."""
    return str(value or "").strip()


def _clean_metadata(value: object | None) -> dict[str, object]:
    """Normalize YAML metadata into a string-key mapping."""
    if not isinstance(value, dict):
        return {}
    out: dict[str, object] = {}
    for key, item in value.items():
        clean_key = _clean_text(key)
        if clean_key:
            out[clean_key] = item
    return out


def _clean_tags(value: object) -> list[str]:
    """Normalize YAML tag values into unique non-empty strings."""
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.replace("\n", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        raw_items: list[str] = []
        for item in value:
            if isinstance(item, str):
                raw_items.extend(item.replace("\n", ",").split(","))
            else:
                clean = _clean_text(item)
                if clean:
                    raw_items.append(clean)
    else:
        clean = _clean_text(value)
        raw_items = [clean] if clean else []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        clean = _clean_text(item)
        if not clean:
            continue
        key = clean.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return out


def _event_date(at: str | None) -> str:
    """Return the event timestamp for history entries."""
    clean = _clean_text(at)
    if clean:
        return clean
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _next_item_id(items: list["InboxItem"]) -> str:
    """Return the next stable inbox item id."""
    today = date.today().strftime("%Y%m%d")
    max_index = 0
    for item in items:
        suffix = item.id.rsplit("_", 1)[-1].removeprefix("item-")
        try:
            max_index = max(max_index, int(suffix))
        except ValueError:
            continue
    return f"inbox_{today}_{max_index + 1:03d}"


@dataclass
class InboxHistoryEvent:
    """One transition recorded against an inbox item."""

    at: str
    action: str
    from_status: str = ""
    to_status: str = ""
    note: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "InboxHistoryEvent":
        """Build a history event from a YAML-loaded mapping."""
        if not isinstance(data, dict):
            return cls(at="", action="")
        return cls(
            at=_clean_text(data.get("at")),
            action=_clean_text(data.get("action")),
            from_status=_clean_text(data.get("from_status")),
            to_status=_clean_text(data.get("to_status")),
            note=_clean_text(data.get("note")),
            metadata=_clean_metadata(data.get("metadata")),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize a history event for YAML output."""
        out: dict[str, object] = {
            "at": self.at,
            "action": self.action,
        }
        if self.from_status:
            out["from_status"] = self.from_status
        if self.to_status:
            out["to_status"] = self.to_status
        if self.note:
            out["note"] = self.note
        if self.metadata:
            out["metadata"] = dict(self.metadata)
        return out


@dataclass
class InboxItem:
    """One item tracked in ``inbox.yaml``."""

    id: str
    title: str
    type: str = "note"
    source: str = ""
    created_at: str = ""
    captured_by: str = "human"
    raw_text: str = ""
    tags: list[str] = field(default_factory=list)
    visibility: str = "private"
    status: str = "inbox"
    metadata: dict[str, object] = field(default_factory=dict)
    history: list[InboxHistoryEvent] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "InboxItem":
        """Build an inbox item from a YAML-loaded mapping."""
        if not isinstance(data, dict):
            return cls(id="", title="")
        raw_history = data.get("history") or []
        history: list[InboxHistoryEvent] = []
        if isinstance(raw_history, list):
            for item in raw_history:
                if isinstance(item, dict):
                    history.append(InboxHistoryEvent.from_dict(item))
        metadata = _clean_metadata(data.get("metadata"))
        return cls(
            id=_clean_text(data.get("id")),
            type=_clean_text(data.get("type")) or "note",
            title=_clean_text(data.get("title")),
            source=_clean_text(data.get("source") or metadata.get("source")),
            created_at=_clean_text(data.get("created_at")),
            captured_by=_clean_text(data.get("captured_by")) or "human",
            raw_text=_clean_text(data.get("raw_text")),
            tags=_clean_tags(data.get("tags") or data.get("tag")),
            visibility=_clean_text(data.get("visibility")) or "private",
            status=_clean_text(data.get("status")) or "inbox",
            metadata=metadata,
            history=history,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize an inbox item for YAML output."""
        out: dict[str, object] = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
        }
        if self.source:
            out["source"] = self.source
        if self.created_at:
            out["created_at"] = self.created_at
        if self.captured_by and self.captured_by != "human":
            out["captured_by"] = self.captured_by
        if self.raw_text:
            out["raw_text"] = self.raw_text
        if self.tags:
            out["tags"] = list(self.tags)
        if self.visibility:
            out["visibility"] = self.visibility
        if self.status:
            out["status"] = self.status
        if self.metadata:
            out["metadata"] = dict(self.metadata)
        if self.history:
            out["history"] = [event.to_dict() for event in self.history]
        return out


@dataclass
class Inbox:
    """Profile-level inbox document."""

    profile: str = ""
    updated: str = ""
    items: list[InboxItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Inbox":
        """Build an inbox from a YAML-loaded mapping."""
        if not isinstance(data, dict):
            return cls()
        raw_items = data.get("items") or []
        items: list[InboxItem] = []
        if isinstance(raw_items, list):
            for item in raw_items:
                if isinstance(item, dict):
                    items.append(InboxItem.from_dict(item))
        return cls(
            profile=_clean_text(data.get("profile")),
            updated=_clean_text(data.get("updated")),
            items=items,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the document for YAML output."""
        return {
            "profile": self.profile,
            "updated": self.updated,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass
class InboxSummary:
    """Aggregate status and tag counts for one inbox."""

    profile: str = ""
    total_items: int = 0
    status_counts: dict[str, int] = field(default_factory=dict)
    tag_counts: dict[str, int] = field(default_factory=dict)
    active_titles: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize the summary for rendering or tests."""
        return {
            "profile": self.profile,
            "total_items": self.total_items,
            "status_counts": dict(self.status_counts),
            "tag_counts": dict(self.tag_counts),
            "active_titles": list(self.active_titles),
        }


def load_inbox(name_or_dir: str | Path) -> Inbox:
    """Load ``inbox.yaml`` into a typed document."""
    path = _profile_file_path(name_or_dir, INBOX_FILENAME)
    raw = _load_yaml_dict(path)
    if raw is None:
        return Inbox(profile=_profile_name(name_or_dir))
    inbox = Inbox.from_dict(raw)
    if not inbox.profile:
        inbox.profile = path.parent.name
    return inbox


def load_inbox_raw(name_or_dir: str | Path) -> dict | None:
    """Load ``inbox.yaml`` as a raw mapping."""
    path = _profile_file_path(name_or_dir, INBOX_FILENAME)
    return _load_yaml_dict(path)


def _find_inbox_item(inbox: Inbox, item_id: str) -> InboxItem:
    """Return one inbox item by id or raise ``KeyError``."""
    clean_id = _clean_text(item_id)
    for item in inbox.items:
        if item.id == clean_id:
            return item
    raise KeyError(f"Unknown inbox item: {clean_id}")


def _append_history(
    item: InboxItem,
    *,
    action: str,
    from_status: str,
    to_status: str,
    note: str,
    metadata: dict[str, object] | None,
    at: str | None,
) -> None:
    """Append a normalized history event to an item."""
    item.history.append(
        InboxHistoryEvent(
            at=_event_date(at),
            action=action,
            from_status=from_status,
            to_status=to_status,
            note=_clean_text(note),
            metadata=dict(metadata or {}),
        )
    )


def add_inbox_item(
    inbox: Inbox,
    title: str,
    *,
    item_id: str = "",
    type: str = "note",
    source: str = "",
    created_at: str = "",
    captured_by: str = "human",
    raw_text: str = "",
    visibility: str = "private",
    status: str = "inbox",
    tags: object = None,
    metadata: dict[str, object] | None = None,
    note: str = "",
    at: str | None = None,
) -> InboxItem:
    """Add one item to the inbox and record its initial history."""
    clean_title = _clean_text(title)
    if not clean_title:
        raise ValueError("Inbox item title cannot be blank.")
    clean_id = _clean_text(item_id) or _next_item_id(inbox.items)
    if any(existing.id == clean_id for existing in inbox.items):
        raise ValueError(f"Duplicate inbox item id: {clean_id}")
    clean_status = _clean_text(status) or "inbox"
    if clean_status not in INBOX_STATUSES:
        clean_status = "inbox"
    item = InboxItem(
        id=clean_id,
        type=_clean_text(type) or "note",
        title=clean_title,
        source=_clean_text(source),
        created_at=_clean_text(created_at) or _event_date(at),
        captured_by=_clean_text(captured_by) or "human",
        raw_text=_clean_text(raw_text),
        tags=_clean_tags(tags),
        visibility=_clean_text(visibility) or "private",
        status=clean_status,
        metadata=_clean_metadata(metadata),
    )
    _append_history(
        item,
        action="added",
        from_status="",
        to_status=clean_status,
        note=note,
        metadata=item.metadata,
        at=at,
    )
    inbox.items.append(item)
    return item


def _clarify_inbox_item_in_doc(
    inbox: Inbox,
    item_id: str,
    *,
    status: str | None = None,
    tags: object | None = None,
    metadata: dict[str, object] | None = None,
    title: str | None = None,
    note: str = "",
    at: str | None = None,
) -> InboxItem:
    """Update an inbox item with clarified status, title, or metadata."""
    item = _find_inbox_item(inbox, item_id)
    from_status = item.status
    changed = False

    if title is not None:
        clean_title = _clean_text(title)
        if not clean_title:
            raise ValueError("Inbox item title cannot be blank.")
        if clean_title != item.title:
            item.title = clean_title
            changed = True

    if status is not None:
        clean_status = _clean_text(status) or item.status
        if clean_status not in INBOX_STATUSES:
            clean_status = item.status
        if clean_status != item.status:
            item.status = clean_status
            changed = True

    if tags is not None:
        clean_tags = _clean_tags(tags)
        if clean_tags != item.tags:
            item.tags = clean_tags
            changed = True

    metadata_delta = _clean_metadata(metadata)
    if metadata is not None:
        for key, value in metadata_delta.items():
            if item.metadata.get(key) != value:
                item.metadata[key] = value
                changed = True

    clean_note = _clean_text(note)
    if not changed and not clean_note:
        return item

    _append_history(
        item,
        action="clarified",
        from_status=from_status,
        to_status=item.status,
        note=clean_note,
        metadata=metadata_delta,
        at=at,
    )
    return item


def archive_inbox_item(
    inbox: Inbox,
    item_id: str,
    *,
    note: str = "",
    metadata: dict[str, object] | None = None,
    at: str | None = None,
) -> InboxItem:
    """Mark an inbox item archived and keep an explicit history event."""
    item = _find_inbox_item(inbox, item_id)
    from_status = item.status
    metadata_delta = _clean_metadata(metadata)
    for key, value in metadata_delta.items():
        item.metadata[key] = value
    item.status = "archived"
    _append_history(
        item,
        action="archived",
        from_status=from_status,
        to_status=item.status,
        note=note,
        metadata=metadata_delta,
        at=at,
    )
    return item


def discard_inbox_item(
    inbox: Inbox,
    item_id: str,
    *,
    note: str = "",
    metadata: dict[str, object] | None = None,
    at: str | None = None,
) -> InboxItem:
    """Mark an inbox item discarded and keep an explicit history event."""
    item = _find_inbox_item(inbox, item_id)
    from_status = item.status
    metadata_delta = _clean_metadata(metadata)
    for key, value in metadata_delta.items():
        item.metadata[key] = value
    item.status = "discarded"
    _append_history(
        item,
        action="discarded",
        from_status=from_status,
        to_status=item.status,
        note=note,
        metadata=metadata_delta,
        at=at,
    )
    return item


def clarify_inbox_item(
    inbox_or_profile: Inbox | str | Path,
    item_id: str,
    action: str | None = None,
    payload: dict[str, object] | None = None,
    **kwargs: object,
) -> InboxItem | dict[str, object]:
    """Clarify an item in memory or dispatch a profile-scoped action."""
    if isinstance(inbox_or_profile, Inbox):
        return _clarify_inbox_item_in_doc(
            inbox_or_profile,
            item_id,
            status=kwargs.get("status") if "status" in kwargs else None,
            tags=kwargs.get("tags") if "tags" in kwargs else None,
            metadata=(
                kwargs.get("metadata")
                if isinstance(kwargs.get("metadata"), dict)
                else None
            ),
            title=kwargs.get("title") if "title" in kwargs else None,
            note=_clean_text(kwargs.get("note")),
            at=kwargs.get("at") if isinstance(kwargs.get("at"), str) else None,
        )

    target_action = _clean_text(action)
    if target_action not in CLARIFY_ACTIONS:
        raise ValueError(f"Unsupported clarify action: {target_action}")
    data = dict(payload or {})
    inbox = load_inbox(inbox_or_profile) or Inbox(
        profile=_profile_name(inbox_or_profile)
    )
    item = _find_inbox_item(inbox, item_id)
    result: dict[str, object] = {
        "action": target_action,
        "item_id": item.id,
        "status": item.status,
    }

    if target_action == "discard":
        item = discard_inbox_item(
            inbox,
            item_id,
            note=_clean_text(data.get("note")),
            metadata={"clarify_action": target_action},
        )
        save_inbox(inbox_or_profile, inbox)
        result["status"] = item.status
        return result

    if target_action == "archive":
        item = archive_inbox_item(
            inbox,
            item_id,
            note=_clean_text(data.get("note")),
            metadata={"clarify_action": target_action},
        )
        save_inbox(inbox_or_profile, inbox)
        result["status"] = item.status
        return result

    if target_action == "to_kanban_queue":
        from nblane.core.io import KANBAN_QUEUE, parse_kanban, save_kanban
        from nblane.core.kanban_io import ensure_kanban_task_ids
        from nblane.core.models import KanbanTask

        profile = _profile_name(inbox_or_profile)
        sections = parse_kanban(profile)
        sections.setdefault(KANBAN_QUEUE, []).append(
            KanbanTask(
                title=_clean_text(data.get("title")) or item.title,
                tags=_clean_tags(data.get("tags") or item.tags),
                context=item.raw_text or item.source,
            )
        )
        ensured = ensure_kanban_task_ids(sections, profile)
        task_id = ensured[KANBAN_QUEUE][-1].id
        save_kanban(profile, ensured)
        result["target_id"] = task_id

    elif target_action == "to_learning_resource":
        from nblane.core.learning_log import add_learning_resource

        resource = add_learning_resource(
            inbox_or_profile,
            title=_clean_text(data.get("title")) or item.title,
            kind=_clean_text(data.get("kind")) or item.type or "other",
            url=_clean_text(data.get("url")) or item.source,
            tags=data.get("tags") or item.tags,
            summary=_clean_text(data.get("summary")) or item.raw_text,
            visibility=item.visibility,
        )
        result["target_id"] = resource.id

    elif target_action == "to_activity_habit":
        from nblane.core.activity_log import add_habit

        habit = add_habit(
            inbox_or_profile,
            _clean_text(data.get("title")) or item.title,
            kind=_clean_text(data.get("kind")) or "practice",
            cadence=_clean_text(data.get("cadence")) or "daily",
            target=data.get("target"),
            tags=_clean_tags(data.get("tags") or item.tags),
            notes=_clean_text(data.get("notes") or data.get("note")),
        )
        result["target_id"] = habit.id

    elif target_action == "to_evidence_draft":
        result["draft"] = {
            "source": "inbox",
            "item_id": item.id,
            "title": _clean_text(data.get("title")) or item.title,
            "summary": _clean_text(data.get("summary")) or item.raw_text,
            "visibility": item.visibility,
            "draft": True,
        }

    metadata: dict[str, object] = {"clarify_action": target_action}
    if "target_id" in result:
        metadata["target_id"] = result["target_id"]
    item = _clarify_inbox_item_in_doc(
        inbox,
        item_id,
        status="clarified",
        metadata=metadata,
        note=_clean_text(data.get("note")),
    )
    save_inbox(inbox_or_profile, inbox)
    result["status"] = item.status
    return result


def save_inbox(
    name_or_dir: str | Path,
    data: Inbox | dict,
) -> None:
    """Write ``inbox.yaml`` with today's date updated."""
    path = _profile_file_path(name_or_dir, INBOX_FILENAME)
    inbox = data if isinstance(data, Inbox) else Inbox.from_dict(data)
    inbox.profile = inbox.profile or path.parent.name
    inbox.updated = date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# Inbox for {inbox.profile or path.parent.name}\n"
        "# status: inbox | clarified | archived | discarded\n"
        "# Each item keeps capture, triage, and closure history.\n\n"
    )
    body = yaml.dump(
        inbox.to_dict(),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    atomic_write_text(path, header + body)
    git_backup.record_change(
        [path],
        action=f"update {path.parent.name}/inbox.yaml",
    )


def summarize_inbox(inbox_or_name: Inbox | str | Path) -> InboxSummary:
    """Return a compact aggregate summary for one inbox."""
    inbox = (
        load_inbox(inbox_or_name)
        if isinstance(inbox_or_name, (str, Path))
        else inbox_or_name
    )
    if inbox is None:
        return InboxSummary(profile=_profile_name(inbox_or_name))

    status_counts: dict[str, int] = {}
    tag_counts: dict[str, int] = {}
    active_titles: list[str] = []
    for item in inbox.items:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1
        for tag in item.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        if item.status in {"inbox", "captured", "clarified", "active"}:
            active_titles.append(item.title)

    return InboxSummary(
        profile=inbox.profile,
        total_items=len(inbox.items),
        status_counts=dict(sorted(status_counts.items())),
        tag_counts=dict(sorted(tag_counts.items())),
        active_titles=active_titles,
    )


__all__ = [
    "CLARIFY_ACTIONS",
    "INBOX_FILENAME",
    "INBOX_STATUSES",
    "Inbox",
    "InboxHistoryEvent",
    "InboxItem",
    "InboxSummary",
    "add_inbox_item",
    "archive_inbox_item",
    "clarify_inbox_item",
    "discard_inbox_item",
    "load_inbox",
    "load_inbox_raw",
    "save_inbox",
    "summarize_inbox",
]
