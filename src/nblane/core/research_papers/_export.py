"""Internal module for nblane.core.research_papers package."""

from __future__ import annotations

import copy
import base64
import contextlib
import difflib
import hashlib
from html import unescape
from html.parser import HTMLParser
import io
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from nblane.core import git_backup
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_io import profile_dir, validate_profile_name
from nblane.core.research_sources import (
    RESEARCH_DIRNAME,
    SOURCE_STATUSES,
    SOURCE_VISIBILITIES,
    ResearchSource,
    ResearchSourceInbox,
    add_research_source,
    load_research_sources,
    save_research_sources,
    update_research_source,
)
from nblane.core.research_workspace import (
    RESEARCH_CHUNKS_DIRNAME,
    ResearchCitation,
    ResearchChunk,
    load_chunks,
    load_research_citations,
    load_research_claims,
    save_chunks,
    source_slug,
    validate_research_workspace,
)
from nblane.core.yaml_io import _load_yaml_dict

try:
    import streamlit as st
except Exception:  # pragma: no cover - Streamlit is optional for core imports.
    st = None
from ._constants import (
    PAPER_ANALYSIS_DIRNAME,
    PAPER_EXPORTS_DIRNAME,
    PAPER_NOTES_DIRNAME,
)
from ._paths import (
    _jsonl_path,
    _md_path,
    _profile_root,
    _research_chunk_path,
    _research_root,
)
from ._types import PaperAnnotation, PaperLibraryNode
from ._utils import (
    _clean_list,
    _clean_mapping,
    _clean_text,
    _now,
    _slug,
    _today,
    text_hash,
)
from ._io import load_paper_annotations, load_paper_pages, load_paper_segments
from ._types import _published_year

def save_paper_note(profile: str | Path, source_id: str, body: str, *, metadata: dict[str, object] | None = None) -> Path:
    _source_by_id(profile, source_id)
    path = _md_path(profile, PAPER_NOTES_DIRNAME, source_id)
    front = {"source_id": source_id, **_clean_mapping(metadata)}
    text = "---\n" + yaml.dump(front, allow_unicode=True, sort_keys=False) + "---\n\n" + _clean_text(body) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, text)
    git_backup.record_change([path], action=f"update paper note for {source_id}")
    return path


def _bibtex_key(source: ResearchSource, year: str = "") -> str:
    author = _slug(source.authors[0].split()[-1] if source.authors else source.title.split()[0], fallback="paper")
    return f"{author}{year or _published_year(source.published) or 'nd'}"


def _bibliography_line(source: ResearchSource, citation: ResearchCitation | None = None) -> str:
    year = _published_year(source.published)
    authors = ", ".join(source.authors)
    venue = _clean_text((source.metadata or {}).get("venue"))
    url = source.url
    bits = [bit for bit in [authors, f"({year})" if year else "", source.title, venue, url] if bit]
    line = ". ".join(bits)
    if citation and citation.locator:
        line += f", {citation.locator}"
    return line


def format_research_citations(
    profile: str | Path,
    refs: list[str],
    *,
    format: str,
) -> str:
    """Format research citations without writing files."""

    clean_format = _clean_text(format).lower()
    if clean_format not in {"bibtex", "markdown", "md", "ris", "csl", "csl-json", "csl_json"}:
        raise ValueError("Citation export format must be bibtex, markdown, ris, or csl-json.")
    sources = load_research_sources(_profile_root(profile)).by_id()
    citations = {citation.id: citation for citation in load_research_citations(_profile_root(profile))}
    selected_refs = _clean_list(refs)
    selected = [citations[ref] for ref in selected_refs if ref in citations] if selected_refs else list(citations.values())
    if clean_format == "bibtex":
        entries: list[str] = []
        seen: set[str] = set()
        for citation in selected:
            source = sources.get(citation.source_id)
            if source is None:
                continue
            year = _published_year(source.published)
            key = _bibtex_key(source, year)
            if key in seen:
                key = f"{key}{len(seen) + 1}"
            seen.add(key)
            metadata = source.metadata or {}
            fields = {
                "title": source.title,
                "author": " and ".join(source.authors),
                "year": year,
                "url": source.url,
                "doi": _clean_text(metadata.get("doi")),
                "journal": _clean_text(metadata.get("venue")),
            }
            field_lines = [
                f"  {name} = {{{value}}}"
                for name, value in fields.items()
                if value
            ]
            entries.append("@article{" + key + ",\n" + ",\n".join(field_lines) + "\n}")
        return "\n\n".join(entries).strip() + ("\n" if entries else "")
    if clean_format == "ris":
        entries = []
        for citation in selected:
            source = sources.get(citation.source_id)
            if source is None:
                continue
            metadata = source.metadata or {}
            lines = ["TY  - JOUR"]
            if source.title:
                lines.append(f"TI  - {source.title}")
            for author in source.authors:
                lines.append(f"AU  - {author}")
            year = _published_year(source.published)
            if year:
                lines.append(f"PY  - {year}")
            venue = _clean_text(metadata.get("venue"))
            if venue:
                lines.append(f"JO  - {venue}")
            doi = _clean_text(metadata.get("doi"))
            if doi:
                lines.append(f"DO  - {doi}")
            if source.url:
                lines.append(f"UR  - {source.url}")
            if citation.locator:
                lines.append(f"SP  - {citation.locator}")
            if citation.quote:
                lines.append(f"N1  - {citation.quote}")
            lines.append("ER  -")
            entries.append("\n".join(lines))
        return "\n\n".join(entries).strip() + ("\n" if entries else "")
    if clean_format in {"csl", "csl-json", "csl_json"}:
        rows = []
        seen: set[str] = set()
        for citation in selected:
            source = sources.get(citation.source_id)
            if source is None:
                continue
            year = _published_year(source.published)
            key = _bibtex_key(source, year)
            if key in seen:
                key = f"{key}-{len(seen) + 1}"
            seen.add(key)
            metadata = source.metadata or {}
            row: dict[str, object] = {
                "id": key,
                "type": "article-journal" if source.kind == "paper" else "webpage",
                "title": source.title,
            }
            authors = []
            for author in source.authors:
                parts = [part for part in author.split() if part]
                if len(parts) >= 2:
                    authors.append({"given": " ".join(parts[:-1]), "family": parts[-1]})
                elif author:
                    authors.append({"literal": author})
            if authors:
                row["author"] = authors
            if year:
                row["issued"] = {"date-parts": [[int(year)]]}
            doi = _clean_text(metadata.get("doi"))
            venue = _clean_text(metadata.get("venue"))
            if doi:
                row["DOI"] = doi
            if venue:
                row["container-title"] = venue
            if source.url:
                row["URL"] = source.url
            if citation.locator or citation.quote:
                row["note"] = " ".join(
                    part for part in [citation.locator, citation.quote] if part
                )
            rows.append(row)
        return json.dumps(rows, ensure_ascii=False, indent=2) + ("\n" if rows else "")
    lines = ["# Research Bibliography", ""]
    for citation in selected:
        source = sources.get(citation.source_id)
        if source is None:
            continue
        lines.append(f"- {citation.id}: {_bibliography_line(source, citation)}")
        if citation.quote:
            lines.append(f"  Quote: {citation.quote}")
    return "\n".join(lines).rstrip() + "\n"


def save_research_export(
    profile: str | Path,
    body: str,
    *,
    format: str,
    prefix: str = "paper-export",
    manifest: dict[str, object] | None = None,
) -> Path:
    """Persist an explicit user-requested paper export."""

    clean_format = _clean_text(format).lower()
    ext = {
        "bibtex": "bib",
        "ris": "ris",
        "csl": "json",
        "csl-json": "json",
        "csl_json": "json",
    }.get(clean_format, "md")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = _research_root(profile) / PAPER_EXPORTS_DIRNAME / f"{_slug(prefix, fallback='export')}-{timestamp}.{ext}"
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, body if body.endswith("\n") else body + "\n")
    changed_paths = [path]
    if manifest is not None:
        manifest_path = path.with_name(f"{path.stem}.manifest.yaml")
        manifest_payload = {
            "schema_version": "1.0",
            "export_file": path.name,
            "created": _now(),
            **_clean_mapping(manifest),
        }
        atomic_write_text(
            manifest_path,
            yaml.dump(
                manifest_payload,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
        )
        changed_paths.append(manifest_path)
    git_backup.record_change(changed_paths, action=f"save research export {path.name}")
    return path


def create_reading_note_markdown(
    profile: str | Path,
    source_id: str,
    *,
    claim_refs: list[str] | None = None,
    chunk_refs: list[str] | None = None,
    citation_refs: list[str] | None = None,
) -> str:
    """Build a Markdown reading note from selected paper artifacts."""

    _, source = _source_by_id(profile, source_id)
    chunks = {chunk.id: chunk for chunk in load_chunks(_profile_root(profile), source_id)}
    claims = {claim.id: claim for claim in load_research_claims(_profile_root(profile))}
    citations = {citation.id: citation for citation in load_research_citations(_profile_root(profile))}
    lines = [f"# {source.title}", ""]
    if source.summary:
        lines.extend(["## Summary", "", source.summary, ""])
    chosen_chunks = [chunks[ref] for ref in _clean_list(chunk_refs) if ref in chunks]
    if chosen_chunks:
        lines.extend(["## Chunks", ""])
        for chunk in chosen_chunks:
            lines.append(f"- {chunk.locator or chunk.id}: {chunk.text}")
        lines.append("")
    chosen_claims = [claims[ref] for ref in _clean_list(claim_refs) if ref in claims]
    if chosen_claims:
        lines.extend(["## Claims", ""])
        for claim in chosen_claims:
            lines.append(f"- [{claim.status}] {claim.text}")
        lines.append("")
    chosen_citations = [citations[ref] for ref in _clean_list(citation_refs) if ref in citations]
    if chosen_citations:
        lines.extend(["## Citations", ""])
        for citation in chosen_citations:
            lines.append(f"- {citation.locator or citation.id}: {citation.quote or citation.bibliography}")
        lines.append("")
    lines.extend(["## Boundary", "", "Paper-reading evidence is weak evidence until reviewed against real project or goal facts."])
    return "\n".join(lines).rstrip() + "\n"


def create_reading_note_pack_markdown(
    profile: str | Path,
    source_ids: object,
    *,
    claim_refs: object = None,
    chunk_refs: object = None,
    citation_refs: object = None,
    title: str = "Research Reading Note Pack",
) -> str:
    """Build a multi-source Markdown reading note pack with scoped refs."""

    clean_sources = _clean_list(source_ids)
    if not clean_sources:
        raise ValueError("Reading note pack needs at least one source.")
    profile_path = _profile_root(profile)
    sources = load_research_sources(profile_path).by_id()
    missing = [ref for ref in clean_sources if ref not in sources]
    if missing:
        raise ValueError(f"Unknown research sources: {', '.join(missing)}")
    chunks = load_chunks(profile_path)
    claims = load_research_claims(profile_path)
    citations = load_research_citations(profile_path)
    wanted_claims = set(_clean_list(claim_refs))
    wanted_chunks = set(_clean_list(chunk_refs))
    wanted_citations = set(_clean_list(citation_refs))
    chunks_by_id = {chunk.id: chunk for chunk in chunks}
    lines = [
        f"# {_clean_text(title) or 'Research Reading Note Pack'}",
        "",
        "## Sources",
        "",
    ]
    for source_id in clean_sources:
        source = sources[source_id]
        lines.append(f"- {source.title} (`{source.id}`)")
    lines.extend(["", "---", ""])
    for index, source_id in enumerate(clean_sources, start=1):
        source_chunk_refs = [
            chunk.id
            for chunk in chunks
            if chunk.source_id == source_id
            and (not wanted_chunks or chunk.id in wanted_chunks)
        ]
        source_claim_refs = [
            claim.id
            for claim in claims
            if (
                source_id in claim.source_refs
                or any(
                    chunk_ref in chunks_by_id
                    and chunks_by_id[chunk_ref].source_id == source_id
                    for chunk_ref in claim.chunk_refs
                )
            )
            and (not wanted_claims or claim.id in wanted_claims)
        ]
        source_citation_refs = [
            citation.id
            for citation in citations
            if (
                citation.source_id == source_id
                or (
                    citation.chunk_id in chunks_by_id
                    and chunks_by_id[citation.chunk_id].source_id == source_id
                )
            )
            and (not wanted_citations or citation.id in wanted_citations)
        ]
        note = create_reading_note_markdown(
            profile_path,
            source_id,
            claim_refs=source_claim_refs,
            chunk_refs=source_chunk_refs,
            citation_refs=source_citation_refs,
        )
        lines.append(f"## {index}. {sources[source_id].title}")
        lines.append("")
        lines.append(note.strip())
        if index < len(clean_sources):
            lines.extend(["", "---", ""])
    return "\n".join(lines).rstrip() + "\n"


def auto_chunk_paper(
    profile: str | Path,
    source_id: str,
    *,
    overwrite: bool = False,
) -> list[ResearchChunk]:
    """Create citable chunks from paper segments for text-mode Reader workflows."""

    _source_by_id(profile, source_id)
    existing = load_chunks(_profile_root(profile), source_id)
    if existing and not overwrite:
        return existing
    segments = load_paper_segments(profile, source_id)
    chunks: list[ResearchChunk] = []
    for index, segment in enumerate(segments, start=1):
        if not segment.text.strip():
            continue
        chunks.append(
            ResearchChunk(
                id=f"chunk:{source_slug(source_id)}:{index:03d}",
                source_id=source_id,
                text=segment.text,
                kind="paragraph",
                locator=segment.locator,
                metadata={
                    "segment_id": segment.segment_id,
                    "source_hash": segment.text_hash,
                    "page": segment.page,
                    "rects": copy.deepcopy(segment.rects),
                },
            )
        )
    save_chunks(_profile_root(profile), source_id, chunks)
    return chunks
