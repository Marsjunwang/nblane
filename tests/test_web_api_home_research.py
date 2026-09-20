"""Tests for the M4 Home and Research overview endpoints of the FastAPI backend."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.web_api import app

KANBAN_MD = """# alice · Kanban

> Updated: 2026-09-19

---

## Doing

- [ ] Build robot arm
  - id: kb_doing1
  - started_on: 2026-09-01

---

## Done

- [x] Setup repo
  - id: kb_done1
  - completed_on: 2026-09-18

---

## Queue

- (empty)

---

## Someday / Maybe

- (empty)

---
"""

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
        },
        {
            "id": "goal_done",
            "title": "Old goal",
            "status": "completed",
        },
    ],
}

EVIDENCE_POOL = {
    "profile": "alice",
    "evidence_entries": [
        {
            "id": "ev_1",
            "type": "project",
            "title": "Built ROS2 pick demo",
            "date": "2026-08-20",
            "review_status": "reviewed",
        },
        {
            "id": "ev_2",
            "type": "learning",
            "title": "MoveIt2 workshop notes",
            "date": "2026-07-15",
        },
    ],
}

AGENT_ACTIVITY = {
    "schema_version": "1.0",
    "profile": "alice",
    "items": [
        {
            "id": "act:candidate:aaa",
            "kind": "candidate",
            "candidate_type": "agent_dispatch",
            "target_owner": "kanban",
            "status": "pending",
            "title": "Pending candidate",
            "updated": "2026-09-18T10:00:00+00:00",
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

RESEARCH_SOURCES = {
    "schema_version": "1.0",
    "profile": "alice",
    "updated": "2026-09-19",
    "sources": [
        {
            "id": "src:001",
            "title": "SLAM survey",
            "kind": "paper",
            "status": "reading",
            "url": "https://example.org/slam",
            "captured_at": "2026-09-18",
            "tags": ["robotics"],
        },
        {
            "id": "src:002",
            "title": " grasp tooling post",
            "kind": "web",
            "status": "inbox",
            "captured_at": "2026-09-19",
        },
        {
            "id": "src:003",
            "title": "Archived reference",
            "kind": "paper",
            "status": "archived",
            "captured_at": "2026-08-01",
        },
    ],
}

RESEARCH_CLAIMS = {
    "schema_version": "1.0",
    "profile": "alice",
    "claims": [
        {
            "id": "rclaim:20260919:001",
            "text": "SLAM pipelines degrade under low light",
            "status": "draft",
            "type": "learning",
            "source_refs": ["src:001"],
            "human_note": False,
        },
    ],
}

RESEARCH_CITATIONS = {
    "schema_version": "1.0",
    "profile": "alice",
    "citations": [
        {
            "id": "rcite:001",
            "claim_id": "rclaim:20260919:001",
            "source_id": "src:001",
            "locator": "p.3",
        },
    ],
}


def _write_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    (profile / "research").mkdir(parents=True)
    (profile / "kanban.md").write_text(
        KANBAN_MD.replace("alice", name), encoding="utf-8"
    )
    (profile / "SKILL.md").write_text(
        SKILL_MD.replace("alice", name), encoding="utf-8"
    )

    def _dump(filename: str, doc: dict) -> None:
        data = dict(doc)
        data["profile"] = name
        (profile / filename).write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    _dump("goals.yaml", GOALS)
    _dump("evidence-pool.yaml", EVIDENCE_POOL)
    _dump("agent-activity.yaml", AGENT_ACTIVITY)
    _dump("research/sources.yaml", RESEARCH_SOURCES)
    _dump("research/claims.yaml", RESEARCH_CLAIMS)
    _dump("research/citations.yaml", RESEARCH_CITATIONS)
    return profile


class _HomeResearchBase(unittest.TestCase):
    def _client(self, root: Path, env: dict[str, str] | None = None) -> TestClient:
        # Loaders resolve profile dirs through profile_io; parts of
        # home_dashboard go through the core.io compat facade, so patch both.
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        if env is not None:
            patcher = patch.dict(os.environ, env)
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(app)


class TestHomeEndpoint(_HomeResearchBase):
    def test_home_aggregates_dashboard_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/home")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        # North Star from SKILL.md identity.
        self.assertTrue(payload["north_star"]["is_set"])
        self.assertEqual(payload["north_star"]["brief"], "Ship real robot demos")
        # Primary goal with derived progress fields.
        goal = payload["primary_goal"]
        self.assertEqual(goal["id"], "goal_main")
        self.assertEqual(goal["title"], "Ship the pick-and-place demo")
        self.assertEqual(goal["target"], "2026-12-31")
        self.assertIn("progress", goal)
        self.assertFalse(goal["stalled"])
        self.assertEqual(payload["goal_counts"], {"active": 1, "total": 2})
        # Kanban section counts + Doing strip.
        self.assertEqual(payload["kanban"]["doing_total"], 1)
        self.assertEqual(
            [t["id"] for t in payload["kanban"]["doing"]], ["kb_doing1"]
        )
        self.assertEqual(payload["kanban"]["counts"].get("Done"), 1)
        # Evidence attention counters (both rows are unrated → needs review).
        evidence = payload["evidence"]
        self.assertEqual(evidence["total_entries"], 2)
        self.assertEqual(evidence["needs_review_count"], 2)
        # Research source counters (reading + inbox are active).
        self.assertEqual(payload["sources"]["total"], 3)
        self.assertEqual(payload["sources"]["active_total"], 2)
        # Agent activity queue counters.
        self.assertEqual(payload["agent_activity"]["total"], 2)
        self.assertEqual(payload["agent_activity"]["pending_total"], 1)
        self.assertEqual(
            payload["agent_activity"]["pending_titles"], ["Pending candidate"]
        )
        # Skills / health / projects / claims blocks are present.
        self.assertIn("has_tree", payload["skills"])
        self.assertIn("counts", payload["health"])
        self.assertIn("total", payload["projects"])
        self.assertIn("accepted_count", payload["claims"])

    def test_home_sidecar_defaults_to_local_reader_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root, env={"NBLANE_READER_API_BASE": ""})
            response = client.get("/api/v1/profiles/alice/home")
        sidecar = response.json()["sidecar"]
        self.assertEqual(sidecar["base"], "http://127.0.0.1:8502")
        self.assertFalse(sidecar["configured"])
        self.assertFalse(sidecar["auth_enabled"])
        self.assertEqual(sidecar["handoff_token"], "")
        self.assertEqual(
            sidecar["dashboard_url"],
            "http://127.0.0.1:8502/dashboard?profile=alice&embed=1",
        )

    def test_home_sidecar_same_origin_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root, env={"NBLANE_READER_API_BASE": "0"})
            response = client.get("/api/v1/profiles/alice/home")
        sidecar = response.json()["sidecar"]
        self.assertEqual(sidecar["base"], "")
        self.assertTrue(sidecar["configured"])
        self.assertEqual(
            sidecar["dashboard_url"], "/dashboard?profile=alice&embed=1"
        )
        self.assertEqual(
            sidecar["paper_library_url"], "/paper-library?profile=alice"
        )

    def test_home_sidecar_configured_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(
                root, env={"NBLANE_READER_API_BASE": "https://reader.example.com/"}
            )
            response = client.get("/api/v1/profiles/alice/home")
        sidecar = response.json()["sidecar"]
        self.assertEqual(sidecar["base"], "https://reader.example.com")
        self.assertTrue(sidecar["configured"])
        self.assertTrue(
            sidecar["dashboard_url"].startswith(
                "https://reader.example.com/dashboard?"
            )
        )

    def test_home_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/nobody/home")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "profile_not_found")


class TestResearchEndpoint(_HomeResearchBase):
    def test_research_summary_counts_and_recent_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/research")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        summary = payload["summary"]
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["active_total"], 2)
        self.assertEqual(
            summary["status_counts"], {"reading": 1, "inbox": 1, "archived": 1}
        )
        self.assertEqual(summary["kind_counts"], {"paper": 2, "web": 1})
        self.assertEqual(summary["claims_total"], 1)
        self.assertEqual(summary["citations_total"], 1)
        # Recent sources are captured_at-desc (newest first).
        ids = [s["id"] for s in payload["sources"]]
        self.assertEqual(ids, ["src:002", "src:001", "src:003"])
        first = payload["sources"][0]
        self.assertEqual(first["kind"], "web")
        self.assertEqual(first["status"], "inbox")
        self.assertEqual(first["captured_at"], "2026-09-19")

    def test_research_sidecar_links_carry_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root, env={"NBLANE_READER_API_BASE": ""})
            response = client.get("/api/v1/profiles/alice/research")
        sidecar = response.json()["sidecar"]
        self.assertEqual(
            sidecar["paper_library_url"],
            "http://127.0.0.1:8502/paper-library?profile=alice",
        )
        self.assertEqual(
            sidecar["dashboard_url"],
            "http://127.0.0.1:8502/dashboard?profile=alice&embed=1",
        )

    def test_research_empty_profile_returns_zeroed_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "alice"
            profile.mkdir(parents=True)
            (profile / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/research")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["summary"]["total"], 0)
        self.assertEqual(payload["summary"]["claims_total"], 0)
        self.assertEqual(payload["summary"]["citations_total"], 0)
        self.assertEqual(payload["sources"], [])

    def test_research_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/nobody/research")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "profile_not_found")


if __name__ == "__main__":
    unittest.main()
