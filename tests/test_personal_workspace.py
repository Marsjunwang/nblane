"""Tests for compact Kanban check-in helper logic."""

from __future__ import annotations

import sys
import tempfile
import types
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

try:
    import streamlit  # noqa: F401
except ModuleNotFoundError:
    sys.modules.setdefault("streamlit", types.SimpleNamespace())

from nblane.core.activity_log import ActivityLog, Checkin
from nblane.core.paths import REPO_ROOT
from nblane.kanban_ui.personal_workspace import (
    EXERCISE_HABIT_ID,
    LEARNING_HABIT_ID,
    checkin_calendar_payload_from_activity,
    checkin_month_payload,
    checkin_month_payload_from_activity,
    daily_workspace_counts,
    month_day_window,
    record_learning_checkin,
    recent_day_window,
    workspace_habit_id,
)


def _load_kanban_page_helpers():
    """Load Kanban page helpers without running the page body."""
    path = REPO_ROOT / "pages" / "3_Kanban.py"
    source = path.read_text(encoding="utf-8")
    marker = "# -- Page "
    helper_source = source.split(marker, 1)[0]
    module = types.ModuleType("kanban_page_helpers")
    module.__file__ = str(path)
    exec(compile(helper_source, str(path), "exec"), module.__dict__)
    return module


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

    def test_invalid_activity_yaml_marks_payload_unwritable(self) -> None:
        """The workspace catches malformed YAML instead of returning records."""
        with tempfile.TemporaryDirectory() as tmp:
            profile_path = Path(tmp) / "demo"
            profile_path.mkdir()
            (profile_path / "activity-log.yaml").write_text(
                "checkins:\n  - [\n",
                encoding="utf-8",
            )
            with patch("nblane.kanban_ui.personal_workspace.st") as mock_st:
                payload = checkin_month_payload(
                    "demo",
                    profile_path,
                    {},
                    year=2026,
                    month=4,
                    today=date(2026, 4, 28),
                )

        self.assertFalse(payload["activity_log_writable"])
        self.assertIn("activity-log.yaml", payload["activity_log_error"])
        mock_st.error.assert_called_once()

    def test_invalid_activity_yaml_blocks_workspace_writes(self) -> None:
        """Malformed activity-log.yaml stays untouched on check-in attempts."""
        with tempfile.TemporaryDirectory() as tmp:
            profile_path = Path(tmp) / "demo"
            profile_path.mkdir()
            path = profile_path / "activity-log.yaml"
            original = "checkins:\n  - [\n"
            path.write_text(original, encoding="utf-8")

            with (
                patch("nblane.kanban_ui.personal_workspace.st") as mock_st,
                patch(
                    "nblane.kanban_ui.personal_workspace.assert_files_current"
                ),
                patch(
                    "nblane.kanban_ui.personal_workspace.refresh_file_snapshots"
                ) as mock_refresh,
            ):
                record_learning_checkin(
                    profile_path,
                    when=date(2026, 4, 28),
                    note="Should not write",
                    links=[],
                )

            self.assertEqual(path.read_text(encoding="utf-8"), original)
        mock_st.error.assert_called_once()
        mock_refresh.assert_not_called()

    def test_toolbar_calendar_state_updates_without_navigation_url(self) -> None:
        """Date clicks update Streamlit state instead of building anchor links."""
        helpers = _load_kanban_page_helpers()
        fake_st = types.SimpleNamespace(session_state={}, query_params={})

        with patch.object(helpers, "st", fake_st):
            helpers._store_checkin_calendar_state(
                "demo",
                month_label="2026-04",
                day_iso="2026-04-28",
                open_detail=True,
            )

        self.assertEqual(
            fake_st.session_state["kb_toolbar_checkin_month_demo"],
            "2026-04",
        )
        self.assertEqual(
            fake_st.session_state["kb_toolbar_checkin_day_demo"],
            "2026-04-28",
        )
        self.assertTrue(
            fake_st.session_state["kb_toolbar_checkin_detail_open_demo"]
        )
        self.assertEqual(
            fake_st.query_params,
            {
                "kb_ci_month": "2026-04",
                "kb_ci_day": "2026-04-28",
                "kb_ci_open": "1",
            },
        )
        self.assertFalse(hasattr(helpers, "_checkin_query_href"))
        self.assertFalse(hasattr(helpers, "_month_calendar_html"))


if __name__ == "__main__":
    unittest.main()
