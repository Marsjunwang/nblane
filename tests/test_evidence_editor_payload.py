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
    def _run(self, pool_rows: list[dict]):
        from nblane.core import io as io_mod
        from nblane.core import paths as paths_mod
        from nblane.core import profile_io
        from nblane.core.evidence_review import build_evidence_editor_payload

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
                _make_profile(tmp_path, "dev", pool_rows)
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
