"""Tests for project timeline task aggregation helpers."""

from __future__ import annotations

import unittest

from nblane.core.models import KanbanTask
from nblane.core.project_board import ProjectCase
from nblane.core.project_board_events import (
    count_no_anchor_tasks,
    task_anchor,
    task_owned_by_case,
    timeline_date_range,
    timeline_tasks,
)


def _task(**kw) -> KanbanTask:
    base = dict(title="t", id="", project_id="", milestone_id="")
    base.update(kw)
    return KanbanTask(**base)


class TaskAnchorTests(unittest.TestCase):
    def test_completed_wins_over_started(self) -> None:
        t = _task(started_on="2026-01-01", completed_on="2026-02-01")
        self.assertEqual(task_anchor(t), "2026-02-01")

    def test_falls_back_to_started(self) -> None:
        self.assertEqual(task_anchor(_task(started_on="2026-01-01")), "2026-01-01")

    def test_no_date_returns_empty(self) -> None:
        self.assertEqual(task_anchor(_task()), "")


class TaskOwnershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case = ProjectCase(id="project:x", title="X", task_refs=["task:ref"])

    def test_owned_via_project_id(self) -> None:
        self.assertTrue(task_owned_by_case(_task(id="t1", project_id="project:x"), self.case))

    def test_owned_via_task_refs(self) -> None:
        self.assertTrue(task_owned_by_case(_task(id="task:ref"), self.case))

    def test_not_owned(self) -> None:
        self.assertFalse(task_owned_by_case(_task(id="t2", project_id="project:y"), self.case))


class TimelineTasksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case = ProjectCase(id="project:x", title="X")

    def test_filters_drops_no_anchor_and_sorts(self) -> None:
        live = [
            ("Doing", _task(id="a", project_id="project:x", started_on="2026-03-01")),
            ("Queue", _task(id="b", project_id="project:x")),  # no anchor -> dropped
            ("Done", _task(id="c", project_id="project:x", completed_on="2026-01-15", done=True)),
            ("Doing", _task(id="d", project_id="project:other", started_on="2026-02-01")),  # not owned
        ]
        rows = timeline_tasks(self.case, live, [])
        self.assertEqual([r["id"] for r in rows], ["c", "a"])  # sorted by anchor
        self.assertEqual(rows[0]["anchor"], "2026-01-15")
        self.assertTrue(rows[0]["done"])

    def test_includes_archived_and_dedupes_live_wins(self) -> None:
        live = [("Doing", _task(id="a", project_id="project:x", started_on="2026-03-01"))]
        archived = [
            _task(id="a", project_id="project:x", completed_on="2026-02-01", done=True),  # dup id
            _task(id="z", project_id="project:x", completed_on="2026-01-01", done=True),
        ]
        rows = timeline_tasks(self.case, live, archived)
        ids = [r["id"] for r in rows]
        self.assertEqual(ids, ["z", "a"])  # sorted; 'a' kept from live (not archived)
        a_row = next(r for r in rows if r["id"] == "a")
        self.assertFalse(a_row["archived"])
        self.assertEqual(a_row["anchor"], "2026-03-01")  # live started_on, not archive completed
        z_row = next(r for r in rows if r["id"] == "z")
        self.assertTrue(z_row["archived"])

    def test_count_no_anchor(self) -> None:
        live = [
            ("Queue", _task(id="b", project_id="project:x")),
            ("Someday / Maybe", _task(id="e", project_id="project:x")),
            ("Doing", _task(id="a", project_id="project:x", started_on="2026-03-01")),
            ("Queue", _task(id="f", project_id="project:other")),  # not owned, not counted
        ]
        self.assertEqual(count_no_anchor_tasks(self.case, live), 2)

    def test_timeline_date_range_uses_earliest_and_latest_task_dates(self) -> None:
        rows = [
            {
                "anchor": "2026-04-15",
                "started_on": "2026-04-01",
                "completed_on": "2026-04-15",
            },
            {
                "anchor": "2026-05-10",
                "started_on": "2026-05-02",
                "completed_on": "",
            },
        ]
        self.assertEqual(timeline_date_range(rows), "2026-04-01/2026-05-10")

    def test_timeline_date_range_ignores_invalid_dates(self) -> None:
        rows = [
            {"anchor": "2026-99-99", "started_on": "", "completed_on": ""},
            {"anchor": "2026-05-10", "started_on": "", "completed_on": ""},
        ]
        self.assertEqual(timeline_date_range(rows), "2026-05-10")


if __name__ == "__main__":
    unittest.main()
