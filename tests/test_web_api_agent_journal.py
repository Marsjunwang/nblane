"""Agent write policy: journal + undo (T1) and chat confirmation (T2).

Reuses the tmp-profile / auth-on fixtures of test_web_api_agent_writeback.
Real profiles/ is never touched.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core import agent_policy
from nblane.core.kanban_io import parse_kanban
from tests.test_web_api_agent_writeback import AgentWritebackTestBase, _write_profile

BASE = "/api/v1/profiles/alice"


def _titles(profile: Path) -> list[str]:
    return [task.title for tasks in parse_kanban(profile).values() for task in tasks]


def _checkin_ids(profile: Path) -> list[str]:
    raw = yaml.safe_load((profile / "activity-log.yaml").read_text(encoding="utf-8"))
    return [item["id"] for item in raw.get("checkins") or []]


class JournalTestBase(AgentWritebackTestBase):
    def setUp(self) -> None:
        agent_policy.reset()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "profiles"
        self.profile = _write_profile(self.root)

    def journal(self, client) -> list[dict]:
        response = client.get(f"{BASE}/agent/journal")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["entries"]


class TestJournalAndUndo(JournalTestBase):
    def test_add_card_then_undo_removes_it(self) -> None:
        client = self._client(self.root, login="openclaw")
        created = client.post(f"{BASE}/kanban/cards", json={"title": "Buy milk"})
        self.assertEqual(created.status_code, 201, created.text)
        entries = self.journal(client)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["action"], "kanban.card.add")
        self.assertEqual(entries[0]["status"], "undoable")
        self.assertIn("Buy milk", entries[0]["summary"])

        undone = client.post(f"{BASE}/agent/journal/{entries[0]['id']}/undo")
        self.assertEqual(undone.status_code, 200, undone.text)
        self.assertNotIn("Buy milk", _titles(self.profile))
        self.assertEqual(self.journal(client)[0]["status"], "undone")
        again = client.post(f"{BASE}/agent/journal/{entries[0]['id']}/undo")
        self.assertEqual(again.status_code, 409)
        self.assertEqual(again.json()["code"], "journal_entry_already_undone")

    def test_todo_tick_undo_restores_previous_state(self) -> None:
        client = self._client(self.root, login="openclaw")
        client.patch(f"{BASE}/kanban/cards/taskQ", json={"todos": [{"text": "a", "done": False}]})
        client.patch(f"{BASE}/kanban/cards/taskQ", json={"todos": [{"text": "a", "done": True}]})
        latest = self.journal(client)[0]
        client.post(f"{BASE}/agent/journal/{latest['id']}/undo")
        card = next(t for tasks in parse_kanban(self.profile).values() for t in tasks if t.id == "taskQ")
        self.assertEqual([(t.text, t.done) for t in card.todos], [("a", False)])

    def test_undo_refused_after_human_edit(self) -> None:
        agent = self._client(self.root, login="openclaw")
        agent.patch(f"{BASE}/kanban/cards/taskQ", json={"context": "agent"})
        entry = self.journal(agent)[0]
        human = self._client(self.root, login="wang")
        human.patch(f"{BASE}/kanban/cards/taskQ", json={"context": "human"})
        self.assertEqual(self.journal(human)[0]["status"], "conflict")
        refused = human.post(f"{BASE}/agent/journal/{entry['id']}/undo")
        self.assertEqual(refused.status_code, 409)
        self.assertEqual(refused.json()["code"], "journal_undo_conflict")
        card = next(t for tasks in parse_kanban(self.profile).values() for t in tasks if t.id == "taskQ")
        self.assertEqual(card.context, "human")

    def test_checkin_add_undo(self) -> None:
        client = self._client(self.root, login="openclaw")
        added = client.post(f"{BASE}/checkins", json={"habit": "exercise", "summary": "swim"})
        new_id = added.json()["checkin"]["id"]
        self.assertIn(new_id, _checkin_ids(self.profile))
        entry = self.journal(client)[0]
        client.post(f"{BASE}/agent/journal/{entry['id']}/undo")
        self.assertNotIn(new_id, _checkin_ids(self.profile))
        self.assertIn("act_20260920_exercise", _checkin_ids(self.profile))

    def test_human_writes_are_not_journaled(self) -> None:
        client = self._client(self.root, login="wang")
        client.post(f"{BASE}/kanban/cards", json={"title": "Human card"})
        self.assertEqual(self.journal(client), [])
        self.assertFalse((self.profile / "agent-journal.yaml").exists())

    def test_partial_write_before_route_error_is_journaled_and_undoable(self) -> None:
        client = self._client(self.root, login="openclaw")
        with patch(
            "nblane.web_api.routes_v1._record_agent_writeback",
            side_effect=RuntimeError("post-write failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "post-write failure"):
                client.post(f"{BASE}/kanban/cards", json={"title": "Partial card"})

        self.assertIn("Partial card", _titles(self.profile))
        entries = self.journal(client)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["action"], "kanban.card.add")
        undone = client.post(f"{BASE}/agent/journal/{entries[0]['id']}/undo")
        self.assertEqual(undone.status_code, 200, undone.text)
        self.assertNotIn("Partial card", _titles(self.profile))


class TestConfirmation(JournalTestBase):
    def test_delete_needs_confirmation_and_is_undoable(self) -> None:
        client = self._client(self.root, login="openclaw")
        url = f"{BASE}/kanban/cards/taskQ"
        first = client.delete(url)
        self.assertEqual(first.status_code, 428, first.text)
        body = first.json()
        self.assertEqual(body["code"], "confirmation_required")
        self.assertIn("Card One", body["confirmation"]["summary"])
        self.assertIn("Card One", _titles(self.profile))

        confirm_id = body["confirmation"]["confirm_id"]
        done = client.delete(url, headers={agent_policy.CONFIRM_HEADER: confirm_id})
        self.assertEqual(done.status_code, 200, done.text)
        self.assertNotIn("Card One", _titles(self.profile))

        # Single use: replaying the token asks again instead of acting.
        replay = client.delete(url, headers={agent_policy.CONFIRM_HEADER: confirm_id})
        self.assertNotEqual(replay.status_code, 200)

        entry = self.journal(client)[0]
        self.assertEqual(entry["action"], "kanban.card.delete")
        client.post(f"{BASE}/agent/journal/{entry['id']}/undo")
        sections = parse_kanban(self.profile)
        self.assertEqual([t.title for t in sections["Queue"]], ["Card One"])

    def test_token_is_bound_to_the_request(self) -> None:
        client = self._client(self.root, login="openclaw")
        client.post(f"{BASE}/kanban/cards", json={"title": "Other"})
        first = client.delete(f"{BASE}/kanban/cards/taskQ")
        confirm_id = first.json()["confirmation"]["confirm_id"]
        other = client.delete(
            f"{BASE}/kanban/cards/Other",
            headers={agent_policy.CONFIRM_HEADER: confirm_id},
        )
        self.assertEqual(other.status_code, 428)
        self.assertEqual(other.json()["code"], "confirmation_invalid")
        self.assertIn("Other", _titles(self.profile))

    def test_token_is_bound_to_the_caller(self) -> None:
        agent = self._client(self.root, login="openclaw")
        confirm_id = agent.delete(f"{BASE}/kanban/cards/taskQ").json()["confirmation"]["confirm_id"]
        self.assertFalse(
            agent_policy.consume(confirm_id, actor="wang", fingerprint="x")
        )

    def test_humans_are_never_asked(self) -> None:
        client = self._client(self.root, login="wang")
        response = client.delete(f"{BASE}/kanban/cards/taskQ")
        self.assertEqual(response.status_code, 200, response.text)


class TestPolicyTable(JournalTestBase):
    def test_batch_threshold(self) -> None:
        self.assertEqual(agent_policy.tier_for("kanban.card.add", 3), agent_policy.T1)
        self.assertEqual(agent_policy.tier_for("kanban.card.add", 4), agent_policy.T2)

    def test_unknown_actions_default_to_confirmation(self) -> None:
        self.assertEqual(agent_policy.tier_for("something.new"), agent_policy.T2)

    def test_agent_flag_marks_other_accounts(self) -> None:
        users = self.root / "users-agent.yaml"
        from nblane.core import auth as auth_core

        users.write_text(
            yaml.safe_dump(
                {"users": {"muse": {"password_hash": "x", "role": "member", "agent": True}}}
            ),
            encoding="utf-8",
        )
        self.assertTrue(auth_core.load_users(users)["muse"].agent)


def _yaml(profile: Path, name: str) -> dict:
    return yaml.safe_load((profile / name).read_text(encoding="utf-8")) or {}


class TestPhase2Undo(JournalTestBase):
    """Every agent-writable entity kind can be undone (guard + journal)."""

    def _agent(self):
        from tests.test_web_api_agent_writeback import AutoConfirmClient  # noqa: F401

        self.auto_confirm = True
        return self._client(self.root, login="openclaw")

    def _undo_latest(self, client) -> dict:
        entry = next(e for e in self.journal(client) if e["status"] != "undone")
        response = client.post(f"{BASE}/agent/journal/{entry['id']}/undo")
        self.assertEqual(response.status_code, 200, response.text)
        return entry

    def test_goal_add_and_patch_undo(self) -> None:
        client = self._agent()
        created = client.post(f"{BASE}/goals", json={"title": "Run a marathon"})
        self.assertEqual(created.status_code, 201, created.text)
        goal_id = created.json()["goal"]["id"]
        patched = client.patch(f"{BASE}/goals/{goal_id}", json={"status": "completed"})
        self.assertEqual(patched.status_code, 200, patched.text)
        entry = self._undo_latest(client)
        self.assertEqual(entry["action"], "goal.patch")
        self.assertEqual(entry["tier"], "T2")
        goal = next(g for g in _yaml(self.profile, "goals.yaml")["goals"] if g["id"] == goal_id)
        self.assertNotEqual(goal["status"], "completed")
        self._undo_latest(client)
        ids = [g["id"] for g in _yaml(self.profile, "goals.yaml").get("goals") or []]
        self.assertNotIn(goal_id, ids)

    def test_north_star_undo(self) -> None:
        client = self._agent()
        before = (self.profile / "SKILL.md").read_text(encoding="utf-8")
        response = client.patch(f"{BASE}/north-star", json={"brief": "Ship robots"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("Ship robots", (self.profile / "SKILL.md").read_text(encoding="utf-8"))
        self._undo_latest(client)
        self.assertEqual((self.profile / "SKILL.md").read_text(encoding="utf-8"), before)

    def test_skill_node_undo(self) -> None:
        client = self._agent()
        response = client.patch(f"{BASE}/skill-tree/nodes/slam_basics", json={"status": "lit"})
        self.assertEqual(response.status_code, 200, response.text)
        self._undo_latest(client)
        node = next(n for n in _yaml(self.profile, "skill-tree.yaml")["nodes"] if n["id"] == "slam_basics")
        self.assertEqual(node["status"], "learning")

    def test_evidence_edit_undo(self) -> None:
        client = self._agent()
        response = client.post(f"{BASE}/evidence/ev_alpha/edit", json={"fields": {"title": "Renamed"}})
        self.assertEqual(response.status_code, 200, response.text)
        self._undo_latest(client)
        row = next(r for r in _yaml(self.profile, "evidence-pool.yaml")["evidence_entries"] if r["id"] == "ev_alpha")
        self.assertEqual(row["title"], "Alpha")

    def test_project_case_add_save_undo(self) -> None:
        client = self._agent()
        created = client.post(f"{BASE}/project-board/cases", json={"title": "Robot arm"})
        self.assertEqual(created.status_code, 201, created.text)
        case_id = created.json()["case"]["id"]
        saved = client.post(f"{BASE}/project-board/cases/{case_id}/save", json={"summary": "v2"})
        self.assertEqual(saved.status_code, 200, saved.text)
        self._undo_latest(client)
        case = next(c for c in _yaml(self.profile, "project-board.yaml")["project_cases"] if c["id"] == case_id)
        self.assertNotEqual(case.get("summary"), "v2")
        self._undo_latest(client)
        ids = [c["id"] for c in _yaml(self.profile, "project-board.yaml").get("project_cases") or []]
        self.assertNotIn(case_id, ids)


class TestGuardPolicy(JournalTestBase):
    def test_web_only_routes_refused_for_agents(self) -> None:
        client = self._client(self.root, login="openclaw")
        for method, url in (
            ("POST", f"{BASE}/public-site/deploy"),
            ("PATCH", f"{BASE}/settings"),
            ("POST", f"{BASE}/ai-exceptions/dismiss"),
            ("POST", f"{BASE}/studio/init"),
            ("POST", f"{BASE}/content/images/accept"),
            ("DELETE", f"{BASE}/content/blog/example"),
        ):
            response = client.request(method, url, json={})
            self.assertEqual(response.status_code, 403, (url, response.text))
            self.assertEqual(response.json()["code"], "agent_forbidden")

    def test_t2_summary_names_the_target(self) -> None:
        client = self._client(self.root, login="openclaw")
        response = client.post(f"{BASE}/evidence/ev_alpha/edit", json={"fields": {"title": "X"}})
        self.assertEqual(response.status_code, 428)
        self.assertEqual(response.json()["confirmation"]["summary"], "编辑证据「Alpha」")

    def test_batch_over_threshold_needs_confirmation(self) -> None:
        client = self._client(self.root, login="openclaw")
        response = client.post(
            f"{BASE}/evidence-review/deprecate",
            json={"ids": ["ev_alpha", "a", "b", "c"], "deprecated": True},
        )
        self.assertEqual(response.status_code, 428)
        self.assertIn("4 条", response.json()["confirmation"]["summary"])

    def test_failed_confirmed_request_refunds_token(self) -> None:
        client = self._client(self.root, login="openclaw")
        url = f"{BASE}/kanban/cards/taskQ"
        confirm_id = client.delete(url).json()["confirmation"]["confirm_id"]
        stale = client.delete(url, headers={agent_policy.CONFIRM_HEADER: confirm_id, "If-Match": 'W/"stale"'})
        self.assertEqual(stale.status_code, 412, stale.text)
        retried = client.delete(url, headers={agent_policy.CONFIRM_HEADER: confirm_id})
        self.assertEqual(retried.status_code, 200, retried.text)

    def test_reads_and_divination_pass(self) -> None:
        client = self._client(self.root, login="openclaw")
        self.assertEqual(client.get(f"{BASE}/kanban").status_code, 200)
        from unittest.mock import patch

        def no_llm(*_args, **_kwargs):
            raise RuntimeError("no LLM in tests")

        with patch("nblane.core.divination._default_runner", no_llm):
            cast = client.post(f"{BASE}/divination", json={"mode": "play"})
        self.assertNotEqual(cast.status_code, 428)
        self.assertNotEqual(cast.status_code, 403)


class TestHttpOnlyAssistantEndpoints(JournalTestBase):
    """The growth log is reachable over HTTP."""

    def test_growth_log_append_is_journaled_and_undoable(self) -> None:
        client = self._client(self.root, login="openclaw")
        before = (self.profile / "SKILL.md").read_text(encoding="utf-8")
        response = client.post(f"{BASE}/growth-log", json={"event": "Shipped the arm demo"})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertIn("Shipped the arm demo", (self.profile / "SKILL.md").read_text(encoding="utf-8"))
        entry = self.journal(client)[0]
        self.assertEqual(entry["action"], "growth_log.append")
        self.assertEqual(entry["tier"], "T1")
        undone = client.post(f"{BASE}/agent/journal/{entry['id']}/undo")
        self.assertEqual(undone.status_code, 200, undone.text)
        self.assertEqual((self.profile / "SKILL.md").read_text(encoding="utf-8"), before)

    def test_growth_log_rejects_blank_event(self) -> None:
        client = self._client(self.root, login="wang")
        response = client.post(f"{BASE}/growth-log", json={"event": "  "})
        self.assertEqual(response.status_code, 422)


class TestAgentAsyncJobs(JournalTestBase):
    def _register_job(self, name: str, runner, *, action: str) -> None:
        from nblane.web_api import jobs as jobs_module

        spec = jobs_module.JobKind(
            name=name,
            validate=lambda job_input: dict(job_input),
            run=runner,
            effect="write",
            action=action,
            journal=("research_source",),
            context_runner=True,
        )
        patcher = patch.dict(jobs_module._KINDS, {name: spec})
        self.addCleanup(patcher.stop)
        patcher.start()

    def _wait_final(self, client, job_id: str) -> dict:
        import time

        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            payload = client.get(f"{BASE}/jobs/{job_id}").json()
            if payload["job"]["status"] in {"done", "failed"}:
                return payload
            time.sleep(0.03)
        self.fail(f"job {job_id} did not finish")

    def _source_titles(self) -> list[str]:
        from nblane.core.research_sources import load_research_sources

        return [source.title for source in load_research_sources(self.profile).sources]

    @staticmethod
    def _commit_source(ctx, title: str) -> None:
        from nblane.core import profile_io
        from nblane.core.research_sources import add_research_source, mutate_research_sources

        def commit() -> None:
            def mutate(inbox) -> None:
                add_research_source(inbox, title=title, url=f"https://example.com/{title}")

            mutate_research_sources(profile_io.profile_dir("alice"), mutate)

        ctx.apply(commit, summary="导入一条资料")

    def _paper_fixture(self, source_id: str) -> None:
        import os

        import fitz
        from nblane.core.research_sources import add_research_source, mutate_research_sources

        asset_root = Path(self.tmp.name) / "assets"
        pdf = asset_root / "profiles" / "alice" / "papers" / "demo.pdf"
        pdf.parent.mkdir(parents=True, exist_ok=True)
        document = fitz.open()
        page = document.new_page(width=320, height=420)
        page.insert_text((36, 42), "A Grounded Paper", fontsize=16)
        page.insert_textbox(
            fitz.Rect(36, 82, 282, 190),
            "Abstract\nThis paper contains a complete paragraph for real reader preparation.",
            fontsize=10,
        )
        pdf.write_bytes(document.tobytes())
        document.close()
        mutate_research_sources(
            self.profile,
            lambda inbox: add_research_source(
                inbox,
                source_id=source_id,
                title="Grounded Paper",
                kind="paper",
                url="https://example.com/grounded-paper",
                metadata={
                    "pdf_asset_ref": "papers/demo.pdf",
                    "pdf_download_status": "downloaded",
                },
            ),
        )
        env = patch.dict(os.environ, {"NBLANE_RESEARCH_ASSET_ROOT": str(asset_root)})
        self.addCleanup(env.stop)
        env.start()

    def _start_prepare_job(self, kind_name: str, source_id: str) -> str:
        from nblane.core import agent_ops
        from nblane.web_api import jobs as jobs_module
        from nblane.web_api import research_papers

        kinds = research_papers._analysis_journal_kinds(self.profile, source_id)
        write = agent_ops.reserve(
            self.profile,
            actor="openclaw",
            action="research.paper_analysis",
            kinds=kinds,
            fingerprint=f"test:{kind_name}",
            describe=lambda _before: "生成论文分析",
        )

        def runner(_profile, _job_input, report, ctx):
            return research_papers._prepare_analysis_artifacts(
                self.profile, source_id, report, ctx, kinds
            )

        spec = jobs_module.JobKind(
            name=kind_name,
            validate=lambda job_input: dict(job_input),
            run=runner,
            effect="write",
            action="research.paper_analysis",
            journal=kinds,
            context_runner=True,
        )
        patcher = patch.dict(jobs_module._KINDS, {kind_name: spec})
        self.addCleanup(patcher.stop)
        patcher.start()
        snapshot = jobs_module.create_job(
            "alice",
            kind_name,
            {},
            profile_scope=self.profile,
            agent_write=write,
            actor="openclaw",
        )
        return snapshot["job_id"]

    def test_generic_t2_job_normalizes_kind_and_journals_in_worker(self) -> None:
        import threading

        from nblane.core import agent_journal
        from nblane.web_api import jobs as jobs_module

        started = threading.Event()
        release = threading.Event()
        self.addCleanup(release.set)

        def runner(_profile, _job_input, _report, ctx):
            started.set()
            release.wait(5)
            self._commit_source(ctx, "Agent async import")
            return {"ok": True}

        self._register_job("test-agent-t2-job", runner, action="research.import")
        client = self._client(self.root, login="openclaw")
        job_body = {"kind": "  test-agent-t2-job  ", "input": {}}
        with patch(
            "nblane.core.agent_ops.agent_journal.snapshot",
            wraps=agent_journal.snapshot,
        ) as snapshot:
            first = client.post(f"{BASE}/jobs", json=job_body)
            self.assertEqual(first.status_code, 428, first.text)
            self.assertFalse(
                any(job.get("kind") == "test-agent-t2-job" for job in jobs_module._JOBS.values())
            )
            confirm_id = first.json()["confirmation"]["confirm_id"]
            created = client.post(
                f"{BASE}/jobs",
                json=job_body,
                headers={agent_policy.CONFIRM_HEADER: confirm_id},
            )
            self.assertEqual(created.status_code, 202, created.text)
            self.assertTrue(started.wait(2))
            self.assertEqual(snapshot.call_count, 0)
            release.set()
            final = self._wait_final(client, created.json()["job_id"])

        self.assertEqual(final["job"]["status"], "done")
        self.assertEqual(final["job"]["kind"], "test-agent-t2-job")
        self.assertGreaterEqual(snapshot.call_count, 2)
        self.assertIn("Agent async import", self._source_titles())
        self.assertFalse(
            agent_policy.consume(
                confirm_id,
                actor="openclaw",
                fingerprint=agent_policy.fingerprint("POST", f"{BASE}/jobs", job_body),
            )
        )
        entries = self.journal(client)
        self.assertEqual(entries[0]["action"], "research.import")
        self.assertEqual(entries[0]["tier"], "T2")
        undone = client.post(f"{BASE}/agent/journal/{entries[0]['id']}/undo")
        self.assertEqual(undone.status_code, 200, undone.text)
        self.assertNotIn("Agent async import", self._source_titles())

    def test_worker_snapshot_failure_prevents_domain_commit(self) -> None:
        def runner(_profile, _job_input, _report, ctx):
            self._commit_source(ctx, "Must not exist")
            return {"ok": True}

        self._register_job("test-agent-snapshot-failure", runner, action="research_source.patch")
        client = self._client(self.root, login="openclaw")
        with patch("nblane.core.agent_ops.agent_journal.prepare", side_effect=OSError("snapshot down")):
            created = client.post(
                f"{BASE}/jobs", json={"kind": "test-agent-snapshot-failure", "input": {}}
            )
            self.assertEqual(created.status_code, 202, created.text)
            final = self._wait_final(client, created.json()["job_id"])

        self.assertEqual(final["job"]["status"], "failed")
        self.assertEqual(final["job"]["error"]["code"], "agent_journal_failed")
        self.assertFalse(final["job"]["write_committed"])
        self.assertNotIn("Must not exist", self._source_titles())

    def test_worker_journal_failure_after_commit_is_explicit_partial_failure(self) -> None:
        def runner(_profile, _job_input, _report, ctx):
            self._commit_source(ctx, "Retained without journal")
            return {"ok": True}

        self._register_job("test-agent-journal-failure", runner, action="research_source.patch")
        client = self._client(self.root, login="openclaw")
        with patch("nblane.core.agent_ops.agent_journal.record", side_effect=OSError("journal down")):
            created = client.post(
                f"{BASE}/jobs", json={"kind": "test-agent-journal-failure", "input": {}}
            )
            self.assertEqual(created.status_code, 202, created.text)
            final = self._wait_final(client, created.json()["job_id"])

        self.assertEqual(final["job"]["status"], "failed")
        self.assertEqual(final["job"]["error"]["code"], "agent_journal_failed")
        self.assertTrue(final["job"]["write_committed"])
        self.assertIn("Retained without journal", self._source_titles())
        self.assertIn("已保留部分写入", final["job"]["error"]["message"])

    def test_dedicated_connector_import_stays_t2_and_journals_worker_commit(self) -> None:
        from types import SimpleNamespace

        from nblane.core.research_connectors import ConnectorItem, upsert_connector

        with patch("nblane.core.research_connectors.git_backup.record_change"):
            connector = upsert_connector(self.profile, provider="github", query="octo/demo")
        item = ConnectorItem(
            provider="github",
            title="Dedicated connector import",
            url="https://github.com/octo/dedicated",
            external_id="repo-dedicated",
        )
        adapter = SimpleNamespace(discover=lambda _config: [item])
        client = self._client(self.root, login="openclaw")
        url = f"{BASE}/research/connectors/{connector['id']}/import"
        body = {
            "fingerprints": [],
            "target": {"kind": "source_inbox", "node_id": ""},
        }
        with patch.dict("nblane.core.research_connectors.ADAPTERS", {"github": adapter}):
            first = client.post(url, json=body)
            self.assertEqual(first.status_code, 428, first.text)
            self.assertEqual(first.json()["confirmation"]["action"], "research.import")
            created = client.post(
                url,
                json=body,
                headers={agent_policy.CONFIRM_HEADER: first.json()["confirmation"]["confirm_id"]},
            )
            self.assertEqual(created.status_code, 202, created.text)
            final = self._wait_final(client, created.json()["job_id"])

        self.assertEqual(final["job"]["status"], "done")
        self.assertIn("Dedicated connector import", self._source_titles())
        self.assertEqual(self.journal(client)[0]["action"], "research.import")

    def test_paper_reattach_does_not_reserve_or_journal_again(self) -> None:
        import time

        from nblane.core.research_sources import add_research_source, mutate_research_sources
        from nblane.web_api import jobs as jobs_module
        from nblane.web_api import research_papers

        source_id = "source:paper:demo"
        mutate_research_sources(
            self.profile,
            lambda inbox: add_research_source(
                inbox,
                source_id=source_id,
                title="Paper",
                kind="paper",
                url="https://example.com/paper",
            ),
        )
        job_id = "job-paper-reattach"
        record = {
            "job_id": job_id,
            "profile": "alice",
            "kind": "paper-quick-analysis",
            "status": "running",
            "phase": "reading",
            "message": "Reading",
            "created_at": time.time(),
            "started_at": 0.0,
            "finished_at": 0.0,
            "error": None,
            "result": None,
            "events": [],
            "_started_monotonic": 0.0,
            "_finished_monotonic": 0.0,
        }
        active = {(research_papers._scope(self.profile), source_id, "paper-quick-analysis"): job_id}
        client = self._client(self.root, login="openclaw")
        with (
            patch.dict(jobs_module._JOBS, {job_id: record}, clear=False),
            patch.dict(research_papers._ACTIVE_JOBS, active, clear=False),
            patch(
                "nblane.web_api.agent_guard.agent_ops.reserve",
                side_effect=AssertionError("reattach must not reserve"),
            ),
        ):
            response = client.post(
                f"{BASE}/research/papers/{source_id}/analysis-jobs",
                json={"kind": "paper-quick-analysis"},
            )

        self.assertEqual(response.status_code, 202, response.text)
        self.assertEqual(response.json()["job_id"], job_id)
        self.assertEqual(self.journal(client), [])

    def test_real_prepare_journals_derived_jsonl_and_undo(self) -> None:
        from nblane.core import agent_journal
        from nblane.core.research_papers import load_paper_pages, load_paper_segments
        from nblane.core.research_sources import load_research_sources
        from nblane.core.research_workspace import source_slug

        source_id = "source:paper:demo"
        self._paper_fixture(source_id)
        client = self._client(self.root, login="openclaw")
        job_id = self._start_prepare_job("test-real-prepare-journal", source_id)
        final = self._wait_final(client, job_id)
        self.assertEqual(final["job"]["status"], "done", final)
        self.assertTrue(load_paper_pages(self.profile, source_id))
        self.assertTrue(load_paper_segments(self.profile, source_id))

        entry = next(
            row
            for row in agent_journal.recent(self.profile)
            if row["id"] == self.journal(client)[0]["id"]
        )
        self.assertEqual(entry["action"], "research.paper_analysis")
        entities = {change["entity"] for change in entry["changes"]}
        slug = source_slug(source_id)
        self.assertIn(agent_journal.jsonl_kind(f"research/paper-pages/{slug}.jsonl"), entities)
        self.assertIn(agent_journal.jsonl_kind(f"research/paper-segments/{slug}.jsonl"), entities)
        self.assertIn("research_source", entities)

        undone = client.post(f"{BASE}/agent/journal/{entry['id']}/undo")
        self.assertEqual(undone.status_code, 200, undone.text)
        self.assertEqual(load_paper_pages(self.profile, source_id), [])
        self.assertEqual(load_paper_segments(self.profile, source_id), [])
        source = load_research_sources(self.profile).by_id()[source_id]
        self.assertFalse(source.metadata.get("reading_artifacts_status"))

    def test_real_prepare_cancellation_stops_later_segments_and_journals_pages(self) -> None:
        import threading

        from nblane.core import agent_journal
        from nblane.core import research_papers as paper_core
        from nblane.core.research_papers import load_paper_pages, load_paper_segments
        from nblane.core.research_sources import load_research_sources
        from nblane.core.research_workspace import source_slug
        from nblane.web_api import jobs as jobs_module

        source_id = "source:paper:demo"
        self._paper_fixture(source_id)
        client = self._client(self.root, login="openclaw")
        pages_written = threading.Event()
        release = threading.Event()
        self.addCleanup(release.set)
        extract_pages = paper_core.extract_paper_pages

        def gated_extract(*args, **kwargs):
            pages = extract_pages(*args, **kwargs)
            pages_written.set()
            release.wait(5)
            return pages

        with (
            patch.object(paper_core, "extract_paper_pages", side_effect=gated_extract),
            patch.object(
                paper_core,
                "migrate_legacy_translations_to_segments",
                wraps=paper_core.migrate_legacy_translations_to_segments,
            ) as migration,
        ):
            job_id = self._start_prepare_job("test-real-prepare-cancel", source_id)
            self.assertTrue(pages_written.wait(3))
            stopped = client.delete(f"{BASE}/jobs/{job_id}")
            self.assertEqual(stopped.status_code, 200, stopped.text)
            self.assertEqual(stopped.json()["job"]["status"], "running")
            self.assertTrue(stopped.json()["job"]["cancel_requested"])
            release.set()
            final = self._wait_final(client, job_id)

        migration.assert_not_called()
        self.assertEqual(final["job"]["status"], "failed")
        self.assertEqual(final["job"]["error"]["code"], "job_cancelled")
        self.assertTrue(final["job"]["write_committed"])
        self.assertIn("已保留部分写入", final["job"]["error"]["message"])
        self.assertTrue(load_paper_pages(self.profile, source_id))
        self.assertEqual(load_paper_segments(self.profile, source_id), [])
        source = load_research_sources(self.profile).by_id()[source_id]
        self.assertFalse(source.metadata.get("reading_artifacts_status"))
        self.assertFalse(source.metadata.get("reading_artifacts_ready_at"))

        entry = next(
            row
            for row in agent_journal.recent(self.profile)
            if row["id"] == self.journal(client)[0]["id"]
        )
        entities = {change["entity"] for change in entry["changes"]}
        slug = source_slug(source_id)
        self.assertIn(agent_journal.jsonl_kind(f"research/paper-pages/{slug}.jsonl"), entities)
        self.assertNotIn(agent_journal.jsonl_kind(f"research/paper-segments/{slug}.jsonl"), entities)
        self.assertIn("research_source", entities)
        self.assertEqual(jobs_module._JOBS[job_id]["commit_summary"], "准备论文阅读产物")
