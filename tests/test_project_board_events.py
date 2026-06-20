"""Tests for the custom project-board component event mapping."""

from __future__ import annotations

import unittest

from nblane.core.project_board import ProjectCase, ProjectMilestone
from nblane.core.project_board_events import (
    case_from_event,
    case_payload,
    clean_ref_list,
    milestone_from_event,
    milestone_payload,
)


class CleanRefListTests(unittest.TestCase):
    def test_strips_dedupes_and_drops_empties(self) -> None:
        self.assertEqual(
            clean_ref_list([" a ", "a", "", None, "b"]),
            ["a", "b"],
        )

    def test_non_list_returns_empty(self) -> None:
        self.assertEqual(clean_ref_list("a"), [])
        self.assertEqual(clean_ref_list(None), [])


class CasePayloadTests(unittest.TestCase):
    def test_roundtrip_fields(self) -> None:
        case = ProjectCase(
            id="project:x",
            title="X",
            status="active",
            kind="research",
            visibility="private",
            time_range="2026",
            summary="s",
            notes="n",
            goal_refs=["goal:1"],
            task_refs=["task:1"],
        )
        payload = case_payload(case)
        self.assertEqual(payload["id"], "project:x")
        self.assertEqual(payload["kind"], "research")
        self.assertEqual(payload["goal_refs"], ["goal:1"])
        self.assertEqual(payload["task_refs"], ["task:1"])
        # ref lists are copies, not the originals
        payload["goal_refs"].append("goal:2")
        self.assertEqual(case.goal_refs, ["goal:1"])


class CaseFromEventTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case = ProjectCase(
            id="project:x",
            title="Old",
            status="active",
            kind="internal",
            visibility="private",
            summary="old summary",
            goal_refs=["goal:1"],
        )

    def test_applies_changes_and_cleans_refs(self) -> None:
        submitted = case_from_event(
            self.case,
            {
                "title": "  New  ",
                "status": "paused",
                "kind": "work",
                "summary": "  fresh  ",
                "goal_refs": ["goal:2", "goal:2", " goal:3 "],
                "task_refs": [],
            },
        )
        self.assertEqual(submitted.title, "New")
        self.assertEqual(submitted.status, "paused")
        self.assertEqual(submitted.kind, "work")
        self.assertEqual(submitted.summary, "fresh")
        self.assertEqual(submitted.goal_refs, ["goal:2", "goal:3"])
        self.assertEqual(submitted.task_refs, [])
        # original untouched
        self.assertEqual(self.case.title, "Old")

    def test_missing_simple_fields_fall_back(self) -> None:
        submitted = case_from_event(self.case, {"title": "Keep"})
        self.assertEqual(submitted.status, "active")
        self.assertEqual(submitted.kind, "internal")
        self.assertEqual(submitted.visibility, "private")

    def test_blank_title_raises(self) -> None:
        with self.assertRaises(ValueError):
            case_from_event(self.case, {"title": "   "})


class MilestoneEventTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ms = ProjectMilestone(
            id="milestone:a",
            title="A",
            status="planned",
            target="2026-Q1",
            task_refs=["task:1"],
        )

    def test_payload_includes_counts(self) -> None:
        payload = milestone_payload(self.ms, done=1, total=3)
        self.assertEqual(payload["id"], "milestone:a")
        self.assertEqual(payload["done_count"], 1)
        self.assertEqual(payload["total_count"], 3)
        self.assertEqual(payload["task_refs"], ["task:1"])

    def test_from_event_applies_and_cleans(self) -> None:
        updated = milestone_from_event(
            self.ms,
            {
                "title": " Done phase ",
                "status": "completed",
                "target": " 2026-Q2 ",
                "task_refs": ["task:1", "task:1", "task:2"],
            },
        )
        self.assertEqual(updated.title, "Done phase")
        self.assertEqual(updated.status, "completed")
        self.assertEqual(updated.target, "2026-Q2")
        self.assertEqual(updated.task_refs, ["task:1", "task:2"])

    def test_blank_title_raises(self) -> None:
        with self.assertRaises(ValueError):
            milestone_from_event(self.ms, {"title": ""})


if __name__ == "__main__":
    unittest.main()
