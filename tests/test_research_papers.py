"""Tests for Paper Reading Studio core helpers."""

from __future__ import annotations

import os
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

from nblane.core.research_papers import (
    NO_LLM_TRANSLATION_WARNING,
    PaperPage,
    PaperSegment,
    PaperSearchResult,
    PaperStructureUnit,
    _reader_outline_from_segments,
    build_reader_payload,
    build_paper_layout_units,
    build_paper_structure_units,
    create_reading_note_markdown,
    ensure_paper_reading_artifacts,
    create_paper_annotation,
    extract_paper_figures,
    extract_paper_segments,
    format_research_citations,
    get_stable_pdf_url,
    grobid_tei_to_bibliography,
    grobid_tei_to_segments,
    import_paper_pdf,
    import_paper_search_results,
    load_paper_annotations,
    load_paper_library_tree,
    load_paper_pdf_bytes,
    load_paper_structure_units,
    load_paper_translations,
    migrate_legacy_translations_to_segments,
    move_papers_to_node,
    paper_overview,
    paper_pdf_asset_path,
    paper_rows,
    pymupdf_available,
    paper_citation_diagnostics,
    paper_source_diagnostics,
    reader_translation_structure_units,
    research_asset_root,
    render_paper_page_preview,
    save_paper_pages,
    save_paper_segments,
    save_paper_structure_units,
    search_papers_with_codex,
    text_hash,
    translate_full_paper,
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

    def test_selection_translations_are_scoped_by_selection_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            first_hash = text_hash("A selected sentence.")
            second_hash = text_hash("Another selected sentence.")

            with patch("nblane.core.research_papers.git_backup.record_change"):
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "scope_type": "selection",
                            "scope_ref": first_hash,
                            "segment_id": "selection:first",
                            "source_hash": first_hash,
                            "source_text": "A selected sentence.",
                            "target_lang": "zh",
                            "translated_text": "第一句译文。",
                        },
                        {
                            "scope_type": "selection",
                            "scope_ref": second_hash,
                            "segment_id": "selection:second",
                            "source_hash": second_hash,
                            "source_text": "Another selected sentence.",
                            "target_lang": "zh",
                            "translated_text": "第二句译文。",
                        },
                    ],
                )
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "scope_type": "selection",
                            "scope_ref": first_hash,
                            "segment_id": "selection:first",
                            "source_hash": first_hash,
                            "source_text": "A selected sentence.",
                            "target_lang": "zh",
                            "translated_text": "第一句更新译文。",
                        }
                    ],
                )

            translations = load_paper_translations(profile, source_id)
            by_scope = {(row.scope_type, row.scope_ref): row for row in translations}

        self.assertEqual(len(by_scope), 2)
        self.assertEqual(by_scope[("selection", first_hash)].translated_text, "第一句更新译文。")
        self.assertEqual(by_scope[("selection", second_hash)].translated_text, "第二句译文。")
        self.assertEqual(by_scope[("selection", first_hash)].status, "translated")

    def test_translation_upsert_dedupes_by_scope_ref_and_target_lang(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            scope_ref = text_hash("A reusable selection.")

            with patch("nblane.core.research_papers.git_backup.record_change"):
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "id": "tr:first",
                            "scope_type": "selection",
                            "scope_ref": scope_ref,
                            "source_hash": scope_ref,
                            "source_text": "A reusable selection.",
                            "target_lang": "zh",
                            "translated_text": "旧译文。",
                        }
                    ],
                )
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "id": "tr:second",
                            "scope_type": "selection",
                            "scope_ref": scope_ref,
                            "source_hash": scope_ref,
                            "source_text": "A reusable selection.",
                            "target_lang": "zh",
                            "translated_text": "新译文。",
                        }
                    ],
                )

            translations = load_paper_translations(profile, source_id)

        self.assertEqual(len(translations), 1)
        self.assertEqual(translations[0].id, "tr:first")
        self.assertEqual(translations[0].translated_text, "新译文。")

    def test_translation_rows_accept_provider_text_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            first_hash = text_hash("Alias one.")
            second_hash = text_hash("Alias two.")

            with patch("nblane.core.research_papers.git_backup.record_change"):
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "scope_type": "selection",
                            "scope_ref": first_hash,
                            "source_hash": first_hash,
                            "source_text": "Alias one.",
                            "target_lang": "zh",
                            "text": "第一条别名译文。",
                        },
                        {
                            "scope_type": "selection",
                            "scope_ref": second_hash,
                            "source_hash": second_hash,
                            "source_text": "Alias two.",
                            "target_lang": "zh",
                            "translation": "第二条别名译文。",
                        },
                    ],
                )

            path = profile / "research" / "translations" / "source-paper-grounded.jsonl"
            legacy_row = {
                "id": "tr:legacy",
                "source_id": source_id,
                "scope_type": "selection",
                "scope_ref": "legacy",
                "source_hash": "legacy",
                "source_text": "Legacy row.",
                "target_lang": "zh",
                "target_text": "旧行译文。",
            }
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(legacy_row, ensure_ascii=False) + "\n")

            translations = load_paper_translations(profile, source_id)
            by_scope = {row.scope_ref: row.translated_text for row in translations}

        self.assertEqual(by_scope[first_hash], "第一条别名译文。")
        self.assertEqual(by_scope[second_hash], "第二条别名译文。")
        self.assertEqual(by_scope["legacy"], "旧行译文。")

    def test_build_reader_payload_limits_context_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            pages = [
                PaperPage(source_id=source_id, page=index, text=f"Page {index}", text_hash=text_hash(f"Page {index}"))
                for index in range(1, 13)
            ]
            segments = [
                PaperSegment(
                    segment_id=f"seg:{index}",
                    source_id=source_id,
                    page=index,
                    order=index,
                    text=f"Segment {index}",
                    text_hash=text_hash(f"Segment {index}"),
                )
                for index in range(1, 13)
            ]
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_pages(profile, source_id, pages)
                save_paper_segments(profile, source_id, segments)
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "segment_id": segment.segment_id,
                            "source_hash": segment.text_hash,
                            "source_text": segment.text,
                            "target_lang": "zh",
                            "translated_text": f"zh {segment.page}",
                        }
                        for segment in segments
                    ],
                )

            with (
                patch("nblane.core.research_papers.render_paper_page_preview", return_value={"page": 1, "data_url": "data:image/png;base64,x"}),
                patch("nblane.core.research_papers.get_stable_pdf_url", return_value="/media/stable.pdf"),
            ):
                payload = build_reader_payload(
                    profile,
                    source_id,
                    page=10,
                    requested_pages={5},
                    target_lang="zh",
                )

        segment_pages = {row["page"] for row in payload["segments"]}
        translation_pages = {row["page"] for row in payload["translations"]}

        self.assertEqual(segment_pages, {5, 9, 10, 11})
        self.assertEqual(translation_pages, {5, 9, 10, 11})
        self.assertEqual(payload["context_window"]["pages"], [5, 9, 10, 11])

    def test_build_reader_payload_keeps_unpaged_structured_segments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            pages = [
                PaperPage(source_id=source_id, page=1, text="Page 1", text_hash=text_hash("Page 1")),
                PaperPage(source_id=source_id, page=2, text="Page 2", text_hash=text_hash("Page 2")),
            ]
            segments = [
                PaperSegment(
                    segment_id="seg:unpaged:00001",
                    source_id=source_id,
                    page=0,
                    order=1,
                    text="Structured segment without PDF page.",
                    text_hash=text_hash("Structured segment without PDF page."),
                )
            ]
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_pages(profile, source_id, pages)
                save_paper_segments(profile, source_id, segments)
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "segment_id": segments[0].segment_id,
                            "source_hash": segments[0].text_hash,
                            "source_text": segments[0].text,
                            "target_lang": "zh",
                            "translated_text": "无页码结构化段落译文。",
                        },
                        {
                            "scope_type": "page",
                            "scope_ref": f"page:1:{pages[0].text_hash}",
                            "page": 1,
                            "source_hash": pages[0].text_hash,
                            "source_text": pages[0].text,
                            "target_lang": "zh",
                            "translated_text": "第一页译文。",
                        },
                    ],
                )

            payload = build_reader_payload(
                profile,
                source_id,
                page=1,
                requested_pages={1, 2},
                target_lang="zh",
                include_page_previews=False,
            )

        self.assertEqual([row["segment_id"] for row in payload["segments"]], ["seg:unpaged:00001"])
        self.assertIn(
            "无页码结构化段落译文。",
            [row["translated_text"] for row in payload["translations"]],
        )
        self.assertIn("translation_units", payload)
        self.assertIn("translation_summary", payload)
        self.assertIn("translation_revision", payload)
        self.assertEqual(payload["compare_split_ratio"], 50)
        self.assertEqual(payload["panel_width"], 340)
        units_by_scope = {row["scope_ref"]: row for row in payload["translation_units"]}
        self.assertEqual(units_by_scope["seg:unpaged:00001"]["translated_text"], "无页码结构化段落译文。")
        self.assertNotIn(f"page:1:{pages[0].text_hash}", units_by_scope)
        self.assertEqual({row["scope_type"] for row in payload["translation_units"]}, {"segment"})
        self.assertEqual(payload["translation_summary"], {"translated": 1, "missing": 0, "stale": 0, "failed": 0})

    def test_build_reader_payload_prefers_layout_units_when_layout_translations_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            page_hash = text_hash("Whole page text.")
            layout_hash = text_hash("Positioned body text")
            layout_scope = "layout:v2:1:00001:abc123"
            table_scope = "layout:v2:1:00002:table"
            layout_units = [
                {
                    "unit_id": layout_scope,
                    "anchor_id": layout_scope,
                    "scope_type": "layout",
                    "scope_ref": layout_scope,
                    "page": 1,
                    "order": 1,
                    "kind": "paragraph",
                    "locator": "p. 1",
                    "source_text": "Positioned body text",
                    "source_hash": layout_hash,
                    "translatable": True,
                    "font_size": 9.5,
                    "line_count": 2,
                    "rects": [
                        {
                            "x": 10,
                            "y": 20,
                            "w": 80,
                            "h": 24,
                            "x_pct": 0.05,
                            "y_pct": 0.10,
                            "w_pct": 0.40,
                            "h_pct": 0.12,
                            "page_width": 200,
                            "page_height": 200,
                        }
                    ],
                },
                {
                    "unit_id": table_scope,
                    "anchor_id": table_scope,
                    "scope_type": "layout",
                    "scope_ref": table_scope,
                    "page": 1,
                    "order": 2,
                    "kind": "table_cell",
                    "locator": "p. 1",
                    "source_text": "Table cell text",
                    "source_hash": text_hash("Table cell text"),
                    "translatable": True,
                    "rects": [{"x": 90, "y": 20, "w": 48, "h": 20, "page_width": 200, "page_height": 200}],
                    "table_id": "table:1",
                    "row": 0,
                    "col": 1,
                },
                {
                    "unit_id": "layout:v2:1:00003:symbol",
                    "anchor_id": "layout:v2:1:00003:symbol",
                    "scope_type": "layout",
                    "scope_ref": "layout:v2:1:00003:symbol",
                    "page": 1,
                    "order": 3,
                    "kind": "symbol",
                    "locator": "p. 1",
                    "source_text": "%",
                    "source_hash": text_hash("%"),
                    "translatable": False,
                    "rects": [{"x": 95, "y": 20, "w": 8, "h": 8, "page_width": 200, "page_height": 200}],
                },
                {
                    "unit_id": "layout:v2:1:00004:figlabel",
                    "anchor_id": "layout:v2:1:00004:figlabel",
                    "scope_type": "layout",
                    "scope_ref": "layout:v2:1:00004:figlabel",
                    "page": 1,
                    "order": 4,
                    "kind": "figure_label",
                    "locator": "p. 1",
                    "source_text": "Dense axis label",
                    "source_hash": text_hash("Dense axis label"),
                    "translatable": False,
                    "display_source": False,
                    "font_size": 6.0,
                    "line_count": 1,
                    "rects": [{"x": 120, "y": 120, "w": 32, "h": 9, "page_width": 200, "page_height": 200}],
                },
            ]
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_pages(
                    profile,
                    source_id,
                    [PaperPage(source_id=source_id, page=1, text="Whole page text.", text_hash=page_hash)],
                )
                save_paper_segments(
                    profile,
                    source_id,
                    [
                        PaperSegment(
                            segment_id="seg:1",
                            source_id=source_id,
                            page=1,
                            order=1,
                            text="Segment text.",
                            text_hash=text_hash("Segment text."),
                        )
                    ],
                )
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "scope_type": "layout",
                            "scope_ref": layout_scope,
                            "source_hash": layout_hash,
                            "source_text": "Positioned body text",
                            "target_lang": "zh",
                            "page": 1,
                            "translated_text": "正文译文。",
                        },
                        {
                            "scope_type": "layout",
                            "scope_ref": table_scope,
                            "source_hash": text_hash("Table cell text"),
                            "source_text": "Table cell text",
                            "target_lang": "zh",
                            "page": 1,
                            "translated_text": "表格单元译文不应显示。",
                        },
                        {
                            "scope_type": "layout",
                            "scope_ref": "layout:v2:1:00004:figlabel",
                            "source_hash": text_hash("Dense axis label"),
                            "source_text": "Dense axis label",
                            "target_lang": "zh",
                            "page": 1,
                            "translated_text": "旧图内标签译文不应显示。",
                        }
                    ],
                )

            with patch("nblane.core.research_papers.build_paper_layout_units", return_value=layout_units):
                payload = build_reader_payload(
                    profile,
                    source_id,
                    page=1,
                    requested_pages={1},
                    target_lang="zh",
                    include_page_previews=False,
                )

            stale_units = [
                {
                    **layout_units[0],
                    "source_text": "Changed positioned body text",
                    "source_hash": text_hash("Changed positioned body text"),
                }
            ]
            with patch("nblane.core.research_papers.build_paper_layout_units", return_value=stale_units):
                stale_payload = build_reader_payload(
                    profile,
                    source_id,
                    page=1,
                    requested_pages={1},
                    target_lang="zh",
                    include_page_previews=False,
                )

        self.assertEqual({row["scope_type"] for row in payload["translation_units"]}, {"structure"})
        units_by_scope = {row["scope_ref"]: row for row in payload["translation_units"]}
        structure_units = list(units_by_scope.values())
        self.assertEqual(len(structure_units), 1)
        self.assertEqual(structure_units[0]["source_text"], "Positioned body text")
        self.assertEqual(structure_units[0]["translated_text"], "正文译文。")
        self.assertEqual(structure_units[0]["status"], "translated")
        self.assertNotIn("seg:1", units_by_scope)
        self.assertNotIn(table_scope, units_by_scope)
        self.assertEqual(payload["page_models"], [{"page": 1, "width": 200.0, "height": 200.0, "rotation": 0}])
        self.assertEqual(payload["translation_summary"], {"translated": 1, "missing": 0, "stale": 0, "failed": 0})
        self.assertEqual(stale_payload["translation_units"][0]["status"], "translated")
        self.assertEqual(stale_payload["translation_summary"], {"translated": 1, "missing": 0, "stale": 0, "failed": 0})

    def test_build_paper_layout_units_outputs_stable_geometry_and_figure_labels(self) -> None:
        if not pymupdf_available():
            self.skipTest("PyMuPDF is not available")
        import fitz  # type: ignore[import-not-found]

        doc = fitz.open()
        page = doc.new_page(width=240, height=320)
        page.insert_text((24, 32), "A Precise Title", fontsize=18)
        page.insert_textbox(
            fitz.Rect(24, 60, 210, 92),
            "This is a main body paragraph for layout extraction.",
            fontsize=10,
        )
        page.insert_text((24, 120), "Figure 1. A useful caption", fontsize=10)
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10), 0)
        pix.clear_with(0xEEEEEE)
        page.insert_image(fitz.Rect(40, 150, 190, 220), stream=pix.tobytes("png"))
        page.insert_text((55, 178), "AXIS LABEL", fontsize=8)
        pdf_bytes = doc.tobytes()
        doc.close()

        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")},
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            with patch("nblane.core.research_papers.git_backup.record_change"):
                import_paper_pdf(profile, source_id, pdf_bytes, "geometry.pdf")
            units = build_paper_layout_units(profile, source_id, pages={1})

        self.assertTrue(units)
        by_kind: dict[str, list[dict[str, object]]] = {}
        for unit in units:
            by_kind.setdefault(str(unit.get("kind")), []).append(unit)

        self.assertIn("title", by_kind)
        self.assertIn("paragraph", by_kind)
        self.assertIn("caption", by_kind)
        self.assertIn("figure_label", by_kind)
        self.assertTrue(by_kind["title"][0]["translatable"])
        self.assertTrue(by_kind["paragraph"][0]["translatable"])
        self.assertTrue(by_kind["caption"][0]["translatable"])

        figure_label = by_kind["figure_label"][0]
        self.assertFalse(figure_label["translatable"])
        self.assertFalse(figure_label["display_source"])
        self.assertEqual(figure_label["translated_text"], "")
        self.assertGreater(float(figure_label["font_size"]), 0)
        self.assertEqual(figure_label["line_count"], 1)

        for unit in [by_kind["title"][0], by_kind["paragraph"][0], by_kind["caption"][0], figure_label]:
            rect = unit["rects"][0]
            self.assertEqual(rect["page_width"], 240.0)
            self.assertEqual(rect["page_height"], 320.0)
            for key in ("x", "y", "w", "h", "x_pct", "y_pct", "w_pct", "h_pct"):
                self.assertIn(key, rect)
            self.assertGreater(rect["w"], 0)
            self.assertGreater(rect["h"], 0)
            self.assertGreaterEqual(rect["x_pct"], 0)
            self.assertGreaterEqual(rect["y_pct"], 0)
            self.assertLessEqual(rect["x_pct"] + rect["w_pct"], 1)
            self.assertLessEqual(rect["y_pct"] + rect["h_pct"], 1)

    def test_build_paper_layout_units_merges_title_and_marks_front_matter(self) -> None:
        if not pymupdf_available():
            self.skipTest("PyMuPDF is not available")
        import fitz  # type: ignore[import-not-found]

        doc = fitz.open()
        page = doc.new_page(width=320, height=420)
        page.insert_text((36, 42), "RH20T-P: A Primitive-Level", fontsize=18)
        page.insert_text((46, 64), "Robotic Manipulation Benchmark", fontsize=18)
        page.insert_text((62, 104), "Alice Chen, Bob Li, Carol Wang", fontsize=10)
        page.insert_text((66, 120), "Robotics Lab, Example University", fontsize=10)
        page.insert_textbox(
            fitz.Rect(36, 170, 290, 220),
            "This benchmark evaluates robotic manipulation policies with primitive-level annotations.",
            fontsize=10,
        )
        pdf_bytes = doc.tobytes()
        doc.close()

        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")},
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            with patch("nblane.core.research_papers.git_backup.record_change"):
                import_paper_pdf(profile, source_id, pdf_bytes, "front-matter.pdf")
            units = build_paper_layout_units(profile, source_id, pages={1})

        titles = [unit for unit in units if unit.get("kind") == "title"]
        front_matter = [unit for unit in units if unit.get("kind") in {"authors", "affiliation"}]
        paragraphs = [unit for unit in units if unit.get("kind") == "paragraph"]

        self.assertEqual(len(titles), 1)
        self.assertIn("Primitive-Level", titles[0]["source_text"])
        self.assertIn("Robotic Manipulation Benchmark", titles[0]["source_text"])
        self.assertTrue(titles[0]["translatable"])
        self.assertEqual(titles[0]["line_count"], 2)
        self.assertEqual(len(front_matter), 1)
        self.assertIn("Alice Chen", front_matter[0]["source_text"])
        self.assertIn("Example University", front_matter[0]["source_text"])
        self.assertFalse(front_matter[0]["translatable"])
        self.assertTrue(front_matter[0]["display_source"])
        self.assertTrue(paragraphs)

    def test_build_paper_structure_units_merges_front_matter_and_caption_flow(self) -> None:
        if not pymupdf_available():
            self.skipTest("PyMuPDF is not available")
        import fitz  # type: ignore[import-not-found]

        doc = fitz.open()
        page = doc.new_page(width=340, height=460)
        page.insert_text((36, 42), "RH20T-P: A Primitive-Level", fontsize=18)
        page.insert_text((40, 64), "Robotic Manipulation Dataset", fontsize=18)
        page.insert_text((54, 100), "Alice Chen Bob Li Carol Wang", fontsize=10)
        page.insert_text((54, 116), "Robotics Laboratory, Example University", fontsize=10)
        page.insert_text((36, 160), "Abstract", fontsize=12)
        page.insert_textbox(
            fitz.Rect(36, 180, 300, 222),
            "This benchmark evaluates composable robotic manipulation agents.",
            fontsize=10,
        )
        page.insert_text((36, 260), "Figure 1: Overview of the collection setup", fontsize=10)
        page.insert_text((36, 276), "and primitive-level annotations.", fontsize=10)
        pdf_bytes = doc.tobytes()
        doc.close()

        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")},
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            with patch("nblane.core.research_papers.git_backup.record_change"):
                import_paper_pdf(profile, source_id, pdf_bytes, "structure.pdf")
            units = build_paper_structure_units(profile, source_id, force=True)
            cached = load_paper_structure_units(profile, source_id)

        self.assertEqual(len(cached), len(units))
        titles = [unit for unit in units if unit.kind == "title"]
        authors = [unit for unit in units if unit.kind == "authors"]
        affiliations = [unit for unit in units if unit.kind == "affiliation"]
        captions = [unit for unit in units if unit.kind == "caption"]
        figure_objects = [unit for unit in units if unit.kind == "figure"]
        translation_rows = reader_translation_structure_units(units)

        self.assertEqual(len(titles), 1)
        self.assertIn("Primitive-Level", titles[0].text)
        self.assertIn("Robotic Manipulation Dataset", titles[0].text)
        self.assertTrue(authors)
        self.assertTrue(affiliations)
        self.assertFalse(authors[0].translatable)
        self.assertFalse(affiliations[0].translatable)
        self.assertEqual({row["scope_type"] for row in translation_rows}, {"structure"})
        self.assertNotIn("authors", {row["kind"] for row in translation_rows})
        self.assertNotIn("affiliation", {row["kind"] for row in translation_rows})
        self.assertTrue(captions)
        self.assertIn("primitive-level annotations", captions[0].text)
        self.assertTrue(figure_objects)
        self.assertFalse(figure_objects[0].translatable)
        self.assertIn("caption", {row["kind"] for row in translation_rows})
        self.assertNotIn("figure", {row["kind"] for row in translation_rows})

    def test_build_paper_structure_units_repairs_split_span_spaces(self) -> None:
        if not pymupdf_available():
            self.skipTest("PyMuPDF is not available")
        import fitz  # type: ignore[import-not-found]

        doc = fitz.open()
        page = doc.new_page(width=260, height=220)
        page.insert_text((24, 60), "dataset", fontsize=10)
        page.insert_text((68, 60), "for", fontsize=10)
        page.insert_text((90, 60), "future", fontsize=10)
        page.insert_text((130, 60), "development", fontsize=10)
        pdf_bytes = doc.tobytes()
        doc.close()

        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")},
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            with patch("nblane.core.research_papers.git_backup.record_change"):
                import_paper_pdf(profile, source_id, pdf_bytes, "spaces.pdf")
            units = build_paper_structure_units(profile, source_id, force=True)

        text = " ".join(unit.text for unit in units)
        self.assertIn("dataset for future development", text)
        self.assertNotIn("datasetforfuturedevelopment", text)

    def test_build_paper_structure_units_orders_two_columns_without_cross_column_merge(self) -> None:
        if not pymupdf_available():
            self.skipTest("PyMuPDF is not available")
        import fitz  # type: ignore[import-not-found]

        doc = fitz.open()
        page = doc.new_page(width=420, height=520)
        page.insert_textbox(fitz.Rect(34, 80, 190, 125), "Left column first paragraph.", fontsize=10)
        page.insert_textbox(fitz.Rect(230, 80, 386, 125), "Right column first paragraph.", fontsize=10)
        page.insert_textbox(fitz.Rect(34, 150, 190, 195), "Left column second paragraph.", fontsize=10)
        page.insert_textbox(fitz.Rect(230, 150, 386, 195), "Right column second paragraph.", fontsize=10)
        pdf_bytes = doc.tobytes()
        doc.close()

        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")},
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            with patch("nblane.core.research_papers.git_backup.record_change"):
                import_paper_pdf(profile, source_id, pdf_bytes, "columns.pdf")
            units = build_paper_structure_units(profile, source_id, force=True)

        paragraphs = [unit.text for unit in units if unit.kind == "paragraph"]
        self.assertEqual(
            paragraphs[:4],
            [
                "Left column first paragraph.",
                "Left column second paragraph.",
                "Right column first paragraph.",
                "Right column second paragraph.",
            ],
        )

    def test_build_paper_structure_units_uses_grobid_section_path_without_overriding_boundaries(self) -> None:
        layout_hash = text_hash("A layout-grounded paragraph about robots.")
        layout_units = [
            {
                "unit_id": "layout:v2:2:00001:intro",
                "scope_type": "layout",
                "scope_ref": "layout:v2:2:00001:intro",
                "page": 2,
                "order": 1,
                "kind": "paragraph",
                "source_text": "A layout-grounded paragraph about robots.",
                "source_hash": layout_hash,
                "translatable": True,
                "rects": [{"x": 20, "y": 80, "w": 160, "h": 24, "page_width": 240, "page_height": 320}],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(
                    profile,
                    source_id,
                    [
                        PaperSegment(
                            segment_id="seg:intro",
                            source_id=source_id,
                            page=2,
                            order=1,
                            text="A layout-grounded paragraph about robots.",
                            text_hash=layout_hash,
                            section_path=["1 Introduction"],
                        )
                    ],
                )
            with (
                patch("nblane.core.research_papers.build_paper_layout_units", return_value=layout_units),
                patch("nblane.core.research_papers.git_backup.record_change"),
            ):
                units = build_paper_structure_units(profile, source_id, force=True)

        paragraphs = [unit for unit in units if unit.kind == "paragraph"]
        self.assertEqual(len(paragraphs), 1)
        self.assertEqual(paragraphs[0].section_path, ["1 Introduction"])
        self.assertEqual(paragraphs[0].text, "A layout-grounded paragraph about robots.")

    def test_build_paper_structure_units_keeps_pre_abstract_caption_outside_abstract_and_merges_cross_page_abstract(self) -> None:
        layout_units = [
            {
                "unit_id": "layout:v2:1:00001:caption",
                "scope_type": "layout",
                "scope_ref": "layout:v2:1:00001:caption",
                "page": 1,
                "order": 1,
                "kind": "caption",
                "source_text": "Figure 1: Overview of our RH20T-P dataset.",
                "source_hash": text_hash("Figure 1: Overview of our RH20T-P dataset."),
                "translatable": True,
                "rects": [{"x": 64, "y": 450, "w": 450, "h": 34, "x_pct": 0.10, "y_pct": 0.57, "w_pct": 0.72, "h_pct": 0.04, "page_width": 640, "page_height": 790}],
            },
            {
                "unit_id": "layout:v2:1:00002:abstract-heading",
                "scope_type": "layout",
                "scope_ref": "layout:v2:1:00002:abstract-heading",
                "page": 1,
                "order": 2,
                "kind": "paragraph",
                "source_text": "Abstract",
                "source_hash": text_hash("Abstract"),
                "translatable": True,
                "font_size": 13,
                "rects": [{"x": 280, "y": 515, "w": 80, "h": 20, "x_pct": 0.44, "y_pct": 0.65, "w_pct": 0.13, "h_pct": 0.03, "page_width": 640, "page_height": 790}],
            },
            {
                "unit_id": "layout:v2:1:00003:abstract-p1",
                "scope_type": "layout",
                "scope_ref": "layout:v2:1:00003:abstract-p1",
                "page": 1,
                "order": 3,
                "kind": "paragraph",
                "source_text": "Achieving generalizability in solving out-of-distribution tasks is one of the ultimate goals of learning robotic manipulation. Therefore, we propose RH20T-P, a primitive-level robotic manipulation dataset, which contains about 38k video clips covering diverse manipulation tasks.",
                "source_hash": text_hash("abstract p1"),
                "translatable": True,
                "rects": [{"x": 100, "y": 540, "w": 430, "h": 150, "x_pct": 0.16, "y_pct": 0.68, "w_pct": 0.67, "h_pct": 0.19, "page_width": 640, "page_height": 790}],
            },
            {
                "unit_id": "layout:v2:2:00001:abstract-p2",
                "scope_type": "layout",
                "scope_ref": "layout:v2:2:00001:abstract-p2",
                "page": 2,
                "order": 1,
                "kind": "paragraph",
                "source_text": "and implement an exemplar baseline called RA-P on our RH20T-P, whose positive performance validates that the proposed dataset can offer composable generalization.",
                "source_hash": text_hash("abstract p2"),
                "translatable": True,
                "rects": [{"x": 100, "y": 72, "w": 430, "h": 54, "x_pct": 0.16, "y_pct": 0.09, "w_pct": 0.67, "h_pct": 0.07, "page_width": 640, "page_height": 790}],
            },
            {
                "unit_id": "layout:v2:1:00004:footnote",
                "scope_type": "layout",
                "scope_ref": "layout:v2:1:00004:footnote",
                "page": 1,
                "order": 4,
                "kind": "paragraph",
                "source_text": "∗Equal contribution. †Corresponding author.",
                "source_hash": text_hash("∗Equal contribution. †Corresponding author."),
                "translatable": True,
                "rects": [{"x": 100, "y": 690, "w": 430, "h": 18, "x_pct": 0.16, "y_pct": 0.87, "w_pct": 0.67, "h_pct": 0.02, "page_width": 640, "page_height": 790}],
            },
            {
                "unit_id": "layout:v2:2:00002:intro",
                "scope_type": "layout",
                "scope_ref": "layout:v2:2:00002:intro",
                "page": 2,
                "order": 2,
                "kind": "paragraph",
                "source_text": "INTRODUCTION",
                "source_hash": text_hash("INTRODUCTION"),
                "translatable": True,
                "font_size": 13,
                "rects": [{"x": 260, "y": 145, "w": 120, "h": 22, "x_pct": 0.41, "y_pct": 0.18, "w_pct": 0.19, "h_pct": 0.03, "page_width": 640, "page_height": 790}],
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            with (
                patch("nblane.core.research_papers.build_paper_layout_units", return_value=layout_units),
                patch("nblane.core.research_papers.git_backup.record_change"),
            ):
                units = build_paper_structure_units(profile, source_id, force=True)

        captions = [unit for unit in units if unit.kind == "caption"]
        footnotes = [unit for unit in units if unit.kind == "footnote"]
        abstract_paragraphs = [unit for unit in units if unit.kind == "paragraph" and unit.section_path == ["Abstract"]]

        self.assertTrue(captions)
        self.assertEqual(captions[0].section_path, [])
        self.assertLess(captions[0].order, next(unit.order for unit in units if unit.kind == "heading" and unit.text == "Abstract"))
        self.assertEqual(len(footnotes), 1)
        self.assertEqual(footnotes[0].section_path, [])
        self.assertEqual(len(abstract_paragraphs), 1)
        self.assertEqual(abstract_paragraphs[0].page_start, 1)
        self.assertEqual(abstract_paragraphs[0].page_end, 2)
        self.assertIn("Achieving generalizability", abstract_paragraphs[0].text)
        self.assertIn("and implement an exemplar baseline", abstract_paragraphs[0].text)
        self.assertNotIn("Equal contribution", abstract_paragraphs[0].text)
        self.assertEqual({rect.get("page") for rect in abstract_paragraphs[0].rects}, {1, 2})

    def test_extract_paper_figures_returns_cropped_images_with_rects(self) -> None:
        if not pymupdf_available():
            self.skipTest("PyMuPDF is not available")
        import fitz  # type: ignore[import-not-found]

        doc = fitz.open()
        page = doc.new_page(width=240, height=320)
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 18, 12), 0)
        pix.clear_with(0xDDDDDD)
        page.insert_image(fitz.Rect(36, 70, 204, 170), stream=pix.tobytes("png"))
        page.insert_text((42, 190), "Figure 1. A compact architecture diagram.", fontsize=10)
        pdf_bytes = doc.tobytes()
        doc.close()

        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")},
            clear=False,
        ):
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            with patch("nblane.core.research_papers.git_backup.record_change"):
                import_paper_pdf(profile, source_id, pdf_bytes, "figures.pdf")
            figures = extract_paper_figures(profile, source_id, pages={1}, max_items=4, max_width=240)

        self.assertTrue(figures)
        figure = figures[0]
        self.assertEqual(figure["page"], 1)
        self.assertTrue(str(figure["data_url"]).startswith("data:image/png;base64,"))
        self.assertIn("Figure 1", figure["caption"])
        self.assertEqual(figure["anchor_id"], figure["id"])
        self.assertEqual(figure["rects"], [figure["rect"]])
        rect = figure["rect"]
        self.assertGreater(rect["w"], 0)
        self.assertGreater(rect["h"], 0)
        self.assertLessEqual(rect["x_pct"] + rect["w_pct"], 1)
        self.assertLessEqual(rect["y_pct"] + rect["h_pct"], 1)

    def test_build_reader_payload_filters_old_layout_cache_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            layout_hash = text_hash("Current positioned text.")
            layout_scope = "layout:v2:1:00001:current"
            old_scope = "layout:1:00001:oldfailed"
            layout_units = [
                {
                    "unit_id": layout_scope,
                    "anchor_id": layout_scope,
                    "scope_type": "layout",
                    "scope_ref": layout_scope,
                    "page": 1,
                    "order": 1,
                    "kind": "paragraph",
                    "locator": "p. 1",
                    "source_text": "Current positioned text.",
                    "source_hash": layout_hash,
                    "translatable": True,
                    "rects": [{"x": 10, "y": 20, "w": 80, "h": 24, "page_width": 200, "page_height": 200}],
                }
            ]
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_pages(
                    profile,
                    source_id,
                    [PaperPage(source_id=source_id, page=1, text="Whole page text.", text_hash=text_hash("Whole page text."))],
                )
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "scope_type": "layout",
                            "scope_ref": old_scope,
                            "source_hash": text_hash("Old positioned text."),
                            "source_text": "Old positioned text.",
                            "target_lang": "zh",
                            "page": 1,
                            "translated_text": "",
                            "status": "failed",
                        }
                    ],
                )

            with patch("nblane.core.research_papers.build_paper_layout_units", return_value=layout_units):
                payload = build_reader_payload(
                    profile,
                    source_id,
                    page=1,
                    requested_pages={1},
                    target_lang="zh",
                    include_page_previews=False,
                )

        self.assertEqual([row["scope_type"] for row in payload["translation_units"]], ["structure"])
        self.assertNotIn(old_scope, [row["scope_ref"] for row in payload["translations"]])
        self.assertEqual(payload["translation_units"][0]["status"], "missing")
        self.assertEqual(payload["translation_summary"], {"translated": 0, "missing": 1, "stale": 0, "failed": 0})

    def test_reader_outline_rejects_fragmentary_headings(self) -> None:
        source_id = "source:paper:grounded"
        outline = _reader_outline_from_segments(
            [
                PaperSegment(
                    segment_id="seg:bad-number-path",
                    source_id=source_id,
                    page=1,
                    order=1,
                    text="3.",
                    kind="heading",
                    section_path=["3."],
                ),
                PaperSegment(
                    segment_id="seg:bad-short-path",
                    source_id=source_id,
                    page=2,
                    order=2,
                    text="Metric.",
                    kind="paragraph",
                    section_path=["Metric."],
                ),
                PaperSegment(
                    segment_id="seg:good-path",
                    source_id=source_id,
                    page=3,
                    order=3,
                    text="The experiment setup uses three suites.",
                    kind="paragraph",
                    section_path=["Experimental Setup"],
                ),
            ]
        )
        fallback_outline = _reader_outline_from_segments(
            [
                PaperSegment(segment_id="seg:number", source_id=source_id, page=1, order=1, text="3.", kind="paragraph"),
                PaperSegment(segment_id="seg:metric", source_id=source_id, page=1, order=2, text="Metric.", kind="paragraph"),
                PaperSegment(segment_id="seg:unpaged", source_id=source_id, page=0, order=3, text="Conclusion", kind="heading"),
                PaperSegment(segment_id="seg:results", source_id=source_id, page=2, order=4, text="3 Experimental Results", kind="paragraph"),
                PaperSegment(segment_id="seg:conclusion", source_id=source_id, page=3, order=5, text="CONCLUSION", kind="paragraph"),
            ]
        )

        self.assertEqual([row["title"] for row in outline], ["Experimental Setup"])
        self.assertEqual(outline[0]["page"], 3)
        self.assertEqual([row["title"] for row in fallback_outline], ["3 Experimental Results", "CONCLUSION"])
        self.assertNotIn(0, [row["page"] for row in fallback_outline])

    def test_reader_outline_extracts_headings_from_page_text_fallback(self) -> None:
        source_id = "source:paper:page-text"
        outline = _reader_outline_from_segments(
            [
                PaperSegment(
                    segment_id="seg:page-1",
                    source_id=source_id,
                    page=1,
                    order=1,
                    text="\n".join(
                        [
                            "A Very Useful Paper",
                            "Alice Example, Bob Example",
                            "1 Example University",
                            "Abstract",
                            "This paper studies robust readers.",
                        ]
                    ),
                    kind="paragraph",
                ),
                PaperSegment(
                    segment_id="seg:page-2",
                    source_id=source_id,
                    page=2,
                    order=2,
                    text="\n".join(
                        [
                            "1",
                            "INTRODUCTION",
                            "The body starts here.",
                            "2",
                            "RELATED WORK",
                            "Table 1: Comparison with Existing Systems.",
                            "Dataset",
                            "Amount",
                            "3.1",
                            "Experimental Setup",
                            "We evaluate the system.",
                        ]
                    ),
                    kind="paragraph",
                ),
            ]
        )

        self.assertEqual(
            [row["title"] for row in outline],
            ["Abstract", "1 Introduction", "2 Related Work", "3.1 Experimental Setup"],
        )
        self.assertNotIn("1 Example University", [row["title"] for row in outline])
        self.assertNotIn("Dataset", [row["title"] for row in outline])

    def test_get_stable_pdf_url_uses_fingerprint_cache_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            with patch.dict(os.environ, {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")}):
                import_paper_pdf(profile, source_id, PDF_BYTES, "paper.pdf")

                with patch("nblane.core.research_papers._stable_pdf_url_cached") as cached:
                    cached.return_value = "/media/stable.pdf"
                    first = get_stable_pdf_url(profile, source_id)
                    second = get_stable_pdf_url(profile, source_id)

        self.assertEqual(first, "/media/stable.pdf")
        self.assertEqual(second, "/media/stable.pdf")
        self.assertEqual(cached.call_count, 2)
        self.assertEqual(cached.call_args.args[1], source_id)

    def test_reader_payload_can_skip_page_previews_and_override_pdf_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_pages(
                    profile,
                    source_id,
                    [PaperPage(source_id=source_id, page=1, text="Page 1", text_hash=text_hash("Page 1"))],
                )
                save_paper_segments(
                    profile,
                    source_id,
                    [
                        PaperSegment(
                            segment_id="seg:1",
                            source_id=source_id,
                            page=1,
                            order=1,
                            text="Segment 1",
                            text_hash=text_hash("Segment 1"),
                        )
                    ],
                )

            with patch("nblane.core.research_papers.render_paper_page_preview") as preview:
                payload = build_reader_payload(
                    profile,
                    source_id,
                    page=1,
                    requested_pages={1},
                    target_lang="zh",
                    include_page_previews=False,
                    pdf_url_override="/reader/api/source%3Apaper%3Agrounded/pdf",
                )

        preview.assert_not_called()
        self.assertEqual(payload["page_previews"], [])
        self.assertEqual(payload["pdf_url"], "/reader/api/source%3Apaper%3Agrounded/pdf")

    def test_ensure_paper_reading_artifacts_prepares_missing_pages_and_segments_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            inbox = load_research_sources(profile)
            update_research_source(
                inbox,
                source_id,
                metadata={"pdf_asset_ref": "papers/demo.pdf", "pdf_sha256": "abc123"},
            )
            with patch("nblane.core.research_sources.git_backup.record_change"):
                save_research_sources(profile, inbox)

            def fake_pages(profile_arg, source_id_arg, *, backend="auto"):
                pages = [PaperPage(source_id=source_id_arg, page=1, text="Page text.")]
                save_paper_pages(profile_arg, source_id_arg, pages)
                return pages

            def fake_segments(profile_arg, source_id_arg, *, backend="auto"):
                segments = [
                    PaperSegment(
                        segment_id="seg:source-paper-grounded:00001",
                        source_id=source_id_arg,
                        page=1,
                        order=1,
                        text="Page text.",
                        text_hash=text_hash("Page text."),
                    )
                ]
                save_paper_segments(profile_arg, source_id_arg, segments)
                return segments

            with (
                patch("nblane.core.research_papers.extract_paper_pages", side_effect=fake_pages) as pages_mock,
                patch("nblane.core.research_papers.extract_paper_segments", side_effect=fake_segments) as segments_mock,
                patch("nblane.core.research_papers.git_backup.record_change"),
                patch("nblane.core.research_sources.git_backup.record_change"),
            ):
                progress: list[dict[str, object]] = []
                first = ensure_paper_reading_artifacts(
                    profile,
                    source_id,
                    prefer_grobid=False,
                    progress_callback=progress.append,
                )
                second = ensure_paper_reading_artifacts(profile, source_id, prefer_grobid=False)
            source = load_research_sources(profile).by_id()[source_id]

        self.assertTrue(first["ready"])
        self.assertEqual(first["pages"], 1)
        self.assertEqual(first["segments"], 1)
        self.assertEqual(
            [row["phase"] for row in progress],
            ["extracting_pages", "saving_segments", "done"],
        )
        self.assertEqual(progress[-1]["label"], "Structured text ready")
        self.assertEqual(second["pages"], 1)
        self.assertEqual(pages_mock.call_count, 1)
        self.assertEqual(segments_mock.call_count, 1)
        self.assertEqual(source.metadata["reading_artifacts_pdf_sha256"], "abc123")
        self.assertEqual(source.metadata["reading_artifacts_page_count"], 1)
        self.assertIn("translation_migration", first)

    def test_ensure_paper_reading_artifacts_reports_grobid_coordinate_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            inbox = load_research_sources(profile)
            update_research_source(
                inbox,
                source_id,
                metadata={
                    "pdf_asset_ref": "papers/demo.pdf",
                    "pdf_sha256": "abc123",
                    "reading_artifacts_pdf_sha256": "abc123",
                    "structure_backend": "grobid",
                },
            )
            with (
                patch("nblane.core.research_sources.git_backup.record_change"),
                patch("nblane.core.research_papers.git_backup.record_change"),
            ):
                save_research_sources(profile, inbox)
                save_paper_pages(profile, source_id, [PaperPage(source_id=source_id, page=1, text="Page text.")])
                save_paper_segments(
                    profile,
                    source_id,
                    [
                        PaperSegment(
                            segment_id="seg:source-paper-grounded:00001",
                            source_id=source_id,
                            page=1,
                            order=1,
                            text="Structured text without coordinates.",
                        )
                    ],
                )

                result = ensure_paper_reading_artifacts(profile, source_id, prefer_grobid=True)

        self.assertEqual(result["coordinate_extraction"]["segments_with_rects"], 0)
        self.assertEqual(result["coordinate_extraction"]["segments_without_rects"], 1)
        self.assertIn("without PDF coordinates", " ".join(result["warnings"]))

    def test_migrate_legacy_translations_to_segments_copies_safe_layout_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            segment = PaperSegment(
                segment_id="seg:safe",
                source_id=source_id,
                page=1,
                order=1,
                text="Legacy layout source text.",
                text_hash=text_hash("Legacy layout source text."),
                rects=[{"page": 1, "x": 10, "y": 20, "w": 80, "h": 12, "page_width": 200, "page_height": 200}],
            )
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(profile, source_id, [segment])
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "id": "tr:legacy-layout",
                            "scope_type": "layout",
                            "scope_ref": "layout:v2:1:00001:legacy",
                            "page": 1,
                            "source_hash": text_hash("Legacy layout source text."),
                            "source_text": "Legacy layout source text.",
                            "target_lang": "zh",
                            "translated_text": "安全迁移译文。",
                        }
                    ],
                )

                summary = migrate_legacy_translations_to_segments(profile, source_id, target_lang="zh")
            translations = load_paper_translations(profile, source_id)
            migrated = [row for row in translations if row.scope_type == "segment"]

        self.assertEqual(summary["migrated"], 1)
        self.assertEqual(summary["migrated_ids"], ["tr:legacy-layout"])
        self.assertEqual(migrated[0].segment_id, "seg:safe")
        self.assertEqual(migrated[0].source_hash, segment.text_hash)
        self.assertEqual(migrated[0].translated_text, "安全迁移译文。")
        self.assertEqual(migrated[0].generated_by, "migration:layout_to_segment")
        self.assertEqual(migrated[0].rects, segment.rects)

    def test_migrate_legacy_translations_to_segments_preserves_unsafe_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            segment = PaperSegment(
                segment_id="seg:current",
                source_id=source_id,
                page=1,
                order=1,
                text="Current segment body.",
                text_hash=text_hash("Current segment body."),
            )
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(profile, source_id, [segment])
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "scope_type": "layout",
                            "scope_ref": "layout:v2:1:00001:legacy",
                            "page": 1,
                            "source_hash": text_hash("Unrelated legacy body."),
                            "source_text": "Unrelated legacy body.",
                            "target_lang": "zh",
                            "translated_text": "不安全旧译文。",
                        }
                    ],
                )

                summary = migrate_legacy_translations_to_segments(profile, source_id, target_lang="zh")
            translations = load_paper_translations(profile, source_id)

        self.assertEqual(summary["migrated"], 0)
        self.assertEqual(len([row for row in translations if row.scope_type == "layout"]), 1)
        self.assertFalse([row for row in translations if row.scope_type == "segment"])
        self.assertIn("no safe segment match", " ".join(summary["warnings"]))

    def test_migrate_legacy_page_translation_to_single_segment_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            segment = PaperSegment(
                segment_id="seg:single-page",
                source_id=source_id,
                page=2,
                order=1,
                text="Only paragraph on this page.",
                text_hash=text_hash("Only paragraph on this page."),
            )
            page_hash = text_hash("Legacy full page text.")
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(profile, source_id, [segment])
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "id": "tr:legacy-page",
                            "scope_type": "page",
                            "scope_ref": f"page:2:{page_hash}",
                            "page": 2,
                            "source_hash": page_hash,
                            "source_text": "Legacy full page text.",
                            "target_lang": "zh",
                            "translated_text": "单段页迁移译文。",
                        }
                    ],
                )

                summary = migrate_legacy_translations_to_segments(profile, source_id, target_lang="zh")
            migrated = [row for row in load_paper_translations(profile, source_id) if row.scope_type == "segment"]

        self.assertEqual(summary["migrated"], 1)
        self.assertEqual(migrated[0].segment_id, segment.segment_id)
        self.assertEqual(migrated[0].source_hash, segment.text_hash)
        self.assertEqual(migrated[0].generated_by, "migration:page_to_segment")

    def test_migrate_legacy_translation_does_not_overwrite_current_segment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            segment = PaperSegment(
                segment_id="seg:current",
                source_id=source_id,
                page=1,
                order=1,
                text="Current segment body.",
                text_hash=text_hash("Current segment body."),
            )
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(profile, source_id, [segment])
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "id": "tr:current",
                            "scope_type": "segment",
                            "scope_ref": segment.segment_id,
                            "segment_id": segment.segment_id,
                            "page": 1,
                            "source_hash": segment.text_hash,
                            "source_text": segment.text,
                            "target_lang": "zh",
                            "translated_text": "已有当前译文。",
                        },
                        {
                            "id": "tr:legacy-layout",
                            "scope_type": "layout",
                            "scope_ref": "layout:v2:1:00001:legacy",
                            "page": 1,
                            "source_hash": segment.text_hash,
                            "source_text": segment.text,
                            "target_lang": "zh",
                            "translated_text": "旧布局译文。",
                        },
                    ],
                )

                summary = migrate_legacy_translations_to_segments(profile, source_id, target_lang="zh")
            segment_rows = [row for row in load_paper_translations(profile, source_id) if row.scope_type == "segment"]

        self.assertEqual(summary["migrated"], 0)
        self.assertEqual(len(segment_rows), 1)
        self.assertEqual(segment_rows[0].translated_text, "已有当前译文。")

    def test_ensure_paper_reading_artifacts_missing_pdf_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            before = sorted(path.relative_to(profile) for path in profile.rglob("*"))
            result = ensure_paper_reading_artifacts(profile, "source:paper:grounded")
            after = sorted(path.relative_to(profile) for path in profile.rglob("*"))

        self.assertFalse(result["ready"])
        self.assertEqual(result["status"], "missing_pdf")
        self.assertEqual(after, before)

    def test_translate_full_paper_translates_only_missing_and_stale_segments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            segments = [
                PaperSegment(
                    segment_id="seg:source-paper-grounded:00001",
                    source_id=source_id,
                    page=1,
                    order=1,
                    text="Already translated.",
                    text_hash=text_hash("Already translated."),
                ),
                PaperSegment(
                    segment_id="seg:source-paper-grounded:00002",
                    source_id=source_id,
                    page=1,
                    order=2,
                    text="Changed segment.",
                    text_hash=text_hash("Changed segment."),
                ),
                PaperSegment(
                    segment_id="seg:source-paper-grounded:00003",
                    source_id=source_id,
                    page=2,
                    order=3,
                    text="Missing segment.",
                    text_hash=text_hash("Missing segment."),
                ),
            ]
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(profile, source_id, segments)
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "segment_id": segments[0].segment_id,
                            "source_hash": segments[0].text_hash,
                            "source_text": segments[0].text,
                            "target_lang": "zh",
                            "translated_text": "已经翻译。",
                        },
                        {
                            "segment_id": segments[1].segment_id,
                            "source_hash": text_hash("Old segment."),
                            "source_text": "Old segment.",
                            "target_lang": "zh",
                            "translated_text": "旧译文。",
                        },
                    ],
                )

            def fake_translate(profile_arg, source_id_arg, batch, *, target_lang="zh", require_review=True, **kwargs):
                return SimpleNamespace(
                    warnings=[],
                    error="",
                    structured={
                        "translations": [
                            {
                                "segment_id": row["segment_id"],
                                "source_hash": row["text_hash"],
                                "source_text": row["text"],
                                "target_lang": target_lang,
                                "text": f"zh:{row['segment_id']}",
                            }
                            for row in batch
                        ]
                    },
                )

            with (
                patch("nblane.core.ai.gateway.translate_paper_segments", side_effect=fake_translate) as translate_mock,
                patch("nblane.core.research_papers.git_backup.record_change"),
            ):
                summary = translate_full_paper(
                    profile,
                    source_id,
                    target_lang="zh",
                    mode="missing_or_stale",
                    batch_size=20,
                    ai_profile="",
                    require_review=False,
                )
            call_batch = translate_mock.call_args.args[2]
            translations = load_paper_translations(profile, source_id)
            by_segment = {row.segment_id: row for row in translations}

        self.assertEqual([row["segment_id"] for row in call_batch], [segments[1].segment_id, segments[2].segment_id])
        self.assertEqual(summary["scope"], "segment")
        self.assertEqual(summary["segments_selected"], 2)
        self.assertEqual(summary["translated"], 3)
        self.assertEqual(by_segment[segments[0].segment_id].translated_text, "已经翻译。")
        self.assertEqual(by_segment[segments[1].segment_id].source_hash, segments[1].text_hash)
        self.assertEqual(by_segment[segments[2].segment_id].translated_text, f"zh:{segments[2].segment_id}")

    def test_translate_full_paper_rejects_hash_mismatch_without_overwriting_current_translation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            segment = PaperSegment(
                segment_id="seg:source-paper-grounded:00001",
                source_id=source_id,
                page=1,
                order=1,
                text="Stable segment.",
                text_hash=text_hash("Stable segment."),
            )
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_segments(profile, source_id, [segment])
                upsert_paper_translations(
                    profile,
                    source_id,
                    [
                        {
                            "segment_id": segment.segment_id,
                            "source_hash": segment.text_hash,
                            "source_text": segment.text,
                            "target_lang": "zh",
                            "translated_text": "稳定译文。",
                        }
                    ],
                )
            result = SimpleNamespace(
                warnings=[],
                error="",
                structured={
                    "translations": [
                        {
                            "segment_id": segment.segment_id,
                            "source_hash": text_hash("wrong"),
                            "source_text": segment.text,
                            "target_lang": "zh",
                            "translated_text": "bad overwrite",
                        }
                    ]
                },
            )
            with (
                patch("nblane.core.ai.gateway.translate_paper_segments", return_value=result),
                patch("nblane.core.research_papers.git_backup.record_change"),
            ):
                summary = translate_full_paper(
                    profile,
                    source_id,
                    target_lang="zh",
                    mode="all",
                    ai_profile="",
                    require_review=False,
                )
            translations = load_paper_translations(profile, source_id)

        self.assertIn("source_hash mismatch", " ".join(summary["warnings"]))
        self.assertEqual(len(translations), 1)
        self.assertEqual(translations[0].translated_text, "稳定译文。")

    def test_translate_full_paper_supports_layout_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            layout_hash = text_hash("A positioned paragraph.")
            layout_scope = "layout:v2:1:00001:abc123"
            layout_units = [
                {
                    "unit_id": layout_scope,
                    "anchor_id": layout_scope,
                    "scope_type": "layout",
                    "scope_ref": layout_scope,
                    "page": 1,
                    "order": 1,
                    "kind": "paragraph",
                    "locator": "p. 1",
                    "source_text": "A positioned paragraph.",
                    "source_hash": layout_hash,
                    "translatable": True,
                    "rects": [{"x": 10, "y": 20, "w": 90, "h": 30, "page_width": 200, "page_height": 200}],
                }
            ]

            def fake_translate(profile_arg, source_id_arg, batch, *, target_lang="zh", require_review=True, **kwargs):
                return SimpleNamespace(
                    warnings=[],
                    error="",
                    structured={
                        "translations": [
                            {
                                "segment_id": row["segment_id"],
                                "source_hash": row["source_hash"],
                                "translated_text": "定位段落译文。",
                            }
                            for row in batch
                        ]
                    },
                )

            with (
                patch("nblane.core.research_papers.build_paper_layout_units", return_value=layout_units),
                patch("nblane.core.ai.gateway.translate_paper_segments", side_effect=fake_translate),
                patch("nblane.core.research_papers.git_backup.record_change"),
            ):
                summary = translate_full_paper(
                    profile,
                    source_id,
                    target_lang="zh",
                    mode="all",
                    scope_strategy="layout",
                    ai_profile="",
                    require_review=False,
                )
            translations = load_paper_translations(profile, source_id)

        self.assertEqual(summary["scope"], "layout")
        self.assertEqual(summary["segments_selected"], 1)
        self.assertEqual(summary["updated"], 1)
        self.assertEqual(summary["translated"], 1)
        self.assertEqual(translations[0].scope_type, "layout")
        self.assertEqual(translations[0].scope_ref, layout_scope)
        self.assertEqual(translations[0].segment_id, "")
        self.assertEqual(translations[0].page, 1)
        self.assertEqual(translations[0].rects[0]["w"], 90)
        self.assertEqual(translations[0].translated_text, "定位段落译文。")

    def test_translate_full_paper_skips_blank_layout_fallback_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            layout_hash = text_hash("A positioned paragraph.")
            layout_scope = "layout:v2:1:00001:abc123"
            layout_units = [
                {
                    "unit_id": layout_scope,
                    "anchor_id": layout_scope,
                    "scope_type": "layout",
                    "scope_ref": layout_scope,
                    "page": 1,
                    "order": 1,
                    "kind": "paragraph",
                    "locator": "p. 1",
                    "source_text": "A positioned paragraph.",
                    "source_hash": layout_hash,
                    "translatable": True,
                    "rects": [{"x": 10, "y": 20, "w": 90, "h": 30, "page_width": 200, "page_height": 200}],
                }
            ]

            def fake_translate(profile_arg, source_id_arg, batch, *, target_lang="zh", require_review=True, **kwargs):
                return SimpleNamespace(
                    backend="rule_fallback",
                    warnings=["Deterministic fallback used."],
                    error="",
                    structured={
                        "translations": [
                            {
                                "segment_id": row["segment_id"],
                                "source_hash": row["source_hash"],
                                "translated_text": "",
                                "generated_by": "rule_fallback",
                            }
                            for row in batch
                        ]
                    },
                )

            with (
                patch("nblane.core.research_papers.build_paper_layout_units", return_value=layout_units),
                patch("nblane.core.ai.gateway.translate_paper_segments", side_effect=fake_translate),
                patch("nblane.core.research_papers.git_backup.record_change"),
            ):
                summary = translate_full_paper(
                    profile,
                    source_id,
                    target_lang="zh",
                    mode="all",
                    scope_strategy="layout",
                    ai_profile="",
                    require_review=False,
                )
            translations = load_paper_translations(profile, source_id)

        self.assertEqual(summary["scope"], "layout")
        self.assertEqual(summary["segments_selected"], 1)
        self.assertEqual(summary["updated"], 0)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["missing"], 1)
        self.assertEqual(translations, [])
        self.assertIn(NO_LLM_TRANSLATION_WARNING, summary["warnings"])

    def test_translate_full_paper_uses_page_fallback_for_unpaged_segments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            source_id = "source:paper:grounded"
            page = PaperPage(
                source_id=source_id,
                page=1,
                text="Whole PDF page text.",
                text_hash=text_hash("Whole PDF page text."),
            )
            segment = PaperSegment(
                segment_id="seg:unpaged",
                source_id=source_id,
                page=0,
                order=1,
                text="Structured text without page.",
                text_hash=text_hash("Structured text without page."),
            )
            with patch("nblane.core.research_papers.git_backup.record_change"):
                save_paper_pages(profile, source_id, [page])
                save_paper_segments(profile, source_id, [segment])

            def fake_translate(profile_arg, source_id_arg, batch, *, target_lang="zh", require_review=True, **kwargs):
                return SimpleNamespace(
                    warnings=[],
                    error="",
                    structured={
                        "translations": [
                            {
                                "segment_id": row["segment_id"],
                                "source_hash": row["text_hash"],
                                "text": f"zh page {row['page']}",
                            }
                            for row in batch
                        ]
                    },
                )

            with (
                patch("nblane.core.ai.gateway.translate_paper_segments", side_effect=fake_translate),
                patch("nblane.core.research_papers.git_backup.record_change"),
            ):
                summary = translate_full_paper(
                    profile,
                    source_id,
                    target_lang="zh",
                    mode="all",
                    scope_strategy="auto",
                    ai_profile="",
                    require_review=False,
                )
            translations = load_paper_translations(profile, source_id)

        self.assertEqual(summary["scope"], "page")
        self.assertEqual(summary["segments_selected"], 1)
        self.assertEqual(summary["updated"], 1)
        self.assertEqual(translations[0].scope_type, "page")
        self.assertEqual(translations[0].segment_id, "")
        self.assertEqual(translations[0].page, 1)
        self.assertEqual(translations[0].translated_text, "zh page 1")

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

    def test_search_papers_with_codex_uses_structured_candidates_without_importing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            codex_result = SimpleNamespace(
                structured={
                    "results": [
                        {"title": "Title Only Candidate"},
                        {
                            "title": "Grounded Candidate",
                            "url": "https://example.com/grounded",
                            "doi": "10.1000/grounded",
                            "provider_refs": ["semantic_scholar:grounded"],
                            "reason": "Matches the query.",
                        },
                    ],
                    "warnings": [],
                },
                warnings=[],
                ok=True,
                error="",
            )
            with patch(
                "nblane.core.ai.gateway.run_ai_action",
                return_value=codex_result,
            ) as run:
                rows = search_papers_with_codex(
                    profile,
                    "VLA memory",
                    filters={"providers": ["semantic_scholar"], "limit": 5},
                    context_refs={
                        "context_refs": ["goal:vla"],
                        "project_refs": ["project:piper"],
                        "goal_refs": ["goal:vla"],
                    },
                )
            sources = load_research_sources(profile).sources

        self.assertEqual([row.title for row in rows], ["Grounded Candidate"])
        self.assertEqual(rows[0].doi, "10.1000/grounded")
        self.assertEqual(len(sources), 1)
        payload = run.call_args.args[1]
        self.assertEqual(payload["query"], "VLA memory")
        self.assertEqual(payload["project_refs"], ["project:piper"])
        self.assertEqual(payload["goal_refs"], ["goal:vla"])
        self.assertIn("already_imported", payload)
        self.assertIn("library_tree_hint", payload)

    def test_search_papers_with_codex_falls_back_to_provider_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            codex_result = SimpleNamespace(
                structured={"results": [], "warnings": ["No candidates"]},
                warnings=["No candidates"],
                ok=True,
                error="",
            )
            provider_result = [
                PaperSearchResult(
                    title="Provider Candidate",
                    canonical_url="https://example.com/provider",
                    provider_refs=["arxiv"],
                )
            ]
            with (
                patch(
                    "nblane.core.ai.gateway.run_ai_action",
                    return_value=codex_result,
                ),
                patch(
                    "nblane.core.research_papers.search_papers",
                    return_value=provider_result,
                ) as provider_search,
            ):
                rows = search_papers_with_codex(
                    profile,
                    "VLA memory",
                    filters={"providers": ["arxiv"], "limit": 3},
                )

        self.assertEqual(rows, provider_result)
        provider_search.assert_called_once()
        self.assertEqual(provider_search.call_args.args[1], ("arxiv",))
        self.assertEqual(provider_search.call_args.args[2], 3)

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
          <facsimile>
            <surface n="3" ulx="0" uly="0" lrx="600" lry="800" />
          </facsimile>
          <text>
            <body>
              <div n="3"><head>Method</head><p coords="3,60,120,300,40">Memory encoder stores observations.</p></div>
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

        self.assertEqual(len(segments), 2)
        self.assertEqual([segment.kind for segment in segments], ["heading", "paragraph"])
        self.assertEqual(segments[0].page, 3)
        self.assertEqual(segments[0].section_path, ["Method"])
        self.assertEqual(segments[1].page, 3)
        self.assertEqual(segments[1].rects[0]["page"], 3)
        self.assertAlmostEqual(segments[1].rects[0]["x_pct"], 0.1)
        self.assertAlmostEqual(segments[1].rects[0]["w_pct"], 0.5)
        self.assertEqual(segments[1].section_path, ["Method"])
        self.assertIn("§ Method", segments[1].locator)
        self.assertEqual(refs[0]["title"], "Useful Paper")
        self.assertEqual(refs[0]["year"], "1843")

    def test_grobid_tei_to_segments_includes_head_caption_and_formula_coordinates(self) -> None:
        tei = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
          <facsimile>
            <surface n="2" ulx="0" uly="0" lrx="500" lry="700" />
          </facsimile>
          <text>
            <body>
              <div n="2">
                <head coords="2,40,50,180,24">Results</head>
                <p coords="2,40,90,300,40">Accuracy improves with retrieval.</p>
                <figure>
                  <figDesc coords="2,42,180,260,32">Figure 1 shows the retrieval curve.</figDesc>
                </figure>
                <formula coords="2,50,250,200,28">R = softmax(qK^T)</formula>
              </div>
            </body>
          </text>
        </TEI>"""

        segments = grobid_tei_to_segments("source:paper:grounded", tei)

        self.assertEqual([segment.kind for segment in segments], ["heading", "paragraph", "caption", "formula"])
        self.assertEqual([segment.text for segment in segments], [
            "Results",
            "Accuracy improves with retrieval.",
            "Figure 1 shows the retrieval curve.",
            "R = softmax(qK^T)",
        ])
        self.assertTrue(all(segment.page == 2 for segment in segments))
        self.assertTrue(all(segment.rects and segment.rects[0]["page"] == 2 for segment in segments))
        self.assertEqual(segments[0].section_path, ["Results"])
        self.assertAlmostEqual(segments[2].rects[0]["x_pct"], 42 / 500)

    def test_grobid_tei_to_segments_keeps_headings_without_coordinates(self) -> None:
        tei = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
          <facsimile>
            <surface n="3" ulx="0" uly="0" lrx="500" lry="700" />
          </facsimile>
          <text>
            <body>
              <div>
                <head>Method</head>
                <p coords="3,50,80,250,40">We train a policy.</p>
              </div>
            </body>
          </text>
        </TEI>"""

        segments = grobid_tei_to_segments("source:paper:grounded", tei)

        self.assertEqual([segment.kind for segment in segments], ["heading", "paragraph"])
        self.assertEqual(segments[0].text, "Method")
        self.assertEqual(segments[0].page, 3)
        self.assertEqual(segments[0].section_path, ["Method"])
        self.assertEqual(segments[0].rects, [])
        self.assertEqual(segments[1].rects[0]["page"], 3)

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
        self.assertEqual(
            source.metadata["structure_backend"],
            "pymupdf_fallback" if pymupdf_available() else "fallback",
        )
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

        self.assertEqual(len(segments), 2)
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
