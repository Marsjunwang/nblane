"""Tests for the MCP resources/tools added for the OpenClaw integration."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.agent_activity import load_agent_activity
from nblane.core.inbox import load_inbox

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"

_SKIP_NO_MCP = unittest.skipUnless(find_spec("mcp"), "mcp dependency is not installed")


def _template_profile(tmp: Path, name: str = "alice") -> Path:
    profile = tmp / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            text = text.replace("{YYYY-MM-DD}", "2026-05-14")
            file_path.write_text(text, encoding="utf-8")
    return profile


@_SKIP_NO_MCP
class TestMcpProfileResources(unittest.TestCase):
    """New read-only profile resources render summaries and redact private data."""

    def _patch_profile(self, profile: Path):
        from nblane import mcp_server

        return (
            patch.object(
                mcp_server,
                "resolve_active_profile",
                lambda: ("alice", None),
            ),
            patch.object(mcp_server, "profile_dir", lambda _name: profile),
        )

    def test_goals_resource_redacts_private_content(self) -> None:
        """Private North Star and private goals never reach the MCP output."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "SKILL.md").write_text(
                """# alice

## Identity

- **Name**: alice
- **North Star**: Secret Mars plan
- **North Star Brief**: Mars brief
- **North Star Visibility**: private
""",
                encoding="utf-8",
            )
            (profile / "goals.yaml").write_text(
                yaml.dump(
                    {
                        "schema_version": "1.0",
                        "profile": "alice",
                        "current_goal_id": "g1",
                        "goals": [
                            {
                                "id": "g1",
                                "title": "Ship VLA demo",
                                "status": "active",
                                "ui_visibility": "visible",
                                "summary": "demo for review",
                            },
                            {
                                "id": "g2",
                                "title": "Secret goal",
                                "status": "active",
                                "ui_visibility": "private",
                            },
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_goals()

        self.assertIn("# Goals: alice", text)
        self.assertIn("- active: 2", text)
        self.assertIn("Ship VLA demo", text)
        self.assertIn("redacted", text)
        self.assertNotIn("Secret Mars plan", text)
        self.assertNotIn("Mars brief", text)
        self.assertNotIn("Secret goal", text)

    def test_goals_resource_shows_visible_north_star_and_primary(self) -> None:
        """Visible North Star and the primary goal render for the agent."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "SKILL.md").write_text(
                """# alice

## Identity

- **Name**: alice
- **North Star**: Mars by 2035
- **North Star Visibility**: visible
""",
                encoding="utf-8",
            )
            (profile / "goals.yaml").write_text(
                yaml.dump(
                    {
                        "profile": "alice",
                        "current_goal_id": "g1",
                        "goals": [
                            {
                                "id": "g1",
                                "title": "Ship VLA demo",
                                "status": "active",
                                "target": "2026-10-01",
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_goals()

        self.assertIn("Mars by 2035", text)
        self.assertIn("## Primary goal", text)
        self.assertIn("Ship VLA demo", text)

    def test_resource_profile_resolution_errors(self) -> None:
        """Every new resource reports profile-resolution errors inline."""
        from nblane import mcp_server

        resources = [
            ("profile://goals", mcp_server.resource_goals),
            ("profile://evidence", mcp_server.resource_evidence),
            ("profile://inbox", mcp_server.resource_inbox),
            ("profile://learning", mcp_server.resource_learning),
            ("agent://activity", mcp_server.resource_agent_activity),
        ]
        with patch.object(
            mcp_server,
            "resolve_active_profile",
            lambda: (None, "no profile set"),
        ):
            for getter, fn in resources:
                with self.subTest(getter=getter):
                    text = fn()
                    self.assertTrue(
                        text.startswith(f"ERROR [{getter}]: no profile set"),
                        text,
                    )

    def test_evidence_resource_summarizes_pool(self) -> None:
        """Evidence summary counts by review status and lists recent rows."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "evidence-pool.yaml").write_text(
                yaml.dump(
                    {
                        "profile": "alice",
                        "evidence_entries": [
                            {
                                "id": "ev_old",
                                "type": "project",
                                "title": "Built robot arm",
                                "date": "2026-01-01",
                                "review_status": "reviewed",
                            },
                            {
                                "id": "ev_new",
                                "type": "paper",
                                "title": "VLA survey read",
                                "date": "2026-06-01",
                                "review_status": "needs_review",
                            },
                            {
                                "id": "ev_gone",
                                "type": "practice",
                                "title": "Deprecated thing",
                                "date": "2026-07-01",
                                "deprecated": True,
                            },
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_evidence()

        self.assertIn("Total entries: 2", text)
        self.assertIn("- needs_review: 1", text)
        self.assertIn("- reviewed: 1", text)
        self.assertIn("Deprecated (hidden below): 1", text)
        self.assertLess(text.index("ev_new"), text.index("ev_old"))
        self.assertNotIn("ev_gone", text)

    def test_evidence_resource_handles_missing_pool(self) -> None:
        """A profile without evidence-pool.yaml gets a placeholder, not an error."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_evidence()

        self.assertIn("no evidence-pool.yaml", text)

    def test_inbox_resource_lists_open_items_only(self) -> None:
        """Inbox resource shows inbox/captured/clarified items, not archived."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "inbox.yaml").write_text(
                yaml.dump(
                    {
                        "profile": "alice",
                        "items": [
                            {
                                "id": "i1",
                                "title": "Read VLA paper",
                                "status": "inbox",
                                "type": "link",
                                "tags": ["reading"],
                                "created_at": "2026-09-01",
                            },
                            {
                                "id": "i2",
                                "title": "Old archived note",
                                "status": "archived",
                            },
                            {
                                "id": "i3",
                                "title": "Clarified thought",
                                "status": "clarified",
                                "type": "note",
                                "created_at": "2026-09-02",
                            },
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_inbox()

        self.assertIn("Open items: 2 (total: 3)", text)
        self.assertIn("`i1`", text)
        self.assertIn("Read VLA paper", text)
        self.assertIn("reading", text)
        self.assertIn("`i3`", text)
        self.assertNotIn("Old archived note", text)

    def test_learning_resource_summary(self) -> None:
        """Learning resource shows status counts, reading list, recent entries."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "learning-log.yaml").write_text(
                yaml.dump(
                    {
                        "profile": "alice",
                        "resources": [
                            {
                                "id": "l1",
                                "kind": "paper",
                                "title": "VLA survey",
                                "status": "reading",
                                "added_at": "2026-09-01",
                            },
                            {
                                "id": "l2",
                                "kind": "book",
                                "title": "RL book",
                                "status": "processed",
                                "added_at": "2026-05-01",
                            },
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_learning()

        self.assertIn("Total resources: 2", text)
        self.assertIn("- reading: 1", text)
        self.assertIn("- processed: 1", text)
        self.assertIn("## Active (reading) — 1", text)
        self.assertIn("VLA survey", text)
        self.assertIn("## Recent entries", text)

    def test_agent_activity_resource_lists_pending_queue(self) -> None:
        """Agent activity resource counts statuses and lists pending items."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "agent-activity.yaml").write_text(
                yaml.dump(
                    {
                        "schema_version": "1.0",
                        "profile": "alice",
                        "items": [
                            {
                                "id": "act:candidate:aaa",
                                "kind": "candidate",
                                "candidate_type": "evidence",
                                "source_page": "Review",
                                "target_owner": "evidence_pool",
                                "status": "pending",
                                "title": "Pending evidence item",
                                "created": "2026-09-01T00:00:00+00:00",
                            },
                            {
                                "id": "act:writeback:bbb",
                                "kind": "writeback",
                                "candidate_type": "kanban_move",
                                "source_page": "Kanban",
                                "target_owner": "kanban",
                                "status": "applied",
                                "title": "Old applied item",
                                "created": "2026-08-01T00:00:00+00:00",
                            },
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            patches = self._patch_profile(profile)
            with patches[0], patches[1]:
                text = mcp_server.resource_agent_activity()

        self.assertIn("- pending: 1", text)
        self.assertIn("- applied: 1", text)
        self.assertIn("Pending review (1 total, 1 shown)", text)
        self.assertIn("act:candidate:aaa", text)
        self.assertIn("Pending evidence item", text)
        self.assertNotIn("act:writeback:bbb", text)


@_SKIP_NO_MCP
class TestMcpStructuredTools(unittest.TestCase):
    """New dict-returning tools write through locked core helpers."""

    def test_capture_inbox_appends_item_via_update_inbox(self) -> None:
        """capture_inbox writes one inbox item with captured_by=source."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch.object(mcp_server, "profile_dir", lambda _name: profile),
            ):
                result = mcp_server.tool_capture_inbox(
                    " Read the VLA survey ",
                    raw_text="https://example.com/vla",
                    tags=["paper", "vla"],
                    note="from wechat",
                )
                inbox = load_inbox(profile)

        self.assertTrue(result["ok"])
        self.assertTrue(result["item_id"].startswith("inbox_"))
        self.assertEqual(result["status"], "inbox")
        self.assertEqual(result["captured_by"], "openclaw")
        self.assertEqual(len(inbox.items), 1)
        item = inbox.items[0]
        self.assertEqual(item.title, "Read the VLA survey")
        self.assertEqual(item.source, "openclaw")
        self.assertEqual(item.captured_by, "openclaw")
        self.assertEqual(item.tags, ["paper", "vla"])
        self.assertEqual(item.raw_text, "https://example.com/vla")
        self.assertEqual(item.status, "inbox")
        self.assertEqual(item.history[0].note, "from wechat")

    def test_capture_inbox_error_paths(self) -> None:
        """capture_inbox returns structured errors, never raises."""
        from nblane import mcp_server

        with patch.object(
            mcp_server,
            "resolve_active_profile",
            lambda: (None, "no profile set"),
        ):
            result = mcp_server.tool_capture_inbox("hello")
        self.assertEqual(result, {"ok": False, "error": "no profile set"})

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch.object(mcp_server, "profile_dir", lambda _name: profile),
            ):
                blank = mcp_server.tool_capture_inbox("   ")
        self.assertFalse(blank["ok"])
        self.assertIn("title", blank["error"])

    def test_submit_evidence_candidate_queues_pending_review_item(self) -> None:
        """Evidence candidate lands in Agent Activity with the Review contract."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch(
                    "nblane.core.agent_activity.profile_dir",
                    lambda _name: profile,
                ),
                patch(
                    "nblane.core.review_actions.profile_dir",
                    lambda _name: profile,
                ),
            ):
                result = mcp_server.tool_submit_evidence_candidate(
                    skill_id="ros2_basics",
                    title="Built nav stack",
                    evidence_type="project",
                    date="2026-09-01",
                    url="https://example.com/nav",
                    summary="shipped nav",
                )
                activity = load_agent_activity("alice")

        self.assertTrue(result["ok"])
        self.assertTrue(result["item_id"].startswith("act:review:evidence:"))
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["target_owner"], "evidence_pool")
        self.assertEqual(result["candidate_type"], "evidence")
        self.assertEqual(len(activity["items"]), 1)
        item = activity["items"][0]
        self.assertEqual(item["status"], "pending")
        self.assertEqual(item["source_page"], "Review")
        self.assertEqual(item["payload"]["skill_id"], "ros2_basics")
        self.assertEqual(item["payload"]["type"], "project")
        self.assertEqual(item["payload"]["date"], "2026-09-01")
        self.assertIn("skill:ros2_basics", item["preview"])

    def test_submit_evidence_candidate_error_paths(self) -> None:
        """Evidence candidate validates inputs and profile resolution."""
        from nblane import mcp_server

        with patch.object(
            mcp_server,
            "resolve_active_profile",
            lambda: (None, "no profile set"),
        ):
            result = mcp_server.tool_submit_evidence_candidate(
                skill_id="ros2_basics",
                title="x",
                evidence_type="project",
                date="2026-09-01",
            )
        self.assertEqual(result, {"ok": False, "error": "no profile set"})

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch(
                    "nblane.core.agent_activity.profile_dir",
                    lambda _name: profile,
                ),
                patch(
                    "nblane.core.review_actions.profile_dir",
                    lambda _name: profile,
                ),
            ):
                bad_type = mcp_server.tool_submit_evidence_candidate(
                    skill_id="ros2_basics",
                    title="x",
                    evidence_type="bogus",
                    date="2026-09-01",
                )
                blank_title = mcp_server.tool_submit_evidence_candidate(
                    skill_id="ros2_basics",
                    title=" ",
                    evidence_type="project",
                    date="2026-09-01",
                )
                blank_skill = mcp_server.tool_submit_evidence_candidate(
                    skill_id="",
                    title="x",
                    evidence_type="project",
                    date="2026-09-01",
                )
                activity = load_agent_activity("alice")

        self.assertFalse(bad_type["ok"])
        self.assertIn("unknown evidence_type", bad_type["error"])
        self.assertFalse(blank_title["ok"])
        self.assertFalse(blank_skill["ok"])
        self.assertEqual(activity["items"], [])

    def test_submit_profile_model_candidate_is_manual_review_only(self) -> None:
        """Profile-model candidates carry a self-describing payload, no applier."""
        from nblane import mcp_server
        from nblane.core.review_actions import apply_review_activity_item

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch(
                    "nblane.core.agent_activity.profile_dir",
                    lambda _name: profile,
                ),
                patch(
                    "nblane.core.review_actions.profile_dir",
                    lambda _name: profile,
                ),
            ):
                result = mcp_server.tool_submit_profile_model_candidate(
                    "working_style.prefers",
                    "terse answers",
                    "user asked three times this week",
                )
                activity = load_agent_activity("alice")
                with self.assertRaises(ValueError):
                    apply_review_activity_item("alice", result["item_id"])

        self.assertTrue(result["ok"])
        self.assertEqual(result["candidate_type"], "profile_model")
        self.assertEqual(result["target_owner"], "profile_context")
        item = activity["items"][0]
        self.assertEqual(item["status"], "pending")
        self.assertEqual(
            item["payload"],
            {
                "field": "working_style.prefers",
                "proposed_value": "terse answers",
                "rationale": "user asked three times this week",
                "target_file": "agent-profile.yaml",
            },
        )

        with patch.object(
            mcp_server,
            "resolve_active_profile",
            lambda: (None, "no profile set"),
        ):
            failed = mcp_server.tool_submit_profile_model_candidate("a", "b", "c")
        self.assertEqual(failed, {"ok": False, "error": "no profile set"})

    def test_submit_kanban_candidate_queues_pending_review_item(self) -> None:
        """Kanban candidates carry the move payload the applier consumes."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch(
                    "nblane.core.agent_activity.profile_dir",
                    lambda _name: profile,
                ),
                patch(
                    "nblane.core.review_actions.profile_dir",
                    lambda _name: profile,
                ),
            ):
                result = mcp_server.tool_submit_kanban_candidate(
                    "move",
                    "Write VLA survey",
                    target_section="Doing",
                    note="start now",
                )
                activity = load_agent_activity("alice")

        self.assertTrue(result["ok"])
        self.assertTrue(result["item_id"].startswith("act:candidate:"))
        self.assertEqual(result["candidate_type"], "kanban_move")
        self.assertEqual(result["target_owner"], "kanban")
        item = activity["items"][0]
        self.assertEqual(item["status"], "pending")
        self.assertEqual(item["source_page"], "Review")
        self.assertEqual(
            item["payload"],
            {
                "action": "move",
                "card_ref": "Write VLA survey",
                "target_section": "Doing",
                "note": "start now",
            },
        )

    def test_submit_kanban_candidate_error_paths(self) -> None:
        """Kanban candidate rejects unsupported actions and bad profiles."""
        from nblane import mcp_server

        with patch.object(
            mcp_server,
            "resolve_active_profile",
            lambda: (None, "no profile set"),
        ):
            result = mcp_server.tool_submit_kanban_candidate("move", "card")
        self.assertEqual(result, {"ok": False, "error": "no profile set"})

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch(
                    "nblane.core.agent_activity.profile_dir",
                    lambda _name: profile,
                ),
                patch(
                    "nblane.core.review_actions.profile_dir",
                    lambda _name: profile,
                ),
            ):
                bad_action = mcp_server.tool_submit_kanban_candidate(
                    "delete", "card"
                )
                blank_ref = mcp_server.tool_submit_kanban_candidate("move", " ")
                activity = load_agent_activity("alice")

        self.assertFalse(bad_action["ok"])
        self.assertIn("unsupported action", bad_action["error"])
        self.assertFalse(blank_ref["ok"])
        self.assertEqual(activity["items"], [])

    def test_submit_kanban_candidate_rejects_unknown_section(self) -> None:
        """A non-empty target_section must resolve to a real board column."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch(
                    "nblane.core.agent_activity.profile_dir",
                    lambda _name: profile,
                ),
                patch(
                    "nblane.core.review_actions.profile_dir",
                    lambda _name: profile,
                ),
            ):
                bad = mcp_server.tool_submit_kanban_candidate(
                    "move", "card", target_section="Someday"
                )
                empty_ok = mcp_server.tool_submit_kanban_candidate(
                    "move", "card-a", target_section=""
                )
                slash_name = mcp_server.tool_submit_kanban_candidate(
                    "move", "card-b", target_section="someday / maybe"
                )
                activity = load_agent_activity("alice")

        self.assertFalse(bad["ok"])
        self.assertIn("unknown target_section", bad["error"])
        self.assertIn("Someday / Maybe", bad["error"])
        # Empty stays allowed; the full column name (with the slash) works
        # case-insensitively and is stored in canonical form.
        self.assertTrue(empty_ok["ok"])
        self.assertTrue(slash_name["ok"])
        sections = [
            item["payload"]["target_section"] for item in activity["items"]
        ]
        self.assertEqual(sections, ["", "Someday / Maybe"])

    def test_submit_kanban_candidate_corrupt_activity_file_is_error_payload(
        self,
    ) -> None:
        """Corrupted profile YAML surfaces as an error payload, not a raise."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "agent-activity.yaml").write_text(
                "items: [unclosed\n", encoding="utf-8"
            )
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch(
                    "nblane.core.agent_activity.profile_dir",
                    lambda _name: profile,
                ),
                patch(
                    "nblane.core.review_actions.profile_dir",
                    lambda _name: profile,
                ),
            ):
                result = mcp_server.tool_submit_kanban_candidate(
                    "move", "card", target_section="Doing"
                )

        self.assertFalse(result["ok"])
        self.assertTrue(result["error"])

    def test_capture_inbox_corrupt_inbox_file_is_error_payload(self) -> None:
        """capture_inbox also converts YAML corruption into an error payload."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            (profile / "inbox.yaml").write_text(
                "items: [unclosed\n", encoding="utf-8"
            )
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch.object(mcp_server, "profile_dir", lambda _name: profile),
            ):
                result = mcp_server.tool_capture_inbox("note")

        self.assertFalse(result["ok"])
        self.assertTrue(result["error"])

    def test_run_validate_reports_ok_and_errors(self) -> None:
        """run_validate returns bounded ok/errors/warnings without writing."""
        from nblane import mcp_server

        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch.object(mcp_server, "profile_dir", lambda _name: profile),
            ):
                healthy = mcp_server.tool_run_validate()
                (profile / "skill-tree.yaml").write_text(
                    'profile: "alice"\nupdated: "2026-05-14"\nnodes: []\n',
                    encoding="utf-8",
                )
                broken = mcp_server.tool_run_validate()

        self.assertTrue(healthy["ok"])
        self.assertEqual(healthy["errors"], [])
        self.assertEqual(healthy["warnings"], [])
        self.assertEqual(healthy["profile"], "alice")
        self.assertFalse(broken["ok"])
        self.assertEqual(broken["error_count"], len(broken["errors"]))
        self.assertTrue(any("schema" in e for e in broken["errors"]))

    def test_run_validate_profile_error(self) -> None:
        """run_validate surfaces profile-resolution errors as structured dicts."""
        from nblane import mcp_server

        with patch.object(
            mcp_server,
            "resolve_active_profile",
            lambda: (None, "no profile set"),
        ):
            result = mcp_server.tool_run_validate()
        self.assertEqual(result, {"ok": False, "error": "no profile set"})

    def test_run_sync_check_reports_drift_and_in_sync(self) -> None:
        """run_sync_check lists drifted blocks and never writes."""
        from nblane import mcp_server

        skill_md = (
            "# alice\n\n"
            "## Skill Tree\n\n"
            "<!-- BEGIN GENERATED:skill_tree -->\n"
            "{body}\n"
            "<!-- END GENERATED:skill_tree -->\n\n"
            "## Current Focus\n\n"
            "<!-- BEGIN GENERATED:current_focus -->\n"
            "{focus}\n"
            "<!-- END GENERATED:current_focus -->\n"
        )
        expected_focus = (
            "**Active** (this week):\n"
            "- kanban.md not found.\n\n"
            "**Queued** (next):\n"
            "- none\n\n"
            "**Blocked**:\n"
            "- none"
        )
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch.object(mcp_server, "profile_dir", lambda _name: profile),
            ):
                (profile / "SKILL.md").write_text(
                    skill_md.format(body="- [x] stale", focus="stale focus"),
                    encoding="utf-8",
                )
                drifted = mcp_server.tool_run_sync_check()
                (profile / "SKILL.md").write_text(
                    skill_md.format(
                        body="- skill-tree.yaml not found.",
                        focus=expected_focus,
                    ),
                    encoding="utf-8",
                )
                in_sync = mcp_server.tool_run_sync_check()

        self.assertTrue(drifted["ok"])
        self.assertFalse(drifted["in_sync"])
        self.assertEqual(
            drifted["drifted_blocks"], ["skill_tree", "current_focus"]
        )
        self.assertTrue(in_sync["ok"])
        self.assertTrue(in_sync["in_sync"])
        self.assertEqual(in_sync["drifted_blocks"], [])

    def test_run_sync_check_error_paths(self) -> None:
        """run_sync_check reports missing profile and missing SKILL.md."""
        from nblane import mcp_server

        with patch.object(
            mcp_server,
            "resolve_active_profile",
            lambda: (None, "no profile set"),
        ):
            result = mcp_server.tool_run_sync_check()
        self.assertEqual(result, {"ok": False, "error": "no profile set"})

        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch.object(mcp_server, "profile_dir", lambda _name: profile),
            ):
                missing = mcp_server.tool_run_sync_check()
        self.assertFalse(missing["ok"])
        self.assertIn("SKILL.md", missing["error"])

    def test_evidence_candidate_full_loop_lands_in_pool(self) -> None:
        """Tool → activity item → apply_review_activity_item → pool row."""
        from nblane import mcp_server
        from nblane.core.review_actions import apply_review_activity_item

        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            with (
                patch.object(
                    mcp_server,
                    "resolve_active_profile",
                    lambda: ("alice", None),
                ),
                patch(
                    "nblane.core.agent_activity.profile_dir",
                    lambda _name: profile,
                ),
                patch(
                    "nblane.core.review_actions.profile_dir",
                    lambda _name: profile,
                ),
                patch("nblane.core.profile_io.PROFILES_DIR", profile.parent),
            ):
                submitted = mcp_server.tool_submit_evidence_candidate(
                    skill_id="ros2_basics",
                    title="Built nav stack",
                    evidence_type="project",
                    date="2026-09-01",
                    url="https://example.com/nav",
                    summary="shipped nav",
                )
                applied = apply_review_activity_item(
                    "alice", submitted["item_id"]
                )
                pool = yaml.safe_load(
                    (profile / "evidence-pool.yaml").read_text(encoding="utf-8")
                )
                activity = load_agent_activity("alice")

        self.assertTrue(submitted["ok"])
        self.assertTrue(applied.ok, applied.errors)
        row = next(
            entry
            for entry in pool["evidence_entries"]
            if entry["title"] == "Built nav stack"
        )
        self.assertEqual(row["type"], "project")
        self.assertEqual(row["date"], "2026-09-01")
        self.assertEqual(row["url"], "https://example.com/nav")
        self.assertEqual(row["review_status"], "needs_review")
        self.assertIn("skill:ros2_basics", row["source_refs"])
        item = next(
            entry
            for entry in activity["items"]
            if entry["id"] == submitted["item_id"]
        )
        self.assertEqual(item["status"], "applied")


if __name__ == "__main__":
    unittest.main()
