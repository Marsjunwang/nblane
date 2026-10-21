"""OpenClaw memory corpus: render nblane profile data as read-only Markdown.

This is the "priming" half of the OpenClaw dual-memory design
(``docs/zh/architecture/ai-architecture.md``): profile files
are rendered into a derived Markdown corpus that OpenClaw's memory search can
index via ``memory.search.extraPaths``. The corpus is read-only output —
it is never a source of truth and is never recorded in ``git_backup``.

Goal privacy matches the agent-context contract used by
``core/context.py`` and the ``profile://goals`` MCP resource: private goals
never reach the rendered corpus. The North Star is always rendered in full —
its binary visibility gates only public artifacts, never agent/local context
(``docs/zh/guides/home.md``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from nblane.core.file_write import atomic_write_text
from nblane.core.io import profile_dir
from nblane.core.profile_text_views import render_goals_text, render_summary_text
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
    """Return the default corpus output directory.

    Resolved through :func:`openclaw_setup.state_dir` so
    ``NBLANE_OPENCLAW_PROFILE`` isolated setups (``~/.openclaw-<name>``)
    get their own corpus instead of sharing ``~/.openclaw``.
    """
    from nblane.core import openclaw_setup

    return openclaw_setup.state_dir() / "workspace" / "memory" / "nblane"


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


def _render_skill_tree_body(profile_name: str, pdir: Path) -> str:
    """Skill tree checklist; reuses the SKILL.md generated-block renderer."""
    body = _render_skill_tree_block(pdir)
    return f"# Skill tree: {profile_name}\n\n{body}\n"


def _render_goals_body(profile_name: str, pdir: Path) -> str:
    """Goals summary with the same privacy redaction as agent context.

    Shared with the ``profile://goals`` MCP resource via
    :func:`profile_text_views.render_goals_text`.
    """
    return render_goals_text(profile_name, pdir)


def _render_kanban_body(pdir: Path) -> str:
    """Copy the profile's kanban.md verbatim (it is already Markdown)."""
    return (pdir / "kanban.md").read_text(encoding="utf-8")


def _render_summary_body(profile_name: str, pdir: Path) -> str:
    """Profile summary: current goal, tree counts, preferences, kanban focus.

    Shared with the ``profile://summary`` MCP resource via
    :func:`profile_text_views.render_summary_text` (kept FastMCP-free so the
    corpus renderer stays a pure core module).
    """
    return render_summary_text(profile_name, pdir)


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
