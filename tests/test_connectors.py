"""Tests for Research Workspace connectors."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.research_connectors import (
    ConnectorAdapter,
    ConnectorItem,
    load_connectors,
    parse_arxiv_feed,
    parse_github_payload,
    parse_semantic_scholar_payload,
    sync_connector,
    upsert_connector,
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
            <feed xmlns='http://www.w3.org/2005/Atom'>
              <entry>
                <id>https://arxiv.org/abs/2605.00001</id>
                <title> Source Aware Writing </title>
                <summary> A test abstract. </summary>
                <published>2026-05-13T00:00:00Z</published>
                <author><name>Alice</name></author>
                <category term='cs.CL'/>
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
                        "externalIds": {"ArXiv": "2605.00001"},
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
        self.assertEqual(semantic[0].metadata["paper_id"], "S2-1")
        self.assertEqual(github[0].kind, "repo")
        self.assertIn("Python", github[0].tags)

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


if __name__ == "__main__":
    unittest.main()
