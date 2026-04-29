"""Tests for weekly growth review aggregation."""

from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.growth_review import (
    build_weekly_growth_review,
    build_weekly_review,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    _write(
        profile / "kanban.md",
        """# Alice · Kanban

## Doing

- [ ] Ship activity log
  - context: future work

## Done

- [x] Close weekly loop
  - context: weekly review
  - outcome: review notes collected
  - completed_on: 2026-04-27
  - crystallized: true
  - detail line

- [x] Draft learning memo
  - outcome: memo published

## Queue

- [ ] Something else
""",
    )
    return profile


class TestGrowthReview(unittest.TestCase):
    """Growth review aggregation stays read-only and deterministic."""

    def test_build_weekly_growth_review_aggregates_done_tasks_and_logs(
        self,
    ) -> None:
        """Done tasks and optional summaries are collected together."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))

            activity_module = types.ModuleType(
                "nblane.core.activity_log"
            )
            learning_module = types.ModuleType(
                "nblane.core.learning_log"
            )

            def load_activity_log(profile_dir: Path) -> list[dict]:
                self.assertEqual(profile_dir, profile)
                return [
                    {"summary": "shipped aggregation"},
                    {"summary": "reviewed kanban"},
                ]

            def summarize_activity_log(entries: list[dict]) -> dict:
                return {
                    "count": len(entries),
                    "items": [entry["summary"] for entry in entries],
                }

            def load(path: Path) -> list[str]:
                self.assertEqual(path, profile)
                return ["read postmortem", "wrote memo"]

            def summarize(log: list[str]) -> dict:
                return {
                    "count": len(log),
                    "headline": log[0],
                }

            activity_module.load_activity_log = load_activity_log
            activity_module.summarize_activity_log = (
                summarize_activity_log
            )
            learning_module.load = load
            learning_module.summarize = summarize

            with patch.dict(
                sys.modules,
                {
                    "nblane.core.activity_log": activity_module,
                    "nblane.core.learning_log": learning_module,
                },
            ):
                review = build_weekly_growth_review(
                    "alice",
                    profile_path=profile,
                )

            self.assertEqual(review.profile, "alice")
            self.assertEqual(review.profile_path, profile)
            self.assertEqual(review.done_count, 2)
            self.assertEqual(review.crystallized_done_count, 1)
            self.assertEqual(
                [task.title for task in review.done_tasks],
                ["Close weekly loop", "Draft learning memo"],
            )
            self.assertEqual(
                review.done_tasks[0].outcome,
                "review notes collected",
            )
            self.assertEqual(
                review.done_tasks[0].completed_on,
                "2026-04-27",
            )
            self.assertEqual(
                review.done_tasks[0].details,
                ["detail line"],
            )
            self.assertTrue(review.activity.source_available)
            self.assertEqual(review.activity.entry_count, 2)
            self.assertEqual(
                review.activity.summary,
                {
                    "count": 2,
                    "items": [
                        "shipped aggregation",
                        "reviewed kanban",
                    ],
                },
            )
            self.assertTrue(review.learning.source_available)
            self.assertEqual(review.learning.entry_count, 2)
            self.assertEqual(
                review.learning.summary,
                {
                    "count": 2,
                    "headline": "read postmortem",
                },
            )

    def test_build_weekly_growth_review_handles_missing_optional_modules(
        self,
    ) -> None:
        """Missing activity/learning helpers produce empty summaries."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            with patch(
                "nblane.core.growth_review._load_optional_module",
                side_effect=lambda name: None,
            ):
                review = build_weekly_growth_review(
                    "alice",
                    profile_path=profile,
                )

            self.assertEqual(review.done_count, 2)
            self.assertFalse(review.activity.source_available)
            self.assertEqual(review.activity.entry_count, 0)
            self.assertIsNone(review.activity.summary)
            self.assertFalse(review.learning.source_available)
            self.assertEqual(review.learning.entry_count, 0)
            self.assertIsNone(review.learning.summary)

    def test_build_weekly_growth_review_uses_default_profile_lookup(
        self,
    ) -> None:
        """The aggregator can resolve a profile path from profile_dir."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            with patch(
                "nblane.core.growth_review.profile_dir",
                lambda _name: profile,
            ):
                review = build_weekly_growth_review("alice")

            self.assertEqual(review.profile_path, profile)
            self.assertEqual(review.done_count, 2)

    def test_build_weekly_growth_review_reads_real_activity_and_learning_logs(
        self,
    ) -> None:
        """Real YAML-backed helpers are picked up through flexible signatures."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            _write(
                profile / "activity-log.yaml",
                """profile: alice
updated: 2026-04-28
habits:
  - id: reading
    title: Reading
checkins:
  - date: 2026-04-27
    habits: [reading]
    tags: [habit/reading]
    summary: reviewed notes
""",
            )
            _write(
                profile / "learning-log.yaml",
                """profile: alice
updated: 2026-04-28
entries:
  - id: resource-1
    title: Paper
    resource_kind: paper
    status: active
    tags: [ml]
""",
            )

            review = build_weekly_growth_review(
                "alice",
                profile_path=profile,
            )

        self.assertTrue(review.activity.source_available)
        self.assertEqual(review.activity.entry_count, 1)
        self.assertIsInstance(review.activity.summary, object)
        self.assertTrue(review.learning.source_available)
        self.assertEqual(review.learning.entry_count, 1)
        self.assertEqual(
            getattr(review.learning.summary, "active_titles", []),
            ["Paper"],
        )

    def test_build_weekly_review_returns_candidates_without_mutation(self) -> None:
        """Weekly review emits drafts and summaries without writing canonical files."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            _write(
                profile / "kanban.md",
                """# Alice · Kanban

## Done

- [x] Ship public demo
  - id: done-public
  - tags: visibility/public_candidate, project/demo
  - outcome: demo shipped
  - completed_on: 2026-04-28

- [x] Private cleanup
  - id: done-private
  - outcome: cleaned notes
  - completed_on: 2026-04-28

## Queue
""",
            )
            _write(
                profile / "activity-log.yaml",
                """profile: alice
habits:
  - id: workout
    title: Workout
checkins:
  - id: act_1
    habit_id: workout
    date: 2026-04-28
""",
            )
            _write(
                profile / "learning-log.yaml",
                """profile: alice
resources:
  - id: learn_1
    kind: paper
    title: Paper
    added_at: 2026-04-28
    status: processed
    visibility: public_candidate
    next_actions:
      - title: Reproduce setup
        target: kanban_queue
""",
            )
            _write(
                profile / "inbox.yaml",
                """profile: alice
items:
  - id: inbox_1
    type: note
    title: Triage me
    status: inbox
""",
            )
            before = {
                path.name: path.read_text(encoding="utf-8")
                for path in profile.glob("*.yaml")
            }
            before["kanban.md"] = (profile / "kanban.md").read_text(
                encoding="utf-8"
            )

            review = build_weekly_review(
                "alice",
                "2026-04-27",
                "2026-05-03",
                profile_path=profile,
            )

            after = {
                path.name: path.read_text(encoding="utf-8")
                for path in profile.glob("*.yaml")
            }
            after["kanban.md"] = (profile / "kanban.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(before, after)
        self.assertEqual(
            review.done_task_ids,
            ["done-public", "done-private"],
        )
        self.assertEqual(review.inbox_summary["total_items"], 1)
        self.assertEqual(len(review.evidence_candidates), 2)
        self.assertEqual(
            review.next_queue_candidates[0]["title"],
            "Reproduce setup",
        )
        self.assertEqual(len(review.public_candidates), 2)
        self.assertTrue(
            all(item["draft"] for item in review.public_candidates)
        )


if __name__ == "__main__":
    unittest.main()
