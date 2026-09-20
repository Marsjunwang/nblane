"""Tests for the Kanban card mutation endpoints (add/move/done).

Covers the quick-add loop (POST 201 lands in kanban.md, verified via
``parse_kanban``), card moves by exact title or unique substring
(ambiguous → 422, unknown section → 422, missing → 404), the mark-done
transition, If-Match/412 stale-client protection, the 3-way merge notice
path when kanban.md changes mid-request, and the 401/403 auth rules.
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
from nblane.core.kanban_io import parse_kanban, save_kanban
from nblane.core.models import KanbanTask
from nblane.core.paths import REPO_ROOT
from nblane.web_api import app, create_app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"
PASSWORD = "correct horse battery staple"
TEST_SESSION_SECRET = "web-api-kanban-test-secret"


def _template_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            text = text.replace("{YYYY-MM-DD}", "2026-09-19")
            file_path.write_text(text, encoding="utf-8")
    # The template's placeholder cards parse as real tasks; start each test
    # from a clean empty board instead.
    sections = ("Doing", "Done", "Queue", "Someday / Maybe")
    (profile / "kanban.md").write_text(
        f"# {name} · Kanban\n\n> Updated: 2026-09-19\n\n---\n"
        + "".join(f"\n## {section}\n\n- (empty)\n\n---\n" for section in sections),
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


def _add_card(client: TestClient, title: str, **extra: object) -> dict:
    response = client.post(
        "/api/v1/profiles/alice/kanban/cards", json={"title": title, **extra}
    )
    assert response.status_code == 201, response.text
    return dict(response.json()["card"])


def _section_titles(profile: Path, section: str) -> list[str]:
    return [task.title for task in parse_kanban(profile).get(section, [])]


class TestKanbanMutations(unittest.TestCase):
    """Add/move/done against a tmp template profile."""

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
        patcher = patch("nblane.core.kanban_io.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)

    def test_add_201_and_lands_in_kanban_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)

            created = client.post(
                "/api/v1/profiles/alice/kanban/cards",
                json={
                    "title": "读 VLA 综述",
                    "section": "Queue",
                    "context": "周末前读完",
                    "tags": ["vla", "reading"],
                },
            )
            sections = parse_kanban(profile)

        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.headers["etag"].startswith('W/"'))
        body = created.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["section"], "Queue")
        card = body["card"]
        self.assertEqual(card["title"], "读 VLA 综述")
        self.assertEqual(card["context"], "周末前读完")
        self.assertEqual(card["tags"], "vla, reading")
        self.assertTrue(card["id"])
        stored = sections["Queue"]
        self.assertEqual([task.title for task in stored], ["读 VLA 综述"])
        self.assertEqual(stored[0].context, "周末前读完")
        self.assertEqual(stored[0].id, card["id"])

    def test_add_defaults_to_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            card = _add_card(client, "默认进 Queue")
            titles = _section_titles(profile, "Queue")
        self.assertEqual(card["title"], "默认进 Queue")
        self.assertFalse(card["done"])
        self.assertEqual(titles, ["默认进 Queue"])

    def test_add_blank_title_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/kanban/cards", json={"title": "   "}
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_kanban_card")

    def test_add_schema_validation_errors_use_error_response_shape(self) -> None:
        """Pydantic request failures share the ErrorResponse{code,message} body."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            cases = [
                {},  # missing title
                {"title": ""},  # min_length=1
                {"title": "x" * 201},  # max_length=200
            ]
            responses = [
                client.post("/api/v1/profiles/alice/kanban/cards", json=body)
                for body in cases
            ]
        for response in responses:
            self.assertEqual(response.status_code, 422)
            payload = response.json()
            self.assertEqual(sorted(payload.keys()), ["code", "message"])
            self.assertEqual(payload["code"], "validation_error")
            self.assertIn("title", payload["message"])

    def test_add_unknown_section_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/kanban/cards",
                json={"title": "x", "section": "Backlog"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "unknown_kanban_section")

    def test_move_success_by_exact_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            _add_card(client, "搭 CI 流水线")
            _add_card(client, "写文档")

            moved = client.post(
                "/api/v1/profiles/alice/kanban/cards/搭 CI 流水线/move",
                json={"target_section": "Doing"},
            )
            sections = parse_kanban(profile)

        self.assertEqual(moved.status_code, 200)
        body = moved.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["section"], "Doing")
        self.assertEqual(body["card"]["title"], "搭 CI 流水线")
        self.assertTrue(body["card"]["started_on"])
        self.assertEqual(
            [task.title for task in sections["Doing"]], ["搭 CI 流水线"]
        )
        self.assertEqual(
            [task.title for task in sections["Queue"]], ["写文档"]
        )

    def test_move_success_by_unique_substring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            _add_card(client, "读 VLA 综述论文")
            moved = client.post(
                "/api/v1/profiles/alice/kanban/cards/VLA 综述/move",
                json={"target_section": "Doing"},
            )
        self.assertEqual(moved.status_code, 200)
        self.assertEqual(moved.json()["card"]["title"], "读 VLA 综述论文")

    def test_move_ambiguous_ref_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            _add_card(client, "Review paper A")
            _add_card(client, "Review paper B")
            response = client.post(
                "/api/v1/profiles/alice/kanban/cards/Review paper/move",
                json={"target_section": "Doing"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "kanban_card_ambiguous")

    def test_move_unknown_card_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = client.post(
                "/api/v1/profiles/alice/kanban/cards/不存在的卡片/move",
                json={"target_section": "Doing"},
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "kanban_card_not_found")

    def test_move_unknown_section_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            _add_card(client, "卡片")
            response = client.post(
                "/api/v1/profiles/alice/kanban/cards/卡片/move",
                json={"target_section": "Backlog"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "unknown_kanban_section")

    def test_done_flow_marks_card_and_moves_to_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            _add_card(client, "完成我")

            done = client.post("/api/v1/profiles/alice/kanban/cards/完成我/done")
            again = client.post("/api/v1/profiles/alice/kanban/cards/完成我/done")
            sections = parse_kanban(profile)

        self.assertEqual(done.status_code, 200)
        body = done.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["section"], "Done")
        self.assertTrue(body["card"]["done"])
        self.assertTrue(body["card"]["completed_on"])
        done_tasks = sections["Done"]
        self.assertEqual([task.title for task in done_tasks], ["完成我"])
        self.assertTrue(done_tasks[0].done)
        self.assertTrue(done_tasks[0].completed_on)
        self.assertEqual(sections["Queue"], [])
        # Already in Done: idempotent 200 with an "already there" warning.
        self.assertEqual(again.status_code, 200)
        self.assertTrue(again.json()["warnings"])

    def test_stale_if_match_412_then_fresh_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            _add_card(client, "卡片 A")
            board = client.get("/api/v1/profiles/alice/kanban")
            stale_etag = board.headers["etag"]
            # Another writer changes kanban.md, rotating the ETag.
            _add_card(client, "卡片 B")

            conflicted = client.post(
                "/api/v1/profiles/alice/kanban/cards/卡片 A/move",
                json={"target_section": "Doing"},
                headers={"If-Match": stale_etag},
            )
            matching = client.post(
                "/api/v1/profiles/alice/kanban/cards/卡片 A/move",
                json={"target_section": "Doing"},
                headers={"If-Match": conflicted.headers["etag"]},
            )

        self.assertEqual(board.status_code, 200)
        self.assertEqual(conflicted.status_code, 412)
        self.assertEqual(conflicted.json()["code"], "etag_mismatch")
        # The 412 also carries the fresh ETag so the client can retry.
        self.assertNotEqual(conflicted.headers["etag"], stale_etag)
        self.assertEqual(matching.status_code, 200)
        self.assertEqual(matching.json()["section"], "Doing")

    def test_concurrent_write_merges_with_notice(self) -> None:
        """A write landing between parse and save is merged, not 412."""
        import nblane.web_api.routes_v1 as routes_v1

        real_parse = routes_v1.parse_kanban

        def parse_then_external_write(profile):
            sections = real_parse(profile)
            # Simulate an external writer changing kanban.md after the
            # request snapshot but before the merge-aware save.
            external = real_parse(profile)
            external.setdefault("Queue", []).append(
                KanbanTask(title="外部并发卡片")
            )
            save_kanban(profile, external)
            return sections

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            board = client.get("/api/v1/profiles/alice/kanban")
            etag = board.headers["etag"]
            patcher = patch.object(
                routes_v1, "parse_kanban", parse_then_external_write
            )
            self.addCleanup(patcher.stop)
            patcher.start()
            created = client.post(
                "/api/v1/profiles/alice/kanban/cards",
                json={"title": "我的新卡片"},
                headers={"If-Match": etag},
            )
            queue_titles = _section_titles(profile, "Queue")

        self.assertEqual(created.status_code, 201)
        body = created.json()
        self.assertTrue(body["merged_external"])
        self.assertTrue(body["merge_notices"])
        # Both the external card and the new card survive the merge.
        self.assertEqual(
            sorted(queue_titles),
            ["外部并发卡片", "我的新卡片"],
        )

    def test_move_without_if_match_proceeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            _add_card(client, "卡片")
            moved = client.post(
                "/api/v1/profiles/alice/kanban/cards/卡片/move",
                json={"target_section": "Doing"},
            )
        self.assertEqual(moved.status_code, 200)


class TestKanbanMutationAuth(unittest.TestCase):
    """401/403 rules for the kanban mutations under auth-on."""

    def _auth_client(self, root: Path) -> TestClient:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch("nblane.core.kanban_io.git_backup.record_change")
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
            added = client.post(
                "/api/v1/profiles/alice/kanban/cards", json={"title": "x"}
            )
            moved = client.post(
                "/api/v1/profiles/alice/kanban/cards/x/move",
                json={"target_section": "Doing"},
            )
            done = client.post("/api/v1/profiles/alice/kanban/cards/x/done")
        for response in (added, moved, done):
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
            added = client.post(
                "/api/v1/profiles/alice/kanban/cards", json={"title": "x"}
            )
            moved = client.post(
                "/api/v1/profiles/alice/kanban/cards/x/move",
                json={"target_section": "Doing"},
            )
            done = client.post("/api/v1/profiles/alice/kanban/cards/x/done")
        self.assertEqual(login.status_code, 200)
        for response in (added, moved, done):
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["code"], "profile_forbidden")


if __name__ == "__main__":
    unittest.main()
