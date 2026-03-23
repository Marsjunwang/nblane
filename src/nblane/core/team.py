"""Team operations: summarize team.yaml + product-pool.yaml."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

POOL_KEYS = (
    "problem_pool",
    "project_pool",
    "evidence_pool",
    "method_pool",
    "decision_pool",
)


def summarize_team(team_dir: Path) -> int:
    """Print team summary; return 0 on success."""
    team_path = team_dir / "team.yaml"
    pool_path = team_dir / "product-pool.yaml"

    if not team_path.exists():
        print(
            f"ERROR: missing {team_path}", file=sys.stderr
        )
        return 1

    with open(team_path, encoding="utf-8") as f:
        team = yaml.safe_load(f) or {}

    name = team.get("team_name", team_dir.name)
    members = team.get("members") or []
    focus = team.get("shared_focus") or []
    rules = team.get("shared_rules") or []

    print(f"Team: {name}")
    print(f"Directory: {team_dir}")
    members_str = (
        ", ".join(members) if members else "(none)"
    )
    print(f"Members: {members_str}")
    if focus:
        print(f"Shared focus: {', '.join(focus)}")
    if rules:
        print("Rules:")
        for r in rules:
            print(f"  - {r}")

    if not pool_path.exists():
        print("\nProduct pool: (not created yet)")
        return 0

    with open(pool_path, encoding="utf-8") as f:
        pool = yaml.safe_load(f) or {}

    print("\nProduct pool counts:")
    for key in POOL_KEYS:
        items = pool.get(key) or []
        print(f"  {key}: {len(items)}")

    return 0
