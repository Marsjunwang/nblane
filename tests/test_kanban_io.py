"""Tests for kanban.md parse/render."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.io import (
    append_kanban_archive,
    parse_kanban,
    render_kanban,
)
from nblane.core.models import KanbanSubtask, KanbanTask


class TestKanbanParseRender(unittest.TestCase):
    """Round-trip structured kanban tasks."""

    def test_meta_subtasks_roundtrip(self) -> None:
        """context, subtasks, and notes survive parse/render."""
        sections = {
            "Doing": [
                KanbanTask(
                    title="Main",
                    done=False,
                    context="ctx",
                    started_on="2026-03-01",
                    subtasks=[
                        KanbanSubtask(title="a", done=False),
                        KanbanSubtask(title="b", done=True),
                    ],
                    details=["free note"],
                )
            ],
            "Done": [],
            "Queue": [],
            "Someday / Maybe": [],
        }
        text = render_kanban("u1", sections)
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "u1"
            prof.mkdir()
            (prof / "kanban.md").write_text(text, encoding="utf-8")
            with patch(
                "nblane.core.io.profile_dir",
                lambda _n: prof,
            ):
                back = parse_kanban("u1")
        t = back["Doing"][0]
        self.assertEqual(t.title, "Main")
        self.assertEqual(t.context, "ctx")
        self.assertEqual(t.started_on, "2026-03-01")
        self.assertEqual(len(t.subtasks), 2)
        self.assertFalse(t.subtasks[0].done)
        self.assertTrue(t.subtasks[1].done)
        self.assertEqual(t.details, ["free note"])

    def test_legacy_details_only(self) -> None:
        """Old files: plain bullets stay in details."""
        md = """# x · Kanban

> Updated: 2026-01-01

---

## Doing

- [ ] T1
  - plain line

---
"""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "p"
            prof.mkdir()
            (prof / "kanban.md").write_text(md, encoding="utf-8")
            with patch(
                "nblane.core.io.profile_dir",
                lambda _n: prof,
            ):
                back = parse_kanban("p")
        self.assertEqual(back["Doing"][0].details, ["plain line"])

    def test_append_kanban_archive_creates_file(self) -> None:
        """Archive append writes kanban-archive.md."""
        tasks = [
            KanbanTask(
                title="Old done",
                done=True,
                outcome="shipped",
            )
        ]
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "p2"
            prof.mkdir()
            with patch(
                "nblane.core.io.profile_dir",
                lambda _n: prof,
            ):
                append_kanban_archive("p2", tasks)
                append_kanban_archive("p2", tasks)
            arc = prof / "kanban-archive.md"
            self.assertTrue(arc.exists())
            body = arc.read_text(encoding="utf-8")
            self.assertIn("Old done", body)
            self.assertIn("Archived", body)


if __name__ == "__main__":
    unittest.main()
