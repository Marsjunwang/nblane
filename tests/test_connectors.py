"""Tests for Research Workspace connectors."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.research_connectors import (
    ConnectorAdapter,
    ConnectorItem,
    discover_connector_items,
    import_connector_items,
    import_manual_connector_items,
    load_connectors,
    parse_arxiv_feed,
    parse_github_payload,
    parse_semantic_scholar_payload,
    sync_connector,
    upsert_connector,
    preview_manual_connector_items,
)
from nblane.core.research_sources import load_research_sources


class FakeAdapter(ConnectorAdapter):
    provider = "github"

    def discover(self, config: dict[str, object]) -> list[ConnectorItem]:
        return [
            ConnectorItem(
                provider="github",
                title="octo/demo",
                url="https://github.com/octo/demo",
                kind="repo",
                external_id="repo-1",
                summary="Demo repo",
                tags=["github"],
                metadata={"token": "should-not-persist"},
            )
        ]


class TestResearchConnectors(unittest.TestCase):
    def test_provider_fixtures_normalize(self) -> None:
        arxiv = parse_arxiv_feed(
            b"""<?xml version='1.0' encoding='UTF-8'?>
            <feed xmlns='http://www.w3.org/2005/Atom'
                  xmlns:arxiv='http://arxiv.org/schemas/atom'>
              <entry>
                <id>https://arxiv.org/abs/2605.00001</id>
                <title> Source Aware Writing </title>
                <summary> A test abstract. </summary>
                <published>2026-05-13T00:00:00Z</published>
                <author><name>Alice</name></author>
                <category term='cs.CL'/>
                <arxiv:doi>10.48550/arXiv.2605.00001</arxiv:doi>
                <link title='pdf' href='https://arxiv.org/pdf/2605.00001' type='application/pdf'/>
              </entry>
            </feed>"""
        )
        semantic = parse_semantic_scholar_payload(
            {
                "data": [
                    {
                        "paperId": "S2-1",
                        "title": "Grounded Claims",
                        "url": "https://semanticscholar.org/paper/S2-1",
                        "abstract": "Abstract",
                        "authors": [{"name": "Bob"}],
                        "year": 2026,
                        "externalIds": {"ArXiv": "2605.00001", "DOI": "10.48550/arXiv.2605.00001"},
                        "citationCount": 42,
                        "venue": "ACL",
                        "fieldsOfStudy": ["Computer Science"],
                        "openAccessPdf": {
                            "url": "https://arxiv.org/pdf/2605.00001",
                            "status": "GREEN",
                        },
                    }
                ]
            }
        )
        github = parse_github_payload(
            {
                "items": [
                    {
                        "id": 1,
                        "full_name": "octo/demo",
                        "html_url": "https://github.com/octo/demo",
                        "description": "Demo",
                        "owner": {"login": "octo"},
                        "language": "Python",
                        "topics": ["research"],
                    }
                ]
            }
        )

        self.assertEqual(arxiv[0].kind, "paper")
        self.assertEqual(arxiv[0].authors, ["Alice"])
        self.assertEqual(arxiv[0].metadata["arxiv_id"], "2605.00001")
        self.assertEqual(arxiv[0].metadata["pdf_url"], "https://arxiv.org/pdf/2605.00001")
        self.assertEqual(arxiv[0].metadata["open_access_pdf_url"], "https://arxiv.org/pdf/2605.00001")
        self.assertEqual(arxiv[0].metadata["categories"], ["cs.CL"])
        self.assertEqual(arxiv[0].metadata["doi"], "10.48550/arXiv.2605.00001")
        self.assertEqual(semantic[0].metadata["paper_id"], "S2-1")
        self.assertEqual(semantic[0].metadata["semantic_scholar_id"], "S2-1")
        self.assertEqual(semantic[0].metadata["arxiv_id"], "2605.00001")
        self.assertEqual(semantic[0].metadata["doi"], "10.48550/arXiv.2605.00001")
        self.assertEqual(semantic[0].metadata["citation_count"], 42)
        self.assertEqual(semantic[0].metadata["venue"], "ACL")
        self.assertEqual(semantic[0].metadata["fields_of_study"], ["Computer Science"])
        self.assertEqual(
            semantic[0].metadata["open_access_pdf_url"],
            "https://arxiv.org/pdf/2605.00001",
        )
        self.assertEqual(
            semantic[0].metadata["open_access_pdf"],
            {"url": "https://arxiv.org/pdf/2605.00001", "status": "GREEN"},
        )
        self.assertEqual(github[0].kind, "repo")
        self.assertIn("Python", github[0].tags)

    def test_paper_adapters_honor_provider_timeout_config(self) -> None:
        with patch(
            "nblane.core.research_connectors._http_get",
            return_value=b"""<?xml version='1.0' encoding='UTF-8'?><feed xmlns='http://www.w3.org/2005/Atom' />""",
        ) as http_get:
            from nblane.core.research_connectors import ArxivAdapter

            ArxivAdapter().discover({"query": "vla memory", "limit": 1, "provider_timeout_seconds": 3})

        self.assertEqual(http_get.call_args.kwargs["timeout"], 3)

    def test_dry_run_does_not_write_and_run_dedupes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with patch("nblane.core.research_connectors.git_backup.record_change"):
                row = upsert_connector(
                    profile,
                    provider="github",
                    query="octo/demo",
                    options={"api_key": "secret", "limit": 1},
                )
            before = (profile / "research" / "connectors.yaml").read_text(encoding="utf-8")

            with (
                patch.dict("nblane.core.research_connectors.ADAPTERS", {"github": FakeAdapter()}),
                patch("nblane.core.research_sources.git_backup.record_change"),
                patch("nblane.core.research_connectors.git_backup.record_change"),
            ):
                dry = sync_connector(profile, str(row["id"]), dry_run=True)
                after_dry = (profile / "research" / "connectors.yaml").read_text(encoding="utf-8")
                first = sync_connector(profile, str(row["id"]))
                second = sync_connector(profile, str(row["id"]))

            sources = load_research_sources(profile)
            saved = load_connectors(profile)
            serialized = (profile / "research" / "connectors.yaml").read_text(encoding="utf-8")
            sources_serialized = (profile / "research" / "sources.yaml").read_text(encoding="utf-8")

        self.assertEqual(after_dry, before)
        self.assertEqual(dry.imported, 1)
        self.assertEqual(first.imported, 1)
        self.assertEqual(second.imported, 0)
        self.assertEqual(second.skipped, 1)
        self.assertEqual([source.title for source in sources.sources], ["octo/demo"])
        self.assertNotIn("secret", serialized)
        self.assertNotIn("should-not-persist", sources_serialized)
        self.assertEqual(saved["connectors"][0]["last_result"]["imported"], 0)

    def test_discover_preview_and_selected_import_with_collection_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with patch("nblane.core.research_connectors.git_backup.record_change"):
                row = upsert_connector(
                    profile,
                    provider="github",
                    query="octo/demo",
                    options={"api_key": "secret", "limit": 1},
                )
            before_sources_exists = (profile / "research" / "sources.yaml").exists()

            with (
                patch.dict("nblane.core.research_connectors.ADAPTERS", {"github": FakeAdapter()}),
                patch("nblane.core.research_sources.git_backup.record_change"),
                patch("nblane.core.research_connectors.git_backup.record_change"),
            ):
                preview = discover_connector_items(profile, str(row["id"]))
                after_preview_sources_exists = (profile / "research" / "sources.yaml").exists()
                fingerprint = str(preview["candidates"][0]["fingerprint"])
                imported = import_connector_items(
                    profile,
                    str(row["id"]),
                    [fingerprint],
                    target={"kind": "collection", "node_id": "paper-node:vla"},
                )
                duplicate_preview = discover_connector_items(profile, str(row["id"]))

            sources = load_research_sources(profile)
            saved = load_connectors(profile)
            serialized = (profile / "research" / "connectors.yaml").read_text(encoding="utf-8")
            sources_serialized = (profile / "research" / "sources.yaml").read_text(encoding="utf-8")

        self.assertFalse(before_sources_exists)
        self.assertFalse(after_preview_sources_exists)
        self.assertEqual(preview["discovered"], 1)
        self.assertEqual(preview["importable"], 1)
        self.assertFalse(preview["candidates"][0]["duplicate"]["is_duplicate"])
        self.assertEqual(imported.imported, 1)
        self.assertEqual(imported.skipped, 0)
        self.assertEqual([source.title for source in sources.sources], ["octo/demo"])
        self.assertEqual(sources.sources[0].library_node_refs, ["paper-node:vla"])
        self.assertTrue(duplicate_preview["candidates"][0]["duplicate"]["is_duplicate"])
        self.assertEqual(
            duplicate_preview["candidates"][0]["duplicate"]["existing_source_id"],
            sources.sources[0].id,
        )
        self.assertEqual(saved["connectors"][0]["last_result"]["selected"], 1)
        self.assertNotIn("secret", serialized)
        self.assertNotIn("should-not-persist", sources_serialized)

    def test_manual_preview_accepts_urls_csv_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            url_preview = preview_manual_connector_items(
                profile,
                "xiaohongshu",
                "https://example.com/a\nhttps://example.com/b",
            )
            csv_preview = preview_manual_connector_items(
                profile,
                "x_twitter",
                "title,url,summary\nTweet note,https://x.com/demo,Useful thread",
            )
            json_preview = preview_manual_connector_items(
                profile,
                "github",
                '[{"title": "octo/manual", "url": "https://github.com/octo/manual", "kind": "repo"}]',
            )
            with patch("nblane.core.research_sources.git_backup.record_change"):
                imported = import_manual_connector_items(
                    profile,
                    "xiaohongshu",
                    "https://example.com/a\nhttps://example.com/b",
                    [url_preview["candidates"][0]["fingerprint"]],
                    target={"kind": "collection", "node_id": "paper-node:manual"},
                )
            sources = load_research_sources(profile)

        self.assertEqual(url_preview["discovered"], 2)
        self.assertEqual(url_preview["candidates"][0]["item"]["url"], "https://example.com/a")
        self.assertEqual(csv_preview["candidates"][0]["item"]["title"], "Tweet note")
        self.assertEqual(json_preview["candidates"][0]["item"]["kind"], "repo")
        self.assertEqual(imported.imported, 1)
        self.assertEqual(sources.sources[0].library_node_refs, ["paper-node:manual"])

    def test_manual_import_can_target_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            raw = "title,url\nReading later,https://example.com/later"
            preview = preview_manual_connector_items(profile, "xiaohongshu", raw)
            with patch("nblane.core.research_sources.git_backup.record_change"):
                result = import_manual_connector_items(
                    profile,
                    "xiaohongshu",
                    raw,
                    [preview["candidates"][0]["fingerprint"]],
                    target={"kind": "metadata_only"},
                )
            source = load_research_sources(profile).sources[0]

        self.assertEqual(result.imported, 1)
        self.assertEqual(source.library_node_refs, [])
        self.assertEqual(source.metadata["import_target_kind"], "metadata_only")
        self.assertTrue(source.metadata["metadata_only"])


if __name__ == "__main__":
    unittest.main()
