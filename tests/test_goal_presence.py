"""Tests for the React goal presence payload and copy."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.goals import Goal, goal_for_ui
from nblane.web_i18n import common_ui
from nblane.web_shared import _build_goal_presence_payload


_UI = {
    "goal_presence_current": "Current goal",
    "goal_presence_details": "Goal details",
    "goal_presence_edit_home": "Edit on Home.",
    "goal_presence_hidden_note": "Hidden on regular pages.",
    "goal_presence_agent_context_on": "Agent context enabled",
    "goal_presence_agent_context_off": "Agent context disabled",
    "goal_strip_default_label": "Stage goal",
    "goal_strip_focus": "Focus",
    "goal_strip_hidden": "Goal set",
    "goal_strip_target": "Target",
    "goal_status_active": "Active",
    "goal_status_paused": "Paused",
    "goal_status_completed": "Completed",
    "goal_status_archived": "Archived",
}


class TestGoalPresencePayload(unittest.TestCase):
    """Payloads sent to React stay privacy-safe."""

    def test_visible_payload_contains_details(self) -> None:
        """Visible goals can show the full UI-safe details."""
        goal = Goal(
            id="g",
            title="Sensitive title",
            label="Safe label",
            summary="Summary",
            focus=["f1", "f2", "f3", "f4"],
            ui_visibility="visible",
        )
        payload = _build_goal_presence_payload(
            goal_for_ui(goal),
            _UI,
            goal=goal,
        )

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["title"], "Sensitive title")
        self.assertEqual(payload["summary"], "Summary")
        self.assertEqual(payload["focus"], ["f1", "f2", "f3"])

    def test_discreet_payload_omits_sensitive_details(self) -> None:
        """Discreet goals do not send title, summary, notes, or focus."""
        goal = Goal(
            id="g",
            title="Sensitive title",
            label="Safe label",
            summary="Summary",
            notes="Notes",
            focus=["f1"],
            ui_visibility="discreet",
        )
        payload = _build_goal_presence_payload(
            goal_for_ui(goal),
            _UI,
            goal=goal,
        )

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["label"], "Safe label")
        self.assertNotIn("title", payload)
        self.assertNotIn("summary", payload)
        self.assertNotIn("notes", payload)
        self.assertNotIn("focus", payload)

    def test_hidden_payload_omits_label_and_details(self) -> None:
        """Hidden goals only tell React that a goal exists."""
        goal = Goal(
            id="g",
            title="Sensitive title",
            label="Safe label",
            summary="Summary",
            focus=["f1"],
            ui_visibility="hidden",
        )
        payload = _build_goal_presence_payload(
            goal_for_ui(goal),
            _UI,
            goal=goal,
        )

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["visibility"], "hidden")
        self.assertNotIn("label", payload)
        self.assertNotIn("title", payload)
        self.assertNotIn("summary", payload)
        self.assertNotIn("focus", payload)

    def test_private_payload_is_none(self) -> None:
        """Private goals are not sent to React at all."""
        goal = Goal(
            id="g",
            title="Sensitive title",
            ui_visibility="private",
        )

        self.assertIsNone(
            _build_goal_presence_payload(goal_for_ui(goal), _UI, goal=goal)
        )


class TestGoalPresenceI18n(unittest.TestCase):
    """Goal presence copy follows the selected UI language."""

    def test_zh_goal_presence_copy_is_localized(self) -> None:
        """Chinese goal UI labels should not fall back to raw English values."""
        with patch("nblane.core.llm._UI_LANG", "zh"):
            ui = common_ui()

        self.assertEqual(ui["goal_strip_focus"], "当前重点")
        self.assertEqual(ui["goal_visibility_visible"], "完整显示")
        self.assertEqual(ui["goal_visibility_discreet"], "低调显示")
        self.assertEqual(ui["goal_visibility_hidden"], "只显示已设置")
        self.assertEqual(ui["goal_visibility_private"], "私密")
        self.assertEqual(ui["goal_presence_current"], "当前目标")

    def test_home_applies_language_before_building_ui(self) -> None:
        """Home must sync session language before reading i18n strings."""
        source = (Path(__file__).resolve().parent.parent / "app.py").read_text(
            encoding="utf-8"
        )

        self.assertLess(
            source.index("_sync_home_ui()\n\nst.set_page_config("),
            source.index("st.set_page_config("),
        )
        self.assertIn(
            "selected = select_profile()\n    _sync_home_ui()\n"
            "    render_git_backup_notices()",
            source,
        )
        # main() must gate before nav, seed the language, and sync Home copy
        # all before st.navigation builds the sidebar, so nav labels render in
        # the right language on the first paint. Assert ordering rather than an
        # exact adjacency so intervening lines (the login gate, comments) don't
        # make this brittle.
        nav_pos = source.index("page = st.navigation(")
        gate_pos = source.index("render_login_gate()")
        seed_pos = source.index("seed_ui_language_before_nav()\n    _sync_home_ui()")
        self.assertLess(gate_pos, nav_pos)
        self.assertLess(seed_pos, nav_pos)

    def test_page_ui_refreshes_after_sidebar_language(self) -> None:
        """Pages must refresh UI strings after sidebar settings are applied."""
        root = Path(__file__).resolve().parent.parent
        expectations = {
            "pages/1_Skill_Tree.py": "selected = select_profile()\nui = skill_tree_ui()",
            "pages/2_Gap_Analysis.py": "selected = select_profile()\nui = gap_ui()",
            "pages/2_Evidence_Review.py": "selected = select_profile()\nui = evidence_review_ui()",
            "pages/3_Kanban.py": "selected = select_profile()\nui = kanban_ui()",
            "pages/4_Team_View.py": "selected_profile = select_profile()\nui = team_ui()",
            "pages/5_Profile_Health.py": "selected = select_profile()\nui = profile_health_ui()",
            "pages/6_Public_Site.py": "selected = select_profile()\nui = _ui()",
            "pages/7_Research.py": "selected = select_profile()\nui = research_ui()",
            "pages/8_Review.py": "selected = select_profile()\nui = review_ui()",
            "pages/9_Agent_Activity.py": "selected = select_profile()\nui = agent_activity_ui()",
            "src/nblane/web_output_studio.py": "selected = select_profile()\n    ui = _ui()",
            "src/nblane/web_public_build.py": "selected = select_profile()\n    ui = _ui()",
        }
        for relative, snippet in expectations.items():
            source = (root / relative).read_text(encoding="utf-8")
            self.assertIn(snippet, source, relative)

    def test_language_widgets_use_persistent_session_keys(self) -> None:
        """Sidebar language widgets must not be page-local source of truth."""
        source = (
            Path(__file__).resolve().parent.parent
            / "src"
            / "nblane"
            / "web_shared.py"
        ).read_text(encoding="utf-8")

        self.assertIn('_UI_LANG_KEY = "nblane_ui_lang"', source)
        self.assertIn('_UI_LANG_WIDGET_KEY = "_nblane_ui_lang"', source)
        self.assertIn(
            "on_change=_sync_language_widget_to_persistent",
            source,
        )
        self.assertIn(
            "st.session_state[_UI_LANG_KEY] = ui_lang",
            source,
        )


if __name__ == "__main__":
    unittest.main()
