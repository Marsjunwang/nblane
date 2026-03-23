"""Validate skill-tree.yaml against the referenced domain schema."""

from __future__ import annotations

import sys
from pathlib import Path

from nblane.core.io import (
    load_evidence_pool,
    load_schema_raw,
    load_skill_tree_raw,
    schema_node_index,
)
from nblane.core.models import EVIDENCE_TYPES
from nblane.core.paths import PROFILES_DIR

ALLOWED_STATUS = frozenset(
    {"expert", "solid", "learning", "locked"}
)


def validate_one(
    profile_dir: Path,
    check_sync: bool = False,
) -> tuple[list[str], list[str]]:
    """Validate one profile directory.

    Returns (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    name = profile_dir.name
    tree = load_skill_tree_raw(profile_dir)
    if tree is None:
        errors.append(f"[{name}] skill-tree.yaml missing")
        return errors, warnings

    schema_name = tree.get("schema")
    if schema_name is None or schema_name == "":
        errors.append(
            f"[{name}] skill-tree.yaml: "
            "'schema' is required"
        )
        return errors, warnings

    schema_data = load_schema_raw(schema_name)
    if schema_data is None:
        errors.append(
            f"[{name}] schema file not found: "
            f"schemas/{schema_name}.yaml"
        )
        return errors, warnings

    index = schema_node_index(schema_data)
    pool = load_evidence_pool(profile_dir)
    pool_ids: set[str] = (
        set(pool.by_id().keys()) if pool is not None else set()
    )
    pool_missing = pool is None

    for node in tree.get("nodes") or []:
        nid = node.get("id")
        if nid is None:
            errors.append(
                f"[{name}] node entry missing 'id'"
            )
            continue
        if nid not in index:
            errors.append(
                f"[{name}] unknown node id "
                f"(not in schema): {nid}"
            )
        st = node.get("status", "locked")
        if st not in ALLOWED_STATUS:
            errors.append(
                f"[{name}] invalid status for "
                f"{nid}: {st!r}"
            )

    for node in tree.get("nodes") or []:
        nid = node.get("id")
        if nid is None or nid not in index:
            continue
        st = node.get("status", "locked")
        if st not in ("solid", "expert"):
            continue
        prereqs = index[nid].get("requires") or []
        for r in prereqs:
            r_entry = next(
                (
                    x
                    for x in tree.get("nodes") or []
                    if x.get("id") == r
                ),
                None,
            )
            r_st = (
                r_entry.get("status", "locked")
                if r_entry
                else "locked"
            )
            if r_st in ("locked", "learning"):
                warnings.append(
                    f"[{name}] {nid} is {st} but "
                    f"prerequisite {r} is {r_st}"
                )

    for node in tree.get("nodes") or []:
        nid = node.get("id")
        if nid is None:
            continue
        raw_refs = node.get("evidence_refs") or []
        if raw_refs is not None and not isinstance(raw_refs, list):
            errors.append(
                f"[{name}] {nid}: "
                f"'evidence_refs' must be a list"
            )
        elif isinstance(raw_refs, list):
            non_empty = [
                r for r in raw_refs
                if isinstance(r, str) and r.strip()
            ]
            if non_empty and pool_missing:
                errors.append(
                    f"[{name}] {nid}: evidence_refs set but "
                    f"evidence-pool.yaml is missing"
                )
            elif not pool_missing:
                for j, rid in enumerate(raw_refs):
                    if not isinstance(rid, str) or not rid.strip():
                        warnings.append(
                            f"[{name}] {nid} evidence_refs[{j}]: "
                            f"expected non-empty string"
                        )
                        continue
                    key = rid.strip()
                    if key not in pool_ids:
                        errors.append(
                            f"[{name}] {nid}: evidence_refs "
                            f"unknown id {key!r} "
                            f"(not in evidence-pool.yaml)"
                        )

        raw_ev = node.get("evidence") or []
        if not isinstance(raw_ev, list):
            warnings.append(
                f"[{name}] {nid}: "
                f"'evidence' should be a list"
            )
            continue
        for j, ev in enumerate(raw_ev):
            if not isinstance(ev, dict):
                warnings.append(
                    f"[{name}] {nid} evidence[{j}]: "
                    f"expected a mapping"
                )
                continue
            et = ev.get("type", "")
            if et not in EVIDENCE_TYPES:
                warnings.append(
                    f"[{name}] {nid} evidence[{j}]: "
                    f"unknown type {et!r} "
                    f"(expected one of {sorted(EVIDENCE_TYPES)})"
                )
            title = ev.get("title", "")
            if not str(title).strip():
                warnings.append(
                    f"[{name}] {nid} evidence[{j}]: "
                    f"empty title"
                )

    if check_sync:
        from nblane.core.sync import get_drifted_blocks

        try:
            drifted = get_drifted_blocks(profile_dir)
            if drifted:
                joined = ", ".join(drifted)
                errors.append(
                    f"[{name}] generated section drift "
                    f"in SKILL.md: {joined}"
                )
        except ValueError as exc:
            errors.append(
                f"[{name}] sync check failed: {exc}"
            )

    return errors, warnings


def run_all_profiles(
    check_sync: bool = False,
) -> tuple[list[str], list[str]]:
    """Validate every profile under profiles/ except template.

    Returns (all_errors, all_warnings).
    """
    dirs = sorted(
        d
        for d in PROFILES_DIR.iterdir()
        if d.is_dir() and d.name != "template"
    )
    all_errors: list[str] = []
    all_warnings: list[str] = []
    for d in dirs:
        if not (d / "SKILL.md").exists():
            continue
        err, warn = validate_one(d, check_sync=check_sync)
        all_errors.extend(err)
        all_warnings.extend(warn)
    return all_errors, all_warnings


def print_results(
    errors: list[str],
    warnings: list[str],
) -> int:
    """Print messages and return 0 if no errors."""
    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors:
        print(
            f"\nValidation failed: {len(errors)} error(s).",
            file=sys.stderr,
        )
        return 1
    if warnings:
        print(f"\nOK with {len(warnings)} warning(s).")
    else:
        print("OK.")
    return 0
