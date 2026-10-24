"""Internal module for nblane.core.research_papers package."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from nblane.core.file_state import FileSnapshot
from nblane.core.research_jsonl import mutate_jsonl
from nblane.core.research_workspace import (
    ResearchChunk,
    source_slug,
)

from ._constants import (
    PAPER_ANNOTATIONS_DIRNAME,
    PAPER_PAGES_DIRNAME,
    PAPER_SEGMENTS_DIRNAME,
    PAPER_STRUCTURE_DIRNAME,
    PAPER_TRANSLATIONS_DIRNAME,
)
from ._paths import _jsonl_path, _load_jsonl, _write_jsonl
from ._types import (
    PaperAnnotation,
    PaperPage,
    PaperSegment,
    PaperStructureUnit,
    PaperTranslation,
)

def load_paper_pages(profile: str | Path, source_id: str) -> list[PaperPage]:
    return [
        page
        for row in _load_jsonl(_jsonl_path(profile, PAPER_PAGES_DIRNAME, source_id))
        if (page := PaperPage.from_dict(row)) is not None
    ]


def save_paper_pages(
    profile: str | Path,
    source_id: str,
    pages: list[PaperPage | dict],
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> Path:
    rows = []
    for item in pages:
        page = item if isinstance(item, PaperPage) else PaperPage.from_dict(item)
        if page is not None:
            rows.append(page.to_dict())
    return _write_jsonl(
        _jsonl_path(profile, PAPER_PAGES_DIRNAME, source_id),
        rows,
        action=f"update paper pages for {source_id}",
        expected_snapshot=expected_snapshot,
    )


def load_paper_segments(profile: str | Path, source_id: str) -> list[PaperSegment]:
    return [
        segment
        for row in _load_jsonl(_jsonl_path(profile, PAPER_SEGMENTS_DIRNAME, source_id))
        if (segment := PaperSegment.from_dict(row)) is not None
    ]


def save_paper_segments(
    profile: str | Path,
    source_id: str,
    segments: list[PaperSegment | dict],
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> Path:
    rows = []
    for item in segments:
        segment = item if isinstance(item, PaperSegment) else PaperSegment.from_dict(item)
        if segment is not None:
            rows.append(segment.to_dict())
    return _write_jsonl(
        _jsonl_path(profile, PAPER_SEGMENTS_DIRNAME, source_id),
        rows,
        action=f"update paper segments for {source_id}",
        expected_snapshot=expected_snapshot,
    )


def load_paper_structure_units(profile: str | Path, source_id: str) -> list[PaperStructureUnit]:
    return [
        unit
        for row in _load_jsonl(_jsonl_path(profile, PAPER_STRUCTURE_DIRNAME, source_id))
        if (unit := PaperStructureUnit.from_dict(row)) is not None
    ]


def save_paper_structure_units(
    profile: str | Path,
    source_id: str,
    units: list[PaperStructureUnit | dict],
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> Path:
    rows = []
    for item in units:
        unit = item if isinstance(item, PaperStructureUnit) else PaperStructureUnit.from_dict(item)
        if unit is not None:
            rows.append(unit.to_dict())
    return _write_jsonl(
        _jsonl_path(profile, PAPER_STRUCTURE_DIRNAME, source_id),
        rows,
        action=f"update paper structure units for {source_id}",
        expected_snapshot=expected_snapshot,
    )


def load_paper_annotations(profile: str | Path, source_id: str) -> list[PaperAnnotation]:
    return [
        ann
        for row in _load_jsonl(_jsonl_path(profile, PAPER_ANNOTATIONS_DIRNAME, source_id))
        if (ann := PaperAnnotation.from_dict(row)) is not None
    ]


def save_paper_annotations(
    profile: str | Path,
    source_id: str,
    rows: list[PaperAnnotation | dict],
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> Path:
    serialized = []
    for item in rows:
        ann = item if isinstance(item, PaperAnnotation) else PaperAnnotation.from_dict(item)
        if ann is not None:
            serialized.append(ann.to_dict())
    return _write_jsonl(
        _jsonl_path(profile, PAPER_ANNOTATIONS_DIRNAME, source_id),
        serialized,
        action=f"update paper annotations for {source_id}",
        expected_snapshot=expected_snapshot,
    )


_T = TypeVar("_T")


def mutate_paper_annotations(
    profile: str | Path,
    source_id: str,
    fn: Callable[[list[PaperAnnotation]], _T],
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> _T:
    path = _jsonl_path(profile, PAPER_ANNOTATIONS_DIRNAME, source_id)

    def apply(rows: list[dict]) -> _T:
        annotations = [
            ann
            for row in rows
            if (ann := PaperAnnotation.from_dict(row)) is not None
        ]
        result = fn(annotations)
        rows[:] = [ann.to_dict() for ann in annotations]
        return result

    return mutate_jsonl(
        path,
        apply,
        expected_snapshot=expected_snapshot,
        action=f"update paper annotations for {source_id}",
    )


def _next_annotation_id(existing: list[PaperAnnotation], source_id: str) -> str:
    prefix = f"ann:{source_slug(source_id)}:"
    max_index = 0
    for row in existing:
        if not row.id.startswith(prefix):
            continue
        try:
            max_index = max(max_index, int(row.id.rsplit(":", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_index + 1:04d}"


def _next_chunk_id(existing: list[ResearchChunk], source_id: str) -> str:
    prefix = f"chunk:{source_slug(source_id)}:"
    max_index = 0
    for chunk in existing:
        if not chunk.id.startswith(prefix):
            continue
        try:
            max_index = max(max_index, int(chunk.id.rsplit(":", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_index + 1:03d}"


def _segment_hash_map(profile: str | Path, source_id: str) -> dict[str, PaperSegment]:
    return {segment.segment_id: segment for segment in load_paper_segments(profile, source_id)}


def load_paper_translations(profile: str | Path, source_id: str) -> list[PaperTranslation]:
    segments = _segment_hash_map(profile, source_id)
    rows = []
    for raw in _load_jsonl(_jsonl_path(profile, PAPER_TRANSLATIONS_DIRNAME, source_id)):
        tr = PaperTranslation.from_dict(raw)
        if tr is not None:
            rows.append(_mark_translation_status(tr, segments))
    return rows


def save_paper_translations(
    profile: str | Path,
    source_id: str,
    rows: list[PaperTranslation | dict],
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> Path:
    serialized = []
    for item in rows:
        tr = item if isinstance(item, PaperTranslation) else PaperTranslation.from_dict(item)
        if tr is not None:
            serialized.append(tr.to_dict())
    return _write_jsonl(
        _jsonl_path(profile, PAPER_TRANSLATIONS_DIRNAME, source_id),
        serialized,
        action=f"update paper translations for {source_id}",
        expected_snapshot=expected_snapshot,
    )


def mutate_paper_translations(
    profile: str | Path,
    source_id: str,
    fn: Callable[[list[PaperTranslation], dict[str, PaperSegment]], _T],
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> _T:
    path = _jsonl_path(profile, PAPER_TRANSLATIONS_DIRNAME, source_id)

    def apply(rows: list[dict]) -> _T:
        segments = _segment_hash_map(profile, source_id)
        translations = []
        for raw in rows:
            translation = PaperTranslation.from_dict(raw)
            if translation is not None:
                translations.append(_mark_translation_status(translation, segments))
        result = fn(translations, segments)
        rows[:] = [translation.to_dict() for translation in translations]
        return result

    return mutate_jsonl(
        path,
        apply,
        expected_snapshot=expected_snapshot,
        action=f"update paper translations for {source_id}",
    )


def _next_translation_id(existing: list[PaperTranslation], source_id: str) -> str:
    prefix = f"tr:{source_slug(source_id)}:"
    max_index = 0
    for row in existing:
        if not row.id.startswith(prefix):
            continue
        try:
            max_index = max(max_index, int(row.id.rsplit(":", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_index + 1:04d}"
