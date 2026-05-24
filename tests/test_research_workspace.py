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
    build_synthesis_draft_review,
    create_chunk,
    create_citation,
    create_citation_from_chunk,
    duplicate_research_claim_groups,
    draft_synthesis_from_claims,
    load_chunks,
    load_research_citations,
    load_research_claims,
    load_research_drafts,
    merge_duplicate_research_claims,
    patch_research_claim,
    research_claim_to_evidence_candidate,
    research_draft_to_blog_candidate,
    research_draft_to_output_candidates,
    research_draft_to_project_update_candidate,
    research_draft_to_resume_bullet_candidates,
    research_output_project_options,
    request_citation_for_claim,
    select_research_export_scope,
    update_research_claim_links,
    update_research_claim_status,
    upsert_research_claim,
    verify_research_citation,
    verify_research_citations,
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
            tags=["grounding"],
            goal_refs=["goal:writing"],
            library_node_refs=["paper-node:grounded"],
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
            draft_review = build_synthesis_draft_review(profile, draft["id"])

        self.assertEqual([item.id for item in loaded_chunks], [chunk.id])
        self.assertEqual(loaded_claims[0].citation_refs, [citation.id])
        self.assertEqual(loaded_citations[0].chunk_id, chunk.id)
        self.assertEqual(loaded_drafts[0]["claim_refs"], [claim.id])
        self.assertEqual(blog_candidate["related_sources"], ["source:paper:grounded"])
        self.assertEqual(blog_candidate["related_research_claims"], [claim.id])
        self.assertEqual(blog_candidate["related_citations"], [citation.id])
        self.assertIn("## Outline", blog_candidate["body"])
        self.assertIn("## Argument Map", blog_candidate["body"])
        self.assertEqual(draft_review["coverage"]["citations"], 1)
        self.assertFalse(draft_review["warnings"]["missing_citation_claim_refs"])

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

    def test_claim_card_operations_patch_links_request_and_merge_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.research_workspace.git_backup.record_change"):
                chunk = create_chunk(
                    profile,
                    "source:paper:grounded",
                    "Exact source text for citation.",
                    locator="p. 4",
                )
                primary = upsert_research_claim(
                    profile,
                    "Exact source text needs citation.",
                    source_refs=["source:paper:grounded"],
                    status="draft",
                )
                duplicate = upsert_research_claim(
                    profile,
                    "Exact source text needs citation.",
                    source_refs=["source:paper:grounded"],
                    status="draft",
                    claim_id="rclaim:duplicate",
                )

                linked = update_research_claim_links(profile, primary.id, chunk_refs=[chunk.id])
                citation = create_citation_from_chunk(profile, primary.id, chunk.id)
                patched = patch_research_claim(
                    profile,
                    primary.id,
                    text="Exact source text needs a verified citation.",
                    type="finding",
                    confidence="high",
                    warnings=["check locator"],
                )
                requested = request_citation_for_claim(profile, duplicate.id, note="Find a stronger quote.")
                unlinked = update_research_claim_links(
                    profile,
                    primary.id,
                    citation_refs=[citation.id],
                    mode="remove",
                )
                update_research_claim_links(profile, primary.id, citation_refs=[citation.id])
                merged = merge_duplicate_research_claims(
                    profile,
                    primary.id,
                    [duplicate.id],
                    rationale="Duplicate review.",
                )

            claims = {claim.id: claim for claim in load_research_claims(profile)}
            verify = verify_research_citations(profile, [citation.id])
            duplicates = duplicate_research_claim_groups(profile)
            payload = build_research_claim_review_payload(profile, source_id="source:paper:grounded")

        self.assertEqual(linked.chunk_refs, [chunk.id])
        self.assertEqual(citation.source_id, "source:paper:grounded")
        self.assertEqual(citation.locator, "p. 4")
        self.assertEqual(patched.type, "finding")
        self.assertEqual(patched.confidence, "high")
        self.assertIn("citation_requested", requested.warnings)
        self.assertNotIn(citation.id, unlinked.citation_refs)
        self.assertIn(citation.id, merged.citation_refs)
        self.assertEqual(claims[duplicate.id].status, "dismissed")
        self.assertIn("Merged into", claims[duplicate.id].rationale)
        self.assertEqual(verify["ok"], 1)
        self.assertFalse(duplicates)
        self.assertEqual(payload["duplicate_claim_groups"], [])

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
        self.assertTrue(overview["pipeline"])
        claims_action = next(item for item in overview["next_actions"] if item["kind"] == "review_claims")
        private_action = next(item for item in overview["next_actions"] if item["kind"] == "review_private_publish_risk")
        self.assertEqual(claims_action["count"], 1)
        self.assertEqual(private_action["count"], 1)
        self.assertEqual(claims_action["target"]["surface"], "claims")
        self.assertEqual(claims_action["secondary_targets"][0]["surface"], "paper_library")
        self.assertEqual(claims_action["secondary_targets"][0]["focus"], "claims")
        self.assertEqual(private_action["target"]["surface"], "export")
        self.assertEqual(private_action["target"]["focus"], "private_publish_risk")
        self.assertEqual(overview["safety"]["private_publish_risk_refs"], ["source:note:private"])
        self.assertTrue(any(row["id"] == "no_pdf" and row["target"]["action"] == "attach_pdf" for row in overview["work_queues"]))
        self.assertEqual(manifest["private_source_refs"], ["source:note:private"])
        self.assertEqual(manifest["unpromoted_claim_refs"], [private_claim.id])
        self.assertFalse(manifest["broken_citation_refs"])
        self.assertFalse(manifest["publish_allowed"])
        self.assertEqual(export_payload["counts"]["blockers"], 2)

    def test_research_output_candidates_share_manifest_gate_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            (profile / "projects.yaml").write_text(
                yaml.dump(
                    {
                        "projects": [
                            {
                                "id": "demo_project",
                                "title": "Demo Project",
                                "status": "draft",
                            }
                        ]
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (profile / "resume-source.yaml").write_text(
                yaml.dump(
                    {
                        "profile": "alice",
                        "visibility": "private",
                        "basics": {"name": "Alice"},
                        "experiences": [],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            projects_before = (profile / "projects.yaml").read_text(encoding="utf-8")
            resume_before = (profile / "resume-source.yaml").read_text(encoding="utf-8")
            with patch("nblane.core.research_workspace.git_backup.record_change"):
                public_chunk = create_chunk(
                    profile,
                    "source:paper:grounded",
                    "Project updates need source-backed evidence.",
                    locator="p. 5",
                )
                public_claim = upsert_research_claim(
                    profile,
                    "Project updates can be drafted from grounded claims.",
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
                    quote="Project updates need source-backed evidence.",
                )
                private_claim = upsert_research_claim(
                    profile,
                    "Private notes identify a possible resume bullet.",
                    source_refs=["source:note:private"],
                    status="ready",
                    type="learning",
                )
                draft = draft_synthesis_from_claims(
                    profile,
                    "Candidate expansion",
                    [public_claim.id, private_claim.id],
                )

            project_options = research_output_project_options(profile)
            blog_candidate = research_draft_to_blog_candidate(profile, draft["id"])
            project_candidate = research_draft_to_project_update_candidate(
                profile,
                draft["id"],
                project_id="demo_project",
            )
            bullets = research_draft_to_resume_bullet_candidates(profile, draft["id"])
            output_candidates = research_draft_to_output_candidates(
                profile,
                draft["id"],
                project_id="demo_project",
            )
            manifest = build_research_export_manifest(
                profile,
                source_refs=project_candidate["related_sources"],
                claim_refs=project_candidate["related_research_claims"],
                citation_refs=project_candidate["related_citations"],
            )
            projects_after = (profile / "projects.yaml").read_text(encoding="utf-8")
            resume_after = (profile / "resume-source.yaml").read_text(encoding="utf-8")

        self.assertEqual(projects_after, projects_before)
        self.assertEqual(resume_after, resume_before)
        self.assertEqual(project_options[0]["id"], "demo_project")
        self.assertEqual(blog_candidate["kind"], "blog_draft")
        self.assertEqual(project_candidate["project_id"], "demo_project")
        self.assertEqual(project_candidate["related_sources"], ["source:paper:grounded", "source:note:private"])
        self.assertEqual(project_candidate["related_research_claims"], [public_claim.id, private_claim.id])
        self.assertEqual(project_candidate["related_citations"], [public_citation.id])
        self.assertEqual(len(bullets), 2)
        self.assertIn(private_claim.id, bullets[1]["related_research_claims"])
        self.assertTrue(any("no linked citation" in warning for warning in bullets[1]["warnings"]))
        self.assertEqual(output_candidates["project_update"]["project_id"], "demo_project")
        self.assertEqual(output_candidates["resume_bullets"][0]["kind"], "resume_bullet")
        blocker_kinds = {item["kind"] for item in manifest["blockers"]}
        self.assertIn("private_source", blocker_kinds)
        self.assertIn("unpromoted_research_claim", blocker_kinds)
        self.assertFalse(manifest["publish_allowed"])

    def test_export_scope_selects_collection_tag_and_claim_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with patch("nblane.core.research_workspace.git_backup.record_change"):
                chunk = create_chunk(
                    profile,
                    "source:paper:grounded",
                    "Collection scoped writing keeps citations nearby.",
                )
                public_claim = upsert_research_claim(
                    profile,
                    "Collection scope claim.",
                    source_refs=["source:paper:grounded"],
                    chunk_refs=[chunk.id],
                    status="promoted",
                )
                public_citation = create_citation(
                    profile,
                    public_claim.id,
                    source_id="source:paper:grounded",
                    chunk_id=chunk.id,
                    quote="Collection scoped writing keeps citations nearby.",
                )
                ready_private = upsert_research_claim(
                    profile,
                    "Ready private claim.",
                    source_refs=["source:note:private"],
                    status="ready",
                )

            collection = select_research_export_scope(
                profile,
                {
                    "library_node_refs": ["paper-node:grounded"],
                    "tags": ["grounding"],
                    "goal_refs": ["goal:writing"],
                },
            )
            ready = select_research_export_scope(profile, {"claim_statuses": ["ready"]})
            manual = build_research_export_payload(
                profile,
                scope={"claim_refs": [public_claim.id]},
            )

        self.assertEqual(collection["source_refs"], ["source:paper:grounded"])
        self.assertEqual(collection["claim_refs"], [public_claim.id])
        self.assertEqual(collection["citation_refs"], [public_citation.id])
        self.assertEqual(ready["claim_refs"], [ready_private.id])
        self.assertEqual(ready["source_refs"], ["source:note:private"])
        self.assertEqual(manual["manifest"]["claim_refs"], [public_claim.id])
        self.assertEqual(manual["manifest"]["citation_refs"], [public_citation.id])


if __name__ == "__main__":
    unittest.main()
