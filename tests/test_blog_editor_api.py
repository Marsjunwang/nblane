"""Tests for the standalone blog editor Reader API endpoints."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from nblane.web_reader_api import app


def _write_blog(path: Path, *, title: str, status: str, body: str = "Body text.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "---\n"
            f"title: {title}\n"
            f"status: {status}\n"
            "summary: A short summary.\n"
            "date: '2026-05-01'\n"
            "---\n\n"
            f"{body}\n"
        ),
        encoding="utf-8",
    )


class BlogEditorApiTests(unittest.TestCase):
    def _profile(self, root: Path) -> Path:
        profile = root / "alice"
        (profile / "blog").mkdir(parents=True)
        _write_blog(profile / "blog" / "2026-05-01-first.md", title="First", status="draft")
        return profile

    def _client(self, profile: Path) -> TestClient:
        patcher = patch("nblane.web_reader_api.profile_dir", return_value=profile)
        self.addCleanup(patcher.stop)
        patcher.start()
        # blog_workspace resolves through public_site.profile_dir
        patcher2 = patch("nblane.core.public_site.profile_dir", lambda _n: profile)
        self.addCleanup(patcher2.stop)
        patcher2.start()
        return TestClient(app)

    def test_blog_editor_page_serves_standalone_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_READER_TOKEN_SECRET": "test-secret"}, clear=False
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            resp = client.get("/blog-editor?profile=alice")
        # The build may or may not be present in CI; both are acceptable contracts.
        if resp.status_code == 200:
            self.assertIn("__NBLANE_BLOG_STANDALONE__", resp.text)
            self.assertIn("/blog-editor/assets/", resp.text)
        else:
            self.assertEqual(resp.status_code, 404)

    def test_workspace_payload_lists_posts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_READER_TOKEN_SECRET": "test-secret"}, clear=False
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            resp = client.get("/api/blog/alice/workspace")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()["payload"]
        self.assertEqual(len(payload["posts"]), 1)
        self.assertEqual(payload["active_slug"], "2026-05-01-first")

    def test_event_run_check_handled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_READER_TOKEN_SECRET": "test-secret"}, clear=False
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            resp = client.post(
                "/api/blog/alice/events",
                json={"event": {"action": "run_check", "payload": {"slug": "2026-05-01-first"}}},
                headers={"Origin": "http://testserver", "Host": "testserver"},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["handled"])

    def test_event_unhandled_returns_422(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_READER_TOKEN_SECRET": "test-secret"}, clear=False
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            resp = client.post(
                "/api/blog/alice/events",
                json={"event": {"action": "ai_inline_action", "payload": {}}},
                headers={"Origin": "http://testserver", "Host": "testserver"},
            )
        self.assertEqual(resp.status_code, 422)
        self.assertFalse(resp.json()["handled"])

    def test_event_cross_origin_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_READER_TOKEN_SECRET": "test-secret"}, clear=False
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            resp = client.post(
                "/api/blog/alice/events",
                json={"event": {"action": "run_check", "payload": {"slug": "2026-05-01-first"}}},
                headers={"Origin": "http://evil.example", "Host": "testserver"},
            )
        self.assertEqual(resp.status_code, 403)

    def test_ai_start_poll_cancel_lifecycle(self) -> None:
        snapshot = {"task_id": "t1", "status": "running", "text": "", "patch": {}}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_READER_TOKEN_SECRET": "test-secret"}, clear=False
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            headers = {"Origin": "http://testserver", "Host": "testserver"}
            with patch(
                "nblane.web_reader_api.ai_stream_tasks.start_ai_patch_stream",
                return_value=snapshot,
            ) as start, patch(
                "nblane.web_reader_api.ai_stream_tasks.cleanup"
            ):
                resp = client.post(
                    "/api/blog/alice/ai/start",
                    json={"payload": {"slug": "2026-05-01-first", "operation": "polish", "stream_id": "t1"}},
                    headers=headers,
                )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["stream_id"], "t1")
            self.assertTrue(start.called)

            with patch(
                "nblane.web_reader_api.ai_stream_tasks.snapshot",
                return_value={**snapshot, "status": "done"},
            ):
                resp = client.get("/api/blog/alice/ai/poll?stream_id=t1")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["stream"]["status"], "done")

            with patch(
                "nblane.web_reader_api.ai_stream_tasks.cancel",
                return_value={**snapshot, "status": "cancelled"},
            ):
                resp = client.post(
                    "/api/blog/alice/ai/cancel",
                    json={"payload": {"stream_id": "t1"}},
                    headers=headers,
                )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["stream"]["status"], "cancelled")

    def test_ai_poll_requires_stream_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_READER_TOKEN_SECRET": "test-secret"}, clear=False
        ):
            profile = self._profile(Path(tmp))
            client = self._client(profile)
            resp = client.get("/api/blog/alice/ai/poll")
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
