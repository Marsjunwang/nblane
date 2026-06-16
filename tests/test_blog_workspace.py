"""Tests for the shared blog workspace payload + event dispatcher."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core import blog_workspace as bw
from nblane.core import public_site


def _write_blog(path: Path, *, title: str, status: str, body: str = "Body text.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    front = (
        "---\n"
        f"title: {title}\n"
        f"status: {status}\n"
        "summary: A short summary.\n"
        "date: '2026-05-01'\n"
        "---\n\n"
        f"{body}\n"
    )
    path.write_text(front, encoding="utf-8")


class BlogWorkspaceTests(unittest.TestCase):
    def _profile(self, root: Path) -> Path:
        profile = root / "alice"
        (profile / "blog").mkdir(parents=True)
        _write_blog(
            profile / "blog" / "2026-05-01-first.md",
            title="First Post",
            status="draft",
        )
        _write_blog(
            profile / "blog" / "2026-05-02-second.md",
            title="Second Post",
            status="published",
        )
        return profile

    def test_build_payload_lists_posts_and_loads_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                payload = bw.build_blog_workspace_payload("alice")
        self.assertEqual(len(payload["posts"]), 2)
        self.assertTrue(payload["active_slug"])
        self.assertIn("initial_markdown", payload)
        self.assertIsInstance(payload["category_options"], list)
        self.assertIsInstance(payload["library_tree"], list)

    def test_status_filter_narrows_posts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                payload = bw.build_blog_workspace_payload("alice", status_filter="published")
        self.assertTrue(all(p["status"] == "published" for p in payload["posts"]))

    def test_active_slug_resolves_by_route(self) -> None:
        # The library tree selects posts by route; the payload builder must
        # resolve that route back to the post so the document loads.
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                payload = bw.build_blog_workspace_payload("alice")
                route = payload["posts"][0]["route"]
                loaded = bw.build_blog_workspace_payload("alice", active_slug=route)
        self.assertEqual(loaded["active_slug"], payload["posts"][0]["slug"])
        self.assertTrue(loaded["initial_markdown"])

    def test_select_post_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = bw.handle_blog_workspace_event(
                    "alice",
                    {"action": "select_post", "payload": {"slug": "2026-05-01-first"}},
                )
        self.assertTrue(result.handled)
        self.assertEqual(result.slug, "2026-05-01-first")

    def test_save_post_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                event = {
                    "action": "save_post",
                    "payload": {
                        "slug": "2026-05-01-first",
                        "meta": {"title": "First Post", "status": "draft"},
                        "markdown": "# Heading\n\nNew body content.",
                        "blocks_json": [],
                    },
                }
                result = bw.handle_blog_workspace_event("alice", event)
                self.assertTrue(result.ok, result.errors)
                reloaded = public_site.load_blog_post("alice", "2026-05-01-first")
        self.assertIn("New body content.", reloaded.body)

    def test_run_check_validates_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = bw.handle_blog_workspace_event(
                    "alice",
                    {
                        "action": "run_check",
                        "payload": {"slug": "2026-05-01-first"},
                    },
                )
        self.assertTrue(result.handled)
        self.assertEqual(result.action, "run_check")

    def test_unhandled_action_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = bw.handle_blog_workspace_event(
                    "alice",
                    {"action": "ai_inline_action", "payload": {}},
                )
        self.assertFalse(result.handled)
        self.assertEqual(result.action, "ai_inline_action")

    def test_preview_post_renders_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = bw.handle_blog_workspace_event(
                    "alice",
                    {"action": "preview_post", "payload": {"slug": "2026-05-01-first"}},
                )
        self.assertTrue(result.ok, result.errors)
        self.assertTrue(result.extra.get("preview_html"))

    def test_upload_and_delete_media_round_trip(self) -> None:
        import base64

        # 1x1 transparent PNG.
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
            "+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
        )
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                up = bw.handle_blog_workspace_event(
                    "alice",
                    {
                        "action": "upload_media",
                        "payload": {
                            "slug": "2026-05-01-first",
                            "data": base64.b64encode(png).decode(),
                            "filename": "tiny.png",
                            "kind": "image",
                        },
                    },
                )
                self.assertTrue(up.ok, up.errors)
                rel = up.extra["media"]["relative_path"]
                self.assertTrue(rel)
                deleted = bw.handle_blog_workspace_event(
                    "alice",
                    {"action": "delete_media", "payload": {"slug": "2026-05-01-first", "rel": rel}},
                )
        self.assertTrue(deleted.ok, deleted.errors)

    def test_upload_media_requires_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = bw.handle_blog_workspace_event(
                    "alice",
                    {"action": "upload_media", "payload": {"data": "x"}},
                )
        self.assertFalse(result.ok)
        self.assertTrue(result.handled)

    def test_permanent_delete_active_post_removes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            md_path = profile / "blog" / "2026-05-01-first.md"
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                # Reconcile so the active post gets a library node id.
                public_site.reconcile_public_library("alice")
                tree = public_site.list_public_library_tree("alice")
                node_id = ""

                def _walk(nodes: list) -> None:
                    nonlocal node_id
                    for node in nodes:
                        if node.get("type") == "post" and "first" in (
                            node.get("ref", "") + node.get("route", "")
                        ):
                            node_id = node.get("id", "")
                        _walk(node.get("children", []) or [])

                _walk(tree.get("children", []) if isinstance(tree, dict) else tree)
                self.assertTrue(node_id, "active post node id not found")

                result = bw.handle_blog_workspace_event(
                    "alice",
                    {
                        "action": "library_permanent_delete_node",
                        "payload": {
                            "node_id": node_id,
                            "delete_files": True,
                            "trash_first": True,
                        },
                    },
                )
                self.assertTrue(result.ok, result.errors)
                # The markdown file must be gone so the post does not reappear.
                self.assertFalse(md_path.exists())
                payload = bw.build_blog_workspace_payload("alice")
            slugs = {p["slug"] for p in payload["posts"]}
            self.assertNotIn("2026-05-01-first", slugs)

    def test_permanent_delete_virtual_post_removes_file(self) -> None:
        # A virtual post is a markdown file on disk with no library node yet
        # (id "post:<route>"). Deleting it must materialize then purge the file.
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            md_path = profile / "blog" / "2026-05-01-first.md"
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                self.assertTrue(md_path.exists())
                result = bw.handle_blog_workspace_event(
                    "alice",
                    {
                        "action": "library_permanent_delete_node",
                        "payload": {
                            "node_id": "post:2026-05-01-first",
                            "ref": "blog/2026-05-01-first.md",
                            "parent_id": "root",
                            "title": "First Post",
                            "delete_files": True,
                            "trash_first": True,
                        },
                    },
                )
                self.assertTrue(result.ok, result.errors)
                self.assertFalse(md_path.exists())
                payload = bw.build_blog_workspace_payload("alice")
            slugs = {p["slug"] for p in payload["posts"]}
            self.assertNotIn("2026-05-01-first", slugs)


if __name__ == "__main__":
    unittest.main()
