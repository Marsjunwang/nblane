"""Build the MCP stdio server entry for local agent runtimes.

Local runtimes (Cursor, Claude Desktop, …) connect to the ``nblane-mcp``
stdio server (see ``nblane.mcp_server``). This module renders the
ready-to-merge server entry so users do not hand-write paths. The OpenClaw
assistant does not use this channel — it reaches nblane over HTTP.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from nblane.core import paths


def resolve_mcp_server_command(
    executable: str | None = None,
) -> tuple[str, list[str]]:
    """Return ``(command, args)`` that launches the nblane MCP server."""
    if executable:
        return executable, []
    found = shutil.which("nblane-mcp")
    if found:
        return found, []
    return sys.executable, ["-m", "nblane.mcp_server"]


def _default_profile(root: Path) -> str | None:
    """Prefill the profile when exactly one exists under *root*."""
    try:
        from nblane.core.profile_io import list_profiles

        names = list_profiles()
    except Exception:
        return None
    if len(names) == 1:
        return names[0]
    return None


def build_mcp_server_entry(
    profile: str | None = None,
    *,
    root: Path | None = None,
    executable: str | None = None,
) -> dict:
    """Return one MCP stdio server entry (command/args/env) as a dict."""
    command, args = resolve_mcp_server_command(executable)
    repo_root = Path(root) if root is not None else paths.REPO_ROOT
    env = {"NBLANE_ROOT": str(repo_root)}
    chosen = profile or _default_profile(repo_root)
    if chosen:
        env["NBLANE_PROFILE"] = chosen
    entry: dict = {"command": command, "env": env}
    if args:
        # JSON convention: args after command; keep order command, args, env.
        entry = {"command": command, "args": args, "env": env}
    return entry


__all__ = [
    "build_mcp_server_entry",
    "resolve_mcp_server_command",
]
