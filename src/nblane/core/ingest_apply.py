"""Disk apply and validation flow for profile ingest merges."""

from __future__ import annotations

from pathlib import Path

from nblane.core.ingest_merge import merge_ingest_patch
from nblane.core.ingest_models import ApplyOutcome, IngestPatch, MergeOutcome
from nblane.core.io import (
    load_evidence_pool_raw,
    load_skill_tree_raw,
    profile_dir,
    save_evidence_pool,
    save_skill_tree,
)
from nblane.core.validate import validate_one


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
