"""Locked JSONL persistence primitives for research artifacts."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from nblane.core import git_backup
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_state import FileSnapshot, assert_unchanged
from nblane.core.file_write import atomic_write_text

_T = TypeVar("_T")
JsonlRows = list[dict[str, Any]]


def load_jsonl(path: str | Path) -> JsonlRows:
    """Load object rows, ignoring blank, malformed, and non-object lines."""
    target = Path(path)
    if not target.exists():
        return []
    rows: JsonlRows = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def _write_rows(path: Path, rows: JsonlRows) -> None:
    text = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        for row in rows
    )
    atomic_write_text(path, text)


def mutate_jsonl(
    path: str | Path,
    fn: Callable[[JsonlRows], _T],
    *,
    expected_snapshot: FileSnapshot | None = None,
    action: str = "",
) -> _T:
    """Apply an in-memory mutation to the latest rows under the file lock."""
    target = Path(path)
    changed = False
    with locked_profile_write(target.parent, target.name):
        if expected_snapshot is not None:
            assert_unchanged(target, expected_snapshot, label=target.name)
        rows = load_jsonl(target)
        before = copy.deepcopy(rows)
        result = fn(rows)
        changed = rows != before
        if changed:
            _write_rows(target, rows)
    if changed:
        git_backup.record_change(
            [target],
            action=action or f"update research JSONL {target.name}",
        )
    return result


def replace_jsonl(
    path: str | Path,
    rows: list[dict[str, Any]],
    *,
    expected_snapshot: FileSnapshot | None = None,
    action: str = "",
) -> Path:
    """Replace a JSONL document under its lock, with optional conflict checking."""
    target = Path(path)
    replacement = copy.deepcopy(rows)

    def apply(current: JsonlRows) -> None:
        current[:] = replacement

    mutate_jsonl(
        target,
        apply,
        expected_snapshot=expected_snapshot,
        action=action,
    )
    return target


def delete_jsonl(
    path: str | Path,
    *,
    expected_snapshot: FileSnapshot | None = None,
    action: str = "",
    record_backup: bool = True,
) -> bool:
    """Delete a JSONL file under the same lock used by writers."""
    target = Path(path)
    deleted = False
    with locked_profile_write(target.parent, target.name):
        if expected_snapshot is not None:
            assert_unchanged(target, expected_snapshot, label=target.name)
        if target.exists():
            if not target.is_file():
                raise ValueError(f"Refusing to delete non-file path: {target}")
            target.unlink()
            deleted = True
    if deleted and record_backup:
        git_backup.record_change(
            [target],
            action=action or f"delete research JSONL {target.name}",
        )
    return deleted


__all__ = [
    "JsonlRows",
    "delete_jsonl",
    "load_jsonl",
    "mutate_jsonl",
    "replace_jsonl",
]
