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


# Modern arXiv ids (``2407.08693`` / ``2407.08693v2``) and old-style
# ``archive[.subject]/YYMMNNN`` ids (``hep-th/9901001``, ``math.GT/0309136``).
_ARXIV_NEW_ID_RE = re.compile(r"^(\d{4}\.\d{4,5})(v\d+)?$", re.IGNORECASE)
_ARXIV_OLD_ID_RE = re.compile(r"^([a-z][a-z\-]*(?:\.[a-z]{2})?/\d{7})(v\d+)?$", re.IGNORECASE)
_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
_SEMANTIC_SCHOLAR_ID_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


def _bare_arxiv_id(text: str) -> str:
    """Return a normalized arXiv id when *text* is exactly one, else ``""``."""

    clean = re.sub(r"^arxiv:\s*", "", _clean_text(text), flags=re.IGNORECASE).strip()
    if _ARXIV_NEW_ID_RE.match(clean) or _ARXIV_OLD_ID_RE.match(clean):
        return clean
    return ""


def _bare_doi(text: str) -> str:
    """Return a normalized DOI when *text* is a bare ``10.x/...`` or ``doi:`` DOI."""

    clean = _clean_text(text)
    if clean.lower().startswith("doi:"):
        clean = clean[4:].strip()
    clean = clean.rstrip(".,;")
    return clean if _DOI_RE.match(clean) else ""


def parse_paper_identifier(value: object) -> dict[str, str]:
    """Classify a pasted paper reference without touching the network.

    Accepts DOI / arXiv / Semantic Scholar URLs as well as bare identifiers
    (``10.1145/...``, ``doi:10...``, ``2407.08693v2``, ``arXiv:2407.08693``,
    ``hep-th/9901001``). Returns ``{"kind", "doi", "arxiv_id",
    "semantic_scholar_id", "url"}``; ``kind`` is ``doi`` / ``arxiv`` /
    ``semantic_scholar`` / ``url`` / ``""``. ``url`` is the canonical landing
    URL for bare ids, or the original URL otherwise.
    """

    clean = _clean_text(value)
    out = {"kind": "", "doi": "", "arxiv_id": "", "semantic_scholar_id": "", "url": ""}
    if not clean:
        return out
    arxiv = _bare_arxiv_id(clean)
    if arxiv:
        out.update(kind="arxiv", arxiv_id=arxiv, url=f"https://arxiv.org/abs/{arxiv}")
        return out
    doi = _bare_doi(clean)
    if doi:
        out.update(kind="doi", doi=doi, url=f"https://doi.org/{doi}")
        return out
    parsed = urllib.parse.urlparse(clean)
    host = parsed.netloc.lower()
    path = urllib.parse.unquote(parsed.path)
    out["url"] = clean
    if not host:
        return out
    out["kind"] = "url"
    if host.endswith("arxiv.org"):
        # /abs/<id>, /pdf/<id>[.pdf], /html/<id>; old-style ids contain one slash.
        match = re.match(r"^/(?:abs|pdf|html|format)/(.+?)/?$", path)
        candidate = _normalize_arxiv_id(match.group(1)) if match else ""
        arxiv = _bare_arxiv_id(candidate)
        if arxiv:
            out.update(kind="arxiv", arxiv_id=arxiv)
        return out
    if host.endswith("doi.org"):
        doi = _bare_doi(path.lstrip("/"))
        if doi:
            out.update(kind="doi", doi=doi)
        return out
    if host.endswith("semanticscholar.org"):
        segments = [segment for segment in path.split("/") if segment]
        if segments and segments[0] == "paper":
            paper_id = segments[-1]
            if _SEMANTIC_SCHOLAR_ID_RE.match(paper_id):
                out.update(kind="semantic_scholar", semantic_scholar_id=paper_id.lower())
        return out
    return out


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


def fetch_semantic_scholar_metadata(paper_id: str, *, timeout: float | None = None) -> dict[str, object]:
    """Fetch one paper from the Semantic Scholar Graph API. Returns ``{}`` on failure."""

    clean = _clean_text(paper_id).lower()
    if not _SEMANTIC_SCHOLAR_ID_RE.match(clean):
        return {}
    if os.environ.get("NBLANE_DISABLE_NETWORK_LOOKUPS"):
        return {}
    cache_key = f"s2:{clean}"
    cached = _metadata_cache_get(cache_key)
    if cached is not None:
        return cached
    fields = "title,abstract,authors,year,venue,externalIds,url,openAccessPdf"
    url = (
        f"https://api.semanticscholar.org/graph/v1/paper/{clean}?"
        + urllib.parse.urlencode({"fields": fields})
    )
    try:
        payload = json.loads(_http_get_text(url, accept="application/json", timeout=timeout))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    external = payload.get("externalIds") if isinstance(payload.get("externalIds"), dict) else {}
    pdf = payload.get("openAccessPdf") if isinstance(payload.get("openAccessPdf"), dict) else {}
    authors = [
        _clean_text(entry.get("name"))
        for entry in payload.get("authors") or []
        if isinstance(entry, dict) and _clean_text(entry.get("name"))
    ]
    out: dict[str, object] = {
        "semantic_scholar_id": clean,
        "title": _clean_text(payload.get("title")),
        "abstract": _clean_text(payload.get("abstract")),
        "authors": authors,
        "year": _clean_text(payload.get("year")),
        "venue": _clean_text(payload.get("venue")),
        "doi": _normalize_doi(external.get("DOI")),
        "arxiv_id": _normalize_arxiv_id(external.get("ArXiv")),
        "canonical_url": _clean_text(payload.get("url")) or f"https://www.semanticscholar.org/paper/{clean}",
        "pdf_url": _clean_text(pdf.get("url")),
    }
    out = {key: value for key, value in out.items() if value not in ("", [], None)}
    _metadata_cache_set(cache_key, out)
    return out


def lookup_paper_metadata(
    *,
    doi: str = "",
    arxiv_id: str = "",
    url: str = "",
    semantic_scholar_id: str = "",
) -> dict[str, object]:
    """Best-effort metadata lookup combining Crossref, arXiv and Semantic Scholar."""

    found: dict[str, object] = {}
    parsed_ref = parse_paper_identifier(url) if url else {}
    s2_id = _clean_text(semantic_scholar_id) or _clean_text(parsed_ref.get("semantic_scholar_id"))
    if s2_id:
        # Semantic Scholar resolves external ids, which feed the arXiv/Crossref lookups below.
        found.update(fetch_semantic_scholar_metadata(s2_id))
        arxiv_id = arxiv_id or _clean_text(found.get("arxiv_id"))
        doi = doi or _clean_text(found.get("doi"))
    arxiv = _normalize_arxiv_id(arxiv_id) or _clean_text(parsed_ref.get("arxiv_id"))
    if arxiv:
        for key, value in fetch_arxiv_metadata(arxiv).items():
            if value and not found.get(key):
                found[key] = value
    clean_doi = _normalize_doi(doi)
    if not clean_doi and not found:
        clean_doi = _clean_text(parsed_ref.get("doi"))
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
