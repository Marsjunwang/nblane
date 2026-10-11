"""Share cards: settings, HTML, render/cache, pack and API (Chromium mocked)."""

from __future__ import annotations

import io
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import public_site, social_cards
from nblane.core.paths import REPO_ROOT
from nblane.web_api import app

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"


def _fake_pdf(pages: int) -> bytes:
    import fitz

    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=810, height=1080)
    data = doc.tobytes()
    doc.close()
    return data


class SocialCardsTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        profile = self.root / "alice"
        shutil.copytree(TEMPLATE_DIR, profile)
        (profile / "public-profile.yaml").write_text(
            yaml.safe_dump({"profile": "alice", "site": {"base_url": "https://alice.example.com/"}}),
            encoding="utf-8",
        )
        for target in (
            "nblane.core.paths.PROFILES_DIR",
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, self.root)
            patcher.start()
            self.addCleanup(patcher.stop)
        for target in (
            "nblane.core.public_site.git_backup.record_change",
            "nblane.core.social_cards.git_backup.record_change",
        ):
            patcher = patch(target)
            patcher.start()
            self.addCleanup(patcher.stop)
        cache = patch("nblane.core.social_cards._cache_root", lambda profile: self.root / ".cache" / profile)
        cache.start()
        self.addCleanup(cache.stop)
        self.client = TestClient(app)

    def _post(self, body: str = "第一段。第二句。\n\n### " + "这是一个被写成小标题的长段落，" * 4 + "\n", status: str = "published") -> str:
        created = self.client.post(
            "/api/v1/profiles/alice/content/blog", json={"title": "随笔", "body": body}
        )
        self.assertEqual(created.status_code, 201, created.text)
        slug = created.json()["post"]["slug"]
        if status == "published":
            post = public_site.load_blog_post("alice", slug)
            meta = {**post.meta, "status": "published", "summary": "s"}
            public_site.save_blog_post("alice", slug, meta, post.body)
        return slug

    def test_settings_default_and_round_trip(self) -> None:
        defaults = social_cards.load_settings("alice", "x")
        self.assertEqual(defaults["theme"], "paper")
        self.assertEqual(defaults["end_card"], "thanks")
        self.assertEqual(defaults["site_url"], "alice.example.com")
        saved = social_cards.save_settings(
            "alice", "x", {"theme": "night", "end_card": "thanks_url", "site_url": "https://b.example/", "bogus": 1}
        )
        self.assertEqual(saved["site_url"], "b.example")
        self.assertNotIn("bogus", saved)
        self.assertEqual(social_cards.load_settings("alice", "x")["theme"], "night")
        # The site URL is remembered for the next post.
        self.assertEqual(social_cards.load_settings("alice", "other")["site_url"], "b.example")
        self.assertEqual(social_cards.normalize_settings({"theme": "neon"})["theme"], "paper")

    def test_html_respects_signature_and_end_card(self) -> None:
        slug = self._post()
        post = public_site.load_blog_post("alice", slug)
        page = social_cards.build_card_html("alice", post, {"signature": "none", "end_card": "none", "site_url": "a.b"})
        self.assertNotIn("a.b", page)
        self.assertNotIn("谢谢你读到这里", page)
        page = social_cards.build_card_html("alice", post, {"end_card": "thanks", "site_url": "a.b", "signature": "custom", "signature_text": "小王"})
        self.assertIn("谢谢你读到这里", page)
        self.assertIn("小王", page)
        self.assertNotIn('class="url"', page)
        page = social_cards.build_card_html("alice", post, {"end_card": "thanks_url", "site_url": "a.b"})
        self.assertIn('<span class="url">a.b</span>', page)
        # A long ### "heading" is body text on a card.
        self.assertNotIn("<h3>", page)

    def test_render_caches_and_warns_over_limit(self) -> None:
        slug = self._post()
        post = public_site.load_blog_post("alice", slug)
        with patch("nblane.core.resume_doc.print_html_to_pdf", return_value=_fake_pdf(20)) as printer:
            first = social_cards.render_cards("alice", post, {})
            again = social_cards.render_cards("alice", post, {})
        self.assertEqual(printer.call_count, 1)
        self.assertEqual(first, again)
        self.assertEqual(first["count"], 20)
        self.assertTrue(first["warnings"])
        png = social_cards.card_files("alice", first["key"])[0].read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertIsNone(social_cards.cache_dir("alice", "../etc"))

    def test_api_render_pack_and_draft_gate(self) -> None:
        draft = self._post(status="draft")
        settings = {"theme": "warm", "end_card": "thanks_url", "xhs_title": "标题", "xhs_body": "正文", "x_text": "推文"}
        blocked = self.client.post(
            "/api/v1/profiles/alice/content/social/render", json={"slug": draft, "settings": settings}
        )
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.json()["code"], "social_post_draft")

        slug = self._post()
        with patch("nblane.core.resume_doc.print_html_to_pdf", return_value=_fake_pdf(3)):
            rendered = self.client.post(
                "/api/v1/profiles/alice/content/social/render", json={"slug": slug, "settings": settings}
            )
        self.assertEqual(rendered.status_code, 200, rendered.text)
        data = rendered.json()
        self.assertEqual(data["count"], 3)
        image = self.client.get(data["images"][0])
        self.assertEqual(image.status_code, 200)
        self.assertEqual(image.headers["content-type"], "image/png")
        self.assertEqual(self.client.get(data["images"][0].replace("/1.png", "/9.png")).status_code, 404)

        info = self.client.get("/api/v1/profiles/alice/content/social", params={"slug": slug}).json()
        self.assertEqual(info["settings"]["theme"], "warm")
        self.assertTrue(info["published"])
        self.assertTrue(info["post_url"].startswith("https://alice.example.com/blog/"))

        pack = self.client.get(data["pack_url"])
        self.assertEqual(pack.status_code, 200)
        names = zipfile.ZipFile(io.BytesIO(pack.content)).namelist()
        self.assertEqual(names[:3], ["card-01.png", "card-02.png", "card-03.png"])
        x_text = zipfile.ZipFile(io.BytesIO(pack.content)).read("x.txt").decode()
        self.assertIn("推文", x_text)
        self.assertIn("https://alice.example.com/blog/", x_text)

    def test_x_copy_has_no_link_without_url_end_card(self) -> None:
        slug = self._post()
        with patch("nblane.core.resume_doc.print_html_to_pdf", return_value=_fake_pdf(2)):
            data = self.client.post(
                "/api/v1/profiles/alice/content/social/render",
                json={"slug": slug, "settings": {"end_card": "thanks", "x_text": "推文"}},
            ).json()
        x_text = zipfile.ZipFile(io.BytesIO(self.client.get(data["pack_url"]).content)).read("x.txt").decode()
        self.assertEqual(x_text.strip(), "推文")

    def test_render_unavailable_maps_to_503(self) -> None:
        from nblane.core import resume_doc

        slug = self._post()
        with patch("nblane.core.resume_doc.print_html_to_pdf", side_effect=resume_doc.ResumePdfUnavailable("no chromium")):
            response = self.client.post(
                "/api/v1/profiles/alice/content/social/render", json={"slug": slug, "settings": {}}
            )
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
