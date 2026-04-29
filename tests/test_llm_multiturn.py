"""Tests for multi-turn ``chat_messages``."""

from __future__ import annotations

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class TestChatMessages(unittest.TestCase):
    """``chat_messages`` forwards history to the API."""

    def test_runtime_config_updates_label_and_mask(self) -> None:
        """Runtime configuration can override env-loaded values."""
        with patch("nblane.core.llm._BASE_URL", "https://old.example/v1"):
            with patch("nblane.core.llm._API_KEY", ""):
                with patch("nblane.core.llm._MODEL", "old-model"):
                    with patch("nblane.core.llm._UI_LANG", "en"):
                        with patch("nblane.core.llm._REPLY_LANG", "en"):
                            from nblane.core import llm

                            llm.configure(
                                base_url=" https://new.example/v1 ",
                                api_key="sk-1234567890",
                                model=" qwen-plus ",
                                ui_lang="ZH",
                                reply_lang="en",
                            )

                            self.assertTrue(llm.is_configured())
                            self.assertEqual(
                                llm.model_label(),
                                "qwen-plus @ https://new.example/v1",
                            )
                            self.assertEqual(llm.ui_language(), "zh")
                            self.assertEqual(llm.reply_language(), "en")

                            masked = llm.current_config()
                            self.assertEqual(
                                masked["api_key"],
                                "sk-1...7890",
                            )
                            self.assertEqual(masked["ui_lang"], "zh")
                            self.assertEqual(masked["reply_lang"], "en")
                            raw = llm.current_config(mask_key=False)
                            self.assertEqual(
                                raw["api_key"],
                                "sk-1234567890",
                            )

    def test_visual_config_reuses_llm_key_for_dashscope(self) -> None:
        """Visual generation defaults to DashScope and can reuse LLM_API_KEY."""
        from nblane.core import visual_generation

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("nblane.core.llm._API_KEY", "llm-visual-key"),
            patch(
                "nblane.core.llm._BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
        ):
            cfg = visual_generation.current_config(mask_key=False)

        self.assertTrue(cfg["configured"])
        self.assertEqual(cfg["provider"], "dashscope_wan")
        self.assertEqual(cfg["api_key"], "llm-visual-key")
        self.assertEqual(cfg["api_key_source"], "LLM_API_KEY")
        self.assertEqual(cfg["base_url_source"], "LLM_BASE_URL")
        self.assertEqual(cfg["image_model"], "wan2.7-image-pro")
        self.assertEqual(cfg["video_model"], "wan2.7-videoedit")

    def test_visual_key_priority_and_default_endpoint(self) -> None:
        """VISUAL_API_KEY wins, then DASHSCOPE_API_KEY, then LLM_API_KEY."""
        from nblane.core import visual_generation

        with (
            patch.dict(
                os.environ,
                {
                    "VISUAL_API_KEY": "visual-key",
                    "DASHSCOPE_API_KEY": "dash-key",
                    "VISUAL_IMAGE_MODEL": "custom-image",
                },
                clear=True,
            ),
            patch("nblane.core.llm._API_KEY", "llm-key"),
            patch("nblane.core.llm._BASE_URL", "https://api.openai.com/v1"),
        ):
            cfg = visual_generation.current_config(mask_key=False)
        self.assertEqual(cfg["api_key"], "visual-key")
        self.assertEqual(cfg["api_key_source"], "VISUAL_API_KEY")
        self.assertEqual(cfg["image_model"], "custom-image")

        with (
            patch.dict(os.environ, {"DASHSCOPE_API_KEY": "dash-key"}, clear=True),
            patch("nblane.core.llm._API_KEY", "llm-key"),
            patch("nblane.core.llm._BASE_URL", "https://api.openai.com/v1"),
        ):
            cfg = visual_generation.current_config(mask_key=False)
        self.assertEqual(cfg["api_key"], "dash-key")
        self.assertEqual(cfg["api_key_source"], "DASHSCOPE_API_KEY")
        self.assertEqual(cfg["base_url_source"], "default")
        self.assertIn("api/v1/services/aigc", cfg["base_url"])

    def test_visual_config_missing_key_is_unconfigured(self) -> None:
        """Missing visual credentials produce a clear unconfigured state."""
        from nblane.core import visual_generation

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("nblane.core.llm._API_KEY", ""),
            patch("nblane.core.llm._BASE_URL", "https://api.openai.com/v1"),
        ):
            cfg = visual_generation.current_config()

        self.assertFalse(cfg["configured"])
        self.assertEqual(cfg["api_key_source"], "")
        self.assertIn("Missing visual API key", "\n".join(cfg["warnings"]))

    def test_blog_visual_prompt_strategy_constraints(self) -> None:
        """Prompt builder adds asset-specific constraints and hides private paths."""
        from nblane.core import visual_generation

        flow = visual_generation.build_blog_visual_prompt(
            "flowchart",
            "A to B to C",
        )
        self.assertIn("rectangular boxes", flow.positive_prompt)
        self.assertIn("clear arrows", flow.positive_prompt)
        self.assertIn("tiny text", flow.negative_prompt)
        self.assertIn("watermark", flow.negative_prompt)

        cover = visual_generation.build_blog_visual_prompt(
            "cover",
            "Robot deployment",
            title="Robot Notes",
        )
        self.assertIn("Do not embed title text", cover.positive_prompt)
        self.assertIn("negative space", cover.positive_prompt)

        example = visual_generation.build_blog_visual_prompt(
            "example",
            "Use profiles/alice/kanban.md and agent-profile.yaml",
        )
        combined = example.positive_prompt + " " + " ".join(example.safety_notes)
        self.assertNotIn("profiles/alice/kanban.md", combined)
        self.assertNotIn("agent-profile.yaml", example.positive_prompt)

    def test_dashscope_image_payload_uses_messages(self) -> None:
        """Wan 2.7 image generation uses DashScope multimodal messages."""
        from nblane.core import visual_generation

        prompt = visual_generation.VisualPrompt(
            positive_prompt="clean cover",
            negative_prompt="watermark",
            asset_type="cover",
            recommended_size="1536*864",
            rationale="test",
        )

        payload = visual_generation._dashscope_payload(
            prompt,
            asset_type="cover",
            model="wan2.7-image-pro",
            size="1024x1024",
        )

        self.assertIn("messages", payload["input"])
        self.assertNotIn("prompt", payload["input"])
        self.assertEqual(payload["parameters"]["size"], "1024*1024")
        text = payload["input"]["messages"][0]["content"][0]["text"]
        self.assertIn("clean cover", text)
        self.assertIn("Avoid: watermark", text)

    def test_dashscope_image_response_extracts_content_image_url(self) -> None:
        """Wan 2.7 responses may return asset URLs under content.image."""
        from nblane.core import visual_generation

        response = {
            "output": {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {
                                    "image": "https://example.com/generated.png",
                                }
                            ],
                        }
                    }
                ],
            }
        }

        self.assertEqual(
            visual_generation._extract_urls(response),
            ["https://example.com/generated.png"],
        )

    def test_dashscope_legacy_image_payload_still_uses_prompt(self) -> None:
        """Explicit Wan 2.1 image models keep the older prompt payload."""
        from nblane.core import visual_generation

        prompt = visual_generation.VisualPrompt(
            positive_prompt="legacy cover",
            negative_prompt="watermark",
            asset_type="cover",
            recommended_size="1024*1024",
            rationale="test",
        )

        payload = visual_generation._dashscope_payload(
            prompt,
            asset_type="cover",
            model="wan2.1-t2i-turbo",
            size="1024*1024",
        )

        self.assertIn("prompt", payload["input"])
        self.assertNotIn("messages", payload["input"])
        self.assertIn("legacy cover", payload["input"]["prompt"])

    def test_dashscope_image_size_validation_is_local(self) -> None:
        """Invalid DashScope sizes fail before an API task is started."""
        from nblane.core import visual_generation

        with self.assertRaisesRegex(RuntimeError, "at least 768\\*768"):
            visual_generation._normalize_image_size(
                "512*512",
                model="wan2.7-image-pro",
            )
        with self.assertRaisesRegex(RuntimeError, "1:8 and 8:1"):
            visual_generation._normalize_image_size(
                "4096*500",
                model="wan2.7-image-pro",
            )
        with self.assertRaisesRegex(RuntimeError, "only available"):
            visual_generation._normalize_image_size(
                "4K",
                model="wan2.7-image-pro",
                has_reference_image=True,
            )
        self.assertEqual(
            visual_generation._normalize_image_size(
                "1536x864",
                model="wan2.7-image-pro",
            ),
            "1536*864",
        )

    def test_ui_copy_uses_ui_language_not_reply_language(self) -> None:
        """Interface strings follow UI_LANG independently."""
        from nblane.web_i18n import common_ui

        with patch("nblane.core.llm._UI_LANG", "zh"):
            with patch("nblane.core.llm._REPLY_LANG", "en"):
                zh_ui = common_ui()
        self.assertEqual(zh_ui["profile_header"], "## 当前档案")
        self.assertEqual(zh_ui["llm_reply_lang"], "模型回复语言")

        with patch("nblane.core.llm._UI_LANG", "en"):
            with patch("nblane.core.llm._REPLY_LANG", "zh"):
                en_ui = common_ui()
        self.assertEqual(en_ui["profile_header"], "## Current profile")
        self.assertEqual(en_ui["llm_reply_lang"], "Model reply language")

    def test_returns_assistant_content(self) -> None:
        """OpenAI client receives system plus user/assistant turns."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(content="final reply")
                )
            ]
        )
        fake_openai = types.SimpleNamespace(OpenAI=MagicMock(return_value=mock_client))
        with patch(
            "nblane.core.llm._API_KEY",
            "test-key",
        ):
            with patch.dict(sys.modules, {"openai": fake_openai}):
                from nblane.core import llm

                out = llm.chat_messages(
                    "You are a coach.",
                    [
                        {"role": "user", "content": "hello"},
                        {"role": "assistant", "content": "hi"},
                        {"role": "user", "content": "follow up"},
                    ],
                )
        self.assertEqual(out, "final reply")
        call = mock_client.chat.completions.create
        msgs = call.call_args.kwargs["messages"]
        self.assertEqual(len(msgs), 4)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[-1]["role"], "user")
        self.assertEqual(msgs[-1]["content"], "follow up")


if __name__ == "__main__":
    unittest.main()
