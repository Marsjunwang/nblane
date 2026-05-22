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
    build_research_claim_review_payload,
    build_research_export_manifest,
    build_research_export_payload,
    build_research_overview_payload,
    create_chunk,
    create_citation,
    draft_synthesis_from_claims,
    load_chunks,
    load_research_citations,
    load_research_claims,
    load_research_drafts,
    research_claim_to_evidence_candidate,
    research_draft_to_blog_candidate,
    update_research_claim_links,
    update_research_claim_status,
    upsert_research_claim,
    verify_research_citation,
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
        add_research_source(
            inbox,
            "Private field notes",
            source_id="source:note:private",
            kind="note",
            visibility="private",
            status="reading",
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

    def test_evidence_candidate_infers_source_refs_from_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.research_workspace.git_backup.record_change"):
                chunk = create_chunk(
                    profile,
                    "source:paper:grounded",
                    "Claims should be grounded in retrieved evidence.",
                )
                claim = upsert_research_claim(
                    profile,
                    "Chunk-only claims can still resolve their source.",
                    chunk_refs=[chunk.id],
                )

            patch_data = research_claim_to_evidence_candidate(profile, claim.id)
            review = build_research_claim_review_payload(profile, source_id="source:paper:grounded")

        self.assertEqual(patch_data["evidence_entries"][0]["source_refs"], ["source:paper:grounded"])
        self.assertEqual(review["claim_cards"][0]["source_refs"], ["source:paper:grounded"])

    def test_review_payload_status_links_and_quote_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.research_workspace.git_backup.record_change"):
                chunk = create_chunk(
                    profile,
                    "source:paper:grounded",
                    "Claims should be grounded in retrieved evidence.",
                    locator="p. 3",
                )
                claim = upsert_research_claim(
                    profile,
                    "Grounded claims need exact citations.",
                    source_refs=["source:paper:grounded"],
                    chunk_refs=[chunk.id],
                )
                citation = create_citation(
                    profile,
                    claim.id,
                    source_id="source:paper:grounded",
                    chunk_id=chunk.id,
                    quote="This quote is not in the chunk.",
                )

                ready = update_research_claim_status(
                    profile,
                    claim.id,
                    "ready",
                    note="Reviewed for source awareness.",
                )
                linked = update_research_claim_links(
                    profile,
                    claim.id,
                    citation_refs=[citation.id],
                )

            check = verify_research_citation(profile, citation.id)
            payload = build_research_claim_review_payload(
                profile,
                source_id="source:paper:grounded",
            )

        self.assertEqual(ready.status, "ready")
        self.assertEqual(linked.citation_refs, [citation.id])
        self.assertFalse(check["ok"])
        self.assertEqual(check["level"], "warning")
        self.assertEqual(payload["summary"]["quote_warnings"], 1)
        self.assertEqual(payload["claim_cards"][0]["citation_status"], "weak")
        self.assertEqual(payload["claim_cards"][0]["quote_status"], "warning")
        self.assertEqual(payload["citation_cards"][0]["quote_check"]["level"], "warning")

    def test_overview_and_export_manifest_surface_review_risks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.research_workspace.git_backup.record_change"):
                public_chunk = create_chunk(
                    profile,
                    "source:paper:grounded",
                    "Claims should be grounded in retrieved evidence.",
                    locator="p. 3",
                )
                public_claim = upsert_research_claim(
                    profile,
                    "Grounding generated claims reduces unsupported statements.",
                    source_refs=["source:paper:grounded"],
                    chunk_refs=[public_chunk.id],
                    status="promoted",
                    type="finding",
                )
                public_citation = create_citation(
                    profile,
                    public_claim.id,
                    source_id="source:paper:grounded",
                    chunk_id=public_chunk.id,
                    quote="Claims should be grounded in retrieved evidence.",
                )
                private_claim = upsert_research_claim(
                    profile,
                    "Private notes suggest a future experiment.",
                    source_refs=["source:note:private"],
                    status="ready",
                    type="hypothesis",
                )
                draft_synthesis_from_claims(
                    profile,
                    "Grounded writing",
                    [public_claim.id, private_claim.id],
                )

            overview = build_research_overview_payload(profile)
            manifest = build_research_export_manifest(
                profile,
                claim_refs=[public_claim.id, private_claim.id],
                citation_refs=[public_citation.id],
            )
            export_payload = build_research_export_payload(
                profile,
                claim_refs=[public_claim.id, private_claim.id],
                citation_refs=[public_citation.id],
            )

        self.assertEqual(overview["funnel_counts"]["sources"], 2)
        self.assertEqual(overview["funnel_counts"]["claims_ready"], 1)
        self.assertEqual(overview["funnel_counts"]["claims_promoted"], 1)
        self.assertIn("review_claims", [item["kind"] for item in overview["next_actions"]])
        self.assertIn("review_private_publish_risk", [item["kind"] for item in overview["next_actions"]])
        self.assertEqual(manifest["private_source_refs"], ["source:note:private"])
        self.assertEqual(manifest["unpromoted_claim_refs"], [private_claim.id])
        self.assertFalse(manifest["broken_citation_refs"])
        self.assertFalse(manifest["publish_allowed"])
        self.assertEqual(export_payload["counts"]["blockers"], 2)


if __name__ == "__main__":
    unittest.main()
