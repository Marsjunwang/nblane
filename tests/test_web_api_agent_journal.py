"""Agent write policy: journal + undo (T1) and chat confirmation (T2).

Reuses the tmp-profile / auth-on fixtures of test_web_api_agent_writeback.
Real profiles/ is never touched.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

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

    def test_inbox_capture_undo(self) -> None:
        client = self._agent()
        response = client.post(f"{BASE}/inbox", json={"title": "Read the SLAM paper"})
        self.assertEqual(response.status_code, 201, response.text)
        entry = self._undo_latest(client)
        self.assertIn("Read the SLAM paper", entry["summary"])
        titles = [i["title"] for i in _yaml(self.profile, "inbox.yaml").get("items") or []]
        self.assertNotIn("Read the SLAM paper", titles)


class TestGuardPolicy(JournalTestBase):
    def test_web_only_routes_refused_for_agents(self) -> None:
        client = self._client(self.root, login="openclaw")
        for method, url in (
            ("POST", f"{BASE}/public-site/deploy"),
            ("PATCH", f"{BASE}/settings"),
            ("POST", f"{BASE}/activity/act:x/apply"),
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
    """Growth log + profile-model candidates are reachable over HTTP."""

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

    def test_profile_model_candidate_queues_pending_item(self) -> None:
        client = self._client(self.root, login="openclaw")
        response = client.post(
            f"{BASE}/activity/profile-model",
            json={"field": "preferences.tone", "proposed_value": "concise", "rationale": "asked twice"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        item = response.json()
        self.assertEqual(item["status"], "pending")
        self.assertEqual(item["candidate_type"], "profile_model")
        self.assertEqual(item["payload"]["proposed_value"], "concise")
        # A review submission changes no profile facts: nothing to undo.
        self.assertEqual(self.journal(client), [])

    def test_profile_model_candidate_validation(self) -> None:
        client = self._client(self.root, login="openclaw")
        response = client.post(f"{BASE}/activity/profile-model", json={"field": "x", "proposed_value": " "})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_profile_model_candidate")
