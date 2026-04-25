"""Team CLI command."""

from __future__ import annotations

import sys

from nblane.core.paths import TEAMS_DIR


def cmd_team(team_id: str) -> None:
    """Show team summary."""
    team_dir = TEAMS_DIR / team_id
    if not team_dir.is_dir():
        print(
            f"Team directory not found: {team_dir}",
            file=sys.stderr,
        )
        sys.exit(1)
    from nblane.core.team import summarize_team

    sys.exit(summarize_team(team_dir))
