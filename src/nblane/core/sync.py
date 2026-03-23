"""Profile sync: deterministic rendering of generated SKILL.md blocks."""

from __future__ import annotations

import re
from pathlib import Path

from nblane.core.io import (
    load_schema_raw,
    load_skill_tree_raw,
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


def _top_level_task(line: str) -> str | None:
    """Return task title if line is a top-level checkbox."""
    match = re.match(r"^\s*-\s\[[ xX]\]\s+(.*)$", line)
    if match is None:
        return None
    return match.group(1).strip()


def _render_focus_from_kanban(profile_dir: Path) -> str:
    """Render Current Focus block from kanban.md."""
    kanban_path = profile_dir / "kanban.md"
    if not kanban_path.exists():
        return (
            "**Active** (this week):\n"
            "- kanban.md not found.\n\n"
            "**Queued** (next):\n"
            "- none\n\n"
            "**Blocked**:\n"
            "- none"
        )

    section = ""
    doing: list[str] = []
    queue: list[str] = []
    blocked: list[str] = []
    current_task = ""
    current_detail: list[str] = []

    text = kanban_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if section == "Queue" and current_task != "":
                queue.append(current_task)
                detail_text = (
                    " ".join(current_detail).strip().lower()
                )
                if (
                    "blocked by:" in detail_text
                    and "{dependency" not in detail_text
                ):
                    blocked.append(current_task)
            section = stripped.replace("## ", "", 1).strip()
            current_task = ""
            current_detail = []
            continue

        task = _top_level_task(line)
        if task is not None:
            if section == "Queue" and current_task != "":
                queue.append(current_task)
                detail_text = (
                    " ".join(current_detail).strip().lower()
                )
                if (
                    "blocked by:" in detail_text
                    and "{dependency" not in detail_text
                ):
                    blocked.append(current_task)
            current_task = task
            current_detail = []
            if section == "Doing":
                doing.append(task)
            continue

        if section == "Queue" and current_task != "":
            current_detail.append(stripped)

    if section == "Queue" and current_task != "":
        queue.append(current_task)
        detail_text = (
            " ".join(current_detail).strip().lower()
        )
        if (
            "blocked by:" in detail_text
            and "{dependency" not in detail_text
        ):
            blocked.append(current_task)

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
    skill_md.write_text(updated, encoding="utf-8")
