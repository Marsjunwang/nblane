"""Tests for the web_api async-jobs slice (jobs registry + SSE + LLM kinds).

Covers ``POST /profiles/{name}/jobs``, ``GET .../jobs/{job_id}``, and
``GET .../jobs/{job_id}/stream`` (SSE), plus the registered kinds:
``gap-analysis`` (wired into ``POST .../gap/analyze?use_llm=true``),
``studio-jd-match`` (Output Studio JD match) and ``project-suggest-refs``
(Project Board AI ref suggestion). The LLM router / gateway / core LLM
entry points are always patched — tests never touch the network or the
real ``.env`` key, and the learned-keyword store is redirected into the
tmp schemas tree so ``schemas/.learned/`` in the repo is never written.
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
from nblane.core.gap_llm_router import RouterOutcome
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
                        "teams": ["example-team"],
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
            ("nblane.core.gap.PROFILES_DIR", root),
            ("nblane.core.project_board.PROFILES_DIR", root),
            (
                "nblane.core.learned_keywords._LEARNED_DIR",
                schemas / ".learned",
            ),
        ):
            patcher = patch(target, value)
            self.addCleanup(patcher.stop)
            patcher.start()

    def _client(self, root: Path, schemas: Path) -> TestClient:
        self._patch_roots(root, schemas)
        return TestClient(app)

    def _patch_router(self, outcome: RouterOutcome | None = None, **kwargs) -> None:
        """Patch the LLM router so gap jobs never hit the network."""
        if outcome is None:
            outcome = RouterOutcome(ok=True, **kwargs)
        patcher = patch(
            "nblane.core.gap_llm_router.route_task_to_nodes",
            return_value=outcome,
        )
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
                json={"kind": "gap-analysis", "input": {"task": "   "}},
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
            self._patch_router(node_ids=[], keywords={})
            created = client.post(
                "/api/v1/profiles/alice/jobs",
                json={
                    "kind": "gap-analysis",
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


class TestGapAnalysisJob(JobsTestBase):
    """The gap-analysis kind: lifecycle, LLM degradation, structured failure."""

    def test_lifecycle_rule_plus_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_router(
                node_ids=["navigation"],
                keywords={"navigation": ["路径规划/path planning"]},
            )
            created = client.post(
                "/api/v1/profiles/alice/gap/analyze",
                json={"task": "grasp manipulation task", "use_llm": True},
            )
            self.assertEqual(created.status_code, 202)
            job_id = created.json()["job_id"]
            final = self._wait_final(client, job_id)
            learned_path = schemas / ".learned" / "test-domain.yaml"
            learned = (
                yaml.safe_load(learned_path.read_text(encoding="utf-8"))
                if learned_path.exists()
                else None
            )
        job = final["job"]
        self.assertEqual(job["status"], "done")
        self.assertEqual(job["kind"], "gap-analysis")
        self.assertEqual(job["phase"], "done")
        self.assertIsNone(job["error"])
        self.assertGreaterEqual(job["elapsed_ms"], 0)
        result = final["result"]
        self.assertEqual(result["profile"], "alice")
        self.assertEqual(result["analysis_mode"], "rule+llm")
        self.assertIn("navigation", result["roots_from_llm"])
        self.assertIn("manipulation", result["roots_from_rule"])
        self.assertIsNone(result["llm_router_error"])
        # LLM-only root joins the closure; the sync rule path never sees it.
        closure_ids = [node["id"] for node in result["closure"]]
        self.assertIn("navigation", closure_ids)
        # Router keywords persisted into the *tmp* learned store.
        self.assertTrue(result["learned_merged"])
        self.assertIsNotNone(learned)
        self.assertIn("navigation", learned)

    def test_llm_failure_degrades_to_rule_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_router(
                outcome=RouterOutcome(ok=False, error="LLM not configured")
            )
            created = client.post(
                "/api/v1/profiles/alice/gap/analyze",
                json={"task": "grasp manipulation task", "use_llm": True},
            )
            self.assertEqual(created.status_code, 202)
            job_id = created.json()["job_id"]
            final = self._wait_final(client, job_id)
        self.assertEqual(final["job"]["status"], "done")
        result = final["result"]
        self.assertEqual(result["analysis_mode"], "rule+llm")
        self.assertEqual(result["llm_router_error"], "LLM not configured")
        self.assertEqual(result["roots_from_llm"], [])
        self.assertIn("manipulation", result["roots_from_rule"])
        self.assertFalse(result["learned_merged"])

    def test_no_roots_fails_with_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_router(node_ids=[], keywords={})
            created = client.post(
                "/api/v1/profiles/alice/gap/analyze",
                json={"task": "zzqqxxyy nothing matches", "use_llm": True},
            )
            self.assertEqual(created.status_code, 202)
            job_id = created.json()["job_id"]
            final = self._wait_final(client, job_id)
        job = final["job"]
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["error"]["code"], "no_roots")
        self.assertIn("No skill nodes matched", job["error"]["message"])
        self.assertIsNone(final["result"])

    def test_generic_jobs_endpoint_creates_gap_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_router(node_ids=[], keywords={})
            created = client.post(
                "/api/v1/profiles/alice/jobs",
                json={
                    "kind": "gap-analysis",
                    "input": {"task": "grasp manipulation"},
                },
            )
            self.assertEqual(created.status_code, 202)
            payload = created.json()
            self.assertEqual(payload["job"]["status"], "queued")
            self.assertEqual(payload["job"]["phase"], "queued")
            final = self._wait_final(client, payload["job_id"])
        self.assertEqual(final["job"]["status"], "done")
        self.assertEqual(final["result"]["analysis_mode"], "rule+llm")


class TestJobStream(JobsTestBase):
    """SSE stream: initial snapshot, replayed progress, terminal frame."""

    def test_stream_done_replays_progress_phases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_router(node_ids=["navigation"], keywords={})
            created = client.post(
                "/api/v1/profiles/alice/gap/analyze",
                json={"task": "grasp manipulation task", "use_llm": True},
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
        # Core-reported stages survive even when the subscriber connects
        # after the job already finished (seq-log replay).
        self.assertIn("routing", phases)
        self.assertIn("merging", phases)
        done = frames[-1][1]
        self.assertTrue(done["ok"])
        self.assertEqual(done["job"]["status"], "done")
        self.assertEqual(done["result"]["analysis_mode"], "rule+llm")
        self.assertIn("navigation", done["result"]["roots_from_llm"])

    def test_stream_terminal_error_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_router(node_ids=[], keywords={})
            created = client.post(
                "/api/v1/profiles/alice/gap/analyze",
                json={"task": "zzqqxxyy nothing matches", "use_llm": True},
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
                json={"kind": "gap-analysis", "input": {"task": "grasp"}},
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
            self._patch_router(node_ids=[], keywords={})
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            create = client.post(
                "/api/v1/profiles/alice/jobs",
                json={"kind": "gap-analysis", "input": {"task": "grasp"}},
            )
            status = client.get("/api/v1/profiles/alice/jobs/job-x")
            stream = client.get("/api/v1/profiles/alice/jobs/job-x/stream")
            # Member may still run jobs on their own profile.
            own = client.post(
                "/api/v1/profiles/wang/jobs",
                json={"kind": "gap-analysis", "input": {"task": "grasp"}},
            )
            self.assertEqual(own.status_code, 202)
            self._wait_final(client, own.json()["job_id"], name="wang")
        self.assertEqual(create.status_code, 403)
        self.assertEqual(create.json()["code"], "profile_forbidden")
        self.assertEqual(status.status_code, 403)
        self.assertEqual(stream.status_code, 403)


class TestStudioJdMatchJob(JobsTestBase):
    """The studio-jd-match kind: lifecycle plus unavailable/failed mapping.

    ``llm.is_configured`` and the core ``jd_match`` entry points are always
    patched — tests never touch the network or the real .env key.
    """

    def _patch_llm(self, configured: bool = True) -> None:
        patcher = patch("nblane.core.llm.is_configured", return_value=configured)
        self.addCleanup(patcher.stop)
        patcher.start()

    def _patch_core(self, analysis: str = "## 匹配分析\n\n✅ 符合") -> None:
        for target, value in (
            ("nblane.core.jd_match.gather_profile_context", "(context)"),
            ("nblane.core.jd_match.analyze_jd", analysis),
        ):
            patcher = patch(target, return_value=value)
            self.addCleanup(patcher.stop)
            patcher.start()

    def _create(self, client: TestClient, **job_input: str):
        return client.post(
            "/api/v1/profiles/alice/jobs",
            json={"kind": "studio-jd-match", "input": job_input},
        )

    def test_success_phases_result_and_sse_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_llm(configured=True)
            self._patch_core()
            created = self._create(
                client, resume_md="# Resume", jd_text="Robotics engineer"
            )
            self.assertEqual(created.status_code, 202)
            job = created.json()["job"]
            self.assertEqual(job["kind"], "studio-jd-match")
            self.assertEqual(job["status"], "queued")
            job_id = created.json()["job_id"]
            final = self._wait_final(client, job_id)
            with client.stream(
                "GET", f"/api/v1/profiles/alice/jobs/{job_id}/stream"
            ) as response:
                frames = _read_sse_frames(response)
        self.assertEqual(final["job"]["status"], "done")
        result = final["result"]
        self.assertTrue(result["ok"])
        self.assertIn("匹配分析", result["analysis"])
        kinds = [event for event, _ in frames]
        self.assertEqual(kinds[0], "job")
        self.assertEqual(kinds[-1], "done")
        phases = [
            data["event"]["phase"] for event, data in frames if event == "progress"
        ]
        # The two real stages (context gather, LLM write) replay in order.
        self.assertEqual(phases, ["analyzing", "generating"])
        done = frames[-1][1]
        self.assertEqual(done["result"]["analysis"], result["analysis"])

    def test_unavailable_without_llm_fails_structured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_llm(configured=False)
            created = self._create(
                client, resume_md="# Resume", jd_text="Robotics engineer"
            )
            self.assertEqual(created.status_code, 202)
            job_id = created.json()["job_id"]
            final = self._wait_final(client, job_id)
            with client.stream(
                "GET", f"/api/v1/profiles/alice/jobs/{job_id}/stream"
            ) as response:
                frames = _read_sse_frames(response)
        job = final["job"]
        self.assertEqual(job["status"], "failed")
        # Same code as the sync endpoint's 422 — the SPA maps it to the
        # same yellow degradation card.
        self.assertEqual(job["error"]["code"], "studio_jd_match_unavailable")
        self.assertIsNone(final["result"])
        self.assertEqual(frames[-1][0], "error")
        self.assertEqual(
            frames[-1][1]["error"]["code"], "studio_jd_match_unavailable"
        )

    def test_provider_error_fails_with_failed_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_llm(configured=True)
            self._patch_core(analysis="LLM error: provider timeout")
            created = self._create(
                client, resume_md="# Resume", jd_text="Robotics engineer"
            )
            self.assertEqual(created.status_code, 202)
            final = self._wait_final(client, created.json()["job_id"])
        self.assertEqual(final["job"]["status"], "failed")
        self.assertEqual(final["job"]["error"]["code"], "studio_jd_match_failed")
        self.assertIn("provider timeout", final["job"]["error"]["message"])

    def test_blank_input_422_at_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            self._patch_llm(configured=True)
            response = self._create(client, resume_md="   ", jd_text="JD")
            too_long = self._create(
                client, resume_md="x" * 50_001, jd_text="JD"
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_jd_match_request")
        self.assertEqual(too_long.status_code, 422)
        self.assertEqual(too_long.json()["code"], "invalid_jd_match_request")


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
    """The two new kinds ride the same auth-guarded generic endpoints."""

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
            jd = client.post(
                "/api/v1/profiles/alice/jobs",
                json={
                    "kind": "studio-jd-match",
                    "input": {"resume_md": "r", "jd_text": "j"},
                },
            )
            suggest = client.post(
                "/api/v1/profiles/alice/jobs",
                json={
                    "kind": "project-suggest-refs",
                    "input": {"case_id": "project:robot-arm"},
                },
            )
        self.assertEqual(jd.status_code, 401)
        self.assertEqual(suggest.status_code, 401)


if __name__ == "__main__":
    unittest.main()
