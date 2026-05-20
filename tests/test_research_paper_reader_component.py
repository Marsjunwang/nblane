"""Contract tests for the Paper Reading Streamlit component boundary."""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from unittest.mock import patch

import nblane.research_paper_reader_component as reader


class TestResearchPaperReaderComponent(unittest.TestCase):
    def test_static_reader_uses_local_pdfjs_assets_and_known_actions(self) -> None:
        static_dir = Path(reader.__file__).parent / "frontend" / "static"
        html = (static_dir / "index.html").read_text(encoding="utf-8")
        page_source = Path("pages/7_Research.py").read_text(encoding="utf-8")

        self.assertTrue(reader.research_paper_reader_component_available())
        self.assertTrue((static_dir / "assets" / "pdf.min.js").is_file())
        self.assertTrue((static_dir / "assets" / "pdf.worker.min.js").is_file())
        self.assertIn("./assets/pdf.min.js", html)
        self.assertIn("./assets/pdf.worker.min.js", html)
        self.assertNotIn("cdnjs.cloudflare.com/ajax/libs/pdf.js", html)
        self.assertIn("page_previews", html)
        self.assertIn("pdf_url", html)
        self.assertIn("{ url: pdfUrl }", html)
        self.assertIn("lastFrameHeight", html)
        self.assertIn("emit_passive_events", html)
        self.assertIn("PDF.js render timed out", html)
        self.assertIn("pr-page-preview", html)
        self.assertIn("renderPreviewOnly", html)
        self.assertIn("pr-continuous-document", html)
        self.assertIn("pr-page-container", html)
        self.assertIn("pr-dock", html)
        self.assertIn("pr-selection-popover", html)
        self.assertIn("selectionDock", html)
        self.assertIn("placeSelectionDock", html)
        self.assertIn("translatedTextFromRow", html)
        self.assertIn("translation_units", html)
        self.assertIn("renderTranslationPage", html)
        self.assertIn("syncCompareScroll", html)
        self.assertIn("annotationPopover", html)
        self.assertIn("panelResize", html)
        self.assertIn("compare_split_ratio", html)
        self.assertIn("panel_width", html)
        self.assertIn("Deep Read", html)
        self.assertNotIn('tabButton("translation"', html)
        self.assertIn("segmentRowsForPages", html)
        self.assertIn("pageTranslationRowsForPages", html)
        self.assertIn("data-delete-annotation", html)
        self.assertIn('data-action="chunk"', html)
        self.assertIn('data-action="cite"', html)
        self.assertIn("continuousDocument", html)
        self.assertIn("IntersectionObserver", html)
        self.assertIn("nblane_pdf_reader_cache_v1", html)
        self.assertIn("indexedDB.open", html)
        self.assertIn("applyCachedPagePreview", html)
        self.assertIn("refreshForArgsUpdate", html)
        self.assertIn("pdfSourceSignature", html)
        self.assertIn("render_cache_max_pages", html)
        self.assertIn("scale_mode", html)
        self.assertIn("overscan_pages", html)
        self.assertIn("NBLANE_READER_SEND_FULL_PDF", page_source)
        self.assertIn('pdf_base64=_reader_pdf_base64(source_id)', page_source)
        self.assertIn('pdf_url=str(reader_payload.get("pdf_url") or _reader_pdf_url(source_id))', page_source)
        self.assertIn('"view_mode": "continuous"', page_source)
        self.assertIn('"scale_mode": reader_state.get("scale_mode") or "fit-width"', page_source)
        self.assertIn('"auto_save_progress": False', page_source)
        self.assertIn('"emit_passive_events": False', page_source)
        self.assertIn('"render_cache": True', page_source)
        self.assertIn('"translation_dock_default": "selection"', page_source)
        self.assertIn('"compare_split_ratio": reader_state.get("compare_split_ratio")', page_source)
        self.assertIn('"panel_width": reader_state.get("panel_width")', page_source)
        self.assertIn('"pdf_load_timeout_ms": 9000', page_source)
        self.assertIn("loadingWatchdogTimer", html)
        self.assertIn("pageDomReady", html)
        self.assertIn("renderAfterLayout", html)
        self.assertIn("requestFullscreen", html)
        self.assertIn("reader-mode-compare", html)
        self.assertIn("translationReaderHtml", html)
        self.assertIn("generate_review_card", html)
        self.assertIn("save_progress", html)
        self.assertIn("reader_state_changed", html)
        self.assertIn("request_reader_context", html)
        self.assertIn("request_page_previews", html)
        self.assertIn("retry_translation_scope", html)
        self.assertIn("debugState", html)
        self.assertIn("pr-page-spacer", html)
        self.assertIn("pr-action-status", html)
        self.assertIn("actionState", html)
        self.assertIn("setActionState", html)
        self.assertIn("syncActionStatusFromSettings", html)

        actions = set(re.findall(r'emitAction\("([^"]+)"', html))
        self.assertGreaterEqual(
            actions,
            {
                "selection_created",
                "annotation_create",
                "annotation_delete",
                "create_chunk_from_selection",
                "create_citation",
                "translate_selection",
                "translate_full_paper",
                "translate_visible_pages",
                "explain_selection",
                "ask_paper",
                "page_changed",
                "viewport_changed",
                "request_page_previews",
                "request_reader_context",
                "reader_state_changed",
                "retry_translation_scope",
                "save_progress",
                "generate_review_card",
                "codex_deep_read",
            },
        )

    def test_event_contract_exports_reader_event_names(self) -> None:
        from nblane.research_paper_reader_component import events

        self.assertIn("request_reader_context", events.EVENT_NAMES)
        self.assertIn("request_page_previews", events.EVENT_NAMES)
        self.assertIn("reader_state_changed", events.EVENT_NAMES)
        self.assertIn("retry_translation_scope", events.EVENT_NAMES)
        self.assertIn("prepare_reader_artifacts", events.EVENT_NAMES)
        self.assertEqual(events.clean_page_list([1, "2", 2, 0, "bad", 3]), [1, 2, 3])

    def test_wrapper_returns_none_for_empty_component_event(self) -> None:
        def fake_component(**kwargs):
            return {"action": None, "payload": {}}

        with patch.object(reader, "_get_component_func", return_value=fake_component):
            event = reader.st_research_paper_reader(source={"id": "source:paper:test"})

        self.assertIsNone(event)

    def test_wrapper_passes_real_component_event(self) -> None:
        def fake_component(**kwargs):
            return {
                "action": "selection_created",
                "event_id": "evt-1",
                "payload": {"source_id": "source:paper:test"},
            }

        with patch.object(reader, "_get_component_func", return_value=fake_component):
            event = reader.st_research_paper_reader(source={"id": "source:paper:test"})

        self.assertEqual(event["action"], "selection_created")
        self.assertEqual(event["payload"]["source_id"], "source:paper:test")

    def test_wrapper_normalizes_bad_component_events(self) -> None:
        with patch.object(reader, "_get_component_func", return_value=lambda **kwargs: "bad"):
            self.assertIsNone(reader.st_research_paper_reader(source={"id": "source:paper:test"}))

        def fake_component(**kwargs):
            return {"action": "ask_paper", "payload": "bad"}

        with patch.object(reader, "_get_component_func", return_value=fake_component):
            event = reader.st_research_paper_reader(source={"id": "source:paper:test"})

        self.assertEqual(event["action"], "ask_paper")
        self.assertEqual(event["payload"], {})

    def test_wrapper_passes_page_previews_to_component(self) -> None:
        captured = {}

        def fake_component(**kwargs):
            captured.update(kwargs)
            return {"action": None, "payload": {}}

        preview = {"page": 1, "data_url": "data:image/png;base64,abc"}
        with patch.object(reader, "_get_component_func", return_value=fake_component):
            event = reader.st_research_paper_reader(
                source={"id": "source:paper:test"},
                page_previews=[preview],
            )

        self.assertIsNone(event)
        self.assertEqual(captured["page_previews"], [preview])

    def test_wrapper_passes_pdf_url_to_component(self) -> None:
        captured = {}

        def fake_component(**kwargs):
            captured.update(kwargs)
            return {"action": None, "payload": {}}

        with patch.object(reader, "_get_component_func", return_value=fake_component):
            event = reader.st_research_paper_reader(
                source={"id": "source:paper:test"},
                pdf_url="/media/test.pdf",
            )

        self.assertIsNone(event)
        self.assertEqual(captured["pdf_url"], "/media/test.pdf")

    def test_wrapper_passes_reader_payload_collections_and_settings(self) -> None:
        captured = {}

        def fake_component(**kwargs):
            captured.update(kwargs)
            return {"action": None, "payload": {}}

        with patch.object(reader, "_get_component_func", return_value=fake_component):
            event = reader.st_research_paper_reader(
                source={"id": "source:paper:test"},
                pages=[{"page": 1}],
                segments=[{"segment_id": "seg-1"}],
                annotations=[{"id": "ann-1"}],
                translations=[{"id": "tr-1"}],
                translation_units=[{"unit_id": "unit-1"}],
                translation_summary={"translated": 1},
                translation_revision="rev-1",
                compare_split_ratio=62,
                panel_width=420,
                chunks=[{"id": "chunk-1"}],
                analysis={"tldr": "Useful paper."},
                ui={"page": "Page"},
                settings={"view_mode": "continuous"},
                height=900,
            )

        self.assertIsNone(event)
        self.assertEqual(captured["pages"], [{"page": 1}])
        self.assertEqual(captured["segments"], [{"segment_id": "seg-1"}])
        self.assertEqual(captured["annotations"], [{"id": "ann-1"}])
        self.assertEqual(captured["translations"], [{"id": "tr-1"}])
        self.assertEqual(captured["translation_units"], [{"unit_id": "unit-1"}])
        self.assertEqual(captured["translation_summary"], {"translated": 1})
        self.assertEqual(captured["translation_revision"], "rev-1")
        self.assertEqual(captured["compare_split_ratio"], 62)
        self.assertEqual(captured["panel_width"], 420)
        self.assertEqual(captured["chunks"], [{"id": "chunk-1"}])
        self.assertEqual(captured["analysis"], {"tldr": "Useful paper."})
        self.assertEqual(captured["ui"], {"page": "Page"})
        self.assertEqual(captured["settings"], {"view_mode": "continuous"})
        self.assertEqual(captured["height"], 900)


if __name__ == "__main__":
    unittest.main()
