"""Tests for learning log YAML helpers."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.learning_log import (
    LearningLog,
    LearningLogEntry,
    add_learning_resource,
    append_learning_entry,
    archive_resource,
    create_queue_task_from_learning,
    load_learning_log,
    load_learning_log_raw,
    save_learning_log,
    summarize_learning_log,
    update_resource,
)


class _FakeDate:
    @staticmethod
    def today() -> date:
        return date(2026, 4, 28)


class TestLearningLog(unittest.TestCase):
    """Learning log entries round-trip cleanly to YAML."""

    def test_entry_round_trip_normalizes_lists_and_kind_alias(self) -> None:
        """Resource helpers keep the fields expected by the new template."""
        entry = LearningLogEntry.from_dict(
            {
                "id": "r-1",
                "title": " Designing Data-Intensive Applications ",
                "kind": " book ",
                "status": " reading ",
                "tags": ["systems", " systems ", "", None],
                "takeaways": ["replication", "replication", "queues"],
                "next_actions": "review chapter 8",
                "url": "https://example.com/ddia",
                "summary": "revisit logs",
            }
        )

        self.assertEqual(entry.id, "r-1")
        self.assertEqual(entry.title, "Designing Data-Intensive Applications")
        self.assertEqual(entry.resource_kind, "book")
        self.assertEqual(entry.status, "reading")
        self.assertEqual(entry.tags, ["systems"])
        self.assertEqual(
            entry.takeaways,
            [
                {"text": "replication", "kind": "note"},
                {"text": "queues", "kind": "note"},
            ],
        )
        self.assertEqual(
            entry.next_actions,
            [{"title": "review chapter 8", "target": "kanban_queue"}],
        )
        self.assertEqual(
            entry.to_dict(),
            {
                "id": "r-1",
                "kind": "book",
                "title": "Designing Data-Intensive Applications",
                "url": "https://example.com/ddia",
                "status": "reading",
                "tags": ["systems"],
                "summary": "revisit logs",
                "takeaways": [
                    {"text": "replication", "kind": "note"},
                    {"text": "queues", "kind": "note"},
                ],
                "next_actions": [
                    {"title": "review chapter 8", "target": "kanban_queue"}
                ],
            },
        )

    def test_loaders_accept_name_and_path(self) -> None:
        """Raw and typed loaders share path resolution."""
        raw = {
            "profile": "u1",
            "updated": "2026-04-20",
            "resources": [
                {
                    "id": "r-1",
                    "kind": "paper",
                    "title": "Paper",
                    "status": "processed",
                    "tags": ["ml"],
                    "takeaways": [
                        {"text": "ablation matters", "kind": "claim"}
                    ],
                    "next_actions": [
                        {"title": "reuse eval table", "target": "kanban_queue"}
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "u1"
            prof.mkdir()
            (prof / "learning-log.yaml").write_text(
                yaml.dump(raw, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            with patch(
                "nblane.core.learning_log.profile_dir",
                lambda _name: prof,
            ):
                self.assertEqual(load_learning_log_raw("u1"), raw)

            log = load_learning_log(prof)

        self.assertIsNotNone(log)
        assert log is not None
        self.assertEqual(log.profile, "u1")
        self.assertEqual(log.resources[0].kind, "paper")
        self.assertEqual(
            log.resources[0].takeaways,
            [{"text": "ablation matters", "kind": "claim"}],
        )

    def test_save_learning_log_stamps_updated(self) -> None:
        """Saving preserves ordering, comments, and the updated date."""
        log = LearningLog(
            profile="demo",
            entries=[
                LearningLogEntry(
                    id="r-2",
                    title="Async Rust",
                    kind="course",
                    status="unread",
                    tags=["rust"],
                    next_actions=["book lab time"],
                )
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            with patch("nblane.core.learning_log.date", _FakeDate):
                with patch(
                    "nblane.core.learning_log.git_backup.record_change"
                ) as record_change:
                    save_learning_log(prof, log)

            content = (prof / "learning-log.yaml").read_text(
                encoding="utf-8"
            )
            stored = yaml.safe_load(content)

        self.assertIn("# Learning log for demo", content)
        self.assertEqual(stored["updated"], "2026-04-28")
        self.assertEqual(stored["resources"][0]["kind"], "course")
        record_change.assert_called_once()

    def test_append_entry_assigns_stable_id(self) -> None:
        """Appending an entry to a missing file seeds a typed log."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            with patch(
                "nblane.core.learning_log.git_backup.record_change"
            ):
                entry = append_learning_entry(
                    prof,
                    {
                        "title": "The Bitter Lesson",
                        "kind": "article",
                        "status": "reading",
                        "tags": ["ml", "history"],
                    },
                )
            stored = load_learning_log(prof)

        self.assertTrue(entry.id.startswith("learn_"))
        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.resources[0].title, "The Bitter Lesson")

    def test_summarize_learning_log_counts_status_kinds_and_tags(self) -> None:
        """Summaries expose the active queue without losing taxonomy counts."""
        log = LearningLog(
            profile="demo",
            entries=[
                LearningLogEntry(
                    id="r-1",
                    title="Paper",
                    kind="paper",
                    status="reading",
                    tags=["ml", "agents"],
                ),
                LearningLogEntry(
                    id="r-2",
                    title="Book",
                    kind="book",
                    status="processed",
                    tags=["systems"],
                ),
            ],
        )

        summary = summarize_learning_log(log)

        self.assertEqual(summary.total_entries, 2)
        self.assertEqual(
            summary.status_counts,
            {"processed": 1, "reading": 1},
        )
        self.assertEqual(
            summary.resource_kind_counts,
            {"book": 1, "paper": 1},
        )
        self.assertEqual(
            summary.tag_counts,
            {"agents": 1, "ml": 1, "systems": 1},
        )
        self.assertEqual(summary.reading_titles, ["Paper"])
        self.assertEqual(summary.processed_titles, ["Book"])

    def test_add_update_archive_and_create_queue_task(self) -> None:
        """Learning resources can drive Queue tasks without writing evidence."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            (prof / "kanban.md").write_text(
                """# demo · Kanban

## Doing

## Done

## Queue

## Someday / Maybe
""",
                encoding="utf-8",
            )
            with patch(
                "nblane.core.learning_log.git_backup.record_change"
            ), patch(
                "nblane.core.kanban_io.git_backup.record_change"
            ), patch(
                "nblane.core.learning_log.profile_dir",
                lambda _name: prof,
            ), patch(
                "nblane.core.io.profile_dir",
                lambda _name: prof,
            ):
                resource = add_learning_resource(
                    "demo",
                    title="OpenVLA paper",
                    kind="paper",
                    status="reading",
                    tags=["paper", "robotics"],
                    next_actions=[
                        {"title": "Reproduce setup", "target": "kanban_queue"}
                    ],
                )
                updated = update_resource(
                    "demo",
                    resource.id,
                    summary="Important baseline.",
                    status="processed",
                )
                archived = archive_resource("demo", resource.id)
                task_id = create_queue_task_from_learning("demo", resource.id)
                stored = load_learning_log("demo")
                body = (prof / "kanban.md").read_text(encoding="utf-8")

        self.assertEqual(updated.summary, "Important baseline.")
        self.assertEqual(archived.status, "archived")
        self.assertTrue(task_id.startswith("kb_"))
        self.assertIn(task_id, stored.resources[0].related_kanban)
        self.assertIn("Reproduce setup", body)
        self.assertIn("flow/learning", body)


if __name__ == "__main__":
    unittest.main()
