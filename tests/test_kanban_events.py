"""Tests for pure kanban board event helpers."""

from __future__ import annotations

import unittest
from datetime import date

from nblane.core.kanban_ai import (
    KanbanSubtaskProposal,
    apply_kanban_subtask_proposals,
)
from nblane.core.kanban_events import (
    append_ai_proposal_details,
    alignment_context_from_payload,
    apply_kanban_card_update,
    apply_kanban_subtask_toggle,
    build_quick_add_task,
    discard_subtask_proposal_at,
    discard_task_ai_state,
    event_subtask_index,
    invalid_kanban_card_date_fields,
    subtask_proposals_from_payload,
)
from nblane.core.models import KanbanSubtask, KanbanTask


class TestKanbanEvents(unittest.TestCase):
    """Board event payloads update tasks predictably."""

    def test_apply_card_update_replaces_subtasks_and_filters_empty(self) -> None:
        """Edit mode submits the full subtask list as ordinary items."""
        task = KanbanTask(
            title="Original",
            id="task-1",
            context="old",
            tags="old-tag",
            subtasks=[KanbanSubtask("Old item", done=True)],
            details=["old detail"],
        )

        updated = apply_kanban_card_update(
            task,
            {
                "title": " Updated ",
                "context": " new context ",
                "tags": " GAC ",
                "notes": "line one\n\nline two",
                "started_on": "",
                "completed_on": "2026-04-27",
                "subtasks": [
                    {"title": " Keep ", "done": True},
                    {"title": "Drop because blank", "done": "false"},
                    {"title": " ", "done": True},
                    "String item",
                ],
            },
        )

        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated.title, "Updated")
        self.assertEqual(updated.context, "new context")
        self.assertEqual(updated.tags, "GAC")
        self.assertIsNone(updated.started_on)
        self.assertEqual(updated.completed_on, "2026-04-27")
        self.assertEqual(updated.details, ["line one", "line two"])
        self.assertEqual(
            [(item.title, item.done) for item in updated.subtasks],
            [
                ("Keep", True),
                ("Drop because blank", False),
                ("String item", False),
            ],
        )

    def test_apply_card_update_keeps_subtasks_for_invalid_payload(self) -> None:
        """Malformed subtask values do not accidentally clear the checklist."""
        task = KanbanTask(
            title="Task",
            id="task-1",
            subtasks=[KanbanSubtask("Keep existing", done=True)],
        )

        updated = apply_kanban_card_update(
            task,
            {"context": "new", "subtasks": None},
        )

        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated.context, "new")
        self.assertEqual(
            [(item.title, item.done) for item in updated.subtasks],
            [("Keep existing", True)],
        )

    def test_apply_card_update_can_clear_subtasks_with_empty_list(self) -> None:
        """An intentional empty list removes all subtasks."""
        task = KanbanTask(
            title="Task",
            id="task-1",
            subtasks=[KanbanSubtask("Remove me")],
        )

        updated = apply_kanban_card_update(task, {"subtasks": []})

        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated.subtasks, [])

    def test_apply_card_update_rejects_blank_title(self) -> None:
        """A blank required title rejects the update."""
        self.assertIsNone(
            apply_kanban_card_update(
                KanbanTask(title="Task", id="task-1"),
                {"title": "   "},
            )
        )

    def test_apply_card_update_rejects_invalid_iso_dates(self) -> None:
        """Date fields must be strict YYYY-MM-DD calendar dates."""
        task = KanbanTask(title="Task", id="task-1")

        bad = {
            "started_on": "2026-2-3",
            "completed_on": "2026-02-31",
        }

        self.assertEqual(
            invalid_kanban_card_date_fields(bad),
            ["started_on", "completed_on"],
        )
        self.assertIsNone(apply_kanban_card_update(task, bad))
        self.assertIsNotNone(
            apply_kanban_card_update(
                task,
                {
                    "started_on": "2026-02-03",
                    "completed_on": "",
                },
            )
        )

    def test_apply_card_update_accepts_project_and_milestone(self) -> None:
        """Edit payloads can assign or clear Project Board metadata."""
        task = KanbanTask(title="Task", id="task-1")

        updated = apply_kanban_card_update(
            task,
            {
                "project_id": " project:demo ",
                "milestone_id": " milestone:first ",
            },
        )

        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated.project_id, "project:demo")
        self.assertEqual(updated.milestone_id, "milestone:first")

    def test_apply_card_update_sets_and_clears_agent_task_id(self) -> None:
        """Edit payloads can bind or clear the dispatched agent task."""
        task = KanbanTask(title="Task", id="task-1")
        bound = apply_kanban_card_update(task, {"agent_task_id": " agenttask_x "})
        self.assertIsNotNone(bound)
        assert bound is not None
        self.assertEqual(bound.agent_task_id, "agenttask_x")
        cleared = apply_kanban_card_update(bound, {"agent_task_id": ""})
        self.assertIsNotNone(cleared)
        assert cleared is not None
        self.assertEqual(cleared.agent_task_id, "")

    def test_event_subtask_index_supports_new_and_old_payloads(self) -> None:
        """Current index and older subtask-id payloads both resolve."""
        task = KanbanTask(
            title="Task",
            id="task-1",
            subtasks=[KanbanSubtask("A"), KanbanSubtask("B")],
        )

        self.assertEqual(event_subtask_index({"subtask_index": 1}, task), 1)
        self.assertEqual(event_subtask_index({"subtask_id": "subtask-0"}, task), 0)
        self.assertEqual(event_subtask_index({"subtask_index": 4}, task), -1)

    def test_apply_subtask_toggle_updates_by_index_and_title(self) -> None:
        """Read-mode checkbox toggles only the intended subtask."""
        sections = {
            "Doing": [
                KanbanTask(
                    title="Task",
                    id="task-1",
                    context="keep context",
                    started_on="2026-04-01",
                    subtasks=[
                        KanbanSubtask("A", done=False),
                        KanbanSubtask("B", done=True),
                    ],
                    details=["keep detail"],
                )
            ],
            "Queue": [KanbanTask(title="Other", id="task-2")],
        }

        updated, ok = apply_kanban_subtask_toggle(
            sections,
            "task-1",
            0,
            "A",
            True,
        )

        self.assertTrue(ok)
        self.assertFalse(sections["Doing"][0].subtasks[0].done)
        task = updated["Doing"][0]
        self.assertEqual(task.context, "keep context")
        self.assertEqual(task.started_on, "2026-04-01")
        self.assertEqual(task.details, ["keep detail"])
        self.assertTrue(task.subtasks[0].done)
        self.assertTrue(task.subtasks[1].done)
        self.assertEqual(updated["Queue"][0].title, "Other")

    def test_apply_subtask_toggle_falls_back_to_unique_title(self) -> None:
        """A stale index can still update when title uniquely identifies the row."""
        sections = {
            "Doing": [
                KanbanTask(
                    title="Task",
                    id="task-1",
                    subtasks=[
                        KanbanSubtask("A", done=False),
                        KanbanSubtask("B", done=False),
                    ],
                )
            ],
        }

        updated, ok = apply_kanban_subtask_toggle(
            sections,
            "task-1",
            0,
            "B",
            True,
        )

        self.assertTrue(ok)
        self.assertFalse(updated["Doing"][0].subtasks[0].done)
        self.assertTrue(updated["Doing"][0].subtasks[1].done)

    def test_apply_subtask_toggle_rejects_ambiguous_title(self) -> None:
        """Ambiguous stale payloads do not update the wrong checkbox."""
        sections = {
            "Doing": [
                KanbanTask(
                    title="Task",
                    id="task-1",
                    subtasks=[
                        KanbanSubtask("A", done=False),
                        KanbanSubtask("B", done=False),
                        KanbanSubtask("B", done=False),
                    ],
                )
            ],
        }

        updated, ok = apply_kanban_subtask_toggle(
            sections,
            "task-1",
            0,
            "B",
            True,
        )

        self.assertFalse(ok)
        self.assertEqual(updated, sections)
        self.assertFalse(sections["Doing"][0].subtasks[1].done)
        self.assertFalse(sections["Doing"][0].subtasks[2].done)

    def test_alignment_context_from_payload(self) -> None:
        """Confirmed candidate plus user clarification become prompt context."""
        context = alignment_context_from_payload(
            {
                "alignment": {
                    "label": "Small slice",
                    "goal": "Ship one reviewable note",
                    "assumptions": ["One paper only", ""],
                    "subtask_style": "artifact checklist",
                },
                "custom_context": "Include acceptance criteria.",
            }
        )

        self.assertIn("Label: Small slice", context)
        self.assertIn("Goal: Ship one reviewable note", context)
        self.assertIn("Assumptions: One paper only", context)
        self.assertIn("Subtask style: artifact checklist", context)
        self.assertIn("User clarification: Include acceptance criteria.", context)

    def test_other_alignment_uses_only_custom_context(self) -> None:
        """Other alignment payloads do not mix in the first model candidate."""
        context = alignment_context_from_payload(
            {
                "alignment_kind": "other",
                "alignment": {
                    "label": "Wrong default",
                    "goal": "Use the default candidate",
                },
                "custom_context": "家庭机器人鞋子摆放测试闭环",
            }
        )

        self.assertEqual(
            context,
            "User clarification: 家庭机器人鞋子摆放测试闭环",
        )

    def test_alignment_context_supports_multiple_edited_understandings(self) -> None:
        """Multi-select alignment payloads use edited candidate text."""
        context = alignment_context_from_payload(
            {
                "alignment_mode": "selected_plus_custom",
                "granularity": "milestone",
                "selected_alignments": [
                    {
                        "label": "里程碑复现",
                        "goal": "完成 iup-pose 训练到评测的复现闭环",
                        "assumptions": ["a800 -> 4090", "保持高层粒度"],
                        "subtask_style": "训练、评测、对齐、记录差异",
                    },
                    {
                        "label": "时间对齐",
                        "goal": "对齐 baseline 效果和训练时间",
                        "assumptions": "不要生成脚本名\n不要下钻到 env_check.py",
                    },
                ],
                "custom_context": "只拆到阶段检查点。",
            }
        )

        self.assertIn("Selected understanding 1:", context)
        self.assertIn("Label: 里程碑复现", context)
        self.assertIn("Assumptions: a800 -> 4090; 保持高层粒度", context)
        self.assertIn("Selected understanding 2:", context)
        self.assertIn("不要生成脚本名; 不要下钻到 env_check.py", context)
        self.assertIn("Granularity: milestone", context)
        self.assertIn("User clarification: 只拆到阶段检查点。", context)

    def test_custom_only_alignment_ignores_selected_candidates(self) -> None:
        """Custom-only mode uses the user's supplement alone."""
        context = alignment_context_from_payload(
            {
                "alignment_mode": "custom_only",
                "selected_alignments": [
                    {"label": "Wrong", "goal": "Use this candidate"}
                ],
                "custom_context": "只按我的理解生成。",
            }
        )

        self.assertEqual(context, "User clarification: 只按我的理解生成。")

    def test_alignment_context_requires_understanding_or_custom_text(self) -> None:
        """Granularity alone is not enough to confirm task understanding."""
        self.assertEqual(
            alignment_context_from_payload(
                {
                    "alignment_mode": "custom_only",
                    "granularity": "milestone",
                    "custom_context": "",
                }
            ),
            "",
        )
        self.assertEqual(
            alignment_context_from_payload(
                {
                    "alignment_mode": "selected_plus_custom",
                    "selected_alignments": [],
                    "granularity": "milestone",
                }
            ),
            "",
        )

    def test_subtask_proposals_from_payload_uses_edited_selected_drafts(self) -> None:
        """Draft apply payloads keep edited titles, metadata, and selection."""
        proposals = subtask_proposals_from_payload(
            {
                "drafts": [
                    {
                        "index": 0,
                        "title": " 跑通完整训练评测 ",
                        "selected": True,
                        "artifact": "report.md",
                        "verification": "reviewed by human",
                    },
                    {
                        "index": 1,
                        "title": "不要应用这一条",
                        "selected": False,
                    },
                    {"index": 2, "title": " "},
                    "对齐 baseline 效果和训练时间",
                    "对齐 baseline 效果和训练时间",
                ]
            },
            "task-1",
        )

        self.assertEqual(
            [proposal.title for proposal in proposals],
            ["跑通完整训练评测", "对齐 baseline 效果和训练时间"],
        )
        self.assertEqual(proposals[0].artifact, "report.md")
        self.assertEqual(proposals[0].verification, "reviewed by human")
        self.assertTrue(all(proposal.task_id == "task-1" for proposal in proposals))

    def test_append_ai_proposal_details_preserves_artifact_metadata(self) -> None:
        """Applied AI proposal metadata is retained on the task details."""
        task = KanbanTask(title="Task", id="task-1", details=["existing"])

        updated = append_ai_proposal_details(
            task,
            [
                KanbanSubtaskProposal(
                    title="Run eval",
                    artifact="eval.md",
                    verification="metrics reviewed",
                    task_id="task-1",
                ),
                KanbanSubtaskProposal(
                    title="No metadata",
                    task_id="task-1",
                ),
            ],
        )
        updated_again = append_ai_proposal_details(
            updated,
            [
                KanbanSubtaskProposal(
                    title="Run eval",
                    artifact="eval.md",
                    verification="metrics reviewed",
                    task_id="task-1",
                )
            ],
        )

        self.assertEqual(
            updated.details,
            [
                "existing",
                (
                    "AI subtask: Run eval | Artifact: eval.md | "
                    "Verification: metrics reviewed"
                ),
            ],
        )
        self.assertEqual(updated_again.details, updated.details)

    def test_subtask_proposals_from_payload_supports_legacy_titles(self) -> None:
        """Older static component title payloads remain supported."""
        proposals = subtask_proposals_from_payload(
            {"titles": [" First ", "", "Second"]},
            "task-1",
        )

        self.assertEqual([proposal.title for proposal in proposals], ["First", "Second"])

    def test_discard_ai_drafts_helpers(self) -> None:
        """Session-only AI drafts can be removed individually or by task."""
        proposals = {
            "task-1": [
                KanbanSubtaskProposal("A"),
                KanbanSubtaskProposal("B"),
            ],
            "task-2": [KanbanSubtaskProposal("C")],
        }
        alignments = {"task-1": ["alignment"]}
        errors = {"task-1": ["error"]}

        self.assertTrue(discard_subtask_proposal_at(proposals, "task-1", 0))
        self.assertEqual([item.title for item in proposals["task-1"]], ["B"])
        self.assertFalse(discard_subtask_proposal_at(proposals, "task-1", 9))

        changed = discard_task_ai_state(
            proposals,
            alignments,
            errors,
            "task-1",
            scope="all",
        )

        self.assertTrue(changed)
        self.assertNotIn("task-1", proposals)
        self.assertNotIn("task-1", alignments)
        self.assertNotIn("task-1", errors)
        self.assertIn("task-2", proposals)

    def test_applied_ai_subtasks_can_be_removed_by_card_update(self) -> None:
        """AI-applied subtasks use the same full-list edit path as manual ones."""
        sections = {
            "Doing": [
                KanbanTask(
                    title="Task",
                    id="task-1",
                    subtasks=[KanbanSubtask("Keep existing", done=True)],
                )
            ]
        }
        out = apply_kanban_subtask_proposals(
            sections,
            "task-1",
            [KanbanSubtaskProposal(title="AI generated item", task_id="task-1")],
        )

        updated = apply_kanban_card_update(
            out["Doing"][0],
            {"subtasks": [{"title": "Keep existing", "done": True}]},
        )

        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(
            [(item.title, item.done) for item in updated.subtasks],
            [("Keep existing", True)],
        )


class TestBuildQuickAddTask(unittest.TestCase):
    """NL quick-add intents build structured cards; plain text stays plain."""

    def test_intent_with_due_tags_column_builds_structured_card(self) -> None:
        section, task, intent = build_quick_add_task(
            "把评审 Narwal 论文加到 Queue #papers 周五前",
            section="Doing",
            today=date(2026, 9, 16),
        )
        self.assertEqual(intent.kind, "kanban.add")
        self.assertEqual(section, "Queue")
        self.assertEqual(task.title, "评审 Narwal 论文")
        self.assertEqual(task.tags, "papers")
        self.assertIn("due: 2026-09-18", task.details)
        self.assertFalse(task.done)

    def test_intent_doing_gets_started_on_only_with_auto_dates(self) -> None:
        section, task, _ = build_quick_add_task(
            "新增任务 修 bug #backend 明天前",
            section="Queue",
            auto_dates=True,
            today=date(2026, 9, 16),
        )
        self.assertEqual(section, "Doing")
        self.assertEqual(task.started_on, "2026-09-16")
        _s2, task_no_dates, _i2 = build_quick_add_task(
            "新增任务 修 bug #backend 明天前",
            section="Queue",
            auto_dates=False,
            today=date(2026, 9, 16),
        )
        self.assertIsNone(task_no_dates.started_on)
        self.assertEqual(task_no_dates.tags, "backend")

    def test_plain_title_keeps_legacy_behavior(self) -> None:
        section, task, intent = build_quick_add_task(
            "just a plain title",
            section="Queue",
            context="ctx",
            notes="line one\nline two",
            today=date(2026, 9, 16),
        )
        self.assertEqual(intent.kind, "unknown")
        self.assertEqual(section, "Queue")
        self.assertEqual(task.title, "just a plain title")
        self.assertEqual(task.context, "ctx")
        self.assertEqual(task.details, ["line one", "line two"])

    def test_done_section_legacy_marks_done_with_date(self) -> None:
        section, task, _ = build_quick_add_task(
            "wrap up notes",
            section="Done",
            today=date(2026, 9, 16),
        )
        self.assertEqual(section, "Done")
        self.assertTrue(task.done)
        self.assertEqual(task.completed_on, "2026-09-16")

    def test_notes_merge_after_due_detail(self) -> None:
        section, task, _ = build_quick_add_task(
            "加到 Queue 写文档 #docs 后天前",
            section="Queue",
            notes="extra note",
            today=date(2026, 9, 16),
        )
        self.assertEqual(task.details, ["due: 2026-09-18", "extra note"])


if __name__ == "__main__":
    unittest.main()
