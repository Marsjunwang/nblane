"""Paper library tree, search, and detail UI."""
from __future__ import annotations

import html
import os

import streamlit as st
import yaml

from nblane.core.paper_library_workspace import (
    build_paper_library_payload,
    handle_paper_library_event,
    resolve_paper_library_runtime,
)
from nblane.core.research_papers import (
    auto_chunk_paper,
    create_paper_library_node,
    ensure_paper_reading_artifacts,
    extract_paper_pages,
    extract_paper_segments,
    grobid_readiness,
    move_papers_to_node,
    paper_library_paths,
    paper_rows,
    position_paper_library_node,
    purge_paper_library_node,
    remove_papers_from_node,
    rename_paper_library_node,
    reorder_paper_library_node,
    restore_paper_library_node,
    trash_paper_library_node,
    validate_paper_library,
)
from nblane.core.research_sources import (
    SOURCE_STATUSES,
    update_research_source,
)
from nblane.paper_library_component import (
    paper_library_component_available,
    st_paper_library_tree,
)
from nblane.web_cache import (
    clear_web_cache,
    load_chunks,
    load_paper_annotations,
    load_paper_library_tree,
    load_paper_pages,
    load_paper_segments,
    load_paper_translations,
    load_research_sources,
)
from nblane.web_shared import (
    assert_files_current,
    refresh_file_snapshots,
    stash_git_backup_results,
)

from .context import ResearchContext
from ._helpers import (
    _cached_paper_rows,
    _l,
    _node_options,
    _node_select_index,
    _paper_library_key,
    _paper_library_sidecar_status,
    _paper_library_sidecar_unavailable,
    _paper_library_workspace_url,
    _reader_api_base,
    _reader_view_url,
    _render_iframe,
    _render_sidecar_link_button,
    _short_text,
    _source_label,
    _status_label,
    _tags,
    _unique_text,
)
from .source_inbox import _save_sources
from .paper_search import _render_paper_search, _search_state_key


_LIBRARY_VIEW_LABELS = {
    "all": "All Papers",
    "unsorted": "Unsorted Inbox",
    "reading": "Reading",
    "no_pdf": "PDF Missing",
    "needs_extraction": "Needs Extraction",
    "claims_need_review": "Claims Need Review",
    "duplicate_risk": "Duplicate Risk",
    "stale_translation": "Stale Translation",
    "recent": "Recently Read",
    "private": "Private Sources",
    "reviewed": "Reviewed",
    "archived": "Archived",
    "discarded": "Discarded",
}


_LIBRARY_VIEW_GROUPS = (
    ("library", "Library", ("all", "unsorted", "recent")),
    (
        "work_queue",
        "Work Queue",
        (
            "reading",
            "no_pdf",
            "needs_extraction",
            "claims_need_review",
            "duplicate_risk",
            "stale_translation",
        ),
    ),
    ("system", "System", ("private", "reviewed", "archived", "discarded")),
)


_TECHNICAL_TAXONOMY_LABELS = (
    ("topics", "Topics"),
    ("methods", "Methods"),
    ("datasets", "Datasets"),
    ("benchmarks", "Benchmarks"),
)


def _badge_html(label: object, *, tone: str = "neutral") -> str:
    clean = html.escape(str(label or "").strip())
    if not clean:
        return ""
    return f'<span class="paper-badge paper-badge-{tone}">{clean}</span>'


def _badge_tone(label: object) -> str:
    text = str(label or "").lower()
    if any(part in text for part in ("missing", "broken", "failed", "warning")):
        return "warn"
    if any(part in text for part in ("duplicate", "stale", "needs")):
        return "alert"
    if any(part in text for part in ("ready", "pdf", "reviewed")):
        return "ok"
    return "neutral"


def _paper_badges_html(row: dict[str, object], *, limit: int = 5) -> str:
    badges = [str(item) for item in row.get("badges", []) if str(item).strip()]
    if row.get("has_pdf") and "PDF ready" not in badges:
        badges.insert(0, "PDF ready")
    if not badges:
        return ""
    visible = badges[:limit]
    rendered = [_badge_html(label, tone=_badge_tone(label)) for label in visible]
    if len(badges) > limit:
        rendered.append(_badge_html(f"+{len(badges) - limit}", tone="neutral"))
    return " ".join(item for item in rendered if item)


def _paper_primary_meta(row: dict[str, object]) -> str:
    parts = []
    if row.get("authors"):
        parts.append(_short_text(row.get("authors"), 80))
    if row.get("published"):
        parts.append(str(row.get("published")))
    if row.get("venue"):
        parts.append(str(row.get("venue")))
    if row.get("tree_path"):
        parts.append(str(row.get("tree_path")))
    return " · ".join(part for part in parts if part)


def _paper_tag_line(row: dict[str, object]) -> str:
    tags = [str(tag) for tag in row.get("tags", []) if str(tag).strip()]
    return " ".join(_badge_html(tag, tone="tag") for tag in tags[:6])


def _library_badge_set(row: dict[str, object]) -> set[str]:
    return {str(item) for item in row.get("badges", []) if str(item).strip()}


def _library_row_matches_view(row: dict[str, object], view: str) -> bool:
    badges = _library_badge_set(row)
    source = row.get("source")
    status = str(row.get("status") or "")
    visibility = str(row.get("visibility") or "")
    if view == "all":
        return True
    if view == "unsorted":
        return str(row.get("tree_path") or "") == "Unsorted" or "Unsorted" in badges
    if view in {"reading", "archived", "discarded"}:
        return status == view
    if view == "candidate_ready":
        return status == "candidate_ready" or "AI candidates" in badges
    if view == "no_pdf":
        return not bool(row.get("has_pdf"))
    if view == "needs_extraction":
        return bool(row.get("has_pdf")) and (
            not int(row.get("chunks_count") or 0) or "Needs structured extraction" in badges
        )
    if view == "claims_need_review":
        return status == "candidate_ready" or "AI candidates" in badges
    if view == "duplicate_risk":
        return "Duplicate risk" in badges
    if view == "stale_translation":
        return "Stale translation" in badges
    if view == "recent":
        return bool(row.get("last_read"))
    if view == "private":
        return visibility == "private"
    if view == "reviewed":
        return status == "summarized" or bool(getattr(source, "evidence_refs", []))
    return True


def _library_view_count(rows: list[dict[str, object]], view: str) -> int:
    return sum(1 for row in rows if _library_row_matches_view(row, view))


def _paper_node_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        source = row.get("source")
        for ref in getattr(source, "library_node_refs", []) or []:
            counts[str(ref)] = counts.get(str(ref), 0) + 1
    return counts


def _paper_tree_buttons(ctx, tree, rows: list[dict[str, object]]) -> None:
    ui = ctx.ui
    counts = _paper_node_counts(rows)
    nodes = {node.id: node for node in tree.nodes if node.status != "trashed"}
    children: dict[str, list] = {}
    for node in tree.nodes:
        if node.status == "trashed":
            continue
        children.setdefault(node.parent_id or "", []).append(node)

    current_node = str(st.session_state.get(_paper_library_key(ctx, "node"), "") or "")

    def walk(parent_id: str = "", depth: int = 0, seen: set[str] | None = None) -> None:
        seen = seen or set()
        for node in sorted(children.get(parent_id, []), key=lambda item: (item.order, item.title)):
            if node.id in seen:
                continue
            prefix = "  " * depth + ("> " if depth else "")
            label = f"{prefix}{node.title} ({counts.get(node.id, 0)})"
            button_type = "primary" if current_node == node.id else "secondary"
            if st.button(label, key=_paper_library_key(ctx, f"node:{node.id}"), type=button_type, use_container_width=True):
                st.session_state[_paper_library_key(ctx, "node")] = node.id
                st.session_state[_paper_library_key(ctx, "view")] = "all"
                st.session_state.pop(_paper_library_key(ctx, "detail"), None)
                st.rerun()
            walk(node.id, depth + 1, seen | {node.id})

    if not nodes:
        st.caption(_l(ui, "tree_empty", "No library nodes yet."))
        return
    walk()


def _render_library_view_button(ctx, 
    view_id: str,
    fallback: str,
    rows: list[dict[str, object]],
    current_view: str,
    current_node: str,
) -> None:
    ui = ctx.ui
    count = _library_view_count(rows, view_id)
    label = f"{_l(ui, f'library_view_{view_id}', fallback)} ({count})"
    button_type = "primary" if current_view == view_id and not current_node else "secondary"
    if st.button(
        label,
        key=_paper_library_key(ctx, f"view:{view_id}"),
        type=button_type,
        use_container_width=True,
    ):
        st.session_state[_paper_library_key(ctx, "view")] = view_id
        st.session_state[_paper_library_key(ctx, "node")] = ""
        st.session_state.pop(_paper_library_key(ctx, "detail"), None)
        st.rerun()


def _render_library_view_group(ctx, 
    group_id: str,
    fallback: str,
    view_ids: tuple[str, ...],
    rows: list[dict[str, object]],
    current_view: str,
    current_node: str,
) -> None:
    ui = ctx.ui
    st.markdown(f"**{_l(ui, f'library_group_{group_id}', fallback)}**")
    for view_id in view_ids:
        _render_library_view_button(ctx, 
            view_id,
            _LIBRARY_VIEW_LABELS.get(view_id, view_id),
            rows,
            current_view,
            current_node,
        )


def _paper_collection_tree_items(ctx, tree, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    _pdir = ctx.pdir
    ui = ctx.ui
    counts = _paper_node_counts(rows)
    paths = paper_library_paths(_pdir)
    children: dict[str, list] = {}
    for node in tree.nodes:
        if node.status == "trashed":
            continue
        children.setdefault(node.parent_id or "", []).append(node)

    def walk(parent_id: str = "") -> list[dict[str, object]]:
        out: list[dict[str, object]] = []
        for node in sorted(children.get(parent_id, []), key=lambda item: (item.order, item.title.lower(), item.id)):
            out.append(
                {
                    "id": node.id,
                    "type": "collection",
                    "title": node.title,
                    "path": paths.get(node.id, node.title),
                    "description": node.description,
                    "count": counts.get(node.id, 0),
                    "parent_id": node.parent_id,
                    "color": node.color,
                    "icon": node.icon,
                    "children": walk(node.id),
                }
            )
        return out

    return [
        {
            "id": "collections:all",
            "type": "collection_root",
            "node_id": "",
            "title": _l(ui, "clear_tree_filter", "All collections"),
            "count": len(rows),
            "children": walk(""),
        }
    ]


def _paper_library_component_payload(ctx, 
    tree,
    rows: list[dict[str, object]],
    *,
    current_view: str,
    current_node: str,
    selected_paper_ids: list[str],
    papers: list[dict[str, object]] | None = None,
    active_label: str = "",
    detail_id: str = "",
) -> dict[str, object]:
    ui = ctx.ui
    def view_items(view_ids: tuple[str, ...]) -> list[dict[str, object]]:
        return [
            {
                "id": view_id,
                "type": "view",
                "title": _l(ui, f"library_view_{view_id}", _LIBRARY_VIEW_LABELS.get(view_id, view_id)),
                "count": _library_view_count(rows, view_id),
            }
            for view_id in view_ids
        ]

    return {
        "active_view": current_view,
        "active_node_id": current_node,
        "active_label": active_label,
        "detail_id": detail_id,
        "selected_paper_ids": list(selected_paper_ids),
        "papers": list(papers or []),
        "sections": [
            {
                "id": "library",
                "title": _l(ui, "library_group_library", "Library"),
                "items": view_items(_LIBRARY_VIEW_GROUPS[0][2]),
            },
            {
                "id": "collections",
                "title": _l(ui, "collections", "Collections"),
                "items": _paper_collection_tree_items(ctx, tree, rows),
            },
            {
                "id": "technical_taxonomy",
                "title": _l(ui, "technical_taxonomy", "Technical Taxonomy"),
                "items": [
                    {
                        "id": f"technical:{taxonomy_id}",
                        "type": "taxonomy",
                        "title": _l(ui, f"technical_taxonomy_{taxonomy_id}", fallback),
                        "count": 0,
                    }
                    for taxonomy_id, fallback in _TECHNICAL_TAXONOMY_LABELS
                ],
            },
            {
                "id": "work_queue",
                "title": _l(ui, "library_group_work_queue", "Work Queue"),
                "items": view_items(_LIBRARY_VIEW_GROUPS[1][2]),
            },
            {
                "id": "system",
                "title": _l(ui, "library_group_system", "System"),
                "items": view_items(_LIBRARY_VIEW_GROUPS[2][2]),
            },
        ],
        "capabilities": {
            "create_collection": True,
            "rename_collection": True,
            "move_collection": True,
            "delete_collection": True,
            "drop_papers": True,
        },
        "labels": {
            "add_selected_here": _l(ui, "add_selected_here", "Add selected papers here"),
            "add_to_collection": _l(ui, "add_to_collection", "Add to collection"),
            "archive": _l(ui, "archive", "Archive"),
            "cancel": _l(ui, "cancel", "Cancel"),
            "collapse": _l(ui, "collapse", "Collapse"),
            "collapse_all": _l(ui, "collapse_all", "Collapse all"),
            "collection_actions": _l(ui, "collection_actions", "Collection actions"),
            "collection_title": _l(ui, "collection_title", "Collection title"),
            "delete_collection": _l(ui, "delete_collection", "Delete collection"),
            "discard": _l(ui, "discard", "Discard"),
            "expand": _l(ui, "expand", "Expand"),
            "expand_all": _l(ui, "expand_all", "Expand all"),
            "mark_as_reading": _l(ui, "mark_as_reading", "Mark as reading"),
            "move_collection": _l(ui, "move_collection", "Move collection"),
            "move_down": _l(ui, "move_down", "Move down"),
            "move_papers_to_collection": _l(ui, "move_papers_to_collection", "Move papers to collection"),
            "move_papers_to_parent": _l(ui, "move_papers_to_parent", "Move papers to parent collection"),
            "move_papers_to_unsorted": _l(ui, "move_papers_to_unsorted", "Move papers to Unsorted Inbox"),
            "move_selected_here": _l(ui, "move_selected_here", "Move selected papers here"),
            "move_to_collection": _l(ui, "move_to_collection", "Move to collection"),
            "move_up": _l(ui, "move_up", "Move up"),
            "new_collection": _l(ui, "new_collection", "New collection"),
            "new_subcollection": _l(ui, "new_subcollection", "New subcollection"),
            "open_reader": _l(ui, "open_reader", "Open Reader"),
            "paper_policy": _l(ui, "paper_policy", "Paper policy"),
            "parent_collection": _l(ui, "parent_collection", "Parent collection"),
            "remove_from_current_collection": _l(ui, "remove_from_current_collection", "Remove from current collection"),
            "rename": _l(ui, "rename", "Rename"),
            "run_extraction": _l(ui, "run_extraction", "Run extraction"),
            "save": _l(ui, "save", "Save"),
            "search_collections": _l(ui, "search_collections", "Search collections"),
            "selected_papers": _l(ui, "selected_papers", "{count} papers selected"),
            "select_all": _l(ui, "select_all", "Select all"),
            "clear_selection": _l(ui, "clear_selection", "Clear"),
            "select_paper": _l(ui, "select_paper", "Select paper"),
            "show_details": _l(ui, "show_details", "Show details"),
            "library_empty": _l(ui, "library_empty", "No papers match this view."),
            "library_result_count": _l(ui, "paper_list_result_count", "{count} papers"),
            "target_collection": _l(ui, "target_collection", "Target collection"),
            "top_level": _l(ui, "top_level", "Top level"),
        },
    }


def _handle_paper_library_component_event(ctx, event: dict[str, object] | None) -> None:
    selected = ctx.selected
    _pdir = ctx.pdir
    _sources_path = ctx.sources_path
    if not isinstance(event, dict):
        return
    action = str(event.get("action") or "")
    if not action:
        return
    event_id = str(event.get("event_id") or "")
    dedupe_key = _paper_library_key(ctx, "component_last_event")
    if event_id and st.session_state.get(dedupe_key) == event_id:
        return
    if event_id:
        st.session_state[dedupe_key] = event_id

    try:
        source_mutating_actions = {
            "paper_library_trash_collection",
            "paper_library_purge_collection",
            "paper_library_add_selected_papers_to_collection",
            "paper_library_move_selected_papers_to_collection",
            "paper_library_drop_papers_to_collection",
            "paper_library_remove_papers_from_collection",
            "paper_library_update_papers_status",
            "paper_library_run_extraction",
            "paper_library_auto_chunk",
            "paper_library_delete_paper_record",
            "paper_library_delete_paper_asset",
            "paper_library_delete_paper_artifacts",
            "paper_library_purge_discarded_papers",
        }
        if action in source_mutating_actions:
            assert_files_current([_sources_path])
        result = handle_paper_library_event(
            _pdir,
            event,
            selected_paper_ids=[
                str(item).strip()
                for item in st.session_state.get(_paper_library_key(ctx, "bulk_select"), []) or []
                if str(item).strip()
            ],
        )
        if not result.ok:
            if result.message:
                st.error(result.message)
            return
        if action in source_mutating_actions:
            refresh_file_snapshots([_sources_path])

        next_state = result.next
        if "view" in next_state:
            st.session_state[_paper_library_key(ctx, "view")] = next_state.get("view") or "all"
        if "node_id" in next_state:
            st.session_state[_paper_library_key(ctx, "node")] = next_state.get("node_id") or ""
        if "detail_id" in next_state:
            detail_id = next_state.get("detail_id") or ""
            if detail_id:
                st.session_state[_paper_library_key(ctx, "detail")] = detail_id
            else:
                st.session_state.pop(_paper_library_key(ctx, "detail"), None)
        if "reader_source_id" in next_state and next_state["reader_source_id"]:
            st.session_state[f"paper_reader_source:{selected}"] = next_state["reader_source_id"]

        if result.changed:
            stash_git_backup_results()
            clear_web_cache()
        if result.message:
            st.success(result.message if result.changed else result.message)
        st.rerun()
    except Exception as exc:
        st.error(str(exc))


def _render_paper_library_styles() -> None:
    st.markdown(
        """
<style>
.paper-card {
  border: 1px solid rgba(49, 51, 63, 0.16);
  border-radius: 8px;
  padding: 0.8rem 0.9rem;
  margin: 0 0 0.75rem 0;
  background: rgba(255, 255, 255, 0.82);
}
.paper-card-active {
  border-color: rgba(33, 115, 220, 0.7);
  background: rgba(33, 115, 220, 0.06);
}
.paper-title {
  font-weight: 700;
  font-size: 1.02rem;
  line-height: 1.35;
  color: rgb(31, 41, 55);
  margin-bottom: 0.22rem;
}
.paper-meta {
  color: rgba(49, 51, 63, 0.68);
  font-size: 0.82rem;
  line-height: 1.35;
  margin-bottom: 0.45rem;
}
.paper-summary {
  color: rgba(49, 51, 63, 0.82);
  font-size: 0.88rem;
  line-height: 1.45;
  margin: 0.35rem 0 0.55rem 0;
}
.paper-badge {
  display: inline-block;
  border-radius: 999px;
  padding: 0.12rem 0.45rem;
  margin: 0.08rem 0.16rem 0.08rem 0;
  font-size: 0.72rem;
  line-height: 1.35;
  border: 1px solid rgba(49, 51, 63, 0.14);
  background: rgba(49, 51, 63, 0.055);
  color: rgba(31, 41, 55, 0.86);
}
.paper-badge-ok {
  border-color: rgba(22, 163, 74, 0.22);
  background: rgba(22, 163, 74, 0.09);
  color: rgb(22, 101, 52);
}
.paper-badge-warn {
  border-color: rgba(245, 158, 11, 0.32);
  background: rgba(245, 158, 11, 0.12);
  color: rgb(146, 64, 14);
}
.paper-badge-alert {
  border-color: rgba(220, 38, 38, 0.24);
  background: rgba(220, 38, 38, 0.08);
  color: rgb(153, 27, 27);
}
.paper-badge-tag {
  border-color: rgba(37, 99, 235, 0.18);
  background: rgba(37, 99, 235, 0.075);
  color: rgb(30, 64, 175);
}
.paper-detail-title {
  font-size: 1.05rem;
  font-weight: 750;
  line-height: 1.35;
  margin-bottom: 0.25rem;
}
.paper-muted {
  color: rgba(49, 51, 63, 0.65);
  font-size: 0.82rem;
}
</style>
""",
        unsafe_allow_html=True,
    )


def _render_grobid_status_block(ctx, source=None) -> None:
    ui = ctx.ui
    configured = bool(os.getenv("NBLANE_GROBID_URL", "").strip())
    with st.expander(_l(ui, "grobid_readiness", "GROBID readiness"), expanded=False):
        if not configured:
            st.info(
                _l(ui, 
                    "grobid_not_configured",
                    "NBLANE_GROBID_URL is not configured; structured extraction will try the local GROBID default and fall back if unavailable.",
                )
            )
            if source is not None:
                metadata = source.metadata or {}
                warnings = metadata.get("structured_extraction_warnings") or []
                for warning in warnings:
                    st.warning(str(warning))
                st.caption(
                    " · ".join(
                        [
                            f"structure_backend={metadata.get('structure_backend', '') or 'missing'}",
                            f"structured_extracted_at={metadata.get('structured_extracted_at', '') or 'never'}",
                        ]
                    )
                )
            return
        try:
            status = grobid_readiness()
            if status.get("available"):
                st.success(str(status.get("message") or "GROBID available."))
            else:
                st.warning(str(status.get("message") or "GROBID unavailable."))
            st.code(
                yaml.dump(status, allow_unicode=True, default_flow_style=False, sort_keys=False),
                language="yaml",
            )
        except Exception as exc:
            st.warning(str(exc))
        if source is not None:
            metadata = source.metadata or {}
            warnings = metadata.get("structured_extraction_warnings") or []
            if warnings:
                for warning in warnings:
                    st.warning(str(warning))
            st.caption(
                " · ".join(
                    [
                        f"structure_backend={metadata.get('structure_backend', '') or 'missing'}",
                        f"structured_extracted_at={metadata.get('structured_extracted_at', '') or 'never'}",
                    ]
                )
            )


def _render_library_collection_manager(ctx, tree, node_options: dict[str, str]) -> None:
    _pdir = ctx.pdir
    ui = ctx.ui
    _sources_path = ctx.sources_path
    with st.expander(_l(ui, "manage_collections", "Manage collections"), expanded=False):
        paths = paper_library_paths(_pdir)
        active_node_options = {node_id: label for node_id, label in node_options.items() if node_id}
        node_counts = _paper_node_counts(paper_rows(_pdir, view="all"))
        if tree.nodes:
            st.dataframe(
                [
                    {
                        "path": paths.get(node.id, node.title),
                        "description": node.description,
                        "status": node.status,
                        "papers": node_counts.get(node.id, 0),
                    }
                    for node in tree.nodes
                ],
                use_container_width=True,
                hide_index=True,
            )
        current_node = str(st.session_state.get(_paper_library_key(ctx, "node"), "") or "")
        parent_options = {"": _l(ui, "top_level", "Top level"), **active_node_options}

        st.markdown(f"**{_l(ui, 'new_collection', 'New collection')}**")
        with st.form(_paper_library_key(ctx, "collection_create")):
            default_parent = current_node if current_node in parent_options else ""
            parent_id = st.selectbox(
                _l(ui, "parent_collection", "Parent collection"),
                options=list(parent_options),
                index=_node_select_index(parent_options, default_parent),
                format_func=lambda ref: parent_options.get(ref, ref),
            )
            title = st.text_input(_l(ui, "collection_title", "Collection title"))
            c1, c2 = st.columns(2)
            with c1:
                icon = st.text_input(_l(ui, "collection_icon", "Icon"))
            with c2:
                color = st.text_input(_l(ui, "collection_color", "Color"))
            description = st.text_area(ui["notes"], height=72)
            create_submitted = st.form_submit_button(_l(ui, "create", "Create"), type="primary")
        if create_submitted:
            try:
                create_paper_library_node(
                    _pdir,
                    title,
                    parent_id=parent_id,
                    description=description,
                    color=color,
                    icon=icon,
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(_l(ui, "created", "Created: {id}").format(id=title))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if active_node_options:
            st.markdown(f"**{_l(ui, 'edit_collection', 'Edit collection')}**")
            selected_node_id = st.selectbox(
                _l(ui, "collection", "Collection"),
                options=list(active_node_options),
                index=_node_select_index(active_node_options, current_node),
                format_func=lambda ref: active_node_options.get(ref, ref),
                key=_paper_library_key(ctx, "manage_selected_node"),
            )
            selected_node = tree.by_id().get(selected_node_id)
            if selected_node is not None:
                with st.form(_paper_library_key(ctx, f"collection_rename:{selected_node_id}")):
                    next_title = st.text_input(
                        _l(ui, "collection_title", "Collection title"),
                        value=selected_node.title,
                    )
                    rename_submitted = st.form_submit_button(_l(ui, "rename", "Rename"), type="primary")
                if rename_submitted:
                    try:
                        rename_paper_library_node(_pdir, selected_node_id, next_title)
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(ui["saved"])
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

                move_parent_options = {
                    key: value
                    for key, value in parent_options.items()
                    if key != selected_node_id
                }
                with st.form(_paper_library_key(ctx, f"collection_move:{selected_node_id}")):
                    next_parent = st.selectbox(
                        _l(ui, "move_under", "Move under"),
                        options=list(move_parent_options),
                        index=_node_select_index(move_parent_options, selected_node.parent_id),
                        format_func=lambda ref: move_parent_options.get(ref, ref),
                    )
                    move_submitted = st.form_submit_button(
                        _l(ui, "move_collection", "Move collection"),
                        type="secondary",
                    )
                if move_submitted:
                    try:
                        position_paper_library_node(_pdir, selected_node_id, parent_id=next_parent)
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(ui["saved"])
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

                r1, r2 = st.columns(2)
                with r1:
                    if st.button(
                        _l(ui, "move_up", "Move up"),
                        key=_paper_library_key(ctx, f"collection_up:{selected_node_id}"),
                        icon=":material/arrow_upward:",
                        use_container_width=True,
                    ):
                        try:
                            reorder_paper_library_node(_pdir, selected_node_id, "up")
                            stash_git_backup_results()
                            clear_web_cache()
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                with r2:
                    if st.button(
                        _l(ui, "move_down", "Move down"),
                        key=_paper_library_key(ctx, f"collection_down:{selected_node_id}"),
                        icon=":material/arrow_downward:",
                        use_container_width=True,
                    ):
                        try:
                            reorder_paper_library_node(_pdir, selected_node_id, "down")
                            stash_git_backup_results()
                            clear_web_cache()
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

                with st.form(_paper_library_key(ctx, f"collection_delete:{selected_node_id}")):
                    delete_policy = st.selectbox(
                        _l(ui, "paper_policy", "Paper policy"),
                        options=["move_to_parent", "move_to_unsorted", "move_to_collection"],
                        format_func=lambda value: {
                            "move_to_parent": _l(ui, "move_papers_to_parent", "Move papers to parent collection"),
                            "move_to_unsorted": _l(ui, "move_papers_to_unsorted", "Move papers to Unsorted Inbox"),
                            "move_to_collection": _l(ui, "move_papers_to_collection", "Move papers to collection"),
                        }.get(value, value),
                    )
                    policy_target = ""
                    if delete_policy == "move_to_collection":
                        target_options = {
                            key: value
                            for key, value in active_node_options.items()
                            if key != selected_node_id
                        }
                        if target_options:
                            policy_target = st.selectbox(
                                _l(ui, "target_collection", "Target collection"),
                                options=list(target_options),
                                format_func=lambda ref: target_options.get(ref, ref),
                            )
                        else:
                            st.caption(_l(ui, "no_target_collections", "No target collections."))
                    confirmed = st.checkbox(_l(ui, "confirm_delete", "Confirm delete"))
                    delete_submitted = st.form_submit_button(
                        _l(ui, "delete_collection", "Delete collection"),
                        type="secondary",
                    )
                if delete_submitted:
                    if not confirmed:
                        st.warning(_l(ui, "confirm_delete_required", "Confirm delete first."))
                    elif delete_policy == "move_to_collection" and not policy_target:
                        st.warning(_l(ui, "target_collection_required", "Choose a target collection first."))
                    else:
                        try:
                            assert_files_current([_sources_path])
                            policy = f"move_to:{policy_target}" if delete_policy == "move_to_collection" else delete_policy
                            trash_paper_library_node(_pdir, selected_node_id, paper_policy=policy)
                            refresh_file_snapshots([_sources_path])
                            stash_git_backup_results()
                            clear_web_cache()
                            st.success(ui["saved"])
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

        trashed_nodes = [node for node in tree.nodes if node.status == "trashed"]
        if trashed_nodes:
            st.markdown(f"**{_l(ui, 'collection_trash', 'Trash')}**")
            trash_options = {node.id: paths.get(node.id, node.title) for node in trashed_nodes}
            trashed_id = st.selectbox(
                _l(ui, "collection", "Collection"),
                options=list(trash_options),
                format_func=lambda ref: trash_options.get(ref, ref),
                key=_paper_library_key(ctx, "trashed_node"),
            )
            t1, t2 = st.columns(2)
            with t1:
                if st.button(
                    _l(ui, "restore", "Restore"),
                    key=_paper_library_key(ctx, f"restore:{trashed_id}"),
                    icon=":material/restore:",
                    use_container_width=True,
                ):
                    try:
                        restore_paper_library_node(_pdir, trashed_id)
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(ui["saved"])
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with t2:
                if st.button(
                    _l(ui, "purge", "Permanently delete"),
                    key=_paper_library_key(ctx, f"purge:{trashed_id}"),
                    icon=":material/delete_forever:",
                    use_container_width=True,
                ):
                    try:
                        assert_files_current([_sources_path])
                        purge_paper_library_node(_pdir, trashed_id, paper_policy="move_to_unsorted")
                        refresh_file_snapshots([_sources_path])
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(ui["saved"])
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

        diagnostics = validate_paper_library(_pdir)
        if diagnostics:
            st.markdown(f"**{_l(ui, 'library_diagnostics', 'Library diagnostics')}**")
            for item in diagnostics:
                st.warning(str(item))


def _render_library_bulk_actions(ctx, selected_rows: list[str], node_options: dict[str, str]) -> None:
    selected = ctx.selected
    _pdir = ctx.pdir
    ui = ctx.ui
    _sources_path = ctx.sources_path
    if not selected_rows:
        return
    current_node = str(st.session_state.get(_paper_library_key(ctx, "node"), "") or "")
    with st.container(border=True):
        st.markdown(
            _l(ui, "bulk_selected_count", "**{count} selected**").format(count=len(selected_rows)),
            unsafe_allow_html=True,
        )
        b1, b2, b3 = st.columns(3)
        with b1:
            bulk_node = st.selectbox(
                _l(ui, "move_to_node", "Move to node"),
                options=list(node_options),
                format_func=lambda ref: node_options.get(ref, ref),
                key=f"bulk_node:{selected}",
            )
            if st.button(
                _l(ui, "move_to_node", "Move to node"),
                disabled=not selected_rows,
                icon=":material/drive_file_move:",
                key=_paper_library_key(ctx, "bulk_move_to_node"),
                use_container_width=True,
            ):
                try:
                    assert_files_current([_sources_path])
                    move_papers_to_node(_pdir, selected_rows, bulk_node)
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if st.button(
                _l(ui, "add_to_node", "Add to node"),
                disabled=not selected_rows or not bulk_node,
                icon=":material/create_new_folder:",
                key=_paper_library_key(ctx, "bulk_add_to_node"),
                use_container_width=True,
            ):
                try:
                    assert_files_current([_sources_path])
                    move_papers_to_node(_pdir, selected_rows, bulk_node, append=True)
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if st.button(
                _l(ui, "remove_from_current_collection", "Remove from current collection"),
                disabled=not selected_rows or not current_node,
                icon=":material/remove_circle:",
                key=_paper_library_key(ctx, "bulk_remove_from_current_node"),
                use_container_width=True,
            ):
                try:
                    assert_files_current([_sources_path])
                    remove_papers_from_node(_pdir, selected_rows, current_node)
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with b2:
            bulk_status = st.selectbox(
                _l(ui, "set_status", "Set status"),
                SOURCE_STATUSES,
                key=f"bulk_status:{selected}",
                format_func=_status_label,
            )
            if st.button(
                _l(ui, "set_status", "Set status"),
                disabled=not selected_rows,
                icon=":material/rule:",
                use_container_width=True,
            ):
                try:
                    assert_files_current([_sources_path])
                    current = load_research_sources(selected)
                    for source_id in selected_rows:
                        update_research_source(current, source_id, status=bulk_status)
                    _save_sources(ctx, current, ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with b3:
            tag_text = st.text_input(_l(ui, "add_tags", "Add tags"), key=f"bulk_tags:{selected}")
            if st.button(
                _l(ui, "add_tags", "Add tags"),
                disabled=not selected_rows,
                icon=":material/sell:",
                use_container_width=True,
            ):
                try:
                    assert_files_current([_sources_path])
                    current = load_research_sources(selected)
                    by_id = current.by_id()
                    for source_id in selected_rows:
                        source = by_id.get(source_id)
                        if source is not None:
                            update_research_source(
                                current,
                                source_id,
                                tags=_unique_text([*source.tags, *_tags(tag_text)]),
                            )
                    _save_sources(ctx, current, ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


def _filter_paper_library_rows(
    rows: list[dict[str, object]],
    *,
    query: str,
    sort_mode: str,
) -> list[dict[str, object]]:
    clean_query = str(query or "").strip().lower()
    if clean_query:
        rows = [
            row
            for row in rows
            if clean_query
            in " ".join(
                [
                    str(row.get("title") or ""),
                    str(row.get("authors") or ""),
                    str(row.get("published") or ""),
                    str(row.get("venue") or ""),
                    str(row.get("tree_path") or ""),
                    str(row.get("summary") or ""),
                    str(row.get("notes") or ""),
                    " ".join(str(tag) for tag in row.get("tags", [])),
                    " ".join(str(badge) for badge in row.get("badges", [])),
                ]
            ).lower()
        ]
    if sort_mode == "title":
        return sorted(rows, key=lambda row: str(row.get("title") or "").lower())
    if sort_mode == "status":
        return sorted(rows, key=lambda row: (str(row.get("status") or ""), str(row.get("title") or "").lower()))
    if sort_mode == "claims":
        return sorted(rows, key=lambda row: int(row.get("claims_count") or 0), reverse=True)
    if sort_mode == "added":
        return sorted(rows, key=lambda row: str(getattr(row.get("source"), "captured_at", "") or ""), reverse=True)
    return sorted(rows, key=lambda row: str(row.get("last_read") or ""), reverse=True)


def _paper_component_rows(ctx, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    ui = ctx.ui
    out: list[dict[str, object]] = []
    sidecar_unavailable, _sidecar_message = _paper_library_sidecar_unavailable(ctx)
    for row in rows:
        source_id = str(row.get("id") or "")
        if not source_id:
            continue
        has_pdf = bool(getattr(row.get("source"), "metadata", {}).get("pdf_asset_ref"))
        out.append(
            {
                "id": source_id,
                "title": str(row.get("title") or source_id),
                "meta": _paper_primary_meta(row),
                "summary": _short_text(row.get("summary") or row.get("notes"), 220),
                "badges": [str(item) for item in row.get("badges", []) if str(item).strip()],
                "tags": [str(item) for item in row.get("tags", []) if str(item).strip()],
                "reader_url": _reader_view_url(ctx, source_id) if has_pdf and not sidecar_unavailable else "",
                "metrics": " · ".join(
                    [
                        f"{_l(ui, 'annotations', 'Annotations')}: {row.get('annotations_count', 0)}",
                        f"{ui['chunk_refs']}: {row.get('chunks_count', 0)}",
                        f"{ui['research_claims']}: {row.get('claims_count', 0)}",
                        f"{ui['research_citations']}: {row.get('citations_count', 0)}",
                    ]
                ),
            }
        )
    return out


def _render_paper_card(ctx, row: dict[str, object], *, active: bool) -> None:
    ui = ctx.ui
    source = row.get("source")
    source_id = str(row.get("id") or "")
    classes = "paper-card paper-card-active" if active else "paper-card"
    title = html.escape(str(row.get("title") or source_id))
    meta = html.escape(_paper_primary_meta(row))
    summary = html.escape(_short_text(row.get("summary") or row.get("notes"), 220))
    badges = _paper_badges_html(row)
    tags = _paper_tag_line(row)
    metrics = html.escape(
        " · ".join(
            [
                f"{_l(ui, 'annotations', 'Annotations')}: {row.get('annotations_count', 0)}",
                f"{ui['chunk_refs']}: {row.get('chunks_count', 0)}",
                f"{ui['research_claims']}: {row.get('claims_count', 0)}",
                f"{ui['research_citations']}: {row.get('citations_count', 0)}",
            ]
        )
    )
    st.markdown(
        f"""
<div class="{classes}">
  <div class="paper-title">{title}</div>
  <div class="paper-meta">{meta}</div>
  <div>{badges}</div>
  {f'<div class="paper-summary">{summary}</div>' if summary else ''}
  {f'<div>{tags}</div>' if tags else ''}
  <div class="paper-meta">{metrics}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    a1, a2 = st.columns(2)
    with a1:
        if st.button(
            _l(ui, "details", "Details"),
            key=_paper_library_key(ctx, f"detail_button:{source_id}"),
            type="primary" if active else "secondary",
            icon=":material/article:",
            use_container_width=True,
        ):
            st.session_state[_paper_library_key(ctx, "detail")] = source_id
            st.rerun()
    with a2:
        if getattr(source, "metadata", {}).get("pdf_asset_ref"):
            _render_sidecar_link_button(ctx, 
                _l(ui, "open_reader", "Open Reader"),
                _reader_view_url(ctx, source_id),
                key=_paper_library_key(ctx, f"reader_link:{source_id}"),
                icon=":material/menu_book:",
                use_container_width=True,
            )
        else:
            st.button(
                _l(ui, "open_reader", "Open Reader"),
                key=_paper_library_key(ctx, f"reader_disabled:{source_id}"),
                disabled=True,
                icon=":material/menu_book:",
                use_container_width=True,
            )


def _render_paper_detail_panel(ctx, 
    inbox,
    source,
    detail_row: dict[str, object],
    node_options: dict[str, str],
) -> None:
    selected = ctx.selected
    _pdir = ctx.pdir
    ui = ctx.ui
    _sources_path = ctx.sources_path
    annotations = load_paper_annotations(_pdir, source.id)
    translations = load_paper_translations(_pdir, source.id)
    pages_count = len(load_paper_pages(_pdir, source.id))
    segments_count = len(load_paper_segments(_pdir, source.id))
    source_chunks = load_chunks(_pdir, source.id)
    title = html.escape(source.title or source.id)
    meta = html.escape(_paper_primary_meta(detail_row))
    st.markdown(
        f"""
<div class="paper-detail-title">{title}</div>
<div class="paper-muted">{meta}</div>
<div>{_paper_badges_html(detail_row, limit=8)}</div>
""",
        unsafe_allow_html=True,
    )
    st.caption(f"`{source.id}`")

    m1, m2 = st.columns(2)
    m1.metric("PDF", "ready" if source.metadata.get("pdf_asset_ref") else "missing")
    m2.metric(_l(ui, "last_read_page", "Last page"), source.metadata.get("last_read_page", "") or "-")
    m3, m4 = st.columns(2)
    m3.metric(_l(ui, "segments", "Segments"), segments_count)
    m4.metric(_l(ui, "annotations", "Annotations"), len([ann for ann in annotations if ann.status == "active"]))
    m5, m6 = st.columns(2)
    m5.metric(ui["research_claims"], detail_row.get("claims_count", 0))
    m6.metric(ui["research_citations"], detail_row.get("citations_count", 0))

    st.markdown(f"**{_l(ui, 'quick_actions', 'Quick actions')}**")
    q1, q2 = st.columns(2)
    with q1:
        if source.metadata.get("pdf_asset_ref"):
            _render_sidecar_link_button(ctx, 
                _l(ui, "open_reader", "Open Reader"),
                _reader_view_url(ctx, source.id),
                key=_paper_library_key(ctx, f"detail_reader_link:{source.id}"),
                icon=":material/menu_book:",
                type="primary",
                use_container_width=True,
            )
        else:
            st.button(
                _l(ui, "open_reader", "Open Reader"),
                disabled=True,
                icon=":material/menu_book:",
                use_container_width=True,
            )
    with q2:
        if st.button(
            _l(ui, "run_extraction", "Run extraction"),
            key=_paper_library_key(ctx, f"extract:{source.id}"),
            disabled=not source.metadata.get("pdf_asset_ref"),
            icon=":material/auto_fix_high:",
            use_container_width=True,
        ):
            try:
                ensure_paper_reading_artifacts(_pdir, source.id)
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["saved"])
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    q3, _ = st.columns(2)
    with q3:
        if st.button(
            _l(ui, "auto_chunk", "Auto chunk"),
            key=_paper_library_key(ctx, f"auto_chunk:{source.id}"),
            icon=":material/content_cut:",
            use_container_width=True,
        ):
            try:
                chunks = auto_chunk_paper(_pdir, source.id)
                stash_git_backup_results()
                clear_web_cache()
                st.success(_l(ui, "created_chunks", "Created chunks: {count}").format(count=len(chunks)))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with st.expander(_l(ui, "organize_paper", "Organize paper"), expanded=False):
        first_ref = source.library_node_refs[0] if source.library_node_refs else ""
        status_index = SOURCE_STATUSES.index(source.status) if source.status in SOURCE_STATUSES else 0
        node_refs = list(node_options)
        node_index = node_refs.index(first_ref) if first_ref in node_refs else 0
        with st.form(_paper_library_key(ctx, f"organize_form:{source.id}")):
            next_status = st.selectbox(
                _l(ui, "set_status", "Set status"),
                SOURCE_STATUSES,
                index=status_index,
                format_func=_status_label,
            )
            next_node = st.selectbox(
                _l(ui, "move_to_node", "Move to node"),
                node_refs,
                index=node_index,
                format_func=lambda ref: node_options.get(ref, ref),
            )
            next_tags = st.text_input(ui["tags"], value=", ".join(source.tags))
            saved = st.form_submit_button(ui["save"], type="primary")
        if saved:
            try:
                assert_files_current([_sources_path])
                current = load_research_sources(selected)
                update_research_source(
                    current,
                    source.id,
                    status=next_status,
                    tags=_tags(next_tags),
                    library_node_refs=[next_node] if next_node else [],
                )
                _save_sources(ctx, current, ui["saved"])
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    detail_tabs = st.tabs(
        [
            _l(ui, "notes", "Notes"),
            _l(ui, "artifacts", "Artifacts"),
            _l(ui, "metadata", "Metadata"),
        ]
    )
    with detail_tabs[0]:
        if source.summary:
            st.markdown(f"**{ui['summary']}**")
            st.write(source.summary)
        if source.notes:
            st.markdown(f"**{ui['notes']}**")
            st.write(source.notes)
        if source.url:
            st.link_button(_l(ui, "open_source", "Open source"), source.url, icon=":material/open_in_new:")
        explanation_links = _paper_explanation_links((source.metadata or {}).get("explanation_links"))
        if explanation_links:
            st.markdown(f"**{_l(ui, 'explainer_links', 'Explainer links')}**")
            rendered_links = [
                _search_result_link_html(
                    str(link.get("title") or link.get("url") or ""),
                    str(link.get("url") or ""),
                    source=str(link.get("source") or ""),
                    summary=str(link.get("summary") or ""),
                )
                for link in explanation_links
                if str(link.get("url") or "").strip()
            ]
            rendered = "\n".join(item for item in rendered_links if item)
            if rendered:
                st.markdown(rendered, unsafe_allow_html=True)
        if not any([source.summary, source.notes, source.url, explanation_links]):
            st.caption(_l(ui, "paper_notes_empty", "No summary, notes, or source URL yet."))
    with detail_tabs[1]:
        st.write(
            {
                "pdf_asset_ref": source.metadata.get("pdf_asset_ref", ""),
                "pages": source.metadata.get("page_count", "") or pages_count,
                "segments": segments_count,
                "chunks": len(source_chunks),
                "translations": len(translations),
                "structure_backend": source.metadata.get("structure_backend", ""),
                "structured_extracted_at": source.metadata.get("structured_extracted_at", ""),
            }
        )
        artifact_actions = st.columns(3)
        with artifact_actions[0]:
            if st.button(
                _l(ui, "extract_pages", "Extract pages"),
                key=_paper_library_key(ctx, f"detail_extract_pages:{source.id}"),
                disabled=not source.metadata.get("pdf_asset_ref"),
                use_container_width=True,
            ):
                try:
                    extract_paper_pages(_pdir, source.id)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with artifact_actions[1]:
            if st.button(
                _l(ui, "extract_segments", "Extract segments"),
                key=_paper_library_key(ctx, f"detail_extract_segments:{source.id}"),
                disabled=not source.metadata.get("pdf_asset_ref"),
                use_container_width=True,
            ):
                try:
                    extract_paper_segments(_pdir, source.id)
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with artifact_actions[2]:
            if st.button(
                _l(ui, "run_structured_extraction", "Run structured extraction"),
                key=_paper_library_key(ctx, f"detail_structured:{source.id}"),
                disabled=not source.metadata.get("pdf_asset_ref"),
                use_container_width=True,
            ):
                try:
                    extract_paper_segments(_pdir, source.id, backend="grobid")
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        warnings = source.metadata.get("structured_extraction_warnings") or source.metadata.get("text_extraction_warnings") or []
        for warning in warnings:
            st.warning(str(warning))
        _render_grobid_status_block(ctx, source)
    with detail_tabs[2]:
        st.code(
            yaml.dump(
                {
                    "metadata": source.metadata,
                    "library_node_refs": source.library_node_refs,
                    "tags": source.tags,
                    "authors": source.authors,
                    "published": source.published,
                    "project_refs": source.project_refs,
                    "goal_refs": source.goal_refs,
                    "reading": source.reading.to_dict(),
                },
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
            language="yaml",
        )


def _render_paper_library(ctx, inbox) -> None:
    selected = ctx.selected
    ui = ctx.ui
    st.subheader(_l(ui, "paper_library", "Paper Library"))
    st.caption(
        _l(ui, 
            "paper_library_caption",
            "Organize papers into collections, continue reading, and move each source through extraction, claims, and review.",
        )
    )
    current_view = str(st.session_state.get(_paper_library_key(ctx, "view"), "all") or "all")
    current_node = str(st.session_state.get(_paper_library_key(ctx, "node"), "") or "")
    query = str(st.session_state.get(_paper_library_key(ctx, "query"), "") or "")
    sort_mode = str(st.session_state.get(_paper_library_key(ctx, "sort"), "recent") or "recent")
    detail_id = str(st.session_state.get(_paper_library_key(ctx, "detail"), "") or "")
    workspace_url = _paper_library_workspace_url(ctx, 
        view=current_view if current_view != "all" else "",
        node_id=current_node,
        query=query,
        sort=sort_mode if sort_mode != "recent" else "",
        detail_id=detail_id,
    )
    runtime, invalid_runtime = resolve_paper_library_runtime()
    workspace_ok: bool | None = None
    workspace_message = ""
    if runtime != "streamlit_component":
        workspace_ok, workspace_message = _paper_library_sidecar_status(ctx)
    if invalid_runtime:
        st.warning(
            _l(ui, 
                "paper_library_runtime_invalid",
                "Unknown Paper Library runtime; using 8502 link mode.",
            )
            + f" `{invalid_runtime}`"
        )

    _render_sidecar_link_button(ctx, 
        _l(ui, "open_paper_library_workspace", "Open Paper Library Workspace"),
        workspace_url,
        key=f"paper_library_open_workspace:{selected}",
        icon=":material/open_in_new:",
        disabled=workspace_ok is False,
    )

    if workspace_ok is False:
        st.warning(
            _l(ui, 
                "paper_library_workspace_unavailable",
                "8502 Paper Library is not reachable right now; using the Streamlit fallback below.",
            )
            + (f" `{workspace_message}`" if workspace_message else "")
        )

    if runtime == "fastapi_iframe" and workspace_ok is not False:
        _render_iframe(ctx, workspace_url, height=1100, scrolling=True)
        return

    if runtime == "streamlit_component":
        _render_paper_library_streamlit_component(ctx, inbox)
        return

    show_fallback = workspace_ok is False or st.toggle(
        _l(ui, "paper_library_fallback", "Show Streamlit Paper Library fallback"),
        value=False,
        key=_paper_library_key(ctx, "show_streamlit_fallback"),
    )
    if show_fallback:
        try:
            with st.container(border=True):
                _render_paper_library_streamlit_component(ctx, inbox, include_import=True)
        except TypeError:
            _render_paper_library_streamlit_component(ctx, inbox, include_import=True)


def _render_paper_library_streamlit_component(ctx, inbox, *, include_import: bool = True) -> None:
    _pdir = ctx.pdir
    ui = ctx.ui
    user = ctx.user
    _render_paper_library_styles()

    all_rows = paper_rows(_pdir, view="all")
    tree = load_paper_library_tree(_pdir)
    node_options = _node_options(ctx)
    current_view = str(st.session_state.setdefault(_paper_library_key(ctx, "view"), "all") or "all")
    current_node = str(st.session_state.setdefault(_paper_library_key(ctx, "node"), "") or "")
    if current_view not in _LIBRARY_VIEW_LABELS:
        current_view = "all"
        st.session_state[_paper_library_key(ctx, "view")] = current_view
    active_node_ids = {node.id for node in tree.nodes if node.status != "trashed"}
    if current_node and current_node not in active_node_ids:
        current_node = ""
        st.session_state[_paper_library_key(ctx, "node")] = ""

    metric_cols = st.columns(5)
    metric_cols[0].metric(_l(ui, "papers_total", "Papers"), len(all_rows))
    metric_cols[1].metric(_l(ui, "reading", "Reading"), _library_view_count(all_rows, "reading"))
    metric_cols[2].metric(_l(ui, "pdf_missing", "PDF missing"), _library_view_count(all_rows, "no_pdf"))
    metric_cols[3].metric(_l(ui, "needs_extraction", "Needs extraction"), _library_view_count(all_rows, "needs_extraction"))
    metric_cols[4].metric(_l(ui, "claims_need_review", "Claims review"), _library_view_count(all_rows, "claims_need_review"))

    if include_import:
        search_results_open = bool(st.session_state.get(_search_state_key(ctx, "results")) or [])
        with st.expander(
            _l(ui, "find_import_papers", "Find and import papers"),
            expanded=search_results_open,
        ):
            _render_paper_search(ctx, inbox, embedded=True)

    selected_paper_ids_for_tree = [
        str(item)
        for item in st.session_state.get(_paper_library_key(ctx, "bulk_select"), []) or []
        if str(item).strip()
    ]
    if paper_library_component_available():
        toolbar = st.columns([2.2, 1])
        with toolbar[0]:
            query = st.text_input(
                _l(ui, "search_library", "Search title, author, tag, note..."),
                key=_paper_library_key(ctx, "query"),
                label_visibility="collapsed",
                placeholder=_l(ui, "search_library", "Search title, author, tag, note..."),
            )
        with toolbar[1]:
            sort_mode = st.selectbox(
                _l(ui, "sort", "Sort"),
                ["recent", "added", "title", "status", "claims"],
                format_func=lambda item: {
                    "recent": _l(ui, "sort_recent", "Recently read"),
                    "added": _l(ui, "sort_added", "Recently added"),
                    "title": ui["title_label"],
                    "status": ui["status"],
                    "claims": ui["research_claims"],
                }.get(item, item),
                key=_paper_library_key(ctx, "sort"),
                label_visibility="collapsed",
            )
        payload = build_paper_library_payload(
            _pdir,
            current_view=current_view,
            current_node=current_node,
            query=str(query or ""),
            sort_mode=str(sort_mode or "recent"),
            selected_paper_ids=selected_paper_ids_for_tree,
            detail_id=str(st.session_state.get(_paper_library_key(ctx, "detail"), "") or ""),
            user_id=user.id,
            reader_base="" if _paper_library_sidecar_unavailable(ctx)[0] else _reader_api_base(),
        )
        if payload.get("detail_id"):
            st.session_state[_paper_library_key(ctx, "detail")] = str(payload.get("detail_id") or "")
        component_event = st_paper_library_tree(
            payload=payload,
            key=_paper_library_key(ctx, "workbench_component"),
            height=860,
        )
        _handle_paper_library_component_event(ctx, component_event)
        _render_library_collection_manager(ctx, tree, node_options)
        with st.expander(_l(ui, "parser_status", "Parser status"), expanded=False):
            _render_grobid_status_block(ctx)
        return

    left, middle, right = st.columns([0.23, 0.47, 0.30], gap="large")
    with left:
        if paper_library_component_available():
            component_event = st_paper_library_tree(
                payload=_paper_library_component_payload(ctx, 
                    tree,
                    all_rows,
                    current_view=current_view,
                    current_node=current_node,
                    selected_paper_ids=selected_paper_ids_for_tree,
                ),
                key=_paper_library_key(ctx, "tree_component"),
                height=760,
            )
            _handle_paper_library_component_event(ctx, component_event)
            _render_library_collection_manager(ctx, tree, node_options)
        else:
            _render_library_view_group(ctx, 
                "library",
                "Library",
                _LIBRARY_VIEW_GROUPS[0][2],
                all_rows,
                current_view,
                current_node,
            )
            st.divider()
            st.markdown(f"**{_l(ui, 'collections', 'Collections')}**")
            if st.button(
                _l(ui, "clear_tree_filter", "All collections"),
                key=_paper_library_key(ctx, "clear_node"),
                type="primary" if not current_node else "secondary",
                use_container_width=True,
            ):
                st.session_state[_paper_library_key(ctx, "view")] = "all"
                st.session_state[_paper_library_key(ctx, "node")] = ""
                st.session_state.pop(_paper_library_key(ctx, "detail"), None)
                st.rerun()
            _paper_tree_buttons(ctx, tree, all_rows)
            _render_library_collection_manager(ctx, tree, node_options)
            st.divider()
            st.markdown(f"**{_l(ui, 'technical_taxonomy', 'Technical Taxonomy')}**")
            for taxonomy_id, fallback in _TECHNICAL_TAXONOMY_LABELS:
                st.button(
                    f"{_l(ui, f'technical_taxonomy_{taxonomy_id}', fallback)} (0)",
                    key=_paper_library_key(ctx, f"taxonomy:{taxonomy_id}"),
                    disabled=True,
                    use_container_width=True,
                )
            st.divider()
            _render_library_view_group(ctx, 
                "work_queue",
                "Work Queue",
                _LIBRARY_VIEW_GROUPS[1][2],
                all_rows,
                current_view,
                current_node,
            )
            st.divider()
            _render_library_view_group(ctx, 
                "system",
                "System",
                _LIBRARY_VIEW_GROUPS[2][2],
                all_rows,
                current_view,
                current_node,
            )
        with st.expander(_l(ui, "parser_status", "Parser status"), expanded=False):
            _render_grobid_status_block(ctx)

    with middle:
        toolbar = st.columns([2.2, 1, 1])
        with toolbar[0]:
            query = st.text_input(
                _l(ui, "search_library", "Search title, author, tag, note..."),
                key=_paper_library_key(ctx, "query"),
                label_visibility="collapsed",
                placeholder=_l(ui, "search_library", "Search title, author, tag, note..."),
            )
        with toolbar[1]:
            sort_mode = st.selectbox(
                _l(ui, "sort", "Sort"),
                ["recent", "added", "title", "status", "claims"],
                format_func=lambda item: {
                    "recent": _l(ui, "sort_recent", "Recently read"),
                    "added": _l(ui, "sort_added", "Recently added"),
                    "title": ui["title_label"],
                    "status": ui["status"],
                    "claims": ui["research_claims"],
                }.get(item, item),
                key=_paper_library_key(ctx, "sort"),
                label_visibility="collapsed",
            )
        with toolbar[2]:
            show_table = st.toggle(
                _l(ui, "table_view", "Table"),
                value=False,
                key=_paper_library_key(ctx, "table_view"),
            )

        rows = paper_rows(_pdir, view=current_view, node_id=current_node)
        clean_query = str(query or "").strip().lower()
        if clean_query:
            rows = [
                row
                for row in rows
                if clean_query
                in " ".join(
                    [
                        str(row.get("title") or ""),
                        str(row.get("authors") or ""),
                        str(row.get("published") or ""),
                        str(row.get("venue") or ""),
                        str(row.get("tree_path") or ""),
                        str(row.get("summary") or ""),
                        str(row.get("notes") or ""),
                        " ".join(str(tag) for tag in row.get("tags", [])),
                        " ".join(str(badge) for badge in row.get("badges", [])),
                    ]
                ).lower()
            ]
        if sort_mode == "title":
            rows = sorted(rows, key=lambda row: str(row.get("title") or "").lower())
        elif sort_mode == "status":
            rows = sorted(rows, key=lambda row: (str(row.get("status") or ""), str(row.get("title") or "").lower()))
        elif sort_mode == "claims":
            rows = sorted(rows, key=lambda row: int(row.get("claims_count") or 0), reverse=True)
        elif sort_mode == "added":
            rows = sorted(rows, key=lambda row: str(getattr(row.get("source"), "captured_at", "") or ""), reverse=True)
        else:
            rows = sorted(rows, key=lambda row: str(row.get("last_read") or ""), reverse=True)

        paper_ids = [str(row.get("id")) for row in rows]
        selected_rows = st.multiselect(
            _l(ui, "select_papers", "Select papers"),
            options=paper_ids,
            format_func=lambda sid: _source_label(inbox, sid),
            key=_paper_library_key(ctx, "bulk_select"),
        )
        _render_library_bulk_actions(ctx, selected_rows, node_options)

        active_label = _LIBRARY_VIEW_LABELS.get(current_view, current_view)
        if current_node:
            active_label = node_options.get(current_node, current_node)
        st.caption(
            _l(ui, "library_result_count", "{count} papers in {view}").format(
                count=len(rows),
                view=active_label,
            )
        )
        if not rows:
            st.info(_l(ui, "library_empty", "No papers match this view."))
        elif show_table:
            display_rows = []
            for row in rows:
                display_row = {
                    key: value
                    for key, value in row.items()
                    if key not in {"source", "diagnostics"}
                }
                display_row["tags"] = ", ".join(str(item) for item in row.get("tags", []))
                display_row["badges"] = ", ".join(str(item) for item in row.get("badges", []) if str(item).strip())
                display_rows.append(display_row)
            st.dataframe(display_rows, use_container_width=True, hide_index=True)
        else:
            detail_id = str(st.session_state.get(_paper_library_key(ctx, "detail"), "") or "")
            if detail_id not in paper_ids and paper_ids:
                detail_id = paper_ids[0]
                st.session_state[_paper_library_key(ctx, "detail")] = detail_id
            for row in rows:
                _render_paper_card(ctx, row, active=str(row.get("id")) == detail_id)

    with right:
        detail_id = str(st.session_state.get(_paper_library_key(ctx, "detail"), "") or "")
        by_id = inbox.by_id()
        if not detail_id and rows:
            detail_id = str(rows[0].get("id") or "")
            st.session_state[_paper_library_key(ctx, "detail")] = detail_id
        source = by_id.get(detail_id)
        if source is None:
            st.info(_l(ui, "select_paper_detail_hint", "Select a paper to see details and actions."))
            return
        detail_row = next(
            (row for row in all_rows if str(row.get("id")) == detail_id),
            next((row for row in rows if str(row.get("id")) == detail_id), {}),
        )
        _render_paper_detail_panel(ctx, inbox, source, detail_row, node_options)


