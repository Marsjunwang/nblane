"""Tests for Phase 4: evidence editor payload builder."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml


def _make_profile(tmp: Path, name: str, pool_rows: list[dict]) -> None:
    pdir = tmp / name
    pdir.mkdir(parents=True)
    (pdir / "evidence-pool.yaml").write_text(
        yaml.safe_dump(
            {"profile": name, "evidence_entries": pool_rows},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    # Minimal skill tree + schema so build_evidence_review does not error.
    (pdir / "skill-tree.yaml").write_text(
        yaml.safe_dump({"schema": "_none_", "nodes": []}),
        encoding="utf-8",
    )


class TestEditorPayload(unittest.TestCase):
    def _run(self, pool_rows: list[dict], project_board_data: dict | None = None):
        from nblane.core import io as io_mod
        from nblane.core import paths as paths_mod
        from nblane.core import profile_io
        from nblane.core import project_board
        from nblane.core.evidence_review import build_evidence_editor_payload

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            origs = {
                paths_mod: paths_mod.PROFILES_DIR,
                profile_io: profile_io.PROFILES_DIR,
                io_mod: io_mod.PROFILES_DIR,
                project_board: project_board.PROFILES_DIR,
            }
            for mod in origs:
                mod.PROFILES_DIR = tmp_path
            try:
                _make_profile(tmp_path, "dev", pool_rows)
                if project_board_data is not None:
                    (tmp_path / "dev" / "project-board.yaml").write_text(
                        yaml.safe_dump(project_board_data, allow_unicode=True),
                        encoding="utf-8",
                    )
                return build_evidence_editor_payload("dev")
            finally:
                for mod, val in origs.items():
                    mod.PROFILES_DIR = val

    def test_payload_shape(self) -> None:
        payload = self._run(
            [
                {
                    "id": "ev1",
                    "type": "project",
                    "title": "GAC work",
                    "origin": "resume_parse",
                    "original_content": "原始内容",
                }
            ]
        )
        for key in (
            "evidence_rows",
            "project_options",
            "public_project_options",
            "output_options",
            "project_suggestions",
            "migration_summary",
            "origin_options",
            "type_options",
            "language_options",
            "skill_summaries",
            "skill_options",
        ):
            self.assertIn(key, payload)

    def test_derived_flags(self) -> None:
        payload = self._run(
            [
                {
                    "id": "ev1",
                    "type": "project",
                    "title": "Has raw",
                    "origin": "resume_parse",
                    "original_content": "x",
                },
                {
                    "id": "ev2",
                    "type": "project",
                    "title": "Legacy no origin",
                },
            ]
        )
        by_id = {r["id"]: r for r in payload["evidence_rows"]}
        self.assertFalse(by_id["ev1"]["needs_migration"])
        self.assertTrue(by_id["ev1"]["has_original_content"])
        self.assertTrue(by_id["ev2"]["needs_migration"])
        self.assertFalse(by_id["ev2"]["has_original_content"])

    def test_migration_summary_counts(self) -> None:
        payload = self._run(
            [
                {
                    "id": "ev1",
                    "type": "project",
                    "title": "Orphan resume",
                    "origin": "resume_parse",
                    "review_status": "reviewed",
                },
            ]
        )
        ms = payload["migration_summary"]
        # No original_content -> missing_raw and needs_migration.
        self.assertGreaterEqual(ms["missing_raw"], 1)
        self.assertGreaterEqual(ms["resume_manual_unassigned"], 1)

    def test_resume_rows_allow_optional_project_and_shared_resume_source(self) -> None:
        payload = self._run(
            [
                {
                    "id": "ev_ap_boost",
                    "type": "project",
                    "title": "Far-range Monocular Detection Optimization",
                    "origin": "resume_parse",
                    "origin_ref": "resume",
                    "original_content": "Improved AP by 15.",
                    "project_refs": ["project:gac"],
                },
                {
                    "id": "ev_training_speedup",
                    "type": "project",
                    "title": "End-to-End Model Training Acceleration",
                    "origin": "resume_parse",
                    "origin_ref": "resume",
                    "original_content": "Improved training throughput.",
                },
            ],
            {
                "profile": "dev",
                "project_cases": [
                    {
                        "id": "project:gac",
                        "title": "GAC",
                    }
                ],
            },
        )
        by_id = {r["id"]: r for r in payload["evidence_rows"]}
        self.assertEqual(by_id["ev_ap_boost"]["project_resolution_status"], "valid")
        self.assertFalse(by_id["ev_ap_boost"]["source_conflict"])
        self.assertEqual(
            by_id["ev_training_speedup"]["project_resolution_status"],
            "not_required",
        )
        self.assertFalse(by_id["ev_training_speedup"]["source_conflict"])
        self.assertEqual(payload["migration_summary"]["project_without_goal"], 0)
        self.assertEqual(payload["migration_summary"]["missing_project"], 0)
        self.assertEqual(payload["migration_summary"]["source_conflict"], 0)

    def test_output_options_mark_source_ready_and_count_only_ready(self) -> None:
        from nblane.core import io as io_mod
        from nblane.core import paths as paths_mod
        from nblane.core import profile_io
        from nblane.core import project_board
        from nblane.core.evidence_review import build_evidence_editor_payload

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            origs = {
                paths_mod: paths_mod.PROFILES_DIR,
                profile_io: profile_io.PROFILES_DIR,
                io_mod: io_mod.PROFILES_DIR,
                project_board: project_board.PROFILES_DIR,
            }
            for mod in origs:
                mod.PROFILES_DIR = tmp_path
            try:
                _make_profile(
                    tmp_path,
                    "dev",
                    [
                        {
                            "id": "ev_existing",
                            "type": "practice",
                            "title": "Existing output evidence",
                            "origin": "output",
                            "origin_ref": "output:already",
                            "original_content": "raw",
                            "formatted_content": "formatted",
                            "date": "2026-02-01",
                            "project_refs": ["project:demo"],
                        }
                    ],
                )
                pdir = tmp_path / "dev"
                (pdir / "project-board.yaml").write_text(
                    yaml.safe_dump(
                        {
                            "profile": "dev",
                            "project_cases": [
                                {
                                    "id": "project:demo",
                                    "title": "Demo",
                                    "goal_refs": ["goal:demo"],
                                }
                            ],
                        },
                        allow_unicode=True,
                    ),
                    encoding="utf-8",
                )
                (pdir / "outputs.yaml").write_text(
                    yaml.safe_dump(
                        {
                            "outputs": [
                                {
                                    "id": "ready_project",
                                    "title": "Ready with project",
                                    "status": "published",
                                    "date": "2026-02-01",
                                    "summary": "Ready summary.",
                                    "project_refs": ["project:demo"],
                                },
                                {
                                    "id": "ready_needs_project",
                                    "title": "Ready needs project",
                                    "status": "published",
                                    "date": "2026-02-02",
                                    "summary": "Ready summary.",
                                },
                                {
                                    "id": "draft",
                                    "title": "Draft",
                                    "status": "draft",
                                    "date": "2026-02-03",
                                    "summary": "Draft summary.",
                                },
                                {
                                    "id": "missing_summary",
                                    "title": "Missing summary",
                                    "status": "published",
                                    "date": "2026-02-04",
                                },
                                {
                                    "id": "already",
                                    "title": "Already has evidence",
                                    "status": "published",
                                    "date": "2026-02-05",
                                    "summary": "Already summary.",
                                    "project_refs": ["project:demo"],
                                },
                                {
                                    "id": "ignored",
                                    "title": "Ignored",
                                    "status": "published",
                                    "date": "2026-02-06",
                                    "summary": "Ignored summary.",
                                    "project_refs": ["project:demo"],
                                },
                            ]
                        },
                        allow_unicode=True,
                    ),
                    encoding="utf-8",
                )
                (pdir / "web-preferences.yaml").write_text(
                    yaml.safe_dump(
                        {
                            "evidence_review": {
                                "ignored_output_candidates": [
                                    {
                                        "source_key": "output:ignored",
                                        "source_kind": "output",
                                        "output_id": "ignored",
                                        "reason": "not_evidence",
                                    }
                                ]
                            }
                        },
                        allow_unicode=True,
                    ),
                    encoding="utf-8",
                )
                payload = build_evidence_editor_payload("dev")
            finally:
                for mod, val in origs.items():
                    mod.PROFILES_DIR = val

        options = {item["id"]: item for item in payload["output_options"]}
        # ready_project, ready_needs_project, and draft (convertible now).
        self.assertEqual(payload["migration_summary"]["output_candidates"], 3)
        self.assertTrue(options["ready_project"]["source_ready"])
        self.assertFalse(options["ready_project"]["requires_project_selection"])
        self.assertTrue(options["ready_needs_project"]["source_ready"])
        self.assertTrue(options["ready_needs_project"]["requires_project_selection"])
        # draft is convertible (confidential content that can't be published
        # yet can still become private evidence); it just needs a project pick.
        self.assertTrue(options["draft"]["source_ready"])
        self.assertFalse(options["missing_summary"]["source_ready"])
        self.assertTrue(options["already"]["already_has_evidence"])
        self.assertFalse(options["already"]["source_changed"])
        self.assertFalse(options["already"]["source_ready"])
        self.assertTrue(options["ignored"]["ignored"])
        self.assertFalse(options["ignored"]["source_ready"])

    def test_done_task_options_lists_done_incl_uncrystallized(self) -> None:
        from nblane.core import io as io_mod
        from nblane.core import paths as paths_mod
        from nblane.core import profile_io
        from nblane.core.evidence_review import build_evidence_editor_payload
        from nblane.core.kanban_io import render_kanban
        from nblane.core.models import KanbanTask

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            origs = {
                paths_mod: paths_mod.PROFILES_DIR,
                profile_io: profile_io.PROFILES_DIR,
                io_mod: io_mod.PROFILES_DIR,
            }
            for mod in origs:
                mod.PROFILES_DIR = tmp_path
            try:
                _make_profile(tmp_path, "dev", [])
                tasks = [
                    KanbanTask(title="Done crystal", id="taskA", done=True,
                               crystallized=True),
                    KanbanTask(title="Done plain", id="taskB", done=True,
                               crystallized=False),
                ]
                (tmp_path / "dev" / "kanban.md").write_text(
                    render_kanban("dev", {"Done": tasks}), encoding="utf-8"
                )
                payload = build_evidence_editor_payload("dev")
            finally:
                for mod, val in origs.items():
                    mod.PROFILES_DIR = val

        opts = payload["done_task_options"]
        by_id = {o["id"]: o for o in opts}
        # Both Done tasks appear, regardless of crystallized state.
        self.assertEqual(set(by_id), {"taskA", "taskB"})
        self.assertTrue(by_id["taskA"]["crystallized"])
        self.assertFalse(by_id["taskB"]["crystallized"])
        # Neither has evidence yet.
        self.assertFalse(by_id["taskB"]["has_evidence"])


if __name__ == "__main__":
    unittest.main()
