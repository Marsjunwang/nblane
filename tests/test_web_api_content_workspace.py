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
from contextlib import contextmanager
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
        # Back-date through the API so the .md and the sidecar move together
        # (a hand-edited .md would win over the sidecar on read).
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

    def test_replayed_save_with_stale_etag_succeeds_without_writing(self) -> None:
        slug, etag = self._create()
        blocks = [{"id": "b1", "type": "paragraph", "props": {}, "content": [], "children": []}]
        payload = {"title": "Hello", "body": "Saved once.\n", "blocks_json": blocks}
        first = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}",
            json=payload,
            headers={"If-Match": etag},
        )
        self.assertEqual(first.status_code, 200, first.text)
        # The client never saw the first response and retries with the old ETag.
        replay = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}",
            json=payload,
            headers={"If-Match": etag},
        )
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertEqual(replay.headers["ETag"], first.headers["ETag"])
        # A different body with the stale ETag is still a real conflict.
        stale = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}",
            json={**payload, "body": "Someone else's edit.\n"},
            headers={"If-Match": etag},
        )
        self.assertEqual(stale.status_code, 412)

    def test_erasing_a_non_empty_body_needs_allow_empty(self) -> None:
        slug, etag = self._create(body="Keep me.")
        blocked = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}?autosave=1",
            json={"body": "", "blocks_json": []},
            headers={"If-Match": etag},
        )
        self.assertEqual(blocked.status_code, 409, blocked.text)
        self.assertEqual(blocked.json()["code"], "empty_body_requires_confirm")
        detail = self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}").json()
        self.assertEqual(detail["body"].strip(), "Keep me.")
        allowed = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}?allow_empty=1",
            json={"body": "", "blocks_json": []},
            headers={"If-Match": etag},
        )
        self.assertEqual(allowed.status_code, 200, allowed.text)
        self.assertEqual(
            self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}").json()["body"].strip(), ""
        )

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

    def test_autosave_returns_slim_response_and_usable_etag(self) -> None:
        slug, etag = self._create()
        saved = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}?autosave=1",
            json={"body": "Autosaved body.\n", "summary": "S"},
            headers={"If-Match": etag},
        )
        self.assertEqual(saved.status_code, 200, saved.text)
        payload = saved.json()
        self.assertTrue(payload["ok"])
        # Slim autosave: no post echo, only the fresh ETag in the header.
        self.assertIsNone(payload["post"])
        autosaved_etag = saved.headers["ETag"]
        self.assertTrue(autosaved_etag)
        # The ETag must match what a reload reports (next save can use it).
        detail = self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}")
        self.assertEqual(detail.headers["ETag"], autosaved_etag)
        self.assertEqual(detail.json()["body"].strip(), "Autosaved body.")
        followup = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}?autosave=1",
            json={"body": "Second autosave.\n"},
            headers={"If-Match": autosaved_etag},
        )
        self.assertEqual(followup.status_code, 200, followup.text)
        # Explicit saves still echo the re-parsed post.
        explicit = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}",
            json={"body": "Explicit body.\n"},
            headers={"If-Match": followup.headers["ETag"]},
        )
        self.assertEqual(explicit.status_code, 200, explicit.text)
        self.assertIsNotNone(explicit.json()["post"])
        self.assertEqual(explicit.json()["post"]["body"].strip(), "Explicit body.")

    def test_list_reads_meta_without_validating_sidecar_blocks(self) -> None:
        slug, etag = self._create()
        saved = self.client.put(
            f"/api/v1/profiles/alice/content/blog/{slug}",
            json={
                "body": "Body.\n",
                "summary": "List summary",
                "tags": ["a", "b"],
                "blocks_json": [
                    {"id": "b1", "type": "paragraph", "props": {}, "content": [], "children": []}
                ],
            },
            headers={"If-Match": etag},
        )
        self.assertEqual(saved.status_code, 200, saved.text)
        # The list must not pydantic-validate sidecar blocks: make that blow up.
        with patch(
            "nblane.core.public_site.BlockNoteDocument.model_validate",
            side_effect=AssertionError("sidecar blocks were validated"),
        ):
            response = self.client.get("/api/v1/profiles/alice/content")
        self.assertEqual(response.status_code, 200, response.text)
        posts = response.json()["posts"]
        row = next(item for item in posts if item["slug"] == slug)
        self.assertEqual(row["title"], "Hello")
        self.assertEqual(row["summary"], "List summary")
        self.assertEqual(row["tags"], ["a", "b"])
        self.assertEqual(row["status"], "draft")

    def test_list_response_is_gzipped_over_threshold(self) -> None:
        for index in range(3):
            created = self.client.post(
                "/api/v1/profiles/alice/content/blog",
                json={"title": f"Post {index}", "summary": "摘要填充。" * 200},
            )
            self.assertEqual(created.status_code, 201, created.text)
        response = self.client.get(
            "/api/v1/profiles/alice/content", headers={"Accept-Encoding": "gzip"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers.get("content-encoding"), "gzip")
        # httpx already decoded it: the payload must still parse.
        self.assertEqual(len(response.json()["posts"]), 3)
        # Small responses stay uncompressed.
        small = self.client.get("/api/v1/health", headers={"Accept-Encoding": "gzip"})
        self.assertNotEqual(small.headers.get("content-encoding"), "gzip")

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

    def _delete(self, slug: str, etag: str, title: str = "Hello", **extra):
        return self.client.request(
            "DELETE", f"/api/v1/profiles/alice/content/blog/{slug}",
            json={"confirm_title": title, **extra}, headers={"If-Match": etag},
        )

    def test_delete_removes_documents_and_library_entry_but_keeps_shared_media(self) -> None:
        from nblane.core import public_site

        slug, etag = self._create()
        uploaded = self._upload(slug)
        # Another article uses this article's media; deleting must not break it.
        other, _ = self._create("Other", body=uploaded["snippet"])
        attached = public_site.attach_existing_public_library_node("alice", None, f"blog/{slug}.md")
        public_site.attach_existing_public_library_node("alice", attached.node.id, uploaded["path"])
        response = self._delete(slug, etag)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["deleted_slug"], slug)
        for suffix in (".md", ".blocknote.json"):
            self.assertFalse((self.profile / "blog" / f"{slug}{suffix}").exists())
        self.assertTrue((self.profile / uploaded["path"]).exists())
        library = public_site.load_public_library("alice")
        self.assertFalse(any(node.ref == f"blog/{slug}.md" for node in library.nodes))
        media = next(node for node in library.nodes if node.ref == uploaded["path"])
        self.assertEqual(media.parent_id, "root")
        self.assertEqual(self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/profiles/alice/content/blog/{other}").status_code, 200)
        posts = self.client.get("/api/v1/profiles/alice/content").json()["posts"]
        self.assertNotIn(slug, [post["slug"] for post in posts])
        self.assertFalse((self.profile / "chronicle.yaml").exists())
        # A late autosave cannot resurrect either source document.
        late = self.client.put(f"/api/v1/profiles/alice/content/blog/{slug}", json={"body": "late"})
        self.assertEqual(late.status_code, 404)

    def test_delete_requires_exact_title_and_concrete_etag(self) -> None:
        slug, etag = self._create()
        for bad_etag in ("", "*"):
            response = self._delete(slug, bad_etag)
            self.assertEqual(response.status_code, 428, response.text)
        for bad_title in ("hello", " Hello", "Hello "):
            response = self._delete(slug, etag, bad_title)
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(response.json()["code"], "content_delete_confirm_mismatch")
        self.assertEqual(self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}").status_code, 200)

    def test_delete_rejects_stale_etag_and_unknown_post(self) -> None:
        slug, etag = self._create()
        updated = self.client.put(f"/api/v1/profiles/alice/content/blog/{slug}", json={"body": "New body"})
        self.assertEqual(updated.status_code, 200, updated.text)
        stale = self._delete(slug, etag)
        self.assertEqual(stale.status_code, 412, stale.text)
        self.assertEqual(stale.headers["ETag"], updated.headers["ETag"])
        self.assertEqual(self._delete("missing", etag).status_code, 404)

    def test_delete_detects_edit_landing_before_lock(self) -> None:
        from nblane.core import public_site

        slug, etag = self._create()
        real_lock = public_site.locked_profile_write
        path = self.profile / "blog" / f"{slug}.md"

        @contextmanager
        def racing_lock(*args, **kwargs):
            path.write_text(path.read_text() + "\nConcurrent edit\n", encoding="utf-8")
            with real_lock(*args, **kwargs) as lock:
                yield lock

        with patch.object(public_site, "locked_profile_write", racing_lock):
            response = self._delete(slug, etag)
        self.assertEqual(response.status_code, 412, response.text)
        self.assertIn("Concurrent edit", path.read_text())
        self.assertTrue(path.with_suffix(".blocknote.json").exists())

    def test_delete_rolls_back_when_library_write_fails(self) -> None:
        from nblane.core import public_site

        slug, etag = self._create()
        public_site.attach_existing_public_library_node("alice", None, f"blog/{slug}.md")
        paths = [self.profile / "blog" / f"{slug}.md", self.profile / "blog" / f"{slug}.blocknote.json",
                 self.profile / "public-library.yaml"]
        before = [path.read_bytes() for path in paths]
        with patch.object(public_site, "save_public_library", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self._delete(slug, etag)
        self.assertEqual([path.read_bytes() for path in paths], before)

    def test_delete_published_and_archived_posts_with_optional_chronicle(self) -> None:
        from nblane.core.chronicle import load_chronicle

        for status in ("published", "archived"):
            slug, etag = self._create(status)
            endpoint = f"/api/v1/profiles/alice/content/blog/{slug}"
            if status == "published":
                changed = self.client.post(endpoint + "/publish", json={"summary": "Summary"}, headers={"If-Match": etag})
            else:
                changed = self.client.put(endpoint, json={"status": status}, headers={"If-Match": etag})
            self.assertEqual(changed.status_code, 200, changed.text)
            deleted = self._delete(slug, changed.headers["ETag"], status, record_chronicle=True)
            self.assertEqual(deleted.status_code, 200, deleted.text)
            self.assertEqual(self.client.get(endpoint).status_code, 404)
        entries = load_chronicle(self.profile)
        self.assertEqual([entry.kind for entry in entries], ["content.deleted", "content.deleted"])
        self.assertEqual([entry.note for entry in entries], ["published", "archived"])

    def test_delete_supports_nested_routes_and_sidecar_only_posts(self) -> None:
        slug, _ = self._create()
        directory = self.profile / "blog" / "notes"
        directory.mkdir()
        for suffix in (".md", ".blocknote.json"):
            (self.profile / "blog" / f"{slug}{suffix}").rename(directory / f"{slug}{suffix}")
        (directory / f"{slug}.md").unlink()
        nested = f"notes/{slug}"
        detail = self.client.get(f"/api/v1/profiles/alice/content/blog/{nested}")
        self.assertEqual(detail.status_code, 200, detail.text)
        response = self._delete(nested, detail.headers["ETag"])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse((directory / f"{slug}.blocknote.json").exists())

    def _trash(self) -> list[dict]:
        response = self.client.get("/api/v1/profiles/alice/content/trash")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["items"]

    def test_delete_moves_post_to_trash_and_restore_brings_it_back(self) -> None:
        from nblane.core import public_site, social_cards

        slug, etag = self._create()
        public_site.attach_existing_public_library_node("alice", None, f"blog/{slug}.md")
        social_cards.save_settings("alice", slug, {"cover_title": "封面"})
        original = (self.profile / "blog" / f"{slug}.md").read_bytes()
        deleted = self._delete(slug, etag)
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertFalse(deleted.json()["was_published"])
        # Share-card settings leave with the post, so a new post at the same
        # route starts clean.
        self.assertEqual(social_cards.load_settings("alice", slug)["cover_title"], "")
        items = self._trash()
        self.assertEqual([(item["route"], item["title"]) for item in items], [(slug, "Hello")])
        # Trash is hidden from listings.
        posts = self.client.get("/api/v1/profiles/alice/content").json()["posts"]
        self.assertNotIn(slug, [post["slug"] for post in posts])

        restored = self.client.post(f"/api/v1/profiles/alice/content/trash/{items[0]['id']}/restore")
        self.assertEqual(restored.status_code, 200, restored.text)
        self.assertEqual(restored.json()["slug"], slug)
        self.assertEqual((self.profile / "blog" / f"{slug}.md").read_bytes(), original)
        self.assertEqual(self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}").status_code, 200)
        self.assertTrue(any(node.ref == f"blog/{slug}.md" for node in public_site.load_public_library("alice").nodes))
        self.assertEqual(social_cards.load_settings("alice", slug)["cover_title"], "封面")
        self.assertEqual(self._trash(), [])

    def test_restore_refuses_to_overwrite_and_purge_removes_entry(self) -> None:
        slug, etag = self._create()
        self.assertEqual(self._delete(slug, etag).status_code, 200)
        trash_id = self._trash()[0]["id"]
        # A new post took the same route meanwhile.
        again, _ = self._create()
        self.assertEqual(again, slug)
        conflict = self.client.post(f"/api/v1/profiles/alice/content/trash/{trash_id}/restore")
        self.assertEqual(conflict.status_code, 409, conflict.text)
        self.assertEqual(len(self._trash()), 1)
        purged = self.client.delete(f"/api/v1/profiles/alice/content/trash/{trash_id}")
        self.assertEqual(purged.status_code, 200, purged.text)
        self.assertEqual(self._trash(), [])
        self.assertFalse((self.profile / "blog" / ".trash" / trash_id).exists())
        for bad in (trash_id, "nope"):
            self.assertEqual(self.client.post(f"/api/v1/profiles/alice/content/trash/{bad}/restore").status_code, 404)
            self.assertEqual(self.client.delete(f"/api/v1/profiles/alice/content/trash/{bad}").status_code, 404)

    def test_trash_ids_cannot_escape_the_trash_folder(self) -> None:
        from nblane.core import public_site
        from nblane.core.public_site import PublicSiteError

        for bad in ("..", "../x", "20260101T000000-abcdef/../..", ""):
            with self.assertRaises(PublicSiteError):
                public_site.restore_trashed_blog_post("alice", bad)
            with self.assertRaises(PublicSiteError):
                public_site.purge_trashed_blog_post("alice", bad)

    def test_delete_reports_published_and_failed_delete_leaves_no_trash(self) -> None:
        from nblane.core import public_site

        slug, etag = self._create()
        endpoint = f"/api/v1/profiles/alice/content/blog/{slug}"
        published = self.client.post(endpoint + "/publish", json={"summary": "Summary"}, headers={"If-Match": etag})
        self.assertEqual(published.status_code, 200, published.text)
        public_site.attach_existing_public_library_node("alice", None, f"blog/{slug}.md")
        with patch.object(public_site, "save_public_library", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self._delete(slug, published.headers["ETag"])
        self.assertEqual(self._trash(), [])
        self.assertTrue((self.profile / "blog" / f"{slug}.md").exists())
        fresh = self.client.get(endpoint).headers["ETag"]
        deleted = self._delete(slug, fresh)
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertTrue(deleted.json()["was_published"])

    def _unused(self) -> list[str]:
        response = self.client.get("/api/v1/profiles/alice/content/unused-media")
        self.assertEqual(response.status_code, 200, response.text)
        return [item["path"] for item in response.json()["items"]]

    def test_unused_media_counts_every_post_and_the_trash(self) -> None:
        slug, etag = self._create()
        used = self._upload(slug)
        spare = self._upload(slug)
        # This post embeds one file; the other is only used by a second post.
        put = self.client.put(f"/api/v1/profiles/alice/content/blog/{slug}",
                              json={"body": used["snippet"]}, headers={"If-Match": etag})
        self.assertEqual(put.status_code, 200, put.text)
        other, other_etag = self._create("Other", body=spare["snippet"])
        self.assertEqual(self._unused(), [])
        # Deleting the second post keeps its file in use while it sits in the trash.
        self.assertEqual(self._delete(other, other_etag, "Other").status_code, 200)
        self.assertEqual(self._unused(), [])
        trash_id = self.client.get("/api/v1/profiles/alice/content/trash").json()["items"][0]["id"]
        self.assertEqual(self.client.delete(f"/api/v1/profiles/alice/content/trash/{trash_id}").status_code, 200)
        self.assertEqual(self._unused(), [spare["path"]])

        removed = self.client.post("/api/v1/profiles/alice/content/unused-media/delete",
                                   json={"paths": [spare["path"], used["path"], "../../etc/passwd"]})
        self.assertEqual(removed.status_code, 200, removed.text)
        # Only the unused file goes; the referenced one and junk are skipped.
        self.assertEqual(removed.json()["removed"], [spare["path"]])
        self.assertFalse((self.profile / spare["path"]).exists())
        self.assertTrue((self.profile / used["path"]).exists())
        self.assertEqual(self._unused(), [])

    def test_single_media_delete_refuses_files_other_posts_use(self) -> None:
        from nblane.core import public_site
        from nblane.core.public_site import PublicSiteError

        slug, _ = self._create()
        uploaded = self._upload(slug)
        self._create("Other", body=uploaded["snippet"])
        with self.assertRaisesRegex(PublicSiteError, "another post"):
            public_site.delete_blog_media("alice", slug, uploaded["path"])
        self.assertTrue((self.profile / uploaded["path"]).exists())


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
