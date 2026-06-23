"""Host-level tests for the shared evidence-editor event layer.

Exercises the extracted handlers end to end against a temp profile, proving the
event layer still reads/writes pool + skill tree correctly after extraction.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from nblane.evidence_editor_host import (
    EvidenceEditorHost,
    compact_evidence_row,
    pool_index_by_id,
    save_evidence_pool,
)


class _FakeSessionState(dict):
    """dict that also supports attribute-free .get/.pop used by the host."""


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


class TestPureHelpers(unittest.TestCase):
    def test_pool_index_by_id_skips_blank(self) -> None:
        idx = pool_index_by_id([{"id": "a"}, {"id": ""}, {"id": "b"}])
        self.assertEqual(idx, {"a": 0, "b": 2})

    def test_compact_row_drops_empty(self) -> None:
        out = compact_evidence_row(
            {"id": "e1", "title": "T", "summary": "", "url": "http://x"}
        )
        self.assertNotIn("summary", out)
        self.assertEqual(out["url"], "http://x")
        self.assertEqual(out["type"], "practice")


class TestEvidenceEditorHost(unittest.TestCase):
    """Handlers operate on a temp profile with a fake Streamlit module."""

    def setUp(self) -> None:
        from nblane.core import io as io_mod
        from nblane.core import paths as paths_mod
        from nblane.core import profile_io
        from nblane.core import project_board

        self._tmp = tempfile.TemporaryDirectory()
        tmp_path = Path(self._tmp.name)
        self._origs = {
            m: m.PROFILES_DIR for m in (paths_mod, profile_io, io_mod, project_board)
        }
        for m in self._origs:
            m.PROFILES_DIR = tmp_path
        self.pdir = tmp_path / "dev"
        self.pdir.mkdir(parents=True)
        _write_yaml(
            self.pdir / "evidence-pool.yaml",
            {
                "profile": "dev",
                "evidence_entries": [
                    {
                        "id": "e1",
                        "type": "practice",
                        "title": "First",
                        "date": "2026-01-02",
                        "origin": "manual_daily",
                        "origin_ref": "manual:e1",
                        "original_content": "raw",
                        "formatted_content": "formatted",
                        "project_refs": ["project:demo"],
                    },
                ],
            },
        )
        _write_yaml(
            self.pdir / "skill-tree.yaml",
            {
                "profile": "dev",
                "schema": "robotics-engineer",
                "updated": "2026-01-01",
                "nodes": [
                    {"id": "ros2_basics", "status": "solid", "evidence_refs": []},
                    {"id": "nav2", "status": "learning", "evidence_refs": ["e1"]},
                ],
            },
        )
        _write_yaml(
            self.pdir / "project-board.yaml",
            {
                "profile": "dev",
                "project_cases": [
                    {
                        "id": "project:demo",
                        "title": "Demo Project",
                        "goal_refs": ["goal:demo"],
                    }
                ],
            },
        )

        # Fake Streamlit: collect messages, real-ish session_state.
        self.fake_st = MagicMock()
        self.fake_st.session_state = _FakeSessionState()
        self._patch_st = patch(
            "nblane.evidence_editor_host.st", self.fake_st
        )
        self._patch_st.start()
        # Avoid touching the real web cache / git backup during tests.
        self._patches = [
            patch("nblane.evidence_editor_host.clear_web_cache", lambda: None),
            patch(
                "nblane.evidence_editor_host.stash_git_backup_results",
                lambda: None,
            ),
            patch(
                "nblane.evidence_editor_host.assert_files_current",
                lambda paths: None,
            ),
            patch(
                "nblane.evidence_editor_host.refresh_file_snapshots",
                lambda paths: None,
            ),
            patch(
                "nblane.evidence_editor_host.write_generated_blocks",
                lambda pdir: None,
            ),
            patch(
                "nblane.evidence_editor_host.clear_web_cache",
                lambda: None,
            ),
            patch(
                "nblane.core.web_preferences.git_backup.record_change",
                lambda paths, action="": None,
            ),
        ]
        for p in self._patches:
            p.start()

        self.host = EvidenceEditorHost("dev", ui={})

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        self._patch_st.stop()
        for m, v in self._origs.items():
            m.PROFILES_DIR = v
        self._tmp.cleanup()

    def _pool(self) -> list[dict]:
        raw = yaml.safe_load(
            (self.pdir / "evidence-pool.yaml").read_text(encoding="utf-8")
        )
        return raw.get("evidence_entries") or []

    def _tree_nodes(self) -> list[dict]:
        raw = yaml.safe_load(
            (self.pdir / "skill-tree.yaml").read_text(encoding="utf-8")
        )
        return raw.get("nodes") or []

    def _write_outputs(self, outputs: list[dict]) -> None:
        _write_yaml(self.pdir / "outputs.yaml", {"outputs": outputs})

    def _web_preferences(self) -> dict:
        path = self.pdir / "web-preferences.yaml"
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def test_save_evidence_writes_pool(self) -> None:
        ok = self.host.handle_event(
            {
                "action": "save_evidence",
                "event_id": "ev-1",
                "payload": {"id": "e1", "fields": {"title": "Renamed", "url": "http://x"}},
            }
        )
        self.assertTrue(ok)
        row = next(r for r in self._pool() if r["id"] == "e1")
        self.assertEqual(row["title"], "Renamed")
        self.assertEqual(row["url"], "http://x")

    def test_add_evidence_appends_row(self) -> None:
        ok = self.host.handle_event(
            {
                "action": "add_evidence",
                "event_id": "ev-2",
                "payload": {
                    "fields": {
                        "title": "Brand new",
                        "type": "project",
                        "date": "2026-01-03",
                        "original_content": "manual raw",
                        "formatted_content": "manual formatted",
                        "project_refs": ["project:demo"],
                    }
                },
            }
        )
        self.assertTrue(ok)
        titles = [r["title"] for r in self._pool()]
        self.assertIn("Brand new", titles)

    def test_deprecate_marks_row(self) -> None:
        ok = self.host.handle_event(
            {
                "action": "deprecate_evidence",
                "event_id": "ev-3",
                "payload": {"id": "e1", "replaced_by": "e9"},
            }
        )
        self.assertTrue(ok)
        row = next(r for r in self._pool() if r["id"] == "e1")
        self.assertTrue(row.get("deprecated"))
        self.assertEqual(row.get("replaced_by"), "e9")

    def test_link_skills_reconciles_nodes(self) -> None:
        # e1 starts on nav2 only; move it to ros2_basics + new node.
        ok = self.host.handle_event(
            {
                "action": "link_skills",
                "event_id": "ev-4",
                "payload": {"id": "e1", "skill_ids": ["ros2_basics", "perception"]},
            }
        )
        self.assertTrue(ok)
        by_id = {n["id"]: n for n in self._tree_nodes()}
        self.assertIn("e1", by_id["ros2_basics"].get("evidence_refs") or [])
        self.assertNotIn("e1", by_id["nav2"].get("evidence_refs") or [])
        self.assertEqual(by_id["perception"]["status"], "learning")
        self.assertIn("e1", by_id["perception"]["evidence_refs"])

    def test_link_skill_appends_evidence_to_one_node(self) -> None:
        # Skill-centric: attach e1 to ros2_basics WITHOUT removing it from nav2
        # (append semantics, unlike the reconcile of link_skills).
        ok = self.host.handle_event(
            {
                "action": "link_skill",
                "event_id": "ev-ls1",
                "payload": {"skill_id": "ros2_basics", "evidence_ids": ["e1"]},
            }
        )
        self.assertTrue(ok)
        by_id = {n["id"]: n for n in self._tree_nodes()}
        self.assertIn("e1", by_id["ros2_basics"].get("evidence_refs") or [])
        # nav2 still keeps e1 (append, not reconcile).
        self.assertIn("e1", by_id["nav2"].get("evidence_refs") or [])

    def test_link_skill_creates_missing_node_as_learning(self) -> None:
        ok = self.host.handle_event(
            {
                "action": "link_skill",
                "event_id": "ev-ls2",
                "payload": {"skill_id": "slam", "evidence_ids": ["e1"]},
            }
        )
        self.assertTrue(ok)
        by_id = {n["id"]: n for n in self._tree_nodes()}
        self.assertIn("slam", by_id)
        self.assertEqual(by_id["slam"]["status"], "learning")
        self.assertEqual(by_id["slam"]["evidence_refs"], ["e1"])

    def test_link_skill_noop_without_skill_or_evidence(self) -> None:
        self.assertFalse(
            self.host.handle_event(
                {
                    "action": "link_skill",
                    "event_id": "ev-ls3",
                    "payload": {"skill_id": "", "evidence_ids": ["e1"]},
                }
            )
        )
        self.assertFalse(
            self.host.handle_event(
                {
                    "action": "link_skill",
                    "event_id": "ev-ls4",
                    "payload": {"skill_id": "ros2_basics", "evidence_ids": []},
                }
            )
        )

    def test_save_evidence_writes_experience_and_source_refs(self) -> None:
        ok = self.host.handle_event(
            {
                "action": "save_evidence",
                "event_id": "ev-refs",
                "payload": {
                    "id": "e1",
                    "fields": {
                        "experience_refs": ["exp:acme", " "],
                        "source_refs": ["src:paper1"],
                    },
                },
            }
        )
        self.assertTrue(ok)
        row = next(r for r in self._pool() if r["id"] == "e1")
        self.assertEqual(row.get("experience_refs"), ["exp:acme"])
        self.assertEqual(row.get("source_refs"), ["src:paper1"])

    def test_event_dedup_by_id(self) -> None:
        ev = {
            "action": "save_evidence",
            "event_id": "dup-1",
            "payload": {"id": "e1", "fields": {"title": "Once"}},
        }
        self.assertTrue(self.host.handle_event(ev))
        # Same event id again -> treated as a resend, ignored.
        self.assertFalse(self.host.handle_event(ev))

    def test_suggest_skills_stashes_llm_without_writing(self) -> None:
        # The LLM-suggest action must stash candidates for the next render and
        # never mutate skill-tree links (human still confirms via chips).
        from nblane.core.models import GapResult

        fake = GapResult(
            top_matches=[
                {"id": "nav2", "label": "Nav2", "score": 7, "source": "rule+llm"},
                {"id": "perception", "label": "Perception", "score": 3, "source": "llm"},
            ]
        )
        before = self._tree_nodes()
        with patch(
            "nblane.core.gap.analyze", return_value=fake
        ) as analyze_mock:
            ok = self.host.handle_event(
                {
                    "action": "suggest_skills",
                    "event_id": "sk-1",
                    "payload": {"id": "e1"},
                }
            )
        self.assertTrue(ok)
        analyze_mock.assert_called_once()
        # use_llm_router must be on for this explicit, slow path.
        self.assertTrue(analyze_mock.call_args.kwargs.get("use_llm_router"))
        stash = self.fake_st.session_state.get(
            self.host._k("skill_suggest")
        )
        self.assertEqual(stash["id"], "e1")
        self.assertEqual(
            [s["id"] for s in stash["suggestions"]], ["nav2", "perception"]
        )
        # Skill-tree nodes are unchanged (no write happened).
        self.assertEqual(self._tree_nodes(), before)

    def test_unknown_action_returns_false(self) -> None:
        self.assertFalse(
            self.host.handle_event(
                {"action": "nope", "event_id": "x", "payload": {}}
            )
        )

    def test_session_keys_are_prefixed(self) -> None:
        # last_id is namespaced by prefix + profile.
        self.host.handle_event(
            {
                "action": "save_evidence",
                "event_id": "ev-5",
                "payload": {"id": "e1", "fields": {"title": "Y"}},
            }
        )
        self.assertEqual(
            self.fake_st.session_state.get("evidence_editor_last_id_dev"), "e1"
        )

    def test_custom_prefix_isolates_state(self) -> None:
        other = EvidenceEditorHost("dev", key_prefix="project_board", ui={})
        self.assertEqual(other._k("last_id"), "project_board_last_id_dev")
        self.assertNotEqual(other._k("last_id"), self.host._k("last_id"))

    def test_bulk_apply_sets_field_on_many(self) -> None:
        # Add a second row so the bulk action spans more than one id.
        self.host.handle_event(
            {
                "action": "add_evidence",
                "event_id": "seed-1",
                "payload": {"fields": {"title": "Second"}},
            }
        )
        ids = [r["id"] for r in self._pool()]
        ok = self.host.handle_event(
            {
                "action": "bulk_apply",
                "event_id": "bulk-1",
                "payload": {
                    "ids": ids,
                    "field": "review_status",
                    "value": "reviewed",
                },
            }
        )
        self.assertTrue(ok)
        statuses = {r["id"]: r.get("review_status") for r in self._pool()}
        self.assertTrue(all(v == "reviewed" for v in statuses.values()))

    def test_bulk_apply_deprecate_action(self) -> None:
        ok = self.host.handle_event(
            {
                "action": "bulk_apply",
                "event_id": "bulk-2",
                "payload": {"ids": ["e1"], "bulk_action": "deprecate"},
            }
        )
        self.assertTrue(ok)
        row = next(r for r in self._pool() if r["id"] == "e1")
        self.assertTrue(row.get("deprecated"))

    def test_bulk_apply_link_skills_action(self) -> None:
        ok = self.host.handle_event(
            {
                "action": "bulk_apply",
                "event_id": "bulk-3",
                "payload": {
                    "ids": ["e1"],
                    "bulk_action": "link_skills",
                    "skill_ids": ["ros2_basics"],
                },
            }
        )
        self.assertTrue(ok)
        by_id = {n["id"]: n for n in self._tree_nodes()}
        self.assertIn("e1", by_id["ros2_basics"].get("evidence_refs") or [])

    def test_bulk_apply_rejects_out_of_domain_value(self) -> None:
        ok = self.host.handle_event(
            {
                "action": "bulk_apply",
                "event_id": "bulk-4",
                "payload": {
                    "ids": ["e1"],
                    "field": "review_status",
                    "value": "not_a_status",
                },
            }
        )
        self.assertFalse(ok)
        row = next(r for r in self._pool() if r["id"] == "e1")
        self.assertNotIn("review_status", row)

    def test_bulk_create_from_output_creates_two_rows_with_one_save(self) -> None:
        self._write_outputs(
            [
                {
                    "id": "out_a",
                    "title": "Output A",
                    "status": "published",
                    "date": "2026-03-01",
                    "summary": "Output A summary.",
                    "project_refs": ["project:demo"],
                },
                {
                    "id": "out_b",
                    "title": "Output B",
                    "status": "published",
                    "date": "2026-03-02",
                    "summary": "Output B summary.",
                    "project_refs": ["project:demo"],
                },
            ]
        )
        real_save = save_evidence_pool
        with patch(
            "nblane.evidence_editor_host.save_evidence_pool",
            wraps=real_save,
        ) as save_mock:
            ok = self.host.handle_event(
                {
                    "action": "bulk_create_from_output",
                    "event_id": "out-bulk-1",
                    "payload": {
                        "items": [
                            {"output_id": "out_a", "source_kind": "output"},
                            {"output_id": "out_b", "source_kind": "output"},
                        ]
                    },
                }
            )

        self.assertTrue(ok)
        save_mock.assert_called_once()
        by_ref = {r.get("origin_ref"): r for r in self._pool()}
        self.assertEqual(by_ref["output:out_a"]["title"], "Output A")
        self.assertEqual(by_ref["output:out_b"]["title"], "Output B")

    def test_bulk_create_from_output_uses_payload_project_refs(self) -> None:
        self._write_outputs(
            [
                {
                    "id": "needs_project",
                    "title": "Needs project",
                    "status": "published",
                    "date": "2026-03-03",
                    "summary": "Needs project summary.",
                }
            ]
        )
        ok = self.host.handle_event(
            {
                "action": "bulk_create_from_output",
                "event_id": "out-bulk-2",
                "payload": {
                    "items": [
                        {
                            "output_id": "needs_project",
                            "source_kind": "output",
                            "project_refs": ["project:demo"],
                        }
                    ]
                },
            }
        )

        self.assertTrue(ok)
        row = next(r for r in self._pool() if r.get("origin_ref") == "output:needs_project")
        self.assertEqual(row["project_refs"], ["project:demo"])

    def test_bulk_create_from_output_updates_existing_source(self) -> None:
        rows = self._pool()
        rows.append(
            {
                "id": "existing_output",
                "type": "practice",
                "title": "Old title",
                "origin": "output",
                "origin_ref": "output:update_me",
                "original_content": "old raw",
                "formatted_content": "old formatted",
                "date": "2026-03-01",
                "project_refs": ["project:demo"],
            }
        )
        _write_yaml(
            self.pdir / "evidence-pool.yaml",
            {"profile": "dev", "evidence_entries": rows},
        )
        self._write_outputs(
            [
                {
                    "id": "update_me",
                    "title": "New title",
                    "status": "published",
                    "date": "2026-03-04",
                    "summary": "New summary.",
                    "project_refs": ["project:demo"],
                }
            ]
        )

        ok = self.host.handle_event(
            {
                "action": "bulk_create_from_output",
                "event_id": "out-bulk-3",
                "payload": {
                    "items": [{"output_id": "update_me", "source_kind": "output"}]
                },
            }
        )

        self.assertTrue(ok)
        matches = [r for r in self._pool() if r.get("origin_ref") == "output:update_me"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["id"], "existing_output")
        self.assertEqual(matches[0]["title"], "New title")

    def test_bulk_create_from_output_blocks_entire_batch_when_one_invalid(self) -> None:
        before = self._pool()
        self._write_outputs(
            [
                {
                    "id": "good",
                    "title": "Good",
                    "status": "published",
                    "date": "2026-03-05",
                    "summary": "Good summary.",
                    "project_refs": ["project:demo"],
                },
                {
                    "id": "draft",
                    "title": "Draft",
                    "status": "draft",
                    "date": "2026-03-06",
                    "summary": "Draft summary.",
                    "project_refs": ["project:demo"],
                },
            ]
        )
        ok = self.host.handle_event(
            {
                "action": "bulk_create_from_output",
                "event_id": "out-bulk-4",
                "payload": {
                    "items": [
                        {"output_id": "good", "source_kind": "output"},
                        {"output_id": "draft", "source_kind": "output"},
                    ]
                },
            }
        )

        self.assertFalse(ok)
        self.assertEqual(self._pool(), before)
        self.fake_st.error.assert_called()

    def test_ignore_and_restore_output_candidates_only_touch_preferences(self) -> None:
        self._write_outputs(
            [
                {
                    "id": "skip_me",
                    "title": "Skip me",
                    "status": "published",
                    "date": "2026-03-07",
                    "summary": "Skip summary.",
                    "project_refs": ["project:demo"],
                }
            ]
        )
        original_outputs = (self.pdir / "outputs.yaml").read_text(encoding="utf-8")

        ok = self.host.handle_event(
            {
                "action": "ignore_output_candidates",
                "event_id": "ignore-1",
                "payload": {
                    "items": [{"output_id": "skip_me", "source_kind": "output"}],
                    "reason": "not_evidence",
                },
            }
        )

        self.assertTrue(ok)
        self.assertEqual(
            (self.pdir / "outputs.yaml").read_text(encoding="utf-8"),
            original_outputs,
        )
        ignored = self._web_preferences()["evidence_review"]["ignored_output_candidates"]
        self.assertEqual(ignored[0]["source_key"], "output:skip_me")

        ok = self.host.handle_event(
            {
                "action": "restore_output_candidates",
                "event_id": "restore-1",
                "payload": {
                    "items": [{"output_id": "skip_me", "source_kind": "output"}]
                },
            }
        )

        self.assertTrue(ok)
        ignored = self._web_preferences()["evidence_review"]["ignored_output_candidates"]
        self.assertEqual(ignored, [])

    def test_done_tasks_to_evidence_includes_uncrystallized(self) -> None:
        # A Done task that was never crystallized should still produce evidence.
        (self.pdir / "kanban.md").write_text(
            "## Done\n\n"
            "- [x] Shipped detector\n"
            "  - id: kb_det\n"
            "  - completed_on: 2026-02-01\n"
            "  - project_id: project:demo\n"
            "  - outcome: faster pipeline\n",
            encoding="utf-8",
        )
        ok = self.host.handle_event(
            {
                "action": "done_tasks_to_evidence",
                "event_id": "done-1",
                "payload": {"task_ids": ["kb_det"], "mark_crystallized": True},
            }
        )
        self.assertTrue(ok)
        # A new kanban-origin evidence row referencing the task exists.
        rows = self._pool()
        match = [
            r
            for r in rows
            if "kanban:kb_det" in (r.get("kanban_refs") or [])
        ]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].get("origin"), "kanban_task")
        self.assertEqual(match[0].get("date"), "2026-02-01")
        self.assertTrue(match[0].get("formatted_content"))
        # The task is now crystallized in kanban.md.
        self.assertIn(
            "crystallized: true",
            (self.pdir / "kanban.md").read_text(encoding="utf-8"),
        )

    def test_prepare_done_ai_preview_blocks_missing_completed_on(self) -> None:
        (self.pdir / "kanban.md").write_text(
            "## Done\n\n"
            "- [x] Missing date\n"
            "  - id: kb_missing_date\n"
            "  - project_id: project:demo\n",
            encoding="utf-8",
        )
        with patch("nblane.evidence_editor_host.ingest_kanban_done_json") as ai:
            ok = self.host.handle_event(
                {
                    "action": "prepare_done_task_evidence",
                    "event_id": "done-ai-block-1",
                    "payload": {"task_ids": ["kb_missing_date"]},
                }
            )
        self.assertTrue(ok)
        ai.assert_not_called()
        preview = self.fake_st.session_state[self.host._done_preview_state_key()]
        self.assertFalse(preview["can_accept"])
        self.assertIn("completed_on", preview["task_blockers"][0]["blockers"][0])

    def test_prepare_and_apply_done_ai_preview_writes_evidence_and_skills(self) -> None:
        (self.pdir / "kanban.md").write_text(
            "## Done\n\n"
            "- [x] AI detector\n"
            "  - id: kb_ai\n"
            "  - completed_on: 2026-02-02\n"
            "  - project_id: project:demo\n"
            "  - outcome: detector improved\n",
            encoding="utf-8",
        )
        ai_patch = {
            "evidence_entries": [
                {
                    "id": "ai_ev",
                    "title": "AI normalized detector",
                    "summary": "Detector work was completed.",
                    "formatted_content": "## Detector\n\nCompleted detector work.",
                    "strength": "medium",
                    "confidence": "high",
                    # Host must overwrite identity fields from the task.
                    "date": "1900-01-01",
                    "origin": "manual_daily",
                    "origin_ref": "wrong",
                    "project_refs": ["project:wrong"],
                    "original_content": "wrong raw",
                    "kanban_refs": ["kanban:kb_ai"],
                }
            ],
            "node_updates": [
                {
                    "id": "ros2_basics",
                    "evidence_refs": ["ai_ev"],
                    "status": "learning",
                }
            ],
        }
        with patch(
            "nblane.evidence_editor_host.ingest_kanban_done_json",
            return_value=(ai_patch, None),
        ), patch(
            "nblane.evidence_editor_host.kanban_ai_backend",
            return_value="llm",
        ), patch(
            "nblane.evidence_editor_host.current_goal_agent_context",
            return_value="",
        ):
            ok = self.host.handle_event(
                {
                    "action": "prepare_done_task_evidence",
                    "event_id": "done-ai-1",
                    "payload": {"task_ids": ["kb_ai"]},
                }
            )
        self.assertTrue(ok)
        preview = self.fake_st.session_state[self.host._done_preview_state_key()]
        self.assertTrue(preview["can_accept"])
        row = preview["rows"][0]["row"]
        self.assertEqual(row["date"], "2026-02-02")
        self.assertEqual(row["origin"], "kanban_task")
        self.assertEqual(row["origin_ref"], "kanban:kb_ai")
        self.assertEqual(row["project_refs"], ["project:demo"])
        self.assertIn("AI detector", row["original_content"])

        ok = self.host.handle_event(
            {
                "action": "apply_done_task_evidence",
                "event_id": "done-ai-apply-1",
                "payload": {
                    "preview_id": preview["preview_id"],
                    "mark_crystallized": True,
                },
            }
        )
        self.assertTrue(ok)
        rows = self._pool()
        match = [r for r in rows if r.get("origin_ref") == "kanban:kb_ai"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]["title"], "AI normalized detector")
        self.assertEqual(match[0]["strength"], "medium")
        by_id = {n["id"]: n for n in self._tree_nodes()}
        self.assertIn(match[0]["id"], by_id["ros2_basics"].get("evidence_refs") or [])

    def test_done_ai_duplicate_rows_block_accept(self) -> None:
        (self.pdir / "kanban.md").write_text(
            "## Done\n\n"
            "- [x] Duplicate AI rows\n"
            "  - id: kb_dup\n"
            "  - completed_on: 2026-02-03\n"
            "  - project_id: project:demo\n",
            encoding="utf-8",
        )
        row = {
            "title": "Duplicate",
            "summary": "summary",
            "formatted_content": "formatted",
            "strength": "medium",
            "confidence": "high",
            "kanban_refs": ["kanban:kb_dup"],
        }
        with patch(
            "nblane.evidence_editor_host.ingest_kanban_done_json",
            return_value=({"evidence_entries": [row, dict(row)], "node_updates": []}, None),
        ), patch(
            "nblane.evidence_editor_host.kanban_ai_backend",
            return_value="llm",
        ), patch(
            "nblane.evidence_editor_host.current_goal_agent_context",
            return_value="",
        ):
            ok = self.host.handle_event(
                {
                    "action": "prepare_done_task_evidence",
                    "event_id": "done-ai-dup-1",
                    "payload": {"task_ids": ["kb_dup"]},
                }
            )
        self.assertTrue(ok)
        preview = self.fake_st.session_state[self.host._done_preview_state_key()]
        self.assertFalse(preview["can_accept"])
        self.assertIn("multiple", preview["blocking_errors"][0])

    def test_archive_done_tasks_by_id_removes_from_kanban(self) -> None:
        (self.pdir / "kanban.md").write_text(
            "## Done\n\n"
            "- [x] Keep me\n"
            "  - id: kb_keep\n"
            "  - completed_on: 2026-02-01\n"
            "- [x] Archive me\n"
            "  - id: kb_arch\n"
            "  - completed_on: 2026-02-02\n",
            encoding="utf-8",
        )
        ok = self.host.handle_event(
            {
                "action": "archive_done_tasks",
                "event_id": "arch-1",
                "payload": {"task_ids": ["kb_arch"]},
            }
        )
        self.assertTrue(ok)
        kanban = (self.pdir / "kanban.md").read_text(encoding="utf-8")
        self.assertNotIn("kb_arch", kanban)
        self.assertIn("kb_keep", kanban)
        archive = (self.pdir / "kanban-archive.md").read_text(encoding="utf-8")
        self.assertIn("kb_arch", archive)

    def test_delete_done_task_blocked_when_cited_by_active_evidence(self) -> None:
        # e1 already cites kb_cited via kanban_refs -> deletion must be blocked.
        entries = self._pool()
        entries[0]["origin"] = "kanban_task"
        entries[0]["origin_ref"] = "kanban:kb_cited"
        entries[0]["kanban_refs"] = ["kanban:kb_cited"]
        save_evidence_pool(
            "dev", {"profile": "dev", "evidence_entries": entries}
        )
        (self.pdir / "kanban.md").write_text(
            "## Done\n\n"
            "- [x] Cited task\n"
            "  - id: kb_cited\n"
            "  - completed_on: 2026-02-01\n",
            encoding="utf-8",
        )
        ok = self.host.handle_event(
            {
                "action": "delete_done_tasks",
                "event_id": "del-blocked",
                "payload": {"task_ids": ["kb_cited"]},
            }
        )
        self.assertFalse(ok)
        # Task remains in kanban.md.
        self.assertIn(
            "kb_cited", (self.pdir / "kanban.md").read_text(encoding="utf-8")
        )

    def test_delete_done_task_succeeds_when_not_cited(self) -> None:
        (self.pdir / "kanban.md").write_text(
            "## Done\n\n"
            "- [x] Orphan task\n"
            "  - id: kb_orphan\n"
            "  - completed_on: 2026-02-01\n",
            encoding="utf-8",
        )
        ok = self.host.handle_event(
            {
                "action": "delete_done_tasks",
                "event_id": "del-ok",
                "payload": {"task_ids": ["kb_orphan"]},
            }
        )
        self.assertTrue(ok)
        self.assertNotIn(
            "kb_orphan", (self.pdir / "kanban.md").read_text(encoding="utf-8")
        )

    def test_done_housekeeping_missing_task_id_errors(self) -> None:
        (self.pdir / "kanban.md").write_text(
            "## Done\n\n- [x] Only task\n  - id: kb_only\n", encoding="utf-8"
        )
        ok = self.host.handle_event(
            {
                "action": "archive_done_tasks",
                "event_id": "arch-missing",
                "payload": {"task_ids": ["kb_ghost"]},
            }
        )
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
