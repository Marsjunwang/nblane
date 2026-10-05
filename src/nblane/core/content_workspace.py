"""Public content workspace helpers.

The content workspace is deliberately a thin projection over the existing
public blog store.  It keeps the product boundary clear: no evidence, claim,
skill tree, or kanban files are read when listing or editing content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nblane.core import public_site


def overview(name: str) -> dict[str, Any]:
    """Return the content workspace projection for *name*."""
    posts = public_site.load_blog_posts(name, include_drafts=True, include_archived=True)
    rows = []
    for post in posts:
        rows.append(
            {
                "slug": post.slug,
                "title": post.title,
                "date": post.date,
                "status": post.status,
                "summary": post.summary,
                "cover": str(post.meta.get("cover") or ""),
                "tags": [str(item) for item in (post.meta.get("tags") or []) if str(item).strip()],
                "category_path": list(post.category_path),
            }
        )
    # Newest first: the writer almost always wants the post they just made.
    rows.sort(key=lambda row: (str(row["date"] or ""), row["slug"]), reverse=True)
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row["status"] or "draft")
        counts[status] = counts.get(status, 0) + 1
    return {"profile": name, "posts": rows, "summary": {"status_counts": counts, "total_posts": len(rows)}}


def post_media(name: str, post: public_site.BlogPost) -> list[dict[str, Any]]:
    """List one post's media directory without building inline previews.

    ``public_site.blog_media_library_rows`` base64-encodes every file for the
    Streamlit component; the SPA loads files by URL instead, so this listing
    only stats the files.
    """
    profile_root = public_site._profile_path(name)
    media_dir = (
        profile_root
        / public_site.MEDIA_DIRNAME
        / public_site.BLOG_DIRNAME
        / public_site._slugify_route(post.slug)
    )
    if not media_dir.is_dir():
        return []
    cover = str(post.meta.get("cover") or "")
    rows: list[dict[str, Any]] = []
    for path in sorted(media_dir.iterdir()):
        if not path.is_file():
            continue
        ext = path.suffix.lower().lstrip(".")
        if ext in public_site.BLOG_IMAGE_EXTENSIONS:
            kind = "image"
        elif ext in public_site.BLOG_VIDEO_EXTENSIONS:
            kind = "video"
        else:
            continue
        rel = path.resolve().relative_to(profile_root.resolve()).as_posix()
        rows.append(
            {
                "path": rel,
                "name": path.name,
                "kind": kind,
                "size": path.stat().st_size,
                "referenced": rel in post.body or rel == cover,
                "cover": rel == cover,
            }
        )
    return rows


def media_file(name: str, rel: str) -> Path | None:
    """Resolve *rel* to a file under the profile ``media/`` dir, else None."""
    profile_root = public_site._profile_path(name)
    target = public_site._local_media_target(profile_root, str(rel or ""))
    if target is None or not target.is_file():
        return None
    return target
