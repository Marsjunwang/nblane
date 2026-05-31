"""Tests for Skill Tree editor-row dirty detection."""

from __future__ import annotations

import unittest

from nblane.core.skill_tree_edit import (
    rows_dirty,
    rows_to_nodes,
    serialize_rows_for_dirty,
)


def _rows() -> list[dict]:
    return [
        {
            "id": "skill:a",
            "status": "learning",
            "note": "first",
            "evidence": [
                {
                    "type": "practice",
                    "title": "did a thing",
                    "date": "2026-01-01",
                    "url": "",
                    "summary": "",
                }
            ],
            "evidence_refs": ["ev:1", "ev:2"],
            "label": "A",
            "level": 1,
            "category": "core",
        },
        {
            "id": "skill:b",
            "status": "locked",
            "note": "",
            "evidence": [],
            "evidence_refs": [],
            "label": "B",
            "level": 2,
            "category": "core",
        },
    ]


class SkillTreeDirtyTests(unittest.TestCase):
    def test_baseline_none_returns_false(self) -> None:
        self.assertFalse(rows_dirty(None, _rows()))

    def test_identical_rows_not_dirty(self) -> None:
        rows = _rows()
        baseline = serialize_rows_for_dirty(rows)
        self.assertFalse(rows_dirty(baseline, rows))

    def test_status_change_is_dirty(self) -> None:
        rows = _rows()
        baseline = serialize_rows_for_dirty(rows)
        rows[0]["status"] = "done"
        self.assertTrue(rows_dirty(baseline, rows))

    def test_note_change_is_dirty(self) -> None:
        rows = _rows()
        baseline = serialize_rows_for_dirty(rows)
        rows[0]["note"] = "edited"
        self.assertTrue(rows_dirty(baseline, rows))

    def test_row_reorder_not_dirty(self) -> None:
        rows = _rows()
        baseline = serialize_rows_for_dirty(rows)
        rows.reverse()
        self.assertFalse(rows_dirty(baseline, rows))

    def test_empty_title_evidence_roundtrip_not_dirty(self) -> None:
        # Appending an empty-title evidence block to an already-materialized
        # node is cleaned out by the save projection, so it must not be dirty.
        rows = _rows()
        baseline = serialize_rows_for_dirty(rows)
        rows[0]["evidence"].append(
            {"type": "practice", "title": "", "date": "", "url": "", "summary": ""}
        )
        self.assertFalse(rows_dirty(baseline, rows))

    def test_evidence_on_locked_empty_node_is_dirty(self) -> None:
        # Adding evidence to a locked+empty node materializes it on save,
        # so the projection genuinely changes -> correctly dirty.
        rows = _rows()
        baseline = serialize_rows_for_dirty(rows)
        rows[1]["evidence"].append(
            {"type": "practice", "title": "", "date": "", "url": "", "summary": ""}
        )
        self.assertTrue(rows_dirty(baseline, rows))

    def test_filling_evidence_title_is_dirty(self) -> None:
        rows = _rows()
        baseline = serialize_rows_for_dirty(rows)
        rows[1]["evidence"].append(
            {"type": "practice", "title": "new", "date": "", "url": "", "summary": ""}
        )
        self.assertTrue(rows_dirty(baseline, rows))

    def test_locked_empty_toggle_roundtrip_not_dirty(self) -> None:
        rows = _rows()
        baseline = serialize_rows_for_dirty(rows)
        rows[1]["status"] = "learning"
        rows[1]["status"] = "locked"
        self.assertFalse(rows_dirty(baseline, rows))

    def test_evidence_ref_reorder_is_dirty(self) -> None:
        rows = _rows()
        baseline = serialize_rows_for_dirty(rows)
        rows[0]["evidence_refs"] = ["ev:2", "ev:1"]
        self.assertTrue(rows_dirty(baseline, rows))

    def test_serialize_is_stable(self) -> None:
        rows = _rows()
        self.assertEqual(
            serialize_rows_for_dirty(rows), serialize_rows_for_dirty(rows)
        )

    def test_display_only_field_change_not_dirty(self) -> None:
        rows = _rows()
        baseline = serialize_rows_for_dirty(rows)
        rows[0]["label"] = "renamed"
        rows[0]["level"] = 99
        self.assertFalse(rows_dirty(baseline, rows))

    def test_rows_to_nodes_drops_locked_empty(self) -> None:
        nodes = rows_to_nodes(_rows())
        ids = [n["id"] for n in nodes]
        self.assertIn("skill:a", ids)
        self.assertNotIn("skill:b", ids)


if __name__ == "__main__":
    unittest.main()
