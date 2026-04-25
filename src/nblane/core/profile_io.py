"""Profile-scoped file I/O for nblane."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from nblane.core.models import EvidencePool, SkillTree
from nblane.core.paths import PROFILES_DIR
from nblane.core.yaml_io import _load_yaml_dict, _load_yaml_file

STATUSES = ("locked", "learning", "solid", "expert")
EVIDENCE_POOL_FILENAME = "evidence-pool.yaml"
SKILL_TREE_FILENAME = "skill-tree.yaml"


def _profile_file_path(
    name_or_dir: str | Path,
    filename: str,
) -> Path:
    """Resolve a profile-scoped file path from a name or profile directory."""
    if isinstance(name_or_dir, Path):
        return name_or_dir / filename
    return profile_dir(name_or_dir) / filename


def list_profiles() -> list[str]:
    """Return profile names (non-template subdirs of profiles/)."""
    if not PROFILES_DIR.exists():
        return []
    return sorted(
        d.name
        for d in PROFILES_DIR.iterdir()
        if d.is_dir() and d.name != "template"
    )


def profile_dir(name: str) -> Path:
    """Return path to profiles/{name}."""
    return PROFILES_DIR / name


def load_skill_tree(name_or_dir: str | Path) -> SkillTree | None:
    """Load skill-tree.yaml for a profile.

    *name_or_dir* may be a profile name (string) or a Path to the
    profile directory (for backward compatibility with tools that
    pass a resolved path).
    """
    path = _profile_file_path(name_or_dir, SKILL_TREE_FILENAME)
    raw = _load_yaml_file(path)
    if raw is None:
        return None
    return SkillTree.from_dict(raw)


def load_skill_tree_raw(name_or_dir: str | Path) -> dict | None:
    """Load skill-tree.yaml as a raw dict (for legacy callers)."""
    path = _profile_file_path(name_or_dir, SKILL_TREE_FILENAME)
    raw = _load_yaml_file(path)
    if raw is None:
        return None
    return raw


def save_skill_tree(name: str, data: dict) -> None:
    """Write skill-tree.yaml with today's date updated."""
    data = dict(data)
    data["updated"] = date.today().isoformat()
    path = profile_dir(name) / SKILL_TREE_FILENAME
    header = (
        f"# Skill tree for {name}\n"
        "# Schema defined in schemas/ — "
        "status: locked | learning | solid | expert\n\n"
    )
    body = yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    path.write_text(header + body, encoding="utf-8")


def load_evidence_pool(
    name_or_dir: str | Path,
) -> EvidencePool | None:
    """Load evidence-pool.yaml for a profile.

    Returns None if the file is missing.
    """
    path = _profile_file_path(name_or_dir, EVIDENCE_POOL_FILENAME)
    raw = _load_yaml_dict(path)
    if raw is None:
        return None
    return EvidencePool.from_dict(raw)


def load_evidence_pool_raw(
    name_or_dir: str | Path,
) -> dict | None:
    """Load evidence-pool.yaml as a raw dict."""
    path = _profile_file_path(name_or_dir, EVIDENCE_POOL_FILENAME)
    return _load_yaml_dict(path)


def save_evidence_pool(name: str, data: dict) -> None:
    """Write evidence-pool.yaml with today's date updated."""
    data = dict(data)
    data["updated"] = date.today().isoformat()
    path = profile_dir(name) / EVIDENCE_POOL_FILENAME
    header = (
        f"# Evidence pool for {name}\n"
        "# Shared records; skill-tree nodes reference ids via "
        "evidence_refs\n\n"
    )
    body = yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    path.write_text(header + body, encoding="utf-8")


def load_skill_md(name: str) -> str:
    """Return raw SKILL.md content, or empty string if absent."""
    path = profile_dir(name) / "SKILL.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def init_profile(name: str) -> Path:
    """Create a new profile from the template directory.

    Returns the path to the new profile directory.
    Raises FileExistsError if it already exists.
    """
    import shutil

    from nblane.core.paths import TEMPLATE_DIR

    dest = PROFILES_DIR / name
    if dest.exists():
        raise FileExistsError(
            f"Profile '{name}' already exists."
        )

    shutil.copytree(TEMPLATE_DIR, dest)

    for filepath in dest.rglob("*"):
        if filepath.is_file():
            text = filepath.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            filepath.write_text(text, encoding="utf-8")

    return dest
