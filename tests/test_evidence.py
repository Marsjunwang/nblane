"""Tests for skill evidence (models, gap output, validation)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from nblane.core.evidence_resolve import (
    resolve_node_evidence_dict,
    resolved_evidence_count,
)
from nblane.core.gap import format_text
from nblane.core.models import (
    EVIDENCE_TYPES,
    EvidencePool,
    SkillNode,
    SkillTree,
)
from nblane.core.validate import validate_one


class TestEvidenceModel(unittest.TestCase):
    """SkillNode and Evidence YAML mapping."""

    def test_round_trip_dict(self) -> None:
        """to_dict / from_dict preserves evidence lists."""
        raw = {
            "id": "ros2_basics",
            "status": "solid",
            "note": "ok",
            "evidence": [
                {
                    "type": "project",
                    "title": "Bringup",
                    "date": "2026-01",
                    "summary": "Done",
                }
            ],
        }
        node = SkillNode.from_dict(raw)
        self.assertEqual(len(node.evidence), 1)
        self.assertEqual(node.evidence[0].type, "project")
        self.assertEqual(node.evidence[0].title, "Bringup")
        back = node.to_dict()
        self.assertEqual(back["id"], "ros2_basics")
        self.assertEqual(len(back["evidence"]), 1)

    def test_empty_evidence_omitted(self) -> None:
        """Nodes without evidence omit the key in YAML dict."""
        node = SkillNode(id="x", status="locked")
        d = node.to_dict()
        self.assertNotIn("evidence", d)
        self.assertNotIn("evidence_refs", d)

    def test_evidence_refs_round_trip(self) -> None:
        """evidence_refs survives dict serialization."""
        raw = {
            "id": "n1",
            "status": "solid",
            "evidence_refs": ["proj_a", "proj_a", "proj_b"],
            "evidence": [
                {"type": "practice", "title": "Inline"},
            ],
        }
        node = SkillNode.from_dict(raw)
        self.assertEqual(node.evidence_refs, ["proj_a", "proj_b"])
        back = node.to_dict()
        self.assertEqual(
            back["evidence_refs"],
            ["proj_a", "proj_b"],
        )

    def test_evidence_types_constant(self) -> None:
        """Expected taxonomy is stable."""
        self.assertEqual(
            EVIDENCE_TYPES,
            frozenset(
                {"project", "paper", "course", "practice"}
            ),
        )


class TestEvidenceValidate(unittest.TestCase):
    """validate_one warns on bad evidence rows."""

    def test_unknown_evidence_ref_errors(self) -> None:
        """Missing pool id for evidence_refs is an error."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            pool = {
                "profile": "t",
                "evidence_entries": [
                    {"id": "only", "type": "project", "title": "X"},
                ],
            }
            (p / "evidence-pool.yaml").write_text(
                yaml.dump(
                    pool,
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            tree = {
                "profile": "t",
                "schema": "robotics-engineer",
                "updated": "2026-01-01",
                "nodes": [
                    {
                        "id": "ros2_basics",
                        "status": "solid",
                        "evidence_refs": ["ghost_id"],
                    }
                ],
            }
            (p / "skill-tree.yaml").write_text(
                yaml.dump(
                    tree,
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            err, warn = validate_one(p)
            self.assertTrue(
                any("ghost_id" in e for e in err),
            )

    def test_unknown_type_and_empty_title(self) -> None:
        """Illegal type and blank title produce warnings."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            tree = {
                "profile": "t",
                "schema": "robotics-engineer",
                "updated": "2026-01-01",
                "nodes": [
                    {
                        "id": "ros2_basics",
                        "status": "solid",
                        "evidence": [
                            {
                                "type": "invalid_kind",
                                "title": " ",
                            },
                            {
                                "type": "project",
                                "title": "",
                            },
                        ],
                    }
                ],
            }
            (p / "skill-tree.yaml").write_text(
                yaml.dump(
                    tree,
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            err, warn = validate_one(p)
            self.assertEqual(err, [])
            self.assertTrue(
                any("unknown type" in w for w in warn)
            )
            self.assertTrue(
                any("empty title" in w for w in warn)
            )


class TestEvidenceResolve(unittest.TestCase):
    """Pool refs plus inline materialization."""

    def test_refs_then_inline(self) -> None:
        """Refs resolve first; duplicate ref ids dedupe."""
        pool = EvidencePool.from_dict(
            {
                "profile": "p",
                "evidence_entries": [
                    {
                        "id": "a",
                        "type": "project",
                        "title": "Shared",
                    },
                ],
            }
        )
        node = {
            "evidence_refs": ["a", "a"],
            "evidence": [
                {"type": "paper", "title": "Only inline"},
            ],
        }
        got = resolve_node_evidence_dict(node, pool)
        self.assertEqual(len(got), 2)
        self.assertEqual(got[0].title, "Shared")
        self.assertEqual(got[1].title, "Only inline")

    def test_count_matches_resolve(self) -> None:
        """resolved_evidence_count matches list length."""
        pool = EvidencePool.from_dict(
            {
                "evidence_entries": [
                    {"id": "x", "type": "course", "title": "C"},
                ],
            }
        )
        node = {
            "evidence_refs": ["x"],
            "evidence": [],
        }
        self.assertEqual(
            resolved_evidence_count(node, pool),
            1,
        )

    def test_deprecated_pool_row_skipped(self) -> None:
        """Deprecated pool records do not materialize."""
        pool = EvidencePool.from_dict(
            {
                "evidence_entries": [
                    {
                        "id": "old",
                        "type": "project",
                        "title": "Retired",
                        "deprecated": True,
                    },
                    {
                        "id": "new",
                        "type": "project",
                        "title": "Active",
                    },
                ],
            }
        )
        node = {
            "evidence_refs": ["old", "new"],
            "evidence": [],
        }
        got = resolve_node_evidence_dict(node, pool)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0].title, "Active")


class TestGapEvidenceFormatting(unittest.TestCase):
    """CLI gap output includes evidence counts."""

    def test_closure_line_shows_count(self) -> None:
        """format_text annotates status with evidence count."""
        from nblane.core.models import GapResult

        result = GapResult(
            task="demo",
            top_matches=[],
            closure=[
                {
                    "id": "n1",
                    "label": "L1",
                    "status": "solid",
                    "is_gap": False,
                    "evidence_count": 3,
                }
            ],
            gaps=[],
            strong=["n1"],
            can_solve=True,
        )
        text = format_text(result)
        self.assertIn("solid (3 evidence)", text)


class TestSkillTreeEvidence(unittest.TestCase):
    """SkillTree aggregates nodes with evidence."""

    def test_from_dict_skips_non_dict_evidence(self) -> None:
        """Malformed list entries are ignored."""
        raw = {
            "profile": "p",
            "schema": "robotics-engineer",
            "nodes": [
                {
                    "id": "a",
                    "status": "expert",
                    "evidence": ["bad", {"type": "paper", "title": "T"}],
                }
            ],
        }
        tree = SkillTree.from_dict(raw)
        self.assertEqual(len(tree.nodes[0].evidence), 1)
        self.assertEqual(tree.nodes[0].evidence[0].title, "T")


if __name__ == "__main__":
    unittest.main()
