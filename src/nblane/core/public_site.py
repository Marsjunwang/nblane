"""Public personal site generation for nblane profiles."""

from __future__ import annotations

import html
import base64
import hashlib
import mimetypes
import re
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

import yaml

from nblane.core import git_backup, llm
from nblane.core.kanban_io import KANBAN_DONE, parse_kanban
from nblane.core.paths import REPO_ROOT
from nblane.core.profile_io import profile_dir

PUBLIC_PROFILE_FILENAME = "public-profile.yaml"
RESUME_SOURCE_FILENAME = "resume-source.yaml"
PROJECTS_FILENAME = "projects.yaml"
OUTPUTS_FILENAME = "outputs.yaml"
BLOG_DIRNAME = "blog"
MEDIA_DIRNAME = "media"
RESUMES_DIRNAME = "resumes"
GENERATED_RESUME_DIRNAME = "generated"

PUBLIC_VISIBILITIES = {"private", "public"}
PUBLISH_STATUSES = {"draft", "published", "archived"}
LOCAL_MEDIA_FIELDS = ("avatar", "cover")
BLOG_INSERT_MARKER = "<!-- nblane:insert -->"
BLOG_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
BLOG_VIDEO_EXTENSIONS = {"mp4", "webm"}
BLOG_DIRECT_VIDEO_EXTENSIONS = {"mp4", "webm", "ogg"}
BLOG_IMAGE_MAX_BYTES = 10 * 1024 * 1024
BLOG_VIDEO_MAX_BYTES = 25 * 1024 * 1024
BLOG_PREVIEW_VIDEO_INLINE_MAX_BYTES = 2 * 1024 * 1024
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
            "cover_prompt": self.cover_prompt,
            "warnings": list(self.warnings),
            "body": self.body,
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


def parse_blog_post(path: Path) -> BlogPost:
    """Parse a blog Markdown file."""
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_front_matter(text)
    return BlogPost(
        slug=path.stem,
        path=path,
        meta=meta,
        body=body,
    )


def load_blog_posts(
    name: str,
    *,
    include_drafts: bool = False,
    include_archived: bool = False,
) -> list[BlogPost]:
    """Load visible blog posts from profiles/<name>/blog."""
    blog_dir = _profile_path(name) / BLOG_DIRNAME
    if not blog_dir.exists():
        return []
    posts: list[BlogPost] = []
    for path in sorted(blog_dir.glob("*.md")):
        post = parse_blog_post(path)
        if _status_visible(
            post.status,
            include_drafts=include_drafts,
            include_archived=include_archived,
        ):
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


def markdown_contains_math(text: str) -> bool:
    """Return True when Markdown appears to contain LaTeX math delimiters."""
    clean = _FENCED_CODE_RE.sub("", text)
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


def validate_blog_text_for_publish(
    name: str,
    path: Path,
    text: str,
) -> PublicValidationResult:
    """Validate one blog document as if it will become public."""
    root = _profile_path(name)
    meta, body = _parse_front_matter(text)
    post = BlogPost(
        slug=path.stem,
        path=path,
        meta=meta,
        body=body,
    )
    result = PublicValidationResult()
    _validate_blog_post(
        result,
        root,
        post,
        known_evidence_ids=_evidence_ids(name),
        include_refs=True,
        require_publish_ready=True,
    )
    return result


def _validate_blog_post(
    result: PublicValidationResult,
    profile_root: Path,
    post: BlogPost,
    *,
    known_evidence_ids: set[str],
    include_refs: bool,
    require_publish_ready: bool,
) -> None:
    label = f"blog/{post.path.name}"
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
    cover = post.meta.get("cover", "")
    if require_publish_ready or str(cover or "").strip():
        _validate_media_path(
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
        for path in sorted(blog_dir.glob("*.md")):
            post = parse_blog_post(path)
            include_refs = _status_visible(
                post.status,
                include_drafts=include_drafts,
            )
            _validate_blog_post(
                result,
                root,
            post,
            known_evidence_ids=known_ids,
            include_refs=include_refs,
            require_publish_ready=(post.status == "published"),
        )

    return result


def _markdown_to_html(text: str) -> str:
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
            if line.startswith('<figure class="media-block">') or line.startswith(
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
        + '  <meta name="twitter:card" content="summary">\n'
        + f'  <meta name="twitter:title" content="{html.escape(full_title, quote=True)}">\n'
        + f'  <meta name="twitter:description" content="{html.escape(meta_description, quote=True)}">\n'
    )
    math_head = _MATHJAX_HEAD if include_math else ""
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
.prose pre { overflow: auto; padding: 16px; background: #10201e; color: #eef5f1; }
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


def _render_post_item(post: BlogPost) -> str:
    tags = _as_string_list(post.meta.get("tags"))
    tag_html = "".join(
        f'<span class="pill">{html.escape(t)}</span>' for t in tags
    )
    return f"""
<article class="item">
  <div class="meta">{html.escape(post.date)}</div>
  <h3><a href="/{post.url_path}">{html.escape(post.title)}</a></h3>
  <p>{html.escape(post.summary)}</p>
  <div class="tag-row">{tag_html}</div>
</article>
"""


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

    def page_url(rel: str) -> str:
        return _site_url(base_url, _url_path_for_page(rel))

    public_profile = _merge_public_profile_override(
        load_public_profile(name),
        public_profile_override,
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

    blog_body = (
        '<section class="section"><div class="section-inner">'
        "<h1>Blog</h1><div class=\"grid\">"
        + "".join(_render_post_item(p) for p in posts)
        + "</div></div></section>"
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
    for post in posts:
        article = (
            '<article class="prose">'
            f'<p class="meta">{html.escape(post.date)}</p>'
            f"<h1>{html.escape(post.title)}</h1>"
            + _markdown_to_html(post.body)
            + "</article>"
        )
        _add_render_page(
            pages,
            page_titles,
            f"blog/{post.slug}/index.html",
            post.title,
            _html_page(
                title=post.title,
                body=article,
                public_profile=public_profile,
                current="blog",
                description=post.summary,
                canonical_url=page_url(f"blog/{post.slug}/index.html"),
                og_type="article",
                include_resume=resume_visible,
                include_math=markdown_contains_math(post.body),
            ),
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


def _data_uri_for_media(
    profile_root: Path,
    rel: str,
    media_overrides: dict[str, bytes],
    warnings: list[str],
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
    if mime.startswith("video/") and len(data) > BLOG_PREVIEW_VIDEO_INLINE_MAX_BYTES:
        warnings.append(
            f"preview skipped large video media; build will copy it: {clean}"
        )
        return ""
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _inline_preview_assets(
    html_text: str,
    *,
    css: str,
    profile_root: Path,
    media_overrides: dict[str, bytes],
    warnings: list[str],
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
        )
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
        )
        for rel, text in rendered.pages.items()
    }
    return PublicSitePreviewResult(
        pages=pages,
        page_titles=dict(rendered.page_titles),
        warnings=warnings,
    )


def _render_sitemap(
    pages: list[Path],
    root: Path,
    *,
    base_url: str,
) -> str:
    urls = []
    for path in pages:
        if path.suffix not in (".html", ".xml", ".txt"):
            continue
        if path.name not in ("index.html", "sitemap.xml"):
            continue
        rel = path.relative_to(root)
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


def _blog_slug_text(slug: str | Path) -> str:
    """Normalize public blog slug inputs for API compatibility."""
    if isinstance(slug, Path):
        return slug.stem
    if not isinstance(slug, str):
        raise PublicSiteError("Blog slug must be a string or Path.")
    return slug


def _safe_blog_path(name: str, slug: str) -> Path:
    clean = _slugify(slug)
    path = _profile_path(name) / BLOG_DIRNAME / f"{clean}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def blog_path_for_slug(name: str, slug: str) -> Path:
    """Return the canonical Markdown path for a blog slug."""
    return _safe_blog_path(name, slug)


def load_blog_post(name: str, slug: str) -> BlogPost:
    """Load a blog post by slug."""
    path = _safe_blog_path(name, slug)
    if not path.exists():
        raise PublicSiteError(f"Unknown blog post: {slug}")
    return parse_blog_post(path)


def _write_blog_post_file(
    name: str,
    path: Path,
    meta: dict,
    body: str,
    *,
    action: str,
    changed_paths: list[Path] | None = None,
) -> Path:
    paths = [path]
    if changed_paths:
        paths.extend(changed_paths)
    path.write_text(_format_front_matter(meta, body), encoding="utf-8")
    git_backup.record_change(paths, action=action)
    return path


def _blog_media_dir(name: str, slug: str) -> Path:
    clean_slug = _slugify(slug)
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


def _image_ext_from_data_uri(kind: str) -> str:
    ext = kind.lower()
    return "jpg" if ext == "jpeg" else ext


def extract_blog_base64_images(
    name: str,
    slug: str,
    body: str,
) -> tuple[str, list[Path]]:
    """Extract Markdown data-URI images into media/blog/<slug>/ files."""
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
    action: str | None = None,
) -> tuple[Path, list[Path]]:
    """Save a blog post from structured metadata and Markdown body."""
    path = _safe_blog_path(name, slug)
    if not path.exists():
        raise PublicSiteError(f"Unknown blog post: {slug}")
    changed: list[Path] = []
    if extract_inline_images:
        body, changed = extract_blog_base64_images(name, path.stem, body)
    _write_blog_post_file(
        name,
        path,
        meta,
        body,
        action=action or f"update {name}/blog/{path.name}",
        changed_paths=changed,
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
    """Copy a media file into media/blog/<slug>/ and optionally update a post."""
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
    media_dir = _blog_media_dir(name, post.slug)
    clean_filename = _safe_media_filename(filename, fallback=media_kind)
    target = _unique_media_path(media_dir, clean_filename, data)
    if not target.exists():
        target.write_bytes(data)
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
    """Copy a media file into media/blog/<slug>/ and optionally update a post."""
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


def publish_blog_post(name: str, slug: str | Path) -> Path:
    """Set a blog post status to published after publish validation."""
    slug_text = _blog_slug_text(slug)
    post = load_blog_post(name, slug_text)
    meta = dict(post.meta)
    meta["status"] = "published"
    candidate = _format_front_matter(meta, post.body)
    result = validate_blog_text_for_publish(name, post.path, candidate)
    result.raise_for_errors()
    post.path.write_text(candidate, encoding="utf-8")
    git_backup.record_change(
        [post.path],
        action=f"publish {name}/blog/{post.path.name}",
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
    slug: str | None = None,
) -> Path:
    """Write a draft blog post and return its path."""
    today = date.today().isoformat()
    slug_text = slug or f"{today}-{title}"
    path = _safe_blog_path(name, slug_text)
    if path.exists():
        stem = path.stem
        path = _safe_blog_path(name, f"{stem}-{today}")
    meta = {
        "title": title,
        "date": today,
        "status": "draft",
        "tags": tags or [],
        "summary": summary,
        "cover": "",
        "related_evidence": related_evidence or [],
        "related_kanban": related_kanban or [],
    }
    path.write_text(
        _format_front_matter(meta, body),
        encoding="utf-8",
    )
    git_backup.record_change(
        [path],
        action=f"create {name} blog draft",
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
    system = (
        "You draft public blog candidates for nblane. Return a YAML mapping "
        "with exactly these keys: title, summary, tags, cover_prompt, "
        "warnings, body. The body must be Markdown. Because the user only "
        "provided a title, do not invent specific projects, metrics, dates, "
        "paper claims, employers, links, or private facts. Write useful "
        "structure, cautious prose, and explicit placeholders where facts "
        "must be verified. If mathematical notation is useful, use "
        "\\(...\\) for inline math and \\[...\\] for display math; never "
        "leave formula placeholders empty. Keep the result suitable as a "
        "human-reviewed candidate, not a final publication."
    )
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
    system = (
        "You draft public blog posts from verified nblane evidence. "
        "Use only the provided evidence. Do not invent metrics, dates, "
        "links, publications, or claims. Return Markdown body only. "
        "The post will remain draft until a human publishes it."
    )
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
    system = (
        "You draft public-facing work notes from kanban Done tasks. "
        "Use only the provided task titles, outcomes, and details. "
        "Do not expose private planning context or invent facts. "
        "Return Markdown body only; the file must remain draft."
    )
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


def blog_slug_from_path(path: Path) -> str:
    """Return a URL-safe slug for display or output paths."""
    return quote(path.stem)
