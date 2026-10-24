"""Deterministic concurrency regressions for research files."""

from __future__ import annotations

import multiprocessing
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest

from nblane.core.file_state import FileConflictError, snapshot_file
from nblane.core.reader_actions import ReaderActionContext, save_reader_progress
from nblane.core.research_jsonl import (
    delete_jsonl,
    load_jsonl,
    mutate_jsonl,
    replace_jsonl,
)
from nblane.core.research_papers import (
    PaperPage,
    PaperSegment,
    PaperStructureUnit,
    create_paper_annotation,
    load_paper_annotations,
    load_paper_translations,
    save_paper_pages,
    save_paper_segments,
    save_paper_structure_units,
    upsert_paper_translations,
)
from nblane.core.research_sources import (
    ResearchSourceInbox,
    add_research_source,
    load_research_sources,
    mutate_research_sources,
    save_research_sources,
    update_research_source,
)
from nblane.core.research_workspace import create_chunk, load_chunks

SOURCE_ID = "source:paper:concurrency"


def _profile(root: Path) -> Path:
    profile = root / "alice"
    profile.mkdir()
    inbox = ResearchSourceInbox(profile="alice")
    add_research_source(
        inbox,
        "Original title",
        source_id=SOURCE_ID,
        kind="paper",
        metadata={"last_read_page": 1, "last_read_at": "2020-01-01T00:00:00+00:00"},
    )
    save_research_sources(profile, inbox)
    return profile


def _reader_context(profile: Path) -> ReaderActionContext:
    return ReaderActionContext(
        profile_name="alice",
        profile_path=profile,
        user_id="test",
        source_id=SOURCE_ID,
    )


def test_stale_title_save_and_reader_progress_preserve_both(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    stale = load_research_sources(profile)
    update_research_source(stale, SOURCE_ID, title="Edited title")
    reader_started = threading.Event()
    reader_done = threading.Event()

    def reader() -> None:
        reader_started.set()
        try:
            save_reader_progress(_reader_context(profile), {"page": 9})
        finally:
            reader_done.set()

    def title_save() -> None:
        assert reader_started.wait(timeout=5)
        assert reader_done.wait(timeout=5)
        save_research_sources(profile, stale)

    with ThreadPoolExecutor(max_workers=2) as pool:
        reader_future = pool.submit(reader)
        title_future = pool.submit(title_save)
        reader_future.result(timeout=10)
        title_future.result(timeout=10)

    source = load_research_sources(profile).by_id()[SOURCE_ID]
    assert source.title == "Edited title"
    assert source.metadata["last_read_page"] == 9

    save_reader_progress(_reader_context(profile), {"page": 10})
    source = load_research_sources(profile).by_id()[SOURCE_ID]
    assert source.title == "Edited title"
    assert source.metadata["last_read_page"] == 10


def test_sources_mutation_noop_exception_and_explicit_clear(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    path = profile / "research" / "sources.yaml"
    before = snapshot_file(path)

    with patch("nblane.core.research_sources.git_backup.record_change") as backup:
        assert mutate_research_sources(profile, lambda inbox: "unchanged") == "unchanged"

        def fail(inbox: ResearchSourceInbox) -> None:
            inbox.sources[0].title = "Must not persist"
            raise RuntimeError("abort")

        with pytest.raises(RuntimeError, match="abort"):
            mutate_research_sources(profile, fail)
        assert snapshot_file(path) == before
        backup.assert_not_called()

        def clear(inbox: ResearchSourceInbox) -> None:
            update_research_source(inbox, SOURCE_ID, metadata={})

        mutate_research_sources(profile, clear)
        backup.assert_called_once()

    source = load_research_sources(profile).by_id()[SOURCE_ID]
    assert "last_read_page" not in source.metadata
    assert "last_read_at" not in source.metadata


def test_sources_mutation_rechecks_expected_snapshot(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    path = profile / "research" / "sources.yaml"
    expected = snapshot_file(path)
    concurrent = load_research_sources(profile)
    update_research_source(concurrent, SOURCE_ID, title="Concurrent title")
    save_research_sources(profile, concurrent)
    called = False

    def stale_mutation(inbox: ResearchSourceInbox) -> None:
        nonlocal called
        called = True
        inbox.sources[0].title = "Stale title"

    with pytest.raises(FileConflictError):
        mutate_research_sources(
            profile,
            stale_mutation,
            expected_snapshot=expected,
        )

    assert not called
    assert load_research_sources(profile).by_id()[SOURCE_ID].title == "Concurrent title"


def test_concurrent_annotation_chunk_and_translation_ids(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    workers = 8

    def run_concurrently(call) -> None:
        barrier = threading.Barrier(workers)

        def invoke(index: int):
            barrier.wait(timeout=5)
            return call(index)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(invoke, index) for index in range(workers)]
            for future in futures:
                future.result(timeout=15)

    with (
        patch("nblane.core.research_jsonl.git_backup.record_change"),
        patch("nblane.core.research_sources.git_backup.record_change"),
    ):
        run_concurrently(
            lambda index: create_paper_annotation(
                profile, SOURCE_ID, f"Annotation {index}", page=index + 1
            )
        )
        annotations = load_paper_annotations(profile, SOURCE_ID)
        assert len(annotations) == workers
        assert len({row.id for row in annotations}) == workers
        assert {row.selected_text for row in annotations} == {
            f"Annotation {index}" for index in range(workers)
        }

        run_concurrently(
            lambda index: create_chunk(profile, SOURCE_ID, f"Chunk {index}")
        )
        chunks = load_chunks(profile, SOURCE_ID)
        assert len(chunks) == workers
        assert len({row.id for row in chunks}) == workers
        assert {row.text for row in chunks} == {
            f"Chunk {index}" for index in range(workers)
        }

        run_concurrently(
            lambda index: upsert_paper_translations(
                profile,
                SOURCE_ID,
                [
                    {
                        "scope_type": "selection",
                        "scope_ref": f"selection:{index}",
                        "source_hash": f"hash:{index}",
                        "source_text": f"Source {index}",
                        "target_lang": "zh",
                        "translated_text": f"Translation {index}",
                    }
                ],
            )
        )
        translations = load_paper_translations(profile, SOURCE_ID)
        assert len(translations) == workers
        assert len({row.id for row in translations}) == workers
        assert {row.translated_text for row in translations} == {
            f"Translation {index}" for index in range(workers)
        }


def _cross_process_worker(
    profile_text: str,
    jsonl_text: str,
    barrier,
    worker_index: int,
) -> None:
    os.environ["NBLANE_DATA_GIT_AUTOCOMMIT"] = "0"
    os.environ["NBLANE_DATA_GIT_AUTOPUSH"] = "0"
    from nblane.core.research_jsonl import mutate_jsonl
    from nblane.core.research_sources import (
        add_research_source,
        mutate_research_sources,
    )

    profile = Path(profile_text)
    jsonl_path = Path(jsonl_text)
    barrier.wait(timeout=30)
    for row_index in range(3):
        def add_source(inbox) -> None:
            add_research_source(
                inbox,
                f"Process {worker_index} source {row_index}",
                kind="paper",
            )

        mutate_research_sources(profile, add_source)

        def append_row(rows) -> None:
            rows.append(
                {
                    "id": f"row:{len(rows) + 1:04d}",
                    "text": f"Process {worker_index} row {row_index}",
                }
            )

        mutate_jsonl(jsonl_path, append_row)


def test_cross_process_sources_and_jsonl_do_not_lose_rows(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    jsonl_path = profile / "research" / "chunks" / "cross-process.jsonl"
    context = multiprocessing.get_context("spawn")
    count = 4
    barrier = context.Barrier(count)
    processes = [
        context.Process(
            target=_cross_process_worker,
            args=(str(profile), str(jsonl_path), barrier, index),
        )
        for index in range(count)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=60)
    try:
        assert [process.exitcode for process in processes] == [0] * count
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

    sources = load_research_sources(profile).sources
    imported = [source for source in sources if source.id != SOURCE_ID]
    assert len(imported) == count * 3
    assert len({source.id for source in imported}) == count * 3
    rows = load_jsonl(jsonl_path)
    assert len(rows) == count * 3
    assert len({row["id"] for row in rows}) == count * 3
    assert {row["text"] for row in rows} == {
        f"Process {worker} row {index}"
        for worker in range(count)
        for index in range(3)
    }


def _derived_row(kind: str, text: str):
    if kind == "pages":
        return PaperPage(source_id=SOURCE_ID, page=1, text=text)
    if kind == "segments":
        return PaperSegment(
            segment_id="seg:derived",
            source_id=SOURCE_ID,
            page=1,
            order=1,
            text=text,
        )
    return PaperStructureUnit(
        unit_id="unit:derived",
        source_id=SOURCE_ID,
        kind="paragraph",
        page_start=1,
        page_end=2,
        order=1,
        text=text,
    )


@pytest.mark.parametrize("kind", ["pages", "segments", "structure"])
def test_derived_replacement_conflict_preserves_concurrent_update(
    tmp_path: Path,
    kind: str,
) -> None:
    profile = _profile(tmp_path)
    save = {
        "pages": save_paper_pages,
        "segments": save_paper_segments,
        "structure": save_paper_structure_units,
    }[kind]
    path = save(profile, SOURCE_ID, [_derived_row(kind, "initial")])
    expected = snapshot_file(path)
    save(profile, SOURCE_ID, [_derived_row(kind, "concurrent")])

    with pytest.raises(FileConflictError):
        save(
            profile,
            SOURCE_ID,
            [_derived_row(kind, "stale derived result")],
            expected_snapshot=expected,
        )

    rows = load_jsonl(path)
    assert [row["text"] for row in rows] == ["concurrent"]


def test_delete_waits_for_jsonl_mutation(tmp_path: Path) -> None:
    path = tmp_path / "research" / "chunks" / "delete-lock.jsonl"
    replace_jsonl(path, [{"id": "row:initial"}])
    entered = threading.Event()
    release = threading.Event()
    delete_started = threading.Event()
    delete_done = threading.Event()

    def writer() -> None:
        def apply(rows) -> None:
            entered.set()
            assert release.wait(timeout=5)
            rows.append({"id": "row:written"})

        mutate_jsonl(path, apply)

    def deleter() -> None:
        delete_started.set()
        delete_jsonl(path)
        delete_done.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        write_future = pool.submit(writer)
        assert entered.wait(timeout=5)
        delete_future = pool.submit(deleter)
        assert delete_started.wait(timeout=5)
        assert not delete_done.wait(timeout=0.05)
        release.set()
        write_future.result(timeout=10)
        delete_future.result(timeout=10)

    assert not path.exists()
