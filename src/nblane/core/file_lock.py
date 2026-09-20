"""Advisory per-host file locks for profile data writes.

Uses stdlib ``fcntl.flock`` (Linux/Unix) on a sidecar
``<filename>.lock`` file next to the data file — never on the data
file itself, because ``core.file_write.atomic_write_text`` installs
writes via ``os.replace`` and a lock held on the replaced inode would
not serialize against a fresh lock taken on the new inode.

Caveats:

- Advisory and per-host: only writers that also go through this
  module (UI, CLI, MCP server on the same host) are serialized.
  NFS semantics depend on the mount.
- Not reentrant for the same lock file: nesting
  ``locked_profile_write`` for the same path in one process
  self-deadlocks (each ``open`` creates a new open file
  description). Different lock files nest safely.
- The kernel releases the lock when the process dies, so a crashed
  writer never leaves a stale lock behind. The empty ``.lock``
  sidecar files are safe to ignore in VCS.
"""

from __future__ import annotations

import fcntl
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def locked_profile_write(
    profile_dir: Path,
    filename: str,
) -> Iterator[Path]:
    """Hold an exclusive lock for writes to ``filename`` in *profile_dir*.

    Creates the profile directory and the sidecar lock file when
    missing, takes ``flock(LOCK_EX)`` on the sidecar, yields the lock
    path, and releases the lock on exit (including on exceptions).
    """
    directory = Path(profile_dir)
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / f"{filename}.lock"
    with open(lock_path, "a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield lock_path
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


__all__ = ["locked_profile_write"]
