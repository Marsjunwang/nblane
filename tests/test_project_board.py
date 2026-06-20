"""Tests for internal project-board helpers."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.project_board import (
    ProjectBoard,
    ProjectCase,
    ProjectMilestone,
    add_project_case,
    archive_project_case,
    load_project_board,
    load_project_board_raw,
    save_project_board,
    update_project_case,
)


class _FakeDate:
    @staticmethod
    def today() -> date:
        return date(2026, 5, 13)


class TestProjectBoard(unittest.TestCase):
    """Project cases are internal context, not public projects."""

    def test_empty_template_shape_loads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            path = profile / "project-board.yaml"
            path.write_text(
                "schema_version: '1.0'\nprofile: alice\nproject_cases: []\n",
                encoding="utf-8",
            )

            board = load_project_board(profile)
            raw = load_project_board_raw(profile)

        self.assertEqual(board.profile, "alice")
        self.assertEqual(board.project_cases, [])
        self.assertEqual(raw["project_cases"], [])

    def test_legacy_project_case_loads_without_new_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "project-board.yaml").write_text(
                yaml.dump(
                    {
                        "schema_version": "1.0",
                        "profile": "alice",
                        "project_cases": [
                            {
                                "id": "project:legacy",
                                "title": "Legacy 项目",
                                "status": "active",
                                "task_refs": ["task_1"],
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            board = load_project_board(profile)

        case = board.project_cases[0]
        self.assertEqual(case.title, "Legacy 项目")
        self.assertEqual(case.evidence_refs, [])
        self.assertEqual(case.milestones, [])

    def test_add_update_archive_and_save_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            board = ProjectBoard(profile="alice")
            case = add_project_case(
                board,
                "Nblane Workbench",
                goal_refs=["goal_1"],
                source_refs=["source:research:20260513-001"],
                experience_refs=["experience:openai-engineer"],
            )
            self.assertEqual(case.id, "project:nblane-workbench")

            update_project_case(
                board,
                case.id,
                title="Nblane Growth Workbench",
                kind="research",
                task_refs=["task_1", "task_1"],
            )
            archive_project_case(board, case.id)

            with patch("nblane.core.project_board.date", _FakeDate):
                save_project_board(profile, board)

            loaded = load_project_board(profile)
            saved = yaml.safe_load(
                (profile / "project-board.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(saved["updated"], "2026-05-13")
        self.assertEqual(loaded.project_cases[0].status, "archived")
        self.assertEqual(loaded.project_cases[0].kind, "research")
        self.assertEqual(loaded.project_cases[0].task_refs, ["task_1"])

    def test_project_case_milestones_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            board = ProjectBoard(
                profile="alice",
                project_cases=[
                    ProjectCase(
                        id="project:demo",
                        title="中文 Benchmark",
                        task_refs=["task_a", "task_a"],
                        evidence_refs=["ev_1", "ev_1"],
                        milestones=[
                            ProjectMilestone(
                                id="milestone:first-benchmark",
                                title="First benchmark",
                                status="active",
                                target="2026-06",
                                date="2026-06-30",
                                summary="Run first closed-loop benchmark.",
                                task_refs=["task_a", "task_b", "task_a"],
                                evidence_refs=["ev_1", "ev_2"],
                                source_refs=["source:research:001"],
                                output_refs=["output:note"],
                            )
                        ],
                    )
                ],
            )

            with patch("nblane.core.project_board.date", _FakeDate):
                save_project_board(profile, board)

            loaded = load_project_board(profile)
            saved = yaml.safe_load(
                (profile / "project-board.yaml").read_text(encoding="utf-8")
            )

        case = loaded.project_cases[0]
        self.assertEqual(saved["updated"], "2026-05-13")
        self.assertEqual(saved["project_cases"][0]["task_refs"], ["task_a"])
        self.assertEqual(
            saved["project_cases"][0]["milestones"][0]["task_refs"],
            ["task_a", "task_b"],
        )
        self.assertEqual(case.title, "中文 Benchmark")
        self.assertEqual(case.task_refs, ["task_a"])
        self.assertEqual(case.evidence_refs, ["ev_1"])
        self.assertEqual(len(case.milestones), 1)
        self.assertEqual(case.milestones[0].task_refs, ["task_a", "task_b"])
        self.assertEqual(case.milestones[0].evidence_refs, ["ev_1", "ev_2"])
        self.assertEqual(case.milestones[0].date, "2026-06-30")
        self.assertEqual(
            saved["project_cases"][0]["milestones"][0]["date"], "2026-06-30"
        )

    def test_duplicate_id_rejected(self) -> None:
        board = ProjectBoard(profile="alice")
        add_project_case(board, "Demo", case_id="project:demo")
        with self.assertRaises(ValueError):
            add_project_case(board, "Demo again", case_id="project:demo")


if __name__ == "__main__":
    unittest.main()
