"""Tests for the Inbox mutation endpoints (capture/clarify/archive/discard).

Covers the quick-capture loop (POST 201 lands in inbox.yaml), the clarify
dispatch (to_kanban_queue actually moves the item onto kanban.md), error
mapping (unknown action 422, unknown item 404), If-Match/412 conflict
protection, and the 401/403 auth rules.
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
from nblane.core import inbox as inbox_core
from nblane.core.paths import REPO_ROOT
from nblane.web_api import app, create_app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"
PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-inbox-test-secret"


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


def _capture(client: TestClient, title: str, **extra: object) -> dict:
    response = client.post(
        "/api/v1/profiles/alice/inbox", json={"title": title, **extra}
    )
    assert response.status_code == 201, response.text
    return dict(response.json()["item"])


class TestInboxMutations(unittest.TestCase):
    """Capture/clarify/archive/discard against a tmp template profile."""

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
        for target in (
            "nblane.core.inbox.git_backup.record_change",
            "nblane.core.kanban_io.git_backup.record_change",
        ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        return TestClient(app)

    def test_capture_201_and_lands_in_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)

            created = client.post(
                "/api/v1/profiles/alice/inbox",
                json={
                    "title": "微信: 看看 VLA 综述",
                    "raw_text": "群里转的文章链接",
                    "tags": ["vla", "reading"],
                },
            )
            stored = inbox_core.load_inbox(profile)

        self.assertEqual(created.status_code, 201)
        body = created.json()
        self.assertTrue(body["ok"])
        item = body["item"]
        self.assertEqual(item["title"], "微信: 看看 VLA 综述")
        self.assertEqual(item["raw_text"], "群里转的文章链接")
        # Default source web → captured_by human-web (distinct from the
        # MCP/openclaw capture path).
        self.assertEqual(item["source"], "web")
        self.assertEqual(item["captured_by"], "human-web")
        self.assertEqual(item["tags"], ["vla", "reading"])
        self.assertEqual(item["status"], "inbox")
        self.assertTrue(created.headers["etag"].startswith('W/"'))

        self.assertEqual(len(stored.items), 1)
        self.assertEqual(stored.items[0].id, item["id"])
        self.assertEqual(stored.items[0].captured_by, "human-web")
        self.assertEqual(stored.items[0].history[0].action, "added")

    def test_capture_custom_source_marks_captured_by(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            created = client.post(
                "/api/v1/profiles/alice/inbox",
                json={"title": "Note from wechat", "source": "wechat"},
            )
        self.assertEqual(created.status_code, 201)
        item = created.json()["item"]
        self.assertEqual(item["source"], "wechat")
        self.assertEqual(item["captured_by"], "human-wechat")

    def test_capture_blank_title_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            created = client.post(
                "/api/v1/profiles/alice/inbox", json={"title": "   "}
            )
        self.assertEqual(created.status_code, 422)
        self.assertEqual(created.json()["code"], "invalid_inbox_capture")

    def test_clarify_to_kanban_queue_moves_to_kanban(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            item_id = _capture(client, "整理 VLA 访谈笔记")["id"]

            clarified = client.post(
                f"/api/v1/profiles/alice/inbox/{item_id}/clarify",
                json={"action": "to_kanban_queue", "note": "本周做"},
            )
            stored = inbox_core.load_inbox(profile)
            kanban_body = (profile / "kanban.md").read_text(encoding="utf-8")

        self.assertEqual(clarified.status_code, 200)
        body = clarified.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["item"]["id"], item_id)
        self.assertEqual(body["item"]["status"], "clarified")
        result = body["result"]
        self.assertEqual(result["action"], "to_kanban_queue")
        self.assertTrue(str(result["target_id"]).startswith("kb_"))
        self.assertIn("etag", clarified.headers)

        # The dispatch actually wrote the kanban Queue card.
        self.assertIn("整理 VLA 访谈笔记", kanban_body)
        item = next(i for i in stored.items if i.id == item_id)
        self.assertEqual(item.status, "clarified")
        self.assertEqual(item.metadata["clarify_action"], "to_kanban_queue")
        self.assertEqual(item.metadata["target_id"], result["target_id"])

    def test_clarify_unknown_action_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            item_id = _capture(client, "Keep me")["id"]
            response = client.post(
                f"/api/v1/profiles/alice/inbox/{item_id}/clarify",
                json={"action": "to_the_moon"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "unsupported_clarify_action")

    def test_unknown_item_404_on_all_item_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            clarified = client.post(
                "/api/v1/profiles/alice/inbox/item-nope/clarify",
                json={"action": "archive"},
            )
            archived = client.post(
                "/api/v1/profiles/alice/inbox/item-nope/archive"
            )
            discarded = client.post(
                "/api/v1/profiles/alice/inbox/item-nope/discard"
            )
        for response in (clarified, archived, discarded):
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["code"], "inbox_item_not_found")

    def test_archive_and_discard_wrappers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            keep_id = _capture(client, "Archive me")["id"]
            drop_id = _capture(client, "Discard me")["id"]

            archived = client.post(
                f"/api/v1/profiles/alice/inbox/{keep_id}/archive",
                json={"note": "已处理完"},
            )
            discarded = client.post(
                f"/api/v1/profiles/alice/inbox/{drop_id}/discard"
            )
            stored = inbox_core.load_inbox(profile)

        self.assertEqual(archived.status_code, 200)
        self.assertEqual(archived.json()["item"]["status"], "archived")
        self.assertEqual(discarded.status_code, 200)
        self.assertEqual(discarded.json()["item"]["status"], "discarded")
        by_id = {item.id: item for item in stored.items}
        self.assertEqual(by_id[keep_id].status, "archived")
        self.assertEqual(by_id[drop_id].status, "discarded")
        self.assertEqual(
            by_id[keep_id].history[-1].note, "已处理完"
        )

    def test_list_carries_etag_and_stale_if_match_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            keep_id = _capture(client, "Keep open")["id"]
            other_id = _capture(client, "Discard to bump etag")["id"]

            listing = client.get("/api/v1/profiles/alice/inbox")
            stale_etag = listing.headers["etag"]
            # Any other mutation rewrites inbox.yaml → new sha256.
            discarded = client.post(
                f"/api/v1/profiles/alice/inbox/{other_id}/discard"
            )
            conflicted = client.post(
                f"/api/v1/profiles/alice/inbox/{keep_id}/archive",
                headers={"If-Match": stale_etag},
            )
            matching = client.post(
                f"/api/v1/profiles/alice/inbox/{keep_id}/archive",
                headers={"If-Match": conflicted.headers["etag"]},
            )

        self.assertEqual(listing.status_code, 200)
        self.assertTrue(stale_etag.startswith('W/"'))
        self.assertEqual(discarded.status_code, 200)
        self.assertEqual(conflicted.status_code, 412)
        body = conflicted.json()
        self.assertEqual(body["code"], "etag_mismatch")
        self.assertEqual(body["item"]["id"], keep_id)
        self.assertEqual(body["item"]["status"], "inbox")
        # The 412 also carries the fresh ETag so the client can retry.
        self.assertNotEqual(conflicted.headers["etag"], stale_etag)
        self.assertEqual(matching.status_code, 200)
        self.assertEqual(matching.json()["item"]["status"], "archived")

    def test_capture_without_if_match_proceeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            _capture(client, "First")
            created = client.post(
                "/api/v1/profiles/alice/inbox", json={"title": "Second"}
            )
        self.assertEqual(created.status_code, 201)


class TestInboxMutationAuth(unittest.TestCase):
    """401/403 rules for the inbox mutations under auth-on."""

    def _auth_client(self, root: Path) -> TestClient:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch("nblane.core.inbox.git_backup.record_change")
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
            captured = client.post(
                "/api/v1/profiles/alice/inbox", json={"title": "x"}
            )
            clarified = client.post(
                "/api/v1/profiles/alice/inbox/item-1/clarify",
                json={"action": "archive"},
            )
            archived = client.post("/api/v1/profiles/alice/inbox/item-1/archive")
            discarded = client.post("/api/v1/profiles/alice/inbox/item-1/discard")
        for response in (captured, clarified, archived, discarded):
            self.assertEqual(response.status_code, 401)

    def test_member_forbidden_from_other_profile_403(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root, "alice")
            _template_profile(root, "wang")
            client = self._auth_client(root)
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "wang", "password": PASSWORD},
            )
            captured = client.post(
                "/api/v1/profiles/alice/inbox", json={"title": "x"}
            )
            clarified = client.post(
                "/api/v1/profiles/alice/inbox/item-1/clarify",
                json={"action": "archive"},
            )
            archived = client.post("/api/v1/profiles/alice/inbox/item-1/archive")
            discarded = client.post("/api/v1/profiles/alice/inbox/item-1/discard")
        self.assertEqual(login.status_code, 200)
        for response in (captured, clarified, archived, discarded):
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["code"], "profile_forbidden")


if __name__ == "__main__":
    unittest.main()
