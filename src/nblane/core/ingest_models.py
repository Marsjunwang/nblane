"""Data containers for profile ingest operations."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IngestPatch:
    """Normalized ingest payload (evidence rows + per-node updates)."""

    evidence_entries: list[dict] = field(default_factory=list)
    node_updates: list[dict] = field(default_factory=list)


@dataclass
class MergeOutcome:
    """Result of in-memory merge (no disk write)."""

    ok: bool
    merged_pool: dict | None
    merged_tree: dict | None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class ApplyOutcome:
    """Result after optional disk write, validate, sync."""

    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    dry_run: bool = False
