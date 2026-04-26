"""Tests for multi-turn ``chat_messages``."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class TestChatMessages(unittest.TestCase):
    """``chat_messages`` forwards history to the API."""

    def test_runtime_config_updates_label_and_mask(self) -> None:
        """Runtime configuration can override env-loaded values."""
        with patch("nblane.core.llm._BASE_URL", "https://old.example/v1"):
            with patch("nblane.core.llm._API_KEY", ""):
                with patch("nblane.core.llm._MODEL", "old-model"):
                    with patch("nblane.core.llm._REPLY_LANG", "en"):
                        from nblane.core import llm

                        llm.configure(
                            base_url=" https://new.example/v1 ",
                            api_key="sk-1234567890",
                            model=" qwen-plus ",
                            reply_lang="ZH",
                        )

                        self.assertTrue(llm.is_configured())
                        self.assertEqual(
                            llm.model_label(),
                            "qwen-plus @ https://new.example/v1",
                        )
                        self.assertEqual(llm.reply_language(), "zh")

                        masked = llm.current_config()
                        self.assertEqual(
                            masked["api_key"],
                            "sk-1...7890",
                        )
                        raw = llm.current_config(mask_key=False)
                        self.assertEqual(
                            raw["api_key"],
                            "sk-1234567890",
                        )

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
        with patch(
            "nblane.core.llm._API_KEY",
            "test-key",
        ):
            with patch(
                "openai.OpenAI",
                return_value=mock_client,
            ):
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
