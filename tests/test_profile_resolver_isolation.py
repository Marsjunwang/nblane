"""Regression tests for stateless profile path resolution."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from nblane.core import home_dashboard, io as io_facade, kanban_io, profile_health
from nblane.core.models import KanbanTask


def _run_pair(call) -> None:
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(call, Path(f"/tmp/{name}")) for name in ("alice", "bob")]
        for future in futures:
            future.result(timeout=10)


def test_kanban_facades_keep_profile_paths_and_resolver_isolated() -> None:
    sentinel = lambda name: Path(f"/sentinel/{name}")
    operations = {
        "parse_kanban": lambda profile: io_facade.parse_kanban(profile),
        "save_kanban": lambda profile: io_facade.save_kanban(profile, {}),
        "append_kanban_archive": lambda profile: io_facade.append_kanban_archive(
            profile, [KanbanTask(title="Done", done=True)]
        ),
        "archive_kanban_done_tasks": lambda profile: io_facade.archive_kanban_done_tasks(
            profile, {}, []
        ),
    }
    for operation, call in operations.items():
        barrier = threading.Barrier(2)
        seen: list[tuple[Path, bool]] = []

        def bottom(profile, *args, **kwargs):
            seen.append((profile, kanban_io.profile_dir is sentinel))
            barrier.wait(timeout=5)
            return {}

        with (
            patch.object(kanban_io, operation, side_effect=bottom),
            patch.object(kanban_io, "profile_dir", sentinel),
        ):
            _run_pair(call)
            assert kanban_io.profile_dir is sentinel, operation

        assert {profile for profile, _ in seen} == {
            Path("/tmp/alice"),
            Path("/tmp/bob"),
        }, operation
        assert all(unchanged for _, unchanged in seen), operation


def test_health_summary_interleaving_uses_explicit_profile_paths() -> None:
    resolver = lambda name: Path(f"/sentinel/{name}")
    io_resolver = lambda name: Path(f"/io-sentinel/{name}")
    barrier = threading.Barrier(2)
    seen: list[tuple[Path, bool, bool]] = []

    def parse(profile):
        seen.append(
            (
                profile,
                profile_health.profile_dir is resolver,
                io_facade.profile_dir is io_resolver,
            )
        )
        barrier.wait(timeout=5)
        return {}

    with (
        patch.object(profile_health, "profile_dir", resolver),
        patch.object(io_facade, "profile_dir", io_resolver),
        patch.object(profile_health, "parse_kanban", side_effect=parse),
        patch.object(profile_health, "validate_one", return_value=([], [])),
        patch.object(profile_health, "get_drifted_blocks", return_value=[]),
        patch.object(profile_health, "load_skill_tree_raw", return_value=None),
        patch.object(profile_health, "_ref_integrity_issues", return_value=[]),
    ):
        _run_pair(home_dashboard.dashboard_health_summary)
        assert profile_health.profile_dir is resolver
        assert io_facade.profile_dir is io_resolver

    assert {profile for profile, _, _ in seen} == {
        Path("/tmp/alice"),
        Path("/tmp/bob"),
    }
    assert all(health_ok and io_ok for _, health_ok, io_ok in seen)
