"""Helpers for evidence-pool entry ids (CLI / Web)."""

from __future__ import annotations

import re
from datetime import date


def slug_fragment(title: str) -> str:
    """ASCII slug from title for auto-generated ids."""
    s = re.sub(r"[^a-zA-Z0-9]+", "_", title.strip().lower())
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:48] if s else "entry"


def new_evidence_id(title: str, existing: set[str]) -> str:
    """Generate ``YYYYMMDD_slug`` with numeric suffix on collision."""
    base = f"{date.today().strftime('%Y%m%d')}_{slug_fragment(title)}"
    cand = base
    n = 2
    while cand in existing:
        cand = f"{base}_{n}"
        n += 1
    return cand


def fingerprint_match_id(
    entries: list[dict],
    type_: str,
    title: str,
    date_str: str,
) -> str | None:
    """Return existing id when type+title+date match (CLI upsert)."""
    t = title.strip()
    d = date_str.strip()
    for e in entries:
        if not isinstance(e, dict):
            continue
        if (
            e.get("type") == type_
            and str(e.get("title", "")).strip() == t
            and str(e.get("date", "")).strip() == d
        ):
            eid = str(e.get("id", "") or "").strip()
            if eid:
                return eid
    return None
