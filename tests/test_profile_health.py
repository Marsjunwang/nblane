"""Tests for deterministic profile health reports."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.profile_health import (
    HealthIssue,
    HealthReport,
    analyze_profile_health,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"


class TestProfileHealth(unittest.TestCase):
    """Profile health checks without mutating source profiles."""

    def _template_profile(self, tmp: Path, name: str = "h") -> Path:
        profile = tmp / name
        shutil.copytree(TEMPLATE_DIR, profile)
        for file_path in profile.rglob("*"):
            if file_path.is_file():
                text = file_path.read_text(encoding="utf-8")
                text = text.replace("{Name}", name)
                text = text.replace("{YYYY-MM-DD}", "2026-03-21")
                file_path.write_text(text, encoding="utf-8")
        return profile

    def test_validate_error_blocks_context_publish(self) -> None:
        """validate errors make can_publish_context false."""
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            profile = tmp / "bad"
            profile.mkdir()
            (profile / "SKILL.md").write_text("# bad\n", encoding="utf-8")
            with patch(
                "nblane.core.profile_health.profile_dir",
                lambda _name: profile,
            ):
                report = analyze_profile_health("bad")
        self.assertFalse(report.can_publish_context)
        self.assertTrue(
            any(i.category == "validate" for i in report.issues)
        )

    def test_sync_drift_is_reported(self) -> None:
        """Generated block drift creates a sync issue."""
        from nblane.core.sync import write_generated_blocks

        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._template_profile(Path(tmp_s), "syncuser")
            write_generated_blocks(profile)
            skill_md = profile / "SKILL.md"
            content = skill_md.read_text(encoding="utf-8")
            skill_md.write_text(
                content.replace(
                    "<!-- BEGIN GENERATED:skill_tree -->\n",
                    "<!-- BEGIN GENERATED:skill_tree -->\n"
                    "- [x] manual drift\n",
                    1,
                ),
                encoding="utf-8",
            )
            with patch(
                "nblane.core.profile_health.profile_dir",
                lambda _name: profile,
            ):
                report = analyze_profile_health("syncuser")
        self.assertFalse(report.can_publish_context)
        self.assertTrue(any(i.category == "sync" for i in report.issues))

    def test_solid_node_without_evidence_warns(self) -> None:
        """solid/expert nodes without resolved evidence are warned."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._template_profile(Path(tmp_s), "evuser")
            tree = {
                "profile": "evuser",
                "schema": "robotics-engineer",
                "updated": "2026-03-21",
                "nodes": [
                    {"id": "ros2_basics", "status": "solid"},
                ],
            }
            (profile / "skill-tree.yaml").write_text(
                yaml.dump(tree, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            with patch(
                "nblane.core.profile_health.profile_dir",
                lambda _name: profile,
            ):
                report = analyze_profile_health("evuser")
        self.assertTrue(any(i.category == "evidence" for i in report.issues))

    def test_status_with_insufficient_evidence_strength_warns(self) -> None:
        """solid needs medium+ and expert needs strong+, without validate errors."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._template_profile(Path(tmp_s), "strengthuser")
            _pool = {
                "profile": "strengthuser",
                "evidence_entries": [
                    {
                        "id": "ev_weak",
                        "type": "project",
                        "title": "Weak proof",
                        "strength": "weak",
                        "review_status": "reviewed",
                    },
                    {
                        "id": "ev_medium",
                        "type": "project",
                        "title": "Medium proof",
                        "strength": "medium",
                        "review_status": "reviewed",
                    },
                ],
            }
            tree = {
                "profile": "strengthuser",
                "schema": "robotics-engineer",
                "updated": "2026-03-21",
                "nodes": [
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
                ],
            }
            (profile / "evidence-pool.yaml").write_text(
                yaml.dump(_pool, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            (profile / "skill-tree.yaml").write_text(
                yaml.dump(tree, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            with patch(
                "nblane.core.profile_health.profile_dir",
                lambda _name: profile,
            ):
                report = analyze_profile_health("strengthuser")

        evidence_issues = [
            issue for issue in report.issues if issue.category == "evidence"
        ]
        self.assertGreaterEqual(len(evidence_issues), 2)
        self.assertFalse(
            any(
                issue.category == "validate" and issue.severity == "error"
                for issue in report.issues
            )
        )

    def test_done_task_not_crystallized_is_info(self) -> None:
        """Done tasks without crystallized true show a kanban info issue."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._template_profile(Path(tmp_s), "kanbanuser")
            (profile / "kanban.md").write_text(
                "# kanbanuser · Kanban\n\n"
                "## Done\n\n"
                "- [x] Ship demo\n"
                "  - outcome: shipped\n",
                encoding="utf-8",
            )
            with patch(
                "nblane.core.profile_health.profile_dir",
                lambda _name: profile,
            ):
                report = analyze_profile_health("kanbanuser")
        self.assertTrue(any(i.category == "kanban" for i in report.issues))

    def test_non_done_task_marked_crystallized_is_warning(self) -> None:
        """Only Done tasks may carry crystallized true."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._template_profile(Path(tmp_s), "kanbanuser")
            (profile / "kanban.md").write_text(
                "# kanbanuser · Kanban\n\n"
                "## Doing\n\n"
                "- [ ] Still active\n"
                "  - crystallized: true\n",
                encoding="utf-8",
            )
            with patch(
                "nblane.core.profile_health.profile_dir",
                lambda _name: profile,
            ):
                report = analyze_profile_health("kanbanuser")

        self.assertTrue(
            any(
                issue.title == "Non-Done tasks marked crystallized"
                and issue.severity == "warning"
                for issue in report.issues
            )
        )

    def test_dangling_workspace_refs_warn_without_blocking_publish(self) -> None:
        """Internal dangling refs are warnings, not publish blockers."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._template_profile(Path(tmp_s), "refsuser")
            (profile / "evidence-pool.yaml").write_text(
                yaml.dump(
                    {
                        "profile": "refsuser",
                        "evidence_entries": [
                            {
                                "id": "ev_1",
                                "title": "Evidence",
                                "project_refs": ["project:missing"],
                                "experience_refs": ["experience:missing"],
                                "source_refs": ["source:research:20260513-404"],
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            with patch(
                "nblane.core.profile_health.profile_dir",
                lambda _name: profile,
            ), patch(
                "nblane.core.profile_health.validate_one",
                return_value=([], []),
            ), patch(
                "nblane.core.profile_health.get_drifted_blocks",
                return_value=[],
            ):
                report = analyze_profile_health("refsuser")

        ref_issues = [issue for issue in report.issues if issue.category == "refs"]
        self.assertGreaterEqual(len(ref_issues), 3)
        self.assertTrue(report.can_publish_context)

    def test_dangling_project_board_and_kanban_refs_warn(self) -> None:
        """Project Board and Kanban project/milestone refs are checked."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._template_profile(Path(tmp_s), "projectrefs")
            (profile / "project-board.yaml").write_text(
                yaml.dump(
                    {
                        "schema_version": "1.0",
                        "profile": "projectrefs",
                        "project_cases": [
                            {
                                "id": "project:demo",
                                "title": "Demo",
                                "goal_refs": ["goal_missing"],
                                "task_refs": ["task_missing"],
                                "evidence_refs": ["ev_missing"],
                                "source_refs": ["source:research:missing"],
                                "milestones": [
                                    {
                                        "id": "milestone:first",
                                        "title": "First",
                                        "task_refs": ["task_missing"],
                                        "evidence_refs": ["ev_missing"],
                                        "source_refs": ["source:research:missing"],
                                    }
                                ],
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (profile / "kanban.md").write_text(
                "# projectrefs · Kanban\n\n"
                "## Doing\n\n"
                "- [ ] Bad project\n"
                "  - id: task_bad_project\n"
                "  - project_id: project:missing\n"
                "- [ ] Bad milestone\n"
                "  - id: task_bad_milestone\n"
                "  - project_id: project:demo\n"
                "  - milestone_id: milestone:missing\n",
                encoding="utf-8",
            )
            with patch(
                "nblane.core.profile_health.profile_dir",
                lambda _name: profile,
            ), patch(
                "nblane.core.profile_health.validate_one",
                return_value=([], []),
            ), patch(
                "nblane.core.profile_health.get_drifted_blocks",
                return_value=[],
            ):
                report = analyze_profile_health("projectrefs")

        details = "\n".join(issue.detail for issue in report.issues)
        self.assertIn("missing goal: goal_missing", details)
        self.assertIn("missing kanban task: task_missing", details)
        self.assertIn("missing evidence row: ev_missing", details)
        self.assertIn("missing research source: source:research:missing", details)
        self.assertIn("missing project case: project:missing", details)
        self.assertIn("missing project milestone: milestone:missing", details)

    def test_valid_workspace_refs_do_not_warn(self) -> None:
        """Existing project, experience, and source refs pass health checks."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = self._template_profile(Path(tmp_s), "validrefs")
            (profile / "goals.yaml").write_text(
                yaml.dump(
                    {
                        "schema_version": "1.0",
                        "profile": "validrefs",
                        "current_goal_id": "goal_1",
                        "goals": [
                            {
                                "id": "goal_1",
                                "title": "Goal",
                                "status": "active",
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (profile / "kanban.md").write_text(
                "# validrefs · Kanban\n\n"
                "## Doing\n\n"
                "- [ ] Linked task\n"
                "  - id: task_1\n"
                "  - project_id: project:demo\n"
                "  - milestone_id: milestone:first\n",
                encoding="utf-8",
            )
            (profile / "project-board.yaml").write_text(
                yaml.dump(
                    {
                        "schema_version": "1.0",
                        "profile": "validrefs",
                        "project_cases": [
                            {
                                "id": "project:demo",
                                "title": "Demo",
                                "goal_refs": ["goal_1"],
                                "task_refs": ["task_1"],
                                "evidence_refs": ["ev_1"],
                                "source_refs": ["source:research:20260513-001"],
                                "experience_refs": ["experience:lab"],
                                "milestones": [
                                    {
                                        "id": "milestone:first",
                                        "title": "First",
                                        "task_refs": ["task_1"],
                                        "evidence_refs": ["ev_1"],
                                        "source_refs": ["source:research:20260513-001"],
                                    }
                                ],
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (profile / "experience.yaml").write_text(
                yaml.dump(
                    {
                        "schema_version": "1.0",
                        "profile": "validrefs",
                        "experience_cases": [
                            {
                                "id": "experience:lab",
                                "organization": "Lab",
                                "project_refs": ["project:demo"],
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (profile / "research" / "sources.yaml").write_text(
                yaml.dump(
                    {
                        "schema_version": "1.0",
                        "profile": "validrefs",
                        "sources": [
                            {
                                "id": "source:research:20260513-001",
                                "title": "Source",
                                "project_refs": ["project:demo"],
                                "experience_refs": ["experience:lab"],
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (profile / "evidence-pool.yaml").write_text(
                yaml.dump(
                    {
                        "profile": "validrefs",
                        "evidence_entries": [
                            {
                                "id": "ev_1",
                                "title": "Evidence",
                                "project_refs": ["project:demo"],
                                "experience_refs": ["experience:lab"],
                                "source_refs": ["source:research:20260513-001"],
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            with patch(
                "nblane.core.profile_health.profile_dir",
                lambda _name: profile,
            ), patch(
                "nblane.core.profile_health.validate_one",
                return_value=([], []),
            ), patch(
                "nblane.core.profile_health.get_drifted_blocks",
                return_value=[],
            ):
                report = analyze_profile_health("validrefs")

        self.assertFalse(any(issue.category == "refs" for issue in report.issues))


class TestHealthCliExit(unittest.TestCase):
    """CLI exit policy for health reports."""

    def test_warning_only_health_exits_zero(self) -> None:
        """Warning/info reports do not fail the command."""
        from nblane.commands.health import cmd_health

        report = HealthReport(
            profile="x",
            issues=[
                HealthIssue(
                    severity="warning",
                    category="evidence",
                    title="Needs evidence",
                )
            ],
            can_publish_context=True,
        )
        with patch("nblane.commands.health._require_profile"):
            with patch(
                "nblane.commands.health.analyze_profile_health",
                return_value=report,
            ):
                with self.assertRaises(SystemExit) as cm:
                    cmd_health("x")
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
