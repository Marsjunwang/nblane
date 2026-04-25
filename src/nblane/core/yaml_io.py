"""Small YAML loading helpers shared by file I/O modules."""

from __future__ import annotations

from pathlib import Path

import yaml


def _load_yaml_file(path: Path) -> object | None:
    """Load YAML from *path*, returning None when the file is absent or empty."""
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_yaml_dict(path: Path) -> dict | None:
    """Load YAML from *path* only when the document is a mapping."""
    raw = _load_yaml_file(path)
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return None
    return raw
