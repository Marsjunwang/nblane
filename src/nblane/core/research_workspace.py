"""Research Workspace facts and candidate helpers.

This module owns source-aware research artifacts that sit between raw
``research/sources.yaml`` entries and reviewed evidence / public output.
Research claims here are draft provenance objects; accepted public-facing
claims remain in ``evidence-pool.yaml.claims``.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from nblane.core import git_backup
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_io import profile_dir
from nblane.core.research_sources import (
    RESEARCH_DIRNAME,
    ResearchSource,
    load_research_sources,
)
from nblane.core.yaml_io import _load_yaml_dict

RESEARCH_CLAIMS_FILENAME = "claims.yaml"
RESEARCH_CITATIONS_FILENAME = "citations.yaml"
RESEARCH_DRAFTS_FILENAME = "drafts.yaml"
RESEARCH_CHUNKS_DIRNAME = "chunks"
RESEARCH_DRAFTS_DIRNAME = "drafts"

RESEARCH_CLAIM_STATUSES = ("draft", "ready", "promoted", "dismissed")
RESEARCH_CLAIM_TYPES = (
    "achievement",
    "skill",
    "impact",
    "role",
    "learning",
    "project",
    "finding",
    "hypothesis",
)
RESEARCH_CHUNK_KINDS = (
    "excerpt",
    "paragraph",
    "figure",
    "table",
    "method",
    "result",
    "repo",
    "note",
)
RESEARCH_DRAFT_STATUSES = ("draft", "ready", "archived")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today() -> str:
    return date.today().isoformat()


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _clean_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = [part for line in value.splitlines() for part in line.split(",")]
    elif isinstance(value, (list, tuple, set)):
        raw = list(value)
    else:
        raw = [value]
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        clean = _clean_text(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _clean_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {
        _clean_text(key): copy.deepcopy(item)
        for key, item in value.items()
        if _clean_text(key)
    }


def _choice(value: object, options: tuple[str, ...], default: str) -> str:
    clean = _clean_text(value)
    return clean if clean in options else default


def _append_unique(values: list[str], value: object) -> None:
    clean = _clean_text(value)
    if clean and clean not in values:
        values.append(clean)


def _normalized_text(value: object) -> str:
    return re.sub(r"\s+", " ", _clean_text(value)).casefold()


def _research_root(profile: str | Path) -> Path:
    if isinstance(profile, Path):
        return profile / RESEARCH_DIRNAME if profile.name != RESEARCH_DIRNAME else profile
    return profile_dir(profile) / RESEARCH_DIRNAME


def _profile_root(profile: str | Path) -> Path:
    root = _research_root(profile)
    return root.parent if root.name == RESEARCH_DIRNAME else root


def _profile_name(profile: str | Path) -> str:
    if isinstance(profile, Path):
        return profile.parent.name if profile.name == RESEARCH_DIRNAME else profile.name
    return str(profile)


def _slug(value: object, *, fallback: str = "item") -> str:
    clean = _clean_text(value).replace(":", "-").replace("/", "-")
    clean = re.sub(r"[^A-Za-z0-9._~\-\u4e00-\u9fff]+", "-", clean)
    clean = re.sub(r"-+", "-", clean).strip(".-")
    return clean or fallback


def source_slug(source_id: str) -> str:
    """Return the stable chunk filename slug for a source id."""
    return _slug(source_id, fallback="source")


def _yaml_path(profile: str | Path, filename: str) -> Path:
    return _research_root(profile) / filename


def _write_yaml_doc(
    path: Path,
    data: dict[str, Any],
    *,
    header: str,
    action: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    atomic_write_text(path, header + body)
    git_backup.record_change([path], action=action)


def _known_source_map(profile: str | Path) -> dict[str, ResearchSource]:
    root = _research_root(profile)
    profile_path = root.parent if root.name == RESEARCH_DIRNAME else root
    return load_research_sources(profile_path).by_id()


def _chunk_path(profile: str | Path, source_id: str) -> Path:
    return _research_root(profile) / RESEARCH_CHUNKS_DIRNAME / f"{source_slug(source_id)}.jsonl"


@dataclass
class ResearchChunk:
    """One source-scoped citable research chunk."""

    id: str
    source_id: str
    text: str
    kind: str = "excerpt"
    title: str = ""
    locator: str = ""
    created: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> "ResearchChunk | None":
        if not isinstance(data, dict):
            return None
        source_id = _clean_text(data.get("source_id"))
        text = _clean_text(data.get("text"))
        chunk_id = _clean_text(data.get("id"))
        if not source_id or not text or not chunk_id:
            return None
        return cls(
            id=chunk_id,
            source_id=source_id,
            text=text,
            kind=_choice(data.get("kind"), RESEARCH_CHUNK_KINDS, "excerpt"),
            title=_clean_text(data.get("title")),
            locator=_clean_text(data.get("locator")),
            created=_clean_text(data.get("created")),
            metadata=_clean_mapping(data.get("metadata")),
        )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "id": self.id,
            "source_id": self.source_id,
            "kind": self.kind,
            "text": self.text,
        }
        for key in ("title", "locator", "created"):
            value = getattr(self, key)
            if value:
                data[key] = value
        if self.metadata:
            data["metadata"] = copy.deepcopy(self.metadata)
        return data


@dataclass
class ResearchClaim:
    """A draft source-aware claim from reading or synthesis."""

    id: str
    text: str
    status: str = "draft"
    type: str = "learning"
    source_refs: list[str] = field(default_factory=list)
    chunk_refs: list[str] = field(default_factory=list)
    citation_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    output_refs: list[str] = field(default_factory=list)
    confidence: str = "medium"
    rationale: str = ""
    human_note: bool = False
    warnings: list[str] = field(default_factory=list)
    generated_by: str = ""
    created: str = ""
    updated: str = ""

    @classmethod
    def from_dict(cls, data: object) -> "ResearchClaim | None":
        if not isinstance(data, dict):
            return None
        claim_id = _clean_text(data.get("id"))
        text = _clean_text(data.get("text"))
        if not claim_id or not text:
            return None
        return cls(
            id=claim_id,
            text=text,
            status=_choice(data.get("status"), RESEARCH_CLAIM_STATUSES, "draft"),
            type=_choice(data.get("type"), RESEARCH_CLAIM_TYPES, "learning"),
            source_refs=_clean_list(data.get("source_refs")),
            chunk_refs=_clean_list(data.get("chunk_refs")),
            citation_refs=_clean_list(data.get("citation_refs")),
            evidence_refs=_clean_list(data.get("evidence_refs")),
            output_refs=_clean_list(data.get("output_refs")),
            confidence=_choice(data.get("confidence"), ("low", "medium", "high"), "medium"),
            rationale=_clean_text(data.get("rationale")),
            human_note=bool(data.get("human_note")),
            warnings=_clean_list(data.get("warnings")),
            generated_by=_clean_text(data.get("generated_by")),
            created=_clean_text(data.get("created")),
            updated=_clean_text(data.get("updated")),
        )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "id": self.id,
            "status": self.status,
            "type": self.type,
            "text": self.text,
            "source_refs": list(self.source_refs),
            "chunk_refs": list(self.chunk_refs),
            "citation_refs": list(self.citation_refs),
            "confidence": self.confidence,
            "human_note": bool(self.human_note),
        }
        for key in (
            "evidence_refs",
            "output_refs",
            "warnings",
        ):
            values = getattr(self, key)
            if values:
                data[key] = list(values)
        for key in ("rationale", "generated_by", "created", "updated"):
            value = getattr(self, key)
            if value:
                data[key] = value
        return data


@dataclass
class ResearchCitation:
    """A citation binding a claim to source/chunk material."""

    id: str
    claim_id: str
    source_id: str = ""
    chunk_id: str = ""
    locator: str = ""
    quote: str = ""
    url: str = ""
    bibliography: str = ""
    note: str = ""
    created: str = ""

    @classmethod
    def from_dict(cls, data: object) -> "ResearchCitation | None":
        if not isinstance(data, dict):
            return None
        citation_id = _clean_text(data.get("id"))
        claim_id = _clean_text(data.get("claim_id"))
        if not citation_id or not claim_id:
            return None
        return cls(
            id=citation_id,
            claim_id=claim_id,
            source_id=_clean_text(data.get("source_id")),
            chunk_id=_clean_text(data.get("chunk_id")),
            locator=_clean_text(data.get("locator")),
            quote=_clean_text(data.get("quote")),
            url=_clean_text(data.get("url")),
            bibliography=_clean_text(data.get("bibliography")),
            note=_clean_text(data.get("note")),
            created=_clean_text(data.get("created")),
        )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "id": self.id,
            "claim_id": self.claim_id,
        }
        for key in (
            "source_id",
            "chunk_id",
            "locator",
            "quote",
            "url",
            "bibliography",
            "note",
            "created",
        ):
            value = getattr(self, key)
            if value:
                data[key] = value
        return data


def load_chunks(profile: str | Path, source_id: str = "") -> list[ResearchChunk]:
    """Load research chunks for one source or all sources."""
    root = _research_root(profile) / RESEARCH_CHUNKS_DIRNAME
    paths = [_chunk_path(profile, source_id)] if source_id else sorted(root.glob("*.jsonl"))
    chunks: list[ResearchChunk] = []
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            chunk = ResearchChunk.from_dict(parsed)
            if chunk is not None:
                chunks.append(chunk)
    return chunks


def save_chunks(profile: str | Path, source_id: str, chunks: list[ResearchChunk | dict]) -> Path:
    """Persist all chunks for one source as JSONL."""
    path = _chunk_path(profile, source_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for item in chunks:
        chunk = item if isinstance(item, ResearchChunk) else ResearchChunk.from_dict(item)
        if chunk is not None:
            rows.append(chunk.to_dict())
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    atomic_write_text(path, text)
    git_backup.record_change([path], action=f"update research chunks for {source_id}")
    return path


def _next_chunk_id(existing: list[ResearchChunk], source_id: str) -> str:
    slug = source_slug(source_id)
    max_index = 0
    prefix = f"chunk:{slug}:"
    for chunk in existing:
        if not chunk.id.startswith(prefix):
            continue
        try:
            max_index = max(max_index, int(chunk.id.rsplit(":", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_index + 1:03d}"


def create_chunk(
    profile: str | Path,
    source_id: str,
    text: str,
    *,
    kind: str = "excerpt",
    title: str = "",
    locator: str = "",
    chunk_id: str = "",
    metadata: dict[str, object] | None = None,
) -> ResearchChunk:
    """Append a citable chunk to ``research/chunks/<source>.jsonl``."""
    clean_source = _clean_text(source_id)
    if not clean_source:
        raise ValueError("Research chunk source_id cannot be blank.")
    if clean_source not in _known_source_map(profile):
        raise ValueError(f"Unknown research source: {clean_source}")
    clean_text = _clean_text(text)
    if not clean_text:
        raise ValueError("Research chunk text cannot be blank.")
    chunks = load_chunks(profile, clean_source)
    existing_ids = {chunk.id for chunk in chunks}
    clean_id = _clean_text(chunk_id) or _next_chunk_id(chunks, clean_source)
    if clean_id in existing_ids:
        raise ValueError(f"Duplicate research chunk id: {clean_id}")
    chunk = ResearchChunk(
        id=clean_id,
        source_id=clean_source,
        text=clean_text,
        kind=_choice(kind, RESEARCH_CHUNK_KINDS, "excerpt"),
        title=_clean_text(title),
        locator=_clean_text(locator),
        created=_now(),
        metadata=_clean_mapping(metadata),
    )
    chunks.append(chunk)
    save_chunks(profile, clean_source, chunks)
    return chunk


def _load_list_doc(profile: str | Path, filename: str, key: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw = _load_yaml_dict(_yaml_path(profile, filename)) or {}
    rows = [copy.deepcopy(item) for item in raw.get(key) or [] if isinstance(item, dict)]
    return raw, rows


def load_research_claims(profile: str | Path) -> list[ResearchClaim]:
    raw, rows = _load_list_doc(profile, RESEARCH_CLAIMS_FILENAME, "claims")
    return [claim for row in rows if (claim := ResearchClaim.from_dict(row)) is not None]


def save_research_claims(profile: str | Path, claims: list[ResearchClaim | dict]) -> Path:
    path = _yaml_path(profile, RESEARCH_CLAIMS_FILENAME)
    profile_name = _profile_name(profile)
    rows = []
    for item in claims:
        claim = item if isinstance(item, ResearchClaim) else ResearchClaim.from_dict(item)
        if claim is not None:
            rows.append(claim.to_dict())
    data = {
        "schema_version": "1.0",
        "profile": profile_name,
        "updated": _today(),
        "claims": rows,
    }
    _write_yaml_doc(
        path,
        data,
        header=(
            f"# Research claims for {profile_name}\n"
            "# Draft source-aware claims; accepted claims live in evidence-pool.yaml.\n\n"
        ),
        action=f"update {profile_name}/research/claims.yaml",
    )
    return path


def _next_claim_id(claims: list[ResearchClaim]) -> str:
    today = date.today().strftime("%Y%m%d")
    prefix = f"rclaim:{today}:"
    max_index = 0
    for claim in claims:
        if not claim.id.startswith(prefix):
            continue
        try:
            max_index = max(max_index, int(claim.id.rsplit(":", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_index + 1:03d}"


def _known_chunk_ids(profile: str | Path) -> set[str]:
    return {chunk.id for chunk in load_chunks(profile)}


def _validate_claim_refs(profile: str | Path, claim: ResearchClaim) -> None:
    if not claim.source_refs and not claim.chunk_refs and not claim.human_note:
        raise ValueError("Research claim must reference a source/chunk or set human_note=true.")
    known_sources = _known_source_map(profile)
    unknown_sources = [ref for ref in claim.source_refs if ref not in known_sources]
    if unknown_sources:
        raise ValueError(f"Unknown research source refs: {', '.join(unknown_sources)}")
    known_chunks = _known_chunk_ids(profile)
    unknown_chunks = [ref for ref in claim.chunk_refs if ref not in known_chunks]
    if unknown_chunks:
        raise ValueError(f"Unknown research chunk refs: {', '.join(unknown_chunks)}")


def upsert_research_claim(
    profile: str | Path,
    text: str,
    *,
    claim_id: str = "",
    status: str = "draft",
    type: str = "learning",
    source_refs: object = None,
    chunk_refs: object = None,
    citation_refs: object = None,
    evidence_refs: object = None,
    output_refs: object = None,
    confidence: str = "medium",
    rationale: str = "",
    human_note: bool = False,
    warnings: object = None,
    generated_by: str = "manual",
) -> ResearchClaim:
    """Create or update a Research Workspace claim."""
    clean_text = _clean_text(text)
    if not clean_text:
        raise ValueError("Research claim text cannot be blank.")
    claims = load_research_claims(profile)
    clean_id = _clean_text(claim_id) or _next_claim_id(claims)
    now = _now()
    existing = next((claim for claim in claims if claim.id == clean_id), None)
    claim = ResearchClaim(
        id=clean_id,
        text=clean_text,
        status=_choice(status, RESEARCH_CLAIM_STATUSES, existing.status if existing else "draft"),
        type=_choice(type, RESEARCH_CLAIM_TYPES, existing.type if existing else "learning"),
        source_refs=_clean_list(source_refs),
        chunk_refs=_clean_list(chunk_refs),
        citation_refs=_clean_list(citation_refs),
        evidence_refs=_clean_list(evidence_refs),
        output_refs=_clean_list(output_refs),
        confidence=_choice(confidence, ("low", "medium", "high"), "medium"),
        rationale=_clean_text(rationale),
        human_note=bool(human_note),
        warnings=_clean_list(warnings),
        generated_by=_clean_text(generated_by),
        created=existing.created if existing else now,
        updated=now,
    )
    _validate_claim_refs(profile, claim)
    if existing is None:
        claims.append(claim)
    else:
        claims = [claim if item.id == clean_id else item for item in claims]
    save_research_claims(profile, claims)
    return claim


def load_research_citations(profile: str | Path) -> list[ResearchCitation]:
    raw, rows = _load_list_doc(profile, RESEARCH_CITATIONS_FILENAME, "citations")
    return [citation for row in rows if (citation := ResearchCitation.from_dict(row)) is not None]


def save_research_citations(profile: str | Path, citations: list[ResearchCitation | dict]) -> Path:
    path = _yaml_path(profile, RESEARCH_CITATIONS_FILENAME)
    profile_name = _profile_name(profile)
    rows = []
    for item in citations:
        citation = item if isinstance(item, ResearchCitation) else ResearchCitation.from_dict(item)
        if citation is not None:
            rows.append(citation.to_dict())
    data = {
        "schema_version": "1.0",
        "profile": profile_name,
        "updated": _today(),
        "citations": rows,
    }
    _write_yaml_doc(
        path,
        data,
        header=f"# Research citations for {profile_name}\n\n",
        action=f"update {profile_name}/research/citations.yaml",
    )
    return path


def _next_citation_id(citations: list[ResearchCitation], claim_id: str) -> str:
    slug = _slug(claim_id, fallback="claim")
    prefix = f"cite:{slug}:"
    max_index = 0
    for citation in citations:
        if not citation.id.startswith(prefix):
            continue
        try:
            max_index = max(max_index, int(citation.id.rsplit(":", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_index + 1:03d}"


def create_citation(
    profile: str | Path,
    claim_id: str,
    *,
    source_id: str = "",
    chunk_id: str = "",
    locator: str = "",
    quote: str = "",
    url: str = "",
    bibliography: str = "",
    note: str = "",
    citation_id: str = "",
) -> ResearchCitation:
    """Create a citation binding a research claim to a source or chunk."""
    clean_claim = _clean_text(claim_id)
    claims = load_research_claims(profile)
    if clean_claim not in {claim.id for claim in claims}:
        raise ValueError(f"Unknown research claim: {clean_claim}")
    clean_source = _clean_text(source_id)
    clean_chunk = _clean_text(chunk_id)
    if not clean_source and not clean_chunk:
        raise ValueError("Research citation must reference a source or chunk.")
    if clean_source and clean_source not in _known_source_map(profile):
        raise ValueError(f"Unknown research source: {clean_source}")
    if clean_chunk and clean_chunk not in _known_chunk_ids(profile):
        raise ValueError(f"Unknown research chunk: {clean_chunk}")
    citations = load_research_citations(profile)
    clean_id = _clean_text(citation_id) or _next_citation_id(citations, clean_claim)
    if clean_id in {citation.id for citation in citations}:
        raise ValueError(f"Duplicate research citation id: {clean_id}")
    citation = ResearchCitation(
        id=clean_id,
        claim_id=clean_claim,
        source_id=clean_source,
        chunk_id=clean_chunk,
        locator=_clean_text(locator),
        quote=_clean_text(quote),
        url=_clean_text(url),
        bibliography=_clean_text(bibliography),
        note=_clean_text(note),
        created=_now(),
    )
    citations.append(citation)
    save_research_citations(profile, citations)
    for claim in claims:
        if claim.id == clean_claim and citation.id not in claim.citation_refs:
            claim.citation_refs.append(citation.id)
            claim.updated = _now()
            break
    save_research_claims(profile, claims)
    return citation


def load_research_drafts(profile: str | Path) -> list[dict[str, Any]]:
    raw = _load_yaml_dict(_yaml_path(profile, RESEARCH_DRAFTS_FILENAME)) or {}
    return [copy.deepcopy(item) for item in raw.get("drafts") or [] if isinstance(item, dict)]


def save_research_drafts(profile: str | Path, drafts: list[dict[str, Any]]) -> Path:
    path = _yaml_path(profile, RESEARCH_DRAFTS_FILENAME)
    profile_name = _profile_name(profile)
    data = {
        "schema_version": "1.0",
        "profile": profile_name,
        "updated": _today(),
        "drafts": drafts,
    }
    _write_yaml_doc(
        path,
        data,
        header=f"# Research synthesis drafts for {profile_name}\n\n",
        action=f"update {profile_name}/research/drafts.yaml",
    )
    return path


def _next_draft_id(drafts: list[dict[str, Any]]) -> str:
    today = date.today().strftime("%Y%m%d")
    prefix = f"rdraft:{today}:"
    max_index = 0
    for draft in drafts:
        draft_id = _clean_text(draft.get("id"))
        if not draft_id.startswith(prefix):
            continue
        try:
            max_index = max(max_index, int(draft_id.rsplit(":", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_index + 1:03d}"


def _draft_body_path(profile: str | Path, draft_id: str) -> Path:
    return _research_root(profile) / RESEARCH_DRAFTS_DIRNAME / f"{_slug(draft_id, fallback='draft')}.md"


def _find_research_draft(profile: str | Path, draft_id: str) -> dict[str, Any]:
    clean_id = _clean_text(draft_id)
    draft = next((item for item in load_research_drafts(profile) if _clean_text(item.get("id")) == clean_id), None)
    if draft is None:
        raise ValueError(f"Unknown research draft: {clean_id}")
    return draft


def _research_draft_context(profile: str | Path, draft_id: str) -> dict[str, Any]:
    draft = _find_research_draft(profile, draft_id)
    body_path = _research_root(profile) / _clean_text(draft.get("body_path"))
    body = body_path.read_text(encoding="utf-8") if body_path.exists() else ""
    chunks = {chunk.id: chunk for chunk in load_chunks(profile)}
    claims = {claim.id: claim for claim in load_research_claims(profile)}
    citation_map = {citation.id: citation for citation in load_research_citations(profile)}
    claim_refs = _clean_list(draft.get("claim_refs"))
    source_refs = _clean_list(draft.get("source_refs"))
    citation_refs = _clean_list(draft.get("citation_refs"))
    claim_rows: list[ResearchClaim] = []
    missing_claim_refs: list[str] = []
    for claim_ref in claim_refs:
        claim = claims.get(claim_ref)
        if claim is None:
            missing_claim_refs.append(claim_ref)
            continue
        claim_rows.append(claim)
        for source_ref in _claim_source_refs(claim, chunks):
            _append_unique(source_refs, source_ref)
        for citation_ref in claim.citation_refs:
            _append_unique(citation_refs, citation_ref)
    missing_citation_refs = [ref for ref in citation_refs if ref and ref not in citation_map]
    missing_citation_claim_refs = [claim.id for claim in claim_rows if not claim.citation_refs]
    return {
        "draft": draft,
        "body": body,
        "claim_refs": claim_refs,
        "source_refs": source_refs,
        "citation_refs": citation_refs,
        "claims": claim_rows,
        "missing_claim_refs": missing_claim_refs,
        "missing_citation_refs": missing_citation_refs,
        "missing_citation_claim_refs": missing_citation_claim_refs,
        "chunks": chunks,
    }


def draft_synthesis_from_claims(
    profile: str | Path,
    title: str,
    claim_ids: list[str],
    *,
    draft_id: str = "",
    body: str = "",
    status: str = "draft",
) -> dict[str, Any]:
    """Create a synthesis draft from selected research claims."""
    clean_title = _clean_text(title)
    if not clean_title:
        raise ValueError("Research draft title cannot be blank.")
    clean_claim_ids = _clean_list(claim_ids)
    claims = {claim.id: claim for claim in load_research_claims(profile)}
    missing = [claim_id for claim_id in clean_claim_ids if claim_id not in claims]
    if missing:
        raise ValueError(f"Unknown research claims: {', '.join(missing)}")
    drafts = load_research_drafts(profile)
    clean_id = _clean_text(draft_id) or _next_draft_id(drafts)
    if clean_id in {_clean_text(item.get("id")) for item in drafts}:
        raise ValueError(f"Duplicate research draft id: {clean_id}")
    source_refs: list[str] = []
    citation_refs: list[str] = []
    for claim_id in clean_claim_ids:
        for source_ref in claims[claim_id].source_refs:
            if source_ref not in source_refs:
                source_refs.append(source_ref)
        for citation_ref in claims[claim_id].citation_refs:
            if citation_ref not in citation_refs:
                citation_refs.append(citation_ref)
    clean_body = _clean_text(body)
    if not clean_body:
        missing_citation_claims = [
            claims[claim_id]
            for claim_id in clean_claim_ids
            if not claims[claim_id].citation_refs
        ]
        lines = [
            f"# {clean_title}",
            "",
            "## Outline",
            "",
            "1. Frame the research question and collection scope.",
            "2. Connect reviewed claims to source-backed evidence.",
            "3. Separate implications from open citation gaps.",
            "",
            "## Argument Map",
            "",
        ]
        for claim_id in clean_claim_ids:
            claim = claims[claim_id]
            cited = ", ".join(claim.citation_refs) or "missing citation"
            lines.append(f"- [{claim.type}] {claim.text} (citations: {cited})")
        lines.extend(
            [
                "",
                "## Coverage",
                "",
                f"- Claims: {len(clean_claim_ids)}",
                f"- Sources: {len(source_refs)}",
                f"- Citations: {len(citation_refs)}",
                "",
                "## Draft",
                "",
            ]
        )
        for claim_id in clean_claim_ids:
            lines.append(f"- {claims[claim_id].text}")
        if missing_citation_claims:
            lines.extend(["", "## Missing Citation Warnings", ""])
            for claim in missing_citation_claims:
                lines.append(f"- {claim.id}: {claim.text}")
        clean_body = "\n".join(lines).strip() + "\n"
    path = _draft_body_path(profile, clean_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, clean_body if clean_body.endswith("\n") else clean_body + "\n")
    draft = {
        "id": clean_id,
        "title": clean_title,
        "status": _choice(status, RESEARCH_DRAFT_STATUSES, "draft"),
        "claim_refs": clean_claim_ids,
        "source_refs": source_refs,
        "citation_refs": citation_refs,
        "body_path": path.relative_to(_research_root(profile)).as_posix(),
        "created": _now(),
        "updated": _now(),
    }
    drafts.append(draft)
    save_research_drafts(profile, drafts)
    git_backup.record_change([path], action=f"write research draft {clean_id}")
    return draft


def research_claim_to_evidence_candidate(profile: str | Path, claim_id: str) -> dict[str, list[dict[str, Any]]]:
    """Return a non-mutating evidence candidate patch for a research claim."""
    clean_claim = _clean_text(claim_id)
    claim = next((item for item in load_research_claims(profile) if item.id == clean_claim), None)
    if claim is None:
        raise ValueError(f"Unknown research claim: {clean_claim}")
    if not claim.source_refs and not claim.chunk_refs and not claim.human_note:
        raise ValueError("Research claim is not source-aware enough for evidence.")
    chunks = {chunk.id: chunk for chunk in load_chunks(profile)}
    source_refs = _claim_source_refs(claim, chunks)
    row: dict[str, Any] = {
        "type": "learning" if claim.type in {"finding", "hypothesis"} else claim.type,
        "title": claim.text[:96],
        "summary": claim.text,
        "source_refs": source_refs,
        "review_status": "needs_review",
        "public_readiness": "private",
        "confidence": claim.confidence,
        "research_claim_refs": [claim.id],
    }
    if claim.citation_refs:
        row["citation_refs"] = list(claim.citation_refs)
    return {"evidence_entries": [row], "node_updates": []}


def research_draft_to_blog_candidate(profile: str | Path, draft_id: str) -> dict[str, Any]:
    """Return a source-aware blog draft candidate without writing public files."""
    clean_id = _clean_text(draft_id)
    context = _research_draft_context(profile, draft_id)
    draft = context["draft"]
    body = str(context.get("body") or "")
    title = _clean_text(draft.get("title")) or clean_id
    claim_refs = _clean_list(context.get("claim_refs"))
    source_refs = _clean_list(context.get("source_refs"))
    citation_refs = _clean_list(context.get("citation_refs"))
    return {
        "kind": "blog_draft",
        "title": title,
        "summary": body.splitlines()[0].lstrip("# ").strip() if body.strip() else title,
        "tags": ["research"],
        "related_evidence": [],
        "related_kanban": [],
        "related_claims": [],
        "related_sources": source_refs,
        "related_research_claims": claim_refs,
        "related_citations": citation_refs,
        "warnings": [
            "Research draft candidate: publish only after checking source visibility and promoted research claims."
        ],
        "body": body,
    }


def _research_project_rows(profile: str | Path) -> list[dict[str, Any]]:
    raw = _load_yaml_dict(_profile_root(profile) / "projects.yaml") or {}
    projects = raw.get("projects") or []
    return [copy.deepcopy(item) for item in projects if isinstance(item, dict)]


def research_output_project_options(profile: str | Path) -> list[dict[str, str]]:
    """Return project choices usable by research output candidate previews."""
    options: list[dict[str, str]] = []
    for row in _research_project_rows(profile):
        project_id = _clean_text(row.get("id"))
        if not project_id:
            continue
        options.append(
            {
                "id": project_id,
                "title": _clean_text(row.get("title")) or project_id,
                "status": _clean_text(row.get("status")),
            }
        )
    return options


def _project_ref_index(profile: str | Path) -> dict[str, dict[str, Any]]:
    return {
        _clean_text(row.get("id")): row
        for row in _research_project_rows(profile)
        if _clean_text(row.get("id"))
    }


def _project_refs_from_sources(profile: str | Path, source_refs: list[str]) -> list[str]:
    sources = _known_source_map(profile)
    refs: list[str] = []
    for source_ref in source_refs:
        source = sources.get(source_ref)
        if source is None:
            continue
        for project_ref in source.project_refs:
            _append_unique(refs, project_ref)
    return refs


def research_draft_to_project_update_candidate(
    profile: str | Path,
    draft_id: str,
    *,
    project_id: str = "",
) -> dict[str, Any]:
    """Return a project update candidate from one research draft without writing."""
    context = _research_draft_context(profile, draft_id)
    draft = context["draft"]
    claim_rows: list[ResearchClaim] = list(context.get("claims") or [])
    source_refs = _clean_list(context.get("source_refs"))
    citation_refs = _clean_list(context.get("citation_refs"))
    claim_refs = _clean_list(context.get("claim_refs"))
    projects = _project_ref_index(profile)
    clean_project = _clean_text(project_id)
    inferred_projects = _project_refs_from_sources(profile, source_refs)
    if not clean_project and len(inferred_projects) == 1:
        clean_project = inferred_projects[0]
    if clean_project and clean_project not in projects:
        raise ValueError(f"Unknown project id: {clean_project}")
    project = projects.get(clean_project, {})
    project_title = _clean_text(project.get("title")) or clean_project
    title_base = project_title or _clean_text(draft.get("title")) or _clean_text(draft.get("id")) or "Research draft"
    title = f"{title_base} claim-backed update"
    lines = [f"Update draft for {title_base}.", "", "Supported research claims:"]
    for claim in claim_rows:
        cited = ", ".join(claim.citation_refs) or "missing citation"
        lines.append(f"- [{claim.type}] {claim.text} (citations: {cited})")
    if not claim_rows:
        lines.append("- Review the synthesis draft and add supported research claims.")
    lines.extend(
        [
            "",
            "Review angle:",
            "Connect these source-backed claims to project progress without adding unsupported facts.",
        ]
    )
    warnings = [
        "Research project update candidate: review source visibility, promoted claims, metrics, links, and private details before publishing.",
    ]
    if not clean_project:
        warnings.append("Select a project before writing this candidate into projects.yaml.")
    if context.get("missing_claim_refs"):
        warnings.append("Some draft claim refs are missing: " + ", ".join(context["missing_claim_refs"]))
    if context.get("missing_citation_refs"):
        warnings.append("Some draft citation refs are missing: " + ", ".join(context["missing_citation_refs"]))
    if context.get("missing_citation_claim_refs"):
        warnings.append(
            "Some selected claims need citation links before public use: "
            + ", ".join(context["missing_citation_claim_refs"])
        )
    return {
        "kind": "project_update",
        "project_id": clean_project,
        "title": title,
        "body": "\n".join(lines).strip() + "\n",
        "related_evidence": [],
        "related_claims": [],
        "related_sources": source_refs,
        "related_research_claims": claim_refs,
        "related_citations": citation_refs,
        "warnings": warnings,
    }


def research_draft_to_resume_bullet_candidates(profile: str | Path, draft_id: str) -> list[dict[str, Any]]:
    """Return resume bullet candidates from one research draft without writing."""
    context = _research_draft_context(profile, draft_id)
    chunks: dict[str, ResearchChunk] = context.get("chunks") or {}
    bullets: list[dict[str, Any]] = []
    base_warning = (
        "Research resume bullet candidate: review scope, metrics, source visibility, and private details before adding to resume-source.yaml."
    )
    for claim in context.get("claims") or []:
        source_refs = _claim_source_refs(claim, chunks)
        warnings = [base_warning]
        if not claim.citation_refs:
            warnings.append(f"{claim.id} has no linked citation.")
        if claim.status != "promoted":
            warnings.append(f"{claim.id} is not promoted yet.")
        bullets.append(
            {
                "kind": "resume_bullet",
                "text": claim.text.rstrip(".。"),
                "related_evidence": [],
                "related_claims": [],
                "related_sources": source_refs,
                "related_research_claims": [claim.id],
                "related_citations": list(claim.citation_refs),
                "warnings": warnings,
            }
        )
    if not bullets:
        bullets.append(
            {
                "kind": "resume_bullet",
                "text": "Add a citation-backed research claim before drafting a resume bullet.",
                "related_evidence": [],
                "related_claims": [],
                "related_sources": _clean_list(context.get("source_refs")),
                "related_research_claims": _clean_list(context.get("claim_refs")),
                "related_citations": _clean_list(context.get("citation_refs")),
                "warnings": [base_warning],
            }
        )
    return bullets


def research_draft_to_output_candidates(
    profile: str | Path,
    draft_id: str,
    *,
    project_id: str = "",
) -> dict[str, Any]:
    """Return all public-output candidates for one research draft without writing."""
    clean_id = _clean_text(draft_id)
    return {
        "draft_id": clean_id,
        "project_options": research_output_project_options(profile),
        "blog_draft": research_draft_to_blog_candidate(profile, clean_id),
        "project_update": research_draft_to_project_update_candidate(
            profile,
            clean_id,
            project_id=project_id,
        ),
        "resume_bullets": research_draft_to_resume_bullet_candidates(profile, clean_id),
    }


def build_synthesis_draft_review(profile: str | Path, draft_id: str) -> dict[str, Any]:
    """Return coverage and citation review data for one synthesis draft."""

    clean_id = _clean_text(draft_id)
    draft = next((item for item in load_research_drafts(profile) if _clean_text(item.get("id")) == clean_id), None)
    if draft is None:
        raise ValueError(f"Unknown research draft: {clean_id}")
    chunks = {chunk.id: chunk for chunk in load_chunks(profile)}
    claims = {claim.id: claim for claim in load_research_claims(profile)}
    citations = {citation.id: citation for citation in load_research_citations(profile)}
    claim_refs = _clean_list(draft.get("claim_refs"))
    citation_refs = _clean_list(draft.get("citation_refs"))
    source_refs = _clean_list(draft.get("source_refs"))
    argument_map = []
    missing_citation_claim_refs = []
    missing_claim_refs = []
    broken_citation_refs = []
    for claim_ref in claim_refs:
        claim = claims.get(claim_ref)
        if claim is None:
            missing_claim_refs.append(claim_ref)
            continue
        claim_sources = _claim_source_refs(claim, chunks)
        claim_citations = [ref for ref in claim.citation_refs if ref in citations]
        if not claim_citations:
            missing_citation_claim_refs.append(claim.id)
        for citation_ref in claim_citations:
            if not verify_research_citation(profile, citation_ref).get("ok"):
                _append_unique(broken_citation_refs, citation_ref)
        argument_map.append(
            {
                "claim_id": claim.id,
                "type": claim.type,
                "status": claim.status,
                "text": claim.text,
                "source_refs": claim_sources,
                "citation_refs": list(claim.citation_refs),
            }
        )
    missing_citation_refs = [ref for ref in citation_refs if ref and ref not in citations]
    return {
        "draft_id": clean_id,
        "title": _clean_text(draft.get("title")) or clean_id,
        "coverage": {
            "claim_refs": claim_refs,
            "source_refs": source_refs,
            "citation_refs": citation_refs,
            "claims": len(claim_refs),
            "sources": len(source_refs),
            "citations": len(citation_refs),
        },
        "argument_map": argument_map,
        "warnings": {
            "missing_claim_refs": missing_claim_refs,
            "missing_citation_refs": missing_citation_refs,
            "missing_citation_claim_refs": missing_citation_claim_refs,
            "broken_citation_refs": broken_citation_refs,
        },
    }


def _source_card(source: ResearchSource | None) -> dict[str, Any]:
    if source is None:
        return {}
    return {
        "id": source.id,
        "title": source.title,
        "kind": source.kind,
        "url": source.url,
        "status": source.status,
        "visibility": source.visibility,
        "authors": list(source.authors),
        "published": source.published,
        "tags": list(source.tags),
        "library_node_refs": list(source.library_node_refs),
    }


def _claim_source_refs(claim: ResearchClaim, chunks: dict[str, ResearchChunk]) -> list[str]:
    refs: list[str] = []
    for ref in claim.source_refs:
        _append_unique(refs, ref)
    for chunk_ref in claim.chunk_refs:
        chunk = chunks.get(chunk_ref)
        if chunk is not None:
            _append_unique(refs, chunk.source_id)
    return refs


def _verify_citation_row(
    citation: ResearchCitation,
    *,
    claims: dict[str, ResearchClaim],
    chunks: dict[str, ResearchChunk],
    sources: dict[str, ResearchSource],
) -> dict[str, Any]:
    if citation.claim_id not in claims:
        return {
            "ok": False,
            "level": "error",
            "message": f"Unknown research claim: {citation.claim_id}",
            "citation_id": citation.id,
        }
    if citation.source_id and citation.source_id not in sources:
        return {
            "ok": False,
            "level": "error",
            "message": f"Unknown research source: {citation.source_id}",
            "citation_id": citation.id,
        }
    chunk = chunks.get(citation.chunk_id)
    if citation.chunk_id and chunk is None:
        return {
            "ok": False,
            "level": "error",
            "message": f"Unknown research chunk: {citation.chunk_id}",
            "citation_id": citation.id,
        }
    if chunk is not None and citation.source_id and citation.source_id != chunk.source_id:
        return {
            "ok": False,
            "level": "error",
            "message": f"Citation source {citation.source_id} does not match chunk source {chunk.source_id}.",
            "citation_id": citation.id,
        }
    if not citation.quote:
        return {
            "ok": False,
            "level": "missing_quote",
            "message": "Citation has no quote to verify.",
            "citation_id": citation.id,
        }
    if chunk is None:
        return {
            "ok": False,
            "level": "weak",
            "message": "Citation quote cannot be verified without a chunk.",
            "citation_id": citation.id,
        }
    quote = _normalized_text(citation.quote)
    chunk_text = _normalized_text(chunk.text)
    if quote and chunk_text and quote in chunk_text:
        return {
            "ok": True,
            "level": "ok",
            "message": "Quote matches the linked chunk.",
            "citation_id": citation.id,
        }
    return {
        "ok": False,
        "level": "warning",
        "message": f"Quote does not match linked chunk {citation.chunk_id}.",
        "citation_id": citation.id,
    }


def verify_research_citation(profile: str | Path, citation_id: str) -> dict[str, Any]:
    """Verify one citation's claim/source/chunk/quote linkage."""
    clean_id = _clean_text(citation_id)
    citations = {citation.id: citation for citation in load_research_citations(profile)}
    citation = citations.get(clean_id)
    if citation is None:
        return {
            "ok": False,
            "level": "error",
            "message": f"Unknown research citation: {clean_id}",
            "citation_id": clean_id,
        }
    return _verify_citation_row(
        citation,
        claims={claim.id: claim for claim in load_research_claims(profile)},
        chunks={chunk.id: chunk for chunk in load_chunks(profile)},
        sources=_known_source_map(profile),
    )


def update_research_claim_status(
    profile: str | Path,
    claim_id: str,
    status: str,
    note: str = "",
) -> ResearchClaim:
    """Update one research claim's lifecycle status."""
    clean_id = _clean_text(claim_id)
    clean_status = _choice(status, RESEARCH_CLAIM_STATUSES, "")
    if not clean_status:
        raise ValueError(f"Unknown research claim status: {status}")
    claims = load_research_claims(profile)
    claim = next((item for item in claims if item.id == clean_id), None)
    if claim is None:
        raise ValueError(f"Unknown research claim: {clean_id}")
    updated = copy.deepcopy(claim)
    updated.status = clean_status
    updated.updated = _now()
    if note:
        updated.rationale = (
            f"{updated.rationale}\n{_clean_text(note)}".strip()
            if updated.rationale
            else _clean_text(note)
        )
    if updated.status == "ready":
        _validate_claim_refs(profile, updated)
    claims = [updated if item.id == clean_id else item for item in claims]
    save_research_claims(profile, claims)
    return updated


def update_research_claim_links(
    profile: str | Path,
    claim_id: str,
    *,
    source_refs: object = None,
    chunk_refs: object = None,
    citation_refs: object = None,
    mode: str = "append",
) -> ResearchClaim:
    """Patch source/chunk/citation refs for one research claim."""
    clean_id = _clean_text(claim_id)
    clean_mode = _clean_text(mode) or "append"
    if clean_mode not in {"append", "replace", "remove"}:
        raise ValueError(f"Unknown research claim link mode: {mode}")
    replace = clean_mode == "replace"
    remove = clean_mode == "remove"
    claims = load_research_claims(profile)
    claim = next((item for item in claims if item.id == clean_id), None)
    if claim is None:
        raise ValueError(f"Unknown research claim: {clean_id}")
    known_citations = {citation.id for citation in load_research_citations(profile)}
    next_claim = copy.deepcopy(claim)
    for attr, raw_refs, known in (
        ("source_refs", source_refs, set(_known_source_map(profile))),
        ("chunk_refs", chunk_refs, _known_chunk_ids(profile)),
        ("citation_refs", citation_refs, known_citations),
    ):
        if raw_refs is None:
            continue
        refs = _clean_list(raw_refs)
        missing = [ref for ref in refs if ref not in known]
        if missing:
            raise ValueError(f"Unknown research {attr}: {', '.join(missing)}")
        if replace:
            setattr(next_claim, attr, refs)
        elif remove:
            removal = set(refs)
            setattr(next_claim, attr, [ref for ref in getattr(next_claim, attr) if ref not in removal])
        else:
            merged = list(getattr(next_claim, attr))
            for ref in refs:
                _append_unique(merged, ref)
            setattr(next_claim, attr, merged)
    next_claim.updated = _now()
    _validate_claim_refs(profile, next_claim)
    claims = [next_claim if item.id == clean_id else item for item in claims]
    save_research_claims(profile, claims)
    return next_claim


def patch_research_claim(
    profile: str | Path,
    claim_id: str,
    *,
    text: object = None,
    status: object = None,
    type: object = None,
    confidence: object = None,
    rationale: object = None,
    human_note: object = None,
    warnings: object = None,
) -> ResearchClaim:
    """Patch editable claim fields while preserving unspecified values."""

    clean_id = _clean_text(claim_id)
    claims = load_research_claims(profile)
    claim = next((item for item in claims if item.id == clean_id), None)
    if claim is None:
        raise ValueError(f"Unknown research claim: {clean_id}")
    updated = copy.deepcopy(claim)
    if text is not None:
        updated.text = _clean_text(text)
        if not updated.text:
            raise ValueError("Research claim text cannot be blank.")
    if status is not None:
        clean_status = _choice(status, RESEARCH_CLAIM_STATUSES, "")
        if not clean_status:
            raise ValueError(f"Unknown research claim status: {status}")
        updated.status = clean_status
    if type is not None:
        clean_type = _choice(type, RESEARCH_CLAIM_TYPES, "")
        if not clean_type:
            raise ValueError(f"Unknown research claim type: {type}")
        updated.type = clean_type
    if confidence is not None:
        clean_confidence = _choice(confidence, ("low", "medium", "high"), "")
        if not clean_confidence:
            raise ValueError(f"Unknown research claim confidence: {confidence}")
        updated.confidence = clean_confidence
    if rationale is not None:
        updated.rationale = _clean_text(rationale)
    if human_note is not None:
        updated.human_note = bool(human_note)
    if warnings is not None:
        updated.warnings = _clean_list(warnings)
    updated.updated = _now()
    _validate_claim_refs(profile, updated)
    claims = [updated if item.id == clean_id else item for item in claims]
    save_research_claims(profile, claims)
    return updated


def create_citation_from_chunk(
    profile: str | Path,
    claim_id: str,
    chunk_id: str,
    *,
    quote: str = "",
    locator: str = "",
    note: str = "",
    bibliography: str = "",
) -> ResearchCitation:
    """Create a citation for a claim using a linked or selected chunk."""

    clean_chunk = _clean_text(chunk_id)
    chunk = next((item for item in load_chunks(profile) if item.id == clean_chunk), None)
    if chunk is None:
        raise ValueError(f"Unknown research chunk: {clean_chunk}")
    selected_quote = _clean_text(quote) or chunk.text
    selected_locator = _clean_text(locator) or chunk.locator
    return create_citation(
        profile,
        claim_id,
        source_id=chunk.source_id,
        chunk_id=chunk.id,
        locator=selected_locator,
        quote=selected_quote,
        bibliography=bibliography,
        note=note,
    )


def request_citation_for_claim(
    profile: str | Path,
    claim_id: str,
    *,
    note: str = "",
) -> ResearchClaim:
    """Mark a claim as needing citation work without creating fake evidence."""

    clean_note = _clean_text(note) or "Citation requested; bind a source chunk before public use."
    claim = next((item for item in load_research_claims(profile) if item.id == _clean_text(claim_id)), None)
    if claim is None:
        raise ValueError(f"Unknown research claim: {_clean_text(claim_id)}")
    warnings = list(claim.warnings)
    _append_unique(warnings, "citation_requested")
    rationale = f"{claim.rationale}\n{clean_note}".strip() if claim.rationale else clean_note
    return patch_research_claim(
        profile,
        claim.id,
        rationale=rationale,
        warnings=warnings,
    )


def verify_research_citations(
    profile: str | Path,
    refs: object = None,
) -> dict[str, Any]:
    """Verify a selected set of citations and return summary counts."""

    requested = set(_clean_list(refs))
    citations = load_research_citations(profile)
    selected = [citation for citation in citations if not requested or citation.id in requested]
    checks = [verify_research_citation(profile, citation.id) for citation in selected]
    return {
        "total": len(checks),
        "ok": sum(1 for check in checks if check.get("ok")),
        "warnings": sum(1 for check in checks if not check.get("ok")),
        "checks": checks,
    }


def duplicate_research_claim_groups(
    profile: str | Path,
) -> list[dict[str, Any]]:
    """Return exact-normalized duplicate claim groups for review."""

    groups: dict[str, list[ResearchClaim]] = {}
    for claim in load_research_claims(profile):
        key = _normalized_text(claim.text)
        if key:
            groups.setdefault(key, []).append(claim)
    return [
        {
            "text": claims[0].text,
            "claim_refs": [claim.id for claim in claims],
            "statuses": [claim.status for claim in claims],
        }
        for claims in groups.values()
        if len(claims) > 1
    ]


def merge_duplicate_research_claims(
    profile: str | Path,
    primary_claim_id: str,
    duplicate_claim_ids: object,
    *,
    rationale: str = "",
) -> ResearchClaim:
    """Merge duplicate claims into a primary claim and dismiss merged rows."""

    clean_primary = _clean_text(primary_claim_id)
    duplicate_ids = [ref for ref in _clean_list(duplicate_claim_ids) if ref != clean_primary]
    if not duplicate_ids:
        raise ValueError("At least one duplicate claim id is required.")
    claims = load_research_claims(profile)
    by_id = {claim.id: claim for claim in claims}
    primary = by_id.get(clean_primary)
    if primary is None:
        raise ValueError(f"Unknown primary research claim: {clean_primary}")
    missing = [ref for ref in duplicate_ids if ref not in by_id]
    if missing:
        raise ValueError(f"Unknown duplicate research claims: {', '.join(missing)}")
    updated_primary = copy.deepcopy(primary)
    merge_note = _clean_text(rationale) or f"Merged duplicate claims: {', '.join(duplicate_ids)}."
    for duplicate_id in duplicate_ids:
        duplicate = by_id[duplicate_id]
        for attr in ("source_refs", "chunk_refs", "citation_refs", "evidence_refs", "output_refs", "warnings"):
            merged = list(getattr(updated_primary, attr))
            for ref in getattr(duplicate, attr):
                _append_unique(merged, ref)
            setattr(updated_primary, attr, merged)
        if duplicate.human_note:
            updated_primary.human_note = True
    updated_primary.rationale = (
        f"{updated_primary.rationale}\n{merge_note}".strip()
        if updated_primary.rationale
        else merge_note
    )
    updated_primary.updated = _now()
    _validate_claim_refs(profile, updated_primary)
    next_claims: list[ResearchClaim] = []
    for claim in claims:
        if claim.id == clean_primary:
            next_claims.append(updated_primary)
            continue
        if claim.id in duplicate_ids:
            dismissed = copy.deepcopy(claim)
            dismissed.status = "dismissed"
            dismissed.rationale = (
                f"{dismissed.rationale}\nMerged into {clean_primary}."
                if dismissed.rationale
                else f"Merged into {clean_primary}."
            )
            dismissed.updated = _now()
            next_claims.append(dismissed)
            continue
        next_claims.append(claim)
    save_research_claims(profile, next_claims)
    return updated_primary


def build_research_claim_review_payload(
    profile: str | Path,
    *,
    source_id: str = "",
    status: str = "",
    queue: str = "",
) -> dict[str, Any]:
    """Build a review-board payload for source-aware claims and citations."""
    sources = _known_source_map(profile)
    chunks = {chunk.id: chunk for chunk in load_chunks(profile)}
    claims = {claim.id: claim for claim in load_research_claims(profile)}
    citations = {citation.id: citation for citation in load_research_citations(profile)}
    clean_source = _clean_text(source_id)
    clean_status = _clean_text(status)
    clean_queue = _clean_text(queue)
    source_chunks = [
        chunk
        for chunk in chunks.values()
        if not clean_source or chunk.source_id == clean_source
    ]
    quote_checks = {
        citation.id: _verify_citation_row(
            citation,
            claims=claims,
            chunks=chunks,
            sources=sources,
        )
        for citation in citations.values()
    }

    def claim_matches(claim: ResearchClaim) -> bool:
        if clean_status and claim.status != clean_status:
            return False
        if clean_source and clean_source not in _claim_source_refs(claim, chunks):
            return False
        claim_citations = [citations[ref] for ref in claim.citation_refs if ref in citations]
        checks = [quote_checks[citation.id] for citation in claim_citations]
        if clean_queue == "missing_citation" and claim_citations:
            return False
        if clean_queue == "quote_warning" and not any(not check.get("ok") for check in checks):
            return False
        if clean_queue == "ready" and claim.status != "ready":
            return False
        if clean_queue == "promoted" and claim.status != "promoted":
            return False
        return True

    chunk_cards: list[dict[str, Any]] = []
    for chunk in source_chunks:
        related_claims = [
            claim.id
            for claim in claims.values()
            if chunk.id in claim.chunk_refs
        ]
        related_citations = [
            citation.id
            for citation in citations.values()
            if citation.chunk_id == chunk.id
        ]
        chunk_cards.append(
            {
                "id": chunk.id,
                "source_id": chunk.source_id,
                "kind": chunk.kind,
                "title": chunk.title,
                "locator": chunk.locator,
                "text": chunk.text,
                "linked_claims": related_claims,
                "linked_citations": related_citations,
            }
        )

    claim_cards: list[dict[str, Any]] = []
    for claim in claims.values():
        if not claim_matches(claim):
            continue
        claim_citation_refs = [ref for ref in claim.citation_refs if ref in citations]
        checks = [quote_checks[ref] for ref in claim_citation_refs]
        citation_status = "missing"
        quote_status = "missing"
        if claim_citation_refs:
            citation_status = "verified" if checks and all(check.get("ok") for check in checks) else "weak"
            quote_status = "ok" if citation_status == "verified" else "warning"
        claim_cards.append(
            {
                "id": claim.id,
                "text": claim.text,
                "status": claim.status,
                "type": claim.type,
                "confidence": claim.confidence,
                "source_refs": _claim_source_refs(claim, chunks),
                "chunk_refs": list(claim.chunk_refs),
                "citation_refs": list(claim.citation_refs),
                "evidence_refs": list(claim.evidence_refs),
                "output_refs": list(claim.output_refs),
                "citation_status": citation_status,
                "quote_status": quote_status,
                "promote_ready": bool(claim.source_refs or claim.chunk_refs or claim.human_note),
                "human_note": bool(claim.human_note),
                "warnings": list(claim.warnings),
                "rationale": claim.rationale,
                "generated_by": claim.generated_by,
                "created": claim.created,
                "updated": claim.updated,
            }
        )

    citation_cards: list[dict[str, Any]] = []
    for citation in citations.values():
        chunk = chunks.get(citation.chunk_id)
        if clean_source and citation.source_id != clean_source and (
            chunk is None or chunk.source_id != clean_source
        ):
            continue
        citation_cards.append(
            {
                "id": citation.id,
                "claim_id": citation.claim_id,
                "source_id": citation.source_id,
                "chunk_id": citation.chunk_id,
                "locator": citation.locator,
                "quote": citation.quote,
                "url": citation.url,
                "bibliography": citation.bibliography,
                "note": citation.note,
                "quote_check": quote_checks[citation.id],
            }
        )

    duplicate_groups = []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for card in claim_cards:
        key = _normalized_text(card.get("text"))
        if key:
            grouped.setdefault(key, []).append(card)
    for cards in grouped.values():
        if len(cards) > 1:
            duplicate_groups.append(
                {
                    "text": cards[0].get("text"),
                    "claim_refs": [str(card.get("id")) for card in cards],
                    "statuses": [str(card.get("status")) for card in cards],
                }
            )

    return {
        "filters": {
            "source_id": clean_source,
            "status": clean_status,
            "queue": clean_queue,
        },
        "source": _source_card(sources.get(clean_source)),
        "summary": {
            "sources": len(sources),
            "chunks": len(chunk_cards),
            "claims": len(claim_cards),
            "citations": len(citation_cards),
            "ready_claims": sum(1 for claim in claims.values() if claim.status == "ready"),
            "promoted_claims": sum(1 for claim in claims.values() if claim.status == "promoted"),
            "missing_citation_claims": sum(1 for claim in claims.values() if not claim.citation_refs),
            "quote_warnings": sum(1 for check in quote_checks.values() if not check.get("ok")),
        },
        "chunk_cards": chunk_cards,
        "claim_cards": claim_cards,
        "citation_cards": citation_cards,
        "duplicate_claim_groups": duplicate_groups,
    }


def build_research_export_manifest(
    profile: str | Path,
    *,
    citation_refs: object = None,
    claim_refs: object = None,
    source_refs: object = None,
) -> dict[str, Any]:
    """Build a provenance and safety manifest before exporting research material."""
    sources = _known_source_map(profile)
    chunks = {chunk.id: chunk for chunk in load_chunks(profile)}
    claims = {claim.id: claim for claim in load_research_claims(profile)}
    citations = {citation.id: citation for citation in load_research_citations(profile)}
    selected_citations = _clean_list(citation_refs)
    selected_claims = _clean_list(claim_refs)
    selected_sources = _clean_list(source_refs)
    if not selected_citations and not selected_claims and not selected_sources:
        selected_citations = list(citations)
        selected_claims = list(claims)
    if selected_citations:
        for citation_id in selected_citations:
            citation = citations.get(citation_id)
            if citation is not None:
                _append_unique(selected_claims, citation.claim_id)
                _append_unique(selected_sources, citation.source_id)
                chunk = chunks.get(citation.chunk_id)
                if chunk is not None:
                    _append_unique(selected_sources, chunk.source_id)
    if selected_claims:
        for claim_id in selected_claims:
            claim = claims.get(claim_id)
            if claim is None:
                continue
            for source_ref in _claim_source_refs(claim, chunks):
                _append_unique(selected_sources, source_ref)
            for citation_ref in claim.citation_refs:
                _append_unique(selected_citations, citation_ref)
    private_source_refs = [
        ref for ref in selected_sources
        if sources.get(ref) is not None and sources[ref].visibility == "private"
    ]
    missing_source_refs = [ref for ref in selected_sources if ref and ref not in sources]
    missing_claim_refs = [ref for ref in selected_claims if ref and ref not in claims]
    missing_citation_refs = [ref for ref in selected_citations if ref and ref not in citations]
    broken_citation_refs = [
        ref for ref in selected_citations
        if ref in citations and not verify_research_citation(profile, ref).get("ok")
    ]
    unpromoted_claim_refs = [
        ref for ref in selected_claims
        if ref in claims and claims[ref].status != "promoted"
    ]
    blockers: list[dict[str, object]] = []
    for ref in private_source_refs:
        blockers.append({"kind": "private_source", "ref": ref})
    for ref in unpromoted_claim_refs:
        blockers.append({"kind": "unpromoted_research_claim", "ref": ref})
    for ref in broken_citation_refs:
        blockers.append({"kind": "broken_citation", "ref": ref})
    for kind, refs in (
        ("missing_source", missing_source_refs),
        ("missing_research_claim", missing_claim_refs),
        ("missing_citation", missing_citation_refs),
    ):
        for ref in refs:
            blockers.append({"kind": kind, "ref": ref})
    return {
        "source_refs": selected_sources,
        "claim_refs": selected_claims,
        "citation_refs": selected_citations,
        "private_source_refs": private_source_refs,
        "unpromoted_claim_refs": unpromoted_claim_refs,
        "broken_citation_refs": broken_citation_refs,
        "missing_source_refs": missing_source_refs,
        "missing_claim_refs": missing_claim_refs,
        "missing_citation_refs": missing_citation_refs,
        "publish_allowed": not blockers,
        "blockers": blockers,
        "sources": [_source_card(sources.get(ref)) for ref in selected_sources if ref in sources],
        "claims": [claims[ref].to_dict() for ref in selected_claims if ref in claims],
        "citations": [citations[ref].to_dict() for ref in selected_citations if ref in citations],
    }


def select_research_export_scope(
    profile: str | Path,
    scope: dict[str, object] | None = None,
) -> dict[str, Any]:
    """Select source/claim/citation refs for one export scope."""
    clean_scope = scope if isinstance(scope, dict) else {}
    sources = _known_source_map(profile)
    chunks = {chunk.id: chunk for chunk in load_chunks(profile)}
    claims = {claim.id: claim for claim in load_research_claims(profile)}
    citations = {citation.id: citation for citation in load_research_citations(profile)}
    source_refs = _clean_list(clean_scope.get("source_refs"))
    claim_refs = _clean_list(clean_scope.get("claim_refs"))
    citation_refs = _clean_list(clean_scope.get("citation_refs"))
    node_refs = set(
        _clean_list(
            clean_scope.get("library_node_refs")
            or clean_scope.get("library_node_ref")
        )
    )
    goal_refs = set(_clean_list(clean_scope.get("goal_refs") or clean_scope.get("goal_ref")))
    source_statuses = set(_clean_list(clean_scope.get("source_statuses") or clean_scope.get("source_status")))
    claim_statuses = set(_clean_list(clean_scope.get("claim_statuses") or clean_scope.get("claim_status")))
    tags = {tag.casefold() for tag in _clean_list(clean_scope.get("tags") or clean_scope.get("tag"))}
    source_filter = bool(source_refs or node_refs or goal_refs or source_statuses or tags)
    explicit_refs = bool(source_refs or claim_refs or citation_refs)

    def source_matches(source: ResearchSource) -> bool:
        if node_refs and not node_refs.intersection(source.library_node_refs):
            return False
        if goal_refs and not goal_refs.intersection(source.goal_refs):
            return False
        if source_statuses and source.status not in source_statuses:
            return False
        if tags and not tags.intersection(tag.casefold() for tag in source.tags):
            return False
        return True

    selected_sources: list[str] = []
    if source_refs:
        for ref in source_refs:
            _append_unique(selected_sources, ref)
    elif source_filter:
        for source in sources.values():
            if source_matches(source):
                _append_unique(selected_sources, source.id)
    elif not explicit_refs and not claim_statuses:
        for source in sources.values():
            _append_unique(selected_sources, source.id)

    selected_claims: list[str] = []
    for ref in claim_refs:
        _append_unique(selected_claims, ref)
    for claim in claims.values():
        if claim_refs and claim.id not in claim_refs:
            continue
        claim_sources = _claim_source_refs(claim, chunks)
        source_in_scope = not source_filter or any(ref in selected_sources for ref in claim_sources)
        if source_filter and not source_in_scope:
            continue
        if claim_statuses and claim.status not in claim_statuses:
            continue
        if citation_refs and not claim_refs and not source_filter and not claim_statuses:
            continue
        _append_unique(selected_claims, claim.id)
    for claim_id in selected_claims:
        claim = claims.get(claim_id)
        if claim is None:
            continue
        for ref in _claim_source_refs(claim, chunks):
            _append_unique(selected_sources, ref)

    selected_citations: list[str] = []
    for ref in citation_refs:
        _append_unique(selected_citations, ref)
    for citation in citations.values():
        chunk = chunks.get(citation.chunk_id)
        citation_sources = [citation.source_id]
        if chunk is not None:
            citation_sources.append(chunk.source_id)
        citation_source_scope = source_filter or (not explicit_refs and not claim_statuses)
        if citation.claim_id in selected_claims or (
            citation_source_scope
            and any(ref in selected_sources for ref in citation_sources if ref)
        ):
            _append_unique(selected_citations, citation.id)
    for citation_id in selected_citations:
        citation = citations.get(citation_id)
        if citation is None:
            continue
        _append_unique(selected_claims, citation.claim_id)
        _append_unique(selected_sources, citation.source_id)
        chunk = chunks.get(citation.chunk_id)
        if chunk is not None:
            _append_unique(selected_sources, chunk.source_id)

    return {
        "scope": {
            "source_refs": source_refs,
            "claim_refs": claim_refs,
            "citation_refs": citation_refs,
            "library_node_refs": sorted(node_refs),
            "goal_refs": sorted(goal_refs),
            "source_statuses": sorted(source_statuses),
            "claim_statuses": sorted(claim_statuses),
            "tags": sorted(tags),
        },
        "source_refs": selected_sources,
        "claim_refs": selected_claims,
        "citation_refs": selected_citations,
        "sources": [_source_card(sources.get(ref)) for ref in selected_sources if ref in sources],
    }


def build_research_export_payload(
    profile: str | Path,
    *,
    citation_refs: object = None,
    claim_refs: object = None,
    source_refs: object = None,
    scope: dict[str, object] | None = None,
) -> dict[str, Any]:
    """Build the synthesis/export read model for UI callers."""
    drafts = load_research_drafts(profile)
    selected = select_research_export_scope(profile, scope)
    selected_sources = _clean_list(source_refs) or selected["source_refs"]
    selected_claims = _clean_list(claim_refs) or selected["claim_refs"]
    selected_citations = _clean_list(citation_refs) or selected["citation_refs"]
    manifest = build_research_export_manifest(
        profile,
        citation_refs=selected_citations,
        claim_refs=selected_claims,
        source_refs=selected_sources,
    )
    return {
        "selection": selected,
        "manifest": manifest,
        "drafts": copy.deepcopy(drafts),
        "counts": {
            "drafts": len(drafts),
            "sources": len(manifest["source_refs"]),
            "claims": len(manifest["claim_refs"]),
            "citations": len(manifest["citation_refs"]),
            "blockers": len(manifest["blockers"]),
        },
    }


def _overview_paper_library_target(
    *,
    view: str = "",
    detail_id: str = "",
    node_id: str = "",
    query: str = "",
    sort: str = "",
    focus: str = "",
    action: str = "",
    return_to: str = "overview",
) -> dict[str, object]:
    """Return a structured Paper Library target for Overview navigation."""

    return {
        "surface": "paper_library",
        "view": _clean_text(view),
        "detail_id": _clean_text(detail_id),
        "node_id": _clean_text(node_id),
        "query": _clean_text(query),
        "sort": _clean_text(sort),
        "focus": _clean_text(focus),
        "action": _clean_text(action),
        "return_to": _clean_text(return_to),
    }


def _overview_reader_target(source_id: str) -> dict[str, object]:
    return {"surface": "reader", "source_id": _clean_text(source_id)}


def _overview_claims_target(
    *,
    source_id: str = "",
    status: str = "",
    queue: str = "",
    claim_refs: list[str] | None = None,
    citation_refs: list[str] | None = None,
) -> dict[str, object]:
    return {
        "surface": "claims",
        "source_id": _clean_text(source_id),
        "status": _clean_text(status),
        "queue": _clean_text(queue),
        "claim_refs": list(claim_refs or []),
        "citation_refs": list(citation_refs or []),
    }


def _overview_internal_target(surface: str, **values: object) -> dict[str, object]:
    target = {"surface": _clean_text(surface)}
    target.update({key: copy.deepcopy(value) for key, value in values.items()})
    return target


def build_research_overview_payload(profile: str | Path) -> dict[str, Any]:
    """Build an action-oriented Research Workspace overview payload."""
    inbox = load_research_sources(_profile_root(profile))
    sources = inbox.by_id()
    chunks = load_chunks(profile)
    claims = load_research_claims(profile)
    citations = load_research_citations(profile)
    drafts = load_research_drafts(profile)
    citation_checks = {
        citation.id: verify_research_citation(profile, citation.id)
        for citation in citations
    }
    ready_claims = [claim for claim in claims if claim.status == "ready"]
    promoted_claims = [claim for claim in claims if claim.status == "promoted"]
    chunks_by_id = {chunk.id: chunk for chunk in chunks}
    private_risk_refs: list[str] = []
    for claim in [*ready_claims, *promoted_claims]:
        for ref in _claim_source_refs(claim, chunks_by_id):
            source = sources.get(ref)
            if source is not None and source.visibility == "private":
                _append_unique(private_risk_refs, ref)
    broken_citation_refs = [
        citation_id
        for citation_id, check in citation_checks.items()
        if not check.get("ok")
    ]
    ready_claim_refs = [claim.id for claim in ready_claims]
    ready_claim_source_refs: list[str] = []
    for claim in ready_claims:
        for ref in _claim_source_refs(claim, chunks_by_id):
            _append_unique(ready_claim_source_refs, ref)
    broken_citation_source_refs: list[str] = []
    for citation in citations:
        if citation.id not in broken_citation_refs:
            continue
        if citation.source_id:
            _append_unique(broken_citation_source_refs, citation.source_id)
        chunk = chunks_by_id.get(citation.chunk_id)
        if chunk is not None:
            _append_unique(broken_citation_source_refs, chunk.source_id)
    recent_sources = sorted(
        inbox.sources,
        key=lambda source: _clean_text(
            (source.metadata or {}).get("last_read_at")
            or source.reading.updated_at
            or source.captured_at
        ),
        reverse=True,
    )[:8]
    reading_sources = [source for source in inbox.sources if source.status == "reading"]
    paper_rows_by_view: dict[str, list[dict[str, object]]] = {}
    paper_queue_specs = [
        ("reading", "Reading", "Continue", "reading", "open_reader", "live"),
        ("needs_extraction", "Needs extraction", "Parser status", "artifacts", "run_extraction", "risk"),
        ("no_pdf", "PDF missing", "Paper Library", "artifacts", "attach_pdf", "risk"),
        ("claims_need_review", "Claims review", "AI candidates", "claims", "review_claims", "live"),
        ("duplicate_risk", "Duplicate risk", "Deduplicate", "metadata", "dedupe", "risk"),
        ("stale_translation", "Stale translations", "Translation", "translations", "retry_translation", "risk"),
        ("private", "Private sources", "Visibility", "safety", "review_visibility", "risk"),
        ("recent", "Recently read", "Recent", "reading", "open_reader", "live"),
    ]
    try:
        from nblane.core.research_papers import paper_rows as _paper_rows

        for view_id, *_ in paper_queue_specs:
            paper_rows_by_view[view_id] = _paper_rows(profile, view=view_id)
        paper_rows_by_view["all"] = _paper_rows(profile, view="all")
    except Exception:
        paper_rows_by_view = {}

    def queue_detail(view_id: str) -> str:
        rows = paper_rows_by_view.get(view_id) or []
        return _clean_text(rows[0].get("id")) if rows else ""

    def queue_count(view_id: str) -> int:
        if view_id in paper_rows_by_view:
            return len(paper_rows_by_view[view_id])
        if view_id == "reading":
            return len([source for source in inbox.sources if source.kind == "paper" and source.status == "reading"])
        if view_id == "no_pdf":
            return len([source for source in inbox.sources if source.kind == "paper" and not (source.metadata or {}).get("pdf_asset_ref")])
        if view_id == "private":
            return len([source for source in inbox.sources if source.kind == "paper" and source.visibility == "private"])
        return 0

    work_queues = [
        {
            "id": view_id,
            "label": label,
            "caption": caption,
            "count": queue_count(view_id),
            "severity": severity if queue_count(view_id) else "neutral",
            "target": _overview_paper_library_target(
                view=view_id,
                detail_id=queue_detail(view_id),
                focus=focus,
                action=target_action,
            ),
        }
        for view_id, label, caption, focus, target_action, severity in paper_queue_specs
    ]

    next_actions: list[dict[str, object]] = []
    if reading_sources:
        reading_ref = reading_sources[0].id
        next_actions.append(
            {
                "kind": "continue_reading",
                "label": f"Continue reading {len(reading_sources)} source(s)",
                "count": len(reading_sources),
                "target_tab": "reader",
                "source_refs": [source.id for source in reading_sources[:5]],
                "target": _overview_reader_target(reading_ref),
                "secondary_targets": [
                    _overview_paper_library_target(
                        view="reading",
                        detail_id=reading_ref,
                        focus="reading",
                        action="open_reader",
                    )
                ],
            }
        )
    if ready_claims:
        source_ref = ready_claim_source_refs[0] if ready_claim_source_refs else ""
        next_actions.append(
            {
                "kind": "review_claims",
                "label": f"Review {len(ready_claims)} ready research claim(s)",
                "count": len(ready_claims),
                "target_tab": "claims",
                "filters": {"status": "ready"},
                "claim_refs": ready_claim_refs[:8],
                "source_refs": ready_claim_source_refs[:8],
                "target": _overview_claims_target(
                    source_id=source_ref,
                    status="ready",
                    queue="ready",
                    claim_refs=ready_claim_refs[:8],
                ),
                "secondary_targets": [
                    _overview_paper_library_target(
                        view="claims_need_review",
                        detail_id=source_ref,
                        focus="claims",
                        action="review_claims",
                    )
                ],
            }
        )
    if broken_citation_refs:
        source_ref = broken_citation_source_refs[0] if broken_citation_source_refs else ""
        next_actions.append(
            {
                "kind": "fix_citations",
                "label": f"Fix {len(broken_citation_refs)} citation warning(s)",
                "count": len(broken_citation_refs),
                "target_tab": "claims",
                "filters": {"queue": "quote_warning"},
                "citation_refs": broken_citation_refs,
                "source_refs": broken_citation_source_refs[:8],
                "target": _overview_claims_target(
                    source_id=source_ref,
                    queue="quote_warning",
                    citation_refs=broken_citation_refs,
                ),
                "secondary_targets": [
                    _overview_paper_library_target(
                        detail_id=source_ref,
                        focus="claims",
                        action="fix_citations",
                    )
                ],
            }
        )
    if private_risk_refs:
        private_paper_risk_refs = [
            ref for ref in private_risk_refs if sources.get(ref) is not None and sources[ref].kind == "paper"
        ]
        next_actions.append(
            {
                "kind": "review_private_publish_risk",
                "label": f"Review {len(private_risk_refs)} private source risk(s)",
                "count": len(private_risk_refs),
                "target_tab": "export",
                "source_refs": private_risk_refs,
                "target": _overview_internal_target(
                    "export",
                    focus="private_publish_risk",
                    source_refs=private_risk_refs,
                ),
                "secondary_targets": [
                    _overview_paper_library_target(
                        view="private",
                        detail_id=private_paper_risk_refs[0],
                        focus="safety",
                        action="review_visibility",
                    )
                ]
                if private_paper_risk_refs
                else [],
            }
        )
    if drafts:
        next_actions.append(
            {
                "kind": "review_drafts",
                "label": f"Review {len(drafts)} synthesis draft(s)",
                "count": len(drafts),
                "target_tab": "export",
                "draft_refs": [str(draft.get("id") or "") for draft in drafts[:8] if str(draft.get("id") or "")],
                "target": _overview_internal_target(
                    "export",
                    focus="drafts",
                    draft_refs=[str(draft.get("id") or "") for draft in drafts[:8] if str(draft.get("id") or "")],
                ),
            }
        )
    if not inbox.sources:
        next_actions.append(
            {
                "kind": "import_sources",
                "label": "Import papers, repos, or web sources",
                "target_tab": "advanced_connectors",
                "target": _overview_internal_target("advanced_connections", focus="connectors"),
                "secondary_targets": [_overview_paper_library_target(view="unsorted")],
            }
        )
    risks = []
    if private_risk_refs:
        risks.append(
            {
                "kind": "private_publish_risk",
                "refs": private_risk_refs,
                "action": "open_export_gate",
            }
        )
    if broken_citation_refs:
        risks.append(
            {
                "kind": "broken_citations",
                "refs": broken_citation_refs,
                "action": "open_citation_inspector",
            }
        )
    all_paper_rows = paper_rows_by_view.get("all") or []
    recent_work = [
        {
            "source": _source_card(source),
            "last_read": _clean_text((source.metadata or {}).get("last_read_at") or source.reading.updated_at),
            "next_action": "continue_reading" if source.status == "reading" else "review_source",
            "target": _overview_paper_library_target(
                detail_id=source.id,
                focus="reading" if source.status == "reading" else "metadata",
                action="open_reader" if (source.metadata or {}).get("pdf_asset_ref") else "review_metadata",
            ),
            "reader_target": _overview_reader_target(source.id)
            if (source.metadata or {}).get("pdf_asset_ref")
            else {},
        }
        for source in recent_sources
    ]
    pipeline = [
        {
            "id": "sources",
            "label": "Sources",
            "count": len(inbox.sources),
            "caption": "Source Inbox",
            "target": _overview_paper_library_target(view="all"),
        },
        {
            "id": "reading",
            "label": "Reading",
            "count": len(reading_sources),
            "caption": "Reader",
            "target": _overview_paper_library_target(
                view="reading",
                detail_id=queue_detail("reading"),
                focus="reading",
                action="open_reader",
            ),
        },
        {
            "id": "extracted",
            "label": "Extracted",
            "count": sum(1 for row in all_paper_rows if row.get("annotations_count") or row.get("chunks_count")),
            "caption": "Chunks / annotations",
            "target": _overview_paper_library_target(view="needs_extraction", focus="artifacts"),
        },
        {
            "id": "claims_ready",
            "label": "Claims ready",
            "count": len(ready_claims),
            "caption": "Review queue",
            "target": _overview_claims_target(status="ready", queue="ready", claim_refs=ready_claim_refs[:8]),
        },
        {
            "id": "citations",
            "label": "Citations",
            "count": len(citations),
            "caption": f"{len(broken_citation_refs)} warnings",
            "target": _overview_claims_target(queue="quote_warning", citation_refs=broken_citation_refs),
        },
        {
            "id": "drafts",
            "label": "Drafts",
            "count": len(drafts),
            "caption": "Synthesis / Export",
            "target": _overview_internal_target("export", focus="drafts"),
        },
    ]

    return {
        "profile": _profile_name(profile),
        "funnel_counts": {
            "sources": len(inbox.sources),
            "papers": sum(1 for source in inbox.sources if source.kind == "paper"),
            "reading": len(reading_sources),
            "chunks": len(chunks),
            "claims_draft": sum(1 for claim in claims if claim.status == "draft"),
            "claims_ready": len(ready_claims),
            "claims_promoted": len(promoted_claims),
            "citations": len(citations),
            "drafts": len(drafts),
        },
        "queues": {
            "inbox": sum(1 for source in inbox.sources if source.status == "inbox"),
            "candidate_ready": sum(1 for source in inbox.sources if source.status == "candidate_ready"),
            "archived": sum(1 for source in inbox.sources if source.status == "archived"),
            "discarded": sum(1 for source in inbox.sources if source.status == "discarded"),
            "private_sources": sum(1 for source in inbox.sources if source.visibility == "private"),
            "public_sources": sum(1 for source in inbox.sources if source.visibility == "public"),
        },
        "pipeline": pipeline,
        "work_queues": work_queues,
        "safety": {
            "private_sources": sum(1 for source in inbox.sources if source.visibility == "private"),
            "public_sources": sum(1 for source in inbox.sources if source.visibility == "public"),
            "citation_broken": len(broken_citation_refs),
            "private_publish_risk": len(private_risk_refs),
            "private_publish_risk_refs": private_risk_refs,
        },
        "next_actions": next_actions,
        "risks": risks,
        "recent_work": recent_work,
        "recent_activity": [
            {
                "source": _source_card(source),
                "last_read": _clean_text((source.metadata or {}).get("last_read_at") or source.reading.updated_at),
                "next_action": "continue_reading" if source.status == "reading" else "review_source",
            }
            for source in recent_sources
        ],
    }


def build_connector_inbox_payload(
    profile: str | Path,
    connector_id: str = "",
    dry_run_cache_id: str = "",
) -> dict[str, Any]:
    """Return connector configs and optional discovery preview for the Research UI."""
    from nblane.core.research_connectors import discover_connector_items, load_connectors

    book = load_connectors(profile)
    clean_id = _clean_text(connector_id)
    preview = discover_connector_items(profile, clean_id) if clean_id else {}
    return {
        "connectors": copy.deepcopy(book.get("connectors") or []),
        "selected_connector_id": clean_id,
        "dry_run_cache_id": _clean_text(dry_run_cache_id),
        "preview": preview,
    }


def validate_research_workspace(profile: str | Path) -> list[str]:
    """Return research workspace diagnostics."""
    diagnostics: list[str] = []
    sources = _known_source_map(profile)
    chunks = {chunk.id: chunk for chunk in load_chunks(profile)}
    claims = {claim.id: claim for claim in load_research_claims(profile)}
    citations = {citation.id: citation for citation in load_research_citations(profile)}
    for claim in claims.values():
        if not claim.source_refs and not claim.chunk_refs and not claim.human_note:
            diagnostics.append(f"{claim.id}: missing source_refs/chunk_refs or human_note")
        for ref in claim.source_refs:
            if ref not in sources:
                diagnostics.append(f"{claim.id}: unknown source ref {ref}")
        for ref in claim.chunk_refs:
            if ref not in chunks:
                diagnostics.append(f"{claim.id}: unknown chunk ref {ref}")
        for ref in claim.citation_refs:
            if ref not in citations:
                diagnostics.append(f"{claim.id}: unknown citation ref {ref}")
    for citation in citations.values():
        if citation.claim_id not in claims:
            diagnostics.append(f"{citation.id}: unknown claim ref {citation.claim_id}")
        if citation.source_id and citation.source_id not in sources:
            diagnostics.append(f"{citation.id}: unknown source ref {citation.source_id}")
        if citation.chunk_id and citation.chunk_id not in chunks:
            diagnostics.append(f"{citation.id}: unknown chunk ref {citation.chunk_id}")
    return diagnostics


__all__ = [
    "RESEARCH_CHUNKS_DIRNAME",
    "RESEARCH_CITATIONS_FILENAME",
    "RESEARCH_CLAIMS_FILENAME",
    "RESEARCH_DRAFTS_FILENAME",
    "RESEARCH_DRAFTS_DIRNAME",
    "RESEARCH_CLAIM_STATUSES",
    "RESEARCH_CLAIM_TYPES",
    "ResearchChunk",
    "ResearchClaim",
    "ResearchCitation",
    "build_connector_inbox_payload",
    "build_research_claim_review_payload",
    "build_research_export_manifest",
    "build_research_export_payload",
    "build_research_overview_payload",
    "build_synthesis_draft_review",
    "create_chunk",
    "create_citation",
    "create_citation_from_chunk",
    "duplicate_research_claim_groups",
    "draft_synthesis_from_claims",
    "load_chunks",
    "load_research_citations",
    "load_research_claims",
    "load_research_drafts",
    "merge_duplicate_research_claims",
    "patch_research_claim",
    "research_claim_to_evidence_candidate",
    "research_draft_to_output_candidates",
    "research_draft_to_blog_candidate",
    "research_draft_to_project_update_candidate",
    "research_draft_to_resume_bullet_candidates",
    "research_output_project_options",
    "request_citation_for_claim",
    "save_chunks",
    "save_research_citations",
    "save_research_claims",
    "save_research_drafts",
    "select_research_export_scope",
    "source_slug",
    "update_research_claim_links",
    "update_research_claim_status",
    "upsert_research_claim",
    "validate_research_workspace",
    "verify_research_citation",
    "verify_research_citations",
]
