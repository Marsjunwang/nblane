"""Tests for Research Source Inbox helpers."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.research_sources import (
    ResearchReading,
    ResearchSourceInbox,
    add_research_source,
    apply_research_evidence_candidate,
    archive_research_source,
    generate_reading_draft,
    load_research_sources,
    research_evidence_patch,
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

    def test_reading_fields_round_trip(self) -> None:
        """Reading annotations stay source-scoped in sources.yaml."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            inbox = ResearchSourceInbox(profile="alice")
            source = add_research_source(
                inbox,
                "Paper",
                source_id="source:research:20260513-001",
                kind="paper",
            )
            update_research_source(
                inbox,
                source.id,
                evidence_refs=["ev_paper"],
                reading=ResearchReading(
                    excerpt="A useful excerpt.",
                    translation="一段有用摘录。",
                    summary="Useful paper.",
                    key_points=["Point one"],
                    claim_candidates=[
                        {
                            "id": "rclaim:source-research-20260513-001:001",
                            "text": "Useful paper.",
                            "type": "learning",
                            "source_refs": [source.id],
                            "citation_refs": [],
                            "confidence": "medium",
                            "warnings": [],
                        }
                    ],
                    citations=[
                        {
                            "id": "cite:source-research-20260513-001:001",
                            "label": "Paper",
                            "title": "Paper",
                            "url": "",
                        }
                    ],
                    synthesis_notes="Use after review.",
                ),
            )

            with patch("nblane.core.research_sources.date", _FakeDate):
                save_research_sources(profile, inbox)

            loaded = load_research_sources(profile)

        loaded_source = loaded.sources[0]
        self.assertEqual(loaded_source.evidence_refs, ["ev_paper"])
        self.assertEqual(loaded_source.reading.translation, "一段有用摘录。")
        self.assertEqual(loaded_source.reading.claim_candidates[0]["type"], "learning")

    def test_generate_reading_draft_fallback(self) -> None:
        """Reading draft fallback is useful without configured AI."""
        inbox = ResearchSourceInbox(profile="alice")
        source = add_research_source(
            inbox,
            "Interesting web article",
            source_id="source:research:20260513-001",
            kind="web",
            url="https://example.com/article",
        )

        with patch("nblane.core.research_sources.llm_client.is_configured", return_value=False):
            reading, warnings = generate_reading_draft(
                source,
                "The article argues that source-grounded claims reduce hallucination.",
            )

        self.assertTrue(warnings)
        self.assertIn("source-grounded", reading.summary)
        self.assertEqual(reading.claim_candidates[0]["source_refs"], [source.id])
        self.assertEqual(reading.citations[0]["url"], "https://example.com/article")

    def test_research_evidence_patch_is_evidence_only(self) -> None:
        """Research patches do not write skill-tree node updates."""
        inbox = ResearchSourceInbox(profile="alice")
        source = add_research_source(
            inbox,
            "Interesting web article",
            source_id="source:research:20260513-001",
            kind="web",
        )
        reading = ResearchReading(summary="A reviewed source summary.")

        patch_data = research_evidence_patch(source, reading)

        self.assertEqual(patch_data["node_updates"], [])
        self.assertEqual(patch_data["evidence_entries"][0]["type"], "learning")
        self.assertEqual(
            patch_data["evidence_entries"][0]["source_refs"],
            [source.id],
        )
        self.assertEqual(
            patch_data["evidence_entries"][0]["review_status"],
            "needs_review",
        )

    def test_apply_research_evidence_candidate_writes_pool_source_and_activity(self) -> None:
        """Confirmed research evidence writes only evidence/source/activity files."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "alice"
            profile.mkdir()
            (profile / "skill-tree.yaml").write_text("sentinel", encoding="utf-8")
            (profile / "evidence-pool.yaml").write_text(
                yaml.dump(
                    {
                        "profile": "alice",
                        "updated": "2026-05-01",
                        "evidence_entries": [],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            inbox = ResearchSourceInbox(profile="alice")
            source = add_research_source(
                inbox,
                "Interesting paper",
                source_id="source:research:20260513-001",
                kind="paper",
                url="https://example.com/paper",
            )
            save_research_sources(profile, inbox)
            patch_data = research_evidence_patch(
                source,
                ResearchReading(summary="Paper summary."),
            )

            with (
                patch("nblane.core.research_sources.PROFILES_DIR", root),
                patch("nblane.core.profile_io.PROFILES_DIR", root),
                patch("nblane.core.agent_activity.profile_dir", lambda _name: profile),
                patch("nblane.core.research_sources.git_backup.record_change"),
                patch("nblane.core.profile_io.git_backup.record_change"),
                patch("nblane.core.agent_activity.git_backup.record_change"),
            ):
                result = apply_research_evidence_candidate(
                    "alice",
                    source.id,
                    patch_data,
                )

            pool = yaml.safe_load((profile / "evidence-pool.yaml").read_text(encoding="utf-8"))
            loaded = load_research_sources(profile)
            activity = yaml.safe_load((profile / "agent-activity.yaml").read_text(encoding="utf-8"))
            skill_tree_text = (profile / "skill-tree.yaml").read_text(encoding="utf-8")

        self.assertTrue(result["evidence_id"].startswith("2026"))
        self.assertEqual(pool["evidence_entries"][0]["source_refs"], [source.id])
        self.assertEqual(loaded.sources[0].evidence_refs, [result["evidence_id"]])
        self.assertEqual(skill_tree_text, "sentinel")
        self.assertEqual(activity["items"][0]["source_page"], "Research")
        self.assertEqual(activity["items"][0]["target_owner"], "evidence_pool")


if __name__ == "__main__":
    unittest.main()
