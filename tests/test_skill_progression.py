"""Unit tests for core.skill_progression (tunable rung-up math)."""

from __future__ import annotations

import unittest

from nblane.core.models import EvidencePool
from nblane.core import skill_progression as sp


def _pool(*rows: dict) -> EvidencePool:
    return EvidencePool.from_dict(
        {"profile": "alice", "evidence_entries": list(rows)}
    )


class TestWeights(unittest.TestCase):
    """弱/中/强 = 1/10/100, breakthrough adds 1000, unrated defaults to 1."""

    def test_strength_weights(self) -> None:
        pool = _pool(
            {"id": "ev_w", "type": "practice", "title": "W", "strength": "weak"},
            {"id": "ev_m", "type": "practice", "title": "M", "strength": "medium"},
            {"id": "ev_s", "type": "practice", "title": "S", "strength": "strong"},
        )
        node = {"id": "n", "status": "locked",
                "evidence_refs": ["ev_w", "ev_m", "ev_s"]}
        progress = sp.node_progress(node, pool)
        self.assertEqual(progress.score, 1 + 10 + 100)

    def test_breakthrough_adds_thousand(self) -> None:
        pool = _pool(
            {
                "id": "ev_b",
                "type": "project",
                "title": "B",
                "strength": "strong",
                "breakthrough": True,
            }
        )
        node = {"id": "n", "status": "locked", "evidence_refs": ["ev_b"]}
        progress = sp.node_progress(node, pool)
        self.assertEqual(progress.score, 100 + sp.BREAKTHROUGH_WEIGHT)
        self.assertEqual(progress.breakthrough_count, 1)

    def test_unrated_and_high_trust_fallbacks(self) -> None:
        pool = _pool(
            {"id": "ev_u", "type": "practice", "title": "U"},
            {"id": "ev_h", "type": "paper", "title": "H", "strength": "high_trust"},
        )
        node = {"id": "n", "status": "locked",
                "evidence_refs": ["ev_u", "ev_h"]}
        progress = sp.node_progress(node, pool)
        self.assertEqual(progress.score, sp.DEFAULT_STRENGTH_WEIGHT + 100)

    def test_deprecated_missing_and_duplicate_refs_skipped(self) -> None:
        pool = _pool(
            {"id": "ev_a", "type": "practice", "title": "A", "strength": "medium"},
            {"id": "ev_d", "type": "practice", "title": "D",
             "strength": "strong", "deprecated": True},
        )
        node = {
            "id": "n",
            "status": "locked",
            "evidence_refs": ["ev_a", "ev_a", "ev_d", "ev_missing", " "],
        }
        progress = sp.node_progress(node, pool)
        self.assertEqual(progress.score, 10)

    def test_no_pool_scores_zero(self) -> None:
        node = {"id": "n", "status": "locked", "evidence_refs": ["ev_a"]}
        progress = sp.node_progress(node, None)
        self.assertEqual(progress.score, 0)
        self.assertEqual(progress.breakthrough_count, 0)


class TestRungsAndThresholds(unittest.TestCase):
    """Rung ladder and locked/learning/solid thresholds; expert tops out."""

    def test_next_rung_ladder(self) -> None:
        self.assertEqual(sp.next_rung("locked"), "learning")
        self.assertEqual(sp.next_rung("learning"), "solid")
        self.assertEqual(sp.next_rung("solid"), "expert")
        self.assertIsNone(sp.next_rung("expert"))
        # Unknown statuses behave as locked.
        self.assertEqual(sp.next_rung(""), "learning")
        self.assertEqual(sp.next_rung("bogus"), "learning")

    def test_thresholds(self) -> None:
        self.assertEqual(sp.threshold_for_next("locked"), 10)
        self.assertEqual(sp.threshold_for_next("learning"), 30)
        self.assertEqual(sp.threshold_for_next("solid"), 100)
        self.assertIsNone(sp.threshold_for_next("expert"))

    def test_expert_node_progress(self) -> None:
        pool = _pool(
            {"id": "ev_b", "type": "project", "title": "B",
             "strength": "strong", "breakthrough": True},
        )
        node = {"id": "n", "status": "expert", "evidence_refs": ["ev_b"]}
        progress = sp.node_progress(node, pool)
        self.assertIsNone(progress.next_rung)
        self.assertIsNone(progress.threshold_next)
        # No next rung: never eligible, however strong the evidence.
        self.assertFalse(progress.eligible)


class TestEligible(unittest.TestCase):
    """eligible = score >= threshold_next OR breakthrough_count >= 1."""

    def test_score_threshold_met(self) -> None:
        pool = _pool(
            {"id": "ev_m", "type": "practice", "title": "M", "strength": "medium"},
        )
        node = {"id": "n", "status": "locked", "evidence_refs": ["ev_m"]}
        progress = sp.node_progress(node, pool)
        self.assertEqual(progress.score, 10)
        self.assertEqual(progress.threshold_next, 10)
        self.assertTrue(progress.eligible)

    def test_score_below_threshold_not_eligible(self) -> None:
        pool = _pool(
            {"id": "ev_w", "type": "practice", "title": "W", "strength": "weak"},
        )
        node = {"id": "n", "status": "locked", "evidence_refs": ["ev_w"]}
        self.assertFalse(sp.node_progress(node, pool).eligible)

    def test_single_breakthrough_unlocks_eligibility(self) -> None:
        pool = _pool(
            {"id": "ev_b", "type": "project", "title": "B",
             "strength": "weak", "breakthrough": True},
        )
        node = {"id": "n", "status": "solid", "evidence_refs": ["ev_b"]}
        progress = sp.node_progress(node, pool)
        self.assertEqual(progress.breakthrough_count, 1)
        self.assertTrue(progress.eligible)
        # Same shape on expert: no next rung -> not eligible.
        node_expert = {"id": "n", "status": "expert", "evidence_refs": ["ev_b"]}
        self.assertFalse(sp.node_progress(node_expert, pool).eligible)

    def test_breakthrough_clause_independent_of_score(self) -> None:
        # The breakthrough OR clause matters when thresholds are tuned
        # above BREAKTHROUGH_WEIGHT: eligible stays true on the landmark
        # alone. Constants are the tuning surface, so exercise that path.
        pool = _pool(
            {"id": "ev_b", "type": "project", "title": "B",
             "strength": "weak", "breakthrough": True},
        )
        node = {"id": "n", "status": "locked", "evidence_refs": ["ev_b"]}
        original = dict(sp.RUNG_THRESHOLDS)
        self.addCleanup(sp.RUNG_THRESHOLDS.update, original)
        sp.RUNG_THRESHOLDS[("locked", "learning")] = 5000
        progress = sp.node_progress(node, pool)
        self.assertLess(progress.score, progress.threshold_next)
        self.assertTrue(progress.eligible)

    def test_to_dict_shape(self) -> None:
        node = {"id": "n", "status": "learning"}
        payload = sp.node_progress(node, None).to_dict()
        self.assertEqual(
            payload,
            {
                "score": 0,
                "next_rung": "solid",
                "threshold_next": 30,
                "breakthrough_count": 0,
                "eligible": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
