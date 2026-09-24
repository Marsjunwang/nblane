"""Tests for G1 (openclaw writeback trace) and G2 (per-request git actor).

G1: mutations by the ``openclaw`` service account append ``kind=writeback``
entries (``source_page="openclaw"``, ``status="applied"``) to
agent-activity.yaml via ``record_writeback_activity`` — but only when the
mutation actually changed something, and never for other users.

G2: ``GitActorMiddleware`` starts a ``git_backup`` operation per request
scoped to the current user id, so ``record_change`` commits as the caller
instead of the default ``cli`` actor.

All profiles live under tmp dirs; real profiles/ is never touched.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.core import git_backup
from nblane.core import plan_templates
from nblane.core.kanban_io import render_kanban
from nblane.core.models import KanbanTask
from nblane.core.paths import REPO_ROOT
from nblane.web_api import app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"
PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-agent-writeback-test-secret"

ACTIVITY_LOG = {
    "profile": "alice",
    "habits": [
        {"id": "exercise", "title": "Exercise", "kind": "health",
         "cadence": "daily"},
    ],
    "checkins": [
        {"id": "act_20260920_exercise", "date": "2026-09-20",
         "habit_id": "exercise", "habits": ["exercise"], "summary": "run"},
    ],
    "weekly_summaries": [],
}

EVIDENCE_POOL = {
    "profile": "alice",
    "evidence_entries": [
        {"id": "ev_alpha", "type": "project", "title": "Alpha"},
        {"id": "ev_gamma", "type": "paper", "title": "Gamma",
         "deprecated": True},
    ],
}

SKILL_TREE = {
    "profile": "alice",
    "schema": "robotics-engineer",
    "updated": "2026-09-10",
    "nodes": [
        {"id": "ros2_basics", "status": "solid"},
        {"id": "slam_basics", "status": "learning"},
    ],
}


def _write_profile(root: Path, name: str = "alice") -> Path:
    """Template-based profile with controlled kanban/log/pool/tree files."""
    profile = root / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            text = text.replace("{YYYY-MM-DD}", "2026-09-19")
            file_path.write_text(text, encoding="utf-8")
    (profile / "activity-log.yaml").write_text(
        yaml.safe_dump(dict(ACTIVITY_LOG, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "evidence-pool.yaml").write_text(
        yaml.safe_dump(dict(EVIDENCE_POOL, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "skill-tree.yaml").write_text(
        yaml.safe_dump(dict(SKILL_TREE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    sections = {
        "Queue": [KanbanTask(title="Card One", id="taskQ")],
        "Done": [
            KanbanTask(
                title="Tuned latency",
                id="taskA",
                done=True,
                completed_on="2026-01-02",
            )
        ],
    }
    (profile / "kanban.md").write_text(
        render_kanban(name, sections), encoding="utf-8"
    )
    return profile


def _write_users_file(path: Path) -> Path:
    """Users: openclaw service account (member), admin, and a plain member."""
    stored = auth_core.hash_password(
        PASSWORD, iterations=100_000, salt=b"0123456789abcdef"
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
                        "profiles": ["alice"],
                    },
                    "openclaw": {
                        "display_name": "openclaw",
                        "password_hash": stored,
                        "role": "member",
                        "profiles": ["alice"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def _writeback_items(profile: Path) -> list[dict]:
    path = profile / "agent-activity.yaml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [
        item
        for item in (raw.get("items") or [])
        if isinstance(item, dict) and item.get("kind") == "writeback"
    ]


class AgentWritebackTestBase(unittest.TestCase):
    """Shared setup: tmp profile root, auth-on env, git-backup isolation."""

    def _client(self, root: Path, *, login: str | None = None) -> TestClient:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
            "nblane.core.project_board.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        env = {
            "NBLANE_AUTH_FILE": str(_write_users_file(root / "users.yaml")),
            "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
        }
        patcher = patch.dict(os.environ, env)
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch("nblane.core.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        client = TestClient(app)
        if login is not None:
            response = client.post(
                "/api/v1/auth/login",
                json={"username": login, "password": PASSWORD},
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["id"], login)
        return client


class TestOpenclawWriteback(AgentWritebackTestBase):
    """G1: openclaw mutations land writeback entries with correct shape."""

    def test_checkin_add_and_delete_traced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            profile = _write_profile(root)
            client = self._client(root, login="openclaw")
            added = client.post(
                "/api/v1/profiles/alice/checkins",
                json={"habit": "exercise", "summary": "5k run"},
            )
            self.assertEqual(added.status_code, 201, added.text)
            deleted = client.delete(
                "/api/v1/profiles/alice/checkins/act_20260920_exercise"
            )
            self.assertEqual(deleted.status_code, 200, deleted.text)
            items = _writeback_items(profile)

        self.assertEqual(len(items), 2)
        add_item = next(
            i for i in items if i["candidate_type"] == "checkin.add"
        )
        del_item = next(
            i for i in items if i["candidate_type"] == "checkin.delete"
        )
        for item in (add_item, del_item):
            self.assertEqual(item["source_page"], "openclaw")
            self.assertEqual(item["target_owner"], "work")
            self.assertEqual(item["status"], "applied")
            self.assertTrue(item["applied_at"])
            self.assertTrue(item["title"])
            self.assertTrue(
                item["source_ref"].startswith("openclaw:"), item["source_ref"]
            )
        self.assertEqual(add_item["refs"]["habit"], "exercise")
        self.assertTrue(add_item["refs"]["checkin_id"])
        self.assertTrue(
            any("activity-log.yaml" in p for p in add_item["changed_paths"])
        )
        self.assertEqual(
            del_item["refs"]["checkin_id"], "act_20260920_exercise"
        )

    def test_kanban_mutations_traced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            profile = _write_profile(root)
            client = self._client(root, login="openclaw")
            created = client.post(
                "/api/v1/profiles/alice/kanban/cards",
                json={"title": "Write G1 tests"},
            )
            self.assertEqual(created.status_code, 201, created.text)
            moved = client.post(
                "/api/v1/profiles/alice/kanban/cards/Write G1 tests/move",
                json={"target_section": "Doing"},
            )
            self.assertEqual(moved.status_code, 200, moved.text)
            scheduled = client.post(
                "/api/v1/profiles/alice/kanban/cards/Write G1 tests/schedule",
                json={"planned_start": "2026-09-25"},
            )
            self.assertEqual(scheduled.status_code, 200, scheduled.text)
            patched = client.patch(
                "/api/v1/profiles/alice/kanban/cards/Write G1 tests",
                json={"context": "agent trace"},
            )
            self.assertEqual(patched.status_code, 200, patched.text)
            done = client.post(
                "/api/v1/profiles/alice/kanban/cards/Write G1 tests/done"
            )
            self.assertEqual(done.status_code, 200, done.text)
            deleted = client.delete(
                "/api/v1/profiles/alice/kanban/cards/Write G1 tests"
            )
            self.assertEqual(deleted.status_code, 200, deleted.text)
            items = _writeback_items(profile)

        actions = [item["candidate_type"] for item in items]
        self.assertEqual(
            actions,
            [
                "kanban.card.add",
                "kanban.card.move",
                "kanban.card.schedule",
                "kanban.card.patch",
                "kanban.card.done",
                "kanban.card.delete",
            ],
        )
        for item in items:
            self.assertEqual(item["status"], "applied")
            self.assertEqual(item["source_page"], "openclaw")
            self.assertTrue(
                any("kanban.md" in p for p in item["changed_paths"]),
                item,
            )

    def test_goals_north_star_and_skill_node_traced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            profile = _write_profile(root)
            client = self._client(root, login="openclaw")
            created = client.post(
                "/api/v1/profiles/alice/goals",
                json={"title": "Ship G1", "status": "active"},
            )
            self.assertEqual(created.status_code, 201, created.text)
            goal_id = created.json()["goal"]["id"]
            patched = client.patch(
                f"/api/v1/profiles/alice/goals/{goal_id}",
                json={"status": "completed"},
            )
            self.assertEqual(patched.status_code, 200, patched.text)
            star = client.patch(
                "/api/v1/profiles/alice/north-star",
                json={"visibility": "public"},
            )
            self.assertEqual(star.status_code, 200, star.text)
            self.assertTrue(star.json()["changed"])
            node = client.patch(
                "/api/v1/profiles/alice/skill-tree/nodes/slam_basics",
                json={"status": "lit"},
            )
            self.assertEqual(node.status_code, 200, node.text)
            self.assertTrue(node.json()["changed"])
            items = _writeback_items(profile)

        actions = [item["candidate_type"] for item in items]
        self.assertEqual(
            actions,
            ["goal.add", "goal.patch", "north_star.patch", "skill_node.patch"],
        )
        node_item = items[-1]
        self.assertEqual(node_item["refs"]["node_id"], "slam_basics")
        self.assertEqual(node_item["refs"]["status"], "solid")
        self.assertTrue(
            any("skill-tree.yaml" in p for p in node_item["changed_paths"])
        )

    def test_evidence_flows_traced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            profile = _write_profile(root)
            client = self._client(root, login="openclaw")
            edited = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/edit",
                json={"fields": {"summary": "edited by agent"}},
            )
            self.assertEqual(edited.status_code, 200, edited.text)
            reviewed = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/review",
                json={"action": "accept", "strength": "strong"},
            )
            self.assertEqual(reviewed.status_code, 200, reviewed.text)
            linked = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/skill-links",
                json={"skill_ids": ["ros2_basics"]},
            )
            self.assertEqual(linked.status_code, 200, linked.text)
            items = _writeback_items(profile)

        actions = [item["candidate_type"] for item in items]
        self.assertEqual(
            actions,
            ["evidence.edit", "evidence.review", "evidence.skill_links"],
        )
        self.assertEqual(
            items[-1]["refs"]["skill_ids"], ["ros2_basics"]
        )

    def test_habit_and_plan_and_project_flows_traced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            profile = _write_profile(root)
            client = self._client(root, login="openclaw")
            archived = client.post(
                "/api/v1/profiles/alice/habits/exercise/archive",
                json={"archived": True},
            )
            self.assertEqual(archived.status_code, 200, archived.text)
            template_id = sorted(plan_templates.builtin_template_index())[0]
            plan = client.post(
                "/api/v1/profiles/alice/plan-templates/instantiate",
                json={"template_id": template_id},
            )
            self.assertEqual(plan.status_code, 201, plan.text)
            case_id = plan.json()["case"]["id"]
            saved = client.post(
                f"/api/v1/profiles/alice/project-board/cases/{case_id}/save",
                json={"summary": "agent-maintained plan"},
            )
            self.assertEqual(saved.status_code, 200, saved.text)
            case_archived = client.post(
                f"/api/v1/profiles/alice/project-board/cases/{case_id}/archive"
            )
            self.assertEqual(case_archived.status_code, 200,
                             case_archived.text)
            items = _writeback_items(profile)

        actions = [item["candidate_type"] for item in items]
        self.assertEqual(
            actions,
            [
                "habit.archive",
                "plan_template.instantiate",
                "project_case.save",
                "project_case.archive",
            ],
        )
        plan_item = items[1]
        self.assertEqual(plan_item["refs"]["habit_id"],
                         plan.json()["habit_id"])
        self.assertEqual(
            plan_item["refs"]["project_id"], plan.json()["case"]["id"]
        )

    def test_project_case_delete_and_habit_delete_traced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            profile = _write_profile(root)
            client = self._client(root, login="openclaw")
            created = client.post(
                "/api/v1/profiles/alice/project-board/cases",
                json={"title": "Temp project"},
            )
            self.assertEqual(created.status_code, 201, created.text)
            case_id = created.json()["case"]["id"]
            deleted_case = client.request(
                "DELETE",
                f"/api/v1/profiles/alice/project-board/cases/{case_id}",
                json={"confirm_title": "Temp project"},
            )
            self.assertEqual(deleted_case.status_code, 200,
                             deleted_case.text)
            deleted_habit = client.request(
                "DELETE",
                "/api/v1/profiles/alice/habits/exercise",
                json={"confirm_title": "Exercise"},
            )
            self.assertEqual(deleted_habit.status_code, 200,
                             deleted_habit.text)
            items = _writeback_items(profile)

        actions = [item["candidate_type"] for item in items]
        self.assertEqual(
            actions, ["project_case.delete", "habit.delete"]
        )
        self.assertEqual(items[0]["refs"]["project_id"], case_id)
        self.assertEqual(items[1]["refs"]["checkins_removed"], 1)

    def test_crystallize_apply_traced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            profile = _write_profile(root)
            client = self._client(root, login="openclaw")
            draft = client.post(
                "/api/v1/profiles/alice/crystallize/draft",
                json={"task_ids": ["taskA"]},
            )
            self.assertEqual(draft.status_code, 200, draft.text)
            applied = client.post(
                "/api/v1/profiles/alice/crystallize/apply",
                json={"patch": draft.json()["patch"], "task_ids": ["taskA"]},
            )
            self.assertEqual(applied.status_code, 200, applied.text)
            items = _writeback_items(profile)

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["candidate_type"], "crystallize.apply")
        self.assertEqual(item["refs"]["task_ids"], ["taskA"])
        self.assertEqual(
            item["refs"]["new_evidence_ids"],
            applied.json()["new_evidence_ids"],
        )


class TestNoopDiscipline(AgentWritebackTestBase):
    """G1: mutations that change nothing leave no writeback entry."""

    def test_noop_mutations_not_traced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            profile = _write_profile(root)
            client = self._client(root, login="openclaw")
            # Kanban move to the current section is an idempotent no-op.
            moved = client.post(
                "/api/v1/profiles/alice/kanban/cards/Card One/move",
                json={"target_section": "Queue"},
            )
            self.assertEqual(moved.status_code, 200, moved.text)
            self.assertTrue(moved.json()["warnings"])
            # Habit archive matching the current state writes nothing.
            archived = client.post(
                "/api/v1/profiles/alice/habits/exercise/archive",
                json={"archived": False},
            )
            self.assertEqual(archived.status_code, 200, archived.text)
            self.assertFalse(archived.json()["changed"])
            # North-star patch with the current value is a no-op.
            star = client.patch(
                "/api/v1/profiles/alice/north-star",
                json={"visibility": "private"},
            )
            self.assertEqual(star.status_code, 200, star.text)
            self.assertFalse(star.json()["changed"])
            # Skill node patch to the current rung writes nothing.
            node = client.patch(
                "/api/v1/profiles/alice/skill-tree/nodes/ros2_basics",
                json={"status": "lit"},
            )
            self.assertEqual(node.status_code, 200, node.text)
            self.assertFalse(node.json()["changed"])
            # Rejecting an already-deprecated entry changes nothing.
            rejected = client.post(
                "/api/v1/profiles/alice/evidence/ev_gamma/review",
                json={"action": "reject"},
            )
            self.assertEqual(rejected.status_code, 200, rejected.text)
            self.assertEqual(rejected.json()["changed"], 0)
            items = _writeback_items(profile)

        self.assertEqual(items, [])

    def test_noop_goal_patch_and_skill_links_not_traced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            profile = _write_profile(root)
            client = self._client(root, login="openclaw")
            created = client.post(
                "/api/v1/profiles/alice/goals",
                json={"title": "Keep me", "status": "active"},
            )
            self.assertEqual(created.status_code, 201, created.text)
            goal_id = created.json()["goal"]["id"]
            # Patch with the identical status -> changed=false.
            patched = client.patch(
                f"/api/v1/profiles/alice/goals/{goal_id}",
                json={"status": "active"},
            )
            self.assertEqual(patched.status_code, 200, patched.text)
            self.assertFalse(patched.json()["changed"])
            # Skill-links chip-save with the already-linked set is a no-op.
            linked = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/skill-links",
                json={"skill_ids": ["ros2_basics"]},
            )
            self.assertEqual(linked.status_code, 200, linked.text)
            again = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/skill-links",
                json={"skill_ids": ["ros2_basics"]},
            )
            self.assertEqual(again.status_code, 200, again.text)
            items = _writeback_items(profile)

        # goal.add + the first skill-links change only.
        self.assertEqual(
            [item["candidate_type"] for item in items],
            ["goal.add", "evidence.skill_links"],
        )


class TestNonAgentUsersNotTraced(AgentWritebackTestBase):
    """G1: admin / plain-member mutations produce no writeback entries."""

    def test_admin_mutations_not_traced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            profile = _write_profile(root)
            client = self._client(root, login="admin")
            self.assertEqual(
                client.post(
                    "/api/v1/profiles/alice/checkins",
                    json={"habit": "exercise"},
                ).status_code,
                201,
            )
            self.assertEqual(
                client.post(
                    "/api/v1/profiles/alice/kanban/cards",
                    json={"title": "Admin card"},
                ).status_code,
                201,
            )
            self.assertEqual(
                client.post(
                    "/api/v1/profiles/alice/goals",
                    json={"title": "Admin goal"},
                ).status_code,
                201,
            )
            items = _writeback_items(profile)

        self.assertEqual(items, [])

    def test_member_mutations_not_traced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            profile = _write_profile(root)
            client = self._client(root, login="wang")
            self.assertEqual(
                client.post(
                    "/api/v1/profiles/alice/checkins",
                    json={"habit": "exercise"},
                ).status_code,
                201,
            )
            items = _writeback_items(profile)

        self.assertEqual(items, [])


class TestGitActorPerRequest(unittest.TestCase):
    """G2: record_change observes the request user's id as the actor."""

    def _run_mutation_and_capture_actors(
        self, root: Path, *, login: str | None
    ) -> list[str]:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
            "nblane.core.project_board.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        env: dict[str, str] = {
            "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
        }
        if login is not None:
            env["NBLANE_AUTH_FILE"] = str(
                _write_users_file(root / "users.yaml")
            )
        else:
            env["NBLANE_AUTH_FILE"] = ""
        patcher = patch.dict(os.environ, env)
        self.addCleanup(patcher.stop)
        patcher.start()

        actors: list[str] = []

        def _capture(paths, *, action):
            actors.append(git_backup._actor_var.get())

        patcher = patch(
            "nblane.core.git_backup.record_change", side_effect=_capture
        )
        self.addCleanup(patcher.stop)
        patcher.start()

        client = TestClient(app)
        if login is not None:
            response = client.post(
                "/api/v1/auth/login",
                json={"username": login, "password": PASSWORD},
            )
            self.assertEqual(response.status_code, 200, response.text)
        response = client.post(
            "/api/v1/profiles/alice/checkins", json={"habit": "exercise"}
        )
        self.assertEqual(response.status_code, 201, response.text)
        return actors

    def test_actor_is_openclaw_for_service_account(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            actors = self._run_mutation_and_capture_actors(
                root, login="openclaw"
            )
        self.assertTrue(actors)
        self.assertEqual(set(actors), {"openclaw"})

    def test_actor_is_current_user_for_admin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            actors = self._run_mutation_and_capture_actors(
                root, login="admin"
            )
        self.assertTrue(actors)
        self.assertEqual(set(actors), {"admin"})

    def test_actor_is_local_when_auth_off(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "profiles"
            _write_profile(root)
            actors = self._run_mutation_and_capture_actors(root, login=None)
        self.assertTrue(actors)
        self.assertEqual(set(actors), {"local"})


if __name__ == "__main__":
    unittest.main()
