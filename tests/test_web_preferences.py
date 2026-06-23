"""Tests for profile-scoped Web UI preferences."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.web_preferences import (
    load_web_preferences,
    normalize_web_preferences,
    save_web_preferences,
    update_web_preferences,
    web_preferences_path,
)


class TestWebPreferences(unittest.TestCase):
    """Web preferences persist UI habits without storing secrets."""

    def test_missing_preferences_load_defaults(self) -> None:
        """Old profiles without web-preferences.yaml remain compatible."""

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            prefs = load_web_preferences(profile)

        self.assertEqual(prefs["profile"], "alice")
        self.assertEqual(prefs["ai"]["kanban_backend"], "")
        self.assertIn("research.paper_translate", prefs["ai"]["actions"])
        self.assertEqual(prefs["ai"]["actions"]["research.paper_translate"]["backend"], "")
        self.assertEqual(prefs["kanban"]["subtask_granularity"], "")
        # Board view toggles default to focus off, auto-dates on.
        self.assertFalse(prefs["kanban"]["focus_mode"])
        self.assertTrue(prefs["kanban"]["auto_dates"])

    def test_kanban_view_toggles_round_trip(self) -> None:
        """focus_mode/auto_dates persist as bools through normalization."""

        normalized = normalize_web_preferences(
            {"kanban": {"focus_mode": True, "auto_dates": False}},
            profile="alice",
        )
        self.assertIs(normalized["kanban"]["focus_mode"], True)
        self.assertIs(normalized["kanban"]["auto_dates"], False)
        # String-ish stored values coerce; unknown values fall back to default.
        coerced = normalize_web_preferences(
            {"kanban": {"focus_mode": "true", "auto_dates": "0"}},
            profile="alice",
        )
        self.assertIs(coerced["kanban"]["focus_mode"], True)
        self.assertIs(coerced["kanban"]["auto_dates"], False)
        fallback = normalize_web_preferences(
            {"kanban": {"focus_mode": "maybe"}},
            profile="alice",
        )
        self.assertIs(fallback["kanban"]["focus_mode"], False)
        self.assertIs(fallback["kanban"]["auto_dates"], True)


    def test_save_and_load_profile_scoped_preferences(self) -> None:
        """LLM and Kanban usage preferences are stored per profile."""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def pdir(name: str) -> Path:
                path = root / name
                path.mkdir(exist_ok=True)
                return path

            with (
                patch("nblane.core.web_preferences.profile_dir", pdir),
                patch("nblane.core.web_preferences.git_backup.record_change"),
            ):
                save_web_preferences(
                    "alice",
                    {
                        "ai": {
                            "llm": {
                                "provider": "OpenAI",
                                "base_url": "https://api.openai.com/v1",
                                "model": "gpt-4o",
                                "custom_model": "gpt-4o",
                                "ui_lang": "zh",
                                "reply_lang": "en",
                            },
                            "paper": {
                                "translation_backend": "codex",
                                "translation_model": "qwen-plus",
                                "deep_read_model": "gpt-5.1-codex",
                            },
                            "actions": {
                                "research.paper_review_card": {
                                    "backend": "codex",
                                    "codex_model": "gpt-5.1-codex",
                                },
                                "kanban.subtasks": {
                                    "backend": "llm",
                                    "llm_model": "qwen-max",
                                },
                            },
                            "kanban_backend": "codex",
                        },
                        "kanban": {
                            "subtask_granularity": "checklist",
                            "subtask_style_hint": "artifact-first",
                        },
                    },
                )
                update_web_preferences(
                    "bob",
                    {"ai": {"kanban_backend": "llm"}},
                )
                alice = load_web_preferences("alice")
                bob = load_web_preferences("bob")

        self.assertEqual(alice["ai"]["llm"]["provider"], "OpenAI")
        self.assertEqual(alice["ai"]["paper"]["translation_backend"], "codex")
        self.assertEqual(alice["ai"]["paper"]["translation_model"], "qwen-plus")
        self.assertEqual(alice["ai"]["paper"]["deep_read_model"], "gpt-5.1-codex")
        self.assertEqual(alice["ai"]["actions"]["research.paper_translate"]["backend"], "codex")
        self.assertEqual(alice["ai"]["actions"]["research.paper_translate"]["codex_model"], "qwen-plus")
        self.assertEqual(alice["ai"]["actions"]["research.paper_review_card"]["backend"], "codex")
        self.assertEqual(alice["ai"]["actions"]["research.paper_review_card"]["codex_model"], "gpt-5.1-codex")
        self.assertEqual(alice["ai"]["actions"]["kanban.subtasks"]["backend"], "llm")
        self.assertEqual(alice["ai"]["actions"]["kanban.subtasks"]["llm_model"], "qwen-max")
        self.assertEqual(alice["ai"]["kanban_backend"], "codex")
        self.assertEqual(alice["ai"]["actions"]["kanban.task_alignment"]["backend"], "codex")
        self.assertEqual(alice["kanban"]["subtask_granularity"], "checklist")
        self.assertEqual(alice["kanban"]["subtask_style_hint"], "artifact-first")
        self.assertEqual(bob["ai"]["kanban_backend"], "llm")
        self.assertEqual(bob["ai"]["actions"]["kanban.subtasks"]["backend"], "llm")
        self.assertNotEqual(web_preferences_path(root / "alice"), web_preferences_path(root / "bob"))

    def test_secret_like_fields_are_not_normalized_or_saved(self) -> None:
        """API keys, tokens, auth, cookies, and config text are stripped."""

        raw = {
            "ai": {
                "llm": {
                    "provider": "OpenAI",
                    "api_key": "sk-should-not-save",
                    "token": "tok",
                    "authorization": "Bearer nope",
                },
                "kanban_backend": "codex",
                "actions": {
                    "research.paper_translate": {
                        "backend": "llm",
                        "llm_model": "qwen-plus",
                        "api_key": "sk-should-not-save",
                    },
                    "research.paper_search_codex": {
                        "backend": "codex",
                        "codex_model": "gpt-5.1-codex",
                        "token": "tok",
                    },
                    "unknown.action": {
                        "backend": "codex",
                        "codex_model": "not-normalized",
                    },
                },
                "secret": {"nested": "nope"},
            },
            "kanban": {
                "subtask_granularity": "implementation",
                "subtask_style_hint": "small patches",
                "password": "nope",
            },
            "config_toml": "model = 'secret-adjacent'",
            "auth_json": {"token": "nope"},
        }

        normalized = normalize_web_preferences(raw, profile="alice")
        dumped = str(normalized)

        self.assertEqual(normalized["ai"]["llm"]["provider"], "OpenAI")
        self.assertEqual(normalized["ai"]["kanban_backend"], "codex")
        self.assertEqual(normalized["ai"]["actions"]["research.paper_translate"]["llm_model"], "qwen-plus")
        self.assertEqual(normalized["ai"]["actions"]["research.paper_search_codex"]["codex_model"], "gpt-5.1-codex")
        self.assertNotIn("unknown.action", normalized["ai"]["actions"])
        self.assertNotIn("sk-should-not-save", dumped)
        self.assertNotIn("authorization", dumped)
        self.assertNotIn("password", dumped)
        self.assertNotIn("config_toml", dumped)
        self.assertNotIn("auth_json", dumped)

    def test_evidence_review_ignored_output_candidates_are_whitelisted(self) -> None:
        """Evidence Review skip state survives normalization without secrets."""

        normalized = normalize_web_preferences(
            {
                "evidence_review": {
                    "ignored_output_candidates": [
                        {
                            "source_key": "blog:2026-04-29-tttt",
                            "source_kind": "blog",
                            "output_id": "2026-04-29-tttt",
                            "reason": "not_evidence",
                            "ignored_at": "2026-06-23T00:00:00+00:00",
                            "api_key": "sk-nope",
                        },
                        {
                            "source_kind": "output",
                            "output_id": "route-or-id",
                            "token": "tok-nope",
                        },
                        {
                            "source_kind": "output",
                            "output_id": "route-or-id",
                            "reason": "duplicate should be dropped",
                        },
                        {"source_kind": "bad", "output_id": "x"},
                    ]
                }
            },
            profile="alice",
        )

        ignored = normalized["evidence_review"]["ignored_output_candidates"]
        self.assertEqual(
            [item["source_key"] for item in ignored],
            ["blog:2026-04-29-tttt", "output:route-or-id"],
        )
        self.assertEqual(ignored[1]["reason"], "not_evidence")
        dumped = str(normalized)
        self.assertNotIn("sk-nope", dumped)
        self.assertNotIn("tok-nope", dumped)
        self.assertNotIn("api_key", dumped)

    def test_profile_name_is_owned_by_target_profile(self) -> None:
        """A patch cannot rewrite the owning profile name."""

        normalized = normalize_web_preferences(
            {"profile": "bob", "ai": {"kanban_backend": "codex"}},
            profile="alice",
        )

        self.assertEqual(normalized["profile"], "alice")

    def test_update_web_preferences_strips_secret_patch_fields(self) -> None:
        """Partial updates cannot smuggle secret keys into the profile file."""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def pdir(name: str) -> Path:
                path = root / name
                path.mkdir(exist_ok=True)
                return path

            with (
                patch("nblane.core.web_preferences.profile_dir", pdir),
                patch("nblane.core.web_preferences.git_backup.record_change"),
            ):
                update_web_preferences(
                    "alice",
                    {
                        "ai": {
                            "llm": {
                                "provider": "Custom",
                                "base_url": "http://localhost:11434/v1",
                                "api_key": "sk-nope",
                            },
                            "kanban_backend": "codex",
                        },
                    },
                )
                text = web_preferences_path("alice").read_text(encoding="utf-8")
                prefs = load_web_preferences("alice")

        self.assertEqual(prefs["ai"]["llm"]["provider"], "Custom")
        self.assertEqual(prefs["ai"]["kanban_backend"], "codex")
        self.assertNotIn("sk-nope", text)
        self.assertNotIn("api_key", text)


if __name__ == "__main__":
    unittest.main()
