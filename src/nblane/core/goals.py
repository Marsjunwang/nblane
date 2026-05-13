"""Current goal data model and privacy-aware projections."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from nblane.core import git_backup
from nblane.core.file_write import atomic_write_text
from nblane.core.paths import PROFILES_DIR
from nblane.core.profile_io import safe_profile_dir
from nblane.core.yaml_io import _load_yaml_dict

GOALS_FILENAME = "goals.yaml"
GOAL_STATUSES = ("active", "paused", "completed", "archived")
GOAL_UI_VISIBILITIES = ("visible", "discreet", "hidden", "private")
GOAL_SKILL_LINK_SOURCES = ("rule", "ai", "manual", "rule+ai")
DEFAULT_GOAL_STATUS = "active"
DEFAULT_GOAL_UI_VISIBILITY = "discreet"
DEFAULT_GOAL_SKILL_LINK_SOURCE = "manual"


def _clean_text(value: object) -> str:
    """Return a trimmed string for scalar YAML fields."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value).strip()
    return ""


def _clean_bool(value: object, default: bool) -> bool:
    """Normalize common YAML/user booleans with a stable default."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in ("1", "true", "yes", "on"):
            return True
        if raw in ("0", "false", "no", "off"):
            return False
    return default


def _clean_list(value: object) -> list[str]:
    """Normalize list-like text fields to a list of non-empty strings."""
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _clean_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _clean_status(value: object) -> str:
    """Normalize goal status."""
    raw = _clean_text(value).lower()
    return raw if raw in GOAL_STATUSES else DEFAULT_GOAL_STATUS


def _clean_ui_visibility(value: object) -> str:
    """Normalize goal UI visibility."""
    raw = _clean_text(value).lower()
    if raw == "public":
        raw = "visible"
    return (
        raw
        if raw in GOAL_UI_VISIBILITIES
        else DEFAULT_GOAL_UI_VISIBILITY
    )


def _clean_skill_link_source(value: object) -> str:
    """Normalize a goal-skill link provenance value."""
    raw = _clean_text(value).lower()
    return (
        raw
        if raw in GOAL_SKILL_LINK_SOURCES
        else DEFAULT_GOAL_SKILL_LINK_SOURCE
    )


def _clean_int(value: object, default: int = 0) -> int:
    """Normalize integer-ish YAML values."""
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _profile_path(name_or_dir: str | Path) -> Path:
    """Resolve a profile name or path to its profile directory."""
    if isinstance(name_or_dir, Path):
        return name_or_dir
    return safe_profile_dir(name_or_dir, PROFILES_DIR)


@dataclass
class GoalSkillLink:
    """A confirmed relationship between one goal and one skill node."""

    node_id: str
    label: str = ""
    source: str = DEFAULT_GOAL_SKILL_LINK_SOURCE
    score: int = 0
    rationale: str = ""

    @classmethod
    def from_dict(cls, raw: object) -> GoalSkillLink | None:
        """Build a normalized goal-skill link from raw YAML."""
        if not isinstance(raw, dict):
            return None
        node_id = _clean_text(raw.get("node_id") or raw.get("id"))
        if not node_id:
            return None
        return cls(
            node_id=node_id,
            label=_clean_text(raw.get("label")),
            source=_clean_skill_link_source(raw.get("source")),
            score=max(0, _clean_int(raw.get("score"), 0)),
            rationale=_clean_text(raw.get("rationale")),
        )

    def to_dict(self) -> dict:
        """Serialize the link with stable field order."""
        return {
            "node_id": self.node_id,
            "label": self.label,
            "source": _clean_skill_link_source(self.source),
            "score": max(0, _clean_int(self.score, 0)),
            "rationale": self.rationale,
        }


def _clean_skill_links(value: object) -> list[GoalSkillLink]:
    """Normalize a list of goal-skill link records."""
    if not isinstance(value, list):
        return []
    out: list[GoalSkillLink] = []
    seen: set[str] = set()
    for item in value:
        link = GoalSkillLink.from_dict(item)
        if link is None or link.node_id in seen:
            continue
        seen.add(link.node_id)
        out.append(link)
    return out


@dataclass
class Goal:
    """One stage goal in profiles/<name>/goals.yaml."""

    id: str
    title: str = ""
    label: str = ""
    status: str = DEFAULT_GOAL_STATUS
    start: str = ""
    target: str = ""
    ui_visibility: str = DEFAULT_GOAL_UI_VISIBILITY
    include_in_agent_context: bool = True
    include_in_public_output: bool = False
    summary: str = ""
    alignment: str = ""
    target_skills: list[str] = field(default_factory=list)
    skill_links: list[GoalSkillLink] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    focus: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    task_refs: list[str] = field(default_factory=list)
    output_refs: list[str] = field(default_factory=list)
    notes: str = ""

    @classmethod
    def from_dict(cls, raw: object) -> Goal | None:
        """Build a normalized goal from raw YAML."""
        if not isinstance(raw, dict):
            return None
        goal_id = _clean_text(raw.get("id"))
        if not goal_id:
            return None
        visibility = _clean_ui_visibility(raw.get("ui_visibility"))
        include_agent = _clean_bool(
            raw.get("include_in_agent_context"),
            True,
        )
        include_public = _clean_bool(
            raw.get("include_in_public_output"),
            False,
        )
        if visibility == "private":
            include_agent = False
            include_public = False
        return cls(
            id=goal_id,
            title=_clean_text(raw.get("title")),
            label=_clean_text(raw.get("label")),
            status=_clean_status(raw.get("status")),
            start=_clean_text(raw.get("start")),
            target=_clean_text(raw.get("target")),
            ui_visibility=visibility,
            include_in_agent_context=include_agent,
            include_in_public_output=include_public,
            summary=_clean_text(raw.get("summary")),
            alignment=_clean_text(raw.get("alignment")),
            target_skills=_clean_list(raw.get("target_skills")),
            skill_links=_clean_skill_links(raw.get("skill_links")),
            success_criteria=_clean_list(raw.get("success_criteria")),
            focus=_clean_list(raw.get("focus")),
            evidence_refs=_clean_list(raw.get("evidence_refs")),
            task_refs=_clean_list(raw.get("task_refs")),
            output_refs=_clean_list(raw.get("output_refs")),
            notes=_clean_text(raw.get("notes")),
        )

    def to_dict(self) -> dict:
        """Serialize a goal with stable field order."""
        include_agent = (
            False
            if self.ui_visibility == "private"
            else bool(self.include_in_agent_context)
        )
        include_public = (
            False
            if self.ui_visibility == "private"
            else bool(self.include_in_public_output)
        )
        return {
            "id": self.id,
            "title": self.title,
            "label": self.label,
            "status": _clean_status(self.status),
            "start": self.start,
            "target": self.target,
            "ui_visibility": _clean_ui_visibility(self.ui_visibility),
            "include_in_agent_context": include_agent,
            "include_in_public_output": include_public,
            "summary": self.summary,
            "alignment": self.alignment,
            "target_skills": list(self.target_skills),
            "skill_links": [link.to_dict() for link in self.skill_links],
            "success_criteria": list(self.success_criteria),
            "focus": list(self.focus),
            "evidence_refs": list(self.evidence_refs),
            "task_refs": list(self.task_refs),
            "output_refs": list(self.output_refs),
            "notes": self.notes,
        }


@dataclass
class GoalBook:
    """Profile-scoped goal collection."""

    schema_version: str = "1.0"
    profile: str = ""
    updated: str = ""
    current_goal_id: str = ""
    goals: list[Goal] = field(default_factory=list)

    @classmethod
    def empty(cls, profile: str = "") -> GoalBook:
        """Return an empty goal book."""
        return cls(profile=profile)

    @classmethod
    def from_dict(
        cls,
        raw: object,
        *,
        profile: str = "",
    ) -> GoalBook:
        """Build a normalized goal book from raw YAML."""
        if not isinstance(raw, dict):
            return cls.empty(profile=profile)
        goals = [
            goal
            for goal in (
                Goal.from_dict(item)
                for item in (raw.get("goals") or [])
            )
            if goal is not None
        ]
        return cls(
            schema_version=_clean_text(raw.get("schema_version")) or "1.0",
            profile=_clean_text(raw.get("profile")) or profile,
            updated=_clean_text(raw.get("updated")),
            current_goal_id=_clean_text(raw.get("current_goal_id")),
            goals=goals,
        )

    def to_dict(self) -> dict:
        """Serialize a goal book with stable field order."""
        return {
            "schema_version": self.schema_version or "1.0",
            "profile": self.profile,
            "updated": self.updated,
            "current_goal_id": self.current_goal_id,
            "goals": [goal.to_dict() for goal in self.goals],
        }

    def by_id(self) -> dict[str, Goal]:
        """Return id -> goal lookup."""
        return {goal.id: goal for goal in self.goals if goal.id}

    def current(self) -> Goal | None:
        """Return the primary non-archived goal, if any.

        ``current`` is kept as the compatibility name for callers that still
        treat the primary stage goal as a single current goal.
        """
        return self.primary()

    def primary(self) -> Goal | None:
        """Return the primary non-archived goal, if any."""
        if not self.current_goal_id:
            return None
        goal = self.by_id().get(self.current_goal_id)
        if goal is None or goal.status == "archived":
            return None
        return goal

    def active_goals(self) -> list[Goal]:
        """Return goals currently active in this stage."""
        return [goal for goal in self.goals if goal.status == "active"]

    def set_primary(self, goal_id: str) -> bool:
        """Set the primary goal pointer when the id exists and is usable."""
        goal = self.by_id().get(goal_id)
        if goal is None or goal.status == "archived":
            return False
        self.current_goal_id = goal.id
        return True


def _default_raw(profile: str = "") -> dict:
    """Return the raw empty goal book shape."""
    return {
        "schema_version": "1.0",
        "profile": profile,
        "updated": "",
        "current_goal_id": "",
        "goals": [],
    }


def load_goal_book(name_or_dir: str | Path) -> GoalBook:
    """Load and normalize goals.yaml; missing files are empty."""
    pdir = _profile_path(name_or_dir)
    raw = _load_yaml_dict(pdir / GOALS_FILENAME)
    if raw is None:
        return GoalBook.empty(profile=pdir.name)
    return GoalBook.from_dict(raw, profile=pdir.name)


def load_goal_book_raw(name_or_dir: str | Path) -> dict:
    """Load goals.yaml as a normalized raw mapping."""
    return load_goal_book(name_or_dir).to_dict()


def save_goal_book(name: str, data: dict | GoalBook) -> None:
    """Persist goals.yaml with today's updated date."""
    book = data if isinstance(data, GoalBook) else GoalBook.from_dict(data)
    if not book.profile:
        book.profile = name
    book.updated = date.today().isoformat()
    path = safe_profile_dir(name, PROFILES_DIR) / GOALS_FILENAME
    body = yaml.dump(
        book.to_dict(),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    atomic_write_text(path, body)
    git_backup.record_change(
        [path],
        action=f"update {name}/goals.yaml",
    )


def current_goal(name_or_dir: str | Path) -> Goal | None:
    """Return the profile's current goal, if any."""
    return load_goal_book(name_or_dir).current()


def goal_for_ui(goal: Goal | None) -> dict[str, object] | None:
    """Return a privacy-safe UI projection for a goal."""
    if goal is None:
        return None
    visibility = _clean_ui_visibility(goal.ui_visibility)
    if visibility == "private":
        return None
    if visibility == "hidden":
        return {
            "id": goal.id,
            "visibility": visibility,
            "status": goal.status,
            "is_set": True,
        }
    if visibility == "discreet":
        return {
            "id": goal.id,
            "visibility": visibility,
            "label": goal.label or "Stage goal",
            "status": goal.status,
            "target": goal.target,
        }
    return {
        "id": goal.id,
        "visibility": visibility,
        "title": goal.title,
        "label": goal.label,
        "status": goal.status,
        "start": goal.start,
        "target": goal.target,
        "summary": goal.summary,
        "alignment": goal.alignment,
        "focus": list(goal.focus[:3]),
        "target_skills": list(goal.target_skills),
        "skill_links": [link.to_dict() for link in goal.skill_links],
        "success_criteria": list(goal.success_criteria),
    }


def goal_for_agent_context(goal: Goal | None) -> str:
    """Return goal text allowed for agent/MCP/AI context."""
    if goal is None:
        return ""
    if goal.ui_visibility == "private":
        return ""
    if not goal.include_in_agent_context:
        return ""

    lines: list[str] = []
    head = goal.title or goal.label or goal.id
    lines.append(f"- id: {goal.id}")
    lines.append(f"- title: {head}")
    if goal.label and goal.label != head:
        lines.append(f"- label: {goal.label}")
    lines.append(f"- status: {goal.status}")
    if goal.start:
        lines.append(f"- start: {goal.start}")
    if goal.target:
        lines.append(f"- target: {goal.target}")
    if goal.summary:
        lines.append(f"- summary: {goal.summary}")
    if goal.alignment:
        lines.append(f"- north star alignment: {goal.alignment}")
    if goal.target_skills:
        lines.append("- target skills: " + ", ".join(goal.target_skills))
    if goal.skill_links:
        lines.append("- confirmed skill links:")
        for link in goal.skill_links:
            label = f" — {link.label}" if link.label else ""
            src = f" [{link.source}]" if link.source else ""
            lines.append(f"  - {link.node_id}{label}{src}")
            if link.rationale:
                lines.append(f"    rationale: {link.rationale}")
    if goal.success_criteria:
        lines.append("- success criteria:")
        lines.extend(f"  - {item}" for item in goal.success_criteria)
    if goal.focus:
        lines.append("- focus:")
        lines.extend(f"  - {item}" for item in goal.focus)
    if goal.notes:
        lines.append(f"- notes: {goal.notes}")
    return "\n".join(lines)


def goal_for_public_output(goal: Goal | None) -> str:
    """Return goal text allowed for public output; disabled in P0."""
    return ""
