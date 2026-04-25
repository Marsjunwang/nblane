"""Shared helpers for CLI command handlers."""

from __future__ import annotations

import sys
from pathlib import Path

from nblane.core.paths import PROFILES_DIR


def _profile_dir(name: str) -> Path:
    """Return the profile directory path."""
    return PROFILES_DIR / name


def _require_profile(name: str) -> Path:
    """Return profile dir, exit if not found."""
    d = _profile_dir(name)
    if not d.exists():
        print(
            f"Profile '{name}' not found. "
            f"Run: nblane init {name}",
            file=sys.stderr,
        )
        sys.exit(1)
    return d


# -- commands ---------------------------------------------------------------
