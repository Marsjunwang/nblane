"""Tests for internal experience-case helpers."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core.experience import (
    ExperienceBook,
    add_experience_case,
    archive_experience_case,
    load_experience_book,
    save_experience_book,
    update_experience_case,
)


class _FakeDate:
    @staticmethod
    def today() -> date:
        return date(2026, 5, 13)


class TestExperienceBook(unittest.TestCase):
    """Experience cases hold private resume context."""

    def test_add_update_archive_and_project_refs_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "alice"
            profile.mkdir()
            book = ExperienceBook(profile="alice")
            case = add_experience_case(
                book,
                "OpenAI",
                role="Research Engineer",
                project_refs=["project:nblane", "project:nblane"],
                source_refs=["source:research:20260513-001"],
            )
            self.assertEqual(case.id, "experience:openai-research-engineer")

            update_experience_case(
                book,
                case.id,
                location="San Francisco",
                status="completed",
            )
            archive_experience_case(book, case.id)

            with patch("nblane.core.experience.date", _FakeDate):
                save_experience_book(profile, book)

            loaded = load_experience_book(profile)
            saved = yaml.safe_load(
                (profile / "experience.yaml").read_text(encoding="utf-8")
            )

        self.assertEqual(saved["updated"], "2026-05-13")
        self.assertEqual(loaded.experience_cases[0].status, "archived")
        self.assertEqual(loaded.experience_cases[0].location, "San Francisco")
        self.assertEqual(loaded.experience_cases[0].project_refs, ["project:nblane"])

    def test_duplicate_id_rejected(self) -> None:
        book = ExperienceBook(profile="alice")
        add_experience_case(book, "OpenAI", case_id="experience:openai")
        with self.assertRaises(ValueError):
            add_experience_case(book, "OpenAI", case_id="experience:openai")


if __name__ == "__main__":
    unittest.main()
