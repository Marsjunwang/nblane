"""Canonical path constants for the nblane repository."""

from __future__ import annotations

import os
from pathlib import Path


def _detect_repo_root() -> Path:
    """Locate the nblane repository root directory.

    Resolution order:
    1. ``NBLANE_ROOT`` environment variable (explicit override).
    2. Walk up from this file looking for a ``profiles/`` directory.
    3. Fall back to the current working directory.
    """
    env_root = os.getenv("NBLANE_ROOT")
    if env_root:
        return Path(env_root).resolve()

    candidate = Path(__file__).resolve()
    for _ in range(6):
        candidate = candidate.parent
        if (candidate / "profiles").is_dir():
            return candidate

    return Path.cwd()


REPO_ROOT: Path = _detect_repo_root()
PROFILES_DIR: Path = REPO_ROOT / "profiles"
SCHEMAS_DIR: Path = REPO_ROOT / "schemas"
TEAMS_DIR: Path = REPO_ROOT / "teams"
TEMPLATE_DIR: Path = PROFILES_DIR / "template"
