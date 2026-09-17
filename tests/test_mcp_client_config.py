"""Tests for nblane.core.mcp_client_config."""

from __future__ import annotations

import json
import re

from nblane.core import mcp_client_config


def _json_block(text: str) -> dict:
    match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
    assert match, "expected a ```json fenced block"
    return json.loads(match.group(1))


def test_resolve_command_prefers_explicit_executable() -> None:
    cmd, args = mcp_client_config.resolve_mcp_server_command("/x/bin/nblane-mcp")
    assert cmd == "/x/bin/nblane-mcp"
    assert args == []


def test_resolve_command_falls_back_to_module(monkeypatch) -> None:
    monkeypatch.setattr(mcp_client_config.shutil, "which", lambda name: None)
    cmd, args = mcp_client_config.resolve_mcp_server_command()
    assert cmd
    assert args == ["-m", "nblane.mcp_server"]


def test_entry_env_includes_root_and_profile(tmp_path) -> None:
    entry = mcp_client_config.build_mcp_server_entry(
        "alice", root=tmp_path, executable="/x/bin/nblane-mcp"
    )
    assert entry["command"] == "/x/bin/nblane-mcp"
    assert "args" not in entry
    assert entry["env"]["NBLANE_ROOT"] == str(tmp_path)
    assert entry["env"]["NBLANE_PROFILE"] == "alice"


def test_entry_prefills_single_profile(tmp_path, monkeypatch) -> None:
    import nblane.core.profile_io as profile_io

    monkeypatch.setattr(profile_io, "list_profiles", lambda: ["solo"])
    entry = mcp_client_config.build_mcp_server_entry(
        root=tmp_path, executable="/x/bin/nblane-mcp"
    )
    assert entry["env"]["NBLANE_PROFILE"] == "solo"


def test_entry_omits_profile_when_ambiguous(tmp_path, monkeypatch) -> None:
    import nblane.core.profile_io as profile_io

    monkeypatch.setattr(profile_io, "list_profiles", lambda: ["a", "b"])
    entry = mcp_client_config.build_mcp_server_entry(
        root=tmp_path, executable="/x/bin/nblane-mcp"
    )
    assert "NBLANE_PROFILE" not in entry["env"]


def test_openclaw_snippet_has_parseable_mcp_servers(tmp_path) -> None:
    body = mcp_client_config.build_openclaw_mcp_snippet(
        "alice", root=tmp_path, executable="/x/bin/nblane-mcp"
    )
    config = _json_block(body)
    server = config["mcp"]["servers"]["nblane"]
    assert server["command"] == "/x/bin/nblane-mcp"
    assert server["env"]["NBLANE_PROFILE"] == "alice"
    assert server["env"]["NBLANE_ROOT"] == str(tmp_path)


def test_openclaw_snippet_guides_when_profile_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mcp_client_config, "_default_profile", lambda root: None)
    body = mcp_client_config.build_openclaw_mcp_snippet(
        root=tmp_path, executable="/x/bin/nblane-mcp"
    )
    server = _json_block(body)["mcp"]["servers"]["nblane"]
    assert "NBLANE_PROFILE" not in server["env"]
    assert "NBLANE_PROFILE" in body
