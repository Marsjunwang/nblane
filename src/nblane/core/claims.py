"""Claim candidate and accepted-claim helpers.

Claims are the P2 bridge between reviewed evidence and downstream skills or
public output. They live in ``evidence-pool.yaml`` as a top-level ``claims``
list for now; there is intentionally no separate ``claims.yaml`` store.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any

from nblane.core import io as io_facade
from nblane.core.models import (
    CLAIM_STATUSES,
    CLAIM_TYPES,
    EVIDENCE_CONFIDENCES,
    EVIDENCE_PUBLIC_READINESS,
)


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _clean_string_list(value: object) -> list[str]:
    raw_items: Iterable[object]
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, tuple):
        raw_items = value
    elif isinstance(value, str):
        raw_items = [
            item
            for chunk in value.splitlines()
            for item in chunk.split(",")
        ]
    else:
        raw_items = []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        text = _clean_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _profile_name(profile: str | Path) -> str:
    return profile.name if isinstance(profile, Path) else str(profile)


def _normalized_text(value: object) -> str:
    return " ".join(_clean_text(value).casefold().split())


def _claim_key(claim: dict[str, Any]) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    return (
        _normalized_text(claim.get("text")),
        tuple(_clean_string_list(claim.get("evidence_refs"))),
        tuple(_clean_string_list(claim.get("skill_refs"))),
    )


def _claim_id(text: str, existing_ids: set[str]) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")[:36]
    if not slug:
        slug = "claim"
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    base = f"claim:{slug}-{digest}"
    candidate = base
    suffix = 2
    while candidate in existing_ids:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _evidence_index_from_pool(pool_raw: dict | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not isinstance(pool_raw, dict):
        return out
    entries = pool_raw.get("evidence_entries") or []
    if not isinstance(entries, list):
        return out
    for item in entries:
        if not isinstance(item, dict):
            continue
        evidence_id = _clean_text(item.get("id"))
        if evidence_id:
            out[evidence_id] = item
    return out


def _skill_refs_by_evidence(profile: str | Path) -> dict[str, list[str]]:
    tree = io_facade.load_skill_tree_raw(profile)
    out: dict[str, list[str]] = {}
    if not isinstance(tree, dict):
        return out
    for node in tree.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        node_id = _clean_text(node.get("id"))
        if not node_id:
            continue
        for ref in _clean_string_list(node.get("evidence_refs")):
            refs = out.setdefault(ref, [])
            if node_id not in refs:
                refs.append(node_id)
    return out


def normalize_claim(
    raw: dict[str, Any],
    *,
    existing_ids: set[str] | None = None,
    created: str | None = None,
    force_accepted: bool = True,
) -> dict[str, Any] | None:
    """Return a stable accepted-claim mapping or ``None`` for empty text."""
    text = _clean_text(raw.get("text"))
    if not text:
        return None
    existing = existing_ids if existing_ids is not None else set()
    raw_id = _clean_text(raw.get("id"))
    claim_id = raw_id if raw_id else _claim_id(text, existing)
    claim_type = _clean_text(raw.get("type")) or "achievement"
    if claim_type not in CLAIM_TYPES:
        claim_type = "achievement"
    public_readiness = _clean_text(raw.get("public_readiness")) or "private"
    if public_readiness not in EVIDENCE_PUBLIC_READINESS:
        public_readiness = "private"
    confidence = _clean_text(raw.get("confidence")) or "medium"
    if confidence not in EVIDENCE_CONFIDENCES:
        confidence = "medium"
    status = _clean_text(raw.get("status"))
    if force_accepted or not status:
        status = "accepted"
    elif status not in CLAIM_STATUSES:
        # Preserve non-accepted statuses for diagnostics, but never emit an
        # empty status because claim validators need to distinguish bad state
        # from a missing claim id.
        status = _clean_text(raw.get("status")) or "unknown"
    return {
        "id": claim_id,
        "status": status,
        "type": claim_type,
        "text": text,
        "evidence_refs": _clean_string_list(raw.get("evidence_refs")),
        "skill_refs": _clean_string_list(raw.get("skill_refs")),
        "project_refs": _clean_string_list(raw.get("project_refs")),
        "experience_refs": _clean_string_list(raw.get("experience_refs")),
        "source_refs": _clean_string_list(raw.get("source_refs")),
        "output_refs": _clean_string_list(raw.get("output_refs")),
        "public_readiness": public_readiness,
        "confidence": confidence,
        "rationale": _clean_text(raw.get("rationale")),
        "warnings": _clean_string_list(raw.get("warnings")),
        "generated_by": _clean_text(raw.get("generated_by")) or "rule",
        "created": _clean_text(raw.get("created")) or created or date.today().isoformat(),
    }


def accepted_claims(pool_raw: dict | None) -> list[dict[str, Any]]:
    """Return normalized accepted claims from an evidence-pool mapping."""
    if not isinstance(pool_raw, dict):
        return []
    out: list[dict[str, Any]] = []
    existing_ids: set[str] = set()
    for item in pool_raw.get("claims") or []:
        if not isinstance(item, dict):
            continue
        raw_status = _clean_text(item.get("status")) or "accepted"
        if raw_status != "accepted":
            continue
        claim = normalize_claim(
            item,
            existing_ids=existing_ids,
            force_accepted=False,
        )
        if claim is None or claim.get("status") != "accepted":
            continue
        existing_ids.add(str(claim["id"]))
        out.append(claim)
    return out


def claim_index(pool_raw: dict | None) -> dict[str, dict[str, Any]]:
    """Return all claim id -> claim mappings, preserving raw status."""
    if not isinstance(pool_raw, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    existing_ids: set[str] = set()
    for item in pool_raw.get("claims") or []:
        if not isinstance(item, dict):
            continue
        claim = normalize_claim(
            item,
            existing_ids=existing_ids,
            force_accepted=False,
        )
        if claim is None:
            continue
        claim_id = _clean_text(claim.get("id"))
        if not claim_id:
            continue
        existing_ids.add(claim_id)
        out[claim_id] = claim
    return out


def accepted_claim_index(pool_raw: dict | None) -> dict[str, dict[str, Any]]:
    """Return accepted claim id -> claim mapping."""
    return {
        str(claim.get("id")): claim
        for claim in accepted_claims(pool_raw)
        if _clean_text(claim.get("id"))
    }


def claim_usage_index(pool_raw: dict | None) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Return accepted claims grouped by upstream/downstream refs."""
    usage: dict[str, dict[str, list[dict[str, Any]]]] = {
        "by_evidence": {},
        "by_skill": {},
        "by_project": {},
        "by_experience": {},
        "by_source": {},
        "by_output": {},
    }
    ref_fields = {
        "by_evidence": "evidence_refs",
        "by_skill": "skill_refs",
        "by_project": "project_refs",
        "by_experience": "experience_refs",
        "by_source": "source_refs",
        "by_output": "output_refs",
    }
    for claim in accepted_claims(pool_raw):
        for bucket, field_name in ref_fields.items():
            for ref in _clean_string_list(claim.get(field_name)):
                usage[bucket].setdefault(ref, []).append(claim)
    return usage


def generate_claim_candidates(
    profile: str | Path,
    evidence_ids: list[str],
) -> list[dict[str, Any]]:
    """Generate deterministic claim candidates from selected evidence rows.

    This function is intentionally non-mutating. It provides a stable fallback
    even when AI is not configured; later AI routing can replace or augment the
    candidate text while preserving the same apply path.
    """
    pool_raw = io_facade.load_evidence_pool_raw(profile) or {}
    evidence = _evidence_index_from_pool(pool_raw)
    skill_refs = _skill_refs_by_evidence(profile)
    candidates: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
    for evidence_id in _clean_string_list(evidence_ids):
        row = evidence.get(evidence_id)
        if row is None:
            continue
        title = _clean_text(row.get("title")) or evidence_id
        summary = _clean_text(row.get("summary"))
        evidence_type = _clean_text(row.get("type")) or "practice"
        claim_type = {
            "project": "achievement",
            "paper": "learning",
            "course": "learning",
            "learning": "learning",
            "practice": "skill",
        }.get(evidence_type, "achievement")
        text = summary if summary and len(summary) >= len(title) else title
        if not text.endswith((".", "。", "!", "！", "?", "？")):
            text = f"{text}."
        candidate = normalize_claim(
            {
                "type": claim_type,
                "text": text,
                "evidence_refs": [evidence_id],
                "skill_refs": skill_refs.get(evidence_id, []),
                "project_refs": row.get("project_refs") or [],
                "experience_refs": row.get("experience_refs") or [],
                "source_refs": row.get("source_refs") or [],
                "public_readiness": row.get("public_readiness") or "private",
                "confidence": row.get("confidence") or "medium",
                "rationale": f"Derived from evidence {evidence_id}: {title}",
                "warnings": [
                    "Review wording before using this claim in skill or public output.",
                ],
                "generated_by": "rule:evidence_review",
            },
            existing_ids=set(),
        )
        if candidate is None:
            continue
        key = _claim_key(candidate)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        candidates.append(candidate)
    return candidates


def apply_claim_candidates(
    pool_raw: dict | None,
    candidates: list[dict[str, Any]],
    *,
    known_skill_ids: set[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    """Merge selected candidates into ``pool_raw`` and return the new pool.

    Candidates with dangling evidence refs are skipped. Unknown skill refs are
    dropped with warnings instead of being silently persisted.
    """
    pool: dict[str, Any] = dict(pool_raw or {})
    entries = pool.get("evidence_entries")
    if not isinstance(entries, list):
        entries = []
    pool["evidence_entries"] = entries
    evidence_ids = set(_evidence_index_from_pool(pool).keys())
    skill_ids = known_skill_ids if known_skill_ids is not None else set()
    existing_claims = accepted_claims(pool)
    existing_ids = {str(claim.get("id")) for claim in existing_claims}
    by_key = {_claim_key(claim): index for index, claim in enumerate(existing_claims)}
    warnings: list[str] = []
    applied: list[dict[str, Any]] = []

    for raw in candidates:
        if not isinstance(raw, dict):
            continue
        normalized = normalize_claim(raw, existing_ids=existing_ids)
        if normalized is None:
            continue
        unknown_evidence = [
            ref for ref in normalized["evidence_refs"] if ref not in evidence_ids
        ]
        if unknown_evidence:
            warnings.append(
                f"skipped claim with unknown evidence refs: {', '.join(unknown_evidence)}"
            )
            continue
        if known_skill_ids is not None:
            valid_skills: list[str] = []
            for ref in normalized["skill_refs"]:
                if ref in skill_ids:
                    valid_skills.append(ref)
                else:
                    warnings.append(
                        f"{normalized['id']}: dropped unknown skill ref {ref!r}"
                    )
            normalized["skill_refs"] = valid_skills
        key = _claim_key(normalized)
        if key in by_key:
            existing = existing_claims[by_key[key]]
            normalized["id"] = str(existing.get("id"))
            normalized["created"] = str(existing.get("created") or normalized["created"])
            existing_claims[by_key[key]] = normalized
        else:
            while normalized["id"] in existing_ids:
                normalized["id"] = _claim_id(normalized["text"], existing_ids)
            existing_ids.add(str(normalized["id"]))
            by_key[key] = len(existing_claims)
            existing_claims.append(normalized)
        applied.append(normalized)

    pool["claims"] = existing_claims
    return pool, applied, warnings
