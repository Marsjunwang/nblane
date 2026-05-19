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
        self.assertIn("NBLANE_READER_SEND_FULL_PDF", page_source)
        self.assertIn('pdf_base64=_reader_pdf_base64(source_id)', page_source)

        actions = set(re.findall(r'emitAction\("([^"]+)"', html))
        self.assertGreaterEqual(
            actions,
            {
                "selection_created",
                "annotation_create",
                "create_chunk_from_selection",
                "create_citation",
                "translate_selection",
                "explain_selection",
                "ask_paper",
                "jump_to_annotation",
                "page_changed",
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


if __name__ == "__main__":
    unittest.main()
