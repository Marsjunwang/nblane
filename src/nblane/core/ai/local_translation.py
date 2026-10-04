"""Optional CPU-local neural translation for short paper passages.

The runtime is deliberately optional. A local Marian/OPUS-MT directory is
loaded only when ``NBLANE_LOCAL_TRANSLATION_MODEL`` points at a valid model
directory. Hugging Face Transformers is the default quality path for raw
PyTorch model directories; a pre-converted CTranslate2 directory remains
available for operators who explicitly choose that engine.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LOCAL_TRANSLATION_BACKEND = "local_translation"
DEFAULT_MAX_CHARS = 6000


@dataclass(frozen=True)
class LocalTranslationStatus:
    """Describe whether the optional local translator can be used."""

    enabled: bool
    available: bool
    model_path: str
    reason: str = ""
    engine: str = ""


@dataclass
class _Runtime:
    engine: str
    translator: Any
    source_tokenizer: Any
    target_tokenizer: Any
    model: Any = None


_RUNTIME: _Runtime | None = None
_RUNTIME_KEY = ""
_RUNTIME_LOCK = threading.RLock()


def _clean_env(name: str) -> str:
    return str(os.getenv(name, "") or "").strip()


def model_path() -> Path | None:
    value = _clean_env("NBLANE_LOCAL_TRANSLATION_MODEL")
    if not value:
        return None
    return Path(value).expanduser()


def enabled() -> bool:
    value = _clean_env("NBLANE_LOCAL_TRANSLATION_ENABLED").lower()
    if value in {"0", "false", "no", "off"}:
        return False
    # Auto mode is safe: no model path means no optional import or load.
    return value in {"1", "true", "yes", "on", "auto", ""}


def status() -> LocalTranslationStatus:
    path = model_path()
    if not enabled():
        return LocalTranslationStatus(False, False, str(path or ""), "disabled")
    if path is None:
        return LocalTranslationStatus(False, False, "", "model path is not configured")
    if not path.is_dir():
        return LocalTranslationStatus(False, False, str(path), "model directory does not exist")
    source_spm = path / "source.spm"
    target_spm = path / "target.spm"
    if not source_spm.is_file() or not target_spm.is_file():
        return LocalTranslationStatus(False, False, str(path), "source.spm and target.spm are required")
    if (path / "pytorch_model.bin").is_file() or (path / "model.safetensors").is_file():
        return LocalTranslationStatus(True, True, str(path), engine="transformers")
    if (path / "model.bin").is_file():
        engine = _clean_env("NBLANE_LOCAL_TRANSLATION_ENGINE").lower() or "ctranslate2"
        if engine != "ctranslate2":
            return LocalTranslationStatus(False, False, str(path), f"unsupported local engine: {engine}")
        return LocalTranslationStatus(True, True, str(path), engine="ctranslate2")
    return LocalTranslationStatus(False, False, str(path), "missing pytorch_model.bin, model.safetensors, or model.bin")


def is_available() -> bool:
    """Return whether the local model is configured and structurally valid."""

    return status().available


def _runtime() -> _Runtime:
    global _RUNTIME, _RUNTIME_KEY
    current = status()
    if not current.available:
        raise RuntimeError(current.reason or "local translation is unavailable")
    path = Path(current.model_path)
    key = f"{path}:{current.engine}:{_clean_env('NBLANE_LOCAL_TRANSLATION_COMPUTE_TYPE') or 'int8'}"
    with _RUNTIME_LOCK:
        if _RUNTIME is not None and _RUNTIME_KEY == key:
            return _RUNTIME
        threads = max(1, min(2, int(_clean_env("NBLANE_LOCAL_TRANSLATION_THREADS") or "2")))
        if current.engine == "transformers":
            try:
                import torch  # type: ignore[import-not-found]
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # type: ignore[import-not-found]
            except ImportError as exc:
                raise RuntimeError(
                    "local translation dependencies are missing; install "
                    "nblane[local-translation]"
                ) from exc
            torch.set_num_threads(threads)
            tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True)
            model = AutoModelForSeq2SeqLM.from_pretrained(str(path), local_files_only=True)
            model.eval()
            _RUNTIME = _Runtime("transformers", None, tokenizer, tokenizer, model)
        else:
            try:
                import ctranslate2  # type: ignore[import-not-found]
                import sentencepiece  # type: ignore[import-not-found]
            except ImportError as exc:
                raise RuntimeError(
                    "local translation dependencies are missing; install "
                    "nblane[local-translation]"
                ) from exc
            compute_type = _clean_env("NBLANE_LOCAL_TRANSLATION_COMPUTE_TYPE") or "int8"
            translator = ctranslate2.Translator(
                str(path), device="cpu", compute_type=compute_type,
                inter_threads=1, intra_threads=threads,
            )
            source_tokenizer = sentencepiece.SentencePieceProcessor(model_file=str(path / "source.spm"))
            target_tokenizer = sentencepiece.SentencePieceProcessor(model_file=str(path / "target.spm"))
            _RUNTIME = _Runtime("ctranslate2", translator, source_tokenizer, target_tokenizer)
        _RUNTIME_KEY = key
        return _RUNTIME


def _max_chars() -> int:
    try:
        value = int(_clean_env("NBLANE_LOCAL_TRANSLATION_MAX_CHARS") or DEFAULT_MAX_CHARS)
    except ValueError:
        value = DEFAULT_MAX_CHARS
    return max(200, min(12000, value))


def _beam_size() -> int:
    try:
        value = int(_clean_env("NBLANE_LOCAL_TRANSLATION_BEAM_SIZE") or "4")
    except ValueError:
        value = 4
    return max(2, min(5, value))


def translate_segments(
    segments: list[dict[str, Any]],
    *,
    target_lang: str = "zh",
) -> list[dict[str, Any]]:
    """Translate paper segments with a warm CPU-local model."""

    if target_lang.lower() not in {"zh", "zh-cn", "zh-hans", "zh-tw"}:
        raise RuntimeError("local OPUS-MT translator only supports English to Chinese")
    if not segments:
        return []
    runtime = _runtime()
    max_chars = _max_chars()
    texts: list[str] = []
    for segment in segments:
        text = str(segment.get("text") or segment.get("source_text") or "").strip()
        if not text:
            raise ValueError("local translation received an empty segment")
        if len(text) > max_chars:
            raise ValueError(f"local translation segment exceeds {max_chars} characters")
        texts.append(text)
    if runtime.engine == "transformers":
        import torch  # type: ignore[import-not-found]
        encoded = runtime.source_tokenizer(
            texts, return_tensors="pt", padding=True, truncation=True,
            max_length=512,
        )
        with torch.inference_mode():
            results = runtime.model.generate(
                **encoded,
                num_beams=_beam_size(),
                max_new_tokens=256,
            )
        decoded = runtime.source_tokenizer.batch_decode(results, skip_special_tokens=True)
    else:
        source_tokens = [runtime.source_tokenizer.encode(text, out_type=str) for text in texts]
        results = runtime.translator.translate_batch(
            source_tokens,
            beam_size=_beam_size(),
            return_scores=False,
            max_batch_size=max(1, min(4, len(source_tokens))),
            max_decoding_length=256,
        )
        decoded = [runtime.target_tokenizer.decode(item.hypotheses[0]).strip() for item in results]
    translations: list[dict[str, Any]] = []
    for segment, translated in zip(segments, decoded, strict=True):
        translated = str(translated or "").strip()
        translations.append(
            {
                "segment_id": str(segment.get("segment_id") or segment.get("id") or ""),
                "scope_type": str(segment.get("scope_type") or ""),
                "scope_ref": str(segment.get("scope_ref") or ""),
                "page": segment.get("page"),
                "order": segment.get("order"),
                "source_hash": str(segment.get("source_hash") or segment.get("text_hash") or ""),
                "source_text": texts[len(translations)],
                "target_lang": target_lang,
                "translated_text": translated,
                "generated_by": "local:opus-mt-en-zh",
            }
        )
    return translations


__all__ = [
    "LOCAL_TRANSLATION_BACKEND",
    "LocalTranslationStatus",
    "enabled",
    "is_available",
    "model_path",
    "status",
    "translate_segments",
]
