"""Tests for the habit-plan (阶段计划) endpoints.

Covers GET /profiles/{name}/habit-plans (list + computed progress),
POST /profiles/{name}/habit-plans (create + weekly kanban card
generation), PATCH /profiles/{name}/habit-plans/{plan_id} (forward-only
status flow + title/weekly_tasks edits), the ``plan_id`` extension of
POST /profiles/{name}/checkins, and the If-Match/412 discipline. All
profiles are built under tmp dirs; real profiles/ is never touched.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core.kanban_io import KANBAN_QUEUE, parse_kanban
from nblane.web_api import app

ACTIVITY_LOG_FIXTURE = {
    "profile": "alice",
    "habits": [
        {"id": "exercise", "title": "Exercise", "kind": "health",
         "cadence": "daily"},
        {"id": "reading", "title": "Reading", "kind": "learning",
         "cadence": "daily"},
    ],
    "checkins": [],
}

PROJECT_BOARD_FIXTURE = {
    "profile": "alice",
    "project_cases": [
        {"id": "pc_fitness", "title": "Fitness", "status": "active",
         "habit_id": "exercise"},
        {"id": "pc_old", "title": "Old push", "status": "archived",
         "habit_id": "exercise"},
    ],
}

PLAN_BODY = {
    "title": "28天减脂计划",
    "habit_id": "exercise",
    "start_date": "2026-09-25",
    "end_date": "2026-10-22",
    "weekly_tasks": [
        {"week": 1, "tasks": ["每日晨跑30min", "晚餐碳水减半"]},
        {"week": 2, "tasks": ["每日晨跑30min"]},
        {"week": 3, "tasks": ["每日晨跑30min"]},
        {"week": 4, "tasks": ["复盘"]},
    ],
}


def _write_profile(
    root: Path,
    name: str = "alice",
    *,
    with_board: bool = True,
) -> Path:
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "activity-log.yaml").write_text(
        yaml.safe_dump(dict(ACTIVITY_LOG_FIXTURE), allow_unicode=True),
        encoding="utf-8",
    )
    if with_board:
        (profile / "project-board.yaml").write_text(
            yaml.safe_dump(dict(PROJECT_BOARD_FIXTURE), allow_unicode=True),
            encoding="utf-8",
        )
    return profile


def _read_activity_log(pdir: Path) -> dict:
    return yaml.safe_load(
        (pdir / "activity-log.yaml").read_text(encoding="utf-8")
    )


class HabitPlanTestBase(unittest.TestCase):
    """Shared env patching: profile roots plus git-backup isolation."""

    def _client(self, root: Path) -> TestClient:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
            "nblane.core.project_board.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch("nblane.core.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)

    def _create_plan(
        self, client: TestClient, **overrides: object
    ) -> dict:
        body = dict(PLAN_BODY)
        body.update(overrides)
        response = client.post(
            "/api/v1/profiles/alice/habit-plans", json=body
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()


class TestHabitPlanCreate(HabitPlanTestBase):
    """POST /habit-plans — validation, persistence, weekly cards."""

    def test_create_persists_plan_and_generates_weekly_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            payload = self._create_plan(client)
            disk = _read_activity_log(pdir)
            sections = parse_kanban(pdir)
            queue = sections.get(KANBAN_QUEUE) or []

        plan = payload["plan"]
        self.assertEqual(plan["title"], "28天减脂计划")
        self.assertEqual(plan["habit_id"], "exercise")
        self.assertEqual(plan["start_date"], "2026-09-25")
        self.assertEqual(plan["end_date"], "2026-10-22")
        self.assertEqual(plan["status"], "active")
        self.assertTrue(plan["id"].startswith("hp_"))
        self.assertEqual(len(plan["weeks"]), 4)
        self.assertEqual(plan["days_total"], 28)
        self.assertEqual(plan["days_done"], 0)
        stored = disk["habit_plans"][0]
        self.assertEqual(stored["id"], plan["id"])
        self.assertEqual(stored["habit_id"], "exercise")
        self.assertEqual(len(stored["weekly_tasks"]), 4)

        self.assertEqual(len(payload["kanban_card_ids"]), 4)
        self.assertEqual(
            [task.title for task in queue],
            ["28天减脂计划 W1", "28天减脂计划 W2",
             "28天减脂计划 W3", "28天减脂计划 W4"],
        )
        self.assertEqual(
            [task.id for task in queue], payload["kanban_card_ids"]
        )
        first = queue[0]
        self.assertEqual(first.planned_start, "2026-09-25")
        self.assertEqual(first.planned_end, "2026-10-01")
        self.assertEqual(
            [todo.text for todo in first.todos],
            ["每日晨跑30min", "晚餐碳水减半"],
        )
        # Cards link to the first ACTIVE case carrying the habit.
        self.assertEqual(first.project_id, "pc_fitness")
        last = queue[-1]
        self.assertEqual(last.planned_start, "2026-10-16")
        self.assertEqual(last.planned_end, "2026-10-22")

    def test_create_without_active_case_leaves_cards_unlinked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root, with_board=False)
            client = self._client(root)
            payload = self._create_plan(client)
            queue = parse_kanban(pdir).get(KANBAN_QUEUE) or []

        self.assertEqual(len(payload["kanban_card_ids"]), 4)
        self.assertTrue(all(task.project_id == "" for task in queue))

    def test_create_with_cards_disabled_writes_no_kanban(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            payload = self._create_plan(client, generate_weekly_cards=False)

        self.assertEqual(payload["kanban_card_ids"], [])
        self.assertFalse((pdir / "kanban.md").exists())

    def test_create_rejects_unknown_habit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/habit-plans",
                json=dict(PLAN_BODY, habit_id="ghost"),
            )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "habit_plan_habit_not_found")

    def test_create_rejects_reversed_or_bad_dates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            reversed_range = client.post(
                "/api/v1/profiles/alice/habit-plans",
                json=dict(
                    PLAN_BODY,
                    end_date="2026-09-01",
                    weekly_tasks=[{"week": 1, "tasks": ["x"]}],
                ),
            )
            bad_date = client.post(
                "/api/v1/profiles/alice/habit-plans",
                json=dict(PLAN_BODY, start_date="not-a-date"),
            )

        self.assertEqual(reversed_range.status_code, 422)
        self.assertEqual(reversed_range.json()["code"], "invalid_plan_range")
        self.assertEqual(bad_date.status_code, 422)
        self.assertEqual(bad_date.json()["code"], "invalid_plan_dates")

    def test_create_rejects_weekly_tasks_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            too_few = client.post(
                "/api/v1/profiles/alice/habit-plans",
                json=dict(
                    PLAN_BODY,
                    weekly_tasks=[{"week": 1, "tasks": ["x"]}],
                ),
            )
            wrong_numbers = client.post(
                "/api/v1/profiles/alice/habit-plans",
                json=dict(
                    PLAN_BODY,
                    weekly_tasks=[
                        {"week": week, "tasks": []} for week in (1, 2, 3, 5)
                    ],
                ),
            )

        self.assertEqual(too_few.status_code, 422)
        self.assertEqual(too_few.json()["code"], "invalid_weekly_tasks")
        self.assertEqual(wrong_numbers.status_code, 422)
        self.assertEqual(wrong_numbers.json()["code"], "invalid_weekly_tasks")

    def test_create_rejects_blank_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/habit-plans",
                json=dict(PLAN_BODY, title="  "),
            )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_habit_plan")

    def test_create_allows_partial_tail_week(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            payload = self._create_plan(
                client,
                start_date="2026-09-25",
                end_date="2026-10-03",
                weekly_tasks=[
                    {"week": 1, "tasks": ["a"]},
                    {"week": 2, "tasks": ["b"]},
                ],
            )

        plan = payload["plan"]
        self.assertEqual(plan["days_total"], 9)
        self.assertEqual(
            [(w["week"], w["start"], w["end"]) for w in plan["weeks"]],
            [(1, "2026-09-25", "2026-10-01"),
             (2, "2026-10-02", "2026-10-03")],
        )


class TestHabitPlanListAndPatch(HabitPlanTestBase):
    """GET /habit-plans and PATCH /habit-plans/{plan_id}."""

    def test_list_reports_progress_after_plan_checkins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            created = self._create_plan(client, generate_weekly_cards=False)
            plan_id = created["plan"]["id"]
            for day in ("2026-09-25", "2026-09-26", "2026-10-05"):
                response = client.post(
                    "/api/v1/profiles/alice/checkins",
                    json={
                        "habit": "exercise",
                        "plan_id": plan_id,
                        "date": day,
                    },
                )
                self.assertEqual(response.status_code, 201, response.text)
            listing = client.get("/api/v1/profiles/alice/habit-plans")

        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.headers.get("etag"))
        plan = listing.json()["plans"][0]
        self.assertEqual(plan["days_done"], 3)
        self.assertEqual(plan["days_total"], 28)
        self.assertAlmostEqual(plan["completion_rate"], 3 / 28)
        self.assertEqual(
            [(w["week"], w["days_done"]) for w in plan["weeks"]],
            [(1, 2), (2, 1), (3, 0), (4, 0)],
        )
        # current_week tracks the wall clock: 0 before start, the final
        # week after end, and 1..4 while the plan is running.
        today = date.today().isoformat()
        if today < "2026-09-25":
            expected_week = 0
        elif today > "2026-10-22":
            expected_week = 4
        else:
            expected_week = (
                date.fromisoformat(today) - date.fromisoformat("2026-09-25")
            ).days // 7 + 1
        self.assertEqual(plan["current_week"], expected_week)

    def test_list_filters_by_habit_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            first = self._create_plan(client, generate_weekly_cards=False)
            self._create_plan(
                client,
                title="读书月",
                habit_id="reading",
                start_date="2026-09-25",
                end_date="2026-10-01",
                weekly_tasks=[{"week": 1, "tasks": ["读一章"]}],
                generate_weekly_cards=False,
            )
            by_habit = client.get(
                "/api/v1/profiles/alice/habit-plans",
                params={"habit_id": "reading"},
            )
            client.patch(
                f"/api/v1/profiles/alice/habit-plans/"
                f"{first['plan']['id']}",
                json={"status": "archived"},
            )
            archived = client.get(
                "/api/v1/profiles/alice/habit-plans",
                params={"status": "archived"},
            )
            active = client.get("/api/v1/profiles/alice/habit-plans")

        self.assertEqual(
            [p["habit_id"] for p in by_habit.json()["plans"]], ["reading"]
        )
        self.assertEqual(len(archived.json()["plans"]), 1)
        self.assertEqual(
            {p["status"] for p in active.json()["plans"]},
            {"archived", "active"},
        )

    def test_patch_status_title_and_weekly_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            created = self._create_plan(client, generate_weekly_cards=False)
            plan_id = created["plan"]["id"]
            patched = client.patch(
                f"/api/v1/profiles/alice/habit-plans/{plan_id}",
                json={
                    "status": "completed",
                    "title": "减脂收官",
                    "weekly_tasks": [
                        {"week": week, "tasks": ["维持"]}
                        for week in (1, 2, 3, 4)
                    ],
                },
            )
            disk = _read_activity_log(pdir)

        self.assertEqual(patched.status_code, 200)
        plan = patched.json()["plan"]
        self.assertEqual(plan["status"], "completed")
        self.assertEqual(plan["title"], "减脂收官")
        self.assertEqual(
            [w["tasks"] for w in plan["weekly_tasks"]],
            [["维持"]] * 4,
        )
        stored = disk["habit_plans"][0]
        self.assertEqual(stored["status"], "completed")
        self.assertEqual(stored["title"], "减脂收官")

    def test_patch_rejects_backward_or_unknown_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            created = self._create_plan(client, generate_weekly_cards=False)
            plan_id = created["plan"]["id"]
            client.patch(
                f"/api/v1/profiles/alice/habit-plans/{plan_id}",
                json={"status": "completed"},
            )
            backward = client.patch(
                f"/api/v1/profiles/alice/habit-plans/{plan_id}",
                json={"status": "active"},
            )
            unknown = client.patch(
                f"/api/v1/profiles/alice/habit-plans/{plan_id}",
                json={"status": "paused"},
            )

        self.assertEqual(backward.status_code, 422)
        self.assertEqual(
            backward.json()["code"], "invalid_plan_status_transition"
        )
        self.assertEqual(unknown.status_code, 422)
        self.assertEqual(unknown.json()["code"], "invalid_plan_status")

    def test_patch_rejects_weekly_tasks_mismatch_and_blank_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            created = self._create_plan(client, generate_weekly_cards=False)
            plan_id = created["plan"]["id"]
            bad_weeks = client.patch(
                f"/api/v1/profiles/alice/habit-plans/{plan_id}",
                json={"weekly_tasks": [{"week": 1, "tasks": ["x"]}]},
            )
            blank_title = client.patch(
                f"/api/v1/profiles/alice/habit-plans/{plan_id}",
                json={"title": " "},
            )

        self.assertEqual(bad_weeks.status_code, 422)
        self.assertEqual(bad_weeks.json()["code"], "invalid_weekly_tasks")
        self.assertEqual(blank_title.status_code, 422)

    def test_patch_unknown_plan_is_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            response = client.patch(
                "/api/v1/profiles/alice/habit-plans/hp_ghost",
                json={"status": "archived"},
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "habit_plan_not_found")

    def test_no_op_patch_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            created = self._create_plan(client, generate_weekly_cards=False)
            plan_id = created["plan"]["id"]
            before = (pdir / "activity-log.yaml").read_text(
                encoding="utf-8"
            )
            response = client.patch(
                f"/api/v1/profiles/alice/habit-plans/{plan_id}", json={}
            )
            after = (pdir / "activity-log.yaml").read_text(
                encoding="utf-8"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(before, after)


class TestHabitPlanCheckins(HabitPlanTestBase):
    """POST /checkins with a plan binding."""

    def _create_plan(self, client: TestClient) -> str:
        payload = super()._create_plan(client, generate_weekly_cards=False)
        return str(payload["plan"]["id"])

    def test_checkin_with_plan_writes_plan_id_and_week_number(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            plan_id = self._create_plan(client)
            created = client.post(
                "/api/v1/profiles/alice/checkins",
                json={
                    "habit": "exercise",
                    "plan_id": plan_id,
                    "date": "2026-10-03",
                },
            )
            disk = _read_activity_log(pdir)

        self.assertEqual(created.status_code, 201, created.text)
        checkin = created.json()["checkin"]
        self.assertEqual(checkin["plan_id"], plan_id)
        self.assertEqual(checkin["week_number"], 2)
        stored = disk["checkins"][-1]
        self.assertEqual(stored["plan_id"], plan_id)
        self.assertEqual(stored["week_number"], 2)

    def test_checkin_plan_validation_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            plan_id = self._create_plan(client)
            unknown = client.post(
                "/api/v1/profiles/alice/checkins",
                json={"habit": "exercise", "plan_id": "hp_ghost"},
            )
            mismatch = client.post(
                "/api/v1/profiles/alice/checkins",
                json={
                    "habit": "reading",
                    "plan_id": plan_id,
                    "date": "2026-09-26",
                },
            )
            outside = client.post(
                "/api/v1/profiles/alice/checkins",
                json={
                    "habit": "exercise",
                    "plan_id": plan_id,
                    "date": "2026-12-01",
                },
            )
            client.patch(
                f"/api/v1/profiles/alice/habit-plans/{plan_id}",
                json={"status": "completed"},
            )
            inactive = client.post(
                "/api/v1/profiles/alice/checkins",
                json={
                    "habit": "exercise",
                    "plan_id": plan_id,
                    "date": "2026-09-26",
                },
            )

        self.assertEqual(unknown.status_code, 422)
        self.assertEqual(unknown.json()["code"], "habit_plan_not_found")
        self.assertEqual(mismatch.status_code, 422)
        self.assertEqual(
            mismatch.json()["code"], "habit_plan_habit_mismatch"
        )
        self.assertEqual(outside.status_code, 422)
        self.assertEqual(
            outside.json()["code"], "checkin_outside_plan_range"
        )
        self.assertEqual(inactive.status_code, 422)
        self.assertEqual(inactive.json()["code"], "habit_plan_not_active")

    def test_checkin_without_plan_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            created = client.post(
                "/api/v1/profiles/alice/checkins",
                json={"habit": "exercise", "date": "2026-09-26"},
            )
            disk = _read_activity_log(pdir)

        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()["checkin"]["plan_id"], "")
        self.assertNotIn("plan_id", disk["checkins"][-1])


class TestHabitPlanEtagDiscipline(HabitPlanTestBase):
    """If-Match/412 on habit-plan mutations."""

    def test_create_and_patch_with_stale_etag_return_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            create_stale = client.post(
                "/api/v1/profiles/alice/habit-plans",
                json=dict(PLAN_BODY, generate_weekly_cards=False),
                headers={"If-Match": 'W/"bogus"'},
            )
            created = self._create_plan(client, generate_weekly_cards=False)
            plan_id = created["plan"]["id"]
            patch_stale = client.patch(
                f"/api/v1/profiles/alice/habit-plans/{plan_id}",
                json={"status": "completed"},
                headers={"If-Match": 'W/"bogus"'},
            )

        for response in (create_stale, patch_stale):
            self.assertEqual(response.status_code, 412)
            self.assertEqual(response.json()["code"], "etag_mismatch")
            self.assertTrue(response.headers.get("etag"))

    def test_mutation_with_fresh_etag_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            listing = client.get("/api/v1/profiles/alice/habit-plans")
            etag = listing.headers["etag"]
            created = client.post(
                "/api/v1/profiles/alice/habit-plans",
                json=dict(PLAN_BODY, generate_weekly_cards=False),
                headers={"If-Match": etag},
            )
            plan_id = created.json()["plan"]["id"]
            patched = client.patch(
                f"/api/v1/profiles/alice/habit-plans/{plan_id}",
                json={"status": "archived"},
                headers={"If-Match": created.headers["etag"]},
            )

        self.assertEqual(created.status_code, 201)
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.json()["plan"]["status"], "archived")


if __name__ == "__main__":
    unittest.main()
