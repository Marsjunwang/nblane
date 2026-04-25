"""In-memory merge logic for profile ingest patches."""

from __future__ import annotations

import copy
from datetime import date

from nblane.core.evidence_pool_id import (
    fingerprint_match_id,
    new_evidence_id,
)
from nblane.core.ingest_models import IngestPatch, MergeOutcome
from nblane.core.ingest_parse import (
    _llm_status_effective,
    _normalize_evidence_row,
    _ordinal_placeholder_to_id,
    _status_rank,
    parse_ingest_patch,
)
from nblane.core.models import Evidence
from nblane.core.schema_io import load_schema_raw, schema_node_index


def merge_ingest_patch(
    profile_name: str,
    pool_raw: dict | None,
    tree_raw: dict | None,
    patch: IngestPatch | dict,
    *,
    allow_status_change: bool = False,
    bump_locked_with_evidence: bool = True,
) -> MergeOutcome:
    """Merge patch into pool then tree (memory only)."""
    if isinstance(patch, dict):
        patch = parse_ingest_patch(patch)

    warnings: list[str] = []
    errors: list[str] = []

    if tree_raw is None or not isinstance(tree_raw, dict):
        errors.append("skill-tree.yaml is missing or empty.")
        return MergeOutcome(
            ok=False,
            merged_pool=None,
            merged_tree=None,
            warnings=warnings,
            errors=errors,
        )

    schema_name = tree_raw.get("schema")
    if not schema_name:
        errors.append("skill-tree.yaml has no 'schema' field.")
        return MergeOutcome(
            ok=False,
            merged_pool=None,
            merged_tree=None,
            warnings=warnings,
            errors=errors,
        )

    schema_data = load_schema_raw(str(schema_name))
    if schema_data is None:
        errors.append(
            f"schema file not found: schemas/{schema_name}.yaml"
        )
        return MergeOutcome(
            ok=False,
            merged_pool=None,
            merged_tree=None,
            warnings=warnings,
            errors=errors,
        )

    schema_index = schema_node_index(schema_data)
    allowed_node_ids = frozenset(schema_index.keys())

    pool: dict = copy.deepcopy(pool_raw) if pool_raw else {}
    if "profile" not in pool:
        pool["profile"] = profile_name
    raw_entries = pool.get("evidence_entries")
    if not isinstance(raw_entries, list):
        raw_entries = []
    entries: list[dict] = [
        copy.deepcopy(e) for e in raw_entries if isinstance(e, dict)
    ]

    existing_ids: set[str] = {
        str(e.get("id", "") or "").strip()
        for e in entries
        if str(e.get("id", "") or "").strip()
    }

    ordinal_to_id: dict[int, str] = {}

    for ord_idx, raw in enumerate(patch.evidence_entries):
        norm = _normalize_evidence_row(raw)
        if norm is None:
            warnings.append("skipped evidence_entries row with empty title")
            continue

        fp = fingerprint_match_id(
            entries,
            norm["type"],
            norm["title"],
            norm.get("date", "") or "",
        )
        if fp is not None:
            ordinal_to_id[ord_idx + 1] = fp
            continue

        want_id = norm.pop("id", "") or ""
        if want_id and want_id not in existing_ids:
            norm["id"] = want_id
        elif want_id and want_id in existing_ids:
            warnings.append(
                f"evidence id {want_id!r} collides; "
                f"generated new id"
            )
            norm["id"] = new_evidence_id(
                norm["title"], existing_ids
            )
        else:
            norm["id"] = new_evidence_id(
                norm["title"], existing_ids
            )

        eid = norm["id"]
        existing_ids.add(eid)
        entries.append(norm)
        ordinal_to_id[ord_idx + 1] = eid

    pool["evidence_entries"] = entries
    pool_ids = existing_ids

    tree: dict = copy.deepcopy(tree_raw)
    nodes: list[dict] = [
        copy.deepcopy(n)
        for n in (tree.get("nodes") or [])
        if isinstance(n, dict)
    ]
    by_id: dict[str, int] = {}
    for i, n in enumerate(nodes):
        nid = n.get("id")
        if isinstance(nid, str) and nid.strip():
            by_id[nid.strip()] = i

    for upd in patch.node_updates:
        nid = str(upd.get("id", "") or "").strip()
        if not nid:
            warnings.append("skipped node_updates entry without id")
            continue
        if nid not in allowed_node_ids:
            warnings.append(
                f"skipped unknown node id (not in schema): {nid!r}"
            )
            continue

        if nid not in by_id:
            nodes.append(
                {
                    "id": nid,
                    "status": "locked",
                }
            )
            by_id[nid] = len(nodes) - 1

        idx = by_id[nid]
        node = nodes[idx]

        raw_refs = upd.get("evidence_refs")
        if isinstance(raw_refs, list):
            cur = node.get("evidence_refs")
            if not isinstance(cur, list):
                cur = []
            seen = {str(x).strip() for x in cur if isinstance(x, str)}
            for r in raw_refs:
                if not isinstance(r, str):
                    continue
                key = r.strip()
                if not key:
                    continue
                resolved = key
                if key not in pool_ids:
                    mapped = _ordinal_placeholder_to_id(
                        key,
                        ordinal_to_id,
                    )
                    if mapped is not None and mapped in pool_ids:
                        resolved = mapped
                    else:
                        warnings.append(
                            f"{nid}: dropped evidence_refs id "
                            f"{key!r} (not in pool)"
                        )
                        continue
                if resolved not in seen:
                    cur.append(resolved)
                    seen.add(resolved)
            if cur:
                node["evidence_refs"] = cur

        raw_ev = upd.get("evidence")
        if isinstance(raw_ev, list):
            ev_list = node.get("evidence")
            if not isinstance(ev_list, list):
                ev_list = []
            for item in raw_ev:
                if not isinstance(item, dict):
                    continue
                ev_obj = Evidence.from_dict(item)
                if not str(ev_obj.title).strip():
                    warnings.append(
                        f"{nid}: skipped inline evidence with "
                        f"empty title"
                    )
                    continue
                ev_list.append(ev_obj.to_dict())
            if ev_list:
                node["evidence"] = ev_list

        note_add = str(upd.get("note", "") or "").strip()
        if note_add:
            prev = str(node.get("note", "") or "").strip()
            if prev:
                node["note"] = f"{prev}\n\n{note_add}"
            else:
                node["note"] = note_add

        if allow_status_change and "status" in upd:
            st_raw = str(upd.get("status", "") or "").strip()
            prev_st = str(node.get("status", "locked") or "locked")
            if prev_st == "expert":
                if st_raw and st_raw != "expert":
                    warnings.append(
                        f"{nid}: preserved expert status "
                        f"(ignored LLM status {st_raw!r})"
                    )
            else:
                eff = _llm_status_effective(st_raw)
                if eff is None:
                    if st_raw:
                        warnings.append(
                            f"{nid}: ignored invalid status {st_raw!r}"
                        )
                elif _status_rank(eff) < _status_rank(prev_st):
                    warnings.append(
                        f"{nid}: preserved {prev_st} status "
                        f"(ignored LLM status {st_raw!r}; "
                        f"ingest only upgrades)"
                    )
                else:
                    if st_raw == "expert":
                        warnings.append(
                            f"{nid}: LLM expert treated as learning tier "
                            f"(expert requires human confirmation)"
                        )
                    node["status"] = eff

        nodes[idx] = node

    tree["nodes"] = nodes

    if bump_locked_with_evidence:
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                continue
            cur = str(node.get("status", "locked") or "locked")
            if cur != "locked":
                continue
            raw_refs = node.get("evidence_refs") or []
            ev_inline = node.get("evidence") or []
            has_refs = (
                isinstance(raw_refs, list)
                and any(
                    isinstance(r, str) and r.strip()
                    for r in raw_refs
                )
            )
            has_inline = (
                isinstance(ev_inline, list) and len(ev_inline) > 0
            )
            if has_refs or has_inline:
                node["status"] = "learning"
                nodes[i] = node
        tree["nodes"] = nodes

    today = date.today().isoformat()
    pool["updated"] = today
    tree["updated"] = today

    return MergeOutcome(
        ok=True,
        merged_pool=pool,
        merged_tree=tree,
        warnings=warnings,
        errors=errors,
    )
