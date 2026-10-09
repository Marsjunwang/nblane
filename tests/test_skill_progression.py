"""Unit tests for core.skill_progression (tunable rung-up math)."""

from __future__ import annotations

import unittest

from nblane.core.models import EvidencePool
from nblane.core import skill_progression as sp


def _pool(*rows: dict) -> EvidencePool:
    # Rows default to reviewed: only human-confirmed evidence scores.
    entries = [{"review_status": "reviewed", **row} for row in rows]
    return EvidencePool.from_dict(
        {"profile": "alice", "evidence_entries": entries}
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

    def test_unreviewed_rows_do_not_score(self) -> None:
        pool = _pool(
            {"id": "ev_r", "type": "practice", "title": "R", "strength": "medium"},
            {"id": "ev_n", "type": "practice", "title": "N", "strength": "strong",
             "review_status": "needs_review", "breakthrough": True},
            {"id": "ev_e", "type": "practice", "title": "E", "strength": "strong",
             "review_status": ""},
        )
        node = {"id": "n", "status": "locked",
                "evidence_refs": ["ev_r", "ev_n", "ev_e"]}
        progress = sp.node_progress(node, pool)
        self.assertEqual(progress.score, 10)
        self.assertEqual(progress.breakthrough_count, 0)
        # The switch restores the old count-everything behavior.
        loose = sp.node_progress(
            node, pool, sp.ProgressionRules(reviewed_only=False)
        )
        self.assertEqual(loose.score, 10 + 100 + sp.BREAKTHROUGH_WEIGHT + 100)
        self.assertEqual(loose.breakthrough_count, 1)

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
        rules = sp.ProgressionRules()
        rules.thresholds["learning"] = 5000
        progress = sp.node_progress(node, pool, rules)
        self.assertLess(progress.score, progress.threshold_next)
        self.assertTrue(progress.eligible)
        # The switch turns the landmark shortcut off.
        rules.breakthrough_unlocks = False
        self.assertFalse(sp.node_progress(node, pool, rules).eligible)

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


class TestConfigurableRules(unittest.TestCase):
    """Per-profile rules from web-preferences.yaml (skill_progression)."""

    def test_defaults_match_constants(self) -> None:
        rules = sp.normalize_rules(None)
        self.assertEqual(rules["weights"], {"weak": 1, "medium": 10, "strong": 100})
        self.assertEqual(rules["breakthrough_bonus"], sp.BREAKTHROUGH_WEIGHT)
        self.assertEqual(
            rules["thresholds"], {"learning": 10, "solid": 30, "expert": 100}
        )
        self.assertTrue(rules["breakthrough_unlocks"])
        self.assertTrue(rules["reviewed_only"])
        self.assertIsNone(sp.rules_error(rules))

    def test_normalize_clamps_and_ignores_junk(self) -> None:
        rules = sp.normalize_rules(
            {
                "weights": {"weak": "3", "medium": -5, "strong": "x", "bogus": 9},
                "breakthrough_bonus": 10**9,
                "thresholds": {"solid": 50},
                "reviewed_only": "false",
                "extra": 1,
            }
        )
        self.assertEqual(rules["weights"], {"weak": 3, "medium": 0, "strong": 100})
        self.assertEqual(rules["breakthrough_bonus"], sp.MAX_RULE_VALUE)
        self.assertEqual(rules["thresholds"]["solid"], 50)
        self.assertFalse(rules["reviewed_only"])
        self.assertNotIn("extra", rules)

    def test_rules_error_requires_climbing_positive_thresholds(self) -> None:
        bad_order = sp.normalize_rules(
            {"thresholds": {"learning": 10, "solid": 10, "expert": 100}}
        )
        self.assertIn("逐级递增", sp.rules_error(bad_order) or "")
        zero = sp.normalize_rules({"thresholds": {"learning": 0}})
        self.assertIn("大于 0", sp.rules_error(zero) or "")

    def test_custom_rules_change_score_and_threshold(self) -> None:
        pool = _pool(
            {"id": "ev_u", "type": "practice", "title": "U"},
            {"id": "ev_h", "type": "paper", "title": "H", "strength": "high_trust"},
        )
        rules = sp.rules_from_preferences(
            {
                "skill_progression": {
                    "weights": {"weak": 2, "medium": 20, "strong": 50},
                    "thresholds": {"learning": 5, "solid": 60, "expert": 200},
                }
            }
        )
        node = {"id": "n", "status": "learning", "evidence_refs": ["ev_u", "ev_h"]}
        progress = sp.node_progress(node, pool, rules)
        # Unrated scores as weak, high_trust as strong.
        self.assertEqual(progress.score, 2 + 50)
        self.assertEqual(progress.threshold_next, 60)
        self.assertFalse(progress.eligible)


if __name__ == "__main__":
    unittest.main()
