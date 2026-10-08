"""Whole-paper Markdown export for AI reading.

Builds one Markdown document from the GROBID/PyMuPDF segments a paper
already has, plus cropped table/figure images and page renders for
equations. AI flows read this instead of a sampled list of segments:

- quick analysis sends the Markdown text (tables included as extracted
  PyMuPDF text) to a text-only model;
- deep read sends the Markdown and attaches the images to Codex, so table
  numbers and formulas can be checked against the real page.

Every paragraph ends with a short anchor such as ``〔s12〕``. Models cite the
short id; ``aliases`` maps it back to the real segment id so saved refs and
Reader jump links stay unchanged.

The export is derived data. It is cached under the research asset root
(outside the git-backed data dir), keyed by PDF fingerprint plus a digest of
the segments, and rebuilt only when either changes.
"""

from __future__ import annotations

import base64
import contextlib
import fcntl
import hashlib
import io
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nblane.core.file_write import atomic_write_text
from nblane.core.research_papers import (
    PaperSegment,
    extract_paper_figures,
    load_paper_segments,
    paper_pdf_asset_path,
    research_asset_root,
)
from nblane.core.research_papers import _paper_pdf_fingerprint as _pdf_fingerprint
from nblane.core.research_papers import _paper_segment_is_reference_section as _is_reference
from nblane.core.research_papers import _source_by_id
from nblane.core.research_workspace import source_slug

PAPER_MARKDOWN_DIRNAME = "paper-markdown"
EXPORT_VERSION = "1"
MAX_FIGURE_IMAGES = 20
MAX_EQUATION_PAGES = 4
MAX_TABLE_PAGES = 6
MAX_REFERENCE_ENTRIES = 80

_LABEL_RE = re.compile(r"^\s*(fig(?:ure)?|table|tab)\.?\s*(\d+)\s*([:.]?)", re.IGNORECASE)


@dataclass
class PaperMarkdown:
    """A built (or cached) whole-paper Markdown export."""

    source_id: str
    markdown: str
    aliases: dict[str, str] = field(default_factory=dict)
    images: list[dict[str, Any]] = field(default_factory=list)
    directory: Path | None = None
    stats: dict[str, Any] = field(default_factory=dict)

    def image_paths(self, *, limit: int | None = None) -> list[Path]:
        """Return absolute image paths, figures/tables first, then equation pages."""

        ordered = sorted(self.images, key=lambda row: 0 if row.get("kind") != "page" else 1)
        paths = [Path(str(row["path"])) for row in ordered if row.get("path")]
        return paths[:limit] if limit else paths


def _label_key(text: str) -> tuple[str, bool]:
    """Return ("table:3", has_colon) for captions like "Table 3: ...", else ("", False)."""

    match = _LABEL_RE.match(text or "")
    if not match:
        return "", False
    kind = "table" if match.group(1).lower().startswith("tab") else "figure"
    return f"{kind}:{int(match.group(2))}", bool(match.group(3))


def _is_label_only_caption(text: str) -> bool:
    """GROBID emits a bare "Table 3 :" segment next to the real caption."""

    key, _ = _label_key(text)
    return bool(key) and len(text.strip()) <= 16


def _caption_labels(segments: list[PaperSegment]) -> dict[str, str]:
    """Map caption segment id -> "table:3" / "figure:1".

    For tables GROBID often emits the label ("Table 3 :", page 0) as its own
    segment and the description without it, so a bare label is carried
    forward to the next caption that has none of its own.
    """

    labels: dict[str, str] = {}
    pending = ""
    for segment in segments:
        if str(segment.kind or "").lower() != "caption":
            continue
        text = " ".join(str(segment.text or "").split())
        key, _ = _label_key(text)
        if _is_label_only_caption(text):
            pending = key
            continue
        if key:
            labels[segment.segment_id] = key
        elif pending:
            labels[segment.segment_id] = pending
        pending = ""
    return labels


def _segments_digest(segments: list[PaperSegment]) -> str:
    digest = hashlib.sha256()
    for segment in segments:
        digest.update(f"{segment.segment_id}\x1f{segment.kind}\x1f{segment.text_hash or segment.text}\x1e".encode("utf-8"))
    return digest.hexdigest()[:16]


def _export_dir(profile: str | Path, source_id: str) -> Path:
    return research_asset_root(profile) / PAPER_MARKDOWN_DIRNAME / source_slug(source_id)


def _cache_key(profile: str | Path, source_id: str, segments: list[PaperSegment]) -> str:
    _, source = _source_by_id(profile, source_id)
    fingerprint = _pdf_fingerprint(source) or "nopdf"
    raw = f"{EXPORT_VERSION}|{fingerprint}|{_segments_digest(segments)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _heading_prefix(segment: PaperSegment) -> str:
    depth = len([part for part in segment.section_path if str(part or "").strip()])
    return "#" * min(4, 1 + max(1, depth))


def _write_figure_images(
    profile: str | Path,
    source_id: str,
    image_dir: Path,
) -> list[dict[str, Any]]:
    """Crop tables/figures from the PDF into PNG files."""

    rows = extract_paper_figures(profile, source_id, max_items=MAX_FIGURE_IMAGES, max_width=1000)
    images: list[dict[str, Any]] = []
    for row in rows:
        data_url = str(row.get("data_url") or "")
        if "," not in data_url:
            continue
        page = int(row.get("page") or 0)
        order = int(row.get("order") or 0)
        kind = str(row.get("kind") or "figure")
        path = image_dir / f"p{page:02d}-{order:02d}-{kind}.png"
        path.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
        caption = str(row.get("caption") or "").strip()
        label, has_colon = _label_key(caption)
        images.append(
            {
                "path": str(path),
                "name": path.name,
                "kind": kind,
                "page": page,
                "caption": caption[:300],
                "label": label,
                "label_is_caption": has_colon,
            }
        )
    return images


def _table_texts(pdf_path: Path, pages: set[int]) -> dict[int, list[str]]:
    """Return PyMuPDF table Markdown per page (numbers are reliable, headers often are not)."""

    if not pages:
        return {}
    try:
        import fitz  # type: ignore[import-not-found]
    except Exception:
        return {}
    out: dict[int, list[str]] = {}
    try:
        with fitz.open(str(pdf_path)) as doc:
            for page_number in sorted(pages):
                if page_number < 1 or page_number > doc.page_count:
                    continue
                try:
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        tables = list(doc[page_number - 1].find_tables().tables or [])
                except Exception:
                    continue
                for table in tables:
                    try:
                        text = table.to_markdown().strip()
                    except Exception:
                        continue
                    # A header line plus separator is not a table worth sending.
                    if text.count("\n") >= 2:
                        out.setdefault(page_number, []).append(text)
    except Exception:
        return out
    return out


def _write_page_renders(
    pdf_path: Path,
    pages: list[int],
    image_dir: Path,
    *,
    reasons: dict[int, str],
) -> list[dict[str, Any]]:
    """Render whole pages: display equations (formula text is lossy) and
    tables the cropper missed (numbers must be checkable)."""

    try:
        import fitz  # type: ignore[import-not-found]
    except Exception:
        return []
    images: list[dict[str, Any]] = []
    try:
        with fitz.open(str(pdf_path)) as doc:
            for page_number in pages:
                if page_number < 1 or page_number > doc.page_count:
                    continue
                path = image_dir / f"page-{page_number:02d}.png"
                doc[page_number - 1].get_pixmap(dpi=150, alpha=False).save(str(path))
                images.append(
                    {
                        "path": str(path),
                        "name": path.name,
                        "kind": "page",
                        "page": page_number,
                        "caption": f"Page {page_number} ({reasons.get(page_number, 'full page')})",
                        "label": "",
                        "label_is_caption": False,
                    }
                )
    except Exception:
        return images
    return images


def _render_markdown(
    title: str,
    segments: list[PaperSegment],
    images: list[dict[str, Any]],
    table_texts: dict[int, list[str]],
) -> tuple[str, dict[str, str], dict[str, Any]]:
    by_label: dict[str, dict[str, Any]] = {}
    for image in images:
        label = str(image.get("label") or "")
        if not label:
            continue
        # Prefer the crop whose caption is the real "Table 3:" line over a
        # crop that only mentions the label in body text.
        if label not in by_label or (image.get("label_is_caption") and not by_label[label].get("label_is_caption")):
            by_label[label] = image
    placed: set[str] = set()
    pending_tables = {page: list(rows) for page, rows in table_texts.items()}
    caption_labels = _caption_labels(segments)
    page_by_number = {int(image["page"]): image for image in images if image.get("kind") == "page"}

    lines: list[str] = []
    aliases: dict[str, str] = {}
    reference_lines: list[str] = []
    counts = {"paragraphs": 0, "captions": 0, "formulas": 0, "tables_text": 0}
    if title:
        lines.extend([f"# {title}", ""])

    for segment in segments:
        text = " ".join(str(segment.text or "").split())
        if not text:
            continue
        kind = str(segment.kind or "paragraph").lower()
        if _is_reference(segment):
            if kind != "heading" and len(reference_lines) < MAX_REFERENCE_ENTRIES:
                reference_lines.append(f"- {text[:240]}")
            continue
        if kind == "title":
            if not title:
                lines.extend([f"# {text}", ""])
            continue
        if kind == "heading":
            lines.extend([f"{_heading_prefix(segment)} {text}", ""])
            continue
        if kind == "caption" and _is_label_only_caption(text):
            continue
        alias = f"s{len(aliases) + 1}"
        aliases[alias] = segment.segment_id
        anchor = f"〔{alias}〕"
        page_note = f" (p.{segment.page})" if segment.page else ""
        if kind == "caption":
            counts["captions"] += 1
            label = caption_labels.get(segment.segment_id, "")
            prefix = ""
            if label and not _label_key(text)[0]:
                kind_name, number = label.split(":", 1)
                prefix = f"**{kind_name.capitalize()} {number}.** "
            lines.extend([f"> {prefix}{text} {anchor}{page_note}", ""])
            image = by_label.get(label) if label else None
            if image and image["name"] not in placed:
                placed.add(image["name"])
                lines.extend([f"![{label}](images/{image['name']})", ""])
            elif label.startswith("table:") and segment.page in page_by_number:
                lines.extend([f"(See page render: images/{page_by_number[segment.page]['name']})", ""])
            if label.startswith("table:") and pending_tables.get(segment.page):
                counts["tables_text"] += 1
                lines.extend(
                    [
                        "<!-- table text extracted by PyMuPDF: numbers are reliable, multi-level headers may be lost -->",
                        pending_tables[segment.page].pop(0),
                        "",
                    ]
                )
            continue
        if kind == "formula":
            counts["formulas"] += 1
            lines.extend([f"Equation (text extraction, see page image): `{text}` {anchor}{page_note}", ""])
            continue
        counts["paragraphs"] += 1
        lines.extend([f"{text} {anchor}", ""])

    unplaced = [image for image in images if image["name"] not in placed and image.get("kind") != "page"]
    page_renders = [image for image in images if image.get("kind") == "page"]
    if page_renders:
        lines.extend(["## Page renders", ""])
        for image in page_renders:
            lines.extend([f"![{image['caption']}](images/{image['name']})", ""])
    if unplaced:
        lines.extend(["## Other figure and table crops", ""])
        for image in unplaced:
            lines.extend([f"![p.{image['page']} {image['kind']}](images/{image['name']}) {image['caption'][:160]}", ""])
    if reference_lines:
        lines.extend(["## References", "", *reference_lines, ""])
    stats = {
        **counts,
        "segments": len(segments),
        "cited_segments": len(aliases),
        "images": len(images),
        "references": len(reference_lines),
    }
    return "\n".join(lines).rstrip() + "\n", aliases, stats


def build_paper_markdown(
    profile: str | Path,
    source_id: str,
    *,
    include_images: bool = True,
    force: bool = False,
) -> PaperMarkdown:
    """Return the whole-paper Markdown export, building it when stale.

    ``include_images=False`` skips cropping (text-only callers); a cached
    export that already has images is still returned as is.
    """

    root = _export_dir(profile, source_id)
    root.mkdir(parents=True, exist_ok=True)
    # Quick analysis and deep read may build the same export at once; the
    # build deletes and rewrites its directory, so serialise per paper.
    with open(root / ".build.lock", "a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            return _build_paper_markdown_locked(
                profile,
                source_id,
                root,
                include_images=include_images,
                force=force,
            )
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _build_paper_markdown_locked(
    profile: str | Path,
    source_id: str,
    root: Path,
    *,
    include_images: bool,
    force: bool,
) -> PaperMarkdown:
    segments = sorted(load_paper_segments(profile, source_id), key=lambda row: (row.order, row.page))
    _, source = _source_by_id(profile, source_id)
    key = _cache_key(profile, source_id, segments)
    directory = root / key
    manifest_path = directory / "manifest.json"
    markdown_path = directory / "paper.md"

    if not force and manifest_path.is_file() and markdown_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest = {}
        if manifest and (manifest.get("has_images") or not include_images):
            images = [row for row in manifest.get("images") or [] if Path(str(row.get("path") or "")).is_file()]
            return PaperMarkdown(
                source_id=source_id,
                markdown=markdown_path.read_text(encoding="utf-8"),
                aliases=dict(manifest.get("aliases") or {}),
                images=images,
                directory=directory,
                stats=dict(manifest.get("stats") or {}),
            )

    image_dir = directory / "images"
    if directory.exists():
        shutil.rmtree(directory)
    image_dir.mkdir(parents=True, exist_ok=True)

    images: list[dict[str, Any]] = []
    table_texts: dict[int, list[str]] = {}
    try:
        pdf_path = paper_pdf_asset_path(profile, source_id)
    except (FileNotFoundError, ValueError):
        pdf_path = None
    if pdf_path is not None:
        caption_labels = _caption_labels(segments)
        caption_pages = {
            segment.page
            for segment in segments
            if segment.page and caption_labels.get(segment.segment_id, "").startswith("table:")
        }
        table_texts = _table_texts(pdf_path, caption_pages)
        if include_images:
            images = _write_figure_images(profile, source_id, image_dir)
            cropped_labels = {str(row.get("label") or "") for row in images if row.get("label")}
            reasons: dict[int, str] = {}
            # Tables without their own crop get a page render: numbers must
            # stay checkable even when region detection merged or missed them.
            for segment in segments:
                label = caption_labels.get(segment.segment_id, "")
                if label.startswith("table:") and label not in cropped_labels and segment.page:
                    reasons.setdefault(segment.page, f"{label.replace(':', ' ')} without a crop")
            table_pages = sorted(reasons)[:MAX_TABLE_PAGES]
            equation_pages = sorted(
                {
                    segment.page
                    for segment in segments
                    if segment.kind == "formula" and segment.page and not _is_reference(segment)
                }
                - set(table_pages)
            )[:MAX_EQUATION_PAGES]
            for page in equation_pages:
                reasons.setdefault(page, "display equations")
            images.extend(
                _write_page_renders(pdf_path, sorted(set(table_pages) | set(equation_pages)), image_dir, reasons=reasons)
            )

    markdown, aliases, stats = _render_markdown(str(source.title or ""), segments, images, table_texts)
    atomic_write_text(markdown_path, markdown)
    atomic_write_text(
        manifest_path,
        json.dumps(
            {
                "version": EXPORT_VERSION,
                "source_id": source_id,
                "has_images": bool(include_images),
                "aliases": aliases,
                "images": images,
                "stats": stats,
            },
            ensure_ascii=False,
            indent=2,
        ),
    )
    # Older exports for this paper (previous PDF/segments) are dead weight.
    for stale in root.iterdir():
        if stale.is_dir() and stale.name != key:
            shutil.rmtree(stale, ignore_errors=True)
    return PaperMarkdown(
        source_id=source_id,
        markdown=markdown,
        aliases=aliases,
        images=images,
        directory=directory,
        stats=stats,
    )


__all__ = [
    "PAPER_MARKDOWN_DIRNAME",
    "PaperMarkdown",
    "build_paper_markdown",
]
