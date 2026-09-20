"""Tests for the M1 profile-scoped read endpoints of the FastAPI backend."""

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
TEST_SESSION_SECRET = "web-api-reads-test-secret"

KANBAN_MD = """# alice · Kanban

> Updated: 2026-09-18

---

## Doing

- [ ] Build robot arm
  - id: kb_doing1
  - context: M1 milestone
  - tags: robotics, hardware
  - started_on: 2026-09-01
  - [x] Gather parts
  - [ ] Wire motors
  - order the torque sensor

---

## Done

- [x] Setup repo
  - id: kb_done1
  - completed_on: 2026-08-30

---

## Queue

- (empty)

---

## Someday / Maybe

- Learn advanced MoveIt

---
"""

AGENT_ACTIVITY = {
    "schema_version": "1.0",
    "profile": "alice",
    "items": [
        {
            "id": "act:candidate:aaa",
            "kind": "candidate",
            "candidate_type": "agent_dispatch",
            "source_page": "Kanban",
            "target_owner": "kanban",
            "status": "pending",
            "title": "Pending candidate",
            "summary": "first",
            "payload": {"agent_task_id": "agenttask_1"},
            "updated": "2026-09-18T10:00:00+00:00",
        },
        {
            "id": "act:patch:bbb",
            "kind": "patch",
            "candidate_type": "skill_update",
            "target_owner": "skill_tree",
            "status": "pending",
            "title": "Pending patch",
            "updated": "2026-09-18T12:00:00+00:00",
        },
        {
            "id": "act:candidate:ccc",
            "kind": "candidate",
            "candidate_type": "evidence_draft",
            "target_owner": "evidence_pool",
            "status": "applied",
            "title": "Applied candidate",
            "updated": "2026-09-17T09:00:00+00:00",
        },
    ],
}

INBOX = {
    "profile": "alice",
    "items": [
        {
            "id": "inbox_20260918_001",
            "title": "Read the SLAM survey",
            "type": "link",
            "source": "https://example.org/slam",
            "status": "inbox",
            "tags": ["robotics"],
        },
        {
            "id": "inbox_20260918_002",
            "title": "Captured idea",
            "status": "captured",
        },
        {
            "id": "inbox_20260917_001",
            "title": "Clarified note",
            "status": "clarified",
        },
        {
            "id": "inbox_20260901_001",
            "title": "Old archived note",
            "status": "archived",
        },
    ],
}

SKILL_MD = """# SKILL — alice

## Identity

- **Name**: Alice
- **Domain**: Robotics
- **North Star**: Become a robotics generalist who ships real demos
- **North Star Brief**: Ship real robot demos
- **North Star Visibility**: discreet

---

## Core Competencies
"""

EVIDENCE_POOL = {
    "profile": "alice",
    "evidence_entries": [
        {
            "id": "ev_1",
            "type": "project",
            "title": "Built ROS2 pick demo",
            "date": "2026-08-20",
            "url": "https://example.org/demo",
            "summary": "End-to-end pick-and-place demo",
            "strength": "strong",
            "review_status": "reviewed",
            "source_refs": ["kb_doing1", "out_blog1"],
            "project_refs": ["proj_demo"],
            "source_excerpt": "demo ran 20 pick cycles",
            "origin": "manual",
            "origin_ref": "kanban:kb_doing1",
            "language": "en",
        },
        {
            "id": "ev_2",
            "type": "learning",
            "title": "MoveIt2 workshop notes",
            "date": "2026-07-15",
            "summary": "Workshop takeaways",
        },
        {
            "id": "ev_3",
            "type": "output",
            "title": "Published grasp paper review",
            "date": "2026-06-01",
            "review_status": "reviewed",
            "url": "https://example.org/blog/grasp",
        },
        {
            "id": "ev_4",
            "type": "project",
            "title": "Old demo v1",
            "date": "2025-12-01",
            "deprecated": True,
            "replaced_by": "ev_1",
        },
    ],
}

AGENT_TASKS = {
    "schema_version": "1.0",
    "profile": "alice",
    "tasks": [
        {
            "id": "agenttask_1",
            "target_harness": "codex",
            "role": "researcher",
            "title": "Survey grasp planners",
            "status": "ready",
        },
        {
            "id": "agenttask_2",
            "target_harness": "opencode",
            "role": "remote_dev",
            "title": "Refactor driver node",
            "status": "running",
        },
        {
            "id": "agenttask_3",
            "target_harness": "codex",
            "role": "reviewer",
            "title": "Review motion plan PR",
            "status": "applied",
        },
    ],
}

GOALS = {
    "schema_version": "1.0",
    "profile": "alice",
    "current_goal_id": "goal_main",
    "goals": [
        {
            "id": "goal_main",
            "title": "Ship the pick-and-place demo",
            "label": "Stage goal",
            "status": "active",
            "target": "2026-12-31",
            "ui_visibility": "visible",
            "summary": "Public demo summary",
            "target_skills": ["ros2_basics", "moveit2"],
            "skill_links": [
                {
                    "node_id": "moveit2",
                    "label": "Motion planning",
                    "source": "manual",
                    "score": 8,
                }
            ],
            "success_criteria": ["Demo runs end to end"],
            "focus": ["integration"],
            "notes": "owner notes",
        },
        {
            "id": "goal_private",
            "title": "Private career goal",
            "status": "active",
            "ui_visibility": "private",
            "summary": "private summary",
            "notes": "secret owner-only notes",
        },
    ],
}


def _write_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    profile.mkdir(parents=True)
    (profile / "kanban.md").write_text(KANBAN_MD.replace("alice", name), encoding="utf-8")
    (profile / "SKILL.md").write_text(SKILL_MD.replace("alice", name), encoding="utf-8")

    def _dump(filename: str, doc: dict) -> None:
        data = dict(doc)
        data["profile"] = name
        (profile / filename).write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    _dump("agent-activity.yaml", AGENT_ACTIVITY)
    _dump("inbox.yaml", INBOX)
    _dump("agent-tasks.yaml", AGENT_TASKS)
    _dump("goals.yaml", GOALS)
    _dump("evidence-pool.yaml", EVIDENCE_POOL)
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
                    "admin": {
                        "display_name": "Admin",
                        "password_hash": stored,
                        "role": "admin",
                        "teams": ["*"],
                    },
                    "wang": {
                        "display_name": "Wang",
                        "password_hash": stored,
                        "role": "member",
                        "profile": "wang",
                        "teams": ["example-team"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return path


class TestProfileReads(unittest.TestCase):
    """Happy paths, filters, and 404s against a rich tmp profile."""

    def _client(self, root: Path) -> TestClient:
        # Loaders resolve profile dirs through profile_io; profile_health
        # goes through the core.io compat facade, so patch both.
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(app)

    def test_activity_defaults_to_pending_with_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/activity")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertEqual(payload["status"], "pending")
        self.assertEqual(payload["limit"], 50)
        self.assertEqual(payload["total"], 2)
        ids = [item["id"] for item in payload["items"]]
        self.assertEqual(ids, ["act:patch:bbb", "act:candidate:aaa"])
        item = payload["items"][0]
        self.assertEqual(item["kind"], "patch")
        self.assertEqual(item["target_owner"], "skill_tree")
        # Summary counts the whole queue, not just the filtered page.
        summary = payload["summary"]
        self.assertEqual(summary["status"], {"pending": 2, "applied": 1})
        self.assertEqual(summary["kind"], {"candidate": 2, "patch": 1})
        self.assertIn("target_owner", summary)
        self.assertIn("candidate_type", summary)

    def test_activity_status_kind_and_limit_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            applied = client.get(
                "/api/v1/profiles/alice/activity", params={"status": "applied"}
            )
            by_kind = client.get(
                "/api/v1/profiles/alice/activity",
                params={"status": "all", "kind": "candidate"},
            )
            limited = client.get(
                "/api/v1/profiles/alice/activity",
                params={"status": "all", "limit": 2},
            )
        self.assertEqual(applied.status_code, 200)
        self.assertEqual(
            [i["id"] for i in applied.json()["items"]], ["act:candidate:ccc"]
        )
        self.assertEqual(by_kind.status_code, 200)
        self.assertEqual(
            {i["kind"] for i in by_kind.json()["items"]}, {"candidate"}
        )
        self.assertEqual(by_kind.json()["total"], 2)
        self.assertEqual(limited.status_code, 200)
        self.assertEqual(limited.json()["total"], 3)
        self.assertEqual(len(limited.json()["items"]), 2)

    def test_activity_item_detail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get(
                "/api/v1/profiles/alice/activity/act:candidate:aaa"
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["id"], "act:candidate:aaa")
        self.assertEqual(payload["title"], "Pending candidate")
        self.assertEqual(payload["payload"], {"agent_task_id": "agenttask_1"})
        self.assertEqual(payload["candidate_type"], "agent_dispatch")

    def test_activity_item_detail_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/activity/act:nope")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "activity_item_not_found")

    def test_kanban_returns_parsed_board(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/kanban")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertEqual(payload["total"], 3)
        sections = {s["name"]: s["tasks"] for s in payload["sections"]}
        self.assertEqual(
            set(sections), {"Doing", "Done", "Queue", "Someday / Maybe"}
        )
        doing = sections["Doing"]
        self.assertEqual(len(doing), 1)
        task = doing[0]
        self.assertEqual(task["title"], "Build robot arm")
        self.assertEqual(task["id"], "kb_doing1")
        self.assertEqual(task["context"], "M1 milestone")
        self.assertEqual(task["tags"], "robotics, hardware")
        self.assertEqual(task["started_on"], "2026-09-01")
        self.assertFalse(task["done"])
        self.assertEqual(
            [(st["title"], st["done"]) for st in task["subtasks"]],
            [("Gather parts", True), ("Wire motors", False)],
        )
        self.assertEqual(task["details"], ["order the torque sensor"])
        self.assertEqual(sections["Done"][0]["completed_on"], "2026-08-30")
        self.assertEqual(sections["Queue"], [])
        self.assertEqual(
            sections["Someday / Maybe"][0]["title"], "Learn advanced MoveIt"
        )
        # No markdown body leaks into the structured response.
        self.assertNotIn("# alice", str(payload))

    def test_inbox_defaults_to_open_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/inbox")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["statuses"], ["inbox", "captured", "clarified"])
        self.assertEqual(payload["total"], 3)
        self.assertNotIn("archived", {i["status"] for i in payload["items"]})
        first = payload["items"][0]
        self.assertEqual(first["id"], "inbox_20260918_001")
        self.assertEqual(first["tags"], ["robotics"])
        self.assertEqual(first["source"], "https://example.org/slam")
        self.assertIn("history", first)

    def test_inbox_status_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            archived = client.get(
                "/api/v1/profiles/alice/inbox", params={"status": "archived"}
            )
            everything = client.get(
                "/api/v1/profiles/alice/inbox", params={"status": "all"}
            )
        self.assertEqual(archived.status_code, 200)
        self.assertEqual(archived.json()["total"], 1)
        self.assertEqual(
            archived.json()["items"][0]["title"], "Old archived note"
        )
        self.assertEqual(everything.json()["total"], 4)

    def test_agent_tasks_list_and_status_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            all_tasks = client.get("/api/v1/profiles/alice/agent-tasks")
            running = client.get(
                "/api/v1/profiles/alice/agent-tasks",
                params={"status": "running"},
            )
        self.assertEqual(all_tasks.status_code, 200)
        self.assertEqual(all_tasks.json()["total"], 3)
        first = all_tasks.json()["tasks"][0]
        self.assertEqual(first["id"], "agenttask_1")
        self.assertEqual(first["target_harness"], "codex")
        self.assertEqual(first["role"], "researcher")
        self.assertEqual(running.status_code, 200)
        self.assertEqual(running.json()["total"], 1)
        self.assertEqual(running.json()["tasks"][0]["id"], "agenttask_2")

    def test_goals_return_full_owner_view_without_redaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/goals")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["current_goal_id"], "goal_main")
        goals = {g["id"]: g for g in payload["goals"]}
        self.assertEqual(set(goals), {"goal_main", "goal_private"})
        main = goals["goal_main"]
        self.assertEqual(main["title"], "Ship the pick-and-place demo")
        self.assertEqual(main["target_skills"], ["ros2_basics", "moveit2"])
        self.assertEqual(main["skill_links"][0]["node_id"], "moveit2")
        self.assertEqual(main["success_criteria"], ["Demo runs end to end"])
        # The owner's UI gets private goals in full; redaction is agent-side.
        private = goals["goal_private"]
        self.assertEqual(private["ui_visibility"], "private")
        self.assertEqual(private["notes"], "secret owner-only notes")
        self.assertEqual(private["summary"], "private summary")

    def test_goals_include_full_north_star_for_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/goals")
        self.assertEqual(response.status_code, 200)
        north_star = response.json()["north_star"]
        self.assertTrue(north_star["is_set"])
        self.assertEqual(north_star["visibility"], "discreet")
        # Owner view: no discreet/hidden redaction, full and brief verbatim.
        self.assertEqual(
            north_star["full"],
            "Become a robotics generalist who ships real demos",
        )
        self.assertEqual(north_star["brief"], "Ship real robot demos")

    def test_evidence_list_defaults_to_non_deprecated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/evidence")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertEqual(payload["status"], "")
        self.assertEqual(payload["limit"], 100)
        self.assertEqual(payload["total"], 3)
        ids = [item["id"] for item in payload["items"]]
        self.assertEqual(ids, ["ev_1", "ev_2", "ev_3"])
        first = payload["items"][0]
        self.assertEqual(first["title"], "Built ROS2 pick demo")
        self.assertEqual(first["evidence_type"], "project")
        self.assertEqual(first["review_status"], "reviewed")
        self.assertEqual(first["date"], "2026-08-20")
        self.assertEqual(first["url"], "https://example.org/demo")
        self.assertEqual(first["source_refs"], ["kb_doing1", "out_blog1"])
        self.assertEqual(first["summary"], "End-to-end pick-and-place demo")
        # Empty review_status normalizes to needs_review for display.
        second = payload["items"][1]
        self.assertEqual(second["review_status"], "needs_review")

    def test_evidence_status_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            reviewed = client.get(
                "/api/v1/profiles/alice/evidence", params={"status": "reviewed"}
            )
            needs = client.get(
                "/api/v1/profiles/alice/evidence",
                params={"status": "needs_review"},
            )
            everything = client.get(
                "/api/v1/profiles/alice/evidence", params={"status": "all"}
            )
            deprecated = client.get(
                "/api/v1/profiles/alice/evidence",
                params={"status": "deprecated"},
            )
        self.assertEqual(
            [i["id"] for i in reviewed.json()["items"]], ["ev_1", "ev_3"]
        )
        self.assertEqual([i["id"] for i in needs.json()["items"]], ["ev_2"])
        self.assertEqual(everything.json()["total"], 4)
        dep_items = deprecated.json()["items"]
        self.assertEqual([i["id"] for i in dep_items], ["ev_4"])

    def test_evidence_q_filter_is_case_insensitive_title_substring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            moveit = client.get(
                "/api/v1/profiles/alice/evidence", params={"q": "moveit2"}
            )
            demo = client.get(
                "/api/v1/profiles/alice/evidence", params={"q": "DEMO"}
            )
        self.assertEqual(moveit.json()["total"], 1)
        self.assertEqual(moveit.json()["items"][0]["id"], "ev_2")
        # "DEMO" matches "Built ROS2 pick demo"; deprecated "Old demo v1" is
        # excluded by the default status filter.
        self.assertEqual(demo.json()["total"], 1)
        self.assertEqual(demo.json()["items"][0]["id"], "ev_1")

    def test_evidence_limit_caps_items_but_not_total(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get(
                "/api/v1/profiles/alice/evidence", params={"limit": 2}
            )
            too_big = client.get(
                "/api/v1/profiles/alice/evidence", params={"limit": 501}
            )
        payload = response.json()
        self.assertEqual(payload["total"], 3)
        self.assertEqual(len(payload["items"]), 2)
        self.assertEqual(payload["limit"], 2)
        self.assertEqual(too_big.status_code, 422)

    def test_evidence_detail_returns_full_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/evidence/ev_1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["id"], "ev_1")
        self.assertEqual(payload["title"], "Built ROS2 pick demo")
        self.assertEqual(payload["strength"], "strong")
        self.assertEqual(payload["project_refs"], ["proj_demo"])
        self.assertEqual(payload["source_excerpt"], "demo ran 20 pick cycles")
        self.assertEqual(payload["origin"], "manual")
        self.assertEqual(payload["origin_ref"], "kanban:kb_doing1")
        self.assertEqual(payload["language"], "en")
        self.assertFalse(payload["deprecated"])

    def test_evidence_detail_404_for_unknown_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/evidence/ev_nope")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "evidence_not_found")

    def test_unknown_profile_404_on_all_read_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            responses = [
                client.get("/api/v1/profiles/nobody/activity"),
                client.get("/api/v1/profiles/nobody/activity/act:x"),
                client.get("/api/v1/profiles/nobody/kanban"),
                client.get("/api/v1/profiles/nobody/inbox"),
                client.get("/api/v1/profiles/nobody/agent-tasks"),
                client.get("/api/v1/profiles/nobody/goals"),
                client.get("/api/v1/profiles/nobody/evidence"),
                client.get("/api/v1/profiles/nobody/evidence/ev_1"),
            ]
        for response in responses:
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["code"], "profile_not_found")


class TestProfileScopeEnforcement(unittest.TestCase):
    """403 rules for profile-scoped routes under auth-on and auth-off."""

    def _patched_root(self, root: Path) -> None:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()

    def _auth_client(self, root: Path) -> TestClient:
        self._patched_root(root)
        users_file = _write_users_file(root / "users.yaml")
        env = {
            "NBLANE_AUTH_FILE": str(users_file),
            "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
        }
        patcher = patch.dict(os.environ, env)
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(create_app())

    def test_member_forbidden_from_other_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root, "alice")
            _write_profile(root, "wang")
            client = self._auth_client(root)
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            forbidden = [
                client.get("/api/v1/profiles/alice/activity"),
                client.get("/api/v1/profiles/alice/kanban"),
                client.get("/api/v1/profiles/alice/inbox"),
                client.get("/api/v1/profiles/alice/agent-tasks"),
                client.get("/api/v1/profiles/alice/goals"),
                client.get("/api/v1/profiles/alice/evidence"),
                client.get("/api/v1/profiles/alice/evidence/ev_1"),
                client.get("/api/v1/profiles/alice/summary"),
            ]
            allowed = client.get("/api/v1/profiles/wang/kanban")
        for response in forbidden:
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["code"], "profile_forbidden")
        self.assertEqual(allowed.status_code, 200)

    def test_admin_wildcard_can_access_any_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root, "alice")
            client = self._auth_client(root)
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            response = client.get("/api/v1/profiles/alice/goals")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["profile"], "alice")

    def test_auth_off_allows_every_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root, "alice")
            self._patched_root(root)
            env = {
                "NBLANE_AUTH_FILE": "",
                "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
            }
            patcher = patch.dict(os.environ, env)
            self.addCleanup(patcher.stop)
            patcher.start()
            client = TestClient(create_app())
            response = client.get("/api/v1/profiles/alice/activity")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
