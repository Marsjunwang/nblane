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
    PAPER_ANNOTATION_KINDS,
    PAPER_ANNOTATION_STATUSES,
    PAPER_TRANSLATION_STATUSES,
    PAPER_TRANSLATION_SCOPES,
    PAPER_STRUCTURE_VERSION,
)
from ._utils import (
    _clean_text,
    _clean_list,
    _clean_mapping,
    _clean_bool,
    _choice,
    _now,
    _url_looks_like_pdf,
    text_hash,
)

class PaperImportError(ValueError):
    """User-facing error raised by paper import flows.

    The ``code`` attribute is a stable identifier that UIs can map to localized
    copy and recovery affordances (e.g. retry button, fix-link banner).
    """

    def __init__(self, message: str, *, code: str = "import_failed", retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class PaperDownloadError(PaperImportError):
    """Raised when downloading the open-access PDF fails."""

    def __init__(self, message: str, *, code: str = "pdf_download_failed", retryable: bool = True) -> None:
        super().__init__(message, code=code, retryable=retryable)


@dataclass
class PaperAsset:
    """External PDF asset metadata stored back onto a paper source."""

    source_id: str
    asset_ref: str
    sha256: str
    byte_size: int
    page_count: int = 0
    filename: str = ""
    pdf_url: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_metadata(self) -> dict[str, object]:
        data: dict[str, object] = {
            "pdf_asset_ref": self.asset_ref,
            "pdf_sha256": self.sha256,
            "pdf_byte_size": self.byte_size,
            "page_count": self.page_count,
        }
        if self.pdf_url:
            data["pdf_url"] = self.pdf_url
            data["open_access_pdf_url"] = self.pdf_url
        if self.filename:
            data["pdf_filename"] = self.filename
        if self.warnings:
            data["pdf_warnings"] = list(self.warnings)
        return data


@dataclass
class PaperPage:
    source_id: str
    page: int
    text: str = ""
    char_count: int = 0
    text_hash: str = ""
    extracted_at: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> "PaperPage | None":
        if not isinstance(data, dict):
            return None
        source_id = _clean_text(data.get("source_id"))
        try:
            page = int(data.get("page") or 0)
        except (TypeError, ValueError):
            page = 0
        if not source_id or page < 1:
            return None
        text = _clean_text(data.get("text"))
        return cls(
            source_id=source_id,
            page=page,
            text=text,
            char_count=int(data.get("char_count") or len(text)),
            text_hash=_clean_text(data.get("text_hash")) or text_hash(text),
            extracted_at=_clean_text(data.get("extracted_at")),
            metadata=_clean_mapping(data.get("metadata")),
        )

    def to_dict(self) -> dict[str, object]:
        text = _clean_text(self.text)
        data: dict[str, object] = {
            "source_id": self.source_id,
            "page": int(self.page),
            "text": text,
            "char_count": int(self.char_count or len(text)),
            "text_hash": self.text_hash or text_hash(text),
            "extracted_at": self.extracted_at or _now(),
        }
        if self.metadata:
            data["metadata"] = copy.deepcopy(self.metadata)
        return data


@dataclass
class PaperSegment:
    segment_id: str
    source_id: str
    page: int
    order: int
    text: str
    section_path: list[str] = field(default_factory=list)
    kind: str = "paragraph"
    text_hash: str = ""
    locator: str = ""
    rects: list[dict[str, object]] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> "PaperSegment | None":
        if not isinstance(data, dict):
            return None
        segment_id = _clean_text(data.get("segment_id"))
        source_id = _clean_text(data.get("source_id"))
        text = _clean_text(data.get("text"))
        if not segment_id or not source_id or not text:
            return None
        try:
            page = int(data.get("page") or 0)
            order = int(data.get("order") or 0)
        except (TypeError, ValueError):
            return None
        return cls(
            segment_id=segment_id,
            source_id=source_id,
            page=page,
            order=order,
            text=text,
            section_path=_clean_list(data.get("section_path")),
            kind=_clean_text(data.get("kind")) or "paragraph",
            text_hash=_clean_text(data.get("text_hash")) or text_hash(text),
            locator=_clean_text(data.get("locator")),
            rects=[
                copy.deepcopy(row)
                for row in data.get("rects") or []
                if isinstance(row, dict)
            ],
            metadata=_clean_mapping(data.get("metadata")),
        )

    def to_dict(self) -> dict[str, object]:
        text = _clean_text(self.text)
        data: dict[str, object] = {
            "segment_id": self.segment_id,
            "source_id": self.source_id,
            "page": int(self.page),
            "order": int(self.order),
            "section_path": list(self.section_path),
            "kind": self.kind or "paragraph",
            "text": text,
            "text_hash": self.text_hash or text_hash(text),
            "locator": self.locator or f"p. {self.page}",
            "rects": copy.deepcopy(self.rects),
        }
        if self.metadata:
            data["metadata"] = copy.deepcopy(self.metadata)
        return data


@dataclass
class PaperStructureUnit:
    unit_id: str
    source_id: str
    kind: str
    page_start: int
    page_end: int
    order: int
    text: str
    text_hash: str = ""
    section_path: list[str] = field(default_factory=list)
    locator: str = ""
    rects: list[dict[str, object]] = field(default_factory=list)
    source_unit_ids: list[str] = field(default_factory=list)
    translatable: bool = True
    display_source: bool = False
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> "PaperStructureUnit | None":
        if not isinstance(data, dict):
            return None
        unit_id = _clean_text(data.get("unit_id"))
        source_id = _clean_text(data.get("source_id"))
        text = _clean_text(data.get("text") or data.get("source_text"))
        if not unit_id or not source_id or not text:
            return None
        try:
            page_start = int(data.get("page_start") or data.get("page") or 0)
            page_end = int(data.get("page_end") or page_start)
            order = int(data.get("order") or 0)
        except (TypeError, ValueError):
            return None
        if page_start < 1 or page_end < page_start:
            return None
        metadata = _clean_mapping(data.get("metadata"))
        translatable = _metadata_bool(
            {"value": data.get("translatable")},
            "value",
            default=True,
        )
        display_source = _metadata_bool(
            {"value": data.get("display_source")},
            "value",
            default=not translatable,
        )
        return cls(
            unit_id=unit_id,
            source_id=source_id,
            kind=_clean_text(data.get("kind")) or "paragraph",
            page_start=page_start,
            page_end=page_end,
            order=order,
            text=text,
            text_hash=_clean_text(data.get("text_hash")) or text_hash(text),
            section_path=_clean_list(data.get("section_path")),
            locator=_clean_text(data.get("locator")) or (
                f"p. {page_start}" if page_start == page_end else f"pp. {page_start}-{page_end}"
            ),
            rects=[
                copy.deepcopy(row)
                for row in data.get("rects") or []
                if isinstance(row, dict)
            ],
            source_unit_ids=_clean_list(data.get("source_unit_ids")),
            translatable=translatable,
            display_source=display_source,
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, object]:
        text = _clean_text(self.text)
        metadata = copy.deepcopy(self.metadata)
        metadata.setdefault("structure_version", PAPER_STRUCTURE_VERSION)
        data: dict[str, object] = {
            "unit_id": self.unit_id,
            "source_id": self.source_id,
            "kind": self.kind or "paragraph",
            "page_start": int(self.page_start),
            "page_end": int(self.page_end or self.page_start),
            "order": int(self.order),
            "text": text,
            "text_hash": self.text_hash or text_hash(text),
            "section_path": list(self.section_path),
            "locator": self.locator
            or (f"p. {self.page_start}" if self.page_start == self.page_end else f"pp. {self.page_start}-{self.page_end}"),
            "rects": copy.deepcopy(self.rects),
            "source_unit_ids": list(self.source_unit_ids),
            "translatable": bool(self.translatable),
            "display_source": bool(self.display_source),
        }
        if metadata:
            data["metadata"] = metadata
        return data


@dataclass
class GrobidDocument:
    source_id: str
    tei_xml: str
    generated_at: str = ""


@dataclass
class PaperAnnotation:
    id: str
    source_id: str
    kind: str = "highlight"
    page: int = 0
    locator: str = ""
    selected_text: str = ""
    selected_text_hash: str = ""
    note: str = ""
    color: str = "yellow"
    rects: list[dict[str, object]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    chunk_refs: list[str] = field(default_factory=list)
    segment_refs: list[str] = field(default_factory=list)
    status: str = "active"
    created: str = ""
    updated: str = ""

    @classmethod
    def from_dict(cls, data: object) -> "PaperAnnotation | None":
        if not isinstance(data, dict):
            return None
        ann_id = _clean_text(data.get("id"))
        source_id = _clean_text(data.get("source_id"))
        if not ann_id or not source_id:
            return None
        selected = _clean_text(data.get("selected_text"))
        try:
            page = int(data.get("page") or 0)
        except (TypeError, ValueError):
            page = 0
        return cls(
            id=ann_id,
            source_id=source_id,
            kind=_choice(data.get("kind"), PAPER_ANNOTATION_KINDS, "highlight"),
            page=page,
            locator=_clean_text(data.get("locator")),
            selected_text=selected,
            selected_text_hash=_clean_text(data.get("selected_text_hash")) or text_hash(selected),
            note=_clean_text(data.get("note")),
            color=_clean_text(data.get("color")) or "yellow",
            rects=[copy.deepcopy(row) for row in data.get("rects") or [] if isinstance(row, dict)],
            tags=_clean_list(data.get("tags")),
            chunk_refs=_clean_list(data.get("chunk_refs")),
            segment_refs=_clean_list(data.get("segment_refs")),
            status=_choice(data.get("status"), PAPER_ANNOTATION_STATUSES, "active"),
            created=_clean_text(data.get("created")),
            updated=_clean_text(data.get("updated")),
        )

    def to_dict(self) -> dict[str, object]:
        selected = _clean_text(self.selected_text)
        return {
            "id": self.id,
            "source_id": self.source_id,
            "kind": self.kind,
            "page": int(self.page),
            "locator": self.locator or (f"p. {self.page}" if self.page else ""),
            "selected_text": selected,
            "selected_text_hash": self.selected_text_hash or text_hash(selected),
            "note": self.note,
            "color": self.color or "yellow",
            "rects": copy.deepcopy(self.rects),
            "tags": list(self.tags),
            "chunk_refs": list(self.chunk_refs),
            "segment_refs": list(self.segment_refs),
            "status": self.status or "active",
            "created": self.created or _now(),
            "updated": self.updated or self.created or _now(),
        }


@dataclass
class PaperTranslation:
    id: str
    source_id: str
    scope_type: str = "segment"
    scope_ref: str = ""
    segment_id: str = ""
    page: int = 0
    order: int = 0
    anchor_id: str = ""
    locator: str = ""
    source_hash: str = ""
    source_text: str = ""
    target_lang: str = "zh"
    translated_text: str = ""
    rects: list[dict[str, object]] = field(default_factory=list)
    glossary: dict[str, object] = field(default_factory=dict)
    generated_by: str = ""
    status: str = "translated"
    status_reason: str = ""
    warnings: list[str] = field(default_factory=list)
    created: str = ""

    @classmethod
    def from_dict(cls, data: object) -> "PaperTranslation | None":
        if not isinstance(data, dict):
            return None
        tr_id = _clean_text(data.get("id"))
        source_id = _clean_text(data.get("source_id"))
        if not tr_id or not source_id:
            return None
        try:
            page = int(data.get("page") or 0)
        except (TypeError, ValueError):
            page = 0
        try:
            order = int(data.get("order") or 0)
        except (TypeError, ValueError):
            order = 0
        return cls(
            id=tr_id,
            source_id=source_id,
            scope_type=_clean_text(data.get("scope_type")) or "segment",
            scope_ref=_clean_text(data.get("scope_ref")),
            segment_id=_clean_text(data.get("segment_id")),
            page=page,
            order=order,
            anchor_id=_clean_text(data.get("anchor_id")),
            locator=_clean_text(data.get("locator")),
            source_hash=_clean_text(data.get("source_hash")),
            source_text=_clean_text(data.get("source_text")),
            target_lang=_clean_text(data.get("target_lang")) or "zh",
            translated_text=translation_text_from_row(data),
            rects=[copy.deepcopy(row) for row in data.get("rects") or [] if isinstance(row, dict)],
            glossary=_clean_mapping(data.get("glossary")),
            generated_by=_clean_text(data.get("generated_by")),
            status=_choice(data.get("status"), PAPER_TRANSLATION_STATUSES, "translated"),
            status_reason=_clean_text(data.get("status_reason")),
            warnings=_clean_list(data.get("warnings")),
            created=_clean_text(data.get("created")),
        )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "id": self.id,
            "source_id": self.source_id,
            "scope_type": self.scope_type or "segment",
            "scope_ref": self.scope_ref,
            "segment_id": self.segment_id,
            "page": int(self.page),
            "order": int(self.order),
            "anchor_id": self.anchor_id,
            "locator": self.locator,
            "source_hash": self.source_hash,
            "source_text": self.source_text,
            "target_lang": self.target_lang or "zh",
            "translated_text": self.translated_text,
            "rects": copy.deepcopy(self.rects),
            "glossary": copy.deepcopy(self.glossary),
            "generated_by": self.generated_by,
            "status": self.status or "translated",
            "status_reason": self.status_reason,
            "warnings": list(self.warnings),
            "created": self.created or _now(),
        }
        return data


TRANSLATION_TEXT_KEYS = ("translated_text", "translation", "target_text", "target", "text")


def translation_text_from_row(data: object) -> str:
    """Return translated text from standard or provider-drifted translation rows."""

    if isinstance(data, PaperTranslation):
        return _clean_text(data.translated_text)
    if not isinstance(data, dict):
        return ""
    for key in TRANSLATION_TEXT_KEYS:
        clean = _clean_text(data.get(key))
        if clean:
            return clean
    return ""


def normalize_translation_row(
    data: object,
    *,
    source_id: str = "",
    target_lang: str = "",
) -> dict[str, Any]:
    """Normalize accepted AI translation rows before validation or storage."""

    raw = data.to_dict() if isinstance(data, PaperTranslation) else copy.deepcopy(data)
    if not isinstance(raw, dict):
        return {}
    translated_text = translation_text_from_row(raw)
    if translated_text:
        raw["translated_text"] = translated_text
    raw["source_hash"] = (
        _clean_text(raw.get("source_hash"))
        or _clean_text(raw.get("text_hash"))
        or _clean_text(raw.get("source_text_hash"))
    )
    clean_source_id = _clean_text(source_id)
    if clean_source_id and not _clean_text(raw.get("source_id")):
        raw["source_id"] = clean_source_id
    clean_lang = _clean_text(target_lang)
    if clean_lang and not _clean_text(raw.get("target_lang")):
        raw["target_lang"] = clean_lang
    return raw


def _translation_from_input(
    data: object,
    *,
    source_id: str,
    fallback_id: str = "",
) -> PaperTranslation | None:
    """Normalize accepted AI translation rows that may not have storage ids."""

    if isinstance(data, PaperTranslation):
        return data
    if not isinstance(data, dict):
        return None
    raw = normalize_translation_row(data, source_id=source_id)
    raw["id"] = _clean_text(raw.get("id")) or fallback_id or "pending"
    raw["source_id"] = _clean_text(raw.get("source_id")) or source_id
    return PaperTranslation.from_dict(raw)


def _metadata_bool(metadata: dict[str, object], key: str, default: bool = False) -> bool:
    value = metadata.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        clean = value.strip().lower()
        if clean in {"1", "true", "yes", "on"}:
            return True
        if clean in {"0", "false", "no", "off"}:
            return False
    if value is None:
        return default
    return bool(value)


@dataclass
class PaperLibraryNode:
    id: str
    title: str
    parent_id: str = ""
    description: str = ""
    color: str = ""
    icon: str = ""
    order: int = 0
    status: str = "active"
    created_by: str = "user"
    project_refs: list[str] = field(default_factory=list)
    goal_refs: list[str] = field(default_factory=list)
    trashed_at: str = ""
    trashed_from_parent_id: str = ""
    trashed_from_order: int | None = None

    @classmethod
    def from_dict(cls, data: object) -> "PaperLibraryNode | None":
        if not isinstance(data, dict):
            return None
        node_id = _clean_text(data.get("id"))
        title = _clean_text(data.get("title"))
        if not node_id or not title:
            return None
        try:
            order = int(data.get("order") or 0)
        except (TypeError, ValueError):
            order = 0
        trashed_from_order = data.get("trashed_from_order")
        try:
            clean_trashed_from_order = int(trashed_from_order) if trashed_from_order not in (None, "") else None
        except (TypeError, ValueError):
            clean_trashed_from_order = None
        return cls(
            id=node_id,
            title=title,
            parent_id=_clean_text(data.get("parent_id")),
            description=_clean_text(data.get("description")),
            color=_clean_text(data.get("color")),
            icon=_clean_text(data.get("icon")),
            order=order,
            status=_clean_text(data.get("status")) or "active",
            created_by=_clean_text(data.get("created_by")) or "user",
            project_refs=_clean_list(data.get("project_refs")),
            goal_refs=_clean_list(data.get("goal_refs")),
            trashed_at=_clean_text(data.get("trashed_at")),
            trashed_from_parent_id=_clean_text(data.get("trashed_from_parent_id")),
            trashed_from_order=clean_trashed_from_order,
        )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "id": self.id,
            "title": self.title,
            "parent_id": self.parent_id,
            "description": self.description,
            "color": self.color,
            "order": int(self.order),
            "status": self.status or "active",
            "created_by": self.created_by or "user",
        }
        if self.icon:
            data["icon"] = self.icon
        if self.project_refs:
            data["project_refs"] = list(self.project_refs)
        if self.goal_refs:
            data["goal_refs"] = list(self.goal_refs)
        if self.trashed_at:
            data["trashed_at"] = self.trashed_at
        if self.trashed_from_parent_id:
            data["trashed_from_parent_id"] = self.trashed_from_parent_id
        if self.trashed_from_order is not None:
            data["trashed_from_order"] = int(self.trashed_from_order)
        return data


@dataclass
class PaperLibraryTree:
    profile: str = ""
    updated: str = ""
    schema_version: str = "1.0"
    nodes: list[PaperLibraryNode] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: object) -> "PaperLibraryTree":
        if not isinstance(data, dict):
            return cls()
        nodes = []
        for item in data.get("nodes") or []:
            node = PaperLibraryNode.from_dict(item)
            if node is not None:
                nodes.append(node)
        return cls(
            profile=_clean_text(data.get("profile")),
            updated=_clean_text(data.get("updated")),
            schema_version=_clean_text(data.get("schema_version")) or "1.0",
            nodes=nodes,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version or "1.0",
            "profile": self.profile,
            "updated": self.updated,
            "nodes": [node.to_dict() for node in sorted(self.nodes, key=lambda n: (n.parent_id, n.order, n.title))],
        }

    def by_id(self) -> dict[str, PaperLibraryNode]:
        return {node.id: node for node in self.nodes}


@dataclass
class PaperSearchResult:
    title: str
    authors: list[str] = field(default_factory=list)
    year: str = ""
    venue: str = ""
    abstract: str = ""
    doi: str = ""
    arxiv_id: str = ""
    semantic_scholar_id: str = ""
    canonical_url: str = ""
    pdf_url: str = ""
    open_access_pdf: bool = False
    provider_refs: list[str] = field(default_factory=list)
    why_relevant: str = ""
    ai_summary: str = ""
    explanation_links: list[dict[str, str]] = field(default_factory=list)
    link_check: dict[str, object] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    suggested_library_nodes: list[dict[str, object]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    citation_count: int | None = None
    fields_of_study: list[str] = field(default_factory=list)
    imported_source_id: str = ""
    needs_link_check: bool = False
    candidate_id: str = ""

    @classmethod
    def from_dict(cls, data: object) -> "PaperSearchResult | None":
        if not isinstance(data, dict):
            return None
        title = _clean_text(data.get("title"))
        if not title:
            return None
        canonical_url = _clean_text(data.get("canonical_url") or data.get("url"))
        pdf_url = _clean_text(data.get("pdf_url") or data.get("open_access_pdf_url"))
        if not pdf_url and _url_looks_like_pdf(canonical_url):
            pdf_url = canonical_url
        citation_count = data.get("citation_count") or data.get("citations")
        try:
            citation_value = int(citation_count) if citation_count not in (None, "") else None
        except (TypeError, ValueError):
            citation_value = None
        result = cls(
            title=title,
            authors=_clean_list(data.get("authors")),
            year=_clean_text(data.get("year") or data.get("published"))[:4],
            venue=_clean_text(data.get("venue")),
            abstract=_clean_text(data.get("abstract") or data.get("summary")),
            doi=_clean_text(data.get("doi")),
            arxiv_id=_clean_text(data.get("arxiv_id")),
            semantic_scholar_id=_clean_text(data.get("semantic_scholar_id") or data.get("paper_id")),
            canonical_url=canonical_url,
            pdf_url=pdf_url,
            open_access_pdf=bool(data.get("open_access_pdf") or pdf_url),
            provider_refs=_clean_list(data.get("provider_refs") or data.get("providers")),
            why_relevant=_clean_text(data.get("why_relevant") or data.get("reason")),
            ai_summary=_clean_text(
                data.get("ai_summary")
                or data.get("ai_overview")
                or data.get("plain_language_summary")
                or data.get("llm_summary")
            ),
            explanation_links=_paper_explanation_links(data.get("explanation_links") or data.get("reading_links") or data.get("explainers")),
            link_check=_clean_mapping(data.get("link_check")),
            warnings=_clean_list(data.get("warnings")),
            suggested_library_nodes=[
                copy.deepcopy(row)
                for row in data.get("suggested_library_nodes") or []
                if isinstance(row, dict)
            ],
            tags=_clean_list(data.get("tags") or data.get("categories") or data.get("fields_of_study")),
            citation_count=citation_value,
            fields_of_study=_clean_list(data.get("fields_of_study")),
            imported_source_id=_clean_text(data.get("imported_source_id")),
            needs_link_check=bool(data.get("needs_link_check")),
            candidate_id=_clean_text(data.get("candidate_id")),
        )
        result.candidate_id = result.candidate_id or result.fingerprint()[:16]
        return result

    def fingerprint(self) -> str:
        seed = "|".join(
            [
                self.doi.lower(),
                self.arxiv_id.lower(),
                self.semantic_scholar_id.lower(),
                _canonical_url(self.canonical_url),
                self.title.lower(),
                self.year,
            ]
        )
        return hashlib.sha1(seed.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "candidate_id": self.candidate_id or self.fingerprint()[:16],
            "title": self.title,
            "authors": list(self.authors),
            "year": self.year,
            "venue": self.venue,
            "abstract": self.abstract,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "semantic_scholar_id": self.semantic_scholar_id,
            "canonical_url": self.canonical_url,
            "pdf_url": self.pdf_url,
            "open_access_pdf": bool(self.open_access_pdf),
            "provider_refs": list(self.provider_refs),
            "why_relevant": self.why_relevant,
            "ai_summary": self.ai_summary,
            "explanation_links": copy.deepcopy(self.explanation_links),
            "link_check": copy.deepcopy(self.link_check),
            "warnings": list(self.warnings),
            "suggested_library_nodes": copy.deepcopy(self.suggested_library_nodes),
            "tags": list(self.tags),
            "fields_of_study": list(self.fields_of_study),
            "imported_source_id": self.imported_source_id,
            "needs_link_check": bool(self.needs_link_check),
        }
        if self.citation_count is not None:
            data["citation_count"] = self.citation_count
        return data

    def source_metadata(self) -> dict[str, object]:
        data: dict[str, object] = {
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "semantic_scholar_id": self.semantic_scholar_id,
            "venue": self.venue,
            "citation_count": self.citation_count if self.citation_count is not None else "",
            "fields_of_study": list(self.fields_of_study),
            "open_access_pdf_url": self.pdf_url,
            "provider_refs": list(self.provider_refs),
            "needs_link_check": bool(self.needs_link_check),
            "why_relevant": self.why_relevant,
            "ai_summary": self.ai_summary,
            "explanation_links": copy.deepcopy(self.explanation_links),
        }
        return {key: value for key, value in data.items() if value not in ("", [], None)}


def _paper_explanation_links(value: object) -> list[dict[str, str]]:
    raw_items = value if isinstance(value, list) else []
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw_items:
        if isinstance(item, str):
            url = _clean_text(item)
            title = url
            source = ""
            summary = ""
        elif isinstance(item, dict):
            url = _clean_text(item.get("url") or item.get("link"))
            title = _clean_text(item.get("title") or item.get("name") or url)
            source = _clean_text(item.get("source") or item.get("site") or item.get("platform"))
            summary = _clean_text(item.get("summary") or item.get("note") or item.get("why"))
        else:
            continue
        if not url or url in seen:
            continue
        seen.add(url)
        row = {"url": url, "title": title or url}
        if source:
            row["source"] = source
        if summary:
            row["summary"] = summary
        out.append(row)
    return out[:6]


def _canonical_url(url: str) -> str:
    clean = _clean_text(url)
    if not clean:
        return ""
    parsed = urllib.parse.urlparse(clean)
    if not parsed.scheme or not parsed.netloc:
        return clean.rstrip("/")
    path = parsed.path.rstrip("/")
    return urllib.parse.urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", parsed.query, ""))


def _published_year(value: str) -> str:
    match = re.search(r"(19|20)\d{2}", _clean_text(value))
    return match.group(0) if match else ""
