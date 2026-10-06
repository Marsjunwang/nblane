"""Contract tests for the backup + personal agent settings API."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from nblane.web_api import create_app
from tests.test_web_api_settings import PASSWORD, _profile, _write_users

_TARGET = {
    "id": "openclaw-workspace", "label": "OpenClaw 工作区", "description": "", "path": "/srv/agent-data/openclaw/workspace",
    "commit_mode": "all", "exists": True, "is_git": True, "remote_url": "", "branch": "main", "upstream": "",
    "ahead": 2, "dirty": 0, "has_commits": True, "last_commit_at": "", "last_commit_subject": "", "key_path": "/k",
    "key_ready": False, "public_key": "", "last_run": {},
}
_STATUS = {
    "targets": [_TARGET],
    "timer": {"unit": "nblane-backup", "installed": False, "enabled": False, "next_run": "", "schedule": "每天 03:30"},
    "backups_dir": "/srv/backups/agents",
    "data_git": {"autocommit": True, "autopush": True},
}


class TestWebApiAgentsSetup(unittest.TestCase):
    def _client(self, root: Path, *, auth: bool = False) -> TestClient:
        for item in (
            patch("nblane.core.profile_io.PROFILES_DIR", root),
            patch("nblane.core.io.PROFILES_DIR", root),
        ):
            item.start()
            self.addCleanup(item.stop)
        env = {"NBLANE_AUTH_FILE": ""}
        if auth:
            users = root / "users.yaml"
            _write_users(users)
            env.update({"NBLANE_AUTH_FILE": str(users), "NBLANE_AUTH_SESSION_SECRET": "agents-test-secret"})
        env_patch = patch.dict(os.environ, env)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        return TestClient(create_app())

    def test_backup_status_and_unknown_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            with patch("nblane.core.backup_targets.status", return_value=_STATUS):
                listing = client.get("/api/v1/settings/backup")
                self.assertEqual(listing.status_code, 200)
                self.assertEqual(listing.json()["targets"][0]["ahead"], 2)
                missing = client.post("/api/v1/settings/backup/targets/..%2Fetc/key")
                # Never reaches a handler: the encoded slash fails routing.
                self.assertGreaterEqual(missing.status_code, 400)
                unknown = client.post("/api/v1/settings/backup/targets/nope/key")
                self.assertEqual(unknown.status_code, 404)
                self.assertEqual(unknown.json()["code"], "backup_target_not_found")

    def test_remote_test_passes_url_through_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            with patch("nblane.core.openclaw_setup.workspace_path", return_value=root):
                response = client.post(
                    "/api/v1/settings/backup/targets/openclaw-workspace/remote/test",
                    json={"url": "https://github.com/a/b.git"},
                )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["ok"])
        self.assertIn("SSH", response.json()["message"])

    def test_openclaw_job_blocked_and_unknown_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            with patch("nblane.core.openclaw_setup.start_job", side_effect=__import__(
                "nblane.core.openclaw_setup", fromlist=["x"]
            ).OpenClawSetupError("本机还没有可用的 OpenClaw。")):
                blocked = client.post("/api/v1/settings/agents/openclaw/connect", json={"profile": "alice"})
            self.assertEqual(blocked.status_code, 400)
            self.assertEqual(blocked.json()["code"], "agent_job_blocked")
            unknown = client.post("/api/v1/settings/agents/openclaw/rm-rf", json={})
            self.assertEqual(unknown.status_code, 404)
            bad_gateway = client.post("/api/v1/settings/agents/openclaw-gateway", json={"action": "kill"})
            self.assertEqual(bad_gateway.status_code, 422)

    def test_openclaw_status_never_exposes_llm_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root)
            with patch("nblane.core.openclaw_setup.Path.home", return_value=root), patch(
                "nblane.core.llm.current_config",
                side_effect=lambda mask_key=True: {
                    "base_url": "https://llm.example/v1", "model": "m", "configured": True,
                    "api_key": "sk-****" if mask_key else "sk-plain-secret",
                },
            ):
                response = client.get("/api/v1/settings/agents/openclaw")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("sk-plain-secret", response.text)
        self.assertTrue(response.json()["llm_reusable"])

    def test_member_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _profile(root)
            client = self._client(root, auth=True)
            client.post("/api/v1/auth/login", json={"username": "member", "password": PASSWORD})
            calls = [
                client.get("/api/v1/settings/backup"),
                client.put("/api/v1/settings/backup/timer", json={"enabled": True}),
                client.get("/api/v1/settings/agents/openclaw"),
                client.post("/api/v1/settings/agents/openclaw/install", json={"profile": "alice"}),
            ]
        self.assertEqual([call.status_code for call in calls], [403, 403, 403, 403])


if __name__ == "__main__":
    unittest.main()
