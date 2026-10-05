"""Public-site console: display switches, per-post toggles, works, go-live.

Backs the SPA "公开站点" page. The static site itself is rendered by
``core/public_site.py``; this module only adds the console operations:

- ``site:`` display switches in ``public-profile.yaml`` (photo, phone,
  email, resume PDF, projects, base URL);
- one "public" toggle per blog post (status + public-library visibility);
- the works list (``outputs.yaml``: video / links / papers / articles);
- go-live (build straight into the live directory, keeping the previous
  build for rollback) and a diff between the current files and the live
  site.

Drafts never reach the live directory: deploys always build with
``include_drafts=False``.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from nblane.core import career_workspace, file_state, git_backup, public_site, resume_doc
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_write import atomic_write_text
from nblane.core.public_site import (
    BLOG_IMAGE_EXTENSIONS,
    BLOG_IMAGE_MAX_BYTES,
    BLOG_VIDEO_EXTENSIONS,
    BLOG_VIDEO_MAX_BYTES,
    MEDIA_DIRNAME,
    OUTPUTS_FILENAME,
    PUBLIC_PROFILE_FILENAME,
    RESUME_PDF_FILENAME,
    SITE_SETTING_DEFAULTS,
    WORK_TYPES,
    PublicSiteError,
)

WORKS_MEDIA_DIR = f"{MEDIA_DIRNAME}/works"
VIDEO_MODES = ("embed", "link")
WORKS_MAX = 60


class ConsoleError(ValueError):
    """User-facing console error with a stable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# --- Paths / etags --------------------------------------------------------------


def _profile_root(name: str) -> Path:
    return public_site._profile_path(name)


def works_etag(name: str) -> str:
    snapshot = file_state.snapshot_file(_profile_root(name) / OUTPUTS_FILENAME)
    return snapshot.sha256 or "missing"


# --- Validation messages ------------------------------------------------------------

_ISSUE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^(?P<l>.+?): missing required field '(?P<f>[^']+)'$"), "{l} 缺少必填字段「{f}」"),
    (re.compile(r"^(?P<l>.+?): draft missing field '(?P<f>[^']+)'$"), "{l} 草稿缺少字段「{f}」（发布前需补齐）"),
    (re.compile(r"^(?P<l>.+?): unknown evidence ref '(?P<r>[^']+)'$"), "{l} 引用了不存在的证据 {r}"),
    (re.compile(r"^(?P<l>.+?): unknown claim ref '(?P<r>[^']+)'$"), "{l} 引用了不存在的结论 {r}"),
    (re.compile(r"^(?P<l>.+?): claim ref '(?P<r>[^']+)' is not accepted$"), "{l} 引用的结论 {r} 还没有被接受"),
    (re.compile(r"^(?P<l>.+?): media file does not exist: (?P<r>.+)$"), "{l} 引用的媒体文件不存在：{r}"),
    (re.compile(r"^(?P<l>.+?): media path must stay under 'media/': (?P<r>.+)$"), "{l} 的媒体路径必须在 media/ 目录下：{r}"),
    (re.compile(r"^(?P<l>.+?): unsafe URL scheme '(?P<s>[^']+)' is not allowed: (?P<r>.+)$"), "{l} 的链接协议 {s} 不安全：{r}"),
    (re.compile(r"^(?P<l>.+?): invalid status '(?P<s>[^']+)'.*$"), "{l} 的状态「{s}」无效"),
    (re.compile(r"^public-profile\.yaml: visibility must be public.*$"), "网站还没有设为公开（打开「网站公开」开关）"),
)


def _issue_label(label: str) -> str:
    clean = label.strip()
    match = re.match(r"^blog/(.+)\.md$", clean)
    if match:
        return f"文章「{match.group(1)}」"
    match = re.match(rf"^{re.escape(OUTPUTS_FILENAME)}:(.+?)(\..+)?$", clean)
    if match:
        return f"作品「{match.group(1)}」{match.group(2) or ''}"
    match = re.match(r"^projects\.yaml:(.+?)(\..+)?$", clean)
    if match:
        return f"项目「{match.group(1)}」{match.group(2) or ''}"
    return clean


def humanize_issue(message: str) -> str:
    """Chinese rendering of a public-layer validation message (fallback: as-is)."""
    text = str(message or "").strip()
    for pattern, template in _ISSUE_PATTERNS:
        match = pattern.match(text)
        if match:
            groups = match.groupdict()
            if "l" in groups:
                groups["l"] = _issue_label(groups["l"])
            return template.format(**groups)
    return text


# --- Settings -------------------------------------------------------------------


def _load_public_profile(name: str) -> dict[str, Any]:
    data = public_site.load_public_profile(name)
    return data if data else public_site._default_public_profile(name)


def update_settings(name: str, patch: dict[str, Any]) -> dict[str, Any]:
    """Merge display switches (and optional ``visibility``) into public-profile.yaml.

    Only the ``site:`` mapping and ``visibility`` are touched, under the file
    lock, so concurrent edits of other public-profile fields survive.
    """
    root = _profile_root(name)
    path = root / PUBLIC_PROFILE_FILENAME
    with locked_profile_write(root, path.name):
        data = _load_public_profile(name)
        site = dict(public_site.site_settings(data))
        for key, default in SITE_SETTING_DEFAULTS.items():
            if key not in patch or patch[key] is None:
                continue
            value = patch[key]
            site[key] = bool(value) if isinstance(default, bool) else str(value).strip()
        if site["base_url"]:
            try:
                site["base_url"] = public_site._normalize_base_url(site["base_url"])
            except PublicSiteError as exc:
                raise ConsoleError("invalid_base_url", "网站地址需要是完整的 http(s) 网址。") from exc
        data["site"] = site
        visibility = patch.get("visibility")
        if visibility is not None:
            if visibility not in public_site.PUBLIC_VISIBILITIES:
                raise ConsoleError("invalid_visibility", "visibility 只能是 public 或 private。")
            data["visibility"] = visibility
        atomic_write_text(
            path,
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        )
    git_backup.record_change([path], action=f"update {name} public site settings")
    return site


# --- Posts ----------------------------------------------------------------------


def _library_visibility(name: str) -> dict[str, str] | None:
    """Post route → library visibility, or None when the library is not in use.

    When the library has real nodes, a published post without a node is
    *not* on the site (``load_blog_posts`` filters it), so callers treat a
    missing route as hidden.
    """
    library = public_site.load_public_library(name)
    if not public_site._public_library_has_real_nodes(library):
        return None
    out: dict[str, str] = {}
    for node in library.nodes:
        if node.type == "post" and node.ref and node.status != "trashed":
            out[public_site._library_blog_route(node.ref)] = node.visibility
    return out


def set_post_public(name: str, slug: str, public: bool) -> None:
    """Make one post part of the public site (publish + library public) or not.

    Turning a post off reverts it to draft, the same as "撤回为草稿" in the
    content workspace. Publishing goes through the full publish gate.
    """
    try:
        post = public_site.load_blog_post(name, slug)
    except PublicSiteError as exc:
        raise ConsoleError("post_not_found", "文章不存在。") from exc
    if public:
        if post.status != "published":
            try:
                public_site.publish_blog_post(name, post.route)
            except PublicSiteError as exc:
                issues = "；".join(humanize_issue(line) for line in str(exc).splitlines() if line.strip())
                raise ConsoleError("post_not_publishable", f"这篇还不能公开：{issues}") from exc
        if _library_visibility(name) is not None and not public_site.set_public_library_post_visibility(
            name, post.route, "public"
        ):
            public_site.attach_existing_public_library_node(
                name, None, post.route, visibility="public"
            )
    elif post.status == "published":
        public_site.unpublish_blog_post(name, post.route)


# --- Works ----------------------------------------------------------------------


def _clean_text(value: object, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _work_id(title: str, taken: set[str]) -> str:
    base = re.sub(r"[^a-zA-Z0-9一-鿿_-]+", "-", title.strip().lower()).strip("-")[:40]
    candidate = base or f"work-{uuid.uuid4().hex[:6]}"
    while candidate in taken:
        candidate = f"{base or 'work'}-{uuid.uuid4().hex[:4]}"
    return candidate


def _normalize_work(raw: dict[str, Any]) -> dict[str, Any]:
    links_raw = raw.get("links")
    links: list[dict[str, str]] = []
    if isinstance(links_raw, dict):
        links = [{"label": str(k), "url": str(v)} for k, v in links_raw.items() if str(v or "").strip()]
    elif isinstance(links_raw, list):
        for row in links_raw:
            if isinstance(row, dict) and str(row.get("url") or "").strip():
                links.append({"label": _clean_text(row.get("label"), 40), "url": _clean_text(row.get("url"), 1000)})
    kind = str(raw.get("type") or "other").strip()
    mode = str(raw.get("video_mode") or "embed").strip()
    return {
        "id": _clean_text(raw.get("id"), 80),
        "title": _clean_text(raw.get("title"), 200),
        "type": kind if kind in WORK_TYPES else "other",
        "year": _clean_text(raw.get("year"), 20),
        "summary": _clean_text(raw.get("summary"), 2000),
        "video": _clean_text(raw.get("video"), 1000),
        "video_mode": mode if mode in VIDEO_MODES else "embed",
        "cover": _clean_text(raw.get("cover"), 1000),
        "links": links,
        "status": "published" if str(raw.get("status") or "") == "published" else "draft",
        "featured": bool(raw.get("featured")),
    }


def list_works(name: str) -> list[dict[str, Any]]:
    return [_normalize_work(row) for row in public_site.load_outputs(name)]


def save_works(name: str, works: list[dict[str, Any]], *, expected_etag: str = "") -> list[dict[str, Any]]:
    """Replace the works list in ``outputs.yaml``; unknown keys of existing rows survive."""
    if len(works) > WORKS_MAX:
        raise ConsoleError("invalid_works", f"作品最多 {WORKS_MAX} 条。")
    root = _profile_root(name)
    path = root / OUTPUTS_FILENAME
    with locked_profile_write(root, path.name):
        if expected_etag and works_etag(name) != expected_etag:
            raise ConsoleError("etag_mismatch", "作品列表已在别处修改，请刷新后再保存。")
        raw = public_site._read_yaml_mapping(path)
        existing = {
            str(row.get("id")): row
            for row in (raw.get("outputs") or [])
            if isinstance(row, dict) and row.get("id")
        }
        taken: set[str] = set()
        rows: list[dict[str, Any]] = []
        for item in works:
            work = _normalize_work(item if isinstance(item, dict) else {})
            if not work["title"]:
                raise ConsoleError("invalid_works", "每条作品都需要标题。")
            if not work["id"] or work["id"] in taken:
                work["id"] = _work_id(work["title"], taken | set(existing))
            taken.add(work["id"])
            row = dict(existing.get(work["id"], {}))
            row.update({k: v for k, v in work.items() if k != "links"})
            row["links"] = {link["label"] or link["url"]: link["url"] for link in work["links"]}
            for key in ("video", "cover", "year", "summary"):
                if not row.get(key):
                    row.pop(key, None)
            if row.get("video_mode") == "embed" and not row.get("video"):
                row.pop("video_mode", None)
            if not row.get("featured"):
                row.pop("featured", None)
            rows.append(row)
        raw["outputs"] = rows
        atomic_write_text(path, yaml.safe_dump(raw, allow_unicode=True, sort_keys=False))
    git_backup.record_change([path], action=f"update {name} public works")
    return list_works(name)


def save_work_media(name: str, filename: str, data: bytes) -> str:
    """Store a work cover image or video under ``media/works/``; returns the relative path."""
    ext = Path(filename or "").suffix.lower().lstrip(".")
    if ext in BLOG_IMAGE_EXTENSIONS:
        limit = BLOG_IMAGE_MAX_BYTES
    elif ext in BLOG_VIDEO_EXTENSIONS:
        limit = BLOG_VIDEO_MAX_BYTES
        data, filename = public_site._browser_compatible_video_data(data, filename)
        ext = Path(filename).suffix.lower().lstrip(".")
    else:
        raise ConsoleError("invalid_media", "只支持图片（PNG/JPG/WebP/GIF）或视频（MP4/WebM）。")
    if not data:
        raise ConsoleError("invalid_media", "文件为空。")
    if len(data) > limit:
        raise ConsoleError("invalid_media", f"文件不能超过 {limit // (1024 * 1024)} MB。")
    digest = hashlib.sha256(data).hexdigest()[:10]
    stem = Path(public_site._safe_media_filename(filename, fallback="work")).stem[:40]
    rel = f"{WORKS_MEDIA_DIR}/{stem}-{digest}.{ext}"
    target = _profile_root(name) / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(data)
        git_backup.record_change([target], action=f"upload {name} work media")
    return rel


# --- Live site ------------------------------------------------------------------


def _mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def _live_pages(live_dir: Path) -> set[str]:
    if not live_dir.is_dir():
        return set()
    return {p.relative_to(live_dir).as_posix() for p in live_dir.rglob("index.html") if p.is_file()}


def live_state(name: str, live_dir: Path) -> dict[str, Any]:
    """Diff the current files against the live directory (renders in memory)."""
    profile = _load_public_profile(name)
    settings = public_site.site_settings(profile)
    rendered = public_site.render_public_site_pages(
        name,
        base_url=str(settings["base_url"] or ""),
    )
    live = _live_pages(live_dir)
    added: list[str] = []
    changed: list[str] = []
    for rel, text in rendered.pages.items():
        target = live_dir / rel
        if not target.is_file():
            added.append(rel)
        elif target.read_text(encoding="utf-8") != text:
            changed.append(rel)
    removed = sorted(live - set(rendered.pages))
    pdf_path = live_dir / RESUME_PDF_FILENAME
    pdf_live = pdf_path.is_file()
    resume_path = career_workspace.resume_path(name)
    # The PDF is printed from the master resume at deploy time; a resume
    # edited after the last deploy makes the live PDF stale.
    pdf_stale = (
        pdf_live
        and resume_path.is_file()
        and resume_path.stat().st_mtime > pdf_path.stat().st_mtime
    )
    index = live_dir / "index.html"
    prev = public_site.previous_build_dir(live_dir)
    prev_index = prev / "index.html"

    def titled(rels: list[str]) -> list[dict[str, str]]:
        return [{"path": rel, "title": rendered.page_titles.get(rel, rel)} for rel in sorted(rels)]

    return {
        "output_dir": str(live_dir),
        "exists": index.is_file(),
        "built_at": _mtime_iso(index) if index.is_file() else "",
        "page_count": len(live),
        "has_previous": prev_index.is_file(),
        "previous_built_at": _mtime_iso(prev_index) if prev_index.is_file() else "",
        "added": titled(added),
        "changed": titled(changed),
        "removed": [{"path": rel, "title": rel} for rel in removed],
        "pdf_live": pdf_live,
        "pdf_pending": bool(settings["resume_pdf"]) != pdf_live or pdf_stale,
        "in_sync": (
            not (added or changed or removed)
            and bool(settings["resume_pdf"]) == pdf_live
            and not pdf_stale
        ),
    }


def deploy(name: str, live_dir: Path) -> dict[str, Any]:
    """Build the public site straight into *live_dir* (no drafts), keeping the previous build."""
    settings = public_site.site_settings(_load_public_profile(name))
    try:
        result = public_site.build_public_site(
            name,
            out_dir=live_dir,
            include_drafts=False,
            base_url=str(settings["base_url"] or ""),
            keep_previous=True,
        )
    except PublicSiteError as exc:
        issues = [humanize_issue(line) for line in str(exc).splitlines() if line.strip()]
        raise ConsoleError("deploy_blocked", "；".join(issues) or "构建失败。") from exc
    return {
        "page_count": sum(1 for page in result.pages if page.name == "index.html"),
        "warnings": list(result.warnings),
    }


def rollback(name: str, live_dir: Path) -> None:
    try:
        public_site.rollback_public_site(name, out_dir=live_dir)
    except PublicSiteError as exc:
        raise ConsoleError("no_previous_build", str(exc)) from exc


# --- Overview -------------------------------------------------------------------


def overview(name: str, live_dir: Path) -> dict[str, Any]:
    profile = _load_public_profile(name)
    settings = public_site.site_settings(profile)
    resume = career_workspace.load_resume(name)
    basics = resume.get("basics") or {}
    library = _library_visibility(name)
    live_pages = _live_pages(live_dir)
    posts = []
    for post in public_site.load_blog_posts(name, include_drafts=True):
        library_visibility = "public" if library is None else library.get(post.route, "private")
        published = post.status == "published"
        posts.append(
            {
                "slug": post.route,
                "title": post.title,
                "date": post.date,
                "status": post.status,
                "summary": post.summary,
                "library_hidden": library_visibility == "private",
                "public": published and library_visibility != "private",
                "live": f"{post.url_path}index.html" in live_pages,
            }
        )
    validation = public_site.validate_public_layer(name, include_drafts=False)
    errors = [humanize_issue(line) for line in validation.errors]
    visibility = str(profile.get("visibility") or "private")
    if visibility != "public":
        # The build enforces this gate; surface it before the deploy button.
        errors.insert(0, humanize_issue(f"{PUBLIC_PROFILE_FILENAME}: visibility must be public"))
    return {
        "profile": name,
        "visibility": visibility,
        "settings": settings,
        "intro": {
            "name": str(profile.get("public_name") or basics.get("name") or name),
            "english_name": str(profile.get("english_name") or ""),
            "title": str(basics.get("title") or profile.get("headline") or ""),
            "summary": str(resume.get("summary") or profile.get("bio_short") or ""),
            "photo": str(basics.get("photo") or ""),
            "phone": str(basics.get("phone") or ""),
            "email": str(basics.get("email") or ""),
            "has_resume": resume_doc.has_content(resume),
        },
        "posts": posts,
        "works": list_works(name),
        "works_etag": works_etag(name),
        "projects_count": len(public_site.load_projects(name)),
        "errors": errors,
        "warnings": [humanize_issue(line) for line in validation.warnings],
        "live": live_state(name, live_dir),
    }
