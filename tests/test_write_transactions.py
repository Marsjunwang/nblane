"""Concurrent mutations preserve committed data across conflicts and rollback."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from nblane.core import (
    agent_journal,
    file_state,
    git_backup,
    ingest_apply,
    io,
    profile_io,
    project_board,
    project_board_sync,
    research_sources,
)
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_write import atomic_write_text, profile_file_transaction
from nblane.core.kanban_io import parse_kanban, save_kanban
from nblane.core.models import KanbanTask
from nblane.core.project_board import ProjectBoard, ProjectCase


@pytest.fixture
def pdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "profiles"
    profile = root / "review"
    profile.mkdir(parents=True)
    for module in (profile_io, io, project_board, research_sources):
        monkeypatch.setattr(module, "PROFILES_DIR", root)
    monkeypatch.setattr(git_backup, "record_change", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("NBLANE_AGENT_STATE_DIR", str(tmp_path / "agent-state"))
    profile_io.save_evidence_pool("review", {"profile": "review", "evidence_entries": []})
    profile_io.save_skill_tree("review", {
        "profile": "review", "schema": "robotics-engineer",
        "nodes": [{"id": "ros2_basics", "status": "locked"}],
    })
    return profile


def test_transaction_rollback_releases_waiting_writer_without_erasing_it(pdir: Path) -> None:
    target = pdir / "example.md"
    target.write_text("original", encoding="utf-8")
    waiting = threading.Event()
    finished = threading.Event()

    def other_writer() -> None:
        waiting.set()
        with locked_profile_write(pdir, target.name):
            atomic_write_text(target, "other writer")
        finished.set()

    with ThreadPoolExecutor(max_workers=1) as executor:
        with pytest.raises(ValueError, match="failed"):
            with profile_file_transaction(pdir, (target.name,)):
                # An existing domain writer can reenter the transaction lock.
                with locked_profile_write(pdir, target.name):
                    atomic_write_text(target, "unfinished transaction")
                pending = executor.submit(other_writer)
                assert waiting.wait(2)
                assert not finished.wait(0.05)
                raise ValueError("failed")
        pending.result(timeout=2)
    assert target.read_text(encoding="utf-8") == "other writer"


def _seed_project(pdir: Path) -> ProjectBoard:
    board = ProjectBoard(profile=pdir.name, project_cases=[ProjectCase(id="proj", title="Original")])
    project_board.save_project_board(pdir, board)
    save_kanban(pdir, {"Queue": [KanbanTask(id="task1", title="Task")]})
    return board


def test_project_sync_preflights_all_files_before_first_write(pdir: Path) -> None:
    board = _seed_project(pdir)
    snapshots = {
        "board": file_state.snapshot_file(pdir / "project-board.yaml"),
        "kanban": file_state.snapshot_file(pdir / "kanban.md"),
    }
    board.project_cases[0].title = "New title"
    board.project_cases[0].task_refs = ["task1"]
    save_kanban(pdir, {"Queue": [KanbanTask(id="task1", title="Human edit")]})
    with pytest.raises(file_state.FileConflictError):
        project_board_sync.sync_project_case_workspace(
            pdir.name, board, "proj", expected_snapshots=snapshots,
        )
    stored = project_board.load_project_board(pdir).project_cases[0]
    assert (stored.title, stored.task_refs) == ("Original", [])
    assert parse_kanban(pdir)["Queue"][0].title == "Human edit"


def test_project_sync_restores_earlier_files_on_later_io_failure(
    pdir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    board = _seed_project(pdir)
    before = (pdir / "project-board.yaml").read_bytes()
    board.project_cases[0].title = "New title"
    board.project_cases[0].task_refs = ["task1"]

    def fail(*_args, **_kwargs):
        raise OSError("disk error")

    monkeypatch.setattr(project_board_sync, "save_kanban", fail)
    with pytest.raises(OSError, match="disk error"):
        project_board_sync.sync_project_case_workspace(pdir.name, board, "proj")
    assert (pdir / "project-board.yaml").read_bytes() == before
    assert parse_kanban(pdir)["Queue"][0].project_id == ""


def test_concurrent_ingest_merges_keep_both_new_evidence_rows(
    pdir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_merging = threading.Event()
    release_first = threading.Event()
    second_started = threading.Event()
    original_merge = ingest_apply.merge_ingest_patch

    def merge(name, pool, tree, patch, **kwargs):
        if patch["evidence_entries"][0]["id"] == "first":
            first_merging.set()
            assert release_first.wait(2)
        return original_merge(name, pool, tree, patch, **kwargs)

    monkeypatch.setattr(ingest_apply, "merge_ingest_patch", merge)

    def run(row_id: str):
        if row_id == "second":
            second_started.set()
        return ingest_apply.run_ingest_patch(pdir.name, {
            "evidence_entries": [{"id": row_id, "type": "practice", "title": row_id}],
            "node_updates": [],
        })

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(run, "first")
        assert first_merging.wait(2)
        second = executor.submit(run, "second")
        assert second_started.wait(2)
        release_first.set()
        for future in (first, second):
            merged, applied = future.result(timeout=5)
            assert merged.ok, merged.errors
            assert applied.ok, applied.errors
    rows = profile_io.load_evidence_pool_raw(pdir)["evidence_entries"]
    assert {row["id"] for row in rows} == {"first", "second"}


def test_ingest_sync_failure_restores_pool_tree_and_generated_file(
    pdir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from nblane.core import sync

    (pdir / "SKILL.md").write_text("original identity", encoding="utf-8")
    before = {name: (pdir / name).read_bytes() for name in ingest_apply._INGEST_FILES}
    monkeypatch.setattr(ingest_apply, "validate_one", lambda *_args, **_kwargs: ([], []))

    def fail_after_sync(directory: Path) -> None:
        atomic_write_text(directory / "SKILL.md", "partial sync")
        raise OSError("sync failed")

    monkeypatch.setattr(sync, "write_generated_blocks", fail_after_sync)
    _merged, applied = ingest_apply.run_ingest_patch(pdir.name, {
        "evidence_entries": [{"id": "new", "type": "practice", "title": "New"}],
    })
    assert not applied.ok
    assert {name: (pdir / name).read_bytes() for name in before} == before


def test_evidence_undo_rechecks_entity_at_the_domain_write_boundary(
    pdir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_io.save_evidence_pool(pdir.name, {"evidence_entries": [
        {"id": "target", "type": "practice", "title": "Original"},
    ]})
    before = agent_journal.snapshot(pdir, ("evidence",))
    profile_io.update_evidence_pool(pdir.name, lambda raw: raw["evidence_entries"][0].update(title="Agent"))
    after = agent_journal.snapshot(pdir, ("evidence",))
    entry = agent_journal.record(
        pdir, actor="agent", action="evidence.edit", tier="T2", summary="Edit evidence",
        changes=agent_journal.diff(before, after),
    )
    original_restore = agent_journal._restore_list

    def race_before_restore(*args, **kwargs):
        profile_io.update_evidence_pool(pdir.name, lambda raw: raw["evidence_entries"][0].update(title="Human"))
        return original_restore(*args, **kwargs)

    monkeypatch.setattr(agent_journal, "_restore_list", race_before_restore)
    with pytest.raises(agent_journal.UndoError) as caught:
        agent_journal.undo(pdir, entry["id"], actor="human")
    assert caught.value.code == "journal_undo_conflict"
    assert profile_io.load_evidence_pool_raw(pdir)["evidence_entries"][0]["title"] == "Human"
    assert not agent_journal.load_entries(pdir)[0]["undone_at"]


def test_undo_project_link_restores_card_and_case_together(pdir: Path) -> None:
    board = _seed_project(pdir)
    kinds = ("kanban_card", "project_case")
    before = agent_journal.snapshot(pdir, kinds)
    board.project_cases[0].task_refs = ["task1"]
    project_board_sync.sync_project_case_workspace(pdir.name, board, "proj")
    after = agent_journal.snapshot(pdir, kinds)
    entry = agent_journal.record(
        pdir, actor="agent", action="project.case.save", tier="T2", summary="Link task",
        changes=agent_journal.diff(before, after),
    )

    agent_journal.undo(pdir, entry["id"], actor="human")

    assert agent_journal.snapshot(pdir, kinds) == before
    assert agent_journal.load_entries(pdir)[0]["undone_at"]


def test_undo_journal_failure_restores_business_files(
    pdir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    board = _seed_project(pdir)
    before = agent_journal.snapshot(pdir, ("project_case",))
    board.project_cases[0].title = "Agent edit"
    project_board.save_project_board(pdir, board)
    after = agent_journal.snapshot(pdir, ("project_case",))
    entry = agent_journal.record(
        pdir, actor="agent", action="project.case.save", tier="T2", summary="Edit project",
        changes=agent_journal.diff(before, after),
    )

    def fail(*_args, **_kwargs):
        raise OSError("journal disk error")

    monkeypatch.setattr(agent_journal, "_write", fail)
    with pytest.raises(OSError, match="journal disk error"):
        agent_journal.undo(pdir, entry["id"], actor="human")

    assert agent_journal.snapshot(pdir, ("project_case",)) == after
    assert not agent_journal.load_entries(pdir)[0]["undone_at"]
