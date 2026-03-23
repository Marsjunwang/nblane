"""Resolve skill-node evidence: pool refs plus inline rows."""

from __future__ import annotations

from nblane.core.models import Evidence, EvidencePool, EvidenceRecord, SkillNode


def resolve_node_evidence_dict(
    node: dict,
    pool: EvidencePool | None,
) -> list[Evidence]:
    """Materialize evidence for a raw skill-tree node dict.

    Order: ``evidence_refs`` first (deduplicated by id), then inline
    ``evidence`` rows. Missing pool ids are skipped (validate catches refs).
    """
    index: dict[str, EvidenceRecord] = (
        pool.by_id() if pool is not None else {}
    )
    out: list[Evidence] = []
    seen: set[str] = set()

    raw_refs = node.get("evidence_refs") or []
    if isinstance(raw_refs, list):
        for rid in raw_refs:
            if not isinstance(rid, str):
                continue
            key = rid.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            rec = index.get(key)
            if rec is None:
                continue
            out.append(rec.to_evidence())

    raw_ev = node.get("evidence") or []
    if isinstance(raw_ev, list):
        for item in raw_ev:
            if isinstance(item, dict):
                out.append(Evidence.from_dict(item))
    return out


def resolve_skill_node(
    node: SkillNode,
    pool: EvidencePool | None,
) -> list[Evidence]:
    """Materialize evidence for a SkillNode model instance."""
    d = node.to_dict()
    return resolve_node_evidence_dict(d, pool)


def resolved_evidence_count(
    node: dict,
    pool: EvidencePool | None,
) -> int:
    """Count materialized evidence rows for gap metrics."""
    return len(resolve_node_evidence_dict(node, pool))
