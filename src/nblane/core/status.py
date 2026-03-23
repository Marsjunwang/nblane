"""Skill tree status summary for one or all profiles."""

from __future__ import annotations

from pathlib import Path

from nblane.core.io import load_skill_tree_raw
from nblane.core.paths import PROFILES_DIR

STATUS_ICONS = {
    "expert": "★",
    "solid": "●",
    "learning": "◐",
    "locked": "○",
}


def count_nodes(tree_data: dict) -> dict[str, int]:
    """Count nodes by status."""
    counts: dict[str, int] = {
        "expert": 0,
        "solid": 0,
        "learning": 0,
        "locked": 0,
        "total": 0,
    }
    for node in tree_data.get("nodes") or []:
        status = node.get("status", "locked")
        counts[status] = counts.get(status, 0) + 1
        counts["total"] += 1
    return counts


def lit_fraction(counts: dict[str, int]) -> str:
    """Return 'X/Y lit' string."""
    lit = counts.get("expert", 0) + counts.get("solid", 0)
    total = counts.get("total", 0)
    return f"{lit}/{total} lit"


def summarize_profile(profile_dir: Path) -> None:
    """Print a one-block summary for a profile directory."""
    name = profile_dir.name
    if name == "template":
        return

    skill_md = profile_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"  [{name}]  no SKILL.md found")
        return

    tree_data = load_skill_tree_raw(profile_dir)

    print(f"\n{'─' * 50}")
    print(f"  {name}")
    print(f"{'─' * 50}")

    if tree_data is not None:
        counts = count_nodes(tree_data)
        print(f"  Skill tree: {lit_fraction(counts)}")
        for status, icon in STATUS_ICONS.items():
            n = counts.get(status, 0)
            if n > 0:
                print(f"    {icon} {status}: {n}")
    else:
        print("  Skill tree: not initialized yet")

    kanban = profile_dir / "kanban.md"
    if kanban.exists():
        doing_count = sum(
            1
            for line in kanban.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip().startswith("- [ ]")
            and "started" in line.lower()
        )
        print(
            f"  Kanban 'doing': ~{doing_count} active items"
        )

    print()


def summarize_all() -> None:
    """Print status for all profiles."""
    profile_dirs = sorted(PROFILES_DIR.iterdir())
    if not profile_dirs:
        print("No profiles found.")
        return
    print("\nnblane · crew status")
    for d in profile_dirs:
        if d.is_dir():
            summarize_profile(d)
