"""Tests for core.ai.skill_suggest (embedding / llm / rule tiers)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.ai import skill_suggest

TREE = {
    "profile": "dev",
    "schema": "robotics-engineer",
    "nodes": [{"id": "ros2_basics", "status": "solid"}],
}


def _write_profile(root: Path, name: str = "dev") -> Path:
    pdir = root / name
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "skill-tree.yaml").write_text(
        yaml.safe_dump(dict(TREE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    return pdir


class SkillSuggestTestBase(unittest.TestCase):
    def _patched(self, root: Path) -> None:
        for target in (
            "nblane.core.profile_io.PROFILES_DIR",
            "nblane.core.io.PROFILES_DIR",
        ):
            patcher = patch(target, root)
            self.addCleanup(patcher.stop)
            patcher.start()


class TestRuleTier(SkillSuggestTestBase):
    def test_rule_fallback_without_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            self._patched(root)
            with patch("nblane.core.llm.is_configured", lambda: False):
                out = skill_suggest.suggest_skills_for_text(
                    root / "dev",
                    "Tuned the ROS2 navigation stack with lidar SLAM.",
                )
            self.assertEqual(out["backend"], "rule")
            ids = [s["id"] for s in out["suggestions"]]
            self.assertTrue(ids)
            self.assertLessEqual(len(ids), 5)
            for item in out["suggestions"]:
                self.assertEqual(item["source"], "rule")
                self.assertIn("label", item)
                self.assertIn("category", item)

    def test_empty_text_or_schema_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = _write_profile(root)
            self._patched(root)
            out = skill_suggest.suggest_skills_for_text(pdir, "   ")
            self.assertEqual(out["backend"], "none")
            self.assertEqual(out["suggestions"], [])


class TestLlmTier(SkillSuggestTestBase):
    def test_llm_ranking_used_when_embedding_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_profile(root)
            self._patched(root)
            reply = json.dumps({"skill_ids": ["nav2", "ros2_basics", "nav2"]})
            with patch("nblane.core.llm.is_configured", lambda: True), patch(
                "nblane.core.llm.chat", lambda *a, **k: reply
            ):
                out = skill_suggest.suggest_skills_for_text(
                    root / "dev", "anything", exclude_ids=["ros2_basics"]
                )
            self.assertEqual(out["backend"], "llm")
            # De-duped, excluded ids filtered, catalog-only ids kept.
            self.assertEqual(
                [s["id"] for s in out["suggestions"]], ["nav2"]
            )
            self.assertEqual(out["suggestions"][0]["source"], "llm")


class TestEmbeddingTier(SkillSuggestTestBase):
    def test_embedding_tier_ranks_and_caches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = _write_profile(root)
            self._patched(root)

            calls: list[list[str]] = []

            def fake_embed(texts: list[str]) -> list[list[float]]:
                calls.append(list(texts))
                # 2-D toy vectors: ros2_basics points along x, nav2 along y.
                return [[1.0, 0.0] if "ros2" in t.lower() else [0.0, 1.0]
                        for t in texts]

            with patch.object(skill_suggest, "_embedding_model", lambda: "m0"), \
                patch("nblane.core.llm.is_configured", lambda: True), \
                patch.object(skill_suggest, "_embed_texts", fake_embed):
                out = skill_suggest.suggest_skills_for_text(
                    pdir, "ros2 fundamentals", top_n=3
                )
                self.assertEqual(out["backend"], "embedding")
                self.assertEqual(out["suggestions"][0]["id"], "ros2_basics")
                # Cache file was written; a second call embeds only the query.
                cache = pdir / ".cache" / "skill-embeddings.json"
                self.assertTrue(cache.exists())
                node_calls = sum(len(c) for c in calls)  # nodes + 1 query
                out2 = skill_suggest.suggest_skills_for_text(
                    pdir, "ros2 fundamentals", top_n=3
                )
                self.assertEqual(out2["backend"], "embedding")
                # Second run: all node vectors came from cache, so only one
                # additional embed call (the query) happened.
                self.assertEqual(
                    sum(len(c) for c in calls), node_calls + 1
                )


if __name__ == "__main__":
    unittest.main()
