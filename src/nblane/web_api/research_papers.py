"""Single-paper overview + analysis jobs for the SPA paper overview page.

The paper overview (``docs/zh/product/paper_reading.md`` §1.1.2) is the
landing page of one paper: metadata, abstract (+ its translation when the
canonical structure already has one), PDF/extraction state, reading and
translation progress, recent notes, the quick-analysis card and the deep
study (深度研读) report. The Reader stays on the sidecar; this module only
reads the same profile files through the core loaders.

Endpoints:

- ``GET  /profiles/{name}/research/papers/{source_id}`` — overview payload.
  Analysis refs (segment / structure-unit / chunk / annotation ids) are
  resolved to page numbers server-side so the SPA can link each chip to
  ``/read?page=N``.
- ``POST /profiles/{name}/research/papers/{source_id}/analysis-jobs`` —
  start (or re-attach to) a ``paper-quick-analysis`` / ``paper-deep-read``
  job; progress streams over the shared job SSE endpoint.

Job kinds run the exact Reader actions (``analyze_paper`` /
``codex_deep_read`` via ``core.reader_actions.handle_reader_action``), which
route through the AI gateway — no provider SDK is touched here. Before the
call the runner checks that the configured backend is usable (LLM key for
quick analysis, Codex CLI for deep study) so a missing backend surfaces as a
clear, retryable error instead of a silent deterministic fallback.

Claim / Evidence data is deliberately not exposed: paper reading produces
reading material only.
"""

from __future__ import annotations

import ast
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import Depends
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from nblane.core import codex_adapter, profile_io
from nblane.core.file_write import atomic_write_text
from nblane.core import llm as llm_client
from nblane.core.reader_actions import (
    ANALYSIS_FALLBACK_KEPT_WARNING,
    ReaderActionContext,
    handle_reader_action,
)
from nblane.core.research_papers import (
    build_translation_units,
    load_paper_analysis,
    load_paper_annotations,
    load_paper_segments,
    load_paper_structure_units,
    load_paper_translations,
    paper_pdf_asset_path,
    reader_translation_structure_units,
)
from nblane.core.research_papers._paths import _yaml_path
from nblane.core.research_papers._constants import PAPER_ANALYSIS_DIRNAME
from nblane.core.research_sources import ResearchSource, load_research_sources
from nblane.core.research_workspace import load_chunks
from nblane.core.web_preferences import AI_ACTION_DEFAULT_BACKENDS, load_web_preferences
from nblane.web_api import jobs
from nblane.web_api.auth import CurrentUser
from nblane.web_api.routes_v1 import (
    ERROR_RESPONSES,
    ApiError,
    _resolve_profile,
    require_profile_access,
)
from nblane.web_api.schemas import JobCreateResponse, JobModel

router = APIRouter(prefix="/api/v1")

KIND_PAPER_QUICK_ANALYSIS = "paper-quick-analysis"
KIND_PAPER_DEEP_READ = "paper-deep-read"
PAPER_JOB_KINDS = (KIND_PAPER_QUICK_ANALYSIS, KIND_PAPER_DEEP_READ)

_READER_ACTIONS = {
    KIND_PAPER_QUICK_ANALYSIS: "analyze_paper",
    KIND_PAPER_DEEP_READ: "codex_deep_read",
}
_AI_ACTIONS = {
    KIND_PAPER_QUICK_ANALYSIS: "research.paper_review_card",
    KIND_PAPER_DEEP_READ: "research.paper_deep_read_codex",
}
_RECENT_NOTES_LIMIT = 5

# Deep-study report sections in reading order, with the same Chinese labels
# the sidecar Reader's Review panel uses (web_reader_api deep_section_*).
_DEEP_READ_SECTIONS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("problem", "问题与动机", ("problem", "motivation")),
    ("context", "背景与缺口", ("context",)),
    ("contributions", "核心贡献", ("contributions",)),
    ("method", "方法与机制", ("method", "mechanism")),
    ("metrics", "指标与公式", ("metrics",)),
    ("experiments", "实验与结果", ("experiments", "results")),
    ("limitations", "局限", ("limitations",)),
    ("project_relevance", "项目相关性", ("project_relevance",)),
    ("open_questions", "开放问题", ("open_questions",)),
    ("reading_plan", "阅读计划", ("reading_plan",)),
    ("terms", "关键术语", ("terms",)),
    ("section_summaries", "分节摘要", ("section_summaries",)),
)
_REF_KEYS = (
    "refs",
    "cited_refs",
    "segment_refs",
    "cited_segment_refs",
    "chunk_refs",
    "cited_chunk_refs",
    "annotation_refs",
    "cited_annotation_refs",
)
_REF_SCALAR_KEYS = ("segment_id", "segment_ref", "scope_ref", "chunk_id", "annotation_id")
_ITEM_TEXT_KEYS = ("text", "summary", "reason", "definition", "rationale", "point", "title")
_ITEM_LABEL_KEYS = ("term", "section", "metric", "label")


# --- Response models -----------------------------------------------------------


class PaperRefModel(BaseModel):
    """One cited ref resolved to a PDF page (``page`` 0 = unresolved)."""

    ref: str
    page: int = 0


class PaperAnalysisItemModel(BaseModel):
    """One analysis bullet: optional label (term/metric/section) + refs."""

    text: str
    label: str = ""
    latex: str = Field(default="", description="LaTeX source for an equation item (deep read).")
    badge: str = Field(default="", description="Short tag such as evidence support (deep read).")
    refs: list[PaperRefModel] = Field(default_factory=list)


class PaperAnalysisSectionModel(BaseModel):
    key: str
    label: str
    items: list[PaperAnalysisItemModel] = Field(default_factory=list)


class PaperCoverageModel(BaseModel):
    """What part of the paper an AI result actually cites."""

    cited_segments: int = 0
    pages: list[int] = Field(default_factory=list)
    page_count: int = 0
    sections: list[str] = Field(default_factory=list)


class PaperQuickAnalysisModel(BaseModel):
    """Quick analysis (快速分析): judge what the paper did / whether to read on."""

    updated: str = ""
    status: str = "ready"
    fallback: bool = False
    tldr: str = ""
    key_points: list[PaperAnalysisItemModel] = Field(default_factory=list)
    method: list[PaperAnalysisItemModel] = Field(default_factory=list)
    experiments: list[PaperAnalysisItemModel] = Field(default_factory=list)
    limitations: list[PaperAnalysisItemModel] = Field(default_factory=list)
    usefulness: list[PaperAnalysisItemModel] = Field(default_factory=list)
    project_relevance: list[PaperAnalysisItemModel] = Field(default_factory=list)
    reading_plan: list[PaperAnalysisItemModel] = Field(default_factory=list)
    open_questions: list[PaperAnalysisItemModel] = Field(default_factory=list)
    scores: dict[str, int] = Field(default_factory=dict)
    scores_evaluated: bool = False
    score_rationale: list[PaperAnalysisItemModel] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    coverage: PaperCoverageModel = Field(default_factory=PaperCoverageModel)


class PaperDeepReadModel(BaseModel):
    """Deep study (深度研读) report saved under ``codex_deep_read``."""

    updated: str = ""
    status: str = "ready"
    fallback: bool = False
    takeaway: str = ""
    takeaway_refs: list[PaperRefModel] = Field(default_factory=list)
    worth_reading: str = Field(default="", description="必读 / 值得细读 / 略读即可 / 可以跳过 (v2 notes).")
    audience: str = ""
    sections: list[PaperAnalysisSectionModel] = Field(default_factory=list)
    batch_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    coverage: PaperCoverageModel = Field(default_factory=PaperCoverageModel)


class PaperSourceMetaModel(BaseModel):
    id: str
    title: str = ""
    status: str = "inbox"
    authors: list[str] = Field(default_factory=list)
    venue: str = ""
    year: str = ""
    published: str = ""
    doi: str = ""
    arxiv_id: str = ""
    url: str = ""
    pdf_url: str = ""
    tags: list[str] = Field(default_factory=list)
    captured_at: str = ""


class PaperAbstractModel(BaseModel):
    text: str = ""
    translation: str = ""
    translation_status: str = "missing"
    page: int = 0
    origin: str = ""


class PaperPdfStatusModel(BaseModel):
    available: bool = False
    page_count: int = 0
    download_status: str = ""
    download_error: str = ""
    extraction_status: str = ""
    structure_backend: str = ""
    segment_count: int = 0
    structure_unit_count: int = 0
    extracted_at: str = ""


class PaperReadingProgressModel(BaseModel):
    last_page: int = 0
    page_count: int = 0
    last_read_at: str = ""
    mode: str = ""


class PaperTranslationProgressModel(BaseModel):
    total: int = 0
    translated: int = 0
    missing: int = 0
    stale: int = 0
    failed: int = 0
    status: str = "missing"


class PaperNoteModel(BaseModel):
    id: str
    page: int = 0
    quote: str = ""
    note: str = ""
    color: str = ""
    locator: str = ""
    updated: str = ""


class PaperNotesSummaryModel(BaseModel):
    annotation_count: int = 0
    chunk_count: int = 0
    recent: list[PaperNoteModel] = Field(default_factory=list)


class PaperJobRefModel(BaseModel):
    """An in-flight analysis job the page can re-attach its SSE stream to."""

    job_id: str
    kind: str
    status: str
    phase: str = ""
    message: str = ""


class PaperOverviewResponse(BaseModel):
    profile: str
    source: PaperSourceMetaModel
    abstract: PaperAbstractModel = Field(default_factory=PaperAbstractModel)
    pdf: PaperPdfStatusModel = Field(default_factory=PaperPdfStatusModel)
    progress: PaperReadingProgressModel = Field(default_factory=PaperReadingProgressModel)
    translation: PaperTranslationProgressModel = Field(default_factory=PaperTranslationProgressModel)
    notes: PaperNotesSummaryModel = Field(default_factory=PaperNotesSummaryModel)
    quick_analysis: PaperQuickAnalysisModel | None = None
    deep_read: PaperDeepReadModel | None = None
    reader_available: bool = False
    reader_unavailable_reason: str = ""
    active_jobs: list[PaperJobRefModel] = Field(default_factory=list)


class PaperJobStartRequest(BaseModel):
    kind: str = Field(description="paper-quick-analysis | paper-deep-read")


# --- Small helpers -------------------------------------------------------------


def _text(value: object) -> str:
    return str(value or "").strip()


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_items(value: Any) -> list[Any]:
    """Normalize a stored analysis field into a list of raw items.

    Older review cards stored ``usefulness`` as a Python-repr string of a
    list of dicts; parse that safely (``ast.literal_eval`` only accepts
    literals) instead of showing the repr to the user.
    """
    if value is None:
        return []
    if isinstance(value, str):
        clean = value.strip()
        if not clean:
            return []
        if clean.startswith("[") and clean.endswith("]"):
            try:
                parsed = ast.literal_eval(clean)
            except (ValueError, SyntaxError):
                parsed = None
            if isinstance(parsed, list):
                return [item for item in parsed if item]
        return [clean]
    if isinstance(value, (list, tuple)):
        return [item for item in value if item]
    if isinstance(value, dict):
        return [value]
    return [value]


def _item_refs(value: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in _REF_KEYS:
        raw = value.get(key)
        if isinstance(raw, str):
            refs.extend(part.strip() for part in raw.split(",") if part.strip())
        elif isinstance(raw, (list, tuple)):
            refs.extend(_text(part) for part in raw if _text(part))
    for key in _REF_SCALAR_KEYS:
        if _text(value.get(key)):
            refs.append(_text(value.get(key)))
    out: list[str] = []
    for ref in refs:
        if ref not in out:
            out.append(ref)
    return out


class _RefResolver:
    """Map segment / structure-unit / chunk / annotation ids to pages."""

    def __init__(self, pages: dict[str, int]) -> None:
        self._pages = pages

    def page(self, ref: str) -> int:
        return self._pages.get(ref, 0)

    def refs(self, raw: list[str]) -> list[PaperRefModel]:
        return [PaperRefModel(ref=ref, page=self.page(ref)) for ref in raw]


def _items(value: Any, resolver: _RefResolver) -> list[PaperAnalysisItemModel]:
    out: list[PaperAnalysisItemModel] = []
    for raw in _as_items(value):
        if isinstance(raw, dict):
            text = next((_text(raw.get(key)) for key in _ITEM_TEXT_KEYS if _text(raw.get(key))), "")
            label = next((_text(raw.get(key)) for key in _ITEM_LABEL_KEYS if _text(raw.get(key))), "")
            refs = resolver.refs(_item_refs(raw))
        else:
            text, label, refs = _text(raw), "", []
        if not text:
            continue
        out.append(PaperAnalysisItemModel(text=text, label=label, refs=refs))
    return out


def _coverage(
    items: list[PaperAnalysisItemModel],
    cited: list[str],
    resolver: _RefResolver,
    *,
    sections: list[str] | None = None,
) -> PaperCoverageModel:
    pages = {ref.page for item in items for ref in item.refs if ref.page > 0}
    pages.update(resolver.page(ref) for ref in cited if resolver.page(ref) > 0)
    seg_refs = {ref for ref in cited if ref.startswith("seg:")}
    seg_refs.update(ref.ref for item in items for ref in item.refs if ref.ref.startswith("seg:"))
    return PaperCoverageModel(
        cited_segments=len(seg_refs),
        pages=sorted(pages),
        page_count=len(pages),
        sections=sections or [],
    )


def _is_fallback(warnings: list[str]) -> bool:
    lowered = " ".join(warnings).lower()
    return "fallback" in lowered or "deterministic" in lowered


def _string_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [_text(item) for item in value if _text(item)]
    clean = _text(value)
    return [clean] if clean else []


# --- Overview projection -------------------------------------------------------


def _ref_pages(pdir: Path, source_id: str, structure_rows: list[dict[str, Any]]) -> dict[str, int]:
    pages: dict[str, int] = {}
    for segment in load_paper_segments(pdir, source_id):
        if segment.segment_id and segment.page > 0:
            pages[segment.segment_id] = segment.page
    for row in structure_rows:
        unit_id = _text(row.get("unit_id"))
        page = _int(row.get("page_start") or row.get("page"))
        if unit_id and page > 0:
            pages[unit_id] = page
    for chunk in load_chunks(pdir, source_id):
        page = _int((chunk.metadata or {}).get("page"))
        if chunk.id and page > 0:
            pages[chunk.id] = page
    for annotation in load_paper_annotations(pdir, source_id):
        if annotation.id and annotation.page > 0:
            pages[annotation.id] = annotation.page
    return pages


def _translation_projection(
    pdir: Path, source_id: str, structure_units: list[Any]
) -> tuple[PaperTranslationProgressModel, list[dict[str, Any]]]:
    """Translation counts keyed by the canonical structure (Reader semantics).

    Mirrors ``routes_v1.get_profile_research`` so the overview and the desk
    card can never disagree; falls back to legacy segments when the paper
    has no positioned structure yet.
    """
    translations = load_paper_translations(pdir, source_id)
    structure_rows = reader_translation_structure_units(structure_units)
    if structure_rows:
        units, counts = build_translation_units(
            pages=[],
            segments=[],
            translations=[item.to_dict() for item in translations],
            target_lang="zh",
            layout_units=structure_rows,
        )
        translated = int(counts.get("translated", 0))
        missing = int(counts.get("missing", 0))
        stale = int(counts.get("stale", 0))
        failed = int(counts.get("failed", 0))
        total = sum(int(value) for value in counts.values())
    else:
        units = []
        translated = missing = stale = failed = 0
        segments = load_paper_segments(pdir, source_id)
        for segment in segments:
            match = next(
                (
                    item
                    for item in translations
                    if item.segment_id == segment.segment_id and item.target_lang == "zh"
                ),
                None,
            )
            if match is None:
                missing += 1
            elif match.status == "failed":
                failed += 1
            elif (
                match.status == "translated"
                and match.source_hash == segment.text_hash
                and match.translated_text
            ):
                translated += 1
            else:
                stale += 1
        total = len(segments)
    status = (
        "translated"
        if total and translated == total
        else "failed"
        if failed and not translated
        else "stale"
        if stale
        else "partial"
        if translated
        else "missing"
    )
    progress = PaperTranslationProgressModel(
        total=total,
        translated=translated,
        missing=missing,
        stale=stale,
        failed=failed,
        status=status,
    )
    return progress, units


def _abstract(
    source: ResearchSource,
    structure_units: list[Any],
    translation_units: list[dict[str, Any]],
) -> PaperAbstractModel:
    """Abstract from the canonical structure, with its cached translation.

    Only already-saved translations are shown; the overview never triggers a
    translation request.
    """
    # The first contiguous run of Abstract paragraphs: a footnote or caption
    # interleaved on page 1 ends the run, so footnote continuations that the
    # layout pass also tagged "Abstract" are not shown as abstract text.
    ordered = sorted(structure_units, key=lambda unit: (unit.page_start, unit.order))
    abstract_units = []
    for unit in ordered:
        in_abstract = bool(unit.section_path) and _text(unit.section_path[0]).lower() == "abstract"
        if in_abstract and unit.kind == "paragraph":
            abstract_units.append(unit)
        elif abstract_units and not (in_abstract and unit.kind == "heading"):
            break
    if abstract_units:
        by_id = {_text(row.get("unit_id")): row for row in translation_units}
        translated_parts: list[str] = []
        statuses: list[str] = []
        for unit in abstract_units:
            row = by_id.get(unit.unit_id) or {}
            status = _text(row.get("status")) or "missing"
            statuses.append(status)
            if status == "translated" and _text(row.get("translated_text")):
                translated_parts.append(_text(row.get("translated_text")))
        if statuses and all(status == "translated" for status in statuses):
            translation_status = "translated"
        elif translated_parts:
            translation_status = "partial"
        else:
            translation_status = statuses[0] if statuses else "missing"
        return PaperAbstractModel(
            text="\n\n".join(_text(unit.text) for unit in abstract_units),
            translation="\n\n".join(translated_parts),
            translation_status=translation_status,
            page=abstract_units[0].page_start,
            origin="structure",
        )
    metadata = source.metadata or {}
    fallback = _text(metadata.get("abstract")) or _text(source.summary)
    return PaperAbstractModel(text=fallback, origin="metadata" if fallback else "")


def _quick_analysis(analysis: dict[str, Any], resolver: _RefResolver) -> PaperQuickAnalysisModel | None:
    tldr = _text(analysis.get("tldr"))
    if not tldr and not analysis.get("key_points"):
        return None
    sections = {
        key: _items(analysis.get(key), resolver)
        for key in (
            "key_points",
            "method",
            "experiments",
            "limitations",
            "usefulness",
            "project_relevance",
            "reading_plan",
            "open_questions",
        )
    }
    rationale = _items(analysis.get("score_rationale"), resolver)
    raw_scores = analysis.get("scores") if isinstance(analysis.get("scores"), dict) else {}
    scores = {str(key): _int(value) for key, value in raw_scores.items()}
    warnings = _string_list(analysis.get("warnings"))
    fallback = _is_fallback(warnings)
    scores_evaluated = any(value > 0 for value in scores.values())
    all_items = [item for rows in sections.values() for item in rows] + rationale
    cited = _string_list(analysis.get("cited_segment_refs"))
    return PaperQuickAnalysisModel(
        updated=_text(analysis.get("updated")),
        status="needs_review" if (fallback or warnings or not scores_evaluated) else "ready",
        fallback=fallback,
        tldr=tldr,
        scores=scores,
        scores_evaluated=scores_evaluated,
        score_rationale=rationale,
        warnings=warnings,
        coverage=_coverage(all_items, cited, resolver),
        **sections,
    )


_WORTH_READING_LABELS = {
    "must_read": "必读",
    "worth_reading": "值得细读",
    "skim": "略读即可",
    "skip": "可以跳过",
}
_SUPPORT_LABELS = {"strong": "支撑充分", "partial": "部分支撑", "weak": "支撑不足"}
_NEXT_KIND_LABELS = {"question": "疑问", "reading": "延伸阅读"}


def _join_parts(*parts: tuple[str, object]) -> str:
    """Join labelled fragments like ``做什么：…；为什么：…`` skipping blanks."""

    out = []
    for label, value in parts:
        # Model prose usually ends with "。"; drop it so joins read "…；直觉：…".
        clean = _text(value).rstrip("。；;，, ")
        if clean:
            out.append(f"{label}：{clean}" if label else clean)
    return "；".join(out)


def _v2_item(
    raw: Any,
    resolver: _RefResolver,
    *,
    text: str,
    label: str = "",
    latex: str = "",
    badge: str = "",
) -> PaperAnalysisItemModel | None:
    if not text and not latex:
        return None
    refs = resolver.refs(_item_refs(raw)) if isinstance(raw, dict) else []
    return PaperAnalysisItemModel(text=text, label=label, latex=latex, badge=badge, refs=refs)


def _v2_rows(value: Any) -> list[dict[str, Any]]:
    return [row for row in _as_items(value) if isinstance(row, dict)]


def _deep_read_v2_sections(raw: dict[str, Any], resolver: _RefResolver) -> list[PaperAnalysisSectionModel]:
    """Map study notes (schema v2) onto labelled overview sections."""

    method = raw.get("method") if isinstance(raw.get("method"), dict) else {}
    experiments = raw.get("experiments") if isinstance(raw.get("experiments"), dict) else {}
    plan: list[tuple[str, str, list[PaperAnalysisItemModel | None]]] = [
        (
            "setting",
            "问题设定",
            [_v2_item(row, resolver, text=_text(row.get("text"))) for row in _v2_rows(raw.get("setting"))],
        ),
        (
            "components",
            "方法组件",
            [
                _v2_item(
                    row,
                    resolver,
                    label=_text(row.get("name")),
                    text=_join_parts(("做什么", row.get("what")), ("为什么", row.get("why")), ("怎么做", row.get("how"))),
                )
                for row in _v2_rows(method.get("components"))
            ],
        ),
        (
            "equations",
            "关键公式",
            [
                _v2_item(
                    row,
                    resolver,
                    label=_text(row.get("label")),
                    latex=_text(row.get("latex")),
                    text=_join_parts(("含义", row.get("meaning")), ("直觉", row.get("intuition"))),
                )
                for row in _v2_rows(method.get("equations"))
            ],
        ),
        (
            "training",
            "训练细节",
            [_v2_item(row, resolver, text=_text(row.get("text"))) for row in _v2_rows(method.get("training"))],
        ),
        (
            "tables",
            "实验表格",
            [
                _v2_item(
                    row,
                    resolver,
                    label=_text(row.get("label")),
                    text=_join_parts(
                        ("设置", row.get("setup")),
                        ("对比", row.get("baselines")),
                        ("关键数字", row.get("key_numbers")),
                        ("说明", row.get("takeaway")),
                    ),
                )
                for row in _v2_rows(experiments.get("tables"))
            ],
        ),
        (
            "claims",
            "论点与支撑",
            [
                _v2_item(
                    row,
                    resolver,
                    text=_join_parts(("", row.get("claim")), ("依据", row.get("evidence")), ("保留", row.get("caveat"))),
                    badge=_SUPPORT_LABELS.get(_text(row.get("support")), ""),
                )
                for row in _v2_rows(raw.get("claims"))
            ],
        ),
        (
            "reproduction",
            "复现要点",
            [_v2_item(row, resolver, text=_text(row.get("text"))) for row in _v2_rows(raw.get("reproduction"))],
        ),
        (
            "sections",
            "逐节笔记",
            [
                _v2_item(row, resolver, label=_text(row.get("section")), text=_text(row.get("summary")))
                for row in _v2_rows(raw.get("sections"))
            ],
        ),
        (
            "terms",
            "术语",
            [
                _v2_item(
                    row,
                    resolver,
                    label=_join_parts(("", row.get("term")), ("", row.get("translation"))).replace("；", " · "),
                    text=_text(row.get("definition")),
                )
                for row in _v2_rows(raw.get("terms"))
            ],
        ),
        (
            "relevance",
            "与我的关联",
            [
                _v2_item(row, resolver, label=_text(row.get("target")), text=_text(row.get("text")))
                for row in _v2_rows(raw.get("relevance"))
            ],
        ),
        (
            "next",
            "疑问与下一步",
            [
                _v2_item(
                    row,
                    resolver,
                    text=_text(row.get("text")),
                    badge=_NEXT_KIND_LABELS.get(_text(row.get("kind")), ""),
                )
                for row in _v2_rows(raw.get("next"))
            ],
        ),
    ]
    sections: list[PaperAnalysisSectionModel] = []
    for key, label, items in plan:
        clean = [item for item in items if item is not None]
        if clean:
            sections.append(PaperAnalysisSectionModel(key=key, label=label, items=clean))
    return sections


def _deep_read_v2(analysis: dict[str, Any], raw: dict[str, Any], resolver: _RefResolver) -> PaperDeepReadModel | None:
    verdict = raw.get("verdict") if isinstance(raw.get("verdict"), dict) else {}
    sections = _deep_read_v2_sections(raw, resolver)
    takeaway = _text(verdict.get("summary"))
    if not takeaway and not sections:
        return None
    warnings = _string_list(raw.get("warnings"))
    fallback = _is_fallback(warnings) or not sections
    section_names = [
        _text(row.get("section"))
        for row in _v2_rows(raw.get("sections"))
        if _text(row.get("section"))
    ]
    all_items = [item for section in sections for item in section.items]
    return PaperDeepReadModel(
        updated=_text(analysis.get("codex_deep_read_updated")),
        status="needs_review" if fallback else "ready",
        fallback=fallback,
        takeaway=takeaway,
        takeaway_refs=resolver.refs(_item_refs(verdict)),
        worth_reading=_WORTH_READING_LABELS.get(_text(verdict.get("worth_reading")), ""),
        audience=_text(verdict.get("audience")),
        sections=sections,
        warnings=warnings,
        coverage=_coverage(
            all_items,
            _string_list(raw.get("cited_segment_refs")),
            resolver,
            sections=section_names,
        ),
    )


def _deep_read(analysis: dict[str, Any], resolver: _RefResolver) -> PaperDeepReadModel | None:
    raw = analysis.get("codex_deep_read")
    if not isinstance(raw, dict) or not raw:
        return None
    if _text(raw.get("schema_version")) == "2" or isinstance(raw.get("verdict"), dict):
        return _deep_read_v2(analysis, raw, resolver)
    sections: list[PaperAnalysisSectionModel] = []
    for key, label, sources in _DEEP_READ_SECTIONS:
        items: list[PaperAnalysisItemModel] = []
        for source_key in sources:
            items.extend(_items(raw.get(source_key), resolver))
        if items:
            sections.append(PaperAnalysisSectionModel(key=key, label=label, items=items))
    takeaway = _text(raw.get("takeaway"))
    if not takeaway and not sections:
        return None
    warnings = _string_list(raw.get("warnings"))
    fallback = _is_fallback(warnings)
    section_names: list[str] = []
    for row in _as_items(raw.get("section_summaries")):
        name = _text(row.get("section")) if isinstance(row, dict) else ""
        if name and name not in section_names:
            section_names.append(name)
    batch = raw.get("batch_reading") if isinstance(raw.get("batch_reading"), dict) else {}
    all_items = [item for section in sections for item in section.items]
    return PaperDeepReadModel(
        updated=_text(analysis.get("codex_deep_read_updated")),
        status="needs_review" if fallback else "ready",
        fallback=fallback,
        takeaway=takeaway,
        sections=sections,
        batch_count=_int(batch.get("batch_count")),
        warnings=warnings,
        coverage=_coverage(
            all_items,
            _string_list(raw.get("cited_segment_refs")),
            resolver,
            sections=section_names,
        ),
    )


def _source_meta(source: ResearchSource) -> PaperSourceMetaModel:
    metadata = source.metadata or {}
    published = _text(source.published)
    year = _text(metadata.get("year"))
    if not year and len(published) >= 4 and published[:4].isdigit():
        year = published[:4]
    return PaperSourceMetaModel(
        id=source.id,
        title=source.title or source.id,
        status=source.status,
        authors=list(source.authors),
        venue=_text(metadata.get("venue") or metadata.get("journal") or metadata.get("booktitle")),
        year=year,
        published=published,
        doi=_text(metadata.get("doi")),
        arxiv_id=_text(metadata.get("arxiv_id")),
        url=_text(source.url),
        pdf_url=_text(metadata.get("pdf_url") or metadata.get("open_access_pdf_url")),
        tags=list(source.tags),
        captured_at=_text(source.captured_at),
    )


def _recent_notes(pdir: Path, source_id: str) -> PaperNotesSummaryModel:
    annotations = [
        item for item in load_paper_annotations(pdir, source_id) if item.status != "deleted"
    ]
    annotations.sort(key=lambda item: item.updated or item.created, reverse=True)
    return PaperNotesSummaryModel(
        annotation_count=len(annotations),
        chunk_count=len(load_chunks(pdir, source_id)),
        recent=[
            PaperNoteModel(
                id=item.id,
                page=item.page,
                quote=item.selected_text,
                note=item.note,
                color=item.color,
                locator=item.locator,
                updated=item.updated or item.created,
            )
            for item in annotations[:_RECENT_NOTES_LIMIT]
        ],
    )


def build_paper_overview(pdir: Path, source: ResearchSource) -> PaperOverviewResponse:
    """Compose the overview payload from the profile's paper files (read-only)."""
    source_id = source.id
    metadata = source.metadata or {}
    structure_units = load_paper_structure_units(pdir, source_id)
    structure_rows = [unit.to_dict() for unit in structure_units]
    resolver = _RefResolver(_ref_pages(pdir, source_id, structure_rows))
    translation, translation_units = _translation_projection(pdir, source_id, structure_units)
    analysis = load_paper_analysis(pdir, source_id)

    reader_available = False
    unavailable_reason = ""
    try:
        paper_pdf_asset_path(pdir, source_id)
        reader_available = True
    except (FileNotFoundError, ValueError, OSError):
        unavailable_reason = "PDF 尚未就绪，暂时无法打开阅读器。"

    page_count = _int(metadata.get("page_count") or metadata.get("reading_artifacts_page_count"))
    return PaperOverviewResponse(
        profile=pdir.name,
        source=_source_meta(source),
        abstract=_abstract(source, structure_units, translation_units),
        pdf=PaperPdfStatusModel(
            available=reader_available,
            page_count=page_count,
            download_status=_text(metadata.get("pdf_download_status")),
            download_error=_text(metadata.get("pdf_download_error")),
            extraction_status=_text(metadata.get("reading_artifacts_status")),
            structure_backend=_text(metadata.get("structure_backend")),
            segment_count=len(load_paper_segments(pdir, source_id)),
            structure_unit_count=len(structure_units),
            extracted_at=_text(
                metadata.get("structured_extracted_at") or metadata.get("text_extracted_at")
            ),
        ),
        progress=PaperReadingProgressModel(
            last_page=_int(metadata.get("last_read_page")),
            page_count=page_count,
            last_read_at=_text(metadata.get("last_read_at")),
            mode=_text(metadata.get("reader_mode")),
        ),
        translation=translation,
        notes=_recent_notes(pdir, source_id),
        quick_analysis=_quick_analysis(analysis, resolver),
        deep_read=_deep_read(analysis, resolver),
        reader_available=reader_available,
        reader_unavailable_reason=unavailable_reason,
        active_jobs=_active_jobs(pdir, source_id),
    )


# --- Analysis jobs ---------------------------------------------------------------

# (profile scope, source_id, kind) -> job_id of the latest started job, so a
# page reload can re-attach to a running job and a double click does not
# start a second LLM/Codex run. Process-local like the job registry itself.
_ACTIVE_JOBS: dict[tuple[str, str, str], str] = {}
_ACTIVE_LOCK = threading.Lock()


def _scope(pdir: Path) -> str:
    try:
        return str(Path(pdir).resolve())
    except (OSError, RuntimeError):
        return str(pdir)


def _live_job(job_id: str) -> dict[str, Any] | None:
    bundle = jobs.read_job(job_id)
    if bundle is None:
        return None
    snapshot = bundle["snapshot"]
    if snapshot.get("status") in jobs.FINAL_STATUSES:
        return None
    return snapshot


def _active_jobs(pdir: Path, source_id: str) -> list[PaperJobRefModel]:
    scope = _scope(pdir)
    out: list[PaperJobRefModel] = []
    with _ACTIVE_LOCK:
        entries = [
            (kind, job_id)
            for (job_scope, job_source, kind), job_id in _ACTIVE_JOBS.items()
            if job_scope == scope and job_source == source_id
        ]
    for kind, job_id in entries:
        snapshot = _live_job(job_id)
        if snapshot is None:
            continue
        out.append(
            PaperJobRefModel(
                job_id=job_id,
                kind=kind,
                status=str(snapshot.get("status") or ""),
                phase=str(snapshot.get("phase") or ""),
                message=str(snapshot.get("message") or ""),
            )
        )
    return out


def _effective_backend(profile: str, action: str) -> str:
    """User-facing backend (``llm`` / ``codex``) for one AI action."""
    try:
        prefs = load_web_preferences(profile)
    except Exception:  # noqa: BLE001 - unreadable prefs fall back to defaults
        prefs = {}
    ai = prefs.get("ai") if isinstance(prefs.get("ai"), dict) else {}
    actions = ai.get("actions") if isinstance(ai.get("actions"), dict) else {}
    config = actions.get(action) if isinstance(actions.get(action), dict) else {}
    backend = _text(config.get("backend"))
    if backend not in {"llm", "codex"}:
        backend = AI_ACTION_DEFAULT_BACKENDS.get(action, "llm")
    return backend if backend in {"llm", "codex"} else "llm"


def backend_problem(profile: str, kind: str) -> tuple[str, str] | None:
    """Return ``(code, message)`` when the action's backend cannot run.

    The gateway would otherwise silently degrade to the deterministic
    fallback; the overview wants a clear error the user can fix and retry.
    """
    backend = _effective_backend(profile, _AI_ACTIONS[kind])
    label = "深度研读" if kind == KIND_PAPER_DEEP_READ else "快速分析"
    if backend == "codex":
        status = codex_adapter.codex_status(codex_adapter.current_config(profile=profile))
        if not status.installed:
            return (
                "codex_unavailable",
                f"{label}使用 Codex CLI，但当前环境未安装 Codex。请在设置中配置 Codex，"
                "或在 AI 设置里把该功能改为 LLM 后重试。",
            )
        if not status.logged_in:
            return (
                "codex_not_logged_in",
                f"{label}使用 Codex CLI，但 Codex 尚未登录。请在终端执行 codex login 后重试。",
            )
        return None
    llm_client.reload_env_if_changed()
    if not llm_client.is_configured():
        return (
            "ai_not_configured",
            f"{label}需要 LLM 连接，但当前未配置 LLM_API_KEY。请在设置中配置模型连接后重试。",
        )
    return None


_PHASE_MESSAGES = {
    "preparing": "正在准备阅读结构…",
    "summarizing": "正在读取论文段落…",
    "scoring": "模型正在生成 TL;DR、要点与评分…",
    "normalizing": "正在整理分析结果…",
    "compacting": "正在压缩全文段落…",
    "reading": "Codex 正在通读全文…",
    "synthesizing": "正在综合各章节研读…",
    "structuring": "正在整理发现与阅读计划…",
    "saving": "正在保存结果…",
    "done": "即将完成…",
}


def _progress_bridge(report: Callable[..., None]) -> Callable[[dict[str, Any]], None]:
    def callback(event: dict[str, Any]) -> None:
        if not isinstance(event, dict):
            return
        phase = _text(event.get("phase")) or "running"
        current = _int(event.get("current"))
        total = _int(event.get("total"))
        if phase == "reading_batch" and total:
            message = f"分章节研读 {current}/{max(total - 2, current)}…"
        else:
            message = _PHASE_MESSAGES.get(phase) or _text(event.get("label")) or "处理中…"
        extra: dict[str, Any] = {}
        if total:
            extra = {"current": current, "total": total}
        report(phase, message, **extra)

    return callback


_FALLBACK_MARKER = "used rule_fallback"


def _has_result(analysis: dict[str, Any], kind: str) -> bool:
    if kind == KIND_PAPER_DEEP_READ:
        return isinstance(analysis.get("codex_deep_read"), dict) and bool(analysis.get("codex_deep_read"))
    return bool(_text(analysis.get("tldr")) or analysis.get("key_points"))


def _validate_paper_job_input(job_input: dict[str, Any]) -> dict[str, Any]:
    source_id = _text(job_input.get("source_id"))
    if not source_id:
        raise jobs.JobInputError("invalid_paper_job", "source_id is required.")
    if len(source_id) > 300:
        raise jobs.JobInputError("invalid_paper_job", "source_id is too long.")
    return {"source_id": source_id, "user_id": _text(job_input.get("user_id"))[:200]}


def _make_runner(kind: str) -> Callable[[str, dict[str, Any], Callable[..., None]], Any]:
    def run(profile: str, job_input: dict[str, Any], report: Callable[..., None]) -> Any:
        source_id = job_input["source_id"]
        pdir = profile_io.profile_dir(profile)
        if load_research_sources(pdir).by_id().get(source_id) is None:
            raise jobs.JobFailedError("paper_not_found", f"找不到论文：{source_id}")
        try:
            paper_pdf_asset_path(pdir, source_id)
        except (FileNotFoundError, ValueError, OSError) as exc:
            raise jobs.JobFailedError("paper_pdf_missing", "PDF 尚未就绪，无法分析。") from exc
        report("checking", "正在检查 AI 后端…")
        problem = backend_problem(profile, kind)
        if problem is not None:
            raise jobs.JobFailedError(*problem)
        # Snapshot the saved analysis: the Reader action persists even a
        # deterministic fallback, which must not replace a real result.
        analysis_path = _yaml_path(pdir, PAPER_ANALYSIS_DIRNAME, source_id)
        previous_text = analysis_path.read_text(encoding="utf-8") if analysis_path.exists() else ""
        had_previous = _has_result(load_paper_analysis(pdir, source_id), kind)
        ctx = ReaderActionContext(
            profile_name=profile,
            profile_path=pdir,
            user_id=job_input.get("user_id") or "web",
            source_id=source_id,
        )
        result = handle_reader_action(
            ctx,
            _READER_ACTIONS[kind],
            {"source_id": source_id, "scope": "paper", "full_paper": True, "target_lang": "zh"},
            progress_callback=_progress_bridge(report),
        )
        fallback_warning = next(
            (str(item) for item in result.warnings if _FALLBACK_MARKER in str(item)),
            "",
        )
        if not result.ok and ANALYSIS_FALLBACK_KEPT_WARNING in (result.message or ""):
            reason = f"（{fallback_warning[:160]}）" if fallback_warning else ""
            raise jobs.JobFailedError(
                "paper_analysis_fallback",
                f"模型没有返回可靠结果{reason}，已保留原有结果。详情见右上角「AI 异常」。",
            )
        if not result.ok:
            raise jobs.JobFailedError(
                "paper_analysis_failed",
                result.message or "AI 没有返回可用的结构化结果，请重试。",
            )
        if fallback_warning and had_previous and previous_text:
            atomic_write_text(analysis_path, previous_text)
            raise jobs.JobFailedError(
                "paper_analysis_fallback",
                "模型没有返回可靠结果（" + fallback_warning[:160] + "），已保留原有结果。详情见右上角「AI 异常」。",
            )
        analysis = load_paper_analysis(pdir, source_id)
        updated_key = "codex_deep_read_updated" if kind == KIND_PAPER_DEEP_READ else "updated"
        return {
            "source_id": source_id,
            "kind": kind,
            "message": result.message,
            "warnings": list(result.warnings)[:20],
            "updated": _text(analysis.get(updated_key)),
        }

    return run


def _register(spec: jobs.JobKind) -> None:
    register = getattr(jobs, "register_kind", None)
    if callable(register):
        register(spec)
    else:  # pragma: no cover - older jobs module without the helper
        jobs._KINDS[spec.name] = spec  # noqa: SLF001


_register(
    jobs.JobKind(
        name=KIND_PAPER_QUICK_ANALYSIS,
        validate=_validate_paper_job_input,
        run=_make_runner(KIND_PAPER_QUICK_ANALYSIS),
        queued_message="已排队：快速分析。",
        # A 16k-token card at ~30 tok/s takes ~9 minutes; stay below the
        # 20-minute job prune like deep read.
        timeout_seconds=1140,
        timeout_message="快速分析超时（19 分钟），请重试；可在「设置 → AI 服务」调低分析输出上限。",
    )
)
_register(
    jobs.JobKind(
        name=KIND_PAPER_DEEP_READ,
        validate=_validate_paper_job_input,
        run=_make_runner(KIND_PAPER_DEEP_READ),
        queued_message="已排队：深度研读。",
        # The job registry prunes records after 20 minutes; stay below it so
        # the stream always ends with a terminal frame.
        timeout_seconds=1140,
        timeout_message="深度研读超时（19 分钟），请重试；已完成的部分不会写入。",
    )
)


# --- Routes ---------------------------------------------------------------------


def _load_paper(name: str, source_id: str) -> tuple[Path, ResearchSource]:
    pdir = _resolve_profile(name)
    source = load_research_sources(pdir).by_id().get(source_id)
    if source is None or source.kind != "paper":
        raise ApiError(404, "paper_not_found", f"Unknown paper: {source_id}")
    return pdir, source


@router.get(
    "/profiles/{name}/research/papers/{source_id}",
    response_model=PaperOverviewResponse,
    responses=ERROR_RESPONSES,
)
def get_paper_overview(
    name: str,
    source_id: str,
    user: CurrentUser = Depends(require_profile_access),
) -> PaperOverviewResponse:
    """Single-paper overview (paper_reading.md §1.1.2). Read-only."""
    pdir, source = _load_paper(name, source_id)
    return build_paper_overview(pdir, source)


@router.post(
    "/profiles/{name}/research/papers/{source_id}/analysis-jobs",
    response_model=JobCreateResponse,
    status_code=202,
    responses=ERROR_RESPONSES,
)
def start_paper_analysis_job(
    name: str,
    source_id: str,
    body: PaperJobStartRequest,
    user: CurrentUser = Depends(require_profile_access),
) -> JSONResponse:
    """Start quick analysis / deep study for one paper (202 + job handle).

    A job of the same kind already running for this paper is returned
    instead of starting a second run. Subscribe to
    ``GET .../jobs/{job_id}/stream`` for progress.
    """
    kind = _text(body.kind)
    if kind not in PAPER_JOB_KINDS:
        raise ApiError(422, "invalid_paper_job", f"kind must be one of: {', '.join(PAPER_JOB_KINDS)}")
    pdir, source = _load_paper(name, source_id)
    key = (_scope(pdir), source.id, kind)
    with _ACTIVE_LOCK:
        existing = _ACTIVE_JOBS.get(key)
        snapshot = _live_job(existing) if existing else None
        if snapshot is None:
            try:
                snapshot = jobs.create_job(
                    pdir.name,
                    kind,
                    {"source_id": source.id, "user_id": user.id},
                    profile_scope=pdir,
                )
            except jobs.JobInputError as exc:
                raise ApiError(422, exc.code, exc.message) from exc
            _ACTIVE_JOBS[key] = snapshot["job_id"]
    payload = JobCreateResponse(job_id=snapshot["job_id"], job=JobModel(**snapshot))
    return JSONResponse(status_code=202, content=payload.model_dump(mode="json"))


__all__ = [
    "KIND_PAPER_DEEP_READ",
    "KIND_PAPER_QUICK_ANALYSIS",
    "PaperOverviewResponse",
    "backend_problem",
    "build_paper_overview",
    "router",
]
