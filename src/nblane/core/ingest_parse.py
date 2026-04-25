"""Parsing and filtering helpers for profile ingest patches."""

from __future__ import annotations

import copy
import re

from nblane.core.ingest_models import IngestPatch
from nblane.core.models import EVIDENCE_TYPES
from nblane.core.validate import ALLOWED_STATUS


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
