"""Tests for Evidence Review read models."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from nblane.core.evidence_review import (
    apply_pool_edits,
    apply_project_ref_inferences,
    build_evidence_review,
    bulk_set_pool_field,
    evidence_status_risks,
    evidence_project_ref_candidates,
    evidence_usage_index,
    link_skill_to_evidence_nodes,
    set_evidence_skill_refs,
    skill_evidence_summaries,
)


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


class TestPoolEditHelpers(unittest.TestCase):
    """Pure helpers backing inline + bulk pool editing."""

    def test_apply_pool_edits_matches_by_id(self) -> None:
        entries = [
            {"id": "e1", "title": "A", "strength": "weak"},
            {"id": "e2", "title": "B"},
        ]
        _, changed = apply_pool_edits(
            entries,
            {
                "e1": {"strength": "strong", "review_status": "reviewed"},
                "e2": {"confidence": "high"},
            },
        )
        self.assertEqual(changed, 2)
        self.assertEqual(entries[0]["strength"], "strong")
        self.assertEqual(entries[0]["review_status"], "reviewed")
        self.assertEqual(entries[1]["confidence"], "high")

    def test_apply_pool_edits_rejects_bad_field_and_value(self) -> None:
        entries = [{"id": "e1", "strength": "medium"}]
        _, changed = apply_pool_edits(
            entries,
            {"e1": {"strength": "legendary", "id": "hacked"}},
        )
        # out-of-domain strength ignored, id is not an editable field
        self.assertEqual(changed, 0)
        self.assertEqual(entries[0]["strength"], "medium")
        self.assertEqual(entries[0]["id"], "e1")

    def test_apply_pool_edits_empty_clears_field(self) -> None:
        entries = [{"id": "e1", "strength": "strong"}]
        _, changed = apply_pool_edits(entries, {"e1": {"strength": ""}})
        self.assertEqual(changed, 1)
        self.assertNotIn("strength", entries[0])

    def test_bulk_set_pool_field(self) -> None:
        entries = [
            {"id": "e1"},
            {"id": "e2", "review_status": "reviewed"},
            {"id": "e3"},
        ]
        _, changed = bulk_set_pool_field(
            entries, ["e1", "e2", "e3"], "review_status", "reviewed"
        )
        # e2 already reviewed -> only e1, e3 change
        self.assertEqual(changed, 2)
        self.assertTrue(all(r["review_status"] == "reviewed" for r in entries))

    def test_bulk_set_pool_field_rejects_bad_value(self) -> None:
        entries = [{"id": "e1"}]
        _, changed = bulk_set_pool_field(entries, ["e1"], "strength", "nope")
        self.assertEqual(changed, 0)

    def test_link_skill_to_evidence_creates_node(self) -> None:
        nodes: list[dict] = []
        link_skill_to_evidence_nodes(nodes, "ros2_basics", ["e1", "e2"])
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["id"], "ros2_basics")
        self.assertEqual(nodes[0]["status"], "learning")
        self.assertEqual(nodes[0]["evidence_refs"], ["e1", "e2"])

    def test_link_skill_to_evidence_dedupes(self) -> None:
        nodes = [{"id": "nav2", "status": "solid", "evidence_refs": ["e1"]}]
        link_skill_to_evidence_nodes(nodes, "nav2", ["e1", "e2", "e2"])
        self.assertEqual(nodes[0]["evidence_refs"], ["e1", "e2"])
        self.assertEqual(nodes[0]["status"], "solid")  # untouched

    def test_set_evidence_skill_refs_adds_and_removes(self) -> None:
        nodes = [
            {"id": "ros2_basics", "status": "solid", "evidence_refs": ["e1"]},
            {"id": "nav2", "status": "learning", "evidence_refs": ["e1", "e9"]},
        ]
        # e1 should now belong to ros2_basics + a brand-new node, not nav2.
        set_evidence_skill_refs(nodes, "e1", ["ros2_basics", "perception"])
        by_id = {n["id"]: n for n in nodes}
        self.assertIn("e1", by_id["ros2_basics"]["evidence_refs"])
        self.assertNotIn("e1", by_id["nav2"]["evidence_refs"])
        # nav2's other ref survives.
        self.assertEqual(by_id["nav2"]["evidence_refs"], ["e9"])
        # New selected node is created as learning.
        self.assertEqual(by_id["perception"]["status"], "learning")
        self.assertEqual(by_id["perception"]["evidence_refs"], ["e1"])
        # Existing node status untouched.
        self.assertEqual(by_id["ros2_basics"]["status"], "solid")

    def test_set_evidence_skill_refs_drops_empty_evidence_refs(self) -> None:
        nodes = [{"id": "nav2", "status": "solid", "evidence_refs": ["e1"]}]
        # Unlinking the only ref should remove the key entirely.
        set_evidence_skill_refs(nodes, "e1", [])
        self.assertNotIn("evidence_refs", nodes[0])
        self.assertEqual(nodes[0]["status"], "solid")

    def test_set_evidence_skill_refs_dedupes(self) -> None:
        nodes = [{"id": "nav2", "status": "solid", "evidence_refs": ["e1", "e1"]}]
        set_evidence_skill_refs(nodes, "e2", ["nav2"])
        self.assertEqual(nodes[0]["evidence_refs"], ["e1", "e2"])


class TestEvidenceReview(unittest.TestCase):
    """Evidence Review derives queues from existing owner files."""

    def _profile(self, tmp: Path) -> Path:
        profile = tmp / "alice"
        profile.mkdir()
        (profile / "kanban.md").write_text(
            "# alice · Kanban\n\n"
            "## Done\n\n"
            "- [x] Ship demo\n"
            "  - id: done_ship\n"
            "  - outcome: shipped\n"
            "- [x] Already reviewed\n"
            "  - crystallized: true\n",
            encoding="utf-8",
        )
        _write_yaml(
            profile / "evidence-pool.yaml",
            {
                "profile": "alice",
                "evidence_entries": [
                    {
                        "id": "ev_weak",
                        "type": "project",
                        "title": "Weak project note",
                        "strength": "weak",
                        "review_status": "reviewed",
                    },
                    {
                        "id": "ev_medium",
                        "type": "project",
                        "title": "Medium project note",
                        "strength": "medium",
                        "review_status": "reviewed",
                        "project_refs": ["project:demo"],
                        "experience_refs": ["experience:robotics-lab"],
                        "source_refs": ["source:research:20260513-001"],
                    },
                    {
                        "id": "ev_unlinked",
                        "type": "practice",
                        "title": "Needs review",
                    },
                    {
                        "id": "ev_old",
                        "type": "practice",
                        "title": "Deprecated",
                        "deprecated": True,
                    },
                ],
                "claims": [
                    {
                        "id": "claim:demo",
                        "status": "accepted",
                        "type": "achievement",
                        "text": "Demo claim.",
                        "evidence_refs": ["ev_medium"],
                        "skill_refs": ["experiment_design"],
                        "project_refs": ["project:demo"],
                        "experience_refs": ["experience:robotics-lab"],
                    }
                ],
            },
        )
        _write_yaml(
            profile / "skill-tree.yaml",
            {
                "profile": "alice",
                "schema": "robotics-engineer",
                "nodes": [
                    {"id": "ros2_basics", "status": "solid"},
                    {
                        "id": "pose_estimation",
                        "status": "solid",
                        "evidence_refs": ["ev_weak"],
                    },
                    {
                        "id": "experiment_design",
                        "status": "expert",
                        "evidence_refs": ["ev_medium"],
                    },
                    {
                        "id": "sim2real",
                        "status": "learning",
                        "evidence_refs": ["ev_old"],
                    },
                ],
            },
        )
        _write_yaml(
            profile / "project-board.yaml",
            {
                "schema_version": "1.0",
                "profile": "alice",
                "project_cases": [
                    {
                        "id": "project:demo",
                        "title": "Demo Project",
                        "status": "active",
                    }
                ],
            },
        )
        _write_yaml(
            profile / "experience.yaml",
            {
                "schema_version": "1.0",
                "profile": "alice",
                "experience_cases": [
                    {
                        "id": "experience:robotics-lab",
                        "organization": "Robotics Lab",
                        "role": "Engineer",
                        "status": "active",
                    }
                ],
            },
        )
        (profile / "research").mkdir()
        _write_yaml(
            profile / "research" / "sources.yaml",
            {
                "schema_version": "1.0",
                "profile": "alice",
                "sources": [
                    {
                        "id": "source:research:20260513-001",
                        "kind": "paper",
                        "title": "Demo source",
                        "status": "inbox",
                    }
                ],
            },
        )
        return profile

    def test_build_evidence_review_counts_derived_queues(self) -> None:
        """Done, unlinked, needs-review, and status-risk counts are derived."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            review = build_evidence_review(profile)

        summary = review["summary"]
        self.assertEqual(summary["done_uncrystallized_count"], 1)
        self.assertEqual(summary["unlinked_count"], 1)
        self.assertEqual(summary["needs_review_count"], 1)
        self.assertEqual(summary["status_risk_count"], 3)
        self.assertEqual(review["unlinked"][0]["id"], "ev_unlinked")
        self.assertEqual(review["needs_review"][0]["strength"], "unrated")
        medium = next(
            row for row in review["evidence_rows"] if row["id"] == "ev_medium"
        )
        self.assertEqual(medium["project_refs"], ["project:demo"])
        self.assertEqual(medium["experience_refs"], ["experience:robotics-lab"])
        self.assertEqual(
            medium["source_refs"],
            ["source:research:20260513-001"],
        )
        self.assertEqual(medium["claim_refs"], ["claim:demo"])
        self.assertEqual(
            review["claim_usage"]["by_skill"]["experiment_design"][0]["id"],
            "claim:demo",
        )
        self.assertEqual(review["project_options"][0]["id"], "project:demo")
        self.assertEqual(
            review["experience_options"][0]["id"],
            "experience:robotics-lab",
        )
        self.assertEqual(
            review["source_options"][0]["id"],
            "source:research:20260513-001",
        )
        self.assertFalse(
            any(row["id"] == "ev_old" for row in review["evidence_rows"])
        )

    def test_evidence_skill_suggestions_rank_and_exclude_linked(self) -> None:
        """Rule recall suggests skills by text overlap, excluding linked ones."""
        from nblane.core.evidence_review import (
            build_evidence_editor_payload,
            evidence_skill_suggestions,
        )

        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            sugg = evidence_skill_suggestions(profile)
            payload = build_evidence_editor_payload(profile)

        # ev_medium is linked to experiment_design -> excluded from its own list.
        med = sugg.get("ev_medium") or []
        self.assertNotIn("experiment_design", [s["id"] for s in med])
        # Suggestions are ranked by score descending and tagged rule source.
        for items in sugg.values():
            scores = [s["score"] for s in items]
            self.assertEqual(scores, sorted(scores, reverse=True))
            self.assertTrue(all(s["source"] == "rule" for s in items))
        # The editor payload threads per-row suggestions onto each row.
        rows = {r["id"]: r for r in payload["evidence_rows"]}
        self.assertIn("skill_suggestions", rows["ev_medium"])

    def test_project_ref_candidates_infer_from_kanban_tasks(self) -> None:
        """Reviewed evidence can inherit project refs from live/archive tasks."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = Path(tmp_s) / "alice"
            profile.mkdir()
            (profile / "kanban.md").write_text(
                "# alice · Kanban\n\n"
                "## Done\n\n"
                "- [x] Live demo\n"
                "  - id: task_live\n"
                "  - project_id: project:demo\n"
                "- [x] Other project\n"
                "  - id: task_other\n"
                "  - project_id: project:other\n"
                "- [x] No project\n"
                "  - id: task_no_project\n",
                encoding="utf-8",
            )
            (profile / "kanban-archive.md").write_text(
                "# alice · Kanban archive\n\n"
                "## Archived · 2026-05-01\n\n"
                "- [x] Archived demo\n"
                "  - id: task_arch\n"
                "  - project_id: project:archive\n",
                encoding="utf-8",
            )
            entries = [
                {
                    "id": "ev_live",
                    "title": "Live evidence",
                    "review_status": "reviewed",
                    "kanban_refs": ["kanban:task_live"],
                },
                {
                    "id": "ev_arch",
                    "title": "Archived evidence",
                    "review_status": "reviewed",
                    "kanban_refs": ["kanban:task_arch"],
                },
                {
                    "id": "ev_conflict",
                    "title": "Conflict evidence",
                    "review_status": "reviewed",
                    "kanban_refs": ["kanban:task_live", "kanban:task_other"],
                },
                {
                    "id": "ev_no_project",
                    "title": "No project evidence",
                    "review_status": "reviewed",
                    "kanban_refs": ["kanban:task_no_project"],
                },
                {
                    "id": "ev_existing",
                    "title": "Already linked",
                    "review_status": "reviewed",
                    "project_refs": ["project:existing"],
                    "kanban_refs": ["kanban:task_live"],
                },
                {
                    "id": "ev_needs_review",
                    "title": "Not reviewed",
                    "kanban_refs": ["kanban:task_live"],
                },
            ]
            _write_yaml(
                profile / "evidence-pool.yaml",
                {"profile": "alice", "evidence_entries": entries},
            )

            candidates = evidence_project_ref_candidates(profile)
            by_id = {str(item["id"]): item for item in candidates}
            entries, changed = apply_project_ref_inferences(
                entries,
                candidates,
                ["ev_live", "ev_arch", "ev_conflict", "ev_no_project"],
            )

        self.assertEqual(
            set(by_id),
            {"ev_live", "ev_arch", "ev_conflict", "ev_no_project"},
        )
        self.assertEqual(by_id["ev_live"]["status"], "single_project")
        self.assertEqual(
            by_id["ev_live"]["inferred_project_refs"],
            ["project:demo"],
        )
        self.assertEqual(
            by_id["ev_arch"]["inferred_project_refs"],
            ["project:archive"],
        )
        self.assertEqual(by_id["ev_conflict"]["status"], "multiple_projects")
        self.assertEqual(
            by_id["ev_conflict"]["inferred_project_refs"],
            ["project:demo", "project:other"],
        )
        self.assertEqual(by_id["ev_no_project"]["status"], "no_project")
        self.assertEqual(changed, 2)
        updated = {str(row["id"]): row for row in entries}
        self.assertEqual(updated["ev_live"]["project_refs"], ["project:demo"])
        self.assertEqual(updated["ev_arch"]["project_refs"], ["project:archive"])
        self.assertNotIn("project_refs", updated["ev_conflict"])
        self.assertNotIn("project_refs", updated["ev_no_project"])

    def test_usage_index_tracks_skill_refs(self) -> None:
        """Evidence ids reverse-map to linked skill nodes."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            usage = evidence_usage_index(profile)

        self.assertEqual(usage["ev_weak"][0]["id"], "pose_estimation")
        self.assertEqual(usage["ev_medium"][0]["id"], "experiment_design")

    def test_skill_evidence_summaries_include_strength_signals(self) -> None:
        """Skill summaries expose count, highest strength, and review state."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            summaries = {
                item["id"]: item
                for item in skill_evidence_summaries(profile)
            }

        pose = summaries["pose_estimation"]
        self.assertEqual(pose["evidence_count"], 1)
        self.assertEqual(pose["highest_strength"], "weak")
        self.assertEqual(pose["review_status"], "reviewed")
        self.assertEqual(pose["risk_level"], "insufficient_strength")
        self.assertEqual(summaries["ros2_basics"]["risk_level"], "missing_evidence")

    def test_status_risks_apply_v1_strength_thresholds(self) -> None:
        """solid needs medium+; expert needs strong+."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            risks = {
                item["id"]: item
                for item in evidence_status_risks(profile)
            }

        self.assertEqual(risks["ros2_basics"]["required_strength"], "medium")
        self.assertEqual(risks["pose_estimation"]["required_strength"], "medium")
        self.assertEqual(
            risks["experiment_design"]["required_strength"],
            "strong",
        )

    def test_page_exposes_done_housekeeping_workbench(self) -> None:
        """Evidence Review owns Done batch cleanup and writeback activity."""
        source = Path("pages/2_Evidence_Review.py").read_text(encoding="utf-8")

        self.assertIn("_render_done_housekeeping", source)
        self.assertIn("archive_kanban_done_tasks", source)
        self.assertIn("sync_project_board_from_kanban", source)
        self.assertIn("done_housekeeping_confirm_delete", source)
        self.assertIn("record_writeback_activity", source)
        self.assertIn("kanban_ai_backend(selected)", source)

    def test_page_exposes_claim_studio_scopes(self) -> None:
        """Claim Studio exposes all generation scopes via the scope selector."""
        source = Path("pages/2_Evidence_Review.py").read_text(encoding="utf-8")

        self.assertIn("_render_claim_studio", source)
        self.assertIn('options=["project", "goal", "skill", "all", "manual"]', source)
        self.assertIn("claim_generate_scope_label", source)
        self.assertIn("_render_claim_scope_generator", source)
        self.assertIn("_render_claim_manual", source)
        self.assertIn("generate_claim_candidates_for_scope", source)
        self.assertIn("apply_claim_candidates_to_book", source)
        self.assertIn("migrate_legacy_claims", source)

    def test_page_exposes_project_ref_backfill(self) -> None:
        """Project-ref backfill is owned by Evidence Review, not Project Board."""
        source = Path("pages/2_Evidence_Review.py").read_text(encoding="utf-8")

        self.assertIn("_render_project_ref_backfill", source)
        self.assertIn("apply_project_ref_inferences", source)
        self.assertIn("refs_project_backfill_title", source)


if __name__ == "__main__":
    unittest.main()
