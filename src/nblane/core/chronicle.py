"""Append-only per-profile chronicle (``profiles/<name>/chronicle.yaml``).

Narrative-level events for the home briefing line, 拓片 (yearly rubbings),
and openclaw review material — git history is noise, the chronicle is the
story (docs/zh/dev/home-editing-starmap-design.md §8). Write endpoints append
entries themselves, only when the change actually happened (a no-op save logs
nothing).

File shape::

    schema_version: "1.0"
    profile: alice
    entries:
      - date: 2026-09-23
        kind: goal.added
        ref: goal-ship-vla-demo
        note: Ship the VLA demo

Entries are append-only and ordered oldest -> newest. Writes hold the
chronicle.yaml sidecar lock; when the caller passes an ``expected_snapshot``
the file is re-checked inside the lock and a mismatch raises
``file_state.FileConflictError`` (same discipline as the activity-log
checkin append).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from nblane.core import git_backup
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_state import FileSnapshot, assert_unchanged
from nblane.core.file_write import atomic_write_text
from nblane.core.paths import PROFILES_DIR
from nblane.core.profile_io import safe_profile_dir
from nblane.core.yaml_io import _load_yaml_dict

CHRONICLE_FILENAME = "chronicle.yaml"

# Kinds currently emitted by the write endpoints. ``ref`` points at the
# changed object (goal/habit/skill-node id; empty for the North Star).
CHRONICLE_KINDS: tuple[str, ...] = (
    "north_star.rewritten",
    "goal.added",
    "goal.completed",
    "goal.renamed",
    "project.deleted",
    "habit.deleted",
    "skill.lit",
)


@dataclass
class ChronicleEntry:
    """One append-only chronicle line."""

    date: str
    kind: str
    ref: str = ""
    note: str = ""

    @classmethod
    def from_dict(cls, raw: object) -> ChronicleEntry | None:
        """Build a normalized entry from raw YAML."""
        if not isinstance(raw, dict):
            return None
        when = str(raw.get("date") or "").strip()
        kind = str(raw.get("kind") or "").strip()
        if not when or not kind:
            return None
        return cls(
            date=when,
            kind=kind,
            ref=str(raw.get("ref") or "").strip(),
            note=str(raw.get("note") or "").strip(),
        )

    def to_dict(self) -> dict:
        """Serialize with stable field order."""
        return {
            "date": self.date,
            "kind": self.kind,
            "ref": self.ref,
            "note": self.note,
        }


def _chronicle_path(name_or_dir: str | Path) -> Path:
    """Resolve chronicle.yaml from a profile name or directory."""
    if isinstance(name_or_dir, Path):
        return name_or_dir / CHRONICLE_FILENAME
    return safe_profile_dir(name_or_dir, PROFILES_DIR) / CHRONICLE_FILENAME


def load_chronicle(name_or_dir: str | Path) -> list[ChronicleEntry]:
    """Load chronicle entries (oldest first); a missing file is empty."""
    path = _chronicle_path(name_or_dir)
    raw = _load_yaml_dict(path)
    if raw is None:
        return []
    entries = raw.get("entries") or []
    if not isinstance(entries, list):
        return []
    out: list[ChronicleEntry] = []
    for item in entries:
        entry = ChronicleEntry.from_dict(item)
        if entry is not None:
            out.append(entry)
    return out


def append_chronicle(
    name_or_dir: str | Path,
    kind: str,
    *,
    ref: str = "",
    note: str = "",
    when: str | None = None,
    expected_snapshot: FileSnapshot | None = None,
) -> ChronicleEntry:
    """Append one entry to chronicle.yaml under the write lock.

    *kind* must be one of ``CHRONICLE_KINDS``; *when* defaults to today and
    must be an ISO date when given. The whole load -> append -> write cycle
    holds the lock, so concurrent appends never lose entries. When
    *expected_snapshot* is given it is re-checked inside the lock and a
    mismatch raises ``file_state.FileConflictError``.
    """
    clean_kind = str(kind or "").strip()
    if clean_kind not in CHRONICLE_KINDS:
        raise ValueError(
            f"Unknown chronicle kind: {clean_kind!r} "
            f"(expected one of {', '.join(CHRONICLE_KINDS)})"
        )
    day = str(when or "").strip() or date.today().isoformat()
    try:
        day = date.fromisoformat(day).isoformat()
    except ValueError:
        raise ValueError(
            f"chronicle date must be ISO (YYYY-MM-DD), got {day!r}."
        ) from None

    entry = ChronicleEntry(
        date=day,
        kind=clean_kind,
        ref=str(ref or "").strip(),
        note=str(note or "").strip(),
    )
    path = _chronicle_path(name_or_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with locked_profile_write(path.parent, CHRONICLE_FILENAME):
        if expected_snapshot is not None:
            assert_unchanged(path, expected_snapshot, label=CHRONICLE_FILENAME)
        entries = load_chronicle(path.parent)
        entries.append(entry)
        header = (
            f"# Chronicle for {path.parent.name}\n"
            "# Append-only narrative events (date, kind, ref, note).\n"
            "# Written by the mutation endpoints; consumed by the home "
            "briefing line, rubbings, and openclaw reviews.\n\n"
        )
        body = yaml.dump(
            {
                "schema_version": "1.0",
                "profile": path.parent.name,
                "entries": [item.to_dict() for item in entries],
            },
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
        atomic_write_text(path, header + body)
    git_backup.record_change(
        [path],
        action=f"append {path.parent.name}/chronicle.yaml",
    )
    return entry
