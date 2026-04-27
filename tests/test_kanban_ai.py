"""Tests for kanban AI service helpers."""

from __future__ import annotations

import unittest
import tempfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from nblane.core.kanban_ai import (
    KanbanSubtaskProposal,
    _parse_alignments,
    _parse_proposals,
    _parse_proposals_detailed,
    analyze_kanban_task_gap,
    apply_kanban_subtask_proposals,
    build_kanban_ai_context,
    format_kanban_task_for_ai,
    generate_kanban_task_alignment_options,
    generate_kanban_subtask_proposals,
    generate_kanban_subtask_proposals_detailed,
    kanban_task_needs_alignment,
)
from nblane.core.models import GapResult, KanbanSubtask, KanbanTask


class TestKanbanAi(unittest.TestCase):
    """Kanban AI helpers stay pure until apply."""

    def _write_profile_prior(self, root: Path, profile: str = "王军") -> None:
        """Create a tiny profile with VLA and shoe-placement priors."""
        pdir = root / profile
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "kanban-archive.md").write_text(
            """
# 王军 · Kanban archive

## Archived · 2026-04-15

- [x] pi05复现
  - context: vla算法
  - outcome: 提交台架搭建及部署最新代码，支持同事复用
  - crystallized: true
  - [x] 使用已经采集的数据复现现有方案作为baseline

- [x] 将spatial forcing的vggt监督加入到openpi模型中
  - context: 3d增强vla
  - crystallized: true
  - [x] 实现openpi0.5 baseline实现
  - [x] 增加vggt监督

- [x] 临时任务，修复桌面piper鞋子摆放及物品收纳
  - context: 给投资人演示桌面摆放
  - crystallized: true
  - [x] 测试现有模型性能：鞋子摆放 70%
""",
            encoding="utf-8",
        )
        (pdir / "evidence-pool.yaml").write_text(
            """
profile: 王军
evidence_entries:
- id: ev_piper_repro
  type: project
  title: PI0.5 Reproduction on Piper Arm
  summary: Reproduced PI0.5 on a Piper robotic arm.
- id: ev_spatial_forcing_vggt
  type: practice
  title: Integrated spatial forcing with VGGT supervision into OpenPI model
  summary: Added VGGT supervision to a 3D-augmented VLA training loop.
- id: ev_shoe_benchmark_new
  type: practice
  title: 家庭鞋子抓取摆放 benchmark
  summary: Defined home-robot shoe placement challenge scenarios.
""",
            encoding="utf-8",
        )
        (pdir / "skill-tree.yaml").write_text(
            """
schema: robotics-engineer
nodes:
- id: vlm_robot
  status: learning
  evidence_refs: [ev_spatial_forcing_vggt, ev_piper_repro]
- id: real_robot_ops
  status: solid
  evidence_refs: [ev_piper_repro]
""",
            encoding="utf-8",
        )
        (pdir / "SKILL.md").write_text(
            """
## Identity
- **Domain**: 具身和自动驾驶
- **Current Role**: 具身算法工程师

| VLA 及大模型 | learning | 正在补齐数据采集、数据构建、模型微调与整体训练链路能力 |

## Research Fingerprint
- 我重视方法在工程上的可落地性。
""",
            encoding="utf-8",
        )

    def test_format_kanban_task_for_ai_includes_context(self) -> None:
        """Task fields, subtasks, and details are rendered for prompts."""
        task = KanbanTask(
            title="Ship VLA demo",
            id="task-1",
            context="robot arm",
            why="portfolio evidence",
            outcome="repeatable demo",
            blocked_by="dataset",
            subtasks=[
                KanbanSubtask("Collect episodes", done=True),
                KanbanSubtask("Train policy"),
            ],
            details=["Use OpenVLA baseline"],
        )

        out = format_kanban_task_for_ai(task)

        self.assertIn("Title: Ship VLA demo", out)
        self.assertIn("Task id: task-1", out)
        self.assertIn("Context: robot arm", out)
        self.assertIn("- [x] Collect episodes", out)
        self.assertIn("- [ ] Train policy", out)
        self.assertIn("- Use OpenVLA baseline", out)

    @patch("nblane.core.kanban_ai.gap.analyze")
    def test_analyze_locates_by_task_id_and_disables_persist(
        self, mock_analyze
    ) -> None:
        """Gap analysis uses stable task ids and default no persistence."""
        mock_analyze.return_value = GapResult(task="ok")
        sections = {
            "Doing": [
                KanbanTask(title="Wrong", id="task-a"),
                KanbanTask(title="Right", id="task-b"),
            ]
        }

        result = analyze_kanban_task_gap("template", sections, "task-b")

        self.assertEqual(result.task, "ok")
        mock_analyze.assert_called_once()
        args, kwargs = mock_analyze.call_args
        self.assertEqual(args[0], "template")
        self.assertIn("Title: Right", args[1])
        self.assertEqual(args[2], None)
        self.assertFalse(kwargs["persist_router_keywords"])

    def test_analyze_missing_task_returns_gap_error(self) -> None:
        """Missing ids produce a structured GapResult error."""
        result = analyze_kanban_task_gap(
            "template",
            {"Doing": [KanbanTask(title="A", id="a")]},
            "missing",
        )

        self.assertEqual(result.error_key, "task_not_found")
        self.assertIn("missing", result.error or "")

    def test_task_alignment_needed_only_for_thin_tasks(self) -> None:
        """Title-only tasks ask for alignment; contextual tasks can draft."""
        self.assertTrue(
            kanban_task_needs_alignment(
                KanbanTask(title="Paper reading", id="task-1")
            )
        )
        self.assertFalse(
            kanban_task_needs_alignment(
                KanbanTask(
                    title="Paper reading",
                    id="task-1",
                    context="Read RT-2 and write takeaways",
                )
            )
        )
        self.assertFalse(
            kanban_task_needs_alignment(
                KanbanTask(
                    title="Baseline",
                    id="task-2",
                    subtasks=[KanbanSubtask("Run pytest")],
                )
            )
        )

    def test_parse_alignment_options(self) -> None:
        """Alignment parsing keeps concise task-understanding choices."""
        reply = """
{
  "alignments": [
    {
      "label": "Small slice",
      "goal": "Finish one reviewable reading card",
      "assumptions": ["The task is about one paper"],
      "subtask_style": "artifact checklist"
    },
    {
      "label": "Small slice",
      "goal": "Finish one reviewable reading card"
    },
    {
      "label": "Survey pass",
      "goal": "Compare two related papers",
      "assumptions": "The user wants breadth"
    }
  ]
}
"""

        alignments = _parse_alignments(reply, task_id="task-1")

        self.assertEqual(
            [alignment.label for alignment in alignments],
            ["Small slice", "Survey pass"],
        )
        self.assertEqual(
            alignments[0].assumptions,
            ("The task is about one paper",),
        )
        self.assertEqual(alignments[0].task_id, "task-1")

    @patch("nblane.core.kanban_ai.llm.chat")
    def test_generate_alignment_options_does_not_mutate_board(
        self, mock_chat
    ) -> None:
        """Thin-task alignment options are drafts only."""
        mock_chat.return_value = """
{
  "alignments": [
    {
      "label": "Clarify output",
      "goal": "Produce one concrete checklist",
      "assumptions": ["No scope is known yet"],
      "subtask_style": "discovery first"
    }
  ]
}
"""
        sections = {"Doing": [KanbanTask(title="Plan demo", id="task-1")]}

        alignments = generate_kanban_task_alignment_options(
            sections,
            "task-1",
        )

        self.assertEqual(len(alignments), 1)
        self.assertEqual(alignments[0].label, "Clarify output")
        self.assertEqual(sections["Doing"][0].subtasks, [])
        system_prompt, user_prompt = mock_chat.call_args.args[:2]
        self.assertIn("confirm the intended scope and granularity", system_prompt)
        self.assertIn("Prefer milestone-level decomposition", user_prompt)
        self.assertIn("Title: Plan demo", user_prompt)

    @patch("nblane.core.kanban_ai.llm.chat")
    def test_alignment_prompt_uses_shoe_robotics_prior(
        self, mock_chat
    ) -> None:
        """Thin shoe tasks are grounded as robot placement, not commerce."""
        mock_chat.return_value = """
{"alignments": [{"label": "Robot loop", "goal": "Close a home robot shoe placement loop"}]}
"""
        sections = {
            "Doing": [
                KanbanTask(
                    title="形成鞋子测试场景的最小闭环",
                    id="shoe-task",
                )
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_profile_prior(root)
            with patch("nblane.core.kanban_ai.PROFILES_DIR", root):
                generate_kanban_task_alignment_options(
                    sections,
                    "shoe-task",
                    profile_name="王军",
                )

        _system_prompt, user_prompt = mock_chat.call_args.args[:2]
        self.assertIn("home-robot shoe placement", user_prompt)
        self.assertIn("Piper demo", user_prompt)
        self.assertIn("家庭鞋子抓取摆放 benchmark", user_prompt)
        self.assertNotIn("e-commerce", user_prompt.casefold())

    def test_build_context_prior_handles_vla_archive_and_evidence(self) -> None:
        """Context builder pulls recent VLA work without mutating profile data."""
        sections = {
            "Doing": [
                KanbanTask(
                    title="VLA memory模块",
                    id="vla-task",
                    subtasks=[KanbanSubtask("模型调研及选择")],
                )
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_profile_prior(root)
            with patch("nblane.core.kanban_ai.PROFILES_DIR", root):
                context = build_kanban_ai_context(
                    "王军",
                    sections,
                    "vla-task",
                )

        self.assertIn("PI0.5", context)
        self.assertIn("OpenPI", context)
        self.assertIn("VGGT", context)
        self.assertIn("Piper", context)
        self.assertIn("vlm_robot: learning", context)

    @patch("nblane.core.kanban_ai.llm.chat")
    @patch("nblane.core.kanban_ai.gap.analyze")
    def test_generate_returns_drafts_without_mutating_board(
        self, mock_analyze, mock_chat
    ) -> None:
        """Generation parses JSON proposals but does not append subtasks."""
        mock_analyze.return_value = GapResult(
            task="task",
            closure=[
                {
                    "id": "linux_basics",
                    "label": "Linux",
                    "status": "learning",
                    "is_gap": True,
                }
            ],
            gaps=["linux_basics"],
            next_steps=["Advance linux"],
        )
        mock_chat.return_value = """
```json
{
  "subtasks": [
    {
      "title": "Write reproduction notes",
      "reason": "Creates evidence",
      "gap_node_id": "linux_basics"
    },
    {
      "title": "Ignore unknown node",
      "reason": "Bad id",
      "gap_node_id": "made_up"
    }
  ]
}
```
"""
        sections = {
            "Doing": [
                KanbanTask(
                    title="Reproduce baseline",
                    id="task-1",
                    subtasks=[KanbanSubtask("Keep existing")],
                )
            ]
        }

        proposals = generate_kanban_subtask_proposals(
            "template",
            sections,
            "task-1",
        )

        self.assertEqual(
            [proposal.title for proposal in proposals],
            ["Write reproduction notes", "Ignore unknown node"],
        )
        self.assertEqual(proposals[0].gap_node_id, "linux_basics")
        self.assertEqual(proposals[1].gap_node_id, "")
        self.assertEqual(
            [st.title for st in sections["Doing"][0].subtasks],
            ["Keep existing"],
        )
        mock_chat.assert_called_once()
        system_prompt, user_prompt = mock_chat.call_args.args[:2]
        self.assertIn("Return 3 to 5 subtasks", system_prompt)
        self.assertIn("milestone-level", system_prompt)
        self.assertIn("not env_check.py", system_prompt)
        self.assertIn("Do not replace, summarize, or repeat", system_prompt)
        self.assertIn("artifact", system_prompt)
        self.assertIn("verification", system_prompt)
        self.assertIn("Output 3-5 new subtasks only at milestone granularity", user_prompt)
        self.assertIn("Do not invent file names", user_prompt)
        self.assertIn("Avoid generic learning/research", user_prompt)
        _, kwargs = mock_analyze.call_args
        self.assertFalse(kwargs["persist_router_keywords"])

    @patch("nblane.core.kanban_ai.llm.chat")
    @patch("nblane.core.kanban_ai.gap.analyze")
    def test_iup_pose_prompt_defaults_to_high_level_milestones(
        self, mock_analyze, mock_chat
    ) -> None:
        """Reproduction tasks should not default to invented script work."""
        mock_analyze.return_value = GapResult(task="task")
        mock_chat.return_value = """
{"subtasks": [{"title": "记录复现差异和下一步修正", "verification": "note reviewed"}]}
"""
        sections = {
            "Doing": [
                KanbanTask(
                    title="iup-pose结果复现",
                    id="iup-task",
                    context="a800->4090",
                    subtasks=[
                        KanbanSubtask("先跑一个完整的训练评测", done=True),
                        KanbanSubtask(
                            "性能对齐，实现baseline， 对齐效果和训练时间",
                            done=True,
                        ),
                    ],
                )
            ]
        }

        generate_kanban_subtask_proposals_detailed(
            "王军",
            sections,
            "iup-task",
            alignment_context=(
                "User clarification: 子任务保持在训练、评测、对齐、记录差异这一层"
            ),
        )

        system_prompt, user_prompt = mock_chat.call_args.args[:2]
        combined = f"{system_prompt}\n{user_prompt}"
        self.assertIn("milestone-level", combined)
        self.assertIn("complete one full training/evaluation run", combined)
        self.assertIn("baseline metrics and training time", combined)
        self.assertIn("先跑一个完整的训练评测", combined)
        self.assertIn("性能对齐", combined)
        self.assertIn("env_check.py", combined)
        self.assertIn("Do not invent file names", user_prompt)

    @patch("nblane.core.kanban_ai.llm.chat")
    @patch("nblane.core.kanban_ai.gap.analyze")
    def test_generate_detailed_uses_vla_prior(
        self, mock_analyze, mock_chat
    ) -> None:
        """Proposal prompts include profile/recent VLA context."""
        mock_analyze.return_value = GapResult(
            task="task",
            closure=[
                {
                    "id": "vlm_robot",
                    "label": "VLM-guided Robot Control",
                    "status": "learning",
                    "is_gap": True,
                }
            ],
            gaps=["vlm_robot"],
        )
        mock_chat.return_value = """
{"subtasks": [{"title": "Write OpenPI memory design note", "artifact": "note", "verification": "reviewed"}]}
"""
        sections = {
            "Doing": [
                KanbanTask(
                    title="VLA memory模块",
                    id="vla-task",
                    subtasks=[KanbanSubtask("模型调研及选择")],
                )
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_profile_prior(root)
            with patch("nblane.core.kanban_ai.PROFILES_DIR", root):
                result = generate_kanban_subtask_proposals_detailed(
                    "王军",
                    sections,
                    "vla-task",
                )

        self.assertEqual(result.error_key, "")
        self.assertEqual(
            [proposal.title for proposal in result.proposals],
            ["Write OpenPI memory design note"],
        )
        _system_prompt, user_prompt = mock_chat.call_args.args[:2]
        self.assertIn("OpenPI", user_prompt)
        self.assertIn("VGGT", user_prompt)
        self.assertIn("Piper", user_prompt)
        self.assertIn("data construction", user_prompt)

    @patch("nblane.core.kanban_ai.llm.chat")
    @patch("nblane.core.kanban_ai.gap.analyze")
    def test_generate_uses_confirmed_alignment_context(
        self, mock_analyze, mock_chat
    ) -> None:
        """Confirmed task understanding is included in the proposal prompt."""
        mock_analyze.return_value = GapResult(task="task")
        mock_chat.return_value = """
{"subtasks": [{"title": "Write scope note", "reason": "Pins intent"}]}
"""
        sections = {
            "Doing": [KanbanTask(title="Plan demo", id="task-1")]
        }

        proposals = generate_kanban_subtask_proposals(
            "template",
            sections,
            "task-1",
            alignment_context="Goal: Produce one concrete demo plan",
        )

        self.assertEqual([proposal.title for proposal in proposals], ["Write scope note"])
        _system_prompt, user_prompt = mock_chat.call_args.args[:2]
        self.assertIn("Confirmed task understanding", user_prompt)
        self.assertIn("Produce one concrete demo plan", user_prompt)

    def test_parse_filters_existing_vague_and_duplicate_subtasks(
        self,
    ) -> None:
        """Parsing keeps only concrete new checklist items."""
        reply = """
{
  "subtasks": [
    {
      "title": "Keep existing",
      "reason": "Would overwrite context",
      "gap_node_id": "linux_basics"
    },
    {
      "title": "Research Linux basics",
      "reason": "Too vague",
      "gap_node_id": "linux_basics"
    },
    {
      "title": "Write shell trace note",
      "reason": "Captures command evidence for the Linux gap",
      "gap_node_id": "linux_basics",
      "artifact": "docs/shell-trace.md",
      "verification": "Note includes command, output, and observed exit code"
    },
    {
      "title": "write shell trace note",
      "reason": "Duplicate casing",
      "gap_node_id": "linux_basics"
    },
    {
      "title": "Record dataset checksum",
      "reason": "Pins the input artifact",
      "gap_node_id": "linux_basics",
      "artifact": "checksums.txt",
      "verification": "Checksum file matches the downloaded dataset"
    },
    {
      "title": "Run baseline pytest",
      "reason": "Creates regression evidence",
      "gap_node_id": "made_up",
      "verification": "pytest exits with code 0"
    },
    {
      "title": "Save demo screenshot",
      "reason": "Shows the visible result",
      "gap_node_id": "linux_basics",
      "verification": "Screenshot is attached to the task"
    },
    {
      "title": "Capture blocker log",
      "reason": "Makes the blocker reviewable",
      "gap_node_id": "linux_basics",
      "verification": "Log contains failing command and timestamp"
    },
    {
      "title": "Draft review checklist",
      "reason": "Defines completion criteria",
      "gap_node_id": "linux_basics",
      "verification": "Checklist has owner and acceptance rows"
    },
    {
      "title": "Export final evidence bundle",
      "reason": "Collects handoff artifacts",
      "gap_node_id": "linux_basics",
      "verification": "Bundle contains note, log, screenshot, and checksum"
    },
    {
      "title": "Add seventh accepted item",
      "reason": "Should be capped",
      "gap_node_id": "linux_basics"
    }
  ]
}
"""

        proposals = _parse_proposals(
            reply,
            task_id="task-1",
            allowed_gap_ids={"linux_basics"},
            existing_titles={"Keep existing"},
        )

        self.assertEqual(
            [proposal.title for proposal in proposals],
            [
                "Write shell trace note",
                "Record dataset checksum",
                "Run baseline pytest",
                "Save demo screenshot",
                "Capture blocker log",
            ],
        )
        self.assertEqual(proposals[0].artifact, "docs/shell-trace.md")
        self.assertEqual(
            proposals[0].verification,
            "Note includes command, output, and observed exit code",
        )
        self.assertEqual(proposals[2].gap_node_id, "")
        self.assertTrue(
            all(proposal.task_id == "task-1" for proposal in proposals)
        )

    def test_parse_detailed_reports_non_json_and_empty_json(self) -> None:
        """Detailed parsing distinguishes invalid and empty model replies."""
        invalid = _parse_proposals_detailed(
            "not json",
            task_id="task-1",
            allowed_gap_ids=set(),
        )
        empty = _parse_proposals_detailed(
            '{"subtasks": []}',
            task_id="task-1",
            allowed_gap_ids=set(),
        )

        self.assertEqual(invalid.error_key, "parse_empty")
        self.assertEqual(empty.error_key, "empty_json")

    def test_parse_detailed_reports_filtered_vague_and_duplicate(self) -> None:
        """Detailed parsing reports why returned drafts were rejected."""
        vague = _parse_proposals_detailed(
            '{"subtasks": [{"title": "Research VLA memory"}]}',
            task_id="task-1",
            allowed_gap_ids=set(),
        )
        duplicate = _parse_proposals_detailed(
            '{"subtasks": [{"title": "Keep existing"}]}',
            task_id="task-1",
            allowed_gap_ids=set(),
            existing_titles={"Keep existing"},
        )

        self.assertEqual(vague.error_key, "filtered_vague")
        self.assertEqual(vague.raw_count, 1)
        self.assertEqual(vague.accepted_count, 0)
        self.assertEqual(vague.filtered_count, 1)
        self.assertEqual(duplicate.error_key, "filtered_duplicate")

    def test_apply_appends_without_overwriting_or_mutating(self) -> None:
        """Apply copies the board, preserves existing state, and dedupes."""
        sections = {
            "Doing": [
                KanbanTask(
                    title="Task",
                    id="task-1",
                    subtasks=[
                        KanbanSubtask("Keep existing", done=True),
                    ],
                )
            ],
            "Queue": [KanbanTask(title="Other", id="task-2")],
        }
        proposals = [
            KanbanSubtaskProposal(
                title="Keep existing",
                task_id="task-1",
            ),
            KanbanSubtaskProposal(
                title="New evidence note",
                task_id="task-1",
            ),
            KanbanSubtaskProposal(
                title="Wrong task",
                task_id="task-2",
            ),
            KanbanSubtaskProposal(
                title="Global suggestion",
            ),
        ]

        out = apply_kanban_subtask_proposals(
            sections,
            "task-1",
            proposals,
        )

        original_task = sections["Doing"][0]
        updated_task = out["Doing"][0]
        self.assertIsNot(original_task, updated_task)
        self.assertEqual(
            [st.title for st in original_task.subtasks],
            ["Keep existing"],
        )
        self.assertEqual(
            [(st.title, st.done) for st in updated_task.subtasks],
            [
                ("Keep existing", True),
                ("New evidence note", False),
                ("Global suggestion", False),
            ],
        )
        self.assertEqual(out["Queue"][0].subtasks, [])

    def test_applied_ai_subtasks_are_plain_editable_subtasks(self) -> None:
        """Applied proposals become ordinary list items callers can replace."""
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
            [
                KanbanSubtaskProposal(
                    title="AI generated item",
                    task_id="task-1",
                )
            ],
        )

        edited = replace(
            out["Doing"][0],
            subtasks=[
                subtask
                for subtask in out["Doing"][0].subtasks
                if subtask.title != "AI generated item"
            ],
        )

        self.assertEqual(
            [(subtask.title, subtask.done) for subtask in edited.subtasks],
            [("Keep existing", True)],
        )


if __name__ == "__main__":
    unittest.main()
