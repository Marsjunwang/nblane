"""Tests for Agent Activity / Review writeback helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.agent_activity import (
    activity_items_for_page,
    activity_summary,
    append_activity_item,
    delete_activity_items,
    delete_activity_items_for_filters,
    load_agent_activity,
    save_agent_activity,
    update_activity_status,
)


class TestAgentActivity(unittest.TestCase):
    """Activity queue stays append-only-ish and profile scoped."""

    def test_missing_activity_file_reads_empty(self) -> None:
        """Old profiles without agent-activity.yaml remain compatible."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            activity = load_agent_activity(profile)

        self.assertEqual(activity["items"], [])
        self.assertEqual(activity["profile"], "alice")

    def test_append_updates_duplicate_id(self) -> None:
        """Saving the same Review candidate id updates rather than duplicates."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with patch("nblane.core.agent_activity.profile_dir", lambda _name: profile):
                first = append_activity_item(
                    "alice",
                    {
                        "id": "act:review:evidence:1",
                        "kind": "candidate",
                        "candidate_type": "evidence",
                        "source_page": "Review",
                        "target_owner": "evidence_pool",
                        "status": "pending",
                        "title": "First",
                        "payload": {"x": 1},
                    },
                )
                second = append_activity_item(
                    "alice",
                    {
                        "id": "act:review:evidence:1",
                        "kind": "candidate",
                        "candidate_type": "evidence",
                        "source_page": "Review",
                        "target_owner": "evidence_pool",
                        "status": "pending",
                        "title": "Updated",
                        "payload": {"x": 2},
                    },
                )
                activity = load_agent_activity("alice")

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(activity["items"]), 1)
        self.assertEqual(activity["items"][0]["title"], "Updated")
        self.assertEqual(activity["items"][0]["payload"], {"x": 2})

    def test_status_update_preserves_payload(self) -> None:
        """Dismiss / reopen only changes review state metadata."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with patch("nblane.core.agent_activity.profile_dir", lambda _name: profile):
                append_activity_item(
                    "alice",
                    {
                        "id": "act:1",
                        "title": "Candidate",
                        "payload": {"keep": True},
                    },
                )
                update_activity_status("alice", "act:1", "dismissed")
                reopened = update_activity_status("alice", "act:1", "pending")

        self.assertEqual(reopened["status"], "pending")
        self.assertEqual(reopened["payload"], {"keep": True})

    def test_summary_and_filters(self) -> None:
        """Activity page helpers count and filter common dimensions."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with patch("nblane.core.agent_activity.profile_dir", lambda _name: profile):
                append_activity_item(
                    "alice",
                    {
                        "id": "act:applied",
                        "kind": "writeback",
                        "candidate_type": "blog_patch",
                        "source_page": "Review",
                        "target_owner": "public_site",
                        "status": "applied",
                        "title": "Applied",
                    },
                )
                append_activity_item(
                    "alice",
                    {
                        "id": "act:pending",
                        "kind": "candidate",
                        "candidate_type": "evidence",
                        "source_page": "Kanban",
                        "target_owner": "evidence_pool",
                        "status": "pending",
                        "title": "Pending",
                    },
                )
                summary = activity_summary("alice")
                rows = activity_items_for_page("alice", {"status": "pending"})
                source_rows = activity_items_for_page(
                    "alice",
                    {"source_page": "Kanban"},
                )

        self.assertEqual(summary["status"]["pending"], 1)
        self.assertEqual(summary["target_owner"]["public_site"], 1)
        self.assertEqual([row["id"] for row in rows], ["act:pending"])
        self.assertEqual([row["id"] for row in source_rows], ["act:pending"])

    def test_activity_sort_modes(self) -> None:
        """Activity lists default to newest-first and keep queue sorting available."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with patch("nblane.core.agent_activity.profile_dir", lambda _name: profile):
                save_agent_activity(
                    "alice",
                    {
                        "items": [
                            {
                                "id": "act:old-pending",
                                "status": "pending",
                                "title": "Old pending",
                                "updated": "2026-05-17T00:00:00+00:00",
                            },
                            {
                                "id": "act:new-applied",
                                "status": "applied",
                                "title": "New applied",
                                "updated": "2026-05-19T00:00:00+00:00",
                            },
                            {
                                "id": "act:mid-failed",
                                "status": "failed",
                                "title": "Mid failed",
                                "updated": "2026-05-18T00:00:00+00:00",
                            },
                        ]
                    },
                )
                newest = activity_items_for_page("alice")
                oldest = activity_items_for_page("alice", sort="updated_asc")
                queue = activity_items_for_page("alice", sort="queue")

        self.assertEqual(
            [item["id"] for item in newest],
            ["act:new-applied", "act:mid-failed", "act:old-pending"],
        )
        self.assertEqual(
            [item["id"] for item in oldest],
            ["act:old-pending", "act:mid-failed", "act:new-applied"],
        )
        self.assertEqual(queue[0]["id"], "act:old-pending")

    def test_delete_activity_items_removes_only_selected_ids(self) -> None:
        """Direct deletion removes selected Activity rows without archiving."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with patch("nblane.core.agent_activity.profile_dir", lambda _name: profile):
                save_agent_activity(
                    "alice",
                    {
                        "items": [
                            {"id": "act:keep", "title": "Keep"},
                            {"id": "act:delete", "title": "Delete"},
                        ]
                    },
                )
                removed = delete_activity_items("alice", ["act:delete", "missing"])
                rows = load_agent_activity("alice")["items"]

        self.assertEqual(removed, 1)
        self.assertEqual([item["id"] for item in rows], ["act:keep"])

    def test_delete_activity_items_for_filters(self) -> None:
        """Filtered deletion removes all rows matching simple Activity fields."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with patch("nblane.core.agent_activity.profile_dir", lambda _name: profile):
                save_agent_activity(
                    "alice",
                    {
                        "items": [
                            {
                                "id": "act:failed-kanban",
                                "title": "Failed",
                                "source_page": "Kanban",
                                "status": "failed",
                            },
                            {
                                "id": "act:pending-kanban",
                                "title": "Pending",
                                "source_page": "Kanban",
                                "status": "pending",
                            },
                            {
                                "id": "act:failed-review",
                                "title": "Review failed",
                                "source_page": "Review",
                                "status": "failed",
                            },
                        ]
                    },
                )
                removed = delete_activity_items_for_filters(
                    "alice",
                    {"source_page": "Kanban", "status": "failed"},
                )
                rows = load_agent_activity("alice")["items"]

        self.assertEqual(removed, 1)
        self.assertEqual(
            [item["id"] for item in rows],
            ["act:pending-kanban", "act:failed-review"],
        )

    def test_activity_page_supports_query_focus_and_source_grouping(self) -> None:
        """The Streamlit page accepts activity_item/source_page query jumps."""

        source = Path("pages/9_Agent_Activity.py").read_text(encoding="utf-8")

        self.assertIn('_query_value("activity_item")', source)
        self.assertIn('_query_value("source_page")', source)
        self.assertIn("def _group_items_by_source", source)
        self.assertIn("def _render_activity_module", source)
        self.assertIn("module_tabs = st.tabs", source)
        self.assertIn("source_module", source)
        self.assertIn("def _render_focus_scroll", source)
        self.assertIn("scrollIntoView", source)
        self.assertIn("focused_item_highlight", source)
        self.assertNotIn("source_module = st.radio", source)
        self.assertNotIn(
            "key=lambda item: 0 if str(item.get(\"id\") or \"\") == target_activity_item else 1",
            source,
        )


if __name__ == "__main__":
    unittest.main()
