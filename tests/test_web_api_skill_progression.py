"""API tests: skill-tree node ``progress`` and the ``skill.lit`` chronicle.

GET /profiles/{name}/skill-tree attaches the tunable progression readout
(core.skill_progression) to every node; PATCH
/profiles/{name}/skill-tree/nodes/{node_id} appends a ``skill.lit``
chronicle entry only when the rung actually advances (not on downgrade or
no-op). Profiles/schemas are built under tmp dirs.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.web_api import app

SCHEMA = {
    "schema_version": "1.0",
    "domain": "Test Domain",
    "nodes": [
        {"id": "root_a", "label": "Root A", "level": 1, "category": "foundations"},
        {"id": "child_a1", "label": "Child A1", "level": 2,
         "requires": ["root_a"]},
        {"id": "child_a2", "label": "Child A2", "level": 2,
         "requires": ["root_a"]},
    ],
}

SKILL_TREE = {
    "profile": "alice",
    "schema": "test-domain",
    "updated": "2026-09-10",
    "nodes": [
        {
            "id": "root_a",
            "status": "learning",
            "evidence_refs": ["ev_strong", "ev_breakthrough",
                              "ev_deprecated", "ev_missing"],
        },
        {"id": "child_a1", "status": "locked", "evidence_refs": ["ev_weak"]},
        {"id": "child_a2", "status": "expert",
         "evidence_refs": ["ev_breakthrough"]},
    ],
}

EVIDENCE_POOL = {
    "profile": "alice",
    "evidence_entries": [
        {"id": "ev_strong", "type": "project", "title": "Strong",
         "strength": "strong"},
        {"id": "ev_breakthrough", "type": "project", "title": "Landmark",
         "strength": "medium", "breakthrough": True},
        {"id": "ev_weak", "type": "practice", "title": "Weak",
         "strength": "weak"},
        {"id": "ev_deprecated", "type": "project", "title": "Old",
         "strength": "strong", "deprecated": True},
    ],
}


def _write_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "skill-tree.yaml").write_text(
        yaml.safe_dump(dict(SKILL_TREE, profile=name), allow_unicode=True,
                       sort_keys=False),
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


def _read_chronicle(pdir: Path) -> list[dict]:
    path = pdir / "chronicle.yaml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(raw.get("entries") or [])


class SkillProgressionApiTestBase(unittest.TestCase):
    """Shared env patching: profile/schema roots plus git-backup isolation."""

    def _client(self, root: Path, schemas: Path) -> TestClient:
        for target, value in (
            ("nblane.core.profile_io.PROFILES_DIR", root),
            ("nblane.core.io.PROFILES_DIR", root),
            ("nblane.core.schema_io.SCHEMAS_DIR", schemas),
        ):
            patcher = patch(target, value)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch("nblane.core.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)

    def _setup(self, base: Path) -> tuple[TestClient, Path]:
        root = base / "profiles"
        pdir = _write_profile(root)
        schemas = _write_schemas(base)
        return self._client(root, schemas), pdir


def _flatten(nodes: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for node in nodes:
        out[node["id"]] = node
        out.update(_flatten(node["children"]))
    return out


class TestSkillTreeProgress(SkillProgressionApiTestBase):
    """GET /skill-tree: every node carries the progression readout."""

    def test_progress_math_per_node(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client, _pdir = self._setup(Path(tmp))
            response = client.get("/api/v1/profiles/alice/skill-tree")
        self.assertEqual(response.status_code, 200)
        nodes = _flatten(response.json()["nodes"])
        self.assertEqual(set(nodes), {"root_a", "child_a1", "child_a2"})

        root_a = nodes["root_a"]["progress"]
        # strong (100) + breakthrough medium (10 + 1000); deprecated and
        # missing refs are excluded.
        self.assertEqual(root_a["score"], 1110)
        self.assertEqual(root_a["breakthrough_count"], 1)
        self.assertEqual(root_a["next_rung"], "solid")
        self.assertEqual(root_a["threshold_next"], 30)
        self.assertTrue(root_a["eligible"])

        child_a1 = nodes["child_a1"]["progress"]
        self.assertEqual(child_a1["score"], 1)
        self.assertEqual(child_a1["breakthrough_count"], 0)
        self.assertEqual(child_a1["next_rung"], "learning")
        self.assertEqual(child_a1["threshold_next"], 10)
        self.assertFalse(child_a1["eligible"])

        child_a2 = nodes["child_a2"]["progress"]
        # Expert tops out: no next rung, never eligible.
        self.assertIsNone(child_a2["next_rung"])
        self.assertIsNone(child_a2["threshold_next"])
        self.assertFalse(child_a2["eligible"])
        self.assertEqual(child_a2["score"], 1010)


class TestSkillLitChronicle(SkillProgressionApiTestBase):
    """PATCH node status: skill.lit fires on rung-up only."""

    def _patch(self, client: TestClient, node_id: str, status: str):
        etag = client.get("/api/v1/profiles/alice/skill-tree").headers["ETag"]
        return client.patch(
            f"/api/v1/profiles/alice/skill-tree/nodes/{node_id}",
            json={"status": status},
            headers={"If-Match": etag},
        )

    def test_rung_up_appends_skill_lit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client, pdir = self._setup(Path(tmp))
            response = self._patch(client, "child_a1", "learning")
            chronicle = _read_chronicle(pdir)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["changed"])
        self.assertEqual(len(chronicle), 1)
        entry = chronicle[0]
        self.assertEqual(entry["kind"], "skill.lit")
        self.assertEqual(entry["ref"], "child_a1")
        # The note carries the schema label for the briefing line.
        self.assertEqual(entry["note"], "Child A1")
        self.assertTrue(entry["date"])

    def test_lit_lands_solid_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client, pdir = self._setup(Path(tmp))
            response = self._patch(client, "root_a", "lit")
            chronicle = _read_chronicle(pdir)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "solid")
        self.assertEqual(response.json()["previous_status"], "learning")
        self.assertEqual(len(chronicle), 1)
        self.assertEqual(chronicle[0]["kind"], "skill.lit")
        self.assertEqual(chronicle[0]["ref"], "root_a")
        self.assertEqual(chronicle[0]["note"], "Root A")

    def test_downgrade_and_noop_log_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client, pdir = self._setup(Path(tmp))
            downgrade = self._patch(client, "root_a", "locked")
            noop = self._patch(client, "child_a1", "locked")
            chronicle = _read_chronicle(pdir)
        self.assertEqual(downgrade.status_code, 200)
        self.assertTrue(downgrade.json()["changed"])
        self.assertEqual(downgrade.json()["status"], "locked")
        self.assertEqual(noop.status_code, 200)
        self.assertFalse(noop.json()["changed"])
        self.assertEqual(chronicle, [])


if __name__ == "__main__":
    unittest.main()
