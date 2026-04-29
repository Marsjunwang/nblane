"""Tests for inbox YAML helpers and flows."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.inbox import (
    Inbox,
    InboxItem,
    add_inbox_item,
    archive_inbox_item,
    clarify_inbox_item,
    discard_inbox_item,
    load_inbox,
    load_inbox_raw,
    save_inbox,
    summarize_inbox,
)


class _FakeDate:
    @staticmethod
    def today() -> date:
        return date(2026, 4, 28)


class TestInbox(unittest.TestCase):
    """Inbox items keep a visible capture-to-closure history."""

    def test_add_item_assigns_next_id_and_initial_history(self) -> None:
        """New items default to inbox state and record the add event."""
        inbox = Inbox(
            profile="demo",
            items=[InboxItem(id="item-2", title="Existing")],
        )

        item = add_inbox_item(
            inbox,
            " Follow up with paper authors ",
            tags=["company/openai", "person/sam", "company/openai"],
            metadata={"source": "email"},
            note="captured from notes",
            at="2026-04-20",
        )

        self.assertEqual(item.id, "inbox_20260428_003")
        self.assertEqual(item.title, "Follow up with paper authors")
        self.assertEqual(item.status, "inbox")
        self.assertEqual(item.visibility, "private")
        self.assertEqual(
            item.tags,
            ["company/openai", "person/sam"],
        )
        self.assertEqual(item.metadata, {"source": "email"})
        self.assertEqual(len(item.history), 1)
        self.assertEqual(item.history[0].action, "added")
        self.assertEqual(item.history[0].to_status, "inbox")

    def test_clarify_merges_metadata_and_tracks_history(self) -> None:
        """Clarify updates the item in place and keeps the transition log."""
        inbox = Inbox(profile="demo")
        add_inbox_item(
            inbox,
            "Read the safety report",
            item_id="item-1",
            metadata={"source": "meeting"},
            at="2026-04-18",
        )

        item = clarify_inbox_item(
            inbox,
            "item-1",
            status="active",
            tags=["company/openai", "person/sam"],
            metadata={"owner": "nb", "source": "slack"},
            note="narrowed to action item",
            at="2026-04-19",
        )

        self.assertEqual(item.status, "active")
        self.assertEqual(
            item.tags,
            ["company/openai", "person/sam"],
        )
        self.assertEqual(
            item.metadata,
            {"source": "slack", "owner": "nb"},
        )
        self.assertEqual(len(item.history), 2)
        self.assertEqual(item.history[-1].action, "clarified")
        self.assertEqual(item.history[-1].from_status, "inbox")
        self.assertEqual(item.history[-1].to_status, "active")
        self.assertEqual(
            item.history[-1].metadata,
            {"owner": "nb", "source": "slack"},
        )

    def test_archive_and_discard_keep_explicit_history(self) -> None:
        """Archive and discard use dedicated actions instead of a generic clarify."""
        inbox = Inbox(profile="demo")
        add_inbox_item(
            inbox,
            "Maybe publish internal note",
            item_id="item-1",
            at="2026-04-10",
        )
        clarify_inbox_item(
            inbox,
            "item-1",
            status="clarified",
            at="2026-04-11",
        )
        archive_inbox_item(
            inbox,
            "item-1",
            note="covered by weekly digest",
            at="2026-04-12",
        )

        add_inbox_item(
            inbox,
            "Investigate duplicate alert",
            item_id="item-2",
            at="2026-04-13",
        )
        discard_inbox_item(
            inbox,
            "item-2",
            note="false positive",
            metadata={"reason": "duplicate"},
            at="2026-04-14",
        )

        archived = inbox.items[0]
        discarded = inbox.items[1]
        self.assertEqual(archived.status, "archived")
        self.assertEqual(archived.history[-1].action, "archived")
        self.assertEqual(archived.history[-1].to_status, "archived")
        self.assertEqual(discarded.status, "discarded")
        self.assertEqual(discarded.history[-1].action, "discarded")
        self.assertEqual(
            discarded.history[-1].metadata,
            {"reason": "duplicate"},
        )

    def test_loaders_and_save_round_trip(self) -> None:
        """Typed/raw inbox helpers and save behavior share one YAML shape."""
        raw = {
            "profile": "demo",
            "updated": "2026-04-20",
            "items": [
                {
                    "id": "item-1",
                    "title": "Capture team retro theme",
                    "status": "clarified",
                    "tags": ["company/openai"],
                    "metadata": {"source": "retro"},
                    "history": [
                        {
                            "at": "2026-04-19",
                            "action": "added",
                            "to_status": "inbox",
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            (prof / "inbox.yaml").write_text(
                yaml.dump(raw, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            with patch("nblane.core.inbox.profile_dir", lambda _name: prof):
                self.assertEqual(load_inbox_raw("demo"), raw)

            inbox = load_inbox(prof)
            assert inbox is not None
            with patch("nblane.core.inbox.date", _FakeDate):
                with patch(
                    "nblane.core.inbox.git_backup.record_change"
                ) as record_change:
                    save_inbox(prof, inbox)

            content = (prof / "inbox.yaml").read_text(encoding="utf-8")
            stored = yaml.safe_load(content)

        self.assertIsNotNone(inbox)
        assert inbox is not None
        self.assertEqual(inbox.items[0].history[0].action, "added")
        self.assertEqual(inbox.items[0].tags, ["company/openai"])
        self.assertIn("# Inbox for demo", content)
        self.assertEqual(stored["updated"], "2026-04-28")
        record_change.assert_called_once()

    def test_summarize_inbox_counts_statuses_and_tags(self) -> None:
        """Summary helpers expose active items and context tags."""
        inbox = Inbox(
            profile="demo",
            items=[
                InboxItem(
                    id="item-1",
                    title="Follow up",
                    status="inbox",
                    tags=["company/openai", "person/sam"],
                ),
                InboxItem(
                    id="item-2",
                    title="Archive note",
                    status="archived",
                    tags=["company/openai"],
                ),
            ],
        )

        summary = summarize_inbox(inbox)

        self.assertEqual(summary.total_items, 2)
        self.assertEqual(
            summary.status_counts,
            {"archived": 1, "inbox": 1},
        )
        self.assertEqual(
            summary.tag_counts,
            {"company/openai": 2, "person/sam": 1},
        )
        self.assertEqual(summary.active_titles, ["Follow up"])

    def test_profile_clarify_to_learning_and_queue_preserves_item(self) -> None:
        """Profile-scoped clarify actions create drafts/Queue and keep history."""
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
            inbox = Inbox(profile="demo")
            add_inbox_item(
                inbox,
                "Read VLA interview",
                item_id="item-1",
                type="link",
                source="https://example.com/vla",
                tags=["vla"],
            )
            save_inbox(prof, inbox)

            with patch(
                "nblane.core.inbox.git_backup.record_change"
            ), patch(
                "nblane.core.learning_log.git_backup.record_change"
            ), patch(
                "nblane.core.kanban_io.git_backup.record_change"
            ), patch(
                "nblane.core.inbox.profile_dir",
                lambda _name: prof,
            ), patch(
                "nblane.core.learning_log.profile_dir",
                lambda _name: prof,
            ), patch(
                "nblane.core.io.profile_dir",
                lambda _name: prof,
            ):
                learning_result = clarify_inbox_item(
                    "demo",
                    "item-1",
                    "to_learning_resource",
                    {"kind": "interview"},
                )
                queue_result = clarify_inbox_item(
                    "demo",
                    "item-1",
                    "to_kanban_queue",
                    {"title": "Extract VLA interview notes"},
                )
                stored = load_inbox(prof)
                learning_exists = (prof / "learning-log.yaml").exists()
                kanban_body = (prof / "kanban.md").read_text(encoding="utf-8")

        self.assertEqual(learning_result["status"], "clarified")
        self.assertTrue(str(learning_result["target_id"]).startswith("learn_"))
        self.assertEqual(queue_result["status"], "clarified")
        self.assertTrue(str(queue_result["target_id"]).startswith("kb_"))
        self.assertEqual(stored.items[0].status, "clarified")
        self.assertGreaterEqual(len(stored.items[0].history), 3)
        self.assertTrue(learning_exists)
        self.assertIn(
            "Extract VLA interview notes",
            kanban_body,
        )

    def test_profile_clarify_to_activity_habit_uses_canonical_add_habit(self) -> None:
        """Inbox-to-habit creates a reusable activity catalog entry."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            inbox = Inbox(profile="demo")
            add_inbox_item(
                inbox,
                "Read Paper",
                item_id="item-1",
                tags=["research"],
            )
            save_inbox(prof, inbox)

            with patch(
                "nblane.core.inbox.git_backup.record_change"
            ), patch(
                "nblane.core.activity_log.git_backup.record_change"
            ), patch(
                "nblane.core.inbox.profile_dir",
                lambda _name: prof,
            ), patch(
                "nblane.core.activity_log.profile_dir",
                lambda _name: prof,
            ):
                result = clarify_inbox_item(
                    "demo",
                    "item-1",
                    "to_activity_habit",
                    {
                        "kind": "learning",
                        "target": {"count": 3, "unit": "paper"},
                    },
                )
                result_again = clarify_inbox_item(
                    "demo",
                    "item-1",
                    "to_activity_habit",
                    {},
                )

            from nblane.core.activity_log import load_activity_log

            log = load_activity_log(prof)

        self.assertEqual(result["target_id"], "read_paper")
        self.assertEqual(result_again["target_id"], "read_paper")
        self.assertEqual(len(log.habits), 1)
        self.assertEqual(log.habits[0].target.unit, "paper")


if __name__ == "__main__":
    unittest.main()
