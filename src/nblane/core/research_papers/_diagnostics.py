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
    PAPER_DIAGNOSTIC_BADGES,
    PAPER_DIAGNOSTIC_SEVERITIES,
)
from ._paths import _profile_root, _research_root
from ._types import PaperSegment
from ._utils import (
    _append_badge,
    _append_unique,
    _clean_list,
    _clean_text,
)
from ._io import (
    load_paper_annotations,
    load_paper_segments,
    load_paper_translations,
)
from ._library_tree import paper_library_paths, validate_paper_library
from nblane.core import research_papers as _pkg  # noqa: F401

def _duplicate_risk_refs(inbox: ResearchSourceInbox) -> dict[str, list[str]]:
    keys: dict[str, list[str]] = {}
    for source in inbox.sources:
        if source.kind != "paper":
            continue
        for key in _duplicate_keys_for_source(source):
            keys.setdefault(key, []).append(source.id)
    risks: dict[str, set[str]] = {}
    for ids in keys.values():
        unique = sorted(set(ids))
        if len(unique) < 2:
            continue
        for source_id in unique:
            risks.setdefault(source_id, set()).update(
                other for other in unique if other != source_id
            )
    return {source_id: sorted(refs) for source_id, refs in risks.items()}


def _normalized_quote_text(value: str) -> str:
    return re.sub(r"\s+", " ", _clean_text(value)).casefold()


def paper_citation_diagnostics(
    profile: str | Path,
    source_id: str = "",
) -> list[str]:
    """Return citation diagnostics that need paper-reading UI attention."""

    chunks = {chunk.id: chunk for chunk in load_chunks(_profile_root(profile))}
    diagnostics: list[str] = []
    clean_source = _clean_text(source_id)
    for citation in load_research_citations(_profile_root(profile)):
        chunk = chunks.get(citation.chunk_id)
        if clean_source and citation.source_id != clean_source and (
            chunk is None or chunk.source_id != clean_source
        ):
            continue
        if chunk is not None and citation.source_id and citation.source_id != chunk.source_id:
            diagnostics.append(
                f"{citation.id}: source {citation.source_id} does not match chunk source {chunk.source_id}"
            )
        if not citation.quote or chunk is None:
            continue
        quote = _normalized_quote_text(citation.quote)
        chunk_text = _normalized_quote_text(chunk.text)
        if quote and chunk_text and quote not in chunk_text:
            diagnostics.append(
                f"{citation.id}: quote does not match chunk {citation.chunk_id}"
            )
    return diagnostics


def _needs_structured_extraction(source: ResearchSource, segments: list[PaperSegment]) -> bool:
    metadata = source.metadata or {}
    if source.kind != "paper" or not metadata.get("pdf_asset_ref"):
        return False
    return not bool(segments)


def _metadata_has_grobid_unavailable(metadata: dict[str, object]) -> bool:
    status = _clean_text(metadata.get("grobid_status")).lower()
    if status == "unavailable" or metadata.get("grobid_available") is False:
        return True
    messages = _clean_list(metadata.get("structured_extraction_warnings")) + _clean_list(
        metadata.get("structured_extraction_notices")
    )
    return any(
        "grobid unavailable" in message.casefold() or "grobid 当前不可用" in message
        for message in messages
    )


def paper_source_diagnostics(
    profile: str | Path,
    source_id: str,
    *,
    grobid_status: dict[str, object] | None = None,
    inbox: ResearchSourceInbox | None = None,
    source: ResearchSource | None = None,
    workspace_diagnostics: list[str] | None = None,
    library_diagnostics: list[str] | None = None,
    duplicate_risk_refs: dict[str, list[str]] | None = None,
) -> dict[str, object]:
    """Return display-ready diagnostics and badges for one paper source."""

    if inbox is None:
        inbox = load_research_sources(_profile_root(profile))
    if source is None:
        source = inbox.by_id().get(source_id)
    if source is None:
        inbox, source = _source_by_id(profile, source_id)
    metadata = source.metadata or {}
    segments = load_paper_segments(profile, source.id) if source.kind == "paper" else []
    translations = load_paper_translations(profile, source.id) if source.kind == "paper" else []
    stale_translations = [row for row in translations if row.status == "stale"]
    all_workspace_diagnostics = (
        workspace_diagnostics
        if workspace_diagnostics is not None
        else validate_research_workspace(_profile_root(profile))
    )
    all_library_diagnostics = (
        library_diagnostics
        if library_diagnostics is not None
        else validate_paper_library(profile)
    )
    workspace_diagnostics = [
        item
        for item in all_workspace_diagnostics
        if source.id in item
    ]
    library_diagnostics = [
        item for item in all_library_diagnostics if source.id in item
    ]
    citation_diagnostics = [
        *workspace_diagnostics,
        *paper_citation_diagnostics(profile, source.id),
    ]
    duplicate_refs = (
        duplicate_risk_refs
        if duplicate_risk_refs is not None
        else _duplicate_risk_refs(inbox)
    ).get(source.id, [])
    needs_structured = _needs_structured_extraction(source, segments)
    badges: list[str] = []
    badge_details: list[dict[str, str]] = []
    warnings: list[str] = []

    for warning in _clean_list(metadata.get("structured_extraction_warnings")):
        _append_unique(warnings, warning)
    for translation in stale_translations:
        for warning in translation.warnings:
            _append_unique(warnings, warning)
    for diagnostic in [*citation_diagnostics, *library_diagnostics]:
        _append_unique(warnings, diagnostic)

    if needs_structured:
        _append_badge(
            badges,
            badge_details,
            "needs_structured_extraction",
            detail="No GROBID structured segments are available for this PDF.",
        )
    structure_backend = _clean_text(metadata.get("structure_backend"))
    if not needs_structured and segments and structure_backend and structure_backend != "grobid":
        fallback_detail = (
            "Reader text is ready from the PDF fallback extractor; GROBID upgrade is optional."
        )
        last_error = _clean_text(metadata.get("grobid_last_error"))
        if last_error:
            fallback_detail = f"{fallback_detail} Last GROBID attempt: {last_error}"
        _append_badge(
            badges,
            badge_details,
            "fallback_extraction",
            detail=fallback_detail,
        )
    if (
        grobid_status is not None
        and not bool(grobid_status.get("available"))
        and needs_structured
    ) or _metadata_has_grobid_unavailable(metadata):
        detail = _clean_text((grobid_status or {}).get("message")) or "GROBID is not available for structured extraction."
        _append_badge(badges, badge_details, "grobid_unavailable", detail=detail)
    if stale_translations:
        _append_badge(
            badges,
            badge_details,
            "stale_translation",
            detail=f"{len(stale_translations)} translation row(s) no longer match current segments.",
        )
    if citation_diagnostics or library_diagnostics:
        _append_badge(
            badges,
            badge_details,
            "citation_broken",
            detail="Citation, chunk, quote, or library references need repair.",
        )
    if source.visibility == "private":
        _append_badge(
            badges,
            badge_details,
            "private_source",
            detail="Private sources cannot be published directly.",
        )
    if duplicate_refs:
        _append_badge(
            badges,
            badge_details,
            "duplicate_risk",
            detail="Potential duplicate paper source(s): " + ", ".join(duplicate_refs),
        )

    return {
        "source_id": source.id,
        "badges": badges,
        "badge_details": badge_details,
        "warnings": warnings,
        "needs_structured_extraction": needs_structured,
        "stale_translation_count": len(stale_translations),
        "citation_diagnostics": citation_diagnostics,
        "library_diagnostics": library_diagnostics,
        "duplicate_source_refs": duplicate_refs,
        "grobid": copy.deepcopy(grobid_status) if grobid_status is not None else {},
    }


def paper_source_badges(
    profile: str | Path,
    source_id: str,
    *,
    grobid_status: dict[str, object] | None = None,
) -> list[str]:
    """Return only the badge labels for one paper source."""

    return list(
        paper_source_diagnostics(
            profile,
            source_id,
            grobid_status=grobid_status,
        )["badges"]
    )


def paper_diagnostics(
    profile: str | Path,
    *,
    include_grobid: bool = False,
) -> dict[str, object]:
    """Return profile-level Paper Reading diagnostics for UI surfaces."""

    inbox = load_research_sources(_profile_root(profile))
    grobid_status = _pkg.grobid_readiness() if include_grobid else None
    source_diagnostics = [
        paper_source_diagnostics(profile, source.id, grobid_status=grobid_status)
        for source in inbox.sources
        if source.kind == "paper"
    ]
    badge_counts: dict[str, int] = {}
    for diagnostic in source_diagnostics:
        for badge in diagnostic.get("badges") or []:
            label = _clean_text(badge)
            if label:
                badge_counts[label] = badge_counts.get(label, 0) + 1
    return {
        "grobid": copy.deepcopy(grobid_status) if grobid_status is not None else {},
        "sources": source_diagnostics,
        "badge_counts": badge_counts,
    }


def paper_rows(profile: str | Path, *, view: str = "all", node_id: str = "") -> list[dict[str, object]]:
    """Return display-ready Paper Library rows."""

    inbox = load_research_sources(_profile_root(profile))
    paths = paper_library_paths(profile)
    claims = load_research_claims(_profile_root(profile))
    citations = load_research_citations(_profile_root(profile))
    chunks = load_chunks(_profile_root(profile))
    workspace_diagnostics = validate_research_workspace(_profile_root(profile))
    library_diagnostics = validate_paper_library(profile)
    duplicate_risk_refs = _duplicate_risk_refs(inbox)
    claim_counts: dict[str, int] = {}
    citation_counts: dict[str, int] = {}
    chunk_counts: dict[str, int] = {}
    for chunk in chunks:
        chunk_counts[chunk.source_id] = chunk_counts.get(chunk.source_id, 0) + 1
    for claim in claims:
        for ref in claim.source_refs:
            claim_counts[ref] = claim_counts.get(ref, 0) + 1
    for citation in citations:
        if citation.source_id:
            citation_counts[citation.source_id] = citation_counts.get(citation.source_id, 0) + 1
    rows: list[dict[str, object]] = []
    for source in inbox.sources:
        is_paper = source.kind == "paper"
        if view == "other" and is_paper:
            continue
        if view != "other" and not is_paper:
            continue
        metadata = source.metadata or {}
        pdf_download_status = _clean_text(metadata.get("pdf_download_status"))
        pdf_download_error = _clean_text(metadata.get("pdf_download_error"))
        open_access_pdf_url = _clean_text(metadata.get("open_access_pdf_url") or metadata.get("pdf_url"))
        annotations = load_paper_annotations(profile, source.id) if is_paper else []
        translations = load_paper_translations(profile, source.id) if is_paper else []
        diagnostics = (
            paper_source_diagnostics(
                profile,
                source.id,
                inbox=inbox,
                source=source,
                workspace_diagnostics=workspace_diagnostics,
                library_diagnostics=library_diagnostics,
                duplicate_risk_refs=duplicate_risk_refs,
            )
            if is_paper
            else {"badges": []}
        )
        stale = any(row.status == "stale" for row in translations)
        refs = list(source.library_node_refs)
        row = {
            "id": source.id,
            "title": source.title,
            "tree_path": ", ".join(paths.get(ref, ref) for ref in refs) or "Unsorted",
            "status": source.status,
            "authors": ", ".join(source.authors),
            "published": source.published or _clean_text(metadata.get("year")),
            "venue": _clean_text(metadata.get("venue")),
            "tags": list(source.tags),
            "url": source.url or _clean_text(metadata.get("canonical_url") or metadata.get("pdf_url")),
            "open_access_pdf_url": open_access_pdf_url,
            "pdf_download_status": pdf_download_status,
            "pdf_download_error": pdf_download_error,
            "pdf_download_attempted_at": _clean_text(metadata.get("pdf_download_attempted_at")),
            "summary": source.summary or _clean_text(metadata.get("abstract")),
            "notes": source.notes,
            "has_pdf": bool(metadata.get("pdf_asset_ref")),
            "pdf_pages": metadata.get("page_count", ""),
            "last_read_page": metadata.get("last_read_page", ""),
            "annotations_count": len([ann for ann in annotations if ann.status == "active"]),
            "chunks_count": chunk_counts.get(source.id, 0),
            "claims_count": claim_counts.get(source.id, 0),
            "citations_count": citation_counts.get(source.id, 0),
            "last_read": _clean_text(metadata.get("last_read_at") or source.reading.updated_at),
            "visibility": source.visibility,
            "badges": [],
            "diagnostics": diagnostics,
            "source": source,
        }
        badges: list[str] = row["badges"]  # type: ignore[assignment]
        if is_paper and not refs:
            badges.append("Unsorted")
        if is_paper and not row["has_pdf"]:
            badges.append("PDF missing")
        if stale:
            badges.append("Stale translation")
        if source.visibility == "private":
            badges.append("Private source")
        if pdf_download_status == "downloading":
            badges.append("PDF downloading")
        if pdf_download_status in {
            "failed",
            "skipped_needs_link_check",
            "skipped_no_pdf_url",
        }:
            badges.append("PDF download warning")
        if source.reading.claim_candidates or source.status == "candidate_ready":
            badges.append("AI candidates")
        for badge in diagnostics.get("badges", []):  # type: ignore[union-attr]
            label = _clean_text(badge)
            if label and label not in badges:
                badges.append(label)
        badge_set = set(badges)
        match = True
        if view == "unsorted":
            match = is_paper and not refs
        elif view in {"reading", "archived", "discarded", "candidate_ready"}:
            match = source.status == view
        elif view == "annotated":
            match = bool(row["annotations_count"] or row["chunks_count"] or not source.reading.empty)
        elif view == "no_pdf":
            match = is_paper and not row["has_pdf"]
        elif view in {"needs_extraction", "ready_to_parse"}:
            match = (
                is_paper
                and bool(row["has_pdf"])
                and PAPER_DIAGNOSTIC_BADGES["needs_structured_extraction"] in badge_set
            )
        elif view in {"claims_need_review", "review_queue"}:
            match = source.status == "candidate_ready" or "AI candidates" in badge_set
        elif view == "duplicate_risk":
            match = PAPER_DIAGNOSTIC_BADGES["duplicate_risk"] in badge_set
        elif view == "stale_translation":
            match = "Stale translation" in badge_set or PAPER_DIAGNOSTIC_BADGES["stale_translation"] in badge_set
        elif view in {"recent", "recently_read"}:
            match = bool(row["last_read"])
        elif view == "private":
            match = source.visibility == "private"
        elif view in {"reviewed", "summarized"}:
            match = source.status == "summarized"
        if node_id and node_id not in refs:
            match = False
        if match:
            rows.append(row)
    return rows


def paper_overview(profile: str | Path) -> dict[str, object]:
    """Compute Overview metrics and integrity warnings."""

    inbox = load_research_sources(_profile_root(profile))
    papers = [source for source in inbox.sources if source.kind == "paper"]
    rows = paper_rows(profile)
    claims = load_research_claims(_profile_root(profile))
    ready_claims = [claim for claim in claims if claim.status == "ready"]
    promoted_claims = [claim for claim in claims if claim.status == "promoted"]
    stale_translations = 0
    for source in papers:
        stale_translations += sum(1 for row in load_paper_translations(profile, source.id) if row.status == "stale")
    workspace_diagnostics = validate_research_workspace(_profile_root(profile))
    library_diagnostics = validate_paper_library(profile)
    quote_diagnostics = paper_citation_diagnostics(_profile_root(profile))
    citation_broken = [
        item
        for item in [*workspace_diagnostics, *library_diagnostics]
        if "citation" in item or "chunk" in item or "source ref" in item or "library node" in item
    ] + quote_diagnostics
    source_diagnostics = [paper_source_diagnostics(profile, source.id) for source in papers]
    badge_counts: dict[str, int] = {}
    for diagnostic in source_diagnostics:
        for badge in diagnostic.get("badges") or []:
            label = _clean_text(badge)
            if label:
                badge_counts[label] = badge_counts.get(label, 0) + 1
    private_publish_risk = [
        source.id
        for source in papers
        if source.visibility == "private"
        and (
            source.evidence_refs
            or any(source.id in claim.source_refs and claim.status in {"ready", "promoted"} for claim in claims)
        )
    ]
    recent = sorted(
        rows,
        key=lambda row: str(row.get("last_read") or ""),
        reverse=True,
    )[:5]
    return {
        "papers_total": len(papers),
        "reading": sum(1 for source in papers if source.status == "reading"),
        "annotated": sum(1 for row in rows if row.get("annotations_count") or row.get("chunks_count")),
        "candidate_ready": sum(1 for source in papers if source.status == "candidate_ready" or source.reading.claim_candidates),
        "archived": sum(1 for source in papers if source.status == "archived"),
        "ready_research_claims": len(ready_claims),
        "promoted_research_claims": len(promoted_claims),
        "private_sources": sum(1 for source in papers if source.visibility == "private"),
        "public_sources": sum(1 for source in papers if source.visibility == "public"),
        "ai_candidates": sum(len(source.reading.claim_candidates) for source in papers),
        "citation_broken": len(citation_broken),
        "citation_diagnostics": citation_broken,
        "private_publish_risk": len(private_publish_risk),
        "private_publish_risk_refs": private_publish_risk,
        "stale_translation_warning": stale_translations,
        "needs_structured_extraction": badge_counts.get(
            PAPER_DIAGNOSTIC_BADGES["needs_structured_extraction"],
            0,
        ),
        "grobid_unavailable": badge_counts.get(
            PAPER_DIAGNOSTIC_BADGES["grobid_unavailable"],
            0,
        ),
        "duplicate_risk": badge_counts.get(
            PAPER_DIAGNOSTIC_BADGES["duplicate_risk"],
            0,
        ),
        "diagnostic_badge_counts": badge_counts,
        "source_diagnostics": source_diagnostics,
        "recent_papers": recent,
    }
