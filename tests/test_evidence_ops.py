"""Tests for evidence_ops (pool ref scan and prune)."""

from __future__ import annotations

import unittest

from nblane.core.evidence_ops import (
    pool_id_referenced_by_nodes,
    prune_pool_id_from_tree,
    prune_pool_id_in_rows,
)


class TestPoolIdReferencedByNodes(unittest.TestCase):
    """pool_id_referenced_by_nodes."""

    def test_empty_tree(self) -> None:
        """No nodes → empty list."""
        self.assertEqual(
            pool_id_referenced_by_nodes({}, "x"),
            [],
        )

    def test_finds_nodes_stable_order(self) -> None:
        """Returns each node id once, in traversal order."""
        tree = {
            "nodes": [
                {
                    "id": "a",
                    "evidence_refs": ["p1", "p2"],
                },
                {
                    "id": "b",
                    "evidence_refs": ["p2"],
                },
            ],
        }
        self.assertEqual(
            pool_id_referenced_by_nodes(tree, "p2"),
            ["a", "b"],
        )

    def test_blank_pool_id(self) -> None:
        """Whitespace-only id → no matches."""
        tree = {
            "nodes": [
                {"id": "a", "evidence_refs": ["x"]},
            ],
        }
        self.assertEqual(
            pool_id_referenced_by_nodes(tree, "   "),
            [],
        )


class TestPrunePoolIdFromTree(unittest.TestCase):
    """prune_pool_id_from_tree."""

    def test_immutable_input(self) -> None:
        """Original tree unchanged after prune."""
        tree = {
            "profile": "u",
            "nodes": [
                {
                    "id": "n1",
                    "evidence_refs": ["keep", "drop"],
                },
            ],
        }
        orig_refs = list(
            tree["nodes"][0]["evidence_refs"]
        )
        out = prune_pool_id_from_tree(tree, "drop")
        self.assertEqual(
            tree["nodes"][0]["evidence_refs"],
            orig_refs,
        )
        self.assertEqual(
            out["nodes"][0]["evidence_refs"],
            ["keep"],
        )

    def test_removes_empty_refs_key(self) -> None:
        """Drops evidence_refs when list becomes empty."""
        tree = {
            "nodes": [
                {"id": "n1", "evidence_refs": ["only"]},
            ],
        }
        out = prune_pool_id_from_tree(tree, "only")
        self.assertNotIn(
            "evidence_refs",
            out["nodes"][0],
        )


class TestPrunePoolIdInRows(unittest.TestCase):
    """prune_pool_id_in_rows."""

    def test_mutates_rows(self) -> None:
        """Strips id from row evidence_refs."""
        rows = [
            {
                "id": "a",
                "evidence_refs": ["p1", "p2"],
            },
        ]
        prune_pool_id_in_rows(rows, "p1")
        self.assertEqual(rows[0]["evidence_refs"], ["p2"])
