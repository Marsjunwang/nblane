"""LLM prompts for resume / kanban Done → structured ingest JSON."""

from __future__ import annotations

import os

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


def _positive_env_float(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(5.0, value)


def _positive_env_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(256, value)


def _kanban_done_llm_timeout_seconds() -> float:
    return _positive_env_float(
        "KANBAN_DONE_LLM_TIMEOUT_SECONDS",
        max(llm_client.timeout_seconds(), 180.0),
    )


def _kanban_done_llm_max_tokens(task_count: int = 1) -> int:
    task_budget = max(4096, 2048 + max(1, int(task_count or 1)) * 1200)
    return _positive_env_int(
        "KANBAN_DONE_LLM_MAX_TOKENS",
        min(llm_client.max_tokens_default(), task_budget),
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
        "- title、date、url、summary：summary 写清可核验要点，便于判断 solid。\n"
        + _evidence_provenance_resume_zh()
        + "node_updates 每项：id（仅允许列表中的节点）、evidence_refs、"
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
        "to support solid vs learning.\n"
        + _evidence_provenance_resume_en()
        + "node_updates: id (allowed nodes only), evidence_refs, optional "
        "evidence, note, status.\n"
        "evidence_refs: same ids as evidence_entries, or first_1 / ev_2 "
        "meaning row index in evidence_entries (1-based).\n\n"
        + _status_rubric_en()
        + "\nUse empty arrays if mapping is unreliable."
    )


def _evidence_provenance_resume_zh() -> str:
    """v2 provenance fields each resume evidence row must carry."""
    return (
        "- origin：固定为 \"resume_parse\"。\n"
        "- origin_ref：\"resume\"，或更精确的 resume:<区块/hash/block-id>。\n"
        "- origin_detail：简历区块名（如 GAC / CloudMile / Publications）。\n"
        "- source_excerpt：简历原文中证明该条的一两句照抄。\n"
        "- original_content：对应简历**原始片段（span）**原样保留，"
        "**不要**只存模型摘要。\n"
        "- formatted_content：结构化、可读的 Markdown 正文。\n"
        "- language：规范化字段语言，按回复语言填 \"en\"/\"zh\"。\n"
        "- original_language：original_content 的实际语言。\n"
        "- project_refs：若能确定对应已有 Project Board 项目则给出；"
        "不确定就留空（后续由项目建议处理）。\n\n"
    )


def _evidence_provenance_resume_en() -> str:
    """v2 provenance fields each resume evidence row must carry."""
    return (
        "- origin: always \"resume_parse\".\n"
        "- origin_ref: \"resume\", or a more precise resume:<block/hash/id>.\n"
        "- origin_detail: the resume section name (e.g. GAC / CloudMile / "
        "Publications).\n"
        "- source_excerpt: a literal sentence or two from the resume "
        "grounding the row.\n"
        "- original_content: keep the **original resume span** verbatim; "
        "do NOT store only the model summary.\n"
        "- formatted_content: a structured, readable Markdown body.\n"
        "- language: language of the normalized fields; set \"en\"/\"zh\" to "
        "match the reply language.\n"
        "- original_language: the actual language of original_content.\n"
        "- project_refs: provide it only when an existing Project Board "
        "project clearly matches; otherwise leave empty (a separate project "
        "suggestion step handles it).\n\n"
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
        "- **严禁**把看板任务 id（形如 kb_… ）或 kanban:<任务 id> 写进 "
        "node_updates 的 evidence_refs：它们只是证据来源（provenance），"
        "应放在对应 evidence_entries 行的 kanban_refs 里；"
        "node_updates 的 evidence_refs 只接受证据 id / 新行 id / first_1 / ev_2。\n"
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
        "- **Never** put a Kanban task id (shaped like kb_…) or a "
        "kanban:<task id> ref in node_updates evidence_refs: those are "
        "evidence provenance and belong in an evidence_entries row's "
        "kanban_refs. node_updates evidence_refs accept only pool evidence "
        "ids, new evidence row ids, or first_1 / ev_2 placeholders.\n"
        "- Multiple Done tasks: if all map to existing pool rows, "
        "evidence_entries can be empty.\n"
    )


def _kanban_skip_protocol_zh() -> str:
    """Ask the model to explain Done tasks that should not create rows."""
    return (
        "### skipped_tasks（不能生成 evidence 时必填）\n\n"
        "- 对每个被选中的 Done task：如果没有为它输出新的 evidence_entries 行，"
        "请在 skipped_tasks 中输出一项，解释为什么不生成新证据。\n"
        "- skipped_tasks 每项字段：task_id、reason、detail。\n"
        "reason 仅限 not_evidence | too_vague | already_covered | "
        "out_of_scope | insufficient_source。\n"
        "- already_covered 表示该事实已由 Current evidence pool 中的旧证据覆盖；"
        "这时不要重复写 evidence_entries，可在 node_updates 中引用已有证据 id。\n"
        "- skipped_tasks 只解释跳过原因。除非 node_updates 明确引用已有证据 id，"
        "否则不要为跳过任务输出技能更新。宿主可能仍会把这些 Done 任务"
        "标记 crystallized 并归档。\n\n"
    )


def _kanban_skip_protocol_en() -> str:
    """Ask the model to explain Done tasks that should not create rows."""
    return (
        "### skipped_tasks (required when no evidence row is created)\n\n"
        "- For every selected Done task: if you do not output a new "
        "evidence_entries row for it, add one skipped_tasks item explaining "
        "why no new evidence should be created.\n"
        "- skipped_tasks fields: task_id, reason, detail. reason must be one "
        "of not_evidence | too_vague | already_covered | out_of_scope | "
        "insufficient_source.\n"
        "- already_covered means the fact is already covered by an existing "
        "Current evidence pool id; do not duplicate it in evidence_entries, "
        "but node_updates may reference that existing evidence id.\n"
        "- skipped_tasks only explains the skip. Do not emit skill updates "
        "for skipped tasks unless node_updates cites existing evidence ids. "
        "The host may still mark these Done tasks crystallized and archive "
        "them.\n\n"
    )


def _evidence_grading_zh() -> str:
    """Ask the model to pre-grade evidence strength/confidence (kanban)."""
    return (
        "### evidence_entries 字段（除 id/type/title/date/url/summary/source_excerpt 外）\n\n"
        "每条 evidence_entries 还应给出**预判**字段，供人工审阅时确认或微调：\n"
        "- strength（证据强度，取值仅限 weak | medium | strong | high_trust）：\n"
        "  · strong/high_trust — 论文（会议/期刊/arxiv/一作）、可复制的开源链接"
        "（GitHub/GitLab、org/repo、PR/release）、或相对基线的量化指标。\n"
        "  · medium — 真实交付/复现/工程事实，但无上述可核验亮点。\n"
        "  · weak — 主要靠推断、描述含糊或缺可核验细节。\n"
        "- confidence（你对该判断的信心，取值仅限 low | medium | high）：\n"
        "  · high — 证据直接可核验（有链接/论文/明确数字），强度评级几乎不会错。\n"
        "  · medium — 基本可信，但需要一点推断或细节不全。\n"
        "  · low — 主要靠推测，来源或细节存疑。\n"
        "判断口径与下文 status 规则一致；无把握时**省略**该字段（留给人工填）。\n\n"
    )


def _evidence_grading_en() -> str:
    """English variant of the evidence pre-grading guidance."""
    return (
        "### evidence_entries fields (besides id/type/title/date/url/summary/source_excerpt)\n\n"
        "Each evidence_entries item should also include **pre-graded** fields "
        "for humans to confirm or tweak during review:\n"
        "- strength (evidence strength, only one of weak | medium | strong | high_trust):\n"
        "  · strong/high_trust — paper (venue/journal/arxiv/first author), a "
        "copyable open-source link (GitHub/GitLab, org/repo, PR/release), or "
        "quantitative metrics vs a baseline.\n"
        "  · medium — real delivery/reproduction/engineering fact without the "
        "verifiable highlights above.\n"
        "  · weak — mostly inferred, vague, or missing verifiable detail.\n"
        "- confidence (your confidence in the grade, only one of low | medium | high):\n"
        "  · high — directly verifiable (link/paper/explicit numbers); the grade is almost certainly right.\n"
        "  · medium — largely trustworthy but needs some inference or details are incomplete.\n"
        "  · low — mostly speculative; source or details are questionable.\n"
        "Use the same bar as the status rules below; **omit** the field when "
        "unsure (a human will fill it).\n\n"
    )


def _evidence_provenance_kanban_zh() -> str:
    """v2 provenance fields the kanban distillation must emit per row."""
    return (
        "### v2 出处字段（看板蒸馏每条 evidence_entries 必填）\n\n"
        "- origin：固定为 \"kanban_task\"。\n"
        "- origin_ref：对应 Done 任务的 id（如 task 的 id 字段）。\n"
        "- origin_detail：Done 任务标题 + 完成日期，便于人审时识别来源。\n"
        "- kanban_refs：[\"kanban:<task id>\"]，至少含主任务。\n"
        "- project_refs：仅当任务带 project_id 时填 [<project_id>]，否则省略。\n"
        "- original_content：把**完整任务原文**（title/context/why/outcome/notes/"
        "subtasks/dates/project_id）原样保留，**不要压成摘要**。\n"
        "- formatted_content：结构化、可读的 Markdown 正文（标题/要点/指标/出处），"
        "可读但**不替代** original_content。\n"
        "- language：规范化字段（title/summary/formatted_content）的语言，"
        "按系统回复语言填 \"en\" 或 \"zh\"。\n"
        "- original_language：original_content 的实际语言（en/zh/mixed）。\n\n"
    )


def _evidence_provenance_kanban_en() -> str:
    """v2 provenance fields the kanban distillation must emit per row."""
    return (
        "### v2 provenance fields (required on every kanban evidence row)\n\n"
        "- origin: always \"kanban_task\".\n"
        "- origin_ref: the source Done task id.\n"
        "- origin_detail: Done task title + completed date (for human review).\n"
        "- kanban_refs: [\"kanban:<task id>\"], at least the primary task.\n"
        "- project_refs: [<project_id>] only when the task has a project_id; "
        "otherwise omit.\n"
        "- original_content: keep the **full task text** verbatim "
        "(title/context/why/outcome/notes/subtasks/dates/project_id). "
        "Do NOT compress it into a summary.\n"
        "- formatted_content: a structured, readable Markdown body "
        "(heading/points/metrics/source). Readable, but it does NOT replace "
        "original_content.\n"
        "- language: language of the normalized fields "
        "(title/summary/formatted_content); set \"en\" or \"zh\" to match the "
        "reply language.\n"
        "- original_language: the actual language of original_content "
        "(en/zh/mixed).\n\n"
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
        "只输出一个 JSON：evidence_entries、node_updates、skipped_tasks。\n"
        "node_updates 每项字段：id（必须是 Allowed nodes 中的技能节点 id；"
        "字段名必须写作 id，禁止写 node_id、skill_id 或 node）、"
        "evidence_refs、status、rationale。\n\n"
        + _evidence_grading_zh()
        + _evidence_provenance_kanban_zh()
        + _kanban_skip_protocol_zh()
        + "### 出处（必填）\n\n"
        "- evidence_entries 每项必须含 **source_excerpt**：从对应 Done 任务原文"
        "（title/context/outcome/notes/subtask）中**照抄或极短摘录**一两句，"
        "证明该条证据不是臆测。\n"
        "- node_updates 每项必须含 **rationale**（1–3 句）：说明为何更新该节点，"
        "并引用任务中的具体事实（可与 source_excerpt 呼应）。\n"
        "禁止空 rationale 或空 source_excerpt（若无把握则不要输出该条）。\n\n"
        "### Current goal\n\n"
        "若 user 消息包含 Current goal，它只能用于判断优先级和解释方向；"
        "不得从 goal 本身编造 evidence。每条 evidence 仍必须由 Done 任务原文支撑。\n\n"
        + _kanban_evidence_contract_zh()
        + "\n"
        + _status_rubric_kanban_zh()
        + "\n无把握则 evidence_entries、node_updates、skipped_tasks 可为 []。"
    )


def _system_prompt_kanban_en() -> str:
    """System prompt: Done tasks → JSON (English UI)."""
    return (
        "You map completed kanban tasks to evidence and skill nodes. "
        "Output one JSON: evidence_entries, node_updates, skipped_tasks.\n"
        "Each node_updates item fields: id (must be an allowed skill node id; "
        "the field name must be exactly id, not node_id, skill_id, or node), "
        "evidence_refs, status, rationale.\n\n"
        + _evidence_grading_en()
        + _evidence_provenance_kanban_en()
        + _kanban_skip_protocol_en()
        + "### Provenance (required)\n\n"
        "- Each evidence_entries item MUST include **source_excerpt**: "
        "a short literal quote from the Done task (title/context/outcome/"
        "notes/subtasks) proving the row is grounded.\n"
        "- Each node_updates item MUST include **rationale** (1–3 sentences): "
        "why this node changes, citing concrete task facts.\n"
        "Do not emit empty rationale or source_excerpt (omit the row if "
        "unsure).\n\n"
        "### Current goal\n\n"
        "If the user message includes Current goal, use it only for "
        "priority and interpretation. Never invent evidence from the goal; "
        "each evidence row must still be grounded in the Done task text.\n\n"
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
            "没有新证据行的 Done 任务必须写进 skipped_tasks；"
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
            "Done tasks without a new evidence row must be listed in "
            "skipped_tasks. "
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
        if t.id.strip():
            lines.append(f"  id: {t.id.strip()}")
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
        if t.project_id.strip():
            lines.append(f"  project_id: {t.project_id.strip()}")
        if t.milestone_id.strip():
            lines.append(f"  milestone_id: {t.milestone_id.strip()}")
        if t.tags.strip():
            lines.append(f"  tags: {t.tags.strip()}")
        if getattr(t, "crystallized", False):
            lines.append("  crystallized: true")
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
    goal_context: str = "",
) -> str:
    """Build user message for kanban Done ingest."""
    goal_block = ""
    if goal_context.strip():
        goal_block = (
            "Current goal (context only; do not invent evidence from it):\n"
            f"{goal_context.strip()}\n\n"
        )
    return (
        f"Schema file: {schema_name}\n\n"
        f"{goal_block}"
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
    goal_context: str = "",
    ai_backend: str = "llm",
) -> tuple[dict | None, str | None]:
    """Produce ingest JSON from Done-column tasks."""
    if not done_tasks:
        return None, "no Done tasks selected"
    use_codex = _use_codex_backend(ai_backend)
    if not use_codex and not llm_client.is_configured():
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
            goal_context=goal_context,
        )
    )
    if use_codex:
        return _codex_ingest_json(profile_name, system, user)
    reply = llm_client.chat(
        system,
        user,
        temperature=0.2,
        timeout=_kanban_done_llm_timeout_seconds(),
        max_tokens=_kanban_done_llm_max_tokens(len(done_tasks)),
    )
    if reply.startswith("LLM error:") or reply.startswith(
        "AI features not configured"
    ):
        return None, reply

    data = extract_json_object(reply)
    if data is None:
        return None, "Could not parse ingest JSON from LLM."
    return data, None


def _codex_ingest_json(
    profile_name: str,
    system: str,
    user: str,
) -> tuple[dict | None, str | None]:
    """Run the kanban ingest prompt through local read-only Codex."""

    from nblane.core import codex_adapter

    prompt = (
        "You are Codex used by nblane Kanban as a read-only AI backend. "
        "Do not edit files, do not generate patches, do not write profile "
        "facts, and do not submit agent-task candidates. Return only the JSON "
        "object requested by the system prompt.\n\n"
        "System instructions:\n"
        f"{system.strip()}\n\n"
        "User message:\n"
        f"{user.strip()}\n"
    )
    result = codex_adapter.run_readonly_codex_prompt(profile_name, prompt)
    if not result.ok:
        return None, result.error or result.output or "Codex ingest failed."
    data = extract_json_object(result.output)
    if data is None:
        return None, "Could not parse ingest JSON from Codex."
    return data, None


def _use_codex_backend(value: object) -> bool:
    """Return True when kanban ingest should use local read-only Codex."""

    return str(value or "").strip().casefold() == "codex"


# --- Evidence v2: AI reformat (target-language normalization) ---------------

_REFORMAT_KEYS = ("title", "summary", "formatted_content")


def _reformat_system_prompt(target_lang: str) -> str:
    """System prompt for reformatting one evidence row to *target_lang*."""
    if target_lang == "zh":
        return (
            "你是一个履历证据规范化助手。给定一条证据的原始内容"
            "(original_content) 与现有字段，请把它整理成规范、可读的中文。\n"
            "严格要求：\n"
            "1. 只输出 JSON：{\"title\":..., \"summary\":..., "
            "\"formatted_content\":...}。\n"
            "2. title 为简短标题；summary 为 1-3 句摘要；formatted_content 为"
            "完整、结构化的 Markdown 正文，可读且包含原始事实。\n"
            "3. 事实只能来自 original_content / 现有字段，不要编造数字或成果。\n"
            "4. 绝对不要改写或返回 original_content 本身。\n"
            "5. 全部用中文输出。"
        )
    return (
        "You normalize a single resume/evidence row. Given its raw "
        "original_content and current fields, produce clean, readable English.\n"
        "Strict rules:\n"
        '1. Output JSON only: {"title":..., "summary":..., '
        '"formatted_content":...}.\n'
        "2. title is a short heading; summary is 1-3 sentences; "
        "formatted_content is a complete, structured Markdown body that is "
        "readable and preserves the original facts.\n"
        "3. Facts must come only from original_content / current fields. Do "
        "not invent metrics or outcomes.\n"
        "4. Never rewrite or return original_content itself.\n"
        "5. Write everything in English."
    )


def _reformat_user_message(row: dict) -> str:
    def _g(key: str) -> str:
        return str(row.get(key, "") or "").strip()

    return (
        "Current fields:\n"
        f"- id: {_g('id')}\n"
        f"- type: {_g('type')}\n"
        f"- origin: {_g('origin')}\n"
        f"- title: {_g('title')}\n"
        f"- summary: {_g('summary')}\n\n"
        "original_content (source of truth, do not rewrite):\n"
        "<<<\n"
        f"{_g('original_content')}\n"
        ">>>\n\n"
        "Return the JSON object now."
    )


def reformat_evidence(
    profile: str,
    row: dict,
    *,
    target_lang: str | None = None,
) -> tuple[dict | None, str | None]:
    """Propose normalized title/summary/formatted_content in *target_lang*.

    Returns ``(proposed_row, error)``. The proposal only carries the
    reformatted fields plus ``language``; it never touches original_content,
    origin, refs, or status. Does not save — the caller confirms.
    """
    target_lang = (target_lang or llm_client.reply_language() or "en").strip()
    target_lang = "zh" if target_lang == "zh" else "en"

    if not str(row.get("original_content", "") or "").strip() and not str(
        row.get("summary", "") or ""
    ).strip():
        return None, "no original_content to reformat"
    if not llm_client.is_configured():
        return None, "LLM not configured"

    system = _reformat_system_prompt(target_lang)
    user = _reformat_user_message(row)
    reply = llm_client.chat(system, user, temperature=0.2)
    if reply.startswith("LLM error:") or reply.startswith(
        "AI features not configured"
    ):
        return None, reply
    data = extract_json_object(reply)
    if data is None:
        return None, "Could not parse reformat JSON from LLM."

    proposed: dict = {}
    for key in _REFORMAT_KEYS:
        val = str(data.get(key, "") or "").strip()
        if val:
            proposed[key] = val
    if not proposed:
        return None, "reformat produced no usable fields"
    proposed["language"] = target_lang
    return proposed, None
