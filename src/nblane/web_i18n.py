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
        "page_help_short": "Guide",
        "page_help_docs_link": "[Open full guide]({path})",
        "page_help_docs_open_inline": "Open full guide",
        "page_help_docs_missing": "Full guide not found: {path}",
        "ai_config_overview_title": "AI config map",
        "ai_config_overview_caption": (
            "This view separates deployment-wide runtime, page-level action preferences, "
            "Codex scope, and candidate-first write gates."
        ),
        "ai_scope_global_llm": "Global LLM",
        "ai_scope_page_actions": "Page actions",
        "ai_scope_codex": "Codex",
        "ai_scope_review_gate": "Review gate",
        "ai_scope_ready": "ready",
        "ai_scope_missing": "missing",
        "ai_scope_overrides_count": "{count} override(s)",
        "ai_scope_candidate_first": "candidate-first writes",
        "ai_config_overview_llm_title": "Global LLM runtime",
        "ai_config_overview_llm_line": "Base URL: {provider} · Model: {model}",
        "ai_config_overview_llm_scope": (
            "API keys are session/env scoped. Page actions only persist non-secret model/backend preferences."
        ),
        "ai_config_overview_codex_title": "Codex runtime",
        "ai_config_overview_actions_title": "Page action preferences",
        "ai_config_overview_col_page": "Page",
        "ai_config_overview_col_action": "Action",
        "ai_config_overview_col_backend": "Backend",
        "ai_config_overview_col_model": "Model",
        "ai_config_overview_col_source": "Source",
        "ai_config_overview_default_model": "app default",
        "ai_config_overview_profile_override": "profile override",
        "ai_config_overview_app_default": "app default",
        "ai_page_dashboard": "Dashboard",
        "ai_page_evidence": "Evidence Review",
        "ai_page_research": "Research",
        "ai_page_kanban": "Kanban",
        "ai_page_project": "Project Board",
        "codex_settings_title": "Codex",
        "codex_bin": "Codex binary",
        "codex_cloud_env_id": "Codex Cloud env id",
        "codex_model": "Codex model override",
        "codex_attempts": "Cloud attempts",
        "codex_branch": "Cloud branch",
        "codex_timeout": "Timeout seconds",
        "codex_profile_config": "Profile Codex config for {profile}: `{path}`",
        "codex_installed": "Codex installed: {version}",
        "codex_missing": "Codex CLI is not installed or not on PATH.",
        "codex_logged_in": "Codex login: ready.",
        "codex_not_logged_in": "Codex login is not ready.",
        "codex_cloud_configured": "Codex Cloud env configured.",
        "codex_cloud_missing": "Set a Codex Cloud env id to submit tasks from Web.",
        "codex_install": "Install",
        "codex_upgrade": "Upgrade",
        "codex_save_env": "Save Codex settings to .env",
        "codex_save_profile": "Save for this profile",
        "codex_saved_env": "Codex settings saved to .env.",
        "codex_saved_profile": "Profile Codex settings saved.",
        "codex_install_done": "Codex install command completed.",
        "codex_install_failed": "Codex install command failed.",
        "codex_session_only": (
            "Auth stays in Codex CLI; nblane only stores non-secret NBLANE_CODEX_* settings."
        ),
        "codex_scope_hint": (
            "Auth and CLI config are shared for this deployment; profile config only stores non-secret preferences."
        ),
        "kb_ai_backend": "Kanban AI Engine",
        "kb_ai_backend_help": (
            "Choose the engine used by Kanban AI actions. Codex uses the "
            "local Codex CLI in read-only mode."
        ),
        "kb_ai_backend_llm": "LLM",
        "kb_ai_backend_codex": "Codex",
        "kb_ai_backend_codex_status": "Codex: read-only local",
        "codex_configure": "Configure Codex",
        "codex_config_dialog_title": "Codex Configuration",
        "codex_status_tab": "Status",
        "codex_api_key_tab": "Shared API Key",
        "codex_cli_config_tab": "Shared CLI Config",
        "codex_profile_config_tab": "Profile Preferences",
        "codex_dialog_close": "Close",
        "codex_current_profile": "Current profile: `{profile}`",
        "codex_web_home": "Codex home: `{path}`",
        "codex_cli_config_path": "CLI config: `{path}`",
        "codex_auth_path": "Auth file: `{path}`",
        "codex_auth_managed": (
            "Codex auth for this deployment is managed by Codex CLI at `{path}`. "
            "nblane does not display raw auth.json."
        ),
        "codex_profile_isolated_note": (
            "Saving here logs in the shared service-level Codex home used by all "
            "Codex actions in this deployment."
        ),
        "codex_cli_profile_scope_note": (
            "This config.toml belongs to the shared service-level Codex home. "
            "Per-profile preferences live in codex.yaml."
        ),
        "codex_terminal_hint": (
            "Web Codex uses this service-level CODEX_HOME. Profile config below "
            "only stores non-secret preferences such as model, cloud env, and timeout."
        ),
        "codex_api_key": "Codex API key",
        "codex_api_key_help": (
            "Saved through `codex login --with-api-key` with the service-level "
            "CODEX_HOME; the key is sent through stdin and not stored by nblane."
        ),
        "codex_save_api_key": "Save API Key",
        "codex_api_key_saved": "Codex API key saved.",
        "codex_api_key_failed": "Codex API key was not saved: {error}",
        "codex_cli_config_editor": "Edit config.toml",
        "codex_save_cli_config": "Save config.toml",
        "codex_cli_config_saved": (
            "Saved config.toml. Previous file backup: {backup}"
        ),
        "codex_cli_config_invalid": "config.toml was not saved: {error}",
        "codex_cli_config_template_note": (
            "config.toml does not exist yet. The editor is showing a template."
        ),
        "codex_config_path": "Codex profile config: `{path}`",
        "codex_config_editor": "Edit codex.yaml",
        "codex_config_reload": "Reload from disk",
        "codex_config_save": "Save Codex config",
        "codex_config_reloaded": "Codex config reloaded from disk.",
        "codex_config_saved": "Codex config saved.",
        "codex_config_invalid": "Codex config was not saved: {error}",
        "codex_config_template_note": (
            "codex.yaml does not exist yet. The editor is showing a template."
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
        "sidebar_nav_project_board": "Project Board",
        "sidebar_nav_evidence_review": "Evidence Review",
        "sidebar_nav_research": "Research",
        "sidebar_nav_skill_map": "Skill Map",
        "sidebar_nav_gap": "Gap Analysis",
        "sidebar_nav_review": "Review",
        "sidebar_nav_health": "Profile Health",
        "sidebar_nav_agent_activity": "Agent Activity",
        "sidebar_nav_public": "Output Studio",
        "sidebar_nav_public_build": "Public Build",
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
        "page_help_short": "使用说明",
        "page_help_docs_link": "[打开完整说明]({path})",
        "page_help_docs_open_inline": "打开完整说明",
        "page_help_docs_missing": "未找到完整说明：{path}",
        "ai_config_overview_title": "AI 配置地图",
        "ai_config_overview_caption": (
            "这里把部署级运行时、页面级动作偏好、Codex 生效范围和候选优先写入门槛分开显示。"
        ),
        "ai_scope_global_llm": "全局 LLM",
        "ai_scope_page_actions": "页面动作",
        "ai_scope_codex": "Codex",
        "ai_scope_review_gate": "人工确认",
        "ai_scope_ready": "可用",
        "ai_scope_missing": "未就绪",
        "ai_scope_overrides_count": "{count} 个覆盖",
        "ai_scope_candidate_first": "候选优先写入",
        "ai_config_overview_llm_title": "全局 LLM 运行时",
        "ai_config_overview_llm_line": "Base URL：{provider} · 模型：{model}",
        "ai_config_overview_llm_scope": (
            "API key 只来自当前会话或环境变量；页面动作只保存非密钥的模型/后端偏好。"
        ),
        "ai_config_overview_codex_title": "Codex 运行时",
        "ai_config_overview_actions_title": "页面动作偏好",
        "ai_config_overview_col_page": "页面",
        "ai_config_overview_col_action": "动作",
        "ai_config_overview_col_backend": "后端",
        "ai_config_overview_col_model": "模型",
        "ai_config_overview_col_source": "来源",
        "ai_config_overview_default_model": "应用默认",
        "ai_config_overview_profile_override": "当前档案覆盖",
        "ai_config_overview_app_default": "应用默认",
        "ai_page_dashboard": "每日仪表盘",
        "ai_page_evidence": "证据审阅",
        "ai_page_research": "研究",
        "ai_page_kanban": "看板",
        "ai_page_project": "项目看板",
        "codex_settings_title": "Codex",
        "codex_bin": "Codex binary",
        "codex_cloud_env_id": "Codex Cloud env id",
        "codex_model": "Codex 模型覆盖",
        "codex_attempts": "Cloud attempts",
        "codex_branch": "Cloud 分支",
        "codex_timeout": "超时时间（秒）",
        "codex_profile_config": "{profile} 的 Codex 配置文件：`{path}`",
        "codex_installed": "已安装 Codex：{version}",
        "codex_missing": "未安装 Codex CLI，或不在 PATH 中。",
        "codex_logged_in": "Codex 登录：可用。",
        "codex_not_logged_in": "Codex 尚未登录或登录状态不可用。",
        "codex_cloud_configured": "已配置 Codex Cloud env。",
        "codex_cloud_missing": "填写 Codex Cloud env id 后，Web 才能提交任务。",
        "codex_install": "安装",
        "codex_upgrade": "升级",
        "codex_save_env": "保存 Codex 设置到 .env",
        "codex_save_profile": "保存到当前档案",
        "codex_saved_env": "Codex 设置已保存到 .env。",
        "codex_saved_profile": "当前档案的 Codex 设置已保存。",
        "codex_install_done": "Codex 安装命令已完成。",
        "codex_install_failed": "Codex 安装命令失败。",
        "codex_session_only": (
            "认证仍由 Codex CLI 管理；nblane 只保存非密钥的 NBLANE_CODEX_* 设置。"
        ),
        "codex_scope_hint": (
            "认证与 CLI 配置属于当前部署共享范围；当前档案只保存非密钥偏好。"
        ),
        "kb_ai_backend": "看板 AI 引擎",
        "kb_ai_backend_help": (
            "选择看板 AI 动作使用的引擎。Codex 使用本地 Codex CLI 的只读模式。"
        ),
        "kb_ai_backend_llm": "LLM",
        "kb_ai_backend_codex": "Codex",
        "kb_ai_backend_codex_status": "Codex：本地只读",
        "codex_configure": "配置 Codex",
        "codex_config_dialog_title": "Codex 配置",
        "codex_status_tab": "状态",
        "codex_api_key_tab": "全局 API Key",
        "codex_cli_config_tab": "全局 CLI 配置",
        "codex_profile_config_tab": "当前档案偏好",
        "codex_dialog_close": "关闭",
        "codex_current_profile": "当前档案：`{profile}`",
        "codex_web_home": "Codex home：`{path}`",
        "codex_cli_config_path": "CLI 配置：`{path}`",
        "codex_auth_path": "认证文件：`{path}`",
        "codex_auth_managed": (
            "当前部署的 Codex 认证由 Codex CLI 管理，文件位于 `{path}`。"
            "nblane 不展示 auth.json 原文。"
        ),
        "codex_profile_isolated_note": (
            "这里保存后会登录当前部署共享的 service-level Codex home，所有 "
            "Codex 动作都会使用它。"
        ),
        "codex_cli_profile_scope_note": (
            "这个 config.toml 属于当前部署共享的 service-level Codex home；"
            "每个档案的非密钥偏好放在 codex.yaml。"
        ),
        "codex_terminal_hint": (
            "Web Codex 使用这个 service-level CODEX_HOME。下面的档案配置"
            "只保存 model、cloud env、timeout 等非密钥偏好。"
        ),
        "codex_api_key": "Codex API key",
        "codex_api_key_help": (
            "通过 service-level CODEX_HOME 调用 `codex login --with-api-key` 保存；"
            "key 通过 stdin 传入，不会由 nblane 存储。"
        ),
        "codex_save_api_key": "保存 API Key",
        "codex_api_key_saved": "Codex API key 已保存。",
        "codex_api_key_failed": "Codex API key 未保存：{error}",
        "codex_cli_config_editor": "编辑 config.toml",
        "codex_save_cli_config": "保存 config.toml",
        "codex_cli_config_saved": (
            "config.toml 已保存。上一个文件备份：{backup}"
        ),
        "codex_cli_config_invalid": "config.toml 未保存：{error}",
        "codex_cli_config_template_note": (
            "config.toml 还不存在，编辑器当前显示的是新建模板。"
        ),
        "codex_config_path": "Codex profile 配置：`{path}`",
        "codex_config_editor": "编辑 codex.yaml",
        "codex_config_reload": "从磁盘重载",
        "codex_config_save": "保存 Codex 配置",
        "codex_config_reloaded": "已从磁盘重载 Codex 配置。",
        "codex_config_saved": "Codex 配置已保存。",
        "codex_config_invalid": "Codex 配置未保存：{error}",
        "codex_config_template_note": (
            "codex.yaml 还不存在，编辑器当前显示的是新建模板。"
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
        "sidebar_nav_home_group": "首页",
        "sidebar_nav_work_group": "工作",
        "sidebar_nav_growth_group": "成长",
        "sidebar_nav_output_group": "输出",
        "sidebar_nav_team_group": "团队",
        "sidebar_nav_dashboard": "每日仪表盘",
        "sidebar_nav_kanban": "看板",
        "sidebar_nav_project_board": "项目看板",
        "sidebar_nav_evidence_review": "证据审阅",
        "sidebar_nav_research": "研究工作台",
        "sidebar_nav_skill_map": "技能地图",
        "sidebar_nav_gap": "差距分析",
        "sidebar_nav_review": "复盘",
        "sidebar_nav_health": "档案体检",
        "sidebar_nav_agent_activity": "Agent 活动",
        "sidebar_nav_public": "输出工作台",
        "sidebar_nav_public_build": "公开构建",
        "sidebar_nav_team": "团队视图",
    },
}

_PROJECT_BOARD: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Project Board · nblane",
        "title": "Project Board",
        "page_context_line": (
            "Internal project cases connect goals, tasks, sources, evidence, "
            "milestones, and outputs. Public projects still live in projects.yaml."
        ),
        "page_help_short": "Guide",
        "page_help_body": (
            "### Project Board workflow\n\n"
            "1. Create internal project cases for work that connects goals, Kanban tasks, evidence, research sources, milestones, and outputs.\n"
            "2. Keep project status private by default; public project pages still come from the public output layer.\n"
            "3. Link tasks and evidence so Dashboard and Evidence Review can show ownership gaps.\n"
            "4. Add milestones when a project has visible checkpoints. Milestones can own Kanban tasks without changing the task text.\n"
            "5. Use the create-task action only for execution work you intend to track on Kanban.\n\n"
            "This page writes project-board.yaml and may sync task ownership back to kanban.md."
        ),
        "create_project": "Create project",
        "create_task": "Create Kanban task",
        "project_detail": "Project detail",
        "milestones": "Milestones",
        "add_milestone": "Add milestone",
        "save_project": "Save project",
        "save_milestone": "Save milestone",
        "archive_project": "Archive project",
        "edit": "Edit",
        "saved": "Saved project board.",
        "task_created": "Created Kanban task.",
        "empty_board": "No internal projects yet.",
        "empty_status": "No projects in this status.",
        "select_project": "Project",
        "field_id": "ID",
        "field_title": "Title",
        "field_status": "Status",
        "field_kind": "Kind",
        "field_visibility": "Visibility",
        "field_time_range": "Time range",
        "field_summary": "Summary",
        "field_notes": "Notes",
        "field_goal_refs": "Goals",
        "field_task_refs": "Kanban tasks",
        "field_evidence_refs": "Evidence",
        "field_source_refs": "Research sources",
        "field_experience_refs": "Experience cases",
        "field_output_refs": "Outputs",
        "field_goal_refs_help": (
            "Goals explain why the project exists and let Dashboard/Gap Analysis group work by objective."
        ),
        "field_task_refs_help": (
            "Kanban tasks are execution ownership. Tasks linked from Kanban are synced back automatically."
        ),
        "field_evidence_refs_help": (
            "Evidence rows are reviewed facts this project owns or produced. AI can suggest candidates, but saved links stay human-confirmed."
        ),
        "field_source_refs_help": (
            "Research sources are papers, URLs, and imported material that belong to this project."
        ),
        "field_experience_refs_help": "Experience cases that support this project story.",
        "field_output_refs_help": "Outputs or public drafts connected to this project.",
        "project_refs_hint": (
            "Links here are project ownership refs, not copied content. Model-suggested links should still be reviewed before saving."
        ),
        "project_ai_suggest_refs": "AI suggest refs",
        "project_ai_suggest_help": (
            "Ask the model to suggest goal, task, evidence, source, and output refs. Suggestions prefill the form but are not saved until you click Save project."
        ),
        "project_ai_suggest_running": "Suggesting project refs...",
        "project_ai_suggest_applied": "Added {count} suggested ref(s) to the form. Review them before saving.",
        "project_ai_suggest_none": "No new project refs were suggested.",
        "project_ai_suggest_failed": "Project ref suggestion failed.",
        "project_ai_suggest_summary": "{count} suggested ref(s) are staged in the form.",
        "project_missing_reload": "Project `{id}` changed or was removed. The latest board was loaded; refresh before editing it again.",
        "milestone_missing_reload": "Milestone `{id}` changed or was removed. Refresh before editing it again.",
        "field_target": "Target",
        "field_milestone": "Milestone",
        "task_title": "Task title",
        "task_section": "Column",
        "no_milestone": "No milestone",
        "id_help": "Leave blank to auto-generate project:<slug>.",
        "milestone_id_help": "Leave blank to auto-generate milestone:<slug>.",
        "title_required": "Title is required.",
        "duplicate_milestone": "Milestone id already exists: {id}",
        "missing_ref": "missing",
        "claimed_elsewhere_hint": (
            "{count} task(s) already belong to another project and are hidden "
            "from this selector."
        ),
        "card_counts": (
            "Goals {goals} · Tasks {tasks} · Evidence {evidence} · "
            "Sources {sources} · Milestones {milestones}"
        ),
        "metric_unassigned_tasks": "Unassigned tasks",
        "metric_unassigned_evidence": "Unassigned evidence",
        "metric_current_goal_projects": "Current-goal projects",
        "unassigned_evidence_hint": (
            "{count} reviewed evidence row(s) are not linked to any project."
        ),
        "status_active": "Active",
        "status_paused": "Paused",
        "status_completed": "Completed",
        "status_archived": "Archived",
        "status_planned": "Planned",
    },
    "zh": {
        "page_title": "项目看板 · nblane",
        "title": "项目看板",
        "page_context_line": (
            "内部项目案例连接目标、任务、资料、证据、里程碑和输出；公开项目仍由 "
            "projects.yaml 管理。"
        ),
        "page_help_short": "使用说明",
        "page_help_body": (
            "### 项目看板使用流程\n\n"
            "1. 为需要跨目标、看板任务、证据、研究资料、里程碑和输出追踪的工作创建内部项目案例。\n"
            "2. 内部项目默认服务于个人工作流；公开项目页仍由公开输出层管理。\n"
            "3. 关联任务和证据后，首页与证据审阅才能识别项目归属缺口。\n"
            "4. 项目有阶段节点时添加里程碑；里程碑可以承接看板任务，不必改写任务正文。\n"
            "5. 只有准备进入执行流的事项才用「新建看板任务」。\n\n"
            "本页会写入 project-board.yaml，并可能把任务归属同步回 kanban.md。"
        ),
        "create_project": "新建项目",
        "create_task": "新建看板任务",
        "project_detail": "项目详情",
        "milestones": "里程碑",
        "add_milestone": "新增里程碑",
        "save_project": "保存项目",
        "save_milestone": "保存里程碑",
        "archive_project": "归档项目",
        "edit": "编辑",
        "saved": "已保存项目看板。",
        "task_created": "已创建看板任务。",
        "empty_board": "还没有内部项目。",
        "empty_status": "这个状态下没有项目。",
        "select_project": "项目",
        "field_id": "ID",
        "field_title": "标题",
        "field_status": "状态",
        "field_kind": "类型",
        "field_visibility": "可见性",
        "field_time_range": "时间范围",
        "field_summary": "摘要",
        "field_notes": "备注",
        "field_goal_refs": "目标",
        "field_task_refs": "看板任务",
        "field_evidence_refs": "证据",
        "field_source_refs": "研究资料",
        "field_experience_refs": "经历案例",
        "field_output_refs": "输出",
        "field_goal_refs_help": (
            "目标说明这个项目服务于哪条阶段目标，用于首页和差距分析按目标归因。"
        ),
        "field_task_refs_help": (
            "看板任务表示执行归属；从看板任务上选择项目后会自动同步回这里。"
        ),
        "field_evidence_refs_help": (
            "证据是这个项目承担或产出的已审阅事实。模型可以建议候选，但保存的关联仍是人工确认后的归属。"
        ),
        "field_source_refs_help": (
            "研究资料是属于这个项目的论文、URL 或导入材料。"
        ),
        "field_experience_refs_help": "支持这个项目叙事的经历案例。",
        "field_output_refs_help": "与这个项目相关的输出或公开草稿。",
        "project_refs_hint": (
            "这里的关联表示项目归属，不会复制目标或证据正文；模型建议的关联也需要保存前确认。"
        ),
        "project_ai_suggest_refs": "AI 建议关联",
        "project_ai_suggest_help": (
            "让模型建议目标、任务、证据、资料和输出关联。建议只会预填表单，点击保存项目后才会写入。"
        ),
        "project_ai_suggest_running": "正在建议项目关联...",
        "project_ai_suggest_applied": "已向表单加入 {count} 个建议关联，请确认后再保存。",
        "project_ai_suggest_none": "没有新的项目关联建议。",
        "project_ai_suggest_failed": "项目关联建议失败。",
        "project_ai_suggest_summary": "表单中已暂存 {count} 个建议关联。",
        "project_missing_reload": "项目 `{id}` 已变化或被移除。已读取最新看板，请刷新后再编辑。",
        "milestone_missing_reload": "里程碑 `{id}` 已变化或被移除。请刷新后再编辑。",
        "field_target": "目标日期",
        "field_milestone": "里程碑",
        "task_title": "任务标题",
        "task_section": "列",
        "no_milestone": "无里程碑",
        "id_help": "留空会自动生成 project:<slug>。",
        "milestone_id_help": "留空会自动生成 milestone:<slug>。",
        "title_required": "标题不能为空。",
        "duplicate_milestone": "里程碑 id 已存在：{id}",
        "missing_ref": "缺失",
        "claimed_elsewhere_hint": (
            "{count} 个任务已属于其他项目，因此不会出现在这个选择器里。"
        ),
        "card_counts": (
            "目标 {goals} · 任务 {tasks} · 证据 {evidence} · "
            "资料 {sources} · 里程碑 {milestones}"
        ),
        "metric_unassigned_tasks": "未归属任务",
        "metric_unassigned_evidence": "未归属证据",
        "metric_current_goal_projects": "当前目标项目",
        "unassigned_evidence_hint": (
            "{count} 条已审阅证据尚未关联任何项目。"
        ),
        "status_active": "进行中",
        "status_paused": "暂停",
        "status_completed": "已完成",
        "status_archived": "已归档",
        "status_planned": "计划中",
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
        "page_help_short": "Guide",
        "page_help_body": (
            "### Gap Analysis workflow\n\n"
            "1. Describe the task as concretely as possible: target system, constraints, expected result, and unknowns.\n"
            "2. Use rule matching for deterministic keyword coverage; enable AI routing when the task language does not match the schema well.\n"
            "3. Include current goal context when the task should be interpreted through the active stage goal.\n"
            "4. Read matched nodes and dependency closure before trusting the suggested next steps.\n"
            "5. Apply skill status updates only after the task is actually completed and evidence exists.\n\n"
            "This page is a planning lens. It should not replace Evidence Review."
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
        "context_source_label": "Context source",
        "context_privacy_label": "Context privacy: {state}",
        "result_source_line": "Source: {source} ({kind})",
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
        "page_help_short": "使用说明",
        "page_help_body": (
            "### 差距分析使用流程\n\n"
            "1. 尽量具体描述任务：目标系统、约束、期望结果和未知点。\n"
            "2. 规则匹配适合可解释的关键词覆盖；当任务语言和技能 schema 不一致时，再开启 AI 首轮匹配。\n"
            "3. 任务需要围绕当前阶段目标解释时，勾选 current goal 上下文。\n"
            "4. 先看匹配节点和依赖闭包，再参考建议下一步。\n"
            "5. 只有任务完成且证据存在后，才应用技能状态更新。\n\n"
            "本页是规划视角，不替代证据审阅。"
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
        "context_source_label": "上下文来源",
        "context_privacy_label": "上下文隐私：{state}",
        "result_source_line": "来源：{source}（{kind}）",
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
        "page_help_short": "Guide",
        "page_help_body": (
            "### Skill Tree workflow\n\n"
            "1. Treat status as a claim about capability, not as a mood marker.\n"
            "2. Add inline evidence for quick notes, or attach stable evidence-pool rows when the same proof supports several skills.\n"
            "3. Use Evidence Review for stronger review status, confidence, project refs, and publish readiness.\n"
            "4. Save writes skill-tree.yaml and refreshes generated SKILL.md blocks.\n"
            "5. Check evidence risk warnings before raising a skill to solid or expert.\n\n"
            "Skill status should move only when evidence can explain why."
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
        "page_help_short": "使用说明",
        "page_help_body": (
            "### 技能树使用流程\n\n"
            "1. 把技能状态当作能力 claim，而不是当天心情或主观感觉。\n"
            "2. 轻量记录可写入内联证据；同一证据支撑多个技能时，优先放入共享证据池并用 id 引用。\n"
            "3. 证据强度、置信度、项目引用和公开准备度请在证据审阅里处理。\n"
            "4. 点击保存会写入 skill-tree.yaml，并刷新 SKILL.md 中的生成块。\n"
            "5. 将技能提升到扎实或专家前，先检查证据风险提示。\n\n"
            "技能升级必须能被证据解释。"
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
        "evidence_review_link": "打开证据审阅",
        "evidence_signal_count": "{n} 条 evidence",
        "evidence_signal_strength": "强度：{strength}",
        "evidence_signal_review": "审阅：{status}",
        "evidence_signal_missing": "缺少 evidence",
        "evidence_signal_risk": "证据风险：{reason}",
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
        "page_help_short": "Guide",
        "evidence_ai_short": "Evidence AI",
        "evidence_ai_config_caption": (
            "These settings only affect Evidence Review actions for the active profile: "
            "Done-to-evidence drafting and Kanban task understanding."
        ),
        "evidence_ai_backend": "Evidence AI engine",
        "evidence_ai_backend_help": (
            "LLM uses the global AI / LLM runtime. Codex uses the shared service-level "
            "Codex CLI in read-only mode."
        ),
        "evidence_ai_subtasks_model": "Done -> evidence model",
        "evidence_ai_subtasks_help": "Generate reviewable evidence drafts from selected Done tasks.",
        "evidence_ai_alignment_model": "Task alignment model",
        "evidence_ai_alignment_help": "Clarify underspecified Kanban cards before drafting.",
        "evidence_ai_codex_model_placeholder": "Codex CLI default",
        "evidence_ai_config_saved": "Evidence AI preferences saved.",
        "evidence_ai_default_hint": "App default: {backend}",
        "evidence_help_body": (
            "### Evidence Review workflow\n\n"
            "1. **Done Queue / Housekeeping**: select completed Kanban tasks, generate a reviewable evidence draft, then apply only the rows you trust.\n"
            "2. **Claim Studio**: turn reviewed evidence into reusable public claims by project, goal, skill, all evidence, or manual selection.\n"
            "3. **Evidence Pool**: edit evidence rows, strength, confidence, review status, and public readiness.\n"
            "4. **Skill Links**: link active evidence to skill nodes so status upgrades stay grounded.\n"
            "5. **Project / Experience Refs**: connect evidence to project cases, experience cases, and research sources.\n"
            "6. **Status Risks**: check solid/expert skills whose evidence strength is too weak before publishing or upgrading claims.\n\n"
            "AI never writes directly without a preview/apply step on this page."
        ),
        "save_pool": "Save evidence pool",
        "saved_pool": "Saved evidence-pool.yaml.",
        "saved_pool_synced": "Saved evidence-pool.yaml and synced SKILL.md.",
        "metric_done_uncrystallized": "Done not crystallized",
        "metric_unlinked": "Unlinked evidence",
        "metric_needs_review": "Needs review",
        "metric_status_risk": "Status evidence risk",
        "tab_queue": "Done Queue / Housekeeping",
        "tab_claims": "Claim Studio",
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
        "done_housekeeping_title": "Done housekeeping",
        "done_housekeeping_caption": (
            "Archive or delete Done tasks after their evidence review is handled."
        ),
        "done_housekeeping_pick": "Pick Done tasks",
        "done_housekeeping_archive": "Archive selected Done tasks",
        "done_housekeeping_delete": "Delete selected Done tasks",
        "done_housekeeping_confirm_archive": "Confirm archive selected",
        "done_housekeeping_confirm_delete": "Confirm delete selected",
        "done_housekeeping_uncrystallized_warning": (
            "Some selected tasks are not crystallized yet. Archive or delete only if "
            "you are sure they do not need Done -> evidence review."
        ),
        "done_housekeeping_confirm_uncrystallized": (
            "I understand the selected uncrystallized Done tasks may not have evidence yet"
        ),
        "done_housekeeping_archived": "Archived {n} Done task(s).",
        "done_housekeeping_deleted": "Deleted {n} Done task(s).",
        "done_housekeeping_empty": "No Done tasks to clean up.",
        "done_crystallized_label": "crystallized",
        "done_uncrystallized_label": "uncrystallized",
        "review_rows_title": "Pool rows needing review",
        "review_rows_empty": "No evidence rows need review.",
        "unlinked_rows_title": "Unlinked evidence",
        "unlinked_rows_empty": "All active evidence rows are linked to skills.",
        "claim_candidates_title": "Evidence -> claim candidates",
        "claim_studio_title": "Claim Studio",
        "claim_studio_intro": (
            "Generate reusable public claims from reviewed evidence by "
            "project, goal, skill, all evidence, or manual selection."
        ),
        "claim_studio_caption": "Claims are stored in {path}.",
        "claim_tab_overview": "Overview",
        "claim_tab_project": "By Project",
        "claim_tab_goal": "By Goal",
        "claim_tab_skill": "By Skill",
        "claim_tab_all": "All Evidence",
        "claim_tab_refresh": "Needs Refresh",
        "claim_tab_manual": "Manual",
        "claim_scope_project": "Project",
        "claim_scope_goal": "Goal",
        "claim_scope_skill": "Skill",
        "claim_scope_empty": "No scope options yet.",
        "claim_project_refs": "Projects: {refs}",
        "claim_goal_refs": "Goals: {refs}",
        "claim_metric_accepted": "Accepted",
        "claim_metric_draft": "Draft",
        "claim_metric_refresh": "Needs refresh",
        "claim_metric_unsupported": "Unsupported",
        "claim_refresh_statuses": "Refresh claim statuses",
        "claim_refresh_empty": "No claims need refresh.",
        "claim_legacy_warning": "Legacy claims still exist in evidence-pool.yaml.",
        "claim_migrate_legacy": "Migrate legacy claims",
        "claim_migrated": "Migrated {n} claim(s).",
        "claim_text": "Claim text",
        "claim_status": "Claim status",
        "claim_save": "Save claim",
        "claim_pick_evidence": "Pick evidence rows",
        "claim_generate": "Generate claim candidates",
        "claim_candidates_empty": "No claim candidates yet.",
        "claim_existing_title": "Accepted claims",
        "claim_candidates_preview": "Claim candidate preview",
        "claim_adopt": "Adopt claim",
        "claim_evidence_refs": "Evidence: {refs}",
        "claim_skill_refs": "Skills: {refs}",
        "claim_public_readiness": "Public readiness: {value}",
        "claim_confidence": "Confidence: {value}",
        "claim_apply_selected": "Apply {n} selected claim(s)",
        "claim_apply_empty": "No valid claim candidates were applied.",
        "claim_applied": "Applied {n} claim(s).",
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
        "refs_case_editor_title": "Project and experience owners",
        "refs_open_project_board": "Open Project Board",
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
        "page_title": "证据审阅 · nblane",
        "title": "证据审阅",
        "page_context_line": (
            "审阅已完成工作、证据池条目、技能关联与强度风险，"
            "避免技能状态变成没有证据支撑的断言。"
        ),
        "page_help_short": "使用说明",
        "evidence_ai_short": "证据 AI",
        "evidence_ai_config_caption": (
            "这些设置只影响当前档案的证据审阅动作："
            "已完成任务到证据草案，以及看板任务理解。"
        ),
        "evidence_ai_backend": "证据 AI 引擎",
        "evidence_ai_backend_help": (
            "LLM 使用全局 AI / LLM 运行时；Codex 使用当前部署共享的 service-level "
            "Codex CLI 只读模式。"
        ),
        "evidence_ai_subtasks_model": "已完成任务 → 证据模型",
        "evidence_ai_subtasks_help": "从所选已完成任务生成可审阅的证据草案。",
        "evidence_ai_alignment_model": "任务理解模型",
        "evidence_ai_alignment_help": "在生成草案前，澄清描述不完整的看板任务。",
        "evidence_ai_codex_model_placeholder": "Codex CLI 默认模型",
        "evidence_ai_config_saved": "证据 AI 配置已保存。",
        "evidence_ai_default_hint": "应用默认：{backend}",
        "evidence_help_body": (
            "### 证据审阅使用流程\n\n"
            "1. **已完成队列 / 整理**：选择已完成的看板任务，生成可审阅的证据草案，只应用你确认可信的条目。\n"
            "2. **断言工作台**：从已审阅证据按项目、目标、技能、全部证据或手动选择生成可复用公开断言。\n"
            "3. **证据池**：维护证据条目的强度、置信度、审阅状态、公开准备度和引用。\n"
            "4. **技能关联**：把活跃证据绑定到技能节点，避免技能状态没有证据支撑。\n"
            "5. **项目 / 经历引用**：把证据关联到项目案例、经历案例和研究资料。\n"
            "6. **状态风险**：发布或升级前检查扎实/专家技能是否缺少足够强的证据。\n\n"
            "本页 AI 只生成候选，必须经过预览和人工应用才会写入文件。"
        ),
        "save_pool": "保存证据池",
        "saved_pool": "已保存 evidence-pool.yaml。",
        "saved_pool_synced": "已保存 evidence-pool.yaml，并同步 SKILL.md。",
        "metric_done_uncrystallized": "已完成未结晶",
        "metric_unlinked": "未挂技能",
        "metric_needs_review": "待审阅",
        "metric_status_risk": "状态证据风险",
        "tab_queue": "已完成队列 / 整理",
        "tab_claims": "断言工作台",
        "tab_pool": "证据池",
        "tab_links": "技能关联",
        "tab_refs": "项目 / 经历引用",
        "tab_risks": "状态风险",
        "done_queue_title": "已完成 -> 证据候选",
        "done_queue_empty": "没有等待证据审阅的已完成任务。",
        "done_generate": "生成已完成 -> 证据草案",
        "done_pick": "选择已完成任务",
        "done_allow_status": "允许 AI 更新状态",
        "done_allow_status_help": (
            "关闭：只合并 evidence 与引用；有 evidence 的 locked 节点可变为 "
            "learning。开启：AI status 仍只允许升级，expert 不会被自动采信。"
        ),
        "done_mark_crystallized": "应用后标记所选已完成任务为已结晶",
        "done_preview_source": "来源已完成任务：{sources}",
        "done_no_ai": "未配置 AI。",
        "done_spinner": "生成证据草案中…",
        "done_apply_selected": "应用所选",
        "done_apply_all": "应用全部",
        "done_applied": "已应用证据草案。",
        "done_housekeeping_title": "已完成任务整理",
        "done_housekeeping_caption": (
            "在证据审阅完成后，把已完成任务批量归档或删除。"
        ),
        "done_housekeeping_pick": "选择已完成任务",
        "done_housekeeping_archive": "归档所选已完成任务",
        "done_housekeeping_delete": "删除所选已完成任务",
        "done_housekeeping_confirm_archive": "确认归档所选",
        "done_housekeeping_confirm_delete": "确认删除所选",
        "done_housekeeping_uncrystallized_warning": (
            "所选任务中包含未结晶的已完成任务。只有确认它们不需要已完成任务 -> 证据 "
            "审阅时才建议归档或删除。"
        ),
        "done_housekeeping_confirm_uncrystallized": (
            "我确认所选未结晶已完成任务可能尚未生成证据"
        ),
        "done_housekeeping_archived": "已归档 {n} 个已完成任务。",
        "done_housekeeping_deleted": "已删除 {n} 个已完成任务。",
        "done_housekeeping_empty": "没有可整理的已完成任务。",
        "done_crystallized_label": "已结晶",
        "done_uncrystallized_label": "未结晶",
        "review_rows_title": "需要审阅的池条目",
        "review_rows_empty": "没有需要审阅的证据条目。",
        "unlinked_rows_title": "未挂技能的证据",
        "unlinked_rows_empty": "所有活跃证据都已关联技能。",
        "claim_candidates_title": "证据 -> 断言候选",
        "claim_studio_title": "断言工作台",
        "claim_studio_intro": (
            "从已审阅证据按项目、目标、技能、全量证据或手动选择生成可复用的对外断言。"
        ),
        "claim_studio_caption": "断言保存于 {path}。",
        "claim_tab_overview": "概览",
        "claim_tab_project": "按项目",
        "claim_tab_goal": "按目标",
        "claim_tab_skill": "按技能",
        "claim_tab_all": "全部证据",
        "claim_tab_refresh": "需要刷新",
        "claim_tab_manual": "手动",
        "claim_scope_project": "项目",
        "claim_scope_goal": "目标",
        "claim_scope_skill": "技能",
        "claim_scope_empty": "暂无可选范围。",
        "claim_project_refs": "项目：{refs}",
        "claim_goal_refs": "目标：{refs}",
        "claim_metric_accepted": "已确认",
        "claim_metric_draft": "草稿",
        "claim_metric_refresh": "需刷新",
        "claim_metric_unsupported": "缺支撑",
        "claim_refresh_statuses": "刷新断言状态",
        "claim_refresh_empty": "没有需要刷新的断言。",
        "claim_legacy_warning": "evidence-pool.yaml 中仍有旧断言。",
        "claim_migrate_legacy": "迁移旧断言",
        "claim_migrated": "已迁移 {n} 条断言。",
        "claim_text": "断言文本",
        "claim_status": "断言状态",
        "claim_save": "保存断言",
        "claim_pick_evidence": "选择证据条目",
        "claim_generate": "生成断言候选",
        "claim_candidates_empty": "暂无断言候选。",
        "claim_existing_title": "已确认断言",
        "claim_candidates_preview": "断言候选预览",
        "claim_adopt": "采纳断言",
        "claim_evidence_refs": "证据：{refs}",
        "claim_skill_refs": "技能：{refs}",
        "claim_public_readiness": "公开准备度：{value}",
        "claim_confidence": "置信度：{value}",
        "claim_apply_selected": "应用 {n} 条已选断言",
        "claim_apply_empty": "没有可应用的断言候选。",
        "claim_applied": "已应用 {n} 条断言。",
        "pool_add_title": "新增证据条目",
        "pool_edit_title": "编辑证据条目",
        "pool_empty": "尚无证据条目。",
        "pool_deprecate": "软下线",
        "pool_deprecated": "已软下线证据条目。",
        "pool_add": "添加证据",
        "pool_added": "已添加证据条目。",
        "pool_update": "更新条目",
        "pool_updated": "已更新证据条目。",
        "pool_id": "证据 id",
        "pool_type": "类型",
        "pool_title": "标题",
        "pool_date": "日期",
        "pool_url": "链接",
        "pool_summary": "摘要",
        "pool_strength": "强度",
        "pool_confidence": "置信度",
        "pool_review_status": "审阅状态",
        "pool_public_readiness": "公开准备度",
        "pool_source_refs": "来源引用（每行一项）",
        "pool_project_refs": "项目引用",
        "pool_experience_refs": "经历引用",
        "pool_replaced_by": "替代条目",
        "pool_title_required": "证据标题不能为空。",
        "pool_id_exists": "证据 id 已存在：{id}",
        "link_title": "把证据关联到技能",
        "link_pick_evidence": "证据条目",
        "link_pick_skills": "技能",
        "link_button": "关联所选技能",
        "link_done": "已把证据关联到所选技能。",
        "link_empty": "没有可关联的活跃证据条目。",
        "refs_options_title": "可关联对象",
        "refs_options_empty": "暂无记录。",
        "refs_projects": "项目案例",
        "refs_experiences": "经历案例",
        "refs_sources": "研究资料",
        "refs_linker_title": "关联证据到项目 / 经历 / 来源",
        "refs_manual_source_refs": "研究收件箱之外的手动来源引用",
        "refs_save": "保存引用",
        "refs_saved": "已保存证据引用。",
        "refs_evidence_missing": "未找到证据条目。",
        "refs_case_editor_title": "项目 / 经历归属",
        "refs_open_project_board": "打开项目看板",
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
        "refs_goal_refs": "目标引用",
        "refs_task_refs": "任务引用",
        "refs_output_refs": "输出引用",
        "refs_notes": "备注",
        "refs_add_project": "新增项目案例",
        "refs_add_experience": "新增经历案例",
        "refs_case_saved": "已保存案例。",
        "risk_empty": "没有扎实/专家证据强度风险。",
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
        "dashboard_output_empty": "Public layer has no summary yet. Open Output Studio to initialize drafts.",
        "dashboard_public_drafts": "Drafts",
        "dashboard_public_published": "Published",
        "dashboard_public_visibility": "Visibility",
        "dashboard_public_build": "Build",
        "dashboard_public_build_exists": "Built",
        "dashboard_public_build_missing": "Not built",
        "dashboard_public_build_detail": "{pages} HTML page(s) at `{path}`.",
        "dashboard_quick_title": "Quick actions",
        "dashboard_priority_goal_title": "Current goal",
        "dashboard_priority_work_title": "This week's execution",
        "dashboard_priority_evidence_title": "Evidence to organize",
        "dashboard_scope_title": "Scope",
        "dashboard_scope_profile": "Profile",
        "dashboard_scope_goal": "Goal",
        "dashboard_scope_ai": "AI",
        "dashboard_scope_health": "Health",
        "dashboard_primary_actions_title": "Start here",
        "dashboard_action_capture": "Quick capture",
        "dashboard_action_capture_help": "Capture a source or note into Research.",
        "dashboard_action_kanban": "Open Kanban",
        "dashboard_action_evidence": "Organize evidence",
        "dashboard_action_output": "Generate output",
        "dashboard_canvas_section_title": "Context Canvas",
        "dashboard_canvas_section_caption": "Graph view loads after the stable daily summary.",
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
        "dashboard_help_title": "Dashboard guide",
        "dashboard_help_full_doc": "Open full Dashboard guide",
        "dashboard_help_body": (
            "### How to read this dashboard\n\n"
            "The top cards answer what you are pursuing now: North Star, primary goal, active goals, and current work.\n\n"
            "The canvas follows the Growth Graph: **Source** is raw material, **Evidence** is reviewable fact, "
            "**Claim** is interpretation, **Skill** is capability state, and **Output** is public or reusable expression.\n\n"
            "Use **Capture source** for lightweight notes and links. Captures stay private in Research until reviewed; "
            "they do not become evidence or skill status automatically.\n\n"
            "Use **Evidence Review** for Done tasks, unlinked evidence, claim candidates, and status risks. "
            "AI can suggest links or summaries, but confirmed facts still require review.\n\n"
            "**Dashboard AI settings** only affect Dashboard actions such as goal-skill matching and graph insights. "
            "Research has its own Research AI settings for paper search, translation, Reader, and DeepRead.\n\n"
            "8503 owns safe profile selection and writes. 8502 can host a richer canvas or reader surface when the sidecar is running."
        ),
        "dashboard_ai_settings_title": "Dashboard AI",
        "dashboard_ai_settings_caption": (
            "These settings only affect Dashboard AI actions for the active profile. Research, Kanban, and other pages keep their own page-level AI preferences. API keys are never written here."
        ),
        "dashboard_ai_action_goal_skill_match": "Goal-skill match",
        "dashboard_ai_action_goal_skill_match_help": "Suggest skill nodes for a goal. Candidates must be confirmed before saving.",
        "dashboard_ai_action_graph_insights": "Graph insights",
        "dashboard_ai_action_graph_insights_help": "Summarize graph risks and next actions without changing files.",
        "dashboard_ai_backend": "Backend",
        "dashboard_ai_llm_model": "LLM model",
        "dashboard_ai_codex_model": "Codex model",
        "dashboard_ai_use_default": "Use default",
        "dashboard_ai_custom_model": "Custom model",
        "dashboard_ai_app_default": "App default",
        "dashboard_ai_codex_default": "Codex default",
        "dashboard_ai_effective": "Effective: {backend} · {model}",
        "dashboard_ai_effective_backend": "Effective backend: {backend}",
        "dashboard_ai_effective_model": "Effective model: {model}",
        "dashboard_ai_test": "Test",
        "dashboard_ai_test_model": "Test model",
        "dashboard_ai_available": "available",
        "dashboard_ai_unavailable": "unavailable",
        "dashboard_ai_llm_unconfigured": "LLM API key is not configured.",
        "dashboard_ai_model_available": "Model test succeeded ({seconds}s).",
        "dashboard_ai_configured": "configured",
        "dashboard_ai_missing": "missing",
        "dashboard_ai_missing_key": "missing key",
        "dashboard_ai_installed": "installed",
        "dashboard_ai_logged_in": "logged in",
        "dashboard_ai_login_unknown": "login unknown",
        "dashboard_ai_llm_status": "LLM: {status} · {model}",
        "dashboard_ai_codex_status": "Codex: {status}",
        "dashboard_ai_save": "Save AI settings",
        "dashboard_ai_saved": "Dashboard AI settings saved.",
        "dashboard_ai_test_goal_skill_match": "Test goal-skill model",
        "dashboard_ai_test_ok": "Model test succeeded ({seconds}s).",
        "dashboard_open_8502_canvas": "Open 8502 Canvas",
        "dashboard_canvas_sidecar_unavailable": "8502 Dashboard Canvas is not reachable at {base}; using the local Dashboard fallback.",
        "dashboard_canvas_sidecar_link_disabled_help": "Start or forward the 8502 Dashboard Canvas sidecar to use this link.",
        "dashboard_embedded_canvas_title": "Embedded canvas",
        "dashboard_canvas_summary_title": "Canvas summary",
        "dashboard_canvas_summary_caption": "The daily dashboard keeps the big canvas folded until you need deeper graph exploration.",
        "dashboard_canvas_load_embed": "Load embedded canvas",
        "dashboard_graph_hero_title": "Live growth graph",
        "dashboard_graph_hero_caption": "A compact 3D map of today's goals, sources, evidence, skills, and outputs.",
        "dashboard_hero_start_here": "Start here",
        "dashboard_graph_selected_node": "Selected node",
        "dashboard_graph_open_selected": "Open selected in 8502",
        "dashboard_today_focus_title": "Today focus",
        "dashboard_action_queue_title": "Action queue",
        "dashboard_action_review_evidence": "Review evidence",
        "dashboard_action_open_focus": "Open current work",
        "dashboard_action_open_kanban_hint": "Choose current work from Kanban.",
        "dashboard_action_resolve_gap": "Resolve gap risk",
        "dashboard_action_gap_clear": "No urgent gap signal.",
        "dashboard_action_open_output": "Open output drafts",
        "dashboard_action_draft_output": "Draft output",
        "dashboard_action_review_source": "Review source",
        "dashboard_action_capture_source": "Capture source",
        "dashboard_open_research": "Open Research",
        "dashboard_action_why_evidence": "Evidence queues are the highest-confidence next review work.",
        "dashboard_action_why_clear": "No urgent queue is blocking the daily path.",
        "dashboard_action_why_focus": "Current Doing work keeps today's actions tied to the active goal.",
        "dashboard_action_why_focus_empty": "Pick one active task before expanding the rest of the system.",
        "dashboard_action_why_gap": "Gap risks can block the current goal if they stay unresolved.",
        "dashboard_action_why_output": "Drafts are ready to turn reviewed work into reusable output.",
        "dashboard_action_why_output_empty": "Create an output only after the review queues have enough support.",
        "dashboard_capture_more_fields": "More fields",
        "dashboard_canvas_more_filters": "More filters",
        "dashboard_claim_summary": "Claims translate reviewed evidence into skill and output assertions.",
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
        "dashboard_add_active_goal": "Add goal",
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
        "dashboard_view_focus_path": "Focus Path",
        "dashboard_view_attention": "Attention",
        "dashboard_view_3d_graph": "3D Graph",
        "dashboard_graph_fit": "Fit",
        "dashboard_graph_focus_selected": "Focus",
        "dashboard_open_8503": "Open 8503",
        "dashboard_explore_title": "Graph",
        "dashboard_explore_nodes": "Graph nodes",
        "dashboard_explore_all": "All",
        "dashboard_explore_context": "Context",
        "dashboard_explore_upstream": "Upstream",
        "dashboard_explore_downstream": "Downstream",
        "dashboard_explore_search": "Search",
        "dashboard_explore_search_placeholder": "Node, layer, status",
        "dashboard_explore_hide_placeholders": "Hide placeholders",
        "dashboard_explore_result_count": "shown",
        "dashboard_explore_no_matches": "No graph nodes match this filter.",
        "dashboard_explore_lane_direction": "Direction",
        "dashboard_explore_lane_work_source": "Work / Source",
        "dashboard_explore_lane_evidence_claim": "Evidence / Claim",
        "dashboard_explore_lane_skill_gap": "Skill / Gap",
        "dashboard_explore_lane_output_feedback": "Output / Feedback",
        "dashboard_attention_title": "Attention",
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
        "dashboard_private_source": "Private source",
        "dashboard_node_evidence_candidate": "Evidence Candidates",
        "dashboard_node_atomic_evidence": "Atomic Evidence",
        "dashboard_private_evidence": "Private evidence",
        "dashboard_node_composite_evidence": "Composite Evidence",
        "dashboard_node_claim": "Claims",
        "dashboard_private_claim": "Private claim",
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
        "quick_public_site": "Output Studio",
        "quick_public_site_help": "Review drafts and create public output.",
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
            "Git 是唯一可信来源。"
        ),
        "dashboard_status_overview": "状态概览",
        "dashboard_metric_goal": "当前目标",
        "dashboard_primary_goal": "主目标",
        "dashboard_active_goal": "活跃目标",
        "dashboard_active_goals_title": "活跃目标",
        "dashboard_goal_set": "已设置",
        "dashboard_goal_missing": "未设置",
        "dashboard_metric_skill_lit": "已点亮技能",
        "dashboard_skill_progress_suffix": "扎实 / 专家",
        "dashboard_metric_doing": "进行中",
        "dashboard_metric_pending_evidence": "待整理证据",
        "dashboard_metric_health": "健康 E/W/I",
        "dashboard_metric_health_help": "来自档案体检的错误 / 警告 / 信息数量。",
        "dashboard_public_not_initialized": (
            "公开层尚未初始化；首页这里只提供入口。"
        ),
        "dashboard_doing_title": "本周进行中",
        "dashboard_doing_empty": "当前没有进行中任务。打开看板选择本周正在推进的工作。",
        "dashboard_doing_started": "开始于 {date}",
        "dashboard_doing_blocked": "阻塞：{blocked}",
        "dashboard_doing_more": "看板上还有 {n} 个 Doing 任务。",
        "dashboard_pending_evidence_title": "待整理证据",
        "dashboard_done_uncrystallized": "已完成但未结晶",
        "dashboard_unlinked_evidence": "未挂技能的证据",
        "dashboard_needs_review_evidence": "待审阅证据",
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
        "dashboard_output_empty": "公开层暂无摘要。进入输出工作台初始化草稿。",
        "dashboard_public_drafts": "草稿",
        "dashboard_public_published": "已发布",
        "dashboard_public_visibility": "可见性",
        "dashboard_public_build": "构建",
        "dashboard_public_build_exists": "已构建",
        "dashboard_public_build_missing": "未构建",
        "dashboard_public_build_detail": "`{path}` 下有 {pages} 个 HTML 页面。",
        "dashboard_quick_title": "快捷操作",
        "dashboard_priority_goal_title": "当前目标",
        "dashboard_priority_work_title": "本周执行",
        "dashboard_priority_evidence_title": "待整理证据",
        "dashboard_scope_title": "当前范围",
        "dashboard_scope_profile": "档案",
        "dashboard_scope_goal": "目标",
        "dashboard_scope_ai": "AI",
        "dashboard_scope_health": "健康",
        "dashboard_primary_actions_title": "从这里开始",
        "dashboard_action_capture": "快速捕获",
        "dashboard_action_capture_help": "把来源、笔记或想法先放入 Research。",
        "dashboard_action_kanban": "打开看板",
        "dashboard_action_evidence": "整理证据",
        "dashboard_action_output": "生成输出",
        "dashboard_canvas_section_title": "上下文画布",
        "dashboard_canvas_section_caption": "稳定的每日摘要先显示，图谱画布在下方加载。",
        "dashboard_overview_map_title": "当前地图",
        "dashboard_graph_eyebrow": "上下文",
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
        "dashboard_help_title": "使用说明",
        "dashboard_help_full_doc": "打开完整 Dashboard 使用说明",
        "dashboard_help_body": (
            "### 如何阅读 Dashboard\n\n"
            "顶部卡片回答当前正在追求什么：长期方向、主目标、活跃目标和当前工作。\n\n"
            "画布遵循成长图谱：**来源** 是原始材料，**证据** 是可审查事实，"
            "**断言** 是解释和结论，**技能** 是能力状态，**输出** 是公开或可复用表达。\n\n"
            "用 **捕捉来源** 记录轻量笔记和链接。捕捉内容默认进入研究工作台的私有收件箱；"
            "不会自动变成证据，也不会自动改技能状态。\n\n"
            "用 **证据审阅** 处理已完成任务、未链接证据、claim 候选和状态风险。"
            "AI 可以生成候选和摘要，但事实确认仍需要人工审阅。\n\n"
            "**本页 AI 设置**只影响首页内的目标-技能匹配和图谱洞察。"
            "研究工作台有自己的研究 AI 设置，用于论文搜索、翻译、阅读器和深读。\n\n"
            "8503 负责安全的档案选择与写入；8502 sidecar 启动后可承载更高交互的画布或阅读器界面。"
        ),
        "dashboard_ai_settings_title": "本页 AI 设置",
        "dashboard_ai_settings_caption": "这些设置只影响当前档案的首页 AI 动作。研究、看板等页面保留自己的页面级 AI 设置；这里不会写入 API key。",
        "dashboard_ai_action_goal_skill_match": "目标-技能匹配",
        "dashboard_ai_action_goal_skill_match_help": "为目标建议技能节点。候选必须确认后才会保存。",
        "dashboard_ai_action_graph_insights": "图谱洞察",
        "dashboard_ai_action_graph_insights_help": "总结图谱风险和下一步，不直接修改文件。",
        "dashboard_ai_backend": "后端",
        "dashboard_ai_llm_model": "LLM 模型",
        "dashboard_ai_codex_model": "Codex 模型",
        "dashboard_ai_use_default": "使用默认",
        "dashboard_ai_custom_model": "自定义模型",
        "dashboard_ai_app_default": "应用默认",
        "dashboard_ai_codex_default": "Codex 默认",
        "dashboard_ai_effective": "实际使用：{backend} · {model}",
        "dashboard_ai_effective_backend": "实际后端：{backend}",
        "dashboard_ai_effective_model": "实际模型：{model}",
        "dashboard_ai_test": "测试",
        "dashboard_ai_test_model": "测试模型",
        "dashboard_ai_available": "可用",
        "dashboard_ai_unavailable": "不可用",
        "dashboard_ai_llm_unconfigured": "LLM API key 未配置。",
        "dashboard_ai_model_available": "模型测试成功（{seconds}s）。",
        "dashboard_ai_configured": "已配置",
        "dashboard_ai_missing": "缺失",
        "dashboard_ai_missing_key": "缺少 key",
        "dashboard_ai_installed": "已安装",
        "dashboard_ai_logged_in": "已登录",
        "dashboard_ai_login_unknown": "登录状态未知",
        "dashboard_ai_llm_status": "LLM：{status} · {model}",
        "dashboard_ai_codex_status": "Codex：{status}",
        "dashboard_ai_save": "保存 AI 设置",
        "dashboard_ai_saved": "首页 AI 设置已保存。",
        "dashboard_ai_test_goal_skill_match": "测试目标-技能模型",
        "dashboard_ai_test_ok": "模型测试成功（{seconds}s）。",
        "dashboard_open_8502_canvas": "打开 8502 画布",
        "dashboard_canvas_sidecar_unavailable": "8502 画布当前不可达：{base}；已使用本地首页回退视图。",
        "dashboard_canvas_sidecar_link_disabled_help": "请先启动或转发 8502 画布 sidecar，再使用这个入口。",
        "dashboard_embedded_canvas_title": "内嵌画布",
        "dashboard_canvas_summary_title": "画布摘要",
        "dashboard_canvas_summary_caption": "日常首页先折叠大画布；需要深入探索图谱时再展开或打开 8502 画布。",
        "dashboard_canvas_load_embed": "加载内嵌画布",
        "dashboard_graph_hero_title": "实时成长图谱",
        "dashboard_graph_hero_caption": "用一张紧凑 3D 图把今天的目标、来源、证据、技能和输出串起来。",
        "dashboard_hero_start_here": "从这里开始",
        "dashboard_graph_selected_node": "当前节点",
        "dashboard_graph_open_selected": "在 8502 打开所选节点",
        "dashboard_today_focus_title": "今日焦点",
        "dashboard_action_queue_title": "行动队列",
        "dashboard_action_review_evidence": "整理证据",
        "dashboard_action_open_focus": "打开当前工作",
        "dashboard_action_open_kanban_hint": "从看板选择当前正在推进的工作。",
        "dashboard_action_resolve_gap": "处理缺口风险",
        "dashboard_action_gap_clear": "当前没有紧急缺口信号。",
        "dashboard_action_open_output": "打开输出草稿",
        "dashboard_action_draft_output": "起草输出",
        "dashboard_action_review_source": "审阅来源",
        "dashboard_action_capture_source": "捕捉来源",
        "dashboard_open_research": "打开研究工作台",
        "dashboard_action_why_evidence": "证据队列是当前最可靠的审阅入口。",
        "dashboard_action_why_clear": "没有紧急队列阻塞今日主路径。",
        "dashboard_action_why_focus": "进行中的工作能把今日动作保持在当前目标上。",
        "dashboard_action_why_focus_empty": "先选定一个活跃任务，再展开其他系统工作。",
        "dashboard_action_why_gap": "缺口风险如果不处理，会阻塞当前目标。",
        "dashboard_action_why_output": "草稿可以把已审阅工作转成可复用输出。",
        "dashboard_action_why_output_empty": "等审阅队列有足够支撑后再创建输出。",
        "dashboard_capture_more_fields": "更多字段",
        "dashboard_canvas_more_filters": "更多过滤",
        "dashboard_claim_summary": "断言会把已审阅证据翻译成可复用的技能与输出结论。",
        "north_star_strip_title": "长期方向",
        "north_star_empty": "尚未设置长期方向",
        "north_star_empty_action": "填写长期方向",
        "north_star_hidden_display": "已设置长期方向",
        "north_star_private_display": "私密长期方向",
        "north_star_edit_action": "编辑档案上下文",
        "north_star_visibility_visible": "完整显示",
        "north_star_visibility_discreet": "简略显示",
        "north_star_visibility_hidden": "隐藏明文",
        "north_star_visibility_private": "私密",
        "skill_alignment_title": "目标-技能关联",
        "skill_alignment_confirmed": "已确认关联",
        "skill_alignment_candidates": "候选关联",
        "skill_alignment_no_links": "尚无已确认技能关联。",
        "skill_alignment_no_candidates": "运行规则匹配或 AI 匹配后选择候选。",
        "skill_alignment_rule": "规则匹配",
        "skill_alignment_ai": "AI 匹配",
        "skill_alignment_confirm": "确认关联",
        "skill_alignment_manual_label": "手动添加",
        "skill_alignment_manual_add": "添加",
        "skill_alignment_suggested": "建议",
        "skill_alignment_gap_hint": "关联到锁定/学习中节点时，建议进入差距分析。",
        "goal_alignment_goal_missing": "未找到要关联技能的目标。",
        "goal_alignment_node_missing": "当前 schema 中没有这个技能节点。",
        "goal_alignment_candidates_ready": "已生成 {n} 个技能候选，请确认。",
        "goal_alignment_links_saved": "目标-技能关联已保存。",
        "goal_primary_saved": "主目标已更新。",
        "goal_archived": "目标已归档。",
        "dashboard_add_active_goal": "添加目标",
        "dashboard_archive_goal": "归档",
        "dashboard_inspector_empty": "选择一个节点查看详情。",
        "dashboard_inspector_node_hint": "进入归属页面查看完整内容。",
        "dashboard_inspector_placeholder_hint": "这个区域仍是骨架状态，还没有对应的真实记录。",
        "dashboard_inspector_locked_hint": "该节点的私密或锁定细节已在当前视图隐藏。",
        "dashboard_inspector_owner_reserved": "搭建状态",
        "dashboard_placeholder_metric": "预留",
        "dashboard_inspector_setup_title": "先完成基础设置，或选择真实节点",
        "dashboard_inspector_setup_hint": "当前图谱仍以骨架节点为主。建议先补长期方向，再设置当前目标。",
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
        "dashboard_capture_goal": "目标",
        "dashboard_capture_type": "类型",
        "dashboard_capture_type_note": "笔记",
        "dashboard_capture_type_link": "链接",
        "dashboard_capture_type_resource": "资源",
        "dashboard_capture_type_idea": "想法",
        "dashboard_source_inbox_title": "来源收件箱",
        "dashboard_source_inbox_empty": "还没有捕捉来源。",
        "dashboard_source_to_evidence_hint": "捕捉内容先进入收件箱，审阅后再成为证据候选。",
        "dashboard_atomic_evidence_title": "原子证据",
        "dashboard_evidence_candidate_title": "证据候选",
        "dashboard_atomic_evidence_unlinked": "未挂技能的原子证据",
        "dashboard_atomic_evidence_needs_review": "待审阅",
        "dashboard_atomic_evidence_status_risk": "状态风险",
        "dashboard_gap_risk_title": "缺口风险",
        "dashboard_feedback_planned": "反馈区域仍在搭建中。",
        "dashboard_graph_loading": "正在加载图谱…",
        "dashboard_graph_3d_hint": (
            "长期方向依次流向目标、项目容器、活动、来源、证据、断言、能力、输出、反馈与治理。"
            "可旋转、缩放；点击节点后在右侧查看。"
        ),
        "dashboard_view_canvas": "2D 画布",
        "dashboard_view_focus_path": "焦点路径",
        "dashboard_view_attention": "关注",
        "dashboard_view_3d_graph": "3D 全局图",
        "dashboard_graph_fit": "适配视图",
        "dashboard_graph_focus_selected": "聚焦所选",
        "dashboard_open_8503": "打开 8503",
        "dashboard_explore_title": "图谱",
        "dashboard_explore_nodes": "图谱节点",
        "dashboard_explore_all": "全部",
        "dashboard_explore_context": "上下文",
        "dashboard_explore_upstream": "上游",
        "dashboard_explore_downstream": "下游",
        "dashboard_explore_search": "搜索",
        "dashboard_explore_search_placeholder": "节点、层级、状态",
        "dashboard_explore_hide_placeholders": "隐藏占位节点",
        "dashboard_explore_result_count": "个可见",
        "dashboard_explore_no_matches": "没有符合当前过滤的图谱节点。",
        "dashboard_explore_lane_direction": "方向",
        "dashboard_explore_lane_work_source": "工作 / 来源",
        "dashboard_explore_lane_evidence_claim": "证据 / 断言",
        "dashboard_explore_lane_skill_gap": "能力 / 缺口",
        "dashboard_explore_lane_output_feedback": "输出 / 反馈",
        "dashboard_attention_title": "关注信号",
        "dashboard_workbench_title": "今日工作台",
        "dashboard_workbench_caption": "集中查看今天的信号、捕捉入口和快捷操作。",
        "dashboard_canvas_setup_title": "当前画布仍处于搭建阶段",
        "dashboard_canvas_setup_hint": "先补长期方向和当前目标，再逐步用真实来源与证据替换骨架。",
        "dashboard_canvas_missing_north_star": "缺少长期方向",
        "dashboard_canvas_missing_goal": "缺少当前目标",
        "dashboard_canvas_missing_sources": "还没有捕捉来源",
        "dashboard_canvas_reset_filters": "显示全部层",
        "dashboard_canvas_no_layers": "已隐藏全部层。",
        "dashboard_skill_progress_title": "技能进度",
        "dashboard_skill_progress_caption": "扎实 / 专家点亮率",
        "dashboard_skill_progress_empty": "暂无技能树数据。",
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
        "dashboard_private_source": "私密来源",
        "dashboard_node_evidence_candidate": "证据候选",
        "dashboard_node_atomic_evidence": "原子证据",
        "dashboard_private_evidence": "私密证据",
        "dashboard_node_composite_evidence": "组合证据",
        "dashboard_node_claim": "断言",
        "dashboard_private_claim": "私密断言",
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
        "quick_skill_tree": "技能地图",
        "quick_skill_tree_help": "编辑技能状态与证据引用。",
        "quick_evidence_review": "证据审阅",
        "quick_evidence_review_help": "审阅证据强度、技能关联与完成项结晶。",
        "quick_research": "研究工作台",
        "quick_research_help": "捕捉和整理外部来源。",
        "quick_gap": "差距分析",
        "quick_gap_help": "把任务映射到技能与缺口。",
        "quick_kanban": "看板",
        "quick_kanban_help": "查看进行中、队列与已完成任务。",
        "quick_public_site": "输出工作台",
        "quick_public_site_help": "查看草稿并生成公开输出。",
        "quick_profile_health": "档案体检",
        "quick_profile_health_help": "查看校验、同步漂移与证据风险。",
        "profile_evidence_import_expander": "批量导入档案证据",
        "profile_evidence_import_caption": (
            "粘贴简历或长文本，让 AI 生成证据与技能树变更草案；"
            "写入前请逐条审阅。"
        ),
        "profile_context_expander": "档案上下文 / SKILL.md",
        "profile_context_caption": (
            "高级区：维护长期的人写画像与 Agent 上下文；"
            "生成事实继续由各归属文件负责。"
        ),
        "profile_context_structured_title": "结构化画像",
        "profile_context_narrative_title": "长期叙事章节",
        "profile_context_narrative_caption": (
            "这些章节由人维护，继续写入 SKILL.md。"
        ),
        "identity_name": "姓名",
        "identity_domain": "领域",
        "identity_journey": "经历线索",
        "identity_current_role": "当前角色",
        "identity_north_star": "长期方向",
        "identity_north_star_brief": "长期方向摘要",
        "identity_north_star_visibility": "长期方向可见性",
        "profile_section_research_fingerprint": "研究指纹",
        "profile_section_thinking_style": "思考与沟通风格",
        "profile_section_growth_log": "成长记录",
        "profile_section_influence_output": "影响力与输出",
        "save_profile_context": "保存档案上下文",
        "generated_block_preview_title": "生成块预览",
        "generated_block_owner_hint": (
            "`skill_tree` 由 skill-tree.yaml / evidence-pool.yaml 负责；"
            "`current_focus` 由 kanban.md 负责。此处只读预览。"
        ),
        "generated_block_expander": "{block}",
        "generated_block_skill_tree_help": "归属：skill-tree.yaml 与 evidence-pool.yaml。",
        "generated_block_kanban_help": "归属：kanban.md 的当前焦点。",
        "generated_block_sync_hint": "如需刷新生成块，运行 `nblane sync <profile> --write`。",
        "generated_block_missing": "未找到该生成块。",
        "raw_markdown_expander": "原始 Markdown",
        "raw_drift_warning": (
            "原始编辑可能改到生成块并造成同步漂移。"
            "保存后请用档案体检检查漂移。"
        ),
        "tab_overview": "📊 概览",
        "tab_editor": "✏️ 结构化编辑",
        "tab_raw": "📝 原文",
        "sub_overview": "技能概览",
        "sub_category": "按分类",
        "goal_module_title": "当前目标",
        "goal_module_caption": (
            "4-8 周阶段目标，用来统一差距分析、证据整理和输出规划。"
        ),
        "goal_create_title": "创建当前目标",
        "goal_edit_title": "编辑当前目标",
        "goal_reveal_private": "本会话显示私密目标",
        "goal_private_locked": (
            "该目标标记为私密。需在本会话显式显示后才能编辑明文细节。"
        ),
        "goal_field_title": "标题",
        "goal_field_label": "隐私替代标签",
        "goal_field_status": "状态",
        "goal_field_start": "开始日期",
        "goal_field_target": "目标日期",
        "goal_field_summary": "摘要",
        "goal_field_alignment": "与长期方向的关系",
        "goal_field_target_skills": "目标技能（每行一项）",
        "goal_field_success_criteria": "成功标准（每行一项）",
        "goal_field_focus": "本周焦点（每行一项）",
        "goal_field_evidence_refs": "证据引用（每行一项）",
        "goal_field_task_refs": "任务引用（每行一项）",
        "goal_field_output_refs": "输出引用（每行一项）",
        "goal_field_notes": "私密备注",
        "goal_field_ui_visibility": "UI 展示级别",
        "goal_field_agent_context": "进入 Agent 上下文",
        "goal_field_public_output": "允许未来公开输出引用",
        "goal_public_disabled_caption": (
            "P0 只保存该字段，公开站构建不会读取 goals.yaml。"
        ),
        "goal_save": "保存当前目标",
        "goal_saved": "当前目标已保存。",
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
            "生成最新系统提示词。"
        ),
        "raw_label": (
            "编辑 SKILL.md（即 Agent 系统提示词的来源）"
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
        "page_help_short": "Guide",
        "page_help_body": (
            "### Kanban workflow\n\n"
            "1. Capture uncertain work into Queue or Inbox; keep Doing small enough to finish this week.\n"
            "2. Use task details for outcome, context, blockers, and links. Subtasks should be checkable execution steps.\n"
            "3. Done is not evidence by itself. Send Done tasks through Evidence Review before they upgrade skills or public claims.\n"
            "4. Personal check-ins record learning and exercise without cluttering execution columns.\n"
            "5. Kanban AI can draft subtasks or clarify vague tasks, but proposals must be accepted before they write to kanban.md.\n\n"
            "Save or autosave writes kanban.md and syncs project-board ownership."
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
        "kb_ai_backend": "Kanban AI",
        "kb_ai_backend_help": (
            "Choose the engine used by Kanban AI actions. Codex uses the "
            "local Codex CLI in read-only mode and needs no Kanban-specific "
            "configuration."
        ),
        "kb_ai_backend_llm": "LLM",
        "kb_ai_backend_codex": "Codex",
        "kb_ai_backend_codex_status": "Codex: read-only local",
        "kb_ai_settings_title": "Kanban AI Config",
        "kb_ai_settings_caption": (
            "These settings only affect Kanban task clarification and subtask drafting "
            "for the current profile. API keys still come from the shared AI / LLM runtime."
        ),
        "kb_ai_action_task_alignment": "Task clarification",
        "kb_ai_action_task_alignment_help": (
            "Suggest candidate interpretations before drafting subtasks for vague tasks."
        ),
        "kb_ai_action_subtasks": "Subtask drafting",
        "kb_ai_action_subtasks_help": (
            "Draft reviewable subtasks from the chosen task interpretation."
        ),
        "kb_ai_config_backend": "Backend",
        "kb_ai_config_llm_model": "LLM model override",
        "kb_ai_config_codex_model": "Codex model override",
        "kb_ai_config_model_help": "Leave blank to use the global/default model.",
        "kb_ai_effective_config": "Effective: {backend} · {model}",
        "kb_ai_llm_status": "LLM: {status} · {model}",
        "kb_ai_codex_status": "Codex: {status}",
        "kb_ai_configured": "configured",
        "kb_ai_missing_key": "missing key",
        "kb_ai_installed": "installed",
        "kb_ai_missing": "missing",
        "kb_ai_logged_in": "logged in",
        "kb_ai_login_unknown": "login unknown",
        "kb_ai_codex_default": "Codex CLI default",
        "kb_ai_app_default": "app default",
        "kb_ai_save": "Save AI preferences",
        "kb_ai_saved": "Kanban AI preferences saved.",
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
        "kb_project": "Project",
        "kb_milestone": "Milestone",
        "kb_no_project": "No project",
        "kb_no_milestone": "No milestone",
        "subtasks_label": "Subtasks (checkbox)",
        "add_subtask": "+ Subtask",
        "crystallized": "Crystallized (ingested)",
        "kb_open_evidence_review": "Open Evidence Review",
        "kb_done_review_hint": (
            "Use Evidence Review for Done -> evidence drafts and batch cleanup. "
            "Done cards still support single-card archive or delete here."
        ),
        "kb_archive_card": "Archive",
        "kb_archive_short": "Archive",
        "kb_archive_confirm": "Archive this Done task?",
        "kb_archive_done_only": "Only Done tasks can be archived from the board.",
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
        "ingest_preview_projects": "Projects: {projects}",
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
        "page_help_short": "使用说明",
        "page_help_body": (
            "### 看板使用流程\n\n"
            "1. 不确定的事项先放入队列或收件区；进行中保持足够小，确保本周能收尾。\n"
            "2. 任务详情写清结果、背景、阻塞和链接；子任务应是可勾选的执行步骤。\n"
            "3. 已完成不等于证据。Done 任务需要进入 Evidence Review，审阅后才支撑技能升级或公开 claim。\n"
            "4. 学习和运动记录放在个人工作台，避免污染执行列。\n"
            "5. 看板 AI 可以生成子任务或澄清模糊任务，但必须确认候选后才会写入 kanban.md。\n\n"
            "保存或自动保存会写入 kanban.md，并同步项目归属到 project-board.yaml。"
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
        "kb_ai_backend": "看板 AI",
        "kb_ai_backend_help": (
            "选择看板 AI 动作使用的引擎。Codex 使用本地 Codex CLI 的只读模式，"
            "不需要看板内额外配置。"
        ),
        "kb_ai_backend_llm": "LLM",
        "kb_ai_backend_codex": "Codex",
        "kb_ai_backend_codex_status": "Codex：本地只读",
        "kb_ai_settings_title": "看板 AI 配置",
        "kb_ai_settings_caption": (
            "这些设置只影响当前档案的看板任务理解与拆任务动作。API key 仍由全局 AI / LLM 运行时提供。"
        ),
        "kb_ai_action_task_alignment": "任务理解",
        "kb_ai_action_task_alignment_help": (
            "为含糊任务先生成候选理解，再进入拆任务。"
        ),
        "kb_ai_action_subtasks": "拆任务",
        "kb_ai_action_subtasks_help": (
            "基于已确认的任务理解生成可审阅的子任务草案。"
        ),
        "kb_ai_config_backend": "后端",
        "kb_ai_config_llm_model": "LLM 模型覆盖",
        "kb_ai_config_codex_model": "Codex 模型覆盖",
        "kb_ai_config_model_help": "留空则使用全局/应用默认模型。",
        "kb_ai_effective_config": "当前生效：{backend} · {model}",
        "kb_ai_llm_status": "LLM：{status} · {model}",
        "kb_ai_codex_status": "Codex：{status}",
        "kb_ai_configured": "已配置",
        "kb_ai_missing_key": "缺少 key",
        "kb_ai_installed": "已安装",
        "kb_ai_missing": "缺失",
        "kb_ai_logged_in": "已登录",
        "kb_ai_login_unknown": "登录状态未知",
        "kb_ai_codex_default": "Codex CLI 默认",
        "kb_ai_app_default": "应用默认",
        "kb_ai_save": "保存 AI 配置",
        "kb_ai_saved": "看板 AI 配置已保存。",
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
        "kb_project": "项目",
        "kb_milestone": "里程碑",
        "kb_no_project": "无项目",
        "kb_no_milestone": "无里程碑",
        "subtasks_label": "子任务（可勾选）",
        "add_subtask": "+ 子任务",
        "crystallized": "已结晶（已摄入）",
        "kb_open_evidence_review": "打开证据审阅",
        "kb_done_review_hint": (
            "已完成 -> 证据草案与批量整理统一在证据审阅处理；"
            "看板已完成卡片这里只保留单卡归档或删除。"
        ),
        "kb_archive_card": "归档",
        "kb_archive_short": "归档",
        "kb_archive_confirm": "归档这个 Done 任务？",
        "kb_archive_done_only": "只有 Done 任务可以在看板中归档。",
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
        "ingest_preview_projects": "项目：{projects}",
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
        "page_help_short": "Guide",
        "page_help_body": (
            "### Team View workflow\n\n"
            "1. Pick the team you are editing; team files live under teams/ and are not filtered by the personal profile.\n"
            "2. Update mission, members, rules, and priorities in team.yaml when the team operating context changes.\n"
            "3. Use product pools to collect shared problems, projects, evidence, methods, and decisions.\n"
            "4. Check the write-owner block before saving so you know which team files will change.\n"
            "5. Personal skill or evidence claims still belong in the selected profile pages, not team.yaml.\n\n"
            "Team View writes team.yaml and product-pool.yaml for the selected team."
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
        "write_owner": "Write owner",
        "team_scope": "Team scope",
        "writes": "Writes",
        "view_as_profile": "View-as profile",
        "save_team_path": "Save team.yaml -> {path}",
        "save_pool_path": "Save product-pool.yaml -> {path}",
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
        "page_help_short": "使用说明",
        "page_help_body": (
            "### 团队视图使用流程\n\n"
            "1. 先选择要编辑的团队；团队文件位于 teams/，不会按个人档案过滤。\n"
            "2. 团队使命、成员、规则和当前优先级变化时，更新 team.yaml。\n"
            "3. 产品池用于沉淀共享问题、项目、证据、方法和决策。\n"
            "4. 保存前查看写入范围，确认本次会修改哪些团队文件。\n"
            "5. 个人技能、个人证据和个人目标仍应回到当前 profile 的页面维护。\n\n"
            "本页写入所选团队的 team.yaml 和 product-pool.yaml。"
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
        "write_owner": "写入归属",
        "team_scope": "团队范围",
        "writes": "写入文件",
        "view_as_profile": "按档案查看",
        "save_team_path": "保存 team.yaml -> {path}",
        "save_pool_path": "保存 product-pool.yaml -> {path}",
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
        "page_context_line": (
            "Read-only health checks for profile trust, context readiness, "
            "and publication risks."
        ),
        "page_help_short": "Guide",
        "page_help_body": (
            "### Profile Health workflow\n\n"
            "1. Use this page as a read-only preflight before publishing, generating output, or trusting profile context.\n"
            "2. Errors are blockers; warnings usually need review; info items explain context quality.\n"
            "3. Follow suggested actions on the owner page instead of editing data here.\n"
            "4. Open Review when you need to turn recent activity into evidence, next actions, or draft output.\n"
            "5. Re-run after evidence, skill tree, project, or public layer edits.\n\n"
            "Health never writes files. It points to the page that should own each fix."
        ),
        "review_link": "Open Review",
        "review_link_help": (
            "Review candidates live in the Review page; Health stays read-only."
        ),
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
        "page_context_line": (
            "只读体检页：检查档案可信度、上下文可发布性和公开风险。"
        ),
        "page_help_short": "使用说明",
        "page_help_body": (
            "### 档案体检使用流程\n\n"
            "1. 发布、生成输出或信任 profile context 前，先把这里当作只读预检。\n"
            "2. 错误是阻断项；警告通常需要审阅；信息项用于解释上下文质量。\n"
            "3. 按建议跳到 owner 页面修复，不在本页直接编辑数据。\n"
            "4. 需要把近期 activity 整理成 evidence、next action 或草稿时，打开 Review。\n"
            "5. 修改证据、技能树、项目或公开层后，再回本页复查。\n\n"
            "Health 不写文件，只指出应由哪个页面负责修复。"
        ),
        "review_link": "打开 Review",
        "review_link_help": (
            "复盘候选在 Review 页面生成；Health 保持只读。"
        ),
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

_REVIEW: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Review · nblane",
        "title": "复盘",
        "page_context_line": (
            "Turn weekly or stage review inputs into evidence, next action, "
            "and public draft candidates."
        ),
        "page_help_short": "Guide",
        "review_help_body": (
            "### Review workflow\n\n"
            "1. Pick a time window and generate candidates from activity, Done tasks, learning, and inbox signals.\n"
            "2. In **Evidence candidates**, save selected rows to Activity for traceability or apply them into the evidence pool. Leave crystallization on when the source Done tasks are covered.\n"
            "3. In **Next action candidates**, save or apply only the queue items you want to carry forward.\n"
            "4. In **Public draft candidates**, create draft blog posts; this page never publishes them.\n"
            "5. Use **Method notes** and **Agent Activity** to audit how the candidates were derived.\n\n"
            "Review is a candidate generator. File writes are explicit and selected-row based."
        ),
        "preset": "Window",
        "preset_current_week": "Current week",
        "preset_previous_week": "Previous week",
        "preset_last_30_days": "Last 30 days",
        "preset_custom": "Custom",
        "start_date": "Start",
        "end_date": "End",
        "generate": "Generate candidates",
        "summary": "Summary",
        "done_tasks": "Done tasks",
        "activity": "Activity",
        "learning": "Learning",
        "inbox": "Inbox",
        "evidence_candidates": "Evidence candidates",
        "next_action_candidates": "Next action candidates",
        "public_draft_candidates": "Public draft candidates",
        "method_notes": "Method notes",
        "agent_activity": "Agent Activity",
        "save_to_activity": "Save selected to Activity",
        "apply_selected": "Apply selected",
        "create_public_drafts": "Create selected drafts",
        "mark_crystallized": "Mark source Done tasks crystallized",
        "no_candidates": "No candidates for this window.",
        "saved": "Saved to Activity.",
        "applied": "Applied.",
        "failed": "Failed",
        "select_rows": "Select rows",
        "candidate_preview": "Preview",
        "open_activity": "Open Agent Activity",
        "public_draft_note": "Creates draft blog posts only; it never publishes.",
    },
    "zh": {
        "page_title": "复盘 · nblane",
        "title": "复盘",
        "page_context_line": (
            "把周复盘或阶段复盘整理成证据、下一步行动和公开草稿候选。"
        ),
        "page_help_short": "使用说明",
        "review_help_body": (
            "### 复盘使用流程\n\n"
            "1. 选择时间窗口，从活动、已完成任务、学习记录和收件信号生成候选。\n"
            "2. 在 **证据候选** 中，可先保存到 Activity 留痕，也可把确认过的条目应用到证据池；来源 Done 已覆盖时保留 crystallized 标记。\n"
            "3. 在 **下一步行动候选** 中，只保存或应用你决定继续推进的队列项。\n"
            "4. 在 **公开草稿候选** 中创建博客草稿；本页不会发布内容。\n"
            "5. 用 **方法说明** 和 **Agent 活动** 审计候选来源和写入记录。\n\n"
            "复盘是候选生成器；所有文件写入都需要显式选择并应用。"
        ),
        "preset": "时间窗口",
        "preset_current_week": "本周",
        "preset_previous_week": "上周",
        "preset_last_30_days": "最近 30 天",
        "preset_custom": "自定义",
        "start_date": "开始",
        "end_date": "结束",
        "generate": "生成候选",
        "summary": "摘要",
        "done_tasks": "已完成任务",
        "activity": "活动",
        "learning": "学习",
        "inbox": "收件箱",
        "evidence_candidates": "证据候选",
        "next_action_candidates": "下一步行动候选",
        "public_draft_candidates": "公开草稿候选",
        "method_notes": "方法说明",
        "agent_activity": "Agent 活动",
        "save_to_activity": "保存所选到活动",
        "apply_selected": "应用所选",
        "create_public_drafts": "生成所选草稿",
        "mark_crystallized": "标记来源已完成任务为已结晶",
        "no_candidates": "这个时间窗口暂无候选。",
        "saved": "已保存到活动。",
        "applied": "已应用。",
        "failed": "失败",
        "select_rows": "选择行",
        "candidate_preview": "预览",
        "open_activity": "打开 Agent 活动",
        "public_draft_note": "只创建博客草稿，不会发布。",
    },
}

_AGENT_ACTIVITY: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Agent Activity · nblane",
        "title": "Agent Activity",
        "page_context_line": (
            "Review cross-page candidates, patches, writebacks, and failed "
            "apply attempts."
        ),
        "page_help_short": "Guide",
        "page_help_body": (
            "### Agent Activity workflow\n\n"
            "1. Treat this page as the audit queue for AI or agent-generated candidates across the app.\n"
            "2. Filter by status, module, kind, or candidate type to find pending and failed work.\n"
            "3. Apply only candidates whose owner page supports safe writeback; otherwise open the owner page and review there.\n"
            "4. Dismiss stale candidates instead of deleting them when you still need audit history.\n"
            "5. Use technical details for debugging failed agent/Codex runs, but use preview and refs for product decisions.\n\n"
            "Activity is the review ledger. It should make AI writes traceable, not invisible."
        ),
        "status": "Status",
        "kind": "Kind",
        "candidate_type": "Candidate type",
        "source_page": "Source page",
        "target_owner": "Target owner",
        "all": "All",
        "pending": "Pending",
        "applied": "Applied",
        "failed": "Failed",
        "dismissed": "Dismissed",
        "superseded": "Superseded",
        "items": "Items",
        "no_items": "No Activity items match the current filters.",
        "source_group": "Source",
        "module": "Module",
        "all_modules": "All modules",
        "advanced_filters": "Advanced filters",
        "sort": "Sort",
        "sort_updated_desc": "Newest first",
        "sort_updated_asc": "Oldest first",
        "sort_queue": "Pending first",
        "focused_item_notice": "Focused Activity item: {id}",
        "focused_item_highlight": "Opened from {source}.",
        "focused_item_missing": "The focused Activity item is not visible with the current filters.",
        "created": "Created",
        "updated": "Updated",
        "applied_at": "Applied",
        "error_summary": "Error",
        "technical_details": "Technical details",
        "manage_activity": "Manage Activity",
        "visible_items": "Visible items",
        "delete_item": "Delete item",
        "delete_item_confirm": "Confirm delete this item",
        "delete_visible": "Delete current view",
        "delete_visible_confirm": "Confirm delete all visible items",
        "delete_failed_dismissed": "Delete failed/dismissed in this module",
        "delete_failed_dismissed_confirm": "Confirm delete failed and dismissed items in this module",
        "deleted_items": "Deleted {count} Activity item(s).",
        "delete_none": "No matching Activity items to delete.",
        "payload": "Payload",
        "preview": "Preview",
        "refs": "Refs",
        "warnings": "Warnings",
        "changed_paths": "Changed paths",
        "agent_task_result": "Agent task result",
        "agent_harness_filter": "Harness result",
        "agent_harness_filter_all": "All",
        "agent_harness_filter_agent_tasks": "Agent tasks only",
        "agent_harness_filter_codex": "Codex",
        "agent_harness_filter_local_codex": "Local Codex",
        "agent_harness_filter_codex_cloud": "Codex Cloud",
        "agent_harness_filter_opencode": "OpenCode",
        "codex_cloud_title": "Codex Cloud",
        "codex_cloud_task": "Cloud task",
        "codex_cloud_refresh": "Refresh status",
        "codex_cloud_diff": "Pull diff candidate",
        "codex_cloud_refreshing": "Refreshing Codex Cloud...",
        "codex_cloud_diffing": "Pulling Codex Cloud diff...",
        "codex_cloud_refreshed": "Codex Cloud status refreshed.",
        "codex_cloud_diff_ready": "Codex Cloud diff is ready for review.",
        "apply": "Apply",
        "dismiss": "Dismiss",
        "reopen": "Reopen",
        "open_owner": "Open owner page",
        "saved": "Saved.",
        "applied_message": "Applied.",
        "apply_unavailable": "Only pending Review candidates can be applied here.",
    },
    "zh": {
        "page_title": "Agent 活动 · nblane",
        "title": "Agent 活动",
        "page_context_line": (
            "审查跨页面候选、补丁、写回结果和失败状态。"
        ),
        "page_help_short": "使用说明",
        "page_help_body": (
            "### Agent 活动使用流程\n\n"
            "1. 把这里当作全应用 AI / Agent 候选的审计队列。\n"
            "2. 通过状态、模块、类型和候选类型筛选待处理或失败项。\n"
            "3. 只有 owner 页面支持安全写回的候选才在这里应用；否则打开 owner 页面审阅。\n"
            "4. 仍需要留痕的过期候选请标记丢弃，不要直接删除。\n"
            "5. 技术详情用于排查失败的 Agent / Codex 调用；产品判断优先看预览和引用。\n\n"
            "Agent 活动是审阅账本，目标是让 AI 写入可追踪，而不是隐形发生。"
        ),
        "status": "状态",
        "kind": "类型",
        "candidate_type": "候选类型",
        "source_page": "来源页面",
        "target_owner": "目标归属",
        "all": "全部",
        "pending": "待审阅",
        "applied": "已应用",
        "failed": "失败",
        "dismissed": "已丢弃",
        "superseded": "已替代",
        "items": "条目",
        "no_items": "当前过滤条件下没有活动条目。",
        "source_group": "来源",
        "module": "模块",
        "all_modules": "全部模块",
        "advanced_filters": "高级筛选",
        "sort": "排序",
        "sort_updated_desc": "最新在前",
        "sort_updated_asc": "最早在前",
        "sort_queue": "队列优先",
        "focused_item_notice": "已定位活动条目：{id}",
        "focused_item_highlight": "从 {source} 跳转而来。",
        "focused_item_missing": "目标 Activity 条目在当前筛选条件下不可见。",
        "created": "创建",
        "updated": "更新",
        "applied_at": "应用",
        "error_summary": "错误",
        "technical_details": "技术详情",
        "manage_activity": "管理 Activity",
        "visible_items": "当前可见条目",
        "delete_item": "删除条目",
        "delete_item_confirm": "确认删除这个条目",
        "delete_visible": "删除当前视图",
        "delete_visible_confirm": "确认删除当前可见条目",
        "delete_failed_dismissed": "删除本模块失败/已丢弃条目",
        "delete_failed_dismissed_confirm": "确认删除本模块失败和已丢弃条目",
        "deleted_items": "已删除 {count} 条 Activity。",
        "delete_none": "没有匹配的 Activity 可删除。",
        "payload": "Payload",
        "preview": "预览",
        "refs": "Refs",
        "warnings": "警告",
        "changed_paths": "变更文件",
        "agent_task_result": "Agent task 结果",
        "agent_harness_filter": "Harness 结果",
        "agent_harness_filter_all": "全部",
        "agent_harness_filter_agent_tasks": "仅 Agent tasks",
        "agent_harness_filter_codex": "Codex",
        "agent_harness_filter_local_codex": "本地 Codex",
        "agent_harness_filter_codex_cloud": "Codex Cloud",
        "agent_harness_filter_opencode": "OpenCode",
        "codex_cloud_title": "Codex Cloud",
        "codex_cloud_task": "Cloud 任务",
        "codex_cloud_refresh": "刷新状态",
        "codex_cloud_diff": "拉取 diff 候选",
        "codex_cloud_refreshing": "正在刷新 Codex Cloud...",
        "codex_cloud_diffing": "正在拉取 Codex Cloud diff...",
        "codex_cloud_refreshed": "Codex Cloud 状态已刷新。",
        "codex_cloud_diff_ready": "Codex Cloud diff 已进入审阅。",
        "apply": "应用",
        "dismiss": "丢弃",
        "reopen": "重新打开",
        "open_owner": "打开 owner 页面",
        "saved": "已保存。",
        "applied_message": "已应用。",
        "apply_unavailable": "这里只能应用 pending 的 Review 候选。",
    },
}

_RESEARCH: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Research · nblane",
        "title": "Research Workspace",
        "page_context_line": (
            "Capture sources, read them into claims/citations, then promote only reviewed candidates."
        ),
        "page_help_short": "Guide",
        "source_inbox": "Source Inbox",
        "reading_room": "Reading Room",
        "claims_citations": "Claims & Citations",
        "synthesis_drafts": "Synthesis Drafts",
        "connectors": "Connectors",
        "inbox_connectors": "Inbox & Connectors",
        "ai_config": "Research AI Config",
        "ai_config_short": "Research AI",
        "ai_config_caption": (
            "These settings only affect Research AI actions for the active profile: paper search, translation, Reader, and DeepRead. Other pages keep their own page-level AI preferences."
        ),
        "ai_config_translation_model": "Current-page translation model",
        "ai_config_deep_read_model": "DeepRead model",
        "ai_config_use_default": "Use app default",
        "ai_config_custom_model": "Custom model",
        "ai_config_overrides_default": "overrides default",
        "ai_config_saved": "AI preferences saved.",
        "research_help_body": (
            "### Research workflow\n\n"
            "1. **Overview**: start with the action queue for reading, extraction, citation, privacy, and synthesis blockers.\n"
            "2. **Paper Library**: import papers, attach PDFs, open Reader, run extraction, translate, annotate, and create paper claims.\n"
            "3. **Claims & Citations**: review research claims and citations before promoting anything to evidence or output.\n"
            "4. **Synthesis / Export**: assemble reviewed claims into draft exports, blog candidates, or project updates.\n"
            "5. **Inbox & Connectors**: capture manual sources, preview evidence candidates, and configure connector discovery. Connector configs do not store secrets.\n\n"
            "Research claims are source-aware working claims. Promotion to Evidence Review or public output remains candidate-first."
        ),
        "workspace_overview": "Workspace overview",
        "sources_total": "Sources",
        "sources_private": "Private",
        "sources_public": "Public",
        "ready_claims": "Ready claims",
        "drafts_total": "Drafts",
        "connectors_enabled": "Enabled connectors",
        "research_primary_actions": "Research actions",
        "action_add_source": "Add source",
        "action_open_reading": "Open reading queue",
        "action_create_synthesis": "Create synthesis",
        "reading_flow_hint": "Read source -> cut chunk -> write claim -> bind citation -> promote candidate.",
        "claim_boundary_hint": (
            "Research claims are not accepted evidence claims. Promotion to evidence or output always stays candidate-first."
        ),
        "research_workspace": "Research Workspace",
        "research_command_center": "Research Command Center",
        "research_command_center_caption": "Sources, reading state, review queues, and export safety in one workspace.",
        "research_sidecar_disabled": "Paper Library sidecar links are disabled; Reader and 8502 workspace buttons will use relative URLs.",
        "research_sidecar_unavailable": "8502 Paper Library sidecar is not reachable; Reader and Paper Library links are temporarily disabled for {base}.",
        "research_sidecar_connected": "Paper Library sidecar: {origin} · {base}",
        "paper_library_sidecar_link_disabled_help": "Start or forward the 8502 Paper Library sidecar to use this link.",
        "reader_sidecar_unavailable_fallback": "PDF Reader is temporarily unavailable because the 8502 sidecar cannot be reached. Showing text-mode Reader fallback.",
        "configured": "configured",
        "auto_detected": "auto-detected",
        "private_public_sources": "Private / public",
        "citation_broken": "Citation broken",
        "private_publish_risk": "Private publish risk",
        "stale_translation_warning": "Stale translations",
        "research_sources": "Sources",
        "papers_reading": "Reading",
        "reader": "Reader",
        "extracted": "Extracted",
        "chunks_annotations": "Chunks / annotations",
        "claims_ready": "Claims ready",
        "review_queue": "Review queue",
        "warnings_count": "{count} warnings",
        "synthesis_export": "Synthesis / Export",
        "integrity_publish_safety": "Integrity & Publish Safety",
        "work_queues": "Work queues",
        "paper_library": "Paper Library",
        "reading": "Reading",
        "continue": "Continue",
        "needs_extraction": "Needs extraction",
        "parser_status": "Parser status",
        "pdf_missing": "PDF missing",
        "claims_need_review": "Claims review",
        "ai_candidates": "AI candidates",
        "ready_research_claims": "Ready claims",
        "promote_to_evidence": "Promote to evidence",
        "quote_warnings": "Quote warnings",
        "citation_inspector": "Citation inspector",
        "private_sources": "Private sources",
        "recent_papers": "Recent",
        "duplicate_risk": "Duplicate risk",
        "metadata_review": "Metadata review",
        "open_reader": "Open Reader",
        "open_in_paper_library": "Open in Library",
        "open_source_library": "Open source",
        "open_paper_library_workspace": "Open Paper Library",
        "focus_ready_claims": "Focus ready claims",
        "focus_quote_warnings": "Focus quote warnings",
        "focus_export_gate": "Focus export gate",
        "focus_connector_inbox": "Connector inbox",
        "focus_claims": "Claims",
        "claims_focus_saved": "Claims review focus updated.",
        "citations_focus_saved": "Citation inspector is focused on quote warnings.",
        "export_focus_saved": "Export gate focus updated.",
        "connector_focus_saved": "Connector inbox focus updated.",
        "next_actions": "Next actions",
        "next_action": "Next action",
        "no_research_actions": "No research actions need attention.",
        "discovery_updates": "Discovery updates",
        "overview_imported_count": "{count} imported",
        "overview_skipped_count": "{count} skipped",
        "connector_status_idle": "idle",
        "connector_status_enabled": "enabled",
        "connector_status_disabled": "disabled",
        "connector_status_error": "error",
        "connector_status_failed": "failed",
        "connector_status_ok": "ok",
        "recent_work": "Recent work",
        "chunks": "Chunks",
        "recent_work_empty": "No recent paper reading yet.",
        "ready_to_review": "Ready to review",
        "review_claim": "Review claim",
        "more_claims_hidden": "{count} more claim(s) hidden by this compact view.",
        "claims_empty_next_step": "Run extraction in Paper Library, then create claim candidates from the Reader.",
        "prepare_claim_candidates": "Prepare claim candidates",
        "risk_queue": "Risk queue",
        "risk_queue_empty": "No publish blockers in the current research queue.",
        "overview_queue_continue_reading": "Continue reading",
        "overview_queue_run_extraction": "Run extraction",
        "overview_queue_attach_pdf": "Attach PDF",
        "overview_queue_review_candidates": "Review candidates",
        "overview_queue_deduplicate": "Deduplicate",
        "overview_queue_refresh_translations": "Refresh translations",
        "overview_queue_review_visibility": "Review visibility",
        "overview_queue_open_recent": "Open recent",
        "overview_action_continue_reading": "Continue reading {count} source(s)",
        "overview_action_review_claims": "Review {count} ready research claim(s)",
        "overview_action_fix_citations": "Fix {count} citation warning(s)",
        "overview_action_private_risk": "Review {count} private source risk(s)",
        "overview_action_review_drafts": "Review {count} synthesis draft(s)",
        "overview_action_import_sources": "Import papers, repos, or web sources",
        "risk_private_publish": "Private publish risk",
        "risk_broken_citations": "Broken citations",
        "risk_open_export_gate": "Open export gate",
        "risk_open_citation_inspector": "Open citation inspector",
        "badge_unsorted": "Unsorted",
        "badge_pdf_ready": "PDF ready",
        "badge_stale_translation": "Stale translation",
        "badge_private_source": "Private source",
        "badge_needs_structured_extraction": "Needs structured extraction",
        "badge_grobid_unavailable": "GROBID unavailable",
        "badge_fallback_extraction": "Fallback extraction",
        "ready": "Ready",
        "risk": "Risk",
        "reading_mode": "Mode",
        "excerpt": "Excerpt",
        "translation": "Translation",
        "key_points": "Key points",
        "claim_candidates": "Claim candidates",
        "citations": "Citations",
        "synthesis_notes": "Synthesis notes",
        "create_chunk": "Create chunk",
        "chunk_kind": "Chunk kind",
        "chunk_title": "Chunk title",
        "chunk_locator": "Locator",
        "chunk_text": "Chunk text",
        "chunk_refs": "Chunk refs",
        "chunks_empty": "No chunks for this source yet.",
        "create_research_claim": "Create research claim",
        "research_claim_id": "Research claim id",
        "research_claim_type": "Claim type",
        "research_claim_status": "Claim status",
        "research_claim_text": "Claim text",
        "research_claims": "Research claims",
        "claims_empty": "No research claims yet.",
        "human_note": "Human note without source/chunk",
        "rationale": "Rationale",
        "create_citation": "Create citation",
        "citation_quote": "Quote",
        "bibliography": "Bibliography",
        "research_citations": "Research citations",
        "citations_empty": "No citations yet.",
        "create_synthesis_draft": "Create synthesis draft",
        "synthesis_draft_id": "Synthesis draft id",
        "drafts_empty": "No synthesis drafts yet.",
        "blog_candidate_preview": "Blog candidate preview",
        "create_blog_draft": "Create blog draft",
        "body": "Body",
        "connectors_caption": "Connector configs do not store tokens, cookies, or API keys.",
        "connectors_empty": "No connectors configured yet.",
        "configure_connector": "Configure connector",
        "connector_provider": "Provider",
        "connector_id": "Connector id",
        "connector_query": "Query / subscription",
        "connector_enabled": "Enabled",
        "privacy_default": "Default visibility",
        "connector_options": "Options YAML",
        "connector_dry_run": "Dry run",
        "connector_run_now": "Run now",
        "generate_reading_draft": "Generate reading draft",
        "save_reading_annotations": "Save reading annotations",
        "create_evidence_candidate": "Create evidence candidate",
        "evidence_candidate_preview": "Evidence candidate preview",
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
        "title": "研究工作台",
        "page_context_line": "外部资料先沉淀为 source-aware claim / citation；审阅后再进入 evidence 或公开输出。",
        "page_help_short": "使用说明",
        "source_inbox": "来源收件箱",
        "reading_room": "阅读室",
        "claims_citations": "断言与引用",
        "synthesis_drafts": "综合草稿",
        "connectors": "连接器",
        "inbox_connectors": "收件箱与连接器",
        "ai_config": "Research AI 配置",
        "ai_config_short": "研究 AI",
        "ai_config_caption": "这些设置只影响当前 profile 的 Research AI 动作：论文搜索、翻译、Reader 和 DeepRead。其他页面保留自己的页面级 AI 设置。",
        "ai_config_translation_model": "当前页翻译模型",
        "ai_config_deep_read_model": "DeepRead 模型",
        "ai_config_use_default": "使用应用默认模型",
        "ai_config_custom_model": "自定义模型",
        "ai_config_overrides_default": "覆盖默认",
        "ai_config_saved": "AI 配置已保存。",
        "research_help_body": (
            "### Research 使用流程\n\n"
            "1. **概览**：先看行动队列，处理阅读、解析、引用、隐私和综合导出的阻塞项。\n"
            "2. **论文库**：导入论文、补 PDF、打开 Reader、运行解析、翻译、标注，并生成论文 claim。\n"
            "3. **断言与引用**：先审阅 research claims 和 citations，再推进到 evidence 或输出。\n"
            "4. **综合 / 导出**：把已审阅 claims 组织成综合草稿、博客候选或项目更新。\n"
            "5. **收件箱与连接器**：手动捕捉 sources、预览 evidence 候选、配置连接器发现；连接器配置不保存 token、cookie 或 API key。\n\n"
            "Research claim 是带来源的工作断言；进入 Evidence Review 或公开输出前仍然必须走候选和人工确认。"
        ),
        "workspace_overview": "工作台概览",
        "sources_total": "来源 Sources",
        "sources_private": "私有 Private",
        "sources_public": "公开 Public",
        "ready_claims": "待审断言",
        "drafts_total": "草稿",
        "connectors_enabled": "已启用连接器",
        "research_primary_actions": "研究动作",
        "action_add_source": "新增来源",
        "action_open_reading": "打开待读队列",
        "action_create_synthesis": "生成 synthesis",
        "reading_flow_hint": "读 source -> 切 chunk -> 写 claim -> 绑定 citation -> 推进候选。",
        "claim_boundary_hint": (
            "Research claim 不是 accepted evidence claim；进入 evidence 或公开输出前必须先走候选/人工确认。"
        ),
        "research_workspace": "研究工作台",
        "research_command_center": "研究中控台",
        "research_command_center_caption": "把来源、阅读状态、审阅队列和发布安全放在同一个工作区。",
        "research_sidecar_disabled": "Paper Library sidecar 链接已关闭；Reader 和 8502 工作区按钮会使用相对 URL。",
        "research_sidecar_unavailable": "8502 Paper Library sidecar 当前不可达；Reader 和 Paper Library 链接已暂时禁用：{base}。",
        "research_sidecar_connected": "Paper Library sidecar：{origin} · {base}",
        "paper_library_sidecar_link_disabled_help": "请先启动或转发 8502 Paper Library sidecar，再使用这个链接。",
        "reader_sidecar_unavailable_fallback": "8502 sidecar 暂时不可达，PDF Reader 无法打开；下面显示 text-mode Reader fallback。",
        "configured": "已配置",
        "auto_detected": "自动检测",
        "private_public_sources": "私有 / 公开",
        "citation_broken": "引用断裂",
        "private_publish_risk": "私有发布风险",
        "stale_translation_warning": "过期翻译",
        "research_sources": "来源",
        "papers_reading": "阅读中",
        "reader": "阅读器",
        "extracted": "已提取",
        "chunks_annotations": "片段 / 标注",
        "claims_ready": "断言待审",
        "review_queue": "审阅队列",
        "warnings_count": "{count} 个警告",
        "synthesis_export": "综合 / 导出",
        "integrity_publish_safety": "完整性与发布安全",
        "work_queues": "工作队列",
        "paper_library": "论文库",
        "reading": "阅读中",
        "continue": "继续",
        "needs_extraction": "需要解析",
        "parser_status": "解析状态",
        "pdf_missing": "缺少 PDF",
        "claims_need_review": "断言审阅",
        "ai_candidates": "AI 候选",
        "ready_research_claims": "待审断言",
        "promote_to_evidence": "推进到证据",
        "quote_warnings": "引用警告",
        "citation_inspector": "引用检查器",
        "private_sources": "私有来源",
        "recent_papers": "最近阅读",
        "duplicate_risk": "重复风险",
        "metadata_review": "元数据审阅",
        "open_reader": "打开阅读器",
        "open_in_paper_library": "打开论文库",
        "open_source_library": "打开来源",
        "open_paper_library_workspace": "打开论文库",
        "focus_ready_claims": "聚焦待审断言",
        "focus_quote_warnings": "聚焦引用警告",
        "focus_export_gate": "聚焦导出门禁",
        "focus_connector_inbox": "连接器收件箱",
        "focus_claims": "断言",
        "claims_focus_saved": "已更新断言审阅焦点。",
        "citations_focus_saved": "引用检查器已聚焦到引用警告。",
        "export_focus_saved": "已更新导出门禁焦点。",
        "connector_focus_saved": "已更新连接器收件箱焦点。",
        "next_actions": "下一步动作",
        "next_action": "下一步动作",
        "no_research_actions": "当前没有需要处理的研究动作。",
        "discovery_updates": "发现更新",
        "overview_imported_count": "已导入 {count}",
        "overview_skipped_count": "已跳过 {count}",
        "connector_status_idle": "空闲",
        "connector_status_enabled": "已启用",
        "connector_status_disabled": "已停用",
        "connector_status_error": "出错",
        "connector_status_failed": "失败",
        "connector_status_ok": "正常",
        "recent_work": "最近工作",
        "chunks": "片段",
        "recent_work_empty": "还没有最近阅读记录。",
        "ready_to_review": "待审阅",
        "review_claim": "审阅断言",
        "more_claims_hidden": "还有 {count} 条断言未在此紧凑视图中显示。",
        "claims_empty_next_step": "先在论文库中运行解析，再从阅读器生成断言候选。",
        "prepare_claim_candidates": "准备断言候选",
        "risk_queue": "风险队列",
        "risk_queue_empty": "当前研究队列没有发布阻塞项。",
        "overview_queue_continue_reading": "继续阅读",
        "overview_queue_run_extraction": "运行解析",
        "overview_queue_attach_pdf": "补 PDF",
        "overview_queue_review_candidates": "审阅候选",
        "overview_queue_deduplicate": "去重",
        "overview_queue_refresh_translations": "刷新翻译",
        "overview_queue_review_visibility": "检查可见性",
        "overview_queue_open_recent": "打开最近项",
        "overview_action_continue_reading": "继续阅读 {count} 个来源",
        "overview_action_review_claims": "审阅 {count} 条待审研究断言",
        "overview_action_fix_citations": "修复 {count} 个引用警告",
        "overview_action_private_risk": "检查 {count} 个私有来源风险",
        "overview_action_review_drafts": "审阅 {count} 份综合草稿",
        "overview_action_import_sources": "导入论文、代码仓库或网页来源",
        "risk_private_publish": "私有发布风险",
        "risk_broken_citations": "断裂引用",
        "risk_open_export_gate": "打开导出门禁",
        "risk_open_citation_inspector": "打开引用检查器",
        "badge_unsorted": "未分类",
        "badge_pdf_ready": "PDF 就绪",
        "badge_stale_translation": "翻译过期",
        "badge_private_source": "私有来源",
        "badge_needs_structured_extraction": "需要结构化解析",
        "badge_grobid_unavailable": "GROBID 不可用",
        "badge_fallback_extraction": "备用解析",
        "ready": "就绪",
        "risk": "风险",
        "reading_mode": "模式",
        "excerpt": "摘录",
        "translation": "翻译",
        "key_points": "要点",
        "claim_candidates": "断言候选",
        "citations": "引用",
        "synthesis_notes": "综合笔记",
        "create_chunk": "创建 chunk",
        "chunk_kind": "Chunk 类型",
        "chunk_title": "Chunk 标题",
        "chunk_locator": "定位",
        "chunk_text": "Chunk 文本",
        "chunk_refs": "Chunk refs",
        "chunks_empty": "这个来源还没有 chunk。",
        "create_research_claim": "创建研究断言",
        "research_claim_id": "研究断言 id",
        "research_claim_type": "断言类型",
        "research_claim_status": "断言状态",
        "research_claim_text": "断言文本",
        "research_claims": "研究断言",
        "claims_empty": "暂无研究断言。",
        "human_note": "无 source/chunk 的人工备注",
        "rationale": "理由",
        "create_citation": "创建引用",
        "citation_quote": "引用摘录",
        "bibliography": "Bibliography",
        "research_citations": "研究引用",
        "citations_empty": "暂无引用。",
        "create_synthesis_draft": "创建综合草稿",
        "synthesis_draft_id": "综合草稿 id",
        "drafts_empty": "暂无综合草稿。",
        "blog_candidate_preview": "博客候选预览",
        "create_blog_draft": "创建博客草稿",
        "body": "正文",
        "connectors_caption": (
            "连接器负责把外部 URL、CSV 或订阅结果导入研究收件箱；"
            "配置不保存 token、cookie 或 API key。导入后的论文再进入 Reader。"
        ),
        "connectors_empty": "暂无连接器配置。",
        "configure_connector": "配置连接器",
        "connector_provider": "来源类型",
        "connector_id": "连接器 id",
        "connector_query": "查询 / 订阅",
        "connector_enabled": "启用",
        "privacy_default": "默认可见性",
        "connector_options": "选项 YAML",
        "connector_dry_run": "预演",
        "connector_run_now": "立即同步",
        "generate_reading_draft": "生成阅读草稿",
        "save_reading_annotations": "保存阅读标注",
        "create_evidence_candidate": "生成证据候选",
        "evidence_candidate_preview": "证据候选预览",
        "add_source": "新增来源",
        "edit_source": "编辑来源",
        "source_queue": "来源队列",
        "candidate_preview": "证据候选预览",
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
        "status_inbox": "收件箱",
        "status_reading": "阅读中",
        "status_summarized": "已总结",
        "status_candidate_ready": "候选待审",
        "status_archived": "已归档",
        "status_discarded": "已丢弃",
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


def review_ui() -> dict[str, str]:
    """Review page."""
    lg = _lang()
    merged = dict(_COMMON.get(lg, _COMMON["en"]))
    merged.update(_REVIEW.get(lg, _REVIEW["en"]))
    return merged


def agent_activity_ui() -> dict[str, str]:
    """Agent Activity page."""
    lg = _lang()
    merged = dict(_COMMON.get(lg, _COMMON["en"]))
    merged.update(_AGENT_ACTIVITY.get(lg, _AGENT_ACTIVITY["en"]))
    return merged


def project_board_ui() -> dict[str, str]:
    """Project Board page."""
    lg = _lang()
    merged = dict(_COMMON.get(lg, _COMMON["en"]))
    merged.update(_PROJECT_BOARD.get(lg, _PROJECT_BOARD["en"]))
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
