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
(``save_kanban_with_merge``) instead of answering 412.
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

from nblane.core import profile_io
from nblane.core import project_board as project_board_core
from nblane.core import public_site as public_site_core
from nblane.core.file_write import atomic_write_text
from nblane.core.paths import REPO_ROOT
from nblane.web_api import app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"

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

    # -- content (blog) ---------------------------------------------------------------

    def test_content_blog_save_conflict_412(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _template_profile(root)
            client = self._client(root)
            created = client.post(
                "/api/v1/profiles/alice/content/blog",
                json={"title": "冲突演示", "body": "初始正文"},
            )
            assert created.status_code == 201, created.text
            slug = str(created.json()["post"]["slug"])
            detail = client.get(f"/api/v1/profiles/alice/content/blog/{slug}")
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
                    conflicted = client.put(
                        f"/api/v1/profiles/alice/content/blog/{slug}",
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
