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
import hashlib
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
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
PAPER_ANNOTATIONS_DIRNAME = "annotations"
PAPER_TRANSLATIONS_DIRNAME = "translations"
PAPER_ANALYSIS_DIRNAME = "analysis"
PAPER_NOTES_DIRNAME = "notes"
PAPER_EXPORTS_DIRNAME = "exports"

PAPER_ANNOTATION_KINDS = ("highlight", "note", "question")
PAPER_ANNOTATION_STATUSES = ("active", "deleted")
PAPER_TRANSLATION_STATUSES = ("translated", "missing", "stale", "failed")
PAPER_SEARCH_PROVIDERS = ("arxiv", "semantic_scholar")
PDF_MAX_BYTES_DEFAULT = 75 * 1024 * 1024
PAPER_DIAGNOSTIC_BADGES = {
    "grobid_unavailable": "GROBID unavailable",
    "needs_structured_extraction": "Needs structured extraction",
    "stale_translation": "Stale translation",
    "citation_broken": "Citation broken",
    "private_source": "Private source",
    "duplicate_risk": "Duplicate risk",
}
PAPER_DIAGNOSTIC_SEVERITIES = {
    "grobid_unavailable": "warning",
    "needs_structured_extraction": "warning",
    "stale_translation": "warning",
    "citation_broken": "error",
    "private_source": "info",
    "duplicate_risk": "warning",
}


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
    out: dict[str, object] = {}
    for key, item in value.items():
        clean = _clean_text(key)
        if clean:
            out[clean] = copy.deepcopy(item)
    return out


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
    with urllib.request.urlopen(request, timeout=30) as response:
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(1024 * 128)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("Downloaded PDF exceeds NBLANE_RESEARCH_PDF_MAX_BYTES.")
            chunks.append(chunk)
    filename = Path(parsed.path).name or f"{source_slug(source_id)}.pdf"
    return import_paper_pdf(profile, source_id, b"".join(chunks), filename, pdf_url=clean_url)


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
                    },
                )
                return segments
            warnings.append("GROBID returned no usable segments; used page-text fallback.")
        except Exception as exc:
            warnings.append(f"GROBID extraction failed: {exc}")
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


def ensure_paper_reading_artifacts(
    profile: str | Path,
    source_id: str,
    *,
    prefer_grobid: bool = True,
) -> dict[str, object]:
    """Ensure page text and reading segments exist for the PDF reader.

    The helper is intentionally idempotent: when pages, segments, and ready
    metadata already match the current PDF fingerprint, it returns without
    touching profile files. GROBID is treated as an enhancement; if it is not
    configured or fails, the reader keeps working through page-text fallback.
    """

    _, source = _source_by_id(profile, source_id)
    source_metadata = dict(source.metadata or {})
    pdf_fingerprint = _paper_pdf_fingerprint(source)
    if not _paper_has_pdf(source):
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
    needs_pages = not pages or pdf_changed
    needs_segments = not segments or pdf_changed
    warnings: list[str] = []

    if needs_pages:
        try:
            pages = extract_paper_pages(profile, source_id, backend="auto")
        except Exception as exc:
            warnings.append(f"Page extraction failed: {exc}")

    _, source = _source_by_id(profile, source_id)
    source_metadata = dict(source.metadata or {})
    if needs_segments:
        configured_grobid = bool(_clean_text(os.getenv("NBLANE_GROBID_URL")))
        segment_backend = "grobid" if prefer_grobid and configured_grobid else "fallback"
        try:
            segments = extract_paper_segments(profile, source_id, backend=segment_backend)
        except Exception as exc:
            warnings.append(f"Structured extraction failed: {exc}")
            if not segments:
                try:
                    segments = extract_paper_segments(profile, source_id, backend="fallback")
                except Exception as fallback_exc:
                    warnings.append(f"Page-text fallback failed: {fallback_exc}")

    _, source = _source_by_id(profile, source_id)
    metadata = dict(source.metadata or {})
    structure_backend = _clean_text(metadata.get("structure_backend"))
    structured_warnings = _clean_list(metadata.get("structured_extraction_warnings"))
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

    return {
        "source_id": source_id,
        "ready": bool(pages) or bool(segments),
        "status": status,
        "pages": len(pages),
        "segments": len(segments),
        "structure_backend": structure_backend,
        "warnings": warnings + structured_warnings,
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


def process_grobid_fulltext(profile: str | Path, source_id: str) -> GrobidDocument:
    """Call GROBID ``processFulltextDocument`` for one paper PDF."""

    base = _clean_text(os.getenv("NBLANE_GROBID_URL")) or "http://127.0.0.1:8070"
    pdf_bytes = load_paper_pdf_bytes(profile, source_id)
    boundary = "----nblane-paper-boundary"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="input"; filename="paper.pdf"\r\n'
        "Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8") + pdf_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    request = urllib.request.Request(
        base.rstrip("/") + "/api/processFulltextDocument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        tei = response.read().decode("utf-8", errors="replace")
    return GrobidDocument(source_id=source_id, tei_xml=tei, generated_at=_now())


def _tei_text(node: ET.Element) -> str:
    return " ".join(" ".join(node.itertext()).split())


def grobid_tei_to_segments(source_id: str, tei_xml: str) -> list[PaperSegment]:
    """Convert a small useful subset of GROBID TEI to paper segments."""

    if not _clean_text(tei_xml):
        return []
    root = ET.fromstring(tei_xml)
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    body = root.find(".//tei:text/tei:body", ns)
    if body is None:
        body = root.find(".//text/body")
    if body is None:
        return []
    segments: list[PaperSegment] = []
    order = 0
    slug = source_slug(source_id)
    for div in body.findall(".//tei:div", ns) + body.findall(".//div"):
        section_path = []
        head = div.find("tei:head", ns)
        if head is None:
            head = div.find("head")
        if head is not None:
            title = _tei_text(head)
            if title:
                section_path.append(title)
        paragraphs = div.findall("tei:p", ns) + div.findall("p")
        for paragraph in paragraphs:
            text = _tei_text(paragraph)
            if not text:
                continue
            order += 1
            try:
                page = int(paragraph.attrib.get("n") or div.attrib.get("n") or 0)
            except ValueError:
                page = 0
            locator = f"p. {page}" if page else ""
            if section_path:
                locator = (locator + " " if locator else "") + "§ " + " / ".join(section_path)
            segments.append(
                PaperSegment(
                    segment_id=f"seg:{slug}:{order:05d}",
                    source_id=source_id,
                    page=page,
                    order=order,
                    section_path=section_path,
                    kind="paragraph",
                    text=text,
                    locator=locator or f"§ {order}",
                )
            )
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
    source_hash: str = ""
    source_text: str = ""
    target_lang: str = "zh"
    translated_text: str = ""
    glossary: dict[str, object] = field(default_factory=dict)
    generated_by: str = ""
    status: str = "translated"
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
        return cls(
            id=tr_id,
            source_id=source_id,
            scope_type=_clean_text(data.get("scope_type")) or "segment",
            scope_ref=_clean_text(data.get("scope_ref")),
            segment_id=_clean_text(data.get("segment_id")),
            page=page,
            source_hash=_clean_text(data.get("source_hash")),
            source_text=_clean_text(data.get("source_text")),
            target_lang=_clean_text(data.get("target_lang")) or "zh",
            translated_text=_clean_text(data.get("translated_text")),
            glossary=_clean_mapping(data.get("glossary")),
            generated_by=_clean_text(data.get("generated_by")),
            status=_choice(data.get("status"), PAPER_TRANSLATION_STATUSES, "translated"),
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
            "source_hash": self.source_hash,
            "source_text": self.source_text,
            "target_lang": self.target_lang or "zh",
            "translated_text": self.translated_text,
            "glossary": copy.deepcopy(self.glossary),
            "generated_by": self.generated_by,
            "status": self.status or "translated",
            "warnings": list(self.warnings),
            "created": self.created or _now(),
        }
        return data


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
    raw = dict(data)
    raw["id"] = _clean_text(raw.get("id")) or fallback_id or "pending"
    raw["source_id"] = _clean_text(raw.get("source_id")) or source_id
    raw["source_hash"] = (
        _clean_text(raw.get("source_hash"))
        or _clean_text(raw.get("text_hash"))
        or _clean_text(raw.get("source_text_hash"))
    )
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


def _reader_state_from_metadata(metadata: dict[str, object], *, page: int, target_lang: str) -> dict[str, object]:
    return {
        "reader_mode": _clean_text(metadata.get("reader_mode")) or "pdf",
        "scale_mode": _clean_text(metadata.get("scale_mode")) or "fit-width",
        "active_tab": _clean_text(metadata.get("active_tab")) or "translation",
        "target_lang": _clean_text(metadata.get("target_lang")) or target_lang or "zh",
        "side_panel_collapsed": bool(metadata.get("side_panel_collapsed", True)),
        "focused_annotation_id": _clean_text(metadata.get("focused_annotation_id")),
        "focused_chunk_id": _clean_text(metadata.get("focused_chunk_id")),
        "last_visible_pages": [
            int(item)
            for item in metadata.get("last_visible_pages", [])
            if str(item).strip().isdigit()
        ] if isinstance(metadata.get("last_visible_pages"), list) else [],
        "last_read_page": max(1, int(metadata.get("last_read_page") or page or 1)),
        "last_read_at": _clean_text(metadata.get("last_read_at")),
    }


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
    segments = [
        segment.to_dict()
        for segment in load_paper_segments(profile, source_id)
        if segment.page in context_page_set
    ]
    segment_ids = {str(row.get("segment_id") or "") for row in segments}
    segment_pages = {str(row.get("segment_id") or ""): int(row.get("page") or 0) for row in segments}
    translations = [
        {
            **row.to_dict(),
            "page": int(row.page or segment_pages.get(row.segment_id, 0)),
        }
        for row in load_paper_translations(profile, source_id)
        if row.target_lang == target_lang
        and (
            row.page in context_page_set
            or (row.segment_id and row.segment_id in segment_ids)
            or (
                row.scope_type == "page"
                and any(str(row.scope_ref).startswith(f"page:{page_number}:") for page_number in context_pages)
            )
        )
    ]
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
    pdf_url = (
        _clean_text(pdf_url_override)
        if pdf_url_override is not None
        else get_stable_pdf_url(profile, source_id) if _clean_text(metadata.get("pdf_asset_ref")) else ""
    )
    return {
        "source": source.to_dict(),
        "pdf_url": pdf_url,
        "page_previews": preview_rows,
        "pages": [page_row.to_dict() for page_row in all_pages if page_row.page in context_page_set],
        "segments": segments,
        "translations": translations,
        "annotations": annotations,
        "chunks": chunks,
        "analysis": load_paper_analysis(profile, source_id),
        "reader_state": _reader_state_from_metadata(metadata, page=page, target_lang=target_lang),
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


def translate_full_paper(
    profile: str | Path,
    source_id: str,
    target_lang: str = "zh",
    mode: str = "missing_or_stale",
    batch_size: int = 20,
    *,
    ai_profile: str | None = None,
    require_review: bool = True,
) -> dict[str, object]:
    """Translate a paper at segment granularity and persist valid rows.

    Existing translations whose ``source_hash`` still matches the current
    segment are skipped in the default mode. Incoming AI rows without a known
    segment id, with a mismatched hash, or with blank translated text are kept
    from overwriting valid translations and surfaced as warnings.
    """

    clean_lang = _clean_text(target_lang) or "zh"
    clean_mode = _clean_text(mode).lower() or "missing_or_stale"
    if clean_mode not in {"all", "missing", "stale", "missing_or_stale"}:
        raise ValueError(f"Unknown full-paper translation mode: {mode}")
    try:
        clean_batch_size = max(1, min(50, int(batch_size or 20)))
    except (TypeError, ValueError):
        clean_batch_size = 20

    segments = load_paper_segments(profile, source_id)
    if not segments:
        ensure_paper_reading_artifacts(profile, source_id, prefer_grobid=True)
        segments = load_paper_segments(profile, source_id)
    translations = load_paper_translations(profile, source_id)
    existing_by_segment = {
        row.segment_id: row
        for row in translations
        if row.segment_id and row.target_lang == clean_lang
    }
    selected_segments: list[PaperSegment] = []
    for segment in segments:
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
    segment_map = {segment.segment_id: segment for segment in selected_segments}
    batches = [
        selected_segments[index : index + clean_batch_size]
        for index in range(0, len(selected_segments), clean_batch_size)
    ]
    if batches:
        from nblane.core.ai.gateway import translate_paper_segments

        for batch in batches:
            try:
                result = translate_paper_segments(
                    ai_profile if ai_profile is not None else _profile_name(profile),
                    source_id,
                    [segment.to_dict() for segment in batch],
                    target_lang=clean_lang,
                    require_review=require_review,
                )
            except Exception as exc:
                warnings.append(f"Translation batch failed: {exc}")
                continue
            warnings.extend(str(warning) for warning in result.warnings)
            if result.error:
                warnings.append(result.error)
            structured = result.structured if isinstance(result.structured, dict) else {}
            for raw in structured.get("translations") or []:
                if not isinstance(raw, dict):
                    continue
                segment_id = _clean_text(raw.get("segment_id") or raw.get("scope_ref"))
                if not segment_id or segment_id not in segment_map:
                    warnings.append("Skipped translation row without a known segment_id.")
                    continue
                segment = segment_map[segment_id]
                source_hash = _clean_text(
                    raw.get("source_hash")
                    or raw.get("text_hash")
                    or raw.get("source_text_hash")
                )
                if source_hash != segment.text_hash:
                    warnings.append(f"Skipped translation for {segment_id}: source_hash mismatch.")
                    continue
                translated_text = _clean_text(raw.get("translated_text"))
                if not translated_text:
                    warnings.append(f"Skipped translation for {segment_id}: translated_text is blank.")
                    existing = existing_by_segment.get(segment_id)
                    if not _translation_is_current(existing, segment, clean_lang):
                        accepted_rows.append(
                            {
                                **copy.deepcopy(raw),
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
                                "warnings": _clean_list(raw.get("warnings"))
                                + ["translated_text is blank."],
                            }
                        )
                    continue
                accepted_rows.append(
                    {
                        **copy.deepcopy(raw),
                        "source_id": source_id,
                        "scope_type": "segment",
                        "scope_ref": segment.segment_id,
                        "segment_id": segment.segment_id,
                        "page": segment.page,
                        "source_hash": segment.text_hash,
                        "source_text": segment.text,
                        "target_lang": clean_lang,
                        "translated_text": translated_text,
                        "status": _choice(raw.get("status"), PAPER_TRANSLATION_STATUSES, "translated"),
                    }
                )

    if accepted_rows:
        upsert_paper_translations(profile, source_id, accepted_rows)
    final_translations = load_paper_translations(profile, source_id)
    counts = _translation_status_counts(segments, final_translations, target_lang=clean_lang)
    return {
        "source_id": source_id,
        "target_lang": clean_lang,
        "mode": clean_mode,
        "segments_total": len(segments),
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


def upsert_paper_library_node(
    profile: str | Path,
    title: str,
    *,
    node_id: str = "",
    parent_id: str = "",
    description: str = "",
    color: str = "",
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
    if _clean_text(parent_id) == clean_id:
        raise ValueError("Paper library node cannot be its own parent.")
    nodes = tree.by_id()
    if parent_id and parent_id not in nodes:
        raise ValueError(f"Unknown parent paper library node: {parent_id}")
    node = PaperLibraryNode(
        id=clean_id,
        title=clean_title,
        parent_id=_clean_text(parent_id),
        description=_clean_text(description),
        color=_clean_text(color),
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
    if clean_node and clean_node not in tree.by_id():
        raise ValueError(f"Unknown paper library node: {clean_node}")
    inbox = load_research_sources(_profile_root(profile))
    changed: list[str] = []
    wanted = set(_clean_list(source_ids))
    for source in inbox.sources:
        if source.id not in wanted:
            continue
        refs = list(source.library_node_refs) if append else []
        if clean_node and clean_node not in refs:
            refs.append(clean_node)
        source.library_node_refs = refs
        changed.append(source.id)
    save_research_sources(_profile_root(profile), inbox)
    return changed


def validate_paper_library(profile: str | Path) -> list[str]:
    diagnostics: list[str] = []
    tree = load_paper_library_tree(profile)
    nodes = tree.by_id()
    for node in tree.nodes:
        if node.parent_id and node.parent_id not in nodes:
            diagnostics.append(f"{node.id}: unknown parent node {node.parent_id}")
    for source in load_research_sources(_profile_root(profile)).sources:
        if source.kind != "paper":
            continue
        for ref in source.library_node_refs:
            if ref not in nodes:
                diagnostics.append(f"{source.id}: unknown library node ref {ref}")
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
            canonical_url=_clean_text(data.get("canonical_url") or data.get("url")),
            pdf_url=_clean_text(data.get("pdf_url") or data.get("open_access_pdf_url")),
            open_access_pdf=bool(data.get("open_access_pdf") or data.get("pdf_url") or data.get("open_access_pdf_url")),
            provider_refs=_clean_list(data.get("provider_refs") or data.get("providers")),
            why_relevant=_clean_text(data.get("why_relevant") or data.get("reason")),
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
        }
        return {key: value for key, value in data.items() if value not in ("", [], None)}


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
    providers: tuple[str, ...] = ("arxiv", "semantic_scholar"),
    limit: int = 10,
    filters: dict | None = None,
) -> list[PaperSearchResult]:
    """Search provider APIs and return import candidates without writing files."""

    clean_query = _clean_text(query)
    if not clean_query:
        return []
    from nblane.core.research_connectors import ADAPTERS

    rows: list[PaperSearchResult] = []
    for provider in providers:
        clean_provider = _clean_text(provider)
        if clean_provider not in PAPER_SEARCH_PROVIDERS:
            continue
        adapter = ADAPTERS.get(clean_provider)
        if adapter is None:
            continue
        config = {"query": clean_query, "limit": max(1, min(int(limit or 10), 50))}
        if filters:
            config.update(copy.deepcopy(filters))
        try:
            items = adapter.discover(config)
        except Exception:
            continue
        for item in items:
            result = _paper_result_from_connector(item)
            if result is not None:
                rows.append(result)
    return rows[: max(1, int(limit or 10))]


def search_papers_with_codex(
    profile: str,
    query: str,
    *,
    filters: dict | None = None,
    context_refs: dict | list[str] | None = None,
) -> list[PaperSearchResult]:
    """Run Codex-first paper discovery through AI Gateway, falling back to providers."""

    refs = []
    if isinstance(context_refs, list):
        refs = _clean_list(context_refs)
    elif isinstance(context_refs, dict):
        refs = _clean_list(context_refs.get("context_refs"))
    from nblane.core.ai.gateway import run_ai_action

    result = run_ai_action(
        "research.paper_search_codex",
        {"query": query, "filters": filters or {}},
        profile=profile,
        context_refs=refs,
        require_review=True,
    )
    candidates: list[PaperSearchResult] = []
    structured = result.structured if isinstance(result.structured, dict) else {}
    for row in structured.get("results") or structured.get("candidates") or []:
        candidate = PaperSearchResult.from_dict(row)
        if candidate is not None:
            candidates.append(candidate)
    if candidates:
        return candidates
    return search_papers(query, tuple((filters or {}).get("providers") or PAPER_SEARCH_PROVIDERS), int((filters or {}).get("limit") or 10), filters)


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
    imported = import_paper_search_results(profile, [result.to_dict()], [result.candidate_id], options)
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
                if bool((source.metadata or {}).get("needs_link_check")):
                    _update_source_metadata(
                        profile,
                        source_id,
                        {
                            "pdf_download_status": "skipped_needs_link_check",
                            "pdf_download_attempted_at": _now(),
                            "pdf_download_error": "PDF download skipped because the link still needs checking.",
                        },
                    )
                    continue
                try:
                    download_paper_pdf(profile, source_id, pdf_url)
                    _update_source_metadata(
                        profile,
                        source_id,
                        {
                            "pdf_download_status": "downloaded",
                            "pdf_download_attempted_at": _now(),
                        },
                    )
                except Exception as exc:
                    _update_source_metadata(
                        profile,
                        source_id,
                        {
                            "pdf_download_status": "failed",
                            "pdf_download_attempted_at": _now(),
                            "pdf_download_error": f"PDF download failed during import: {exc}",
                        },
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
    backend = _clean_text(metadata.get("structure_backend"))
    if backend == "grobid" and segments:
        return False
    return True


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
) -> dict[str, object]:
    """Return display-ready diagnostics and badges for one paper source."""

    inbox, source = _source_by_id(profile, source_id)
    metadata = source.metadata or {}
    segments = load_paper_segments(profile, source.id) if source.kind == "paper" else []
    translations = load_paper_translations(profile, source.id) if source.kind == "paper" else []
    stale_translations = [row for row in translations if row.status == "stale"]
    workspace_diagnostics = [
        item
        for item in validate_research_workspace(_profile_root(profile))
        if source.id in item
    ]
    library_diagnostics = [
        item for item in validate_paper_library(profile) if source.id in item
    ]
    citation_diagnostics = [
        *workspace_diagnostics,
        *paper_citation_diagnostics(profile, source.id),
    ]
    duplicate_refs = _duplicate_risk_refs(inbox).get(source.id, [])
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
        annotations = load_paper_annotations(profile, source.id) if is_paper else []
        translations = load_paper_translations(profile, source.id) if is_paper else []
        diagnostics = paper_source_diagnostics(profile, source.id) if is_paper else {"badges": []}
        stale = any(row.status == "stale" for row in translations)
        refs = list(source.library_node_refs)
        row = {
            "id": source.id,
            "title": source.title,
            "tree_path": ", ".join(paths.get(ref, ref) for ref in refs) or "Unsorted",
            "status": source.status,
            "has_pdf": bool((source.metadata or {}).get("pdf_asset_ref")),
            "annotations_count": len([ann for ann in annotations if ann.status == "active"]),
            "chunks_count": chunk_counts.get(source.id, 0),
            "claims_count": claim_counts.get(source.id, 0),
            "citations_count": citation_counts.get(source.id, 0),
            "last_read": _clean_text((source.metadata or {}).get("last_read_at") or source.reading.updated_at),
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
        if _clean_text((source.metadata or {}).get("pdf_download_status")) in {
            "failed",
            "skipped_needs_link_check",
        }:
            badges.append("PDF download warning")
        if source.reading.claim_candidates or source.status == "candidate_ready":
            badges.append("AI candidates")
        for badge in diagnostics.get("badges", []):  # type: ignore[union-attr]
            label = _clean_text(badge)
            if label and label not in badges:
                badges.append(label)
        match = True
        if view == "unsorted":
            match = is_paper and not refs
        elif view in {"reading", "archived", "discarded", "candidate_ready"}:
            match = source.status == view
        elif view == "annotated":
            match = bool(row["annotations_count"] or row["chunks_count"] or not source.reading.empty)
        elif node_id:
            match = node_id in refs
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
    """Format research citations as BibTeX or Markdown without writing files."""

    clean_format = _clean_text(format).lower()
    if clean_format not in {"bibtex", "markdown", "md"}:
        raise ValueError("Citation export format must be bibtex or markdown.")
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
) -> Path:
    """Persist an explicit user-requested paper export."""

    clean_format = _clean_text(format).lower()
    ext = "bib" if clean_format == "bibtex" else "md"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = _research_root(profile) / PAPER_EXPORTS_DIRNAME / f"{_slug(prefix, fallback='export')}-{timestamp}.{ext}"
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, body if body.endswith("\n") else body + "\n")
    git_backup.record_change([path], action=f"save research export {path.name}")
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
    "PAPER_ANNOTATIONS_DIRNAME",
    "PAPER_EXPORTS_DIRNAME",
    "PAPER_PAGES_DIRNAME",
    "PAPER_SEGMENTS_DIRNAME",
    "PAPER_TRANSLATIONS_DIRNAME",
    "PaperAnnotation",
    "PaperAsset",
    "PaperLibraryNode",
    "PaperLibraryTree",
    "PaperPage",
    "PaperSearchResult",
    "PaperSegment",
    "PaperTranslation",
    "auto_chunk_paper",
    "build_reader_payload",
    "check_paper_links",
    "create_chunk_from_annotation",
    "create_paper_annotation",
    "create_reading_note_markdown",
    "download_paper_pdf",
    "ensure_paper_reading_artifacts",
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
    "load_paper_translations",
    "mark_imported_paper_results",
    "move_papers_to_node",
    "paper_citation_diagnostics",
    "paper_diagnostics",
    "paper_library_path",
    "paper_library_paths",
    "paper_overview",
    "paper_pdf_asset_path",
    "paper_rows",
    "paper_source_badges",
    "paper_source_diagnostics",
    "process_grobid_fulltext",
    "pymupdf_available",
    "research_asset_root",
    "render_paper_page_preview",
    "save_paper_analysis",
    "save_paper_annotations",
    "save_paper_library_tree",
    "save_paper_note",
    "save_paper_pages",
    "save_paper_segments",
    "save_paper_translations",
    "save_research_export",
    "search_papers",
    "search_papers_with_codex",
    "text_hash",
    "translate_full_paper",
    "translation_rows_for_segments",
    "upsert_paper_library_node",
    "upsert_paper_translations",
    "validate_paper_library",
]
