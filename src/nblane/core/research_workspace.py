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


def _research_root(profile: str | Path) -> Path:
    if isinstance(profile, Path):
        return profile / RESEARCH_DIRNAME if profile.name != RESEARCH_DIRNAME else profile
    return profile_dir(profile) / RESEARCH_DIRNAME


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
        lines = [f"# {clean_title}", ""]
        for claim_id in clean_claim_ids:
            claim = claims[claim_id]
            lines.append(f"- {claim.text}")
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
    row: dict[str, Any] = {
        "type": "learning" if claim.type in {"finding", "hypothesis"} else claim.type,
        "title": claim.text[:96],
        "summary": claim.text,
        "source_refs": list(claim.source_refs),
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
    draft = next((item for item in load_research_drafts(profile) if _clean_text(item.get("id")) == clean_id), None)
    if draft is None:
        raise ValueError(f"Unknown research draft: {clean_id}")
    body_path = _research_root(profile) / _clean_text(draft.get("body_path"))
    body = body_path.read_text(encoding="utf-8") if body_path.exists() else ""
    title = _clean_text(draft.get("title")) or clean_id
    claim_refs = _clean_list(draft.get("claim_refs"))
    source_refs = _clean_list(draft.get("source_refs"))
    citation_refs = _clean_list(draft.get("citation_refs"))
    return {
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
    "ResearchChunk",
    "ResearchClaim",
    "ResearchCitation",
    "create_chunk",
    "create_citation",
    "draft_synthesis_from_claims",
    "load_chunks",
    "load_research_citations",
    "load_research_claims",
    "load_research_drafts",
    "research_claim_to_evidence_candidate",
    "research_draft_to_blog_candidate",
    "save_chunks",
    "save_research_citations",
    "save_research_claims",
    "save_research_drafts",
    "source_slug",
    "upsert_research_claim",
    "validate_research_workspace",
]
