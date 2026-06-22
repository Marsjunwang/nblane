"""Evidence duplicate detection + merge/deprecate (suggest-and-confirm).

Pure functions (no Streamlit). Detection never writes; callers persist after the
user confirms. Two tiers:

- ``find_duplicate_candidates`` — deterministic and always available: exact
  normalized title, shared kanban task id, shared original_content_hash, and
  token overlap (CJK bigrams + latin words). Cheap; safe to run on every render.
- ``suggest_duplicates_ai`` — one LLM pass that clusters cross-language
  same-work rows (Chinese kanban titles vs English manual titles) that token
  overlap cannot bridge. Slow; run only behind an explicit user action.

Both return the same candidate shape::

    {"a": <id>, "b": <id>, "score": float, "reason": str, "recommend_keep": <id>}
"""

from __future__ import annotations

import re
from typing import Any

# Token-overlap threshold for a deterministic candidate. Cross-language pairs
# score near 0 here (handled by the AI pass); this catches same-language and
# near-identical rows.
_OVERLAP_THRESHOLD = 0.45


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _norm_title(text: str) -> str:
    return " ".join(_clean(text).lower().split())


def _kanban_task_id(row: dict) -> str:
    for ref in row.get("kanban_refs") or []:
        s = _clean(ref)
        if s.startswith("kanban:"):
            return s.split(":", 1)[1]
    o = _clean(row.get("origin_ref"))
    if o.startswith("kanban:"):
        return o.split(":", 1)[1]
    return ""


def _tokens(row: dict) -> set[str]:
    blob = " ".join(
        _clean(row.get(k))
        for k in ("title", "summary", "original_content", "formatted_content")
    )
    cjk = re.findall(r"[一-鿿]", blob)
    bigrams = {cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1)}
    words = {w.lower() for w in re.findall(r"[A-Za-z]{3,}", blob)}
    return bigrams | words


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _provenance_score(row: dict) -> int:
    """Higher = keep. Prefer rows with more provenance / fuller content."""
    score = 0
    if _kanban_task_id(row):
        score += 4
    if _clean(row.get("origin")):
        score += 1
    score += min(len(_clean(row.get("original_content"))) // 200, 5)
    score += min(len(_clean(row.get("formatted_content"))) // 200, 3)
    if _clean(row.get("review_status")) == "reviewed":
        score += 2
    if [r for r in (row.get("project_refs") or []) if _clean(r)]:
        score += 1
    return score


def _recommend_keep(a: dict, b: dict) -> str:
    """Return the id of the row to keep (richer provenance wins; tie -> a)."""
    sa, sb = _provenance_score(a), _provenance_score(b)
    if sb > sa:
        return _clean(b.get("id"))
    return _clean(a.get("id"))


def _active(rows: list[dict]) -> list[dict]:
    return [
        r
        for r in rows
        if isinstance(r, dict)
        and not r.get("deprecated")
        and _clean(r.get("id"))
    ]


def find_duplicate_candidates(
    rows: list[dict],
    *,
    focus_id: str | None = None,
    threshold: float = _OVERLAP_THRESHOLD,
) -> list[dict]:
    """Deterministic duplicate candidate pairs among active rows.

    When *focus_id* is given, only pairs involving that row are returned.
    Each unordered pair is reported once. Strongest signal wins the reason.
    """
    active = _active(rows)
    by_id = {_clean(r.get("id")): r for r in active}
    focus = _clean(focus_id) if focus_id else ""
    if focus and focus not in by_id:
        return []

    title_index: dict[str, list[str]] = {}
    task_index: dict[str, list[str]] = {}
    hash_index: dict[str, list[str]] = {}
    tokens: dict[str, set[str]] = {}
    for r in active:
        rid = _clean(r.get("id"))
        title_index.setdefault(_norm_title(r.get("title")), []).append(rid)
        tid = _kanban_task_id(r)
        if tid:
            task_index.setdefault(tid, []).append(rid)
        h = _clean(r.get("original_content_hash"))
        if h:
            hash_index.setdefault(h, []).append(rid)
        tokens[rid] = _tokens(r)

    seen: set[tuple[str, str]] = set()
    out: list[dict] = []

    def _emit(id_a: str, id_b: str, score: float, reason: str) -> None:
        if id_a == id_b:
            return
        if focus and focus not in (id_a, id_b):
            return
        key = tuple(sorted((id_a, id_b)))
        if key in seen:
            return
        seen.add(key)
        a, b = by_id[id_a], by_id[id_b]
        out.append(
            {
                "a": id_a,
                "b": id_b,
                "score": round(score, 2),
                "reason": reason,
                "recommend_keep": _recommend_keep(a, b),
            }
        )

    # Strong signals first.
    for ids in task_index.values():
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                _emit(ids[i], ids[j], 1.0, "same_kanban_task")
    for ids in hash_index.values():
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                _emit(ids[i], ids[j], 1.0, "same_original_content")
    for ids in title_index.values():
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                _emit(ids[i], ids[j], 0.95, "same_title")

    # Token overlap (same-language near-duplicates).
    ids = list(by_id)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            score = _jaccard(tokens[ids[i]], tokens[ids[j]])
            if score >= threshold:
                _emit(ids[i], ids[j], score, "high_overlap")

    out.sort(key=lambda c: c["score"], reverse=True)
    return out


def merge_rows(kept: dict, other: dict, *, fields: list[str] | None = None) -> dict:
    """Return a copy of *kept* with non-empty *fields* from *other* filled in.

    Only fills fields that are empty on *kept* (never overwrites). When *fields*
    is None, no field copy happens (pure deprecate path). List fields are unioned.
    """
    out = dict(kept)
    for key in fields or []:
        kept_val = out.get(key)
        other_val = other.get(key)
        if isinstance(kept_val, list) or isinstance(other_val, list):
            merged = list(kept_val or [])
            for item in other_val or []:
                if item not in merged:
                    merged.append(item)
            if merged:
                out[key] = merged
            continue
        if not _clean(kept_val) and _clean(other_val):
            out[key] = other_val
    return out


def apply_merge_or_deprecate(
    rows: list[dict],
    *,
    keep_id: str,
    other_id: str,
    merge_fields: list[str] | None = None,
) -> tuple[list[dict], bool]:
    """Deprecate *other_id* (replaced_by=keep_id); optionally merge fields first.

    Returns (new_rows, changed). Non-destructive: the other row is flagged
    deprecated, not removed, so the action is reversible.
    """
    keep_id = _clean(keep_id)
    other_id = _clean(other_id)
    if not keep_id or not other_id or keep_id == other_id:
        return rows, False
    by_id = {_clean(r.get("id")): i for i, r in enumerate(rows) if isinstance(r, dict)}
    if keep_id not in by_id or other_id not in by_id:
        return rows, False
    new_rows = [dict(r) if isinstance(r, dict) else r for r in rows]
    kept = new_rows[by_id[keep_id]]
    other = new_rows[by_id[other_id]]
    if merge_fields:
        new_rows[by_id[keep_id]] = merge_rows(kept, other, fields=merge_fields)
    other["deprecated"] = True
    other["replaced_by"] = keep_id
    return new_rows, True


# --- AI-assisted cross-language clustering (on demand, slow) ----------------


def _ai_system_prompt() -> str:
    return (
        "你是证据去重助手。下面是同一个人的工作证据池。有些条目其实是**同一项工作**，"
        "只是来自不同录入管道（manual_daily 手动 / resume_parse 简历 / "
        "kanban_task 看板沉淀），标题语言（中/英）和措辞不同，但描述的是同一件事。\n"
        "请对比 title 与 content，把描述**同一项工作**的条目聚成一组。\n"
        "宁可谨慎：只在有把握是同一件事时才聚类，不确定就不聚。\n"
        '只输出 JSON：{"clusters":[{"ids":["..."],'
        '"reason":"为什么是同一件事","recommend_keep":"<id>"}]}。'
        "只返回含 2 个及以上 id 的组。"
    )


def _ai_compact_rows(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for r in _active(rows):
        out.append(
            {
                "id": _clean(r.get("id")),
                "origin": _clean(r.get("origin")),
                "title": _clean(r.get("title"))[:120],
                "content": (
                    _clean(r.get("summary"))
                    + " "
                    + _clean(r.get("original_content"))
                ).strip()[:320],
            }
        )
    return out


def clusters_to_pairs(clusters: list[dict], rows: list[dict]) -> list[dict]:
    """Flatten AI clusters into the standard pairwise candidate shape."""
    by_id = {_clean(r.get("id")): r for r in _active(rows)}
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for c in clusters or []:
        ids = [
            _clean(i) for i in (c.get("ids") or []) if _clean(i) in by_id
        ]
        if len(ids) < 2:
            continue
        keep = _clean(c.get("recommend_keep"))
        if keep not in ids:
            # fall back to provenance-based pick across the cluster
            keep = max(ids, key=lambda i: _provenance_score(by_id[i]))
        reason = _clean(c.get("reason")) or "ai_same_work"
        # Emit each non-keep id paired with the keep id.
        for other in ids:
            if other == keep:
                continue
            key = tuple(sorted((keep, other)))
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "a": keep,
                    "b": other,
                    "score": 0.9,
                    "reason": f"ai: {reason}"[:120],
                    "recommend_keep": keep,
                }
            )
    return out


def suggest_duplicates_ai(rows: list[dict]) -> tuple[list[dict], str | None]:
    """One LLM clustering pass over the pool. Returns (pairs, error).

    Slow (full-pool prompt). Call only behind an explicit user action. Falls
    back gracefully: on any failure returns ([], error) and the caller can use
    the deterministic candidates instead.
    """
    import json

    from nblane.core import llm as llm_client
    from nblane.core.jsonutil import extract_json_object

    if not llm_client.is_configured():
        return [], "LLM not configured"
    compact = _ai_compact_rows(rows)
    if len(compact) < 2:
        return [], None
    user = "证据池：\n" + json.dumps(compact, ensure_ascii=False)
    reply = llm_client.chat(_ai_system_prompt(), user, temperature=0.1)
    if reply.startswith("LLM error:") or reply.startswith(
        "AI features not configured"
    ):
        return [], reply
    data = extract_json_object(reply)
    if data is None:
        return [], "Could not parse duplicate clusters from LLM."
    return clusters_to_pairs(data.get("clusters") or [], rows), None
