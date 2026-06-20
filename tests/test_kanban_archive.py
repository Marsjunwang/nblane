"""Tests for evidence -> kanban-archive linking helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.kanban_archive import (
    add_kanban_refs_to_ingest_patch,
    find_kanban_tasks_by_ref,
    kanban_ref,
    kanban_ref_id,
    kanban_refs_for_tasks,
)
from nblane.core.models import KanbanTask

_ARCHIVE = """# p · Kanban archive

> Tasks moved here from kanban.md (Done column).

---

## Archived · 2026-04-15

- [x] Reproduce PI0.5 on Piper
  - id: kb_pi05
  - context: vla algorithm
  - outcome: bench built, code shared
  - started_on: 2026-03-23
  - completed_on: 2026-03-31
  - [x] build test bench
  - [x] run data pipeline

- [x] Benchmark shoe placement
  - id: kb_bench
  - context: shoe owner
  - completed_on: 2026-04-15
"""


class TestKanbanRefHelpers(unittest.TestCase):
    def test_ref_roundtrip(self) -> None:
        self.assertEqual(kanban_ref("kb_1"), "kanban:kb_1")
        self.assertEqual(kanban_ref_id("kanban:kb_1"), "kb_1")
        self.assertEqual(kanban_ref_id("project:x"), "")

    def test_refs_for_tasks_skips_idless_and_dedups(self) -> None:
        tasks = [
            KanbanTask(title="a", id="kb_1"),
            KanbanTask(title="b", id=""),
            KanbanTask(title="c", id="kb_1"),
        ]
        self.assertEqual(kanban_refs_for_tasks(tasks), ["kanban:kb_1"])

    def test_add_refs_to_patch_merges_per_row(self) -> None:
        patch = {
            "evidence_entries": [
                {"title": "a"},
                {"title": "b", "kanban_refs": ["kanban:old"]},
            ]
        }
        out = add_kanban_refs_to_ingest_patch(patch, ["kanban:kb_1", "kanban:kb_1"])
        self.assertEqual(
            [r.get("kanban_refs") for r in out["evidence_entries"]],
            [["kanban:kb_1"], ["kanban:old", "kanban:kb_1"]],
        )

    def test_add_refs_empty_is_noop(self) -> None:
        patch = {"evidence_entries": [{"title": "a"}]}
        out = add_kanban_refs_to_ingest_patch(patch, [])
        self.assertNotIn("kanban_refs", out["evidence_entries"][0])

    def test_find_tasks_resolves_archive_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "p"
            prof.mkdir(parents=True)
            (prof / "kanban-archive.md").write_text(_ARCHIVE, encoding="utf-8")
            with patch(
                "nblane.core.kanban_archive.profile_dir", lambda _n: prof
            ), patch(
                "nblane.core.kanban_archive.parse_kanban", lambda _n: {}
            ):
                found = find_kanban_tasks_by_ref(
                    "p", ["kanban:kb_pi05", "kanban:nope"]
                )
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].title, "Reproduce PI0.5 on Piper")
        self.assertEqual(found[0].outcome, "bench built, code shared")
        self.assertEqual(len(found[0].subtasks), 2)

    def test_find_tasks_accepts_profile_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "p"
            prof.mkdir(parents=True)
            (prof / "kanban.md").write_text(
                "# p · Kanban\n\n"
                "## Done\n\n"
                "- [x] Live task\n"
                "  - id: kb_live\n"
                "  - project_id: project:demo\n",
                encoding="utf-8",
            )
            (prof / "kanban-archive.md").write_text(_ARCHIVE, encoding="utf-8")

            found = find_kanban_tasks_by_ref(
                prof,
                ["kanban:kb_live", "kanban:kb_pi05"],
            )

        self.assertEqual([task.id for task in found], ["kb_live", "kb_pi05"])
        self.assertEqual(found[0].project_id, "project:demo")


if __name__ == "__main__":
    unittest.main()
