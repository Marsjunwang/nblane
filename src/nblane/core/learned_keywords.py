"""Learned-keyword store for adaptive gap matching.

When the LLM identifies relevant skill nodes for a task, it
also outputs keywords that link the task to each node. These
keywords are persisted per-schema so that future rule-based
matching benefits from accumulated LLM feedback.

Storage: ``schemas/.learned/{schema_name}.yaml``
Format::

    vlm_robot:
      - vla控制
      - vla control
      - rt2复现
      - rt2 reproduction
    diffusion_policy:
      - 扩散策略
      - diffusion strategy

LLM outputs bilingual pairs (``中文/english``); the parser
expands each pair into separate entries so both languages
contribute to token matching.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from nblane.core.paths import SCHEMAS_DIR

MAX_LEARNED_KEYWORDS: int = 100

_LEARNED_DIR: Path = SCHEMAS_DIR / ".learned"


def _learned_path(schema_name: str) -> Path:
    """Return sidecar file path for a schema."""
    return _LEARNED_DIR / f"{schema_name}.yaml"


def load(schema_name: str) -> dict[str, list[str]]:
    """Load learned keywords for *schema_name*.

    Returns ``{node_id: [keyword, ...]}`` or empty dict.
    """
    path = _learned_path(schema_name)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        return {}
    result: dict[str, list[str]] = {}
    for nid, kws in raw.items():
        if isinstance(kws, list):
            result[nid] = [str(k) for k in kws]
    return result


def save(
    schema_name: str,
    data: dict[str, list[str]],
) -> None:
    """Write learned keywords to disk."""
    _LEARNED_DIR.mkdir(parents=True, exist_ok=True)
    body = yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=True,
    )
    _learned_path(schema_name).write_text(
        body, encoding="utf-8"
    )


def merge(
    schema_name: str,
    new_keywords: dict[str, list[str]],
    limit: int = MAX_LEARNED_KEYWORDS,
) -> dict[str, list[str]]:
    """Merge *new_keywords* into the existing store.

    Per-node keyword count is capped at *limit*; newest
    entries are kept when the cap is exceeded.
    Returns the merged result (also persisted to disk).
    """
    existing = load(schema_name)
    for nid, kws in new_keywords.items():
        old = existing.get(nid, [])
        seen = set(old)
        for kw in kws:
            kw = kw.strip()
            if kw and kw not in seen:
                old.append(kw)
                seen.add(kw)
        if len(old) > limit:
            old = old[-limit:]
        existing[nid] = old
    save(schema_name, existing)
    return existing


def _expand_bilingual(raw: str) -> list[str]:
    """Split a bilingual token like ``中文/english`` into parts.

    Also handles ``english/中文``, ``中文(english)``, and
    plain single-language tokens. Returns all non-empty
    fragments.
    """
    raw = raw.strip().strip("`").strip()
    if not raw:
        return []
    parts: list[str] = []
    for seg in re.split(r"[/／]", raw):
        seg = seg.strip().strip("()（）").strip()
        if seg:
            parts.append(seg)
    if len(parts) <= 1:
        m = re.match(r"^(.+?)[（(](.+?)[)）]$", raw)
        if m:
            parts = [
                m.group(1).strip(),
                m.group(2).strip(),
            ]
    return [p for p in parts if p]


def keywords_dict_from_router_payload(
    raw: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Expand router JSON keyword lists for :func:`merge`.

    Each phrase may use bilingual ``中文/english`` pairs;
    fragments are produced via :func:`_expand_bilingual`.
    """
    out: dict[str, list[str]] = {}
    for nid, phrases in raw.items():
        if not isinstance(phrases, list):
            continue
        acc: list[str] = []
        for phrase in phrases:
            if not isinstance(phrase, str):
                continue
            phrase = phrase.strip()
            if not phrase:
                continue
            acc.extend(_expand_bilingual(phrase))
        if acc:
            out[str(nid)] = acc
    return out


def parse_llm_keywords(
    text: str,
) -> dict[str, list[str]]:
    """Extract ``node_id: kw1, kw2, ...`` lines from LLM output.

    Looks for a section headed by ``**Keywords**`` (or
    ``**关键词**``) and parses lines that look like::

        node_id: 中文/english, 中文2/english2

    Bilingual pairs separated by ``/`` are expanded into
    individual keywords so both languages match.
    """
    result: dict[str, list[str]] = {}
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if "keyword" in lower or "关键词" in stripped:
            in_section = True
            continue
        if in_section and stripped.startswith("**"):
            break
        if in_section and stripped.startswith("#"):
            break
        if not in_section:
            continue
        match = re.match(
            r"^[-*\d.)\s]*`?([a-z][a-z0-9_]*)`?"
            r"\s*[:：]\s*(.+)$",
            stripped,
        )
        if match is None:
            continue
        nid = match.group(1)
        raw_kws = match.group(2)
        kws: list[str] = []
        for token in re.split(r"[,，;；、]", raw_kws):
            kws.extend(_expand_bilingual(token))
        if kws:
            result[nid] = kws
    return result
