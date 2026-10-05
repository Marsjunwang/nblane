"""File-first career workspace operations.

The career surface only consumes the resume source, an uploaded/typed resume,
and a job description.  It intentionally does not call evidence/claim
helpers, so a person can prepare an application without understanding the
internal growth model.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from nblane.core import file_state, git_backup
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_write import atomic_write_text
from nblane.core.public_site import (
    GENERATED_RESUME_DIRNAME,
    RESUMES_DIRNAME,
    _profile_path,
    load_resume_source,
    render_resume_markdown,
)

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#.-]{1,}|[\u4e00-\u9fff]{2,}")


def _words(text: str) -> list[str]:
    return list(dict.fromkeys(w.lower() for w in _WORD_RE.findall(text or "")))


def resume_path(name: str) -> Path:
    return _profile_path(name) / "resume-source.yaml"


def resume_etag(name: str) -> str:
    snapshot = file_state.snapshot_file(resume_path(name))
    return snapshot.sha256 or "missing"


def update_resume(name: str, data: dict[str, Any], *, expected_etag: str = "") -> dict[str, Any]:
    """Replace the structured resume after an optional optimistic check."""
    path = resume_path(name)
    with locked_profile_write(_profile_path(name), path.name):
        if expected_etag and resume_etag(name) != expected_etag:
            raise ValueError("resume changed since it was loaded")
        clean = dict(data)
        clean.setdefault("profile", name)
        atomic_write_text(path, yaml.safe_dump(clean, allow_unicode=True, sort_keys=False))
    git_backup.record_change([path], action=f"update {name} career resume")
    return clean


def _draft_rows(name: str) -> list[dict[str, Any]]:
    root = _profile_path(name) / RESUMES_DIRNAME / GENERATED_RESUME_DIRNAME
    if not root.is_dir():
        return []
    rows = []
    for path in sorted(root.glob("*.md")):
        if path.name == ".gitkeep":
            continue
        rows.append({"id": path.stem, "target": path.stem, "path": str(path), "markdown": path.read_text(encoding="utf-8")})
    return rows


def overview(name: str) -> dict[str, Any]:
    source = load_resume_source(name)
    markdown = render_resume_markdown(source)
    return {
        "profile": name,
        "resume": source,
        "resume_markdown": markdown,
        "resume_etag": resume_etag(name),
        "drafts": _draft_rows(name),
    }


def match(resume_md: str, jd_text: str) -> dict[str, Any]:
    """Produce a deterministic, reviewable match report without external AI."""
    resume_words = set(_words(resume_md))
    jd_words = _words(jd_text)
    covered = [word for word in jd_words if word in resume_words]
    missing = [word for word in jd_words if word not in resume_words]
    score = round(100 * len(covered) / max(len(jd_words), 1))
    return {
        "score": score,
        "summary": f"已覆盖 {len(covered)} / {len(jd_words)} 个 JD 关键词（规则分析，可人工复核）。",
        "key_requirements": jd_words[:30],
        "covered": covered[:30],
        "gaps": missing[:30],
        "keyword_suggestions": missing[:15],
        "strengthen": [f"在真实经历中补充与“{word}”相关的事实、范围或结果" for word in missing[:8]],
        "de_emphasize": [],
        "interview_questions": [f"请结合真实经历说明你如何使用 {word}。" for word in covered[:5]],
    }


def save_draft(name: str, target: str, markdown: str, *, overwrite: bool = False) -> dict[str, Any]:
    clean_target = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff_-]+", "-", target.strip()).strip("-")[:80]
    if not clean_target:
        raise ValueError("target is required")
    root = _profile_path(name) / RESUMES_DIRNAME / GENERATED_RESUME_DIRNAME
    path = root / f"{clean_target}.md"
    root.mkdir(parents=True, exist_ok=True)
    with locked_profile_write(root, path.name):
        if path.exists() and not overwrite:
            raise FileExistsError(f"resume draft already exists: {clean_target}")
        atomic_write_text(path, markdown.rstrip() + "\n")
    git_backup.record_change([path], action=f"save {name} tailored resume draft")
    return {"id": clean_target, "target": clean_target, "path": str(path), "markdown": path.read_text(encoding="utf-8")}
