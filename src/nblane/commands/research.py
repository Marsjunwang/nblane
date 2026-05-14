"""CLI handlers for Research Workspace and connectors."""

from __future__ import annotations

import sys

import yaml

from nblane.commands.common import _require_profile
from nblane.core.research_connectors import sync_connector, sync_connectors


def _print_yaml(data: object) -> None:
    print(
        yaml.dump(
            data,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ).rstrip()
    )


def cmd_research_connector_sync(
    name: str,
    *,
    provider: str,
    connector_id: str,
    all_connectors: bool,
    dry_run: bool,
) -> None:
    """Run configured research connector sync."""
    _require_profile(name)
    if all_connectors:
        results = sync_connectors(name, provider=provider, dry_run=dry_run)
    else:
        if not connector_id:
            print("ERROR: pass --id or --all", file=sys.stderr)
            sys.exit(1)
        results = [sync_connector(name, connector_id, dry_run=dry_run)]
    _print_yaml({"results": [result.to_dict() for result in results]})
    if any(result.error for result in results):
        sys.exit(1)
