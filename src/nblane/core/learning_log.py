"""Typed YAML helpers and summaries for profile learning logs."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from nblane.core import git_backup
from nblane.core.paths import PROFILES_DIR
from nblane.core.yaml_io import _load_yaml_dict

LEARNING_LOG_FILENAME = "learning-log.yaml"
RESOURCE_KINDS = (
    "paper",
    "article",
    "blog",
    "interview",
    "book",
    "video",
    "repo",
    "course",
    "other",
)
LEARNING_STATUSES = (
    "unread",
    "reading",
    "processed",
    "archived",
)
LEGACY_STATUS_ALIASES = {
    "captured": "unread",
    "queued": "unread",
    "active": "reading",
    "paused": "reading",
    "completed": "processed",
}


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


def _clean_text(value: object) -> str:
    """Return a stripped string, tolerating ``None``."""
    return str(value or "").strip()


def _clean_text_list(value: object) -> list[str]:
    """Normalize a YAML list or scalar into unique non-empty strings."""
    if value is None:
        return []
    if isinstance(value, str):
        items: list[object] = value.replace("\n", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        items = []
        for item in value:
            if isinstance(item, str):
                items.extend(item.replace("\n", ",").split(","))
            else:
                items.append(item)
    else:
        items = [value]

    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _clean_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned


def _coerce_date_text(value: object) -> str:
    """Normalize date-like values to ISO date text when possible."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = _clean_text(value)
    if not text:
        return ""
    candidate = text.replace("/", "-")
    if "T" in candidate:
        candidate = candidate.split("T", 1)[0]
    if " " in candidate:
        candidate = candidate.split(" ", 1)[0]
    if len(candidate) >= 10:
        candidate = candidate[:10]
    try:
        return date.fromisoformat(candidate).isoformat()
    except ValueError:
        return text


def _parse_date(value: object) -> date | None:
    """Parse an ISO-ish date string when possible."""
    text = _coerce_date_text(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _normalize_kind(value: object) -> str:
    """Return a supported resource kind, preserving unknowns as ``other``."""
    kind = _clean_text(value).casefold()
    return kind if kind in RESOURCE_KINDS else "other"


def _normalize_status(value: object) -> str:
    """Return a supported status, accepting legacy aliases."""
    status = _clean_text(value).casefold()
    if status in LEARNING_STATUSES:
        return status
    return LEGACY_STATUS_ALIASES.get(status, "unread")


def _normalize_takeaways(value: object) -> list[dict[str, str]]:
    """Normalize takeaway rows to short dictionaries."""
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        if isinstance(item, dict):
            text = _clean_text(item.get("text") or item.get("summary"))
            kind = _clean_text(item.get("kind")) or "note"
        else:
            text = _clean_text(item)
            kind = "note"
        if not text:
            continue
        key = (text, kind)
        if key in seen:
            continue
        seen.add(key)
        out.append({"text": text, "kind": kind})
    return out


def _normalize_action_list(value: object) -> list[dict[str, str]]:
    """Normalize next-action rows to dictionaries."""
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        if isinstance(item, dict):
            title = _clean_text(item.get("title") or item.get("text"))
            target = _clean_text(item.get("target")) or "kanban_queue"
        else:
            title = _clean_text(item)
            target = "kanban_queue"
        if not title or title in seen:
            continue
        seen.add(title)
        out.append({"title": title, "target": target})
    return out


@dataclass(init=False)
class LearningResource:
    """One resource row inside ``learning-log.yaml``."""

    id: str
    kind: str
    title: str
    url: str
    authors: list[str]
    source: str
    added_at: str
    status: str
    tags: list[str]
    skill_refs: list[str]
    project_refs: list[str]
    related_kanban: list[str]
    related_evidence: list[str]
    visibility: str
    summary: str
    takeaways: list[dict[str, str]]
    next_actions: list[dict[str, str]]
    warnings: list[str]

    def __init__(
        self,
        title: str = "",
        *,
        id: str = "",
        kind: str = "",
        resource_kind: str = "",
        url: str = "",
        authors: object = None,
        source: str = "",
        added_at: str = "",
        status: str = "",
        tags: object = None,
        skill_refs: object = None,
        project_refs: object = None,
        related_kanban: object = None,
        related_evidence: object = None,
        visibility: str = "private",
        summary: str = "",
        takeaways: object = None,
        next_actions: object = None,
        notes: str = "",
        warnings: object = None,
    ) -> None:
        """Accept both the new resource shape and older entry kwargs."""
        raw_kind = kind or resource_kind or "article"
        raw_status = status or "unread"
        self.id = _clean_text(id)
        self.kind = _normalize_kind(raw_kind)
        self.title = _clean_text(title)
        self.url = _clean_text(url)
        self.authors = _clean_text_list(authors)
        self.source = _clean_text(source)
        self.added_at = _coerce_date_text(added_at)
        self.status = _normalize_status(raw_status)
        self.tags = _clean_text_list(tags)
        self.skill_refs = _clean_text_list(skill_refs)
        self.project_refs = _clean_text_list(project_refs)
        self.related_kanban = _clean_text_list(related_kanban)
        self.related_evidence = _clean_text_list(related_evidence)
        self.visibility = _clean_text(visibility) or "private"
        self.summary = _clean_text(summary or notes)
        self.takeaways = _normalize_takeaways(takeaways)
        self.next_actions = _normalize_action_list(next_actions)
        self.warnings = _clean_text_list(warnings)
        if raw_kind and _clean_text(raw_kind).casefold() not in RESOURCE_KINDS:
            self.warnings.append(f"Unknown resource kind: {raw_kind}")
        if (
            raw_status
            and _clean_text(raw_status).casefold() not in LEARNING_STATUSES
            and _clean_text(raw_status).casefold() not in LEGACY_STATUS_ALIASES
        ):
            self.warnings.append(f"Unknown learning status: {raw_status}")

    @property
    def resource_kind(self) -> str:
        """Compatibility alias for older callers."""
        return self.kind

    @resource_kind.setter
    def resource_kind(self, value: str) -> None:
        self.kind = _normalize_kind(value)

    @property
    def notes(self) -> str:
        """Compatibility alias for older callers."""
        return self.summary

    @notes.setter
    def notes(self, value: str) -> None:
        self.summary = _clean_text(value)

    @classmethod
    def from_dict(cls, data: dict) -> "LearningResource":
        """Build an entry from a YAML-loaded mapping."""
        if not isinstance(data, dict):
            return cls(title="")
        return cls(
            id=_clean_text(data.get("id")),
            title=_clean_text(data.get("title")),
            kind=_clean_text(data.get("kind") or data.get("resource_kind")),
            url=_clean_text(data.get("url")),
            authors=data.get("authors") or [],
            source=_clean_text(data.get("source")),
            added_at=data.get("added_at") or data.get("created_at"),
            status=_clean_text(data.get("status")),
            tags=data.get("tags") or [],
            skill_refs=data.get("skill_refs") or [],
            project_refs=data.get("project_refs") or [],
            related_kanban=data.get("related_kanban") or [],
            related_evidence=data.get("related_evidence") or [],
            visibility=_clean_text(data.get("visibility")) or "private",
            summary=_clean_text(data.get("summary") or data.get("notes")),
            takeaways=data.get("takeaways") or [],
            next_actions=data.get("next_actions") or [],
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize an entry for YAML output."""
        out: dict[str, object] = {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
        }
        if self.url:
            out["url"] = self.url
        if self.authors:
            out["authors"] = list(self.authors)
        if self.source:
            out["source"] = self.source
        if self.added_at:
            out["added_at"] = self.added_at
        if self.status:
            out["status"] = self.status
        if self.tags:
            out["tags"] = list(self.tags)
        if self.skill_refs:
            out["skill_refs"] = list(self.skill_refs)
        if self.project_refs:
            out["project_refs"] = list(self.project_refs)
        if self.related_kanban:
            out["related_kanban"] = list(self.related_kanban)
        if self.related_evidence:
            out["related_evidence"] = list(self.related_evidence)
        if self.visibility and self.visibility != "private":
            out["visibility"] = self.visibility
        if self.summary:
            out["summary"] = self.summary
        if self.takeaways:
            out["takeaways"] = [dict(item) for item in self.takeaways]
        if self.next_actions:
            out["next_actions"] = [dict(item) for item in self.next_actions]
        return out


LearningLogEntry = LearningResource


@dataclass(init=False)
class LearningLog:
    """Profile-level learning log document."""

    profile: str = ""
    updated: str = ""
    resources: list[LearningResource] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list, repr=False)

    def __init__(
        self,
        profile: str = "",
        updated: str = "",
        resources: list[LearningResource] | None = None,
        entries: list[LearningResource] | None = None,
        warnings: list[str] | None = None,
    ) -> None:
        """Accept both ``resources`` and the older ``entries`` keyword."""
        self.profile = _clean_text(profile)
        self.updated = _coerce_date_text(updated)
        self.resources = list(resources if resources is not None else entries or [])
        self.warnings = list(warnings or [])

    @property
    def entries(self) -> list[LearningResource]:
        """Compatibility alias for older callers."""
        return self.resources

    @entries.setter
    def entries(self, value: list[LearningResource]) -> None:
        self.resources = value

    @classmethod
    def from_dict(cls, data: dict) -> "LearningLog":
        """Build a log from a YAML-loaded mapping."""
        if not isinstance(data, dict):
            return cls()
        raw_entries = data.get("resources")
        if raw_entries is None:
            raw_entries = data.get("entries") or []
        resources: list[LearningResource] = []
        warnings: list[str] = []
        if isinstance(raw_entries, list):
            for item in raw_entries:
                if isinstance(item, dict):
                    resource = LearningResource.from_dict(item)
                    resources.append(resource)
                    warnings.extend(resource.warnings)
        return cls(
            profile=_clean_text(data.get("profile")),
            updated=_coerce_date_text(data.get("updated")),
            resources=resources,
            warnings=warnings,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the document for YAML output."""
        return {
            "profile": self.profile,
            "updated": self.updated,
            "resources": [
                resource.to_dict() for resource in self.resources
            ],
        }


@dataclass
class LearningLogSummary:
    """Computed counts and tag breakdowns for one learning log."""

    profile: str = ""
    total_entries: int = 0
    status_counts: dict[str, int] = field(default_factory=dict)
    resource_kind_counts: dict[str, int] = field(default_factory=dict)
    tag_counts: dict[str, int] = field(default_factory=dict)
    active_titles: list[str] = field(default_factory=list)
    completed_titles: list[str] = field(default_factory=list)
    reading_titles: list[str] = field(default_factory=list)
    processed_titles: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize the summary for rendering or tests."""
        return {
            "profile": self.profile,
            "total_entries": self.total_entries,
            "status_counts": dict(self.status_counts),
            "resource_kind_counts": dict(self.resource_kind_counts),
            "tag_counts": dict(self.tag_counts),
            "active_titles": list(self.active_titles),
            "completed_titles": list(self.completed_titles),
            "reading_titles": list(self.reading_titles),
            "processed_titles": list(self.processed_titles),
            "warnings": list(self.warnings),
        }


def _empty_learning_log(name_or_dir: str | Path) -> LearningLog:
    """Return an empty typed document for a profile path or name."""
    if isinstance(name_or_dir, Path):
        profile = name_or_dir.stem if name_or_dir.suffix else name_or_dir.name
        return LearningLog(profile=profile)
    return LearningLog(profile=_clean_text(name_or_dir))


def _next_learning_resource_id(log: LearningLog) -> str:
    """Return the next stable resource id."""
    today = date.today().strftime("%Y%m%d")
    max_index = 0
    for entry in log.resources:
        suffix = entry.id.rsplit("_", 1)[-1]
        try:
            max_index = max(max_index, int(suffix))
        except ValueError:
            continue
    return f"learn_{today}_{max_index + 1:03d}"


def load_learning_log(name_or_dir: str | Path) -> LearningLog:
    """Load ``learning-log.yaml`` into a typed document."""
    path = _profile_file_path(name_or_dir, LEARNING_LOG_FILENAME)
    raw = _load_yaml_dict(path)
    if raw is None:
        return _empty_learning_log(name_or_dir)
    log = LearningLog.from_dict(raw)
    if not log.profile:
        log.profile = path.parent.name
    return log


def load_learning_log_raw(name_or_dir: str | Path) -> dict | None:
    """Load ``learning-log.yaml`` as a raw mapping."""
    path = _profile_file_path(name_or_dir, LEARNING_LOG_FILENAME)
    return _load_yaml_dict(path)


def save_learning_log(
    name_or_dir: str | Path,
    data: LearningLog | dict,
) -> None:
    """Write ``learning-log.yaml`` with today's date updated."""
    path = _profile_file_path(name_or_dir, LEARNING_LOG_FILENAME)
    log = data if isinstance(data, LearningLog) else LearningLog.from_dict(data)
    log.profile = log.profile or path.parent.name
    log.updated = date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# Learning log for {log.profile or path.parent.name}\n"
        "# kind: paper | article | blog | interview | book | video | repo | course | other\n"
        "# status: unread | reading | processed | archived\n\n"
    )
    body = yaml.dump(
        log.to_dict(),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    path.write_text(header + body, encoding="utf-8")
    git_backup.record_change(
        [path],
        action=f"update {path.parent.name}/learning-log.yaml",
    )


def add_learning_resource(
    name_or_dir: str | Path,
    **kwargs: Any,
) -> LearningResource:
    """Append one resource to the learning log and persist the file."""
    log = load_learning_log(name_or_dir)
    resource = LearningResource(**kwargs)
    if not resource.title:
        raise ValueError("Learning resource title cannot be blank.")
    if not resource.id:
        resource.id = _next_learning_resource_id(log)
    if not resource.added_at:
        resource.added_at = date.today().isoformat()
    if any(existing.id == resource.id for existing in log.resources):
        raise ValueError(f"Duplicate learning resource id: {resource.id}")
    log.resources.append(resource)
    save_learning_log(name_or_dir, log)
    return resource


def append_learning_entry(
    name_or_dir: str | Path,
    entry: LearningResource | dict[str, object],
) -> LearningResource:
    """Compatibility wrapper for appending one learning resource."""
    if isinstance(entry, LearningResource):
        kwargs = entry.to_dict()
        kwargs["summary"] = entry.summary
    else:
        kwargs = dict(entry)
    return add_learning_resource(name_or_dir, **kwargs)


def _find_resource(log: LearningLog, resource_id: str) -> LearningResource:
    """Return one learning resource by id or raise ``KeyError``."""
    clean_id = _clean_text(resource_id)
    for resource in log.resources:
        if resource.id == clean_id:
            return resource
    raise KeyError(f"Unknown learning resource: {clean_id}")


def update_resource(
    name_or_dir: str | Path,
    resource_id: str,
    **updates: Any,
) -> LearningResource:
    """Update one resource in place and persist the learning log."""
    log = load_learning_log(name_or_dir)
    resource = _find_resource(log, resource_id)
    updated = LearningResource.from_dict(
        {
            **resource.to_dict(),
            **updates,
            "id": resource.id,
            "title": updates.get("title", resource.title),
        }
    )
    index = log.resources.index(resource)
    log.resources[index] = updated
    save_learning_log(name_or_dir, log)
    return updated


def archive_resource(
    name_or_dir: str | Path,
    resource_id: str,
) -> LearningResource:
    """Mark a resource archived and persist the learning log."""
    return update_resource(name_or_dir, resource_id, status="archived")


def summarize_learning_log(
    log_or_name: LearningLog | str | Path | None,
    *,
    start: str | date | None = None,
    end: str | date | None = None,
) -> LearningLogSummary:
    """Return aggregate counts and tag breakdowns for one log."""
    if log_or_name is None:
        return LearningLogSummary()
    log = (
        load_learning_log(log_or_name)
        if isinstance(log_or_name, (str, Path))
        else log_or_name
    )
    start_date = _parse_date(start) if start is not None else None
    end_date = _parse_date(end) if end is not None else None

    status_counts: Counter[str] = Counter()
    resource_kind_counts: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()
    active_titles: list[str] = []
    completed_titles: list[str] = []
    reading_titles: list[str] = []
    processed_titles: list[str] = []
    total = 0
    for entry in log.resources:
        when = _parse_date(entry.added_at)
        if start_date is not None and when is not None and when < start_date:
            continue
        if end_date is not None and when is not None and when > end_date:
            continue
        total += 1
        if entry.status:
            status_counts[entry.status] += 1
        if entry.kind:
            resource_kind_counts[entry.kind] += 1
        for tag in entry.tags:
            tag_counts[tag] += 1
        if entry.status == "reading" and entry.title:
            reading_titles.append(entry.title)
            active_titles.append(entry.title)
        if entry.status == "processed" and entry.title:
            processed_titles.append(entry.title)
            completed_titles.append(entry.title)
    return LearningLogSummary(
        profile=log.profile,
        total_entries=total,
        status_counts=dict(sorted(status_counts.items())),
        resource_kind_counts=dict(sorted(resource_kind_counts.items())),
        tag_counts=dict(sorted(tag_counts.items())),
        active_titles=active_titles,
        completed_titles=completed_titles,
        reading_titles=reading_titles,
        processed_titles=processed_titles,
        warnings=list(log.warnings),
    )


def learning_summary(
    log_or_name: LearningLog | str | Path,
    *,
    start: str | date | None = None,
    end: str | date | None = None,
) -> dict[str, object]:
    """Return a summary mapping for API callers."""
    return summarize_learning_log(
        log_or_name,
        start=start,
        end=end,
    ).to_dict()


def create_queue_task_from_learning(
    profile: str,
    resource_id: str,
    *,
    title: str = "",
    action_index: int = 0,
) -> str:
    """Create a Kanban Queue task from a learning resource next action."""
    from nblane.core.io import KANBAN_QUEUE, parse_kanban, save_kanban
    from nblane.core.kanban_io import ensure_kanban_task_ids
    from nblane.core.models import KanbanTask

    log = load_learning_log(profile)
    resource = _find_resource(log, resource_id)
    action_title = _clean_text(title)
    if not action_title and 0 <= action_index < len(resource.next_actions):
        action_title = resource.next_actions[action_index].get("title", "")
    if not action_title:
        action_title = f"Process learning: {resource.title}"

    sections = parse_kanban(profile)
    tags = _clean_text_list([*resource.tags, "flow/learning"])
    task = KanbanTask(
        title=action_title,
        tags=tags,
        context=f"From learning resource: {resource.title}",
        why=resource.summary,
    )
    sections.setdefault(KANBAN_QUEUE, []).append(task)
    ensured = ensure_kanban_task_ids(sections, profile)
    task_id = ensured[KANBAN_QUEUE][-1].id
    save_kanban(profile, ensured)
    if task_id and task_id not in resource.related_kanban:
        resource.related_kanban.append(task_id)
        save_learning_log(profile, log)
    return task_id


def learning_evidence_candidates(
    log_or_name: LearningLog | str | Path,
    *,
    start: str | date | None = None,
    end: str | date | None = None,
) -> list[dict[str, object]]:
    """Return draft evidence candidates without writing evidence-pool.yaml."""
    log = (
        load_learning_log(log_or_name)
        if isinstance(log_or_name, (str, Path))
        else log_or_name
    )
    start_date = _parse_date(start) if start is not None else None
    end_date = _parse_date(end) if end is not None else None
    out: list[dict[str, object]] = []
    for resource in log.resources:
        if resource.status != "processed":
            continue
        when = _parse_date(resource.added_at)
        if start_date is not None and when is not None and when < start_date:
            continue
        if end_date is not None and when is not None and when > end_date:
            continue
        if not resource.summary and not resource.takeaways:
            continue
        out.append(
            {
                "source": "learning",
                "resource_id": resource.id,
                "title": resource.title,
                "kind": resource.kind,
                "visibility": resource.visibility,
                "summary": resource.summary,
                "skill_refs": list(resource.skill_refs),
                "draft": True,
            }
        )
    return out


__all__ = [
    "LEARNING_LOG_FILENAME",
    "LEARNING_STATUSES",
    "RESOURCE_KINDS",
    "LearningLog",
    "LearningLogEntry",
    "LearningLogSummary",
    "LearningResource",
    "add_learning_resource",
    "append_learning_entry",
    "archive_resource",
    "create_queue_task_from_learning",
    "learning_evidence_candidates",
    "learning_summary",
    "load_learning_log",
    "load_learning_log_raw",
    "save_learning_log",
    "summarize_learning_log",
    "update_resource",
]
