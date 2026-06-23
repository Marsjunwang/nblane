"""Tests for evidence v2 migration pure functions."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nblane.core.evidence_migrate import (
    backfill_row,
    content_hash,
    detect_language,
    infer_origin,
    migrate_evidence_pool,
    refresh_from_crystallized_tasks,
    render_kanban_task_source,
)
from nblane.core.models import KanbanTask, KanbanSubtask


class TestDetectLanguage(unittest.TestCase):
    def test_chinese(self) -> None:
        self.assertEqual(detect_language("完成了远距离检测优化"), "zh")

    def test_english(self) -> None:
        self.assertEqual(
            detect_language("Improved detection by +15 AP"), "en"
        )

    def test_mixed(self) -> None:
        self.assertEqual(
            detect_language("完成 GAC 项目 with strong metrics and gains"),
            "mixed",
        )

    def test_empty(self) -> None:
        self.assertEqual(detect_language("   "), "unknown")

    def test_sprinkle_of_english_stays_zh(self) -> None:
        # A lone acronym in a long Chinese sentence should not flip to mixed.
        text = "我们在自动驾驶感知项目中显著提升了远距离检测的精度 AP"
        self.assertEqual(detect_language(text), "zh")


class TestContentHash(unittest.TestCase):
    def test_stable(self) -> None:
        a = content_hash("hello world")
        b = content_hash("hello world")
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("sha256:"))

    def test_empty(self) -> None:
        self.assertEqual(content_hash("  "), "")


class TestInferOrigin(unittest.TestCase):
    def test_kanban(self) -> None:
        origin, ref, _ = infer_origin({"kanban_refs": ["kanban:abc"]})
        self.assertEqual(origin, "kanban_task")
        self.assertEqual(ref, "kanban:abc")

    def test_paper_by_type(self) -> None:
        origin, _, _ = infer_origin({"type": "paper", "title": "X"})
        self.assertEqual(origin, "paper")

    def test_paper_by_title(self) -> None:
        origin, _, _ = infer_origin(
            {"type": "project", "title": "CVPR publication on detection"}
        )
        self.assertEqual(origin, "paper")

    def test_resume_orphan(self) -> None:
        origin, ref, _ = infer_origin(
            {"id": "ev_ap_boost", "type": "project", "title": "GAC work"}
        )
        self.assertEqual(origin, "resume_parse")
        self.assertEqual(ref, "resume:ev_ap_boost")

    def test_manual_when_has_project_only(self) -> None:
        origin, _, _ = infer_origin(
            {
                "id": "x",
                "type": "project",
                "title": "Daily note",
                "project_refs": ["project:foo"],
            }
        )
        self.assertEqual(origin, "manual_daily")


class TestRenderKanbanTaskSource(unittest.TestCase):
    def test_full_fields(self) -> None:
        task = KanbanTask(
            title="Latency tuning",
            id="t1",
            context="ctx",
            why="why",
            outcome="cut to 20fps",
            completed_on="2026-01-02",
            project_id="project:perf",
            crystallized=True,
            subtasks=[KanbanSubtask(title="profile", done=True)],
            details=["note one"],
        )
        out = render_kanban_task_source(task)
        self.assertIn("# Latency tuning", out)
        self.assertIn("id: t1", out)
        self.assertIn("outcome: cut to 20fps", out)
        self.assertIn("project_id: project:perf", out)
        self.assertIn("crystallized: true", out)
        self.assertIn("- [x] profile", out)
        self.assertIn("- note one", out)


class TestBackfillRow(unittest.TestCase):
    def test_fills_blanks_only(self) -> None:
        row = {
            "id": "ev1",
            "type": "project",
            "title": "GAC detection",
            "summary": "Human written summary",
        }
        out, changed, notes = backfill_row(
            row, profile="dev", target_lang="en"
        )
        self.assertTrue(changed)
        self.assertEqual(out["origin"], "resume_parse")
        self.assertEqual(out["language"], "en")
        # human summary preserved
        self.assertEqual(out["summary"], "Human written summary")
        # original_content backfilled from summary fallback
        self.assertTrue(out["original_content"])
        self.assertTrue(out["original_content_hash"])

    def test_does_not_overwrite_existing(self) -> None:
        row = {
            "id": "ev1",
            "type": "project",
            "title": "T",
            "origin": "manual_daily",
            "summary": "keep me",
            "language": "zh",
            "original_content": "原文",
        }
        out, _, _ = backfill_row(row, profile="dev", target_lang="en")
        self.assertEqual(out["origin"], "manual_daily")
        self.assertEqual(out["language"], "zh")
        self.assertEqual(out["original_content"], "原文")
        self.assertEqual(out["original_language"], "zh")

    def test_protected_summary_never_clobbered(self) -> None:
        row = {"id": "x", "type": "project", "title": "T", "summary": "S"}
        out, _, _ = backfill_row(row, profile="dev")
        self.assertEqual(out["summary"], "S")


class TestMigratePool(unittest.TestCase):
    ENTRIES = [
        {"id": "ev_ap_boost", "type": "project", "title": "GAC AP boost"},
        {"id": "p1", "type": "paper", "title": "A journal paper"},
        {
            "id": "k1",
            "type": "practice",
            "title": "tuned",
            "kanban_refs": ["kanban:zzz"],
        },
    ]

    def test_idempotent(self) -> None:
        first = migrate_evidence_pool(
            "dev", entries=self.ENTRIES, target_lang="en"
        )
        self.assertGreater(first["changed_count"], 0)
        second = migrate_evidence_pool(
            "dev", entries=first["entries"], target_lang="en"
        )
        self.assertEqual(second["changed_count"], 0)

    def test_resume_and_paper_inferred(self) -> None:
        result = migrate_evidence_pool(
            "dev", entries=self.ENTRIES, target_lang="en"
        )
        by_id = {r["id"]: r for r in result["entries"]}
        self.assertEqual(by_id["ev_ap_boost"]["origin"], "resume_parse")
        self.assertEqual(by_id["p1"]["origin"], "paper")
        self.assertEqual(by_id["k1"]["origin"], "kanban_task")

    def test_per_row_diff_present(self) -> None:
        result = migrate_evidence_pool(
            "dev", entries=self.ENTRIES, target_lang="en"
        )
        self.assertEqual(len(result["per_row"]), 3)
        for item in result["per_row"]:
            self.assertIn("before", item)
            self.assertIn("after", item)
            self.assertIn("notes", item)


class TestRefreshCrystallized(unittest.TestCase):
    def _write_kanban(self, pdir: Path) -> None:
        from nblane.core.kanban_io import render_kanban

        task = KanbanTask(
            title="Tuned latency",
            id="taskA",
            done=True,
            completed_on="2026-01-02",
            crystallized=True,
        )
        text = render_kanban("dev", {"Done": [task]})
        (pdir / "kanban.md").write_text(text, encoding="utf-8")

    def test_new_and_no_duplicate(self) -> None:
        # refresh proposes for crystallized tasks; existing kanban_refs -> update.
        from nblane.core import paths as paths_mod
        from nblane.core import profile_io

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            orig = paths_mod.PROFILES_DIR
            paths_mod.PROFILES_DIR = tmp_path
            profile_io.PROFILES_DIR = tmp_path
            try:
                pdir = tmp_path / "dev"
                pdir.mkdir(parents=True)
                self._write_kanban(pdir)
                # No evidence yet -> proposal kind "new".
                result = refresh_from_crystallized_tasks("dev", entries=[])
                self.assertEqual(len(result["proposals"]), 1)
                self.assertEqual(result["proposals"][0]["kind"], "new")
                self.assertEqual(result["proposals"][0]["task_id"], "taskA")
                self.assertIn(
                    "Tuned latency",
                    result["proposals"][0]["original_content"],
                )

                # With evidence already referencing it -> "update".
                existing = [
                    {
                        "id": "ev_x",
                        "type": "practice",
                        "title": "Tuned",
                        "kanban_refs": ["kanban:taskA"],
                    }
                ]
                result2 = refresh_from_crystallized_tasks(
                    "dev", entries=existing
                )
                self.assertEqual(result2["proposals"][0]["kind"], "update")
                self.assertEqual(
                    result2["proposals"][0]["evidence_id"], "ev_x"
                )
            finally:
                paths_mod.PROFILES_DIR = orig
                profile_io.PROFILES_DIR = orig

    def _match_case(self, existing_rows: list[dict]) -> dict:
        """Run refresh against a profile with one crystallized task taskA."""
        from nblane.core import io as io_mod
        from nblane.core import paths as paths_mod
        from nblane.core import profile_io

        tmp = tempfile.TemporaryDirectory()
        tmp_path = Path(tmp.name)
        origs = {m: m.PROFILES_DIR for m in (paths_mod, profile_io, io_mod)}
        for m in origs:
            m.PROFILES_DIR = tmp_path
        try:
            pdir = tmp_path / "dev"
            pdir.mkdir(parents=True)
            self._write_kanban(pdir)
            return refresh_from_crystallized_tasks("dev", entries=existing_rows)
        finally:
            for m, v in origs.items():
                m.PROFILES_DIR = v
            tmp.cleanup()

    def test_match_by_origin_ref_no_kanban_refs(self) -> None:
        # The reported case: row from a crystallized task with only origin_ref
        # set (no kanban_refs) must be updated, not duplicated.
        existing = [
            {
                "id": "ev_y",
                "type": "practice",
                "title": "Anything",
                "origin": "kanban_task",
                "origin_ref": "kanban:taskA",
            }
        ]
        result = self._match_case(existing)
        self.assertEqual(len(result["proposals"]), 1)
        self.assertEqual(result["proposals"][0]["kind"], "update")
        self.assertEqual(result["proposals"][0]["evidence_id"], "ev_y")

    def test_match_by_title_when_no_refs(self) -> None:
        # Last-resort: kanban-origin row with matching title, no refs at all.
        existing = [
            {
                "id": "ev_z",
                "type": "practice",
                "title": "  Tuned   Latency ",  # normalized match
                "origin": "kanban_task",
            }
        ]
        result = self._match_case(existing)
        self.assertEqual(len(result["proposals"]), 1)
        self.assertEqual(result["proposals"][0]["kind"], "update")
        self.assertEqual(result["proposals"][0]["evidence_id"], "ev_z")

    def test_no_title_match_for_non_kanban_origin(self) -> None:
        # A same-title row that is NOT kanban-origin must not absorb the task.
        existing = [
            {
                "id": "ev_other",
                "type": "practice",
                "title": "Tuned latency",
                "origin": "resume_parse",
            }
        ]
        result = self._match_case(existing)
        self.assertEqual(result["proposals"][0]["kind"], "new")

    def _run_mixed(self, **kwargs) -> dict:
        """Run refresh against a Done section with one crystallized + one plain."""
        from nblane.core import io as io_mod
        from nblane.core import paths as paths_mod
        from nblane.core import profile_io
        from nblane.core.kanban_io import render_kanban

        tmp = tempfile.TemporaryDirectory()
        tmp_path = Path(tmp.name)
        origs = {m: m.PROFILES_DIR for m in (paths_mod, profile_io, io_mod)}
        for m in origs:
            m.PROFILES_DIR = tmp_path
        try:
            pdir = tmp_path / "dev"
            pdir.mkdir(parents=True)
            tasks = [
                KanbanTask(title="Crystallized one", id="taskA", done=True,
                           crystallized=True),
                KanbanTask(title="Plain done", id="taskB", done=True,
                           crystallized=False),
            ]
            (pdir / "kanban.md").write_text(
                render_kanban("dev", {"Done": tasks}), encoding="utf-8"
            )
            return refresh_from_crystallized_tasks("dev", entries=[], **kwargs)
        finally:
            for m, v in origs.items():
                m.PROFILES_DIR = v
            tmp.cleanup()

    def test_default_excludes_uncrystallized(self) -> None:
        # Default: only the crystallized task is proposed.
        result = self._run_mixed()
        ids = {p["task_id"] for p in result["proposals"]}
        self.assertEqual(ids, {"taskA"})

    def test_include_uncrystallized_adds_plain_done(self) -> None:
        result = self._run_mixed(include_uncrystallized=True)
        ids = {p["task_id"] for p in result["proposals"]}
        self.assertEqual(ids, {"taskA", "taskB"})

    def test_task_ids_restricts_regardless_of_crystallized(self) -> None:
        # An explicit non-crystallized id is honored even without the flag.
        result = self._run_mixed(task_ids=["taskB"])
        ids = {p["task_id"] for p in result["proposals"]}
        self.assertEqual(ids, {"taskB"})


if __name__ == "__main__":
    unittest.main()
