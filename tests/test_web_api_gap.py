"""Tests for the gap-analysis slice (POST .../gap/analyze and .../gap/intake)."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.core.gap_llm_router import RouterOutcome
from nblane.web_api import app, create_app

PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-gap-test-secret"

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


class GapTestBase(unittest.TestCase):
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


class TestGapAnalyze(GapTestBase):
    """Rule-only analysis: happy path, validation, and use_llm gating."""

    def test_analyze_happy_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/alice/gap/analyze",
                json={"task": "grasp manipulation task"},
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertEqual(payload["task"], "grasp manipulation task")
        match_ids = [m["id"] for m in payload["top_matches"]]
        self.assertIn("manipulation", match_ids)
        closure_by_id = {n["id"]: n for n in payload["closure"]}
        # Requires-closure pulls in the prerequisite chain.
        self.assertIn("manipulation", closure_by_id)
        self.assertIn("robotics", closure_by_id)
        self.assertEqual(closure_by_id["robotics"]["status"], "solid")
        self.assertFalse(closure_by_id["robotics"]["is_gap"])
        self.assertEqual(closure_by_id["manipulation"]["status"], "learning")
        self.assertTrue(closure_by_id["manipulation"]["is_gap"])
        # learning node is a gap, solid prerequisite is strong.
        self.assertIn("manipulation", payload["gaps"])
        self.assertIn("robotics", payload["strong"])
        self.assertFalse(payload["can_solve"])
        self.assertTrue(payload["next_steps"])
        self.assertIn("manipulation", payload["roots_from_rule"])
        self.assertEqual(payload["roots_from_llm"], [])
        # Coverage = strong share of the closure (1 strong of 2 here, or more
        # if the task matched extra nodes — keep the check relative).
        expected = 1 - len(payload["gaps"]) / len(payload["closure"])
        self.assertAlmostEqual(payload["coverage"], expected, places=4)

    def test_analyze_empty_task_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            blank = client.post(
                "/api/v1/profiles/alice/gap/analyze", json={"task": ""}
            )
            whitespace = client.post(
                "/api/v1/profiles/alice/gap/analyze", json={"task": "   "}
            )
        # Blank fails request validation (min_length=1).
        self.assertEqual(blank.status_code, 422)
        # Whitespace passes validation but the core rejects it as empty.
        self.assertEqual(whitespace.status_code, 422)
        self.assertEqual(whitespace.json()["code"], "empty_task")

    def test_analyze_use_llm_creates_job_202(self) -> None:
        """use_llm=true dispatches an async gap-analysis job (202).

        The full job lifecycle (progress events, LLM degradation, learned
        keywords) is covered in tests/test_web_api_jobs.py. The router is
        patched here too so the test never depends on LLM configuration.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            router = patch(
                "nblane.core.gap_llm_router.route_task_to_nodes",
                return_value=RouterOutcome(ok=True, node_ids=[], keywords={}),
            )
            self.addCleanup(router.stop)
            router.start()
            response = client.post(
                "/api/v1/profiles/alice/gap/analyze",
                json={"task": "grasp manipulation", "use_llm": True},
            )
            self.assertEqual(response.status_code, 202)
            payload = response.json()
            job_id = payload["job_id"]
            # Let the worker reach a final state before tmp teardown.
            deadline = time.monotonic() + 10
            status = ""
            while status not in {"done", "failed"}:
                self.assertLess(time.monotonic(), deadline)
                status = client.get(
                    f"/api/v1/profiles/alice/jobs/{job_id}"
                ).json()["job"]["status"]
                time.sleep(0.05)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["job_id"], payload["job"]["job_id"])
        self.assertEqual(payload["job"]["kind"], "gap-analysis")
        self.assertEqual(payload["job"]["profile"], "alice")
        self.assertEqual(status, "done")

    def test_analyze_unmatched_task_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/alice/gap/analyze",
                json={"task": "zzqqxxyy nothing matches this"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "no_roots")

    def test_analyze_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/nobody/gap/analyze", json={"task": "grasp"}
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "profile_not_found")


class TestGapIntake(GapTestBase):
    """Turning a detected gap into a kanban learning task."""

    def test_intake_creates_kanban_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/alice/gap/intake",
                json={
                    "title": "学习 Manipulation",
                    "node_id": "manipulation",
                    "why": "grasp manipulation task",
                },
            )
            board = client.get("/api/v1/profiles/alice/kanban")
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["section"], "Queue")
        card = payload["card"]
        self.assertEqual(card["title"], "学习 Manipulation")
        self.assertEqual(card["context"], "Gap analysis node: manipulation")
        self.assertIn("manipulation", card["tags"])
        self.assertEqual(board.status_code, 200)
        titles = [
            task["title"]
            for section in board.json()["sections"]
            for task in section["tasks"]
        ]
        self.assertIn("学习 Manipulation", titles)

    def test_intake_unknown_section_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/alice/gap/intake",
                json={"title": "x", "section": "Nope"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_gap_intake")

    def test_intake_echoes_actual_disk_section(self) -> None:
        """The response section is read back from kanban.md, not the request."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/alice/gap/intake",
                json={"title": "立即学 VLA", "section": "Doing"},
            )
            board = client.get("/api/v1/profiles/alice/kanban")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["section"], "Doing")
        doing_titles = [
            task["title"]
            for section in board.json()["sections"]
            if section["name"] == "Doing"
            for task in section["tasks"]
        ]
        self.assertIn("立即学 VLA", doing_titles)


class TestGapScope(GapTestBase):
    """401/403 enforcement under auth-on."""

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
            analyze = client.post(
                "/api/v1/profiles/alice/gap/analyze", json={"task": "grasp"}
            )
            intake = client.post(
                "/api/v1/profiles/alice/gap/intake", json={"title": "x"}
            )
        self.assertEqual(analyze.status_code, 401)
        self.assertEqual(intake.status_code, 401)

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
            forbidden = client.post(
                "/api/v1/profiles/alice/gap/analyze", json={"task": "grasp"}
            )
            forbidden_intake = client.post(
                "/api/v1/profiles/alice/gap/intake", json={"title": "x"}
            )
            allowed = client.post(
                "/api/v1/profiles/wang/gap/analyze", json={"task": "grasp"}
            )
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.json()["code"], "profile_forbidden")
        self.assertEqual(forbidden_intake.status_code, 403)
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["profile"], "wang")


if __name__ == "__main__":
    unittest.main()
