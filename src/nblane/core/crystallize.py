"""Stub method crystallization: write human-editable drafts under methods/."""

from __future__ import annotations

import re
from pathlib import Path

from nblane.core.io import profile_dir


def _slug(s: str) -> str:
    """Return a filesystem-safe slug."""
    x = re.sub(r"[^a-zA-Z0-9._-]+", "-", s.strip().lower())
    return x.strip("-") or "session"


def write_method_draft(
    profile: str,
    project: str,
    body: str,
) -> Path:
    """Write ``profiles/{profile}/methods/{project}_draft.md``."""
    pdir = profile_dir(profile)
    mdir = pdir / "methods"
    mdir.mkdir(parents=True, exist_ok=True)
    slug = _slug(project)
    path = mdir / f"{slug}_draft.md"
    header = (
        f"# Method draft: {project}\n\n"
        "_Edit freely; this file is not overwritten "
        "automatically._\n\n"
    )
    path.write_text(header + body.strip() + "\n", encoding="utf-8")
    return path
