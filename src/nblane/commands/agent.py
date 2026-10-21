"""External agent harness CLI commands."""

from __future__ import annotations

import sys
from pathlib import Path

from nblane.commands.common import _require_profile
from nblane.core.agent_tasks import (
    find_agent_task,
    render_agent_handoff,
    sync_agent_harness_snippet,
)
from nblane.core.file_write import atomic_write_text


def cmd_sync_agent_harness(
    target: str,
    *,
    out_path: str | None = None,
) -> None:
    """Print or write a Codex/OpenCode harness config snippet."""

    try:
        body = sync_agent_harness_snippet(target)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    if out_path:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, body)
        print(f"Wrote {target} harness snippet: {path}")
        return
    print(body, end="")


def cmd_agent_handoff(
    task_id: str,
    *,
    target: str | None = None,
    profile: str | None = None,
) -> None:
    """Render a copy-paste handoff for one profile-scoped agent task."""

    if profile:
        _require_profile(profile)
    found = find_agent_task(task_id, profile=profile)
    if found is None:
        scope = f" in profile {profile}" if profile else ""
        print(f"ERROR: unknown agent task {task_id}{scope}", file=sys.stderr)
        sys.exit(1)
    found_profile, task = found
    print(
        render_agent_handoff(
            task,
            profile=found_profile,
            target=target,
        ),
        end="",
    )


__all__ = ["cmd_agent_handoff", "cmd_sync_agent_harness"]
