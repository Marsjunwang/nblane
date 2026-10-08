"""Tests for the M1 cookie-auth slice of the FastAPI SPA backend."""

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
from nblane.web_api.auth import GENERIC_LOGIN_ERROR, LoginRateLimiter

PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-auth-test-secret"


def _write_users_file(path: Path) -> Path:
    """Create a users yaml with one admin, hashed via core/auth."""
    stored = auth_core.hash_password(
        PASSWORD,
        iterations=100_000,
        salt=b"0123456789abcdef",
    )
    path.write_text(
        yaml.safe_dump(
            {
                "users": {
                    "admin": {
                        "display_name": "Admin",
                        "password_hash": stored,
                        "role": "admin",
                        "teams": ["*"],
                    },
                    "wang": {
                        "display_name": "Wang",
                        "password_hash": stored,
                        "role": "member",
                        "profile": "wang",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def _auth_off_env() -> dict[str, str]:
    return {"NBLANE_AUTH_FILE": "", "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET}


class TestAuthOff(unittest.TestCase):
    """With NBLANE_AUTH_FILE unset, auth is off and everything is open."""

    def test_me_returns_synthetic_local_admin(self) -> None:
        with patch.dict(os.environ, _auth_off_env()):
            client = TestClient(create_app())
            response = client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["id"], "local")
        self.assertEqual(payload["role"], "admin")
        self.assertFalse(payload["auth_enabled"])

    def test_protected_routes_open_without_cookie(self) -> None:
        with patch.dict(os.environ, _auth_off_env()):
            client = TestClient(create_app())
            self.assertEqual(client.get("/api/v1/health").status_code, 200)
            self.assertEqual(client.get("/api/v1/profiles").status_code, 200)

    def test_login_rejected_when_auth_not_configured(self) -> None:
        with patch.dict(os.environ, _auth_off_env()):
            client = TestClient(create_app())
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": PASSWORD},
            )
        self.assertEqual(response.status_code, 400)


class TestAuthOn(unittest.TestCase):
    """Cookie login flow against a tmp users file."""

    def _client(self, tmp: Path, app=None) -> TestClient:
        users_file = _write_users_file(tmp / "users.yaml")
        env = {
            "NBLANE_AUTH_FILE": str(users_file),
            "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
        }
        patcher = patch.dict(os.environ, env)
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app if app is not None else create_app())

    def test_login_sets_httponly_cookie_and_me_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp))
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": PASSWORD},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["id"], "admin")
            self.assertEqual(payload["display_name"], "Admin")
            self.assertEqual(payload["role"], "admin")
            self.assertTrue(payload["auth_enabled"])

            set_cookie = response.headers["set-cookie"]
            self.assertIn(f"{auth_core.AUTH_SESSION_COOKIE_NAME}=", set_cookie)
            self.assertIn("HttpOnly", set_cookie)
            self.assertIn("samesite=lax", set_cookie.lower())
            self.assertIn("Path=/", set_cookie)

            me = client.get("/api/v1/auth/me")
            self.assertEqual(me.status_code, 200)
            self.assertEqual(me.json()["id"], "admin")

    def test_member_login_carries_profile_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp))
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["role"], "member")
        self.assertEqual(payload["profiles"], ["wang"])

    def test_wrong_password_401_generic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp))
            bad_password = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "wrong"},
            )
            unknown_user = client.post(
                "/api/v1/auth/login",
                json={"username": "nobody", "password": PASSWORD},
            )
        self.assertEqual(bad_password.status_code, 401)
        self.assertEqual(unknown_user.status_code, 401)
        # Same generic message either way: no user enumeration.
        self.assertEqual(bad_password.json()["detail"], GENERIC_LOGIN_ERROR)
        self.assertEqual(
            bad_password.json()["detail"], unknown_user.json()["detail"]
        )

    def test_protected_routes_401_without_cookie(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp))
            self.assertEqual(client.get("/api/v1/profiles").status_code, 401)
            self.assertEqual(client.get("/api/v1/profiles/alice/summary").status_code, 401)
            self.assertEqual(client.get("/api/v1/profiles/alice/health").status_code, 401)
            self.assertEqual(client.get("/api/v1/profiles/alice/goals").status_code, 401)
            self.assertEqual(client.get("/api/v1/profiles/alice/evidence").status_code, 401)
            self.assertEqual(client.get("/api/v1/profiles/alice/evidence/ev_1").status_code, 401)
            self.assertEqual(client.get("/api/v1/auth/me").status_code, 401)
            # Liveness probe and auth endpoints stay open.
            self.assertEqual(client.get("/api/v1/health").status_code, 200)
            self.assertEqual(client.post("/api/v1/auth/logout").status_code, 200)

    def test_tampered_cookie_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp))
            client.cookies.set(auth_core.AUTH_SESSION_COOKIE_NAME, "garbage.token")
            response = client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_logout_invalidates_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp))
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            self.assertEqual(client.get("/api/v1/auth/me").status_code, 200)
            logout = client.post("/api/v1/auth/logout")
            self.assertEqual(logout.status_code, 200)
            self.assertEqual(client.get("/api/v1/auth/me").status_code, 401)
            self.assertEqual(client.get("/api/v1/profiles").status_code, 401)

    def test_rate_limit_429_after_repeated_failures(self) -> None:
        limiter = LoginRateLimiter(max_failures=2, window_seconds=60.0)
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp), app=create_app(login_rate_limiter=limiter))
            for _ in range(2):
                response = client.post(
                    "/api/v1/auth/login",
                    json={"username": "admin", "password": "wrong"},
                )
                self.assertEqual(response.status_code, 401)
            # Budget exhausted: even the correct password is now refused.
            blocked = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": PASSWORD},
            )
            self.assertEqual(blocked.status_code, 429)

    def test_successful_login_resets_failure_budget(self) -> None:
        limiter = LoginRateLimiter(max_failures=2, window_seconds=60.0)
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp), app=create_app(login_rate_limiter=limiter))
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "wrong"},
            )
            self.assertEqual(response.status_code, 401)
            ok = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": PASSWORD},
            )
            self.assertEqual(ok.status_code, 200)
            # Budget was cleared, so two fresh failures are needed to block.
            for _ in range(2):
                response = client.post(
                    "/api/v1/auth/login",
                    json={"username": "admin", "password": "wrong"},
                )
                self.assertEqual(response.status_code, 401)
            self.assertEqual(
                client.post(
                    "/api/v1/auth/login",
                    json={"username": "admin", "password": "wrong"},
                ).status_code,
                429,
            )


class TestSessionsAndTokens(unittest.TestCase):
    """Session versions, password change, logout-all, disable, API tokens."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.users_file = _write_users_file(Path(tmp.name) / "users.yaml")
        patcher = patch.dict(
            os.environ,
            {
                "NBLANE_AUTH_FILE": str(self.users_file),
                "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        auth_core.clear_users_cache()
        self.addCleanup(auth_core.clear_users_cache)
        self.app = create_app()

    def _login(self, username: str = "admin", password: str = PASSWORD) -> TestClient:
        client = TestClient(self.app)
        response = client.post(
            "/api/v1/auth/login", json={"username": username, "password": password}
        )
        self.assertEqual(response.status_code, 200, response.text)
        return client

    def _edit_user(self, user_id: str, **fields) -> None:
        raw = yaml.safe_load(self.users_file.read_text(encoding="utf-8"))
        raw["users"][user_id].update(fields)
        self.users_file.write_text(yaml.safe_dump(raw), encoding="utf-8")

    def test_legacy_cookie_without_sv_still_valid(self) -> None:
        import json

        payload = {"user_id": "admin", "kind": auth_core.AUTH_SESSION_KIND, "iat": 1,
                   "exp": 4_000_000_000}
        b64 = auth_core._b64(json.dumps(payload, separators=(",", ":")).encode())
        token = f"{b64}.{auth_core._auth_session_token_signature(b64)}"
        client = TestClient(self.app)
        client.cookies.set(auth_core.AUTH_SESSION_COOKIE_NAME, token)
        self.assertEqual(client.get("/api/v1/auth/me").status_code, 200)

    def test_password_change_invalidates_other_sessions(self) -> None:
        current = self._login()
        other = self._login()
        wrong = current.post(
            "/api/v1/auth/password",
            json={"current_password": "nope", "new_password": "brand-new-password"},
        )
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(wrong.json()["code"], "invalid_current_password")
        weak = current.post(
            "/api/v1/auth/password",
            json={"current_password": PASSWORD, "new_password": "short"},
        )
        self.assertEqual(weak.status_code, 422)
        self.assertEqual(weak.json()["code"], "weak_password")
        ok = current.post(
            "/api/v1/auth/password",
            json={"current_password": PASSWORD, "new_password": "brand-new-password"},
        )
        self.assertEqual(ok.status_code, 200, ok.text)
        self.assertFalse(ok.json()["must_change_password"])
        self.assertEqual(current.get("/api/v1/auth/me").status_code, 200)
        self.assertEqual(other.get("/api/v1/auth/me").status_code, 401)
        self._login(password="brand-new-password")

    def test_logout_all(self) -> None:
        first = self._login()
        second = self._login()
        response = first.post("/api/v1/auth/logout-all")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(first.get("/api/v1/auth/me").status_code, 401)
        self.assertEqual(second.get("/api/v1/auth/me").status_code, 401)
        self._login()

    def test_disabled_user_cookie_and_login_401(self) -> None:
        client = self._login("wang")
        self._edit_user("wang", disabled=True)
        self.assertEqual(client.get("/api/v1/auth/me").status_code, 401)
        response = TestClient(self.app).post(
            "/api/v1/auth/login", json={"username": "wang", "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], GENERIC_LOGIN_ERROR)

    def test_bearer_token_and_revoke(self) -> None:
        from nblane.core import auth_store

        token, record = auth_store.create_api_token("wang", "cli")
        client = TestClient(self.app)
        headers = {"Authorization": f"Bearer {token}"}
        me = client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["id"], "wang")
        bad = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}x"})
        self.assertEqual(bad.status_code, 401)
        auth_store.revoke_api_token("wang", record.id)
        self.assertEqual(client.get("/api/v1/auth/me", headers=headers).status_code, 401)

    def test_must_change_password_in_me(self) -> None:
        self._edit_user("wang", must_change_password=True)
        client = self._login("wang")
        self.assertTrue(client.get("/api/v1/auth/me").json()["must_change_password"])

    def test_load_users_cache_invalidates_on_file_change(self) -> None:
        self.assertEqual(auth_core.load_users()["wang"].display_name, "Wang")
        self._edit_user("wang", display_name="Wang Jun Changed")
        self.assertEqual(
            auth_core.load_users()["wang"].display_name, "Wang Jun Changed"
        )


class TestProfilesListingScope(unittest.TestCase):
    """GET /api/v1/profiles is scope-filtered (M-API-1)."""

    def _client(self, tmp: Path) -> TestClient:
        users_file = _write_users_file(tmp / "users.yaml")
        profiles_root = tmp / "profiles"
        for name in ("wang", "alice"):
            (profiles_root / name).mkdir(parents=True)
        env = {
            "NBLANE_AUTH_FILE": str(users_file),
            "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
        }
        env_patcher = patch.dict(os.environ, env)
        self.addCleanup(env_patcher.stop)
        env_patcher.start()
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, profiles_root)
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(create_app())

    def test_member_sees_only_own_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp))
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            response = client.get("/api/v1/profiles")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p["name"] for p in response.json()], ["wang"])

    def test_admin_sees_all_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp))
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            response = client.get("/api/v1/profiles")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p["name"] for p in response.json()], ["alice", "wang"])

    def test_unauthenticated_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp))
            response = client.get("/api/v1/profiles")
        self.assertEqual(response.status_code, 401)


class TestLoginRateLimitKeying(unittest.TestCase):
    """Rate-limit buckets are keyed on ip+username, honoring trusted XFF."""

    def _client(
        self, tmp: Path, limiter: LoginRateLimiter, *, trust_proxy: str = ""
    ) -> TestClient:
        users_file = _write_users_file(tmp / "users.yaml")
        env = {
            "NBLANE_AUTH_FILE": str(users_file),
            "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
            "NBLANE_TRUST_PROXY_HEADERS": trust_proxy,
        }
        patcher = patch.dict(os.environ, env)
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(create_app(login_rate_limiter=limiter))

    def test_bucket_key_includes_username(self) -> None:
        limiter = LoginRateLimiter(max_failures=2, window_seconds=60.0)
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp), limiter)
            for _ in range(2):
                response = client.post(
                    "/api/v1/auth/login",
                    json={"username": "admin", "password": "wrong"},
                )
                self.assertEqual(response.status_code, 401)
            # admin's bucket is exhausted ...
            blocked = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": PASSWORD},
            )
            self.assertEqual(blocked.status_code, 429)
            # ... but a different username from the same client IP is not.
            other = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            self.assertEqual(other.status_code, 200)

    def test_xff_ignored_unless_trusted(self) -> None:
        limiter = LoginRateLimiter(max_failures=2, window_seconds=60.0)
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp), limiter, trust_proxy="")
            for _ in range(2):
                response = client.post(
                    "/api/v1/auth/login",
                    json={"username": "admin", "password": "wrong"},
                    headers={"X-Forwarded-For": "1.1.1.1"},
                )
                self.assertEqual(response.status_code, 401)
            # A spoofed XFF does not move the client into a fresh bucket.
            blocked = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": PASSWORD},
                headers={"X-Forwarded-For": "9.9.9.9"},
            )
            self.assertEqual(blocked.status_code, 429)

    def test_xff_trusted_separates_buckets(self) -> None:
        limiter = LoginRateLimiter(max_failures=2, window_seconds=60.0)
        with tempfile.TemporaryDirectory() as tmp:
            client = self._client(Path(tmp), limiter, trust_proxy="1")
            for _ in range(2):
                response = client.post(
                    "/api/v1/auth/login",
                    json={"username": "admin", "password": "wrong"},
                    headers={"X-Forwarded-For": "1.1.1.1, 10.0.0.1"},
                )
                self.assertEqual(response.status_code, 401)
            # First XFF hop is the bucket key: 1.1.1.1 is blocked ...
            blocked = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": PASSWORD},
                headers={"X-Forwarded-For": "1.1.1.1"},
            )
            self.assertEqual(blocked.status_code, 429)
            # ... while the same username from another client IP still works.
            ok = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": PASSWORD},
                headers={"X-Forwarded-For": "2.2.2.2"},
            )
            self.assertEqual(ok.status_code, 200)


if __name__ == "__main__":
    unittest.main()
