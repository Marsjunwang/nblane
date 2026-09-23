"""Tests for the workshop (ttyd terminal) endpoint, web_api/workshop.py.

The http_get probe seam is injected via ``app.state.workshop_http_get`` so
these tests never touch the network.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.web_api import create_app

PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-workshop-test-secret"


class FakeResponse:
    """Minimal stand-in for an httpx response."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


def make_client(http_get=None) -> TestClient:
    """App with an injected probe seam (auth off)."""
    app = create_app()
    app.state.workshop_http_get = http_get or (lambda url, timeout: FakeResponse(200))
    return TestClient(app)


class TestWorkshopUrlConfig(unittest.TestCase):
    def test_default_url_is_same_origin_terminal_path(self) -> None:
        client = make_client()
        with patch.dict(os.environ, {"NBLANE_AUTH_FILE": "", "NBLANE_WORKSHOP_URL": ""}):
            payload = client.get("/api/v1/system/workshop").json()
        self.assertEqual(payload["url"], "/terminal/")

    def test_url_env_override(self) -> None:
        client = make_client()
        env = {
            "NBLANE_AUTH_FILE": "",
            "NBLANE_WORKSHOP_URL": "http://127.0.0.1:7668/",
        }
        with patch.dict(os.environ, env):
            payload = client.get("/api/v1/system/workshop").json()
        self.assertEqual(payload["url"], "http://127.0.0.1:7668/")


class TestWorkshopProbe(unittest.TestCase):
    def test_reachable_when_ttyd_answers(self) -> None:
        client = make_client()
        with patch.dict(os.environ, {"NBLANE_AUTH_FILE": ""}):
            payload = client.get("/api/v1/system/workshop").json()
        self.assertTrue(payload["reachable"])
        self.assertTrue(payload["checked_at"])

    def test_unreachable_when_ttyd_down(self) -> None:
        def down_http_get(url: str, timeout: float) -> FakeResponse:
            raise ConnectionError("refused")

        client = make_client(http_get=down_http_get)
        with patch.dict(os.environ, {"NBLANE_AUTH_FILE": ""}):
            response = client.get("/api/v1/system/workshop")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["reachable"])

    def test_probe_url_env_override(self) -> None:
        calls: list[str] = []

        def recording_http_get(url: str, timeout: float) -> FakeResponse:
            calls.append(url)
            return FakeResponse(200)

        client = make_client(http_get=recording_http_get)
        env = {
            "NBLANE_AUTH_FILE": "",
            "NBLANE_WORKSHOP_PROBE_URL": "http://127.0.0.1:17668",
        }
        with patch.dict(os.environ, env):
            client.get("/api/v1/system/workshop")
        self.assertEqual(calls, ["http://127.0.0.1:17668"])

    def test_cache_hit_avoids_second_probe(self) -> None:
        calls: list[str] = []

        def recording_http_get(url: str, timeout: float) -> FakeResponse:
            calls.append(url)
            return FakeResponse(200)

        client = make_client(http_get=recording_http_get)
        with patch.dict(os.environ, {"NBLANE_AUTH_FILE": ""}):
            first = client.get("/api/v1/system/workshop")
            second = client.get("/api/v1/system/workshop")
        self.assertEqual(first.json(), second.json())
        self.assertEqual(len(calls), 1)


class TestWorkshopAuth(unittest.TestCase):
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
                response = client.get("/api/v1/system/workshop")
        self.assertEqual(response.status_code, 401)
