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
    replace = _clean_text(mode) == "replace"
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


def build_research_export_payload(
    profile: str | Path,
    *,
    citation_refs: object = None,
    claim_refs: object = None,
    source_refs: object = None,
) -> dict[str, Any]:
    """Build the synthesis/export read model for UI callers."""
    drafts = load_research_drafts(profile)
    manifest = build_research_export_manifest(
        profile,
        citation_refs=citation_refs,
        claim_refs=claim_refs,
        source_refs=source_refs,
    )
    return {
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
    private_risk_refs: list[str] = []
    for claim in [*ready_claims, *promoted_claims]:
        for ref in _claim_source_refs(claim, {chunk.id: chunk for chunk in chunks}):
            source = sources.get(ref)
            if source is not None and source.visibility == "private":
                _append_unique(private_risk_refs, ref)
    broken_citation_refs = [
        citation_id
        for citation_id, check in citation_checks.items()
        if not check.get("ok")
    ]
    recent_sources = sorted(
        inbox.sources,
        key=lambda source: _clean_text(
            (source.metadata or {}).get("last_read_at")
            or source.reading.updated_at
            or source.captured_at
        ),
        reverse=True,
    )[:8]
    next_actions: list[dict[str, object]] = []
    reading_sources = [source for source in inbox.sources if source.status == "reading"]
    if reading_sources:
        next_actions.append(
            {
                "kind": "continue_reading",
                "label": f"Continue reading {len(reading_sources)} source(s)",
                "target_tab": "reader",
                "source_refs": [source.id for source in reading_sources[:5]],
            }
        )
    if ready_claims:
        next_actions.append(
            {
                "kind": "review_claims",
                "label": f"Review {len(ready_claims)} ready research claim(s)",
                "target_tab": "claims",
                "filters": {"status": "ready"},
            }
        )
    if broken_citation_refs:
        next_actions.append(
            {
                "kind": "fix_citations",
                "label": f"Fix {len(broken_citation_refs)} citation warning(s)",
                "target_tab": "claims",
                "filters": {"queue": "quote_warning"},
                "citation_refs": broken_citation_refs,
            }
        )
    if private_risk_refs:
        next_actions.append(
            {
                "kind": "review_private_publish_risk",
                "label": f"Review {len(private_risk_refs)} private source risk(s)",
                "target_tab": "export",
                "source_refs": private_risk_refs,
            }
        )
    if drafts:
        next_actions.append(
            {
                "kind": "review_drafts",
                "label": f"Review {len(drafts)} synthesis draft(s)",
                "target_tab": "export",
            }
        )
    if not inbox.sources:
        next_actions.append(
            {
                "kind": "import_sources",
                "label": "Import papers, repos, or web sources",
                "target_tab": "advanced_connectors",
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
        "next_actions": next_actions,
        "risks": risks,
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
    "ResearchChunk",
    "ResearchClaim",
    "ResearchCitation",
    "build_connector_inbox_payload",
    "build_research_claim_review_payload",
    "build_research_export_manifest",
    "build_research_export_payload",
    "build_research_overview_payload",
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
    "update_research_claim_links",
    "update_research_claim_status",
    "upsert_research_claim",
    "validate_research_workspace",
    "verify_research_citation",
]
