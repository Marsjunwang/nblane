"""Tests for modular AI Action / Gateway behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

from nblane.core.ai import (
    create_remote_dev_task,
    crystallize_done_tasks,
    deep_read_paper_codex,
    draft_kanban_subtasks,
    draft_resume_for_job,
    generate_paper_review_card,
    recommend_research_sources,
    run_ai_action,
    translate_paper_segments,
)
from nblane.core.ai.actions import AIActionRequest
from nblane.core.ai.backends import (
    DirectLLMBackend,
    LocalTranslationBackend,
    LocalReadonlyCodexBackend,
    RuleFallbackBackend,
    default_backends,
)
from nblane.core.codex_adapter import CodexConfig
from nblane.core.ai.router import get_action_spec, registered_actions
from nblane.core.ai.structured import validate_schema


class TestAIGateway(unittest.TestCase):
    """AI Gateway keeps business code off raw provider and harness APIs."""

    def test_mvp_actions_are_registered(self) -> None:
        """First AI Action batch is present in the registry."""

        self.assertEqual(
            set(registered_actions()),
            {
                "research.reading_draft",
                "research.recommend_sources",
                "research.paper_search_codex",
                "research.paper_translate",
                "research.paper_explain_selection",
                "research.paper_source_guide",
                "research.paper_review_card",
                "research.paper_qa",
                "research.paper_claim_extract",
                "research.paper_deep_read_codex",
                "research.paper_compare_codex",
                "resume.bullets_from_claims",
                "resume.target_for_job",
                "output.blog_candidate",
                "output.inline_patch",
                "kanban.task_alignment",
                "kanban.subtasks",
                "evidence.crystallize",
                "project.suggest_refs",
                "work.remote_dev_task",
                "gap.skill_coach",
                "gap.task_routing",
                "profile.resume_ingest",
                "profile.kanban_ingest",
                "output.visual_caption",
                "dashboard.daily_brief",
                "divination.cast",
            },
        )

    def test_direct_backend_missing_key_returns_typed_error(self) -> None:
        """Direct LLM backend does not raise when the provider is unconfigured."""

        spec = get_action_spec("research.reading_draft")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="research.reading_draft",
            profile="alice",
            payload={"source": {"id": "src_1", "title": "Paper"}},
        )
        with patch("nblane.core.llm._API_KEY", ""):
            result = DirectLLMBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertFalse(result.ok)
        self.assertEqual(result.backend, "direct_llm")
        self.assertIn("ai_not_configured", result.error)

    def test_crystallize_action_uses_ingest_prompt_and_model(self) -> None:
        """The mature Kanban ingest protocol stays behind the new action."""

        spec = get_action_spec("evidence.crystallize")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="evidence.crystallize",
            profile="alice",
            payload={
                "done_tasks": [SimpleNamespace(id="task-1")],
                "ai_model": "qwen-plus",
                "timeout_seconds": 12,
            },
        )
        with patch(
            "nblane.core.profile_ingest_llm.ingest_kanban_done_json",
            return_value=({"evidence_entries": [], "node_updates": []}, None),
        ) as ingest:
            result = DirectLLMBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "direct_llm")
        self.assertEqual(ingest.call_args.kwargs["model"], "qwen-plus")
        self.assertEqual(ingest.call_args.kwargs["timeout_seconds"], 12.0)
        self.assertEqual(ingest.call_args.kwargs["ai_backend"], "llm")

    def test_crystallize_preference_selects_codex_and_model(self) -> None:
        """Profile action preferences choose Codex without a rule fallback."""

        with (
            patch(
                "nblane.core.ai.gateway.load_web_preferences",
                return_value={
                    "ai": {
                        "actions": {
                            "evidence.crystallize": {
                                "backend": "codex",
                                "codex_model": "gpt-5.1-codex",
                            }
                        }
                    }
                },
            ),
            patch("nblane.core.ai.gateway.run_ai_action") as run,
        ):
            run.return_value = SimpleNamespace(ok=True)
            crystallize_done_tasks("alice", [SimpleNamespace(id="task-1")])

        self.assertEqual(run.call_args.args[0], "evidence.crystallize")
        self.assertEqual(run.call_args.kwargs["preferred_backend"], "local_codex_readonly")
        self.assertEqual(run.call_args.args[1]["codex_model"], "gpt-5.1-codex")

    def test_deep_read_settings_effort_reaches_codex(self) -> None:
        """A settings-page effort beats the deep-read default but not the caller."""

        readonly = SimpleNamespace(
            ok=True,
            output='{"verdict": {}, "method": {}, "experiments": {}, "claims": [], "sections": [], "warnings": []}',
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex exec --sandbox read-only -",
        )
        prefs = {
            "ai": {
                "actions": {
                    "research.paper_deep_read_codex": {
                        "backend": "",
                        "codex_model": "gpt-6.1-sol",
                        "codex_effort": "medium",
                    }
                }
            }
        }
        with (
            patch("nblane.core.ai.gateway.load_web_preferences", return_value=prefs),
            patch("nblane.core.codex_adapter.run_readonly_codex_prompt", return_value=readonly) as run,
        ):
            from_settings = deep_read_paper_codex("alice", "source:paper:1", payload={})
            from_caller = deep_read_paper_codex(
                "alice", "source:paper:1", payload={"codex_reasoning_effort": "xhigh"}
            )

        self.assertTrue(from_settings.ok)
        first, second = run.call_args_list
        self.assertEqual(first.kwargs["reasoning_effort"], "medium")
        self.assertEqual(first.kwargs["config"].model, "gpt-6.1-sol")
        self.assertEqual(second.kwargs["reasoning_effort"], "xhigh")
        self.assertTrue(from_caller.ok)

    def test_deep_read_effort_defaults_to_high_without_settings(self) -> None:
        readonly = SimpleNamespace(
            ok=True,
            output='{"verdict": {}, "method": {}, "experiments": {}, "claims": [], "sections": [], "warnings": []}',
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex exec --sandbox read-only -",
        )
        with (
            patch("nblane.core.ai.gateway.load_web_preferences", return_value={}),
            patch("nblane.core.codex_adapter.run_readonly_codex_prompt", return_value=readonly) as run,
        ):
            deep_read_paper_codex("alice", "source:paper:1", payload={})

        self.assertEqual(run.call_args.kwargs["reasoning_effort"], "high")

    def test_direct_backend_passes_per_action_model_override(self) -> None:
        """Paper action model preferences are handed to the LLM client."""

        spec = get_action_spec("research.paper_translate")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="research.paper_translate",
            profile="",
            payload={
                "source_id": "source:paper:1",
                "ai_model": "qwen-plus",
                "model_timeout_seconds": 11,
                "segments": [
                    {
                        "segment_id": "seg:1",
                        "text": "hello",
                        "text_hash": "sha256:abc",
                    }
                ],
            },
        )
        with (
            patch("nblane.core.llm.is_configured", return_value=True),
            patch(
                "nblane.core.llm.chat",
                return_value='{"translations":[{"segment_id":"seg:1","source_hash":"sha256:abc","translated_text":"你好"}],"warnings":[],"ref":"paper:1"}',
            ) as chat,
        ):
            result = DirectLLMBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertTrue(result.ok)
        self.assertEqual(chat.call_args.kwargs["model"], "qwen-plus")
        self.assertEqual(chat.call_args.kwargs["timeout"], 11.0)
        self.assertTrue(chat.call_args.kwargs["stream"])

    def test_direct_backend_passes_max_retries_override(self) -> None:
        """Interactive actions can disable the SDK's silent retry-on-timeout."""

        spec = get_action_spec("divination.cast")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="divination.cast",
            profile="",
            payload={"llm_max_retries": 0, "llm_timeout_seconds": 90},
        )
        with (
            patch("nblane.core.llm.is_configured", return_value=True),
            patch(
                "nblane.core.llm.chat",
                return_value='{"judgment":"判","reading":"解"}',
            ) as chat,
        ):
            result = DirectLLMBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertTrue(result.ok)
        self.assertEqual(chat.call_args.kwargs["max_retries"], 0)
        self.assertEqual(chat.call_args.kwargs["timeout"], 90.0)

    def test_direct_backend_defaults_max_retries_to_sdk(self) -> None:
        """Without an override the SDK default (2 retries) is left in place."""

        spec = get_action_spec("divination.cast")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="divination.cast",
            profile="",
            payload={},
        )
        with (
            patch("nblane.core.llm.is_configured", return_value=True),
            patch(
                "nblane.core.llm.chat",
                return_value='{"judgment":"判","reading":"解"}',
            ) as chat,
        ):
            result = DirectLLMBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertTrue(result.ok)
        self.assertIsNone(chat.call_args.kwargs["max_retries"])

    def test_direct_backend_can_disable_streaming_paper_translation(self) -> None:
        """Operators can temporarily return paper translation to non-streaming HTTP."""

        spec = get_action_spec("research.paper_translate")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="research.paper_translate",
            profile="",
            payload={
                "source_id": "source:paper:1",
                "model_timeout_seconds": 11,
                "segments": [
                    {
                        "segment_id": "seg:1",
                        "text": "hello",
                        "text_hash": "sha256:abc",
                    }
                ],
            },
        )
        with (
            patch.dict("os.environ", {"NBLANE_STREAM_PAPER_TRANSLATION": "0"}),
            patch("nblane.core.llm.is_configured", return_value=True),
            patch(
                "nblane.core.llm.chat",
                return_value='{"translations":[{"segment_id":"seg:1","source_hash":"sha256:abc","translated_text":"你好"}],"warnings":[],"ref":"paper:1"}',
            ) as chat,
        ):
            result = DirectLLMBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertTrue(result.ok)
        self.assertFalse(chat.call_args.kwargs["stream"])

    def test_direct_backend_streams_paper_review_card(self) -> None:
        """Whole-paper analysis streams so slow generations do not hit the read timeout."""

        spec = get_action_spec("research.paper_review_card")
        request = AIActionRequest(
            action="research.paper_review_card",
            profile="",
            payload={"source_id": "source:paper:1", "model_timeout_seconds": 300},
        )
        with (
            patch("nblane.core.llm.is_configured", return_value=True),
            patch("nblane.core.llm.chat", return_value="LLM error: boom") as chat,
        ):
            DirectLLMBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertTrue(chat.call_args.kwargs["stream"])
        self.assertEqual(chat.call_args.kwargs["timeout"], 300.0)

    def test_review_card_sets_analysis_timeout_and_one_retry(self) -> None:
        with (
            patch("nblane.core.ai.gateway.load_web_preferences", return_value={}),
            patch("nblane.core.ai.gateway.run_ai_action") as run,
        ):
            run.return_value = SimpleNamespace(ok=True)
            generate_paper_review_card("alice", "source:paper:1", require_review=False)

        payload = run.call_args.args[1]
        self.assertEqual(payload["model_timeout_seconds"], 300.0)
        self.assertEqual(payload["llm_max_retries"], 1)
        self.assertEqual(payload["llm_max_tokens"], 16384)

    def test_direct_backend_reports_truncated_json_output(self) -> None:
        """finish_reason=length with broken JSON names the token ceiling."""

        spec = get_action_spec("research.paper_review_card")
        request = AIActionRequest(
            action="research.paper_review_card",
            profile="",
            payload={"source_id": "source:paper:1", "llm_max_tokens": 4096},
        )

        def fake_chat(*args, **kwargs):
            kwargs["meta_out"]["finish_reason"] = "length"
            return '{"tldr": "cut off'

        with (
            patch("nblane.core.llm.is_configured", return_value=True),
            patch("nblane.core.llm.chat", side_effect=fake_chat) as chat,
        ):
            result = DirectLLMBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertFalse(result.ok)
        self.assertEqual(chat.call_args.kwargs["max_tokens"], 4096)
        self.assertTrue(result.error.startswith("output_truncated:"))
        self.assertIn("4096", result.error)

    def test_translate_paper_segments_sets_long_translation_timeout(self) -> None:
        """Full-paper translation batches should not inherit short UI polling limits."""

        with (
            patch("nblane.core.ai.gateway.load_web_preferences", return_value={}),
            patch("nblane.core.ai.gateway.run_ai_action") as run,
        ):
            run.return_value = SimpleNamespace(ok=True)
            translate_paper_segments(
                "alice",
                "source:paper:1",
                [{"segment_id": "seg:1", "text": "hello", "text_hash": "sha256:abc"}],
                require_review=False,
            )

        payload = run.call_args.args[1]
        self.assertEqual(payload["model_timeout_seconds"], 180.0)

    def test_translate_paper_segments_honors_timeout_override(self) -> None:
        """Callers can still tune one paper translation request explicitly."""

        with (
            patch("nblane.core.ai.gateway.load_web_preferences", return_value={}),
            patch("nblane.core.ai.gateway.run_ai_action") as run,
        ):
            run.return_value = SimpleNamespace(ok=True)
            translate_paper_segments(
                "alice",
                "source:paper:1",
                [{"segment_id": "seg:1", "text": "hello", "text_hash": "sha256:abc"}],
                model_timeout_seconds=240,
                require_review=False,
            )

        payload = run.call_args.args[1]
        self.assertEqual(payload["model_timeout_seconds"], 240)

    def test_local_readonly_codex_backend_registered_for_paper_actions(self) -> None:
        """Paper Codex actions default to local read-only Codex, not handoff."""

        registry = default_backends()

        self.assertIn("local_codex_readonly", registry)
        self.assertIsInstance(registry["local_codex_readonly"], LocalReadonlyCodexBackend)
        for action in (
            "research.paper_search_codex",
            "research.paper_deep_read_codex",
            "research.paper_compare_codex",
        ):
            spec = get_action_spec(action)
            self.assertIsNotNone(spec)
            self.assertEqual(spec.default_backend, "local_codex_readonly")  # type: ignore[union-attr]
            self.assertEqual(spec.fallback_backend, "rule_fallback")  # type: ignore[union-attr]
        self.assertEqual(
            get_action_spec("research.paper_translate").default_backend,  # type: ignore[union-attr]
            "direct_llm",
        )

    def test_local_translation_backend_is_registered_without_being_required(self) -> None:
        registry = default_backends()
        self.assertIsInstance(registry["local_translation"], LocalTranslationBackend)

    def test_local_translation_backend_returns_structured_rows(self) -> None:
        spec = get_action_spec("research.paper_translate")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="research.paper_translate",
            profile="alice",
            payload={
                "source_id": "source:paper:1",
                "target_lang": "zh",
                "segments": [{
                    "segment_id": "seg:1",
                    "source_hash": "sha256:abc",
                    "text": "The model is fast.",
                }],
            },
        )
        with (
            patch("nblane.core.ai.backends.local_translation_available", return_value=True),
            patch(
                "nblane.core.ai.backends.translate_local_segments",
                return_value=[{
                    "segment_id": "seg:1",
                    "source_hash": "sha256:abc",
                    "translated_text": "模型很快。",
                }],
            ),
        ):
            result = LocalTranslationBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "local_translation")
        self.assertEqual(result.structured["translations"][0]["translated_text"], "模型很快。")  # type: ignore[index]

    def test_local_translation_is_selected_when_model_is_available(self) -> None:
        with patch("nblane.core.ai.gateway.local_translation_available", return_value=True):
            # The explicit backend is exercised through the gateway registry
            # below; this assertion verifies the auto-selection signal.
            with patch("nblane.core.ai.gateway.run_ai_action") as run:
                run.return_value = SimpleNamespace(ok=True, backend="local_translation")
                translate_paper_segments(
                    "alice",
                    "source:paper:1",
                    [{"segment_id": "seg:1", "text": "hello", "text_hash": "sha256:abc"}],
                    require_review=False,
                )
                self.assertEqual(run.call_args.kwargs["preferred_backend"], "local_translation")

    def test_local_readonly_codex_backend_parses_paper_search_json(self) -> None:
        """Gateway parses Codex's final JSON message as structured candidates."""

        reply = """
        {
          "query": "VLA memory",
          "results": [
            {
              "title": "Memory for Vision-Language-Action Models",
              "url": "https://example.com/paper",
              "provider_refs": ["semantic_scholar:abc"],
              "abstract": "The paper studies memory for embodied agents.",
              "ai_summary": "A plain-language overview for triage.",
              "explanation_links": [{"title": "Explainer", "url": "https://example.com/explainer"}],
              "reason": "Relevant memory architecture."
            }
          ],
          "warnings": ["Verify venue."],
          "ref": "paper-search:vla-memory"
        }
        """
        readonly = SimpleNamespace(
            ok=True,
            output=reply,
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex exec --sandbox read-only -",
        )
        with patch(
            "nblane.core.codex_adapter.run_readonly_codex_prompt",
            return_value=readonly,
        ) as run:
            result = run_ai_action(
                "research.paper_search_codex",
                {"query": "VLA memory"},
                profile="",
                require_review=False,
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "local_codex_readonly")
        self.assertEqual(result.structured["results"][0]["title"], "Memory for Vision-Language-Action Models")  # type: ignore[index]
        self.assertEqual(result.structured["results"][0]["ai_summary"], "A plain-language overview for triage.")  # type: ignore[index]
        self.assertIn("Verify venue.", result.warnings)
        prompt = run.call_args.args[1]
        self.assertIn("Codex is read-only", prompt)
        self.assertIn("explanation_links", prompt)
        self.assertIn("Do not edit files", prompt)
        self.assertIn("Do not generate patches", prompt)
        self.assertIn("Do not write profile facts", prompt)
        self.assertIn("Return one JSON object only", prompt)
        self.assertIn("Stop as soon as you have up to", prompt)
        self.assertIn("arXiv APIs", prompt)
        self.assertIn("user's query language", prompt)
        self.assertTrue(run.call_args.kwargs["enable_search"])
        self.assertEqual(run.call_args.kwargs["reasoning_effort"], "medium")

    def test_paper_search_codex_uses_terminal_codex_home_by_default(self) -> None:
        """Paper search should match the terminal/plugin Codex environment by default."""

        readonly = SimpleNamespace(
            ok=True,
            output='{"query":"VLA","results":[],"warnings":[],"ref":"search"}',
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex --search exec --sandbox read-only -",
        )
        with (
            patch("nblane.core.codex_adapter.current_config", return_value=CodexConfig()) as current_config,
            patch("nblane.core.codex_adapter.run_readonly_codex_prompt", return_value=readonly) as run,
        ):
            result = run_ai_action(
                "research.paper_search_codex",
                {"query": "vla最新论文", "reply_language": "zh"},
                profile="",
                runtime_profile="alice",
                require_review=False,
        )

        self.assertTrue(result.ok)
        current_config.assert_called_once_with(
            profile="alice",
            codex_home_policy="default",
        )
        self.assertIn("Use Chinese", run.call_args.args[1])

    def test_paper_search_codex_can_opt_into_profile_codex_home(self) -> None:
        """The older profile-isolated Codex home remains available explicitly."""

        readonly = SimpleNamespace(
            ok=True,
            output='{"query":"VLA","results":[],"warnings":[],"ref":"search"}',
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex --search exec --sandbox read-only -",
        )
        with (
            patch("nblane.core.codex_adapter.current_config", return_value=CodexConfig()) as current_config,
            patch("nblane.core.codex_adapter.run_readonly_codex_prompt", return_value=readonly),
        ):
            result = run_ai_action(
                "research.paper_search_codex",
                {"query": "vla最新论文", "codex_home_policy": "profile"},
                profile="",
                runtime_profile="alice",
                require_review=False,
            )

        self.assertTrue(result.ok)
        current_config.assert_called_once_with(
            profile="alice",
            codex_home_policy="profile",
        )

    def test_local_readonly_codex_backend_passes_model_override(self) -> None:
        """DeepRead can use a profile-selected Codex model."""

        reply = """
        {
          "reading_plan": [],
          "findings": [],
          "cited_segment_refs": [],
          "cited_chunk_refs": [],
          "cited_annotation_refs": [],
          "warnings": [],
          "ref": "paper:1"
        }
        """
        readonly = SimpleNamespace(
            ok=True,
            output=reply,
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex exec --sandbox read-only -",
        )
        with (
            patch("nblane.core.codex_adapter.current_config", return_value=CodexConfig(model="default-codex")),
            patch(
                "nblane.core.codex_adapter.run_readonly_codex_prompt",
                return_value=readonly,
            ) as run,
        ):
            result = run_ai_action(
                "research.paper_deep_read_codex",
                {"source_id": "source:paper:1", "codex_model": "gpt-5.1-codex"},
                profile="",
                require_review=False,
            )

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.kwargs["config"].model, "gpt-5.1-codex")
        self.assertEqual(run.call_args.kwargs["reasoning_effort"], "high")

    def test_deep_read_codex_respects_reasoning_effort_override(self) -> None:
        """Payload overrides still win over the deep-read high default."""

        reply = """
        {
          "reading_plan": [],
          "findings": [],
          "cited_segment_refs": [],
          "cited_chunk_refs": [],
          "cited_annotation_refs": [],
          "warnings": [],
          "ref": "paper:1"
        }
        """
        readonly = SimpleNamespace(
            ok=True,
            output=reply,
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex exec --sandbox read-only -",
        )
        with patch(
            "nblane.core.codex_adapter.run_readonly_codex_prompt",
            return_value=readonly,
        ) as run:
            result = run_ai_action(
                "research.paper_deep_read_codex",
                {
                    "source_id": "source:paper:1",
                    "codex_reasoning_effort": "xhigh",
                },
                profile="",
                require_review=False,
            )

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.kwargs["reasoning_effort"], "xhigh")

    def test_local_readonly_codex_backend_passes_timeout_override(self) -> None:
        """UI actions can cap read-only Codex latency before fallback."""

        readonly = SimpleNamespace(
            ok=True,
            output='{"query":"VLA memory","results":[],"warnings":[],"ref":"search"}',
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex exec --sandbox read-only -",
        )
        with patch(
            "nblane.core.codex_adapter.run_readonly_codex_prompt",
            return_value=readonly,
        ) as run:
            events: list[dict[str, object]] = []
            progress_callback = events.append
            cancelled = False
            result = run_ai_action(
                "research.paper_search_codex",
                {
                    "query": "VLA memory",
                    "codex_timeout_seconds": 7,
                    "codex_idle_timeout_seconds": 3,
                    "codex_reasoning_effort": "xhigh",
                },
                profile="",
                require_review=False,
                progress_callback=progress_callback,
                cancel_callback=lambda: cancelled,
            )

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.kwargs["timeout_seconds"], 7.0)
        self.assertEqual(run.call_args.kwargs["idle_timeout_seconds"], 3.0)
        self.assertIs(run.call_args.kwargs["progress_callback"], progress_callback)
        self.assertIsNotNone(run.call_args.kwargs["cancel_check"])
        self.assertTrue(run.call_args.kwargs["enable_search"])
        self.assertEqual(run.call_args.kwargs["reasoning_effort"], "xhigh")

    def test_translate_paper_segments_can_use_profile_codex_backend(self) -> None:
        """Paper translation can route through Codex when the profile asks for it."""

        reply = """
        {
          "translations": [
            {
              "segment_id": "seg:1",
              "source_hash": "sha256:abc",
              "translated_text": "你好"
            }
          ],
          "warnings": [],
          "ref": "paper:1"
        }
        """
        readonly = SimpleNamespace(
            ok=True,
            output=reply,
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex exec --sandbox read-only -",
        )
        prefs = {
            "ai": {
                "paper": {
                    "translation_backend": "codex",
                    "translation_model": "gpt-5.1-codex",
                }
            }
        }
        with (
            patch("nblane.core.ai.gateway.load_web_preferences", return_value=prefs),
            patch("nblane.core.ai.gateway.record_activity_item", return_value=""),
            patch("nblane.core.ai.gateway.append_ai_run"),
            patch("nblane.core.codex_adapter.current_config", return_value=CodexConfig(model="default-codex")),
            patch(
                "nblane.core.codex_adapter.run_readonly_codex_prompt",
                return_value=readonly,
            ) as run,
        ):
            result = translate_paper_segments(
                "alice",
                "source:paper:1",
                [{"segment_id": "seg:1", "text": "hello", "text_hash": "sha256:abc"}],
                require_review=False,
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "local_codex_readonly")
        self.assertEqual(run.call_args.kwargs["config"].model, "gpt-5.1-codex")

    def test_action_matrix_can_route_paper_review_to_codex_model(self) -> None:
        """Feature-level preferences can pick Codex and a Codex model."""

        reply = """
        {
          "tldr": "Useful paper.",
          "key_points": [],
          "innovations": [],
          "method": [],
          "experiments": [],
          "limitations": [],
          "usefulness": "",
          "scores": {
            "novelty": 5,
            "technical_depth": 5,
            "evidence_quality": 5,
            "reproducibility": 5,
            "relevance": 5,
            "overall": 5
          },
          "score_rationale": [],
          "cited_segment_refs": [],
          "cited_chunk_refs": [],
          "cited_annotation_refs": [],
          "warnings": [],
          "ref": "source:paper:1"
        }
        """
        readonly = SimpleNamespace(
            ok=True,
            output=reply,
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex exec --sandbox read-only -",
        )
        prefs = {
            "ai": {
                "actions": {
                    "research.paper_review_card": {
                        "backend": "codex",
                        "codex_model": "gpt-5.1-codex",
                    }
                }
            }
        }
        with (
            patch("nblane.core.ai.gateway.load_web_preferences", return_value=prefs),
            patch("nblane.core.ai.gateway.record_activity_item", return_value=""),
            patch("nblane.core.ai.gateway.append_ai_run"),
            patch("nblane.core.codex_adapter.current_config", return_value=CodexConfig(model="default-codex")),
            patch(
                "nblane.core.codex_adapter.run_readonly_codex_prompt",
                return_value=readonly,
            ) as run,
        ):
            result = generate_paper_review_card(
                "alice",
                "source:paper:1",
                segments=[],
                require_review=False,
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "local_codex_readonly")
        self.assertEqual(run.call_args.kwargs["config"].model, "gpt-5.1-codex")

    def test_action_matrix_passes_kanban_llm_model_override(self) -> None:
        """Kanban subtask drafting can use a feature-selected LLM model."""

        prefs = {
            "ai": {
                "actions": {
                    "kanban.subtasks": {
                        "backend": "llm",
                        "llm_model": "qwen-max",
                    }
                }
            }
        }
        with (
            patch("nblane.core.ai.gateway.load_web_preferences", return_value=prefs),
            patch("nblane.core.llm.is_configured", return_value=True),
            patch(
                "nblane.core.llm.chat",
                return_value='{"subtasks":[{"title":"Draft evaluation table"}]}',
            ) as chat,
        ):
            result = draft_kanban_subtasks(
                "alice",
                task_id="task_1",
                task_title="Evaluate VLA paper",
                task_text="Evaluate VLA paper",
                existing_subtasks="- (none)",
                gap_analysis="No gap.",
                allowed_gap_ids=[],
                require_review=False,
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "direct_llm")
        self.assertEqual(chat.call_args.kwargs["model"], "qwen-max")

    def test_local_readonly_codex_invalid_json_falls_back_with_warning(self) -> None:
        """Malformed Codex output is converted to a typed warning/fallback."""

        readonly = SimpleNamespace(
            ok=True,
            output="not json",
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex exec --sandbox read-only -",
        )
        with patch(
            "nblane.core.codex_adapter.run_readonly_codex_prompt",
            return_value=readonly,
        ):
            result = run_ai_action(
                "research.paper_search_codex",
                {"query": "VLA memory"},
                profile="",
                require_review=False,
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "rule_fallback")
        self.assertIn("local_codex_readonly failed", result.warnings[0])
        self.assertIn("codex_json_error", result.warnings[0])

    def test_codex_timeout_diagnostics_survive_fallback(self) -> None:
        """Reconnect / last-output notes from a timed-out Codex run reach the job warnings."""

        readonly = SimpleNamespace(
            ok=False,
            output="",
            warnings=["Codex stream reconnected 3 time(s); the provider connection was unstable."],
            error="command_timeout: exceeded 960s",
            stdout="",
            stderr="",
            command="codex exec --sandbox read-only -",
        )
        with patch(
            "nblane.core.codex_adapter.run_readonly_codex_prompt",
            return_value=readonly,
        ):
            result = run_ai_action(
                "research.paper_search_codex",
                {"query": "VLA memory"},
                profile="",
                require_review=False,
            )

        self.assertEqual(result.backend, "rule_fallback")
        self.assertIn("command_timeout", result.warnings[0])
        self.assertIn("reconnected 3 time(s)", result.warnings[1])

    def test_rule_fallback_returns_deterministic_result(self) -> None:
        """Rule fallback can provide a usable empty/candidate state."""

        spec = get_action_spec("research.recommend_sources")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="research.recommend_sources",
            profile="alice",
            payload={
                "sources": [
                    {"id": "src_a", "title": "A"},
                    {"id": "src_b", "title": "B"},
                ]
            },
        )
        result = RuleFallbackBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "rule_fallback")
        self.assertEqual(
            result.structured["recommendations"][0]["source_ref"],  # type: ignore[index]
            "src_a",
        )

    def test_paper_fallback_actions_are_candidate_first_with_refs(self) -> None:
        """Paper Reading Studio fallback outputs stay reviewable and traceable."""

        paper_actions = [
            "research.paper_search_codex",
            "research.paper_translate",
            "research.paper_explain_selection",
            "research.paper_source_guide",
            "research.paper_review_card",
            "research.paper_qa",
            "research.paper_claim_extract",
            "research.paper_deep_read_codex",
            "research.paper_compare_codex",
        ]
        for action in paper_actions:
            spec = get_action_spec(action)
            self.assertIsNotNone(spec)
            self.assertEqual(spec.activity_policy, "candidate")  # type: ignore[union-attr]
            request = AIActionRequest(
                action=action,
                profile="alice",
                payload={
                    "source_id": "source:paper:1",
                    "segments": [
                        {
                            "segment_id": "seg:paper:1:0001",
                            "text_hash": "sha256:abc",
                            "text": "The method uses a memory encoder.",
                        }
                    ],
                },
                context_refs=["source:paper:1"],
            )
            result = RuleFallbackBackend().run(request, spec)  # type: ignore[arg-type]

            self.assertTrue(result.ok)
            self.assertIsInstance(result.structured, dict)
            self.assertIn("warnings", result.structured)  # type: ignore[operator]
            self.assertIn("ref", result.structured)  # type: ignore[operator]
            self.assertEqual(result.structured["ref"], "source:paper:1")  # type: ignore[index]
            self.assertTrue(result.structured["warnings"])  # type: ignore[index]

    def test_paper_translation_fallback_preserves_segment_hash(self) -> None:
        """Translation candidates include stable alignment keys for cache safety."""

        spec = get_action_spec("research.paper_translate")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="research.paper_translate",
            profile="alice",
            payload={
                "source_id": "source:paper:1",
                "target_lang": "zh",
                "segments": [
                    {
                        "segment_id": "seg:paper:1:0001",
                        "source_hash": "sha256:known",
                        "text": "The memory encoder stores observations.",
                    }
                ],
            },
        )
        result = RuleFallbackBackend().run(request, spec)  # type: ignore[arg-type]

        row = result.structured["translations"][0]  # type: ignore[index]
        self.assertEqual(row["segment_id"], "seg:paper:1:0001")
        self.assertEqual(row["source_hash"], "sha256:known")
        self.assertEqual(row["target_lang"], "zh")

    def test_deep_read_fallback_returns_empty_v2_shell(self) -> None:
        """Without Codex, deep read returns a valid empty shell, not a keyword skeleton."""

        spec = get_action_spec("research.paper_deep_read_codex")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="research.paper_deep_read_codex",
            profile="alice",
            payload={
                "source_id": "source:paper:1",
                "source": {"id": "source:paper:1", "title": "Tiny Transformer"},
                "paper_markdown": "# Tiny Transformer\n\nAttention only. 〔s1〕\n",
            },
            context_refs=["source:paper:1"],
        )

        result = RuleFallbackBackend().run(request, spec)  # type: ignore[arg-type]
        structured = result.structured

        self.assertTrue(result.ok)
        self.assertEqual(validate_schema(structured, spec.schema), "")  # type: ignore[arg-type, union-attr]
        self.assertIn("Tiny Transformer", structured["verdict"]["summary"])  # type: ignore[index]
        self.assertEqual(structured["claims"], [])  # type: ignore[index]
        self.assertEqual(structured["method"]["components"], [])  # type: ignore[index]
        self.assertIn("没有生成替代内容", " ".join(structured["warnings"]))  # type: ignore[index]

    def test_paper_translation_schema_accepts_scope_ref_only_layout_rows(self) -> None:
        """Layout providers may key rows by scope_ref instead of segment_id."""

        spec = get_action_spec("research.paper_translate")
        self.assertIsNotNone(spec)
        error = validate_schema(
            {
                "translations": [
                    {
                        "scope_type": "layout",
                        "scope_ref": "layout:v2:1:00001:abc123",
                        "source_hash": "sha256:known",
                        "translated_text": "定位译文。",
                        "target_lang": "zh",
                    }
                ],
                "warnings": [],
                "ref": "source:paper:1",
            },
            spec.schema,  # type: ignore[union-attr]
        )

        self.assertEqual(error, "")

    def test_paper_qa_without_input_refs_warns_and_does_not_guess(self) -> None:
        """Paper QA fallback refuses unsupported answers."""

        spec = get_action_spec("research.paper_qa")
        self.assertIsNotNone(spec)
        request = AIActionRequest(
            action="research.paper_qa",
            profile="alice",
            payload={"question": "What is the main result?"},
            context_refs=[],
        )
        result = RuleFallbackBackend().run(request, spec)  # type: ignore[arg-type]

        self.assertEqual(result.structured["answer"], "")  # type: ignore[index]
        self.assertIn("No input refs were provided", " ".join(result.warnings))

    def test_gateway_uses_action_default_backend(self) -> None:
        """run_ai_action routes through the action spec backend."""

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
                patch("nblane.core.ai.runs.profile_dir", lambda _name: profile),
            ):
                result = recommend_research_sources(
                    "alice",
                    "robotics",
                    [{"id": "src_1", "title": "OpenVLA"}],
                )

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "workflow_agent")
        self.assertEqual(result.activity_item_id.startswith("act:ai:"), True)

    def test_preferred_backend_unknown_is_explicit_error(self) -> None:
        """Invalid overrides fail clearly instead of silently picking a model."""

        result = run_ai_action(
            "research.recommend_sources",
            {"sources": []},
            profile="",
            preferred_backend="missing_backend",
            require_review=False,
        )

        self.assertFalse(result.ok)
        self.assertIn("routing_error", result.error)
        self.assertIn("missing_backend", result.error)

    def test_json_action_bad_output_returns_validation_error(self) -> None:
        """Business callers never have to parse malformed raw JSON."""

        with (
            patch("nblane.core.llm._API_KEY", "test-key"),
            patch("nblane.core.llm.chat", return_value="not json"),
        ):
            result = run_ai_action(
                "resume.bullets_from_claims",
                {"claims": []},
                profile="",
                require_review=False,
            )

        self.assertFalse(result.ok)
        self.assertEqual(result.backend, "direct_llm")
        self.assertIn("validation_error", result.error)

    def test_typed_resume_helper_returns_traceable_candidate(self) -> None:
        """Typed helpers expose action results without provider details."""

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
                patch("nblane.core.ai.runs.profile_dir", lambda _name: profile),
            ):
                result = draft_resume_for_job(
                    "alice",
                    "Need robotics engineer",
                    claims=[{"id": "claim_1", "text": "Built ROS demo"}],
                    evidence=[{"id": "ev_1"}],
                    projects=[{"id": "proj_1"}],
                )

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "workflow_agent")
        self.assertEqual(result.structured["claim_refs"], ["claim_1"])  # type: ignore[index]
        self.assertEqual(result.structured["evidence_refs"], ["ev_1"])  # type: ignore[index]
        self.assertEqual(result.structured["project_refs"], ["proj_1"])  # type: ignore[index]

    def test_remote_dev_task_creates_candidate_not_code_changes(self) -> None:
        """External agent action creates a task and Activity item only."""

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_tasks.profile_dir", lambda _name: profile),
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
                patch("nblane.core.ai.runs.profile_dir", lambda _name: profile),
            ):
                result = create_remote_dev_task(
                    "alice",
                    "Implement gateway tests",
                    target_harness="opencode",
                    input_refs=["kanban:task_1"],
                )

                from nblane.core.agent_activity import activity_items_for_page
                from nblane.core.agent_tasks import load_agent_tasks

                tasks = load_agent_tasks("alice")["tasks"]
                activity = activity_items_for_page(
                    "alice",
                    {"target_owner": "work"},
                )

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "external_agent")
        self.assertEqual(result.structured["target_harness"], "opencode")  # type: ignore[index]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["activity_item_id"], result.activity_item_id)
        self.assertEqual(activity[0]["kind"], "patch")
        self.assertEqual(activity[0]["changed_paths"], [])

    def test_paper_codex_preferred_external_agent_still_creates_handoff(self) -> None:
        """Explicit Paper handoff overrides still create external agent tasks."""

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_tasks.profile_dir", lambda _name: profile),
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
                patch("nblane.core.ai.runs.profile_dir", lambda _name: profile),
            ):
                result = run_ai_action(
                    "research.paper_search_codex",
                    {"query": "VLA memory"},
                    profile="alice",
                    preferred_backend="external_agent",
                )

                from nblane.core.agent_tasks import load_agent_tasks

                tasks = load_agent_tasks("alice")["tasks"]

        self.assertTrue(result.ok)
        self.assertEqual(result.backend, "external_agent")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["action_name"], "research.paper_search_codex")
        self.assertEqual(tasks[0]["activity_item_id"], result.activity_item_id)

    def test_paper_codex_success_activity_is_privacy_thin(self) -> None:
        """Paper Codex success Activity stores refs and counts, not raw content."""

        secret_segment = "PRIVATE SEGMENT TEXT SHOULD NOT BE STORED"
        reply = {
            "reading_plan": ["Read methods"],
            "findings": [{"text": secret_segment, "refs": ["seg:1"]}],
            "cited_segment_refs": ["seg:1"],
            "cited_chunk_refs": [],
            "cited_annotation_refs": [],
            "warnings": [],
            "ref": "source:paper:1",
        }
        readonly = SimpleNamespace(
            ok=True,
            output=__import__("json").dumps(reply),
            warnings=[],
            error="",
            stdout="",
            stderr="",
            command="codex exec --sandbox read-only -",
        )
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
                patch("nblane.core.ai.runs.profile_dir", lambda _name: profile),
                patch(
                    "nblane.core.codex_adapter.run_readonly_codex_prompt",
                    return_value=readonly,
                ),
            ):
                result = run_ai_action(
                    "research.paper_deep_read_codex",
                    {
                        "source_id": "source:paper:1",
                        "segments": [{"segment_id": "seg:1", "text": secret_segment}],
                    },
                    profile="alice",
                    context_refs=["source:paper:1"],
                    require_review=True,
                )
                activity_text = (profile / "agent-activity.yaml").read_text(encoding="utf-8")

        self.assertTrue(result.ok)
        self.assertNotIn(secret_segment, activity_text)
        self.assertNotIn("action_result", activity_text)
        self.assertNotIn("content:", activity_text)
        self.assertNotIn("command", activity_text)
        self.assertNotIn("stdout", activity_text)
        self.assertNotIn("stderr", activity_text)
        self.assertNotIn("raw_text", activity_text)

    def test_paper_codex_failure_activity_is_privacy_thin(self) -> None:
        """Paper Codex failure Activity stores a short error only."""

        secret_raw = "RAW CODEX OUTPUT SHOULD NOT BE STORED"
        readonly = SimpleNamespace(
            ok=False,
            output=secret_raw,
            warnings=[],
            error="config parse failed",
            stdout=f"stdout {secret_raw}",
            stderr="invalid config",
            command="codex exec --sandbox read-only -",
        )
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
                patch("nblane.core.ai.runs.profile_dir", lambda _name: profile),
                patch(
                    "nblane.core.codex_adapter.run_readonly_codex_prompt",
                    return_value=readonly,
                ),
            ):
                result = run_ai_action(
                    "research.paper_search_codex",
                    {"query": "VLA memory"},
                    profile="alice",
                    preferred_backend="local_codex_readonly",
                    require_review=True,
                )
                activity = yaml.safe_load(
                    (profile / "agent-activity.yaml").read_text(encoding="utf-8")
                )

        item = activity["items"][0]
        dumped = yaml.dump(item, allow_unicode=True)
        self.assertFalse(result.ok)
        self.assertEqual(item["status"], "failed")
        self.assertEqual(item["payload"]["provider"], "local_codex_readonly")
        self.assertLessEqual(len(item["summary"]), 240)
        self.assertLessEqual(len(item["preview"]), 300)
        self.assertNotIn(secret_raw, dumped)
        for key in ("command", "stdout", "stderr", "raw_text"):
            self.assertNotIn(key, item["payload"])


if __name__ == "__main__":
    unittest.main()
