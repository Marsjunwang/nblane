"""Tests for Profile Context / SKILL.md editing helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from nblane.core.profile_context import (
    apply_profile_context_structured_edits,
    extract_generated_blocks,
    north_star_context_from_identity,
    north_star_payload_from_identity,
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
        self.assertEqual(
            next_parsed["North Star Visibility"],
            "discreet",
        )

    def test_north_star_brief_and_visibility_round_trip(self) -> None:
        """North Star display metadata lives in Identity bullets."""
        text = TEMPLATE_SKILL.read_text(encoding="utf-8")
        updated = apply_profile_context_structured_edits(
            text,
            identity_fields={
                "North Star": "Build useful real-world robot learning systems.",
                "North Star Brief": "Useful robot learning systems.",
                "North Star Visibility": "hidden",
            },
        )
        identity = parse_identity_fields(updated)

        self.assertEqual(
            identity["North Star Brief"],
            "Useful robot learning systems.",
        )
        self.assertEqual(identity["North Star Visibility"], "hidden")
        payload = north_star_payload_from_identity(identity)
        self.assertTrue(payload["is_set"])
        self.assertEqual(payload["visibility"], "hidden")
        self.assertEqual(payload["display_text"], "North Star set")
        self.assertEqual(
            north_star_context_from_identity(identity, for_agent=True),
            "Build useful real-world robot learning systems.",
        )

    def test_private_north_star_redacts_payload_and_agent_context(self) -> None:
        """Private North Star does not expose its text to payload/context."""
        identity = {
            "North Star": "Sensitive five-year direction",
            "North Star Brief": "Safe brief",
            "North Star Visibility": "private",
        }
        payload = north_star_payload_from_identity(identity)

        self.assertTrue(payload["is_set"])
        self.assertTrue(payload["locked"])
        self.assertEqual(payload["display_text"], "")
        self.assertEqual(north_star_context_from_identity(identity), "")
        self.assertEqual(
            north_star_context_from_identity(identity, for_agent=True),
            "",
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
