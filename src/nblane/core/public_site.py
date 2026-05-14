"""Public personal site generation for nblane profiles."""

from __future__ import annotations

import html
import base64
import hashlib
import io
import json
import mimetypes
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

import yaml

from schemas.blocknote_doc import Document as BlockNoteDocument
from schemas.blocknote_doc import coerce_blocks, document_to_dict
from nblane.core import git_backup, llm, visual_generation
from nblane.core.ai_blog_prompts import get_prompt
from nblane.core.claims import accepted_claim_index, claim_index
from nblane.core.file_write import atomic_write_text
from nblane.core.kanban_io import KANBAN_DONE, parse_kanban
from nblane.core.paths import REPO_ROOT
from nblane.core.profile_io import profile_dir

PUBLIC_PROFILE_FILENAME = "public-profile.yaml"
RESUME_SOURCE_FILENAME = "resume-source.yaml"
PROJECTS_FILENAME = "projects.yaml"
OUTPUTS_FILENAME = "outputs.yaml"
BLOG_TAXONOMY_FILENAME = "blog-taxonomy.yaml"
PUBLIC_LIBRARY_FILENAME = "public-library.yaml"
BLOG_DIRNAME = "blog"
MEDIA_DIRNAME = "media"
RESUMES_DIRNAME = "resumes"
GENERATED_RESUME_DIRNAME = "generated"

PUBLIC_VISIBILITIES = {"private", "public"}
PUBLISH_STATUSES = {"draft", "published", "archived"}
PUBLIC_LIBRARY_TYPES = {"root", "folder", "post", "media"}
PUBLIC_LIBRARY_STATUSES = {"active", "trashed"}
LOCAL_MEDIA_FIELDS = ("avatar", "cover")
BLOG_INSERT_MARKER = "<!-- nblane:insert -->"
BLOG_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
BLOG_VIDEO_EXTENSIONS = {"mp4", "webm"}
BLOG_DIRECT_VIDEO_EXTENSIONS = {"mp4", "webm", "ogg"}
BLOG_IMAGE_MAX_BYTES = 10 * 1024 * 1024
BLOG_VIDEO_MAX_BYTES = 25 * 1024 * 1024
BLOG_PREVIEW_VIDEO_INLINE_MAX_BYTES = 2 * 1024 * 1024
BLOG_IMAGE_PREVIEW_MAX_EDGE = 640
BLOG_IMAGE_PREVIEW_QUALITY = 55
BLOG_BROWSER_VIDEO_CODECS = {
    "mp4": {"h264"},
    "webm": {"vp8", "vp9", "av1"},
}
SAFE_HREF_SCHEMES = {"http", "https", "mailto"}
SAFE_SRC_SCHEMES = {"http", "https"}
_FENCED_CODE_RE = re.compile(r"(?ms)^(```|~~~).*?^\1\s*$")
_URL_CONTROL_RE = re.compile(r"[\x00-\x20\x7f]+")
_URL_SCHEME_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.-]*):")
_URL_ATTR_RE = re.compile(
    r"(?P<prefix>\s)(?P<attr>href|src)\s*=\s*"
    r"(?:(?P<quote>[\"'])(?P<quoted>.*?)(?P=quote)|"
    r"(?P<bare>[^\s>]+))",
    re.IGNORECASE | re.DOTALL,
)
_VISUAL_BLOCK_COMMENT_RE = re.compile(
    r"<!--\s*nblane:visual_block(?:\s+(?P<payload>\{[^\r\n]*\}))?\s*-->",
    re.IGNORECASE,
)
_AI_LOADING_COMMENT_RE = re.compile(
    r"<!--\s*nblane:ai_loading(?:\s+(?P<payload>\{[^\r\n]*\}))?\s*-->",
    re.IGNORECASE,
)
_MATH_BLOCK_COMMENT_RE = re.compile(
    r"<!--\s*nblane:math_block(?:\s+(?P<payload>\{[^\r\n]*\}))?\s*-->",
    re.IGNORECASE,
)
_MARKDOWN_LINK_RE = re.compile(
    r"(?<!!)\[[^\]]+\]\(\s*(?P<href><[^>]+>|[^)\s]+)"
    r"(?:\s+[\"'][^\"']*[\"'])?\s*\)"
)
_DISPLAY_DOLLAR_MATH_BLOCK_RE = re.compile(
    r"(?ms)^[ \t]*\$\$[ \t]*(?:\n(?P<body_multi>.*?)\n[ \t]*|"
    r"(?P<body_single>.+?))[ \t]*\$\$[ \t]*$"
)
_DISPLAY_BRACKET_MATH_BLOCK_RE = re.compile(
    r"(?ms)^[ \t]*\\\[[ \t]*(?:\n(?P<body_multi>.*?)\n[ \t]*|"
    r"(?P<body_single>.+?))[ \t]*\\\][ \t]*$"
)
_DISPLAY_DOLLAR_MATH_RE = re.compile(r"(?<!\\)\$\$(?!\$).+?(?<!\\)\$\$", re.S)
_DISPLAY_BRACKET_MATH_RE = re.compile(r"\\\[.+?\\\]", re.S)
_INLINE_DOLLAR_MATH_RE = re.compile(r"(?<!\\)\$(?![\s$])([^\n$]+?)(?<!\\)\$")
_INLINE_PAREN_MATH_RE = re.compile(r"\\\((.+?)\\\)")
_CODE_TOKEN = "NBLANE_CODE_BLOCK_{index}_TOKEN"
_MATH_BLOCK_TOKEN = "NBLANE_MATH_BLOCK_{index}_TOKEN"
_MATH_INLINE_TOKEN = "NBLANE_MATH_INLINE_{index}_TOKEN"
_MATHJAX_HEAD = r"""
  <script>
  window.MathJax = {
    tex: {
      inlineMath: [["$", "$"], ["\\(", "\\)"]],
      displayMath: [["$$", "$$"], ["\\[", "\\]"]],
      processEscapes: true
    },
    svg: { fontCache: "global" }
  };
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
"""
_MERMAID_HEAD = r"""
  <script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10.9.5/dist/mermaid.esm.min.mjs";
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "default"
  });
  window.addEventListener("DOMContentLoaded", () => {
    mermaid.run({ querySelector: ".mermaid" }).catch((error) => {
      console.error("Mermaid render failed", error);
    });
  });
  </script>
"""


class PublicSiteError(RuntimeError):
    """Raised when the public site cannot be validated or built."""


@dataclass
class PublicValidationResult:
    """Validation outcome for the profile public layer."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Return True when no validation errors were found."""
        return not self.errors

    def raise_for_errors(self) -> None:
        """Raise a compact exception if validation failed."""
        if self.errors:
            raise PublicSiteError("\n".join(self.errors))


@dataclass
class BlogPost:
    """A Markdown blog post with parsed front matter."""

    slug: str
    path: Path
    meta: dict
    body: str
    category_path: list[str] = field(default_factory=list)
    blocks_json: list[dict] = field(default_factory=list)
    sidecar_path: Path | None = None

    @property
    def status(self) -> str:
        """Return draft / published / archived."""
        return str(self.meta.get("status", "draft") or "draft")

    @property
    def title(self) -> str:
        """Return the public post title."""
        return str(self.meta.get("title", "") or self.slug)

    @property
    def summary(self) -> str:
        """Return the public post summary."""
        return str(self.meta.get("summary", "") or "")

    @property
    def date(self) -> str:
        """Return the post date as a display string."""
        return str(self.meta.get("date", "") or "")

    @property
    def url_path(self) -> str:
        """Return the relative output URL path."""
        return f"blog/{self.slug}/"

    @property
    def route(self) -> str:
        """Return the unique route for this post.

        For legacy flat posts this equals the leaf slug. For categorized posts
        it includes slash-separated category segments.
        """
        return self.slug

    @property
    def leaf_slug(self) -> str:
        """Return the final route segment / Markdown filename stem."""
        return self.slug.rstrip("/").split("/")[-1] or self.slug


@dataclass
class PublicLibraryNode:
    """One node in the public-site management tree."""

    id: str
    type: str
    title: str
    parent_id: str = ""
    order: int = 0
    visibility: str = "private"
    status: str = "active"
    ref: str = ""
    owned: bool = False
    trashed_at: str = ""
    trashed_from_parent_id: str = ""
    trashed_from_order: int | None = None
    previous_post_status: str = ""

    @property
    def active(self) -> bool:
        return self.status == "active"

    @property
    def trashed(self) -> bool:
        return self.status == "trashed"

    def to_dict(self) -> dict:
        data: dict[str, object] = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "parent_id": self.parent_id,
            "order": self.order,
            "visibility": self.visibility,
            "status": self.status,
        }
        if self.ref:
            data["ref"] = self.ref
        if self.owned:
            data["owned"] = True
        if self.trashed_at:
            data["trashed_at"] = self.trashed_at
        if self.trashed_from_parent_id:
            data["trashed_from_parent_id"] = self.trashed_from_parent_id
        if self.trashed_from_order is not None:
            data["trashed_from_order"] = self.trashed_from_order
        if self.previous_post_status:
            data["previous_post_status"] = self.previous_post_status
        return data


@dataclass
class PublicLibrary:
    """Public-site file tree stored in ``public-library.yaml``."""

    profile: str
    version: int = 1
    nodes: list[PublicLibraryNode] = field(default_factory=list)


@dataclass
class PublicLibraryIndex:
    """Lookup indexes for a public library."""

    by_id: dict[str, PublicLibraryNode] = field(default_factory=dict)
    by_ref: dict[str, PublicLibraryNode] = field(default_factory=dict)
    children_by_parent: dict[str, list[PublicLibraryNode]] = field(default_factory=dict)


@dataclass
class PublicLibraryOperationResult:
    """Result for public library mutations."""

    node: PublicLibraryNode | None = None
    changed_paths: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize mutation results for CLI/Streamlit event handlers."""
        data: dict[str, object] = {}
        if self.node is not None:
            data.update(self.node.to_dict())
            if self.node.type == "post" and self.node.ref:
                route = _library_blog_route(self.node.ref)
                data["route"] = route
                data["slug"] = route
        data["node"] = self.node.to_dict() if self.node is not None else {}
        data["changed_paths"] = [str(path) for path in self.changed_paths]
        data["warnings"] = list(self.warnings)
        return data


@dataclass
class PublicBuildResult:
    """Result returned by the static site builder."""

    output_dir: Path
    pages: list[Path]


@dataclass
class PublicSiteRenderResult:
    """In-memory public site render result."""

    pages: dict[str, str]
    page_titles: dict[str, str]
    css: str
    media_refs: list[str] = field(default_factory=list)
    resume_markdown: str = ""
    sitemap_exclude: set[str] = field(default_factory=set)


@dataclass
class PublicSitePreviewResult:
    """Preview-ready public site pages with inline assets."""

    pages: dict[str, str]
    page_titles: dict[str, str]
    warnings: list[str] = field(default_factory=list)


@dataclass
class BlogMediaResult:
    """Result of adding one media file to a blog post."""

    path: Path
    relative_path: str
    snippet: str
    post_path: Path | None = None
    changed_paths: list[Path] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for CLI output."""
        return {
            "path": str(self.path),
            "relative_path": self.relative_path,
            "snippet": self.snippet,
            "post_path": str(self.post_path) if self.post_path else "",
            "changed_paths": [str(path) for path in self.changed_paths],
        }


@dataclass
class BlogDraftCandidate:
    """Draft blog content that has not been written to disk yet."""

    title: str
    body: str
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    related_evidence: list[str] = field(default_factory=list)
    related_kanban: list[str] = field(default_factory=list)
    related_claims: list[str] = field(default_factory=list)
    related_sources: list[str] = field(default_factory=list)
    related_research_claims: list[str] = field(default_factory=list)
    related_citations: list[str] = field(default_factory=list)
    cover_prompt: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for UI or CLI previews."""
        return {
            "title": self.title,
            "summary": self.summary,
            "tags": list(self.tags),
            "related_evidence": list(self.related_evidence),
            "related_kanban": list(self.related_kanban),
            "related_claims": list(self.related_claims),
            "related_sources": list(self.related_sources),
            "related_research_claims": list(self.related_research_claims),
            "related_citations": list(self.related_citations),
            "cover_prompt": self.cover_prompt,
            "warnings": list(self.warnings),
            "body": self.body,
        }


@dataclass
class ResumeBulletCandidate:
    """Resume bullet candidate generated from accepted claims."""

    text: str
    related_claims: list[str] = field(default_factory=list)
    related_evidence: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for UI previews."""
        return {
            "text": self.text,
            "related_claims": list(self.related_claims),
            "related_evidence": list(self.related_evidence),
            "warnings": list(self.warnings),
        }


@dataclass
class ProjectUpdateCandidate:
    """Project update candidate generated from accepted claims."""

    title: str
    body: str
    related_claims: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for UI previews."""
        return {
            "title": self.title,
            "body": self.body,
            "related_claims": list(self.related_claims),
            "evidence_refs": list(self.evidence_refs),
            "warnings": list(self.warnings),
        }


def _profile_path(name: str) -> Path:
    path = profile_dir(name)
    if not path.exists():
        raise FileNotFoundError(f"Profile '{name}' does not exist: {path}")
    return path


def _dump_yaml(data: dict) -> str:
    return yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )


def _read_yaml_mapping(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_yaml(data), encoding="utf-8")


def _default_public_profile(name: str) -> dict:
    return {
        "profile": name,
        "visibility": "private",
        "public_name": name,
        "english_name": "",
        "headline": "",
        "avatar": "",
        "bio_short": "",
        "contacts": {
            "email": "",
            "wechat": "",
            "github": "",
            "linkedin": "",
            "google_scholar": "",
            "zhihu": "",
            "website": "",
        },
        "featured": {
            "projects": [],
            "outputs": [],
            "posts": [],
        },
    }


def _default_resume_source(name: str) -> dict:
    return {
        "profile": name,
        "visibility": "private",
        "basics": {
            "name": name,
            "title": "",
            "location": "",
            "email": "",
            "website": "",
        },
        "summary": "",
        "skills": [],
        "experiences": [],
        "projects": [],
        "outputs": [],
        "education": [],
    }


def _default_projects() -> dict:
    return {"projects": []}


def _default_outputs() -> dict:
    return {"outputs": []}


def _default_public_library(name: str) -> dict:
    return {
        "version": 1,
        "profile": name,
        "nodes": [
            {
                "id": "root",
                "type": "root",
                "title": "Public Library",
                "parent_id": "",
                "order": 0,
                "visibility": "private",
                "status": "active",
            }
        ],
    }


def init_public_layer(name: str) -> list[Path]:
    """Create missing public-layer files and directories.

    Existing files are never overwritten. The function is intentionally
    idempotent so it can be used by both CLI and Streamlit pages.
    """
    root = _profile_path(name)
    created: list[Path] = []

    defaults = {
        PUBLIC_PROFILE_FILENAME: _default_public_profile(name),
        RESUME_SOURCE_FILENAME: _default_resume_source(name),
        PROJECTS_FILENAME: _default_projects(),
        OUTPUTS_FILENAME: _default_outputs(),
        PUBLIC_LIBRARY_FILENAME: _default_public_library(name),
    }
    for filename, data in defaults.items():
        path = root / filename
        if path.exists():
            continue
        _write_yaml(path, data)
        created.append(path)

    for rel in (
        f"{BLOG_DIRNAME}/.gitkeep",
        f"{MEDIA_DIRNAME}/.gitkeep",
        f"{RESUMES_DIRNAME}/{GENERATED_RESUME_DIRNAME}/.gitkeep",
    ):
        path = root / rel
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        created.append(path)

    if created:
        git_backup.record_change(
            created,
            action=f"initialize {name} public layer",
        )
    return created


def load_public_profile(name: str) -> dict:
    """Load public-profile.yaml as a mapping."""
    return _read_yaml_mapping(
        _profile_path(name) / PUBLIC_PROFILE_FILENAME
    )


def load_resume_source(name: str) -> dict:
    """Load resume-source.yaml as a mapping."""
    return _read_yaml_mapping(
        _profile_path(name) / RESUME_SOURCE_FILENAME
    )


def load_projects(name: str) -> list[dict]:
    """Load project rows from projects.yaml."""
    raw = _read_yaml_mapping(_profile_path(name) / PROJECTS_FILENAME)
    projects = raw.get("projects") or []
    return [p for p in projects if isinstance(p, dict)]


def load_outputs(name: str) -> list[dict]:
    """Load output rows from outputs.yaml."""
    raw = _read_yaml_mapping(_profile_path(name) / OUTPUTS_FILENAME)
    outputs = raw.get("outputs") or []
    return [o for o in outputs if isinstance(o, dict)]


def load_blog_taxonomy(name: str) -> dict:
    """Load optional blog taxonomy configuration."""
    return _read_yaml_mapping(_profile_path(name) / BLOG_TAXONOMY_FILENAME)


def _public_library_path(name: str) -> Path:
    return _profile_path(name) / PUBLIC_LIBRARY_FILENAME


def _blog_markdown_path_for_route(name: str, route: str) -> Path:
    return _profile_path(name) / BLOG_DIRNAME / f"{_slugify_route(route)}.md"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_library_parent_id(value: object) -> str:
    parent_id = str(value or "").strip()
    return "" if parent_id in {"", "none", "None", "null"} else parent_id


def _clean_library_ref(value: object) -> str:
    return str(value or "").strip().replace("\\", "/").strip("/")


def _library_blog_ref(route: str) -> str:
    return f"{BLOG_DIRNAME}/{_slugify_route(route)}.md"


def _library_blog_route(ref_or_route: str) -> str:
    clean = _clean_library_ref(ref_or_route)
    prefix = f"{BLOG_DIRNAME}/"
    if clean.startswith(prefix):
        clean = clean[len(prefix) :]
    if clean.endswith(".md"):
        clean = clean[:-3]
    if clean.endswith(".blocknote.json"):
        clean = clean[: -len(".blocknote.json")]
    return _slugify_route(clean)


def _normalize_library_node(raw: object, index: int) -> PublicLibraryNode | None:
    if not isinstance(raw, dict):
        return None
    node_type = str(raw.get("type", raw.get("kind", "")) or "").strip().lower()
    if not node_type:
        node_type = "folder"
    raw_id = str(raw.get("id", "") or "").strip()
    ref = _clean_library_ref(raw.get("ref", raw.get("target", "")))
    title = str(raw.get("title", "") or "").strip()
    if node_type == "root":
        node_id = raw_id or "root"
        title = title or "Public Library"
    else:
        seed = ref or title or str(index)
        node_id = raw_id or f"{node_type}_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"
        title = title or Path(ref).stem or node_id
    try:
        order = int(raw.get("order", index * 10) or 0)
    except (TypeError, ValueError):
        order = index * 10
    visibility = str(raw.get("visibility", "private") or "private").strip().lower()
    status = str(raw.get("status", "active") or "active").strip().lower()
    trashed_order = raw.get("trashed_from_order")
    try:
        trashed_from_order = (
            int(trashed_order) if trashed_order is not None and str(trashed_order) != "" else None
        )
    except (TypeError, ValueError):
        trashed_from_order = None
    return PublicLibraryNode(
        id=node_id,
        type=node_type,
        title=title,
        parent_id=_clean_library_parent_id(raw.get("parent_id")),
        order=order,
        visibility=visibility,
        status=status,
        ref=ref,
        owned=bool(raw.get("owned", False)),
        trashed_at=str(raw.get("trashed_at", "") or ""),
        trashed_from_parent_id=_clean_library_parent_id(
            raw.get("trashed_from_parent_id")
        ),
        trashed_from_order=trashed_from_order,
        previous_post_status=str(raw.get("previous_post_status", "") or ""),
    )


def _normalize_public_library(raw: dict, name: str) -> PublicLibrary:
    nodes_raw = raw.get("nodes") if isinstance(raw, dict) else []
    nodes: list[PublicLibraryNode] = []
    if isinstance(nodes_raw, list):
        for index, item in enumerate(nodes_raw):
            node = _normalize_library_node(item, index)
            if node is not None:
                nodes.append(node)
    if not any(node.id == "root" for node in nodes):
        nodes.insert(
            0,
            PublicLibraryNode(
                id="root",
                type="root",
                title="Public Library",
                parent_id="",
                order=0,
            ),
        )
    for node in nodes:
        if node.type == "root":
            node.id = "root"
            node.parent_id = ""
            node.status = "active"
    version = raw.get("version", 1) if isinstance(raw, dict) else 1
    try:
        clean_version = int(version)
    except (TypeError, ValueError):
        clean_version = 1
    profile = str(raw.get("profile", name) or name) if isinstance(raw, dict) else name
    return PublicLibrary(profile=profile, version=clean_version, nodes=nodes)


def _public_library_to_yaml(library: PublicLibrary) -> dict:
    nodes = sorted(
        library.nodes,
        key=lambda node: (
            0 if node.id == "root" else 1,
            node.parent_id,
            node.order,
            node.id,
        ),
    )
    return {
        "version": int(library.version or 1),
        "profile": library.profile,
        "nodes": [node.to_dict() for node in nodes],
    }


def load_public_library(name: str) -> PublicLibrary:
    """Load the optional public-site file tree."""
    path = _public_library_path(name)
    if not path.exists():
        return _normalize_public_library({}, name)
    return _normalize_public_library(_read_yaml_mapping(path), name)


def save_public_library(
    name: str,
    library: PublicLibrary,
    *,
    action: str = "",
) -> Path:
    """Persist ``public-library.yaml`` and record a git backup event."""
    path = _public_library_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    library.profile = name
    atomic_write_text(path, _dump_yaml(_public_library_to_yaml(library)))
    git_backup.record_change(
        [path],
        action=action or f"update {name}/{PUBLIC_LIBRARY_FILENAME}",
    )
    return path


def index_public_library(library: PublicLibrary) -> PublicLibraryIndex:
    """Build lookup indexes for public library nodes."""
    by_id: dict[str, PublicLibraryNode] = {}
    by_ref: dict[str, PublicLibraryNode] = {}
    children_by_parent: dict[str, list[PublicLibraryNode]] = {}
    for node in library.nodes:
        by_id.setdefault(node.id, node)
        if node.ref:
            by_ref.setdefault(node.ref, node)
        children_by_parent.setdefault(node.parent_id, []).append(node)
    for children in children_by_parent.values():
        children.sort(key=lambda node: (node.order, node.title, node.id))
    return PublicLibraryIndex(
        by_id=by_id,
        by_ref=by_ref,
        children_by_parent=children_by_parent,
    )


def load_public_library_index(name: str) -> PublicLibraryIndex:
    """Load and index one profile public library."""
    return index_public_library(load_public_library(name))


def _public_library_has_real_nodes(library: PublicLibrary) -> bool:
    return any(node.id != "root" for node in library.nodes)


def _blog_route_for_library_node(node: PublicLibraryNode) -> str:
    if node.type != "post" or not node.ref:
        return ""
    return _library_blog_route(node.ref)


def public_library_node_for_blog(
    name: str,
    slug: str | Path,
    *,
    include_trashed: bool = False,
) -> PublicLibraryNode | None:
    """Return the library node for a blog route, if one exists."""
    try:
        route = _resolve_blog_route(name, slug)
    except Exception:
        route = _slugify_route(_blog_route_text(name, slug))
    ref = _library_blog_ref(route)
    for node in load_public_library(name).nodes:
        if node.type != "post" or node.ref != ref:
            continue
        if include_trashed or node.status != "trashed":
            return node
    return None


def is_blog_route_trashed(name: str, slug: str | Path) -> bool:
    """Return True when the blog route is in the library trash."""
    try:
        route = _resolve_blog_route(name, slug)
    except Exception:
        route = _slugify_route(_blog_route_text(name, slug))
    ref = _library_blog_ref(route)
    trashed = False
    for node in load_public_library(name).nodes:
        if node.type != "post" or node.ref != ref:
            continue
        if node.status != "trashed":
            return False
        trashed = True
    return trashed


def active_blog_routes_from_library(name: str) -> set[str] | None:
    """Return active blog routes from the library, or None when unused."""
    library = load_public_library(name)
    if not _public_library_has_real_nodes(library):
        return None
    routes = {
        _blog_route_for_library_node(node)
        for node in library.nodes
        if node.type == "post" and node.status != "trashed" and node.ref
    }
    return {route for route in routes if route}


def _library_node_path_titles(
    library: PublicLibrary,
    index: PublicLibraryIndex,
    node: PublicLibraryNode,
) -> list[str]:
    titles: list[str] = []
    seen: set[str] = set()
    parent_id = node.parent_id
    while parent_id and parent_id not in seen:
        seen.add(parent_id)
        parent = index.by_id.get(parent_id)
        if parent is None or parent.type == "root":
            break
        titles.append(parent.title)
        parent_id = parent.parent_id
    return list(reversed(titles))


def _blog_post_for_library_ref(name: str, ref: str) -> BlogPost | None:
    try:
        return load_blog_post(name, _library_blog_route(ref), include_trashed=True)
    except Exception:
        return None


def _public_library_node_payload(
    name: str,
    library: PublicLibrary,
    index: PublicLibraryIndex,
    node: PublicLibraryNode,
    *,
    include_trashed: bool,
) -> dict | None:
    if node.status == "trashed" and not include_trashed:
        return None
    payload = node.to_dict()
    payload["children"] = []
    if node.type == "post":
        route = _blog_route_for_library_node(node)
        payload["route"] = route
        payload["slug"] = route
        payload["leaf_slug"] = _blog_route_leaf(route)
        post = _blog_post_for_library_ref(name, node.ref)
        if post is not None:
            payload["title"] = node.title or post.title
            payload["date"] = post.date
            payload["post_status"] = post.status
            payload["summary"] = post.summary
            payload["category_path"] = list(post.category_path)
            payload["url_path"] = post.url_path
    elif node.type == "media":
        payload["relative_path"] = node.ref
    elif node.type == "folder":
        payload["path_titles"] = _library_node_path_titles(library, index, node)
    for child in index.children_by_parent.get(node.id, []):
        child_payload = _public_library_node_payload(
            name,
            library,
            index,
            child,
            include_trashed=include_trashed,
        )
        if child_payload is not None:
            payload["children"].append(child_payload)
    return payload


def _virtual_blog_node(post: BlogPost) -> dict:
    return {
        "id": "post:" + hashlib.sha1(post.route.encode("utf-8")).hexdigest()[:12],
        "type": "post",
        "title": post.title,
        "ref": _library_blog_ref(post.route),
        "parent_id": "root",
        "order": 0,
        "visibility": "public" if post.status == "published" else "private",
        "status": "active",
        "owned": False,
        "virtual": True,
        "route": post.route,
        "slug": post.route,
        "leaf_slug": post.leaf_slug,
        "category_path": list(post.category_path),
        "date": post.date,
        "post_status": post.status,
        "summary": post.summary,
        "url_path": post.url_path,
        "children": [],
    }


def list_public_library_tree(
    name: str,
    *,
    include_trashed: bool = False,
    include_posts: bool = True,
) -> list[dict]:
    """Return the public library tree payload for Streamlit/React."""
    library = load_public_library(name)
    index = index_public_library(library)
    root = index.by_id.get("root")
    if root is None:
        root = PublicLibraryNode(id="root", type="root", title="Public Library")
    root_payload = _public_library_node_payload(
        name,
        library,
        index,
        root,
        include_trashed=include_trashed,
    ) or {
        "id": "root",
        "type": "root",
        "title": "Public Library",
        "children": [],
    }
    if include_posts:
        known_refs = {
            node.ref
            for node in library.nodes
            if node.type == "post" and node.ref
        }
        for post in load_blog_posts(
            name,
            include_drafts=True,
            include_archived=True,
            include_trashed=include_trashed,
        ):
            ref = _library_blog_ref(post.route)
            if ref in known_refs:
                continue
            root_payload.setdefault("children", []).append(_virtual_blog_node(post))
    return [root_payload]


def public_library_trash_nodes(name: str) -> list[dict]:
    """Return trashed nodes as flat dictionaries for the editor UI."""
    library = load_public_library(name)
    index = index_public_library(library)
    rows: list[dict] = []
    trashed_ids = {node.id for node in library.nodes if node.status == "trashed"}
    for node in sorted(library.nodes, key=lambda item: (item.trashed_at, item.order, item.id)):
        if node.status != "trashed":
            continue
        if node.parent_id in trashed_ids:
            continue
        payload = _public_library_node_payload(
            name,
            library,
            index,
            node,
            include_trashed=True,
        )
        if payload is not None:
            rows.append(payload)
    return rows


def _library_next_order(library: PublicLibrary, parent_id: str) -> int:
    orders = [
        node.order
        for node in library.nodes
        if node.parent_id == parent_id and node.status != "trashed"
    ]
    return (max(orders) + 10) if orders else 10


def _library_unique_id(prefix: str, seed: str = "") -> str:
    clean = re.sub(r"[^a-z0-9_]+", "_", prefix.lower()).strip("_") or "node"
    digest_seed = seed or uuid.uuid4().hex
    digest = hashlib.sha1(digest_seed.encode("utf-8")).hexdigest()[:12]
    return f"{clean}_{digest}"


def _library_parent_or_root(library: PublicLibrary, parent_id: str | None) -> str:
    clean = _clean_library_parent_id(parent_id)
    if not clean:
        return "root"
    for node in library.nodes:
        if node.id != clean:
            continue
        if node.status == "trashed":
            raise PublicSiteError(f"Public library parent is in trash: {clean}")
        if node.type not in {"root", "folder", "post"}:
            raise PublicSiteError("Public library parent must be root, folder, or post.")
        return clean
    raise PublicSiteError(f"Unknown public library parent: {clean}")


def _library_require_node(
    library: PublicLibrary,
    node_id: str,
    *,
    include_trashed: bool = False,
) -> PublicLibraryNode:
    clean = str(node_id or "").strip()
    for node in library.nodes:
        if node.id != clean:
            continue
        if node.status == "trashed" and not include_trashed:
            raise PublicSiteError(f"Public library node is in trash: {clean}")
        return node
    raise PublicSiteError(f"Unknown public library node: {node_id}")


def create_public_library_folder(
    name: str,
    parent_id: str | None,
    title: str,
    *,
    visibility: str = "private",
) -> PublicLibraryOperationResult:
    """Create a folder node in the public library."""
    clean_title = str(title or "").strip()
    if not clean_title:
        raise PublicSiteError("Folder title is required.")
    library = load_public_library(name)
    parent = _library_parent_or_root(library, parent_id)
    node = PublicLibraryNode(
        id=_library_unique_id("folder", f"{parent}:{clean_title}:{uuid.uuid4().hex}"),
        type="folder",
        title=clean_title,
        parent_id=parent,
        order=_library_next_order(library, parent),
        visibility=visibility if visibility in PUBLIC_VISIBILITIES else "private",
    )
    library.nodes.append(node)
    path = save_public_library(name, library, action=f"create {name} public folder")
    return PublicLibraryOperationResult(node=node, changed_paths=[path])


def _library_add_post_node(
    name: str,
    *,
    library: PublicLibrary,
    parent_id: str | None,
    route: str,
    title: str,
    visibility: str = "public",
    owned: bool = True,
) -> PublicLibraryNode:
    ref = _library_blog_ref(route)
    for node in library.nodes:
        if node.type == "post" and node.ref == ref and node.status != "trashed":
            raise PublicSiteError(f"Blog post is already in the public library: {route}")
    parent = _library_parent_or_root(library, parent_id)
    node = PublicLibraryNode(
        id=_library_unique_id("post", ref),
        type="post",
        title=title or _blog_route_leaf(route),
        parent_id=parent,
        order=_library_next_order(library, parent),
        visibility=visibility if visibility in PUBLIC_VISIBILITIES else "private",
        ref=ref,
        owned=owned,
    )
    library.nodes.append(node)
    return node


def create_blog_draft_in_library(
    name: str,
    parent_id: str | None,
    title: str = "",
    body: str = "",
    summary: str = "",
    *,
    tags: list[str] | None = None,
    slug: str | None = None,
    visibility: str = "public",
) -> PublicLibraryOperationResult:
    """Create a blog draft and attach it to the public library tree."""
    clean_title = str(title or "").strip()
    if not clean_title:
        raise PublicSiteError("Blog title is required.")
    library = load_public_library(name)
    parent = _library_parent_or_root(library, parent_id)
    path = create_blog_draft(
        name,
        title=clean_title,
        body=body or BLOG_INSERT_MARKER + "\n\n",
        tags=tags,
        summary=summary,
        slug=slug,
        category_path=[],
        respect_taxonomy=False,
    )
    route = _blog_route_from_document_path(path)
    node = _library_add_post_node(
        name,
        library=library,
        parent_id=parent,
        route=route,
        title=clean_title,
        visibility=visibility,
        owned=True,
    )
    lib_path = save_public_library(
        name,
        library,
        action=f"attach {name} blog draft to public library",
    )
    git_backup.record_change(
        [path, _blog_sidecar_path_for_markdown(path), lib_path],
        action=f"create {name} library blog draft",
    )
    return PublicLibraryOperationResult(
        node=node,
        changed_paths=[path, _blog_sidecar_path_for_markdown(path), lib_path],
    )


def attach_existing_public_library_node(
    name: str,
    parent_id: str | None,
    ref: str,
    title: str = "",
    *,
    visibility: str = "",
) -> PublicLibraryOperationResult:
    """Attach an existing blog or media file to the public library."""
    clean_ref = _clean_library_ref(ref)
    if not clean_ref:
        raise PublicSiteError("Reference is required.")
    library = load_public_library(name)
    parent = _library_parent_or_root(library, parent_id)
    node_type = "media"
    normalized_ref = clean_ref
    if clean_ref.startswith(f"{BLOG_DIRNAME}/") or clean_ref.endswith(".md"):
        route = _resolve_blog_route(name, _library_blog_route(clean_ref))
        normalized_ref = _library_blog_ref(route)
        node_type = "post"
        path = _blog_markdown_path_for_route(name, route)
        if not path.exists() and not _blog_sidecar_path_for_markdown(path).exists():
            raise PublicSiteError(f"Unknown blog post: {clean_ref}")
    elif clean_ref.startswith(f"{MEDIA_DIRNAME}/"):
        target = _local_media_target(_profile_path(name), clean_ref)
        if target is None or not target.exists() or not target.is_file():
            raise PublicSiteError(f"Unknown media file: {clean_ref}")
    else:
        route = _resolve_blog_route(name, clean_ref)
        path = _blog_markdown_path_for_route(name, route)
        if path.exists() or _blog_sidecar_path_for_markdown(path).exists():
            normalized_ref = _library_blog_ref(route)
            node_type = "post"
        else:
            raise PublicSiteError(f"Unknown public library reference: {clean_ref}")
    for node in library.nodes:
        if node.ref == normalized_ref and node.status != "trashed":
            raise PublicSiteError(f"Reference is already attached: {normalized_ref}")
    clean_title = str(title or "").strip()
    if not clean_title and node_type == "post":
        post = _blog_post_for_library_ref(name, normalized_ref)
        clean_title = post.title if post is not None else _blog_route_leaf(normalized_ref)
    if not clean_title:
        clean_title = Path(normalized_ref).name
    node = PublicLibraryNode(
        id=_library_unique_id(node_type, normalized_ref),
        type=node_type,
        title=clean_title,
        parent_id=parent,
        order=_library_next_order(library, parent),
        visibility=(
            visibility
            if visibility in PUBLIC_VISIBILITIES
            else ("public" if node_type == "post" else "private")
        ),
        ref=normalized_ref,
        owned=False,
    )
    library.nodes.append(node)
    path = save_public_library(name, library, action=f"attach {name} public library node")
    return PublicLibraryOperationResult(node=node, changed_paths=[path])


def add_public_library_media_bytes(
    name: str,
    parent_id: str | None,
    *,
    data: bytes,
    filename: str,
    kind: str = "image",
    title: str = "",
) -> PublicLibraryOperationResult:
    """Store uploaded media and attach it to the public library."""
    if not data:
        raise PublicSiteError("Media data is empty.")
    library = load_public_library(name)
    parent = _library_parent_or_root(library, parent_id)
    parent_node = index_public_library(library).by_id.get(parent)
    if parent_node is not None and parent_node.type == "post" and parent_node.ref:
        route = _library_blog_route(parent_node.ref)
        result = _add_blog_media_data(
            name,
            route,
            data=data,
            filename=filename,
            kind=kind,
            append=False,
            cover=False,
        )
        rel = result.relative_path
        changed = list(result.changed_paths)
    else:
        media_dir = _profile_path(name) / MEDIA_DIRNAME / "library" / parent
        media_dir.mkdir(parents=True, exist_ok=True)
        safe_name = _safe_media_filename(filename, fallback="media")
        target = _unique_media_path(media_dir, safe_name, data)
        target.write_bytes(data)
        rel = _media_relative_path(name, target)
        changed = [target]
        git_backup.record_change(changed, action=f"upload {name} public library media")
    node = PublicLibraryNode(
        id=_library_unique_id("media", rel),
        type="media",
        title=str(title or "").strip() or Path(rel).name,
        parent_id=parent,
        order=_library_next_order(library, parent),
        visibility="private",
        ref=rel,
        owned=True,
    )
    library.nodes.append(node)
    lib_path = save_public_library(
        name,
        library,
        action=f"attach {name} media to public library",
    )
    return PublicLibraryOperationResult(node=node, changed_paths=[*changed, lib_path])


def rename_public_library_node(
    name: str,
    node_id: str,
    title: str,
) -> PublicLibraryOperationResult:
    """Rename one public library node title."""
    clean_title = str(title or "").strip()
    if not clean_title:
        raise PublicSiteError("Title is required.")
    library = load_public_library(name)
    node = _library_require_node(library, node_id, include_trashed=True)
    if node.type == "root":
        raise PublicSiteError("The root node cannot be renamed.")
    node.title = clean_title
    path = save_public_library(name, library, action=f"rename {name} public library node")
    return PublicLibraryOperationResult(node=node, changed_paths=[path])


def move_public_library_node(
    name: str,
    node_id: str,
    new_parent_id: str | None,
) -> PublicLibraryOperationResult:
    """Move a public library node without changing content URLs or files."""
    library = load_public_library(name)
    index = index_public_library(library)
    node = _library_require_node(library, node_id)
    if node.type == "root":
        raise PublicSiteError("The root node cannot be moved.")
    parent = _library_parent_or_root(library, new_parent_id)
    if parent == node.id:
        raise PublicSiteError("A node cannot be moved under itself.")
    cursor = index.by_id.get(parent)
    while cursor is not None and cursor.parent_id:
        if cursor.parent_id == node.id:
            raise PublicSiteError("A node cannot be moved under its descendant.")
        cursor = index.by_id.get(cursor.parent_id)
    node.parent_id = parent
    node.order = _library_next_order(library, parent)
    path = save_public_library(name, library, action=f"move {name} public library node")
    return PublicLibraryOperationResult(node=node, changed_paths=[path])


def _library_assert_not_descendant_parent(
    index: PublicLibraryIndex,
    *,
    node: PublicLibraryNode,
    parent_id: str,
) -> None:
    """Reject moving ``node`` under itself or under one of its descendants."""
    if parent_id == node.id:
        raise PublicSiteError("A node cannot be moved under itself.")
    cursor = index.by_id.get(parent_id)
    while cursor is not None and cursor.parent_id:
        if cursor.parent_id == node.id:
            raise PublicSiteError("A node cannot be moved under its descendant.")
        cursor = index.by_id.get(cursor.parent_id)


def position_public_library_node(
    name: str,
    node_id: str,
    *,
    parent_id: str | None = None,
    before_node_id: str = "",
    after_node_id: str = "",
) -> PublicLibraryOperationResult:
    """Move a node to a concrete parent/sibling position in one save.

    ``before_node_id`` and ``after_node_id`` are mutually exclusive. When one is
    supplied, the target node's parent decides the destination parent. Without a
    relative target, the node is appended under ``parent_id``.
    """
    before_id = str(before_node_id or "").strip()
    after_id = str(after_node_id or "").strip()
    if before_id and after_id:
        raise PublicSiteError("Use either before_node_id or after_node_id, not both.")

    library = load_public_library(name)
    index = index_public_library(library)
    node = _library_require_node(library, node_id)
    if node.type == "root":
        raise PublicSiteError("The root node cannot be moved.")

    target: PublicLibraryNode | None = None
    insert_after = False
    if before_id or after_id:
        target_id = before_id or after_id
        if target_id == node.id:
            raise PublicSiteError("A node cannot be positioned relative to itself.")
        target = _library_require_node(library, target_id)
        if target.type == "root":
            raise PublicSiteError("The root node cannot be used as a position target.")
        parent = target.parent_id or "root"
        insert_after = bool(after_id)
    else:
        parent = _library_parent_or_root(library, parent_id)

    _library_assert_not_descendant_parent(index, node=node, parent_id=parent)

    before_state = {
        item.id: (item.parent_id, item.order)
        for item in library.nodes
    }
    old_parent = node.parent_id
    siblings = [
        item
        for item in index.children_by_parent.get(parent, [])
        if item.status != "trashed" and item.id != node.id
    ]
    if target is not None:
        target_pos = next(
            (i for i, item in enumerate(siblings) if item.id == target.id),
            -1,
        )
        if target_pos < 0:
            raise PublicSiteError(f"Unknown public library position target: {target.id}")
        insert_pos = target_pos + 1 if insert_after else target_pos
    else:
        insert_pos = len(siblings)

    next_siblings = list(siblings)
    next_siblings.insert(insert_pos, node)
    node.parent_id = parent
    for index_pos, item in enumerate(next_siblings, start=1):
        item.order = index_pos * 10

    if old_parent != parent:
        old_siblings = [
            item
            for item in index.children_by_parent.get(old_parent, [])
            if item.status != "trashed" and item.id != node.id
        ]
        for index_pos, item in enumerate(old_siblings, start=1):
            item.order = index_pos * 10

    after_state = {
        item.id: (item.parent_id, item.order)
        for item in library.nodes
    }
    if before_state == after_state:
        return PublicLibraryOperationResult(node=node, changed_paths=[])

    path = save_public_library(
        name,
        library,
        action=f"position {name} public library node",
    )
    return PublicLibraryOperationResult(node=node, changed_paths=[path])


def reorder_public_library_node(
    name: str,
    node_id: str,
    direction: str,
) -> PublicLibraryOperationResult:
    """Move a node up or down among siblings."""
    library = load_public_library(name)
    index = index_public_library(library)
    node = _library_require_node(library, node_id)
    siblings = [
        item
        for item in index.children_by_parent.get(node.parent_id, [])
        if item.status != "trashed"
    ]
    pos = next((i for i, item in enumerate(siblings) if item.id == node.id), -1)
    if pos < 0:
        raise PublicSiteError(f"Unknown public library node: {node_id}")
    target_pos = pos - 1 if str(direction).lower() == "up" else pos + 1
    if target_pos < 0 or target_pos >= len(siblings):
        return PublicLibraryOperationResult(node=node, changed_paths=[])
    other = siblings[target_pos]
    node.order, other.order = other.order, node.order
    path = save_public_library(name, library, action=f"reorder {name} public library node")
    return PublicLibraryOperationResult(node=node, changed_paths=[path])


def _library_descendant_ids(
    index: PublicLibraryIndex,
    node_id: str,
) -> list[str]:
    ids: list[str] = []
    for child in index.children_by_parent.get(node_id, []):
        ids.append(child.id)
        ids.extend(_library_descendant_ids(index, child.id))
    return ids


def trash_public_library_node(
    name: str,
    node_id: str,
    *,
    recursive: bool = True,
) -> PublicLibraryOperationResult:
    """Move one node, and optionally its descendants, to library trash."""
    library = load_public_library(name)
    index = index_public_library(library)
    node = _library_require_node(library, node_id)
    if node.type == "root":
        raise PublicSiteError("The root node cannot be trashed.")
    descendant_ids = _library_descendant_ids(index, node.id)
    if descendant_ids and not recursive:
        raise PublicSiteError("Folder is not empty. Use recursive trash.")
    now = _utc_now()
    ids = [node.id, *descendant_ids]
    changed_nodes: list[PublicLibraryNode] = []
    for item in library.nodes:
        if item.id not in ids or item.status == "trashed":
            continue
        item.trashed_from_parent_id = item.parent_id
        item.trashed_from_order = item.order
        item.trashed_at = now
        if item.type == "post" and item.ref and not item.previous_post_status:
            post = _blog_post_for_library_ref(name, item.ref)
            if post is not None:
                item.previous_post_status = post.status
        item.status = "trashed"
        changed_nodes.append(item)
    path = save_public_library(name, library, action=f"trash {name} public library node")
    return PublicLibraryOperationResult(
        node=node,
        changed_paths=[path],
        warnings=[f"trashed {len(changed_nodes)} node(s)"],
    )


def restore_public_library_node(
    name: str,
    node_id: str,
) -> PublicLibraryOperationResult:
    """Restore one trashed public library node and its trashed descendants."""
    library = load_public_library(name)
    index = index_public_library(library)
    node = _library_require_node(library, node_id, include_trashed=True)
    if node.status != "trashed":
        return PublicLibraryOperationResult(node=node, changed_paths=[])
    ids = [node.id, *_library_descendant_ids(index, node.id)]
    warnings: list[str] = []
    active_ids = {
        item.id
        for item in library.nodes
        if item.status != "trashed"
    }
    used_orders = {
        (item.parent_id, item.order)
        for item in library.nodes
        if item.status != "trashed" and item.id not in ids
    }
    max_order_by_parent: dict[str, int] = {}
    for item in library.nodes:
        if item.status != "trashed" and item.id not in ids:
            max_order_by_parent[item.parent_id] = max(
                max_order_by_parent.get(item.parent_id, 0),
                item.order,
            )
    for item in library.nodes:
        if item.id not in ids:
            continue
        parent = item.trashed_from_parent_id or item.parent_id or "root"
        if parent not in active_ids and parent not in ids:
            warnings.append(f"{item.title}: restored under root because parent is unavailable")
            parent = "root"
        item.parent_id = parent
        if item.trashed_from_order is not None:
            item.order = item.trashed_from_order
        if (item.parent_id, item.order) in used_orders:
            item.order = max_order_by_parent.get(item.parent_id, 0) + 10
        used_orders.add((item.parent_id, item.order))
        max_order_by_parent[item.parent_id] = max(
            max_order_by_parent.get(item.parent_id, 0),
            item.order,
        )
        item.status = "active"
        item.trashed_at = ""
        item.trashed_from_parent_id = ""
        item.trashed_from_order = None
        item.previous_post_status = ""
    path = save_public_library(name, library, action=f"restore {name} public library node")
    return PublicLibraryOperationResult(node=node, changed_paths=[path], warnings=warnings)


def _active_library_refs(
    library: PublicLibrary,
    *,
    exclude_node_id: str = "",
) -> set[str]:
    return {
        node.ref
        for node in library.nodes
        if node.id != exclude_node_id and node.status != "trashed" and node.ref
    }


def _active_media_refs(name: str) -> set[str]:
    refs: set[str] = set()
    for post in load_blog_posts(
        name,
        include_drafts=True,
        include_archived=True,
        include_trashed=False,
    ):
        cover = _normalize_media_ref(
            _strip_markdown_url(str(post.meta.get("cover", "") or ""))
        ).lstrip("/")
        if cover:
            refs.add(cover)
        refs.update(_blog_body_media_refs(post.body))
    return refs


def purge_public_library_node(
    name: str,
    node_id: str,
    *,
    delete_files: bool = False,
) -> PublicLibraryOperationResult:
    """Permanently remove a trashed node from the library.

    Physical files are removed only when ``delete_files`` is True and no active
    library node still references the same content.
    """
    library = load_public_library(name)
    index = index_public_library(library)
    node = _library_require_node(library, node_id, include_trashed=True)
    if node.type == "root":
        raise PublicSiteError("The root node cannot be purged.")
    if node.status != "trashed":
        raise PublicSiteError("Only trashed nodes can be permanently deleted.")
    ids = [node.id, *_library_descendant_ids(index, node.id)]
    active_refs = _active_library_refs(library, exclude_node_id="")
    changed: list[Path] = []
    warnings: list[str] = []
    if delete_files:
        profile_root = _profile_path(name)
        media_refs = _active_media_refs(name)
        for item in list(library.nodes):
            if item.id not in ids or not item.ref:
                continue
            sibling_refs = active_refs - {item.ref}
            if item.type == "post":
                if item.ref in sibling_refs:
                    warnings.append(f"kept files for shared post ref {item.ref}")
                    continue
                route = _library_blog_route(item.ref)
                md_path = _blog_markdown_path_for_route(name, route)
                sidecar = _blog_sidecar_path_for_markdown(md_path)
                media_dir = profile_root / MEDIA_DIRNAME / BLOG_DIRNAME / _slugify_route(route)
                media_prefix = f"{MEDIA_DIRNAME}/{BLOG_DIRNAME}/{_slugify_route(route)}/"
                external_media_refs = sorted(
                    ref for ref in media_refs if ref.startswith(media_prefix)
                )
                if external_media_refs:
                    raise PublicSiteError(
                        "Blog media directory is still referenced by an active post: "
                        + ", ".join(external_media_refs)
                    )
                for path in (md_path, sidecar):
                    if path.exists():
                        path.unlink()
                        changed.append(path)
                if media_dir.exists() and media_dir.is_dir():
                    shutil.rmtree(media_dir)
                    changed.append(media_dir)
            elif item.type == "media":
                if item.ref in media_refs:
                    raise PublicSiteError(
                        f"Media is still referenced by an active post: {item.ref}"
                    )
                target = _local_media_target(profile_root, item.ref)
                if target is not None and target.exists() and target.is_file():
                    target.unlink()
                    changed.append(target)
                    try:
                        target.parent.rmdir()
                    except OSError:
                        pass
    library.nodes = [item for item in library.nodes if item.id not in ids]
    lib_path = save_public_library(name, library, action=f"purge {name} public library node")
    changed.append(lib_path)
    if changed:
        git_backup.record_change(changed, action=f"purge {name} public library files")
    return PublicLibraryOperationResult(node=node, changed_paths=changed, warnings=warnings)


def reconcile_public_library(
    name: str,
    *,
    create_missing: bool = True,
) -> PublicLibraryOperationResult:
    """Attach existing blog posts and blog media to ``public-library.yaml``."""
    library = load_public_library(name)
    existing_refs = {node.ref for node in library.nodes if node.ref}
    created: list[PublicLibraryNode] = []
    if create_missing:
        for post in load_blog_posts(
            name,
            include_drafts=True,
            include_archived=True,
            include_trashed=True,
        ):
            ref = _library_blog_ref(post.route)
            if ref in existing_refs:
                continue
            node = _library_add_post_node(
                name,
                library=library,
                parent_id="root",
                route=post.route,
                title=post.title,
                visibility="public" if post.status == "published" else "private",
                owned=False,
            )
            created.append(node)
            existing_refs.add(ref)
            media_dir = _profile_path(name) / MEDIA_DIRNAME / BLOG_DIRNAME / _slugify_route(post.route)
            if media_dir.exists():
                for media_path in sorted(media_dir.iterdir()):
                    if not media_path.is_file():
                        continue
                    ext = media_path.suffix.lower().lstrip(".")
                    if ext not in BLOG_IMAGE_EXTENSIONS and ext not in BLOG_VIDEO_EXTENSIONS:
                        continue
                    rel = _media_relative_path(name, media_path)
                    if rel in existing_refs:
                        continue
                    media_node = PublicLibraryNode(
                        id=_library_unique_id("media", rel),
                        type="media",
                        title=media_path.name,
                        parent_id=node.id,
                        order=_library_next_order(library, node.id),
                        visibility="private",
                        ref=rel,
                        owned=False,
                    )
                    library.nodes.append(media_node)
                    created.append(media_node)
                    existing_refs.add(rel)
    path = save_public_library(name, library, action=f"reconcile {name} public library")
    return PublicLibraryOperationResult(
        node=None,
        changed_paths=[path],
        warnings=[f"created {len(created)} node(s)"],
    )


def _validate_public_library(
    result: PublicValidationResult,
    name: str,
    library: PublicLibrary,
) -> None:
    """Validate ``public-library.yaml`` structural integrity."""
    if not _public_library_path(name).exists():
        return
    label = PUBLIC_LIBRARY_FILENAME
    ids: set[str] = set()
    active_refs: set[str] = set()
    for node in library.nodes:
        if not node.id:
            result.errors.append(f"{label}: node missing id")
            continue
        if node.id in ids:
            result.errors.append(f"{label}: duplicate node id '{node.id}'")
        ids.add(node.id)
        if node.type == "root" and node.id != "root":
            result.errors.append(f"{label}:{node.id}: root node id must be 'root'")
        if node.type not in PUBLIC_LIBRARY_TYPES:
            result.errors.append(f"{label}:{node.id}: invalid type '{node.type}'")
        if node.status not in PUBLIC_LIBRARY_STATUSES:
            result.errors.append(f"{label}:{node.id}: invalid status '{node.status}'")
        if node.visibility not in PUBLIC_VISIBILITIES:
            result.errors.append(f"{label}:{node.id}: invalid visibility '{node.visibility}'")
        if node.id != "root" and node.parent_id and node.parent_id not in ids:
            # A second pass below catches forward references; keep this as warning-free.
            pass
        if node.status != "trashed":
            if node.ref:
                if node.ref in active_refs:
                    result.errors.append(
                        f"{label}:{node.id}: duplicate active ref '{node.ref}'"
                    )
                active_refs.add(node.ref)
    ids = {node.id for node in library.nodes}
    by_id = {node.id: node for node in library.nodes}
    for node in library.nodes:
        if node.id == "root":
            continue
        if node.parent_id not in ids:
            result.errors.append(
                f"{label}:{node.id}: parent_id does not exist: {node.parent_id or '(empty)'}"
            )
        else:
            parent = by_id.get(node.parent_id)
            if parent is not None and parent.type not in {"root", "folder", "post"}:
                result.errors.append(
                    f"{label}:{node.id}: parent must be root, folder, or post"
                )
        seen: set[str] = set()
        cursor = node
        while cursor.parent_id:
            if cursor.parent_id in seen:
                result.errors.append(f"{label}:{node.id}: parent cycle detected")
                break
            seen.add(cursor.parent_id)
            parent = next((item for item in library.nodes if item.id == cursor.parent_id), None)
            if parent is None:
                break
            cursor = parent
        if node.status == "trashed":
            continue
        if node.type == "post":
            if not node.ref:
                result.errors.append(f"{label}:{node.id}: post node missing ref")
                continue
            ref_parts = _clean_library_ref(node.ref).split("/")
            if (
                not node.ref.startswith(f"{BLOG_DIRNAME}/")
                or not node.ref.endswith(".md")
                or any(part in {"", ".", ".."} for part in ref_parts)
            ):
                result.errors.append(
                    f"{label}:{node.id}: post ref must be a safe '{BLOG_DIRNAME}/<route>.md' path"
                )
                continue
            route = _library_blog_route(node.ref)
            path = _blog_markdown_path_for_route(name, route)
            if not path.exists() and not _blog_sidecar_path_for_markdown(path).exists():
                result.errors.append(
                    f"{label}:{node.id}: blog ref does not exist: {node.ref}"
                )
        elif node.type == "media":
            ref_parts = _clean_library_ref(node.ref).split("/")
            if not node.ref.startswith(f"{MEDIA_DIRNAME}/") or any(
                part in {"", ".", ".."} for part in ref_parts
            ):
                result.errors.append(
                    f"{label}:{node.id}: media ref must be a safe '{MEDIA_DIRNAME}/...' path"
                )
                continue
            target = _local_media_target(_profile_path(name), node.ref)
            if not node.ref or target is None or not target.exists():
                result.errors.append(
                    f"{label}:{node.id}: media ref does not exist: {node.ref}"
                )


def _parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw_meta = text[4:end]
    body_start = end + len("\n---")
    if text[body_start : body_start + 1] == "\n":
        body_start += 1
    meta = yaml.safe_load(raw_meta) or {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, text[body_start:]


def _format_front_matter(meta: dict, body: str) -> str:
    return "---\n" + _dump_yaml(meta) + "---\n\n" + body.lstrip()


def format_blog_document(meta: dict, body: str) -> str:
    """Format a blog Markdown document with YAML front matter."""
    return _format_front_matter(meta, body)


def blog_post_text(meta: dict, body: str) -> str:
    """Backward-friendly alias for formatting blog documents."""
    return format_blog_document(meta, body)


def _blog_sidecar_path_for_markdown(path: Path) -> Path:
    """Return the BlockNote sidecar path for a Markdown blog path."""

    return path.with_suffix(".blocknote.json")


def _blog_slug_from_sidecar_path(path: Path) -> str:
    """Return a blog slug from ``<slug>.blocknote.json``."""

    name = path.name
    suffix = ".blocknote.json"
    return name[: -len(suffix)] if name.endswith(suffix) else path.stem


def _blog_root_for_path(path: Path) -> Path | None:
    """Return the nearest ancestor named ``blog`` for a blog document path."""
    for parent in path.resolve().parents:
        if parent.name == BLOG_DIRNAME:
            return parent
    return None


def _blog_route_from_document_path(path: Path, blog_dir: Path | None = None) -> str:
    """Return the slash-separated blog route represented by a document path."""
    root = blog_dir or _blog_root_for_path(path)
    if root is None:
        return _blog_slug_from_sidecar_path(path) if path.name.endswith(".blocknote.json") else path.stem
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return _blog_slug_from_sidecar_path(path) if path.name.endswith(".blocknote.json") else path.stem
    parts = list(rel.parts)
    if not parts:
        return ""
    if path.name.endswith(".blocknote.json"):
        parts[-1] = _blog_slug_from_sidecar_path(path)
    else:
        parts[-1] = path.stem
    return "/".join(part for part in parts if part)


def _blog_category_path_from_route(route: str) -> list[str]:
    parts = [part for part in str(route or "").split("/") if part]
    return parts[:-1]


def _blog_category_path_for_document(path: Path, meta: dict | None = None) -> list[str]:
    route = _blog_route_from_document_path(path)
    category_path = _blog_category_path_from_route(route)
    if category_path:
        return category_path
    raw = (meta or {}).get("category_path")
    return _coerce_string_list(raw)


def _blog_route_leaf(route: str) -> str:
    parts = [part for part in str(route or "").split("/") if part]
    return parts[-1] if parts else ""


def _hidden_blog_path(path: Path, blog_dir: Path) -> bool:
    try:
        rel = path.resolve().relative_to(blog_dir.resolve())
    except ValueError:
        return True
    return any(part.startswith(".") for part in rel.parts)


def _taxonomy_nodes(raw: dict | None = None) -> list[dict]:
    data = raw or {}
    nodes = data.get("taxonomy") if isinstance(data, dict) else []
    return [node for node in nodes or [] if isinstance(node, dict)]


def _taxonomy_path_titles(raw: dict | None) -> dict[tuple[str, ...], list[str]]:
    """Return taxonomy category paths mapped to display title paths."""
    titles: dict[tuple[str, ...], list[str]] = {}

    def walk(nodes: list[dict], path: tuple[str, ...], title_path: list[str]) -> None:
        for node in nodes:
            slug = str(node.get("slug", "") or "").strip()
            if not slug:
                continue
            title = str(node.get("title", "") or slug).strip() or slug
            next_path = (*path, slug)
            next_title_path = [*title_path, title]
            titles[next_path] = next_title_path
            children = node.get("children")
            if isinstance(children, list):
                walk([child for child in children if isinstance(child, dict)], next_path, next_title_path)

    walk(_taxonomy_nodes(raw), (), [])
    return titles


def _taxonomy_enabled(raw: dict | None) -> bool:
    return bool(_taxonomy_nodes(raw))


def _taxonomy_child_nodes(raw: dict | None, category_path: list[str]) -> list[dict]:
    nodes = _taxonomy_nodes(raw)
    for segment in category_path:
        match = next(
            (
                node
                for node in nodes
                if str(node.get("slug", "") or "").strip() == segment
            ),
            None,
        )
        if match is None:
            return []
        children = match.get("children")
        nodes = [node for node in children or [] if isinstance(node, dict)]
    return nodes


def _taxonomy_category_title(raw: dict | None, category_path: list[str]) -> str:
    if not category_path:
        return "Blog"
    titles = _taxonomy_path_titles(raw).get(tuple(category_path))
    if titles:
        return " / ".join(titles)
    return " / ".join(category_path)


def _taxonomy_category_url_path(category_path: list[str]) -> str:
    if not category_path:
        return "blog/"
    return "blog/" + "/".join(category_path) + "/"


def _blog_aliases(meta: dict) -> list[str]:
    aliases = _coerce_string_list((meta or {}).get("aliases"))
    return [
        alias.strip().strip("/")
        for alias in aliases
        if alias.strip().strip("/")
    ]


def _read_blog_sidecar(path: Path) -> BlockNoteDocument | None:
    """Read a BlockNote sidecar, returning ``None`` on malformed files."""

    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return BlockNoteDocument.model_validate(raw)
    except Exception:
        return None


def _parse_blog_sidecar(path: Path, markdown_path: Path | None = None) -> BlogPost | None:
    """Parse one ``*.blocknote.json`` sidecar as a BlogPost."""

    doc = _read_blog_sidecar(path)
    if doc is None:
        return None
    route_from_path = _blog_route_from_document_path(markdown_path or path)
    slug = str(route_from_path or doc.slug or _blog_slug_from_sidecar_path(path)).strip()
    if not slug:
        slug = route_from_path or _blog_slug_from_sidecar_path(path)
    md_path = markdown_path or path.with_name(f"{_blog_slug_from_sidecar_path(path)}.md")
    meta = dict(doc.meta or {})
    category_path = _blog_category_path_for_document(md_path, meta)
    if category_path and not meta.get("category_path"):
        meta["category_path"] = list(category_path)
    return BlogPost(
        slug=slug,
        path=md_path,
        meta=meta,
        body=str(doc.markdown or ""),
        category_path=category_path,
        blocks_json=[block.model_dump(mode="json", exclude_none=True) for block in doc.blocks],
        sidecar_path=path,
    )


def _blog_post_candidate_paths(blog_dir: Path) -> list[Path]:
    """Return de-duplicated blog document paths, preferring Markdown when present."""

    candidate_paths: dict[str, Path] = {}
    if not blog_dir.exists():
        return []
    for path in sorted(blog_dir.rglob("*.md")):
        if _hidden_blog_path(path, blog_dir):
            continue
        candidate_paths[_blog_route_from_document_path(path, blog_dir)] = path
    for path in sorted(blog_dir.rglob("*.blocknote.json")):
        if _hidden_blog_path(path, blog_dir):
            continue
        route = _blog_route_from_document_path(path, blog_dir)
        candidate_paths.setdefault(route, path)
    return [candidate_paths[route] for route in sorted(candidate_paths)]


def parse_blog_post(path: Path) -> BlogPost:
    """Parse a blog post, preferring BlockNote sidecar state when present."""
    if path.name.endswith(".blocknote.json"):
        sidecar_post = _parse_blog_sidecar(path)
        if sidecar_post is not None:
            return sidecar_post
        raise PublicSiteError(f"Invalid blog sidecar: {path}")
    sidecar_path = _blog_sidecar_path_for_markdown(path)
    sidecar_post = _parse_blog_sidecar(sidecar_path, markdown_path=path)
    if sidecar_post is not None:
        return sidecar_post
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_front_matter(text)
    route = _blog_route_from_document_path(path)
    category_path = _blog_category_path_for_document(path, meta)
    if category_path and not meta.get("category_path"):
        meta["category_path"] = list(category_path)
    return BlogPost(
        slug=route or path.stem,
        path=path,
        meta=meta,
        body=body,
        category_path=category_path,
        blocks_json=[],
        sidecar_path=sidecar_path if sidecar_path.exists() else None,
    )


def load_blog_posts(
    name: str,
    *,
    include_drafts: bool = False,
    include_archived: bool = False,
    include_trashed: bool = False,
) -> list[BlogPost]:
    """Load visible blog posts from profiles/<name>/blog."""
    blog_dir = _profile_path(name) / BLOG_DIRNAME
    if not blog_dir.exists():
        return []
    library = load_public_library(name)
    library_enabled = _public_library_has_real_nodes(library)
    library_posts: dict[str, PublicLibraryNode] = {}
    trashed_routes: set[str] = set()
    if library_enabled:
        for node in library.nodes:
            if node.type != "post" or not node.ref:
                continue
            route = _library_blog_route(node.ref)
            if not route:
                continue
            if node.status == "trashed":
                trashed_routes.add(route)
                continue
            library_posts.setdefault(route, node)
        trashed_routes -= set(library_posts)
    public_library_only = library_enabled and not include_drafts and not include_archived
    posts: list[BlogPost] = []
    for path in _blog_post_candidate_paths(blog_dir):
        post = parse_blog_post(path)
        if not include_trashed and post.route in trashed_routes:
            continue
        if _status_visible(
            post.status,
            include_drafts=include_drafts,
            include_archived=include_archived,
        ):
            if public_library_only:
                node = library_posts.get(post.route)
                if node is None or node.visibility != "public":
                    continue
            posts.append(post)
    return sorted(
        posts,
        key=lambda p: (p.date, p.slug),
        reverse=True,
    )


def _status_visible(
    status: str,
    *,
    include_drafts: bool,
    include_archived: bool = False,
) -> bool:
    status = status or "draft"
    if status == "published":
        return True
    if include_drafts and status == "draft":
        return True
    if include_archived and status == "archived":
        return True
    return False


def _visibility_visible(visibility: str, *, include_drafts: bool) -> bool:
    if visibility == "public":
        return True
    return include_drafts and visibility == "private"


def _looks_like_domain(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}(/.*)?$", value))


def _strip_url_value(value: str) -> str:
    clean = str(value or "").strip()
    if clean.startswith("<") and clean.endswith(">"):
        clean = clean[1:-1].strip()
    return clean


def _url_compact(value: str) -> str:
    return _URL_CONTROL_RE.sub("", html.unescape(_strip_url_value(value)))


def _url_scheme(value: str) -> str:
    match = _URL_SCHEME_RE.match(_url_compact(value))
    return match.group(1).lower() if match else ""


def _is_protocol_relative_url(value: str) -> bool:
    return _url_compact(value).startswith("//")


def _unsafe_url_scheme(value: str, allowed_schemes: set[str]) -> str:
    scheme = _url_scheme(value)
    if scheme and scheme not in allowed_schemes:
        return scheme
    if _is_protocol_relative_url(value):
        return "protocol-relative"
    return ""


def _is_external_url(value: str) -> bool:
    return _url_scheme(value) in {"http", "https"}


def _safe_url_attr(
    value: str,
    *,
    allowed_schemes: set[str],
    allow_relative: bool = True,
) -> str:
    clean = _strip_url_value(html.unescape(str(value or "")))
    if not clean:
        return ""
    if _unsafe_url_scheme(clean, allowed_schemes):
        return ""
    if _url_scheme(clean):
        return clean
    if allow_relative:
        return clean
    return ""


def _public_link_href(value: str) -> str:
    clean = _strip_url_value(str(value or ""))
    if not clean:
        return ""
    if _unsafe_url_scheme(clean, SAFE_HREF_SCHEMES):
        return ""
    if _url_scheme(clean):
        return clean
    if _looks_like_domain(clean):
        return "https://" + clean
    return clean


def _validate_url_scheme(
    diagnostics: list[str],
    label: str,
    value: object,
    *,
    allowed_schemes: set[str],
) -> None:
    raw = str(value or "").strip()
    if not raw:
        return
    unsafe = _unsafe_url_scheme(raw, allowed_schemes)
    if unsafe:
        diagnostics.append(
            f"{label}: unsafe URL scheme '{unsafe}' is not allowed: {raw}"
        )


def _sanitize_html_url_attrs(html_text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        attr = match.group("attr").lower()
        raw = match.group("quoted")
        if raw is None:
            raw = match.group("bare") or ""
        allowed = SAFE_HREF_SCHEMES if attr == "href" else SAFE_SRC_SCHEMES
        clean = _safe_url_attr(
            raw,
            allowed_schemes=allowed,
            allow_relative=True,
        )
        if not clean:
            return ""
        quote_char = match.group("quote") or '"'
        return (
            f"{match.group('prefix')}{attr}={quote_char}"
            f"{html.escape(clean, quote=True)}{quote_char}"
        )

    return _URL_ATTR_RE.sub(repl, html_text)


def _as_string_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _coerce_string_list(raw: object) -> list[str]:
    """Return a clean list from list, comma text, or newline text."""
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    if isinstance(raw, str):
        return [
            item.strip()
            for chunk in raw.splitlines()
            for item in chunk.split(",")
            if item.strip()
        ]
    return []


def _normalize_blog_meta(meta: dict) -> dict:
    """Normalize structured blog front matter fields before writing."""
    clean = dict(meta or {})
    for field_name in (
        "tags",
        "related_evidence",
        "related_kanban",
        "related_claims",
        "related_sources",
        "related_research_claims",
        "related_citations",
        "category_path",
        "aliases",
    ):
        clean[field_name] = _coerce_string_list(clean.get(field_name))
    for field_name in ("title", "date", "status", "summary", "cover"):
        if clean.get(field_name) is None:
            clean[field_name] = ""
    clean["status"] = str(clean.get("status", "") or "draft")
    return clean


def markdown_contains_math(text: str) -> bool:
    """Return True when Markdown appears to contain LaTeX math delimiters."""
    clean = _FENCED_CODE_RE.sub("", text)
    if _MATH_BLOCK_COMMENT_RE.search(clean):
        return True
    if _DISPLAY_DOLLAR_MATH_RE.search(clean):
        return True
    if _DISPLAY_BRACKET_MATH_RE.search(clean):
        return True
    if _INLINE_PAREN_MATH_RE.search(clean):
        return True
    for match in _INLINE_DOLLAR_MATH_RE.finditer(clean):
        if _looks_like_inline_math(match.group(1)):
            return True
    return False


def _looks_like_inline_math(value: str) -> bool:
    candidate = value.strip()
    if re.search(r"[\\_^=+\-*/<>()]", candidate):
        return True
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", candidate))


def _links(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for key, val in raw.items():
        if val is None:
            continue
        text = str(val).strip()
        if text:
            out[str(key)] = text
    return out


def _validate_link_map_schemes(
    result: PublicValidationResult,
    label: str,
    raw: object,
) -> None:
    for key, value in _links(raw).items():
        _validate_url_scheme(
            result.errors,
            f"{label}.links.{key}",
            value,
            allowed_schemes=SAFE_HREF_SCHEMES,
        )


def _validate_contact_schemes(
    result: PublicValidationResult,
    raw: object,
) -> None:
    for key, value in _links(raw).items():
        _validate_url_scheme(
            result.errors,
            f"{PUBLIC_PROFILE_FILENAME}.contacts.{key}",
            value,
            allowed_schemes=SAFE_HREF_SCHEMES,
        )


def _evidence_ids(name: str) -> set[str]:
    raw = _read_yaml_mapping(_profile_path(name) / "evidence-pool.yaml")
    entries = raw.get("evidence_entries") or []
    ids: set[str] = set()
    if isinstance(entries, list):
        for item in entries:
            if isinstance(item, dict):
                eid = str(item.get("id", "") or "").strip()
                if eid:
                    ids.add(eid)
    return ids


def _evidence_index(name: str) -> dict[str, dict]:
    raw = _read_yaml_mapping(_profile_path(name) / "evidence-pool.yaml")
    entries = raw.get("evidence_entries") or []
    out: dict[str, dict] = {}
    if isinstance(entries, list):
        for item in entries:
            if isinstance(item, dict):
                eid = str(item.get("id", "") or "").strip()
                if eid:
                    out[eid] = item
    return out


def _claim_index(name: str) -> dict[str, dict]:
    """Return all claim id -> claim from evidence-pool.yaml."""
    raw = _read_yaml_mapping(_profile_path(name) / "evidence-pool.yaml")
    return claim_index(raw)


def _accepted_claim_index(name: str) -> dict[str, dict]:
    """Return accepted claim id -> claim from evidence-pool.yaml."""
    raw = _read_yaml_mapping(_profile_path(name) / "evidence-pool.yaml")
    return accepted_claim_index(raw)


def _validate_claim_refs(
    result: PublicValidationResult,
    label: str,
    refs: list[str],
    known_claims: dict[str, dict],
    known_evidence_ids: set[str],
) -> None:
    """Validate claim provenance for public-output front matter."""
    for ref in refs:
        claim = known_claims.get(ref)
        if claim is None:
            result.errors.append(f"{label}: unknown claim ref '{ref}'")
            continue
        if str(claim.get("status", "") or "") != "accepted":
            result.errors.append(f"{label}: claim ref '{ref}' is not accepted")
        for evidence_ref in _as_string_list(claim.get("evidence_refs")):
            if evidence_ref not in known_evidence_ids:
                result.errors.append(
                    f"{label}: claim ref '{ref}' has unknown evidence ref "
                    f"'{evidence_ref}'"
                )


def _skill_refs_for_evidence(name: str, refs: list[str]) -> list[str]:
    raw = _read_yaml_mapping(_profile_path(name) / "skill-tree.yaml")
    nodes = raw.get("nodes") or []
    wanted = set(refs)
    out: list[str] = []
    seen: set[str] = set()
    if not isinstance(nodes, list):
        return out
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", "") or "").strip()
        if not node_id:
            continue
        node_refs = set(_as_string_list(node.get("evidence_refs")))
        if not wanted.intersection(node_refs):
            continue
        if node_id not in seen:
            seen.add(node_id)
            out.append(node_id)
    return out


def _validate_required(
    result: PublicValidationResult,
    label: str,
    data: dict,
    fields: tuple[str, ...],
) -> None:
    for field_name in fields:
        if field_name not in data or data.get(field_name) is None:
            result.errors.append(
                f"{label}: missing required field '{field_name}'"
            )
            continue
        value = data.get(field_name)
        if not isinstance(value, str) or value.strip():
            continue
        result.errors.append(f"{label}: missing required field '{field_name}'")


def _validate_media_path(
    result: PublicValidationResult,
    profile_root: Path,
    label: str,
    value: object,
) -> None:
    if value is None:
        return
    rel = str(value).strip()
    if not rel:
        return
    unsafe = _unsafe_url_scheme(rel, SAFE_SRC_SCHEMES)
    if unsafe:
        result.errors.append(
            f"{label}: unsafe URL scheme '{unsafe}' is not allowed: {rel}"
        )
        return
    if _is_external_url(rel):
        return
    media_root = (profile_root / MEDIA_DIRNAME).resolve()
    target = (profile_root / rel).resolve()
    try:
        target.relative_to(media_root)
    except ValueError:
        result.errors.append(
            f"{label}: media path must stay under '{MEDIA_DIRNAME}/': {rel}"
        )
        return
    if not target.exists():
        result.errors.append(f"{label}: media file does not exist: {rel}")


def _validate_blog_cover(
    result: PublicValidationResult,
    profile_root: Path,
    label: str,
    value: object,
) -> None:
    rel = str(value or "").strip()
    if not rel:
        return
    _validate_url_scheme(
        result.errors,
        label,
        rel,
        allowed_schemes=SAFE_SRC_SCHEMES,
    )
    if _unsafe_url_scheme(rel, SAFE_SRC_SCHEMES):
        return
    if _is_external_url(rel):
        return
    if not _is_local_media_ref(rel):
        result.errors.append(
            f"{label}: cover image must stay under '{MEDIA_DIRNAME}/': {rel}"
        )
        return
    _validate_local_media_ref(
        result.errors,
        profile_root,
        label,
        rel,
        max_bytes=BLOG_IMAGE_MAX_BYTES,
        allowed_extensions=BLOG_IMAGE_EXTENSIONS,
    )


def _valid_blog_cover_ref(profile_root: Path, value: object) -> str:
    rel = str(value or "").strip()
    if not rel or _unsafe_url_scheme(rel, SAFE_SRC_SCHEMES):
        return ""
    if _is_external_url(rel):
        return rel
    clean = _strip_markdown_url(rel).lstrip("/")
    if not _is_local_media_ref(clean):
        return ""
    target = _local_media_target(profile_root, clean)
    if target is None or not target.exists() or not target.is_file():
        return ""
    if _media_extension(clean) not in BLOG_IMAGE_EXTENSIONS:
        return ""
    if target.stat().st_size > BLOG_IMAGE_MAX_BYTES:
        return ""
    return clean


def _media_src(ref: str) -> str:
    clean = str(ref or "").strip()
    if not clean:
        return ""
    if _is_external_url(clean):
        return clean
    return "/" + clean.lstrip("/")


def _strip_markdown_url(value: str) -> str:
    return _strip_url_value(value)


def _media_extension(value: str) -> str:
    clean = _strip_markdown_url(value)
    parsed = urlparse(clean)
    path = parsed.path if parsed.scheme else clean
    suffix = Path(path).suffix.lower().lstrip(".")
    return suffix


def _is_local_media_ref(value: str) -> bool:
    clean = _strip_markdown_url(value).lstrip("/")
    return bool(clean) and not _is_external_url(clean) and clean.startswith(
        f"{MEDIA_DIRNAME}/"
    )


def _local_media_target(profile_root: Path, rel: str) -> Path | None:
    clean = _strip_markdown_url(rel).lstrip("/")
    media_root = (profile_root / MEDIA_DIRNAME).resolve()
    target = (profile_root / clean).resolve()
    try:
        target.relative_to(media_root)
    except ValueError:
        return None
    return target


def _validate_local_media_ref(
    diagnostics: list[str],
    profile_root: Path,
    label: str,
    rel: str,
    *,
    max_bytes: int | None = None,
    allowed_extensions: set[str] | None = None,
) -> None:
    clean = _strip_markdown_url(rel).lstrip("/")
    target = _local_media_target(profile_root, clean)
    if target is None:
        diagnostics.append(
            f"{label}: media path must stay under '{MEDIA_DIRNAME}/': {clean}"
        )
        return
    if allowed_extensions is not None:
        ext = _media_extension(clean)
        if ext not in allowed_extensions:
            diagnostics.append(
                f"{label}: unsupported media extension '.{ext}'"
            )
            return
    if not target.exists() or not target.is_file():
        diagnostics.append(f"{label}: media file does not exist: {clean}")
        return
    if max_bytes is not None and target.stat().st_size > max_bytes:
        diagnostics.append(
            f"{label}: media file is larger than {max_bytes // (1024 * 1024)}MB: {clean}"
        )


def _markdown_image_refs(text: str) -> list[str]:
    refs: list[str] = []
    pattern = re.compile(
        r"!\[[^\]]*\]\(\s*(?P<src><[^>]+>|[^)\s]+)"
        r"(?:\s+[\"'][^\"']*[\"'])?\s*\)"
    )
    for match in pattern.finditer(text):
        refs.append(_strip_markdown_url(match.group("src")))
    return refs


def _markdown_link_refs(text: str) -> list[str]:
    return [
        _strip_markdown_url(match.group("href"))
        for match in _MARKDOWN_LINK_RE.finditer(text)
    ]


def _html_url_attr_refs(text: str, attr_name: str) -> list[str]:
    refs: list[str] = []
    for match in _URL_ATTR_RE.finditer(text):
        attr = match.group("attr").lower()
        if attr != attr_name:
            continue
        raw = match.group("quoted")
        if raw is None:
            raw = match.group("bare") or ""
        refs.append(_strip_url_value(html.unescape(raw)))
    return refs


def _video_directives(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"::video\[(?P<caption>[^\]]*)\]\((?P<src>[^)]+)\)")
    return [
        (match.group("caption").strip(), _strip_markdown_url(match.group("src")))
        for match in pattern.finditer(text)
    ]


def _visual_block_comment_payloads(text: str) -> list[dict]:
    payloads: list[dict] = []
    for match in _VISUAL_BLOCK_COMMENT_RE.finditer(text):
        raw = str(match.group("payload") or "").strip()
        if not raw:
            payloads.append({})
            continue
        try:
            loaded = json.loads(raw)
        except Exception:
            payloads.append({})
            continue
        payloads.append(loaded if isinstance(loaded, dict) else {})
    return payloads


def _blog_body_media_refs(body: str) -> list[str]:
    refs: list[str] = []
    refs.extend(
        _strip_markdown_url(ref).lstrip("/")
        for ref in _markdown_image_refs(body)
        if _is_local_media_ref(ref)
    )
    refs.extend(
        _strip_markdown_url(src).lstrip("/")
        for _caption, src in _video_directives(body)
        if _is_local_media_ref(src)
    )
    refs.extend(
        _strip_markdown_url(str(payload.get("src", "") or "")).lstrip("/")
        for payload in _visual_block_comment_payloads(body)
        if _is_local_media_ref(str(payload.get("src", "") or ""))
    )
    return refs


def _youtube_embed_url(parsed) -> str:
    host = parsed.netloc.lower().removeprefix("www.")
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    else:
        if parsed.path.startswith("/embed/"):
            video_id = parsed.path.split("/", 2)[2].split("/")[0]
        else:
            video_id = (parse_qs(parsed.query).get("v") or [""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,}", video_id or ""):
        return ""
    return f"https://www.youtube.com/embed/{quote(video_id, safe='')}"


def _vimeo_embed_url(parsed) -> str:
    parts = [part for part in parsed.path.split("/") if part]
    if not parts or not re.fullmatch(r"\d+", parts[0]):
        return ""
    return f"https://player.vimeo.com/video/{quote(parts[0], safe='')}"


def _whitelisted_video_embed(src: str) -> str:
    parsed = urlparse(src)
    host = parsed.netloc.lower().removeprefix("www.")
    if host in {"youtube.com", "m.youtube.com", "youtu.be"}:
        return _youtube_embed_url(parsed)
    if host in {"vimeo.com", "player.vimeo.com"}:
        if host == "player.vimeo.com" and parsed.path.startswith("/video/"):
            return src
        return _vimeo_embed_url(parsed)
    if host == "player.bilibili.com":
        return src
    return ""


def _direct_video_allowed(src: str) -> bool:
    ext = _media_extension(src)
    if _is_external_url(src):
        return ext in BLOG_DIRECT_VIDEO_EXTENSIONS
    return ext in BLOG_VIDEO_EXTENSIONS


def _ffprobe_video_stream(path: Path) -> dict:
    """Return the first video stream metadata when ffprobe is available."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {}
    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name,codec_tag_string,profile,width,height",
                "-of",
                "json",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if result.returncode != 0:
        return {}
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return {}
    streams = payload.get("streams")
    if not isinstance(streams, list) or not streams:
        return {}
    stream = streams[0]
    return stream if isinstance(stream, dict) else {}


def _browser_video_compatible(path: Path, stream: dict) -> bool | None:
    codec = str(stream.get("codec_name", "") or "").strip().lower()
    if not codec:
        return None
    ext = path.suffix.lower().lstrip(".")
    compatible = BLOG_BROWSER_VIDEO_CODECS.get(ext)
    if compatible is None:
        return False
    return codec in compatible


def _video_compatibility_payload(path: Path) -> dict:
    stream = _ffprobe_video_stream(path)
    if not stream:
        return {}
    codec = str(stream.get("codec_name", "") or "").strip()
    tag = str(stream.get("codec_tag_string", "") or "").strip()
    compatible = _browser_video_compatible(path, stream)
    payload: dict = {
        "video_codec": codec,
        "video_codec_tag": tag,
        "video_profile": str(stream.get("profile", "") or "").strip(),
        "video_browser_compatible": compatible,
        "needs_video_conversion": compatible is False,
    }
    if compatible is False:
        label = codec or tag or "unknown"
        payload["video_compatibility_warning"] = (
            f"Video codec '{label}' may not play in browsers. Convert it to "
            "H.264 MP4 before publishing."
        )
    return payload


def _video_compatibility_payload_from_bytes(data: bytes, filename: str) -> dict:
    suffix = Path(filename).suffix.lower() or ".mp4"
    if suffix.lstrip(".") not in BLOG_VIDEO_EXTENSIONS:
        return {}
    with tempfile.TemporaryDirectory(prefix="nblane-video-probe-") as tmp:
        target = Path(tmp) / f"probe{suffix}"
        target.write_bytes(data)
        return _video_compatibility_payload(target)


def _transcode_video_file(source: Path, target: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise PublicSiteError(
            "ffmpeg is required to convert videos to browser-compatible MP4."
        )
    try:
        result = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(source),
                "-map",
                "0:v:0",
                "-map",
                "0:a?",
                "-c:v",
                "libx264",
                "-profile:v",
                "high",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(target),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PublicSiteError(f"Video conversion failed: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        message = detail[-1] if detail else "unknown ffmpeg error"
        raise PublicSiteError(f"Video conversion failed: {message}")
    if not target.exists() or target.stat().st_size <= 0:
        raise PublicSiteError("Video conversion produced an empty file.")


def _browser_compatible_video_data(data: bytes, filename: str) -> tuple[bytes, str]:
    """Transcode uploaded/generated videos to H.264 MP4 when needed and possible."""
    suffix = Path(filename).suffix.lower()
    if suffix.lstrip(".") not in BLOG_VIDEO_EXTENSIONS:
        return data, filename
    with tempfile.TemporaryDirectory(prefix="nblane-video-") as tmp:
        tmp_dir = Path(tmp)
        source = tmp_dir / f"source{suffix or '.mp4'}"
        source.write_bytes(data)
        compatibility = _video_compatibility_payload(source)
        if compatibility.get("video_browser_compatible") is not False:
            return data, filename
        if not shutil.which("ffmpeg"):
            return data, filename
        target = tmp_dir / "browser-compatible.mp4"
        _transcode_video_file(source, target)
        converted = target.read_bytes()
    if len(converted) > BLOG_VIDEO_MAX_BYTES:
        return data, filename
    stem = _safe_media_filename(filename, fallback="video")
    clean_stem = Path(stem).stem[:52].rstrip(".-") or "video"
    return converted, f"{clean_stem}-h264.mp4"


def _render_video_block(caption: str, src: str) -> str:
    clean = _strip_markdown_url(src)
    escaped_caption = html.escape(caption)
    caption_html = (
        f'<figcaption class="media-caption">{escaped_caption}</figcaption>'
        if caption
        else ""
    )
    if _is_local_media_ref(clean) or (
        _is_external_url(clean) and _direct_video_allowed(clean)
    ):
        if not _direct_video_allowed(clean):
            return (
                '<p class="media-caption">'
                f'<a href="{html.escape(clean, quote=True)}">'
                f"{escaped_caption or html.escape(clean)}</a>"
                "</p>"
            )
        return (
            '<figure class="media-block">'
            f'<video class="media-video" controls preload="metadata" '
            f'src="{html.escape(clean, quote=True)}"></video>'
            f"{caption_html}</figure>"
        )
    if _is_external_url(clean):
        embed = _whitelisted_video_embed(clean)
        if embed:
            title = caption or "Embedded video"
            return (
                '<figure class="media-block">'
                f'<iframe class="media-video media-embed" '
                f'src="{html.escape(embed, quote=True)}" '
                f'title="{html.escape(title, quote=True)}" '
                'loading="lazy" allowfullscreen></iframe>'
                f"{caption_html}</figure>"
            )
        label = escaped_caption or html.escape(clean)
        return (
            '<p class="media-caption">'
            f'<a href="{html.escape(clean, quote=True)}">{label}</a>'
            "</p>"
        )
    return (
        '<p class="media-caption">'
        f"{escaped_caption or html.escape(clean)}"
        "</p>"
    )


def _replace_video_directives(text: str) -> str:
    pattern = re.compile(r"::video\[(?P<caption>[^\]]*)\]\((?P<src>[^)]+)\)")

    def repl(match: re.Match[str]) -> str:
        return _render_video_block(
            match.group("caption").strip(),
            match.group("src").strip(),
        )

    return pattern.sub(repl, text)


def _parse_mermaid_node(token: str) -> tuple[str, str]:
    clean = token.strip().rstrip(";")
    match = re.match(
        r'^(?P<id>[A-Za-z][A-Za-z0-9_-]*)(?:\["(?P<quoted>[^"]+)"\]|\[(?P<bracket>[^\]]+)\]|\{(?P<brace>[^}]+)\}|\((?P<paren>[^)]+)\))?',
        clean,
    )
    if not match:
        return "", ""
    node_id = match.group("id")
    label = (
        match.group("quoted")
        or match.group("bracket")
        or match.group("brace")
        or match.group("paren")
        or node_id
    )
    return node_id, re.sub(r"\s+", " ", label).strip()[:80] or node_id


def _normalize_mermaid_edge_line(line: str) -> str:
    """Remove common Mermaid edge labels before conservative node parsing."""

    clean = line.strip().rstrip(";")
    clean = re.sub(r"\s+--\s+[^-]+?\s+-->\s+", " --> ", clean)
    clean = re.sub(r"\s+==\s+[^=]+?\s+==>\s+", " ==> ", clean)
    clean = re.sub(r"\s+-\.\s+[^.]+?\s+\.->\s+", " -.-> ", clean)
    return clean


def _strip_mermaid_leading_edge_label(token: str) -> str:
    return re.sub(r"^\|[^|]*\|\s*", "", token.strip())


def _render_mermaid_static_svg(source: str) -> str:
    """Render a conservative SVG fallback for simple flowchart Mermaid graphs."""

    source = _normalize_mermaid_source(source)
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    if not lines or not re.match(r"^(flowchart|graph)\s+", lines[0], re.I):
        return ""
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str]] = []
    for line in lines[1:]:
        if line.startswith(("%%", "classDef ", "class ", "style ")):
            continue
        edge_line = _normalize_mermaid_edge_line(line)
        edge_match = re.match(
            r"^(?P<left>.+?)\s*(?:-->|---?>|==>|-\.\->)\s*(?P<right>.+?)$",
            edge_line,
        )
        if not edge_match:
            node_id, label = _parse_mermaid_node(line)
            if node_id:
                nodes.setdefault(node_id, label)
            continue
        left_id, left_label = _parse_mermaid_node(edge_match.group("left"))
        right_id, right_label = _parse_mermaid_node(
            _strip_mermaid_leading_edge_label(edge_match.group("right"))
        )
        if not left_id or not right_id:
            continue
        nodes.setdefault(left_id, left_label)
        nodes.setdefault(right_id, right_label)
        edges.append((left_id, right_id))
    if not nodes:
        return ""
    node_ids = list(nodes)
    positions = {
        node_id: (40, 36 + index * 92)
        for index, node_id in enumerate(node_ids)
    }
    width = 460
    height = max(140, 76 + len(node_ids) * 92)
    marker_id = f"arrow-{hashlib.sha1(str(source).encode('utf-8')).hexdigest()[:10]}"
    edge_parts: list[str] = []
    for left_id, right_id in edges:
        if left_id not in positions or right_id not in positions:
            continue
        x1, y1 = positions[left_id]
        x2, y2 = positions[right_id]
        edge_parts.append(
            '<path class="mermaid-static-edge" '
            f'd="M {x1 + 180} {y1 + 54} C {x1 + 180} {y1 + 76}, '
            f"{x2 + 180} {y2 - 22}, {x2 + 180} {y2} "
            f'" marker-end="url(#{marker_id})" />'
        )
    node_parts: list[str] = []
    for node_id in node_ids:
        x, y = positions[node_id]
        label = html.escape(nodes[node_id])
        node_parts.append(
            '<g class="mermaid-static-node">'
            f'<rect x="{x}" y="{y}" width="360" height="54" rx="8" />'
            f'<text x="{x + 180}" y="{y + 33}" text-anchor="middle">{label}</text>'
            "</g>"
        )
    return (
        '<svg class="mermaid-static" xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Mermaid diagram">'
        "<defs>"
        f'<marker id="{marker_id}" viewBox="0 0 10 10" refX="8" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" />'
        "</marker>"
        "</defs>"
        f'{"".join(edge_parts)}{"".join(node_parts)}'
        "</svg>"
    )


def _normalize_mermaid_source(source: str) -> str:
    """Normalize common one-line Mermaid flowcharts produced by LLMs."""

    text = (
        str(source or "")
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\u002d", "-")
        .strip()
        .rstrip("，。")
    )
    if "\n" in text:
        return text
    match = re.match(r"^(?P<header>(?:flowchart|graph)\s+(?:TB|TD|BT|LR|RL))\s+(?P<body>.+)$", text, re.I)
    if not match:
        return text
    statements = _split_one_line_mermaid_flowchart(match.group("body").strip())
    if not statements:
        return text
    return "\n".join([match.group("header"), *(f"  {statement}" for statement in statements)])


def _split_one_line_mermaid_flowchart(body: str) -> list[str]:
    statements: list[str] = []
    start = 0
    quote = ""
    square = curly = paren = 0
    for index, char in enumerate(body):
        if quote:
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"', "`"}:
            quote = char
            continue
        if char == "[":
            square += 1
            continue
        if char == "]" and square:
            square -= 1
            continue
        if char == "{":
            curly += 1
            continue
        if char == "}" and curly:
            curly -= 1
            continue
        if char == "(":
            paren += 1
            continue
        if char == ")" and paren:
            paren -= 1
            continue
        if not char.isspace() or square or curly or paren:
            continue
        previous = body[index - 1] if index > 0 else ""
        if not re.match(r"[\w\]\}\)]", previous, re.I):
            continue
        rest = body[index:].lstrip()
        if re.match(
            r"^[A-Za-z_][\w-]*(?:\s*(?:\[[^\]]*\]|\{[^}]*\}|\([^)]*\)))?\s*(?:-->|---|--|==>|-\.\->|-\.)",
            rest,
        ):
            statement = body[start:index].strip().rstrip(";")
            if statement:
                statements.append(statement)
            start = len(body) - len(rest)
    tail = body[start:].strip().rstrip(";")
    if tail:
        statements.append(tail)
    if len(statements) == 1 and ";" in statements[0]:
        statements = [part.strip() for part in statements[0].split(";") if part.strip()]
    return statements


def _render_visual_block_comment(payload: dict) -> str:
    src = _strip_markdown_url(str(payload.get("src", "") or "")).strip()
    asset_type = str(payload.get("asset_type", "") or "").strip().lower()
    visual_kind = str(payload.get("visual_kind", "") or "").strip().lower()
    mermaid = str(payload.get("mermaid", "") or "").strip()
    caption = str(payload.get("caption", "") or "").strip()
    alt = str(payload.get("alt", "") or caption or "Visual").strip()
    if not src and (asset_type == "diagram" or mermaid):
        diagram_source = _normalize_mermaid_source(
            mermaid or str(payload.get("prompt", "") or "")
        )
        static_fallback = _render_mermaid_static_svg(diagram_source)
        diagram_html = f'<pre class="mermaid">{html.escape(diagram_source)}</pre>'
        if static_fallback:
            diagram_html += f"<noscript>{static_fallback}</noscript>"
        caption_html = (
            f'<figcaption class="media-caption">{html.escape(caption)}</figcaption>'
            if caption
            else ""
        )
        return (
            '<figure class="media-block visual-block"'
            f' data-visual-kind="{html.escape(visual_kind or "flowchart", quote=True)}"'
            f' data-asset-type="{html.escape(asset_type or "diagram", quote=True)}">'
            f"{diagram_html}"
            f"{caption_html}</figure>"
        )
    if not src:
        return ""
    display_src = _media_src(src)
    if (
        asset_type == "video"
        or visual_kind == "video_edit"
        or _media_extension(src) in BLOG_VIDEO_EXTENSIONS
    ):
        return _render_video_block(caption or alt, display_src)
    attrs = ""
    if visual_kind:
        attrs += f' data-visual-kind="{html.escape(visual_kind, quote=True)}"'
    if asset_type:
        attrs += f' data-asset-type="{html.escape(asset_type, quote=True)}"'
    caption_html = (
        f'<figcaption class="media-caption">{html.escape(caption)}</figcaption>'
        if caption
        else ""
    )
    return (
        f'<figure class="media-block visual-block"{attrs}>'
        f'<img src="{html.escape(display_src, quote=True)}" '
        f'alt="{html.escape(alt, quote=True)}" loading="lazy" />'
        f"{caption_html}</figure>"
    )


def _replace_visual_block_comments(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        raw = str(match.group("payload") or "").strip()
        if not raw:
            return ""
        try:
            loaded = json.loads(raw)
        except Exception:
            return ""
        if not isinstance(loaded, dict):
            return ""
        return _render_visual_block_comment(loaded)

    return _VISUAL_BLOCK_COMMENT_RE.sub(repl, text)


def _replace_ai_loading_comments(text: str) -> str:
    """Drop unaccepted inline AI candidates from public-site rendering."""

    return _AI_LOADING_COMMENT_RE.sub("", text)


def _replace_math_block_comments(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        raw = str(match.group("payload") or "").strip()
        if not raw:
            return ""
        try:
            loaded = json.loads(raw)
        except Exception:
            return ""
        if not isinstance(loaded, dict):
            return ""
        latex = str(loaded.get("latex", "") or "").strip()
        if not latex:
            return ""
        return f"\n\n$$\n{latex}\n$$\n\n"

    return _MATH_BLOCK_COMMENT_RE.sub(repl, text)


def _validate_blog_body_media(
    diagnostics: list[str],
    profile_root: Path,
    label: str,
    body: str,
) -> None:
    clean_body = _FENCED_CODE_RE.sub("", body)
    for href in _markdown_link_refs(clean_body):
        _validate_url_scheme(
            diagnostics,
            f"{label}.link",
            href,
            allowed_schemes=SAFE_HREF_SCHEMES,
        )
    for href in _html_url_attr_refs(clean_body, "href"):
        _validate_url_scheme(
            diagnostics,
            f"{label}.html.href",
            href,
            allowed_schemes=SAFE_HREF_SCHEMES,
        )
    for src in _html_url_attr_refs(clean_body, "src"):
        _validate_url_scheme(
            diagnostics,
            f"{label}.html.src",
            src,
            allowed_schemes=SAFE_SRC_SCHEMES,
        )
    for ref in _markdown_image_refs(clean_body):
        _validate_url_scheme(
            diagnostics,
            f"{label}.image",
            ref,
            allowed_schemes=SAFE_SRC_SCHEMES,
        )
        if _unsafe_url_scheme(ref, SAFE_SRC_SCHEMES):
            continue
        if _is_external_url(ref):
            continue
        if not _is_local_media_ref(ref):
            diagnostics.append(
                f"{label}: local image must stay under '{MEDIA_DIRNAME}/': {ref}"
            )
            continue
        _validate_local_media_ref(
            diagnostics,
            profile_root,
            f"{label}.image",
            ref,
            max_bytes=BLOG_IMAGE_MAX_BYTES,
            allowed_extensions=BLOG_IMAGE_EXTENSIONS,
        )
    for _caption, src in _video_directives(clean_body):
        _validate_url_scheme(
            diagnostics,
            f"{label}.video",
            src,
            allowed_schemes=SAFE_SRC_SCHEMES,
        )
        if _unsafe_url_scheme(src, SAFE_SRC_SCHEMES):
            continue
        if _is_external_url(src):
            if _direct_video_allowed(src) or _whitelisted_video_embed(src):
                continue
            diagnostics.append(
                f"{label}: unsupported video URL; use mp4/webm/ogg or a whitelisted embed URL: {src}"
            )
            continue
        if not _is_local_media_ref(src):
            diagnostics.append(
                f"{label}: local video must stay under '{MEDIA_DIRNAME}/': {src}"
            )
            continue
        _validate_local_media_ref(
            diagnostics,
            profile_root,
            f"{label}.video",
            src,
            max_bytes=BLOG_VIDEO_MAX_BYTES,
            allowed_extensions=BLOG_VIDEO_EXTENSIONS,
        )
        target = _local_media_target(profile_root, src)
        if target is not None and target.exists() and target.is_file():
            compatibility = _video_compatibility_payload(target)
            if compatibility.get("video_browser_compatible") is False:
                diagnostics.append(
                    f"{label}: video may not play in browsers; convert to "
                    f"H.264 MP4: {src}"
                )


def _validate_evidence_refs(
    result: PublicValidationResult,
    label: str,
    refs: list[str],
    known_ids: set[str],
) -> None:
    for ref in refs:
        if ref not in known_ids:
            result.errors.append(f"{label}: unknown evidence ref '{ref}'")


def _validate_status(
    result: PublicValidationResult,
    label: str,
    status: str,
) -> None:
    if status not in PUBLISH_STATUSES:
        result.errors.append(
            f"{label}: status must be one of "
            f"{', '.join(sorted(PUBLISH_STATUSES))}"
        )


def _validate_blog_taxonomy(
    result: PublicValidationResult,
    raw: dict,
) -> None:
    """Validate the optional blog taxonomy tree."""
    if not raw:
        return
    if str(raw.get("profile", "") or "").strip() and not isinstance(raw.get("profile"), str):
        result.errors.append(f"{BLOG_TAXONOMY_FILENAME}: 'profile' must be a string")
    nodes = raw.get("taxonomy")
    if nodes is None:
        return
    if not isinstance(nodes, list):
        result.errors.append(f"{BLOG_TAXONOMY_FILENAME}: 'taxonomy' must be a list")
        return
    seen: set[tuple[str, ...]] = set()

    def walk(items: list, path: tuple[str, ...]) -> None:
        sibling_slugs: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                result.errors.append(f"{BLOG_TAXONOMY_FILENAME}: category entries must be mappings")
                continue
            raw_slug = str(item.get("slug", "") or "").strip()
            title = str(item.get("title", "") or "").strip()
            if not raw_slug:
                result.errors.append(f"{BLOG_TAXONOMY_FILENAME}: category missing slug")
                continue
            slug = _slugify(raw_slug)
            if slug != raw_slug:
                result.errors.append(
                    f"{BLOG_TAXONOMY_FILENAME}: category slug must be URL-safe: {raw_slug}"
                )
            if raw_slug in sibling_slugs:
                result.errors.append(
                    f"{BLOG_TAXONOMY_FILENAME}: duplicate category slug '{raw_slug}'"
                )
            sibling_slugs.add(raw_slug)
            if not title:
                result.errors.append(
                    f"{BLOG_TAXONOMY_FILENAME}: category '{raw_slug}' missing title"
                )
            next_path = (*path, raw_slug)
            if next_path in seen:
                result.errors.append(
                    f"{BLOG_TAXONOMY_FILENAME}: duplicate category path "
                    + "/".join(next_path)
                )
            seen.add(next_path)
            children = item.get("children")
            if children is None:
                continue
            if not isinstance(children, list):
                result.errors.append(
                    f"{BLOG_TAXONOMY_FILENAME}: children for '{raw_slug}' must be a list"
                )
                continue
            walk(children, next_path)

    walk(nodes, ())


def validate_blog_text_for_publish(
    name: str,
    path: Path,
    text: str,
) -> PublicValidationResult:
    """Validate one blog document as if it will become public."""
    root = _profile_path(name)
    meta, body = _parse_front_matter(text)
    route = _blog_route_from_document_path(path) or path.stem
    post = BlogPost(
        slug=route,
        path=path,
        meta=meta,
        body=body,
        category_path=_blog_category_path_for_document(path, meta),
    )
    result = PublicValidationResult()
    blog_taxonomy = load_blog_taxonomy(name)
    public_library = load_public_library(name)
    taxonomy_paths = set(_taxonomy_path_titles(blog_taxonomy))
    if _taxonomy_enabled(blog_taxonomy) and not _public_library_has_real_nodes(public_library):
        route_category = _blog_category_path_from_route(post.route)
        meta_category = _coerce_string_list(post.meta.get("category_path"))
        label = f"blog/{post.route}.md"
        if not route_category:
            result.errors.append(
                f"{label}: taxonomy blogs must be stored under a category folder"
            )
        elif tuple(route_category) not in taxonomy_paths:
            result.errors.append(
                f"{label}: category_path is not defined in {BLOG_TAXONOMY_FILENAME}: "
                + "/".join(route_category)
            )
        if meta_category and meta_category != route_category:
            result.errors.append(
                f"{label}: front matter category_path must match file path"
            )
    _validate_blog_post(
        result,
        name,
        root,
        post,
        known_evidence_ids=_evidence_ids(name),
        known_claims=_claim_index(name),
        include_refs=True,
        require_publish_ready=True,
    )
    return result


def _unsafe_research_quote(text: str) -> bool:
    clean = str(text or "").lower()
    if not clean:
        return False
    markers = (
        "profiles/",
        "auth/users",
        ".env",
        "api_key",
        "apikey",
        "secret",
        "token",
        "cookie",
        "password",
    )
    return any(marker in clean for marker in markers)


def _validate_research_provenance_refs(
    result: PublicValidationResult,
    name: str,
    label: str,
    post: BlogPost,
    *,
    require_publish_ready: bool,
) -> None:
    """Validate optional Research Workspace provenance on blog front matter."""
    source_refs = _as_string_list(post.meta.get("related_sources"))
    claim_refs = _as_string_list(post.meta.get("related_research_claims"))
    citation_refs = _as_string_list(post.meta.get("related_citations"))
    if not source_refs and not claim_refs and not citation_refs:
        return
    diagnostics = result.errors if require_publish_ready else result.warnings
    try:
        from nblane.core.research_sources import load_research_sources
        from nblane.core.research_workspace import (
            load_chunks,
            load_research_citations,
            load_research_claims,
        )

        sources = load_research_sources(_profile_path(name)).by_id()
        chunks = {chunk.id: chunk for chunk in load_chunks(_profile_path(name))}
        claims = {claim.id: claim for claim in load_research_claims(_profile_path(name))}
        citations = {
            citation.id: citation
            for citation in load_research_citations(_profile_path(name))
        }
    except Exception as exc:
        diagnostics.append(f"{label}: cannot load research provenance: {exc}")
        return

    for ref in source_refs:
        source = sources.get(ref)
        if source is None:
            diagnostics.append(f"{label}: unknown research source ref '{ref}'")
            continue
        if source.visibility != "public":
            diagnostics.append(
                f"{label}: research source '{ref}' is private and cannot be published"
            )

    for ref in claim_refs:
        claim = claims.get(ref)
        if claim is None:
            diagnostics.append(f"{label}: unknown research claim ref '{ref}'")
            continue
        if claim.status != "promoted":
            diagnostics.append(
                f"{label}: research claim '{ref}' must be promoted before publish"
            )
        for source_ref in claim.source_refs:
            source = sources.get(source_ref)
            if source is None:
                diagnostics.append(
                    f"{label}: research claim '{ref}' references unknown source '{source_ref}'"
                )
            elif source.visibility != "public":
                diagnostics.append(
                    f"{label}: research claim '{ref}' references private source '{source_ref}'"
                )
        for chunk_ref in claim.chunk_refs:
            if chunk_ref not in chunks:
                diagnostics.append(
                    f"{label}: research claim '{ref}' references unknown chunk '{chunk_ref}'"
                )

    for ref in citation_refs:
        citation = citations.get(ref)
        if citation is None:
            diagnostics.append(f"{label}: unknown research citation ref '{ref}'")
            continue
        if citation.claim_id and citation.claim_id not in claims:
            diagnostics.append(
                f"{label}: research citation '{ref}' references unknown claim '{citation.claim_id}'"
            )
        if citation.source_id and citation.source_id not in sources:
            diagnostics.append(
                f"{label}: research citation '{ref}' references unknown source '{citation.source_id}'"
            )
        if citation.chunk_id and citation.chunk_id not in chunks:
            diagnostics.append(
                f"{label}: research citation '{ref}' references unknown chunk '{citation.chunk_id}'"
            )
        if _unsafe_research_quote(citation.quote):
            diagnostics.append(
                f"{label}: research citation '{ref}' quote may leak private paths or secrets"
            )


def _validate_blog_post(
    result: PublicValidationResult,
    name: str,
    profile_root: Path,
    post: BlogPost,
    *,
    known_evidence_ids: set[str],
    known_claims: dict[str, dict] | None = None,
    include_refs: bool,
    require_publish_ready: bool,
) -> None:
    label = f"blog/{post.route}.md"
    required_fields = (
        "title",
        "date",
        "status",
        "tags",
        "summary",
        "related_evidence",
        "related_kanban",
    )
    if require_publish_ready:
        _validate_required(result, label, post.meta, required_fields)
    else:
        for field_name in required_fields:
            if field_name not in post.meta or post.meta.get(field_name) is None:
                result.warnings.append(
                    f"{label}: draft missing field '{field_name}'"
                )
    status = post.status
    _validate_status(result, label, status)
    type_diagnostics = result.errors if require_publish_ready else result.warnings
    if "tags" in post.meta and not isinstance(post.meta.get("tags"), list):
        type_diagnostics.append(f"{label}: 'tags' must be a list")
    if "related_evidence" in post.meta and not isinstance(
        post.meta.get("related_evidence"),
        list,
    ):
        type_diagnostics.append(f"{label}: 'related_evidence' must be a list")
    if "related_kanban" in post.meta and not isinstance(
        post.meta.get("related_kanban"),
        list,
    ):
        type_diagnostics.append(f"{label}: 'related_kanban' must be a list")
    if "related_claims" in post.meta and not isinstance(
        post.meta.get("related_claims"),
        list,
    ):
        type_diagnostics.append(f"{label}: 'related_claims' must be a list")
    for research_field in (
        "related_sources",
        "related_research_claims",
        "related_citations",
    ):
        if research_field in post.meta and not isinstance(
            post.meta.get(research_field),
            list,
        ):
            type_diagnostics.append(f"{label}: '{research_field}' must be a list")
    cover = post.meta.get("cover", "")
    if require_publish_ready or str(cover or "").strip():
        _validate_blog_cover(
            result,
            profile_root,
            f"{label}.cover",
            cover,
        )
    if include_refs:
        _validate_evidence_refs(
            result,
            label,
            _as_string_list(post.meta.get("related_evidence")),
            known_evidence_ids,
        )
        _validate_claim_refs(
            result,
            label,
            _as_string_list(post.meta.get("related_claims")),
            known_claims or {},
            known_evidence_ids,
        )
        _validate_research_provenance_refs(
            result,
            name,
            label,
            post,
            require_publish_ready=require_publish_ready,
        )
    if require_publish_ready or post.body.strip():
        _validate_blog_body_media(
            type_diagnostics,
            profile_root,
            label,
            post.body,
        )


def validate_public_layer(
    name: str,
    *,
    include_drafts: bool = False,
) -> PublicValidationResult:
    """Validate the profile public layer."""
    root = _profile_path(name)
    result = PublicValidationResult()
    known_ids = _evidence_ids(name)
    known_claims = _claim_index(name)
    blog_taxonomy = load_blog_taxonomy(name)
    public_library = load_public_library(name)
    _validate_blog_taxonomy(result, blog_taxonomy)
    _validate_public_library(result, name, public_library)
    taxonomy_paths = set(_taxonomy_path_titles(blog_taxonomy))
    taxonomy_is_enabled = (
        _taxonomy_enabled(blog_taxonomy)
        and not _public_library_has_real_nodes(public_library)
    )

    public_profile = load_public_profile(name)
    if not public_profile:
        result.errors.append(f"missing {PUBLIC_PROFILE_FILENAME}")
    else:
        _validate_required(
            result,
            PUBLIC_PROFILE_FILENAME,
            public_profile,
            ("profile", "visibility", "public_name"),
        )
        visibility = str(
            public_profile.get("visibility", "private") or "private"
        )
        if visibility not in PUBLIC_VISIBILITIES:
            result.errors.append(
                f"{PUBLIC_PROFILE_FILENAME}: visibility must be "
                "'private' or 'public'"
            )
        _validate_media_path(
            result,
            root,
            f"{PUBLIC_PROFILE_FILENAME}.avatar",
            public_profile.get("avatar", ""),
        )
        _validate_contact_schemes(
            result,
            public_profile.get("contacts"),
        )

    resume_source = load_resume_source(name)
    if not resume_source:
        result.errors.append(f"missing {RESUME_SOURCE_FILENAME}")
    else:
        _validate_required(
            result,
            RESUME_SOURCE_FILENAME,
            resume_source,
            ("profile", "visibility"),
        )
        visibility = str(
            resume_source.get("visibility", "private") or "private"
        )
        if visibility not in PUBLIC_VISIBILITIES:
            result.errors.append(
                f"{RESUME_SOURCE_FILENAME}: visibility must be "
                "'private' or 'public'"
            )
        basics = resume_source.get("basics")
        if not isinstance(basics, dict):
            result.errors.append(
                f"{RESUME_SOURCE_FILENAME}: 'basics' must be a mapping"
            )
        elif not str(basics.get("name", "") or "").strip():
            result.errors.append(
                f"{RESUME_SOURCE_FILENAME}: basics.name is required"
            )

    for project in load_projects(name):
        pid = str(project.get("id", "") or "").strip()
        label = f"{PROJECTS_FILENAME}:{pid or '(missing id)'}"
        _validate_required(result, label, project, ("id", "title", "status"))
        status = str(project.get("status", "draft") or "draft")
        _validate_status(result, label, status)
        _validate_media_path(
            result,
            root,
            f"{label}.cover",
            project.get("cover", ""),
        )
        _validate_link_map_schemes(result, label, project.get("links"))
        if _status_visible(status, include_drafts=include_drafts):
            _validate_evidence_refs(
                result,
                label,
                _as_string_list(project.get("evidence_refs")),
                known_ids,
            )

    for output in load_outputs(name):
        oid = str(output.get("id", "") or "").strip()
        label = f"{OUTPUTS_FILENAME}:{oid or '(missing id)'}"
        _validate_required(
            result,
            label,
            output,
            ("id", "type", "title", "status"),
        )
        status = str(output.get("status", "draft") or "draft")
        _validate_status(result, label, status)
        _validate_link_map_schemes(result, label, output.get("links"))
        if _status_visible(status, include_drafts=include_drafts):
            _validate_evidence_refs(
                result,
                label,
                _as_string_list(output.get("evidence_refs")),
                known_ids,
            )

    blog_dir = root / BLOG_DIRNAME
    if blog_dir.exists():
        for path in _blog_post_candidate_paths(blog_dir):
            post = parse_blog_post(path)
            if taxonomy_is_enabled:
                route_category = _blog_category_path_from_route(post.route)
                meta_category = _coerce_string_list(post.meta.get("category_path"))
                label = f"blog/{post.route}.md"
                if not route_category:
                    result.errors.append(
                        f"{label}: taxonomy blogs must be stored under a category folder"
                    )
                elif tuple(route_category) not in taxonomy_paths:
                    result.errors.append(
                        f"{label}: category_path is not defined in {BLOG_TAXONOMY_FILENAME}: "
                        + "/".join(route_category)
                    )
                if meta_category and meta_category != route_category:
                    result.errors.append(
                        f"{label}: front matter category_path must match file path"
                    )
            include_refs = _status_visible(
                post.status,
                include_drafts=include_drafts,
            )
            _validate_blog_post(
                result,
                name,
                root,
                post,
                known_evidence_ids=known_ids,
                known_claims=known_claims,
                include_refs=include_refs,
                require_publish_ready=(post.status == "published"),
            )

    return result


def _markdown_to_html(text: str) -> str:
    text = _replace_ai_loading_comments(text)
    text = _replace_math_block_comments(text)
    text = _replace_visual_block_comments(text)
    text = _replace_video_directives(text)
    prepared, math_blocks, inline_math = _extract_markdown_math(text)
    try:
        import markdown as markdown_lib

        rendered = markdown_lib.markdown(
            prepared,
            extensions=["extra", "sane_lists"],
            output_format="html5",
        )
        return _sanitize_html_url_attrs(
            _restore_markdown_math(rendered, math_blocks, inline_math)
        )
    except Exception:
        lines = []
        image_pattern = re.compile(
            r"!\[(?P<alt>[^\]]*)\]\(\s*(?P<src><[^>]+>|[^)\s]+)"
            r"(?:\s+[\"'][^\"']*[\"'])?\s*\)"
        )
        for raw in prepared.splitlines():
            line = raw.strip()
            if not line:
                continue
            image_match = image_pattern.fullmatch(line)
            if line.startswith('<figure class="media-block') or line.startswith(
                '<p class="media-caption">'
            ):
                lines.append(line)
            elif image_match:
                src = _strip_markdown_url(image_match.group("src"))
                alt = image_match.group("alt")
                lines.append(
                    '<p><img src="'
                    + html.escape(src, quote=True)
                    + '" alt="'
                    + html.escape(alt, quote=True)
                    + '" /></p>'
                )
            elif line.startswith("### "):
                lines.append(f"<h3>{html.escape(line[4:])}</h3>")
            elif line.startswith("## "):
                lines.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.startswith("# "):
                lines.append(f"<h1>{html.escape(line[2:])}</h1>")
            elif line.startswith("- "):
                lines.append(f"<p>• {html.escape(line[2:])}</p>")
            else:
                lines.append(f"<p>{html.escape(line)}</p>")
        return _sanitize_html_url_attrs(
            _restore_markdown_math("\n".join(lines), math_blocks, inline_math)
        )


def _extract_markdown_math(text: str) -> tuple[str, list[str], list[str]]:
    """Replace math spans with stable tokens before Markdown conversion."""
    code_blocks: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        token = _CODE_TOKEN.format(index=len(code_blocks))
        code_blocks.append(match.group(0))
        return token

    work = _FENCED_CODE_RE.sub(stash_code, text)
    math_blocks: list[str] = []
    inline_math: list[str] = []

    def stash_block(body: str) -> str:
        token = _MATH_BLOCK_TOKEN.format(index=len(math_blocks))
        math_blocks.append(body.strip())
        return f"\n\n{token}\n\n"

    def replace_dollar_block(match: re.Match[str]) -> str:
        body = match.group("body_multi")
        if body is None:
            body = match.group("body_single") or ""
        return stash_block(body)

    def replace_bracket_block(match: re.Match[str]) -> str:
        body = match.group("body_multi")
        if body is None:
            body = match.group("body_single") or ""
        return stash_block(body)

    work = _DISPLAY_DOLLAR_MATH_BLOCK_RE.sub(replace_dollar_block, work)
    work = _DISPLAY_BRACKET_MATH_BLOCK_RE.sub(replace_bracket_block, work)

    def stash_inline(body: str) -> str:
        token = _MATH_INLINE_TOKEN.format(index=len(inline_math))
        inline_math.append(body.strip())
        return token

    def replace_dollar_inline(match: re.Match[str]) -> str:
        body = match.group(1)
        if not _looks_like_inline_math(body):
            return match.group(0)
        return stash_inline(body)

    def replace_paren_inline(match: re.Match[str]) -> str:
        return stash_inline(match.group(1))

    work = _INLINE_DOLLAR_MATH_RE.sub(replace_dollar_inline, work)
    work = _INLINE_PAREN_MATH_RE.sub(replace_paren_inline, work)

    for index, block in enumerate(code_blocks):
        work = work.replace(_CODE_TOKEN.format(index=index), block)
    return work, math_blocks, inline_math


def _restore_markdown_math(
    html_text: str,
    math_blocks: list[str],
    inline_math: list[str],
) -> str:
    """Restore protected TeX snippets after Markdown conversion."""
    out = html_text
    for index, body in enumerate(math_blocks):
        token = _MATH_BLOCK_TOKEN.format(index=index)
        block_html = (
            '<div class="math-display">\\[\n'
            + html.escape(body)
            + "\n\\]</div>"
        )
        out = re.sub(
            rf"<p>\s*{re.escape(token)}\s*</p>",
            lambda _match: block_html,
            out,
        )
        out = out.replace(token, block_html)
    for index, body in enumerate(inline_math):
        token = _MATH_INLINE_TOKEN.format(index=index)
        inline_html = (
            '<span class="math-inline">\\('
            + html.escape(body)
            + "\\)</span>"
        )
        out = out.replace(token, inline_html)
    return out


def _site_name(public_profile: dict) -> str:
    return str(
        public_profile.get("public_name")
        or public_profile.get("profile")
        or "nblane"
    )


def _html_page(
    *,
    title: str,
    body: str,
    public_profile: dict,
    current: str,
    description: str = "",
    canonical_url: str = "",
    og_type: str = "website",
    asset_href: str = "/assets/site.css",
    include_resume: bool = True,
    include_math: bool = False,
    image_url: str = "",
) -> str:
    site_name = _site_name(public_profile)
    avatar = str(public_profile.get("avatar", "") or "")
    nav_items = [
        ("Home", "index.html", "home"),
        ("Blog", "blog/", "blog"),
        ("Projects", "projects/", "projects"),
        ("Outputs", "outputs/", "outputs"),
    ]
    if include_resume:
        nav_items.append(("Resume", "resume/", "resume"))
    nav = "\n".join(
        (
            f'<a class="{"active" if key == current else ""}" '
            f'href="/{href}">{label}</a>'
        )
        for label, href, key in nav_items
    )
    avatar_html = ""
    if avatar:
        avatar_html = (
            f'<img class="site-avatar" src="/{html.escape(avatar)}" '
            f'alt="{html.escape(site_name)}" />'
        )
    meta_description = description or str(
        public_profile.get("bio_short", "") or public_profile.get("headline", "")
    )
    full_title = f"{title} · {site_name}"
    canonical_html = (
        f'  <link rel="canonical" href="{html.escape(canonical_url, quote=True)}">\n'
        if canonical_url
        else ""
    )
    image = _safe_url_attr(
        image_url,
        allowed_schemes=SAFE_SRC_SCHEMES,
        allow_relative=True,
    )
    image_html = ""
    if image:
        image_html = (
            f'  <meta property="og:image" content="{html.escape(image, quote=True)}">\n'
            f'  <meta name="twitter:image" content="{html.escape(image, quote=True)}">\n'
        )
    seo_html = (
        canonical_html
        + f'  <meta property="og:type" content="{html.escape(og_type, quote=True)}">\n'
        + f'  <meta property="og:title" content="{html.escape(full_title, quote=True)}">\n'
        + f'  <meta property="og:description" content="{html.escape(meta_description, quote=True)}">\n'
        + f'  <meta property="og:site_name" content="{html.escape(site_name, quote=True)}">\n'
        + (
            f'  <meta property="og:url" content="{html.escape(canonical_url, quote=True)}">\n'
            if canonical_url
            else ""
        )
        + image_html
        + f'  <meta name="twitter:card" content="{"summary_large_image" if image else "summary"}">\n'
        + f'  <meta name="twitter:title" content="{html.escape(full_title, quote=True)}">\n'
        + f'  <meta name="twitter:description" content="{html.escape(meta_description, quote=True)}">\n'
    )
    math_head = _MATHJAX_HEAD if include_math else ""
    mermaid_head = _MERMAID_HEAD if 'class="mermaid"' in body else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(full_title)}</title>
  <meta name="description" content="{html.escape(meta_description, quote=True)}">
{seo_html.rstrip()}
  <link rel="stylesheet" href="{html.escape(asset_href)}">
{math_head}
{mermaid_head}
</head>
<body>
  <header class="site-header">
    <a class="brand" href="/">
      {avatar_html}
      <span>{html.escape(site_name)}</span>
    </a>
    <nav>{nav}</nav>
  </header>
  <main>{body}</main>
  <footer>
    <span>Generated by nblane.</span>
  </footer>
</body>
</html>
"""


def _site_css() -> str:
    return """
:root {
  color-scheme: light;
  --ink: #17211f;
  --muted: #60716e;
  --line: #d8e0dc;
  --paper: #fbfcfb;
  --band: #eef5f1;
  --accent: #006d75;
  --warm: #a04f2a;
  --mark: #f3c969;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
  color: var(--ink);
  background: var(--paper);
  line-height: 1.58;
}
a { color: var(--accent); text-decoration-thickness: 0.08em; }
.site-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 14px clamp(18px, 5vw, 64px);
  border-bottom: 1px solid var(--line);
  background: rgba(251, 252, 251, 0.94);
  backdrop-filter: blur(10px);
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--ink);
  font-weight: 700;
  text-decoration: none;
}
.site-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--line);
}
nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 12px;
}
nav a {
  color: var(--muted);
  font-size: 0.95rem;
  text-decoration: none;
}
nav a.active, nav a:hover { color: var(--ink); }
.hero, .section {
  padding: clamp(36px, 7vw, 86px) clamp(18px, 5vw, 64px);
}
.hero {
  min-height: 48vh;
  display: grid;
  align-content: center;
  border-bottom: 1px solid var(--line);
  background:
    linear-gradient(120deg, rgba(0,109,117,0.12), transparent 42%),
    linear-gradient(300deg, rgba(160,79,42,0.14), transparent 45%),
    var(--band);
}
.hero-inner, .section-inner {
  width: min(1040px, 100%);
  margin: 0 auto;
}
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(180px, 280px);
  align-items: center;
  gap: clamp(28px, 6vw, 72px);
}
.hero-copy {
  min-width: 0;
}
.hero-portrait {
  width: min(280px, 54vw);
  aspect-ratio: 1;
  justify-self: end;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid rgba(23, 33, 31, 0.16);
  box-shadow: 0 18px 48px rgba(23, 33, 31, 0.16);
  background: #fff;
}
.eyebrow {
  color: var(--warm);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.78rem;
}
h1 {
  max-width: 920px;
  margin: 10px 0 16px;
  font-size: clamp(2.3rem, 7vw, 5.6rem);
  line-height: 1.02;
  letter-spacing: 0;
}
h2 {
  margin: 0 0 18px;
  font-size: clamp(1.7rem, 3.5vw, 2.8rem);
  letter-spacing: 0;
}
h3 { margin: 0 0 8px; letter-spacing: 0; }
.lead {
  max-width: 760px;
  color: var(--muted);
  font-size: clamp(1.05rem, 2vw, 1.35rem);
}
.contact-row, .tag-row, .link-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}
.section-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}
.section-head h2 { margin: 0; }
.section-head a { font-weight: 700; text-decoration: none; }
.pill {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 6px 11px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fff;
  color: var(--ink);
  text-decoration: none;
  font-size: 0.93rem;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
}
.item {
  min-height: 160px;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
}
.item-cover {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  margin: -4px 0 14px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid var(--line);
}
.portal {
  display: flex;
  min-height: 150px;
  flex-direction: column;
  justify-content: space-between;
  color: var(--ink);
  text-decoration: none;
}
.portal strong {
  display: block;
  font-size: 1.2rem;
  margin-bottom: 8px;
}
.portal:hover { border-color: var(--accent); }
.compact-list {
  display: grid;
  gap: 10px;
}
.compact-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  text-decoration: none;
}
.compact-row:hover .compact-title { color: var(--accent); }
.compact-title { font-weight: 700; }
.compact-meta {
  flex: 0 0 auto;
  color: var(--muted);
  font-size: 0.9rem;
}
.item p { color: var(--muted); margin: 0.35rem 0 0; }
.meta { color: var(--muted); font-size: 0.93rem; }
.prose {
  width: min(820px, 100%);
  margin: 0 auto;
  padding: clamp(32px, 6vw, 72px) clamp(18px, 5vw, 64px);
}
.detail {
  width: min(920px, 100%);
}
.detail h2 {
  margin-top: 34px;
  font-size: clamp(1.45rem, 2.4vw, 2.15rem);
}
.evidence-list {
  display: grid;
  gap: 14px;
}
.evidence-item {
  padding: 16px 0;
  border-top: 1px solid var(--line);
}
.evidence-item h3 {
  margin-top: 4px;
}
.prose img { max-width: 100%; border-radius: 8px; }
.blog-header {
  margin-bottom: 26px;
}
.blog-cover {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  margin: 24px 0 4px;
  border: 1px solid var(--line);
  border-radius: 8px;
  object-fit: cover;
}
.media-block {
  margin: 28px 0;
}
.media-video {
  display: block;
  width: 100%;
  max-width: 100%;
  aspect-ratio: 16 / 9;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #101816;
}
.media-embed {
  border: 0;
}
.media-caption {
  margin-top: 8px;
  color: var(--muted);
  font-size: 0.95rem;
}
.mermaid-static {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f7faf8;
}
.mermaid-static-node rect {
  fill: #ffffff;
  stroke: #7aa79b;
  stroke-width: 1.5;
}
.mermaid-static-node text {
  fill: var(--ink);
  font: 600 15px system-ui, sans-serif;
}
.mermaid-static-edge {
  fill: none;
  stroke: #426c62;
  stroke-width: 2;
}
.mermaid-static marker path {
  fill: #426c62;
}
.prose pre { overflow: auto; padding: 16px; background: #10201e; color: #eef5f1; }
.prose pre.mermaid,
.prose .mermaid {
  overflow: auto;
  margin: 0;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f6f8f7;
  color: var(--ink);
}
.prose .mermaid svg {
  display: block;
  max-width: 100%;
  height: auto;
}
.prose code { font-size: 0.95em; }
.prose mjx-container[display="true"] {
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 8px 0;
}
footer {
  padding: 28px clamp(18px, 5vw, 64px);
  border-top: 1px solid var(--line);
  color: var(--muted);
}
@media (max-width: 720px) {
  .site-header { align-items: flex-start; flex-direction: column; }
  nav { justify-content: flex-start; }
  .section-head { align-items: flex-start; flex-direction: column; }
  .compact-row { align-items: flex-start; flex-direction: column; }
  .hero-grid { grid-template-columns: 1fr; }
  .hero-portrait {
    justify-self: start;
    width: min(220px, 62vw);
    order: -1;
  }
}
"""


def _featured_items(
    items: list[dict],
    featured_ids: list[str],
    *,
    id_key: str = "id",
) -> list[dict]:
    if not featured_ids:
        return [x for x in items if x.get("featured")][:3] or items[:3]
    index = {str(x.get(id_key, "")): x for x in items}
    return [index[i] for i in featured_ids if i in index]


def _visible_projects(
    name: str,
    *,
    include_drafts: bool,
) -> list[dict]:
    return [
        p
        for p in load_projects(name)
        if _status_visible(
            str(p.get("status", "draft") or "draft"),
            include_drafts=include_drafts,
        )
    ]


def _visible_outputs(
    name: str,
    *,
    include_drafts: bool,
) -> list[dict]:
    return [
        o
        for o in load_outputs(name)
        if _status_visible(
            str(o.get("status", "draft") or "draft"),
            include_drafts=include_drafts,
        )
    ]


def _safe_path_segment(value: object, *, fallback: str = "item") -> str:
    clean = str(value or "").strip()
    clean = re.sub(r"[\\/]+", "-", clean)
    clean = re.sub(r"[^A-Za-z0-9._~\-\u4e00-\u9fff]+", "-", clean)
    clean = clean.strip(".-")
    return clean or fallback


def _detail_url(kind: str, item: dict) -> str:
    segment = quote(
        _safe_path_segment(item.get("id"), fallback=kind[:-1] or "item"),
        safe="",
    )
    return f"/{kind}/{segment}/"


def _render_project_item(project: dict) -> str:
    links = _links(project.get("links"))
    link_html = "".join(
        f'<a class="pill" href="{html.escape(href, quote=True)}">'
        f"{html.escape(label)}</a>"
        for label, url in links.items()
        for href in [_public_link_href(url)]
        if href
    )
    summary = str(project.get("summary", "") or "")
    tags = _as_string_list(project.get("tags"))
    tag_html = "".join(
        f'<span class="pill">{html.escape(t)}</span>' for t in tags
    )
    href = _detail_url("projects", project)
    title = str(project.get("title", "") or "")
    return f"""
<article class="item">
  <h3><a href="{html.escape(href)}">{html.escape(title)}</a></h3>
  <p>{html.escape(summary)}</p>
  <div class="tag-row">{tag_html}</div>
  <div class="link-row">{link_html}</div>
</article>
"""


def _render_output_item(output: dict) -> str:
    links = _links(output.get("links"))
    link_html = "".join(
        f'<a class="pill" href="{html.escape(href, quote=True)}">'
        f"{html.escape(label)}</a>"
        for label, url in links.items()
        for href in [_public_link_href(url)]
        if href
    )
    summary = str(output.get("summary", "") or "")
    kind = str(output.get("type", "") or "")
    year = str(output.get("year", "") or "")
    meta = " · ".join(x for x in (kind, year) if x)
    href = _detail_url("outputs", output)
    title = str(output.get("title", "") or "")
    return f"""
<article class="item">
  <div class="meta">{html.escape(meta)}</div>
  <h3><a href="{html.escape(href)}">{html.escape(title)}</a></h3>
  <p>{html.escape(summary)}</p>
  <div class="link-row">{link_html}</div>
</article>
"""


def _render_pills(values: list[str]) -> str:
    return "".join(
        f'<span class="pill">{html.escape(value)}</span>'
        for value in values
        if value
    )


def _render_external_links(links: dict[str, str]) -> str:
    return "".join(
        f'<a class="pill" href="{html.escape(href, quote=True)}">'
        f"{html.escape(label)}</a>"
        for label, url in links.items()
        for href in [_public_link_href(url)]
        if href
    )


def _render_evidence_summaries(
    evidence: dict[str, dict],
    refs: list[str],
) -> str:
    rows: list[str] = []
    for ref in refs:
        item = evidence.get(ref)
        if not item:
            continue
        title = str(item.get("title", "") or ref)
        summary = str(item.get("summary", "") or "")
        kind = str(item.get("type", "") or "")
        when = str(item.get("date", "") or "")
        meta = " · ".join(x for x in (ref, kind, when) if x)
        rows.append(
            "<article class=\"evidence-item\">"
            f"<div class=\"meta\">{html.escape(meta)}</div>"
            f"<h3>{html.escape(title)}</h3>"
            f"<p>{html.escape(summary)}</p>"
            "</article>"
        )
    if not rows:
        return '<p class="meta">No public evidence summaries are linked.</p>'
    return '<div class="evidence-list">' + "".join(rows) + "</div>"


def _render_project_detail(
    name: str,
    project: dict,
    evidence: dict[str, dict],
) -> str:
    title = str(project.get("title", "") or project.get("id", "Project"))
    summary = str(project.get("summary", "") or "")
    public_angle = str(project.get("public_angle", "") or "")
    tags = _as_string_list(project.get("tags"))
    refs = _as_string_list(project.get("evidence_refs"))
    skill_refs = _as_string_list(project.get("skill_refs"))
    if not skill_refs:
        skill_refs = _skill_refs_for_evidence(name, refs)
    links = _links(project.get("links"))
    angle_html = (
        f"<h2>Public Angle</h2><p>{html.escape(public_angle)}</p>"
        if public_angle
        else ""
    )
    tag_html = _render_pills(tags)
    skill_html = _render_pills(skill_refs)
    link_html = _render_external_links(links)
    no_skill = '<span class="meta">No skill refs linked.</span>'
    return f"""
<article class="prose detail">
  <p class="meta">Project</p>
  <h1>{html.escape(title)}</h1>
  <p class="lead">{html.escape(summary)}</p>
  <div class="tag-row">{tag_html}</div>
  <div class="link-row">{link_html}</div>
  {angle_html}
  <h2>Skill Signals</h2>
  <div class="tag-row">{skill_html or no_skill}</div>
  <h2>Evidence</h2>
  {_render_evidence_summaries(evidence, refs)}
</article>
"""


def _render_output_detail(
    name: str,
    output: dict,
    evidence: dict[str, dict],
) -> str:
    title = str(output.get("title", "") or output.get("id", "Output"))
    summary = str(output.get("summary", "") or "")
    kind = str(output.get("type", "") or "")
    year = str(output.get("year", "") or "")
    meta = " · ".join(x for x in (kind, year) if x)
    refs = _as_string_list(output.get("evidence_refs"))
    skill_refs = _as_string_list(output.get("skill_refs"))
    if not skill_refs:
        skill_refs = _skill_refs_for_evidence(name, refs)
    links = _links(output.get("links"))
    link_html = _render_external_links(links)
    skill_html = _render_pills(skill_refs)
    no_skill = '<span class="meta">No skill refs linked.</span>'
    return f"""
<article class="prose detail">
  <p class="meta">{html.escape(meta or "Output")}</p>
  <h1>{html.escape(title)}</h1>
  <p class="lead">{html.escape(summary)}</p>
  <div class="link-row">{link_html}</div>
  <h2>Skill Signals</h2>
  <div class="tag-row">{skill_html or no_skill}</div>
  <h2>Evidence</h2>
  {_render_evidence_summaries(evidence, refs)}
</article>
"""


def _blog_cover_img(
    profile_root: Path,
    post: BlogPost,
    *,
    css_class: str,
    alt: str = "",
) -> str:
    cover = _valid_blog_cover_ref(profile_root, post.meta.get("cover"))
    if not cover:
        return ""
    src = _media_src(cover)
    return (
        f'<img class="{html.escape(css_class)}" '
        f'src="{html.escape(src, quote=True)}" '
        f'alt="{html.escape(alt or post.title, quote=True)}">'
    )


def _seo_image_url(base_url: str, cover_ref: str) -> str:
    if not cover_ref:
        return ""
    if _is_external_url(cover_ref):
        return cover_ref
    return _site_url(base_url, "/" + cover_ref.lstrip("/"))


def _render_post_item(post: BlogPost, profile_root: Path | None = None) -> str:
    tags = _as_string_list(post.meta.get("tags"))
    tag_html = "".join(
        f'<span class="pill">{html.escape(t)}</span>' for t in tags
    )
    cover_html = (
        _blog_cover_img(profile_root, post, css_class="item-cover")
        if profile_root is not None
        else ""
    )
    return f"""
<article class="item">
  {cover_html}
  <div class="meta">{html.escape(post.date)}</div>
  <h3><a href="/{post.url_path}">{html.escape(post.title)}</a></h3>
  <p>{html.escape(post.summary)}</p>
  <div class="tag-row">{tag_html}</div>
	</article>
	"""


def _category_post_count(posts: list[BlogPost], category_path: list[str]) -> int:
    if not category_path:
        return len(posts)
    prefix = "/".join(category_path) + "/"
    return sum(1 for post in posts if post.route.startswith(prefix))


def _posts_for_category(posts: list[BlogPost], category_path: list[str]) -> list[BlogPost]:
    if not category_path:
        return posts
    prefix = "/".join(category_path) + "/"
    return [post for post in posts if post.route.startswith(prefix)]


def _render_category_cards(
    posts: list[BlogPost],
    taxonomy: dict,
    category_path: list[str],
) -> str:
    cards: list[str] = []
    for node in _taxonomy_child_nodes(taxonomy, category_path):
        slug = str(node.get("slug", "") or "").strip()
        if not slug:
            continue
        title = str(node.get("title", "") or slug).strip() or slug
        next_path = [*category_path, slug]
        href = "/" + _taxonomy_category_url_path(next_path)
        count = _category_post_count(posts, next_path)
        detail = f"{count} post" if count == 1 else f"{count} posts"
        cards.append(
            "<article class=\"item\">"
            f"<div class=\"meta\">{html.escape(detail)}</div>"
            f"<h3><a href=\"{html.escape(href)}\">{html.escape(title)}</a></h3>"
            "</article>"
        )
    return "".join(cards)


def _render_blog_listing(
    posts: list[BlogPost],
    profile_root: Path,
    *,
    taxonomy: dict | None = None,
    category_path: list[str] | None = None,
) -> str:
    category_path = category_path or []
    title = _taxonomy_category_title(taxonomy, category_path) if taxonomy else "Blog"
    visible_posts = _posts_for_category(posts, category_path)
    category_cards = (
        _render_category_cards(posts, taxonomy or {}, category_path)
        if taxonomy
        else ""
    )
    category_section = (
        "<h2>Categories</h2><div class=\"grid\">" + category_cards + "</div>"
        if category_cards
        else ""
    )
    post_section = (
        "<h2>Posts</h2>"
        if category_cards and visible_posts
        else ""
    )
    post_cards = "".join(_render_post_item(p, profile_root) for p in visible_posts)
    empty = '<p class="meta">No posts in this category.</p>' if not post_cards else ""
    return (
        '<section class="section"><div class="section-inner">'
        f"<h1>{html.escape(title)}</h1>"
        f"{category_section}{post_section}<div class=\"grid\">{post_cards}</div>{empty}"
        "</div></section>"
    )


def _taxonomy_category_paths(raw: dict) -> list[list[str]]:
    return [list(path) for path in sorted(_taxonomy_path_titles(raw))]


def _redirect_page(target_url_path: str) -> str:
    target = "/" + target_url_path.strip("/") + "/"
    escaped = html.escape(target, quote=True)
    return (
        "<!doctype html><html><head>"
        '<meta charset="utf-8">'
        f'<meta http-equiv="refresh" content="0; url={escaped}">'
        f'<link rel="canonical" href="{escaped}">'
        "</head><body>"
        f'<p><a href="{escaped}">Redirecting</a></p>'
        "</body></html>"
    )


def _render_public_library_children(
    name: str,
    post: BlogPost,
    posts_by_route: dict[str, BlogPost],
) -> str:
    """Render public child nodes attached below one blog post."""
    library = load_public_library(name)
    if not _public_library_has_real_nodes(library):
        return ""
    index = index_public_library(library)
    parent = public_library_node_for_blog(name, post.route)
    if parent is None:
        return ""
    cards: list[str] = []
    for node in index.children_by_parent.get(parent.id, []):
        if node.status == "trashed" or node.visibility != "public":
            continue
        if node.type == "post":
            child = posts_by_route.get(_blog_route_for_library_node(node))
            if child is None:
                continue
            cards.append(_render_post_item(child))
        elif node.type == "media":
            target = _local_media_target(_profile_path(name), node.ref)
            if target is None or not target.exists():
                continue
            title = node.title or Path(node.ref).name
            cards.append(
                "<article class=\"item\">"
                "<div class=\"meta\">Media</div>"
                f"<h3><a href=\"/{html.escape(node.ref, quote=True)}\">"
                f"{html.escape(title)}</a></h3>"
                "</article>"
            )
    if not cards:
        return ""
    return (
        '<section class="related-files">'
        "<h2>Related Files</h2>"
        '<div class="grid">'
        + "".join(cards)
        + "</div></section>"
    )


def _render_blog_article(
    profile_root: Path,
    post: BlogPost,
    *,
    related_files_html: str = "",
) -> str:
    cover_html = _blog_cover_img(profile_root, post, css_class="blog-cover")
    summary_html = (
        f'<p class="lead">{html.escape(post.summary)}</p>'
        if post.summary
        else ""
    )
    return (
        '<article class="prose blog-article">'
        '<header class="blog-header">'
        f'<p class="meta">{html.escape(post.date)}</p>'
        f"<h1>{html.escape(post.title)}</h1>"
        f"{summary_html}{cover_html}"
        "</header>"
        + _markdown_to_html(post.body)
        + related_files_html
        + "</article>"
    )


def _render_portal_card(
    *,
    label: str,
    href: str,
    count: int,
    detail: str,
) -> str:
    count_text = f"{count} item" if count == 1 else f"{count} items"
    return f"""
<a class="item portal" href="{html.escape(href)}">
  <span>
    <strong>{html.escape(label)}</strong>
    <span class="meta">{html.escape(count_text)}</span>
  </span>
  <span>{html.escape(detail)}</span>
</a>
"""


def _render_section_head(title: str, href: str, link_label: str) -> str:
    return (
        '<div class="section-head">'
        f"<h2>{html.escape(title)}</h2>"
        f'<a href="{html.escape(href)}">{html.escape(link_label)}</a>'
        "</div>"
    )


def _render_compact_post(post: BlogPost) -> str:
    return f"""
<a class="compact-row" href="/{post.url_path}">
  <span class="compact-title">{html.escape(post.title)}</span>
  <span class="compact-meta">{html.escape(post.date)}</span>
</a>
"""


def _render_compact_project(project: dict) -> str:
    title = str(project.get("title", "") or project.get("id", "Project"))
    status = str(project.get("status", "") or "")
    href = _detail_url("projects", project)
    return f"""
<a class="compact-row" href="{html.escape(href)}">
  <span class="compact-title">{html.escape(title)}</span>
  <span class="compact-meta">{html.escape(status)}</span>
</a>
"""


def _render_compact_output(output: dict) -> str:
    title = str(output.get("title", "") or output.get("id", "Output"))
    kind = str(output.get("type", "") or "")
    year = str(output.get("year", "") or "")
    meta = " · ".join(x for x in (kind, year) if x)
    href = _detail_url("outputs", output)
    return f"""
<a class="compact-row" href="{html.escape(href)}">
  <span class="compact-title">{html.escape(title)}</span>
  <span class="compact-meta">{html.escape(meta)}</span>
</a>
"""


def _latest_label(values: list[str], fallback: str) -> str:
    for value in values:
        if value.strip():
            return value.strip()
    return fallback


def _render_home(
    public_profile: dict,
    projects: list[dict],
    outputs: list[dict],
    posts: list[BlogPost],
    resume_source: dict,
    *,
    resume_visible: bool,
) -> str:
    contacts = _links(public_profile.get("contacts"))
    basics = resume_source.get("basics") or {}
    if not isinstance(basics, dict):
        basics = {}
    if resume_visible:
        fallback_email = str(basics.get("email", "") or "").strip()
        fallback_website = str(basics.get("website", "") or "").strip()
        if fallback_email and not contacts.get("email"):
            contacts["email"] = fallback_email
        if fallback_website and not contacts.get("website"):
            contacts["website"] = fallback_website
    contact_html = "".join(_render_contact(k, v) for k, v in contacts.items())
    headline = str(public_profile.get("headline", "") or "")
    if resume_visible and not headline:
        headline = str(basics.get("title", "") or "")
    bio_short = str(public_profile.get("bio_short", "") or "")
    if resume_visible and not bio_short:
        bio_short = str(resume_source.get("summary", "") or "")
    avatar = str(public_profile.get("avatar", "") or "")
    avatar_html = (
        f'<img class="hero-portrait" src="/{html.escape(avatar)}" '
        f'alt="{html.escape(_site_name(public_profile))}" />'
        if avatar
        else ""
    )
    resume_title = str(
        basics.get("title")
        or public_profile.get("headline")
        or "Resume"
    )
    resume_href = "/resume/" if resume_visible else "#resume"
    resume_detail = (
        resume_title
        if resume_visible
        else "Resume source is private or not ready for publishing."
    )
    latest_post = posts[0].title if posts else ""
    latest_project = _latest_label(
        [str(p.get("title", "") or "") for p in projects],
        "Open the complete project list.",
    )
    latest_output = _latest_label(
        [str(o.get("title", "") or "") for o in outputs],
        "Open the complete output list.",
    )
    portal_html = "".join(
        [
            _render_portal_card(
                label="Blog",
                href="/blog/",
                count=len(posts),
                detail=latest_post or "No published posts yet.",
            ),
            _render_portal_card(
                label="Projects",
                href="/projects/",
                count=len(projects),
                detail=latest_project,
            ),
            _render_portal_card(
                label="Outputs",
                href="/outputs/",
                count=len(outputs),
                detail=latest_output,
            ),
            _render_portal_card(
                label="Resume",
                href=resume_href,
                count=1 if resume_visible else 0,
                detail=resume_detail,
            ),
        ]
    )
    post_html = "".join(_render_compact_post(p) for p in posts[:5])
    project_html = "".join(_render_compact_project(p) for p in projects[:5])
    output_html = "".join(_render_compact_output(o) for o in outputs[:5])
    if not contact_html:
        contact_html = '<span class="meta">No public contacts yet.</span>'
    if not post_html:
        post_html = '<p class="meta">No published posts yet.</p>'
    if not project_html:
        project_html = '<p class="meta">No public projects yet.</p>'
    if not output_html:
        output_html = '<p class="meta">No public outputs yet.</p>'
    resume_links = (
        '<div class="link-row">'
        '<a class="pill" href="/resume/">View full resume</a>'
        '<a class="pill" href="/resume/resume.md">Download Markdown</a>'
        "</div>"
        if resume_visible
        else '<p class="meta">Resume is not public yet.</p>'
    )
    return f"""
<section class="hero">
  <div class="hero-inner hero-grid">
    <div class="hero-copy">
      <div class="eyebrow">Public Profile</div>
      <h1>{html.escape(_site_name(public_profile))}</h1>
      <p class="lead">{html.escape(headline)}</p>
      <p class="lead">{html.escape(bio_short)}</p>
      <div class="contact-row">{contact_html}</div>
    </div>
    {avatar_html}
  </div>
</section>
<section class="section">
  <div class="section-inner">
    <h2>Content Index</h2>
    <div class="grid">{portal_html}</div>
  </div>
</section>
<section class="section">
  <div class="section-inner">
    {_render_section_head("Blog", "/blog/", "View all posts")}
    <div class="compact-list">{post_html}</div>
  </div>
</section>
<section class="section">
  <div class="section-inner">
    {_render_section_head("Projects", "/projects/", "View all projects")}
    <div class="compact-list">{project_html}</div>
  </div>
</section>
<section class="section">
  <div class="section-inner">
    {_render_section_head("Outputs", "/outputs/", "View all outputs")}
    <div class="compact-list">{output_html}</div>
  </div>
</section>
<section class="section" id="resume">
  <div class="section-inner">
    {_render_section_head("Resume", resume_href, "View full resume" if resume_visible else "Not public yet")}
    <p class="lead">{html.escape(resume_detail)}</p>
    {resume_links}
  </div>
</section>
"""


CONTACT_LABELS = {
    "email": "Email",
    "wechat": "WeChat",
    "github": "GitHub",
    "linkedin": "LinkedIn",
    "google_scholar": "Google Scholar",
    "zhihu": "Zhihu",
    "website": "Website",
}


def _render_contact(kind: str, value: str) -> str:
    label = html.escape(_contact_label(kind, value))
    href = _contact_url(kind, value)
    if href:
        return f'<a class="pill" href="{html.escape(href, quote=True)}">{label}</a>'
    return f'<span class="pill">{label}</span>'


def _contact_url(kind: str, value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    if _unsafe_url_scheme(value, SAFE_HREF_SCHEMES):
        return ""
    if kind == "email":
        if value.startswith("mailto:"):
            return value
        if "@" in value:
            return "mailto:" + value
        return _public_link_href(value)
    if _is_external_url(value):
        return value
    if _looks_like_domain(value):
        return "https://" + value
    compact = value.lstrip("@").strip()
    if kind == "github" and compact and "/" not in compact:
        return "https://github.com/" + quote(compact)
    if kind == "linkedin" and compact and "/" not in compact:
        return "https://www.linkedin.com/in/" + quote(compact)
    if kind == "zhihu" and compact and "/" not in compact:
        return "https://www.zhihu.com/people/" + quote(compact)
    if kind == "google_scholar" and compact and "/" not in compact:
        return (
            "https://scholar.google.com/citations?user="
            + quote(compact, safe="")
        )
    if kind == "wechat":
        return ""
    if kind == "website":
        return "https://" + value
    return _public_link_href(value)


def _contact_label(kind: str, value: str) -> str:
    label = CONTACT_LABELS.get(kind, kind.replace("_", " ").title())
    display_value = _contact_display_value(kind, value)
    if not display_value:
        return label
    return f"{label}: {display_value}"


def _contact_display_value(kind: str, value: str) -> str:
    value = str(value or "").strip()
    if _unsafe_url_scheme(value, SAFE_HREF_SCHEMES):
        return ""
    if kind == "email":
        return value.removeprefix("mailto:")
    if not value:
        return ""
    if _is_external_url(value) or _looks_like_domain(value):
        parsed_value = value if _is_external_url(value) else "https://" + value
        parsed = urlparse(parsed_value)
        if parsed.netloc:
            display = parsed.netloc + parsed.path.rstrip("/")
            if parsed.query:
                display += "?" + parsed.query
            return display
    compact = value.lstrip("@").strip()
    if kind == "wechat":
        return value
    if kind in {"github", "linkedin", "zhihu"} and compact:
        return "@" + compact
    return value


def _write_text(path: Path, text: str, pages: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    pages.append(path)


def _copy_media_refs(
    profile_root: Path,
    output_dir: Path,
    refs: list[str],
) -> None:
    media_root = (profile_root / MEDIA_DIRNAME).resolve()
    for rel in sorted(set(refs)):
        if not rel or _is_external_url(rel):
            continue
        clean = _strip_markdown_url(rel).lstrip("/")
        src = (profile_root / clean).resolve()
        try:
            src.relative_to(media_root)
        except ValueError:
            continue
        if not src.exists() or not src.is_file():
            continue
        dest = output_dir / clean
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def _collect_media_refs(
    public_profile: dict,
    projects: list[dict],
    posts: list[BlogPost],
) -> list[str]:
    refs = []
    avatar = str(public_profile.get("avatar", "") or "")
    if avatar:
        refs.append(avatar)
    for project in projects:
        cover = str(project.get("cover", "") or "")
        if cover:
            refs.append(cover)
    for post in posts:
        cover = str(post.meta.get("cover", "") or "")
        if cover:
            refs.append(cover)
        refs.extend(_blog_body_media_refs(post.body))
    return refs


def _replace_directory(tmp_dir: Path, output_dir: Path) -> None:
    old_dir = output_dir.with_name(f".{output_dir.name}.old")
    if old_dir.exists():
        shutil.rmtree(old_dir)
    if output_dir.exists():
        output_dir.rename(old_dir)
    try:
        tmp_dir.rename(output_dir)
    except Exception:
        if old_dir.exists() and not output_dir.exists():
            old_dir.rename(output_dir)
        raise
    if old_dir.exists():
        shutil.rmtree(old_dir)


def _normalize_base_url(base_url: str) -> str:
    clean = str(base_url or "").strip().rstrip("/")
    if not clean:
        return ""
    parsed = urlparse(clean)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PublicSiteError("--base-url must be an absolute http(s) URL")
    if parsed.query or parsed.fragment:
        raise PublicSiteError("--base-url must not include query or fragment")
    return clean


def _base_path_from_url(base_url: str) -> str:
    """Return the deployment path prefix implied by an absolute base URL."""
    if not base_url:
        return ""
    parsed = urlparse(base_url)
    path = parsed.path.strip("/")
    return f"/{path}" if path else ""


def _url_path_for_page(rel: str | Path) -> str:
    rel_text = str(rel).replace("\\", "/")
    url_path = "/" if rel_text == "index.html" else "/" + rel_text
    if url_path.endswith("/index.html"):
        url_path = url_path[: -len("index.html")]
    return url_path


def _site_path(base_path: str, url_path: str) -> str:
    """Prefix an absolute site path for sub-path deployments."""
    prefix = str(base_path or "").strip().rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = "/" + prefix
    clean_path = str(url_path or "/").strip()
    if not clean_path.startswith("/"):
        clean_path = "/" + clean_path
    if prefix and (clean_path == prefix or clean_path.startswith(prefix + "/")):
        return clean_path
    if clean_path == "/":
        return prefix + "/" if prefix else "/"
    return prefix + clean_path


def _site_url(base_url: str, url_path: str) -> str:
    clean_path = url_path if url_path.startswith("/") else "/" + url_path
    return base_url + clean_path if base_url else clean_path


def _apply_public_url_paths(html_text: str, *, base_path: str) -> str:
    """Route generated local href/src values through the deployment prefix."""

    def replace_attr(match: re.Match[str]) -> str:
        attr = match.group("attr")
        url = match.group("url")
        clean = url.strip()
        if (
            not clean
            or clean.startswith("#")
            or clean.startswith("//")
            or _url_scheme(clean)
        ):
            return match.group(0)
        if clean.startswith("/"):
            next_url = _site_path(base_path, clean)
        elif clean.startswith("media/") or clean.startswith("assets/"):
            next_url = _site_path(base_path, "/" + clean)
        else:
            return match.group(0)
        return f'{attr}="{html.escape(next_url, quote=True)}"'

    return re.sub(
        r'(?P<attr>src|href)="(?P<url>[^"]*)"',
        replace_attr,
        html_text,
    )


def _merge_public_profile_override(base: dict, override: dict | None) -> dict:
    """Return a public profile copy with preview-only overrides applied."""
    merged = dict(base)
    if not override:
        return merged
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged.get(key) or {})
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def _add_render_page(
    pages: dict[str, str],
    titles: dict[str, str],
    rel: str,
    title: str,
    text: str,
) -> None:
    pages[rel] = text
    titles[rel] = title


def render_public_site_pages(
    name: str,
    *,
    include_drafts: bool = False,
    base_url: str = "",
    public_profile_override: dict | None = None,
) -> PublicSiteRenderResult:
    """Render public site pages in memory without writing files."""
    base_url = _normalize_base_url(base_url)
    base_path = _base_path_from_url(base_url)
    profile_root = _profile_path(name)

    def page_url(rel: str) -> str:
        return _site_url(base_url, _url_path_for_page(rel))

    public_profile = _merge_public_profile_override(
        load_public_profile(name),
        public_profile_override,
    )
    blog_taxonomy = load_blog_taxonomy(name)
    public_library = load_public_library(name)
    taxonomy_is_enabled = (
        _taxonomy_enabled(blog_taxonomy)
        and not _public_library_has_real_nodes(public_library)
    )
    projects = _visible_projects(name, include_drafts=include_drafts)
    outputs = _visible_outputs(name, include_drafts=include_drafts)
    posts = load_blog_posts(name, include_drafts=include_drafts)
    evidence = _evidence_index(name)
    resume_source = load_resume_source(name)
    resume_visible = _visibility_visible(
        str(resume_source.get("visibility", "private") or "private"),
        include_drafts=include_drafts,
    )

    pages: dict[str, str] = {}
    page_titles: dict[str, str] = {}
    css = _site_css()

    _add_render_page(
        pages,
        page_titles,
        "index.html",
        "Home",
        _html_page(
            title="Home",
            body=_render_home(
                public_profile,
                projects,
                outputs,
                posts,
                resume_source,
                resume_visible=resume_visible,
            ),
            public_profile=public_profile,
            current="home",
            canonical_url=page_url("index.html"),
            include_resume=resume_visible,
        ),
    )

    project_body = (
        '<section class="section"><div class="section-inner">'
        "<h1>Projects</h1><div class=\"grid\">"
        + "".join(_render_project_item(p) for p in projects)
        + "</div></div></section>"
    )
    _add_render_page(
        pages,
        page_titles,
        "projects/index.html",
        "Projects",
        _html_page(
            title="Projects",
            body=project_body,
            public_profile=public_profile,
            current="projects",
            canonical_url=page_url("projects/index.html"),
            include_resume=resume_visible,
        ),
    )
    for project in projects:
        segment = _safe_path_segment(
            project.get("id"),
            fallback="project",
        )
        title = str(project.get("title", "") or "Project")
        _add_render_page(
            pages,
            page_titles,
            f"projects/{segment}/index.html",
            title,
            _html_page(
                title=title,
                body=_render_project_detail(name, project, evidence),
                public_profile=public_profile,
                current="projects",
                description=str(project.get("summary", "") or ""),
                canonical_url=page_url(f"projects/{segment}/index.html"),
                include_resume=resume_visible,
            ),
        )

    output_body = (
        '<section class="section"><div class="section-inner">'
        "<h1>Outputs</h1><div class=\"grid\">"
        + "".join(_render_output_item(o) for o in outputs)
        + "</div></div></section>"
    )
    _add_render_page(
        pages,
        page_titles,
        "outputs/index.html",
        "Outputs",
        _html_page(
            title="Outputs",
            body=output_body,
            public_profile=public_profile,
            current="outputs",
            canonical_url=page_url("outputs/index.html"),
            include_resume=resume_visible,
        ),
    )
    for output in outputs:
        segment = _safe_path_segment(
            output.get("id"),
            fallback="output",
        )
        title = str(output.get("title", "") or "Output")
        _add_render_page(
            pages,
            page_titles,
            f"outputs/{segment}/index.html",
            title,
            _html_page(
                title=title,
                body=_render_output_detail(name, output, evidence),
                public_profile=public_profile,
                current="outputs",
                description=str(output.get("summary", "") or ""),
                canonical_url=page_url(f"outputs/{segment}/index.html"),
                include_resume=resume_visible,
            ),
        )

    blog_body = _render_blog_listing(
        posts,
        profile_root,
        taxonomy=blog_taxonomy if taxonomy_is_enabled else None,
    )
    _add_render_page(
        pages,
        page_titles,
        "blog/index.html",
        "Blog",
        _html_page(
            title="Blog",
            body=blog_body,
            public_profile=public_profile,
            current="blog",
            canonical_url=page_url("blog/index.html"),
            include_resume=resume_visible,
        ),
    )
    if taxonomy_is_enabled:
        for category_path in _taxonomy_category_paths(blog_taxonomy):
            category_url_path = _taxonomy_category_url_path(category_path)
            category_rel = f"{category_url_path}index.html"
            category_title = _taxonomy_category_title(blog_taxonomy, category_path)
            _add_render_page(
                pages,
                page_titles,
                category_rel,
                category_title,
                _html_page(
                    title=category_title,
                    body=_render_blog_listing(
                        posts,
                        profile_root,
                        taxonomy=blog_taxonomy,
                        category_path=category_path,
                    ),
                    public_profile=public_profile,
                    current="blog",
                    canonical_url=page_url(category_rel),
                    include_resume=resume_visible,
                ),
            )
    posts_by_route = {post.route: post for post in posts}
    for post in posts:
        cover_ref = _valid_blog_cover_ref(
            profile_root,
            post.meta.get("cover"),
        )
        article = _render_blog_article(
            profile_root,
            post,
            related_files_html=_render_public_library_children(
                name,
                post,
                posts_by_route,
            ),
        )
        post_rel = f"{post.url_path}index.html"
        _add_render_page(
            pages,
            page_titles,
            post_rel,
            post.title,
            _html_page(
                title=post.title,
                body=article,
                public_profile=public_profile,
                current="blog",
                description=post.summary,
                canonical_url=page_url(post_rel),
                og_type="article",
                include_resume=resume_visible,
                include_math=markdown_contains_math(post.body),
                image_url=_seo_image_url(base_url, cover_ref),
            ),
        )
        for alias in _blog_aliases(post.meta):
            alias_rel = alias.strip("/") + "/index.html"
            if alias_rel not in pages:
                _add_render_page(
                    pages,
                    page_titles,
                    alias_rel,
                    post.title,
                    _redirect_page(_site_path(base_path, "/" + post.url_path)),
                )

    resume_md = ""
    if resume_visible:
        resume_md = render_resume_markdown(resume_source)
        resume_html = (
            '<article class="prose">'
            + _markdown_to_html(resume_md)
            + "</article>"
        )
        _add_render_page(
            pages,
            page_titles,
            "resume/index.html",
            "Resume",
            _html_page(
                title="Resume",
                body=resume_html,
                public_profile=public_profile,
                current="resume",
                canonical_url=page_url("resume/index.html"),
                include_resume=True,
                include_math=markdown_contains_math(resume_md),
            ),
        )

    pages = {
        rel: _apply_public_url_paths(text, base_path=base_path)
        for rel, text in pages.items()
    }

    return PublicSiteRenderResult(
        pages=pages,
        page_titles=page_titles,
        css=css,
        media_refs=_collect_media_refs(public_profile, projects, posts),
        resume_markdown=resume_md,
        sitemap_exclude={
            alias.strip("/") + "/index.html"
            for post in posts
            for alias in _blog_aliases(post.meta)
        },
    )


def build_public_site(
    name: str,
    *,
    out_dir: str | Path | None = None,
    include_drafts: bool = False,
    base_url: str = "",
) -> PublicBuildResult:
    """Build a static public site from the public layer."""
    normalized_base_url = _normalize_base_url(base_url)
    result = validate_public_layer(name, include_drafts=include_drafts)
    result.raise_for_errors()
    profile_root = _profile_path(name)
    public_profile = load_public_profile(name)
    profile_visibility = str(
        public_profile.get("visibility", "private") or "private"
    )
    if not _visibility_visible(profile_visibility, include_drafts=include_drafts):
        raise PublicSiteError(
            f"{PUBLIC_PROFILE_FILENAME}: visibility must be public "
            "for a public build; pass --include-drafts for preview."
        )
    rendered = render_public_site_pages(
        name,
        include_drafts=include_drafts,
        base_url=normalized_base_url,
    )

    output_dir = (
        Path(out_dir)
        if out_dir is not None
        else REPO_ROOT / "dist" / "public" / name
    ).resolve()
    tmp_dir = output_dir.with_name(f".{output_dir.name}.tmp")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pages: list[Path] = []

    assets_dir = tmp_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "site.css").write_text(rendered.css, encoding="utf-8")

    _copy_media_refs(
        profile_root,
        tmp_dir,
        rendered.media_refs,
    )

    for rel, text in rendered.pages.items():
        _write_text(
            tmp_dir / rel,
            text,
            pages,
        )

    if rendered.resume_markdown:
        _write_text(
            tmp_dir / "resume" / "resume.md",
            rendered.resume_markdown,
            pages,
        )

    _write_text(
        tmp_dir / "robots.txt",
        (
            "User-agent: *\nAllow: /\n"
            f"Sitemap: {_site_url(normalized_base_url, '/sitemap.xml')}\n"
        ),
        pages,
    )
    sitemap = _render_sitemap(
        pages,
        tmp_dir,
        base_url=normalized_base_url,
        exclude=rendered.sitemap_exclude,
    )
    _write_text(tmp_dir / "sitemap.xml", sitemap, pages)

    _replace_directory(tmp_dir, output_dir)
    return PublicBuildResult(
        output_dir=output_dir,
        pages=[output_dir / p.relative_to(tmp_dir) for p in pages],
    )


def _normalize_media_ref(value: str) -> str:
    clean = value.strip()
    while clean.startswith("/"):
        clean = clean[1:]
    return clean


def _normalize_preview_quality(value: str) -> str:
    return "full" if str(value or "").strip().lower() == "full" else "fast"


def _data_uri(data: bytes, mime: str) -> str:
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _svg_placeholder_data_uri(label: str) -> str:
    safe = html.escape(str(label or "Missing media")[:120])
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" '
        'viewBox="0 0 960 540" role="img">'
        '<rect width="960" height="540" fill="#f6f8f7"/>'
        '<rect x="24" y="24" width="912" height="492" rx="18" '
        'fill="none" stroke="#d8e0dc" stroke-width="4"/>'
        '<text x="480" y="258" text-anchor="middle" '
        'font-family="Inter, Arial, sans-serif" font-size="28" '
        'font-weight="700" fill="#60716e">Preview media unavailable</text>'
        f'<text x="480" y="306" text-anchor="middle" '
        'font-family="Inter, Arial, sans-serif" font-size="20" '
        f'fill="#60716e">{safe}</text>'
        "</svg>"
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _image_preview_from_bytes(
    data: bytes,
    source_name: str,
    *,
    preview_quality: str = "fast",
) -> tuple[str, str, int, int]:
    """Return an image data URI, using a small preview when Pillow is available."""
    source_mime = mimetypes.guess_type(source_name)[0] or "application/octet-stream"
    quality = _normalize_preview_quality(preview_quality)
    width = 0
    height = 0
    if quality == "full":
        return _data_uri(data, source_mime), source_mime, width, height
    try:
        from PIL import Image, ImageOps

        with Image.open(io.BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            width, height = image.size
            preview = image.copy()
        preview.thumbnail(
            (BLOG_IMAGE_PREVIEW_MAX_EDGE, BLOG_IMAGE_PREVIEW_MAX_EDGE),
            Image.Resampling.LANCZOS,
        )
        has_alpha = preview.mode in {"RGBA", "LA"} or (
            preview.mode == "P" and "transparency" in preview.info
        )
        out = io.BytesIO()
        try:
            if has_alpha:
                preview.save(out, format="WEBP", quality=BLOG_IMAGE_PREVIEW_QUALITY)
                return _data_uri(out.getvalue(), "image/webp"), "image/webp", width, height
            rgb = preview.convert("RGB")
            rgb.save(
                out,
                format="JPEG",
                quality=BLOG_IMAGE_PREVIEW_QUALITY,
                optimize=True,
            )
            return _data_uri(out.getvalue(), "image/jpeg"), "image/jpeg", width, height
        except Exception:
            out = io.BytesIO()
            if has_alpha:
                preview.save(out, format="PNG", optimize=True)
                return _data_uri(out.getvalue(), "image/png"), "image/png", width, height
            rgb = preview.convert("RGB")
            rgb.save(out, format="JPEG", quality=BLOG_IMAGE_PREVIEW_QUALITY)
            return _data_uri(out.getvalue(), "image/jpeg"), "image/jpeg", width, height
    except Exception:
        return _data_uri(data, source_mime), source_mime, width, height


def _image_dimensions_from_bytes(data: bytes) -> tuple[int, int]:
    try:
        from PIL import Image, ImageOps

        with Image.open(io.BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            return image.size
    except Exception:
        return 0, 0


def _media_preview_payload_from_bytes(
    data: bytes,
    *,
    source_name: str,
    kind: str,
    mime: str = "",
    preview_quality: str = "fast",
) -> dict:
    clean_kind = str(kind or "").strip().lower() or "image"
    clean_mime = mime or mimetypes.guess_type(source_name)[0] or "application/octet-stream"
    size_kb = round(len(data) / 1024, 1)
    if clean_kind == "image" or clean_mime.startswith("image/"):
        src, preview_mime, width, height = _image_preview_from_bytes(
            data,
            source_name,
            preview_quality=preview_quality,
        )
        if not width or not height:
            width, height = _image_dimensions_from_bytes(data)
        return {
            "preview_src": src,
            "preview_mime": preview_mime,
            "preview_width": width,
            "preview_height": height,
            "original_size_kb": size_kb,
            "full_preview_available": len(data) <= BLOG_IMAGE_MAX_BYTES,
        }
    inline_available = len(data) <= BLOG_PREVIEW_VIDEO_INLINE_MAX_BYTES
    full_available = len(data) <= BLOG_VIDEO_MAX_BYTES
    return {
        "preview_src": _data_uri(data, clean_mime) if inline_available else "",
        "preview_mime": clean_mime,
        "preview_width": 0,
        "preview_height": 0,
        "original_size_kb": size_kb,
        "full_preview_available": full_available,
        **_video_compatibility_payload_from_bytes(data, source_name),
    }


def _blog_media_preview_payload(
    path: Path,
    kind: str,
    *,
    preview_quality: str = "fast",
) -> dict:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if kind == "video" and path.stat().st_size > BLOG_PREVIEW_VIDEO_INLINE_MAX_BYTES:
        return {
            "preview_src": "",
            "preview_mime": mime,
            "preview_width": 0,
            "preview_height": 0,
            "original_size_kb": round(path.stat().st_size / 1024, 1),
            "full_preview_available": path.stat().st_size <= BLOG_VIDEO_MAX_BYTES,
            **_video_compatibility_payload(path),
        }
    return _media_preview_payload_from_bytes(
        path.read_bytes(),
        source_name=path.name,
        kind=kind,
        mime=mime,
        preview_quality=preview_quality,
    )


def blog_media_full_preview_payload(
    profile_root: Path,
    rel: str,
    *,
    data: bytes | None = None,
    filename: str = "",
    kind: str = "",
    mime: str = "",
) -> dict:
    """Return an on-demand full preview payload for one local media item."""
    clean = _normalize_media_ref(_strip_markdown_url(rel))
    source_name = filename or Path(clean).name or "media.bin"
    payload_data = data
    if payload_data is None:
        if not clean or _is_external_url(clean):
            return {}
        target = _local_media_target(profile_root, clean)
        if target is None or not target.exists() or not target.is_file():
            return {}
        source_name = target.name
        payload_data = target.read_bytes()
    clean_mime = mime or mimetypes.guess_type(source_name)[0] or "application/octet-stream"
    clean_kind = str(kind or "").strip().lower()
    if not clean_kind:
        clean_kind = "video" if clean_mime.startswith("video/") else "image"
    if clean_kind == "video" and len(payload_data) > BLOG_VIDEO_MAX_BYTES:
        return {
            "full_preview_available": False,
            "full_preview_src": "",
            "full_preview_mime": clean_mime,
        }
    if clean_kind == "image" and len(payload_data) > BLOG_IMAGE_MAX_BYTES:
        return {
            "full_preview_available": False,
            "full_preview_src": "",
            "full_preview_mime": clean_mime,
        }
    width, height = (
        _image_dimensions_from_bytes(payload_data)
        if clean_kind == "image" or clean_mime.startswith("image/")
        else (0, 0)
    )
    return {
        "full_preview_available": True,
        "full_preview_src": _data_uri(payload_data, clean_mime),
        "full_preview_mime": clean_mime,
        "full_preview_width": width,
        "full_preview_height": height,
        "original_size_kb": round(len(payload_data) / 1024, 1),
    }


def _data_uri_for_media(
    profile_root: Path,
    rel: str,
    media_overrides: dict[str, bytes],
    warnings: list[str],
    *,
    preview_quality: str = "fast",
) -> str:
    clean = _normalize_media_ref(rel)
    if not clean or _is_external_url(clean):
        return rel
    override = media_overrides.get(clean)
    suffix_source = clean
    data: bytes | None = override
    if data is None:
        media_root = (profile_root / MEDIA_DIRNAME).resolve()
        target = (profile_root / clean).resolve()
        try:
            target.relative_to(media_root)
        except ValueError:
            warnings.append(
                f"preview skipped media outside {MEDIA_DIRNAME}/: {clean}"
            )
            return ""
        if not target.exists() or not target.is_file():
            warnings.append(f"preview media not found: {clean}")
            return ""
        data = target.read_bytes()
        suffix_source = target.name
    mime = mimetypes.guess_type(suffix_source)[0] or "application/octet-stream"
    if mime.startswith("image/"):
        src, _preview_mime, _width, _height = _image_preview_from_bytes(
            data,
            suffix_source,
            preview_quality=preview_quality,
        )
        return src
    if (
        mime.startswith("video/")
        and _normalize_preview_quality(preview_quality) == "fast"
        and len(data) > BLOG_PREVIEW_VIDEO_INLINE_MAX_BYTES
    ):
        warnings.append(
            f"fast preview skipped large video media; use full preview to play it: {clean}"
        )
        return ""
    if mime.startswith("video/") and len(data) > BLOG_VIDEO_MAX_BYTES:
        warnings.append(
            f"preview skipped video larger than {BLOG_VIDEO_MAX_BYTES // (1024 * 1024)}MB: {clean}"
        )
        return ""
    return _data_uri(data, mime)


def _inline_preview_assets(
    html_text: str,
    *,
    css: str,
    profile_root: Path,
    media_overrides: dict[str, bytes],
    warnings: list[str],
    preview_quality: str = "fast",
) -> str:
    text = html_text.replace(
        '<link rel="stylesheet" href="/assets/site.css">',
        f"<style>{css}</style>",
    )
    text = text.replace(
        '<link rel="stylesheet" href="assets/site.css">',
        f"<style>{css}</style>",
    )

    def replace_media(match: re.Match[str]) -> str:
        attr = match.group("attr")
        url = match.group("url")
        uri = _data_uri_for_media(
            profile_root,
            url,
            media_overrides,
            warnings,
            preview_quality=preview_quality,
        )
        if not uri and attr == "src":
            uri = _svg_placeholder_data_uri(_normalize_media_ref(url))
        return f'{attr}="{html.escape(uri, quote=True)}"' if uri else f'{attr}=""'

    text = re.sub(
        r'(?P<attr>src|href)="(?P<url>/?media/[^"]+)"',
        replace_media,
        text,
    )
    guard_script = """
<script>
document.addEventListener("click", function (event) {
  const anchor = event.target.closest("a");
  if (!anchor) return;
  const href = anchor.getAttribute("href") || "";
  if (href.startsWith("/") || href.endsWith("/")) {
    event.preventDefault();
  }
});
</script>
"""
    return text.replace("</body>", guard_script + "\n</body>")


def render_public_site_preview(
    name: str,
    *,
    include_drafts: bool = True,
    public_profile_override: dict | None = None,
    media_overrides: dict[str, bytes] | None = None,
    preview_quality: str = "fast",
) -> PublicSitePreviewResult:
    """Render preview pages with inline CSS and media data URIs."""
    profile_root = _profile_path(name)
    rendered = render_public_site_pages(
        name,
        include_drafts=include_drafts,
        public_profile_override=public_profile_override,
    )
    validation = validate_public_layer(name, include_drafts=include_drafts)
    warnings = list(validation.warnings)
    warnings.extend(f"preview validation: {error}" for error in validation.errors)
    normalized_overrides = {
        _normalize_media_ref(key): value
        for key, value in (media_overrides or {}).items()
    }
    pages = {
        rel: _inline_preview_assets(
            text,
            css=rendered.css,
            profile_root=profile_root,
            media_overrides=normalized_overrides,
            warnings=warnings,
            preview_quality=preview_quality,
        )
        for rel, text in rendered.pages.items()
    }
    return PublicSitePreviewResult(
        pages=pages,
        page_titles=dict(rendered.page_titles),
        warnings=warnings,
    )


def blog_preview_fingerprint(
    profile_root: Path,
    meta: dict,
    body: str,
    *,
    preview_quality: str = "fast",
) -> str:
    """Return a stable fingerprint for one in-editor blog preview."""
    refs = set(_blog_body_media_refs(str(body or "")))
    cover = _strip_markdown_url(str((meta or {}).get("cover", "") or "")).lstrip("/")
    if cover and _is_local_media_ref(cover):
        refs.add(cover)
    media_state: list[dict] = []
    for ref in sorted(refs):
        target = _local_media_target(profile_root, ref)
        if target is None:
            media_state.append({"ref": ref, "state": "outside"})
            continue
        if not target.exists() or not target.is_file():
            media_state.append({"ref": ref, "state": "missing"})
            continue
        stat = target.stat()
        media_state.append(
            {
                "ref": ref,
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    raw = json.dumps(
        {
            "meta": _normalize_blog_meta(meta or {}),
            "body": str(body or ""),
            "preview_quality": _normalize_preview_quality(preview_quality),
            "media": media_state,
        },
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def render_blog_post_preview(
    name: str,
    slug: str,
    meta: dict,
    body: str,
    *,
    preview_quality: str = "fast",
) -> str:
    """Render one blog post preview from unsaved meta/body without writing files."""
    profile_root = _profile_path(name)
    public_profile = load_public_profile(name)
    clean_slug = _slugify_route(slug)
    category_path = _blog_category_path_from_route(clean_slug)
    clean_meta = _normalize_blog_meta(meta)
    if category_path and not clean_meta.get("category_path"):
        clean_meta["category_path"] = category_path
    post = BlogPost(
        slug=clean_slug,
        path=profile_root / BLOG_DIRNAME / f"{clean_slug}.md",
        meta=clean_meta,
        body=str(body or ""),
        category_path=category_path,
    )
    cover_ref = _valid_blog_cover_ref(profile_root, post.meta.get("cover"))
    html_text = _html_page(
        title=post.title,
        body=_render_blog_article(profile_root, post),
        public_profile=public_profile,
        current="blog",
        description=post.summary,
        og_type="article",
        include_math=markdown_contains_math(post.body),
        image_url=_media_src(cover_ref) if cover_ref else "",
    )
    warnings: list[str] = []
    return _inline_preview_assets(
        html_text,
        css=_site_css(),
        profile_root=profile_root,
        media_overrides={},
        warnings=warnings,
        preview_quality=preview_quality,
    )


def _render_sitemap(
    pages: list[Path],
    root: Path,
    *,
    base_url: str,
    exclude: set[str] | None = None,
) -> str:
    urls = []
    excluded = {str(item).strip("/") for item in (exclude or set())}
    for path in pages:
        if path.suffix not in (".html", ".xml", ".txt"):
            continue
        if path.name not in ("index.html", "sitemap.xml"):
            continue
        rel = path.relative_to(root)
        if rel.as_posix().strip("/") in excluded:
            continue
        loc = _site_url(base_url, _url_path_for_page(rel))
        urls.append(f"  <url><loc>{html.escape(loc)}</loc></url>")
    body = "\n".join(urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )


def render_resume_markdown(resume_source: dict) -> str:
    """Render resume-source.yaml into Markdown."""
    basics = resume_source.get("basics") or {}
    if not isinstance(basics, dict):
        basics = {}
    name = str(basics.get("name", "") or resume_source.get("profile", ""))
    title = str(basics.get("title", "") or "")
    lines = [f"# {name}", ""]
    if title:
        lines += [f"**{title}**", ""]
    contact_bits = [
        str(basics.get("location", "") or ""),
        str(basics.get("email", "") or ""),
        str(basics.get("website", "") or ""),
    ]
    contact_line = " · ".join(x for x in contact_bits if x)
    if contact_line:
        lines += [contact_line, ""]
    summary = str(resume_source.get("summary", "") or "")
    if summary:
        lines += ["## Summary", "", summary, ""]
    _append_resume_list(lines, "Skills", resume_source.get("skills"))
    _append_resume_records(lines, "Experience", resume_source.get("experiences"))
    _append_resume_records(lines, "Projects", resume_source.get("projects"))
    _append_resume_records(lines, "Outputs", resume_source.get("outputs"))
    _append_resume_records(lines, "Education", resume_source.get("education"))
    return "\n".join(lines).rstrip() + "\n"


def _append_resume_list(lines: list[str], title: str, raw: object) -> None:
    items = _as_string_list(raw)
    if not items:
        return
    lines += [f"## {title}", ""]
    for item in items:
        lines.append(f"- {item}")
    lines.append("")


def _append_resume_records(lines: list[str], title: str, raw: object) -> None:
    if not isinstance(raw, list) or not raw:
        return
    records = [r for r in raw if isinstance(r, dict)]
    if not records:
        return
    lines += [f"## {title}", ""]
    for record in records:
        heading = str(
            record.get("role")
            or record.get("title")
            or record.get("degree")
            or record.get("company")
            or ""
        )
        org = str(record.get("company") or record.get("org") or "")
        period = " - ".join(
            x
            for x in (
                str(record.get("start", "") or ""),
                str(record.get("end", "") or ""),
            )
            if x
        )
        meta = " · ".join(x for x in (org, period) if x)
        if heading:
            lines.append(f"### {heading}")
        if meta:
            lines.append(meta)
        bullets = record.get("bullets") or []
        if isinstance(bullets, list):
            for bullet in bullets:
                text = str(bullet).strip()
                if text:
                    lines.append(f"- {text}")
        summary = str(record.get("summary", "") or "").strip()
        if summary:
            lines.append(summary)
        lines.append("")


def generate_resume_files(
    name: str,
    *,
    out_path: str | Path | None = None,
    target: str = "",
    markdown_text: str | None = None,
) -> tuple[Path, Path]:
    """Generate resume HTML and Markdown files under resumes/generated."""
    root = _profile_path(name)
    if out_path is None:
        html_path = (
            root
            / RESUMES_DIRNAME
            / GENERATED_RESUME_DIRNAME
            / "default.html"
        )
    else:
        html_path = Path(out_path)
        if html_path.suffix.lower() != ".html":
            html_path = html_path.with_suffix(".html")
    md_path = html_path.with_suffix(".md")
    resume_source = load_resume_source(name)
    resume_md = markdown_text or render_resume_markdown(resume_source)
    if target:
        resume_md = f"<!-- Target: {target} -->\n\n" + resume_md
    html_body = '<article class="prose">' + _markdown_to_html(resume_md) + "</article>"
    public_profile = load_public_profile(name) or _default_public_profile(name)
    html_text = _html_page(
        title="Resume",
        body=html_body,
        public_profile=public_profile,
        current="resume",
        asset_href="assets/site.css",
        include_math=markdown_contains_math(resume_md),
    )
    html_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    assets_dir = html_path.parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    css_path = assets_dir / "site.css"
    css_path.write_text(_site_css(), encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")
    md_path.write_text(resume_md, encoding="utf-8")
    git_backup.record_change(
        [html_path, md_path, css_path],
        action=f"generate {name} public resume",
    )
    return html_path, md_path


def _slugify(text: str) -> str:
    clean = text.strip().lower()
    clean = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", clean)
    clean = clean.strip("-")
    if not clean:
        clean = "draft"
    return clean[:72]


def _slugify_route(text: str) -> str:
    """Return a slash-separated, filesystem-safe blog route."""
    parts = []
    for part in re.split(r"[\\/]+", str(text or "")):
        clean = _slugify(part)
        if clean:
            parts.append(clean)
    return "/".join(parts) or "draft"


def _blog_route_text(name: str, slug: str | Path) -> str:
    """Normalize public blog slug/route inputs for API compatibility."""
    if isinstance(slug, Path):
        path = slug
        blog_dir = _profile_path(name) / BLOG_DIRNAME
        try:
            rel = path.resolve().relative_to(blog_dir.resolve())
            parts = list(rel.parts)
            if not parts:
                return ""
            if path.name.endswith(".blocknote.json"):
                parts[-1] = _blog_slug_from_sidecar_path(path)
            elif path.suffix:
                parts[-1] = path.stem
            return "/".join(parts)
        except ValueError:
            return _blog_slug_from_sidecar_path(path) if path.name.endswith(".blocknote.json") else path.stem
    if not isinstance(slug, str):
        raise PublicSiteError("Blog slug must be a string or Path.")
    return slug


def _resolve_blog_route(name: str, slug: str | Path) -> str:
    """Resolve a route, accepting legacy leaf slugs when unambiguous."""
    route = _slugify_route(_blog_route_text(name, slug))
    blog_dir = _profile_path(name) / BLOG_DIRNAME
    direct = blog_dir / f"{route}.md"
    if direct.exists() or _blog_sidecar_path_for_markdown(direct).exists():
        return route
    if "/" in route or not blog_dir.exists():
        return route
    matches = [
        candidate_route
        for candidate_route in (
            _blog_route_from_document_path(path, blog_dir)
            for path in _blog_post_candidate_paths(blog_dir)
        )
        if _blog_route_leaf(candidate_route) == route
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise PublicSiteError(
            f"Ambiguous blog slug '{slug}'. Use the full route: "
            + ", ".join(sorted(matches))
        )
    return route


def _safe_blog_path(name: str, slug: str) -> Path:
    clean = _slugify_route(slug)
    path = _profile_path(name) / BLOG_DIRNAME / f"{clean}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def blog_path_for_slug(name: str, slug: str) -> Path:
    """Return the canonical Markdown path for a blog slug."""
    return _safe_blog_path(name, _resolve_blog_route(name, slug))


def blog_sidecar_path_for_slug(name: str, slug: str) -> Path:
    """Return the canonical BlockNote sidecar path for a blog slug."""

    return _blog_sidecar_path_for_markdown(blog_path_for_slug(name, slug))


def load_blog_post(
    name: str,
    slug: str | Path,
    *,
    include_trashed: bool = False,
) -> BlogPost:
    """Load a blog post by slug."""
    route = _resolve_blog_route(name, slug)
    if not include_trashed and is_blog_route_trashed(name, route):
        raise PublicSiteError(f"Blog post is in public library trash: {route}")
    path = _safe_blog_path(name, route)
    sidecar_path = _blog_sidecar_path_for_markdown(path)
    if not path.exists() and not sidecar_path.exists():
        raise PublicSiteError(f"Unknown blog post: {slug}")
    return parse_blog_post(path)


def _write_blog_sidecar(
    name: str,
    path: Path,
    meta: dict,
    body: str,
    blocks_json: list[dict] | None,
) -> Path:
    """Write the canonical BlockNote sidecar for one blog post."""

    sidecar = _blog_sidecar_path_for_markdown(path)
    route = _blog_route_from_document_path(path) or path.stem
    if blocks_json is None:
        existing = _read_blog_sidecar(sidecar)
        if existing is not None:
            blocks_json = [
                block.model_dump(mode="json", exclude_none=True)
                for block in existing.blocks
            ]
    document = BlockNoteDocument(
        document_id=route,
        profile=name,
        slug=route,
        meta=_normalize_blog_meta(meta),
        blocks=coerce_blocks(blocks_json),
        markdown=str(body or ""),
        source_md_sha256=hashlib.sha256(
            _format_front_matter(meta, body).encode("utf-8")
        ).hexdigest(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    payload = json.dumps(
        document_to_dict(document),
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    )
    atomic_write_text(sidecar, payload + "\n")
    return sidecar


def _write_blog_post_file(
    name: str,
    path: Path,
    meta: dict,
    body: str,
    *,
    action: str,
    changed_paths: list[Path] | None = None,
    blocks_json: list[dict] | None = None,
) -> Path:
    sidecar = _write_blog_sidecar(name, path, meta, body, blocks_json)
    paths = [sidecar, path]
    if changed_paths:
        paths.extend(changed_paths)
    atomic_write_text(path, _format_front_matter(meta, body))
    git_backup.record_change(paths, action=action)
    return path


def _blog_media_dir(name: str, slug: str) -> Path:
    clean_slug = _slugify_route(slug)
    path = _profile_path(name) / MEDIA_DIRNAME / BLOG_DIRNAME / clean_slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_media_filename(source_name: str, *, fallback: str) -> str:
    path = Path(source_name)
    stem = re.sub(r"[^A-Za-z0-9._~\-\u4e00-\u9fff]+", "-", path.stem)
    stem = stem.strip(".-") or fallback
    suffix = path.suffix.lower()
    return f"{stem[:60]}{suffix}"


def _unique_media_path(media_dir: Path, filename: str, data: bytes) -> Path:
    target = media_dir / filename
    if not target.exists():
        return target
    digest = hashlib.sha256(data).hexdigest()[:10]
    stem = target.stem[:48]
    return media_dir / f"{stem}-{digest}{target.suffix}"


def _media_relative_path(name: str, path: Path) -> str:
    root = _profile_path(name).resolve()
    return path.resolve().relative_to(root).as_posix()


def blog_media_library_rows(
    profile_root: Path,
    slug: str,
    meta: dict,
    body: str,
) -> list[dict]:
    """Return local blog media rows with preview data for editor components."""
    media_dir = profile_root / MEDIA_DIRNAME / BLOG_DIRNAME / _slugify_route(slug)
    if not media_dir.exists():
        return []
    cover = str((meta or {}).get("cover", "") or "")
    rows: list[dict] = []
    for path in sorted(media_dir.iterdir()):
        if not path.is_file():
            continue
        ext = path.suffix.lower().lstrip(".")
        if ext in BLOG_IMAGE_EXTENSIONS:
            kind = "image"
        elif ext in BLOG_VIDEO_EXTENSIONS:
            kind = "video"
        else:
            continue
        rel = path.resolve().relative_to(profile_root.resolve()).as_posix()
        preview_payload = _blog_media_preview_payload(path, kind)
        rows.append(
            {
                "name": path.name,
                "kind": kind,
                "relative_path": rel,
                "size_kb": round(path.stat().st_size / 1024, 1),
                "referenced": rel in body or rel == cover,
                **preview_payload,
            }
        )
    return rows


_VISUAL_KIND_TO_ASSET_TYPE = {
    "cover": "image",
    "flowchart": "diagram",
    "sequence": "diagram",
    "state": "diagram",
    "class": "diagram",
    "mindmap": "diagram",
    "example": "image",
    "video_edit": "video",
}


def _normalize_visual_kind(value: str) -> str:
    clean = str(value or "").strip().lower()
    if clean in {"diagram", "mermaid"}:
        return "flowchart"
    return clean if clean in _VISUAL_KIND_TO_ASSET_TYPE else ""


def _visual_asset_type(asset_type: str, visual_kind: str = "") -> str:
    clean_type = str(asset_type or "").strip().lower()
    clean_kind = _normalize_visual_kind(visual_kind or clean_type)
    if clean_kind:
        return _VISUAL_KIND_TO_ASSET_TYPE[clean_kind]
    return clean_type if clean_type in {"image", "video", "diagram"} else "image"


def blog_visual_result_rows(
    profile_root: Path,
    slug: str,
    results: list[BlogMediaResult],
    *,
    asset_type: str,
    alt: str = "",
    caption: str = "",
    meta: dict | None = None,
    body: str = "",
) -> list[dict]:
    """Return editor payload rows for newly generated visual candidates."""
    clean_visual_kind = _normalize_visual_kind(asset_type)
    clean_asset_type = _visual_asset_type(asset_type, clean_visual_kind)
    media_rows = blog_media_library_rows(
        profile_root,
        slug,
        meta or {},
        body,
    )
    rows_by_rel = {str(row.get("relative_path", "")): row for row in media_rows}
    payload: list[dict] = []
    for result in results:
        row = dict(rows_by_rel.get(result.relative_path, {}))
        if not row:
            path = result.path
            kind = (
                "video"
                if path.suffix.lower().lstrip(".") in BLOG_VIDEO_EXTENSIONS
                else "image"
            )
            preview_payload = _blog_media_preview_payload(path, kind)
            row = {
                "name": path.name,
                "kind": kind,
                "relative_path": result.relative_path,
                "size_kb": round(path.stat().st_size / 1024, 1),
                "referenced": result.relative_path in body
                or result.relative_path == str((meta or {}).get("cover", "") or ""),
                **preview_payload,
            }
        row.update(
            {
                "asset_type": clean_asset_type,
                "visual_kind": clean_visual_kind,
                "alt": str(alt or ""),
                "caption": str(caption or ""),
                "snippet": result.snippet,
                "generated": True,
            }
        )
        payload.append(row)
    return payload


def blog_visual_candidate_rows(
    slug: str,
    assets: list[visual_generation.GeneratedVisualAsset],
    *,
    asset_type: str,
    alt: str = "",
    caption: str = "",
) -> list[dict]:
    """Return editor rows for unsaved visual candidates."""
    clean_type = str(asset_type or "").strip().lower() or "cover"
    clean_visual_kind = _normalize_visual_kind(clean_type)
    clean_asset_type = _visual_asset_type(clean_type, clean_visual_kind)
    kind = _generated_media_kind(clean_type)
    rows: list[dict] = []
    for index, asset in enumerate(assets):
        filename = visual_generation.generated_filename(
            clean_type,
            asset.data,
            asset.extension,
        )
        rel = f"{MEDIA_DIRNAME}/{BLOG_DIRNAME}/{_slugify_route(slug)}/{filename}"
        preview_payload = _media_preview_payload_from_bytes(
            asset.data,
            source_name=filename,
            kind=kind,
            mime=asset.mime_type,
        )
        candidate_id = hashlib.sha256(
            b"|".join(
                [
                    clean_type.encode("utf-8"),
                    str(index).encode("ascii"),
                    asset.data,
                ]
            )
        ).hexdigest()[:16]
        rows.append(
            {
                "id": candidate_id,
                "name": filename,
                "kind": kind,
                "relative_path": rel,
                "size_kb": round(len(asset.data) / 1024, 1),
                "referenced": False,
                **preview_payload,
                "asset_type": clean_asset_type,
                "visual_kind": clean_visual_kind,
                "alt": str(alt or ""),
                "caption": str(caption or ""),
                "snippet": _blog_media_snippet(
                    kind=kind,
                    rel=rel,
                    alt=alt,
                    caption=caption,
                ),
                "generated": True,
                "unsaved": True,
            }
        )
    return rows


def _image_ext_from_data_uri(kind: str) -> str:
    ext = kind.lower()
    return "jpg" if ext == "jpeg" else ext


def extract_blog_base64_images(
    name: str,
    slug: str,
    body: str,
) -> tuple[str, list[Path]]:
    """Extract Markdown data-URI images into media/blog/<slug-or-route>/ files."""
    media_dir = _blog_media_dir(name, slug)
    changed: list[Path] = []
    pattern = re.compile(
        r"!\[(?P<alt>[^\]]*)\]\("
        r"data:image/(?P<kind>png|jpeg|jpg|webp|gif);base64,"
        r"(?P<data>[A-Za-z0-9+/=\r\n]+)\)"
    )

    def repl(match: re.Match[str]) -> str:
        alt = match.group("alt")
        ext = _image_ext_from_data_uri(match.group("kind"))
        raw_data = re.sub(r"\s+", "", match.group("data"))
        try:
            data = base64.b64decode(raw_data, validate=True)
        except Exception as exc:
            raise PublicSiteError("Invalid base64 image in blog body") from exc
        if len(data) > BLOG_IMAGE_MAX_BYTES:
            raise PublicSiteError("Inline blog image is larger than 10MB")
        digest = hashlib.sha256(data).hexdigest()[:12]
        target = media_dir / f"img-{digest}.{ext}"
        if not target.exists():
            target.write_bytes(data)
            changed.append(target)
        rel = _media_relative_path(name, target)
        return f"![{alt}]({rel})"

    return pattern.sub(repl, body), changed


def save_blog_post(
    name: str,
    slug: str,
    meta: dict,
    body: str,
    *,
    extract_inline_images: bool = True,
    blocks_json: list[dict] | None = None,
    action: str | None = None,
) -> tuple[Path, list[Path]]:
    """Save a blog post from structured metadata and Markdown body."""
    route = _resolve_blog_route(name, slug)
    if is_blog_route_trashed(name, route):
        raise PublicSiteError(f"Blog post is in public library trash: {route}")
    path = _safe_blog_path(name, route)
    sidecar_path = _blog_sidecar_path_for_markdown(path)
    if not path.exists() and not sidecar_path.exists():
        raise PublicSiteError(f"Unknown blog post: {slug}")
    changed: list[Path] = []
    meta = _normalize_blog_meta(meta)
    category_path = _blog_category_path_from_route(route)
    if category_path and not meta.get("category_path"):
        meta["category_path"] = category_path
    if extract_inline_images:
        body, changed = extract_blog_base64_images(
            name,
            route,
            body,
        )
    _write_blog_post_file(
        name,
        path,
        meta,
        body,
        action=action or f"update {name}/blog/{path.name}",
        changed_paths=changed,
        blocks_json=blocks_json,
    )
    return path, changed


def _blog_media_snippet(
    *,
    kind: str,
    rel: str,
    alt: str = "",
    caption: str = "",
) -> str:
    if kind == "image":
        return f"![{alt or caption}]({rel})"
    return f"::video[{caption or alt}]({rel})"


def insert_blog_snippet(body: str, snippet: str) -> str:
    """Insert a snippet at the blog marker, or append it if no marker exists."""
    clean_snippet = snippet.strip()
    if not clean_snippet:
        return body
    if BLOG_INSERT_MARKER in body:
        return body.replace(
            BLOG_INSERT_MARKER,
            f"{clean_snippet}\n\n{BLOG_INSERT_MARKER}",
            1,
        )
    base = body.rstrip()
    return f"{base}\n\n{clean_snippet}\n" if base else f"{clean_snippet}\n"


def _add_blog_media_data(
    name: str,
    slug: str,
    *,
    data: bytes,
    filename: str,
    kind: str,
    alt: str = "",
    caption: str = "",
    cover: bool = False,
    append: bool = False,
) -> BlogMediaResult:
    """Copy a media file into media/blog/<slug-or-route>/ and optionally update a post."""
    post = load_blog_post(name, slug)
    media_kind = kind.strip().lower()
    if media_kind not in {"image", "video"}:
        raise PublicSiteError("Media kind must be image or video")
    ext = Path(filename).suffix.lower().lstrip(".")
    allowed = BLOG_IMAGE_EXTENSIONS if media_kind == "image" else BLOG_VIDEO_EXTENSIONS
    max_bytes = BLOG_IMAGE_MAX_BYTES if media_kind == "image" else BLOG_VIDEO_MAX_BYTES
    if ext not in allowed:
        raise PublicSiteError(
            f"Unsupported {media_kind} extension '.{ext}'"
        )
    if len(data) > max_bytes:
        raise PublicSiteError(
            f"{media_kind.title()} is larger than {max_bytes // (1024 * 1024)}MB"
        )
    media_data = data
    media_filename = filename
    if media_kind == "video":
        media_data, media_filename = _browser_compatible_video_data(data, filename)
        ext = Path(media_filename).suffix.lower().lstrip(".")
        if ext not in allowed:
            raise PublicSiteError(
                f"Unsupported {media_kind} extension '.{ext}'"
            )
        if len(media_data) > max_bytes:
            raise PublicSiteError(
                f"{media_kind.title()} is larger than {max_bytes // (1024 * 1024)}MB"
            )
    media_dir = _blog_media_dir(name, post.slug)
    clean_filename = _safe_media_filename(media_filename, fallback=media_kind)
    target = _unique_media_path(media_dir, clean_filename, media_data)
    if not target.exists():
        target.write_bytes(media_data)
    rel = _media_relative_path(name, target)
    snippet = _blog_media_snippet(
        kind=media_kind,
        rel=rel,
        alt=alt,
        caption=caption,
    )
    changed_paths = [target]
    if cover and media_kind != "image":
        raise PublicSiteError("Only image media can be used as a blog cover")
    if append or cover:
        meta = dict(post.meta)
        body = post.body
        if append:
            body = insert_blog_snippet(body, snippet)
        if cover:
            meta["cover"] = rel
        _write_blog_post_file(
            name,
            post.path,
            meta,
            body,
            action=f"add {name}/blog/{post.slug} media",
            changed_paths=changed_paths,
        )
        changed_paths = [target, post.path]
    else:
        git_backup.record_change(
            [target],
            action=f"add {name}/blog/{post.slug} media",
        )
    return BlogMediaResult(
        path=target,
        relative_path=rel,
        snippet=snippet,
        post_path=post.path if append or cover else None,
        changed_paths=changed_paths,
    )


def add_blog_media(
    name: str,
    slug: str,
    *,
    source: str | Path,
    kind: str,
    alt: str = "",
    caption: str = "",
    cover: bool = False,
    append: bool = False,
) -> BlogMediaResult:
    """Copy a media file into media/blog/<slug-or-route>/ and optionally update a post."""
    source_path = Path(source)
    if not source_path.exists() or not source_path.is_file():
        raise PublicSiteError(f"Media file does not exist: {source_path}")
    return _add_blog_media_data(
        name,
        slug,
        data=source_path.read_bytes(),
        filename=source_path.name,
        kind=kind,
        alt=alt,
        caption=caption,
        cover=cover,
        append=append,
    )


def add_blog_media_bytes(
    name: str,
    slug: str,
    *,
    data: bytes,
    filename: str,
    kind: str,
    alt: str = "",
    caption: str = "",
    cover: bool = False,
    append: bool = False,
) -> BlogMediaResult:
    """Add uploaded media bytes to a blog post."""
    return _add_blog_media_data(
        name,
        slug,
        data=data,
        filename=filename,
        kind=kind,
        alt=alt,
        caption=caption,
        cover=cover,
        append=append,
    )


def delete_blog_media(
    name: str,
    slug: str,
    rel: str,
    *,
    meta: dict | None = None,
    body: str | None = None,
    allow_referenced: bool = False,
) -> Path:
    """Delete one local blog media file after safety checks."""
    post = load_blog_post(name, slug)
    profile_root = _profile_path(name)
    clean = _normalize_media_ref(_strip_markdown_url(str(rel or ""))).lstrip("/")
    if not clean or _is_external_url(clean):
        raise PublicSiteError("Media path is missing or external.")
    target = _local_media_target(profile_root, clean)
    if target is None:
        raise PublicSiteError(f"Media path must stay under '{MEDIA_DIRNAME}/': {clean}")
    media_dir = (
        profile_root / MEDIA_DIRNAME / BLOG_DIRNAME / _slugify_route(post.slug)
    ).resolve()
    try:
        target.resolve().relative_to(media_dir)
    except ValueError as exc:
        raise PublicSiteError(
            f"Blog media must stay under '{MEDIA_DIRNAME}/{BLOG_DIRNAME}/{_slugify_route(post.slug)}/': {clean}"
        ) from exc
    if not target.exists() or not target.is_file():
        raise PublicSiteError(f"Media file does not exist: {clean}")
    ext = target.suffix.lower().lstrip(".")
    if ext not in BLOG_IMAGE_EXTENSIONS and ext not in BLOG_VIDEO_EXTENSIONS:
        raise PublicSiteError(f"Unsupported media file: {clean}")
    active_meta = post.meta if meta is None else meta
    active_body = post.body if body is None else body
    cover = _normalize_media_ref(
        _strip_markdown_url(str((active_meta or {}).get("cover", "") or ""))
    ).lstrip("/")
    referenced = clean == cover or clean in str(active_body or "")
    if referenced and not allow_referenced:
        raise PublicSiteError(
            "Media is still referenced by this post; remove it from the body or cover before deleting."
        )
    target.unlink()
    try:
        target.parent.rmdir()
    except OSError:
        pass
    git_backup.record_change(
        [target],
        action=f"delete {name}/blog/{post.slug} media",
    )
    return target


def _unique_transcoded_video_path(source: Path) -> Path:
    stem = source.stem[:52].rstrip(".-") or "video"
    base = source.with_name(f"{stem}-h264.mp4")
    if not base.exists():
        return base
    for index in range(2, 100):
        candidate = source.with_name(f"{stem}-h264-{index}.mp4")
        if not candidate.exists():
            return candidate
    raise PublicSiteError("Could not choose a unique converted video filename.")


def convert_blog_media_video(name: str, slug: str, rel: str) -> BlogMediaResult:
    """Create a browser-compatible H.264 MP4 copy of a blog video."""
    post = load_blog_post(name, slug)
    profile_root = _profile_path(name)
    clean = _normalize_media_ref(_strip_markdown_url(str(rel or ""))).lstrip("/")
    if not clean or _is_external_url(clean):
        raise PublicSiteError("Media path is missing or external.")
    target = _local_media_target(profile_root, clean)
    if target is None or not target.exists() or not target.is_file():
        raise PublicSiteError(f"Media file does not exist: {clean}")
    media_dir = (
        profile_root / MEDIA_DIRNAME / BLOG_DIRNAME / _slugify_route(post.slug)
    ).resolve()
    try:
        target.resolve().relative_to(media_dir)
    except ValueError as exc:
        raise PublicSiteError(
            f"Blog media must stay under '{MEDIA_DIRNAME}/{BLOG_DIRNAME}/{_slugify_route(post.slug)}/': {clean}"
        ) from exc
    if target.suffix.lower().lstrip(".") not in BLOG_VIDEO_EXTENSIONS:
        raise PublicSiteError(f"Media is not a supported blog video: {clean}")
    output = _unique_transcoded_video_path(target)
    with tempfile.NamedTemporaryFile(
        dir=target.parent,
        prefix=f".{target.stem}-h264-",
        suffix=".mp4",
        delete=False,
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        _transcode_video_file(target, tmp_path)
        if tmp_path.stat().st_size > BLOG_VIDEO_MAX_BYTES:
            raise PublicSiteError(
                f"Converted video is larger than {BLOG_VIDEO_MAX_BYTES // (1024 * 1024)}MB"
            )
        tmp_path.replace(output)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    new_rel = _media_relative_path(name, output)
    git_backup.record_change(
        [output],
        action=f"convert {name}/blog/{post.slug} video",
    )
    return BlogMediaResult(
        path=output,
        relative_path=new_rel,
        snippet=_blog_media_snippet(kind="video", rel=new_rel),
        changed_paths=[output],
    )


def _generated_media_kind(asset_type: str) -> str:
    return "video" if str(asset_type or "").strip().lower() == "video_edit" else "image"


def generate_blog_visual_asset(
    name: str,
    slug: str,
    asset_type: str,
    prompt: str,
    *,
    style: str = "",
    size: str = "",
    alt: str = "",
    caption: str = "",
    source_video: str = "",
    reference_image: str = "",
) -> list[BlogMediaResult]:
    """Generate visual assets into media/blog/<slug-or-route>/ without editing the post."""
    post = load_blog_post(name, slug)
    clean_type = str(asset_type or "").strip().lower() or "cover"
    generated = visual_generation.generate_visual_asset(
        clean_type,
        prompt,
        style=style,
        size=size,
        title=post.title,
        summary=post.summary,
        tags=_coerce_string_list(post.meta.get("tags")),
        body=post.body,
        source_video=source_video,
        reference_image=reference_image,
    )
    results: list[BlogMediaResult] = []
    kind = _generated_media_kind(clean_type)
    for asset in generated:
        filename = visual_generation.generated_filename(
            clean_type,
            asset.data,
            asset.extension,
        )
        results.append(
            _add_blog_media_data(
                name,
                post.slug,
                data=asset.data,
                filename=filename,
                kind=kind,
                alt=alt,
                caption=caption,
                cover=False,
                append=False,
            )
        )
    return results


def generate_blog_cover_image(
    name: str,
    slug: str,
    prompt: str,
    *,
    style: str = "",
    size: str = "",
    alt: str = "",
    caption: str = "",
) -> list[BlogMediaResult]:
    """Generate cover image candidates into the blog media library."""
    return generate_blog_visual_asset(
        name,
        slug,
        "cover",
        prompt,
        style=style,
        size=size,
        alt=alt,
        caption=caption,
    )


def generate_blog_video_edit_candidate(
    name: str,
    slug: str,
    prompt: str,
    *,
    source_video: str,
    reference_image: str = "",
    style: str = "",
    caption: str = "",
) -> list[BlogMediaResult]:
    """Generate a video-edit candidate with the configured video model."""
    return generate_blog_visual_asset(
        name,
        slug,
        "video_edit",
        prompt,
        style=style,
        caption=caption,
        source_video=source_video,
        reference_image=reference_image,
    )


def publish_blog_post(name: str, slug: str | Path) -> Path:
    """Set a blog post status to published after publish validation."""
    slug_text = _resolve_blog_route(name, slug)
    post = load_blog_post(name, slug_text)
    meta = dict(post.meta)
    meta["status"] = "published"
    candidate = _format_front_matter(meta, post.body)
    result = validate_blog_text_for_publish(name, post.path, candidate)
    result.raise_for_errors()
    _write_blog_post_file(
        name,
        post.path,
        meta,
        post.body,
        action=f"publish {name}/blog/{post.path.name}",
        blocks_json=post.blocks_json,
    )
    return post.path


def publish_blog_text(
    name: str,
    slug: str,
    meta: dict,
    body: str,
    *,
    blocks_json: list[dict] | None = None,
) -> Path:
    """Publish unsaved structured blog text after full validation."""
    post = load_blog_post(name, slug)
    publish_meta = _normalize_blog_meta(meta)
    publish_meta["status"] = "published"
    candidate = _format_front_matter(publish_meta, body)
    result = validate_blog_text_for_publish(name, post.path, candidate)
    result.raise_for_errors()
    _write_blog_post_file(
        name,
        post.path,
        publish_meta,
        body,
        action=f"publish {name}/blog/{post.path.name}",
        blocks_json=blocks_json if blocks_json is not None else post.blocks_json,
    )
    return post.path


def create_blog_draft(
    name: str,
    *,
    title: str,
    body: str,
    tags: list[str] | None = None,
    summary: str = "",
    related_evidence: list[str] | None = None,
    related_kanban: list[str] | None = None,
    related_claims: list[str] | None = None,
    related_sources: list[str] | None = None,
    related_research_claims: list[str] | None = None,
    related_citations: list[str] | None = None,
    slug: str | None = None,
    category_path: list[str] | None = None,
    respect_taxonomy: bool = True,
) -> Path:
    """Write a draft blog post and return its path."""
    today = date.today().isoformat()
    slug_text = slug or f"{today}-{title}"
    clean_category = [
        _slugify(part)
        for part in (category_path or [])
        if _slugify(part)
    ]
    taxonomy = load_blog_taxonomy(name) if respect_taxonomy else {}
    if clean_category and "/" not in slug_text:
        slug_text = "/".join([*clean_category, slug_text])
    elif _taxonomy_enabled(taxonomy) and "/" not in slug_text:
        taxonomy_paths = _taxonomy_path_titles(taxonomy)
        if ("uncategorized",) in taxonomy_paths:
            slug_text = f"uncategorized/{slug_text}"
    path = _safe_blog_path(name, slug_text)
    if path.exists() or _blog_sidecar_path_for_markdown(path).exists():
        route = _blog_route_from_document_path(path) or path.stem
        path = _safe_blog_path(name, f"{route}-{today}")
    post_category = _blog_category_path_from_route(_blog_route_from_document_path(path))
    meta = {
        "title": title,
        "date": today,
        "status": "draft",
        "tags": tags or [],
        "summary": summary,
        "cover": "",
        "category_path": post_category,
        "related_evidence": related_evidence or [],
        "related_kanban": related_kanban or [],
        "related_claims": related_claims or [],
        "related_sources": related_sources or [],
        "related_research_claims": related_research_claims or [],
        "related_citations": related_citations or [],
    }
    _write_blog_post_file(
        name,
        path,
        meta,
        body,
        action=f"create {name} blog draft",
        blocks_json=[],
    )
    return path


def _chat_or_fallback(system: str, user: str, fallback: str) -> str:
    if not llm.is_configured():
        return fallback
    reply = llm.chat(system, user, temperature=0.35)
    if reply.startswith("LLM error:") or reply.startswith("AI features"):
        return fallback
    return reply.strip() or fallback


def _strip_fenced_yaml(text: str) -> str:
    clean = text.strip()
    if clean.startswith("```"):
        lines = clean.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        clean = "\n".join(lines).strip()
    return clean


def _candidate_string_list(raw: object) -> list[str]:
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    if isinstance(raw, str):
        return [
            item.strip()
            for chunk in raw.splitlines()
            for item in chunk.split(",")
            if item.strip()
        ]
    return []


def _candidate_from_mapping(
    data: dict,
    *,
    fallback_title: str,
    fallback_body: str,
) -> BlogDraftCandidate:
    title = str(data.get("title", "") or fallback_title).strip() or fallback_title
    body = str(data.get("body", "") or fallback_body).strip() or fallback_body
    return BlogDraftCandidate(
        title=title,
        body=body + ("" if body.endswith("\n") else "\n"),
        summary=str(data.get("summary", "") or "").strip(),
        tags=_candidate_string_list(data.get("tags")),
        related_evidence=_candidate_string_list(data.get("related_evidence")),
        related_kanban=_candidate_string_list(data.get("related_kanban")),
        related_claims=_candidate_string_list(data.get("related_claims")),
        cover_prompt=str(data.get("cover_prompt", "") or "").strip(),
        warnings=_candidate_string_list(data.get("warnings")),
    )


def blog_candidate_from_title(name: str, title: str) -> BlogDraftCandidate:
    """Return a full blog candidate from a title without writing files."""
    clean_title = title.strip()
    if not clean_title:
        raise PublicSiteError("Blog title is required")
    fallback_body = (
        "## Opening\n\n"
        "Draft the hook here. Keep claims grounded in verified facts.\n\n"
        "## Main points\n\n"
        "- Add the first reviewed point.\n"
        "- Add the second reviewed point.\n"
        "- Add links, demos, metrics, or caveats after verification.\n\n"
        "## Takeaways\n\n"
        "Summarize what readers should remember.\n"
    )
    fallback = _dump_yaml(
        {
            "title": clean_title,
            "summary": f"Draft article candidate for {clean_title}.",
            "tags": ["draft"],
            "cover_prompt": (
                "A clean editorial cover image for a technical blog post "
                f"about {clean_title}, no text, realistic lighting"
            ),
            "warnings": [
                "Title-only generation is not evidence-grounded; verify all claims before publishing.",
            ],
            "body": fallback_body,
        }
    )
    system = get_prompt("scaffold_title", llm.reply_language())
    user = _dump_yaml(
        {
            "profile": name,
            "title": clean_title,
            "constraints": [
                "candidate only",
                "no invented facts",
                "Markdown body",
                "include summary, tags, and cover_prompt",
            ],
        }
    )
    raw = _chat_or_fallback(system, user, fallback)
    try:
        loaded = yaml.safe_load(_strip_fenced_yaml(raw)) or {}
    except Exception as exc:
        raise PublicSiteError("AI title candidate was not valid YAML") from exc
    if not isinstance(loaded, dict):
        raise PublicSiteError("AI title candidate must be a YAML mapping")
    candidate = _candidate_from_mapping(
        loaded,
        fallback_title=clean_title,
        fallback_body=fallback_body,
    )
    if not candidate.warnings:
        candidate.warnings.append(
            "Title-only generation is not evidence-grounded; verify all claims before publishing."
        )
    return candidate


def blog_candidate_from_evidence(
    name: str,
    evidence_id: str,
) -> BlogDraftCandidate:
    """Return a blog draft candidate from one public evidence record."""
    evidence = _evidence_index(name).get(evidence_id)
    if evidence is None:
        raise PublicSiteError(f"Unknown evidence id: {evidence_id}")
    title = str(evidence.get("title", "") or evidence_id)
    summary = str(evidence.get("summary", "") or "")
    fallback = (
        f"## What happened\n\n{summary or title}\n\n"
        "## Why it matters\n\n"
        "Add the public interpretation here after review.\n\n"
        "## Notes\n\n"
        "Confirm links, metrics, and claims before publishing.\n"
    )
    system = get_prompt("scaffold_evidence", llm.reply_language())
    user = _dump_yaml({"evidence": evidence})
    body = _chat_or_fallback(system, user, fallback)
    return BlogDraftCandidate(
        title=title,
        body=body,
        tags=[str(evidence.get("type", "") or "evidence")],
        summary=summary[:220],
        related_evidence=[evidence_id],
    )


def draft_blog_from_evidence(name: str, evidence_id: str) -> Path:
    """Create a blog draft from one public evidence record."""
    candidate = blog_candidate_from_evidence(name, evidence_id)
    return create_blog_draft(
        name,
        title=candidate.title,
        body=candidate.body,
        tags=candidate.tags,
        summary=candidate.summary,
        related_evidence=candidate.related_evidence,
        related_kanban=candidate.related_kanban,
        related_claims=candidate.related_claims,
    )


def blog_candidate_from_claims(
    name: str,
    claim_ids: list[str],
) -> BlogDraftCandidate:
    """Return a blog draft candidate from accepted claims without writing."""
    known_claims = _accepted_claim_index(name)
    evidence = _evidence_index(name)
    selected: list[dict] = []
    missing: list[str] = []
    for claim_id in _candidate_string_list(claim_ids):
        claim = known_claims.get(claim_id)
        if claim is None:
            missing.append(claim_id)
            continue
        selected.append(claim)
    if missing:
        raise PublicSiteError(f"Unknown claim id(s): {', '.join(missing)}")
    if not selected:
        raise PublicSiteError("At least one accepted claim is required")

    related_evidence: list[str] = []
    for claim in selected:
        for evidence_id in _as_string_list(claim.get("evidence_refs")):
            if evidence_id not in related_evidence:
                related_evidence.append(evidence_id)
    supporting_evidence = [
        evidence[evidence_id]
        for evidence_id in related_evidence
        if evidence_id in evidence
    ]
    title = str(selected[0].get("text", "") or selected[0].get("id", "Claim draft"))
    title = title.strip().rstrip(".。")
    if len(title) > 80:
        title = title[:77].rstrip() + "..."

    fallback_lines = ["## What the evidence supports", ""]
    for claim in selected:
        fallback_lines.append(f"- {claim.get('text', '')}")
    fallback_lines.extend(["", "## Supporting evidence", ""])
    for row in supporting_evidence:
        fallback_lines.append(f"- `{row.get('id', '')}` {row.get('title', '')}")
    fallback_lines.extend(
        [
            "",
            "## Public narrative",
            "",
            "Turn the accepted claims into a publishable narrative without adding unsupported facts.",
        ]
    )
    fallback = "\n".join(fallback_lines) + "\n"
    system = (
        "You draft public blog candidates from accepted nblane claims and "
        "their supporting evidence. Use only the provided claims and evidence. "
        "Do not invent metrics, dates, links, employers, publications, or "
        "extra claims. Return Markdown body only. The result is a candidate "
        "for human review."
    )
    body = _chat_or_fallback(
        system,
        _dump_yaml(
            {
                "claims": selected,
                "supporting_evidence": supporting_evidence,
            }
        ),
        fallback,
    )
    warnings = [
        "Review claim wording, links, metrics, and private details before publishing.",
    ]
    dangling = [
        evidence_id
        for evidence_id in related_evidence
        if evidence_id not in evidence
    ]
    if dangling:
        warnings.append(
            "Some claim evidence refs are missing: " + ", ".join(dangling)
        )
    return BlogDraftCandidate(
        title=title or "Claim-backed draft",
        body=body,
        tags=["claims"],
        summary="Draft public article from accepted claims.",
        related_evidence=related_evidence,
        related_claims=[str(claim.get("id", "")) for claim in selected],
        warnings=warnings,
    )


def _accepted_claim_selection(
    name: str,
    claim_ids: list[str],
) -> tuple[list[dict], list[str], list[dict], list[str]]:
    """Return accepted claims, evidence ids, supporting evidence, and warnings."""
    known_claims = _accepted_claim_index(name)
    evidence = _evidence_index(name)
    selected: list[dict] = []
    missing: list[str] = []
    for claim_id in _candidate_string_list(claim_ids):
        claim = known_claims.get(claim_id)
        if claim is None:
            missing.append(claim_id)
            continue
        selected.append(claim)
    if missing:
        raise PublicSiteError(f"Unknown claim id(s): {', '.join(missing)}")
    if not selected:
        raise PublicSiteError("At least one accepted claim is required")
    related_evidence: list[str] = []
    for claim in selected:
        for evidence_id in _as_string_list(claim.get("evidence_refs")):
            if evidence_id not in related_evidence:
                related_evidence.append(evidence_id)
    supporting_evidence = [
        evidence[evidence_id]
        for evidence_id in related_evidence
        if evidence_id in evidence
    ]
    warnings: list[str] = []
    dangling = [
        evidence_id
        for evidence_id in related_evidence
        if evidence_id not in evidence
    ]
    if dangling:
        warnings.append(
            "Some claim evidence refs are missing: " + ", ".join(dangling)
        )
    return selected, related_evidence, supporting_evidence, warnings


def resume_bullet_candidates_from_claims(
    name: str,
    claim_ids: list[str],
) -> list[ResumeBulletCandidate]:
    """Return resume bullet candidates from accepted claims without writing."""
    selected, related_evidence, supporting_evidence, warnings = _accepted_claim_selection(
        name,
        claim_ids,
    )
    fallback_lines = [
        f"- {str(claim.get('text', '') or '').strip()}"
        for claim in selected
        if str(claim.get("text", "") or "").strip()
    ]
    fallback = "\n".join(fallback_lines) or "- Add a claim-backed resume bullet."
    system = (
        "You convert accepted nblane claims into concise resume bullets. "
        "Use only the provided claims and supporting evidence. Do not invent "
        "metrics, employers, dates, titles, links, or unverified outcomes. "
        "Return only a Markdown bullet list."
    )
    body = _chat_or_fallback(
        system,
        _dump_yaml(
            {
                "claims": selected,
                "supporting_evidence": supporting_evidence,
            }
        ),
        fallback,
    )
    bullets: list[ResumeBulletCandidate] = []
    for line in body.splitlines():
        text = re.sub(r"^\s*[-*]\s+", "", line).strip()
        if not text:
            continue
        bullets.append(
            ResumeBulletCandidate(
                text=text,
                related_claims=[str(claim.get("id", "")) for claim in selected],
                related_evidence=related_evidence,
                warnings=list(warnings),
            )
        )
    if not bullets:
        bullets.append(
            ResumeBulletCandidate(
                text=fallback.lstrip("- ").strip(),
                related_claims=[str(claim.get("id", "")) for claim in selected],
                related_evidence=related_evidence,
                warnings=list(warnings),
            )
        )
    review_warning = (
        "Review claim wording, metrics, scope, and private details before adding to resume-source.yaml."
    )
    for bullet in bullets:
        if review_warning not in bullet.warnings:
            bullet.warnings.append(review_warning)
    return bullets


def draft_blog_from_claims(name: str, claim_ids: list[str]) -> Path:
    """Create a blog draft from accepted claims."""
    candidate = blog_candidate_from_claims(name, claim_ids)
    return create_blog_draft(
        name,
        title=candidate.title,
        body=candidate.body,
        tags=candidate.tags,
        summary=candidate.summary,
        related_evidence=candidate.related_evidence,
        related_kanban=candidate.related_kanban,
        related_claims=candidate.related_claims,
    )


def blog_candidate_from_kanban_done(name: str) -> BlogDraftCandidate:
    """Return a blog draft candidate from current Done tasks."""
    sections = parse_kanban(name)
    tasks = sections.get(KANBAN_DONE, [])
    if not tasks:
        raise PublicSiteError("No Done tasks found in kanban.md")
    rows = []
    for task in tasks:
        rows.append(
            {
                "title": task.title,
                "outcome": task.outcome,
                "details": task.details,
                "completed_on": task.completed_on,
            }
        )
    today = date.today().isoformat()
    title = f"Work Notes {today}"
    fallback_lines = ["## Completed work", ""]
    for row in rows:
        fallback_lines.append(f"- **{row['title']}**")
        if row.get("outcome"):
            fallback_lines.append(f"  - outcome: {row['outcome']}")
    fallback_lines += [
        "",
        "## Public angle",
        "",
        "Add the reviewed public narrative here before publishing.",
    ]
    system = get_prompt("scaffold_kanban_done", llm.reply_language())
    body = _chat_or_fallback(
        system,
        _dump_yaml({"done_tasks": rows}),
        "\n".join(fallback_lines) + "\n",
    )
    return BlogDraftCandidate(
        title=title,
        body=body,
        tags=["work-notes"],
        summary="Draft public notes from completed kanban work.",
        related_kanban=[str(row["title"]) for row in rows],
    )


def draft_blog_from_kanban_done(name: str) -> Path:
    """Create a blog draft from current Done tasks."""
    candidate = blog_candidate_from_kanban_done(name)
    return create_blog_draft(
        name,
        title=candidate.title,
        body=candidate.body,
        tags=candidate.tags,
        summary=candidate.summary,
        related_evidence=candidate.related_evidence,
        related_kanban=candidate.related_kanban,
        related_claims=candidate.related_claims,
    )


def draft_resume_for_target(name: str, target: str) -> tuple[Path, Path]:
    """Create a target-specific resume draft from resume-source.yaml."""
    source = load_resume_source(name)
    fallback = render_resume_markdown(source)
    system = (
        "You draft a targeted resume from a structured fact source. "
        "Use only facts present in the YAML. Do not invent employers, "
        "dates, metrics, titles, publications, or links. Return Markdown "
        "only. The generated resume is a draft for human review."
    )
    body = _chat_or_fallback(
        system,
        _dump_yaml({"target": target, "resume_source": source}),
        fallback,
    )
    slug = _slugify(f"{date.today().isoformat()}-{target}")
    out = (
        _profile_path(name)
        / RESUMES_DIRNAME
        / GENERATED_RESUME_DIRNAME
        / f"{slug}.html"
    )
    return generate_resume_files(
        name,
        out_path=out,
        target=target,
        markdown_text=body,
    )


def draft_project_update(name: str, project_id: str) -> Path:
    """Append a draft public update to one project row."""
    root = _profile_path(name)
    path = root / PROJECTS_FILENAME
    raw = _read_yaml_mapping(path)
    projects = raw.get("projects") or []
    if not isinstance(projects, list):
        raise PublicSiteError(f"{PROJECTS_FILENAME}: projects must be a list")
    target: dict | None = None
    for item in projects:
        if isinstance(item, dict) and str(item.get("id", "")) == project_id:
            target = item
            break
    if target is None:
        raise PublicSiteError(f"Unknown project id: {project_id}")
    evidence = _evidence_index(name)
    refs = _as_string_list(target.get("evidence_refs"))
    related = [evidence[r] for r in refs if r in evidence]
    fallback = (
        f"Update draft for {target.get('title', project_id)}.\n\n"
        "Review claims, links, and metrics before publishing."
    )
    system = (
        "You draft a public project update from a project row and "
        "verified evidence. Use only the provided facts. Do not invent "
        "claims, metrics, dates, or links. Return Markdown body only."
    )
    body = _chat_or_fallback(
        system,
        _dump_yaml({"project": target, "evidence": related}),
        fallback,
    )
    updates = target.setdefault("draft_updates", [])
    if not isinstance(updates, list):
        updates = []
        target["draft_updates"] = updates
    updates.append(
        {
            "id": _slugify(f"{date.today().isoformat()}-{project_id}"),
            "date": date.today().isoformat(),
            "status": "draft",
            "title": f"{target.get('title', project_id)} update",
            "body": body,
        }
    )
    _write_yaml(path, {"projects": projects})
    git_backup.record_change(
        [path],
        action=f"draft {name} project update",
    )
    return path


def draft_project_update_from_claims(
    name: str,
    project_id: str,
    claim_ids: list[str],
) -> Path:
    """Append a draft project update from accepted claims."""
    candidate = project_update_candidate_from_claims(name, project_id, claim_ids)
    root = _profile_path(name)
    path = root / PROJECTS_FILENAME
    raw = _read_yaml_mapping(path)
    projects = raw.get("projects") or []
    if not isinstance(projects, list):
        raise PublicSiteError(f"{PROJECTS_FILENAME}: projects must be a list")
    target: dict | None = None
    for item in projects:
        if isinstance(item, dict) and str(item.get("id", "")) == project_id:
            target = item
            break
    if target is None:
        raise PublicSiteError(f"Unknown project id: {project_id}")

    updates = target.setdefault("draft_updates", [])
    if not isinstance(updates, list):
        updates = []
        target["draft_updates"] = updates
    updates.append(
        {
            "id": _slugify(f"{date.today().isoformat()}-{project_id}-claims"),
            "date": date.today().isoformat(),
            "status": "draft",
            "title": candidate.title,
            "body": candidate.body,
            "related_claims": candidate.related_claims,
            "evidence_refs": candidate.evidence_refs,
            "warnings": candidate.warnings,
        }
    )
    _write_yaml(path, {"projects": projects})
    git_backup.record_change(
        [path],
        action=f"draft {name} project update from claims",
    )
    return path


def project_update_candidate_from_claims(
    name: str,
    project_id: str,
    claim_ids: list[str],
) -> ProjectUpdateCandidate:
    """Return a project update candidate from accepted claims without writing."""
    root = _profile_path(name)
    path = root / PROJECTS_FILENAME
    raw = _read_yaml_mapping(path)
    projects = raw.get("projects") or []
    if not isinstance(projects, list):
        raise PublicSiteError(f"{PROJECTS_FILENAME}: projects must be a list")
    target: dict | None = None
    for item in projects:
        if isinstance(item, dict) and str(item.get("id", "")) == project_id:
            target = item
            break
    if target is None:
        raise PublicSiteError(f"Unknown project id: {project_id}")

    selected, related_evidence, supporting_evidence, warnings = _accepted_claim_selection(
        name,
        claim_ids,
    )
    title = f"{target.get('title', project_id)} claim-backed update"
    fallback_lines = [f"Update draft for {target.get('title', project_id)}.", ""]
    fallback_lines.append("Supported claims:")
    for claim in selected:
        fallback_lines.append(f"- {claim.get('text', '')}")
    fallback = "\n".join(fallback_lines) + "\n"
    system = (
        "You draft a public project update from accepted nblane claims, "
        "supporting evidence, and a project row. Use only the provided facts. "
        "Do not invent claims, metrics, dates, links, employers, or outcomes. "
        "Return Markdown body only."
    )
    body = _chat_or_fallback(
        system,
        _dump_yaml(
            {
                "project": target,
                "claims": selected,
                "supporting_evidence": supporting_evidence,
            }
        ),
        fallback,
    )
    review_warning = (
        "Review claim wording, project scope, links, metrics, and private details before publishing."
    )
    if review_warning not in warnings:
        warnings.append(review_warning)
    return ProjectUpdateCandidate(
        title=title,
        body=body,
        related_claims=[str(claim.get("id", "")) for claim in selected],
        evidence_refs=related_evidence,
        warnings=warnings,
    )


def blog_slug_from_path(path: Path) -> str:
    """Return a URL-safe slug for display or output paths."""
    return quote(_blog_route_from_document_path(path) or path.stem)
