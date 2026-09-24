"""Tests for the habit lifecycle endpoints (archive / confirmed delete).

Covers POST /profiles/{name}/habits/{habit_id}/archive (archive + restore,
no-op discipline, projects-board exclusion by default with the
``include_archived`` opt-in, 404/412/401) and DELETE
/profiles/{name}/habits/{habit_id} (typed-title confirmation, check-in
purge count, opt-in ``habit.deleted`` chronicle entry, 404/412). All
profiles are built under tmp dirs; real profiles/ is never touched.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.web_api import app, create_app

PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-habit-lifecycle-test-secret"

ACTIVITY_LOG_FIXTURE = {
    "profile": "alice",
    "habits": [
        {"id": "exercise", "title": "Exercise", "kind": "health",
         "cadence": "daily"},
        {"id": "reading", "title": "Reading", "kind": "learning",
         "cadence": "daily"},
    ],
    "checkins": [
        {"id": "act_20260920_exercise", "date": "2026-09-20",
         "habit_id": "exercise", "habits": ["exercise"], "summary": "run"},
        {"id": "act_20260921_exercise", "date": "2026-09-21",
         "habit_id": "exercise", "habits": ["exercise"], "summary": "swim"},
        {"id": "act_20260921_reading", "date": "2026-09-21",
         "habit_id": "reading", "habits": ["reading"], "summary": "paper"},
    ],
}


def _write_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "activity-log.yaml").write_text(
        yaml.safe_dump(dict(ACTIVITY_LOG_FIXTURE, profile=name),
                       allow_unicode=True),
        encoding="utf-8",
    )
    return profile


def _read_activity_log(pdir: Path) -> dict:
    return yaml.safe_load(
        (pdir / "activity-log.yaml").read_text(encoding="utf-8")
    )


def _read_chronicle(pdir: Path) -> list[dict]:
    path = pdir / "chronicle.yaml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(raw.get("entries") or [])


class HabitLifecycleTestBase(unittest.TestCase):
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

    def _board_habits(self, client: TestClient, **params: object) -> list[dict]:
        response = client.get(
            "/api/v1/profiles/alice/projects-board", params=params
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["habits"]


class TestHabitArchive(HabitLifecycleTestBase):
    """POST /habits/{habit_id}/archive — reversible catalog toggle."""

    def test_archive_sets_flag_and_excludes_from_board(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            self.assertEqual(
                {h["id"] for h in self._board_habits(client)},
                {"exercise", "reading"},
            )
            response = client.post(
                "/api/v1/profiles/alice/habits/exercise/archive",
                json={"archived": True},
            )
            board_habits = self._board_habits(client)
            board_with_archived = self._board_habits(
                client, include_archived=True
            )
            disk = _read_activity_log(pdir)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["habit_id"], "exercise")
        self.assertTrue(payload["archived"])
        self.assertTrue(payload["changed"])
        self.assertTrue(response.headers["ETag"].startswith('W/"'))
        # YAML round-trip: the habit entry gains archived: true.
        habit = next(h for h in disk["habits"] if h["id"] == "exercise")
        self.assertIs(habit["archived"], True)
        # History is kept: all check-ins survive an archive.
        self.assertEqual(len(disk["checkins"]), 3)
        # Excluded from the board by default; opt-in shows it flagged.
        self.assertEqual({h["id"] for h in board_habits}, {"reading"})
        self.assertEqual(
            {h["id"] for h in board_with_archived}, {"exercise", "reading"}
        )
        archived_row = next(
            h for h in board_with_archived if h["id"] == "exercise"
        )
        self.assertTrue(archived_row["archived"])
        self.assertEqual(archived_row["total_checkins"], 2)

    def test_unarchive_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            client.post(
                "/api/v1/profiles/alice/habits/reading/archive",
                json={"archived": True},
            )
            response = client.post(
                "/api/v1/profiles/alice/habits/reading/archive",
                json={"archived": False},
            )
            board_habits = self._board_habits(client)
            disk = _read_activity_log(pdir)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["changed"])
        self.assertFalse(response.json()["archived"])
        habit = next(h for h in disk["habits"] if h["id"] == "reading")
        self.assertNotIn("archived", habit)
        self.assertEqual(
            {h["id"] for h in board_habits}, {"exercise", "reading"}
        )

    def test_noop_archive_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            etag_before = client.get(
                "/api/v1/profiles/alice/projects-board"
            ).headers["ETag"]
            response = client.post(
                "/api/v1/profiles/alice/habits/exercise/archive",
                json={"archived": False},
            )
            etag_after = client.get(
                "/api/v1/profiles/alice/projects-board"
            ).headers["ETag"]
            disk = _read_activity_log(pdir)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["changed"])
        self.assertEqual(etag_before, etag_after)
        habit = next(h for h in disk["habits"] if h["id"] == "exercise")
        self.assertNotIn("archived", habit)

    def test_unknown_habit_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/habits/nope/archive",
                json={"archived": True},
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "habit_not_found")

    def test_stale_if_match_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/habits/exercise/archive",
                json={"archived": True},
                headers={"If-Match": 'W/"stale"'},
            )
        self.assertEqual(response.status_code, 412)
        self.assertEqual(response.json()["code"], "etag_mismatch")
        self.assertTrue(response.headers["ETag"].startswith('W/"'))

    def test_archive_requires_auth_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            users_file = base / "users.yaml"
            stored = auth_core.hash_password(
                PASSWORD, iterations=100_000, salt=b"0123456789abcdef"
            )
            users_file.write_text(
                yaml.safe_dump(
                    {
                        "users": {
                            "wang": {
                                "display_name": "Wang",
                                "password_hash": stored,
                                "role": "member",
                                "profile": "alice",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            env = {
                "NBLANE_AUTH_FILE": str(users_file),
                "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
            }
            for target in (
                "nblane.core.profile_io.PROFILES_DIR",
                "nblane.core.io.PROFILES_DIR",
            ):
                patcher = patch(target, root)
                self.addCleanup(patcher.stop)
                patcher.start()
            with patch.dict(os.environ, env):
                    client = TestClient(create_app())
                    archived = client.post(
                        "/api/v1/profiles/alice/habits/exercise/archive",
                        json={"archived": True},
                    )
                    deleted = client.request(
                        "DELETE",
                        "/api/v1/profiles/alice/habits/exercise",
                        json={"confirm_title": "Exercise"},
                    )
        self.assertEqual(archived.status_code, 401)
        self.assertEqual(deleted.status_code, 401)


class TestHabitDelete(HabitLifecycleTestBase):
    """DELETE /habits/{habit_id} — typed-title confirmed purge."""

    def test_delete_purges_habit_and_checkins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            response = client.request(
                "DELETE",
                "/api/v1/profiles/alice/habits/exercise",
                json={"confirm_title": "Exercise"},
            )
            disk = _read_activity_log(pdir)
            board_habits = self._board_habits(client)
            chronicle = _read_chronicle(pdir)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["deleted_id"], "exercise")
        self.assertEqual(payload["checkins_removed"], 2)
        self.assertTrue(response.headers["ETag"].startswith('W/"'))
        # The habit entry is gone; other habits and their rows survive.
        self.assertEqual([h["id"] for h in disk["habits"]], ["reading"])
        self.assertEqual(len(disk["checkins"]), 1)
        self.assertEqual(disk["checkins"][0]["habit_id"], "reading")
        self.assertEqual({h["id"] for h in board_habits}, {"reading"})
        # record_chronicle defaults to false: no narrative entry.
        self.assertEqual(chronicle, [])

    def test_confirm_title_mismatch_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            for confirm in ("exercise", "Exercise ", "", "Exercis"):
                response = client.request(
                    "DELETE",
                    "/api/v1/profiles/alice/habits/exercise",
                    json={"confirm_title": confirm},
                )
                self.assertEqual(response.status_code, 422, confirm)
                self.assertEqual(
                    response.json()["code"], "habit_delete_confirm_mismatch"
                )
            disk = _read_activity_log(pdir)
        # Nothing written across all mismatches.
        self.assertEqual(len(disk["habits"]), 2)
        self.assertEqual(len(disk["checkins"]), 3)

    def test_record_chronicle_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            pdir = _write_profile(root)
            client = self._client(root)
            response = client.request(
                "DELETE",
                "/api/v1/profiles/alice/habits/reading",
                json={"confirm_title": "Reading", "record_chronicle": True},
            )
            chronicle = _read_chronicle(pdir)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checkins_removed"], 1)
        self.assertEqual(len(chronicle), 1)
        entry = chronicle[0]
        self.assertEqual(entry["kind"], "habit.deleted")
        self.assertEqual(entry["ref"], "reading")
        self.assertEqual(entry["note"], "Reading")
        self.assertTrue(entry["date"])

    def test_unknown_habit_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            response = client.request(
                "DELETE",
                "/api/v1/profiles/alice/habits/nope",
                json={"confirm_title": "nope"},
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "habit_not_found")

    def test_stale_if_match_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            client = self._client(root)
            response = client.request(
                "DELETE",
                "/api/v1/profiles/alice/habits/exercise",
                json={"confirm_title": "Exercise"},
                headers={"If-Match": 'W/"stale"'},
            )
        self.assertEqual(response.status_code, 412)
        self.assertEqual(response.json()["code"], "etag_mismatch")


if __name__ == "__main__":
    unittest.main()
