"""Tests for the content workspace API (blog-only projection over the public layer).

Covers route ordering (``.../media`` must not be swallowed by the greedy
``{slug:path}`` post GET), media upload leaving the post untouched, the
media-file path guard, the save path refusing to skip the publish gate, and
the publish gate itself.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core.paths import REPO_ROOT
from nblane.web_api import app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"

# 1x1 transparent PNG.
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    shutil.copytree(TEMPLATE_DIR, profile)
    (profile / "public-profile.yaml").write_text(
        yaml.safe_dump({"profile": name, "visibility": "private"}),
        encoding="utf-8",
    )
    # Boundary check: the content workspace must work without these.
    for filename in ("evidence-pool.yaml", "claims.yaml"):
        (profile / filename).unlink(missing_ok=True)
    return profile


class ContentWorkspaceApiTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.profile = _profile(self.root)
        for target in (
            "nblane.core.paths.PROFILES_DIR",
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, self.root)
            patcher.start()
            self.addCleanup(patcher.stop)
        for target in (
            "nblane.core.profile_io.git_backup.record_change",
            "nblane.core.public_site.git_backup.record_change",
        ):
            patcher = patch(target)
            patcher.start()
            self.addCleanup(patcher.stop)
        llm = patch("nblane.core.llm.is_configured", return_value=False)
        llm.start()
        self.addCleanup(llm.stop)
        self.client = TestClient(app)

    def _create(self, title: str = "Hello", body: str = "First paragraph.") -> tuple[str, str]:
        response = self.client.post(
            "/api/v1/profiles/alice/content/blog",
            json={"title": title, "body": body},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["post"]["slug"], response.headers["ETag"]

    def _upload(self, slug: str) -> dict:
        response = self.client.post(
            f"/api/v1/profiles/alice/content/blog/{slug}/media?kind=image",
            files={"file": ("shot.png", PNG_BYTES, "image/png")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_list_is_newest_first_and_create_returns_post_etag(self) -> None:
        older, older_etag = self._create("Older")
        # Back-date through the API: the BlockNote sidecar wins over the
        # Markdown front matter on read, so editing the .md is not enough.
        backdated = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{older}",
            json={"date": "2001-01-01"},
            headers={"If-Match": older_etag},
        )
        self.assertEqual(backdated.status_code, 200, backdated.text)
        newer, etag = self._create("Newer")
        detail = self.client.get(f"/api/v1/profiles/alice/content/blog/{newer}")
        self.assertEqual(detail.headers["ETag"], etag)
        posts = self.client.get("/api/v1/profiles/alice/content").json()["posts"]
        self.assertEqual(posts[0]["slug"], newer)

    def test_media_routes_are_not_swallowed_by_post_route(self) -> None:
        slug, _ = self._create()
        self.assertEqual(self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}/media").json(), [])
        uploaded = self._upload(slug)
        rows = self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}/media").json()
        self.assertEqual([row["path"] for row in rows], [uploaded["path"]])
        self.assertEqual(rows[0]["kind"], "image")
        self.assertFalse(rows[0]["referenced"])

    def test_upload_stores_file_without_rewriting_the_post(self) -> None:
        slug, etag = self._create()
        uploaded = self._upload(slug)
        self.assertTrue(uploaded["path"].startswith(f"media/blog/{slug}/"))
        self.assertIn(uploaded["path"], uploaded["snippet"])
        # Same ETag: an open editor can still save without a 412.
        detail = self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}")
        self.assertEqual(detail.headers["ETag"], etag)
        self.assertNotIn(uploaded["path"], detail.json()["body"])
        self.assertEqual(detail.json()["cover"], "")

    def test_media_file_serves_only_under_media(self) -> None:
        slug, _ = self._create()
        uploaded = self._upload(slug)
        ok = self.client.get(f"/api/v1/profiles/alice/content/media-file/{uploaded['path']}")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.content, PNG_BYTES)
        for bad in ("resume-source.yaml", "media/../resume-source.yaml", "media/missing.png"):
            response = self.client.get(f"/api/v1/profiles/alice/content/media-file/{bad}")
            self.assertEqual(response.status_code, 404, bad)

    def test_save_cannot_skip_publish_gate(self) -> None:
        slug, etag = self._create()
        response = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}",
            json={"status": "published"},
            headers={"If-Match": etag},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "publish_requires_check")
        detail = self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}")
        self.assertEqual(detail.json()["status"], "draft")

    def test_save_round_trips_body_and_blocks_and_detects_conflicts(self) -> None:
        slug, etag = self._create()
        blocks = [{"id": "b1", "type": "paragraph", "props": {}, "content": [], "children": []}]
        saved = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}",
            json={"body": "Edited body.\n", "summary": "S", "blocks_json": blocks},
            headers={"If-Match": etag},
        )
        self.assertEqual(saved.status_code, 200, saved.text)
        detail = self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}").json()
        self.assertEqual(detail["body"].strip(), "Edited body.")
        self.assertEqual([block["id"] for block in detail["blocks_json"]], ["b1"])
        stale = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}",
            json={"body": "Lost update"},
            headers={"If-Match": etag},
        )
        self.assertEqual(stale.status_code, 412)

    def test_autosave_writes_but_skips_git_backup(self) -> None:
        from nblane.core import git_backup

        # setUp replaced record_change with a mock; record whether each call
        # happened inside skip_changes() (the deferral context is set).
        suppressed: list[bool] = []
        git_backup.record_change.side_effect = lambda *a, **k: suppressed.append(
            git_backup._deferred_changes.get() is not None
        )
        slug, etag = self._create()
        suppressed.clear()
        saved = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}?autosave=1",
            json={"body": "Autosaved body.\n"},
            headers={"If-Match": etag},
        )
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertTrue(suppressed and all(suppressed), suppressed)
        suppressed.clear()
        explicit = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}",
            json={"body": "Explicit body.\n"},
            headers={"If-Match": saved.headers["ETag"]},
        )
        self.assertEqual(explicit.status_code, 200, explicit.text)
        self.assertTrue(suppressed and not any(suppressed), suppressed)
        detail = self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}").json()
        self.assertEqual(detail["body"].strip(), "Explicit body.")

    def test_publish_runs_the_gate(self) -> None:
        slug, etag = self._create()
        blocked = self.client.post(
            f"/api/v1/profiles/alice/content/blog/{slug}/publish",
            json={"summary": ""},
            headers={"If-Match": etag},
        )
        self.assertEqual(blocked.status_code, 422)
        published = self.client.post(
            f"/api/v1/profiles/alice/content/blog/{slug}/publish",
            json={"summary": "A real summary.", "status": "published"},
            headers={"If-Match": etag},
        )
        self.assertEqual(published.status_code, 200, published.text)
        self.assertEqual(published.json()["post"]["status"], "published")


def test_skip_changes_suppresses_record_change(tmp_path: Path) -> None:
    """Inside skip_changes() the real hook neither commits nor queues."""
    from nblane.core import git_backup

    with patch("nblane.core.git_backup.autocommit_enabled", return_value=True), patch(
        "nblane.core.git_backup._run_git"
    ) as run_git:
        with git_backup.skip_changes():
            result = git_backup.record_change([tmp_path / "a.md"], action="autosave")
        run_git.assert_not_called()
    assert result.skipped_reason == "deferred"
    assert result.committed is False


if __name__ == "__main__":
    unittest.main()
