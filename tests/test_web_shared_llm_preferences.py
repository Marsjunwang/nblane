import unittest
from contextlib import contextmanager
from unittest.mock import patch

from nblane import web_shared


def _prefs(provider: str, base_url: str, model: str) -> dict:
    return {
        "ai": {
            "llm": {
                "provider": provider,
                "base_url": base_url,
                "model": model,
                "custom_model": model,
                "ui_lang": "zh",
                "reply_lang": "zh",
            }
        }
    }


class TestWebSharedLlmPreferences(unittest.TestCase):
    @contextmanager
    def _patch_defaults(self, state: dict, prefs: dict):
        with (
            patch.object(web_shared.st, "session_state", state),
            patch.object(web_shared, "load_web_preferences", return_value=prefs),
            patch.object(
                web_shared.llm_client,
                "current_config",
                return_value={
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model": "qwen3.6-plus",
                },
            ),
            patch.object(web_shared, "apply_ui_language_from_session"),
        ):
            yield

    def test_llm_sidebar_syncs_persisted_prefs_over_stale_session(self) -> None:
        state: dict = {}
        qwen = _prefs(
            "Qwen / DashScope",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "qwen3.6-plus",
        )
        with self._patch_defaults(state, qwen):
            web_shared._ensure_llm_session_defaults("alice")
            state[web_shared._LLM_PROVIDER_KEY] = "OpenAI"
            state[web_shared._LLM_BASE_URL_KEY] = "https://api.openai.com/v1"
            state[web_shared._LLM_MODEL_CHOICE_KEY] = "gpt-4o"

            web_shared._ensure_llm_session_defaults("alice")

        self.assertEqual(state[web_shared._LLM_PROVIDER_KEY], "Qwen / DashScope")
        self.assertEqual(
            state[web_shared._LLM_BASE_URL_KEY],
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.assertEqual(state[web_shared._LLM_MODEL_CHOICE_KEY], "qwen3.6-plus")

    def test_llm_sidebar_keeps_dirty_user_changes_until_persisted(self) -> None:
        state: dict = {
            web_shared._LLM_PREFS_PROFILE_KEY: "alice",
            web_shared._LLM_PREFS_DIRTY_KEY: True,
            web_shared._LLM_PROVIDER_KEY: "Qwen / DashScope",
            web_shared._LLM_BASE_URL_KEY: "https://dashscope.aliyuncs.com/compatible-mode/v1",
            web_shared._LLM_MODEL_CHOICE_KEY: "qwen3.6-plus",
        }
        openai = _prefs("OpenAI", "https://api.openai.com/v1", "gpt-4o")
        with self._patch_defaults(state, openai):
            web_shared._ensure_llm_session_defaults("alice")

        self.assertTrue(state[web_shared._LLM_PREFS_DIRTY_KEY])
        self.assertEqual(state[web_shared._LLM_PROVIDER_KEY], "Qwen / DashScope")
        self.assertEqual(state[web_shared._LLM_MODEL_CHOICE_KEY], "qwen3.6-plus")


if __name__ == "__main__":
    unittest.main()
