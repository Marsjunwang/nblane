"""Editor-row helpers for the Skill Tree page.

Lives in ``core`` (not the Streamlit page) so the dirty-detection logic is
unit-testable: pages are digit-prefixed and execute Streamlit at import time.
"""

from __future__ import annotations

import json

from nblane.core.models import EVIDENCE_TYPES


def rows_to_nodes(rows: list[dict]) -> list[dict]:
    """Convert edited rows back to skill-tree nodes list."""
    out: list[dict] = []
    for r in rows:
        has_inline = bool(r.get("evidence"))
        has_refs = bool(r.get("evidence_refs"))
        has_ev = has_inline or has_refs
        if (
            r.get("status") == "locked"
            and not r.get("note")
            and not has_ev
        ):
            continue
        node: dict = {
            "id": r["id"],
            "status": r["status"],
        }
        if r.get("note"):
            node["note"] = r["note"]
        evs = r.get("evidence") or []
        cleaned: list[dict] = []
        for ev in evs:
            if not isinstance(ev, dict):
                continue
            title = str(ev.get("title", "") or "").strip()
            et = str(ev.get("type", "practice") or "practice")
            if et not in EVIDENCE_TYPES:
                et = "practice"
            if not title:
                continue
            item = {"type": et, "title": title}
            for k in ("date", "url", "summary"):
                v = str(ev.get(k, "") or "").strip()
                if v:
                    item[k] = v
            cleaned.append(item)
        if cleaned:
            node["evidence"] = cleaned
        refs_in = r.get("evidence_refs") or []
        uniq: list[str] = []
        seen: set[str] = set()
        if isinstance(refs_in, list):
            for x in refs_in:
                if not isinstance(x, str) or not x.strip():
                    continue
                key = x.strip()
                if key not in seen:
                    seen.add(key)
                    uniq.append(key)
        if uniq:
            node["evidence_refs"] = uniq
        out.append(node)
    return out


def serialize_rows_for_dirty(rows: list[dict]) -> str:
    """Canonical user-editable projection of editor rows.

    Routes through the same ``rows_to_nodes`` projection used at save time so
    baseline and current value are measured by identical rules. Top-level
    nodes are sorted by id to stay stable against row reordering;
    ``evidence_refs`` order is preserved because it is user-meaningful.
    """
    nodes = rows_to_nodes(rows)
    nodes_sorted = sorted(nodes, key=lambda n: n.get("id", ""))
    return json.dumps(nodes_sorted, sort_keys=True, ensure_ascii=False)


def rows_dirty(baseline: str | None, rows: list[dict]) -> bool:
    """Whether ``rows`` differ from the baseline projection captured on load."""
    if baseline is None:
        return False
    return serialize_rows_for_dirty(rows) != baseline
