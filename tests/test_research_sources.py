"""Tests for Research Source Inbox helpers."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    archive_research_source,
    load_research_sources,
    save_research_sources,
    update_research_source,
)


class _FakeDate:
    @staticmethod
    def today() -> date:
        return date(2026, 5, 13)


class TestResearchSources(unittest.TestCase):
    """Sources stay source-aware and do not write evidence."""

    def test_add_source_assigns_stable_id_and_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            inbox = ResearchSourceInbox(profile="alice")

            with patch("nblane.core.research_sources.date", _FakeDate):
                source = add_research_source(
                    inbox,
                    "Interesting paper",
                    kind="paper",
                    captured_at="2026-05-13T12:00:00+00:00",
                    project_refs=["project:nblane"],
                )
                second = add_research_source(
                    inbox,
                    "Repo",
                    kind="repo",
                    captured_at="2026-05-13T12:10:00+00:00",
                )

            self.assertEqual(source.id, "source:research:20260513-001")
            self.assertEqual(second.id, "source:research:20260513-002")

            update_research_source(inbox, source.id, status="reading")
            archive_research_source(inbox, second.id)

            with patch("nblane.core.research_sources.date", _FakeDate):
                save_research_sources(profile, inbox)

            loaded = load_research_sources(profile)
            saved = yaml.safe_load(
                (profile / "research" / "sources.yaml").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(saved["updated"], "2026-05-13")
        self.assertEqual(loaded.sources[0].status, "reading")
        self.assertEqual(loaded.sources[1].status, "archived")
        self.assertFalse((profile / "evidence-pool.yaml").exists())

    def test_duplicate_id_rejected(self) -> None:
        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(
            inbox,
            "One",
            source_id="source:research:20260513-001",
        )
        with self.assertRaises(ValueError):
            add_research_source(
                inbox,
                "Two",
                source_id="source:research:20260513-001",
            )


if __name__ == "__main__":
    unittest.main()
