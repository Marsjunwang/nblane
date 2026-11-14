"""Build synthetic browser fixtures through the regular domain writers."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path

from nblane.core.activity_log import ActivityLog, Habit, HabitPlan, save
from nblane.core.auth_store import create_user
from nblane.core.goals import Goal, GoalBook, save_goal_book
from nblane.core.kanban_io import save_kanban
from nblane.core.models import KanbanTask
from nblane.core.north_star import update_north_star
from nblane.core.profile_io import init_profile
from nblane.core.project_board import ProjectBoard, ProjectCase, save_project_board


def main() -> None:
    root = Path(os.environ["NBLANE_ROOT"]).resolve()
    marker = json.loads((root / ".nblane-e2e.json").read_text())
    if marker["root"] != str(root) or marker["run_id"] != os.environ["NBLANE_E2E_RUN_ID"]:
        raise RuntimeError("Refusing to seed an unowned data directory")
    profile = init_profile("dev")
    init_profile("other")
    today = date.today()
    start = (today - timedelta(days=7)).isoformat()
    end = (today + timedelta(days=22)).isoformat()
    update_north_star(profile, full="Build and learn with a reliable personal agent", brief="Learn by doing")
    save_goal_book(profile, GoalBook(profile="dev", current_goal_id="goal-e2e", goals=[
        Goal(id="goal-e2e", title="Ship a synthetic demo", status="active", start=start, target=end),
    ]))
    save_project_board(profile, ProjectBoard(profile="dev", project_cases=[
        ProjectCase(id="project:e2e", title="Synthetic demo", goal_refs=["goal-e2e"], time_range=f"{start}/{end}"),
        ProjectCase(id="project:e2e-habit", title="Training routine", kind="habit-plan", habit_id="e2e-training", time_range=f"{start}/{end}"),
    ]))
    save(profile, ActivityLog(profile="dev", habits=[
        Habit(id="e2e-training", title="训练习惯", kind="health"),
        Habit(id="e2e-reading", title="阅读习惯", kind="learning"),
    ], habit_plans=[HabitPlan(id="hp-e2e", title="30 day routine", habit_id="e2e-training", start_date=start, end_date=end)]))
    save_kanban(profile, {
        "Doing": [KanbanTask(id="kb_e2e_doing", title="Implement demo", project_id="project:e2e", started_on=start)],
        "Done": [
            KanbanTask(id="kb_e2e_history", title="Earlier milestone", done=True, project_id="project:e2e", started_on="2022-02-01", completed_on="2022-03-01"),
            KanbanTask(id="kb_e2e_recent", title="Recent milestone", done=True, project_id="project:e2e", started_on=(today - timedelta(days=3)).isoformat(), completed_on=(today - timedelta(days=1)).isoformat()),
        ],
        "Queue": [KanbanTask(id="kb_e2e_queue", title="Review demo", project_id="project:e2e")],
        "Someday / Maybe": [],
    })
    create_user("admin", display_name="Test Admin", role="admin", password=os.environ["NBLANE_E2E_ADMIN_PASSWORD"], must_change_password=False)
    create_user("member", display_name="Test Member", role="member", password=os.environ["NBLANE_E2E_MEMBER_PASSWORD"], profiles=["dev"], must_change_password=False)


if __name__ == "__main__":
    main()
