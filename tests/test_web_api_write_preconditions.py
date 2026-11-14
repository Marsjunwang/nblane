"""If-Match versions remain the write baseline when another request commits."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import Response

from nblane.core import career_workspace, git_backup, io, profile_io, project_board
from nblane.core.kanban_io import save_kanban
from nblane.core.models import KanbanTask
from nblane.web_api import routes_v1 as routes
from nblane.web_api.auth import CurrentUser
from nblane.web_api.schemas import CareerDraftUpdateRequest, SkillNodePatchRequest


@pytest.fixture
def pdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "profiles"
    profile = root / "review"
    profile.mkdir(parents=True)
    for module in (profile_io, io, project_board):
        monkeypatch.setattr(module, "PROFILES_DIR", root)
    monkeypatch.setattr(git_backup, "record_change", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(routes, "_resolve_profile", lambda _name: profile)
    return profile


def test_evidence_update_between_etag_check_and_write_returns_412(
    pdir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_io.save_evidence_pool(pdir.name, {"evidence_entries": [
        {"id": "ev1", "type": "practice", "title": "Evidence", "strength": "weak"},
    ]})
    etag = routes._evidence_pool_etag(pdir)
    original_check = routes._if_match_satisfied

    def check_then_race(if_match, current):
        accepted = original_check(if_match, current)
        profile_io.update_evidence_pool(pdir.name, lambda raw: raw["evidence_entries"][0].update(strength="strong"))
        return accepted

    monkeypatch.setattr(routes, "_if_match_satisfied", check_then_race)

    def apply(rows):
        rows[0]["strength"] = "medium"
        return 1, []

    result = routes._mutate_evidence_pool(pdir.name, etag, apply)
    assert result.status_code == 412
    assert profile_io.load_evidence_pool_raw(pdir)["evidence_entries"][0]["strength"] == "strong"


def test_skill_update_after_etag_check_preserves_newer_status(
    pdir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_io.save_skill_tree(pdir.name, {"nodes": [{"id": "node", "status": "locked"}]})
    etag = routes._skill_tree_etag(pdir)
    original_check = routes._if_match_satisfied

    def check_then_race(if_match, current):
        accepted = original_check(if_match, current)
        profile_io.update_skill_tree(pdir.name, lambda raw: raw["nodes"][0].update(status="solid"))
        return accepted

    monkeypatch.setattr(routes, "_if_match_satisfied", check_then_race)
    result = routes.patch_profile_skill_node(
        pdir.name, "node", SkillNodePatchRequest(status="learning"), Response(), etag,
        CurrentUser(id="human", display_name="Human", role="admin"),
    )
    assert result.status_code == 412
    assert profile_io.load_skill_tree_raw(pdir)["nodes"][0]["status"] == "solid"


def test_board_request_uses_the_same_snapshot_for_etag_and_sync(
    pdir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    board = project_board.ProjectBoard(profile=pdir.name, project_cases=[
        project_board.ProjectCase(id="proj", title="Original"),
    ])
    project_board.save_project_board(pdir, board)
    etag = routes._project_board_etag(pdir)
    original_check = routes._if_match_satisfied

    def check_then_race(if_match, current):
        accepted = original_check(if_match, current)
        project_board.update_project_board(pdir, lambda latest: setattr(latest.project_cases[0], "title", "Human"))
        return accepted

    monkeypatch.setattr(routes, "_if_match_satisfied", check_then_race)
    _directory, loaded, snapshots = routes._check_board_mutation(pdir.name, etag)
    loaded.project_cases[0].title = "Stale request"
    result = routes._synced_case_response(pdir, loaded, "proj", Response(), snapshots)
    assert result.status_code == 412
    assert project_board.load_project_board(pdir).project_cases[0].title == "Human"


def test_kanban_merge_base_is_captured_with_its_version(pdir: Path) -> None:
    save_kanban(pdir, {"Queue": [KanbanTask(id="task", title="Original")]})
    version, sections = routes._kanban_edit_snapshot(pdir)
    assert routes._snapshot_etag(version) == routes._kanban_etag(pdir)
    save_kanban(pdir, {"Queue": [KanbanTask(id="task", title="Human")]})
    assert sections["Queue"][0].title == "Original"
    assert routes._snapshot_etag(version) != routes._kanban_etag(pdir)


def test_career_metadata_update_changes_etag_and_rejects_stale_save(pdir: Path) -> None:
    initial = career_workspace.save_draft(pdir.name, "role", "Original", meta={"notes": "Old"})
    fresh = career_workspace.update_draft_meta(pdir.name, "role", {"notes": "Human notes"})
    assert fresh["etag"] != initial["etag"]
    with pytest.raises(career_workspace.ResumeConflict):
        career_workspace.update_draft(
            pdir.name, "role", markdown="Stale", meta={"notes": "Stale notes"},
            expected_etag=initial["etag"],
        )
    assert career_workspace.get_draft(pdir.name, "role") == fresh


def test_career_request_race_does_not_save_metadata_before_conflict(
    pdir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial = career_workspace.save_draft(pdir.name, "role", "Original")
    original_check = routes._if_match_satisfied

    def check_then_race(if_match, current):
        accepted = original_check(if_match, current)
        career_workspace.update_draft(pdir.name, "role", markdown="Human")
        return accepted

    monkeypatch.setattr(routes, "_if_match_satisfied", check_then_race)
    result = routes.update_profile_career_draft(
        pdir.name, "role", CareerDraftUpdateRequest(markdown="Stale", notes="Stale notes"),
        Response(), initial["etag"], False,
    )
    assert result.status_code == 412
    stored = career_workspace.get_draft(pdir.name, "role")
    assert stored["markdown"] == "Human\n"
    assert stored["notes"] == ""


def test_career_metadata_write_failure_rolls_back_markdown(
    pdir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial = career_workspace.save_draft(pdir.name, "role", "Original", meta={"notes": "Old"})
    original_write = career_workspace.atomic_write_text

    def fail_metadata(path, content):
        if path.name.endswith(".meta.yaml"):
            raise OSError("metadata disk error")
        return original_write(path, content)

    monkeypatch.setattr(career_workspace, "atomic_write_text", fail_metadata)
    with pytest.raises(OSError, match="metadata disk error"):
        career_workspace.update_draft(
            pdir.name, "role", markdown="Updated", meta={"notes": "New"},
            expected_etag=initial["etag"],
        )
    stored = career_workspace.get_draft(pdir.name, "role")
    assert stored["markdown"] == initial["markdown"]
    assert stored["notes"] == initial["notes"]
    assert stored["etag"] == initial["etag"]


def test_card_project_link_conflict_does_not_save_half_the_relationship(pdir: Path) -> None:
    project_board.save_project_board(pdir, project_board.ProjectBoard(
        profile=pdir.name, project_cases=[project_board.ProjectCase(id="proj", title="Original")],
    ))
    save_kanban(pdir, {"Queue": [KanbanTask(id="task", title="Original")]})
    version, sections = routes._kanban_edit_snapshot(pdir)
    base = routes.copy_kanban_sections(sections)
    board_version = routes.file_state.snapshot_file(pdir / "project-board.yaml")
    project_board.update_project_board(pdir, lambda board: setattr(board.project_cases[0], "title", "Human"))
    sections["Queue"][0].project_id = "proj"

    with pytest.raises(routes.file_state.FileConflictError):
        routes._save_linked_kanban_mutation(pdir, sections, base, version, board_version)

    assert routes.parse_kanban(pdir)["Queue"][0].project_id == ""
    assert project_board.load_project_board(pdir).project_cases[0].title == "Human"


def test_card_project_sync_failure_restores_saved_card(
    pdir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    save_kanban(pdir, {"Queue": [KanbanTask(id="task", title="Original")]})
    version, sections = routes._kanban_edit_snapshot(pdir)
    base = routes.copy_kanban_sections(sections)
    board_version = routes.file_state.snapshot_file(pdir / "project-board.yaml")
    sections["Queue"][0].project_id = "proj"

    def fail(*_args, **_kwargs):
        raise OSError("board disk error")

    monkeypatch.setattr(routes, "sync_project_board_from_kanban", fail)
    with pytest.raises(OSError, match="board disk error"):
        routes._save_linked_kanban_mutation(pdir, sections, base, version, board_version)

    assert routes.parse_kanban(pdir)["Queue"][0].project_id == ""
