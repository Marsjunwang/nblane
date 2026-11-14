"""First-use initialization is private, consistent and all-or-nothing."""

from __future__ import annotations

import shutil
import threading
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

from nblane.core import profile_io, profile_setup
from nblane.core.goals import load_goal_book
from nblane.core.kanban_io import KANBAN_QUEUE, parse_kanban
from nblane.core.profile_context import parse_identity_fields
from nblane.core.project_board import load_project_board
from nblane.core.sync import get_drifted_blocks
from nblane.core.validate import validate_one


@pytest.fixture
def profiles(tmp_path, monkeypatch):
    directory = tmp_path / "profiles"
    monkeypatch.setattr(profile_io, "PROFILES_DIR", directory)
    monkeypatch.setattr(profile_setup.git_backup, "record_change", lambda *args, **kwargs: None)
    return directory


def test_first_plan_links_goal_project_and_task(profiles):
    directory = profile_setup.create_profile(
        "演示档案", schema="robotics-engineer", north_star="独立交付机器人", goal_title="完成原型",
        project_title="抓取演示", task_title="定义验收标准",
    )
    assert profile_io.list_profiles() == ["演示档案"]
    goal = load_goal_book(directory).current()
    project = load_project_board(directory).project_cases[0]
    task = parse_kanban(directory)[KANBAN_QUEUE][0]
    assert goal.title == "完成原型"
    assert project.goal_refs == [goal.id]
    assert goal.task_refs == project.task_refs == [task.id]
    assert task.project_id == project.id
    assert project.visibility == "private"
    assert not goal.include_in_public_output
    assert parse_identity_fields((directory / "SKILL.md").read_text())["North Star"] == "独立交付机器人"
    assert validate_one(directory)[0] == []
    assert get_drifted_blocks(directory) == []


def test_failure_leaves_no_visible_profile(profiles):
    with patch.object(profile_setup, "write_generated_blocks", side_effect=OSError("disk full")):
        with pytest.raises(OSError, match="disk full"):
            profile_setup.create_profile("new", schema="robotics-engineer")
    assert not (profiles / "new").exists()
    assert profile_io.list_profiles() == []
    assert not list(profiles.parent.glob(".profile-setup-*"))


def test_existing_profile_is_not_replaced(profiles):
    existing = profiles / "existing"
    existing.mkdir(parents=True)
    (existing / "keep.md").write_text("keep")
    with pytest.raises(FileExistsError):
        profile_setup.create_profile("existing", schema="robotics-engineer")
    assert (existing / "keep.md").read_text() == "keep"


@pytest.mark.parametrize("first", ["web", "cli"])
def test_web_and_cli_creation_share_the_creation_lock(profiles, monkeypatch, first):
    """The second creator must not copy over the first creator's files."""
    copying = threading.Event()
    release_copy = threading.Event()
    second_waiting = threading.Event()
    second_copying = threading.Event()
    second = "cli" if first == "web" else "web"
    original_copy = shutil.copytree
    original_lock = profile_io.locked_profile_write
    created = {}
    errors = {}

    @contextmanager
    def observe_lock(directory, filename):
        if filename == ".profile-create" and threading.current_thread().name == second:
            second_waiting.set()
        with original_lock(directory, filename) as lock:
            yield lock

    def pause_copy(source, destination, *args, **kwargs):
        if Path(source) == profile_setup.TEMPLATE_DIR:
            if threading.current_thread().name == first:
                copying.set()
                assert release_copy.wait(5), "first creator was not released"
            else:
                second_copying.set()
        return original_copy(source, destination, *args, **kwargs)

    def create(kind):
        try:
            if kind == "web":
                created[kind] = profile_setup.create_profile(
                    "same", schema="robotics-engineer", goal_title="Keep this goal", task_title="Keep this task",
                )
            else:
                created[kind] = profile_io.init_profile("same", schema="autonomous-driving")
        except Exception as error:
            errors[kind] = error

    monkeypatch.setattr(profile_io, "locked_profile_write", observe_lock)
    monkeypatch.setattr(profile_setup, "locked_profile_write", observe_lock)
    monkeypatch.setattr(shutil, "copytree", pause_copy)
    workers = {kind: threading.Thread(target=create, args=(kind,), name=kind) for kind in (first, second)}
    workers[first].start()
    try:
        assert copying.wait(5), "first creator did not reach template copy"
        workers[second].start()
        assert second_waiting.wait(5), "second creator did not attempt the shared creation lock"
        assert not second_copying.is_set()
    finally:
        release_copy.set()
        for worker in workers.values():
            if worker.ident is not None:
                worker.join(5)
                assert not worker.is_alive()

    assert set(created) == {first}
    assert set(errors) == {second}
    assert isinstance(errors[second], FileExistsError)
    directory = profiles / "same"
    assert profile_io.load_skill_tree(directory).schema == (
        "robotics-engineer" if first == "web" else "autonomous-driving"
    )
    assert validate_one(directory)[0] == []
    if first == "web":
        assert [goal.title for goal in load_goal_book(directory).goals] == ["Keep this goal"]
        assert [task.title for task in parse_kanban(directory)[KANBAN_QUEUE]] == ["Keep this task"]
        assert get_drifted_blocks(directory) == []
    assert not list(profiles.parent.glob(".profile-setup-*"))


@pytest.mark.parametrize("name,schema", [("../escape", "robotics-engineer"), ("template", "robotics-engineer"), ("new", "unknown")])
def test_invalid_input_does_not_create_data(profiles, name, schema):
    with pytest.raises(ValueError):
        profile_setup.create_profile(name, schema=schema)
    assert not profiles.exists()


def test_empty_profile_has_no_placeholder_north_star_or_tasks(profiles):
    directory = profile_setup.create_profile("new", schema="autonomous-driving")
    assert profile_io.load_skill_tree(directory).schema == "autonomous-driving"
    assert load_goal_book(directory).goals == []
    assert not any(parse_kanban(directory).values())
    assert parse_identity_fields((directory / "SKILL.md").read_text())["North Star"] == ""


def test_task_without_goal_is_rejected(profiles):
    with pytest.raises(ValueError, match="阶段目标"):
        profile_setup.create_profile("new", schema="robotics-engineer", task_title="孤立任务")
    assert not profiles.exists()
