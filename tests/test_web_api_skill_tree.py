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
        {"id": "root_a", "label": "Root A", "level": 1, "category": "foundations"},
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
        # Schema grouping flows through; off-schema nodes answer "".
        self.assertEqual(root_a["category"], "foundations")
        self.assertEqual(roots[2]["category"], "")
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

    def test_categories_rollup_for_banner_headers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
            client = self._client(root, schemas)
            response = client.get("/api/v1/profiles/alice/skill-tree")
        self.assertEqual(response.status_code, 200)
        categories = response.json()["categories"]
        # Schema order: foundations (root_a) first, then the uncategorized
        # bucket (schema nodes without category + off-schema nodes).
        self.assertEqual([c["id"] for c in categories], ["foundations", ""])
        foundations = categories[0]
        self.assertEqual(foundations["name"], "基础")  # CATEGORY_ZH table
        self.assertEqual(foundations["count"], 1)
        self.assertEqual(foundations["lit_count"], 1)  # solid counts as lit
        self.assertEqual(foundations["learning_count"], 0)
        misc = categories[1]
        self.assertEqual(misc["name"], "")
        self.assertEqual(misc["count"], 5)
        # root_b is expert (lit); child_a1/child_a2/off_schema are learning.
        self.assertEqual(misc["lit_count"], 1)
        self.assertEqual(misc["learning_count"], 3)


SKILL_MD_WITH_BLOCK = """# SKILL — {name}

<!-- BEGIN GENERATED:skill_tree -->
- stale
<!-- END GENERATED:skill_tree -->

<!-- BEGIN GENERATED:current_focus -->
- stale
<!-- END GENERATED:current_focus -->
"""


class TestSkillNodePatch(unittest.TestCase):
    """PATCH /skill-tree/nodes/{node_id}: 三态 status write (G3)."""

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

    def _setup(self, base: Path, skill_md: bool = False) -> tuple[TestClient, Path]:
        root = base / "profiles"
        pdir = _write_profile(root, tree=SKILL_TREE)
        if skill_md:
            (pdir / "SKILL.md").write_text(
                SKILL_MD_WITH_BLOCK.format(name="alice"), encoding="utf-8"
            )
        schemas = _write_schemas(base)
        return self._client(root, schemas), pdir

    def _tree_status(self, pdir: Path, node_id: str) -> str:
        raw = yaml.safe_load((pdir / "skill-tree.yaml").read_text(encoding="utf-8"))
        node = next(n for n in raw["nodes"] if n["id"] == node_id)
        return str(node.get("status") or "locked")

    def test_patch_lit_maps_to_solid_and_syncs_skill_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client, pdir = self._setup(Path(tmp), skill_md=True)
            etag = client.get("/api/v1/profiles/alice/skill-tree").headers["ETag"]
            response = client.patch(
                "/api/v1/profiles/alice/skill-tree/nodes/child_a1",
                json={"status": "lit"},
                headers={"If-Match": etag},
            )
            skill_md = (pdir / "SKILL.md").read_text(encoding="utf-8")
            disk_status = self._tree_status(pdir, "child_a1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["node_id"], "child_a1")
        self.assertEqual(payload["previous_status"], "learning")
        # 点亮 (三态 lit) lands as the YAML status solid.
        self.assertEqual(payload["status"], "solid")
        self.assertTrue(payload["changed"])
        self.assertTrue(response.headers["ETag"])
        self.assertNotEqual(response.headers["ETag"], etag)
        self.assertEqual(disk_status, "solid")
        # SKILL.md generated block re-synced: learning icon -> lit icon.
        self.assertIn("- [x] child_a1 (`child_a1`)", skill_md)

    def test_patch_locked_and_learning_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client, pdir = self._setup(Path(tmp))
            etag = client.get("/api/v1/profiles/alice/skill-tree").headers["ETag"]
            first = client.patch(
                "/api/v1/profiles/alice/skill-tree/nodes/grand_a11",
                json={"status": "learning"},
                headers={"If-Match": etag},
            )
            back = client.patch(
                "/api/v1/profiles/alice/skill-tree/nodes/grand_a11",
                json={"status": "locked"},
                headers={"If-Match": first.headers["ETag"]},
            )
            disk_status = self._tree_status(pdir, "grand_a11")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(back.status_code, 200)
        self.assertEqual(disk_status, "locked")

    def test_noop_patch_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client, pdir = self._setup(Path(tmp))
            etag = client.get("/api/v1/profiles/alice/skill-tree").headers["ETag"]
            before = (pdir / "skill-tree.yaml").read_text(encoding="utf-8")
            # root_a is already solid; 三态 lit maps to solid: no-op.
            response = client.patch(
                "/api/v1/profiles/alice/skill-tree/nodes/root_a",
                json={"status": "lit"},
                headers={"If-Match": etag},
            )
            after = (pdir / "skill-tree.yaml").read_text(encoding="utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["changed"])
        self.assertEqual(before, after)

    def test_unknown_node_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client, _ = self._setup(Path(tmp))
            response = client.patch(
                "/api/v1/profiles/alice/skill-tree/nodes/ghost_node",
                json={"status": "learning"},
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "skill_node_not_found")

    def test_invalid_status_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client, _ = self._setup(Path(tmp))
            responses = [
                client.patch(
                    "/api/v1/profiles/alice/skill-tree/nodes/root_a",
                    json={"status": "glowing"},
                ),
                # Raw YAML rungs are not part of the 三态 write vocabulary.
                client.patch(
                    "/api/v1/profiles/alice/skill-tree/nodes/root_a",
                    json={"status": "expert"},
                ),
                client.patch(
                    "/api/v1/profiles/alice/skill-tree/nodes/root_a",
                    json={"status": "solid"},
                ),
            ]
        for response in responses:
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()["code"], "invalid_skill_status")

    def test_stale_if_match_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client, pdir = self._setup(Path(tmp))
            response = client.patch(
                "/api/v1/profiles/alice/skill-tree/nodes/child_a1",
                json={"status": "lit"},
                headers={"If-Match": 'W/"stale"'},
            )
            disk_status = self._tree_status(pdir, "child_a1")
        self.assertEqual(response.status_code, 412)
        self.assertEqual(response.json()["code"], "etag_mismatch")
        self.assertEqual(disk_status, "learning")

    def test_unauthenticated_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root, tree=SKILL_TREE)
            schemas = _write_schemas(base)
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
            client = TestClient(create_app())
            response = client.patch(
                "/api/v1/profiles/alice/skill-tree/nodes/child_a1",
                json={"status": "lit"},
            )
        self.assertEqual(response.status_code, 401)


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
