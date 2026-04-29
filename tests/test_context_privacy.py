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
understanding_of_user:
  current_focus:
    - ship nblane
  private_notes: do not leak this
working_style:
  prefers:
    - concise plans
  health_notes: also private
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
        self.assertIn("concise plans", prompt)
        self.assertNotIn("do not leak this", prompt)
        self.assertNotIn("also private", prompt)
        self.assertNotIn("hidden value", prompt)
        self.assertNotIn("private workout note", prompt)
        self.assertNotIn("private reading note", prompt)


if __name__ == "__main__":
    unittest.main()
