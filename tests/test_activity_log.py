"""Tests for YAML-backed activity log helpers."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.activity_log import (
    ACTIVITY_LOG_FILENAME,
    ActivityLog,
    ActivityLogParseError,
    Checkin,
    HabitPlan,
    WeeklyTasks,
    add_activity_checkin,
    activity_summary,
    add_habit,
    add_habit_plan,
    add_checkin,
    delete_checkin,
    habit_daily_counts,
    habit_plan_progress,
    load,
    monthly_summary,
    plan_week_bounds,
    plan_week_count,
    plan_week_number,
    resolve_habit_id,
    save,
    update_habit_plan,
    weekly_summary,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ACTIVITY_LOG = (
    REPO_ROOT / "profiles" / "template" / ACTIVITY_LOG_FILENAME
)


class TestActivityLog(unittest.TestCase):
    """Activity log helpers normalize YAML and compute summaries."""

    def test_load_missing_file_returns_empty_log(self) -> None:
        """Missing files load as an empty structured log."""
        with tempfile.TemporaryDirectory() as tmp:
            log = load(Path(tmp) / ACTIVITY_LOG_FILENAME)

        self.assertIsInstance(log, ActivityLog)
        self.assertEqual(log.profile, "")
        self.assertEqual(log.habits, [])
        self.assertEqual(log.checkins, [])
        self.assertEqual(log.weekly_summaries, [])

    def test_load_invalid_yaml_raises_parse_error(self) -> None:
        """Malformed YAML is fail-closed instead of returning an empty log."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ACTIVITY_LOG_FILENAME
            path.write_text("checkins:\n  - [\n", encoding="utf-8")

            with self.assertRaises(ActivityLogParseError) as ctx:
                load(path)

        self.assertEqual(ctx.exception.path, path)

    def test_save_refuses_to_overwrite_invalid_existing_yaml(self) -> None:
        """Direct saves also fail closed when the existing file is malformed."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ACTIVITY_LOG_FILENAME
            original = "checkins:\n  - [\n"
            path.write_text(original, encoding="utf-8")

            with self.assertRaises(ActivityLogParseError):
                save(path, {"profile": "demo"})

            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_load_refuses_non_mapping_yaml(self) -> None:
        """Schema-shaped failures also fail closed instead of becoming empty."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ACTIVITY_LOG_FILENAME
            path.write_text("- not a mapping\n", encoding="utf-8")

            with self.assertRaises(ActivityLogParseError):
                load(path)

    def test_save_refuses_to_overwrite_non_mapping_yaml(self) -> None:
        """Existing scalar/null YAML is treated as unsafe to overwrite."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ACTIVITY_LOG_FILENAME
            original = "null\n"
            path.write_text(original, encoding="utf-8")

            with self.assertRaises(ActivityLogParseError):
                save(path, {"profile": "demo"})

            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_load_tolerates_legacy_shapes_and_dedupes_tags(self) -> None:
        """String habits, singular keys, and weekly maps normalize cleanly."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ACTIVITY_LOG_FILENAME
            path.write_text(
                """
profile: demo
updated: 2026-04-28
habits:
  - Deep Work
  - id: deep_work
    tags: focus, Focus
  - title: Exercise
    tag:
      - health
      - Health
checkins:
  - day: 2026-04-22T09:00:00
    habit:
      - deep_work
      - deep_work
      - exercise
    tag: focus, Focus, energy
    note: Stayed with the hard part.
weekly_summaries:
  2026-W17:
    summary: Good consistency.
    tags:
      - focus
      - Focus
""".strip(),
                encoding="utf-8",
            )

            log = load(path)

        self.assertEqual(len(log.habits), 2)
        self.assertEqual(log.habits[0].id, "deep_work")
        self.assertEqual(log.habits[0].tags, ["focus"])
        self.assertEqual(log.habits[1].id, "exercise")
        self.assertEqual(log.habits[1].tags, ["health"])

        self.assertEqual(len(log.checkins), 1)
        self.assertEqual(log.checkins[0].date, "2026-04-22")
        self.assertEqual(
            log.checkins[0].habits,
            ["deep_work", "exercise"],
        )
        self.assertEqual(
            log.checkins[0].tags,
            ["focus", "energy"],
        )
        self.assertEqual(
            log.weekly_summaries[0].week_start,
            date.fromisocalendar(2026, 17, 1).isoformat(),
        )
        self.assertEqual(
            log.weekly_summaries[0].tags,
            ["focus"],
        )

    def test_checkin_workout_fields_read_and_write(self) -> None:
        """Workout fields normalize without changing legacy check-ins."""
        checkin = Checkin.from_dict(
            {
                "date": "2026-04-28",
                "habit_id": "run",
                "workout_type": " run ",
                "duration_min": "45.5",
                "intensity": " moderate ",
                "metrics": {
                    " distance_km ": 5.2,
                    "avg_hr": 142,
                    "outdoors": True,
                    "effort": "steady",
                    "": 99,
                    "splits": [8, 9],
                    "nested": {"pace": "bad"},
                    "missing": None,
                },
            }
        )

        self.assertEqual(checkin.workout_type, "run")
        self.assertEqual(checkin.duration_min, 45.5)
        self.assertEqual(checkin.intensity, "moderate")
        self.assertEqual(
            checkin.metrics,
            {
                "distance_km": 5.2,
                "avg_hr": 142,
                "outdoors": True,
                "effort": "steady",
            },
        )
        self.assertEqual(
            checkin.to_dict()["metrics"],
            {
                "distance_km": 5.2,
                "avg_hr": 142,
                "outdoors": True,
                "effort": "steady",
            },
        )
        self.assertEqual(checkin.to_dict()["duration_min"], 45.5)

        empty = Checkin.from_dict(
            {
                "date": "2026-04-28",
                "duration_min": "-3",
                "metrics": {"": 1, "bad": []},
            }
        )

        self.assertEqual(empty.duration_min, 0.0)
        self.assertEqual(empty.metrics, {})
        self.assertNotIn("duration_min", empty.to_dict())
        self.assertNotIn("metrics", empty.to_dict())

    def test_checkin_links_read_and_write(self) -> None:
        """Learning links normalize and survive YAML persistence."""
        checkin = Checkin.from_dict(
            {
                "date": "2026-04-28",
                "habit_id": "learning",
                "links": [
                    "https://example.com/video",
                    "https://example.com/video",
                ],
            }
        )

        self.assertEqual(checkin.links, ["https://example.com/video"])
        self.assertEqual(
            Checkin.from_dict(
                {
                    "date": "2026-04-28",
                    "habit_id": "learning",
                    "url": "https://example.com/paper",
                }
            ).links,
            ["https://example.com/paper"],
        )
        self.assertEqual(
            Checkin.from_dict(
                {
                    "date": "2026-04-28",
                    "habit_id": "learning",
                    "urls": ["https://example.com/a"],
                }
            ).links,
            ["https://example.com/a"],
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ACTIVITY_LOG_FILENAME
            with patch("nblane.core.activity_log.git_backup.record_change"):
                save(
                    path,
                    {
                        "profile": "demo",
                        "habits": [{"id": "learning"}],
                        "checkins": [checkin.to_dict()],
                    },
                )
            reloaded = load(path)

        self.assertEqual(
            reloaded.checkins[0].links,
            ["https://example.com/video"],
        )

    def test_save_and_reload_preserves_workout_fields(self) -> None:
        """Workout check-in fields survive YAML persistence."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ACTIVITY_LOG_FILENAME
            with patch("nblane.core.activity_log.git_backup.record_change"):
                save(
                    path,
                    {
                        "profile": "demo",
                        "habits": [{"id": "run"}],
                        "checkins": [
                            {
                                "date": "2026-04-28",
                                "habit_id": "run",
                                "workout_type": "run",
                                "duration_min": 30,
                                "intensity": "hard",
                                "metrics": {
                                    "distance_km": 5,
                                    "avg_hr": 150,
                                },
                            }
                        ],
                    },
                )
            reloaded = load(path)

        self.assertEqual(len(reloaded.checkins), 1)
        self.assertEqual(reloaded.checkins[0].workout_type, "run")
        self.assertEqual(reloaded.checkins[0].duration_min, 30.0)
        self.assertEqual(reloaded.checkins[0].intensity, "hard")
        self.assertEqual(
            reloaded.checkins[0].metrics,
            {"distance_km": 5, "avg_hr": 150},
        )

    def test_save_writes_yaml_and_calls_git_backup(self) -> None:
        """Save writes a comment header and records the file change."""
        with tempfile.TemporaryDirectory() as tmp:
            profile_dir = Path(tmp) / "demo"
            path = profile_dir / ACTIVITY_LOG_FILENAME
            with patch(
                "nblane.core.activity_log.git_backup.record_change"
            ) as mock_backup:
                saved = save(
                    path,
                    {
                        "profile": "demo",
                        "habits": [{"id": "deep_work"}],
                        "checkins": [
                            {
                                "date": "2026-04-28",
                                "summary": "Solid day.",
                                "tags": ["focus", "focus"],
                            }
                        ],
                    },
                )

            content = path.read_text(encoding="utf-8")

        self.assertEqual(saved.profile, "demo")
        self.assertTrue(content.startswith("# Activity log for demo\n"))
        self.assertIn("updated:", content)
        mock_backup.assert_called_once()
        self.assertEqual(
            mock_backup.call_args.kwargs["action"],
            f"update {ACTIVITY_LOG_FILENAME}",
        )

    def test_add_checkin_uses_template_and_normalizes_lists(self) -> None:
        """Adding a check-in works from a copied template file."""
        with tempfile.TemporaryDirectory() as tmp:
            profile_dir = Path(tmp) / "demo"
            profile_dir.mkdir()
            path = profile_dir / ACTIVITY_LOG_FILENAME
            shutil.copyfile(TEMPLATE_ACTIVITY_LOG, path)
            content = path.read_text(encoding="utf-8")
            path.write_text(
                content.replace("{Name}", "demo").replace(
                    "{YYYY-MM-DD}",
                    "2026-04-01",
                ),
                encoding="utf-8",
            )

            with patch(
                "nblane.core.activity_log.git_backup.record_change"
            ) as mock_backup:
                updated = add_checkin(
                    path,
                    habits=["deep_work", "deep_work", "exercise"],
                    tags="focus, Focus, health",
                    summary="Finished the hard thing.",
                )

        self.assertEqual(len(updated.checkins), 1)
        self.assertEqual(
            updated.checkins[0].habits,
            ["deep_work", "exercise"],
        )
        self.assertEqual(
            updated.checkins[0].tags,
            ["focus", "health"],
        )
        self.assertEqual(
            updated.checkins[0].date,
            date.today().isoformat(),
        )
        mock_backup.assert_called_once()

    def test_add_habit_reuses_duplicates_and_resolves_titles(self) -> None:
        """Habit creation has one canonical id resolver for UI and tools."""
        with tempfile.TemporaryDirectory() as tmp:
            profile_dir = Path(tmp) / "demo"
            profile_dir.mkdir()
            with patch(
                "nblane.core.activity_log.git_backup.record_change"
            ):
                first = add_habit(
                    profile_dir,
                    "Read Paper",
                    kind="learning",
                    cadence="weekly",
                    target={"count": 3, "unit": "paper"},
                    tags="paper, research",
                    notes="Track real reading input.",
                )
                duplicate = add_habit(profile_dir, " read paper ")
                checkin = add_activity_checkin(
                    profile_dir,
                    "Read Paper",
                    when="2026-04-28",
                )
            stored = load(profile_dir)

        self.assertEqual(first.id, "read_paper")
        self.assertEqual(duplicate.id, first.id)
        self.assertEqual(len(stored.habits), 1)
        self.assertEqual(stored.habits[0].target.count, 3)
        self.assertEqual(stored.habits[0].target.unit, "paper")
        self.assertEqual(stored.habits[0].tags, ["paper", "research"])
        self.assertEqual(stored.habits[0].notes, "Track real reading input.")
        self.assertEqual(resolve_habit_id(stored, "READ PAPER"), "read_paper")
        self.assertEqual(resolve_habit_id(stored, "read-paper"), "read_paper")
        self.assertEqual(checkin.habit_id, "read_paper")
        self.assertEqual(stored.checkins[0].habit_id, "read_paper")

    def test_add_activity_checkin_writes_workout_fields(self) -> None:
        """Quick activity check-ins can include workout detail."""
        with tempfile.TemporaryDirectory() as tmp:
            profile_dir = Path(tmp) / "demo"
            profile_dir.mkdir()
            with patch("nblane.core.activity_log.git_backup.record_change"):
                add_habit(profile_dir, "Run", kind="health")
                checkin = add_activity_checkin(
                    profile_dir,
                    "run",
                    when="2026-04-28",
                    workout_type="run",
                    duration_min=32,
                    intensity="hard",
                    metrics={
                        "distance_km": 5,
                        "avg_hr": 148,
                        "splits": [6.2, 6.4],
                        "": "drop",
                    },
                )
            stored = load(profile_dir)

        self.assertEqual(checkin.workout_type, "run")
        self.assertEqual(checkin.duration_min, 32.0)
        self.assertEqual(checkin.intensity, "hard")
        self.assertEqual(
            checkin.metrics,
            {"distance_km": 5, "avg_hr": 148},
        )
        self.assertEqual(stored.checkins[0].workout_type, "run")
        self.assertEqual(stored.checkins[0].duration_min, 32.0)
        self.assertEqual(stored.checkins[0].intensity, "hard")
        self.assertEqual(
            stored.checkins[0].metrics,
            {"distance_km": 5, "avg_hr": 148},
        )

    def test_add_activity_checkin_writes_learning_summary_and_links(self) -> None:
        """Learning check-ins can carry notes and links without learning-log."""
        with tempfile.TemporaryDirectory() as tmp:
            profile_dir = Path(tmp) / "demo"
            profile_dir.mkdir()
            with patch("nblane.core.activity_log.git_backup.record_change"):
                add_habit(profile_dir, "Learning", kind="learning")
                checkin = add_activity_checkin(
                    profile_dir,
                    "learning",
                    when="2026-04-28",
                    summary="Read paper notes",
                    note="Line one\nLine two",
                    links=[
                        "https://example.com/paper",
                        "https://example.com/paper",
                    ],
                )
            stored = load(profile_dir)

        self.assertEqual(checkin.habit_id, "learning")
        self.assertEqual(checkin.summary, "Read paper notes")
        self.assertEqual(checkin.notes, "Line one\nLine two")
        self.assertEqual(checkin.links, ["https://example.com/paper"])
        self.assertEqual(stored.checkins[0].links, ["https://example.com/paper"])

    def test_delete_checkin_removes_one_entry_by_id(self) -> None:
        """Accidental check-ins can be removed without touching habits."""
        with tempfile.TemporaryDirectory() as tmp:
            profile_dir = Path(tmp) / "demo"
            profile_dir.mkdir()
            with patch("nblane.core.activity_log.git_backup.record_change"):
                add_habit(profile_dir, "Learning", kind="learning")
                first = add_activity_checkin(
                    profile_dir,
                    "learning",
                    when="2026-04-28",
                    summary="Keep this one",
                )
                second = add_activity_checkin(
                    profile_dir,
                    "learning",
                    when="2026-04-28",
                    summary="Delete this one",
                )
                deleted = delete_checkin(profile_dir, second.id)
                missing = delete_checkin(profile_dir, second.id)
            stored = load(profile_dir)

        self.assertTrue(deleted)
        self.assertFalse(missing)
        self.assertEqual([item.id for item in stored.checkins], [first.id])
        self.assertEqual(stored.habits[0].id, "learning")

    def test_activity_checkin_requires_existing_habit_catalog(self) -> None:
        """Quick check-in never creates an orphan habit by accident."""
        with tempfile.TemporaryDirectory() as tmp:
            profile_dir = Path(tmp) / "demo"
            profile_dir.mkdir()
            with self.assertRaisesRegex(ValueError, "No habits defined"):
                add_activity_checkin(profile_dir, "workout")

            self.assertFalse((profile_dir / ACTIVITY_LOG_FILENAME).exists())

    def test_unknown_legacy_checkin_keeps_summary_warning(self) -> None:
        """Legacy orphan check-ins stay readable but surface warnings."""
        log = ActivityLog.from_dict(
            {
                "profile": "demo",
                "habits": [],
                "checkins": [
                    {"date": "2026-04-28", "habit_id": "orphan"}
                ],
            }
        )

        summary = activity_summary(
            log,
            start="2026-04-28",
            end="2026-04-28",
        )

        self.assertIn(
            "Check-in references unknown habit: orphan",
            log.warnings,
        )
        self.assertEqual(summary.habit_count, 1)
        self.assertEqual(summary.habits[0].id, "orphan")

    def test_activity_summary_groups_weeks_and_habits(self) -> None:
        """Weekly summaries merge check-ins and explicit weekly notes."""
        log = ActivityLog.from_dict(
            {
                "profile": "demo",
                "habits": [
                    {
                        "id": "deep_work",
                        "title": "Deep work",
                        "tags": ["focus"],
                    },
                    {
                        "id": "exercise",
                        "title": "Exercise",
                        "tags": ["health"],
                    },
                ],
                "checkins": [
                    {
                        "date": "2026-04-20",
                        "habits": ["deep_work"],
                        "tags": ["focus"],
                    },
                    {
                        "date": "2026-04-22",
                        "habits": ["deep_work", "exercise"],
                        "tags": ["focus", "health"],
                    },
                    {
                        "date": "2026-04-28",
                        "habits": ["exercise"],
                        "tags": ["health"],
                    },
                ],
                "weekly_summaries": [
                    {
                        "week": "2026-W17",
                        "summary": "Solid rhythm.",
                        "wins": ["Held focus"],
                        "tags": ["focus", "Focus"],
                    }
                ],
            }
        )

        summary = activity_summary(log)

        self.assertEqual(summary.total_checkins, 3)
        self.assertEqual(summary.habit_count, 2)
        self.assertEqual(summary.tag_counts, {"focus": 2, "health": 2})
        self.assertEqual(len(summary.habits), 2)
        self.assertEqual(summary.habits[0].id, "deep_work")
        self.assertEqual(summary.habits[0].checkins, 2)
        self.assertEqual(summary.habits[0].last_checkin, "2026-04-22")
        self.assertEqual(len(summary.weeks), 2)
        self.assertEqual(summary.latest_week.week_start, "2026-04-27")
        self.assertEqual(summary.latest_week.total_checkins, 1)

        previous_week = summary.weeks[1]
        self.assertEqual(previous_week.week_start, "2026-04-20")
        self.assertEqual(previous_week.total_checkins, 2)
        self.assertEqual(
            previous_week.habit_counts,
            {"deep_work": 2, "exercise": 1},
        )
        self.assertEqual(previous_week.summary, "Solid rhythm.")
        self.assertEqual(previous_week.tags, ["focus", "health"])
        self.assertEqual(previous_week.wins, ["Held focus"])

    def test_completion_rate_is_cadence_aware_and_target_strings_parse(self) -> None:
        """Daily targets scale by window while compact weekly targets parse."""
        log = ActivityLog.from_dict(
            {
                "profile": "demo",
                "habits": [
                    {
                        "id": "daily_write",
                        "title": "Daily write",
                        "cadence": "daily",
                        "target": {"count": 1, "unit": "session"},
                    },
                    {
                        "id": "paper_reading",
                        "title": "Paper reading",
                        "target": "3x/week",
                    },
                ],
                "checkins": [
                    {"date": "2026-04-27", "habit_id": "daily_write"},
                    {"date": "2026-04-27", "habit_id": "paper_reading"},
                    {"date": "2026-04-28", "habit_id": "paper_reading"},
                    {"date": "2026-04-29", "habit_id": "paper_reading"},
                ],
            }
        )

        summary = activity_summary(
            log,
            start="2026-04-27",
            end="2026-05-03",
        )
        by_id = {item.id: item for item in summary.habits}

        self.assertAlmostEqual(
            by_id["daily_write"].completion_rate,
            1 / 7,
        )
        self.assertEqual(by_id["paper_reading"].cadence, "weekly")
        self.assertEqual(by_id["paper_reading"].target_count, 3)
        self.assertEqual(by_id["paper_reading"].completion_rate, 1.0)

    def test_weekly_and_monthly_summary_wrappers_return_dicts(self) -> None:
        """Public wrappers expose read-only summary mappings."""
        log = ActivityLog.from_dict(
            {
                "profile": "demo",
                "habits": [{"id": "practice"}],
                "checkins": [
                    {"date": "2026-04-28", "habit_id": "practice"}
                ],
            }
        )

        week = weekly_summary(log, week_start="2026-04-28")
        month = monthly_summary(log, month="2026-04-01")

        self.assertEqual(week["start"], "2026-04-27")
        self.assertEqual(week["end"], "2026-05-03")
        self.assertEqual(month["start"], "2026-04-01")
        self.assertEqual(month["end"], "2026-04-30")

    def test_habit_daily_counts_filters_habits_and_fills_empty_days(self) -> None:
        """Daily count helper powers the simplified workspace calendar."""
        log = ActivityLog.from_dict(
            {
                "profile": "demo",
                "habits": [
                    {"id": "learning"},
                    {"id": "exercise"},
                    {"id": "sleep"},
                ],
                "checkins": [
                    {"date": "2026-04-01", "habit_id": "learning"},
                    {"date": "2026-04-01", "habit_id": "learning"},
                    {
                        "date": "2026-04-02",
                        "habit_id": "exercise",
                        "habits": ["exercise", "learning"],
                    },
                    {"date": "2026-04-02", "habit_id": "sleep"},
                    {"date": "2026-04-04", "habit_id": "learning"},
                ],
            }
        )

        counts = habit_daily_counts(
            log,
            ["learning", "exercise"],
            start="2026-04-01",
            end="2026-04-03",
        )

        self.assertEqual(
            counts,
            {
                "2026-04-01": {"learning": 2, "exercise": 0},
                "2026-04-02": {"learning": 1, "exercise": 1},
                "2026-04-03": {"learning": 0, "exercise": 0},
            },
        )


class TestHabitPlans(unittest.TestCase):
    """Habit plans (阶段计划): parsing, round-trip, week math, progress."""

    PLAN_FIXTURE = {
        "id": "hp_cut",
        "title": "28天减脂计划",
        "habit_id": "exercise",
        "start_date": "2026-09-25",
        "end_date": "2026-10-22",
        "status": "active",
        "weekly_tasks": [
            {"week": 1, "tasks": ["每日晨跑30min", "晚餐碳水减半"]},
            {"week": 2, "tasks": ["每日晨跑30min"]},
            {"week": 3, "tasks": ["每日晨跑30min"]},
            {"week": 4, "tasks": ["每日晨跑30min"]},
        ],
    }

    def _write_log(self, tmp: str, extra: dict | None = None) -> Path:
        path = Path(tmp) / ACTIVITY_LOG_FILENAME
        payload = {
            "profile": "demo",
            "habits": [{"id": "exercise", "title": "Exercise"}],
            "habit_plans": [dict(self.PLAN_FIXTURE)],
            "checkins": [],
        }
        payload.update(extra or {})
        path.write_text(
            yaml.safe_dump(payload, allow_unicode=True),
            encoding="utf-8",
        )
        return path

    def test_habit_plan_round_trip_preserves_fields(self) -> None:
        """from_dict/to_dict keeps id, dates, status, and weekly tasks."""
        plan = HabitPlan.from_dict(dict(self.PLAN_FIXTURE))
        self.assertEqual(plan.id, "hp_cut")
        self.assertEqual(plan.habit_id, "exercise")
        self.assertEqual(plan.start_date, "2026-09-25")
        self.assertEqual(plan.end_date, "2026-10-22")
        self.assertEqual(plan.status, "active")
        self.assertEqual(
            [(w.week, w.tasks) for w in plan.weekly_tasks],
            [
                (1, ["每日晨跑30min", "晚餐碳水减半"]),
                (2, ["每日晨跑30min"]),
                (3, ["每日晨跑30min"]),
                (4, ["每日晨跑30min"]),
            ],
        )
        reloaded = HabitPlan.from_dict(plan.to_dict())
        self.assertEqual(reloaded.to_dict(), plan.to_dict())

    def test_legacy_file_without_habit_plans_loads_empty(self) -> None:
        """Old activity logs without habit_plans stay readable."""
        log = ActivityLog.from_dict(
            {"profile": "demo", "habits": [{"id": "exercise"}], "checkins": []}
        )
        self.assertEqual(log.habit_plans, [])
        self.assertEqual(log.to_dict()["habit_plans"], [])

    def test_plan_with_unknown_habit_warns_but_loads(self) -> None:
        """A dangling habit reference surfaces as a warning, not an error."""
        log = ActivityLog.from_dict(
            {
                "profile": "demo",
                "habits": [{"id": "exercise"}],
                "habit_plans": [dict(self.PLAN_FIXTURE, habit_id="ghost")],
            }
        )
        self.assertEqual(len(log.habit_plans), 1)
        self.assertTrue(
            any("ghost" in warning for warning in log.warnings)
        )

    def test_save_and_reload_preserves_habit_plans(self) -> None:
        """A full save round-trip keeps plans and checkin plan fields."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_log(tmp)
            log = load(path)
            log.checkins.append(
                Checkin(
                    date="2026-09-26",
                    habit_id="exercise",
                    habits=["exercise"],
                    plan_id="hp_cut",
                    week_number=1,
                )
            )
            with patch("nblane.core.git_backup.record_change"):
                save(path, log)
            reloaded = load(path)

        self.assertEqual(
            reloaded.habit_plans[0].to_dict(),
            HabitPlan.from_dict(self.PLAN_FIXTURE).to_dict(),
        )
        entry = reloaded.checkins[0]
        self.assertEqual(entry.plan_id, "hp_cut")
        self.assertEqual(entry.week_number, 1)
        self.assertEqual(
            entry.to_dict().get("plan_id"), "hp_cut"
        )
        self.assertEqual(entry.to_dict().get("week_number"), 1)

    def test_checkin_plan_fields_default_off(self) -> None:
        """Check-ins without a plan omit plan_id/week_number in YAML."""
        entry = Checkin(date="2026-09-26", habit_id="exercise")
        self.assertNotIn("plan_id", entry.to_dict())
        self.assertNotIn("week_number", entry.to_dict())

    def test_week_math_ceil_and_bounds(self) -> None:
        """Week count is ceil(days/7); the tail week clamps to end_date."""
        plan = HabitPlan.from_dict(self.PLAN_FIXTURE)
        self.assertEqual(plan_week_count(plan), 4)
        self.assertEqual(
            plan_week_bounds(plan, 1), ("2026-09-25", "2026-10-01")
        )
        self.assertEqual(
            plan_week_bounds(plan, 4), ("2026-10-16", "2026-10-22")
        )
        self.assertEqual(plan_week_bounds(plan, 5), ("", ""))
        short = HabitPlan(
            id="hp_x", start_date="2026-09-25", end_date="2026-09-28"
        )
        self.assertEqual(plan_week_count(short), 1)
        self.assertEqual(
            plan_week_bounds(short, 1), ("2026-09-25", "2026-09-28")
        )

    def test_plan_week_number_inside_and_outside(self) -> None:
        """Week numbers are 1-based inside the window, None outside."""
        plan = HabitPlan.from_dict(self.PLAN_FIXTURE)
        self.assertEqual(plan_week_number(plan, "2026-09-25"), 1)
        self.assertEqual(plan_week_number(plan, "2026-10-01"), 1)
        self.assertEqual(plan_week_number(plan, "2026-10-02"), 2)
        self.assertEqual(plan_week_number(plan, "2026-10-22"), 4)
        self.assertIsNone(plan_week_number(plan, "2026-09-24"))
        self.assertIsNone(plan_week_number(plan, "2026-10-23"))

    def test_habit_plan_progress_counts_distinct_days(self) -> None:
        """Progress counts distinct checked days per week window."""
        plan = HabitPlan.from_dict(self.PLAN_FIXTURE)
        checkins = [
            Checkin(
                date="2026-09-25",
                habit_id="exercise",
                habits=["exercise"],
                plan_id="hp_cut",
                week_number=1,
            ),
            # Same-day duplicate still counts as one day.
            Checkin(
                date="2026-09-25",
                habit_id="exercise",
                habits=["exercise"],
                plan_id="hp_cut",
                week_number=1,
            ),
            Checkin(
                date="2026-10-03",
                habit_id="exercise",
                habits=["exercise"],
                plan_id="hp_cut",
                week_number=2,
            ),
            # Wrong plan / wrong habit rows never count.
            Checkin(
                date="2026-09-26",
                habit_id="exercise",
                habits=["exercise"],
                plan_id="hp_other",
            ),
            Checkin(
                date="2026-09-26",
                habit_id="reading",
                habits=["reading"],
                plan_id="hp_cut",
            ),
        ]
        progress = habit_plan_progress(
            plan, checkins, today="2026-10-03"
        )
        self.assertEqual(progress.current_week, 2)
        self.assertEqual(progress.days_done, 2)
        self.assertEqual(progress.days_total, 28)
        self.assertAlmostEqual(progress.completion_rate, 2 / 28)
        self.assertEqual(
            [(w.week, w.days_done, w.days_total) for w in progress.weeks],
            [(1, 1, 7), (2, 1, 7), (3, 0, 7), (4, 0, 7)],
        )

    def test_habit_plan_progress_current_week_clamps(self) -> None:
        """current_week is 0 before start and the last week after end."""
        plan = HabitPlan.from_dict(self.PLAN_FIXTURE)
        self.assertEqual(
            habit_plan_progress(plan, [], today="2026-09-01").current_week,
            0,
        )
        self.assertEqual(
            habit_plan_progress(plan, [], today="2026-12-01").current_week,
            4,
        )

    def test_add_and_update_habit_plan_persist(self) -> None:
        """add_habit_plan assigns an hp_ id; update edits selected fields."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_log(tmp)
            plan = HabitPlan(
                id="",
                title="晨跑冲刺",
                habit_id="exercise",
                start_date="2026-10-01",
                end_date="2026-10-07",
                weekly_tasks=[WeeklyTasks(week=1, tasks=["run"])],
            )
            with patch("nblane.core.git_backup.record_change"):
                stored = add_habit_plan(path, plan)
                updated = update_habit_plan(
                    path,
                    stored.id,
                    status="completed",
                    weekly_tasks=[WeeklyTasks(week=1, tasks=["run", "stretch"])],
                )
            reloaded = load(path)

        self.assertEqual(stored.id, "hp_晨跑冲刺")
        self.assertIsNotNone(updated)
        plans = {item.id: item for item in reloaded.habit_plans}
        self.assertEqual(set(plans), {"hp_cut", stored.id})
        self.assertEqual(plans[stored.id].status, "completed")
        self.assertEqual(
            plans[stored.id].weekly_tasks[0].tasks, ["run", "stretch"]
        )
        # Untouched fields survive the partial update.
        self.assertEqual(plans[stored.id].title, "晨跑冲刺")

    def test_add_habit_plan_ids_dedupe(self) -> None:
        """Repeated titles get suffixed ids like other id helpers."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ACTIVITY_LOG_FILENAME
            path.write_text(
                "profile: demo\nhabits: []\n", encoding="utf-8"
            )
            plan = HabitPlan(id="", title="冲刺")
            with patch("nblane.core.git_backup.record_change"):
                first = add_habit_plan(path, HabitPlan(id="", title="冲刺"))
                second = add_habit_plan(path, plan)

        self.assertEqual(first.id, "hp_冲刺")
        self.assertEqual(second.id, "hp_冲刺_2")


if __name__ == "__main__":
    unittest.main()
