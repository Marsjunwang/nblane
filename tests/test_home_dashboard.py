"""Tests for Home dashboard read-model helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.home_dashboard import (
    dashboard_payload,
    dashboard_health_summary,
    dashboard_kanban_summary,
    dashboard_pending_evidence_summary,
    dashboard_public_summary,
    dashboard_skill_summary,
)
from nblane.core.profile_health import HealthReport


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


class TestHomeDashboard(unittest.TestCase):
    """Dashboard helpers summarize existing owner files only."""

    def _profile(self, tmp: Path) -> Path:
        profile = tmp / "alice"
        profile.mkdir()
        (profile / "kanban.md").write_text(
            "# alice · Kanban\n\n"
            "## Doing\n\n"
            "- [ ] Ship robot demo\n"
            "  - blocked by: calibration data\n"
            "- [ ] Write eval notes\n\n"
            "## Queue\n\n"
            "- [ ] Read paper\n\n"
            "## Done\n\n"
            "- [x] Finish benchmark\n"
            "  - outcome: done\n"
            "- [x] Archive old result\n"
            "  - crystallized: true\n\n"
            "## Someday / Maybe\n\n"
            "- Future idea\n",
            encoding="utf-8",
        )
        _write_yaml(
            profile / "skill-tree.yaml",
            {
                "profile": "alice",
                "schema": "robotics-engineer",
                "nodes": [
                    {"id": "ros2_basics", "status": "learning"},
                    {"id": "pose_estimation", "status": "solid"},
                    {
                        "id": "experiment_design",
                        "status": "solid",
                        "evidence_refs": ["ev_linked"],
                    },
                ],
            },
        )
        _write_yaml(
            profile / "evidence-pool.yaml",
            {
                "profile": "alice",
                "evidence_entries": [
                    {
                        "id": "ev_linked",
                        "type": "project",
                        "title": "Linked evidence",
                    },
                    {
                        "id": "ev_unused",
                        "type": "practice",
                        "title": "Needs linking",
                    },
                ],
            },
        )
        _write_yaml(
            profile / "goals.yaml",
            {
                "schema_version": "1.0",
                "profile": "alice",
                "current_goal_id": "g1",
                "goals": [
                    {
                        "id": "g1",
                        "title": "Robotics demo",
                        "status": "active",
                        "target_skills": ["ros2_basics"],
                    }
                ],
            },
        )
        _write_yaml(
            profile / "public-profile.yaml",
            {
                "profile": "alice",
                "visibility": "public",
                "public_name": "Alice",
            },
        )
        _write_yaml(
            profile / "projects.yaml",
            {
                "projects": [
                    {"id": "p1", "title": "Project", "status": "draft"}
                ]
            },
        )
        _write_yaml(profile / "outputs.yaml", {"outputs": []})
        blog_dir = profile / "blog"
        blog_dir.mkdir()
        (blog_dir / "draft.md").write_text(
            "---\ntitle: Draft\nstatus: draft\n---\n\nBody\n",
            encoding="utf-8",
        )
        return profile

    def test_kanban_summary_surfaces_doing_and_uncrystallized_done(self) -> None:
        """Kanban summary reads Doing and Done crystallization state."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            summary = dashboard_kanban_summary(profile)

        self.assertEqual(summary["doing_total"], 2)
        self.assertEqual(summary["doing"][0]["title"], "Ship robot demo")
        self.assertEqual(summary["doing"][0]["blocked_by"], "calibration data")
        self.assertEqual(summary["done_uncrystallized_count"], 1)

    def test_skill_summary_counts_risks_and_goal_targets(self) -> None:
        """Skill summary reads status, evidence risk, and current goal targets."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            summary = dashboard_skill_summary(profile)

        self.assertTrue(summary["has_tree"])
        self.assertGreater(summary["total"], 0)
        self.assertGreaterEqual(summary["counts"]["learning"], 1)
        self.assertEqual(summary["evidence_risk_count"], 1)
        self.assertEqual(summary["evidence_risk_nodes"][0]["id"], "pose_estimation")
        self.assertEqual(
            summary["target_learning_locked"][0]["id"],
            "ros2_basics",
        )

    def test_pending_evidence_summary_combines_done_and_unlinked_pool(self) -> None:
        """Evidence summary shows both Done review and unlinked pool rows."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            summary = dashboard_pending_evidence_summary(profile)

        self.assertEqual(summary["done_uncrystallized_count"], 1)
        self.assertEqual(summary["unlinked_count"], 1)
        self.assertEqual(summary["unlinked"][0]["id"], "ev_unused")

    def test_health_summary_counts_report(self) -> None:
        """Health summary is a compact view of analyze_profile_health."""
        report = HealthReport(profile="alice", can_publish_context=False)
        with patch(
            "nblane.core.home_dashboard.profile_health.analyze_profile_health",
            return_value=report,
        ):
            summary = dashboard_health_summary("alice")

        self.assertEqual(summary["counts"]["error"], 0)
        self.assertFalse(summary["context_ready"])
        self.assertEqual(summary["issues"], [])

    def test_public_summary_counts_drafts_without_building(self) -> None:
        """Public summary reads draft status and build presence only."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            summary = dashboard_public_summary(profile)

        self.assertTrue(summary["initialized"])
        self.assertEqual(summary["visibility"], "public")
        self.assertEqual(summary["draft_total"], 2)
        self.assertFalse(summary["build_exists"])

    def test_dashboard_payload_has_stable_chart_and_graph_shape(self) -> None:
        """Aggregate payload exposes stable JSON for the React component."""
        ui = {
            "quick_kanban": "Kanban",
            "quick_kanban_help": "Do work",
            "quick_skill_tree": "Skill Tree",
            "quick_skill_tree_help": "Skills",
            "quick_gap": "Gap",
            "quick_gap_help": "Analyze",
            "quick_public_site": "Public",
            "quick_public_site_help": "Output",
            "quick_profile_health": "Health",
            "quick_profile_health_help": "Check",
        }
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            payload = dashboard_payload(
                profile,
                ui=ui,
                ai={"configured": True, "label": "test-model"},
            )

        self.assertEqual(payload["profile"], "alice")
        self.assertIn("charts", payload)
        self.assertEqual(payload["charts"]["public"]["draft"], 2)
        self.assertTrue(payload["goal"]["is_set"])
        self.assertFalse(payload["goal"]["locked"])
        self.assertEqual(payload["goal"]["projection"]["visibility"], "discreet")
        self.assertEqual(payload["goal"]["editor"]["title"], "Robotics demo")
        self.assertGreaterEqual(len(payload["graph"]["nodes"]), 4)
        self.assertTrue(
            any(link["path"] == "pages/3_Kanban.py" for link in payload["quick_links"])
        )

    def test_dashboard_payload_redacts_private_goal_editor(self) -> None:
        """Private goals do not send full editable text into React."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._profile(Path(tmp_s))
            goals_path = profile / "goals.yaml"
            raw = yaml.safe_load(goals_path.read_text(encoding="utf-8"))
            raw["goals"][0]["ui_visibility"] = "private"
            raw["goals"][0]["title"] = "Sensitive title"
            _write_yaml(goals_path, raw)

            payload = dashboard_payload(profile)

        self.assertTrue(payload["goal"]["is_set"])
        self.assertTrue(payload["goal"]["locked"])
        self.assertIsNone(payload["goal"]["projection"])
        self.assertEqual(payload["goal"]["editor"], {})
        graph_text = yaml.dump(payload["graph"], allow_unicode=True)
        self.assertNotIn("Sensitive title", graph_text)

    def test_dashboard_payload_empty_profile_defaults(self) -> None:
        """Empty profiles still provide renderable fallback payload fields."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = Path(tmp_s) / "empty"
            profile.mkdir()
            payload = dashboard_payload(profile)

        self.assertEqual(payload["profile"], "empty")
        self.assertFalse(payload["goal"]["is_set"])
        self.assertEqual(payload["goal"]["editor"]["status"], "active")
        self.assertEqual(payload["charts"]["skills"]["total"], 0)
        self.assertEqual(payload["quick_links"][0]["path"], "pages/3_Kanban.py")


if __name__ == "__main__":
    unittest.main()
