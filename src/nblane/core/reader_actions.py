"""Side-effecting paper Reader actions shared by Streamlit and FastAPI entrypoints."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from nblane.core import git_backup
from nblane.core.ai import (
    answer_paper_question,
    deep_read_paper_codex,
    explain_paper_selection,
    generate_paper_review_card,
    translate_paper_segments,
)
from nblane.core.research_papers import (
    NO_LLM_TRANSLATION_WARNING,
    build_paper_layout_units,
    build_paper_structure_units,
    create_paper_annotation,
    ensure_paper_reading_artifacts,
    load_paper_analysis,
    load_paper_annotations,
    load_paper_pages,
    load_paper_segments,
    load_paper_translations,
    normalize_translation_row,
    reader_translation_layout_units,
    reader_translation_structure_units,
    save_paper_analysis,
    save_paper_annotations,
    text_hash,
    translate_full_paper,
    translation_text_from_row,
    upsert_paper_translations,
)
from nblane.core.research_sources import (
    load_research_sources,
    save_research_sources,
    update_research_source,
)
from nblane.core.research_workspace import (
    create_chunk,
    create_citation,
    load_chunks,
    upsert_research_claim,
)
from nblane.research_paper_reader_component.events import (
    ANALYZE_PAPER,
    ANNOTATION_CREATE,
    ANNOTATION_DELETE,
    ANNOTATION_UPDATE,
    ASK_PAPER,
    CREATE_CHUNK_FROM_SELECTION,
    CREATE_CITATION,
    EXPLAIN_SELECTION,
    PREPARE_READER_ARTIFACTS,
    RETRY_TRANSLATION_SCOPE,
    SAVE_PROGRESS,
    TRANSLATE_FULL_PAPER,
    TRANSLATE_SELECTION,
    TRANSLATE_VISIBLE_PAGES,
    clean_page_list,
)


@dataclass(frozen=True)
class ReaderActionContext:
    """Context required to perform one Reader action."""

    profile_name: str
    profile_path: Path
    user_id: str
    source_id: str


@dataclass
class ReaderActionResult:
    """JSON-serializable Reader action result."""

    ok: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    changed_ids: dict[str, str] = field(default_factory=dict)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "data": dict(self.data),
            "warnings": list(self.warnings),
            "changed_ids": dict(self.changed_ids),
            "message": self.message,
        }


def _payload_text(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _payload_list(payload: dict[str, Any], *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            values.extend(part.strip() for part in value.split(",") if part.strip())
        elif isinstance(value, (list, tuple, set)):
            values.extend(str(item).strip() for item in value if str(item).strip())
        elif value is not None and str(value).strip():
            values.append(str(value).strip())
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _payload_int(payload: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(payload.get(key) or default)
    except (TypeError, ValueError):
        return default


def _payload_float(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key) or default)
    except (TypeError, ValueError):
        return default


def _payload_bool(payload: dict[str, Any], key: str, default: bool = False) -> bool:
    if key not in payload:
        return default
    value = payload.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        clean = value.strip().lower()
        if clean in {"1", "true", "yes", "on"}:
            return True
        if clean in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _backup_warnings() -> list[str]:
    warnings: list[str] = []
    for result in git_backup.consume_results():
        if result.error:
            warnings.append(f"Git backup failed: {result.error}")
        if result.push_error:
            warnings.append(f"Git backup committed but push failed: {result.push_error}")
    return warnings


def _selection_segments(payload: dict[str, Any], segment_rows) -> list[dict[str, Any]]:
    refs = set(
        _payload_list(
            payload,
            "segment_refs",
            "segment_ids",
            "segment_id",
            "scope_refs",
            "scope_ref",
        )
    )
    if refs:
        return [segment.to_dict() for segment in segment_rows if segment.segment_id in refs]
    selected_text = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
    if not selected_text:
        return []
    selected_hash = _payload_text(payload, "selected_text_hash", "text_hash", "source_hash")
    if not selected_hash:
        selected_hash = text_hash(selected_text)
    synthetic_id = f"selection:{selected_hash.rsplit(':', 1)[-1][:16]}"
    page = _payload_int(payload, "page")
    locator = _payload_text(payload, "locator") or (f"p. {page}" if page else "")
    return [
        {
            "segment_id": _payload_text(payload, "segment_id") or synthetic_id,
            "source_id": payload.get("source_id", ""),
            "scope_type": "selection",
            "scope_ref": selected_hash,
            "page": page,
            "order": 0,
            "section_path": [],
            "kind": "selection",
            "text": selected_text,
            "text_hash": selected_hash,
            "locator": locator,
            "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
        }
    ]


def _context_segments(payload: dict[str, Any], segment_rows, *, limit: int = 30) -> list[dict[str, Any]]:
    picked = _selection_segments(payload, segment_rows)
    if picked:
        return picked
    return [segment.to_dict() for segment in segment_rows[:limit]]


def _question_context_segments(payload: dict[str, Any], segment_rows) -> list[dict[str, Any]]:
    picked = _selection_segments(payload, segment_rows)
    if picked:
        return picked
    whole_paper_payload = dict(payload)
    whole_paper_payload["full_paper"] = True
    whole_paper_payload.setdefault("scope", "paper")
    return _compact_segments_for_deep_read(whole_paper_payload, segment_rows)


def _balanced_paper_segment_indexes(count: int, *, limit: int) -> list[int]:
    """Return indexes sampled across a paper instead of only the first pages."""

    if count <= limit:
        return list(range(count))
    selected_indexes: set[int] = set()
    front_count = min(8, max(1, limit // 5))
    for index in range(front_count):
        selected_indexes.add(index)
    remaining = max(0, limit - len(selected_indexes))
    if remaining:
        span = max(1, count - 1)
        for step in range(remaining):
            index = round(step * span / max(1, remaining - 1))
            selected_indexes.add(min(count - 1, max(0, index)))
            if len(selected_indexes) >= limit:
                break
    return sorted(selected_indexes)[:limit]


def _balanced_paper_segments(segment_rows, *, limit: int) -> list:
    """Sample segments across the paper instead of only the first pages."""

    rows = list(segment_rows)
    return [rows[index] for index in _balanced_paper_segment_indexes(len(rows), limit=limit)]


_DEEP_READ_SECTION_PRIORITY: tuple[tuple[int, tuple[str, ...]], ...] = (
    (0, ("abstract", "摘要")),
    (1, ("introduction", "intro", "background", "背景", "引言")),
    (2, ("related", "prior", "literature", "相关")),
    (3, ("method", "methods", "approach", "model", "architecture", "算法", "方法", "模型")),
    (4, ("experiment", "evaluation", "benchmark", "dataset", "实验", "评估", "数据")),
    (5, ("result", "analysis", "ablation", "study", "结果", "分析", "消融")),
    (6, ("discussion", "limitation", "future", "讨论", "局限")),
    (7, ("conclusion", "结论")),
)


def _segment_section_label(segment: Any) -> str:
    """Return a compact section label for a paper segment."""

    path = getattr(segment, "section_path", []) or []
    if isinstance(path, (list, tuple)):
        parts = [str(item or "").strip() for item in path if str(item or "").strip()]
        if parts:
            return " / ".join(parts)
    locator = str(getattr(segment, "locator", "") or "").strip()
    if "§" in locator:
        return locator.rsplit("§", 1)[-1].strip() or "Unsectioned"
    return "Unsectioned"


def _deep_read_section_priority(label: str) -> int:
    """Rank recognizable paper sections for deep-read context sampling."""

    lower = str(label or "").lower()
    for priority, needles in _DEEP_READ_SECTION_PRIORITY:
        if any(needle in lower for needle in needles):
            return priority
    return 50


def _section_aware_paper_segments(segment_rows, *, limit: int) -> list:
    """Sample the whole paper while reserving coverage for major sections."""

    rows = list(segment_rows)
    if len(rows) <= limit:
        return rows

    selected_indexes: set[int] = set()

    def add(index: int) -> None:
        if 0 <= index < len(rows) and len(selected_indexes) < limit:
            selected_indexes.add(index)

    for index in range(min(6, len(rows))):
        add(index)
    for index in range(max(0, len(rows) - 4), len(rows)):
        add(index)

    buckets: dict[str, list[int]] = {}
    for index, segment in enumerate(rows):
        label = _segment_section_label(segment)
        buckets.setdefault(label, []).append(index)

    ranked = sorted(
        buckets.items(),
        key=lambda item: (
            _deep_read_section_priority(item[0]),
            item[1][0] if item[1] else len(rows),
        ),
    )
    for label, indexes in ranked:
        priority = _deep_read_section_priority(label)
        quota = 3 if priority <= 7 else 1
        positions = [0]
        if quota >= 2 and len(indexes) > 2:
            positions.append(len(indexes) // 2)
        if quota >= 3 and len(indexes) > 1:
            positions.append(len(indexes) - 1)
        for position in positions:
            add(indexes[position])
            if len(selected_indexes) >= limit:
                break
        if len(selected_indexes) >= limit:
            break

    for index in _balanced_paper_segment_indexes(len(rows), limit=limit):
        add(index)
        if len(selected_indexes) >= limit:
            break

    return [rows[index] for index in sorted(selected_indexes)[:limit]]


def _deep_read_sections_covered(rows: list[dict[str, Any]]) -> list[str]:
    """Return stable section labels represented in a deep-read context."""

    labels: list[str] = []
    seen: set[str] = set()
    for row in rows:
        path = row.get("section_path") if isinstance(row, dict) else []
        if isinstance(path, (list, tuple)):
            label = " / ".join(str(item or "").strip() for item in path if str(item or "").strip())
        else:
            label = str(path or "").strip()
        if not label:
            label = "Unsectioned"
        if label not in seen:
            seen.add(label)
            labels.append(label)
    return labels


def _compact_picked_segments(
    picked,
    *,
    limit: int,
    char_limit: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total_chars = 0
    for segment in picked:
        text = str(segment.text or "").strip()
        remaining = char_limit - total_chars
        if remaining <= 0 or len(rows) >= limit:
            break
        clipped = text[: min(len(text), remaining, 1200)]
        if not clipped:
            continue
        total_chars += len(clipped)
        rows.append(
            {
                "segment_id": segment.segment_id,
                "source_id": segment.source_id,
                "page": segment.page,
                "order": segment.order,
                "section_path": list(segment.section_path),
                "kind": segment.kind,
                "text": clipped,
                "text_hash": segment.text_hash,
                "locator": segment.locator,
            }
        )
    return rows


def _compact_segments_for_deep_read(
    payload: dict[str, Any],
    segment_rows,
    *,
    limit: int = 40,
    char_limit: int = 24_000,
) -> list[dict[str, Any]]:
    full_paper = _payload_bool(payload, "full_paper") or _payload_text(payload, "scope") == "paper"
    refs = set(_payload_list(payload, "segment_refs", "segment_ids", "segment_id"))
    visible_pages = set()
    if not full_paper:
        visible_pages = {
            int(item)
            for item in payload.get("visible_pages", [])
            if str(item).strip().isdigit()
        } if isinstance(payload.get("visible_pages"), list) else set()
    primary_page = _payload_int(payload, "primary_page", _payload_int(payload, "page", 0))
    if not full_paper and not refs and not visible_pages and primary_page:
        visible_pages = {primary_page}
    if full_paper and not refs:
        limit = 80
        char_limit = 60_000
        picked = _section_aware_paper_segments(segment_rows, limit=limit)
    else:
        picked = [
            segment
            for segment in segment_rows
            if (refs and segment.segment_id in refs)
            or (visible_pages and segment.page in visible_pages)
        ]
    if not picked:
        picked = list(segment_rows[:limit])
    return _compact_picked_segments(picked, limit=limit, char_limit=char_limit)


def _deep_read_batch_group(segment: Any) -> str:
    label = _segment_section_label(segment)
    priority = _deep_read_section_priority(label)
    if priority <= 1:
        return "问题与动机"
    if priority == 2:
        return "相关工作与缺口"
    if priority == 3:
        return "方法与机制"
    if priority in {4, 5}:
        return "实验与结果"
    if priority in {6, 7}:
        return "局限与结论"
    return "其它证据"


def _deep_read_section_batches(
    segment_rows,
    *,
    max_batches: int = 6,
    segment_limit: int = 24,
    char_limit: int = 18_000,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[Any]] = {}
    order = ["问题与动机", "相关工作与缺口", "方法与机制", "实验与结果", "局限与结论", "其它证据"]
    for segment in segment_rows:
        grouped.setdefault(_deep_read_batch_group(segment), []).append(segment)

    batches: list[dict[str, Any]] = []
    for label in order:
        rows = grouped.get(label) or []
        if not rows:
            continue
        picked = _section_aware_paper_segments(rows, limit=min(segment_limit, len(rows)))
        compact = _compact_picked_segments(picked, limit=segment_limit, char_limit=char_limit)
        if not compact:
            continue
        batches.append(
            {
                "label": label,
                "segments": compact,
                "source_segments": len(rows),
                "sections_covered": _deep_read_sections_covered(compact),
                "pages_covered": sorted(
                    {
                        int(row.get("page") or 0)
                        for row in compact
                        if int(row.get("page") or 0) > 0
                    }
                ),
            }
        )
    return batches[:max_batches]


def _explicit_codex_timeout(payload: dict[str, Any]) -> float:
    return _payload_float(payload, "codex_timeout_seconds") or _payload_float(payload, "timeout_seconds")


def _adaptive_deep_read_timeout_seconds(
    *,
    source_segments: int,
    supplied_segments: int,
    pages: int,
    mode: str = "single",
    batch_count: int = 0,
) -> int:
    if mode == "batch":
        return int(max(300, min(540, 120 + supplied_segments * 8 + pages * 4)))
    if mode == "synthesis":
        return int(max(420, min(720, 240 + batch_count * 70 + supplied_segments * 2)))
    return int(max(420, min(900, 180 + supplied_segments * 4 + pages * 5 + source_segments * 1.5)))


def _copy_deep_read_runtime_options(source: dict[str, Any], target: dict[str, Any]) -> None:
    for key in (
        "codex_timeout_seconds",
        "timeout_seconds",
        "codex_idle_timeout_seconds",
        "idle_timeout_seconds",
        "codex_model",
        "deep_read_model",
        "codex_home_policy",
    ):
        value = source.get(key)
        if value not in (None, "", []):
            target[key] = value


def _deep_read_payload_pages(rows: list[dict[str, Any]]) -> list[int]:
    return sorted(
        {
            int(row.get("page") or 0)
            for row in rows
            if int(row.get("page") or 0) > 0
        }
    )


def _deep_read_report_text(report: dict[str, Any], *, limit: int = 4000) -> str:
    picked: dict[str, Any] = {}
    for key in (
        "takeaway",
        "problem",
        "motivation",
        "context",
        "contributions",
        "method",
        "mechanism",
        "metrics",
        "experiments",
        "results",
        "limitations",
        "project_relevance",
        "open_questions",
        "section_summaries",
        "terms",
        "findings",
        "reading_plan",
        "warnings",
        "cited_segment_refs",
    ):
        if key in report:
            picked[key] = report.get(key)
    text = json.dumps(picked, ensure_ascii=False, sort_keys=True)
    return text[:limit]


def _deep_read_batch_chunks(batch_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for index, report in enumerate(batch_reports, start=1):
        label = _payload_text(report, "batch_label") or f"batch {index}"
        chunks.append(
            {
                "chunk_id": f"deep-read-batch:{index}",
                "title": label,
                "kind": "deep_read_batch",
                "text": _deep_read_report_text(report),
                "locator": label,
                "metadata": {
                    "batch_index": index,
                    "batch_label": label,
                    "cited_segment_refs": _payload_list(report, "cited_segment_refs", "segment_refs"),
                },
            }
        )
    return chunks


def _compact_chunks_for_deep_read(chunk_rows, *, limit: int = 20) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chunk in chunk_rows[:limit]:
        metadata = chunk.metadata if isinstance(chunk.metadata, dict) else {}
        rows.append(
            {
                "chunk_id": chunk.id,
                "title": chunk.title,
                "kind": chunk.kind,
                "text": str(chunk.text or "")[:900],
                "locator": chunk.locator,
                "metadata": {
                    key: metadata.get(key)
                    for key in ("page", "segment_id", "selected_text_hash", "annotation_id")
                    if metadata.get(key) not in (None, "", [])
                },
            }
        )
    return rows


def _compact_annotations_for_deep_read(annotation_rows, *, limit: int = 24) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in annotation_rows[:limit]:
        rows.append(
            {
                "annotation_id": row.id,
                "kind": row.kind,
                "page": row.page,
                "locator": row.locator,
                "selected_text": str(row.selected_text or "")[:600],
                "note": str(row.note or "")[:400],
                "tags": list(row.tags),
                "segment_refs": list(row.segment_refs),
            }
        )
    return rows


def _compact_source_for_deep_read(source: Any, source_id: str) -> dict[str, Any]:
    if source is None:
        return {"id": source_id}
    metadata = source.metadata if isinstance(source.metadata, dict) else {}
    return {
        "id": source.id,
        "title": source.title,
        "url": source.url,
        "authors": list(source.authors),
        "published": source.published,
        "summary": str(source.summary or "")[:1200],
        "metadata": {
            key: metadata.get(key)
            for key in (
                "doi",
                "arxiv_id",
                "semantic_scholar_id",
                "venue",
                "page_count",
                "fields_of_study",
                "provider_refs",
            )
            if metadata.get(key) not in (None, "", [])
        },
    }


def _clean_analysis_items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        clean = value.strip()
        return [clean] if clean else []
    if isinstance(value, (list, tuple)):
        return [item for item in value if str(item or "").strip()]
    return [value] if str(value or "").strip() else []


def _analysis_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("text", "summary", "reason", "title", "rationale", "point"):
            clean = str(value.get(key) or "").strip()
            if clean:
                return clean
        return ""
    return str(value or "").strip()


def _analysis_refs_from_value(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        for key in (
            "refs",
            "cited_refs",
            "segment_refs",
            "cited_segment_refs",
            "chunk_refs",
            "cited_chunk_refs",
            "annotation_refs",
            "cited_annotation_refs",
            "segment_id",
            "segment_ref",
            "scope_ref",
            "chunk_id",
            "annotation_id",
        ):
            refs.extend(_payload_list(value, key))
    return refs


def _analysis_score(value: Any) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(10, score))


def _normalize_paper_analysis(raw: dict[str, Any], source_id: str) -> dict[str, Any]:
    warnings = _payload_list(raw, "warnings")
    scores_raw = raw.get("scores") if isinstance(raw.get("scores"), dict) else {}
    scores = {
        "novelty": _analysis_score(scores_raw.get("novelty") or raw.get("novelty")),
        "technical_depth": _analysis_score(scores_raw.get("technical_depth") or raw.get("technical_depth")),
        "evidence_quality": _analysis_score(scores_raw.get("evidence_quality") or raw.get("evidence_quality")),
        "reproducibility": _analysis_score(scores_raw.get("reproducibility") or raw.get("reproducibility")),
        "relevance": _analysis_score(scores_raw.get("relevance") or raw.get("relevance")),
        "overall": _analysis_score(scores_raw.get("overall") or raw.get("overall")),
    }
    analysis: dict[str, Any] = {
        "source_id": source_id,
        "tldr": _payload_text(raw, "tldr", "tl_dr", "summary", "abstract_judgement"),
        "key_points": _clean_analysis_items(raw.get("key_points") or raw.get("findings") or raw.get("contributions")),
        "method": _clean_analysis_items(raw.get("method") or raw.get("methods")),
        "experiments": _clean_analysis_items(raw.get("experiments") or raw.get("evaluation")),
        "limitations": _clean_analysis_items(raw.get("limitations")),
        "usefulness": _payload_text(raw, "usefulness", "useful_for", "project_fit"),
        "scores": scores,
        "score_rationale": _clean_analysis_items(raw.get("score_rationale") or raw.get("rationale")),
        "project_relevance": _clean_analysis_items(raw.get("project_relevance") or raw.get("relevance_notes")),
        "reading_plan": _clean_analysis_items(raw.get("reading_plan") or raw.get("next_steps")),
        "open_questions": _clean_analysis_items(raw.get("open_questions") or raw.get("questions")),
        "cited_segment_refs": _payload_list(raw, "cited_segment_refs", "segment_refs"),
        "cited_chunk_refs": _payload_list(raw, "cited_chunk_refs", "chunk_refs"),
        "cited_annotation_refs": _payload_list(raw, "cited_annotation_refs", "annotation_refs"),
        "warnings": warnings,
    }
    for key in ("key_points", "method", "experiments", "limitations", "score_rationale", "project_relevance"):
        for item in _clean_analysis_items(analysis.get(key)):
            for ref in _analysis_refs_from_value(item):
                if ref.startswith("seg:") and ref not in analysis["cited_segment_refs"]:
                    analysis["cited_segment_refs"].append(ref)
                elif ref.startswith("chunk") and ref not in analysis["cited_chunk_refs"]:
                    analysis["cited_chunk_refs"].append(ref)
                elif ref.startswith("ann") and ref not in analysis["cited_annotation_refs"]:
                    analysis["cited_annotation_refs"].append(ref)
    substantive = [
        *_clean_analysis_items(analysis["key_points"]),
        *_clean_analysis_items(analysis["score_rationale"]),
        *_clean_analysis_items(analysis["limitations"]),
    ]
    has_refs = bool(
        analysis["cited_segment_refs"]
        or analysis["cited_chunk_refs"]
        or analysis["cited_annotation_refs"]
        or any(_analysis_refs_from_value(item) for item in substantive)
    )
    if substantive and not has_refs:
        warning = "Analysis has substantive claims without cited refs."
        if warning not in analysis["warnings"]:
            analysis["warnings"].append(warning)
    if not analysis["tldr"]:
        text_items = [_analysis_text(item) for item in _clean_analysis_items(analysis["key_points"])]
        analysis["tldr"] = text_items[0] if text_items else ""
    return analysis


def _selection_text(payload: dict[str, Any], segment_rows) -> str:
    selected = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
    if selected:
        return selected
    refs = {
        row.get("segment_id")
        for row in _selection_segments(payload, segment_rows)
        if row.get("segment_id")
    }
    if not refs:
        return ""
    return "\n\n".join(segment.text for segment in segment_rows if segment.segment_id in refs)


def _translation_row_current(row: Any, source_hash: str, target_lang: str) -> bool:
    return bool(
        row is not None
        and getattr(row, "target_lang", "") == target_lang
        and getattr(row, "source_hash", "") == source_hash
        and getattr(row, "status", "") == "translated"
        and str(getattr(row, "translated_text", "") or "").strip()
    )


def _visible_translation_summary(
    *,
    scope: str,
    requested_pages: list[int],
    segments_selected: int,
    ai_rows: int,
    saved: int,
    failed: int,
    skipped: int,
    target_lang: str,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "requested_pages": requested_pages,
        "segments_selected": segments_selected,
        "ai_rows": ai_rows,
        "saved": saved,
        "failed": failed,
        "skipped": skipped,
        "target_lang": target_lang,
    }


def _layout_translation_payload(unit: dict[str, Any], source_id: str) -> dict[str, Any]:
    source_text = _payload_text(unit, "source_text", "text")
    source_hash = _payload_text(unit, "source_hash") or text_hash(source_text)
    scope_ref = _payload_text(unit, "scope_ref", "unit_id")
    scope_type = _payload_text(unit, "scope_type") or "layout"
    page = _payload_int(unit, "page")
    return {
        "segment_id": scope_ref,
        "source_id": source_id,
        "scope_type": scope_type,
        "scope_ref": scope_ref,
        "page": page,
        "order": _payload_int(unit, "order"),
        "section_path": unit.get("section_path") if isinstance(unit.get("section_path"), list) else [],
        "kind": _payload_text(unit, "kind") or "paragraph",
        "text": source_text,
        "source_text": source_text,
        "text_hash": source_hash,
        "source_hash": source_hash,
        "locator": _payload_text(unit, "locator") or (f"p. {page}" if page else ""),
        "rects": unit.get("rects") if isinstance(unit.get("rects"), list) else [],
        "table_id": _payload_text(unit, "table_id"),
        "row": unit.get("row"),
        "col": unit.get("col"),
        "row_span": unit.get("row_span"),
        "col_span": unit.get("col_span"),
    }


def _blank_translation_backend_warning(ai_result: Any, translations: list[dict[str, Any]]) -> str:
    if not translations or any(translation_text_from_row(row) for row in translations):
        return ""
    generated_by = {
        _payload_text(row, "generated_by")
        for row in translations
        if isinstance(row, dict) and _payload_text(row, "generated_by")
    }
    marker = " ".join(
        [
            str(getattr(ai_result, "backend", "") or ""),
            " ".join(generated_by),
            " ".join(str(item) for item in getattr(ai_result, "warnings", []) or []),
            str(getattr(ai_result, "error", "") or ""),
        ]
    ).lower()
    if "rule_fallback" in marker or "llm_api_key" in marker or "ai_not_configured" in marker:
        return _translation_backend_failure_message(marker)
    return ""


def _translation_backend_failure_message(marker: str) -> str:
    if "arrearage" in marker or "overdue-payment" in marker:
        return (
            f"{NO_LLM_TRANSLATION_WARNING} Provider rejected the request: "
            "the configured LLM account appears to have overdue payment or arrears."
        )
    if "too many requests" in marker or " 429 " in marker:
        return (
            f"{NO_LLM_TRANSLATION_WARNING} Provider rejected the request: "
            "rate limit or quota was reached."
        )
    if "llm_api_key" in marker or "ai_not_configured" in marker:
        return (
            f"{NO_LLM_TRANSLATION_WARNING} Configure an LLM API key/model before translating."
        )
    return NO_LLM_TRANSLATION_WARNING


def _visible_translation_batch_size(scope: str) -> int:
    default = 12 if scope == "layout" else 12
    try:
        value = int(os.getenv("NBLANE_READER_VISIBLE_TRANSLATION_BATCH_SIZE", str(default)) or default)
    except (TypeError, ValueError):
        value = default
    return max(1, min(20, value))


def _update_or_delete_paper_annotation(
    profile_path: Path,
    source_id: str,
    payload: dict[str, Any],
    *,
    delete: bool = False,
) -> str:
    annotation_id = _payload_text(payload, "annotation_id", "id")
    if not annotation_id:
        raise ValueError("Reader annotation update needs annotation_id.")
    annotations = load_paper_annotations(profile_path, source_id)
    updated = ""
    for ann in annotations:
        if ann.id != annotation_id:
            continue
        if delete:
            ann.status = "deleted"
        else:
            selected_text = _payload_text(payload, "selected_text", "selection_text", "text", "quote")
            if selected_text:
                ann.selected_text = selected_text
                ann.selected_text_hash = _payload_text(payload, "selected_text_hash") or text_hash(selected_text)
            if "note" in payload:
                ann.note = str(payload.get("note") or "").strip()
            color = _payload_text(payload, "color")
            if color:
                ann.color = color
            locator = _payload_text(payload, "locator")
            if locator:
                ann.locator = locator
            ann.page = _payload_int(payload, "page", ann.page)
            tags = _payload_list(payload, "tags")
            if tags:
                ann.tags = tags
            segment_refs = _payload_list(payload, "segment_refs", "segment_ids", "segment_id")
            if segment_refs:
                ann.segment_refs = segment_refs
            if isinstance(payload.get("rects"), list):
                ann.rects = payload["rects"]
        ann.updated = datetime.now().astimezone().isoformat(timespec="seconds")
        updated = ann.id
        break
    if not updated:
        raise ValueError(f"Unknown paper annotation: {annotation_id}")
    save_paper_annotations(profile_path, source_id, annotations)
    return updated


def save_reader_progress(ctx: ReaderActionContext, payload: dict[str, Any]) -> ReaderActionResult:
    page = max(1, _payload_int(payload, "page", _payload_int(payload, "primary_page", 1)))
    inbox = load_research_sources(ctx.profile_path)
    src = inbox.by_id().get(ctx.source_id)
    if src is None:
        raise ValueError(f"Unknown research source: {ctx.source_id}")
    metadata = dict(src.metadata or {})
    metadata["last_read_page"] = page
    metadata["last_read_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    for key in (
        "reader_mode",
        "scale_mode",
        "active_tab",
        "target_lang",
        "focused_annotation_id",
        "focused_chunk_id",
        "active_left_tab",
        "active_translation_anchor",
    ):
        value = _payload_text(payload, key)
        if value:
            metadata[key] = value
    for key, default in (("compare_split_ratio", 50), ("panel_width", 340)):
        if key in payload:
            metadata[key] = _payload_int(payload, key, default)
    for key, default in (
        ("side_panel_collapsed", True),
        ("left_rail_collapsed", False),
        ("translation_source_visible", True),
    ):
        if key in payload:
            metadata[key] = _payload_bool(payload, key, default)
    visible_pages = clean_page_list(payload.get("visible_pages") or payload.get("last_visible_pages"))
    if visible_pages:
        metadata["last_visible_pages"] = visible_pages
    update_research_source(inbox, ctx.source_id, metadata=metadata, status="reading")
    save_research_sources(ctx.profile_path, inbox)
    return ReaderActionResult(
        data={"page": page},
        changed_ids={"source_id": ctx.source_id},
        message="Saved",
    )


def handle_reader_action(
    ctx: ReaderActionContext,
    action: str,
    payload: dict[str, Any] | None = None,
    *,
    progress_callback: Any | None = None,
) -> ReaderActionResult:
    """Run one Reader action and return a JSON-friendly result."""

    clean_action = str(action or "").strip()
    if not clean_action:
        raise ValueError("Reader action cannot be blank.")
    data = dict(payload or {})
    payload_source = _payload_text(data, "source_id")
    if payload_source and payload_source != ctx.source_id:
        raise ValueError(f"Reader action source mismatch: {payload_source}")

    git_backup.start_operation(ctx.user_id or "reader")
    result = _handle_reader_action_inner(ctx, clean_action, data, progress_callback=progress_callback)
    result.warnings.extend(_backup_warnings())
    return result


def _handle_reader_action_inner(
    ctx: ReaderActionContext,
    action: str,
    payload: dict[str, Any],
    *,
    progress_callback: Any | None = None,
) -> ReaderActionResult:
    profile = ctx.profile_path
    source_id = ctx.source_id
    segment_rows = load_paper_segments(profile, source_id)
    annotation_rows = load_paper_annotations(profile, source_id)
    chunk_rows = load_chunks(profile, source_id)

    if action == SAVE_PROGRESS:
        return save_reader_progress(ctx, payload)

    if action == PREPARE_READER_ARTIFACTS:
        prefer_grobid = payload.get("prefer_grobid", True)
        if isinstance(prefer_grobid, str):
            prefer_grobid = prefer_grobid.strip().lower() not in {"0", "false", "no", "off"}
        summary = ensure_paper_reading_artifacts(
            profile,
            source_id,
            prefer_grobid=bool(prefer_grobid),
            target_lang=_payload_text(payload, "target_lang", "language") or "zh",
            progress_callback=progress_callback,
        )
        status = str(summary.get("status") or "")
        if status == "missing_pdf":
            message = "No PDF asset is attached."
        elif status == "fallback":
            message = "Fallback text ready"
        elif status == "failed":
            message = "Preparation failed"
        else:
            message = "Structured text ready"
        return ReaderActionResult(
            ok=status not in {"missing_pdf", "failed"} or bool(summary.get("ready")),
            data={"summary": summary},
            warnings=[str(item) for item in summary.get("warnings") or []],
            message=message,
        )

    if action in {ANNOTATION_CREATE, "create_annotation"}:
        ann = create_paper_annotation(
            profile,
            source_id,
            _payload_text(payload, "selected_text", "selection_text", "text", "quote"),
            kind=_payload_text(payload, "kind") or "highlight",
            page=_payload_int(payload, "page"),
            locator=_payload_text(payload, "locator"),
            note=_payload_text(payload, "note"),
            color=_payload_text(payload, "color") or "yellow",
            tags=_payload_list(payload, "tags"),
            segment_refs=_payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
            rects=payload.get("rects") if isinstance(payload.get("rects"), list) else [],
        )
        return ReaderActionResult(
            data={"annotation": ann.to_dict()},
            changed_ids={"annotation_id": ann.id},
            message=f"Created {ann.id}",
        )

    if action == ANNOTATION_UPDATE:
        annotation_id = _update_or_delete_paper_annotation(profile, source_id, payload)
        return ReaderActionResult(changed_ids={"annotation_id": annotation_id}, message="Saved")

    if action == ANNOTATION_DELETE:
        annotation_id = _update_or_delete_paper_annotation(profile, source_id, payload, delete=True)
        return ReaderActionResult(changed_ids={"annotation_id": annotation_id}, message="Saved")

    if action in {CREATE_CHUNK_FROM_SELECTION, "create_chunk"}:
        selected_text = _selection_text(payload, segment_rows)
        chunk = create_chunk(
            profile,
            source_id,
            selected_text,
            kind=_payload_text(payload, "kind") or "excerpt",
            title=_payload_text(payload, "title"),
            locator=_payload_text(payload, "locator"),
            metadata={
                "page": _payload_int(payload, "page"),
                "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
                "segment_refs": _payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
                "annotation_id": _payload_text(payload, "annotation_id"),
                "source": "reader_sidecar",
            },
        )
        return ReaderActionResult(
            data={"chunk": chunk.to_dict()},
            changed_ids={"chunk_id": chunk.id},
            message=f"Created {chunk.id}",
        )

    if action == CREATE_CITATION:
        selected_text = _selection_text(payload, segment_rows)
        chunk_id = _payload_text(payload, "chunk_id", "chunk_ref")
        if not chunk_id and selected_text:
            chunk = create_chunk(
                profile,
                source_id,
                selected_text,
                kind="excerpt",
                locator=_payload_text(payload, "locator"),
                metadata={
                    "page": _payload_int(payload, "page"),
                    "rects": payload.get("rects") if isinstance(payload.get("rects"), list) else [],
                    "segment_refs": _payload_list(payload, "segment_refs", "segment_ids", "segment_id"),
                    "annotation_id": _payload_text(payload, "annotation_id"),
                    "source": "reader_sidecar",
                },
            )
            chunk_id = chunk.id
        claim_id = _payload_text(payload, "claim_id", "research_claim_id")
        if not claim_id:
            claim_text = _payload_text(payload, "claim_text", "text") or selected_text
            if not claim_text:
                raise ValueError("Reader citation needs a claim id, selected text, or claim text.")
            claim = upsert_research_claim(
                profile,
                claim_text,
                status="draft",
                type=_payload_text(payload, "claim_type") or "finding",
                source_refs=[source_id],
                chunk_refs=[chunk_id] if chunk_id else [],
                confidence="medium",
                rationale="Created from Reader selection; review before promotion.",
                generated_by="reader_sidecar",
            )
            claim_id = claim.id
        citation = create_citation(
            profile,
            claim_id,
            source_id=source_id,
            chunk_id=chunk_id,
            locator=_payload_text(payload, "locator"),
            quote=_payload_text(payload, "quote", "selected_text", "selection_text", "text"),
            bibliography=_payload_text(payload, "bibliography"),
            note=_payload_text(payload, "note"),
        )
        return ReaderActionResult(
            data={"citation": citation.to_dict()},
            changed_ids={"citation_id": citation.id, "claim_id": claim_id, "chunk_id": chunk_id},
            message=f"Created {citation.id}",
        )

    if action == TRANSLATE_FULL_PAPER:
        summary = translate_full_paper(
            profile,
            source_id,
            target_lang=_payload_text(payload, "target_lang", "language") or "zh",
            mode=_payload_text(payload, "mode") or "missing_or_stale",
            scope_strategy=_payload_text(payload, "scope_strategy") or "segment",
            ai_profile=ctx.profile_name,
            require_review=False,
            progress_callback=progress_callback,
        )
        return ReaderActionResult(
            data={"summary": summary},
            message=f"Full-paper translation updated: {summary.get('updated', 0)} row(s).",
        )

    if action in {TRANSLATE_VISIBLE_PAGES, RETRY_TRANSLATION_SCOPE}:
        target_lang = _payload_text(payload, "target_lang", "language") or "zh"
        scope_strategy = _payload_text(payload, "scope_strategy") or "auto"
        if scope_strategy not in {"auto", "segment", "page", "layout", "structure"}:
            scope_strategy = "auto"
        refs = set(_payload_list(payload, "segment_refs", "segment_ids", "segment_id"))
        scope_refs = set(_payload_list(payload, "scope_refs", "scope_ref"))
        visible_pages = {
            int(item)
            for item in payload.get("visible_pages", [])
            if str(item).strip().isdigit()
        } if isinstance(payload.get("visible_pages"), list) else set()
        primary_page = _payload_int(payload, "primary_page", _payload_int(payload, "page", 0))
        if not visible_pages and primary_page:
            visible_pages = {primary_page}
        requested_pages = sorted(visible_pages)
        current_translations = load_paper_translations(profile, source_id)
        def emit_translation_progress(phase: str, label: str, *, current: int = 0, total: int = 0, saved_count: int = 0) -> None:
            if progress_callback is None:
                return
            try:
                progress_callback(
                    {
                        "phase": phase,
                        "label": label,
                        "current": current,
                        "total": total,
                        "saved": saved_count,
                        "segments_selected": total,
                        "requested_pages": requested_pages,
                        "target_lang": target_lang,
                        "scope": scope_strategy,
                    }
                )
            except Exception:
                return

        positioned_scope_rows: dict[str, dict[str, Any]] = {}
        positioned_scope_type = ""
        if visible_pages and scope_strategy in {"structure", "auto"} and (not refs or scope_refs):
            emit_translation_progress("extracting_structure", "Building paper structure...")
            structure_units = [
                unit
                for unit in reader_translation_structure_units(build_paper_structure_units(profile, source_id))
                if bool(unit.get("translatable", True))
                and (
                    int(unit.get("page") or 0) in visible_pages
                    or int(unit.get("page_end") or unit.get("page") or 0) in visible_pages
                )
            ]
            existing_structure_by_scope = {
                row.scope_ref: row
                for row in current_translations
                if row.scope_type == "structure" and row.target_lang == target_lang
            }
            for unit in structure_units:
                payload_row = _layout_translation_payload(unit, source_id)
                scope_ref = _payload_text(payload_row, "scope_ref", "segment_id")
                if not scope_ref or not _payload_text(payload_row, "text", "source_text"):
                    continue
                if scope_refs and scope_ref not in scope_refs:
                    continue
                if not scope_refs and _translation_row_current(existing_structure_by_scope.get(scope_ref), _payload_text(payload_row, "source_hash"), target_lang):
                    continue
                positioned_scope_rows[scope_ref] = payload_row
            if positioned_scope_rows:
                positioned_scope_type = "structure"
        if (
            visible_pages
            and not positioned_scope_rows
            and scope_strategy in {"layout", "auto"}
            and (not refs or scope_refs)
        ):
            emit_translation_progress("extracting_layout", "Extracting page layout...")
            layout_units = [
                unit
                for unit in reader_translation_layout_units(build_paper_layout_units(profile, source_id, pages=visible_pages))
                if bool(unit.get("translatable", True))
            ]
            existing_layout_by_scope = {
                row.scope_ref: row
                for row in current_translations
                if row.scope_type == "layout" and row.target_lang == target_lang
            }
            for unit in layout_units:
                payload_row = _layout_translation_payload(unit, source_id)
                scope_ref = _payload_text(payload_row, "scope_ref", "segment_id")
                if not scope_ref or not _payload_text(payload_row, "text", "source_text"):
                    continue
                if scope_refs and scope_ref not in scope_refs:
                    continue
                if not scope_refs and _translation_row_current(existing_layout_by_scope.get(scope_ref), _payload_text(payload_row, "source_hash"), target_lang):
                    continue
                positioned_scope_rows[scope_ref] = payload_row
            if positioned_scope_rows:
                positioned_scope_type = "layout"
        segments = [
            segment
            for segment in segment_rows
            if (refs and segment.segment_id in refs)
            or (visible_pages and segment.page in visible_pages)
        ]
        segment_payloads = list(positioned_scope_rows.values()) if positioned_scope_rows else [segment.to_dict() for segment in segments]
        page_scope_rows: dict[str, dict[str, Any]] = {}
        use_page_scope = bool(visible_pages) and not positioned_scope_rows and (
            scope_strategy == "page"
            or (
                scope_strategy == "auto"
                and not refs
                and not scope_refs
                and (not segment_payloads or not any(segment.page > 0 for segment in segments))
            )
        )
        if use_page_scope:
            segment_payloads = []
            for page in load_paper_pages(profile, source_id):
                if page.page not in visible_pages or not str(page.text or "").strip():
                    continue
                page_hash = page.text_hash or text_hash(page.text)
                synthetic_id = f"page:{page.page}"
                page_scope_rows[synthetic_id] = {
                    "segment_id": synthetic_id,
                    "source_id": source_id,
                    "scope_type": "page",
                    "scope_ref": f"page:{page.page}:{page_hash}",
                    "page": page.page,
                    "order": 0,
                    "section_path": [],
                    "kind": "page",
                    "text": page.text,
                    "text_hash": page_hash,
                    "locator": f"p. {page.page}",
                }
            segment_payloads = list(page_scope_rows.values())
        if not segment_payloads:
            summary = _visible_translation_summary(
                scope="page" if visible_pages else "segment",
                requested_pages=requested_pages,
                segments_selected=0,
                ai_rows=0,
                saved=0,
                failed=0,
                skipped=0,
                target_lang=target_lang,
            )
            return ReaderActionResult(
                ok=False,
                data={"summary": summary},
                message="No extracted text is available for the visible page yet.",
            )
        batch_scope = positioned_scope_type if positioned_scope_rows else "page" if page_scope_rows else "segment"
        batch_size = _visible_translation_batch_size(batch_scope)
        batches = [
            segment_payloads[index : index + batch_size]
            for index in range(0, len(segment_payloads), batch_size)
        ]
        translations: list[dict[str, Any]] = []
        warnings: list[str] = []
        combined_structured: dict[str, Any] = {"translations": [], "warnings": []}
        positioned_backend_warning = ""
        translation_backend_warning = ""
        processed = 0
        for batch_index, batch in enumerate(batches, start=1):
            emit_translation_progress(
                "translating",
                f"Translating visible pages... {processed}/{len(segment_payloads)}",
                current=processed,
                total=len(segment_payloads),
            )
            ai_result = translate_paper_segments(
                ctx.profile_name,
                source_id,
                batch,
                target_lang=target_lang,
                require_review=False,
            )
            batch_warnings = [str(item) for item in ai_result.warnings]
            warnings.extend(batch_warnings)
            if getattr(ai_result, "error", ""):
                warnings.append(str(ai_result.error))
            batch_rows: list[dict[str, Any]] = []
            structured = ai_result.structured if isinstance(ai_result.structured, dict) else {}
            for raw in structured.get("translations") or []:
                if not isinstance(raw, dict):
                    continue
                row = normalize_translation_row(raw, source_id=source_id, target_lang=target_lang)
                batch_rows.append(row)
            translations.extend(batch_rows)
            combined_structured["translations"].extend(batch_rows)
            if batch_warnings:
                combined_structured["warnings"].extend(batch_warnings)
            warning = _blank_translation_backend_warning(ai_result, batch_rows)
            if warning:
                translation_backend_warning = warning
                if positioned_scope_rows:
                    positioned_backend_warning = warning
            processed += len(batch)
            emit_translation_progress(
                "translating",
                f"Translating visible pages... {processed}/{len(segment_payloads)}",
                current=processed,
                total=len(segment_payloads),
            )
        emit_translation_progress(
            "saving",
            "Saving translations...",
            current=len(segment_payloads),
            total=len(segment_payloads),
        )
        savable: list[dict[str, Any]] = []
        saved = 0
        failed = 0
        skipped = 0
        if positioned_scope_rows:
            scope = positioned_scope_type or "layout"
            backend_warning = positioned_backend_warning
            if backend_warning and backend_warning not in warnings:
                warnings.append(backend_warning)
        else:
            backend_warning = translation_backend_warning
            if backend_warning and backend_warning not in warnings:
                warnings.append(backend_warning)
        if positioned_scope_rows:
            scope = positioned_scope_type or "layout"
            positioned_index: dict[str, dict[str, Any]] = {}
            for positioned_row in positioned_scope_rows.values():
                positioned_index[str(positioned_row["segment_id"])] = positioned_row
                positioned_index[str(positioned_row["scope_ref"])] = positioned_row
            for row in translations:
                row_ref = str(row.get("segment_id") or row.get("scope_ref") or "")
                if not row_ref:
                    warnings.append("Skipped translation row without segment_id or scope_ref.")
                    skipped += 1
                    continue
                positioned_row = positioned_index.get(row_ref)
                if positioned_row is None:
                    warnings.append(f"Skipped translation row for unknown {scope} scope: {row_ref}.")
                    skipped += 1
                    continue
                source_hash = str(row.get("source_hash") or row.get("text_hash") or row.get("source_text_hash") or "").strip()
                if source_hash != positioned_row["source_hash"]:
                    warnings.append(f"Skipped translation for {row_ref}: source_hash mismatch.")
                    skipped += 1
                    continue
                translated_text = translation_text_from_row(row)
                if not translated_text:
                    if not backend_warning:
                        warnings.append(f"Skipped translation for {row_ref}: translated_text is blank.")
                    skipped += 1
                    continue
                savable.append(
                    {
                        **row,
                        "scope_type": scope,
                        "scope_ref": positioned_row["scope_ref"],
                        "segment_id": "",
                        "page": positioned_row["page"],
                        "order": positioned_row["order"],
                        "locator": positioned_row["locator"],
                        "source_hash": positioned_row["source_hash"],
                        "source_text": positioned_row["source_text"],
                        "target_lang": target_lang,
                        "translated_text": translated_text,
                        "rects": positioned_row.get("rects", []),
                    }
                )
                saved += 1
        elif page_scope_rows:
            scope = "page"
            page_index: dict[str, dict[str, Any]] = {}
            for page_row in page_scope_rows.values():
                page_index[str(page_row["segment_id"])] = page_row
                page_index[str(page_row["scope_ref"])] = page_row
            existing_by_scope = {
                row.scope_ref: row
                for row in current_translations
                if row.scope_type == "page" and row.target_lang == target_lang
            }
            for row in translations:
                row_ref = str(row.get("segment_id") or row.get("scope_ref") or "")
                if not row_ref:
                    warnings.append("Skipped translation row without segment_id or scope_ref.")
                    skipped += 1
                    continue
                page_row = page_index.get(row_ref)
                if page_row is None:
                    warnings.append(f"Skipped translation row for unknown page scope: {row_ref}.")
                    skipped += 1
                    continue
                source_hash = str(row.get("source_hash") or row.get("text_hash") or row.get("source_text_hash") or "").strip()
                if source_hash != page_row["text_hash"]:
                    warnings.append(f"Skipped translation for {row_ref}: source_hash mismatch.")
                    skipped += 1
                    continue
                translated_text = translation_text_from_row(row)
                if not translated_text:
                    if backend_warning:
                        skipped += 1
                        continue
                    warnings.append(f"Skipped translation for {row_ref}: translated_text is blank.")
                    existing = existing_by_scope.get(str(page_row["scope_ref"]))
                    if not _translation_row_current(existing, str(page_row["text_hash"]), target_lang):
                        savable.append(
                            {
                                **row,
                                "scope_type": "page",
                                "scope_ref": page_row["scope_ref"],
                                "segment_id": "",
                                "page": page_row["page"],
                                "source_hash": page_row["text_hash"],
                                "source_text": page_row["text"],
                                "target_lang": target_lang,
                                "translated_text": "",
                                "status": "failed",
                                "warnings": _payload_list(row, "warnings") + ["translated_text is blank."],
                            }
                        )
                        failed += 1
                    else:
                        skipped += 1
                    continue
                savable.append(
                    {
                        **row,
                        "scope_type": "page",
                        "scope_ref": page_row["scope_ref"],
                        "segment_id": "",
                        "page": page_row["page"],
                        "source_hash": page_row["text_hash"],
                        "source_text": page_row["text"],
                        "target_lang": target_lang,
                        "translated_text": translated_text,
                    }
                )
                saved += 1
        else:
            scope = "segment"
            segment_ids = {segment.segment_id for segment in segments}
            segment_by_id = {segment.segment_id: segment for segment in segments}
            existing_by_segment = {
                row.segment_id: row
                for row in current_translations
                if row.segment_id and row.target_lang == target_lang
            }
            for row in translations:
                row_ref = str(row.get("segment_id") or row.get("scope_ref") or "")
                if not row_ref:
                    warnings.append("Skipped translation row without segment_id or scope_ref.")
                    skipped += 1
                    continue
                if row_ref not in segment_ids:
                    warnings.append(f"Skipped translation row for unknown segment: {row_ref}.")
                    skipped += 1
                    continue
                segment = segment_by_id[row_ref]
                source_hash = str(row.get("source_hash") or row.get("text_hash") or row.get("source_text_hash") or "").strip()
                if source_hash != segment.text_hash:
                    warnings.append(f"Skipped translation for {row_ref}: source_hash mismatch.")
                    skipped += 1
                    continue
                translated_text = translation_text_from_row(row)
                if not translated_text:
                    if backend_warning:
                        skipped += 1
                        continue
                    warnings.append(f"Skipped translation for {row_ref}: translated_text is blank.")
                    existing = existing_by_segment.get(row_ref)
                    if not _translation_row_current(existing, segment.text_hash, target_lang):
                        savable.append(
                            {
                                **row,
                                "source_id": source_id,
                                "scope_type": "segment",
                                "scope_ref": segment.segment_id,
                                "segment_id": segment.segment_id,
                                "page": segment.page,
                                "source_hash": segment.text_hash,
                                "source_text": segment.text,
                                "target_lang": target_lang,
                                "translated_text": "",
                                "status": "failed",
                                "warnings": _payload_list(row, "warnings") + ["translated_text is blank."],
                            }
                        )
                        failed += 1
                    else:
                        skipped += 1
                    continue
                savable.append(
                    {
                        **row,
                        "source_id": source_id,
                        "scope_type": "segment",
                        "scope_ref": segment.segment_id,
                        "segment_id": segment.segment_id,
                        "page": segment.page,
                        "source_hash": segment.text_hash,
                        "source_text": segment.text,
                        "target_lang": target_lang,
                        "translated_text": translated_text,
                    }
                )
                saved += 1
        if savable:
            upsert_paper_translations(profile, source_id, savable)
        summary = _visible_translation_summary(
            scope=scope,
            requested_pages=requested_pages,
            segments_selected=len(segment_payloads),
            ai_rows=len(translations),
            saved=saved,
            failed=failed,
            skipped=skipped,
            target_lang=target_lang,
        )
        emit_translation_progress(
            "done",
            "Visible-page translation finished.",
            current=len(segment_payloads),
            total=len(segment_payloads),
            saved_count=saved,
        )
        no_backend_text = bool(translation_backend_warning and not saved)
        if saved:
            message = f"Saved {saved} translation row(s)."
        elif failed:
            message = f"Saved {failed} failed translation row(s)."
        elif no_backend_text:
            message = translation_backend_warning
        else:
            message = "No translation rows were saved."
        return ReaderActionResult(
            data={
                "structured": combined_structured,
                "translations": savable,
                "summary": summary,
                "saved": saved,
            },
            warnings=warnings,
            message=message,
        )

    if action in {TRANSLATE_SELECTION, "translate_segment"}:
        selected_text = _selection_text(payload, segment_rows)
        target_lang = _payload_text(payload, "target_lang", "language") or "zh"
        translation_payload = dict(payload)
        if action == TRANSLATE_SELECTION and selected_text:
            for key in ("segment_refs", "segment_ids", "segment_id", "scope_refs", "scope_ref"):
                translation_payload.pop(key, None)
        segment_refs = set(_payload_list(translation_payload, "segment_refs", "segment_ids", "segment_id"))
        segments = _selection_segments(translation_payload, segment_rows)
        if not segments:
            raise ValueError("Reader translation needs selected text or segment refs.")
        ai_result = translate_paper_segments(
            ctx.profile_name,
            source_id,
            segments,
            target_lang=target_lang,
            require_review=False,
        )
        translations = []
        if isinstance(ai_result.structured, dict):
            translations = [
                normalize_translation_row(row, source_id=source_id, target_lang=target_lang)
                for row in ai_result.structured.get("translations", [])
                if isinstance(row, dict)
            ]
        backend_warning = _blank_translation_backend_warning(ai_result, translations)
        if segment_refs:
            segment_ids = {segment.segment_id for segment in segment_rows}
            savable = [
                {
                    **row,
                    "scope_type": "segment",
                    "scope_ref": str(row.get("segment_id") or row.get("scope_ref") or ""),
                }
                for row in translations
                if str(row.get("segment_id") or row.get("scope_ref") or "") in segment_ids
            ]
        else:
            selected_hash = _payload_text(payload, "selected_text_hash", "text_hash", "source_hash")
            if not selected_hash and selected_text:
                selected_hash = text_hash(selected_text)
            synthetic_ids = {
                str(segment.get("segment_id") or "")
                for segment in segments
                if isinstance(segment, dict)
            }
            savable = []
            for row in translations:
                row_ref = str(row.get("segment_id") or row.get("scope_ref") or "")
                if synthetic_ids and row_ref and row_ref not in synthetic_ids:
                    continue
                savable.append(
                    {
                        **row,
                        "scope_type": "selection",
                        "scope_ref": selected_hash,
                        "segment_id": "",
                        "source_hash": selected_hash,
                        "source_text": selected_text,
                        "target_lang": target_lang,
                    }
                )
        translation_text = next(
            (translation_text_from_row(row) for row in savable if translation_text_from_row(row)),
            "",
        )
        no_backend_text = bool(backend_warning and not translation_text)
        warnings = list(ai_result.warnings)
        if backend_warning and backend_warning not in warnings:
            warnings.append(backend_warning)
        if savable and not no_backend_text:
            upsert_paper_translations(profile, source_id, savable)
        return ReaderActionResult(
            data={
                "structured": ai_result.structured or {},
                "translations": [] if no_backend_text else savable,
                "translation_text": translation_text,
                "saved": 0 if no_backend_text else len(savable),
            },
            warnings=warnings,
            message=backend_warning if no_backend_text else "Saved" if savable else "",
        )

    if action == EXPLAIN_SELECTION:
        selected_text = _selection_text(payload, segment_rows)
        if not selected_text:
            raise ValueError("Reader explanation needs selected text or segment refs.")
        ai_result = explain_paper_selection(
            ctx.profile_name,
            source_id,
            selected_text,
            payload={
                "page": _payload_int(payload, "page"),
                "locator": _payload_text(payload, "locator"),
                "segments": _context_segments(payload, segment_rows, limit=8),
                "annotations": [row.to_dict() for row in annotation_rows[:20]],
            },
        )
        return ReaderActionResult(
            data={"structured": ai_result.structured or {}},
            warnings=list(ai_result.warnings),
        )

    if action == ASK_PAPER:
        question = _payload_text(payload, "question", "prompt", "text")
        if not question:
            raise ValueError("Reader question cannot be blank.")
        qa_segments = _question_context_segments(payload, segment_rows)
        has_selection_scope = bool(_selection_segments(payload, segment_rows))
        source = load_research_sources(profile).by_id().get(source_id)
        ai_result = answer_paper_question(
            ctx.profile_name,
            source_id,
            question,
            payload={
                "source": _compact_source_for_deep_read(source, source_id),
                "segments": qa_segments,
                "annotations": [row.to_dict() for row in annotation_rows[:30]],
                "chunks": [row.to_dict() for row in chunk_rows[:30]],
                "scope": "selection" if has_selection_scope else "paper",
                "full_paper": not has_selection_scope,
                "paper_context": {
                    "source_segments": len(segment_rows),
                    "supplied_segments": len(qa_segments),
                    "pages_covered": sorted(
                        {
                            int(row.get("page") or 0)
                            for row in qa_segments
                            if int(row.get("page") or 0) > 0
                        }
                    ),
                },
            },
        )
        return ReaderActionResult(
            data={"structured": ai_result.structured or {}},
            warnings=list(ai_result.warnings),
        )

    if action == ANALYZE_PAPER:
        def emit_analysis_progress(phase: str, label: str, *, current: int = 0, total: int = 5) -> None:
            if progress_callback is None:
                return
            try:
                progress_callback({"phase": phase, "label": label, "current": current, "total": total})
            except Exception:
                pass

        emit_analysis_progress("preparing", "Preparing reader artifacts...", current=0, total=5)
        artifact_summary = ensure_paper_reading_artifacts(
            profile,
            source_id,
            prefer_grobid=True,
            target_lang=_payload_text(payload, "target_lang", "language") or "zh",
            progress_callback=progress_callback,
        )
        segment_rows = load_paper_segments(profile, source_id)
        artifact_warnings = [str(item) for item in artifact_summary.get("warnings") or []]
        source = load_research_sources(profile).by_id().get(source_id)
        emit_analysis_progress(
            "summarizing",
            f"Reading {len(segment_rows)} segments…",
            current=1,
            total=5,
        )
        emit_analysis_progress(
            "scoring",
            "Asking model for TL;DR, key points, scores…",
            current=2,
            total=5,
        )
        ai_result = generate_paper_review_card(
            ctx.profile_name,
            source_id,
            source=source.to_dict() if source is not None else {"id": source_id},
            segments=[row.to_dict() for row in segment_rows],
            chunks=[row.to_dict() for row in chunk_rows],
            annotations=[row.to_dict() for row in annotation_rows],
            require_review=False,
        )
        emit_analysis_progress("normalizing", "Normalizing analysis output…", current=3, total=5)
        structured = ai_result.structured if isinstance(ai_result.structured, dict) else {}
        analysis = _normalize_paper_analysis(structured, source_id) if structured else _normalize_paper_analysis({}, source_id)
        if structured:
            emit_analysis_progress("saving", "Saving analysis…", current=4, total=5)
            save_paper_analysis(profile, source_id, analysis)
        emit_analysis_progress("done", "Analysis saved" if structured else "Analysis incomplete", current=5, total=5)
        message = "Analysis saved" if structured else (getattr(ai_result, "error", "") or "Analysis did not return structured output.")
        return ReaderActionResult(
            ok=bool(getattr(ai_result, "ok", True) and structured),
            data={
                "structured": analysis,
                "analysis": load_paper_analysis(profile, source_id),
                "artifact_summary": artifact_summary,
            },
            warnings=artifact_warnings + list(ai_result.warnings) + list(analysis.get("warnings") or []),
            message=message,
        )

    if action == "codex_deep_read":
        def emit_deepread_progress(phase: str, label: str, *, current: int = 0, total: int = 5) -> None:
            if progress_callback is None:
                return
            try:
                progress_callback({"phase": phase, "label": label, "current": current, "total": total})
            except Exception:
                pass

        emit_deepread_progress("preparing", "Preparing reader artifacts...", current=0, total=5)
        artifact_summary = ensure_paper_reading_artifacts(
            profile,
            source_id,
            prefer_grobid=True,
            target_lang=_payload_text(payload, "target_lang", "language") or "zh",
            progress_callback=progress_callback,
        )
        segment_rows = load_paper_segments(profile, source_id)
        artifact_warnings = [str(item) for item in artifact_summary.get("warnings") or []]
        source = load_research_sources(profile).by_id().get(source_id)
        compact_segments = _compact_segments_for_deep_read(payload, segment_rows)
        full_paper_scope = _payload_bool(payload, "full_paper", True) or (_payload_text(payload, "scope") or "paper") == "paper"
        emit_deepread_progress(
            "compacting",
            f"Compacting {len(compact_segments)} segments for deep read…",
            current=1,
            total=5,
        )
        emit_deepread_progress(
            "reading",
            "Codex is reading the paper end-to-end…",
            current=2,
            total=5,
        )
        total_pages = max([int(getattr(row, "page", 0) or 0) for row in segment_rows] + [0])
        deep_read_payload = {
            "source": _compact_source_for_deep_read(source, source_id),
            "segments": compact_segments,
            "chunks": _compact_chunks_for_deep_read(chunk_rows),
            "annotations": _compact_annotations_for_deep_read(annotation_rows),
            "question": _payload_text(payload, "question", "prompt", "text"),
            "reading_goal": _payload_text(payload, "reading_goal", "goal"),
            "scope": _payload_text(payload, "scope") or "paper",
            "full_paper": _payload_bool(payload, "full_paper", True),
            "paper_context": {
                "source_segments": len(segment_rows),
                "supplied_segments": len(compact_segments),
                "segment_budget": {"segments": 80, "chars": 60_000}
                if full_paper_scope
                else {"segments": 40, "chars": 24_000},
                "truncated": bool(full_paper_scope and len(compact_segments) < len(segment_rows)),
                "sections_covered": _deep_read_sections_covered(compact_segments),
                "pages_covered": _deep_read_payload_pages(compact_segments),
            },
            "page": _payload_int(payload, "page"),
            "visible_pages": payload.get("visible_pages")
            if isinstance(payload.get("visible_pages"), list)
            else [],
            "locator": _payload_text(payload, "locator"),
        }
        _copy_deep_read_runtime_options(payload, deep_read_payload)
        explicit_codex_timeout = _explicit_codex_timeout(payload)
        if not explicit_codex_timeout:
            deep_read_payload["codex_timeout_seconds"] = _adaptive_deep_read_timeout_seconds(
                source_segments=len(segment_rows),
                supplied_segments=len(compact_segments),
                pages=total_pages,
            )

        if "batch_deep_read" in payload:
            use_batched_deep_read = _payload_bool(payload, "batch_deep_read", False)
        elif "batched_deep_read" in payload:
            use_batched_deep_read = _payload_bool(payload, "batched_deep_read", False)
        else:
            use_batched_deep_read = bool(full_paper_scope and len(segment_rows) > 110)
        use_batched_deep_read = use_batched_deep_read and full_paper_scope

        ai_result = None
        batch_reports: list[dict[str, Any]] = []
        deepread_warnings: list[str] = []
        if use_batched_deep_read:
            section_batches = _deep_read_section_batches(segment_rows)
            if len(section_batches) >= 2:
                batch_total = len(section_batches)
                for batch_index, batch in enumerate(section_batches, start=1):
                    batch_segments = batch.get("segments") if isinstance(batch.get("segments"), list) else []
                    batch_label = _payload_text(batch, "label") or f"batch {batch_index}"
                    emit_deepread_progress(
                        "reading_batch",
                        f"Deep reading section batch {batch_index}/{batch_total}: {batch_label}",
                        current=batch_index,
                        total=batch_total + 2,
                    )
                    batch_payload = {
                        "source": _compact_source_for_deep_read(source, source_id),
                        "segments": batch_segments,
                        "chunks": [],
                        "annotations": _compact_annotations_for_deep_read(annotation_rows, limit=8),
                        "question": _payload_text(payload, "question", "prompt", "text"),
                        "reading_goal": (
                            _payload_text(payload, "reading_goal", "goal")
                            or "先生成本章节/批次的可引用深读笔记，稍后统一综合。"
                        ),
                        "scope": "section_batch",
                        "full_paper": False,
                        "paper_context": {
                            "mode": "section_batch",
                            "batch_label": batch_label,
                            "batch_index": batch_index,
                            "batch_count": batch_total,
                            "source_segments": len(segment_rows),
                            "batch_source_segments": int(batch.get("source_segments") or len(batch_segments)),
                            "supplied_segments": len(batch_segments),
                            "segment_budget": {"segments": 24, "chars": 18_000},
                            "truncated": int(batch.get("source_segments") or 0) > len(batch_segments),
                            "sections_covered": list(batch.get("sections_covered") or []),
                            "pages_covered": list(batch.get("pages_covered") or []),
                        },
                    }
                    _copy_deep_read_runtime_options(payload, batch_payload)
                    if not explicit_codex_timeout:
                        batch_payload["codex_timeout_seconds"] = _adaptive_deep_read_timeout_seconds(
                            source_segments=int(batch.get("source_segments") or len(batch_segments)),
                            supplied_segments=len(batch_segments),
                            pages=len(batch.get("pages_covered") or []),
                            mode="batch",
                        )
                    batch_result = deep_read_paper_codex(
                        ctx.profile_name,
                        source_id,
                        payload=batch_payload,
                        require_review=True,
                    )
                    batch_structured = batch_result.structured if isinstance(batch_result.structured, dict) else {}
                    deepread_warnings.extend(str(item) for item in getattr(batch_result, "warnings", []) or [])
                    deepread_warnings.extend(str(item) for item in batch_structured.get("warnings") or [])
                    if batch_result.ok and batch_structured:
                        batch_structured = dict(batch_structured)
                        batch_structured["batch_label"] = batch_label
                        batch_structured["batch_index"] = batch_index
                        batch_structured["batch_count"] = batch_total
                        batch_reports.append(batch_structured)
                    else:
                        error = getattr(batch_result, "error", "") or "section batch returned no structured output"
                        deepread_warnings.append(f"Deep-read batch {batch_index}/{batch_total} failed: {error}")

            if batch_reports:
                emit_deepread_progress(
                    "synthesizing",
                    f"Synthesizing {len(batch_reports)} section deep reads…",
                    current=len(batch_reports) + 1,
                    total=len(batch_reports) + 2,
                )
                synthesis_payload = dict(deep_read_payload)
                synthesis_payload["chunks"] = _compact_chunks_for_deep_read(chunk_rows) + _deep_read_batch_chunks(batch_reports)
                synthesis_payload["batch_reports"] = batch_reports
                synthesis_payload["reading_goal"] = (
                    _payload_text(payload, "reading_goal", "goal")
                    or "把分章节/分批深读笔记综合成一份 Moonlight-style 完整阅读报告。"
                )
                synthesis_payload["paper_context"] = {
                    **dict(deep_read_payload.get("paper_context") or {}),
                    "mode": "synthesis",
                    "batch_count": len(batch_reports),
                    "batch_labels": [_payload_text(row, "batch_label") for row in batch_reports],
                    "batch_reading": True,
                }
                if not explicit_codex_timeout:
                    synthesis_payload["codex_timeout_seconds"] = _adaptive_deep_read_timeout_seconds(
                        source_segments=len(segment_rows),
                        supplied_segments=len(compact_segments),
                        pages=total_pages,
                        mode="synthesis",
                        batch_count=len(batch_reports),
                    )
                ai_result = deep_read_paper_codex(
                    ctx.profile_name,
                    source_id,
                    payload=synthesis_payload,
                    require_review=True,
                )

        if ai_result is None:
            ai_result = deep_read_paper_codex(
                ctx.profile_name,
                source_id,
                payload=deep_read_payload,
                require_review=True,
            )
        emit_deepread_progress("structuring", "Structuring findings + reading plan…", current=3, total=5)
        structured = ai_result.structured if isinstance(ai_result.structured, dict) else {}
        if structured and batch_reports:
            structured = dict(structured)
            structured["batch_reading"] = {
                "enabled": True,
                "batch_count": len(batch_reports),
                "batch_labels": [_payload_text(row, "batch_label") for row in batch_reports],
            }
            existing_warnings = [str(item) for item in structured.get("warnings") or []]
            for warning in deepread_warnings:
                if warning and warning not in existing_warnings:
                    existing_warnings.append(warning)
            structured["warnings"] = existing_warnings
        if ai_result.ok and structured:
            emit_deepread_progress("saving", "Saving deep-read result…", current=4, total=5)
            analysis = load_paper_analysis(profile, source_id)
            analysis["codex_deep_read"] = structured
            analysis["codex_deep_read_updated"] = datetime.now().astimezone().isoformat(
                timespec="seconds"
            )
            save_paper_analysis(profile, source_id, analysis)
        emit_deepread_progress(
            "done",
            "Deep read candidate ready" if (ai_result.ok and structured) else "Deep read incomplete",
            current=5,
            total=5,
        )
        message = (
            "Deep read candidate ready."
            if ai_result.ok and structured
            else ai_result.error or "Deep read did not return a candidate."
        )
        return ReaderActionResult(
            ok=bool(ai_result.ok and structured),
            data={
                "structured": structured,
                "analysis": load_paper_analysis(profile, source_id),
                "artifact_summary": artifact_summary,
            },
            warnings=artifact_warnings + deepread_warnings + list(ai_result.warnings),
            message=message,
        )

    if action == "generate_review_card":
        artifact_summary = ensure_paper_reading_artifacts(
            profile,
            source_id,
            prefer_grobid=True,
            target_lang=_payload_text(payload, "target_lang", "language") or "zh",
            progress_callback=progress_callback,
        )
        segment_rows = load_paper_segments(profile, source_id)
        artifact_warnings = [str(item) for item in artifact_summary.get("warnings") or []]
        source = load_research_sources(profile).by_id().get(source_id)
        ai_result = generate_paper_review_card(
            ctx.profile_name,
            source_id,
            source=source.to_dict() if source is not None else {"id": source_id},
            segments=[row.to_dict() for row in segment_rows],
            chunks=[row.to_dict() for row in chunk_rows],
            annotations=[row.to_dict() for row in annotation_rows],
            require_review=False,
        )
        structured = ai_result.structured if isinstance(ai_result.structured, dict) else {}
        analysis = _normalize_paper_analysis(structured, source_id) if structured else _normalize_paper_analysis({}, source_id)
        if structured:
            save_paper_analysis(profile, source_id, analysis)
        return ReaderActionResult(
            ok=bool(getattr(ai_result, "ok", True) and structured),
            data={
                "structured": analysis,
                "analysis": load_paper_analysis(profile, source_id),
                "artifact_summary": artifact_summary,
            },
            warnings=artifact_warnings + list(ai_result.warnings) + list(analysis.get("warnings") or []),
            message="Saved" if structured else "",
        )

    if action == "request_page_previews":
        pages = clean_page_list(payload.get("pages") or payload.get("visible_pages"))
        return ReaderActionResult(data={"pages": pages})

    if action in {"selection_created", "page_changed", "viewport_changed", "reader_state_changed", "request_reader_context"}:
        return ReaderActionResult(data={"ignored": True})

    raise ValueError(f"Unsupported reader action: {action}")
