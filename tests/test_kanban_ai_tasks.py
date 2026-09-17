"""Tests for the Kanban AI background job registry."""

from __future__ import annotations

import threading
import time
import unittest
from unittest.mock import patch

from nblane.core import kanban_ai_tasks


def _wait_for(predicate, timeout: float = 3.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


class TestKanbanAiTasks(unittest.TestCase):
    """Job lifecycle: done / failed / cancelled / timeout / cleanup."""

    def setUp(self) -> None:
        kanban_ai_tasks._TASKS.clear()

    def tearDown(self) -> None:
        kanban_ai_tasks._TASKS.clear()

    def test_start_runs_runner_in_thread_and_completes(self) -> None:
        hold = threading.Event()
        main_thread = threading.current_thread()

        def runner():
            self.assertIsNot(threading.current_thread(), main_thread)
            hold.wait(2)
            return {"proposals": [1, 2]}

        snap = kanban_ai_tasks.start_job(
            profile="p",
            kanban_task_id="kb_1",
            kind=kanban_ai_tasks.KIND_SUBTASKS,
            runner=runner,
        )
        self.assertTrue(str(snap["job_id"]).startswith("kbai-"))
        self.assertEqual(snap["status"], "running")
        hold.set()
        self.assertTrue(
            _wait_for(
                lambda: kanban_ai_tasks.snapshot(snap["job_id"])["status"]
                == "done"
            )
        )
        final = kanban_ai_tasks.snapshot(snap["job_id"])
        self.assertEqual(final["result"], {"proposals": [1, 2]})
        self.assertEqual(final["kind"], kanban_ai_tasks.KIND_SUBTASKS)
        self.assertEqual(final["kanban_task_id"], "kb_1")
        # Internal cancel event is never exposed in snapshots.
        self.assertNotIn("cancel_event", final)

    def test_runner_exception_marks_failed(self) -> None:
        def runner():
            raise RuntimeError("LLM exploded")

        snap = kanban_ai_tasks.start_job(
            profile="p",
            kanban_task_id="kb_1",
            kind=kanban_ai_tasks.KIND_GAP,
            runner=runner,
        )
        self.assertTrue(
            _wait_for(
                lambda: kanban_ai_tasks.snapshot(snap["job_id"])["status"]
                == "failed"
            )
        )
        self.assertIn(
            "LLM exploded",
            kanban_ai_tasks.snapshot(snap["job_id"])["error"],
        )

    def test_cancel_discards_late_result(self) -> None:
        release = threading.Event()

        def runner():
            release.wait(2)
            return "late result"

        snap = kanban_ai_tasks.start_job(
            profile="p",
            kanban_task_id="kb_1",
            kind=kanban_ai_tasks.KIND_ALIGNMENTS,
            runner=runner,
        )
        cancelled = kanban_ai_tasks.cancel_job(snap["job_id"])
        self.assertEqual(cancelled["status"], "cancelled")
        release.set()
        time.sleep(0.05)
        final = kanban_ai_tasks.snapshot(snap["job_id"])
        self.assertEqual(final["status"], "cancelled")
        self.assertIsNone(final["result"])

    def test_timeout_marks_failed_and_late_result_loses(self) -> None:
        def runner():
            time.sleep(0.6)
            return "too late"

        with patch.object(kanban_ai_tasks, "_TIMEOUT_SECONDS", 0.2):
            snap = kanban_ai_tasks.start_job(
                profile="p",
                kanban_task_id="kb_1",
                kind=kanban_ai_tasks.KIND_GAP,
                runner=runner,
            )
            self.assertTrue(
                _wait_for(
                    lambda: kanban_ai_tasks.snapshot(snap["job_id"])["status"]
                    == "failed",
                    timeout=3.0,
                )
            )
            self.assertIn(
                "timed out",
                kanban_ai_tasks.snapshot(snap["job_id"])["error"],
            )
            time.sleep(0.6)
            self.assertEqual(
                kanban_ai_tasks.snapshot(snap["job_id"])["status"],
                "failed",
            )

    def test_unknown_job_snapshot_is_synthetic_failure(self) -> None:
        snap = kanban_ai_tasks.snapshot("kbai-missing")
        self.assertEqual(snap["status"], "failed")
        self.assertIn("lost", snap["error"])
        self.assertEqual(kanban_ai_tasks.snapshot(""), {})

    def test_cancel_jobs_for_kanban_task_is_scoped(self) -> None:
        hold = threading.Event()

        def runner():
            hold.wait(2)

        mine = kanban_ai_tasks.start_job(
            profile="p",
            kanban_task_id="kb_1",
            kind=kanban_ai_tasks.KIND_GAP,
            runner=runner,
        )
        other_card = kanban_ai_tasks.start_job(
            profile="p",
            kanban_task_id="kb_2",
            kind=kanban_ai_tasks.KIND_GAP,
            runner=runner,
        )
        other_profile = kanban_ai_tasks.start_job(
            profile="q",
            kanban_task_id="kb_1",
            kind=kanban_ai_tasks.KIND_GAP,
            runner=runner,
        )
        self.assertEqual(
            kanban_ai_tasks.cancel_jobs_for_kanban_task("p", "kb_1"),
            1,
        )
        self.assertEqual(
            kanban_ai_tasks.snapshot(mine["job_id"])["status"],
            "cancelled",
        )
        self.assertEqual(
            kanban_ai_tasks.snapshot(other_card["job_id"])["status"],
            "running",
        )
        self.assertEqual(
            kanban_ai_tasks.snapshot(other_profile["job_id"])["status"],
            "running",
        )
        hold.set()

    def test_cleanup_drops_old_final_records(self) -> None:
        snap = kanban_ai_tasks.start_job(
            profile="p",
            kanban_task_id="kb_1",
            kind=kanban_ai_tasks.KIND_GAP,
            runner=lambda: 1,
        )
        self.assertTrue(
            _wait_for(
                lambda: kanban_ai_tasks.snapshot(snap["job_id"])["status"]
                == "done"
            )
        )
        kanban_ai_tasks.cleanup(
            now=time.time() + kanban_ai_tasks._TTL_SECONDS + 1
        )
        self.assertNotIn(snap["job_id"], kanban_ai_tasks._TASKS)

    def test_drop_job_removes_only_final(self) -> None:
        hold = threading.Event()
        snap = kanban_ai_tasks.start_job(
            profile="p",
            kanban_task_id="kb_1",
            kind=kanban_ai_tasks.KIND_GAP,
            runner=lambda: hold.wait(2),
        )
        kanban_ai_tasks.drop_job(snap["job_id"])
        self.assertIn(snap["job_id"], kanban_ai_tasks._TASKS)
        kanban_ai_tasks.cancel_job(snap["job_id"])
        kanban_ai_tasks.drop_job(snap["job_id"])
        self.assertNotIn(snap["job_id"], kanban_ai_tasks._TASKS)
        hold.set()

    def test_unknown_kind_rejected(self) -> None:
        with self.assertRaises(ValueError):
            kanban_ai_tasks.start_job(
                profile="p",
                kanban_task_id="kb_1",
                kind="not-a-kind",
                runner=lambda: None,
            )


if __name__ == "__main__":
    unittest.main()
