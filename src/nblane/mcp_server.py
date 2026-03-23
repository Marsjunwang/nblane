"""Read-only MCP server: expose nblane profile context via MCP resources (stdio).

Environment:
  NBLANE_PROFILE — default profile name (optional if exactly one profile exists).
  NBLANE_ROOT — repo root override (see nblane.core.paths).
  NBLANE_CONTEXT_MODE — chat | review | write | plan for profile://context.
  NBLANE_GAP_USE_LLM — if ``1`` / ``true``, enable LLM routing in gap analysis.
"""

from __future__ import annotations

import os
import urllib.parse
from collections.abc import Callable
from pathlib import Path

import yaml
from mcp.server.fastmcp import FastMCP

from nblane.core.context import generate
from nblane.core.crystallize import write_method_draft
from nblane.core.gap import analyze, format_text
from nblane.core.growth_log import append_growth_log_row
from nblane.core.interaction import append_interaction_record
from nblane.core.io import (
    list_profiles,
    load_skill_tree_raw,
    parse_kanban,
    profile_dir,
)
from nblane.core.paths import PROFILES_DIR
from nblane.core.skill_evidence_inline import add_inline_evidence
from nblane.core.status import STATUS_ICONS, count_nodes, lit_fraction

_PROFILE_ENV_KEYS = ("NBLANE_PROFILE", "NBLANE_MCP_PROFILE")


def _truthy_env(name: str) -> bool:
    """Return True if env *name* is set to a truthy string."""
    v = os.getenv(name)
    if v is None:
        return False
    return v.strip().lower() in ("1", "true", "yes", "on")


def resolve_active_profile() -> tuple[str | None, str | None]:
    """Return ``(profile_name, None)`` or ``(None, error_message)``."""
    for key in _PROFILE_ENV_KEYS:
        raw = os.getenv(key)
        if raw is None or not str(raw).strip():
            continue
        name = str(raw).strip()
        p = profile_dir(name)
        if not p.is_dir():
            return (
                None,
                f"Profile {name!r} not found under {PROFILES_DIR}.",
            )
        return (name, None)

    names = list_profiles()
    if len(names) == 1:
        return (names[0], None)
    if not names:
        return (
            None,
            f"No profiles under {PROFILES_DIR}. "
            "Create one or set NBLANE_PROFILE.",
        )
    return (
        None,
        "Set NBLANE_PROFILE to choose a profile "
        f"(found: {', '.join(names)}).",
    )


def _load_agent_profile_dict(pdir: Path) -> dict:
    """Load agent-profile.yaml as a dict, or empty dict."""
    path = pdir / "agent-profile.yaml"
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def build_summary_text(profile_name: str) -> str:
    """Tree summary, focus, and working-style preferences for MCP."""
    pdir = profile_dir(profile_name)
    lines: list[str] = [
        f"# Profile summary: {profile_name}",
        "",
    ]

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

    ap = _load_agent_profile_dict(pdir)
    uou = ap.get("understanding_of_user")
    if isinstance(uou, dict):
        focus = uou.get("current_focus")
        if isinstance(focus, list) and focus:
            lines.append("## Focus (agent-profile)")
            for item in focus:
                lines.append(f"- {item}")
            lines.append("")

    ws = ap.get("working_style")
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

    sections = parse_kanban(profile_name)
    doing = sections.get("Doing") or []
    titles = [
        t.title.strip()
        for t in doing
        if t.title and t.title.strip() not in ("(empty)",)
    ]
    lines.append("## Kanban · Doing")
    if titles:
        for t in titles:
            lines.append(f"- {t}")
    else:
        lines.append("(none)")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _profile_text_resource(
    getter: str,
    builder: Callable[[str], str],
) -> str:
    """Shared error handling for profile-scoped resources."""
    name, err = resolve_active_profile()
    if err is not None:
        return f"ERROR [{getter}]: {err}\n"
    try:
        return builder(name)
    except FileNotFoundError as exc:
        return f"ERROR [{getter}]: {exc}\n"


mcp = FastMCP("nblane")


@mcp.resource(
    "profile://summary",
    mime_type="text/markdown",
)
def resource_summary() -> str:
    """Skill tree counts, focus, preferences, and Doing kanban."""
    return _profile_text_resource(
        "profile://summary",
        build_summary_text,
    )


@mcp.resource(
    "profile://kanban",
    mime_type="text/markdown",
)
def resource_kanban() -> str:
    """Raw kanban.md for the active profile."""
    def _read(name: str) -> str:
        """Return kanban.md text or a short placeholder."""
        path = profile_dir(name) / "kanban.md"
        if not path.exists():
            return f"(no kanban.md for profile {name!r})\n"
        return path.read_text(encoding="utf-8")

    return _profile_text_resource("profile://kanban", _read)


@mcp.resource(
    "profile://context",
    mime_type="text/plain",
)
def resource_context() -> str:
    """Full agent system prompt (SKILL.md + evidence + kanban + mode)."""
    mode = os.getenv("NBLANE_CONTEXT_MODE", "chat")
    if mode not in ("chat", "review", "write", "plan"):
        mode = "chat"

    def _gen(name: str) -> str:
        """Build system prompt for *name* at ``mode``."""
        return generate(
            name,
            mode=mode,
            include_kanban=True,
        )

    return _profile_text_resource("profile://context", _gen)


@mcp.resource(
    "profile://gap/{task}",
    mime_type="text/plain",
)
def resource_gap(task: str) -> str:
    """Gap analysis for a natural-language task (URL-encode spaces in *task*)."""
    name, err = resolve_active_profile()
    if err is not None:
        return f"ERROR [profile://gap]: {err}\n"

    decoded = urllib.parse.unquote(task)
    if not decoded.strip():
        return (
            "ERROR [profile://gap]: Empty task. "
            "Use a non-empty path segment, e.g. "
            "profile://gap/VLM%20robot%20control\n"
        )

    use_llm = _truthy_env("NBLANE_GAP_USE_LLM")
    result = analyze(
        name,
        decoded.strip(),
        explicit_node=None,
        use_rule_match=True,
        use_llm_router=use_llm,
        persist_router_keywords=False,
    )
    if result.error:
        return f"ERROR [profile://gap]: {result.error}\n"
    return format_text(result) + "\n"


def _tool_profile_or_error() -> tuple[str | None, str | None]:
    """Return ``(name, None)`` or ``(None, error)`` for MCP tools."""
    return resolve_active_profile()


@mcp.tool(name="append_growth_log")
def tool_append_growth_log(event: str) -> str:
    """Append one row to the Growth Log table in SKILL.md."""
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    try:
        append_growth_log_row(profile_dir(name), event.strip())
    except (OSError, ValueError) as exc:
        return f"ERROR: {exc}\n"
    return f"OK: growth log updated for profile {name!r}.\n"


@mcp.tool(name="log_skill_evidence")
def tool_log_skill_evidence(
    skill_id: str,
    title: str,
    evidence_type: str = "practice",
    date: str = "",
    url: str = "",
    summary: str = "",
) -> str:
    """Add one inline evidence item to a skill-tree node."""
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    try:
        add_inline_evidence(
            name,
            skill_id.strip(),
            type_=evidence_type.strip() or "practice",
            title=title,
            date=date,
            url=url,
            summary=summary,
        )
    except ValueError as exc:
        return f"ERROR: {exc}\n"
    return (
        f"OK: evidence on {skill_id!r} "
        f"({title.strip()!r}) for {name!r}.\n"
    )


@mcp.tool(name="log_interaction")
def tool_log_interaction(
    question: str,
    answer: str,
    skill_ids: list[str] | None = None,
) -> str:
    """Append Q/A JSONL under profiles/<name>/interactions/."""
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    ids = skill_ids if skill_ids is not None else []
    path = append_interaction_record(
        name,
        question=question,
        answer=answer,
        skill_ids=ids,
    )
    return f"OK: appended to {path}\n"


@mcp.tool(name="suggest_skill_upgrade")
def tool_suggest_skill_upgrade(
    skill_id: str,
    proposed_status: str,
    rationale: str,
) -> str:
    """Suggest a status change (does not write YAML)."""
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    return (
        f"SUGGESTION only (no write) for profile {name!r}: "
        f"set {skill_id!r} -> {proposed_status!r}. "
        f"Reason: {rationale.strip()}\n"
    )


@mcp.tool(name="crystallize_method_draft")
def tool_crystallize_method_draft(
    project: str,
    body: str,
) -> str:
    """Write a human-editable method draft under profiles/.../methods/."""
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    path = write_method_draft(name, project, body)
    return f"OK: wrote {path}\n"


def main() -> None:
    """Run the MCP server on stdio (default)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
