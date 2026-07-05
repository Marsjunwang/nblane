"""Tests for output -> evidence conversion."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from nblane.core.evidence_from_output import (
    evidence_row_from_blog_post,
    evidence_row_from_output,
    merge_source_refresh,
)


SAMPLE_OUTPUT = {
    "id": "blog_18502",
    "title": "NB-Lane Reader launch",
    "summary": "Shipped the standalone reader page.",
    "target": "blog",
    "status": "published",
    "body": "A" * 500,
    "project_refs": ["project:nblane"],
    "year": "2026",
}


class TestEvidenceFromOutput(unittest.TestCase):
    def test_basic_fields(self) -> None:
        row = evidence_row_from_output(SAMPLE_OUTPUT, target_lang="en")
        self.assertEqual(row["id"], "out_blog_18502")
        self.assertEqual(row["origin"], "output")
        self.assertEqual(row["origin_ref"], "output:blog_18502")
        self.assertEqual(row["review_status"], "needs_review")
        # Never auto-published.
        self.assertEqual(row["public_readiness"], "private")

    def test_body_preserved_as_preview(self) -> None:
        row = evidence_row_from_output(SAMPLE_OUTPUT, target_lang="en")
        self.assertIn("Body preview:", row["original_content"])
        # Full 500-char body is truncated to a preview, not copied whole.
        self.assertLess(len(row["original_content"]), 400)
        self.assertTrue(row["original_content_hash"].startswith("sha256:"))

    def test_project_refs_inherited(self) -> None:
        row = evidence_row_from_output(SAMPLE_OUTPUT, target_lang="en")
        self.assertEqual(row["project_refs"], ["project:nblane"])

    def test_no_duplicate_id(self) -> None:
        row = evidence_row_from_output(
            SAMPLE_OUTPUT,
            existing_ids={"out_blog_18502"},
            target_lang="en",
        )
        self.assertEqual(row["id"], "out_blog_18502_2")

    def test_type_inference(self) -> None:
        out = dict(SAMPLE_OUTPUT, target="project_update")
        row = evidence_row_from_output(out, target_lang="en")
        self.assertEqual(row["type"], "project")

    def test_missing_optional_fields(self) -> None:
        row = evidence_row_from_output({"id": "x"}, target_lang="en")
        self.assertEqual(row["id"], "out_x")
        self.assertEqual(row["title"], "x")
        self.assertEqual(row["type"], "practice")
        self.assertNotIn("project_refs", row)

    def test_blog_post_source_identity(self) -> None:
        post = SimpleNamespace(
            route="notes/launch",
            slug="notes/launch",
            title="Launch note",
            summary="Published launch note.",
            status="published",
            date="2026-05-01",
            path="blog/notes/launch.md",
            body="Full body",
            url_path="blog/notes/launch/",
        )
        row = evidence_row_from_blog_post(
            post,
            project_refs=["project:nblane"],
            target_lang="en",
        )
        self.assertEqual(row["origin"], "output")
        self.assertEqual(row["origin_ref"], "blog:notes/launch")
        self.assertEqual(row["date"], "2026-05-01")
        self.assertEqual(row["project_refs"], ["project:nblane"])
        self.assertIn("Body preview:", row["original_content"])


class TestSourceContentHash(unittest.TestCase):
    """source_content_hash covers the full source body, not the truncated preview.

    original_content_hash only hashes the (100/2000-char) preview stored in
    original_content, so edits past that window are invisible to it. This is
    the whole point of source_content_hash: it must change even when the edit
    is far outside the preview window.
    """

    def test_output_hash_detects_change_past_preview_window(self) -> None:
        out = dict(SAMPLE_OUTPUT, body="A" * 5000)
        row_before = evidence_row_from_output(out, target_lang="en")
        out_changed = dict(out, body=out["body"][:4000] + "X" + out["body"][4001:])
        row_after = evidence_row_from_output(out_changed, target_lang="en")
        # original_content_hash is blind to this change (edit is past the preview).
        self.assertEqual(
            row_before["original_content_hash"], row_after["original_content_hash"]
        )
        # source_content_hash is not.
        self.assertNotEqual(
            row_before["source_content_hash"], row_after["source_content_hash"]
        )

    def test_blog_hash_detects_change_past_preview_window(self) -> None:
        def make_post(body: str) -> SimpleNamespace:
            return SimpleNamespace(
                route="notes/launch",
                slug="notes/launch",
                title="Launch note",
                summary="",
                status="published",
                date="2026-05-01",
                path="blog/notes/launch.md",
                body=body,
                url_path="blog/notes/launch/",
            )

        long_body = "A" * 3000
        row_before = evidence_row_from_blog_post(
            make_post(long_body), project_refs=[], target_lang="en"
        )
        changed_body = long_body[:2500] + "X" + long_body[2501:]
        row_after = evidence_row_from_blog_post(
            make_post(changed_body), project_refs=[], target_lang="en"
        )
        self.assertEqual(
            row_before["original_content_hash"], row_after["original_content_hash"]
        )
        self.assertNotEqual(
            row_before["source_content_hash"], row_after["source_content_hash"]
        )


class TestMergeSourceRefresh(unittest.TestCase):
    def test_refreshes_source_fields(self) -> None:
        old_row = {
            "id": "out_blog_18502",
            "type": "practice",
            "title": "Old title",
            "original_content": "old preview",
            "original_content_hash": "sha256:old",
            "source_content_hash": "sha256:old",
            "date": "2026-01-01",
        }
        new_row = {
            "title": "New title",
            "original_content": "new preview",
            "original_content_hash": "sha256:new",
            "source_content_hash": "sha256:new",
            "date": "2026-06-01",
            "url": "https://example.com/new",
        }
        merged = merge_source_refresh(old_row, new_row)
        self.assertEqual(merged["id"], "out_blog_18502")
        self.assertEqual(merged["title"], "New title")
        self.assertEqual(merged["original_content"], "new preview")
        self.assertEqual(merged["source_content_hash"], "sha256:new")
        self.assertEqual(merged["date"], "2026-06-01")
        self.assertEqual(merged["url"], "https://example.com/new")

    def test_preserves_human_review_fields(self) -> None:
        old_row = {
            "id": "e1",
            "type": "practice",
            "title": "Old",
            "source_content_hash": "sha256:old",
            "strength": "expert",
            "confidence": "high",
            "review_status": "reviewed",
            "public_readiness": "public",
            "project_refs": ["project:nblane"],
            "experience_refs": ["exp:1"],
        }
        new_row = {
            "title": "New",
            "source_content_hash": "sha256:new",
            "review_status": "needs_review",
            "public_readiness": "private",
            "project_refs": [],
        }
        merged = merge_source_refresh(old_row, new_row)
        self.assertEqual(merged["strength"], "expert")
        self.assertEqual(merged["confidence"], "high")
        self.assertEqual(merged["public_readiness"], "public")
        self.assertEqual(merged["project_refs"], ["project:nblane"])
        self.assertEqual(merged["experience_refs"], ["exp:1"])

    def test_bumps_review_status_when_source_changed(self) -> None:
        old_row = {
            "id": "e1",
            "type": "practice",
            "title": "Old",
            "source_content_hash": "sha256:old",
            "review_status": "reviewed",
        }
        new_row = {"title": "New", "source_content_hash": "sha256:new"}
        merged = merge_source_refresh(old_row, new_row)
        self.assertEqual(merged["review_status"], "needs_review")

    def test_keeps_review_status_when_source_unchanged(self) -> None:
        old_row = {
            "id": "e1",
            "type": "practice",
            "title": "Old",
            "source_content_hash": "sha256:same",
            "review_status": "reviewed",
        }
        new_row = {"title": "Old", "source_content_hash": "sha256:same"}
        merged = merge_source_refresh(old_row, new_row)
        self.assertEqual(merged["review_status"], "reviewed")

    def test_keeps_human_polished_summary_and_formatted_content(self) -> None:
        old_row = {
            "id": "e1",
            "type": "practice",
            "title": "Old",
            "summary": "Human-polished summary.",
            "formatted_content": "# Human-polished body",
        }
        new_row = {
            "title": "New",
            "summary": "AI regenerated summary.",
            "formatted_content": "# AI regenerated body",
        }
        merged = merge_source_refresh(old_row, new_row)
        self.assertEqual(merged["summary"], "Human-polished summary.")
        self.assertEqual(merged["formatted_content"], "# Human-polished body")

    def test_fills_empty_summary_and_formatted_content_from_new_row(self) -> None:
        old_row = {"id": "e1", "type": "practice", "title": "Old"}
        new_row = {
            "title": "New",
            "summary": "First summary.",
            "formatted_content": "# First body",
        }
        merged = merge_source_refresh(old_row, new_row)
        self.assertEqual(merged["summary"], "First summary.")
        self.assertEqual(merged["formatted_content"], "# First body")


if __name__ == "__main__":
    unittest.main()
