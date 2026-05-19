"""Codex CLI / Codex Cloud command helpers."""

from __future__ import annotations

import sys

from nblane.commands.common import _require_profile
from nblane.core.codex_adapter import (
    codex_status,
    current_config,
    install_codex,
    install_command,
    profile_config_path,
    refresh_codex_cloud_task,
    run_local_codex_task,
    submit_codex_cloud_task,
)


def cmd_codex_status(*, profile: str | None = None) -> None:
    """Print Codex CLI and Codex Cloud readiness."""

    if profile:
        _require_profile(profile)
    status = codex_status(current_config(profile=profile))
    print("Codex")
    if profile:
        print(f"  profile: {profile}")
        print(f"  profile_config: {profile_config_path(profile)}")
    print(f"  installed: {'yes' if status.installed else 'no'}")
    print(f"  bin: {status.bin_path}")
    if status.resolved_path:
        print(f"  resolved: {status.resolved_path}")
    if status.version:
        print(f"  version: {status.version}")
    print(f"  logged_in: {'yes' if status.logged_in else 'no'}")
    if status.login_status:
        print(f"  login_status: {status.login_status}")
    print(
        "  cloud_env: "
        f"{status.cloud_env_id if status.cloud_env_configured else '(missing)'}"
    )
    if status.error:
        print(f"  error: {status.error}")
    if not status.installed:
        print(f"  install: {status.install_command}")
    else:
        print(f"  upgrade: {status.upgrade_command}")


def cmd_codex_install(
    *,
    upgrade: bool = False,
    print_command: bool = False,
) -> None:
    """Install or upgrade Codex CLI."""

    command = install_command(upgrade=upgrade)
    if print_command:
        print(command)
        return
    result = install_codex(upgrade=upgrade)
    if result.ok:
        print("Codex install command completed.")
        if result.output:
            print(result.output)
        return
    print(f"ERROR: {result.error}", file=sys.stderr)
    if result.output:
        print(result.output, file=sys.stderr)
    print(f"Run manually: {command}", file=sys.stderr)
    sys.exit(1)


def cmd_codex_cloud_submit(task_id: str, *, profile: str) -> None:
    """Submit an agent task to Codex Cloud."""

    _require_profile(profile)
    result = submit_codex_cloud_task(profile, task_id)
    if not result.ok:
        print(f"ERROR: {result.error}", file=sys.stderr)
        if result.output:
            print(result.output, file=sys.stderr)
        sys.exit(1)
    print(f"Submitted {task_id} to Codex Cloud.")
    if result.cloud_task_id:
        print(f"Cloud task id: {result.cloud_task_id}")
    print(f"Status: {result.status}")
    if result.output:
        print(result.output)


def cmd_codex_local_run(
    task_id: str,
    *,
    profile: str,
    keep_worktree: bool = False,
) -> None:
    """Run an agent task through local Codex and store a review candidate."""

    _require_profile(profile)
    result = run_local_codex_task(
        profile,
        task_id,
        keep_worktree=keep_worktree,
    )
    if not result.ok:
        print(f"ERROR: {result.error}", file=sys.stderr)
        if result.output:
            print(result.output, file=sys.stderr)
        sys.exit(1)
    print(f"Local Codex completed for {task_id}.")
    print(f"Status: {result.status}")
    print(f"Changed paths: {', '.join(result.changed_paths) or '(none)'}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")


def cmd_codex_cloud_refresh(
    task_id: str,
    *,
    profile: str,
    include_diff: bool = False,
) -> None:
    """Refresh Codex Cloud task state and optionally pull a diff."""

    _require_profile(profile)
    result = refresh_codex_cloud_task(
        profile,
        task_id,
        include_diff=include_diff,
    )
    if not result.ok:
        print(f"ERROR: {result.error}", file=sys.stderr)
        if result.output:
            print(result.output, file=sys.stderr)
        sys.exit(1)
    print(f"Refreshed Codex Cloud task for {task_id}.")
    if result.cloud_task_id:
        print(f"Cloud task id: {result.cloud_task_id}")
    if result.status:
        print(f"Status: {result.status}")
    if include_diff:
        print(f"Changed paths: {', '.join(result.changed_paths) or '(none)'}")
    if result.output and not include_diff:
        print(result.output)


__all__ = [
    "cmd_codex_cloud_refresh",
    "cmd_codex_cloud_submit",
    "cmd_codex_install",
    "cmd_codex_local_run",
    "cmd_codex_status",
]
