"""Tests for gap analysis, router keywords, and analyze options."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from nblane.core import learned_keywords as lk_store
from nblane.core.gap import analyze
from nblane.core.gap_llm_router import RouterOutcome


class TestLearnedRouterPayload(unittest.TestCase):
    """keywords_dict_from_router_payload expands bilingual rows."""

    def test_expands_slash_pairs(self) -> None:
        """Router-style strings split like coaching keywords."""
        raw = {
            "vlm_robot": ["openpi/PI model", "plain"],
        }
        out = lk_store.keywords_dict_from_router_payload(raw)
        self.assertIn("vlm_robot", out)
        self.assertIn("openpi", out["vlm_robot"])
        self.assertIn("PI model", out["vlm_robot"])
        self.assertIn("plain", out["vlm_robot"])


class TestGapAnalyze(unittest.TestCase):
    """analyze() rule / LLM options and explicit path."""

    def test_openpi_matches_via_synonym(self) -> None:
        """openpi synonym links to schema tokens."""
        result = analyze(
            "王军",
            "openpi",
            use_llm_router=False,
        )
        self.assertIsNone(result.error)
        self.assertTrue(len(result.closure) > 0)

    def test_no_roots_when_both_matchers_off(self) -> None:
        """Neither rule nor LLM yields an error."""
        result = analyze(
            "王军",
            "something obscure xyz123",
            use_rule_match=False,
            use_llm_router=False,
        )
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error_key, "no_roots")

    @patch("nblane.core.gap.lk_store.merge")
    @patch("nblane.core.gap_llm_router.route_task_to_nodes")
    def test_llm_router_merges_keywords(
        self, mock_route, mock_merge
    ) -> None:
        """Router calls merge when LLM returns ids and keywords."""
        mock_route.return_value = RouterOutcome(
            ok=True,
            node_ids=["linux_basics"],
            keywords={
                "linux_basics": ["router_kw/test"],
            },
        )
        result = analyze(
            "王军",
            "custom router task",
            use_rule_match=False,
            use_llm_router=True,
        )
        self.assertIsNone(result.error)
        self.assertTrue(result.learned_merged)
        self.assertIn("linux_basics", result.roots_from_llm)
        mock_merge.assert_called_once()
        call_kw = mock_merge.call_args[0][1]
        self.assertIn("linux_basics", call_kw)


if __name__ == "__main__":
    unittest.main()
