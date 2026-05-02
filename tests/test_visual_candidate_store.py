from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core import ai_dispatcher, public_site, visual_candidate_store, visual_generation


def _write_blog(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "title": "Draft",
        "date": "2026-05-02",
        "status": "draft",
        "tags": [],
        "summary": "",
        "cover": "",
        "related_evidence": [],
        "related_kanban": [],
    }
    path.write_text(
        "---\n"
        + yaml.dump(meta, allow_unicode=True, default_flow_style=False, sort_keys=False)
        + "---\n\nBody\n",
        encoding="utf-8",
    )


class VisualCandidateStoreTests(unittest.TestCase):
    def test_candidate_promotes_to_blog_media_only_on_accept(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            _write_blog(profile / "blog" / "post.md")
            with (
                patch("nblane.core.visual_candidate_store.profile_dir", lambda _n: profile),
                patch("nblane.core.public_site.profile_dir", lambda _n: profile),
                patch("nblane.core.public_site.git_backup.record_change"),
            ):
                candidate = visual_candidate_store.write_candidate(
                    "alice",
                    "post",
                    "patch-1",
                    data=b"\x89PNG\r\n\x1a\ncandidate",
                    filename="example.png",
                    kind="image",
                    alt="Alt",
                    caption="Caption",
                )

                self.assertTrue(candidate.path.exists())
                self.assertTrue(
                    visual_candidate_store.candidate_exists(
                        "alice",
                        candidate.relative_path,
                    )
                )
                self.assertFalse((profile / "media" / "blog" / "post").exists())

                result = visual_candidate_store.promote_candidate(
                    "alice",
                    "post",
                    candidate.relative_path,
                    kind="image",
                    alt="Alt",
                    caption="Caption",
                )

                self.assertFalse(candidate.path.exists())
                self.assertTrue(result.path.exists())
                self.assertEqual(result.relative_path, "media/blog/post/example.png")

    def test_candidate_discard_removes_temp_file_without_media_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            (profile / "blog").mkdir(parents=True)
            with patch("nblane.core.visual_candidate_store.profile_dir", lambda _n: profile):
                candidate = visual_candidate_store.write_candidate(
                    "alice",
                    "post",
                    "patch-2",
                    data=b"candidate",
                    filename="example.png",
                    kind="image",
                )

                self.assertTrue(
                    visual_candidate_store.discard_candidate(
                        "alice",
                        candidate.relative_path,
                    )
                )

                self.assertFalse(candidate.path.exists())
                self.assertFalse(
                    visual_candidate_store.candidate_exists(
                        "alice",
                        candidate.relative_path,
                    )
                )
                self.assertFalse((profile / "media" / "blog" / "post").exists())

    def test_inline_visual_patch_stages_candidate_path_not_media_src(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            _write_blog(profile / "blog" / "post.md")
            prompt = visual_generation.VisualPrompt(
                positive_prompt="Prompt",
                negative_prompt="",
                asset_type="example",
                recommended_size="1024*1024",
                rationale="",
                safety_notes=[],
            )
            asset = visual_generation.GeneratedVisualAsset(
                data=b"\x89PNG\r\n\x1a\ncandidate",
                mime_type="image/png",
                extension="png",
                prompt=prompt,
                provider="dashscope_wan",
                model="wan2.7-image-pro",
            )
            with (
                patch("nblane.core.visual_candidate_store.profile_dir", lambda _n: profile),
                patch("nblane.core.ai_dispatcher.llm_client.chat", return_value="caption"),
                patch(
                    "nblane.core.ai_dispatcher.visual_generation.from_caption_intent",
                    return_value={
                        "prompt": "A clean system image",
                        "caption": "System",
                        "alt": "System",
                        "provider": "dashscope_wan",
                        "model": "wan2.7-image-pro",
                        "warnings": [],
                        "generated_assets": [asset],
                    },
                ),
            ):
                patch_payload = ai_dispatcher.generate_ai_patch(
                    profile="alice",
                    slug="post",
                    meta={},
                    markdown="Robot system",
                    selected_block={"block_id": "b1", "selection_text": "Robot system"},
                    operation="visual",
                    source_event_id="task-visual",
                )

            props = patch_payload["block_patches"][0]["block"]["props"]
            self.assertEqual(props["src"], "")
            self.assertIn("blog/.candidates/", props["candidate_path"])
            self.assertEqual(patch_payload["assets"][0]["candidate_path"], props["candidate_path"])
            self.assertFalse((profile / "media" / "blog" / "post").exists())

    def test_inline_visual_patch_fails_when_generated_asset_cannot_be_staged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            _write_blog(profile / "blog" / "post.md")
            prompt = visual_generation.VisualPrompt(
                positive_prompt="Prompt",
                negative_prompt="",
                asset_type="example",
                recommended_size="1024*1024",
                rationale="",
                safety_notes=[],
            )
            asset = visual_generation.GeneratedVisualAsset(
                data=b"\x89PNG\r\n\x1a\ncandidate",
                mime_type="image/png",
                extension="png",
                prompt=prompt,
                provider="dashscope_wan",
                model="wan2.7-image-pro",
            )
            with (
                patch("nblane.core.visual_candidate_store.profile_dir", lambda _n: profile),
                patch("nblane.core.ai_dispatcher.llm_client.chat", return_value="caption"),
                patch(
                    "nblane.core.ai_dispatcher.visual_generation.from_caption_intent",
                    return_value={
                        "prompt": "A clean system image",
                        "caption": "System",
                        "alt": "System",
                        "provider": "dashscope_wan",
                        "model": "wan2.7-image-pro",
                        "warnings": [],
                        "generated_assets": [asset],
                    },
                ),
                patch(
                    "nblane.core.ai_dispatcher.visual_candidate_store.write_candidate",
                    side_effect=RuntimeError("disk full"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "could not be staged"):
                    ai_dispatcher.generate_ai_patch(
                        profile="alice",
                        slug="post",
                        meta={},
                        markdown="Robot system",
                        selected_block={"block_id": "b1", "selection_text": "Robot system"},
                        operation="visual",
                        source_event_id="task-visual",
                    )

            self.assertFalse((profile / "media" / "blog" / "post").exists())


if __name__ == "__main__":
    unittest.main()
