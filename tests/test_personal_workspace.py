"""Tests for compact Kanban check-in helper logic."""

from __future__ import annotations

import sys
import types
import unittest
from datetime import date

try:
    import streamlit  # noqa: F401
except ModuleNotFoundError:
    sys.modules.setdefault("streamlit", types.SimpleNamespace())

from nblane.core.activity_log import ActivityLog, Checkin
from nblane.kanban_ui.personal_workspace import (
    EXERCISE_HABIT_ID,
    LEARNING_HABIT_ID,
    checkin_calendar_payload_from_activity,
    checkin_month_payload_from_activity,
    daily_workspace_counts,
    month_day_window,
    recent_day_window,
    workspace_habit_id,
)


class TestPersonalWorkspaceHelpers(unittest.TestCase):
    """Pure helpers keep the check-in strip predictable."""

    def test_recent_day_window_includes_today_and_has_fourteen_days(self) -> None:
        """The compact strip is a fixed 14-day window ending today."""
        today = date(2026, 4, 28)

        days = recent_day_window(today=today, days=14)

        self.assertEqual(len(days), 14)
        self.assertEqual(days[0], date(2026, 4, 15))
        self.assertEqual(days[-1], today)

    def test_workspace_counts_include_legacy_exercise_habit(self) -> None:
        """Legacy Chinese exercise records still count as exercise."""
        target = date(2026, 4, 28)
        log = ActivityLog(
            checkins=[
                Checkin(date=target.isoformat(), habit_id="learning"),
                Checkin(date=target.isoformat(), habit_id="exercise"),
                Checkin(date=target.isoformat(), habit_id="锻炼"),
                Checkin(date=target.isoformat(), habit_id="deep_work"),
            ]
        )

        counts = daily_workspace_counts(log, [target])

        self.assertEqual(workspace_habit_id(log.checkins[2]), "exercise")
        self.assertEqual(
            counts[target.isoformat()],
            {
                LEARNING_HABIT_ID: 1,
                EXERCISE_HABIT_ID: 2,
            },
        )

    def test_calendar_payload_keeps_fourteen_days_and_day_records(self) -> None:
        """The React shell receives a compact 7x2-friendly calendar payload."""
        today = date(2026, 4, 28)
        log = ActivityLog(
            checkins=[
                Checkin(
                    date=today.isoformat(),
                    id="learning_2026-04-28_1",
                    habit_id="learning",
                    summary="Read paper notes",
                ),
                Checkin(
                    date=today.isoformat(),
                    id="exercise_2026-04-28_1",
                    habit_id="锻炼",
                    workout_type="running",
                    duration_min=30,
                    intensity="moderate",
                ),
            ]
        )
        ui = {
            "kb_calendar_weekdays": "一,二,三,四,五,六,日",
            "kb_checkin_strip_title": "最近 14 天",
            "kb_checkin_type_learning": "学习",
            "kb_checkin_type_exercise": "锻炼",
            "kb_checkin_strip_learning_short": "学{count}",
            "kb_checkin_strip_exercise_short": "练{count}",
            "kb_calendar_learning_short": "学 {count}",
            "kb_calendar_exercise_short": "练 {count}",
            "kb_exercise_type_running": "跑步",
            "kb_exercise_intensity_moderate": "中等",
            "kb_checkin_minutes": "{minutes:g} 分钟",
        }

        payload = checkin_calendar_payload_from_activity(
            log,
            ui,
            today=today,
        )

        self.assertEqual(payload["title"], "最近 14 天")
        self.assertEqual(len(payload["days"]), 14)
        self.assertEqual(payload["days"][0]["date"], "2026-04-15")
        self.assertEqual(payload["days"][-1]["date"], "2026-04-28")
        self.assertEqual(payload["days"][-1]["weekday"], "二")
        self.assertTrue(payload["days"][-1]["is_today"])
        self.assertEqual(
            payload["days"][-1]["counts"],
            {"learning": 1, "exercise": 1},
        )
        self.assertEqual(payload["days"][-1]["marker_text"], "学1 练1")
        self.assertEqual(
            payload["days"][-1]["records"],
            [
                {
                    "id": "learning_2026-04-28_1",
                    "date": "2026-04-28",
                    "kind": "learning",
                    "label": "学习",
                    "detail": "Read paper notes",
                    "can_delete": True,
                },
                {
                    "id": "exercise_2026-04-28_1",
                    "date": "2026-04-28",
                    "kind": "exercise",
                    "label": "锻炼",
                    "detail": "跑步 · 30 分钟 · 中等",
                    "can_delete": True,
                },
            ],
        )

    def test_month_day_window_returns_six_week_grid_with_padding(self) -> None:
        """The month grid is stable and padded to complete weeks."""
        cells = month_day_window(2026, 4)

        self.assertEqual(len(cells), 42)
        self.assertIsNone(cells[0])
        self.assertIsNone(cells[1])
        self.assertEqual(cells[2], date(2026, 4, 1))
        self.assertEqual(cells[31], date(2026, 4, 30))
        self.assertIsNone(cells[32])
        self.assertIsNone(cells[-1])

    def test_month_payload_keeps_counts_records_and_month_boundary(self) -> None:
        """Month payload powers the compact calendar without leaking dates."""
        target = date(2026, 4, 28)
        log = ActivityLog(
            checkins=[
                Checkin(
                    date="2026-03-31",
                    id="learning_2026-03-31_1",
                    habit_id="learning",
                    summary="Previous month",
                ),
                Checkin(
                    date=target.isoformat(),
                    id="learning_2026-04-28_1",
                    habit_id="learning",
                    summary="Read paper notes",
                ),
                Checkin(
                    date=target.isoformat(),
                    id="exercise_2026-04-28_1",
                    habit_id="exercise",
                    workout_type="running",
                    duration_min=30,
                    intensity="moderate",
                ),
                Checkin(
                    date="2026-05-01",
                    id="exercise_2026-05-01_1",
                    habit_id="exercise",
                    workout_type="strength",
                ),
            ]
        )
        ui = {
            "kb_calendar_weekdays": "一,二,三,四,五,六,日",
            "kb_checkin_type_learning": "学习",
            "kb_checkin_type_exercise": "锻炼",
            "kb_checkin_strip_learning_short": "学{count}",
            "kb_checkin_strip_exercise_short": "练{count}",
            "kb_calendar_learning_short": "学 {count}",
            "kb_calendar_exercise_short": "练 {count}",
            "kb_exercise_type_running": "跑步",
            "kb_exercise_intensity_moderate": "中等",
            "kb_checkin_minutes": "{minutes:g} 分钟",
        }

        payload = checkin_month_payload_from_activity(
            log,
            ui,
            year=2026,
            month=4,
            today=target,
        )
        days = [item for item in payload["days"] if item]
        by_date = {item["date"]: item for item in days}

        self.assertEqual(payload["month_label"], "2026-04")
        self.assertEqual(len(payload["weeks"]), 6)
        self.assertEqual(len(payload["days"]), 42)
        self.assertEqual(payload["weeks"][0][0], None)
        self.assertEqual(payload["weeks"][0][2]["date"], "2026-04-01")
        self.assertNotIn("2026-03-31", by_date)
        self.assertNotIn("2026-05-01", by_date)
        self.assertEqual(
            by_date[target.isoformat()]["counts"],
            {"learning": 1, "exercise": 1},
        )
        self.assertEqual(
            by_date[target.isoformat()]["marker_text"],
            "学1 练1",
        )
        self.assertTrue(by_date[target.isoformat()]["is_today"])
        self.assertEqual(
            by_date[target.isoformat()]["records"],
            [
                {
                    "id": "learning_2026-04-28_1",
                    "date": "2026-04-28",
                    "kind": "learning",
                    "label": "学习",
                    "detail": "Read paper notes",
                    "can_delete": True,
                },
                {
                    "id": "exercise_2026-04-28_1",
                    "date": "2026-04-28",
                    "kind": "exercise",
                    "label": "锻炼",
                    "detail": "跑步 · 30 分钟 · 中等",
                    "can_delete": True,
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
