"""Tests for content-workspace AI (rewrite / meta suggestions / cover candidates).

LLM and image provider calls are mocked; no network. Covers the core helpers
(validation, JSON parsing, candidate staging/promotion, never writing the
post), the three job kinds end-to-end through ``POST .../jobs``, and the cover
candidate routes (path guard, promote leaves the post file untouched).
"""

from __future__ import annotations

import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from fastapi.testclient import TestClient

from nblane.core import content_ai, visual_generation
from nblane.core.paths import REPO_ROOT
from nblane.web_api import app
from nblane.web_api import jobs as jobs_module

TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"

PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)

BODY = "这篇文章介绍如何在家用机械臂上复现 VLA 训练流程，包括数据采集、标注与评测。" * 3


def _fake_asset() -> visual_generation.GeneratedVisualAsset:
    prompt = visual_generation.VisualPrompt(
        positive_prompt="editorial cover",
        negative_prompt="text",
        asset_type="cover",
        recommended_size="1536*864",
        rationale="",
    )
    return visual_generation.GeneratedVisualAsset(
        data=PNG_BYTES,
        mime_type="image/png",
        extension="png",
        prompt=prompt,
        provider="dashscope_wan",
        model="wan-test",
    )


class ContentAITestBase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.profile = self.root / "alice"
        shutil.copytree(TEMPLATE_DIR, self.profile)
        (self.profile / "public-profile.yaml").write_text(
            yaml.safe_dump({"profile": "alice", "visibility": "private"}), encoding="utf-8"
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
            "nblane.core.profile_io.git_backup.record_change",
            "nblane.core.public_site.git_backup.record_change",
        ):
            patcher = patch(target)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = TestClient(app)

    def _llm(self, reply: str, configured: bool = True):
        stack = [
            patch("nblane.core.llm.is_configured", return_value=configured),
            patch("nblane.core.llm.chat", return_value=reply),
        ]
        mocks = [p.start() for p in stack]
        for p in stack:
            self.addCleanup(p.stop)
        return mocks[1]

    def _cover_provider(self, configured: bool = True):
        stack = [
            patch("nblane.core.content_ai.cover_available", return_value=configured),
            patch(
                "nblane.core.visual_generation.generate_visual_asset",
                return_value=[_fake_asset()],
            ),
        ]
        mocks = [p.start() for p in stack]
        for p in stack:
            self.addCleanup(p.stop)
        return mocks[1]

    def _create_post(self) -> tuple[str, Path]:
        response = self.client.post(
            "/api/v1/profiles/alice/content/blog", json={"title": "VLA 复现", "body": BODY}
        )
        self.assertEqual(response.status_code, 201, response.text)
        slug = response.json()["post"]["slug"]
        return slug, self.profile / "blog" / f"{slug}.md"

    def _run_job(self, kind: str, job_input: dict) -> dict:
        created = self.client.post("/api/v1/profiles/alice/jobs", json={"kind": kind, "input": job_input})
        self.assertEqual(created.status_code, 202, created.text)
        job_id = created.json()["job_id"]
        deadline = time.monotonic() + 10
        while True:
            payload = self.client.get(f"/api/v1/profiles/alice/jobs/{job_id}").json()
            if payload["job"]["status"] in jobs_module.FINAL_STATUSES:
                return payload
            if time.monotonic() > deadline:
                self.fail(f"job {job_id} did not finish")
            time.sleep(0.05)


class TestRewrite(ContentAITestBase):
    def test_rewrite_returns_candidate_text(self) -> None:
        chat = self._llm("```markdown\n润色后的段落。\n```")
        result = content_ai.rewrite_selection(operation="polish", selection="原始段落。", title="T")
        self.assertEqual(result, {"operation": "polish", "original": "原始段落。", "text": "润色后的段落。"})
        user_prompt = chat.call_args.args[1]
        self.assertIn("目标文本：\n原始段落。", user_prompt)

    def test_rewrite_rejects_unknown_operation_and_long_selection(self) -> None:
        self._llm("x")
        with self.assertRaises(content_ai.ContentAIError) as ctx:
            content_ai.rewrite_selection(operation="reorganize", selection="a")
        self.assertEqual(ctx.exception.code, "invalid_content_ai_request")
        with self.assertRaises(content_ai.ContentAIError):
            content_ai.rewrite_selection(operation="polish", selection="字" * (content_ai.SELECTION_MAX_CHARS + 1))

    def test_rewrite_requires_llm(self) -> None:
        self._llm("x", configured=False)
        with self.assertRaises(content_ai.ContentAIError) as ctx:
            content_ai.rewrite_selection(operation="shorten", selection="a")
        self.assertEqual(ctx.exception.code, "content_ai_unavailable")

    def test_llm_error_string_becomes_failure(self) -> None:
        self._llm("LLM error: boom")
        with self.assertRaises(content_ai.ContentAIError) as ctx:
            content_ai.rewrite_selection(operation="polish", selection="a")
        self.assertEqual(ctx.exception.code, "content_ai_failed")

    def test_rewrite_job_end_to_end(self) -> None:
        self._llm("更短的版本。")
        payload = self._run_job("content-rewrite", {"operation": "shorten", "selection": "一段很长的文字。"})
        self.assertEqual(payload["job"]["status"], "done", payload)
        self.assertEqual(payload["result"]["text"], "更短的版本。")

    def test_rewrite_job_rejects_empty_selection(self) -> None:
        response = self.client.post(
            "/api/v1/profiles/alice/jobs",
            json={"kind": "content-rewrite", "input": {"operation": "polish", "selection": "  "}},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_content_ai_request")


class TestMetaSuggestions(ContentAITestBase):
    def test_parses_and_cleans_json(self) -> None:
        self._llm(
            '好的：```json\n{"titles": ["标题一", "标题一", "标题二"], '
            '"summaries": ["摘要一。"], "tags": ["#机器人", "VLA", ""]}\n```'
        )
        result = content_ai.suggest_meta(title="", summary="", tags=[], body=BODY)
        self.assertEqual(result["titles"], ["标题一", "标题二"])
        self.assertEqual(result["summaries"], ["摘要一。"])
        self.assertEqual(result["tags"], ["机器人", "VLA"])

    def test_rejects_short_body_and_bad_json(self) -> None:
        self._llm("not json")
        with self.assertRaises(content_ai.ContentAIError) as ctx:
            content_ai.suggest_meta(title="", summary="", tags=[], body="太短")
        self.assertEqual(ctx.exception.code, "invalid_content_ai_request")
        with self.assertRaises(content_ai.ContentAIError) as ctx:
            content_ai.suggest_meta(title="", summary="", tags=[], body=BODY)
        self.assertEqual(ctx.exception.code, "content_ai_failed")

    def test_meta_job_failure_is_structured(self) -> None:
        self._llm("x", configured=False)
        payload = self._run_job("content-meta", {"title": "t", "summary": "", "tags": [], "body": BODY})
        self.assertEqual(payload["job"]["status"], "failed")
        self.assertEqual(payload["job"]["error"]["code"], "content_ai_unavailable")


class TestCover(ContentAITestBase):
    def test_cover_job_stages_candidates_without_touching_post(self) -> None:
        generate = self._cover_provider()
        slug, md_path = self._create_post()
        before = md_path.read_bytes()
        payload = self._run_job("content-cover", {"slug": slug, "brief": "夜景", "title": "实时标题"})
        self.assertEqual(payload["job"]["status"], "done", payload)
        rows = payload["result"]["candidates"]
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["candidate_path"].startswith("blog/.candidates/"))
        self.assertEqual(md_path.read_bytes(), before)
        # Live editor title overrides the saved one in the prompt inputs.
        self.assertEqual(generate.call_args.kwargs["title"], "实时标题")
        self.assertEqual(generate.call_args.args, ("cover", "夜景"))

        served = self.client.get(
            "/api/v1/profiles/alice/content/cover-candidates/file", params={"path": rows[0]["candidate_path"]}
        )
        self.assertEqual(served.status_code, 200)
        self.assertEqual(served.content, PNG_BYTES)

    def test_promote_moves_into_media_and_keeps_post(self) -> None:
        self._cover_provider()
        slug, md_path = self._create_post()
        etag = self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}").headers["ETag"]
        rows = content_ai.generate_cover_candidates("alice", slug)
        promoted = self.client.post(
            f"/api/v1/profiles/alice/content/blog/{slug}/cover-candidates/promote",
            json={"candidate_path": rows[0]["candidate_path"]},
        )
        self.assertEqual(promoted.status_code, 200, promoted.text)
        path = promoted.json()["path"]
        self.assertTrue(path.startswith(f"media/blog/{slug}/generated-cover-"))
        self.assertTrue((self.profile / path).is_file())
        self.assertFalse((self.profile / rows[0]["candidate_path"]).exists())
        # Post untouched: same ETag, cover still empty until the editor saves.
        detail = self.client.get(f"/api/v1/profiles/alice/content/blog/{slug}")
        self.assertEqual(detail.headers["ETag"], etag)
        self.assertEqual(detail.json()["cover"], "")
        # Generated candidates must never surface as blog posts.
        slugs = [p["slug"] for p in self.client.get("/api/v1/profiles/alice/content").json()["posts"]]
        self.assertEqual(slugs, [slug])

    def test_discard_and_path_guard(self) -> None:
        self._cover_provider()
        slug, _ = self._create_post()
        rows = content_ai.generate_cover_candidates("alice", slug)
        for bad in ("resume-source.yaml", "blog/.candidates/../../resume-source.yaml"):
            response = self.client.get("/api/v1/profiles/alice/content/cover-candidates/file", params={"path": bad})
            self.assertEqual(response.status_code, 404, bad)
        discarded = self.client.post(
            "/api/v1/profiles/alice/content/cover-candidates/discard",
            json={"candidate_path": rows[0]["candidate_path"]},
        )
        self.assertEqual(discarded.json(), {"ok": True, "removed": True})
        missing = self.client.post(
            f"/api/v1/profiles/alice/content/blog/{slug}/cover-candidates/promote",
            json={"candidate_path": rows[0]["candidate_path"]},
        )
        self.assertEqual(missing.status_code, 404)

    def test_cover_unavailable(self) -> None:
        self._cover_provider(configured=False)
        slug, _ = self._create_post()
        payload = self._run_job("content-cover", {"slug": slug})
        self.assertEqual(payload["job"]["status"], "failed")
        self.assertEqual(payload["job"]["error"]["code"], "cover_unavailable")

    def test_status_endpoint(self) -> None:
        with patch("nblane.core.content_ai.llm_available", return_value=True), patch(
            "nblane.core.content_ai.cover_available", return_value=False
        ):
            response = self.client.get("/api/v1/profiles/alice/content/ai/status")
        self.assertEqual(response.json(), {"text": True, "cover": False})


if __name__ == "__main__":
    unittest.main()
