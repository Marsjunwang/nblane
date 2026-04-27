"""Tests for public site files, validation, and static builds."""

from __future__ import annotations

import io
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
    body: str = "Public body.",
) -> None:
    meta = {
        "title": title,
        "date": "2026-04-26",
        "status": status,
        "tags": ["demo"],
        "summary": summary,
        "cover": "",
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
