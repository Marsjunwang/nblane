"""Preview helpers for profile ingest merges."""

from __future__ import annotations

from nblane.core.schema_io import load_schema_raw, schema_node_index


def _evidence_refs_set(node: dict) -> frozenset[str]:
    """Return normalized evidence ref ids for a tree node dict."""
    raw = node.get("evidence_refs")
    if not isinstance(raw, list):
        return frozenset()
    out: set[str] = set()
    for x in raw:
        if isinstance(x, str) and x.strip():
            out.add(x.strip())
    return frozenset(out)


def _inline_evidence_count(node: dict) -> int:
    """Count inline evidence dicts attached to a tree node."""
    raw = node.get("evidence")
    if not isinstance(raw, list):
        return 0
    return len([x for x in raw if isinstance(x, dict)])


def ingest_preview_delta(
    pool_before: dict | None,
    tree_before: dict | None,
    merged_pool: dict | None,
    merged_tree: dict | None,
    labels: dict[str, str] | None = None,
) -> tuple[list[str], list[str]]:
    """Compare merged snapshot to on-disk pool/tree for preview UI."""
    if merged_pool is None or merged_tree is None:
        return [], []

    before_entries = (pool_before or {}).get("evidence_entries")
    if not isinstance(before_entries, list):
        before_entries = []
    before_ids: set[str] = set()
    for e in before_entries:
        if isinstance(e, dict):
            eid = str(e.get("id", "") or "").strip()
            if eid:
                before_ids.add(eid)

    new_ev: list[str] = []
    merged_entries = merged_pool.get("evidence_entries")
    if isinstance(merged_entries, list):
        for e in merged_entries:
            if not isinstance(e, dict):
                continue
            eid = str(e.get("id", "") or "").strip()
            if not eid or eid in before_ids:
                continue
            title = str(e.get("title", "") or "").strip()
            typ = str(e.get("type", "") or "").strip()
            new_ev.append(f"{eid} — {title} ({typ})")

    before_nodes_raw = (tree_before or {}).get("nodes")
    if not isinstance(before_nodes_raw, list):
        before_nodes_raw = []
    before_map: dict[str, dict] = {}
    for n in before_nodes_raw:
        if isinstance(n, dict):
            nid = str(n.get("id", "") or "").strip()
            if nid:
                before_map[nid] = n

    tree_changes: list[str] = []
    merged_nodes = merged_tree.get("nodes")
    if not isinstance(merged_nodes, list):
        merged_nodes = []

    for n in merged_nodes:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id", "") or "").strip()
        if not nid:
            continue
        label = (labels or {}).get(nid, nid)
        bn = before_map.get(nid)
        if bn is None:
            st = str(n.get("status", "locked") or "locked")
            tree_changes.append(
                f"{nid} ({label}): new node row, status={st}"
            )
            continue
        bs = str(bn.get("status", "locked") or "locked")
        as_ = str(n.get("status", "locked") or "locked")
        brefs = _evidence_refs_set(bn)
        arefs = _evidence_refs_set(n)
        bic = _inline_evidence_count(bn)
        aic = _inline_evidence_count(n)
        parts: list[str] = []
        if bs != as_:
            parts.append(f"status {bs}->{as_}")
        added = sorted(arefs - brefs)
        removed = sorted(brefs - arefs)
        if added:
            parts.append(f"refs +{', '.join(added)}")
        if removed:
            parts.append(f"refs -{', '.join(removed)}")
        if bic != aic:
            parts.append(f"inline evidence {bic}->{aic}")
        if parts:
            tree_changes.append(
                f"{nid} ({label}): " + "; ".join(parts)
            )

    return new_ev, tree_changes


def schema_node_labels(tree_raw: dict | None) -> dict[str, str]:
    """Map skill node id -> display label using the tree's schema file."""
    if tree_raw is None:
        return {}
    sn = tree_raw.get("schema")
    if not sn:
        return {}
    data = load_schema_raw(str(sn))
    if data is None:
        return {}
    idx = schema_node_index(data)
    return {
        nid: str(meta.get("label") or nid)
        for nid, meta in idx.items()
    }


def pool_tree_summaries_for_prompt(
    pool_raw: dict | None,
    tree_raw: dict | None,
    *,
    max_pool: int = 40,
    max_nodes: int = 80,
) -> tuple[str, str]:
    """Compact strings for LLM user messages (pool + tree refs)."""
    lines_p: list[str] = []
    if pool_raw and isinstance(pool_raw, dict):
        evs = pool_raw.get("evidence_entries") or []
        if isinstance(evs, list):
            for i, e in enumerate(evs):
                if i >= max_pool:
                    lines_p.append("... (pool truncated)")
                    break
                if not isinstance(e, dict):
                    continue
                eid = str(e.get("id", "") or "")
                title = str(e.get("title", "") or "")
                if eid:
                    lines_p.append(f"- {eid}: {title}")
    pool_text = (
        "\n".join(lines_p) if lines_p else "(empty evidence pool)"
    )

    lines_t: list[str] = []
    if tree_raw and isinstance(tree_raw, dict):
        for i, n in enumerate(tree_raw.get("nodes") or []):
            if i >= max_nodes:
                lines_t.append("... (tree truncated)")
                break
            if not isinstance(n, dict):
                continue
            nid = str(n.get("id", "") or "")
            st = str(n.get("status", "") or "")
            refs = n.get("evidence_refs") or []
            ref_n = (
                len(refs)
                if isinstance(refs, list)
                else 0
            )
            if nid:
                lines_t.append(
                    f"- {nid}: status={st}, evidence_refs={ref_n}"
                )
    tree_text = (
        "\n".join(lines_t)
        if lines_t
        else "(no skill-tree nodes yet)"
    )
    return pool_text, tree_text
