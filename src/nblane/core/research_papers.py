"""Paper Reading Studio core helpers.

This module owns paper-specific facts that sit beside the existing Research
Workspace source/chunk/claim/citation layer:

* PDF assets live outside profile Git directories.
* Pages, segments, annotations, translations, analysis, notes, exports, and
  library-tree taxonomy live under ``profiles/<name>/research``.
* AI/search results remain candidates until callers explicitly import or save
  them through these helpers.
"""

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

LIBRARY_TREE_FILENAME = "library-tree.yaml"
PAPER_PAGES_DIRNAME = "paper-pages"
PAPER_SEGMENTS_DIRNAME = "paper-segments"
PAPER_STRUCTURE_DIRNAME = "paper-structure"
PAPER_ANNOTATIONS_DIRNAME = "annotations"
PAPER_TRANSLATIONS_DIRNAME = "translations"
PAPER_ANALYSIS_DIRNAME = "analysis"
PAPER_NOTES_DIRNAME = "notes"
PAPER_EXPORTS_DIRNAME = "exports"

PAPER_ANNOTATION_KINDS = ("highlight", "note", "question")
PAPER_ANNOTATION_STATUSES = ("active", "deleted")
PAPER_TRANSLATION_STATUSES = ("translated", "missing", "stale", "failed")
PAPER_TRANSLATION_SCOPES = ("segment", "page", "selection", "layout", "structure")
PAPER_STRUCTURE_VERSION = "v4"
PAPER_STRUCTURE_TRANSLATION_KINDS = ("title", "heading", "paragraph", "caption")
PAPER_STRUCTURE_BODY_EXCLUDED_KINDS = (
    "authors",
    "affiliation",
    "figure",
    "table",
    "footnote",
    "reference",
    "symbol",
    "figure_label",
    "table_cell",
)
PAPER_SEARCH_PROVIDERS = ("arxiv_html", "arxiv", "semantic_scholar")
NO_LLM_TRANSLATION_WARNING = "No LLM translation backend produced text."
PDF_MAX_BYTES_DEFAULT = 75 * 1024 * 1024
PDF_DOWNLOAD_TIMEOUT_SECONDS_DEFAULT = 45.0
PDF_DOWNLOAD_IDLE_TIMEOUT_SECONDS_DEFAULT = 10.0
PDF_DOWNLOAD_CHUNK_BYTES = 32 * 1024
GROBID_FULLTEXT_TIMEOUT_SECONDS_DEFAULT = 120.0
GROBID_RETRY_COOLDOWN_SECONDS_DEFAULT = 24 * 60 * 60
PAPER_TRANSLATION_BATCH_SIZE_DEFAULT = 12
PAPER_STRUCTURE_TRANSLATION_BATCH_SIZE_DEFAULT = 12
PAPER_LAYOUT_TRANSLATION_BATCH_SIZE_DEFAULT = 12
PAPER_PAGE_TRANSLATION_BATCH_SIZE_DEFAULT = 4
PAPER_TRANSLATION_BATCH_CHARS_DEFAULT = 9000
PAPER_PAGE_TRANSLATION_BATCH_CHARS_DEFAULT = 12000
PAPER_TRANSLATION_INCLUDE_REFERENCES_ENV = "NBLANE_PAPER_TRANSLATION_INCLUDE_REFERENCES"
PAPER_REFERENCE_SECTION_LABELS = {
    "references",
    "bibliography",
    "works cited",
    "literature cited",
    "参考文献",
    "參考文獻",
}
PAPER_DIAGNOSTIC_BADGES = {
    "grobid_unavailable": "GROBID unavailable",
    "needs_structured_extraction": "Needs structured extraction",
    "fallback_extraction": "Fallback ready",
    "stale_translation": "Stale translation",
    "citation_broken": "Citation broken",
    "private_source": "Private source",
    "duplicate_risk": "Duplicate risk",
}
PAPER_DIAGNOSTIC_SEVERITIES = {
    "grobid_unavailable": "warning",
    "needs_structured_extraction": "warning",
    "fallback_extraction": "info",
    "stale_translation": "warning",
    "citation_broken": "error",
    "private_source": "info",
    "duplicate_risk": "warning",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _timestamp_from_iso(value: object) -> float:
    text = _clean_text(value)
    if not text:
        return 0.0
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


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
    out: dict[str, object] = {}
    for key, item in value.items():
        clean = _clean_text(key)
        if clean:
            out[clean] = copy.deepcopy(item)
    return out


def _clean_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    clean = _clean_text(value).lower()
    if clean in {"1", "true", "yes", "on"}:
        return True
    if clean in {"0", "false", "no", "off"}:
        return False
    return default


def _url_looks_like_pdf(url: object) -> bool:
    clean = _clean_text(url)
    if not clean:
        return False
    parsed = urllib.parse.urlparse(clean)
    if parsed.scheme not in {"http", "https"}:
        return False
    path = parsed.path.lower()
    return path.endswith(".pdf") or (parsed.netloc.lower().endswith("arxiv.org") and path.startswith("/pdf/"))


def _choice(value: object, options: tuple[str, ...], default: str) -> str:
    clean = _clean_text(value)
    return clean if clean in options else default


def _append_unique(values: list[str], value: str) -> None:
    clean = _clean_text(value)
    if clean and clean not in values:
        values.append(clean)


def _append_badge(
    badges: list[str],
    badge_details: list[dict[str, str]],
    badge_id: str,
    *,
    detail: str = "",
) -> None:
    label = PAPER_DIAGNOSTIC_BADGES.get(badge_id, badge_id)
    _append_unique(badges, label)
    if any(row.get("id") == badge_id for row in badge_details):
        return
    row = {
        "id": badge_id,
        "label": label,
        "severity": PAPER_DIAGNOSTIC_SEVERITIES.get(badge_id, "info"),
    }
    clean_detail = _clean_text(detail)
    if clean_detail:
        row["detail"] = clean_detail
    badge_details.append(row)


def _slug(value: object, *, fallback: str = "paper") -> str:
    clean = _clean_text(value).replace(":", "-").replace("/", "-").replace("\\", "-")
    clean = re.sub(r"[^A-Za-z0-9._~\-\u4e00-\u9fff]+", "-", clean)
    clean = re.sub(r"-+", "-", clean).strip(".-")
    return clean[:96] or fallback


def _profile_root(profile: str | Path) -> Path:
    if isinstance(profile, Path):
        return profile.parent if profile.name == RESEARCH_DIRNAME else profile
    return profile_dir(profile)


def _profile_name(profile: str | Path) -> str:
    return _profile_root(profile).name if isinstance(profile, Path) else str(profile)


def _research_root(profile: str | Path) -> Path:
    root = _profile_root(profile)
    return root / RESEARCH_DIRNAME


def _jsonl_path(profile: str | Path, dirname: str, source_id: str) -> Path:
    return _research_root(profile) / dirname / f"{source_slug(source_id)}.jsonl"


def _yaml_path(profile: str | Path, dirname: str, source_id: str) -> Path:
    return _research_root(profile) / dirname / f"{source_slug(source_id)}.yaml"


def _md_path(profile: str | Path, dirname: str, source_id: str) -> Path:
    return _research_root(profile) / dirname / f"{source_slug(source_id)}.md"


def _research_chunk_path(profile: str | Path, source_id: str) -> Path:
    return _research_root(profile) / RESEARCH_CHUNKS_DIRNAME / f"{source_slug(source_id)}.jsonl"


def text_hash(text: str) -> str:
    """Return the stable hash label used by pages, segments, and translations."""

    return "sha256:" + hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]], *, action: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        for row in rows
    )
    atomic_write_text(path, text)
    git_backup.record_change([path], action=action)
    return path


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
        tmp_name = ""
    finally:
        if tmp_name:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass


def _page_count_fallback(pdf_bytes: bytes) -> int:
    # Good enough for fixtures and graceful fallback when PyMuPDF is absent.
    return len(re.findall(rb"/Type\s*/Page\b", pdf_bytes))


def _pdf_page_count(pdf_bytes: bytes) -> tuple[int, list[str]]:
    if pymupdf_available():
        try:
            import fitz  # type: ignore[import-not-found]

            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                return int(doc.page_count), []
        except Exception as exc:
            return _page_count_fallback(pdf_bytes), [f"PyMuPDF page count failed: {exc}"]
    return _page_count_fallback(pdf_bytes), ["PyMuPDF unavailable; used lightweight page-count fallback."]


def _max_pdf_bytes() -> int:
    raw = os.getenv("NBLANE_RESEARCH_PDF_MAX_BYTES", "").strip()
    if not raw:
        return PDF_MAX_BYTES_DEFAULT
    try:
        return max(1024, int(raw))
    except ValueError:
        return PDF_MAX_BYTES_DEFAULT


def _pdf_download_timeout_seconds() -> float:
    raw = os.getenv("NBLANE_PAPER_PDF_DOWNLOAD_TIMEOUT_SECONDS", "").strip()
    configured = _positive_float(raw) if raw else None
    return configured if configured is not None else PDF_DOWNLOAD_TIMEOUT_SECONDS_DEFAULT


def _pdf_download_idle_timeout_seconds() -> float:
    raw = os.getenv("NBLANE_PAPER_PDF_DOWNLOAD_IDLE_TIMEOUT_SECONDS", "").strip()
    configured = _positive_float(raw) if raw else None
    return configured if configured is not None else PDF_DOWNLOAD_IDLE_TIMEOUT_SECONDS_DEFAULT


def _format_download_progress(total: int, expected: int | None) -> str:
    if expected and expected > 0:
        return f"{total}/{expected} bytes"
    return f"{total} bytes"


def _validate_pdf_bytes(file_bytes: bytes) -> None:
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise ValueError("PDF payload must be bytes.")
    if not file_bytes:
        raise ValueError("PDF payload is empty.")
    if len(file_bytes) > _max_pdf_bytes():
        raise ValueError("PDF payload exceeds NBLANE_RESEARCH_PDF_MAX_BYTES.")
    if not bytes(file_bytes).lstrip().startswith(b"%PDF"):
        raise ValueError("Uploaded file does not look like a PDF.")


def _source_by_id(profile: str | Path, source_id: str) -> tuple[ResearchSourceInbox, ResearchSource]:
    inbox = load_research_sources(_profile_root(profile))
    clean = _clean_text(source_id)
    source = inbox.by_id().get(clean)
    if source is None:
        raise ValueError(f"Unknown research source: {clean}")
    return inbox, source


def _update_source_metadata(
    profile: str | Path,
    source_id: str,
    metadata: dict[str, object],
    *,
    status: str = "",
    library_node_refs: object = None,
) -> ResearchSource:
    inbox, source = _source_by_id(profile, source_id)
    merged = dict(source.metadata or {})
    merged.update(_clean_mapping(metadata))
    fields: dict[str, object] = {"metadata": merged, "kind": "paper"}
    if status:
        fields["status"] = status
    if library_node_refs is not None:
        fields["library_node_refs"] = library_node_refs
    update_research_source(inbox, source.id, **fields)
    save_research_sources(_profile_root(profile), inbox)
    return inbox.by_id()[source.id]


def _update_source_metadata_if_changed(
    profile: str | Path,
    source_id: str,
    metadata: dict[str, object],
    *,
    status: str = "",
) -> ResearchSource:
    inbox, source = _source_by_id(profile, source_id)
    merged = dict(source.metadata or {})
    clean = _clean_mapping(metadata)
    next_metadata = dict(merged)
    next_metadata.update(clean)
    status_changed = bool(status) and source.status != status
    if next_metadata == merged and not status_changed:
        return source
    fields: dict[str, object] = {"metadata": next_metadata, "kind": "paper"}
    if status:
        fields["status"] = status
    update_research_source(inbox, source.id, **fields)
    save_research_sources(_profile_root(profile), inbox)
    return inbox.by_id()[source.id]


def _asset_profile_segment(profile: str | Path) -> str:
    name = _profile_name(profile)
    try:
        return validate_profile_name(name).replace(" ", "-")
    except ValueError:
        return _slug(name, fallback="profile")


def research_asset_root(profile: str | Path) -> Path:
    """Return the profile-scoped external research asset root.

    The returned path is the profile asset directory. PDF refs such as
    ``papers/<sha>-name.pdf`` resolve under this directory.
    """

    env_root = os.getenv("NBLANE_RESEARCH_ASSET_ROOT", "").strip()
    base = Path(env_root).expanduser() if env_root else Path.home() / ".nblane" / "research-assets"
    return (base / "profiles" / _asset_profile_segment(profile)).resolve()


def _asset_path(profile: str | Path, asset_ref: str) -> Path:
    clean = _clean_text(asset_ref)
    if not clean:
        raise ValueError("Paper asset ref is empty.")
    if clean.startswith("/") or "\\" in clean:
        raise ValueError("Paper asset ref must be a relative POSIX path.")
    parts = Path(clean)
    if any(part in ("", ".", "..") for part in parts.parts):
        raise ValueError("Paper asset ref may not contain path traversal.")
    root = research_asset_root(profile)
    candidate = (root / parts).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("Paper asset ref escapes the research asset root.") from exc
    return candidate


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


def import_paper_pdf(
    profile: str | Path,
    source_id: str,
    file_bytes: bytes,
    filename: str,
    *,
    pdf_url: str = "",
) -> PaperAsset:
    """Save a PDF outside the profile Git tree and update source metadata."""

    _source_by_id(profile, source_id)
    payload = bytes(file_bytes)
    _validate_pdf_bytes(payload)
    clean_name = Path(_clean_text(filename) or "paper.pdf").name
    if not clean_name.lower().endswith(".pdf"):
        clean_name += ".pdf"
    digest = hashlib.sha256(payload).hexdigest()
    page_count, warnings = _pdf_page_count(payload)
    asset_ref = f"papers/{digest[:12]}-{_slug(Path(clean_name).stem, fallback='paper')}.pdf"
    path = _asset_path(profile, asset_ref)
    _atomic_write_bytes(path, payload)
    asset = PaperAsset(
        source_id=_clean_text(source_id),
        asset_ref=asset_ref,
        sha256=digest,
        byte_size=len(payload),
        page_count=page_count,
        filename=clean_name,
        pdf_url=_clean_text(pdf_url),
        warnings=warnings,
    )
    metadata = asset.to_metadata()
    metadata["pdf_imported_at"] = _now()
    metadata["pdf_download_status"] = "downloaded"
    metadata["pdf_download_error"] = ""
    _update_source_metadata(profile, source_id, metadata)
    return asset


def download_paper_pdf(profile: str | Path, source_id: str, pdf_url: str) -> PaperAsset:
    """Download an open-access PDF into the external asset root."""

    clean_url = _clean_text(pdf_url)
    parsed = urllib.parse.urlparse(clean_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("PDF URL must be http or https.")
    request = urllib.request.Request(
        clean_url,
        headers={"User-Agent": "nblane-paper-reading/1.0"},
        method="GET",
    )
    max_bytes = _max_pdf_bytes()
    timeout_seconds = _pdf_download_timeout_seconds()
    idle_timeout_seconds = _pdf_download_idle_timeout_seconds()
    socket_timeout = max(1.0, min(idle_timeout_seconds, timeout_seconds))
    started = time.monotonic()
    expected_bytes: int | None = None
    with urllib.request.urlopen(request, timeout=socket_timeout) as response:
        content_length = _clean_text(response.headers.get("content-length"))
        try:
            expected_bytes = int(content_length) if content_length else None
        except ValueError:
            expected_bytes = None
        chunks: list[bytes] = []
        total = 0
        while True:
            elapsed = time.monotonic() - started
            if elapsed > timeout_seconds:
                progress = _format_download_progress(total, expected_bytes)
                raise TimeoutError(
                    f"PDF download exceeded {timeout_seconds:.0f}s after {progress}; "
                    "try again later or increase NBLANE_PAPER_PDF_DOWNLOAD_TIMEOUT_SECONDS."
                )
            chunk = response.read(PDF_DOWNLOAD_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("Downloaded PDF exceeds NBLANE_RESEARCH_PDF_MAX_BYTES.")
            chunks.append(chunk)
    filename = Path(parsed.path).name or f"{source_slug(source_id)}.pdf"
    return import_paper_pdf(profile, source_id, b"".join(chunks), filename, pdf_url=clean_url)


def _source_pdf_download_url(source: ResearchSource, override_url: str = "") -> str:
    metadata = source.metadata or {}
    return _clean_text(
        override_url
        or metadata.get("open_access_pdf_url")
        or metadata.get("pdf_url")
        or (source.url if _clean_text(source.url).lower().endswith(".pdf") else "")
    )


def ensure_paper_pdf_downloaded(
    profile: str | Path,
    source_id: str,
    *,
    pdf_url: str = "",
    error_prefix: str = "PDF download failed",
) -> dict[str, object]:
    """Download a source's open-access PDF and persist a user-visible status."""

    _, source = _source_by_id(profile, source_id)
    clean_source_id = _clean_text(source_id)
    existing_asset_ref = _clean_text((source.metadata or {}).get("pdf_asset_ref"))
    if existing_asset_ref:
        existing_path: Path | None = None
        try:
            existing_path = _asset_path(profile, existing_asset_ref)
        except ValueError:
            existing_path = None
        if existing_path is not None and existing_path.is_file() and existing_path.stat().st_size > 0:
            _update_source_metadata(
                profile,
                clean_source_id,
                {
                    "pdf_download_status": "downloaded",
                    "pdf_download_error": "",
                },
            )
            return {
                "source_id": clean_source_id,
                "status": "downloaded",
                "asset_ref": existing_asset_ref,
                "byte_size": existing_path.stat().st_size,
                "page_count": (source.metadata or {}).get("page_count", ""),
                "existing": True,
            }
    clean_url = _source_pdf_download_url(source, pdf_url)
    attempted_at = _now()
    if not clean_url:
        message = "No open-access PDF URL is recorded for this paper."
        _update_source_metadata(
            profile,
            clean_source_id,
            {
                "pdf_download_status": "skipped_no_pdf_url",
                "pdf_download_attempted_at": attempted_at,
                "pdf_download_error": message,
            },
        )
        return {
            "source_id": clean_source_id,
            "status": "skipped_no_pdf_url",
            "pdf_url": "",
            "error": message,
        }
    if bool((source.metadata or {}).get("needs_link_check")):
        message = "PDF download skipped because the link still needs checking."
        _update_source_metadata(
            profile,
            clean_source_id,
            {
                "pdf_download_status": "skipped_needs_link_check",
                "pdf_download_attempted_at": attempted_at,
                "pdf_download_error": message,
            },
        )
        return {
            "source_id": clean_source_id,
            "status": "skipped_needs_link_check",
            "pdf_url": clean_url,
            "error": message,
        }
    _update_source_metadata(
        profile,
        clean_source_id,
        {
            "pdf_download_status": "downloading",
            "pdf_download_attempted_at": attempted_at,
            "pdf_download_error": "",
        },
    )
    try:
        asset = download_paper_pdf(profile, clean_source_id, clean_url)
    except Exception as exc:
        message = f"{error_prefix}: {exc}"
        _update_source_metadata(
            profile,
            clean_source_id,
            {
                "pdf_download_status": "failed",
                "pdf_download_attempted_at": _now(),
                "pdf_download_error": message,
            },
        )
        return {
            "source_id": clean_source_id,
            "status": "failed",
            "pdf_url": clean_url,
            "error": message,
        }
    _update_source_metadata(
        profile,
        clean_source_id,
        {
            "pdf_download_status": "downloaded",
            "pdf_download_attempted_at": _now(),
            "pdf_download_error": "",
        },
    )
    return {
        "source_id": clean_source_id,
        "status": "downloaded",
        "pdf_url": clean_url,
        "asset_ref": asset.asset_ref,
        "byte_size": asset.byte_size,
        "page_count": asset.page_count,
    }


def load_paper_pdf_bytes(profile: str | Path, source_id: str) -> bytes:
    """Load a paper PDF through the source's relative asset ref."""

    _, source = _source_by_id(profile, source_id)
    asset_ref = _clean_text((source.metadata or {}).get("pdf_asset_ref"))
    path = _asset_path(profile, asset_ref)
    if not path.exists():
        raise FileNotFoundError(f"Paper PDF asset is missing: {asset_ref}")
    return path.read_bytes()


def paper_pdf_asset_path(profile: str | Path, source_id: str) -> Path:
    """Return the validated local PDF asset path for a paper source."""

    _, source = _source_by_id(profile, source_id)
    asset_ref = _clean_text((source.metadata or {}).get("pdf_asset_ref"))
    path = _asset_path(profile, asset_ref)
    if not path.exists():
        raise FileNotFoundError(f"Paper PDF asset is missing: {asset_ref}")
    return path


if st is not None:
    _pdf_url_cache = st.cache_resource(show_spinner=False, max_entries=128)
else:
    from functools import lru_cache

    def _pdf_url_cache(func):
        return lru_cache(maxsize=128)(func)


@_pdf_url_cache
def _stable_pdf_url_cached(
    profile_name: str,
    source_id: str,
    pdf_asset_ref: str,
    pdf_sha256: str,
    path_text: str,
) -> str:
    try:
        from streamlit import runtime
    except Exception:
        return ""
    try:
        if not runtime.exists():
            return ""
        path = Path(path_text)
        return runtime.get_instance().media_file_mgr.add(
            str(path),
            "application/pdf",
            f"paper-reader-pdf:{profile_name}:{source_id}:{pdf_asset_ref}:{pdf_sha256}",
            file_name=path.name,
        )
    except Exception:
        return ""


def get_stable_pdf_url(profile: str | Path, source_id: str) -> str:
    """Return a Streamlit media URL that only changes when the PDF fingerprint changes."""

    _, source = _source_by_id(profile, source_id)
    metadata = dict(source.metadata or {})
    pdf_asset_ref = _clean_text(metadata.get("pdf_asset_ref"))
    pdf_sha256 = _clean_text(metadata.get("pdf_sha256")) or pdf_asset_ref
    path = paper_pdf_asset_path(profile, source_id)
    return _stable_pdf_url_cached(
        _profile_name(profile),
        source_id,
        pdf_asset_ref,
        pdf_sha256,
        str(path),
    )


def render_paper_page_preview(
    profile: str | Path,
    source_id: str,
    page: int = 1,
    *,
    max_width: int = 1100,
) -> dict[str, object]:
    """Render one PDF page to a PNG data URL for Reader visual fallback."""

    try:
        page_number = max(1, int(page or 1))
    except (TypeError, ValueError):
        page_number = 1
    try:
        width_limit = max(320, min(2200, int(max_width or 1100)))
    except (TypeError, ValueError):
        width_limit = 1100
    pdf_bytes = load_paper_pdf_bytes(profile, source_id)
    try:
        import fitz  # type: ignore[import-not-found]
    except Exception as exc:
        raise RuntimeError("PyMuPDF is required for PDF page preview fallback.") from exc

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        if doc.page_count < 1:
            raise ValueError("PDF has no pages.")
        safe_page = max(1, min(page_number, int(doc.page_count)))
        pdf_page = doc.load_page(safe_page - 1)
        rect = pdf_page.rect
        zoom = min(2.0, max(0.5, width_limit / max(1.0, float(rect.width))))
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = pdf_page.get_pixmap(matrix=matrix, alpha=False)
        png_bytes = pixmap.tobytes("png")
    return {
        "page": safe_page,
        "width": int(pixmap.width),
        "height": int(pixmap.height),
        "mime": "image/png",
        "data_url": "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii"),
    }


def extract_paper_figures(
    profile: str | Path,
    source_id: str,
    *,
    pages: set[int] | list[int] | tuple[int, ...] | None = None,
    max_items: int = 12,
    max_width: int = 520,
) -> list[dict[str, object]]:
    """Return cropped figure/table-like page images for Reader review panes."""

    try:
        requested_pages = {
            int(item)
            for item in (pages or [])
            if str(item).strip().isdigit() and int(item) > 0
        }
        limit = max(1, min(36, int(max_items or 12)))
        width_limit = max(160, min(1000, int(max_width or 520)))
    except (TypeError, ValueError):
        requested_pages = set()
        limit = 12
        width_limit = 520
    try:
        pdf_path = paper_pdf_asset_path(profile, source_id)
        import fitz  # type: ignore[import-not-found]
    except Exception:
        return []

    out: list[dict[str, object]] = []
    try:
        with fitz.open(str(pdf_path)) as doc:
            for page_number, pdf_page in enumerate(doc, start=1):
                if requested_pages and page_number not in requested_pages:
                    continue
                page_rect = pdf_page.rect
                page_width = float(page_rect.width)
                page_height = float(page_rect.height)
                if page_width <= 0 or page_height <= 0:
                    continue
                layer = _pdf_page_text_layer_payload(pdf_page, page_number)
                captions = _figure_caption_candidates(layer)
                candidates: list[tuple[str, int, dict[str, object]]] = []
                for image_index, raw_rect in enumerate(layer.get("image_rects") or [], start=1):
                    if isinstance(raw_rect, dict):
                        candidates.append(("figure", image_index, raw_rect))
                try:
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        tables = list(getattr(pdf_page.find_tables(), "tables", []) or [])
                except Exception:
                    tables = []
                for table_index, table in enumerate(tables, start=1):
                    table_rect = _rect_payload(
                        getattr(table, "bbox", ()),
                        page_width=page_width,
                        page_height=page_height,
                    )
                    if table_rect is not None:
                        candidates.append(("table", table_index, table_rect))
                for caption_index, caption in enumerate(captions, start=1):
                    fallback_rect = _caption_region_rect(
                        caption,
                        candidates=[row[2] for row in candidates],
                        page_width=page_width,
                        page_height=page_height,
                    )
                    if fallback_rect is not None:
                        candidates.append(("caption", caption_index, fallback_rect))
                grouped: list[dict[str, object]] = []
                by_caption: dict[str, dict[str, object]] = {}
                for item_index, (kind, kind_index, raw_rect) in enumerate(candidates, start=1):
                    rect = _expanded_figure_rect(raw_rect, captions, page_width=page_width, page_height=page_height)
                    if rect is None:
                        continue
                    if _rect_area(rect) < max(900.0, page_width * page_height * 0.01):
                        continue
                    caption = _nearest_caption_text(rect, captions)
                    group_key = f"caption:{caption.casefold()}" if caption else ""
                    if group_key and group_key in by_caption:
                        group = by_caption[group_key]
                        rects = group.setdefault("rects", [])
                        if isinstance(rects, list):
                            rects.append(rect)
                        if not group.get("kind") or group.get("kind") == "caption":
                            group["kind"] = kind
                            group["kind_index"] = kind_index
                        continue
                    group = {
                        "kind": kind,
                        "kind_index": kind_index,
                        "caption": caption,
                        "rects": [rect],
                        "order": item_index,
                    }
                    grouped.append(group)
                    if group_key:
                        by_caption[group_key] = group

                used_rects: list[dict[str, object]] = []
                for item_index, group in enumerate(grouped, start=1):
                    rect = _rect_union_payload(
                        [row for row in group.get("rects") or [] if isinstance(row, dict)],
                        page_width=page_width,
                        page_height=page_height,
                    )
                    if rect is None:
                        continue
                    if any(
                        _rect_overlap_ratio(rect, used) > 0.72 or _rect_overlap_ratio(used, rect) > 0.72
                        for used in used_rects
                    ):
                        continue
                    used_rects.append(rect)
                    clip = fitz.Rect(
                        float(rect.get("x") or 0),
                        float(rect.get("y") or 0),
                        float(rect.get("x") or 0) + float(rect.get("w") or 0),
                        float(rect.get("y") or 0) + float(rect.get("h") or 0),
                    )
                    zoom = min(2.0, max(0.6, width_limit / max(1.0, float(rect.get("w") or 1))))
                    pixmap = pdf_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False)
                    png_bytes = pixmap.tobytes("png")
                    caption = _clean_text(group.get("caption")) or _nearest_caption_text(rect, captions)
                    figure_id = f"figure:{source_slug(source_id)}:{page_number}:{item_index:03d}"
                    out.append(
                        {
                            "id": figure_id,
                            "anchor_id": figure_id,
                            "page": page_number,
                            "order": item_index,
                            "kind": _clean_text(group.get("kind")) or "figure",
                            "kind_index": int(group.get("kind_index") or item_index),
                            "caption": caption,
                            "source_text": caption,
                            "locator": f"p. {page_number}",
                            "rect": rect,
                            "rects": [rect],
                            "mime": "image/png",
                            "width": int(pixmap.width),
                            "height": int(pixmap.height),
                            "data_url": "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii"),
                        }
                    )
                    if len(out) >= limit:
                        return out
    except Exception:
        return out
    return out


def pymupdf_available() -> bool:
    """Return True when PyMuPDF's ``fitz`` module can be imported."""

    try:
        import fitz  # noqa: F401  # type: ignore[import-not-found]
    except Exception:
        return False
    return True


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


def load_paper_pages(profile: str | Path, source_id: str) -> list[PaperPage]:
    return [
        page
        for row in _load_jsonl(_jsonl_path(profile, PAPER_PAGES_DIRNAME, source_id))
        if (page := PaperPage.from_dict(row)) is not None
    ]


def save_paper_pages(profile: str | Path, source_id: str, pages: list[PaperPage | dict]) -> Path:
    rows = []
    for item in pages:
        page = item if isinstance(item, PaperPage) else PaperPage.from_dict(item)
        if page is not None:
            rows.append(page.to_dict())
    return _write_jsonl(
        _jsonl_path(profile, PAPER_PAGES_DIRNAME, source_id),
        rows,
        action=f"update paper pages for {source_id}",
    )


def load_paper_segments(profile: str | Path, source_id: str) -> list[PaperSegment]:
    return [
        segment
        for row in _load_jsonl(_jsonl_path(profile, PAPER_SEGMENTS_DIRNAME, source_id))
        if (segment := PaperSegment.from_dict(row)) is not None
    ]


def save_paper_segments(profile: str | Path, source_id: str, segments: list[PaperSegment | dict]) -> Path:
    rows = []
    for item in segments:
        segment = item if isinstance(item, PaperSegment) else PaperSegment.from_dict(item)
        if segment is not None:
            rows.append(segment.to_dict())
    return _write_jsonl(
        _jsonl_path(profile, PAPER_SEGMENTS_DIRNAME, source_id),
        rows,
        action=f"update paper segments for {source_id}",
    )


def load_paper_structure_units(profile: str | Path, source_id: str) -> list[PaperStructureUnit]:
    return [
        unit
        for row in _load_jsonl(_jsonl_path(profile, PAPER_STRUCTURE_DIRNAME, source_id))
        if (unit := PaperStructureUnit.from_dict(row)) is not None
    ]


def save_paper_structure_units(
    profile: str | Path,
    source_id: str,
    units: list[PaperStructureUnit | dict],
) -> Path:
    rows = []
    for item in units:
        unit = item if isinstance(item, PaperStructureUnit) else PaperStructureUnit.from_dict(item)
        if unit is not None:
            rows.append(unit.to_dict())
    return _write_jsonl(
        _jsonl_path(profile, PAPER_STRUCTURE_DIRNAME, source_id),
        rows,
        action=f"update paper structure units for {source_id}",
    )


def _segments_from_page_text(source_id: str, pages: list[PaperPage]) -> list[PaperSegment]:
    segments: list[PaperSegment] = []
    order = 0
    slug = source_slug(source_id)
    for page in pages:
        parts = [
            part.strip()
            for part in re.split(r"\n\s*\n+", page.text)
            if part.strip()
        ]
        if not parts and page.text.strip():
            parts = [page.text.strip()]
        for part in parts:
            order += 1
            segments.append(
                PaperSegment(
                    segment_id=f"seg:{slug}:{order:05d}",
                    source_id=source_id,
                    page=page.page,
                    order=order,
                    text=part,
                    locator=f"p. {page.page}",
                )
            )
    return segments


def extract_paper_pages(
    profile: str | Path,
    source_id: str,
    *,
    backend: str = "auto",
) -> list[PaperPage]:
    """Extract page text with PyMuPDF when available, else a safe fallback."""

    clean_backend = _clean_text(backend).lower() or "auto"
    if clean_backend not in {"auto", "pymupdf", "fallback"}:
        raise ValueError(f"Unknown paper page extraction backend: {backend}")
    pdf_bytes = load_paper_pdf_bytes(profile, source_id)
    extracted_at = _now()
    warnings: list[str] = []
    pages: list[PaperPage] = []
    if clean_backend != "fallback" and pymupdf_available():
        try:
            import fitz  # type: ignore[import-not-found]

            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                for index, page in enumerate(doc, start=1):
                    text = page.get_text("text") or ""
                    pages.append(
                        PaperPage(
                            source_id=source_id,
                            page=index,
                            text=text,
                            char_count=len(text),
                            text_hash=text_hash(text),
                            extracted_at=extracted_at,
                            metadata={"backend": "pymupdf"},
                        )
                    )
        except Exception as exc:
            warnings.append(f"PyMuPDF extraction failed: {exc}")
            pages = []
    elif clean_backend == "pymupdf":
        warnings.append("PyMuPDF unavailable.")

    if not pages:
        count = max(1, _page_count_fallback(pdf_bytes))
        pages = [
            PaperPage(
                source_id=source_id,
                page=index,
                text="",
                char_count=0,
                text_hash=text_hash(""),
                extracted_at=extracted_at,
                metadata={"backend": "fallback"},
            )
            for index in range(1, count + 1)
        ]
        if not warnings:
            warnings.append("No text backend was available; saved blank page placeholders.")

    save_paper_pages(profile, source_id, pages)
    metadata = {
        "page_count": len(pages),
        "text_extraction_backend": "pymupdf" if pages and pages[0].metadata.get("backend") == "pymupdf" else "fallback",
        "text_extracted_at": extracted_at,
        "local_pdf_backend": "pymupdf" if pages and pages[0].metadata.get("backend") == "pymupdf" else "fallback",
    }
    if warnings:
        metadata["text_extraction_warnings"] = warnings
    _update_source_metadata(profile, source_id, metadata)
    return pages


def extract_paper_segments(
    profile: str | Path,
    source_id: str,
    *,
    backend: str = "auto",
) -> list[PaperSegment]:
    """Extract stable reading/translation segments from pages or GROBID TEI."""

    clean_backend = _clean_text(backend).lower() or "auto"
    if clean_backend in {"pymupdf", "heuristic"}:
        clean_backend = "fallback"
    if clean_backend not in {"auto", "grobid", "fallback"}:
        raise ValueError(f"Unknown paper segment extraction backend: {backend}")
    warnings: list[str] = []
    grobid_status: dict[str, object] = {}
    grobid_failure = ""
    if clean_backend in {"auto", "grobid"}:
        grobid_status = grobid_readiness()
    if clean_backend in {"auto", "grobid"} and grobid_status.get("available"):
        try:
            doc = process_grobid_fulltext(profile, source_id)
            segments = grobid_tei_to_segments(source_id, doc.tei_xml)
            references = grobid_tei_to_bibliography(source_id, doc.tei_xml)
            if segments:
                save_paper_segments(profile, source_id, segments)
                _update_source_metadata(
                    profile,
                    source_id,
                    {
                        "structure_backend": "grobid",
                        "structured_extracted_at": _now(),
                        "structured_references": references,
                        "structured_references_count": len(references),
                        "structured_extraction_warnings": [],
                        "grobid_status": "available",
                        "grobid_available": True,
                        "grobid_last_error": "",
                        "grobid_last_failed_at": "",
                        "grobid_failure_pdf_sha256": "",
                    },
                )
                return segments
            warnings.append("GROBID returned no usable segments; used page-text fallback.")
        except Exception as exc:
            grobid_failure = f"GROBID extraction failed: {exc}"
            warnings.append(grobid_failure)
    elif clean_backend in {"auto", "grobid"}:
        message = _clean_text(grobid_status.get("message")) or "GROBID unavailable; used page-text fallback."
        warnings.append(message)
    else:
        warnings.append("Used page-text fallback for structured segments.")
    pages = load_paper_pages(profile, source_id)
    if not pages:
        pages = extract_paper_pages(profile, source_id, backend="auto")
    segments = _segments_from_page_text(source_id, pages)
    save_paper_segments(profile, source_id, segments)
    metadata: dict[str, object] = {
        "structure_backend": "pymupdf_fallback" if pymupdf_available() else "fallback",
        "structured_extracted_at": _now(),
        "structured_extraction_warnings": warnings
        or ["GROBID unavailable or returned no usable segments; used page-text fallback."],
    }
    if grobid_failure:
        metadata["grobid_last_error"] = grobid_failure
        metadata["grobid_last_failed_at"] = _now()
        metadata["grobid_failure_pdf_sha256"] = _paper_pdf_fingerprint(_source_by_id(profile, source_id)[1])
    if grobid_status:
        metadata["grobid_status"] = _clean_text(grobid_status.get("status")) or (
            "available" if grobid_status.get("available") else "unavailable"
        )
        metadata["grobid_available"] = bool(grobid_status.get("available"))
    _update_source_metadata(profile, source_id, metadata)
    return segments


def _paper_has_pdf(source: ResearchSource) -> bool:
    return bool(_clean_text((source.metadata or {}).get("pdf_asset_ref")))


def _paper_pdf_fingerprint(source: ResearchSource) -> str:
    metadata = source.metadata or {}
    return (
        _clean_text(metadata.get("pdf_sha256"))
        or _clean_text(metadata.get("pdf_asset_ref"))
    )


def _reader_preparation_label(status: str, structure_backend: str = "") -> str:
    if status == "ready":
        return "Structured text ready"
    if status == "fallback" or (structure_backend and structure_backend != "grobid"):
        return "Fallback text ready"
    if status == "failed":
        return "Preparation failed"
    if status == "missing_pdf":
        return "PDF missing"
    return "PDF ready"


def _reader_preparation_summary(
    source: ResearchSource,
    pages: list[PaperPage],
    segments: list[PaperSegment],
) -> dict[str, object]:
    metadata = dict(source.metadata or {})
    pdf_fingerprint = _paper_pdf_fingerprint(source)
    marker = _clean_text(metadata.get("reading_artifacts_pdf_sha256"))
    pdf_changed = bool(marker and pdf_fingerprint and marker != pdf_fingerprint)
    has_pdf = _paper_has_pdf(source)
    needs_prepare = bool(has_pdf and (not pages or not segments or pdf_changed))
    structure_backend = _clean_text(metadata.get("structure_backend"))
    status = _clean_text(metadata.get("reading_artifacts_status")) or ""
    if not has_pdf:
        status = "missing_pdf"
    elif needs_prepare:
        status = "pending"
    elif not status:
        status = "fallback" if structure_backend and structure_backend != "grobid" else "ready"
    warnings = _clean_list(metadata.get("reading_artifacts_warnings")) + _clean_list(
        metadata.get("structured_extraction_warnings")
    )
    total_pages = max(
        [
            int(metadata.get("page_count") or 0),
            int(metadata.get("reading_artifacts_page_count") or 0),
            *[page.page for page in pages],
            1,
        ]
    )
    return {
        "ready": bool(has_pdf and not needs_prepare and (pages or segments)),
        "needs_prepare": needs_prepare,
        "status": status,
        "label": _reader_preparation_label(status, structure_backend),
        "pages": len(pages),
        "segments": len(segments),
        "total_pages": total_pages,
        "structure_backend": structure_backend,
        "pdf_fingerprint": pdf_fingerprint,
        "pdf_changed": pdf_changed,
        "warnings": warnings,
    }


def ensure_paper_reading_artifacts(
    profile: str | Path,
    source_id: str,
    *,
    prefer_grobid: bool = True,
    force_grobid: bool = False,
    target_lang: str = "",
    progress_callback: Any | None = None,
) -> dict[str, object]:
    """Ensure page text and reading segments exist for the PDF reader.

    The helper is intentionally idempotent: when pages, segments, and ready
    metadata already match the current PDF fingerprint, it returns without
    touching profile files. GROBID is treated as an enhancement; if it is not
    configured or fails, the reader keeps working through page-text fallback.
    """

    def emit_progress(
        phase: str,
        label: str,
        current: int,
        total: int = 3,
        *,
        saved: int = 0,
    ) -> None:
        if not callable(progress_callback):
            return
        progress_callback(
            {
                "phase": phase,
                "label": label,
                "message": label,
                "source_id": source_id,
                "current": current,
                "total": total,
                "saved": saved,
            }
        )

    _, source = _source_by_id(profile, source_id)
    source_metadata = dict(source.metadata or {})
    pdf_fingerprint = _paper_pdf_fingerprint(source)
    if not _paper_has_pdf(source):
        emit_progress("failed", "Preparation failed", 0, saved=0)
        return {
            "source_id": source_id,
            "ready": False,
            "status": "missing_pdf",
            "pages": 0,
            "segments": 0,
            "structure_backend": _clean_text(source_metadata.get("structure_backend")),
            "warnings": ["No PDF asset is attached."],
        }

    pages = load_paper_pages(profile, source_id)
    segments = load_paper_segments(profile, source_id)
    marker = _clean_text(source_metadata.get("reading_artifacts_pdf_sha256"))
    pdf_changed = bool(marker and pdf_fingerprint and marker != pdf_fingerprint)
    current_structure_backend = _clean_text(source_metadata.get("structure_backend"))
    skip_recent_grobid_failure = bool(
        prefer_grobid
        and not force_grobid
        and current_structure_backend
        and current_structure_backend != "grobid"
        and pages
        and segments
        and not pdf_changed
        and _metadata_has_recent_grobid_failure(source_metadata, pdf_fingerprint)
    )
    needs_pages = not pages or pdf_changed
    needs_segments = (
        not segments
        or pdf_changed
        or bool(prefer_grobid and current_structure_backend != "grobid" and not skip_recent_grobid_failure)
    )
    warnings: list[str] = []

    if needs_pages:
        emit_progress("extracting_pages", "Extracting page text...", 1, saved=0)
        try:
            pages = extract_paper_pages(profile, source_id, backend="auto")
        except Exception as exc:
            warnings.append(f"Page extraction failed: {exc}")

    _, source = _source_by_id(profile, source_id)
    source_metadata = dict(source.metadata or {})
    if skip_recent_grobid_failure and not needs_pages:
        emit_progress(
            "fallback_ready",
            "Using current fallback text; recent GROBID failure was not retried.",
            2,
            saved=len(segments),
        )
    if needs_segments:
        segment_backend = "grobid" if prefer_grobid else "fallback"
        segment_label = "Saving fallback text..."
        if segment_backend == "grobid":
            segment_label = (
                "Forcing GROBID full-text upgrade..."
                if force_grobid
                else "Running GROBID full-text extraction..."
            )
        emit_progress(
            "running_grobid" if segment_backend == "grobid" else "saving_segments",
            segment_label,
            2,
            saved=len(segments),
        )
        try:
            segments = extract_paper_segments(profile, source_id, backend=segment_backend)
        except Exception as exc:
            warnings.append(f"Structured extraction failed: {exc}")
            if not segments:
                try:
                    emit_progress("saving_segments", "Saving fallback text...", 2, saved=0)
                    segments = extract_paper_segments(profile, source_id, backend="fallback")
                except Exception as fallback_exc:
                    warnings.append(f"Page-text fallback failed: {fallback_exc}")

    migration_lang = _clean_text(target_lang) or _clean_text(source_metadata.get("target_lang")) or "zh"
    migration_summary = migrate_legacy_translations_to_segments(profile, source_id, target_lang=migration_lang)

    _, source = _source_by_id(profile, source_id)
    metadata = dict(source.metadata or {})
    structure_backend = _clean_text(metadata.get("structure_backend"))
    structured_warnings = _clean_list(metadata.get("structured_extraction_warnings"))
    rect_count = sum(1 for segment in segments if segment.rects)
    structure_rect_count = 0
    structure_anchor_warnings: list[str] = []
    if structure_backend == "grobid" and segments and rect_count == 0:
        try:
            structure_rect_count = sum(
                1
                for unit in build_paper_structure_units(profile, source_id)
                if unit.rects
            )
        except Exception as exc:
            structure_anchor_warnings.append(
                f"Layout structure anchor check failed: {exc}"
            )
    coordinate_summary = {
        "segments_with_rects": rect_count,
        "segments_without_rects": max(0, len(segments) - rect_count),
        "structure_units_with_rects": structure_rect_count,
    }
    coordinate_warnings: list[str] = structure_anchor_warnings
    if structure_backend == "grobid" and segments:
        if rect_count == 0 and structure_rect_count > 0:
            coordinate_warnings.append(
                "GROBID returned structured text without segment coordinates; Reader will use layout-grounded structure anchors for navigation and translation overlays."
            )
        elif rect_count == 0:
            coordinate_warnings.append(
                "GROBID returned structured text without PDF coordinates; Reader navigation will fall back to page-level anchors."
            )
        elif rect_count < len(segments):
            coordinate_warnings.append(
                "Some GROBID segments did not include PDF coordinates; those anchors will fall back to page-level navigation."
            )
    status = "ready"
    if structure_backend and structure_backend != "grobid":
        status = "fallback"
    if warnings:
        status = "failed" if not pages else "fallback"
    ready_metadata: dict[str, object] = {
        "reading_artifacts_status": status,
        "reading_artifacts_pdf_sha256": pdf_fingerprint,
        "reading_artifacts_page_count": len(pages),
        "reading_artifacts_segment_count": len(segments),
    }
    if not _clean_text(metadata.get("reading_artifacts_ready_at")) or needs_pages or needs_segments or warnings:
        ready_metadata["reading_artifacts_ready_at"] = _now()
    if warnings:
        ready_metadata["reading_artifacts_warnings"] = warnings
    elif metadata.get("reading_artifacts_warnings"):
        ready_metadata["reading_artifacts_warnings"] = []
    _update_source_metadata_if_changed(profile, source_id, ready_metadata)
    emit_progress(
        "done" if status != "failed" else "failed",
        _reader_preparation_label(status, structure_backend),
        3 if status != "failed" else 0,
        saved=len(segments),
    )

    return {
        "source_id": source_id,
        "ready": bool(pages) or bool(segments),
        "status": status,
        "pages": len(pages),
        "segments": len(segments),
        "structure_backend": structure_backend,
        "coordinate_extraction": coordinate_summary,
        "translation_migration": migration_summary,
        "warnings": warnings + structured_warnings + coordinate_warnings,
    }


@dataclass
class GrobidDocument:
    source_id: str
    tei_xml: str
    generated_at: str = ""


def grobid_readiness(url: str | None = None) -> dict[str, object]:
    """Return display-ready readiness information for a GROBID service."""

    base = _clean_text(url or os.getenv("NBLANE_GROBID_URL")) or "http://127.0.0.1:8070"
    endpoint = base.rstrip("/") + "/api/isalive"
    badges: list[str] = []
    badge_details: list[dict[str, str]] = []
    try:
        with urllib.request.urlopen(endpoint, timeout=2) as response:
            status_code = int(getattr(response, "status", 200))
            body = response.read(64).decode("utf-8", errors="ignore").strip().lower()
    except Exception as exc:
        message = f"GROBID unavailable: {exc}"
        _append_badge(badges, badge_details, "grobid_unavailable", detail=message)
        return {
            "available": False,
            "status": "unavailable",
            "url": base,
            "endpoint": endpoint,
            "message": message,
            "badges": badges,
            "badge_details": badge_details,
        }
    alive = status_code < 500 and (not body or "true" in body or "alive" in body)
    if not alive:
        message = f"GROBID unavailable: isalive returned HTTP {status_code}"
        if body:
            message += f" with body {body[:80]}"
        _append_badge(badges, badge_details, "grobid_unavailable", detail=message)
        return {
            "available": False,
            "status": "unavailable",
            "url": base,
            "endpoint": endpoint,
            "http_status": status_code,
            "message": message,
            "badges": badges,
            "badge_details": badge_details,
        }
    return {
        "available": True,
        "status": "available",
        "url": base,
        "endpoint": endpoint,
        "http_status": status_code,
        "message": "GROBID available.",
        "badges": badges,
        "badge_details": badge_details,
    }


def grobid_available(url: str | None = None) -> bool:
    """Return True when a configured GROBID service responds."""

    return bool(grobid_readiness(url).get("available"))


def _grobid_fulltext_timeout_seconds() -> float:
    configured = _positive_float(os.getenv("NBLANE_GROBID_FULLTEXT_TIMEOUT_SECONDS"))
    return configured if configured is not None else GROBID_FULLTEXT_TIMEOUT_SECONDS_DEFAULT


def process_grobid_fulltext(profile: str | Path, source_id: str) -> GrobidDocument:
    """Call GROBID ``processFulltextDocument`` for one paper PDF."""

    base = _clean_text(os.getenv("NBLANE_GROBID_URL")) or "http://127.0.0.1:8070"
    pdf_bytes = load_paper_pdf_bytes(profile, source_id)
    boundary = "----nblane-paper-boundary"
    fields = {
        "teiCoordinates": "p,head,figure,formula,biblStruct",
    }
    chunks: list[bytes] = []
    chunks.append(
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="input"; filename="paper.pdf"\r\n'
            "Content-Type: application/pdf\r\n\r\n"
        ).encode("utf-8")
        + pdf_bytes
        + b"\r\n"
    )
    for name, value in fields.items():
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(chunks)
    request = urllib.request.Request(
        base.rstrip("/") + "/api/processFulltextDocument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_grobid_fulltext_timeout_seconds()) as response:
        tei = response.read().decode("utf-8", errors="replace")
    return GrobidDocument(source_id=source_id, tei_xml=tei, generated_at=_now())


def _tei_text(node: ET.Element) -> str:
    return " ".join(" ".join(node.itertext()).split())


def _tei_local_name(node: ET.Element) -> str:
    return str(node.tag).rsplit("}", 1)[-1].lower()


def _tei_float(value: object) -> float:
    text_value = _clean_text(value)
    if not text_value:
        return 0.0
    match = re.search(r"-?\d+(?:\.\d+)?", text_value)
    return float(match.group(0)) if match else 0.0


def _tei_page_models(root: ET.Element) -> dict[int, dict[str, float]]:
    models: dict[int, dict[str, float]] = {}
    for node in root.iter():
        if _tei_local_name(node) != "surface":
            continue
        raw_page = (
            node.attrib.get("n")
            or node.attrib.get("{http://www.w3.org/XML/1998/namespace}id")
            or node.attrib.get("xml:id")
            or ""
        )
        match = re.search(r"\d+", str(raw_page))
        if not match:
            continue
        page = int(match.group(0))
        ulx = _tei_float(node.attrib.get("ulx"))
        uly = _tei_float(node.attrib.get("uly"))
        lrx = _tei_float(node.attrib.get("lrx"))
        lry = _tei_float(node.attrib.get("lry"))
        width = lrx - ulx if lrx > ulx else _tei_float(node.attrib.get("width"))
        height = lry - uly if lry > uly else _tei_float(node.attrib.get("height"))
        if width > 0 and height > 0:
            models[page] = {"width": width, "height": height}
    return models


def _grobid_coord_rects(coords: object, page_models: dict[int, dict[str, float]]) -> list[dict[str, object]]:
    rects: list[dict[str, object]] = []
    for chunk in re.split(r";\s*", _clean_text(coords)):
        if not chunk:
            continue
        parts = [part.strip() for part in chunk.split(",")]
        if len(parts) < 5:
            continue
        try:
            page = int(float(parts[0]))
            x = float(parts[1])
            y = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])
        except (TypeError, ValueError):
            continue
        if page < 1 or width <= 0 or height <= 0:
            continue
        model = page_models.get(page) or {}
        page_width = float(model.get("width") or 0)
        page_height = float(model.get("height") or 0)
        if page_width <= 0 or page_height <= 0:
            rect: dict[str, object] = {
                "page": page,
                "x": x,
                "y": y,
                "w": width,
                "h": height,
            }
        else:
            rect = _rect_payload((x, y, x + width, y + height), page_width=page_width, page_height=page_height) or {}
            rect["page"] = page
        if rect:
            rects.append(rect)
    return rects


def _grobid_node_rects(node: ET.Element, page_models: dict[int, dict[str, float]]) -> list[dict[str, object]]:
    rects = _grobid_coord_rects(node.attrib.get("coords"), page_models)
    if rects:
        return rects
    merged: list[dict[str, object]] = []
    for child in node.iter():
        if child is node:
            continue
        merged.extend(_grobid_coord_rects(child.attrib.get("coords"), page_models))
    return merged


def _grobid_page_from_rects(rects: list[dict[str, object]]) -> int:
    pages = [int(row.get("page") or 0) for row in rects if str(row.get("page") or "").strip().isdigit()]
    return min(pages) if pages else 0


def _grobid_first_page_hint(node: ET.Element, page_models: dict[int, dict[str, float]]) -> int:
    rect_page = _grobid_page_from_rects(_grobid_node_rects(node, page_models))
    if rect_page:
        return rect_page
    own_page = _tei_int_attr(node, "n", "facs", "target")
    if own_page:
        return own_page
    for child in node.iter():
        if child is node:
            continue
        child_page = _grobid_page_from_rects(_grobid_node_rects(child, page_models)) or _tei_int_attr(
            child,
            "n",
            "facs",
            "target",
        )
        if child_page:
            return child_page
    return 0


def _tei_int_attr(node: ET.Element | None, *names: str) -> int:
    if node is None:
        return 0
    for name in names:
        value = _clean_text(node.attrib.get(name))
        if not value:
            continue
        match = re.search(r"\d+", value)
        if match:
            return int(match.group(0))
    return 0


def _tei_first_direct_child(node: ET.Element, local_name: str) -> ET.Element | None:
    for child in list(node):
        if _tei_local_name(child) == local_name:
            return child
    return None


def _tei_first_descendant(node: ET.Element, local_name: str) -> ET.Element | None:
    for child in node.iter():
        if child is not node and _tei_local_name(child) == local_name:
            return child
    return None


def grobid_tei_to_segments(source_id: str, tei_xml: str) -> list[PaperSegment]:
    """Convert a small useful subset of GROBID TEI to paper segments."""

    if not _clean_text(tei_xml):
        return []
    root = ET.fromstring(tei_xml)
    body = _tei_first_descendant(root, "body")
    if body is None:
        return []
    page_models = _tei_page_models(root)
    segments: list[PaperSegment] = []
    order = 0
    slug = source_slug(source_id)

    def append_segment(
        node: ET.Element,
        *,
        kind: str,
        section_path: list[str],
        text: str = "",
        page_hint: int = 0,
        require_rects: bool = False,
    ) -> None:
        nonlocal order
        clean_text = _clean_text(text) or _tei_text(node)
        if not clean_text:
            return
        rects = _grobid_node_rects(node, page_models)
        if require_rects and not rects:
            return
        page = (
            _grobid_page_from_rects(rects)
            or page_hint
            or _tei_int_attr(node, "n", "facs", "target")
        )
        order += 1
        locator = f"p. {page}" if page else ""
        if section_path:
            locator = (locator + " " if locator else "") + "§ " + " / ".join(section_path)
        segments.append(
            PaperSegment(
                segment_id=f"seg:{slug}:{order:05d}",
                source_id=source_id,
                page=page,
                order=order,
                section_path=list(section_path),
                kind=kind,
                text=clean_text,
                locator=locator or f"§ {order}",
                rects=rects,
                metadata={"grobid_tag": _tei_local_name(node)},
            )
        )

    def walk_figure(figure: ET.Element, section_path: list[str], page_hint: int) -> None:
        figure_page = _grobid_page_from_rects(_grobid_node_rects(figure, page_models)) or page_hint
        for child in list(figure):
            local = _tei_local_name(child)
            if local in {"head", "figdesc"}:
                append_segment(child, kind="caption", section_path=section_path, page_hint=figure_page)
            elif local == "p":
                append_segment(child, kind="caption", section_path=section_path, page_hint=figure_page)
            elif local == "formula":
                append_segment(child, kind="formula", section_path=section_path, page_hint=figure_page)

    def walk_container(container: ET.Element, section_path: list[str], page_hint: int = 0) -> None:
        for child in list(container):
            local = _tei_local_name(child)
            if local == "div":
                div_page = _grobid_first_page_hint(child, page_models) or page_hint
                head = _tei_first_direct_child(child, "head")
                title = _tei_text(head) if head is not None else ""
                next_path = list(section_path)
                if head is not None and title:
                    next_path.append(title)
                    append_segment(
                        head,
                        kind="heading",
                        section_path=next_path,
                        text=title,
                        page_hint=div_page,
                        require_rects=False,
                    )
                walk_container(child, next_path, page_hint=div_page)
            elif local == "p":
                append_segment(child, kind="paragraph", section_path=section_path, page_hint=page_hint)
            elif local == "figure":
                walk_figure(child, section_path, page_hint)
            elif local == "formula":
                append_segment(child, kind="formula", section_path=section_path, page_hint=page_hint)

    walk_container(body, [])
    return segments


def grobid_tei_to_bibliography(source_id: str, tei_xml: str) -> list[dict[str, object]]:
    """Extract lightweight bibliography rows from GROBID TEI references."""

    if not _clean_text(tei_xml):
        return []
    root = ET.fromstring(tei_xml)
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    rows: list[dict[str, object]] = []
    for index, item in enumerate(root.findall(".//tei:listBibl/tei:biblStruct", ns), start=1):
        title = _tei_text(item.find(".//tei:title", ns)) if item.find(".//tei:title", ns) is not None else ""
        if not title:
            continue
        authors = []
        for name in item.findall(".//tei:author//tei:persName", ns):
            clean = _tei_text(name)
            if clean:
                authors.append(clean)
        year = ""
        date_node = item.find(".//tei:date", ns)
        if date_node is not None:
            year = _clean_text(date_node.attrib.get("when") or date_node.attrib.get("from"))[:4]
        rows.append(
            {
                "id": f"grobid-ref:{source_slug(source_id)}:{index:03d}",
                "source_id": source_id,
                "title": title,
                "authors": authors,
                "year": year,
            }
        )
    return rows


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


def load_paper_annotations(profile: str | Path, source_id: str) -> list[PaperAnnotation]:
    return [
        ann
        for row in _load_jsonl(_jsonl_path(profile, PAPER_ANNOTATIONS_DIRNAME, source_id))
        if (ann := PaperAnnotation.from_dict(row)) is not None
    ]


def save_paper_annotations(
    profile: str | Path,
    source_id: str,
    rows: list[PaperAnnotation | dict],
) -> Path:
    serialized = []
    for item in rows:
        ann = item if isinstance(item, PaperAnnotation) else PaperAnnotation.from_dict(item)
        if ann is not None:
            serialized.append(ann.to_dict())
    return _write_jsonl(
        _jsonl_path(profile, PAPER_ANNOTATIONS_DIRNAME, source_id),
        serialized,
        action=f"update paper annotations for {source_id}",
    )


def _next_annotation_id(existing: list[PaperAnnotation], source_id: str) -> str:
    prefix = f"ann:{source_slug(source_id)}:"
    max_index = 0
    for row in existing:
        if not row.id.startswith(prefix):
            continue
        try:
            max_index = max(max_index, int(row.id.rsplit(":", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_index + 1:04d}"


def create_paper_annotation(
    profile: str | Path,
    source_id: str,
    selected_text: str,
    *,
    kind: str = "highlight",
    page: int = 0,
    locator: str = "",
    note: str = "",
    color: str = "yellow",
    tags: object = None,
    segment_refs: object = None,
    rects: list[dict[str, object]] | None = None,
) -> PaperAnnotation:
    """Append a paper annotation without modifying the PDF file."""

    _source_by_id(profile, source_id)
    clean_text = _clean_text(selected_text)
    if not clean_text and not _clean_text(note):
        raise ValueError("Paper annotation needs selected text or a note.")
    annotations = load_paper_annotations(profile, source_id)
    ann = PaperAnnotation(
        id=_next_annotation_id(annotations, source_id),
        source_id=source_id,
        kind=_choice(kind, PAPER_ANNOTATION_KINDS, "highlight"),
        page=max(0, int(page or 0)),
        locator=_clean_text(locator) or (f"p. {page}" if page else ""),
        selected_text=clean_text,
        selected_text_hash=text_hash(clean_text),
        note=_clean_text(note),
        color=_clean_text(color) or "yellow",
        rects=[copy.deepcopy(row) for row in (rects or []) if isinstance(row, dict)],
        tags=_clean_list(tags),
        segment_refs=_clean_list(segment_refs),
        created=_now(),
        updated=_now(),
    )
    annotations.append(ann)
    save_paper_annotations(profile, source_id, annotations)
    _update_source_metadata(profile, source_id, {"last_read_at": _now()})
    return ann


def create_chunk_from_annotation(
    profile: str | Path,
    annotation_id: str,
    *,
    title: str = "",
    kind: str = "excerpt",
) -> ResearchChunk:
    """Create a citable ResearchChunk from a saved paper annotation."""

    clean_id = _clean_text(annotation_id)
    for source in load_research_sources(_profile_root(profile)).sources:
        annotations = load_paper_annotations(profile, source.id)
        ann = next((row for row in annotations if row.id == clean_id), None)
        if ann is None:
            continue
        chunk = ResearchChunk(
            id="",
            source_id=source.id,
            text=ann.selected_text or ann.note,
            kind=kind,
            title=_clean_text(title),
            locator=ann.locator,
            metadata={
                "annotation_id": ann.id,
                "segment_refs": list(ann.segment_refs),
                "page": ann.page,
                "rects": copy.deepcopy(ann.rects),
                "selected_text_hash": ann.selected_text_hash,
            },
        )
        existing = load_chunks(profile, source.id)
        chunk.id = _next_chunk_id(existing, source.id)
        existing.append(chunk)
        save_chunks(profile, source.id, existing)
        if chunk.id not in ann.chunk_refs:
            ann.chunk_refs.append(chunk.id)
            ann.updated = _now()
            save_paper_annotations(profile, source.id, annotations)
        return chunk
    raise ValueError(f"Unknown paper annotation: {clean_id}")


def _next_chunk_id(existing: list[ResearchChunk], source_id: str) -> str:
    prefix = f"chunk:{source_slug(source_id)}:"
    max_index = 0
    for chunk in existing:
        if not chunk.id.startswith(prefix):
            continue
        try:
            max_index = max(max_index, int(chunk.id.rsplit(":", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_index + 1:03d}"


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


def _segment_hash_map(profile: str | Path, source_id: str) -> dict[str, PaperSegment]:
    return {segment.segment_id: segment for segment in load_paper_segments(profile, source_id)}


def _mark_translation_status(
    translation: PaperTranslation,
    segments: dict[str, PaperSegment],
) -> PaperTranslation:
    if (translation.scope_type or "segment") == "segment" and translation.segment_id:
        segment = segments.get(translation.segment_id)
        if segment is None:
            translation.status = "stale"
            if "Segment no longer exists." not in translation.warnings:
                translation.warnings.append("Segment no longer exists.")
        elif translation.source_hash != segment.text_hash:
            translation.status = "stale"
            if "Source hash no longer matches the current segment." not in translation.warnings:
                translation.warnings.append("Source hash no longer matches the current segment.")
    return translation


def load_paper_translations(profile: str | Path, source_id: str) -> list[PaperTranslation]:
    segments = _segment_hash_map(profile, source_id)
    rows = []
    for raw in _load_jsonl(_jsonl_path(profile, PAPER_TRANSLATIONS_DIRNAME, source_id)):
        tr = PaperTranslation.from_dict(raw)
        if tr is not None:
            rows.append(_mark_translation_status(tr, segments))
    return rows


def save_paper_translations(
    profile: str | Path,
    source_id: str,
    rows: list[PaperTranslation | dict],
) -> Path:
    serialized = []
    for item in rows:
        tr = item if isinstance(item, PaperTranslation) else PaperTranslation.from_dict(item)
        if tr is not None:
            serialized.append(tr.to_dict())
    return _write_jsonl(
        _jsonl_path(profile, PAPER_TRANSLATIONS_DIRNAME, source_id),
        serialized,
        action=f"update paper translations for {source_id}",
    )


def paper_translations_bulk(
    profile: str | Path,
    source_id: str,
    *,
    target_lang: str = "zh",
) -> tuple[dict[str, object], str]:
    """Return every translation segment for a paper, plus a content-hash ETag.

    Lets the reader pre-load the full translated overlay in one shot instead of
    repeatedly hitting the page-window /payload endpoint as the user scrolls.
    """

    rows = load_paper_translations(profile, source_id)
    inbox = load_research_sources(profile)
    source = inbox.by_id().get(source_id)
    metadata = dict(source.metadata or {}) if source is not None else {}
    page_rows = load_paper_pages(profile, source_id) if source is not None else []
    segment_rows = load_paper_segments(profile, source_id) if source is not None else []
    segment_pages = {seg.segment_id: int(seg.page or 0) for seg in segment_rows}
    total_pages = max(
        [
            int(metadata.get("page_count") or 0),
            int(metadata.get("reading_artifacts_page_count") or 0),
            *[int(row.page or 0) for row in page_rows],
            *[int(row.page or 0) for row in rows],
            *segment_pages.values(),
            0,
        ]
    )

    segments: list[dict[str, object]] = []
    for row in rows:
        if target_lang and row.target_lang and row.target_lang != target_lang:
            continue
        translated = _clean_text(row.translated_text)
        if not translated and row.status not in {"stale", "missing", "failed"}:
            continue
        page_value = int(row.page or 0)
        if page_value <= 0:
            page_value = int(segment_pages.get(row.segment_id, 0) or 0)
        if page_value <= 0:
            for rect in row.rects or []:
                if isinstance(rect, dict):
                    try:
                        candidate = int(rect.get("page") or 0)
                    except (TypeError, ValueError):
                        candidate = 0
                    if candidate > 0:
                        page_value = candidate
                        break
        rects = []
        for rect in row.rects or []:
            if not isinstance(rect, dict):
                continue
            try:
                rects.append(
                    {
                        "x": float(rect.get("x") or 0),
                        "y": float(rect.get("y") or 0),
                        "w": float(rect.get("w") or rect.get("width") or 0),
                        "h": float(rect.get("h") or rect.get("height") or 0),
                        "page": int(rect.get("page") or page_value or 0),
                    }
                )
            except (TypeError, ValueError):
                continue
        font_size = 0.0
        try:
            font_size = float((row.glossary or {}).get("font_size") or 0)
        except (TypeError, ValueError):
            font_size = 0.0
        segments.append(
            {
                "id": row.id,
                "page": page_value,
                "anchor_id": row.anchor_id,
                "scope_type": row.scope_type or "segment",
                "scope_ref": row.scope_ref,
                "segment_id": row.segment_id,
                "rects": rects,
                "translated_text": translated,
                "source_text": row.source_text,
                "source_hash": row.source_hash,
                "status": row.status or ("translated" if translated else "missing"),
                "target_lang": row.target_lang or target_lang,
                "font_size": font_size,
                "created": row.created,
            }
        )

    segments.sort(key=lambda row: (int(row.get("page") or 0), str(row.get("anchor_id") or ""), str(row.get("id") or "")))

    fingerprint_parts = [
        str(_clean_text(metadata.get("pdf_asset_ref"))),
        str(_clean_text(metadata.get("pdf_sha256"))),
        str(int(total_pages)),
        str(len(segments)),
    ]
    for segment in segments:
        fingerprint_parts.append(str(segment.get("id") or ""))
        fingerprint_parts.append(str(segment.get("status") or ""))
        fingerprint_parts.append(str(segment.get("source_hash") or ""))
        fingerprint_parts.append(str(segment.get("created") or ""))
    content_hash = hashlib.sha1("|".join(fingerprint_parts).encode("utf-8")).hexdigest()[:16]

    body = {
        "paper_id": source_id,
        "target_lang": target_lang,
        "content_hash": content_hash,
        "total_pages": int(total_pages),
        "segment_count": len(segments),
        "generated_at": _now(),
        "segments": segments,
    }
    etag = f'W/"{content_hash}"'
    return body, etag


def _next_translation_id(existing: list[PaperTranslation], source_id: str) -> str:
    prefix = f"tr:{source_slug(source_id)}:"
    max_index = 0
    for row in existing:
        if not row.id.startswith(prefix):
            continue
        try:
            max_index = max(max_index, int(row.id.rsplit(":", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_index + 1:04d}"


def _translation_storage_scope(translation: PaperTranslation) -> tuple[str, str]:
    """Return the durable scope used to merge cached translations."""

    scope_type = _clean_text(translation.scope_type) or (
        "segment" if _clean_text(translation.segment_id) else "selection"
    )
    if scope_type == "segment":
        scope_ref = _clean_text(translation.scope_ref) or _clean_text(translation.segment_id)
    else:
        scope_ref = (
            _clean_text(translation.scope_ref)
            or _clean_text(translation.source_hash)
            or text_hash(translation.source_text)
        )
    return scope_type, scope_ref


def _translation_merge_key(translation: PaperTranslation) -> tuple[str, str, str]:
    scope_type, scope_ref = _translation_storage_scope(translation)
    return (scope_type, scope_ref, _clean_text(translation.target_lang) or "zh")


def upsert_paper_translations(
    profile: str | Path,
    source_id: str,
    rows: list[PaperTranslation | dict],
) -> list[PaperTranslation]:
    """Merge accepted translation rows without overwriting stale translations."""

    segments = _segment_hash_map(profile, source_id)
    existing = load_paper_translations(profile, source_id)
    by_key = {_translation_merge_key(row): row for row in existing}
    merged = [row for row in existing]
    for item in rows:
        incoming = _translation_from_input(
            item,
            source_id=source_id,
            fallback_id=_next_translation_id(merged, source_id),
        )
        if incoming is None:
            continue
        incoming.source_id = source_id
        if not incoming.id or incoming.id == "pending":
            incoming.id = _next_translation_id(merged, source_id)
        incoming.scope_type, incoming.scope_ref = _translation_storage_scope(incoming)
        if incoming.scope_type == "segment" and incoming.segment_id and not incoming.scope_ref:
            incoming.scope_ref = incoming.segment_id
        segment = segments.get(incoming.segment_id) if incoming.scope_type == "segment" else None
        if incoming.scope_type == "segment" and incoming.segment_id and segment is None:
            incoming.status = "stale"
            incoming.warnings.append("Skipped: segment no longer exists.")
            merged.append(incoming)
            continue
        if incoming.scope_type == "segment" and segment is not None and incoming.source_hash != segment.text_hash:
            incoming.status = "stale"
            incoming.warnings.append("Skipped: source_hash does not match current segment.")
            merged.append(incoming)
            continue
        key = _translation_merge_key(incoming)
        old = by_key.get(key)
        if old is None:
            merged.append(incoming)
            by_key[key] = incoming
            continue
        for index, row in enumerate(merged):
            if row.id == old.id:
                incoming.id = old.id
                merged[index] = incoming
                by_key[key] = incoming
                break
    save_paper_translations(profile, source_id, merged)
    return merged


def _translation_match_text(value: str) -> str:
    clean = _clean_text(value).casefold()
    return re.sub(r"\s+", " ", clean)


def _translation_text_match_ratio(source_text: str, segment_text: str) -> float:
    source = _translation_match_text(source_text)
    segment = _translation_match_text(segment_text)
    if not source or not segment:
        return 0.0
    if source == segment:
        return 1.0
    shorter, longer = (source, segment) if len(source) <= len(segment) else (segment, source)
    if shorter and shorter in longer:
        return len(shorter) / max(1, len(longer))
    source_tokens = set(source.split())
    segment_tokens = set(segment.split())
    if not source_tokens or not segment_tokens:
        return 0.0
    return len(source_tokens & segment_tokens) / max(1, len(source_tokens | segment_tokens))


def migrate_legacy_translations_to_segments(
    profile: str | Path,
    source_id: str,
    target_lang: str = "zh",
) -> dict[str, object]:
    """Copy safe page/layout translation cache rows onto current segment scopes."""

    clean_lang = _clean_text(target_lang) or "zh"
    segments = load_paper_segments(profile, source_id)
    if not segments:
        return {"migrated": 0, "skipped": 0, "warnings": ["No segments available for translation migration."]}
    translations = load_paper_translations(profile, source_id)
    existing_current = {
        row.segment_id
        for row in translations
        if row.scope_type == "segment"
        and row.segment_id
        and row.target_lang == clean_lang
        and row.status == "translated"
        and _clean_text(row.translated_text)
        and any(segment.segment_id == row.segment_id and segment.text_hash == row.source_hash for segment in segments)
    }
    by_page: dict[int, list[PaperSegment]] = {}
    for segment in segments:
        by_page.setdefault(int(segment.page or 0), []).append(segment)

    savable: list[dict[str, object]] = []
    migrated_ids: list[str] = []
    warnings: list[str] = []
    skipped = 0
    for row in translations:
        if row.target_lang != clean_lang or row.scope_type not in {"layout", "page"}:
            continue
        translated = _clean_text(row.translated_text)
        if not translated or row.status == "failed":
            skipped += 1
            continue
        candidates = by_page.get(int(row.page or 0), [])
        picked: PaperSegment | None = None
        if row.scope_type == "page":
            if len(candidates) == 1:
                picked = candidates[0]
            else:
                for segment in candidates:
                    if _translation_text_match_ratio(row.source_text, segment.text) >= 0.96:
                        picked = segment
                        break
        else:
            best_score = 0.0
            for segment in candidates:
                score = _translation_text_match_ratio(row.source_text, segment.text)
                if score > best_score:
                    best_score = score
                    picked = segment
            if best_score < 0.8:
                picked = None
        if picked is None:
            skipped += 1
            warnings.append(f"Skipped legacy {row.scope_type} translation {row.id}: no safe segment match.")
            continue
        if picked.segment_id in existing_current:
            skipped += 1
            continue
        savable.append(
            {
                "source_id": source_id,
                "scope_type": "segment",
                "scope_ref": picked.segment_id,
                "segment_id": picked.segment_id,
                "page": picked.page,
                "order": picked.order,
                "anchor_id": f"segment:{picked.segment_id}",
                "locator": picked.locator or (f"p. {picked.page}" if picked.page else ""),
                "source_hash": picked.text_hash,
                "source_text": picked.text,
                "target_lang": clean_lang,
                "translated_text": translated,
                "rects": copy.deepcopy(picked.rects),
                "generated_by": f"migration:{row.scope_type}_to_segment",
                "warnings": [f"Migrated from legacy {row.scope_type} translation {row.id}."],
                "status": "translated",
            }
        )
        migrated_ids.append(row.id)
        existing_current.add(picked.segment_id)
    if savable:
        upsert_paper_translations(profile, source_id, savable)
    return {
        "migrated": len(savable),
        "skipped": skipped,
        "migrated_ids": migrated_ids,
        "warnings": warnings,
    }


def _reader_page_set(
    *,
    page: int,
    requested_pages: set[int],
    total_pages: int,
) -> set[int]:
    current = max(1, int(page or 1))
    pages = {current, max(1, current - 1), current + 1}
    for item in requested_pages:
        try:
            requested = int(item)
        except (TypeError, ValueError):
            continue
        if requested > 0:
            pages.add(requested)
    if total_pages:
        pages = {item for item in pages if item <= total_pages}
    return pages


def _metadata_int(metadata: dict[str, object], key: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(metadata.get(key) or default)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


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


def _reader_state_from_metadata(metadata: dict[str, object], *, page: int, target_lang: str) -> dict[str, object]:
    try:
        last_read_page = int(metadata.get("last_read_page") or page or 1)
    except (TypeError, ValueError):
        last_read_page = page or 1
    return {
        "reader_mode": _clean_text(metadata.get("reader_mode")) or "pdf",
        "scale_mode": _clean_text(metadata.get("scale_mode")) or "fit-width",
        "active_tab": _clean_text(metadata.get("active_tab")) or "notes",
        "target_lang": _clean_text(metadata.get("target_lang")) or target_lang or "zh",
        "side_panel_collapsed": _metadata_bool(metadata, "side_panel_collapsed", True),
        "compare_split_ratio": _metadata_int(metadata, "compare_split_ratio", 50, minimum=20, maximum=80),
        "panel_width": _metadata_int(metadata, "panel_width", 340, minimum=280, maximum=560),
        "focused_annotation_id": _clean_text(metadata.get("focused_annotation_id")),
        "focused_chunk_id": _clean_text(metadata.get("focused_chunk_id")),
        "left_rail_collapsed": _metadata_bool(metadata, "left_rail_collapsed", False),
        "active_left_tab": _clean_text(metadata.get("active_left_tab")) or "outline",
        "translation_source_visible": _metadata_bool(metadata, "translation_source_visible", True),
        "active_translation_anchor": _clean_text(metadata.get("active_translation_anchor")),
        "last_visible_pages": [
            int(item)
            for item in metadata.get("last_visible_pages", [])
            if str(item).strip().isdigit()
        ] if isinstance(metadata.get("last_visible_pages"), list) else [],
        "last_read_page": max(1, last_read_page),
        "last_read_at": _clean_text(metadata.get("last_read_at")),
    }


def _reader_outline_from_segments(segments: list[PaperSegment]) -> list[dict[str, object]]:
    """Build a lightweight section outline without including segment body text."""

    outline: list[dict[str, object]] = []
    seen: set[tuple[str, ...]] = set()
    sorted_segments = sorted(segments, key=lambda row: (row.page or 10**9, row.order, row.segment_id))
    page_by_path: dict[tuple[str, ...], int] = {}
    target_by_path: dict[tuple[str, ...], PaperSegment] = {}
    for segment in sorted_segments:
        path = tuple(_clean_text(item) for item in segment.section_path if _clean_text(item))
        for level, _ in enumerate(path, start=1):
            key = path[:level]
            if int(segment.page or 0) > 0:
                page_by_path.setdefault(key, int(segment.page or 0))
                target_by_path.setdefault(key, segment)
    for segment in sorted_segments:
        path = tuple(_clean_text(item) for item in segment.section_path if _clean_text(item))
        for level, _ in enumerate(path, start=1):
            key = path[:level]
            if key in seen:
                continue
            seen.add(key)
            title = key[-1]
            if not _outline_title_allowed(title, kind="heading"):
                continue
            target_segment = target_by_path.get(key) or segment
            page_number = int(page_by_path.get(key) or target_segment.page or segment.page or 0)
            if page_number <= 0:
                continue
            anchor_seed = "|".join(key)
            outline.append(
                {
                    "anchor_id": f"outline:{source_slug(segment.source_id)}:{hashlib.sha256(anchor_seed.encode('utf-8')).hexdigest()[:12]}",
                    "target_anchor_id": f"segment:{target_segment.segment_id}",
                    "segment_id": target_segment.segment_id,
                    "title": title,
                    "page": page_number,
                    "order": int(target_segment.order or segment.order or 0),
                    "level": level,
                    "section_path": list(key),
                }
            )
    if not outline:
        fallback_seen: set[tuple[int, str]] = set()
        for segment in sorted_segments:
            for title, level, offset in _outline_titles_from_segment(segment):
                if not title:
                    continue
                page_number = int(segment.page or 0)
                key = (page_number, title.lower())
                if key in fallback_seen:
                    continue
                fallback_seen.add(key)
                anchor_seed = f"{segment.segment_id}|{offset}|{title}"
                outline.append(
                    {
                        "anchor_id": f"outline:{source_slug(segment.source_id)}:{hashlib.sha256(anchor_seed.encode('utf-8')).hexdigest()[:12]}",
                        "target_anchor_id": f"segment:{segment.segment_id}",
                        "segment_id": segment.segment_id,
                        "title": title,
                        "page": page_number,
                        "order": int(segment.order or 0) * 1000 + int(offset or 0),
                        "level": level,
                        "section_path": [title],
                    }
                )
    return outline


def _reader_outline_from_structure_units(units: list[PaperStructureUnit]) -> list[dict[str, object]]:
    """Build the Reader outline from paper structure headings."""

    outline: list[dict[str, object]] = []
    seen: set[tuple[str, ...]] = set()
    for unit in sorted(units, key=lambda row: (row.page_start, row.order, row.unit_id)):
        if unit.kind != "heading":
            continue
        title = " ".join(_clean_text(unit.text).split())
        if not _outline_title_allowed(title, kind="heading"):
            continue
        path = tuple(unit.section_path or [title])
        for level, _ in enumerate(path, start=1):
            key = path[:level]
            if key in seen:
                continue
            seen.add(key)
            clean_title = key[-1]
            if not _outline_title_allowed(clean_title, kind="heading"):
                continue
            anchor_seed = "|".join(key)
            outline.append(
                {
                    "anchor_id": f"outline:{source_slug(unit.source_id)}:{hashlib.sha256(anchor_seed.encode('utf-8')).hexdigest()[:12]}",
                    "target_anchor_id": unit.unit_id,
                    "segment_id": "",
                    "scope_ref": unit.unit_id,
                    "scope_type": "structure",
                    "title": clean_title,
                    "page": int(unit.page_start or 0),
                    "order": int(unit.order or 0),
                    "level": level,
                    "section_path": list(key),
                }
            )
    return outline


_COMMON_OUTLINE_HEADINGS = {
    "abstract",
    "introduction",
    "background",
    "related work",
    "preliminaries",
    "method",
    "methods",
    "methodology",
    "approach",
    "experiments",
    "experiment",
    "experimental setup",
    "evaluation",
    "results",
    "analysis",
    "discussion",
    "limitations",
    "limitation",
    "conclusion",
    "conclusions",
    "references",
    "appendix",
    "acknowledgements",
    "acknowledgments",
}

_TABLE_OR_FIGURE_HEADINGS = {
    "amount",
    "annotation",
    "action seq.",
    "current pos.",
    "data communication",
    "dataset",
    "depth",
    "destination",
    "done",
    "end frame",
    "image",
    "modality",
    "plan segmentation",
    "primitive",
    "spatial information",
    "start frame",
    "state",
    "task desc.",
    "trajectory",
}


def _outline_title_from_segment(segment: PaperSegment) -> str:
    kind = _clean_text(segment.kind).lower()
    text = " ".join(_clean_text(segment.text).split())
    if int(segment.page or 0) <= 0:
        return ""
    if not _outline_title_allowed(text, kind=kind):
        return ""
    if kind == "heading":
        return text
    if re.match(r"^\d+(?:\.\d+)*\.?\s+[A-Z][A-Za-z0-9 ,:/()\\-]{2,}$", text):
        return text
    letters = re.sub(r"[^A-Za-z]", "", text)
    if len(letters) >= 5 and letters.upper() == letters and not text.endswith("."):
        return text.title() if len(text) > 28 else text
    return ""


def _outline_titles_from_segment(segment: PaperSegment) -> list[tuple[str, int, int]]:
    title = _outline_title_from_segment(segment)
    if title:
        return [(title, _outline_level_for_title(title), 0)]
    return _outline_titles_from_segment_lines(segment)


def _outline_titles_from_segment_lines(segment: PaperSegment) -> list[tuple[str, int, int]]:
    if int(segment.page or 0) <= 0:
        return []
    kind = _clean_text(segment.kind).lower()
    if kind in {"title", "authors", "affiliation", "caption", "formula", "table_cell", "figure_label", "symbol", "page"}:
        return []
    raw_lines = [
        (idx, " ".join(_clean_text(line).split()))
        for idx, line in enumerate(str(segment.text or "").splitlines(), start=1)
    ]
    lines = [(idx, line) for idx, line in raw_lines if line]
    results: list[tuple[str, int, int]] = []
    seen: set[str] = set()
    consumed_lines: set[int] = set()
    for pos, (line_no, line) in enumerate(lines):
        if line_no in consumed_lines:
            continue
        marker_match = re.fullmatch(r"\d+(?:\.\d+)*\.?", line)
        if marker_match and pos + 1 < len(lines):
            next_no, next_line = lines[pos + 1]
            marker = line.rstrip(".")
            if _section_marker_allowed(marker) and _line_looks_like_outline_heading(next_line, numbered=True, page=int(segment.page or 0), marker=marker):
                title = f"{marker} {_outline_display_title(next_line)}"
                if _outline_title_allowed(title, kind="heading"):
                    clean_key = title.lower()
                    if clean_key not in seen:
                        seen.add(clean_key)
                        results.append((title, _outline_level_for_title(title), line_no * 10))
                        consumed_lines.add(next_no)
                continue
        inline_match = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$", line)
        if inline_match:
            marker = inline_match.group(1)
            title_text = _outline_display_title(inline_match.group(2).strip())
            title = f"{marker} {title_text}"
            if _section_marker_allowed(marker) and _line_looks_like_outline_heading(title_text, numbered=True, page=int(segment.page or 0), marker=marker) and _outline_title_allowed(title, kind="heading"):
                clean_key = title.lower()
                if clean_key not in seen:
                    seen.add(clean_key)
                    results.append((title, _outline_level_for_title(title), line_no * 10))
                continue
        if _line_looks_like_outline_heading(line, numbered=False, page=int(segment.page or 0)):
            title = _outline_display_title(line)
            if _outline_title_allowed(title, kind="heading"):
                clean_key = title.lower()
                if clean_key not in seen:
                    seen.add(clean_key)
                    results.append((title, _outline_level_for_title(title), line_no * 10))
    return results[:12]


def _outline_level_for_title(title: str) -> int:
    clean = " ".join(_clean_text(title).split())
    match = re.match(r"^(\d+(?:\.\d+)*)", clean)
    if match:
        return max(1, min(4, match.group(1).count(".") + 1))
    if re.match(r"^[A-Z]\s+", clean):
        return 2
    return 1


def _outline_display_title(title: str) -> str:
    clean = " ".join(_clean_text(title).split())
    letters = re.sub(r"[^A-Za-z]", "", clean)
    if letters and letters.upper() == letters and len(letters) >= 4:
        return clean.title()
    return clean


def _section_marker_allowed(marker: str) -> bool:
    clean = marker.rstrip(".")
    first = clean.split(".", 1)[0]
    if not first.isdigit() or int(first) <= 0:
        return False
    return len(first) <= 1


def _line_looks_like_outline_heading(line: str, *, numbered: bool, page: int, marker: str = "") -> bool:
    clean = " ".join(_clean_text(line).split())
    if not clean or len(clean) > 88:
        return False
    lowered = clean.lower().strip(" .:")
    if lowered in _TABLE_OR_FIGURE_HEADINGS:
        return False
    if not _outline_title_allowed(clean, kind="heading"):
        return False
    if re.search(r"@\w|https?://|www\.|[{}%/]", clean, flags=re.IGNORECASE):
        return False
    if re.search(r"\[[0-9,;:\-\s]+\]", clean):
        return False
    if clean.endswith((".", ",", ";")):
        return False
    words = clean.split()
    if len(words) > 10:
        return False
    if numbered:
        if page == 1 and lowered not in _COMMON_OUTLINE_HEADINGS:
            return False
        if re.fullmatch(r"[\W\d_]+", clean):
            return False
        if marker and "." not in marker and lowered not in _COMMON_OUTLINE_HEADINGS and len(words) <= 1:
            return False
        if marker and "." not in marker and ("：" in clean or ":" in clean) and len(clean) > 20:
            return False
        return bool(re.match(r"^[A-Z0-9\u4e00-\u9fff]", clean))
    if lowered in _COMMON_OUTLINE_HEADINGS:
        return True
    if page == 1:
        return lowered in {"abstract", "introduction"}
    letters = re.sub(r"[^A-Za-z]", "", clean)
    if not re.match(r"^[A-Z\u4e00-\u9fff]", clean):
        return False
    if re.search(r"\d", clean):
        return False
    if letters and letters.upper() == letters and len(letters) >= 4 and 2 <= len(words) <= 6:
        return True
    return False


def _outline_title_allowed(title: str, *, kind: str = "") -> bool:
    clean = " ".join(_clean_text(title).split())
    if not clean or len(clean) > 96:
        return False
    clean_kind = _clean_text(kind).lower()
    if clean_kind in {"title", "authors", "affiliation", "caption", "formula", "table_cell", "figure_label", "symbol", "page"}:
        return False
    if re.fullmatch(r"\d+(?:\.\d+)*\.?", clean):
        return False
    if re.match(r"^(figure|fig\.?|table|algorithm|equation|appendix)\s*\d*[\s.:,-]", clean, flags=re.IGNORECASE):
        return False
    if re.fullmatch(r"[A-Za-z][A-Za-z -]{1,24}\.", clean):
        return False
    if re.search(r"@\w|https?://|www\.", clean, flags=re.IGNORECASE):
        return False
    if len(clean.split()) <= 2 and clean.endswith("."):
        return False
    return True


def _translation_revision(profile: str | Path, source_id: str, target_lang: str) -> str:
    parts = [source_id, target_lang]
    for dirname in (PAPER_PAGES_DIRNAME, PAPER_SEGMENTS_DIRNAME, PAPER_STRUCTURE_DIRNAME, PAPER_TRANSLATIONS_DIRNAME):
        path = _jsonl_path(profile, dirname, source_id)
        try:
            stat = path.stat()
        except FileNotFoundError:
            parts.append(f"{dirname}:missing")
            continue
        parts.append(f"{dirname}:{stat.st_mtime_ns}:{stat.st_size}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def _translation_unit_status(row: dict[str, object] | None, source_hash: str) -> str:
    if row is None:
        return "missing"
    status = _choice(row.get("status"), PAPER_TRANSLATION_STATUSES, "translated")
    if status == "failed":
        return "failed"
    if status == "stale":
        return "stale"
    if _clean_text(row.get("source_hash")) and _clean_text(row.get("source_hash")) != source_hash:
        return "stale"
    if not translation_text_from_row(row):
        return "missing"
    return "translated"


def _default_page_model(page: int) -> dict[str, object]:
    return {"page": int(page), "width": 612.0, "height": 792.0, "rotation": 0}


def _page_models_from_pdf(
    profile: str | Path,
    source_id: str,
    pages: set[int] | list[int] | tuple[int, ...],
) -> list[dict[str, object]]:
    requested_pages = {
        int(item)
        for item in (pages or [])
        if str(item).strip().isdigit() and int(item) > 0
    }
    if not requested_pages:
        return []
    try:
        pdf_path = paper_pdf_asset_path(profile, source_id)
    except (FileNotFoundError, ValueError):
        return []
    try:
        import fitz  # type: ignore[import-not-found]  # noqa: F401
    except Exception:
        return []
    models: list[dict[str, object]] = []
    try:
        with fitz.open(str(pdf_path)) as doc:  # type: ignore[name-defined]
            for page_number in sorted(requested_pages):
                if page_number < 1 or page_number > int(doc.page_count):
                    continue
                pdf_page = doc.load_page(page_number - 1)
                rect = pdf_page.rect
                models.append(
                    {
                        "page": page_number,
                        "width": float(rect.width),
                        "height": float(rect.height),
                        "rotation": int(getattr(pdf_page, "rotation", 0) or 0),
                    }
                )
    except Exception:
        return []
    return models


def _page_models_from_layout_units(
    layout_units: list[dict[str, object]],
    pages: list[int],
) -> list[dict[str, object]]:
    by_page: dict[int, dict[str, object]] = {}
    for unit in layout_units:
        try:
            page_number = int(unit.get("page") or 0)
        except (TypeError, ValueError):
            page_number = 0
        if page_number < 1:
            continue
        for raw_rect in unit.get("rects") or []:
            if not isinstance(raw_rect, dict):
                continue
            try:
                width = float(raw_rect.get("page_width") or 0)
                height = float(raw_rect.get("page_height") or 0)
            except (TypeError, ValueError):
                width = 0.0
                height = 0.0
            if width > 0 and height > 0:
                by_page.setdefault(
                    page_number,
                    {"page": page_number, "width": width, "height": height, "rotation": 0},
                )
                break
    return [by_page.get(page_number, _default_page_model(page_number)) for page_number in pages]


def _rect_payload(
    bbox: object,
    *,
    page_width: float,
    page_height: float,
) -> dict[str, object] | None:
    if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
        return None
    try:
        x0, y0, x1, y1 = [float(value) for value in bbox[:4]]
    except (TypeError, ValueError):
        return None
    if x1 <= x0 or y1 <= y0 or page_width <= 0 or page_height <= 0:
        return None
    width = x1 - x0
    height = y1 - y0
    return {
        "x": x0,
        "y": y0,
        "w": width,
        "h": height,
        "x_pct": x0 / page_width,
        "y_pct": y0 / page_height,
        "w_pct": width / page_width,
        "h_pct": height / page_height,
        "page_width": page_width,
        "page_height": page_height,
    }


def _rect_area(rect: dict[str, object]) -> float:
    try:
        return max(0.0, float(rect.get("w") or 0)) * max(0.0, float(rect.get("h") or 0))
    except (TypeError, ValueError):
        return 0.0


def _rect_overlap_ratio(rect: dict[str, object], other: dict[str, object]) -> float:
    try:
        ax0 = float(rect.get("x") or 0)
        ay0 = float(rect.get("y") or 0)
        ax1 = ax0 + float(rect.get("w") or 0)
        ay1 = ay0 + float(rect.get("h") or 0)
        bx0 = float(other.get("x") or 0)
        by0 = float(other.get("y") or 0)
        bx1 = bx0 + float(other.get("w") or 0)
        by1 = by0 + float(other.get("h") or 0)
    except (TypeError, ValueError):
        return 0.0
    overlap_w = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    overlap_h = max(0.0, min(ay1, by1) - max(ay0, by0))
    area = _rect_area(rect)
    return (overlap_w * overlap_h / area) if area else 0.0


def _rect_union_payload(
    rects: list[dict[str, object]],
    *,
    page_width: float,
    page_height: float,
) -> dict[str, object] | None:
    if not rects:
        return None
    try:
        x0 = min(float(rect.get("x") or 0) for rect in rects)
        y0 = min(float(rect.get("y") or 0) for rect in rects)
        x1 = max(float(rect.get("x") or 0) + float(rect.get("w") or 0) for rect in rects)
        y1 = max(float(rect.get("y") or 0) + float(rect.get("h") or 0) for rect in rects)
    except (TypeError, ValueError):
        return None
    return _rect_payload((x0, y0, x1, y1), page_width=page_width, page_height=page_height)


def _figure_caption_candidates(layer: dict[str, object]) -> list[dict[str, object]]:
    captions: list[dict[str, object]] = []
    for raw_line in layer.get("lines") or []:
        if not isinstance(raw_line, dict):
            continue
        text = _clean_text(raw_line.get("text"))
        if not re.match(r"^(fig(?:ure)?\.?|table)\s*\d+", text, flags=re.IGNORECASE):
            continue
        rect = _rect_from_layer_line(raw_line)
        if rect is None:
            continue
        captions.append({"text": text, "rect": rect})
    return captions


def _expanded_figure_rect(
    image_rect: dict[str, object],
    captions: list[dict[str, object]],
    *,
    page_width: float,
    page_height: float,
) -> dict[str, object] | None:
    near_rects = [copy.deepcopy(image_rect)]
    try:
        image_x = float(image_rect.get("x") or 0)
        image_y = float(image_rect.get("y") or 0)
        image_w = float(image_rect.get("w") or 0)
        image_h = float(image_rect.get("h") or 0)
    except (TypeError, ValueError):
        return None
    for caption in captions:
        rect = caption.get("rect") if isinstance(caption, dict) else None
        if not isinstance(rect, dict):
            continue
        try:
            cap_x = float(rect.get("x") or 0)
            cap_y = float(rect.get("y") or 0)
            cap_w = float(rect.get("w") or 0)
            cap_h = float(rect.get("h") or 0)
        except (TypeError, ValueError):
            continue
        horizontal_overlap = max(0.0, min(image_x + image_w, cap_x + cap_w) - max(image_x, cap_x))
        if horizontal_overlap < min(image_w, cap_w) * 0.25:
            continue
        gap_below = cap_y - (image_y + image_h)
        gap_above = image_y - (cap_y + cap_h)
        if -24 <= gap_below <= 90 or -24 <= gap_above <= 70:
            near_rects.append(copy.deepcopy(rect))
    return _rect_union_payload(near_rects, page_width=page_width, page_height=page_height)


def _caption_region_rect(
    caption: dict[str, object],
    *,
    candidates: list[dict[str, object]],
    page_width: float,
    page_height: float,
) -> dict[str, object] | None:
    """Infer a figure/table crop around a caption when the PDF has vector art."""

    rect = caption.get("rect") if isinstance(caption, dict) else None
    if not isinstance(rect, dict):
        return None
    try:
        cap_x = float(rect.get("x") or 0)
        cap_y = float(rect.get("y") or 0)
        cap_w = float(rect.get("w") or 0)
        cap_h = float(rect.get("h") or 0)
    except (TypeError, ValueError):
        return None
    if cap_w <= 0 or cap_h <= 0 or page_width <= 0 or page_height <= 0:
        return None
    text_value = _clean_text(caption.get("text")).lower()
    is_table = text_value.startswith("table")
    center = cap_x + cap_w / 2
    width = min(page_width - 24, max(cap_w + 80, page_width * 0.68))
    x0 = max(12.0, min(page_width - width - 12.0, center - width / 2))
    x1 = min(page_width - 12.0, x0 + width)
    if is_table:
        y0 = max(12.0, cap_y - 8.0)
        y1 = min(page_height - 12.0, cap_y + cap_h + min(260.0, page_height * 0.38))
    else:
        y0 = max(12.0, cap_y - min(260.0, page_height * 0.38))
        y1 = min(page_height - 12.0, cap_y + cap_h + 8.0)
    if y1 - y0 < max(36.0, cap_h * 2.0):
        return None
    fallback = _rect_payload((x0, y0, x1, y1), page_width=page_width, page_height=page_height)
    if fallback is None:
        return None
    if any(_rect_overlap_ratio(candidate, fallback) > 0.45 for candidate in candidates):
        return None
    return fallback


def _nearest_caption_text(rect: dict[str, object], captions: list[dict[str, object]]) -> str:
    try:
        x = float(rect.get("x") or 0)
        y = float(rect.get("y") or 0)
        w = float(rect.get("w") or 0)
        h = float(rect.get("h") or 0)
    except (TypeError, ValueError):
        return ""
    best: tuple[float, str] | None = None
    for caption in captions:
        cap_rect = caption.get("rect") if isinstance(caption, dict) else None
        if not isinstance(cap_rect, dict):
            continue
        try:
            cap_x = float(cap_rect.get("x") or 0)
            cap_y = float(cap_rect.get("y") or 0)
        except (TypeError, ValueError):
            continue
        distance = abs(cap_y - (y + h)) + abs(cap_x - x) * 0.15
        text_value = _clean_text(caption.get("text"))
        if text_value and (best is None or distance < best[0]):
            best = (distance, text_value)
    return best[1] if best else ""


def _bbox_values(bbox: object) -> tuple[float, float, float, float] | None:
    if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
        return None
    try:
        x0, y0, x1, y1 = [float(value) for value in bbox[:4]]
    except (TypeError, ValueError):
        return None
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def _bbox_union(values: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float] | None:
    if not values:
        return None
    return (
        min(row[0] for row in values),
        min(row[1] for row in values),
        max(row[2] for row in values),
        max(row[3] for row in values),
    )


def _line_direction(line: dict[str, object]) -> tuple[list[float], float]:
    raw = line.get("dir")
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        return [1.0, 0.0], 0.0
    try:
        dx = float(raw[0])
        dy = float(raw[1])
    except (TypeError, ValueError):
        return [1.0, 0.0], 0.0
    rotation = math.degrees(math.atan2(dy, dx))
    if abs(rotation) < 0.25:
        rotation = 0.0
    return [round(dx, 4), round(dy, 4)], round(rotation, 2)


def _text_boundary_needs_space(left: str, right: str) -> bool:
    left_clean = str(left or "")
    right_clean = str(right or "")
    if not left_clean or not right_clean:
        return False
    if left_clean[-1].isspace() or right_clean[0].isspace():
        return False
    if re.search(r"[\u4e00-\u9fff]$", left_clean) or re.match(r"^[\u4e00-\u9fff]", right_clean):
        return False
    if left_clean[-1] in "([{/<-" or right_clean[0] in ".,;:!?)]}%/":
        return False
    return bool(re.search(r"[A-Za-z0-9]$", left_clean) and re.match(r"^[A-Za-z0-9]", right_clean))


def _join_pdf_spans_with_geometry(span_parts: list[tuple[str, tuple[float, float, float, float], float]]) -> str:
    """Join PyMuPDF spans without losing natural word spaces."""

    out = ""
    previous_bbox: tuple[float, float, float, float] | None = None
    previous_size = 0.0
    for raw_text, bbox, font_size in span_parts:
        part = str(raw_text or "")
        if not part:
            continue
        if not out:
            out = part
            previous_bbox = bbox
            previous_size = font_size
            continue
        separator = ""
        if previous_bbox is not None:
            gap = float(bbox[0]) - float(previous_bbox[2])
            threshold = max(1.2, min(8.0, max(previous_size, font_size, 8.0) * 0.16))
            if gap > threshold and _text_boundary_needs_space(out, part):
                separator = " "
        elif _text_boundary_needs_space(out, part):
            separator = " "
        out = f"{out}{separator}{part}"
        previous_bbox = bbox
        previous_size = font_size
    return re.sub(r"[ \t]{2,}", " ", out).strip()


def _join_pdf_lines_as_text(lines: list[str]) -> str:
    """Join visual PDF lines into source text while repairing hyphenated wraps."""

    cleaned = [_clean_text(line) for line in lines if _clean_text(line)]
    if not cleaned:
        return ""
    out = cleaned[0]
    for line in cleaned[1:]:
        if re.search(r"[A-Za-z]-$", out) and re.match(r"^[a-z]", line):
            out = out[:-1] + line
        elif re.search(r"[\u4e00-\u9fff]$", out) and re.match(r"^[\u4e00-\u9fff]", line):
            out += line
        elif out.endswith(("(", "[", "{", "/", "-")) or line.startswith((".", ",", ";", ":", "!", "?", ")", "]", "}", "%")):
            out += line
        else:
            out += " " + line
    return re.sub(r"[ \t]{2,}", " ", out).strip()


def _pdf_page_text_layer_payload(pdf_page: object, page_number: int) -> dict[str, object]:
    """Return the PyMuPDF text layer used by both Reader selection fallback and layout units."""

    rect = getattr(pdf_page, "rect")
    page_width = float(getattr(rect, "width", 0.0) or 0.0)
    page_height = float(getattr(rect, "height", 0.0) or 0.0)
    data = pdf_page.get_text("dict")
    image_rects: list[dict[str, object]] = []
    spans: list[dict[str, object]] = []
    lines: list[dict[str, object]] = []
    for block_index, block in enumerate(data.get("blocks", []) if isinstance(data, dict) else []):
        if not isinstance(block, dict):
            continue
        if block.get("type") != 0:
            image_rect = _rect_payload(
                block.get("bbox", ()),
                page_width=page_width,
                page_height=page_height,
            )
            if image_rect is not None:
                image_rects.append(image_rect)
            continue
        for line_index, line in enumerate(block.get("lines", []) or []):
            if not isinstance(line, dict):
                continue
            direction, rotation = _line_direction(line)
            line_parts: list[str] = []
            line_span_parts: list[tuple[str, tuple[float, float, float, float], float]] = []
            line_bboxes: list[tuple[float, float, float, float]] = []
            max_font_size = 0.0
            span_indexes: list[int] = []
            for span in line.get("spans", []) or []:
                if not isinstance(span, dict):
                    continue
                body = str(span.get("text") or "")
                if not body.strip():
                    continue
                span_bbox = _bbox_values(span.get("bbox", ()))
                if span_bbox is None:
                    continue
                x0, y0, x1, y1 = span_bbox
                font_size = float(span.get("size") or max(1.0, y1 - y0))
                span_indexes.append(len(spans))
                spans.append(
                    {
                        "text": body,
                        "x": x0,
                        "y": y0,
                        "w": x1 - x0,
                        "h": y1 - y0,
                        "font_size": font_size,
                        "block": block_index,
                        "line": line_index,
                        "dir": direction,
                        "rotation": rotation,
                    }
                )
                line_parts.append(body)
                line_span_parts.append((body, span_bbox, font_size))
                line_bboxes.append(span_bbox)
                max_font_size = max(max_font_size, font_size)
            text = _join_pdf_spans_with_geometry(line_span_parts) if line_span_parts else "".join(line_parts).strip()
            if not text:
                continue
            line_bbox = _bbox_values(line.get("bbox", ())) or _bbox_union(line_bboxes)
            if line_bbox is None:
                continue
            line_rect = _rect_payload(line_bbox, page_width=page_width, page_height=page_height)
            if line_rect is None:
                continue
            lines.append(
                {
                    "text": text,
                    "x": line_rect["x"],
                    "y": line_rect["y"],
                    "w": line_rect["w"],
                    "h": line_rect["h"],
                    "font_size": max_font_size or float(line_rect["h"] or 0),
                    "block": block_index,
                    "line": line_index,
                    "span_indexes": span_indexes,
                    "dir": direction,
                    "rotation": rotation,
                    "rect": line_rect,
                }
            )
    return {
        "page": int(page_number),
        "width": page_width,
        "height": page_height,
        "image_rects": image_rects[:1000],
        "spans": spans[:4000],
        "lines": lines[:4000],
    }


def extract_paper_page_text_layer(profile: str | Path, source_id: str, page: int) -> dict[str, object]:
    """Extract the Reader text layer for one PDF page with PyMuPDF span and line coordinates."""

    try:
        import fitz  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - optional dependency guard
        raise RuntimeError("PyMuPDF is not available.") from exc
    pdf_path = paper_pdf_asset_path(profile, source_id)
    try:
        page_number = max(1, int(page or 1))
    except (TypeError, ValueError):
        page_number = 1
    with fitz.open(str(pdf_path)) as doc:
        if page_number > int(doc.page_count):
            raise ValueError("page not found")
        return _pdf_page_text_layer_payload(doc[page_number - 1], page_number)


def _layout_text_lines(block: dict[str, object]) -> tuple[str, float]:
    lines: list[str] = []
    max_font = 0.0
    for raw_line in block.get("lines") or []:
        if not isinstance(raw_line, dict):
            continue
        parts: list[tuple[str, tuple[float, float, float, float], float]] = []
        fallback_parts: list[str] = []
        for raw_span in raw_line.get("spans") or []:
            if not isinstance(raw_span, dict):
                continue
            body = str(raw_span.get("text") or "")
            fallback_parts.append(body)
            try:
                font_size = float(raw_span.get("size") or 0)
            except (TypeError, ValueError):
                font_size = 0.0
            max_font = max(max_font, font_size)
            bbox = _bbox_values(raw_span.get("bbox", ()))
            if body and bbox is not None:
                parts.append((body, bbox, font_size))
        line = _join_pdf_spans_with_geometry(parts) if parts else "".join(fallback_parts).strip()
        if line:
            lines.append(line)
    return "\n".join(lines).strip(), max_font


def _layout_text_is_translatable(value: str) -> bool:
    clean = re.sub(r"\s+", "", value or "")
    if not clean:
        return False
    if re.fullmatch(r"https?://\S+|www\.\S+|\S+@\S+", clean, flags=re.IGNORECASE):
        return False
    if clean.isdigit() and len(clean) <= 4:
        return False
    if not re.search(r"[A-Za-z0-9\u4e00-\u9fff]", clean):
        return False
    if len(clean) <= 2:
        return False
    return True


def _layout_kind(text: str, font_size: float, *, table: bool = False, symbol: bool = False) -> str:
    clean = _clean_text(text)
    if table:
        return "table_cell"
    if symbol:
        return "symbol"
    if re.match(r"^(figure|fig\.|table)\s+\d+", clean, flags=re.IGNORECASE):
        return "caption"
    if font_size >= 15:
        return "title"
    return "paragraph"


def _front_matter_layout_kind(
    *,
    page: int,
    text: str,
    rect: dict[str, object],
    font_size: float,
    current_kind: str,
) -> str:
    """Classify first-page title/author metadata before translation grouping."""

    if int(page or 0) != 1:
        return current_kind
    try:
        y_pct = float(rect.get("y_pct"))
    except (TypeError, ValueError):
        try:
            y_pct = float(rect.get("y") or 0) / max(1.0, float(rect.get("page_height") or 0))
        except (TypeError, ValueError):
            y_pct = 1.0
    if y_pct > 0.36:
        return current_kind
    clean = " ".join(_clean_text(text).split())
    if not clean:
        return current_kind
    if font_size >= 15:
        return "title"
    lower = clean.lower()
    affiliation_markers = (
        "university",
        "institute",
        "college",
        "department",
        "school",
        "laboratory",
        "lab",
        "academy",
        "research",
        "corresponding",
        "equal contribution",
    )
    looks_affiliation = any(marker in lower for marker in affiliation_markers) or bool(
        re.search(r"@\w|\.edu\b|\.ac\.", lower)
    )
    nameish_words = re.findall(r"[A-Z][A-Za-z.'-]+", clean)
    has_author_separators = "," in clean or ";" in clean or re.search(r"\band\b", lower)
    sentence_like = clean.endswith(".") and len(clean.split()) > 6
    if looks_affiliation and len(clean) <= 240:
        return "affiliation"
    if has_author_separators and len(nameish_words) >= 2 and not sentence_like:
        return "authors"
    return current_kind


def _candidate_primary_rect(candidate: dict[str, object]) -> dict[str, object] | None:
    for rect in candidate.get("rects") or []:
        if isinstance(rect, dict) and _rect_area(rect) > 0:
            return rect
    return None


def _layout_candidates_same_band(previous: dict[str, object], current: dict[str, object]) -> bool:
    prev_rect = _candidate_primary_rect(previous)
    cur_rect = _candidate_primary_rect(current)
    if prev_rect is None or cur_rect is None:
        return False
    try:
        prev_y = float(prev_rect.get("y") or 0)
        prev_h = float(prev_rect.get("h") or 0)
        cur_y = float(cur_rect.get("y") or 0)
        prev_x = float(prev_rect.get("x") or 0)
        cur_x = float(cur_rect.get("x") or 0)
        prev_w = float(prev_rect.get("w") or 0)
        cur_w = float(cur_rect.get("w") or 0)
        page_width = max(float(prev_rect.get("page_width") or 0), float(cur_rect.get("page_width") or 0), 1.0)
        font_size = max(float(previous.get("font_size") or 0), float(current.get("font_size") or 0), 8.0)
    except (TypeError, ValueError):
        return False
    vertical_gap = cur_y - (prev_y + prev_h)
    if vertical_gap < -6 or vertical_gap > max(14.0, font_size * 1.25):
        return False
    prev_center = prev_x + prev_w / 2
    cur_center = cur_x + cur_w / 2
    center_delta = abs(prev_center - cur_center)
    overlap = max(0.0, min(prev_x + prev_w, cur_x + cur_w) - max(prev_x, cur_x))
    return center_delta <= max(48.0, page_width * 0.18) or overlap >= min(prev_w, cur_w) * 0.28


def _merge_layout_candidate_pair(previous: dict[str, object], current: dict[str, object], *, kind: str) -> dict[str, object]:
    rects = [
        copy.deepcopy(rect)
        for rect in [*_clean_rect_list(previous.get("rects")), *_clean_rect_list(current.get("rects"))]
    ]
    merged = {
        **previous,
        "source_text": "\n".join(
            part
            for part in [_clean_text(previous.get("source_text")), _clean_text(current.get("source_text"))]
            if part
        ),
        "kind": kind,
        "rects": rects,
        "sort_y": min(float(previous.get("sort_y") or 0), float(current.get("sort_y") or 0)),
        "sort_x": min(float(previous.get("sort_x") or 0), float(current.get("sort_x") or 0)),
        "font_size": max(float(previous.get("font_size") or 0), float(current.get("font_size") or 0)),
        "line_count": int(previous.get("line_count") or 1) + int(current.get("line_count") or 1),
    }
    if kind in {"authors", "affiliation"}:
        merged["translatable"] = False
        merged["preserve_source"] = True
    return merged


def _clean_rect_list(value: object) -> list[dict[str, object]]:
    return [copy.deepcopy(row) for row in value or [] if isinstance(row, dict)]


def _merge_adjacent_layout_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    if not candidates:
        return []
    rows = sorted(candidates, key=lambda row: (int(row.get("page") or 0), float(row.get("sort_y") or 0), float(row.get("sort_x") or 0)))
    merged: list[dict[str, object]] = []
    for candidate in rows:
        if not merged:
            merged.append(candidate)
            continue
        previous = merged[-1]
        prev_kind = _clean_text(previous.get("kind"))
        cur_kind = _clean_text(candidate.get("kind"))
        same_page = int(previous.get("page") or 0) == int(candidate.get("page") or 0)
        if same_page and prev_kind == cur_kind == "title" and _layout_candidates_same_band(previous, candidate):
            merged[-1] = _merge_layout_candidate_pair(previous, candidate, kind="title")
            continue
        if same_page and {prev_kind, cur_kind} <= {"authors", "affiliation"} and _layout_candidates_same_band(previous, candidate):
            merged[-1] = _merge_layout_candidate_pair(
                previous,
                candidate,
                kind="affiliation" if "affiliation" in {prev_kind, cur_kind} else "authors",
            )
            continue
        merged.append(candidate)
    return merged


def _layout_scope_ref(page: int, order: int, source_hash: str) -> str:
    short_hash = _clean_text(source_hash).removeprefix("sha256:")[:12] or f"{order:05d}"
    return f"layout:v2:{int(page)}:{int(order):05d}:{short_hash}"


def _layout_unit_from_candidate(candidate: dict[str, object], order: int) -> dict[str, object] | None:
    source_text = _clean_text(candidate.get("source_text"))
    if not source_text:
        return None
    try:
        page = int(candidate.get("page") or 0)
    except (TypeError, ValueError):
        page = 0
    if page < 1:
        return None
    source_hash = text_hash(source_text)
    scope_ref = _layout_scope_ref(page, order, source_hash)
    translatable = bool(candidate.get("translatable", True))
    preserve_source = bool(candidate.get("preserve_source", not translatable))
    unit: dict[str, object] = {
        "unit_id": scope_ref,
        "anchor_id": scope_ref,
        "scope_type": "layout",
        "scope_ref": scope_ref,
        "segment_id": "",
        "page": page,
        "order": order,
        "section_path": [],
        "kind": _clean_text(candidate.get("kind")) or "paragraph",
        "locator": f"p. {page}",
        "source_hash": source_hash,
        "source_text": source_text,
        "target_lang": "",
        "translated_text": source_text if not translatable and preserve_source else "",
        "status": "translated" if not translatable else "missing",
        "status_reason": "",
        "rects": copy.deepcopy(candidate.get("rects") or []),
        "translatable": translatable,
        "display_source": preserve_source,
    }
    for key in ("table_id", "row", "col", "row_span", "col_span", "rotation", "dir", "font_size", "line_count"):
        if key in candidate:
            unit[key] = candidate[key]
    return unit


def _rect_from_layer_line(line: dict[str, object]) -> dict[str, object] | None:
    rect = line.get("rect")
    if isinstance(rect, dict):
        return copy.deepcopy(rect)
    try:
        page_width = float(line.get("page_width") or 0)
        page_height = float(line.get("page_height") or 0)
        x0 = float(line.get("x") or 0)
        y0 = float(line.get("y") or 0)
        width = float(line.get("w") or 0)
        height = float(line.get("h") or 0)
    except (TypeError, ValueError):
        return None
    return _rect_payload((x0, y0, x0 + width, y0 + height), page_width=page_width, page_height=page_height)


def _layout_skip_text_layer_line(text: str, line: dict[str, object], rect: dict[str, object]) -> bool:
    clean = _clean_text(text)
    if not clean:
        return True
    try:
        rotation = abs(float(line.get("rotation") or 0.0))
    except (TypeError, ValueError):
        rotation = 0.0
    if rotation > 2.0 and abs(rotation - 180.0) > 2.0:
        return True
    try:
        font_size = float(line.get("font_size") or 0.0)
    except (TypeError, ValueError):
        font_size = 0.0
    if font_size and font_size < 5.5:
        return True
    if _rect_area(rect) < 18:
        return True
    compact = re.sub(r"\s+", "", clean)
    if re.fullmatch(r"https?://\S+|www\.\S+|\S+@\S+", compact, flags=re.IGNORECASE):
        return True
    if re.fullmatch(r"(arxiv|doi|issn|isbn)[:\w./-]+", compact, flags=re.IGNORECASE):
        return True
    return False


def _line_group_rect(lines: list[dict[str, object]]) -> dict[str, object] | None:
    rects = [
        rect
        for line in lines
        if isinstance(line, dict) and isinstance(rect := _rect_from_layer_line(line), dict)
    ]
    if not rects:
        return None
    try:
        page_width = float(rects[0].get("page_width") or 0)
        page_height = float(rects[0].get("page_height") or 0)
        x0 = min(float(rect.get("x") or 0) for rect in rects)
        y0 = min(float(rect.get("y") or 0) for rect in rects)
        x1 = max(float(rect.get("x") or 0) + float(rect.get("w") or 0) for rect in rects)
        y1 = max(float(rect.get("y") or 0) + float(rect.get("h") or 0) for rect in rects)
    except (TypeError, ValueError):
        return None
    return _rect_payload((x0, y0, x1, y1), page_width=page_width, page_height=page_height)


def _same_layout_paragraph(previous: dict[str, object], current: dict[str, object]) -> bool:
    prev_rect = _rect_from_layer_line(previous)
    cur_rect = _rect_from_layer_line(current)
    if prev_rect is None or cur_rect is None:
        return False
    prev_text = _clean_text(previous.get("text"))
    cur_text = _clean_text(current.get("text"))
    if not prev_text or not cur_text:
        return False
    prev_kind = _layout_kind(prev_text, float(previous.get("font_size") or 0))
    cur_kind = _layout_kind(cur_text, float(current.get("font_size") or 0))
    if prev_kind == "title" or cur_kind == "title":
        if prev_kind != cur_kind:
            return False
        try:
            prev_center = float(prev_rect.get("x") or 0) + float(prev_rect.get("w") or 0) / 2
            cur_center = float(cur_rect.get("x") or 0) + float(cur_rect.get("w") or 0) / 2
            page_width = max(float(prev_rect.get("page_width") or 0), float(cur_rect.get("page_width") or 0), 1.0)
            prev_y = float(prev_rect.get("y") or 0)
            prev_h = float(prev_rect.get("h") or 0)
            cur_y = float(cur_rect.get("y") or 0)
            font_size = max(float(previous.get("font_size") or 0), float(current.get("font_size") or 0), 12.0)
        except (TypeError, ValueError):
            return False
        return -6 <= cur_y - (prev_y + prev_h) <= max(14.0, font_size * 1.15) and abs(prev_center - cur_center) <= max(56.0, page_width * 0.20)
    if prev_kind == "caption" or cur_kind == "caption":
        return False
    try:
        prev_x = float(prev_rect.get("x") or 0)
        prev_y = float(prev_rect.get("y") or 0)
        prev_w = float(prev_rect.get("w") or 0)
        prev_h = float(prev_rect.get("h") or 0)
        cur_x = float(cur_rect.get("x") or 0)
        cur_y = float(cur_rect.get("y") or 0)
        cur_w = float(cur_rect.get("w") or 0)
        font_size = max(float(previous.get("font_size") or 0), float(current.get("font_size") or 0), 8.0)
    except (TypeError, ValueError):
        return False
    vertical_gap = cur_y - (prev_y + prev_h)
    if vertical_gap < -2 or vertical_gap > max(12.0, font_size * 1.3):
        return False
    if abs(cur_x - prev_x) > max(9.0, font_size * 1.1):
        return False
    if min(prev_w, cur_w) > 24 and max(prev_w, cur_w) / max(1.0, min(prev_w, cur_w)) > 2.8:
        return False
    return True


def _layout_candidates_from_text_layer(
    *,
    page: int,
    layer: dict[str, object],
    accepted_table_rects: list[dict[str, object]],
) -> list[dict[str, object]]:
    image_rects = [
        rect
        for raw in layer.get("image_rects") or []
        if isinstance(raw, dict) and _rect_area(raw) > 0
        if isinstance(rect := copy.deepcopy(raw), dict)
    ]
    lines_by_block: dict[int, list[dict[str, object]]] = {}
    for raw_line in layer.get("lines") or []:
        if not isinstance(raw_line, dict):
            continue
        text = _clean_text(raw_line.get("text"))
        rect = _rect_from_layer_line(raw_line)
        if rect is None or _layout_skip_text_layer_line(text, raw_line, rect):
            continue
        if any(_rect_overlap_ratio(rect, table_rect) > 0.45 for table_rect in accepted_table_rects):
            continue
        try:
            block_index = int(raw_line.get("block") or 0)
        except (TypeError, ValueError):
            block_index = 0
        lines_by_block.setdefault(block_index, []).append(raw_line)

    candidates: list[dict[str, object]] = []
    for _, block_lines in sorted(lines_by_block.items()):
        sorted_lines = sorted(block_lines, key=lambda row: (float(row.get("y") or 0), float(row.get("x") or 0), int(row.get("line") or 0)))
        groups: list[list[dict[str, object]]] = []
        for line in sorted_lines:
            if not groups or not _same_layout_paragraph(groups[-1][-1], line):
                groups.append([line])
            else:
                groups[-1].append(line)
        for group in groups:
            rect = _line_group_rect(group)
            if rect is None:
                continue
            text = _join_pdf_lines_as_text([
                _clean_text(row.get("text"))
                for row in group
                if _clean_text(row.get("text"))
            ])
            if not text:
                continue
            font_size = max((float(row.get("font_size") or 0) for row in group), default=0.0)
            inside_image = any(_rect_overlap_ratio(rect, image_rect) > 0.55 for image_rect in image_rects)
            translatable = _layout_text_is_translatable(text) and not inside_image
            if not translatable and re.search(r"[A-Za-z\u4e00-\u9fff]", text):
                if not inside_image:
                    continue
            kind = "figure_label" if inside_image else _layout_kind(text, font_size, symbol=not translatable)
            kind = _front_matter_layout_kind(
                page=page,
                text=text,
                rect=rect,
                font_size=font_size,
                current_kind=kind,
            )
            preserve_source = (not translatable) and not inside_image
            if kind in {"authors", "affiliation"}:
                translatable = False
                preserve_source = True
            candidates.append(
                {
                    "page": page,
                    "source_text": text,
                    "kind": kind,
                    "rects": [rect],
                    "translatable": translatable,
                    "preserve_source": preserve_source,
                    "sort_y": rect["y"],
                    "sort_x": rect["x"],
                    "font_size": font_size,
                    "line_count": len(group),
                    "rotation": group[0].get("rotation", 0),
                    "dir": copy.deepcopy(group[0].get("dir") or [1.0, 0.0]),
                }
            )
    return _merge_adjacent_layout_candidates(candidates)


def build_paper_layout_units(
    profile: str | Path,
    source_id: str,
    *,
    pages: set[int] | list[int] | tuple[int, ...] | None = None,
) -> list[dict[str, object]]:
    """Extract positioned translation units from the original PDF page layout."""

    try:
        pdf_path = paper_pdf_asset_path(profile, source_id)
    except (FileNotFoundError, ValueError):
        return []
    try:
        import fitz  # type: ignore[import-not-found]
    except Exception:
        return []

    requested_pages = {
        int(item)
        for item in (pages or [])
        if str(item).strip().isdigit() and int(item) > 0
    }
    units: list[dict[str, object]] = []
    try:
        with fitz.open(str(pdf_path)) as doc:
            for index, pdf_page in enumerate(doc, start=1):
                if requested_pages and index not in requested_pages:
                    continue
                page_rect = pdf_page.rect
                page_width = float(page_rect.width)
                page_height = float(page_rect.height)
                candidates: list[dict[str, object]] = []
                accepted_table_rects: list[dict[str, object]] = []
                try:
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        tables = list(getattr(pdf_page.find_tables(), "tables", []) or [])
                except Exception:
                    tables = []
                for table_index, table in enumerate(tables, start=1):
                    try:
                        row_count = int(getattr(table, "row_count", 0) or 0)
                        col_count = int(getattr(table, "col_count", 0) or 0)
                        cell_texts = table.extract()
                        cells = list(getattr(table, "cells", []) or [])
                    except Exception:
                        continue
                    flat_texts = [
                        _clean_text(cell)
                        for row in cell_texts
                        for cell in (row if isinstance(row, list) else [])
                    ]
                    if row_count < 2 and len([cell for cell in flat_texts if cell]) < 3:
                        continue
                    table_rect = _rect_payload(
                        getattr(table, "bbox", ()),
                        page_width=page_width,
                        page_height=page_height,
                    )
                    if table_rect is not None:
                        accepted_table_rects.append(table_rect)
                    for row_index in range(row_count):
                        row_values = cell_texts[row_index] if row_index < len(cell_texts) and isinstance(cell_texts[row_index], list) else []
                        for col_index in range(col_count):
                            text = _clean_text(row_values[col_index] if col_index < len(row_values) else "")
                            if not text:
                                continue
                            cell_offset = row_index * col_count + col_index
                            rect = _rect_payload(
                                cells[cell_offset] if cell_offset < len(cells) else (),
                                page_width=page_width,
                                page_height=page_height,
                            )
                            if rect is None:
                                continue
                            translatable = _layout_text_is_translatable(text)
                            candidates.append(
                                {
                                    "page": index,
                                    "source_text": text,
                                    "kind": _layout_kind(text, 0, table=True, symbol=not translatable),
                                    "rects": [rect],
                                    "translatable": translatable,
                                    "sort_y": rect["y"],
                                    "sort_x": rect["x"],
                                    "table_id": f"table:{index}:{table_index}",
                                    "row": row_index,
                                    "col": col_index,
                                    "row_span": 1,
                                    "col_span": 1,
                                }
                            )
                try:
                    layer = _pdf_page_text_layer_payload(pdf_page, index)
                except Exception:
                    layer = {}
                candidates.extend(
                    _layout_candidates_from_text_layer(
                        page=index,
                        layer=layer,
                        accepted_table_rects=accepted_table_rects,
                    )
                )
                candidates.sort(key=lambda row: (float(row.get("sort_y") or 0), float(row.get("sort_x") or 0)))
                for order, candidate in enumerate(candidates, start=1):
                    unit = _layout_unit_from_candidate(candidate, order)
                    if unit is not None:
                        units.append(unit)
    except Exception:
        return []
    return units


def reader_translation_layout_units(layout_units: list[dict[str, object]]) -> list[dict[str, object]]:
    """Return layout units suitable for the normal Reader translation flow.

    The raw PDF layout contains table cells, figure-internal labels, and symbols.
    Those are useful for geometry and debugging overlays, but they make the normal
    paragraph translation view noisy and can regress to page-like chunks.
    """

    rows: list[dict[str, object]] = []
    excluded_kinds = {"table_cell", "figure_label", "symbol"}
    for raw_unit in layout_units:
        if not isinstance(raw_unit, dict):
            continue
        source_text = _clean_text(raw_unit.get("source_text") or raw_unit.get("text"))
        if not source_text:
            continue
        kind = _clean_text(raw_unit.get("kind"))
        if kind in excluded_kinds:
            continue
        translatable = bool(raw_unit.get("translatable", True))
        display_source = bool(raw_unit.get("display_source", not translatable))
        if not translatable and not display_source:
            continue
        rows.append(copy.deepcopy(raw_unit))
    return rows


def _paper_structure_clean_text(text: object) -> str:
    return _join_pdf_lines_as_text(str(text or "").replace("\r\n", "\n").splitlines())


def _paper_structure_locator(page_start: int, page_end: int) -> str:
    return f"p. {page_start}" if page_start == page_end else f"pp. {page_start}-{page_end}"


def _paper_structure_rect_union(rects: list[dict[str, object]]) -> dict[str, object] | None:
    clean_rects = [rect for rect in rects if isinstance(rect, dict) and _rect_area(rect) > 0]
    if not clean_rects:
        return None
    try:
        page_width = max(float(rect.get("page_width") or 0) for rect in clean_rects)
        page_height = max(float(rect.get("page_height") or 0) for rect in clean_rects)
    except (TypeError, ValueError):
        return None
    return _rect_union_payload(clean_rects, page_width=page_width, page_height=page_height)


def _paper_structure_rects_for_page(rects: object, page: int) -> list[dict[str, object]]:
    rows = _clean_rect_list(rects)
    for rect in rows:
        rect.setdefault("page", int(page))
    return rows


def _paper_structure_primary_rect(row: dict[str, object]) -> dict[str, object] | None:
    for rect in row.get("rects") or []:
        if isinstance(rect, dict) and _rect_area(rect) > 0:
            return rect
    return None


def _paper_structure_heading_kind(text: str, *, page: int, font_size: float, layout_kind: str) -> str:
    clean = " ".join(_clean_text(text).split())
    if not clean:
        return layout_kind or "paragraph"
    lower = clean.lower().strip(" .:")
    if re.match(r"^[*∗†‡§¶]\s*", clean) or lower.startswith(("preprint", "under review", "equal contribution", "corresponding author")):
        return "footnote"
    if re.match(r"^(figure|fig\.?|table|algorithm)\s*\d+", clean, flags=re.IGNORECASE):
        return "caption"
    if layout_kind in {"title", "authors", "affiliation", "table_cell", "figure_label", "symbol", "footnote"}:
        return layout_kind
    if lower in _TABLE_OR_FIGURE_HEADINGS and len(clean.split()) <= 4:
        return "table_cell"
    if re.fullmatch(r"\d+(?:\.\d+)*\.?", clean):
        return "heading_marker"
    numbered = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$", clean)
    if numbered:
        marker = numbered.group(1)
        title = numbered.group(2).strip()
        if _section_marker_allowed(marker) and _line_looks_like_outline_heading(title, numbered=True, page=page, marker=marker):
            return "heading"
    if lower in _COMMON_OUTLINE_HEADINGS or lower.startswith(("appendix", "references", "acknowledg")):
        return "heading"
    if font_size >= 13 and _line_looks_like_outline_heading(clean, numbered=False, page=page):
        return "heading"
    return "paragraph"


def _paper_structure_front_matter_kind(
    *,
    page: int,
    text: str,
    rect: dict[str, object] | None,
    font_size: float,
    layout_kind: str,
    seen_title: bool,
) -> str:
    if page != 1 or rect is None:
        return layout_kind
    try:
        y_pct = float(rect.get("y_pct"))
    except (TypeError, ValueError):
        y_pct = 1.0
    if y_pct > 0.38:
        return layout_kind
    clean = " ".join(_clean_text(text).split())
    lower = clean.lower()
    if not clean:
        return layout_kind
    if layout_kind == "title" or (not seen_title and font_size >= 14 and y_pct <= 0.28):
        return "title"
    affiliation_markers = (
        "university",
        "institute",
        "college",
        "department",
        "school",
        "laboratory",
        "laboratories",
        "lab",
        "academy",
        "email",
        "corresponding",
        "equal contribution",
    )
    if any(marker in lower for marker in affiliation_markers) or re.search(r"@\w|\.edu\b|\.ac\.", lower):
        return "affiliation"
    nameish_words = re.findall(r"[A-Z][A-Za-z.'-]+", clean)
    mostly_names = len(nameish_words) >= 2 and len(clean.split()) <= max(12, len(nameish_words) + 4)
    if mostly_names and not clean.endswith(".") and y_pct <= 0.34:
        return "authors"
    return layout_kind


def _paper_structure_kind_for_layout(unit: dict[str, object], *, seen_title: bool) -> str:
    text = _paper_structure_clean_text(unit.get("source_text") or unit.get("text"))
    layout_kind = _clean_text(unit.get("kind")) or "paragraph"
    try:
        page = int(unit.get("page") or 0)
    except (TypeError, ValueError):
        page = 0
    try:
        font_size = float(unit.get("font_size") or 0)
    except (TypeError, ValueError):
        font_size = 0.0
    rect = _paper_structure_primary_rect(unit)
    front_kind = _paper_structure_front_matter_kind(
        page=page,
        text=text,
        rect=rect,
        font_size=font_size,
        layout_kind=layout_kind,
        seen_title=seen_title,
    )
    if front_kind != layout_kind:
        return front_kind
    return _paper_structure_heading_kind(text, page=page, font_size=font_size, layout_kind=layout_kind)


def _paper_structure_candidate_looks_like_table_cell(candidate: dict[str, object]) -> bool:
    kind = _clean_text(candidate.get("kind"))
    if kind not in {"paragraph", "heading", "heading_marker"}:
        return False
    text = " ".join(_clean_text(candidate.get("text")).split())
    if not text:
        return False
    if re.match(r"^(fig(?:ure)?\.?|table|algorithm)\s*\d+", text, flags=re.IGNORECASE):
        return False
    rect = _paper_structure_primary_rect(candidate)
    if rect is None:
        return False
    try:
        width = float(rect.get("w") or 0)
        page_width = float(rect.get("page_width") or 0)
        line_count = int(candidate.get("line_count") or 1)
    except (TypeError, ValueError):
        return False
    if line_count > 2:
        return False
    if page_width and width > page_width * 0.58:
        return False
    tokens = re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+(?:[-/][A-Za-z0-9\u4e00-\u9fff]+)*", text)
    token_count = len(tokens)
    if token_count <= 0:
        return False
    if len(text) > 96 or token_count > 10:
        return False
    if token_count >= 3 and re.search(r"[.!?。！？]$", text):
        return False
    if token_count >= 6 and re.search(
        r"\b(is|are|was|were|has|have|had|can|could|should|would|will|contains|evaluates|studies|proposes?)\b",
        text,
        flags=re.IGNORECASE,
    ):
        return False
    return True


def _paper_structure_distinct_x_count(rows: list[tuple[int, dict[str, object], dict[str, object]]]) -> int:
    centers: list[float] = []
    page_width = 0.0
    for _, _, rect in rows:
        try:
            centers.append(float(rect.get("x") or 0) + float(rect.get("w") or 0) / 2)
            page_width = max(page_width, float(rect.get("page_width") or 0))
        except (TypeError, ValueError):
            continue
    if not centers:
        return 0
    threshold = max(12.0, page_width * 0.025)
    distinct = 0
    last: float | None = None
    for center in sorted(centers):
        if last is None or abs(center - last) > threshold:
            distinct += 1
            last = center
    return distinct


def _paper_structure_row_groups(
    rows: list[tuple[int, dict[str, object], dict[str, object]]],
) -> list[list[tuple[int, dict[str, object], dict[str, object]]]]:
    groups: list[dict[str, object]] = []
    for item in sorted(rows, key=lambda row: (float(row[2].get("y") or 0), float(row[2].get("x") or 0))):
        _, candidate, rect = item
        try:
            center_y = float(rect.get("y") or 0) + float(rect.get("h") or 0) / 2
            height = float(rect.get("h") or 0)
            font_size = float(candidate.get("font_size") or height or 8.0)
        except (TypeError, ValueError):
            continue
        if groups:
            previous = groups[-1]
            threshold = max(4.0, float(previous.get("height") or 0) * 0.75, font_size * 0.70)
            if abs(center_y - float(previous.get("center_y") or 0)) <= threshold:
                items = previous["items"]
                if isinstance(items, list):
                    items.append(item)
                    count = len(items)
                    previous["center_y"] = (float(previous.get("center_y") or 0) * (count - 1) + center_y) / count
                    previous["height"] = max(float(previous.get("height") or 0), height)
                continue
        groups.append({"center_y": center_y, "height": height, "items": [item]})
    return [group["items"] for group in groups if isinstance(group.get("items"), list)]  # type: ignore[list-item]


def _paper_structure_column_groups(
    rows: list[tuple[int, dict[str, object], dict[str, object]]],
) -> list[list[tuple[int, dict[str, object], dict[str, object]]]]:
    groups: list[dict[str, object]] = []
    page_width = 0.0
    for _, _, rect in rows:
        try:
            page_width = max(page_width, float(rect.get("page_width") or 0))
        except (TypeError, ValueError):
            continue
    threshold = max(14.0, page_width * 0.035)
    for item in sorted(rows, key=lambda row: (float(row[2].get("x") or 0) + float(row[2].get("w") or 0) / 2, float(row[2].get("y") or 0))):
        _, _, rect = item
        try:
            center_x = float(rect.get("x") or 0) + float(rect.get("w") or 0) / 2
        except (TypeError, ValueError):
            continue
        if groups and abs(center_x - float(groups[-1].get("center_x") or 0)) <= threshold:
            items = groups[-1]["items"]
            if isinstance(items, list):
                items.append(item)
                count = len(items)
                groups[-1]["center_x"] = (float(groups[-1].get("center_x") or 0) * (count - 1) + center_x) / count
            continue
        groups.append({"center_x": center_x, "items": [item]})
    return [group["items"] for group in groups if isinstance(group.get("items"), list)]  # type: ignore[list-item]


def _paper_structure_table_caption_regions(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    regions: list[dict[str, object]] = []
    for candidate in candidates:
        if _clean_text(candidate.get("kind")) != "caption":
            continue
        text = " ".join(_clean_text(candidate.get("text")).split())
        if not re.match(r"^table\s*\d+", text, flags=re.IGNORECASE):
            continue
        rect = _paper_structure_primary_rect(candidate)
        if rect is None:
            continue
        try:
            page_width = float(rect.get("page_width") or 0)
            page_height = float(rect.get("page_height") or 0)
            cap_x = float(rect.get("x") or 0)
            cap_y = float(rect.get("y") or 0)
            cap_w = float(rect.get("w") or 0)
            cap_h = float(rect.get("h") or 0)
        except (TypeError, ValueError):
            continue
        if page_width <= 0 or page_height <= 0:
            continue
        center = cap_x + cap_w / 2
        width = min(page_width - 24.0, max(cap_w + 120.0, page_width * 0.72))
        x0 = max(12.0, min(page_width - width - 12.0, center - width / 2))
        y0 = max(12.0, cap_y - min(130.0, page_height * 0.18))
        y1 = min(page_height - 12.0, cap_y + cap_h + min(280.0, page_height * 0.38))
        region = _rect_payload((x0, y0, x0 + width, y1), page_width=page_width, page_height=page_height)
        if region is not None:
            region["page"] = int(candidate.get("page_start") or 0)
            regions.append(region)
    return regions


def _paper_structure_rect_inside_region(rect: dict[str, object], region: dict[str, object]) -> bool:
    try:
        cx = float(rect.get("x") or 0) + float(rect.get("w") or 0) / 2
        cy = float(rect.get("y") or 0) + float(rect.get("h") or 0) / 2
        rx0 = float(region.get("x") or 0)
        ry0 = float(region.get("y") or 0)
        rx1 = rx0 + float(region.get("w") or 0)
        ry1 = ry0 + float(region.get("h") or 0)
    except (TypeError, ValueError):
        return False
    return rx0 <= cx <= rx1 and ry0 <= cy <= ry1


def _paper_structure_apply_inferred_table_cells(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    """Mark table-like layout fragments that PyMuPDF did not label as cells."""

    if not candidates:
        return candidates
    by_page: dict[int, list[tuple[int, dict[str, object], dict[str, object]]]] = {}
    for index, candidate in enumerate(candidates):
        if not _paper_structure_candidate_looks_like_table_cell(candidate):
            continue
        rect = _paper_structure_primary_rect(candidate)
        if rect is None:
            continue
        try:
            page = int(candidate.get("page_start") or 0)
        except (TypeError, ValueError):
            page = 0
        if page > 0:
            by_page.setdefault(page, []).append((index, candidate, rect))
    if not by_page:
        return candidates

    caption_regions_by_page: dict[int, list[dict[str, object]]] = {}
    for region in _paper_structure_table_caption_regions(candidates):
        try:
            page = int(region.get("page") or 0)
        except (TypeError, ValueError):
            page = 0
        if page > 0:
            caption_regions_by_page.setdefault(page, []).append(region)

    marked: set[int] = set()
    for page, cells in by_page.items():
        if len(cells) < 4:
            continue
        row_groups = _paper_structure_row_groups(cells)
        dense_rows = [group for group in row_groups if _paper_structure_distinct_x_count(group) >= 2]
        if len(dense_rows) >= 2 and sum(len(group) for group in dense_rows) >= 4:
            for group in dense_rows:
                marked.update(index for index, _, _ in group)

        column_groups = _paper_structure_column_groups(cells)
        dense_columns = [group for group in column_groups if len(group) >= 2]
        if len(dense_columns) >= 2 and sum(len(group) for group in dense_columns) >= 4:
            for group in dense_columns:
                marked.update(index for index, _, _ in group)

        for region in caption_regions_by_page.get(page, []):
            in_region = [item for item in cells if _paper_structure_rect_inside_region(item[2], region) or _rect_overlap_ratio(item[2], region) > 0.35]
            if len(in_region) < 3:
                continue
            region_rows = _paper_structure_row_groups(in_region)
            region_columns = _paper_structure_column_groups(in_region)
            has_rows = any(_paper_structure_distinct_x_count(group) >= 2 for group in region_rows)
            has_columns = len([group for group in region_columns if len(group) >= 2]) >= 2
            if has_rows or has_columns:
                marked.update(index for index, _, _ in in_region)

    if not marked:
        return candidates

    clusters_by_page: dict[int, list[list[int]]] = {}
    for page, cells in by_page.items():
        page_marked = [item for item in cells if item[0] in marked]
        if not page_marked:
            continue
        page_height = 0.0
        try:
            page_height = max(float(item[2].get("page_height") or 0) for item in page_marked)
        except (TypeError, ValueError):
            page_height = 0.0
        cluster_gap = max(32.0, page_height * 0.045)
        clusters: list[list[int]] = []
        previous_bottom: float | None = None
        for index, _, rect in sorted(page_marked, key=lambda item: (float(item[2].get("y") or 0), float(item[2].get("x") or 0))):
            try:
                top = float(rect.get("y") or 0)
                bottom = top + float(rect.get("h") or 0)
            except (TypeError, ValueError):
                top = bottom = 0.0
            if not clusters or (previous_bottom is not None and top - previous_bottom > cluster_gap):
                clusters.append([index])
            else:
                clusters[-1].append(index)
            previous_bottom = max(previous_bottom or bottom, bottom)
        clusters_by_page[page] = clusters

    table_id_by_index: dict[int, str] = {}
    for page, clusters in clusters_by_page.items():
        for cluster_index, indexes in enumerate(clusters, start=1):
            if len(indexes) < 3:
                continue
            table_id = f"table:inferred:{page}:{cluster_index}"
            for index in indexes:
                table_id_by_index[index] = table_id

    out = [copy.deepcopy(candidate) for candidate in candidates]
    for index in marked:
        row = out[index]
        row["kind"] = "table_cell"
        row["translatable"] = False
        row["display_source"] = False
        metadata = _clean_mapping(row.get("metadata"))
        metadata.setdefault("inferred_table_cell", True)
        table_id = table_id_by_index.get(index)
        if table_id:
            metadata.setdefault("table_id", table_id)
        row["metadata"] = metadata
    return out


def _paper_structure_sort_key_factory(candidates: list[dict[str, object]]):
    page_has_columns: dict[int, bool] = {}
    for page in {int(row.get("page_start") or 0) for row in candidates}:
        page_rows = [row for row in candidates if int(row.get("page_start") or 0) == page]
        centers: list[float] = []
        page_width = 0.0
        for row in page_rows:
            rect = _paper_structure_primary_rect(row)
            if rect is None:
                continue
            try:
                width = float(rect.get("w") or 0)
                x = float(rect.get("x") or 0)
                page_width = max(page_width, float(rect.get("page_width") or 0))
            except (TypeError, ValueError):
                continue
            if page_width and width < page_width * 0.58 and row.get("kind") not in {"title", "authors", "affiliation"}:
                centers.append(x + width / 2)
        if page_width and centers:
            left = [value for value in centers if value < page_width * 0.46]
            right = [value for value in centers if value > page_width * 0.54]
            page_has_columns[page] = len(left) >= 2 and len(right) >= 2

    def key(row: dict[str, object]) -> tuple[float, float, float, float, str]:
        page = int(row.get("page_start") or 0)
        rect = _paper_structure_primary_rect(row) or {}
        try:
            x = float(rect.get("x") or row.get("sort_x") or 0)
            y = float(rect.get("y") or row.get("sort_y") or 0)
            width = float(rect.get("w") or 0)
            page_width = float(rect.get("page_width") or 0)
            y_pct = float(rect.get("y_pct") or 0)
        except (TypeError, ValueError):
            x = y = width = page_width = y_pct = 0.0
        kind = _clean_text(row.get("kind"))
        is_front = page == 1 and y_pct <= 0.34 and kind in {"title", "authors", "affiliation"}
        if page_has_columns.get(page) and not is_front and page_width and width < page_width * 0.62:
            column = 0 if x + width / 2 < page_width / 2 else 1
            return (page, 1, column, y, _clean_text(row.get("unit_id")))
        return (page, 0 if is_front else 2, y, x, _clean_text(row.get("unit_id")))

    return key


def _paper_structure_candidates_from_layout(layout_units: list[dict[str, object]], source_id: str) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    seen_title = False
    for raw in sorted(layout_units, key=lambda row: (int(row.get("page") or 0), int(row.get("order") or 0), _clean_text(row.get("unit_id")))):
        if not isinstance(raw, dict):
            continue
        raw_text_value = str(raw.get("source_text") or raw.get("text") or "")
        raw_front_matter_lines = [
            _clean_text(line)
            for line in raw_text_value.replace("\r\n", "\n").splitlines()
            if _clean_text(line)
        ]
        raw_kind = _clean_text(raw.get("kind"))
        if raw_kind in {"authors", "affiliation"} and len(raw_front_matter_lines) > 1:
            try:
                base_order = int(raw.get("order") or 0)
            except (TypeError, ValueError):
                base_order = 0
            for line_index, line_text in enumerate(raw_front_matter_lines, start=1):
                line_raw = {
                    **raw,
                    "source_text": line_text,
                    "text": line_text,
                    "order": base_order * 10 + line_index,
                    "line_count": 1,
                }
                candidates.extend(_paper_structure_candidates_from_layout([line_raw], source_id))
            if any(candidate.get("kind") == "title" for candidate in candidates):
                seen_title = True
            continue
        text = _paper_structure_clean_text(raw_text_value)
        if not text:
            continue
        try:
            page = int(raw.get("page") or 0)
            order = int(raw.get("order") or 0)
        except (TypeError, ValueError):
            continue
        if page < 1:
            continue
        kind = _paper_structure_kind_for_layout(raw, seen_title=seen_title)
        if kind == "title":
            seen_title = True
        rects = _paper_structure_rects_for_page(raw.get("rects"), page)
        translatable = kind in PAPER_STRUCTURE_TRANSLATION_KINDS and _layout_text_is_translatable(text)
        display_source = kind in {"authors", "affiliation"}
        candidates.append(
            {
                "source_id": source_id,
                "kind": kind,
                "page_start": page,
                "page_end": page,
                "order": order,
                "text": text,
                "rects": rects,
                "source_unit_ids": [_clean_text(raw.get("unit_id") or raw.get("scope_ref"))],
                "translatable": translatable,
                "display_source": display_source,
                "sort_x": float((_paper_structure_primary_rect(raw) or {}).get("x") or raw.get("sort_x") or 0),
                "sort_y": float((_paper_structure_primary_rect(raw) or {}).get("y") or raw.get("sort_y") or 0),
                "font_size": raw.get("font_size"),
                "line_count": raw.get("line_count"),
                "metadata": {
                    key: copy.deepcopy(raw.get(key))
                    for key in ("table_id", "row", "col", "row_span", "col_span", "rotation", "dir")
                    if key in raw
                },
            }
        )
    candidates = _paper_structure_apply_inferred_table_cells(candidates)
    candidates.sort(key=_paper_structure_sort_key_factory(candidates))
    return candidates


def _paper_structure_merge_text(left: str, right: str, *, kind: str) -> str:
    if kind == "title":
        return "\n".join(part for part in [_clean_text(left), _clean_text(right)] if part)
    return _join_pdf_lines_as_text([left, right])


def _paper_structure_merge_pair(left: dict[str, object], right: dict[str, object], *, kind: str | None = None) -> dict[str, object]:
    merged_kind = kind or _clean_text(left.get("kind")) or _clean_text(right.get("kind")) or "paragraph"
    rects = [*_clean_rect_list(left.get("rects")), *_clean_rect_list(right.get("rects"))]
    source_ids = [*_clean_list(left.get("source_unit_ids")), *_clean_list(right.get("source_unit_ids"))]
    text = _paper_structure_merge_text(_clean_text(left.get("text")), _clean_text(right.get("text")), kind=merged_kind)
    metadata = _clean_mapping(left.get("metadata"))
    metadata.update(_clean_mapping(right.get("metadata")))
    return {
        **left,
        "kind": merged_kind,
        "page_end": max(int(left.get("page_end") or left.get("page_start") or 0), int(right.get("page_end") or right.get("page_start") or 0)),
        "text": text,
        "rects": rects,
        "source_unit_ids": [item for item in source_ids if item],
        "translatable": merged_kind in PAPER_STRUCTURE_TRANSLATION_KINDS and _layout_text_is_translatable(text),
        "display_source": merged_kind in {"authors", "affiliation"},
        "font_size": max(float(left.get("font_size") or 0), float(right.get("font_size") or 0)),
        "line_count": int(left.get("line_count") or 1) + int(right.get("line_count") or 1),
        "metadata": metadata,
    }


def _paper_structure_same_column(left: dict[str, object], right: dict[str, object]) -> bool:
    left_rect = _paper_structure_primary_rect(left)
    right_rect = _paper_structure_primary_rect(right)
    if left_rect is None or right_rect is None:
        return False
    try:
        lx = float(left_rect.get("x") or 0)
        lw = float(left_rect.get("w") or 0)
        rx = float(right_rect.get("x") or 0)
        rw = float(right_rect.get("w") or 0)
        page_width = max(float(left_rect.get("page_width") or 0), float(right_rect.get("page_width") or 0), 1.0)
    except (TypeError, ValueError):
        return False
    overlap = max(0.0, min(lx + lw, rx + rw) - max(lx, rx))
    if overlap >= min(lw, rw) * 0.40:
        return True
    return abs(lx - rx) <= max(14.0, page_width * 0.035)


def _paper_structure_vertical_gap(left: dict[str, object], right: dict[str, object]) -> float:
    left_rect = _paper_structure_primary_rect(left)
    right_rect = _paper_structure_primary_rect(right)
    if left_rect is None or right_rect is None:
        return 10**9
    try:
        return float(right_rect.get("y") or 0) - (float(left_rect.get("y") or 0) + float(left_rect.get("h") or 0))
    except (TypeError, ValueError):
        return 10**9


def _paper_structure_caption_continuation(left: dict[str, object], right: dict[str, object]) -> bool:
    if int(left.get("page_end") or 0) != int(right.get("page_start") or 0):
        return False
    if _clean_text(right.get("kind")) in {"title", "heading", "caption", "authors", "affiliation", "table_cell", "figure_label", "symbol"}:
        return False
    gap = _paper_structure_vertical_gap(left, right)
    return -3 <= gap <= 24 and _paper_structure_same_column(left, right)


def _paper_structure_paragraph_continuation(left: dict[str, object], right: dict[str, object]) -> bool:
    if int(left.get("page_end") or 0) != int(right.get("page_start") or 0):
        return False
    if _clean_text(left.get("kind")) != "paragraph" or _clean_text(right.get("kind")) != "paragraph":
        return False
    if not _paper_structure_same_column(left, right):
        return False
    gap = _paper_structure_vertical_gap(left, right)
    if gap < -3 or gap > 20:
        return False
    left_text = _clean_text(left.get("text"))
    right_text = _clean_text(right.get("text"))
    if not left_text or not right_text:
        return False
    if len(left_text) < 80 or len(right_text) < 80:
        return True
    if re.search(r"[-,:;(\[]$", left_text):
        return True
    if re.match(r"^[a-z,;:)]", right_text):
        return True
    return False


def _paper_structure_unit_sort_key_factory(units: list[PaperStructureUnit]):
    page_has_columns: dict[int, bool] = {}
    for page in {int(unit.page_start or 0) for unit in units}:
        centers: list[float] = []
        page_width = 0.0
        for unit in units:
            if int(unit.page_start or 0) != page or unit.kind not in {"paragraph", "heading", "caption"}:
                continue
            rect = _paper_structure_primary_rect(unit.to_dict())
            if rect is None:
                continue
            try:
                width = float(rect.get("w") or 0)
                x = float(rect.get("x") or 0)
                page_width = max(page_width, float(rect.get("page_width") or 0))
            except (TypeError, ValueError):
                continue
            if page_width and width < page_width * 0.58:
                centers.append(x + width / 2)
        if page_width and centers:
            left = [value for value in centers if value < page_width * 0.46]
            right = [value for value in centers if value > page_width * 0.54]
            page_has_columns[page] = len(left) >= 2 and len(right) >= 2

    def key(unit: PaperStructureUnit) -> tuple[float, float, float, float, str]:
        rect = _paper_structure_primary_rect(unit.to_dict()) or {}
        try:
            page = int(unit.page_start or 0)
            x = float(rect.get("x") or 0)
            y = float(rect.get("y") or 0)
            width = float(rect.get("w") or 0)
            page_width = float(rect.get("page_width") or 0)
            y_pct = float(rect.get("y_pct") or 0)
        except (TypeError, ValueError):
            page = int(unit.page_start or 0)
            x = y = width = page_width = y_pct = 0.0
        is_front = page == 1 and y_pct <= 0.34 and unit.kind in {"title", "authors", "affiliation"}
        lane = 0 if is_front else 1
        if page_has_columns.get(page) and page_width and width < page_width * 0.62 and not is_front:
            column = 0 if x + width / 2 < page_width / 2 else 1
            return (page, lane, column, y, unit.unit_id)
        return (page, lane, 2, y, unit.unit_id)

    return key


def _paper_structure_reassign_order_and_sections(units: list[PaperStructureUnit]) -> list[PaperStructureUnit]:
    sorted_units = sorted(units, key=_paper_structure_unit_sort_key_factory(units))
    current_section: list[str] = []
    out: list[PaperStructureUnit] = []
    for order, unit in enumerate(sorted_units, start=1):
        unit.order = order
        if unit.kind == "heading":
            current_section = [" ".join(unit.text.split())]
            unit.section_path = list(current_section)
        elif unit.kind == "paragraph":
            unit.section_path = list(unit.section_path or current_section)
        elif unit.kind == "caption":
            if current_section:
                unit.metadata.setdefault("near_section_path", list(current_section))
            unit.section_path = []
        elif unit.kind in {"figure", "table"}:
            if current_section:
                unit.metadata.setdefault("near_section_path", list(current_section))
            unit.section_path = []
        elif unit.kind in {"title", "authors", "affiliation", "footnote", "reference", "symbol", "figure_label", "table_cell"}:
            unit.section_path = []
        unit.locator = _paper_structure_locator(unit.page_start, unit.page_end)
        out.append(unit)
    return out


def _paper_structure_top_y(unit: PaperStructureUnit) -> float:
    rect = _paper_structure_primary_rect(unit.to_dict()) or {}
    try:
        return float(rect.get("y_pct"))
    except (TypeError, ValueError):
        return 1.0


def _paper_structure_cross_page_continuation(left: PaperStructureUnit, right: PaperStructureUnit) -> bool:
    if left.kind != "paragraph" or right.kind != "paragraph":
        return False
    if left.page_end + 1 != right.page_start:
        return False
    if not left.section_path or left.section_path != right.section_path:
        return False
    if _paper_structure_top_y(right) > 0.22:
        return False
    left_text = _clean_text(left.text)
    right_text = _clean_text(right.text)
    if not left_text or not right_text:
        return False
    if re.match(r"^(and|or|but|while|which|that|whose|where|with|without|by|to|of|for|in|on|as|also|furthermore|moreover)\b", right_text, flags=re.IGNORECASE):
        return True
    if re.match(r"^[a-z,;:)]", right_text):
        return True
    if not re.search(r"[.!?。！？][\"')\]]?$", left_text):
        return True
    return False


def _paper_structure_merge_unit_pair(left: PaperStructureUnit, right: PaperStructureUnit) -> PaperStructureUnit:
    text = _join_pdf_lines_as_text([left.text, right.text])
    row_hash = text_hash(text)
    left.text = text
    left.text_hash = row_hash
    left.page_end = max(left.page_end, right.page_end)
    left.rects = [*_clean_rect_list(left.rects), *_clean_rect_list(right.rects)]
    left.source_unit_ids = [*_clean_list(left.source_unit_ids), right.unit_id, *_clean_list(right.source_unit_ids)]
    left.locator = _paper_structure_locator(left.page_start, left.page_end)
    left.unit_id = f"psu:{source_slug(left.source_id)}:{left.page_start}:{int(left.order):05d}:{row_hash.removeprefix('sha256:')[:12]}"
    return left


def _paper_structure_merge_cross_page_continuations(units: list[PaperStructureUnit]) -> list[PaperStructureUnit]:
    ordered = sorted(units, key=lambda unit: (unit.page_start, unit.order, unit.unit_id))
    consumed: set[str] = set()
    for current in ordered:
        if current.unit_id in consumed or current.kind != "paragraph":
            continue
        for previous in reversed(ordered):
            if previous.unit_id == current.unit_id or previous.unit_id in consumed:
                continue
            if previous.page_end + 1 < current.page_start:
                break
            if _paper_structure_cross_page_continuation(previous, current):
                _paper_structure_merge_unit_pair(previous, current)
                consumed.add(current.unit_id)
                break
    return [unit for unit in ordered if unit.unit_id not in consumed]


def _paper_structure_units_from_candidates(source_id: str, candidates: list[dict[str, object]]) -> list[PaperStructureUnit]:
    merged: list[dict[str, object]] = []
    for candidate in candidates:
        kind = _clean_text(candidate.get("kind"))
        if kind == "heading_marker" and merged:
            merged.append(candidate)
            continue
        if merged:
            previous = merged[-1]
            prev_kind = _clean_text(previous.get("kind"))
            same_page = int(previous.get("page_end") or 0) == int(candidate.get("page_start") or 0)
            if same_page and prev_kind == kind == "title":
                merged[-1] = _paper_structure_merge_pair(previous, candidate, kind="title")
                continue
            if same_page and prev_kind == kind and kind in {"authors", "affiliation"}:
                merged[-1] = _paper_structure_merge_pair(previous, candidate, kind=kind)
                continue
            if same_page and prev_kind == "heading_marker" and kind in {"paragraph", "heading"}:
                title = _join_pdf_lines_as_text([_clean_text(previous.get("text")), _clean_text(candidate.get("text"))])
                if _paper_structure_heading_kind(
                    title,
                    page=int(candidate.get("page_start") or 0),
                    font_size=float(candidate.get("font_size") or 0),
                    layout_kind="paragraph",
                ) == "heading":
                    previous["text"] = title
                    merged[-1] = _paper_structure_merge_pair(previous, candidate, kind="heading")
                    continue
            if prev_kind == "caption" and _paper_structure_caption_continuation(previous, candidate):
                merged[-1] = _paper_structure_merge_pair(previous, candidate, kind="caption")
                continue
            if _paper_structure_paragraph_continuation(previous, candidate):
                merged[-1] = _paper_structure_merge_pair(previous, candidate, kind="paragraph")
                continue
        merged.append(candidate)

    units: list[PaperStructureUnit] = []
    slug = source_slug(source_id)
    current_section: list[str] = []
    order = 0
    for row in merged:
        kind = _clean_text(row.get("kind"))
        if kind == "heading_marker":
            continue
        text = _clean_text(row.get("text"))
        if not text:
            continue
        order += 1
        page_start = int(row.get("page_start") or 1)
        page_end = int(row.get("page_end") or page_start)
        row_hash = text_hash(text)
        short_hash = row_hash.removeprefix("sha256:")[:12]
        if kind == "heading":
            current_section = [" ".join(text.split())]
        section_path = list(current_section) if kind == "paragraph" else ([] if kind in {"title", "authors", "affiliation", "caption", "figure", "table"} else list(current_section))
        rects = _clean_rect_list(row.get("rects"))
        translatable = kind in PAPER_STRUCTURE_TRANSLATION_KINDS and bool(row.get("translatable", True))
        display_source = kind in {"authors", "affiliation"} or bool(row.get("display_source", False))
        units.append(
            PaperStructureUnit(
                unit_id=f"psu:{slug}:{page_start}:{order:05d}:{short_hash}",
                source_id=source_id,
                kind=kind,
                page_start=page_start,
                page_end=page_end,
                order=order,
                text=text,
                text_hash=row_hash,
                section_path=section_path,
                locator=_paper_structure_locator(page_start, page_end),
                rects=rects,
                source_unit_ids=_clean_list(row.get("source_unit_ids")),
                translatable=translatable,
                display_source=display_source,
                metadata=_clean_mapping(row.get("metadata")),
            )
        )

    units = _paper_structure_add_caption_objects(units, slug=slug)
    units = _paper_structure_add_table_units(units, slug=slug)
    return _paper_structure_reassign_order_and_sections(units)


def _paper_structure_add_caption_objects(units: list[PaperStructureUnit], *, slug: str) -> list[PaperStructureUnit]:
    additions: list[PaperStructureUnit] = []
    for caption in units:
        if caption.kind != "caption":
            continue
        clean = " ".join(caption.text.split())
        match = re.match(r"^(fig(?:ure)?\.?|table|algorithm)\s*\d+", clean, flags=re.IGNORECASE)
        if not match:
            continue
        label = match.group(1).lower()
        kind = "table" if label == "table" else "figure"
        text = clean[:400]
        row_hash = text_hash(f"{kind}:{text}")
        order = max(1, int(caption.order or 1) - 1)
        additions.append(
            PaperStructureUnit(
                unit_id=f"psu:{slug}:{caption.page_start}:{order:05d}:{row_hash.removeprefix('sha256:')[:12]}",
                source_id=caption.source_id,
                kind=kind,
                page_start=caption.page_start,
                page_end=caption.page_end,
                order=order,
                text=text,
                text_hash=row_hash,
                section_path=list(caption.section_path),
                locator=caption.locator,
                rects=copy.deepcopy(caption.rects),
                source_unit_ids=[caption.unit_id],
                translatable=False,
                display_source=False,
                metadata={"inferred_from_caption": True, "caption_unit_id": caption.unit_id},
            )
        )
    if not additions:
        return units
    return sorted([*units, *additions], key=lambda unit: (unit.page_start, unit.order, unit.unit_id))


def _paper_structure_add_table_units(units: list[PaperStructureUnit], *, slug: str) -> list[PaperStructureUnit]:
    table_groups: dict[str, list[PaperStructureUnit]] = {}
    for unit in units:
        table_id = _clean_text(unit.metadata.get("table_id"))
        if table_id and unit.kind == "table_cell":
            table_groups.setdefault(table_id, []).append(unit)
    additions: list[PaperStructureUnit] = []
    for table_id, cells in table_groups.items():
        if not cells:
            continue
        page_start = min(cell.page_start for cell in cells)
        page_end = max(cell.page_end for cell in cells)
        order = min(cell.order for cell in cells)
        rect = _paper_structure_rect_union([rect for cell in cells for rect in cell.rects])
        text = " ".join(cell.text for cell in cells if cell.text)[:2000] or table_id
        row_hash = text_hash(text)
        additions.append(
            PaperStructureUnit(
                unit_id=f"psu:{slug}:{page_start}:{order:05d}:{row_hash.removeprefix('sha256:')[:12]}",
                source_id=cells[0].source_id,
                kind="table",
                page_start=page_start,
                page_end=page_end,
                order=order - 1 if order > 1 else order,
                text=text,
                text_hash=row_hash,
                section_path=list(cells[0].section_path),
                locator=_paper_structure_locator(page_start, page_end),
                rects=[rect] if rect is not None else [],
                source_unit_ids=[unit.unit_id for unit in cells],
                translatable=False,
                display_source=False,
                metadata={"table_id": table_id},
            )
        )
    if not additions:
        return units
    return sorted([*units, *additions], key=lambda unit: (unit.page_start, unit.order, unit.unit_id))


def _paper_structure_match_ratio(left: str, right: str) -> float:
    clean_left = _translation_match_text(left)
    clean_right = _translation_match_text(right)
    if not clean_left or not clean_right:
        return 0.0
    if clean_left == clean_right:
        return 1.0
    if clean_left in clean_right or clean_right in clean_left:
        return min(len(clean_left), len(clean_right)) / max(len(clean_left), len(clean_right))
    return difflib.SequenceMatcher(None, clean_left[:900], clean_right[:900]).ratio()


def _paper_structure_apply_grobid_alignment(
    units: list[PaperStructureUnit],
    segments: list[PaperSegment],
) -> list[PaperStructureUnit]:
    if not units or not segments:
        return units
    candidates = [
        segment
        for segment in segments
        if segment.section_path and _clean_text(segment.text)
    ]
    if not candidates:
        return units
    out: list[PaperStructureUnit] = []
    current_section: list[str] = []
    for unit in units:
        if unit.kind == "heading":
            current_section = [" ".join(unit.text.split())]
            unit.section_path = list(current_section)
            out.append(unit)
            continue
        if unit.kind != "paragraph":
            out.append(unit)
            continue
        best: tuple[float, PaperSegment] | None = None
        for segment in candidates:
            if segment.page and unit.page_start and abs(int(segment.page) - int(unit.page_start)) > 1:
                continue
            score = _paper_structure_match_ratio(unit.text, segment.text)
            if score >= 0.72 and (best is None or score > best[0]):
                best = (score, segment)
        if best is not None:
            unit.section_path = list(best[1].section_path)
            current_section = list(unit.section_path)
        elif current_section and not unit.section_path:
            unit.section_path = list(current_section)
        out.append(unit)
    return out


def _paper_structure_quality_flags(units: list[PaperStructureUnit]) -> list[str]:
    flags: list[str] = []
    if not any(unit.kind == "heading" for unit in units):
        flags.append("outline_empty")
    translatable = [unit for unit in units if unit.kind in PAPER_STRUCTURE_TRANSLATION_KINDS and unit.translatable]
    if translatable:
        short_count = sum(1 for unit in translatable if len(unit.text.split()) <= 4 and unit.kind == "paragraph")
        if short_count / max(1, len(translatable)) > 0.30:
            flags.append("short_fragment_ratio_high")
    if units and not any(unit.kind == "title" for unit in units if unit.page_start == 1):
        flags.append("front_matter_title_missing")
    captions = [unit for unit in units if unit.kind == "caption"]
    figures_or_tables = [unit for unit in units if unit.kind in {"figure", "table"}]
    if captions and len(figures_or_tables) and len(captions) > len(figures_or_tables) * 3:
        flags.append("caption_orphan_ratio_high")
    return flags


def _paper_structure_llm_repair_enabled() -> bool:
    return str(os.environ.get("NBLANE_PAPER_STRUCTURE_LLM_REPAIR", "")).strip().lower() in {"1", "true", "yes", "on"}


def _paper_structure_apply_llm_repair_hook(units: list[PaperStructureUnit]) -> list[PaperStructureUnit]:
    if not _paper_structure_llm_repair_enabled():
        return units
    flags = _paper_structure_quality_flags(units)
    if not flags:
        return units
    for unit in units:
        unit.metadata.setdefault("llm_repair_requested", False)
        unit.metadata.setdefault("structure_quality_flags", list(flags))
    return units


def build_paper_structure_units(
    profile: str | Path,
    source_id: str,
    *,
    force: bool = False,
) -> list[PaperStructureUnit]:
    """Build cached, layout-grounded paper structure units for Reader translation."""

    if not force:
        cached = load_paper_structure_units(profile, source_id)
        if cached and all(unit.metadata.get("structure_version") == PAPER_STRUCTURE_VERSION for unit in cached):
            return cached
    layout_units = build_paper_layout_units(profile, source_id)
    if not layout_units:
        return []
    candidates = _paper_structure_candidates_from_layout(layout_units, source_id)
    units = _paper_structure_units_from_candidates(source_id, candidates)
    units = _paper_structure_apply_grobid_alignment(units, load_paper_segments(profile, source_id))
    units = _paper_structure_merge_cross_page_continuations(units)
    units = _paper_structure_reassign_order_and_sections(units)
    units = _paper_structure_apply_llm_repair_hook(units)
    if units:
        save_paper_structure_units(profile, source_id, units)
    return units


def reader_translation_structure_units(
    units: list[PaperStructureUnit | dict],
    *,
    include_references: bool | None = True,
) -> list[dict[str, object]]:
    """Return structure units that belong in the normal Reader translation flow."""

    rows: list[dict[str, object]] = []
    allowed = set(PAPER_STRUCTURE_TRANSLATION_KINDS)
    for item in units:
        unit = item if isinstance(item, PaperStructureUnit) else PaperStructureUnit.from_dict(item)
        if unit is None or unit.kind not in allowed:
            continue
        if _paper_structure_unit_is_translation_noise(unit):
            continue
        if _paper_structure_unit_is_reference_section(unit) and not _paper_translation_include_references(include_references):
            continue
        if not unit.translatable and not unit.display_source:
            continue
        source_text = _clean_text(unit.text)
        if not source_text:
            continue
        row = unit.to_dict()
        row.update(
            {
                "unit_id": unit.unit_id,
                "anchor_id": unit.unit_id,
                "scope_type": "structure",
                "scope_ref": unit.unit_id,
                "segment_id": "",
                "page": unit.page_start,
                "page_end": unit.page_end,
                "source_hash": unit.text_hash or text_hash(source_text),
                "source_text": source_text,
                "target_lang": "",
                "translated_text": source_text if unit.display_source and not unit.translatable else "",
                "status": "translated" if not unit.translatable else "missing",
            }
        )
        rows.append(row)
    return sorted(rows, key=lambda row: (int(row.get("page") or 0), int(row.get("order") or 0), _clean_text(row.get("unit_id"))))


def _paper_structure_unit_is_translation_noise(unit: PaperStructureUnit) -> bool:
    """Return True for figure/table fragments that should not enter translation."""

    metadata = unit.metadata if isinstance(unit.metadata, dict) else {}
    if _clean_text(metadata.get("table_id")):
        return True
    lower = " ".join(_clean_text(unit.text).lower().split()).strip(" .:")
    if unit.kind in {"paragraph", "heading"} and lower in _TABLE_OR_FIGURE_HEADINGS and len(lower.split()) <= 4:
        return True
    return False


def _truthy_env(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _paper_translation_include_references(value: bool | None = None) -> bool:
    if value is not None:
        return bool(value)
    return _truthy_env(os.environ.get(PAPER_TRANSLATION_INCLUDE_REFERENCES_ENV))


def _paper_reference_section_label(value: object) -> str:
    clean = " ".join(_clean_text(value).split()).strip(" .:-").lower()
    if not clean:
        return ""
    clean = re.sub(r"^(?:\d+(?:\.\d+)*|[ivxlcdm]+)\s*[\.\)]?\s*", "", clean, flags=re.IGNORECASE)
    return clean.strip(" .:-")


def _paper_section_path_is_reference_section(section_path: object, *, heading_text: object = "") -> bool:
    labels = [_paper_reference_section_label(part) for part in _clean_list(section_path)]
    if _clean_text(heading_text):
        labels.append(_paper_reference_section_label(heading_text))
    for label_text in labels:
        if not label_text:
            continue
        if label_text in PAPER_REFERENCE_SECTION_LABELS:
            return True
        if label_text.startswith("references"):
            return True
        if label_text.startswith("bibliography"):
            return True
    return False


def _paper_structure_unit_is_reference_section(unit: PaperStructureUnit) -> bool:
    heading_text = unit.text if unit.kind == "heading" else ""
    return _paper_section_path_is_reference_section(unit.section_path, heading_text=heading_text)


def _paper_segment_is_reference_section(segment: PaperSegment) -> bool:
    heading_text = segment.text if _clean_text(segment.kind).lower() == "heading" else ""
    return _paper_section_path_is_reference_section(segment.section_path, heading_text=heading_text)


def build_translation_units(
    *,
    pages: list[PaperPage],
    segments: list[dict[str, object]],
    translations: list[dict[str, object]],
    target_lang: str,
    layout_units: list[dict[str, object]] | None = None,
) -> tuple[list[dict[str, object]], dict[str, int]]:
    """Return ordered translation reading units for Reader visual modes."""

    units: list[dict[str, object]] = []
    summary = {"translated": 0, "missing": 0, "stale": 0, "failed": 0}
    layout_rows = [copy.deepcopy(row) for row in (layout_units or []) if isinstance(row, dict)]
    if layout_rows and not segments and not pages:
        layout_translations = {
            (
                _clean_text(row.get("scope_type")) or "segment",
                _clean_text(row.get("scope_ref") or row.get("segment_id")),
            ): row
            for row in translations
            if _clean_text(row.get("target_lang") or "zh") == target_lang
            and _clean_text(row.get("scope_ref") or row.get("segment_id"))
        }
        legacy_by_hash: dict[str, dict[str, object]] = {
            _clean_text(row.get("source_hash")): row
            for row in translations
            if _clean_text(row.get("target_lang") or "zh") == target_lang
            and _clean_text(row.get("scope_type")) in {"layout", "segment", "page"}
            and _clean_text(row.get("source_hash"))
            and translation_text_from_row(row)
        }
        for raw_unit in sorted(layout_rows, key=lambda row: (int(row.get("page") or 0), int(row.get("order") or 0), _clean_text(row.get("unit_id")))):
            scope_ref = _clean_text(raw_unit.get("scope_ref") or raw_unit.get("unit_id"))
            source_text = _clean_text(raw_unit.get("source_text") or raw_unit.get("text"))
            if not scope_ref or not source_text:
                continue
            scope_type = _clean_text(raw_unit.get("scope_type")) or "layout"
            source_hash = _clean_text(raw_unit.get("source_hash")) or text_hash(source_text)
            translation = layout_translations.get((scope_type, scope_ref))
            if translation is None and scope_type == "structure":
                translation = legacy_by_hash.get(source_hash)
            translatable = bool(raw_unit.get("translatable", True))
            display_source = bool(raw_unit.get("display_source", not translatable))
            translated_text = translation_text_from_row(translation or {})
            status = _translation_unit_status(translation, source_hash) if translatable else "translated"
            if not translatable:
                translated_text = source_text if display_source else ""
            if translatable:
                summary[status] = summary.get(status, 0) + 1
            unit = {
                **raw_unit,
                "unit_id": scope_ref,
                "anchor_id": _clean_text(raw_unit.get("anchor_id")) or scope_ref,
                "scope_type": scope_type,
                "scope_ref": scope_ref,
                "segment_id": "",
                "source_hash": source_hash,
                "source_text": source_text,
                "target_lang": target_lang,
                "translated_text": translated_text,
                "status": status,
                "status_reason": _clean_text((translation or {}).get("status_reason")),
                "rects": copy.deepcopy(raw_unit.get("rects") or []),
                "translatable": translatable,
                "display_source": display_source,
            }
            units.append(unit)
        return units, summary

    page_rows = sorted(pages, key=lambda row: row.page)
    page_translations: dict[int, dict[str, object]] = {}
    segment_translations: dict[str, dict[str, object]] = {}
    for row in translations:
        if _clean_text(row.get("target_lang") or "zh") != target_lang:
            continue
        scope_type = _clean_text(row.get("scope_type")) or "segment"
        if scope_type == "page":
            try:
                page_number = int(row.get("page") or 0)
            except (TypeError, ValueError):
                page_number = 0
            if page_number > 0:
                page_translations[page_number] = row
        elif scope_type == "segment":
            segment_id = _clean_text(row.get("segment_id") or row.get("scope_ref"))
            if segment_id:
                segment_translations[segment_id] = row

    if not segments:
        for index, page_row in enumerate(page_rows, start=1):
            source_text = _clean_text(page_row.text)
            if not source_text:
                continue
            page_hash = page_row.text_hash or text_hash(source_text)
            translation = page_translations.get(page_row.page)
            translated_text = translation_text_from_row(translation or {})
            status = _translation_unit_status(translation, page_hash)
            summary[status] = summary.get(status, 0) + 1
            scope_ref = f"page:{page_row.page}:{page_hash}"
            units.append(
                {
                    "unit_id": scope_ref,
                    "anchor_id": scope_ref,
                    "scope_type": "page",
                    "scope_ref": scope_ref,
                    "segment_id": "",
                    "page": page_row.page,
                    "order": index * 100000,
                    "section_path": [],
                    "kind": "page",
                    "locator": f"p. {page_row.page}",
                    "source_hash": page_hash,
                    "source_text": source_text,
                    "target_lang": target_lang,
                    "translated_text": translated_text,
                    "status": status,
                    "status_reason": _clean_text((translation or {}).get("status_reason")),
                    "rects": [],
                }
            )

    for raw_segment in sorted(segments, key=lambda row: (int(row.get("page") or 0), int(row.get("order") or 0), _clean_text(row.get("segment_id")))):
        segment_id = _clean_text(raw_segment.get("segment_id"))
        source_text = _clean_text(raw_segment.get("text"))
        if not segment_id or not source_text:
            continue
        source_hash = _clean_text(raw_segment.get("text_hash")) or text_hash(source_text)
        translation = segment_translations.get(segment_id)
        translated_text = translation_text_from_row(translation or {})
        status = _translation_unit_status(translation, source_hash)
        summary[status] = summary.get(status, 0) + 1
        try:
            page_number = int(raw_segment.get("page") or 0)
        except (TypeError, ValueError):
            page_number = 0
        try:
            order = int(raw_segment.get("order") or 0)
        except (TypeError, ValueError):
            order = 0
        units.append(
            {
                "unit_id": f"segment:{segment_id}",
                "anchor_id": f"segment:{segment_id}",
                "scope_type": "segment",
                "scope_ref": segment_id,
                "segment_id": segment_id,
                "page": page_number,
                "order": order,
                "section_path": copy.deepcopy(raw_segment.get("section_path") or []),
                "kind": _clean_text(raw_segment.get("kind")) or "paragraph",
                "locator": _clean_text(raw_segment.get("locator")) or (f"p. {page_number}" if page_number else ""),
                "source_hash": source_hash,
                "source_text": source_text,
                "target_lang": target_lang,
                "translated_text": translated_text,
                "status": status,
                "status_reason": _clean_text((translation or {}).get("status_reason")),
                "rects": copy.deepcopy(raw_segment.get("rects") or []),
            }
        )
    units.sort(key=lambda row: (int(row.get("page") or 0) if int(row.get("page") or 0) > 0 else 10**9, int(row.get("order") or 0), _clean_text(row.get("unit_id"))))
    return units, summary


def build_reader_payload(
    profile: str | Path,
    source_id: str,
    *,
    page: int,
    requested_pages: set[int],
    target_lang: str,
    include_page_previews: bool = True,
    pdf_url_override: str | None = None,
) -> dict[str, object]:
    """Build a bounded reader payload without extracting, translating, or calling AI."""

    _, source = _source_by_id(profile, source_id)
    metadata = dict(source.metadata or {})
    all_pages = load_paper_pages(profile, source_id)
    page_numbers = [page_row.page for page_row in all_pages]
    total_pages = max(
        [
            int(metadata.get("page_count") or 0),
            int(metadata.get("reading_artifacts_page_count") or 0),
            *page_numbers,
            1,
        ]
    )
    context_pages = sorted(_reader_page_set(page=page, requested_pages=requested_pages, total_pages=total_pages))
    context_page_set = set(context_pages)
    preview_rows: list[dict[str, object]] = []
    if include_page_previews:
        for page_number in context_pages:
            try:
                preview_rows.append(render_paper_page_preview(profile, source_id, page_number, max_width=1100))
            except Exception:
                continue
    all_structure_units = build_paper_structure_units(profile, source_id)
    layout_units = build_paper_layout_units(profile, source_id, pages=context_pages)
    page_models = _page_models_from_pdf(profile, source_id, context_pages)
    if not page_models:
        page_models = _page_models_from_layout_units(layout_units, context_pages)
    figures = extract_paper_figures(profile, source_id, pages=context_pages, max_items=24, max_width=640)
    reader_layout_units = reader_translation_layout_units(layout_units)
    reader_structure_units = reader_translation_structure_units(
        [
            unit
            for unit in all_structure_units
            if unit.page_start in context_page_set
            or unit.page_end in context_page_set
            or any(page_number in context_page_set for page_number in range(unit.page_start, unit.page_end + 1))
        ]
    )
    structure_scope_refs = {
        _clean_text(row.get("scope_ref") or row.get("unit_id"))
        for row in reader_structure_units
        if isinstance(row, dict)
    }
    structure_hashes = {
        _clean_text(row.get("source_hash"))
        for row in reader_structure_units
        if isinstance(row, dict) and _clean_text(row.get("source_hash"))
    }
    layout_scope_refs = {
        _clean_text(row.get("scope_ref") or row.get("unit_id"))
        for row in reader_layout_units
        if isinstance(row, dict)
    }
    all_segments = load_paper_segments(profile, source_id)
    outline = _reader_outline_from_structure_units(all_structure_units) or _reader_outline_from_segments(all_segments)
    reader_preparation = _reader_preparation_summary(source, all_pages, all_segments)
    has_paged_segments = any(segment.page > 0 for segment in all_segments)
    segments = [
        segment.to_dict()
        for segment in all_segments
        if segment.page in context_page_set
        or (not has_paged_segments and segment.page <= 0)
    ]
    segment_ids = {str(row.get("segment_id") or "") for row in segments}
    segment_pages = {str(row.get("segment_id") or ""): int(row.get("page") or 0) for row in segments}
    current_translation_rows = load_paper_translations(profile, source_id)
    prefer_structure_units = bool(reader_structure_units)
    prefer_layout_units = bool(reader_layout_units) and not prefer_structure_units
    translations: list[dict[str, object]] = []
    for row in current_translation_rows:
        if row.target_lang != target_lang:
            continue
        has_translated_text = bool(_clean_text(row.translated_text))
        scope_type = _clean_text(row.scope_type) or "segment"
        row_page = int(row.page or segment_pages.get(row.segment_id, 0))
        include_row = False
        if scope_type == "structure":
            include_row = row.scope_ref in structure_scope_refs
        elif prefer_structure_units and scope_type in {"layout", "segment", "page"}:
            include_row = row.source_hash in structure_hashes and bool(_clean_text(row.translated_text))
        elif scope_type == "layout":
            include_row = row.scope_ref in layout_scope_refs
        elif scope_type == "page":
            if prefer_layout_units or all_segments:
                include_row = False
            else:
                include_row = row_page in context_page_set or any(str(row.scope_ref).startswith(f"page:{page_number}:") for page_number in context_pages)
        elif scope_type == "selection":
            include_row = row_page in context_page_set or row_page <= 0
        elif scope_type == "segment":
            include_row = False if prefer_layout_units else row_page in context_page_set or bool(row.segment_id and row.segment_id in segment_ids)
        if include_row and has_translated_text:
            translations.append({**row.to_dict(), "page": row_page})
    page_context_rows = [page_row for page_row in all_pages if page_row.page in context_page_set]
    positioned_units = reader_structure_units if prefer_structure_units else reader_layout_units
    prefer_positioned_units = prefer_structure_units or prefer_layout_units
    unit_pages = [] if prefer_positioned_units else page_context_rows
    unit_segments = [] if prefer_positioned_units else segments
    translation_units, translation_summary = build_translation_units(
        pages=unit_pages,
        segments=unit_segments,
        translations=translations,
        target_lang=target_lang,
        layout_units=positioned_units,
    )
    annotations = [
        ann.to_dict()
        for ann in load_paper_annotations(profile, source_id)
        if ann.status != "deleted" or ann.page in context_page_set
    ]
    chunks = [
        {
            "id": chunk.id,
            "source_id": chunk.source_id,
            "kind": chunk.kind,
            "title": chunk.title,
            "text": chunk.text[:420],
            "locator": chunk.locator,
            "metadata": {
                key: value
                for key, value in dict(chunk.metadata or {}).items()
                if key in {"page", "segment_id", "selected_text_hash", "annotation_id"}
            },
        }
        for chunk in load_chunks(_profile_root(profile), source_id)
    ]
    chunk_ids = {str(row.get("id") or "") for row in chunks}
    citations = [
        citation.to_dict()
        for citation in load_research_citations(_profile_root(profile))
        if citation.source_id == source_id or (citation.chunk_id and citation.chunk_id in chunk_ids)
    ]
    citation_ids = {str(row.get("id") or "") for row in citations}
    claims = [
        claim.to_dict()
        for claim in load_research_claims(_profile_root(profile))
        if source_id in claim.source_refs
        or any(ref in chunk_ids for ref in claim.chunk_refs)
        or any(ref in citation_ids for ref in claim.citation_refs)
    ]
    pdf_url = (
        _clean_text(pdf_url_override)
        if pdf_url_override is not None
        else get_stable_pdf_url(profile, source_id) if _clean_text(metadata.get("pdf_asset_ref")) else ""
    )
    return {
        "source": source.to_dict(),
        "pdf_url": pdf_url,
        "page_previews": preview_rows,
        "page_models": page_models,
        "figures": figures,
        "outline": outline,
        "pages": [page_row.to_dict() for page_row in page_context_rows],
        "segments": segments,
        "translations": translations,
        "translation_units": translation_units,
        "translation_summary": translation_summary,
        "translation_revision": _translation_revision(profile, source_id, target_lang),
        "compare_split_ratio": _metadata_int(metadata, "compare_split_ratio", 50, minimum=20, maximum=80),
        "panel_width": _metadata_int(metadata, "panel_width", 340, minimum=280, maximum=560),
        "annotations": annotations,
        "chunks": chunks,
        "citations": citations,
        "claims": claims,
        "analysis": load_paper_analysis(profile, source_id),
        "reader_state": _reader_state_from_metadata(metadata, page=page, target_lang=target_lang),
        "reader_preparation": reader_preparation,
        "context_window": {
            "pages": context_pages,
            "has_more_before": bool(context_pages and min(context_pages) > 1),
            "has_more_after": bool(context_pages and max(context_pages) < total_pages),
            "total_pages": total_pages,
        },
    }


def translation_rows_for_segments(
    profile: str | Path,
    source_id: str,
    segment_ids: list[str],
    *,
    target_lang: str = "zh",
    translated_text_by_id: dict[str, str] | None = None,
    generated_by: str = "rule:paper_translate",
) -> list[PaperTranslation]:
    """Build validated translation rows for explicit user acceptance."""

    segments = _segment_hash_map(profile, source_id)
    existing = load_paper_translations(profile, source_id)
    rows: list[PaperTranslation] = []
    for segment_id in _clean_list(segment_ids):
        segment = segments.get(segment_id)
        if segment is None:
            continue
        rows.append(
            PaperTranslation(
                id=_next_translation_id(existing + rows, source_id),
                source_id=source_id,
                scope_type="segment",
                scope_ref=segment.segment_id,
                segment_id=segment.segment_id,
                page=segment.page,
                source_hash=segment.text_hash,
                source_text=segment.text,
                target_lang=_clean_text(target_lang) or "zh",
                translated_text=(translated_text_by_id or {}).get(segment.segment_id, segment.text),
                generated_by=generated_by,
                created=_now(),
            )
        )
    return rows


def _translation_is_current(
    translation: PaperTranslation | None,
    segment: PaperSegment,
    target_lang: str,
) -> bool:
    if translation is None:
        return False
    if translation.target_lang != target_lang:
        return False
    if translation.status != "translated":
        return False
    if not _clean_text(translation.translated_text):
        return False
    return translation.source_hash == segment.text_hash


def _translation_status_counts(
    segments: list[PaperSegment],
    translations: list[PaperTranslation],
    *,
    target_lang: str,
) -> dict[str, int]:
    by_segment = {
        row.segment_id: row
        for row in translations
        if row.segment_id and row.target_lang == target_lang
    }
    counts = {"translated": 0, "missing": 0, "stale": 0, "failed": 0}
    for segment in segments:
        row = by_segment.get(segment.segment_id)
        if row is None:
            counts["missing"] += 1
        elif row.status == "failed":
            counts["failed"] += 1
        elif not _translation_is_current(row, segment, target_lang):
            counts["stale"] += 1
        else:
            counts["translated"] += 1
    return counts


def _page_translation_is_current(
    translation: PaperTranslation | None,
    page: PaperPage,
    target_lang: str,
) -> bool:
    if translation is None:
        return False
    if translation.target_lang != target_lang:
        return False
    if translation.status != "translated":
        return False
    if not _clean_text(translation.translated_text):
        return False
    return translation.source_hash == (page.text_hash or text_hash(page.text))


def _page_translation_status_counts(
    pages: list[PaperPage],
    translations: list[PaperTranslation],
    *,
    target_lang: str,
) -> dict[str, int]:
    by_scope = {
        row.scope_ref: row
        for row in translations
        if row.scope_type == "page" and row.target_lang == target_lang
    }
    counts = {"translated": 0, "missing": 0, "stale": 0, "failed": 0}
    for page in pages:
        if not _clean_text(page.text):
            continue
        page_hash = page.text_hash or text_hash(page.text)
        row = by_scope.get(f"page:{page.page}:{page_hash}")
        if row is None:
            counts["missing"] += 1
        elif row.status == "failed":
            counts["failed"] += 1
        elif not _page_translation_is_current(row, page, target_lang):
            counts["stale"] += 1
        else:
            counts["translated"] += 1
    return counts


def _layout_translation_is_current(
    translation: PaperTranslation | None,
    unit: dict[str, object],
    target_lang: str,
) -> bool:
    if translation is None:
        return False
    if translation.target_lang != target_lang:
        return False
    if translation.status != "translated":
        return False
    if not _clean_text(translation.translated_text):
        return False
    return translation.source_hash == _clean_text(unit.get("source_hash"))


def _layout_translation_status_counts(
    layout_units: list[dict[str, object]],
    translations: list[PaperTranslation],
    *,
    target_lang: str,
    scope_type: str = "layout",
) -> dict[str, int]:
    clean_scope_type = _clean_text(scope_type) or "layout"
    by_scope = {
        row.scope_ref: row
        for row in translations
        if row.scope_type == clean_scope_type and row.target_lang == target_lang
    }
    counts = {"translated": 0, "missing": 0, "stale": 0, "failed": 0}
    for unit in layout_units:
        if not bool(unit.get("translatable", True)):
            continue
        scope_ref = _clean_text(unit.get("scope_ref") or unit.get("unit_id"))
        if not scope_ref:
            continue
        row = by_scope.get(scope_ref)
        if row is None:
            counts["missing"] += 1
        elif row.status == "failed":
            counts["failed"] += 1
        elif not _layout_translation_is_current(row, unit, target_lang):
            counts["stale"] += 1
        else:
            counts["translated"] += 1
    return counts


def _layout_unit_translation_payload(unit: dict[str, object], *, source_id: str) -> dict[str, object]:
    source_text = _clean_text(unit.get("source_text") or unit.get("text"))
    source_hash = _clean_text(unit.get("source_hash")) or text_hash(source_text)
    scope_ref = _clean_text(unit.get("scope_ref") or unit.get("unit_id"))
    scope_type = _clean_text(unit.get("scope_type")) or "layout"
    return {
        "segment_id": scope_ref,
        "source_id": source_id,
        "scope_type": scope_type,
        "scope_ref": scope_ref,
        "page": int(unit.get("page") or 0),
        "order": int(unit.get("order") or 0),
        "section_path": copy.deepcopy(unit.get("section_path") or []),
        "kind": _clean_text(unit.get("kind")) or "paragraph",
        "text": source_text,
        "source_text": source_text,
        "text_hash": source_hash,
        "source_hash": source_hash,
        "locator": _clean_text(unit.get("locator")) or (f"p. {int(unit.get('page') or 0)}" if int(unit.get("page") or 0) else ""),
        "rects": copy.deepcopy(unit.get("rects") or []),
        "table_id": _clean_text(unit.get("table_id")),
        "row": unit.get("row"),
        "col": unit.get("col"),
        "row_span": unit.get("row_span"),
        "col_span": unit.get("col_span"),
    }


def _blank_translation_backend_warning(ai_result: object, translations: list[dict[str, object]]) -> str:
    if not translations or any(translation_text_from_row(row) for row in translations):
        return ""
    backend = _clean_text(getattr(ai_result, "backend", ""))
    generated_by = {
        _clean_text(row.get("generated_by"))
        for row in translations
        if isinstance(row, dict) and _clean_text(row.get("generated_by"))
    }
    warnings = " ".join(str(item) for item in getattr(ai_result, "warnings", []) or [])
    error = _clean_text(getattr(ai_result, "error", ""))
    marker = f"{backend} {' '.join(generated_by)} {warnings} {error}".lower()
    if "rule_fallback" in marker or "llm_api_key" in marker or "ai_not_configured" in marker:
        return _translation_backend_failure_message(marker)
    return ""


def _translation_backend_failure_message(marker: str) -> str:
    if "arrearage" in marker or "overdue-payment" in marker:
        return (
            f"{NO_LLM_TRANSLATION_WARNING} Provider rejected the request: "
            "the configured LLM account appears to have overdue payment or arrears."
        )
    if "too many requests" in marker or " 429 " in marker:
        return (
            f"{NO_LLM_TRANSLATION_WARNING} Provider rejected the request: "
            "rate limit or quota was reached."
        )
    if "llm_api_key" in marker or "ai_not_configured" in marker:
        return (
            f"{NO_LLM_TRANSLATION_WARNING} Configure an LLM API key/model before translating."
        )
    return NO_LLM_TRANSLATION_WARNING


def _positive_int(value: object) -> int | None:
    try:
        clean = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return clean if clean > 0 else None


def _paper_translation_batch_size(scope: str, requested: object = None) -> int:
    explicit = _positive_int(requested)
    if explicit is not None:
        return max(1, min(50, explicit))
    clean_scope = _clean_text(scope).lower()
    env_key = {
        "structure": "NBLANE_PAPER_TRANSLATION_STRUCTURE_BATCH_SIZE",
        "layout": "NBLANE_PAPER_TRANSLATION_LAYOUT_BATCH_SIZE",
        "page": "NBLANE_PAPER_TRANSLATION_PAGE_BATCH_SIZE",
        "segment": "NBLANE_PAPER_TRANSLATION_SEGMENT_BATCH_SIZE",
    }.get(clean_scope, "")
    configured = _positive_int(os.getenv(env_key)) if env_key else None
    if configured is None:
        configured = _positive_int(os.getenv("NBLANE_PAPER_TRANSLATION_BATCH_SIZE"))
    default = {
        "structure": PAPER_STRUCTURE_TRANSLATION_BATCH_SIZE_DEFAULT,
        "layout": PAPER_LAYOUT_TRANSLATION_BATCH_SIZE_DEFAULT,
        "page": PAPER_PAGE_TRANSLATION_BATCH_SIZE_DEFAULT,
    }.get(clean_scope, PAPER_TRANSLATION_BATCH_SIZE_DEFAULT)
    return max(1, min(50, configured if configured is not None else default))


def _paper_translation_batch_char_limit(scope: str) -> int:
    clean_scope = _clean_text(scope).lower()
    env_key = {
        "structure": "NBLANE_PAPER_TRANSLATION_STRUCTURE_BATCH_CHARS",
        "layout": "NBLANE_PAPER_TRANSLATION_LAYOUT_BATCH_CHARS",
        "page": "NBLANE_PAPER_TRANSLATION_PAGE_BATCH_CHARS",
        "segment": "NBLANE_PAPER_TRANSLATION_SEGMENT_BATCH_CHARS",
    }.get(clean_scope, "")
    configured = _positive_int(os.getenv(env_key)) if env_key else None
    if configured is None:
        configured = _positive_int(os.getenv("NBLANE_PAPER_TRANSLATION_BATCH_CHARS"))
    default = PAPER_PAGE_TRANSLATION_BATCH_CHARS_DEFAULT if clean_scope == "page" else PAPER_TRANSLATION_BATCH_CHARS_DEFAULT
    return max(1200, min(60000, configured if configured is not None else default))


def _paper_translation_payload_text(value: object) -> str:
    if isinstance(value, PaperSegment):
        return _clean_text(value.text)
    if isinstance(value, dict):
        return _clean_text(value.get("source_text") or value.get("text"))
    return ""


def _paper_translation_batches(
    items: list[dict[str, object]],
    scope: str,
    requested_batch_size: object = None,
) -> list[list[dict[str, object]]]:
    clean_batch_size = _paper_translation_batch_size(scope, requested_batch_size)
    char_limit = _paper_translation_batch_char_limit(scope)
    batches: list[list[dict[str, object]]] = []
    current: list[dict[str, object]] = []
    current_chars = 0
    for item in items:
        item_chars = max(1, len(_paper_translation_payload_text(item)))
        if current and (len(current) >= clean_batch_size or current_chars + item_chars > char_limit):
            batches.append(current)
            current = []
            current_chars = 0
        current.append(item)
        current_chars += item_chars
    if current:
        batches.append(current)
    return batches


def _persist_translation_batch(
    profile: str | Path,
    source_id: str,
    rows: list[dict[str, object]],
    persisted_count: int,
    warnings: list[str],
) -> int:
    if len(rows) <= persisted_count:
        return persisted_count
    lock = _translation_persist_lock(profile, source_id)
    with lock:
        try:
            upsert_paper_translations(profile, source_id, rows[persisted_count:])
        except Exception as exc:
            warnings.append(f"Saving translation batch failed: {exc}")
            return persisted_count
        return len(rows)


_TRANSLATION_PERSIST_LOCKS: dict[tuple[str, str], threading.RLock] = {}
_TRANSLATION_PERSIST_LOCKS_GUARD = threading.Lock()


def _translation_persist_lock(profile: str | Path, source_id: str) -> threading.RLock:
    """Per-(profile, source) lock that serializes JSONL read-modify-write."""

    key = (str(profile), str(source_id))
    with _TRANSLATION_PERSIST_LOCKS_GUARD:
        lock = _TRANSLATION_PERSIST_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _TRANSLATION_PERSIST_LOCKS[key] = lock
        return lock


def _translation_concurrency() -> int:
    """Return the desired translation batch concurrency.

    Defaults to 4. Override with NBLANE_TRANSLATION_CONCURRENCY=N (1-16).
    A value of 1 keeps the original serial behavior, useful when an LLM
    backend cannot tolerate parallel calls.
    """

    raw = os.getenv("NBLANE_TRANSLATION_CONCURRENCY", "").strip()
    if not raw:
        return 4
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 4
    return max(1, min(16, value))


def _translation_streaming_enabled() -> bool:
    raw = os.getenv("NBLANE_STREAM_PAPER_TRANSLATION", "").strip().lower()
    if not raw:
        return True
    return raw in {"1", "true", "yes", "on"}


def _process_translation_batches(
    batches: list[list[dict[str, object]]],
    *,
    ai_profile_arg: str,
    source_id: str,
    target_lang: str,
    require_review: bool,
    handle_result: Any,  # Callable[[batch, result_or_None, exc_or_None], None]
    progress_lock: threading.Lock,
    stream_callback: Any = None,  # Callable[[batch, str_chunk], None] | None
) -> None:
    """Run translation batches with optional concurrency.

    `handle_result(batch, result, exc)` is called once per batch under
    `progress_lock`. Either `result` is the gateway return value and `exc`
    is None, or `result` is None and `exc` is the exception raised by the
    gateway call.
    """

    if not batches:
        return
    from nblane.core.ai.gateway import translate_paper_segments

    concurrency = max(1, min(_translation_concurrency(), len(batches)))
    streaming = _translation_streaming_enabled()

    def run_one(batch: list[dict[str, object]]):
        kwargs: dict[str, object] = {
            "target_lang": target_lang,
            "require_review": require_review,
        }
        if streaming and stream_callback is not None:
            kwargs["stream_callback"] = lambda chunk, b=batch: stream_callback(b, chunk)
        try:
            result = translate_paper_segments(
                ai_profile_arg,
                source_id,
                batch,
                **kwargs,
            )
            return ("ok", result, batch)
        except TypeError:
            # Gateway might not yet accept stream_callback; retry without it.
            kwargs.pop("stream_callback", None)
            try:
                result = translate_paper_segments(
                    ai_profile_arg,
                    source_id,
                    batch,
                    **kwargs,
                )
                return ("ok", result, batch)
            except Exception as exc:
                return ("err", exc, batch)
        except Exception as exc:
            return ("err", exc, batch)

    if concurrency <= 1:
        for batch in batches:
            tag, payload, b = run_one(batch)
            with progress_lock:
                if tag == "ok":
                    handle_result(b, payload, None)
                else:
                    handle_result(b, None, payload)
        return

    with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="translate-batch") as executor:
        futures = {executor.submit(run_one, batch): batch for batch in batches}
        for fut in as_completed(futures):
            try:
                tag, payload, b = fut.result()
            except Exception as exc:
                tag, payload, b = "err", exc, futures[fut]
            with progress_lock:
                if tag == "ok":
                    handle_result(b, payload, None)
                else:
                    handle_result(b, None, payload)


def translate_full_paper(
    profile: str | Path,
    source_id: str,
    target_lang: str = "zh",
    mode: str = "missing_or_stale",
    batch_size: int | None = None,
    *,
    scope_strategy: str = "segment",
    include_references: bool | None = None,
    ai_profile: str | None = None,
    require_review: bool = True,
    progress_callback: Any | None = None,
) -> dict[str, object]:
    """Translate a paper at segment granularity and persist valid rows.

    Existing translations whose ``source_hash`` still matches the current
    segment are skipped in the default mode. Incoming AI rows without a known
    segment id, with a mismatched hash, or with blank translated text are kept
    from overwriting valid translations and surfaced as warnings.
    """

    clean_lang = _clean_text(target_lang) or "zh"
    clean_mode = _clean_text(mode).lower() or "missing_or_stale"
    clean_scope_strategy = _clean_text(scope_strategy).lower() or "segment"
    if clean_scope_strategy not in {"auto", "segment", "page", "layout", "structure"}:
        clean_scope_strategy = "auto"
    if clean_mode not in {"all", "missing", "stale", "missing_or_stale"}:
        raise ValueError(f"Unknown full-paper translation mode: {mode}")
    requested_batch_size = _positive_int(batch_size)
    clean_include_references = _paper_translation_include_references(include_references)

    segments = load_paper_segments(profile, source_id)
    if not segments:
        ensure_paper_reading_artifacts(profile, source_id, prefer_grobid=True)
        segments = load_paper_segments(profile, source_id)
    pages = load_paper_pages(profile, source_id)
    structure_units = (
        reader_translation_structure_units(
            build_paper_structure_units(profile, source_id),
            include_references=clean_include_references,
        )
        if clean_scope_strategy in {"auto", "structure"}
        else []
    )
    layout_units = (
        reader_translation_layout_units(build_paper_layout_units(profile, source_id))
        if not structure_units and clean_scope_strategy in {"auto", "layout"}
        else []
    )
    positioned_scope_type = "structure" if structure_units else "layout" if layout_units else ""
    layout_units = structure_units or layout_units
    if layout_units:
        translations = load_paper_translations(profile, source_id)
        existing_by_scope = {
            row.scope_ref: row
            for row in translations
            if row.scope_type == positioned_scope_type and row.target_lang == clean_lang
        }
        selected_units: list[dict[str, object]] = []
        for unit in layout_units:
            if not bool(unit.get("translatable", True)):
                continue
            scope_ref = _clean_text(unit.get("scope_ref") or unit.get("unit_id"))
            if not scope_ref:
                continue
            existing = existing_by_scope.get(scope_ref)
            is_current = _layout_translation_is_current(existing, unit, clean_lang)
            is_stale = existing is not None and not is_current
            if clean_mode == "all":
                selected_units.append(unit)
            elif clean_mode == "missing" and existing is None:
                selected_units.append(unit)
            elif clean_mode == "stale" and is_stale:
                selected_units.append(unit)
            elif clean_mode == "missing_or_stale" and (existing is None or is_stale):
                selected_units.append(unit)

        warnings: list[str] = []
        accepted_rows: list[dict[str, object]] = []
        persisted_count = 0
        unit_payloads = [_layout_unit_translation_payload(unit, source_id=source_id) for unit in selected_units]
        unit_map: dict[str, dict[str, object]] = {}
        for unit, payload in zip(selected_units, unit_payloads, strict=False):
            unit_map[_clean_text(payload.get("segment_id"))] = unit
            unit_map[_clean_text(payload.get("scope_ref"))] = unit
        batches = _paper_translation_batches(unit_payloads, positioned_scope_type, requested_batch_size)
        batches_completed = 0
        units_processed = 0
        if progress_callback is not None:
            try:
                progress_callback(
                    {
                        "source_id": source_id,
                        "target_lang": clean_lang,
                        "mode": clean_mode,
                        "scope": positioned_scope_type,
                        "batches": len(batches),
                        "batches_completed": batches_completed,
                        "segments_selected": len(selected_units),
                        "segments_processed": units_processed,
                        "updated": len(accepted_rows),
                        "warnings": len(warnings),
                    }
                )
            except Exception as exc:
                warnings.append(f"Progress callback failed: {exc}")
        if batches:
            progress_lock = threading.Lock()
            ai_profile_arg = ai_profile if ai_profile is not None else _profile_name(profile)

            def emit_progress() -> None:
                if progress_callback is None:
                    return
                try:
                    progress_callback(
                        {
                            "source_id": source_id,
                            "target_lang": clean_lang,
                            "mode": clean_mode,
                            "scope": positioned_scope_type,
                            "batches": len(batches),
                            "batches_completed": batches_completed,
                            "segments_selected": len(selected_units),
                            "segments_processed": units_processed,
                            "updated": len(accepted_rows),
                            "warnings": len(warnings),
                        }
                    )
                except Exception as cb_exc:
                    warnings.append(f"Progress callback failed: {cb_exc}")

            def handle_layout_result(batch: list[dict[str, object]], result, exc) -> None:
                nonlocal batches_completed, units_processed, persisted_count
                if exc is not None:
                    warnings.append(f"Translation batch failed: {exc}")
                    batches_completed += 1
                    units_processed += len(batch)
                    emit_progress()
                    return
                warnings.extend(str(warning) for warning in result.warnings)
                if result.error:
                    warnings.append(result.error)
                structured = result.structured if isinstance(result.structured, dict) else {}
                normalized_rows: list[dict[str, object]] = [
                    normalize_translation_row(raw, source_id=source_id, target_lang=clean_lang)
                    for raw in structured.get("translations") or []
                    if isinstance(raw, dict)
                ]
                backend_warning = _blank_translation_backend_warning(result, normalized_rows)
                if backend_warning and backend_warning not in warnings:
                    warnings.append(backend_warning)
                for row in normalized_rows:
                    row_ref = _clean_text(row.get("segment_id") or row.get("scope_ref"))
                    unit = unit_map.get(row_ref)
                    if unit is None:
                        warnings.append(f"Skipped translation row without a known {positioned_scope_type} scope.")
                        continue
                    source_hash = _clean_text(row.get("source_hash") or row.get("text_hash") or row.get("source_text_hash"))
                    unit_hash = _clean_text(unit.get("source_hash"))
                    if source_hash != unit_hash:
                        warnings.append(f"Skipped translation for {row_ref}: source_hash mismatch.")
                        continue
                    translated_text = translation_text_from_row(row)
                    page_number = int(unit.get("page") or 0)
                    scope_ref = _clean_text(unit.get("scope_ref") or unit.get("unit_id"))
                    if not translated_text:
                        if not backend_warning:
                            warnings.append(f"Skipped translation for {row_ref}: translated_text is blank.")
                        continue
                    accepted_rows.append(
                        {
                            **copy.deepcopy(row),
                            "source_id": source_id,
                            "scope_type": positioned_scope_type,
                            "scope_ref": scope_ref,
                            "segment_id": "",
                            "page": page_number,
                            "order": int(unit.get("order") or 0),
                            "locator": _clean_text(unit.get("locator")) or f"p. {page_number}",
                            "source_hash": unit_hash,
                            "source_text": _clean_text(unit.get("source_text")),
                            "target_lang": clean_lang,
                            "translated_text": translated_text,
                            "rects": copy.deepcopy(unit.get("rects") or []),
                            "status": _choice(row.get("status"), PAPER_TRANSLATION_STATUSES, "translated"),
                        }
                    )
                persisted_count = _persist_translation_batch(
                    profile,
                    source_id,
                    accepted_rows,
                    persisted_count,
                    warnings,
                )
                batches_completed += 1
                units_processed += len(batch)
                emit_progress()

            _process_translation_batches(
                batches,
                ai_profile_arg=ai_profile_arg,
                source_id=source_id,
                target_lang=clean_lang,
                require_review=require_review,
                handle_result=handle_layout_result,
                progress_lock=progress_lock,
            )
        persisted_count = _persist_translation_batch(
            profile,
            source_id,
            accepted_rows,
            persisted_count,
            warnings,
        )
        final_translations = load_paper_translations(profile, source_id)
        counts = _layout_translation_status_counts(
            layout_units,
            final_translations,
            target_lang=clean_lang,
            scope_type=positioned_scope_type,
        )
        return {
            "source_id": source_id,
            "target_lang": clean_lang,
            "mode": clean_mode,
            "scope": positioned_scope_type,
            "include_references": clean_include_references,
            "segments_total": len([unit for unit in layout_units if bool(unit.get("translatable", True))]),
            "segments_selected": len(selected_units),
            "batches": len(batches),
            "updated": len(accepted_rows),
            "translated": counts["translated"],
            "missing": counts["missing"],
            "stale": counts["stale"],
            "failed": counts["failed"],
            "warnings": warnings,
        }
    use_page_scope = bool(pages) and (
        clean_scope_strategy == "page"
        or (clean_scope_strategy == "auto" and segments and not any(segment.page > 0 for segment in segments))
        or (clean_scope_strategy == "auto" and not segments)
    )
    if use_page_scope:
        translations = load_paper_translations(profile, source_id)
        existing_by_scope = {
            row.scope_ref: row
            for row in translations
            if row.scope_type == "page" and row.target_lang == clean_lang
        }
        selected_pages: list[PaperPage] = []
        for page_row in pages:
            if not _clean_text(page_row.text):
                continue
            page_hash = page_row.text_hash or text_hash(page_row.text)
            existing = existing_by_scope.get(f"page:{page_row.page}:{page_hash}")
            is_current = _page_translation_is_current(existing, page_row, clean_lang)
            is_stale = existing is not None and not is_current
            if clean_mode == "all":
                selected_pages.append(page_row)
            elif clean_mode == "missing" and existing is None:
                selected_pages.append(page_row)
            elif clean_mode == "stale" and is_stale:
                selected_pages.append(page_row)
            elif clean_mode == "missing_or_stale" and (existing is None or is_stale):
                selected_pages.append(page_row)

        warnings: list[str] = []
        accepted_rows: list[dict[str, object]] = []
        persisted_count = 0
        page_map: dict[str, PaperPage] = {}
        page_payloads: list[dict[str, object]] = []
        for page_row in selected_pages:
            page_hash = page_row.text_hash or text_hash(page_row.text)
            synthetic_id = f"page:{page_row.page}"
            payload = {
                "segment_id": synthetic_id,
                "source_id": source_id,
                "scope_type": "page",
                "scope_ref": f"page:{page_row.page}:{page_hash}",
                "page": page_row.page,
                "order": page_row.page,
                "section_path": [],
                "kind": "page",
                "text": page_row.text,
                "text_hash": page_hash,
                "locator": f"p. {page_row.page}",
            }
            page_map[synthetic_id] = page_row
            page_map[payload["scope_ref"]] = page_row
            page_payloads.append(payload)
        batches = _paper_translation_batches(page_payloads, "page", requested_batch_size)
        batches_completed = 0
        pages_processed = 0
        if progress_callback is not None:
            try:
                progress_callback(
                    {
                        "source_id": source_id,
                        "target_lang": clean_lang,
                        "mode": clean_mode,
                        "scope": "page",
                        "batches": len(batches),
                        "batches_completed": batches_completed,
                        "segments_selected": len(selected_pages),
                        "segments_processed": pages_processed,
                        "updated": len(accepted_rows),
                        "warnings": len(warnings),
                    }
                )
            except Exception as exc:
                warnings.append(f"Progress callback failed: {exc}")
        if batches:
            progress_lock = threading.Lock()
            ai_profile_arg = ai_profile if ai_profile is not None else _profile_name(profile)

            def emit_progress() -> None:
                if progress_callback is None:
                    return
                try:
                    progress_callback(
                        {
                            "source_id": source_id,
                            "target_lang": clean_lang,
                            "mode": clean_mode,
                            "scope": "page",
                            "batches": len(batches),
                            "batches_completed": batches_completed,
                            "segments_selected": len(selected_pages),
                            "segments_processed": pages_processed,
                            "updated": len(accepted_rows),
                            "warnings": len(warnings),
                        }
                    )
                except Exception as cb_exc:
                    warnings.append(f"Progress callback failed: {cb_exc}")

            def handle_page_result(batch: list[dict[str, object]], result, exc) -> None:
                nonlocal batches_completed, pages_processed, persisted_count
                if exc is not None:
                    warnings.append(f"Translation batch failed: {exc}")
                    batches_completed += 1
                    pages_processed += len(batch)
                    emit_progress()
                    return
                warnings.extend(str(warning) for warning in result.warnings)
                if result.error:
                    warnings.append(result.error)
                structured = result.structured if isinstance(result.structured, dict) else {}
                for raw in structured.get("translations") or []:
                    if not isinstance(raw, dict):
                        continue
                    row = normalize_translation_row(raw, source_id=source_id, target_lang=clean_lang)
                    row_ref = _clean_text(row.get("segment_id") or row.get("scope_ref"))
                    page_row = page_map.get(row_ref)
                    if page_row is None:
                        warnings.append("Skipped translation row without a known page scope.")
                        continue
                    page_hash = page_row.text_hash or text_hash(page_row.text)
                    source_hash = _clean_text(row.get("source_hash") or row.get("text_hash") or row.get("source_text_hash"))
                    if source_hash != page_hash:
                        warnings.append(f"Skipped translation for page {page_row.page}: source_hash mismatch.")
                        continue
                    translated_text = translation_text_from_row(row)
                    if not translated_text:
                        warnings.append(f"Skipped translation for page {page_row.page}: translated_text is blank.")
                        existing = existing_by_scope.get(f"page:{page_row.page}:{page_hash}")
                        if not _page_translation_is_current(existing, page_row, clean_lang):
                            accepted_rows.append(
                                {
                                    **copy.deepcopy(row),
                                    "source_id": source_id,
                                    "scope_type": "page",
                                    "scope_ref": f"page:{page_row.page}:{page_hash}",
                                    "segment_id": "",
                                    "page": page_row.page,
                                    "order": page_row.page,
                                    "locator": f"p. {page_row.page}",
                                    "source_hash": page_hash,
                                    "source_text": page_row.text,
                                    "target_lang": clean_lang,
                                    "translated_text": "",
                                    "status": "failed",
                                    "warnings": _clean_list(row.get("warnings")) + ["translated_text is blank."],
                                }
                            )
                        continue
                    accepted_rows.append(
                        {
                            **copy.deepcopy(row),
                            "source_id": source_id,
                            "scope_type": "page",
                            "scope_ref": f"page:{page_row.page}:{page_hash}",
                            "segment_id": "",
                            "page": page_row.page,
                            "order": page_row.page,
                            "locator": f"p. {page_row.page}",
                            "source_hash": page_hash,
                            "source_text": page_row.text,
                            "target_lang": clean_lang,
                            "translated_text": translated_text,
                            "status": _choice(row.get("status"), PAPER_TRANSLATION_STATUSES, "translated"),
                        }
                    )
                persisted_count = _persist_translation_batch(
                    profile,
                    source_id,
                    accepted_rows,
                    persisted_count,
                    warnings,
                )
                batches_completed += 1
                pages_processed += len(batch)
                emit_progress()

            _process_translation_batches(
                batches,
                ai_profile_arg=ai_profile_arg,
                source_id=source_id,
                target_lang=clean_lang,
                require_review=require_review,
                handle_result=handle_page_result,
                progress_lock=progress_lock,
            )
        persisted_count = _persist_translation_batch(
            profile,
            source_id,
            accepted_rows,
            persisted_count,
            warnings,
        )
        final_translations = load_paper_translations(profile, source_id)
        counts = _page_translation_status_counts(pages, final_translations, target_lang=clean_lang)
        return {
            "source_id": source_id,
            "target_lang": clean_lang,
            "mode": clean_mode,
            "scope": "page",
            "include_references": clean_include_references,
            "segments_total": len(pages),
            "segments_selected": len(selected_pages),
            "batches": len(batches),
            "updated": len(accepted_rows),
            "translated": counts["translated"],
            "missing": counts["missing"],
            "stale": counts["stale"],
            "failed": counts["failed"],
            "warnings": warnings,
        }
    translations = load_paper_translations(profile, source_id)
    existing_by_segment = {
        row.segment_id: row
        for row in translations
        if row.segment_id and row.target_lang == clean_lang
    }
    translation_segments = [
        segment
        for segment in segments
        if clean_include_references or not _paper_segment_is_reference_section(segment)
    ]
    selected_segments: list[PaperSegment] = []
    for segment in translation_segments:
        existing = existing_by_segment.get(segment.segment_id)
        is_current = _translation_is_current(existing, segment, clean_lang)
        is_stale = existing is not None and not is_current
        if clean_mode == "all":
            selected_segments.append(segment)
        elif clean_mode == "missing" and existing is None:
            selected_segments.append(segment)
        elif clean_mode == "stale" and is_stale:
            selected_segments.append(segment)
        elif clean_mode == "missing_or_stale" and (existing is None or is_stale):
            selected_segments.append(segment)

    warnings: list[str] = []
    accepted_rows: list[dict[str, object]] = []
    persisted_count = 0
    segment_map = {segment.segment_id: segment for segment in selected_segments}
    segment_payloads = [segment.to_dict() for segment in selected_segments]
    batches = _paper_translation_batches(segment_payloads, "segment", requested_batch_size)
    batches_completed = 0
    segments_processed = 0
    if progress_callback is not None:
        try:
            progress_callback(
                {
                    "source_id": source_id,
                    "target_lang": clean_lang,
                    "mode": clean_mode,
                    "scope": "segment",
                    "batches": len(batches),
                    "batches_completed": batches_completed,
                    "segments_selected": len(selected_segments),
                    "segments_processed": segments_processed,
                    "updated": len(accepted_rows),
                    "warnings": len(warnings),
                }
            )
        except Exception as exc:
            warnings.append(f"Progress callback failed: {exc}")
    if batches:
        progress_lock = threading.Lock()
        ai_profile_arg = ai_profile if ai_profile is not None else _profile_name(profile)

        def emit_progress() -> None:
            if progress_callback is None:
                return
            try:
                progress_callback(
                    {
                        "source_id": source_id,
                        "target_lang": clean_lang,
                        "mode": clean_mode,
                        "batches": len(batches),
                        "batches_completed": batches_completed,
                        "segments_selected": len(selected_segments),
                        "segments_processed": segments_processed,
                        "updated": len(accepted_rows),
                        "warnings": len(warnings),
                    }
                )
            except Exception as cb_exc:
                warnings.append(f"Progress callback failed: {cb_exc}")

        def handle_segment_result(batch: list[dict[str, object]], result, exc) -> None:
            nonlocal batches_completed, segments_processed, persisted_count
            if exc is not None:
                warnings.append(f"Translation batch failed: {exc}")
                batches_completed += 1
                segments_processed += len(batch)
                emit_progress()
                return
            warnings.extend(str(warning) for warning in result.warnings)
            if result.error:
                warnings.append(result.error)
            structured = result.structured if isinstance(result.structured, dict) else {}
            for raw in structured.get("translations") or []:
                if not isinstance(raw, dict):
                    continue
                row = normalize_translation_row(raw, source_id=source_id, target_lang=clean_lang)
                segment_id = _clean_text(row.get("segment_id") or row.get("scope_ref"))
                if not segment_id or segment_id not in segment_map:
                    warnings.append("Skipped translation row without a known segment_id.")
                    continue
                segment = segment_map[segment_id]
                source_hash = _clean_text(
                    row.get("source_hash")
                    or row.get("text_hash")
                    or row.get("source_text_hash")
                )
                if source_hash != segment.text_hash:
                    warnings.append(f"Skipped translation for {segment_id}: source_hash mismatch.")
                    continue
                translated_text = translation_text_from_row(row)
                if not translated_text:
                    warnings.append(f"Skipped translation for {segment_id}: translated_text is blank.")
                    existing = existing_by_segment.get(segment_id)
                    if not _translation_is_current(existing, segment, clean_lang):
                        accepted_rows.append(
                            {
                                **copy.deepcopy(row),
                                "source_id": source_id,
                                "scope_type": "segment",
                                "scope_ref": segment.segment_id,
                                "segment_id": segment.segment_id,
                                "page": segment.page,
                                "source_hash": segment.text_hash,
                                "source_text": segment.text,
                                "target_lang": clean_lang,
                                "translated_text": "",
                                "status": "failed",
                                "warnings": _clean_list(row.get("warnings"))
                                + ["translated_text is blank."],
                            }
                        )
                    continue
                accepted_rows.append(
                    {
                        **copy.deepcopy(row),
                        "source_id": source_id,
                        "scope_type": "segment",
                        "scope_ref": segment.segment_id,
                        "segment_id": segment.segment_id,
                        "page": segment.page,
                        "source_hash": segment.text_hash,
                        "source_text": segment.text,
                        "target_lang": clean_lang,
                        "translated_text": translated_text,
                        "status": _choice(row.get("status"), PAPER_TRANSLATION_STATUSES, "translated"),
                    }
                )
            persisted_count = _persist_translation_batch(
                profile,
                source_id,
                accepted_rows,
                persisted_count,
                warnings,
            )
            batches_completed += 1
            segments_processed += len(batch)
            emit_progress()

        _process_translation_batches(
            batches,
            ai_profile_arg=ai_profile_arg,
            source_id=source_id,
            target_lang=clean_lang,
            require_review=require_review,
            handle_result=handle_segment_result,
            progress_lock=progress_lock,
        )

    persisted_count = _persist_translation_batch(
        profile,
        source_id,
        accepted_rows,
        persisted_count,
        warnings,
    )
    final_translations = load_paper_translations(profile, source_id)
    counts = _translation_status_counts(translation_segments, final_translations, target_lang=clean_lang)
    return {
        "source_id": source_id,
        "target_lang": clean_lang,
        "mode": clean_mode,
        "scope": "segment",
        "include_references": clean_include_references,
        "segments_total": len(translation_segments),
        "segments_selected": len(selected_segments),
        "batches": len(batches),
        "updated": len(accepted_rows),
        "translated": counts["translated"],
        "missing": counts["missing"],
        "stale": counts["stale"],
        "failed": counts["failed"],
        "warnings": warnings,
    }


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


def _library_tree_path(profile: str | Path) -> Path:
    return _research_root(profile) / LIBRARY_TREE_FILENAME


def load_paper_library_tree(profile: str | Path) -> PaperLibraryTree:
    path = _library_tree_path(profile)
    raw = _load_yaml_dict(path) or {}
    tree = PaperLibraryTree.from_dict(raw)
    if not tree.profile:
        tree.profile = _profile_name(profile)
    return tree


def save_paper_library_tree(profile: str | Path, tree: PaperLibraryTree | dict) -> Path:
    path = _library_tree_path(profile)
    doc = tree if isinstance(tree, PaperLibraryTree) else PaperLibraryTree.from_dict(tree)
    doc.profile = doc.profile or _profile_name(profile)
    doc.updated = _today()
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.dump(doc.to_dict(), allow_unicode=True, default_flow_style=False, sort_keys=False)
    atomic_write_text(path, f"# Paper library tree for {doc.profile}\n\n" + body)
    git_backup.record_change([path], action=f"update {doc.profile}/research/library-tree.yaml")
    return path


def _paper_library_root_parent(parent_id: object) -> str:
    clean = _clean_text(parent_id)
    return "" if clean in {"", "root", "paper-root", "paper-library-root"} else clean


def _paper_library_require_node(
    tree: PaperLibraryTree,
    node_id: str,
    *,
    include_trashed: bool = False,
) -> PaperLibraryNode:
    clean = _clean_text(node_id)
    if not clean or clean in {"root", "paper-root", "paper-library-root"}:
        raise ValueError("The Paper Library root cannot be changed.")
    for node in tree.nodes:
        if node.id != clean:
            continue
        if node.status == "trashed" and not include_trashed:
            raise ValueError(f"Paper library node is in trash: {clean}")
        return node
    raise ValueError(f"Unknown paper library node: {clean}")


def _paper_library_parent_id(tree: PaperLibraryTree, parent_id: object) -> str:
    clean = _paper_library_root_parent(parent_id)
    if not clean:
        return ""
    node = _paper_library_require_node(tree, clean)
    if node.status == "trashed":
        raise ValueError(f"Paper library parent is in trash: {clean}")
    return clean


def _paper_library_children_by_parent(
    tree: PaperLibraryTree,
    *,
    include_trashed: bool = False,
) -> dict[str, list[PaperLibraryNode]]:
    children: dict[str, list[PaperLibraryNode]] = {}
    for node in tree.nodes:
        if node.status == "trashed" and not include_trashed:
            continue
        children.setdefault(node.parent_id or "", []).append(node)
    for siblings in children.values():
        siblings.sort(key=lambda item: (item.order, item.title.lower(), item.id))
    return children


def _paper_library_next_order(tree: PaperLibraryTree, parent_id: str) -> int:
    siblings = _paper_library_children_by_parent(tree).get(parent_id or "", [])
    return (max((node.order for node in siblings), default=0) // 10 + 1) * 10


def _paper_library_unique_node_id(tree: PaperLibraryTree, title: str) -> str:
    base = f"paper-node:{_slug(title, fallback='collection')}"
    existing = {node.id for node in tree.nodes}
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def _paper_library_descendant_ids(
    tree: PaperLibraryTree,
    node_id: str,
    *,
    include_trashed: bool = True,
) -> list[str]:
    children = _paper_library_children_by_parent(tree, include_trashed=include_trashed)
    out: list[str] = []

    def walk(parent: str, seen: set[str]) -> None:
        for child in children.get(parent, []):
            if child.id in seen:
                continue
            out.append(child.id)
            walk(child.id, seen | {child.id})

    walk(_clean_text(node_id), {_clean_text(node_id)})
    return out


def _paper_library_assert_not_descendant_parent(
    tree: PaperLibraryTree,
    *,
    node: PaperLibraryNode,
    parent_id: str,
) -> None:
    parent = _paper_library_root_parent(parent_id)
    if not parent:
        return
    if parent == node.id:
        raise ValueError("A paper library node cannot be moved under itself.")
    nodes = tree.by_id()
    cursor = nodes.get(parent)
    seen: set[str] = set()
    while cursor is not None and cursor.id not in seen:
        if cursor.id == node.id:
            raise ValueError("A paper library node cannot be moved under its descendant.")
        seen.add(cursor.id)
        cursor = nodes.get(cursor.parent_id)


def _normalize_paper_library_sibling_orders(
    tree: PaperLibraryTree,
    parent_ids: set[str] | None = None,
) -> None:
    children = _paper_library_children_by_parent(tree)
    wanted = set(children) if parent_ids is None else {parent_id or "" for parent_id in parent_ids}
    for parent_id in wanted:
        siblings = children.get(parent_id, [])
        for index, node in enumerate(siblings, start=1):
            node.order = index * 10


def _paper_library_policy_target(
    tree: PaperLibraryTree,
    paper_policy: str,
    *,
    fallback_parent_id: str,
    deleted_ids: set[str],
) -> str:
    policy = _clean_text(paper_policy) or "move_to_parent"
    if policy in {"cancel", "cancel_delete"}:
        raise ValueError("Paper library delete was cancelled.")
    if policy == "move_to_parent":
        target = fallback_parent_id or ""
    elif policy == "move_to_unsorted":
        target = ""
    elif policy.startswith("move_to:"):
        target = _clean_text(policy.split(":", 1)[1])
    elif policy.startswith("move_to_node:"):
        target = _clean_text(policy.split(":", 1)[1])
    else:
        raise ValueError(f"Unknown paper library delete policy: {paper_policy}")
    if target:
        if target in deleted_ids:
            raise ValueError("Papers cannot be moved into a collection that is being deleted.")
        _paper_library_require_node(tree, target)
    return target


def _apply_paper_library_delete_policy(
    profile: str | Path,
    tree: PaperLibraryTree,
    node_ids: list[str],
    *,
    paper_policy: str,
    fallback_parent_id: str,
) -> list[str]:
    deleted = set(_clean_list(node_ids))
    if not deleted:
        return []
    target = _paper_library_policy_target(
        tree,
        paper_policy,
        fallback_parent_id=fallback_parent_id,
        deleted_ids=deleted,
    )
    inbox = load_research_sources(_profile_root(profile))
    changed: list[str] = []
    for source in inbox.sources:
        refs = list(source.library_node_refs)
        if not any(ref in deleted for ref in refs):
            continue
        next_refs: list[str] = []
        inserted_target = False
        for ref in refs:
            if ref in deleted:
                if target and not inserted_target and target not in next_refs:
                    next_refs.append(target)
                    inserted_target = True
                continue
            if ref not in next_refs:
                next_refs.append(ref)
        if next_refs != refs:
            source.library_node_refs = next_refs
            changed.append(source.id)
    if changed:
        save_research_sources(_profile_root(profile), inbox)
    return changed


def create_paper_library_node(
    profile: str | Path,
    title: str,
    parent_id: str = "",
    description: str = "",
    color: str = "",
    icon: str = "",
) -> PaperLibraryNode:
    clean_title = _clean_text(title)
    if not clean_title:
        raise ValueError("Paper library node title cannot be blank.")
    tree = load_paper_library_tree(profile)
    parent = _paper_library_parent_id(tree, parent_id)
    node = PaperLibraryNode(
        id=_paper_library_unique_node_id(tree, clean_title),
        title=clean_title,
        parent_id=parent,
        description=_clean_text(description),
        color=_clean_text(color),
        icon=_clean_text(icon),
        order=_paper_library_next_order(tree, parent),
        created_by="user",
    )
    tree.nodes.append(node)
    save_paper_library_tree(profile, tree)
    return node


def rename_paper_library_node(
    profile: str | Path,
    node_id: str,
    title: str,
) -> PaperLibraryNode:
    clean_title = _clean_text(title)
    if not clean_title:
        raise ValueError("Paper library node title cannot be blank.")
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id)
    node.title = clean_title
    save_paper_library_tree(profile, tree)
    return node


def position_paper_library_node(
    profile: str | Path,
    node_id: str,
    parent_id: str = "",
    before_node_id: str = "",
    after_node_id: str = "",
) -> PaperLibraryNode:
    before_id = _clean_text(before_node_id)
    after_id = _clean_text(after_node_id)
    if before_id and after_id:
        raise ValueError("Use either before_node_id or after_node_id, not both.")
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id)

    target: PaperLibraryNode | None = None
    insert_after = False
    if before_id or after_id:
        target_id = before_id or after_id
        if target_id == node.id:
            raise ValueError("A paper library node cannot be positioned relative to itself.")
        target = _paper_library_require_node(tree, target_id)
        parent = target.parent_id or ""
        insert_after = bool(after_id)
    else:
        parent = _paper_library_parent_id(tree, parent_id)

    _paper_library_assert_not_descendant_parent(tree, node=node, parent_id=parent)

    before_state = {item.id: (item.parent_id, item.order) for item in tree.nodes}
    children = _paper_library_children_by_parent(tree)
    old_parent = node.parent_id or ""
    siblings = [
        item
        for item in children.get(parent, [])
        if item.id != node.id
    ]
    if target is not None:
        target_pos = next((index for index, item in enumerate(siblings) if item.id == target.id), -1)
        if target_pos < 0:
            raise ValueError(f"Unknown paper library position target: {target.id}")
        insert_pos = target_pos + 1 if insert_after else target_pos
    else:
        insert_pos = len(siblings)
    next_siblings = list(siblings)
    next_siblings.insert(insert_pos, node)
    node.parent_id = parent
    for index, item in enumerate(next_siblings, start=1):
        item.order = index * 10
    if old_parent != parent:
        _normalize_paper_library_sibling_orders(tree, {old_parent})

    after_state = {item.id: (item.parent_id, item.order) for item in tree.nodes}
    if before_state != after_state:
        save_paper_library_tree(profile, tree)
    return node


def reorder_paper_library_node(
    profile: str | Path,
    node_id: str,
    direction: str,
) -> PaperLibraryNode:
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id)
    siblings = _paper_library_children_by_parent(tree).get(node.parent_id or "", [])
    pos = next((index for index, item in enumerate(siblings) if item.id == node.id), -1)
    if pos < 0:
        raise ValueError(f"Unknown paper library node: {node_id}")
    clean_direction = _clean_text(direction).lower()
    if clean_direction in {"up", "before"}:
        target_pos = pos - 1
    elif clean_direction in {"down", "after"}:
        target_pos = pos + 1
    else:
        raise ValueError("Paper library reorder direction must be up or down.")
    if target_pos < 0 or target_pos >= len(siblings):
        return node
    siblings[pos], siblings[target_pos] = siblings[target_pos], siblings[pos]
    for index, item in enumerate(siblings, start=1):
        item.order = index * 10
    save_paper_library_tree(profile, tree)
    return node


def trash_paper_library_node(
    profile: str | Path,
    node_id: str,
    paper_policy: str = "move_to_parent",
) -> PaperLibraryNode:
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id)
    ids = [node.id, *_paper_library_descendant_ids(tree, node.id)]
    _apply_paper_library_delete_policy(
        profile,
        tree,
        ids,
        paper_policy=paper_policy,
        fallback_parent_id=node.parent_id,
    )
    now = _now()
    id_set = set(ids)
    for item in tree.nodes:
        if item.id not in id_set or item.status == "trashed":
            continue
        item.trashed_from_parent_id = item.parent_id
        item.trashed_from_order = item.order
        item.trashed_at = now
        item.status = "trashed"
    _normalize_paper_library_sibling_orders(tree, {node.parent_id or ""})
    save_paper_library_tree(profile, tree)
    return node


def restore_paper_library_node(
    profile: str | Path,
    node_id: str,
) -> PaperLibraryNode:
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id, include_trashed=True)
    ids = [node.id, *_paper_library_descendant_ids(tree, node.id)]
    id_set = set(ids)
    active_ids = {item.id for item in tree.nodes if item.status != "trashed"}
    touched_parents: set[str] = set()
    for item in tree.nodes:
        if item.id not in id_set:
            continue
        parent = item.trashed_from_parent_id or item.parent_id or ""
        if parent and parent not in active_ids and parent not in id_set:
            parent = ""
        item.parent_id = parent
        if item.trashed_from_order is not None:
            item.order = item.trashed_from_order
        item.status = "active"
        item.trashed_at = ""
        item.trashed_from_parent_id = ""
        item.trashed_from_order = None
        touched_parents.add(parent)
    _normalize_paper_library_sibling_orders(tree, touched_parents or None)
    save_paper_library_tree(profile, tree)
    return node


def purge_paper_library_node(
    profile: str | Path,
    node_id: str,
    paper_policy: str = "move_to_unsorted",
) -> PaperLibraryNode:
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id, include_trashed=True)
    ids = [node.id, *_paper_library_descendant_ids(tree, node.id)]
    _apply_paper_library_delete_policy(
        profile,
        tree,
        ids,
        paper_policy=paper_policy,
        fallback_parent_id=node.parent_id,
    )
    id_set = set(ids)
    tree.nodes = [item for item in tree.nodes if item.id not in id_set]
    _normalize_paper_library_sibling_orders(tree)
    save_paper_library_tree(profile, tree)
    return node


def upsert_paper_library_node(
    profile: str | Path,
    title: str,
    *,
    node_id: str = "",
    parent_id: str = "",
    description: str = "",
    color: str = "",
    icon: str = "",
    order: int = 0,
    created_by: str = "user",
    project_refs: object = None,
    goal_refs: object = None,
) -> PaperLibraryNode:
    clean_title = _clean_text(title)
    if not clean_title:
        raise ValueError("Paper library node title cannot be blank.")
    tree = load_paper_library_tree(profile)
    clean_id = _clean_text(node_id) or f"paper-node:{_slug(clean_title, fallback='topic')}"
    clean_parent = _paper_library_root_parent(parent_id)
    if clean_parent == clean_id:
        raise ValueError("Paper library node cannot be its own parent.")
    nodes = tree.by_id()
    if clean_parent and clean_parent not in nodes:
        raise ValueError(f"Unknown parent paper library node: {clean_parent}")
    node = PaperLibraryNode(
        id=clean_id,
        title=clean_title,
        parent_id=clean_parent,
        description=_clean_text(description),
        color=_clean_text(color),
        icon=_clean_text(icon),
        order=int(order or 0),
        created_by=_clean_text(created_by) or "user",
        project_refs=_clean_list(project_refs),
        goal_refs=_clean_list(goal_refs),
    )
    replaced = False
    for index, existing in enumerate(tree.nodes):
        if existing.id == clean_id:
            tree.nodes[index] = node
            replaced = True
            break
    if not replaced:
        tree.nodes.append(node)
    save_paper_library_tree(profile, tree)
    return node


def paper_library_path(tree: PaperLibraryTree, node_id: str) -> str:
    nodes = tree.by_id()
    path: list[str] = []
    seen: set[str] = set()
    cur = nodes.get(_clean_text(node_id))
    while cur is not None and cur.id not in seen:
        seen.add(cur.id)
        path.append(cur.title)
        cur = nodes.get(cur.parent_id)
    return " / ".join(reversed(path))


def paper_library_paths(profile: str | Path) -> dict[str, str]:
    tree = load_paper_library_tree(profile)
    return {node.id: paper_library_path(tree, node.id) for node in tree.nodes}


def move_papers_to_node(
    profile: str | Path,
    source_ids: list[str],
    node_id: str,
    *,
    append: bool = False,
) -> list[str]:
    tree = load_paper_library_tree(profile)
    clean_node = _clean_text(node_id)
    if clean_node:
        _paper_library_require_node(tree, clean_node)
    inbox = load_research_sources(_profile_root(profile))
    changed: list[str] = []
    wanted = set(_clean_list(source_ids))
    for source in inbox.sources:
        if source.id not in wanted:
            continue
        existing_refs = list(source.library_node_refs)
        if append:
            refs = list(existing_refs)
            if clean_node and clean_node not in refs:
                refs.append(clean_node)
        elif clean_node:
            refs = [
                clean_node,
                *[
                    ref
                    for ref in existing_refs[1:]
                    if ref and ref != clean_node
                ],
            ]
        else:
            refs = []
        if refs == existing_refs:
            continue
        source.library_node_refs = refs
        changed.append(source.id)
    if changed:
        save_research_sources(_profile_root(profile), inbox)
    return changed


def remove_papers_from_node(
    profile: str | Path,
    source_ids: list[str],
    node_id: str,
) -> list[str]:
    tree = load_paper_library_tree(profile)
    clean_node = _clean_text(node_id)
    _paper_library_require_node(tree, clean_node, include_trashed=True)
    inbox = load_research_sources(_profile_root(profile))
    wanted = set(_clean_list(source_ids))
    changed: list[str] = []
    for source in inbox.sources:
        if source.id not in wanted:
            continue
        refs = [ref for ref in source.library_node_refs if ref != clean_node]
        if refs == source.library_node_refs:
            continue
        source.library_node_refs = refs
        changed.append(source.id)
    if changed:
        save_research_sources(_profile_root(profile), inbox)
    return changed


def set_paper_primary_node(
    profile: str | Path,
    source_id: str,
    node_id: str,
) -> ResearchSource:
    clean_source = _clean_text(source_id)
    changed = move_papers_to_node(profile, [clean_source], node_id, append=False)
    inbox = load_research_sources(_profile_root(profile))
    source = inbox.by_id().get(clean_source)
    if source is None:
        raise ValueError(f"Unknown research source: {clean_source}")
    if not changed and _clean_text(node_id):
        tree = load_paper_library_tree(profile)
        _paper_library_require_node(tree, _clean_text(node_id))
    return source


def validate_paper_library(profile: str | Path) -> list[str]:
    diagnostics: list[str] = []
    tree = load_paper_library_tree(profile)
    nodes = tree.by_id()
    for node in tree.nodes:
        if node.id in {"root", "paper-root", "paper-library-root"}:
            diagnostics.append(f"{node.id}: root must stay virtual")
        if node.parent_id and node.parent_id not in nodes:
            diagnostics.append(f"{node.id}: unknown parent node {node.parent_id}")
        if node.parent_id == node.id:
            diagnostics.append(f"{node.id}: node cannot be its own parent")
    for source in load_research_sources(_profile_root(profile)).sources:
        if source.kind != "paper":
            continue
        for ref in source.library_node_refs:
            if ref not in nodes:
                diagnostics.append(f"{source.id}: unknown library node ref {ref}")
            elif nodes[ref].status == "trashed":
                diagnostics.append(f"{source.id}: trashed library node ref {ref}")
    return diagnostics


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


def _search_debug(debug: dict[str, Any] | None) -> dict[str, Any] | None:
    if debug is None:
        return None
    debug.setdefault("steps", [])
    debug.setdefault("warnings", [])
    return debug


def _append_search_warning(debug: dict[str, Any] | None, warning: str) -> None:
    target = _search_debug(debug)
    clean = _clean_text(warning)
    if target is None or not clean:
        return
    warnings = target.setdefault("warnings", [])
    if clean not in warnings:
        warnings.append(clean)


def _append_search_step(debug: dict[str, Any] | None, step: dict[str, object]) -> None:
    target = _search_debug(debug)
    if target is None:
        return
    clean_step = {key: value for key, value in step.items() if value not in ("", [], None)}
    target.setdefault("steps", []).append(clean_step)
    progress = target.get("_progress_callback")
    if callable(progress):
        try:
            progress({"event": "step", "step": clean_step})
        except Exception:
            pass


def _int_filter(value: object) -> int | None:
    clean = _clean_text(value)
    if not re.fullmatch(r"(19|20)\d{2}", clean):
        return None
    return int(clean)


def _paper_search_year_range(filters: dict | None) -> tuple[int | None, int | None]:
    filters = filters or {}
    year_from = _int_filter(filters.get("year_from"))
    year_to = _int_filter(filters.get("year_to"))
    if year_from is not None and year_to is not None and year_from > year_to:
        year_from, year_to = year_to, year_from
    return year_from, year_to


def _paper_search_time_left(filters: dict | None, default: float) -> float:
    deadline = (filters or {}).get("_deadline_monotonic")
    try:
        deadline_value = float(deadline)
    except (TypeError, ValueError):
        return max(0.1, default)
    return max(0.0, min(default, deadline_value - time.monotonic()))


def _paper_search_cancelled(filters: dict | None = None, debug: dict[str, Any] | None = None) -> bool:
    callback = (filters or {}).get("_cancel_check")
    if not callable(callback):
        target = _search_debug(debug)
        callback = target.get("_cancel_check") if target is not None else None
    if not callable(callback):
        return False
    try:
        return bool(callback())
    except Exception:
        return False


def _copy_paper_search_filters(filters: dict | None) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for key, value in (filters or {}).items():
        if str(key).startswith("_") or callable(value):
            copied[key] = value
        else:
            copied[key] = copy.deepcopy(value)
    return copied


def _paper_search_result_matches_year(result: PaperSearchResult, filters: dict | None) -> bool:
    year_from, year_to = _paper_search_year_range(filters)
    if year_from is None and year_to is None:
        return True
    year = _int_filter(result.year)
    if year is None:
        return False
    if year_from is not None and year < year_from:
        return False
    if year_to is not None and year > year_to:
        return False
    return True


def _paper_search_query_variants(query: str, filters: dict | None = None) -> list[str]:
    """Return a small ordered set of practical paper-search query variants."""

    clean = " ".join(_clean_text(query).split())
    if not clean:
        return []
    variants: list[str] = []

    def add(value: str) -> None:
        value = " ".join(_clean_text(value).split())
        if value and value.lower() not in {item.lower() for item in variants}:
            variants.append(value)

    core = _paper_search_query_core(clean)
    lowered = clean.lower()
    mentions_vla = _paper_search_mentions_vla(clean)
    mentions_memory = "memory" in lowered or "mem" in lowered or "记忆" in clean
    wants_recent = _paper_search_recent_requested(clean)
    wants_survey = _paper_search_survey_requested(clean)
    if mentions_vla and mentions_memory:
        add("MemoryVLA")
        add('"Vision-Language-Action" memory robot')
        add("VLA memory robotic manipulation")
        add("vla memory robot")
        add(core)
        if core.lower() != clean.lower():
            add(clean)
    elif mentions_vla:
        if core and core.lower() not in {"vla", "vlas"}:
            add(core)
            replaced = _paper_search_replace_standalone_vla(core)
            if replaced.lower() != core.lower():
                add(replaced)
        add("vision language action robotics manipulation")
        if wants_recent:
            add("Vision-Language-Action robot manipulation latest")
        add("VLA robot manipulation")
        if core.lower() != clean.lower():
            add(clean)
    else:
        add(core)
        if wants_recent:
            add(f"{core} latest")
            add(f"{core} recent papers")
        if wants_survey:
            add(f"{core} survey")
        if core.lower() != clean.lower():
            add(clean)
    explicit = _clean_list((filters or {}).get("query_variants"))
    for item in explicit:
        add(item)
    return variants[:6]


def _paper_search_mentions_vla(query: str) -> bool:
    lowered = _clean_text(query).lower()
    return any(
        term in lowered
        for term in ("vla", "vlas", "vision-language-action", "vision language action")
    )


def _paper_search_recent_requested(query: str) -> bool:
    lowered = _clean_text(query).lower()
    return any(
        marker in lowered
        for marker in (
            "最新",
            "近期",
            "近年",
            "最近",
            "新近",
            "latest",
            "recent",
            "newest",
            "state of the art",
            "sota",
        )
    )


def _paper_search_survey_requested(query: str) -> bool:
    lowered = _clean_text(query).lower()
    return any(marker in lowered for marker in ("综述", "survey", "review", "overview"))


def _paper_search_query_core(query: str) -> str:
    """Strip UI/search-intent words that hurt scholarly provider search."""

    clean = " ".join(_clean_text(query).split())
    if not clean:
        return ""
    core = clean
    for phrase in (
        "最新论文",
        "最新文献",
        "近期论文",
        "近年论文",
        "最近论文",
        "论文推荐",
        "推荐论文",
    ):
        core = core.replace(phrase, " ")
    for phrase in ("论文", "文献", "文章", "最新", "近期", "近年", "最近", "新近", "推荐", "搜索", "搜一下", "查找", "找"):
        core = core.replace(phrase, " ")
    core = re.sub(
        r"(?i)\b(latest|recent|newest|new|paper|papers|publication|publications|recommend|recommendations?|find|search)\b",
        " ",
        core,
    )
    core = re.sub(r"\s+", " ", core).strip(" ,，。;；:：")
    return core or clean


def _paper_search_replace_standalone_vla(query: str) -> str:
    return re.sub(
        r"(?i)(?<![A-Za-z0-9])vlas?(?![A-Za-z0-9])",
        "Vision-Language-Action",
        _clean_text(query),
    )


def _paper_search_normalized_terms(query: str) -> list[str]:
    return [
        term
        for term in re.findall(r"[a-z0-9][a-z0-9-]{1,}", _clean_text(query).lower())
        if term not in {"the", "and", "with", "for", "from", "paper", "papers"}
    ]


def _paper_search_relevance_score(result: PaperSearchResult, query: str) -> float:
    title = result.title.lower()
    body = " ".join(
        [
            result.abstract,
            " ".join(result.tags),
            " ".join(result.fields_of_study),
            " ".join(result.provider_refs),
        ]
    ).lower()
    query_terms = _paper_search_normalized_terms(query)
    score = 0.0
    for term in query_terms:
        if term in title:
            score += 5.0
        if term in body:
            score += 1.0
    if _clean_text(query).lower() and _clean_text(query).lower() in title:
        score += 4.0
    lowered_query = _clean_text(query).lower()
    if "vla" in lowered_query and "memory" in lowered_query:
        if "memory" in title:
            score += 5.0
        if "vla" in title or "vision-language-action" in title or "vision language action" in title:
            score += 5.0
        if any(
            marker in " ".join([title, body])
            for marker in (
                "vision-language-action",
                "vision language action",
                "robot",
                "robotic",
                "manipulation",
                "embodied",
                "vla model",
                "vlas",
            )
        ):
            score += 10.0
        if any(marker in " ".join([title, body]) for marker in ("integrin", "cd4", "t cell", "hiv provirus")):
            score -= 12.0
    if result.pdf_url:
        score += 2.0
    if "arxiv" in result.provider_refs:
        score += 1.0
    year = _int_filter(result.year)
    if year is not None:
        score += min(max(year - 2000, 0), 40) / 100.0
        if _paper_search_recent_requested(query):
            current_year = date.today().year
            if year >= current_year:
                score += 5.0
            elif year == current_year - 1:
                score += 3.0
            elif year == current_year - 2:
                score += 1.0
    return score


def _paper_search_reason_is_generic(value: str) -> bool:
    clean = _clean_text(value)
    if not clean:
        return True
    lowered = clean.rstrip(".").lower()
    return lowered in {
        "matched provider search query",
        "manual url / doi import candidate",
        "provided search candidate; verify url/doi before import",
    } or lowered.startswith("matched arxiv web search query:")


def _paper_search_provider_label(result: PaperSearchResult) -> str:
    labels: list[str] = []
    raw_refs = [*result.provider_refs, result.canonical_url, result.pdf_url]
    for ref in raw_refs:
        clean = _clean_text(ref).lower()
        label = ""
        if "arxiv" in clean:
            label = "arXiv"
        elif "openreview" in clean:
            label = "OpenReview"
        elif "openalex" in clean:
            label = "OpenAlex"
        elif "semantic" in clean or "s2orc" in clean:
            label = "Semantic Scholar"
        elif "doi.org" in clean or result.doi:
            label = "DOI"
        elif clean.startswith("http"):
            parsed = urllib.parse.urlparse(clean)
            label = parsed.netloc.removeprefix("www.")
        elif clean:
            label = clean.split(":", 1)[0].replace("_", " ").title()
        if label and label not in labels:
            labels.append(label)
    return ", ".join(labels[:2])


def _paper_search_selection_reason(result: PaperSearchResult, query: str) -> str:
    query_text = _clean_text(query)
    lowered_query = query_text.lower()
    haystack = " ".join(
        [
            result.title,
            result.abstract,
            " ".join(result.tags),
            " ".join(result.fields_of_study),
            " ".join(result.provider_refs),
        ]
    ).lower()
    title = result.title.lower()
    matches: list[str] = []

    def add_match(label: str) -> None:
        if label and label not in matches:
            matches.append(label)

    if "vla" in lowered_query or "vision-language-action" in lowered_query or "vision language action" in lowered_query:
        if any(marker in haystack for marker in ("vla", "vision-language-action", "vision language action")):
            add_match("VLA/Vision-Language-Action")
    if "memory" in lowered_query or "mem" in lowered_query:
        if "memory" in haystack or re.search(r"\bmem[a-z0-9-]*\b", title):
            add_match("memory")
    if any(marker in lowered_query for marker in ("robot", "manipulation", "vla")):
        if any(marker in haystack for marker in ("robot", "robotic", "manipulation", "embodied")):
            add_match("robotics/manipulation")
    for term in _paper_search_normalized_terms(query_text):
        if term in {"vla", "memory", "mem"}:
            continue
        if term in title:
            add_match(f"{term} in the title")
        elif term in haystack:
            add_match(term)
        if len(matches) >= 4:
            break

    details: list[str] = []
    if matches:
        details.append("the title/abstract matches " + ", ".join(matches[:4]))
    elif query_text:
        details.append(f"it matches the search intent for '{query_text}'")
    else:
        details.append("it has importable paper metadata")
    if result.year:
        details.append(f"it is marked as a {result.year} paper")
    provider_label = _paper_search_provider_label(result)
    if result.pdf_url or _url_looks_like_pdf(result.canonical_url):
        pdf_detail = "a direct PDF is available"
        if provider_label:
            pdf_detail += f" via {provider_label}"
        details.append(pdf_detail)
    elif provider_label:
        details.append(f"the source is {provider_label}")
    return "Selected for this query because " + "; ".join(details) + "."


def _paper_link_source_label(url: str, fallback: str = "") -> str:
    parsed = urllib.parse.urlparse(_clean_text(url))
    host = parsed.netloc.lower().removeprefix("www.")
    if not host:
        return fallback
    labels = {
        "arxiv.org": "arXiv",
        "doi.org": "DOI",
        "openreview.net": "OpenReview",
        "github.com": "GitHub",
        "zhihu.com": "Zhihu",
        "xiaohongshu.com": "Xiaohongshu",
        "bilibili.com": "Bilibili",
        "youtube.com": "YouTube",
        "youtu.be": "YouTube",
    }
    for marker, label in labels.items():
        if host == marker or host.endswith(f".{marker}"):
            return label
    return fallback or host


def _paper_search_explanation_links_for_result(result: PaperSearchResult) -> list[dict[str, str]]:
    links = _paper_explanation_links(result.explanation_links)
    seen = {_canonical_url(_clean_text(row.get("url"))) for row in links}

    def add(url: str, title: str, source: str = "", summary: str = "") -> None:
        clean_url = _clean_text(url)
        key = _canonical_url(clean_url)
        if not clean_url or key in seen:
            return
        seen.add(key)
        row = {"url": clean_url, "title": title or clean_url}
        if source:
            row["source"] = source
        if summary:
            row["summary"] = summary
        links.append(row)

    canonical_url = _clean_text(result.canonical_url)
    pdf_url = _clean_text(result.pdf_url)
    if canonical_url and not _url_looks_like_pdf(canonical_url):
        source = _paper_link_source_label(canonical_url, "Paper page")
        title = "arXiv abstract" if source == "arXiv" else "Paper page"
        add(canonical_url, title, source, "Source page with abstract, metadata, and related references.")
    if result.doi:
        add(f"https://doi.org/{result.doi}", "Publisher / DOI page", "DOI", "Publisher landing page resolved from the DOI.")
    if pdf_url and not links:
        source = _paper_link_source_label(pdf_url, "PDF")
        add(pdf_url, "Direct PDF", source, "Direct PDF for reading when no separate explainer page is available.")
    return links[:6]


def _enrich_paper_search_results(rows: list[PaperSearchResult], query: str) -> list[PaperSearchResult]:
    for row in rows:
        if _paper_search_reason_is_generic(row.why_relevant):
            row.why_relevant = _paper_search_selection_reason(row, query)
        row.explanation_links = _paper_search_explanation_links_for_result(row)
        row.candidate_id = row.candidate_id or row.fingerprint()[:16]
    return rows


def _dedupe_paper_search_results(rows: list[PaperSearchResult]) -> list[PaperSearchResult]:
    out: list[PaperSearchResult] = []
    seen: set[str] = set()
    for row in rows:
        keys = [
            row.doi.lower(),
            row.arxiv_id.lower(),
            row.semantic_scholar_id.lower(),
            _canonical_url(row.canonical_url),
            _canonical_url(row.pdf_url),
            row.fingerprint(),
        ]
        key = next((item for item in keys if item), row.fingerprint())
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _filter_paper_search_results(
    rows: list[PaperSearchResult],
    filters: dict | None,
    *,
    debug: dict[str, Any] | None = None,
) -> list[PaperSearchResult]:
    filtered: list[PaperSearchResult] = []
    dropped_no_pdf = 0
    dropped_year = 0
    for row in rows:
        if bool((filters or {}).get("has_open_access_pdf")) and not _paper_search_result_has_downloadable_pdf(row):
            dropped_no_pdf += 1
            continue
        if not _paper_search_result_matches_year(row, filters):
            dropped_year += 1
            continue
        filtered.append(row)
    target = _search_debug(debug)
    if target is not None:
        dropped = target.setdefault("dropped", {})
        dropped["no_pdf"] = int(dropped.get("no_pdf") or 0) + dropped_no_pdf
        dropped["year"] = int(dropped.get("year") or 0) + dropped_year
    return filtered


def _squash_html_text(value: object) -> str:
    clean = unescape(_clean_text(value))
    clean = re.sub(r"\s+", " ", clean)
    clean = re.sub(r"\s+-\s+", "-", clean)
    clean = re.sub(r"\s+([:;,.)\]])", r"\1", clean)
    clean = re.sub(r"([(])\s+", r"\1", clean)
    clean = clean.replace(" Abstract :", "").replace("Abstract :", "")
    clean = clean.replace("\u25bd More", "").replace("\u25b3 Less", "")
    return clean.strip()


def _absolute_arxiv_url(url: str) -> str:
    return urllib.parse.urljoin("https://arxiv.org", _clean_text(url))


def _arxiv_id_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(_clean_text(url))
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] in {"abs", "pdf"}:
        return parts[1].removesuffix(".pdf")
    return ""


class _ArxivSearchHTMLParser(HTMLParser):
    """Small structured parser for arXiv search result pages."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: list[dict[str, object]] = []
        self._current: dict[str, object] | None = None
        self._capture_stack: list[tuple[str, str]] = []
        self._author_parts: list[str] = []
        self._tag_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        classes = set(_clean_text(attrs_dict.get("class")).split())
        if tag == "li" and "arxiv-result" in classes:
            self._current = {
                "title_parts": [],
                "abstract_parts": [],
                "authors": [],
                "tags": [],
                "submitted_parts": [],
                "canonical_url": "",
                "pdf_url": "",
                "arxiv_id": "",
            }
            self._capture_stack = []
            return
        if self._current is None:
            return
        href = _absolute_arxiv_url(attrs_dict.get("href", "")) if tag == "a" else ""
        arxiv_id = _arxiv_id_from_url(href)
        if arxiv_id:
            if "/abs/" in urllib.parse.urlparse(href).path and not self._current.get("canonical_url"):
                self._current["canonical_url"] = href
                self._current["arxiv_id"] = arxiv_id
            if "/pdf/" in urllib.parse.urlparse(href).path:
                self._current["pdf_url"] = href
                self._current["arxiv_id"] = self._current.get("arxiv_id") or arxiv_id
        if tag == "p" and "title" in classes:
            self._capture_stack.append(("title", tag))
            return
        if tag == "p" and "authors" in classes:
            self._capture_stack.append(("authors_block", tag))
            return
        if tag == "a" and self._capture_active("authors_block"):
            self._author_parts = []
            self._capture_stack.append(("author", tag))
            return
        if tag == "span" and "tag" in classes:
            self._tag_parts = []
            self._capture_stack.append(("tag", tag))
            return
        if tag == "span" and "abstract-full" in classes:
            self._capture_stack.append(("abstract", tag))
            return
        if tag == "p" and "is-size-7" in classes and "comments" not in classes:
            self._capture_stack.append(("submitted", tag))

    def handle_endtag(self, tag: str) -> None:
        if tag == "li" and self._current is not None:
            self._finish_current()
            self._current = None
            self._capture_stack = []
            return
        if self._current is None or not self._capture_stack:
            return
        name, capture_tag = self._capture_stack[-1]
        if capture_tag != tag:
            return
        self._capture_stack.pop()
        if name == "author":
            author = _squash_html_text(" ".join(self._author_parts))
            authors = self._current.setdefault("authors", [])
            if author and isinstance(authors, list) and author not in authors:
                authors.append(author)
            self._author_parts = []
        elif name == "tag":
            tag_text = _squash_html_text(" ".join(self._tag_parts))
            tags = self._current.setdefault("tags", [])
            if tag_text and isinstance(tags, list) and tag_text not in tags:
                tags.append(tag_text)
            self._tag_parts = []

    def handle_data(self, data: str) -> None:
        if self._current is None:
            return
        if self._capture_active("title"):
            self._current.setdefault("title_parts", []).append(data)
        if self._capture_active("abstract"):
            self._current.setdefault("abstract_parts", []).append(data)
        if self._capture_active("submitted"):
            self._current.setdefault("submitted_parts", []).append(data)
        if self._capture_active("author"):
            self._author_parts.append(data)
        if self._capture_active("tag"):
            self._tag_parts.append(data)

    def _capture_active(self, name: str) -> bool:
        return any(item[0] == name for item in self._capture_stack)

    def _finish_current(self) -> None:
        if self._current is None:
            return
        title = _squash_html_text(" ".join(self._current.get("title_parts") or []))
        canonical_url = _clean_text(self._current.get("canonical_url"))
        pdf_url = _clean_text(self._current.get("pdf_url"))
        arxiv_id = _clean_text(self._current.get("arxiv_id")) or _arxiv_id_from_url(canonical_url)
        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        if not title or not arxiv_id:
            return
        submitted = _squash_html_text(" ".join(self._current.get("submitted_parts") or []))
        self.results.append(
            {
                "title": title,
                "canonical_url": canonical_url or f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": pdf_url,
                "arxiv_id": arxiv_id,
                "authors": list(self._current.get("authors") or []),
                "abstract": _squash_html_text(" ".join(self._current.get("abstract_parts") or [])),
                "year": _published_year(submitted),
                "tags": list(self._current.get("tags") or []),
                "submitted": submitted,
            }
        )


def _parse_arxiv_search_html(payload: str, *, source_query: str = "") -> list[PaperSearchResult]:
    parser = _ArxivSearchHTMLParser()
    parser.feed(payload or "")
    rows: list[PaperSearchResult] = []
    for item in parser.results:
        arxiv_id = _clean_text(item.get("arxiv_id"))
        tags = _clean_list(item.get("tags"))
        submitted = _clean_text(item.get("submitted"))
        year = _published_year(submitted)
        v1_match = re.search(r"\bv1\b[^.;]*(19|20)\d{2}", submitted, flags=re.IGNORECASE)
        if v1_match:
            year = re.search(r"(19|20)\d{2}", v1_match.group(0)).group(0)  # type: ignore[union-attr]
        rows.append(
            PaperSearchResult(
                title=_clean_text(item.get("title")),
                authors=_clean_list(item.get("authors")),
                year=year or _clean_text(item.get("year")),
                venue="arXiv",
                abstract=_clean_text(item.get("abstract")),
                arxiv_id=arxiv_id,
                canonical_url=_clean_text(item.get("canonical_url")) or f"https://arxiv.org/abs/{arxiv_id}",
                pdf_url=_clean_text(item.get("pdf_url")) or f"https://arxiv.org/pdf/{arxiv_id}",
                open_access_pdf=True,
                provider_refs=["arxiv", "arxiv_html"],
                why_relevant=f"Matched arXiv web search query: {source_query}",
                tags=[*tags, "arxiv"],
                fields_of_study=tags,
            )
        )
    return rows


def _fetch_arxiv_search_html(query: str, *, timeout: float = 8.0, max_bytes: int = 180_000) -> str:
    encoded = urllib.parse.urlencode(
        {
            "query": query,
            "searchtype": "all",
            "source": "header",
        }
    )
    url = f"https://arxiv.org/search/?{encoded}"
    curl = shutil.which("curl")
    if curl:
        timeout = max(1.0, float(timeout))
        try:
            completed = subprocess.run(
                [
                    curl,
                    "-sS",
                    "-L",
                    "--max-time",
                    f"{timeout:.2f}",
                    "--connect-timeout",
                    f"{min(timeout, 4.0):.2f}",
                    "--user-agent",
                    "nblane-paper-library/1.0",
                    url,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 1.0,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"arXiv web search exceeded {timeout:.1f}s") from exc
        if completed.stdout:
            return completed.stdout[:max_bytes].decode("utf-8", errors="replace")
        if completed.returncode:
            raise RuntimeError(completed.stderr.decode("utf-8", errors="replace").strip())
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "nblane-paper-library/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(max_bytes).decode("utf-8", errors="replace")


def _search_arxiv_html(
    query_variants: list[str],
    limit: int,
    filters: dict | None,
    *,
    debug: dict[str, Any] | None = None,
) -> list[PaperSearchResult]:
    rows: list[PaperSearchResult] = []
    timeout = _positive_float((filters or {}).get("web_timeout_seconds"))
    timeout = timeout or _positive_float((filters or {}).get("provider_timeout_seconds")) or 8.0
    for variant in query_variants[:3]:
        timeout_left = _paper_search_time_left(filters, timeout)
        if timeout_left <= 0:
            _append_search_warning(debug, "arxiv_html stopped because the provider search budget was exhausted.")
            break
        started = time.monotonic()
        try:
            payload = _fetch_arxiv_search_html(variant, timeout=timeout_left)
            parsed = _parse_arxiv_search_html(payload, source_query=variant)
        except Exception as exc:
            warning = f"arxiv_html failed for {variant}: {type(exc).__name__}: {exc}"
            _append_search_warning(debug, warning)
            _append_search_step(
                debug,
                {
                    "stage": "arxiv_html",
                    "query": variant,
                    "ok": False,
                    "elapsed_ms": int((time.monotonic() - started) * 1000),
                    "warning": warning,
                },
            )
            continue
        accepted = _filter_paper_search_results(parsed, filters, debug=debug)
        rows.extend(accepted)
        _append_search_step(
            debug,
            {
                "stage": "arxiv_html",
                "query": variant,
                "ok": True,
                "raw_count": len(parsed),
                "accepted_count": len(accepted),
                "elapsed_ms": int((time.monotonic() - started) * 1000),
            },
        )
        if len(_dedupe_paper_search_results(rows)) >= limit:
            break
    return rows


def _preferred_ai_backend_from_filters(filters: dict | None) -> str | None:
    clean = _clean_text(
        (filters or {}).get("preferred_backend")
        or (filters or {}).get("ai_backend")
        or (filters or {}).get("model_backend")
    ).lower()
    if clean in {"codex", "local_codex_readonly"}:
        return "local_codex_readonly"
    if clean in {"model", "llm", "direct_llm"}:
        return "direct_llm"
    return None


def _paper_search_uses_profile_context(filters: dict | None) -> bool:
    filters = filters or {}
    return _clean_bool(
        filters.get("use_profile_context")
        or filters.get("include_profile_context")
        or filters.get("personalize_with_profile")
        or filters.get("profile_context"),
        False,
    )


def _paper_result_from_connector(item: object) -> PaperSearchResult | None:
    title = _clean_text(getattr(item, "title", ""))
    if not title:
        return None
    metadata = getattr(item, "metadata", {}) if isinstance(getattr(item, "metadata", {}), dict) else {}
    provider = _clean_text(getattr(item, "provider", ""))
    external_id = _clean_text(getattr(item, "external_id", ""))
    pdf_url = _clean_text(metadata.get("pdf_url") or metadata.get("open_access_pdf_url"))
    arxiv_id = _clean_text(metadata.get("arxiv_id"))
    if not arxiv_id and provider == "arxiv":
        arxiv_id = external_id.rsplit("/", 1)[-1]
    doi = _clean_text(metadata.get("doi"))
    semantic_id = _clean_text(metadata.get("semantic_scholar_id") or metadata.get("paper_id"))
    try:
        citation_count = int(metadata.get("citation_count")) if metadata.get("citation_count") not in (None, "") else None
    except (TypeError, ValueError):
        citation_count = None
    return PaperSearchResult(
        title=title,
        authors=list(getattr(item, "authors", []) or []),
        year=_published_year(_clean_text(getattr(item, "published", ""))),
        venue=_clean_text(metadata.get("venue")),
        abstract=_clean_text(getattr(item, "summary", "")),
        doi=doi,
        arxiv_id=arxiv_id,
        semantic_scholar_id=semantic_id,
        canonical_url=_clean_text(getattr(item, "url", "")),
        pdf_url=pdf_url,
        open_access_pdf=bool(pdf_url or metadata.get("open_access_pdf")),
        provider_refs=[provider] if provider else [],
        why_relevant="Matched provider search query.",
        link_check={"status": "needs check"},
        tags=list(getattr(item, "tags", []) or []),
        citation_count=citation_count,
        fields_of_study=_clean_list(metadata.get("fields_of_study")),
    )


def search_papers(
    query: str,
    providers: tuple[str, ...] = PAPER_SEARCH_PROVIDERS,
    limit: int = 10,
    filters: dict | None = None,
    debug: dict[str, Any] | None = None,
) -> list[PaperSearchResult]:
    """Search provider APIs and return import candidates without writing files."""

    clean_query = _clean_text(query)
    if not clean_query:
        return []
    from nblane.core.research_connectors import ADAPTERS

    rows: list[PaperSearchResult] = []
    filters = _copy_paper_search_filters(filters)
    budget_seconds = _positive_float(filters.get("provider_budget_seconds"))
    if budget_seconds is not None and "_deadline_monotonic" not in filters:
        filters["_deadline_monotonic"] = time.monotonic() + budget_seconds
    variants = _paper_search_query_variants(clean_query, filters)
    target_debug = _search_debug(debug)
    if target_debug is not None:
        target_debug["query_variants"] = variants
        target_debug["year_from"] = _clean_text(filters.get("year_from"))
        target_debug["year_to"] = _clean_text(filters.get("year_to"))
    provider_order = _clean_list(providers) or list(PAPER_SEARCH_PROVIDERS)
    for provider in provider_order:
        if _paper_search_cancelled(filters, debug):
            _append_search_warning(debug, "Paper search was cancelled.")
            break
        if _paper_search_time_left(filters, 1.0) <= 0:
            _append_search_warning(debug, "Provider search stopped because the request budget was exhausted.")
            break
        clean_provider = _clean_text(provider)
        if clean_provider in {"arxiv_html", "arxiv_web"}:
            rows.extend(_search_arxiv_html(variants, max(1, int(limit or 10)), filters, debug=debug))
            rows = _dedupe_paper_search_results(rows)
            if len(rows) >= max(1, int(limit or 10)):
                break
            continue
        adapter = ADAPTERS.get(clean_provider)
        if adapter is None:
            _append_search_step(
                debug,
                {
                    "stage": "provider",
                    "provider": clean_provider,
                    "ok": False,
                    "warning": "provider adapter is not configured",
                },
            )
            continue
        provider_query = variants[0] if variants else clean_query
        config = {
            "query": provider_query,
            "query_variants": variants,
            "original_query": clean_query,
            "limit": max(1, min(int(limit or 10), 50)),
        }
        config.update(_copy_paper_search_filters(filters))
        provider_timeout = _positive_float(config.get("provider_timeout_seconds"))
        if provider_timeout is not None:
            config["provider_timeout_seconds"] = max(1.0, _paper_search_time_left(filters, provider_timeout))
        started = time.monotonic()
        try:
            items = adapter.discover(config)
        except Exception as exc:
            warning = f"{clean_provider} failed: {type(exc).__name__}: {exc}"
            _append_search_warning(debug, warning)
            _append_search_step(
                debug,
                {
                    "stage": "provider",
                    "provider": clean_provider,
                    "query": provider_query,
                    "ok": False,
                    "elapsed_ms": int((time.monotonic() - started) * 1000),
                    "warning": warning,
                },
            )
            continue
        accepted = 0
        for item in items:
            result = _paper_result_from_connector(item)
            if result is not None and _filter_paper_search_results([result], filters, debug=debug):
                rows.append(result)
                accepted += 1
        _append_search_step(
            debug,
            {
                "stage": "provider",
                "provider": clean_provider,
                "query": provider_query,
                "ok": True,
                "raw_count": len(items),
                "accepted_count": accepted,
                "elapsed_ms": int((time.monotonic() - started) * 1000),
            },
        )
    rows = _dedupe_paper_search_results(rows)
    rows = _filter_paper_search_results(rows, filters, debug=debug)
    rows.sort(key=lambda row: _paper_search_relevance_score(row, clean_query), reverse=True)
    rows = _enrich_paper_search_results(rows, clean_query)
    if target_debug is not None:
        target_debug["provider_order"] = provider_order
        target_debug["raw_candidate_count"] = len(rows)
    return rows[: max(1, int(limit or 10))]


def search_papers_with_codex(
    profile: str,
    query: str,
    *,
    filters: dict | None = None,
    context_refs: dict | list[str] | None = None,
    debug: dict[str, Any] | None = None,
) -> list[PaperSearchResult]:
    """Run Codex-first paper discovery through AI Gateway, falling back to providers."""

    refs = []
    include_profile_context = _paper_search_uses_profile_context(filters)
    if include_profile_context:
        if isinstance(context_refs, list):
            refs = _clean_list(context_refs)
        elif isinstance(context_refs, dict):
            refs = _clean_list(context_refs.get("context_refs"))
    from nblane.core.ai.gateway import run_ai_action

    search_context = _paper_search_context_bundle(
        profile,
        query,
        filters or {},
        context_refs=context_refs,
        include_profile_context=include_profile_context,
    )
    target_debug = _search_debug(debug)
    if target_debug is not None:
        target_debug["query_variants"] = search_context.get("query_variants") or []
        target_debug["profile_context_used"] = include_profile_context
        target_debug["codex_home_policy"] = search_context.get("codex_home_policy") or "default"
    progress_callback = target_debug.get("_progress_callback") if target_debug is not None else None
    if not callable(progress_callback):
        progress_callback = None
    cancel_callback = (filters or {}).get("_cancel_check")
    if not callable(cancel_callback):
        cancel_callback = target_debug.get("_cancel_check") if target_debug is not None else None
    if not callable(cancel_callback):
        cancel_callback = None
    started = time.monotonic()
    result = run_ai_action(
        "research.paper_search_codex",
        search_context,
        profile=_profile_name(profile) if include_profile_context else "",
        runtime_profile=_profile_name(profile),
        context_refs=refs,
        preferred_backend=_preferred_ai_backend_from_filters(filters),
        require_review=True,
        progress_callback=progress_callback,
        cancel_callback=cancel_callback,
    )
    candidates: list[PaperSearchResult] = []
    structured = result.structured if isinstance(result.structured, dict) else {}
    for row in structured.get("results") or structured.get("candidates") or []:
        candidate = PaperSearchResult.from_dict(row)
        if (
            candidate is not None
            and _paper_search_result_has_downloadable_pdf(candidate)
            and _paper_search_result_matches_year(candidate, filters)
        ):
            candidates.append(candidate)
    _append_search_step(
        debug,
        {
            "stage": "ai",
            "backend": getattr(result, "backend", ""),
            "run_id": getattr(result, "run_id", ""),
            "ok": bool(getattr(result, "ok", False)),
            "raw_count": len(structured.get("results") or structured.get("candidates") or []),
            "accepted_count": len(candidates),
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "warnings": _clean_list(getattr(result, "warnings", [])) or _clean_list(structured.get("warnings")),
            "error": _clean_text(getattr(result, "error", "")),
        },
    )
    for warning in _clean_list(getattr(result, "warnings", [])) + _clean_list(structured.get("warnings")):
        _append_search_warning(debug, warning)
    if _paper_search_cancelled(filters, debug) or _clean_text(getattr(result, "error", "")) == "command_cancelled":
        _append_search_warning(debug, "Codex paper search was cancelled before fallback.")
        return []
    if candidates:
        candidates = _dedupe_paper_search_results(candidates)
        candidates.sort(key=lambda row: _paper_search_relevance_score(row, query), reverse=True)
        return _enrich_paper_search_results(candidates, query)
    fallback_filters = _copy_paper_search_filters(filters)
    fallback_filters["has_open_access_pdf"] = True
    rows = search_papers(
        query,
        tuple(fallback_filters.get("providers") or PAPER_SEARCH_PROVIDERS),
        int(fallback_filters.get("limit") or 10),
        fallback_filters,
        debug=debug,
    )
    return _enrich_paper_search_results(rows, query)


def _paper_search_context_bundle(
    profile: str | Path,
    query: str,
    filters: dict[str, Any],
    *,
    context_refs: dict | list[str] | None = None,
    include_profile_context: bool = False,
) -> dict[str, Any]:
    """Build the compact retrieval payload for local read-only Codex search."""

    codex_reasoning_effort = _paper_search_codex_reasoning_effort(filters)
    codex_search_depth = "deep" if codex_reasoning_effort == "xhigh" else _paper_search_codex_depth(filters)
    public_filters = {
        key: copy.deepcopy(value)
        for key, value in filters.items()
        if not str(key).startswith("_") and not callable(value)
    }
    payload: dict[str, Any] = {
        "query": _clean_text(query),
        "filters": public_filters,
        "providers": _clean_list(filters.get("providers")),
        "query_variants": _paper_search_query_variants(query, filters),
        "provider_policy": "any_source_with_downloadable_pdf",
        "required_import_ref": "direct_pdf_url",
        "profile_context_used": bool(include_profile_context),
        "profile_context_policy": (
            "available_for_optional_rerank"
            if include_profile_context
            else "not_sent_for_discovery"
        ),
        "codex_reasoning_effort": codex_reasoning_effort,
        "codex_search_depth": codex_search_depth,
        "codex_home_policy": _paper_search_codex_home_policy(filters),
        "reply_language": _paper_search_reply_language(query, filters),
        "search_strategy": [
            "Prefer Codex/model discovery for fresh web results.",
            "Use the query_variants list to expand acronyms and avoid provider drift.",
            "If VLA means robotics, treat it as Vision-Language-Action unless the payload says otherwise.",
            "For latest/recent requests, check submitted-date sorted sources such as arXiv API when possible.",
            "Return direct arXiv PDF links when arXiv papers match.",
            "Do not use personal profile data as a retrieval constraint.",
            "Stop as soon as enough strong PDF-ready candidates are found.",
        ],
    }
    timeout_seconds = _positive_float(filters.get("codex_timeout_seconds"))
    if timeout_seconds is not None:
        payload["codex_timeout_seconds"] = timeout_seconds
    model_timeout_seconds = _positive_float(filters.get("model_timeout_seconds"))
    if model_timeout_seconds is not None:
        payload["model_timeout_seconds"] = model_timeout_seconds
        payload["llm_timeout_seconds"] = model_timeout_seconds
    if include_profile_context and isinstance(context_refs, dict):
        payload["context_refs"] = _clean_list(context_refs.get("context_refs"))
        payload["project_refs"] = _clean_list(context_refs.get("project_refs"))
        payload["goal_refs"] = _clean_list(context_refs.get("goal_refs"))
    elif include_profile_context and isinstance(context_refs, list):
        payload["context_refs"] = _clean_list(context_refs)
    else:
        payload["context_refs"] = []
    if include_profile_context:
        payload["already_imported"] = _paper_search_imported_refs(profile)
        payload["library_tree_hint"] = _paper_search_library_tree_hint(profile)
    return payload


def _paper_search_codex_reasoning_effort(filters: dict[str, Any]) -> str:
    clean = _clean_text(
        filters.get("codex_reasoning_effort")
        or filters.get("reasoning_effort")
    ).lower()
    if clean in {"low", "medium", "high", "xhigh"}:
        return clean
    if _paper_search_codex_depth(filters) == "deep":
        return "xhigh"
    return "medium"


def _paper_search_codex_depth(filters: dict[str, Any]) -> str:
    clean = _clean_text(
        filters.get("codex_search_depth")
        or filters.get("search_depth")
        or filters.get("codex_depth")
    ).lower()
    if clean in {"deep", "xhigh", "thorough", "careful"}:
        return "deep"
    if _clean_bool(filters.get("codex_deep_search"), False) or _clean_bool(filters.get("deep_search"), False):
        return "deep"
    return "quick"


def _paper_search_codex_home_policy(filters: dict[str, Any]) -> str:
    clean = _clean_text(
        filters.get("codex_home_policy")
        or filters.get("codex_home_mode")
        or os.getenv("NBLANE_CODEX_HOME_POLICY")
        or os.getenv("NBLANE_PAPER_SEARCH_CODEX_HOME_POLICY")
    ).lower()
    if clean in {"profile", "isolated", "profile_isolated", "web_profile"}:
        return "profile"
    if clean in {"default", "global", "terminal", "terminal_default", "shared"}:
        return "default"
    return "default"


def _paper_search_reply_language(query: str, filters: dict[str, Any]) -> str:
    clean = _clean_text(filters.get("reply_language") or filters.get("reply_lang")).lower()
    if clean in {"en", "zh"}:
        return clean
    return "zh" if re.search(r"[\u4e00-\u9fff]", _clean_text(query)) else ""


def _positive_float(value: object) -> float | None:
    try:
        clean = float(value)
    except (TypeError, ValueError):
        return None
    return clean if clean > 0 else None


def _grobid_retry_cooldown_seconds() -> float:
    configured = _positive_float(os.getenv("NBLANE_GROBID_RETRY_COOLDOWN_SECONDS"))
    return configured if configured is not None else float(GROBID_RETRY_COOLDOWN_SECONDS_DEFAULT)


def _metadata_has_recent_grobid_failure(metadata: dict[str, object], pdf_fingerprint: str) -> bool:
    cooldown = _grobid_retry_cooldown_seconds()
    if cooldown <= 0:
        return False
    failure_pdf = _clean_text(metadata.get("grobid_failure_pdf_sha256"))
    if failure_pdf and pdf_fingerprint and failure_pdf != pdf_fingerprint:
        return False
    warnings = " ".join(_clean_list(metadata.get("structured_extraction_warnings"))).casefold()
    last_error = _clean_text(metadata.get("grobid_last_error")).casefold()
    marker = f"{warnings} {last_error}"
    if not any(token in marker for token in ("grobid extraction failed", "grobid unavailable", "timed out")):
        return False
    failed_at = (
        _timestamp_from_iso(metadata.get("grobid_last_failed_at"))
        or _timestamp_from_iso(metadata.get("structured_extracted_at"))
        or _timestamp_from_iso(metadata.get("reading_artifacts_ready_at"))
    )
    if failed_at <= 0:
        return True
    return (time.time() - failed_at) < cooldown


def _paper_search_imported_refs(profile: str | Path) -> list[dict[str, str]]:
    """Return compact duplicate-avoidance refs for already imported papers."""

    rows: list[dict[str, str]] = []
    try:
        sources = load_research_sources(_profile_root(profile)).sources
    except Exception:
        return rows
    for source in sources:
        if source.kind != "paper":
            continue
        metadata = source.metadata or {}
        row = {
            "source_id": _clean_text(source.id),
            "title": _clean_text(source.title)[:160],
            "doi": _clean_text(metadata.get("doi")),
            "arxiv_id": _clean_text(metadata.get("arxiv_id")),
            "semantic_scholar_id": _clean_text(metadata.get("semantic_scholar_id")),
            "url": _canonical_url(source.url),
        }
        compact = {key: value for key, value in row.items() if value}
        if compact:
            rows.append(compact)
        if len(rows) >= 200:
            break
    return rows


def _paper_search_library_tree_hint(profile: str | Path) -> list[dict[str, str]]:
    """Return compact library taxonomy hints for candidate placement."""

    try:
        tree = load_paper_library_tree(profile)
    except Exception:
        return []
    rows: list[dict[str, str]] = []
    for node in tree.nodes[:80]:
        row = {
            "id": _clean_text(node.id),
            "title": _clean_text(node.title)[:120],
            "parent_id": _clean_text(node.parent_id),
            "description": _clean_text(node.description)[:240],
        }
        rows.append({key: value for key, value in row.items() if value})
    return rows


def _paper_search_result_has_downloadable_pdf(result: PaperSearchResult) -> bool:
    """Return True when a search candidate carries a direct PDF download URL."""

    return bool(result.pdf_url or _url_looks_like_pdf(result.canonical_url))


def _paper_search_result_has_import_ref(result: PaperSearchResult) -> bool:
    """Backward-compatible alias for the current PDF-first import policy."""

    return _paper_search_result_has_downloadable_pdf(result)


def check_paper_links(results: list[PaperSearchResult | dict]) -> list[PaperSearchResult]:
    """Check canonical/PDF URLs without importing candidates."""

    checked: list[PaperSearchResult] = []
    for item in results:
        result = item if isinstance(item, PaperSearchResult) else PaperSearchResult.from_dict(item)
        if result is None:
            continue
        url = result.pdf_url or result.canonical_url
        if not url:
            result.link_check = {"status": "missing", "checked_at": _now()}
            checked.append(result)
            continue
        try:
            request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "nblane-paper-reading/1.0"})
            with urllib.request.urlopen(request, timeout=8) as response:
                status = int(getattr(response, "status", 200))
            result.link_check = {"status": "ok" if status < 400 else str(status), "checked_at": _now()}
        except Exception as exc:
            result.link_check = {"status": "needs check", "checked_at": _now(), "error": str(exc)[:160]}
        checked.append(result)
    return checked


def _result_from_url(url: str) -> PaperSearchResult:
    clean = _clean_text(url)
    parsed = urllib.parse.urlparse(clean)
    title = clean
    metadata: dict[str, object] = {}
    pdf_url = clean if parsed.path.lower().endswith(".pdf") else ""
    arxiv_id = ""
    doi = ""
    if "arxiv.org" in parsed.netloc:
        arxiv_id = parsed.path.rsplit("/", 1)[-1].replace(".pdf", "")
        title = f"arXiv {arxiv_id}"
        if not pdf_url:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        metadata["provider_refs"] = ["arxiv"]
    if "doi.org" in parsed.netloc:
        doi = parsed.path.lstrip("/")
        title = f"DOI {doi}"
    return PaperSearchResult(
        title=title,
        doi=doi,
        arxiv_id=arxiv_id,
        canonical_url=clean,
        pdf_url=pdf_url,
        open_access_pdf=bool(pdf_url),
        provider_refs=_clean_list(metadata.get("provider_refs")) or ["manual"],
        why_relevant="Manual URL / DOI import candidate.",
        link_check={"status": "needs check"},
        needs_link_check=True,
    )


def import_paper_url(profile: str | Path, url: str, options: dict) -> str:
    """Create a metadata-only paper source from a DOI/arXiv/PDF URL candidate."""

    result = _result_from_url(url)
    title = _clean_text((options or {}).get("title") or (options or {}).get("title_hint"))
    if title:
        result.title = title
    row = result.to_dict()
    imported = import_paper_search_results(profile, [row], [_clean_text(row.get("candidate_id"))], options)
    if not imported:
        raise ValueError("Paper URL was not imported, likely because it is a duplicate.")
    return imported[0]


def _duplicate_keys_for_source(source: ResearchSource) -> set[str]:
    metadata = source.metadata or {}
    keys = set()
    for key in ("doi", "arxiv_id", "semantic_scholar_id"):
        value = _clean_text(metadata.get(key)).lower()
        if value:
            keys.add(f"{key}:{value}")
    canonical = _canonical_url(source.url).lower()
    if canonical:
        keys.add(f"url:{canonical}")
    title_year = "|".join([source.title.lower(), _published_year(source.published)])
    if source.title:
        keys.add(f"title_year:{title_year}")
    return keys


def _duplicate_keys_for_result(result: PaperSearchResult) -> set[str]:
    keys = set()
    for key, value in (
        ("doi", result.doi),
        ("arxiv_id", result.arxiv_id),
        ("semantic_scholar_id", result.semantic_scholar_id),
    ):
        clean = _clean_text(value).lower()
        if clean:
            keys.add(f"{key}:{clean}")
    canonical = _canonical_url(result.canonical_url).lower()
    if canonical:
        keys.add(f"url:{canonical}")
    keys.add(f"title_year:{result.title.lower()}|{result.year}")
    return keys


def mark_imported_paper_results(
    profile: str | Path,
    results: list[PaperSearchResult | dict],
) -> list[PaperSearchResult]:
    inbox = load_research_sources(_profile_root(profile))
    existing: dict[str, str] = {}
    for source in inbox.sources:
        if source.kind != "paper":
            continue
        for key in _duplicate_keys_for_source(source):
            existing[key] = source.id
    out: list[PaperSearchResult] = []
    for item in results:
        result = item if isinstance(item, PaperSearchResult) else PaperSearchResult.from_dict(item)
        if result is None:
            continue
        for key in _duplicate_keys_for_result(result):
            if key in existing:
                result.imported_source_id = existing[key]
                if "Already imported." not in result.warnings:
                    result.warnings.append("Already imported.")
                break
        out.append(result)
    return out


def import_paper_search_results(
    profile: str | Path,
    results: list[dict],
    selected_ids: list[str],
    options: dict,
) -> list[str]:
    """Import selected search candidates into ``research/sources.yaml``."""

    candidates = [row for row in (PaperSearchResult.from_dict(item) for item in results) if row is not None]
    selected = set(_clean_list(selected_ids))
    if not selected:
        return []
    inbox = load_research_sources(_profile_root(profile))
    existing_keys: dict[str, str] = {}
    for source in inbox.sources:
        if source.kind == "paper":
            for key in _duplicate_keys_for_source(source):
                existing_keys[key] = source.id
    imported: list[str] = []
    visibility = _choice((options or {}).get("visibility"), SOURCE_VISIBILITIES, "private")
    status = _choice((options or {}).get("status"), SOURCE_STATUSES, "inbox")
    base_tags = _clean_list((options or {}).get("tags"))
    node_refs = _clean_list((options or {}).get("library_node_refs") or (options or {}).get("library_node_ref"))
    goal_refs = _clean_list((options or {}).get("goal_refs"))
    project_refs = _clean_list((options or {}).get("project_refs"))
    allow_duplicates = bool((options or {}).get("allow_duplicates"))
    download_pdf = bool((options or {}).get("download_pdf"))
    for result in candidates:
        if result.candidate_id not in selected and result.title not in selected:
            continue
        duplicate = ""
        for key in _duplicate_keys_for_result(result):
            if key in existing_keys:
                duplicate = existing_keys[key]
                break
        if duplicate and not allow_duplicates:
            continue
        source = add_research_source(
            inbox,
            result.title,
            kind="paper",
            url=result.canonical_url,
            status=status,
            authors=result.authors,
            published=result.year,
            tags=[*base_tags, *result.tags],
            goal_refs=goal_refs,
            project_refs=project_refs,
            library_node_refs=node_refs,
            summary=result.abstract,
            visibility=visibility,
            origin="connector" if result.provider_refs else "manual",
            metadata=result.source_metadata(),
        )
        imported.append(source.id)
        for key in _duplicate_keys_for_source(source):
            existing_keys[key] = source.id
    save_research_sources(_profile_root(profile), inbox)
    if download_pdf:
        for source_id in imported:
            source = load_research_sources(_profile_root(profile)).by_id().get(source_id)
            if source is None:
                continue
            pdf_url = _clean_text((source.metadata or {}).get("open_access_pdf_url"))
            if pdf_url:
                ensure_paper_pdf_downloaded(
                    profile,
                    source_id,
                    pdf_url=pdf_url,
                    error_prefix="PDF download failed during import",
                )
    return imported


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
    warnings = _clean_list(metadata.get("structured_extraction_warnings"))
    return any("grobid unavailable" in warning.casefold() for warning in warnings)


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
    grobid_status = grobid_readiness() if include_grobid else None
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


def save_paper_analysis(profile: str | Path, source_id: str, data: dict[str, object]) -> Path:
    _source_by_id(profile, source_id)
    path = _yaml_path(profile, PAPER_ANALYSIS_DIRNAME, source_id)
    payload = {
        "schema_version": "1.0",
        "source_id": source_id,
        "updated": _now(),
        **_clean_mapping(data),
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


__all__ = [
    "LIBRARY_TREE_FILENAME",
    "NO_LLM_TRANSLATION_WARNING",
    "PAPER_ANNOTATIONS_DIRNAME",
    "PAPER_EXPORTS_DIRNAME",
    "PAPER_PAGES_DIRNAME",
    "PAPER_SEGMENTS_DIRNAME",
    "PAPER_STRUCTURE_DIRNAME",
    "PAPER_TRANSLATIONS_DIRNAME",
    "PaperAnnotation",
    "PaperAsset",
    "PaperLibraryNode",
    "PaperLibraryTree",
    "PaperPage",
    "PaperSearchResult",
    "PaperSegment",
    "PaperStructureUnit",
    "PaperTranslation",
    "auto_chunk_paper",
    "build_paper_layout_units",
    "build_paper_structure_units",
    "build_paper_delete_preview",
    "build_reader_payload",
    "build_translation_units",
    "check_paper_links",
    "create_paper_library_node",
    "create_chunk_from_annotation",
    "create_paper_annotation",
    "create_reading_note_markdown",
    "create_reading_note_pack_markdown",
    "delete_paper_pdf_asset",
    "delete_paper_reader_artifacts",
    "delete_paper_record",
    "download_paper_pdf",
    "ensure_paper_pdf_downloaded",
    "ensure_paper_reading_artifacts",
    "extract_paper_figures",
    "extract_paper_page_text_layer",
    "extract_paper_pages",
    "extract_paper_segments",
    "format_research_citations",
    "grobid_available",
    "grobid_readiness",
    "grobid_tei_to_bibliography",
    "grobid_tei_to_segments",
    "get_stable_pdf_url",
    "import_paper_pdf",
    "import_paper_search_results",
    "import_paper_url",
    "load_paper_analysis",
    "load_paper_annotations",
    "load_paper_library_tree",
    "load_paper_pages",
    "load_paper_pdf_bytes",
    "load_paper_segments",
    "load_paper_structure_units",
    "load_paper_translations",
    "mark_imported_paper_results",
    "migrate_legacy_translations_to_segments",
    "move_papers_to_node",
    "normalize_translation_row",
    "paper_citation_diagnostics",
    "paper_diagnostics",
    "paper_library_path",
    "paper_library_paths",
    "paper_overview",
    "paper_pdf_asset_path",
    "paper_rows",
    "paper_source_badges",
    "paper_source_diagnostics",
    "position_paper_library_node",
    "process_grobid_fulltext",
    "purge_paper_library_node",
    "purge_discarded_papers",
    "pymupdf_available",
    "reader_translation_layout_units",
    "reader_translation_structure_units",
    "remove_papers_from_node",
    "rename_paper_library_node",
    "reorder_paper_library_node",
    "research_asset_root",
    "render_paper_page_preview",
    "restore_paper_library_node",
    "save_paper_analysis",
    "save_paper_annotations",
    "save_paper_library_tree",
    "save_paper_note",
    "save_paper_pages",
    "save_paper_segments",
    "save_paper_structure_units",
    "save_paper_translations",
    "save_research_export",
    "search_papers",
    "search_papers_with_codex",
    "set_paper_primary_node",
    "text_hash",
    "trash_paper_library_node",
    "translate_full_paper",
    "translation_text_from_row",
    "translation_rows_for_segments",
    "upsert_paper_library_node",
    "upsert_paper_translations",
    "validate_paper_library",
]
