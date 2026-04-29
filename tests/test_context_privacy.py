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


if __name__ == "__main__":
    unittest.main()
