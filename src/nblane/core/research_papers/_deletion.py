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
    PAPER_ANNOTATIONS_DIRNAME,
    PAPER_NOTES_DIRNAME,
    PAPER_PAGES_DIRNAME,
    PAPER_SEGMENTS_DIRNAME,
    PAPER_STRUCTURE_DIRNAME,
    PAPER_TRANSLATIONS_DIRNAME,
)
from ._paths import (
    _asset_path,
    _jsonl_path,
    _md_path,
    _profile_root,
    _research_chunk_path,
    _research_root,
    _yaml_path,
)
from ._types import PaperImportError
from ._utils import _clean_list, _clean_mapping, _clean_text, _now
from ._io import load_paper_annotations

_ANALYSIS_PRESERVED_KEYS = (
    "codex_deep_read",
    "codex_deep_read_updated",
)


def save_paper_analysis(
    profile: str | Path,
    source_id: str,
    data: dict[str, object],
    *,
    replace: bool = False,
) -> Path:
    _source_by_id(profile, source_id)
    path = _yaml_path(profile, PAPER_ANALYSIS_DIRNAME, source_id)
    incoming = _clean_mapping(data)
    if replace:
        merged: dict[str, object] = dict(incoming)
    else:
        existing = _load_yaml_dict(path) or {}
        merged = dict(_clean_mapping(existing))
        for key in _ANALYSIS_PRESERVED_KEYS:
            if key in existing and key not in incoming:
                merged[key] = existing[key]
        merged.update(incoming)
    payload = {
        "schema_version": "1.0",
        "source_id": source_id,
        "updated": _now(),
        **merged,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, yaml.dump(payload, allow_unicode=True, default_flow_style=False, sort_keys=False))
    git_backup.record_change([path], action=f"update paper analysis for {source_id}")
    return path


def load_paper_analysis(profile: str | Path, source_id: str) -> dict[str, object]:
    return _load_yaml_dict(_yaml_path(profile, PAPER_ANALYSIS_DIRNAME, source_id)) or {}


def _paper_artifact_paths(profile: str | Path, source_id: str) -> list[tuple[str, Path]]:
    return [
        ("pages", _jsonl_path(profile, PAPER_PAGES_DIRNAME, source_id)),
        ("segments", _jsonl_path(profile, PAPER_SEGMENTS_DIRNAME, source_id)),
        ("structure", _jsonl_path(profile, PAPER_STRUCTURE_DIRNAME, source_id)),
        ("annotations", _jsonl_path(profile, PAPER_ANNOTATIONS_DIRNAME, source_id)),
        ("translations", _jsonl_path(profile, PAPER_TRANSLATIONS_DIRNAME, source_id)),
        ("analysis", _yaml_path(profile, PAPER_ANALYSIS_DIRNAME, source_id)),
        ("notes", _md_path(profile, PAPER_NOTES_DIRNAME, source_id)),
        ("chunks", _research_chunk_path(profile, source_id)),
    ]


def _relative_preview_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _delete_existing_file(path: Path, *, action: str, record_change: bool = True) -> bool:
    if not path.exists():
        return False
    if not path.is_file():
        raise ValueError(f"Refusing to delete non-file path: {path}")
    path.unlink()
    if record_change:
        git_backup.record_change([path], action=action)
    return True


def build_paper_delete_preview(profile: str | Path, source_ids: object) -> dict[str, object]:
    """Preview source, asset, artifact, and reference impact before deleting papers."""

    profile_path = _profile_root(profile)
    clean_ids = _clean_list(source_ids)
    if not clean_ids:
        raise ValueError("At least one paper source id is required.")

    inbox = load_research_sources(profile_path)
    sources = inbox.by_id()
    target_ids = set(clean_ids)
    claims = load_research_claims(profile_path)
    citations = load_research_citations(profile_path)
    asset_refs: dict[str, list[str]] = {}
    for source in inbox.sources:
        asset_ref = _clean_text((source.metadata or {}).get("pdf_asset_ref"))
        if asset_ref:
            asset_refs.setdefault(asset_ref, []).append(source.id)

    papers: list[dict[str, object]] = []
    blocking_refs: list[dict[str, object]] = []
    warnings: list[str] = []
    totals = {
        "papers": 0,
        "pdf_assets": 0,
        "artifact_files": 0,
        "active_annotations": 0,
        "chunks": 0,
        "claims": 0,
        "citations": 0,
        "evidence_refs": 0,
    }

    for source_id in clean_ids:
        source = sources.get(source_id)
        if source is None:
            raise ValueError(f"Unknown research source: {source_id}")
        totals["papers"] += 1
        source_blocks: list[dict[str, object]] = []
        if source.kind != "paper":
            source_blocks.append(
                {
                    "source_id": source.id,
                    "type": "source_kind",
                    "id": source.kind,
                    "message": "Only paper sources can be deleted from Paper Library.",
                }
            )

        annotations = load_paper_annotations(profile_path, source.id)
        active_annotations = [ann for ann in annotations if ann.status == "active"]
        chunks = load_chunks(profile_path, source.id)
        chunk_ids = {chunk.id for chunk in chunks}
        claim_refs = [
            claim
            for claim in claims
            if source.id in claim.source_refs or any(ref in chunk_ids for ref in claim.chunk_refs)
        ]
        citation_refs = [
            citation
            for citation in citations
            if citation.source_id == source.id or (citation.chunk_id and citation.chunk_id in chunk_ids)
        ]
        evidence_refs = list(source.evidence_refs)

        for ann in active_annotations:
            source_blocks.append(
                {
                    "source_id": source.id,
                    "type": "annotation",
                    "id": ann.id,
                    "message": "Active annotation exists.",
                }
            )
        for chunk in chunks:
            source_blocks.append(
                {
                    "source_id": source.id,
                    "type": "chunk",
                    "id": chunk.id,
                    "message": "Research chunk exists.",
                }
            )
        for claim in claim_refs:
            source_blocks.append(
                {
                    "source_id": source.id,
                    "type": "claim",
                    "id": claim.id,
                    "message": "Research claim references this paper or its chunks.",
                }
            )
        for citation in citation_refs:
            source_blocks.append(
                {
                    "source_id": source.id,
                    "type": "citation",
                    "id": citation.id,
                    "message": "Research citation references this paper or its chunks.",
                }
            )
        for evidence_ref in evidence_refs:
            source_blocks.append(
                {
                    "source_id": source.id,
                    "type": "evidence_ref",
                    "id": evidence_ref,
                    "message": "Source is already linked to reviewed evidence.",
                }
            )

        metadata = dict(source.metadata or {})
        asset_ref = _clean_text(metadata.get("pdf_asset_ref"))
        pdf: dict[str, object] = {
            "asset_ref": asset_ref,
            "exists": False,
            "shared_by": [],
            "warning": "",
        }
        if asset_ref:
            try:
                asset_path = _asset_path(profile_path, asset_ref)
                shared_by = [sid for sid in asset_refs.get(asset_ref, []) if sid not in target_ids]
                pdf.update(
                    {
                        "exists": asset_path.exists(),
                        "path": asset_ref,
                        "shared_by": shared_by,
                    }
                )
                if asset_path.exists():
                    totals["pdf_assets"] += 1
                if shared_by:
                    pdf["warning"] = "PDF asset is shared by another source and cannot be deleted with this paper."
            except ValueError as exc:
                pdf["warning"] = str(exc)
                warnings.append(f"{source.id}: {exc}")

        artifact_rows: list[dict[str, object]] = []
        for kind, path in _paper_artifact_paths(profile_path, source.id):
            exists = path.exists()
            if exists:
                totals["artifact_files"] += 1
            artifact_rows.append(
                {
                    "kind": kind,
                    "exists": exists,
                    "path": _relative_preview_path(path, profile_path),
                }
            )

        totals["active_annotations"] += len(active_annotations)
        totals["chunks"] += len(chunks)
        totals["claims"] += len(claim_refs)
        totals["citations"] += len(citation_refs)
        totals["evidence_refs"] += len(evidence_refs)
        blocking_refs.extend(source_blocks)
        papers.append(
            {
                "source_id": source.id,
                "title": source.title,
                "status": source.status,
                "kind": source.kind,
                "pdf": pdf,
                "artifacts": artifact_rows,
                "refs": {
                    "active_annotations": [ann.id for ann in active_annotations],
                    "chunks": [chunk.id for chunk in chunks],
                    "claims": [claim.id for claim in claim_refs],
                    "citations": [citation.id for citation in citation_refs],
                    "evidence_refs": evidence_refs,
                },
                "blocking_refs": source_blocks,
            }
        )

    return {
        "source_ids": clean_ids,
        "papers": papers,
        "totals": totals,
        "blocking_refs": blocking_refs,
        "warnings": warnings,
        "can_delete": not blocking_refs,
    }


def _assert_preview_allows_delete(preview: dict[str, object]) -> None:
    blockers = preview.get("blocking_refs") if isinstance(preview, dict) else []
    if blockers:
        first = blockers[0] if isinstance(blockers, list) and blockers else {}
        if isinstance(first, dict):
            detail = f"{first.get('type')}: {first.get('id')}"
        else:
            detail = str(first)
        raise ValueError(f"Paper deletion is blocked by existing references ({detail}).")


def delete_paper_record(
    profile: str | Path,
    source_ids: object,
    *,
    delete_pdf_asset: bool = False,
    delete_reader_artifacts: bool = False,
    unlink_refs: bool = False,
) -> dict[str, object]:
    """Delete paper source records after preview confirms there are no blocking refs."""

    if unlink_refs:
        raise ValueError("unlink_refs is not implemented; remove references before deleting papers.")
    profile_path = _profile_root(profile)
    preview = build_paper_delete_preview(profile_path, source_ids)
    _assert_preview_allows_delete(preview)
    clean_ids = set(_clean_list(preview.get("source_ids")))
    inbox = load_research_sources(profile_path)

    deleted_assets: list[str] = []
    if delete_pdf_asset:
        for paper in preview.get("papers", []):
            if not isinstance(paper, dict):
                continue
            pdf = paper.get("pdf") if isinstance(paper.get("pdf"), dict) else {}
            asset_ref = _clean_text(pdf.get("asset_ref")) if isinstance(pdf, dict) else ""
            if not asset_ref:
                continue
            shared_by = _clean_list(pdf.get("shared_by")) if isinstance(pdf, dict) else []
            if shared_by:
                raise ValueError(f"PDF asset is shared by other sources: {', '.join(shared_by)}")
            path = _asset_path(profile_path, asset_ref)
            if _delete_existing_file(path, action=f"delete paper PDF asset {asset_ref}", record_change=False):
                deleted_assets.append(asset_ref)

    deleted_artifacts: list[str] = []
    if delete_reader_artifacts:
        for source_id in clean_ids:
            for kind, path in _paper_artifact_paths(profile_path, source_id):
                if _delete_existing_file(path, action=f"delete paper {kind} for {source_id}"):
                    deleted_artifacts.append(_relative_preview_path(path, profile_path))

    remaining_sources = [source for source in inbox.sources if source.id not in clean_ids]
    deleted_sources = [source.id for source in inbox.sources if source.id in clean_ids]
    inbox.sources = remaining_sources
    save_research_sources(profile_path, inbox)
    return {
        "deleted_sources": deleted_sources,
        "deleted_pdf_assets": deleted_assets,
        "deleted_artifacts": deleted_artifacts,
        "preview": preview,
    }


def delete_paper_pdf_asset(profile: str | Path, source_id: str) -> dict[str, object]:
    """Delete only one paper's PDF asset after checking it is not shared."""

    profile_path = _profile_root(profile)
    preview = build_paper_delete_preview(profile_path, [source_id])
    paper = preview["papers"][0] if preview.get("papers") else {}
    pdf = paper.get("pdf") if isinstance(paper, dict) and isinstance(paper.get("pdf"), dict) else {}
    asset_ref = _clean_text(pdf.get("asset_ref")) if isinstance(pdf, dict) else ""
    if not asset_ref:
        return {"deleted_pdf_assets": [], "preview": preview}
    shared_by = _clean_list(pdf.get("shared_by")) if isinstance(pdf, dict) else []
    if shared_by:
        raise ValueError(f"PDF asset is shared by other sources: {', '.join(shared_by)}")
    path = _asset_path(profile_path, asset_ref)
    deleted = _delete_existing_file(path, action=f"delete paper PDF asset {asset_ref}", record_change=False)
    if deleted:
        inbox, source = _source_by_id(profile_path, source_id)
        metadata = dict(source.metadata or {})
        for key in ("pdf_asset_ref", "pdf_sha256", "pdf_byte_size", "pdf_filename"):
            metadata.pop(key, None)
        update_research_source(inbox, source.id, metadata=metadata)
        save_research_sources(profile_path, inbox)
    return {"deleted_pdf_assets": [asset_ref] if deleted else [], "preview": preview}


def delete_paper_reader_artifacts(profile: str | Path, source_id: str) -> dict[str, object]:
    """Delete only cached reader artifacts for one paper source."""

    profile_path = _profile_root(profile)
    preview = build_paper_delete_preview(profile_path, [source_id])
    _assert_preview_allows_delete(preview)
    deleted: list[str] = []
    for kind, path in _paper_artifact_paths(profile_path, source_id):
        if _delete_existing_file(path, action=f"delete paper {kind} for {source_id}"):
            deleted.append(_relative_preview_path(path, profile_path))
    return {"deleted_artifacts": deleted, "preview": preview}


def purge_discarded_papers(
    profile: str | Path,
    *,
    delete_pdf_asset: bool = False,
    delete_reader_artifacts: bool = False,
) -> dict[str, object]:
    """Delete all discarded paper source records that have no blocking refs."""

    profile_path = _profile_root(profile)
    inbox = load_research_sources(profile_path)
    source_ids = [source.id for source in inbox.sources if source.kind == "paper" and source.status == "discarded"]
    if not source_ids:
        return {
            "deleted_sources": [],
            "deleted_pdf_assets": [],
            "deleted_artifacts": [],
            "preview": {
                "source_ids": [],
                "papers": [],
                "totals": {
                    "papers": 0,
                    "pdf_assets": 0,
                    "artifact_files": 0,
                    "active_annotations": 0,
                    "chunks": 0,
                    "claims": 0,
                    "citations": 0,
                    "evidence_refs": 0,
                },
                "blocking_refs": [],
                "warnings": [],
                "can_delete": True,
            },
        }
    return delete_paper_record(
        profile_path,
        source_ids,
        delete_pdf_asset=delete_pdf_asset,
        delete_reader_artifacts=delete_reader_artifacts,
    )
