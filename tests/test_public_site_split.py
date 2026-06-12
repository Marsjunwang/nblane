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
    def test_compat_and_split_pages_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        compat = root / "pages" / "6_Public_Site.py"
        output = root / "pages" / "6_Output_Studio.py"
        build = root / "pages" / "10_Public_Build.py"
        output_module = root / "src" / "nblane" / "web_output_studio.py"

        self.assertTrue(compat.exists())
        self.assertTrue(output.exists())
        self.assertTrue(build.exists())
        self.assertIn("pages/6_Output_Studio.py", compat.read_text(encoding="utf-8"))
        self.assertIn("pages/10_Public_Build.py", compat.read_text(encoding="utf-8"))
        output_text = output.read_text(encoding="utf-8")
        build_text = build.read_text(encoding="utf-8")
        self.assertIn("from nblane.web_output_studio import main", output_text)
        self.assertIn("from nblane.web_public_build import main", build_text)
        self.assertIn("main()", output_text)
        self.assertIn("main()", build_text)
        self.assertNotIn("import *", output_text)
        self.assertNotIn("import *", build_text)
        self.assertNotIn("with tab_build", output_module.read_text(encoding="utf-8"))

    def test_app_navigation_uses_split_output_and_workbench_order(self) -> None:
        root = Path(__file__).resolve().parents[1]
        app_text = (root / "app.py").read_text(encoding="utf-8")
        shared_text = (root / "src/nblane/web_shared.py").read_text(encoding="utf-8")
        self.assertIn('"pages/6_Output_Studio.py"', app_text)
        self.assertIn('"pages/10_Public_Build.py"', app_text)
        nav_text = app_text.split("def _navigation_pages", 1)[1]
        # Daily (work) group: doing-the-work pages only.
        work_order = [
            nav_text.index('"pages/3_Kanban.py"'),
            nav_text.index('"pages/7_Research.py"'),
            nav_text.index('"pages/11_Project_Board.py"'),
        ]
        self.assertEqual(work_order, sorted(work_order))
        # Build (growth) group: capability-building trio, Evidence beside Skill Tree.
        growth_order = [
            nav_text.index('"pages/1_Skill_Tree.py"'),
            nav_text.index("EVIDENCE_REVIEW_PAGE"),
            nav_text.index('"pages/2_Gap_Analysis.py"'),
        ]
        self.assertEqual(growth_order, sorted(growth_order))
        # Evidence Review sits in the Build group, after Skill Tree and before
        # the Output group (so it is no longer in the Daily group).
        self.assertLess(
            nav_text.index('"pages/1_Skill_Tree.py"'),
            nav_text.index("EVIDENCE_REVIEW_PAGE"),
        )
        self.assertLess(
            nav_text.index("EVIDENCE_REVIEW_PAGE"),
            nav_text.index('"pages/6_Output_Studio.py"'),
        )
        fallback_nav = shared_text.split("def render_workspace_navigation", 1)[1]
        fallback_work_order = [
            fallback_nav.index('"pages/3_Kanban.py"'),
            fallback_nav.index('"pages/7_Research.py"'),
            fallback_nav.index('"pages/11_Project_Board.py"'),
        ]
        self.assertEqual(fallback_work_order, sorted(fallback_work_order))
        fallback_growth_order = [
            fallback_nav.index('"pages/1_Skill_Tree.py"'),
            fallback_nav.index('"pages/2_Evidence_Review.py"'),
            fallback_nav.index('"pages/2_Gap_Analysis.py"'),
        ]
        self.assertEqual(fallback_growth_order, sorted(fallback_growth_order))

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
