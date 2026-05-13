"""Streamlit UI strings for ``UI_LANG`` (en / zh).

Centralizes copy so all pages stay consistent with Gap Analysis.

Set ``NBLANE_UI_EMOJI=0`` (or ``false`` / ``no`` / ``off``) to drop
emoji prefixes in metrics and skill-status rows (see ``web_shared``).
"""

from __future__ import annotations

from nblane.core import llm as llm_client
from nblane.core.io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
)

# Kanban file sections are English keys; this is display-only.
_KANBAN_SEC: dict[str, dict[str, str]] = {
    "en": {
        KANBAN_DOING: KANBAN_DOING,
        KANBAN_DONE: KANBAN_DONE,
        KANBAN_QUEUE: KANBAN_QUEUE,
        KANBAN_SOMEDAY: KANBAN_SOMEDAY,
    },
    "zh": {
        KANBAN_DOING: "进行中",
        KANBAN_DONE: "已完成",
        KANBAN_QUEUE: "队列",
        KANBAN_SOMEDAY: "也许 / 将来",
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
            "Set an API key in the sidebar AI / LLM settings, "
            "or add `LLM_API_KEY` to `.env`."
        ),
        "llm_settings_title": "AI / LLM",
        "llm_provider": "Provider",
        "llm_base_url": "Base URL",
        "llm_model": "Model",
        "llm_custom_model": "Custom model",
        "llm_custom_model_choice": "Custom…",
        "llm_api_key": "API key",
        "llm_api_key_help": (
            "Session only. Leave blank to keep an existing key from "
            "this session or .env."
        ),
        "llm_ui_lang": "Interface language",
        "llm_reply_lang": "Model reply language",
        "llm_reply_lang_en": "English",
        "llm_reply_lang_zh": "Chinese",
        "llm_configured": "AI enabled: {label}",
        "llm_not_configured": "API key is not set.",
        "llm_session_only": (
            "These settings apply to this app session and are not "
            "written to disk."
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
        "goal_strip_hidden": "Goal set",
        "goal_strip_default_label": "Stage goal",
        "goal_strip_status": "Status",
        "goal_strip_target": "Target",
        "goal_strip_focus": "Focus",
        "goal_status_active": "Active",
        "goal_status_paused": "Paused",
        "goal_status_completed": "Completed",
        "goal_status_archived": "Archived",
        "goal_visibility_visible": "Visible",
        "goal_visibility_discreet": "Discreet",
        "goal_visibility_hidden": "Hidden",
        "goal_visibility_private": "Private",
        "goal_no_current": "No current goal set.",
        "goal_presence_current": "Current goal",
        "goal_presence_details": "Goal details",
        "goal_presence_edit_home": "Edit on Home.",
        "goal_presence_hidden_note": (
            "Goal details are hidden on regular pages."
        ),
        "goal_presence_agent_context_on": "Agent context enabled",
        "goal_presence_agent_context_off": "Agent context disabled",
        "sidebar_nav_title": "Workspace",
        "sidebar_nav_home_group": "Home",
        "sidebar_nav_work_group": "Work",
        "sidebar_nav_growth_group": "Growth",
        "sidebar_nav_output_group": "Output",
        "sidebar_nav_team_group": "Team",
        "sidebar_nav_dashboard": "Daily Dashboard",
        "sidebar_nav_kanban": "Kanban",
        "sidebar_nav_evidence_review": "Evidence Review",
        "sidebar_nav_research": "Research",
        "sidebar_nav_skill_map": "Skill Map",
        "sidebar_nav_gap": "Gap Analysis",
        "sidebar_nav_health": "Profile Health",
        "sidebar_nav_public": "Public Site",
        "sidebar_nav_team": "Team View",
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
            "可在侧边栏 AI / LLM 设置里填写 API key，"
            "也可在 `.env` 中设置 `LLM_API_KEY`。"
        ),
        "llm_settings_title": "AI / LLM",
        "llm_provider": "服务商",
        "llm_base_url": "Base URL",
        "llm_model": "模型",
        "llm_custom_model": "自定义模型",
        "llm_custom_model_choice": "自定义…",
        "llm_api_key": "API key",
        "llm_api_key_help": (
            "仅当前会话生效。留空会继续使用本会话或 .env 中已有的 key。"
        ),
        "llm_ui_lang": "界面语言",
        "llm_reply_lang": "模型回复语言",
        "llm_reply_lang_en": "英文",
        "llm_reply_lang_zh": "中文",
        "llm_configured": "AI 已启用：{label}",
        "llm_not_configured": "尚未设置 API key。",
        "llm_session_only": "这些设置只应用到当前页面会话，不会写入磁盘。",
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
        "goal_strip_hidden": "目标已设置",
        "goal_strip_default_label": "阶段目标",
        "goal_strip_status": "状态",
        "goal_strip_target": "目标日期",
        "goal_strip_focus": "当前重点",
        "goal_status_active": "进行中",
        "goal_status_paused": "暂停",
        "goal_status_completed": "已完成",
        "goal_status_archived": "已归档",
        "goal_visibility_visible": "完整显示",
        "goal_visibility_discreet": "低调显示",
        "goal_visibility_hidden": "只显示已设置",
        "goal_visibility_private": "私密",
        "goal_no_current": "尚未设置 current goal。",
        "goal_presence_current": "当前目标",
        "goal_presence_details": "目标详情",
        "goal_presence_edit_home": "在首页编辑。",
        "goal_presence_hidden_note": "普通页面已隐藏目标详情。",
        "goal_presence_agent_context_on": "已进入 Agent 上下文",
        "goal_presence_agent_context_off": "未进入 Agent 上下文",
        "sidebar_nav_title": "工作区",
        "sidebar_nav_home_group": "Home",
        "sidebar_nav_work_group": "Work",
        "sidebar_nav_growth_group": "Growth",
        "sidebar_nav_output_group": "Output",
        "sidebar_nav_team_group": "Team",
        "sidebar_nav_dashboard": "Daily Dashboard",
        "sidebar_nav_kanban": "看板",
        "sidebar_nav_evidence_review": "Evidence Review",
        "sidebar_nav_research": "Research",
        "sidebar_nav_skill_map": "Skill Map",
        "sidebar_nav_gap": "差距分析",
        "sidebar_nav_health": "Profile Health",
        "sidebar_nav_public": "Public Site",
        "sidebar_nav_team": "Team View",
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
        "use_goal_context": "Use current goal context",
        "goal_context_used": "Current goal context is included in this analysis.",
        "goal_context_not_used": "Current goal context is not included.",
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
        "use_goal_context": "使用 current goal 作为分析上下文",
        "goal_context_used": "本次分析已包含 current goal context。",
        "goal_context_not_used": "本次分析未包含 current goal context。",
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
        "evidence_review_link": "Open Evidence Review",
        "evidence_signal_count": "{n} evidence",
        "evidence_signal_strength": "strength: {strength}",
        "evidence_signal_review": "review: {status}",
        "evidence_signal_missing": "Missing evidence",
        "evidence_signal_risk": "Evidence risk: {reason}",
        "evidence_strength_unrated": "unrated",
        "evidence_strength_weak": "weak",
        "evidence_strength_medium": "medium",
        "evidence_strength_strong": "strong",
        "evidence_strength_high_trust": "high trust",
        "evidence_review_status_needs_review": "needs review",
        "evidence_review_status_reviewed": "reviewed",
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
        "evidence_review_link": "打开 Evidence Review",
        "evidence_signal_count": "{n} 条 evidence",
        "evidence_signal_strength": "强度：{strength}",
        "evidence_signal_review": "审阅：{status}",
        "evidence_signal_missing": "缺少 evidence",
        "evidence_signal_risk": "Evidence 风险：{reason}",
        "evidence_strength_unrated": "未评级",
        "evidence_strength_weak": "弱",
        "evidence_strength_medium": "中",
        "evidence_strength_strong": "强",
        "evidence_strength_high_trust": "高可信",
        "evidence_review_status_needs_review": "待审阅",
        "evidence_review_status_reviewed": "已审阅",
    },
}

_EVIDENCE_REVIEW: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Evidence Review · nblane",
        "title": "Evidence Review",
        "page_context_line": (
            "Review Done work, evidence-pool rows, skill links, and "
            "strength risks before skill status becomes a claim."
        ),
        "save_pool": "Save evidence pool",
        "saved_pool": "Saved evidence-pool.yaml.",
        "saved_pool_synced": "Saved evidence-pool.yaml and synced SKILL.md.",
        "metric_done_uncrystallized": "Done not crystallized",
        "metric_unlinked": "Unlinked evidence",
        "metric_needs_review": "Needs review",
        "metric_status_risk": "Status evidence risk",
        "tab_queue": "Review Queue",
        "tab_pool": "Evidence Pool",
        "tab_links": "Skill Links",
        "tab_refs": "Project / Experience Refs",
        "tab_risks": "Status Risks",
        "done_queue_title": "Done -> evidence candidates",
        "done_queue_empty": "No Done tasks waiting for evidence review.",
        "done_generate": "Generate Done -> evidence draft",
        "done_pick": "Pick Done tasks",
        "done_allow_status": "Allow AI status updates",
        "done_allow_status_help": (
            "Off: merge evidence and refs only; locked nodes with evidence "
            "may become learning. On: AI status is still upgrade-only and "
            "expert is never trusted automatically."
        ),
        "done_mark_crystallized": "Mark selected Done tasks crystallized after apply",
        "done_preview_source": "Source Done tasks: {sources}",
        "done_no_ai": "AI is not configured.",
        "done_spinner": "Generating evidence draft...",
        "done_apply_selected": "Apply selected",
        "done_apply_all": "Apply all",
        "done_applied": "Applied evidence draft.",
        "review_rows_title": "Pool rows needing review",
        "review_rows_empty": "No evidence rows need review.",
        "unlinked_rows_title": "Unlinked evidence",
        "unlinked_rows_empty": "All active evidence rows are linked to skills.",
        "pool_add_title": "Add evidence row",
        "pool_edit_title": "Edit evidence rows",
        "pool_empty": "No evidence rows yet.",
        "pool_deprecate": "Deprecate",
        "pool_deprecated": "Deprecated evidence row.",
        "pool_add": "Add evidence",
        "pool_added": "Added evidence row.",
        "pool_update": "Update row",
        "pool_updated": "Updated evidence row.",
        "pool_id": "Evidence id",
        "pool_type": "Type",
        "pool_title": "Title",
        "pool_date": "Date",
        "pool_url": "URL",
        "pool_summary": "Summary",
        "pool_strength": "Strength",
        "pool_confidence": "Confidence",
        "pool_review_status": "Review status",
        "pool_public_readiness": "Public readiness",
        "pool_source_refs": "Source refs (one per line)",
        "pool_project_refs": "Project refs",
        "pool_experience_refs": "Experience refs",
        "pool_replaced_by": "Replaced by",
        "pool_title_required": "Evidence title is required.",
        "pool_id_exists": "Evidence id already exists: {id}",
        "link_title": "Link evidence to skills",
        "link_pick_evidence": "Evidence row",
        "link_pick_skills": "Skills",
        "link_button": "Link selected skills",
        "link_done": "Linked evidence to selected skills.",
        "link_empty": "No active evidence rows are available to link.",
        "refs_options_title": "Available ref targets",
        "refs_options_empty": "No records yet.",
        "refs_projects": "Project cases",
        "refs_experiences": "Experience cases",
        "refs_sources": "Research sources",
        "refs_linker_title": "Link evidence to project / experience / source",
        "refs_manual_source_refs": "Manual source refs not in Research Inbox",
        "refs_save": "Save refs",
        "refs_saved": "Saved evidence refs.",
        "refs_evidence_missing": "Evidence row was not found.",
        "refs_case_editor_title": "Minimal case editor",
        "refs_case_id": "ID",
        "refs_project_title": "Project title",
        "refs_experience_organization": "Organization",
        "refs_experience_role": "Role",
        "refs_experience_location": "Location",
        "refs_status": "Status",
        "refs_kind": "Kind",
        "refs_visibility": "Visibility",
        "refs_time_range": "Time range",
        "refs_summary": "Summary",
        "refs_goal_refs": "Goal refs",
        "refs_task_refs": "Task refs",
        "refs_output_refs": "Output refs",
        "refs_notes": "Notes",
        "refs_add_project": "Add project case",
        "refs_add_experience": "Add experience case",
        "refs_case_saved": "Saved case.",
        "risk_empty": "No solid/expert evidence-strength risks.",
        "open_skill_tree": "Open Skill Tree",
        "strength_unrated": "unrated",
        "strength_weak": "weak",
        "strength_medium": "medium",
        "strength_strong": "strong",
        "strength_high_trust": "high trust",
        "confidence_empty": "unset",
        "confidence_low": "low",
        "confidence_medium": "medium",
        "confidence_high": "high",
        "review_status_needs_review": "needs review",
        "review_status_reviewed": "reviewed",
        "public_readiness_private": "private",
        "public_readiness_draftable": "draftable",
        "public_readiness_public_ready": "public ready",
        "public_readiness_published": "published",
        "row_meta": "{type} · {strength} · {review_status}",
        "row_usage": "Skills: {skills}",
        "row_unlinked": "No linked skills",
        "risk_line": "{label} is {status}; highest {highest}, expected {required}+.",
        "merge_preview_title": "Preview delta",
        "merge_preview_pool": "Merged evidence-pool preview",
        "merge_preview_tree": "Merged skill-tree preview",
    },
    "zh": {
        "page_title": "Evidence Review · nblane",
        "title": "Evidence Review",
        "page_context_line": (
            "审阅 Done 工作、evidence-pool 条目、技能关联与强度风险，"
            "避免 skill status 变成没有证据支撑的 claim。"
        ),
        "save_pool": "保存证据池",
        "saved_pool": "已保存 evidence-pool.yaml。",
        "saved_pool_synced": "已保存 evidence-pool.yaml，并同步 SKILL.md。",
        "metric_done_uncrystallized": "Done 未结晶",
        "metric_unlinked": "未挂技能",
        "metric_needs_review": "待审阅",
        "metric_status_risk": "状态证据风险",
        "tab_queue": "审阅队列",
        "tab_pool": "Evidence Pool",
        "tab_links": "技能关联",
        "tab_refs": "项目 / 经历引用",
        "tab_risks": "状态风险",
        "done_queue_title": "Done -> evidence 候选",
        "done_queue_empty": "没有等待 evidence review 的 Done 任务。",
        "done_generate": "生成 Done -> evidence 草案",
        "done_pick": "选择 Done 任务",
        "done_allow_status": "允许 AI 更新状态",
        "done_allow_status_help": (
            "关闭：只合并 evidence 与引用；有 evidence 的 locked 节点可变为 "
            "learning。开启：AI status 仍只允许升级，expert 不会被自动采信。"
        ),
        "done_mark_crystallized": "应用后标记所选 Done 任务为已结晶",
        "done_preview_source": "来源 Done 任务：{sources}",
        "done_no_ai": "未配置 AI。",
        "done_spinner": "生成 evidence 草案中…",
        "done_apply_selected": "应用所选",
        "done_apply_all": "应用全部",
        "done_applied": "已应用 evidence 草案。",
        "review_rows_title": "需要审阅的池条目",
        "review_rows_empty": "没有需要审阅的 evidence 条目。",
        "unlinked_rows_title": "未挂技能的 evidence",
        "unlinked_rows_empty": "所有活跃 evidence 都已关联技能。",
        "pool_add_title": "新增 evidence 条目",
        "pool_edit_title": "编辑 evidence 条目",
        "pool_empty": "尚无 evidence 条目。",
        "pool_deprecate": "软下线",
        "pool_deprecated": "已软下线 evidence 条目。",
        "pool_add": "添加 evidence",
        "pool_added": "已添加 evidence 条目。",
        "pool_update": "更新条目",
        "pool_updated": "已更新 evidence 条目。",
        "pool_id": "Evidence id",
        "pool_type": "类型",
        "pool_title": "标题",
        "pool_date": "日期",
        "pool_url": "链接",
        "pool_summary": "摘要",
        "pool_strength": "强度",
        "pool_confidence": "置信度",
        "pool_review_status": "审阅状态",
        "pool_public_readiness": "公开准备度",
        "pool_source_refs": "Source refs（每行一项）",
        "pool_project_refs": "Project refs",
        "pool_experience_refs": "Experience refs",
        "pool_replaced_by": "替代条目",
        "pool_title_required": "Evidence 标题不能为空。",
        "pool_id_exists": "Evidence id 已存在：{id}",
        "link_title": "把 evidence 关联到技能",
        "link_pick_evidence": "Evidence 条目",
        "link_pick_skills": "技能",
        "link_button": "关联所选技能",
        "link_done": "已把 evidence 关联到所选技能。",
        "link_empty": "没有可关联的活跃 evidence 条目。",
        "refs_options_title": "可关联对象",
        "refs_options_empty": "暂无记录。",
        "refs_projects": "Project cases",
        "refs_experiences": "Experience cases",
        "refs_sources": "Research sources",
        "refs_linker_title": "关联 evidence 到项目 / 经历 / 来源",
        "refs_manual_source_refs": "Research Inbox 之外的手动 source refs",
        "refs_save": "保存引用",
        "refs_saved": "已保存 evidence refs。",
        "refs_evidence_missing": "未找到 evidence 条目。",
        "refs_case_editor_title": "最小 case 编辑器",
        "refs_case_id": "ID",
        "refs_project_title": "项目标题",
        "refs_experience_organization": "组织 / 公司",
        "refs_experience_role": "角色",
        "refs_experience_location": "地点",
        "refs_status": "状态",
        "refs_kind": "类型",
        "refs_visibility": "可见性",
        "refs_time_range": "时间范围",
        "refs_summary": "摘要",
        "refs_goal_refs": "Goal refs",
        "refs_task_refs": "Task refs",
        "refs_output_refs": "Output refs",
        "refs_notes": "备注",
        "refs_add_project": "新增 project case",
        "refs_add_experience": "新增 experience case",
        "refs_case_saved": "已保存 case。",
        "risk_empty": "没有 solid/expert 证据强度风险。",
        "open_skill_tree": "打开技能树",
        "strength_unrated": "未评级",
        "strength_weak": "弱",
        "strength_medium": "中",
        "strength_strong": "强",
        "strength_high_trust": "高可信",
        "confidence_empty": "未设置",
        "confidence_low": "低",
        "confidence_medium": "中",
        "confidence_high": "高",
        "review_status_needs_review": "待审阅",
        "review_status_reviewed": "已审阅",
        "public_readiness_private": "私有",
        "public_readiness_draftable": "可整理",
        "public_readiness_public_ready": "可公开",
        "public_readiness_published": "已发布",
        "row_meta": "{type} · {strength} · {review_status}",
        "row_usage": "技能：{skills}",
        "row_unlinked": "未关联技能",
        "risk_line": "{label} 为 {status}；最高 {highest}，期望 {required}+。",
        "merge_preview_title": "变更预览",
        "merge_preview_pool": "合并后的 evidence-pool 预览",
        "merge_preview_tree": "合并后的 skill-tree 预览",
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
        "dashboard_status_overview": "Status overview",
        "dashboard_metric_goal": "Current goal",
        "dashboard_primary_goal": "Primary goal",
        "dashboard_active_goal": "Active goal",
        "dashboard_active_goals_title": "Active goals",
        "dashboard_goal_set": "Set",
        "dashboard_goal_missing": "Missing",
        "dashboard_metric_skill_lit": "Lit skills",
        "dashboard_skill_progress_suffix": "solid / expert",
        "dashboard_metric_doing": "Doing",
        "dashboard_metric_pending_evidence": "Evidence to review",
        "dashboard_metric_health": "Health E/W/I",
        "dashboard_metric_health_help": "Errors / warnings / info from Profile Health.",
        "dashboard_public_not_initialized": (
            "Public layer is not initialized yet; this dashboard only links to setup."
        ),
        "dashboard_doing_title": "This week's Doing",
        "dashboard_doing_empty": "No Doing tasks yet. Open Kanban to choose the week's active work.",
        "dashboard_doing_started": "started {date}",
        "dashboard_doing_blocked": "Blocked by: {blocked}",
        "dashboard_doing_more": "+{n} more Doing task(s) on Kanban.",
        "dashboard_pending_evidence_title": "Evidence to organize",
        "dashboard_done_uncrystallized": "Done not crystallized",
        "dashboard_unlinked_evidence": "Unlinked pool rows",
        "dashboard_needs_review_evidence": "Evidence needing review",
        "dashboard_status_risk_evidence": "Skill status evidence risks",
        "dashboard_pending_evidence_empty": "No pending evidence review found.",
        "dashboard_health_title": "Health",
        "dashboard_health_errors": "Errors",
        "dashboard_health_warnings": "Warnings",
        "dashboard_health_info": "Info",
        "dashboard_health_context_ready": "Context ready",
        "dashboard_health_empty": "Profile Health has no issues.",
        "dashboard_yes": "Yes",
        "dashboard_no": "No",
        "dashboard_output_title": "Output",
        "dashboard_output_empty": "Public layer has no summary yet. Open Public Site to initialize drafts.",
        "dashboard_public_drafts": "Drafts",
        "dashboard_public_published": "Published",
        "dashboard_public_visibility": "Visibility",
        "dashboard_public_build": "Build",
        "dashboard_public_build_exists": "Built",
        "dashboard_public_build_missing": "Not built",
        "dashboard_public_build_detail": "{pages} HTML page(s) at `{path}`.",
        "dashboard_quick_title": "Quick actions",
        "dashboard_overview_map_title": "Map of now",
        "dashboard_graph_eyebrow": "Context",
        "dashboard_graph_title": "Context Canvas",
        "dashboard_graph_goal_missing": "Set current goal",
        "dashboard_graph_blocked": "Blocked",
        "dashboard_evidence_inbox_title": "Evidence inbox",
        "dashboard_open_section": "Open",
        "dashboard_goal_create_inline": "Create goal",
        "dashboard_goal_edit_inline": "Edit goal",
        "dashboard_goal_close_form": "Close",
        "dashboard_goal_advanced_fields": "Advanced goal fields",
        "dashboard_ai_ready": "AI ready",
        "dashboard_ai_not_ready": "AI off",
        "north_star_strip_title": "North Star",
        "north_star_empty": "No North Star set",
        "north_star_empty_action": "Add North Star",
        "north_star_hidden_display": "North Star set",
        "north_star_private_display": "Private North Star",
        "north_star_edit_action": "Edit Profile Context",
        "north_star_visibility_visible": "Visible",
        "north_star_visibility_discreet": "Discreet",
        "north_star_visibility_hidden": "Hidden",
        "north_star_visibility_private": "Private",
        "skill_alignment_title": "Skill Alignment",
        "skill_alignment_confirmed": "Confirmed links",
        "skill_alignment_candidates": "Candidates",
        "skill_alignment_no_links": "No confirmed skill links yet.",
        "skill_alignment_no_candidates": "Run rule match or AI match to get candidates.",
        "skill_alignment_rule": "Rule match",
        "skill_alignment_ai": "AI match",
        "skill_alignment_confirm": "Confirm links",
        "skill_alignment_manual_label": "Manual add",
        "skill_alignment_manual_add": "Add",
        "skill_alignment_suggested": "suggested",
        "skill_alignment_gap_hint": "Linked locked/learning nodes may need Gap Analysis.",
        "goal_alignment_goal_missing": "No goal found for skill alignment.",
        "goal_alignment_node_missing": "That skill node is not available in the current schema.",
        "goal_alignment_candidates_ready": "{n} skill candidate(s) ready for review.",
        "goal_alignment_links_saved": "Goal-skill links saved.",
        "goal_primary_saved": "Primary goal updated.",
        "goal_archived": "Goal archived.",
        "dashboard_add_active_goal": "+ Active Goal",
        "dashboard_archive_goal": "Archive",
        "dashboard_inspector_empty": "Select a node to inspect it.",
        "dashboard_inspector_node_hint": "Open the owner page for details.",
        "dashboard_inspector_placeholder_hint": "This area is still scaffolded and does not have a backing record yet.",
        "dashboard_inspector_locked_hint": "Private or locked details are hidden in this view.",
        "dashboard_inspector_owner_reserved": "Setup state",
        "dashboard_placeholder_metric": "Planned",
        "dashboard_inspector_setup_title": "Choose a real node or finish setup",
        "dashboard_inspector_setup_hint": "This graph is still mostly scaffolded. Start with North Star, then set a current goal.",
        "dashboard_today_current_focus": "Current focus",
        "dashboard_today_capture_sources": "Capture / Sources",
        "dashboard_today_evidence_review": "Evidence review",
        "dashboard_today_gap_next_action": "Gap / Next action",
        "dashboard_today_output_feedback": "Output / Feedback",
        "dashboard_capture_title": "Capture source",
        "dashboard_capture_submit": "Capture",
        "dashboard_capture_saved": "Captured source {id}.",
        "dashboard_capture_title_required": "Capture title is required.",
        "dashboard_capture_title_placeholder": "What did you notice?",
        "dashboard_capture_raw_text": "Note",
        "dashboard_capture_source": "Source URL or origin",
        "dashboard_capture_tags": "Tags",
        "dashboard_capture_goal": "Goal",
        "dashboard_capture_type": "Type",
        "dashboard_capture_type_note": "Note",
        "dashboard_capture_type_link": "Link",
        "dashboard_capture_type_resource": "Resource",
        "dashboard_capture_type_idea": "Idea",
        "dashboard_source_inbox_title": "Source inbox",
        "dashboard_source_inbox_empty": "No source items captured yet.",
        "dashboard_source_to_evidence_hint": "Captured sources stay in inbox until reviewed into evidence candidates.",
        "dashboard_atomic_evidence_title": "Atomic evidence",
        "dashboard_evidence_candidate_title": "Evidence candidates",
        "dashboard_atomic_evidence_unlinked": "Unlinked atomic rows",
        "dashboard_atomic_evidence_needs_review": "Needs review",
        "dashboard_atomic_evidence_status_risk": "Status risks",
        "dashboard_gap_risk_title": "Gap risk",
        "dashboard_feedback_planned": "Feedback surface is still in setup.",
        "dashboard_graph_loading": "Loading graph...",
        "dashboard_graph_3d_hint": (
            "North Star flows through goals, work context, activity, sources, "
            "evidence, claims, capability, output, feedback, and governance."
        ),
        "dashboard_view_canvas": "2D Canvas",
        "dashboard_view_3d_graph": "3D Graph",
        "dashboard_workbench_title": "Workbench",
        "dashboard_workbench_caption": "Today's signals, capture inbox, and quick actions.",
        "dashboard_canvas_setup_title": "The canvas is still in setup",
        "dashboard_canvas_setup_hint": (
            "Add North Star and a current goal first, then capture sources to replace the skeleton."
        ),
        "dashboard_canvas_missing_north_star": "North Star missing",
        "dashboard_canvas_missing_goal": "Current goal missing",
        "dashboard_canvas_missing_sources": "No captured sources yet",
        "dashboard_canvas_reset_filters": "Show all layers",
        "dashboard_canvas_no_layers": "All layers are hidden.",
        "dashboard_skill_progress_title": "Skill Progress",
        "dashboard_skill_progress_caption": "solid + expert lit rate",
        "dashboard_skill_progress_empty": "No skill tree data yet.",
        "dashboard_skill_lit_rate": "Lit rate",
        "dashboard_skill_status_expert": "Expert",
        "dashboard_skill_status_solid": "Solid",
        "dashboard_skill_status_learning": "Learning",
        "dashboard_skill_status_locked": "Locked",
        "dashboard_node_north_star": "North Star",
        "dashboard_node_goal": "Goal",
        "dashboard_node_skill": "Skills",
        "dashboard_node_task": "Tasks",
        "dashboard_node_project_case": "Project Cases",
        "dashboard_private_project_case": "Private project case",
        "dashboard_node_daily_work": "Daily Work",
        "dashboard_node_research": "Research",
        "dashboard_node_agent_run": "Agent Runs",
        "dashboard_node_source": "Sources",
        "dashboard_node_evidence_candidate": "Evidence Candidates",
        "dashboard_node_atomic_evidence": "Atomic Evidence",
        "dashboard_node_composite_evidence": "Composite Evidence",
        "dashboard_node_claim": "Claims",
        "dashboard_node_evidence": "Evidence",
        "dashboard_node_gap": "Gap",
        "dashboard_node_next_action": "Next Action",
        "dashboard_node_output": "Output",
        "dashboard_node_feedback": "Feedback",
        "dashboard_node_capacity": "North Star Capacity",
        "dashboard_node_health": "Health",
        "dashboard_layer_direction": "Direction",
        "dashboard_layer_objective": "Objective",
        "dashboard_layer_work_context": "Work Context",
        "dashboard_layer_activity": "Activity",
        "dashboard_layer_source": "Source",
        "dashboard_layer_evidence": "Evidence",
        "dashboard_layer_claim": "Claim",
        "dashboard_layer_capability": "Capability",
        "dashboard_layer_output": "Output",
        "dashboard_layer_feedback": "Feedback",
        "dashboard_layer_governance": "Governance",
        "dashboard_set_as_primary": "Set as primary",
        "dashboard_set_primary": "Set primary",
        "quick_skill_tree": "Skill Tree",
        "quick_skill_tree_help": "Edit skill status and evidence refs.",
        "quick_evidence_review": "Evidence Review",
        "quick_evidence_review_help": "Review evidence strength, links, and Done crystallization.",
        "quick_research": "Research",
        "quick_research_help": "Capture and triage external sources.",
        "quick_gap": "Gap Analysis",
        "quick_gap_help": "Map a task to skills and gaps.",
        "quick_kanban": "Kanban",
        "quick_kanban_help": "Review Doing, Queue, and Done tasks.",
        "quick_public_site": "Public Site",
        "quick_public_site_help": "Review drafts and build public output.",
        "quick_profile_health": "Profile Health",
        "quick_profile_health_help": "Inspect validation, sync drift, and evidence risks.",
        "profile_evidence_import_expander": "Batch import profile evidence",
        "profile_evidence_import_caption": (
            "Paste a resume or long bio to draft evidence and skill-tree changes. "
            "Review every row before applying."
        ),
        "profile_context_expander": "Profile Context / SKILL.md",
        "profile_context_caption": (
            "Advanced area for long-term human-written profile context. "
            "Generated facts stay owned by their source files."
        ),
        "profile_context_structured_title": "Structured profile",
        "profile_context_narrative_title": "Long-term narrative sections",
        "profile_context_narrative_caption": (
            "These sections are human-authored and remain in SKILL.md."
        ),
        "identity_name": "Name",
        "identity_domain": "Domain",
        "identity_journey": "Journey",
        "identity_current_role": "Current Role",
        "identity_north_star": "North Star",
        "identity_north_star_brief": "North Star Brief",
        "identity_north_star_visibility": "North Star Visibility",
        "profile_section_research_fingerprint": "Research Fingerprint",
        "profile_section_thinking_style": "Thinking & Communication Style",
        "profile_section_growth_log": "Growth Log",
        "profile_section_influence_output": "Influence & Output",
        "save_profile_context": "Save Profile Context",
        "generated_block_preview_title": "Generated block preview",
        "generated_block_owner_hint": (
            "`skill_tree` is owned by skill-tree.yaml / evidence-pool.yaml; "
            "`current_focus` is owned by kanban.md. Preview only."
        ),
        "generated_block_expander": "{block}",
        "generated_block_skill_tree_help": "Owner: skill-tree.yaml and evidence-pool.yaml.",
        "generated_block_kanban_help": "Owner: kanban.md current focus.",
        "generated_block_sync_hint": "To refresh generated blocks, run `nblane sync <profile> --write`.",
        "generated_block_missing": "Generated block not found.",
        "raw_markdown_expander": "Raw Markdown",
        "raw_drift_warning": (
            "Raw edits can modify generated blocks and create sync drift. "
            "After saving, use Profile Health to check drift."
        ),
        "tab_overview": "📊 Overview",
        "tab_editor": "✏️ Structured Editor",
        "tab_raw": "📝 Raw",
        "sub_overview": "Skill overview",
        "sub_category": "Category breakdown",
        "goal_module_title": "Current Goal",
        "goal_module_caption": (
            "A 4-8 week anchor for gap analysis, evidence review, "
            "and output planning."
        ),
        "goal_create_title": "Create current goal",
        "goal_edit_title": "Edit current goal",
        "goal_reveal_private": "Reveal private goal in this session",
        "goal_private_locked": (
            "This goal is private. Reveal it in this session to edit details."
        ),
        "goal_field_title": "Title",
        "goal_field_label": "Discreet label",
        "goal_field_status": "Status",
        "goal_field_start": "Start date",
        "goal_field_target": "Target date",
        "goal_field_summary": "Summary",
        "goal_field_alignment": "North Star alignment",
        "goal_field_target_skills": "Target skills (one per line)",
        "goal_field_success_criteria": "Success criteria (one per line)",
        "goal_field_focus": "This week's focus (one per line)",
        "goal_field_evidence_refs": "Evidence refs (one per line)",
        "goal_field_task_refs": "Task refs (one per line)",
        "goal_field_output_refs": "Output refs (one per line)",
        "goal_field_notes": "Private notes",
        "goal_field_ui_visibility": "UI visibility",
        "goal_field_agent_context": "Include in Agent context",
        "goal_field_public_output": "Allow future public output reference",
        "goal_public_disabled_caption": (
            "P0 stores this flag but public site generation does not read goals.yaml."
        ),
        "goal_save": "Save current goal",
        "goal_saved": "Current goal saved.",
        "goal_title_required": "Title is required.",
        "goal_preview": "Preview",
        "home_expander_cat": "{cat} — {total} nodes",
        "info_no_skill_tree": (
            "skill-tree.yaml is not initialized yet. "
            "Edit `profiles/{profile}/skill-tree.yaml` "
            "to add nodes."
        ),
        "home_nav_compact": (
            "**Sidebar:** Skill Tree · Gap Analysis · Kanban · "
            "Team View. More: `docs/zh/project/status.md`, "
            "`docs/zh/product/web-experience.md`."
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
        "dashboard_status_overview": "状态概览",
        "dashboard_metric_goal": "当前目标",
        "dashboard_primary_goal": "主目标",
        "dashboard_active_goal": "活跃目标",
        "dashboard_active_goals_title": "活跃目标",
        "dashboard_goal_set": "已设置",
        "dashboard_goal_missing": "未设置",
        "dashboard_metric_skill_lit": "已点亮技能",
        "dashboard_skill_progress_suffix": "solid / expert",
        "dashboard_metric_doing": "Doing",
        "dashboard_metric_pending_evidence": "待整理证据",
        "dashboard_metric_health": "健康 E/W/I",
        "dashboard_metric_health_help": "来自 Profile Health 的错误 / 警告 / 信息数量。",
        "dashboard_public_not_initialized": (
            "Public layer 尚未初始化；Dashboard 这里只提供入口。"
        ),
        "dashboard_doing_title": "本周 Doing",
        "dashboard_doing_empty": "当前没有 Doing 任务。打开看板选择本周正在推进的工作。",
        "dashboard_doing_started": "开始于 {date}",
        "dashboard_doing_blocked": "阻塞：{blocked}",
        "dashboard_doing_more": "看板上还有 {n} 个 Doing 任务。",
        "dashboard_pending_evidence_title": "待整理 evidence",
        "dashboard_done_uncrystallized": "Done 未结晶",
        "dashboard_unlinked_evidence": "未挂技能的证据",
        "dashboard_needs_review_evidence": "待审阅 evidence",
        "dashboard_status_risk_evidence": "技能状态证据风险",
        "dashboard_pending_evidence_empty": "没有发现待整理证据。",
        "dashboard_health_title": "健康摘要",
        "dashboard_health_errors": "错误",
        "dashboard_health_warnings": "警告",
        "dashboard_health_info": "信息",
        "dashboard_health_context_ready": "上下文就绪",
        "dashboard_health_empty": "Profile Health 未发现问题。",
        "dashboard_yes": "是",
        "dashboard_no": "否",
        "dashboard_output_title": "输出机会",
        "dashboard_output_empty": "Public layer 暂无摘要。进入 Public Site 初始化草稿。",
        "dashboard_public_drafts": "草稿",
        "dashboard_public_published": "已发布",
        "dashboard_public_visibility": "可见性",
        "dashboard_public_build": "构建",
        "dashboard_public_build_exists": "已构建",
        "dashboard_public_build_missing": "未构建",
        "dashboard_public_build_detail": "`{path}` 下有 {pages} 个 HTML 页面。",
        "dashboard_quick_title": "快捷操作",
        "dashboard_overview_map_title": "当前地图",
        "dashboard_graph_eyebrow": "Context",
        "dashboard_graph_title": "上下文画布",
        "dashboard_graph_goal_missing": "设置当前目标",
        "dashboard_graph_blocked": "阻塞",
        "dashboard_evidence_inbox_title": "证据收件箱",
        "dashboard_open_section": "打开",
        "dashboard_goal_create_inline": "创建目标",
        "dashboard_goal_edit_inline": "编辑目标",
        "dashboard_goal_close_form": "收起",
        "dashboard_goal_advanced_fields": "高级目标字段",
        "dashboard_ai_ready": "AI 就绪",
        "dashboard_ai_not_ready": "AI 未启用",
        "north_star_strip_title": "North Star",
        "north_star_empty": "尚未设置 North Star",
        "north_star_empty_action": "填写 North Star",
        "north_star_hidden_display": "已设置长期方向",
        "north_star_private_display": "私密 North Star",
        "north_star_edit_action": "编辑 Profile Context",
        "north_star_visibility_visible": "完整显示",
        "north_star_visibility_discreet": "简略显示",
        "north_star_visibility_hidden": "隐藏明文",
        "north_star_visibility_private": "私密",
        "skill_alignment_title": "Goal-Skill 关联",
        "skill_alignment_confirmed": "已确认关联",
        "skill_alignment_candidates": "候选关联",
        "skill_alignment_no_links": "尚无已确认 skill links。",
        "skill_alignment_no_candidates": "运行规则匹配或 AI 匹配后选择候选。",
        "skill_alignment_rule": "规则匹配",
        "skill_alignment_ai": "AI 匹配",
        "skill_alignment_confirm": "确认关联",
        "skill_alignment_manual_label": "手动添加",
        "skill_alignment_manual_add": "添加",
        "skill_alignment_suggested": "建议",
        "skill_alignment_gap_hint": "关联到 locked/learning 节点时，建议进入差距分析。",
        "goal_alignment_goal_missing": "未找到要关联技能的 goal。",
        "goal_alignment_node_missing": "当前 schema 中没有这个技能节点。",
        "goal_alignment_candidates_ready": "已生成 {n} 个技能候选，请确认。",
        "goal_alignment_links_saved": "Goal-skill 关联已保存。",
        "goal_primary_saved": "Primary goal 已更新。",
        "goal_archived": "Goal 已归档。",
        "dashboard_add_active_goal": "+ Active Goal",
        "dashboard_archive_goal": "归档",
        "dashboard_inspector_empty": "选择一个节点查看详情。",
        "dashboard_inspector_node_hint": "进入 owner 页面查看完整内容。",
        "dashboard_inspector_placeholder_hint": "这个区域仍是骨架状态，还没有对应的真实记录。",
        "dashboard_inspector_locked_hint": "该节点的私密或锁定细节已在当前视图隐藏。",
        "dashboard_inspector_owner_reserved": "搭建状态",
        "dashboard_placeholder_metric": "预留",
        "dashboard_inspector_setup_title": "先完成基础设置，或选择真实节点",
        "dashboard_inspector_setup_hint": "当前图谱仍以骨架节点为主。建议先补 North Star，再设置当前目标。",
        "dashboard_today_current_focus": "当前焦点",
        "dashboard_today_capture_sources": "捕捉 / 来源",
        "dashboard_today_evidence_review": "证据审阅",
        "dashboard_today_gap_next_action": "缺口 / 下一步",
        "dashboard_today_output_feedback": "输出 / 反馈",
        "dashboard_capture_title": "捕捉来源",
        "dashboard_capture_submit": "捕捉",
        "dashboard_capture_saved": "已捕捉来源 {id}。",
        "dashboard_capture_title_required": "捕捉标题不能为空。",
        "dashboard_capture_title_placeholder": "你注意到了什么？",
        "dashboard_capture_raw_text": "备注",
        "dashboard_capture_source": "来源 URL 或出处",
        "dashboard_capture_tags": "标签",
        "dashboard_capture_goal": "Goal",
        "dashboard_capture_type": "类型",
        "dashboard_capture_type_note": "笔记",
        "dashboard_capture_type_link": "链接",
        "dashboard_capture_type_resource": "资源",
        "dashboard_capture_type_idea": "想法",
        "dashboard_source_inbox_title": "来源收件箱",
        "dashboard_source_inbox_empty": "还没有捕捉来源。",
        "dashboard_source_to_evidence_hint": "捕捉内容先进入 inbox，审阅后再成为 evidence candidate。",
        "dashboard_atomic_evidence_title": "原子证据",
        "dashboard_evidence_candidate_title": "证据候选",
        "dashboard_atomic_evidence_unlinked": "未挂技能的原子证据",
        "dashboard_atomic_evidence_needs_review": "待审阅",
        "dashboard_atomic_evidence_status_risk": "状态风险",
        "dashboard_gap_risk_title": "缺口风险",
        "dashboard_feedback_planned": "反馈区域仍在搭建中。",
        "dashboard_graph_loading": "正在加载图谱…",
        "dashboard_graph_3d_hint": (
            "North Star 依次流向目标、项目容器、活动、来源、证据、断言、能力、输出、反馈与治理。"
            "可旋转、缩放；点击节点后在右侧查看。"
        ),
        "dashboard_view_canvas": "2D 画布",
        "dashboard_view_3d_graph": "3D 图谱",
        "dashboard_workbench_title": "今日工作台",
        "dashboard_workbench_caption": "集中查看今天的信号、捕捉入口和快捷操作。",
        "dashboard_canvas_setup_title": "当前画布仍处于搭建阶段",
        "dashboard_canvas_setup_hint": "先补 North Star 和当前目标，再逐步用真实来源与证据替换骨架。",
        "dashboard_canvas_missing_north_star": "缺少 North Star",
        "dashboard_canvas_missing_goal": "缺少当前目标",
        "dashboard_canvas_missing_sources": "还没有捕捉来源",
        "dashboard_canvas_reset_filters": "显示全部层",
        "dashboard_canvas_no_layers": "已隐藏全部层。",
        "dashboard_skill_progress_title": "技能进度",
        "dashboard_skill_progress_caption": "solid / expert 点亮率",
        "dashboard_skill_progress_empty": "暂无 skill tree 数据。",
        "dashboard_skill_lit_rate": "点亮率",
        "dashboard_skill_status_expert": "专家",
        "dashboard_skill_status_solid": "扎实",
        "dashboard_skill_status_learning": "学习中",
        "dashboard_skill_status_locked": "锁定",
        "dashboard_node_north_star": "长期方向",
        "dashboard_node_goal": "目标",
        "dashboard_node_skill": "技能",
        "dashboard_node_task": "任务",
        "dashboard_node_project_case": "项目案例",
        "dashboard_private_project_case": "私密项目案例",
        "dashboard_node_daily_work": "日常工作",
        "dashboard_node_research": "研究",
        "dashboard_node_agent_run": "Agent 运行",
        "dashboard_node_source": "来源",
        "dashboard_node_evidence_candidate": "证据候选",
        "dashboard_node_atomic_evidence": "原子证据",
        "dashboard_node_composite_evidence": "组合证据",
        "dashboard_node_claim": "断言",
        "dashboard_node_evidence": "证据",
        "dashboard_node_gap": "缺口",
        "dashboard_node_next_action": "下一步行动",
        "dashboard_node_output": "输出",
        "dashboard_node_feedback": "反馈",
        "dashboard_node_capacity": "方向容量",
        "dashboard_node_health": "健康",
        "dashboard_layer_direction": "方向",
        "dashboard_layer_objective": "目标",
        "dashboard_layer_work_context": "工作语境",
        "dashboard_layer_activity": "活动",
        "dashboard_layer_source": "来源",
        "dashboard_layer_evidence": "证据",
        "dashboard_layer_claim": "断言",
        "dashboard_layer_capability": "能力",
        "dashboard_layer_output": "输出",
        "dashboard_layer_feedback": "反馈",
        "dashboard_layer_governance": "治理",
        "dashboard_set_as_primary": "设为主目标",
        "dashboard_set_primary": "设为主目标",
        "quick_skill_tree": "技能树",
        "quick_skill_tree_help": "编辑技能状态与 evidence refs。",
        "quick_evidence_review": "Evidence Review",
        "quick_evidence_review_help": "审阅 evidence 强度、技能关联与 Done 结晶。",
        "quick_research": "Research",
        "quick_research_help": "捕捉和整理外部来源。",
        "quick_gap": "差距分析",
        "quick_gap_help": "把任务映射到技能与缺口。",
        "quick_kanban": "看板",
        "quick_kanban_help": "查看 Doing、Queue 与 Done。",
        "quick_public_site": "Public Site",
        "quick_public_site_help": "查看公开草稿与构建状态。",
        "quick_profile_health": "Profile Health",
        "quick_profile_health_help": "查看校验、sync drift 与证据风险。",
        "profile_evidence_import_expander": "批量导入 profile evidence",
        "profile_evidence_import_caption": (
            "粘贴简历或长文本，让 AI 生成 evidence 与 skill-tree 变更草案；"
            "写入前请逐条审阅。"
        ),
        "profile_context_expander": "Profile Context / SKILL.md",
        "profile_context_caption": (
            "高级区：维护长期的人写画像与 Agent Context；"
            "生成事实继续由各 owner 文件负责。"
        ),
        "profile_context_structured_title": "结构化画像",
        "profile_context_narrative_title": "长期叙事章节",
        "profile_context_narrative_caption": (
            "这些章节由人维护，继续写入 SKILL.md。"
        ),
        "identity_name": "Name",
        "identity_domain": "Domain",
        "identity_journey": "Journey",
        "identity_current_role": "Current Role",
        "identity_north_star": "North Star",
        "identity_north_star_brief": "North Star Brief",
        "identity_north_star_visibility": "North Star Visibility",
        "profile_section_research_fingerprint": "Research Fingerprint",
        "profile_section_thinking_style": "Thinking & Communication Style",
        "profile_section_growth_log": "Growth Log",
        "profile_section_influence_output": "Influence & Output",
        "save_profile_context": "保存 Profile Context",
        "generated_block_preview_title": "生成块预览",
        "generated_block_owner_hint": (
            "`skill_tree` 由 skill-tree.yaml / evidence-pool.yaml 负责；"
            "`current_focus` 由 kanban.md 负责。此处只读预览。"
        ),
        "generated_block_expander": "{block}",
        "generated_block_skill_tree_help": "Owner：skill-tree.yaml 与 evidence-pool.yaml。",
        "generated_block_kanban_help": "Owner：kanban.md 的 current focus。",
        "generated_block_sync_hint": "如需刷新生成块，运行 `nblane sync <profile> --write`。",
        "generated_block_missing": "未找到该 generated block。",
        "raw_markdown_expander": "Raw Markdown",
        "raw_drift_warning": (
            "Raw 编辑可能改到 generated block 并造成 sync drift。"
            "保存后请用 Profile Health 检查 drift。"
        ),
        "tab_overview": "📊 概览",
        "tab_editor": "✏️ 结构化编辑",
        "tab_raw": "📝 原文",
        "sub_overview": "技能概览",
        "sub_category": "按分类",
        "goal_module_title": "Current Goal",
        "goal_module_caption": (
            "4-8 周阶段目标，用来统一差距分析、证据整理和输出规划。"
        ),
        "goal_create_title": "创建 current goal",
        "goal_edit_title": "编辑 current goal",
        "goal_reveal_private": "本会话显示 private goal",
        "goal_private_locked": (
            "该 goal 标记为 private。需在本会话显式显示后才能编辑明文细节。"
        ),
        "goal_field_title": "标题",
        "goal_field_label": "隐私替代标签",
        "goal_field_status": "状态",
        "goal_field_start": "开始日期",
        "goal_field_target": "目标日期",
        "goal_field_summary": "摘要",
        "goal_field_alignment": "与 North Star 的关系",
        "goal_field_target_skills": "目标技能（每行一项）",
        "goal_field_success_criteria": "成功标准（每行一项）",
        "goal_field_focus": "本周 focus（每行一项）",
        "goal_field_evidence_refs": "Evidence refs（每行一项）",
        "goal_field_task_refs": "Task refs（每行一项）",
        "goal_field_output_refs": "Output refs（每行一项）",
        "goal_field_notes": "私密备注",
        "goal_field_ui_visibility": "UI 展示级别",
        "goal_field_agent_context": "进入 Agent context",
        "goal_field_public_output": "允许未来公开输出引用",
        "goal_public_disabled_caption": (
            "P0 只保存该字段，公开站构建不会读取 goals.yaml。"
        ),
        "goal_save": "保存 current goal",
        "goal_saved": "Current goal 已保存。",
        "goal_title_required": "标题不能为空。",
        "goal_preview": "预览",
        "home_expander_cat": "{cat} — 共 {total} 个节点",
        "info_no_skill_tree": (
            "skill-tree.yaml 尚未初始化。"
            "请编辑 `profiles/{profile}/skill-tree.yaml` "
            "添加节点。"
        ),
        "home_nav_compact": (
            "**侧栏：** 技能树 · 差距分析 · 看板 · 团队视图。"
            "详见 `docs/zh/project/status.md`、`docs/zh/product/web-experience.md`。"
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
        "kb_unsaved_subtasks": (
            "Unsaved subtask changes — use Save to write them to kanban.md."
        ),
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
        "task_tags": "Tags",
        "kb_tags": "Tags",
        "kb_quick_kind": "Add to",
        "kb_quick_kind_task": "Task",
        "kb_quick_kind_inbox": "Inbox",
        "kb_quick_kind_learning": "Learning",
        "kb_quick_kind_habit": "Habit",
        "details": "details",
        "details_ph": (
            "context / outcome / why / blocked by..."
        ),
        "kb_personal_workspace_title": "Personal check-ins",
        "kb_personal_workspace_help": (
            "Keep this focused: record learning and exercise here, and leave "
            "workflow state on the board."
        ),
        "kb_tab_learning_checkin": "Learning check-in",
        "kb_tab_exercise_checkin": "Exercise check-in",
        "kb_tab_month_summary": "Monthly summary",
        "kb_checkin_date": "Date",
        "kb_checkin_saved": "Check-in saved.",
        "kb_checkin_deleted": "Check-in deleted.",
        "kb_checkin_delete_missing": "That check-in was already gone.",
        "kb_checkin_delete": "Delete",
        "kb_checkin_delete_help": "Remove this check-in from activity-log.yaml.",
        "kb_checkin_type_learning": "Learning",
        "kb_checkin_type_exercise": "Exercise",
        "kb_checkin_detail_empty": "No details",
        "kb_checkin_links_count": "{count} links",
        "kb_checkin_minutes": "{minutes:g} min",
        "kb_checkin_strip_title": "Recent 14 days",
        "kb_checkin_today_short": "Today",
        "kb_checkin_strip_learning_short": "L{count}",
        "kb_checkin_strip_exercise_short": "E{count}",
        "kb_checkin_day_help": "Open this day to add or delete check-ins.",
        "kb_checkin_day_records": "Day records",
        "kb_checkin_day_records_empty": (
            "No learning/exercise records on this day."
        ),
        "kb_checkin_add_learning": "Add learning",
        "kb_checkin_add_exercise": "Add exercise",
        "kb_checkin_no_marks": "No marks",
        "kb_summary_records": "Monthly records",
        "kb_summary_records_empty": "No learning/exercise records this month.",
        "kb_tab_today": "Today",
        "kb_tab_exercise": "Exercise",
        "kb_tab_learning": "Learning",
        "kb_tab_habits": "Habits",
        "kb_tab_context": "Context",
        "kb_tab_review": "Review",
        "kb_workspace_view": "Workspace view",
        "kb_personal_tags_hint": (
            "Use tags like company/openai, person/sam, project/nblane, "
            "or flow/learning."
        ),
        "kb_today_inbox": "Open inbox",
        "kb_today_learning": "Active learning",
        "kb_today_habits": "Habits today",
        "kb_today_total_habits": "Habit catalog",
        "kb_today_light_help": (
            "Use Today for capture and triage; use Activity and Learning for structured details."
        ),
        "kb_today_add_task": "Add Queue task",
        "kb_today_habit_strip_title": "Today habits",
        "kb_open_learning_detail": "Open Learning details",
        "kb_open_activity_detail": "Open Activity details",
        "kb_capture_title": "Title",
        "kb_capture_source": "Source",
        "kb_capture_note": "Note",
        "kb_capture_url": "URL",
        "kb_capture_inbox_title": "Capture to inbox",
        "kb_capture_inbox_submit": "Capture inbox",
        "kb_capture_learning_title": "Capture learning",
        "kb_capture_learning_submit": "Capture learning",
        "kb_capture_habit_title": "Check in a habit",
        "kb_capture_habit_submit": "Record check-in",
        "kb_tag_companies": "Companies",
        "kb_tag_people": "People",
        "kb_tag_projects": "Projects",
        "kb_tag_other": "Other tags",
        "kb_learning_kind": "Resource kind",
        "kb_learning_status": "Status",
        "kb_learning_takeaway": "Takeaway",
        "kb_learning_next": "Next action",
        "kb_learning_total": "Resources",
        "kb_learning_active": "Active",
        "kb_learning_unread": "unread",
        "kb_learning_completed": "Completed",
        "kb_learning_add_title": "Add learning resource",
        "kb_learning_add_short": "Add",
        "kb_learning_title": "Learning",
        "kb_learning_today_help": (
            "Capture papers, interviews, and videos as resources."
        ),
        "kb_learning_detail": "Details",
        "kb_learning_checkin_note": "Learning note",
        "kb_learning_checkin_note_placeholder": (
            "What did you study, and what is worth remembering?"
        ),
        "kb_learning_checkin_links": "Links",
        "kb_learning_checkin_links_placeholder": "One link per line.",
        "kb_learning_checkin_submit": "Record learning",
        "kb_learning_checkin_required": "Add a note or at least one link.",
        "kb_learning_summary": "Summary",
        "kb_learning_summary_placeholder": (
            "One or two lines about why this resource matters."
        ),
        "kb_learning_lines_placeholder": "One item per line.",
        "kb_learning_empty": "No matching resources yet.",
        "kb_learning_takeaways": "Takeaways",
        "kb_learning_next_actions": "Next actions",
        "kb_learning_queue_task": "Queue",
        "kb_learning_kind_paper": "Paper",
        "kb_learning_kind_interview": "Interview",
        "kb_learning_kind_video": "Video",
        "kb_learning_kind_book": "Book",
        "kb_learning_kind_article": "Article",
        "kb_learning_kind_course": "Course",
        "kb_learning_kind_other": "Other",
        "kb_learning_kind_blog": "Blog",
        "kb_learning_kind_repo": "Repo",
        "kb_learning_status_unread": "Unread",
        "kb_learning_status_reading": "Reading",
        "kb_learning_status_processed": "Processed",
        "kb_learning_status_archived": "Archived",
        "kb_open_link": "Open link",
        "kb_filter_all": "All",
        "kb_filter_status": "Status filter",
        "kb_filter_tag": "Tag filter",
        "kb_exercise_title": "Exercise",
        "kb_exercise_today": "Today",
        "kb_exercise_today_help": (
            "Keep the daily anchor light; add details in Exercise."
        ),
        "kb_exercise_quick_checkin": "Check in",
        "kb_exercise_done": "Done",
        "kb_exercise_detail": "Details",
        "kb_exercise_progress": "Progress",
        "kb_exercise_detail_checkin": "Detailed check-in",
        "kb_exercise_type": "Type",
        "kb_exercise_duration": "Duration (min)",
        "kb_exercise_duration_value": "{minutes:g} min",
        "kb_exercise_intensity": "Intensity",
        "kb_exercise_checkin_submit": "Record exercise",
        "kb_exercise_7d_checkins": "Check-ins (7d)",
        "kb_exercise_recent": "Recent workouts",
        "kb_exercise_empty": "No exercise check-ins yet.",
        "kb_exercise_type_running": "Cardio run",
        "kb_exercise_type_strength": "Strength",
        "kb_exercise_type_squat": "Weighted squat",
        "kb_exercise_type_rowing": "Rowing machine",
        "kb_exercise_type_mobility": "Mobility",
        "kb_exercise_type_other": "Other",
        "kb_exercise_intensity_easy": "Easy",
        "kb_exercise_intensity_moderate": "Moderate",
        "kb_exercise_intensity_hard": "Hard",
        "kb_summary_month": "Month",
        "kb_summary_learning_count": "Learning check-ins",
        "kb_summary_exercise_count": "Exercise check-ins",
        "kb_summary_learning_days": "Learning days",
        "kb_summary_exercise_days": "Exercise days",
        "kb_calendar_weekdays": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
        "kb_calendar_learning_short": "Learn {count}",
        "kb_calendar_exercise_short": "Exercise {count}",
        "kb_habit_empty_hint": (
            "Add a habit in the Habits view before checking it in here."
        ),
        "kb_habit_pick": "Habit",
        "kb_habit_count": "Count",
        "kb_habit_related_tasks": "Related tasks",
        "kb_habit_add_title": "Add a habit",
        "kb_habit_kind": "Kind",
        "kb_habit_cadence": "Cadence",
        "kb_habit_target_count": "Target count",
        "kb_habit_target_unit": "Target unit",
        "kb_habit_add_submit": "Save habit",
        "kb_habit_summary_total": "Check-ins (7d)",
        "kb_habit_summary_catalog": "Habit catalog",
        "kb_habit_summary_volume": "Recorded volume",
        "kb_habit_summary_window": "Last 7 days of habit progress.",
        "kb_habit_empty_summary": "No habits yet.",
        "kb_habit_summary_checkins": "check-ins",
        "kb_habit_summary_days": "days hit",
        "kb_habit_summary_streak": "streak",
        "kb_habit_done": "Done",
        "kb_strip_learning_help": "Open Learning details for this habit.",
        "kb_strip_more": "More",
        "kb_context_total_tags": "Tracked tags",
        "kb_context_company_tags": "Company tags",
        "kb_context_people_tags": "People tags",
        "kb_context_namespace": "Namespace",
        "kb_context_pick": "Tag",
        "kb_context_empty": "No matching tags yet.",
        "kb_context_flow_prefix": "Workflow facet",
        "kb_context_source_kanban": "Kanban",
        "kb_context_source_learning": "Learning",
        "kb_context_source_inbox": "Inbox",
        "kb_context_source_habit": "Habits",
        "kb_context_source_empty": "No matches",
        "kb_review_done": "Done tasks",
        "kb_review_crystallized": "Crystallized",
        "kb_review_activity": "Activity entries",
        "kb_review_learning": "Learning entries",
        "kb_review_done_detail": "Done this cycle",
        "kb_review_done_empty": "No done tasks yet.",
        "kb_review_learning_focus": "Learning focus",
        "kb_review_learning_empty": "No active learning focus.",
        "kb_review_activity_focus": "Activity pulse",
        "kb_review_activity_empty": "No activity summary yet.",
        "kb_review_checkins": "check-ins",
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
        "kb_drag_title": "Drag board",
        "kb_drag_help": (
            "Drag cards across columns or within a column, then apply. "
            "The detailed card editor below remains the source for fields."
        ),
        "kb_drag_applied": "Applied the drag-board order.",
        "kb_drag_stale": (
            "Drag order was stale or incomplete; reload and try again."
        ),
        "kb_done_render_limit": (
            "Showing {shown}/{total} Done cards here. Use housekeeping "
            "or Done -> evidence above for the full list."
        ),
        "kb_title_required": "Task title is required.",
        "kb_invalid_date": "Use YYYY-MM-DD for date fields: {fields}.",
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
        "kb_card_actions_help": "Delete or move this task to another column",
        "kb_edit_move": "⇄",
        "kb_edit_move_help": "Move this task to another column",
        "kb_card_delete_hint": "Removing a task cannot be undone here.",
        "kb_delete_card": "Delete task",
        "kb_delete_confirm": "Delete this task?",
        "kb_delete_short": "x",
        "kb_delete_subtask": "Delete subtask",
        "kb_edit_short": "Edit",
        "kb_save_short": "Save",
        "kb_cancel_short": "Cancel",
        "kb_ai_gap": "Analyze gap",
        "kb_ai_gap_short": "Gap",
        "kb_ai_subtasks": "Draft subtasks",
        "kb_ai_subtasks_short": "Sub",
        "kb_ai_done_short": "Evd",
        "kb_mark_crystallized": "Mark crystallized",
        "kb_crystallize_short": "Cry",
        "kb_crystallize_done_only": "Only Done tasks can be crystallized.",
        "kb_artifact": "Artifact",
        "kb_verification": "Verification",
        "kb_move_to_label": "Move to",
        "kb_confirm_move": "Move",
        "kb_read_new_subtask_ph": "New subtask…",
        "kb_read_add_subtask_expander": "Add subtask",
        "kb_alignment_title": "Confirm task understanding",
        "kb_alignment_custom": "Add detail or correction",
        "kb_alignment_confirm": "Use this understanding",
        "kb_alignment_custom_only": "Use only my supplement",
        "kb_alignment_assumptions": "Assumptions",
        "kb_alignment_style": "Subtask style",
        "kb_alignment_goal": "Goal",
        "kb_alignment_label": "Label",
        "kb_alignment_other": "Other",
        "kb_alignment_other_hint": "Use only my note below",
        "kb_alignment_status": "Understanding ready",
        "kb_alignment_required": (
            "Choose an understanding or add a clarification."
        ),
        "kb_no_alignment_options": (
            "No task understanding options were generated."
        ),
        "kb_discard_draft": "Discard draft",
        "kb_discard_all_drafts": "Discard all",
        "kb_no_selected_drafts": "Select at least one draft to apply.",
        "kb_draft_status": "{count} drafts",
        "kb_ai_error_status": "AI error",
        "kb_granularity": "Granularity",
        "kb_granularity_milestone": "Milestone",
        "kb_granularity_checklist": "Checklist",
        "kb_granularity_implementation": "Implementation",
        "kb_no_subtask_proposals": "No usable subtask draft was generated.",
        "kb_subtask_error_generic": "No usable subtask draft was generated.",
        "kb_subtask_error_task_not_found": "Kanban task was not found.",
        "kb_subtask_error_gap_error": "Gap analysis could not run for this task.",
        "kb_subtask_error_llm_error": "The model call failed or AI is not configured.",
        "kb_subtask_error_parse_empty": "The model did not return valid JSON subtasks.",
        "kb_subtask_error_empty_json": "The model returned no subtask items.",
        "kb_subtask_error_invalid_schema": "The model returned subtask items without usable titles.",
        "kb_subtask_error_filtered_vague": (
            "The model returned drafts, but every title was too vague. "
            "Add a concrete artifact or verification detail in Other and retry."
        ),
        "kb_subtask_error_filtered_duplicate": (
            "The model only returned subtasks that already exist."
        ),
        "kb_subtask_error_filtered_empty": (
            "The model returned drafts, but none passed validation."
        ),
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
        "kb_unsaved_subtasks": "有未保存的子任务修改，请点「保存」写入 kanban.md。",
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
        "task_tags": "标签",
        "kb_tags": "标签",
        "kb_quick_kind": "保存到",
        "kb_quick_kind_task": "任务",
        "kb_quick_kind_inbox": "收件",
        "kb_quick_kind_learning": "学习",
        "kb_quick_kind_habit": "习惯",
        "details": "详情",
        "details_ph": "背景 / 结果 / 阻塞…",
        "kb_personal_workspace_title": "个人工作台",
        "kb_personal_workspace_help": (
            "这里只记录学习和锻炼；其他流程状态继续放在看板里。"
        ),
        "kb_tab_learning_checkin": "学习打卡",
        "kb_tab_exercise_checkin": "锻炼打卡",
        "kb_tab_month_summary": "本月汇总",
        "kb_checkin_date": "日期",
        "kb_checkin_saved": "已记录。",
        "kb_checkin_deleted": "已删除记录。",
        "kb_checkin_delete_missing": "这条记录已经不存在。",
        "kb_checkin_delete": "删除",
        "kb_checkin_delete_help": "从 activity-log.yaml 删除这条打卡记录。",
        "kb_checkin_type_learning": "学习",
        "kb_checkin_type_exercise": "锻炼",
        "kb_checkin_detail_empty": "无详情",
        "kb_checkin_links_count": "{count} 个链接",
        "kb_checkin_minutes": "{minutes:g} 分钟",
        "kb_checkin_strip_title": "最近 14 天",
        "kb_checkin_today_short": "今",
        "kb_checkin_strip_learning_short": "学{count}",
        "kb_checkin_strip_exercise_short": "练{count}",
        "kb_checkin_day_help": "打开这一天，新增或删除打卡。",
        "kb_checkin_day_records": "当天记录",
        "kb_checkin_day_records_empty": "这一天还没有学习/锻炼记录。",
        "kb_checkin_add_learning": "新增学习",
        "kb_checkin_add_exercise": "新增锻炼",
        "kb_checkin_no_marks": "未打卡",
        "kb_summary_records": "本月记录",
        "kb_summary_records_empty": "本月还没有学习/锻炼记录。",
        "kb_tab_today": "今天",
        "kb_tab_exercise": "锻炼",
        "kb_tab_learning": "学习",
        "kb_tab_habits": "习惯",
        "kb_tab_context": "上下文",
        "kb_tab_review": "复盘",
        "kb_workspace_view": "工作区视图",
        "kb_personal_tags_hint": (
            "建议使用 company/openai、person/sam、project/nblane、flow/learning 这样的标签。"
        ),
        "kb_today_inbox": "开放收件",
        "kb_today_learning": "进行中的学习",
        "kb_today_habits": "今日打卡",
        "kb_today_total_habits": "习惯总数",
        "kb_today_light_help": (
            "今天页只做捕捉和分流；结构化习惯记录与学习心得请进入活动/学习详情。"
        ),
        "kb_today_add_task": "添加 Queue 任务",
        "kb_today_habit_strip_title": "今日习惯",
        "kb_open_learning_detail": "打开学习详情",
        "kb_open_activity_detail": "打开活动详情",
        "kb_capture_title": "标题",
        "kb_capture_source": "来源",
        "kb_capture_note": "备注",
        "kb_capture_url": "链接",
        "kb_capture_inbox_title": "快速收入 inbox",
        "kb_capture_inbox_submit": "收入 inbox",
        "kb_capture_learning_title": "快速记录学习",
        "kb_capture_learning_submit": "记录学习",
        "kb_capture_habit_title": "习惯打卡",
        "kb_capture_habit_submit": "记录打卡",
        "kb_tag_companies": "公司",
        "kb_tag_people": "人物",
        "kb_tag_projects": "项目",
        "kb_tag_other": "其他标签",
        "kb_learning_kind": "资源类型",
        "kb_learning_status": "状态",
        "kb_learning_takeaway": "心得",
        "kb_learning_next": "下一步动作",
        "kb_learning_total": "学习条目",
        "kb_learning_active": "进行中",
        "kb_learning_unread": "未读",
        "kb_learning_completed": "已完成",
        "kb_learning_add_title": "新增学习资源",
        "kb_learning_add_short": "新增",
        "kb_learning_title": "学习",
        "kb_learning_today_help": "把论文、采访、视频作为可回看的资源沉淀。",
        "kb_learning_detail": "详情",
        "kb_learning_checkin_note": "学习记录",
        "kb_learning_checkin_note_placeholder": "今天学了什么？哪些内容值得记住？",
        "kb_learning_checkin_links": "链接列表",
        "kb_learning_checkin_links_placeholder": "每行一个链接。",
        "kb_learning_checkin_submit": "记录学习",
        "kb_learning_checkin_required": "请填写学习记录或至少一个链接。",
        "kb_learning_summary": "摘要",
        "kb_learning_summary_placeholder": "用一两句话说明这个资源为什么重要。",
        "kb_learning_lines_placeholder": "每行一条。",
        "kb_learning_empty": "还没有匹配的学习条目。",
        "kb_learning_takeaways": "关键收获",
        "kb_learning_next_actions": "下一步动作",
        "kb_learning_queue_task": "入队",
        "kb_learning_kind_paper": "论文",
        "kb_learning_kind_interview": "采访",
        "kb_learning_kind_video": "视频",
        "kb_learning_kind_book": "书",
        "kb_learning_kind_article": "文章",
        "kb_learning_kind_course": "课程",
        "kb_learning_kind_other": "其他",
        "kb_learning_kind_blog": "博客",
        "kb_learning_kind_repo": "代码仓库",
        "kb_learning_status_unread": "未读",
        "kb_learning_status_reading": "进行中",
        "kb_learning_status_processed": "已处理",
        "kb_learning_status_archived": "已归档",
        "kb_open_link": "打开链接",
        "kb_filter_all": "全部",
        "kb_filter_status": "状态筛选",
        "kb_filter_tag": "标签筛选",
        "kb_exercise_title": "锻炼",
        "kb_exercise_today": "今天",
        "kb_exercise_today_help": "日常锚点保持轻量；更细记录进入锻炼页。",
        "kb_exercise_quick_checkin": "锻炼打卡",
        "kb_exercise_done": "已完成",
        "kb_exercise_detail": "详情",
        "kb_exercise_progress": "进度",
        "kb_exercise_detail_checkin": "详细打卡",
        "kb_exercise_type": "类型",
        "kb_exercise_duration": "时长（分钟）",
        "kb_exercise_duration_value": "{minutes:g} 分钟",
        "kb_exercise_intensity": "强度",
        "kb_exercise_checkin_submit": "记录锻炼",
        "kb_exercise_7d_checkins": "近 7 天打卡",
        "kb_exercise_recent": "最近锻炼",
        "kb_exercise_empty": "还没有锻炼打卡。",
        "kb_exercise_type_running": "有氧跑步",
        "kb_exercise_type_strength": "力量训练",
        "kb_exercise_type_squat": "负重深蹲",
        "kb_exercise_type_rowing": "划船机",
        "kb_exercise_type_mobility": "拉伸活动",
        "kb_exercise_type_other": "其他",
        "kb_exercise_intensity_easy": "轻松",
        "kb_exercise_intensity_moderate": "中等",
        "kb_exercise_intensity_hard": "较累",
        "kb_summary_month": "月份",
        "kb_summary_learning_count": "学习次数",
        "kb_summary_exercise_count": "锻炼次数",
        "kb_summary_learning_days": "学习天数",
        "kb_summary_exercise_days": "锻炼天数",
        "kb_calendar_weekdays": "一,二,三,四,五,六,日",
        "kb_calendar_learning_short": "学 {count}",
        "kb_calendar_exercise_short": "练 {count}",
        "kb_habit_empty_hint": "先在“习惯”视图里新增一个习惯，再回来打卡。",
        "kb_habit_pick": "习惯",
        "kb_habit_count": "数量",
        "kb_habit_related_tasks": "关联任务",
        "kb_habit_add_title": "新增习惯",
        "kb_habit_kind": "类别",
        "kb_habit_cadence": "频率",
        "kb_habit_target_count": "目标数量",
        "kb_habit_target_unit": "目标单位",
        "kb_habit_add_submit": "保存习惯",
        "kb_habit_summary_total": "近 7 天打卡",
        "kb_habit_summary_catalog": "习惯总数",
        "kb_habit_summary_volume": "记录总量",
        "kb_habit_summary_window": "最近 7 天的习惯进展。",
        "kb_habit_empty_summary": "还没有习惯。",
        "kb_habit_summary_checkins": "打卡次数",
        "kb_habit_summary_days": "命中天数",
        "kb_habit_summary_streak": "连续次数",
        "kb_habit_done": "已完成",
        "kb_strip_learning_help": "打开学习详情记录具体内容。",
        "kb_strip_more": "更多",
        "kb_context_total_tags": "追踪标签数",
        "kb_context_company_tags": "公司标签",
        "kb_context_people_tags": "人物标签",
        "kb_context_namespace": "命名空间",
        "kb_context_pick": "标签",
        "kb_context_empty": "还没有匹配的标签。",
        "kb_context_flow_prefix": "流程标签",
        "kb_context_source_kanban": "看板",
        "kb_context_source_learning": "学习",
        "kb_context_source_inbox": "Inbox",
        "kb_context_source_habit": "习惯",
        "kb_context_source_empty": "暂无匹配",
        "kb_review_done": "完成任务",
        "kb_review_crystallized": "已结晶",
        "kb_review_activity": "活动记录",
        "kb_review_learning": "学习记录",
        "kb_review_done_detail": "本轮完成",
        "kb_review_done_empty": "还没有完成任务。",
        "kb_review_learning_focus": "学习焦点",
        "kb_review_learning_empty": "当前没有进行中的学习焦点。",
        "kb_review_activity_focus": "活动脉搏",
        "kb_review_activity_empty": "还没有活动摘要。",
        "kb_review_checkins": "次打卡",
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
        "kb_drag_title": "拖拽看板",
        "kb_drag_help": (
            "可在列内或跨列拖动卡片，然后应用排序。"
            "下方详细卡片编辑器仍负责字段内容。"
        ),
        "kb_drag_applied": "已应用拖拽看板顺序。",
        "kb_drag_stale": "拖拽结果已过期或不完整，请重新加载后再试。",
        "kb_done_render_limit": (
            "此处仅显示 {shown}/{total} 个「已完成」卡片。"
            "完整列表请使用上方整理区或「已完成 → 证据」。"
        ),
        "kb_title_required": "任务标题不能为空。",
        "kb_invalid_date": "日期字段请使用 YYYY-MM-DD：{fields}。",
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
        "kb_card_actions_help": "删除或将任务移到其他列",
        "kb_edit_move": "⇄",
        "kb_edit_move_help": "将任务移到其他列",
        "kb_card_delete_hint": "删除后无法在此恢复。",
        "kb_delete_card": "删除任务",
        "kb_delete_confirm": "确定删除这个任务吗？",
        "kb_delete_short": "删",
        "kb_delete_subtask": "删除子任务",
        "kb_edit_short": "改",
        "kb_save_short": "存",
        "kb_cancel_short": "取",
        "kb_ai_gap": "分析缺口",
        "kb_ai_gap_short": "Gap",
        "kb_ai_subtasks": "拆任务",
        "kb_ai_subtasks_short": "拆",
        "kb_ai_done_short": "证",
        "kb_mark_crystallized": "标记已结晶",
        "kb_crystallize_short": "晶",
        "kb_crystallize_done_only": "只有「已完成」任务可以标记为已结晶。",
        "kb_artifact": "产物",
        "kb_verification": "验证",
        "kb_move_to_label": "移动到",
        "kb_confirm_move": "移动",
        "kb_read_new_subtask_ph": "新子任务…",
        "kb_read_add_subtask_expander": "添加子任务",
        "kb_alignment_title": "确认任务理解",
        "kb_alignment_custom": "补充细节或修正理解",
        "kb_alignment_confirm": "按这个理解拆解",
        "kb_alignment_custom_only": "只用我的补充",
        "kb_alignment_assumptions": "假设",
        "kb_alignment_style": "拆分风格",
        "kb_alignment_goal": "目标理解",
        "kb_alignment_label": "短标签",
        "kb_alignment_other": "其他理解",
        "kb_alignment_other_hint": "只使用下方我填写的理解",
        "kb_alignment_status": "理解待确认",
        "kb_alignment_required": "请选择一个理解，或补充你的说明。",
        "kb_no_alignment_options": "未生成可选的任务理解。",
        "kb_discard_draft": "废弃草案",
        "kb_discard_all_drafts": "废弃全部",
        "kb_no_selected_drafts": "请至少选择一个要应用的草案。",
        "kb_draft_status": "{count} 条草案",
        "kb_ai_error_status": "AI 出错",
        "kb_granularity": "粒度",
        "kb_granularity_milestone": "里程碑",
        "kb_granularity_checklist": "清单",
        "kb_granularity_implementation": "实现细节",
        "kb_no_subtask_proposals": "没有生成可用的子任务草案。",
        "kb_subtask_error_generic": "没有生成可用的子任务草案。",
        "kb_subtask_error_task_not_found": "没有找到这个看板任务。",
        "kb_subtask_error_gap_error": "这个任务的能力缺口分析没有跑通。",
        "kb_subtask_error_llm_error": "模型调用失败，或 AI 尚未配置。",
        "kb_subtask_error_parse_empty": "模型没有返回可解析的 JSON 子任务。",
        "kb_subtask_error_empty_json": "模型返回了 JSON，但没有子任务条目。",
        "kb_subtask_error_invalid_schema": "模型返回的子任务缺少可用标题。",
        "kb_subtask_error_filtered_vague": (
            "模型返回了草案，但标题都过泛。请在「其他理解」里补充具体产物"
            "或验证方式后重试。"
        ),
        "kb_subtask_error_filtered_duplicate": "模型只返回了已存在的子任务。",
        "kb_subtask_error_filtered_empty": "模型返回了草案，但没有条目通过校验。",
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

_PROFILE_HEALTH: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Profile Health",
        "title": "Profile Health",
        "errors": "Errors",
        "warnings": "Warnings",
        "info": "Info",
        "context_ready": "Context ready",
        "yes": "Yes",
        "no": "No",
        "no_issues": "No health issues found.",
        "severity_error": "ERROR",
        "severity_warning": "WARN",
        "severity_info": "INFO",
    },
    "zh": {
        "page_title": "档案健康检查",
        "title": "档案健康检查",
        "errors": "错误",
        "warnings": "警告",
        "info": "信息",
        "context_ready": "上下文可发布",
        "yes": "是",
        "no": "否",
        "no_issues": "未发现健康问题。",
        "severity_error": "错误",
        "severity_warning": "警告",
        "severity_info": "信息",
    },
}

_RESEARCH: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Research · nblane",
        "title": "Research Source Inbox",
        "page_context_line": (
            "Capture external sources first; review them into evidence later."
        ),
        "add_source": "Add source",
        "edit_source": "Edit source",
        "source_queue": "Source queue",
        "candidate_preview": "Evidence candidate preview",
        "candidate_preview_help": "Read-only draft; this page does not write evidence.",
        "source_id": "Source id",
        "kind": "Kind",
        "title_label": "Title",
        "url": "URL",
        "status": "Status",
        "captured_at": "Captured at",
        "authors": "Authors",
        "published": "Published",
        "tags": "Tags",
        "goal_refs": "Goal refs",
        "project_refs": "Project refs",
        "experience_refs": "Experience refs",
        "summary": "Summary",
        "notes": "Notes",
        "visibility": "Visibility",
        "save": "Save",
        "create": "Create",
        "saved": "Saved source.",
        "created": "Created source {id}.",
        "title_required": "Source title is required.",
        "empty_status": "No sources in this status.",
        "copy_id": "Source id",
        "discard": "Discard",
        "archive": "Archive",
        "status_inbox": "Inbox",
        "status_reading": "Reading",
        "status_summarized": "Summarized",
        "status_candidate_ready": "Candidate ready",
        "status_archived": "Archived",
        "status_discarded": "Discarded",
    },
    "zh": {
        "page_title": "Research · nblane",
        "title": "Research Source Inbox",
        "page_context_line": "外部资料先进入来源收件箱；审阅后再进入 evidence。",
        "add_source": "新增来源",
        "edit_source": "编辑来源",
        "source_queue": "来源队列",
        "candidate_preview": "Evidence candidate 预览",
        "candidate_preview_help": "只读草稿；本页不会写入 evidence。",
        "source_id": "Source id",
        "kind": "类型",
        "title_label": "标题",
        "url": "URL",
        "status": "状态",
        "captured_at": "捕捉时间",
        "authors": "作者",
        "published": "发布时间",
        "tags": "标签",
        "goal_refs": "Goal refs",
        "project_refs": "Project refs",
        "experience_refs": "Experience refs",
        "summary": "摘要",
        "notes": "备注",
        "visibility": "可见性",
        "save": "保存",
        "create": "创建",
        "saved": "已保存来源。",
        "created": "已创建来源 {id}。",
        "title_required": "来源标题不能为空。",
        "empty_status": "此状态下暂无来源。",
        "copy_id": "Source id",
        "discard": "丢弃",
        "archive": "归档",
        "status_inbox": "Inbox",
        "status_reading": "Reading",
        "status_summarized": "Summarized",
        "status_candidate_ready": "Candidate ready",
        "status_archived": "Archived",
        "status_discarded": "Discarded",
    },
}


def _lang() -> str:
    """Return ``en`` or ``zh``."""
    return llm_client.ui_language()


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


def evidence_review_ui() -> dict[str, str]:
    """Evidence Review page."""
    lg = _lang()
    merged = dict(_COMMON.get(lg, _COMMON["en"]))
    merged.update(_EVIDENCE_REVIEW.get(lg, _EVIDENCE_REVIEW["en"]))
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


def profile_health_ui() -> dict[str, str]:
    """Profile Health page."""
    lg = _lang()
    merged = dict(_COMMON.get(lg, _COMMON["en"]))
    merged.update(_PROFILE_HEALTH.get(lg, _PROFILE_HEALTH["en"]))
    return merged


def research_ui() -> dict[str, str]:
    """Research Source Inbox page."""
    lg = _lang()
    merged = dict(_COMMON.get(lg, _COMMON["en"]))
    merged.update(_RESEARCH.get(lg, _RESEARCH["en"]))
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
