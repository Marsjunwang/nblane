"""Tests for Evidence Review read models."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from nblane.core.evidence_review import (
    build_evidence_review,
    evidence_status_risks,
    evidence_usage_index,
    skill_evidence_summaries,
)


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


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


if __name__ == "__main__":
    unittest.main()
