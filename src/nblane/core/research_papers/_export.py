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
import unicodedata
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
from nblane.core.file_state import FileConflictError, snapshot_file
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

from ._constants import (
    PAPER_ANALYSIS_DIRNAME,
    PAPER_EXPORTS_DIRNAME,
    PAPER_NOTES_DIRNAME,
)
from ._paths import (
    _jsonl_path,
    _md_path,
    _profile_root,
    _research_chunk_path,
    _research_root,
)
from ._types import PaperAnnotation, PaperLibraryNode
from ._utils import (
    _clean_list,
    _clean_mapping,
    _clean_text,
    _now,
    _slug,
    _today,
    text_hash,
)
from ._io import load_paper_annotations, load_paper_pages, load_paper_segments
from ._types import _published_year

def save_paper_note(profile: str | Path, source_id: str, body: str, *, metadata: dict[str, object] | None = None) -> Path:
    _source_by_id(profile, source_id)
    path = _md_path(profile, PAPER_NOTES_DIRNAME, source_id)
    front = {"source_id": source_id, **_clean_mapping(metadata)}
    text = "---\n" + yaml.dump(front, allow_unicode=True, sort_keys=False) + "---\n\n" + _clean_text(body) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, text)
    git_backup.record_change([path], action=f"update paper note for {source_id}")
    return path


def _bibtex_key(source: ResearchSource, year: str = "") -> str:
    persisted = _clean_text((source.metadata or {}).get(CITATION_KEY_METADATA))
    if persisted:
        return persisted
    author = _slug(source.authors[0].split()[-1] if source.authors else source.title.split()[0], fallback="paper")
    return f"{author}{year or _published_year(source.published) or 'nd'}"


# ---------------------------------------------------------------------------
# Library paper export (BibTeX / RIS / CSL-JSON / Markdown) with stable keys
# ---------------------------------------------------------------------------

CITATION_KEY_METADATA = "citation_key"
LIBRARY_EXPORT_FORMATS: dict[str, tuple[str, str]] = {
    # format -> (file extension, media type)
    "bibtex": ("bib", "application/x-bibtex; charset=utf-8"),
    "ris": ("ris", "application/x-research-info-systems; charset=utf-8"),
    "csl-json": ("json", "application/vnd.citationstyles.csl+json; charset=utf-8"),
    "markdown": ("md", "text/markdown; charset=utf-8"),
}
_LIBRARY_EXPORT_ALIASES = {
    "bib": "bibtex",
    "bibtex": "bibtex",
    "ris": "ris",
    "csl": "csl-json",
    "csl-json": "csl-json",
    "csl_json": "csl-json",
    "json": "csl-json",
    "md": "markdown",
    "markdown": "markdown",
}
_CITATION_KEY_STOPWORDS = frozenset(
    {
        "a", "an", "the", "on", "of", "in", "for", "to", "and", "with", "from",
        "by", "at", "as", "is", "are", "via", "towards", "toward",
    }
)
_CONFERENCE_VENUE_RE = re.compile(
    r"conference|proceedings|\bproc\.|symposium|workshop|congress|\bmeeting\b|"
    r"\b(?:neurips|nips|icml|iclr|cvpr|iccv|eccv|wacv|bmvc|aaai|ijcai|acl|emnlp|naacl|"
    r"coling|eacl|siggraph|chi|uist|kdd|www|sigir|wsdm|cikm|icde|vldb|sigmod|icra|iros|"
    r"rss|corl|humanoids|aistats|uai|colt|interspeech|icassp|miccai|osdi|sosp|nsdi|"
    r"usenix|ccs|ndss|isca|micro|asplos|pldi|popl|icse|fse)\b",
    re.IGNORECASE,
)
# Full venue names that are conferences even without the word "conference"
# (as Crossref / Semantic Scholar commonly spell them).
_CONFERENCE_FULL_NAME_RE = re.compile(
    r"neural information processing systems|learning representations|"
    r"computer vision and pattern recognition|robotics: science and systems|"
    r"robot learning|annual meeting of the association|"
    r"empirical methods in natural language processing",
    re.IGNORECASE,
)
# Words that mark a periodical; they win over conference keywords
# ("IEEE Transactions on ...", "Journal of Machine Learning Research").
_JOURNAL_VENUE_RE = re.compile(r"\b(?:journal|transactions|letters|magazine|review|bulletin)\b", re.IGNORECASE)
_ARXIV_CATEGORY_RE = re.compile(r"^[a-z\-]+(?:\.[A-Za-z\-]+)?$")


def normalize_library_export_format(value: object) -> str:
    """Return the canonical export format or raise ``ValueError``."""

    clean = _LIBRARY_EXPORT_ALIASES.get(_clean_text(value).lower())
    if not clean:
        raise ValueError("Export format must be bibtex, ris, csl-json, or markdown.")
    return clean


def _ascii_fold(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value)
    return "".join(char for char in folded if not unicodedata.combining(char))


def _author_surname(author: str) -> str:
    clean = _clean_text(author)
    if not clean:
        return ""
    if "," in clean:
        return clean.split(",", 1)[0].strip()
    parts = clean.split()
    return parts[-1] if parts else clean


def _citation_key_base(source: ResearchSource) -> str:
    """``surname + year + first significant title word``, lowercase ASCII."""

    def token(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", _ascii_fold(value).lower())

    surname = token(_author_surname(source.authors[0])) if source.authors else ""
    year = _published_year(source.published) or _published_year(
        _clean_text((source.metadata or {}).get("year"))
    )
    word = ""
    for raw in re.split(r"[\s\-:/]+", _clean_text(source.title)):
        candidate = token(raw)
        if candidate and candidate not in _CITATION_KEY_STOPWORDS:
            word = candidate
            break
    base = f"{surname or 'anon'}{year or 'nd'}{word}"
    return base[:64]


def _key_with_suffix(base: str, taken: set[str]) -> str:
    """Return *base* or the first free ``base + a..z, aa..`` variant."""

    if base not in taken:
        return base
    index = 0
    while True:
        index += 1
        letters = ""
        n = index
        while n:
            n, rem = divmod(n - 1, 26)
            letters = chr(ord("a") + rem) + letters
        candidate = f"{base}{letters}"
        if candidate not in taken:
            return candidate


def assign_citation_keys(
    inbox: ResearchSourceInbox,
    source_ids: list[str] | None = None,
) -> tuple[dict[str, str], list[str]]:
    """Ensure each selected source carries a persisted, unique citation key.

    Existing ``metadata["citation_key"]`` values are never changed. New keys
    are computed in source-id order so the result does not depend on the
    selection order, and collisions (with any key already persisted in the
    inbox) get ``a``, ``b``, ``c`` ... suffixes. Mutates *inbox* in place and
    returns ``({source_id: key}, [newly keyed source ids])``.
    """

    by_id = inbox.by_id()
    wanted = _clean_list(source_ids) if source_ids is not None else list(by_id)
    taken = {
        _clean_text((source.metadata or {}).get(CITATION_KEY_METADATA))
        for source in inbox.sources
    }
    taken.discard("")
    keys: dict[str, str] = {}
    created: list[str] = []
    for source_id in sorted(set(wanted)):
        source = by_id.get(source_id)
        if source is None:
            continue
        existing = _clean_text((source.metadata or {}).get(CITATION_KEY_METADATA))
        if existing:
            keys[source_id] = existing
            continue
        key = _key_with_suffix(_citation_key_base(source), taken)
        taken.add(key)
        metadata = dict(source.metadata or {})
        metadata[CITATION_KEY_METADATA] = key
        source.metadata = metadata
        keys[source_id] = key
        created.append(source_id)
    return keys, created


def _persist_citation_keys(profile: str | Path, source_ids: list[str]) -> tuple[ResearchSourceInbox, dict[str, str]]:
    """Load sources, assign missing keys, and save under a conflict check."""

    root = _profile_root(profile)
    path = root / RESEARCH_DIRNAME / "sources.yaml"
    for attempt in range(3):
        snapshot = snapshot_file(path)
        inbox = load_research_sources(root)
        keys, created = assign_citation_keys(inbox, source_ids)
        if not created:
            return inbox, keys
        try:
            save_research_sources(root, inbox, expected_snapshot=snapshot)
        except FileConflictError:
            if attempt == 2:
                raise
            continue
        return inbox, keys
    raise RuntimeError("unreachable")  # pragma: no cover


def _paper_venue_kind(source: ResearchSource) -> str:
    """Classify a paper as ``journal`` / ``conference`` / ``arxiv`` / ``misc``."""

    metadata = source.metadata or {}
    venue = _clean_text(metadata.get("venue") or metadata.get("journal") or metadata.get("booktitle"))
    arxiv_id = _clean_text(metadata.get("arxiv_id"))
    doi = _clean_text(metadata.get("doi"))
    if venue and "arxiv" not in venue.lower() and "corr" != venue.strip().lower():
        if _clean_text(metadata.get("booktitle")):
            return "conference"
        if _JOURNAL_VENUE_RE.search(venue) and not re.search(r"proceedings|conference", venue, re.IGNORECASE):
            return "journal"
        if _CONFERENCE_VENUE_RE.search(venue) or _CONFERENCE_FULL_NAME_RE.search(venue):
            return "conference"
        return "journal"
    if arxiv_id and (not doi or doi.lower().startswith("10.48550/arxiv")):
        return "arxiv"
    if venue and arxiv_id:
        return "arxiv"
    return "misc"


def _paper_export_fields(source: ResearchSource) -> dict[str, str]:
    metadata = source.metadata or {}
    arxiv_id = _clean_text(metadata.get("arxiv_id"))
    url = _clean_text(source.url or metadata.get("canonical_url"))
    if not url and arxiv_id:
        url = f"https://arxiv.org/abs/{arxiv_id}"
    category = ""
    for candidate in [metadata.get("primary_category"), *(_clean_list(metadata.get("categories")))]:
        clean = _clean_text(candidate)
        if clean and _ARXIV_CATEGORY_RE.match(clean):
            category = clean
            break
    return {
        "title": _clean_text(source.title),
        "year": _published_year(source.published) or _published_year(_clean_text(metadata.get("year"))),
        "venue": _clean_text(metadata.get("venue") or metadata.get("journal") or metadata.get("booktitle")),
        "doi": _clean_text(metadata.get("doi")),
        "arxiv_id": arxiv_id,
        "primary_class": category,
        "url": url,
        "volume": _clean_text(metadata.get("volume")),
        "issue": _clean_text(metadata.get("issue") or metadata.get("number")),
        "pages": _clean_text(metadata.get("pages") or metadata.get("page")),
        "publisher": _clean_text(metadata.get("publisher")),
        "abstract": _clean_text(metadata.get("abstract") or source.summary),
    }


def _bibtex_escape(value: str) -> str:
    text = _clean_text(value).replace("\\", r"\textbackslash{}")
    text = re.sub(r"([&%$#_])", r"\\\1", text)
    text = text.replace("{", r"\{").replace("}", r"\}")
    text = text.replace(r"\textbackslash\{\}", r"\textbackslash{}")
    return re.sub(r"\s+", " ", text)


def _bibtex_author(author: str) -> str:
    clean = _clean_text(author)
    if not clean:
        return ""
    if "," in clean:
        return _bibtex_escape(clean)
    parts = clean.split()
    if len(parts) == 1:
        # Single-token / CJK names: brace so BibTeX does not split them.
        return "{" + _bibtex_escape(clean) + "}"
    return f"{_bibtex_escape(parts[-1])}, {_bibtex_escape(' '.join(parts[:-1]))}"


def _bibtex_entry(source: ResearchSource, key: str) -> str:
    fields = _paper_export_fields(source)
    kind = _paper_venue_kind(source)
    entry_type = {"journal": "article", "conference": "inproceedings"}.get(kind, "misc")
    rows: list[tuple[str, str]] = [
        ("title", "{" + _bibtex_escape(fields["title"]) + "}"),
        ("author", " and ".join(name for name in (_bibtex_author(a) for a in source.authors) if name)),
        ("year", fields["year"]),
    ]
    if kind == "journal":
        rows.append(("journal", _bibtex_escape(fields["venue"])))
    elif kind == "conference":
        rows.append(("booktitle", _bibtex_escape(fields["venue"])))
    if kind in {"journal", "conference"}:
        rows.extend(
            [
                ("volume", _bibtex_escape(fields["volume"])),
                ("number", _bibtex_escape(fields["issue"])),
                ("pages", _bibtex_escape(fields["pages"]).replace("-", "--").replace("----", "--")),
                ("publisher", _bibtex_escape(fields["publisher"])),
            ]
        )
    if fields["arxiv_id"] and kind in {"arxiv", "misc"}:
        rows.extend(
            [
                ("eprint", fields["arxiv_id"]),
                ("archivePrefix", "arXiv"),
                ("primaryClass", fields["primary_class"]),
            ]
        )
    rows.extend(
        [
            ("doi", fields["doi"].replace("{", "").replace("}", "")),
            ("url", fields["url"].replace("{", "").replace("}", "")),
        ]
    )
    body = ",\n".join(f"  {name} = {{{value}}}" for name, value in rows if value)
    return f"@{entry_type}{{{key},\n{body}\n}}"


def _ris_entry(source: ResearchSource, key: str) -> str:
    fields = _paper_export_fields(source)
    kind = _paper_venue_kind(source)
    lines = [f"TY  - {({'journal': 'JOUR', 'conference': 'CPAPER'}).get(kind, 'GEN')}", f"ID  - {key}"]
    if fields["title"]:
        lines.append(f"TI  - {fields['title']}")
    lines.extend(f"AU  - {author}" for author in source.authors if _clean_text(author))
    if fields["year"]:
        lines.append(f"PY  - {fields['year']}")
    if kind == "journal" and fields["venue"]:
        lines.append(f"JO  - {fields['venue']}")
    elif kind == "conference" and fields["venue"]:
        lines.append(f"T2  - {fields['venue']}")
    if fields["volume"]:
        lines.append(f"VL  - {fields['volume']}")
    if fields["issue"]:
        lines.append(f"IS  - {fields['issue']}")
    if fields["pages"]:
        start, _, end = fields["pages"].replace("--", "-").partition("-")
        lines.append(f"SP  - {start.strip()}")
        if end.strip():
            lines.append(f"EP  - {end.strip()}")
    if fields["publisher"]:
        lines.append(f"PB  - {fields['publisher']}")
    if fields["arxiv_id"]:
        lines.append(f"AN  - arXiv:{fields['arxiv_id']}")
    if fields["doi"]:
        lines.append(f"DO  - {fields['doi']}")
    if fields["url"]:
        lines.append(f"UR  - {fields['url']}")
    if fields["abstract"]:
        abstract = re.sub(r"\s+", " ", fields["abstract"])
        lines.append(f"AB  - {abstract}")
    lines.append("ER  - ")
    return "\n".join(lines)


def _csl_entry(source: ResearchSource, key: str) -> dict[str, object]:
    fields = _paper_export_fields(source)
    kind = _paper_venue_kind(source)
    row: dict[str, object] = {
        "id": key,
        "citation-key": key,
        "type": {"journal": "article-journal", "conference": "paper-conference"}.get(kind, "article"),
        "title": fields["title"],
    }
    authors: list[dict[str, str]] = []
    for author in source.authors:
        clean = _clean_text(author)
        if not clean:
            continue
        if "," in clean:
            family, given = (part.strip() for part in clean.split(",", 1))
            authors.append({"family": family, "given": given})
            continue
        parts = clean.split()
        if len(parts) >= 2:
            authors.append({"family": parts[-1], "given": " ".join(parts[:-1])})
        else:
            authors.append({"literal": clean})
    if authors:
        row["author"] = authors
    if fields["year"]:
        row["issued"] = {"date-parts": [[int(fields["year"])]]}
    if fields["venue"] and kind in {"journal", "conference"}:
        row["container-title"] = fields["venue"]
    if kind == "arxiv":
        row["publisher"] = "arXiv"
        row["number"] = fields["arxiv_id"]
    for csl_key, field_key in (("volume", "volume"), ("issue", "issue"), ("page", "pages"), ("DOI", "doi"), ("URL", "url")):
        if fields[field_key] and not (kind == "arxiv" and csl_key in {"volume", "issue", "page"}):
            row[csl_key] = fields[field_key]
    if fields["publisher"] and "publisher" not in row:
        row["publisher"] = fields["publisher"]
    if fields["abstract"]:
        row["abstract"] = fields["abstract"]
    return row


def _markdown_entry(source: ResearchSource, key: str) -> str:
    fields = _paper_export_fields(source)
    head = f"- **{fields['title'] or source.id}**"
    bits = [", ".join(source.authors)] if source.authors else []
    if fields["year"]:
        bits.append(f"({fields['year']})")
    line = head + (" — " + " ".join(bits) if bits else "")
    if fields["venue"]:
        line += f". *{fields['venue']}*"
    links: list[str] = []
    if fields["doi"]:
        links.append(f"[DOI](https://doi.org/{fields['doi']})")
    if fields["arxiv_id"]:
        links.append(f"[arXiv:{fields['arxiv_id']}](https://arxiv.org/abs/{fields['arxiv_id']})")
    if fields["url"] and not links:
        links.append(f"<{fields['url']}>")
    if links:
        line += ". " + " · ".join(links)
    return line + f" `@{key}`"


def format_library_papers(
    sources: list[ResearchSource],
    keys: dict[str, str],
    *,
    format: str,
    heading: str = "Papers",
) -> str:
    """Render library sources (already keyed) in one export format."""

    clean_format = normalize_library_export_format(format)
    keyed = [(source, keys.get(source.id) or _citation_key_base(source)) for source in sources]
    if clean_format == "bibtex":
        entries = [_bibtex_entry(source, key) for source, key in keyed]
        return "\n\n".join(entries) + ("\n" if entries else "")
    if clean_format == "ris":
        entries = [_ris_entry(source, key) for source, key in keyed]
        return "\n\n".join(entries) + ("\n" if entries else "")
    if clean_format == "csl-json":
        return json.dumps([_csl_entry(source, key) for source, key in keyed], ensure_ascii=False, indent=2) + "\n"
    lines = [f"# {_clean_text(heading) or 'Papers'}", ""]
    lines.extend(_markdown_entry(source, key) for source, key in keyed)
    return "\n".join(lines).rstrip() + "\n"


def export_library_papers(
    profile: str | Path,
    source_ids: list[str],
    *,
    format: str,
    persist_keys: bool = True,
    heading: str = "Papers",
) -> dict[str, object]:
    """Export selected library papers and persist their citation keys.

    Returns ``{"body", "filename", "media_type", "format", "count", "keys"}``.
    Selection order is preserved in the output; unknown ids are skipped.
    """

    clean_format = normalize_library_export_format(format)
    wanted = _clean_list(source_ids)
    if not wanted:
        raise ValueError("Select at least one paper to export.")
    if persist_keys:
        inbox, keys = _persist_citation_keys(profile, wanted)
    else:
        inbox = load_research_sources(_profile_root(profile))
        keys, _ = assign_citation_keys(inbox, wanted)
    by_id = inbox.by_id()
    sources = [by_id[source_id] for source_id in wanted if source_id in by_id]
    if not sources:
        raise ValueError("None of the selected papers exist.")
    body = format_library_papers(sources, keys, format=clean_format, heading=heading)
    extension, media_type = LIBRARY_EXPORT_FORMATS[clean_format]
    stem = keys.get(sources[0].id, "paper") if len(sources) == 1 else f"papers-{_today()}"
    return {
        "body": body,
        "filename": f"{stem}.{extension}",
        "media_type": media_type,
        "format": clean_format,
        "count": len(sources),
        "keys": {source.id: keys.get(source.id, "") for source in sources},
    }


def _bibliography_line(source: ResearchSource, citation: ResearchCitation | None = None) -> str:
    year = _published_year(source.published)
    authors = ", ".join(source.authors)
    venue = _clean_text((source.metadata or {}).get("venue"))
    url = source.url
    bits = [bit for bit in [authors, f"({year})" if year else "", source.title, venue, url] if bit]
    line = ". ".join(bits)
    if citation and citation.locator:
        line += f", {citation.locator}"
    return line


def format_research_citations(
    profile: str | Path,
    refs: list[str],
    *,
    format: str,
) -> str:
    """Format research citations without writing files."""

    clean_format = _clean_text(format).lower()
    if clean_format not in {"bibtex", "markdown", "md", "ris", "csl", "csl-json", "csl_json"}:
        raise ValueError("Citation export format must be bibtex, markdown, ris, or csl-json.")
    sources = load_research_sources(_profile_root(profile)).by_id()
    citations = {citation.id: citation for citation in load_research_citations(_profile_root(profile))}
    selected_refs = _clean_list(refs)
    selected = [citations[ref] for ref in selected_refs if ref in citations] if selected_refs else list(citations.values())
    if clean_format == "bibtex":
        entries: list[str] = []
        seen: set[str] = set()
        for citation in selected:
            source = sources.get(citation.source_id)
            if source is None:
                continue
            year = _published_year(source.published)
            key = _bibtex_key(source, year)
            if key in seen:
                key = f"{key}{len(seen) + 1}"
            seen.add(key)
            metadata = source.metadata or {}
            fields = {
                "title": source.title,
                "author": " and ".join(source.authors),
                "year": year,
                "url": source.url,
                "doi": _clean_text(metadata.get("doi")),
                "journal": _clean_text(metadata.get("venue")),
            }
            field_lines = [
                f"  {name} = {{{value}}}"
                for name, value in fields.items()
                if value
            ]
            entries.append("@article{" + key + ",\n" + ",\n".join(field_lines) + "\n}")
        return "\n\n".join(entries).strip() + ("\n" if entries else "")
    if clean_format == "ris":
        entries = []
        for citation in selected:
            source = sources.get(citation.source_id)
            if source is None:
                continue
            metadata = source.metadata or {}
            lines = ["TY  - JOUR"]
            if source.title:
                lines.append(f"TI  - {source.title}")
            for author in source.authors:
                lines.append(f"AU  - {author}")
            year = _published_year(source.published)
            if year:
                lines.append(f"PY  - {year}")
            venue = _clean_text(metadata.get("venue"))
            if venue:
                lines.append(f"JO  - {venue}")
            doi = _clean_text(metadata.get("doi"))
            if doi:
                lines.append(f"DO  - {doi}")
            if source.url:
                lines.append(f"UR  - {source.url}")
            if citation.locator:
                lines.append(f"SP  - {citation.locator}")
            if citation.quote:
                lines.append(f"N1  - {citation.quote}")
            lines.append("ER  -")
            entries.append("\n".join(lines))
        return "\n\n".join(entries).strip() + ("\n" if entries else "")
    if clean_format in {"csl", "csl-json", "csl_json"}:
        rows = []
        seen: set[str] = set()
        for citation in selected:
            source = sources.get(citation.source_id)
            if source is None:
                continue
            year = _published_year(source.published)
            key = _bibtex_key(source, year)
            if key in seen:
                key = f"{key}-{len(seen) + 1}"
            seen.add(key)
            metadata = source.metadata or {}
            row: dict[str, object] = {
                "id": key,
                "type": "article-journal" if source.kind == "paper" else "webpage",
                "title": source.title,
            }
            authors = []
            for author in source.authors:
                parts = [part for part in author.split() if part]
                if len(parts) >= 2:
                    authors.append({"given": " ".join(parts[:-1]), "family": parts[-1]})
                elif author:
                    authors.append({"literal": author})
            if authors:
                row["author"] = authors
            if year:
                row["issued"] = {"date-parts": [[int(year)]]}
            doi = _clean_text(metadata.get("doi"))
            venue = _clean_text(metadata.get("venue"))
            if doi:
                row["DOI"] = doi
            if venue:
                row["container-title"] = venue
            if source.url:
                row["URL"] = source.url
            if citation.locator or citation.quote:
                row["note"] = " ".join(
                    part for part in [citation.locator, citation.quote] if part
                )
            rows.append(row)
        return json.dumps(rows, ensure_ascii=False, indent=2) + ("\n" if rows else "")
    lines = ["# Research Bibliography", ""]
    for citation in selected:
        source = sources.get(citation.source_id)
        if source is None:
            continue
        lines.append(f"- {citation.id}: {_bibliography_line(source, citation)}")
        if citation.quote:
            lines.append(f"  Quote: {citation.quote}")
    return "\n".join(lines).rstrip() + "\n"


def save_research_export(
    profile: str | Path,
    body: str,
    *,
    format: str,
    prefix: str = "paper-export",
    manifest: dict[str, object] | None = None,
) -> Path:
    """Persist an explicit user-requested paper export."""

    clean_format = _clean_text(format).lower()
    ext = {
        "bibtex": "bib",
        "ris": "ris",
        "csl": "json",
        "csl-json": "json",
        "csl_json": "json",
    }.get(clean_format, "md")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = _research_root(profile) / PAPER_EXPORTS_DIRNAME / f"{_slug(prefix, fallback='export')}-{timestamp}.{ext}"
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, body if body.endswith("\n") else body + "\n")
    changed_paths = [path]
    if manifest is not None:
        manifest_path = path.with_name(f"{path.stem}.manifest.yaml")
        manifest_payload = {
            "schema_version": "1.0",
            "export_file": path.name,
            "created": _now(),
            **_clean_mapping(manifest),
        }
        atomic_write_text(
            manifest_path,
            yaml.dump(
                manifest_payload,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
        )
        changed_paths.append(manifest_path)
    git_backup.record_change(changed_paths, action=f"save research export {path.name}")
    return path


def create_reading_note_markdown(
    profile: str | Path,
    source_id: str,
    *,
    claim_refs: list[str] | None = None,
    chunk_refs: list[str] | None = None,
    citation_refs: list[str] | None = None,
) -> str:
    """Build a Markdown reading note from selected paper artifacts."""

    _, source = _source_by_id(profile, source_id)
    chunks = {chunk.id: chunk for chunk in load_chunks(_profile_root(profile), source_id)}
    claims = {claim.id: claim for claim in load_research_claims(_profile_root(profile))}
    citations = {citation.id: citation for citation in load_research_citations(_profile_root(profile))}
    lines = [f"# {source.title}", ""]
    if source.summary:
        lines.extend(["## Summary", "", source.summary, ""])
    chosen_chunks = [chunks[ref] for ref in _clean_list(chunk_refs) if ref in chunks]
    if chosen_chunks:
        lines.extend(["## Chunks", ""])
        for chunk in chosen_chunks:
            lines.append(f"- {chunk.locator or chunk.id}: {chunk.text}")
        lines.append("")
    chosen_claims = [claims[ref] for ref in _clean_list(claim_refs) if ref in claims]
    if chosen_claims:
        lines.extend(["## Claims", ""])
        for claim in chosen_claims:
            lines.append(f"- [{claim.status}] {claim.text}")
        lines.append("")
    chosen_citations = [citations[ref] for ref in _clean_list(citation_refs) if ref in citations]
    if chosen_citations:
        lines.extend(["## Citations", ""])
        for citation in chosen_citations:
            lines.append(f"- {citation.locator or citation.id}: {citation.quote or citation.bibliography}")
        lines.append("")
    lines.extend(["## Boundary", "", "Paper-reading evidence is weak evidence until reviewed against real project or goal facts."])
    return "\n".join(lines).rstrip() + "\n"


def create_reading_note_pack_markdown(
    profile: str | Path,
    source_ids: object,
    *,
    claim_refs: object = None,
    chunk_refs: object = None,
    citation_refs: object = None,
    title: str = "Research Reading Note Pack",
) -> str:
    """Build a multi-source Markdown reading note pack with scoped refs."""

    clean_sources = _clean_list(source_ids)
    if not clean_sources:
        raise ValueError("Reading note pack needs at least one source.")
    profile_path = _profile_root(profile)
    sources = load_research_sources(profile_path).by_id()
    missing = [ref for ref in clean_sources if ref not in sources]
    if missing:
        raise ValueError(f"Unknown research sources: {', '.join(missing)}")
    chunks = load_chunks(profile_path)
    claims = load_research_claims(profile_path)
    citations = load_research_citations(profile_path)
    wanted_claims = set(_clean_list(claim_refs))
    wanted_chunks = set(_clean_list(chunk_refs))
    wanted_citations = set(_clean_list(citation_refs))
    chunks_by_id = {chunk.id: chunk for chunk in chunks}
    lines = [
        f"# {_clean_text(title) or 'Research Reading Note Pack'}",
        "",
        "## Sources",
        "",
    ]
    for source_id in clean_sources:
        source = sources[source_id]
        lines.append(f"- {source.title} (`{source.id}`)")
    lines.extend(["", "---", ""])
    for index, source_id in enumerate(clean_sources, start=1):
        source_chunk_refs = [
            chunk.id
            for chunk in chunks
            if chunk.source_id == source_id
            and (not wanted_chunks or chunk.id in wanted_chunks)
        ]
        source_claim_refs = [
            claim.id
            for claim in claims
            if (
                source_id in claim.source_refs
                or any(
                    chunk_ref in chunks_by_id
                    and chunks_by_id[chunk_ref].source_id == source_id
                    for chunk_ref in claim.chunk_refs
                )
            )
            and (not wanted_claims or claim.id in wanted_claims)
        ]
        source_citation_refs = [
            citation.id
            for citation in citations
            if (
                citation.source_id == source_id
                or (
                    citation.chunk_id in chunks_by_id
                    and chunks_by_id[citation.chunk_id].source_id == source_id
                )
            )
            and (not wanted_citations or citation.id in wanted_citations)
        ]
        note = create_reading_note_markdown(
            profile_path,
            source_id,
            claim_refs=source_claim_refs,
            chunk_refs=source_chunk_refs,
            citation_refs=source_citation_refs,
        )
        lines.append(f"## {index}. {sources[source_id].title}")
        lines.append("")
        lines.append(note.strip())
        if index < len(clean_sources):
            lines.extend(["", "---", ""])
    return "\n".join(lines).rstrip() + "\n"


def auto_chunk_paper(
    profile: str | Path,
    source_id: str,
    *,
    overwrite: bool = False,
) -> list[ResearchChunk]:
    """Create citable chunks from paper segments for text-mode Reader workflows."""

    _source_by_id(profile, source_id)
    existing = load_chunks(_profile_root(profile), source_id)
    if existing and not overwrite:
        return existing
    segments = load_paper_segments(profile, source_id)
    chunks: list[ResearchChunk] = []
    for index, segment in enumerate(segments, start=1):
        if not segment.text.strip():
            continue
        chunks.append(
            ResearchChunk(
                id=f"chunk:{source_slug(source_id)}:{index:03d}",
                source_id=source_id,
                text=segment.text,
                kind="paragraph",
                locator=segment.locator,
                metadata={
                    "segment_id": segment.segment_id,
                    "source_hash": segment.text_hash,
                    "page": segment.page,
                    "rects": copy.deepcopy(segment.rects),
                },
            )
        )
    save_chunks(_profile_root(profile), source_id, chunks)
    return chunks
