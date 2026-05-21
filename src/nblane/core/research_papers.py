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
import hashlib
import io
import json
import math
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
PAPER_TRANSLATION_SCOPES = ("segment", "page", "selection", "layout")
PAPER_SEARCH_PROVIDERS = ("arxiv", "semantic_scholar")
NO_LLM_TRANSLATION_WARNING = "No LLM translation backend produced text."
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
                used_rects: list[dict[str, object]] = []
                for item_index, (kind, kind_index, raw_rect) in enumerate(candidates, start=1):
                    rect = _expanded_figure_rect(raw_rect, captions, page_width=page_width, page_height=page_height)
                    if rect is None:
                        continue
                    if _rect_area(rect) < max(900.0, page_width * page_height * 0.01):
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
                    caption = _nearest_caption_text(rect, captions)
                    figure_id = f"figure:{source_slug(source_id)}:{page_number}:{item_index:03d}"
                    out.append(
                        {
                            "id": figure_id,
                            "anchor_id": figure_id,
                            "page": page_number,
                            "order": item_index,
                            "kind": kind,
                            "kind_index": kind_index,
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
    needs_pages = not pages or pdf_changed
    needs_segments = not segments or pdf_changed
    warnings: list[str] = []

    if needs_pages:
        emit_progress("extracting_pages", "Extracting page text...", 1, saved=0)
        try:
            pages = extract_paper_pages(profile, source_id, backend="auto")
        except Exception as exc:
            warnings.append(f"Page extraction failed: {exc}")

    _, source = _source_by_id(profile, source_id)
    source_metadata = dict(source.metadata or {})
    if needs_segments:
        configured_grobid = bool(_clean_text(os.getenv("NBLANE_GROBID_URL")))
        segment_backend = "grobid" if prefer_grobid and configured_grobid else "fallback"
        emit_progress(
            "running_grobid" if segment_backend == "grobid" else "saving_segments",
            "Running GROBID..." if segment_backend == "grobid" else "Saving fallback text...",
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
    coordinate_summary = {
        "segments_with_rects": rect_count,
        "segments_without_rects": max(0, len(segments) - rect_count),
    }
    coordinate_warnings: list[str] = []
    if structure_backend == "grobid" and segments:
        if rect_count == 0:
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
    with urllib.request.urlopen(request, timeout=60) as response:
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
    for dirname in (PAPER_PAGES_DIRNAME, PAPER_SEGMENTS_DIRNAME, PAPER_TRANSLATIONS_DIRNAME):
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
                line_bboxes.append(span_bbox)
                max_font_size = max(max_font_size, font_size)
            text = "".join(line_parts).strip()
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
        parts: list[str] = []
        for raw_span in raw_line.get("spans") or []:
            if not isinstance(raw_span, dict):
                continue
            parts.append(str(raw_span.get("text") or ""))
            try:
                max_font = max(max_font, float(raw_span.get("size") or 0))
            except (TypeError, ValueError):
                pass
        line = "".join(parts).strip()
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
            text = "\n".join(_clean_text(row.get("text")) for row in group if _clean_text(row.get("text"))).strip()
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
            _clean_text(row.get("scope_ref") or row.get("segment_id")): row
            for row in translations
            if _clean_text(row.get("scope_type")) == "layout" and _clean_text(row.get("target_lang") or "zh") == target_lang
        }
        for raw_unit in sorted(layout_rows, key=lambda row: (int(row.get("page") or 0), int(row.get("order") or 0), _clean_text(row.get("unit_id")))):
            scope_ref = _clean_text(raw_unit.get("scope_ref") or raw_unit.get("unit_id"))
            source_text = _clean_text(raw_unit.get("source_text") or raw_unit.get("text"))
            if not scope_ref or not source_text:
                continue
            source_hash = _clean_text(raw_unit.get("source_hash")) or text_hash(source_text)
            translation = layout_translations.get(scope_ref)
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
                "scope_type": "layout",
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
    layout_units = build_paper_layout_units(profile, source_id, pages=context_pages)
    page_models = _page_models_from_pdf(profile, source_id, context_pages)
    if not page_models:
        page_models = _page_models_from_layout_units(layout_units, context_pages)
    figures = extract_paper_figures(profile, source_id, pages=context_pages, max_items=12, max_width=520)
    reader_layout_units = reader_translation_layout_units(layout_units)
    layout_scope_refs = {
        _clean_text(row.get("scope_ref") or row.get("unit_id"))
        for row in reader_layout_units
        if isinstance(row, dict)
    }
    all_segments = load_paper_segments(profile, source_id)
    outline = _reader_outline_from_segments(all_segments)
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
    prefer_layout_units = bool(reader_layout_units)
    translations: list[dict[str, object]] = []
    for row in current_translation_rows:
        if row.target_lang != target_lang:
            continue
        scope_type = _clean_text(row.scope_type) or "segment"
        row_page = int(row.page or segment_pages.get(row.segment_id, 0))
        include_row = False
        if scope_type == "layout":
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
        if include_row:
            translations.append({**row.to_dict(), "page": row_page})
    page_context_rows = [page_row for page_row in all_pages if page_row.page in context_page_set]
    unit_pages = [] if prefer_layout_units else page_context_rows
    unit_segments = [] if prefer_layout_units else segments
    translation_units, translation_summary = build_translation_units(
        pages=unit_pages,
        segments=unit_segments,
        translations=translations,
        target_lang=target_lang,
        layout_units=reader_layout_units,
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
) -> dict[str, int]:
    by_scope = {
        row.scope_ref: row
        for row in translations
        if row.scope_type == "layout" and row.target_lang == target_lang
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
    return {
        "segment_id": scope_ref,
        "source_id": source_id,
        "scope_type": "layout",
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
        return NO_LLM_TRANSLATION_WARNING
    return ""


def translate_full_paper(
    profile: str | Path,
    source_id: str,
    target_lang: str = "zh",
    mode: str = "missing_or_stale",
    batch_size: int = 20,
    *,
    scope_strategy: str = "segment",
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
    if clean_scope_strategy not in {"auto", "segment", "page", "layout"}:
        clean_scope_strategy = "auto"
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
    pages = load_paper_pages(profile, source_id)
    layout_units = (
        reader_translation_layout_units(build_paper_layout_units(profile, source_id))
        if clean_scope_strategy == "layout"
        else []
    )
    if layout_units:
        translations = load_paper_translations(profile, source_id)
        existing_by_scope = {
            row.scope_ref: row
            for row in translations
            if row.scope_type == "layout" and row.target_lang == clean_lang
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
        unit_payloads = [_layout_unit_translation_payload(unit, source_id=source_id) for unit in selected_units]
        unit_map: dict[str, dict[str, object]] = {}
        for unit, payload in zip(selected_units, unit_payloads, strict=False):
            unit_map[_clean_text(payload.get("segment_id"))] = unit
            unit_map[_clean_text(payload.get("scope_ref"))] = unit
        batches = [
            unit_payloads[index : index + clean_batch_size]
            for index in range(0, len(unit_payloads), clean_batch_size)
        ]
        batches_completed = 0
        units_processed = 0
        if batches:
            from nblane.core.ai.gateway import translate_paper_segments

            for batch in batches:
                try:
                    result = translate_paper_segments(
                        ai_profile if ai_profile is not None else _profile_name(profile),
                        source_id,
                        batch,
                        target_lang=clean_lang,
                        require_review=require_review,
                    )
                except Exception as exc:
                    warnings.append(f"Translation batch failed: {exc}")
                    batches_completed += 1
                    units_processed += len(batch)
                    continue
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
                        warnings.append("Skipped translation row without a known layout scope.")
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
                            "scope_type": "layout",
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
                batches_completed += 1
                units_processed += len(batch)
                if progress_callback is not None:
                    try:
                        progress_callback(
                            {
                                "source_id": source_id,
                                "target_lang": clean_lang,
                                "mode": clean_mode,
                                "scope": "layout",
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
        if accepted_rows:
            upsert_paper_translations(profile, source_id, accepted_rows)
        final_translations = load_paper_translations(profile, source_id)
        counts = _layout_translation_status_counts(layout_units, final_translations, target_lang=clean_lang)
        return {
            "source_id": source_id,
            "target_lang": clean_lang,
            "mode": clean_mode,
            "scope": "layout",
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
        batches = [
            page_payloads[index : index + clean_batch_size]
            for index in range(0, len(page_payloads), clean_batch_size)
        ]
        batches_completed = 0
        pages_processed = 0
        if batches:
            from nblane.core.ai.gateway import translate_paper_segments

            for batch in batches:
                try:
                    result = translate_paper_segments(
                        ai_profile if ai_profile is not None else _profile_name(profile),
                        source_id,
                        batch,
                        target_lang=clean_lang,
                        require_review=require_review,
                    )
                except Exception as exc:
                    warnings.append(f"Translation batch failed: {exc}")
                    batches_completed += 1
                    pages_processed += len(batch)
                    continue
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
                batches_completed += 1
                pages_processed += len(batch)
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
        if accepted_rows:
            upsert_paper_translations(profile, source_id, accepted_rows)
        final_translations = load_paper_translations(profile, source_id)
        counts = _page_translation_status_counts(pages, final_translations, target_lang=clean_lang)
        return {
            "source_id": source_id,
            "target_lang": clean_lang,
            "mode": clean_mode,
            "scope": "page",
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
    batches_completed = 0
    segments_processed = 0
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
                batches_completed += 1
                segments_processed += len(batch)
                if progress_callback is not None:
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
                    except Exception as callback_exc:
                        warnings.append(f"Progress callback failed: {callback_exc}")
                continue
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
            batches_completed += 1
            segments_processed += len(batch)
            if progress_callback is not None:
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
                except Exception as exc:
                    warnings.append(f"Progress callback failed: {exc}")

    if accepted_rows:
        upsert_paper_translations(profile, source_id, accepted_rows)
    final_translations = load_paper_translations(profile, source_id)
    counts = _translation_status_counts(segments, final_translations, target_lang=clean_lang)
    return {
        "source_id": source_id,
        "target_lang": clean_lang,
        "mode": clean_mode,
        "scope": "segment",
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

    search_context = _paper_search_context_bundle(
        profile,
        query,
        filters or {},
        context_refs=context_refs,
    )
    result = run_ai_action(
        "research.paper_search_codex",
        search_context,
        profile=profile,
        context_refs=refs,
        require_review=True,
    )
    candidates: list[PaperSearchResult] = []
    structured = result.structured if isinstance(result.structured, dict) else {}
    for row in structured.get("results") or structured.get("candidates") or []:
        candidate = PaperSearchResult.from_dict(row)
        if candidate is not None and _paper_search_result_has_import_ref(candidate):
            candidates.append(candidate)
    if candidates:
        return candidates
    return search_papers(query, tuple((filters or {}).get("providers") or PAPER_SEARCH_PROVIDERS), int((filters or {}).get("limit") or 10), filters)


def _paper_search_context_bundle(
    profile: str | Path,
    query: str,
    filters: dict[str, Any],
    *,
    context_refs: dict | list[str] | None = None,
) -> dict[str, Any]:
    """Build the compact prompt payload for local read-only Codex search."""

    payload: dict[str, Any] = {
        "query": _clean_text(query),
        "filters": copy.deepcopy(filters),
        "providers": _clean_list(filters.get("providers")) or list(PAPER_SEARCH_PROVIDERS),
    }
    if isinstance(context_refs, dict):
        payload["context_refs"] = _clean_list(context_refs.get("context_refs"))
        payload["project_refs"] = _clean_list(context_refs.get("project_refs"))
        payload["goal_refs"] = _clean_list(context_refs.get("goal_refs"))
    elif isinstance(context_refs, list):
        payload["context_refs"] = _clean_list(context_refs)
    else:
        payload["context_refs"] = []
    payload["already_imported"] = _paper_search_imported_refs(profile)
    payload["library_tree_hint"] = _paper_search_library_tree_hint(profile)
    return payload


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


def _paper_search_result_has_import_ref(result: PaperSearchResult) -> bool:
    """Return True when a search candidate has a checkable import reference."""

    return bool(
        result.canonical_url
        or result.pdf_url
        or result.doi
        or result.arxiv_id
        or result.semantic_scholar_id
        or result.provider_refs
    )


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
    "NO_LLM_TRANSLATION_WARNING",
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
    "build_paper_layout_units",
    "build_reader_payload",
    "build_translation_units",
    "check_paper_links",
    "create_chunk_from_annotation",
    "create_paper_annotation",
    "create_reading_note_markdown",
    "download_paper_pdf",
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
    "process_grobid_fulltext",
    "pymupdf_available",
    "reader_translation_layout_units",
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
    "translation_text_from_row",
    "translation_rows_for_segments",
    "upsert_paper_library_node",
    "upsert_paper_translations",
    "validate_paper_library",
]
