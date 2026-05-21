"""Research source inbox facts for nblane profiles."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from nblane.core import agent_activity, git_backup
from nblane.core import llm as llm_client  # legacy patch point for tests/callers
from nblane.core.evidence_pool_id import new_evidence_id
from nblane.core.file_write import atomic_write_text
from nblane.core.jsonutil import extract_json_object
from nblane.core.paths import PROFILES_DIR, REPO_ROOT
from nblane.core.profile_io import (
    load_evidence_pool_raw,
    save_evidence_pool,
)
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
READER_STATE_METADATA_KEYS = (
    "last_read_page",
    "last_read_at",
    "last_visible_pages",
    "reader_mode",
    "scale_mode",
    "active_tab",
    "target_lang",
    "focused_annotation_id",
    "focused_chunk_id",
    "active_left_tab",
    "active_translation_anchor",
    "compare_split_ratio",
    "panel_width",
    "side_panel_collapsed",
    "left_rail_collapsed",
    "translation_source_visible",
)


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


def _relative_file(path: str | Path) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        return str(path)


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


def _source_ref_slug(source_id: str) -> str:
    clean = _clean_text(source_id).replace(":", "-")
    clean = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in clean)
    clean = "-".join(part for part in clean.split("-") if part)
    return clean or "source"


def _candidate_id(prefix: str, source_id: str, existing: set[str], index: int) -> str:
    base = f"{prefix}:{_source_ref_slug(source_id)}:{index:03d}"
    candidate = base
    suffix = 2
    while candidate in existing:
        candidate = f"{base}-{suffix}"
        suffix += 1
    existing.add(candidate)
    return candidate


def _claim_type(value: object) -> str:
    clean = _clean_text(value)
    return clean if clean in {"achievement", "skill", "impact", "role", "learning", "project"} else "learning"


def _confidence(value: object) -> str:
    clean = _clean_text(value)
    return clean if clean in {"low", "medium", "high"} else "medium"


def _reading_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            out.append(copy.deepcopy(item))
    return out


@dataclass
class ResearchReading:
    """Source-scoped reading annotations and draft candidates."""

    excerpt: str = ""
    translation: str = ""
    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    claim_candidates: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    synthesis_notes: str = ""
    generated_by: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(cls, data: object) -> "ResearchReading":
        """Build reading annotations from YAML."""
        if not isinstance(data, dict):
            return cls()
        return cls(
            excerpt=_clean_text(data.get("excerpt")),
            translation=_clean_text(data.get("translation")),
            summary=_clean_text(data.get("summary")),
            key_points=_clean_list(data.get("key_points")),
            claim_candidates=_reading_items(data.get("claim_candidates")),
            citations=_reading_items(data.get("citations")),
            synthesis_notes=_clean_text(data.get("synthesis_notes")),
            generated_by=_clean_text(data.get("generated_by")),
            updated_at=_clean_text(data.get("updated_at")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize non-empty reading annotations for YAML output."""
        out: dict[str, Any] = {}
        for key in ("excerpt", "translation", "summary"):
            value = getattr(self, key)
            if value:
                out[key] = value
        if self.key_points:
            out["key_points"] = list(self.key_points)
        if self.claim_candidates:
            out["claim_candidates"] = copy.deepcopy(self.claim_candidates)
        if self.citations:
            out["citations"] = copy.deepcopy(self.citations)
        if self.synthesis_notes:
            out["synthesis_notes"] = self.synthesis_notes
        if self.generated_by:
            out["generated_by"] = self.generated_by
        if self.updated_at:
            out["updated_at"] = self.updated_at
        return out

    @property
    def empty(self) -> bool:
        """Return True when the reading has no user-visible content."""
        return not bool(self.to_dict())


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
    library_node_refs: list[str] = field(default_factory=list)
    summary: str = ""
    notes: str = ""
    visibility: str = "private"
    origin: str = "manual"
    evidence_refs: list[str] = field(default_factory=list)
    reading: ResearchReading = field(default_factory=ResearchReading)
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
            library_node_refs=_clean_list(data.get("library_node_refs")),
            summary=_clean_text(data.get("summary")),
            notes=_clean_text(data.get("notes")),
            visibility=_clean_choice(
                data.get("visibility"),
                SOURCE_VISIBILITIES,
                "private",
            ),
            origin=_clean_choice(data.get("origin"), SOURCE_ORIGINS, "manual"),
            evidence_refs=_clean_list(data.get("evidence_refs")),
            reading=ResearchReading.from_dict(data.get("reading")),
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
            "library_node_refs",
        ):
            values = getattr(self, key)
            if values:
                out[key] = list(values)
        if self.evidence_refs:
            out["evidence_refs"] = list(self.evidence_refs)
        reading = self.reading.to_dict()
        if reading:
            out["reading"] = reading
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


def _metadata_epoch(value: object) -> float | None:
    clean = _clean_text(value)
    if not clean:
        return None
    try:
        return datetime.fromisoformat(clean.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _reader_state_is_newer(
    current_metadata: dict[str, object],
    next_metadata: dict[str, object],
) -> bool:
    """Return True when disk has newer passive Reader state."""
    current_at = _metadata_epoch(current_metadata.get("last_read_at"))
    next_at = _metadata_epoch(next_metadata.get("last_read_at"))
    if current_at is not None:
        if next_at is None or current_at > next_at:
            return True
        return False
    current_text = _clean_text(current_metadata.get("last_read_at"))
    next_text = _clean_text(next_metadata.get("last_read_at"))
    if current_text:
        return not next_text or current_text > next_text
    return any(
        key in current_metadata and key not in next_metadata
        for key in READER_STATE_METADATA_KEYS
    )


def _preserve_newer_reader_state(
    path: Path,
    inbox: ResearchSourceInbox,
) -> None:
    """Merge newer passive Reader metadata from disk into a pending save."""
    if not path.exists():
        return
    raw = _load_yaml_dict(path)
    if raw is None:
        return
    current_by_id = ResearchSourceInbox.from_dict(raw).by_id()
    for source in inbox.sources:
        current = current_by_id.get(source.id)
        if current is None:
            continue
        current_metadata = dict(current.metadata or {})
        if not any(key in current_metadata for key in READER_STATE_METADATA_KEYS):
            continue
        next_metadata = dict(source.metadata or {})
        if not _reader_state_is_newer(current_metadata, next_metadata):
            continue
        merged = dict(next_metadata)
        for key in READER_STATE_METADATA_KEYS:
            if key in current_metadata:
                merged[key] = copy.deepcopy(current_metadata[key])
        source.metadata = merged


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
    library_node_refs: object = None,
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
        library_node_refs=_clean_list(library_node_refs),
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
    for key in (
        "authors",
        "tags",
        "goal_refs",
        "project_refs",
        "experience_refs",
        "library_node_refs",
    ):
        if key in fields:
            setattr(source, key, _clean_list(fields[key]))
    if "evidence_refs" in fields:
        source.evidence_refs = _clean_list(fields["evidence_refs"])
    if "reading" in fields:
        reading = fields["reading"]
        if isinstance(reading, ResearchReading):
            source.reading = reading
        else:
            source.reading = ResearchReading.from_dict(reading)
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
    _preserve_newer_reader_state(path, inbox)
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


def _source_metadata(source: ResearchSource) -> dict[str, Any]:
    return {
        "id": source.id,
        "kind": source.kind,
        "title": source.title,
        "url": source.url,
        "authors": list(source.authors),
        "published": source.published,
        "tags": list(source.tags),
        "summary": source.summary,
        "notes": source.notes,
    }


def _fallback_reading(source: ResearchSource, excerpt: str, mode: str) -> ResearchReading:
    clean_excerpt = _clean_text(excerpt)
    summary_source = clean_excerpt or source.summary or source.notes or source.title
    words = summary_source.split()
    summary = " ".join(words[:80]).strip() or source.title
    if clean_excerpt and len(clean_excerpt) > len(summary):
        summary = summary.rstrip(".。") + "."
    key_points = []
    for raw in (source.summary, source.notes, clean_excerpt):
        text = _clean_text(raw)
        if text and text not in key_points:
            key_points.append(text[:220])
        if len(key_points) >= 3:
            break
    existing_claim_ids: set[str] = set()
    existing_citation_ids: set[str] = set()
    claim = {
        "id": _candidate_id("rclaim", source.id, existing_claim_ids, 1),
        "text": summary,
        "type": "learning",
        "source_refs": [source.id],
        "citation_refs": [],
        "confidence": "medium",
        "warnings": [
            "Deterministic fallback; review this source claim before turning it into evidence or public output."
        ],
    }
    citation = {
        "id": _candidate_id("cite", source.id, existing_citation_ids, 1),
        "label": source.title or source.id,
        "title": source.title,
        "url": source.url,
        "authors": list(source.authors),
        "published": source.published,
        "locator": "",
        "quote": clean_excerpt[:500],
        "note": "Created from source metadata and pasted excerpt.",
    }
    return ResearchReading(
        excerpt=clean_excerpt,
        translation=clean_excerpt if mode == "translate" else "",
        summary=summary,
        key_points=key_points,
        claim_candidates=[claim] if summary else [],
        citations=[citation],
        synthesis_notes=(
            "Connect this source to a reviewed evidence row before using it in public output."
        ),
        generated_by="rule:research_reading",
        updated_at=_event_time(),
    )


def _normalize_claim_candidates(
    raw: object,
    *,
    source_id: str,
) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    existing_ids: set[str] = set()
    out: list[dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            continue
        text = _clean_text(item.get("text"))
        if not text:
            continue
        candidate = {
            "id": _clean_text(item.get("id"))
            or _candidate_id("rclaim", source_id, existing_ids, index),
            "text": text,
            "type": _claim_type(item.get("type")),
            "source_refs": _clean_list(item.get("source_refs")) or [source_id],
            "citation_refs": _clean_list(item.get("citation_refs")),
            "confidence": _confidence(item.get("confidence")),
            "warnings": _clean_list(item.get("warnings")),
        }
        if source_id not in candidate["source_refs"]:
            candidate["source_refs"].insert(0, source_id)
        out.append(candidate)
    return out


def _normalize_citations(raw: object, *, source: ResearchSource) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    existing_ids: set[str] = set()
    out: list[dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            continue
        citation = {
            "id": _clean_text(item.get("id"))
            or _candidate_id("cite", source.id, existing_ids, index),
            "label": _clean_text(item.get("label")) or source.title or source.id,
            "title": _clean_text(item.get("title")) or source.title,
            "url": _clean_text(item.get("url")) or source.url,
            "authors": _clean_list(item.get("authors")) or list(source.authors),
            "published": _clean_text(item.get("published")) or source.published,
            "locator": _clean_text(item.get("locator")),
            "quote": _clean_text(item.get("quote")),
            "note": _clean_text(item.get("note")),
        }
        out.append(citation)
    return out


def _reading_from_llm_payload(
    payload: dict[str, Any],
    *,
    source: ResearchSource,
    excerpt: str,
    mode: str,
) -> ResearchReading:
    fallback = _fallback_reading(source, excerpt, mode)
    reading = ResearchReading(
        excerpt=_clean_text(payload.get("excerpt")) or fallback.excerpt,
        translation=_clean_text(payload.get("translation")),
        summary=_clean_text(payload.get("summary")) or fallback.summary,
        key_points=_clean_list(payload.get("key_points")) or fallback.key_points,
        claim_candidates=_normalize_claim_candidates(
            payload.get("claim_candidates"),
            source_id=source.id,
        )
        or fallback.claim_candidates,
        citations=_normalize_citations(payload.get("citations"), source=source)
        or fallback.citations,
        synthesis_notes=_clean_text(payload.get("synthesis_notes"))
        or fallback.synthesis_notes,
        generated_by=_clean_text(payload.get("generated_by")) or "llm:research_reading",
        updated_at=_clean_text(payload.get("updated_at")) or _event_time(),
    )
    return reading


def generate_reading_draft(
    source: ResearchSource,
    excerpt: str,
    mode: str = "summary",
    *,
    profile: str = "",
    chat_func=None,
) -> tuple[ResearchReading, list[str]]:
    """Return source-scoped reading annotations without writing files."""
    clean_excerpt = _clean_text(excerpt)
    clean_mode = _clean_text(mode) or "summary"
    warnings: list[str] = []
    fallback = _fallback_reading(source, clean_excerpt, clean_mode)
    if not clean_excerpt and not source.summary and not source.notes:
        warnings.append(
            "No excerpt, source summary, or source notes were provided; generated a metadata-only reading draft."
        )
    if chat_func is None:
        from nblane.core.ai.gateway import run_ai_action

        refs = [f"research:{source.id}"] if source.id else []
        result = run_ai_action(
            "research.reading_draft",
            {
                "mode": clean_mode,
                "source": _source_metadata(source),
                "excerpt": clean_excerpt,
            },
            profile=profile,
            context_refs=refs,
            require_review=bool(profile),
        )
        warnings.extend(result.warnings)
        if result.ok and isinstance(result.structured, dict):
            return (
                _reading_from_llm_payload(
                    result.structured,
                    source=source,
                    excerpt=clean_excerpt,
                    mode=clean_mode,
                ),
                warnings,
            )
        warnings.append(
            result.error or "AI reading generation failed; used fallback."
        )
        return fallback, warnings

    chat = chat_func
    system = (
        "You turn one research source into source-scoped reading annotations for nblane. "
        "Use only the provided source metadata and excerpt. Return a JSON object with keys: "
        "excerpt, translation, summary, key_points, claim_candidates, citations, "
        "synthesis_notes, generated_by. claim_candidates must be draft source claims, "
        "not accepted public claims. Do not invent unsupported facts."
    )
    user = json.dumps(
        {
            "mode": clean_mode,
            "source": _source_metadata(source),
            "excerpt": clean_excerpt,
            "output_contract": {
                "claim_candidates": [
                    {
                        "text": "string",
                        "type": "learning|project|skill|achievement|impact|role",
                        "source_refs": [source.id],
                        "citation_refs": [],
                        "confidence": "low|medium|high",
                        "warnings": [],
                    }
                ],
                "citations": [
                    {
                        "label": "string",
                        "title": "string",
                        "url": "string",
                        "authors": [],
                        "published": "string",
                        "locator": "string",
                        "quote": "short excerpt only",
                        "note": "string",
                    }
                ],
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    raw = chat(system, user, temperature=0.2)
    if not isinstance(raw, str) or raw.startswith("LLM error:") or raw.startswith(
        "AI features not configured"
    ):
        warnings.append(_clean_text(raw) or "AI reading generation failed; used fallback.")
        return fallback, warnings
    payload = extract_json_object(raw)
    if payload is None:
        warnings.append("Could not parse reading JSON from AI response; used fallback.")
        return fallback, warnings
    return _reading_from_llm_payload(
        payload,
        source=source,
        excerpt=clean_excerpt,
        mode=clean_mode,
    ), warnings


def _evidence_type_for_source(source: ResearchSource) -> str:
    if source.kind == "paper":
        return "paper"
    if source.kind == "repo":
        return "project"
    if source.kind == "book":
        return "course"
    return "learning"


def research_evidence_patch(
    source: ResearchSource,
    reading: ResearchReading | dict[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Return a non-mutating evidence ingest-style patch for a research source."""
    if not _clean_text(source.id):
        raise ValueError("Research source id cannot be blank.")
    if not _clean_text(source.title):
        raise ValueError("Research source title cannot be blank.")
    resolved_reading = (
        reading
        if isinstance(reading, ResearchReading)
        else ResearchReading.from_dict(reading)
        if isinstance(reading, dict)
        else source.reading
    )
    summary = (
        resolved_reading.summary
        or source.summary
        or resolved_reading.synthesis_notes
        or source.notes
        or source.title
    )
    title = source.title
    row: dict[str, Any] = {
        "type": _evidence_type_for_source(source),
        "title": title,
        "summary": summary,
        "source_refs": [source.id],
        "review_status": "needs_review",
        "public_readiness": "private",
        "confidence": "medium",
    }
    if source.published:
        row["date"] = source.published
    if source.url:
        row["url"] = source.url
    if source.project_refs:
        row["project_refs"] = list(source.project_refs)
    if source.experience_refs:
        row["experience_refs"] = list(source.experience_refs)
    if not _clean_text(row.get("summary")):
        raise ValueError("Research evidence candidate summary cannot be blank.")
    return {"evidence_entries": [row], "node_updates": []}


def apply_research_evidence_candidate(
    profile: str,
    source_id: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    """Write a confirmed research evidence candidate and update source refs."""
    clean_profile = _clean_text(profile)
    if not clean_profile:
        raise ValueError("Profile cannot be blank.")
    inbox = load_research_sources(clean_profile)
    source = _find_source(inbox, source_id)
    entries = patch.get("evidence_entries") if isinstance(patch, dict) else None
    if not isinstance(entries, list) or not entries:
        raise ValueError("Research evidence patch must include evidence_entries.")
    row = entries[0] if isinstance(entries[0], dict) else {}
    title = _clean_text(row.get("title"))
    if not title:
        raise ValueError("Research evidence candidate title cannot be blank.")
    if source.id not in _clean_list(row.get("source_refs")):
        raise ValueError("Research evidence candidate must reference its source.")

    pool_raw = load_evidence_pool_raw(clean_profile) or {}
    pool = copy.deepcopy(pool_raw)
    raw_entries = pool.get("evidence_entries")
    if not isinstance(raw_entries, list):
        raw_entries = []
    evidence_entries = [copy.deepcopy(item) for item in raw_entries if isinstance(item, dict)]
    existing_ids = {
        _clean_text(item.get("id"))
        for item in evidence_entries
        if _clean_text(item.get("id"))
    }
    new_row = copy.deepcopy(row)
    requested_id = _clean_text(new_row.get("id"))
    if requested_id and requested_id not in existing_ids:
        new_row["id"] = requested_id
    else:
        new_row["id"] = new_evidence_id(title, existing_ids)
    evidence_entries.append(new_row)
    pool["profile"] = _clean_text(pool.get("profile")) or clean_profile
    pool["evidence_entries"] = evidence_entries
    save_evidence_pool(clean_profile, pool)

    if new_row["id"] not in source.evidence_refs:
        source.evidence_refs.append(new_row["id"])
    if source.status in {"inbox", "reading", "summarized"}:
        source.status = "candidate_ready"
    save_research_sources(clean_profile, inbox)

    pdir = profile_dir(clean_profile)
    changed_paths = [
        pdir / "evidence-pool.yaml",
        pdir / RESEARCH_DIRNAME / RESEARCH_SOURCES_FILENAME,
    ]
    activity = agent_activity.append_activity_item(
        clean_profile,
        {
            "kind": "writeback",
            "candidate_type": "evidence",
            "source_page": "Research",
            "source_ref": source.id,
            "target_owner": "evidence_pool",
            "status": "applied",
            "title": f"Research evidence from {source.title}",
            "summary": _clean_text(new_row.get("summary")) or source.title,
            "refs": {
                "source_refs": [source.id],
                "evidence_refs": [new_row["id"]],
                "files": [_relative_file(path) for path in changed_paths],
            },
            "payload": {"patch": patch, "evidence_id": new_row["id"]},
            "preview": yaml.dump(
                {"evidence_entries": [new_row], "node_updates": []},
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ).strip(),
            "changed_paths": [_relative_file(path) for path in changed_paths],
            "applied_at": _event_time(),
        },
    )
    return {
        "evidence_id": new_row["id"],
        "evidence": new_row,
        "changed_paths": changed_paths,
        "activity_item": activity,
    }


__all__ = [
    "RESEARCH_DIRNAME",
    "RESEARCH_SOURCES_FILENAME",
    "SOURCE_KINDS",
    "SOURCE_ORIGINS",
    "SOURCE_STATUSES",
    "SOURCE_VISIBILITIES",
    "ResearchSource",
    "ResearchSourceInbox",
    "ResearchReading",
    "add_research_source",
    "apply_research_evidence_candidate",
    "archive_research_source",
    "generate_reading_draft",
    "load_research_sources",
    "load_research_sources_raw",
    "research_evidence_patch",
    "save_research_sources",
    "update_research_source",
]
