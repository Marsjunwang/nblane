"""Smoke tests: core module functions and CLI entry point."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestCoreSmoke(unittest.TestCase):
    """Ensure core modules work on the repo fixtures."""

    def test_validate_all(self) -> None:
        """run_all_profiles should return no errors."""
        from nblane.core.validate import run_all_profiles

        errors, _warnings = run_all_profiles()
        self.assertEqual(errors, [])

    def test_gap_analysis(self) -> None:
        """gap.analyze should match OpenVLA task to nodes."""
        from nblane.core.gap import analyze

        result = analyze("template", "OpenVLA robot control")
        self.assertIsNone(result.error)
        self.assertTrue(len(result.top_matches) > 0)
        self.assertTrue(len(result.closure) > 0)

    def test_team_summary(self) -> None:
        """summarize_team should succeed on example-team."""
        from nblane.core.team import summarize_team

        team_dir = REPO_ROOT / "teams" / "example-team"
        rc = summarize_team(team_dir)
        self.assertEqual(rc, 0)

    def test_list_profiles(self) -> None:
        """list_profiles should return a list."""
        from nblane.core.io import list_profiles

        profiles = list_profiles()
        self.assertIsInstance(profiles, list)

    def test_list_teams(self) -> None:
        """list_teams should find example-team."""
        from nblane.core.io import list_teams

        teams = list_teams()
        self.assertIn("example-team", teams)


class TestCliEntryPoint(unittest.TestCase):
    """Ensure the ``nblane`` console script works."""

    def test_validate_cli(self) -> None:
        """``nblane validate`` should exit 0."""
        result = subprocess.run(
            [sys.executable, "-m", "nblane.cli", "validate"],
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0)

    def test_status_cli(self) -> None:
        """``nblane status`` should exit 0."""
        result = subprocess.run(
            [sys.executable, "-m", "nblane.cli", "status"],
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0)

    def test_context_cli(self) -> None:
        """``nblane context template`` should exit 0."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "nblane.cli",
                "context",
                "template",
            ],
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0)

    def test_team_cli(self) -> None:
        """``nblane team example-team`` should exit 0."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "nblane.cli",
                "team",
                "example-team",
            ],
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0)

    def test_gap_cli(self) -> None:
        """``nblane gap`` should exit 0 on repo fixture."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "nblane.cli",
                "gap",
                "template",
                "OpenVLA robot control",
            ],
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
