"""Tests for installable llama.cpp local translation models."""

from __future__ import annotations

import hashlib
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from nblane.core.ai import local_models, local_translation
from nblane.core.ai.gateway import translate_paper_segments


class _Response(io.BytesIO):
    def __init__(self, data: bytes, status: int = 200) -> None:
        super().__init__(data)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class LocalModelsTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = patch.dict(
            os.environ,
            {"NBLANE_LOCAL_MODELS_DIR": str(self.root), "NBLANE_LOCAL_MT_MODEL": ""},
        )
        self.env.start()
        self.spec = local_models.CATALOG[0]

    def tearDown(self) -> None:
        self.env.stop()
        self.tmp.cleanup()

    def _fake_install(self, spec: local_models.LocalModelSpec) -> None:
        path = local_models.model_path(spec)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as handle:
            handle.truncate(spec.size)
        binary = local_models.runtime_dir() / "llama-server"
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_text("#!/bin/sh\n")


class TestCatalogAndActivation(LocalModelsTestBase):
    def test_catalog_has_fit_and_quality_tiers_with_pins(self) -> None:
        tiers = {spec.tier for spec in local_models.CATALOG}
        self.assertEqual(tiers, {"fit", "quality"})
        for spec in local_models.CATALOG:
            self.assertRegex(spec.sha256, r"^[0-9a-f]{64}$")
            self.assertRegex(spec.revision, r"^[0-9a-f]{40}$")
            self.assertTrue(spec.filename.endswith(".gguf"))
            self.assertIn(spec.revision, spec.download_url())

    def test_hf_endpoint_mirror_is_honored(self) -> None:
        with patch.dict(os.environ, {"NBLANE_HF_ENDPOINT": "https://hf-mirror.example/"}):
            self.assertTrue(self.spec.download_url().startswith("https://hf-mirror.example/tencent/"))

    def test_not_active_until_installed_and_selected(self) -> None:
        self.assertIsNone(local_models.active_spec())
        with self.assertRaises(local_models.LocalModelError):
            local_models.set_active_model(self.spec.id)
        self._fake_install(self.spec)
        with patch.object(local_models, "total_ram_mb", return_value=4096):
            local_models.set_active_model(self.spec.id)
        self.assertEqual(local_models.active_spec(), self.spec)
        self.assertTrue(local_translation.is_available())
        self.assertEqual(local_translation.active_label(), f"local:{self.spec.id}")
        local_models.set_active_model("")
        self.assertIsNone(local_models.active_spec())

    def test_activation_refuses_models_larger_than_ram(self) -> None:
        big = next(spec for spec in local_models.CATALOG if spec.tier == "quality")
        self._fake_install(big)
        with patch.object(local_models, "total_ram_mb", return_value=3600):
            with self.assertRaisesRegex(local_models.LocalModelError, "内存不足"):
                local_models.set_active_model(big.id)
            self.assertIn("内存", local_models.install_blocker(big))

    def test_catalog_status_hides_sha_and_reports_state(self) -> None:
        status = local_models.catalog_status()
        self.assertEqual(len(status["models"]), len(local_models.CATALOG))
        self.assertNotIn("sha256", status["models"][0])
        self.assertFalse(status["active_ready"])
        self.assertIn("total_ram_mb", status["resources"])

    def test_delete_deactivates_and_removes_file(self) -> None:
        self._fake_install(self.spec)
        with patch.object(local_models, "total_ram_mb", return_value=4096):
            local_models.set_active_model(self.spec.id)
        local_models.delete_model(self.spec.id)
        self.assertFalse(local_models.model_path(self.spec).exists())
        self.assertEqual(local_models.active_model_id(), "")


class TestDownload(LocalModelsTestBase):
    def test_download_resumes_and_verifies_sha(self) -> None:
        data = b"x" * 3000 + b"y" * 2000
        target = self.root / "models" / "file.gguf"
        target.parent.mkdir(parents=True)
        target.with_name("file.gguf.part").write_bytes(data[:3000])
        seen: list[str] = []

        def fake_urlopen(request, timeout=0):
            seen.append(request.get_header("Range") or "")
            return _Response(data[3000:], status=206)

        with patch.object(local_models.urllib.request, "urlopen", side_effect=fake_urlopen):
            local_models._download_verified(
                "https://example/file", target, size=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
            )
        self.assertEqual(seen, ["bytes=3000-"])
        self.assertEqual(target.read_bytes(), data)

    def test_download_rejects_checksum_mismatch(self) -> None:
        target = self.root / "bad.gguf"
        with patch.object(local_models.urllib.request, "urlopen", return_value=_Response(b"abc")):
            with self.assertRaisesRegex(local_models.LocalModelError, "SHA-256"):
                local_models._download_verified("https://example/x", target, size=3, sha256="0" * 64)
        self.assertFalse(target.exists())
        self.assertFalse(target.with_name("bad.gguf.part").exists())

    def test_download_gives_up_after_network_errors(self) -> None:
        target = self.root / "net.gguf"
        with (
            patch.object(local_models.urllib.request, "urlopen", side_effect=urllib.error.URLError("down")),
            patch.object(local_models.time, "sleep"),
        ):
            with self.assertRaisesRegex(local_models.LocalModelError, "下载失败"):
                local_models._download_verified("https://example/x", target, size=3, sha256="0" * 64)


class TestTranslation(LocalModelsTestBase):
    def test_prompt_uses_official_template(self) -> None:
        self.assertEqual(
            local_models.build_prompt("Hello", "zh"),
            "将以下文本翻译为中文，注意只需要输出翻译后的结果，不要额外解释：\n\nHello",
        )
        self.assertIn("into Japanese", local_models.build_prompt("你好", "ja"))
        with self.assertRaises(local_models.LocalModelError):
            local_models.build_prompt("x", "xx")

    def test_translate_text_posts_chat_completion(self) -> None:
        captured: dict[str, object] = {}

        def fake_urlopen(request, timeout=0):
            captured["url"] = request.full_url
            captured["auth"] = request.get_header("Authorization")
            captured["body"] = json.loads(request.data)
            return _Response(json.dumps({"choices": [{"message": {"content": " 注意力 \n"}}]}).encode())

        with (
            patch.object(local_models, "ensure_server", return_value=("http://127.0.0.1:9", "k")),
            patch.object(local_models.urllib.request, "urlopen", side_effect=fake_urlopen),
        ):
            self.assertEqual(local_models.translate_text(self.spec, "attention"), "注意力")
        self.assertEqual(captured["url"], "http://127.0.0.1:9/v1/chat/completions")
        self.assertEqual(captured["auth"], "Bearer k")
        body = captured["body"]
        self.assertEqual(len(body["messages"]), 1)  # no system prompt
        self.assertEqual(body["messages"][0]["role"], "user")

    def test_local_translation_routes_segments_to_llama(self) -> None:
        self._fake_install(self.spec)
        with patch.object(local_models, "total_ram_mb", return_value=4096):
            local_models.set_active_model(self.spec.id)
        with patch.object(local_models, "translate_text", side_effect=lambda spec, text, target_lang: f"译:{text}"):
            rows = local_translation.translate_segments(
                [{"segment_id": "s1", "text": "hello", "text_hash": "h1", "scope_type": "segment", "scope_ref": "s1"}],
                target_lang="zh",
            )
        self.assertEqual(rows[0]["translated_text"], "译:hello")
        self.assertEqual(rows[0]["generated_by"], f"local:{self.spec.id}")
        self.assertEqual(rows[0]["source_hash"], "h1")


class TestScopeRouting(unittest.TestCase):
    def _run(self, scope: str, routes: dict[str, str] | None, *, available: bool = True, backend: str = "") -> str:
        prefs = {"ai": {"local_translation": routes or {}, "actions": {}}}
        with (
            patch("nblane.core.ai.gateway.local_translation_available", return_value=available),
            patch("nblane.core.ai.gateway.load_web_preferences", return_value=prefs),
            patch("nblane.core.ai.gateway._with_action_ai_preferences", return_value=({}, backend)),
            patch("nblane.core.ai.gateway.run_ai_action") as run,
        ):
            run.return_value = SimpleNamespace(ok=True)
            translate_paper_segments("alice", "src", [], scope=scope)
            return run.call_args.kwargs["preferred_backend"] or ""

    def test_default_routes_selection_and_visible_local_full_ai(self) -> None:
        self.assertEqual(self._run("selection", None), "local_translation")
        self.assertEqual(self._run("visible", None), "local_translation")
        self.assertEqual(self._run("full", None), "")

    def test_profile_routes_override_defaults(self) -> None:
        self.assertEqual(self._run("full", {"full": "local"}), "local_translation")
        self.assertEqual(self._run("selection", {"selection": "ai"}, backend="direct_llm"), "direct_llm")

    def test_local_route_beats_backend_preference_only_when_model_available(self) -> None:
        self.assertEqual(self._run("selection", None, backend="direct_llm"), "local_translation")
        self.assertEqual(self._run("selection", None, available=False, backend="direct_llm"), "direct_llm")


if __name__ == "__main__":
    unittest.main()
