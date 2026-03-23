"""Evidence pool ids vs skill-tree evidence_refs (scan, prune)."""

from __future__ import annotations

import copy
from typing import Any


def pool_id_referenced_by_nodes(
    tree: dict[str, Any],
    pool_id: str,
) -> list[str]:
    """Return node ids that list *pool_id* in ``evidence_refs``.

    Order follows first occurrence in ``tree["nodes"]``; each id once.
    """
    key = pool_id.strip()
    if not key:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for n in tree.get("nodes") or []:
        if not isinstance(n, dict):
            continue
        nid = n.get("id")
        if not isinstance(nid, str) or not nid.strip():
            continue
        refs = n.get("evidence_refs") or []
        if not isinstance(refs, list):
            continue
        for r in refs:
            if isinstance(r, str) and r.strip() == key:
                sid = nid.strip()
                if sid not in seen:
                    seen.add(sid)
                    out.append(sid)
                break
    return out


def prune_pool_id_from_tree(
    tree: dict[str, Any],
    pool_id: str,
) -> dict[str, Any]:
    """Deep-copy *tree*; remove *pool_id* from every ``evidence_refs`` list."""
    key = pool_id.strip()
    new_tree: dict[str, Any] = copy.deepcopy(tree)
    nodes = new_tree.get("nodes")
    if not isinstance(nodes, list):
        return new_tree
    for n in nodes:
        if not isinstance(n, dict):
            continue
        refs = n.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            continue
        filtered: list[str] = []
        seen: set[str] = set()
        for r in refs:
            if not isinstance(r, str):
                continue
            s = r.strip()
            if not s or s == key:
                continue
            if s not in seen:
                seen.add(s)
                filtered.append(s)
        if filtered:
            n["evidence_refs"] = filtered
        else:
            n.pop("evidence_refs", None)
    return new_tree


def prune_pool_id_in_rows(
    rows: list[dict[str, Any]],
    pool_id: str,
) -> None:
    """Remove *pool_id* from each row's ``evidence_refs`` (mutates *rows*)."""
    key = pool_id.strip()
    if not key:
        return
    for r in rows:
        refs = r.get("evidence_refs") or []
        if not isinstance(refs, list) or not refs:
            continue
        filtered: list[str] = []
        seen: set[str] = set()
        for x in refs:
            if not isinstance(x, str):
                continue
            s = x.strip()
            if not s or s == key:
                continue
            if s not in seen:
                seen.add(s)
                filtered.append(s)
        if filtered:
            r["evidence_refs"] = filtered
        else:
            r.pop("evidence_refs", None)
