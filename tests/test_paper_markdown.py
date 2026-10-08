"""Tests for the whole-paper Markdown export used by AI reading."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core import paper_markdown
from nblane.core.paper_markdown import build_paper_markdown
from nblane.core.research_papers import PaperSegment, save_paper_segments, text_hash
from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    save_research_sources,
)

SOURCE_ID = "source:paper:md"


def _segments() -> list[PaperSegment]:
    rows = [
        ("title", [], "A Tiny Paper"),
        ("heading", ["Introduction"], "Introduction"),
        ("paragraph", ["Introduction"], "We   study\nattention."),
        ("caption", ["Experiments"], "Table 2 :"),
        ("caption", ["Experiments"], "Results on the benchmark."),
        ("caption", ["Experiments"], "Figure 1: Overview."),
        ("formula", ["Method"], "y = f(x) (1)"),
        ("heading", ["References"], "References"),
        ("paragraph", ["References"], "[1] Someone. A paper. 2020."),
    ]
    return [
        PaperSegment(
            segment_id=f"seg:md:{index:03d}",
            source_id=SOURCE_ID,
            page=index,
            order=index,
            kind=kind,
            section_path=path,
            text=text,
            text_hash=text_hash(text),
        )
        for index, (kind, path, text) in enumerate(rows, start=1)
    ]


class TestPaperMarkdown(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        self.profile = base / "alice"
        self.profile.mkdir()
        env = patch.dict(os.environ, {"NBLANE_RESEARCH_ASSET_ROOT": str(base / "assets")})
        env.start()
        self.addCleanup(env.stop)
        for target in (
            "nblane.core.research_sources.git_backup.record_change",
            "nblane.core.research_papers.git_backup.record_change",
        ):
            patcher = patch(target)
            patcher.start()
            self.addCleanup(patcher.stop)
        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(inbox, "A Tiny Paper", source_id=SOURCE_ID, kind="paper", visibility="private")
        save_research_sources(self.profile, inbox)
        save_paper_segments(self.profile, SOURCE_ID, _segments())

    def test_renders_full_paper_with_anchors_and_aliases(self) -> None:
        md = build_paper_markdown(self.profile, SOURCE_ID, include_images=False)

        self.assertTrue(md.markdown.startswith("# A Tiny Paper\n"))
        self.assertIn("## Introduction", md.markdown)
        # Whitespace is collapsed and every body block ends with its anchor.
        self.assertIn("We study attention. 〔s1〕", md.markdown)
        self.assertEqual(md.aliases["s1"], "seg:md:003")
        # GROBID's bare "Table 2 :" label is folded into the next caption.
        self.assertNotIn("Table 2 :", md.markdown)
        self.assertIn("> **Table 2.** Results on the benchmark.", md.markdown)
        self.assertIn("> Figure 1: Overview.", md.markdown)
        self.assertIn("`y = f(x) (1)`", md.markdown)
        # References are listed once at the end, not anchored as body text.
        self.assertTrue(md.markdown.rstrip().endswith("- [1] Someone. A paper. 2020."))
        self.assertNotIn("seg:md:009", md.aliases.values())
        self.assertEqual(md.stats["references"], 1)
        self.assertEqual(md.images, [])

    def test_cache_hit_until_segments_change(self) -> None:
        first = build_paper_markdown(self.profile, SOURCE_ID, include_images=False)
        with patch.object(paper_markdown, "_render_markdown", side_effect=AssertionError("cache miss")):
            again = build_paper_markdown(self.profile, SOURCE_ID, include_images=False)
        self.assertEqual(again.directory, first.directory)
        self.assertEqual(again.markdown, first.markdown)

        changed = _segments()
        changed[2] = PaperSegment(
            segment_id="seg:md:003",
            source_id=SOURCE_ID,
            page=3,
            order=3,
            kind="paragraph",
            section_path=["Introduction"],
            text="We study recurrence.",
            text_hash=text_hash("We study recurrence."),
        )
        save_paper_segments(self.profile, SOURCE_ID, changed)
        rebuilt = build_paper_markdown(self.profile, SOURCE_ID, include_images=False)

        self.assertNotEqual(rebuilt.directory, first.directory)
        self.assertIn("We study recurrence.", rebuilt.markdown)
        # The stale export directory is removed.
        self.assertFalse(first.directory.exists())

    def test_without_pdf_images_are_skipped(self) -> None:
        md = build_paper_markdown(self.profile, SOURCE_ID, include_images=True)
        self.assertEqual(md.images, [])
        self.assertEqual(md.image_paths(), [])
        self.assertTrue((md.directory / "paper.md").is_file())


if __name__ == "__main__":
    unittest.main()
