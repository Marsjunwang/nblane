"""Tests for /api/v1/accounts (admin account management) and agent guards."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.core import auth_store
from nblane.web_api import create_app

PASSWORD = "correct horse battery staple"
SECRET = "web-api-accounts-test-secret"


def _write_users(path: Path) -> Path:
    stored = auth_core.hash_password(PASSWORD, iterations=100_000, salt=b"0123456789abcdef")
    path.write_text(
        yaml.safe_dump(
            {
                "users": {
                    "admin": {"display_name": "Admin", "password_hash": stored, "role": "admin"},
                    "wang": {"display_name": "Wang", "password_hash": stored, "role": "member",
                             "profile": "wang"},
                    # Admin-role agent: the guard (not require_admin) must refuse it.
                    "bot": {"display_name": "Bot", "password_hash": stored, "role": "admin",
                            "agent": True},
                }
            }
        ),
        encoding="utf-8",
    )
    return path


class AccountsTestBase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "auth").mkdir()
        self.users_file = _write_users(self.root / "auth" / "users.yaml")
        self.profiles = self.root / "profiles"
        (self.profiles / "wang").mkdir(parents=True)
        for target in (
            "nblane.core.paths.PROFILES_DIR",
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, self.profiles)
            patcher.start()
            self.addCleanup(patcher.stop)
        for patcher in (
            patch.dict(os.environ, {"NBLANE_AUTH_FILE": str(self.users_file),
                                    "NBLANE_AUTH_SESSION_SECRET": SECRET}),
            patch("nblane.core.git_backup.record_change"),
            # Fast hashes for created/reset passwords.
            patch.object(auth_store.auth_core, "hash_password",
                         lambda pw, _real=auth_core.hash_password, **kw: _real(pw, iterations=100_000)),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        auth_core.clear_users_cache()
        self.addCleanup(auth_core.clear_users_cache)
        self.app = create_app()

    def login(self, username: str = "admin", password: str = PASSWORD) -> TestClient:
        client = TestClient(self.app)
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return client


class TestAccounts(AccountsTestBase):
    def test_member_forbidden(self) -> None:
        client = self.login("wang")
        self.assertEqual(client.get("/api/v1/accounts").status_code, 403)
        response = client.post("/api/v1/accounts", json={"id": "x", "password": "0123456789"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "admin_required")

    def test_unauthenticated_401(self) -> None:
        self.assertEqual(TestClient(self.app).get("/api/v1/accounts").status_code, 401)

    def test_list_has_no_hashes(self) -> None:
        auth_store.create_api_token("bot", "openclaw")
        client = self.login()
        response = client.get("/api/v1/accounts")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("hash", response.text)
        self.assertNotIn("pbkdf2", response.text)
        rows = {row["id"]: row for row in response.json()}
        self.assertEqual(sorted(rows), ["admin", "bot", "wang"])
        self.assertTrue(rows["bot"]["agent"])
        self.assertEqual(rows["bot"]["tokens"][0]["name"], "openclaw")
        self.assertEqual(set(rows["bot"]["tokens"][0]), {"id", "name", "created"})

    def test_create_with_profile(self) -> None:
        client = self.login()
        response = client.post(
            "/api/v1/accounts",
            json={"id": "li", "display_name": "Li", "role": "member",
                  "password": "0123456789", "create_profile": True},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["profiles"], ["li"])
        self.assertTrue(body["must_change_password"])
        self.assertTrue((self.profiles / "li" / "SKILL.md").exists())
        # The new user can log in and is asked to change the password.
        li = self.login("li", "0123456789")
        self.assertTrue(li.get("/api/v1/auth/me").json()["must_change_password"])

    def test_create_errors(self) -> None:
        client = self.login()
        dup = client.post("/api/v1/accounts", json={"id": "wang", "password": "0123456789"})
        self.assertEqual((dup.status_code, dup.json()["code"]), (409, "user_exists"))
        weak = client.post("/api/v1/accounts", json={"id": "new", "password": "short"})
        self.assertEqual((weak.status_code, weak.json()["code"]), (422, "weak_password"))
        exists = client.post(
            "/api/v1/accounts",
            json={"id": "wang2", "password": "0123456789", "create_profile": True},
        )
        self.assertEqual(exists.status_code, 200)
        (self.profiles / "taken").mkdir()
        taken = client.post(
            "/api/v1/accounts",
            json={"id": "taken", "password": "0123456789", "create_profile": True},
        )
        self.assertEqual((taken.status_code, taken.json()["code"]), (409, "profile_exists"))
        self.assertNotIn("taken", auth_core.load_users())

    def test_create_with_schema(self) -> None:
        client = self.login()
        response = client.post(
            "/api/v1/accounts",
            json={"id": "ad", "password": "0123456789", "create_profile": True,
                  "schema": "autonomous-driving"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        tree = yaml.safe_load((self.profiles / "ad" / "skill-tree.yaml").read_text(encoding="utf-8"))
        self.assertEqual(tree["schema"], "autonomous-driving")
        skill = (self.profiles / "ad" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("自动驾驶工程师", skill)

    def test_create_unknown_schema_writes_nothing(self) -> None:
        client = self.login()
        for bad in ("no-such-domain", "../x"):
            response = client.post(
                "/api/v1/accounts",
                json={"id": "nope", "password": "0123456789", "create_profile": True,
                      "schema": bad},
            )
            self.assertEqual((response.status_code, response.json()["code"]), (422, "unknown_schema"))
        self.assertNotIn("nope", auth_core.load_users())
        self.assertFalse((self.profiles / "nope").exists())

    def test_list_schemas(self) -> None:
        member = self.login("wang")
        response = member.get("/api/v1/schemas")
        self.assertEqual(response.status_code, 200, response.text)
        rows = {row["name"]: row for row in response.json()}
        self.assertIn("robotics-engineer", rows)
        self.assertEqual(
            set(rows["autonomous-driving"]),
            {"name", "domain", "description", "node_count", "source"},
        )
        self.assertEqual(rows["autonomous-driving"]["node_count"], 82)
        self.assertEqual(TestClient(self.app).get("/api/v1/schemas").status_code, 401)

    def test_patch_disable_and_guards(self) -> None:
        client = self.login()
        wang = self.login("wang")
        response = client.patch("/api/v1/accounts/wang", json={"disabled": True, "display_name": "W"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["disabled"])
        self.assertEqual(response.json()["display_name"], "W")
        self.assertEqual(wang.get("/api/v1/auth/me").status_code, 401)
        self_disable = client.patch("/api/v1/accounts/admin", json={"disabled": True})
        self.assertEqual((self_disable.status_code, self_disable.json()["code"]),
                         (409, "cannot_disable_self"))
        demote = client.patch("/api/v1/accounts/admin", json={"role": "member"})
        self.assertEqual(demote.json()["code"], "cannot_demote_self")
        missing = client.patch("/api/v1/accounts/ghost", json={"display_name": "x"})
        self.assertEqual((missing.status_code, missing.json()["code"]), (404, "user_not_found"))

    def test_reset_password(self) -> None:
        client = self.login()
        wang = self.login("wang")
        response = client.post("/api/v1/accounts/wang/reset-password", json={"password": "temp-password-1"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["must_change_password"])
        self.assertEqual(wang.get("/api/v1/auth/me").status_code, 401)
        self.login("wang", "temp-password-1")

    def test_tokens_create_and_revoke(self) -> None:
        client = self.login()
        created = client.post("/api/v1/accounts/bot/tokens", json={"name": "openclaw"})
        self.assertEqual(created.status_code, 200, created.text)
        body = created.json()
        self.assertTrue(body["token"].startswith(f"nbl_{body['id']}_"))
        headers = {"Authorization": f"Bearer {body['token']}"}
        bearer = TestClient(self.app)
        self.assertEqual(bearer.get("/api/v1/auth/me", headers=headers).json()["id"], "bot")
        revoked = client.delete(f"/api/v1/accounts/bot/tokens/{body['id']}")
        self.assertEqual(revoked.status_code, 200)
        self.assertEqual(bearer.get("/api/v1/auth/me", headers=headers).status_code, 401)
        again = client.delete(f"/api/v1/accounts/bot/tokens/{body['id']}")
        self.assertEqual((again.status_code, again.json()["code"]), (404, "token_not_found"))


class TestAgentForbidden(AccountsTestBase):
    """Agent accounts (cookie or bearer) cannot manage accounts or credentials."""

    def _assert_forbidden(self, client: TestClient, headers: dict[str, str] | None = None) -> None:
        for method, url, body in (
            ("POST", "/api/v1/accounts", {"id": "x", "password": "0123456789"}),
            ("PATCH", "/api/v1/accounts/wang", {"disabled": True}),
            ("POST", "/api/v1/accounts/wang/reset-password", {"password": "0123456789"}),
            ("POST", "/api/v1/accounts/bot/tokens", {"name": "t"}),
            ("DELETE", "/api/v1/accounts/bot/tokens/abc", None),
            ("POST", "/api/v1/auth/password", {"current_password": PASSWORD, "new_password": "0123456789"}),
            ("POST", "/api/v1/auth/logout-all", None),
        ):
            response = client.request(method, url, json=body, headers=headers)
            self.assertEqual(response.status_code, 403, (url, response.text))
            self.assertEqual(response.json()["code"], "agent_forbidden")
        self.assertFalse(auth_core.load_users()["wang"].disabled)

    def test_agent_cookie_forbidden(self) -> None:
        self._assert_forbidden(self.login("bot"))

    def test_agent_bearer_forbidden(self) -> None:
        token, _ = auth_store.create_api_token("bot", "t")
        self._assert_forbidden(TestClient(self.app), {"Authorization": f"Bearer {token}"})


if __name__ == "__main__":
    unittest.main()
