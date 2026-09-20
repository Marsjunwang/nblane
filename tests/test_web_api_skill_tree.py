"""Tests for GET /api/v1/profiles/{name}/skill-tree (M2 read endpoint)."""

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
TEST_SESSION_SECRET = "web-api-skill-tree-test-secret"

SCHEMA = {
    "schema_version": "1.0",
    "domain": "Test Domain",
    "nodes": [
        {"id": "root_a", "label": "Root A", "level": 1},
        {"id": "child_a1", "label": "Child A1", "level": 2, "requires": ["root_a"]},
        {"id": "child_a2", "label": "Child A2", "level": 2, "requires": ["root_a"]},
        {
            "id": "grand_a11",
            "label": "Grand A11",
            "level": 3,
            "requires": ["child_a1", "child_a2"],
        },
        {"id": "root_b", "label": "Root B", "level": 1},
    ],
}

SKILL_TREE = {
    "profile": "alice",
    "schema": "test-domain",
    "updated": "2026-09-10",
    "nodes": [
        {
            "id": "root_a",
            "status": "solid",
            "evidence_refs": ["ev_one", "ev_missing", "ev_deprecated"],
        },
        {"id": "child_a1", "status": "learning"},
        {
            "id": "child_a2",
            "status": "learning",
            "evidence": [{"type": "practice", "title": "Inline drill"}],
        },
        {"id": "grand_a11", "status": "locked"},
        {"id": "root_b", "status": "expert", "evidence_refs": ["ev_one"]},
        # Not in the schema: becomes a root with the id as title.
        {"id": "off_schema", "status": "learning"},
    ],
}

EVIDENCE_POOL = {
    "profile": "alice",
    "evidence_entries": [
        {"id": "ev_one", "type": "project", "title": "Demo"},
        {"id": "ev_deprecated", "type": "project", "title": "Old", "deprecated": True},
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


class TestSkillTreeRead(unittest.TestCase):
    """Shape, hierarchy, counts, and empty-tree behavior."""

    def _client(self, root: Path, schemas: Path) -> TestClient:
        for target, value in (
            ("nblane.core.profile_io.PROFILES_DIR", root),
            ("nblane.core.io.PROFILES_DIR", root),
            ("nblane.core.schema_io.SCHEMAS_DIR", schemas),
        ):
            patcher = patch(target, value)
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(app)

    def test_nested_tree_with_counts_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.get("/api/v1/profiles/alice/skill-tree")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertEqual(payload["schema_name"], "test-domain")
        self.assertEqual(payload["updated"], "2026-09-10")
        self.assertEqual(
            payload["status_counts"],
            {"expert": 1, "solid": 1, "learning": 3, "locked": 1, "total": 6},
        )

        roots = payload["nodes"]
        # Schema order: root_a, root_b, then the off-schema node last.
        self.assertEqual([n["id"] for n in roots], ["root_a", "root_b", "off_schema"])
        root_a = roots[0]
        self.assertEqual(root_a["title"], "Root A")
        self.assertEqual(root_a["status"], "solid")
        # ev_missing is not in the pool and ev_deprecated is deprecated:
        # only ev_one resolves.
        self.assertEqual(root_a["evidence_count"], 1)
        self.assertEqual(roots[1]["evidence_count"], 1)
        self.assertEqual(roots[2]["title"], "off_schema")

        children = root_a["children"]
        self.assertEqual([c["id"] for c in children], ["child_a1", "child_a2"])
        # Inline evidence rows count too.
        self.assertEqual(children[1]["evidence_count"], 1)
        # grand_a11 requires both children (a DAG diamond): it renders once,
        # under the first parent in schema order.
        self.assertEqual([g["id"] for g in children[0]["children"]], ["grand_a11"])
        self.assertEqual(children[1]["children"], [])

        def flatten(nodes: list[dict]) -> list[str]:
            out: list[str] = []
            for node in nodes:
                out.append(node["id"])
                out.extend(flatten(node["children"]))
            return out

        flat = flatten(roots)
        self.assertEqual(len(flat), len(set(flat)))
        self.assertEqual(len(flat), payload["status_counts"]["total"])

    def test_empty_tree_returns_empty_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            # No skill-tree.yaml at all: 200 with empty nodes.
            _write_profile(root, tree=None)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            missing = client.get("/api/v1/profiles/alice/skill-tree")
            # Explicitly empty nodes list behaves the same.
            _write_profile(
                root,
                tree={
                    "schema": "test-domain",
                    "updated": "2026-09-11",
                    "nodes": [],
                },
            )
            empty = client.get("/api/v1/profiles/alice/skill-tree")
        for response in (missing, empty):
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["nodes"], [])
            self.assertEqual(payload["status_counts"]["total"], 0)
        self.assertEqual(missing.json()["schema_name"], "")
        self.assertEqual(empty.json()["schema_name"], "test-domain")
        self.assertEqual(empty.json()["updated"], "2026-09-11")

    def test_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.get("/api/v1/profiles/nobody/skill-tree")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "profile_not_found")


class TestSkillTreeScope(unittest.TestCase):
    """401/403 enforcement under auth-on."""

    def _auth_client(self, root: Path, schemas: Path) -> TestClient:
        for target, value in (
            ("nblane.core.profile_io.PROFILES_DIR", root),
            ("nblane.core.io.PROFILES_DIR", root),
            ("nblane.core.schema_io.SCHEMAS_DIR", schemas),
        ):
            patcher = patch(target, value)
            self.addCleanup(patcher.stop)
            patcher.start()
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
            response = client.get("/api/v1/profiles/alice/skill-tree")
        self.assertEqual(response.status_code, 401)

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
            forbidden = client.get("/api/v1/profiles/alice/skill-tree")
            allowed = client.get("/api/v1/profiles/wang/skill-tree")
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.json()["code"], "profile_forbidden")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["profile"], "wang")


if __name__ == "__main__":
    unittest.main()
