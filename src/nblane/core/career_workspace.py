"""File-first career workspace operations.

The career surface works on ``resume-source.yaml`` (the structured master
resume, shape owned by ``core/resume_doc.py``), its photo under
``media/resume/``, imported resumes (preview only until the user saves) and
tailored Markdown drafts under ``resumes/generated/``.

Writes are conflict-checked (sha256 ETag + flock) and never silently replace
user content: imports return a preview, drafts refuse to overwrite unless
asked, exports render to bytes and leave the draft file untouched.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from nblane.core import file_state, git_backup, resume_doc
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_write import atomic_write_text
from nblane.core.public_site import (
    GENERATED_RESUME_DIRNAME,
    MEDIA_DIRNAME,
    RESUMES_DIRNAME,
    _local_media_target,
    _profile_path,
    load_resume_source,
)
from nblane.core.resume_extract import extract_resume_text

PHOTO_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
PHOTO_MAX_BYTES = 5 * 1024 * 1024
IMPORT_MAX_BYTES = 10 * 1024 * 1024
PHOTO_DIR = f"{MEDIA_DIRNAME}/resume"

class CareerError(ValueError):
    """User-facing career workspace error with a stable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ResumeConflict(CareerError):
    def __init__(self, message: str = "简历已在别处修改，请刷新后再保存。") -> None:
        super().__init__("etag_mismatch", message)


# --- Master resume -------------------------------------------------------------


def resume_path(name: str) -> Path:
    return _profile_path(name) / "resume-source.yaml"


def resume_etag(name: str) -> str:
    snapshot = file_state.snapshot_file(resume_path(name))
    return snapshot.sha256 or "missing"


def load_resume(name: str) -> dict[str, Any]:
    """Normalized master resume; a missing file yields an empty resume (no write)."""
    return resume_doc.normalize_resume(load_resume_source(name), profile=name)


def update_resume(name: str, data: dict[str, Any], *, expected_etag: str = "") -> dict[str, Any]:
    """Replace the structured resume after an optional optimistic check."""
    path = resume_path(name)
    clean = resume_doc.normalize_resume(data, profile=name)
    if not clean["basics"]["name"]:
        raise CareerError("invalid_resume", "姓名不能为空。")
    with locked_profile_write(_profile_path(name), path.name):
        if expected_etag and resume_etag(name) != expected_etag:
            raise ResumeConflict()
        atomic_write_text(path, yaml.safe_dump(clean, allow_unicode=True, sort_keys=False))
    git_backup.record_change([path], action=f"update {name} career resume")
    return clean


def resume_markdown(resume: dict[str, Any]) -> str:
    return resume_doc.render_resume_markdown(resume)


# --- Photo ---------------------------------------------------------------------


def photo_file(name: str, resume: dict[str, Any] | None = None) -> Path | None:
    """Resolve ``basics.photo`` to a file under ``media/`` (else None)."""
    doc = resume if resume is not None else load_resume(name)
    rel = str((doc.get("basics") or {}).get("photo") or "").strip()
    if not rel:
        return None
    target = _local_media_target(_profile_path(name), rel)
    if target is None or not target.is_file():
        return None
    return target


def save_photo(name: str, filename: str, data: bytes) -> str:
    """Store an uploaded photo under ``media/resume/``; returns the profile-relative path.

    The resume file is not touched: the editor sets ``basics.photo`` and its
    next save records the change (same contract as blog media uploads).
    """
    ext = Path(filename or "").suffix.lower().lstrip(".")
    if ext not in PHOTO_EXTENSIONS:
        raise CareerError("invalid_photo", "照片仅支持 JPG / PNG / WebP。")
    if not data:
        raise CareerError("invalid_photo", "照片文件为空。")
    if len(data) > PHOTO_MAX_BYTES:
        raise CareerError("invalid_photo", "照片不能超过 5 MB。")
    digest = hashlib.sha256(data).hexdigest()[:10]
    rel = f"{PHOTO_DIR}/photo-{digest}.{'jpg' if ext == 'jpeg' else ext}"
    target = _profile_path(name) / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(data)
        git_backup.record_change([target], action=f"upload {name} resume photo")
    return rel


# --- Import --------------------------------------------------------------------


def import_preview(name: str, filename: str, data: bytes) -> dict[str, Any]:
    """Extract an uploaded resume and, when possible, map it to fields.

    Returns ``{filename, text, markdown, resume, method, error}``. Nothing is
    written; ``resume`` is ``None`` when the text has no recognizable
    structure (the UI then offers AI field recognition or plain use).
    """
    if len(data) > IMPORT_MAX_BYTES:
        raise CareerError("invalid_import", "文件不能超过 10 MB。")
    lowered = (filename or "").lower()
    if lowered.endswith((".html", ".htm")):
        text = data.decode("utf-8", errors="replace")
        markdown = resume_doc.html_resume_to_markdown(text)
        method = "html"
        error = ""
    else:
        markdown, error = extract_resume_text(filename, data)
        method = "markdown" if lowered.endswith((".md", ".markdown")) else "text"
    return preview_from_text(name, markdown, filename=filename, method=method, error=error)


def preview_from_text(
    name: str,
    text: str,
    *,
    filename: str = "",
    method: str = "text",
    error: str = "",
) -> dict[str, Any]:
    markdown = str(text or "").strip()
    resume = None
    if markdown and resume_doc.looks_like_markdown_resume(markdown):
        resume = resume_doc.parse_resume_markdown(markdown, profile=name)
        if method == "text":
            method = "markdown"
    return {
        "filename": filename,
        "text": markdown,
        "markdown": resume_doc.render_resume_markdown(resume) if resume else markdown,
        "resume": resume,
        "method": method if resume else "text",
        "error": error,
    }


# --- Tailored drafts -----------------------------------------------------------


def _drafts_root(name: str) -> Path:
    return _profile_path(name) / RESUMES_DIRNAME / GENERATED_RESUME_DIRNAME


def clean_draft_id(target: str) -> str:
    return re.sub(r"[^a-zA-Z0-9一-鿿_-]+", "-", str(target or "").strip()).strip("-")[:80]


def draft_etag(path: Path) -> str:
    return file_state.snapshot_file(path).sha256 or "missing"


def _meta_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}.meta.yaml")


def _load_meta(path: Path) -> dict[str, Any]:
    meta_path = _meta_path(path)
    if not meta_path.is_file():
        return {}
    try:
        raw = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _draft_row(path: Path) -> dict[str, Any]:
    stat = path.stat()
    meta = _load_meta(path)
    return {
        "id": path.stem,
        "target": path.stem,
        "path": f"{RESUMES_DIRNAME}/{GENERATED_RESUME_DIRNAME}/{path.name}",
        "markdown": path.read_text(encoding="utf-8"),
        "etag": draft_etag(path),
        "updated_at": stat.st_mtime,
        "jd_text": str(meta.get("jd_text") or ""),
        "notes": str(meta.get("notes") or ""),
        "analysis": meta.get("analysis") if isinstance(meta.get("analysis"), dict) else None,
    }


def list_drafts(name: str) -> list[dict[str, Any]]:
    root = _drafts_root(name)
    if not root.is_dir():
        return []
    rows = [_draft_row(path) for path in root.glob("*.md") if path.is_file()]
    return sorted(rows, key=lambda row: row["updated_at"], reverse=True)


def draft_path(name: str, draft_id: str) -> Path | None:
    clean = clean_draft_id(draft_id)
    if not clean or clean != draft_id:
        return None
    path = _drafts_root(name) / f"{clean}.md"
    return path if path.is_file() else None


def get_draft(name: str, draft_id: str) -> dict[str, Any]:
    path = draft_path(name, draft_id)
    if path is None:
        raise CareerError("career_draft_not_found", "定制简历不存在。")
    return _draft_row(path)


def save_draft(
    name: str,
    target: str,
    markdown: str,
    *,
    overwrite: bool = False,
    expected_etag: str = "",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create (or, with *overwrite*/*expected_etag*, replace) one tailored draft.

    *meta* (JD text / notes) is written to the ``<id>.meta.yaml`` sidecar.
    """
    clean_target = clean_draft_id(target)
    if not clean_target:
        raise CareerError("invalid_career_draft", "请填写目标岗位标识。")
    if not str(markdown or "").strip():
        raise CareerError("invalid_career_draft", "定制简历内容为空。")
    root = _drafts_root(name)
    path = root / f"{clean_target}.md"
    root.mkdir(parents=True, exist_ok=True)
    with locked_profile_write(root, path.name):
        if path.exists():
            if expected_etag:
                if draft_etag(path) != expected_etag:
                    raise ResumeConflict("定制简历已在别处修改，请刷新后再保存。")
            elif not overwrite:
                raise CareerError("career_draft_exists", f"已存在同名定制简历：{clean_target}")
        atomic_write_text(path, str(markdown).rstrip() + "\n")
        changed = [path]
        if meta:
            meta_path = _meta_path(path)
            current = _load_meta(path)
            current.update({k: v for k, v in meta.items() if k in META_FIELDS and v is not None})
            atomic_write_text(meta_path, yaml.safe_dump(current, allow_unicode=True, sort_keys=False))
            changed.append(meta_path)
    git_backup.record_change(changed, action=f"save {name} tailored resume draft")
    return _draft_row(path)


META_FIELDS = ("jd_text", "notes", "analysis")


def update_draft_meta(name: str, draft_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    """Merge JD / notes / analysis into ``<id>.meta.yaml`` (the draft text is untouched)."""
    path = draft_path(name, draft_id)
    if path is None:
        raise CareerError("career_draft_not_found", "定制简历不存在。")
    meta_path = _meta_path(path)
    with locked_profile_write(path.parent, meta_path.name):
        meta = _load_meta(path)
        for key in META_FIELDS:
            if key in patch and patch[key] is not None:
                meta[key] = patch[key]
        atomic_write_text(meta_path, yaml.safe_dump(meta, allow_unicode=True, sort_keys=False))
    git_backup.record_change([meta_path], action=f"update {name} tailored resume notes")
    return _draft_row(path)


def delete_draft(name: str, draft_id: str) -> None:
    path = draft_path(name, draft_id)
    if path is None:
        raise CareerError("career_draft_not_found", "定制简历不存在。")
    meta_path = _meta_path(path)
    with locked_profile_write(path.parent, path.name):
        path.unlink()
        meta_path.unlink(missing_ok=True)
    git_backup.record_change([path, meta_path], action=f"delete {name} tailored resume draft")


# --- Export ----------------------------------------------------------------------


def _strip_target_comment(markdown: str) -> str:
    """Drop the legacy ``<!-- Target -->`` header and a whole-document code fence."""
    text = re.sub(r"^\s*<!--\s*Target:.*?-->\s*", "", str(markdown or ""), flags=re.S)
    fence = re.match(r"^\s*```(?:markdown|md)?\s*\n(.*?)\n```\s*$", text, re.S)
    return fence.group(1) if fence else text


def page_html(resume: dict[str, Any], markdown: str, *, photo_src: str = "") -> str:
    """Print-ready resume page for *markdown*, styled with the resume's language/titles."""
    return resume_doc.render_resume_html(
        _strip_target_comment(markdown),
        title=resume["basics"].get("name") or "Resume",
        photo_src=photo_src,
        lang=resume_doc.detect_lang(resume),
        summary_title=resume_doc.section_title(resume, "summary"),
        inline_titles=(resume_doc.section_title(resume, "education"), resume_doc.section_title(resume, "honors")),
    )


def export_document(
    name: str,
    *,
    markdown: str,
    fmt: str,
    include_photo: bool = True,
) -> tuple[bytes, str, str]:
    """Render *markdown* to ``(bytes, media_type, extension)``; writes nothing.

    HTML and PDF inline the master resume photo so the file is self-contained.
    """
    resume = load_resume(name)
    if fmt == "md":
        return _strip_target_comment(markdown).encode("utf-8"), "text/markdown; charset=utf-8", "md"
    if fmt not in ("html", "pdf"):
        raise CareerError("invalid_export_format", "导出格式仅支持 md / html / pdf。")
    photo = resume_doc.photo_data_uri(photo_file(name, resume)) if include_photo else ""
    page = page_html(resume, markdown, photo_src=photo)
    if fmt == "html":
        return page.encode("utf-8"), "text/html; charset=utf-8", "html"
    try:
        return resume_doc.render_resume_pdf(page), "application/pdf", "pdf"
    except resume_doc.ResumePdfUnavailable as exc:
        raise CareerError("pdf_unavailable", str(exc)) from exc


# --- Overview --------------------------------------------------------------


def overview(name: str) -> dict[str, Any]:
    resume = load_resume(name)
    return {
        "profile": name,
        "resume": resume,
        "resume_markdown": resume_markdown(resume),
        "resume_etag": resume_etag(name),
        "has_resume": resume_doc.has_content(resume),
        "drafts": list_drafts(name),
    }
