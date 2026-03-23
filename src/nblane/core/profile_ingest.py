"""Merge LLM / manual ingest patches into pool + skill-tree; validate + sync."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from nblane.core.evidence_pool_id import (
    fingerprint_match_id,
    new_evidence_id,
)
from nblane.core.io import (
    load_evidence_pool_raw,
    load_schema_raw,
    load_skill_tree_raw,
    profile_dir,
    save_evidence_pool,
    save_skill_tree,
    schema_node_index,
)
from nblane.core.models import EVIDENCE_TYPES, Evidence
from nblane.core.validate import ALLOWED_STATUS, validate_one


@dataclass
class IngestPatch:
    """Normalized ingest payload (evidence rows + per-node updates)."""

    evidence_entries: list[dict] = field(default_factory=list)
    node_updates: list[dict] = field(default_factory=list)


@dataclass
class MergeOutcome:
    """Result of in-memory merge (no disk write)."""

    ok: bool
    merged_pool: dict | None
    merged_tree: dict | None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class ApplyOutcome:
    """Result after optional disk write, validate, sync."""

    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    dry_run: bool = False


def parse_ingest_patch(data: dict | None) -> IngestPatch:
    """Coerce arbitrary dict into :class:`IngestPatch`."""
    if data is None or not isinstance(data, dict):
        return IngestPatch()
    raw_ev = data.get("evidence_entries")
    entries: list[dict] = []
    if isinstance(raw_ev, list):
        for item in raw_ev:
            if isinstance(item, dict):
                entries.append(item)
    raw_nodes = data.get("node_updates")
    nodes: list[dict] = []
    if isinstance(raw_nodes, list):
        for item in raw_nodes:
            if isinstance(item, dict):
                nodes.append(item)
    return IngestPatch(
        evidence_entries=entries,
        node_updates=nodes,
    )


_ORD_REF_RE = re.compile(
    r"^(?:first_|ev_)(\d+)$",
    re.IGNORECASE,
)


def filter_ingest_patch(
    patch: IngestPatch | dict,
    *,
    include_evidence: list[bool] | None,
    include_nodes: list[bool] | None,
) -> tuple[IngestPatch, list[str]]:
    """Select evidence rows and node_updates; remap first_k/ev_k ordinals.

    When *include_evidence* or *include_nodes* is None, all rows are kept.
    Dropped evidence rows cause first_N refs on kept nodes to be remapped
    or removed with warnings.
    """
    if isinstance(patch, dict):
        p = parse_ingest_patch(patch)
    else:
        p = patch
    warnings: list[str] = []
    n_e = len(p.evidence_entries)
    n_n = len(p.node_updates)
    ev_mask = (
        include_evidence
        if include_evidence is not None
        else [True] * n_e
    )
    no_mask = (
        include_nodes
        if include_nodes is not None
        else [True] * n_n
    )
    while len(ev_mask) < n_e:
        ev_mask.append(True)
    while len(no_mask) < n_n:
        no_mask.append(True)

    sel_ev_idx = [i for i in range(n_e) if ev_mask[i]]
    old_to_new_ord: dict[int, int] = {}
    for new_ord_1b, old_i in enumerate(sel_ev_idx, start=1):
        old_to_new_ord[old_i] = new_ord_1b

    new_entries: list[dict] = []
    for old_i in sel_ev_idx:
        new_entries.append(copy.deepcopy(p.evidence_entries[old_i]))

    excluded_old_ids: set[str] = set()
    for old_i, row in enumerate(p.evidence_entries):
        if old_i in sel_ev_idx:
            continue
        if isinstance(row, dict):
            eid = str(row.get("id", "") or "").strip()
            if eid:
                excluded_old_ids.add(eid)

    new_nodes: list[dict] = []
    for j, upd in enumerate(p.node_updates):
        if j >= len(no_mask) or not no_mask[j]:
            continue
        if not isinstance(upd, dict):
            continue
        u = copy.deepcopy(upd)
        raw_refs = u.get("evidence_refs")
        if not isinstance(raw_refs, list):
            new_nodes.append(u)
            continue
        filt_refs: list[str] = []
        for r in raw_refs:
            if not isinstance(r, str):
                continue
            key = r.strip()
            if not key:
                continue
            om = _ORD_REF_RE.match(key)
            if om:
                old_ord = int(om.group(1)) - 1
                if old_ord < 0 or old_ord >= n_e:
                    warnings.append(
                        f"node_updates[{j}]: dropped ref {key!r} "
                        "(ordinal out of range)"
                    )
                    continue
                if old_ord not in sel_ev_idx:
                    warnings.append(
                        f"node_updates[{j}]: dropped ref {key!r} "
                        f"(evidence row {old_ord + 1} not selected)"
                    )
                    continue
                new_b = old_to_new_ord[old_ord]
                filt_refs.append(f"first_{new_b}")
                continue
            if key in excluded_old_ids:
                warnings.append(
                    f"node_updates[{j}]: dropped ref {key!r} "
                    "(evidence row not selected)"
                )
                continue
            filt_refs.append(key)
        if filt_refs:
            u["evidence_refs"] = filt_refs
        else:
            u.pop("evidence_refs", None)
        new_nodes.append(u)

    return (
        IngestPatch(
            evidence_entries=new_entries,
            node_updates=new_nodes,
        ),
        warnings,
    )


def _normalize_evidence_row(row: dict) -> dict | None:
    """Return a pool row dict or None if unusable."""
    title = str(row.get("title", "") or "").strip()
    if not title:
        return None
    type_ = str(row.get("type", "") or "practice").strip()
    if type_ not in EVIDENCE_TYPES:
        type_ = "practice"
    out: dict = {
        "id": str(row.get("id", "") or "").strip(),
        "type": type_,
        "title": title,
    }
    for key in ("date", "url", "summary"):
        val = row.get(key)
        if val is not None and str(val).strip():
            out[key] = str(val).strip()
    if row.get("deprecated") is True:
        out["deprecated"] = True
    rb = str(row.get("replaced_by", "") or "").strip()
    if rb:
        out["replaced_by"] = rb
    return out


def _ordinal_placeholder_to_id(
    ref: str,
    ordinal_to_id: dict[int, str],
) -> str | None:
    """Map LLM placeholders like first_1 / ev_3 to pool ids (1-based index)."""
    s = ref.strip()
    for pattern in (r"^first_(\d+)$", r"^ev_(\d+)$"):
        m = re.match(pattern, s, re.IGNORECASE)
        if m is not None:
            idx = int(m.group(1))
            return ordinal_to_id.get(idx)
    return None


_STATUS_RANK: dict[str, int] = {
    "locked": 0,
    "learning": 1,
    "solid": 2,
    "expert": 3,
}


def _status_rank(status: str) -> int:
    """Return tier for upgrade-only status merges."""
    r = _STATUS_RANK.get(status, -1)
    if r < 0:
        return _STATUS_RANK["locked"]
    return r


def _llm_status_effective(raw: str) -> str | None:
    """Map LLM status to a tier we may write; None if invalid.

    LLM ``expert`` is mapped to ``learning`` (never trust model expert).
    """
    s = str(raw or "").strip()
    if not s:
        return None
    if s == "expert":
        return "learning"
    if s in ALLOWED_STATUS:
        return s
    return None


def merge_ingest_patch(
    profile_name: str,
    pool_raw: dict | None,
    tree_raw: dict | None,
    patch: IngestPatch | dict,
    *,
    allow_status_change: bool = False,
    bump_locked_with_evidence: bool = True,
) -> MergeOutcome:
    """Merge patch into pool then tree (memory only).

    *pool_raw* / *tree_raw* may be None; missing files are treated as
    minimal empty structures. Schema name is taken from *tree_raw*.
    When *bump_locked_with_evidence* is True, nodes that still have
    status ``locked`` but have evidence refs or inline evidence
    become ``learning``.

    If a node already has status ``expert`` (human-confirmed in the
    tree), LLM ``status`` in the patch is not applied; ``expert`` is
    preserved.

    Otherwise ingest applies LLM status only when it is an **upgrade**
    or tie in the order locked < learning < solid < expert: e.g. it
    will not replace ``solid`` with ``learning``. LLM ``expert`` is
    mapped to the ``learning`` tier before comparing, and is only
    applied when that is not a downgrade from the current tier.
    """
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
    """Compare merged snapshot to on-disk pool/tree for preview UI.

    Returns (new_evidence_lines, tree_change_lines) as short strings.
    """
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


def _read_text(path: Path) -> str | None:
    """Return file text if it exists."""
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _restore_yaml_files(
    pool_path: Path,
    tree_path: Path,
    prev_pool: str | None,
    prev_tree: str | None,
) -> None:
    """Restore previous file contents (or remove if absent before)."""
    if prev_pool is not None:
        pool_path.write_text(prev_pool, encoding="utf-8")
    elif pool_path.exists():
        pool_path.unlink()
    if prev_tree is not None:
        tree_path.write_text(prev_tree, encoding="utf-8")
    elif tree_path.exists():
        tree_path.unlink()


def apply_merged_profile(
    profile_name: str,
    merged_pool: dict,
    merged_tree: dict,
    *,
    dry_run: bool = False,
) -> ApplyOutcome:
    """Write pool + tree, validate, sync SKILL.md; rollback on error."""
    pdir = profile_dir(profile_name)
    pool_path = pdir / "evidence-pool.yaml"
    tree_path = pdir / "skill-tree.yaml"

    if dry_run:
        return ApplyOutcome(ok=True, warnings=[], dry_run=True)

    prev_pool = _read_text(pool_path)
    prev_tree = _read_text(tree_path)

    from nblane.core.sync import write_generated_blocks

    try:
        save_evidence_pool(profile_name, merged_pool)
        save_skill_tree(profile_name, merged_tree)
    except OSError as exc:
        _restore_yaml_files(pool_path, tree_path, prev_pool, prev_tree)
        return ApplyOutcome(
            ok=False,
            errors=[str(exc)],
            warnings=[],
            dry_run=False,
        )

    errors, warnings = validate_one(pdir, check_sync=False)
    if errors:
        _restore_yaml_files(pool_path, tree_path, prev_pool, prev_tree)
        return ApplyOutcome(
            ok=False,
            errors=list(errors),
            warnings=list(warnings),
            dry_run=False,
        )

    warn_out = list(warnings)
    skill_md = pdir / "SKILL.md"
    if skill_md.exists():
        try:
            write_generated_blocks(pdir)
        except (OSError, ValueError) as exc:
            _restore_yaml_files(pool_path, tree_path, prev_pool, prev_tree)
            return ApplyOutcome(
                ok=False,
                errors=[str(exc)],
                warnings=warn_out,
                dry_run=False,
            )
    else:
        warn_out.append(
            "SKILL.md missing; skipped sync write_generated_blocks"
        )

    return ApplyOutcome(ok=True, warnings=warn_out, dry_run=False)


def run_ingest_patch(
    profile_name: str,
    patch: IngestPatch | dict,
    *,
    allow_status_change: bool = False,
    bump_locked_with_evidence: bool = True,
    dry_run: bool = False,
) -> tuple[MergeOutcome, ApplyOutcome]:
    """Load current YAML, merge *patch*, optionally write + validate + sync."""
    pool_raw = load_evidence_pool_raw(profile_name)
    tree_raw = load_skill_tree_raw(profile_name)
    merge = merge_ingest_patch(
        profile_name,
        pool_raw,
        tree_raw,
        patch,
        allow_status_change=allow_status_change,
        bump_locked_with_evidence=bump_locked_with_evidence,
    )
    if not merge.ok or merge.merged_pool is None:
        return merge, ApplyOutcome(
            ok=False,
            errors=list(merge.errors),
            warnings=list(merge.warnings),
            dry_run=dry_run,
        )
    merged_tree = merge.merged_tree
    if merged_tree is None:
        return merge, ApplyOutcome(
            ok=False,
            errors=["merge produced no tree"],
            warnings=list(merge.warnings),
            dry_run=dry_run,
        )
    apply = apply_merged_profile(
        profile_name,
        merge.merged_pool,
        merged_tree,
        dry_run=dry_run,
    )
    combined = list(merge.warnings) + list(apply.warnings)
    if not apply.ok:
        return merge, ApplyOutcome(
            ok=False,
            errors=list(apply.errors),
            warnings=combined,
            dry_run=dry_run,
        )
    return merge, ApplyOutcome(
        ok=True,
        warnings=combined,
        dry_run=dry_run,
    )


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
