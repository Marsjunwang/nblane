"""Paper Library polish: identifier parsing, library export, tree locking,
paper_rows caching, zh/en labels, and the sidecar export / embed surface."""

from __future__ import annotations

import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from nblane.core.file_state import FileConflictError
from nblane.core.paper_library_workspace import (
    build_paper_library_payload,
    handle_paper_library_event,
    paper_library_labels,
    resolve_paper_library_lang,
)
from nblane.core.research_papers import (
    PaperSearchResult,
    _duplicate_keys_for_result,
    _duplicate_keys_for_source,
    _result_from_url,
    assign_citation_keys,
    clear_paper_rows_cache,
    create_paper_annotation,
    create_paper_library_node,
    export_library_papers,
    format_research_citations,
    import_paper_url,
    load_paper_library_tree,
    paper_library_tree_snapshot,
    paper_rows,
    paper_rows_cache_stats,
    parse_paper_identifier,
    rename_paper_library_node,
    save_paper_library_tree,
)
from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    load_research_sources,
    save_research_sources,
)
from nblane.web_reader_api import app


def _no_backup():
    return patch("nblane.core.git_backup.record_change")


def _make_profile(root: Path) -> Path:
    profile = root / "alice"
    profile.mkdir()
    inbox = ResearchSourceInbox(profile="alice")
    add_research_source(
        inbox,
        "Attention Is All You Need",
        source_id="source:paper:attention",
        kind="paper",
        authors=["Ashish Vaswani", "Noam Shazeer"],
        published="2017",
        metadata={
            "venue": "Advances in Neural Information Processing Systems",
            "doi": "10.5555/3295222.3295349",
            "volume": "30",
            "pages": "5998-6008",
        },
    )
    add_research_source(
        inbox,
        "Deep learning",
        source_id="source:paper:deep",
        kind="paper",
        authors=["Yann LeCun", "Yoshua Bengio", "Geoffrey Hinton"],
        published="2015-05-27",
        metadata={"venue": "Nature", "doi": "10.1038/nature14539", "volume": "521", "issue": "7553", "pages": "436-444"},
    )
    add_research_source(
        inbox,
        "The Annotated Transformer",
        source_id="source:paper:annotated",
        kind="paper",
        authors=["Ashish Vaswani"],
        published="2017",
        url="https://arxiv.org/abs/1706.03762",
        metadata={"arxiv_id": "1706.03762", "categories": ["cs.CL", "cs.LG"]},
    )
    with _no_backup():
        save_research_sources(profile, inbox)
    return profile


class TestPaperIdentifierParsing(unittest.TestCase):
    def test_bare_and_url_identifiers(self) -> None:
        cases = {
            "10.1145/3290605.3300857": ("doi", "10.1145/3290605.3300857", ""),
            "doi:10.1038/nature14539": ("doi", "10.1038/nature14539", ""),
            "DOI: 10.1038/nature14539.": ("doi", "10.1038/nature14539", ""),
            "https://doi.org/10.1145/3290605.3300857": ("doi", "10.1145/3290605.3300857", ""),
            "2407.08693": ("arxiv", "", "2407.08693"),
            "2407.08693v2": ("arxiv", "", "2407.08693v2"),
            "arXiv:2407.08693": ("arxiv", "", "2407.08693"),
            "hep-th/9901001": ("arxiv", "", "hep-th/9901001"),
            "math.GT/0309136": ("arxiv", "", "math.GT/0309136"),
            "https://arxiv.org/abs/2407.08693v2": ("arxiv", "", "2407.08693v2"),
            "https://arxiv.org/pdf/2407.08693.pdf": ("arxiv", "", "2407.08693"),
            "https://arxiv.org/pdf/2407.08693v3": ("arxiv", "", "2407.08693v3"),
            "https://arxiv.org/abs/hep-th/9901001": ("arxiv", "", "hep-th/9901001"),
        }
        for raw, (kind, doi, arxiv_id) in cases.items():
            with self.subTest(raw=raw):
                parsed = parse_paper_identifier(raw)
                self.assertEqual(parsed["kind"], kind)
                self.assertEqual(parsed["doi"], doi)
                self.assertEqual(parsed["arxiv_id"], arxiv_id)

    def test_semantic_scholar_and_plain_urls(self) -> None:
        s2 = parse_paper_identifier(
            "https://www.semanticscholar.org/paper/Attention-Vaswani/204e3073870fae3d05bcbc2f6a8e263d9b72e776"
        )
        self.assertEqual(s2["kind"], "semantic_scholar")
        self.assertEqual(s2["semantic_scholar_id"], "204e3073870fae3d05bcbc2f6a8e263d9b72e776")
        self.assertEqual(parse_paper_identifier("https://example.com/paper.pdf")["kind"], "url")
        self.assertEqual(parse_paper_identifier("not an id")["kind"], "")
        # A year-like number is not an arXiv id.
        self.assertEqual(parse_paper_identifier("2024")["kind"], "")

    def test_bare_ids_use_enrichment_path(self) -> None:
        looked_up = {
            "title": "Looked Up Title",
            "authors": ["Ada Lovelace"],
            "year": "2024",
            "venue": "Nature",
            "canonical_url": "https://doi.org/10.1038/x",
        }
        with patch("nblane.core.research_papers.lookup_paper_metadata", return_value=looked_up) as lookup:
            doi_result = _result_from_url("10.1038/x")
            arxiv_result = _result_from_url("arXiv:2407.08693")
        self.assertEqual(lookup.call_args_list[0].kwargs["doi"], "10.1038/x")
        self.assertEqual(lookup.call_args_list[1].kwargs["arxiv_id"], "2407.08693")
        self.assertEqual(doi_result.doi, "10.1038/x")
        self.assertEqual(doi_result.title, "Looked Up Title")
        self.assertEqual(arxiv_result.arxiv_id, "2407.08693")
        self.assertEqual(arxiv_result.pdf_url, "https://arxiv.org/pdf/2407.08693")

    def test_bare_ids_offline_fall_back_to_placeholders(self) -> None:
        with patch.dict(os.environ, {"NBLANE_DISABLE_NETWORK_LOOKUPS": "1"}):
            doi_result = _result_from_url("doi:10.1038/nature14539")
            arxiv_result = _result_from_url("2407.08693v2")
        self.assertEqual(doi_result.title, "DOI 10.1038/nature14539")
        self.assertEqual(doi_result.canonical_url, "https://doi.org/10.1038/nature14539")
        self.assertEqual(arxiv_result.title, "arXiv 2407.08693v2")
        self.assertEqual(arxiv_result.canonical_url, "https://arxiv.org/abs/2407.08693v2")

    def test_import_bare_doi_creates_paper_and_dedupes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"NBLANE_DISABLE_NETWORK_LOOKUPS": "1"}):
            profile = _make_profile(Path(tmp))
            with _no_backup():
                source_id = import_paper_url(profile, "10.1145/3290605.3300857", {"download_pdf": False})
                with self.assertRaises(ValueError):
                    import_paper_url(profile, "https://doi.org/10.1145/3290605.3300857", {"download_pdf": False})
            source = load_research_sources(profile).by_id()[source_id]
        self.assertEqual(source.metadata["doi"], "10.1145/3290605.3300857")
        self.assertEqual(source.url, "https://doi.org/10.1145/3290605.3300857")

    def test_dedup_title_year_key_matches_source_shape(self) -> None:
        inbox = ResearchSourceInbox(profile="alice")
        source = add_research_source(inbox, "Same Title", kind="paper", published="2024-05-01")
        result = PaperSearchResult(title="Same Title", year="2024")
        self.assertTrue(_duplicate_keys_for_source(source) & _duplicate_keys_for_result(result))
        # Results with no year key on the title alone, like sources without a year.
        undated = add_research_source(inbox, "Undated", kind="paper")
        self.assertTrue(
            _duplicate_keys_for_source(undated) & _duplicate_keys_for_result(PaperSearchResult(title="Undated"))
        )


class TestLibraryExport(unittest.TestCase):
    def test_entry_types_and_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            with _no_backup():
                bib = export_library_papers(
                    profile,
                    ["source:paper:deep", "source:paper:attention", "source:paper:annotated"],
                    format="bibtex",
                )
        body = str(bib["body"])
        self.assertIn("@article{lecun2015deep,", body)
        self.assertIn("journal = {Nature}", body)
        self.assertIn("volume = {521}", body)
        self.assertIn("number = {7553}", body)
        self.assertIn("pages = {436--444}", body)
        self.assertIn("doi = {10.1038/nature14539}", body)
        self.assertIn("@inproceedings{vaswani2017attention,", body)
        self.assertIn("booktitle = {Advances in Neural Information Processing Systems}", body)
        self.assertIn("@misc{vaswani2017annotated,", body)
        self.assertIn("eprint = {1706.03762}", body)
        self.assertIn("archivePrefix = {arXiv}", body)
        self.assertIn("primaryClass = {cs.CL}", body)
        self.assertIn("url = {https://arxiv.org/abs/1706.03762}", body)
        self.assertIn("author = {LeCun, Yann and Bengio, Yoshua and Hinton, Geoffrey}", body)
        # Selection order is preserved.
        self.assertLess(body.index("lecun2015deep"), body.index("vaswani2017attention"))
        self.assertEqual(bib["filename"].rsplit(".", 1)[-1], "bib")
        self.assertEqual(bib["count"], 3)

    def test_ris_csl_markdown_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            ids = ["source:paper:deep", "source:paper:attention", "source:paper:annotated"]
            with _no_backup():
                ris = str(export_library_papers(profile, ids, format="ris")["body"])
                csl = str(export_library_papers(profile, ids, format="csl")["body"])
                md = export_library_papers(profile, ids[:1], format="md")
        self.assertIn("TY  - JOUR", ris)
        self.assertIn("TY  - CPAPER", ris)
        self.assertIn("TY  - GEN", ris)
        self.assertIn("SP  - 436", ris)
        self.assertIn("EP  - 444", ris)
        self.assertIn('"type": "article-journal"', csl)
        self.assertIn('"type": "paper-conference"', csl)
        self.assertIn('"citation-key": "vaswani2017annotated"', csl)
        self.assertIn("**Deep learning**", md["body"])
        self.assertIn("`@lecun2015deep`", md["body"])
        self.assertEqual(md["filename"], "lecun2015deep.md")
        with self.assertRaises(ValueError):
            export_library_papers(Path("/nonexistent"), ids, format="docx")

    def test_stable_keys_persist_and_collisions_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            inbox = load_research_sources(profile)
            add_research_source(
                inbox,
                "Attention Is All You Need (extended)",
                source_id="source:paper:attention-ext",
                kind="paper",
                authors=["Ashish Vaswani"],
                published="2017",
            )
            with _no_backup():
                save_research_sources(profile, inbox)
                # Export the colliding paper first: suffixes follow source-id order,
                # not selection order.
                first = export_library_papers(profile, ["source:paper:attention-ext"], format="bibtex")
                second = export_library_papers(
                    profile, ["source:paper:attention", "source:paper:attention-ext"], format="bibtex"
                )
            persisted = {
                source.id: source.metadata.get("citation_key")
                for source in load_research_sources(profile).sources
            }
        self.assertEqual(first["keys"], {"source:paper:attention-ext": "vaswani2017attention"})
        self.assertEqual(second["keys"]["source:paper:attention-ext"], "vaswani2017attention")
        self.assertEqual(second["keys"]["source:paper:attention"], "vaswani2017attentiona")
        self.assertEqual(persisted["source:paper:attention-ext"], "vaswani2017attention")
        self.assertEqual(persisted["source:paper:attention"], "vaswani2017attentiona")
        self.assertIsNone(persisted.get("source:paper:deep"))

    def test_existing_keys_are_never_changed(self) -> None:
        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(inbox, "A", source_id="s:1", kind="paper", authors=["X Y"], published="2020",
                            metadata={"citation_key": "custom-key"})
        add_research_source(inbox, "Graph nets", source_id="s:2", kind="paper", authors=["Ann Lee"], published="2020")
        add_research_source(inbox, "Graph nets", source_id="s:3", kind="paper", authors=["Ann Lee"], published="2020")
        keys, created = assign_citation_keys(inbox, ["s:3", "s:2", "s:1"])
        self.assertEqual(keys["s:1"], "custom-key")
        self.assertEqual(keys["s:2"], "lee2020graph")
        self.assertEqual(keys["s:3"], "lee2020grapha")
        self.assertEqual(sorted(created), ["s:2", "s:3"])
        again, created_again = assign_citation_keys(inbox, ["s:1", "s:2", "s:3"])
        self.assertEqual(again, keys)
        self.assertEqual(created_again, [])

    def test_citation_export_reuses_persisted_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            with _no_backup():
                export_library_papers(profile, ["source:paper:deep"], format="bibtex")
            # No citations yet: still formats (empty) without error.
            self.assertEqual(format_research_citations(profile, [], format="bibtex"), "")


class TestLibraryTreeLocking(unittest.TestCase):
    def test_concurrent_mutations_do_not_lose_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            original_load = load_paper_library_tree
            errors: list[BaseException] = []

            def slow_load(*args, **kwargs):
                # Widen the read-modify-write window so unlocked writers would race.
                tree = original_load(*args, **kwargs)
                time.sleep(0.02)
                return tree

            def worker(index: int) -> None:
                try:
                    create_paper_library_node(profile, f"Topic {index}")
                except BaseException as exc:  # pragma: no cover - surfaced below
                    errors.append(exc)

            with _no_backup(), patch(
                "nblane.core.research_papers._library_tree.load_paper_library_tree",
                side_effect=slow_load,
            ):
                threads = [threading.Thread(target=worker, args=(index,)) for index in range(8)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join(timeout=30)
            titles = sorted(node.title for node in load_paper_library_tree(profile).nodes)
        self.assertEqual(errors, [])
        self.assertEqual(titles, sorted(f"Topic {index}" for index in range(8)))

    def test_expected_snapshot_conflict_and_nested_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(Path(tmp))
            with _no_backup():
                node = create_paper_library_node(profile, "Robotics")
                snapshot = paper_library_tree_snapshot(profile)
                tree = load_paper_library_tree(profile)
                # A concurrent write lands after our read...
                rename_paper_library_node(profile, node.id, "Robotics (renamed)")
                with self.assertRaises(FileConflictError):
                    save_paper_library_tree(profile, tree, expected_snapshot=snapshot)
                # ...while a fresh snapshot saves fine.
                save_paper_library_tree(
                    profile,
                    load_paper_library_tree(profile),
                    expected_snapshot=paper_library_tree_snapshot(profile),
                )
            self.assertEqual(load_paper_library_tree(profile).nodes[0].title, "Robotics (renamed)")
            self.assertTrue((profile / "research" / "library-tree.yaml.lock").exists())


class TestPaperRowsCache(unittest.TestCase):
    def setUp(self) -> None:
        clear_paper_rows_cache()

    def test_repeated_calls_hit_cache_and_writes_invalidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")}
        ):
            profile = _make_profile(Path(tmp))
            before = paper_rows_cache_stats()
            first = paper_rows(profile)
            paper_rows(profile, view="unsorted")
            after_two = paper_rows_cache_stats()
            self.assertEqual(after_two["misses"] - before["misses"], 1)
            self.assertEqual(after_two["hits"] - before["hits"], 1)
            # Returned rows are copies: mutating them must not poison the cache.
            first[0]["title"] = "mutated"
            first[0]["badges"].append("bogus")
            fresh = paper_rows(profile)
            self.assertNotEqual(fresh[0]["title"], "mutated")
            self.assertNotIn("bogus", fresh[0]["badges"])

            with _no_backup():
                inbox = load_research_sources(profile)
                add_research_source(inbox, "Fresh Paper", source_id="source:paper:fresh", kind="paper")
                save_research_sources(profile, inbox)
            self.assertIn("source:paper:fresh", {row["id"] for row in paper_rows(profile)})

            with _no_backup():
                create_paper_annotation(profile, "source:paper:deep", "Selected text", page=1, kind="note", note="A note")
            deep = next(row for row in paper_rows(profile) if row["id"] == "source:paper:deep")
            self.assertEqual(deep["annotations_count"], 1)

            with _no_backup():
                node = create_paper_library_node(profile, "Vision")
                handle_paper_library_event(
                    profile,
                    {
                        "action": "paper_library_drop_papers_to_collection",
                        "payload": {"node_id": node.id, "paper_ids": ["source:paper:deep"]},
                    },
                )
                rename_paper_library_node(profile, node.id, "Computer Vision")
            deep = next(row for row in paper_rows(profile) if row["id"] == "source:paper:deep")
            self.assertEqual(deep["tree_path"], "Computer Vision")

    def test_payload_build_loads_rows_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")}
        ):
            profile = _make_profile(Path(tmp))
            with patch(
                "nblane.core.research_papers._diagnostics._build_paper_rows_base",
                wraps=__import__(
                    "nblane.core.research_papers._diagnostics", fromlist=["_build_paper_rows_base"]
                )._build_paper_rows_base,
            ) as build:
                build_paper_library_payload(profile, current_view="no_pdf")
                build_paper_library_payload(profile, current_view="reading")
        self.assertEqual(build.call_count, 1)


class TestPaperLibraryLabels(unittest.TestCase):
    def test_language_resolution_and_parity(self) -> None:
        self.assertEqual(resolve_paper_library_lang("zh"), "zh")
        self.assertEqual(resolve_paper_library_lang("zh-CN"), "zh")
        self.assertEqual(resolve_paper_library_lang("EN"), "en")
        en = paper_library_labels("en")
        zh = paper_library_labels("zh")
        self.assertEqual(set(en), set(zh))
        self.assertEqual(en["open_reader"], "Open Reader")
        self.assertEqual(zh["open_reader"], "打开阅读器")
        self.assertEqual(zh["export_selected"], "导出所选")
        self.assertEqual(zh["export_citation"], "导出引用")

    def test_payload_and_events_follow_ui_lang(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets")}
        ):
            profile = _make_profile(Path(tmp))
            zh = build_paper_library_payload(profile, ui_lang="zh")
            en = build_paper_library_payload(profile, ui_lang="en")
            with _no_backup():
                result = handle_paper_library_event(
                    profile,
                    {
                        "action": "paper_library_update_papers_status",
                        "payload": {"paper_ids": ["source:paper:deep"], "status": "archived"},
                        "state": {"ui_lang": "zh"},
                    },
                )
        self.assertEqual(zh["ui_lang"], "zh")
        self.assertEqual(zh["labels"]["open_reader"], "打开阅读器")
        self.assertEqual([section["title"] for section in zh["sections"]][:2], ["论文库", "分组"])
        self.assertEqual(zh["sections"][0]["items"][0]["title"], "全部论文")
        self.assertEqual(zh["active_label"], "全部论文")
        self.assertIn("缺少 PDF", zh["papers"][0]["badges"])
        self.assertIn("第", zh["papers"][0]["metrics"])
        self.assertEqual(en["sections"][0]["items"][0]["title"], "All Papers")
        self.assertIn("PDF missing", en["papers"][0]["badges"])
        self.assertIn("Page", en["papers"][0]["metrics"])
        self.assertEqual(result.message, "已归档 1 篇。")


class TestSidecarExportAndEmbed(unittest.TestCase):
    def _client(self, profile: Path) -> TestClient:
        patcher = patch("nblane.web_reader_api.profile_dir", return_value=profile)
        self.addCleanup(patcher.stop)
        patcher.start()
        return TestClient(app)

    def test_export_endpoint_returns_attachment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
        ):
            profile = _make_profile(Path(tmp))
            client = self._client(profile)
            with _no_backup():
                response = client.post(
                    "/api/research/alice/paper-library/export",
                    headers={"Origin": "http://testserver"},
                    json={"paper_ids": ["source:paper:deep", "source:paper:annotated"], "format": "bibtex"},
                )
                single = client.post(
                    "/api/research/alice/paper-library/export",
                    headers={"Origin": "http://testserver"},
                    json={"paper_ids": ["source:paper:deep"], "format": "ris"},
                )
                bad = client.post(
                    "/api/research/alice/paper-library/export",
                    headers={"Origin": "http://testserver"},
                    json={"paper_ids": [], "format": "bibtex"},
                )
                cross = client.post(
                    "/api/research/alice/paper-library/export",
                    headers={"Origin": "http://evil.example"},
                    json={"paper_ids": ["source:paper:deep"], "format": "bibtex"},
                )
            persisted = load_research_sources(profile).by_id()["source:paper:deep"].metadata
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["content-type"].startswith("application/x-bibtex"))
        self.assertIn("attachment;", response.headers["content-disposition"])
        self.assertIn(".bib", response.headers["content-disposition"])
        self.assertEqual(response.headers["x-nblane-export-count"], "2")
        self.assertIn("@article{lecun2015deep,", response.text)
        self.assertIn("@misc{vaswani2017annotated,", response.text)
        self.assertEqual(single.status_code, 200)
        self.assertIn('filename="lecun2015deep.ris"', single.headers["content-disposition"])
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(cross.status_code, 403)
        self.assertEqual(persisted["citation_key"], "lecun2015deep")

    def test_page_embed_and_ui_lang(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "NBLANE_READER_TOKEN_SECRET": "test-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(Path(tmp) / "assets"),
            },
        ):
            profile = _make_profile(Path(tmp))
            client = self._client(profile)
            page = client.get("/paper-library?profile=alice&embed=1&ui_lang=zh")
            plain = client.get("/paper-library?profile=alice&ui_lang=en")
            payload = client.get("/api/research/alice/paper-library?ui_lang=zh")
        self.assertEqual(page.status_code, 200)
        self.assertIn('class="is-embed"', page.text)
        self.assertIn('lang="zh-CN"', page.text)
        self.assertIn("embed: true", page.text)
        self.assertIn('uiLang: "zh"', page.text)
        self.assertIn("打开阅读器", page.text)
        self.assertIn("background: #0f1930", page.text)
        self.assertNotIn("#f5f7fa", page.text)
        self.assertIn("<title>论文库 · nblane</title>", page.text)
        self.assertNotIn('class="is-embed"', plain.text)
        self.assertIn("embed: false", plain.text)
        self.assertEqual(payload.json()["payload"]["ui_lang"], "zh")
        self.assertEqual(payload.json()["payload"]["labels"]["export_selected"], "导出所选")


if __name__ == "__main__":
    unittest.main()
