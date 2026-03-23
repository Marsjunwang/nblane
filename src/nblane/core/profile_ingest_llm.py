"""LLM prompts for resume / kanban Done → structured ingest JSON."""

from __future__ import annotations

from nblane.core import llm as llm_client
from nblane.core.io import (
    load_evidence_pool_raw,
    load_schema_raw,
    load_skill_tree_raw,
    schema_node_index,
)
from nblane.core.jsonutil import extract_json_object
from nblane.core.models import KanbanTask
from nblane.core.profile_ingest import (
    pool_tree_summaries_for_prompt,
)


def _status_rubric_zh() -> str:
    """Shared Chinese rubric for learning vs solid (resume + kanban)."""
    return """
### status（写在 node_updates 的每条里，与 evidence_refs 指向同一节点）

不要对所有节点一律填 learning。请按**该节点所引用的证据**判断。

**solid** — 该节点所关联的证据中，**至少满足下面一条**即可标 solid（同一节点可综合多条 ref）：
1. **论文**：evidence_entries 里本条 type 为 paper；或 title/summary 写明期刊/会议/一作/通讯/已发表/arxiv 等可核验发表信息。
2. **开源或可复现成果**：summary/title 中出现 GitHub、GitLab、开源仓库、PR、release、对外开源、复现仓库、mainline 贡献等，能指向可查验的开源行为。
3. **非常明显的指标提升**：summary 中有可对比的量化结果（例如 AP、FPS、延迟 ms、准确率、相对基线 +X%、提升倍数、消融前后数字），且能说明**实质改进**，不是空泛形容词。

**learning** — 有可核验的项目/工程/课程/实践（type 常为 project/course/practice），但**不满足**上述任一条 solid 门槛时用 learning。

**locked** — 该节点在 node_updates 中**没有**挂任何 evidence_refs（且没有内联 evidence）时，或完全无法从文本建立映射时。

**expert** — **禁止**在 JSON 中出现 expert 字段取值；永远不要输出 expert。

**实操提示**：若某条证据 id 是 paper 类型，则依赖它支撑「论文阅读/发表/学术影响」类节点时优先 solid；纯工程项目若无论文、无开源描述、无数值亮点，用 learning 即可。
"""


def _status_rubric_en() -> str:
    """Shared English rubric for learning vs solid."""
    return """
### status (on each node_updates item, same node as evidence_refs)

Do not set every node to learning. Judge from the evidence rows referenced.

**solid** — At least one of the following holds for evidence attached to this node:
1. **Paper**: the linked evidence entry has type paper, or title/summary clearly indicates a published paper (venue, first author, arxiv, etc.).
2. **Open source / reproducible artifact**: summary or title mentions GitHub/GitLab, open-source repo, PR, release, reproducible codebase, or traceable OSS contribution.
3. **Strong quantitative gains**: summary contains comparable metrics (AP, FPS, latency, accuracy, +X% vs baseline, multi-fold improvement) showing substantive improvement, not vague claims.

**learning** — Verifiable project/course/practice work that does **not** meet any solid criterion above.

**locked** — Use when the node has no evidence_refs (and no inline evidence) in your patch, or you cannot map credibly.

**expert** — **Never** output expert in JSON.

**Hint**: If an evidence row is type paper, nodes mainly justified by that paper (e.g. publication-related skills) should often be solid; pure engineering delivery without paper/OSS/metrics stays learning.
"""


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


def _system_prompt_resume_zh() -> str:
    """System prompt: resume → JSON (Chinese UI)."""
    return (
        "你是职业规划与技能树助手。用户会粘贴简历或长文本，并给出"
        "允许的 schema 节点 id、当前证据池与技能树摘要。\n"
        "只输出一个 JSON 对象，不要 Markdown 围栏外的其它文字。\n"
        "顶层键：evidence_entries（数组）、node_updates（数组）。\n\n"
        "evidence_entries 每项字段：\n"
        "- id：推荐稳定短 id（如 ev_vla、ev_1），与下文 evidence_refs 字符串完全一致。\n"
        "- type：project | paper | course | practice（有论文或正式发表时务必用 paper）。\n"
        "- title、date、url、summary：summary 写清可核验要点，便于判断 solid。\n\n"
        "node_updates 每项：id（仅允许列表中的节点）、evidence_refs、"
        "可选 evidence、note、status。\n"
        "evidence_refs：引用本 JSON 里 evidence_entries 的 id；"
        "或用 first_1、ev_2 表示 evidence_entries 第 1、2 条（从 1 起）。\n\n"
        + _status_rubric_zh()
        + "\n若无把握，evidence_entries 与 node_updates 可为 []。"
    )


def _system_prompt_resume_en() -> str:
    """System prompt: resume → JSON (English UI)."""
    return (
        "You extract verifiable evidence from a resume or long text "
        "for a skill tree. Reply with ONE JSON object only. "
        "No markdown fences.\n"
        "Top-level keys: evidence_entries (array), node_updates (array).\n\n"
        "evidence_entries fields:\n"
        "- id: stable short id (e.g. ev_vla, ev_1), must match "
        "evidence_refs strings.\n"
        "- type: project | paper | course | practice (use paper when "
        "the resume describes a real publication).\n"
        "- title, date, url, summary: put verifiable details in summary "
        "to support solid vs learning.\n\n"
        "node_updates: id (allowed nodes only), evidence_refs, optional "
        "evidence, note, status.\n"
        "evidence_refs: same ids as evidence_entries, or first_1 / ev_2 "
        "meaning row index in evidence_entries (1-based).\n\n"
        + _status_rubric_en()
        + "\nUse empty arrays if mapping is unreliable."
    )


def _kanban_evidence_contract_zh() -> str:
    """Kanban-only rules so merge never drops refs (multi-task safe)."""
    return (
        "### 与池中已有证据的关系（防重复）\n\n"
        "- user 消息里的「Current evidence pool」是**磁盘上已有**的 id 与标题，"
        "**不是**要求你逐条复述或照抄的输入。\n"
        "- 若「已完成」任务对应的工作**与池中某条实为同一事实**，"
        "**不要**在 evidence_entries 里再写一行（即使换英文标题或缩写）；"
        "只在 node_updates 里用 evidence_refs **引用已有 id**（如 ev1、"
        "或池里列出的长 id）。\n"
        "- **仅当**本次任务包含池中**尚不存在**的新可核验事实时，"
        "才在 evidence_entries **追加**新行；否则 evidence_entries 可为 []，"
        "仅更新 node_updates 的引用。\n"
        "- 禁止用「改写标题 / 换语言」重复描述已在池中的项目，"
        "否则会产生合并无法去重的重复条目。\n\n"
        "### evidence_entries（看板硬性要求，避免合并丢引用）\n\n"
        "- 若追加新行：每条必须有**非空 title**；"
        "若无补充标题，用对应 Done 任务的 title。\n"
        "- 本 JSON 中 evidence_entries 的**书写顺序**即第 1、2、3… 条；"
        "若 evidence_entries 非空，可用 first_1 / ev_2 指这些新行。\n"
        "- node_updates 的 evidence_refs 允许："
        "（1）本 JSON 中 evidence_entries 新行的 id，或 first_1/ev_2；"
        "（2）**或** user 消息里 Current evidence pool 已列出的**已有 id**"
        "（勿在 evidence_entries 里重复写该行）。\n"
        "禁止引用既不在池中、也不在本 JSON evidence_entries 中的 id。\n"
        "- 多选「已完成」：若任务均可映射到已有池条目，"
        "evidence_entries 可为空，仅在 node_updates 挂引用。\n"
    )


def _kanban_evidence_contract_en() -> str:
    """Kanban-only evidence rules for stable merge."""
    return (
        "### Relationship to existing pool (avoid duplicates)\n\n"
        "- The \"Current evidence pool\" block lists **ids already on disk** — "
        "it is **not** a request to copy them into evidence_entries.\n"
        "- If a Done task describes the **same fact** as a pool row, "
        "**do not** add another evidence_entries row (even with a new English "
        "title). Put only that existing id in node_updates evidence_refs.\n"
        "- Add **new** evidence_entries rows only for facts **not** already "
        "in the pool; otherwise evidence_entries may be [] and only "
        "node_updates change.\n"
        "- Do not paraphrase pool items into new rows (merge dedup is "
        "exact title match).\n\n"
        "### evidence_entries (kanban — required for stable merge)\n\n"
        "- New rows: non-empty title; if missing, use the Done task title.\n"
        "- Row order is 1,2,3…; evidence_refs use ids from this array or "
        "first_1 / ev_2. You may also reference **existing pool ids** in "
        "node_updates without re-listing the row (see above).\n"
        "- Multiple Done tasks: if all map to existing pool rows, "
        "evidence_entries can be empty.\n"
    )


def _status_rubric_kanban_zh() -> str:
    """Stricter solid rules for kanban (resume keeps shared rubric)."""
    return (
        "### status（看板专用：solid 门槛严于简历）\n\n"
        "**solid** 仅当该节点所引证据**明确满足**下列至少一类"
        "（可核验、非空话），否则**一律 learning**：\n"
        "1. **论文**：对应 evidence type 为 paper，且 title/summary 含可核验"
        "发表信息（会议/期刊/arxiv/一作等），非泛泛「有论文」。\n"
        "2. **开源对外输出**：title/summary 含可复制的 GitHub/GitLab 链接或 "
        "`org/repo` 形式，或明确 PR/release；"
        "不包括「开源潜力」等无链接表述。\n"
        "3. **非常好的指标**：summary 含相对基线或前后对比的量化数字"
        "（如 +X% AP、latency A→B）；仅有「提升明显」等形容词不足 solid。\n\n"
        "Done 文本简短、主要靠推断时**默认 learning**；"
        "勿将本次任务无关的池内证据硬挂来抬状态。\n\n"
        "**learning**：有交付/复现/工程事实但未达上述 solid 门槛。\n"
        "**locked**：无 evidence_refs 且无内联 evidence。\n"
        "**expert**：禁止输出。\n"
    )


def _status_rubric_kanban_en() -> str:
    """Stricter solid rules for kanban ingest."""
    return (
        "### status (kanban only — stricter than resume)\n\n"
        "Use solid only when linked evidence clearly meets one of:\n"
        "1. **Paper**: type paper and verifiable venue/arxiv/first-author text.\n"
        "2. **Open-source artifact**: GitHub/GitLab URL or org/repo, or "
        "specific PR/release; not potential without a link.\n"
        "3. **Strong metrics**: explicit before/after or vs-baseline numbers; "
        "adjectives alone are not enough.\n\n"
        "Short Done text: default learning. "
        "Do not attach unrelated pool evidence to upgrade status.\n\n"
        "**learning**: real delivery but below the solid bar.\n"
        "**locked**: no refs / no inline evidence.\n"
        "**expert**: never output.\n"
    )


def _system_prompt_kanban_zh() -> str:
    """System prompt: Done tasks → JSON (Chinese UI)."""
    return (
        "你是技术复盘助手。用户给出看板「已完成」条目与允许的 schema、"
        "证据池与技能树摘要。\n"
        "只输出一个 JSON：evidence_entries、node_updates。\n"
        "node id 只能从允许列表选取。\n\n"
        "### 出处（必填）\n\n"
        "- evidence_entries 每项必须含 **source_excerpt**：从对应 Done 任务原文"
        "（title/context/outcome/notes/subtask）中**照抄或极短摘录**一两句，"
        "证明该条证据不是臆测。\n"
        "- node_updates 每项必须含 **rationale**（1–3 句）：说明为何更新该节点，"
        "并引用任务中的具体事实（可与 source_excerpt 呼应）。\n"
        "禁止空 rationale 或空 source_excerpt（若无把握则不要输出该条）。\n\n"
        + _kanban_evidence_contract_zh()
        + "\n"
        + _status_rubric_kanban_zh()
        + "\n无把握则 evidence_entries 与 node_updates 可为 []。"
    )


def _system_prompt_kanban_en() -> str:
    """System prompt: Done tasks → JSON (English UI)."""
    return (
        "You map completed kanban tasks to evidence and skill nodes. "
        "Output one JSON: evidence_entries, node_updates.\n"
        "Allowed node ids only.\n\n"
        "### Provenance (required)\n\n"
        "- Each evidence_entries item MUST include **source_excerpt**: "
        "a short literal quote from the Done task (title/context/outcome/"
        "notes/subtasks) proving the row is grounded.\n"
        "- Each node_updates item MUST include **rationale** (1–3 sentences): "
        "why this node changes, citing concrete task facts.\n"
        "Do not emit empty rationale or source_excerpt (omit the row if "
        "unsure).\n\n"
        + _kanban_evidence_contract_en()
        + "\n"
        + _status_rubric_kanban_en()
        + "\nReturn empty arrays if uncertain."
    )


def _append_ingest_user_reminder(body: str) -> str:
    """Reinforce status output at end of user message."""
    if llm_client.reply_language() == "zh":
        tail = (
            "\n\n【最后检查】node_updates 中凡含 evidence_refs 的条目必须"
            "填写 status。凡所引证据满足系统提示中的 solid 条件"
            "（论文 / 开源或强指标）则标 solid，否则 learning；"
            "不要把本应 solid 的节点全部写成 learning。"
        )
    else:
        tail = (
            "\n\nFinal check: every node_update with evidence_refs must "
            "include status. Use solid when the rubric says paper / OSS / "
            "strong metrics; otherwise learning. Do not default everything "
            "to learning."
        )
    return body + tail


def _append_kanban_user_reminder(body: str) -> str:
    """Reinforce kanban evidence ids and conservative solid."""
    if llm_client.reply_language() == "zh":
        tail = (
            "\n\n【看板最后检查】"
            "不要把池中已有证据再写进 evidence_entries；"
            "能复用则直接引用池中 id。"
            "新增行必须有 title；"
            "evidence_refs 可用本 JSON 新行 id、first_1/ev_2，"
            "或池中已有 id。"
            "status 默认 learning；"
            "仅当论文 / 含链接的开源输出 / 带基线对比的强指标时才 solid。"
        )
    else:
        tail = (
            "\n\nKanban final check: do not duplicate pool rows in "
            "evidence_entries; reuse existing pool ids in refs when the same "
            "work. New rows need titles. "
            "evidence_refs: new ids, first_1/ev_2, or existing pool ids. "
            "Default learning; solid only for paper / linked OSS / "
            "strong baseline-numbered metrics."
        )
    return body + tail


def _user_message_resume(
    resume_text: str,
    schema_name: str,
    index: dict[str, dict],
    pool_text: str,
    tree_text: str,
) -> str:
    """Build user message for resume ingest."""
    return (
        f"Schema file: {schema_name}\n\n"
        "Allowed nodes (id: label):\n"
        f"{_catalog_lines(index)}\n\n"
        "Current evidence pool (summary):\n"
        f"{pool_text}\n\n"
        "Current skill tree (summary):\n"
        f"{tree_text}\n\n"
        "Resume / long text:\n"
        f"{resume_text.strip()}\n"
    )


def _format_done_tasks(tasks: list[KanbanTask]) -> str:
    """Serialize Done tasks for the prompt (full structured context)."""
    lines: list[str] = []
    for t in tasks:
        lines.append(f"- title: {t.title}")
        if t.done:
            lines.append("  done: true")
        if t.context.strip():
            lines.append(f"  context: {t.context.strip()}")
        if t.why.strip():
            lines.append(f"  why: {t.why.strip()}")
        if t.outcome.strip():
            lines.append(f"  outcome: {t.outcome.strip()}")
        if t.blocked_by.strip():
            lines.append(f"  blocked_by: {t.blocked_by.strip()}")
        if t.started_on:
            lines.append(f"  started_on: {t.started_on}")
        if t.completed_on:
            lines.append(f"  completed_on: {t.completed_on}")
        for st in t.subtasks:
            mark = "x" if st.done else " "
            lines.append(f"  subtask [{mark}] {st.title}")
        if t.details:
            joined = "; ".join(t.details)
            lines.append(f"  notes: {joined}")
    return "\n".join(lines) if lines else "(no tasks)"


def _user_message_kanban(
    done_block: str,
    schema_name: str,
    index: dict[str, dict],
    pool_text: str,
    tree_text: str,
) -> str:
    """Build user message for kanban Done ingest."""
    return (
        f"Schema file: {schema_name}\n\n"
        "Allowed nodes (id: label):\n"
        f"{_catalog_lines(index)}\n\n"
        "Current evidence pool (summary — ids already stored; "
        "reuse these ids in evidence_refs when tasks refer to the same work, "
        "do not add duplicate evidence_entries rows unless the task states "
        "a genuinely new fact):\n"
        f"{pool_text}\n\n"
        "Current skill tree (summary):\n"
        f"{tree_text}\n\n"
        "Completed kanban tasks (Done column):\n"
        f"{done_block}\n"
    )


def _load_schema_index_for_profile(
    profile_name: str,
) -> tuple[str, dict[str, dict]] | tuple[None, None]:
    """Return (schema_name, index) or (None, None) on failure."""
    tree = load_skill_tree_raw(profile_name)
    if tree is None:
        return None, None
    schema_name = tree.get("schema")
    if not schema_name:
        return None, None
    schema_data = load_schema_raw(str(schema_name))
    if schema_data is None:
        return None, None
    return str(schema_name), schema_node_index(schema_data)


def ingest_resume_json(profile_name: str, resume_text: str) -> tuple[
    dict | None,
    str | None,
]:
    """Call LLM to produce ingest JSON from resume text.

    Returns ``(patch_dict, error)`` — *error* is set when the call
    fails or JSON cannot be parsed.
    """
    if not resume_text.strip():
        return None, "empty resume text"
    if not llm_client.is_configured():
        return None, "LLM not configured"

    loaded = _load_schema_index_for_profile(profile_name)
    if loaded[0] is None:
        return None, "could not load schema for profile"
    schema_name, index = loaded

    pool_raw = load_evidence_pool_raw(profile_name)
    tree_raw = load_skill_tree_raw(profile_name)
    pool_text, tree_text = pool_tree_summaries_for_prompt(
        pool_raw,
        tree_raw,
    )

    system = (
        _system_prompt_resume_zh()
        if llm_client.reply_language() == "zh"
        else _system_prompt_resume_en()
    )
    user = _append_ingest_user_reminder(
        _user_message_resume(
            resume_text,
            schema_name,
            index,
            pool_text,
            tree_text,
        )
    )
    reply = llm_client.chat(system, user, temperature=0.2)
    if reply.startswith("LLM error:") or reply.startswith(
        "AI features not configured"
    ):
        return None, reply

    data = extract_json_object(reply)
    if data is None:
        return None, "Could not parse ingest JSON from LLM."
    return data, None


def ingest_kanban_done_json(
    profile_name: str,
    done_tasks: list[KanbanTask],
) -> tuple[dict | None, str | None]:
    """Call LLM to produce ingest JSON from Done-column tasks."""
    if not done_tasks:
        return None, "no Done tasks selected"
    if not llm_client.is_configured():
        return None, "LLM not configured"

    loaded = _load_schema_index_for_profile(profile_name)
    if loaded[0] is None:
        return None, "could not load schema for profile"
    schema_name, index = loaded

    pool_raw = load_evidence_pool_raw(profile_name)
    tree_raw = load_skill_tree_raw(profile_name)
    pool_text, tree_text = pool_tree_summaries_for_prompt(
        pool_raw,
        tree_raw,
    )

    system = (
        _system_prompt_kanban_zh()
        if llm_client.reply_language() == "zh"
        else _system_prompt_kanban_en()
    )
    done_block = _format_done_tasks(done_tasks)
    user = _append_kanban_user_reminder(
        _user_message_kanban(
            done_block,
            schema_name,
            index,
            pool_text,
            tree_text,
        )
    )
    reply = llm_client.chat(system, user, temperature=0.2)
    if reply.startswith("LLM error:") or reply.startswith(
        "AI features not configured"
    ):
        return None, reply

    data = extract_json_object(reply)
    if data is None:
        return None, "Could not parse ingest JSON from LLM."
    return data, None
