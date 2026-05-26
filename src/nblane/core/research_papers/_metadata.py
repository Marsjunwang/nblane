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
from ._constants import PAPER_METADATA_FETCH_TIMEOUT_SECONDS
from ._utils import _clean_text

_PAPER_METADATA_LOOKUP_CACHE: dict[str, tuple[float, dict[str, object]]] = {}


_PAPER_METADATA_LOOKUP_CACHE_LOCK = threading.Lock()


_PAPER_METADATA_LOOKUP_CACHE_TTL = 24 * 60 * 60.0


def _http_get_text(url: str, *, accept: str = "application/json", timeout: float | None = None) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "nblane-paper-reading/1.0 (mailto:noreply@nblane.local)",
            "Accept": accept,
        },
        method="GET",
    )
    deadline = timeout if timeout is not None else PAPER_METADATA_FETCH_TIMEOUT_SECONDS
    with urllib.request.urlopen(request, timeout=deadline) as response:
        raw = response.read()
    return raw.decode("utf-8", errors="ignore")


def _normalize_doi(doi: object) -> str:
    text = _clean_text(doi)
    if not text:
        return ""
    if text.lower().startswith("https://doi.org/"):
        text = text[len("https://doi.org/") :]
    elif text.lower().startswith("http://doi.org/"):
        text = text[len("http://doi.org/") :]
    elif text.lower().startswith("doi:"):
        text = text[len("doi:") :]
    return text.strip().strip("/")


def _normalize_arxiv_id(arxiv: object) -> str:
    text = _clean_text(arxiv)
    if not text:
        return ""
    text = re.sub(r"^arxiv:\s*", "", text, flags=re.IGNORECASE)
    text = text.split("?", 1)[0].split("#", 1)[0]
    if text.lower().endswith(".pdf"):
        text = text[: -len(".pdf")]
    return text.strip().strip("/")


def _metadata_cache_get(key: str) -> dict[str, object] | None:
    if not key:
        return None
    with _PAPER_METADATA_LOOKUP_CACHE_LOCK:
        entry = _PAPER_METADATA_LOOKUP_CACHE.get(key)
        if not entry:
            return None
        ts, payload = entry
        if (time.time() - ts) > _PAPER_METADATA_LOOKUP_CACHE_TTL:
            _PAPER_METADATA_LOOKUP_CACHE.pop(key, None)
            return None
        return dict(payload)


def _metadata_cache_set(key: str, payload: dict[str, object]) -> None:
    if not key:
        return
    with _PAPER_METADATA_LOOKUP_CACHE_LOCK:
        _PAPER_METADATA_LOOKUP_CACHE[key] = (time.time(), dict(payload))


def _metadata_cache_clear() -> None:
    """Test hook: drop all cached metadata lookups."""

    with _PAPER_METADATA_LOOKUP_CACHE_LOCK:
        _PAPER_METADATA_LOOKUP_CACHE.clear()


def fetch_crossref_metadata(doi: str, *, timeout: float | None = None) -> dict[str, object]:
    """Fetch DOI metadata from Crossref. Returns ``{}`` on any failure.

    Network calls can be disabled by setting ``NBLANE_DISABLE_NETWORK_LOOKUPS=1``,
    which is honored by the test suite.
    """

    clean = _normalize_doi(doi)
    if not clean:
        return {}
    if os.environ.get("NBLANE_DISABLE_NETWORK_LOOKUPS"):
        return {}
    cache_key = f"crossref:{clean.lower()}"
    cached = _metadata_cache_get(cache_key)
    if cached is not None:
        return cached
    url = f"https://api.crossref.org/works/{urllib.parse.quote(clean, safe='/')}"
    try:
        text = _http_get_text(url, accept="application/json", timeout=timeout)
        payload = json.loads(text)
    except Exception:
        return {}
    message = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(message, dict):
        return {}
    title_list = message.get("title")
    title = ""
    if isinstance(title_list, list) and title_list:
        title = _clean_text(title_list[0])
    elif isinstance(title_list, str):
        title = _clean_text(title_list)
    abstract_html = _clean_text(message.get("abstract"))
    abstract = re.sub(r"<[^>]+>", "", abstract_html) if abstract_html else ""
    authors: list[str] = []
    raw_authors = message.get("author")
    if isinstance(raw_authors, list):
        for entry in raw_authors:
            if not isinstance(entry, dict):
                continue
            given = _clean_text(entry.get("given"))
            family = _clean_text(entry.get("family"))
            full = " ".join(part for part in (given, family) if part).strip()
            if full:
                authors.append(full)
            elif _clean_text(entry.get("name")):
                authors.append(_clean_text(entry.get("name")))
    year = ""
    issued = message.get("issued")
    if isinstance(issued, dict):
        parts = issued.get("date-parts")
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            year = _clean_text(parts[0][0])
    venue = ""
    container = message.get("container-title")
    if isinstance(container, list) and container:
        venue = _clean_text(container[0])
    elif isinstance(container, str):
        venue = _clean_text(container)
    out: dict[str, object] = {
        "doi": clean,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "year": year,
        "venue": venue,
        "canonical_url": _clean_text(message.get("URL")) or f"https://doi.org/{clean}",
    }
    _metadata_cache_set(cache_key, out)
    return out


def fetch_arxiv_metadata(arxiv_id: str, *, timeout: float | None = None) -> dict[str, object]:
    """Fetch arXiv metadata via the public Atom API. Returns ``{}`` on failure."""

    clean = _normalize_arxiv_id(arxiv_id)
    if not clean:
        return {}
    if os.environ.get("NBLANE_DISABLE_NETWORK_LOOKUPS"):
        return {}
    cache_key = f"arxiv:{clean.lower()}"
    cached = _metadata_cache_get(cache_key)
    if cached is not None:
        return cached
    url = f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(clean, safe='')}"
    try:
        text = _http_get_text(url, accept="application/atom+xml", timeout=timeout)
        root = ET.fromstring(text)
    except Exception:
        return {}
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = root.find("a:entry", ns)
    if entry is None:
        return {}
    title = _clean_text((entry.findtext("a:title", default="", namespaces=ns) or "").replace("\n", " "))
    abstract = _clean_text((entry.findtext("a:summary", default="", namespaces=ns) or "").replace("\n", " "))
    published = _clean_text(entry.findtext("a:published", default="", namespaces=ns))
    year = published[:4] if published[:4].isdigit() else ""
    authors = [
        _clean_text(node.findtext("a:name", default="", namespaces=ns))
        for node in entry.findall("a:author", ns)
    ]
    authors = [name for name in authors if name]
    pdf_url = ""
    canonical = ""
    for link in entry.findall("a:link", ns):
        rel = (link.get("rel") or "").strip()
        title_attr = (link.get("title") or "").strip().lower()
        href = _clean_text(link.get("href"))
        if title_attr == "pdf":
            pdf_url = href
        elif rel == "alternate":
            canonical = href
    if not pdf_url:
        pdf_url = f"https://arxiv.org/pdf/{clean}"
    if not canonical:
        canonical = f"https://arxiv.org/abs/{clean}"
    out: dict[str, object] = {
        "arxiv_id": clean,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "year": year,
        "canonical_url": canonical,
        "pdf_url": pdf_url,
    }
    _metadata_cache_set(cache_key, out)
    return out


def lookup_paper_metadata(*, doi: str = "", arxiv_id: str = "", url: str = "") -> dict[str, object]:
    """Best-effort metadata lookup combining Crossref and arXiv signals."""

    found: dict[str, object] = {}
    arxiv = _normalize_arxiv_id(arxiv_id)
    if not arxiv:
        parsed = urllib.parse.urlparse(_clean_text(url))
        if "arxiv.org" in parsed.netloc:
            arxiv = _normalize_arxiv_id(parsed.path.rsplit("/", 1)[-1])
    if arxiv:
        found.update(fetch_arxiv_metadata(arxiv))
    clean_doi = _normalize_doi(doi)
    if not clean_doi and not found:
        parsed = urllib.parse.urlparse(_clean_text(url))
        if "doi.org" in parsed.netloc:
            clean_doi = _normalize_doi(parsed.path.lstrip("/"))
    if clean_doi:
        crossref = fetch_crossref_metadata(clean_doi)
        for key, value in crossref.items():
            # Prefer the more authoritative value when both providers respond.
            if not value:
                continue
            existing = found.get(key)
            if not existing:
                found[key] = value
    return found
