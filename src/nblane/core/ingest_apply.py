"""Disk apply and validation flow for profile ingest merges."""

from __future__ import annotations

from contextlib import nullcontext

from nblane.core.file_lock import locked_profile_files
from nblane.core.file_write import profile_file_transaction

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


_INGEST_FILES = ("evidence-pool.yaml", "skill-tree.yaml", "SKILL.md")


class _InvalidMergedProfile(ValueError):
    """Carry validation errors out through the transaction rollback boundary."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def apply_merged_profile(
    profile_name: str,
    merged_pool: dict,
    merged_tree: dict,
    *,
    dry_run: bool = False,
) -> ApplyOutcome:
    """Write pool + tree, validate, sync SKILL.md; rollback on error."""
    pdir = profile_dir(profile_name)

    if dry_run:
        return ApplyOutcome(ok=True, warnings=[], dry_run=True)

    from nblane.core.sync import write_generated_blocks

    warnings: list[str] = []
    try:
        with profile_file_transaction(pdir, _INGEST_FILES):
            save_evidence_pool(profile_name, merged_pool)
            save_skill_tree(profile_name, merged_tree)
            errors, warnings = validate_one(pdir, check_sync=False)
            if errors:
                raise _InvalidMergedProfile(list(errors))
            if (pdir / "SKILL.md").exists():
                write_generated_blocks(pdir)
            else:
                warnings = [*warnings, "SKILL.md missing; skipped sync write_generated_blocks"]
    except (OSError, ValueError) as exc:
        errors = exc.errors if isinstance(exc, _InvalidMergedProfile) else [str(exc)]
        return ApplyOutcome(ok=False, errors=errors, warnings=list(warnings), dry_run=False)
    return ApplyOutcome(ok=True, warnings=list(warnings), dry_run=False)


def run_ingest_patch(
    profile_name: str,
    patch: IngestPatch | dict,
    *,
    allow_status_change: bool = False,
    bump_locked_with_evidence: bool = True,
    match_task_sources: bool = False,
    dry_run: bool = False,
) -> tuple[MergeOutcome, ApplyOutcome]:
    """Load current YAML, merge *patch*, optionally write + validate + sync."""
    guard = nullcontext() if dry_run else locked_profile_files(profile_dir(profile_name), _INGEST_FILES)
    with guard:
        return _run_ingest_patch_locked(
            profile_name, patch, allow_status_change=allow_status_change,
            bump_locked_with_evidence=bump_locked_with_evidence,
            match_task_sources=match_task_sources, dry_run=dry_run,
        )


def _run_ingest_patch_locked(
    profile_name: str,
    patch: IngestPatch | dict,
    *,
    allow_status_change: bool,
    bump_locked_with_evidence: bool,
    match_task_sources: bool,
    dry_run: bool,
) -> tuple[MergeOutcome, ApplyOutcome]:
    """Keep merge inputs protected until the corresponding apply completes."""
    pool_raw = load_evidence_pool_raw(profile_name)
    tree_raw = load_skill_tree_raw(profile_name)
    merge = merge_ingest_patch(
        profile_name,
        pool_raw,
        tree_raw,
        patch,
        allow_status_change=allow_status_change,
        bump_locked_with_evidence=bump_locked_with_evidence,
        match_task_sources=match_task_sources,
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
