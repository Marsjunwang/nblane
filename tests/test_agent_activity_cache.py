"""agent-activity.yaml is parsed once while unchanged; writes invalidate."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from nblane.core import agent_activity


@pytest.fixture()
def profile(tmp_path: Path):
    path = tmp_path / "alice"
    path.mkdir()
    agent_activity._LOAD_CACHE.clear()
    with patch("nblane.core.agent_activity.git_backup.record_change"):
        yield path
    agent_activity._LOAD_CACHE.clear()


def _seed(path: Path, ids: list[str]) -> None:
    items = [{"id": i, "status": "failed", "title": i} for i in ids]
    (path / "agent-activity.yaml").write_text(yaml.safe_dump({"profile": "alice", "items": items}), encoding="utf-8")


def test_unchanged_file_is_parsed_once_and_copies_are_isolated(profile: Path) -> None:
    _seed(profile, ["a"])
    with patch("nblane.core.agent_activity._load_yaml_dict", wraps=agent_activity._load_yaml_dict) as parse:
        first = agent_activity.load_agent_activity(profile)
        first["items"].append({"id": "mutated"})
        second = agent_activity.load_agent_activity(profile)
        assert parse.call_count == 1
    assert [item["id"] for item in second["items"]] == ["a"]


def test_save_invalidates_the_cache(profile: Path) -> None:
    _seed(profile, ["a"])
    activity = agent_activity.load_agent_activity(profile)
    activity["items"].append({"id": "b", "status": "failed", "title": "b"})
    agent_activity.save_agent_activity(profile, activity)
    assert [item["id"] for item in agent_activity.load_agent_activity(profile)["items"]] == ["a", "b"]


def test_external_rewrite_is_seen(profile: Path) -> None:
    _seed(profile, ["a"])
    agent_activity.load_agent_activity(profile)
    _seed(profile, ["a", "c"])
    assert [item["id"] for item in agent_activity.load_agent_activity(profile)["items"]] == ["a", "c"]
