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
