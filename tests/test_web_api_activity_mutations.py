"""Tests for the Agent Activity apply/dismiss mutation endpoints.

Covers the full approval loop (seed candidate → GET with ETag → apply via
API → evidence pool row lands), the dismiss path, If-Match/412 conflict
protection, 409 state conflicts, and the 401/403 auth rules.
"""

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
from nblane.core.paths import REPO_ROOT
from nblane.core.review_actions import save_review_candidates_to_activity
from nblane.web_api import app, create_app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"
PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-activity-mutations-test-secret"

WINDOW_START = "2026-09-14"
WINDOW_END = "2026-09-19"


def _template_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            text = text.replace("{YYYY-MM-DD}", "2026-09-19")
            file_path.write_text(text, encoding="utf-8")
    return profile


def _seed_evidence_candidate(title: str) -> str:
    """Persist one pending Review evidence candidate; return its item id."""
    stored = save_review_candidates_to_activity(
        "alice",
        WINDOW_START,
        WINDOW_END,
        "evidence",
        [
            {
                "title": title,
                "type": "project",
                "date": "2026-09-15",
                "url": "https://example.com/nav",
                "summary": f"summary for {title}",
            }
        ],
    )
    return str(stored[0]["id"])


def _write_users_file(path: Path) -> Path:
    stored = auth_core.hash_password(
        PASSWORD,
        iterations=100_000,
        salt=b"0123456789abcdef",
    )
    path.write_text(
        yaml.safe_dump(
            {
                "users": {
                    "wang": {
                        "display_name": "Wang",
                        "password_hash": stored,
                        "role": "member",
                        "profile": "wang",
                        "teams": ["example-team"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return path


class TestActivityMutations(unittest.TestCase):
    """Apply/dismiss loop against a tmp copy of the template profile."""

    def _client(self, root: Path) -> TestClient:
        # Loaders resolve profile dirs through profile_io; patch both the
        # canonical module and the core.io compat facade (repo convention).
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(app)

    def test_apply_evidence_candidate_full_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            item_id = _seed_evidence_candidate("Built nav stack")

            detail = client.get(f"/api/v1/profiles/alice/activity/{item_id}")
            etag_before = detail.headers.get("etag")
            applied = client.post(
                f"/api/v1/profiles/alice/activity/{item_id}/apply",
                headers={"If-Match": etag_before or ""},
            )
            reapplied = client.post(
                f"/api/v1/profiles/alice/activity/{item_id}/apply"
            )
            pool = yaml.safe_load(
                (profile / "evidence-pool.yaml").read_text(encoding="utf-8")
            )
            activity = yaml.safe_load(
                (profile / "agent-activity.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["status"], "pending")
        self.assertIsNotNone(etag_before)
        self.assertTrue(etag_before.startswith('W/"'))

        self.assertEqual(applied.status_code, 200)
        body = applied.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["item"]["id"], item_id)
        self.assertEqual(body["item"]["status"], "applied")
        etag_after = applied.headers.get("etag")
        self.assertIsNotNone(etag_after)
        self.assertNotEqual(etag_before, etag_after)

        row = next(
            entry
            for entry in pool["evidence_entries"]
            if entry["title"] == "Built nav stack"
        )
        self.assertEqual(row["type"], "project")
        self.assertEqual(row["date"], "2026-09-15")
        self.assertEqual(row["url"], "https://example.com/nav")
        stored = next(
            item for item in activity["items"] if item["id"] == item_id
        )
        self.assertEqual(stored["status"], "applied")

        # Applying a second time is a state conflict, not a re-apply.
        self.assertEqual(reapplied.status_code, 409)
        conflict = reapplied.json()
        self.assertEqual(conflict["code"], "activity_item_not_pending")
        self.assertEqual(conflict["item"]["status"], "applied")

    def test_apply_without_if_match_proceeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            item_id = _seed_evidence_candidate("No precondition apply")
            response = client.post(
                f"/api/v1/profiles/alice/activity/{item_id}/apply"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["item"]["status"], "applied")

    def test_stale_if_match_returns_412_with_current_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            keep_id = _seed_evidence_candidate("Keep pending")
            other_id = _seed_evidence_candidate("Dismiss me")
            detail = client.get(f"/api/v1/profiles/alice/activity/{keep_id}")
            stale_etag = detail.headers["etag"]
            # Any other mutation rewrites agent-activity.yaml → new sha256.
            dismissed = client.post(
                f"/api/v1/profiles/alice/activity/{other_id}/dismiss"
            )
            conflicted = client.post(
                f"/api/v1/profiles/alice/activity/{keep_id}/apply",
                headers={"If-Match": stale_etag},
            )
            matching = client.post(
                f"/api/v1/profiles/alice/activity/{keep_id}/apply",
                headers={"If-Match": conflicted.headers["etag"]},
            )
        self.assertEqual(dismissed.status_code, 200)
        self.assertEqual(conflicted.status_code, 412)
        body = conflicted.json()
        self.assertEqual(body["code"], "etag_mismatch")
        self.assertEqual(body["item"]["id"], keep_id)
        self.assertEqual(body["item"]["status"], "pending")
        # The 412 also carries the fresh ETag so the client can retry.
        self.assertNotEqual(conflicted.headers["etag"], stale_etag)
        self.assertEqual(matching.status_code, 200)
        self.assertEqual(matching.json()["item"]["status"], "applied")

    def test_dismiss_with_and_without_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            noted_id = _seed_evidence_candidate("Not relevant")
            plain_id = _seed_evidence_candidate("No note dismiss")

            detail = client.get(f"/api/v1/profiles/alice/activity/{noted_id}")
            noted = client.post(
                f"/api/v1/profiles/alice/activity/{noted_id}/dismiss",
                json={"note": "not relevant"},
                headers={"If-Match": detail.headers["etag"]},
            )
            plain = client.post(
                f"/api/v1/profiles/alice/activity/{plain_id}/dismiss"
            )
            redismissed = client.post(
                f"/api/v1/profiles/alice/activity/{noted_id}/dismiss"
            )
            activity = yaml.safe_load(
                (profile / "agent-activity.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(noted.status_code, 200)
        self.assertTrue(noted.json()["ok"])
        self.assertEqual(noted.json()["item"]["status"], "dismissed")
        self.assertIn("etag", noted.headers)
        self.assertEqual(plain.status_code, 200)
        self.assertEqual(plain.json()["item"]["status"], "dismissed")
        stored = next(
            item for item in activity["items"] if item["id"] == noted_id
        )
        self.assertEqual(stored["status"], "dismissed")
        self.assertEqual(stored["dismiss_note"], "not relevant")
        # Dismissing an already-dismissed item is a state conflict.
        self.assertEqual(redismissed.status_code, 409)
        self.assertEqual(
            redismissed.json()["code"], "activity_item_not_dismissable"
        )

    def test_unknown_item_404_on_both_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            applied = client.post("/api/v1/profiles/alice/activity/act:nope/apply")
            dismissed = client.post(
                "/api/v1/profiles/alice/activity/act:nope/dismiss"
            )
        for response in (applied, dismissed):
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["code"], "activity_item_not_found")


class TestActivityMutationAuth(unittest.TestCase):
    """401/403 rules for the mutation endpoints under auth-on."""

    def _auth_client(self, root: Path) -> TestClient:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        users_file = _write_users_file(root / "users.yaml")
        env = {
            "NBLANE_AUTH_FILE": str(users_file),
            "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
        }
        patcher = patch.dict(os.environ, env)
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(create_app())

    def test_unauthenticated_mutations_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, "alice")
            client = self._auth_client(root)
            item_id = _seed_evidence_candidate("Auth check")
            applied = client.post(
                f"/api/v1/profiles/alice/activity/{item_id}/apply"
            )
            dismissed = client.post(
                f"/api/v1/profiles/alice/activity/{item_id}/dismiss"
            )
        self.assertEqual(applied.status_code, 401)
        self.assertEqual(dismissed.status_code, 401)

    def test_member_forbidden_from_other_profile_403(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, "alice")
            _template_profile(root, "wang")
            client = self._auth_client(root)
            item_id = _seed_evidence_candidate("Scope check")
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            applied = client.post(
                f"/api/v1/profiles/alice/activity/{item_id}/apply"
            )
            dismissed = client.post(
                f"/api/v1/profiles/alice/activity/{item_id}/dismiss"
            )
        self.assertEqual(login.status_code, 200)
        for response in (applied, dismissed):
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["code"], "profile_forbidden")


if __name__ == "__main__":
    unittest.main()
