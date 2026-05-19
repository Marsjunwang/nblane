"""Tests for Paper Reading Studio core helpers."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.research_papers import (
    PaperPage,
    PaperSegment,
    create_reading_note_markdown,
    create_paper_annotation,
    extract_paper_segments,
    format_research_citations,
    grobid_tei_to_bibliography,
    grobid_tei_to_segments,
    import_paper_pdf,
    import_paper_search_results,
    load_paper_annotations,
    load_paper_library_tree,
    load_paper_pdf_bytes,
    load_paper_translations,
    move_papers_to_node,
    paper_overview,
    paper_pdf_asset_path,
    paper_rows,
    paper_citation_diagnostics,
    paper_source_diagnostics,
    research_asset_root,
    render_paper_page_preview,
    save_paper_pages,
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
    update_research_source,
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
                patch("nblane.core.research_sources.git_backup.record_change") as record_change,
            ):
                asset = import_paper_pdf(
                    profile,
                    "source:paper:grounded",
                    PDF_BYTES,
                    "../paper.pdf",
                    pdf_url="https://example.com/paper.pdf",
                )
                loaded = load_paper_pdf_bytes(profile, "source:paper:grounded")
                resolved_asset_path = paper_pdf_asset_path(profile, "source:paper:grounded")
                asset_path = research_asset_root(profile) / asset.asset_ref
                recorded_paths = [
                    Path(path)
                    for call in record_change.call_args_list
                    for path in (call.args[0] if call.args else [])
                ]

            source = load_research_sources(profile).by_id()["source:paper:grounded"]

            self.assertEqual(loaded, PDF_BYTES)
            self.assertEqual(resolved_asset_path, asset_path)
            self.assertTrue(asset.asset_ref.startswith("papers/"))
            self.assertFalse((profile / asset.asset_ref).exists())
            self.assertEqual(list(profile.rglob("*.pdf")), [])
            self.assertIn("profiles/alice", str(research_asset_root(profile)))
            self.assertTrue(asset_path.exists())
            self.assertTrue(recorded_paths)
            self.assertFalse(any(path == asset_path for path in recorded_paths))
            self.assertFalse(any(str(path).startswith(str(asset_root)) for path in recorded_paths))
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

    def test_page_preview_reports_missing_pdf_without_writing_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            before = sorted(path.relative_to(profile) for path in profile.rglob("*"))
            with self.assertRaises((FileNotFoundError, ValueError)):
                render_paper_page_preview(profile, "source:paper:grounded", 1)
            after = sorted(path.relative_to(profile) for path in profile.rglob("*"))

        self.assertEqual(after, before)

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

    def test_import_pdf_download_skips_unchecked_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            result = {
                "candidate_id": "candidate-needs-check",
                "title": "Unchecked PDF",
                "pdf_url": "https://example.com/unchecked.pdf",
                "needs_link_check": True,
            }
            with patch("nblane.core.research_sources.git_backup.record_change"):
                imported = import_paper_search_results(
                    profile,
                    [result],
                    ["candidate-needs-check"],
                    {"download_pdf": True},
                )
            source = load_research_sources(profile).by_id()[imported[0]]

        self.assertEqual(source.metadata["pdf_download_status"], "skipped_needs_link_check")
        self.assertNotIn("pdf_asset_ref", source.metadata)

    def test_grobid_tei_to_segments_and_bibliography(self) -> None:
        tei = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
          <text>
            <body>
              <div n="3"><head>Method</head><p n="3">Memory encoder stores observations.</p></div>
            </body>
            <back>
              <listBibl>
                <biblStruct>
                  <analytic>
                    <title>Useful Paper</title>
                    <author><persName><forename>Ada</forename><surname>Lovelace</surname></persName></author>
                  </analytic>
                  <monogr><imprint><date when="1843"/></imprint></monogr>
                </biblStruct>
              </listBibl>
            </back>
          </text>
        </TEI>"""

        segments = grobid_tei_to_segments("source:paper:grounded", tei)
        refs = grobid_tei_to_bibliography("source:paper:grounded", tei)

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].section_path, ["Method"])
        self.assertIn("§ Method", segments[0].locator)
        self.assertEqual(refs[0]["title"], "Useful Paper")
        self.assertEqual(refs[0]["year"], "1843")

    def test_structured_extraction_falls_back_when_grobid_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            with (
                patch("nblane.core.research_papers.grobid_readiness") as readiness,
                patch("nblane.core.research_papers.git_backup.record_change"),
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                readiness.return_value = {
                    "available": False,
                    "status": "unavailable",
                    "message": "GROBID unavailable in test",
                }
                save_paper_pages(
                    profile,
                    source_id,
                    [
                        PaperPage(
                            source_id=source_id,
                            page=1,
                            text="Fallback paragraph.",
                        )
                    ],
                )
                segments = extract_paper_segments(profile, source_id, backend="grobid")
            source = load_research_sources(profile).by_id()[source_id]
            diagnostics = paper_source_diagnostics(
                profile,
                source_id,
                grobid_status={"available": False, "message": "GROBID unavailable in test"},
            )

        self.assertEqual(segments[0].text, "Fallback paragraph.")
        self.assertEqual(source.metadata["structure_backend"], "pymupdf_fallback")
        self.assertIn("GROBID unavailable", " ".join(source.metadata["structured_extraction_warnings"]))
        self.assertIn("GROBID unavailable", diagnostics["badges"])

    def test_structured_extraction_clears_stale_grobid_warnings_on_success(self) -> None:
        tei = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
          <text><body><div><head>Abstract</head><p>Structured segment.</p></div></body></text>
        </TEI>"""
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            inbox = load_research_sources(profile)
            update_research_source(
                inbox,
                source_id,
                metadata={
                    "pdf_asset_ref": "papers/demo.pdf",
                    "structure_backend": "pymupdf_fallback",
                    "structured_extraction_warnings": [
                        "GROBID unavailable or returned no usable segments; used page-text fallback."
                    ],
                },
            )
            with (
                patch("nblane.core.research_sources.git_backup.record_change"),
                patch("nblane.core.research_papers.git_backup.record_change"),
            ):
                save_research_sources(profile, inbox)
            with (
                patch("nblane.core.research_papers.grobid_readiness") as readiness,
                patch("nblane.core.research_papers.process_grobid_fulltext") as process,
                patch("nblane.core.research_papers.git_backup.record_change"),
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                readiness.return_value = {"available": True, "status": "available"}
                process.return_value.tei_xml = tei
                segments = extract_paper_segments(profile, source_id, backend="grobid")
            source = load_research_sources(profile).by_id()[source_id]
            diagnostics = paper_source_diagnostics(
                profile,
                source_id,
                grobid_status={"available": True, "message": "GROBID ready"},
            )

        self.assertEqual(len(segments), 1)
        self.assertEqual(source.metadata["structure_backend"], "grobid")
        self.assertEqual(source.metadata["structured_extraction_warnings"], [])
        self.assertNotIn("GROBID unavailable", diagnostics["badges"])

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
            note = create_reading_note_markdown(
                profile,
                "source:paper:grounded",
                claim_refs=[claim.id],
                chunk_refs=[chunk.id],
                citation_refs=[citation.id],
            )

        self.assertEqual(overview["papers_total"], 1)
        self.assertEqual(overview["ready_research_claims"], 1)
        self.assertIn("@article", bib)
        self.assertIn("Grounded Claims", bib)
        self.assertIn("Claims should cite chunks.", md)
        self.assertIn("## Chunks", note)
        self.assertIn("## Claims", note)
        self.assertIn("## Citations", note)

    def test_quote_mismatch_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            with (
                patch("nblane.core.research_workspace.git_backup.record_change"),
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                chunk = create_chunk(
                    profile,
                    "source:paper:grounded",
                    "The grounded quote is here.",
                    locator="p. 2",
                )
                claim = upsert_research_claim(
                    profile,
                    "The grounded quote is here.",
                    source_refs=["source:paper:grounded"],
                    chunk_refs=[chunk.id],
                )
                create_citation(
                    profile,
                    claim.id,
                    source_id="source:paper:grounded",
                    chunk_id=chunk.id,
                    quote="A different quote.",
                )
            diagnostics = paper_citation_diagnostics(profile, "source:paper:grounded")

        self.assertTrue(any("quote does not match" in item for item in diagnostics))


if __name__ == "__main__":
    unittest.main()
