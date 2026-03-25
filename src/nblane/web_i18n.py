"""Streamlit UI strings for ``LLM_REPLY_LANG`` (en / zh).

Centralizes copy so all pages stay consistent with Gap Analysis.

Set ``NBLANE_UI_EMOJI=0`` (or ``false`` / ``no`` / ``off``) to drop
emoji prefixes in metrics and skill-status rows (see ``web_shared``).
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
        "profile_header": "## Current profile",
        "no_profiles_yet": "No profiles yet.",
        "no_profiles_main": (
            "No profiles. Create one in the sidebar."
        ),
        "select_profile_aria": "Active profile",
        "expander_create": "➕ New profile",
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
        "profile_header": "## 当前档案",
        "no_profiles_yet": "暂无档案。",
        "no_profiles_main": "暂无档案，请在侧边栏创建。",
        "select_profile_aria": "当前档案",
        "expander_create": "➕ 新建档案",
        "profile_name_label": "档案名称",
        "profile_name_ph": "例如 alice",
        "create": "创建",
        "name_empty": "名称不能为空。",
        "name_exists": "「{name}」已存在。",
        "profile_created": "已创建档案「{name}」。",
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
        "page_context_line": (
            "Agent OS: map a task to your skill tree; use rules "
            "and optional AI to plan next steps with your coding agent."
        ),
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
        "page_context_line": (
            "Agent 操作系统：将任务映射到技能树；结合规则与可选 AI，"
            "为与编程 Agent 协作准备下一步。"
        ),
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
        "page_context_line": (
            "Private OS: edit structured skills, inline evidence, "
            "and the shared evidence pool for this profile."
        ),
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
        "pool_list_heading": "Catalogued rows",
        "pool_delete_hint": (
            "Deleting removes the row from this editor; "
            "click Save to write YAML."
        ),
        "pool_prune_refs": (
            "When deleting: also remove this pool id from "
            "all skills (evidence_refs)"
        ),
        "pool_delete_remove": "Delete row",
        "pool_delete_blocked": (
            "Cannot delete `{pid}` — still linked from skills: "
            "{nodes}. Enable the option above or unlink first."
        ),
        "pool_deleted_session": (
            "Removed pool row from editor; click **Save** to persist."
        ),
    },
    "zh": {
        "page_title": "技能树 · nblane",
        "title": "技能树",
        "page_context_line": (
            "私人操作系统：编辑结构化技能、内联证据与本档案的共享证据池。"
        ),
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
        "pool_list_heading": "已登记条目",
        "pool_delete_hint": (
            "删除会从当前编辑区移除该行；需点击「保存」写入 YAML。"
        ),
        "pool_prune_refs": (
            "删除时同时从所有技能的 evidence_refs 中移除此池 id"
        ),
        "pool_delete_remove": "删除此行",
        "pool_delete_blocked": (
            "无法删除 `{pid}` — 以下技能仍引用：{nodes}。"
            "请勾选上方选项或先取消引用。"
        ),
        "pool_deleted_session": (
            "已从编辑区移除池条目；请点击**保存**以写入文件。"
        ),
    },
}

_HOME: dict[str, dict[str, str]] = {
    "en": {
        "app_page_title": "Home · nblane",
        "page_context_line": (
            "Private OS: skills, evidence, and SKILL.md for this "
            "profile — all plain files."
        ),
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
        "home_nav_compact": (
            "**Sidebar:** Skill Tree · Gap Analysis · Kanban · "
            "Team View. More: `docs/design.md`, "
            "`docs/web-ui-product.md`."
        ),
        "home_nav_expander": "Page map (detail)",
        "home_nav_detail": (
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
        "app_page_title": "首页 · nblane",
        "page_context_line": (
            "私人操作系统：本档案的技能、证据与 SKILL.md——"
            "均以本地文件为准。"
        ),
        "app_caption": (
            "当前档案：**{profile}** · "
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
        "home_nav_compact": (
            "**侧栏：** 技能树 · 差距分析 · 看板 · 团队视图。"
            "详见 `docs/zh/design.md`、`docs/zh/web-ui-product.md`。"
        ),
        "home_nav_expander": "页面说明（详细）",
        "home_nav_detail": (
            "**页面导航**（左侧菜单）：\n\n"
            "- **技能树** — 可视化与状态编辑\n"
            "- **差距分析** — 任务与能力匹配、缺口\n"
            "- **看板** — 当前任务\n"
            "- **团队视图** — 团队共享产品池"
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
        "page_context_line": (
            "Private OS: weekly execution board. Done items can be "
            "draft-ingested into evidence — review each proposal before "
            "apply."
        ),
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
        "task_field_title": "Title",
        "details": "details",
        "details_ph": (
            "context / outcome / why / blocked by..."
        ),
        "move_to": "Move to",
        "kb_stay": "(stay)",
        "kb_move_help": (
            "Buttons below only change which **column** the task is in "
            "(not a “completion status” menu)."
        ),
        "kb_auto_dates": "Auto-set started / completed dates on column move",
        "kb_auto_dates_help": (
            "When moving into Doing, sets started_on if empty. "
            "When moving into Done, sets completed_on if empty."
        ),
        "kb_more_fields": "More fields",
        "kb_more_fields_help": (
            "Optional notes, dates, or values kept when moving across "
            "columns."
        ),
        "kb_focus_mode": "Focus mode (Doing full width; other columns in tabs)",
        "kb_focus_mode_help": (
            "Hides the four-column grid. Use tabs for Queue, Done, and "
            "Someday / Maybe when you only want to execute."
        ),
        "kb_links_preview": "Links (click to open)",
        "kb_subtask_progress": "{done} / {total} subtasks done",
        "kb_wip_hint": (
            "Doing has {n} tasks — consider limiting work in progress."
        ),
        "kb_done_column_expander": "Show and edit Done ({n})",
        "kb_done_column_hint": (
            "Expand to add, edit, or archive completed tasks."
        ),
        "kb_task_details": "Details & subtasks",
        "kb_edit_task": "Edit",
        "kb_done_editing": "Done editing",
        "kb_tap_title_to_edit": "Click the title to edit this task",
        "kb_read_subtasks_hint": "Subtasks — check off when done",
        "kb_edit_exit_hint": (
            "Click outside the board cannot close edit mode. "
            "Use \"Done editing\" below (Enter does not apply to all fields)."
        ),
        "kb_card_actions": "⋯",
        "kb_card_delete_hint": "Removing a task cannot be undone here.",
        "kb_delete_card": "Delete task",
        "kb_move_to_label": "Move to",
        "kb_confirm_move": "Move",
        "kb_read_new_subtask_ph": "New subtask…",
        "new_context": "Context",
        "new_context_ph": "What this is / background",
        "new_why": "Why",
        "new_why_ph": "Why this matters",
        "new_blocked": "Blocked by",
        "new_blocked_ph": "Dependency or blocker",
        "new_outcome": "Outcome",
        "new_outcome_ph": "What you delivered",
        "field_context": "context",
        "field_why": "why",
        "field_blocked": "blocked by",
        "field_outcome": "outcome",
        "field_started": "started_on",
        "field_completed": "completed_on",
        "subtasks_label": "Subtasks (checkbox)",
        "add_subtask": "+ Subtask",
        "crystallized": "Crystallized (ingested)",
        "done_bulk_title": "Done column housekeeping",
        "done_bulk_pick": "Select Done tasks",
        "archive_done": "Archive selected",
        "delete_done": "Delete selected",
        "ingest_select_rows": "Choose which draft rows to apply",
        "ingest_adopt_evidence": "Adopt evidence row",
        "ingest_adopt_node": "Adopt node update",
        "ingest_apply_selected": "Apply selected rows",
        "ingest_apply_all": "Apply full draft",
        "ingest_mark_crystallized": (
            "After apply, mark source Done tasks as crystallized"
        ),
        "ingest_filter_warn": "Subset filter",
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
        "ingest_rationale": "Rationale",
        "ingest_excerpt": "Source excerpt",
    },
    "zh": {
        "page_title": "看板 · nblane",
        "title": "看板",
        "page_context_line": (
            "私人操作系统 · 执行面：本周任务看板。「已完成」可经 AI 生成摄入草案，"
            "请按条审阅后再写入。"
        ),
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
        "task_field_title": "标题",
        "details": "详情",
        "details_ph": "背景 / 结果 / 阻塞…",
        "move_to": "移动到",
        "kb_stay": "（留在本列）",
        "kb_move_help": (
            "下方按钮只改变任务所在**列**，不是「完成状态」菜单。"
        ),
        "kb_auto_dates": "移动列时自动填写开始/结束日期",
        "kb_auto_dates_help": (
            "移入「进行中」时若 started_on 为空则填当天；"
            "移入「已完成」时若 completed_on 为空则填当天。"
        ),
        "kb_more_fields": "更多字段",
        "kb_more_fields_help": (
            "可选补充、日期，或从其他列带过来需要保留的字段。"
        ),
        "kb_focus_mode": "专注模式（进行中全宽，其余列在标签页）",
        "kb_focus_mode_help": (
            "隐藏四列并排布局；需要时再在标签中打开「排队」「已完成」「以后再说」。"
        ),
        "kb_links_preview": "链接（点击打开）",
        "kb_subtask_progress": "子任务 {done} / {total} 已完成",
        "kb_wip_hint": (
            "「进行中」已有 {n} 项，可考虑控制并行数量（WIP）。"
        ),
        "kb_done_column_expander": "展开查看并编辑「已完成」（{n} 项）",
        "kb_done_column_hint": "展开后可添加、编辑或配合上方区块归档已完成任务。",
        "kb_task_details": "详情与子任务",
        "kb_edit_task": "编辑",
        "kb_done_editing": "收起编辑",
        "kb_tap_title_to_edit": "点击标题进入编辑",
        "kb_read_subtasks_hint": "子任务 — 完成后可勾选",
        "kb_edit_exit_hint": (
            "无法在空白处退出编辑；请点下方「收起编辑」"
            "（Enter 不会对所有字段生效）。"
        ),
        "kb_card_actions": "⋯",
        "kb_card_delete_hint": "删除后无法在此恢复。",
        "kb_delete_card": "删除任务",
        "kb_move_to_label": "移动到",
        "kb_confirm_move": "移动",
        "kb_read_new_subtask_ph": "新子任务…",
        "new_context": "背景",
        "new_context_ph": "这件事是什么 / 上下文",
        "new_why": "原因",
        "new_why_ph": "为什么要做",
        "new_blocked": "阻塞",
        "new_blocked_ph": "依赖或阻塞项",
        "new_outcome": "结果",
        "new_outcome_ph": "交付或产出",
        "field_context": "背景 context",
        "field_why": "原因 why",
        "field_blocked": "阻塞 blocked by",
        "field_outcome": "结果 outcome",
        "field_started": "开始日 started_on",
        "field_completed": "结束日 completed_on",
        "subtasks_label": "子任务（可勾选）",
        "add_subtask": "+ 子任务",
        "crystallized": "已结晶（已摄入）",
        "done_bulk_title": "「已完成」列整理",
        "done_bulk_pick": "选择已完成任务",
        "archive_done": "归档所选",
        "delete_done": "删除所选",
        "ingest_select_rows": "选择要应用的草案条目",
        "ingest_adopt_evidence": "采纳该证据行",
        "ingest_adopt_node": "采纳该节点更新",
        "ingest_apply_selected": "应用所选条目",
        "ingest_apply_all": "应用完整草案",
        "ingest_mark_crystallized": "应用后将来源「已完成」任务标为已结晶",
        "ingest_filter_warn": "子集过滤",
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
        "ingest_rationale": "理由",
        "ingest_excerpt": "原文摘录",
    },
}

_TEAM: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Team View · nblane",
        "title": "Team View",
        "page_context_line": (
            "Team OS: edit shared team.yaml and product pool files "
            "under teams/."
        ),
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
        "team_profile_scope": (
            "Sidebar profile **{profile}** applies to Home, Skill Tree, "
            "Gap, and Kanban. Team data is stored under **teams/** and is "
            "not filtered by profile."
        ),
    },
    "zh": {
        "page_title": "团队视图 · nblane",
        "title": "团队视图",
        "page_context_line": (
            "团队操作系统：维护 teams/ 下的 team.yaml 与共享产品池。"
        ),
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
        "team_profile_scope": (
            "侧栏所选档案 **{profile}** 用于首页、技能树、差距分析与看板。"
            "团队数据在 **teams/** 下，不按档案过滤。"
        ),
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
