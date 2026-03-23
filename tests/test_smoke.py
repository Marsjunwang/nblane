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

        result = analyze("王军", "OpenVLA robot control")
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
        """list_profiles should find existing profiles."""
        from nblane.core.io import list_profiles

        profiles = list_profiles()
        self.assertIn("王军", profiles)

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


if __name__ == "__main__":
    unittest.main()
