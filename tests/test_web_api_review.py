"""Tests for the weekly Review slice (GET aggregation + save/apply mutations).

Covers the review read (explicit/default/invalid windows, candidate buckets
from kanban Done + learning log, ETag header), the save-to-activity mutation
(candidate-type whitelist, 412), and the apply mutation (evidence pool
writeback + crystallized marking, kanban queue append, public draft creation,
per-candidate failure reporting). 401/403 auth rules mirror the other
web_api suites.
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
from nblane.web_api import app, create_app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"
PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-review-test-secret"

WINDOW_START = "2026-09-14"
WINDOW_END = "2026-09-20"

KANBAN_FIXTURE = """# alice · Kanban

## Doing

- (empty)

---

## Done

- [x] Crystallized task
  - id: done-cryst
  - outcome: already crystallized
  - completed_on: 2026-09-15
  - crystallized: true

- [x] Fresh task
  - id: done-fresh
  - outcome: shipped the thing
  - completed_on: 2026-09-16
  - a detail line

- [x] Public task
  - id: done-public
  - outcome: public-worthy outcome
  - completed_on: 2026-09-17
  - tags: visibility/public_candidate

- [x] Old task
  - id: done-old
  - outcome: outside the window
  - completed_on: 2026-08-01

---

## Queue

- (empty)

---

## Someday / Maybe

- (empty)

---
"""

LEARNING_LOG_FIXTURE = {
    "profile": "alice",
    "updated": "2026-09-19",
    "resources": [
        {
            "id": "res-1",
            "title": "VLA survey",
            "kind": "paper",
            "status": "processed",
            "added_at": "2026-09-16",
            "next_actions": [
                {"title": "Reproduce the benchmark", "target": "kanban_queue"},
                {"title": "Ignore me", "target": "other"},
            ],
        },
        {
            "id": "res-2",
            "title": "Public notes",
            "kind": "blog",
            "status": "processed",
            "added_at": "2026-09-17",
            "visibility": "public_candidate",
        },
        {
            "id": "res-old",
            "title": "Old resource",
            "kind": "book",
            "status": "archived",
            "added_at": "2026-01-01",
            "next_actions": [{"title": "Stale action", "target": "kanban_queue"}],
        },
    ],
}


def _template_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            text = text.replace("{YYYY-MM-DD}", "2026-09-19")
            file_path.write_text(text, encoding="utf-8")
    (profile / "kanban.md").write_text(KANBAN_FIXTURE, encoding="utf-8")
    (profile / "learning-log.yaml").write_text(
        yaml.safe_dump(
            dict(LEARNING_LOG_FIXTURE, profile=name), allow_unicode=True
        ),
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


def _activity_items(profile: Path) -> list[dict]:
    raw = yaml.safe_load(
        (profile / "agent-activity.yaml").read_text(encoding="utf-8")
    )
    return list((raw or {}).get("items") or [])


def _kanban_text(profile: Path) -> str:
    return (profile / "kanban.md").read_text(encoding="utf-8")


class ReviewTestBase(unittest.TestCase):
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


class TestWeeklyReviewGet(ReviewTestBase):
    """GET /review: windows, candidate buckets, ETag."""

    def _get(self, client: TestClient, **params: str):
        return client.get("/api/v1/profiles/alice/review", params=params)

    def test_explicit_window_collects_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = self._get(
                client, start=WINDOW_START, end=WINDOW_END
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["ETag"].startswith('W/"'))
        payload = response.json()
        self.assertEqual(payload["profile"], "alice")
        self.assertEqual(payload["week_start"], WINDOW_START)
        self.assertEqual(payload["week_end"], WINDOW_END)
        # The out-of-window Done card is excluded.
        self.assertEqual(
            payload["done_task_ids"], ["done-cryst", "done-fresh", "done-public"]
        )
        # Evidence candidates skip already-crystallized cards.
        ev_ids = [c["task_id"] for c in payload["evidence_candidates"]]
        self.assertEqual(ev_ids, ["done-fresh", "done-public"])
        # Next actions come from in-window learning resources only.
        next_titles = [c["title"] for c in payload["next_queue_candidates"]]
        self.assertEqual(next_titles, ["Reproduce the benchmark"])
        # Public candidates: tagged Done card + public-candidate resource.
        public_titles = sorted(c["title"] for c in payload["public_candidates"])
        self.assertEqual(public_titles, ["Public notes", "Public task"])
        # Method candidates cover Done cards with outcome/details.
        method_ids = sorted(c["task_id"] for c in payload["method_candidates"])
        self.assertEqual(method_ids, ["done-cryst", "done-fresh", "done-public"])
        self.assertEqual(
            payload["summary"],
            {
                "done_tasks": 3,
                "evidence_candidates": 2,
                "next_action_candidates": 1,
                "public_draft_candidates": 2,
            },
        )

    def test_default_window_is_current_week(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = self._get(client)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertLessEqual(payload["week_start"], payload["week_end"])

    def test_reversed_window_is_swapped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = self._get(
                client, start=WINDOW_END, end=WINDOW_START
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["week_start"], WINDOW_START)
        self.assertEqual(payload["week_end"], WINDOW_END)

    def test_invalid_window_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            garbage = self._get(client, start="not-a-date", end=WINDOW_END)
            one_sided = self._get(client, start=WINDOW_START)
        self.assertEqual(garbage.status_code, 422)
        self.assertEqual(garbage.json()["code"], "invalid_review_window")
        self.assertEqual(one_sided.status_code, 422)
        self.assertEqual(one_sided.json()["code"], "invalid_review_window")

    def test_unknown_profile_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.get("/api/v1/profiles/nobody/review")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "profile_not_found")


class TestReviewSave(ReviewTestBase):
    """POST /review/save: persist candidates as pending Activity items."""

    def test_save_persists_pending_activity_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/review/save",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "next_action",
                    "candidates": [
                        {
                            "source": "learning",
                            "resource_id": "res-1",
                            "title": "Reproduce the benchmark",
                        }
                    ],
                },
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["saved"], 1)
            self.assertEqual(len(payload["item_ids"]), 1)
            items = _activity_items(profile)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["status"], "pending")
        self.assertEqual(items[0]["candidate_type"], "next_action")
        self.assertEqual(
            items[0]["source_ref"], f"review:{WINDOW_START}:{WINDOW_END}"
        )

    def test_save_unknown_candidate_type_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/review/save",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "method_note",
                    "candidates": [{"title": "x"}],
                },
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_review_candidate_type")

    def test_save_empty_candidates_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/review/save",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "evidence",
                    "candidates": [],
                },
            )
        # Empty list fails request validation (min_length=1).
        self.assertEqual(response.status_code, 422)

    def test_save_stale_if_match_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            etag = client.get(
                "/api/v1/profiles/alice/review",
                params={"start": WINDOW_START, "end": WINDOW_END},
            ).headers["ETag"]
            # A concurrent edit to a review source file invalidates the ETag.
            with open(profile / "kanban.md", "a", encoding="utf-8") as fh:
                fh.write("\n<!-- concurrent edit -->\n")
            response = client.post(
                "/api/v1/profiles/alice/review/save",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "evidence",
                    "candidates": [{"title": "x", "task_id": "done-fresh"}],
                },
                headers={"If-Match": etag},
            )
        self.assertEqual(response.status_code, 412)
        self.assertEqual(response.json()["code"], "etag_mismatch")
        # The 412 carries a fresh ETag so the client can reload and retry.
        self.assertNotEqual(response.headers["ETag"], etag)


class TestReviewApply(ReviewTestBase):
    """POST /review/apply: per-candidate writeback to owner files."""

    def test_apply_evidence_writes_pool_and_marks_crystallized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/review/apply",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "evidence",
                    "mark_crystallized": True,
                    "candidates": [
                        {
                            "source": "kanban_done",
                            "task_id": "done-fresh",
                            "title": "Fresh task",
                            "summary": "shipped the thing",
                        }
                    ],
                },
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["applied"], 1)
            self.assertEqual(payload["failed"], 0)
            self.assertTrue(payload["results"][0]["ok"])
            entries = _pool_entries(profile)
            kanban_text = _kanban_text(profile)
        self.assertTrue(
            any(row.get("title") == "Fresh task" for row in entries)
        )
        self.assertIn("crystallized: true", kanban_text)

    def test_apply_next_action_appends_queue_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/review/apply",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "next_action",
                    "candidates": [
                        {
                            "source": "learning",
                            "resource_id": "res-1",
                            "title": "Reproduce the benchmark",
                        }
                    ],
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["ok"])
            kanban_text = _kanban_text(profile)
        self.assertIn("Reproduce the benchmark", kanban_text)

    def test_apply_public_draft_creates_blog_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/review/apply",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "public_draft",
                    "candidates": [
                        {
                            "source": "kanban_done",
                            "task_id": "done-public",
                            "title": "Public task",
                        }
                    ],
                },
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["ok"], payload["results"])
            output_path = Path(payload["results"][0]["output_path"])
            content = output_path.read_text(encoding="utf-8")
        self.assertTrue(str(output_path).endswith(".md"))
        self.assertIn("status: draft", content)

    def test_apply_reports_per_candidate_failure(self) -> None:
        """A bad candidate fails its own result without failing the request."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            # Force the applier to fail by pointing the profile at a candidate
            # whose public-draft creation target directory is a file.
            with patch(
                "nblane.core.review_actions.create_blog_draft",
                side_effect=OSError("disk full"),
            ):
                response = client.post(
                    "/api/v1/profiles/alice/review/apply",
                    json={
                        "start": WINDOW_START,
                        "end": WINDOW_END,
                        "candidate_type": "public_draft",
                        "candidates": [{"title": "Will fail"}],
                    },
                )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["applied"], 0)
        self.assertEqual(payload["failed"], 1)
        self.assertFalse(payload["results"][0]["ok"])
        self.assertIn("disk full", payload["results"][0]["errors"][0])

    def test_apply_unknown_candidate_type_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/review/apply",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "bogus",
                    "candidates": [{"title": "x"}],
                },
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_review_candidate_type")

    def test_apply_stale_if_match_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            etag = client.get(
                "/api/v1/profiles/alice/review",
                params={"start": WINDOW_START, "end": WINDOW_END},
            ).headers["ETag"]
            first = client.post(
                "/api/v1/profiles/alice/review/apply",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "evidence",
                    "candidates": [
                        {
                            "source": "kanban_done",
                            "task_id": "done-fresh",
                            "title": "Fresh task",
                        }
                    ],
                },
                headers={"If-Match": etag},
            )
            stale = client.post(
                "/api/v1/profiles/alice/review/apply",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "next_action",
                    "candidates": [{"title": "Reproduce the benchmark"}],
                },
                headers={"If-Match": etag},
            )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(stale.status_code, 412)
        self.assertEqual(stale.json()["code"], "etag_mismatch")
        self.assertEqual(stale.headers["ETag"], first.headers["ETag"])


class TestReviewScope(ReviewTestBase):
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
            _template_profile(root)
            client = self._auth_client(root)
            listing = client.get("/api/v1/profiles/alice/review")
            save = client.post(
                "/api/v1/profiles/alice/review/save",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "evidence",
                    "candidates": [{"title": "x"}],
                },
            )
            apply = client.post(
                "/api/v1/profiles/alice/review/apply",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "evidence",
                    "candidates": [{"title": "x"}],
                },
            )
        self.assertEqual(listing.status_code, 401)
        self.assertEqual(save.status_code, 401)
        self.assertEqual(apply.status_code, 401)

    def test_member_forbidden_from_other_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, "alice")
            _template_profile(root, "wang")
            client = self._auth_client(root)
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            self.assertEqual(login.status_code, 200)
            forbidden = client.get("/api/v1/profiles/alice/review")
            forbidden_apply = client.post(
                "/api/v1/profiles/alice/review/apply",
                json={
                    "start": WINDOW_START,
                    "end": WINDOW_END,
                    "candidate_type": "evidence",
                    "candidates": [{"title": "x"}],
                },
            )
            allowed = client.get("/api/v1/profiles/wang/review")
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.json()["code"], "profile_forbidden")
        self.assertEqual(forbidden_apply.status_code, 403)
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["profile"], "wang")


if __name__ == "__main__":
    unittest.main()
