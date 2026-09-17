"""Tests for the Streamlit glue around background Kanban AI jobs."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from nblane import kanban_ai_jobs
from nblane.core import kanban_ai_tasks
from nblane.core.kanban_io import KANBAN_DOING, KANBAN_DONE, KANBAN_QUEUE
from nblane.core.models import KanbanTask


def _sections() -> dict:
    return {
        KANBAN_DOING: [KanbanTask(title="Task A", id="kb_a")],
        KANBAN_DONE: [],
        KANBAN_QUEUE: [],
    }


class TestKanbanAiJobs(unittest.TestCase):
    """Page handlers must queue background jobs, never call LLM inline."""

    def setUp(self) -> None:
        self.fake_st = SimpleNamespace(session_state={})
        self.tmp = tempfile.TemporaryDirectory()
        self.profile_path = Path(self.tmp.name) / "p"
        self.profile_path.mkdir()
        patches = [
            patch("nblane.kanban_ai_jobs.st", self.fake_st),
            patch(
                "nblane.kanban_ai_jobs.profile_dir",
                lambda _name: self.profile_path,
            ),
            patch("nblane.kanban_ai_jobs.refresh_file_snapshots"),
            patch("nblane.kanban_ai_jobs.stash_git_backup_results"),
            patch(
                "nblane.kanban_ai_jobs.llm_client.is_configured",
                lambda: False,
            ),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.refresh_mock = kanban_ai_jobs.refresh_file_snapshots

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _fake_start_job(self, calls: list[dict]):
        def _start(**kwargs):
            calls.append(kwargs)
            return {
                "job_id": f"kbai-test-{len(calls)}",
                "status": "running",
                "kind": kwargs.get("kind", ""),
            }

        return _start

    def test_start_gap_job_queues_without_calling_llm(self) -> None:
        calls: list[dict] = []
        llm_calls: list[dict] = []
        sections = _sections()
        with patch(
            "nblane.kanban_ai_jobs.kanban_ai_tasks.start_job",
            self._fake_start_job(calls),
        ), patch(
            "nblane.kanban_ai_jobs.analyze_kanban_task_gap",
            lambda *a, **kw: llm_calls.append({"args": a, "kwargs": kw}),
        ):
            kanban_ai_jobs.start_gap_job(
                "p",
                "suffix",
                sections=sections,
                kanban_task_id="kb_a",
                ai_backend="llm",
                goal_context="goal text",
            )
        # Registry was asked to start a background gap job...
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["kind"], kanban_ai_tasks.KIND_GAP)
        self.assertEqual(calls[0]["kanban_task_id"], "kb_a")
        self.assertTrue(callable(calls[0]["runner"]))
        # ...and the LLM function was NOT invoked synchronously.
        self.assertEqual(llm_calls, [])
        jobs = self.fake_st.session_state[
            kanban_ai_jobs.ai_jobs_key("p", "suffix")
        ]
        self.assertEqual(
            jobs["kb_a"],
            {"job_id": "kbai-test-1", "kind": kanban_ai_tasks.KIND_GAP},
        )

    def test_start_alignment_job_queues_without_calling_llm(self) -> None:
        calls: list[dict] = []
        llm_calls: list[dict] = []
        with patch(
            "nblane.kanban_ai_jobs.kanban_ai_tasks.start_job",
            self._fake_start_job(calls),
        ), patch(
            "nblane.kanban_ai_jobs.generate_kanban_task_alignment_options",
            lambda *a, **kw: llm_calls.append({"args": a, "kwargs": kw}),
        ):
            kanban_ai_jobs.start_alignment_job(
                "p",
                "suffix",
                sections=_sections(),
                kanban_task_id="kb_a",
                ai_backend="llm",
                goal_context="",
            )
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["kind"], kanban_ai_tasks.KIND_ALIGNMENTS)
        self.assertEqual(llm_calls, [])

    def test_start_subtasks_job_runner_runs_in_worker_not_inline(self) -> None:
        calls: list[dict] = []
        llm_calls: list[dict] = []
        with patch(
            "nblane.kanban_ai_jobs.kanban_ai_tasks.start_job",
            self._fake_start_job(calls),
        ), patch(
            "nblane.kanban_ai_jobs.generate_kanban_subtask_proposals_detailed",
            lambda *a, **kw: llm_calls.append({"args": a, "kwargs": kw}),
        ):
            kanban_ai_jobs.start_subtasks_job(
                "p",
                "suffix",
                sections=_sections(),
                kanban_task_id="kb_a",
                ai_backend="llm",
                goal_context="",
                alignment_context="Label: x",
                granularity="checklist",
                style_hint="hint",
            )
        self.assertEqual(calls[0]["kind"], kanban_ai_tasks.KIND_SUBTASKS)
        self.assertEqual(llm_calls, [])
        # Invoking the captured runner (as the worker thread would) passes
        # the original call parameters through.
        with patch(
            "nblane.kanban_ai_jobs.generate_kanban_subtask_proposals_detailed",
            lambda *a, **kw: llm_calls.append({"args": a, "kwargs": kw}),
        ):
            calls[0]["runner"]()
        self.assertEqual(len(llm_calls), 1)
        self.assertEqual(llm_calls[0]["args"][0], "p")
        self.assertEqual(llm_calls[0]["args"][2], "kb_a")
        kwargs = llm_calls[0]["kwargs"]
        self.assertEqual(kwargs["alignment_context"], "Label: x")
        self.assertEqual(kwargs["granularity"], "checklist")
        self.assertEqual(kwargs["subtask_style_hint"], "hint")

    def test_runner_snapshots_sections(self) -> None:
        calls: list[dict] = []
        captured: list[dict] = []
        sections = _sections()
        with patch(
            "nblane.kanban_ai_jobs.kanban_ai_tasks.start_job",
            self._fake_start_job(calls),
        ), patch(
            "nblane.kanban_ai_jobs.analyze_kanban_task_gap",
            lambda _profile, secs, _tid, **kw: captured.append(secs),
        ):
            kanban_ai_jobs.start_gap_job(
                "p",
                "suffix",
                sections=sections,
                kanban_task_id="kb_a",
                ai_backend="llm",
                goal_context="",
            )
            # Mutating the live board after queueing must not leak into the
            # worker's frozen copy.
            sections[KANBAN_DOING].append(KanbanTask(title="Later", id="kb_l"))
            calls[0]["runner"]()
        self.assertEqual(len(captured), 1)
        self.assertEqual(len(captured[0][KANBAN_DOING]), 1)
        self.assertIsNot(captured[0], sections)

    def test_start_replaces_previous_job_for_same_card(self) -> None:
        calls: list[dict] = []
        cancelled: list[str] = []
        with patch(
            "nblane.kanban_ai_jobs.kanban_ai_tasks.start_job",
            self._fake_start_job(calls),
        ), patch(
            "nblane.kanban_ai_jobs.kanban_ai_tasks.cancel_job",
            lambda job_id: cancelled.append(job_id) or {},
        ), patch(
            "nblane.kanban_ai_jobs.analyze_kanban_task_gap",
            lambda *a, **kw: None,
        ):
            kanban_ai_jobs.start_gap_job(
                "p", "suffix", sections=_sections(),
                kanban_task_id="kb_a", ai_backend="llm", goal_context="",
            )
            kanban_ai_jobs.start_gap_job(
                "p", "suffix", sections=_sections(),
                kanban_task_id="kb_a", ai_backend="llm", goal_context="",
            )
        self.assertEqual(cancelled, ["kbai-test-1"])
        jobs = self.fake_st.session_state[
            kanban_ai_jobs.ai_jobs_key("p", "suffix")
        ]
        self.assertEqual(jobs["kb_a"]["job_id"], "kbai-test-2")

    def test_pending_by_task_reports_running_only(self) -> None:
        key = kanban_ai_jobs.ai_jobs_key("p", "suffix")
        self.fake_st.session_state[key] = {
            "kb_a": {"job_id": "j1", "kind": "gap"},
            "kb_b": {"job_id": "j2", "kind": "subtasks"},
        }
        snaps = {
            "j1": {"status": "running"},
            "j2": {"status": "done"},
        }
        with patch(
            "nblane.kanban_ai_jobs.kanban_ai_tasks.snapshot",
            lambda job_id: snaps.get(job_id, {}),
        ):
            pending = kanban_ai_jobs.pending_by_task("p", "suffix")
        self.assertEqual(pending, {"kb_a": "gap"})

    def test_cancel_tracked_job_clears_session_and_registry(self) -> None:
        key = kanban_ai_jobs.ai_jobs_key("p", "suffix")
        self.fake_st.session_state[key] = {
            "kb_a": {"job_id": "j1", "kind": "gap"},
        }
        cancelled: list[tuple[str, str]] = []
        with patch(
            "nblane.kanban_ai_jobs.kanban_ai_tasks.cancel_jobs_for_kanban_task",
            lambda profile, task_id: cancelled.append((profile, task_id)) or 1,
        ):
            kanban_ai_jobs.cancel_tracked_job("p", "suffix", "kb_a")
        self.assertEqual(cancelled, [("p", "kb_a")])
        self.assertEqual(self.fake_st.session_state[key], {})

    def test_collect_finished_jobs_moves_results_and_refreshes(self) -> None:
        key = kanban_ai_jobs.ai_jobs_key("p", "suffix")
        self.fake_st.session_state[key] = {
            "kb_a": {"job_id": "j1", "kind": "gap"},
            "kb_b": {"job_id": "j2", "kind": "subtasks"},
        }
        snaps = {
            "j1": {"status": "done", "result": "GAP"},
            "j2": {"status": "running"},
        }
        handled: list[tuple] = []
        dropped: list[str] = []
        with patch(
            "nblane.kanban_ai_jobs.kanban_ai_tasks.snapshot",
            lambda job_id: snaps.get(job_id, {}),
        ), patch(
            "nblane.kanban_ai_jobs.kanban_ai_tasks.drop_job",
            lambda job_id: dropped.append(job_id),
        ):
            changed = kanban_ai_jobs.collect_finished_jobs(
                "p",
                "suffix",
                lambda task_id, kind, snap: handled.append(
                    (task_id, kind, snap)
                ),
            )
        self.assertTrue(changed)
        self.assertEqual(
            handled,
            [("kb_a", "gap", {"status": "done", "result": "GAP"})],
        )
        # Only the still-running job remains tracked.
        self.assertEqual(
            self.fake_st.session_state[key],
            {"kb_b": {"job_id": "j2", "kind": "subtasks"}},
        )
        self.assertEqual(dropped, ["j1"])
        # Activity files the worker may have written get fresh snapshots.
        paths = self.refresh_mock.call_args[0][0]
        self.assertEqual(
            sorted(path.name for path in paths),
            ["activity-log.yaml", "agent-activity.yaml", "ai-runs.yaml"],
        )

    def test_collect_finished_jobs_noop_when_nothing_final(self) -> None:
        key = kanban_ai_jobs.ai_jobs_key("p", "suffix")
        self.fake_st.session_state[key] = {
            "kb_a": {"job_id": "j1", "kind": "gap"},
        }
        handled: list[tuple] = []
        with patch(
            "nblane.kanban_ai_jobs.kanban_ai_tasks.snapshot",
            lambda job_id: {"status": "running"},
        ):
            changed = kanban_ai_jobs.collect_finished_jobs(
                "p", "suffix", lambda *a: handled.append(a)
            )
        self.assertFalse(changed)
        self.assertEqual(handled, [])
        self.refresh_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
