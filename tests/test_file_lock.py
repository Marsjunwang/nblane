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
from nblane.core.inbox import add_inbox_item, load_inbox, update_inbox


class TestLockedProfileWrite(unittest.TestCase):
    """The sidecar lock serializes writers; the data file is never locked."""

    def test_lock_is_exclusive_and_released(self) -> None:
        """A held lock blocks other flock users and is released on exit."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            with locked_profile_write(prof, "inbox.yaml") as lock_path:
                self.assertEqual(lock_path, prof / "inbox.yaml.lock")
                with open(lock_path, "a", encoding="utf-8") as other:
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(
                            other.fileno(),
                            fcntl.LOCK_EX | fcntl.LOCK_NB,
                        )
            with open(lock_path, "a", encoding="utf-8") as other:
                fcntl.flock(other.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(other.fileno(), fcntl.LOCK_UN)


class TestUpdateInbox(unittest.TestCase):
    """update_inbox holds the lock across load → mutate → save."""

    def test_sidecar_lock_and_atomic_data_write(self) -> None:
        """The lock is a sidecar file; the data write stays atomic."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            with patch(
                "nblane.core.inbox.git_backup.record_change"
            ) as record:
                item = update_inbox(
                    prof,
                    lambda inbox: add_inbox_item(inbox, "first note"),
                )

            self.assertTrue((prof / "inbox.yaml.lock").exists())
            data_path = prof / "inbox.yaml"
            self.assertTrue(data_path.exists())
            self.assertEqual(
                [p for p in prof.iterdir() if p.suffix == ".tmp"],
                [],
            )
            stored = load_inbox(prof)
            self.assertEqual([entry.id for entry in stored.items], [item.id])
            record.assert_called_once()

    def test_unchanged_inbox_skips_write_and_backup(self) -> None:
        """A no-op mutation leaves the file and git history untouched."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            with patch(
                "nblane.core.inbox.git_backup.record_change"
            ) as record:
                update_inbox(prof, lambda inbox: None)

            self.assertFalse((prof / "inbox.yaml").exists())
            record.assert_not_called()

    def test_concurrent_updates_lose_nothing(self) -> None:
        """Two processes × 50 locked updates → all 100 items land."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            worker = textwrap.dedent(
                """
                import sys
                from pathlib import Path
                from unittest.mock import patch

                from nblane.core.inbox import add_inbox_item, update_inbox

                prof = Path(sys.argv[1])
                worker = sys.argv[2]
                with patch("nblane.core.inbox.git_backup.record_change"):
                    for i in range(50):
                        update_inbox(
                            prof,
                            lambda inbox, i=i: add_inbox_item(
                                inbox, f"{worker}-{i}"
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

            stored = load_inbox(prof)
            self.assertEqual(len(stored.items), 100)
            titles = {item.title for item in stored.items}
            expected = {f"w{n}-{i}" for n in range(2) for i in range(50)}
            self.assertEqual(titles, expected)


if __name__ == "__main__":
    unittest.main()
