"""Tests for interaction record append (JSONL + git backup)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.interaction import append_interaction_record


class TestInteraction(unittest.TestCase):
    """Appended JSONL records trigger the git backup hook."""

    def test_append_records_backup(self) -> None:
        """Each appended record is followed by git_backup.record_change."""
        with tempfile.TemporaryDirectory() as tmp:
            prof = Path(tmp) / "demo"
            prof.mkdir()
            with patch(
                "nblane.core.interaction.profile_dir",
                lambda _name: prof,
            ), patch(
                "nblane.core.interaction.git_backup.record_change"
            ) as record:
                path = append_interaction_record(
                    "demo",
                    question="What moved?",
                    answer="Kanban card X",
                    skill_ids=["skill_a", " skill_b "],
                )

            record.assert_called_once()
            self.assertEqual(record.call_args[0][0], [path])
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            data = json.loads(lines[0])
            self.assertEqual(data["question"], "What moved?")
            self.assertEqual(data["answer"], "Kanban card X")
            self.assertEqual(data["skill_ids"], ["skill_a", "skill_b"])


if __name__ == "__main__":
    unittest.main()
