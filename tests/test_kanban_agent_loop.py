"""End-to-end kanban <-> agent dispatch loop against a tmp profile.

No LLM, no network: every step asserts on-disk file contents, not just
in-memory state. Chain: quick-add card -> stable id -> dispatch to agent ->
external candidate -> human approval -> Done/crystallized -> evidence draft
referencing the original kanban task id.
"""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

import yaml

from nblane.core.agent_activity import (
    load_agent_activity,
    update_activity_status,
)
from nblane.core.agent_tasks import (
    dispatch_agent_task_for_kanban,
    get_agent_task,
    load_agent_tasks,
    submit_agent_task_candidate,
)
from nblane.core.evidence_migrate import refresh_from_crystallized_tasks
from nblane.core.file_write import atomic_write_text
from nblane.core.kanban_events import build_quick_add_task
from nblane.core.kanban_io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
    parse_kanban,
    save_kanban,
)


class TestKanbanAgentLoop(unittest.TestCase):
    """The full card -> dispatch -> candidate -> approval -> evidence loop."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.prof = Path(self.tmp.name) / "alice"
        self.prof.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _kanban_text(self) -> str:
        return (self.prof / "kanban.md").read_text(encoding="utf-8")

    def _agent_tasks_doc(self) -> dict:
        return yaml.safe_load(
            (self.prof / "agent-tasks.yaml").read_text(encoding="utf-8")
        )

    def _activity_doc(self) -> dict:
        return yaml.safe_load(
            (self.prof / "agent-activity.yaml").read_text(encoding="utf-8")
        )

    def test_full_dispatch_loop(self) -> None:
        # -- Step 1: quick-add creation path; the id is stable across edits.
        sections = {s: [] for s in (KANBAN_DOING, KANBAN_DONE, KANBAN_QUEUE, KANBAN_SOMEDAY)}
        target, _task, intent = build_quick_add_task(
            "Write the VLA benchmark plan",
            section=KANBAN_QUEUE,
            today=date(2026, 9, 16),
        )
        self.assertEqual(target, KANBAN_QUEUE)
        sections[target].append(_task)
        save_kanban(self.prof, sections)

        parsed = parse_kanban(self.prof)
        task = parsed[KANBAN_QUEUE][-1]
        self.assertTrue(task.id.startswith("kb_"))
        first_id = task.id
        self.assertIn(f"  - id: {first_id}", self._kanban_text())

        parsed[KANBAN_QUEUE][-1] = replace(
            task, title="Write the VLA benchmark plan v2"
        )
        save_kanban(self.prof, parsed)
        task = parse_kanban(self.prof)[KANBAN_QUEUE][-1]
        self.assertEqual(task.id, first_id)
        self.assertEqual(task.title, "Write the VLA benchmark plan v2")

        # -- Step 2: dispatch to an external agent; card binds agent_task_id.
        item = dispatch_agent_task_for_kanban(
            self.prof,
            task,
            harness="codex",
            role="researcher",
            instruction="Focus on the eval harness",
            section=KANBAN_QUEUE,
        )
        agent_id = item["id"]
        self.assertTrue(agent_id.startswith("agenttask_"))
        self.assertEqual(item["status"], "ready")
        self.assertEqual(item["related"]["kanban_task_id"], first_id)
        self.assertEqual(
            item["payload"]["instruction"], "Focus on the eval harness"
        )
        self.assertEqual(item["payload"]["task"]["title"], task.title)
        self.assertTrue(item.get("activity_item_id"))

        tasks_doc = self._agent_tasks_doc()
        self.assertEqual(len(tasks_doc["tasks"]), 1)
        self.assertEqual(tasks_doc["tasks"][0]["id"], agent_id)
        self.assertEqual(
            tasks_doc["tasks"][0]["related"]["kanban_task_id"], first_id
        )

        parsed = parse_kanban(self.prof)
        parsed[KANBAN_QUEUE][-1] = replace(
            parsed[KANBAN_QUEUE][-1], agent_task_id=agent_id
        )
        save_kanban(self.prof, parsed)
        self.assertIn(f"  - agent_task_id: {agent_id}", self._kanban_text())
        task = parse_kanban(self.prof)[KANBAN_QUEUE][-1]
        self.assertEqual(task.agent_task_id, agent_id)
        self.assertEqual(task.id, first_id)

        # A second dispatch of the same card creates a fresh id and keeps
        # the first one in history.
        item2 = dispatch_agent_task_for_kanban(
            self.prof, task, harness="opencode", role="reviewer"
        )
        self.assertNotEqual(item2["id"], agent_id)
        tasks_doc = self._agent_tasks_doc()
        self.assertEqual(len(tasks_doc["tasks"]), 2)
        self.assertEqual(
            {t["related"]["kanban_task_id"] for t in tasks_doc["tasks"]},
            {first_id},
        )

        # -- Step 3: the external agent submits a reviewable candidate.
        submitted = submit_agent_task_candidate(
            self.prof,
            agent_id,
            summary="Benchmark plan drafted",
            changed_paths=["profiles/alice/kanban.md"],
            warnings=["skimmed related work"],
            result_payload={"draft": "plan.md outline"},
        )
        self.assertIsNotNone(submitted)
        assert submitted is not None
        self.assertEqual(submitted["status"], "candidate_ready")
        stored = get_agent_task(self.prof, agent_id)
        self.assertEqual(stored["result_summary"], "Benchmark plan drafted")
        self.assertEqual(
            stored["result_payload"], {"draft": "plan.md outline"}
        )

        activity_item_id = item["activity_item_id"]
        activity_doc = self._activity_doc()
        act_item = next(
            entry
            for entry in activity_doc["items"]
            if entry["id"] == activity_item_id
        )
        self.assertEqual(act_item["status"], "pending")
        result_mirror = act_item["payload"]["agent_task_result"]
        self.assertEqual(result_mirror["status"], "candidate_ready")
        self.assertEqual(result_mirror["summary"], "Benchmark plan drafted")
        self.assertEqual(
            result_mirror["changed_paths"], ["profiles/alice/kanban.md"]
        )
        # The untouched second dispatch stays ready.
        self.assertEqual(
            get_agent_task(self.prof, item2["id"])["status"], "ready"
        )

        # -- Step 4: a human approves the candidate in Agent Activity.
        applied = update_activity_status(
            self.prof,
            activity_item_id,
            "applied",
            changed_paths=["profiles/alice/kanban.md"],
        )
        self.assertEqual(applied["status"], "applied")
        self.assertTrue(applied.get("applied_at"))
        act_item = next(
            entry
            for entry in self._activity_doc()["items"]
            if entry["id"] == activity_item_id
        )
        self.assertEqual(act_item["status"], "applied")

        # -- Step 5: Done + crystallized -> evidence draft referencing the id.
        sections = parse_kanban(self.prof)
        done_task = replace(
            sections[KANBAN_QUEUE][-1],
            done=True,
            completed_on="2026-09-16",
            crystallized=True,
            outcome="benchmark plan v2 shipped",
        )
        sections[KANBAN_QUEUE] = []
        sections[KANBAN_DONE] = [done_task]
        save_kanban(self.prof, sections)
        self.assertIn("  - crystallized: true", self._kanban_text())

        refreshed = refresh_from_crystallized_tasks(self.prof, entries=[])
        proposals = refreshed["proposals"]
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0]["kind"], "new")
        self.assertEqual(proposals[0]["task_id"], first_id)
        self.assertEqual(proposals[0]["kanban_refs"], [f"kanban:{first_id}"])

        # Apply the draft to the pool (same row shape as the deterministic
        # Done -> evidence writer) and assert the pool file contents.
        prop = proposals[0]
        pool = {
            "schema_version": "2.0",
            "profile": "alice",
            "updated": "2026-09-16",
            "evidence_entries": [
                {
                    "id": "ev_loop1",
                    "type": "practice",
                    "title": prop["title"],
                    "date": prop["completed_on"],
                    "origin": "kanban_task",
                    "origin_ref": prop["origin_ref"],
                    "kanban_refs": list(prop["kanban_refs"]),
                    "original_content": prop["original_content"],
                    "original_content_hash": prop["original_content_hash"],
                    "review_status": "needs_review",
                }
            ],
        }
        atomic_write_text(
            self.prof / "evidence-pool.yaml",
            "# Evidence pool for alice\n\n" + yaml.dump(pool, allow_unicode=True),
        )
        pool_back = yaml.safe_load(
            (self.prof / "evidence-pool.yaml").read_text(encoding="utf-8")
        )
        entry = pool_back["evidence_entries"][0]
        self.assertEqual(entry["kanban_refs"], [f"kanban:{first_id}"])
        self.assertEqual(entry["origin"], "kanban_task")
        self.assertEqual(entry["review_status"], "needs_review")

        # Loop closure: re-refreshing repairs the existing row in place
        # (kind "update") instead of drafting a duplicate.
        refreshed2 = refresh_from_crystallized_tasks(
            self.prof, entries=pool_back["evidence_entries"]
        )
        self.assertEqual(len(refreshed2["proposals"]), 1)
        self.assertEqual(refreshed2["proposals"][0]["kind"], "update")
        self.assertEqual(refreshed2["proposals"][0]["evidence_id"], "ev_loop1")

        # Sanity: the library loaders read the same files back identically.
        self.assertEqual(
            load_agent_tasks(self.prof)["tasks"][0]["id"], agent_id
        )
        self.assertEqual(
            load_agent_activity(self.prof)["items"][0]["status"], "applied"
        )


if __name__ == "__main__":
    unittest.main()
