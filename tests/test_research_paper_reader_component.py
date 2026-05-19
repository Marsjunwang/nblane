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
        self.assertIn("continuousDocument", html)
        self.assertIn("IntersectionObserver", html)
        self.assertIn("scale_mode", html)
        self.assertIn("overscan_pages", html)
        self.assertIn("NBLANE_READER_SEND_FULL_PDF", page_source)
        self.assertIn('pdf_base64=_reader_pdf_base64(source_id)', page_source)
        self.assertIn('pdf_url=_reader_pdf_url(source_id)', page_source)
        self.assertIn('"view_mode": "continuous"', page_source)
        self.assertIn('"scale_mode": "fit-width"', page_source)
        self.assertIn('"auto_save_progress": True', page_source)

        actions = set(re.findall(r'emitAction\("([^"]+)"', html))
        self.assertGreaterEqual(
            actions,
            {
                "selection_created",
                "annotation_create",
                "create_chunk_from_selection",
                "create_citation",
                "translate_selection",
                "translate_full_paper",
                "translate_visible_pages",
                "explain_selection",
                "ask_paper",
                "jump_to_annotation",
                "page_changed",
                "viewport_changed",
                "request_page_preview",
            },
        )

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
                chunks=[{"id": "chunk-1"}],
                ui={"page": "Page"},
                settings={"view_mode": "continuous"},
                height=900,
            )

        self.assertIsNone(event)
        self.assertEqual(captured["pages"], [{"page": 1}])
        self.assertEqual(captured["segments"], [{"segment_id": "seg-1"}])
        self.assertEqual(captured["annotations"], [{"id": "ann-1"}])
        self.assertEqual(captured["translations"], [{"id": "tr-1"}])
        self.assertEqual(captured["chunks"], [{"id": "chunk-1"}])
        self.assertEqual(captured["ui"], {"page": "Page"})
        self.assertEqual(captured["settings"], {"view_mode": "continuous"})
        self.assertEqual(captured["height"], 900)


if __name__ == "__main__":
    unittest.main()
