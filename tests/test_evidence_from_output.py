"""Tests for output -> evidence conversion."""

from __future__ import annotations

import unittest

from nblane.core.evidence_from_output import evidence_row_from_output


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


if __name__ == "__main__":
    unittest.main()
