"""Evidence v2 migration: non-destructive backfill + crystallized refresh.

Pure functions only (no Streamlit). These compute proposals; callers persist.

Key contracts:
- Backfill only fills empty fields. It never overwrites human-authored
  summary/title/strength/review_status/public_readiness/project_refs.
- ``original_content`` is preserved verbatim. The deterministic formatter never
  rewrites it; AI reformat (separate module) only proposes summary/formatted.
- ``migrate_evidence_pool`` is idempotent: a second run reports zero changes.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from nblane.core import llm as llm_client
from nblane.core.kanban_archive import find_kanban_tasks_by_ref, kanban_ref_id
from nblane.core.models import EVIDENCE_LANGUAGES

# Fields a human may have curated; backfill must not clobber these.
_PROTECTED_FIELDS = (
    "summary",
    "title",
    "strength",
    "review_status",
    "public_readiness",
    "project_refs",
)

_CJK_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
_LATIN_RE = re.compile(r"[A-Za-z]")


def detect_language(text: str) -> str:
    """Classify text language into one of EVIDENCE_LANGUAGES.

    ``zh`` when CJK present and Latin essentially absent; ``en`` when Latin
    present and no CJK; ``mixed`` when both are meaningfully present; ``unknown``
    when empty / no script signal.
    """
    s = str(text or "").strip()
    if not s:
        return "unknown"
    cjk = len(_CJK_RE.findall(s))
    latin = len(_LATIN_RE.findall(s))
    if cjk and latin:
        # Treat as mixed unless one side is a negligible sprinkle.
        weaker = min(cjk, latin)
        stronger = max(cjk, latin)
        if weaker * 12 < stronger:
            return "zh" if cjk > latin else "en"
        return "mixed"
    if cjk:
        return "zh"
    if latin:
        return "en"
    return "unknown"


def content_hash(text: str) -> str:
    """Stable short sha256 of *text*; empty text yields ''."""
    s = str(text or "")
    if not s.strip():
        return ""
    digest = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:16]}"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _is_paper_like(row: dict) -> bool:
    if _clean(row.get("type")) == "paper":
        return True
    blob = " ".join(
        _clean(row.get(k)) for k in ("title", "summary")
    ).lower()
    needles = (
        "paper",
        "patent",
        "publication",
        "doi",
        "arxiv",
        "论文",
        "专利",
        "发表",
    )
    return any(n in blob for n in needles)


def infer_origin(
    row: dict,
    *,
    resume_ids: set[str] | None = None,
) -> tuple[str, str, str]:
    """Infer (origin, origin_ref, origin_detail) for a legacy row.

    Order of precedence: explicit kanban refs -> paper signal -> resume-orphan
    heuristic -> manual_daily fallback.
    """
    resume_ids = resume_ids or set()
    eid = _clean(row.get("id"))

    kanban_refs = [
        _clean(r) for r in (row.get("kanban_refs") or []) if _clean(r)
    ]
    if kanban_refs:
        primary = kanban_ref_id(kanban_refs[0]) or kanban_refs[0]
        return (
            "kanban_task",
            kanban_refs[0],
            f"Done task {primary}",
        )

    if _is_paper_like(row):
        return ("paper", _clean(row.get("url")), "Paper / publication (inferred)")

    project_refs = [
        _clean(r) for r in (row.get("project_refs") or []) if _clean(r)
    ]
    if eid in resume_ids or (not kanban_refs and not project_refs):
        return (
            "resume_parse",
            "resume",
            "Resume parse (inferred; no original span retained)",
        )

    return ("manual_daily", "", "Manual daily entry (inferred)")


def render_kanban_task_source(task: Any) -> str:
    """Render a KanbanTask as a complete, readable Markdown source block.

    Includes every field the distillation needs to be auditable: id, title,
    context, why, outcome, dates, tags, project/milestone ids, subtasks, notes.
    """
    lines: list[str] = []
    title = _clean(getattr(task, "title", ""))
    lines.append(f"# {title}" if title else "# (untitled task)")
    tid = _clean(getattr(task, "id", ""))
    if tid:
        lines.append(f"id: {tid}")
    for label, attr in (
        ("context", "context"),
        ("why", "why"),
        ("outcome", "outcome"),
        ("blocked_by", "blocked_by"),
        ("started_on", "started_on"),
        ("completed_on", "completed_on"),
        ("project_id", "project_id"),
        ("milestone_id", "milestone_id"),
        ("tags", "tags"),
    ):
        val = _clean(getattr(task, attr, "") or "")
        if val:
            lines.append(f"{label}: {val}")
    if getattr(task, "crystallized", False):
        lines.append("crystallized: true")
    subtasks = [
        st
        for st in (getattr(task, "subtasks", []) or [])
        if _clean(getattr(st, "title", ""))
    ]
    if subtasks:
        lines.append("subtasks:")
        for st in subtasks:
            mark = "x" if getattr(st, "done", False) else " "
            lines.append(f"- [{mark}] {_clean(st.title)}")
    details = [d for d in (getattr(task, "details", []) or []) if _clean(d)]
    if details:
        lines.append("notes:")
        for d in details:
            lines.append(f"- {_clean(d)}")
    return "\n".join(lines)


def _draft_formatted_content(row: dict) -> str:
    """Deterministic (non-AI) formatted_content draft from existing fields."""
    lines: list[str] = []
    origin = _clean(row.get("origin"))
    if origin:
        lines.append(f"Origin: {origin}")
    title = _clean(row.get("title"))
    if title:
        lines.append(f"Title: {title}")
    summary = _clean(row.get("summary"))
    if summary:
        lines.append("")
        lines.append(summary)
    excerpt = _clean(row.get("source_excerpt"))
    if excerpt:
        lines.append("")
        lines.append(f"Source excerpt: {excerpt}")
    refs_bits = []
    for label, key in (
        ("Projects", "project_refs"),
        ("Kanban", "kanban_refs"),
        ("Sources", "source_refs"),
    ):
        vals = [_clean(r) for r in (row.get(key) or []) if _clean(r)]
        if vals:
            refs_bits.append(f"{label}: {', '.join(vals)}")
    if refs_bits:
        lines.append("")
        lines.extend(refs_bits)
    if _clean(row.get("original_content")):
        lines.append("")
        lines.append("See original_content for the full preserved source.")
    return "\n".join(lines).strip()


def backfill_row(
    row: dict,
    *,
    profile: str | Path,
    resume_ids: set[str] | None = None,
    target_lang: str | None = None,
) -> tuple[dict, bool, list[str]]:
    """Return (new_row, changed, notes). Non-destructive: only fills blanks."""
    notes: list[str] = []
    out = dict(row)
    target_lang = (target_lang or llm_client.reply_language() or "en").strip()
    if target_lang not in EVIDENCE_LANGUAGES:
        target_lang = "en"

    # origin / origin_ref / origin_detail
    if not _clean(out.get("origin")):
        origin, origin_ref, origin_detail = infer_origin(
            out, resume_ids=resume_ids
        )
        out["origin"] = origin
        if origin_ref and not _clean(out.get("origin_ref")):
            out["origin_ref"] = origin_ref
        if origin_detail and not _clean(out.get("origin_detail")):
            out["origin_detail"] = origin_detail
        notes.append(f"origin={origin}")

    # original_content: prefer kanban task markdown, then excerpt/formatted/summary.
    if not _clean(out.get("original_content")):
        original = _original_content_candidate(out, profile=profile)
        if original:
            out["original_content"] = original
            notes.append("original_content backfilled")
        else:
            notes.append("original_content unavailable (no source retained)")

    # formatted_content: deterministic draft if empty.
    if not _clean(out.get("formatted_content")):
        draft = _draft_formatted_content(out)
        if draft:
            out["formatted_content"] = draft
            notes.append("formatted_content draft")

    # language of normalized fields: default to target language.
    if not _clean(out.get("language")):
        out["language"] = target_lang
        notes.append(f"language={target_lang}")

    # original_language: detect from original_content.
    if not _clean(out.get("original_language")) and _clean(
        out.get("original_content")
    ):
        out["original_language"] = detect_language(out["original_content"])
        notes.append(f"original_language={out['original_language']}")

    # hash of preserved original.
    if not _clean(out.get("original_content_hash")) and _clean(
        out.get("original_content")
    ):
        out["original_content_hash"] = content_hash(out["original_content"])

    # Guard: never touch protected human fields (defensive — we only add above).
    for key in _PROTECTED_FIELDS:
        if key in row:
            out[key] = row[key]

    changed = out != row
    return out, changed, notes


def _original_content_candidate(
    row: dict,
    *,
    profile: str | Path,
) -> str:
    """Best available original content per the backfill precedence ladder."""
    kanban_refs = [
        _clean(r) for r in (row.get("kanban_refs") or []) if _clean(r)
    ]
    if kanban_refs:
        try:
            tasks = find_kanban_tasks_by_ref(profile, kanban_refs)
        except Exception:
            tasks = []
        if tasks:
            return "\n\n".join(
                render_kanban_task_source(t) for t in tasks
            ).strip()
    # Note: formatted_content is intentionally NOT a fallback here. It can be
    # an auto-generated draft, and treating a derived draft as raw source would
    # break migration idempotency (draft -> original -> re-draft loop).
    for key in ("source_excerpt", "summary"):
        val = _clean(row.get(key))
        if val:
            return val
    return ""


def migrate_evidence_pool(
    profile: str | Path,
    *,
    entries: list[dict] | None = None,
    resume_ids: set[str] | None = None,
    target_lang: str | None = None,
) -> dict[str, Any]:
    """Compute a non-destructive migration proposal for the whole pool.

    Idempotent: re-running on already-migrated entries yields changed_count 0.
    Does not save. Pass *entries* to migrate an in-memory list; otherwise loads
    the profile pool from disk.
    """
    if entries is None:
        from nblane.core.profile_io import load_evidence_pool_raw

        raw = load_evidence_pool_raw(profile)
        entries = list((raw or {}).get("evidence_entries") or [])

    new_entries: list[dict] = []
    per_row: list[dict] = []
    warnings: list[str] = []
    changed_count = 0
    for row in entries:
        if not isinstance(row, dict):
            new_entries.append(row)
            continue
        new_row, changed, notes = backfill_row(
            row,
            profile=profile,
            resume_ids=resume_ids,
            target_lang=target_lang,
        )
        new_entries.append(new_row)
        if changed:
            changed_count += 1
        if "original_content unavailable (no source retained)" in notes:
            warnings.append(
                f"{_clean(row.get('id')) or '(no id)'}: no original source"
            )
        per_row.append(
            {
                "id": _clean(row.get("id")),
                "title": _clean(row.get("title")),
                "changed": changed,
                "notes": notes,
                "before": row,
                "after": new_row,
            }
        )

    return {
        "entries": new_entries,
        "changed_count": changed_count,
        "per_row": per_row,
        "warnings": warnings,
    }


def refresh_from_crystallized_tasks(
    profile: str | Path,
    *,
    entries: list[dict] | None = None,
) -> dict[str, Any]:
    """Find crystallized kanban tasks and propose new/updated evidence.

    Returns {proposals, warnings}. Does not save; the UI confirms each.
    A proposal is ``kind="update"`` when an evidence row already references the
    task (via kanban_refs), else ``kind="new"``.
    """
    from nblane.core.kanban_archive import _all_lookup_tasks, kanban_ref

    if entries is None:
        from nblane.core.profile_io import load_evidence_pool_raw

        raw = load_evidence_pool_raw(profile)
        entries = list((raw or {}).get("evidence_entries") or [])

    # Index existing evidence by referenced kanban task id.
    refs_by_task: dict[str, str] = {}
    for row in entries:
        if not isinstance(row, dict):
            continue
        eid = _clean(row.get("id"))
        for ref in row.get("kanban_refs") or []:
            rid = kanban_ref_id(_clean(ref))
            if rid:
                refs_by_task.setdefault(rid, eid)

    try:
        tasks = _all_lookup_tasks(profile)
    except Exception as exc:  # pragma: no cover - defensive
        return {"proposals": [], "warnings": [f"task load failed: {exc}"]}

    proposals: list[dict] = []
    warnings: list[str] = []
    seen_task_ids: set[str] = set()
    for task in tasks:
        if not getattr(task, "crystallized", False):
            continue
        tid = _clean(getattr(task, "id", ""))
        if not tid or tid in seen_task_ids:
            continue
        seen_task_ids.add(tid)
        original = render_kanban_task_source(task)
        project_id = _clean(getattr(task, "project_id", ""))
        existing_eid = refs_by_task.get(tid)
        proposals.append(
            {
                "kind": "update" if existing_eid else "new",
                "evidence_id": existing_eid or "",
                "task_id": tid,
                "title": _clean(getattr(task, "title", "")),
                "completed_on": _clean(
                    getattr(task, "completed_on", "") or ""
                ),
                "origin": "kanban_task",
                "origin_ref": kanban_ref(tid),
                "kanban_refs": [kanban_ref(tid)],
                "project_refs": [project_id] if project_id else [],
                "original_content": original,
                "original_content_hash": content_hash(original),
                "original_language": detect_language(original),
            }
        )

    return {"proposals": proposals, "warnings": warnings}


# --- Project suggestions from unassigned resume/manual evidence -------------

_STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "project",
        "experience",
        "work",
        "the",
        "a",
        "an",
        "of",
        "to",
        "in",
        "on",
        "at",
        "优化",
        "项目",
        "经历",
        # Generic provenance boilerplate — must never become a grouping token,
        # or every inferred resume orphan would collapse into one bogus group.
        "resume",
        "parse",
        "parsed",
        "inferred",
        "manual",
        "daily",
        "entry",
        "block",
        "span",
        "no",
        "original",
        "retained",
    }
)

# origin_detail strings produced by infer_origin() are generic and must not
# drive grouping; only human/LLM-authored detail (e.g. "GAC ...") should.
_GENERIC_DETAIL_PREFIXES = (
    "resume parse (inferred",
    "manual daily entry (inferred",
    "paper / publication (inferred",
)


def _grouping_key(row: dict) -> str:
    """Derive a coarse grouping token from title/origin_detail.

    Groups resume rows that look like the same project (e.g. three GAC rows).
    Uses the first meaningful uppercase acronym / token, else the first word.
    Generic inferred origin_detail is ignored so unrelated orphans don't merge.
    """
    detail = _clean(row.get("origin_detail"))
    if detail.lower().startswith(_GENERIC_DETAIL_PREFIXES):
        detail = ""
    title = _clean(row.get("title"))
    blob = f"{detail} {title}".strip()
    # Prefer an ALL-CAPS acronym (GAC, CVPR) — strong project signal.
    for token in re.findall(r"\b[A-Z]{2,}\b", blob):
        if token.lower() not in _STOPWORDS:
            return token.lower()
    for token in re.findall(r"[\w一-鿿]+", blob.lower()):
        if token and token not in _STOPWORDS and len(token) >= 2:
            return token
    return ""


def suggest_projects_from_evidence(
    rows: list[dict],
    *,
    origins: tuple[str, ...] = ("resume_parse", "manual_daily"),
) -> list[dict]:
    """Group unassigned resume/manual evidence into Project Board suggestions.

    Only considers rows whose origin is in *origins* and that have no
    project_refs. Returns one suggestion per group with >= 2 members (a single
    orphan is not worth a project). Suggest-and-confirm: never creates anything.
    """
    groups: dict[str, list[dict]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _clean(row.get("origin")) not in origins:
            continue
        if [r for r in (row.get("project_refs") or []) if _clean(r)]:
            continue
        key = _grouping_key(row)
        if not key:
            continue
        groups.setdefault(key, []).append(row)

    suggestions: list[dict] = []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        evidence_ids = [_clean(m.get("id")) for m in members if _clean(m.get("id"))]
        if len(evidence_ids) < 2:
            continue
        titles = [_clean(m.get("title")) for m in members if _clean(m.get("title"))]
        suggested_title = _suggested_title(key, titles)
        suggestions.append(
            {
                "suggested_id": f"project:{key}",
                "suggested_title": suggested_title,
                "kind": "work",
                "visibility": "private",
                "summary": "; ".join(titles[:3]),
                "evidence_ids": evidence_ids,
                "origin": "resume_parse",
            }
        )
    return suggestions


def _suggested_title(key: str, titles: list[str]) -> str:
    """A readable project title from the group key / member titles."""
    acronym = key.upper() if key.isalpha() and len(key) <= 5 else key.title()
    return f"{acronym} Project"

