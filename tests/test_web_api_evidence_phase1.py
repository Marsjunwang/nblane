"""Tests for the Phase 1 evidence-domain endpoints (single Evidence page).

Covers the single-entry edit/review mutations, skill link/unlink, tiered
skill suggestions, the five-stage counters, and the crystallize
candidates/draft/apply flow. LLM tiers are disabled in tests (patched
``is_configured``) so no network is hit.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core.kanban_io import render_kanban
from nblane.core.models import KanbanTask
from nblane.web_api import app

EVIDENCE_POOL = {
    "profile": "alice",
    "evidence_entries": [
        {"id": "ev_alpha", "type": "project", "title": "Alpha", "strength": "strong"},
        {
            "id": "ev_beta",
            "type": "practice",
            "title": "ROS2 SLAM navigation tuning",
            "summary": "Tuned the ROS2 navigation stack and lidar SLAM pipeline.",
            "origin": "kanban_task",
            "review_status": "reviewed",
            "strength": "medium",
            "kanban_refs": ["kanban:taskA", "kanban:taskGone"],
        },
        {"id": "ev_gamma", "type": "paper", "title": "Gamma", "deprecated": True},
    ],
}

SKILL_TREE = {
    "profile": "alice",
    "schema": "robotics-engineer",
    "updated": "2026-09-10",
    "nodes": [
        {"id": "ros2_basics", "status": "solid", "evidence_refs": ["ev_beta"]},
        {"id": "slam_basics", "status": "expert"},
    ],
}


def _write_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "evidence-pool.yaml").write_text(
        yaml.safe_dump(dict(EVIDENCE_POOL, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "skill-tree.yaml").write_text(
        yaml.safe_dump(dict(SKILL_TREE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    done_tasks = [
        KanbanTask(
            title="Tuned latency",
            id="taskA",
            done=True,
            completed_on="2026-01-02",
            context="perf sprint",
            why="cut frame time",
        ),
        KanbanTask(
            title="Already done",
            id="taskB",
            done=True,
            completed_on="2025-12-01",
            crystallized=True,
        ),
    ]
    (profile / "kanban.md").write_text(
        render_kanban(name, {"Done": done_tasks}), encoding="utf-8"
    )
    return profile


def _pool_entries(profile: Path) -> list[dict]:
    raw = yaml.safe_load(
        (profile / "evidence-pool.yaml").read_text(encoding="utf-8")
    )
    return list(raw.get("evidence_entries") or [])


def _tree_nodes(profile: Path) -> list[dict]:
    raw = yaml.safe_load((profile / "skill-tree.yaml").read_text(encoding="utf-8"))
    return list(raw.get("nodes") or [])


class Phase1TestBase(unittest.TestCase):
    """Shared env patching: profile roots, git-backup isolation, no LLM."""

    def _client(self, root: Path) -> TestClient:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch("nblane.core.profile_io.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        # Force the deterministic rule tier; no network in tests.
        patcher = patch("nblane.core.llm.is_configured", lambda: False)
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)


class TestEvidenceEdit(Phase1TestBase):
    def test_edit_whitelist_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/edit",
                json={"fields": {"title": "Alpha v2", "confidence": "high"}},
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["changed"], 1)
            row = next(r for r in _pool_entries(profile) if r["id"] == "ev_alpha")
            self.assertEqual(row["title"], "Alpha v2")
            self.assertEqual(row["confidence"], "high")
            self.assertEqual(row["strength"], "strong")

    def test_edit_rejects_unknown_field_and_bad_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            bad_field = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/edit",
                json={"fields": {"original_content": "tampered"}},
            )
            self.assertEqual(bad_field.status_code, 422)
            self.assertEqual(bad_field.json()["code"], "invalid_edit_field")
            bad_value = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/edit",
                json={"fields": {"strength": "mega"}},
            )
            self.assertEqual(bad_value.status_code, 422)
            self.assertEqual(bad_value.json()["code"], "invalid_edit_value")
            missing = client.post(
                "/api/v1/profiles/alice/evidence/ev_nope/edit",
                json={"fields": {"title": "x"}},
            )
            self.assertEqual(missing.status_code, 404)

    def test_edit_etag_precondition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            stale = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/edit",
                json={"fields": {"title": "x"}},
                headers={"If-Match": 'W/"stale"'},
            )
            self.assertEqual(stale.status_code, 412)
            self.assertTrue(stale.headers["ETag"].startswith('W/"'))


class TestConfidenceDerivation(unittest.TestCase):
    """置信度按 origin 自动推导(评审收敛单维度「分量」)。"""

    def test_mapping(self) -> None:
        from nblane.core.evidence_review import confidence_for_origin

        self.assertEqual(confidence_for_origin("paper"), "high")
        self.assertEqual(confidence_for_origin("research_source"), "high")
        self.assertEqual(confidence_for_origin("kanban_task"), "medium")
        self.assertEqual(confidence_for_origin("manual_daily"), "medium")
        self.assertEqual(confidence_for_origin("resume_parse"), "low")
        self.assertEqual(confidence_for_origin(""), "low")


class TestEvidenceEntryReview(Phase1TestBase):
    def test_accept_with_grades(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/review",
                json={
                    "action": "accept",
                    "confidence": "medium",
                    "public_readiness": "draftable",
                },
            )
            self.assertEqual(response.status_code, 200, response.text)
            row = next(r for r in _pool_entries(profile) if r["id"] == "ev_alpha")
            self.assertEqual(row["review_status"], "reviewed")
            self.assertEqual(row["confidence"], "medium")
            self.assertEqual(row["public_readiness"], "draftable")

    def test_accept_auto_derives_confidence_from_origin(self) -> None:
        """Accept without an explicit grade fills confidence by origin."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            client = self._client(root)
            # ev_beta: kanban_task origin -> medium; explicit grade wins.
            response = client.post(
                "/api/v1/profiles/alice/evidence/ev_beta/review",
                json={"action": "accept"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            row = next(r for r in _pool_entries(profile) if r["id"] == "ev_beta")
            self.assertEqual(row["confidence"], "medium")
            # ev_alpha has no origin -> low; and its pre-existing confidence
            # must not be clobbered (set one first via edit).
            client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/edit",
                json={"fields": {"confidence": "high"}},
            )
            client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/review",
                json={"action": "accept"},
            )
            row = next(r for r in _pool_entries(profile) if r["id"] == "ev_alpha")
            self.assertEqual(row["confidence"], "high")

    def test_reject_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            client = self._client(root)
            reject = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/review",
                json={"action": "reject"},
            )
            self.assertEqual(reject.status_code, 200)
            row = next(r for r in _pool_entries(profile) if r["id"] == "ev_alpha")
            self.assertTrue(row["deprecated"])
            restore = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/review",
                json={"action": "restore"},
            )
            self.assertEqual(restore.status_code, 200)
            row = next(r for r in _pool_entries(profile) if r["id"] == "ev_alpha")
            self.assertNotIn("deprecated", row)

    def test_invalid_action_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/review",
                json={"action": "nuke"},
            )
            self.assertEqual(response.status_code, 422)


class TestEvidenceSkillLinks(Phase1TestBase):
    def test_link_unlink_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            client = self._client(root)
            # Link ev_alpha to two nodes (one pre-existing, one new).
            link = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/skill-links",
                json={"skill_ids": ["ros2_basics", "custom_new_skill"]},
            )
            self.assertEqual(link.status_code, 200, link.text)
            nodes = {n["id"]: n for n in _tree_nodes(profile)}
            self.assertIn("ev_alpha", nodes["ros2_basics"]["evidence_refs"])
            # New nodes are created as learning.
            self.assertEqual(nodes["custom_new_skill"]["status"], "learning")
            self.assertEqual(nodes["custom_new_skill"]["evidence_refs"], ["ev_alpha"])

            # Unlink from ros2_basics by omitting it; ev_beta stays put.
            unlink = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/skill-links",
                json={"skill_ids": ["custom_new_skill"]},
            )
            self.assertEqual(unlink.status_code, 200)
            nodes = {n["id"]: n for n in _tree_nodes(profile)}
            self.assertNotIn("ev_alpha", nodes["ros2_basics"].get("evidence_refs", []))
            self.assertEqual(nodes["ros2_basics"]["evidence_refs"], ["ev_beta"])

    def test_unknown_entry_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/evidence/ev_nope/skill-links",
                json={"skill_ids": ["ros2_basics"]},
            )
            self.assertEqual(response.status_code, 404)

    def test_success_returns_fresh_etag_and_412_is_chinese(self) -> None:
        """Consecutive mutations: the success response hands back the new
        tree ETag (clients write it into their cache), and the 412 copy is
        Chinese and actionable."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            first = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/skill-links",
                json={"skill_ids": ["ros2_basics"]},
            )
            self.assertEqual(first.status_code, 200)
            fresh = first.headers.get("ETag", "")
            self.assertTrue(fresh.startswith('W/"'))
            # Following the fresh ETag succeeds again (consecutive op).
            second = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/skill-links",
                json={"skill_ids": ["ros2_basics"]},
                headers={"If-Match": fresh},
            )
            self.assertEqual(second.status_code, 200, second.text)
            # A stale one is rejected with the Chinese, retry-guiding copy.
            stale = client.post(
                "/api/v1/profiles/alice/evidence/ev_alpha/skill-links",
                json={"skill_ids": []},
                headers={"If-Match": 'W/"stale"'},
            )
            self.assertEqual(stale.status_code, 412)
            self.assertEqual(stale.json()["code"], "etag_mismatch")
            self.assertIn("刷新", stale.json()["message"])


class TestEvidenceSkillSuggestions(Phase1TestBase):
    def test_rule_tier_suggestions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get(
                "/api/v1/profiles/alice/evidence/ev_beta/skill-suggestions"
            )
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            self.assertEqual(payload["backend"], "rule")
            self.assertEqual(payload["entry_id"], "ev_beta")
            # Already-linked nodes (ros2_basics) are excluded.
            ids = [item["id"] for item in payload["suggestions"]]
            self.assertNotIn("ros2_basics", ids)
            self.assertLessEqual(len(ids), 5)

    def test_unknown_entry_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get(
                "/api/v1/profiles/alice/evidence/ev_nope/skill-suggestions"
            )
            self.assertEqual(response.status_code, 404)


class TestEvidenceStages(Phase1TestBase):
    def test_five_stage_counters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/evidence-stages")
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            # taskA uncrystallized; taskB crystallized.
            self.assertEqual(payload["pending_crystallize_count"], 1)
            # ev_alpha needs review; ev_beta reviewed.
            self.assertEqual(payload["needs_review_count"], 1)
            # ev_beta is reviewed and linked to ros2_basics.
            self.assertEqual(payload["seated_count"], 1)
            self.assertEqual(payload["deprecated_count"], 1)
            # navigation is expert with no evidence -> 待补强 risk.
            risk_ids = [r["skill_id"] for r in payload["risks"]]
            self.assertIn("slam_basics", risk_ids)
            self.assertEqual(payload["strengthen_count"], len(payload["risks"]))


class TestCrystallizeFlow(Phase1TestBase):
    def test_candidates_list_uncrystallized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/crystallize/candidates")
            self.assertEqual(response.status_code, 200, response.text)
            items = response.json()["items"]
            self.assertEqual([item["id"] for item in items], ["taskA"])
            # No project link -> advisory blocker present.
            self.assertTrue(items[0]["blockers"])

    def test_candidates_carry_inscription_fields(self) -> None:
        """Candidate cards need context/why/outcome + the原文 snapshot preview."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/crystallize/candidates")
            item = response.json()["items"][0]
            self.assertEqual(item["context"], "perf sprint")
            self.assertEqual(item["why"], "cut frame time")
            self.assertIn("Tuned latency", item["snapshot"])
            self.assertIn("cut frame time", item["snapshot"])

    def test_rule_draft_snapshots_task_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/crystallize/draft",
                json={"task_ids": ["taskA"]},
            )
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            self.assertEqual(payload["backend"], "rule")
            rows = payload["patch"]["evidence_entries"]
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["title"], "Tuned latency")
            self.assertEqual(row["origin"], "kanban_task")
            self.assertEqual(row["kanban_refs"], ["kanban:taskA"])
            self.assertIn("cut frame time", row["original_content"])
            self.assertTrue(row["original_content_hash"].startswith("sha256:"))
            self.assertEqual(payload["tasks"][0]["id"], "taskA")

    def test_draft_empty_selection_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/crystallize/draft",
                json={"task_ids": ["archived-task"]},
            )
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()["code"], "empty_selection")

    def test_apply_writes_pool_and_marks_crystallized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            client = self._client(root)
            draft = client.post(
                "/api/v1/profiles/alice/crystallize/draft",
                json={"task_ids": ["taskA"]},
            ).json()
            apply = client.post(
                "/api/v1/profiles/alice/crystallize/apply",
                json={"patch": draft["patch"], "task_ids": ["taskA"]},
            )
            self.assertEqual(apply.status_code, 200, apply.text)
            payload = apply.json()
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["crystallized_count"], 1)
            self.assertEqual(len(payload["new_evidence_ids"]), 1)
            rows = _pool_entries(profile)
            new_id = payload["new_evidence_ids"][0]
            row = next(r for r in rows if r["id"] == new_id)
            self.assertEqual(row["kanban_refs"], ["kanban:taskA"])
            # 置信度按 origin 自动推导(kanban_task -> medium)。
            self.assertEqual(row["confidence"], "medium")
            # The Done task is now crystallized in kanban.md.
            text = (profile / "kanban.md").read_text(encoding="utf-8")
            done_section = text.split("## Done", 1)[1]
            self.assertIn("crystallized: true", done_section)


class TestEvidenceDetailEnrichment(Phase1TestBase):
    def test_detail_carries_skill_refs_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/evidence/ev_beta")
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            self.assertEqual(payload["skill_refs"], ["ros2_basics"])
            details = {d["ref"]: d for d in payload["kanban_ref_details"]}
            self.assertEqual(details["kanban:taskA"]["status"], "linked")
            self.assertEqual(details["kanban:taskA"]["title"], "Tuned latency")
            # Dead ref -> archived tombstone, not an error.
            self.assertEqual(details["kanban:taskGone"]["status"], "archived")


if __name__ == "__main__":
    unittest.main()
