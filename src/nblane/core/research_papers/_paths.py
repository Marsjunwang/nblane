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
from ._utils import _clean_text, _slug

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
