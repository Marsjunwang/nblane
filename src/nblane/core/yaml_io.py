"""Small YAML loading helpers shared by file I/O modules."""

from __future__ import annotations

import copy
import threading
from pathlib import Path
from typing import IO, Any

import yaml

_FastLoader: type[yaml.SafeLoader] = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

# path -> ((st_ino, st_mtime_ns, st_size), parsed mapping)
_CACHED_DICTS: dict[str, tuple[tuple[int, int, int], dict]] = {}
_CACHED_DICTS_LOCK = threading.Lock()
_CACHED_DICTS_MAX = 64


def fast_safe_load(stream: str | bytes | IO[str] | IO[bytes]) -> Any:
    """Drop-in faster ``yaml.safe_load`` using ``CSafeLoader`` when available."""
    return yaml.load(stream, Loader=_FastLoader)


def _load_yaml_file(path: Path) -> object | None:
    """Load YAML from *path*, returning None when the file is absent or empty."""
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return fast_safe_load(f)


def _load_yaml_dict(path: Path) -> dict | None:
    """Load YAML from *path* only when the document is a mapping."""
    raw = _load_yaml_file(path)
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return None
    return raw


def load_yaml_dict_cached(path: Path) -> dict | None:
    """Like ``_load_yaml_dict`` but reuse the parse while the file is unchanged.

    Large hot files (``research/sources.yaml`` is hundreds of KB) are read
    several times per request. The cache key is the file identity (inode,
    mtime, size), so atomic replace-writes always invalidate it. Callers get
    a deep copy and may mutate it freely.
    """
    try:
        stat = path.stat()
    except OSError:
        return None
    key = str(path)
    signature = (stat.st_ino, stat.st_mtime_ns, stat.st_size)
    with _CACHED_DICTS_LOCK:
        hit = _CACHED_DICTS.get(key)
    if hit is not None and hit[0] == signature:
        return copy.deepcopy(hit[1])
    raw = _load_yaml_dict(path)
    if raw is None:
        return None
    with _CACHED_DICTS_LOCK:
        if len(_CACHED_DICTS) >= _CACHED_DICTS_MAX:
            _CACHED_DICTS.clear()
        _CACHED_DICTS[key] = (signature, raw)
    return copy.deepcopy(raw)
