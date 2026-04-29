"""Shared helpers for CLI command handlers."""

from __future__ import annotations

import sys
from pathlib import Path

from nblane.core.profile_io import safe_profile_dir


def _profile_dir(name: str) -> Path:
    """Return the profile directory path."""
    try:
        return safe_profile_dir(name)
    except ValueError as exc:
        print(f"Invalid profile name: {exc}", file=sys.stderr)
        sys.exit(1)


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
