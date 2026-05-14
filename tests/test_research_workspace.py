"""Tests for full Research Workspace facts."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    save_research_sources,
)
from nblane.core.research_workspace import (
    create_chunk,
    create_citation,
    draft_synthesis_from_claims,
    load_chunks,
    load_research_citations,
    load_research_claims,
    load_research_drafts,
    research_claim_to_evidence_candidate,
    research_draft_to_blog_candidate,
    upsert_research_claim,
)


class TestResearchWorkspace(unittest.TestCase):
    """Research artifacts stay source-aware until promoted."""

    def _profile(self, root: Path) -> Path:
        profile = root / "alice"
        profile.mkdir()
        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(
            inbox,
            "Grounded generation paper",
            source_id="source:paper:grounded",
            kind="paper",
            url="https://example.com/paper",
            visibility="public",
        )
        with patch("nblane.core.research_sources.git_backup.record_change"):
            save_research_sources(profile, inbox)
        return profile

    def test_source_chunk_claim_citation_draft_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.research_workspace.git_backup.record_change"):
                chunk = create_chunk(
                    profile,
                    "source:paper:grounded",
                    "Claims should be grounded in retrieved evidence.",
                    kind="excerpt",
                    locator="p. 3",
                )
                claim = upsert_research_claim(
                    profile,
                    "Grounding generated claims reduces unsupported statements.",
                    source_refs=["source:paper:grounded"],
                    chunk_refs=[chunk.id],
                    status="ready",
                    type="finding",
                )
                citation = create_citation(
                    profile,
                    claim.id,
                    source_id="source:paper:grounded",
                    chunk_id=chunk.id,
                    locator="p. 3",
                    quote="Claims should be grounded in retrieved evidence.",
                )
                draft = draft_synthesis_from_claims(
                    profile,
                    "Source-aware writing",
                    [claim.id],
                )

            loaded_chunks = load_chunks(profile, "source:paper:grounded")
            loaded_claims = load_research_claims(profile)
            loaded_citations = load_research_citations(profile)
            loaded_drafts = load_research_drafts(profile)
            blog_candidate = research_draft_to_blog_candidate(profile, draft["id"])

        self.assertEqual([item.id for item in loaded_chunks], [chunk.id])
        self.assertEqual(loaded_claims[0].citation_refs, [citation.id])
        self.assertEqual(loaded_citations[0].chunk_id, chunk.id)
        self.assertEqual(loaded_drafts[0]["claim_refs"], [claim.id])
        self.assertEqual(blog_candidate["related_sources"], ["source:paper:grounded"])
        self.assertEqual(blog_candidate["related_research_claims"], [claim.id])
        self.assertEqual(blog_candidate["related_citations"], [citation.id])

    def test_claim_requires_source_chunk_or_human_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.research_workspace.git_backup.record_change"):
                with self.assertRaisesRegex(ValueError, "source/chunk"):
                    upsert_research_claim(profile, "Unsupported claim")
                claim = upsert_research_claim(
                    profile,
                    "Human reading note.",
                    human_note=True,
                )

        self.assertTrue(claim.human_note)

    def test_research_claim_to_evidence_candidate_is_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.research_workspace.git_backup.record_change"):
                claim = upsert_research_claim(
                    profile,
                    "Grounded generation needs citation traces.",
                    source_refs=["source:paper:grounded"],
                )
            before = (profile / "research" / "claims.yaml").read_text(encoding="utf-8")

            patch_data = research_claim_to_evidence_candidate(profile, claim.id)

            after = (profile / "research" / "claims.yaml").read_text(encoding="utf-8")

        self.assertEqual(after, before)
        self.assertEqual(patch_data["node_updates"], [])
        self.assertEqual(patch_data["evidence_entries"][0]["review_status"], "needs_review")
        self.assertEqual(patch_data["evidence_entries"][0]["research_claim_refs"], [claim.id])
        self.assertFalse((profile / "skill-tree.yaml").exists())
        saved = yaml.safe_load(before)
        self.assertEqual(saved["claims"][0]["status"], "draft")


if __name__ == "__main__":
    unittest.main()
