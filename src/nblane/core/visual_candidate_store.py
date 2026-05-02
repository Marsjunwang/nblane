"""Temporary visual asset candidates for AI blog patches."""

from __future__ import annotations

import base64
import json
import hashlib
import mimetypes
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nblane.core.profile_io import profile_dir


CANDIDATE_DIRNAME = ".candidates"
DEFAULT_TTL_SECONDS = 24 * 60 * 60
DEFAULT_INLINE_PREVIEW_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class VisualCandidate:
    """One generated asset stored outside the published media library."""

    path: Path
    relative_path: str
    filename: str
    kind: str
    created_at: float


def _clean_segment(value: str, fallback: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._~\-\u4e00-\u9fff]+", "-", str(value or ""))
    clean = clean.strip(".-")
    return clean[:80] or fallback


def _safe_filename(filename: str, *, fallback: str) -> str:
    path = Path(filename)
    stem = _clean_segment(path.stem, fallback)
    suffix = re.sub(r"[^A-Za-z0-9.]+", "", path.suffix.lower())[:12]
    return f"{stem}{suffix or '.bin'}"


def _candidate_root(profile: str) -> Path:
    root = profile_dir(profile) / "blog" / CANDIDATE_DIRNAME
    root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve_candidate_path(profile: str, candidate_path: str | Path) -> Path:
    root = _candidate_root(profile).resolve()
    raw = Path(str(candidate_path or ""))
    path = raw if raw.is_absolute() else profile_dir(profile) / raw
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise FileNotFoundError("Visual candidate path is outside the candidate store.") from exc
    return resolved


def _profile_relative(profile: str, path: Path) -> str:
    return path.resolve().relative_to(profile_dir(profile).resolve()).as_posix()


def candidate_file_path(profile: str, candidate_path: str | Path) -> Path:
    """Resolve a candidate path after verifying it stays inside the store."""

    return _resolve_candidate_path(profile, candidate_path)


def candidate_preview_src(
    profile: str,
    candidate_path: str | Path,
    *,
    kind: str = "",
    max_inline_bytes: int = DEFAULT_INLINE_PREVIEW_BYTES,
) -> str:
    """Return an inline browser preview for small staged image candidates."""

    path = _resolve_candidate_path(profile, candidate_path)
    if not path.exists() or not path.is_file():
        return ""
    clean_kind = str(kind or "").strip().lower()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if clean_kind and clean_kind != "image":
        return ""
    if not mime.startswith("image/"):
        return ""
    if path.stat().st_size > max_inline_bytes:
        return ""
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def write_candidate(
    profile: str,
    slug: str,
    patch_id: str,
    *,
    data: bytes,
    filename: str,
    kind: str,
    alt: str = "",
    caption: str = "",
    provider: str = "",
    model: str = "",
    prompt: str = "",
) -> VisualCandidate:
    """Write candidate bytes and metadata without touching media/blog/<slug>/."""

    if not data:
        raise ValueError("Visual candidate data is empty.")
    clean_patch_id = _clean_segment(patch_id, "patch")
    candidate_dir = _candidate_root(profile) / clean_patch_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    clean_kind = str(kind or "image").strip().lower() or "image"
    clean_filename = _safe_filename(filename, fallback=clean_kind)
    target = candidate_dir / clean_filename
    if target.exists():
        digest = hashlib.sha256(data).hexdigest()[:10]
        target = candidate_dir / f"{target.stem}-{digest}{target.suffix}"
    target.write_bytes(data)
    created_at = time.time()
    metadata = {
        "profile": profile,
        "slug": slug,
        "patch_id": clean_patch_id,
        "filename": target.name,
        "kind": clean_kind,
        "alt": str(alt or ""),
        "caption": str(caption or ""),
        "provider": str(provider or ""),
        "model": str(model or ""),
        "prompt": str(prompt or ""),
        "created_at": created_at,
    }
    target.with_suffix(f"{target.suffix}.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return VisualCandidate(
        path=target,
        relative_path=_profile_relative(profile, target),
        filename=target.name,
        kind=clean_kind,
        created_at=created_at,
    )


def promote_candidate(
    profile: str,
    slug: str,
    candidate_path: str | Path,
    *,
    kind: str = "image",
    alt: str = "",
    caption: str = "",
):
    """Move a temporary candidate into media/blog/<slug>/ and remove the temp file."""

    path = _resolve_candidate_path(profile, candidate_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError("Visual candidate is no longer available.")
    meta_path = path.with_suffix(f"{path.suffix}.json")
    metadata: dict[str, Any] = {}
    if meta_path.exists():
        try:
            loaded = json.loads(meta_path.read_text(encoding="utf-8"))
            metadata = loaded if isinstance(loaded, dict) else {}
        except Exception:
            metadata = {}
    media_kind = str(kind or metadata.get("kind") or "image").strip().lower()
    final_alt = str(alt or metadata.get("alt") or "")
    final_caption = str(caption or metadata.get("caption") or "")
    from nblane.core import public_site

    result = public_site.add_blog_media_bytes(
        profile,
        slug,
        data=path.read_bytes(),
        filename=path.name,
        kind="video" if media_kind == "video" else "image",
        alt=final_alt,
        caption=final_caption,
        append=False,
    )
    path.unlink(missing_ok=True)
    meta_path.unlink(missing_ok=True)
    try:
        path.parent.rmdir()
    except OSError:
        pass
    return result


def candidate_exists(profile: str, candidate_path: str | Path) -> bool:
    """Return whether a temporary candidate path still points to a staged file."""

    try:
        path = _resolve_candidate_path(profile, candidate_path)
    except FileNotFoundError:
        return False
    return path.exists() and path.is_file()


def discard_candidate(profile: str, candidate_path: str | Path) -> bool:
    """Delete a temporary candidate if it still exists."""

    try:
        path = _resolve_candidate_path(profile, candidate_path)
    except FileNotFoundError:
        return False
    removed = False
    if path.exists():
        path.unlink()
        removed = True
    path.with_suffix(f"{path.suffix}.json").unlink(missing_ok=True)
    try:
        path.parent.rmdir()
    except OSError:
        pass
    return removed


def discard_patch(profile: str, patch_id: str) -> bool:
    """Delete all candidates for one AI patch id."""

    clean_patch_id = _clean_segment(patch_id, "patch")
    path = _candidate_root(profile) / clean_patch_id
    if not path.exists():
        return False
    shutil.rmtree(path)
    return True


def cleanup_expired(profile: str, *, now: float | None = None, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> int:
    """Remove candidate directories older than ``ttl_seconds``."""

    root = _candidate_root(profile)
    cutoff = (time.time() if now is None else now) - ttl_seconds
    removed = 0
    for child in root.iterdir():
        if not child.is_dir():
            continue
        try:
            mtime = child.stat().st_mtime
        except OSError:
            continue
        if mtime < cutoff:
            shutil.rmtree(child, ignore_errors=True)
            removed += 1
    return removed
