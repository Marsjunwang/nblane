from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from nblane.core import (
    agent_journal,
    agent_ops,
    git_backup,
    research_journal,
    research_jsonl,
    research_sources,
)


@pytest.fixture
def pdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    profile = tmp_path / "profiles" / "alice"
    profile.mkdir(parents=True)
    monkeypatch.setenv("NBLANE_RESEARCH_ASSET_ROOT", str(tmp_path / "research-assets"))
    monkeypatch.setenv("NBLANE_AGENT_STATE_DIR", str(tmp_path / "agent-state"))
    monkeypatch.setattr(git_backup, "record_change", lambda *_args, **_kwargs: None)
    return profile


def _save_sources(pdir: Path, rows: list[dict]) -> None:
    def replace(inbox: research_sources.ResearchSourceInbox) -> None:
        inbox.sources = [research_sources.ResearchSource.from_dict(row) for row in rows]

    research_sources.mutate_research_sources(pdir, replace)


def _sources_by_id(pdir: Path) -> dict[str, research_sources.ResearchSource]:
    return research_sources.load_research_sources(pdir).by_id()


def _set_title(pdir: Path, source_id: str, title: str) -> None:
    research_sources.mutate_research_sources(
        pdir,
        lambda inbox: research_sources.update_research_source(inbox, source_id, title=title),
    )


def _journal(pdir: Path, kinds: tuple[str, ...], apply) -> dict:
    agent_journal.prepare(pdir, kinds)
    before = agent_journal.snapshot(pdir, kinds)
    apply()
    after = agent_journal.snapshot(pdir, kinds)
    changes = agent_journal.diff(before, after)
    entry = agent_journal.record(
        pdir,
        actor="muse",
        action="reader.test",
        tier="T1",
        summary="Reader test write",
        changes=changes,
    )
    assert entry is not None
    return entry


def _undo(pdir: Path, entry: dict) -> None:
    agent_journal.undo(pdir, entry["id"], actor="wang")


def _asset_path(pdir: Path, ref: str) -> Path:
    from nblane.core.research_papers._paths import _asset_path

    return _asset_path(pdir, ref)


def _write_asset(pdir: Path, ref: str, payload: bytes) -> Path:
    path = _asset_path(pdir, ref)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _snapshot_paths(digest: str) -> list[Path]:
    from nblane.core import agent_policy

    root = agent_policy.state_dir() / "journal-assets"
    return list(root.rglob(digest)) if root.exists() else []


def _begin_assets(pdir: Path, kinds: tuple[str, ...]) -> agent_ops.AgentWrite:
    return agent_ops.begin(
        pdir,
        actor="muse",
        action="reader.pdf.save",
        kinds=kinds,
        fingerprint="reader-test",
        describe=lambda _before: "Save a PDF",
    )


def test_source_undo_rechecks_after_inside_lock_without_reverting_racing_edit(pdir: Path) -> None:
    _save_sources(
        pdir,
        [
            {"id": "target", "title": "Old"},
            {"id": "other", "title": "Other"},
        ],
    )
    entry = _journal(pdir, ("research_source",), lambda: _set_title(pdir, "target", "Agent"))
    real_mutate = research_sources.mutate_research_sources
    raced = False

    def race_before_restore(name_or_dir, fn, **kwargs):
        nonlocal raced
        if not raced:
            raced = True
            real_mutate(
                pdir,
                lambda inbox: research_sources.update_research_source(inbox, "target", title="Human"),
            )
        return real_mutate(name_or_dir, fn, **kwargs)

    with patch.object(research_sources, "mutate_research_sources", side_effect=race_before_restore):
        with pytest.raises(agent_journal.UndoError) as caught:
            _undo(pdir, entry)

    assert caught.value.code == "journal_undo_conflict"
    assert _sources_by_id(pdir)["target"].title == "Human"
    assert agent_journal.load_entries(pdir)[0]["undone_at"] == ""


def test_source_undo_uses_latest_rows_and_preserves_unrelated_changes(pdir: Path) -> None:
    _save_sources(
        pdir,
        [
            {"id": "target", "title": "Old"},
            {"id": "other", "title": "Other"},
        ],
    )
    entry = _journal(pdir, ("research_source",), lambda: _set_title(pdir, "target", "Agent"))
    real_mutate = research_sources.mutate_research_sources
    raced = False

    def add_unrelated_before_restore(name_or_dir, fn, **kwargs):
        nonlocal raced
        if not raced:
            raced = True

            def update(latest: research_sources.ResearchSourceInbox) -> None:
                research_sources.update_research_source(latest, "other", title="Other latest")
                research_sources.add_research_source(latest, source_id="new", title="New source")

            real_mutate(pdir, update)
        return real_mutate(name_or_dir, fn, **kwargs)

    with patch.object(research_sources, "mutate_research_sources", side_effect=add_unrelated_before_restore):
        _undo(pdir, entry)

    sources = _sources_by_id(pdir)
    assert sources["target"].title == "Old"
    assert sources["other"].title == "Other latest"
    assert sources["new"].title == "New source"


@pytest.mark.parametrize(
    ("relative", "key"),
    [
        ("research/annotations/paper.jsonl", "id"),
        ("research/chunks/paper.jsonl", "id"),
        ("research/translations/paper.jsonl", "id"),
        ("research/paper-pages/paper.jsonl", "page"),
        ("research/paper-segments/paper.jsonl", "segment_id"),
        ("research/paper-structure/paper.jsonl", "unit_id"),
    ],
)
def test_jsonl_row_undo_supports_reader_keys_and_preserves_unrelated_rows(
    pdir: Path,
    relative: str,
    key: str,
) -> None:
    first = 1 if key == "page" else f"{key}-1"
    second = 2 if key == "page" else f"{key}-2"
    third = 3 if key == "page" else f"{key}-3"
    path = pdir / relative
    research_jsonl.replace_jsonl(
        path,
        [{key: first, "text": "Old"}, {key: second, "text": "Other"}],
    )
    kind = agent_journal.jsonl_kind(relative)
    entry = _journal(
        pdir,
        (kind,),
        lambda: research_jsonl.mutate_jsonl(path, lambda rows: rows[0].update(text="Agent")),
    )

    assert len(entry["changes"]) == 1
    assert entry["changes"][0]["id"] == str(first)
    assert agent_journal.kind_files(pdir, kind) == (relative,)
    research_jsonl.mutate_jsonl(path, lambda rows: rows.append({key: third, "text": "New"}))
    _undo(pdir, entry)

    rows = research_jsonl.load_jsonl(path)
    by_id = {str(row[key]): row for row in rows}
    assert by_id[str(first)]["text"] == "Old"
    assert by_id[str(second)]["text"] == "Other"
    assert by_id[str(third)]["text"] == "New"


def test_jsonl_locked_conflict_does_not_rollback_the_racing_edit(pdir: Path) -> None:
    relative = "research/annotations/paper.jsonl"
    path = pdir / relative
    research_jsonl.replace_jsonl(path, [{"id": "a", "text": "Old"}, {"id": "b", "text": "Other"}])
    kind = agent_journal.jsonl_kind(relative)
    entry = _journal(
        pdir,
        (kind,),
        lambda: research_jsonl.mutate_jsonl(path, lambda rows: rows[0].update(text="Agent")),
    )
    real_mutate = research_jsonl.mutate_jsonl
    raced = False

    def race_before_restore(jsonl_path, fn, **kwargs):
        nonlocal raced
        if not raced:
            raced = True
            real_mutate(jsonl_path, lambda rows: rows[0].update(text="Human"))
        return real_mutate(jsonl_path, fn, **kwargs)

    with patch.object(research_jsonl, "mutate_jsonl", side_effect=race_before_restore):
        with pytest.raises(agent_journal.UndoError) as caught:
            _undo(pdir, entry)

    assert caught.value.code == "journal_undo_conflict"
    rows = research_jsonl.load_jsonl(path)
    assert rows[0]["text"] == "Human"
    assert rows[1]["text"] == "Other"


@pytest.mark.parametrize("initial", ["Old", None], ids=["restore-text", "restore-missing-file"])
def test_file_locked_conflict_preserves_racing_edit(pdir: Path, initial: str | None) -> None:
    relative = "research/draft.md"
    path = pdir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if initial is not None:
        path.write_text(initial, encoding="utf-8")
    kind = agent_journal.file_kind(relative)
    entry = _journal(
        pdir,
        (kind,),
        lambda: path.write_text("Agent", encoding="utf-8"),
    )
    if initial is None:
        assert entry["changes"][0]["before"] is None
    real_restore = agent_journal._restore_file
    raced = False

    def race_before_locked_recheck(*args):
        nonlocal raced
        if not raced:
            raced = True
            path.write_text("Human", encoding="utf-8")
        return real_restore(*args)

    with patch.object(agent_journal, "_restore_file", side_effect=race_before_locked_recheck):
        with pytest.raises(agent_journal.UndoError) as caught:
            _undo(pdir, entry)

    assert raced
    assert caught.value.code == "journal_undo_conflict"
    assert path.read_text(encoding="utf-8") == "Human"
    assert agent_journal.load_entries(pdir)[0]["undone_at"] == ""


def test_journal_paths_reject_traversal_and_non_utf8_is_not_text(pdir: Path) -> None:
    for relative in ("../escape.jsonl", "/tmp/escape.jsonl", "research/other/paper.jsonl"):
        with pytest.raises(ValueError):
            agent_journal.snapshot(pdir, [agent_journal.jsonl_kind(relative)])
    for ref in ("../escape.pdf", "/tmp/escape.pdf", "papers/not-a-pdf.txt"):
        with pytest.raises(ValueError):
            agent_journal.snapshot(pdir, [agent_journal.asset_kind(ref)])

    binary = pdir / "research" / "binary.dat"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(UnicodeDecodeError):
        agent_journal.snapshot(pdir, [agent_journal.file_kind("research/binary.dat")])
    jsonl = pdir / "research" / "annotations" / "paper.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    jsonl.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(UnicodeDecodeError):
        agent_journal.snapshot(pdir, [agent_journal.jsonl_kind("research/annotations/paper.jsonl")])


def test_pdf_delete_undo_restores_old_bytes_without_embedding_them_in_yaml(pdir: Path) -> None:
    ref = "papers/delete-me.pdf"
    old = b"%PDF-1.4\nold delete bytes\n%%EOF"
    path = _write_asset(pdir, ref, old)
    entry = _journal(pdir, (agent_journal.asset_kind(ref),), path.unlink)

    change = entry["changes"][0]
    item = change["before"]["item"]
    assert item["sha256"] == _digest(old)
    assert item["size"] == len(old)
    assert item["snapshot_ref"].endswith(_digest(old))
    assert old not in agent_journal.journal_path(pdir).read_bytes()
    assert len(_snapshot_paths(_digest(old))) == 1
    assert agent_journal.recent(pdir)[0]["status"] == "undoable"

    _undo(pdir, entry)
    assert path.read_bytes() == old
    assert agent_journal.recent(pdir)[0]["status"] == "undone"


def test_pdf_replace_undo_and_after_recent_do_not_create_new_snapshots(pdir: Path) -> None:
    ref = "papers/replace-me.pdf"
    old = b"%PDF-1.4\nold replace bytes"
    new = b"%PDF-1.4\nnew replace bytes"
    path = _write_asset(pdir, ref, old)
    entry = _journal(
        pdir,
        (agent_journal.asset_kind(ref),),
        lambda: path.write_bytes(new),
    )

    assert _snapshot_paths(_digest(new)) == []
    agent_journal.snapshot(pdir, [agent_journal.asset_kind(ref)])
    agent_journal.recent(pdir)
    assert _snapshot_paths(_digest(new)) == []

    _undo(pdir, entry)
    assert path.read_bytes() == old
    assert _snapshot_paths(_digest(new)) == []


def test_pdf_undo_refuses_a_newer_hash(pdir: Path) -> None:
    ref = "papers/hash-conflict.pdf"
    path = _write_asset(pdir, ref, b"old")
    entry = _journal(
        pdir,
        (agent_journal.asset_kind(ref),),
        lambda: path.write_bytes(b"agent"),
    )
    path.write_bytes(b"human")

    assert agent_journal.recent(pdir)[0]["status"] == "conflict"
    with pytest.raises(agent_journal.UndoError) as caught:
        _undo(pdir, entry)
    assert caught.value.code == "journal_undo_conflict"
    assert path.read_bytes() == b"human"


def test_asset_wildcard_import_undo_restores_sources_before_deleting_pdf(pdir: Path) -> None:
    ref = "papers/imported.pdf"
    payload = b"%PDF-1.4\nimported"
    kinds = ("research_source", agent_journal.asset_kind("*"))

    def import_pdf() -> None:
        _write_asset(pdir, ref, payload)
        research_sources.mutate_research_sources(
            pdir,
            lambda inbox: research_sources.add_research_source(
                inbox,
                source_id="paper-new",
                title="Imported",
                kind="paper",
                metadata={"pdf_asset_ref": ref},
            ),
        )

    entry = _journal(pdir, kinds, import_pdf)
    assert {change["entity"] for change in entry["changes"]} == {"research_source", "asset:*"}
    assert _snapshot_paths(_digest(payload)) == []

    _undo(pdir, entry)
    assert "paper-new" not in _sources_by_id(pdir)
    assert not _asset_path(pdir, ref).exists()


def test_new_asset_undo_keeps_pdf_still_referenced_by_another_source(pdir: Path) -> None:
    ref = "papers/shared.pdf"
    _save_sources(
        pdir,
        [{"id": "paper-a", "title": "A", "kind": "paper", "metadata": {"pdf_asset_ref": ref}}],
    )

    def create_shared_pdf() -> None:
        _write_asset(pdir, ref, b"shared")
        research_sources.mutate_research_sources(
            pdir,
            lambda inbox: research_sources.add_research_source(
                inbox,
                source_id="paper-b",
                title="B",
                kind="paper",
                metadata={"pdf_asset_ref": ref},
            ),
        )

    entry = _journal(pdir, ("research_source", "asset:*"), create_shared_pdf)
    _undo(pdir, entry)

    assert set(_sources_by_id(pdir)) == {"paper-a"}
    assert _asset_path(pdir, ref).read_bytes() == b"shared"


def test_pdf_snapshot_failure_rolls_back_sources_and_already_restored_assets(pdir: Path) -> None:
    ref1 = "papers/first.pdf"
    ref2 = "papers/second.pdf"
    old1 = b"first old"
    old2 = b"second old"
    _save_sources(
        pdir,
        [
            {"id": "paper-1", "title": "One", "kind": "paper", "metadata": {"pdf_asset_ref": ref1}},
            {"id": "paper-2", "title": "Two", "kind": "paper", "metadata": {"pdf_asset_ref": ref2}},
        ],
    )
    path1 = _write_asset(pdir, ref1, old1)
    path2 = _write_asset(pdir, ref2, old2)

    def delete_assets() -> None:
        _set_title(pdir, "paper-1", "Agent")
        path1.unlink()
        path2.unlink()

    entry = _journal(
        pdir,
        ("research_source", agent_journal.asset_kind(ref1), agent_journal.asset_kind(ref2)),
        delete_assets,
    )
    first_change = next(change for change in entry["changes"] if change["entity"] == agent_journal.asset_kind(ref1))
    digest = first_change["before"]["item"]["sha256"]
    snapshots = _snapshot_paths(digest)
    assert len(snapshots) == 1
    snapshots[0].unlink()

    with pytest.raises(agent_journal.UndoError) as caught:
        _undo(pdir, entry)

    assert caught.value.code == "journal_snapshot_invalid"
    assert _sources_by_id(pdir)["paper-1"].title == "Agent"
    assert not path1.exists()
    assert not path2.exists()
    assert agent_journal.load_entries(pdir)[0]["undone_at"] == ""


def test_retention_prunes_only_snapshots_orphaned_by_removed_entries(
    pdir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ref = "papers/retention.pdf"
    payload = b"retained old bytes"
    path = _write_asset(pdir, ref, payload)
    first = _journal(pdir, (agent_journal.asset_kind(ref),), path.unlink)
    digest = _digest(payload)
    assert len(_snapshot_paths(digest)) == 1

    monkeypatch.setattr(agent_journal, "MAX_ENTRIES", 1)
    second = _journal(
        pdir,
        ("research_source",),
        lambda: research_sources.mutate_research_sources(
            pdir,
            lambda inbox: research_sources.add_research_source(inbox, source_id="new", title="New"),
        ),
    )

    entries = agent_journal.load_entries(pdir)
    assert [entry["id"] for entry in entries] == [second["id"]]
    assert first["id"] != second["id"]
    assert _snapshot_paths(digest) == []


def test_asset_snapshot_store_is_isolated_by_resolved_profile(
    pdir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ref = "papers/same-name.pdf"
    first = b"first profile"
    second = b"second profile"
    _write_asset(pdir, ref, first)
    agent_journal.prepare(pdir, [agent_journal.asset_kind(ref)])

    other = tmp_path / "another-root" / "alice"
    other.mkdir(parents=True)
    monkeypatch.setenv("NBLANE_RESEARCH_ASSET_ROOT", str(tmp_path / "other-assets"))
    _write_asset(other, ref, second)
    agent_journal.prepare(other, [agent_journal.asset_kind(ref)])

    assert research_journal._asset_snapshot_root(pdir) != research_journal._asset_snapshot_root(other)
    first_snapshot = _snapshot_paths(_digest(first))
    second_snapshot = _snapshot_paths(_digest(second))
    assert len(first_snapshot) == 1
    assert len(second_snapshot) == 1
    assert first_snapshot[0].read_bytes() == first
    assert second_snapshot[0].read_bytes() == second


def test_agent_ops_asset_snapshot_failure_prevents_domain_write(pdir: Path) -> None:
    ref = "papers/snapshot-failure.pdf"
    path = _write_asset(pdir, ref, b"old")
    with patch.object(research_journal, "prepare_asset_snapshots", side_effect=OSError("snapshot down")):
        with pytest.raises(agent_ops.AgentJournalError):
            _begin_assets(pdir, (agent_journal.asset_kind(ref),))
    assert path.read_bytes() == b"old"
    assert agent_journal.load_entries(pdir) == []


def test_agent_ops_asset_record_failure_is_explicit_and_marks_committed_write(pdir: Path) -> None:
    ref = "papers/record-failure.pdf"
    path = _write_asset(pdir, ref, b"old")
    write = _begin_assets(pdir, (agent_journal.asset_kind(ref),))
    path.unlink()

    with patch.object(agent_journal, "record", side_effect=OSError("journal down")):
        with pytest.raises(agent_ops.AgentJournalError):
            agent_ops.finish(write)

    assert write.write_committed is True
    assert not path.exists()
    assert agent_journal.load_entries(pdir) == []


def test_agent_ops_asset_after_snapshot_failure_is_not_a_silent_success(pdir: Path) -> None:
    ref = "papers/after-snapshot-failure.pdf"
    path = _write_asset(pdir, ref, b"old")
    write = _begin_assets(pdir, (agent_journal.asset_kind(ref),))
    path.unlink()

    with patch.object(agent_journal, "snapshot", side_effect=OSError("after snapshot down")):
        with pytest.raises(agent_ops.AgentJournalError):
            agent_ops.finish(write)

    assert not path.exists()
    assert agent_journal.load_entries(pdir) == []
