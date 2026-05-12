"""Tests for Profile Context / SKILL.md editing helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from nblane.core.profile_context import (
    apply_profile_context_structured_edits,
    extract_generated_blocks,
    parse_identity_fields,
    section_body,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_SKILL = REPO_ROOT / "profiles" / "template" / "SKILL.md"


class TestProfileContextEditor(unittest.TestCase):
    """Human-owned SKILL.md edits stay scoped."""

    def test_identity_field_round_trip_updates_only_bullet_value(self) -> None:
        """Identity fields parse and replace by exact bullet label."""
        text = TEMPLATE_SKILL.read_text(encoding="utf-8")
        parsed = parse_identity_fields(text)
        self.assertEqual(parsed["Name"], "{Name}")
        self.assertIn("Robotics", parsed["Domain"])

        updated = apply_profile_context_structured_edits(
            text,
            identity_fields={
                "Name": "Alice",
                "Domain": "Robotics / Embodied AI",
                "Journey": "Year 2 of 5",
                "Current Role": "Research engineer",
                "North Star": "Build useful real-world robot learning systems.",
            },
        )
        next_parsed = parse_identity_fields(updated)
        self.assertEqual(next_parsed["Name"], "Alice")
        self.assertEqual(next_parsed["Current Role"], "Research engineer")
        self.assertIn(
            "- **North Star**: Build useful real-world robot learning systems.",
            updated,
        )

    def test_narrative_save_preserves_generated_blocks(self) -> None:
        """Structured Profile Context writes do not edit generated blocks."""
        text = TEMPLATE_SKILL.read_text(encoding="utf-8")
        before_blocks = extract_generated_blocks(text)
        updated = apply_profile_context_structured_edits(
            text,
            identity_fields={"Name": "Alice"},
            narrative_sections={
                "Research Fingerprint": (
                    "\n**Papers I keep returning to**:\n"
                    "- Diffusion Policy — action chunking taste\n\n---\n\n"
                ),
                "Thinking & Communication Style": (
                    "\n- I explain intuition before formalism\n"
                    "- I keep technical nouns precise\n\n---\n\n"
                ),
            },
        )

        after_blocks = extract_generated_blocks(updated)
        self.assertEqual(after_blocks["skill_tree"], before_blocks["skill_tree"])
        self.assertEqual(
            after_blocks["current_focus"],
            before_blocks["current_focus"],
        )
        self.assertIn("Diffusion Policy", section_body(updated, "Research Fingerprint"))
        self.assertIn("Alice", section_body(updated, "Identity"))


if __name__ == "__main__":
    unittest.main()
