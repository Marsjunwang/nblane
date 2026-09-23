"""Habit-plan templates: built-in catalog plus per-profile usage history.

Built-ins ship as package data (``core/data/habit_plan_templates.yaml``,
loaded ``__file__``-relative like ``local_dict.py``). A template
instantiates into a ``kind=habit-plan`` project case in project-board.yaml
with a ``time_range`` from start + ``duration_days``, milestone dates
derived from ``offset_days``, and an explicit ``habit_id`` link — so the
projects-board aggregation renders it as a habit lane immediately.

Usage history lives in ``profiles/<name>/plan-templates.yaml`` (a small
profile file like activity-log.yaml): every instantiation records one
entry, de-duplicated by template id, most recent first. All writes go
through the profile write lock + atomic write + optional snapshot
re-check, same contract as ``activity_log.save``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

import yaml

from nblane.core import git_backup
from nblane.core.activity_log import HabitTarget
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_state import FileSnapshot, assert_unchanged
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_io import profile_dir

PLAN_TEMPLATES_FILENAME = "plan-templates.yaml"
_BUILTIN_PATH = (
    Path(__file__).resolve().parent / "data" / "habit_plan_templates.yaml"
)


def _clean_text(value: object) -> str:
    """Return a trimmed string representation."""
    return str(value or "").strip()


@dataclass
class PlanMilestone:
    """One template milestone: a hint plus its offset from the plan start."""

    title: str
    offset_days: int = 0

    @classmethod
    def from_dict(cls, raw: object) -> "PlanMilestone":
        """Build from a YAML/JSON mapping."""
        if not isinstance(raw, Mapping):
            return cls(title="")
        try:
            offset = max(int(raw.get("offset_days") or 0), 0)
        except (TypeError, ValueError):
            offset = 0
        return cls(title=_clean_text(raw.get("title")), offset_days=offset)

    def to_dict(self) -> dict[str, object]:
        """Serialize for YAML/JSON output."""
        return {"title": self.title, "offset_days": self.offset_days}


@dataclass
class PlanTemplate:
    """One habit-plan template (built-in or inline)."""

    id: str
    title: str
    summary: str = ""
    duration_days: int = 30
    habit_title: str = ""
    habit_kind: str = "health"
    cadence: str = "daily"
    target: HabitTarget = field(default_factory=HabitTarget)
    milestones: list[PlanMilestone] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: object) -> "PlanTemplate":
        """Build from a YAML/JSON mapping."""
        if not isinstance(raw, Mapping):
            return cls(id="", title="")
        habit = raw.get("habit")
        habit_map = habit if isinstance(habit, Mapping) else {}
        try:
            duration = int(raw.get("duration_days") or 30)
        except (TypeError, ValueError):
            duration = 30
        return cls(
            id=_clean_text(raw.get("id")),
            title=_clean_text(raw.get("title")),
            summary=_clean_text(raw.get("summary")),
            duration_days=max(duration, 1),
            habit_title=_clean_text(habit_map.get("title") or raw.get("title")),
            habit_kind=_clean_text(habit_map.get("kind")) or "health",
            cadence=_clean_text(habit_map.get("cadence")) or "daily",
            target=HabitTarget.from_dict(habit_map.get("target")),
            milestones=[
                PlanMilestone.from_dict(item)
                for item in (raw.get("milestones") or [])
                if isinstance(item, Mapping)
            ],
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize for JSON API output."""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "duration_days": self.duration_days,
            "habit": {
                "title": self.habit_title,
                "kind": self.habit_kind,
                "cadence": self.cadence,
                "target": self.target.to_dict(),
            },
            "milestones": [milestone.to_dict() for milestone in self.milestones],
            "builtin": self.builtin,
        }

    @property
    def builtin(self) -> bool:
        """True for package-shipped templates (``plan:`` id prefix)."""
        return self.id.startswith("plan:")


def load_builtin_templates() -> list[PlanTemplate]:
    """Load the package-shipped habit-plan templates."""
    raw = yaml.safe_load(_BUILTIN_PATH.read_text(encoding="utf-8"))
    items = raw.get("templates") if isinstance(raw, Mapping) else None
    return [
        PlanTemplate.from_dict(item)
        for item in (items or [])
        if isinstance(item, Mapping) and _clean_text(item.get("id"))
    ]


def builtin_template_index() -> dict[str, PlanTemplate]:
    """Return template id -> built-in template."""
    return {template.id: template for template in load_builtin_templates()}


def _history_path(name_or_dir: str | Path) -> Path:
    """Resolve the profile's plan-templates.yaml path."""
    if isinstance(name_or_dir, Path):
        return name_or_dir / PLAN_TEMPLATES_FILENAME
    return profile_dir(str(name_or_dir)) / PLAN_TEMPLATES_FILENAME


def load_plan_history(name_or_dir: str | Path) -> list[dict[str, Any]]:
    """Load the profile's template usage history (most recent first)."""
    path = _history_path(name_or_dir)
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        return []
    used = raw.get("used") or []
    return [
        dict(item)
        for item in used
        if isinstance(item, Mapping) and _clean_text(item.get("template_id"))
    ]


def record_plan_usage(
    name_or_dir: str | Path,
    entry: Mapping[str, Any],
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> list[dict[str, Any]]:
    """Record one template instantiation in the profile history.

    Entries are de-duplicated by ``template_id`` (latest wins) and stored
    most recent first. The write holds the plan-templates.yaml lock and,
    when *expected_snapshot* is given, re-checks it inside the lock,
    raising ``file_state.FileConflictError`` on mismatch.
    """
    path = _history_path(name_or_dir)
    with locked_profile_write(path.parent, path.name):
        if expected_snapshot is not None:
            assert_unchanged(path, expected_snapshot, label=path.name)
        history = load_plan_history(name_or_dir)
        clean = {
            "template_id": _clean_text(entry.get("template_id")),
            "title": _clean_text(entry.get("title")),
            "used_at": _clean_text(entry.get("used_at"))
            or datetime.now().isoformat(timespec="seconds"),
            "project_id": _clean_text(entry.get("project_id")),
            "habit_id": _clean_text(entry.get("habit_id")),
        }
        history = [
            item
            for item in history
            if item.get("template_id") != clean["template_id"]
        ]
        history.insert(0, clean)
        profile = path.parent.name
        header = (
            f"# Habit-plan template usage for {profile}\n"
            "# Written by the plan-templates instantiate flow; "
            "most recent first, de-duplicated by template_id.\n\n"
        )
        body = yaml.dump(
            {
                "schema_version": "1.0",
                "profile": profile,
                "updated": date.today().isoformat(),
                "used": history,
            },
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, header + body)
    git_backup.record_change(
        [path],
        action=f"update {path.parent.name}/{path.name}",
    )
    return history


def plan_case_fields(
    template: PlanTemplate,
    *,
    title: str = "",
    start: date | None = None,
) -> dict[str, Any]:
    """Derive project-case fields from a template (pure, no I/O).

    ``time_range`` is ``start`` to the inclusive last day
    (``start + duration_days - 1``); milestone dates are
    ``start + offset_days``.
    """
    start = start or date.today()
    end = start + timedelta(days=template.duration_days - 1)
    return {
        "title": _clean_text(title) or template.title,
        "kind": "habit-plan",
        "time_range": f"{start.isoformat()}/{end.isoformat()}",
        "summary": template.summary,
        "milestones": [
            {
                "id": f"milestone:{index + 1}",
                "title": milestone.title,
                "status": "planned",
                "date": (start + timedelta(days=milestone.offset_days)).isoformat(),
            }
            for index, milestone in enumerate(template.milestones)
            if milestone.title
        ],
    }


__all__ = [
    "PLAN_TEMPLATES_FILENAME",
    "PlanMilestone",
    "PlanTemplate",
    "builtin_template_index",
    "load_builtin_templates",
    "load_plan_history",
    "plan_case_fields",
    "record_plan_usage",
]
