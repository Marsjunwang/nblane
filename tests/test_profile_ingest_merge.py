"""Tests for profile ingest merge (no LLM)."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date as date_cls
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.profile_ingest import (
    filter_ingest_patch,
    ingest_preview_delta,
    merge_ingest_patch,
    parse_ingest_patch,
    run_ingest_patch,
)
from nblane.core.validate import validate_one


class TestIngestPreviewDelta(unittest.TestCase):
    """ingest_preview_delta lists new evidence and tree field changes."""

    def test_new_evidence_and_status_change(self) -> None:
        """Detects new pool row and status/refs delta."""
        pool_before = {
            "profile": "t",
            "evidence_entries": [
                {"id": "e1", "type": "project", "title": "Old"},
            ],
        }
        tree_before = {
            "profile": "t",
            "schema": "robotics-engineer",
            "nodes": [
                {
                    "id": "ros2_basics",
                    "status": "locked",
                    "evidence_refs": ["e1"],
                },
            ],
        }
        merged_pool = {
            "profile": "t",
            "evidence_entries": [
                {"id": "e1", "type": "project", "title": "Old"},
                {"id": "e2", "type": "paper", "title": "New paper"},
            ],
        }
        merged_tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "nodes": [
                {
                    "id": "ros2_basics",
                    "status": "learning",
                    "evidence_refs": ["e1", "e2"],
                },
            ],
        }
        labels = {"ros2_basics": "ROS2 基础"}
        new_ev, tree_ch = ingest_preview_delta(
            pool_before,
            tree_before,
            merged_pool,
            merged_tree,
            labels,
        )
        self.assertTrue(any("e2" in x for x in new_ev))
        self.assertTrue(
            any("status" in x and "ros2_basics" in x for x in tree_ch),
        )


class TestParseIngestPatch(unittest.TestCase):
    """parse_ingest_patch coerces shapes."""

    def test_empty(self) -> None:
        """Non-dicts become empty patch."""
        p = parse_ingest_patch(None)
        self.assertEqual(p.evidence_entries, [])
        self.assertEqual(p.node_updates, [])
        self.assertEqual(p.skipped_tasks, [])

    def test_round_trip_keys(self) -> None:
        """Preserves list entries."""
        raw = {
            "evidence_entries": [
                {
                    "type": "project",
                    "title": "A",
                    "project_refs": ["project:demo"],
                },
            ],
            "node_updates": [
                {"id": "n1", "evidence_refs": ["x"]},
            ],
        }
        p = parse_ingest_patch(raw)
        self.assertEqual(len(p.evidence_entries), 1)
        self.assertEqual(len(p.node_updates), 1)
        self.assertEqual(
            p.evidence_entries[0]["project_refs"],
            ["project:demo"],
        )

    def test_skipped_tasks_are_preserved(self) -> None:
        """Done AI skip explanations are parsed but not merged as evidence."""
        raw = {
            "skipped_tasks": [
                {
                    "task_id": "kb_1",
                    "reason": "not_evidence",
                    "detail": "Housekeeping only.",
                },
                "ignore me",
            ],
        }

        p = parse_ingest_patch(raw)

        self.assertEqual(
            p.skipped_tasks,
            [
                {
                    "task_id": "kb_1",
                    "reason": "not_evidence",
                    "detail": "Housekeeping only.",
                }
            ],
        )

    def test_node_update_id_aliases_are_normalized(self) -> None:
        """LLM node_id aliases become the canonical id field."""
        raw = {
            "node_updates": [
                {
                    "node_id": "ros2_basics",
                    "evidence_refs": ["first_1"],
                },
                {
                    "id": "",
                    "skill_id": "experiment_design",
                    "evidence_refs": ["ev_demo"],
                },
            ],
        }

        p = parse_ingest_patch(raw)

        self.assertEqual(p.node_updates[0]["id"], "ros2_basics")
        self.assertEqual(p.node_updates[1]["id"], "experiment_design")


class TestMergeIngestPatch(unittest.TestCase):
    """merge_ingest_patch updates pool then tree."""

    def test_adds_pool_and_refs(self) -> None:
        """New evidence row and node ref."""
        pool = {
            "profile": "t",
            "evidence_entries": [],
        }
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [
                {"id": "ros2_basics", "status": "locked"},
            ],
        }
        patch = {
            "evidence_entries": [
                {
                    "id": "e_demo_1",
                    "type": "project",
                    "title": "Bringup demo",
                    "date": "2026-03",
                }
            ],
            "node_updates": [
                {
                    "id": "ros2_basics",
                    "evidence_refs": ["e_demo_1"],
                }
            ],
        }
        m = merge_ingest_patch("t", pool, tree, patch)
        self.assertTrue(m.ok)
        assert m.merged_pool is not None
        assert m.merged_tree is not None
        entries = m.merged_pool.get("evidence_entries") or []
        self.assertEqual(len(entries), 1)
        eid = entries[0].get("id")
        self.assertTrue(eid)
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        refs = n0.get("evidence_refs") or []
        self.assertIn(eid, refs)

    def test_first_n_placeholder_resolves(self) -> None:
        """LLM-style first_1 maps to 1st evidence_entries row final id."""
        pool = {
            "profile": "t",
            "evidence_entries": [],
        }
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [
                {"id": "ros2_basics", "status": "locked"},
            ],
        }
        patch = {
            "evidence_entries": [
                {
                    "type": "project",
                    "title": "Bringup demo",
                    "date": "2026-03",
                }
            ],
            "node_updates": [
                {
                    "id": "ros2_basics",
                    "evidence_refs": ["first_1"],
                }
            ],
        }
        m = merge_ingest_patch("t", pool, tree, patch)
        self.assertTrue(m.ok)
        assert m.merged_pool is not None
        assert m.merged_tree is not None
        eid = m.merged_pool["evidence_entries"][0].get("id")
        self.assertTrue(eid)
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        refs = n0.get("evidence_refs") or []
        self.assertIn(eid, refs)
        self.assertFalse(
            any("dropped" in w for w in m.warnings),
            msg=m.warnings,
        )

    def test_kanban_task_id_ref_gets_actionable_diagnostic(self) -> None:
        """A kb_*/kanban:<id> ref in node_updates is dropped with guidance."""
        pool = {"profile": "t", "evidence_entries": []}
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [{"id": "ros2_basics", "status": "locked"}],
        }
        patch = {
            "evidence_entries": [
                {"type": "project", "title": "Bringup demo", "date": "2026-03"}
            ],
            "node_updates": [
                {
                    "id": "ros2_basics",
                    "evidence_refs": ["kb_done_ship", "kanban:done_demo", "first_1"],
                }
            ],
        }
        m = merge_ingest_patch("t", pool, tree, patch)
        self.assertTrue(m.ok)
        assert m.merged_tree is not None
        # The valid placeholder still resolves; the Kanban ids are dropped.
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        refs = n0.get("evidence_refs") or []
        self.assertNotIn("kb_done_ship", refs)
        self.assertNotIn("kanban:done_demo", refs)
        kb_warnings = [w for w in m.warnings if "Kanban task id" in w]
        self.assertEqual(len(kb_warnings), 2, msg=m.warnings)
        self.assertTrue(all("kanban_refs" in w for w in kb_warnings))
        """LLM node_id aliases are merged instead of skipped."""
        pool = {
            "profile": "t",
            "evidence_entries": [],
        }
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [
                {"id": "ros2_basics", "status": "locked"},
            ],
        }
        patch = {
            "evidence_entries": [
                {
                    "type": "project",
                    "title": "Bringup demo",
                    "date": "2026-03",
                }
            ],
            "node_updates": [
                {
                    "node_id": "ros2_basics",
                    "evidence_refs": ["first_1"],
                    "status": "learning",
                }
            ],
        }

        m = merge_ingest_patch(
            "t",
            pool,
            tree,
            patch,
            allow_status_change=True,
        )

        self.assertTrue(m.ok)
        assert m.merged_pool is not None
        assert m.merged_tree is not None
        eid = m.merged_pool["evidence_entries"][0].get("id")
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        self.assertIn(eid, n0.get("evidence_refs") or [])
        self.assertEqual(n0.get("status"), "learning")
        self.assertFalse(
            any("without id" in w for w in m.warnings),
            msg=m.warnings,
        )

    def test_evidence_review_metadata_survives_merge(self) -> None:
        """Ingest merge preserves supported evidence review metadata."""
        pool = {
            "profile": "t",
            "evidence_entries": [],
        }
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [
                {"id": "ros2_basics", "status": "locked"},
            ],
        }
        patch = {
            "evidence_entries": [
                {
                    "type": "project",
                    "title": "Reviewed demo",
                    "strength": "medium",
                    "confidence": "high",
                    "review_status": "reviewed",
                    "public_readiness": "draftable",
                    "source_refs": ["kanban:done_ship"],
                }
            ],
            "node_updates": [
                {
                    "id": "ros2_basics",
                    "evidence_refs": ["first_1"],
                }
            ],
        }

        merged = merge_ingest_patch("t", pool, tree, patch)

        self.assertTrue(merged.ok)
        assert merged.merged_pool is not None
        row = merged.merged_pool["evidence_entries"][0]
        self.assertEqual(row["strength"], "medium")
        self.assertEqual(row["confidence"], "high")
        self.assertEqual(row["review_status"], "reviewed")
        self.assertEqual(row["public_readiness"], "draftable")
        self.assertEqual(row["source_refs"], ["kanban:done_ship"])

    def test_out_of_domain_strength_is_dropped(self) -> None:
        """Parser whitelist drops bad strength so a human refills it.

        The kanban prompt now asks the model to pre-grade strength; this is
        the safety net that keeps an out-of-range value (e.g. a hallucinated
        grade) from polluting the pool.
        """
        pool = {"profile": "t", "evidence_entries": []}
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [{"id": "ros2_basics", "status": "locked"}],
        }
        patch = {
            "evidence_entries": [
                {
                    "type": "project",
                    "title": "Graded demo",
                    "strength": "legendary",  # not in EVIDENCE_STRENGTHS
                    "confidence": "high",
                }
            ],
            "node_updates": [{"id": "ros2_basics", "evidence_refs": ["first_1"]}],
        }

        merged = merge_ingest_patch("t", pool, tree, patch)

        self.assertTrue(merged.ok)
        assert merged.merged_pool is not None
        row = merged.merged_pool["evidence_entries"][0]
        self.assertNotIn("strength", row)
        self.assertEqual(row["confidence"], "high")

    def test_status_ignored_by_default(self) -> None:
        """status in patch is ignored unless allow_status_change."""
        pool = {
            "profile": "t",
            "evidence_entries": [],
        }
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [
                {"id": "ros2_basics", "status": "locked"},
            ],
        }
        patch = {
            "evidence_entries": [],
            "node_updates": [
                {"id": "ros2_basics", "status": "solid"},
            ],
        }
        m = merge_ingest_patch(
            "t", pool, tree, patch, allow_status_change=False
        )
        self.assertTrue(m.ok)
        assert m.merged_tree is not None
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        self.assertEqual(n0.get("status"), "locked")

    def test_status_applied_when_allowed(self) -> None:
        """allow_status_change writes status."""
        pool = {
            "profile": "t",
            "evidence_entries": [],
        }
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [
                {"id": "ros2_basics", "status": "locked"},
            ],
        }
        patch = {
            "evidence_entries": [],
            "node_updates": [
                {"id": "ros2_basics", "status": "solid"},
            ],
        }
        m = merge_ingest_patch(
            "t", pool, tree, patch, allow_status_change=True
        )
        self.assertTrue(m.ok)
        assert m.merged_tree is not None
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        self.assertEqual(n0.get("status"), "solid")

    def test_expert_preserved_when_llm_suggests_other_status(self) -> None:
        """Human expert in tree is not overwritten by LLM learning/solid."""
        pool = {
            "profile": "t",
            "evidence_entries": [],
        }
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [
                {"id": "ros2_basics", "status": "expert"},
            ],
        }
        patch = {
            "evidence_entries": [],
            "node_updates": [
                {"id": "ros2_basics", "status": "learning"},
            ],
        }
        m = merge_ingest_patch(
            "t", pool, tree, patch, allow_status_change=True
        )
        self.assertTrue(m.ok)
        assert m.merged_tree is not None
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        self.assertEqual(n0.get("status"), "expert")
        self.assertTrue(
            any("preserved expert" in w for w in m.warnings),
            msg=m.warnings,
        )

    def test_solid_preserved_when_llm_suggests_learning(self) -> None:
        """Ingest does not downgrade solid to learning."""
        pool = {
            "profile": "t",
            "evidence_entries": [],
        }
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [
                {"id": "ros2_basics", "status": "solid"},
            ],
        }
        patch = {
            "evidence_entries": [],
            "node_updates": [
                {"id": "ros2_basics", "status": "learning"},
            ],
        }
        m = merge_ingest_patch(
            "t", pool, tree, patch, allow_status_change=True
        )
        self.assertTrue(m.ok)
        assert m.merged_tree is not None
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        self.assertEqual(n0.get("status"), "solid")
        self.assertTrue(
            any("ingest only upgrades" in w for w in m.warnings),
            msg=m.warnings,
        )

    def test_learning_upgrades_to_solid_when_llm_suggests(self) -> None:
        """LLM solid upgrades learning."""
        pool = {"profile": "t", "evidence_entries": []}
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [
                {"id": "ros2_basics", "status": "learning"},
            ],
        }
        patch = {
            "evidence_entries": [],
            "node_updates": [
                {"id": "ros2_basics", "status": "solid"},
            ],
        }
        m = merge_ingest_patch(
            "t", pool, tree, patch, allow_status_change=True
        )
        self.assertTrue(m.ok)
        assert m.merged_tree is not None
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        self.assertEqual(n0.get("status"), "solid")

    def test_validate_passes_after_merge(self) -> None:
        """Merged dicts validate under temp profile dir."""
        pool = {
            "profile": "t",
            "evidence_entries": [],
        }
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [
                {"id": "ros2_basics", "status": "locked"},
            ],
        }
        patch = {
            "evidence_entries": [
                {
                    "id": "e_ex_1",
                    "type": "practice",
                    "title": "Exercise",
                }
            ],
            "node_updates": [
                {
                    "id": "ros2_basics",
                    "evidence_refs": ["e_ex_1"],
                }
            ],
        }
        m = merge_ingest_patch("t", pool, tree, patch)
        self.assertTrue(m.ok)
        assert m.merged_pool is not None
        assert m.merged_tree is not None
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "evidence-pool.yaml").write_text(
                yaml.dump(
                    m.merged_pool,
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (p / "skill-tree.yaml").write_text(
                yaml.dump(
                    m.merged_tree,
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            err, _warn = validate_one(p)
            self.assertEqual(err, [])

    def test_merged_updated_iso_today(self) -> None:
        """merged pool and tree get updated == date.today().isoformat()."""
        pool = {"profile": "t", "evidence_entries": []}
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "{YYYY-MM-DD}",
            "nodes": [{"id": "ros2_basics", "status": "locked"}],
        }
        ingest = {
            "evidence_entries": [
                {"id": "z1", "type": "project", "title": "P"},
            ],
            "node_updates": [],
        }
        fixed = date_cls(2031, 8, 20)
        with patch(
            "nblane.core.profile_ingest.date"
        ) as mock_date:
            mock_date.today.return_value = fixed
            m = merge_ingest_patch("t", pool, tree, ingest)
        self.assertTrue(m.ok)
        assert m.merged_pool is not None
        assert m.merged_tree is not None
        self.assertEqual(
            m.merged_pool.get("updated"),
            "2031-08-20",
        )
        self.assertEqual(
            m.merged_tree.get("updated"),
            "2031-08-20",
        )

    def test_bump_locked_to_learning(self) -> None:
        """locked + evidence_refs becomes learning when bump on."""
        pool = {"profile": "t", "evidence_entries": []}
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [{"id": "ros2_basics", "status": "locked"}],
        }
        patch = {
            "evidence_entries": [
                {"id": "b1", "type": "project", "title": "P"},
            ],
            "node_updates": [
                {"id": "ros2_basics", "evidence_refs": ["b1"]},
            ],
        }
        m = merge_ingest_patch(
            "t",
            pool,
            tree,
            patch,
            allow_status_change=False,
            bump_locked_with_evidence=True,
        )
        self.assertTrue(m.ok)
        assert m.merged_tree is not None
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        self.assertEqual(n0.get("status"), "learning")

    def test_bump_disabled_keeps_locked(self) -> None:
        """bump_locked_with_evidence False leaves locked."""
        pool = {"profile": "t", "evidence_entries": []}
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [{"id": "ros2_basics", "status": "locked"}],
        }
        patch = {
            "evidence_entries": [
                {"id": "b1", "type": "project", "title": "P"},
            ],
            "node_updates": [
                {"id": "ros2_basics", "evidence_refs": ["b1"]},
            ],
        }
        m = merge_ingest_patch(
            "t",
            pool,
            tree,
            patch,
            bump_locked_with_evidence=False,
        )
        self.assertTrue(m.ok)
        assert m.merged_tree is not None
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        self.assertEqual(n0.get("status"), "locked")

    def test_expert_downgraded_to_learning(self) -> None:
        """LLM expert status becomes learning with warning."""
        pool = {"profile": "t", "evidence_entries": []}
        tree = {
            "profile": "t",
            "schema": "robotics-engineer",
            "updated": "2026-01-01",
            "nodes": [{"id": "ros2_basics", "status": "locked"}],
        }
        patch = {
            "evidence_entries": [],
            "node_updates": [
                {"id": "ros2_basics", "status": "expert"},
            ],
        }
        m = merge_ingest_patch(
            "t",
            pool,
            tree,
            patch,
            allow_status_change=True,
            bump_locked_with_evidence=False,
        )
        self.assertTrue(m.ok)
        assert m.merged_tree is not None
        nodes = m.merged_tree.get("nodes") or []
        n0 = next(x for x in nodes if x.get("id") == "ros2_basics")
        self.assertEqual(n0.get("status"), "learning")
        self.assertTrue(
            any("expert" in w.lower() for w in m.warnings),
        )


class TestRunIngestPatchDryRun(unittest.TestCase):
    """run_ingest_patch does not write when dry_run."""

    def test_dry_run_no_files(self) -> None:
        """Profile dir unchanged on dry run."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            prof = base / "dryuser"
            prof.mkdir()
            pool = {
                "profile": "dryuser",
                "evidence_entries": [],
            }
            tree = {
                "profile": "dryuser",
                "schema": "robotics-engineer",
                "updated": "2026-01-01",
                "nodes": [
                    {"id": "ros2_basics", "status": "locked"},
                ],
            }
            (prof / "evidence-pool.yaml").write_text(
                yaml.dump(pool, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            (prof / "skill-tree.yaml").write_text(
                yaml.dump(tree, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            before_pool = (prof / "evidence-pool.yaml").read_text()

            ingest = {
                "evidence_entries": [
                    {"type": "project", "title": "X", "id": "fixed_id"},
                ],
                "node_updates": [
                    {"id": "ros2_basics", "evidence_refs": ["fixed_id"]},
                ],
            }

            with patch(
                "nblane.core.io.profile_dir",
                lambda _n: prof,
            ):
                merge, apply = run_ingest_patch(
                    "dryuser",
                    ingest,
                    dry_run=True,
                )

            self.assertTrue(merge.ok)
            self.assertTrue(apply.ok)
            self.assertTrue(apply.dry_run)
            after_pool = (prof / "evidence-pool.yaml").read_text()
            self.assertEqual(before_pool, after_pool)


class TestFilterIngestPatch(unittest.TestCase):
    """Selective ingest rows remap first_N ordinals."""

    def test_remaps_ordinal_when_subset(self) -> None:
        """Keeping only row 2 turns first_2 into first_1."""
        raw = {
            "evidence_entries": [
                {"id": "a", "title": "A"},
                {"id": "b", "title": "B"},
            ],
            "node_updates": [
                {"id": "n1", "evidence_refs": ["first_2"]},
            ],
        }
        fp, _warn = filter_ingest_patch(
            raw,
            include_evidence=[False, True],
            include_nodes=None,
        )
        self.assertEqual(len(fp.evidence_entries), 1)
        self.assertEqual(fp.evidence_entries[0]["id"], "b")
        self.assertEqual(
            fp.node_updates[0].get("evidence_refs"),
            ["first_1"],
        )

    def test_drops_excluded_ordinal_with_warning(self) -> None:
        """Excluding the only evidence row drops first_1 ref."""
        raw = {
            "evidence_entries": [
                {"id": "a", "title": "A"},
            ],
            "node_updates": [
                {"id": "n1", "evidence_refs": ["first_1"]},
            ],
        }
        fp, warn = filter_ingest_patch(
            raw,
            include_evidence=[False],
            include_nodes=None,
        )
        self.assertEqual(len(fp.evidence_entries), 0)
        self.assertIsNone(fp.node_updates[0].get("evidence_refs"))
        self.assertTrue(any("not selected" in x for x in warn))


if __name__ == "__main__":
    unittest.main()
