"""System prompt generation from a nblane profile."""

from __future__ import annotations

from pathlib import Path

import yaml

from nblane.core.evidence_resolve import resolve_skill_node
from nblane.core.io import (
    load_evidence_pool,
    load_schema,
    load_skill_tree,
)
from nblane.core.models import Evidence
from nblane.core.paths import PROFILES_DIR
from nblane.core.profile_io import safe_profile_dir

PREAMBLE = """\
You are a specialized AI assistant operating as a projection \
of the person described below. Their SKILL.md is your prior. \
When you reason, write, review code, or give feedback, \
calibrate to their knowledge level, research taste, and \
communication style as described. Do not pretend to know \
things they have marked as "locked". Surface their blind \
spots honestly."""

MODE_SUFFIXES = {
    "chat": (
        "Mode: general assistant. Answer as a "
        "knowledgeable peer who shares this person's domain "
        "background. Be direct, skip basics they already "
        "know, go deep on areas they care about."
    ),
    "review": (
        "Mode: paper / code reviewer. Apply the review "
        "standards described in Research Fingerprint. Flag "
        "weak ablations, missing baselines, or claims "
        "unsupported by evidence. Be as demanding as the "
        "best reviewer they would want."
    ),
    "write": (
        "Mode: writing collaborator. Match the thinking and "
        "communication style described in SKILL.md. Maintain "
        "their voice. Prefer their preferred language mix. "
        "Surface when a draft contradicts their stated taste."
    ),
    "plan": (
        "Mode: growth planner. Given the current skill tree "
        "and kanban state, suggest the highest-leverage next "
        "action. Prioritize unlocking dependent skills and "
        "moving items out of 'blocked'."
    ),
}


def _load_text(path: Path) -> str | None:
    """Read a file if it exists, else return None."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def _public_profile_scalar(value: object) -> object | None:
    """Return a scalar value safe to render from agent-profile.yaml."""
    if isinstance(value, (str, int, float, bool)):
        return value
    return None


def _public_profile_value(value: object) -> object | None:
    """Keep only scalar or list-of-scalar public profile values."""
    scalar = _public_profile_scalar(value)
    if scalar is not None:
        return scalar
    if isinstance(value, (list, tuple, set)):
        out = [
            item
            for item in (
                _public_profile_scalar(entry)
                for entry in value
            )
            if item is not None
        ]
        return out or None
    return None


def _copy_allowed_mapping(
    raw: dict,
    key: str,
    allowed_keys: tuple[str, ...],
) -> dict | None:
    """Copy whitelisted nested keys from a YAML mapping."""
    value = raw.get(key)
    if not isinstance(value, dict):
        return None
    out: dict[str, object] = {}
    for child_key in allowed_keys:
        if child_key not in value:
            continue
        public_value = _public_profile_value(value[child_key])
        if public_value is not None:
            out[child_key] = public_value
    return out or None


def _render_agent_profile(path: Path) -> str | None:
    """Render only public whitelisted agent-profile.yaml fields."""
    if not path.exists():
        return None
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    if not isinstance(raw, dict):
        return None

    out: dict[str, object] = {}
    if "schema_version" in raw:
        schema_version = _public_profile_scalar(raw["schema_version"])
        if schema_version is not None:
            out["schema_version"] = schema_version

    understanding = _copy_allowed_mapping(
        raw,
        "understanding_of_user",
        ("strengths", "weaknesses", "current_focus"),
    )
    if understanding is not None:
        out["understanding_of_user"] = understanding

    working_style = _copy_allowed_mapping(
        raw,
        "working_style",
        ("prefers", "avoids"),
    )
    if working_style is not None:
        out["working_style"] = working_style

    if "confidence" in raw:
        confidence = _public_profile_scalar(raw["confidence"])
        if confidence is not None:
            out["confidence"] = confidence

    if not out:
        return None
    return yaml.dump(
        out,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).strip()


def _format_evidence_lines(
    profile_name: str,
) -> list[str]:
    """Lines for solid/expert nodes with evidence (for system prompt)."""
    tree = load_skill_tree(profile_name)
    if tree is None:
        return []

    schema = (
        load_schema(tree.schema)
        if tree.schema
        else None
    )
    index = schema.node_index() if schema else {}
    pool = load_evidence_pool(profile_name)

    lines: list[str] = []
    for node in tree.nodes:
        if node.status not in ("solid", "expert"):
            continue
        resolved = resolve_skill_node(node, pool)
        if not resolved:
            continue
        label = (
            index[node.id].label
            if node.id in index
            else node.id
        )
        lines.append(
            f"- **{node.id}** ({node.status}) — {label}"
        )
        for ev in resolved:
            lines.extend(
                _evidence_item_lines(ev)
            )
    return lines


def _evidence_item_lines(ev: Evidence) -> list[str]:
    """One bullet block for a single Evidence record."""
    head = f"  Evidence: [{ev.type}] {ev.title}"
    if ev.date:
        head += f" ({ev.date})"
    out = [head]
    if ev.url:
        out.append(f"    URL: {ev.url}")
    if ev.summary:
        out.append(f"    {ev.summary}")
    return out


def build_system_prompt(
    profile_text: str,
    agent_profile_text: str | None,
    kanban_text: str | None,
    mode: str,
    *,
    evidence_section: str | None = None,
) -> str:
    """Assemble a system prompt from profile components."""
    parts = [
        PREAMBLE.strip(),
        "",
        "---",
        "",
        profile_text.strip(),
    ]

    if agent_profile_text is not None:
        parts += [
            "",
            "---",
            "",
            "## Agent profile (structured)",
            "",
            agent_profile_text.strip(),
        ]

    if evidence_section:
        parts += [
            "",
            "---",
            "",
            "## Skill evidence (solid / expert)",
            "",
            evidence_section.strip(),
        ]

    if kanban_text is not None:
        parts += [
            "",
            "---",
            "",
            "## Current Kanban (for context)",
            "",
            kanban_text.strip(),
        ]

    suffix = MODE_SUFFIXES.get(mode)
    if suffix:
        parts += ["", "---", "", suffix]

    return "\n".join(parts)


def generate(
    profile_name: str,
    mode: str = "chat",
    include_kanban: bool = True,
) -> str:
    """Load profile files and return a complete system prompt."""
    pdir = safe_profile_dir(profile_name, PROFILES_DIR)

    skill_md = pdir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(
            f"SKILL.md not found for profile '{profile_name}'"
        )

    profile_text = skill_md.read_text(encoding="utf-8")
    agent_profile_text = _render_agent_profile(
        pdir / "agent-profile.yaml"
    )
    kanban_text = (
        _load_text(pdir / "kanban.md")
        if include_kanban
        else None
    )

    ev_lines = _format_evidence_lines(profile_name)
    evidence_section = (
        "\n".join(ev_lines)
        if ev_lines
        else None
    )

    return build_system_prompt(
        profile_text,
        agent_profile_text,
        kanban_text,
        mode,
        evidence_section=evidence_section,
    )
