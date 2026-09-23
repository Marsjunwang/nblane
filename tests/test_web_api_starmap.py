"""Tests for the Phase 3 starmap slice (GET /profiles/{name}/starmap).

Covers the one-shot home-scene aggregation: north star, active goals, the
skill field WITH locked schema nodes (三态 locked/learning/lit) plus zh
category display names, project planets with progress + goal grouping, and
the evidence guests/seated split (30-day window + newest-4 density floor)
with strength/summary/project_refs. Also the source-file ETag and the
400/403/404 guards. All profiles are built under tmp_path; real profiles/
is never touched.
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
from nblane.core.paths import REPO_ROOT
from nblane.web_api import app, create_app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"
PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-starmap-test-secret"

TODAY = date.today()
RECENT = TODAY - timedelta(days=3)  # inside the 30d guest window
OLD_DATES = [TODAY - timedelta(days=40 + i * 10) for i in range(5)]

SKILL_MD_FIXTURE = """# alice · nblane Profile

## Identity

- **Name**: alice
- **North Star**: 成为能独立交付机器人 demo 的工程师
- **North Star Brief**: Ship real robot demos
- **North Star Visibility**: discreet

---
"""

SKILL_TREE_FIXTURE = {
    "profile": "alice",
    "schema": "robotics-engineer",
    "updated": "2026-09-19",
    "nodes": [
        {
            "id": "linux_basics",
            "status": "solid",
            "evidence_refs": ["ev_seated"],
        },
        {"id": "python_core", "status": "learning"},
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
            "start": "2026-01-01",
        },
        {"id": "goal-2", "title": "Stay healthy", "status": "active"},
        {"id": "goal-3", "title": "Old goal", "status": "archived"},
    ],
}

KANBAN_FIXTURE = """# alice · Kanban

## Doing

- [ ] Arm doing task
  - id: kb_doing_p1
  - project_id: project:robot-arm
  - started_on: 2026-09-20

---

## Done

- [x] Arm done task
  - id: kb_done_p1
  - project_id: project:robot-arm
  - completed_on: 2026-09-18

---

## Queue

- [ ] Arm queued task
  - id: kb_queue_p1
  - project_id: project:robot-arm

---
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
            "time_range": "2026-09-01/2026-12-31",
            "goal_refs": ["goal-1"],
        },
        {
            "id": "project:solo",
            "title": "Solo Project",
            "status": "active",
            "milestones": [
                {"id": "m1", "title": "One", "status": "completed"},
                {"id": "m2", "title": "Two", "status": "planned"},
            ],
        },
    ],
}


def _evidence_entries() -> list[dict]:
    entries = [
        {
            "id": "ev_recent",
            "type": "project",
            "title": "Recent grasping run",
            "date": RECENT.isoformat(),
            "strength": "strong",
            "review_status": "needs_review",
            "summary": "Ran the grasping pipeline.",
            "project_refs": ["project:robot-arm"],
        },
        {
            "id": "ev_seated",
            "type": "practice",
            "title": "Seated practice",
            "date": OLD_DATES[0].isoformat(),
            "strength": "medium",
            "review_status": "reviewed",
            "summary": "Old practice, seated by project.",
            "project_refs": ["project:robot-arm"],
        },
    ]
    # Four more dated entries, progressively older (floor ordering check).
    for i, day in enumerate(OLD_DATES[1:], start=1):
        entries.append(
            {
                "id": f"ev_old_{i}",
                "type": "practice",
                "title": f"Old entry {i}",
                "date": day.isoformat(),
                "review_status": "reviewed",
            }
        )
    entries.append(
        {
            "id": "ev_gone",
            "type": "practice",
            "title": "Deprecated entry",
            "date": RECENT.isoformat(),
            "deprecated": True,
        }
    )
    return entries


def _starmap_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            text = text.replace("{YYYY-MM-DD}", "2026-09-19")
            file_path.write_text(text, encoding="utf-8")
    (profile / "SKILL.md").write_text(SKILL_MD_FIXTURE, encoding="utf-8")
    (profile / "skill-tree.yaml").write_text(
        yaml.safe_dump(dict(SKILL_TREE_FIXTURE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "goals.yaml").write_text(
        yaml.safe_dump(dict(GOALS_FIXTURE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "kanban.md").write_text(KANBAN_FIXTURE, encoding="utf-8")
    (profile / "project-board.yaml").write_text(
        yaml.safe_dump(dict(PROJECT_BOARD_FIXTURE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "evidence-pool.yaml").write_text(
        yaml.safe_dump(
            {
                "profile": name,
                "updated": "2026-09-19",
                "evidence_entries": _evidence_entries(),
            },
            allow_unicode=True,
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


class StarmapTestBase(unittest.TestCase):
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


class TestStarmapGet(StarmapTestBase):
    """GET /starmap aggregation shape and semantics."""

    def _get(self, client: TestClient) -> dict:
        response = client.get("/api/v1/profiles/alice/starmap")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["ETag"].startswith('W/"'))
        return response.json()

    def test_top_level_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _starmap_profile(root)
            payload = self._get(self._client(root))
        self.assertEqual(payload["profile"], "alice")
        self.assertEqual(payload["generated_on"], TODAY.isoformat())
        self.assertEqual(payload["schema_name"], "robotics-engineer")
        self.assertEqual(
            payload["north_star"], "成为能独立交付机器人 demo 的工程师"
        )

    def test_goals_active_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _starmap_profile(root)
            payload = self._get(self._client(root))
        goals = payload["goals"]
        self.assertEqual([g["id"] for g in goals], ["goal-1", "goal-2"])
        self.assertEqual(goals[0]["target"], "2026-12-31")
        self.assertEqual(goals[0]["summary"], "Demo first")

    def test_locked_schema_nodes_included(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _starmap_profile(root)
            payload = self._get(self._client(root))
        skills = {s["id"]: s for s in payload["skills"]}
        # Overlay nodes carry their status…
        self.assertEqual(skills["linux_basics"]["status"], "solid")
        self.assertTrue(skills["linux_basics"]["lit"])
        self.assertEqual(skills["python_core"]["status"], "learning")
        self.assertFalse(skills["python_core"]["lit"])
        # …and schema nodes absent from the overlay ride along as locked.
        self.assertGreater(len(skills), 2)
        locked = [s for s in payload["skills"] if s["status"] == "locked"]
        self.assertGreater(len(locked), 10)
        self.assertIn("ros2_basics", skills)
        self.assertFalse(skills["ros2_basics"]["lit"])

    def test_categories_with_zh_names_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _starmap_profile(root)
            payload = self._get(self._client(root))
        cats = {c["id"]: c for c in payload["categories"]}
        self.assertEqual(cats["foundations"]["name"], "基础")
        # linux_basics + python_core + the other schema foundations nodes.
        self.assertEqual(cats["foundations"]["lit_count"], 1)
        self.assertEqual(cats["foundations"]["learning_count"], 1)
        total = sum(c["count"] for c in payload["categories"])
        self.assertEqual(total, len(payload["skills"]))

    def test_projects_progress_and_goal_grouping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _starmap_profile(root)
            payload = self._get(self._client(root))
        projects = {p["id"]: p for p in payload["projects"]}
        arm = projects["project:robot-arm"]
        # Board grouping: planet hangs under its first goal.
        self.assertEqual(arm["goal_ids"], ["goal-1"])
        # column_counts first: done 1 / total 3.
        self.assertEqual(arm["task_count"], 3)
        self.assertAlmostEqual(arm["progress"], 1 / 3, places=3)
        solo = projects["project:solo"]
        self.assertEqual(solo["goal_ids"], [])
        # Milestone fallback: 1 done of 2.
        self.assertEqual(solo["progress"], 0.5)
        self.assertEqual(solo["task_count"], 0)

    def test_evidence_guest_window_and_floor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _starmap_profile(root)
            payload = self._get(self._client(root))
        evidence = {e["id"]: e for e in payload["evidence"]}
        # Deprecated entries are excluded entirely.
        self.assertNotIn("ev_gone", evidence)
        self.assertEqual(len(evidence), 6)
        # Inside the 30d window -> guest star.
        self.assertTrue(evidence["ev_recent"]["flying"])
        # Newest-4 density floor: the four newest dated entries overall
        # (ev_recent, ev_seated, ev_old_1, ev_old_2) fly even when older
        # than the window; the two oldest stay seated.
        self.assertTrue(evidence["ev_seated"]["flying"])
        self.assertTrue(evidence["ev_old_1"]["flying"])
        self.assertTrue(evidence["ev_old_2"]["flying"])
        self.assertFalse(evidence["ev_old_3"]["flying"])
        self.assertFalse(evidence["ev_old_4"]["flying"])
        counts = payload["counts"]
        self.assertEqual(counts["evidence"], 6)
        self.assertEqual(counts["evidence_flying"], 4)
        self.assertEqual(counts["evidence_needs_review"], 1)
        self.assertEqual(counts["projects_active"], 2)
        self.assertEqual(counts["skills_lit"], 1)

    def test_evidence_strength_summary_and_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _starmap_profile(root)
            payload = self._get(self._client(root))
        evidence = {e["id"]: e for e in payload["evidence"]}
        recent = evidence["ev_recent"]
        self.assertEqual(recent["strength"], "strong")
        self.assertEqual(recent["summary"], "Ran the grasping pipeline.")
        self.assertEqual(recent["project_refs"], ["project:robot-arm"])
        # Reverse skill links come from the tree overlay's evidence_refs.
        self.assertEqual(evidence["ev_seated"]["skill_ids"], ["linux_basics"])
        # Unrated strength / unknown review status normalize.
        old = evidence["ev_old_1"]
        self.assertEqual(old["strength"], "unrated")
        self.assertEqual(old["review_status"], "reviewed")

    def test_etag_changes_with_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _starmap_profile(root)
            client = self._client(root)
            first = client.get("/api/v1/profiles/alice/starmap")
            second = client.get("/api/v1/profiles/alice/starmap")
            self.assertEqual(first.headers["ETag"], second.headers["ETag"])
            with (profile / "evidence-pool.yaml").open("a", encoding="utf-8") as fh:
                fh.write("\n")
            third = client.get("/api/v1/profiles/alice/starmap")
        self.assertNotEqual(first.headers["ETag"], third.headers["ETag"])

    def test_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _starmap_profile(root)
            response = self._client(root).get("/api/v1/profiles/nobody/starmap")
        self.assertEqual(response.status_code, 404)

    def test_invalid_profile_name_400(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _starmap_profile(root)
            response = self._client(root).get("/api/v1/profiles/%2E%2E/starmap")
        self.assertEqual(response.status_code, 400)


class TestStarmapScope(StarmapTestBase):
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
            _starmap_profile(root)
            response = self._auth_client(root).get("/api/v1/profiles/alice/starmap")
        self.assertEqual(response.status_code, 401)

    def test_member_forbidden_from_other_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _starmap_profile(root, "alice")
            _starmap_profile(root, "wang")
            client = self._auth_client(root)
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            forbidden = client.get("/api/v1/profiles/alice/starmap")
            allowed = client.get("/api/v1/profiles/wang/starmap")
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.json()["code"], "profile_forbidden")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["profile"], "wang")


if __name__ == "__main__":
    unittest.main()
