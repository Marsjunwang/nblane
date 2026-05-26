"""Per-render context carrying the bound profile/UI globals."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResearchContext:
    """Container for the page-level globals consumed by render helpers."""

    selected: str
    pdir: Path
    ui: dict
    user: Any
    sources_path: Path
    research_claims_path: Path
    research_citations_path: Path
    research_connectors_path: Path
