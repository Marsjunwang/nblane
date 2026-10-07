"""Tests for the MCP resources/tools added for the OpenClaw integration."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"

_SKIP_NO_MCP = unittest.skipUnless(find_spec("mcp"), "mcp dependency is not installed")


def _template_profile(tmp: Path, name: str = "alice") -> Path:
    profile = tmp / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            text = text.replace("{YYYY-MM-DD}", "2026-05-14")
            file_path.write_text(text, encoding="utf-8")
    return profile


@_SKIP_NO_MCP
class TestMcpProfileResources(unittest.TestCase):
    """New read-only profile resources render summaries and redact private data."""

    def _patch_profile(self, profile: Path):
        from nblane import mcp_server

        return (
            patch.object(
                mcp_server,
                "resolve_active_profile",
                lambda: ("alice", None),
            ),
            patch.object(mcp_server, "profile_dir", lambda _name: profile),
        )

    def test_goals_resource_redacts_private_goals_only(self) -> None:
        """Private goals are hidden; the North Star always renders (binary
        visibility gates public artifacts only, never agent context)."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "SKILL.md").write_text(
                """# alice

## Identity

- **Name**: alice
- **North Star**: Secret Mars plan
- **North Star Brief**: Mars brief
- **North Star Visibility**: private
""",
                encoding="utf-8",
            )
            (profile / "goals.yaml").write_text(
                yaml.dump(
                    {
                        "schema_version": "1.0",
                        "profile": "alice",
                        "current_goal_id": "g1",
                        "goals": [
                            {
                                "id": "g1",
                                "title": "Ship VLA demo",
                                "status": "active",
                                "ui_visibility": "visible",
                                "summary": "demo for review",
                            },
                            {
                                "id": "g2",
                                "title": "Secret goal",
                                "status": "active",
                                "ui_visibility": "private",
                            },
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_goals()

        self.assertIn("# Goals: alice", text)
        self.assertIn("- active: 2", text)
        self.assertIn("Ship VLA demo", text)
        # North Star Visibility gates public artifacts only; agents see full.
        self.assertIn("Secret Mars plan", text)
        # Private goals stay hidden from agent context.
        self.assertNotIn("Secret goal", text)

    def test_goals_resource_shows_visible_north_star_and_primary(self) -> None:
        """Visible North Star and the primary goal render for the agent."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "SKILL.md").write_text(
                """# alice

## Identity

- **Name**: alice
- **North Star**: Mars by 2035
- **North Star Visibility**: visible
""",
                encoding="utf-8",
            )
            (profile / "goals.yaml").write_text(
                yaml.dump(
                    {
                        "profile": "alice",
                        "current_goal_id": "g1",
                        "goals": [
                            {
                                "id": "g1",
                                "title": "Ship VLA demo",
                                "status": "active",
                                "target": "2026-10-01",
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_goals()

        self.assertIn("Mars by 2035", text)
        self.assertIn("## Primary goal", text)
        self.assertIn("Ship VLA demo", text)

    def test_resource_profile_resolution_errors(self) -> None:
        """Every new resource reports profile-resolution errors inline."""
        from nblane import mcp_server

        resources = [
            ("profile://goals", mcp_server.resource_goals),
            ("profile://evidence", mcp_server.resource_evidence),
            ("profile://learning", mcp_server.resource_learning),
        ]
        with patch.object(
            mcp_server,
            "resolve_active_profile",
            lambda: (None, "no profile set"),
        ):
            for getter, fn in resources:
                with self.subTest(getter=getter):
                    text = fn()
                    self.assertTrue(
                        text.startswith(f"ERROR [{getter}]: no profile set"),
                        text,
                    )

    def test_evidence_resource_summarizes_pool(self) -> None:
        """Evidence summary counts by review status and lists recent rows."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "evidence-pool.yaml").write_text(
                yaml.dump(
                    {
                        "profile": "alice",
                        "evidence_entries": [
                            {
                                "id": "ev_old",
                                "type": "project",
                                "title": "Built robot arm",
                                "date": "2026-01-01",
                                "review_status": "reviewed",
                            },
                            {
                                "id": "ev_new",
                                "type": "paper",
                                "title": "VLA survey read",
                                "date": "2026-06-01",
                                "review_status": "needs_review",
                            },
                            {
                                "id": "ev_gone",
                                "type": "practice",
                                "title": "Deprecated thing",
                                "date": "2026-07-01",
                                "deprecated": True,
                            },
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_evidence()

        self.assertIn("Total entries: 2", text)
        self.assertIn("- needs_review: 1", text)
        self.assertIn("- reviewed: 1", text)
        self.assertIn("Deprecated (hidden below): 1", text)
        self.assertLess(text.index("ev_new"), text.index("ev_old"))
        self.assertNotIn("ev_gone", text)

    def test_evidence_resource_handles_missing_pool(self) -> None:
        """A profile without evidence-pool.yaml gets a placeholder, not an error."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_evidence()

        self.assertIn("no evidence-pool.yaml", text)

    def test_learning_resource_summary(self) -> None:
        """Learning resource shows status counts, reading list, recent entries."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "learning-log.yaml").write_text(
                yaml.dump(
                    {
                        "profile": "alice",
                        "resources": [
                            {
                                "id": "l1",
                                "kind": "paper",
                                "title": "VLA survey",
                                "status": "reading",
                                "added_at": "2026-09-01",
                            },
                            {
                                "id": "l2",
                                "kind": "book",
                                "title": "RL book",
                                "status": "processed",
                                "added_at": "2026-05-01",
                            },
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_learning()

        self.assertIn("Total resources: 2", text)
        self.assertIn("- reading: 1", text)
        self.assertIn("- processed: 1", text)
        self.assertIn("## Active (reading) — 1", text)
        self.assertIn("VLA survey", text)
        self.assertIn("## Recent entries", text)

@_SKIP_NO_MCP
class TestMcpStructuredTools(unittest.TestCase):
    """New dict-returning tools write through locked core helpers."""

    def test_run_validate_reports_ok_and_errors(self) -> None:
        """run_validate returns bounded ok/errors/warnings without writing."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch.object(mcp_server, "profile_dir", lambda _name: profile),
            ):
                healthy = mcp_server.tool_run_validate()
                (profile / "skill-tree.yaml").write_text(
                    'profile: "alice"\nupdated: "2026-05-14"\nnodes: []\n',
                    encoding="utf-8",
                )
                broken = mcp_server.tool_run_validate()

        self.assertTrue(healthy["ok"])
        self.assertEqual(healthy["errors"], [])
        self.assertEqual(healthy["warnings"], [])
        self.assertEqual(healthy["profile"], "alice")
        self.assertFalse(broken["ok"])
        self.assertEqual(broken["error_count"], len(broken["errors"]))
        self.assertTrue(any("schema" in e for e in broken["errors"]))

    def test_run_validate_profile_error(self) -> None:
        """run_validate surfaces profile-resolution errors as structured dicts."""
        from nblane import mcp_server

        with patch.object(
            mcp_server,
            "resolve_active_profile",
            lambda: (None, "no profile set"),
        ):
            result = mcp_server.tool_run_validate()
        self.assertEqual(result, {"ok": False, "error": "no profile set"})

    def test_run_sync_check_reports_drift_and_in_sync(self) -> None:
        """run_sync_check lists drifted blocks and never writes."""
        from nblane import mcp_server

        skill_md = (
            "# alice\n\n"
            "## Skill Tree\n\n"
            "<!-- BEGIN GENERATED:skill_tree -->\n"
            "{body}\n"
            "<!-- END GENERATED:skill_tree -->\n\n"
            "## Current Focus\n\n"
            "<!-- BEGIN GENERATED:current_focus -->\n"
            "{focus}\n"
            "<!-- END GENERATED:current_focus -->\n"
        )
        expected_focus = (
            "**Active** (this week):\n"
            "- kanban.md not found.\n\n"
            "**Queued** (next):\n"
            "- none\n\n"
            "**Blocked**:\n"
            "- none"
        )
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch.object(mcp_server, "profile_dir", lambda _name: profile),
            ):
                (profile / "SKILL.md").write_text(
                    skill_md.format(body="- [x] stale", focus="stale focus"),
                    encoding="utf-8",
                )
                drifted = mcp_server.tool_run_sync_check()
                (profile / "SKILL.md").write_text(
                    skill_md.format(
                        body="- skill-tree.yaml not found.",
                        focus=expected_focus,
                    ),
                    encoding="utf-8",
                )
                in_sync = mcp_server.tool_run_sync_check()

        self.assertTrue(drifted["ok"])
        self.assertFalse(drifted["in_sync"])
        self.assertEqual(
            drifted["drifted_blocks"], ["skill_tree", "current_focus"]
        )
        self.assertTrue(in_sync["ok"])
        self.assertTrue(in_sync["in_sync"])
        self.assertEqual(in_sync["drifted_blocks"], [])

    def test_run_sync_check_error_paths(self) -> None:
        """run_sync_check reports missing profile and missing SKILL.md."""
        from nblane import mcp_server

        with patch.object(
            mcp_server,
            "resolve_active_profile",
            lambda: (None, "no profile set"),
        ):
            result = mcp_server.tool_run_sync_check()
        self.assertEqual(result, {"ok": False, "error": "no profile set"})

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch.object(mcp_server, "profile_dir", lambda _name: profile),
            ):
                missing = mcp_server.tool_run_sync_check()
        self.assertFalse(missing["ok"])
        self.assertIn("SKILL.md", missing["error"])

if __name__ == "__main__":
    unittest.main()
