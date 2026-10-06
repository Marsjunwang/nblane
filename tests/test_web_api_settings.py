"""Contract tests for the SPA Settings API."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.web_api import create_app

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"
PASSWORD = "correct horse battery staple"


def _write_users(path: Path) -> None:
    password_hash = auth_core.hash_password(
        PASSWORD,
        iterations=100_000,
        salt=b"settings-test-salt",
    )
    path.write_text(
        yaml.safe_dump(
            {
                "users": {
                    "admin": {
                        "display_name": "Administrator",
                        "password_hash": password_hash,
                        "role": "admin",
                    },
                    "member": {
                        "display_name": "Member",
                        "password_hash": password_hash,
                        "role": "member",
                        "profiles": ["alice"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )


def _profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for path in profile.rglob("*"):
        if path.is_file():
            path.write_text(
                path.read_text(encoding="utf-8")
                .replace("{Name}", name)
                .replace("{YYYY-MM-DD}", "2026-09-28"),
                encoding="utf-8",
            )
    return profile


class TestWebApiSettings(unittest.TestCase):
    def _client(self, root: Path, *, auth: bool = False) -> TestClient:
        patches = [
            patch("nblane.core.profile_io.PROFILES_DIR", root),
            patch("nblane.core.io.PROFILES_DIR", root),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        env = {"NBLANE_AUTH_FILE": ""}
        if auth:
            users = root / "users.yaml"
            _write_users(users)
            env.update(
                {
                    "NBLANE_AUTH_FILE": str(users),
                    "NBLANE_AUTH_SESSION_SECRET": "settings-test-secret",
                }
            )
        env_patch = patch.dict(os.environ, env)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        return TestClient(create_app())

    def test_connection_masks_key_and_explicit_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            with patch("nblane.core.llm._ENV_FILE", root / ".env"):
                saved = client.put(
                    "/api/v1/settings/connection",
                    json={
                        "base_url": "https://llm.example/v1",
                        "model": "test-model",
                        "api_key": "secret-api-key-1234",
                    },
                )
                self.assertEqual(saved.status_code, 200)
                self.assertNotIn("secret-api-key-1234", saved.text)
                self.assertTrue(saved.json()["api_key_set"])
                cleared = client.put(
                    "/api/v1/settings/connection",
                    json={"clear_api_key": True},
                )
        self.assertEqual(cleared.status_code, 200)
        self.assertFalse(cleared.json()["api_key_set"])

    def test_empty_key_keeps_existing_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            with patch("nblane.core.llm._ENV_FILE", root / ".env"):
                client.put(
                    "/api/v1/settings/connection",
                    json={"api_key": "secret-api-key-1234"},
                )
                response = client.put(
                    "/api/v1/settings/connection",
                    json={"model": "new-model"},
                )
                self.assertTrue(response.json()["api_key_set"])
                self.assertEqual(response.json()["model"], "new-model")

    def test_member_cannot_read_or_write_deployment_connection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root, auth=True)
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "member", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            read = client.get("/api/v1/settings/connection")
            write = client.put("/api/v1/settings/connection", json={"model": "x"})
        self.assertEqual(read.status_code, 403)
        self.assertEqual(read.json()["code"], "admin_required")
        self.assertEqual(write.status_code, 403)

    def test_local_models_catalog_activate_and_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            with patch.dict(os.environ, {"NBLANE_LOCAL_MODELS_DIR": str(root / "models"), "NBLANE_LOCAL_MT_MODEL": ""}):
                listing = client.get("/api/v1/settings/local-models")
                self.assertEqual(listing.status_code, 200)
                body = listing.json()
                self.assertEqual({m["tier"] for m in body["models"]}, {"fit", "quality"})
                self.assertNotIn("sha256", listing.text)
                unknown = client.post("/api/v1/settings/local-models/nope/install")
                self.assertEqual(unknown.status_code, 404)
                not_installed = client.put("/api/v1/settings/local-models/active", json={"model_id": body["models"][0]["id"]})
                self.assertEqual(not_installed.status_code, 400)
                empty_test = client.post("/api/v1/settings/local-models/test", json={"model_id": body["models"][0]["id"], "text": " "})
                self.assertEqual(empty_test.status_code, 400)
                disable = client.put("/api/v1/settings/local-models/active", json={"model_id": ""})
                self.assertEqual(disable.status_code, 200)
                self.assertEqual(disable.json()["active_model_id"], "")
            routes = client.patch(
                "/api/v1/profiles/alice/settings",
                json={"ai": {"local_translation": {"full": "local", "selection": "bogus"}}},
            )
            self.assertEqual(
                routes.json()["preferences"]["ai"]["local_translation"],
                {"selection": "local", "visible": "local", "full": "local"},
            )

    def test_member_cannot_manage_local_models(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root, auth=True)
            client.post("/api/v1/auth/login", json={"username": "member", "password": PASSWORD})
            read = client.get("/api/v1/settings/local-models")
            install = client.post("/api/v1/settings/local-models/hy-mt2-1.8b-q4/install")
        self.assertEqual(read.status_code, 403)
        self.assertEqual(install.status_code, 403)


    def test_profile_preferences_round_trip_and_secret_stripping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _profile(root)
            client = self._client(root)
            response = client.patch(
                "/api/v1/profiles/alice/settings",
                json={
                    "ai": {
                        "llm": {"reply_lang": "zh"},
                        "actions": {
                            "dashboard.daily_brief": {"backend": "llm"}
                        },
                        "api_key": "must-not-be-written",
                    }
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["preferences"]["ai"]["llm"]["reply_lang"], "zh")
            self.assertNotIn("api_key", response.text)
            self.assertNotIn("must-not-be-written", (profile / "web-preferences.yaml").read_text())

    def test_profile_codex_settings_do_not_include_auth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            response = client.patch(
                "/api/v1/profiles/alice/settings/codex",
                json={"model": "gpt-test", "attempts": 2},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["settings"]["model"], "gpt-test")
            self.assertNotIn("auth", response.text.lower())


if __name__ == "__main__":
    unittest.main()
