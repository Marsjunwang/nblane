from __future__ import annotations

import unittest
from unittest.mock import patch

from nblane.core import ai_blog_outline, ai_dispatcher, visual_generation


class AIBlogPhase3Tests(unittest.TestCase):
    def test_parse_outline_markdown_to_blocks_adds_heading_and_placeholder(self) -> None:
        blocks = ai_blog_outline.parse_outline_markdown_to_blocks(
            "# Title\n\n## Context\n- Point A\n- Point B\n\n## Next\nDraft paragraph."
        )

        headings = [block for block in blocks if block["type"] == "heading"]
        bullets = [block for block in blocks if block["type"] == "bulletListItem"]
        self.assertEqual(headings[0]["content"], "Title")
        self.assertEqual(headings[0]["props"]["level"], 1)
        self.assertEqual(headings[1]["content"], "Context")
        self.assertEqual(bullets[0]["content"], "Point A")
        self.assertEqual(blocks[-1]["content"], "Draft paragraph.")

    def test_formula_patch_uses_math_block_comment_with_provenance(self) -> None:
        with patch("nblane.core.ai_dispatcher.llm_client.chat", return_value="$$x^2+y^2=z^2$$"):
            patch_payload = ai_dispatcher.generate_ai_patch(
                profile="alice",
                slug="post",
                meta={},
                markdown="",
                selected_block={"block_id": "b1", "selection_text": "pythagorean theorem"},
                operation="formula",
                source_event_id="task-1",
            )

        self.assertEqual(patch_payload["operation"], "formula")
        self.assertIn("nblane:math_block", patch_payload["markdown_fallback"])
        block = patch_payload["block_patches"][0]["block"]
        self.assertEqual(block["type"], "math_block")
        self.assertEqual(block["props"]["latex"], "x^2+y^2=z^2")
        self.assertTrue(block["props"]["ai_generated"])
        self.assertFalse(block["props"]["accepted"])
        self.assertEqual(block["props"]["ai_source_id"], "task-1")

    def test_outline_patch_includes_structured_blocks_and_markdown(self) -> None:
        raw_outline = "## Problem\n- Constraint\n\n## Solution\n- Step"
        with patch("nblane.core.ai_dispatcher.llm_client.chat", return_value=raw_outline):
            patch_payload = ai_dispatcher.generate_ai_patch(
                profile="alice",
                slug="post",
                meta={"title": "Draft"},
                markdown="Context",
                selected_block={"cursor_block_id": "b1"},
                operation="outline",
                prompt="Draft outline",
            )

        self.assertEqual(patch_payload["operation"], "outline")
        self.assertIn("## Problem", patch_payload["markdown_fallback"])
        self.assertGreaterEqual(len(patch_payload["block_patches"]), 4)
        self.assertEqual(patch_payload["block_patches"][0]["block"]["type"], "heading")

    def test_diagram_patch_uses_visual_block_with_mermaid(self) -> None:
        raw = "flowchart TD\n  A[Login] --> B{Valid?}\n  B --> C[Home]"
        with patch("nblane.core.ai_dispatcher.llm_client.chat", return_value=raw):
            patch_payload = ai_dispatcher.generate_ai_patch(
                profile="alice",
                slug="post",
                meta={},
                markdown="",
                selected_block={"cursor_block_id": "b1"},
                operation="visual",
                visual_kind="diagram",
                prompt="User login flow",
            )

        self.assertEqual(patch_payload["operation"], "visual")
        self.assertIn("nblane:visual_block", patch_payload["markdown_fallback"])
        props = patch_payload["block_patches"][0]["block"]["props"]
        self.assertEqual(props["asset_type"], "diagram")
        self.assertEqual(props["visual_kind"], "flowchart")
        self.assertIn("flowchart TD", props["mermaid"])
        self.assertEqual(patch_payload["assets"][0]["kind"], "diagram")

    def test_empty_formula_prompt_requires_selection_or_description(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "请先选中文本"):
            ai_dispatcher.generate_ai_patch(
                profile="alice",
                slug="post",
                meta={},
                markdown="Existing body",
                selected_block={"cursor_block_id": "b1"},
                operation="formula",
            )

    def test_caption_intent_parser_accepts_json_and_plain_text(self) -> None:
        parsed = visual_generation.parse_caption_intent_response(
            '{"prompt":"Clean robot arm diagram","caption":"Robot arm","alt":"Robot arm"}'
        )
        self.assertEqual(parsed["prompt"], "Clean robot arm diagram")
        self.assertEqual(parsed["caption"], "Robot arm")
        self.assertEqual(parsed["alt"], "Robot arm")

        fallback = visual_generation.parse_caption_intent_response(
            "A clear image of the system.",
            source_text="Diffusion policy controls a robot arm.",
        )
        self.assertIn("clear image", fallback["prompt"])
        self.assertIn("Diffusion policy", fallback["caption"])


if __name__ == "__main__":
    unittest.main()
