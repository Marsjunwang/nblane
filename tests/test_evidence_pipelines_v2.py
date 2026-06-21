"""Tests for Phase 2: pipeline prompts emit v2 fields + project suggestions."""

from __future__ import annotations

import unittest

from nblane.core.evidence_migrate import suggest_projects_from_evidence
from nblane.core.profile_ingest_llm import (
    _format_done_tasks,
    _system_prompt_kanban_en,
    _system_prompt_kanban_zh,
    _system_prompt_resume_en,
    _system_prompt_resume_zh,
)
from nblane.core.models import KanbanTask


class TestKanbanPromptV2(unittest.TestCase):
    def test_kanban_prompts_mention_v2_fields(self) -> None:
        for prompt in (_system_prompt_kanban_en(), _system_prompt_kanban_zh()):
            self.assertIn("origin", prompt)
            self.assertIn("original_content", prompt)
            self.assertIn("formatted_content", prompt)
            self.assertIn("kanban_task", prompt)

    def test_resume_prompts_mention_v2_fields(self) -> None:
        for prompt in (_system_prompt_resume_en(), _system_prompt_resume_zh()):
            self.assertIn("origin", prompt)
            self.assertIn("resume_parse", prompt)
            self.assertIn("original_content", prompt)
            self.assertIn("formatted_content", prompt)


class TestDoneTaskFormatterV2(unittest.TestCase):
    def test_includes_id_and_project(self) -> None:
        task = KanbanTask(
            title="Latency tuning",
            id="taskA",
            done=True,
            outcome="cut to 20fps",
            project_id="project:perf",
            completed_on="2026-01-02",
        )
        out = _format_done_tasks([task])
        self.assertIn("id: taskA", out)
        self.assertIn("project_id: project:perf", out)
        self.assertIn("outcome: cut to 20fps", out)
        self.assertIn("completed_on: 2026-01-02", out)


class TestSuggestProjects(unittest.TestCase):
    def test_groups_gac_into_one_project(self) -> None:
        rows = [
            {
                "id": "ev_ap_boost",
                "origin": "resume_parse",
                "title": "GAC far-range detection +15 AP",
                "origin_detail": "GAC experience block",
            },
            {
                "id": "ev_training_speedup",
                "origin": "resume_parse",
                "title": "GAC training throughput 2x",
                "origin_detail": "GAC experience block",
            },
            {
                "id": "ev_gaussian_3d",
                "origin": "resume_parse",
                "title": "GAC 3D gaussian perception",
                "origin_detail": "GAC experience block",
            },
        ]
        suggestions = suggest_projects_from_evidence(rows)
        self.assertEqual(len(suggestions), 1)
        s = suggestions[0]
        self.assertEqual(s["suggested_id"], "project:gac")
        self.assertEqual(
            sorted(s["evidence_ids"]),
            ["ev_ap_boost", "ev_gaussian_3d", "ev_training_speedup"],
        )

    def test_skips_rows_with_project(self) -> None:
        rows = [
            {
                "id": "a",
                "origin": "resume_parse",
                "title": "GAC one",
                "project_refs": ["project:gac"],
            },
            {
                "id": "b",
                "origin": "resume_parse",
                "title": "GAC two",
                "project_refs": ["project:gac"],
            },
        ]
        self.assertEqual(suggest_projects_from_evidence(rows), [])

    def test_single_orphan_not_suggested(self) -> None:
        rows = [
            {"id": "a", "origin": "resume_parse", "title": "Solo XYZ project"}
        ]
        self.assertEqual(suggest_projects_from_evidence(rows), [])

    def test_ignores_kanban_origin(self) -> None:
        rows = [
            {"id": "a", "origin": "kanban_task", "title": "GAC x"},
            {"id": "b", "origin": "kanban_task", "title": "GAC y"},
        ]
        self.assertEqual(suggest_projects_from_evidence(rows), [])


if __name__ == "__main__":
    unittest.main()
