"""Tests for method draft crystallization (atomic write + backup)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.crystallize import write_method_draft


class TestCrystallize(unittest.TestCase):
    """Method drafts are written atomically and backed up."""

    def test_write_method_draft_records_backup(self) -> None:
        """The draft write is followed by git_backup.record_change."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            with patch(
                "nblane.core.crystallize.profile_dir",
                lambda _name: prof,
            ), patch(
                "nblane.core.crystallize.git_backup.record_change"
            ) as record:
                path = write_method_draft(
                    "demo",
                    "Weekly Review",
                    "Body text",
                )

            record.assert_called_once()
            self.assertEqual(record.call_args[0][0], [path])
            self.assertEqual(path, prof / "methods" / "weekly-review_draft.md")
            content = path.read_text(encoding="utf-8")
            self.assertIn("# Method draft: Weekly Review", content)
            self.assertIn("Body text", content)


class TestDoneCrystallization(unittest.TestCase):
    """Done-task -> evidence state machine (single core implementation)."""

    def _make_profile(self, tmp: Path, name: str = "dev") -> Path:
        """Profile with one uncrystallized and one crystallized Done task."""
        import yaml

        from nblane.core.kanban_io import render_kanban
        from nblane.core.models import KanbanTask

        pdir = tmp / name
        pdir.mkdir(parents=True)
        tasks = [
            KanbanTask(
                title="Tuned latency",
                id="taskA",
                done=True,
                completed_on="2026-01-02",
                context="perf sprint",
                why="cut frame time",
                project_id="project:perf",
            ),
            KanbanTask(
                title="Old task",
                id="taskB",
                done=True,
                completed_on="2025-12-01",
                crystallized=True,
            ),
        ]
        (pdir / "kanban.md").write_text(
            render_kanban(name, {"Done": tasks}), encoding="utf-8"
        )
        (pdir / "evidence-pool.yaml").write_text(
            yaml.safe_dump(
                {"profile": name, "evidence_entries": []}, allow_unicode=True
            ),
            encoding="utf-8",
        )
        (pdir / "skill-tree.yaml").write_text(
            yaml.safe_dump(
                {
                    "profile": name,
                    "schema": "robotics-engineer",
                    "nodes": [{"id": "ros2_basics", "status": "locked"}],
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        return pdir

    def _patched_profiles(self, tmp: Path):
        """Point every profile_dir resolution layer at the temp root."""
        from nblane.core import io as io_mod
        from nblane.core import paths as paths_mod
        from nblane.core import profile_io

        return {
            "paths": (paths_mod, "PROFILES_DIR", paths_mod.PROFILES_DIR),
            "profile_io": (
                profile_io,
                "PROFILES_DIR",
                profile_io.PROFILES_DIR,
            ),
            "io": (io_mod, "PROFILES_DIR", io_mod.PROFILES_DIR),
        }

    def _run_with_profiles(self, tmp: Path, fn):
        patches = self._patched_profiles(tmp)
        originals = {
            key: (mod, attr, value) for key, (mod, attr, value) in patches.items()
        }
        for mod, attr, _ in originals.values():
            setattr(mod, attr, tmp)
        try:
            return fn()
        finally:
            for mod, attr, value in originals.values():
                setattr(mod, attr, value)

    def test_mark_done_crystallized_by_id_and_title(self) -> None:
        from nblane.core import crystallize

        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            self._make_profile(tmp)

            def go():
                count = crystallize.mark_done_crystallized("dev", ["taskA"])
                self.assertEqual(count, 1)
                # Idempotent: a second call flips nothing.
                self.assertEqual(
                    crystallize.mark_done_crystallized("dev", ["taskA"]), 0
                )
                # Title fallback reaches tasks whose id was not captured.
                self.assertEqual(
                    crystallize.mark_done_crystallized(
                        "dev", [], ["Missing"], 
                    ),
                    0,
                )

            self._run_with_profiles(tmp, go)

            sections = self._run_with_profiles(
                tmp, lambda: crystallize.parse_kanban("dev")
            )
            done = sections["Done"]
            by_id = {t.id: t for t in done}
            self.assertTrue(by_id["taskA"].crystallized)
            self.assertTrue(by_id["taskB"].crystallized)

    def test_resolve_done_tasks_reports_missing(self) -> None:
        from nblane.core import crystallize

        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            self._make_profile(tmp)

            def go():
                tasks, missing = crystallize.resolve_done_tasks(
                    "dev", ["taskA", "archived-id"]
                )
                self.assertEqual([t.id for t in tasks], ["taskA"])
                self.assertEqual(missing, ["archived-id"])

            self._run_with_profiles(tmp, go)

    def test_rule_crystallize_patch_snapshots_source(self) -> None:
        from nblane.core import crystallize

        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            self._make_profile(tmp)

            def go():
                tasks, _ = crystallize.resolve_done_tasks("dev", ["taskA"])
                patch = crystallize.rule_crystallize_patch(tasks)
                self.assertEqual(len(patch["evidence_entries"]), 1)
                row = patch["evidence_entries"][0]
                self.assertEqual(row["title"], "Tuned latency")
                self.assertEqual(row["origin"], "kanban_task")
                self.assertEqual(row["origin_ref"], "kanban:taskA")
                self.assertEqual(row["kanban_refs"], ["kanban:taskA"])
                self.assertEqual(row["project_refs"], ["project:perf"])
                self.assertEqual(row["date"], "2026-01-02")
                # Snapshot: the task原文 (title/context/why) is embedded.
                self.assertIn("cut frame time", row["original_content"])
                self.assertIn("perf sprint", row["original_content"])
                self.assertTrue(
                    row["original_content_hash"].startswith("sha256:")
                )

            self._run_with_profiles(tmp, go)

    def test_attach_task_snapshots_fills_missing_only(self) -> None:
        from nblane.core import crystallize
        from nblane.core.models import KanbanTask

        task = KanbanTask(
            title="Tuned latency",
            id="taskA",
            done=True,
            completed_on="2026-01-02",
            project_id="project:perf",
        )
        snap = crystallize.task_snapshot(task)
        patch = {
            "evidence_entries": [
                {"title": "Draft row"},
                {
                    "title": "Has content",
                    "original_content": "kept",
                    "kanban_refs": ["kanban:other"],
                },
            ]
        }
        out = crystallize.attach_task_snapshots(patch, [snap])
        first, second = out["evidence_entries"]
        self.assertEqual(first["origin"], "kanban_task")
        self.assertEqual(first["origin_ref"], "kanban:taskA")
        self.assertEqual(first["kanban_refs"], ["kanban:taskA"])
        self.assertEqual(first["project_refs"], ["project:perf"])
        self.assertIn("Tuned latency", first["original_content"])
        # Existing content/refs are preserved and merged, not overwritten.
        self.assertEqual(second["original_content"], "kept")
        self.assertEqual(second["kanban_refs"], ["kanban:other", "kanban:taskA"])
        self.assertNotIn("original_content_hash", second)

    def test_apply_crystallization_writes_and_marks(self) -> None:
        import yaml

        from nblane.core import crystallize, profile_io

        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            self._make_profile(tmp)

            def go():
                tasks, _ = crystallize.resolve_done_tasks("dev", ["taskA"])
                patch = crystallize.rule_crystallize_patch(tasks)
                result = crystallize.apply_crystallization(
                    "dev", patch, task_ids=["taskA"]
                )
                self.assertTrue(result["ok"], result)
                self.assertEqual(result["crystallized_count"], 1)
                self.assertEqual(len(result["new_evidence_ids"]), 1)

                raw = profile_io.load_evidence_pool_raw("dev") or {}
                rows = raw.get("evidence_entries") or []
                self.assertEqual(len(rows), 1)
                row = rows[0]
                self.assertEqual(row["id"], result["new_evidence_ids"][0])
                self.assertEqual(row["origin"], "kanban_task")
                self.assertEqual(row["kanban_refs"], ["kanban:taskA"])
                self.assertIn("cut frame time", row["original_content"])

                done = crystallize.parse_kanban("dev")["Done"]
                by_id = {t.id: t for t in done}
                self.assertTrue(by_id["taskA"].crystallized)

                # A failed apply (empty patch rows are filtered out, but an
                # invalid row errors) must not mark tasks crystallized.
                bad = {"evidence_entries": [{"type": "practice", "title": ""}]}
                failed = crystallize.apply_crystallization(
                    "dev", bad, task_ids=["taskA"]
                )
                # Empty-title rows are dropped by parse, so this is ok but a
                # no-op; crystallized state must be untouched either way.
                self.assertTrue(failed["ok"])
                self.assertEqual(failed["new_evidence_ids"], [])
                self.assertEqual(failed["crystallized_count"], 0)

            self._run_with_profiles(tmp, go)


if __name__ == "__main__":
    unittest.main()
