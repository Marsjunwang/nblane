"""Append rows to the Growth Log table inside SKILL.md."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from nblane.core import git_backup


def append_growth_log_row(profile_dir: Path, event: str) -> None:
    """Insert one dated row under ``## Growth Log`` in SKILL.md.

    Raises:
        FileNotFoundError: If SKILL.md is missing.
        ValueError: If the Growth Log section or table header is missing.
    """
    skill_md = profile_dir / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")

    today = date.today().strftime("%Y-%m")
    new_row = f"| {today} | {event} | — |"

    log_header = "## Growth Log"
    table_header = "| Date | Event | Why it matters |"

    if log_header not in content:
        raise ValueError(
            "Could not find '## Growth Log' section in SKILL.md."
        )

    insert_after = (
        table_header + "\n|------|-------|----------------|"
    )
    if insert_after in content:
        content = content.replace(
            insert_after,
            insert_after + "\n" + new_row,
        )
    else:
        content = content.replace(
            table_header,
            table_header
            + "\n|------|-------|----------------|\n"
            + new_row,
        )

    skill_md.write_text(content, encoding="utf-8")
    git_backup.record_change(
        [skill_md],
        action=f"log growth event for {profile_dir.name}",
    )
