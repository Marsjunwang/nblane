"""Shared Markdown text views over profile data.

Single implementation for the ``profile://goals`` / ``profile://summary``
MCP resources (``mcp_server.py``) and the OpenClaw memory corpus renderer
(``core/openclaw_corpus.py``) so both channels render identical text. This
module is deliberately neutral: no FastMCP import, no OpenClaw concepts —
``mcp_server`` imports from here, never the other way round.

Goal privacy matches the agent-context contract (``core/context.py``):
private goals never appear; the North Star goes through
``north_star_context_from_identity(..., for_agent=True)``.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from nblane.core.goals import (
    GOAL_STATUSES,
    current_goal,
    goal_for_agent_context,
    load_goal_book,
)
from nblane.core.io import (
    KANBAN_DOING,
    load_skill_tree_raw,
    parse_kanban,
)
from nblane.core.profile_context import (
    north_star_context_from_identity,
    parse_identity_fields,
)
from nblane.core.status import STATUS_ICONS, count_nodes, lit_fraction


def load_agent_profile_dict(pdir: Path) -> dict:
    """Load agent-profile.yaml as a dict, or empty dict."""
    path = pdir / "agent-profile.yaml"
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def render_goals_text(profile_name: str, pdir: Path) -> str:
    """Goals summary with the same privacy contract as agent context."""
    lines: list[str] = [f"# Goals: {profile_name}", ""]

    identity: dict[str, str] = {}
    skill_md = pdir / "SKILL.md"
    if skill_md.exists():
        identity = parse_identity_fields(
            skill_md.read_text(encoding="utf-8")
        )
    north_star = north_star_context_from_identity(identity, for_agent=True)
    lines.append("## North Star")
    if north_star:
        lines.append(north_star)
    else:
        lines.append("(not set)")
    lines.append("")

    book = load_goal_book(pdir)
    if not book.goals:
        lines.append("No goals recorded (goals.yaml missing or empty).")
        return "\n".join(lines).rstrip() + "\n"

    counts = Counter(goal.status for goal in book.goals)
    lines.append("## Status counts")
    for status in GOAL_STATUSES:
        count = counts.get(status, 0)
        if count:
            lines.append(f"- {status}: {count}")
    lines.append("")

    primary = book.primary()
    primary_text = goal_for_agent_context(primary)
    lines.append("## Primary goal")
    lines.append(
        primary_text if primary_text else "(none visible to agent context)"
    )
    lines.append("")

    primary_id = primary.id if primary is not None else ""
    visible_others: list[str] = []
    hidden = 0 if primary_text else (1 if primary is not None else 0)
    for goal in book.goals:
        if goal.id == primary_id:
            continue
        text = goal_for_agent_context(goal)
        if not text:
            hidden += 1
            continue
        heading = goal.title or goal.label or goal.id
        visible_others.append(f"### {heading} [{goal.status}]\n{text}")
    if visible_others:
        lines.append("## Other goals visible to agent context")
        for block in visible_others:
            lines.append(block)
            lines.append("")
    if hidden:
        lines.append(
            f"({hidden} goal(s) hidden by visibility / "
            "include_in_agent_context settings.)"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_summary_text(profile_name: str, pdir: Path) -> str:
    """Tree summary, focus, working-style preferences, and Doing kanban."""
    lines: list[str] = [
        f"# Profile summary: {profile_name}",
        "",
    ]

    goal_text = goal_for_agent_context(current_goal(pdir))
    if goal_text:
        lines.append("## Current Goal")
        lines.append(goal_text)
        lines.append("")

    tree = load_skill_tree_raw(pdir)
    if tree is None:
        lines.append("## Skill tree")
        lines.append("Not initialized (no skill-tree.yaml).")
    else:
        counts = count_nodes(tree)
        lines.append("## Skill tree")
        lines.append(f"- Lit: **{lit_fraction(counts)}**")
        for status, icon in STATUS_ICONS.items():
            n = counts.get(status, 0)
            if n > 0:
                lines.append(f"  - {icon} {status}: {n}")
    lines.append("")

    agent_profile = load_agent_profile_dict(pdir)
    uou = agent_profile.get("understanding_of_user")
    if isinstance(uou, dict):
        focus = uou.get("current_focus")
        if isinstance(focus, list) and focus:
            lines.append("## Focus (agent-profile)")
            for item in focus:
                lines.append(f"- {item}")
            lines.append("")

    ws = agent_profile.get("working_style")
    if isinstance(ws, dict):
        prefers = ws.get("prefers")
        avoids = ws.get("avoids")
        if (isinstance(prefers, list) and prefers) or (
            isinstance(avoids, list) and avoids
        ):
            lines.append("## Preferences (working_style)")
            if isinstance(prefers, list) and prefers:
                lines.append("**Prefers**")
                for item in prefers:
                    lines.append(f"- {item}")
            if isinstance(avoids, list) and avoids:
                lines.append("**Avoids**")
                for item in avoids:
                    lines.append(f"- {item}")
            lines.append("")

    sections = parse_kanban(pdir)
    doing = sections.get(KANBAN_DOING) or []
    titles = [
        task.title.strip()
        for task in doing
        if task.title and task.title.strip() not in ("(empty)",)
    ]
    lines.append("## Kanban · Doing")
    if titles:
        for title in titles:
            lines.append(f"- {title}")
    else:
        lines.append("(none)")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "load_agent_profile_dict",
    "render_goals_text",
    "render_summary_text",
]
