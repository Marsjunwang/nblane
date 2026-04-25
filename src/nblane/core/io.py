"""Compatibility facade for nblane file I/O.

Domain-specific implementations live in profile_io, schema_io, kanban_io,
and team_io. Existing imports from nblane.core.io remain supported.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from nblane.core import kanban_io, profile_io, schema_io, team_io
from nblane.core.kanban_io import (
    KANBAN_ARCHIVE_FILENAME,
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SECTIONS,
    KANBAN_SOMEDAY,
)
from nblane.core.models import (
    EvidencePool,
    KanbanSubtask,
    KanbanTask,
    Schema,
    SkillNode,
    SkillTree,
)
from nblane.core.paths import PROFILES_DIR, SCHEMAS_DIR, TEAMS_DIR
from nblane.core.profile_io import (
    EVIDENCE_POOL_FILENAME,
    SKILL_TREE_FILENAME,
    STATUSES,
)
from nblane.core.yaml_io import _load_yaml_dict, _load_yaml_file


def _profile_file_path(
    name_or_dir: str | Path,
    filename: str,
) -> Path:
    """Resolve a profile-scoped file path from a name or profile directory."""
    if isinstance(name_or_dir, Path):
        return name_or_dir / filename
    return profile_dir(name_or_dir) / filename


def profile_dir(name: str) -> Path:
    """Return path to profiles/{name}."""
    return PROFILES_DIR / name


def list_profiles() -> list[str]:
    """Return profile names (non-template subdirs of profiles/)."""
    return profile_io.list_profiles()


def load_skill_tree(name_or_dir: str | Path) -> SkillTree | None:
    """Load skill-tree.yaml for a profile."""
    path = _profile_file_path(name_or_dir, SKILL_TREE_FILENAME)
    raw = _load_yaml_file(path)
    if raw is None:
        return None
    return SkillTree.from_dict(raw)


def load_skill_tree_raw(name_or_dir: str | Path) -> dict | None:
    """Load skill-tree.yaml as a raw dict."""
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


def load_evidence_pool(name_or_dir: str | Path) -> EvidencePool | None:
    """Load evidence-pool.yaml for a profile."""
    path = _profile_file_path(name_or_dir, EVIDENCE_POOL_FILENAME)
    raw = _load_yaml_dict(path)
    if raw is None:
        return None
    return EvidencePool.from_dict(raw)


def load_evidence_pool_raw(name_or_dir: str | Path) -> dict | None:
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
    """Create a new profile from the template directory."""
    return profile_io.init_profile(name)


def load_schema(schema_name: str) -> Schema | None:
    """Load schemas/{schema_name}.yaml as a Schema object."""
    path = SCHEMAS_DIR / f"{schema_name}.yaml"
    raw = _load_yaml_file(path)
    if raw is None:
        return None
    return Schema.from_dict(raw)


def load_schema_raw(schema_name: str) -> dict | None:
    """Load schemas/{schema_name}.yaml as a raw dict."""
    path = SCHEMAS_DIR / f"{schema_name}.yaml"
    raw = _load_yaml_file(path)
    if raw is None:
        return None
    return raw


def list_schemas() -> list[str]:
    """Return available schema names (without .yaml extension)."""
    return sorted(p.stem for p in SCHEMAS_DIR.glob("*.yaml"))


def schema_node_index(schema_data: dict) -> dict[str, dict]:
    """Return id -> schema-node dict from a raw schema dict."""
    return schema_io.schema_node_index(schema_data)


def status_by_node_id(tree_data: dict | None) -> dict[str, str]:
    """Map node id -> status from a raw skill-tree dict."""
    return schema_io.status_by_node_id(tree_data)


def parse_kanban(name: str) -> dict[str, list[KanbanTask]]:
    """Parse kanban.md into section -> task list."""
    old = kanban_io.profile_dir
    kanban_io.profile_dir = profile_dir
    try:
        return kanban_io.parse_kanban(name)
    finally:
        kanban_io.profile_dir = old


def render_kanban(
    name: str,
    sections: dict[str, list[KanbanTask]],
) -> str:
    """Render structured sections back to kanban.md text."""
    return kanban_io.render_kanban(name, sections)


def save_kanban(
    name: str,
    sections: dict[str, list[KanbanTask]],
) -> None:
    """Write kanban.md back from structured sections."""
    old = kanban_io.profile_dir
    kanban_io.profile_dir = profile_dir
    try:
        return kanban_io.save_kanban(name, sections)
    finally:
        kanban_io.profile_dir = old


def append_kanban_archive(
    name: str,
    tasks: list[KanbanTask],
) -> None:
    """Append Done tasks to kanban-archive.md under today's heading."""
    old = kanban_io.profile_dir
    kanban_io.profile_dir = profile_dir
    try:
        return kanban_io.append_kanban_archive(name, tasks)
    finally:
        kanban_io.profile_dir = old


def list_teams() -> list[str]:
    """Return team IDs (non-template subdirs of teams/)."""
    if not TEAMS_DIR.exists():
        return []
    return sorted(
        d.name
        for d in TEAMS_DIR.iterdir()
        if d.is_dir() and d.name != "_template"
    )


def load_team(team_id: str) -> dict | None:
    """Load team.yaml for a team."""
    old = team_io.TEAMS_DIR
    team_io.TEAMS_DIR = TEAMS_DIR
    try:
        return team_io.load_team(team_id)
    finally:
        team_io.TEAMS_DIR = old


def load_product_pool(team_id: str) -> dict | None:
    """Load product-pool.yaml for a team."""
    old = team_io.TEAMS_DIR
    team_io.TEAMS_DIR = TEAMS_DIR
    try:
        return team_io.load_product_pool(team_id)
    finally:
        team_io.TEAMS_DIR = old


def save_team(team_id: str, data: dict) -> None:
    """Write team.yaml for a team."""
    old = team_io.TEAMS_DIR
    team_io.TEAMS_DIR = TEAMS_DIR
    try:
        return team_io.save_team(team_id, data)
    finally:
        team_io.TEAMS_DIR = old


def save_product_pool(team_id: str, data: dict) -> None:
    """Write product-pool.yaml for a team."""
    old = team_io.TEAMS_DIR
    team_io.TEAMS_DIR = TEAMS_DIR
    try:
        return team_io.save_product_pool(team_id, data)
    finally:
        team_io.TEAMS_DIR = old

__all__ = [
    "EVIDENCE_POOL_FILENAME",
    "KANBAN_ARCHIVE_FILENAME",
    "KANBAN_DOING",
    "KANBAN_DONE",
    "KANBAN_QUEUE",
    "KANBAN_SECTIONS",
    "KANBAN_SOMEDAY",
    "KanbanSubtask",
    "KanbanTask",
    "PROFILES_DIR",
    "SCHEMAS_DIR",
    "Schema",
    "SKILL_TREE_FILENAME",
    "STATUSES",
    "SkillNode",
    "SkillTree",
    "TEAMS_DIR",
    "append_kanban_archive",
    "init_profile",
    "list_profiles",
    "list_schemas",
    "list_teams",
    "load_evidence_pool",
    "load_evidence_pool_raw",
    "load_product_pool",
    "load_schema",
    "load_schema_raw",
    "load_skill_md",
    "load_skill_tree",
    "load_skill_tree_raw",
    "load_team",
    "parse_kanban",
    "profile_dir",
    "render_kanban",
    "save_evidence_pool",
    "save_kanban",
    "save_product_pool",
    "save_skill_tree",
    "save_team",
    "schema_node_index",
    "status_by_node_id",
]
