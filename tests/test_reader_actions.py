"""Tests for sidecar Reader action helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from nblane.core.reader_actions import ReaderActionContext, handle_reader_action
from nblane.core.research_papers import (
    PaperSegment,
    load_paper_annotations,
    load_paper_translations,
    save_paper_segments,
    text_hash,
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
