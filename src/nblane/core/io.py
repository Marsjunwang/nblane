"""Unified file I/O for nblane profile, schema, and team data.

Single source of truth — replaces tools/schema_utils.py and
app/utils/file_io.py.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import yaml

from nblane.core.models import (
    EvidencePool,
    KanbanTask,
    Schema,
    SkillNode,
    SkillTree,
)
from nblane.core.paths import PROFILES_DIR, SCHEMAS_DIR, TEAMS_DIR

STATUSES = ("locked", "learning", "solid", "expert")
KANBAN_SECTIONS = ("Doing", "Done", "Queue", "Someday / Maybe")
EVIDENCE_POOL_FILENAME = "evidence-pool.yaml"


# -- Profiles ---------------------------------------------------------------


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


# -- Skill tree YAML --------------------------------------------------------


def load_skill_tree(name_or_dir: str | Path) -> SkillTree | None:
    """Load skill-tree.yaml for a profile.

    *name_or_dir* may be a profile name (string) or a Path to the
    profile directory (for backward compatibility with tools that
    pass a resolved path).
    """
    if isinstance(name_or_dir, Path):
        path = name_or_dir / "skill-tree.yaml"
    else:
        path = profile_dir(name_or_dir) / "skill-tree.yaml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if raw is None:
        return None
    return SkillTree.from_dict(raw)


def load_skill_tree_raw(name_or_dir: str | Path) -> dict | None:
    """Load skill-tree.yaml as a raw dict (for legacy callers)."""
    if isinstance(name_or_dir, Path):
        path = name_or_dir / "skill-tree.yaml"
    else:
        path = profile_dir(name_or_dir) / "skill-tree.yaml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_skill_tree(name: str, data: dict) -> None:
    """Write skill-tree.yaml with today's date updated."""
    data = dict(data)
    data["updated"] = date.today().isoformat()
    path = profile_dir(name) / "skill-tree.yaml"
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


# -- Evidence pool (profile-level) ------------------------------------------


def load_evidence_pool(
    name_or_dir: str | Path,
) -> EvidencePool | None:
    """Load evidence-pool.yaml for a profile.

    Returns None if the file is missing.
    """
    if isinstance(name_or_dir, Path):
        path = name_or_dir / EVIDENCE_POOL_FILENAME
    else:
        path = profile_dir(name_or_dir) / EVIDENCE_POOL_FILENAME
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return None
    return EvidencePool.from_dict(raw)


def load_evidence_pool_raw(
    name_or_dir: str | Path,
) -> dict | None:
    """Load evidence-pool.yaml as a raw dict."""
    if isinstance(name_or_dir, Path):
        path = name_or_dir / EVIDENCE_POOL_FILENAME
    else:
        path = profile_dir(name_or_dir) / EVIDENCE_POOL_FILENAME
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return None
    return raw


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


# -- Schema ------------------------------------------------------------------


def load_schema(schema_name: str) -> Schema | None:
    """Load schemas/{schema_name}.yaml as a Schema object."""
    path = SCHEMAS_DIR / f"{schema_name}.yaml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if raw is None:
        return None
    return Schema.from_dict(raw)


def load_schema_raw(schema_name: str) -> dict | None:
    """Load schemas/{schema_name}.yaml as a raw dict."""
    path = SCHEMAS_DIR / f"{schema_name}.yaml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_schemas() -> list[str]:
    """Return available schema names (without .yaml extension)."""
    return sorted(p.stem for p in SCHEMAS_DIR.glob("*.yaml"))


def schema_node_index(schema_data: dict) -> dict[str, dict]:
    """Return id -> schema-node dict from a raw schema dict.

    Kept for backward compatibility with code that still works on
    raw dicts (Streamlit pages during migration).
    """
    return {
        n["id"]: n
        for n in schema_data.get("nodes") or []
        if "id" in n
    }


def status_by_node_id(tree_data: dict | None) -> dict[str, str]:
    """Map node id -> status from a raw skill-tree dict."""
    if tree_data is None:
        return {}
    out: dict[str, str] = {}
    for node in tree_data.get("nodes") or []:
        nid = node.get("id")
        if nid is None:
            continue
        out[nid] = node.get("status", "locked")
    return out


# -- SKILL.md ----------------------------------------------------------------


def load_skill_md(name: str) -> str:
    """Return raw SKILL.md content, or empty string if absent."""
    path = profile_dir(name) / "SKILL.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


# -- Kanban Markdown ---------------------------------------------------------


def parse_kanban(name: str) -> dict[str, list[KanbanTask]]:
    """Parse kanban.md into section -> task list."""
    path = profile_dir(name) / "kanban.md"
    sections: dict[str, list[KanbanTask]] = {
        s: [] for s in KANBAN_SECTIONS
    }
    if not path.exists():
        return sections

    content = path.read_text(encoding="utf-8")
    current_section = ""
    current_task: KanbanTask | None = None

    for line in content.splitlines():
        stripped = line.strip()

        if stripped.startswith("## "):
            if (
                current_task is not None
                and current_section in sections
            ):
                sections[current_section].append(current_task)
                current_task = None
            current_section = stripped[3:].strip()
            continue

        if stripped in ("---", "") or stripped.startswith(">"):
            continue

        checkbox = re.match(
            r"^\s*-\s+\[([ xX])\]\s+(.+)$", line
        )
        if checkbox:
            if (
                current_task is not None
                and current_section in sections
            ):
                sections[current_section].append(current_task)
            done = checkbox.group(1).lower() == "x"
            current_task = KanbanTask(
                title=checkbox.group(2).strip(),
                done=done,
            )
            continue

        bullet = re.match(r"^\s*-\s+(.+)$", line)
        if bullet:
            text = bullet.group(1).strip()
            if current_section == "Someday / Maybe":
                if current_task is not None:
                    sections[current_section].append(
                        current_task
                    )
                current_task = KanbanTask(title=text)
            elif current_task is not None:
                current_task.details.append(text)
            continue

    if current_task is not None and current_section in sections:
        sections[current_section].append(current_task)

    return sections


def render_kanban(
    name: str,
    sections: dict[str, list[KanbanTask]],
) -> str:
    """Render structured sections back to kanban.md text."""
    today = date.today().isoformat()
    lines = [
        f"# {name} · Kanban",
        "",
        f"> Updated: {today}",
        "> Rule: nothing lives in \"doing\" for more than"
        " 2 weeks. Move it or break it down.",
        "",
        "---",
    ]
    for section in KANBAN_SECTIONS:
        lines += ["", f"## {section}", ""]
        tasks = sections.get(section, [])
        if not tasks:
            lines.append("- (empty)")
        for task in tasks:
            if section == "Someday / Maybe":
                lines.append(f"- {task.title}")
            else:
                check = "[x]" if task.done else "[ ]"
                lines.append(f"- {check} {task.title}")
            for detail in task.details:
                lines.append(f"  - {detail}")
        lines += ["", "---"]
    return "\n".join(lines) + "\n"


def save_kanban(
    name: str,
    sections: dict[str, list[KanbanTask]],
) -> None:
    """Write kanban.md back from structured sections."""
    path = profile_dir(name) / "kanban.md"
    path.write_text(
        render_kanban(name, sections), encoding="utf-8"
    )


# -- Teams -------------------------------------------------------------------


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
    path = TEAMS_DIR / team_id / "team.yaml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_product_pool(team_id: str) -> dict | None:
    """Load product-pool.yaml for a team."""
    path = TEAMS_DIR / team_id / "product-pool.yaml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_team(team_id: str, data: dict) -> None:
    """Write team.yaml for a team."""
    path = TEAMS_DIR / team_id / "team.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    path.write_text(body, encoding="utf-8")


def save_product_pool(team_id: str, data: dict) -> None:
    """Write product-pool.yaml for a team."""
    path = TEAMS_DIR / team_id / "product-pool.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    path.write_text(body, encoding="utf-8")


# -- Profile init ------------------------------------------------------------


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
