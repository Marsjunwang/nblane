"""Tests for the heuristic Daily Brief and its AI-enhanced cache."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.daily_brief import (
    DOING_STALL_DAYS,
    ai_daily_brief_summary,
    build_daily_brief,
    clear_daily_brief_ai_cache,
    daily_brief_ai_cache_key,
)
from nblane.core.home_dashboard import (
    clear_dashboard_payload_cache,
    dashboard_payload,
)


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _profile(tmp: Path) -> Path:
    profile = tmp / "alice"
    profile.mkdir()
    (profile / "kanban.md").write_text(
        "# alice · Kanban\n\n"
        "## Doing\n\n"
        "- [ ] Ship robot demo\n"
        "  - id: task_ship_demo\n"
        f"  - started_on: {(date.today() - timedelta(days=30)).isoformat()}\n"
        "  - blocked by: calibration data\n"
        "- [ ] Fresh task\n"
        f"  - started_on: {date.today().isoformat()}\n"
        "  - id: task_fresh\n\n"
        "## Done\n\n"
        "- [x] Finish benchmark\n"
        "  - id: task_finish_benchmark\n",
        encoding="utf-8",
    )
    _write_yaml(
        profile / "skill-tree.yaml",
        {
            "profile": "alice",
            "schema": "robotics-engineer",
            "nodes": [{"id": "ros2_basics", "status": "learning"}],
        },
    )
    _write_yaml(
        profile / "evidence-pool.yaml",
        {"profile": "alice", "evidence_entries": []},
    )
    _write_yaml(
        profile / "goals.yaml",
        {
            "schema_version": "1.0",
            "profile": "alice",
            "current_goal_id": "g1",
            "goals": [
                {
                    "id": "g1",
                    "title": "Robotics demo",
                    "label": "Demo goal",
                    "status": "active",
                    "ui_visibility": "discreet",
                }
            ],
        },
    )
    (profile / "SKILL.md").write_text("# Alice · nblane Profile\n", encoding="utf-8")
    return profile


def _write_agent_activity(profile: Path, pending_titles: list[str]) -> None:
    items = [
        {
            "id": f"act:writeback:{index}",
            "kind": "writeback",
            "status": "pending",
            "title": title,
        }
        for index, title in enumerate(pending_titles)
    ]
    items.append(
        {
            "id": "act:candidate:done",
            "kind": "candidate",
            "status": "applied",
            "title": "Already applied",
        }
    )
    _write_yaml(
        profile / "agent-activity.yaml",
        {"schema_version": "1.0", "profile": "alice", "items": items},
    )


class TestDailyBrief(unittest.TestCase):
    """The heuristic brief derives structured data from the payload only."""

    def setUp(self) -> None:
        clear_dashboard_payload_cache()
        clear_daily_brief_ai_cache()

    def tearDown(self) -> None:
        clear_dashboard_payload_cache()
        clear_daily_brief_ai_cache()

    def test_brief_focus_decisions_risks_research(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = _profile(Path(tmp_s))
            _write_agent_activity(profile, ["Update SKILL.md", "Patch kanban"])
            payload = dashboard_payload(profile)
        brief = payload["daily_brief"]

        self.assertEqual(brief["date"], date.today().isoformat())
        focus = brief["focus"]
        self.assertEqual(focus["goal_id"], "g1")
        self.assertEqual(focus["goal_label"], "Demo goal")
        self.assertFalse(focus["goal_locked"])
        self.assertEqual(focus["task_title"], "Ship robot demo")
        self.assertEqual(focus["task_blocked_by"], "calibration data")
        self.assertEqual(focus["doing_total"], 2)
        self.assertEqual(focus["path"], "pages/3_Kanban.py")

        decisions = brief["decisions"]
        self.assertEqual(decisions["agent_pending"], 2)
        self.assertEqual(
            decisions["evidence_pending"],
            int(payload["pending_evidence"]["done_uncrystallized_count"])
            + int(payload["pending_evidence"]["unlinked_count"])
            + int(payload["pending_evidence"]["needs_review_count"])
            + int(payload["pending_evidence"]["status_risk_count"]),
        )
        self.assertEqual(
            decisions["total"],
            decisions["evidence_pending"] + decisions["agent_pending"],
        )
        self.assertEqual(decisions["evidence_path"], "pages/2_Evidence_Review.py")
        self.assertEqual(decisions["agent_path"], "pages/9_Agent_Activity.py")

        risks = brief["risks"]
        health_counts = payload["health"]["counts"]
        self.assertEqual(risks["health_errors"], health_counts.get("error", 0))
        self.assertEqual(risks["health_warnings"], health_counts.get("warning", 0))
        # The 30-day-old Doing task is stalled; the one started today is not.
        self.assertEqual(risks["stalled_doing_count"], 1)
        self.assertEqual(risks["stalled_doing"][0]["id"], "task_ship_demo")
        self.assertGreaterEqual(
            risks["stalled_doing"][0]["days"], DOING_STALL_DAYS
        )
        self.assertEqual(risks["health_path"], "pages/5_Profile_Health.py")

        research = brief["research"]
        self.assertEqual(research["path"], "pages/7_Research.py")
        self.assertIn("inbox", research)
        self.assertIn("active", research)

    def test_private_goal_never_leaks_label_into_brief(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = _profile(Path(tmp_s))
            _write_yaml(
                profile / "goals.yaml",
                {
                    "profile": "alice",
                    "current_goal_id": "g1",
                    "goals": [
                        {
                            "id": "g1",
                            "title": "Secret job hunt",
                            "status": "active",
                            "ui_visibility": "private",
                        }
                    ],
                },
            )
            payload = dashboard_payload(profile)
        focus = payload["daily_brief"]["focus"]
        self.assertTrue(focus["goal_locked"])
        self.assertEqual(focus["goal_label"], "")

    def test_agent_activity_summary_and_fingerprint_invalidation(self) -> None:
        """Rewriting agent-activity.yaml busts the payload cache via mtime."""
        with tempfile.TemporaryDirectory() as tmp_s:
            profile = _profile(Path(tmp_s))
            _write_agent_activity(profile, ["One pending"])
            first = dashboard_payload(profile)
            self.assertEqual(first["agent_activity"]["pending_total"], 1)
            self.assertEqual(
                first["agent_activity"]["pending_titles"], ["One pending"]
            )

            _write_agent_activity(profile, ["One pending", "Second pending"])
            second = dashboard_payload(profile)
        self.assertEqual(second["agent_activity"]["pending_total"], 2)
        self.assertEqual(second["agent_activity"]["total"], 3)
        self.assertEqual(second["agent_activity"]["path"], "pages/9_Agent_Activity.py")
        self.assertEqual(second["daily_brief"]["decisions"]["agent_pending"], 2)

    def test_brief_builder_is_pure_over_payload_dict(self) -> None:
        """build_daily_brief needs no profile I/O — just an assembled payload."""
        brief = build_daily_brief(
            {
                "primary_goal": {"is_set": False, "locked": False, "projection": None},
                "kanban": {"doing": [], "doing_items": [], "doing_total": 0},
                "pending_evidence": {},
                "agent_activity": {"pending_total": 0},
                "health": {"counts": {}},
                "sources": {},
            },
            today=date(2026, 9, 16),
        )
        self.assertEqual(brief["date"], "2026-09-16")
        self.assertFalse(brief["focus"]["goal_set"])
        self.assertEqual(brief["decisions"]["total"], 0)
        self.assertEqual(brief["risks"]["stalled_doing"], [])


class TestDailyBriefAi(unittest.TestCase):
    """AI brief: cache keys, failure caching, and offline fallback."""

    def setUp(self) -> None:
        clear_daily_brief_ai_cache()

    def tearDown(self) -> None:
        clear_daily_brief_ai_cache()

    def test_cache_key_includes_revision_date_backend_model_lang(self) -> None:
        day = date(2026, 9, 16)
        key = daily_brief_ai_cache_key(
            "alice", "rev1", "llm", "gpt-x", "zh", today=day
        )
        self.assertEqual(key, ("alice", "rev1", "2026-09-16", "llm", "gpt-x", "zh"))
        self.assertNotEqual(
            key,
            daily_brief_ai_cache_key(
                "alice", "rev2", "llm", "gpt-x", "zh", today=day
            ),
        )
        self.assertNotEqual(
            key,
            daily_brief_ai_cache_key(
                "alice", "rev1", "codex", "gpt-x", "zh", today=day
            ),
        )
        self.assertNotEqual(
            key,
            daily_brief_ai_cache_key(
                "alice", "rev1", "llm", "gpt-x", "en", today=day
            ),
        )

    def test_runner_called_once_per_cache_key(self) -> None:
        calls: list[tuple] = []

        def runner(profile: str, grounding: dict, backend: str, model: str) -> dict:
            calls.append((profile, backend, model))
            return {"summary": "Focus on the demo today.", "backend": backend}

        brief = {"date": "2026-09-16", "focus": {"goal_label": "Demo"}}
        first = ai_daily_brief_summary(
            "alice", brief, backend="llm", model="m1", revision="r1", runner=runner
        )
        second = ai_daily_brief_summary(
            "alice", brief, backend="llm", model="m1", revision="r1", runner=runner
        )
        third = ai_daily_brief_summary(
            "alice", brief, backend="llm", model="m1", revision="r2", runner=runner
        )
        self.assertEqual(first["summary"], "Focus on the demo today.")
        self.assertEqual(second, first)
        self.assertEqual(len(calls), 2)  # r1 cached; r2 forced a re-run
        self.assertEqual(third["summary"], "Focus on the demo today.")

    def test_failures_are_cached_and_fall_back_to_heuristic(self) -> None:
        calls: list[str] = []

        def failing_runner(profile: str, grounding: dict, backend: str, model: str) -> dict:
            calls.append(backend)
            raise RuntimeError("provider down")

        brief = {"date": "2026-09-16"}
        first = ai_daily_brief_summary(
            "alice", brief, backend="llm", model="", revision="r1", runner=failing_runner
        )
        second = ai_daily_brief_summary(
            "alice", brief, backend="llm", model="", revision="r1", runner=failing_runner
        )
        self.assertEqual(first, {"summary": "", "backend": ""})
        self.assertEqual(second, {"summary": "", "backend": ""})
        self.assertEqual(len(calls), 1)

    def test_default_runner_never_calls_gateway_when_network_disabled(self) -> None:
        """NBLANE_DISABLE_NETWORK_LOOKUPS short-circuits before the gateway."""
        self.assertTrue(os.environ.get("NBLANE_DISABLE_NETWORK_LOOKUPS"))
        brief = {"date": "2026-09-16", "focus": {}}
        with patch(
            "nblane.core.llm.is_configured", return_value=True
        ), patch("nblane.core.ai.run_json") as gateway_mock:
            gateway_mock.side_effect = AssertionError(
                "gateway must not be called offline"
            )
            result = ai_daily_brief_summary(
                "alice", brief, backend="llm", model="m", revision="r1"
            )
        self.assertEqual(result, {"summary": "", "backend": ""})
        gateway_mock.assert_not_called()

    def test_default_runner_unconfigured_llm_returns_empty(self) -> None:
        brief = {"date": "2026-09-16"}
        with patch(
            "nblane.core.llm.is_configured", return_value=False
        ), patch.dict(os.environ, {"NBLANE_DISABLE_NETWORK_LOOKUPS": ""}):
            result = ai_daily_brief_summary(
                "alice", brief, backend="llm", model="", revision="r1"
            )
        self.assertEqual(result, {"summary": "", "backend": ""})


if __name__ == "__main__":
    unittest.main()
