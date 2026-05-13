"""Context-source options for Gap Analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from nblane.core.goals import current_goal, goal_for_agent_context
from nblane.core.io import KANBAN_DOING, KANBAN_QUEUE, parse_kanban
from nblane.core.kanban_ai import format_kanban_task_for_ai
from nblane.core.kanban_io import ensure_kanban_task_ids


@dataclass(frozen=True)
class GapContextOption:
    """One privacy-safe context option for gap analysis."""

    kind: str
    id: str
    label: str
    body: str = ""
    refs: dict[str, list[str]] = field(default_factory=dict)
    privacy_state: str = ""

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.id}"


def _profile_name(profile: str | Path) -> str:
    return profile.name if isinstance(profile, Path) else str(profile)


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _goal_option(profile: str | Path) -> GapContextOption | None:
    goal = current_goal(profile)
    body = goal_for_agent_context(goal)
    if goal is None or not body.strip():
        return None
    label = goal.title or goal.label or goal.id
    return GapContextOption(
        kind="current_goal",
        id=goal.id,
        label=label,
        body=body,
        refs={"goal_refs": [goal.id]},
        privacy_state="agent_context",
    )


def _kanban_options(profile: str | Path) -> list[GapContextOption]:
    profile_name = _profile_name(profile)
    sections = ensure_kanban_task_ids(parse_kanban(profile), profile_name)
    out: list[GapContextOption] = []
    for section in (KANBAN_DOING, KANBAN_QUEUE):
        for task in sections.get(section, []) or []:
            title = _clean_text(getattr(task, "title", ""))
            task_id = _clean_text(getattr(task, "id", ""))
            if not title or not task_id:
                continue
            out.append(
                GapContextOption(
                    kind="kanban_task",
                    id=task_id,
                    label=f"{section}: {title}",
                    body=format_kanban_task_for_ai(task),
                    refs={"task_refs": [task_id], "kanban_sections": [section]},
                    privacy_state="profile_private",
                )
            )
    return out


def gap_context_options(profile: str | Path) -> list[GapContextOption]:
    """Return manual, current-goal, and active kanban context options."""
    options = [
        GapContextOption(
            kind="manual",
            id="manual",
            label="Manual input",
            refs={},
            privacy_state="manual",
        )
    ]
    goal = _goal_option(profile)
    if goal is not None:
        options.append(goal)
    options.extend(_kanban_options(profile))
    return options


def default_gap_context_key(
    options: list[GapContextOption],
    previous_key: str = "",
) -> str:
    """Pick a stable default option key for the Gap page."""
    keys = {option.key for option in options}
    if previous_key in keys:
        return previous_key
    for kind in ("kanban_task", "current_goal", "manual"):
        for option in options:
            if option.kind == kind:
                return option.key
    return options[0].key if options else "manual:manual"

