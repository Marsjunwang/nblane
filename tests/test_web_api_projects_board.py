"""Tests for the Phase 2 Projects Board slice (unified /projects page).

Covers the aggregated GET (goal grouping, per-column tasks with someday as
a badge list, Done counts including kanban-archive.md, milestone progress,
the unassigned lane, habit week dots/streak/totals, ETag header), the
kanban card schedule mutation (planned_start/planned_end set/clear,
validation, If-Match 412), and the check-in append mutation (habit or
project ref, default date, validation, If-Match 412). All profiles are
built under tmp_path; real profiles/ is never touched.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.core import plan_templates
from nblane.core.activity_log import load as load_activity_log
from nblane.core.kanban_io import parse_kanban
from nblane.core.paths import REPO_ROOT
from nblane.core.project_board import load_project_board
from nblane.web_api import app, create_app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"
PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-projects-board-test-secret"

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
FIVE_DAYS_AGO = TODAY - timedelta(days=5)
TEN_DAYS_AGO = TODAY - timedelta(days=10)

KANBAN_FIXTURE = """# alice · Kanban

## Doing

- [ ] Unassigned doing task
  - id: kb_doing_free
  - started_on: 2026-09-20

---

## Done

- [x] Shipped the demo
  - id: kb_done_p1
  - project_id: project:robot-arm
  - completed_on: 2026-09-18

---

## Queue

- [ ] Queued arm work
  - id: kb_queue_p1
  - project_id: project:robot-arm
  - started_on: 2026-09-01

---

## Someday / Maybe

- Maybe later arm idea
  - id: kb_someday_p1
  - project_id: project:robot-arm
- Unassigned someday idea
  - id: kb_someday_free

---
"""

ARCHIVE_FIXTURE = """# alice · Kanban archive

> Tasks moved here from kanban.md (Done column).

---

## Archived · 2026-09-01

- [x] Archived arm task one
  - id: kb_arch_p1_a
  - project_id: project:robot-arm
  - completed_on: 2026-08-20
- [x] Archived arm task two
  - id: kb_arch_p1_b
  - project_id: project:robot-arm
  - completed_on: 2026-08-25
- [x] Archived old task
  - id: kb_arch_old
  - project_id: project:old
  - completed_on: 2026-05-01
"""

PROJECT_BOARD_FIXTURE = {
    "schema_version": "1.0",
    "profile": "alice",
    "updated": "2026-09-19",
    "project_cases": [
        {
            "id": "project:robot-arm",
            "title": "Robot Arm",
            "status": "active",
            "kind": "work",
            "summary": "Build the arm",
            "time_range": "2026-09-01/2026-12-31",
            "goal_refs": ["goal-1"],
            "milestones": [
                {
                    "id": "milestone:mvp",
                    "title": "MVP",
                    "status": "planned",
                    "date": "2026-10-01",
                    "task_refs": ["kb_done_p1", "kb_arch_p1_a", "kb_queue_p1"],
                }
            ],
        },
        {
            "id": "project:old",
            "title": "Old Project",
            "status": "archived",
        },
        {
            "id": "project:exercise",
            "title": "Exercise",
            "status": "active",
            "goal_refs": ["goal-2"],
        },
    ],
}

GOALS_FIXTURE = {
    "schema_version": "1.0",
    "profile": "alice",
    "updated": "2026-09-19",
    "current_goal_id": "goal-1",
    "goals": [
        {
            "id": "goal-1",
            "title": "Ship VLA demo",
            "status": "active",
            "target": "2026-12-31",
            "summary": "Demo first",
        },
        {"id": "goal-2", "title": "Stay healthy", "status": "active"},
        {"id": "goal-3", "title": "Empty goal", "status": "planned"},
    ],
}

ACTIVITY_LOG_FIXTURE = {
    "profile": "alice",
    "habits": [
        {"id": "exercise", "title": "Exercise", "kind": "health",
         "cadence": "daily"},
        {"id": "reading", "title": "Reading", "kind": "learning",
         "cadence": "daily"},
    ],
    "checkins": [
        {"date": TODAY.isoformat(), "habit_id": "exercise",
         "habits": ["exercise"], "summary": "run"},
        {"date": YESTERDAY.isoformat(), "habit_id": "exercise",
         "habits": ["exercise"], "summary": "run"},
        # Same-day duplicate: totals count distinct days, not rows.
        {"date": YESTERDAY.isoformat(), "habit_id": "exercise",
         "habits": ["exercise"], "summary": "swim"},
        {"date": FIVE_DAYS_AGO.isoformat(), "habit_id": "exercise",
         "habits": ["exercise"], "summary": "run"},
        {"date": TEN_DAYS_AGO.isoformat(), "habit_id": "reading",
         "habits": ["reading"], "summary": "paper"},
    ],
}


def _template_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            text = text.replace("{YYYY-MM-DD}", "2026-09-19")
            file_path.write_text(text, encoding="utf-8")
    (profile / "kanban.md").write_text(KANBAN_FIXTURE, encoding="utf-8")
    (profile / "kanban-archive.md").write_text(ARCHIVE_FIXTURE, encoding="utf-8")
    (profile / "project-board.yaml").write_text(
        yaml.safe_dump(
            dict(PROJECT_BOARD_FIXTURE, profile=name), allow_unicode=True
        ),
        encoding="utf-8",
    )
    (profile / "goals.yaml").write_text(
        yaml.safe_dump(dict(GOALS_FIXTURE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "activity-log.yaml").write_text(
        yaml.safe_dump(
            dict(ACTIVITY_LOG_FIXTURE, profile=name), allow_unicode=True
        ),
        encoding="utf-8",
    )
    return profile


def _write_users_file(path: Path) -> Path:
    stored = auth_core.hash_password(
        PASSWORD,
        iterations=100_000,
        salt=b"0123456789abcdef",
    )
    path.write_text(
        yaml.safe_dump(
            {
                "users": {
                    "wang": {
                        "display_name": "Wang",
                        "password_hash": stored,
                        "role": "member",
                        "profile": "wang",
                        "teams": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return path


class ProjectsBoardTestBase(unittest.TestCase):
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
        patcher = patch("nblane.core.profile_io.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)


class TestProjectsBoardGet(ProjectsBoardTestBase):
    """GET /projects-board aggregation shape."""

    def _get(self, client: TestClient) -> dict:
        response = client.get("/api/v1/profiles/alice/projects-board")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["ETag"].startswith('W/"'))
        return response.json()

    def test_aggregation_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            payload = self._get(self._client(root))
        self.assertEqual(payload["profile"], "alice")
        self.assertEqual(payload["today"], TODAY.isoformat())
        self.assertIn("north_star", payload)

        goals = {goal["id"]: goal for goal in payload["goals"]}
        self.assertEqual(sorted(goals), ["goal-1", "goal-2", "goal-3"])
        self.assertEqual(goals["goal-1"]["target"], "2026-12-31")
        self.assertEqual(
            [p["id"] for p in goals["goal-1"]["projects"]],
            ["project:robot-arm"],
        )
        self.assertEqual(
            [p["id"] for p in goals["goal-2"]["projects"]],
            ["project:exercise"],
        )
        self.assertEqual(goals["goal-3"]["projects"], [])

        # goal-less project lands in ungrouped_projects.
        self.assertEqual(
            [p["id"] for p in payload["ungrouped_projects"]], ["project:old"]
        )

        arm = goals["goal-1"]["projects"][0]
        self.assertEqual(arm["time_range"], "2026-09-01/2026-12-31")
        self.assertEqual([t["id"] for t in arm["queue"]], ["kb_queue_p1"])
        self.assertEqual(arm["doing"], [])
        # someday is a badge list, not a column.
        self.assertEqual([t["id"] for t in arm["someday"]], ["kb_someday_p1"])
        self.assertEqual(arm["someday"][0]["column"], "someday")
        # Done count = live Done (1) + archive (2).
        self.assertEqual(arm["done_count"], 3)
        self.assertEqual(arm["archived_done_count"], 2)
        self.assertEqual(
            arm["column_counts"],
            {"queue": 1, "doing": 0, "someday": 1, "done": 3},
        )
        self.assertEqual(arm["last_activity"], "2026-09-18")
        # Milestone progress resolves refs against live Done AND the archive.
        milestone = arm["milestones"][0]
        self.assertEqual(milestone["status"], "planned")
        self.assertEqual(milestone["done_count"], 2)
        self.assertEqual(milestone["total_count"], 3)

        # Archived project keeps its archive-only Done count.
        old = payload["ungrouped_projects"][0]
        self.assertEqual(old["done_count"], 1)
        self.assertEqual(old["archived_done_count"], 1)

    def test_unassigned_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            payload = self._get(self._client(root))
        rows = {task["id"]: task for task in payload["unassigned_tasks"]}
        self.assertEqual(sorted(rows), ["kb_doing_free", "kb_someday_free"])
        self.assertEqual(rows["kb_doing_free"]["column"], "doing")
        self.assertEqual(rows["kb_someday_free"]["column"], "someday")
        stats = payload["stats"]
        self.assertEqual(stats["tasks_total"], 5)
        self.assertEqual(stats["tasks_unassigned"], 2)
        self.assertEqual(stats["projects_total"], 3)

    def test_habit_aggregation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            payload = self._get(self._client(root))
        habits = {habit["id"]: habit for habit in payload["habits"]}
        self.assertEqual(sorted(habits), ["exercise", "reading"])

        exercise = habits["exercise"]
        week = exercise["week"]
        self.assertEqual(len(week), 7)
        week_start = TODAY - timedelta(days=TODAY.weekday())
        self.assertEqual(week[0]["date"], week_start.isoformat())
        by_date = {day["date"]: day for day in week}
        self.assertTrue(by_date[TODAY.isoformat()]["done"])
        self.assertTrue(by_date[YESTERDAY.isoformat()]["done"])
        if FIVE_DAYS_AGO >= week_start:
            self.assertTrue(by_date[FIVE_DAYS_AGO.isoformat()]["done"])
        for day in week:
            self.assertEqual(day["future"], day["date"] > TODAY.isoformat())
        # Streak ends today: today + yesterday are consecutive -> 2.
        self.assertEqual(exercise["streak"], 2)
        # Totals count distinct checked days (3), not rows (4).
        self.assertEqual(exercise["total_checkins"], 3)
        self.assertEqual(exercise["last_checkin"], TODAY.isoformat())
        # habit<->project name link (habit id == project title, normalized).
        self.assertEqual(exercise["project_id"], "project:exercise")

        # Broken streak: last checkin ten days ago -> 0 (build_data rule).
        reading = habits["reading"]
        self.assertEqual(reading["streak"], 0)
        self.assertEqual(reading["total_checkins"], 1)
        self.assertEqual(reading["last_checkin"], TEN_DAYS_AGO.isoformat())
        self.assertEqual(reading["project_id"], "")

        goals = {goal["id"]: goal for goal in payload["goals"]}
        exercise_project = goals["goal-2"]["projects"][0]
        self.assertEqual(exercise_project["habit_id"], "exercise")
        self.assertEqual(
            exercise_project["last_activity"], TODAY.isoformat()
        )

    def test_etag_changes_with_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            first = client.get("/api/v1/profiles/alice/projects-board")
            second = client.get("/api/v1/profiles/alice/projects-board")
            self.assertEqual(first.headers["ETag"], second.headers["ETag"])
            with (profile / "kanban-archive.md").open("a", encoding="utf-8") as fh:
                fh.write("\n")
            third = client.get("/api/v1/profiles/alice/projects-board")
        self.assertNotEqual(first.headers["ETag"], third.headers["ETag"])

    def test_missing_optional_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            (profile / "kanban-archive.md").unlink()
            (profile / "activity-log.yaml").unlink()
            payload = self._get(self._client(root))
        arm = payload["goals"][0]["projects"][0]
        self.assertEqual(arm["done_count"], 1)
        self.assertEqual(arm["archived_done_count"], 0)
        self.assertEqual(payload["habits"], [])

    def test_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            response = self._client(root).get(
                "/api/v1/profiles/nobody/projects-board"
            )
        self.assertEqual(response.status_code, 404)


class TestKanbanCardSchedule(ProjectsBoardTestBase):
    """POST /kanban/cards/{card_ref}/schedule: planned date range."""

    def test_set_and_clear_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            etag = client.get("/api/v1/profiles/alice/kanban").headers["ETag"]
            response = client.post(
                "/api/v1/profiles/alice/kanban/cards/Queued arm work/schedule",
                json={
                    "planned_start": "2026-10-01",
                    "planned_end": "2026-10-15",
                },
                headers={"If-Match": etag},
            )
            self.assertEqual(response.status_code, 200)
            card = response.json()["card"]
            self.assertEqual(card["planned_start"], "2026-10-01")
            self.assertEqual(card["planned_end"], "2026-10-15")
            # Persisted to kanban.md and parsed back.
            stored = parse_kanban(profile)["Queue"][0]
            self.assertEqual(stored.planned_start, "2026-10-01")
            self.assertEqual(stored.planned_end, "2026-10-15")
            text = (profile / "kanban.md").read_text(encoding="utf-8")
            self.assertIn("- planned_start: 2026-10-01", text)
            self.assertIn("- planned_end: 2026-10-15", text)
            # Omitted field keeps its value; "" clears.
            cleared = client.post(
                "/api/v1/profiles/alice/kanban/cards/Queued arm work/schedule",
                json={"planned_start": ""},
            )
            self.assertEqual(cleared.status_code, 200)
            card = cleared.json()["card"]
            self.assertIsNone(card["planned_start"])
            self.assertEqual(card["planned_end"], "2026-10-15")
            stored = parse_kanban(profile)["Queue"][0]
            self.assertIsNone(stored.planned_start)
            self.assertEqual(stored.planned_end, "2026-10-15")

    def test_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            url = "/api/v1/profiles/alice/kanban/cards/Queued arm work/schedule"
            bad_date = client.post(url, json={"planned_start": "next week"})
            self.assertEqual(bad_date.status_code, 422)
            self.assertEqual(bad_date.json()["code"], "invalid_planned_date")
            inverted = client.post(
                url,
                json={
                    "planned_start": "2026-10-15",
                    "planned_end": "2026-10-01",
                },
            )
            self.assertEqual(inverted.status_code, 422)
            self.assertEqual(inverted.json()["code"], "invalid_planned_range")
            empty = client.post(url, json={})
            self.assertEqual(empty.status_code, 422)
            missing = client.post(
                "/api/v1/profiles/alice/kanban/cards/no-such-card/schedule",
                json={"planned_start": "2026-10-01"},
            )
            self.assertEqual(missing.status_code, 404)

    def test_if_match_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            etag = client.get("/api/v1/profiles/alice/kanban").headers["ETag"]
            url = "/api/v1/profiles/alice/kanban/cards/Queued arm work/schedule"
            first = client.post(url, json={"planned_start": "2026-10-01"})
            self.assertEqual(first.status_code, 200)
            stale = client.post(
                url,
                json={"planned_end": "2026-10-15"},
                headers={"If-Match": etag},
            )
            self.assertEqual(stale.status_code, 412)
            self.assertEqual(stale.json()["code"], "etag_mismatch")
            self.assertTrue(stale.headers["ETag"].startswith('W/"'))

    def test_create_card_with_planned_dates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            created = client.post(
                "/api/v1/profiles/alice/kanban/cards",
                json={
                    "title": "Scheduled task",
                    "planned_start": "2026-10-01",
                    "planned_end": "2026-10-15",
                },
            )
            self.assertEqual(created.status_code, 201)
            card = created.json()["card"]
            self.assertEqual(card["planned_start"], "2026-10-01")
            stored = parse_kanban(profile)["Queue"][-1]
            self.assertEqual(stored.planned_start, "2026-10-01")
            self.assertEqual(stored.planned_end, "2026-10-15")
            bad = client.post(
                "/api/v1/profiles/alice/kanban/cards",
                json={"title": "Bad", "planned_start": "soon"},
            )
            self.assertEqual(bad.status_code, 422)


class TestCheckins(ProjectsBoardTestBase):
    """POST /checkins: append one habit check-in to the activity log."""

    def test_append_defaults_and_etag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            etag = client.get(
                "/api/v1/profiles/alice/projects-board"
            ).headers["ETag"]
            response = client.post(
                "/api/v1/profiles/alice/checkins",
                json={"habit": "exercise", "note": "morning run"},
            )
            self.assertEqual(response.status_code, 201)
            checkin = response.json()["checkin"]
            self.assertEqual(checkin["habit_id"], "exercise")
            self.assertEqual(checkin["habits"], ["exercise"])
            self.assertEqual(checkin["date"], TODAY.isoformat())
            self.assertEqual(checkin["notes"], "morning run")
            self.assertTrue(checkin["id"])
            self.assertNotEqual(response.headers["ETag"], etag)
            raw = yaml.safe_load(
                (profile / "activity-log.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(len(raw["checkins"]), 6)
            # The board aggregation sees the new check-in.
            board = client.get("/api/v1/profiles/alice/projects-board").json()
            exercise = next(h for h in board["habits"] if h["id"] == "exercise")
            self.assertEqual(exercise["total_checkins"], 3)
            self.assertEqual(exercise["streak"], 2)

    def test_habit_title_and_explicit_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/checkins",
                json={
                    "habit": "Reading",
                    "date": YESTERDAY.isoformat(),
                    "summary": "paper",
                    "count": 2,
                },
            )
            self.assertEqual(response.status_code, 201)
            checkin = response.json()["checkin"]
            self.assertEqual(checkin["habit_id"], "reading")
            self.assertEqual(checkin["date"], YESTERDAY.isoformat())
            self.assertEqual(checkin["count"], 2)

    def test_project_ref_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            linked = client.post(
                "/api/v1/profiles/alice/checkins",
                json={"project_id": "project:exercise"},
            )
            self.assertEqual(linked.status_code, 201)
            self.assertEqual(linked.json()["checkin"]["habit_id"], "exercise")
            unlinked = client.post(
                "/api/v1/profiles/alice/checkins",
                json={"project_id": "project:robot-arm"},
            )
            self.assertEqual(unlinked.status_code, 422)
            self.assertEqual(
                unlinked.json()["code"], "checkin_project_unlinked"
            )
            unknown = client.post(
                "/api/v1/profiles/alice/checkins",
                json={"project_id": "project:nope"},
            )
            self.assertEqual(unknown.status_code, 422)
            self.assertEqual(
                unknown.json()["code"], "checkin_project_not_found"
            )

    def test_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            missing = client.post("/api/v1/profiles/alice/checkins", json={})
            self.assertEqual(missing.status_code, 422)
            self.assertEqual(missing.json()["code"], "checkin_habit_required")
            unknown = client.post(
                "/api/v1/profiles/alice/checkins", json={"habit": "nope"}
            )
            self.assertEqual(unknown.status_code, 422)
            bad_date = client.post(
                "/api/v1/profiles/alice/checkins",
                json={"habit": "exercise", "date": "tomorrow"},
            )
            self.assertEqual(bad_date.status_code, 422)
            self.assertEqual(bad_date.json()["code"], "invalid_checkin_date")
            zero = client.post(
                "/api/v1/profiles/alice/checkins",
                json={"habit": "exercise", "count": 0},
            )
            self.assertEqual(zero.status_code, 422)

    def test_if_match_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            etag = client.get(
                "/api/v1/profiles/alice/projects-board"
            ).headers["ETag"]
            first = client.post(
                "/api/v1/profiles/alice/checkins", json={"habit": "exercise"}
            )
            self.assertEqual(first.status_code, 201)
            stale = client.post(
                "/api/v1/profiles/alice/checkins",
                json={"habit": "exercise"},
                headers={"If-Match": etag},
            )
            self.assertEqual(stale.status_code, 412)
            self.assertEqual(stale.json()["code"], "etag_mismatch")
            self.assertTrue(stale.headers["ETag"].startswith('W/"'))


class TestProjectsBoardScope(ProjectsBoardTestBase):
    """401/403 enforcement under auth-on."""

    def _auth_client(self, root: Path) -> TestClient:
        users_file = _write_users_file(root / "users.yaml")
        env = {
            "NBLANE_AUTH_FILE": str(users_file),
            "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
        }
        patcher = patch.dict(os.environ, env)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
            "nblane.core.project_board.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(create_app())

    def test_unauthenticated_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._auth_client(root)
            listing = client.get("/api/v1/profiles/alice/projects-board")
            checkin = client.post(
                "/api/v1/profiles/alice/checkins", json={"habit": "exercise"}
            )
            schedule = client.post(
                "/api/v1/profiles/alice/kanban/cards/Queued arm work/schedule",
                json={"planned_start": "2026-10-01"},
            )
            patch = client.patch(
                "/api/v1/profiles/alice/kanban/cards/Queued arm work",
                json={"context": "x"},
            )
            templates = client.get("/api/v1/profiles/alice/plan-templates")
            instantiate = client.post(
                "/api/v1/profiles/alice/plan-templates/instantiate",
                json={"template_id": "plan:learning-21"},
            )
        self.assertEqual(listing.status_code, 401)
        self.assertEqual(checkin.status_code, 401)
        self.assertEqual(schedule.status_code, 401)
        self.assertEqual(patch.status_code, 401)
        self.assertEqual(templates.status_code, 401)
        self.assertEqual(instantiate.status_code, 401)

    def test_member_forbidden_from_other_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, "alice")
            _template_profile(root, "wang")
            client = self._auth_client(root)
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            forbidden = client.get("/api/v1/profiles/alice/projects-board")
            allowed = client.get("/api/v1/profiles/wang/projects-board")
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.json()["code"], "profile_forbidden")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["profile"], "wang")


class TestExplicitHabitLink(ProjectsBoardTestBase):
    """Case habit_id field: explicit habit<->project link + case save."""

    def _set_case_habit(self, profile: Path, case_id: str, habit_id: str) -> None:
        board_path = profile / "project-board.yaml"
        raw = yaml.safe_load(board_path.read_text(encoding="utf-8"))
        for case in raw["project_cases"]:
            if case["id"] == case_id:
                case["habit_id"] = habit_id
        board_path.write_text(yaml.safe_dump(raw, allow_unicode=True),
                              encoding="utf-8")

    def test_explicit_link_overrides_heuristic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            # robot-arm's title does not match any habit; link it explicitly.
            self._set_case_habit(profile, "project:robot-arm", "reading")
            client = self._client(root)
            payload = client.get("/api/v1/profiles/alice/projects-board").json()
        goals = {goal["id"]: goal for goal in payload["goals"]}
        arm = goals["goal-1"]["projects"][0]
        self.assertEqual(arm["habit_id"], "reading")
        habits = {habit["id"]: habit for habit in payload["habits"]}
        self.assertEqual(habits["reading"]["project_id"], "project:robot-arm")
        # last_activity merges task dates (09-18) with the habit's last
        # check-in (10 days ago) — the max wins.
        self.assertEqual(arm["last_activity"], "2026-09-18")
        # The name-heuristic link (exercise <-> project:exercise) still works.
        self.assertEqual(habits["exercise"]["project_id"], "project:exercise")
        exercise_project = goals["goal-2"]["projects"][0]
        self.assertEqual(exercise_project["habit_id"], "exercise")

    def test_case_save_and_create_habit_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            etag = client.get(
                "/api/v1/profiles/alice/project-board"
            ).headers["ETag"]
            saved = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:old/save",
                json={"habit_id": "exercise"},
                headers={"If-Match": etag},
            )
            self.assertEqual(saved.status_code, 200)
            self.assertEqual(saved.json()["case"]["habit_id"], "exercise")
            case = load_project_board(profile).by_id()["project:old"]
            self.assertEqual(case.habit_id, "exercise")
            # Empty string clears the link.
            cleared = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:old/save",
                json={"habit_id": ""},
            )
            self.assertEqual(cleared.status_code, 200)
            self.assertEqual(cleared.json()["case"]["habit_id"], "")
            case = load_project_board(profile).by_id()["project:old"]
            self.assertEqual(case.habit_id, "")
            created = client.post(
                "/api/v1/profiles/alice/project-board/cases",
                json={"title": "Meditation", "habit_id": "reading"},
            )
            self.assertEqual(created.status_code, 201)
            self.assertEqual(created.json()["case"]["habit_id"], "reading")

    def test_checkin_project_ref_prefers_explicit_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            self._set_case_habit(profile, "project:robot-arm", "reading")
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/checkins",
                json={"project_id": "project:robot-arm"},
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["checkin"]["habit_id"], "reading")


class TestKanbanCardPatch(ProjectsBoardTestBase):
    """PATCH /kanban/cards/{card_ref}: field edits + lane assignment."""

    def test_assign_and_unassign_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            etag = client.get("/api/v1/profiles/alice/kanban").headers["ETag"]
            assigned = client.patch(
                "/api/v1/profiles/alice/kanban/cards/Unassigned someday idea",
                json={"project_id": "project:robot-arm"},
                headers={"If-Match": etag},
            )
            self.assertEqual(assigned.status_code, 200)
            card = assigned.json()["card"]
            self.assertEqual(card["project_id"], "project:robot-arm")
            # Persisted to kanban.md and synced into the board's task refs.
            stored = parse_kanban(profile)["Someday / Maybe"][1]
            self.assertEqual(stored.project_id, "project:robot-arm")
            board = load_project_board(profile).by_id()["project:robot-arm"]
            self.assertIn("kb_someday_free", board.task_refs)
            # Unassign with the empty string; the board ref is removed.
            unassigned = client.patch(
                "/api/v1/profiles/alice/kanban/cards/Unassigned someday idea",
                json={"project_id": ""},
            )
            self.assertEqual(unassigned.status_code, 200)
            self.assertEqual(unassigned.json()["card"]["project_id"], "")
            board = load_project_board(profile).by_id()["project:robot-arm"]
            self.assertNotIn("kb_someday_free", board.task_refs)

    def test_text_fields_and_tags_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.patch(
                "/api/v1/profiles/alice/kanban/cards/Queued arm work",
                json={
                    "title": "Queued arm work v2",
                    "context": "new context",
                    "why": "because",
                    "tags": ["robotics", "vla"],
                },
            )
            self.assertEqual(response.status_code, 200)
            card = response.json()["card"]
            self.assertEqual(card["title"], "Queued arm work v2")
            self.assertEqual(card["tags"], "robotics, vla")
            stored = parse_kanban(profile)["Queue"][0]
            self.assertEqual(stored.title, "Queued arm work v2")
            self.assertEqual(stored.context, "new context")
            self.assertEqual(stored.why, "because")
            self.assertEqual(stored.tags, "robotics, vla")
            # project_id untouched by a patch that omits it.
            self.assertEqual(stored.project_id, "project:robot-arm")

    def test_validation_and_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            url = "/api/v1/profiles/alice/kanban/cards/Queued arm work"
            blank_title = client.patch(url, json={"title": "  "})
            self.assertEqual(blank_title.status_code, 422)
            empty = client.patch(url, json={})
            self.assertEqual(empty.status_code, 422)
            self.assertEqual(empty.json()["code"], "invalid_kanban_patch")
            missing = client.patch(
                "/api/v1/profiles/alice/kanban/cards/no-such-card",
                json={"context": "x"},
            )
            self.assertEqual(missing.status_code, 404)
            etag = client.get("/api/v1/profiles/alice/kanban").headers["ETag"]
            first = client.patch(url, json={"context": "one"})
            self.assertEqual(first.status_code, 200)
            stale = client.patch(
                url, json={"context": "two"}, headers={"If-Match": etag}
            )
            self.assertEqual(stale.status_code, 412)
            self.assertEqual(stale.json()["code"], "etag_mismatch")


class TestPlanTemplates(ProjectsBoardTestBase):
    """Plan templates: builtin catalog, history, instantiate flow."""

    def test_builtin_catalog_and_empty_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/plan-templates")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["ETag"].startswith('W/"'))
        payload = response.json()
        ids = [template["id"] for template in payload["builtin"]]
        self.assertEqual(
            ids, ["plan:fat-loss-30", "plan:rehab-30", "plan:learning-21"]
        )
        learning = payload["builtin"][2]
        self.assertEqual(learning["duration_days"], 21)
        self.assertEqual(learning["habit"]["title"], "学习打卡")
        self.assertEqual(learning["habit"]["kind"], "learning")
        self.assertEqual(len(learning["milestones"]), 2)
        self.assertTrue(learning["builtin"])
        self.assertEqual(payload["history"], [])

    def test_instantiate_builtin_full_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            etag = client.get(
                "/api/v1/profiles/alice/plan-templates"
            ).headers["ETag"]
            response = client.post(
                "/api/v1/profiles/alice/plan-templates/instantiate",
                json={
                    "template_id": "plan:learning-21",
                    "title": "VLA 论文 21 天",
                    "start": "2026-10-01",
                    "goal_refs": ["goal-1"],
                },
                headers={"If-Match": etag},
            )
            self.assertEqual(response.status_code, 201)
            self.assertNotEqual(response.headers["ETag"], etag)
            payload = response.json()
            self.assertEqual(payload["template_id"], "plan:learning-21")
            self.assertEqual(payload["habit_id"], "学习打卡")
            self.assertTrue(payload["created_habit"])
            case = payload["case"]
            self.assertEqual(case["title"], "VLA 论文 21 天")
            self.assertEqual(case["kind"], "habit-plan")
            self.assertEqual(case["time_range"], "2026-10-01/2026-10-21")
            self.assertEqual(case["habit_id"], "学习打卡")
            self.assertEqual(case["goal_refs"], ["goal-1"])
            milestones = {m["title"]: m["date"] for m in case["milestones"]}
            self.assertEqual(
                milestones, {"第 1 周复盘": "2026-10-07", "21 天总结": "2026-10-21"}
            )
            # Habit persisted to the activity log; case to the board.
            log = load_activity_log(profile)
            self.assertIn("学习打卡", log.habit_index())
            board = load_project_board(profile)
            stored = board.by_id()[case["id"]]
            self.assertEqual(stored.kind, "habit-plan")
            self.assertEqual(stored.habit_id, "学习打卡")
            # The new plan renders as a habit lane on the projects board.
            board_payload = client.get(
                "/api/v1/profiles/alice/projects-board"
            ).json()
            lane = next(
                project
                for goal in board_payload["goals"]
                for project in goal["projects"]
                if project["id"] == case["id"]
            )
            self.assertEqual(lane["habit_id"], "学习打卡")
            habit_row = next(
                h for h in board_payload["habits"] if h["id"] == "学习打卡"
            )
            self.assertEqual(habit_row["project_id"], case["id"])
            self.assertEqual(len(habit_row["week"]), 7)
            # Usage remembered, most recent first.
            history = client.get(
                "/api/v1/profiles/alice/plan-templates"
            ).json()["history"]
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["template_id"], "plan:learning-21")
            self.assertEqual(history[0]["project_id"], case["id"])
            self.assertEqual(history[0]["habit_id"], "学习打卡")

    def test_instantiate_overrides_and_inline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            # habit_id override links to an existing habit (no creation).
            reused = client.post(
                "/api/v1/profiles/alice/plan-templates/instantiate",
                json={
                    "template_id": "plan:fat-loss-30",
                    "habit_id": "exercise",
                },
            )
            self.assertEqual(reused.status_code, 201)
            self.assertEqual(reused.json()["habit_id"], "exercise")
            self.assertFalse(reused.json()["created_habit"])
            self.assertEqual(
                reused.json()["case"]["habit_id"], "exercise"
            )
            # Inline template (no builtin id).
            inline = client.post(
                "/api/v1/profiles/alice/plan-templates/instantiate",
                json={
                    "template": {
                        "title": "自定义计划",
                        "duration_days": 14,
                        "habit": {"title": "冥想", "kind": "health"},
                        "milestones": [{"title": "半程", "offset_days": 6}],
                    },
                    "start": "2026-11-01",
                },
            )
            self.assertEqual(inline.status_code, 201)
            case = inline.json()["case"]
            self.assertEqual(case["kind"], "habit-plan")
            self.assertEqual(case["time_range"], "2026-11-01/2026-11-14")
            self.assertEqual(case["milestones"][0]["date"], "2026-11-07")
            self.assertEqual(inline.json()["habit_id"], "冥想")
            history = client.get(
                "/api/v1/profiles/alice/plan-templates"
            ).json()["history"]
            self.assertEqual(len(history), 2)
            self.assertEqual(
                history[0]["template_id"], f"inline:{case['id']}"
            )

    def test_history_dedup_most_recent_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            for template_id in ("plan:learning-21", "plan:rehab-30",
                                "plan:learning-21"):
                response = client.post(
                    "/api/v1/profiles/alice/plan-templates/instantiate",
                    json={"template_id": template_id},
                )
                self.assertEqual(response.status_code, 201)
            history = client.get(
                "/api/v1/profiles/alice/plan-templates"
            ).json()["history"]
        self.assertEqual(
            [row["template_id"] for row in history],
            ["plan:learning-21", "plan:rehab-30"],
        )

    def test_instantiate_validation_and_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            url = "/api/v1/profiles/alice/plan-templates/instantiate"
            missing = client.post(url, json={})
            self.assertEqual(missing.status_code, 422)
            self.assertEqual(missing.json()["code"], "plan_template_required")
            unknown = client.post(url, json={"template_id": "plan:nope"})
            self.assertEqual(unknown.status_code, 422)
            self.assertEqual(unknown.json()["code"], "unknown_plan_template")
            bad_start = client.post(
                url,
                json={"template_id": "plan:learning-21", "start": "soon"},
            )
            self.assertEqual(bad_start.status_code, 422)
            self.assertEqual(bad_start.json()["code"], "invalid_plan_start")
            etag = client.get(
                "/api/v1/profiles/alice/plan-templates"
            ).headers["ETag"]
            first = client.post(url, json={"template_id": "plan:rehab-30"})
            self.assertEqual(first.status_code, 201)
            stale = client.post(
                url,
                json={"template_id": "plan:fat-loss-30"},
                headers={"If-Match": etag},
            )
            self.assertEqual(stale.status_code, 412)
            self.assertEqual(stale.json()["code"], "etag_mismatch")
            self.assertTrue(stale.headers["ETag"].startswith('W/"'))


class TestPlanTemplatesCore(unittest.TestCase):
    """Core plan_templates helpers (no HTTP)."""

    def test_builtins_load_and_case_fields(self) -> None:
        templates = plan_templates.builtin_template_index()
        self.assertEqual(len(templates), 3)
        template = templates["plan:learning-21"]
        fields = plan_templates.plan_case_fields(
            template, start=date(2026, 10, 1)
        )
        self.assertEqual(fields["kind"], "habit-plan")
        self.assertEqual(fields["time_range"], "2026-10-01/2026-10-21")
        self.assertEqual(fields["title"], template.title)
        self.assertEqual(
            [m["date"] for m in fields["milestones"]],
            ["2026-10-07", "2026-10-21"],
        )

    def test_history_roundtrip_and_snapshot_conflict(self) -> None:
        from nblane.core import file_state

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            self.assertEqual(plan_templates.load_plan_history(profile), [])
            plan_templates.record_plan_usage(
                profile,
                {"template_id": "plan:learning-21", "title": "t",
                 "project_id": "p1", "habit_id": "h1"},
            )
            history = plan_templates.load_plan_history(profile)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["template_id"], "plan:learning-21")
            stale = file_state.snapshot_file(
                profile / plan_templates.PLAN_TEMPLATES_FILENAME
            )
            plan_templates.record_plan_usage(
                profile,
                {"template_id": "plan:rehab-30", "title": "t2"},
            )
            with self.assertRaises(file_state.FileConflictError):
                plan_templates.record_plan_usage(
                    profile,
                    {"template_id": "plan:fat-loss-30", "title": "t3"},
                    expected_snapshot=stale,
                )


if __name__ == "__main__":
    unittest.main()
