"""Tests for evidence duplicate detection + merge/deprecate."""

from __future__ import annotations

import unittest

from nblane.core.evidence_dedup import (
    apply_merge_or_deprecate,
    clusters_to_pairs,
    find_duplicate_candidates,
    merge_rows,
)


def _pair_ids(candidates):
    return {tuple(sorted((c["a"], c["b"]))) for c in candidates}


class TestFindDuplicateCandidates(unittest.TestCase):
    def test_exact_title(self) -> None:
        rows = [
            {"id": "a", "title": "测试腾讯云上海的训练速度", "origin": "kanban_task"},
            {"id": "b", "title": "测试腾讯云上海的训练速度", "origin": "kanban_task"},
            {"id": "c", "title": "unrelated work"},
        ]
        cands = find_duplicate_candidates(rows)
        self.assertIn(("a", "b"), _pair_ids(cands))
        self.assertEqual(len(cands), 1)

    def test_same_kanban_task(self) -> None:
        rows = [
            {"id": "a", "title": "x", "kanban_refs": ["kanban:t1"]},
            {"id": "b", "title": "y", "origin_ref": "kanban:t1"},
        ]
        cands = find_duplicate_candidates(rows)
        self.assertEqual(_pair_ids(cands), {("a", "b")})
        self.assertEqual(cands[0]["reason"], "same_kanban_task")

    def test_same_hash(self) -> None:
        rows = [
            {"id": "a", "title": "x", "original_content_hash": "sha256:zz"},
            {"id": "b", "title": "y", "original_content_hash": "sha256:zz"},
        ]
        cands = find_duplicate_candidates(rows)
        self.assertEqual(_pair_ids(cands), {("a", "b")})

    def test_high_overlap_same_language(self) -> None:
        rows = [
            {
                "id": "a",
                "title": "家庭鞋子抓取摆放 benchmark 梳理",
                "summary": "梳理鞋子抓取摆放 benchmark 的硬件定义与场景",
            },
            {
                "id": "b",
                "title": "家庭鞋子抓取摆放 benchmark 梳理（完整框架）",
                "summary": "梳理鞋子抓取摆放 benchmark 的硬件定义与场景与可复现性",
            },
            {"id": "c", "title": "完全不相关的论文阅读"},
        ]
        cands = find_duplicate_candidates(rows)
        self.assertIn(("a", "b"), _pair_ids(cands))
        self.assertNotIn(("a", "c"), _pair_ids(cands))

    def test_focus_id_limits_pairs(self) -> None:
        rows = [
            {"id": "a", "title": "dup", "origin": "kanban_task"},
            {"id": "b", "title": "dup", "origin": "kanban_task"},
            {"id": "c", "title": "dup", "origin": "kanban_task"},
        ]
        cands = find_duplicate_candidates(rows, focus_id="a")
        for c in cands:
            self.assertIn("a", (c["a"], c["b"]))

    def test_deprecated_excluded(self) -> None:
        rows = [
            {"id": "a", "title": "dup", "deprecated": True},
            {"id": "b", "title": "dup"},
        ]
        self.assertEqual(find_duplicate_candidates(rows), [])

    def test_recommend_keep_prefers_provenance(self) -> None:
        rows = [
            {"id": "manual", "title": "same", "origin": "manual_daily"},
            {
                "id": "kanban",
                "title": "same",
                "origin": "kanban_task",
                "kanban_refs": ["kanban:t1"],
                "original_content": "x" * 600,
                "review_status": "reviewed",
            },
        ]
        cands = find_duplicate_candidates(rows)
        self.assertEqual(cands[0]["recommend_keep"], "kanban")


class TestMergeRows(unittest.TestCase):
    def test_only_fills_empty(self) -> None:
        kept = {"id": "k", "summary": "keep me", "url": ""}
        other = {"id": "o", "summary": "ignore", "url": "http://x"}
        out = merge_rows(kept, other, fields=["summary", "url"])
        self.assertEqual(out["summary"], "keep me")  # not overwritten
        self.assertEqual(out["url"], "http://x")  # filled

    def test_list_union(self) -> None:
        kept = {"id": "k", "project_refs": ["p1"]}
        other = {"id": "o", "project_refs": ["p1", "p2"]}
        out = merge_rows(kept, other, fields=["project_refs"])
        self.assertEqual(out["project_refs"], ["p1", "p2"])

    def test_no_fields_no_change(self) -> None:
        kept = {"id": "k", "summary": "s"}
        self.assertEqual(merge_rows(kept, {"id": "o"}), kept)


class TestApplyMergeOrDeprecate(unittest.TestCase):
    def test_deprecate_only(self) -> None:
        rows = [{"id": "k", "title": "x"}, {"id": "o", "title": "x"}]
        out, changed = apply_merge_or_deprecate(rows, keep_id="k", other_id="o")
        self.assertTrue(changed)
        byid = {r["id"]: r for r in out}
        self.assertTrue(byid["o"]["deprecated"])
        self.assertEqual(byid["o"]["replaced_by"], "k")
        self.assertNotIn("deprecated", byid["k"])

    def test_merge_then_deprecate(self) -> None:
        rows = [
            {"id": "k", "title": "x", "summary": ""},
            {"id": "o", "title": "x", "summary": "from other"},
        ]
        out, changed = apply_merge_or_deprecate(
            rows, keep_id="k", other_id="o", merge_fields=["summary"]
        )
        byid = {r["id"]: r for r in out}
        self.assertEqual(byid["k"]["summary"], "from other")
        self.assertTrue(byid["o"]["deprecated"])

    def test_noop_on_bad_ids(self) -> None:
        rows = [{"id": "k", "title": "x"}]
        out, changed = apply_merge_or_deprecate(
            rows, keep_id="k", other_id="missing"
        )
        self.assertFalse(changed)

    def test_noop_same_id(self) -> None:
        rows = [{"id": "k", "title": "x"}]
        _, changed = apply_merge_or_deprecate(rows, keep_id="k", other_id="k")
        self.assertFalse(changed)


class TestClustersToPairs(unittest.TestCase):
    ROWS = [
        {"id": "a", "title": "t", "origin": "manual_daily"},
        {"id": "b", "title": "t", "origin": "kanban_task", "kanban_refs": ["kanban:1"]},
        {"id": "c", "title": "t", "origin": "resume_parse"},
    ]

    def test_cluster_expands_to_keep_pairs(self) -> None:
        clusters = [{"ids": ["a", "b", "c"], "recommend_keep": "b", "reason": "same"}]
        pairs = clusters_to_pairs(clusters, self.ROWS)
        self.assertEqual(_pair_ids(pairs), {("a", "b"), ("b", "c")})
        for p in pairs:
            self.assertEqual(p["recommend_keep"], "b")

    def test_bad_keep_falls_back_to_provenance(self) -> None:
        clusters = [{"ids": ["a", "c"], "recommend_keep": "nonexistent"}]
        pairs = clusters_to_pairs(clusters, self.ROWS)
        # neither a nor c has kanban provenance; keep is deterministic, valid id
        self.assertTrue(all(p["recommend_keep"] in ("a", "c") for p in pairs))

    def test_singleton_cluster_ignored(self) -> None:
        self.assertEqual(clusters_to_pairs([{"ids": ["a"]}], self.ROWS), [])


if __name__ == "__main__":
    unittest.main()
