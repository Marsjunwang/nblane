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

LIBRARY_TREE_FILENAME = "library-tree.yaml"
PAPER_PAGES_DIRNAME = "paper-pages"
PAPER_SEGMENTS_DIRNAME = "paper-segments"
PAPER_STRUCTURE_DIRNAME = "paper-structure"
PAPER_ANNOTATIONS_DIRNAME = "annotations"
PAPER_TRANSLATIONS_DIRNAME = "translations"
PAPER_ANALYSIS_DIRNAME = "analysis"
PAPER_NOTES_DIRNAME = "notes"
PAPER_EXPORTS_DIRNAME = "exports"

PAPER_ANNOTATION_KINDS = ("highlight", "note", "question")
PAPER_ANNOTATION_STATUSES = ("active", "deleted")
PAPER_TRANSLATION_STATUSES = ("translated", "missing", "stale", "failed")
PAPER_TRANSLATION_SCOPES = ("segment", "page", "selection", "layout", "structure")
PAPER_STRUCTURE_VERSION = "v4"
PAPER_STRUCTURE_TRANSLATION_KINDS = ("title", "heading", "paragraph", "caption")
PAPER_STRUCTURE_BODY_EXCLUDED_KINDS = (
    "authors",
    "affiliation",
    "figure",
    "table",
    "footnote",
    "reference",
    "symbol",
    "figure_label",
    "table_cell",
)
PAPER_SEARCH_PROVIDERS = ("arxiv_html", "arxiv", "semantic_scholar")
NO_LLM_TRANSLATION_WARNING = "No LLM translation backend produced text."
PDF_MAX_BYTES_DEFAULT = 75 * 1024 * 1024
PDF_DOWNLOAD_TIMEOUT_SECONDS_DEFAULT = 45.0
PDF_DOWNLOAD_IDLE_TIMEOUT_SECONDS_DEFAULT = 10.0
PDF_DOWNLOAD_CHUNK_BYTES = 32 * 1024
GROBID_FULLTEXT_TIMEOUT_SECONDS_DEFAULT = 120.0
GROBID_RETRY_COOLDOWN_SECONDS_DEFAULT = 24 * 60 * 60
PAPER_TRANSLATION_BATCH_SIZE_DEFAULT = 12
PAPER_STRUCTURE_TRANSLATION_BATCH_SIZE_DEFAULT = 12
PAPER_LAYOUT_TRANSLATION_BATCH_SIZE_DEFAULT = 12
PAPER_PAGE_TRANSLATION_BATCH_SIZE_DEFAULT = 4
PAPER_TRANSLATION_BATCH_CHARS_DEFAULT = 9000
PAPER_PAGE_TRANSLATION_BATCH_CHARS_DEFAULT = 12000
PAPER_TRANSLATION_INCLUDE_REFERENCES_ENV = "NBLANE_PAPER_TRANSLATION_INCLUDE_REFERENCES"
PAPER_REFERENCE_SECTION_LABELS = {
    "references",
    "bibliography",
    "works cited",
    "literature cited",
    "参考文献",
    "參考文獻",
}
PAPER_DIAGNOSTIC_BADGES = {
    "grobid_unavailable": "GROBID unavailable",
    "needs_structured_extraction": "Needs structured extraction",
    "fallback_extraction": "Fallback ready",
    "stale_translation": "Stale translation",
    "citation_broken": "Citation broken",
    "private_source": "Private source",
    "duplicate_risk": "Duplicate risk",
}
PAPER_DIAGNOSTIC_SEVERITIES = {
    "grobid_unavailable": "warning",
    "needs_structured_extraction": "warning",
    "fallback_extraction": "info",
    "stale_translation": "warning",
    "citation_broken": "error",
    "private_source": "info",
    "duplicate_risk": "warning",
}

PAPER_TITLE_SIMILARITY_THRESHOLD = 0.92
PAPER_METADATA_FETCH_TIMEOUT_SECONDS = 8.0
_PAPER_METADATA_LOOKUP_CACHE: dict[str, tuple[float, dict[str, object]]] = {}
_PAPER_METADATA_LOOKUP_CACHE_LOCK = threading.Lock()
_PAPER_METADATA_LOOKUP_CACHE_TTL = 24 * 60 * 60.0
