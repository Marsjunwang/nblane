"""Research source inbox facts for nblane profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import yaml

from nblane.core import git_backup
from nblane.core.file_write import atomic_write_text
from nblane.core.paths import PROFILES_DIR
from nblane.core.yaml_io import _load_yaml_dict

RESEARCH_DIRNAME = "research"
RESEARCH_SOURCES_FILENAME = "sources.yaml"
SOURCE_KINDS = (
    "web",
    "paper",
    "repo",
    "dataset",
    "pdf",
    "book",
    "note",
    "other",
)
SOURCE_STATUSES = (
    "inbox",
    "reading",
    "summarized",
    "candidate_ready",
    "archived",
    "discarded",
)
SOURCE_VISIBILITIES = ("private", "public")
SOURCE_ORIGINS = ("manual", "home_capture", "connector", "resume_import")


def profile_dir(name: str) -> Path:
    """Return path to ``profiles/{name}``."""
    return PROFILES_DIR / name


def _profile_file_path(name_or_dir: str | Path) -> Path:
    """Resolve a profile-scoped research sources path."""
    if isinstance(name_or_dir, Path):
        if name_or_dir.suffix in (".yaml", ".yml"):
            return name_or_dir
        return name_or_dir / RESEARCH_DIRNAME / RESEARCH_SOURCES_FILENAME
    raw = name_or_dir.strip()
    path = Path(raw)
    if (
        path.suffix in (".yaml", ".yml")
        or "/" in raw
        or raw.startswith(".")
        or path.exists()
    ):
        return path if path.suffix else path / RESEARCH_DIRNAME / RESEARCH_SOURCES_FILENAME
    return profile_dir(raw) / RESEARCH_DIRNAME / RESEARCH_SOURCES_FILENAME


def _profile_name(name_or_dir: str | Path) -> str:
    if isinstance(name_or_dir, Path):
        if name_or_dir.suffix:
            try:
                return name_or_dir.parent.parent.name
            except IndexError:
                return name_or_dir.stem
        return name_or_dir.name
    return Path(name_or_dir).stem if "/" in name_or_dir else str(name_or_dir)


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _clean_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.replace("\n", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        raw_items = []
        for item in value:
            if isinstance(item, str):
                raw_items.extend(item.replace("\n", ",").split(","))
            else:
                raw_items.append(_clean_text(item))
    else:
        raw_items = [_clean_text(value)]
    out: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        clean = _clean_text(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _clean_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, object] = {}
    for key, item in value.items():
        clean = _clean_text(key)
        if clean:
            out[clean] = item
    return out


def _clean_choice(value: object, options: tuple[str, ...], default: str) -> str:
    clean = _clean_text(value)
    return clean if clean in options else default


def _event_time(value: object = None) -> str:
    clean = _clean_text(value)
    if clean:
        return clean
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _next_source_id(sources: list["ResearchSource"]) -> str:
    today = date.today().strftime("%Y%m%d")
    prefix = f"source:research:{today}-"
    max_index = 0
    for source in sources:
        if not source.id.startswith(prefix):
            continue
        try:
            max_index = max(max_index, int(source.id.rsplit("-", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_index + 1:03d}"


def _find_source(inbox: "ResearchSourceInbox", source_id: str) -> "ResearchSource":
    clean_id = _clean_text(source_id)
    for source in inbox.sources:
        if source.id == clean_id:
            return source
    raise KeyError(f"Unknown research source: {clean_id}")


@dataclass
class ResearchSource:
    """One source in the research inbox."""

    id: str
    title: str
    kind: str = "web"
    url: str = ""
    status: str = "inbox"
    captured_at: str = ""
    authors: list[str] = field(default_factory=list)
    published: str = ""
    tags: list[str] = field(default_factory=list)
    goal_refs: list[str] = field(default_factory=list)
    project_refs: list[str] = field(default_factory=list)
    experience_refs: list[str] = field(default_factory=list)
    summary: str = ""
    notes: str = ""
    visibility: str = "private"
    origin: str = "manual"
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchSource":
        """Build a source from YAML."""
        if not isinstance(data, dict):
            return cls(id="", title="")
        return cls(
            id=_clean_text(data.get("id")),
            title=_clean_text(data.get("title")),
            kind=_clean_choice(data.get("kind"), SOURCE_KINDS, "web"),
            url=_clean_text(data.get("url")),
            status=_clean_choice(data.get("status"), SOURCE_STATUSES, "inbox"),
            captured_at=_clean_text(data.get("captured_at")),
            authors=_clean_list(data.get("authors")),
            published=_clean_text(data.get("published")),
            tags=_clean_list(data.get("tags")),
            goal_refs=_clean_list(data.get("goal_refs")),
            project_refs=_clean_list(data.get("project_refs")),
            experience_refs=_clean_list(data.get("experience_refs")),
            summary=_clean_text(data.get("summary")),
            notes=_clean_text(data.get("notes")),
            visibility=_clean_choice(
                data.get("visibility"),
                SOURCE_VISIBILITIES,
                "private",
            ),
            origin=_clean_choice(data.get("origin"), SOURCE_ORIGINS, "manual"),
            metadata=_clean_mapping(data.get("metadata")),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize for YAML output."""
        out: dict[str, object] = {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "status": self.status,
            "visibility": self.visibility,
            "origin": self.origin,
        }
        for key in ("url", "captured_at", "published", "summary", "notes"):
            value = getattr(self, key)
            if value:
                out[key] = value
        for key in (
            "authors",
            "tags",
            "goal_refs",
            "project_refs",
            "experience_refs",
        ):
            values = getattr(self, key)
            if values:
                out[key] = list(values)
        if self.metadata:
            out["metadata"] = dict(self.metadata)
        return out


@dataclass
class ResearchSourceInbox:
    """Profile-level research source inbox document."""

    profile: str = ""
    updated: str = ""
    schema_version: str = "1.0"
    sources: list[ResearchSource] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchSourceInbox":
        """Build a source inbox from YAML."""
        if not isinstance(data, dict):
            return cls()
        raw_sources = data.get("sources") or []
        sources: list[ResearchSource] = []
        if isinstance(raw_sources, list):
            for item in raw_sources:
                if isinstance(item, dict):
                    sources.append(ResearchSource.from_dict(item))
        return cls(
            profile=_clean_text(data.get("profile")),
            updated=_clean_text(data.get("updated")),
            schema_version=_clean_text(data.get("schema_version")) or "1.0",
            sources=sources,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the document for YAML output."""
        return {
            "schema_version": self.schema_version or "1.0",
            "profile": self.profile,
            "updated": self.updated,
            "sources": [source.to_dict() for source in self.sources],
        }

    def by_id(self) -> dict[str, ResearchSource]:
        """Return source id -> source."""
        return {source.id: source for source in self.sources if source.id}


def load_research_sources(name_or_dir: str | Path) -> ResearchSourceInbox:
    """Load ``research/sources.yaml`` into a typed document."""
    path = _profile_file_path(name_or_dir)
    raw = _load_yaml_dict(path)
    if raw is None:
        return ResearchSourceInbox(profile=_profile_name(name_or_dir))
    inbox = ResearchSourceInbox.from_dict(raw)
    if not inbox.profile:
        inbox.profile = path.parent.parent.name
    return inbox


def load_research_sources_raw(name_or_dir: str | Path) -> dict | None:
    """Load ``research/sources.yaml`` as a raw mapping."""
    return _load_yaml_dict(_profile_file_path(name_or_dir))


def add_research_source(
    inbox: ResearchSourceInbox,
    title: str,
    *,
    source_id: str = "",
    kind: str = "web",
    url: str = "",
    status: str = "inbox",
    captured_at: str = "",
    authors: object = None,
    published: str = "",
    tags: object = None,
    goal_refs: object = None,
    project_refs: object = None,
    experience_refs: object = None,
    summary: str = "",
    notes: str = "",
    visibility: str = "private",
    origin: str = "manual",
    metadata: dict[str, object] | None = None,
) -> ResearchSource:
    """Add one source to an in-memory inbox."""
    clean_title = _clean_text(title)
    if not clean_title:
        raise ValueError("Research source title cannot be blank.")
    clean_id = _clean_text(source_id) or _next_source_id(inbox.sources)
    if any(source.id == clean_id for source in inbox.sources):
        raise ValueError(f"Duplicate research source id: {clean_id}")
    source = ResearchSource(
        id=clean_id,
        title=clean_title,
        kind=_clean_choice(kind, SOURCE_KINDS, "web"),
        url=_clean_text(url),
        status=_clean_choice(status, SOURCE_STATUSES, "inbox"),
        captured_at=_event_time(captured_at),
        authors=_clean_list(authors),
        published=_clean_text(published),
        tags=_clean_list(tags),
        goal_refs=_clean_list(goal_refs),
        project_refs=_clean_list(project_refs),
        experience_refs=_clean_list(experience_refs),
        summary=_clean_text(summary),
        notes=_clean_text(notes),
        visibility=_clean_choice(visibility, SOURCE_VISIBILITIES, "private"),
        origin=_clean_choice(origin, SOURCE_ORIGINS, "manual"),
        metadata=_clean_mapping(metadata),
    )
    inbox.sources.append(source)
    return source


def update_research_source(
    inbox: ResearchSourceInbox,
    source_id: str,
    **fields: object,
) -> ResearchSource:
    """Update one source in an in-memory inbox."""
    source = _find_source(inbox, source_id)
    if "title" in fields:
        title = _clean_text(fields["title"])
        if not title:
            raise ValueError("Research source title cannot be blank.")
        source.title = title
    for key, options in (
        ("kind", SOURCE_KINDS),
        ("status", SOURCE_STATUSES),
        ("visibility", SOURCE_VISIBILITIES),
        ("origin", SOURCE_ORIGINS),
    ):
        if key in fields:
            setattr(source, key, _clean_choice(fields[key], options, getattr(source, key)))
    for key in ("url", "captured_at", "published", "summary", "notes"):
        if key in fields:
            setattr(source, key, _clean_text(fields[key]))
    for key in ("authors", "tags", "goal_refs", "project_refs", "experience_refs"):
        if key in fields:
            setattr(source, key, _clean_list(fields[key]))
    if "metadata" in fields:
        source.metadata = _clean_mapping(fields["metadata"])
    return source


def archive_research_source(
    inbox: ResearchSourceInbox,
    source_id: str,
) -> ResearchSource:
    """Mark one source archived."""
    return update_research_source(inbox, source_id, status="archived")


def save_research_sources(
    name_or_dir: str | Path,
    data: ResearchSourceInbox | dict,
) -> None:
    """Write ``research/sources.yaml`` with today's date updated."""
    path = _profile_file_path(name_or_dir)
    inbox = (
        data
        if isinstance(data, ResearchSourceInbox)
        else ResearchSourceInbox.from_dict(data)
    )
    inbox.profile = inbox.profile or path.parent.parent.name
    inbox.updated = date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# Research sources for {inbox.profile or path.parent.parent.name}\n"
        "# Sources are not evidence until reviewed into evidence candidates.\n\n"
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
        action=f"update {path.parent.parent.name}/research/sources.yaml",
    )


__all__ = [
    "RESEARCH_DIRNAME",
    "RESEARCH_SOURCES_FILENAME",
    "SOURCE_KINDS",
    "SOURCE_ORIGINS",
    "SOURCE_STATUSES",
    "SOURCE_VISIBILITIES",
    "ResearchSource",
    "ResearchSourceInbox",
    "add_research_source",
    "archive_research_source",
    "load_research_sources",
    "load_research_sources_raw",
    "save_research_sources",
    "update_research_source",
]
