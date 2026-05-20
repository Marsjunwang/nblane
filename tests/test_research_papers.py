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
    PaperPage,
    PaperSegment,
    PaperSearchResult,
    build_reader_payload,
    create_reading_note_markdown,
    ensure_paper_reading_artifacts,
    create_paper_annotation,
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
    load_paper_translations,
    move_papers_to_node,
    paper_overview,
    paper_pdf_asset_path,
    paper_rows,
    pymupdf_available,
    paper_citation_diagnostics,
    paper_source_diagnostics,
    research_asset_root,
    render_paper_page_preview,
    save_paper_pages,
    save_paper_segments,
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
        self.assertIn(
            "第一页译文。",
            [row["translated_text"] for row in payload["translations"]],
        )
        self.assertIn("translation_units", payload)
        self.assertIn("translation_summary", payload)
        self.assertIn("translation_revision", payload)
        self.assertEqual(payload["compare_split_ratio"], 50)
        self.assertEqual(payload["panel_width"], 340)
        units_by_scope = {row["scope_ref"]: row for row in payload["translation_units"]}
        self.assertEqual(units_by_scope[f"page:1:{pages[0].text_hash}"]["translated_text"], "第一页译文。")
        self.assertEqual(units_by_scope["seg:unpaged:00001"]["translated_text"], "无页码结构化段落译文。")
        self.assertEqual(payload["translation_summary"]["translated"], 2)
        self.assertGreaterEqual(payload["translation_summary"]["missing"], 1)

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
                first = ensure_paper_reading_artifacts(profile, source_id, prefer_grobid=False)
                second = ensure_paper_reading_artifacts(profile, source_id, prefer_grobid=False)
            source = load_research_sources(profile).by_id()[source_id]

        self.assertTrue(first["ready"])
        self.assertEqual(first["pages"], 1)
        self.assertEqual(first["segments"], 1)
        self.assertEqual(second["pages"], 1)
        self.assertEqual(pages_mock.call_count, 1)
        self.assertEqual(segments_mock.call_count, 1)
        self.assertEqual(source.metadata["reading_artifacts_pdf_sha256"], "abc123")
        self.assertEqual(source.metadata["reading_artifacts_page_count"], 1)

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
