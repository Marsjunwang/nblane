"""Derived read models for Evidence Review and skill evidence signals."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nblane.core.claims import (
    claim_usage_index_for_profile,
    claims_with_refresh_status,
    legacy_claims,
)
from nblane.core import io as io_facade
from nblane.core.io import KANBAN_DONE, STATUSES, schema_node_index
from nblane.core.experience import load_experience_book
from nblane.core.kanban_archive import find_kanban_tasks_by_ref, kanban_ref_id
from nblane.core.models import (
    EVIDENCE_CONFIDENCES,
    EVIDENCE_LANGUAGES,
    EVIDENCE_ORIGINS,
    EVIDENCE_PUBLIC_READINESS,
    EVIDENCE_REVIEW_STATUSES,
    EVIDENCE_STRENGTHS,
    EVIDENCE_TYPES,
)
from nblane.core.project_board import load_project_board
from nblane.core.research_sources import load_research_sources

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


def _merge_string_lists(*groups: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            clean = str(item or "").strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            out.append(clean)
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


# Editable pool fields the bulk/inline editors are allowed to touch. Keeping
# this explicit prevents the table editor from clobbering ids, refs, etc.
POOL_EDITABLE_FIELDS: dict[str, tuple[str, ...]] = {
    "strength": EVIDENCE_STRENGTHS,
    "confidence": EVIDENCE_CONFIDENCES,
    "review_status": EVIDENCE_REVIEW_STATUSES,
    "public_readiness": EVIDENCE_PUBLIC_READINESS,
}


def apply_pool_edits(
    entries: list[dict[str, Any]],
    edits: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], int]:
    """Apply per-id field edits to pool *entries*.

    *edits* maps evidence id -> {field: new_value}. Only fields in
    ``POOL_EDITABLE_FIELDS`` are applied, and only values inside each field's
    whitelist (an empty string clears the field). Rows are matched by id, not
    position, so pagination/sort order cannot misroute an edit. Returns the
    updated entries (same list object) and the count of rows changed.
    """
    by_id: dict[str, dict[str, Any]] = {}
    for row in entries:
        if isinstance(row, dict):
            rid = str(row.get("id", "") or "").strip()
            if rid:
                by_id[rid] = row
    changed = 0
    for rid, fields in edits.items():
        row = by_id.get(str(rid).strip())
        if row is None or not isinstance(fields, dict):
            continue
        row_changed = False
        for field, value in fields.items():
            allowed = POOL_EDITABLE_FIELDS.get(field)
            if allowed is None:
                continue
            clean = str(value or "").strip()
            if clean and clean not in allowed:
                continue
            current = str(row.get(field, "") or "").strip()
            if clean == current:
                continue
            if clean:
                row[field] = clean
            else:
                row.pop(field, None)
            row_changed = True
        if row_changed:
            changed += 1
    return entries, changed


def bulk_set_pool_field(
    entries: list[dict[str, Any]],
    ids: list[str],
    field: str,
    value: str,
) -> tuple[list[dict[str, Any]], int]:
    """Set one editable *field* to *value* on every row whose id is in *ids*.

    Validated against ``POOL_EDITABLE_FIELDS``; an unknown field or
    out-of-domain value is a no-op. Returns the entries and the change count.
    """
    allowed = POOL_EDITABLE_FIELDS.get(field)
    if allowed is None:
        return entries, 0
    clean = str(value or "").strip()
    if clean and clean not in allowed:
        return entries, 0
    target = {str(i).strip() for i in ids if str(i).strip()}
    if not target:
        return entries, 0
    changed = 0
    for row in entries:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id", "") or "").strip()
        if rid not in target:
            continue
        current = str(row.get(field, "") or "").strip()
        if clean == current:
            continue
        if clean:
            row[field] = clean
        else:
            row.pop(field, None)
        changed += 1
    return entries, changed


def link_skill_to_evidence_nodes(
    nodes: list[dict[str, Any]],
    skill_id: str,
    evidence_ids: list[str],
) -> list[dict[str, Any]]:
    """Attach *evidence_ids* to one skill node, mirroring per-evidence linking.

    Creates the node (status ``learning``) if missing, de-dupes refs, and
    preserves existing refs. Returns the (possibly extended) node list. Pure:
    operates on the given list of node dicts, no IO.
    """
    skill = str(skill_id or "").strip()
    new_refs = [str(e).strip() for e in evidence_ids if str(e).strip()]
    if not skill or not new_refs:
        return nodes
    by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if isinstance(node, dict):
            nid = str(node.get("id", "") or "").strip()
            if nid:
                by_id[nid] = node
    node = by_id.get(skill)
    if node is None:
        nodes.append(
            {
                "id": skill,
                "status": "learning",
                "evidence_refs": list(dict.fromkeys(new_refs)),
            }
        )
        return nodes
    refs = [
        str(ref).strip()
        for ref in (node.get("evidence_refs") or [])
        if str(ref).strip()
    ]
    for ref in new_refs:
        if ref not in refs:
            refs.append(ref)
    node["evidence_refs"] = refs
    return nodes


def set_evidence_skill_refs(
    nodes: list[dict[str, Any]],
    evidence_id: str,
    skill_ids: list[str],
) -> list[dict[str, Any]]:
    """Reconcile one evidence id across skill nodes (chip-save semantics).

    Unlike :func:`link_skill_to_evidence_nodes` (append-only), this adds the
    evidence id to every node in *skill_ids* and removes it from every other
    node, matching a toggleable chip UI. Selected nodes that don't exist yet
    are created with status ``learning``. De-dupes refs and drops an empty
    ``evidence_refs`` key. Pure: mutates/returns the given node list, no IO.
    """
    eid = str(evidence_id or "").strip()
    if not eid:
        return nodes
    selected = {
        str(s).strip() for s in skill_ids if str(s).strip()
    }

    by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if isinstance(node, dict):
            nid = str(node.get("id", "") or "").strip()
            if nid:
                by_id[nid] = node

    # Remove from / keep on existing nodes.
    for nid, node in by_id.items():
        refs = [
            str(ref).strip()
            for ref in (node.get("evidence_refs") or [])
            if str(ref).strip()
        ]
        has = eid in refs
        want = nid in selected
        if want and not has:
            refs.append(eid)
        elif not want and has:
            refs = [r for r in refs if r != eid]
        # De-dupe while preserving order.
        refs = list(dict.fromkeys(refs))
        if refs:
            node["evidence_refs"] = refs
        else:
            node.pop("evidence_refs", None)

    # Create selected nodes that don't exist yet.
    for nid in selected:
        if nid not in by_id:
            nodes.append(
                {
                    "id": nid,
                    "status": "learning",
                    "evidence_refs": [eid],
                }
            )
    return nodes


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


def _project_options(profile: str | Path) -> list[dict[str, str]]:
    """Return project case options for evidence refs."""
    board = load_project_board(profile)
    options: list[dict[str, str]] = []
    for case in board.project_cases:
        if not case.id:
            continue
        options.append(
            {
                "id": case.id,
                "label": case.title or case.id,
                "status": case.status,
            }
        )
    return options


def _experience_options(profile: str | Path) -> list[dict[str, str]]:
    """Return experience case options for evidence refs."""
    book = load_experience_book(profile)
    options: list[dict[str, str]] = []
    for case in book.experience_cases:
        if not case.id:
            continue
        parts = [case.organization]
        if case.role:
            parts.append(case.role)
        label = " · ".join(part for part in parts if part) or case.id
        options.append(
            {
                "id": case.id,
                "label": label,
                "status": case.status,
            }
        )
    return options


def _source_options(profile: str | Path) -> list[dict[str, str]]:
    """Return research source options for evidence refs."""
    inbox = load_research_sources(profile)
    options: list[dict[str, str]] = []
    for source in inbox.sources:
        if not source.id:
            continue
        options.append(
            {
                "id": source.id,
                "label": source.title or source.id,
                "status": source.status,
            }
        )
    return options


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


def infer_project_refs_from_kanban(
    profile: str | Path,
    row: dict[str, Any],
) -> dict[str, object]:
    """Infer evidence project ownership from linked Kanban task refs.

    Returns a pure candidate payload. Only a single inferred project is
    considered auto-applicable; multiple project ids are intentionally left for
    human choice.
    """
    evidence_id = str(row.get("id", "") or "").strip()
    refs = _clean_string_list(row.get("kanban_refs"))
    existing_projects = _clean_string_list(row.get("project_refs"))
    tasks = find_kanban_tasks_by_ref(profile, refs) if refs else []
    found_ids = {
        str(getattr(task, "id", "") or "").strip()
        for task in tasks
        if str(getattr(task, "id", "") or "").strip()
    }
    task_rows: list[dict[str, str]] = []
    project_refs: list[str] = []
    for task in tasks:
        task_id = str(getattr(task, "id", "") or "").strip()
        title = str(getattr(task, "title", "") or "").strip()
        project_id = str(getattr(task, "project_id", "") or "").strip()
        task_rows.append(
            {
                "id": task_id,
                "title": title,
                "project_id": project_id,
            }
        )
        if project_id and project_id not in project_refs:
            project_refs.append(project_id)
    missing_task_refs = [
        rid
        for rid in (kanban_ref_id(ref) for ref in refs)
        if rid and rid not in found_ids
    ]
    if not refs:
        status = "no_kanban_refs"
    elif len(project_refs) == 1:
        status = "single_project"
    elif len(project_refs) > 1:
        status = "multiple_projects"
    elif not tasks:
        status = "missing_task"
    else:
        status = "no_project"
    return {
        "id": evidence_id,
        "title": str(row.get("title", "") or ""),
        "kanban_refs": refs,
        "existing_project_refs": existing_projects,
        "inferred_project_refs": project_refs,
        "can_apply": status == "single_project",
        "status": status,
        "tasks": task_rows,
        "missing_task_refs": missing_task_refs,
    }


def evidence_project_ref_candidates(profile: str | Path) -> list[dict[str, object]]:
    """Return reviewed evidence rows whose project refs can be checked.

    Candidate rows are active, reviewed, currently missing ``project_refs``, and
    carry at least one ``kanban_refs`` entry.
    """
    candidates: list[dict[str, object]] = []
    for row in _pool_entries(profile):
        if bool(row.get("deprecated", False)):
            continue
        if normalize_review_status(row.get("review_status")) != "reviewed":
            continue
        if _clean_string_list(row.get("project_refs")):
            continue
        if not _clean_string_list(row.get("kanban_refs")):
            continue
        candidates.append(infer_project_refs_from_kanban(profile, row))
    return candidates


def apply_project_ref_inferences(
    entries: list[dict[str, Any]],
    candidates: list[dict[str, object]],
    evidence_ids: list[str],
) -> tuple[list[dict[str, Any]], int]:
    """Apply unambiguous project-ref candidates to matching evidence rows."""
    target_ids = {
        str(eid or "").strip()
        for eid in evidence_ids
        if str(eid or "").strip()
    }
    if not target_ids:
        return entries, 0
    by_id: dict[str, list[str]] = {}
    for candidate in candidates:
        cid = str(candidate.get("id", "") or "").strip()
        refs = _clean_string_list(candidate.get("inferred_project_refs"))
        if cid and len(refs) == 1:
            by_id[cid] = refs
    changed = 0
    for row in entries:
        if not isinstance(row, dict):
            continue
        row_id = str(row.get("id", "") or "").strip()
        inferred = by_id.get(row_id)
        if row_id not in target_ids or not inferred:
            continue
        existing = _clean_string_list(row.get("project_refs"))
        merged = _merge_string_lists(existing, inferred)
        if merged != existing:
            row["project_refs"] = merged
            changed += 1
    return entries, changed


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


def _row_match_text(row: dict[str, Any]) -> str:
    """Concatenate the text fields worth matching a row against skills.

    Title + summary + original/formatted content + source excerpt give the
    rule matcher enough signal without pulling in ids or metadata noise.
    """
    parts = [
        str(row.get("title", "") or ""),
        str(row.get("summary", "") or ""),
        str(row.get("original_content", "") or ""),
        str(row.get("formatted_content", "") or ""),
        str(row.get("source_excerpt", "") or ""),
    ]
    return "\n".join(p for p in parts if p.strip())


def evidence_skill_suggestions(
    profile: str | Path,
    rows: list[dict[str, Any]] | None = None,
    *,
    top_n: int = 6,
) -> dict[str, list[dict[str, object]]]:
    """Map evidence id -> ranked rule-based skill suggestions.

    Deterministic keyword/synonym overlap (no LLM): reuses ``gap.score_nodes``
    against the active schema so the editor can surface "evidence probably
    belongs to these skills" without the human scanning the full node list.
    Already-linked skills are excluded so suggestions only add signal.
    """
    from nblane.core import gap as gap_mod
    from nblane.core import learned_keywords as lk_store

    tree = _tree_raw(profile)
    schema_name = str(tree.get("schema", "") or "")
    if not schema_name:
        return {}
    schema_raw = io_facade.load_schema_raw(schema_name)
    if not isinstance(schema_raw, dict):
        return {}
    index = schema_node_index(schema_raw)
    learned = lk_store.load(schema_name)

    if rows is None:
        rows = _pool_entries(profile)
    usage = evidence_usage_index(profile)

    out: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        eid = str(row.get("id", "") or "").strip()
        if not eid or row.get("deprecated"):
            continue
        text = _row_match_text(row)
        if not text.strip():
            continue
        ranked = gap_mod.score_nodes(text, schema_raw, learned=learned)
        if not ranked:
            continue
        linked = {item["id"] for item in usage.get(eid, [])}
        suggestions: list[dict[str, object]] = []
        for nid, score in ranked:
            if nid in linked or nid not in index:
                continue
            suggestions.append(
                {
                    "id": nid,
                    "label": _node_label(index, nid),
                    "score": int(score),
                    "source": "rule",
                }
            )
            if len(suggestions) >= top_n:
                break
        if suggestions:
            out[eid] = suggestions
    return out


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
    claim_usage: dict[str, dict[str, list[dict[str, Any]]]],
) -> dict[str, object]:
    eid = str(row.get("id", "") or "").strip()
    used_by = list(usage.get(eid, []))
    claims = list((claim_usage.get("by_evidence") or {}).get(eid, []))
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
        "project_refs": _clean_string_list(row.get("project_refs")),
        "experience_refs": _clean_string_list(row.get("experience_refs")),
        "kanban_refs": _clean_string_list(row.get("kanban_refs")),
        "source_excerpt": str(row.get("source_excerpt", "") or ""),
        "origin": str(row.get("origin", "") or ""),
        "origin_ref": str(row.get("origin_ref", "") or ""),
        "origin_detail": str(row.get("origin_detail", "") or ""),
        "original_content": str(row.get("original_content", "") or ""),
        "formatted_content": str(row.get("formatted_content", "") or ""),
        "language": str(row.get("language", "") or ""),
        "original_language": str(row.get("original_language", "") or ""),
        "original_content_hash": str(
            row.get("original_content_hash", "") or ""
        ),
        "deprecated": bool(row.get("deprecated", False)),
        "replaced_by": str(row.get("replaced_by", "") or ""),
        "skill_refs": [item["id"] for item in used_by],
        "skill_ref_labels": [item["label"] for item in used_by],
        "usage": used_by,
        "usage_count": len(used_by),
        "claim_refs": [
            str(item.get("id", ""))
            for item in claims
            if str(item.get("id", "")).strip()
        ],
        "claims": claims,
        "claim_count": len(claims),
        "review_reason": _review_reason(row),
    }


def build_evidence_review(profile: str | Path) -> dict[str, object]:
    """Build the Evidence Review page and Dashboard pending-evidence payload."""
    usage = evidence_usage_index(profile)
    claim_usage = claim_usage_index_for_profile(profile)
    rows = [
        _evidence_row_payload(row, usage, claim_usage)
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
    project_ref_candidates = evidence_project_ref_candidates(profile)
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
            "project_ref_candidate_count": sum(
                1 for item in project_ref_candidates if item.get("can_apply")
            ),
        },
        "done_uncrystallized": done_uncrystallized,
        "evidence_rows": active_rows,
        "all_evidence_rows": rows,
        "unlinked": unlinked,
        "needs_review": needs_review,
        "project_ref_candidates": project_ref_candidates,
        "status_risks": status_risks,
        "skill_summaries": skill_summaries,
        "skill_options": skill_options,
        "project_options": _project_options(profile),
        "experience_options": _experience_options(profile),
        "source_options": _source_options(profile),
        "usage": usage,
        "claim_rows": claims_with_refresh_status(profile),
        "legacy_claim_rows": legacy_claims(profile),
        "claim_usage": claim_usage,
    }


# --- Evidence v2 React editor payload ---------------------------------------


def _public_project_options(profile: str | Path) -> list[dict[str, str]]:
    """Read-only options from public projects.yaml (NOT project_refs targets).

    These are surfaced as "public usage" only; the React editor must never
    write a public project id into project_refs (those are internal-only).
    """
    pdir = profile if isinstance(profile, Path) else io_facade.profile_dir(profile)
    raw = _read_profile_yaml(pdir / "projects.yaml")
    projects = raw.get("projects") or []
    options: list[dict[str, str]] = []
    for proj in projects:
        if not isinstance(proj, dict):
            continue
        pid = str(proj.get("id", "") or "").strip()
        if not pid:
            continue
        options.append(
            {
                "id": pid,
                "label": str(proj.get("title", "") or pid),
                "evidence_refs": [
                    str(r).strip()
                    for r in (proj.get("evidence_refs") or [])
                    if str(r).strip()
                ],
            }
        )
    return options


def _read_profile_yaml(path: Path) -> dict:
    """Load a profile-scoped YAML mapping; tolerate a missing file."""
    from nblane.core.yaml_io import _load_yaml_dict

    if not path.exists():
        return {}
    return _load_yaml_dict(path) or {}


def _output_options(profile: str | Path) -> list[dict[str, str]]:
    """Output rows that could become evidence (create_from_output picker)."""
    pdir = profile if isinstance(profile, Path) else io_facade.profile_dir(profile)
    raw = _read_profile_yaml(pdir / "outputs.yaml")
    outputs = raw.get("outputs") or []
    options: list[dict[str, str]] = []
    for out in outputs:
        if not isinstance(out, dict):
            continue
        oid = str(out.get("id", "") or "").strip()
        if not oid:
            continue
        options.append(
            {
                "id": oid,
                "label": str(out.get("title", "") or oid),
                "target": str(out.get("target", "") or out.get("type", "")),
                "status": str(out.get("status", "") or ""),
            }
        )
    return options


def _editor_row_derived(
    row: dict[str, Any],
    *,
    project_label_by_id: dict[str, str],
) -> dict[str, Any]:
    """UI-derived flags for one row in the React editor list."""
    origin = str(row.get("origin", "") or "")
    project_refs = [
        str(r).strip() for r in (row.get("project_refs") or []) if str(r).strip()
    ]
    has_original = bool(str(row.get("original_content", "") or "").strip())
    # A row needs migration when it lacks any v2 provenance signal.
    needs_migration = not origin or not has_original
    source_label = str(row.get("origin_detail", "") or "") or origin
    return {
        "has_project": bool(project_refs),
        "has_original_content": has_original,
        "needs_migration": needs_migration,
        "source_label": source_label,
        "project_labels": [
            project_label_by_id.get(pid, pid) for pid in project_refs
        ],
    }


def _enum_options(values: tuple[str, ...]) -> list[dict[str, str]]:
    return [{"id": v, "label": v} for v in values]


def evidence_editor_migration_summary(
    profile: str | Path,
    *,
    rows: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Counts driving the editor toolbar (migration / missing raw / orphans)."""
    if rows is None:
        rows = _pool_entries(profile)
    needs_migration = 0
    missing_raw = 0
    resume_manual_unassigned = 0
    for row in rows:
        if row.get("deprecated"):
            continue
        origin = str(row.get("origin", "") or "")
        has_raw = bool(str(row.get("original_content", "") or "").strip())
        if not origin or not has_raw:
            needs_migration += 1
        if not has_raw:
            missing_raw += 1
        project_refs = [
            r for r in (row.get("project_refs") or []) if str(r).strip()
        ]
        if origin in ("resume_parse", "manual_daily") and not project_refs:
            resume_manual_unassigned += 1
    # Crystallized tasks without evidence + output candidates.
    try:
        from nblane.core.evidence_migrate import refresh_from_crystallized_tasks

        crystallized = refresh_from_crystallized_tasks(profile, entries=rows)
        crystallized_new = sum(
            1 for p in crystallized["proposals"] if p["kind"] == "new"
        )
    except Exception:
        crystallized_new = 0
    output_candidates = len(_output_options(profile))
    return {
        "needs_migration": needs_migration,
        "missing_raw": missing_raw,
        "resume_manual_unassigned": resume_manual_unassigned,
        "crystallized_without_evidence": crystallized_new,
        "output_candidates": output_candidates,
    }


def _done_task_options(profile: str | Path) -> list[dict[str, object]]:
    """Done-section kanban tasks for the editor's Done -> evidence picker.

    Includes crystallized *and* non-crystallized Done tasks. Each entry carries
    ``has_evidence`` (an evidence row already references the task) so the React
    picker can show, but not hide, already-ingested tasks.
    """
    from nblane.core.evidence_migrate import refresh_from_crystallized_tasks

    sections = io_facade.parse_kanban(profile)
    done_tasks = sections.get(KANBAN_DONE) or []
    # Reuse the deterministic proposal indexer to know which Done tasks already
    # resolve to an existing evidence row (kind == "update").
    try:
        result = refresh_from_crystallized_tasks(
            profile, entries=_pool_entries(profile), include_uncrystallized=True
        )
        evidence_task_ids = {
            str(p.get("task_id") or "")
            for p in (result.get("proposals") or [])
            if p.get("kind") == "update"
        }
    except Exception:
        evidence_task_ids = set()
    out: list[dict[str, object]] = []
    for task in done_tasks:
        tid = str(getattr(task, "id", "") or "").strip()
        if not tid:
            continue
        out.append(
            {
                "id": tid,
                "title": str(getattr(task, "title", "") or "") or tid,
                "crystallized": bool(getattr(task, "crystallized", False)),
                "has_evidence": tid in evidence_task_ids,
                "completed_on": str(getattr(task, "completed_on", "") or ""),
                "project_id": str(getattr(task, "project_id", "") or ""),
            }
        )
    return out


def build_evidence_editor_payload(profile: str | Path) -> dict[str, object]:
    """Full payload for the unified React evidence editor component.

    Extends build_evidence_review() with editor-only data: public project
    options (read-only), project suggestions, output options, enum option
    lists, migration summary, and per-row UI-derived flags.
    """
    from nblane.core.evidence_migrate import suggest_projects_from_evidence

    review = build_evidence_review(profile)
    all_rows = list(review.get("all_evidence_rows") or [])
    active_rows = list(review.get("evidence_rows") or [])

    project_options = list(review.get("project_options") or [])
    project_label_by_id = {
        str(o.get("id")): str(o.get("label") or o.get("id"))
        for o in project_options
    }

    # Annotate each active row with derived UI flags.
    enriched_rows: list[dict[str, Any]] = []
    skill_suggestions = evidence_skill_suggestions(profile, rows=active_rows)
    for row in active_rows:
        derived = _editor_row_derived(
            row, project_label_by_id=project_label_by_id
        )
        derived["skill_suggestions"] = skill_suggestions.get(
            str(row.get("id", "") or ""), []
        )
        enriched_rows.append({**row, **derived})

    suggestions = suggest_projects_from_evidence(active_rows)

    return {
        "profile": _profile_name(profile),
        "evidence_rows": enriched_rows,
        "all_evidence_rows": all_rows,
        "project_options": project_options,
        "public_project_options": _public_project_options(profile),
        "experience_options": review.get("experience_options") or [],
        "source_options": review.get("source_options") or [],
        "skill_options": review.get("skill_options") or [],
        "output_options": _output_options(profile),
        "done_task_options": _done_task_options(profile),
        "project_ref_candidates": review.get("project_ref_candidates") or [],
        "project_suggestions": suggestions,
        "migration_summary": evidence_editor_migration_summary(
            profile, rows=_pool_entries(profile)
        ),
        "origin_options": _enum_options(EVIDENCE_ORIGINS),
        "type_options": _enum_options(tuple(sorted(EVIDENCE_TYPES))),
        "language_options": _enum_options(EVIDENCE_LANGUAGES),
        "review_status_options": _enum_options(EVIDENCE_REVIEW_STATUSES),
        "strength_options": _enum_options(EVIDENCE_STRENGTHS),
        "confidence_options": _enum_options(EVIDENCE_CONFIDENCES),
        "public_readiness_options": _enum_options(EVIDENCE_PUBLIC_READINESS),
        "summary": review.get("summary") or {},
    }
