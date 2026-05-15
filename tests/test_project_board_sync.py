"""Tests for Project Board cross-file sync helpers."""

from __future__ import annotations

import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.io import (
    KANBAN_DONE,
    KANBAN_DOING,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
    parse_kanban,
)
from nblane.core.kanban_io import render_kanban
from nblane.core.models import KanbanTask
from nblane.core.project_board import (
    ProjectBoard,
    ProjectCase,
    ProjectMilestone,
    load_project_board,
    save_project_board,
)
from nblane.core.project_board_sync import (
    add_project_refs_to_ingest_patch,
    project_refs_for_tasks,
    sync_project_board_from_kanban,
    sync_project_case_workspace,
)
from nblane.core.research_sources import load_research_sources


@contextlib.contextmanager
def _profile_root(root: Path):
    with contextlib.ExitStack() as stack:
        stack.enter_context(patch("nblane.core.io.PROFILES_DIR", root))
        stack.enter_context(patch("nblane.core.profile_io.PROFILES_DIR", root))
        stack.enter_context(patch("nblane.core.project_board.PROFILES_DIR", root))
        stack.enter_context(patch("nblane.core.research_sources.PROFILES_DIR", root))
        stack.enter_context(
            patch("nblane.core.project_board_sync.profile_dir", lambda name: root / name)
        )
        yield


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


class TestProjectBoardSync(unittest.TestCase):
    """Project refs stay connected across Project Board, Kanban, and evidence."""

    def test_project_detail_sync_updates_refs_without_stealing_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "alice"
            profile.mkdir()
            (profile / "kanban.md").write_text(
                render_kanban(
                    "alice",
                    {
                        KANBAN_QUEUE: [
                            KanbanTask(title="Task 1", id="task-1"),
                            KanbanTask(title="Task 2", id="task-2"),
                            KanbanTask(
                                title="Foreign",
                                id="task-foreign",
                                project_id="project:other",
                            ),
                            KanbanTask(
                                title="Old demo task",
                                id="task-old",
                                project_id="project:demo",
                                milestone_id="milestone:old",
                            ),
                        ],
                        KANBAN_DOING: [],
                        KANBAN_DONE: [],
                        KANBAN_SOMEDAY: [],
                    },
                ),
                encoding="utf-8",
            )
            _write_yaml(
                profile / "evidence-pool.yaml",
                {
                    "profile": "alice",
                    "evidence_entries": [
                        {
                            "id": "ev_1",
                            "title": "Selected root",
                            "project_refs": ["project:other"],
                        },
                        {"id": "ev_2", "title": "Selected milestone"},
                        {
                            "id": "ev_3",
                            "title": "Removed demo",
                            "project_refs": ["project:demo", "project:other"],
                        },
                    ],
                },
            )
            _write_yaml(
                profile / "research" / "sources.yaml",
                {
                    "schema_version": "1.0",
                    "profile": "alice",
                    "sources": [
                        {
                            "id": "source:research:s1",
                            "title": "Root source",
                            "project_refs": ["project:other"],
                        },
                        {"id": "source:research:s2", "title": "Milestone source"},
                        {
                            "id": "source:research:s3",
                            "title": "Removed source",
                            "project_refs": ["project:demo", "project:other"],
                        },
                    ],
                },
            )
            board = ProjectBoard(
                profile="alice",
                project_cases=[
                    ProjectCase(
                        id="project:demo",
                        title="中文项目",
                        task_refs=["task-1", "task-foreign"],
                        evidence_refs=["ev_1"],
                        source_refs=["source:research:s1"],
                        milestones=[
                            ProjectMilestone(
                                id="milestone:first",
                                title="First milestone",
                                task_refs=["task-2"],
                                evidence_refs=["ev_2"],
                                source_refs=["source:research:s2"],
                            )
                        ],
                    ),
                    ProjectCase(
                        id="project:other",
                        title="Other",
                        task_refs=["task-foreign"],
                    ),
                ],
            )

            with _profile_root(root):
                result = sync_project_case_workspace("alice", board, "project:demo")
                saved = load_project_board("alice")
                sections = parse_kanban("alice")
                pool = yaml.safe_load(
                    (profile / "evidence-pool.yaml").read_text(encoding="utf-8")
                )
                sources = load_research_sources("alice").by_id()

        self.assertTrue(
            any("task-foreign already belongs to project:other" in warning for warning in result.warnings)
        )
        case = saved.by_id()["project:demo"]
        self.assertEqual(case.title, "中文项目")
        self.assertEqual(case.task_refs, ["task-1", "task-2"])
        self.assertEqual(case.milestones[0].task_refs, ["task-2"])
        self.assertEqual(case.evidence_refs, ["ev_1", "ev_2"])
        self.assertEqual(case.source_refs, ["source:research:s1", "source:research:s2"])

        tasks = {
            task.id: task
            for section_tasks in sections.values()
            for task in section_tasks
        }
        self.assertEqual(tasks["task-1"].project_id, "project:demo")
        self.assertEqual(tasks["task-1"].milestone_id, "")
        self.assertEqual(tasks["task-2"].project_id, "project:demo")
        self.assertEqual(tasks["task-2"].milestone_id, "milestone:first")
        self.assertEqual(tasks["task-foreign"].project_id, "project:other")
        self.assertEqual(tasks["task-old"].project_id, "")
        self.assertEqual(tasks["task-old"].milestone_id, "")

        rows = {row["id"]: row for row in pool["evidence_entries"]}
        self.assertEqual(rows["ev_1"]["project_refs"], ["project:other", "project:demo"])
        self.assertEqual(rows["ev_2"]["project_refs"], ["project:demo"])
        self.assertEqual(rows["ev_3"]["project_refs"], ["project:other"])
        self.assertEqual(
            sources["source:research:s1"].project_refs,
            ["project:other", "project:demo"],
        )
        self.assertEqual(sources["source:research:s2"].project_refs, ["project:demo"])
        self.assertEqual(sources["source:research:s3"].project_refs, ["project:other"])

    def test_kanban_assignment_sync_updates_project_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "alice"
            profile.mkdir()
            with _profile_root(root):
                save_project_board(
                    "alice",
                    ProjectBoard(
                        profile="alice",
                        project_cases=[
                            ProjectCase(
                                id="project:demo",
                                title="Demo",
                                task_refs=["stale"],
                                milestones=[
                                    ProjectMilestone(
                                        id="milestone:first",
                                        title="First",
                                        task_refs=["stale"],
                                    )
                                ],
                            )
                        ],
                    ),
                )
                sections = {
                    KANBAN_DOING: [
                        KanbanTask(title="A", id="task-a", project_id="project:demo"),
                        KanbanTask(
                            title="B",
                            id="task-b",
                            project_id="project:demo",
                            milestone_id="milestone:first",
                        ),
                        KanbanTask(
                            title="Bad milestone",
                            id="task-c",
                            project_id="project:demo",
                            milestone_id="milestone:missing",
                        ),
                        KanbanTask(
                            title="Bad project",
                            id="task-d",
                            project_id="project:missing",
                        ),
                    ],
                    KANBAN_QUEUE: [],
                    KANBAN_DONE: [],
                    KANBAN_SOMEDAY: [],
                }

                result = sync_project_board_from_kanban("alice", sections)
                saved = load_project_board("alice")

        case = saved.by_id()["project:demo"]
        self.assertEqual(case.task_refs, ["task-a", "task-b", "task-c"])
        self.assertEqual(case.milestones[0].task_refs, ["task-b"])
        self.assertTrue(any("unknown project project:missing" in w for w in result.warnings))
        self.assertTrue(any("unknown milestone milestone:missing" in w for w in result.warnings))

    def test_done_ingest_project_refs_helper_dedupes_projects(self) -> None:
        refs = project_refs_for_tasks(
            [
                KanbanTask(title="A", id="a", project_id="project:demo"),
                KanbanTask(title="B", id="b", project_id="project:demo"),
                KanbanTask(title="C", id="c", project_id="project:other"),
                KanbanTask(title="D", id="d"),
            ]
        )
        patch = add_project_refs_to_ingest_patch(
            {
                "evidence_entries": [
                    {"title": "A", "project_refs": ["project:existing"]},
                    {"title": "B"},
                ],
                "node_updates": [],
            },
            refs,
        )

        self.assertEqual(refs, ["project:demo", "project:other"])
        self.assertEqual(
            patch["evidence_entries"][0]["project_refs"],
            ["project:existing", "project:demo", "project:other"],
        )
        self.assertEqual(
            patch["evidence_entries"][1]["project_refs"],
            ["project:demo", "project:other"],
        )


if __name__ == "__main__":
    unittest.main()
