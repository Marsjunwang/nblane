"""Tests for the home-starmap editing backend slice.

Covers PATCH /north-star (surgical SKILL.md identity edit — the rest of the
file stays byte-identical; binary visibility with legacy ``discreet``
mapping; If-Match 412), goals CRUD (create/patch validation + 412), the
append-only chronicle (entries fire only on real changes; no-op writes log
nothing), GET /chronicle, and 401/404 coverage. All profiles are built under
tmp_path; real profiles/ is never touched.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.core.chronicle import CHRONICLE_FILENAME, load_chronicle
from nblane.core.goals import load_goal_book
from nblane.core.paths import REPO_ROOT
from nblane.web_api import app, create_app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"
PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-home-editing-test-secret"

SKILL_MD_FIXTURE = """# alice · nblane Profile

## Identity

- **Name**: alice
- **Domain**: Robotics
- **Journey**: Year 2 of 5
- **Current Role**: Research engineer
- **North Star**: Old north star text
- **North Star Brief**: Old brief
- **North Star Visibility**: discreet

---

## Skill Tree

<!-- BEGIN GENERATED:skill_tree -->
- [x] ROS 2
<!-- END GENERATED:skill_tree -->

---

## Growth Log

| Date | Event | Why it matters |
|------|-------|----------------|
| 2026-09 | Shipped demo | Proof |
"""

GOALS_FIXTURE = {
    "schema_version": "1.0",
    "profile": "alice",
    "updated": "2026-09-19",
    "current_goal_id": "goal-ship-vla-demo",
    "goals": [
        {
            "id": "goal-ship-vla-demo",
            "title": "Ship VLA demo",
            "status": "active",
            "target": "2026-12-31",
            "summary": "Demo first",
        },
        {"id": "goal-2", "title": "Stay healthy", "status": "paused"},
    ],
}


def _profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    shutil.copytree(TEMPLATE_DIR, profile)
    (profile / "SKILL.md").write_text(SKILL_MD_FIXTURE, encoding="utf-8")
    (profile / "goals.yaml").write_text(
        yaml.safe_dump(dict(GOALS_FIXTURE, profile=name), allow_unicode=True),
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


class HomeEditingTestBase(unittest.TestCase):
    """Shared env patching: profile roots plus git-backup isolation."""

    def _client(self, root: Path) -> TestClient:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch("nblane.core.profile_io.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)


class TestNorthStarPatch(HomeEditingTestBase):
    """PATCH /profiles/{name}/north-star surgical writes."""

    def test_surgical_edit_leaves_rest_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _profile(root)
            before = (profile / "SKILL.md").read_bytes()
            client = self._client(root)
            response = client.patch(
                "/api/v1/profiles/alice/north-star",
                json={"full": "Become a robotics 大佬"},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["changed"])
            self.assertEqual(payload["changed_keys"], ["full"])
            self.assertEqual(
                payload["north_star"]["full"], "Become a robotics 大佬"
            )
            after = (profile / "SKILL.md").read_bytes()

        expected = before.replace(
            b"- **North Star**: Old north star text\n",
            "- **North Star**: Become a robotics 大佬\n".encode("utf-8"),
        )
        self.assertEqual(after, expected)

    def test_visibility_binary_write_and_legacy_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _profile(root)
            client = self._client(root)

            # Legacy ``discreet`` in the fixture maps to ``private`` on read.
            goals = client.get("/api/v1/profiles/alice/goals")
            self.assertEqual(
                goals.json()["north_star"]["visibility"], "private"
            )

            response = client.patch(
                "/api/v1/profiles/alice/north-star",
                json={"visibility": "public"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["changed_keys"], ["visibility"])
            text = (profile / "SKILL.md").read_text(encoding="utf-8")
        # Canonical new value is written, not the legacy tier.
        self.assertIn("- **North Star Visibility**: public\n", text)
        self.assertNotIn("discreet", text)

    def test_noop_patch_writes_nothing_and_logs_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _profile(root)
            before = (profile / "SKILL.md").read_bytes()
            client = self._client(root)
            response = client.patch(
                "/api/v1/profiles/alice/north-star",
                json={"full": "Old north star text", "visibility": "private"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["changed"])
            self.assertEqual(response.json()["changed_keys"], [])
            self.assertEqual((profile / "SKILL.md").read_bytes(), before)
            self.assertFalse((profile / CHRONICLE_FILENAME).exists())

    def test_vacant_north_star_first_write(self) -> None:
        """Empty-value identity bullet: the rewrite must stay on one line.

        Regression for the `_IDENTITY_BULLET_RE` newline-eating bug: an empty
        value made `:\\s*` swallow the trailing newline, so the new value
        landed on its own bare line and the star never got set.
        """
        vacant = SKILL_MD_FIXTURE.replace(
            "- **North Star**: Old north star text\n", "- **North Star**:\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _profile(root)
            (profile / "SKILL.md").write_text(vacant, encoding="utf-8")
            client = self._client(root)
            response = client.patch(
                "/api/v1/profiles/alice/north-star",
                json={"full": "验收北极星"},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["changed"])
            self.assertTrue(payload["north_star"]["is_set"])
            after = (profile / "SKILL.md").read_bytes()

        expected = vacant.replace(
            "- **North Star**:\n", "- **North Star**:验收北极星\n"
        ).encode("utf-8")
        self.assertEqual(after, expected)
        # And the write is re-readable: a second no-op patch proves the file
        # still parses with the value on the bullet line.
        with tempfile.TemporaryDirectory() as tmp2:
            root2 = Path(tmp2)
            profile2 = _profile(root2)
            (profile2 / "SKILL.md").write_bytes(after)
            client2 = self._client(root2)
            again = client2.patch(
                "/api/v1/profiles/alice/north-star",
                json={"full": "验收北极星"},
            )
            self.assertFalse(again.json()["changed"])

    def test_rewrite_appends_chronicle_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            client.patch(
                "/api/v1/profiles/alice/north-star",
                json={"full": "New star", "brief": "New brief"},
            )
            entries = load_chronicle(root / "alice")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].kind, "north_star.rewritten")
        self.assertEqual(entries[0].note, "New brief")

    def test_validation_and_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            empty = client.patch(
                "/api/v1/profiles/alice/north-star", json={}
            )
            self.assertEqual(empty.status_code, 422)
            bad_visibility = client.patch(
                "/api/v1/profiles/alice/north-star",
                json={"visibility": "discreet"},
            )
            self.assertEqual(bad_visibility.status_code, 422)
            self.assertEqual(
                bad_visibility.json()["code"], "invalid_north_star_visibility"
            )

            first = client.patch(
                "/api/v1/profiles/alice/north-star", json={"brief": "B1"}
            )
            etag = first.headers["ETag"]
            second = client.patch(
                "/api/v1/profiles/alice/north-star", json={"brief": "B2"}
            )
            stale = client.patch(
                "/api/v1/profiles/alice/north-star",
                json={"brief": "B3"},
                headers={"If-Match": etag},
            )
            self.assertEqual(second.status_code, 200)
            self.assertEqual(stale.status_code, 412)
            self.assertEqual(stale.json()["code"], "etag_mismatch")
            self.assertTrue(stale.headers["ETag"].startswith('W/"'))


class TestGoalsCrud(HomeEditingTestBase):
    """POST/PATCH /profiles/{name}/goals mutations."""

    def test_create_goal_appends_chronicle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/goals",
                json={
                    "title": "Learn RL fundamentals",
                    "summary": "Sutton cover to cover",
                    "target": "2027-03-01",
                },
            )
            self.assertEqual(response.status_code, 201)
            payload = response.json()
            goal = payload["goal"]
            self.assertEqual(goal["id"], "goal-learn-rl-fundamentals")
            self.assertEqual(goal["status"], "active")
            self.assertEqual(goal["target"], "2027-03-01")
            self.assertTrue(response.headers["ETag"].startswith('W/"'))

            listing = client.get("/api/v1/profiles/alice/goals")
            ids = [g["id"] for g in listing.json()["goals"]]
            self.assertIn("goal-learn-rl-fundamentals", ids)
            entries = load_chronicle(root / "alice")
        self.assertEqual([e.kind for e in entries], ["goal.added"])
        self.assertEqual(entries[0].ref, "goal-learn-rl-fundamentals")
        self.assertEqual(entries[0].note, "Learn RL fundamentals")

    def test_create_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            blank = client.post(
                "/api/v1/profiles/alice/goals", json={"title": "  "}
            )
            self.assertEqual(blank.status_code, 422)
            bad_date = client.post(
                "/api/v1/profiles/alice/goals",
                json={"title": "X", "target": "next year"},
            )
            self.assertEqual(bad_date.status_code, 422)
            self.assertEqual(bad_date.json()["code"], "invalid_goal_target")
            bad_status = client.post(
                "/api/v1/profiles/alice/goals",
                json={"title": "X", "status": "archived"},
            )
            self.assertEqual(bad_status.status_code, 422)
            self.assertEqual(bad_status.json()["code"], "invalid_goal_status")
            self.assertFalse((root / "alice" / CHRONICLE_FILENAME).exists())

    def test_create_auto_stamps_start_today(self) -> None:
        """立项日 (design §3): start defaults to today; explicit start kept."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            auto = client.post(
                "/api/v1/profiles/alice/goals", json={"title": "Auto start"}
            )
            self.assertEqual(auto.status_code, 201)
            self.assertEqual(
                auto.json()["goal"]["start"], date.today().isoformat()
            )
            explicit = client.post(
                "/api/v1/profiles/alice/goals",
                json={"title": "Backdated", "start": "2026-01-05"},
            )
            self.assertEqual(explicit.status_code, 201)
            self.assertEqual(explicit.json()["goal"]["start"], "2026-01-05")
            bad = client.post(
                "/api/v1/profiles/alice/goals",
                json={"title": "Bad start", "start": "last week"},
            )
            self.assertEqual(bad.status_code, 422)
            self.assertEqual(bad.json()["code"], "invalid_goal_start")
            # Round-trip: the stamped start persists in goals.yaml.
            book = load_goal_book(root / "alice")
            stamped = book.by_id()["goal-auto-start"]
            self.assertEqual(stamped.start, date.today().isoformat())

    def test_patch_goal_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            url = "/api/v1/profiles/alice/goals/goal-2"

            ok = client.patch(url, json={"start": "2026-09-23"})
            self.assertEqual(ok.status_code, 200)
            self.assertEqual(ok.json()["changed_keys"], ["start"])
            self.assertEqual(ok.json()["goal"]["start"], "2026-09-23")

            bad = client.patch(url, json={"start": "someday"})
            self.assertEqual(bad.status_code, 422)
            self.assertEqual(bad.json()["code"], "invalid_goal_start")

            # Empty start clears the field (same semantics as target).
            cleared = client.patch(url, json={"start": ""})
            self.assertEqual(cleared.status_code, 200)
            self.assertEqual(cleared.json()["goal"]["start"], "")

            book = load_goal_book(root / "alice")
        self.assertEqual(book.by_id()["goal-2"].start, "")

    def test_patch_goal_meaningful_changes_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            url = "/api/v1/profiles/alice/goals/goal-ship-vla-demo"

            # No-op patch: nothing written, nothing logged.
            noop = client.patch(url, json={"title": "Ship VLA demo"})
            self.assertEqual(noop.status_code, 200)
            self.assertFalse(noop.json()["changed"])
            self.assertFalse((root / "alice" / CHRONICLE_FILENAME).exists())

            rename = client.patch(url, json={"title": "Ship VLA demo v2"})
            self.assertEqual(rename.json()["changed_keys"], ["title"])
            complete = client.patch(url, json={"status": "completed"})
            self.assertEqual(complete.json()["changed_keys"], ["status"])
            self.assertEqual(complete.json()["goal"]["status"], "completed")
            entries = load_chronicle(root / "alice")
        self.assertEqual(
            [e.kind for e in entries], ["goal.renamed", "goal.completed"]
        )
        self.assertEqual(entries[0].note, "Ship VLA demo v2")
        self.assertEqual(entries[1].ref, "goal-ship-vla-demo")

    def test_patch_goal_unknown_and_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            missing = client.patch(
                "/api/v1/profiles/alice/goals/goal-nope",
                json={"title": "X"},
            )
            self.assertEqual(missing.status_code, 404)
            self.assertEqual(missing.json()["code"], "goal_not_found")

            url = "/api/v1/profiles/alice/goals/goal-2"
            empty = client.patch(url, json={})
            self.assertEqual(empty.status_code, 422)
            blank = client.patch(url, json={"title": " "})
            self.assertEqual(blank.status_code, 422)
            bad_status = client.patch(url, json={"status": "archived"})
            self.assertEqual(bad_status.status_code, 422)

    def test_if_match_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            first = client.post(
                "/api/v1/profiles/alice/goals", json={"title": "One"}
            )
            etag = first.headers["ETag"]
            second = client.post(
                "/api/v1/profiles/alice/goals", json={"title": "Two"}
            )
            self.assertEqual(second.status_code, 201)
            stale = client.patch(
                "/api/v1/profiles/alice/goals/goal-two",
                json={"summary": "late"},
                headers={"If-Match": etag},
            )
            self.assertEqual(stale.status_code, 412)
            self.assertEqual(stale.json()["code"], "etag_mismatch")
            # The stale patch did not land.
            listing = client.get("/api/v1/profiles/alice/goals")
            goals = {g["id"]: g for g in listing.json()["goals"]}
            self.assertEqual(goals["goal-two"]["summary"], "")


class TestChronicleRead(HomeEditingTestBase):
    """GET /profiles/{name}/chronicle."""

    def test_empty_and_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            empty = client.get("/api/v1/profiles/alice/chronicle")
            self.assertEqual(empty.status_code, 200)
            self.assertEqual(empty.json()["entries"], [])
            self.assertEqual(empty.json()["total"], 0)
            self.assertTrue(empty.headers["ETag"].startswith('W/"'))

            client.post("/api/v1/profiles/alice/goals", json={"title": "A"})
            client.post("/api/v1/profiles/alice/goals", json={"title": "B"})
            client.patch(
                "/api/v1/profiles/alice/goals/goal-a",
                json={"status": "completed"},
            )
            listing = client.get("/api/v1/profiles/alice/chronicle")
            payload = listing.json()
            self.assertEqual(payload["total"], 3)
            # Newest first.
            self.assertEqual(
                [e["kind"] for e in payload["entries"]],
                ["goal.completed", "goal.added", "goal.added"],
            )
            limited = client.get("/api/v1/profiles/alice/chronicle?limit=1")
            self.assertEqual(len(limited.json()["entries"]), 1)
            self.assertEqual(
                limited.json()["entries"][0]["kind"], "goal.completed"
            )


class TestHomeEditingScope(HomeEditingTestBase):
    """401/404 enforcement for the home-editing endpoints."""

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
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(create_app())

    def test_unauthenticated_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._auth_client(root)
            patch_star = client.patch(
                "/api/v1/profiles/alice/north-star", json={"brief": "x"}
            )
            create_goal = client.post(
                "/api/v1/profiles/alice/goals", json={"title": "x"}
            )
            patch_goal = client.patch(
                "/api/v1/profiles/alice/goals/goal-2", json={"title": "y"}
            )
            chronicle = client.get("/api/v1/profiles/alice/chronicle")
        self.assertEqual(patch_star.status_code, 401)
        self.assertEqual(create_goal.status_code, 401)
        self.assertEqual(patch_goal.status_code, 401)
        self.assertEqual(chronicle.status_code, 401)

    def test_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            for response in (
                client.patch(
                    "/api/v1/profiles/ghost/north-star", json={"brief": "x"}
                ),
                client.post(
                    "/api/v1/profiles/ghost/goals", json={"title": "x"}
                ),
                client.patch(
                    "/api/v1/profiles/ghost/goals/goal-1", json={"title": "y"}
                ),
                client.get("/api/v1/profiles/ghost/chronicle"),
            ):
                self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
