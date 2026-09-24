"""Tests for POST /api/v1/profiles/{name}/divination (占卜; design §5).

Covers the play/serious modes, same-day determinism, real-data anchoring,
the serious-mode gap-analysis backbone, the LLM/rule source switch (the
gateway runner is patched — no network), the timeout fallback, and the
422/401/403/404 guards. All profiles live under tmp_path.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.web_api import app, create_app

PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-divination-test-secret"

TODAY = date.today()

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
    "schema": "test-domain",
    "updated": "2026-09-19",
    "nodes": [
        {"id": "robotics", "status": "solid"},
        {"id": "manipulation", "status": "learning"},
        {"id": "navigation", "status": "locked"},
    ],
}

SKILL_MD = """# alice · nblane Profile

## Identity

- **Name**: alice
- **North Star**: 成为能独立交付机器人 demo 的工程师

---
"""

GOALS = {
    "schema_version": "1.0",
    "updated": "2026-09-19",
    "current_goal_id": "goal-1",
    "goals": [
        {"id": "goal-1", "title": "Ship VLA demo", "status": "active"},
    ],
}

KANBAN = """# alice · Kanban

## Doing

---

## Queue

---
"""

PROJECT_BOARD = {
    "schema_version": "1.0",
    "updated": "2026-09-19",
    "project_cases": [
        {
            "id": "project:robot-arm",
            "title": "Robot Arm",
            "status": "active",
            "kind": "work",
            "goal_refs": ["goal-1"],
        },
    ],
}


def _write_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (profile / "skill-tree.yaml").write_text(
        yaml.safe_dump(dict(SKILL_TREE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "goals.yaml").write_text(
        yaml.safe_dump(dict(GOALS, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "kanban.md").write_text(KANBAN, encoding="utf-8")
    (profile / "project-board.yaml").write_text(
        yaml.safe_dump(dict(PROJECT_BOARD, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "evidence-pool.yaml").write_text(
        yaml.safe_dump(
            {
                "profile": name,
                "updated": TODAY.isoformat(),
                "evidence_entries": [
                    {
                        "id": "ev_recent",
                        "type": "project",
                        "title": "Recent grasping run",
                        "date": (TODAY - timedelta(days=3)).isoformat(),
                        "review_status": "needs_review",
                        "project_refs": ["project:robot-arm"],
                    },
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (profile / "activity-log.yaml").write_text(
        yaml.safe_dump(
            {
                "profile": name,
                "updated": TODAY.isoformat(),
                "habits": [
                    {
                        "id": "exercise",
                        "title": "锻炼",
                        "kind": "health",
                        "cadence": "daily",
                    }
                ],
                "checkins": [
                    {
                        "date": (TODAY - timedelta(days=o)).isoformat(),
                        "habits": ["exercise"],
                    }
                    for o in range(3)
                ],
                "weekly_summaries": [],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return profile


def _write_schemas(base: Path) -> Path:
    schemas = base / "schemas"
    schemas.mkdir(parents=True, exist_ok=True)
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
                        "teams": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def _failing_runner(profile: str, payload: dict) -> SimpleNamespace:
    return SimpleNamespace(ok=False, structured=None, error="ai_not_configured")


def _ok_runner(profile: str, payload: dict) -> SimpleNamespace:
    return SimpleNamespace(
        ok=True,
        structured={"judgment": "LLM 判词", "reading": "LLM 解卦"},
    )


class DivinationApiTestBase(unittest.TestCase):
    """Root patching + LLM runner isolation for the API layer."""

    def _client(self, root: Path, schemas: Path, runner=_failing_runner) -> TestClient:
        for target, value in (
            ("nblane.core.profile_io.PROFILES_DIR", root),
            ("nblane.core.io.PROFILES_DIR", root),
            ("nblane.core.io.SCHEMAS_DIR", schemas),
            ("nblane.core.schema_io.SCHEMAS_DIR", schemas),
            ("nblane.core.gap.PROFILES_DIR", root),
            ("nblane.core.project_board.PROFILES_DIR", root),
            ("nblane.core.learned_keywords._LEARNED_DIR", schemas / ".learned"),
        ):
            patcher = patch(target, value)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch("nblane.core.divination._default_runner", runner)
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)


class TestDivinationPlay(DivinationApiTestBase):
    def test_play_happy_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/alice/divination", json={}
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertEqual(payload["mode"], "play")
        self.assertEqual(payload["source"], "rule")
        self.assertEqual(payload["generated_on"], TODAY.isoformat())
        hexagram = payload["hexagram"]
        self.assertEqual(len(hexagram["symbol_lines"]), 6)
        self.assertTrue(set(hexagram["symbol_lines"]) <= {0, 1})
        self.assertTrue(hexagram["name"])
        self.assertTrue(hexagram["judgment"])
        self.assertTrue(payload["reading"])

    def test_play_deterministic_within_a_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            first = client.post("/api/v1/profiles/alice/divination", json={})
            second = client.post("/api/v1/profiles/alice/divination", json={})
        self.assertEqual(first.json()["hexagram"], second.json()["hexagram"])
        self.assertEqual(first.json()["reading"], second.json()["reading"])

    def test_play_anchors_real_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            payload = client.post(
                "/api/v1/profiles/alice/divination", json={}
            ).json()
        anchors = payload["anchors"]
        self.assertEqual(anchors["skills_lit"], 1)
        self.assertEqual(anchors["skills_total"], 3)
        self.assertEqual(anchors["projects_active"], 1)
        self.assertEqual(anchors["project_titles"], ["Robot Arm"])
        self.assertEqual(anchors["evidence_needs_review"], 1)
        self.assertEqual(anchors["best_streak"], 3)
        self.assertIn("Robot Arm", payload["reading"])
        self.assertIn("已连续钤印 3 日", payload["reading"])

    def test_invalid_mode_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/alice/divination", json={"mode": "wild"}
            )
        self.assertEqual(response.status_code, 422)

    def test_question_length_capped_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/alice/divination",
                json={"question": "长" * 501},
            )
        self.assertEqual(response.status_code, 422)


class TestDivinationSerious(DivinationApiTestBase):
    def test_serious_requires_question_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            missing = client.post(
                "/api/v1/profiles/alice/divination", json={"mode": "serious"}
            )
            blank = client.post(
                "/api/v1/profiles/alice/divination",
                json={"mode": "serious", "question": "   "},
            )
        self.assertEqual(missing.status_code, 422)
        self.assertEqual(missing.json()["code"], "question_required")
        self.assertEqual(blank.status_code, 422)
        self.assertEqual(blank.json()["code"], "question_required")

    def test_serious_includes_real_gap_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.post(
                "/api/v1/profiles/alice/divination",
                json={"mode": "serious", "question": "grasp the cube"},
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode"], "serious")
        gap = payload["anchors"]["gap"]
        self.assertFalse(gap["can_solve"])
        self.assertIn("Manipulation", gap["gap_labels"])
        self.assertIn("Robotics", gap["strong_labels"])
        self.assertIn("Manipulation", payload["reading"])


class TestDivinationLlmSwitch(DivinationApiTestBase):
    def test_llm_source_when_gateway_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas, runner=_ok_runner)
            payload = client.post(
                "/api/v1/profiles/alice/divination", json={}
            ).json()
        self.assertEqual(payload["source"], "llm")
        self.assertEqual(payload["hexagram"]["judgment"], "LLM 判词")
        self.assertEqual(payload["reading"], "LLM 解卦")

    def test_timeout_falls_back_to_rule(self) -> None:
        def timeout_runner(profile: str, payload: dict) -> None:
            raise TimeoutError("LLM request timed out")

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            client = self._client(root, schemas, runner=timeout_runner)
            response = client.post(
                "/api/v1/profiles/alice/divination", json={}
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source"], "rule")
        self.assertTrue(payload["hexagram"]["judgment"])
        self.assertTrue(payload["reading"])


class TestDivinationGuards(DivinationApiTestBase):
    def test_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            response = self._client(root, schemas).post(
                "/api/v1/profiles/nobody/divination", json={}
            )
        self.assertEqual(response.status_code, 404)

    def test_invalid_profile_name_400(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            response = self._client(root, schemas).post(
                "/api/v1/profiles/%2E%2E/divination", json={}
            )
        self.assertEqual(response.status_code, 400)

    def _auth_client(self, root: Path, schemas: Path) -> TestClient:
        users_file = _write_users_file(root / "users.yaml")
        env = {
            "NBLANE_AUTH_FILE": str(users_file),
            "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
        }
        patcher = patch.dict(os.environ, env)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target, value in (
            ("nblane.core.profile_io.PROFILES_DIR", root),
            ("nblane.core.io.PROFILES_DIR", root),
            ("nblane.core.io.SCHEMAS_DIR", schemas),
            ("nblane.core.schema_io.SCHEMAS_DIR", schemas),
            ("nblane.core.gap.PROFILES_DIR", root),
            ("nblane.core.project_board.PROFILES_DIR", root),
            ("nblane.core.learned_keywords._LEARNED_DIR", schemas / ".learned"),
        ):
            patcher = patch(target, value)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch(
            "nblane.core.divination._default_runner", _failing_runner
        )
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(create_app())

    def test_unauthenticated_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            response = self._auth_client(root, schemas).post(
                "/api/v1/profiles/alice/divination", json={}
            )
        self.assertEqual(response.status_code, 401)

    def test_member_forbidden_from_other_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, "alice")
            _write_profile(root, "wang")
            schemas = _write_schemas(base)
            client = self._auth_client(root, schemas)
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            forbidden = client.post(
                "/api/v1/profiles/alice/divination", json={}
            )
            allowed = client.post(
                "/api/v1/profiles/wang/divination", json={}
            )
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.json()["code"], "profile_forbidden")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["profile"], "wang")


if __name__ == "__main__":
    unittest.main()
