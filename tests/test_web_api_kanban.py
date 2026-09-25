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
from urllib.parse import quote

import yaml
from fastapi.testclient import TestClient

from nblane.core import auth as auth_core
from nblane.core import chronicle as chronicle_core
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

    def test_move_by_id_with_slash_in_title(self) -> None:
        """Id addressing also fixes move for titles containing '/'."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            card = _add_card(client, "学习 ROS2/运动控制")

            moved = client.post(
                f"/api/v1/profiles/alice/kanban/cards/{card['id']}/move",
                json={"target_section": "Doing"},
            )
            sections = parse_kanban(profile)

        self.assertEqual(moved.status_code, 200)
        body = moved.json()
        self.assertEqual(body["section"], "Doing")
        self.assertEqual(body["card"]["id"], card["id"])
        self.assertEqual(body["card"]["title"], "学习 ROS2/运动控制")
        self.assertEqual(
            [task.title for task in sections["Doing"]], ["学习 ROS2/运动控制"]
        )

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

    def test_move_within_column_to_index(self) -> None:
        """In-column reorder: post-removal insertion index lands the card."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            _add_card(client, "卡片 A")
            _add_card(client, "卡片 B")
            _add_card(client, "卡片 C")

            moved = client.post(
                "/api/v1/profiles/alice/kanban/cards/卡片 A/move",
                json={"target_section": "Queue", "to_index": 2},
            )
            sections = parse_kanban(profile)

        self.assertEqual(moved.status_code, 200)
        body = moved.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["section"], "Queue")
        self.assertEqual(body["warnings"], [])
        self.assertEqual(
            [task.title for task in sections["Queue"]],
            ["卡片 B", "卡片 C", "卡片 A"],
        )

    def test_move_same_section_without_index_warns_noop(self) -> None:
        """Same-column move without to_index keeps the idempotent warning."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            _add_card(client, "卡片 A")
            _add_card(client, "卡片 B")

            moved = client.post(
                "/api/v1/profiles/alice/kanban/cards/卡片 A/move",
                json={"target_section": "Queue"},
            )
            sections = parse_kanban(profile)

        self.assertEqual(moved.status_code, 200)
        self.assertTrue(moved.json()["warnings"])
        self.assertEqual(
            [task.title for task in sections["Queue"]],
            ["卡片 A", "卡片 B"],
        )

    def test_move_cross_column_with_to_index(self) -> None:
        """Cross-column move inserts at the requested position, not the tail."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            _add_card(client, "进行中 1", section="Doing")
            _add_card(client, "进行中 2", section="Doing")
            _add_card(client, "排队卡")

            moved = client.post(
                "/api/v1/profiles/alice/kanban/cards/排队卡/move",
                json={"target_section": "Doing", "to_index": 1},
            )
            sections = parse_kanban(profile)

        self.assertEqual(moved.status_code, 200)
        self.assertEqual(moved.json()["section"], "Doing")
        self.assertEqual(
            [task.title for task in sections["Doing"]],
            ["进行中 1", "排队卡", "进行中 2"],
        )

    def test_move_default_appends_to_tail(self) -> None:
        """Omitting to_index keeps the legacy append-to-tail behavior."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            _add_card(client, "进行中 1", section="Doing")
            _add_card(client, "进行中 2", section="Doing")
            _add_card(client, "排队卡")

            moved = client.post(
                "/api/v1/profiles/alice/kanban/cards/排队卡/move",
                json={"target_section": "Doing"},
            )
            sections = parse_kanban(profile)

        self.assertEqual(moved.status_code, 200)
        self.assertEqual(
            [task.title for task in sections["Doing"]],
            ["进行中 1", "进行中 2", "排队卡"],
        )

    def test_move_to_index_out_of_range_clamps(self) -> None:
        """Core reorder semantics: negative clamps to head, overflow to tail."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            _add_card(client, "卡片 A")
            _add_card(client, "卡片 B")
            _add_card(client, "卡片 C")

            to_head = client.post(
                "/api/v1/profiles/alice/kanban/cards/卡片 C/move",
                json={"target_section": "Queue", "to_index": -3},
            )
            head_titles = _section_titles(profile, "Queue")
            to_tail = client.post(
                "/api/v1/profiles/alice/kanban/cards/卡片 C/move",
                json={"target_section": "Queue", "to_index": 999},
            )
            tail_titles = _section_titles(profile, "Queue")

        self.assertEqual(to_head.status_code, 200)
        self.assertEqual(to_tail.status_code, 200)
        self.assertEqual(head_titles, ["卡片 C", "卡片 A", "卡片 B"])
        self.assertEqual(tail_titles, ["卡片 A", "卡片 B", "卡片 C"])


class TestKanbanCardDelete(unittest.TestCase):
    """DELETE /kanban/cards/{card_ref}: permanent card removal."""

    def _client(self, root: Path) -> TestClient:
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
        patcher = patch("nblane.core.chronicle.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)

    def _delete(
        self, client: TestClient, ref: str, body: dict | None = None, **kwargs: object
    ):
        return client.request(
            "DELETE",
            f"/api/v1/profiles/alice/kanban/cards/{ref}",
            json={"record_chronicle": False, **(body or {})},
            **kwargs,
        )

    def test_delete_happy_path_removes_card_and_its_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            card = _add_card(client, "删掉我", context="临时任务")
            _add_card(client, "保留我")
            # Todos/subtasks/meta live inside the card block and die with it.
            patched = client.patch(
                "/api/v1/profiles/alice/kanban/cards/删掉我",
                json={"todos": [{"text": "子任务甲", "done": False}]},
            )
            self.assertEqual(patched.status_code, 200)

            deleted = self._delete(client, "删掉我")
            board = client.get("/api/v1/profiles/alice/kanban")
            kanban_text = (profile / "kanban.md").read_text(encoding="utf-8")
            sections = parse_kanban(profile)

        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.headers["etag"].startswith('W/"'))
        payload = deleted.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["deleted_ref"], card["id"])
        self.assertEqual(payload["deleted_title"], "删掉我")
        self.assertNotIn("删掉我", kanban_text)
        self.assertNotIn("子任务甲", kanban_text)
        self.assertIn("保留我", kanban_text)
        self.assertEqual(
            [task.title for task in sections["Queue"]], ["保留我"]
        )
        # Board refetch is clean: the card is gone from the JSON too.
        self.assertEqual(board.status_code, 200)
        titles = [
            task["title"]
            for section in board.json()["sections"]
            for task in section["tasks"]
        ]
        self.assertEqual(titles, ["保留我"])
        # record_chronicle defaults off: no chronicle file is created.
        self.assertFalse((profile / "chronicle.yaml").exists())

    def test_delete_by_unique_substring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            _add_card(client, "读 VLA 综述论文")
            deleted = self._delete(client, "VLA 综述")
            titles = _section_titles(profile, "Queue")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json()["deleted_title"], "读 VLA 综述论文")
        self.assertEqual(titles, [])

    def test_delete_by_id_with_slash_in_title(self) -> None:
        """A title containing '/' splits the route and 405s; the id works."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            card = _add_card(client, "学习 ROS2/运动控制")
            _add_card(client, "保留我")

            by_title = self._delete(
                client, quote("学习 ROS2/运动控制", safe="")
            )
            by_id = self._delete(client, card["id"])
            sections = parse_kanban(profile)

        self.assertEqual(by_title.status_code, 405)
        self.assertEqual(by_id.status_code, 200)
        self.assertEqual(by_id.json()["deleted_ref"], card["id"])
        self.assertEqual(by_id.json()["deleted_title"], "学习 ROS2/运动控制")
        self.assertEqual(
            [task.title for task in sections["Queue"]], ["保留我"]
        )

    def test_delete_by_id_plain_title_no_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            card = _add_card(client, "普通标题")
            deleted = self._delete(client, card["id"])
            titles = _section_titles(profile, "Queue")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json()["deleted_title"], "普通标题")
        self.assertEqual(titles, [])

    def test_delete_id_wins_over_title_fallback(self) -> None:
        """A ref equal to a card id resolves that card, not a title match."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            first = _add_card(client, "第一张")
            # Title-shadowing edge: a second card titled like the first id
            # still loses to the id match.
            _add_card(client, first["id"])
            deleted = self._delete(client, first["id"])
            titles = _section_titles(profile, "Queue")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json()["deleted_title"], "第一张")
        self.assertEqual(titles, [first["id"]])

    def test_delete_ambiguous_ref_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            _add_card(client, "Review paper A")
            _add_card(client, "Review paper B")
            before = (profile / "kanban.md").read_text(encoding="utf-8")
            response = self._delete(client, "Review paper")
            after = (profile / "kanban.md").read_text(encoding="utf-8")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "kanban_card_ambiguous")
        self.assertEqual(after, before)

    def test_delete_unknown_card_404(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            response = self._delete(client, "不存在的卡片")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "kanban_card_not_found")

    def test_delete_stale_if_match_412_then_fresh_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            _add_card(client, "卡片 A")
            board = client.get("/api/v1/profiles/alice/kanban")
            stale_etag = board.headers["etag"]
            _add_card(client, "卡片 B")  # rotates the ETag

            conflicted = self._delete(
                client, "卡片 A", headers={"If-Match": stale_etag}
            )
            matching = self._delete(
                client, "卡片 A", headers={"If-Match": conflicted.headers["etag"]}
            )

        self.assertEqual(conflicted.status_code, 412)
        self.assertEqual(conflicted.json()["code"], "etag_mismatch")
        self.assertNotEqual(conflicted.headers["etag"], stale_etag)
        self.assertEqual(matching.status_code, 200)
        self.assertEqual(matching.json()["deleted_title"], "卡片 A")

    def test_delete_without_body_proceeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            _add_card(client, "裸删")
            response = client.request(
                "DELETE", "/api/v1/profiles/alice/kanban/cards/裸删"
            )
            titles = _section_titles(profile, "Queue")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(titles, [])

    def test_delete_record_chronicle_appends_task_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            card = _add_card(client, "里程碑式删除")
            deleted = self._delete(client, "里程碑式删除", {"record_chronicle": True})
            entries = chronicle_core.load_chronicle(profile)
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].kind, "task.deleted")
        self.assertEqual(entries[0].ref, card["id"])
        self.assertEqual(entries[0].note, "里程碑式删除")

    def test_delete_leaves_evidence_kanban_refs_untouched(self) -> None:
        """Evidence kanban_refs keep pointing at the deleted task (tombstone)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            card = _add_card(client, "被证据引用的任务")
            pool_text = yaml.safe_dump(
                {
                    "profile": "alice",
                    "updated": "2026-09-19",
                    "evidence_entries": [
                        {
                            "id": "ev-1",
                            "title": "Demo 视频",
                            "type": "practice",
                            "review_status": "reviewed",
                            "kanban_refs": [f"kanban:{card['id']}"],
                        }
                    ],
                },
                allow_unicode=True,
            )
            (profile / "evidence-pool.yaml").write_text(pool_text, encoding="utf-8")

            deleted = self._delete(client, "被证据引用的任务")
            after = (profile / "evidence-pool.yaml").read_text(encoding="utf-8")

        self.assertEqual(deleted.status_code, 200)
        # The pool file is byte-identical: tombstone display handles the
        # dangling ref, the delete never rewrites evidence.
        self.assertEqual(after, pool_text)
        self.assertIn(f"kanban:{card['id']}", after)


class TestKanbanBoardArchive(unittest.TestCase):
    """GET /kanban archive field (kanban-archive.md projection)."""

    def _client(self, root: Path) -> TestClient:
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

    def test_get_kanban_includes_archive_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            _add_card(client, "看板任务")
            (profile / "kanban-archive.md").write_text(
                "# alice · Kanban archive\n\n"
                "> Tasks moved here from kanban.md (Done column).\n\n"
                "---\n"
                "\n## Archived · 2026-04-15\n\n"
                "- [x] 归档任务\n"
                "  - id: kb_arc111\n"
                "  - project_id: project:demo\n",
                encoding="utf-8",
            )

            board = client.get("/api/v1/profiles/alice/kanban")

        self.assertEqual(board.status_code, 200)
        payload = board.json()
        archive = payload["archive"]
        self.assertEqual(len(archive), 1)
        self.assertEqual(archive[0]["title"], "归档任务")
        self.assertEqual(archive[0]["id"], "kb_arc111")
        self.assertTrue(archive[0]["done"])
        # No completed_on in the file: falls back to the group date.
        self.assertEqual(archive[0]["completed_on"], "2026-04-15")
        self.assertEqual(archive[0]["project_id"], "project:demo")
        # Archive tasks are not counted in the board total.
        self.assertEqual(payload["total"], 1)

    def test_get_kanban_without_archive_file_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            board = client.get("/api/v1/profiles/alice/kanban")

        self.assertEqual(board.status_code, 200)
        self.assertEqual(board.json()["archive"], [])

    def test_archive_file_does_not_change_etag(self) -> None:
        """The ETag fingerprints kanban.md only; archive edits keep it."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            before = client.get("/api/v1/profiles/alice/kanban")
            (profile / "kanban-archive.md").write_text(
                "## Archived · 2026-04-15\n\n- [x] 归档任务\n",
                encoding="utf-8",
            )
            after = client.get("/api/v1/profiles/alice/kanban")

        self.assertEqual(before.headers["ETag"], after.headers["ETag"])
        self.assertEqual(len(after.json()["archive"]), 1)


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
            deleted = client.request(
                "DELETE",
                "/api/v1/profiles/alice/kanban/cards/x",
                json={"record_chronicle": False},
            )
        for response in (added, moved, done, deleted):
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
            deleted = client.request(
                "DELETE",
                "/api/v1/profiles/alice/kanban/cards/x",
                json={"record_chronicle": False},
            )
        self.assertEqual(login.status_code, 200)
        for response in (added, moved, done, deleted):
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["code"], "profile_forbidden")


if __name__ == "__main__":
    unittest.main()
