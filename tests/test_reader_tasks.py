"""Tests for the in-process Reader task registry."""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.reader_actions import ReaderActionContext, ReaderActionResult
from nblane.core import reader_tasks


class TestReaderTasks(unittest.TestCase):
    def _ctx(self, root: Path, *, source_id: str = "source:paper:grounded") -> ReaderActionContext:
        profile = root / "alice"
        profile.mkdir(exist_ok=True)
        return ReaderActionContext(
            profile_name="alice",
            profile_path=profile,
            user_id="local",
            source_id=source_id,
        )

    def test_start_runs_action_and_returns_done_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._ctx(Path(tmp))

            with patch(
                "nblane.core.reader_tasks.handle_reader_action",
                return_value=ReaderActionResult(data={"answer": 42}, changed_ids={"x": "y"}, message="Done"),
            ) as action:
                initial = reader_tasks.start(ctx, "ask_paper", {"question": "Why?"}, task_id="reader-task-test-done")
                snapshots = list(reader_tasks.iter_snapshots("reader-task-test-done", ctx=ctx, poll_seconds=0.01))
                final = snapshots[-1] if snapshots else reader_tasks.snapshot("reader-task-test-done", ctx=ctx)

        self.assertEqual(initial["task_id"], "reader-task-test-done")
        self.assertIn(initial["status"], {"running", "done"})
        self.assertEqual(final["status"], "done")
        self.assertEqual(final["result"]["data"], {"answer": 42})
        self.assertEqual(final["changed_ids"], {"x": "y"})
        action.assert_called_once()

    def test_ask_paper_done_progress_uses_answered_label_without_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._ctx(Path(tmp))

            with patch(
                "nblane.core.reader_tasks.handle_reader_action",
                return_value=ReaderActionResult(data={"structured": {"answer": "Because."}}),
            ):
                reader_tasks.start(ctx, "ask_paper", {"question": "Why?"}, task_id="reader-task-test-ask-done")
                final = list(reader_tasks.iter_snapshots("reader-task-test-ask-done", ctx=ctx, poll_seconds=0.01))[-1]

        self.assertEqual(final["status"], "done")
        self.assertEqual(final["progress"]["label"], "Answered")
        self.assertEqual(final["progress"]["current"], 1)
        self.assertEqual(final["progress"]["total"], 1)

    def test_unknown_task_returns_failed_lost_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._ctx(Path(tmp))
            snap = reader_tasks.snapshot("missing-reader-task", ctx=ctx)

        self.assertEqual(snap["status"], "failed")
        self.assertEqual(snap["task_id"], "missing-reader-task")
        self.assertEqual(snap["source_id"], "source:paper:grounded")
        self.assertIn("lost", snap["error"])

    def test_cancel_marks_running_task_cancelled(self) -> None:
        started = threading.Event()
        release = threading.Event()

        def run_action(_ctx: ReaderActionContext, _action: str, _payload: dict, **_kwargs) -> ReaderActionResult:
            started.set()
            release.wait(timeout=1)
            return ReaderActionResult(message="late")

        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._ctx(Path(tmp))
            with patch("nblane.core.reader_tasks.handle_reader_action", side_effect=run_action):
                reader_tasks.start(ctx, "ask_paper", {"question": "Why?"}, task_id="reader-task-test-cancel")
                self.assertTrue(started.wait(timeout=1))
                cancelled = reader_tasks.cancel("reader-task-test-cancel", ctx=ctx)
                release.set()

        self.assertEqual(cancelled["status"], "cancelled")

    def test_translate_full_progress_callback_updates_snapshot(self) -> None:
        progress_seen = threading.Event()
        release = threading.Event()

        def run_action(
            _ctx: ReaderActionContext,
            _action: str,
            _payload: dict,
            **kwargs,
        ) -> ReaderActionResult:
            callback = kwargs.get("progress_callback")
            if callback is not None:
                callback(
                    {
                        "segments_selected": 5,
                        "segments_processed": 2,
                        "updated": 1,
                        "batches": 3,
                        "batches_completed": 1,
                    }
                )
            progress_seen.set()
            release.wait(timeout=1)
            return ReaderActionResult(data={"summary": {"segments_selected": 5, "updated": 4}}, message="Done")

        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._ctx(Path(tmp))
            with patch("nblane.core.reader_tasks.handle_reader_action", side_effect=run_action):
                reader_tasks.start(
                    ctx,
                    "translate_full_paper",
                    {"target_lang": "zh"},
                    task_id="reader-task-test-progress",
                )
                self.assertTrue(progress_seen.wait(timeout=1))
                running = reader_tasks.snapshot("reader-task-test-progress", ctx=ctx)
                release.set()
                final = list(reader_tasks.iter_snapshots("reader-task-test-progress", ctx=ctx, poll_seconds=0.01))[-1]

        self.assertEqual(running["status"], "running")
        self.assertEqual(running["progress"]["current"], 2)
        self.assertEqual(running["progress"]["total"], 5)
        self.assertEqual(running["progress"]["saved"], 1)
        self.assertEqual(final["status"], "done")

    def test_task_identity_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = self._ctx(root)
            other = ReaderActionContext(
                profile_name="alice",
                profile_path=ctx.profile_path,
                user_id="local",
                source_id="source:paper:other",
            )
            with patch(
                "nblane.core.reader_tasks.handle_reader_action",
                return_value=ReaderActionResult(message="Done"),
            ):
                reader_tasks.start(ctx, "ask_paper", {"question": "Why?"}, task_id="reader-task-test-identity")

            with self.assertRaises(PermissionError):
                reader_tasks.snapshot("reader-task-test-identity", ctx=other)

    def test_disallows_non_whitelisted_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._ctx(Path(tmp))

            with self.assertRaises(ValueError):
                reader_tasks.start(ctx, "page_changed", {"page": 1}, task_id="reader-task-test-denied")

    def test_allows_analyze_paper_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._ctx(Path(tmp))

            with patch(
                "nblane.core.reader_tasks.handle_reader_action",
                return_value=ReaderActionResult(
                    data={"analysis": {"scores": {"overall": 8}}},
                    message="Analysis saved",
                ),
            ):
                initial = reader_tasks.start(ctx, "analyze_paper", {"page": 1}, task_id="reader-task-test-analyze")
                final = list(reader_tasks.iter_snapshots("reader-task-test-analyze", ctx=ctx, poll_seconds=0.01))[-1]

        self.assertEqual(initial["action"], "analyze_paper")
        self.assertEqual(final["status"], "done")
        self.assertEqual(final["progress"]["label"], "Analysis saved")


if __name__ == "__main__":
    unittest.main()
