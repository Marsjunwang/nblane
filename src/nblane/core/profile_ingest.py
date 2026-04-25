"""Compatibility facade for profile ingest operations."""

from __future__ import annotations

from datetime import date

from nblane.core import ingest_apply, ingest_merge
from nblane.core.ingest_apply import apply_merged_profile
from nblane.core.ingest_models import (
    ApplyOutcome,
    IngestPatch,
    MergeOutcome,
)
from nblane.core.ingest_parse import (
    _llm_status_effective,
    _normalize_evidence_row,
    _ordinal_placeholder_to_id,
    _status_rank,
    filter_ingest_patch,
    parse_ingest_patch,
)
from nblane.core.ingest_preview import (
    ingest_preview_delta,
    pool_tree_summaries_for_prompt,
    schema_node_labels,
)


def _sync_legacy_date() -> None:
    """Keep old ``nblane.core.profile_ingest.date`` patch points working."""
    ingest_merge.date = date


def merge_ingest_patch(
    profile_name: str,
    pool_raw: dict | None,
    tree_raw: dict | None,
    patch: IngestPatch | dict,
    *,
    allow_status_change: bool = False,
    bump_locked_with_evidence: bool = True,
) -> MergeOutcome:
    """Merge patch into pool then tree (memory only)."""
    _sync_legacy_date()
    return ingest_merge.merge_ingest_patch(
        profile_name,
        pool_raw,
        tree_raw,
        patch,
        allow_status_change=allow_status_change,
        bump_locked_with_evidence=bump_locked_with_evidence,
    )


def run_ingest_patch(
    profile_name: str,
    patch: IngestPatch | dict,
    *,
    allow_status_change: bool = False,
    bump_locked_with_evidence: bool = True,
    dry_run: bool = False,
) -> tuple[MergeOutcome, ApplyOutcome]:
    """Load current YAML, merge *patch*, optionally write + validate + sync."""
    _sync_legacy_date()
    return ingest_apply.run_ingest_patch(
        profile_name,
        patch,
        allow_status_change=allow_status_change,
        bump_locked_with_evidence=bump_locked_with_evidence,
        dry_run=dry_run,
    )


__all__ = [
    "ApplyOutcome",
    "IngestPatch",
    "MergeOutcome",
    "_llm_status_effective",
    "_normalize_evidence_row",
    "_ordinal_placeholder_to_id",
    "_status_rank",
    "apply_merged_profile",
    "filter_ingest_patch",
    "ingest_preview_delta",
    "merge_ingest_patch",
    "parse_ingest_patch",
    "pool_tree_summaries_for_prompt",
    "run_ingest_patch",
    "schema_node_labels",
]
