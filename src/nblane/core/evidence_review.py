"""Derived read models for Evidence Review and skill evidence signals."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nblane.core import io as io_facade
from nblane.core.io import KANBAN_DONE, STATUSES, schema_node_index
from nblane.core.models import (
    EVIDENCE_CONFIDENCES,
    EVIDENCE_PUBLIC_READINESS,
    EVIDENCE_REVIEW_STATUSES,
    EVIDENCE_STRENGTHS,
)

EVIDENCE_REVIEW_PAGE = "pages/2_Evidence_Review.py"
UNRATED_STRENGTH = "unrated"
EVIDENCE_STRENGTH_ORDER: dict[str, int] = {
    UNRATED_STRENGTH: 0,
    "": 0,
    "weak": 1,
    "medium": 2,
    "strong": 3,
    "high_trust": 4,
}
_STRENGTH_BY_RANK = {
    value: key
    for key, value in EVIDENCE_STRENGTH_ORDER.items()
    if key and key != UNRATED_STRENGTH
}
_STATUS_STRENGTH_REQUIREMENTS = {
    "solid": "medium",
    "expert": "strong",
}


def _profile_name(profile: str | Path) -> str:
    return profile.name if isinstance(profile, Path) else str(profile)


def _as_list(raw: object) -> list:
    return raw if isinstance(raw, list) else []


def _clean_string_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if item is None:
            continue
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def normalize_evidence_strength(value: object) -> str:
    """Return a valid strength string, or ``unrated`` for missing/invalid."""
    raw = str(value or "").strip()
    return raw if raw in EVIDENCE_STRENGTHS else UNRATED_STRENGTH


def evidence_strength_rank(value: object) -> int:
    """Return the comparable rank for an evidence strength."""
    return EVIDENCE_STRENGTH_ORDER.get(
        normalize_evidence_strength(value),
        0,
    )


def normalize_evidence_confidence(value: object) -> str:
    """Return a valid confidence string, or an empty string."""
    raw = str(value or "").strip()
    return raw if raw in EVIDENCE_CONFIDENCES else ""


def normalize_review_status(value: object) -> str:
    """Return review status; missing rows are treated as needing review."""
    raw = str(value or "").strip()
    return raw if raw in EVIDENCE_REVIEW_STATUSES else "needs_review"


def normalize_public_readiness(value: object) -> str:
    """Return public readiness; missing rows stay private by default."""
    raw = str(value or "").strip()
    return raw if raw in EVIDENCE_PUBLIC_READINESS else "private"


def _pool_entries(profile: str | Path) -> list[dict[str, Any]]:
    raw = io_facade.load_evidence_pool_raw(profile) or {}
    entries = raw.get("evidence_entries") or []
    return [dict(item) for item in entries if isinstance(item, dict)]


def _pool_by_id(profile: str | Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in _pool_entries(profile):
        eid = str(row.get("id", "") or "").strip()
        if eid:
            out[eid] = row
    return out


def _tree_raw(profile: str | Path) -> dict[str, Any]:
    raw = io_facade.load_skill_tree_raw(profile)
    return raw if isinstance(raw, dict) else {}


def _schema_index(tree_raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    schema_name = str(tree_raw.get("schema", "") or "")
    if not schema_name:
        return {}
    schema_raw = io_facade.load_schema_raw(schema_name)
    return schema_node_index(schema_raw) if schema_raw else {}


def _node_label(
    index: dict[str, dict[str, Any]],
    node_id: str,
) -> str:
    meta = index.get(node_id) or {}
    return str(meta.get("label") or node_id)


def evidence_usage_index(profile: str | Path) -> dict[str, list[dict[str, str]]]:
    """Return evidence id -> skill-node refs that cite it."""
    tree = _tree_raw(profile)
    index = _schema_index(tree)
    usage: dict[str, list[dict[str, str]]] = {}
    seen: set[tuple[str, str]] = set()
    for node in _as_list(tree.get("nodes")):
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", "") or "").strip()
        if not node_id:
            continue
        status = str(node.get("status", "locked") or "locked")
        for ref in _clean_string_list(node.get("evidence_refs")):
            key = (ref, node_id)
            if key in seen:
                continue
            seen.add(key)
            usage.setdefault(ref, []).append(
                {
                    "id": node_id,
                    "label": _node_label(index, node_id),
                    "status": status,
                }
            )
    return usage


def _highest_strength(
    records: list[dict[str, Any]],
    inline_count: int,
) -> tuple[str, int]:
    ranks = [evidence_strength_rank(record.get("strength")) for record in records]
    ranks.extend([0] * inline_count)
    highest = max(ranks, default=0)
    return _STRENGTH_BY_RANK.get(highest, UNRATED_STRENGTH), highest


def _node_review_status(
    records: list[dict[str, Any]],
    inline_count: int,
) -> str:
    if inline_count:
        return "needs_review"
    if not records:
        return ""
    for record in records:
        if normalize_review_status(record.get("review_status")) != "reviewed":
            return "needs_review"
        if normalize_evidence_strength(record.get("strength")) == UNRATED_STRENGTH:
            return "needs_review"
    return "reviewed"


def _risk_for_status(
    *,
    status: str,
    evidence_count: int,
    highest_strength: str,
    highest_rank: int,
) -> tuple[str, str, str]:
    required = _STATUS_STRENGTH_REQUIREMENTS.get(status, "")
    if not required:
        return "", "", ""
    if evidence_count <= 0:
        return (
            "missing_evidence",
            required,
            f"{status} requires evidence, but none is linked.",
        )
    required_rank = evidence_strength_rank(required)
    if highest_rank < required_rank:
        return (
            "insufficient_strength",
            required,
            (
                f"{status} requires {required}+ evidence; "
                f"highest is {highest_strength}."
            ),
        )
    return "", required, ""


def skill_evidence_summaries(profile: str | Path) -> list[dict[str, object]]:
    """Return one evidence signal row for every skill in the active tree."""
    tree = _tree_raw(profile)
    index = _schema_index(tree)
    pool = _pool_by_id(profile)
    nodes = {
        str(node.get("id", "") or "").strip(): node
        for node in _as_list(tree.get("nodes"))
        if isinstance(node, dict) and str(node.get("id", "") or "").strip()
    }
    if index:
        node_ids = list(index)
    else:
        node_ids = list(nodes)

    summaries: list[dict[str, object]] = []
    for node_id in node_ids:
        meta = index.get(node_id) or {}
        node = nodes.get(node_id, {})
        status = str(node.get("status", "locked") or "locked")
        if status not in STATUSES:
            status = "locked"
        refs = _clean_string_list(node.get("evidence_refs"))
        active_refs: list[str] = []
        missing_refs: list[str] = []
        records: list[dict[str, Any]] = []
        for ref in refs:
            record = pool.get(ref)
            if record is None:
                missing_refs.append(ref)
                continue
            if bool(record.get("deprecated", False)):
                continue
            active_refs.append(ref)
            records.append(record)
        inline = [
            item
            for item in _as_list(node.get("evidence"))
            if isinstance(item, dict)
        ]
        inline_count = len(inline)
        evidence_count = len(records) + inline_count
        highest_strength, highest_rank = _highest_strength(
            records,
            inline_count,
        )
        review_status = _node_review_status(records, inline_count)
        risk_level, required_strength, risk_reason = _risk_for_status(
            status=status,
            evidence_count=evidence_count,
            highest_strength=highest_strength,
            highest_rank=highest_rank,
        )
        summaries.append(
            {
                "id": node_id,
                "label": _node_label(index, node_id),
                "category": str(meta.get("category", "") or ""),
                "level": int(meta.get("level", 0) or 0),
                "status": status,
                "evidence_count": evidence_count,
                "pool_ref_count": len(records),
                "inline_count": inline_count,
                "evidence_refs": refs,
                "active_evidence_refs": active_refs,
                "missing_evidence_refs": missing_refs,
                "highest_strength": highest_strength,
                "highest_strength_rank": highest_rank,
                "review_status": review_status,
                "required_strength": required_strength,
                "risk_level": risk_level,
                "risk_reason": risk_reason,
            }
        )
    return summaries


def evidence_status_risks(profile: str | Path) -> list[dict[str, object]]:
    """Return solid/expert skill rows whose evidence is missing or too weak."""
    risks: list[dict[str, object]] = []
    for summary in skill_evidence_summaries(profile):
        if not summary.get("risk_level"):
            continue
        risks.append(summary)
    return risks


def _done_uncrystallized(profile: str | Path) -> list[dict[str, object]]:
    sections = io_facade.parse_kanban(profile)
    done_tasks = sections.get(KANBAN_DONE) or []
    out: list[dict[str, object]] = []
    for task in done_tasks:
        if getattr(task, "crystallized", False):
            continue
        tags = getattr(task, "tags", "")
        out.append(
            {
                "id": getattr(task, "id", ""),
                "title": getattr(task, "title", ""),
                "completed_on": getattr(task, "completed_on", "") or "",
                "outcome": getattr(task, "outcome", "") or "",
                "tags": tags,
            }
        )
    return out


def _review_reason(row: dict[str, Any]) -> str:
    reasons: list[str] = []
    if normalize_evidence_strength(row.get("strength")) == UNRATED_STRENGTH:
        reasons.append("missing_strength")
    if normalize_review_status(row.get("review_status")) != "reviewed":
        reasons.append("needs_review")
    return ", ".join(reasons)


def _evidence_row_payload(
    row: dict[str, Any],
    usage: dict[str, list[dict[str, str]]],
) -> dict[str, object]:
    eid = str(row.get("id", "") or "").strip()
    used_by = list(usage.get(eid, []))
    return {
        "id": eid,
        "type": str(row.get("type", "") or ""),
        "title": str(row.get("title", "") or ""),
        "date": str(row.get("date", "") or ""),
        "url": str(row.get("url", "") or ""),
        "summary": str(row.get("summary", "") or ""),
        "strength": normalize_evidence_strength(row.get("strength")),
        "confidence": normalize_evidence_confidence(row.get("confidence")),
        "review_status": normalize_review_status(row.get("review_status")),
        "public_readiness": normalize_public_readiness(
            row.get("public_readiness")
        ),
        "source_refs": _clean_string_list(row.get("source_refs")),
        "deprecated": bool(row.get("deprecated", False)),
        "replaced_by": str(row.get("replaced_by", "") or ""),
        "skill_refs": [item["id"] for item in used_by],
        "skill_ref_labels": [item["label"] for item in used_by],
        "usage": used_by,
        "usage_count": len(used_by),
        "review_reason": _review_reason(row),
    }


def build_evidence_review(profile: str | Path) -> dict[str, object]:
    """Build the Evidence Review page and Dashboard pending-evidence payload."""
    usage = evidence_usage_index(profile)
    rows = [
        _evidence_row_payload(row, usage)
        for row in _pool_entries(profile)
        if str(row.get("id", "") or "").strip()
    ]
    active_rows = [row for row in rows if not row["deprecated"]]
    unlinked = [row for row in active_rows if not row["usage_count"]]
    needs_review = [
        row
        for row in active_rows
        if row["strength"] == UNRATED_STRENGTH
        or row["review_status"] != "reviewed"
    ]
    status_risks = evidence_status_risks(profile)
    done_uncrystallized = _done_uncrystallized(profile)
    skill_summaries = skill_evidence_summaries(profile)
    skill_options = [
        {
            "id": str(item.get("id", "")),
            "label": str(item.get("label", "") or item.get("id", "")),
            "status": str(item.get("status", "")),
        }
        for item in skill_summaries
    ]
    return {
        "profile": _profile_name(profile),
        "summary": {
            "done_uncrystallized_count": len(done_uncrystallized),
            "unlinked_count": len(unlinked),
            "needs_review_count": len(needs_review),
            "status_risk_count": len(status_risks),
            "total_entries": len(active_rows),
        },
        "done_uncrystallized": done_uncrystallized,
        "evidence_rows": active_rows,
        "all_evidence_rows": rows,
        "unlinked": unlinked,
        "needs_review": needs_review,
        "status_risks": status_risks,
        "skill_summaries": skill_summaries,
        "skill_options": skill_options,
        "usage": usage,
    }
