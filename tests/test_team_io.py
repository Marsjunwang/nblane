"""Tests for team file I/O hardening (atomic writes + backup)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core import team_io


class TestTeamIo(unittest.TestCase):
    """Team YAML writes go through atomic_write_text with git backup."""

    def test_save_team_uses_atomic_write(self) -> None:
        """team.yaml is written via atomic_write_text, then backed up."""
        with tempfile.TemporaryDirectory() as tmp:
            teams = Path(tmp) / "teams"
            with patch.object(team_io, "TEAMS_DIR", teams), patch(
                "nblane.core.team_io.atomic_write_text"
            ) as atomic, patch(
                "nblane.core.team_io.git_backup.record_change"
            ) as record:
                team_io.save_team("demo", {"name": "Demo"})

        atomic.assert_called_once()
        self.assertEqual(
            atomic.call_args[0][0],
            teams / "demo" / "team.yaml",
        )
        record.assert_called_once()

    def test_save_product_pool_uses_atomic_write(self) -> None:
        """product-pool.yaml is written via atomic_write_text, then backed up."""
        with tempfile.TemporaryDirectory() as tmp:
            teams = Path(tmp) / "teams"
            with patch.object(team_io, "TEAMS_DIR", teams), patch(
                "nblane.core.team_io.atomic_write_text"
            ) as atomic, patch(
                "nblane.core.team_io.git_backup.record_change"
            ) as record:
                team_io.save_product_pool("demo", {"items": []})

        atomic.assert_called_once()
        self.assertEqual(
            atomic.call_args[0][0],
            teams / "demo" / "product-pool.yaml",
        )
        record.assert_called_once()

    def test_save_and_load_round_trip(self) -> None:
        """Saved team data loads back unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            teams = Path(tmp) / "teams"
            with patch.object(team_io, "TEAMS_DIR", teams), patch(
                "nblane.core.team_io.git_backup.record_change"
            ):
                team_io.save_team("demo", {"name": "Demo", "members": ["a"]})
                team_io.save_product_pool("demo", {"items": [{"id": "p1"}]})
                loaded_team = team_io.load_team("demo")
                loaded_pool = team_io.load_product_pool("demo")

        self.assertEqual(loaded_team, {"name": "Demo", "members": ["a"]})
        self.assertEqual(loaded_pool, {"items": [{"id": "p1"}]})


if __name__ == "__main__":
    unittest.main()
