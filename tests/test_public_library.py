"""Tests for Public Site file-tree management."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core import public_site


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(
            data,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_blog(
    path: Path,
    *,
    title: str = "Published Post",
    status: str = "published",
    body: str = "Public body.",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "title": title,
        "date": "2026-04-29",
        "status": status,
        "tags": ["robotics"],
        "summary": "Short summary",
        "cover": "",
        "related_evidence": [],
        "related_kanban": [],
    }
    path.write_text(
        "---\n"
        + yaml.dump(
            meta,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
        + "---\n\n"
        + body
        + "\n",
        encoding="utf-8",
    )


def _library_yaml(nodes: list[dict]) -> dict:
    return {
        "version": 1,
        "profile": "alice",
        "nodes": [
            {
                "id": "root",
                "type": "root",
                "title": "Public Library",
                "parent_id": "",
                "order": 0,
                "visibility": "private",
                "status": "active",
            },
            *nodes,
        ],
    }


def _make_profile(root: Path) -> Path:
    profile = root / "alice"
    profile.mkdir(parents=True)
    _write_blog(profile / "blog" / "published-post.md")
    return profile


def _library_order(library: public_site.PublicLibrary, parent_id: str) -> list[str]:
    return [
        node.id
        for node in sorted(
            (
                node
                for node in library.nodes
                if node.parent_id == parent_id and node.status != "trashed"
            ),
            key=lambda node: (node.order, node.title, node.id),
        )
    ]


class TestPublicLibrary(unittest.TestCase):
    """Public Library data and CLI behavior."""

    def test_reconcile_imports_posts_and_blog_media(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            media_dir = profile / "media" / "blog" / "published-post"
            media_dir.mkdir(parents=True)
            (media_dir / "photo.png").write_bytes(b"png")

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = public_site.reconcile_public_library("alice")
                tree = public_site.list_public_library_tree(
                    "alice",
                    include_trashed=True,
                )

            data = yaml.safe_load(
                (profile / "public-library.yaml").read_text(encoding="utf-8")
            )
            refs = {node.get("ref") for node in data["nodes"]}
            self.assertIn("blog/published-post.md", refs)
            self.assertIn("media/blog/published-post/photo.png", refs)
            self.assertIn("created", "\n".join(result.warnings))
            self.assertEqual(tree[0]["id"], "root")
            self.assertTrue(tree[0]["children"])

    def test_trash_restore_and_purge_filter_blog_posts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            _write_yaml(
                profile / "public-library.yaml",
                _library_yaml(
                    [
                        {
                            "id": "post_published",
                            "type": "post",
                            "title": "Published Post",
                            "ref": "blog/published-post.md",
                            "parent_id": "root",
                            "order": 10,
                            "visibility": "public",
                            "status": "active",
                            "owned": True,
                        }
                    ]
                ),
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                self.assertEqual(
                    [post.route for post in public_site.load_blog_posts("alice")],
                    ["published-post"],
                )

                trashed = public_site.trash_public_library_node(
                    "alice",
                    "post_published",
                )
                self.assertIn("trashed", "\n".join(trashed.warnings))
                self.assertEqual(public_site.load_blog_posts("alice"), [])
                with self.assertRaises(public_site.PublicSiteError):
                    public_site.load_blog_post("alice", "published-post")
                self.assertEqual(
                    public_site.load_blog_post(
                        "alice",
                        "published-post",
                        include_trashed=True,
                    ).title,
                    "Published Post",
                )
                self.assertEqual(
                    public_site.public_library_trash_nodes("alice")[0]["id"],
                    "post_published",
                )

                public_site.restore_public_library_node("alice", "post_published")
                self.assertEqual(
                    [post.route for post in public_site.load_blog_posts("alice")],
                    ["published-post"],
                )

                public_site.trash_public_library_node("alice", "post_published")
                public_site.purge_public_library_node(
                    "alice",
                    "post_published",
                    delete_files=False,
                )
                library = public_site.load_public_library("alice")

            self.assertTrue((profile / "blog" / "published-post.md").exists())
            self.assertNotIn("post_published", {node.id for node in library.nodes})

    def test_active_ref_wins_over_previous_trashed_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            _write_yaml(
                profile / "public-library.yaml",
                _library_yaml(
                    [
                        {
                            "id": "old_post",
                            "type": "post",
                            "title": "Old Post",
                            "ref": "blog/published-post.md",
                            "parent_id": "root",
                            "order": 10,
                            "visibility": "public",
                            "status": "trashed",
                        },
                        {
                            "id": "new_post",
                            "type": "post",
                            "title": "Published Post",
                            "ref": "blog/published-post.md",
                            "parent_id": "root",
                            "order": 20,
                            "visibility": "public",
                            "status": "active",
                        },
                    ]
                ),
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                self.assertFalse(
                    public_site.is_blog_route_trashed("alice", "published-post")
                )
                self.assertEqual(
                    [post.route for post in public_site.load_blog_posts("alice")],
                    ["published-post"],
                )
                self.assertEqual(
                    public_site.load_blog_post("alice", "published-post").title,
                    "Published Post",
                )

    def test_position_public_library_node_places_anywhere_in_one_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            _write_yaml(
                profile / "public-library.yaml",
                _library_yaml(
                    [
                        {
                            "id": "folder_a",
                            "type": "folder",
                            "title": "Folder A",
                            "parent_id": "root",
                            "order": 10,
                        },
                        {
                            "id": "post_a",
                            "type": "post",
                            "title": "Post A",
                            "ref": "blog/post-a.md",
                            "parent_id": "root",
                            "order": 20,
                        },
                        {
                            "id": "post_b",
                            "type": "post",
                            "title": "Post B",
                            "ref": "blog/post-b.md",
                            "parent_id": "root",
                            "order": 30,
                        },
                        {
                            "id": "post_c",
                            "type": "post",
                            "title": "Post C",
                            "ref": "blog/post-c.md",
                            "parent_id": "root",
                            "order": 40,
                        },
                        {
                            "id": "folder_b",
                            "type": "folder",
                            "title": "Folder B",
                            "parent_id": "root",
                            "order": 50,
                        },
                        {
                            "id": "post_parent",
                            "type": "post",
                            "title": "Post Parent",
                            "ref": "blog/post-parent.md",
                            "parent_id": "root",
                            "order": 60,
                        },
                        {
                            "id": "media_one",
                            "type": "media",
                            "title": "Media One",
                            "ref": "media/library/media-one.png",
                            "parent_id": "root",
                            "order": 70,
                        },
                        {
                            "id": "folder_child",
                            "type": "folder",
                            "title": "Folder Child",
                            "parent_id": "folder_a",
                            "order": 10,
                        },
                        {
                            "id": "trashed_post",
                            "type": "post",
                            "title": "Trashed Post",
                            "ref": "blog/trashed-post.md",
                            "parent_id": "root",
                            "order": 80,
                            "status": "trashed",
                        },
                    ]
                ),
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                public_site.position_public_library_node(
                    "alice",
                    "post_c",
                    before_node_id="post_a",
                )
                library = public_site.load_public_library("alice")
                self.assertEqual(
                    _library_order(library, "root"),
                    [
                        "folder_a",
                        "post_c",
                        "post_a",
                        "post_b",
                        "folder_b",
                        "post_parent",
                        "media_one",
                    ],
                )
                self.assertEqual(
                    [
                        node.order
                        for node in sorted(
                            (
                                node
                                for node in library.nodes
                                if node.parent_id == "root"
                                and node.status != "trashed"
                            ),
                            key=lambda node: node.order,
                        )
                    ],
                    [10, 20, 30, 40, 50, 60, 70],
                )

                public_site.position_public_library_node(
                    "alice",
                    "post_b",
                    after_node_id="folder_child",
                )
                library = public_site.load_public_library("alice")
                self.assertEqual(_library_order(library, "folder_a"), ["folder_child", "post_b"])
                self.assertEqual(
                    _library_order(library, "root"),
                    ["folder_a", "post_c", "post_a", "folder_b", "post_parent", "media_one"],
                )

                public_site.position_public_library_node(
                    "alice",
                    "folder_b",
                    parent_id="post_parent",
                )
                library = public_site.load_public_library("alice")
                self.assertEqual(_library_order(library, "post_parent"), ["folder_b"])

                public_site.reorder_public_library_node("alice", "post_a", "up")
                library = public_site.load_public_library("alice")
                self.assertEqual(
                    _library_order(library, "root")[:3],
                    ["folder_a", "post_a", "post_c"],
                )

    def test_position_public_library_node_rejects_invalid_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            _write_yaml(
                profile / "public-library.yaml",
                _library_yaml(
                    [
                        {
                            "id": "folder_a",
                            "type": "folder",
                            "title": "Folder A",
                            "parent_id": "root",
                            "order": 10,
                        },
                        {
                            "id": "folder_child",
                            "type": "folder",
                            "title": "Folder Child",
                            "parent_id": "folder_a",
                            "order": 10,
                        },
                        {
                            "id": "post_a",
                            "type": "post",
                            "title": "Post A",
                            "ref": "blog/post-a.md",
                            "parent_id": "root",
                            "order": 20,
                        },
                        {
                            "id": "media_one",
                            "type": "media",
                            "title": "Media One",
                            "ref": "media/library/media-one.png",
                            "parent_id": "root",
                            "order": 30,
                        },
                        {
                            "id": "trashed_post",
                            "type": "post",
                            "title": "Trashed Post",
                            "ref": "blog/trashed-post.md",
                            "parent_id": "root",
                            "order": 40,
                            "status": "trashed",
                        },
                    ]
                ),
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                with self.assertRaisesRegex(public_site.PublicSiteError, "root"):
                    public_site.position_public_library_node(
                        "alice",
                        "root",
                        parent_id="folder_a",
                    )
                with self.assertRaisesRegex(public_site.PublicSiteError, "descendant"):
                    public_site.position_public_library_node(
                        "alice",
                        "folder_a",
                        parent_id="folder_child",
                    )
                with self.assertRaisesRegex(public_site.PublicSiteError, "parent"):
                    public_site.position_public_library_node(
                        "alice",
                        "post_a",
                        parent_id="media_one",
                    )
                with self.assertRaisesRegex(public_site.PublicSiteError, "trash"):
                    public_site.position_public_library_node(
                        "alice",
                        "post_a",
                        before_node_id="trashed_post",
                    )
                with self.assertRaisesRegex(public_site.PublicSiteError, "itself"):
                    public_site.position_public_library_node(
                        "alice",
                        "post_a",
                        before_node_id="post_a",
                    )

    def test_media_purge_with_delete_files_rejects_active_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            media_dir = profile / "media" / "blog" / "published-post"
            media_dir.mkdir(parents=True)
            photo = media_dir / "photo.png"
            photo.write_bytes(b"png")
            _write_blog(
                profile / "blog" / "published-post.md",
                body="![Photo](media/blog/published-post/photo.png)",
            )
            _write_yaml(
                profile / "public-library.yaml",
                _library_yaml(
                    [
                        {
                            "id": "post_published",
                            "type": "post",
                            "title": "Published Post",
                            "ref": "blog/published-post.md",
                            "parent_id": "root",
                            "order": 10,
                            "visibility": "public",
                            "status": "active",
                        },
                        {
                            "id": "media_photo",
                            "type": "media",
                            "title": "photo.png",
                            "ref": "media/blog/published-post/photo.png",
                            "parent_id": "post_published",
                            "order": 20,
                            "visibility": "private",
                            "status": "trashed",
                            "owned": True,
                        },
                    ]
                ),
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                with self.assertRaisesRegex(
                    public_site.PublicSiteError,
                    "still referenced",
                ):
                    public_site.purge_public_library_node(
                        "alice",
                        "media_photo",
                        delete_files=True,
                    )

            self.assertTrue(photo.exists())

    def test_validate_rejects_invalid_library_nodes_and_escaped_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            _write_yaml(
                profile / "public-library.yaml",
                _library_yaml(
                    [
                        {
                            "id": "bad_type",
                            "type": "strange",
                            "title": "Bad Type",
                            "parent_id": "root",
                            "order": 10,
                            "visibility": "private",
                            "status": "active",
                        },
                        {
                            "id": "bad_status",
                            "type": "folder",
                            "title": "Bad Status",
                            "parent_id": "root",
                            "order": 20,
                            "visibility": "hidden",
                            "status": "gone",
                        },
                        {
                            "id": "bad_post_ref",
                            "type": "post",
                            "title": "Bad Ref",
                            "ref": "blog/../secret.md",
                            "parent_id": "root",
                            "order": 30,
                            "visibility": "public",
                            "status": "active",
                        },
                        {
                            "id": "bad_media_ref",
                            "type": "media",
                            "title": "Bad Media",
                            "ref": "media/../secret.png",
                            "parent_id": "root",
                            "order": 40,
                            "visibility": "private",
                            "status": "active",
                        },
                        {
                            "id": "orphan",
                            "type": "folder",
                            "title": "Orphan",
                            "parent_id": "missing_parent",
                            "order": 50,
                            "visibility": "private",
                            "status": "active",
                        },
                    ]
                ),
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = public_site.validate_public_layer("alice")

            errors = "\n".join(result.errors)
            self.assertIn("invalid type 'strange'", errors)
            self.assertIn("invalid status 'gone'", errors)
            self.assertIn("invalid visibility 'hidden'", errors)
            self.assertIn("post ref must be a safe", errors)
            self.assertIn("media ref must be a safe", errors)
            self.assertIn("parent_id does not exist", errors)

    def test_public_library_cli_tree_and_mutations_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            _write_yaml(
                profile / "public-library.yaml",
                _library_yaml(
                    [
                        {
                            "id": "post_published",
                            "type": "post",
                            "title": "Published Post",
                            "ref": "blog/published-post.md",
                            "parent_id": "root",
                            "order": 10,
                            "visibility": "public",
                            "status": "active",
                        }
                    ]
                ),
            )

            import nblane.cli as cli

            def run_cli(*args: str) -> str:
                out = io.StringIO()
                with (
                    patch.object(sys, "argv", ["nblane", *args]),
                    redirect_stdout(out),
                ):
                    cli.main()
                return out.getvalue()

            with (
                patch("nblane.core.public_site.profile_dir", lambda _n: profile),
                patch(
                    "nblane.commands.public._require_profile",
                    lambda _n: profile,
                ),
            ):
                tree_output = run_cli(
                    "public",
                    "library",
                    "tree",
                    "alice",
                    "--format",
                    "yaml",
                )
                tree = yaml.safe_load(tree_output)
                self.assertEqual(
                    tree["tree"][0]["children"][0]["id"],
                    "post_published",
                )

                trash_output = run_cli(
                    "public",
                    "library",
                    "trash",
                    "alice",
                    "post_published",
                )
                self.assertEqual(
                    yaml.safe_load(trash_output)["id"],
                    "post_published",
                )

                trash_tree_output = run_cli(
                    "public",
                    "library",
                    "tree",
                    "alice",
                    "--include-trash",
                    "--format",
                    "yaml",
                )
                trash_tree = yaml.safe_load(trash_tree_output)
                self.assertEqual(
                    trash_tree["trash"][0]["id"],
                    "post_published",
                )

                restore_output = run_cli(
                    "public",
                    "library",
                    "restore",
                    "alice",
                    "post_published",
                )
                self.assertEqual(
                    yaml.safe_load(restore_output)["status"],
                    "active",
                )


if __name__ == "__main__":
    unittest.main()
