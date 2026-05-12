"""Tests for context generation privacy boundaries."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.context import generate


class TestContextPrivacy(unittest.TestCase):
    """Context keeps Kanban while redacting private agent-profile fields."""

    def test_agent_profile_private_fields_are_not_in_context(self) -> None:
        """Private notes and health notes are dropped before prompt assembly."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "alice"
            profile.mkdir()
            (profile / "SKILL.md").write_text(
                "# Alice\n\nPublic skill profile.",
                encoding="utf-8",
            )
            (profile / "agent-profile.yaml").write_text(
                """
schema_version: "1.0"
understanding_of_user:
  strengths:
    - systems thinking
  weaknesses:
    - impatience
  current_focus:
    - ship nblane
  private_notes: do not leak this
working_style:
  prefers:
    - concise plans
    - label: nested public text
      private_notes: nested private text
  avoids:
    - vague advice
  health_notes: also private
confidence: 0.7
custom_private: hidden value
""",
                encoding="utf-8",
            )
            (profile / "kanban.md").write_text(
                "# Alice · Kanban\n\n## Doing\n\n- [ ] Keep kanban visible\n",
                encoding="utf-8",
            )
            (profile / "activity-log.yaml").write_text(
                "checkins:\n  - note: private workout note\n",
                encoding="utf-8",
            )
            (profile / "learning-log.yaml").write_text(
                "resources:\n  - summary: private reading note\n",
                encoding="utf-8",
            )
            with patch("nblane.core.context.PROFILES_DIR", root):
                prompt = generate("alice")

        self.assertIn("Keep kanban visible", prompt)
        self.assertIn("schema_version:", prompt)
        self.assertIn("systems thinking", prompt)
        self.assertIn("impatience", prompt)
        self.assertIn("concise plans", prompt)
        self.assertIn("vague advice", prompt)
        self.assertIn("confidence: 0.7", prompt)
        self.assertNotIn("do not leak this", prompt)
        self.assertNotIn("also private", prompt)
        self.assertNotIn("hidden value", prompt)
        self.assertNotIn("nested private text", prompt)
        self.assertNotIn("nested public text", prompt)
        self.assertNotIn("private workout note", prompt)
        self.assertNotIn("private reading note", prompt)

    def test_invalid_agent_profile_yaml_is_skipped(self) -> None:
        """Malformed agent-profile.yaml does not leak parser text or raw YAML."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "alice"
            profile.mkdir()
            (profile / "SKILL.md").write_text(
                "# Alice\n\nPublic skill profile.",
                encoding="utf-8",
            )
            (profile / "agent-profile.yaml").write_text(
                "understanding_of_user: [\nprivate_notes: hidden\n",
                encoding="utf-8",
            )
            with patch("nblane.core.context.PROFILES_DIR", root):
                prompt = generate("alice")

        self.assertNotIn("## Agent profile", prompt)
        self.assertNotIn("private_notes", prompt)
        self.assertNotIn("hidden", prompt)

    def test_current_goal_enters_context_when_allowed(self) -> None:
        """Visible/discreet/hidden UI modes do not block Agent context."""
        for visibility in ("visible", "discreet", "hidden"):
            with self.subTest(visibility=visibility):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    profile = root / "alice"
                    profile.mkdir()
                    (profile / "SKILL.md").write_text(
                        "# Alice\n\nPublic skill profile.",
                        encoding="utf-8",
                    )
                    (profile / "goals.yaml").write_text(
                        f"""
schema_version: "1.0"
profile: alice
current_goal_id: g
goals:
  - id: g
    title: Ship current goal
    label: Safe stage goal
    ui_visibility: {visibility}
    include_in_agent_context: true
    summary: Agent-visible summary
    focus:
      - Goal focus item
""",
                        encoding="utf-8",
                    )
                    with patch("nblane.core.context.PROFILES_DIR", root):
                        prompt = generate("alice")

                self.assertIn("## Current Goal", prompt)
                self.assertIn("Ship current goal", prompt)
                self.assertIn("Agent-visible summary", prompt)
                self.assertIn("Goal focus item", prompt)

    def test_current_goal_excluded_when_agent_context_disabled(self) -> None:
        """include_in_agent_context controls context independently of UI."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "alice"
            profile.mkdir()
            (profile / "SKILL.md").write_text(
                "# Alice\n\nPublic skill profile.",
                encoding="utf-8",
            )
            (profile / "goals.yaml").write_text(
                """
schema_version: "1.0"
profile: alice
current_goal_id: g
goals:
  - id: g
    title: Excluded current goal
    ui_visibility: visible
    include_in_agent_context: false
""",
                encoding="utf-8",
            )
            with patch("nblane.core.context.PROFILES_DIR", root):
                prompt = generate("alice")

        self.assertNotIn("## Current Goal", prompt)
        self.assertNotIn("Excluded current goal", prompt)

    def test_private_current_goal_never_enters_context(self) -> None:
        """Private goal details stay out even if the YAML flag is true."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "alice"
            profile.mkdir()
            (profile / "SKILL.md").write_text(
                "# Alice\n\nPublic skill profile.",
                encoding="utf-8",
            )
            (profile / "goals.yaml").write_text(
                """
schema_version: "1.0"
profile: alice
current_goal_id: g
goals:
  - id: g
    title: Sensitive private goal
    label: Sensitive label
    ui_visibility: private
    include_in_agent_context: true
    summary: Sensitive summary
    focus:
      - Sensitive focus
    notes: Sensitive notes
""",
                encoding="utf-8",
            )
            with patch("nblane.core.context.PROFILES_DIR", root):
                prompt = generate("alice")

        self.assertNotIn("## Current Goal", prompt)
        self.assertNotIn("Sensitive private goal", prompt)
        self.assertNotIn("Sensitive label", prompt)
        self.assertNotIn("Sensitive summary", prompt)
        self.assertNotIn("Sensitive focus", prompt)
        self.assertNotIn("Sensitive notes", prompt)


if __name__ == "__main__":
    unittest.main()
