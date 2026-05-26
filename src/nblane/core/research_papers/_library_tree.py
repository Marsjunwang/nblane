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
from ._constants import LIBRARY_TREE_FILENAME
from ._paths import _profile_name, _profile_root, _research_root, _yaml_path
from ._types import PaperLibraryNode, PaperLibraryTree
from ._utils import _clean_list, _clean_text, _now, _slug, _today

def _library_tree_path(profile: str | Path) -> Path:
    return _research_root(profile) / LIBRARY_TREE_FILENAME


def load_paper_library_tree(profile: str | Path) -> PaperLibraryTree:
    path = _library_tree_path(profile)
    raw = _load_yaml_dict(path) or {}
    tree = PaperLibraryTree.from_dict(raw)
    if not tree.profile:
        tree.profile = _profile_name(profile)
    return tree


def save_paper_library_tree(profile: str | Path, tree: PaperLibraryTree | dict) -> Path:
    path = _library_tree_path(profile)
    doc = tree if isinstance(tree, PaperLibraryTree) else PaperLibraryTree.from_dict(tree)
    doc.profile = doc.profile or _profile_name(profile)
    doc.updated = _today()
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.dump(doc.to_dict(), allow_unicode=True, default_flow_style=False, sort_keys=False)
    atomic_write_text(path, f"# Paper library tree for {doc.profile}\n\n" + body)
    git_backup.record_change([path], action=f"update {doc.profile}/research/library-tree.yaml")
    return path


def _paper_library_root_parent(parent_id: object) -> str:
    clean = _clean_text(parent_id)
    return "" if clean in {"", "root", "paper-root", "paper-library-root"} else clean


def _paper_library_require_node(
    tree: PaperLibraryTree,
    node_id: str,
    *,
    include_trashed: bool = False,
) -> PaperLibraryNode:
    clean = _clean_text(node_id)
    if not clean or clean in {"root", "paper-root", "paper-library-root"}:
        raise ValueError("The Paper Library root cannot be changed.")
    for node in tree.nodes:
        if node.id != clean:
            continue
        if node.status == "trashed" and not include_trashed:
            raise ValueError(f"Paper library node is in trash: {clean}")
        return node
    raise ValueError(f"Unknown paper library node: {clean}")


def _paper_library_parent_id(tree: PaperLibraryTree, parent_id: object) -> str:
    clean = _paper_library_root_parent(parent_id)
    if not clean:
        return ""
    node = _paper_library_require_node(tree, clean)
    if node.status == "trashed":
        raise ValueError(f"Paper library parent is in trash: {clean}")
    return clean


def _paper_library_children_by_parent(
    tree: PaperLibraryTree,
    *,
    include_trashed: bool = False,
) -> dict[str, list[PaperLibraryNode]]:
    children: dict[str, list[PaperLibraryNode]] = {}
    for node in tree.nodes:
        if node.status == "trashed" and not include_trashed:
            continue
        children.setdefault(node.parent_id or "", []).append(node)
    for siblings in children.values():
        siblings.sort(key=lambda item: (item.order, item.title.lower(), item.id))
    return children


def _paper_library_next_order(tree: PaperLibraryTree, parent_id: str) -> int:
    siblings = _paper_library_children_by_parent(tree).get(parent_id or "", [])
    return (max((node.order for node in siblings), default=0) // 10 + 1) * 10


def _paper_library_unique_node_id(tree: PaperLibraryTree, title: str) -> str:
    base = f"paper-node:{_slug(title, fallback='collection')}"
    existing = {node.id for node in tree.nodes}
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def _paper_library_descendant_ids(
    tree: PaperLibraryTree,
    node_id: str,
    *,
    include_trashed: bool = True,
) -> list[str]:
    children = _paper_library_children_by_parent(tree, include_trashed=include_trashed)
    out: list[str] = []

    def walk(parent: str, seen: set[str]) -> None:
        for child in children.get(parent, []):
            if child.id in seen:
                continue
            out.append(child.id)
            walk(child.id, seen | {child.id})

    walk(_clean_text(node_id), {_clean_text(node_id)})
    return out


def _paper_library_assert_not_descendant_parent(
    tree: PaperLibraryTree,
    *,
    node: PaperLibraryNode,
    parent_id: str,
) -> None:
    parent = _paper_library_root_parent(parent_id)
    if not parent:
        return
    if parent == node.id:
        raise ValueError("A paper library node cannot be moved under itself.")
    nodes = tree.by_id()
    cursor = nodes.get(parent)
    seen: set[str] = set()
    while cursor is not None and cursor.id not in seen:
        if cursor.id == node.id:
            raise ValueError("A paper library node cannot be moved under its descendant.")
        seen.add(cursor.id)
        cursor = nodes.get(cursor.parent_id)


def _normalize_paper_library_sibling_orders(
    tree: PaperLibraryTree,
    parent_ids: set[str] | None = None,
) -> None:
    children = _paper_library_children_by_parent(tree)
    wanted = set(children) if parent_ids is None else {parent_id or "" for parent_id in parent_ids}
    for parent_id in wanted:
        siblings = children.get(parent_id, [])
        for index, node in enumerate(siblings, start=1):
            node.order = index * 10


def _paper_library_policy_target(
    tree: PaperLibraryTree,
    paper_policy: str,
    *,
    fallback_parent_id: str,
    deleted_ids: set[str],
) -> str:
    policy = _clean_text(paper_policy) or "move_to_parent"
    if policy in {"cancel", "cancel_delete"}:
        raise ValueError("Paper library delete was cancelled.")
    if policy == "move_to_parent":
        target = fallback_parent_id or ""
    elif policy == "move_to_unsorted":
        target = ""
    elif policy.startswith("move_to:"):
        target = _clean_text(policy.split(":", 1)[1])
    elif policy.startswith("move_to_node:"):
        target = _clean_text(policy.split(":", 1)[1])
    else:
        raise ValueError(f"Unknown paper library delete policy: {paper_policy}")
    if target:
        if target in deleted_ids:
            raise ValueError("Papers cannot be moved into a collection that is being deleted.")
        _paper_library_require_node(tree, target)
    return target


def _apply_paper_library_delete_policy(
    profile: str | Path,
    tree: PaperLibraryTree,
    node_ids: list[str],
    *,
    paper_policy: str,
    fallback_parent_id: str,
) -> list[str]:
    deleted = set(_clean_list(node_ids))
    if not deleted:
        return []
    target = _paper_library_policy_target(
        tree,
        paper_policy,
        fallback_parent_id=fallback_parent_id,
        deleted_ids=deleted,
    )
    inbox = load_research_sources(_profile_root(profile))
    changed: list[str] = []
    for source in inbox.sources:
        refs = list(source.library_node_refs)
        if not any(ref in deleted for ref in refs):
            continue
        next_refs: list[str] = []
        inserted_target = False
        for ref in refs:
            if ref in deleted:
                if target and not inserted_target and target not in next_refs:
                    next_refs.append(target)
                    inserted_target = True
                continue
            if ref not in next_refs:
                next_refs.append(ref)
        if next_refs != refs:
            source.library_node_refs = next_refs
            changed.append(source.id)
    if changed:
        save_research_sources(_profile_root(profile), inbox)
    return changed


def create_paper_library_node(
    profile: str | Path,
    title: str,
    parent_id: str = "",
    description: str = "",
    color: str = "",
    icon: str = "",
) -> PaperLibraryNode:
    clean_title = _clean_text(title)
    if not clean_title:
        raise ValueError("Paper library node title cannot be blank.")
    tree = load_paper_library_tree(profile)
    parent = _paper_library_parent_id(tree, parent_id)
    node = PaperLibraryNode(
        id=_paper_library_unique_node_id(tree, clean_title),
        title=clean_title,
        parent_id=parent,
        description=_clean_text(description),
        color=_clean_text(color),
        icon=_clean_text(icon),
        order=_paper_library_next_order(tree, parent),
        created_by="user",
    )
    tree.nodes.append(node)
    save_paper_library_tree(profile, tree)
    return node


def rename_paper_library_node(
    profile: str | Path,
    node_id: str,
    title: str,
) -> PaperLibraryNode:
    clean_title = _clean_text(title)
    if not clean_title:
        raise ValueError("Paper library node title cannot be blank.")
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id)
    node.title = clean_title
    save_paper_library_tree(profile, tree)
    return node


def position_paper_library_node(
    profile: str | Path,
    node_id: str,
    parent_id: str = "",
    before_node_id: str = "",
    after_node_id: str = "",
) -> PaperLibraryNode:
    before_id = _clean_text(before_node_id)
    after_id = _clean_text(after_node_id)
    if before_id and after_id:
        raise ValueError("Use either before_node_id or after_node_id, not both.")
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id)

    target: PaperLibraryNode | None = None
    insert_after = False
    if before_id or after_id:
        target_id = before_id or after_id
        if target_id == node.id:
            raise ValueError("A paper library node cannot be positioned relative to itself.")
        target = _paper_library_require_node(tree, target_id)
        parent = target.parent_id or ""
        insert_after = bool(after_id)
    else:
        parent = _paper_library_parent_id(tree, parent_id)

    _paper_library_assert_not_descendant_parent(tree, node=node, parent_id=parent)

    before_state = {item.id: (item.parent_id, item.order) for item in tree.nodes}
    children = _paper_library_children_by_parent(tree)
    old_parent = node.parent_id or ""
    siblings = [
        item
        for item in children.get(parent, [])
        if item.id != node.id
    ]
    if target is not None:
        target_pos = next((index for index, item in enumerate(siblings) if item.id == target.id), -1)
        if target_pos < 0:
            raise ValueError(f"Unknown paper library position target: {target.id}")
        insert_pos = target_pos + 1 if insert_after else target_pos
    else:
        insert_pos = len(siblings)
    next_siblings = list(siblings)
    next_siblings.insert(insert_pos, node)
    node.parent_id = parent
    for index, item in enumerate(next_siblings, start=1):
        item.order = index * 10
    if old_parent != parent:
        _normalize_paper_library_sibling_orders(tree, {old_parent})

    after_state = {item.id: (item.parent_id, item.order) for item in tree.nodes}
    if before_state != after_state:
        save_paper_library_tree(profile, tree)
    return node


def reorder_paper_library_node(
    profile: str | Path,
    node_id: str,
    direction: str,
) -> PaperLibraryNode:
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id)
    siblings = _paper_library_children_by_parent(tree).get(node.parent_id or "", [])
    pos = next((index for index, item in enumerate(siblings) if item.id == node.id), -1)
    if pos < 0:
        raise ValueError(f"Unknown paper library node: {node_id}")
    clean_direction = _clean_text(direction).lower()
    if clean_direction in {"up", "before"}:
        target_pos = pos - 1
    elif clean_direction in {"down", "after"}:
        target_pos = pos + 1
    else:
        raise ValueError("Paper library reorder direction must be up or down.")
    if target_pos < 0 or target_pos >= len(siblings):
        return node
    siblings[pos], siblings[target_pos] = siblings[target_pos], siblings[pos]
    for index, item in enumerate(siblings, start=1):
        item.order = index * 10
    save_paper_library_tree(profile, tree)
    return node


def trash_paper_library_node(
    profile: str | Path,
    node_id: str,
    paper_policy: str = "move_to_parent",
) -> PaperLibraryNode:
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id)
    ids = [node.id, *_paper_library_descendant_ids(tree, node.id)]
    _apply_paper_library_delete_policy(
        profile,
        tree,
        ids,
        paper_policy=paper_policy,
        fallback_parent_id=node.parent_id,
    )
    now = _now()
    id_set = set(ids)
    for item in tree.nodes:
        if item.id not in id_set or item.status == "trashed":
            continue
        item.trashed_from_parent_id = item.parent_id
        item.trashed_from_order = item.order
        item.trashed_at = now
        item.status = "trashed"
    _normalize_paper_library_sibling_orders(tree, {node.parent_id or ""})
    save_paper_library_tree(profile, tree)
    return node


def restore_paper_library_node(
    profile: str | Path,
    node_id: str,
) -> PaperLibraryNode:
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id, include_trashed=True)
    ids = [node.id, *_paper_library_descendant_ids(tree, node.id)]
    id_set = set(ids)
    active_ids = {item.id for item in tree.nodes if item.status != "trashed"}
    touched_parents: set[str] = set()
    for item in tree.nodes:
        if item.id not in id_set:
            continue
        parent = item.trashed_from_parent_id or item.parent_id or ""
        if parent and parent not in active_ids and parent not in id_set:
            parent = ""
        item.parent_id = parent
        if item.trashed_from_order is not None:
            item.order = item.trashed_from_order
        item.status = "active"
        item.trashed_at = ""
        item.trashed_from_parent_id = ""
        item.trashed_from_order = None
        touched_parents.add(parent)
    _normalize_paper_library_sibling_orders(tree, touched_parents or None)
    save_paper_library_tree(profile, tree)
    return node


def purge_paper_library_node(
    profile: str | Path,
    node_id: str,
    paper_policy: str = "move_to_unsorted",
) -> PaperLibraryNode:
    tree = load_paper_library_tree(profile)
    node = _paper_library_require_node(tree, node_id, include_trashed=True)
    ids = [node.id, *_paper_library_descendant_ids(tree, node.id)]
    _apply_paper_library_delete_policy(
        profile,
        tree,
        ids,
        paper_policy=paper_policy,
        fallback_parent_id=node.parent_id,
    )
    id_set = set(ids)
    tree.nodes = [item for item in tree.nodes if item.id not in id_set]
    _normalize_paper_library_sibling_orders(tree)
    save_paper_library_tree(profile, tree)
    return node


def upsert_paper_library_node(
    profile: str | Path,
    title: str,
    *,
    node_id: str = "",
    parent_id: str = "",
    description: str = "",
    color: str = "",
    icon: str = "",
    order: int = 0,
    created_by: str = "user",
    project_refs: object = None,
    goal_refs: object = None,
) -> PaperLibraryNode:
    clean_title = _clean_text(title)
    if not clean_title:
        raise ValueError("Paper library node title cannot be blank.")
    tree = load_paper_library_tree(profile)
    clean_id = _clean_text(node_id) or f"paper-node:{_slug(clean_title, fallback='topic')}"
    clean_parent = _paper_library_root_parent(parent_id)
    if clean_parent == clean_id:
        raise ValueError("Paper library node cannot be its own parent.")
    nodes = tree.by_id()
    if clean_parent and clean_parent not in nodes:
        raise ValueError(f"Unknown parent paper library node: {clean_parent}")
    node = PaperLibraryNode(
        id=clean_id,
        title=clean_title,
        parent_id=clean_parent,
        description=_clean_text(description),
        color=_clean_text(color),
        icon=_clean_text(icon),
        order=int(order or 0),
        created_by=_clean_text(created_by) or "user",
        project_refs=_clean_list(project_refs),
        goal_refs=_clean_list(goal_refs),
    )
    replaced = False
    for index, existing in enumerate(tree.nodes):
        if existing.id == clean_id:
            tree.nodes[index] = node
            replaced = True
            break
    if not replaced:
        tree.nodes.append(node)
    save_paper_library_tree(profile, tree)
    return node


def paper_library_path(tree: PaperLibraryTree, node_id: str) -> str:
    nodes = tree.by_id()
    path: list[str] = []
    seen: set[str] = set()
    cur = nodes.get(_clean_text(node_id))
    while cur is not None and cur.id not in seen:
        seen.add(cur.id)
        path.append(cur.title)
        cur = nodes.get(cur.parent_id)
    return " / ".join(reversed(path))


def paper_library_paths(profile: str | Path) -> dict[str, str]:
    tree = load_paper_library_tree(profile)
    return {node.id: paper_library_path(tree, node.id) for node in tree.nodes}


def move_papers_to_node(
    profile: str | Path,
    source_ids: list[str],
    node_id: str,
    *,
    append: bool = False,
) -> list[str]:
    tree = load_paper_library_tree(profile)
    clean_node = _clean_text(node_id)
    if clean_node:
        _paper_library_require_node(tree, clean_node)
    inbox = load_research_sources(_profile_root(profile))
    changed: list[str] = []
    wanted = set(_clean_list(source_ids))
    for source in inbox.sources:
        if source.id not in wanted:
            continue
        existing_refs = list(source.library_node_refs)
        if append:
            refs = list(existing_refs)
            if clean_node and clean_node not in refs:
                refs.append(clean_node)
        elif clean_node:
            refs = [
                clean_node,
                *[
                    ref
                    for ref in existing_refs[1:]
                    if ref and ref != clean_node
                ],
            ]
        else:
            refs = []
        if refs == existing_refs:
            continue
        source.library_node_refs = refs
        changed.append(source.id)
    if changed:
        save_research_sources(_profile_root(profile), inbox)
    return changed


def remove_papers_from_node(
    profile: str | Path,
    source_ids: list[str],
    node_id: str,
) -> list[str]:
    tree = load_paper_library_tree(profile)
    clean_node = _clean_text(node_id)
    _paper_library_require_node(tree, clean_node, include_trashed=True)
    inbox = load_research_sources(_profile_root(profile))
    wanted = set(_clean_list(source_ids))
    changed: list[str] = []
    for source in inbox.sources:
        if source.id not in wanted:
            continue
        refs = [ref for ref in source.library_node_refs if ref != clean_node]
        if refs == source.library_node_refs:
            continue
        source.library_node_refs = refs
        changed.append(source.id)
    if changed:
        save_research_sources(_profile_root(profile), inbox)
    return changed


def set_paper_primary_node(
    profile: str | Path,
    source_id: str,
    node_id: str,
) -> ResearchSource:
    clean_source = _clean_text(source_id)
    changed = move_papers_to_node(profile, [clean_source], node_id, append=False)
    inbox = load_research_sources(_profile_root(profile))
    source = inbox.by_id().get(clean_source)
    if source is None:
        raise ValueError(f"Unknown research source: {clean_source}")
    if not changed and _clean_text(node_id):
        tree = load_paper_library_tree(profile)
        _paper_library_require_node(tree, _clean_text(node_id))
    return source


def validate_paper_library(profile: str | Path) -> list[str]:
    diagnostics: list[str] = []
    tree = load_paper_library_tree(profile)
    nodes = tree.by_id()
    for node in tree.nodes:
        if node.id in {"root", "paper-root", "paper-library-root"}:
            diagnostics.append(f"{node.id}: root must stay virtual")
        if node.parent_id and node.parent_id not in nodes:
            diagnostics.append(f"{node.id}: unknown parent node {node.parent_id}")
        if node.parent_id == node.id:
            diagnostics.append(f"{node.id}: node cannot be its own parent")
    for source in load_research_sources(_profile_root(profile)).sources:
        if source.kind != "paper":
            continue
        for ref in source.library_node_refs:
            if ref not in nodes:
                diagnostics.append(f"{source.id}: unknown library node ref {ref}")
            elif nodes[ref].status == "trashed":
                diagnostics.append(f"{source.id}: trashed library node ref {ref}")
    return diagnostics
