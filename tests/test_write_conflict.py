"""Tests for the in-lock snapshot re-check (TOCTOU closure) on core savers.

Every conflict-aware saver takes an optional ``expected_snapshot``
(``file_state.FileSnapshot``) captured by the caller at request start and
re-checks it *inside* the write lock: a mismatch raises
``file_state.FileConflictError`` so a concurrent write landing between the
caller's read/If-Match check and the lock acquisition is never silently
overwritten. These tests simulate exactly that interleaving: snapshot →
external write (through the normal saver, which takes and releases the
lock) → save with the now-stale snapshot.
"""

from __future__ import annotations

import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from nblane.core import agent_activity
from nblane.core.activity_log import ACTIVITY_LOG_FILENAME, load_activity_log
from nblane.core.activity_log import save as save_activity_log
from nblane.core.file_state import FileConflictError, snapshot_file
from nblane.core.growth_log import append_growth_log_row
from nblane.core.inbox import add_inbox_item, load_inbox, update_inbox
from nblane.core.kanban_io import KANBAN_QUEUE, parse_kanban, save_kanban
from nblane.core.kanban_io import update_kanban
from nblane.core.kanban_merge import copy_kanban_sections
from nblane.core.kanban_merge import save_kanban_with_merge
from nblane.core.learning_log import (
    LEARNING_LOG_FILENAME,
    add_learning_resource,
    load_learning_log,
    save_learning_log,
)
from nblane.core.models import KanbanTask
from nblane.core.profile_io import (
    save_evidence_pool,
    save_skill_tree,
    update_evidence_pool,
    update_skill_tree,
)
from nblane.core.project_board import (
    add_project_case,
    load_project_board,
    save_project_board,
    update_project_board,
)
from nblane.core.public_site import (
    create_blog_draft,
    parse_blog_post,
    save_blog_post,
)
from nblane.core.review_actions import apply_review_kanban_candidate

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "profiles" / "template"

KANBAN_FIXTURE = """# demo · Kanban

## Doing

- [ ] Write VLA survey
  - id: task-vla

---

## Done

- (empty)

---

## Queue

- (empty)

---

## Someday / Maybe

- (empty)

---
"""


def _template_profile(tmp: Path, name: str = "demo") -> Path:
    profile = tmp / name
    shutil.copytree(TEMPLATE_DIR, profile)
    for file_path in profile.rglob("*"):
        if file_path.is_file():
            text = file_path.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            text = text.replace("{YYYY-MM-DD}", "2026-09-19")
            file_path.write_text(text, encoding="utf-8")
    return profile


def _suppress_backup():
    # All core modules share the git_backup module object; patching the
    # attribute once silences every caller in this process.
    return patch("nblane.core.git_backup.record_change")


class TestEvidencePoolConflict(unittest.TestCase):
    """save_evidence_pool re-checks the snapshot inside the write lock."""

    def test_stale_snapshot_raises_and_preserves_external_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            pool_path = profile / "evidence-pool.yaml"
            with _suppress_backup():
                stale = snapshot_file(pool_path)
                # External writer lands after the caller's snapshot.
                raw = yaml.safe_load(pool_path.read_text(encoding="utf-8"))
                raw.setdefault("evidence_entries", []).append(
                    {"id": "ev-external", "title": "外部并发证据"}
                )
                with patch(
                    "nblane.core.profile_io.PROFILES_DIR", profile.parent
                ):
                    save_evidence_pool(profile.name, raw)
                    with self.assertRaises(FileConflictError):
                        save_evidence_pool(
                            profile.name, raw, expected_snapshot=stale
                        )
                stored = yaml.safe_load(pool_path.read_text(encoding="utf-8"))
        titles = [row.get("title") for row in stored["evidence_entries"]]
        self.assertIn("外部并发证据", titles)

    def test_matching_snapshot_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            pool_path = profile / "evidence-pool.yaml"
            with _suppress_backup(), patch(
                "nblane.core.profile_io.PROFILES_DIR", profile.parent
            ):
                snapshot = snapshot_file(pool_path)
                raw = yaml.safe_load(pool_path.read_text(encoding="utf-8"))
                raw["evidence_entries"] = [
                    {"id": "ev-1", "title": "新证据"}
                ]
                save_evidence_pool(
                    profile.name, raw, expected_snapshot=snapshot
                )
                stored = yaml.safe_load(pool_path.read_text(encoding="utf-8"))
        self.assertEqual(
            [row["title"] for row in stored["evidence_entries"]], ["新证据"]
        )

    def test_update_evidence_pool_stale_snapshot_raises_before_fn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            pool_path = profile / "evidence-pool.yaml"
            called: list[bool] = []
            with _suppress_backup(), patch(
                "nblane.core.profile_io.PROFILES_DIR", profile.parent
            ):
                stale = snapshot_file(pool_path)
                raw = yaml.safe_load(pool_path.read_text(encoding="utf-8"))
                raw["evidence_entries"] = [{"id": "ev-x", "title": "外部"}]
                save_evidence_pool(profile.name, raw)

                def _fn(doc: dict) -> None:
                    called.append(True)
                    doc["evidence_entries"] = []

                with self.assertRaises(FileConflictError):
                    update_evidence_pool(
                        profile.name, _fn, expected_snapshot=stale
                    )
                stored = yaml.safe_load(pool_path.read_text(encoding="utf-8"))
        self.assertEqual(called, [])
        self.assertEqual(stored["evidence_entries"][0]["title"], "外部")


class TestUpdateKanban(unittest.TestCase):
    """update_kanban holds the lock across parse → mutate → write."""

    def _profile(self, tmp: str) -> Path:
        profile = _template_profile(Path(tmp))
        (profile / "kanban.md").write_text(KANBAN_FIXTURE, encoding="utf-8")
        return profile

    def test_mutation_persists_under_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(tmp)
            with _suppress_backup():

                def _add(sections):
                    sections.setdefault(KANBAN_QUEUE, []).append(
                        KanbanTask(title="新任务")
                    )

                update_kanban(profile, _add)
                titles = [t.title for t in parse_kanban(profile)[KANBAN_QUEUE]]
                lock_exists = (profile / "kanban.md.lock").exists()
        self.assertEqual(titles, ["新任务"])
        self.assertTrue(lock_exists)

    def test_noop_mutation_skips_write_and_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(tmp)
            before = (profile / "kanban.md").read_bytes()
            with patch(
                "nblane.core.git_backup.record_change"
            ) as record:
                update_kanban(profile, lambda sections: None)
            after = (profile / "kanban.md").read_bytes()
        self.assertEqual(before, after)
        record.assert_not_called()

    def test_stale_snapshot_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(tmp)
            with _suppress_backup():
                stale = snapshot_file(profile / "kanban.md")
                # External writer lands after the caller's snapshot.
                sections = parse_kanban(profile)
                sections[KANBAN_QUEUE].append(KanbanTask(title="外部卡片"))
                save_kanban(profile, sections)
                with self.assertRaises(FileConflictError):
                    update_kanban(
                        profile,
                        lambda s: s[KANBAN_QUEUE].append(
                            KanbanTask(title="我的卡片")
                        ),
                        expected_snapshot=stale,
                    )
                titles = [t.title for t in parse_kanban(profile)[KANBAN_QUEUE]]
        self.assertEqual(titles, ["外部卡片"])

    def test_save_kanban_stale_snapshot_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(tmp)
            with _suppress_backup():
                stale = snapshot_file(profile / "kanban.md")
                sections = parse_kanban(profile)
                sections[KANBAN_QUEUE].append(KanbanTask(title="外部卡片"))
                save_kanban(profile, sections)
                with self.assertRaises(FileConflictError):
                    save_kanban(
                        profile,
                        parse_kanban(profile),
                        expected_snapshot=stale,
                    )

    def test_merge_rechecks_inside_the_lock(self) -> None:
        """A write between snapshot and merge save is merged, not lost."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(tmp)
            with _suppress_backup():
                snapshot = snapshot_file(profile / "kanban.md")
                ours = parse_kanban(profile)
                base = copy_kanban_sections(ours)
                ours[KANBAN_QUEUE].append(KanbanTask(title="我的卡片"))
                # External writer lands after the snapshot, before the save.
                external = parse_kanban(profile)
                external[KANBAN_QUEUE].append(KanbanTask(title="外部卡片"))
                save_kanban(profile, external)
                result = save_kanban_with_merge(
                    profile, ours, base, expected_snapshot=snapshot
                )
                titles = [t.title for t in parse_kanban(profile)[KANBAN_QUEUE]]
        self.assertTrue(result.merged_external)
        self.assertEqual(sorted(titles), ["外部卡片", "我的卡片"])


class TestInboxActivityConflict(unittest.TestCase):
    """update_inbox / update_agent_activity re-check inside the lock."""

    def test_update_inbox_stale_snapshot_raises_before_fn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            with _suppress_backup():
                update_inbox(
                    profile, lambda doc: add_inbox_item(doc, "第一条")
                )
                stale = snapshot_file(profile / "inbox.yaml")
                # External writer lands after the caller's snapshot.
                update_inbox(
                    profile, lambda doc: add_inbox_item(doc, "外部并发")
                )
                with self.assertRaises(FileConflictError):
                    update_inbox(
                        profile,
                        lambda doc: add_inbox_item(doc, "我的写入"),
                        expected_snapshot=stale,
                    )
                stored = load_inbox(profile)
        titles = [item.title for item in stored.items]
        self.assertIn("外部并发", titles)
        self.assertNotIn("我的写入", titles)

    def test_update_inbox_matching_snapshot_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            with _suppress_backup():
                update_inbox(
                    profile, lambda doc: add_inbox_item(doc, "第一条")
                )
                snapshot = snapshot_file(profile / "inbox.yaml")
                item = update_inbox(
                    profile,
                    lambda doc: add_inbox_item(doc, "第二条"),
                    expected_snapshot=snapshot,
                )
                stored = load_inbox(profile)
        self.assertEqual(item.title, "第二条")
        self.assertEqual(len(stored.items), 2)

    def test_append_activity_item_stale_snapshot_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            with _suppress_backup(), patch(
                "nblane.core.profile_io.PROFILES_DIR", profile.parent
            ):
                stale = snapshot_file(
                    profile / agent_activity.AGENT_ACTIVITY_FILENAME
                )
                # External writer lands after the caller's snapshot.
                agent_activity.append_activity_item(
                    profile.name,
                    {"id": "act:external", "title": "外部并发"},
                )
                with self.assertRaises(FileConflictError):
                    agent_activity.append_activity_item(
                        profile.name,
                        {"id": "act:mine", "title": "我的写入"},
                        expected_snapshot=stale,
                    )
                stored = agent_activity.load_agent_activity(profile)
        ids = [item["id"] for item in stored["items"]]
        self.assertIn("act:external", ids)
        self.assertNotIn("act:mine", ids)


class TestLearningActivityLogConflict(unittest.TestCase):
    """learning/activity log savers lock and re-check the snapshot."""

    def test_learning_log_locks_and_stale_snapshot_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            log_path = profile / LEARNING_LOG_FILENAME
            with _suppress_backup():
                stale = snapshot_file(log_path)
                # External writer lands after the caller's snapshot.
                add_learning_resource(profile, title="外部资源")
                log = load_learning_log(profile)
                with self.assertRaises(FileConflictError):
                    save_learning_log(profile, log, expected_snapshot=stale)
                titles = [r.title for r in load_learning_log(profile).resources]
                lock_exists = (profile / f"{LEARNING_LOG_FILENAME}.lock").exists()
        self.assertTrue(lock_exists)
        self.assertEqual(titles, ["外部资源"])

    def test_add_learning_resource_stale_snapshot_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            with _suppress_backup():
                stale = snapshot_file(profile / LEARNING_LOG_FILENAME)
                add_learning_resource(profile, title="外部资源")
                with self.assertRaises(FileConflictError):
                    add_learning_resource(
                        profile, title="我的资源", expected_snapshot=stale
                    )

    def test_activity_log_locks_and_stale_snapshot_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            log_path = profile / ACTIVITY_LOG_FILENAME
            with _suppress_backup():
                stale = snapshot_file(log_path)
                log = load_activity_log(profile)
                # External writer lands after the caller's snapshot.
                save_activity_log(profile, log)
                with self.assertRaises(FileConflictError):
                    save_activity_log(profile, log, expected_snapshot=stale)
                lock_exists = (profile / f"{ACTIVITY_LOG_FILENAME}.lock").exists()
        self.assertTrue(lock_exists)


class TestProjectBoardConflict(unittest.TestCase):
    """project-board saves lock and re-check the snapshot."""

    def test_save_project_board_stale_snapshot_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            board_path = profile / "project-board.yaml"
            with _suppress_backup():
                stale = snapshot_file(board_path)
                board = load_project_board(profile)
                # External writer lands after the caller's snapshot.
                add_project_case(board, "外部项目", case_id="external-case")
                save_project_board(profile, board)
                mine = load_project_board(profile)
                add_project_case(mine, "我的项目", case_id="my-case")
                with self.assertRaises(FileConflictError):
                    save_project_board(profile, mine, expected_snapshot=stale)
                stored = load_project_board(profile)
                lock_exists = (profile / "project-board.yaml.lock").exists()
        self.assertTrue(lock_exists)
        self.assertIn("external-case", stored.by_id())
        self.assertNotIn("my-case", stored.by_id())

    def test_update_project_board_mutation_and_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            board_path = profile / "project-board.yaml"
            before = board_path.read_bytes()
            with patch(
                "nblane.core.git_backup.record_change"
            ) as record:
                update_project_board(profile, lambda board: None)
                self.assertEqual(board_path.read_bytes(), before)
                record.assert_not_called()
                update_project_board(
                    profile,
                    lambda board: add_project_case(
                        board, "新项目", case_id="new-case"
                    ),
                )
                stored = load_project_board(profile)
        self.assertIn("new-case", stored.by_id())


class TestSkillTreeConflict(unittest.TestCase):
    """skill-tree saves re-check the snapshot inside the lock."""

    def test_save_skill_tree_stale_snapshot_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            tree_path = profile / "skill-tree.yaml"
            with _suppress_backup(), patch(
                "nblane.core.profile_io.PROFILES_DIR", profile.parent
            ):
                stale = snapshot_file(tree_path)
                raw = yaml.safe_load(tree_path.read_text(encoding="utf-8"))
                raw["nodes"] = [{"id": "n1", "status": "learning"}]
                # External writer lands after the caller's snapshot.
                save_skill_tree(profile.name, raw)
                with self.assertRaises(FileConflictError):
                    save_skill_tree(
                        profile.name, raw, expected_snapshot=stale
                    )

    def test_update_skill_tree_noop_skips_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            tree_path = profile / "skill-tree.yaml"
            before = tree_path.read_bytes()
            with patch(
                "nblane.core.git_backup.record_change"
            ) as record, patch(
                "nblane.core.profile_io.PROFILES_DIR", profile.parent
            ):
                update_skill_tree(profile.name, lambda raw: None)
                after = tree_path.read_bytes()
        self.assertEqual(after, before)
        record.assert_not_called()


class TestBlogSaveConflict(unittest.TestCase):
    """save_blog_post re-checks the Markdown fingerprint inside the lock."""

    def test_stale_snapshot_raises_and_preserves_external_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            with _suppress_backup(), patch(
                "nblane.core.profile_io.PROFILES_DIR", profile.parent
            ):
                path = create_blog_draft(
                    profile.name, title="初稿", body="v1 正文"
                )
                stale = snapshot_file(path)
                # External writer lands after the caller's snapshot.
                post = parse_blog_post(path)
                save_blog_post(profile.name, post.slug, post.meta, "外部并发正文")
                with self.assertRaises(FileConflictError):
                    save_blog_post(
                        profile.name,
                        post.slug,
                        post.meta,
                        "我的正文",
                        expected_snapshot=stale,
                    )
                body = parse_blog_post(path).body
        self.assertIn("外部并发正文", body)

    def test_matching_snapshot_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            with _suppress_backup(), patch(
                "nblane.core.profile_io.PROFILES_DIR", profile.parent
            ):
                path = create_blog_draft(
                    profile.name, title="初稿", body="v1 正文"
                )
                post = parse_blog_post(path)
                save_blog_post(
                    profile.name,
                    post.slug,
                    post.meta,
                    "v2 正文",
                    expected_snapshot=snapshot_file(path),
                )
                body = parse_blog_post(path).body
        self.assertIn("v2 正文", body)


class TestGrowthLogLock(unittest.TestCase):
    """growth_log appends are a locked read-modify-write of SKILL.md."""

    def test_concurrent_appends_keep_every_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = _template_profile(Path(tmp))
            with _suppress_backup():
                threads = [
                    threading.Thread(
                        target=append_growth_log_row,
                        args=(profile, f"event-{index}"),
                    )
                    for index in range(6)
                ]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                content = (profile / "SKILL.md").read_text(encoding="utf-8")
                lock_exists = (profile / "SKILL.md.lock").exists()
        for index in range(6):
            self.assertIn(f"event-{index}", content)
        self.assertTrue(lock_exists)


class TestReviewKanbanMoveLock(unittest.TestCase):
    """The kanban_move applier moves cards inside the kanban write lock."""

    def _profile(self, tmp: str) -> Path:
        profile = _template_profile(Path(tmp), "alice")
        (profile / "kanban.md").write_text(
            KANBAN_FIXTURE.replace("demo · Kanban", "alice · Kanban"),
            encoding="utf-8",
        )
        return profile

    def _patches(self, profile: Path):
        return (
            patch(
                "nblane.core.review_actions.profile_dir",
                lambda _name: profile,
            ),
            patch(
                "nblane.core.agent_activity.profile_dir",
                lambda _name: profile,
            ),
            patch(
                "nblane.core.kanban_io.profile_dir",
                lambda _name: profile,
            ),
            _suppress_backup(),
        )

    def test_move_runs_through_update_kanban(self) -> None:
        import nblane.core.review_actions as review_actions

        real_update = review_actions.update_kanban
        calls: list[bool] = []

        def _spy(profile_arg, fn, **kwargs):
            calls.append(True)
            return real_update(profile_arg, fn, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(tmp)
            patches = self._patches(profile)
            with patches[0], patches[1], patches[2], patches[3], patch(
                "nblane.core.review_actions.update_kanban", _spy
            ):
                result = apply_review_kanban_candidate(
                    "alice",
                    {
                        "action": "move",
                        "card_ref": "Write VLA survey",
                        "target_section": "Done",
                    },
                )
                sections = parse_kanban("alice")
        self.assertTrue(calls)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(
            [task.title for task in sections["Done"]], ["Write VLA survey"]
        )

    def test_stale_kanban_snapshot_raises_not_failed_item(self) -> None:
        """A kanban write between request start and apply must surface as
        FileConflictError (→ 412), never as a swallowed ``failed`` item."""
        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(tmp)
            patches = self._patches(profile)
            with patches[0], patches[1], patches[2], patches[3]:
                stale = snapshot_file(profile / "kanban.md")
                # External writer lands after the request-start snapshot.
                external = parse_kanban("alice")
                external[KANBAN_QUEUE].append(KanbanTask(title="外部卡片"))
                save_kanban("alice", external)
                with self.assertRaises(FileConflictError):
                    apply_review_kanban_candidate(
                        "alice",
                        {
                            "action": "move",
                            "card_ref": "Write VLA survey",
                            "target_section": "Done",
                        },
                        kanban_snapshot=stale,
                    )
                activity = agent_activity.load_agent_activity("alice")
                sections = parse_kanban("alice")
        # The item was appended but never marked failed/applied, and the
        # external kanban write is untouched.
        self.assertEqual(activity["items"][0]["status"], "pending")
        self.assertEqual(
            [task.title for task in sections["Queue"]], ["外部卡片"]
        )
        self.assertEqual(
            [task.title for task in sections["Doing"]], ["Write VLA survey"]
        )


if __name__ == "__main__":
    unittest.main()
