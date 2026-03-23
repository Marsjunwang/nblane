"""Streamlit UI strings for ``LLM_REPLY_LANG`` (en / zh).

Centralizes copy so all pages stay consistent with Gap Analysis.
"""

from __future__ import annotations

from nblane.core import llm as llm_client

# Kanban file sections are English keys; this is display-only.
_KANBAN_SEC: dict[str, dict[str, str]] = {
    "en": {
        "Doing": "Doing",
        "Done": "Done",
        "Queue": "Queue",
        "Someday / Maybe": "Someday / Maybe",
    },
    "zh": {
        "Doing": "进行中",
        "Done": "已完成",
        "Queue": "队列",
        "Someday / Maybe": "也许 / 将来",
    },
}

PRODUCT_POOL_KEYS: tuple[str, ...] = (
    "problem_pool",
    "project_pool",
    "evidence_pool",
    "method_pool",
    "decision_pool",
)

_POOL_LABEL: dict[str, dict[str, str]] = {
    "en": {
        "problem_pool": "Problem Pool",
        "project_pool": "Project Pool",
        "evidence_pool": "Evidence Pool",
        "method_pool": "Method Pool",
        "decision_pool": "Decision Pool",
    },
    "zh": {
        "problem_pool": "问题池",
        "project_pool": "项目池",
        "evidence_pool": "证据池",
        "method_pool": "方法池",
        "decision_pool": "决策池",
    },
}

_COMMON: dict[str, dict[str, str]] = {
    "en": {
        "status_locked": "Locked",
        "status_learning": "Learning",
        "status_solid": "Solid",
        "status_expert": "Expert",
        "profile_header": "### Profile",
        "no_profiles_yet": "No profiles yet.",
        "no_profiles_main": (
            "No profiles. Create one in the sidebar."
        ),
        "select_profile_aria": "Profile",
        "expander_create": "➕ Create new profile",
        "profile_name_label": "Profile name",
        "profile_name_ph": "e.g. alice",
        "create": "Create",
        "name_empty": "Name cannot be empty.",
        "name_exists": "'{name}' already exists.",
        "profile_created": "Profile '{name}' created.",
        "ai_not_configured": "AI not configured (rule-based only)",
        "ai_add_key_caption": (
            "Add `LLM_API_KEY` to `.env` to enable AI features."
        ),
        "merge_llm_status_applied": "applied",
        "merge_llm_status_ignored": "ignored",
        "merge_preview_llm_status_line": (
            "Preview merge: LLM `status` field — **{mode}**"
        ),
        "merge_preview_delta_title": (
            "Delta vs files on disk (this draft)"
        ),
        "merge_preview_delta_new_evidence": "New evidence rows",
        "merge_preview_delta_tree": "Skill tree changes",
        "merge_preview_delta_none": (
            "No new pool rows or node field changes detected."
        ),
        "merge_preview_yaml_readonly_caption": (
            "Read-only YAML below reflects the current merge; toggling "
            "status re-merges the same draft without a new LLM call."
        ),
    },
    "zh": {
        "status_locked": "锁定",
        "status_learning": "学习中",
        "status_solid": "扎实",
        "status_expert": "专家",
        "profile_header": "### Profile",
        "no_profiles_yet": "暂无 Profile。",
        "no_profiles_main": "暂无 Profile，请在侧边栏创建。",
        "select_profile_aria": "选择 Profile",
        "expander_create": "➕ 新建 Profile",
        "profile_name_label": "Profile 名称",
        "profile_name_ph": "例如 alice",
        "create": "创建",
        "name_empty": "名称不能为空。",
        "name_exists": "「{name}」已存在。",
        "profile_created": "已创建 Profile「{name}」。",
        "ai_not_configured": "未配置 AI（仅规则模式）",
        "ai_add_key_caption": (
            "在 `.env` 中设置 `LLM_API_KEY` 以启用 AI。"
        ),
        "merge_llm_status_applied": "已应用",
        "merge_llm_status_ignored": "已忽略",
        "merge_preview_llm_status_line": (
            "预览合并：LLM 的 `status` 字段 — **{mode}**"
        ),
        "merge_preview_delta_title": "与磁盘上文件的差异（本草案）",
        "merge_preview_delta_new_evidence": "新增证据行",
        "merge_preview_delta_tree": "技能树变更",
        "merge_preview_delta_none": (
            "未检测到新的池行或节点字段变化。"
        ),
        "merge_preview_yaml_readonly_caption": (
            "下方 YAML 为只读预览，随当前合并选项即时更新；"
            "切换「允许 AI 更新状态」会重算同一草案，无需再次点生成。"
        ),
    },
}

_GAP: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Gap Analysis · nblane",
        "title": "Gap Analysis",
        "task_label": "Task description",
        "task_placeholder": (
            "Describe your task in natural language, e.g.:\n"
            "Reproduce PI0.5 VLA control on a Piper arm"
        ),
        "analyze_button": "Analyze",
        "analyze_hint": (
            "Enter a task description and click Analyze to run."
        ),
        "spinner_gap": "Running gap analysis...",
        "verdict_ok": "Ready",
        "verdict_gap": "Gaps remain",
        "metric_verdict": "Verdict",
        "metric_matches": "Matched nodes",
        "metric_gaps": "Gap nodes",
        "progress_text": (
            "Dependency coverage: {ok}/{total} ({pct:.0%})"
        ),
        "subheader_matches": "Matched skill nodes",
        "match_score": "Match score",
        "subheader_closure": "Dependency closure",
        "gap_mark_suffix": "gap",
        "subheader_next": "Suggested next steps",
        "subheader_ai": "AI analysis",
        "ai_disabled_hint": (
            "Set LLM_API_KEY in `.env` to enable AI insights:\n"
            "- Why each gap matters for this task\n"
            "- Optimal learning order\n"
            "- Skill status updates after completing the task"
        ),
        "spinner_ai": "AI reasoning...",
        "learned_caption": (
            "Learned keywords updated ({total} total across "
            "{nodes} nodes, max {max_kw}/node)"
        ),
        "writeback_title": "Update skill status",
        "writeback_caption": (
            "Select nodes and new statuses, then apply to "
            "write skill-tree.yaml."
        ),
        "current_label": "Current",
        "apply_button": "Apply {n} update(s)",
        "success_updated": "Skill tree updated:",
        "checkbox_select": "Select",
        "use_rule_match": "Rule keyword overlap",
        "use_llm_router": "AI route to skill nodes (first pass)",
        "manual_node_label": "Or choose a schema node (manual)",
        "manual_node_none": "(automatic only)",
        "gap_error_no_roots": (
            "No roots from the enabled matchers. "
            "Turn on **AI route** or **rule overlap**, "
            "or pick a node below and analyze again."
        ),
        "gap_error_empty_task": "Enter a task description.",
        "gap_error_node_unknown": "That node id is not in the schema.",
        "match_source_rule": "rule",
        "match_source_llm": "AI",
        "match_source_both": "rule+AI",
        "match_source_explicit": "manual",
        "router_learned_caption": (
            "First-pass router saved keywords to learned store."
        ),
        "subheader_coach_followup": "Follow-up (same session)",
        "expander_first_prompt": (
            "First prompt: skill tree + gap analysis (long)"
        ),
        "chat_followup_placeholder": (
            "Ask a follow-up about this gap analysis…"
        ),
        "spinner_ai_followup": "Thinking…",
    },
    "zh": {
        "page_title": "差距分析 · nblane",
        "title": "差距分析",
        "task_label": "任务描述",
        "task_placeholder": (
            "用自然语言描述你想做的任务，例如：\n"
            "复现 PI0.5 在 piper 机械臂上的 VLA 控制"
        ),
        "analyze_button": "分析",
        "analyze_hint": "输入任务描述并点击「分析」开始。",
        "spinner_gap": "正在运行差距分析…",
        "verdict_ok": "可以完成",
        "verdict_gap": "存在能力缺口",
        "metric_verdict": "结论",
        "metric_matches": "匹配节点",
        "metric_gaps": "缺口节点",
        "progress_text": "依赖覆盖：{ok}/{total} ({pct:.0%})",
        "subheader_matches": "匹配到的技能节点",
        "match_score": "匹配分",
        "subheader_closure": "前提闭包",
        "gap_mark_suffix": "缺口",
        "subheader_next": "建议下一步",
        "subheader_ai": "AI 分析",
        "ai_disabled_hint": (
            "配置 LLM_API_KEY 后，AI 将在此处给出：\n"
            "- 每个缺口与任务的关联解释\n"
            "- 最优学习顺序\n"
            "- 本次任务完成后应更新的技能状态"
        ),
        "spinner_ai": "AI 分析中…",
        "learned_caption": (
            "已更新学习关键词（共 {total} 条，分布于 "
            "{nodes} 个节点，每节点最多 {max_kw} 条）"
        ),
        "writeback_title": "更新技能状态",
        "writeback_caption": (
            "选择要更新的节点和新状态，"
            "完成任务后一键写回 skill-tree.yaml。"
        ),
        "current_label": "当前",
        "apply_button": "应用 {n} 项更新",
        "success_updated": "技能树已更新：",
        "checkbox_select": "选择",
        "use_rule_match": "规则关键词重叠",
        "use_llm_router": "AI 首轮匹配到技能节点",
        "manual_node_label": "或手动指定模式中的节点",
        "manual_node_none": "（仅自动匹配）",
        "gap_error_no_roots": (
            "当前开启的匹配方式未得到任何根节点。"
            "请开启 **AI 首轮匹配** 或 **规则重叠**，"
            "或在下方选择节点后再次分析。"
        ),
        "gap_error_empty_task": "请填写任务描述。",
        "gap_error_node_unknown": "该节点 id 不在当前 schema 中。",
        "match_source_rule": "规则",
        "match_source_llm": "AI",
        "match_source_both": "规则+AI",
        "match_source_explicit": "手动",
        "router_learned_caption": "首轮路由已写入学习关键词。",
        "subheader_coach_followup": "继续追问（同一会话）",
        "expander_first_prompt": (
            "首轮完整提示：技能树 + 差距分析（长）"
        ),
        "chat_followup_placeholder": (
            "针对本次差距分析继续提问…"
        ),
        "spinner_ai_followup": "思考中…",
    },
}

_SKILL_TREE: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Skill Tree · nblane",
        "title": "Skill Tree",
        "error_no_tree": "skill-tree.yaml not found for '{profile}'.",
        "metric_expert": "🔵 Expert",
        "metric_solid": "🟢 Solid",
        "metric_learning": "🟡 Learning",
        "metric_locked": "⬜ Locked",
        "metric_lit_rate": "Lit rate",
        "progress_overall": "Overall lit: {pct:.0%}",
        "no_categories": "No categories found in schema.",
        "level_l1": "L1 · Foundation",
        "level_l2": "L2 · Intermediate",
        "level_l3": "L3 · Advanced",
        "level_l4": "L4 · Expert / Frontier",
        "level_n": "Level {n}",
        "widget_status": "Status",
        "widget_note": "Note",
        "note_placeholder": "context / evidence",
        "cat_progress": "{cat}: {lit}/{total} lit ({pct:.0%})",
        "save_button": "Save skill-tree.yaml",
        "save_caption": (
            "Saves skill-tree.yaml and syncs generated blocks "
            "in SKILL.md."
        ),
        "saved_synced": "Saved and synced SKILL.md.",
        "saved_yaml": "Saved skill-tree.yaml.",
        "saved_synced_path": (
            "Saved and synced SKILL.md. "
            "skill-tree.yaml: `{path}`"
        ),
        "saved_yaml_path": (
            "Saved skill-tree.yaml (SKILL.md sync skipped). "
            "File: `{path}`"
        ),
        "evidence_expander": "Evidence ({n})",
        "evidence_item": "Item",
        "evidence_type": "Type",
        "evidence_title": "Title",
        "evidence_date": "Date",
        "evidence_url": "URL",
        "evidence_summary": "Summary",
        "evidence_add": "＋ Add evidence",
        "evidence_remove": "Remove",
        "evidence_pin_help": (
            "Pin: keep this skill's evidence section expanded; "
            "click another skill's pin to switch."
        ),
        "pool_expander": "Evidence pool (shared catalog)",
        "pool_caption": (
            "Stable ids here may be referenced from many skills "
            "via evidence_refs."
        ),
        "pool_id_optional": "Id (optional; auto-generated if empty)",
        "pool_add_button": "Add to pool",
        "pool_added": "Added to evidence pool.",
        "evidence_refs_label": "Pool references",
        "evidence_refs_help": (
            "Choose existing pool rows to attach to this skill."
        ),
        "pool_empty_hint": (
            "No pool rows yet — add entries in the expander above."
        ),
    },
    "zh": {
        "page_title": "技能树 · nblane",
        "title": "技能树",
        "error_no_tree": "未找到「{profile}」的 skill-tree.yaml。",
        "metric_expert": "🔵 专家",
        "metric_solid": "🟢 扎实",
        "metric_learning": "🟡 学习中",
        "metric_locked": "⬜ 锁定",
        "metric_lit_rate": "点亮率",
        "progress_overall": "整体点亮：{pct:.0%}",
        "no_categories": "模式中未找到分类。",
        "level_l1": "L1 · 基础",
        "level_l2": "L2 · 进阶",
        "level_l3": "L3 · 高级",
        "level_l4": "L4 · 专家 / 前沿",
        "level_n": "等级 {n}",
        "widget_status": "状态",
        "widget_note": "备注",
        "note_placeholder": "上下文 / 证据",
        "cat_progress": "{cat}：{lit}/{total} 已点亮（{pct:.0%}）",
        "save_button": "保存 skill-tree.yaml",
        "save_caption": "保存 skill-tree.yaml，并同步 SKILL.md 中的生成块。",
        "saved_synced": "已保存并同步 SKILL.md。",
        "saved_yaml": "已保存 skill-tree.yaml。",
        "saved_synced_path": (
            "已保存并同步 SKILL.md。"
            "skill-tree.yaml 路径：`{path}`"
        ),
        "saved_yaml_path": (
            "已保存 skill-tree.yaml（SKILL.md 生成块未同步）。"
            "文件：`{path}`"
        ),
        "evidence_expander": "证据（{n}）",
        "evidence_item": "条目",
        "evidence_type": "类型",
        "evidence_title": "标题",
        "evidence_date": "日期",
        "evidence_url": "链接",
        "evidence_summary": "摘要",
        "evidence_add": "＋ 添加证据",
        "evidence_remove": "删除",
        "evidence_pin_help": (
            "固定：保持展开此技能的证据区；"
            "点其他技能的图钉可切换。"
        ),
        "pool_expander": "证据池（共享目录）",
        "pool_caption": (
            "在此维护稳定 id，多个技能可通过 evidence_refs 引用。"
        ),
        "pool_id_optional": "Id（可空；留空则自动生成）",
        "pool_add_button": "添加到证据池",
        "pool_added": "已添加到证据池。",
        "evidence_refs_label": "引用池 id",
        "evidence_refs_help": "选择已有池条目挂到此技能。",
        "pool_empty_hint": "尚无池条目 — 请在上方可折叠区添加。",
    },
}

_HOME: dict[str, dict[str, str]] = {
    "en": {
        "app_page_title": "NBL",
        "app_caption": (
            "Current profile: **{profile}** · "
            "Data is plain YAML / Markdown; "
            "Git is the source of truth."
        ),
        "tab_overview": "📊 Overview",
        "tab_editor": "✏️ Structured Editor",
        "tab_raw": "📝 Raw",
        "sub_overview": "Skill overview",
        "sub_category": "Category breakdown",
        "home_expander_cat": "{cat} — {total} nodes",
        "info_no_skill_tree": (
            "skill-tree.yaml is not initialized yet. "
            "Edit `profiles/{profile}/skill-tree.yaml` "
            "to add nodes."
        ),
        "home_nav": (
            "**Page navigation** (left sidebar):\n\n"
            "- **Skill Tree** — Visual tree and status editor\n"
            "- **Gap Analysis** — Task-to-skill matching "
            "and gaps\n"
            "- **Kanban** — Task board\n"
            "- **Team View** — Shared team product pool"
        ),
        "warning_no_skill_md": "SKILL.md not found.",
        "gen_caption": (
            "This section is auto-generated by "
            "`nblane sync`. Edits here will be overwritten."
        ),
        "gen_suffix": " *(auto-generated)*",
        "save_skill_md": "💾 Save SKILL.md",
        "home_saved": "Saved.",
        "hint_after_save": (
            "After saving, run `nblane context {profile}` "
            "for the latest system prompt."
        ),
        "raw_label": (
            "Edit SKILL.md (source for the agent prompt)"
        ),
        "resume_expander": "Resume / long text (AI ingest)",
        "resume_placeholder": (
            "Paste resume, project list, or bio…"
        ),
        "resume_generate": "Generate draft",
        "resume_spinner": "Calling LLM…",
        "resume_allow_status": "Allow AI to update node status",
        "resume_allow_status_help": (
            "Off: ignores LLM status fields; only merges refs/evidence; "
            "locked nodes with new evidence become learning. "
            "On: applies LLM status only when it upgrades or stays at the "
            "same tier (never solid→learning, never expert→lower). "
            "LLM expert is saved as learning when that is an upgrade. "
            "Your YAML expert stays expert."
        ),
        "resume_preview_pool": "Merged evidence-pool (preview)",
        "resume_preview_tree": "Merged skill-tree (preview)",
        "resume_apply": "Apply to profile",
        "resume_applied": "Applied: pool, skill-tree, and SKILL.md sync.",
        "resume_err": "Error: {msg}",
        "resume_no_ai": "AI not configured. Set LLM_API_KEY in .env.",
        "resume_warn": "Warnings",
    },
    "zh": {
        "app_page_title": "NBL",
        "app_caption": (
            "当前 Profile：**{profile}** · "
            "数据以 YAML / Markdown 明文存储，"
            "Git 是唯一的 source of truth。"
        ),
        "tab_overview": "📊 概览",
        "tab_editor": "✏️ 结构化编辑",
        "tab_raw": "📝 原文",
        "sub_overview": "技能概览",
        "sub_category": "按分类",
        "home_expander_cat": "{cat} — 共 {total} 个节点",
        "info_no_skill_tree": (
            "skill-tree.yaml 尚未初始化。"
            "请编辑 `profiles/{profile}/skill-tree.yaml` "
            "添加节点。"
        ),
        "home_nav": (
            "**页面导航**（左侧菜单）：\n\n"
            "- **Skill Tree** — 技能树可视化与状态编辑\n"
            "- **Gap Analysis** — 任务-能力匹配与缺口分析\n"
            "- **Kanban** — 任务看板\n"
            "- **Team View** — 团队共享产品池"
        ),
        "warning_no_skill_md": "未找到 SKILL.md。",
        "gen_caption": (
            "本节由 `nblane sync` 自动生成，"
            "在此编辑会被覆盖。"
        ),
        "gen_suffix": " （自动生成）",
        "save_skill_md": "💾 保存 SKILL.md",
        "home_saved": "已保存。",
        "hint_after_save": (
            "保存后运行 `nblane context {profile}` "
            "生成最新 system prompt。"
        ),
        "raw_label": (
            "编辑 SKILL.md（即 agent system prompt 的来源）"
        ),
        "resume_expander": "简历 / 长文本（AI 摄入）",
        "resume_placeholder": "粘贴简历、项目列表或简介…",
        "resume_generate": "生成草案",
        "resume_spinner": "调用 AI 中…",
        "resume_allow_status": "允许 AI 更新节点状态",
        "resume_allow_status_help": (
            "未勾选：合并时忽略 LLM 的 status，只写入证据与引用；"
            "有证据的 locked 节点会变为 learning。"
            "勾选：仅在「升级或持平」时写入 LLM 的 status（不会 solid→learning，"
            "不会把 expert 降级）；LLM 若输出 expert 会按 learning 档参与比较。"
            "YAML 里已标 expert 的节点不会被覆盖。"
        ),
        "resume_preview_pool": "合并后的 evidence-pool（预览）",
        "resume_preview_tree": "合并后的 skill-tree（预览）",
        "resume_apply": "写入 Profile",
        "resume_applied": "已写入：证据池、技能树，并已同步 SKILL.md。",
        "resume_err": "错误：{msg}",
        "resume_no_ai": "未配置 AI。请在 .env 中设置 LLM_API_KEY。",
        "resume_warn": "警告",
    },
}

_KANBAN: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Kanban · nblane",
        "title": "Kanban",
        "reload": "Reload from file",
        "save": "Save",
        "saved": "Saved to kanban.md",
        "metric_total": "Total",
        "metric_doing": "🔄 Doing",
        "metric_done": "✅ Done",
        "items_count": "{n} item(s)",
        "new_task": "New task",
        "new_task_ph": "+ Add task...",
        "detail": "Detail",
        "detail_ph": "context / why...",
        "add": "Add",
        "title": "Title",
        "details": "details",
        "details_ph": (
            "context / outcome / why / blocked by..."
        ),
        "move_to": "Move to",
        "kb_stay": "(stay)",
        "ingest_expander": "Done → evidence (AI)",
        "ingest_pick_done": "Select Done tasks",
        "ingest_generate": "Generate draft",
        "ingest_spinner": "Calling LLM…",
        "ingest_allow_status": "Allow AI to update node status",
        "ingest_allow_status_help": (
            "Off: ignores LLM status fields; only merges refs/evidence; "
            "locked nodes with new evidence become learning. "
            "On: applies LLM status only when it upgrades or stays at the "
            "same tier (never solid→learning, never expert→lower). "
            "LLM expert is saved as learning when that is an upgrade. "
            "Your YAML expert stays expert."
        ),
        "ingest_preview_pool": "Merged evidence-pool (preview)",
        "ingest_preview_tree": "Merged skill-tree (preview)",
        "ingest_apply": "Apply to profile",
        "ingest_applied": "Applied: pool, skill-tree, and SKILL.md sync.",
        "ingest_err": "Error: {msg}",
        "ingest_no_done": "No tasks in Done.",
        "ingest_no_ai": "AI not configured. Set LLM_API_KEY in .env.",
        "ingest_warn": "Warnings",
        "ingest_preview_source_done": (
            "Draft from Done tasks: {sources}"
        ),
    },
    "zh": {
        "page_title": "看板 · nblane",
        "title": "看板",
        "reload": "从文件重新加载",
        "save": "保存",
        "saved": "已保存到 kanban.md",
        "metric_total": "总计",
        "metric_doing": "🔄 进行中",
        "metric_done": "✅ 已完成",
        "items_count": "{n} 项",
        "new_task": "新任务",
        "new_task_ph": "+ 添加任务…",
        "detail": "详情",
        "detail_ph": "背景 / 原因…",
        "add": "添加",
        "title": "标题",
        "details": "详情",
        "details_ph": "背景 / 结果 / 阻塞…",
        "move_to": "移动到",
        "kb_stay": "（保持）",
        "ingest_expander": "已完成 → 证据（AI）",
        "ingest_pick_done": "选择「已完成」任务",
        "ingest_generate": "生成草案",
        "ingest_spinner": "调用 AI 中…",
        "ingest_allow_status": "允许 AI 更新节点状态",
        "ingest_allow_status_help": (
            "未勾选：合并时忽略 LLM 的 status，只写入证据与引用；"
            "有证据的 locked 节点会变为 learning。"
            "勾选：仅在「升级或持平」时写入 LLM 的 status（不会 solid→learning，"
            "不会把 expert 降级）；LLM 若输出 expert 会按 learning 档参与比较。"
            "YAML 里已标 expert 的节点不会被覆盖。"
        ),
        "ingest_preview_pool": "合并后的 evidence-pool（预览）",
        "ingest_preview_tree": "合并后的 skill-tree（预览）",
        "ingest_apply": "写入 Profile",
        "ingest_applied": "已写入：证据池、技能树，并已同步 SKILL.md。",
        "ingest_err": "错误：{msg}",
        "ingest_no_done": "「已完成」列为空。",
        "ingest_no_ai": "未配置 AI。请在 .env 中设置 LLM_API_KEY。",
        "ingest_warn": "警告",
        "ingest_preview_source_done": (
            "草案依据的「已完成」任务：{sources}"
        ),
    },
}

_TEAM: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Team View · nblane",
        "title": "Team View",
        "no_teams": (
            "No teams found. Create a team under `teams/` "
            "from the template."
        ),
        "team_select": "Team",
        "sub_team": "Team Info",
        "team_name": "Team name",
        "mission": "Mission / shared focus",
        "members": "Members (comma-separated)",
        "rules": "Shared rules (one per line)",
        "priorities": "Current priorities (one per line)",
        "save_team": "Save team.yaml",
        "team_saved": "team.yaml saved.",
        "sub_pool": "Product Pool",
        "items_count": "{n} item(s)",
        "field_title": "Title",
        "field_item": "Item",
        "add_pool": "Add to {label}",
        "add_pool_ph": "New {label} item...",
        "add": "Add",
        "save_pool": "Save product-pool.yaml",
        "pool_saved": "product-pool.yaml saved.",
    },
    "zh": {
        "page_title": "团队视图 · nblane",
        "title": "团队视图",
        "no_teams": (
            "未找到团队。请从模板在 `teams/` 下创建团队。"
        ),
        "team_select": "团队",
        "sub_team": "团队信息",
        "team_name": "团队名称",
        "mission": "使命 / 共同关注点",
        "members": "成员（逗号分隔）",
        "rules": "共同规则（每行一条）",
        "priorities": "当前优先级（每行一条）",
        "save_team": "保存 team.yaml",
        "team_saved": "已保存 team.yaml。",
        "sub_pool": "产品池",
        "items_count": "{n} 项",
        "field_title": "标题",
        "field_item": "条目",
        "add_pool": "添加到 {label}",
        "add_pool_ph": "新{label}条目…",
        "add": "添加",
        "save_pool": "保存 product-pool.yaml",
        "pool_saved": "已保存 product-pool.yaml。",
    },
}


def _lang() -> str:
    """Return ``en`` or ``zh``."""
    return llm_client.reply_language()


def common_ui() -> dict[str, str]:
    """Strings shared by sidebar and several pages."""
    lg = _lang()
    return dict(_COMMON.get(lg, _COMMON["en"]))


def gap_ui() -> dict[str, str]:
    """Gap Analysis page (includes common status labels)."""
    lg = _lang()
    merged = dict(_COMMON.get(lg, _COMMON["en"]))
    merged.update(_GAP.get(lg, _GAP["en"]))
    return merged


def skill_tree_ui() -> dict[str, str]:
    """Skill Tree page."""
    lg = _lang()
    merged = dict(_COMMON.get(lg, _COMMON["en"]))
    merged.update(_SKILL_TREE.get(lg, _SKILL_TREE["en"]))
    return merged


def kanban_ui() -> dict[str, str]:
    """Kanban page."""
    lg = _lang()
    merged = dict(_COMMON.get(lg, _COMMON["en"]))
    merged.update(_KANBAN.get(lg, _KANBAN["en"]))
    return merged


def team_ui() -> dict[str, str]:
    """Team View page."""
    lg = _lang()
    merged = dict(_COMMON.get(lg, _COMMON["en"]))
    merged.update(_TEAM.get(lg, _TEAM["en"]))
    return merged


def home_ui() -> dict[str, str]:
    """Home (`app.py`) — overview and SKILL.md editors."""
    lg = _lang()
    merged = dict(_COMMON.get(lg, _COMMON["en"]))
    st_lines = _SKILL_TREE.get(lg, _SKILL_TREE["en"])
    for key in (
        "metric_expert",
        "metric_solid",
        "metric_learning",
        "metric_locked",
        "metric_lit_rate",
        "progress_overall",
    ):
        merged[key] = st_lines[key]
    merged.update(_HOME.get(lg, _HOME["en"]))
    return merged


def status_label(ui: dict[str, str], raw: str) -> str:
    """Map schema status value to a display label."""
    key = f"status_{raw}"
    return ui.get(key, raw)


def kanban_section_label(section: str) -> str:
    """Display label for a kanban column key."""
    lg = _lang()
    table = _KANBAN_SEC.get(lg, _KANBAN_SEC["en"])
    return table.get(section, section)


def pool_label(pool_key: str) -> str:
    """Display label for a product-pool key."""
    lg = _lang()
    table = _POOL_LABEL.get(lg, _POOL_LABEL["en"])
    return table.get(pool_key, pool_key)


def all_pool_keys() -> tuple[str, ...]:
    """Stable key order for product-pool tabs."""
    return PRODUCT_POOL_KEYS


def kanban_move_option_label(opt: str, ui: dict[str, str]) -> str:
    """Label for move-to selectbox (stay or section key)."""
    if opt == "(stay)":
        return ui["kb_stay"]
    return kanban_section_label(opt)
