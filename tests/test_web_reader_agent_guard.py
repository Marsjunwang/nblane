"""Agent policy and undo coverage for synchronous Reader mutations."""

from __future__ import annotations

import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import quote

from fastapi.testclient import TestClient

from nblane.core import agent_journal, agent_policy, reader_tasks
from nblane.core.auth import AUTH_SESSION_COOKIE_NAME, mint_auth_session_token, mint_reader_token
from nblane.core.reader_actions import ReaderActionContext
from nblane.core.research_papers import (
    PaperPage,
    PaperSegment,
    import_paper_pdf,
    load_paper_annotations,
    load_paper_translations,
    paper_pdf_asset_path,
    save_paper_pages,
    save_paper_segments,
    text_hash,
)
from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    load_research_sources,
    save_research_sources,
)
from nblane.core.research_workspace import load_chunks, load_research_claims
from nblane.web_reader_api import app
from nblane.web_reader_api.agent_guard import ROUTE_ACTIONS, action_for


SOURCE_ID = "source:paper:grounded"
PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>
endobj
trailer
<< /Root 1 0 R >>
%%EOF
"""


class TestWebReaderAgentGuard(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="nblane-reader-agent-"))
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
                "NBLANE_AUTH_SESSION_SECRET": "reader-agent-auth-secret",
                "NBLANE_READER_TOKEN_SECRET": "reader-agent-token-secret",
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

    def _client(self, user_id: str = "agent", *, raise_errors: bool = False) -> TestClient:
        client = TestClient(app, raise_server_exceptions=raise_errors)
        client.cookies.set(AUTH_SESSION_COOKIE_NAME, mint_auth_session_token(user_id))
        client.cookies.set("nblane_reader_session", mint_reader_token(user_id, "alice", SOURCE_ID))
        return client

    def _reader_url(self, suffix: str) -> str:
        return f"/reader/api/{quote(SOURCE_ID, safe='')}/{suffix}"

    def _entries(self) -> list[dict]:
        return agent_journal.load_entries(self.profile)

    def _undo_latest(self) -> dict:
        entry = next(row for row in reversed(self._entries()) if not row.get("undone_at"))
        agent_journal.undo(self.profile, entry["id"], actor="agent")
        return entry

    def test_all_mutating_routes_and_actions_are_classified(self) -> None:
        routes = {
            (method, route.path)
            for route in app.routes
            for method in (route.methods or set())
            if method in {"POST", "PUT", "PATCH", "DELETE"}
        }
        self.assertEqual(len(routes), 28)
        self.assertEqual(routes, set(ROUTE_ACTIONS))
        self.assertEqual(reader_tasks.ALLOWED_READER_TASK_ACTIONS, agent_policy.READER_TASK_ACTIONS)
        self.assertTrue(reader_tasks.ALLOWED_READER_TASK_ACTIONS <= set(agent_policy.READER_ACTIONS))
        for method, template in sorted(routes):
            body: dict = {}
            params: dict = {}
            if template.endswith("/events") or template.endswith("/events/jobs"):
                body = {"action": "paper_library_create_collection", "payload": {}}
            elif template.endswith("/tasks"):
                body = {"action": "ask_paper", "payload": {}}
            elif template.endswith("/action/{action}"):
                params = {"action": "save_progress"}
            with self.subTest(method=method, template=template):
                action = action_for(method, template, params, body)
                self.assertIn(action, agent_policy.ACTION_TIERS)
                self.assertNotEqual(action, "reader.unsupported")
                self.assertTrue(agent_policy.ACTION_LABELS.get(action))
        self.assertEqual(
            action_for("POST", "/reader/api/{source_id}/new-unmapped-write", {}, {}),
            "reader.unsupported",
        )
        self.assertEqual(agent_policy.tier_for("reader.unsupported"), agent_policy.T3)

    def test_human_and_agent_progress_and_sync_undo(self) -> None:
        human = self._client("alice")
        response = human.post(self._reader_url("progress"), json={"page": 2})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self._entries(), [])

        agent = self._client()
        response = agent.post(self._reader_url("progress"), json={"page": 3})
        self.assertEqual(response.status_code, 200, response.text)
        entries = self._entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["action"], "reader.progress")
        self.assertEqual(entries[0]["tier"], "T1")
        self.assertEqual(entries[0]["actor"], "agent")
        self._undo_latest()
        source = load_research_sources(self.profile).by_id()[SOURCE_ID]
        self.assertEqual(source.metadata["last_read_page"], 2)

    def test_dynamic_annotation_translate_and_unknown_action(self) -> None:
        agent = self._client()
        created = agent.post(
            self._reader_url("annotation"),
            json={"selected_text": "Important passage", "page": 1, "note": "agent"},
        )
        self.assertEqual(created.status_code, 200, created.text)
        annotation_id = created.json()["changed_ids"]["annotation_id"]
        self.assertTrue(any(change["entity"].startswith("jsonl:") for change in self._entries()[-1]["changes"]))

        unknown_agent = agent.post(self._reader_url("annotation"), json={"action": "not_registered"})
        self.assertEqual(unknown_agent.status_code, 403)
        self.assertEqual(unknown_agent.json()["code"], "agent_forbidden")
        unknown_human = self._client("alice").post(
            self._reader_url("annotation"), json={"action": "not_registered"}
        )
        self.assertEqual(unknown_human.status_code, 400)
        self.assertIn("Unsupported reader action", str(unknown_human.json()["detail"]))
        unknown_translate = agent.post(self._reader_url("translate"), json={"action": "not_registered"})
        self.assertEqual(unknown_translate.status_code, 403)

        body = {"action": "annotation_delete", "annotation_id": annotation_id}
        required = agent.post(self._reader_url("annotation"), json=body)
        self.assertEqual(required.status_code, 428, required.text)
        self.assertEqual(
            set(required.json()),
            {"code", "message", "confirmation"},
        )
        self.assertEqual(required.json()["code"], "confirmation_required")
        confirm_id = required.json()["confirmation"]["confirm_id"]
        self.assertEqual(load_paper_annotations(self.profile, SOURCE_ID)[0].status, "active")

        bypass = agent.post(self._reader_url("translate"), json=body)
        self.assertEqual(bypass.status_code, 428)
        reused = agent.post(
            self._reader_url("translate"),
            json=body,
            headers={agent_policy.CONFIRM_HEADER: confirm_id},
        )
        self.assertEqual(reused.status_code, 428)
        self.assertEqual(reused.json()["code"], "confirmation_invalid")
        self.assertEqual(load_paper_annotations(self.profile, SOURCE_ID)[0].status, "active")

        deleted = agent.post(
            self._reader_url("annotation"),
            json=body,
            headers={agent_policy.CONFIRM_HEADER: confirm_id},
        )
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertEqual(load_paper_annotations(self.profile, SOURCE_ID)[0].status, "deleted")
        self._undo_latest()
        self.assertEqual(load_paper_annotations(self.profile, SOURCE_ID)[0].status, "active")

    def test_pdf_delete_confirmation_and_asset_restore(self) -> None:
        import_paper_pdf(self.profile, SOURCE_ID, PDF_BYTES, "paper.pdf")
        asset_path = paper_pdf_asset_path(self.profile, SOURCE_ID)
        asset_ref = load_research_sources(self.profile).by_id()[SOURCE_ID].metadata["pdf_asset_ref"]
        body = {
            "action": "paper_library_delete_paper_asset",
            "payload": {"paper_ids": [SOURCE_ID]},
        }
        agent = self._client()
        required = agent.post("/api/research/alice/paper-library/events", json=body)
        self.assertEqual(required.status_code, 428, required.text)
        self.assertTrue(asset_path.exists())
        confirm_id = required.json()["confirmation"]["confirm_id"]
        deleted = agent.post(
            "/api/research/alice/paper-library/events",
            json=body,
            headers={agent_policy.CONFIRM_HEADER: confirm_id},
        )
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertFalse(asset_path.exists())
        entry = next(row for row in reversed(self._entries()) if not row.get("undone_at"))
        kinds = {change["entity"] for change in entry["changes"]}
        self.assertIn("research_source", kinds)
        self.assertIn(f"asset:{asset_ref}", kinds)
        self._undo_latest()
        self.assertEqual(asset_path.read_bytes(), PDF_BYTES)
        source = load_research_sources(self.profile).by_id()[SOURCE_ID]
        self.assertEqual(source.metadata["pdf_asset_ref"], asset_ref)

    def test_partial_sync_failure_is_journaled(self) -> None:
        agent = self._client()
        with patch("nblane.core.reader_actions.create_citation", side_effect=RuntimeError("citation failed")):
            response = agent.post(
                self._reader_url("citation"),
                json={"selected_text": "Important passage", "claim_text": "Grounded claim"},
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(len(load_chunks(self.profile, SOURCE_ID)), 1)
        self.assertEqual(len(load_research_claims(self.profile)), 1)
        entries = self._entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["action"], "reader.citation.create")
        kinds = {change["entity"] for change in entries[0]["changes"]}
        self.assertIn("file:research/claims.yaml", kinds)
        self.assertTrue(any(kind.startswith("jsonl:research/chunks/") for kind in kinds))

    def test_snapshot_and_journal_failures_are_explicit(self) -> None:
        agent = self._client()
        with patch("nblane.core.agent_journal.snapshot", side_effect=RuntimeError("snapshot failed")):
            response = agent.post(self._reader_url("progress"), json={"page": 4})
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json()["code"], "agent_journal_failed")
        self.assertNotEqual(load_research_sources(self.profile).by_id()[SOURCE_ID].metadata.get("last_read_page"), 4)

        with patch("nblane.core.agent_journal.record", side_effect=RuntimeError("record failed")):
            response = agent.post(self._reader_url("progress"), json={"page": 5})
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json()["code"], "agent_journal_failed")
        self.assertEqual(load_research_sources(self.profile).by_id()[SOURCE_ID].metadata["last_read_page"], 5)

    def test_t0_and_unknown_paper_event_do_not_journal(self) -> None:
        agent = self._client()
        answer = SimpleNamespace(structured={"answer": "42"}, warnings=[])
        with patch("nblane.core.reader_actions.answer_paper_question", return_value=answer):
            asked = agent.post(self._reader_url("ask"), json={"question": "Why?"})
        self.assertEqual(asked.status_code, 200, asked.text)
        token = agent.post(f"/api/research/alice/papers/{quote(SOURCE_ID, safe='')}/reader-token")
        self.assertEqual(token.status_code, 200, token.text)
        unknown = agent.post(
            "/api/research/alice/paper-library/events",
            json={"action": "paper_library_not_registered", "payload": {}},
        )
        self.assertEqual(unknown.status_code, 403)
        human_unknown = self._client("alice").post(
            "/api/research/alice/paper-library/events",
            json={"action": "paper_library_not_registered", "payload": {}},
        )
        self.assertEqual(human_unknown.status_code, 400)
        self.assertEqual(self._entries(), [])

    def test_batch_threshold_applies_to_effective_paper_event(self) -> None:
        agent = self._client()
        response = agent.post(
            "/api/research/alice/paper-library/events",
            json={
                "action": "paper_library_update_papers_status",
                "payload": {
                    "paper_ids": ["s1", "s2", "s3", "s4"],
                    "status": "archived",
                },
            },
        )
        self.assertEqual(response.status_code, 428, response.text)
        self.assertEqual(response.json()["confirmation"]["action"], "reader.source.edit")
        self.assertEqual(self._entries(), [])
        discarded = agent.post(
            "/api/research/alice/paper-library/events",
            json={
                "action": "paper_library_update_papers_status",
                "payload": {"paper_ids": [SOURCE_ID], "status": "discarded"},
            },
        )
        self.assertEqual(discarded.status_code, 428, discarded.text)
        self.assertEqual(discarded.json()["confirmation"]["action"], "reader.source.discard")
        self.assertEqual(self._entries(), [])

    def test_translation_saved_flag_unchanged_for_human(self) -> None:
        human = self._client("alice")
        result = SimpleNamespace(
            structured={"translations": [{"segment_id": "selection:abc", "translated_text": "重要段落"}]},
            warnings=[],
            error="",
            backend="direct_llm",
        )
        with patch("nblane.core.reader_actions.translate_paper_segments", return_value=result):
            response = human.post(
                self._reader_url("translate"),
                json={"selected_text": "Important passage", "selected_text_hash": "hash:abc"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(load_paper_translations(self.profile, SOURCE_ID)), 1)
        self.assertEqual(self._entries(), [])


if __name__ == "__main__":
    unittest.main()
