"""Tests for the web_api async-jobs slice (jobs registry + SSE + LLM kinds).

Covers ``POST /profiles/{name}/jobs``, ``GET .../jobs/{job_id}``, and
``GET .../jobs/{job_id}/stream`` (SSE), plus the registered
``project-suggest-refs`` kind (Project Board AI ref suggestion). Registry/SSE mechanics run on a
synthetic ``test-echo`` kind. The gateway / core LLM entry points are
always patched — tests never touch the network or the real ``.env`` key.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.core.ai.actions import AIActionResult
from nblane.web_api import app, create_app
from nblane.web_api import jobs as jobs_module

PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-jobs-test-secret"

SCHEMA = {
    "schema_version": "1.0",
    "domain": "Test Domain",
    "nodes": [
        {"id": "robotics", "label": "Robotics", "level": 1},
        {
            "id": "manipulation",
            "label": "Manipulation",
            "level": 2,
            "requires": ["robotics"],
            "keywords": ["grasp"],
        },
        {
            "id": "navigation",
            "label": "Navigation",
            "level": 2,
            "requires": ["robotics"],
        },
    ],
}

SKILL_TREE = {
    "profile": "alice",
    "schema": "test-domain",
    "updated": "2026-09-10",
    "nodes": [
        {"id": "robotics", "status": "solid"},
        {"id": "manipulation", "status": "learning"},
        {"id": "navigation", "status": "locked"},
    ],
}

EVIDENCE_POOL = {
    "profile": "alice",
    "evidence_entries": [
        {"id": "ev_one", "type": "project", "title": "Demo"},
    ],
}


def _write_profile(root: Path, name: str = "alice", tree: dict | None = None) -> Path:
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    if tree is not None:
        data = dict(tree)
        data["profile"] = name
        (profile / "skill-tree.yaml").write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    (profile / "evidence-pool.yaml").write_text(
        yaml.safe_dump(dict(EVIDENCE_POOL, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    return profile


def _write_schemas(root: Path) -> Path:
    schemas = root / "schemas"
    schemas.mkdir(parents=True)
    (schemas / "test-domain.yaml").write_text(
        yaml.safe_dump(SCHEMA, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return schemas


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
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def _read_sse_frames(response) -> list[tuple[str, dict]]:
    """Parse an SSE response body into ``(event, data)`` frames."""
    frames: list[tuple[str, dict]] = []
    event: str | None = None
    data_lines: list[str] = []
    for line in response.iter_lines():
        if line == "":
            if event is not None:
                frames.append((event, json.loads("".join(data_lines))))
            event, data_lines = None, []
            continue
        if line.startswith("event: "):
            event = line[len("event: "):]
        elif line.startswith("data: "):
            data_lines.append(line[len("data: "):])
    return frames


class JobsTestBase(unittest.TestCase):
    """Shared env patching: profile/schema roots plus learned-keyword isolation."""

    def _patch_roots(self, root: Path, schemas: Path) -> None:
        for target, value in (
            ("nblane.core.profile_io.PROFILES_DIR", root),
            ("nblane.core.io.PROFILES_DIR", root),
            ("nblane.core.io.SCHEMAS_DIR", schemas),
            ("nblane.core.project_board.PROFILES_DIR", root),
        ):
            patcher = patch(target, value)
            self.addCleanup(patcher.stop)
            patcher.start()

    def _client(self, root: Path, schemas: Path) -> TestClient:
        self._patch_roots(root, schemas)
        self._register_echo_kind()
        return TestClient(app)

    def _register_echo_kind(self) -> None:
        """Register ``test-echo``: two progress phases, fails on task "fail"."""

        def validate(job_input: dict) -> dict:
            task = str(job_input.get("task") or "").strip()
            if not task:
                raise jobs_module.JobInputError("empty_task", "Empty task text.")
            return {"task": task}

        def run(profile, job_input, report):
            report(phase="routing", message="Routing.")
            report(phase="merging", message="Merging.")
            if job_input["task"] == "fail":
                raise jobs_module.JobFailedError("no_roots", "Nothing matched.")
            return {"profile": profile, "task": job_input["task"]}

        spec = jobs_module.JobKind(name="test-echo", validate=validate, run=run)
        patcher = patch.dict(jobs_module._KINDS, {"test-echo": spec})
        self.addCleanup(patcher.stop)
        patcher.start()

    def _wait_final(
        self, client: TestClient, job_id: str, name: str = "alice", timeout: float = 10.0
    ) -> dict:
        """Poll the status endpoint until the job reaches a final status."""
        deadline = time.monotonic() + timeout
        while True:
            response = client.get(f"/api/v1/profiles/{name}/jobs/{job_id}")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            if payload["job"]["status"] in jobs_module.FINAL_STATUSES:
                return payload
            if time.monotonic() > deadline:
                self.fail(f"job {job_id} did not finish within {timeout}s")
            time.sleep(0.05)


class TestJobCreation(JobsTestBase):
    """POST /profiles/{name}/jobs — validation and dispatch."""

    def test_unknown_kind_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "nope", "input": {}},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "unknown_job_kind")

    def test_blank_task_422_empty_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-echo", "input": {"task": "   "}},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "empty_task")

    def test_job_status_unknown_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            status = client.get("/api/v1/profiles/alice/jobs/job-doesnotexist")
            stream = client.get(
                "/api/v1/profiles/alice/jobs/job-doesnotexist/stream"
            )
        self.assertEqual(status.status_code, 404)
        self.assertEqual(status.json()["code"], "job_not_found")
        self.assertEqual(stream.status_code, 404)
        self.assertEqual(stream.json()["code"], "job_not_found")

    def test_job_of_other_profile_404(self) -> None:
        """Job ids cannot be polled/streamed through another profile's path."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, "alice", SKILL_TREE)
            _write_profile(root, "wang", SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            created = client.post(
                "/api/v1/profiles/alice/jobs",
                json={
                    "kind": "test-echo",
                    "input": {"task": "grasp manipulation"},
                },
            )
            self.assertEqual(created.status_code, 202)
            job_id = created.json()["job_id"]
            self._wait_final(client, job_id)
            status = client.get(f"/api/v1/profiles/wang/jobs/{job_id}")
            stream = client.get(f"/api/v1/profiles/wang/jobs/{job_id}/stream")
        self.assertEqual(status.status_code, 404)
        self.assertEqual(status.json()["code"], "job_not_found")
        self.assertEqual(stream.status_code, 404)
        self.assertEqual(stream.json()["code"], "job_not_found")


class TestJobStream(JobsTestBase):
    """SSE stream: initial snapshot, replayed progress, terminal frame."""

    def test_stream_is_not_gzipped(self) -> None:
        """GZipMiddleware must pass text/event-stream through uncompressed."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            created = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-echo", "input": {"task": "grasp"}},
            )
            self.assertEqual(created.status_code, 202)
            job_id = created.json()["job_id"]
            self._wait_final(client, job_id)
            with client.stream(
                "GET",
                f"/api/v1/profiles/alice/jobs/{job_id}/stream",
                headers={"Accept-Encoding": "gzip"},
            ) as response:
                self.assertEqual(response.status_code, 200)
                self.assertNotEqual(response.headers.get("content-encoding"), "gzip")
                frames = _read_sse_frames(response)
        self.assertEqual(frames[0][0], "job")
        self.assertEqual(frames[-1][0], "done")

    def test_stream_done_replays_progress_phases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            created = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-echo", "input": {"task": "grasp"}},
            )
            self.assertEqual(created.status_code, 202)
            job_id = created.json()["job_id"]
            self._wait_final(client, job_id)
            with client.stream(
                "GET", f"/api/v1/profiles/alice/jobs/{job_id}/stream"
            ) as response:
                self.assertEqual(response.status_code, 200)
                self.assertTrue(
                    response.headers["content-type"].startswith(
                        "text/event-stream"
                    )
                )
                frames = _read_sse_frames(response)
        kinds = [event for event, _ in frames]
        self.assertEqual(kinds[0], "job")
        self.assertEqual(kinds[-1], "done")
        self.assertIn("progress", kinds)
        phases = [
            data["event"]["phase"]
            for event, data in frames
            if event == "progress"
        ]
        # Runner-reported stages survive even when the subscriber connects
        # after the job already finished (seq-log replay).
        self.assertIn("routing", phases)
        self.assertIn("merging", phases)
        done = frames[-1][1]
        self.assertTrue(done["ok"])
        self.assertEqual(done["job"]["status"], "done")
        self.assertEqual(done["result"]["task"], "grasp")

    def test_stream_terminal_error_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            created = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-echo", "input": {"task": "fail"}},
            )
            self.assertEqual(created.status_code, 202)
            job_id = created.json()["job_id"]
            self._wait_final(client, job_id)
            with client.stream(
                "GET", f"/api/v1/profiles/alice/jobs/{job_id}/stream"
            ) as response:
                frames = _read_sse_frames(response)
        self.assertEqual(frames[-1][0], "error")
        payload = frames[-1][1]
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "no_roots")
        self.assertEqual(payload["job"]["status"], "failed")

    def test_stream_delivers_progress_incrementally(self) -> None:
        """A subscriber connected mid-flight sees phases as they happen."""

        def runner(profile, job_input, report):
            report(phase="one", message="First stage.")
            time.sleep(0.4)
            report(phase="two", message="Second stage.")
            return {"ok": True}

        spec = jobs_module.JobKind(
            name="test-slow",
            validate=lambda job_input: dict(job_input),
            run=runner,
        )
        patcher = patch.dict(jobs_module._KINDS, {"test-slow": spec})
        self.addCleanup(patcher.stop)
        patcher.start()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            created = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-slow", "input": {}},
            )
            self.assertEqual(created.status_code, 202)
            job_id = created.json()["job_id"]
            # Connect immediately: the two phases must arrive as separate
            # frames while the job is still running, followed by done.
            with client.stream(
                "GET", f"/api/v1/profiles/alice/jobs/{job_id}/stream"
            ) as response:
                frames = _read_sse_frames(response)
        kinds = [event for event, _ in frames]
        self.assertEqual(kinds[0], "job")
        self.assertEqual(kinds[-1], "done")
        phases = [
            data["event"]["phase"]
            for event, data in frames
            if event == "progress"
        ]
        self.assertEqual(phases, ["one", "two"])
        seqs = [
            data["event"]["seq"]
            for event, data in frames
            if event == "progress"
        ]
        self.assertEqual(seqs, sorted(seqs))


class TestJobRunnerFailures(JobsTestBase):
    """Registry-level failure semantics with a synthetic test kind."""

    def _register_kind(self, name: str, runner) -> None:
        spec = jobs_module.JobKind(
            name=name,
            validate=lambda job_input: dict(job_input),
            run=runner,
        )
        patcher = patch.dict(jobs_module._KINDS, {name: spec})
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_runner_exception_fails_with_job_failed(self) -> None:
        def runner(profile, job_input, report):
            raise RuntimeError("boom")

        self._register_kind("test-explode", runner)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            created = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-explode", "input": {}},
            )
            self.assertEqual(created.status_code, 202)
            final = self._wait_final(client, created.json()["job_id"])
        self.assertEqual(final["job"]["status"], "failed")
        self.assertEqual(final["job"]["error"]["code"], "job_failed")
        self.assertEqual(final["job"]["error"]["message"], "boom")

    def test_watchdog_marks_hung_job_failed(self) -> None:
        def runner(profile, job_input, report):
            time.sleep(1.0)
            return {"too": "late"}

        self._register_kind("test-hang", runner)
        patcher = patch.object(jobs_module, "_JOB_TIMEOUT_SECONDS", 0.2)
        self.addCleanup(patcher.stop)
        patcher.start()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            created = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-hang", "input": {}},
            )
            self.assertEqual(created.status_code, 202)
            final = self._wait_final(client, created.json()["job_id"])
        self.assertEqual(final["job"]["status"], "failed")
        self.assertEqual(final["job"]["error"]["code"], "job_timeout")
        # The late runner result is discarded, never reported as done.
        self.assertIsNone(final["result"])


class TestJobsScope(JobsTestBase):
    """401/403 enforcement under auth-on for all three job endpoints."""

    def _auth_client(self, root: Path, schemas: Path) -> TestClient:
        self._patch_roots(root, schemas)
        self._register_echo_kind()
        users_file = _write_users_file(root / "users.yaml")
        env = {
            "NBLANE_AUTH_FILE": str(users_file),
            "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
        }
        patcher = patch.dict(os.environ, env)
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(create_app())

    def test_unauthenticated_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._auth_client(root, schemas)
            create = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-echo", "input": {"task": "grasp"}},
            )
            status = client.get("/api/v1/profiles/alice/jobs/job-x")
            stream = client.get("/api/v1/profiles/alice/jobs/job-x/stream")
        self.assertEqual(create.status_code, 401)
        self.assertEqual(status.status_code, 401)
        self.assertEqual(stream.status_code, 401)

    def test_member_forbidden_from_other_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, "alice", SKILL_TREE)
            _write_profile(root, "wang", SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._auth_client(root, schemas)
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            create = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-echo", "input": {"task": "grasp"}},
            )
            status = client.get("/api/v1/profiles/alice/jobs/job-x")
            stream = client.get("/api/v1/profiles/alice/jobs/job-x/stream")
            # Member may still run jobs on their own profile.
            own = client.post(
                "/api/v1/profiles/wang/jobs",
                json={"kind": "test-echo", "input": {"task": "grasp"}},
            )
            self.assertEqual(own.status_code, 202)
            self._wait_final(client, own.json()["job_id"], name="wang")
        self.assertEqual(create.status_code, 403)
        self.assertEqual(create.json()["code"], "profile_forbidden")
        self.assertEqual(status.status_code, 403)
        self.assertEqual(stream.status_code, 403)


SUGGEST_KANBAN = """# alice · Kanban

## Doing

- [ ] Owned task
  - id: task-owned
  - project_id: project:robot-arm

---

## Done

- (empty)

---

## Queue

- [ ] Free task
  - id: task-free

---

## Someday / Maybe

- (empty)

---
"""

SUGGEST_BOARD = {
    "schema_version": "1.0",
    "updated": "2026-09-19",
    "project_cases": [
        {
            "id": "project:robot-arm",
            "title": "Robot Arm",
            "status": "active",
            "kind": "internal",
            "visibility": "private",
            "summary": "Build the arm",
        },
    ],
}

SUGGEST_GOALS = {
    "schema_version": "1.0",
    "updated": "2026-09-19",
    "current_goal_id": "goal-1",
    "goals": [
        {"id": "goal-1", "title": "Ship VLA demo", "status": "active"},
    ],
}


def _write_board_profile(root: Path, name: str = "alice") -> Path:
    """Profile fixture with a project case, kanban tasks, and one goal."""
    profile = _write_profile(root, name, SKILL_TREE)
    (profile / "kanban.md").write_text(SUGGEST_KANBAN, encoding="utf-8")
    (profile / "project-board.yaml").write_text(
        yaml.safe_dump(dict(SUGGEST_BOARD, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "goals.yaml").write_text(
        yaml.safe_dump(dict(SUGGEST_GOALS, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    return profile


class TestProjectSuggestRefsJob(JobsTestBase):
    """The project-suggest-refs kind: lifecycle and failure mapping.

    The gateway action is patched (``core.project_suggest.run_ai_action``)
    so tests never touch the network or the Agent Activity writers.
    """

    def _patch_action(self, result: AIActionResult) -> None:
        patcher = patch(
            "nblane.core.project_suggest.run_ai_action", return_value=result
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    def _create(self, client: TestClient, case_id: str):
        return client.post(
            "/api/v1/profiles/alice/jobs",
            json={"kind": "project-suggest-refs", "input": {"case_id": case_id}},
        )

    def test_success_filters_unknown_ids_and_streams_phases(self) -> None:
        result = AIActionResult(
            ok=True,
            action="project.suggest_refs",
            backend="fake",
            run_id="run-test",
            structured={
                "goal_refs": ["goal-1", "goal-ghost"],
                "task_refs": ["task-free", "task-ghost"],
                "evidence_refs": ["ev_one"],
                "source_refs": [],
                "output_refs": [],
                "rationale": "closest matches",
                "warnings": ["low confidence"],
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_board_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_action(result)
            created = self._create(client, "project:robot-arm")
            self.assertEqual(created.status_code, 202)
            job = created.json()["job"]
            self.assertEqual(job["kind"], "project-suggest-refs")
            job_id = created.json()["job_id"]
            final = self._wait_final(client, job_id)
            with client.stream(
                "GET", f"/api/v1/profiles/alice/jobs/{job_id}/stream"
            ) as response:
                frames = _read_sse_frames(response)
        self.assertEqual(final["job"]["status"], "done")
        payload = final["result"]
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["backend"], "fake")
        # Unknown ids are dropped against the real option rows.
        self.assertEqual(payload["suggestions"]["goal_refs"], ["goal-1"])
        self.assertEqual(payload["suggestions"]["task_refs"], ["task-free"])
        self.assertEqual(payload["suggestions"]["evidence_refs"], ["ev_one"])
        self.assertEqual(payload["rationale"], "closest matches")
        self.assertIn("low confidence", payload["warnings"])
        phases = [
            data["event"]["phase"] for event, data in frames if event == "progress"
        ]
        self.assertEqual(phases, ["collecting", "suggesting"])
        self.assertEqual(frames[-1][0], "done")

    def test_backend_failure_fails_structured(self) -> None:
        result = AIActionResult(
            ok=False,
            action="project.suggest_refs",
            backend="",
            run_id="run-test",
            error="routing_error: no backend available",
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_board_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_action(result)
            created = self._create(client, "project:robot-arm")
            self.assertEqual(created.status_code, 202)
            job_id = created.json()["job_id"]
            final = self._wait_final(client, job_id)
            with client.stream(
                "GET", f"/api/v1/profiles/alice/jobs/{job_id}/stream"
            ) as response:
                frames = _read_sse_frames(response)
        job = final["job"]
        self.assertEqual(job["status"], "failed")
        # Same code as the sync endpoint's 422 — same degradation card.
        self.assertEqual(job["error"]["code"], "project_suggest_refs_failed")
        self.assertIn("no backend available", job["error"]["message"])
        self.assertIsNone(final["result"])
        self.assertEqual(frames[-1][0], "error")
        self.assertEqual(
            frames[-1][1]["error"]["code"], "project_suggest_refs_failed"
        )

    def test_unknown_case_fails_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_board_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            created = self._create(client, "project:ghost")
            self.assertEqual(created.status_code, 202)
            final = self._wait_final(client, created.json()["job_id"])
        self.assertEqual(final["job"]["status"], "failed")
        self.assertEqual(final["job"]["error"]["code"], "project_case_not_found")

    def test_blank_case_id_422_at_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_board_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = self._create(client, "   ")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "empty_case_id")


class TestNewKindsScope(JobsTestBase):
    """LLM kinds ride the same auth-guarded generic endpoints."""

    def test_new_kinds_unauthenticated_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            users_file = _write_users_file(root / "users.yaml")
            env = {
                "NBLANE_AUTH_FILE": str(users_file),
                "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
            }
            patcher = patch.dict(os.environ, env)
            self.addCleanup(patcher.stop)
            patcher.start()
            client = TestClient(create_app())
            suggest = client.post(
                "/api/v1/profiles/alice/jobs",
                json={
                    "kind": "project-suggest-refs",
                    "input": {"case_id": "project:robot-arm"},
                },
            )
        self.assertEqual(suggest.status_code, 401)


class TestCrystallizeJobKind(unittest.TestCase):
    """evidence-crystallize: kind timeout, friendly errors, LLM cap."""

    def test_kind_timeout_overrides_global(self) -> None:
        spec = jobs_module._KINDS[jobs_module.KIND_EVIDENCE_CRYSTALLIZE]
        self.assertEqual(spec.timeout_seconds, 120.0)
        job = {"kind": jobs_module.KIND_EVIDENCE_CRYSTALLIZE}
        self.assertEqual(jobs_module._job_timeout(job), 120.0)
        # Unknown / unset kinds keep the global default.
        self.assertEqual(
            jobs_module._job_timeout({"kind": "nope"}),
            float(jobs_module._JOB_TIMEOUT_SECONDS),
        )

    def test_friendly_error_mapping(self) -> None:
        friendly = jobs_module._crystallize_friendly_error
        self.assertIn("未配置 LLM", friendly("AI features not configured"))
        self.assertIn("未配置 LLM", friendly("LLM not configured"))
        self.assertIn("超时", friendly("LLM error: request timed out"))
        self.assertIn("无法解析", friendly("Could not parse ingest JSON from LLM."))
        self.assertIn("boom", friendly("LLM error: boom"))
        self.assertIn("规则草稿", friendly("LLM error: boom"))

    def test_friendly_error_distinguishes_provider_and_schema_failures(self) -> None:
        friendly = jobs_module._crystallize_friendly_error
        provider = friendly("provider_error: LLM error: HTTP 503")
        schema = friendly("crystallize_schema_error: $.evidence_entries is required")
        codex_json = friendly("codex_json_error: response did not contain a JSON object")
        self.assertIn("后端调用失败", provider)
        self.assertIn("HTTP 503", provider)
        self.assertIn("格式不符合结晶协议", schema)
        self.assertIn("格式不符合结晶协议", codex_json)

    def test_friendly_error_names_entry_missing_source(self) -> None:
        friendly = jobs_module._crystallize_friendly_error
        text = friendly("crystallize_schema_error: $.evidence_entries[2].source_task_id is required")
        self.assertIn("第 3 条证据", text)
        self.assertIn("来自哪个任务", text)
        self.assertIn("规则草稿", text)

    def test_runner_fails_when_selected_ai_backend_is_unavailable(self) -> None:
        """A missing selected backend fails; no implicit rule fallback occurs."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            from nblane.core.kanban_io import render_kanban
            from nblane.core.models import KanbanTask

            (profile / "kanban.md").write_text(
                render_kanban(
                    "alice",
                    {"Done": [KanbanTask(title="t", id="taskA", done=True)]},
                ),
                encoding="utf-8",
            )
            from nblane.core.ai.actions import AIActionResult

            with patch(
                "nblane.core.profile_io.PROFILES_DIR", root
            ), patch("nblane.core.io.PROFILES_DIR", root):
                with patch(
                    "nblane.core.ai.gateway.crystallize_done_tasks",
                    return_value=AIActionResult(
                        ok=False,
                        action="evidence.crystallize",
                        backend="direct_llm",
                        run_id="run-test",
                        error="ai_not_configured: LLM_API_KEY is not configured",
                    ),
                ):
                    try:
                        jobs_module._run_evidence_crystallize(
                            "alice", {"task_ids": ["taskA"], "titles": []}, lambda **kw: None
                        )
                        self.fail("expected JobFailedError")
                    except jobs_module.JobFailedError as exc:
                        self.assertEqual(exc.code, "crystallize_draft_failed")
                        self.assertIn("规则草稿", exc.message)

    def test_runner_uses_codex_backend_selected_in_profile_settings(self) -> None:
        """The returned backend reflects the configured Codex action."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            from nblane.core.kanban_io import render_kanban
            from nblane.core.models import KanbanTask

            (profile / "kanban.md").write_text(
                render_kanban(
                    "alice",
                    {
                        "Done": [
                            KanbanTask(
                                title="t", id="taskA", done=True,
                                completed_on="2026-01-02",
                            )
                        ]
                    },
                ),
                encoding="utf-8",
            )
            with patch(
                "nblane.core.profile_io.PROFILES_DIR", root
            ), patch("nblane.core.io.PROFILES_DIR", root), patch(
                "nblane.core.ai.gateway.crystallize_done_tasks",
                return_value=AIActionResult(
                    ok=True,
                    action="evidence.crystallize",
                    backend="local_codex_readonly",
                    run_id="run-test",
                    structured={"evidence_entries": [], "node_updates": []},
                ),
            ):
                result = jobs_module._run_evidence_crystallize(
                    "alice", {"task_ids": ["taskA"], "titles": []}, lambda **kw: None
                )
            self.assertEqual(result["backend"], "codex")

    def test_runner_passes_90s_timeout_to_gateway(self) -> None:
        """The wizard caps its action call at 90s, below job timeout."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            from nblane.core.kanban_io import render_kanban
            from nblane.core.models import KanbanTask

            (profile / "kanban.md").write_text(
                render_kanban(
                    "alice",
                    {
                        "Done": [
                            KanbanTask(
                                title="t", id="taskA", done=True,
                                completed_on="2026-01-02",
                            )
                        ]
                    },
                ),
                encoding="utf-8",
            )
            with patch(
                "nblane.core.profile_io.PROFILES_DIR", root
            ), patch("nblane.core.io.PROFILES_DIR", root), patch(
                "nblane.core.ai.gateway.crystallize_done_tasks",
                return_value=AIActionResult(
                    ok=True,
                    action="evidence.crystallize",
                    backend="direct_llm",
                    run_id="run-test",
                    structured={"evidence_entries": [], "node_updates": []},
                ),
            ) as run:
                jobs_module._run_evidence_crystallize(
                    "alice", {"task_ids": ["taskA"], "titles": []}, lambda **kw: None
                )
            self.assertEqual(run.call_args.kwargs["timeout_seconds"], 90.0)


    def test_runner_generates_each_selected_task_independently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            from nblane.core.kanban_io import render_kanban
            from nblane.core.models import KanbanTask

            tasks = [
                KanbanTask(title="task-a", id="taskA", done=True, outcome="result-a"),
                KanbanTask(title="task-b", id="taskB", done=True, outcome="result-b"),
            ]
            (profile / "kanban.md").write_text(
                render_kanban("alice", {"Done": tasks}), encoding="utf-8"
            )
            calls = []

            def fake_crystallize(_profile, selected, **kwargs):
                task = selected[0]
                calls.append((task.id, kwargs))
                return AIActionResult(
                    ok=True,
                    action="evidence.crystallize",
                    backend="direct_llm",
                    run_id=f"run-{task.id}",
                    structured={
                        "evidence_entries": [
                            {"title": task.title, "source_task_id": task.id}
                        ],
                        "node_updates": [],
                    },
                )

            with patch("nblane.core.profile_io.PROFILES_DIR", root), patch(
                "nblane.core.io.PROFILES_DIR", root
            ), patch(
                "nblane.core.ai.gateway.crystallize_done_tasks",
                side_effect=fake_crystallize,
            ) as run:
                messages = []
                result = jobs_module._run_evidence_crystallize(
                    "alice",
                    {"task_ids": ["taskA", "taskB"], "titles": []},
                    lambda **kw: messages.append(kw["message"]),
                )
            self.assertEqual([call[0] for call in calls], ["taskA", "taskB"])
            self.assertEqual(run.call_count, 2)
            for _task_id, kwargs in calls:
                self.assertEqual(kwargs["timeout_seconds"], 90.0)
                self.assertEqual(kwargs["max_retries"], 0)
            rows = result["patch"]["evidence_entries"]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["kanban_refs"], ["kanban:taskA"])
            self.assertEqual(rows[1]["kanban_refs"], ["kanban:taskB"])
            self.assertIn("task-a", rows[0]["original_content"])
            self.assertIn("result-a", rows[0]["original_content"])
            self.assertIn("task-b", rows[1]["original_content"])
            self.assertIn("result-b", rows[1]["original_content"])
            self.assertEqual(rows[0]["origin_ref"], "kanban:taskA")
            self.assertEqual(rows[1]["origin_ref"], "kanban:taskB")
            self.assertTrue(any("第 1/2" in message for message in messages))
            self.assertTrue(any("第 2/2" in message for message in messages))

    def test_runner_stops_before_another_task_has_wrong_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            from nblane.core.kanban_io import render_kanban
            from nblane.core.models import KanbanTask

            tasks = [
                KanbanTask(title="task-a", id="taskA", done=True),
                KanbanTask(title="task-b", id="taskB", done=True),
            ]
            (profile / "kanban.md").write_text(
                render_kanban("alice", {"Done": tasks}), encoding="utf-8"
            )
            with patch("nblane.core.profile_io.PROFILES_DIR", root), patch(
                "nblane.core.io.PROFILES_DIR", root
            ), patch(
                "nblane.core.ai.gateway.crystallize_done_tasks",
                return_value=AIActionResult(
                    ok=True,
                    action="evidence.crystallize",
                    backend="direct_llm",
                    run_id="run-wrong-source",
                    structured={
                        "evidence_entries": [
                            {"title": "wrong source", "source_task_id": "taskB"}
                        ],
                        "node_updates": [],
                    },
                ),
            ) as run:
                with self.assertRaises(jobs_module.JobFailedError) as caught:
                    jobs_module._run_evidence_crystallize(
                        "alice", {"task_ids": ["taskA", "taskB"], "titles": []}, lambda **kw: None
                    )
            self.assertEqual(caught.exception.code, "crystallize_draft_failed")
            self.assertIn("task-a", caught.exception.message)
            self.assertEqual(run.call_count, 1)

    def test_gateway_forwards_zero_retries_to_llm(self) -> None:
        from nblane.core.ai.gateway import crystallize_done_tasks
        from nblane.core.models import KanbanTask

        with patch("nblane.core.ai.gateway.run_ai_action") as run:
            crystallize_done_tasks(
                "alice",
                [KanbanTask(title="task-a", id="taskA", done=True)],
                timeout_seconds=90,
                max_retries=0,
            )
        self.assertEqual(run.call_args.args[1]["llm_max_retries"], 0)

    def test_job_records_task_count_for_timeout(self) -> None:
        with patch.object(
            jobs_module._KINDS[jobs_module.KIND_EVIDENCE_CRYSTALLIZE],
            "run",
            return_value={"ok": True},
        ):
            snapshot = jobs_module.create_job(
                "alice",
                jobs_module.KIND_EVIDENCE_CRYSTALLIZE,
                {"task_ids": ["taskA", "taskB"], "titles": []},
            )
        job = jobs_module._JOBS[snapshot["job_id"]]
        self.assertEqual(job["_task_count"], 2)
        self.assertEqual(jobs_module._job_timeout(job), 180.0)
        job["status"] = "running"
        job["started_at"] = time.time() - 181
        jobs_module._mark_timeout_locked(snapshot["job_id"], time.time())
        self.assertIn("180 秒", job["_cancel_message"])


if __name__ == "__main__":
    unittest.main()


class TestJobCancel(JobsTestBase):
    """DELETE requests a stop; only the worker publishes the real terminal state."""

    def _register_slow(self, gate: "threading.Event") -> None:
        def runner(profile, job_input, report):
            gate.wait(5)
            return {"too": "late"}

        spec = jobs_module.JobKind(name="test-slow", validate=lambda job_input: dict(job_input), run=runner)
        patcher = patch.dict(jobs_module._KINDS, {"test-slow": spec})
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_cancel_running_job_waits_for_worker_and_drops_result(self) -> None:
        import threading

        gate = threading.Event()
        self.addCleanup(gate.set)
        self._register_slow(gate)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            job_id = client.post("/api/v1/profiles/alice/jobs", json={"kind": "test-slow", "input": {}}).json()["job_id"]
            cancelled = client.delete(f"/api/v1/profiles/alice/jobs/{job_id}")
            self.assertEqual(cancelled.status_code, 200)
            self.assertEqual(cancelled.json()["job"]["status"], "running")
            self.assertTrue(cancelled.json()["job"]["cancel_requested"])
            self.assertIsNone(cancelled.json()["job"]["error"])
            gate.set()
            final = self._wait_final(client, job_id)
            again = client.delete(f"/api/v1/profiles/alice/jobs/{job_id}")
        self.assertEqual(final["job"]["error"]["code"], "job_cancelled")
        self.assertIsNone(final["result"])
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json()["job"]["error"]["code"], "job_cancelled")

    def test_cancel_unknown_job_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.delete("/api/v1/profiles/alice/jobs/job-missing")
        self.assertEqual(response.status_code, 404)


class TestJobCommitBoundaries(JobsTestBase):
    def _register_commit_kind(self, name: str, runner, *, timeout: float = 0.0) -> None:
        spec = jobs_module.JobKind(
            name=name,
            validate=lambda job_input: dict(job_input),
            run=runner,
            effect="write",
            action="research_source.patch",
            context_runner=True,
            timeout_seconds=timeout,
        )
        patcher = patch.dict(jobs_module._KINDS, {name: spec})
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_cancel_before_commit_never_writes(self) -> None:
        import threading

        started = threading.Event()
        release = threading.Event()
        self.addCleanup(release.set)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            profile = _write_profile(root, tree=SKILL_TREE)
            target = profile / "late-commit.txt"

            def runner(_profile, _job_input, _report, ctx):
                started.set()
                release.wait(5)
                ctx.apply(lambda: target.write_text("late", encoding="utf-8"))

            self._register_commit_kind("test-cancel-before-commit", runner)
            client = self._client(root, _write_schemas(base))
            job_id = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-cancel-before-commit", "input": {}},
            ).json()["job_id"]
            self.assertTrue(started.wait(2))
            stopped = client.delete(f"/api/v1/profiles/alice/jobs/{job_id}")
            self.assertEqual(stopped.json()["job"]["status"], "running")
            release.set()
            final = self._wait_final(client, job_id)
            target_exists = target.exists()

        self.assertEqual(final["job"]["error"]["code"], "job_cancelled")
        self.assertFalse(final["job"]["write_committed"])
        self.assertFalse(target_exists)

    def test_cancel_during_commit_finishes_segment_and_reports_partial_write(self) -> None:
        import threading

        committing = threading.Event()
        release = threading.Event()
        self.addCleanup(release.set)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            profile = _write_profile(root, tree=SKILL_TREE)
            target = profile / "committed.txt"

            def runner(_profile, _job_input, _report, ctx):
                def commit():
                    committing.set()
                    release.wait(5)
                    target.write_text("retained", encoding="utf-8")

                ctx.apply(commit, summary="第一段")
                return {"ignored": True}

            self._register_commit_kind("test-cancel-during-commit", runner)
            client = self._client(root, _write_schemas(base))
            job_id = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-cancel-during-commit", "input": {}},
            ).json()["job_id"]
            self.assertTrue(committing.wait(2))
            stopped = client.delete(f"/api/v1/profiles/alice/jobs/{job_id}")
            self.assertEqual(stopped.json()["job"]["status"], "running")
            self.assertTrue(stopped.json()["job"]["cancel_requested"])
            release.set()
            final = self._wait_final(client, job_id)
            committed_text = target.read_text(encoding="utf-8")

        self.assertEqual(final["job"]["error"]["code"], "job_cancelled")
        self.assertTrue(final["job"]["write_committed"])
        self.assertEqual(final["job"]["commit_summary"], "第一段")
        self.assertIn("已保留部分写入：第一段", final["job"]["error"]["message"])
        self.assertEqual(committed_text, "retained")

    def test_kind_watchdog_timeout_prevents_late_commit_without_polling(self) -> None:
        import threading

        started = threading.Event()
        release = threading.Event()
        self.addCleanup(release.set)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            profile = _write_profile(root, tree=SKILL_TREE)
            target = profile / "timeout-commit.txt"

            def runner(_profile, _job_input, _report, ctx):
                started.set()
                release.wait(5)
                ctx.apply(lambda: target.write_text("late", encoding="utf-8"))

            self._register_commit_kind("test-kind-timeout", runner, timeout=0.2)
            client = self._client(root, _write_schemas(base))
            job_id = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "test-kind-timeout", "input": {}},
            ).json()["job_id"]
            self.assertTrue(started.wait(2))
            deadline = time.monotonic() + 3
            while True:
                with jobs_module._LOCK:
                    requested = bool(jobs_module._JOBS[job_id]["cancel_requested"])
                if requested:
                    break
                self.assertLess(time.monotonic(), deadline, "kind watchdog did not fire")
                time.sleep(0.02)
            release.set()
            final = self._wait_final(client, job_id)
            target_exists = target.exists()

        self.assertEqual(final["job"]["error"]["code"], "job_timeout")
        self.assertFalse(final["job"]["write_committed"])
        self.assertFalse(target_exists)

    def test_ttl_prunes_only_terminal_jobs(self) -> None:
        running = {"status": "running", "created_at": 1.0, "finished_at": 0.0}
        done = {"status": "done", "created_at": 1.0, "finished_at": 1.0}
        with patch.dict(
            jobs_module._JOBS,
            {"test-old-running": running, "test-old-done": done},
            clear=False,
        ):
            jobs_module._prune_jobs()
            self.assertIn("test-old-running", jobs_module._JOBS)
            self.assertNotIn("test-old-done", jobs_module._JOBS)


class TestJobKindPolicies(unittest.TestCase):
    EXPECTED = {
        "project-suggest-refs",
        "evidence-crystallize",
        "content-rewrite",
        "content-meta",
        "content-cover",
        "content-social",
        "content-image",
        "career-match",
        "career-tailor",
        "career-structure",
        "research-connector-preview",
        "research-connector-import",
        "paper-quick-analysis",
        "paper-deep-read",
    }

    def test_all_fourteen_kinds_have_explicit_effect_action_and_tier(self) -> None:
        self.assertEqual(set(jobs_module._JOB_CLASSIFICATIONS), self.EXPECTED)
        self.assertLessEqual(self.EXPECTED, set(jobs_module._KINDS))
        for kind in self.EXPECTED:
            spec = jobs_module._KINDS[kind]
            policy = jobs_module.job_policy(kind)
            self.assertTrue(spec.effect, kind)
            self.assertTrue(spec.action, kind)
            self.assertEqual(policy.tier, jobs_module.agent_policy.tier_for(spec.action), kind)
        self.assertEqual(jobs_module.job_policy("research-connector-import").tier, "T2")
        self.assertEqual(jobs_module.job_policy("paper-quick-analysis").tier, "T1")
        self.assertEqual(jobs_module.job_policy("paper-deep-read").tier, "T1")

    def test_unclassified_kind_fails_closed_for_agents(self) -> None:
        spec = jobs_module.JobKind(
            name="test-unclassified",
            validate=lambda job_input: dict(job_input),
            run=lambda *_args: {},
        )
        with patch.dict(jobs_module._KINDS, {"test-unclassified": spec}):
            with self.assertRaises(jobs_module.UnclassifiedJobKindError):
                jobs_module.job_policy("test-unclassified")


class TestPaperJobCommitSegments(unittest.TestCase):
    class Context:
        def __init__(self, events: list[str]) -> None:
            self.events = events

        def checkpoint(self) -> None:
            return None

        def cancel_requested(self) -> bool:
            return False

        def apply(self, fn, *, kinds=None, summary=""):
            self.events.append(f"commit:{summary}")
            return fn()

    def test_analysis_journal_kinds_cover_all_derived_jsonl(self) -> None:
        from nblane.core import agent_journal
        from nblane.core.research_workspace import source_slug
        from nblane.web_api import research_papers as module

        source_id = "source:paper:demo"
        slug = source_slug(source_id)
        expected = {
            "research_source",
            agent_journal.file_kind(f"research/analysis/{slug}.yaml"),
            *(
                agent_journal.jsonl_kind(f"research/{dirname}/{slug}.jsonl")
                for dirname in (
                    "paper-pages",
                    "paper-segments",
                    "paper-structure",
                    "translations",
                )
            ),
        }
        self.assertEqual(set(module._analysis_journal_kinds(Path("/tmp/profile"), source_id)), expected)

    def test_quick_analysis_model_runs_outside_prepare_and_save_commits(self) -> None:
        from types import SimpleNamespace

        from nblane.web_api import research_papers as module

        source_id = "source:paper:demo"
        events: list[str] = []
        context = {
            "paper_markdown": "md",
            "chunks": [],
            "annotations": [],
            "paper_context": {},
            "aliases": {},
        }
        ai_result = AIActionResult(
            ok=True,
            action="research.paper_review_card",
            backend="fake",
            run_id="run-test",
            structured={"tldr": "ok", "key_points": [{"text": "kp"}]},
        )

        def model(*_args, **_kwargs):
            events.append("model")
            return ai_result

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(module.reader_action_core, "ensure_paper_reading_artifacts", return_value={"warnings": []}),
            patch.object(module, "load_paper_segments", return_value=[]),
            patch.object(module, "load_paper_annotations", return_value=[]),
            patch.object(module, "load_chunks", return_value=[]),
            patch.object(
                module,
                "load_research_sources",
                return_value=SimpleNamespace(by_id=lambda: {source_id: SimpleNamespace()}),
            ),
            patch.object(module.reader_action_core, "_compact_paper_for_analysis", return_value=context),
            patch.object(module.reader_action_core, "_compact_source_for_deep_read", return_value={}),
            patch.object(module.reader_action_core, "generate_paper_review_card", side_effect=model),
            patch.object(module.reader_action_core, "_should_save_quick_analysis", return_value=True),
            patch.object(module, "save_paper_analysis"),
        ):
            result = module._run_quick_analysis(
                "alice", Path(tmp), source_id, lambda *_args, **_kwargs: None, self.Context(events), ()
            )

        self.assertTrue(result.ok)
        self.assertLess(events.index("commit:准备论文阅读产物"), events.index("model"))
        self.assertLess(events.index("model"), events.index("commit:保存论文快速分析"))

    def test_deep_read_model_runs_outside_prepare_and_save_commits(self) -> None:
        from types import SimpleNamespace

        from nblane.web_api import research_papers as module

        source_id = "source:paper:demo"
        events: list[str] = []
        paper_md = SimpleNamespace(
            aliases={},
            markdown="md",
            stats={"segments": 1},
            directory=None,
            image_paths=lambda limit: [],
        )
        ai_result = AIActionResult(
            ok=True,
            action="research.paper_deep_read_codex",
            backend="fake",
            run_id="run-test",
            structured={"verdict": {"summary": "ok"}, "sections": [{"section": "s", "summary": "x"}]},
        )

        def model(*_args, **_kwargs):
            events.append("model")
            return ai_result

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(module.reader_action_core, "ensure_paper_reading_artifacts", return_value={"warnings": []}),
            patch.object(module.reader_action_core, "build_paper_markdown", return_value=paper_md),
            patch.object(module, "load_paper_annotations", return_value=[]),
            patch.object(
                module,
                "load_research_sources",
                return_value=SimpleNamespace(by_id=lambda: {source_id: SimpleNamespace()}),
            ),
            patch.object(module.reader_action_core, "_compact_source_for_deep_read", return_value={}),
            patch.object(module.reader_action_core, "_deep_read_project_context", return_value=[]),
            patch.object(module.reader_action_core, "_deep_read_library_context", return_value=[]),
            patch.object(module.reader_action_core, "deep_read_paper_codex", side_effect=model),
            patch.object(module, "load_paper_analysis", return_value={}),
            patch.object(module, "save_paper_analysis"),
        ):
            result = module._run_deep_read(
                "alice", Path(tmp), source_id, lambda *_args, **_kwargs: None, self.Context(events), ()
            )

        self.assertTrue(result.ok)
        self.assertLess(events.index("commit:准备论文阅读产物"), events.index("model"))
        self.assertLess(events.index("model"), events.index("commit:保存论文深度研读"))


class TestContentJobTimeoutBudget(unittest.TestCase):
    """Each content LLM call must give up before its job's watchdog fires."""

    def test_llm_timeouts_fit_inside_job_timeouts(self) -> None:
        from nblane.core import content_ai

        pairs = {
            "content-rewrite": content_ai.REWRITE_LLM_TIMEOUT_SECONDS,
            "content-meta": content_ai.META_LLM_TIMEOUT_SECONDS,
            "content-social": content_ai.SOCIAL_LLM_TIMEOUT_SECONDS,
        }
        for kind, llm_timeout in pairs.items():
            self.assertLess(llm_timeout, jobs_module._KINDS[kind].timeout_seconds, kind)

    def test_content_calls_disable_sdk_retries(self) -> None:
        from nblane.core import content_ai

        with patch("nblane.core.llm.is_configured", return_value=True), patch(
            "nblane.core.llm.chat", return_value="ok"
        ) as chat:
            content_ai.rewrite_selection(operation="polish", selection="原文。")
        self.assertEqual(chat.call_args.kwargs["max_retries"], 0)
        self.assertEqual(chat.call_args.kwargs["timeout"], content_ai.REWRITE_LLM_TIMEOUT_SECONDS)
