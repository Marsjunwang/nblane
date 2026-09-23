"""Surgical North Star writes to the SKILL.md ``Identity`` section.

SKILL.md is a living document: ``core.sync.write_generated_blocks`` rewrites
its generated blocks and the human edits the rest. This module therefore
never rewrites the whole file — it goes through
``profile_context.update_identity_fields``, which re-joins the parsed
sections losslessly and touches only the targeted ``- **Label**: value``
bullet lines inside ``## Identity``. Everything else stays byte-identical.

The write holds the ``SKILL.md`` sidecar lock (same lock as sync.py and
growth_log.py) and supports the ``expected_snapshot`` discipline: when the
caller passes a request-start fingerprint, it is re-checked inside the lock
and a mismatch raises ``file_state.FileConflictError``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from nblane.core import git_backup
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_state import FileSnapshot, assert_unchanged
from nblane.core.file_write import atomic_write_text
from nblane.core.profile_context import (
    normalize_north_star_visibility,
    parse_identity_fields,
    update_identity_fields,
)

SKILL_MD_FILENAME = "SKILL.md"

_FIELD_BY_KEY = {
    "full": "North Star",
    "brief": "North Star Brief",
    "visibility": "North Star Visibility",
}


@dataclass
class NorthStarUpdate:
    """Outcome of one surgical North Star identity write."""

    changed: bool
    changed_keys: list[str] = field(default_factory=list)
    identity: dict[str, str] = field(default_factory=dict)


def update_north_star(
    profile_dir: Path,
    *,
    full: str | None = None,
    brief: str | None = None,
    visibility: str | None = None,
    expected_snapshot: FileSnapshot | None = None,
) -> NorthStarUpdate:
    """Rewrite only the North Star identity bullets in SKILL.md.

    At least one of *full* / *brief* / *visibility* must be given. Values
    equal to the current ones are a no-op: no write, no backup, and
    ``changed=False`` (callers use this to skip chronicle entries).
    *visibility* is stored in the canonical binary form
    (``public``/``private``) via ``normalize_north_star_visibility``.

    Raises:
        FileNotFoundError: If SKILL.md is missing.
        ValueError: If no field was provided.
        file_state.FileConflictError: If *expected_snapshot* no longer
            matches once the write lock is held.
    """
    updates: dict[str, str] = {}
    if full is not None:
        updates["North Star"] = full.strip()
    if brief is not None:
        updates["North Star Brief"] = brief.strip()
    if visibility is not None:
        updates["North Star Visibility"] = normalize_north_star_visibility(
            visibility
        )
    if not updates:
        raise ValueError(
            "At least one of full, brief, or visibility is required."
        )

    path = Path(profile_dir) / SKILL_MD_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"SKILL.md not found in {profile_dir}")

    changed_keys: list[str] = []
    after_text = ""
    with locked_profile_write(Path(profile_dir), SKILL_MD_FILENAME):
        if expected_snapshot is not None:
            assert_unchanged(path, expected_snapshot, label=SKILL_MD_FILENAME)
        before_text = path.read_text(encoding="utf-8")
        before = parse_identity_fields(before_text)
        for key, field_name in _FIELD_BY_KEY.items():
            if field_name not in updates:
                continue
            current = before.get(field_name, "")
            if key == "visibility":
                # Compare on the normalized binary contract so a stored
                # legacy value (``discreet``) matching the requested value
                # (``private``) is a true no-op, not a canonicalizing write.
                current = normalize_north_star_visibility(current)
            if current != updates[field_name]:
                changed_keys.append(key)
        after_text = before_text
        if changed_keys:
            after_text = update_identity_fields(before_text, updates)
            if after_text != before_text:
                atomic_write_text(path, after_text)
            else:
                changed_keys = []
    if changed_keys:
        git_backup.record_change(
            [path],
            action=f"update {Path(profile_dir).name}/SKILL.md north star",
        )
    return NorthStarUpdate(
        changed=bool(changed_keys),
        changed_keys=changed_keys,
        identity=parse_identity_fields(after_text),
    )
