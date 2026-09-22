"""Skill-link suggestions: which skill nodes should cite a piece of text.

Tiered capability (Phase 1 evidence page; designed for reuse by later phases
— task->project suggestions, openclaw corpus tagging):

1. ``embedding`` — when ``LLM_EMBEDDING_MODEL`` is set (any OpenAI-compatible
   ``/embeddings`` endpoint reusing ``LLM_BASE_URL``/``LLM_API_KEY``), skill
   node texts (label + category) are embedded once and cached under
   ``profiles/<name>/.cache/skill-embeddings.json``; the query text is
   embedded live and ranked by cosine similarity.
2. ``llm`` — with only chat configured, one chat call ranks all candidate
   nodes at once (schema trees are ~80 nodes, well inside one prompt).
3. ``rule`` — deterministic keyword/synonym overlap via ``gap.score_nodes``;
   always available, no network.

Every tier returns the same shape so callers never care which ran.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from nblane.core import io as io_facade
from nblane.core import llm as llm_client
from nblane.core.io import schema_node_index

_CACHE_FILENAME = "skill-embeddings.json"
_MAX_TEXT_CHARS = 4000


def _clean(value: object) -> str:
    return str(value or "").strip()


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _candidate_nodes(profile: str | Path) -> tuple[str, dict[str, dict[str, Any]]]:
    """Return (schema_name, node_id -> {label, category, level, text})."""
    tree = io_facade.load_skill_tree_raw(profile) or {}
    schema_name = _clean(tree.get("schema"))
    if not schema_name:
        return "", {}
    schema_raw = io_facade.load_schema_raw(schema_name)
    if not isinstance(schema_raw, dict):
        return schema_name, {}
    out: dict[str, dict[str, Any]] = {}
    for nid, meta in schema_node_index(schema_raw).items():
        label = _clean(meta.get("label")) or nid
        category = _clean(meta.get("category"))
        try:
            level = int(meta.get("level", 0) or 0)
        except (TypeError, ValueError):
            level = 0
        text = f"{label} — {category}" if category else label
        out[nid] = {
            "label": label,
            "category": category,
            "level": level,
            "text": text,
        }
    return schema_name, out


def _embedding_model() -> str:
    return os.getenv("LLM_EMBEDDING_MODEL", "").strip()


def _embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Embed *texts* via the configured embedding endpoint; None on failure."""
    model = _embedding_model()
    if not model or not llm_client.is_configured():
        return None
    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=llm_client.base_url(),
            api_key=llm_client.api_key_unmasked(),
            timeout=llm_client.timeout_seconds(),
        )
        response = client.embeddings.create(model=model, input=texts)
        return [list(item.embedding) for item in response.data]
    except Exception:  # noqa: BLE001 - any provider failure falls back a tier
        return None


def _cache_path(profile: str | Path) -> Path:
    pdir = profile if isinstance(profile, Path) else io_facade.profile_dir(profile)
    return Path(pdir) / ".cache" / _CACHE_FILENAME


def _skill_embedding_cache(
    profile: str | Path,
    nodes: dict[str, dict[str, Any]],
) -> dict[str, list[float]] | None:
    """Return node_id -> embedding, using the on-disk cache when fresh.

    Cache entries are keyed by (model, node text hash) so schema edits only
    re-embed the changed nodes. Returns None when embeddings are unavailable
    (caller falls back to the LLM/rule tiers).
    """
    model = _embedding_model()
    if not model:
        return None
    path = _cache_path(profile)
    cached: dict[str, Any] = {}
    if path.exists():
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cached = {}
    if cached.get("model") != model or not isinstance(cached.get("nodes"), dict):
        cached = {"model": model, "nodes": {}}
    cache_nodes: dict[str, Any] = cached["nodes"]

    missing_ids: list[str] = []
    vectors: dict[str, list[float]] = {}
    for nid, meta in nodes.items():
        entry = cache_nodes.get(nid)
        if (
            isinstance(entry, dict)
            and entry.get("text_hash") == _text_hash(meta["text"])
            and isinstance(entry.get("vector"), list)
        ):
            vectors[nid] = entry["vector"]
        else:
            missing_ids.append(nid)
    if missing_ids:
        fresh = _embed_texts([nodes[nid]["text"] for nid in missing_ids])
        if fresh is None or len(fresh) != len(missing_ids):
            return None
        for nid, vector in zip(missing_ids, fresh):
            cache_nodes[nid] = {
                "text_hash": _text_hash(nodes[nid]["text"]),
                "vector": vector,
            }
            vectors[nid] = vector
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(cached, ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass  # cache is an optimization; never fail the suggestion
    return vectors


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)


def _suggestion(
    nid: str,
    meta: dict[str, Any],
    score: float,
    source: str,
) -> dict[str, Any]:
    return {
        "id": nid,
        "label": meta.get("label") or nid,
        "category": meta.get("category") or "",
        "level": int(meta.get("level") or 0),
        "score": round(float(score), 4),
        "source": source,
    }


def _llm_rank(
    text: str,
    nodes: dict[str, dict[str, Any]],
    top_n: int,
) -> list[str] | None:
    """One chat call ranking every candidate; returns ordered ids or None."""
    if not llm_client.is_configured():
        return None
    catalog = "\n".join(
        f"- {nid}: {meta['label']} ({meta['category'] or 'uncategorized'})"
        for nid, meta in nodes.items()
    )
    if llm_client.reply_language() == "zh":
        system = (
            "你是技能树关联助手。给定一条证据文本和技能节点目录，"
            "选出与该证据最相关的技能节点。\n"
            f"严格要求：只输出 JSON：{{\"skill_ids\": [..]}}，"
            "按相关度降序，最多 "
            f"{top_n} 个；id 必须原样来自目录；不要输出任何其他文字。"
        )
        user = f"证据文本：\n{text}\n\n技能节点目录：\n{catalog}"
    else:
        system = (
            "You link evidence to skill-tree nodes. Given an evidence text "
            "and a catalog of skill nodes, pick the most relevant nodes.\n"
            "Strict: output only JSON {\"skill_ids\": [...]}, most relevant "
            f"first, at most {top_n}; ids must be copied verbatim from the "
            "catalog; no other text."
        )
        user = f"Evidence text:\n{text}\n\nSkill node catalog:\n{catalog}"
    reply = llm_client.chat(system, user, temperature=0.0)
    if reply.startswith(("LLM error:", "AI features not configured")):
        return None
    from nblane.core.profile_ingest_llm import extract_json_object

    data = extract_json_object(reply)
    if not isinstance(data, dict):
        return None
    raw_ids = data.get("skill_ids")
    if not isinstance(raw_ids, list):
        return None
    out: list[str] = []
    for item in raw_ids:
        nid = _clean(item)
        if nid and nid in nodes and nid not in out:
            out.append(nid)
    return out or None


def suggest_skills_for_text(
    profile: str | Path,
    text: str,
    *,
    top_n: int = 5,
    exclude_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Rank skill nodes for *text*; returns {backend, suggestions, error}.

    Tiers run embedding -> llm -> rule; the first tier that produces a
    ranking wins. ``exclude_ids`` (e.g. already-linked nodes) are filtered
    from every tier's output.
    """
    query = _clean(text)[:_MAX_TEXT_CHARS]
    _, nodes = _candidate_nodes(profile)
    excluded = {_clean(i) for i in (exclude_ids or []) if _clean(i)}
    candidates = {nid: m for nid, m in nodes.items() if nid not in excluded}
    empty = {"backend": "none", "suggestions": [], "error": None}
    if not query or not candidates:
        return empty

    # Tier 1: cached skill embeddings + live query embedding.
    vectors = _skill_embedding_cache(profile, candidates)
    if vectors:
        query_vec = _embed_texts([query])
        if query_vec:
            scored = sorted(
                (
                    (nid, _cosine(query_vec[0], vec))
                    for nid, vec in vectors.items()
                ),
                key=lambda item: item[1],
                reverse=True,
            )[:top_n]
            return {
                "backend": "embedding",
                "suggestions": [
                    _suggestion(nid, candidates[nid], score, "embedding")
                    for nid, score in scored
                ],
                "error": None,
            }

    # Tier 2: single chat-call ranking of all candidates.
    ranked_ids = _llm_rank(query, candidates, top_n)
    if ranked_ids:
        return {
            "backend": "llm",
            "suggestions": [
                _suggestion(nid, candidates[nid], float(top_n - i), "llm")
                for i, nid in enumerate(ranked_ids[:top_n])
            ],
            "error": None,
        }

    # Tier 3: deterministic rule overlap (no network).
    tree = io_facade.load_skill_tree_raw(profile) or {}
    schema_name = _clean(tree.get("schema"))
    schema_raw = io_facade.load_schema_raw(schema_name) if schema_name else None
    if isinstance(schema_raw, dict):
        from nblane.core import gap as gap_mod
        from nblane.core import learned_keywords as lk_store

        ranked = gap_mod.score_nodes(
            query, schema_raw, learned=lk_store.load(schema_name)
        )
        suggestions = [
            _suggestion(nid, candidates[nid], float(score), "rule")
            for nid, score in ranked
            if nid in candidates
        ][:top_n]
        if suggestions:
            return {"backend": "rule", "suggestions": suggestions, "error": None}
    return {
        "backend": "none",
        "suggestions": [],
        "error": "no suggestion tier produced a ranking",
    }


def suggest_skills_for_evidence(
    profile: str | Path,
    row: dict[str, Any],
    *,
    top_n: int = 5,
) -> dict[str, Any]:
    """Suggest skill links for one evidence-pool row.

    Text signal: title + summary + original/formatted content + excerpt.
    Already-linked nodes (via ``evidence_usage_index``) are excluded.
    """
    from nblane.core.evidence_review import evidence_usage_index

    parts = [
        _clean(row.get("title")),
        _clean(row.get("summary")),
        _clean(row.get("original_content")),
        _clean(row.get("formatted_content")),
        _clean(row.get("source_excerpt")),
    ]
    text = "\n".join(part for part in parts if part)
    eid = _clean(row.get("id"))
    linked = []
    if eid:
        linked = [item["id"] for item in evidence_usage_index(profile).get(eid, [])]
    return suggest_skills_for_text(
        profile, text, top_n=top_n, exclude_ids=linked
    )
