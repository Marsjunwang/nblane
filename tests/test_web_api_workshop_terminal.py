"""Tests for the workshop admin gates: /terminal/ proxy, key bar, input box,
and Settings → 车间 routes (web_api/workshop.py, workshop_terminal.py).

The ttyd upstream is replaced by ``app.state.workshop_proxy_http_get`` and
core service calls are patched, so nothing touches the network, tmux or
systemd.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from nblane.core import auth as auth_core
from nblane.core import workshop_service
from nblane.web_api import create_app

PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-workshop-terminal-test-secret"


class FakeUpstream:
    def __init__(self, status_code: int = 200, content: bytes = b"<html>ttyd</html>") -> None:
        self.status_code = status_code
        self.content = content
        self.headers = {"content-type": "text/html", "content-length": str(len(content))}


class _AuthMixin:
    """Auth-on app with one admin and one member."""

    def setUp(self) -> None:  # noqa: D401 - unittest hook
        self._tmp = tempfile.TemporaryDirectory()
        stored = auth_core.hash_password(PASSWORD, iterations=100_000, salt=b"0123456789abcdef")
        users_file = Path(self._tmp.name) / "users.yaml"
        users_file.write_text(
            yaml.safe_dump(
                {
                    "users": {
                        "boss": {"display_name": "Boss", "password_hash": stored, "role": "admin", "teams": ["*"]},
                        "guest": {"display_name": "Guest", "password_hash": stored, "role": "member", "profiles": []},
                    }
                }
            ),
            encoding="utf-8",
        )
        self._env = patch.dict(
            os.environ,
            {"NBLANE_AUTH_FILE": str(users_file), "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET},
        )
        self._env.start()
        self.app = create_app()
        self.upstream_calls: list[str] = []

        def fake_get(url: str, headers: dict[str, str]) -> FakeUpstream:
            self.upstream_calls.append(url)
            return FakeUpstream()

        self.app.state.workshop_proxy_http_get = fake_get
        self.app.state.workshop_http_get = lambda url, timeout: FakeUpstream()

    def tearDown(self) -> None:  # noqa: D401 - unittest hook
        self._env.stop()
        self._tmp.cleanup()

    def client_as(self, username: str | None) -> TestClient:
        client = TestClient(self.app, base_url="http://testserver")
        if username:
            response = client.post("/api/v1/auth/login", json={"username": username, "password": PASSWORD})
            assert response.status_code == 200, response.text
        return client


class TestTerminalProxy(_AuthMixin, unittest.TestCase):
    def test_anonymous_is_rejected(self) -> None:
        response = self.client_as(None).get("/terminal/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.upstream_calls, [])

    def test_member_is_forbidden(self) -> None:
        response = self.client_as("guest").get("/terminal/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.upstream_calls, [])

    def test_admin_reaches_ttyd_with_path_and_query(self) -> None:
        response = self.client_as("boss").get("/terminal/token?fontSize=24")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "<html>ttyd</html>")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(self.upstream_calls, [f"{workshop_service.upstream_url()}/token?fontSize=24"])

    def test_bare_path_redirects(self) -> None:
        response = self.client_as(None).get("/terminal", follow_redirects=False)
        self.assertEqual(response.status_code, 308)
        self.assertEqual(response.headers["location"], "/terminal/")

    def test_upstream_down_is_502(self) -> None:
        def down(url: str, headers: dict[str, str]) -> FakeUpstream:
            raise ConnectionError("refused")

        self.app.state.workshop_proxy_http_get = down
        self.assertEqual(self.client_as("boss").get("/terminal/").status_code, 502)

    def test_websocket_rejects_member_and_cross_origin(self) -> None:
        for user, headers in (
            (None, {}),
            ("guest", {}),
            ("boss", {"origin": "https://evil.example"}),
        ):
            with self.subTest(user=user, headers=headers):
                client = self.client_as(user)
                with self.assertRaises(WebSocketDisconnect) as ctx:
                    with client.websocket_connect("/terminal/ws", subprotocols=["tty"], headers=headers) as socket:
                        socket.receive_bytes()
                self.assertEqual(ctx.exception.code, 1008)


class TestOriginCheck(unittest.TestCase):
    def _ws(self, headers: dict[str, str]):
        from types import SimpleNamespace

        return SimpleNamespace(headers=headers)

    def test_forwarded_host_counts_as_same_origin(self) -> None:
        from nblane.web_api.workshop_terminal import _same_origin

        self.assertTrue(_same_origin(self._ws({"origin": "http://localhost:18504", "host": "127.0.0.1:18504", "x-forwarded-host": "localhost:18504"})))
        self.assertTrue(_same_origin(self._ws({"origin": "http://127.0.0.1:18504", "host": "127.0.0.1:18504"})))
        self.assertFalse(_same_origin(self._ws({"origin": "https://evil.example", "host": "127.0.0.1:18504", "x-forwarded-host": "www.nblane.cloud"})))


class TestKeyBarAndInput(_AuthMixin, unittest.TestCase):
    def test_status_reports_admin_flag(self) -> None:
        self.assertTrue(self.client_as("boss").get("/api/v1/system/workshop").json()["admin"])
        self.assertFalse(self.client_as("guest").get("/api/v1/system/workshop").json()["admin"])

    def test_member_cannot_send_keys_or_text(self) -> None:
        client = self.client_as("guest")
        with patch.object(workshop_service, "send_keys") as send_keys, patch.object(workshop_service, "send_text") as send_text:
            self.assertEqual(client.post("/api/v1/system/workshop/keys", json={"keys": ["esc"]}).status_code, 403)
            self.assertEqual(client.post("/api/v1/system/workshop/input", json={"text": "ls"}).status_code, 403)
        send_keys.assert_not_called()
        send_text.assert_not_called()

    def test_admin_keys_and_input_reach_tmux_layer(self) -> None:
        client = self.client_as("boss")
        with patch.object(workshop_service, "send_keys") as send_keys, patch.object(workshop_service, "send_text") as send_text:
            self.assertEqual(client.post("/api/v1/system/workshop/keys", json={"keys": ["esc", "esc2"]}).status_code, 200)
            self.assertEqual(client.post("/api/v1/system/workshop/input", json={"text": "你好", "submit": False}).status_code, 200)
        send_keys.assert_called_once_with(["esc", "esc2"])
        send_text.assert_called_once_with("你好", submit=False)

    def test_service_errors_become_400(self) -> None:
        client = self.client_as("boss")
        response = client.post("/api/v1/system/workshop/keys", json={"keys": ["not-a-key"]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "workshop_keys_failed")


class TestSettingsRoutes(_AuthMixin, unittest.TestCase):
    def test_member_is_forbidden(self) -> None:
        client = self.client_as("guest")
        self.assertEqual(client.get("/api/v1/settings/workshop").status_code, 403)
        self.assertEqual(client.post("/api/v1/settings/workshop/install").status_code, 403)

    def test_unknown_action_is_404(self) -> None:
        self.assertEqual(self.client_as("boss").post("/api/v1/settings/workshop/explode").status_code, 404)

    def test_settings_roundtrip_and_validation(self) -> None:
        client = self.client_as("boss")
        with patch.object(workshop_service, "probe", return_value=False):
            ok = client.put("/api/v1/settings/workshop", json={"font_size_mobile": 18})
            bad = client.put("/api/v1/settings/workshop", json={"renderer": "svg"})
        self.assertEqual(ok.status_code, 200, ok.text)
        self.assertEqual(ok.json()["settings"]["font_size_mobile"], 18)
        self.assertEqual(bad.status_code, 400)
        # The page's font size follows the saved setting.
        self.assertEqual(client.get("/api/v1/system/workshop").json()["font_size_mobile"], 18)


if __name__ == "__main__":
    unittest.main()
