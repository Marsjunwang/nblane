"""Reader agent reservations, background undo, cancellation and ownership."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import quote

from fastapi.testclient import TestClient

from nblane.core import agent_journal, agent_policy, reader_ops, reader_tasks
from nblane.core.auth import AUTH_SESSION_COOKIE_NAME, mint_auth_session_token, mint_reader_token
from nblane.core.paper_library_workspace import PaperLibraryEventResult
from nblane.core.reader_actions import ReaderActionContext, ReaderActionResult
from nblane.core.research_papers import (
    PaperPage,
    PaperSegment,
    load_paper_library_tree,
    load_paper_translations,
    save_paper_pages,
    save_paper_segments,
    text_hash,
)
from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    load_research_sources,
    mutate_research_sources,
    save_research_sources,
    update_research_source,
)
from nblane.web_reader_api import (
    _PAPER_LIBRARY_EVENT_JOBS,
    _PAPER_LIBRARY_EVENT_JOBS_LOCK,
    _PAPER_LIBRARY_SEARCH_JOBS,
    _PAPER_LIBRARY_SEARCH_JOBS_LOCK,
    app,
)


SOURCE_ID = "source:paper:grounded"
TERMINAL = {"done", "failed", "cancelled"}


class TestReaderAgentJobs(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="nblane-reader-agent-jobs-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.profile = self.root / "alice"
        self.profile.mkdir()
        (self.root / "bob").mkdir()
        auth_file = self.root / "auth" / "users.yaml"
        auth_file.parent.mkdir()
        auth_file.write_text(
            """users:
  alice:
    display_name: Alice
    password_hash: unused
    role: member
    profiles: [alice]
  agent:
    display_name: Agent
    password_hash: unused
    role: member
    profiles: [alice]
    agent: true
  other:
    display_name: Other
    password_hash: unused
    role: member
    profiles: [alice]
""",
            encoding="utf-8",
        )
        env = patch.dict(
            os.environ,
            {
                "NBLANE_AUTH_FILE": str(auth_file),
                "NBLANE_AUTH_SESSION_SECRET": "reader-jobs-auth-secret",
                "NBLANE_READER_TOKEN_SECRET": "reader-jobs-token-secret",
                "NBLANE_RESEARCH_ASSET_ROOT": str(self.root / "assets"),
                "NBLANE_AGENT_STATE_DIR": str(self.root / "agent-state"),
            },
            clear=False,
        )
        env.start()
        self.addCleanup(env.stop)
        resolver = patch(
            "nblane.web_reader_api.profile_dir",
            side_effect=lambda name: self.root / name,
        )
        resolver.start()
        self.addCleanup(resolver.stop)
        backup = patch("nblane.core.git_backup.record_change")
        backup.start()
        self.addCleanup(backup.stop)
        agent_policy.reset()
        self.addCleanup(agent_policy.reset)
        with reader_tasks._COND:
            reader_tasks._TASKS.clear()
        with _PAPER_LIBRARY_EVENT_JOBS_LOCK:
            _PAPER_LIBRARY_EVENT_JOBS.clear()
        with _PAPER_LIBRARY_SEARCH_JOBS_LOCK:
            _PAPER_LIBRARY_SEARCH_JOBS.clear()

        inbox = ResearchSourceInbox(profile="alice")
        add_research_source(
            inbox,
            "Grounded Claims",
            source_id=SOURCE_ID,
            kind="paper",
            visibility="private",
        )
        save_research_sources(self.profile, inbox)
        save_paper_pages(
            self.profile,
            SOURCE_ID,
            [PaperPage(source_id=SOURCE_ID, page=1, text="Important passage", text_hash=text_hash("Important passage"))],
        )
        save_paper_segments(
            self.profile,
            SOURCE_ID,
            [
                PaperSegment(
                    segment_id="seg:1",
                    source_id=SOURCE_ID,
                    page=1,
                    order=1,
                    text="Important passage",
                    text_hash=text_hash("Important passage"),
                )
            ],
        )

    def _client(self, user_id: str = "agent") -> TestClient:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(AUTH_SESSION_COOKIE_NAME, mint_auth_session_token(user_id))
        client.cookies.set("nblane_reader_session", mint_reader_token(user_id, "alice", SOURCE_ID))
        return client

    def _ctx(self, user_id: str = "agent") -> ReaderActionContext:
        return ReaderActionContext("alice", self.profile, user_id, SOURCE_ID)

    def _reader_url(self, suffix: str) -> str:
        return f"/reader/api/{quote(SOURCE_ID, safe='')}/{suffix}"

    def _entries(self) -> list[dict]:
        return agent_journal.load_entries(self.profile)

    def _undo_latest(self) -> dict:
        entry = next(row for row in reversed(self._entries()) if not row.get("undone_at"))
        agent_journal.undo(self.profile, entry["id"], actor="agent")
        return entry

    def _wait_reader(self, task_id: str, user_id: str = "agent") -> dict:
        client = self._client(user_id)
        latest: dict = {}
        for _ in range(200):
            response = client.get(self._reader_url(f"tasks/{task_id}"))
            self.assertEqual(response.status_code, 200, response.text)
            latest = response.json()
            if latest.get("status") in TERMINAL:
                return latest
            time.sleep(0.01)
        self.fail(f"Reader task did not finish: {latest}")

    def _wait_event(self, job_id: str, user_id: str = "agent") -> dict:
        client = self._client(user_id)
        latest: dict = {}
        for _ in range(200):
            response = client.get(f"/api/research/alice/paper-library/events/jobs/{job_id}")
            self.assertEqual(response.status_code, 200, response.text)
            latest = response.json()["job"]
            if latest.get("status") in TERMINAL:
                return latest
            time.sleep(0.01)
        self.fail(f"Paper event job did not finish: {latest}")

    def _write_page(self, commit, page: int) -> None:
        def apply(inbox) -> None:
            source = inbox.by_id()[SOURCE_ID]
            metadata = dict(source.metadata or {})
            metadata["last_read_page"] = page
            update_research_source(inbox, SOURCE_ID, metadata=metadata)

        commit(lambda: mutate_research_sources(self.profile, apply))

    def test_reader_task_async_translation_and_undo(self) -> None:
        result = SimpleNamespace(
            structured={"translations": [{"segment_id": "selection:abc", "translated_text": "重要段落"}]},
            warnings=[],
            error="",
            backend="direct_llm",
        )
        with patch("nblane.core.reader_actions.translate_paper_segments", return_value=result):
            started = self._client().post(
                self._reader_url("tasks"),
                json={
                    "task_id": "agent-translate-undo",
                    "action": "translate_selection",
                    "payload": {"selected_text": "Important passage", "selected_text_hash": "hash:abc"},
                },
            )
            self.assertEqual(started.status_code, 202, started.text)
            final = self._wait_reader("agent-translate-undo")
        self.assertEqual(final["status"], "done")
        self.assertTrue(final["write_committed"])
        self.assertEqual(len(load_paper_translations(self.profile, SOURCE_ID)), 1)
        entry = self._undo_latest()
        self.assertEqual(entry["action"], "reader.translation")
        self.assertEqual(load_paper_translations(self.profile, SOURCE_ID), [])

    def test_t2_confirmation_creates_no_background_job(self) -> None:
        agent = self._client()
        response = agent.post(
            self._reader_url("tasks"),
            json={
                "task_id": "agent-t2-not-created",
                "action": "translate_visible_pages",
                "payload": {"visible_pages": [1, 2, 3, 4]},
            },
        )
        self.assertEqual(response.status_code, 428, response.text)
        lost = reader_tasks.snapshot("agent-t2-not-created", ctx=self._ctx())
        self.assertIn("lost", lost["error"])
        before = len(_PAPER_LIBRARY_EVENT_JOBS)
        response = agent.post(
            "/api/research/alice/paper-library/events/jobs",
            json={"action": "paper_library_delete_paper_asset", "payload": {"paper_ids": [SOURCE_ID]}},
        )
        self.assertEqual(response.status_code, 428, response.text)
        self.assertEqual(len(_PAPER_LIBRARY_EVENT_JOBS), before)
        self.assertEqual(self._entries(), [])

    def test_reader_cancel_before_and_after_commit(self) -> None:
        for committed in (False, True):
            with self.subTest(committed=committed):
                agent_policy.reset()
                task_id = f"agent-cancel-{committed}"
                started = threading.Event()
                release = threading.Event()

                def fake_action(_ctx, _action, _payload, **kwargs):
                    commit = kwargs["commit"]
                    cancel_callback = kwargs["cancel_callback"]
                    if committed:
                        self._write_page(commit, 7)
                    started.set()
                    release.wait(timeout=2)
                    reader_ops.checkpoint(cancel_callback)
                    self._write_page(commit, 9)
                    return ReaderActionResult(message="late")

                with patch("nblane.core.reader_tasks.handle_reader_action", side_effect=fake_action):
                    started_response = self._client().post(
                        self._reader_url("tasks"),
                        json={"task_id": task_id, "action": "translate_selection", "payload": {}},
                    )
                    self.assertEqual(started_response.status_code, 202, started_response.text)
                    self.assertTrue(started.wait(timeout=1))
                    cancelling = reader_tasks.cancel(task_id, ctx=self._ctx())
                    self.assertEqual(cancelling["status"], "cancelling")
                    self.assertEqual(cancelling["write_committed"], committed)
                    release.set()
                    final = self._wait_reader(task_id)
                self.assertEqual(final["status"], "cancelled")
                self.assertEqual(final["write_committed"], committed)
                source = load_research_sources(self.profile).by_id()[SOURCE_ID]
                self.assertNotEqual(source.metadata.get("last_read_page"), 9)
                self.assertEqual(source.metadata.get("last_read_page"), 7 if committed else None)
                self.assertEqual(len(self._entries()), 1 if committed else 0)
                if committed:
                    self.assertIn("Partial writes", final["message"])
                    self._undo_latest()
                    self.assertIsNone(load_research_sources(self.profile).by_id()[SOURCE_ID].metadata.get("last_read_page"))

    def test_late_ai_translation_is_not_saved_after_cancel(self) -> None:
        started = threading.Event()
        release = threading.Event()

        def slow_translate(*_args, **_kwargs):
            started.set()
            release.wait(timeout=2)
            return SimpleNamespace(
                structured={"translations": [{"segment_id": "selection:abc", "translated_text": "晚到译文"}]},
                warnings=[],
                error="",
                backend="direct_llm",
            )

        with patch("nblane.core.reader_actions.translate_paper_segments", side_effect=slow_translate):
            response = self._client().post(
                self._reader_url("tasks"),
                json={
                    "task_id": "agent-late-ai",
                    "action": "translate_selection",
                    "payload": {"selected_text": "Important passage", "selected_text_hash": "hash:abc"},
                },
            )
            self.assertEqual(response.status_code, 202, response.text)
            self.assertTrue(started.wait(timeout=1))
            reader_tasks.cancel("agent-late-ai", ctx=self._ctx())
            release.set()
            final = self._wait_reader("agent-late-ai")
        self.assertEqual(final["status"], "cancelled")
        self.assertEqual(load_paper_translations(self.profile, SOURCE_ID), [])
        self.assertEqual(self._entries(), [])

    def test_timeout_requests_stop_then_worker_fails(self) -> None:
        started = threading.Event()
        release = threading.Event()

        def slow_action(*_args, **_kwargs):
            started.set()
            release.wait(timeout=2)
            return ReaderActionResult(message="late")

        with patch("nblane.core.reader_tasks.handle_reader_action", side_effect=slow_action):
            response = self._client().post(
                self._reader_url("tasks"),
                json={"task_id": "agent-timeout", "action": "translate_selection", "payload": {}},
            )
            self.assertEqual(response.status_code, 202, response.text)
            self.assertTrue(started.wait(timeout=1))
            with reader_tasks._COND:
                task = reader_tasks._TASKS["agent-timeout"]
                task["timeout_seconds"] = 0.01
                task["started_at"] = time.time() - 1
            cancelling = reader_tasks.snapshot("agent-timeout", ctx=self._ctx())
            self.assertEqual(cancelling["status"], "cancelling")
            self.assertEqual(cancelling["finished_at"], 0.0)
            release.set()
            final = self._wait_reader("agent-timeout")
        self.assertEqual(final["status"], "failed")
        self.assertIn("timed out", final["error"])

    def test_paper_event_async_undo_cancel_and_owner(self) -> None:
        agent = self._client()
        started = agent.post(
            "/api/research/alice/paper-library/events/jobs",
            json={"action": "paper_library_create_collection", "payload": {"title": "Agent collection"}},
        )
        self.assertEqual(started.status_code, 200, started.text)
        job_id = started.json()["job_id"]
        final = self._wait_event(job_id)
        self.assertEqual(final["status"], "done")
        self.assertTrue(final["write_committed"])
        self.assertTrue(any(node.title == "Agent collection" for node in load_paper_library_tree(self.profile).nodes))
        self._undo_latest()
        self.assertFalse(any(node.title == "Agent collection" for node in load_paper_library_tree(self.profile).nodes))

        committed = threading.Event()
        release = threading.Event()

        def fake_event(_profile, _body, **kwargs):
            commit = kwargs["commit"]
            self._write_page(commit, 7)
            committed.set()
            release.wait(timeout=2)
            reader_ops.checkpoint(kwargs["cancel_callback"])
            self._write_page(commit, 9)
            return PaperLibraryEventResult(message="late")

        with patch("nblane.web_reader_api.handle_paper_library_event", side_effect=fake_event):
            started = agent.post(
                "/api/research/alice/paper-library/events/jobs",
                json={"action": "paper_library_retry_translation", "payload": {"paper_ids": [SOURCE_ID]}},
            )
            self.assertEqual(started.status_code, 200, started.text)
            job_id = started.json()["job_id"]
            self.assertTrue(committed.wait(timeout=1))
            other = self._client("other")
            self.assertEqual(other.get(f"/api/research/alice/paper-library/events/jobs/{job_id}").status_code, 404)
            self.assertEqual(other.post(f"/api/research/alice/paper-library/events/jobs/{job_id}/cancel").status_code, 404)
            cancelled = agent.post(f"/api/research/alice/paper-library/events/jobs/{job_id}/cancel")
            self.assertEqual(cancelled.status_code, 200, cancelled.text)
            self.assertEqual(cancelled.json()["job"]["status"], "cancelling")
            release.set()
            final = self._wait_event(job_id)
        self.assertEqual(final["status"], "cancelled")
        self.assertTrue(final["write_committed"])
        self.assertIn("Partial writes", final["message"])
        source = load_research_sources(self.profile).by_id()[SOURCE_ID]
        self.assertEqual(source.metadata.get("last_read_page"), 7)
        active_entries = [row for row in self._entries() if not row.get("undone_at")]
        self.assertEqual(len(active_entries), 1)
        self.assertEqual(active_entries[0]["action"], "reader.translation")

    def test_search_and_reader_owner_isolation(self) -> None:
        agent = self._client()
        with patch("nblane.web_reader_api.search_papers_with_codex", return_value=[]):
            started = agent.post(
                "/api/research/alice/paper-library/search/jobs",
                json={"query": "robot memory", "mode": "codex"},
            )
            self.assertEqual(started.status_code, 200, started.text)
            job_id = started.json()["job_id"]
            for _ in range(100):
                if agent.get(f"/api/research/alice/paper-library/search/jobs/{job_id}").json()["job"]["status"] == "done":
                    break
                time.sleep(0.01)
        other = self._client("other")
        self.assertEqual(other.get(f"/api/research/alice/paper-library/search/jobs/{job_id}").status_code, 404)
        self.assertEqual(other.get(f"/api/research/alice/paper-library/search/jobs/{job_id}/stream").status_code, 404)
        self.assertEqual(other.post(f"/api/research/alice/paper-library/search/jobs/{job_id}/cancel").status_code, 404)
        self.assertEqual(agent.get(f"/api/research/alice/paper-library/search/jobs/{job_id}").status_code, 200)

        started = threading.Event()
        release = threading.Event()

        def slow_action(*_args, **_kwargs):
            started.set()
            release.wait(timeout=2)
            return ReaderActionResult(data={"answer": "secret"})

        with patch("nblane.core.reader_tasks.handle_reader_action", side_effect=slow_action):
            response = agent.post(
                self._reader_url("tasks"),
                json={"task_id": "agent-owner", "action": "ask_paper", "payload": {"question": "secret"}},
            )
            self.assertEqual(response.status_code, 202, response.text)
            self.assertTrue(started.wait(timeout=1))
            self.assertEqual(other.get(self._reader_url("tasks/agent-owner")).status_code, 403)
            self.assertEqual(other.delete(self._reader_url("tasks/agent-owner")).status_code, 403)
            events = other.get(self._reader_url("tasks/agent-owner/events"))
            self.assertEqual(events.status_code, 200)
            self.assertIn("different source, profile, or user", events.text)
            self.assertNotIn("secret", events.text)
            reader_tasks.cancel("agent-owner", ctx=self._ctx())
            release.set()
            self._wait_reader("agent-owner")

    def test_cancel_during_commit_finishes_and_journals_current_segment(self) -> None:
        started = threading.Event()
        release = threading.Event()
        original_capture = reader_ops.agent_ops.capture_before

        def gated_capture(write, kinds=None):
            started.set()
            if not release.wait(timeout=2):
                raise RuntimeError("timed out waiting to finish commit")
            original_capture(write, kinds)

        def fake_action(_ctx, _action, _payload, **kwargs):
            self._write_page(kwargs["commit"], 7)
            return ReaderActionResult(message="late")

        with (
            patch("nblane.core.reader_tasks.handle_reader_action", side_effect=fake_action),
            patch("nblane.core.reader_ops.agent_ops.capture_before", side_effect=gated_capture),
        ):
            response = self._client().post(
                self._reader_url("tasks"),
                json={"task_id": "agent-commit-race", "action": "translate_selection", "payload": {}},
            )
            self.assertEqual(response.status_code, 202, response.text)
            self.assertTrue(started.wait(timeout=1))
            cancelling = reader_tasks.cancel("agent-commit-race", ctx=self._ctx())
            self.assertEqual(cancelling["status"], "cancelling")
            release.set()
            final = self._wait_reader("agent-commit-race")

        self.assertEqual(final["status"], "cancelled")
        self.assertTrue(final["write_committed"])
        source = load_research_sources(self.profile).by_id()[SOURCE_ID]
        self.assertEqual(source.metadata.get("last_read_page"), 7)
        self.assertEqual(len(self._entries()), 1)
        self._undo_latest()
        source = load_research_sources(self.profile).by_id()[SOURCE_ID]
        self.assertIsNone(source.metadata.get("last_read_page"))

    def test_worker_snapshot_and_journal_failures_are_visible(self) -> None:
        def fake_action(_ctx, _action, _payload, **kwargs):
            self._write_page(kwargs["commit"], 8)
            return ReaderActionResult(message="done")

        with (
            patch("nblane.core.reader_tasks.handle_reader_action", side_effect=fake_action),
            patch("nblane.core.agent_journal.snapshot", side_effect=RuntimeError("snapshot failed")),
        ):
            response = self._client().post(
                self._reader_url("tasks"),
                json={"task_id": "agent-worker-snapshot", "action": "translate_selection", "payload": {}},
            )
            self.assertEqual(response.status_code, 202, response.text)
            final = self._wait_reader("agent-worker-snapshot")
        self.assertEqual(final["status"], "failed")
        self.assertFalse(final["write_committed"])
        self.assertIn("pre-commit snapshot", final["message"])

        with (
            patch("nblane.core.reader_tasks.handle_reader_action", side_effect=fake_action),
            patch("nblane.core.agent_journal.record", side_effect=RuntimeError("record failed")),
        ):
            response = self._client().post(
                self._reader_url("tasks"),
                json={"task_id": "agent-worker-record", "action": "translate_selection", "payload": {}},
            )
            self.assertEqual(response.status_code, 202, response.text)
            final = self._wait_reader("agent-worker-record")
        self.assertEqual(final["status"], "failed")
        self.assertTrue(final["write_committed"])
        self.assertIn("record failed", final["message"])
        self.assertIn("Partial writes", final["message"])
        self.assertEqual(load_research_sources(self.profile).by_id()[SOURCE_ID].metadata["last_read_page"], 8)


if __name__ == "__main__":
    unittest.main()
