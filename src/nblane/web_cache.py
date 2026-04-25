"""Streamlit-only cached wrappers around core file I/O."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar

from nblane.core import io
from nblane.core.paths import SCHEMAS_DIR, TEAMS_DIR

try:
    import streamlit as st
except ImportError:  # pragma: no cover - Streamlit is a web dependency.
    st = None  # type: ignore[assignment]

_T = TypeVar("_T")


def _streamlit_runtime_exists() -> bool:
    """Return True only inside an active Streamlit runtime."""
    if st is None:
        return False
    runtime = getattr(st, "runtime", None)
    exists = getattr(runtime, "exists", None)
    if exists is None:
        return False
    try:
        return bool(exists())
    except Exception:
        return False


def _mtime_ns(path: Path) -> int:
    """Use file mtime as the cache key segment for YAML/Markdown reads."""
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return -1


def _profile_path(name_or_dir: str | Path, filename: str) -> Path:
    if isinstance(name_or_dir, Path):
        return name_or_dir / filename
    return io.profile_dir(name_or_dir) / filename


def _cached_data(func: Callable[..., _T]) -> Callable[..., _T]:
    if not _streamlit_runtime_exists():
        return func
    return st.cache_data(ttl=60)(func)


@_cached_data
def _cached_load_skill_tree_raw(
    name_or_dir: str | Path,
    mtime_ns: int,
) -> dict | None:
    return io.load_skill_tree_raw(name_or_dir)


@_cached_data
def _cached_load_evidence_pool_raw(
    name_or_dir: str | Path,
    mtime_ns: int,
) -> dict | None:
    return io.load_evidence_pool_raw(name_or_dir)


@_cached_data
def _cached_load_schema_raw(
    schema_name: str,
    mtime_ns: int,
) -> dict | None:
    return io.load_schema_raw(schema_name)


@_cached_data
def _cached_load_skill_md(
    name: str,
    mtime_ns: int,
) -> str:
    return io.load_skill_md(name)


@_cached_data
def _cached_load_team(
    team_id: str,
    mtime_ns: int,
) -> dict | None:
    return io.load_team(team_id)


@_cached_data
def _cached_load_product_pool(
    team_id: str,
    mtime_ns: int,
) -> dict | None:
    return io.load_product_pool(team_id)


def load_skill_tree_raw(name_or_dir: str | Path) -> dict | None:
    """Load skill-tree.yaml with Streamlit cache when available."""
    if not _streamlit_runtime_exists():
        return io.load_skill_tree_raw(name_or_dir)
    path = _profile_path(name_or_dir, io.SKILL_TREE_FILENAME)
    return _cached_load_skill_tree_raw(name_or_dir, _mtime_ns(path))


def load_evidence_pool_raw(name_or_dir: str | Path) -> dict | None:
    """Load evidence-pool.yaml with Streamlit cache when available."""
    if not _streamlit_runtime_exists():
        return io.load_evidence_pool_raw(name_or_dir)
    path = _profile_path(name_or_dir, io.EVIDENCE_POOL_FILENAME)
    return _cached_load_evidence_pool_raw(name_or_dir, _mtime_ns(path))


def load_schema_raw(schema_name: str) -> dict | None:
    """Load schema YAML with Streamlit cache when available."""
    if not _streamlit_runtime_exists():
        return io.load_schema_raw(schema_name)
    path = SCHEMAS_DIR / f"{schema_name}.yaml"
    return _cached_load_schema_raw(schema_name, _mtime_ns(path))


def load_skill_md(name: str) -> str:
    """Load SKILL.md with Streamlit cache when available."""
    if not _streamlit_runtime_exists():
        return io.load_skill_md(name)
    path = io.profile_dir(name) / "SKILL.md"
    return _cached_load_skill_md(name, _mtime_ns(path))


def load_team(team_id: str) -> dict | None:
    """Load team.yaml with Streamlit cache when available."""
    if not _streamlit_runtime_exists():
        return io.load_team(team_id)
    path = TEAMS_DIR / team_id / "team.yaml"
    return _cached_load_team(team_id, _mtime_ns(path))


def load_product_pool(team_id: str) -> dict | None:
    """Load product-pool.yaml with Streamlit cache when available."""
    if not _streamlit_runtime_exists():
        return io.load_product_pool(team_id)
    path = TEAMS_DIR / team_id / "product-pool.yaml"
    return _cached_load_product_pool(team_id, _mtime_ns(path))


def clear_web_cache() -> None:
    """Clear Streamlit data cache after web writes."""
    if _streamlit_runtime_exists():
        st.cache_data.clear()
