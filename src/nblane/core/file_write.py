"""Reliable local file write helpers."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def _fsync_directory(path: Path) -> None:
    """Best-effort fsync for a directory after an atomic replace."""
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write_text(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
) -> None:
    """Atomically replace *path* with *text*.

    The temporary file is written in the destination directory, flushed to
    disk, and then installed with ``os.replace`` so readers never observe a
    partially-written file.
    """
    target = Path(path)
    tmp_name: str | None = None
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            mode = target.stat().st_mode
        except FileNotFoundError:
            mode = None
        if mode is not None:
            os.chmod(tmp_name, mode)
        os.replace(tmp_name, target)
        tmp_name = None
        _fsync_directory(target.parent)
    finally:
        if tmp_name is not None:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass
