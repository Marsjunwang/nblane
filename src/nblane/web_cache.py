"""Streamlit-only cached wrappers around core file I/O."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, TypeVar

from nblane.core import io
from nblane.core.paths import SCHEMAS_DIR, TEAMS_DIR

try:
    import streamlit as st
except ImportError:  # pragma: no cover - Streamlit is a web dependency.
    st = SimpleNamespace()  # type: ignore[assignment]

if st is not None and not hasattr(st, "cache_data"):
    st.cache_data = SimpleNamespace(  # type: ignore[attr-defined]
        clear=lambda: None,
    )

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
def _cached_load_goal_book_raw(
    name_or_dir: str | Path,
    mtime_ns: int,
) -> dict:
    return io.load_goal_book_raw(name_or_dir)


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


def load_goal_book_raw(name_or_dir: str | Path) -> dict:
    """Load goals.yaml with Streamlit cache when available."""
    if not _streamlit_runtime_exists():
        return io.load_goal_book_raw(name_or_dir)
    path = _profile_path(name_or_dir, io.GOALS_FILENAME)
    return _cached_load_goal_book_raw(name_or_dir, _mtime_ns(path))


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


# ---------------------------------------------------------------------------
# Research workspace loaders.
#
# Streamlit pages call these on every rerun. Caching them with mtime-keyed
# invalidation removes redundant YAML/JSONL parse cost without changing
# semantics: writers call ``clear_web_cache()`` after persisting, and the
# mtime delta also forces a refresh.
# ---------------------------------------------------------------------------


def _research_root(name_or_dir: str | Path) -> Path:
    if isinstance(name_or_dir, Path):
        return name_or_dir / "research"
    return io.profile_dir(name_or_dir) / "research"


def _research_file(name_or_dir: str | Path, *parts: str) -> Path:
    return _research_root(name_or_dir).joinpath(*parts)


@_cached_data
def _cached_load_research_sources(
    name_or_dir: str | Path,
    mtime_ns: int,
) -> Any:
    from nblane.core.research_sources import load_research_sources as _impl
    return _impl(name_or_dir)


@_cached_data
def _cached_load_research_claims(
    name_or_dir: str | Path,
    mtime_ns: int,
) -> Any:
    from nblane.core.research_workspace import load_research_claims as _impl
    return _impl(name_or_dir)


@_cached_data
def _cached_load_research_citations(
    name_or_dir: str | Path,
    mtime_ns: int,
) -> Any:
    from nblane.core.research_workspace import load_research_citations as _impl
    return _impl(name_or_dir)


@_cached_data
def _cached_load_research_drafts(
    name_or_dir: str | Path,
    mtime_ns: int,
) -> Any:
    from nblane.core.research_workspace import load_research_drafts as _impl
    return _impl(name_or_dir)


@_cached_data
def _cached_load_chunks(
    name_or_dir: str | Path,
    source_id: str,
    mtime_ns: int,
    dir_mtime_ns: int,
) -> Any:
    from nblane.core.research_workspace import load_chunks as _impl
    return _impl(name_or_dir, source_id)


@_cached_data
def _cached_load_connectors(
    name_or_dir: str | Path,
    mtime_ns: int,
) -> Any:
    from nblane.core.research_connectors import load_connectors as _impl
    return _impl(name_or_dir)


@_cached_data
def _cached_load_paper_pages(
    name_or_dir: str | Path,
    source_id: str,
    mtime_ns: int,
) -> Any:
    from nblane.core.research_papers import load_paper_pages as _impl
    return _impl(name_or_dir, source_id)


@_cached_data
def _cached_load_paper_segments(
    name_or_dir: str | Path,
    source_id: str,
    mtime_ns: int,
) -> Any:
    from nblane.core.research_papers import load_paper_segments as _impl
    return _impl(name_or_dir, source_id)


@_cached_data
def _cached_load_paper_annotations(
    name_or_dir: str | Path,
    source_id: str,
    mtime_ns: int,
) -> Any:
    from nblane.core.research_papers import load_paper_annotations as _impl
    return _impl(name_or_dir, source_id)


@_cached_data
def _cached_load_paper_translations(
    name_or_dir: str | Path,
    source_id: str,
    mtime_ns: int,
) -> Any:
    from nblane.core.research_papers import load_paper_translations as _impl
    return _impl(name_or_dir, source_id)


@_cached_data
def _cached_load_paper_library_tree(
    name_or_dir: str | Path,
    mtime_ns: int,
) -> Any:
    from nblane.core.research_papers import load_paper_library_tree as _impl
    return _impl(name_or_dir)


def _source_slug(source_id: str) -> str:
    from nblane.core.research_sources import source_slug
    return source_slug(source_id)


def load_research_sources(name_or_dir: str | Path) -> Any:
    """Load research/sources.yaml with Streamlit cache when available."""
    from nblane.core.research_sources import load_research_sources as _impl
    if not _streamlit_runtime_exists():
        return _impl(name_or_dir)
    path = _research_file(name_or_dir, "sources.yaml")
    return _cached_load_research_sources(name_or_dir, _mtime_ns(path))


def load_research_claims(name_or_dir: str | Path) -> Any:
    """Load research/claims.yaml with Streamlit cache when available."""
    from nblane.core.research_workspace import load_research_claims as _impl
    if not _streamlit_runtime_exists():
        return _impl(name_or_dir)
    path = _research_file(name_or_dir, "claims.yaml")
    return _cached_load_research_claims(name_or_dir, _mtime_ns(path))


def load_research_citations(name_or_dir: str | Path) -> Any:
    """Load research/citations.yaml with Streamlit cache when available."""
    from nblane.core.research_workspace import load_research_citations as _impl
    if not _streamlit_runtime_exists():
        return _impl(name_or_dir)
    path = _research_file(name_or_dir, "citations.yaml")
    return _cached_load_research_citations(name_or_dir, _mtime_ns(path))


def load_research_drafts(name_or_dir: str | Path) -> Any:
    """Load research/drafts.yaml with Streamlit cache when available."""
    from nblane.core.research_workspace import load_research_drafts as _impl
    if not _streamlit_runtime_exists():
        return _impl(name_or_dir)
    path = _research_file(name_or_dir, "drafts.yaml")
    return _cached_load_research_drafts(name_or_dir, _mtime_ns(path))


def load_chunks(name_or_dir: str | Path, source_id: str = "") -> Any:
    """Load research/chunks/<id>.jsonl with Streamlit cache when available.

    When ``source_id`` is empty the loader walks the chunks directory; the
    cache key includes the directory's mtime to invalidate on file add/remove.
    """
    from nblane.core.research_workspace import load_chunks as _impl
    if not _streamlit_runtime_exists():
        return _impl(name_or_dir, source_id)
    chunks_dir = _research_file(name_or_dir, "chunks")
    file_mtime = (
        _mtime_ns(chunks_dir / f"{_source_slug(source_id)}.jsonl")
        if source_id
        else -1
    )
    return _cached_load_chunks(
        name_or_dir,
        source_id,
        file_mtime,
        _mtime_ns(chunks_dir),
    )


def load_connectors(name_or_dir: str | Path) -> Any:
    """Load research/connectors.yaml with Streamlit cache when available."""
    from nblane.core.research_connectors import load_connectors as _impl
    if not _streamlit_runtime_exists():
        return _impl(name_or_dir)
    path = _research_file(name_or_dir, "connectors.yaml")
    return _cached_load_connectors(name_or_dir, _mtime_ns(path))


def load_paper_pages(name_or_dir: str | Path, source_id: str) -> Any:
    """Load paper-pages/<id>.jsonl with Streamlit cache when available."""
    from nblane.core.research_papers import load_paper_pages as _impl
    if not _streamlit_runtime_exists():
        return _impl(name_or_dir, source_id)
    path = _research_file(name_or_dir, "paper-pages", f"{_source_slug(source_id)}.jsonl")
    return _cached_load_paper_pages(name_or_dir, source_id, _mtime_ns(path))


def load_paper_segments(name_or_dir: str | Path, source_id: str) -> Any:
    """Load paper-segments/<id>.jsonl with Streamlit cache when available."""
    from nblane.core.research_papers import load_paper_segments as _impl
    if not _streamlit_runtime_exists():
        return _impl(name_or_dir, source_id)
    path = _research_file(name_or_dir, "paper-segments", f"{_source_slug(source_id)}.jsonl")
    return _cached_load_paper_segments(name_or_dir, source_id, _mtime_ns(path))


def load_paper_annotations(name_or_dir: str | Path, source_id: str) -> Any:
    """Load annotations/<id>.jsonl with Streamlit cache when available."""
    from nblane.core.research_papers import load_paper_annotations as _impl
    if not _streamlit_runtime_exists():
        return _impl(name_or_dir, source_id)
    path = _research_file(name_or_dir, "annotations", f"{_source_slug(source_id)}.jsonl")
    return _cached_load_paper_annotations(name_or_dir, source_id, _mtime_ns(path))


def load_paper_translations(name_or_dir: str | Path, source_id: str) -> Any:
    """Load translations/<id>.jsonl with Streamlit cache when available."""
    from nblane.core.research_papers import load_paper_translations as _impl
    if not _streamlit_runtime_exists():
        return _impl(name_or_dir, source_id)
    path = _research_file(name_or_dir, "translations", f"{_source_slug(source_id)}.jsonl")
    return _cached_load_paper_translations(name_or_dir, source_id, _mtime_ns(path))


def load_paper_library_tree(name_or_dir: str | Path) -> Any:
    """Load papers/library-tree.yaml with Streamlit cache when available."""
    from nblane.core.research_papers import load_paper_library_tree as _impl
    if not _streamlit_runtime_exists():
        return _impl(name_or_dir)
    path = _research_file(name_or_dir, "papers", "library-tree.yaml")
    return _cached_load_paper_library_tree(name_or_dir, _mtime_ns(path))
