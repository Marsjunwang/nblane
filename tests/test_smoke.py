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

    def test_list_profiles(self) -> None:
        """list_profiles should return a list."""
        from nblane.core.io import list_profiles

        profiles = list_profiles()
        self.assertIsInstance(profiles, list)

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

    def test_auth_hash_password_cli(self) -> None:
        """``nblane auth hash-password`` prints a PBKDF2 hash."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "nblane.cli",
                "auth",
                "hash-password",
                "secret",
                "--iterations",
                "100000",
            ],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("pbkdf2_sha256$"))

    def test_public_validate_cli(self) -> None:
        """``nblane public validate`` should exit 0 on template."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "nblane.cli",
                "public",
                "validate",
                "template",
            ],
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0)

    def test_public_curation_preview_cli(self) -> None:
        """Public curation preview commands should be non-mutating."""
        suggest = subprocess.run(
            [
                sys.executable,
                "-m",
                "nblane.cli",
                "public",
                "suggest-groups",
                "template",
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            check=False,
        )
        hydrate = subprocess.run(
            [
                sys.executable,
                "-m",
                "nblane.cli",
                "public",
                "hydrate",
                "template",
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(suggest.returncode, 0)
        self.assertEqual(hydrate.returncode, 0)


if __name__ == "__main__":
    unittest.main()
