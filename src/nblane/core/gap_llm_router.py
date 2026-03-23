"""LLM-assisted routing from task text to schema node ids.

Returns structured JSON with ``node_ids`` and per-node ``keywords``
for persistence via ``learned_keywords.merge``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from nblane.core import llm as llm_client
from nblane.core.jsonutil import extract_json_object


@dataclass
class RouterOutcome:
    """Result of a single routing call."""

    ok: bool
    node_ids: list[str] = field(default_factory=list)
    keywords: dict[str, list[str]] = field(default_factory=dict)
    error: str | None = None


def _system_prompt_zh() -> str:
    """System prompt for routing (Chinese UI)."""
    return (
        "你是机器人技能树路由助手。用户会给出任务描述和一份"
        "允许的节点 id 与标签列表。\n"
        "你必须只输出一个 JSON 对象，不要 Markdown，不要其它文字。"
        "JSON 格式严格为：\n"
        '{"node_ids": ["id1", "id2"], '
        '"keywords": {"id1": ["短语或 中文/english", ...], ...}}\n'
        "规则：\n"
        "- node_ids 只能从给定列表中选，1–5 个，按与任务相关度排序。\n"
        "- 禁止编造列表中不存在的 id。\n"
        "- keywords 只写你选中的 node_ids 里的 id；每个 id 2–4 条，"
        "连接任务用语与该技能；中英用 中文/english 斜线格式。\n"
        "- 若无法判断，node_ids 可为 []，keywords 为 {}。"
    )


def _system_prompt_en() -> str:
    """System prompt for routing (English UI)."""
    return (
        "You route a robotics task to skill-tree node ids. "
        "You receive a task and an allowed list of node ids "
        "with labels.\n"
        "Reply with ONE JSON object only. No markdown, no prose.\n"
        "Schema: "
        '{"node_ids": ["id1"], '
        '"keywords": {"id1": ["phrase or zh/en pair", ...]}}\n'
        "Rules:\n"
        "- node_ids must be chosen only from the given list, "
        "1–5 entries, most relevant first.\n"
        "- Do not invent ids.\n"
        "- keywords: only for ids you selected; 2–4 phrases each, "
        "linking task wording to that skill; use zh/english "
        "slash pairs where bilingual.\n"
        "- If unsure, use empty arrays/objects."
    )


def _catalog_lines(
    index: dict[str, dict],
    max_nodes: int = 200,
) -> str:
    """Build compact id + label lines for the prompt."""
    lines: list[str] = []
    for i, nid in enumerate(sorted(index.keys())):
        if i >= max_nodes:
            lines.append("... (truncated)")
            break
        label = index[nid].get("label", nid)
        lines.append(f"- {nid}: {label}")
    return "\n".join(lines)


def route_task_to_nodes(
    task: str,
    schema_name: str,
    index: dict[str, dict],
) -> RouterOutcome:
    """Ask the LLM for node ids and optional keywords.

    On failure (missing key, parse error, API error), returns
    ``ok=False`` and empty ids so callers keep rule-only roots.
    """
    if not task.strip():
        return RouterOutcome(ok=False, error="empty task")
    if not llm_client.is_configured():
        return RouterOutcome(ok=False, error="LLM not configured")

    system = (
        _system_prompt_zh()
        if llm_client.reply_language() == "zh"
        else _system_prompt_en()
    )
    user = (
        f"Schema file: {schema_name}\n\n"
        f"Task:\n{task.strip()}\n\n"
        "Allowed nodes (id: label):\n"
        f"{_catalog_lines(index)}\n"
    )
    reply = llm_client.chat(system, user, temperature=0.2)
    if reply.startswith("LLM error:") or reply.startswith(
        "AI features not configured"
    ):
        return RouterOutcome(ok=False, error=reply)

    data = extract_json_object(reply)
    if data is None:
        return RouterOutcome(
            ok=False,
            error="Could not parse routing JSON from LLM.",
        )

    raw_ids = data.get("node_ids")
    if not isinstance(raw_ids, list):
        return RouterOutcome(
            ok=False,
            error="Invalid node_ids in routing JSON.",
        )
    node_ids = [
        str(x).strip()
        for x in raw_ids
        if isinstance(x, (str, int)) and str(x).strip()
    ]
    node_ids = [nid for nid in node_ids if nid in index]

    raw_kw = data.get("keywords")
    keywords: dict[str, list[str]] = {}
    if isinstance(raw_kw, dict):
        for k, v in raw_kw.items():
            nid = str(k).strip()
            if nid not in index:
                continue
            if not isinstance(v, list):
                continue
            phrases = [
                str(p).strip()
                for p in v
                if isinstance(p, (str, int)) and str(p).strip()
            ]
            if phrases:
                keywords[nid] = phrases

    if not node_ids and not keywords:
        return RouterOutcome(
            ok=True,
            node_ids=[],
            keywords={},
        )

    return RouterOutcome(
        ok=True,
        node_ids=node_ids,
        keywords=keywords,
    )
