"""Tests for advisory profile write locks (L0.3)."""

from __future__ import annotations

import fcntl
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.file_lock import locked_profile_write
from nblane.core.project_board import (
    add_project_case,
    load_project_board,
    update_project_board,
)


class TestLockedProfileWrite(unittest.TestCase):
    """The sidecar lock serializes writers; the data file is never locked."""

    def test_lock_is_exclusive_and_released(self) -> None:
        """A held lock blocks other flock users and is released on exit."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            with locked_profile_write(prof, "project-board.yaml") as lock_path:
                self.assertEqual(lock_path, prof / "project-board.yaml.lock")
                with open(lock_path, "a", encoding="utf-8") as other:
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(
                            other.fileno(),
                            fcntl.LOCK_EX | fcntl.LOCK_NB,
                        )
            with open(lock_path, "a", encoding="utf-8") as other:
                fcntl.flock(other.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(other.fileno(), fcntl.LOCK_UN)


class TestLockedUpdate(unittest.TestCase):
    """update_project_board holds the lock across load → mutate → save."""

    def test_sidecar_lock_and_atomic_data_write(self) -> None:
        """The lock is a sidecar file; the data write stays atomic."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            with patch(
                "nblane.core.project_board.git_backup.record_change"
            ) as record:
                update_project_board(
                    prof,
                    lambda board: add_project_case(board, "first", case_id="c1"),
                )

            self.assertTrue((prof / "project-board.yaml.lock").exists())
            self.assertTrue((prof / "project-board.yaml").exists())
            self.assertEqual(
                [p for p in prof.iterdir() if p.suffix == ".tmp"],
                [],
            )
            self.assertIn("c1", load_project_board(prof).by_id())
            record.assert_called_once()

    def test_unchanged_document_skips_write_and_backup(self) -> None:
        """A no-op mutation leaves the file and git history untouched."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            with patch(
                "nblane.core.project_board.git_backup.record_change"
            ) as record:
                update_project_board(prof, lambda board: None)

            self.assertFalse((prof / "project-board.yaml").exists())
            record.assert_not_called()

    def test_concurrent_updates_lose_nothing(self) -> None:
        """Two processes × 25 locked updates → all 50 cases land."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            worker = textwrap.dedent(
                """
                import sys
                from pathlib import Path
                from unittest.mock import patch

                from nblane.core.project_board import (
                    add_project_case,
                    update_project_board,
                )

                prof = Path(sys.argv[1])
                worker = sys.argv[2]
                with patch("nblane.core.project_board.git_backup.record_change"):
                    for i in range(25):
                        update_project_board(
                            prof,
                            lambda board, i=i: add_project_case(
                                board, f"{worker}-{i}", case_id=f"{worker}-{i}"
                            ),
                        )
                """
            )
            procs = [
                subprocess.Popen(
                    [sys.executable, "-c", worker, str(prof), f"w{n}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for n in range(2)
            ]
            for proc in procs:
                _, stderr = proc.communicate(timeout=120)
                self.assertEqual(proc.returncode, 0, stderr)

            ids = set(load_project_board(prof).by_id())
            expected = {f"w{n}-{i}" for n in range(2) for i in range(25)}
            self.assertEqual(ids, expected)


if __name__ == "__main__":
    unittest.main()
