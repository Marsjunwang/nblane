"""OpenClaw memory corpus: render nblane profile data as read-only Markdown.

This is the "priming" half of the OpenClaw dual-memory design
(``docs/zh/architecture/openclaw-deep-integration.md`` §4.1): profile files
are rendered into a derived Markdown corpus that OpenClaw's memory search can
index via ``memory.search.extraPaths``. The corpus is read-only output —
it is never a source of truth and is never recorded in ``git_backup``.

Goal privacy matches the agent-context contract used by
``core/context.py`` and the ``profile://goals`` MCP resource: private goals
never reach the rendered corpus. The North Star is always rendered in full —
its binary visibility gates only public artifacts, never agent/local context
(``docs/zh/dev/home-editing-starmap-design.md`` §1).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import yaml

from nblane.core.file_write import atomic_write_text
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
    profile_dir,
)
from nblane.core.profile_context import (
    north_star_context_from_identity,
    parse_identity_fields,
)
from nblane.core.status import STATUS_ICONS, count_nodes, lit_fraction
from nblane.core.sync import _render_skill_tree_block

SKILL_TREE_FILE = "skill-tree.md"
GOALS_FILE = "goals.md"
KANBAN_FILE = "kanban.md"
SUMMARY_FILE = "profile-summary.md"

CORPUS_FILES = (SKILL_TREE_FILE, GOALS_FILE, KANBAN_FILE, SUMMARY_FILE)

_HEADER_TEMPLATE = "<!-- source: nblane | generated: {ts} | do-not-edit -->"
_HEADER_RE = re.compile(
    r"^<!-- source: nblane \| generated: .* \| do-not-edit -->$"
)


def default_out_dir() -> Path:
    """Return the default corpus output directory."""
    return Path.home() / ".openclaw" / "workspace" / "memory" / "nblane"


@dataclass
class CorpusResult:
    """Outcome of one corpus render."""

    written: list[Path] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    removed: list[Path] = field(default_factory=list)
    out_dir: Path = field(default_factory=default_out_dir)


def _header(ts: str) -> str:
    return _HEADER_TEMPLATE.format(ts=ts)


def _timestamp(today: date | None) -> str:
    if today is not None:
        return today.isoformat()
    return datetime.now().isoformat(timespec="seconds")


def _strip_header_lines(text: str) -> str:
    """Drop generated-header lines so timestamp-only changes are ignored."""
    return "\n".join(
        line for line in text.splitlines() if not _HEADER_RE.match(line)
    )


def _is_own_artifact(path: Path) -> bool:
    """True when *path* starts with our generated do-not-edit header."""
    try:
        with open(path, encoding="utf-8") as f:
            first_line = f.readline().rstrip("\n")
    except OSError:
        return False
    return bool(_HEADER_RE.match(first_line))


def _stale_artifacts(target: Path, bodies: dict[str, str]) -> list[Path]:
    """Own generated files under *target* with no body in this render.

    Only files carrying the generated header count — anything else in the
    output directory is user content and is never reported or removed.
    """
    if not target.is_dir():
        return []
    return [
        path
        for path in sorted(target.glob("*.md"))
        if path.name not in bodies and _is_own_artifact(path)
    ]


def _load_agent_profile_dict(pdir: Path) -> dict:
    """Load agent-profile.yaml as a dict, or empty dict."""
    path = pdir / "agent-profile.yaml"
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _render_skill_tree_body(profile_name: str, pdir: Path) -> str:
    """Skill tree checklist; reuses the SKILL.md generated-block renderer."""
    body = _render_skill_tree_block(pdir)
    return f"# Skill tree: {profile_name}\n\n{body}\n"


def _render_goals_body(profile_name: str, pdir: Path) -> str:
    """Goals summary with the same privacy redaction as agent context.

    Mirrors the ``profile://goals`` MCP resource (``build_goals_text`` in
    ``mcp_server.py``): the North Star goes through
    ``north_star_context_from_identity(..., for_agent=True)`` and each goal
    through ``goal_for_agent_context``.
    """
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


def _render_kanban_body(pdir: Path) -> str:
    """Copy the profile's kanban.md verbatim (it is already Markdown)."""
    return (pdir / "kanban.md").read_text(encoding="utf-8")


def _render_summary_body(profile_name: str, pdir: Path) -> str:
    """Profile summary: current goal, tree counts, preferences, kanban focus.

    Core-level equivalent of ``build_summary_text`` in ``mcp_server.py``,
    kept here so the corpus renderer does not pull in FastMCP.
    """
    lines: list[str] = [f"# Profile summary: {profile_name}", ""]

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

    agent_profile = _load_agent_profile_dict(pdir)
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


def _render_bodies(
    profile_name: str,
    pdir: Path,
) -> tuple[dict[str, str], list[str]]:
    """Render all corpus bodies; missing sources are skipped with a reason."""
    bodies: dict[str, str] = {}
    skipped: list[str] = []

    if (pdir / "skill-tree.yaml").exists():
        bodies[SKILL_TREE_FILE] = _render_skill_tree_body(profile_name, pdir)
    else:
        skipped.append(f"{SKILL_TREE_FILE}: skill-tree.yaml not found")

    if (pdir / "goals.yaml").exists():
        bodies[GOALS_FILE] = _render_goals_body(profile_name, pdir)
    else:
        skipped.append(f"{GOALS_FILE}: goals.yaml not found")

    if (pdir / "kanban.md").exists():
        bodies[KANBAN_FILE] = _render_kanban_body(pdir)
    else:
        skipped.append(f"{KANBAN_FILE}: kanban.md not found")

    bodies[SUMMARY_FILE] = _render_summary_body(profile_name, pdir)
    return bodies, skipped


def render_profile_corpus(
    profile_name: str,
    out_dir: Path | None = None,
    *,
    today: date | None = None,
) -> CorpusResult:
    """Render the profile's Markdown corpus into *out_dir* atomically.

    Missing source files (e.g. no ``goals.yaml``) are skipped with a reason
    instead of failing the whole render. Stale artifacts — files carrying
    our generated header whose source disappeared since the last render —
    are deleted so removed sources never linger in agent memory. The corpus
    is a derived artifact: nothing is recorded in ``git_backup``.
    """
    pdir = profile_dir(profile_name)
    if not pdir.is_dir():
        raise FileNotFoundError(f"Profile {profile_name!r} not found: {pdir}")
    target = Path(out_dir) if out_dir is not None else default_out_dir()
    target.mkdir(parents=True, exist_ok=True)

    bodies, skipped = _render_bodies(profile_name, pdir)
    header = _header(_timestamp(today))
    result = CorpusResult(skipped=skipped, out_dir=target)
    for name in CORPUS_FILES:
        body = bodies.get(name)
        if body is None:
            continue
        path = target / name
        atomic_write_text(path, f"{header}\n\n{body}")
        result.written.append(path)
    for stale in _stale_artifacts(target, bodies):
        stale.unlink()
        result.removed.append(stale)
    return result


def check_corpus_drift(
    profile_name: str,
    out_dir: Path | None = None,
) -> list[str]:
    """Return corpus file names whose on-disk content differs from a render.

    The ``generated:`` timestamp in the header line is excluded from the
    comparison so re-rendering alone never counts as drift. Files that a
    fresh render would produce but that are missing on disk count as
    drifted; files skipped for missing sources are ignored — unless a
    generated artifact for them is still on disk, which counts as drift too
    (a fresh render would delete it). Stale artifacts whose name is not one
    of the current corpus files are reported the same way.
    """
    pdir = profile_dir(profile_name)
    if not pdir.is_dir():
        raise FileNotFoundError(f"Profile {profile_name!r} not found: {pdir}")
    target = Path(out_dir) if out_dir is not None else default_out_dir()

    bodies, _skipped = _render_bodies(profile_name, pdir)
    drifted: list[str] = []
    for name in CORPUS_FILES:
        body = bodies.get(name)
        if body is None:
            continue
        path = target / name
        if not path.exists():
            drifted.append(name)
            continue
        existing = _strip_header_lines(path.read_text(encoding="utf-8"))
        if existing.strip() != body.strip():
            drifted.append(name)
    for stale in _stale_artifacts(target, bodies):
        drifted.append(stale.name)
    return drifted
