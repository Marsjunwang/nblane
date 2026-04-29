"""Profile-scoped activity and habit tracking."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

import yaml

from nblane.core import git_backup
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_io import profile_dir

ACTIVITY_LOG_FILENAME = "activity-log.yaml"
ACTIVITY_HABIT_KINDS = (
    "health",
    "learning",
    "practice",
    "reflection",
    "maintenance",
    "avoid",
)


class ActivityLogParseError(ValueError):
    """Raised when activity-log.yaml exists but is invalid YAML."""

    def __init__(self, path: Path, error: object):
        """Build an error with the failing path and YAML parser detail."""
        self.path = path
        self.error = error
        super().__init__(f"Could not parse {path}: {error}")


def _clean_text(value: object) -> str:
    """Return a trimmed string representation."""
    if value is None:
        return ""
    return str(value).strip()


def _dedupe_texts(values: list[str]) -> list[str]:
    """De-duplicate strings case-insensitively while preserving order."""
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = _clean_text(value)
        if not clean:
            continue
        key = clean.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return out


def _normalize_text_list(value: object) -> list[str]:
    """Coerce scalar or sequence values into a stable string list."""
    if value is None:
        return []
    if isinstance(value, str):
        parts = value.split(",") if "," in value else [value]
        return _dedupe_texts(parts)
    if isinstance(value, (list, tuple, set)):
        out: list[str] = []
        for item in value:
            if isinstance(item, str):
                out.extend(
                    item.split(",") if "," in item else [item]
                )
                continue
            clean = _clean_text(item)
            if clean:
                out.append(clean)
        return _dedupe_texts(out)
    clean = _clean_text(value)
    return [clean] if clean else []


def _has_non_comment_yaml_content(text: str) -> bool:
    """Return True when YAML text contains meaningful non-comment content."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return True
    return False


def _load_activity_yaml(path: Path) -> dict | None:
    """Load and validate activity-log YAML top-level shape."""
    text = path.read_text(encoding="utf-8")
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ActivityLogParseError(path, exc) from exc
    if raw is None:
        if _has_non_comment_yaml_content(text):
            raise ActivityLogParseError(
                path,
                ValueError("activity-log.yaml must be a YAML mapping"),
            )
        return None
    if not isinstance(raw, dict):
        raise ActivityLogParseError(
            path,
            ValueError("activity-log.yaml must be a YAML mapping"),
        )
    return raw


def _parse_nonnegative_float(value: object, default: float = 0.0) -> float:
    """Parse a value as a finite non-negative float."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return max(number, 0.0)


def _normalize_metrics(value: object) -> dict[str, object]:
    """Keep scalar metric values with non-empty keys."""
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, object] = {}
    for key, metric_value in value.items():
        clean_key = _clean_text(key)
        if not clean_key:
            continue
        if isinstance(metric_value, float) and not math.isfinite(
            metric_value
        ):
            continue
        if isinstance(metric_value, (str, int, float, bool)):
            out[clean_key] = metric_value
    return out


def _slugify(value: str) -> str:
    """Build a simple identifier from a free-form title."""
    chars: list[str] = []
    last_sep = False
    for char in value.strip().lower():
        if char.isalnum():
            chars.append(char)
            last_sep = False
            continue
        if not last_sep:
            chars.append("_")
            last_sep = True
    return "".join(chars).strip("_")


def _coerce_date_text(value: object) -> str:
    """Normalize date-like values to YYYY-MM-DD when possible."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = _clean_text(value)
    if not text:
        return ""
    candidate = text.replace("/", "-")
    if "T" in candidate:
        candidate = candidate.split("T", 1)[0]
    if " " in candidate:
        candidate = candidate.split(" ", 1)[0]
    if len(candidate) >= 10:
        candidate = candidate[:10]
    try:
        return date.fromisoformat(candidate).isoformat()
    except ValueError:
        return text


def _parse_date(value: object) -> date | None:
    """Parse a date-like value when possible."""
    text = _coerce_date_text(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _parse_week_start(value: object) -> str:
    """Normalize a week identifier to the ISO week's Monday date."""
    if isinstance(value, datetime):
        monday = value.date() - timedelta(days=value.weekday())
        return monday.isoformat()
    if isinstance(value, date):
        monday = value - timedelta(days=value.weekday())
        return monday.isoformat()
    text = _clean_text(value)
    if not text:
        return ""
    if "-W" in text:
        year_text, week_text = text.split("-W", 1)
        week_digits = "".join(
            char for char in week_text if char.isdigit()
        )
        try:
            monday = date.fromisocalendar(
                int(year_text),
                int(week_digits),
                1,
            )
        except ValueError:
            return ""
        return monday.isoformat()
    day = _parse_date(text)
    if day is None:
        return ""
    monday = day - timedelta(days=day.weekday())
    return monday.isoformat()


def _week_end_from_start(week_start: str) -> str:
    """Return the ISO week end for a Monday ISO date."""
    start_day = _parse_date(week_start)
    if start_day is None:
        return ""
    return (start_day + timedelta(days=6)).isoformat()


def _date_range(
    start: str | date | None,
    end: str | date | None,
) -> tuple[date, date]:
    """Normalize a summary date window."""
    end_date = date.today() if end is None else date.fromisoformat(
        _coerce_date_text(end)
    )
    if start is None:
        start_date = end_date - timedelta(days=6)
    else:
        start_date = date.fromisoformat(_coerce_date_text(start))
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    return start_date, end_date


def _activity_log_path(name_or_dir: str | Path) -> Path:
    """Resolve a profile name, directory, or file path."""
    if isinstance(name_or_dir, Path):
        if name_or_dir.suffix in (".yaml", ".yml"):
            return name_or_dir
        return name_or_dir / ACTIVITY_LOG_FILENAME

    raw = name_or_dir.strip()
    path = Path(raw)
    if (
        path.suffix in (".yaml", ".yml")
        or "/" in raw
        or raw.startswith(".")
        or path.exists()
    ):
        return path if path.suffix else path / ACTIVITY_LOG_FILENAME
    return profile_dir(raw) / ACTIVITY_LOG_FILENAME


@dataclass
class HabitTarget:
    """Target quantity for one habit cadence."""

    count: float = 1.0
    unit: str = ""

    @classmethod
    def from_dict(cls, raw: object) -> "HabitTarget":
        """Build a target from YAML data."""
        if isinstance(raw, str):
            text = _clean_text(raw).lower()
            match = None
            for token in ("x/", "times/"):
                if token in text:
                    left, _right = text.split(token, 1)
                    match = left
                    break
            if match is None and "/" in text:
                match = text.split("/", 1)[0]
            if match is not None:
                try:
                    count = max(float(match.strip()), 0.0)
                except (TypeError, ValueError):
                    count = 1.0
                return cls(count=count, unit="session")
            try:
                count = max(float(text), 0.0)
            except (TypeError, ValueError):
                count = 1.0
            return cls(count=count, unit="")
        if not isinstance(raw, dict):
            return cls()
        count_raw = raw.get("count", 1.0)
        try:
            count = max(float(count_raw), 0.0)
        except (TypeError, ValueError):
            count = 1.0
        return cls(
            count=count,
            unit=_clean_text(raw.get("unit")),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the target for YAML output."""
        out: dict[str, object] = {"count": self.count}
        if self.unit:
            out["unit"] = self.unit
        return out


@dataclass
class Habit:
    """One user-defined repeated habit or ritual."""

    id: str
    title: str = ""
    kind: str = "practice"
    cadence: str = "daily"
    target: HabitTarget = field(default_factory=HabitTarget)
    tags: list[str] = field(default_factory=list)
    skill_refs: list[str] = field(default_factory=list)
    review_policy: str = "weekly_rollup"
    notes: str = ""

    @classmethod
    def from_dict(cls, raw: object) -> "Habit":
        """Build a habit from YAML data."""
        if isinstance(raw, str):
            title = _clean_text(raw)
            habit_id = _slugify(title) or title
            return cls(id=habit_id, title=title)
        if not isinstance(raw, dict):
            return cls(id="")
        habit_id = _clean_text(
            raw.get("id") or raw.get("habit") or raw.get("name")
        )
        title = _clean_text(raw.get("title") or raw.get("label"))
        if not habit_id:
            habit_id = _slugify(title)
        if not title and habit_id:
            title = habit_id.replace("_", " ")
        cadence = _clean_text(raw.get("cadence")) or _infer_cadence_from_target(
            raw.get("target")
        )
        return cls(
            id=habit_id,
            title=title,
            kind=_clean_text(raw.get("kind")) or "practice",
            cadence=cadence or "daily",
            target=HabitTarget.from_dict(raw.get("target")),
            tags=_normalize_text_list(raw.get("tags") or raw.get("tag")),
            skill_refs=_normalize_text_list(raw.get("skill_refs")),
            review_policy=(
                _clean_text(raw.get("review_policy"))
                or "weekly_rollup"
            ),
            notes=_clean_text(raw.get("notes") or raw.get("note")),
        )

    def merged(self, other: "Habit") -> "Habit":
        """Merge duplicate habit definitions."""
        return Habit(
            id=self.id or other.id,
            title=other.title or self.title,
            kind=other.kind or self.kind,
            cadence=other.cadence or self.cadence,
            target=other.target if other.target.count else self.target,
            tags=_dedupe_texts(self.tags + other.tags),
            skill_refs=_dedupe_texts(
                self.skill_refs + other.skill_refs
            ),
            review_policy=other.review_policy or self.review_policy,
            notes=other.notes or self.notes,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize a habit for YAML output."""
        out: dict[str, object] = {"id": self.id}
        if self.title:
            out["title"] = self.title
        if self.kind:
            out["kind"] = self.kind
        if self.cadence:
            out["cadence"] = self.cadence
        if self.target.count != 1.0 or self.target.unit:
            out["target"] = self.target.to_dict()
        if self.tags:
            out["tags"] = list(self.tags)
        if self.skill_refs:
            out["skill_refs"] = list(self.skill_refs)
        if self.review_policy and self.review_policy != "weekly_rollup":
            out["review_policy"] = self.review_policy
        if self.notes:
            out["notes"] = self.notes
        return out


@dataclass
class Checkin:
    """One activity check-in row."""

    date: str
    summary: str = ""
    habits: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    id: str = ""
    habit_id: str = ""
    count: float = 1.0
    unit: str = ""
    workout_type: str = ""
    duration_min: float = 0.0
    intensity: str = ""
    metrics: dict[str, object] = field(default_factory=dict)
    links: list[str] = field(default_factory=list)
    related_learning: list[str] = field(default_factory=list)
    related_kanban: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: object) -> "Checkin":
        """Build a check-in from YAML data."""
        if not isinstance(raw, dict):
            return cls(date="")
        habits = _normalize_text_list(
            raw.get("habits")
            or raw.get("habit")
            or raw.get("habit_ids")
        )
        habit_id = _clean_text(raw.get("habit_id"))
        if habit_id:
            habits = _dedupe_texts([habit_id] + habits)
        summary = _clean_text(
            raw.get("summary") or raw.get("text")
        )
        notes = _clean_text(raw.get("notes") or raw.get("note"))
        count_raw = raw.get("count", 1.0)
        try:
            count = max(float(count_raw), 0.0)
        except (TypeError, ValueError):
            count = 1.0
        return cls(
            date=_coerce_date_text(
                raw.get("date")
                or raw.get("day")
                or raw.get("created_at")
                or raw.get("timestamp")
            ),
            summary=summary,
            habits=habits,
            tags=_normalize_text_list(raw.get("tags") or raw.get("tag")),
            notes=notes,
            id=_clean_text(raw.get("id")),
            habit_id=habit_id or (habits[0] if habits else ""),
            count=count or 1.0,
            unit=_clean_text(raw.get("unit")),
            workout_type=_clean_text(raw.get("workout_type")),
            duration_min=_parse_nonnegative_float(
                raw.get("duration_min")
            ),
            intensity=_clean_text(raw.get("intensity")),
            metrics=_normalize_metrics(raw.get("metrics")),
            links=_normalize_text_list(
                raw.get("links") or raw.get("urls") or raw.get("url")
            ),
            related_learning=_normalize_text_list(
                raw.get("related_learning")
            ),
            related_kanban=_normalize_text_list(
                raw.get("related_kanban")
            ),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize a check-in row for YAML output."""
        out: dict[str, object] = {"date": self.date}
        if self.id:
            out["id"] = self.id
        if self.habit_id:
            out["habit_id"] = self.habit_id
        if self.habits:
            out["habits"] = list(self.habits)
        if self.count != 1.0:
            out["count"] = self.count
        if self.unit:
            out["unit"] = self.unit
        if self.workout_type:
            out["workout_type"] = self.workout_type
        duration_min = _parse_nonnegative_float(self.duration_min)
        if duration_min:
            out["duration_min"] = duration_min
        if self.intensity:
            out["intensity"] = self.intensity
        metrics = _normalize_metrics(self.metrics)
        if metrics:
            out["metrics"] = metrics
        if self.links:
            out["links"] = list(self.links)
        if self.summary:
            out["summary"] = self.summary
        if self.tags:
            out["tags"] = list(self.tags)
        if self.notes:
            out["notes"] = self.notes
        if self.related_learning:
            out["related_learning"] = list(self.related_learning)
        if self.related_kanban:
            out["related_kanban"] = list(self.related_kanban)
        return out


ActivityCheckin = Checkin


@dataclass
class WeeklySummary:
    """Optional narrative rollup for one week."""

    week_start: str
    week_end: str = ""
    summary: str = ""
    wins: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(
        cls,
        raw: object,
        *,
        key_hint: str = "",
    ) -> "WeeklySummary":
        """Build a WeeklySummary from a mapping or scalar value."""
        if isinstance(raw, str):
            week_start = _parse_week_start(key_hint)
            return cls(
                week_start=week_start,
                week_end=_week_end_from_start(week_start),
                summary=_clean_text(raw),
            )
        if not isinstance(raw, dict):
            return cls(week_start="")
        week_start = _parse_week_start(
            raw.get("week_start")
            or raw.get("week")
            or raw.get("start")
            or key_hint
        )
        week_end = _coerce_date_text(
            raw.get("week_end") or raw.get("end")
        )
        if not week_end and week_start:
            week_end = _week_end_from_start(week_start)
        return cls(
            week_start=week_start,
            week_end=week_end,
            summary=_clean_text(raw.get("summary")),
            wins=_normalize_text_list(raw.get("wins")),
            blockers=_normalize_text_list(
                raw.get("blockers") or raw.get("risks")
            ),
            tags=_normalize_text_list(raw.get("tags") or raw.get("tag")),
        )

    def merged(self, other: "WeeklySummary") -> "WeeklySummary":
        """Merge two weekly summaries for the same week."""
        return WeeklySummary(
            week_start=self.week_start or other.week_start,
            week_end=other.week_end or self.week_end,
            summary=other.summary or self.summary,
            wins=_dedupe_texts(self.wins + other.wins),
            blockers=_dedupe_texts(self.blockers + other.blockers),
            tags=_dedupe_texts(self.tags + other.tags),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize a weekly summary for YAML output."""
        out: dict[str, object] = {"week_start": self.week_start}
        if self.week_end:
            out["week_end"] = self.week_end
        if self.summary:
            out["summary"] = self.summary
        if self.wins:
            out["wins"] = list(self.wins)
        if self.blockers:
            out["blockers"] = list(self.blockers)
        if self.tags:
            out["tags"] = list(self.tags)
        return out


@dataclass
class ActivityLog:
    """Profile-level activity log."""

    profile: str = ""
    updated: str = ""
    habits: list[Habit] = field(default_factory=list)
    checkins: list[Checkin] = field(default_factory=list)
    weekly_summaries: list[WeeklySummary] = field(
        default_factory=list
    )
    warnings: list[str] = field(default_factory=list, repr=False)

    @classmethod
    def from_dict(cls, raw: object) -> "ActivityLog":
        """Build an activity log from YAML data."""
        if not isinstance(raw, dict):
            return cls()

        raw_habits = raw.get("habits") or []
        if isinstance(raw_habits, dict):
            habit_items: list[object] = []
            for key, value in raw_habits.items():
                if isinstance(value, dict):
                    merged = dict(value)
                    merged.setdefault("id", key)
                    habit_items.append(merged)
                    continue
                habit_items.append({"id": key, "title": value})
        elif isinstance(raw_habits, list):
            habit_items = list(raw_habits)
        else:
            habit_items = []

        habit_index: dict[str, Habit] = {}
        warnings: list[str] = []
        for item in habit_items:
            habit = Habit.from_dict(item)
            if not habit.id:
                continue
            if habit.kind and habit.kind not in ACTIVITY_HABIT_KINDS:
                warnings.append(
                    f"Unknown habit kind for {habit.id}: {habit.kind}"
                )
            key = habit.id.casefold()
            if key in habit_index:
                habit_index[key] = habit_index[key].merged(habit)
                continue
            habit_index[key] = habit

        raw_checkins = raw.get("checkins") or raw.get("entries") or []
        checkins: list[Checkin] = []
        if isinstance(raw_checkins, list):
            for item in raw_checkins:
                checkin = Checkin.from_dict(item)
                if not checkin.date and not checkin.summary:
                    continue
                checkins.append(checkin)
                seen_refs: set[str] = set()
                for habit_ref in checkin.habits or [checkin.habit_id]:
                    key = habit_ref.casefold()
                    if not key or key in seen_refs or key in habit_index:
                        continue
                    seen_refs.add(key)
                    warnings.append(
                        f"Check-in references unknown habit: {habit_ref}"
                    )

        raw_weeks = (
            raw.get("weekly_summaries")
            or raw.get("weekly_summary")
            or []
        )
        if isinstance(raw_weeks, dict):
            week_items: list[tuple[str, object]] = list(
                raw_weeks.items()
            )
        elif isinstance(raw_weeks, list):
            week_items = [("", item) for item in raw_weeks]
        else:
            week_items = []
        week_index: dict[str, WeeklySummary] = {}
        for key_hint, item in week_items:
            summary = WeeklySummary.from_dict(
                item,
                key_hint=str(key_hint),
            )
            if not summary.week_start:
                continue
            if summary.week_start in week_index:
                week_index[summary.week_start] = week_index[
                    summary.week_start
                ].merged(summary)
                continue
            week_index[summary.week_start] = summary

        return cls(
            profile=_clean_text(raw.get("profile")),
            updated=_coerce_date_text(raw.get("updated")),
            habits=list(habit_index.values()),
            checkins=checkins,
            weekly_summaries=sorted(
                week_index.values(),
                key=lambda item: item.week_start,
            ),
            warnings=warnings,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize an activity log for YAML output."""
        return {
            "profile": self.profile,
            "updated": self.updated,
            "habits": [habit.to_dict() for habit in self.habits],
            "checkins": [checkin.to_dict() for checkin in self.checkins],
            "weekly_summaries": [
                summary.to_dict()
                for summary in self.weekly_summaries
            ],
        }

    def habit_index(self) -> dict[str, Habit]:
        """Return a stable habit lookup."""
        return {habit.id: habit for habit in self.habits if habit.id}

    def habit_by_id(self) -> dict[str, Habit]:
        """Compatibility alias for older callers."""
        return self.habit_index()


@dataclass
class HabitSummary:
    """Aggregate progress for one habit in a time window."""

    id: str
    title: str = ""
    kind: str = ""
    cadence: str = ""
    target_count: float = 0.0
    target_unit: str = ""
    total_count: float = 0.0
    checkins: int = 0
    days_hit: int = 0
    completion_rate: float = 0.0
    streak: int = 0
    last_checkin: str = ""
    tags: list[str] = field(default_factory=list)
    skill_refs: list[str] = field(default_factory=list)

    @property
    def habit_id(self) -> str:
        """Compatibility alias for older callers."""
        return self.id

    @property
    def last_date(self) -> str:
        """Compatibility alias for older callers."""
        return self.last_checkin

    def to_dict(self) -> dict[str, object]:
        """Serialize for tests or downstream rendering."""
        out: dict[str, object] = {
            "id": self.id,
            "checkins": self.checkins,
            "total_count": self.total_count,
            "days_hit": self.days_hit,
            "completion_rate": self.completion_rate,
            "streak": self.streak,
        }
        if self.title:
            out["title"] = self.title
        if self.kind:
            out["kind"] = self.kind
        if self.cadence:
            out["cadence"] = self.cadence
        if self.target_count:
            out["target_count"] = self.target_count
        if self.target_unit:
            out["target_unit"] = self.target_unit
        if self.last_checkin:
            out["last_checkin"] = self.last_checkin
        if self.tags:
            out["tags"] = list(self.tags)
        if self.skill_refs:
            out["skill_refs"] = list(self.skill_refs)
        return out


@dataclass
class WeekActivitySummary:
    """Computed weekly activity stats."""

    week_start: str
    week_end: str
    total_checkins: int = 0
    total_count: float = 0.0
    active_days: list[str] = field(default_factory=list)
    habit_counts: dict[str, int] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    summary: str = ""
    wins: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize for tests or downstream rendering."""
        out: dict[str, object] = {
            "week_start": self.week_start,
            "week_end": self.week_end,
            "total_checkins": self.total_checkins,
            "total_count": self.total_count,
            "active_days": list(self.active_days),
            "habit_counts": dict(self.habit_counts),
        }
        if self.tags:
            out["tags"] = list(self.tags)
        if self.summary:
            out["summary"] = self.summary
        if self.wins:
            out["wins"] = list(self.wins)
        if self.blockers:
            out["blockers"] = list(self.blockers)
        return out


@dataclass
class ActivitySummary:
    """Windowed summary across all habits."""

    profile: str = ""
    start: str = ""
    end: str = ""
    habit_summaries: list[HabitSummary] = field(default_factory=list)
    weeks: list[WeekActivitySummary] = field(default_factory=list)
    total_checkins: int = 0
    total_count: float = 0.0
    tag_counts: dict[str, int] = field(default_factory=dict)
    habit_count: int = 0

    @property
    def habits(self) -> list[HabitSummary]:
        """Compatibility alias for concise callers."""
        return self.habit_summaries

    @property
    def latest_week(self) -> WeekActivitySummary | None:
        """Return the newest computed week, if any."""
        if not self.weeks:
            return None
        return self.weeks[0]

    def to_dict(self) -> dict[str, object]:
        """Serialize for tests or downstream rendering."""
        return {
            "profile": self.profile,
            "start": self.start,
            "end": self.end,
            "habit_count": self.habit_count,
            "total_checkins": self.total_checkins,
            "total_count": self.total_count,
            "tag_counts": dict(self.tag_counts),
            "habits": [
                habit.to_dict() for habit in self.habit_summaries
            ],
            "weeks": [week.to_dict() for week in self.weeks],
        }


def load(path_or_dir: str | Path) -> ActivityLog:
    """Load one activity log or return an empty structure."""
    path = _activity_log_path(path_or_dir)
    if not path.exists():
        profile = ""
        if isinstance(path_or_dir, str):
            raw = path_or_dir.strip()
            if "/" not in raw and not raw.endswith((".yaml", ".yml")):
                profile = raw
        return ActivityLog(profile=profile)
    raw = _load_activity_yaml(path)
    log = ActivityLog.from_dict(raw)
    if not log.profile:
        log.profile = path.parent.name
    return log


def save(
    path_or_dir: str | Path,
    data: ActivityLog | Mapping[str, Any],
) -> ActivityLog:
    """Write an activity log with today's updated date."""
    path = _activity_log_path(path_or_dir)
    if path.exists():
        _load_activity_yaml(path)
    if isinstance(data, ActivityLog):
        log = data
    else:
        log = ActivityLog.from_dict(dict(data))
    log.profile = log.profile or path.parent.name
    log.updated = date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# Activity log for {log.profile or path.parent.name}\n"
        "# Habits define the stable catalog. Checkins append dated "
        "entries.\n"
        "# Weekly summaries are optional Monday-based rollups.\n\n"
    )
    body = yaml.dump(
        log.to_dict(),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    atomic_write_text(path, header + body)
    git_backup.record_change(
        [path],
        action=f"update {path.name}",
    )
    return log


def _next_checkin_id(log: ActivityLog, habit_id: str, when: str) -> str:
    """Build a deterministic unique activity check-in id."""
    base_habit = _slugify(habit_id) or "general"
    base = "act_" + when.replace("-", "") + "_" + base_habit
    used = {checkin.id for checkin in log.checkins if checkin.id}
    if base not in used:
        return base
    suffix = 2
    while f"{base}_{suffix}" in used:
        suffix += 1
    return f"{base}_{suffix}"


def add_checkin(
    path_or_dir: str | Path,
    checkin: Checkin | Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ActivityLog:
    """Append one normalized check-in and persist the activity log."""
    log = load(path_or_dir)
    if isinstance(checkin, Checkin):
        entry = checkin
    else:
        raw: dict[str, Any] = {}
        if isinstance(checkin, Mapping):
            raw.update(checkin)
        raw.update(kwargs)
        if "date" not in raw and "day" not in raw:
            raw["date"] = date.today().isoformat()
        entry = Checkin.from_dict(raw)
    if not entry.date:
        entry.date = date.today().isoformat()
    if not entry.habit_id and entry.habits:
        entry.habit_id = entry.habits[0]
    if not entry.id:
        entry.id = _next_checkin_id(
            log,
            entry.habit_id or "general",
            entry.date,
        )
    log.checkins.append(entry)
    return save(path_or_dir, log)


def delete_checkin(
    path_or_dir: str | Path,
    checkin_id: str,
) -> bool:
    """Delete one check-in by id and persist the activity log."""
    target = _clean_text(checkin_id)
    if not target:
        return False

    log = load(path_or_dir)
    kept = [checkin for checkin in log.checkins if checkin.id != target]
    if len(kept) == len(log.checkins):
        return False

    log.checkins = kept
    save(path_or_dir, log)
    return True


def load_activity_log(name_or_dir: str | Path) -> ActivityLog:
    """Compatibility wrapper for older imports."""
    return load(name_or_dir)


def save_activity_log(
    name_or_dir: str | Path,
    data: ActivityLog | Mapping[str, Any],
) -> ActivityLog:
    """Compatibility wrapper for older imports."""
    return save(name_or_dir, data)


def resolve_habit_id(log: ActivityLog, value: str) -> str | None:
    """Resolve a user-facing habit id or title to the canonical habit id."""
    clean = _clean_text(value)
    if not clean:
        return None
    for habit in log.habits:
        if habit.id == clean:
            return habit.id
    for habit in log.habits:
        if habit.title == clean:
            return habit.id
    folded = clean.casefold()
    for habit in log.habits:
        if habit.id.casefold() == folded:
            return habit.id
    for habit in log.habits:
        if habit.title.casefold() == folded:
            return habit.id
    slug = _slugify(clean).casefold()
    if not slug:
        return None
    for habit in log.habits:
        if habit.id.casefold() == slug:
            return habit.id
    for habit in log.habits:
        if _slugify(habit.title).casefold() == slug:
            return habit.id
    return None


def _habit_options_text(log: ActivityLog) -> str:
    """Return a short list of available habits for error messages."""
    options = [
        f"{habit.id} ({habit.title})" if habit.title else habit.id
        for habit in log.habits
        if habit.id
    ]
    return ", ".join(options)


def _next_habit_id(log: ActivityLog, title: str) -> str:
    """Return a stable unique habit id for a new title."""
    base = _slugify(title) or "habit"
    used = {habit.id.casefold() for habit in log.habits if habit.id}
    if base.casefold() not in used:
        return base
    suffix = 2
    while f"{base}_{suffix}".casefold() in used:
        suffix += 1
    return f"{base}_{suffix}"


def add_habit(
    name_or_dir: str | Path,
    title: str,
    *,
    kind: str = "practice",
    cadence: str = "daily",
    target: HabitTarget | Mapping[str, Any] | str | None = None,
    tags: list[str] | str | None = None,
    skill_refs: list[str] | str | None = None,
    review_policy: str = "weekly_rollup",
    notes: str = "",
    on_duplicate: str = "reuse",
) -> Habit:
    """Add one habit to the catalog, reusing existing titles by default."""
    clean_title = _clean_text(title)
    if not clean_title:
        raise ValueError("Habit title cannot be blank.")

    log = load(name_or_dir)
    existing_id = resolve_habit_id(log, clean_title)
    if existing_id is not None and on_duplicate != "create":
        if on_duplicate == "error":
            raise ValueError(f"Duplicate habit: {clean_title}")
        return log.habit_index()[existing_id]

    if isinstance(target, HabitTarget):
        target_obj = target
    else:
        target_obj = HabitTarget.from_dict(target)
    habit = Habit(
        id=_next_habit_id(log, clean_title),
        title=clean_title,
        kind=_clean_text(kind) or "practice",
        cadence=_clean_text(cadence) or "daily",
        target=target_obj,
        tags=_normalize_text_list(tags),
        skill_refs=_normalize_text_list(skill_refs),
        review_policy=_clean_text(review_policy) or "weekly_rollup",
        notes=_clean_text(notes),
    )
    log.habits.append(habit)
    save(name_or_dir, log)
    return habit


def add_activity_checkin(
    name_or_dir: str | Path,
    habit_id: str,
    *,
    when: str | date | None = None,
    count: float = 1.0,
    unit: str = "",
    summary: str = "",
    note: str = "",
    tags: list[str] | str | None = None,
    links: list[str] | str | None = None,
    related_learning: list[str] | None = None,
    related_kanban: list[str] | None = None,
    workout_type: str = "",
    duration_min: float = 0.0,
    intensity: str = "",
    metrics: Mapping[str, object] | None = None,
) -> Checkin:
    """Compatibility wrapper for a one-habit check-in."""
    log = load(name_or_dir)
    resolved_id = resolve_habit_id(log, habit_id)
    if resolved_id is None:
        if not log.habits:
            raise ValueError("No habits defined. Add a habit before checking in.")
        options = _habit_options_text(log)
        message = f"Unknown habit: {habit_id}"
        if options:
            message += f". Available habits: {options}"
        raise ValueError(message)
    habit = log.habit_index().get(resolved_id)
    when_text = _coerce_date_text(when or date.today())
    entry = Checkin(
        date=when_text,
        habits=[resolved_id],
        tags=_normalize_text_list(tags),
        summary=_clean_text(summary),
        notes=_clean_text(note),
        id=_next_checkin_id(
            log,
            resolved_id,
            when_text,
        ),
        habit_id=resolved_id,
        count=max(float(count), 0.0),
        unit=_clean_text(unit) or (habit.target.unit if habit else ""),
        workout_type=_clean_text(workout_type),
        duration_min=_parse_nonnegative_float(duration_min),
        intensity=_clean_text(intensity),
        metrics=_normalize_metrics(metrics),
        links=_normalize_text_list(links),
        related_learning=_normalize_text_list(
            related_learning or []
        ),
        related_kanban=_normalize_text_list(
            related_kanban or []
        ),
    )
    if entry.count <= 0.0:
        raise ValueError("count must be greater than zero")
    save(
        name_or_dir,
        ActivityLog(
            profile=log.profile,
            updated=log.updated,
            habits=log.habits,
            checkins=log.checkins + [entry],
            weekly_summaries=log.weekly_summaries,
            warnings=log.warnings,
        ),
    )
    return entry


def habit_progress_for_window(
    log: ActivityLog,
    habit: Habit,
    start: str | date,
    end: str | date,
) -> HabitSummary:
    """Return one habit's aggregate progress for a requested window."""
    summary = summarize_activity_log(log, start=start, end=end)
    for item in summary.habit_summaries:
        if item.id == habit.id:
            return item
    return HabitSummary(
        id=habit.id,
        title=habit.title,
        kind=habit.kind,
        cadence=habit.cadence,
        target_count=habit.target.count,
        target_unit=habit.target.unit,
        tags=list(habit.tags),
        skill_refs=list(habit.skill_refs),
    )


def _checkins_for_habit(
    log: ActivityLog,
    habit_id: str,
    start_date: date,
    end_date: date,
) -> list[Checkin]:
    """Return all check-ins for one habit within a date window."""
    out: list[Checkin] = []
    for checkin in log.checkins:
        if habit_id not in checkin.habits and checkin.habit_id != habit_id:
            continue
        when = _parse_date(checkin.date)
        if when is None:
            continue
        if start_date <= when <= end_date:
            out.append(checkin)
    return out


def _daily_streak(log: ActivityLog, habit_id: str) -> int:
    """Count consecutive days with a habit check-in."""
    dates = sorted(
        {
            when
            for checkin in log.checkins
            if habit_id in checkin.habits
            or checkin.habit_id == habit_id
            if (when := _parse_date(checkin.date)) is not None
        },
        reverse=True,
    )
    if not dates:
        return 0
    streak = 1
    current = dates[0]
    for item in dates[1:]:
        if item == current - timedelta(days=1):
            streak += 1
            current = item
            continue
        break
    return streak


def _weekly_streak(log: ActivityLog, habit_id: str) -> int:
    """Count consecutive ISO weeks with a habit check-in."""
    weeks = sorted(
        {
            when - timedelta(days=when.weekday())
            for checkin in log.checkins
            if habit_id in checkin.habits
            or checkin.habit_id == habit_id
            if (when := _parse_date(checkin.date)) is not None
        },
        reverse=True,
    )
    if not weeks:
        return 0
    streak = 1
    current = weeks[0]
    for item in weeks[1:]:
        if item == current - timedelta(days=7):
            streak += 1
            current = item
            continue
        break
    return streak


def _habit_streak(log: ActivityLog, habit: Habit) -> int:
    """Return a cadence-aware habit streak."""
    if habit.cadence == "weekly":
        return _weekly_streak(log, habit.id)
    return _daily_streak(log, habit.id)


def _infer_cadence_from_target(value: object) -> str:
    """Infer a cadence from compact target text such as ``3x/week``."""
    text = _clean_text(value).lower() if isinstance(value, str) else ""
    if not text:
        return ""
    if "month" in text:
        return "monthly"
    if "week" in text or "/w" in text:
        return "weekly"
    if "day" in text or "/d" in text:
        return "daily"
    return ""


def _weeks_in_window(start_date: date, end_date: date) -> int:
    """Return the number of ISO weeks touched by an inclusive window."""
    start_week = start_date - timedelta(days=start_date.weekday())
    end_week = end_date - timedelta(days=end_date.weekday())
    return ((end_week - start_week).days // 7) + 1


def _months_in_window(start_date: date, end_date: date) -> int:
    """Return the number of calendar months touched by a window."""
    return (
        (end_date.year - start_date.year) * 12
        + end_date.month
        - start_date.month
        + 1
    )


def _target_period_count(
    habit: Habit,
    start_date: date,
    end_date: date,
) -> float:
    """Return expected target volume for one habit over a window."""
    target = habit.target.count or 0.0
    if target <= 0.0:
        return 0.0
    cadence = _clean_text(habit.cadence).casefold()
    if cadence == "weekly":
        return target * float(_weeks_in_window(start_date, end_date))
    if cadence == "monthly":
        return target * float(_months_in_window(start_date, end_date))
    return target * float((end_date - start_date).days + 1)


def _week_in_range(
    week_start: str,
    week_end: str,
    start_date: date,
    end_date: date,
) -> bool:
    """Return True when a week overlaps the requested date window."""
    start = _parse_date(week_start)
    end = _parse_date(week_end or _week_end_from_start(week_start))
    if start is None or end is None:
        return False
    return not (end < start_date or start > end_date)


def summarize_activity_log(
    log: ActivityLog,
    *,
    start: str | date | None = None,
    end: str | date | None = None,
) -> ActivitySummary:
    """Aggregate one activity log over a time window."""
    if start is None and end is None:
        dated_items = [
            when
            for checkin in log.checkins
            if (when := _parse_date(checkin.date)) is not None
        ]
        dated_items.extend(
            when
            for summary in log.weekly_summaries
            if (when := _parse_date(summary.week_start)) is not None
        )
        if dated_items:
            start_date = min(dated_items)
            end_date = max(dated_items)
        else:
            start_date = end_date = date.today()
    else:
        start_date, end_date = _date_range(start, end)
    habit_index = log.habit_index()
    habit_counts: dict[str, int] = {}
    habit_last: dict[str, str] = {}
    tag_counts: dict[str, int] = {}
    total_checkins = 0
    total_count = 0.0
    weeks: dict[str, WeekActivitySummary] = {}

    for checkin in log.checkins:
        when = _parse_date(checkin.date)
        if when is None or not (start_date <= when <= end_date):
            continue
        total_checkins += 1
        total_count += checkin.count
        for tag in checkin.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        for habit_id in checkin.habits or [checkin.habit_id]:
            if not habit_id:
                continue
            habit_counts[habit_id] = habit_counts.get(habit_id, 0) + 1
            if (
                habit_id not in habit_last
                or checkin.date > habit_last[habit_id]
            ):
                habit_last[habit_id] = checkin.date
            if habit_id not in habit_index:
                habit_index[habit_id] = Habit(
                    id=habit_id,
                    title=habit_id.replace("_", " "),
                )

        week_start = (when - timedelta(days=when.weekday())).isoformat()
        week_end = (when + timedelta(days=(6 - when.weekday()))).isoformat()
        week = weeks.setdefault(
            week_start,
            WeekActivitySummary(
                week_start=week_start,
                week_end=week_end,
            ),
        )
        week.total_checkins += 1
        week.total_count += checkin.count
        if checkin.date not in week.active_days:
            week.active_days.append(checkin.date)
        for habit_id in checkin.habits or [checkin.habit_id]:
            if not habit_id:
                continue
            week.habit_counts[habit_id] = (
                week.habit_counts.get(habit_id, 0) + 1
            )
        week.tags = _dedupe_texts(week.tags + checkin.tags)

    for summary in log.weekly_summaries:
        week_end = summary.week_end or _week_end_from_start(
            summary.week_start
        )
        if not _week_in_range(
            summary.week_start,
            week_end,
            start_date,
            end_date,
        ):
            continue
        week = weeks.setdefault(
            summary.week_start,
            WeekActivitySummary(
                week_start=summary.week_start,
                week_end=week_end,
            ),
        )
        week.summary = summary.summary or week.summary
        week.wins = _dedupe_texts(week.wins + summary.wins)
        week.blockers = _dedupe_texts(
            week.blockers + summary.blockers
        )
        week.tags = _dedupe_texts(week.tags + summary.tags)

    habit_summaries: list[HabitSummary] = []
    for habit in sorted(habit_index.values(), key=lambda item: item.id):
        checkins = _checkins_for_habit(log, habit.id, start_date, end_date)
        total = sum(checkin.count for checkin in checkins)
        day_hits = len(
            {
                checkin.date
                for checkin in checkins
                if _clean_text(checkin.date)
            }
        )
        target = habit.target.count or 0.0
        target_for_window = _target_period_count(
            habit,
            start_date,
            end_date,
        )
        completion = (
            0.0
            if target_for_window <= 0.0
            else min(total / target_for_window, 1.0)
        )
        habit_summaries.append(
            HabitSummary(
                id=habit.id,
                title=habit.title,
                kind=habit.kind,
                cadence=habit.cadence,
                target_count=target,
                target_unit=habit.target.unit,
                total_count=total,
                checkins=habit_counts.get(habit.id, 0),
                days_hit=day_hits,
                completion_rate=completion,
                streak=_habit_streak(log, habit),
                last_checkin=habit_last.get(habit.id, ""),
                tags=list(habit.tags),
                skill_refs=list(habit.skill_refs),
            )
        )

    return ActivitySummary(
        profile=log.profile,
        start=start_date.isoformat(),
        end=end_date.isoformat(),
        habit_summaries=habit_summaries,
        weeks=sorted(
            weeks.values(),
            key=lambda item: item.week_start,
            reverse=True,
        ),
        total_checkins=total_checkins,
        total_count=total_count,
        tag_counts=dict(sorted(tag_counts.items())),
        habit_count=len(habit_index),
    )


def activity_summary(
    log_or_path: ActivityLog | str | Path,
    *,
    start: str | date | None = None,
    end: str | date | None = None,
) -> ActivitySummary:
    """Load an activity log and aggregate it."""
    log = (
        load(log_or_path)
        if isinstance(log_or_path, (str, Path))
        else log_or_path
    )
    return summarize_activity_log(log, start=start, end=end)


def habit_daily_counts(
    log_or_path: ActivityLog | str | Path,
    habit_ids: list[str] | tuple[str, ...],
    *,
    start: str | date,
    end: str | date,
) -> dict[str, dict[str, int]]:
    """Return per-day check-in counts for selected habits."""
    log = (
        load(log_or_path)
        if isinstance(log_or_path, (str, Path))
        else log_or_path
    )
    start_date, end_date = _date_range(start, end)
    selected = _dedupe_texts([str(item) for item in habit_ids])
    out: dict[str, dict[str, int]] = {}
    cursor = start_date
    while cursor <= end_date:
        out[cursor.isoformat()] = {habit_id: 0 for habit_id in selected}
        cursor += timedelta(days=1)

    selected_set = set(selected)
    for checkin in log.checkins:
        when = _parse_date(checkin.date)
        if when is None or not (start_date <= when <= end_date):
            continue
        refs = {
            habit_id
            for habit_id in [checkin.habit_id, *checkin.habits]
            if habit_id in selected_set
        }
        if not refs:
            continue
        bucket = out[when.isoformat()]
        for habit_id in refs:
            bucket[habit_id] += 1
    return out


def weekly_summary(
    log_or_path: ActivityLog | str | Path,
    *,
    week_start: str | date | None = None,
) -> dict[str, object]:
    """Return a one-week summary as a plain mapping."""
    if week_start is None:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
    else:
        parsed = _parse_date(week_start)
        start_date = (parsed or date.today()) - timedelta(
            days=(parsed or date.today()).weekday()
        )
    end_date = start_date + timedelta(days=6)
    return activity_summary(
        log_or_path,
        start=start_date,
        end=end_date,
    ).to_dict()


def monthly_summary(
    log_or_path: ActivityLog | str | Path,
    *,
    month: str | date | None = None,
) -> dict[str, object]:
    """Return a calendar-month summary as a plain mapping."""
    if month is None:
        day = date.today()
    else:
        day = _parse_date(month) or date.today()
    start_date = day.replace(day=1)
    if start_date.month == 12:
        next_month = start_date.replace(
            year=start_date.year + 1,
            month=1,
        )
    else:
        next_month = start_date.replace(month=start_date.month + 1)
    end_date = next_month - timedelta(days=1)
    return activity_summary(
        log_or_path,
        start=start_date,
        end=end_date,
    ).to_dict()


__all__ = [
    "ACTIVITY_LOG_FILENAME",
    "ACTIVITY_HABIT_KINDS",
    "ActivityCheckin",
    "ActivityLogParseError",
    "ActivityLog",
    "ActivitySummary",
    "Checkin",
    "Habit",
    "HabitSummary",
    "HabitTarget",
    "WeekActivitySummary",
    "WeeklySummary",
    "activity_summary",
    "add_activity_checkin",
    "add_checkin",
    "add_habit",
    "delete_checkin",
    "habit_progress_for_window",
    "habit_daily_counts",
    "load",
    "load_activity_log",
    "monthly_summary",
    "resolve_habit_id",
    "save",
    "save_activity_log",
    "summarize_activity_log",
    "weekly_summary",
]
