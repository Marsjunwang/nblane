"""Profile-agnostic blog workspace payload + event dispatch.

This module is the single source of truth for translating React Blog Editor
events into ``public_site`` calls. Both the Streamlit Output Studio and the
standalone Reader API blog editor page consume it, so the editing contract
cannot drift between the two hosts.

Scope (Stage 1): the editing-essential actions that derive purely from the
public layer on disk -- list/select posts, save, publish, run a publish check,
create drafts, and public-library structural operations. AI generation, visual
asset generation, and inline media upload remain Streamlit-coupled for now and
are handled by the caller; ``handle_blog_workspace_event`` returns an
``unhandled`` result for those so the caller can fall back.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nblane.core import public_site as ps


# Actions this module handles end to end. Anything else returns ``unhandled``
# so a richer host (Streamlit) can take over.
HANDLED_ACTIONS = frozenset(
    {
        "select_post",
        "save_post",
        "publish_request",
        "run_check",
        "create_post",
        "preview_post",
        "generate_ai_candidate",
        "draft_from_evidence",
        "draft_from_claims",
        "draft_from_done",
        "delete_media",
        "convert_media_video",
        "upload_media",
        "library_upload_media",
        "library_attach_existing",
        "library_select_node",
        "library_create_folder",
        "library_create_post",
        "library_rename_node",
        "library_move_node",
        "library_reorder_node",
        "library_trash_node",
        "library_restore_node",
        "library_permanent_delete_node",
    }
)


@dataclass
class BlogEventResult:
    """Outcome of dispatching one editor event."""

    ok: bool = True
    handled: bool = True
    action: str = ""
    slug: str = ""
    status: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    quality: list[str] = field(default_factory=list)
    message: str = ""
    changed_paths: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": self.ok,
            "handled": self.handled,
            "action": self.action,
        }
        if self.slug:
            payload["slug"] = self.slug
        if self.status:
            payload["status"] = self.status
        if self.errors:
            payload["errors"] = list(self.errors)
        if self.warnings:
            payload["warnings"] = list(self.warnings)
        if self.quality:
            payload["quality"] = list(self.quality)
        if self.message:
            payload["message"] = self.message
        if self.changed_paths:
            payload["changed_paths"] = list(self.changed_paths)
        payload.update(self.extra)
        return payload


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _clean_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [
        part.strip()
        for part in str(value or "").replace("\\", "/").split("/")
        if part.strip()
    ]


def _ref_to_slug(ref: object) -> str:
    clean = str(ref or "").strip()
    if not clean:
        return ""
    return clean.removeprefix("blog/").removesuffix(".md").strip("/")


def _decode_upload_payload(payload: dict) -> bytes:
    """Decode base64/data-URL media bytes from an editor event payload."""
    raw = (
        payload.get("data_url")
        or payload.get("data")
        or payload.get("base64")
        or payload.get("content")
        or ""
    )
    if not isinstance(raw, str) or not raw.strip():
        raise ps.PublicSiteError("Upload payload is missing base64 data.")
    encoded = raw.strip()
    if encoded.startswith("data:") and "," in encoded:
        encoded = encoded.split(",", 1)[1]
    try:
        return base64.b64decode(re.sub(r"\s+", "", encoded), validate=True)
    except Exception as exc:
        raise ps.PublicSiteError("Upload payload is not valid base64 data.") from exc


def _result_slug(result: object) -> str:
    """Extract a blog slug from a PublicLibraryOperationResult."""
    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        data = to_dict()
        if isinstance(data, dict):
            slug = _ref_to_slug(
                data.get("slug") or data.get("route") or data.get("ref") or ""
            )
            if slug:
                return slug
    node = getattr(result, "node", None)
    if node is not None:
        slug = _ref_to_slug(getattr(node, "ref", "") or "")
        if slug:
            return slug
    for path in getattr(result, "changed_paths", []) or []:
        slug = _ref_to_slug(str(path))
        if slug:
            return slug
    return ""


def _result_to_dict(result: object) -> dict[str, Any]:
    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        data = to_dict()
        if isinstance(data, dict):
            return data
    return {}


def _result_node_id(result: object) -> str:
    data = _result_to_dict(result)
    for key in ("id", "node_id"):
        value = _clean_text(data.get(key))
        if value:
            return value
    node = getattr(result, "node", None)
    if node is not None:
        return _clean_text(getattr(node, "id", ""))
    return ""


# --------------------------------------------------------------------------
# Payload assembly
# --------------------------------------------------------------------------


def _post_rows(posts: list) -> list[dict[str, Any]]:
    """Compact post rows for the React list panel (mirrors Streamlit shell)."""
    return [
        {
            "slug": post.slug,
            "route": getattr(post, "route", post.slug),
            "leaf_slug": getattr(post, "leaf_slug", post.slug),
            "category_path": list(getattr(post, "category_path", []) or []),
            "title": post.title,
            "date": post.date,
            "status": post.status,
            "summary": post.summary,
        }
        for post in posts
    ]


def _category_options(name: str) -> list[dict[str, Any]]:
    """Taxonomy category choices for blog creation controls."""
    taxonomy = ps.load_blog_taxonomy(name)
    nodes = taxonomy.get("taxonomy") if isinstance(taxonomy, dict) else []
    if not isinstance(nodes, list):
        return []
    options: list[dict[str, Any]] = []

    def walk(items: list, path: list[str], titles: list[str]) -> None:
        for item in items:
            if not isinstance(item, dict):
                continue
            slug = _clean_text(item.get("slug"))
            if not slug:
                continue
            title = _clean_text(item.get("title")) or slug
            next_path = [*path, slug]
            next_titles = [*titles, title]
            options.append(
                {
                    "path": next_path,
                    "value": "/".join(next_path),
                    "label": " / ".join(next_titles),
                }
            )
            children = item.get("children")
            if isinstance(children, list):
                walk(children, next_path, next_titles)

    walk(nodes, [], [])
    return options


def _library_payload(name: str) -> tuple[list[dict], list[dict]]:
    try:
        ps.load_public_library(name)
        tree = ps.list_public_library_tree(name, include_trashed=False)
        trash = ps.public_library_trash_nodes(name)
    except Exception:
        return [], []
    return (
        list(tree) if isinstance(tree, list) else [],
        list(trash) if isinstance(trash, list) else [],
    )


def build_blog_workspace_payload(
    name: str,
    *,
    active_slug: str = "",
    status_filter: str = "all",
) -> dict[str, Any]:
    """Build the standalone editor's initial payload from the public layer.

    Only the parts derivable from disk are populated here. AI/visual/preview
    state is owned by the running host and merged in separately.
    """
    posts = ps.load_blog_posts(name, include_drafts=True, include_archived=True)
    clean_filter = _clean_text(status_filter) or "all"
    if clean_filter != "all":
        posts = [post for post in posts if post.status == clean_filter]

    by_slug = {post.slug: post for post in posts}
    slug = _clean_text(active_slug)
    if slug not in by_slug and posts:
        slug = posts[0].slug

    active_post = None
    active_body = ""
    active_blocks: list[dict] = []
    active_meta: dict[str, Any] = {}
    active_category_path: list[str] = []
    active_route = ""
    if slug and slug in by_slug:
        active_post = ps.load_blog_post(name, slug)
        active_body = active_post.body
        active_blocks = list(active_post.blocks_json or [])
        active_meta = dict(active_post.meta)
        active_category_path = list(active_post.category_path or [])
        active_route = getattr(active_post, "route", slug) or slug

    library_tree, trash_nodes = _library_payload(name)

    return {
        "profile": name,
        "posts": _post_rows(posts),
        "active_slug": slug,
        "active_route": active_route,
        "initial_markdown": active_body,
        "initial_blocks": active_blocks,
        "active_post_meta": active_meta,
        "active_category_path": active_category_path,
        "category_options": _category_options(name),
        "library_tree": library_tree,
        "trash_nodes": trash_nodes,
        "status_filter": clean_filter,
    }


# --------------------------------------------------------------------------
# Event dispatch
# --------------------------------------------------------------------------


def _event_action(event: dict) -> str:
    return _clean_text(event.get("action"))


def _event_payload(event: dict) -> dict[str, Any]:
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else {}


def _extract_text_state(
    event: dict,
    *,
    fallback_meta: dict,
    fallback_body: str,
    fallback_blocks: list[dict] | None,
) -> tuple[dict, str, list[dict]]:
    payload = _event_payload(event)
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        meta = fallback_meta
    body = payload.get("markdown")
    if not isinstance(body, str):
        body = event.get("markdown")
    if not isinstance(body, str):
        body = fallback_body
    blocks = payload.get("blocks_json")
    if not isinstance(blocks, list):
        blocks = event.get("blocks_json")
    if not isinstance(blocks, list):
        blocks = fallback_blocks or []
    return dict(meta), body, list(blocks)


def handle_blog_workspace_event(name: str, event: dict) -> BlogEventResult:
    """Dispatch one validated editor event against the public layer.

    Returns a ``BlogEventResult``. For actions outside :data:`HANDLED_ACTIONS`
    the result has ``handled=False`` so the caller can fall back to its own
    (e.g. Streamlit session-coupled) handling.
    """
    action = _event_action(event)
    payload = _event_payload(event)

    if action not in HANDLED_ACTIONS:
        return BlogEventResult(ok=True, handled=False, action=action)

    if action == "select_post":
        slug = _clean_text(payload.get("slug"))
        return BlogEventResult(action=action, slug=slug)

    if action == "save_post":
        slug = _clean_text(payload.get("slug"))
        if not slug:
            return BlogEventResult(ok=False, action=action, errors=["slug is required"])
        post = ps.load_blog_post(name, slug)
        meta, body, blocks = _extract_text_state(
            event,
            fallback_meta=post.meta,
            fallback_body=post.body,
            fallback_blocks=post.blocks_json,
        )
        try:
            saved_path, changed = ps.save_blog_post(
                name, slug, meta, body, blocks_json=blocks
            )
        except ps.PublicSiteError as exc:
            return BlogEventResult(ok=False, action=action, slug=slug, errors=str(exc).split("\n"))
        return BlogEventResult(
            action=action,
            slug=slug,
            changed_paths=[str(saved_path), *[str(p) for p in changed]],
        )

    if action == "run_check":
        slug = _clean_text(payload.get("slug"))
        if not slug:
            return BlogEventResult(ok=False, action=action, errors=["slug is required"])
        post = ps.load_blog_post(name, slug)
        meta, body, _blocks = _extract_text_state(
            event,
            fallback_meta=post.meta,
            fallback_body=post.body,
            fallback_blocks=post.blocks_json,
        )
        candidate = ps._format_front_matter(meta, body)
        result = ps.validate_blog_text_for_publish(name, post.path, candidate)
        return BlogEventResult(
            ok=result.ok,
            action=action,
            slug=slug,
            errors=list(result.errors),
            warnings=list(result.warnings),
        )

    if action == "publish_request":
        slug = _clean_text(payload.get("slug"))
        if not slug:
            return BlogEventResult(ok=False, action=action, errors=["slug is required"])
        post = ps.load_blog_post(name, slug)
        meta, body, blocks = _extract_text_state(
            event,
            fallback_meta=post.meta,
            fallback_body=post.body,
            fallback_blocks=post.blocks_json,
        )
        meta["status"] = "published"
        try:
            published = ps.publish_blog_text(name, slug, meta, body, blocks_json=blocks)
        except ps.PublicSiteError as exc:
            return BlogEventResult(
                ok=False, action=action, slug=slug, errors=str(exc).split("\n")
            )
        return BlogEventResult(
            action=action,
            slug=slug,
            status="published",
            changed_paths=[str(published)],
        )

    if action == "preview_post":
        slug = _clean_text(payload.get("slug"))
        if not slug:
            return BlogEventResult(ok=False, action=action, errors=["slug is required"])
        post = ps.load_blog_post(name, slug)
        meta, body, _blocks = _extract_text_state(
            event,
            fallback_meta=post.meta,
            fallback_body=post.body,
            fallback_blocks=post.blocks_json,
        )
        quality = _clean_text(payload.get("preview_quality")) or "fast"
        try:
            html = ps.render_blog_post_preview(
                name, slug, meta, body, preview_quality=quality
            )
        except ps.PublicSiteError as exc:
            return BlogEventResult(ok=False, action=action, slug=slug, errors=str(exc).split("\n"))
        return BlogEventResult(action=action, slug=slug, extra={"preview_html": html})

    if action == "generate_ai_candidate":
        source = _clean_text(payload.get("source")) or "title"
        try:
            if source == "evidence":
                candidate = ps.blog_candidate_from_evidence(
                    name, _clean_text(payload.get("evidence_id"))
                )
            elif source == "claims":
                candidate = ps.blog_candidate_from_claims(
                    name, _clean_list(payload.get("claim_ids"))
                )
            elif source in {"done", "kanban_done"}:
                candidate = ps.blog_candidate_from_kanban_done(name)
            else:
                meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
                title = (
                    _clean_text(payload.get("title"))
                    or _clean_text(meta.get("title"))
                )
                candidate = ps.blog_candidate_from_title(name, title)
        except ps.PublicSiteError as exc:
            return BlogEventResult(ok=False, action=action, errors=str(exc).split("\n"))
        return BlogEventResult(action=action, extra={"candidate": candidate.to_dict()})

    if action in {"draft_from_evidence", "draft_from_claims", "draft_from_done"}:
        try:
            if action == "draft_from_evidence":
                path = ps.draft_blog_from_evidence(
                    name, _clean_text(payload.get("evidence_id"))
                )
            elif action == "draft_from_claims":
                path = ps.draft_blog_from_claims(
                    name, _clean_list(payload.get("claim_ids"))
                )
            else:
                path = ps.draft_blog_from_kanban_done(name)
        except (ps.PublicSiteError, ValueError) as exc:
            return BlogEventResult(ok=False, action=action, errors=str(exc).split("\n"))
        return BlogEventResult(action=action, slug=ps.parse_blog_post(path).slug)

    if action == "delete_media":
        slug = _clean_text(payload.get("slug"))
        rel = _clean_text(payload.get("rel") or payload.get("relative_path"))
        if not slug or not rel:
            return BlogEventResult(ok=False, action=action, errors=["slug and rel are required"])
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else None
        body = payload.get("markdown") if isinstance(payload.get("markdown"), str) else None
        try:
            ps.delete_blog_media(name, slug, rel, meta=meta, body=body)
        except ps.PublicSiteError as exc:
            return BlogEventResult(ok=False, action=action, slug=slug, errors=str(exc).split("\n"))
        return BlogEventResult(action=action, slug=slug)

    if action == "convert_media_video":
        slug = _clean_text(payload.get("slug"))
        rel = _clean_text(payload.get("rel") or payload.get("relative_path"))
        if not slug or not rel:
            return BlogEventResult(ok=False, action=action, errors=["slug and rel are required"])
        try:
            result = ps.convert_blog_media_video(name, slug, rel)
        except ps.PublicSiteError as exc:
            return BlogEventResult(ok=False, action=action, slug=slug, errors=str(exc).split("\n"))
        return BlogEventResult(action=action, slug=slug, extra={"media": result.to_dict()})

    if action == "upload_media":
        slug = _clean_text(payload.get("slug"))
        if not slug:
            return BlogEventResult(ok=False, action=action, errors=["slug is required"])
        kind = _clean_text(payload.get("kind")).lower() or "image"
        cover = bool(payload.get("cover", False))
        if cover and kind != "image":
            return BlogEventResult(ok=False, action=action, slug=slug, errors=["Only images can be set as cover."])
        try:
            data = _decode_upload_payload(payload)
            result = ps.add_blog_media_bytes(
                name,
                slug,
                data=data,
                filename=_clean_text(payload.get("filename")) or "upload.bin",
                kind=kind,
                alt=_clean_text(payload.get("alt")),
                caption=_clean_text(payload.get("caption")),
                cover=cover,
                append=bool(payload.get("append", False)),
            )
        except ps.PublicSiteError as exc:
            return BlogEventResult(ok=False, action=action, slug=slug, errors=str(exc).split("\n"))
        return BlogEventResult(action=action, slug=slug, extra={"media": result.to_dict()})

    if action == "library_upload_media":
        try:
            data = _decode_upload_payload(payload)
            result = ps.add_public_library_media_bytes(
                name,
                _clean_text(payload.get("parent_id")) or None,
                data=data,
                filename=_clean_text(payload.get("filename")) or "upload.bin",
                kind=_clean_text(payload.get("kind")).lower() or "image",
                title=_clean_text(payload.get("title")),
            )
        except ps.PublicSiteError as exc:
            return BlogEventResult(ok=False, action=action, errors=str(exc).split("\n"))
        return BlogEventResult(
            action=action,
            extra={"node_id": _result_node_id(result), "media": _result_to_dict(result)},
        )

    if action == "library_attach_existing":
        try:
            result = ps.attach_existing_public_library_node(
                name,
                _clean_text(payload.get("parent_id")) or None,
                _clean_text(payload.get("ref")),
                _clean_text(payload.get("title")),
                visibility=_clean_text(payload.get("visibility")),
            )
        except ps.PublicSiteError as exc:
            return BlogEventResult(ok=False, action=action, errors=str(exc).split("\n"))
        return BlogEventResult(action=action, slug=_result_slug(result))

    if action in {"create_post", "library_create_post"}:
        title = _clean_text(payload.get("title")) or "Untitled"
        parent_id = _clean_text(payload.get("parent_id"))
        category_path = _clean_list(payload.get("category_path"))
        try:
            if parent_id:
                created = ps.create_blog_draft_in_library(
                    name,
                    parent_id,
                    title,
                    "",
                    "",
                )
                new_slug = _result_slug(created)
            else:
                path = ps.create_blog_draft(
                    name,
                    title=title,
                    body="",
                    summary="",
                    category_path=category_path or None,
                )
                new_slug = ps.parse_blog_post(path).slug
        except (ps.PublicSiteError, ValueError, TypeError) as exc:
            return BlogEventResult(ok=False, action=action, errors=str(exc).split("\n"))
        return BlogEventResult(action=action, slug=new_slug, message=title)

    # Public library structural operations -------------------------------
    if action == "library_select_node":
        return BlogEventResult(action=action, extra={"node_id": _clean_text(payload.get("node_id"))})

    if action == "library_create_folder":
        title = _clean_text(payload.get("title")) or "Folder"
        parent_id = _clean_text(payload.get("parent_id"))
        try:
            ps.create_public_library_folder(name, parent_id or None, title)
        except Exception as exc:
            return BlogEventResult(ok=False, action=action, errors=[str(exc)])
        return BlogEventResult(action=action, message=title)

    if action == "library_rename_node":
        node_id = _clean_text(payload.get("node_id"))
        title = _clean_text(payload.get("title"))
        try:
            ps.rename_public_library_node(name, node_id, title)
        except Exception as exc:
            return BlogEventResult(ok=False, action=action, errors=[str(exc)])
        return BlogEventResult(action=action, extra={"node_id": node_id})

    if action == "library_move_node":
        node_id = _clean_text(payload.get("node_id"))
        target = _clean_text(payload.get("target_parent_id")) or _clean_text(
            payload.get("parent_id")
        )
        try:
            ps.move_public_library_node(name, node_id, target or None)
        except Exception as exc:
            return BlogEventResult(ok=False, action=action, errors=[str(exc)])
        return BlogEventResult(action=action, extra={"node_id": node_id})

    if action == "library_reorder_node":
        node_id = _clean_text(payload.get("node_id"))
        before_node_id = _clean_text(payload.get("before_node_id"))
        after_node_id = _clean_text(payload.get("after_node_id"))
        try:
            if before_node_id or after_node_id:
                ps.position_public_library_node(
                    name,
                    node_id,
                    parent_id=(
                        _clean_text(payload.get("target_parent_id"))
                        or _clean_text(payload.get("parent_id"))
                        or None
                    ),
                    before_node_id=before_node_id,
                    after_node_id=after_node_id,
                )
            else:
                ps.reorder_public_library_node(
                    name, node_id, _clean_text(payload.get("direction"))
                )
        except Exception as exc:
            return BlogEventResult(ok=False, action=action, errors=[str(exc)])
        return BlogEventResult(action=action, extra={"node_id": node_id})

    if action == "library_trash_node":
        try:
            ps.trash_public_library_node(name, _clean_text(payload.get("node_id")))
        except Exception as exc:
            return BlogEventResult(ok=False, action=action, errors=[str(exc)])
        return BlogEventResult(action=action)

    if action == "library_restore_node":
        try:
            ps.restore_public_library_node(name, _clean_text(payload.get("node_id")))
        except Exception as exc:
            return BlogEventResult(ok=False, action=action, errors=[str(exc)])
        return BlogEventResult(action=action)

    if action == "library_permanent_delete_node":
        node_id = _clean_text(payload.get("node_id"))
        ref = _clean_text(payload.get("ref"))
        delete_files = bool(payload.get("delete_files", False))
        trash_first = bool(payload.get("trash_first", False))
        # Virtual posts (markdown on disk, not yet in the library yaml) carry an
        # ``post:<route>`` id and no real node. Materialize them first so the
        # standard trash + purge flow can remove both the node and the file.
        is_virtual = not node_id or node_id.startswith("post:")
        try:
            if is_virtual:
                if not ref:
                    raise ValueError("missing ref for virtual post deletion")
                result = ps.attach_existing_public_library_node(
                    name,
                    _clean_text(payload.get("parent_id")) or None,
                    ref,
                    _clean_text(payload.get("title")),
                )
                node_id = _result_node_id(result) or node_id
                trash_first = True
            # Active nodes (e.g. a freshly created post) must be trashed before
            # they can be purged; the editor signals this via trash_first.
            if trash_first:
                try:
                    ps.trash_public_library_node(
                        name,
                        node_id,
                        recursive=bool(payload.get("recursive", True)),
                    )
                except Exception as exc:
                    if "trash" not in str(exc).lower():
                        raise
            ps.purge_public_library_node(
                name,
                node_id,
                delete_files=delete_files,
            )
        except Exception as exc:
            return BlogEventResult(ok=False, action=action, errors=[str(exc)])
        return BlogEventResult(action=action)

    return BlogEventResult(ok=True, handled=False, action=action)
