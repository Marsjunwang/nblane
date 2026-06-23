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
    growth_graph_node_type_roles,
    growth_graph_node_types,
    growth_graph_roles,
)
from nblane.core.workspace_graph import (
    workspace_graph_edge_types,
    workspace_graph_layers,
    workspace_graph_node_type_roles,
    workspace_graph_node_types,
)


class GrowthGraphContractTests(unittest.TestCase):
    def test_growth_graph_contract_reads_product_doc(self) -> None:
        """The product doc exposes the layer, node, and edge ids used by code."""
        contract = growth_graph_contract()

        self.assertEqual(contract["schema_version"], "1.1")
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

    def test_growth_graph_contract_exposes_star_tree_roles(self) -> None:
        """The 8 visual roles and the type->role map are stable."""
        self.assertEqual(
            list(growth_graph_roles()),
            [
                "trunk",
                "direction",
                "branch",
                "leaf",
                "fruit",
                "star",
                "constellation",
                "sand",
            ],
        )
        roles = growth_graph_node_type_roles()
        self.assertEqual(roles["north_star"], "trunk")
        self.assertEqual(roles["goal"], "direction")
        self.assertEqual(roles["project_case"], "branch")
        self.assertEqual(roles["task"], "leaf")
        self.assertEqual(roles["output"], "leaf")
        self.assertEqual(roles["atomic_evidence"], "fruit")
        self.assertEqual(roles["skill"], "star")
        self.assertEqual(roles["claim"], "constellation")
        self.assertEqual(roles["source"], "sand")
        # The 6 node types that stay out of the star tree map to an empty role.
        for out_of_tree in (
            "health",
            "capacity",
            "gap",
            "next_action",
            "feedback",
            "agent_run",
        ):
            self.assertEqual(roles[out_of_tree], "")

    def test_workspace_graph_uses_growth_graph_contract(self) -> None:
        """Workspace graph helpers delegate to the same contract source."""
        self.assertEqual(workspace_graph_layers(), growth_graph_layers())
        self.assertEqual(workspace_graph_node_types(), growth_graph_node_types())
        self.assertEqual(workspace_graph_edge_types(), growth_graph_edge_types())
        self.assertEqual(
            workspace_graph_node_type_roles(), growth_graph_node_type_roles()
        )

    def test_growth_graph_contract_falls_back_when_doc_block_missing(self) -> None:
        """Old docs still get a complete fallback contract."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "growth-graph.md"
            path.write_text("# no contract yet\n", encoding="utf-8")

            contract = growth_graph_contract(path)

        self.assertEqual(contract["layers"][0]["id"], "direction")
        self.assertTrue(any(row["id"] == "health" for row in contract["node_types"]))
        self.assertTrue(any(row["id"] == "watches" for row in contract["edge_types"]))
        self.assertTrue(any(row["id"] == "star" for row in contract["roles"]))
        skill_row = next(
            row for row in contract["node_types"] if row["id"] == "skill"
        )
        self.assertEqual(skill_row["role"], "star")


if __name__ == "__main__":
    unittest.main()
