"""Tests for the Project Board slice (GET aggregation + case/milestone/task mutations).

Covers the board read (cases with milestones/owned tasks/derived range,
summary counters, ref options, ETag header), case create/save/archive with
workspace sync into kanban + evidence pool, milestone add/save/delete,
project-linked kanban task add/move with board re-sync, the AI suggest-refs
endpoint (422 degradation without an LLM backend, mocked success), and the
weak-ETag ``If-Match`` 412 contract. 401/403 auth rules mirror the other
web_api suites.
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
from nblane.core.ai.actions import AIActionResult
from nblane.core.paths import REPO_ROOT
from nblane.web_api import app, create_app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"
PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-project-board-test-secret"

KANBAN_FIXTURE = """# alice · Kanban

## Doing

- [ ] Owned task
  - id: task-owned
  - project_id: project:robot-arm
  - started_on: 2026-09-15

---

## Done

- [x] Done task
  - id: task-done
  - project_id: project:robot-arm
  - milestone_id: milestone:mvp
  - completed_on: 2026-09-16

---

## Queue

- [ ] Free task
  - id: task-free

---

## Someday / Maybe

- (empty)

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
            "kind": "internal",
            "visibility": "private",
            "summary": "Build the arm",
            "goal_refs": ["goal-1"],
            "task_refs": ["task-owned"],
            "evidence_refs": ["ev-1"],
            "milestones": [
                {
                    "id": "milestone:mvp",
                    "title": "MVP",
                    "status": "active",
                    "target": "demo",
                    "date": "2026-10-01",
                    "task_refs": ["task-owned"],
                }
            ],
        },
        {
            "id": "project:old",
            "title": "Old Project",
            "status": "completed",
        },
    ],
}

GOALS_FIXTURE = {
    "schema_version": "1.0",
    "profile": "alice",
    "updated": "2026-09-19",
    "current_goal_id": "goal-1",
    "goals": [
        {"id": "goal-1", "title": "Ship VLA demo", "status": "active"},
    ],
}

EVIDENCE_POOL_FIXTURE = {
    "profile": "alice",
    "updated": "2026-09-19",
    "evidence_entries": [
        {
            "id": "ev-1",
            "title": "Arm demo video",
            "type": "practice",
            "review_status": "reviewed",
            "project_refs": ["project:robot-arm"],
        },
        {
            "id": "ev-2",
            "title": "Loose evidence",
            "type": "practice",
            "review_status": "reviewed",
        },
    ],
}

SOURCES_FIXTURE = {
    "schema_version": "1.0",
    "profile": "alice",
    "updated": "2026-09-19",
    "sources": [
        {"id": "src-1", "title": "VLA survey", "kind": "paper", "status": "inbox"},
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
    (profile / "evidence-pool.yaml").write_text(
        yaml.safe_dump(dict(EVIDENCE_POOL_FIXTURE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "research" / "sources.yaml").write_text(
        yaml.safe_dump(dict(SOURCES_FIXTURE, profile=name), allow_unicode=True),
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
                        "teams": ["example-team"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def _board_yaml(profile: Path) -> dict:
    return yaml.safe_load(
        (profile / "project-board.yaml").read_text(encoding="utf-8")
    )


def _kanban_text(profile: Path) -> str:
    return (profile / "kanban.md").read_text(encoding="utf-8")


class ProjectBoardTestBase(unittest.TestCase):
    """Shared env patching: profile roots plus git-backup isolation.

    Beyond the canonical profile_io/core.io pair, the project-board stack
    binds PROFILES_DIR in ``core.project_board`` and ``core.research_sources``
    (both take plain profile names from the sync helpers), so those module
    globals are patched too.
    """

    def _client(self, root: Path) -> TestClient:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
            "nblane.core.project_board.PROFILES_DIR",
            "nblane.core.research_sources.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch("nblane.core.profile_io.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)


class TestProjectBoardGet(ProjectBoardTestBase):
    """GET /project-board: cases, summary counters, options, ETag."""

    def test_get_board_returns_cases_summary_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/project-board")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["ETag"].startswith('W/"'))
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertEqual(payload["updated"], "2026-09-19")

        cases = {case["id"]: case for case in payload["cases"]}
        self.assertEqual(sorted(cases), ["project:old", "project:robot-arm"])
        arm = cases["project:robot-arm"]
        self.assertEqual(arm["title"], "Robot Arm")
        self.assertEqual(arm["goal_refs"], ["goal-1"])
        self.assertEqual(arm["derived_time_range"], "2026-09-15/2026-09-16")
        # Milestone completion: its only task lives in Doing -> 0/1.
        milestone = arm["milestones"][0]
        self.assertEqual(milestone["id"], "milestone:mvp")
        self.assertEqual(milestone["done_count"], 0)
        self.assertEqual(milestone["total_count"], 1)
        # Owned tasks: live Doing + live Done, sections preserved.
        tasks = {task["id"]: task for task in arm["tasks"]}
        self.assertEqual(sorted(tasks), ["task-done", "task-owned"])
        self.assertEqual(tasks["task-owned"]["section"], "Doing")
        self.assertEqual(tasks["task-done"]["section"], "Done")
        self.assertFalse(tasks["task-done"]["archived"])

        summary = payload["summary"]
        self.assertEqual(summary["status_counts"]["active"], 1)
        self.assertEqual(summary["status_counts"]["completed"], 1)
        # task-free has an id but no project; ev-2 is reviewed without refs.
        self.assertEqual(summary["unassigned_tasks"], 1)
        self.assertEqual(summary["unassigned_evidence"], 1)
        self.assertEqual(summary["current_goal_projects"], 1)

        options = payload["options"]
        self.assertEqual([row["id"] for row in options["goals"]], ["goal-1"])
        task_opts = {row["id"]: row for row in options["tasks"]}
        self.assertEqual(
            sorted(task_opts), ["task-done", "task-free", "task-owned"]
        )
        self.assertEqual(task_opts["task-owned"]["owner"], "project:robot-arm")
        self.assertEqual(task_opts["task-free"]["owner"], "")
        self.assertEqual(
            sorted(row["id"] for row in options["evidence"]), ["ev-1", "ev-2"]
        )
        self.assertEqual([row["id"] for row in options["sources"]], ["src-1"])

    def test_get_empty_board_from_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "alice"
            shutil.copytree(TEMPLATE_DIR, profile)
            for file_path in profile.rglob("*"):
                if file_path.is_file():
                    text = file_path.read_text(encoding="utf-8")
                    text = text.replace("{Name}", "alice")
                    file_path.write_text(text, encoding="utf-8")
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/project-board")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["cases"], [])
        self.assertEqual(payload["summary"]["status_counts"]["active"], 0)

    def test_get_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/nobody/project-board")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "profile_not_found")


class TestProjectCaseMutations(ProjectBoardTestBase):
    """POST cases / save / archive: workspace sync + validation semantics."""

    def test_create_case_201_and_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            before = client.get("/api/v1/profiles/alice/project-board")
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases",
                json={
                    "title": "New Proj",
                    "summary": "fresh",
                    "goal_refs": ["goal-1"],
                },
                headers={"If-Match": before.headers["ETag"]},
            )
            board = _board_yaml(profile)
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload["ok"])
        case = payload["case"]
        self.assertEqual(case["id"], "project:new-proj")
        self.assertEqual(case["status"], "active")
        self.assertEqual(case["goal_refs"], ["goal-1"])
        self.assertNotEqual(response.headers["ETag"], before.headers["ETag"])
        ids = [row["id"] for row in board["project_cases"]]
        self.assertIn("project:new-proj", ids)

    def test_create_case_blank_title_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases",
                json={"title": "   "},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_project_case")

    def test_create_case_duplicate_id_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases",
                json={"title": "Copy", "id": "project:robot-arm"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_project_case")

    def test_create_case_invalid_status_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases",
                json={"title": "Bad status", "status": "flying"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_project_field")

    def test_save_case_updates_fields_and_syncs_kanban(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/save",
                json={
                    "summary": "updated summary",
                    "task_refs": ["task-owned", "task-free"],
                },
            )
            kanban_text = _kanban_text(profile)
            board = _board_yaml(profile)
        self.assertEqual(response.status_code, 200)
        case = response.json()["case"]
        self.assertEqual(case["summary"], "updated summary")
        self.assertEqual(case["title"], "Robot Arm")  # untouched fields kept
        # The sync claims task-free for the project in kanban.md...
        self.assertIn("task-free", case["task_refs"])
        self.assertIn("project_id: project:robot-arm", kanban_text)
        # ...and the persisted board matches.
        stored = {
            row["id"]: row for row in board["project_cases"]
        }["project:robot-arm"]
        self.assertIn("task-free", stored.get("task_refs") or [])

    def test_save_case_unknown_id_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:ghost/save",
                json={"summary": "x"},
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "project_case_not_found")

    def test_save_case_invalid_kind_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/save",
                json={"kind": "galactic"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_project_field")

    def test_archive_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/archive"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["case"]["status"], "archived")

    def test_stale_if_match_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            etag = client.get("/api/v1/profiles/alice/project-board").headers["ETag"]
            first = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/save",
                json={"summary": "first write wins"},
                headers={"If-Match": etag},
            )
            stale = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/save",
                json={"summary": "stale"},
                headers={"If-Match": etag},
            )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(stale.status_code, 412)
        self.assertEqual(stale.json()["code"], "etag_mismatch")
        # The 412 carries a fresh ETag so the client can reload and retry.
        self.assertEqual(stale.headers["ETag"], first.headers["ETag"])


class TestProjectMilestoneMutations(ProjectBoardTestBase):
    """Milestone add/save/delete within a case."""

    def test_add_milestone_201_with_slug_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/milestones",
                json={"title": "Launch", "target": "public demo"},
            )
        self.assertEqual(response.status_code, 201)
        case = response.json()["case"]
        ids = [m["id"] for m in case["milestones"]]
        self.assertEqual(ids, ["milestone:mvp", "milestone:launch"])
        added = case["milestones"][1]
        self.assertEqual(added["title"], "Launch")
        self.assertEqual(added["status"], "planned")
        self.assertEqual(added["target"], "public demo")

    def test_add_milestone_duplicate_id_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/milestones",
                json={"title": "Again", "id": "milestone:mvp"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "duplicate_milestone")

    def test_save_milestone_updates_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm"
                "/milestones/milestone:mvp/save",
                json={"status": "completed", "summary": "shipped"},
            )
            board = _board_yaml(profile)
        self.assertEqual(response.status_code, 200)
        milestone = response.json()["case"]["milestones"][0]
        self.assertEqual(milestone["status"], "completed")
        self.assertEqual(milestone["summary"], "shipped")
        self.assertEqual(milestone["title"], "MVP")  # untouched fields kept
        stored = board["project_cases"][0]["milestones"][0]
        self.assertEqual(stored["status"], "completed")

    def test_save_milestone_unknown_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm"
                "/milestones/milestone:ghost/save",
                json={"title": "x"},
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "project_milestone_not_found")

    def test_delete_milestone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm"
                "/milestones/milestone:mvp/delete"
            )
            board = _board_yaml(profile)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["case"]["milestones"], [])
        self.assertEqual(board["project_cases"][0].get("milestones"), None)


class TestProjectTaskMutations(ProjectBoardTestBase):
    """Project-linked kanban task add/move with board re-sync."""

    def test_add_project_task_201_links_and_syncs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/tasks",
                json={
                    "title": "Wire the gripper",
                    "section": "Queue",
                    "milestone_id": "milestone:mvp",
                    "date": "2026-09-20",
                },
            )
            kanban_text = _kanban_text(profile)
            board = _board_yaml(profile)
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload["ok"])
        card = payload["card"]
        self.assertEqual(card["project_id"], "project:robot-arm")
        self.assertEqual(card["milestone_id"], "milestone:mvp")
        self.assertEqual(card["started_on"], "2026-09-20")
        self.assertTrue(card["id"])
        self.assertIn("Wire the gripper", kanban_text)
        # sync_project_board_from_kanban pulled the new task id into the refs.
        stored = {row["id"]: row for row in board["project_cases"]}[
            "project:robot-arm"
        ]
        self.assertIn(card["id"], stored.get("task_refs") or [])

    def test_add_project_task_unknown_section_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/tasks",
                json={"title": "x", "section": "Limbo"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "unknown_kanban_section")

    def test_add_project_task_unknown_milestone_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/tasks",
                json={"title": "x", "milestone_id": "milestone:ghost"},
            )
            kanban_text = _kanban_text(profile)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "unknown_milestone")
        # Nothing was written.
        self.assertNotIn("> x\n", kanban_text)

    def test_add_project_task_blank_milestone_allowed(self) -> None:
        """An empty milestone_id stays valid (task is just not milestone-linked)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/tasks",
                json={"title": "No milestone", "milestone_id": ""},
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["card"]["milestone_id"], "")

    def test_move_project_task_marks_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/tasks/task-owned/move",
                json={"target_section": "Done"},
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["section"], "Done")
        self.assertTrue(payload["card"]["done"])
        self.assertTrue(payload["card"]["completed_on"])

    def test_move_project_task_unknown_id_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/tasks/task-ghost/move",
                json={"target_section": "Done"},
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "kanban_card_not_found")


class TestProjectSuggestRefs(ProjectBoardTestBase):
    """AI suggest-refs: 422 degradation without LLM, mocked success path."""

    def test_suggest_refs_422_when_backend_fails(self) -> None:
        # No LLM key / unreachable provider surfaces as a structured 422 so
        # the SPA can render a degradation card instead of a hard failure.
        result = AIActionResult(
            ok=False,
            action="project.suggest_refs",
            backend="",
            run_id="run-test",
            error="routing_error: no backend available",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            with patch(
                "nblane.core.project_suggest.run_ai_action", return_value=result
            ):
                response = client.post(
                    "/api/v1/profiles/alice/project-board/cases/project:robot-arm"
                    "/suggest-refs"
                )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "project_suggest_refs_failed")
        self.assertIn("no backend available", response.json()["message"])

    def test_suggest_refs_success_filters_unknown_ids(self) -> None:
        result = AIActionResult(
            ok=True,
            action="project.suggest_refs",
            backend="fake",
            run_id="run-test",
            structured={
                "goal_refs": ["goal-1", "goal-ghost"],
                "task_refs": ["task-free"],
                "evidence_refs": ["ev-2"],
                "source_refs": [],
                "output_refs": [],
                "rationale": "closest matches",
                "warnings": ["low confidence"],
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            with patch(
                "nblane.core.project_suggest.run_ai_action", return_value=result
            ):
                response = client.post(
                    "/api/v1/profiles/alice/project-board/cases/project:robot-arm"
                    "/suggest-refs"
                )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["backend"], "fake")
        # goal-ghost is not a real option row and is dropped.
        self.assertEqual(payload["suggestions"]["goal_refs"], ["goal-1"])
        self.assertEqual(payload["suggestions"]["task_refs"], ["task-free"])
        self.assertEqual(payload["suggestions"]["evidence_refs"], ["ev-2"])
        self.assertEqual(payload["rationale"], "closest matches")
        self.assertIn("low confidence", payload["warnings"])

    def test_suggest_refs_unknown_case_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:ghost/suggest-refs"
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "project_case_not_found")


class TestProjectBoardScope(ProjectBoardTestBase):
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
            "nblane.core.research_sources.PROFILES_DIR",
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
            listing = client.get("/api/v1/profiles/alice/project-board")
            create = client.post(
                "/api/v1/profiles/alice/project-board/cases",
                json={"title": "x"},
            )
            suggest = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm"
                "/suggest-refs"
            )
        self.assertEqual(listing.status_code, 401)
        self.assertEqual(create.status_code, 401)
        self.assertEqual(suggest.status_code, 401)

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
            forbidden = client.get("/api/v1/profiles/alice/project-board")
            forbidden_save = client.post(
                "/api/v1/profiles/alice/project-board/cases/project:robot-arm/save",
                json={"summary": "x"},
            )
            allowed = client.get("/api/v1/profiles/wang/project-board")
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.json()["code"], "profile_forbidden")
        self.assertEqual(forbidden_save.status_code, 403)
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["profile"], "wang")


if __name__ == "__main__":
    unittest.main()
