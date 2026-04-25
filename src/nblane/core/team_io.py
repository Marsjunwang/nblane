"""Team and product-pool file I/O."""

from __future__ import annotations

import yaml

from nblane.core.paths import TEAMS_DIR


def list_teams() -> list[str]:
    """Return team IDs (non-template subdirs of teams/)."""
    if not TEAMS_DIR.exists():
        return []
    return sorted(
        d.name
        for d in TEAMS_DIR.iterdir()
        if d.is_dir() and d.name != "_template"
    )


def load_team(team_id: str) -> dict | None:
    """Load team.yaml for a team."""
    path = TEAMS_DIR / team_id / "team.yaml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_product_pool(team_id: str) -> dict | None:
    """Load product-pool.yaml for a team."""
    path = TEAMS_DIR / team_id / "product-pool.yaml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_team(team_id: str, data: dict) -> None:
    """Write team.yaml for a team."""
    path = TEAMS_DIR / team_id / "team.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    path.write_text(body, encoding="utf-8")


def save_product_pool(team_id: str, data: dict) -> None:
    """Write product-pool.yaml for a team."""
    path = TEAMS_DIR / team_id / "product-pool.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    path.write_text(body, encoding="utf-8")
