"""External research connector adapters.

Connectors normalize external discovery results into Research Source Inbox
items. Secrets are intentionally read from the environment/session boundary
and never persisted to ``research/connectors.yaml``.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from nblane.core import git_backup
from nblane.core.agent_activity import append_activity_item
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_io import profile_dir
from nblane.core.research_sources import (
    RESEARCH_DIRNAME,
    RESEARCH_SOURCES_FILENAME,
    ResearchSourceInbox,
    add_research_source,
    load_research_sources,
    save_research_sources,
)
from nblane.core.yaml_io import _load_yaml_dict

CONNECTORS_FILENAME = "connectors.yaml"
CONNECTOR_SCHEMA_VERSION = "1.0"
CONNECTOR_PROVIDERS = (
    "arxiv",
    "semantic_scholar",
    "github",
    "x_twitter",
    "xiaohongshu",
)
AUTO_PROVIDERS = {"arxiv", "semantic_scholar", "github"}
SECRET_KEY_FRAGMENTS = ("token", "secret", "api_key", "apikey", "password", "cookie", "bearer")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today() -> str:
    return date.today().isoformat()


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _clean_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    clean = _clean_text(value).lower()
    if clean in {"1", "true", "yes", "on"}:
        return True
    if clean in {"0", "false", "no", "off"}:
        return False
    return default


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


def _sanitize_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, object] = {}
    for key, item in value.items():
        clean_key = _clean_text(key)
        if not clean_key:
            continue
        lowered = clean_key.lower()
        if any(fragment in lowered for fragment in SECRET_KEY_FRAGMENTS):
            continue
        if isinstance(item, dict):
            out[clean_key] = _sanitize_mapping(item)
        elif isinstance(item, list):
            out[clean_key] = [
                _sanitize_mapping(child) if isinstance(child, dict) else child
                for child in item
            ]
        else:
            out[clean_key] = item
    return out


def _research_root(profile: str | Path) -> Path:
    if isinstance(profile, Path):
        return profile / RESEARCH_DIRNAME if profile.name != RESEARCH_DIRNAME else profile
    return profile_dir(profile) / RESEARCH_DIRNAME


def _profile_root(profile: str | Path) -> Path:
    root = _research_root(profile)
    return root.parent if root.name == RESEARCH_DIRNAME else root


def _profile_name(profile: str | Path) -> str:
    if isinstance(profile, Path):
        return _profile_root(profile).name
    return str(profile)


def _connectors_path(profile: str | Path) -> Path:
    return _research_root(profile) / CONNECTORS_FILENAME


def _connector_id(provider: str, query: str = "") -> str:
    seed = query or provider
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
    return f"{provider}:{digest}"


@dataclass
class ConnectorItem:
    """One normalized external item ready for Source Inbox import."""

    provider: str
    title: str
    url: str = ""
    kind: str = "web"
    external_id: str = ""
    authors: list[str] = field(default_factory=list)
    published: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    def to_source_kwargs(self, *, privacy_default: str = "private") -> dict[str, object]:
        metadata = _sanitize_mapping(
            {
                **self.metadata,
                "provider": self.provider,
                "external_id": self.external_id,
            }
        )
        return {
            "title": self.title,
            "kind": self.kind,
            "url": self.url,
            "authors": self.authors,
            "published": self.published,
            "summary": self.summary,
            "tags": self.tags,
            "visibility": privacy_default if privacy_default in {"private", "public"} else "private",
            "origin": "connector",
            "metadata": metadata,
        }

    def fingerprint(self) -> str:
        canonical_url = _canonical_url(self.url)
        title_hash = hashlib.sha1(self.title.lower().strip().encode("utf-8")).hexdigest()[:12]
        return "|".join([self.provider, self.external_id, canonical_url, title_hash])

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "title": self.title,
            "url": self.url,
            "kind": self.kind,
            "external_id": self.external_id,
            "authors": list(self.authors),
            "published": self.published,
            "summary": self.summary,
            "tags": list(self.tags),
            "metadata": _sanitize_mapping(self.metadata),
        }


@dataclass
class ConnectorSyncResult:
    """Result of one connector sync."""

    profile: str
    connector_id: str
    provider: str
    dry_run: bool = False
    discovered: int = 0
    imported: int = 0
    skipped: int = 0
    items: list[dict[str, object]] = field(default_factory=list)
    imported_source_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "connector_id": self.connector_id,
            "provider": self.provider,
            "dry_run": self.dry_run,
            "discovered": self.discovered,
            "imported": self.imported,
            "skipped": self.skipped,
            "items": list(self.items),
            "imported_source_ids": list(self.imported_source_ids),
            "warnings": list(self.warnings),
            "error": self.error,
        }


class ConnectorAdapter:
    """Base connector adapter."""

    provider = ""

    def discover(self, config: dict[str, object]) -> list[ConnectorItem]:
        raise NotImplementedError


def _http_get(url: str, *, headers: dict[str, str] | None = None, timeout: int = 20) -> bytes:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


class ArxivAdapter(ConnectorAdapter):
    provider = "arxiv"

    def discover(self, config: dict[str, object]) -> list[ConnectorItem]:
        query = _clean_text(config.get("query"))
        if not query:
            return []
        limit = max(1, min(int(config.get("limit") or 10), 50))
        encoded = urllib.parse.urlencode(
            {
                "search_query": query,
                "start": "0",
                "max_results": str(limit),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
        )
        payload = _http_get(f"https://export.arxiv.org/api/query?{encoded}")
        return parse_arxiv_feed(payload)


class SemanticScholarAdapter(ConnectorAdapter):
    provider = "semantic_scholar"

    def discover(self, config: dict[str, object]) -> list[ConnectorItem]:
        query = _clean_text(config.get("query") or config.get("paper_id"))
        if not query:
            return []
        limit = max(1, min(int(config.get("limit") or 10), 50))
        fields = "title,url,abstract,authors,year,externalIds,publicationDate"
        if config.get("paper_id"):
            url = (
                "https://api.semanticscholar.org/graph/v1/paper/"
                + urllib.parse.quote(query)
                + "?"
                + urllib.parse.urlencode({"fields": fields})
            )
            payload = json.loads(_http_get(url).decode("utf-8"))
            return parse_semantic_scholar_payload(payload)
        encoded = urllib.parse.urlencode({"query": query, "limit": str(limit), "fields": fields})
        headers: dict[str, str] = {}
        api_key = os.getenv("NBLANE_SEMANTIC_SCHOLAR_API_KEY", "").strip()
        if api_key:
            headers["x-api-key"] = api_key
        payload = json.loads(
            _http_get(
                f"https://api.semanticscholar.org/graph/v1/paper/search?{encoded}",
                headers=headers,
            ).decode("utf-8")
        )
        return parse_semantic_scholar_payload(payload)


class GitHubAdapter(ConnectorAdapter):
    provider = "github"

    def discover(self, config: dict[str, object]) -> list[ConnectorItem]:
        query = _clean_text(config.get("query") or config.get("repo"))
        if not query:
            return []
        headers = {"Accept": "application/vnd.github+json"}
        token = os.getenv("NBLANE_GITHUB_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if "/" in query and " " not in query and not query.startswith("http"):
            url = f"https://api.github.com/repos/{urllib.parse.quote(query, safe='/')}"
            payload = json.loads(_http_get(url, headers=headers).decode("utf-8"))
            return parse_github_payload(payload)
        encoded = urllib.parse.urlencode({"q": query, "sort": "updated", "order": "desc", "per_page": "10"})
        payload = json.loads(
            _http_get(f"https://api.github.com/search/repositories?{encoded}", headers=headers).decode("utf-8")
        )
        return parse_github_payload(payload)


class XTwitterAdapter(ConnectorAdapter):
    provider = "x_twitter"

    def discover(self, config: dict[str, object]) -> list[ConnectorItem]:
        manual = _manual_items_from_config("x_twitter", config)
        if manual:
            return manual
        bearer = os.getenv("NBLANE_X_BEARER_TOKEN", "").strip()
        query = _clean_text(config.get("query"))
        if not bearer or not query:
            return []
        encoded = urllib.parse.urlencode(
            {
                "query": query,
                "max_results": str(max(10, min(int(config.get("limit") or 10), 100))),
                "tweet.fields": "created_at,author_id,entities",
            }
        )
        payload = json.loads(
            _http_get(
                f"https://api.x.com/2/tweets/search/recent?{encoded}",
                headers={"Authorization": f"Bearer {bearer}"},
            ).decode("utf-8")
        )
        return parse_x_twitter_payload(payload)


class XiaohongshuAdapter(ConnectorAdapter):
    provider = "xiaohongshu"

    def discover(self, config: dict[str, object]) -> list[ConnectorItem]:
        return _manual_items_from_config("xiaohongshu", config)


ADAPTERS: dict[str, ConnectorAdapter] = {
    "arxiv": ArxivAdapter(),
    "semantic_scholar": SemanticScholarAdapter(),
    "github": GitHubAdapter(),
    "x_twitter": XTwitterAdapter(),
    "xiaohongshu": XiaohongshuAdapter(),
}


def _canonical_url(url: str) -> str:
    clean = _clean_text(url)
    if not clean:
        return ""
    parsed = urllib.parse.urlparse(clean)
    if not parsed.scheme or not parsed.netloc:
        return clean.rstrip("/")
    path = parsed.path.rstrip("/")
    return urllib.parse.urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", parsed.query, ""))


def parse_arxiv_feed(payload: bytes | str) -> list[ConnectorItem]:
    """Normalize an arXiv Atom feed payload."""
    text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    root = ET.fromstring(text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items: list[ConnectorItem] = []
    for entry in root.findall("atom:entry", ns):
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ns) or "").split())
        if not title:
            continue
        external_id = _clean_text(entry.findtext("atom:id", default="", namespaces=ns))
        url = external_id
        authors = [
            _clean_text(author.findtext("atom:name", default="", namespaces=ns))
            for author in entry.findall("atom:author", ns)
        ]
        authors = [author for author in authors if author]
        summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ns) or "").split())
        published = _clean_text(entry.findtext("atom:published", default="", namespaces=ns))[:10]
        tags = [
            _clean_text(category.attrib.get("term"))
            for category in entry.findall("atom:category", ns)
        ]
        items.append(
            ConnectorItem(
                provider="arxiv",
                title=title,
                url=url,
                kind="paper",
                external_id=external_id,
                authors=authors,
                published=published,
                summary=summary,
                tags=[tag for tag in tags if tag],
                metadata={"source_surface": "arxiv"},
            )
        )
    return items


def parse_semantic_scholar_payload(payload: dict[str, Any]) -> list[ConnectorItem]:
    """Normalize Semantic Scholar search or paper payload."""
    raw_items = payload.get("data") if isinstance(payload.get("data"), list) else [payload]
    items: list[ConnectorItem] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        title = _clean_text(item.get("title"))
        if not title:
            continue
        paper_id = _clean_text(item.get("paperId"))
        external_ids = item.get("externalIds") if isinstance(item.get("externalIds"), dict) else {}
        url = _clean_text(item.get("url"))
        authors = [
            _clean_text(author.get("name"))
            for author in item.get("authors") or []
            if isinstance(author, dict)
        ]
        published = _clean_text(item.get("publicationDate")) or _clean_text(item.get("year"))
        items.append(
            ConnectorItem(
                provider="semantic_scholar",
                title=title,
                url=url,
                kind="paper",
                external_id=paper_id,
                authors=[author for author in authors if author],
                published=published,
                summary=_clean_text(item.get("abstract")),
                tags=["semantic-scholar"],
                metadata={
                    "source_surface": "semantic_scholar",
                    "paper_id": paper_id,
                    "external_ids": _sanitize_mapping(external_ids),
                },
            )
        )
    return items


def parse_github_payload(payload: dict[str, Any]) -> list[ConnectorItem]:
    """Normalize GitHub repo or repository search payload."""
    raw_items = payload.get("items") if isinstance(payload.get("items"), list) else [payload]
    items: list[ConnectorItem] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        full_name = _clean_text(item.get("full_name"))
        title = full_name or _clean_text(item.get("name"))
        if not title:
            continue
        topics = _clean_list(item.get("topics"))
        language = _clean_text(item.get("language"))
        tags = [tag for tag in [language, *topics, "github"] if tag]
        items.append(
            ConnectorItem(
                provider="github",
                title=title,
                url=_clean_text(item.get("html_url")),
                kind="repo",
                external_id=str(item.get("id") or full_name),
                authors=[_clean_text((item.get("owner") or {}).get("login"))]
                if isinstance(item.get("owner"), dict)
                else [],
                published=_clean_text(item.get("created_at"))[:10],
                summary=_clean_text(item.get("description")),
                tags=tags,
                metadata={
                    "source_surface": "github",
                    "repo": full_name,
                    "stars": item.get("stargazers_count"),
                    "forks": item.get("forks_count"),
                    "updated_at": item.get("updated_at"),
                },
            )
        )
    return items


def parse_x_twitter_payload(payload: dict[str, Any]) -> list[ConnectorItem]:
    """Normalize an X API recent-search payload."""
    items: list[ConnectorItem] = []
    for item in payload.get("data") or []:
        if not isinstance(item, dict):
            continue
        tweet_id = _clean_text(item.get("id"))
        text = _clean_text(item.get("text"))
        if not tweet_id or not text:
            continue
        author_id = _clean_text(item.get("author_id"))
        url = f"https://x.com/i/web/status/{tweet_id}"
        items.append(
            ConnectorItem(
                provider="x_twitter",
                title=text[:96],
                url=url,
                kind="web",
                external_id=tweet_id,
                authors=[author_id] if author_id else [],
                published=_clean_text(item.get("created_at"))[:10],
                summary=text,
                tags=["x-twitter"],
                metadata={"source_surface": "x_twitter", "tweet_id": tweet_id},
            )
        )
    return items


def _manual_items_from_config(provider: str, config: dict[str, object]) -> list[ConnectorItem]:
    raw = config.get("manual_items") or config.get("items")
    rows: list[dict[str, object]] = []
    if isinstance(raw, list):
        rows = [item for item in raw if isinstance(item, dict)]
    elif isinstance(raw, str) and raw.strip():
        stripped = raw.strip()
        if stripped.startswith("["):
            parsed = json.loads(stripped)
            rows = [item for item in parsed if isinstance(item, dict)] if isinstance(parsed, list) else []
        else:
            reader = csv.DictReader(stripped.splitlines())
            rows = [dict(row) for row in reader]
    items: list[ConnectorItem] = []
    for row in rows:
        title = _clean_text(row.get("title") or row.get("text") or row.get("summary"))
        url = _clean_text(row.get("url") or row.get("link"))
        if not title and url:
            title = url
        if not title:
            continue
        items.append(
            ConnectorItem(
                provider=provider,
                title=title,
                url=url,
                kind=_clean_text(row.get("kind")) or "web",
                external_id=_clean_text(row.get("external_id") or row.get("id") or url),
                authors=_clean_list(row.get("authors") or row.get("author")),
                published=_clean_text(row.get("published") or row.get("date")),
                summary=_clean_text(row.get("summary") or row.get("text")),
                tags=_clean_list(row.get("tags")) or [provider],
                metadata={"source_surface": provider, "manual_import": True},
            )
        )
    return items


def load_connectors(profile: str | Path) -> dict[str, Any]:
    """Load ``research/connectors.yaml`` with normalized defaults."""
    path = _connectors_path(profile)
    raw = _load_yaml_dict(path) or {}
    rows = []
    for item in raw.get("connectors") or []:
        if not isinstance(item, dict):
            continue
        provider = _clean_text(item.get("provider"))
        if provider not in CONNECTOR_PROVIDERS:
            continue
        options = _sanitize_mapping(item.get("options"))
        rate_limit = _sanitize_mapping(item.get("rate_limit"))
        rows.append(
            {
                "id": _clean_text(item.get("id")) or _connector_id(provider, _clean_text(item.get("query"))),
                "provider": provider,
                "enabled": _clean_bool(item.get("enabled"), True),
                "query": _clean_text(item.get("query")),
                "privacy_default": _clean_text(item.get("privacy_default")) or "private",
                "status": _clean_text(item.get("status")) or "idle",
                "last_run": _clean_text(item.get("last_run")),
                "cursor": _clean_text(item.get("cursor")),
                "rate_limit": rate_limit,
                "options": options,
                "last_result": _sanitize_mapping(item.get("last_result")),
            }
        )
    return {
        "schema_version": _clean_text(raw.get("schema_version")) or CONNECTOR_SCHEMA_VERSION,
        "profile": _clean_text(raw.get("profile")) or _profile_name(profile),
        "updated": _clean_text(raw.get("updated")),
        "connectors": rows,
    }


def save_connectors(profile: str | Path, data: dict[str, Any]) -> Path:
    """Persist connector configs without secrets."""
    profile_name = _profile_name(profile)
    rows = []
    for item in data.get("connectors") or []:
        if not isinstance(item, dict):
            continue
        clean = _sanitize_mapping(item)
        provider = _clean_text(clean.get("provider"))
        if provider not in CONNECTOR_PROVIDERS:
            continue
        clean["id"] = _clean_text(clean.get("id")) or _connector_id(provider, _clean_text(clean.get("query")))
        clean["provider"] = provider
        clean["enabled"] = _clean_bool(clean.get("enabled"), True)
        clean["privacy_default"] = _clean_text(clean.get("privacy_default")) or "private"
        rows.append(clean)
    path = _connectors_path(profile)
    payload = {
        "schema_version": CONNECTOR_SCHEMA_VERSION,
        "profile": profile_name,
        "updated": _today(),
        "connectors": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        path,
        "# Research connector configs. Secrets must stay outside this file.\n\n"
        + yaml.dump(payload, allow_unicode=True, default_flow_style=False, sort_keys=False),
    )
    git_backup.record_change([path], action=f"update {profile_name}/research/connectors.yaml")
    return path


def upsert_connector(
    profile: str | Path,
    *,
    provider: str,
    query: str = "",
    connector_id: str = "",
    enabled: bool = True,
    privacy_default: str = "private",
    options: dict[str, object] | None = None,
    rate_limit: dict[str, object] | None = None,
) -> dict[str, object]:
    """Create or update one connector config."""
    clean_provider = _clean_text(provider)
    if clean_provider not in CONNECTOR_PROVIDERS:
        raise ValueError(f"Unknown research connector provider: {provider}")
    book = load_connectors(profile)
    rows = list(book.get("connectors") or [])
    clean_id = _clean_text(connector_id) or _connector_id(clean_provider, query)
    row = {
        "id": clean_id,
        "provider": clean_provider,
        "enabled": bool(enabled),
        "query": _clean_text(query),
        "privacy_default": privacy_default if privacy_default in {"private", "public"} else "private",
        "status": "idle",
        "last_run": "",
        "cursor": "",
        "rate_limit": _sanitize_mapping(rate_limit),
        "options": _sanitize_mapping(options),
        "last_result": {},
    }
    for index, existing in enumerate(rows):
        if _clean_text(existing.get("id")) == clean_id:
            merged = copy.deepcopy(existing)
            merged.update(row)
            rows[index] = merged
            break
    else:
        rows.append(row)
    book["connectors"] = rows
    save_connectors(profile, book)
    return row


def _source_fingerprints(inbox: ResearchSourceInbox) -> set[str]:
    keys: set[str] = set()
    for source in inbox.sources:
        metadata = source.metadata if isinstance(source.metadata, dict) else {}
        provider = _clean_text(metadata.get("provider"))
        external_id = _clean_text(metadata.get("external_id"))
        canonical = _canonical_url(source.url)
        title_hash = hashlib.sha1(source.title.lower().strip().encode("utf-8")).hexdigest()[:12]
        keys.add("|".join([provider, external_id, canonical, title_hash]))
        if canonical:
            keys.add(canonical)
    return keys


def _adapter_config(row: dict[str, object]) -> dict[str, object]:
    options = row.get("options") if isinstance(row.get("options"), dict) else {}
    merged = {**copy.deepcopy(options), "query": _clean_text(row.get("query"))}
    for key in ("limit", "repo", "paper_id", "manual_items", "items"):
        if key in row:
            merged[key] = row[key]
    return _sanitize_mapping(merged)


def _respect_rate_limit(row: dict[str, object]) -> None:
    rate_limit = row.get("rate_limit") if isinstance(row.get("rate_limit"), dict) else {}
    min_interval = float(rate_limit.get("min_interval_seconds") or 0)
    if min_interval <= 0:
        return
    last_run = _clean_text(row.get("last_run"))
    if not last_run:
        return
    try:
        elapsed = time.time() - datetime.fromisoformat(last_run).timestamp()
    except ValueError:
        return
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)


def sync_connector(
    profile: str | Path,
    connector_id: str,
    *,
    dry_run: bool = False,
) -> ConnectorSyncResult:
    """Run one connector, optionally importing normalized sources."""
    profile_name = _profile_name(profile)
    book = load_connectors(profile)
    rows = list(book.get("connectors") or [])
    row = next((item for item in rows if _clean_text(item.get("id")) == connector_id), None)
    if row is None:
        raise ValueError(f"Unknown research connector: {connector_id}")
    provider = _clean_text(row.get("provider"))
    result = ConnectorSyncResult(
        profile=profile_name,
        connector_id=connector_id,
        provider=provider,
        dry_run=dry_run,
    )
    if not _clean_bool(row.get("enabled"), True):
        result.warnings.append("Connector is disabled.")
        return result
    adapter = ADAPTERS.get(provider)
    if adapter is None:
        raise ValueError(f"Unknown connector provider: {provider}")
    config = _adapter_config(row)
    if provider not in AUTO_PROVIDERS and provider == "xiaohongshu":
        result.warnings.append("Xiaohongshu automatic sync is disabled; use manual_items import only.")
    if (
        provider == "x_twitter"
        and not os.getenv("NBLANE_X_BEARER_TOKEN")
        and not (config.get("manual_items") or config.get("items"))
    ):
        result.warnings.append("X automatic sync requires NBLANE_X_BEARER_TOKEN or manual_items.")
    try:
        _respect_rate_limit(row)
        items = adapter.discover(config)
        result.discovered = len(items)
        result.items = [item.to_dict() for item in items]
        inbox = load_research_sources(_profile_root(profile))
        existing = _source_fingerprints(inbox)
        privacy = _clean_text(row.get("privacy_default")) or "private"
        for item in items:
            fingerprint = item.fingerprint()
            canonical = _canonical_url(item.url)
            if fingerprint in existing or (canonical and canonical in existing):
                result.skipped += 1
                continue
            if dry_run:
                result.imported += 1
                continue
            source = add_research_source(
                inbox,
                **item.to_source_kwargs(privacy_default=privacy),
            )
            result.imported += 1
            result.imported_source_ids.append(source.id)
            existing.add(fingerprint)
            if canonical:
                existing.add(canonical)
        if not dry_run and result.imported:
            save_research_sources(_profile_root(profile), inbox)
        row["status"] = "ok"
        row["last_run"] = _now()
        row["last_result"] = {
            "discovered": result.discovered,
            "imported": result.imported,
            "skipped": result.skipped,
            "warnings": list(result.warnings),
        }
    except Exception as exc:
        result.error = str(exc)
        row["status"] = "failed"
        row["last_run"] = _now()
        row["last_result"] = {
            "discovered": result.discovered,
            "imported": result.imported,
            "skipped": result.skipped,
            "warnings": list(result.warnings),
            "error": result.error,
        }
        if not dry_run:
            append_activity_item(
                profile_name,
                {
                    "kind": "writeback",
                    "candidate_type": "connector_sync",
                    "source_page": "Research",
                    "source_ref": connector_id,
                    "target_owner": "research",
                    "status": "failed",
                    "title": f"Connector sync failed: {connector_id}",
                    "summary": result.error,
                    "error": result.error,
                    "refs": {
                        "files": [
                            str(_connectors_path(profile)),
                            str(_profile_root(profile) / RESEARCH_DIRNAME / RESEARCH_SOURCES_FILENAME),
                        ]
                    },
                },
            )
    finally:
        if not dry_run:
            book["connectors"] = rows
            save_connectors(profile, book)
    return result


def sync_connectors(
    profile: str | Path,
    *,
    provider: str = "",
    dry_run: bool = False,
) -> list[ConnectorSyncResult]:
    """Run all enabled connectors, optionally filtered by provider."""
    book = load_connectors(profile)
    results: list[ConnectorSyncResult] = []
    for row in book.get("connectors") or []:
        if provider and _clean_text(row.get("provider")) != provider:
            continue
        if not _clean_bool(row.get("enabled"), True):
            continue
        results.append(sync_connector(profile, _clean_text(row.get("id")), dry_run=dry_run))
    return results


__all__ = [
    "AUTO_PROVIDERS",
    "CONNECTORS_FILENAME",
    "CONNECTOR_PROVIDERS",
    "ConnectorAdapter",
    "ConnectorItem",
    "ConnectorSyncResult",
    "load_connectors",
    "parse_arxiv_feed",
    "parse_github_payload",
    "parse_semantic_scholar_payload",
    "parse_x_twitter_payload",
    "save_connectors",
    "sync_connector",
    "sync_connectors",
    "upsert_connector",
]
