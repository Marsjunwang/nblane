"""Tests for sidecar Reader action helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from nblane.core.reader_actions import ReaderActionContext, handle_reader_action
from nblane.core.research_papers import (
    NO_LLM_TRANSLATION_WARNING,
    PaperPage,
    PaperSegment,
    PaperStructureUnit,
    load_paper_annotations,
    load_paper_analysis,
    load_paper_translations,
    save_paper_pages,
    save_paper_segments,
    save_paper_structure_units,
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
                result = handle_reader_action(
                    ctx,
                    "save_progress",
                    {
                        "page": 3,
                        "reader_mode": "compare",
                        "scale_mode": "fit-page",
                        "active_tab": "translation",
                        "target_lang": "zh",
                        "side_panel_collapsed": False,
                        "left_rail_collapsed": True,
                        "active_left_tab": "pages",
                        "translation_source_visible": False,
                        "active_translation_anchor": "segment:seg:1",
                        "visible_pages": [2, "3", "bad"],
                        "compare_split_ratio": 67,
                        "panel_width": 420,
                    },
                )

            source = load_research_sources(profile).by_id()[ctx.source_id]

        self.assertTrue(result.ok)
        self.assertEqual(source.metadata["last_read_page"], 3)
        self.assertEqual(source.metadata["reader_mode"], "compare")
        self.assertEqual(source.metadata["scale_mode"], "fit-page")
        self.assertEqual(source.metadata["active_tab"], "translation")
        self.assertFalse(source.metadata["side_panel_collapsed"])
        self.assertTrue(source.metadata["left_rail_collapsed"])
        self.assertEqual(source.metadata["active_left_tab"], "pages")
        self.assertFalse(source.metadata["translation_source_visible"])
        self.assertEqual(source.metadata["active_translation_anchor"], "segment:seg:1")
        self.assertEqual(source.metadata["last_visible_pages"], [2, 3])
        self.assertEqual(source.metadata["compare_split_ratio"], 67)
        self.assertEqual(source.metadata["panel_width"], 420)
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
                    "annotation_update",
                    {"annotation_id": annotation_id, "note": ""},
                )
                handle_reader_action(
                    ctx,
                    "annotation_delete",
                    {"annotation_id": annotation_id},
                )
            annotations = load_paper_annotations(profile, ctx.source_id)

        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].note, "")
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
                    {"visible_pages": [2], "target_lang": "zh", "scope_strategy": "page"},
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

    def test_translate_visible_pages_defaults_to_segment_scope(self) -> None:
        ai_result = SimpleNamespace(
            structured={
                "translations": [
                    {
                        "segment_id": "seg:1",
                        "source_hash": text_hash("Important passage"),
                        "translated_text": "重要段落。",
                    }
                ]
            },
            warnings=[],
        )
        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.reader_actions.build_paper_layout_units") as layout_mock,
                patch("nblane.core.reader_actions.translate_paper_segments", return_value=ai_result),
            ):
                result = handle_reader_action(
                    ctx,
                    "translate_visible_pages",
                    {"visible_pages": [1], "target_lang": "zh"},
                )
            translations = load_paper_translations(profile, ctx.source_id)

        layout_mock.assert_called()
        self.assertEqual(result.data["summary"]["scope"], "segment")
        self.assertEqual(translations[0].scope_type, "segment")
        self.assertEqual(translations[0].segment_id, "seg:1")

    def test_translate_visible_pages_auto_prefers_structure_scope(self) -> None:
        structure_hash = text_hash("Visible structure paragraph.")
        structure_scope = "psu:grounded:1:00001:abc123def456"
        captured_batches: list[list[dict[str, object]]] = []

        def fake_translate(profile_arg, source_id_arg, batch, *, target_lang="zh", require_review=True, **kwargs):
            captured_batches.append([dict(row) for row in batch])
            return SimpleNamespace(
                structured={
                    "translations": [
                        {
                            "segment_id": row["segment_id"],
                            "source_hash": row["source_hash"],
                            "translated_text": "结构段落译文。",
                        }
                        for row in batch
                    ]
                },
                warnings=[],
            )

        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_structure_units(
                    profile,
                    ctx.source_id,
                    [
                        PaperStructureUnit(
                            unit_id=structure_scope,
                            source_id=ctx.source_id,
                            kind="paragraph",
                            page_start=1,
                            page_end=1,
                            order=1,
                            text="Visible structure paragraph.",
                            text_hash=structure_hash,
                            section_path=["1 Introduction"],
                            locator="p. 1",
                            rects=[{"x": 10, "y": 20, "w": 80, "h": 24, "page_width": 200, "page_height": 200}],
                            translatable=True,
                        )
                    ],
                )
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.reader_actions.translate_paper_segments", side_effect=fake_translate),
            ):
                result = handle_reader_action(
                    ctx,
                    "translate_visible_pages",
                    {"visible_pages": [1], "target_lang": "zh", "scope_strategy": "auto"},
                )
            translations = load_paper_translations(profile, ctx.source_id)

        summary = result.data["summary"]
        self.assertEqual(summary["scope"], "structure")
        self.assertEqual(summary["segments_selected"], 1)
        self.assertEqual(captured_batches[0][0]["scope_type"], "structure")
        self.assertEqual(captured_batches[0][0]["scope_ref"], structure_scope)
        self.assertEqual(translations[0].scope_type, "structure")
        self.assertEqual(translations[0].scope_ref, structure_scope)
        self.assertEqual(translations[0].segment_id, "")
        self.assertEqual(translations[0].translated_text, "结构段落译文。")

    def test_translate_visible_pages_supports_layout_scope(self) -> None:
        layout_hash = text_hash("Visible positioned text.")
        layout_scope = "layout:v2:1:00001:abc123"
        layout_units = [
            {
                "unit_id": layout_scope,
                "anchor_id": layout_scope,
                "scope_type": "layout",
                "scope_ref": layout_scope,
                "page": 1,
                "order": 1,
                "kind": "paragraph",
                "locator": "p. 1",
                "source_text": "Visible positioned text.",
                "source_hash": layout_hash,
                "translatable": True,
                "rects": [{"x": 10, "y": 20, "w": 80, "h": 24, "page_width": 200, "page_height": 200}],
            }
        ]
        captured_batches: list[list[dict[str, object]]] = []

        def fake_translate(profile_arg, source_id_arg, batch, *, target_lang="zh", require_review=True, **kwargs):
            captured_batches.append([dict(row) for row in batch])
            return SimpleNamespace(
                structured={
                    "translations": [
                        {
                            "scope_ref": row["scope_ref"],
                            "source_hash": row["source_hash"],
                            "translated_text": "可见布局译文。",
                        }
                        for row in batch
                    ]
                },
                warnings=[],
            )

        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.reader_actions.build_paper_layout_units", return_value=layout_units),
                patch("nblane.core.reader_actions.translate_paper_segments", side_effect=fake_translate),
            ):
                result = handle_reader_action(
                    ctx,
                    "translate_visible_pages",
                    {"visible_pages": [1], "target_lang": "zh", "scope_strategy": "layout"},
                )
            translations = load_paper_translations(profile, ctx.source_id)

        summary = result.data["summary"]
        self.assertTrue(result.ok)
        self.assertEqual(summary["scope"], "layout")
        self.assertEqual(summary["requested_pages"], [1])
        self.assertEqual(summary["segments_selected"], 1)
        self.assertEqual(summary["saved"], 1)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["skipped"], 0)
        self.assertEqual(len(captured_batches), 1)
        self.assertEqual(captured_batches[0][0]["scope_type"], "layout")
        self.assertEqual(captured_batches[0][0]["scope_ref"], layout_scope)
        self.assertEqual(captured_batches[0][0]["segment_id"], layout_scope)
        self.assertEqual(captured_batches[0][0]["page"], 1)
        self.assertEqual(captured_batches[0][0]["order"], 1)
        self.assertEqual(captured_batches[0][0]["rects"][0]["w"], 80)
        self.assertEqual(translations[0].scope_type, "layout")
        self.assertEqual(translations[0].scope_ref, layout_scope)
        self.assertEqual(translations[0].segment_id, "")
        self.assertEqual(translations[0].rects[0]["w"], 80)
        self.assertEqual(translations[0].translated_text, "可见布局译文。")

    def test_translate_visible_pages_skips_blank_layout_fallback(self) -> None:
        layout_hash = text_hash("Visible positioned text.")
        layout_scope = "layout:v2:1:00001:abc123"
        layout_units = [
            {
                "unit_id": layout_scope,
                "anchor_id": layout_scope,
                "scope_type": "layout",
                "scope_ref": layout_scope,
                "page": 1,
                "order": 1,
                "kind": "paragraph",
                "locator": "p. 1",
                "source_text": "Visible positioned text.",
                "source_hash": layout_hash,
                "translatable": True,
                "rects": [{"x": 10, "y": 20, "w": 80, "h": 24, "page_width": 200, "page_height": 200}],
            }
        ]

        def fake_translate(profile_arg, source_id_arg, batch, *, target_lang="zh", require_review=True, **kwargs):
            return SimpleNamespace(
                backend="rule_fallback",
                structured={
                    "translations": [
                        {
                            "segment_id": row["segment_id"],
                            "source_hash": row["source_hash"],
                            "translated_text": "",
                            "generated_by": "rule_fallback",
                        }
                        for row in batch
                    ]
                },
                warnings=["Deterministic fallback used."],
            )

        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.reader_actions.build_paper_layout_units", return_value=layout_units),
                patch("nblane.core.reader_actions.translate_paper_segments", side_effect=fake_translate),
            ):
                result = handle_reader_action(
                    ctx,
                    "translate_visible_pages",
                    {"visible_pages": [1], "target_lang": "zh", "scope_strategy": "layout"},
                )
            translations = load_paper_translations(profile, ctx.source_id)

        summary = result.data["summary"]
        self.assertTrue(result.ok)
        self.assertEqual(summary["scope"], "layout")
        self.assertEqual(summary["saved"], 0)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["skipped"], 1)
        self.assertEqual(translations, [])
        self.assertIn(NO_LLM_TRANSLATION_WARNING, result.warnings)

    def test_retry_layout_scope_translates_only_requested_scope_ref(self) -> None:
        first_hash = text_hash("First positioned text.")
        second_hash = text_hash("Second positioned text.")
        first_scope = "layout:v2:1:00001:first"
        second_scope = "layout:v2:1:00002:second"
        layout_units = [
            {
                "unit_id": first_scope,
                "anchor_id": first_scope,
                "scope_type": "layout",
                "scope_ref": first_scope,
                "page": 1,
                "order": 1,
                "kind": "paragraph",
                "locator": "p. 1",
                "source_text": "First positioned text.",
                "source_hash": first_hash,
                "translatable": True,
                "rects": [{"x": 10, "y": 20, "w": 80, "h": 24, "page_width": 200, "page_height": 200}],
            },
            {
                "unit_id": second_scope,
                "anchor_id": second_scope,
                "scope_type": "layout",
                "scope_ref": second_scope,
                "page": 1,
                "order": 2,
                "kind": "paragraph",
                "locator": "p. 1",
                "source_text": "Second positioned text.",
                "source_hash": second_hash,
                "translatable": True,
                "rects": [{"x": 10, "y": 50, "w": 80, "h": 24, "page_width": 200, "page_height": 200}],
            },
        ]
        batches: list[list[str]] = []
        progress: list[dict] = []

        def fake_translate(profile_arg, source_id_arg, batch, *, target_lang="zh", require_review=True, **kwargs):
            batches.append([row["scope_ref"] for row in batch])
            return SimpleNamespace(
                structured={
                    "translations": [
                        {
                            "segment_id": row["segment_id"],
                            "source_hash": row["source_hash"],
                            "translated_text": "第二段译文。",
                        }
                        for row in batch
                    ]
                },
                warnings=[],
            )

        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.reader_actions.build_paper_layout_units", return_value=layout_units),
                patch("nblane.core.reader_actions.translate_paper_segments", side_effect=fake_translate),
            ):
                result = handle_reader_action(
                    ctx,
                    "retry_translation_scope",
                    {
                        "visible_pages": [1],
                        "target_lang": "zh",
                        "scope_strategy": "layout",
                        "scope_refs": [second_scope],
                    },
                    progress_callback=progress.append,
                )
            translations = load_paper_translations(profile, ctx.source_id)

        summary = result.data["summary"]
        self.assertTrue(result.ok)
        self.assertEqual(summary["segments_selected"], 1)
        self.assertEqual(batches, [[second_scope]])
        self.assertEqual([row.scope_ref for row in translations], [second_scope])
        self.assertEqual(translations[0].translated_text, "第二段译文。")
        self.assertIn("extracting_layout", [row["phase"] for row in progress])
        self.assertIn("translating", [row["phase"] for row in progress])

    def test_retry_structure_scope_translates_only_requested_scope_ref(self) -> None:
        first_scope = "psu:grounded:1:00001:first"
        second_scope = "psu:grounded:1:00002:second"
        batches: list[list[str]] = []

        def fake_translate(profile_arg, source_id_arg, batch, *, target_lang="zh", require_review=True, **kwargs):
            batches.append([row["scope_ref"] for row in batch])
            return SimpleNamespace(
                structured={
                    "translations": [
                        {
                            "segment_id": row["segment_id"],
                            "source_hash": row["source_hash"],
                            "translated_text": "第二个结构段落。",
                        }
                        for row in batch
                    ]
                },
                warnings=[],
            )

        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_structure_units(
                    profile,
                    ctx.source_id,
                    [
                        PaperStructureUnit(
                            unit_id=first_scope,
                            source_id=ctx.source_id,
                            kind="paragraph",
                            page_start=1,
                            page_end=1,
                            order=1,
                            text="First structure paragraph.",
                            text_hash=text_hash("First structure paragraph."),
                            locator="p. 1",
                            rects=[{"x": 10, "y": 20, "w": 80, "h": 24, "page_width": 200, "page_height": 200}],
                        ),
                        PaperStructureUnit(
                            unit_id=second_scope,
                            source_id=ctx.source_id,
                            kind="paragraph",
                            page_start=1,
                            page_end=1,
                            order=2,
                            text="Second structure paragraph.",
                            text_hash=text_hash("Second structure paragraph."),
                            locator="p. 1",
                            rects=[{"x": 10, "y": 50, "w": 80, "h": 24, "page_width": 200, "page_height": 200}],
                        ),
                    ],
                )
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.reader_actions.translate_paper_segments", side_effect=fake_translate),
            ):
                result = handle_reader_action(
                    ctx,
                    "retry_translation_scope",
                    {
                        "visible_pages": [1],
                        "target_lang": "zh",
                        "scope_strategy": "structure",
                        "scope_refs": [second_scope],
                    },
                )
            translations = load_paper_translations(profile, ctx.source_id)

        self.assertTrue(result.ok)
        self.assertEqual(result.data["summary"]["scope"], "structure")
        self.assertEqual(batches, [[second_scope]])
        self.assertEqual([row.scope_ref for row in translations], [second_scope])
        self.assertEqual(translations[0].translated_text, "第二个结构段落。")

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
        self.assertEqual(len(progress), 3)
        self.assertEqual(progress[0]["batches_completed"], 0)
        self.assertEqual(progress[0]["segments_processed"], 0)
        self.assertEqual(progress[1]["batches_completed"], 1)
        self.assertEqual(progress[1]["segments_processed"], 2)
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

    def test_ask_paper_uses_whole_paper_context_without_selection(self) -> None:
        ai_result = SimpleNamespace(structured={"answer": "whole"}, warnings=[])
        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            segments = [
                PaperSegment(
                    segment_id=f"seg:{index}",
                    source_id=ctx.source_id,
                    page=max(1, (index + 2) // 3),
                    order=index,
                    text=f"Passage {index}",
                    text_hash=text_hash(f"Passage {index}"),
                )
                for index in range(1, 91)
            ]
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(profile, ctx.source_id, segments)
            with patch("nblane.core.reader_actions.answer_paper_question", return_value=ai_result) as ask:
                handle_reader_action(ctx, "ask_paper", {"question": "文章讲了什么"})

        payload = ask.call_args.kwargs["payload"]
        segment_refs = [row["segment_id"] for row in payload["segments"]]
        self.assertGreater(len(segment_refs), 30)
        self.assertIn("seg:90", segment_refs)
        self.assertEqual(payload["scope"], "paper")
        self.assertTrue(payload["full_paper"])
        self.assertEqual(payload["paper_context"]["source_segments"], 90)
        self.assertEqual(payload["paper_context"]["supplied_segments"], len(segment_refs))

    def test_analyze_paper_saves_normalized_review_schema(self) -> None:
        ai_result = SimpleNamespace(
            ok=True,
            structured={
                "tldr": "Useful paper.",
                "key_points": [{"text": "Grounded point", "refs": ["seg:1"]}],
                "method": ["Ablation study"],
                "scores": {"overall": 8, "novelty": 6},
                "score_rationale": [{"text": "Evidence is direct.", "refs": ["seg:1"]}],
            },
            warnings=[],
            error="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.research_papers.git_backup.record_change"),
                patch("nblane.core.reader_actions.generate_paper_review_card", return_value=ai_result),
            ):
                result = handle_reader_action(ctx, "analyze_paper", {"page": 1})
            analysis = load_paper_analysis(profile, ctx.source_id)

        self.assertTrue(result.ok)
        self.assertEqual(result.message, "Analysis saved")
        self.assertEqual(result.data["structured"]["scores"]["overall"], 8)
        self.assertEqual(result.data["structured"]["cited_segment_refs"], ["seg:1"])
        self.assertEqual(analysis["tldr"], "Useful paper.")
        self.assertEqual(analysis["scores"]["novelty"], 6)
        self.assertEqual(analysis["cited_segment_refs"], ["seg:1"])

    def test_codex_deep_read_saves_rich_schema_and_context_coverage(self) -> None:
        ai_result = SimpleNamespace(
            ok=True,
            structured={
                "takeaway": "这篇论文提出一个可检查的核心机制。",
                "problem": [{"text": "问题定义清楚。", "refs": ["seg:2"]}],
                "method": [{"text": "方法分三步。", "refs": ["seg:45"]}],
                "experiments": [{"text": "实验覆盖主要设置。", "refs": ["seg:72"]}],
                "limitations": [{"text": "仍有边界条件。", "refs": ["seg:94"]}],
                "findings": [{"text": "关键发现保留兼容字段。", "refs": ["seg:45"]}],
                "reading_plan": [{"text": "复读 Method 和 Experiments。", "refs": ["seg:45", "seg:72"]}],
                "cited_segment_refs": ["seg:2", "seg:45", "seg:72", "seg:94"],
                "cited_chunk_refs": [],
                "cited_annotation_refs": [],
                "warnings": [],
                "ref": "source:paper:grounded",
            },
            warnings=[],
            error="",
        )
        captured_payload: dict[str, object] = {}

        def fake_deep_read(profile_arg, source_id_arg, *, payload, require_review=True, **kwargs):
            captured_payload.update(payload)
            return ai_result

        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            sections = (
                ["Abstract"] * 5
                + ["Introduction"] * 20
                + ["Method"] * 35
                + ["Experiments"] * 25
                + ["Conclusion"] * 10
            )
            segments = [
                PaperSegment(
                    segment_id=f"seg:{index}",
                    source_id=ctx.source_id,
                    page=max(1, (index + 2) // 3),
                    order=index,
                    text=f"{sections[index - 1]} passage {index}",
                    section_path=[sections[index - 1]],
                    text_hash=text_hash(f"{sections[index - 1]} passage {index}"),
                    locator=f"p. {max(1, (index + 2) // 3)} § {sections[index - 1]}",
                )
                for index in range(1, 96)
            ]
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(profile, ctx.source_id, segments)
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.research_papers.git_backup.record_change"),
                patch("nblane.core.reader_actions.ensure_paper_reading_artifacts", return_value={"warnings": []}),
                patch("nblane.core.reader_actions.deep_read_paper_codex", side_effect=fake_deep_read),
            ):
                result = handle_reader_action(
                    ctx,
                    "codex_deep_read",
                    {
                        "page": 1,
                        "scope": "paper",
                        "full_paper": True,
                        "codex_timeout_seconds": 2,
                        "codex_idle_timeout_seconds": 1,
                    },
                )
            analysis = load_paper_analysis(profile, ctx.source_id)

        self.assertTrue(result.ok)
        self.assertEqual(analysis["codex_deep_read"]["takeaway"], "这篇论文提出一个可检查的核心机制。")
        self.assertEqual(analysis["codex_deep_read"]["problem"][0]["refs"], ["seg:2"])
        payload_segments = captured_payload["segments"]
        self.assertIsInstance(payload_segments, list)
        segment_refs = [row["segment_id"] for row in payload_segments]  # type: ignore[index]
        self.assertIn("seg:94", segment_refs)
        paper_context = captured_payload["paper_context"]
        self.assertIsInstance(paper_context, dict)
        self.assertEqual(paper_context["source_segments"], 95)
        self.assertEqual(paper_context["supplied_segments"], len(payload_segments))
        self.assertTrue(paper_context["truncated"])
        self.assertEqual(paper_context["segment_budget"], {"segments": 80, "chars": 60000})
        self.assertIn("Method", paper_context["sections_covered"])
        self.assertIn("Conclusion", paper_context["sections_covered"])
        self.assertEqual(captured_payload["codex_timeout_seconds"], 2)
        self.assertEqual(captured_payload["codex_idle_timeout_seconds"], 1)

    def test_codex_deep_read_keeps_legacy_findings_schema(self) -> None:
        ai_result = SimpleNamespace(
            ok=True,
            structured={
                "findings": [{"text": "Legacy finding", "refs": ["seg:1"]}],
                "reading_plan": [{"text": "Legacy plan", "refs": ["seg:1"]}],
                "cited_segment_refs": ["seg:1"],
                "cited_chunk_refs": [],
                "cited_annotation_refs": [],
                "warnings": [],
                "ref": "source:paper:grounded",
            },
            warnings=[],
            error="",
        )

        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.research_papers.git_backup.record_change"),
                patch("nblane.core.reader_actions.ensure_paper_reading_artifacts", return_value={"warnings": []}),
                patch("nblane.core.reader_actions.deep_read_paper_codex", return_value=ai_result),
            ):
                result = handle_reader_action(ctx, "codex_deep_read", {"page": 1})
            analysis = load_paper_analysis(profile, ctx.source_id)

        self.assertTrue(result.ok)
        self.assertEqual(analysis["codex_deep_read"]["findings"][0]["text"], "Legacy finding")
        self.assertEqual(result.data["structured"]["reading_plan"][0]["text"], "Legacy plan")

    def test_codex_deep_read_batches_large_paper_then_synthesizes(self) -> None:
        calls: list[dict[str, object]] = []

        def fake_deep_read(profile_arg, source_id_arg, *, payload, require_review=True, **kwargs):
            calls.append(payload)
            context = payload.get("paper_context") if isinstance(payload.get("paper_context"), dict) else {}
            mode = str(context.get("mode") or "")
            if mode == "synthesis":
                return SimpleNamespace(
                    ok=True,
                    structured={
                        "takeaway": "综合后的 Moonlight 风格结论。",
                        "problem": [{"text": "综合问题。", "refs": ["seg:1"]}],
                        "method": [{"text": "综合方法。", "refs": ["seg:40"]}],
                        "experiments": [{"text": "综合实验。", "refs": ["seg:100"]}],
                        "findings": [{"text": "综合发现。", "refs": ["seg:40"]}],
                        "reading_plan": [{"text": "复查关键章节。", "refs": ["seg:1"]}],
                        "cited_segment_refs": ["seg:1", "seg:40", "seg:100"],
                        "cited_chunk_refs": [],
                        "cited_annotation_refs": [],
                        "warnings": [],
                        "ref": source_id_arg,
                    },
                    warnings=[],
                    error="",
                )
            batch_segments = payload.get("segments") if isinstance(payload.get("segments"), list) else []
            first_ref = str(batch_segments[0].get("segment_id") if batch_segments else "seg:missing")
            return SimpleNamespace(
                ok=True,
                structured={
                    "takeaway": f"批次 {context.get('batch_label')} 读完。",
                    "findings": [{"text": "批次发现。", "refs": [first_ref]}],
                    "reading_plan": [{"text": "继续综合。", "refs": [first_ref]}],
                    "cited_segment_refs": [first_ref],
                    "cited_chunk_refs": [],
                    "cited_annotation_refs": [],
                    "warnings": [],
                    "ref": source_id_arg,
                },
                warnings=[],
                error="",
            )

        with tempfile.TemporaryDirectory() as tmp:
            profile, ctx = self._profile(Path(tmp))
            section_cycle = (
                ["Abstract"] * 8
                + ["Introduction"] * 22
                + ["Related Work"] * 18
                + ["Method"] * 35
                + ["Experiments"] * 32
                + ["Conclusion"] * 15
            )
            segments = [
                PaperSegment(
                    segment_id=f"seg:{index}",
                    source_id=ctx.source_id,
                    page=max(1, index // 5),
                    order=index,
                    text=f"{section_cycle[index - 1]} evidence passage {index}",
                    section_path=[section_cycle[index - 1]],
                    text_hash=text_hash(f"{section_cycle[index - 1]} evidence passage {index}"),
                    locator=f"p. {max(1, index // 5)} § {section_cycle[index - 1]}",
                )
                for index in range(1, 131)
            ]
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(profile, ctx.source_id, segments)
            with (
                patch("nblane.core.git_backup.record_change"),
                patch("nblane.core.research_papers.git_backup.record_change"),
                patch("nblane.core.reader_actions.ensure_paper_reading_artifacts", return_value={"warnings": []}),
                patch("nblane.core.reader_actions.deep_read_paper_codex", side_effect=fake_deep_read),
            ):
                result = handle_reader_action(
                    ctx,
                    "codex_deep_read",
                    {"page": 1, "scope": "paper", "full_paper": True, "batch_deep_read": True},
                )
            analysis = load_paper_analysis(profile, ctx.source_id)

        self.assertTrue(result.ok)
        self.assertEqual(analysis["codex_deep_read"]["takeaway"], "综合后的 Moonlight 风格结论。")
        batch_calls = [
            call
            for call in calls
            if isinstance(call.get("paper_context"), dict)
            and call["paper_context"].get("mode") == "section_batch"  # type: ignore[index, union-attr]
        ]
        synthesis_calls = [
            call
            for call in calls
            if isinstance(call.get("paper_context"), dict)
            and call["paper_context"].get("mode") == "synthesis"  # type: ignore[index, union-attr]
        ]
        self.assertGreaterEqual(len(batch_calls), 4)
        self.assertEqual(len(synthesis_calls), 1)
        self.assertGreaterEqual(int(batch_calls[0]["codex_timeout_seconds"]), 300)
        self.assertGreaterEqual(int(synthesis_calls[0]["codex_timeout_seconds"]), 420)
        synthesis_context = synthesis_calls[0]["paper_context"]
        self.assertIsInstance(synthesis_context, dict)
        self.assertTrue(synthesis_context["batch_reading"])
        self.assertEqual(synthesis_context["batch_count"], len(batch_calls))
        self.assertIn("batch_reports", synthesis_calls[0])
        self.assertEqual(analysis["codex_deep_read"]["batch_reading"]["batch_count"], len(batch_calls))


if __name__ == "__main__":
    unittest.main()
