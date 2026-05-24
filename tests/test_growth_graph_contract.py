"""Tests for the Growth Graph machine-readable contract."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nblane.core.growth_graph_contract import (
    growth_graph_contract,
    growth_graph_edge_types,
    growth_graph_layers,
    growth_graph_node_type_layers,
    growth_graph_node_types,
)
from nblane.core.workspace_graph import (
    workspace_graph_edge_types,
    workspace_graph_layers,
    workspace_graph_node_types,
)


class GrowthGraphContractTests(unittest.TestCase):
    def test_growth_graph_contract_reads_product_doc(self) -> None:
        """The product doc exposes the layer, node, and edge ids used by code."""
        contract = growth_graph_contract()

        self.assertEqual(contract["schema_version"], "1.0")
        self.assertEqual(
            list(growth_graph_layers()),
            [
                "direction",
                "objective",
                "work_context",
                "activity",
                "source",
                "evidence",
                "claim",
                "capability",
                "output",
                "feedback",
                "governance",
            ],
        )
        self.assertIn("north_star", growth_graph_node_types())
        self.assertIn("source_to_candidate", growth_graph_edge_types())
        self.assertEqual(growth_graph_node_type_layers()["claim"], "claim")

    def test_workspace_graph_uses_growth_graph_contract(self) -> None:
        """Workspace graph helpers delegate to the same contract source."""
        self.assertEqual(workspace_graph_layers(), growth_graph_layers())
        self.assertEqual(workspace_graph_node_types(), growth_graph_node_types())
        self.assertEqual(workspace_graph_edge_types(), growth_graph_edge_types())

    def test_growth_graph_contract_falls_back_when_doc_block_missing(self) -> None:
        """Old docs still get a complete fallback contract."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "growth-graph.md"
            path.write_text("# no contract yet\n", encoding="utf-8")

            contract = growth_graph_contract(path)

        self.assertEqual(contract["layers"][0]["id"], "direction")
        self.assertTrue(any(row["id"] == "health" for row in contract["node_types"]))
        self.assertTrue(any(row["id"] == "watches" for row in contract["edge_types"]))


if __name__ == "__main__":
    unittest.main()
