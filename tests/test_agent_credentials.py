"""Tests for core/agent_credentials and /api/v1/settings/agents/token."""

from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import agent_credentials as creds
from nblane.core import auth as auth_core
from nblane.core import auth_store
from nblane.web_api import create_app

PASSWORD = "correct horse battery staple"
SECRET = "agent-credentials-test-secret"


def _write_users(path: Path) -> None:
    stored = auth_core.hash_password(PASSWORD, iterations=100_000, salt=b"0123456789abcdef")
    path.write_text(
        yaml.safe_dump(
            {
                "users": {
                    "admin": {"display_name": "Admin", "password_hash": stored, "role": "admin"},
                    "wang": {"display_name": "Wang", "password_hash": stored, "role": "member",
                             "profile": "wang"},
                    "openclaw": {"display_name": "Bot", "password_hash": stored, "role": "admin",
                                 "agent": True},
                }
            }
        ),
        encoding="utf-8",
    )


class CredsBase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "auth").mkdir()
        self.users_file = self.root / "auth" / "users.yaml"
        _write_users(self.users_file)
        self.env_file = self.root / "cfg" / "nblane" / "api.env"
        profiles = self.root / "profiles"
        (profiles / "wang").mkdir(parents=True)
        for target in (
            "nblane.core.paths.PROFILES_DIR",
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, profiles)
            patcher.start()
            self.addCleanup(patcher.stop)
        env = patch.dict(os.environ, {
            "NBLANE_AUTH_FILE": str(self.users_file),
            "NBLANE_AUTH_SESSION_SECRET": SECRET,
            "NBLANE_OPENCLAW_API_ENV_FILE": str(self.env_file),
            "NBLANE_OPENCLAW_API_USERNAME": "",
        })
        env.start()
        self.addCleanup(env.stop)
        auth_core.clear_users_cache()
        self.addCleanup(auth_core.clear_users_cache)

    def tokens(self, user: str = "openclaw") -> list[str]:
        auth_core.clear_users_cache()
        return [t.id for t in auth_core.load_users()[user].api_tokens]


class TestCore(CredsBase):
    def test_path_override_and_account_default(self) -> None:
        self.assertEqual(creds.api_env_path(), self.env_file)
        self.assertEqual(creds.agent_account_id(), "openclaw")
        with patch.dict(os.environ, {"NBLANE_OPENCLAW_API_ENV_FILE": "", "XDG_CONFIG_HOME": "/x"}):
            self.assertEqual(creds.api_env_path(), Path("/x/nblane/api.env"))

    def test_read_env_token_tolerant(self) -> None:
        self.env_file.parent.mkdir(parents=True)
        self.env_file.write_text(
            "# c\nNBLANE_OPENCLAW_API_TOKEN = \"nbl_a_b\"  # note\n", encoding="utf-8"
        )
        self.assertEqual(creds.read_env_token(self.env_file), "nbl_a_b")
        self.assertEqual(creds.read_env_token(self.root / "missing"), "")

    def test_status_unconfigured(self) -> None:
        state = creds.status()
        self.assertTrue(state["account_exists"])
        self.assertTrue(state["account_is_agent"])
        self.assertFalse(state["configured"])
        self.assertFalse(state["token_valid"])

    def test_first_configure_writes_0600_and_keeps_password(self) -> None:
        self.env_file.parent.mkdir(parents=True)
        self.env_file.write_text("# keep me\nNBLANE_OPENCLAW_API_PASSWORD=hunter2hunter2\n", encoding="utf-8")
        result = creds.configure_token()
        text = self.env_file.read_text(encoding="utf-8")
        self.assertIn("# keep me\n", text)
        self.assertIn("NBLANE_OPENCLAW_API_PASSWORD=hunter2hunter2\n", text)
        token = creds.read_env_token(self.env_file)
        self.assertTrue(token.startswith("nbl_"))
        self.assertEqual(stat.S_IMODE(self.env_file.stat().st_mode), 0o600)
        self.assertFalse(result["rotated"])
        self.assertTrue(result["token_valid"])
        self.assertTrue(result["password_fallback"])
        self.assertTrue(result["created"])
        self.assertNotIn(token, repr(result))
        self.assertNotIn("hunter2", repr(result))
        self.assertEqual(self.tokens(), [result["token_id"]])

    def test_new_file_parent_is_0700(self) -> None:
        creds.configure_token()
        self.assertEqual(stat.S_IMODE(self.env_file.parent.stat().st_mode), 0o700)

    def test_rotate_replaces_line_and_revokes_old(self) -> None:
        first = creds.configure_token()
        manual, _ = auth_store.create_api_token("openclaw", "manual")
        second = creds.configure_token()
        self.assertTrue(second["rotated"])
        self.assertNotEqual(first["token_id"], second["token_id"])
        text = self.env_file.read_text(encoding="utf-8")
        self.assertEqual(text.count("NBLANE_OPENCLAW_API_TOKEN="), 1)
        ids = self.tokens()
        self.assertNotIn(first["token_id"], ids)
        self.assertIn(second["token_id"], ids)
        # Tokens not referenced by the file are left alone.
        self.assertIn(auth_core._api_token_id(manual), ids)

    def test_verify_failure_restores_file_and_revokes_new(self) -> None:
        first = creds.configure_token()
        before = self.env_file.read_text(encoding="utf-8")
        with patch.object(creds, "_verify", return_value=False):
            with self.assertRaises(creds.AgentCredentialsError) as ctx:
                creds.configure_token()
        self.assertEqual(ctx.exception.code, "token_verify_failed")
        self.assertEqual(self.env_file.read_text(encoding="utf-8"), before)
        self.assertEqual(self.tokens(), [first["token_id"]])

    def test_verify_failure_on_fresh_file_removes_it(self) -> None:
        with patch.object(creds, "_verify", return_value=False):
            with self.assertRaises(creds.AgentCredentialsError):
                creds.configure_token()
        self.assertFalse(self.env_file.exists())
        self.assertEqual(self.tokens(), [])

    def test_non_agent_account(self) -> None:
        with patch.dict(os.environ, {"NBLANE_OPENCLAW_API_USERNAME": "wang"}):
            with self.assertRaises(creds.AgentCredentialsError) as ctx:
                creds.configure_token()
        self.assertEqual(ctx.exception.code, "not_agent_account")
        self.assertFalse(self.env_file.exists())

    def test_missing_account(self) -> None:
        with patch.dict(os.environ, {"NBLANE_OPENCLAW_API_USERNAME": "ghost"}):
            with self.assertRaises(creds.AgentCredentialsError) as ctx:
                creds.configure_token()
            self.assertFalse(creds.status()["account_exists"])
        self.assertEqual(ctx.exception.code, "agent_account_missing")

    def test_auth_not_configured(self) -> None:
        with patch.dict(os.environ, {"NBLANE_AUTH_FILE": ""}):
            with self.assertRaises(creds.AgentCredentialsError) as ctx:
                creds.configure_token()
        self.assertEqual(ctx.exception.code, "auth_not_configured")

    def test_status_detects_revoked_token(self) -> None:
        result = creds.configure_token()
        auth_store.revoke_api_token("openclaw", result["token_id"])
        auth_core.clear_users_cache()
        state = creds.status()
        self.assertTrue(state["configured"])
        self.assertFalse(state["token_valid"])


class TestApi(CredsBase):
    URL = "/api/v1/settings/agents/token"

    def setUp(self) -> None:
        super().setUp()
        self.app = create_app()

    def login(self, username: str) -> TestClient:
        client = TestClient(self.app)
        response = client.post("/api/v1/auth/login", json={"username": username, "password": PASSWORD})
        self.assertEqual(response.status_code, 200, response.text)
        return client

    def test_admin_get_and_post(self) -> None:
        client = self.login("admin")
        state = client.get(self.URL).json()
        self.assertFalse(state["configured"])
        self.assertEqual(state["env_path"], str(self.env_file))
        response = client.post(self.URL)
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["token_valid"])
        self.assertNotIn(creds.read_env_token(self.env_file), response.text)
        again = client.post(self.URL).json()
        self.assertTrue(again["rotated"])

    def test_error_mapping(self) -> None:
        client = self.login("admin")
        with patch.dict(os.environ, {"NBLANE_OPENCLAW_API_USERNAME": "wang"}):
            response = client.post(self.URL)
        self.assertEqual((response.status_code, response.json()["code"]), (409, "not_agent_account"))
        with patch.dict(os.environ, {"NBLANE_OPENCLAW_API_USERNAME": "ghost"}):
            response = client.post(self.URL)
        self.assertEqual((response.status_code, response.json()["code"]), (409, "agent_account_missing"))
        with patch.object(creds, "_verify", return_value=False):
            response = client.post(self.URL)
        self.assertEqual((response.status_code, response.json()["code"]), (500, "token_verify_failed"))

    def test_member_forbidden(self) -> None:
        client = self.login("wang")
        self.assertEqual(client.get(self.URL).status_code, 403)
        self.assertEqual(client.post(self.URL).status_code, 403)
        self.assertFalse(self.env_file.exists())

    def test_agent_cookie_forbidden(self) -> None:
        response = self.login("openclaw").post(self.URL)
        self.assertEqual((response.status_code, response.json()["code"]), (403, "agent_forbidden"))
        self.assertFalse(self.env_file.exists())

    def test_agent_bearer_forbidden(self) -> None:
        token, _ = auth_store.create_api_token("openclaw", "t")
        headers = {"Authorization": f"Bearer {token}"}
        client = TestClient(self.app)
        response = client.post(self.URL, headers=headers)
        self.assertEqual((response.status_code, response.json()["code"]), (403, "agent_forbidden"))
        self.assertFalse(self.env_file.exists())


if __name__ == "__main__":
    unittest.main()
