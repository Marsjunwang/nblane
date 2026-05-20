"""Tests for sidecar Reader action helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from nblane.core.reader_actions import ReaderActionContext, handle_reader_action
from nblane.core.research_papers import (
    PaperPage,
    PaperSegment,
    load_paper_annotations,
    load_paper_translations,
    save_paper_pages,
    save_paper_segments,
    text_hash,
    translate_full_paper,
)
from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    load_research_sources,
    save_research_sources,
)


class TestReaderActions(unittest.TestCase):
    def _profile(self, root: Path) -> tuple[Path, ReaderActionContext]:
        profile = root / "alice"
        profile.mkdir()
        source_id = "source:paper:grounded"
        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(
            inbox,
            "Grounded Claims",
            source_id=source_id,
            kind="paper",
            visibility="private",
        )
        with patch("nblane.core.research_sources.git_backup.record_change"):
            save_research_sources(profile, inbox)
        with patch("nblane.core.research_papers.git_backup.record_change"):
            save_paper_segments(
                profile,
                source_id,
                [
                    PaperSegment(
                        segment_id="seg:1",
                        source_id=source_id,
                        page=1,
                        order=1,
                        text="Important passage",
                        text_hash=text_hash("Important passage"),
                    )
                ],
            )
        return profile, ReaderActionContext(
            profile_name="alice",
            profile_path=profile,
            user_id="local",
            source_id=source_id,
        )

    def test_progress_updates_source_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with patch("nblane.core.git_backup.record_change"):
                result = handle_reader_action(ctx, "save_progress", {"page": 3})

            source = load_research_sources(profile).by_id()[ctx.source_id]

        self.assertTrue(result.ok)
        self.assertEqual(source.metadata["last_read_page"], 3)
        self.assertEqual(source.status, "reading")

    def test_annotation_create_update_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with patch("nblane.core.git_backup.record_change"):
                created = handle_reader_action(
                    ctx,
                    "annotation_create",
                    {"selected_text": "Important passage", "page": 1, "note": "yes"},
                )
                annotation_id = created.changed_ids["annotation_id"]
                handle_reader_action(
                    ctx,
                    "annotation_update",
                    {"annotation_id": annotation_id, "note": "updated"},
                )
                handle_reader_action(
                    ctx,
                    "annotation_delete",
                    {"annotation_id": annotation_id},
                )
            annotations = load_paper_annotations(profile, ctx.source_id)

        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].note, "updated")
        self.assertEqual(annotations[0].status, "deleted")

    def test_translate_selection_saves_translation(self) -> None:
        ai_result = SimpleNamespace(
            structured={
                "translations": [
                    {
                        "segment_id": "selection:abc",
                        "translated_text": "重要段落",
                    }
                ]
            },
            warnings=[],
        )
        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.reader_actions.translate_paper_segments", return_value=ai_result),
            ):
                result = handle_reader_action(
                    ctx,
                    "translate_selection",
                    {
                        "selected_text": "Important passage",
                        "selected_text_hash": "hash:abc",
                        "page": 1,
                        "target_lang": "zh",
                    },
                )
            translations = load_paper_translations(profile, ctx.source_id)

        self.assertTrue(result.ok)
        self.assertEqual(result.data["saved"], 1)
        self.assertEqual(translations[0].scope_type, "selection")
        self.assertEqual(translations[0].translated_text, "重要段落")

    def test_translate_selection_accepts_provider_text_alias(self) -> None:
        ai_result = SimpleNamespace(
            structured={
                "translations": [
                    {
                        "segment_id": "selection:abc",
                        "text": "重要段落",
                    }
                ]
            },
            warnings=[],
        )
        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.reader_actions.translate_paper_segments", return_value=ai_result),
            ):
                result = handle_reader_action(
                    ctx,
                    "translate_selection",
                    {
                        "selected_text": "Important passage",
                        "selected_text_hash": "hash:abc",
                        "page": 1,
                        "target_lang": "zh",
                    },
                )
            translations = load_paper_translations(profile, ctx.source_id)

        self.assertTrue(result.ok)
        self.assertEqual(result.data["saved"], 1)
        self.assertEqual(result.data["translation_text"], "重要段落")
        self.assertEqual(translations[0].translated_text, "重要段落")

    def test_translate_visible_pages_returns_summary_and_warns_for_unsavable_rows(self) -> None:
        wrong_hash = text_hash("Wrong passage")
        ai_result = SimpleNamespace(
            structured={
                "translations": [
                    {"translated_text": "missing id"},
                    {
                        "segment_id": "seg:unknown",
                        "source_hash": text_hash("Unknown"),
                        "translated_text": "unknown",
                    },
                    {
                        "segment_id": "seg:1",
                        "source_hash": wrong_hash,
                        "translated_text": "wrong hash",
                    },
                    {
                        "segment_id": "seg:1",
                        "source_hash": text_hash("Important passage"),
                        "translated_text": "  ",
                    },
                ]
            },
            warnings=["ai warning"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.reader_actions.translate_paper_segments", return_value=ai_result),
            ):
                result = handle_reader_action(
                    ctx,
                    "translate_visible_pages",
                    {"visible_pages": [1], "target_lang": "zh"},
                )
            translations = load_paper_translations(profile, ctx.source_id)

        summary = result.data["summary"]
        warning_text = " ".join(result.warnings)
        self.assertTrue(result.ok)
        self.assertEqual(summary["scope"], "segment")
        self.assertEqual(summary["requested_pages"], [1])
        self.assertEqual(summary["segments_selected"], 1)
        self.assertEqual(summary["ai_rows"], 4)
        self.assertEqual(summary["saved"], 0)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["skipped"], 3)
        self.assertEqual(summary["target_lang"], "zh")
        self.assertIn("Saved 1 failed translation row", result.message)
        self.assertIn("without segment_id or scope_ref", warning_text)
        self.assertIn("unknown segment", warning_text)
        self.assertIn("source_hash mismatch", warning_text)
        self.assertIn("translated_text is blank", warning_text)
        self.assertEqual(len(translations), 1)
        self.assertEqual(translations[0].status, "failed")
        self.assertEqual(translations[0].segment_id, "seg:1")

    def test_translate_visible_pages_page_fallback_counts_saved_rows(self) -> None:
        page_text = "Whole page fallback text."
        ai_result = SimpleNamespace(
            structured={
                "translations": [
                    {
                        "segment_id": "page:2",
                        "source_hash": text_hash(page_text),
                        "translated_text": "整页译文。",
                    }
                ]
            },
            warnings=[],
        )
        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_pages(
                    profile,
                    ctx.source_id,
                    [
                        PaperPage(
                            source_id=ctx.source_id,
                            page=2,
                            text=page_text,
                            text_hash=text_hash(page_text),
                        )
                    ],
                )
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.reader_actions.translate_paper_segments", return_value=ai_result),
            ):
                result = handle_reader_action(
                    ctx,
                    "translate_visible_pages",
                    {"visible_pages": [2], "target_lang": "zh"},
                )
            translations = load_paper_translations(profile, ctx.source_id)

        summary = result.data["summary"]
        self.assertEqual(summary["scope"], "page")
        self.assertEqual(summary["requested_pages"], [2])
        self.assertEqual(summary["segments_selected"], 1)
        self.assertEqual(summary["ai_rows"], 1)
        self.assertEqual(summary["saved"], 1)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["skipped"], 0)
        self.assertEqual(result.message, "Saved 1 translation row(s).")
        self.assertEqual(translations[0].scope_type, "page")
        self.assertEqual(translations[0].translated_text, "整页译文。")

    def test_translate_full_paper_reports_batch_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            segments = [
                PaperSegment(
                    segment_id=f"seg:{index}",
                    source_id=ctx.source_id,
                    page=1,
                    order=index,
                    text=f"Passage {index}",
                    text_hash=text_hash(f"Passage {index}"),
                )
                for index in range(1, 4)
            ]
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(profile, ctx.source_id, segments)

            def fake_translate(profile_arg, source_id_arg, batch, *, target_lang="zh", require_review=True, **kwargs):
                return SimpleNamespace(
                    warnings=[],
                    error="",
                    structured={
                        "translations": [
                            {
                                "segment_id": row["segment_id"],
                                "source_hash": row["text_hash"],
                                "translated_text": f"zh:{row['segment_id']}",
                            }
                            for row in batch
                        ]
                    },
                )

            progress = []
            with (
                patch("nblane.core.ai.gateway.translate_paper_segments", side_effect=fake_translate),
                patch("nblane.core.research_papers.git_backup.record_change"),
            ):
                summary = translate_full_paper(
                    profile,
                    ctx.source_id,
                    target_lang="zh",
                    mode="all",
                    batch_size=2,
                    ai_profile="alice",
                    require_review=False,
                    progress_callback=progress.append,
                )

        self.assertEqual(summary["segments_selected"], 3)
        self.assertEqual(summary["updated"], 3)
        self.assertEqual(len(progress), 2)
        self.assertEqual(progress[0]["batches_completed"], 1)
        self.assertEqual(progress[0]["segments_processed"], 2)
        self.assertEqual(progress[-1]["batches_completed"], 2)
        self.assertEqual(progress[-1]["segments_processed"], 3)

    def test_ask_paper_returns_structured_result(self) -> None:
        ai_result = SimpleNamespace(structured={"answer": "42"}, warnings=["check"])
        with tempfile.TemporaryDirectory() as tmp:
            _, ctx = self._profile(Path(tmp))
            with patch("nblane.core.reader_actions.answer_paper_question", return_value=ai_result):
                result = handle_reader_action(ctx, "ask_paper", {"question": "Why?"})

        self.assertEqual(result.data["structured"], {"answer": "42"})
        self.assertEqual(result.warnings, ["check"])


if __name__ == "__main__":
    unittest.main()
