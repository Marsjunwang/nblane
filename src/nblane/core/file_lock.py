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
- Reentrant in the owning thread, allowing a transaction to call existing
  domain writers. Other threads and processes still acquire their own flock.
- Multi-file operations acquire all their locks in sorted path order before
  reading or writing. Do not acquire an earlier lock from inside a later one.
- The kernel releases the lock when the process dies, so a crashed
  writer never leaves a stale lock behind. The empty ``.lock``
  sidecar files are safe to ignore in VCS.
"""

from __future__ import annotations

import fcntl
import os
import threading
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path


_HELD = threading.local()


def _held_locks() -> set[Path]:
    """Return only locks owned by this thread in this process."""
    if getattr(_HELD, "pid", None) != os.getpid():
        _HELD.pid = os.getpid()
        _HELD.paths = set()
    return _HELD.paths


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
    identity = lock_path.resolve()
    held = _held_locks()
    if identity in held:
        yield lock_path
        return
    with open(lock_path, "a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        held.add(identity)
        try:
            yield lock_path
        finally:
            held.remove(identity)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def locked_profile_files(directory: Path, filenames: tuple[str, ...]) -> Iterator[None]:
    """Hold each domain file's sidecar lock in a consistent order."""
    paths = sorted({(directory / name).resolve() for name in filenames})
    with ExitStack() as stack:
        for path in paths:
            stack.enter_context(locked_profile_write(path.parent, path.name))
        yield


__all__ = ["locked_profile_write", "locked_profile_files"]
