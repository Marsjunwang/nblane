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

    def test_duplicate_id_rejected(self) -> None:
        board = ProjectBoard(profile="alice")
        add_project_case(board, "Demo", case_id="project:demo")
        with self.assertRaises(ValueError):
            add_project_case(board, "Demo again", case_id="project:demo")


if __name__ == "__main__":
    unittest.main()
