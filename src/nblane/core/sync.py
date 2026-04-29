"""Profile sync: deterministic rendering of generated SKILL.md blocks."""

from __future__ import annotations

import re
from pathlib import Path

from nblane.core import git_backup
from nblane.core.file_write import atomic_write_text
from nblane.core.io import (
    KANBAN_DOING,
    KANBAN_QUEUE,
    load_schema_raw,
    load_skill_tree_raw,
    parse_kanban,
    schema_node_index,
)

BLOCK_SKILL_TREE = "skill_tree"
BLOCK_CURRENT_FOCUS = "current_focus"

BLOCKS = (BLOCK_SKILL_TREE, BLOCK_CURRENT_FOCUS)

MARK_ICON = {
    "expert": "[x]",
    "solid": "[x]",
    "learning": "[ ]",
    "locked": "[~]",
}


def _marker_lines(block_name: str) -> tuple[str, str]:
    """Return begin/end marker lines for a generated block."""
    begin = f"<!-- BEGIN GENERATED:{block_name} -->"
    end = f"<!-- END GENERATED:{block_name} -->"
    return begin, end


def _extract_block_body(
    content: str,
    block_name: str,
) -> str:
    """Extract the body text between begin/end markers."""
    begin, end = _marker_lines(block_name)
    pattern = re.compile(
        rf"{re.escape(begin)}\n(.*?)\n{re.escape(end)}",
        re.DOTALL,
    )
    match = pattern.search(content)
    if match is None:
        raise ValueError(
            f"Missing generated markers for "
            f"block '{block_name}'."
        )
    return match.group(1).strip()


def _replace_block_body(
    content: str,
    block_name: str,
    body: str,
) -> str:
    """Replace one generated block body."""
    begin, end = _marker_lines(block_name)
    pattern = re.compile(
        rf"{re.escape(begin)}\n(.*?)\n{re.escape(end)}",
        re.DOTALL,
    )
    if pattern.search(content) is None:
        raise ValueError(
            f"Missing generated markers for "
            f"block '{block_name}'."
        )
    replacement = f"{begin}\n{body.strip()}\n{end}"
    return pattern.sub(replacement, content, count=1)


def _render_skill_tree_block(profile_dir: Path) -> str:
    """Render markdown summary from skill-tree.yaml."""
    tree = load_skill_tree_raw(profile_dir)
    if tree is None:
        return "- skill-tree.yaml not found."

    schema_name = tree.get("schema")
    index: dict[str, dict] = {}
    if schema_name is not None:
        schema_data = load_schema_raw(str(schema_name))
        if schema_data is not None:
            index = schema_node_index(schema_data)

    lines: list[str] = []
    for node in tree.get("nodes") or []:
        node_id = node.get("id")
        if node_id is None:
            continue
        status = node.get("status", "locked")
        icon = MARK_ICON.get(status, "[~]")
        label = index.get(node_id, {}).get("label", node_id)
        note = node.get("note")
        if note is None or str(note).strip() == "":
            lines.append(f"- {icon} {label} (`{node_id}`)")
        else:
            lines.append(
                f"- {icon} {label} (`{node_id}`): {note}"
            )

    if not lines:
        return (
            "- No skill nodes configured yet "
            "in skill-tree.yaml."
        )
    return "\n".join(lines)


def _is_placeholder_blocker(value: str) -> bool:
    """Return true for template-only blocker placeholders."""
    text = value.strip().lower()
    return not text or "{dependency" in text


def _render_focus_from_kanban(profile_dir: Path) -> str:
    """Render Current Focus block from kanban.md."""
    if not (profile_dir / "kanban.md").exists():
        return (
            "**Active** (this week):\n"
            "- kanban.md not found.\n\n"
            "**Queued** (next):\n"
            "- none\n\n"
            "**Blocked**:\n"
            "- none"
        )

    sections = parse_kanban(profile_dir)
    focus_tasks = (
        sections.get(KANBAN_DOING, [])
        + sections.get(KANBAN_QUEUE, [])
    )
    doing = [
        task.title.strip()
        for task in sections.get(KANBAN_DOING, [])
        if task.title.strip()
    ]
    queue = [
        task.title.strip()
        for task in sections.get(KANBAN_QUEUE, [])
        if task.title.strip()
    ]
    blocked = [
        (
            f"{task.title.strip()} — blocked by: "
            f"{task.blocked_by.strip()}"
        )
        for task in focus_tasks
        if task.title.strip()
        and not _is_placeholder_blocker(task.blocked_by)
    ]

    doing_lines = doing if doing else ["none"]
    queue_lines = queue if queue else ["none"]
    blocked_lines = blocked if blocked else ["none"]

    active_block = "\n".join(
        f"- {item}" for item in doing_lines
    )
    queue_block = "\n".join(
        f"- {item}" for item in queue_lines
    )
    blocked_block = "\n".join(
        f"- {item}" for item in blocked_lines
    )

    return (
        "**Active** (this week):\n"
        f"{active_block}\n\n"
        "**Queued** (next):\n"
        f"{queue_block}\n\n"
        "**Blocked**:\n"
        f"{blocked_block}"
    )


def build_generated_blocks(
    profile_dir: Path,
) -> dict[str, str]:
    """Build all generated blocks for one profile."""
    return {
        BLOCK_SKILL_TREE: _render_skill_tree_block(
            profile_dir
        ),
        BLOCK_CURRENT_FOCUS: _render_focus_from_kanban(
            profile_dir
        ),
    }


def get_drifted_blocks(profile_dir: Path) -> list[str]:
    """Return block names whose content differs from generated."""
    skill_md = profile_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValueError("SKILL.md not found.")
    content = skill_md.read_text(encoding="utf-8")
    generated = build_generated_blocks(profile_dir)

    drifted: list[str] = []
    for block_name in BLOCKS:
        existing = _extract_block_body(content, block_name)
        expected = generated[block_name].strip()
        if existing.strip() != expected:
            drifted.append(block_name)
    return drifted


def write_generated_blocks(profile_dir: Path) -> None:
    """Rewrite generated blocks in SKILL.md."""
    skill_md = profile_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValueError("SKILL.md not found.")
    content = skill_md.read_text(encoding="utf-8")
    generated = build_generated_blocks(profile_dir)
    updated = content
    for block_name in BLOCKS:
        updated = _replace_block_body(
            updated, block_name, generated[block_name]
        )
    atomic_write_text(skill_md, updated)
    git_backup.record_change(
        [skill_md],
        action=f"sync {profile_dir.name}/SKILL.md",
    )
