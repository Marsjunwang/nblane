"""Read-only weekly growth review aggregation."""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from types import ModuleType

from nblane.core import kanban_io
from nblane.core.profile_io import profile_dir


_HELPER_ARG_MISSING = object()


@dataclass
class DoneTaskReview:
    """Read-only snapshot of one Done kanban task."""

    id: str
    title: str
    context: str = ""
    outcome: str = ""
    completed_on: str = ""
    crystallized: bool = False
    tags: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)


@dataclass
class ReviewSourceSummary:
    """Aggregated summary for an optional profile source."""

    source_available: bool = False
    entry_count: int = 0
    summary: object | None = None


@dataclass
class WeeklyGrowthReview:
    """Combined weekly growth review payload for one profile."""

    profile: str
    profile_path: Path
    done_tasks: list[DoneTaskReview] = field(default_factory=list)
    activity: ReviewSourceSummary = field(
        default_factory=ReviewSourceSummary
    )
    learning: ReviewSourceSummary = field(
        default_factory=ReviewSourceSummary
    )
    inbox: ReviewSourceSummary = field(
        default_factory=ReviewSourceSummary
    )

    @property
    def done_count(self) -> int:
        """Return the number of aggregated Done tasks."""
        return len(self.done_tasks)

    @property
    def crystallized_done_count(self) -> int:
        """Return the number of Done tasks already crystallized."""
        return sum(1 for task in self.done_tasks if task.crystallized)


def _load_optional_module(name: str) -> ModuleType | None:
    """Import an optional review helper module when available."""
    qualified_name = f"nblane.core.{name}"
    try:
        return importlib.import_module(qualified_name)
    except ModuleNotFoundError as exc:
        if exc.name != qualified_name:
            raise
        return None


def _resolve_helper(
    module: ModuleType,
    *names: str,
) -> object | None:
    """Return the first callable helper available on *module*."""
    for name in names:
        helper = getattr(module, name, None)
        if callable(helper):
            return helper
    return None


def _helper_arg(
    param_name: str,
    *,
    profile_name: str,
    profile_path: Path,
    loaded: object = _HELPER_ARG_MISSING,
) -> object:
    """Map a helper parameter name onto known review inputs."""
    if param_name in ("profile", "profile_name", "name"):
        return profile_name
    if param_name in (
        "name_or_dir",
        "path_or_dir",
        "profile_dir",
        "profile_path",
        "path",
        "root",
    ):
        return profile_path
    if param_name in (
        "entries",
        "items",
        "records",
        "log",
        "log_or_name",
        "log_or_path",
        "data",
        "loaded",
        "activity_log",
        "learning_log",
        "inbox",
        "inbox_or_name",
    ):
        return loaded
    return _HELPER_ARG_MISSING


def _call_helper(
    helper: object,
    *,
    profile_name: str,
    profile_path: Path,
    loaded: object = _HELPER_ARG_MISSING,
) -> object:
    """Invoke a helper with common profile/log argument names."""
    signature = inspect.signature(helper)
    args: list[object] = []
    kwargs: dict[str, object] = {}

    for param in signature.parameters.values():
        value = _helper_arg(
            param.name,
            profile_name=profile_name,
            profile_path=profile_path,
            loaded=loaded,
        )
        if value is _HELPER_ARG_MISSING:
            if param.default is inspect._empty:
                raise TypeError(
                    f"Unsupported helper signature for {helper!r}"
                )
            continue
        if param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            args.append(value)
        elif param.kind is inspect.Parameter.KEYWORD_ONLY:
            kwargs[param.name] = value

    return helper(*args, **kwargs)


def _count_entries(entries: object) -> int:
    """Best-effort count for loaded log entries."""
    if entries is None:
        return 0
    for attr in ("entries", "items", "checkins", "done_tasks"):
        value = getattr(entries, attr, None)
        if value is not None:
            try:
                return len(value)  # type: ignore[arg-type]
            except TypeError:
                continue
    try:
        return len(entries)  # type: ignore[arg-type]
    except TypeError:
        return 0


def _summarize_optional_source(
    module_name: str,
    *,
    profile_name: str,
    profile_path: Path,
) -> ReviewSourceSummary:
    """Load and summarize one optional profile review source."""
    module = _load_optional_module(module_name)
    if module is None:
        return ReviewSourceSummary()

    load_helper = _resolve_helper(
        module,
        f"load_{module_name}",
        "load",
        "load_log",
    )
    summary_helper = _resolve_helper(
        module,
        f"summarize_{module_name}",
        "activity_summary",
        "summarize",
        "summary",
        "summarize_log",
    )
    if load_helper is None or summary_helper is None:
        return ReviewSourceSummary()

    loaded = _call_helper(
        load_helper,
        profile_name=profile_name,
        profile_path=profile_path,
    )
    summary = _call_helper(
        summary_helper,
        profile_name=profile_name,
        profile_path=profile_path,
        loaded=loaded,
    )
    return ReviewSourceSummary(
        source_available=True,
        entry_count=_count_entries(loaded),
        summary=summary,
    )


def _parse_done_tasks(
    profile_name: str,
    *,
    profile_path: Path | None = None,
) -> list[DoneTaskReview]:
    """Read the Done column for a profile without writing anything."""
    old_profile_dir = kanban_io.profile_dir
    try:
        if profile_path is not None:
            kanban_io.profile_dir = lambda _name: profile_path
        sections = kanban_io.parse_kanban(profile_name)
    finally:
        kanban_io.profile_dir = old_profile_dir

    done_tasks = sections.get(kanban_io.KANBAN_DONE) or []
    return [
        DoneTaskReview(
            id=task.id,
            title=task.title,
            context=task.context,
            outcome=task.outcome,
            completed_on=task.completed_on or "",
            crystallized=task.crystallized,
            tags=list(getattr(task, "tags", [])),
            details=list(task.details),
        )
        for task in done_tasks
    ]


def build_weekly_growth_review(
    profile_name: str,
    *,
    profile_path: Path | None = None,
) -> WeeklyGrowthReview:
    """Aggregate read-only weekly review inputs for one profile."""
    resolved_profile_path = profile_path or profile_dir(profile_name)
    return WeeklyGrowthReview(
        profile=profile_name,
        profile_path=resolved_profile_path,
        done_tasks=_parse_done_tasks(
            profile_name,
            profile_path=resolved_profile_path,
        ),
        activity=_summarize_optional_source(
            "activity_log",
            profile_name=profile_name,
            profile_path=resolved_profile_path,
        ),
        learning=_summarize_optional_source(
            "learning_log",
            profile_name=profile_name,
            profile_path=resolved_profile_path,
        ),
        inbox=_summarize_optional_source(
            "inbox",
            profile_name=profile_name,
            profile_path=resolved_profile_path,
        ),
    )


@dataclass
class GrowthReview:
    """Candidate-only weekly review payload."""

    profile: str
    week_start: str
    week_end: str
    done_task_ids: list[str] = field(default_factory=list)
    activity_summary: dict[str, object] = field(default_factory=dict)
    learning_summary: dict[str, object] = field(default_factory=dict)
    inbox_summary: dict[str, object] = field(default_factory=dict)
    evidence_candidates: list[dict[str, object]] = field(default_factory=list)
    next_queue_candidates: list[dict[str, object]] = field(default_factory=list)
    method_candidates: list[dict[str, object]] = field(default_factory=list)
    public_candidates: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize the review as the documented YAML-like shape."""
        return {
            "review": {
                "profile": self.profile,
                "week_start": self.week_start,
                "week_end": self.week_end,
                "done_task_ids": list(self.done_task_ids),
                "activity_summary": self.activity_summary,
                "learning_summary": self.learning_summary,
                "inbox_summary": self.inbox_summary,
                "evidence_candidates": list(self.evidence_candidates),
                "next_queue_candidates": list(self.next_queue_candidates),
                "method_candidates": list(self.method_candidates),
                "public_candidates": list(self.public_candidates),
            }
        }


def _parse_review_date(value: str | date) -> date:
    """Return an ISO date from a date or string."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _date_in_window(
    value: str,
    start_date: date,
    end_date: date,
    *,
    include_missing: bool = True,
) -> bool:
    """Return whether an optional date belongs to an inclusive window."""
    if not value:
        return include_missing
    try:
        parsed = date.fromisoformat(value[:10])
    except ValueError:
        return include_missing
    return start_date <= parsed <= end_date


def _summary_to_dict(value: object) -> dict[str, object]:
    """Convert a summary object or mapping to a plain dict."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        converted = to_dict()
        return converted if isinstance(converted, dict) else {}
    return {}


def _source_is_public_candidate(tags: list[str], visibility: str = "") -> bool:
    """Return True only for explicitly public-candidate sources."""
    return visibility == "public_candidate" or "visibility/public_candidate" in tags


def build_weekly_review(
    profile: str,
    week_start: str | date,
    week_end: str | date,
    *,
    profile_path: Path | None = None,
) -> GrowthReview:
    """Build a candidate-only weekly review without mutating profile files."""
    start_date = _parse_review_date(week_start)
    end_date = _parse_review_date(week_end)
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    resolved_profile_path = profile_path or profile_dir(profile)
    legacy = build_weekly_growth_review(
        profile,
        profile_path=resolved_profile_path,
    )
    done_tasks = [
        task
        for task in legacy.done_tasks
        if _date_in_window(task.completed_on, start_date, end_date)
    ]

    activity_summary = _summary_to_dict(legacy.activity.summary)
    learning_summary = _summary_to_dict(legacy.learning.summary)
    inbox_summary = _summary_to_dict(legacy.inbox.summary)

    evidence_candidates: list[dict[str, object]] = []
    method_candidates: list[dict[str, object]] = []
    public_candidates: list[dict[str, object]] = []
    for task in done_tasks:
        if not task.crystallized:
            evidence_candidates.append(
                {
                    "source": "kanban_done",
                    "task_id": task.id,
                    "title": task.title,
                    "summary": task.outcome or task.context,
                    "draft": True,
                }
            )
        if task.outcome or task.details:
            method_candidates.append(
                {
                    "source": "kanban_done",
                    "task_id": task.id,
                    "title": task.title,
                    "notes": list(task.details),
                    "draft": True,
                }
            )
        if _source_is_public_candidate(task.tags):
            public_candidates.append(
                {
                    "source": "kanban_done",
                    "task_id": task.id,
                    "title": task.title,
                    "visibility": "public_candidate",
                    "draft": True,
                }
            )

    next_queue_candidates: list[dict[str, object]] = []
    try:
        from nblane.core.learning_log import load_learning_log

        learning = load_learning_log(resolved_profile_path)
        for resource in learning.resources:
            if not _date_in_window(
                resource.added_at,
                start_date,
                end_date,
                include_missing=False,
            ):
                continue
            for action in resource.next_actions:
                if action.get("target") != "kanban_queue":
                    continue
                next_queue_candidates.append(
                    {
                        "source": "learning",
                        "resource_id": resource.id,
                        "title": action.get("title", ""),
                        "draft": True,
                    }
                )
            if _source_is_public_candidate(resource.tags, resource.visibility):
                public_candidates.append(
                    {
                        "source": "learning",
                        "resource_id": resource.id,
                        "title": resource.title,
                        "visibility": "public_candidate",
                        "draft": True,
                    }
                )
    except (OSError, ValueError, KeyError):
        pass

    return GrowthReview(
        profile=profile,
        week_start=start_date.isoformat(),
        week_end=end_date.isoformat(),
        done_task_ids=[task.id for task in done_tasks if task.id],
        activity_summary=activity_summary,
        learning_summary=learning_summary,
        inbox_summary=inbox_summary,
        evidence_candidates=evidence_candidates,
        next_queue_candidates=next_queue_candidates,
        method_candidates=method_candidates,
        public_candidates=public_candidates,
    )


__all__ = [
    "DoneTaskReview",
    "GrowthReview",
    "ReviewSourceSummary",
    "WeeklyGrowthReview",
    "build_weekly_growth_review",
    "build_weekly_review",
]
