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
    load_agent_activity,
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
                        "target_owner": "evidence_pool",
                        "status": "pending",
                        "title": "Pending",
                    },
                )
                summary = activity_summary("alice")
                rows = activity_items_for_page("alice", {"status": "pending"})

        self.assertEqual(summary["status"]["pending"], 1)
        self.assertEqual(summary["target_owner"]["public_site"], 1)
        self.assertEqual([row["id"] for row in rows], ["act:pending"])


if __name__ == "__main__":
    unittest.main()
