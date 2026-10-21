"""File fingerprints for lightweight concurrent edit detection."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


class FileConflictError(RuntimeError):
    """Raised when a file changed after a web editor loaded it."""


@dataclass(frozen=True)
class FileSnapshot:
    """A stable fingerprint for one file path."""

    exists: bool
    mtime_ns: int | None
    size: int | None
    sha256: str | None


def file_sha256(path: Path) -> str:
    """Return SHA-256 for *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint_file(path: Path) -> str:
    """mtime+size fingerprint for *path* without reading its contents.

    Writes go through atomic replace, so mtime_ns changes on every write;
    use this for ETags where a content hash would reread the whole file.
    """
    try:
        stat = path.stat()
    except OSError:
        return "empty"
    return f"{stat.st_mtime_ns:x}-{stat.st_size:x}"


def snapshot_file(path: Path) -> FileSnapshot:
    """Capture mtime, size, and content hash for *path*."""
    try:
        stat = path.stat()
    except OSError:
        return FileSnapshot(
            exists=False,
            mtime_ns=None,
            size=None,
            sha256=None,
        )
    return FileSnapshot(
        exists=True,
        mtime_ns=stat.st_mtime_ns,
        size=stat.st_size,
        sha256=file_sha256(path),
    )


def snapshot_matches(path: Path, expected: FileSnapshot) -> bool:
    """True when *path* still matches *expected* (content hash decides)."""
    current = snapshot_file(path)
    if current == expected:
        return True
    return bool(
        current.exists
        and expected.exists
        and current.sha256 == expected.sha256
    )


def assert_unchanged(
    path: Path,
    expected: FileSnapshot,
    *,
    label: str | None = None,
) -> None:
    """Raise FileConflictError when *path* differs from *expected*."""
    if snapshot_matches(path, expected):
        return
    name = label or str(path)
    raise FileConflictError(
        f"{name} changed on disk after this page loaded. "
        "Reload the latest version before saving so nblane does not "
        "overwrite someone else's update."
    )
