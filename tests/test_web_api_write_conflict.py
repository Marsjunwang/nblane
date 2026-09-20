"""Route-level TOCTOU closure tests for the If-Match/412 contract.

The pre-flight If-Match check happens at request start; the core saver
re-checks the request-start fingerprint *inside* the write lock and raises
``file_state.FileConflictError`` on mismatch, which the route maps to the
same 412 (``etag_mismatch``) with a fresh ETag header. These tests
simulate a concurrent writer landing exactly in that window by wrapping
the target module's ``locked_profile_write``: the wrapper acquires the
real lock, performs an external (lock-bypassing) write, then lets the
saver proceed — deterministically exercising the in-lock re-check.

Kanban is the merge exception: a concurrent write there is 3-way merged
(``save_kanban_with_merge``), so the inbox clarify kanban branch answers
200 with both cards preserved instead of 412.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import agent_activity
from nblane.core import inbox as inbox_core
from nblane.core import profile_io
from nblane.core import project_board as project_board_core
from nblane.core import public_site as public_site_core
from nblane.core.file_write import atomic_write_text
from nblane.core.kanban_io import KANBAN_QUEUE, parse_kanban, render_kanban
from nblane.core.models import KanbanTask
from nblane.core.paths import REPO_ROOT
from nblane.core.review_actions import save_review_candidates_to_activity
from nblane.web_api import app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"

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


@contextmanager
def _wrap_lock(real_lock, on_enter):
    """Yield a locked_profile_write replacement running *on_enter* first.

    *on_enter* runs after the real lock is acquired and before the saver's
    in-lock snapshot re-check, simulating a concurrent write that landed
    between the route's request-start snapshot and the lock acquisition.
    """

    @contextmanager
    def wrapper(profile_dir, filename):
        with real_lock(profile_dir, filename) as lock_path:
            on_enter()
            yield lock_path

    yield wrapper


class TestWebApiWriteConflict(unittest.TestCase):
    """412 when a write lands between If-Match check and lock acquisition."""

    def _client(self, root: Path) -> TestClient:
        # Same patch set as the per-family test modules: every core module
        # that binds PROFILES_DIR directly must resolve into the tmp root.
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
            "nblane.core.project_board.PROFILES_DIR",
            "nblane.core.research_sources.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch("nblane.core.git_backup.record_change")
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)

    def _capture(self, client: TestClient, title: str) -> dict:
        response = client.post(
            "/api/v1/profiles/alice/inbox", json={"title": title}
        )
        assert response.status_code == 201, response.text
        return dict(response.json()["item"])

    # -- inbox ------------------------------------------------------------

    def test_inbox_archive_conflict_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            item = self._capture(client, "归档我")
            etag = client.get("/api/v1/profiles/alice/inbox").headers["etag"]

            def external_write() -> None:
                doc = inbox_core.load_inbox(profile)
                inbox_core.add_inbox_item(doc, "外部并发捕获")
                inbox_core._write_inbox(profile / "inbox.yaml", doc)

            with _wrap_lock(
                inbox_core.locked_profile_write, external_write
            ) as wrapped:
                with patch.object(
                    inbox_core, "locked_profile_write", wrapped
                ):
                    conflicted = client.post(
                        f"/api/v1/profiles/alice/inbox/{item['id']}/archive",
                        headers={"If-Match": etag},
                    )
            titles = [
                entry.title for entry in inbox_core.load_inbox(profile).items
            ]
            status_by_title = {
                entry.title: entry.status
                for entry in inbox_core.load_inbox(profile).items
            }

        self.assertEqual(conflicted.status_code, 412)
        self.assertEqual(conflicted.json()["code"], "etag_mismatch")
        self.assertNotEqual(conflicted.headers["etag"], etag)
        # The external capture survived; the archive did not happen.
        self.assertIn("外部并发捕获", titles)
        self.assertEqual(status_by_title["归档我"], "inbox")

    def test_inbox_archive_without_conflict_proceeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            item = self._capture(client, "归档我")
            etag = client.get("/api/v1/profiles/alice/inbox").headers["etag"]
            archived = client.post(
                f"/api/v1/profiles/alice/inbox/{item['id']}/archive",
                headers={"If-Match": etag},
            )
            stored = inbox_core.load_inbox(profile)
        self.assertEqual(archived.status_code, 200)
        self.assertEqual(stored.items[0].status, "archived")

    def test_inbox_etag_rotates_when_kanban_changes(self) -> None:
        """M-API-4: the inbox ETag covers the clarify target files."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            before = client.get("/api/v1/profiles/alice/inbox").headers["etag"]
            sections = parse_kanban(profile)
            sections[KANBAN_QUEUE].append(KanbanTask(title="看板变更"))
            atomic_write_text(
                profile / "kanban.md",
                render_kanban(profile.name, sections),
            )
            after = client.get("/api/v1/profiles/alice/inbox").headers["etag"]
        self.assertNotEqual(before, after)

    def test_clarify_kanban_conflict_merges_not_412(self) -> None:
        """M-API-4: a kanban write mid-clarify is merged, both cards land."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            item = self._capture(client, "整理成看板卡")
            etag = client.get("/api/v1/profiles/alice/inbox").headers["etag"]

            import nblane.core.kanban_merge as kanban_merge

            def external_kanban_write() -> None:
                sections = parse_kanban(profile)
                sections[KANBAN_QUEUE].append(KanbanTask(title="外部看板卡"))
                atomic_write_text(
                    profile / "kanban.md",
                    render_kanban(profile.name, sections),
                )

            with _wrap_lock(
                kanban_merge.locked_profile_write, external_kanban_write
            ) as wrapped:
                with patch.object(
                    kanban_merge, "locked_profile_write", wrapped
                ):
                    clarified = client.post(
                        f"/api/v1/profiles/alice/inbox/{item['id']}/clarify",
                        json={"action": "to_kanban_queue"},
                        headers={"If-Match": etag},
                    )
            titles = [t.title for t in parse_kanban(profile)[KANBAN_QUEUE]]

        self.assertEqual(clarified.status_code, 200, clarified.text)
        self.assertTrue(clarified.json()["result"]["target_id"])
        self.assertIn("外部看板卡", titles)
        self.assertIn("整理成看板卡", titles)

    def test_clarify_inbox_conflict_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            item = self._capture(client, "澄清我")
            etag = client.get("/api/v1/profiles/alice/inbox").headers["etag"]

            def external_write() -> None:
                doc = inbox_core.load_inbox(profile)
                inbox_core.add_inbox_item(doc, "外部并发捕获")
                inbox_core._write_inbox(profile / "inbox.yaml", doc)

            with _wrap_lock(
                inbox_core.locked_profile_write, external_write
            ) as wrapped:
                with patch.object(
                    inbox_core, "locked_profile_write", wrapped
                ):
                    conflicted = client.post(
                        f"/api/v1/profiles/alice/inbox/{item['id']}/clarify",
                        json={"action": "archive"},
                        headers={"If-Match": etag},
                    )

        self.assertEqual(conflicted.status_code, 412)
        self.assertEqual(conflicted.json()["code"], "etag_mismatch")

    # -- agent activity -----------------------------------------------------

    def _seed_next_action(self) -> str:
        stored = save_review_candidates_to_activity(
            "alice",
            WINDOW_START,
            WINDOW_END,
            "next_action",
            [{"title": "Review follow-up", "source": "review"}],
        )
        return str(stored[0]["id"])

    def _external_activity_write(self, profile: Path) -> None:
        doc = agent_activity.load_agent_activity(profile)
        doc["items"].append({"id": "act:external", "title": "外部并发"})
        atomic_write_text(
            profile / agent_activity.AGENT_ACTIVITY_FILENAME,
            agent_activity._dump_agent_activity(profile.name, doc),
        )

    def test_activity_apply_conflict_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            item_id = self._seed_next_action()
            fetched = client.get(f"/api/v1/profiles/alice/activity/{item_id}")
            etag = fetched.headers["etag"]

            with _wrap_lock(
                agent_activity.locked_profile_write,
                lambda: self._external_activity_write(profile),
            ) as wrapped:
                with patch.object(
                    agent_activity, "locked_profile_write", wrapped
                ):
                    conflicted = client.post(
                        f"/api/v1/profiles/alice/activity/{item_id}/apply",
                        headers={"If-Match": etag},
                    )
            stored = agent_activity.load_agent_activity(profile)
            by_id = {item["id"]: item for item in stored["items"]}

        self.assertEqual(conflicted.status_code, 412)
        self.assertEqual(conflicted.json()["code"], "etag_mismatch")
        self.assertNotEqual(conflicted.headers["etag"], etag)
        # The external item survived and the candidate was not applied.
        self.assertIn("act:external", by_id)
        self.assertEqual(by_id[item_id]["status"], "pending")

    def test_activity_dismiss_conflict_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            item_id = self._seed_next_action()
            fetched = client.get(f"/api/v1/profiles/alice/activity/{item_id}")
            etag = fetched.headers["etag"]

            with _wrap_lock(
                agent_activity.locked_profile_write,
                lambda: self._external_activity_write(profile),
            ) as wrapped:
                with patch.object(
                    agent_activity, "locked_profile_write", wrapped
                ):
                    conflicted = client.post(
                        f"/api/v1/profiles/alice/activity/{item_id}/dismiss",
                        headers={"If-Match": etag},
                    )

        self.assertEqual(conflicted.status_code, 412)
        self.assertEqual(conflicted.json()["code"], "etag_mismatch")

    # -- evidence review ----------------------------------------------------

    def test_evidence_review_bulk_conflict_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            # The template pool ships empty; seed one triage candidate.
            pool_path = profile / profile_io.EVIDENCE_POOL_FILENAME
            raw = yaml.safe_load(pool_path.read_text(encoding="utf-8")) or {}
            raw["evidence_entries"] = [
                {"id": "ev-cand", "title": "候选证据", "type": "practice"}
            ]
            pool_path.write_text(
                yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8"
            )
            client = self._client(root)
            listing = client.get("/api/v1/profiles/alice/evidence-review")
            etag = listing.headers["etag"]
            items = listing.json()["items"]
            assert items, "seeded review candidate should be listed"
            ids = [items[0]["id"]]

            def external_pool_write() -> None:
                raw = yaml.safe_load(pool_path.read_text(encoding="utf-8")) or {}
                raw.setdefault("evidence_entries", []).append(
                    {"id": "ev-external", "title": "外部并发证据"}
                )
                atomic_write_text(pool_path, yaml.safe_dump(raw, allow_unicode=True))

            with _wrap_lock(
                profile_io.locked_profile_write, external_pool_write
            ) as wrapped:
                with patch.object(
                    profile_io, "locked_profile_write", wrapped
                ):
                    conflicted = client.post(
                        "/api/v1/profiles/alice/evidence-review/bulk",
                        json={
                            "ids": ids,
                            "field": "review_status",
                            "value": "reviewed",
                        },
                        headers={"If-Match": etag},
                    )
            raw = yaml.safe_load(
                (profile / profile_io.EVIDENCE_POOL_FILENAME).read_text(
                    encoding="utf-8"
                )
            )
            by_id = {
                str(row.get("id")): row
                for row in raw.get("evidence_entries") or []
            }

        self.assertEqual(conflicted.status_code, 412)
        self.assertEqual(conflicted.json()["code"], "etag_mismatch")
        self.assertNotEqual(conflicted.headers["etag"], etag)
        self.assertIn("ev-external", by_id)
        # The bulk mutation did not land on top of the external write.
        self.assertNotEqual(
            by_id[ids[0]].get("review_status"), "reviewed"
        )

    # -- review save/apply ----------------------------------------------------

    def test_review_save_conflict_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            review = client.get("/api/v1/profiles/alice/review")
            etag = review.headers["etag"]

            with _wrap_lock(
                agent_activity.locked_profile_write,
                lambda: self._external_activity_write(profile),
            ) as wrapped:
                with patch.object(
                    agent_activity, "locked_profile_write", wrapped
                ):
                    conflicted = client.post(
                        "/api/v1/profiles/alice/review/save",
                        json={
                            "candidate_type": "next_action",
                            "start": WINDOW_START,
                            "end": WINDOW_END,
                            "candidates": [{"title": "候选"}],
                        },
                        headers={"If-Match": etag},
                    )

        self.assertEqual(conflicted.status_code, 412)
        self.assertEqual(conflicted.json()["code"], "etag_mismatch")
        self.assertNotEqual(conflicted.headers["etag"], etag)

    def test_review_etag_covers_activity_and_blog(self) -> None:
        """M-API-5: agent-activity.yaml and blog drafts rotate the ETag."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            base = client.get("/api/v1/profiles/alice/review").headers["etag"]
            self._external_activity_write(profile)
            after_activity = client.get(
                "/api/v1/profiles/alice/review"
            ).headers["etag"]
            blog_dir = profile / "blog"
            blog_dir.mkdir(exist_ok=True)
            (blog_dir / "2026-09-19-draft.md").write_text(
                "---\ntitle: 草稿\n---\n\n正文\n", encoding="utf-8"
            )
            after_blog = client.get(
                "/api/v1/profiles/alice/review"
            ).headers["etag"]
        self.assertNotEqual(base, after_activity)
        self.assertNotEqual(after_activity, after_blog)

    # -- project board --------------------------------------------------------

    def _create_case(self, client: TestClient) -> str:
        created = client.post(
            "/api/v1/profiles/alice/project-board/cases",
            json={"title": "演示项目"},
        )
        assert created.status_code == 201, created.text
        return str(created.json()["case"]["id"])

    def test_project_board_save_conflict_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            case_id = self._create_case(client)
            board = client.get("/api/v1/profiles/alice/project-board")
            etag = board.headers["etag"]

            def external_board_write() -> None:
                path = profile / "project-board.yaml"
                raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                raw.setdefault("project_cases", []).append(
                    {"id": "external-case", "title": "外部并发项目"}
                )
                atomic_write_text(path, yaml.safe_dump(raw, allow_unicode=True))

            with _wrap_lock(
                project_board_core.locked_profile_write,
                external_board_write,
            ) as wrapped:
                with patch.object(
                    project_board_core, "locked_profile_write", wrapped
                ):
                    conflicted = client.post(
                        "/api/v1/profiles/alice/project-board/cases/"
                        f"{case_id}/save",
                        json={"summary": "更新摘要"},
                        headers={"If-Match": etag},
                    )
            stored = project_board_core.load_project_board(profile)

        self.assertEqual(conflicted.status_code, 412)
        self.assertEqual(conflicted.json()["code"], "etag_mismatch")
        self.assertNotEqual(conflicted.headers["etag"], etag)
        self.assertIn("external-case", stored.by_id())

    # -- studio ---------------------------------------------------------------

    def test_studio_save_conflict_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _template_profile(root)
            client = self._client(root)
            created = client.post(
                "/api/v1/profiles/alice/studio/blog",
                json={"title": "冲突演示", "body": "初始正文"},
            )
            assert created.status_code == 201, created.text
            slug = str(created.json()["post"]["slug"])
            detail = client.get(f"/api/v1/profiles/alice/studio/blog/{slug}")
            etag = detail.headers["etag"]
            post_path = Path(
                created.json()["changed_paths"][0]
            )

            def external_post_write() -> None:
                text = post_path.read_text(encoding="utf-8")
                atomic_write_text(post_path, text + "\n外部并发编辑\n")

            with _wrap_lock(
                public_site_core.locked_profile_write, external_post_write
            ) as wrapped:
                with patch.object(
                    public_site_core, "locked_profile_write", wrapped
                ):
                    conflicted = client.post(
                        f"/api/v1/profiles/alice/studio/blog/{slug}/save",
                        json={"body": "我的编辑"},
                        headers={"If-Match": etag},
                    )
            body = post_path.read_text(encoding="utf-8")

        self.assertEqual(conflicted.status_code, 412)
        self.assertEqual(conflicted.json()["code"], "etag_mismatch")
        self.assertIn("外部并发编辑", body)
        self.assertNotIn("我的编辑", body)


if __name__ == "__main__":
    unittest.main()
