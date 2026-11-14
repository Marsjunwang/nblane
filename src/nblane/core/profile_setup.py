"""Build a validated first-use profile before making it visible to readers."""

from __future__ import annotations

import shutil
import tempfile
from datetime import date
from pathlib import Path
from uuid import uuid4

from nblane.core import git_backup, profile_io, schema_io
from nblane.core.file_lock import locked_profile_write
from nblane.core.goals import Goal, GoalBook, save_goal_book
from nblane.core.kanban_io import KANBAN_QUEUE, KANBAN_SECTIONS, save_kanban
from nblane.core.models import KanbanTask
from nblane.core.north_star import update_north_star
from nblane.core.paths import TEMPLATE_DIR
from nblane.core.project_board import ProjectBoard, ProjectCase, save_project_board
from nblane.core.sync import write_generated_blocks
from nblane.core.validate import validate_one


def create_profile(
    name: str,
    *,
    schema: str,
    north_star: str = "",
    goal_title: str = "",
    project_title: str = "",
    task_title: str = "",
) -> Path:
    """Initialize a private profile atomically, including an optional first plan.

    All profile content uses the existing domain writers. Staging lives beside
    profiles/ on the same filesystem and is never exposed by profile listing.
    A failed validation or write leaves no visible partial profile. Existing
    profiles are never replaced, including concurrent create requests.
    """
    clean = profile_io.validate_profile_name(name)
    if clean == "template":
        raise ValueError("template 是保留的档案名称。")
    schema_obj = schema_io.load_schema(schema)
    if schema_obj is None:
        raise ValueError("请选择可用的领域模板。")
    goal_title, project_title, task_title = (value.strip() for value in (goal_title, project_title, task_title))
    if any("\n" in value or "\r" in value for value in (goal_title, project_title, task_title, north_star)):
        raise ValueError("北极星、目标、项目和任务请各写成一行。")
    if (project_title or task_title) and not goal_title:
        raise ValueError("请先填写阶段目标，再添加项目和任务。")
    destination = profile_io.safe_profile_dir(clean)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # This lock serializes creation without creating the destination itself.
    with locked_profile_write(destination.parent, ".profile-create"):
        if destination.exists():
            raise FileExistsError("这个档案名已经存在，请换一个名称。")
        with tempfile.TemporaryDirectory(prefix=".profile-setup-", dir=destination.parent.parent) as scratch:
            staged = Path(scratch) / clean
            with git_backup.skip_changes():
                shutil.copytree(TEMPLATE_DIR, staged)
                profile_io.fill_template_placeholders(staged, clean)
                profile_io.apply_profile_schema(staged, schema, schema_obj.domain)
                profile_io.seed_skill_tree_nodes(staged, clean)
                update_north_star(staged, full=north_star, brief="", visibility="private")
                book = GoalBook(profile=clean)
                board = ProjectBoard(profile=clean)
                sections = {section: [] for section in KANBAN_SECTIONS}
                if goal_title:
                    goal_id = f"goal_{uuid4().hex[:12]}"
                    project_id = f"project:{uuid4().hex[:12]}"
                    task_id = f"kb_{uuid4().hex[:12]}" if task_title else ""
                    book.current_goal_id = goal_id
                    book.goals.append(Goal(id=goal_id, title=goal_title, start=date.today().isoformat(),
                                           task_refs=[task_id] if task_id else []))
                    board.project_cases.append(ProjectCase(
                        id=project_id, title=project_title or goal_title, goal_refs=[goal_id],
                        task_refs=[task_id] if task_id else [],
                    ))
                    if task_title:
                        sections[KANBAN_QUEUE].append(KanbanTask(title=task_title, id=task_id, project_id=project_id))
                save_goal_book(staged, book)
                save_project_board(staged, board)
                save_kanban(staged, sections)
                errors, _warnings = validate_one(staged)
                if errors:
                    raise ValueError("档案校验未通过：" + "; ".join(errors))
                write_generated_blocks(staged)
            # Keep a concurrent CLI-created directory intact too.
            if destination.exists():
                raise FileExistsError("这个档案名已经存在，请换一个名称。")
            staged.rename(destination)
    git_backup.record_change(
        [path for path in destination.rglob("*") if path.is_file() and not path.name.endswith(".lock")],
        action=f"create profile {clean}",
    )
    return destination
