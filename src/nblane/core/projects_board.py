"""Aggregated projects-board read model for the unified /projects SPA page.

Ports the aggregation logic that produced the approved Phase 2 concept
mockups (``.dev-assets/design-mockups/phase2/build_data.py``) into
production code: goal-grouped project swimlanes, Done counts that include
``kanban-archive.md``, per-column task grouping with ``someday`` kept as a
badge list (not a column), an unassigned lane for tasks without
``project_id``, and habit check-in dots/streaks from the activity log.

Read-only over the profile directory; all parsing goes through the core
``*_io`` modules. Dates are compared as ISO strings (``YYYY-MM-DD`` sorts
lexicographically).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from nblane.core import activity_log
from nblane.core.goals import load_goal_book
from nblane.core.kanban_archive import _archive_tasks, kanban_ref_id
from nblane.core.kanban_io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
    parse_kanban,
)
from nblane.core.models import KanbanTask
from nblane.core.project_board import ProjectCase, load_project_board

# Kanban section -> board column key. Someday is surfaced as a badge list on
# the lane, not as a column (locked Phase 2 design decision).
SECTION_COLUMNS = {
    KANBAN_QUEUE: "queue",
    KANBAN_DOING: "doing",
    KANBAN_DONE: "done",
    KANBAN_SOMEDAY: "someday",
}


@dataclass
class BoardTask:
    """One kanban task flattened for a board lane."""

    id: str
    title: str
    section: str
    column: str
    done: bool = False
    context: str = ""
    why: str = ""
    started_on: str | None = None
    completed_on: str | None = None
    planned_start: str | None = None
    planned_end: str | None = None
    project_id: str = ""
    milestone_id: str = ""
    tags: str = ""


@dataclass
class BoardMilestone:
    """One project milestone with task completion progress.

    ``status`` is the stored value; the current data model has no separate
    "completed milestone" workflow (real profiles carry ``planned`` even for
    past dates — overdue planned milestones are a display concern).
    """

    id: str
    title: str = ""
    status: str = "planned"
    target: str = ""
    date: str = ""
    done_count: int = 0
    total_count: int = 0


@dataclass
class BoardProject:
    """One project swimlane: case facts plus owned kanban tasks."""

    id: str
    title: str = ""
    status: str = "active"
    kind: str = "internal"
    visibility: str = "private"
    summary: str = ""
    time_range: str = ""
    goal_refs: list[str] = field(default_factory=list)
    milestones: list[BoardMilestone] = field(default_factory=list)
    queue: list[BoardTask] = field(default_factory=list)
    doing: list[BoardTask] = field(default_factory=list)
    someday: list[BoardTask] = field(default_factory=list)
    column_counts: dict[str, int] = field(default_factory=dict)
    done_count: int = 0
    archived_done_count: int = 0
    last_activity: str = ""
    habit_id: str = ""


@dataclass
class BoardGoal:
    """One goal grouping row with its projects (first-goal grouping)."""

    id: str
    title: str = ""
    status: str = ""
    summary: str = ""
    target: str = ""
    projects: list[BoardProject] = field(default_factory=list)


@dataclass
class BoardHabitDay:
    """One day of the current ISO week check-in strip."""

    date: str
    done: bool = False
    future: bool = False


@dataclass
class BoardHabit:
    """Habit check-in aggregation for continuous (habit) lanes."""

    id: str
    title: str = ""
    kind: str = ""
    cadence: str = ""
    week: list[BoardHabitDay] = field(default_factory=list)
    streak: int = 0
    total_checkins: int = 0
    last_checkin: str = ""
    project_id: str = ""


@dataclass
class ProjectsBoard:
    """Full /projects aggregation: goals, projects, tasks, habits."""

    profile: str = ""
    today: str = ""
    goals: list[BoardGoal] = field(default_factory=list)
    ungrouped_projects: list[BoardProject] = field(default_factory=list)
    unassigned_tasks: list[BoardTask] = field(default_factory=list)
    habits: list[BoardHabit] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


def _board_task(task: KanbanTask, section: str) -> BoardTask:
    """Flatten one core kanban task into a board row."""
    return BoardTask(
        id=str(task.id or "").strip(),
        title=task.title,
        section=section,
        column=SECTION_COLUMNS.get(section, "queue"),
        done=task.done,
        context=task.context,
        why=task.why,
        started_on=task.started_on or None,
        completed_on=task.completed_on or None,
        planned_start=task.planned_start or None,
        planned_end=task.planned_end or None,
        project_id=task.project_id,
        milestone_id=task.milestone_id,
        tags=task.tags,
    )


def _normalize_link_text(value: str) -> str:
    """Casefolded, separator-insensitive text for habit<->project matching."""
    return "".join(
        char for char in value.strip().casefold() if char.isalnum()
    )


def _project_id_tail(project_id: str) -> str:
    """Strip the ``project:`` style prefix for id matching."""
    text = project_id.strip()
    return text.rsplit(":", 1)[-1] if ":" in text else text


def link_habit_to_project(
    habit_id: str, habit_title: str, case: ProjectCase
) -> bool:
    """True when a habit and a project case refer to the same thing.

    The data model has no explicit habit<->project field, so the link is a
    documented heuristic: normalized habit id or title equals the project
    title or the project id tail (after any ``prefix:``). Profiles where
    nothing matches still get the habit lane via the top-level ``habits``
    list; the frontend may pair lanes by its own rule.
    """
    habit_keys = {
        key
        for key in (
            _normalize_link_text(habit_id),
            _normalize_link_text(habit_title),
        )
        if key
    }
    if not habit_keys:
        return False
    project_keys = {
        _normalize_link_text(case.title),
        _normalize_link_text(_project_id_tail(case.id)),
    }
    return bool(habit_keys & project_keys)


def _task_dates(task: KanbanTask) -> list[str]:
    """Activity-relevant ISO dates on one task (for last-activity math)."""
    return [
        text
        for text in (
            task.started_on,
            task.completed_on,
            task.planned_start,
            task.planned_end,
        )
        if text
    ]


def _owned(task: KanbanTask, case: ProjectCase, owned_ids: set[str]) -> bool:
    """Mirror the Streamlit/API ownership rule: project_id or task_refs."""
    task_id = str(task.id or "").strip()
    return task.project_id == case.id or bool(task_id and task_id in owned_ids)


def _build_project(
    case: ProjectCase,
    live: list[tuple[str, KanbanTask]],
    archived: list[KanbanTask],
    done_ids: set[str],
) -> BoardProject:
    """Aggregate one project case into a board swimlane."""
    owned_ids = {str(ref).strip() for ref in case.task_refs if str(ref).strip()}
    project = BoardProject(
        id=case.id,
        title=case.title,
        status=case.status,
        kind=case.kind,
        visibility=case.visibility,
        summary=case.summary,
        time_range=case.time_range,
        goal_refs=list(case.goal_refs),
    )
    last_activity = ""
    for milestone in case.milestones:
        refs = [ref for ref in milestone.task_refs if str(ref).strip()]
        done = sum(1 for ref in refs if kanban_ref_id(ref) in done_ids)
        project.milestones.append(
            BoardMilestone(
                id=milestone.id,
                title=milestone.title,
                status=milestone.status,
                target=milestone.target,
                date=milestone.date,
                done_count=done,
                total_count=len(refs),
            )
        )
    for section, task in live:
        if not _owned(task, case, owned_ids):
            continue
        row = _board_task(task, section)
        for text in _task_dates(task):
            last_activity = max(last_activity, text)
        if row.column == "queue":
            project.queue.append(row)
        elif row.column == "doing":
            project.doing.append(row)
        elif row.column == "someday":
            project.someday.append(row)
        # Live Done tasks are folded into done_count, not listed.
    archived_done = 0
    for task in archived:
        if not _owned(task, case, owned_ids):
            continue
        archived_done += 1
        for text in _task_dates(task):
            last_activity = max(last_activity, text)
    live_done = sum(
        1
        for section, task in live
        if section == KANBAN_DONE and _owned(task, case, owned_ids)
    )
    project.archived_done_count = archived_done
    project.done_count = live_done + archived_done
    project.column_counts = {
        "queue": len(project.queue),
        "doing": len(project.doing),
        "someday": len(project.someday),
        "done": project.done_count,
    }
    project.last_activity = last_activity
    return project


def _habit_checkin_dates(log: activity_log.ActivityLog, habit_id: str) -> set[str]:
    """All ISO dates with a check-in for one habit."""
    dates: set[str] = set()
    for checkin in log.checkins:
        if habit_id not in checkin.habits and checkin.habit_id != habit_id:
            continue
        text = activity_log._coerce_date_text(checkin.date)
        if text:
            dates.add(text)
    return dates


def _build_habit(
    habit: activity_log.Habit,
    dates: set[str],
    today: date,
) -> BoardHabit:
    """Week dots + streak + totals for one habit (build_data semantics).

    The week strip is the current ISO week (Monday..Sunday). The streak
    counts consecutive checked days ending *today* — a day without a
    check-in today means streak 0, matching the approved mockup.
    """
    week_start = today - timedelta(days=today.weekday())
    week = [
        BoardHabitDay(
            date=(day := week_start + timedelta(days=offset)).isoformat(),
            done=day.isoformat() in dates,
            future=day > today,
        )
        for offset in range(7)
    ]
    streak = 0
    cursor = today
    while cursor.isoformat() in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return BoardHabit(
        id=habit.id,
        title=habit.title,
        kind=habit.kind,
        cadence=habit.cadence,
        week=week,
        streak=streak,
        total_checkins=len(dates),
        last_checkin=max(dates) if dates else "",
    )


def build_projects_board(
    profile: str | Path, *, today: date | None = None
) -> ProjectsBoard:
    """Aggregate the /projects board from one profile directory.

    *today* is injectable for tests; defaults to the real current date.
    """
    pdir = Path(profile)
    today = today or date.today()
    board = load_project_board(pdir)
    sections = parse_kanban(pdir)
    archived = _archive_tasks(pdir)
    log = activity_log.load(pdir)

    live: list[tuple[str, KanbanTask]] = [
        (section, task)
        for section, tasks in sections.items()
        for task in tasks
    ]
    done_ids = {
        str(task.id or "").strip()
        for section, task in live
        if section == KANBAN_DONE and str(task.id or "").strip()
    } | {
        str(task.id or "").strip()
        for task in archived
        if str(task.id or "").strip()
    }

    projects = [_build_project(case, live, archived, done_ids) for case in board.project_cases]
    by_id = {project.id: project for project in projects}

    habits: list[BoardHabit] = []
    habit_rows: dict[str, BoardHabit] = {}
    for habit in log.habits:
        row = _build_habit(habit, _habit_checkin_dates(log, habit.id), today)
        habits.append(row)
        habit_rows[habit.id] = row

    def _attach(habit_id: str, case_id: str) -> None:
        row = habit_rows.get(habit_id)
        project = by_id.get(case_id)
        if row is None or project is None:
            return
        row.project_id = case_id
        project.habit_id = habit_id
        project.last_activity = max(project.last_activity, row.last_checkin)

    # Explicit links (case.habit_id) win over the name heuristic; the
    # heuristic only fills projects/habits still unlinked afterwards.
    for case in board.project_cases:
        habit_id = str(case.habit_id or "").strip()
        if habit_id:
            _attach(habit_id, case.id)
    for habit in log.habits:
        if habit_rows[habit.id].project_id:
            continue
        for case in board.project_cases:
            project = by_id.get(case.id)
            if project is None or project.habit_id:
                continue
            if link_habit_to_project(habit.id, habit.title, case):
                _attach(habit.id, case.id)
                break

    goal_book = load_goal_book(pdir)
    known_goal_ids = {goal.id for goal in goal_book.goals}
    goals: list[BoardGoal] = []
    grouped: set[str] = set()
    for goal in goal_book.goals:
        rows = [
            project
            for project in projects
            if project.id not in grouped
            and project.goal_refs
            and next(
                (ref for ref in project.goal_refs if ref in known_goal_ids),
                None,
            )
            == goal.id
        ]
        grouped.update(project.id for project in rows)
        goals.append(
            BoardGoal(
                id=goal.id,
                title=goal.title or goal.label,
                status=goal.status,
                summary=goal.summary,
                target=goal.target,
                projects=rows,
            )
        )
    ungrouped = [project for project in projects if project.id not in grouped]

    unassigned = [
        _board_task(task, section)
        for section, task in live
        if not task.project_id
        and str(task.id or "").strip() not in {
            ref for case in board.project_cases for ref in case.task_refs
        }
    ]
    stats = {
        "tasks_total": len(live),
        "tasks_unassigned": len(unassigned),
        "done_total": sum(project.done_count for project in projects)
        + sum(1 for row in unassigned if row.column == "done"),
        "projects_total": len(projects),
        "habits_total": len(habits),
    }
    return ProjectsBoard(
        profile=pdir.name,
        today=today.isoformat(),
        goals=goals,
        ungrouped_projects=ungrouped,
        unassigned_tasks=unassigned,
        habits=habits,
        stats=stats,
    )
