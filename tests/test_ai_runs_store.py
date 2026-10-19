"""ai-runs.yaml stays bounded, survives concurrent appends and is cached."""
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from nblane.core.ai import runs as ai_runs
from nblane.core.ai.actions import AIActionRequest, AIActionResult, AIActionSpec


@pytest.fixture()
def profile(tmp_path: Path):
    root = tmp_path / "profiles"
    (root / "alice").mkdir(parents=True)
    targets = ("nblane.core.paths.PROFILES_DIR", "nblane.core.profile_io.PROFILES_DIR", "nblane.core.io.PROFILES_DIR")
    patches = [patch(target, root) for target in targets] + [patch("nblane.core.ai.runs.git_backup.record_change")]
    for p in patches:
        p.start()
    ai_runs._LOAD_CACHE.clear()
    yield root / "alice"
    for p in patches:
        p.stop()
    ai_runs._LOAD_CACHE.clear()


def _append(run_id: str) -> None:
    ai_runs.append_ai_run(
        "alice",
        AIActionRequest(action="content.rewrite", profile="alice", payload={}),
        AIActionSpec(name="content.rewrite", owner="content", default_backend="direct_llm"),
        AIActionResult(ok=True, action="content.rewrite", backend="direct_llm", run_id=run_id),
    )


def _seed(path: Path, created: list[str]) -> None:
    rows = [{"id": f"old-{i}", "action": "x", "ok": True, "created": stamp} for i, stamp in enumerate(created)]
    path.write_text(yaml.safe_dump({"profile": "alice", "runs": rows}), encoding="utf-8")


def test_append_drops_runs_older_than_retention(profile: Path) -> None:
    now = datetime.now(timezone.utc)
    _seed(
        profile / "ai-runs.yaml",
        [
            (now - timedelta(days=ai_runs.AI_RUNS_RETENTION_DAYS + 5)).isoformat(),
            (now - timedelta(days=10)).isoformat(),
            "not-a-date",
        ],
    )
    _append("new-1")
    ids = [run["id"] for run in ai_runs.load_ai_runs("alice")["runs"]]
    assert ids == ["old-1", "old-2", "new-1"]


def test_concurrent_appends_keep_every_row(profile: Path) -> None:
    threads = [threading.Thread(target=_append, args=(f"run-{i}",)) for i in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    ids = {run["id"] for run in ai_runs.load_ai_runs("alice")["runs"]}
    assert ids == {f"run-{i}" for i in range(12)}


def test_unchanged_file_is_parsed_once_and_copies_are_isolated(profile: Path) -> None:
    _append("a")
    ai_runs._LOAD_CACHE.clear()
    with patch("nblane.core.ai.runs._load_yaml_dict", wraps=ai_runs._load_yaml_dict) as parse:
        first = ai_runs.load_ai_runs("alice")
        first["runs"].append({"id": "mutated"})
        second = ai_runs.load_ai_runs("alice")
        assert parse.call_count == 1
    assert [run["id"] for run in second["runs"]] == ["a"]


def test_cache_sees_a_new_write(profile: Path) -> None:
    _append("a")
    assert [run["id"] for run in ai_runs.load_ai_runs("alice")["runs"]] == ["a"]
    _append("b")
    assert [run["id"] for run in ai_runs.load_ai_runs("alice")["runs"]] == ["a", "b"]
