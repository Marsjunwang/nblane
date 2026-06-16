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

    def test_reorganize_replaces_whole_document_without_block_patches(self) -> None:
        raw = "# Title\n\nClean body.\n\n## Section\nMore."
        captured: dict[str, object] = {}

        def fake_chat(*_args, **kwargs):
            captured.update(kwargs)
            return raw

        with patch("nblane.core.ai_dispatcher.llm_client.chat", side_effect=fake_chat):
            patch_payload = ai_dispatcher.generate_ai_patch(
                profile="alice",
                slug="post",
                meta={"title": "Draft"},
                markdown="messy body " * 50,
                selected_block={"cursor_block_id": "b1"},
                operation="reorganize",
            )

        self.assertEqual(patch_payload["operation"], "reorganize")
        # Whole-document rewrite: no per-block patches, full body in fallback.
        self.assertEqual(patch_payload["block_patches"], [])
        self.assertIn("Clean body.", patch_payload["markdown_fallback"])
        self.assertFalse(patch_payload["warnings"])
        # Output ceiling must exceed the low default so long articles aren't cut.
        self.assertIsNotNone(captured.get("max_tokens"))
        self.assertGreaterEqual(int(captured["max_tokens"]), len("messy body " * 50))

    def test_reorganize_warns_when_output_truncated(self) -> None:
        def fake_chat(*_args, **kwargs):
            meta_out = kwargs.get("meta_out")
            if meta_out is not None:
                meta_out["finish_reason"] = "length"
            return "# Title\n\nHalf-written"

        with patch("nblane.core.ai_dispatcher.llm_client.chat", side_effect=fake_chat):
            patch_payload = ai_dispatcher.generate_ai_patch(
                profile="alice",
                slug="post",
                meta={},
                markdown="long body " * 100,
                selected_block={"cursor_block_id": "b1"},
                operation="reorganize",
            )

        self.assertTrue(patch_payload["warnings"])
        self.assertIn("cut off", patch_payload["warnings"][0].lower())

    def test_chunk_markdown_keeps_code_and_math_blocks_intact(self) -> None:
        code_block = "```python\nx = 1\n\ny = 2\n```"
        math_block = "$$\na^2 + b^2\n\n= c^2\n$$"
        markdown = f"# Title\n\nIntro paragraph.\n\n{code_block}\n\nMiddle.\n\n{math_block}\n\nEnd."
        blocks = ai_dispatcher._split_markdown_atomic_blocks(markdown)
        # The fenced code block and the $$ math block survive as single atoms
        # even though they contain blank lines internally.
        self.assertIn(code_block, blocks)
        self.assertIn(math_block, blocks)

    def test_chunk_markdown_packs_blocks_under_limit(self) -> None:
        markdown = "\n\n".join(f"Paragraph number {i} with text." for i in range(20))
        chunks = ai_dispatcher._chunk_markdown(markdown, max_chars=120)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            # A chunk may exceed the limit only when a single block already does.
            self.assertTrue(len(chunk) <= 120 or "\n\n" not in chunk)
        # Concatenation preserves every paragraph.
        rejoined = "\n\n".join(chunks)
        self.assertIn("Paragraph number 0", rejoined)
        self.assertIn("Paragraph number 19", rejoined)

    def test_reorganize_chunks_long_document_and_concatenates(self) -> None:
        # A document far larger than the output ceiling must be split into
        # multiple LLM calls and concatenated, not truncated to one call.
        calls: list[str] = []

        def fake_chat(_system, user, *_args, **_kwargs):
            calls.append(user)
            # Echo a marker so we can verify each fragment contributes output.
            return f"reorganized-{len(calls)}"

        with patch("nblane.core.ai_dispatcher.llm_client.max_tokens_default", return_value=512), patch(
            "nblane.core.ai_dispatcher.llm_client.chat", side_effect=fake_chat
        ):
            patch_payload = ai_dispatcher.generate_ai_patch(
                profile="alice",
                slug="post",
                meta={"title": "Draft"},
                markdown="\n\n".join(f"Paragraph {i} body text here." for i in range(200)),
                selected_block={"cursor_block_id": "b1"},
                operation="reorganize",
            )

        self.assertGreater(len(calls), 1)  # actually chunked
        fallback = patch_payload["markdown_fallback"]
        self.assertIn("reorganized-1", fallback)
        self.assertIn(f"reorganized-{len(calls)}", fallback)
        self.assertEqual(patch_payload["block_patches"], [])

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

    def test_outline_patch_can_use_article_context_without_prompt_or_selection(self) -> None:
        raw_outline = "## Context\n- Current draft\n\n## Next\n- Expand"
        with patch("nblane.core.ai_dispatcher.llm_client.chat", return_value=raw_outline):
            patch_payload = ai_dispatcher.generate_ai_patch(
                profile="alice",
                slug="post",
                meta={"title": "Draft"},
                markdown="Existing article context",
                selected_block={"cursor_block_id": "b1"},
                operation="outline",
            )

        self.assertEqual(patch_payload["operation"], "outline")
        self.assertIn("## Context", patch_payload["markdown_fallback"])
        self.assertEqual(patch_payload["block_patches"][0]["block"]["type"], "heading")

    def test_ai_prompt_includes_optional_abstract_meta(self) -> None:
        seen_user_prompt = ""

        def fake_chat(_system: str, user: str, **_kwargs) -> str:
            nonlocal seen_user_prompt
            seen_user_prompt = user
            return "## Context\n- Point"

        with patch("nblane.core.ai_dispatcher.llm_client.chat", side_effect=fake_chat):
            ai_dispatcher.generate_ai_patch(
                profile="alice",
                slug="post",
                meta={"title": "Draft", "abstract": "Paper-style abstract"},
                markdown="Existing article context",
                selected_block={"cursor_block_id": "b1"},
                operation="outline",
            )

        self.assertIn('"abstract": "Paper-style abstract"', seen_user_prompt)

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

    def test_diagram_patch_normalizes_single_line_flowchart(self) -> None:
        raw = (
            "flowchart TD A[用户输入账号密码] --> B{系统校验} "
            "B -->|校验成功| C[成功进入首页] B -->|校验失败| D[失败提示错误]"
        )
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

        mermaid = patch_payload["block_patches"][0]["block"]["props"]["mermaid"]
        self.assertEqual(
            mermaid,
            "\n".join(
                [
                    "flowchart TD",
                    "  A[用户输入账号密码] --> B{系统校验}",
                    "  B -->|校验成功| C[成功进入首页]",
                    "  B -->|校验失败| D[失败提示错误]",
                ]
            ),
        )

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
