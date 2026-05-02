"""Tests for public site files, validation, and static builds."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.commands import public as public_commands
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
    title: str,
    status: str,
    evidence: list[str] | None = None,
    summary: str = "Short summary",
    cover: str = "",
    body: str = "Public body.",
) -> None:
    meta = {
        "title": title,
        "date": "2026-04-26",
        "status": status,
        "tags": ["demo"],
        "summary": summary,
        "cover": cover,
        "related_evidence": evidence or [],
        "related_kanban": [],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
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


def _make_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    profile.mkdir(parents=True)
    (profile / "SKILL.md").write_text(
        "PRIVATE_SKILL_SECRET",
        encoding="utf-8",
    )
    (profile / "kanban.md").write_text(
        "PRIVATE_KANBAN_SECRET",
        encoding="utf-8",
    )
    (profile / "agent-profile.yaml").write_text(
        "PRIVATE_AGENT_SECRET",
        encoding="utf-8",
    )
    _write_yaml(
        profile / "evidence-pool.yaml",
        {
            "profile": name,
            "updated": "2026-04-26",
            "evidence_entries": [
                {
                    "id": "ev_public",
                    "type": "project",
                    "title": "Public Evidence",
                    "summary": "Verified public fact",
                }
            ],
        },
    )
    _write_yaml(
        profile / "skill-tree.yaml",
        {
            "profile": name,
            "nodes": [
                {
                    "id": "real_robot_ops",
                    "status": "solid",
                    "evidence_refs": ["ev_public"],
                }
            ],
        },
    )
    _write_yaml(
        profile / "public-profile.yaml",
        {
            "profile": name,
            "visibility": "public",
            "public_name": "Alice",
            "headline": "Robotics engineer",
            "avatar": "",
            "bio_short": "Builds real robot systems.",
            "contacts": {
                "wechat": "alice-wechat",
                "github": "github.com/alice",
            },
            "featured": {
                "projects": ["demo_project"],
                "outputs": ["demo_output"],
                "posts": ["published-post"],
            },
        },
    )
    _write_yaml(
        profile / "resume-source.yaml",
        {
            "profile": name,
            "visibility": "public",
            "basics": {
                "name": "Alice",
                "title": "Robotics Engineer",
                "email": "alice@example.com",
            },
            "summary": "Works on embodied AI.",
            "skills": ["VLA", "ROS 2"],
            "experiences": [
                {
                    "role": "Engineer",
                    "company": "Lab",
                    "start": "2025",
                    "end": "present",
                    "bullets": ["Built a public demo."],
                }
            ],
            "projects": [],
            "outputs": [],
            "education": [],
        },
    )
    _write_yaml(
        profile / "projects.yaml",
        {
            "projects": [
                {
                    "id": "demo_project",
                    "title": "Demo Project",
                    "status": "published",
                    "featured": True,
                    "summary": "A public project.",
                    "evidence_refs": ["ev_public"],
                    "links": {"demo": "https://example.com/demo"},
                }
            ]
        },
    )
    _write_yaml(
        profile / "outputs.yaml",
        {
            "outputs": [
                {
                    "id": "demo_output",
                    "type": "paper",
                    "title": "Demo Output",
                    "status": "published",
                    "year": "2026",
                    "evidence_refs": ["ev_public"],
                    "links": {"paper": "https://example.com/paper"},
                }
            ]
        },
    )
    _write_blog(
        profile / "blog" / "published-post.md",
        title="Published Post",
        status="published",
        evidence=["ev_public"],
        body="Published body without secrets.",
    )
    _write_blog(
        profile / "blog" / "draft-post.md",
        title="Draft Post",
        status="draft",
        evidence=["missing_draft_ref"],
        body="Draft body.",
    )
    return profile


class TestPublicSite(unittest.TestCase):
    """Public site behavior."""

    def test_init_public_layer_is_idempotent(self) -> None:
        """Init creates missing files and does not overwrite existing ones."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "alice"
            profile.mkdir()
            existing = profile / "public-profile.yaml"
            existing.write_text("custom: true\n", encoding="utf-8")

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                created = public_site.init_public_layer("alice")
                second = public_site.init_public_layer("alice")

            self.assertTrue(created)
            self.assertEqual(second, [])
            self.assertEqual(
                existing.read_text(encoding="utf-8"),
                "custom: true\n",
            )
            self.assertTrue((profile / "resume-source.yaml").exists())
            self.assertTrue((profile / "blog" / ".gitkeep").exists())

    def test_validate_rejects_publish_refs_and_media_escape(self) -> None:
        """Unknown public refs and escaped media paths fail validation."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            data = yaml.safe_load(
                (profile / "public-profile.yaml").read_text(
                    encoding="utf-8"
                )
            )
            data["avatar"] = "../secret.jpg"
            _write_yaml(profile / "public-profile.yaml", data)
            projects = yaml.safe_load(
                (profile / "projects.yaml").read_text(encoding="utf-8")
            )
            projects["projects"][0]["evidence_refs"] = ["missing"]
            _write_yaml(profile / "projects.yaml", projects)

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = public_site.validate_public_layer("alice")

            joined = "\n".join(result.errors)
            self.assertIn("media path must stay under", joined)
            self.assertIn("unknown evidence ref 'missing'", joined)

    def test_build_filters_drafts_and_excludes_private_files(self) -> None:
        """Default build publishes only public layer content."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out = root / "dist"

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = public_site.build_public_site(
                    "alice",
                    out_dir=out,
                )

            self.assertEqual(result.output_dir, out.resolve())
            self.assertTrue((out / "index.html").exists())
            self.assertTrue((out / "blog" / "index.html").exists())
            self.assertTrue(
                (out / "blog" / "published-post" / "index.html").exists()
            )
            self.assertFalse(
                (out / "blog" / "draft-post" / "index.html").exists()
            )
            self.assertTrue((out / "resume" / "index.html").exists())
            self.assertTrue(
                (out / "projects" / "demo_project" / "index.html").exists()
            )
            self.assertTrue(
                (out / "outputs" / "demo_output" / "index.html").exists()
            )

            home = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("Content Index", home)
            self.assertIn('href="/blog/"', home)
            self.assertIn('href="/projects/"', home)
            self.assertIn('href="/outputs/"', home)
            self.assertIn('href="/resume/"', home)
            self.assertIn('href="mailto:alice@example.com"', home)
            self.assertIn('href="https://github.com/alice"', home)
            self.assertIn("Email: alice@example.com", home)
            self.assertIn("<span class=\"pill\">WeChat: alice-wechat</span>", home)
            self.assertIn("GitHub: github.com/alice", home)
            self.assertIn("Published Post", home)
            self.assertIn("Demo Project", home)
            self.assertIn("Demo Output", home)
            self.assertNotIn("Published body without secrets.", home)
            self.assertNotIn("A public project.", home)

            project_detail = (
                out / "projects" / "demo_project" / "index.html"
            ).read_text(encoding="utf-8")
            self.assertIn("Verified public fact", project_detail)
            self.assertIn("real_robot_ops", project_detail)
            output_detail = (
                out / "outputs" / "demo_output" / "index.html"
            ).read_text(encoding="utf-8")
            self.assertIn("Verified public fact", output_detail)

            all_html = "\n".join(
                p.read_text(encoding="utf-8")
                for p in out.rglob("*.html")
            )
            self.assertIn("Published body without secrets.", all_html)
            self.assertNotIn("Draft body.", all_html)
            self.assertNotIn("PRIVATE_SKILL_SECRET", all_html)
            self.assertNotIn("PRIVATE_KANBAN_SECRET", all_html)
            self.assertNotIn("PRIVATE_AGENT_SECRET", all_html)
            self.assertNotIn("related_evidence", all_html)

    def test_include_drafts_builds_preview_content(self) -> None:
        """Preview builds may include draft blog posts and projects."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            draft = profile / "blog" / "draft-post.md"
            _write_blog(
                draft,
                title="Draft Post",
                status="draft",
                evidence=[],
                body="Draft preview body.",
            )
            projects = yaml.safe_load(
                (profile / "projects.yaml").read_text(encoding="utf-8")
            )
            projects["projects"].append(
                {
                    "id": "draft_project",
                    "title": "Draft Project",
                    "status": "draft",
                    "summary": "Draft project summary.",
                    "evidence_refs": ["ev_public"],
                }
            )
            _write_yaml(profile / "projects.yaml", projects)

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                public_site.build_public_site(
                    "alice",
                    out_dir=root / "preview",
                    include_drafts=True,
                )

            self.assertTrue(
                (root / "preview" / "blog" / "draft-post" / "index.html").exists()
            )
            self.assertTrue(
                (
                    root
                    / "preview"
                    / "projects"
                    / "draft_project"
                    / "index.html"
                ).exists()
            )

    def test_home_renders_and_copies_avatar_media(self) -> None:
        """A configured public avatar appears in the generated homepage."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            media = profile / "media" / "avatar.jpg"
            media.parent.mkdir(parents=True, exist_ok=True)
            media.write_bytes(b"fake image")
            data = yaml.safe_load(
                (profile / "public-profile.yaml").read_text(
                    encoding="utf-8"
                )
            )
            data["avatar"] = "media/avatar.jpg"
            _write_yaml(profile / "public-profile.yaml", data)

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                public_site.build_public_site("alice", out_dir=root / "dist")

            home = (root / "dist" / "index.html").read_text(encoding="utf-8")
            self.assertIn('class="hero-portrait"', home)
            self.assertIn('src="/media/avatar.jpg"', home)
            self.assertTrue((root / "dist" / "media" / "avatar.jpg").exists())

    def test_preview_uses_overrides_and_inlines_media_without_writes(self) -> None:
        """Live preview renders unsaved fields and media in memory."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            original_profile = (profile / "public-profile.yaml").read_text(
                encoding="utf-8"
            )
            override = {
                "visibility": "private",
                "public_name": "Preview Alice",
                "headline": "Unsaved headline",
                "bio_short": "Unsaved short bio",
                "avatar": "media/avatar.png",
                "contacts": {
                    "email": "preview@example.com",
                    "wechat": "preview-wechat",
                    "github": "https://example.com/preview",
                },
            }

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                preview = public_site.render_public_site_preview(
                    "alice",
                    public_profile_override=override,
                    media_overrides={
                        "media/avatar.png": b"preview image bytes",
                    },
                )

            home = preview.pages["index.html"]
            self.assertIn("Preview Alice", home)
            self.assertIn("Unsaved headline", home)
            self.assertIn("Unsaved short bio", home)
            self.assertIn("mailto:preview@example.com", home)
            self.assertIn("Email: preview@example.com", home)
            self.assertIn("WeChat: preview-wechat", home)
            self.assertIn("GitHub: example.com/preview", home)
            self.assertIn("data:image/png;base64,", home)
            self.assertNotIn('src="/media/avatar.png"', home)
            self.assertIn("projects/demo_project/index.html", preview.pages)
            self.assertIn("outputs/demo_output/index.html", preview.pages)
            self.assertIn("blog/published-post/index.html", preview.pages)
            self.assertIn("resume/index.html", preview.pages)
            self.assertFalse((profile / "media" / "avatar.png").exists())
            self.assertFalse((root / "dist").exists())
            self.assertEqual(
                (profile / "public-profile.yaml").read_text(encoding="utf-8"),
                original_profile,
            )

    def test_preview_allows_private_profile_but_build_rejects_it(self) -> None:
        """Preview can show private profiles while public builds stay strict."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            data = yaml.safe_load(
                (profile / "public-profile.yaml").read_text(
                    encoding="utf-8"
                )
            )
            data["visibility"] = "private"
            _write_yaml(profile / "public-profile.yaml", data)

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                preview = public_site.render_public_site_preview("alice")
                with self.assertRaises(public_site.PublicSiteError):
                    public_site.build_public_site(
                        "alice",
                        out_dir=root / "dist",
                    )

            self.assertIn("index.html", preview.pages)
            self.assertIn("Alice", preview.pages["index.html"])

    def test_preview_excludes_private_raw_profile_files(self) -> None:
        """Preview HTML never leaks raw private profile files."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                preview = public_site.render_public_site_preview("alice")

            all_html = "\n".join(preview.pages.values())
            self.assertNotIn("PRIVATE_SKILL_SECRET", all_html)
            self.assertNotIn("PRIVATE_KANBAN_SECRET", all_html)
            self.assertNotIn("PRIVATE_AGENT_SECRET", all_html)

    def test_draft_blog_blank_summary_does_not_block_build(self) -> None:
        """Draft posts may be rough without blocking public builds."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            _write_blog(
                profile / "blog" / "rough-draft.md",
                title="Rough Draft",
                status="draft",
                summary="",
                evidence=[],
                body="Draft body.",
            )
            _write_blog(
                profile / "blog" / "draft-post.md",
                title="Draft Post",
                status="draft",
                evidence=[],
                body="Draft body.",
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = public_site.validate_public_layer("alice")
                preview = public_site.validate_public_layer(
                    "alice",
                    include_drafts=True,
                )
                public_site.build_public_site("alice", out_dir=root / "dist")
                public_site.build_public_site(
                    "alice",
                    out_dir=root / "preview",
                    include_drafts=True,
                )

            self.assertEqual(result.errors, [])
            self.assertEqual(preview.errors, [])
            self.assertFalse(
                (root / "dist" / "blog" / "rough-draft" / "index.html").exists()
            )
            self.assertTrue(
                (
                    root
                    / "preview"
                    / "blog"
                    / "rough-draft"
                    / "index.html"
                ).exists()
            )

    def test_base64_blog_image_is_extracted_to_media(self) -> None:
        """Rich-editor data URI images are saved as local blog media."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            body = "Before\n\n![demo](data:image/png;base64,aGVsbG8=)\n"

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                rewritten, changed = public_site.extract_blog_base64_images(
                    "alice",
                    "draft-post",
                    body,
                )

            self.assertEqual(len(changed), 1)
            self.assertTrue(changed[0].exists())
            self.assertIn("media/blog/draft-post/img-", rewritten)
            self.assertNotIn("data:image/png;base64", rewritten)

    def test_blog_body_media_and_video_are_built(self) -> None:
        """Body images and local videos are copied and rendered."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            media_dir = profile / "media" / "blog" / "published-post"
            media_dir.mkdir(parents=True)
            (media_dir / "photo.png").write_bytes(b"fake image")
            (media_dir / "clip.mp4").write_bytes(b"fake video")
            _write_blog(
                profile / "blog" / "published-post.md",
                title="Published Post",
                status="published",
                evidence=["ev_public"],
                body=(
                    "Intro.\n\n"
                    "![Photo](media/blog/published-post/photo.png)\n\n"
                    "::video[Clip](media/blog/published-post/clip.mp4)\n"
                ),
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                public_site.build_public_site("alice", out_dir=root / "dist")

            post_html = (
                root / "dist" / "blog" / "published-post" / "index.html"
            ).read_text(encoding="utf-8")
            self.assertIn("media/blog/published-post/photo.png", post_html)
            self.assertIn('<video class="media-video"', post_html)
            self.assertIn("media/blog/published-post/clip.mp4", post_html)
            self.assertTrue(
                (root / "dist" / "media" / "blog" / "published-post" / "photo.png").exists()
            )
            self.assertTrue(
                (root / "dist" / "media" / "blog" / "published-post" / "clip.mp4").exists()
            )

    def test_blog_math_formula_renders_with_mathjax(self) -> None:
        """Blog posts with LaTeX formulas keep delimiters and load MathJax."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            body = (
                "Inline formula $E=mc^2$ stays readable.\n\n"
                "$$\n"
                "\n"
                "J(\\theta)=\\sum_t r_t\n"
                "\n"
                "$$\n"
            )
            _write_blog(
                profile / "blog" / "published-post.md",
                title="Math Post",
                status="published",
                evidence=["ev_public"],
                body=body,
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                public_site.build_public_site("alice", out_dir=root / "dist")

            post_html = (
                root / "dist" / "blog" / "published-post" / "index.html"
            ).read_text(encoding="utf-8")
            self.assertIn("window.MathJax", post_html)
            self.assertIn("tex-svg.js", post_html)
            self.assertIn('<span class="math-inline">\\(E=mc^2\\)</span>', post_html)
            self.assertIn('<div class="math-display">\\[', post_html)
            self.assertIn("J(\\theta)=\\sum_t r_t", post_html)
            self.assertNotIn("<p>$$</p>", post_html)

    def test_markdown_contains_math_ignores_fenced_code(self) -> None:
        """Math detection drives the formula-safe editor mode."""
        self.assertTrue(public_site.markdown_contains_math("Use $x_t = Ax_{t-1}$"))
        self.assertTrue(public_site.markdown_contains_math("$$\na^2+b^2=c^2\n$$"))
        self.assertFalse(
            public_site.markdown_contains_math("```python\nprice = '$5'\n```")
        )
        self.assertFalse(public_site.markdown_contains_math("Budget is $5 and $6."))

    def test_publish_validation_rejects_unsafe_video_path(self) -> None:
        """Publish checks reject local video paths outside media/."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            text = (
                "---\n"
                + yaml.dump(
                    {
                        "title": "Bad Video",
                        "date": "2026-04-26",
                        "status": "published",
                        "tags": [],
                        "summary": "Bad video",
                        "cover": "",
                        "related_evidence": [],
                        "related_kanban": [],
                    }
                )
                + "---\n\n"
                + "::video[bad](../secret.mp4)\n"
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = public_site.validate_blog_text_for_publish(
                    "alice",
                    profile / "blog" / "bad-video.md",
                    text,
                )

            self.assertTrue(result.errors)
            self.assertIn("local video must stay under", "\n".join(result.errors))

    def test_publish_blog_post_api_publishes_by_slug(self) -> None:
        """The public API publishes a draft by slug and returns its path."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            _write_blog(
                profile / "blog" / "draft-post.md",
                title="Draft Post",
                status="draft",
                evidence=[],
                body="Draft body.",
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                path = public_site.publish_blog_post("alice", "draft-post")
                post = public_site.parse_blog_post(path)

            self.assertEqual(path, profile / "blog" / "draft-post.md")
            self.assertEqual(post.status, "published")

    def test_publish_blog_post_accepts_legacy_path_input(self) -> None:
        """Legacy Path callers get a clear slug-compatible publish path."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            post_path = profile / "blog" / "draft-post.md"
            _write_blog(
                post_path,
                title="Draft Post",
                status="draft",
                evidence=[],
                body="Draft body.",
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                path = public_site.publish_blog_post("alice", post_path)
                post = public_site.parse_blog_post(path)

            self.assertEqual(path, post_path)
            self.assertEqual(post.status, "published")

    def test_public_blog_publish_cli_handler_uses_slug_api(self) -> None:
        """CLI publish delegates to the slug API instead of a Path overload."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            _write_blog(
                profile / "blog" / "draft-post.md",
                title="Draft Post",
                status="draft",
                evidence=[],
                body="Draft body.",
            )
            out = io.StringIO()

            with (
                patch("nblane.core.public_site.profile_dir", lambda _n: profile),
                patch("nblane.commands.public._require_profile", lambda _n: profile),
                redirect_stdout(out),
            ):
                public_commands.cmd_public_blog_publish(
                    "alice",
                    slug="draft-post",
                )

            post = public_site.parse_blog_post(profile / "blog" / "draft-post.md")
            self.assertEqual(post.status, "published")
            self.assertIn("Published blog post:", out.getvalue())
            self.assertIn("draft-post.md", out.getvalue())

    def test_unsafe_link_schemes_are_rejected_and_sanitized(self) -> None:
        """Unsafe URL schemes fail validation and are stripped from HTML."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            public_profile = yaml.safe_load(
                (profile / "public-profile.yaml").read_text(encoding="utf-8")
            )
            public_profile["contacts"]["website"] = "javascript:alert(1)"
            _write_yaml(profile / "public-profile.yaml", public_profile)

            projects = yaml.safe_load(
                (profile / "projects.yaml").read_text(encoding="utf-8")
            )
            projects["projects"][0]["links"]["bad"] = "data:text/html,boom"
            _write_yaml(profile / "projects.yaml", projects)
            _write_blog(
                profile / "blog" / "published-post.md",
                title="Published Post",
                status="published",
                evidence=["ev_public"],
                body=(
                    "[unsafe](javascript:alert)\n\n"
                    '<a href="data:text/html,boom">raw unsafe</a>\n'
                ),
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = public_site.validate_public_layer("alice")
                rendered = public_site.render_public_site_pages("alice")

            errors = "\n".join(result.errors)
            self.assertIn("unsafe URL scheme 'javascript'", errors)
            self.assertIn("unsafe URL scheme 'data'", errors)
            all_html = "\n".join(rendered.pages.values())
            self.assertNotIn('href="javascript:', all_html)
            self.assertNotIn('href="data:', all_html)
            self.assertNotIn('src="data:', all_html)

    def test_build_writes_seo_tags_and_base_url_sitemap(self) -> None:
        """Build base_url feeds canonical URLs, OpenGraph, and sitemap."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            out = root / "dist"
            base_url = "https://alice.example/site"

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                public_site.build_public_site(
                    "alice",
                    out_dir=out,
                    base_url=base_url,
                )

            home = (out / "index.html").read_text(encoding="utf-8")
            post = (
                out / "blog" / "published-post" / "index.html"
            ).read_text(encoding="utf-8")
            sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")
            robots = (out / "robots.txt").read_text(encoding="utf-8")

            self.assertIn(
                '<link rel="canonical" href="https://alice.example/site/">',
                home,
            )
            self.assertIn('href="/site/assets/site.css"', home)
            self.assertIn('href="/site/blog/"', home)
            self.assertIn(
                '<meta property="og:url" content="https://alice.example/site/">',
                home,
            )
            self.assertIn('<meta property="og:title" content="Home · Alice">', home)
            self.assertIn('<meta name="twitter:card" content="summary">', home)
            self.assertIn(
                '<link rel="canonical" href="https://alice.example/site/blog/published-post/">',
                post,
            )
            self.assertIn('<meta property="og:type" content="article">', post)
            self.assertIn(
                "<loc>https://alice.example/site/blog/published-post/</loc>",
                sitemap,
            )
            self.assertIn(
                "Sitemap: https://alice.example/site/sitemap.xml",
                robots,
            )

    def test_add_blog_media_appends_and_updates_cover(self) -> None:
        """CLI/Web media helper copies media and updates the blog document."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            source = root / "cover.png"
            source.write_bytes(b"image bytes")

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = public_site.add_blog_media(
                    "alice",
                    "draft-post",
                    source=source,
                    kind="image",
                    alt="Cover",
                    cover=True,
                    append=True,
                )
                post = public_site.parse_blog_post(
                    profile / "blog" / "draft-post.md"
                )

            self.assertTrue(result.path.exists())
            self.assertIn("![Cover](", result.snippet)
            self.assertEqual(post.meta["cover"], result.relative_path)
            self.assertIn(result.snippet, post.body)

    def test_delete_blog_media_removes_only_unreferenced_local_file(self) -> None:
        """Blog media deletion refuses referenced media and removes unused files."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            media_dir = profile / "media" / "blog" / "draft-post"
            media_dir.mkdir(parents=True)
            unused = media_dir / "unused.png"
            used = media_dir / "used.png"
            cover = media_dir / "cover.png"
            unused.write_bytes(b"unused image")
            used.write_bytes(b"used image")
            cover.write_bytes(b"cover image")
            _write_blog(
                profile / "blog" / "draft-post.md",
                title="Draft Post",
                status="draft",
                cover="media/blog/draft-post/cover.png",
                body="![Used](media/blog/draft-post/used.png)",
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                deleted = public_site.delete_blog_media(
                    "alice",
                    "draft-post",
                    "media/blog/draft-post/unused.png",
                )
                with self.assertRaises(public_site.PublicSiteError):
                    public_site.delete_blog_media(
                        "alice",
                        "draft-post",
                        "media/blog/draft-post/used.png",
                    )
                with self.assertRaises(public_site.PublicSiteError):
                    public_site.delete_blog_media(
                        "alice",
                        "draft-post",
                        "media/blog/draft-post/cover.png",
                    )
                with self.assertRaises(public_site.PublicSiteError):
                    public_site.delete_blog_media(
                        "alice",
                        "draft-post",
                        "media/avatar.png",
                    )

            self.assertEqual(deleted.name, "unused.png")
            self.assertFalse(unused.exists())
            self.assertTrue(used.exists())
            self.assertTrue(cover.exists())

    def test_convert_blog_media_video_creates_h264_copy(self) -> None:
        """Video conversion creates a sibling MP4 and keeps the original."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            media_dir = profile / "media" / "blog" / "draft-post"
            media_dir.mkdir(parents=True)
            video = media_dir / "clip.mp4"
            video.write_bytes(b"original video")

            def fake_run(cmd, **_kwargs):
                Path(cmd[-1]).write_bytes(b"converted video")
                return type(
                    "Completed",
                    (),
                    {"returncode": 0, "stderr": "", "stdout": ""},
                )()

            with (
                patch("nblane.core.public_site.profile_dir", lambda _n: profile),
                patch("nblane.core.public_site.shutil.which", return_value="/usr/bin/ffmpeg"),
                patch("nblane.core.public_site.subprocess.run", side_effect=fake_run),
            ):
                result = public_site.convert_blog_media_video(
                    "alice",
                    "draft-post",
                    "media/blog/draft-post/clip.mp4",
                )

            self.assertTrue(video.exists())
            self.assertTrue(result.path.exists())
            self.assertEqual(result.path.read_bytes(), b"converted video")
            self.assertTrue(result.relative_path.endswith("-h264.mp4"))
            self.assertIn("::video[](", result.snippet)

    def test_blog_media_library_rows_include_inline_image_preview(self) -> None:
        """Editor media rows include image previews and skip large video inlining."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            media_dir = profile / "media" / "blog" / "draft-post"
            media_dir.mkdir(parents=True)
            image = media_dir / "cover.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\npreview")
            video = media_dir / "clip.mp4"
            video.write_bytes(
                b"0" * (public_site.BLOG_PREVIEW_VIDEO_INLINE_MAX_BYTES + 1)
            )
            with patch(
                "nblane.core.public_site._ffprobe_video_stream",
                return_value={
                    "codec_name": "mpeg4",
                    "codec_tag_string": "mp4v",
                    "profile": "Simple Profile",
                },
            ):
                rows = public_site.blog_media_library_rows(
                    profile,
                    "draft-post",
                    {"cover": "media/blog/draft-post/cover.png"},
                    "![Cover](media/blog/draft-post/cover.png)",
                )

            by_name = {row["name"]: row for row in rows}
            self.assertTrue(
                by_name["cover.png"]["preview_src"].startswith(
                    "data:image/png;base64,"
                )
            )
            self.assertEqual(by_name["cover.png"]["preview_mime"], "image/png")
            self.assertIn("preview_width", by_name["cover.png"])
            self.assertIn("preview_height", by_name["cover.png"])
            self.assertIn("original_size_kb", by_name["cover.png"])
            self.assertTrue(by_name["cover.png"]["full_preview_available"])
            self.assertTrue(by_name["cover.png"]["referenced"])
            self.assertEqual(by_name["clip.mp4"]["preview_src"], "")
            self.assertEqual(by_name["clip.mp4"]["preview_mime"], "video/mp4")
            self.assertTrue(by_name["clip.mp4"]["full_preview_available"])
            self.assertFalse(by_name["clip.mp4"]["video_browser_compatible"])
            self.assertTrue(by_name["clip.mp4"]["needs_video_conversion"])
            self.assertEqual(by_name["clip.mp4"]["video_codec"], "mpeg4")

    def test_blog_media_library_marks_h264_video_compatible(self) -> None:
        """H.264 MP4 rows are marked browser-compatible."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            media_dir = profile / "media" / "blog" / "draft-post"
            media_dir.mkdir(parents=True)
            video = media_dir / "clip.mp4"
            video.write_bytes(b"0" * 64)
            with patch(
                "nblane.core.public_site._ffprobe_video_stream",
                return_value={
                    "codec_name": "h264",
                    "codec_tag_string": "avc1",
                    "profile": "High",
                },
            ):
                rows = public_site.blog_media_library_rows(
                    profile,
                    "draft-post",
                    {},
                    "::video[](media/blog/draft-post/clip.mp4)",
                )

            self.assertTrue(rows[0]["video_browser_compatible"])
            self.assertFalse(rows[0]["needs_video_conversion"])

    def test_blog_visual_candidate_rows_are_unsaved_previews(self) -> None:
        """Visual candidates can preview before they are persisted to media."""
        from nblane.core import visual_generation

        prompt = visual_generation.VisualPrompt(
            positive_prompt="positive",
            negative_prompt="negative",
            asset_type="cover",
            recommended_size="1536*864",
            rationale="test",
        )
        asset = visual_generation.GeneratedVisualAsset(
            data=b"\x89PNG\r\n\x1a\ncandidate",
            mime_type="image/png",
            extension="png",
            prompt=prompt,
            provider="dashscope_wan",
            model="wan2.7-image-pro",
        )

        rows = public_site.blog_visual_candidate_rows(
            "draft-post",
            [asset],
            asset_type="cover",
            alt="Candidate cover",
            caption="Candidate caption",
        )

        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["unsaved"])
        self.assertTrue(rows[0]["preview_src"].startswith("data:image/png;base64,"))
        self.assertIn("preview_width", rows[0])
        self.assertEqual(rows[0]["visual_kind"], "cover")
        self.assertIn("preview_height", rows[0])
        self.assertTrue(rows[0]["full_preview_available"])
        self.assertIn("media/blog/draft-post/generated-cover-", rows[0]["relative_path"])
        self.assertIn("![Candidate cover](", rows[0]["snippet"])

    def test_visual_block_comment_counts_as_blog_media_ref(self) -> None:
        """Visual block comments preserve generated visual semantics and media refs."""
        body = (
            '<!-- nblane:visual_block {"asset_type":"diagram",'
            '"visual_kind":"flowchart","src":"media/blog/draft-post/chart.png",'
            '"caption":"Flow"} -->'
        )

        refs = public_site._blog_body_media_refs(body)
        html = public_site._markdown_to_html(body)

        self.assertEqual(refs, ["media/blog/draft-post/chart.png"])
        self.assertIn('data-visual-kind="flowchart"', html)
        self.assertIn('src="/media/blog/draft-post/chart.png"', html)

    def test_visual_block_comment_renders_mermaid_without_src(self) -> None:
        """Diagram visual blocks without image assets render Mermaid runtime source."""
        body = (
            '<!-- nblane:visual_block {"asset_type":"diagram",'
            '"visual_kind":"flowchart","mermaid":"flowchart TD\\\\nA\\\\u002d\\\\u002d>B",'
            '"caption":"Flow"} -->'
        )

        html = public_site._markdown_to_html(body)

        self.assertIn('<pre class="mermaid">', html)
        self.assertIn("flowchart TD", html)
        self.assertIn("A--&gt;B", html)
        self.assertIn("<noscript><svg", html)
        self.assertNotIn("<script", html)
        self.assertIn('data-asset-type="diagram"', html)

    def test_visual_block_comment_renders_labeled_mermaid_edges(self) -> None:
        """Common Mermaid edge labels are preserved for the Mermaid runtime."""
        body = (
            '<!-- nblane:visual_block {"asset_type":"diagram",'
            '"visual_kind":"flowchart",'
            '"mermaid":"flowchart TD\\\\nA[Login] \\\\u002d\\\\u002d>|Yes| B[Home]",'
            '"caption":"Flow"} -->'
        )

        html = public_site._markdown_to_html(body)

        self.assertIn('<pre class="mermaid">', html)
        self.assertIn("A[Login] --&gt;|Yes| B[Home]", html)
        self.assertIn("<noscript><svg", html)

    def test_visual_block_comment_normalizes_single_line_mermaid_flowchart(self) -> None:
        """One-line LLM Mermaid output is normalized before runtime rendering."""
        body = (
            '<!-- nblane:visual_block {"asset_type":"diagram",'
            '"visual_kind":"flowchart",'
            '"mermaid":"flowchart TD A[用户输入账号密码] --> B{系统校验} '
            'B -->|校验成功| C[成功进入首页] B -->|校验失败| D[失败提示错误]",'
            '"caption":"Flow"} -->'
        )

        html = public_site._markdown_to_html(body)

        self.assertIn('<pre class="mermaid">', html)
        self.assertIn("flowchart TD\n  A[用户输入账号密码] --&gt; B{系统校验}", html)
        self.assertIn("B --&gt;|校验成功| C[成功进入首页]", html)
        self.assertIn("B --&gt;|校验失败| D[失败提示错误]", html)

    def test_blog_preview_page_includes_mermaid_runtime_when_needed(self) -> None:
        """Full public pages load Mermaid only when diagram blocks are present."""
        body = public_site._markdown_to_html(
            '<!-- nblane:visual_block {"asset_type":"diagram",'
            '"visual_kind":"flowchart","mermaid":"flowchart TD\\\\nA\\\\u002d\\\\u002d>B"} -->'
        )

        html = public_site._html_page(
            title="Diagram",
            body=body,
            public_profile={"name": "Test"},
            current="blog",
        )

        self.assertIn("mermaid@10.9.5", html)
        self.assertIn("mermaid.run", html)

    def test_public_mermaid_background_matches_editor_shell(self) -> None:
        """Public Mermaid containers use the same light surface as the editor."""
        css = public_site._site_css()

        self.assertIn(".prose pre.mermaid", css)
        self.assertIn("background: #f6f8f7", css)
        self.assertIn("border: 1px solid var(--line)", css)

    def test_video_directive_render_order_matches_markdown_order(self) -> None:
        """Public Markdown rendering keeps video directives in document order."""
        body = (
            "::video[first](https://example.com/a.mp4)\n\n"
            "Between\n\n"
            "::video[second](media/blog/post/b.mp4)\n\n"
            "::video[third](media/blog/post/c.mp4)"
        )

        html = public_site._markdown_to_html(body)

        self.assertLess(html.index("a.mp4"), html.index("Between"))
        self.assertLess(html.index("Between"), html.index("b.mp4"))
        self.assertLess(html.index("b.mp4"), html.index("c.mp4"))

    def test_ai_loading_comments_are_not_public_rendered(self) -> None:
        """Unaccepted inline AI candidates stay out of public previews."""
        body = (
            "Before\n\n"
            '<!-- nblane:ai_loading {"mode":"diagram","status":"candidate",'
            '"summary":"flowchart TD\\\\nA\\\\u002d\\\\u002d>B"} -->\n\n'
            "After"
        )

        html = public_site._markdown_to_html(body)

        self.assertIn("Before", html)
        self.assertIn("After", html)
        self.assertNotIn("ai_loading", html)
        self.assertNotIn("flowchart TD", html)

    def test_math_block_comment_renders_with_mathjax_wrapper(self) -> None:
        """AI math-block comments render through the existing math pipeline."""
        body = (
            '<!-- nblane:math_block {"latex":"x^2+y^2=z^2",'
            '"ai_generated":true,"accepted":false} -->'
        )
        html = public_site._markdown_to_html(body)

        self.assertTrue(public_site.markdown_contains_math(body))
        self.assertIn('class="math-display"', html)
        self.assertIn("x^2+y^2=z^2", html)

    def test_render_blog_post_preview_uses_unsaved_text_and_cover(self) -> None:
        """Single-post preview renders in-memory meta/body and does not write."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            media_dir = profile / "media" / "blog" / "draft-post"
            media_dir.mkdir(parents=True)
            (media_dir / "cover.png").write_bytes(b"\x89PNG\r\n\x1a\npreview")
            post_path = profile / "blog" / "draft-post.md"
            before = post_path.read_text(encoding="utf-8")
            meta = {
                "title": "Unsaved Title",
                "date": "2026-04-29",
                "status": "draft",
                "tags": ["preview"],
                "summary": "Unsaved summary",
                "cover": "media/blog/draft-post/cover.png",
                "related_evidence": [],
                "related_kanban": [],
            }

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                html = public_site.render_blog_post_preview(
                    "alice",
                    "draft-post",
                    meta,
                    "Unsaved **body**.",
                )

            self.assertIn("Unsaved Title", html)
            self.assertIn("Unsaved summary", html)
            self.assertIn("Unsaved", html)
            self.assertIn("data:image/png;base64", html)
            self.assertEqual(post_path.read_text(encoding="utf-8"), before)

    def test_render_blog_post_preview_fast_uses_smaller_image_payload(self) -> None:
        """Fast previews thumbnail images while full previews keep original bytes."""
        try:
            from PIL import Image
        except Exception:
            self.skipTest("Pillow is not installed")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            media_dir = profile / "media" / "blog" / "draft-post"
            media_dir.mkdir(parents=True)
            image_path = media_dir / "cover.jpg"
            image = Image.effect_noise((1600, 900), 96).convert("RGB")
            image.save(image_path, format="JPEG", quality=95)
            meta = {
                "title": "Preview Size",
                "date": "2026-04-29",
                "status": "draft",
                "tags": ["preview"],
                "summary": "Preview summary",
                "cover": "media/blog/draft-post/cover.jpg",
                "related_evidence": [],
                "related_kanban": [],
            }
            body = "![Cover](media/blog/draft-post/cover.jpg)"

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                fast_html = public_site.render_blog_post_preview(
                    "alice",
                    "draft-post",
                    meta,
                    body,
                    preview_quality="fast",
                )
                full_html = public_site.render_blog_post_preview(
                    "alice",
                    "draft-post",
                    meta,
                    body,
                    preview_quality="full",
                )

            self.assertIn("data:image/", fast_html)
            self.assertNotIn('src=""', fast_html)
            self.assertLess(len(fast_html), len(full_html))

    def test_blog_media_full_preview_payload_returns_one_full_item(self) -> None:
        """Full preview payloads are loaded on demand for a single media item."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            media_dir = profile / "media" / "blog" / "draft-post"
            media_dir.mkdir(parents=True)
            image = media_dir / "cover.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\nfull")

            payload = public_site.blog_media_full_preview_payload(
                profile,
                "media/blog/draft-post/cover.png",
                kind="image",
            )

            self.assertTrue(payload["full_preview_src"].startswith("data:image/png;base64,"))
            self.assertEqual(payload["full_preview_mime"], "image/png")
            self.assertTrue(payload["full_preview_available"])

    def test_render_blog_post_preview_full_inlines_large_video(self) -> None:
        """Full blog preview can play local videos that fast preview skips."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            media_dir = profile / "media" / "blog" / "draft-post"
            media_dir.mkdir(parents=True)
            video = media_dir / "clip.mp4"
            video.write_bytes(
                b"0" * (public_site.BLOG_PREVIEW_VIDEO_INLINE_MAX_BYTES + 1)
            )
            meta = {
                "title": "Video Preview",
                "date": "2026-04-29",
                "status": "draft",
                "tags": ["preview"],
                "summary": "Preview summary",
                "cover": "",
                "related_evidence": [],
                "related_kanban": [],
            }
            body = "::video[Clip](media/blog/draft-post/clip.mp4)"

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                fast_html = public_site.render_blog_post_preview(
                    "alice",
                    "draft-post",
                    meta,
                    body,
                    preview_quality="fast",
                )
                full_html = public_site.render_blog_post_preview(
                    "alice",
                    "draft-post",
                    meta,
                    body,
                    preview_quality="full",
                )
                detail = public_site.blog_media_full_preview_payload(
                    profile,
                    "media/blog/draft-post/clip.mp4",
                    kind="video",
                )

            self.assertIn('<video class="media-video"', fast_html)
            self.assertNotIn("data:video/mp4;base64", fast_html)
            self.assertIn("data:video/mp4;base64", full_html)
            self.assertTrue(detail["full_preview_src"].startswith("data:video/mp4;base64,"))
            self.assertEqual(detail["full_preview_mime"], "video/mp4")
            self.assertTrue(detail["full_preview_available"])

    def test_publish_blog_text_validates_before_writing(self) -> None:
        """Unsaved publish writes only after validation succeeds."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            post_path = profile / "blog" / "draft-post.md"
            before = post_path.read_text(encoding="utf-8")
            bad_meta = {
                "title": "Bad Publish",
                "date": "2026-04-29",
                "status": "draft",
                "tags": ["demo"],
                "summary": "",
                "cover": "",
                "related_evidence": ["missing_ref"],
                "related_kanban": [],
            }

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                with self.assertRaises(public_site.PublicSiteError):
                    public_site.publish_blog_text(
                        "alice",
                        "draft-post",
                        bad_meta,
                        "Ready body.",
                    )
            self.assertEqual(post_path.read_text(encoding="utf-8"), before)

            good_meta = dict(bad_meta)
            good_meta["summary"] = "Ready summary"
            good_meta["related_evidence"] = []
            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                path = public_site.publish_blog_text(
                    "alice",
                    "draft-post",
                    good_meta,
                    "Ready body.",
                )
                post = public_site.parse_blog_post(path)

            self.assertEqual(post.status, "published")
            self.assertEqual(post.title, "Bad Publish")
            self.assertIn("Ready body.", post.body)

    def test_generate_blog_visual_asset_unconfigured_is_clear(self) -> None:
        """Visual generation never creates fake media when no key is configured."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            before = sorted((profile / "media" / "blog").glob("**/*"))

            with (
                patch("nblane.core.public_site.profile_dir", lambda _n: profile),
                patch.dict("os.environ", {}, clear=True),
                patch("nblane.core.llm._API_KEY", ""),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "VISUAL_API_KEY / DASHSCOPE_API_KEY / LLM_API_KEY",
                ):
                    public_site.generate_blog_visual_asset(
                        "alice",
                        "draft-post",
                        "cover",
                        "Cover prompt",
                    )

            after = sorted((profile / "media" / "blog").glob("**/*"))
            self.assertEqual(after, before)

    def test_generate_blog_visual_asset_saves_generated_media_candidate(self) -> None:
        """Generated assets enter media/blog/<slug>/ without changing the post."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            post_path = profile / "blog" / "draft-post.md"
            before = post_path.read_text(encoding="utf-8")
            from nblane.core import visual_generation

            prompt = visual_generation.VisualPrompt(
                positive_prompt="positive",
                negative_prompt="negative",
                asset_type="cover",
                recommended_size="1536*864",
                rationale="test",
            )
            generated = visual_generation.GeneratedVisualAsset(
                data=b"\x89PNG\r\n\x1a\ngenerated",
                mime_type="image/png",
                extension="png",
                prompt=prompt,
                provider="dashscope_wan",
                model="wan2.7-image-pro",
            )

            with (
                patch("nblane.core.public_site.profile_dir", lambda _n: profile),
                patch(
                    "nblane.core.public_site.visual_generation.generate_visual_asset",
                    return_value=[generated],
                ),
            ):
                results = public_site.generate_blog_visual_asset(
                    "alice",
                    "draft-post",
                    "cover",
                    "Cover prompt",
                    alt="Generated cover",
                )

            self.assertEqual(len(results), 1)
            result = results[0]
            self.assertTrue(result.path.exists())
            self.assertIn("media/blog/draft-post/generated-cover-", result.relative_path)
            self.assertTrue(result.relative_path.endswith(".png"))
            self.assertIn("![Generated cover](", result.snippet)
            visual_rows = public_site.blog_visual_result_rows(
                profile,
                "draft-post",
                results,
                asset_type="cover",
                alt="Generated cover",
                caption="Candidate caption",
                meta={},
                body="",
            )
            self.assertEqual(len(visual_rows), 1)
            self.assertEqual(visual_rows[0]["asset_type"], "image")
            self.assertEqual(visual_rows[0]["visual_kind"], "cover")
            self.assertEqual(visual_rows[0]["alt"], "Generated cover")
            self.assertEqual(visual_rows[0]["caption"], "Candidate caption")
            self.assertIn("![Generated cover](", visual_rows[0]["snippet"])
            self.assertTrue(
                visual_rows[0]["preview_src"].startswith("data:image/png;base64,")
            )
            self.assertEqual(post_path.read_text(encoding="utf-8"), before)

    def test_blog_cover_renders_on_list_detail_and_social_tags(self) -> None:
        """Cover images are visible in blog cards, detail headers, and SEO tags."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            media_dir = profile / "media" / "blog" / "published-post"
            media_dir.mkdir(parents=True)
            (media_dir / "cover.png").write_bytes(b"\x89PNG\r\n\x1a\ncover")
            _write_blog(
                profile / "blog" / "published-post.md",
                title="Published Post",
                status="published",
                evidence=["ev_public"],
                cover="media/blog/published-post/cover.png",
                body="Published body.",
            )

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                public_site.build_public_site(
                    "alice",
                    out_dir=root / "dist",
                    base_url="https://alice.example/site",
                )

            blog_index = (root / "dist" / "blog" / "index.html").read_text(
                encoding="utf-8"
            )
            detail = (
                root / "dist" / "blog" / "published-post" / "index.html"
            ).read_text(encoding="utf-8")

            self.assertIn('class="item-cover"', blog_index)
            self.assertIn("media/blog/published-post/cover.png", blog_index)
            self.assertIn('class="blog-cover"', detail)
            self.assertIn(
                '<meta property="og:image" content="https://alice.example/site/media/blog/published-post/cover.png">',
                detail,
            )
            self.assertIn(
                '<meta name="twitter:image" content="https://alice.example/site/media/blog/published-post/cover.png">',
                detail,
            )
            self.assertTrue(
                (
                    root
                    / "dist"
                    / "media"
                    / "blog"
                    / "published-post"
                    / "cover.png"
                ).exists()
            )

    def test_blog_media_result_dict_is_json_safe(self) -> None:
        """Media API serialization exposes strings instead of Path objects."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            source = root / "photo.png"
            source.write_bytes(b"image bytes")

            with patch("nblane.core.public_site.profile_dir", lambda _n: profile):
                result = public_site.add_blog_media(
                    "alice",
                    "draft-post",
                    source=source,
                    kind="image",
                )

            json.dumps(result.to_dict())
            self.assertIsInstance(result.to_dict()["path"], str)

    def test_blog_candidate_from_evidence_does_not_write_post(self) -> None:
        """AI-style candidates stay in memory until the user confirms them."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            before = sorted(path.name for path in (profile / "blog").glob("*.md"))

            with (
                patch("nblane.core.public_site.profile_dir", lambda _n: profile),
                patch("nblane.core.public_site.llm.is_configured", return_value=False),
            ):
                candidate = public_site.blog_candidate_from_evidence(
                    "alice",
                    "ev_public",
                )

            after = sorted(path.name for path in (profile / "blog").glob("*.md"))
            self.assertEqual(after, before)
            self.assertEqual(candidate.title, "Public Evidence")
            self.assertIn("Verified public fact", candidate.body)
            self.assertEqual(candidate.related_evidence, ["ev_public"])

    def test_blog_candidate_from_title_is_complete_and_non_mutating(self) -> None:
        """Title-only generation returns full candidate fields in memory."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            before = sorted(path.name for path in (profile / "blog").glob("*.md"))

            with (
                patch("nblane.core.public_site.profile_dir", lambda _n: profile),
                patch("nblane.core.public_site.llm.is_configured", return_value=False),
            ):
                candidate = public_site.blog_candidate_from_title(
                    "alice",
                    "Robot learning notes",
                )

            after = sorted(path.name for path in (profile / "blog").glob("*.md"))
            self.assertEqual(after, before)
            self.assertEqual(candidate.title, "Robot learning notes")
            self.assertTrue(candidate.summary)
            self.assertTrue(candidate.tags)
            self.assertTrue(candidate.cover_prompt)
            self.assertTrue(candidate.warnings)
            self.assertIn("## Opening", candidate.body)

    def test_blocknote_component_bundle_is_available(self) -> None:
        """The packaged BlockNote Streamlit component has a built frontend."""
        from pathlib import Path

        import nblane.public_blog_editor_component as component
        from nblane.public_blog_editor_component import blocknote_component_available

        self.assertTrue(blocknote_component_available())
        static_index = (
            Path(component.__file__).parent
            / "frontend"
            / "static"
            / "index.html"
        )
        html = static_index.read_text(encoding="utf-8")
        self.assertIn("./assets/", html)
        self.assertNotIn('src="/assets/', html)
        self.assertNotIn('href="/assets/', html)
        bundle_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in (static_index.parent / "assets").glob("index-*.js")
        )
        self.assertIn("nb-shell", bundle_text)
        self.assertIn("save_post", bundle_text)
        self.assertIn("publish_request", bundle_text)


if __name__ == "__main__":
    unittest.main()
