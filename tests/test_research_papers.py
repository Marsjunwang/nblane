"""Tests for Paper Reading Studio core helpers."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.research_papers import (
    PaperSegment,
    create_paper_annotation,
    format_research_citations,
    import_paper_pdf,
    import_paper_search_results,
    load_paper_annotations,
    load_paper_library_tree,
    load_paper_pdf_bytes,
    load_paper_translations,
    move_papers_to_node,
    paper_overview,
    research_asset_root,
    save_paper_segments,
    text_hash,
    upsert_paper_library_node,
    upsert_paper_translations,
)
from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    load_research_sources,
    save_research_sources,
)
from nblane.core.research_workspace import (
    create_citation,
    create_chunk,
    upsert_research_claim,
)


PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>
endobj
trailer
<< /Root 1 0 R >>
%%EOF
"""


class TestResearchPapers(unittest.TestCase):
    def _profile(self, root: Path) -> Path:
        profile = root / "alice"
        profile.mkdir()
        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(
            inbox,
            "Grounded Claims",
            source_id="source:paper:grounded",
            kind="paper",
            visibility="private",
        )
        with patch("nblane.core.research_sources.git_backup.record_change"):
            save_research_sources(profile, inbox)
        return profile

    def test_pdf_asset_lives_outside_profile_and_updates_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self._profile(root)
            asset_root = root / "assets"
            with (
                patch.dict(os.environ, {"NBLANE_RESEARCH_ASSET_ROOT": str(asset_root)}),
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                asset = import_paper_pdf(
                    profile,
                    "source:paper:grounded",
                    PDF_BYTES,
                    "../paper.pdf",
                    pdf_url="https://example.com/paper.pdf",
                )
                loaded = load_paper_pdf_bytes(profile, "source:paper:grounded")

            source = load_research_sources(profile).by_id()["source:paper:grounded"]

        self.assertEqual(loaded, PDF_BYTES)
        self.assertTrue(asset.asset_ref.startswith("papers/"))
        self.assertFalse((profile / asset.asset_ref).exists())
        self.assertIn("profiles/alice", str(research_asset_root(profile)))
        self.assertEqual(source.metadata["pdf_asset_ref"], asset.asset_ref)
        self.assertEqual(source.metadata["pdf_byte_size"], len(PDF_BYTES))
        self.assertEqual(source.metadata["pdf_sha256"], asset.sha256)
        self.assertGreaterEqual(int(source.metadata["page_count"]), 1)
        self.assertNotIn(str(asset_root), yaml.dump(source.to_dict()))

    def test_rejects_non_pdf_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with self.assertRaisesRegex(ValueError, "PDF"):
                import_paper_pdf(profile, "source:paper:grounded", b"not a pdf", "x.txt")

    def test_library_tree_and_source_refs_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with (
                patch("nblane.core.research_papers.git_backup.record_change"),
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                node = upsert_paper_library_node(
                    profile,
                    "Memory",
                    node_id="paper-node:vla-memory",
                    description="Memory papers.",
                )
                changed = move_papers_to_node(
                    profile,
                    ["source:paper:grounded"],
                    node.id,
                )
            tree = load_paper_library_tree(profile)
            source = load_research_sources(profile).by_id()["source:paper:grounded"]

        self.assertEqual(changed, ["source:paper:grounded"])
        self.assertEqual(tree.nodes[0].title, "Memory")
        self.assertEqual(source.library_node_refs, ["paper-node:vla-memory"])

    def test_annotations_and_translations_are_segment_hash_aware(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            segment = PaperSegment(
                segment_id="seg:source-paper-grounded:00001",
                source_id=source_id,
                page=1,
                order=1,
                text="The memory encoder stores observations.",
                text_hash=text_hash("The memory encoder stores observations."),
                locator="p. 1",
            )
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(profile, source_id, [segment])
                ann = create_paper_annotation(
                    profile,
                    source_id,
                    "The memory encoder stores observations.",
                    page=1,
                    segment_refs=[segment.segment_id],
                    tags=["memory"],
                )
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "segment_id": segment.segment_id,
                            "source_hash": segment.text_hash,
                            "source_text": segment.text,
                            "target_lang": "zh",
                            "translated_text": "记忆编码器会存储观测。",
                        }
                    ],
                )
                save_paper_segments(
                    profile,
                    source_id,
                    [
                        PaperSegment(
                            segment_id=segment.segment_id,
                            source_id=source_id,
                            page=1,
                            order=1,
                            text="Changed text.",
                            text_hash=text_hash("Changed text."),
                            locator="p. 1",
                        )
                    ],
                )

            annotations = load_paper_annotations(profile, source_id)
            translations = load_paper_translations(profile, source_id)

        self.assertEqual(annotations[0].id, ann.id)
        self.assertEqual(annotations[0].segment_refs, [segment.segment_id])
        self.assertEqual(translations[0].status, "stale")
        self.assertIn("Source hash", " ".join(translations[0].warnings))

    def test_import_selected_search_results_dedupes_and_defaults_private(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            result = {
                "candidate_id": "candidate-a",
                "title": "A Paper",
                "authors": ["Alice"],
                "year": "2026",
                "doi": "10.1000/demo",
                "canonical_url": "https://example.com/a",
                "pdf_url": "https://example.com/a.pdf",
                "tags": ["vla"],
            }
            with patch("nblane.core.research_sources.git_backup.record_change"):
                imported = import_paper_search_results(
                    profile,
                    [result],
                    ["candidate-a"],
                    {"status": "reading", "library_node_refs": ["paper-node:vla"]},
                )
                duplicate = import_paper_search_results(
                    profile,
                    [result],
                    ["candidate-a"],
                    {},
                )
            sources = load_research_sources(profile).by_id()

        self.assertEqual(len(imported), 1)
        self.assertEqual(duplicate, [])
        self.assertEqual(sources[imported[0]].visibility, "private")
        self.assertEqual(sources[imported[0]].status, "reading")
        self.assertEqual(sources[imported[0]].library_node_refs, ["paper-node:vla"])
        self.assertEqual(sources[imported[0]].metadata["doi"], "10.1000/demo")

    def test_overview_and_citation_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with (
                patch("nblane.core.research_workspace.git_backup.record_change"),
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                chunk = create_chunk(
                    profile,
                    "source:paper:grounded",
                    "Claims should cite chunks.",
                    locator="p. 2",
                )
                claim = upsert_research_claim(
                    profile,
                    "Claims should cite chunks.",
                    source_refs=["source:paper:grounded"],
                    chunk_refs=[chunk.id],
                    status="ready",
                )
                citation = create_citation(
                    profile,
                    claim.id,
                    source_id="source:paper:grounded",
                    chunk_id=chunk.id,
                    locator="p. 2",
                    quote="Claims should cite chunks.",
                )
            overview = paper_overview(profile)
            bib = format_research_citations(profile, [citation.id], format="bibtex")
            md = format_research_citations(profile, [citation.id], format="markdown")

        self.assertEqual(overview["papers_total"], 1)
        self.assertEqual(overview["ready_research_claims"], 1)
        self.assertIn("@article", bib)
        self.assertIn("Grounded Claims", bib)
        self.assertIn("Claims should cite chunks.", md)


if __name__ == "__main__":
    unittest.main()
