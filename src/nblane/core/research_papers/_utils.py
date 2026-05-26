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
from ._constants import PAPER_DIAGNOSTIC_BADGES, PAPER_DIAGNOSTIC_SEVERITIES

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


def text_hash(text: str) -> str:
    """Return the stable hash label used by pages, segments, and translations."""

    return "sha256:" + hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()
