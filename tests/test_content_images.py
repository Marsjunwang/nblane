"""Image editing is reference-safe, recoverable and never overwrites originals."""
from __future__ import annotations

import base64
import io
from unittest.mock import patch

from PIL import Image

from test_content_ai import ContentAITestBase, _fake_asset
from nblane.core import content_images, visual_candidate_store, visual_generation
from nblane.web_api import jobs


def png_bytes() -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (640, 360), "white").save(stream, format="PNG", compress_level=0)
    return stream.getvalue()


class TestContentImages(ContentAITestBase):
    def _cover_provider(self, configured=True):
        from dataclasses import replace
        mock = super()._cover_provider(configured)
        mock.return_value = [replace(_fake_asset(), data=png_bytes())]
        return mock

    def reference(self, slug: str) -> str:
        data = png_bytes()
        url = "data:image/png;base64," + base64.b64encode(data).decode()
        self.assertGreater(len(url), 2000)
        result = self.client.post("/api/v1/profiles/alice/content/images/reference", json={"slug": slug, "data_url": url})
        self.assertEqual(result.status_code, 200, result.text)
        ref = result.json()["path"]
        self.assertEqual(visual_candidate_store.candidate_file_path("alice", ref).read_bytes(), data)
        return ref

    def run_image(self, slug: str, reference: str, **extra):
        return self._run_job("content-image", {"slug": slug, "mode": "edit", "instruction": "只调整背景，保留文字", "reference": reference, "target": {"kind": "media"}, **extra})["result"]

    def test_reference_survives_full_job_and_reload(self):
        provider = self._cover_provider()
        slug, md = self._create_post()
        before = md.read_bytes()
        ref = self.reference(slug)
        result = self.run_image(slug, ref)
        self.assertEqual(result["status"], "done", result)
        self.assertEqual(provider.call_args.args[0], "image_edit")
        self.assertEqual(provider.call_args.kwargs["size"], "1365*768")
        self.assertEqual(result["output_size"], "1365*768")
        self.assertEqual(base64.b64decode(provider.call_args.kwargs["reference_image"].split(",")[1]), png_bytes())
        restored = self.client.get("/api/v1/profiles/alice/content/images", params={"slug": slug}).json()["runs"]
        self.assertEqual(restored[0]["id"], result["id"])
        self.assertEqual(md.read_bytes(), before)

    def test_accept_copies_idempotently_and_keeps_reference_and_post(self):
        self._cover_provider()
        slug, md = self._create_post()
        before = md.read_bytes()
        run = self.run_image(slug, self.reference(slug))
        candidate = run["candidates"][0]["candidate_path"]
        payload = {"slug": slug, "run_id": run["id"], "candidate_path": candidate}
        first = self.client.post("/api/v1/profiles/alice/content/images/accept", json=payload)
        self.assertEqual(first.status_code, 200, first.text)
        again = self.client.post("/api/v1/profiles/alice/content/images/accept", json=payload)
        self.assertEqual(first.json(), again.json())
        self.assertTrue(visual_candidate_store.candidate_file_path("alice", candidate).exists())
        self.assertEqual(md.read_bytes(), before)

    def test_edit_prompt_preserves_text_and_ignores_article_theme(self):
        prompt = visual_generation.build_blog_visual_prompt("image_edit", "去黑边", title="技术文章", size="640*360")
        self.assertIn("Preserve all content", prompt.positive_prompt)
        self.assertNotIn("no letters", prompt.positive_prompt)
        self.assertNotIn("技术文章", prompt.positive_prompt)
        self.assertEqual(prompt.recommended_size, "640*360")

    def test_data_url_does_not_become_filesystem_path(self):
        value = "data:image/png;base64," + base64.b64encode(png_bytes()).decode()
        self.assertEqual(visual_generation._prepare_dashscope_media_url(value, model="test", api_key="test", base_url="https://example.test"), value)
        clean = jobs._validate_content_cover_input({"slug": "post", "reference_image": value})
        self.assertEqual(clean["reference_image"], value)

    def test_rejects_invalid_reference_and_cross_article_candidate(self):
        self._cover_provider()
        slug, _ = self._create_post()
        ref = self.reference(slug)
        response = self.client.post("/api/v1/profiles/alice/content/images/reference", json={"slug": slug, "data_url": "data:image/png;base64,YmFk"})
        self.assertEqual(response.status_code, 422)
        response = self.client.post("/api/v1/profiles/alice/jobs", json={"kind": "content-image", "input": {"slug": slug, "mode": "edit", "instruction": "edit", "reference": "https://example.test/image.png"}})
        self.assertEqual(response.status_code, 422)
        with self.assertRaises(ValueError):
            content_images.reference_bytes("alice", "another-post", ref)
        with self.assertRaises(ValueError):
            content_images.reference_bytes("alice", slug, "../../.env")

    def test_failed_generation_keeps_reference_and_request(self):
        self._cover_provider()
        slug, _ = self._create_post()
        ref = self.reference(slug)
        with patch("nblane.core.visual_generation.generate_visual_asset", side_effect=RuntimeError("provider failed")):
            run = self.run_image(slug, ref)
        self.assertEqual(run["status"], "failed")
        self.assertIn("provider failed", run["error"])
        self.assertTrue(run["reference"])
        self.assertEqual(run["request"]["instruction"], "只调整背景，保留文字")
        with patch.object(content_images, "PROCESS_ID", "restart"):
            self.assertEqual(content_images.list_runs("alice", slug)[0]["status"], "failed")

    def test_iteration_snapshots_candidate_before_discard(self):
        self._cover_provider()
        slug, _ = self._create_post()
        # Use decodable provider output for subsequent iterations.
        asset = _fake_asset()
        from dataclasses import replace
        with patch("nblane.core.visual_generation.generate_visual_asset", return_value=[replace(asset, data=png_bytes())]):
            first = self.run_image(slug, self.reference(slug))
            second = self.run_image(slug, first["candidates"][0]["candidate_path"])
        content_images.discard("alice", slug, first["id"])
        self.assertEqual(content_images.reference_bytes("alice", slug, second["reference"]), png_bytes())
        self.assertEqual(len(content_images.list_runs("alice", slug)), 1)

    def test_interrupted_run_can_be_recovered_and_removed(self):
        self._cover_provider()
        slug, _ = self._create_post()
        run = self.run_image(slug, self.reference(slug))
        run["status"] = "running"
        content_images._write("alice", run)
        with patch.object(content_images, "PROCESS_ID", "restarted-process"):
            restored = content_images.list_runs("alice", slug)[0]
            self.assertEqual(restored["status"], "failed")
            self.assertEqual(restored["request"], run["request"])
            content_images.discard("alice", slug, run["id"])
            self.assertEqual(content_images.list_runs("alice", slug), [])

    def test_oversized_target_is_rejected_without_truncation(self):
        with self.assertRaises(jobs.JobInputError):
            jobs._validate_content_image_input({
                "slug": "post", "mode": "cover",
                "target": {"kind": "block", "fingerprint": "x" * 10001},
            })

    def test_size_preview_and_job_use_identical_dimensions(self):
        provider = self._cover_provider()
        slug, _ = self._create_post()
        ref = self.reference(slug)
        for quality, expected in [("standard", "1365*768"), ("high", "2730*1536")]:
            params = dict(slug=slug, mode="edit", reference=ref, quality=quality, aspect="original")
            preview = self.client.get("/api/v1/profiles/alice/content/images/size", params=params)
            self.assertEqual(preview.status_code, 200, preview.text)
            self.assertEqual(preview.json()["size"], expected)
            self.assertFalse(preview.json()["supports_4k"])
            run = self.run_image(slug, ref, quality=quality, aspect="original")
            self.assertEqual(run["status"], "done", run)
            self.assertEqual(provider.call_args.kwargs["size"], expected)
            restored = self.client.get("/api/v1/profiles/alice/content/images", params={"slug": slug}).json()["runs"]
            self.assertTrue(any(row["output_size"] == expected for row in restored))

    def test_quality_limits_and_large_original_are_normalized(self):
        self._cover_provider()
        slug, _ = self._create_post()
        with patch.object(content_images, "reference_bytes", return_value=b"reference"), patch.object(content_images, "image_info", return_value=("image/png", (8000, 4000))):
            result = content_images.output_size("alice", {"slug": slug, "mode": "edit", "reference": "media/test.png", "quality": "high", "aspect": "original"})
            width, height = result["width"], result["height"]
            self.assertLessEqual(width * height, 2048 ** 2)
            self.assertAlmostEqual(width / height, 2, places=2)
        with patch.object(visual_generation, "current_config", return_value={"image_model": "wan2.7-image-pro"}):
            request = {"slug": slug, "mode": "cover", "quality": "ultra", "aspect": "1:1"}
            self.assertEqual(content_images.output_size("alice", request)["size"], "4096*4096")
            with self.assertRaises(ValueError):
                content_images.output_size("alice", {**request, "reference": "media/test.png"})
        with patch.object(visual_generation, "current_config", return_value={"image_model": "wan2.7-image"}):
            with self.assertRaises(ValueError):
                content_images.output_size("alice", request)
        response = self.client.get("/api/v1/profiles/alice/content/images/size", params={"slug": slug, "aspect": "original"})
        self.assertEqual(response.status_code, 422)
        with self.assertRaises(jobs.JobInputError):
            jobs._validate_content_image_input({"slug": slug, "mode": "cover", "quality": "unlimited"})
