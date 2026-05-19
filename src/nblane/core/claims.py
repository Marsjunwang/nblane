"""Claim candidate, claim-book, and accepted-claim helpers.

Claims are the bridge between reviewed evidence and downstream skills or
public output. New profile-level claims live in ``claims.yaml``. Legacy
``evidence-pool.yaml`` top-level ``claims`` are still readable as a fallback
and can be migrated explicitly.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from nblane.core import io as io_facade
from nblane.core import llm
from nblane.core import git_backup
from nblane.core.file_write import atomic_write_text
from nblane.core.jsonutil import extract_json_object
from nblane.core.models import (
    CLAIM_REFRESH_STATUSES,
    CLAIM_TYPES,
    EVIDENCE_CONFIDENCES,
    EVIDENCE_PUBLIC_READINESS,
)
from nblane.core.profile_io import profile_dir
from nblane.core.yaml_io import _load_yaml_dict

CLAIMS_FILENAME = "claims.yaml"


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


def _merge_string_lists(*values: object) -> list[str]:
    out: list[str] = []
    for value in values:
        out.extend(_clean_string_list(value))
    return _clean_string_list(out)


def _profile_name(profile: str | Path) -> str:
    return profile.name if isinstance(profile, Path) else str(profile)


def _profile_path(profile: str | Path) -> Path:
    if isinstance(profile, Path):
        return profile if not profile.suffix else profile.parent
    return profile_dir(profile)


def claim_book_path(profile: str | Path) -> Path:
    """Return the profile-scoped ``claims.yaml`` path."""
    return _profile_path(profile) / CLAIMS_FILENAME


def _today() -> str:
    return date.today().isoformat()


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


def _claim_status(value: object, *, default: str = "accepted") -> str:
    clean = _clean_text(value)
    return clean if clean else default


def _claim_refresh_status(value: object) -> str:
    clean = _clean_text(value)
    return clean if clean in CLAIM_REFRESH_STATUSES else "current"


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
    """Return a stable claim mapping or ``None`` for empty text."""
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
    status = (
        "accepted"
        if force_accepted
        else _claim_status(raw.get("status"), default="draft")
    )
    created_value = _clean_text(raw.get("created")) or created or _today()
    updated_value = _clean_text(raw.get("updated")) or created_value
    history = raw.get("history")
    if not isinstance(history, list):
        history = []
    return {
        "id": claim_id,
        "status": status,
        "refresh_status": _claim_refresh_status(raw.get("refresh_status")),
        "type": claim_type,
        "text": text,
        "evidence_refs": _clean_string_list(raw.get("evidence_refs")),
        "skill_refs": _clean_string_list(raw.get("skill_refs")),
        "project_refs": _clean_string_list(raw.get("project_refs")),
        "goal_refs": _clean_string_list(raw.get("goal_refs")),
        "experience_refs": _clean_string_list(raw.get("experience_refs")),
        "source_refs": _clean_string_list(raw.get("source_refs")),
        "output_refs": _clean_string_list(raw.get("output_refs")),
        "public_readiness": public_readiness,
        "confidence": confidence,
        "rationale": _clean_text(raw.get("rationale")),
        "warnings": _clean_string_list(raw.get("warnings")),
        "generated_by": _clean_text(raw.get("generated_by")) or "rule",
        "created": created_value,
        "updated": updated_value,
        "last_reviewed": _clean_text(raw.get("last_reviewed")),
        "supporting_evidence_signature": _clean_text(
            raw.get("supporting_evidence_signature")
        ),
        "stale_reason": _clean_text(raw.get("stale_reason")),
        "history": [dict(item) for item in history if isinstance(item, dict)],
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
        "by_goal": {},
        "by_experience": {},
        "by_source": {},
        "by_output": {},
    }
    ref_fields = {
        "by_evidence": "evidence_refs",
        "by_skill": "skill_refs",
        "by_project": "project_refs",
        "by_goal": "goal_refs",
        "by_experience": "experience_refs",
        "by_source": "source_refs",
        "by_output": "output_refs",
    }
    for claim in accepted_claims(pool_raw):
        for bucket, field_name in ref_fields.items():
            for ref in _clean_string_list(claim.get(field_name)):
                usage[bucket].setdefault(ref, []).append(claim)
    return usage


def _empty_claim_book(profile: str | Path) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "profile": _profile_name(profile),
        "updated": "",
        "claims": [],
    }


def _normalize_claim_list(
    raw_claims: object,
    *,
    force_accepted: bool = False,
) -> list[dict[str, Any]]:
    if not isinstance(raw_claims, list):
        return []
    out: list[dict[str, Any]] = []
    existing_ids: set[str] = set()
    for item in raw_claims:
        if not isinstance(item, dict):
            continue
        claim = normalize_claim(
            item,
            existing_ids=existing_ids,
            force_accepted=force_accepted,
        )
        if claim is None:
            continue
        claim_id = _clean_text(claim.get("id"))
        if not claim_id:
            continue
        while claim_id in existing_ids:
            claim_id = _claim_id(claim.get("text", ""), existing_ids)
            claim["id"] = claim_id
        existing_ids.add(claim_id)
        out.append(claim)
    return out


def legacy_claims(profile: str | Path) -> list[dict[str, Any]]:
    """Return legacy claims stored under ``evidence-pool.yaml.claims``."""
    pool_raw = io_facade.load_evidence_pool_raw(profile) or {}
    return _normalize_claim_list(pool_raw.get("claims"), force_accepted=False)


def load_claim_book(profile: str | Path) -> dict[str, Any]:
    """Load profile-level claims, falling back to legacy pool claims."""
    path = claim_book_path(profile)
    raw = _load_yaml_dict(path)
    if raw is None:
        book = _empty_claim_book(profile)
        book["claims"] = legacy_claims(profile)
        return book
    book = dict(raw)
    book.setdefault("schema_version", "1.0")
    book.setdefault("profile", _profile_name(profile))
    book.setdefault("updated", "")
    book["claims"] = _normalize_claim_list(book.get("claims"), force_accepted=False)
    return book


def _load_claim_book_without_legacy(profile: str | Path) -> dict[str, Any]:
    path = claim_book_path(profile)
    raw = _load_yaml_dict(path)
    if raw is None:
        return _empty_claim_book(profile)
    book = dict(raw)
    book.setdefault("schema_version", "1.0")
    book.setdefault("profile", _profile_name(profile))
    book.setdefault("updated", "")
    book["claims"] = _normalize_claim_list(book.get("claims"), force_accepted=False)
    return book


def save_claim_book(profile: str | Path, data: dict[str, Any]) -> None:
    """Persist profile-level ``claims.yaml`` with normalized claims."""
    book = dict(data or {})
    book.setdefault("schema_version", "1.0")
    book["profile"] = _clean_text(book.get("profile")) or _profile_name(profile)
    book["updated"] = _today()
    book["claims"] = _normalize_claim_list(book.get("claims"), force_accepted=False)
    path = claim_book_path(profile)
    header = (
        f"# Claims for {book['profile']}\n"
        "# Reusable evidence-backed public assertions.\n\n"
    )
    body = yaml.dump(
        book,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    atomic_write_text(path, header + body)
    git_backup.record_change([path], action=f"update {book['profile']}/claims.yaml")


def claim_index_for_profile(profile: str | Path) -> dict[str, dict[str, Any]]:
    """Return profile claim id -> claim, reading ``claims.yaml`` first."""
    out: dict[str, dict[str, Any]] = {}
    for claim in claims_with_refresh_status(profile):
        if not isinstance(claim, dict):
            continue
        claim_id = _clean_text(claim.get("id"))
        if claim_id:
            out[claim_id] = claim
    return out


def accepted_claims_for_profile(profile: str | Path) -> list[dict[str, Any]]:
    """Return accepted claims from ``claims.yaml`` or legacy fallback."""
    return [
        dict(claim)
        for claim in claims_with_refresh_status(profile)
        if isinstance(claim, dict) and _clean_text(claim.get("status")) == "accepted"
    ]


def accepted_claim_index_for_profile(
    profile: str | Path,
) -> dict[str, dict[str, Any]]:
    """Return accepted profile claim id -> claim."""
    return {
        str(claim.get("id")): claim
        for claim in accepted_claims_for_profile(profile)
        if _clean_text(claim.get("id"))
    }


def claim_usage_index_for_profile(
    profile: str | Path,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Return accepted profile claims grouped by upstream/downstream refs."""
    usage: dict[str, dict[str, list[dict[str, Any]]]] = {
        "by_evidence": {},
        "by_skill": {},
        "by_project": {},
        "by_goal": {},
        "by_experience": {},
        "by_source": {},
        "by_output": {},
    }
    ref_fields = {
        "by_evidence": "evidence_refs",
        "by_skill": "skill_refs",
        "by_project": "project_refs",
        "by_goal": "goal_refs",
        "by_experience": "experience_refs",
        "by_source": "source_refs",
        "by_output": "output_refs",
    }
    for claim in accepted_claims_for_profile(profile):
        for bucket, field_name in ref_fields.items():
            for ref in _clean_string_list(claim.get(field_name)):
                usage[bucket].setdefault(ref, []).append(claim)
    return usage


def _write_evidence_pool_raw(profile: str | Path, pool: dict[str, Any]) -> None:
    if isinstance(profile, Path):
        path = _profile_path(profile) / "evidence-pool.yaml"
        profile_name = _profile_name(profile)
    else:
        path = profile_dir(profile) / "evidence-pool.yaml"
        profile_name = profile
    data = dict(pool or {})
    data["updated"] = _today()
    header = (
        f"# Evidence pool for {profile_name}\n"
        "# Shared records; skill-tree nodes reference ids via evidence_refs\n\n"
    )
    body = yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    atomic_write_text(path, header + body)
    git_backup.record_change([path], action=f"update {profile_name}/evidence-pool.yaml")


def migrate_legacy_claims(profile: str | Path) -> int:
    """Move legacy ``evidence-pool.yaml.claims`` into ``claims.yaml``."""
    pool_raw = io_facade.load_evidence_pool_raw(profile) or {}
    legacy = _normalize_claim_list(pool_raw.get("claims"), force_accepted=False)
    if not legacy:
        return 0
    book = _load_claim_book_without_legacy(profile)
    existing = _normalize_claim_list(book.get("claims"), force_accepted=False)
    by_key = {_claim_key(claim): idx for idx, claim in enumerate(existing)}
    existing_ids = {_clean_text(claim.get("id")) for claim in existing}
    added = 0
    for claim in legacy:
        key = _claim_key(claim)
        if key in by_key:
            continue
        claim_id = _clean_text(claim.get("id"))
        while claim_id in existing_ids:
            claim_id = _claim_id(_clean_text(claim.get("text")), existing_ids)
            claim["id"] = claim_id
        existing_ids.add(claim_id)
        existing.append(claim)
        added += 1
    book["claims"] = existing
    save_claim_book(profile, book)
    pool_without_legacy = dict(pool_raw)
    pool_without_legacy.pop("claims", None)
    _write_evidence_pool_raw(profile, pool_without_legacy)
    return added


def supporting_evidence_signature(
    profile: str | Path,
    evidence_ids: list[str],
) -> str:
    """Return a stable digest for the evidence facts supporting a claim."""
    pool_raw = io_facade.load_evidence_pool_raw(profile) or {}
    evidence = _evidence_index_from_pool(pool_raw)
    rows: list[dict[str, Any]] = []
    for evidence_id in sorted(_clean_string_list(evidence_ids)):
        row = evidence.get(evidence_id)
        if row is None:
            rows.append({"id": evidence_id, "missing": True})
            continue
        rows.append(
            {
                "id": evidence_id,
                "title": _clean_text(row.get("title")),
                "summary": _clean_text(row.get("summary")),
                "date": _clean_text(row.get("date")),
                "url": _clean_text(row.get("url")),
                "source_refs": _clean_string_list(row.get("source_refs")),
                "project_refs": _clean_string_list(row.get("project_refs")),
                "experience_refs": _clean_string_list(row.get("experience_refs")),
                "public_readiness": _clean_text(row.get("public_readiness")),
                "confidence": _clean_text(row.get("confidence")),
                "strength": _clean_text(row.get("strength")),
                "review_status": _clean_text(row.get("review_status")),
            }
        )
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _project_case_indexes(
    profile: str | Path,
) -> tuple[dict[str, Any], dict[str, set[str]], dict[str, list[str]]]:
    try:
        from nblane.core.project_board import load_project_board

        board = load_project_board(profile)
    except Exception:
        return {}, {}, {}
    cases: dict[str, Any] = {}
    evidence_by_project: dict[str, set[str]] = {}
    goals_by_project: dict[str, list[str]] = {}
    for case in getattr(board, "project_cases", []) or []:
        case_id = _clean_text(getattr(case, "id", ""))
        if not case_id:
            continue
        cases[case_id] = case
        evidence_ids = set(_clean_string_list(getattr(case, "evidence_refs", [])))
        for milestone in getattr(case, "milestones", []) or []:
            evidence_ids.update(
                _clean_string_list(getattr(milestone, "evidence_refs", []))
            )
        evidence_by_project[case_id] = evidence_ids
        goals_by_project[case_id] = _clean_string_list(getattr(case, "goal_refs", []))
    return cases, evidence_by_project, goals_by_project


def _goal_indexes(profile: str | Path) -> tuple[dict[str, Any], dict[str, set[str]]]:
    try:
        from nblane.core.goals import load_goal_book

        book = load_goal_book(profile)
    except Exception:
        return {}, {}
    goals: dict[str, Any] = {}
    evidence_by_goal: dict[str, set[str]] = {}
    for goal in getattr(book, "goals", []) or []:
        goal_id = _clean_text(getattr(goal, "id", ""))
        if not goal_id:
            continue
        goals[goal_id] = goal
        evidence_by_goal[goal_id] = set(
            _clean_string_list(getattr(goal, "evidence_refs", []))
        )
    return goals, evidence_by_goal


def _source_goals(profile: str | Path) -> dict[str, list[str]]:
    try:
        from nblane.core.research_sources import load_research_sources

        inbox = load_research_sources(profile)
    except Exception:
        return {}
    out: dict[str, list[str]] = {}
    for source in getattr(inbox, "sources", []) or []:
        source_id = _clean_text(getattr(source, "id", ""))
        if source_id:
            out[source_id] = _clean_string_list(getattr(source, "goal_refs", []))
    return out


def _derived_refs_by_evidence(
    profile: str | Path,
    evidence: dict[str, dict],
) -> dict[str, dict[str, list[str]]]:
    cases, evidence_by_project, goals_by_project = _project_case_indexes(profile)
    goals, evidence_by_goal = _goal_indexes(profile)
    source_goals = _source_goals(profile)
    out: dict[str, dict[str, list[str]]] = {}
    for evidence_id, row in evidence.items():
        project_refs = set(_clean_string_list(row.get("project_refs")))
        goal_refs: set[str] = set()
        for project_id, refs in evidence_by_project.items():
            if evidence_id in refs:
                project_refs.add(project_id)
        for project_id in list(project_refs):
            goal_refs.update(goals_by_project.get(project_id, []))
        for goal_id, refs in evidence_by_goal.items():
            if evidence_id in refs:
                goal_refs.add(goal_id)
        for source_ref in _clean_string_list(row.get("source_refs")):
            goal_refs.update(source_goals.get(source_ref, []))
        out[evidence_id] = {
            "project_refs": sorted(project_refs),
            "goal_refs": sorted(goal_refs),
        }
    return out


def _reviewed_rows(profile: str | Path) -> dict[str, dict[str, Any]]:
    pool_raw = io_facade.load_evidence_pool_raw(profile) or {}
    rows = _evidence_index_from_pool(pool_raw)
    return {
        evidence_id: row
        for evidence_id, row in rows.items()
        if not bool(row.get("deprecated", False))
        and _clean_text(row.get("review_status")) == "reviewed"
    }


def _scope_label(profile: str | Path, scope_type: str, scope_id: str) -> str:
    if scope_type == "project":
        cases, _, _ = _project_case_indexes(profile)
        case = cases.get(scope_id)
        return _clean_text(getattr(case, "title", "")) or scope_id
    if scope_type == "goal":
        goals, _ = _goal_indexes(profile)
        goal = goals.get(scope_id)
        return (
            _clean_text(getattr(goal, "title", ""))
            or _clean_text(getattr(goal, "label", ""))
            or scope_id
        )
    if scope_type == "skill":
        return scope_id
    if scope_type == "all":
        return "reviewed evidence graph"
    return "selected evidence"


def claim_scope_context(
    profile: str | Path,
    scope_type: str,
    *,
    scope_id: str = "",
    evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Return reviewed evidence and refs for one claim-generation scope."""
    scope = _clean_text(scope_type) or "manual"
    pool_raw = io_facade.load_evidence_pool_raw(profile) or {}
    all_evidence = _evidence_index_from_pool(pool_raw)
    reviewed = _reviewed_rows(profile)
    derived_refs = _derived_refs_by_evidence(profile, all_evidence)
    skill_refs = _skill_refs_by_evidence(profile)
    selected_ids: set[str] = set()
    cases, evidence_by_project, goals_by_project = _project_case_indexes(profile)
    goals, evidence_by_goal = _goal_indexes(profile)

    if scope == "manual":
        selected_ids = set(_clean_string_list(evidence_ids or []))
    elif scope == "project":
        selected_ids.update(evidence_by_project.get(scope_id, set()))
        for evidence_id, row in all_evidence.items():
            refs = set(_clean_string_list(row.get("project_refs")))
            refs.update(derived_refs.get(evidence_id, {}).get("project_refs", []))
            if scope_id in refs:
                selected_ids.add(evidence_id)
    elif scope == "goal":
        project_ids = {
            case_id
            for case_id, refs in goals_by_project.items()
            if scope_id in refs
        }
        selected_ids.update(evidence_by_goal.get(scope_id, set()))
        for evidence_id, row in all_evidence.items():
            refs = derived_refs.get(evidence_id, {})
            if scope_id in refs.get("goal_refs", []):
                selected_ids.add(evidence_id)
                continue
            if project_ids.intersection(_clean_string_list(row.get("project_refs"))):
                selected_ids.add(evidence_id)
    elif scope == "skill":
        tree = io_facade.load_skill_tree_raw(profile) or {}
        for node in tree.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            if _clean_text(node.get("id")) == scope_id:
                selected_ids.update(_clean_string_list(node.get("evidence_refs")))
                break
    elif scope == "all":
        selected_ids.update(reviewed)

    rows = [
        all_evidence[evidence_id]
        for evidence_id in sorted(selected_ids)
        if evidence_id in all_evidence
        and (
            scope == "manual"
            or evidence_id in reviewed
        )
    ]
    evidence_ref_list = [
        _clean_text(row.get("id"))
        for row in rows
        if _clean_text(row.get("id"))
    ]
    project_refs: list[str] = []
    goal_refs: list[str] = []
    source_refs: list[str] = []
    experience_refs: list[str] = []
    skill_ref_list: list[str] = []
    for row in rows:
        evidence_id = _clean_text(row.get("id"))
        refs = derived_refs.get(evidence_id, {})
        project_refs.extend(refs.get("project_refs", []))
        goal_refs.extend(refs.get("goal_refs", []))
        source_refs.extend(_clean_string_list(row.get("source_refs")))
        experience_refs.extend(_clean_string_list(row.get("experience_refs")))
        skill_ref_list.extend(skill_refs.get(evidence_id, []))
    if scope == "project" and scope_id:
        project_refs.append(scope_id)
        goal_refs.extend(goals_by_project.get(scope_id, []))
    if scope == "goal" and scope_id:
        goal_refs.append(scope_id)
    if scope == "skill" and scope_id:
        skill_ref_list.append(scope_id)
    return {
        "scope_type": scope,
        "scope_id": scope_id,
        "label": _scope_label(profile, scope, scope_id),
        "evidence_rows": rows,
        "evidence_refs": evidence_ref_list,
        "project_refs": _clean_string_list(project_refs),
        "goal_refs": _clean_string_list(goal_refs),
        "skill_refs": _clean_string_list(skill_ref_list),
        "source_refs": _clean_string_list(source_refs),
        "experience_refs": _clean_string_list(experience_refs),
        "project": cases.get(scope_id) if scope == "project" else None,
        "goal": goals.get(scope_id) if scope == "goal" else None,
    }


def _claim_type_for_scope(scope_type: str, rows: list[dict[str, Any]]) -> str:
    if scope_type == "skill":
        return "skill"
    if scope_type == "goal":
        return "achievement"
    if scope_type == "project":
        return "project"
    if len(rows) == 1:
        evidence_type = _clean_text(rows[0].get("type")) or "practice"
        return {
            "project": "achievement",
            "paper": "learning",
            "course": "learning",
            "learning": "learning",
            "practice": "skill",
        }.get(evidence_type, "achievement")
    return "achievement"


def _public_readiness_for_rows(rows: list[dict[str, Any]]) -> str:
    values = [_clean_text(row.get("public_readiness")) for row in rows]
    if any(value == "private" or not value for value in values):
        return "private"
    for candidate in ("published", "public_ready", "draftable"):
        if candidate in values:
            return candidate
    return "private"


def _confidence_for_rows(rows: list[dict[str, Any]]) -> str:
    values = [_clean_text(row.get("confidence")) for row in rows]
    if values and all(value == "high" for value in values):
        return "high"
    if any(value == "low" for value in values):
        return "low"
    return "medium"


def _candidate_text_for_scope(context: dict[str, Any]) -> str:
    rows = list(context.get("evidence_rows") or [])
    label = _clean_text(context.get("label")) or _clean_text(context.get("scope_id"))
    titles = [
        _clean_text(row.get("summary")) or _clean_text(row.get("title"))
        for row in rows
    ]
    titles = [title.rstrip(".。") for title in titles if title]
    if not titles:
        return ""
    if context.get("scope_type") == "manual" and len(titles) == 1:
        text = titles[0]
    else:
        preview = "; ".join(titles[:3])
        if len(titles) > 3:
            preview = f"{preview}; and {len(titles) - 3} more evidence item(s)"
        if context.get("scope_type") == "skill":
            text = f"Demonstrated {label} through reviewed evidence: {preview}"
        elif context.get("scope_type") == "goal":
            text = f"Advanced {label} through reviewed evidence: {preview}"
        elif context.get("scope_type") == "project":
            text = f"Built evidence-backed progress on {label}: {preview}"
        else:
            text = f"Synthesized reviewed evidence around {label}: {preview}"
    if not text.endswith((".", "。", "!", "！", "?", "？")):
        text = f"{text}."
    return text


def _ai_claim_candidates_from_scope(
    profile: str | Path,
    context: dict[str, Any],
    *,
    existing_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Return AI-drafted grounded claims, or an empty list on fallback."""
    if not llm.is_configured():
        return []
    evidence_refs = _clean_string_list(context.get("evidence_refs"))
    if not evidence_refs:
        return []
    rows = [
        {
            "id": _clean_text(row.get("id")),
            "type": _clean_text(row.get("type")),
            "title": _clean_text(row.get("title")),
            "summary": _clean_text(row.get("summary")),
            "date": _clean_text(row.get("date")),
            "source_refs": _clean_string_list(row.get("source_refs")),
            "project_refs": _clean_string_list(row.get("project_refs")),
            "experience_refs": _clean_string_list(row.get("experience_refs")),
            "public_readiness": _clean_text(row.get("public_readiness")),
            "confidence": _clean_text(row.get("confidence")),
        }
        for row in (context.get("evidence_rows") or [])
        if isinstance(row, dict)
    ]
    system = (
        "You draft evidence-backed public claims for nblane. Use only the "
        "provided evidence and scope context. Do not invent metrics, dates, "
        "employers, titles, links, outcomes, or unsupported facts. Return JSON "
        "only with a top-level claims array."
    )
    user = yaml.dump(
        {
            "scope_type": context.get("scope_type"),
            "scope_id": context.get("scope_id"),
            "scope_label": context.get("label"),
            "evidence": rows,
            "required_claim_fields": [
                "type",
                "text",
                "evidence_refs",
                "project_refs",
                "goal_refs",
                "skill_refs",
                "source_refs",
                "experience_refs",
                "public_readiness",
                "confidence",
                "rationale",
                "warnings",
            ],
        },
        allow_unicode=True,
        sort_keys=False,
    )
    reply = llm.chat(system, user, temperature=0.2)
    if reply.startswith("LLM error:") or reply.startswith("AI features not configured"):
        return []
    parsed = extract_json_object(reply) or {}
    raw_claims = parsed.get("claims")
    if not isinstance(raw_claims, list):
        return []
    allowed_evidence = set(evidence_refs)
    candidates: list[dict[str, Any]] = []
    ids = existing_ids if existing_ids is not None else set()
    for raw in raw_claims[:3]:
        if not isinstance(raw, dict):
            continue
        refs = [
            ref for ref in _clean_string_list(raw.get("evidence_refs"))
            if ref in allowed_evidence
        ]
        if not refs:
            continue
        raw = dict(raw)
        raw["evidence_refs"] = refs
        raw["project_refs"] = _merge_string_lists(
            raw.get("project_refs"),
            context.get("project_refs"),
        )
        raw["goal_refs"] = _merge_string_lists(
            raw.get("goal_refs"),
            context.get("goal_refs"),
        )
        raw["skill_refs"] = _merge_string_lists(
            raw.get("skill_refs"),
            context.get("skill_refs"),
        )
        raw["source_refs"] = _merge_string_lists(
            raw.get("source_refs"),
            context.get("source_refs"),
        )
        raw["experience_refs"] = _merge_string_lists(
            raw.get("experience_refs"),
            context.get("experience_refs"),
        )
        raw.setdefault("public_readiness", _public_readiness_for_rows(rows))
        raw.setdefault("confidence", _confidence_for_rows(rows))
        raw.setdefault("generated_by", "llm:claim_studio")
        raw.setdefault("last_reviewed", _today())
        raw["supporting_evidence_signature"] = supporting_evidence_signature(
            profile,
            refs,
        )
        candidate = normalize_claim(raw, existing_ids=ids)
        if candidate is None:
            continue
        ids.add(str(candidate.get("id")))
        candidates.append(candidate)
    return candidates


def _candidate_from_scope_context(
    profile: str | Path,
    context: dict[str, Any],
    *,
    existing_ids: set[str] | None = None,
) -> dict[str, Any] | None:
    rows = [row for row in (context.get("evidence_rows") or []) if isinstance(row, dict)]
    evidence_refs = _clean_string_list(context.get("evidence_refs"))
    if not rows or not evidence_refs:
        return None
    text = _candidate_text_for_scope(context)
    if not text:
        return None
    candidate = normalize_claim(
        {
            "type": _claim_type_for_scope(_clean_text(context.get("scope_type")), rows),
            "text": text,
            "evidence_refs": evidence_refs,
            "skill_refs": context.get("skill_refs") or [],
            "project_refs": context.get("project_refs") or [],
            "goal_refs": context.get("goal_refs") or [],
            "experience_refs": context.get("experience_refs") or [],
            "source_refs": context.get("source_refs") or [],
            "public_readiness": _public_readiness_for_rows(rows),
            "confidence": _confidence_for_rows(rows),
            "rationale": (
                f"Derived from {context.get('scope_type')} scope "
                f"{context.get('scope_id') or context.get('label')}."
            ),
            "warnings": [
                "Review wording before using this claim in skill or public output.",
            ],
            "generated_by": "rule:claim_studio",
            "supporting_evidence_signature": supporting_evidence_signature(
                profile,
                evidence_refs,
            ),
            "last_reviewed": _today(),
        },
        existing_ids=existing_ids or set(),
    )
    return candidate


def generate_claim_candidates_for_scope(
    profile: str | Path,
    scope_type: str,
    *,
    scope_id: str = "",
    evidence_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Generate deterministic claim candidates from one reviewed graph scope."""
    scope = _clean_text(scope_type) or "manual"
    if scope == "manual":
        return generate_claim_candidates(profile, evidence_ids or [])
    if scope == "all":
        candidates: list[dict[str, Any]] = []
        existing_ids: set[str] = set()
        cases, _, _ = _project_case_indexes(profile)
        for project_id in sorted(cases):
            context = claim_scope_context(profile, "project", scope_id=project_id)
            ai_candidates = _ai_claim_candidates_from_scope(
                profile,
                context,
                existing_ids=existing_ids,
            )
            if ai_candidates:
                candidates.extend(ai_candidates)
                existing_ids.update(str(item.get("id")) for item in ai_candidates)
                continue
            candidate = _candidate_from_scope_context(
                profile,
                context,
                existing_ids=existing_ids,
            )
            if candidate is not None:
                existing_ids.add(str(candidate.get("id")))
                candidates.append(candidate)
        if not candidates:
            context = claim_scope_context(profile, "all")
            ai_candidates = _ai_claim_candidates_from_scope(
                profile,
                context,
                existing_ids=existing_ids,
            )
            if ai_candidates:
                return ai_candidates
            candidate = _candidate_from_scope_context(
                profile,
                context,
                existing_ids=existing_ids,
            )
            if candidate is not None:
                candidates.append(candidate)
        return candidates
    context = claim_scope_context(
        profile,
        scope,
        scope_id=scope_id,
        evidence_ids=evidence_ids,
    )
    ai_candidates = _ai_claim_candidates_from_scope(profile, context)
    if ai_candidates:
        return ai_candidates
    candidate = _candidate_from_scope_context(profile, context)
    return [candidate] if candidate is not None else []


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
    derived_refs = _derived_refs_by_evidence(profile, evidence)
    skill_refs = _skill_refs_by_evidence(profile)
    candidates: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
    for evidence_id in _clean_string_list(evidence_ids):
        row = evidence.get(evidence_id)
        if row is None:
            continue
        title = _clean_text(row.get("title")) or evidence_id
        refs = derived_refs.get(evidence_id, {})
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
                "project_refs": refs.get("project_refs") or row.get("project_refs") or [],
                "goal_refs": refs.get("goal_refs") or [],
                "experience_refs": row.get("experience_refs") or [],
                "source_refs": row.get("source_refs") or [],
                "public_readiness": row.get("public_readiness") or "private",
                "confidence": row.get("confidence") or "medium",
                "rationale": f"Derived from evidence {evidence_id}: {title}",
                "warnings": [
                    "Review wording before using this claim in skill or public output.",
                ],
                "generated_by": "rule:evidence_review",
                "supporting_evidence_signature": supporting_evidence_signature(
                    profile,
                    [evidence_id],
                ),
                "last_reviewed": _today(),
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


def _claim_history_entry(claim: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": _clean_text(claim.get("text")),
        "evidence_refs": _clean_string_list(claim.get("evidence_refs")),
        "project_refs": _clean_string_list(claim.get("project_refs")),
        "goal_refs": _clean_string_list(claim.get("goal_refs")),
        "skill_refs": _clean_string_list(claim.get("skill_refs")),
        "updated": _clean_text(claim.get("updated")),
        "captured": _today(),
    }


def apply_claim_candidates_to_book(
    profile: str | Path,
    candidates: list[dict[str, Any]],
    *,
    known_skill_ids: set[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    """Apply selected candidates into profile ``claims.yaml``."""
    if legacy_claims(profile):
        migrate_legacy_claims(profile)
    book = _load_claim_book_without_legacy(profile)
    pool_raw = io_facade.load_evidence_pool_raw(profile) or {}
    evidence_ids = set(_evidence_index_from_pool(pool_raw))
    skill_ids = known_skill_ids if known_skill_ids is not None else set()
    existing_claims = _normalize_claim_list(book.get("claims"), force_accepted=False)
    existing_ids = {_clean_text(claim.get("id")) for claim in existing_claims}
    by_key = {_claim_key(claim): index for index, claim in enumerate(existing_claims)}
    by_id = {
        _clean_text(claim.get("id")): index
        for index, claim in enumerate(existing_claims)
        if _clean_text(claim.get("id"))
    }
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
        normalized["status"] = "accepted"
        normalized["refresh_status"] = "current"
        normalized["stale_reason"] = ""
        normalized["updated"] = _today()
        normalized["last_reviewed"] = _today()
        if not normalized.get("supporting_evidence_signature"):
            normalized["supporting_evidence_signature"] = supporting_evidence_signature(
                profile,
                normalized["evidence_refs"],
            )
        key = _claim_key(normalized)
        claim_id = _clean_text(normalized.get("id"))
        target_index = by_id.get(claim_id)
        if target_index is None and key in by_key:
            target_index = by_key[key]
        if target_index is not None:
            existing = existing_claims[target_index]
            normalized["id"] = _clean_text(existing.get("id")) or claim_id
            normalized["created"] = _clean_text(existing.get("created")) or normalized["created"]
            history = list(existing.get("history") or [])
            if (
                _clean_text(existing.get("text")) != normalized["text"]
                or _clean_string_list(existing.get("evidence_refs"))
                != normalized["evidence_refs"]
            ):
                history.append(_claim_history_entry(existing))
            normalized["history"] = [
                dict(item) for item in history if isinstance(item, dict)
            ]
            existing_claims[target_index] = normalized
        else:
            while normalized["id"] in existing_ids:
                normalized["id"] = _claim_id(normalized["text"], existing_ids)
            existing_ids.add(str(normalized["id"]))
            by_id[str(normalized["id"])] = len(existing_claims)
            by_key[key] = len(existing_claims)
            existing_claims.append(normalized)
        applied.append(normalized)

    book["claims"] = existing_claims
    save_claim_book(profile, book)
    return book, applied, warnings


def claims_with_refresh_status(profile: str | Path) -> list[dict[str, Any]]:
    """Return claims with computed refresh status, without writing."""
    out: list[dict[str, Any]] = []
    for claim in load_claim_book(profile).get("claims") or []:
        if not isinstance(claim, dict):
            continue
        item = dict(claim)
        refs = _clean_string_list(item.get("evidence_refs"))
        if refs and item.get("status") == "accepted":
            current = supporting_evidence_signature(profile, refs)
            stored = _clean_text(item.get("supporting_evidence_signature"))
            if stored and stored != current:
                item["refresh_status"] = "needs_refresh"
                item["stale_reason"] = "Supporting evidence changed since last review."
            elif not stored:
                item["supporting_evidence_signature"] = current
        out.append(item)
    return out


def refresh_claim_statuses(profile: str | Path) -> list[dict[str, Any]]:
    """Persist computed ``needs_refresh`` statuses for accepted claims."""
    book = _load_claim_book_without_legacy(profile)
    if not book.get("claims") and legacy_claims(profile):
        book["claims"] = legacy_claims(profile)
    claims = claims_with_refresh_status(profile)
    book["claims"] = claims
    save_claim_book(profile, book)
    return claims


__all__ = [
    "CLAIMS_FILENAME",
    "accepted_claim_index",
    "accepted_claim_index_for_profile",
    "accepted_claims",
    "accepted_claims_for_profile",
    "apply_claim_candidates",
    "apply_claim_candidates_to_book",
    "claim_book_path",
    "claim_index",
    "claim_index_for_profile",
    "claim_scope_context",
    "claim_usage_index",
    "claim_usage_index_for_profile",
    "claims_with_refresh_status",
    "generate_claim_candidates",
    "generate_claim_candidates_for_scope",
    "legacy_claims",
    "load_claim_book",
    "migrate_legacy_claims",
    "refresh_claim_statuses",
    "save_claim_book",
    "supporting_evidence_signature",
]
