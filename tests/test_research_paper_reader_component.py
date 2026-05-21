"""Contract tests for the retired Streamlit Reader component boundary."""

from __future__ import annotations

import unittest

import nblane.research_paper_reader_component as reader
from nblane.research_paper_reader_component import events


class TestResearchPaperReaderComponent(unittest.TestCase):
    def test_static_reader_runtime_is_retired(self) -> None:
        self.assertFalse(reader.research_paper_reader_component_available())
        self.assertIsNone(reader._get_component_func())

    def test_event_contract_exports_reader_event_names(self) -> None:
        self.assertIn("request_reader_context", events.EVENT_NAMES)
        self.assertIn("request_page_previews", events.EVENT_NAMES)
        self.assertIn("reader_state_changed", events.EVENT_NAMES)
        self.assertIn("retry_translation_scope", events.EVENT_NAMES)
        self.assertIn("prepare_reader_artifacts", events.EVENT_NAMES)
        self.assertIn("analyze_paper", events.EVENT_NAMES)
        self.assertEqual(events.clean_page_list([1, "2", 2, 0, "bad", 3]), [1, 2, 3])

    def test_reader_state_payload_includes_workbench_state_fields(self) -> None:
        annotations = events.ReaderStatePayload.__annotations__

        self.assertIn("left_rail_collapsed", annotations)
        self.assertIn("active_left_tab", annotations)
        self.assertIn("translation_source_visible", annotations)
        self.assertIn("active_translation_anchor", annotations)


if __name__ == "__main__":
    unittest.main()
