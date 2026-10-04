"""Tests for the optional CPU-local translation runtime."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.ai import local_translation


class TestLocalTranslation(unittest.TestCase):
    def test_missing_model_is_unavailable_without_importing_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(
                "os.environ",
                {
                    "NBLANE_LOCAL_TRANSLATION_ENABLED": "1",
                    "NBLANE_LOCAL_TRANSLATION_MODEL": str(Path(tmp) / "missing"),
                },
                clear=False,
            ):
                state = local_translation.status()

        self.assertFalse(state.available)
        self.assertIn("does not exist", state.reason)

    def test_model_directory_requires_converter_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp)
            (model / "config.json").write_text("{}", encoding="utf-8")
            (model / "model.bin").write_bytes(b"model")
            with patch.dict(
                "os.environ",
                {
                    "NBLANE_LOCAL_TRANSLATION_ENABLED": "1",
                    "NBLANE_LOCAL_TRANSLATION_MODEL": str(model),
                },
                clear=False,
            ):
                state = local_translation.status()

        self.assertFalse(state.available)
        self.assertIn("source.spm", state.reason)

    def test_disabled_model_never_reports_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp)
            for name in ("config.json", "model.bin", "source.spm", "target.spm"):
                (model / name).write_bytes(b"x")
            with patch.dict(
                "os.environ",
                {
                    "NBLANE_LOCAL_TRANSLATION_ENABLED": "0",
                    "NBLANE_LOCAL_TRANSLATION_MODEL": str(model),
                },
                clear=False,
            ):
                state = local_translation.status()

        self.assertFalse(state.available)
        self.assertEqual(state.reason, "disabled")

    def test_raw_transformers_directory_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp)
            for name in ("config.json", "pytorch_model.bin", "source.spm", "target.spm"):
                (model / name).write_bytes(b"x")
            with patch.dict(
                "os.environ",
                {
                    "NBLANE_LOCAL_TRANSLATION_ENABLED": "1",
                    "NBLANE_LOCAL_TRANSLATION_MODEL": str(model),
                },
                clear=False,
            ):
                state = local_translation.status()

        self.assertTrue(state.available)
        self.assertEqual(state.engine, "transformers")

    def test_ctranslate2_directory_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp)
            for name in ("config.json", "model.bin", "source.spm", "target.spm"):
                (model / name).write_bytes(b"x")
            with patch.dict(
                "os.environ",
                {
                    "NBLANE_LOCAL_TRANSLATION_ENABLED": "1",
                    "NBLANE_LOCAL_TRANSLATION_MODEL": str(model),
                    "NBLANE_LOCAL_TRANSLATION_ENGINE": "ctranslate2",
                },
                clear=False,
            ):
                state = local_translation.status()

        self.assertTrue(state.available)
        self.assertEqual(state.engine, "ctranslate2")

    def test_transformers_runtime_returns_segment_rows(self) -> None:
        import torch

        class FakeTokenizer:
            def __call__(self, texts, **kwargs):
                return {"input_ids": torch.ones((len(texts), 2), dtype=torch.long)}

            def batch_decode(self, values, **kwargs):
                return ["翻译一", "翻译二"]

        class FakeModel:
            def generate(self, **kwargs):
                return torch.ones((2, 2), dtype=torch.long)

        runtime = local_translation._Runtime(
            "transformers", None, FakeTokenizer(), FakeTokenizer(), FakeModel()
        )
        segments = [
            {"segment_id": "s1", "text": "one", "text_hash": "h1"},
            {"segment_id": "s2", "text": "two", "text_hash": "h2"},
        ]
        with patch.object(local_translation, "_runtime", return_value=runtime):
            rows = local_translation.translate_segments(segments)

        self.assertEqual([row["translated_text"] for row in rows], ["翻译一", "翻译二"])
        self.assertEqual([row["source_hash"] for row in rows], ["h1", "h2"])

    def test_ctranslate2_runtime_returns_segment_rows(self) -> None:
        class FakeTokenizer:
            def encode(self, text, out_type=str):
                return [text]

            def decode(self, tokens):
                return f"译:{tokens[0]}"

        class FakeResult:
            def __init__(self, text):
                self.hypotheses = [[text]]

        class FakeTranslator:
            def translate_batch(self, source_tokens, **kwargs):
                return [FakeResult(tokens[0]) for tokens in source_tokens]

        runtime = local_translation._Runtime(
            "ctranslate2", FakeTranslator(), FakeTokenizer(), FakeTokenizer()
        )
        segments = [{"segment_id": "s1", "text": "one", "text_hash": "h1"}]
        with patch.object(local_translation, "_runtime", return_value=runtime):
            rows = local_translation.translate_segments(segments)

        self.assertEqual(rows[0]["translated_text"], "译:one")
        self.assertEqual(rows[0]["generated_by"], "local:opus-mt-en-zh")


if __name__ == "__main__":
    unittest.main()
