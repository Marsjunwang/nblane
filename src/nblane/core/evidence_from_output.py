"""Output -> evidence: turn a published/draft output into an evidence row.

Pure function (no Streamlit). The caller persists the proposal. Output rows are
loosely-typed YAML dicts (see public_site.load_outputs); read defensively.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nblane.core import llm as llm_client
from nblane.core.evidence_migrate import content_hash, detect_language

# Map an output "target"/"type" to an evidence proof category. Unknown targets
# fall back to "practice"; the enum is intentionally not expanded here.
_TARGET_TO_TYPE = {
    "blog": "practice",
    "resume": "practice",
    "project_update": "project",
    "project": "project",
    "paper": "paper",
}

# Preserve a compact slice of the output body so original_content stays useful
# without copying an entire long-form post into the pool.
_BODY_PREVIEW_CHARS = 100
_BLOG_BODY_PREVIEW_CHARS = 2000


def _clean(value: Any) -> str:
    return str(value or "").strip()


def evidence_source_key(row: dict) -> tuple[str, str] | None:
    """Return the canonical ``(origin, origin_ref)`` key for a row.

    Empty legacy rows do not have a canonical source key yet and return None.
    New flows should always set both fields before saving.
    """
    origin = _clean(row.get("origin"))
    origin_ref = _clean(row.get("origin_ref"))
    if not origin or not origin_ref:
        return None
    return origin, origin_ref


def active_source_index(entries: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """Map canonical source key -> active evidence rows."""
    out: dict[tuple[str, str], list[dict]] = {}
    for row in entries:
        if not isinstance(row, dict) or bool(row.get("deprecated", False)):
            continue
        key = evidence_source_key(row)
        if key is None:
            continue
        out.setdefault(key, []).append(row)
    return out


def find_active_by_source(
    entries: list[dict],
    origin: str,
    origin_ref: str,
) -> dict | None:
    """Return the active evidence row for one canonical source, if unique."""
    rows = active_source_index(entries).get((_clean(origin), _clean(origin_ref))) or []
    return rows[0] if len(rows) == 1 else None


def _output_original_content(output: dict) -> str:
    """Compose a meta header + short body preview as the preserved source."""
    lines: list[str] = []
    for label, key in (
        ("Output id", "id"),
        ("Title", "title"),
        ("Target", "target"),
        ("Type", "type"),
        ("Status", "status"),
        ("Path", "path"),
        ("Route", "route"),
        ("Created", "created_at"),
        ("Year", "year"),
    ):
        val = _clean(output.get(key))
        if val:
            lines.append(f"{label}: {val}")
    summary = _clean(output.get("summary"))
    if summary:
        lines.append("")
        lines.append(f"Summary: {summary}")
    body = _clean(output.get("body"))
    if body:
        preview = body[:_BODY_PREVIEW_CHARS]
        suffix = "…" if len(body) > _BODY_PREVIEW_CHARS else ""
        lines.append("")
        lines.append("Body preview:")
        lines.append(f"{preview}{suffix}")
    return "\n".join(lines).strip()


def evidence_row_from_output(
    output: dict,
    *,
    profile: str | Path = "",
    existing_ids: set[str] | None = None,
    target_lang: str | None = None,
) -> dict:
    """Build a v2 evidence row dict from one output record.

    - id is ``out_<output_id>`` with a stable numeric suffix on collision.
    - origin/origin_ref/origin_detail mark the output provenance.
    - original_content preserves output meta + a short body preview.
    - project_refs are inherited from the output.
    - review_status defaults to needs_review; public_readiness never auto-published.
    """
    existing_ids = set(existing_ids or set())
    target_lang = (target_lang or llm_client.reply_language() or "en").strip()
    target_lang = "zh" if target_lang == "zh" else "en"

    output_id = _clean(output.get("id")) or "output"
    base_id = f"out_{output_id}"
    eid = base_id
    suffix = 2
    while eid in existing_ids:
        eid = f"{base_id}_{suffix}"
        suffix += 1

    target = _clean(output.get("target")).lower()
    otype = _clean(output.get("type")).lower()
    ev_type = (
        _TARGET_TO_TYPE.get(target)
        or _TARGET_TO_TYPE.get(otype)
        or "practice"
    )

    original_content = _output_original_content(output)
    title = _clean(output.get("title")) or output_id
    summary = _clean(output.get("summary"))

    detail_bits = [b for b in (target or otype, _clean(output.get("path")), _clean(output.get("created_at"))) if b]
    origin_detail = "Output: " + " · ".join(detail_bits) if detail_bits else "Output"

    project_refs = [
        _clean(r) for r in (output.get("project_refs") or []) if _clean(r)
    ]

    row: dict = {
        "id": eid,
        "type": ev_type,
        "title": title,
        "origin": "output",
        "origin_ref": f"output:{output_id}",
        "origin_detail": origin_detail,
        "original_content": original_content,
        "original_content_hash": content_hash(original_content),
        "original_language": detect_language(original_content),
        "language": target_lang,
        "review_status": "needs_review",
        "public_readiness": "private",
    }
    if summary:
        row["summary"] = summary
        row["formatted_content"] = summary
    if project_refs:
        row["project_refs"] = project_refs
    date = (
        _clean(output.get("date"))
        or _clean(output.get("created_at"))
        or _clean(output.get("year"))
    )
    if date:
        row["date"] = date
    url = _clean(output.get("url"))
    if url:
        row["url"] = url
    return row


def _blog_original_content(post: Any) -> str:
    """Compose a compact source snapshot for a public blog post."""
    lines: list[str] = []
    for label, value in (
        ("Blog route", getattr(post, "route", "")),
        ("Title", getattr(post, "title", "")),
        ("Status", getattr(post, "status", "")),
        ("Date", getattr(post, "date", "")),
        ("Path", getattr(post, "path", "")),
    ):
        val = _clean(value)
        if val:
            lines.append(f"{label}: {val}")
    summary = _clean(getattr(post, "summary", ""))
    if summary:
        lines.append("")
        lines.append(f"Summary: {summary}")
    body = _clean(getattr(post, "body", ""))
    if body:
        preview = body[:_BLOG_BODY_PREVIEW_CHARS]
        suffix = "..." if len(body) > _BLOG_BODY_PREVIEW_CHARS else ""
        lines.append("")
        lines.append("Body preview:")
        lines.append(f"{preview}{suffix}")
    return "\n".join(lines).strip()


def evidence_row_from_blog_post(
    post: Any,
    *,
    project_refs: list[str],
    profile: str | Path = "",
    existing_ids: set[str] | None = None,
    target_lang: str | None = None,
) -> dict:
    """Build a v2 evidence row from one public blog post.

    The canonical source is the public document itself:
    ``origin=output`` and ``origin_ref=blog:<route>``.
    """
    existing_ids = set(existing_ids or set())
    target_lang = (target_lang or llm_client.reply_language() or "en").strip()
    target_lang = "zh" if target_lang == "zh" else "en"

    route = _clean(getattr(post, "route", "")) or _clean(getattr(post, "slug", "blog"))
    slug = route.replace("/", "_") or "blog"
    base_id = f"blog_{slug}"
    eid = base_id
    suffix = 2
    while eid in existing_ids:
        eid = f"{base_id}_{suffix}"
        suffix += 1

    original_content = _blog_original_content(post)
    title = _clean(getattr(post, "title", "")) or route
    summary = _clean(getattr(post, "summary", ""))
    status = _clean(getattr(post, "status", ""))
    path = _clean(getattr(post, "path", ""))
    date = _clean(getattr(post, "date", ""))
    row: dict = {
        "id": eid,
        "type": "practice",
        "title": title,
        "origin": "output",
        "origin_ref": f"blog:{route}",
        "origin_detail": "Blog: " + " · ".join(
            bit for bit in (status, path) if bit
        )
        if status or path
        else "Blog",
        "original_content": original_content,
        "original_content_hash": content_hash(original_content),
        "original_language": detect_language(original_content),
        "language": target_lang,
        "review_status": "needs_review",
        "public_readiness": "private",
        "project_refs": [_clean(r) for r in project_refs if _clean(r)],
    }
    if summary:
        row["summary"] = summary
        row["formatted_content"] = summary
    if date:
        row["date"] = date
    url_path = _clean(getattr(post, "url_path", ""))
    if url_path:
        row["url"] = "/" + url_path.lstrip("/")
    return row
