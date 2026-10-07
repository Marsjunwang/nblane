"""Tests for Output Studio / Public Build split and research provenance checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core import public_site
from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    save_research_sources,
)
from nblane.core.research_workspace import (
    create_chunk,
    create_citation,
    upsert_research_claim,
)


class TestPublicSiteSplit(unittest.TestCase):
    def test_validate_public_layer_blocks_private_research_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.public_site.profile_dir", lambda _name: profile),
                patch("nblane.core.public_site.git_backup.record_change"),
            ):
                public_site.init_public_layer("alice")

            inbox = ResearchSourceInbox(profile="alice")
            add_research_source(
                inbox,
                "Private paper",
                source_id="source:private-paper",
                kind="paper",
                visibility="private",
            )
            with patch("nblane.core.research_sources.git_backup.record_change"):
                save_research_sources(profile, inbox)
            with patch("nblane.core.research_workspace.git_backup.record_change"):
                chunk = create_chunk(
                    profile,
                    "source:private-paper",
                    "Private quote.",
                )
                claim = upsert_research_claim(
                    profile,
                    "Private source supports this research claim.",
                    source_refs=["source:private-paper"],
                    chunk_refs=[chunk.id],
                    status="ready",
                )
                citation = create_citation(
                    profile,
                    claim.id,
                    source_id="source:private-paper",
                    chunk_id=chunk.id,
                    quote="Private quote.",
                )

            post_path = profile / "blog" / "private-research.md"
            post_path.parent.mkdir(exist_ok=True)
            post_path.write_text(
                "---\n"
                + yaml.dump(
                    {
                        "title": "Private Research",
                        "date": "2026-05-14",
                        "status": "published",
                        "tags": ["research"],
                        "summary": "Summary",
                        "cover": "",
                        "related_evidence": [],
                        "related_kanban": [],
                        "related_claims": [],
                        "related_sources": ["source:private-paper"],
                        "related_research_claims": [claim.id],
                        "related_citations": [citation.id],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                )
                + "---\n\nBody.\n",
                encoding="utf-8",
            )

            with patch("nblane.core.public_site.profile_dir", lambda _name: profile):
                result = public_site.validate_public_layer("alice")

        joined = "\n".join(result.errors)
        self.assertIn("private", joined)
        self.assertIn("must be promoted", joined)

    def test_validate_public_layer_accepts_public_promoted_research_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch("nblane.core.public_site.profile_dir", lambda _name: profile),
                patch("nblane.core.public_site.git_backup.record_change"),
            ):
                public_site.init_public_layer("alice")

            inbox = ResearchSourceInbox(profile="alice")
            add_research_source(
                inbox,
                "Public paper",
                source_id="source:public-paper",
                kind="paper",
                visibility="public",
            )
            with patch("nblane.core.research_sources.git_backup.record_change"):
                save_research_sources(profile, inbox)
            with patch("nblane.core.research_workspace.git_backup.record_change"):
                chunk = create_chunk(profile, "source:public-paper", "Public quote.")
                claim = upsert_research_claim(
                    profile,
                    "Public source supports this research claim.",
                    source_refs=["source:public-paper"],
                    chunk_refs=[chunk.id],
                    status="promoted",
                )
                citation = create_citation(
                    profile,
                    claim.id,
                    source_id="source:public-paper",
                    chunk_id=chunk.id,
                    quote="Public quote.",
                )

            with (
                patch("nblane.core.public_site.profile_dir", lambda _name: profile),
                patch("nblane.core.public_site.git_backup.record_change"),
            ):
                path = public_site.create_blog_draft(
                    "alice",
                    title="Public Research",
                    body="Body.",
                    tags=["research"],
                    summary="Summary",
                    related_sources=["source:public-paper"],
                    related_research_claims=[claim.id],
                    related_citations=[citation.id],
                    slug="public-research",
                )
                post = public_site.parse_blog_post(path)
                post.meta["status"] = "published"
                public_site.save_blog_post("alice", "public-research", post.meta, post.body)
                result = public_site.validate_public_layer("alice")

        self.assertEqual(result.errors, [])


if __name__ == "__main__":
    unittest.main()
