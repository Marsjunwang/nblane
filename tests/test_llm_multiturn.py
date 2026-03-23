"""Tests for multi-turn ``chat_messages``."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class TestChatMessages(unittest.TestCase):
    """``chat_messages`` forwards history to the API."""

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
