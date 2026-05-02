from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import get_args
from unittest.mock import patch

import yaml

from nblane.core import ai_blog_reviewer, public_site
from nblane.core.ai_blog_prompts import available_prompts, validate_prompt_sets
from schemas.ai_patch import AIOperation


def _write_blog(path: Path, *, title: str = "Draft", body: str = "Body.") -> None:
    meta = {
        "title": title,
        "date": "2026-04-26",
        "status": "draft",
        "tags": ["demo"],
        "summary": "Summary",
        "cover": "",
        "related_evidence": [],
        "related_kanban": [],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        + yaml.dump(meta, allow_unicode=True, default_flow_style=False, sort_keys=False)
        + "---\n\n"
        + body
        + "\n",
        encoding="utf-8",
    )


class AIBlogPhase4Tests(unittest.TestCase):
    def test_sidecar_wins_over_markdown_and_restores_deleted_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            blog = profile / "blog"
            post_path = blog / "post.md"
            _write_blog(post_path, title="Markdown title", body="Markdown body.")
            blocks = [
                {
                    "id": "b1",
                    "type": "paragraph",
                    "props": {},
                    "content": [{"type": "text", "text": "Sidecar body.", "styles": {}}],
                    "children": [],
                }
            ]

            with patch("nblane.core.public_site.profile_dir", lambda _name: profile), patch(
                "nblane.core.public_site.git_backup.record_change"
            ):
                saved, changed = public_site.save_blog_post(
                    "alice",
                    "post",
                    {
                        "title": "Sidecar title",
                        "date": "2026-04-26",
                        "status": "draft",
                        "tags": ["sidecar"],
                        "summary": "Sidecar summary",
                        "cover": "",
                        "related_evidence": [],
                        "related_kanban": [],
                    },
                    "Sidecar body.\n",
                    blocks_json=blocks,
                )

                sidecar = public_site.blog_sidecar_path_for_slug("alice", "post")
                self.assertEqual(saved, post_path)
                self.assertEqual(changed, [])
                self.assertTrue(sidecar.exists())
                self.assertIn("source_md_sha256", sidecar.read_text(encoding="utf-8"))

                post_path.write_text("---\ntitle: External edit\n---\n\nExternal body\n", encoding="utf-8")
                loaded = public_site.load_blog_post("alice", "post")
                self.assertEqual(loaded.title, "Sidecar title")
                self.assertEqual(loaded.body, "Sidecar body.\n")
                self.assertEqual(loaded.blocks_json[0]["id"], "b1")

                post_path.unlink()
                posts = public_site.load_blog_posts("alice", include_drafts=True)
                self.assertEqual([post.slug for post in posts], ["post"])
                restored, _changed = public_site.save_blog_post(
                    "alice",
                    "post",
                    loaded.meta,
                    loaded.body,
                    blocks_json=loaded.blocks_json,
                )
                self.assertEqual(restored, post_path)
                self.assertTrue(post_path.exists())

    def test_reviewer_findings_and_repair_patches(self) -> None:
        meta = {"title": "tttt", "summary": "", "related_evidence": [], "cover": ""}
        body = "See profiles/alice/evidence-pool.yaml.\n\n![](media/blog/post/chart.png)\n"
        media_rows = [
            {
                "kind": "image",
                "name": "chart.png",
                "relative_path": "media/blog/post/chart.png",
                "referenced": True,
            },
            {
                "kind": "image",
                "name": "unused.png",
                "relative_path": "media/blog/post/unused.png",
                "referenced": False,
            },
        ]

        findings = ai_blog_reviewer.review_blog(
            slug="post",
            meta=meta,
            body=body,
            media_rows=media_rows,
            orphan_candidates=[
                {
                    "candidate_path": "blog/.candidates/ai-old/example.png",
                    "size_bytes": 2 * 1024 * 1024,
                }
            ],
        )
        categories = {finding["category"] for finding in findings}
        self.assertIn("privacy_path", categories)
        self.assertIn("weak_title", categories)
        self.assertIn("missing_cover", categories)
        self.assertIn("missing_summary", categories)
        self.assertIn("missing_tags", categories)
        self.assertIn("missing_alt_text", categories)
        self.assertIn("unreferenced_media", categories)
        self.assertIn("orphan_visual_candidates", categories)

        for category in ("missing_summary", "missing_tags"):
            finding = next(item for item in findings if item["category"] == category)
            self.assertTrue(finding["repairable"])
            self.assertEqual(finding["repair_action"], "request_reviewer_repair")

        orphan = next(finding for finding in findings if finding["category"] == "orphan_visual_candidates")
        self.assertFalse(orphan["repairable"])
        self.assertEqual(orphan["location"]["count"], 1)
        self.assertIn("blog/.candidates/ai-old/example.png", orphan["detail"])

        weak = next(finding for finding in findings if finding["category"] == "weak_title")
        weak_patch = ai_blog_reviewer.repair_patch_for_finding(
            slug="post",
            meta=meta,
            body=body,
            media_rows=media_rows,
            finding=weak,
            source_event_id="evt-1",
        )
        self.assertEqual(weak_patch["operation"], "check")
        self.assertIn("title", weak_patch["meta_patch"])

        privacy = next(finding for finding in findings if finding["category"] == "privacy_path")
        privacy_patch = ai_blog_reviewer.repair_patch_for_finding(
            slug="post",
            meta=meta,
            body=body,
            media_rows=media_rows,
            finding=privacy,
            source_event_id="evt-2",
        )
        self.assertIn("[redacted internal reference]", privacy_patch["markdown_fallback"])
        self.assertTrue(privacy_patch["target"]["range"]["full_document"])

        summary = next(finding for finding in findings if finding["category"] == "missing_summary")
        summary_patch = ai_blog_reviewer.repair_patch_for_finding(
            slug="post",
            meta=meta,
            body=body,
            media_rows=media_rows,
            finding=summary,
            source_event_id="evt-3",
        )
        self.assertIn("summary", summary_patch["meta_patch"])
        self.assertTrue(summary_patch["meta_patch"]["summary"])

        tags = next(finding for finding in findings if finding["category"] == "missing_tags")
        tags_patch = ai_blog_reviewer.repair_patch_for_finding(
            slug="post",
            meta=meta,
            body=body,
            media_rows=media_rows,
            finding=tags,
            source_event_id="evt-4",
        )
        self.assertIn("tags", tags_patch["meta_patch"])
        self.assertTrue(tags_patch["meta_patch"]["tags"])

        marker_findings = ai_blog_reviewer.review_blog(
            slug="post",
            meta={**meta, "summary": "Summary", "tags": ["demo"]},
            body="Intro.\n\n<!-- nblane:insert -->\n\nTail.\n",
            media_rows=[],
        )
        marker = next(item for item in marker_findings if item["category"] == "leftover_insert_marker")
        self.assertTrue(marker["repairable"])
        marker_patch = ai_blog_reviewer.repair_patch_for_finding(
            slug="post",
            meta=meta,
            body="Intro.\n\n<!-- nblane:insert -->\n\nTail.\n",
            media_rows=[],
            finding=marker,
            source_event_id="evt-5",
        )
        self.assertNotIn("<!-- nblane:insert -->", marker_patch["markdown_fallback"])
        self.assertTrue(marker_patch["target"]["range"]["full_document"])

    def test_prompt_alignment_covers_ai_operations(self) -> None:
        self.assertEqual(validate_prompt_sets(), {})
        operation_prompt = {
            "polish": "polish",
            "rewrite": "rewrite",
            "shorten": "shorten",
            "expand": "expand",
            "continue": "continue",
            "translate": "translate",
            "tone": "tone",
            "outline": "outline",
            "expand_section": "expand",
            "formula": "nl_to_latex",
            "visual": "visual",
            "meta": "meta",
            "check": "check",
        }
        self.assertEqual(set(get_args(AIOperation)), set(operation_prompt))
        for lang in ("zh", "en"):
            available = available_prompts(lang)
            for prompt_name in operation_prompt.values():
                self.assertIn(prompt_name, available)


if __name__ == "__main__":
    unittest.main()
