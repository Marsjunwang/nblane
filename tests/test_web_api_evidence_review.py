"""Tests for the Evidence Review slice (GET queue + bulk/deprecate mutations).

Covers the triage queue read (status filters, summary counters, usage/skill
refs, review reasons, ETag header), the bulk accept/tag mutation (field/value
whitelist 422s, If-Match 412, disk persistence), and the reject (deprecate) /
restore mutation including missing-id reporting. 401/403 auth rules mirror
the other web_api suites.
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
from nblane.web_api import app, create_app

PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-evidence-review-test-secret"

EVIDENCE_POOL = {
    "profile": "alice",
    "evidence_entries": [
        {
            "id": "ev_alpha",
            "type": "project",
            "title": "Alpha",
            "strength": "strong",
            "breakthrough": True,
        },
        {
            "id": "ev_beta",
            "type": "practice",
            "title": "Beta",
            "review_status": "reviewed",
            "strength": "medium",
        },
        {"id": "ev_gamma", "type": "paper", "title": "Gamma", "deprecated": True},
        {"id": "ev_delta", "type": "course", "title": "Delta"},
    ],
}

SKILL_TREE = {
    "profile": "alice",
    "schema": "test-domain",
    "updated": "2026-09-10",
    "nodes": [
        {"id": "robotics", "status": "solid", "evidence_refs": ["ev_alpha"]},
        {"id": "navigation", "status": "learning"},
    ],
}


def _write_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "evidence-pool.yaml").write_text(
        yaml.safe_dump(dict(EVIDENCE_POOL, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "skill-tree.yaml").write_text(
        yaml.safe_dump(dict(SKILL_TREE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    return profile


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


def _pool_entries(profile: Path) -> list[dict]:
    raw = yaml.safe_load(
        (profile / "evidence-pool.yaml").read_text(encoding="utf-8")
    )
    return list(raw.get("evidence_entries") or [])


def _entry(profile: Path, entry_id: str) -> dict:
    for row in _pool_entries(profile):
        if str(row.get("id", "")) == entry_id:
            return row
    raise AssertionError(f"entry {entry_id} not found")


class EvidenceReviewTestBase(unittest.TestCase):
    """Shared env patching: profile roots plus git-backup isolation."""

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
        patcher = patch("nblane.core.profile_io.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)


class TestEvidenceReviewQueue(EvidenceReviewTestBase):
    """GET /evidence-review: filters, summary, usage refs, ETag."""

    def test_default_needs_review_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/alice/evidence-review")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["ETag"].startswith('W/"'))
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertEqual(payload["status"], "needs_review")
        # Only active, not-yet-reviewed rows land in the default queue.
        ids = [item["id"] for item in payload["items"]]
        self.assertEqual(ids, ["ev_alpha", "ev_delta"])
        by_id = {item["id"]: item for item in payload["items"]}
        # Usage refs come from the skill tree overlay.
        self.assertEqual(by_id["ev_alpha"]["usage_count"], 1)
        self.assertEqual(by_id["ev_alpha"]["skill_refs"], ["robotics"])
        self.assertEqual(by_id["ev_alpha"]["review_reason"], "needs_review")
        self.assertEqual(by_id["ev_alpha"]["strength"], "strong")
        # The raw row's 突破 flag projects into the queue item.
        self.assertTrue(by_id["ev_alpha"]["breakthrough"])
        self.assertFalse(by_id["ev_delta"]["breakthrough"])
        # Unrated strength is reported as such and feeds the review reason.
        self.assertEqual(by_id["ev_delta"]["strength"], "unrated")
        self.assertEqual(
            by_id["ev_delta"]["review_reason"], "missing_strength, needs_review"
        )
        self.assertEqual(
            payload["summary"],
            {
                "needs_review_count": 2,
                "unlinked_count": 2,
                "total_entries": 3,
                "deprecated_count": 1,
            },
        )

    def test_status_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            reviewed = client.get(
                "/api/v1/profiles/alice/evidence-review", params={"status": "reviewed"}
            )
            deprecated = client.get(
                "/api/v1/profiles/alice/evidence-review",
                params={"status": "deprecated"},
            )
            everything = client.get(
                "/api/v1/profiles/alice/evidence-review", params={"status": "all"}
            )
        self.assertEqual(
            [item["id"] for item in reviewed.json()["items"]], ["ev_beta"]
        )
        dep_items = deprecated.json()["items"]
        self.assertEqual([item["id"] for item in dep_items], ["ev_gamma"])
        self.assertTrue(dep_items[0]["deprecated"])
        self.assertEqual(len(everything.json()["items"]), 4)

    def test_query_filter_matches_id_and_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            by_title = client.get(
                "/api/v1/profiles/alice/evidence-review",
                params={"status": "all", "q": "alpha"},
            )
            by_id = client.get(
                "/api/v1/profiles/alice/evidence-review",
                params={"status": "all", "q": "ev_delta"},
            )
        self.assertEqual([i["id"] for i in by_title.json()["items"]], ["ev_alpha"])
        self.assertEqual([i["id"] for i in by_id.json()["items"]], ["ev_delta"])

    def test_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/nobody/evidence-review")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "profile_not_found")


class TestEvidenceReviewBulk(EvidenceReviewTestBase):
    """POST /evidence-review/bulk: accept and tag in one call."""

    def test_bulk_accept_updates_pool_on_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            client = self._client(root)
            etag = client.get("/api/v1/profiles/alice/evidence-review").headers[
                "ETag"
            ]
            response = client.post(
                "/api/v1/profiles/alice/evidence-review/bulk",
                json={
                    "ids": ["ev_alpha", "ev_delta"],
                    "field": "review_status",
                    "value": "reviewed",
                },
                headers={"If-Match": etag},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["changed"], 2)
            self.assertEqual(payload["missing"], [])
            self.assertNotEqual(response.headers["ETag"], etag)
            self.assertEqual(
                _entry(profile, "ev_alpha").get("review_status"), "reviewed"
            )
            self.assertEqual(
                _entry(profile, "ev_delta").get("review_status"), "reviewed"
            )
            # Unrelated rows and fields are untouched.
            self.assertEqual(_entry(profile, "ev_alpha").get("strength"), "strong")
            self.assertTrue(_entry(profile, "ev_gamma").get("deprecated"))

    def test_bulk_tag_strength(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/evidence-review/bulk",
                json={"ids": ["ev_delta"], "field": "strength", "value": "weak"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["changed"], 1)
            self.assertEqual(_entry(profile, "ev_delta").get("strength"), "weak")

    def test_bulk_clear_value_removes_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/evidence-review/bulk",
                json={"ids": ["ev_alpha"], "field": "strength", "value": ""},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["changed"], 1)
            self.assertNotIn("strength", _entry(profile, "ev_alpha"))

    def test_bulk_invalid_field_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/evidence-review/bulk",
                json={"ids": ["ev_alpha"], "field": "title", "value": "x"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_review_field")

    def test_bulk_invalid_value_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/evidence-review/bulk",
                json={"ids": ["ev_alpha"], "field": "strength", "value": "bogus"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_review_value")

    def test_bulk_empty_ids_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            blank = client.post(
                "/api/v1/profiles/alice/evidence-review/bulk",
                json={"ids": [], "field": "review_status", "value": "reviewed"},
            )
            whitespace = client.post(
                "/api/v1/profiles/alice/evidence-review/bulk",
                json={"ids": ["  "], "field": "review_status", "value": "reviewed"},
            )
        # Empty list fails request validation (min_length=1).
        self.assertEqual(blank.status_code, 422)
        # Whitespace-only ids pass validation but the route rejects them.
        self.assertEqual(whitespace.status_code, 422)
        self.assertEqual(whitespace.json()["code"], "empty_selection")

    def test_bulk_stale_if_match_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            etag = client.get("/api/v1/profiles/alice/evidence-review").headers[
                "ETag"
            ]
            first = client.post(
                "/api/v1/profiles/alice/evidence-review/bulk",
                json={"ids": ["ev_alpha"], "field": "review_status", "value": "reviewed"},
                headers={"If-Match": etag},
            )
            stale = client.post(
                "/api/v1/profiles/alice/evidence-review/bulk",
                json={"ids": ["ev_delta"], "field": "review_status", "value": "reviewed"},
                headers={"If-Match": etag},
            )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(stale.status_code, 412)
        self.assertEqual(stale.json()["code"], "etag_mismatch")
        # The 412 carries a fresh ETag so the client can reload and retry.
        self.assertEqual(stale.headers["ETag"], first.headers["ETag"])


class TestEvidenceReviewDeprecate(EvidenceReviewTestBase):
    """POST /evidence-review/deprecate: reject and restore."""

    def test_deprecate_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/evidence-review/deprecate",
                json={"ids": ["ev_alpha", "ev_ghost"]},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["changed"], 1)
            self.assertEqual(payload["missing"], ["ev_ghost"])
            self.assertTrue(_entry(profile, "ev_alpha").get("deprecated"))

            restore = client.post(
                "/api/v1/profiles/alice/evidence-review/deprecate",
                json={"ids": ["ev_alpha", "ev_gamma"], "deprecated": False},
            )
            self.assertEqual(restore.status_code, 200)
            self.assertEqual(restore.json()["changed"], 2)
            self.assertNotIn("deprecated", _entry(profile, "ev_alpha"))
            self.assertNotIn("deprecated", _entry(profile, "ev_gamma"))

    def test_deprecate_already_in_state_not_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/evidence-review/deprecate",
                json={"ids": ["ev_gamma"]},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["changed"], 0)


class TestEvidenceReviewScope(EvidenceReviewTestBase):
    """401/403 enforcement under auth-on."""

    def _auth_client(self, root: Path) -> TestClient:
        users_file = _write_users_file(root / "users.yaml")
        env = {
            "NBLANE_AUTH_FILE": str(users_file),
            "NBLANE_AUTH_SESSION_SECRET": TEST_SESSION_SECRET,
        }
        patcher = patch.dict(os.environ, env)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(create_app())

    def test_unauthenticated_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            client = self._auth_client(root)
            listing = client.get("/api/v1/profiles/alice/evidence-review")
            bulk = client.post(
                "/api/v1/profiles/alice/evidence-review/bulk",
                json={"ids": ["ev_alpha"], "field": "review_status", "value": "reviewed"},
            )
            deprecate = client.post(
                "/api/v1/profiles/alice/evidence-review/deprecate",
                json={"ids": ["ev_alpha"]},
            )
        self.assertEqual(listing.status_code, 401)
        self.assertEqual(bulk.status_code, 401)
        self.assertEqual(deprecate.status_code, 401)

    def test_member_forbidden_from_other_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root, "alice")
            _write_profile(root, "wang")
            client = self._auth_client(root)
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            forbidden = client.get("/api/v1/profiles/alice/evidence-review")
            forbidden_bulk = client.post(
                "/api/v1/profiles/alice/evidence-review/bulk",
                json={"ids": ["ev_alpha"], "field": "review_status", "value": "reviewed"},
            )
            allowed = client.get("/api/v1/profiles/wang/evidence-review")
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.json()["code"], "profile_forbidden")
        self.assertEqual(forbidden_bulk.status_code, 403)
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["profile"], "wang")


if __name__ == "__main__":
    unittest.main()
