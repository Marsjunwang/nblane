"""Tests for the assistant (OpenClaw) status endpoint, web_api/assistant.py.

All probe seams (which / runner / http_get) are injected via ``app.state``
so these tests never spawn a subprocess or touch the network.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.web_api import create_app
from nblane.web_api import assistant as assistant_mod

PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-assistant-test-secret"


class FakeResponse:
    """Minimal stand-in for an httpx response."""

    def __init__(self, status_code: int, body: object = None) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> object:
        if self._body is None:
            raise ValueError("no json body")
        return self._body


def _completed(argv: list[str], stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr="")


def make_runner(
    *,
    version: str | None = "openclaw 2026.9.4",
    mcp_stdout: str = "NAME     TRANSPORT\nnblane   stdio\n",
    automations: object | None = (
        '[{"key": "daily", "enabled": true}, {"key": "weekly", "enabled": false}]'
    ),
    fail: bool = False,
):
    """Fake subprocess runner keyed on the argv it receives."""
    calls: list[list[str]] = []

    def runner(argv: list[str], timeout: float) -> subprocess.CompletedProcess:
        calls.append(list(argv))
        if fail:
            raise subprocess.TimeoutExpired(argv, timeout)
        if argv[1:] == ["--version"]:
            if version is None:
                return _completed(argv, "", returncode=1)
            return _completed(argv, version + "\n")
        if argv[1:] == ["mcp", "list"]:
            return _completed(argv, mcp_stdout)
        if argv[1:] == ["automations", "list", "--all", "--json"]:
            if automations is None:
                return _completed(argv, "boom", returncode=1)
            return _completed(argv, automations if isinstance(automations, str) else "")
        raise AssertionError(f"unexpected argv: {argv}")

    runner.calls = calls  # type: ignore[attr-defined]
    return runner


def make_client(
    *,
    which_result: str | None = "/usr/local/bin/openclaw",
    runner=None,
    http_get=None,
) -> TestClient:
    """App with injected probe seams (auth off)."""
    app = create_app()
    app.state.assistant_which = lambda _name: which_result
    app.state.assistant_runner = runner or make_runner()
    app.state.assistant_http_get = http_get or (
        lambda url, timeout: FakeResponse(200, {"ok": True, "uptime_ms": 123456})
    )
    return TestClient(app)


class TestAssistantUnavailable(unittest.TestCase):
    def test_openclaw_absent_returns_available_false(self) -> None:
        runner = make_runner()
        client = make_client(which_result=None, runner=runner)
        with patch.dict(os.environ, {"NBLANE_AUTH_FILE": ""}):
            response = client.get("/api/v1/system/assistant")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["available"])
        self.assertIsNone(payload["version"])
        self.assertIsNone(payload["gateway"])
        self.assertIsNone(payload["mcp_nblane_registered"])
        self.assertIsNone(payload["automations"])
        # Deep link + timestamp still present.
        self.assertEqual(payload["console_url"], "http://127.0.0.1:18789/")
        self.assertTrue(payload["checked_at"])
        # Binary absent → no subprocess probes at all.
        self.assertEqual(runner.calls, [])

    def test_console_url_env_override(self) -> None:
        client = make_client(which_result=None)
        env = {
            "NBLANE_AUTH_FILE": "",
            "NBLANE_OPENCLAW_CONSOLE_URL": "https://example.com/openclaw/",
        }
        with patch.dict(os.environ, env):
            response = client.get("/api/v1/system/assistant")
        self.assertEqual(
            response.json()["console_url"], "https://example.com/openclaw/"
        )


class TestAssistantProbes(unittest.TestCase):
    def test_all_probes_ok_payload(self) -> None:
        client = make_client()
        with patch.dict(os.environ, {"NBLANE_AUTH_FILE": ""}):
            response = client.get("/api/v1/system/assistant")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["available"])
        self.assertEqual(payload["version"], "openclaw 2026.9.4")
        self.assertEqual(
            payload["gateway"], {"ready": True, "uptime_ms": 123456}
        )
        self.assertTrue(payload["mcp_nblane_registered"])
        self.assertEqual(payload["automations"], {"total": 2, "enabled": 1})

    def test_gateway_down_leaves_other_probes_intact(self) -> None:
        def down_http_get(url: str, timeout: float) -> FakeResponse:
            raise ConnectionError("refused")

        client = make_client(http_get=down_http_get)
        with patch.dict(os.environ, {"NBLANE_AUTH_FILE": ""}):
            payload = client.get("/api/v1/system/assistant").json()
        self.assertTrue(payload["available"])
        self.assertEqual(
            payload["gateway"], {"ready": False, "uptime_ms": None}
        )
        self.assertEqual(payload["version"], "openclaw 2026.9.4")
        self.assertTrue(payload["mcp_nblane_registered"])
        self.assertEqual(payload["automations"], {"total": 2, "enabled": 1})

    def test_automations_jobs_wrapped_shape(self) -> None:
        # OpenClaw 2026.9 wraps the list in a "jobs" key.
        client = make_client(
            runner=make_runner(
                automations='{"jobs": [{"key": "a", "enabled": true}], "total": 1}'
            )
        )
        with patch.dict(os.environ, {"NBLANE_AUTH_FILE": ""}):
            payload = client.get("/api/v1/system/assistant").json()
        self.assertEqual(payload["automations"], {"total": 1, "enabled": 1})

    def test_probe_timeouts_yield_null_fields(self) -> None:        client = make_client(runner=make_runner(fail=True))
        with patch.dict(os.environ, {"NBLANE_AUTH_FILE": ""}):
            payload = client.get("/api/v1/system/assistant").json()
        self.assertTrue(payload["available"])
        self.assertIsNone(payload["version"])
        self.assertIsNone(payload["mcp_nblane_registered"])
        self.assertIsNone(payload["automations"])
        # HTTP seam still fine.
        self.assertTrue(payload["gateway"]["ready"])

    def test_cache_hit_avoids_second_probe_round(self) -> None:
        runner = make_runner()
        client = make_client(runner=runner)
        with patch.dict(os.environ, {"NBLANE_AUTH_FILE": ""}):
            first = client.get("/api/v1/system/assistant")
            second = client.get("/api/v1/system/assistant")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())
        # One probe round = version + mcp list + automations list.
        self.assertEqual(len(runner.calls), 3)


class TestAssistantAuth(unittest.TestCase):
    def test_401_when_auth_on_without_cookie(self) -> None:
        stored = auth_core.hash_password(
            PASSWORD, iterations=100_000, salt=b"0123456789abcdef"
        )
        with tempfile.TemporaryDirectory() as tmp:
            users_file = Path(tmp) / "users.yaml"
            users_file.write_text(
                yaml.safe_dump(
                    {
                        "users": {
                            "admin": {
                                "display_name": "Admin",
                                "password_hash": stored,
                                "role": "admin",
                                "teams": ["*"],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            env = {
                "NBLANE_AUTH_FILE": str(users_file),
                "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
            }
            with patch.dict(os.environ, env):
                client = make_client()
                response = client.get("/api/v1/system/assistant")
        self.assertEqual(response.status_code, 401)


class TestProbeHelpers(unittest.TestCase):
    """Unit-level checks on the individual probe parsers."""

    def test_automations_accepts_dict_with_items_key(self) -> None:
        runner = make_runner(
            automations='{"automations": [{"enabled": true}, {"enabled": true}]}'
        )
        result = assistant_mod._probe_automations(runner)
        self.assertIsNotNone(result)
        self.assertEqual((result.total, result.enabled), (2, 2))

    def test_automations_invalid_json_returns_none(self) -> None:
        runner = make_runner(automations="not json")
        self.assertIsNone(assistant_mod._probe_automations(runner))

    def test_mcp_not_registered(self) -> None:
        runner = make_runner(mcp_stdout="NAME  TRANSPORT\nother stdio\n")
        self.assertFalse(assistant_mod._probe_mcp_registered(runner))

    def test_gateway_uptime_missing_is_null(self) -> None:
        status = assistant_mod._probe_gateway(
            lambda url, timeout: FakeResponse(200, {"ok": True}),
            "http://127.0.0.1:18789",
        )
        self.assertTrue(status.ready)
        self.assertIsNone(status.uptime_ms)
