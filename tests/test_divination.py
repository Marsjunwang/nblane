"""Tests for core/divination.py (占卜; design home-starmap-enhancements §5).

Covers the deterministic hexagram pick (same state + day -> same 卦),
the real-data anchors, the serious-mode gap-analysis backbone, the
LLM/rule source switch, and the rule fallback (unconfigured / failed /
raising runner — the timeout path). All profiles live under tmp_path;
the LLM gateway runner is always injected or patched — no network.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

from nblane.core import divination

TODAY = date.today()

SCHEMA = {
    "schema_version": "1.0",
    "domain": "Test Domain",
    "nodes": [
        {"id": "robotics", "label": "Robotics", "level": 1},
        {
            "id": "manipulation",
            "label": "Manipulation",
            "level": 2,
            "requires": ["robotics"],
            "keywords": ["grasp"],
        },
        {
            "id": "navigation",
            "label": "Navigation",
            "level": 2,
            "requires": ["robotics"],
        },
    ],
}

SKILL_TREE = {
    "schema": "test-domain",
    "updated": "2026-09-19",
    "nodes": [
        {"id": "robotics", "status": "solid"},
        {"id": "manipulation", "status": "learning"},
        {"id": "navigation", "status": "locked"},
    ],
}

SKILL_MD = """# alice · nblane Profile

## Identity

- **Name**: alice
- **North Star**: 成为能独立交付机器人 demo 的工程师

---
"""

GOALS = {
    "schema_version": "1.0",
    "updated": "2026-09-19",
    "current_goal_id": "goal-1",
    "goals": [
        {"id": "goal-1", "title": "Ship VLA demo", "status": "active"},
        {"id": "goal-2", "title": "Old goal", "status": "archived"},
    ],
}

KANBAN = """# alice · Kanban

## Doing

- [ ] Arm doing task
  - id: kb_doing_p1
  - project_id: project:robot-arm

---

## Queue

---
"""

PROJECT_BOARD = {
    "schema_version": "1.0",
    "updated": "2026-09-19",
    "project_cases": [
        {
            "id": "project:robot-arm",
            "title": "Robot Arm",
            "status": "active",
            "kind": "work",
            "goal_refs": ["goal-1"],
        },
        {
            "id": "project:paused",
            "title": "Paused Project",
            "status": "paused",
        },
    ],
}


def _evidence_pool(name: str) -> dict:
    recent = TODAY - timedelta(days=3)
    old = TODAY - timedelta(days=80)
    return {
        "profile": name,
        "updated": TODAY.isoformat(),
        "evidence_entries": [
            {
                "id": "ev_recent",
                "type": "project",
                "title": "Recent grasping run",
                "date": recent.isoformat(),
                "review_status": "needs_review",
                "project_refs": ["project:robot-arm"],
            },
            {
                "id": "ev_old",
                "type": "practice",
                "title": "Old practice",
                "date": old.isoformat(),
                "review_status": "reviewed",
            },
        ],
    }


def _activity_log(name: str) -> dict:
    return {
        "profile": name,
        "updated": TODAY.isoformat(),
        "habits": [
            {"id": "exercise", "title": "锻炼", "kind": "health", "cadence": "daily"}
        ],
        "checkins": [
            {"date": (TODAY - timedelta(days=offset)).isoformat(),
             "habits": ["exercise"]}
            for offset in range(3)  # today, yesterday, day before -> streak 3
        ],
        "weekly_summaries": [],
    }


def _write_profile(root: Path, name: str = "alice") -> Path:
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (profile / "skill-tree.yaml").write_text(
        yaml.safe_dump(dict(SKILL_TREE, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "goals.yaml").write_text(
        yaml.safe_dump(dict(GOALS, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "kanban.md").write_text(KANBAN, encoding="utf-8")
    (profile / "project-board.yaml").write_text(
        yaml.safe_dump(dict(PROJECT_BOARD, profile=name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "evidence-pool.yaml").write_text(
        yaml.safe_dump(_evidence_pool(name), allow_unicode=True),
        encoding="utf-8",
    )
    (profile / "activity-log.yaml").write_text(
        yaml.safe_dump(_activity_log(name), allow_unicode=True),
        encoding="utf-8",
    )
    return profile


def _write_schemas(base: Path) -> Path:
    schemas = base / "schemas"
    schemas.mkdir(parents=True, exist_ok=True)
    (schemas / "test-domain.yaml").write_text(
        yaml.safe_dump(SCHEMA, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return schemas


def _failing_runner(profile: str, payload: dict) -> SimpleNamespace:
    return SimpleNamespace(ok=False, structured=None, error="ai_not_configured")


class DivinationTestBase(unittest.TestCase):
    """Shared root patching; the LLM runner is always injected/patched."""

    def _patch_roots(self, root: Path, schemas: Path) -> None:
        for target, value in (
            ("nblane.core.profile_io.PROFILES_DIR", root),
            ("nblane.core.io.PROFILES_DIR", root),
            ("nblane.core.io.SCHEMAS_DIR", schemas),
            ("nblane.core.schema_io.SCHEMAS_DIR", schemas),
            ("nblane.core.gap.PROFILES_DIR", root),
            ("nblane.core.learned_keywords._LEARNED_DIR", schemas / ".learned"),
        ):
            patcher = patch(target, value)
            self.addCleanup(patcher.stop)
            patcher.start()

    def _cast(self, root: Path, schemas: Path, **kwargs) -> dict:
        self._patch_roots(root, schemas)
        kwargs.setdefault("runner", _failing_runner)
        return divination.cast_divination(root / "alice", **kwargs)


class TestHexagramTable(DivinationTestBase):
    def test_table_integrity(self) -> None:
        names = set()
        king_wen = set()
        for hexagram in divination.HEXAGRAMS:
            self.assertEqual(len(hexagram["lines"]), 6)
            self.assertTrue(set(hexagram["lines"]) <= {0, 1})
            self.assertNotIn(hexagram["name"], names)
            self.assertNotIn(hexagram["king_wen"], king_wen)
            self.assertTrue(hexagram["judgment"])
            self.assertTrue(hexagram["gloss"])
            names.add(hexagram["name"])
            king_wen.add(hexagram["king_wen"])


class TestPickDeterminism(DivinationTestBase):
    def test_same_material_same_hexagram(self) -> None:
        first = divination.pick_hexagram("material-A")
        second = divination.pick_hexagram("material-A")
        self.assertEqual(first, second)

    def test_material_salted_with_date_and_question(self) -> None:
        anchors = {"skills_lit": 1}
        base = divination.hexagram_material(
            "alice", "play", "", anchors, TODAY
        )
        other_day = divination.hexagram_material(
            "alice", "play", "", anchors, TODAY + timedelta(days=1)
        )
        serious = divination.hexagram_material(
            "alice", "serious", "问一事", anchors, TODAY
        )
        serious_other_q = divination.hexagram_material(
            "alice", "serious", "问另一事", anchors, TODAY
        )
        self.assertNotEqual(base, other_day)
        self.assertNotEqual(base, serious)
        self.assertNotEqual(serious, serious_other_q)
        # Play mode ignores the question entirely.
        self.assertEqual(
            base,
            divination.hexagram_material(
                "alice", "play", "ignored", anchors, TODAY
            ),
        )


class TestPlayMode(DivinationTestBase):
    def test_shape_and_rule_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            outcome = self._cast(root, schemas)
        self.assertEqual(outcome["profile"], "alice")
        self.assertEqual(outcome["mode"], "play")
        self.assertEqual(outcome["source"], "rule")
        self.assertEqual(outcome["generated_on"], TODAY.isoformat())
        hexagram = outcome["hexagram"]
        self.assertEqual(len(hexagram["symbol_lines"]), 6)
        self.assertTrue(set(hexagram["symbol_lines"]) <= {0, 1})
        self.assertTrue(hexagram["name"])
        self.assertTrue(hexagram["judgment"])
        self.assertTrue(outcome["reading"])

    def test_deterministic_within_a_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            first = self._cast(root, schemas)
            second = self._cast(root, schemas)
        self.assertEqual(first["hexagram"], second["hexagram"])
        self.assertEqual(first["reading"], second["reading"])

    def test_anchors_are_real_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            outcome = self._cast(root, schemas)
        anchors = outcome["anchors"]
        # One solid node lit, one learning, three schema nodes total.
        self.assertEqual(anchors["skills_lit"], 1)
        self.assertEqual(anchors["skills_learning"], 1)
        self.assertEqual(anchors["skills_total"], 3)
        # One active project (the paused one stays out).
        self.assertEqual(anchors["projects_active"], 1)
        self.assertEqual(anchors["project_titles"], ["Robot Arm"])
        self.assertEqual(anchors["goal_titles"], ["Ship VLA demo"])
        # Evidence: 2 entries; the recent one needs review, and both fly
        # (30d window for ev_recent + newest-4 density floor for ev_old).
        self.assertEqual(anchors["evidence"], 2)
        self.assertEqual(anchors["evidence_flying"], 2)
        self.assertEqual(anchors["evidence_needs_review"], 1)
        # Habit streak from the real activity log.
        self.assertEqual(anchors["best_streak"], 3)
        # The rule reading quotes the real numbers.
        reading = outcome["reading"]
        self.assertIn("1 星官已点亮", reading)
        self.assertIn("Robot Arm", reading)
        self.assertIn("已连续钤印 3 日", reading)


class TestSeriousMode(DivinationTestBase):
    QUESTION = "grasp the cube with the arm"

    def test_gap_analysis_is_the_backbone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            outcome = self._cast(
                root, schemas, mode="serious", question=self.QUESTION
            )
        self.assertEqual(outcome["mode"], "serious")
        self.assertEqual(outcome["question"], self.QUESTION)
        gap = outcome["anchors"]["gap"]
        self.assertFalse(gap["can_solve"])
        # learning node is a real gap; the solid prerequisite is strength.
        self.assertIn("Manipulation", gap["gap_labels"])
        self.assertIn("Robotics", gap["strong_labels"])
        reading = outcome["reading"]
        self.assertIn(self.QUESTION, reading)
        self.assertIn("Manipulation", reading)
        self.assertIn("Robotics", reading)

    def test_unmatched_question_stays_honest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            outcome = self._cast(
                root, schemas, mode="serious", question="zzzqqq unmatchable"
            )
        self.assertEqual(outcome["source"], "rule")
        self.assertTrue(outcome["anchors"]["gap"].get("error"))
        self.assertIn("尚无对应", outcome["reading"])

    def test_can_solve_when_no_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            # Question matching only the solid root node.
            outcome = self._cast(
                root, schemas, mode="serious", question="robotics"
            )
        gap = outcome["anchors"]["gap"]
        self.assertTrue(gap["can_solve"])
        self.assertIn("卦象曰可", outcome["reading"])


class TestLlmSourceSwitch(DivinationTestBase):
    def test_llm_texts_when_gateway_ok(self) -> None:
        def ok_runner(profile: str, payload: dict) -> SimpleNamespace:
            # The prompt payload must carry the real anchors + hexagram.
            self.assertEqual(payload["hexagram"]["symbol_lines"], list(
                payload["hexagram"]["symbol_lines"]
            ))
            self.assertEqual(payload["anchors"]["skills_lit"], 1)
            return SimpleNamespace(
                ok=True,
                structured={"judgment": "LLM 判词", "reading": "LLM 解卦"},
            )

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            outcome = self._cast(root, schemas, runner=ok_runner)
        self.assertEqual(outcome["source"], "llm")
        self.assertEqual(outcome["hexagram"]["judgment"], "LLM 判词")
        self.assertEqual(outcome["reading"], "LLM 解卦")

    def test_llm_payload_includes_gap_for_serious(self) -> None:
        captured: dict = {}

        def ok_runner(profile: str, payload: dict) -> SimpleNamespace:
            captured.update(payload)
            return SimpleNamespace(
                ok=True,
                structured={"judgment": "判", "reading": "解"},
            )

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            outcome = self._cast(
                root,
                schemas,
                mode="serious",
                question="grasp the cube",
                runner=ok_runner,
            )
        self.assertEqual(outcome["source"], "llm")
        self.assertIn("Manipulation", captured["gap"]["gap_labels"])
        self.assertEqual(captured["mode"], "serious")
        self.assertEqual(captured["question"], "grasp the cube")
        self.assertEqual(
            captured["llm_timeout_seconds"], divination.LLM_TIMEOUT_SECONDS
        )

    def test_incomplete_llm_output_falls_back_to_rule(self) -> None:
        def partial_runner(profile: str, payload: dict) -> SimpleNamespace:
            return SimpleNamespace(
                ok=True, structured={"judgment": "只有判词"}
            )

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            outcome = self._cast(root, schemas, runner=partial_runner)
        self.assertEqual(outcome["source"], "rule")
        self.assertTrue(outcome["reading"])


class TestRuleFallback(DivinationTestBase):
    def test_timeout_exception_still_returns_rule_reading(self) -> None:
        def timeout_runner(profile: str, payload: dict) -> None:
            raise TimeoutError("LLM request timed out")

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            outcome = self._cast(root, schemas, runner=timeout_runner)
        self.assertEqual(outcome["source"], "rule")
        self.assertTrue(outcome["hexagram"]["judgment"])
        self.assertTrue(outcome["reading"])

    def test_unknown_mode_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "profiles"
            _write_profile(root)
            schemas = _write_schemas(base)
            with self.assertRaises(ValueError):
                self._cast(root, schemas, mode=" sideways ")


if __name__ == "__main__":
    unittest.main()
