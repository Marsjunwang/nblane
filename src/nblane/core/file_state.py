"""File fingerprints for lightweight concurrent edit detection."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class FileConflictError(RuntimeError):
    """Raised when a file changed after a web editor loaded it."""


@dataclass(frozen=True)
class FileSnapshot:
    """A stable fingerprint for one file path."""

    exists: bool
    mtime_ns: int | None
    size: int | None
    sha256: str | None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for Streamlit session state."""
        return {
            "exists": self.exists,
            "mtime_ns": self.mtime_ns,
            "size": self.size,
            "sha256": self.sha256,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "FileSnapshot":
        """Deserialize from Streamlit session state."""
        return cls(
            exists=bool(raw.get("exists")),
            mtime_ns=raw.get("mtime_ns"),
            size=raw.get("size"),
            sha256=raw.get("sha256"),
        )


def file_sha256(path: Path) -> str:
    """Return SHA-256 for *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def assert_unchanged(
    path: Path,
    expected: FileSnapshot,
    *,
    label: str | None = None,
) -> None:
    """Raise FileConflictError when *path* differs from *expected*."""
    current = snapshot_file(path)
    if current == expected:
        return
    if (
        current.exists
        and expected.exists
        and current.sha256 == expected.sha256
    ):
        return
    name = label or str(path)
    raise FileConflictError(
        f"{name} changed on disk after this page loaded. "
        "Refresh the page before saving so nblane does not overwrite "
        "someone else's update."
    )
