"""Translation batches split when provider content moderation blocks them."""

from __future__ import annotations

import threading
from unittest.mock import patch

from nblane.core import research_papers
from nblane.core.ai.actions import AIActionResult

BLOCK = (
    "direct_llm failed (provider_error: LLM error: <400> InternalError.Algo.DataInspectionFailed: "
    "Output data may contain inappropriate content.); used rule_fallback."
)


def _result(rows: list[dict], *, blocked: bool = False) -> AIActionResult:
    return AIActionResult(
        ok=True,
        action="research.paper_translate",
        backend="rule_fallback" if blocked else "direct_llm",
        run_id="r",
        structured={"translations": rows},
        warnings=[BLOCK] if blocked else [],
    )


def _fake_gateway(_profile, _source, batch, **_kwargs):
    # Any batch containing the "names" segment is rejected wholesale.
    if any("Ryan Yu" in item["text"] for item in batch):
        return _result([{"segment_id": item["id"], "translated_text": ""} for item in batch], blocked=True)
    return _result([{"segment_id": item["id"], "translated_text": "译:" + item["text"]} for item in batch])


def _run(batches):
    calls = []

    def handle(batch, result, exc):
        calls.append((batch, result, exc))

    with patch("nblane.core.ai.gateway.translate_paper_segments", side_effect=_fake_gateway), patch.object(
        research_papers, "_translation_concurrency", return_value=1
    ):
        research_papers._process_translation_batches(
            batches,
            ai_profile_arg="alice",
            source_id="s",
            target_lang="zh",
            require_review=False,
            handle_result=handle,
            progress_lock=threading.Lock(),
        )
    return calls


def test_blocked_batch_is_retried_per_segment_and_reported_once() -> None:
    batch = [
        {"id": "a", "text": "Results improve."},
        {"id": "b", "text": "Ryan Yu, Pushi Zhang"},
        {"id": "c", "text": "We conclude."},
    ]
    calls = _run([batch])
    # Still one handler call per original batch, so progress counts stay right.
    assert len(calls) == 1
    got_batch, result, exc = calls[0]
    assert exc is None and got_batch == batch
    texts = {row["segment_id"]: row["translated_text"] for row in result.structured["translations"]}
    assert texts == {"a": "译:Results improve.", "c": "译:We conclude."}
    assert any("内容审核拦下了 1 段" in w for w in result.warnings)
    assert not any("DataInspectionFailed" in w for w in result.warnings)


def test_unblocked_batches_are_untouched() -> None:
    batch = [{"id": "a", "text": "Hello."}, {"id": "b", "text": "World."}]
    calls = _run([batch])
    assert len(calls) == 1
    assert [row["translated_text"] for row in calls[0][1].structured["translations"]] == ["译:Hello.", "译:World."]


def test_grobid_failure_message_names_timeouts() -> None:
    assert "超时" in research_papers._grobid_failure_message(TimeoutError("timed out"))
    assert "连不上" in research_papers._grobid_failure_message(OSError("Connection refused"))
    assert research_papers._grobid_failure_message(ValueError("bad xml")).startswith("结构化提取遇到问题")
