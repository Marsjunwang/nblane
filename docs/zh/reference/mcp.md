---
status: active
owner: engineering
last_verified: 2026-10-08
source_of_truth: true
---

# MCP 服务器

> 本机 MCP 只给同一台机器上的 Cursor、Claude Code 这类可信客户端用。它不登录，也没有档案 ACL，目前暂停扩展。OpenClaw 助手不用 MCP，读写都走 HTTP，见 [助手](../guides/assistant.md)。

入口：`nblane-mcp`（等价 `python -m nblane.mcp_server`），走 stdio，由客户端拉起子进程。实现以 `src/nblane/mcp_server.py` 为准。

## 资源（只读）

| URI | 返回 |
|-----|------|
| `profile://summary` | 技能树摘要、agent-profile 焦点与偏好、Doing 任务（Markdown） |
| `profile://context` | 完整 system prompt，对齐 `nblane context`，固定带看板；模式由 `NBLANE_CONTEXT_MODE` 决定 |
| `profile://kanban` | `kanban.md` 原文 |
| `profile://goals` | 目标状态计数、主目标与活跃目标、北极星；private 目标不出现 |
| `profile://evidence` | 证据池按审阅状态计数 + 最近 20 条 |
| `profile://learning` | 学习记录计数、在读资源、最近 10 条 |
| `agent://tasks` | 外部 agent 任务列表（`agent-tasks.yaml`） |
| `agent://task/{task_id}` | 单个任务的 handoff、输入 refs、预期产物 |

## 工具

写工具和 HTTP 共用同一套策略（`core/agent_policy.py` 分级 + `core/agent_ops.py` 流程），规则见 [助手 · 三类写入](../guides/assistant.md#三类写入)。

| 工具 | 级别 | 行为 |
|------|------|------|
| `add_kanban_card` | 直写 | 加一张卡（`title`、`section` 默认 Queue、`context`、`tags`、`planned_start`、`planned_end`）。返回 `card_id`、`journal_id` |
| `move_kanban_card` | 直写 | 按 id / 精确标题 / 唯一子串移动到 `target_section`，进出 Done 自动处理完成日期 |
| `delete_kanban_card` | 确认 | 第一次返回 `confirmation_required` + `summary` + `confirm_id`；用户同意后用相同参数带 `confirm_id` 重调才删除 |
| `add_checkin` | 直写 | 打卡一次（`habit` id 或标题、`date`、`count`、`unit`、`summary`、`note`、`tags`） |
| `append_growth_log` | 直写 | 向 SKILL.md Growth Log 追加一行 |
| `crystallize_method_draft` | 直写 | 写方法草稿到 `methods/` |
| `log_skill_evidence` | 确认 | 给技能节点加一条内联证据；需要确认时返回以 `CONFIRM REQUIRED:` 开头的一行 |
| `log_interaction` | 记录 | 追加交互记录到 `interactions/*.jsonl`，不进撤销日志 |
| `suggest_skill_upgrade` | 只读 | 只返回文本建议，不写文件 |
| `submit_agent_task_candidate` | 记录 | 外部 agent 回传任务结果（`summary`、`changed_paths`、`warnings`、`result_payload`），任务变为 `candidate_ready` |
| `update_agent_task_status` | 记录 | 更新外部 agent 任务状态 |
| `recent_actions` | 只读 | 撤销日志最新条目（`limit` 默认 10，上限 50），HTTP 和 MCP 的写入都在里面 |
| `undo_action` | — | 按 `journal_id` 撤销；之后有人改过同一内容时拒绝（`journal_undo_conflict`） |
| `run_validate` | 只读 | 对当前档案跑 validate，返回 errors / warnings |
| `run_sync_check` | 只读 | 返回 SKILL.md 漂移的生成块名，不写文件 |

- 确认码 10 分钟有效、一次性、绑定参数，存在 `~/.local/share/nblane/agent/mcp-confirmations.json`（`NBLANE_AGENT_STATE_DIR` 可改），多个 MCP 进程共享。
- 撤销日志里的操作人是 `NBLANE_MCP_ACTOR`（默认 `mcp`）。
- 结构化工具返回 dict（带 `ToolAnnotations`）；旧版字符串工具（`append_growth_log`、`log_skill_evidence`、`log_interaction`、`suggest_skill_upgrade`、`crystallize_method_draft`、外部 agent 任务两个）返回 `OK:` / `ERROR:` 开头的文本。

摄入简历、完整证据编辑、`sync --write`、看板正文编辑等不经 MCP，用 CLI 或 SPA。

## 档案选定

1. 设置了 `NBLANE_PROFILE` 或 `NBLANE_MCP_PROFILE` 且目录存在，用它。
2. 否则 `profiles/` 下恰好一个非 template 档案时自动用它。
3. 否则读资源报 `ERROR [profile://…]`，提示设置 `NBLANE_PROFILE`。

## 环境变量

| 变量 | 作用 |
|------|------|
| `NBLANE_PROFILE` / `NBLANE_MCP_PROFILE` | 默认档案；有多个档案时必须设置 |
| `NBLANE_ROOT` | 数据根（含 `profiles/`、`schemas/`）。工作区不是 nblane 仓库时建议显式设置 |
| `NBLANE_CONTEXT_MODE` | `chat` / `review` / `write` / `plan`，只影响 `profile://context`，默认 `chat` |
| `NBLANE_MCP_ACTOR` | 撤销日志和确认码里的操作人，默认 `mcp` |
| `NBLANE_AGENT_STATE_DIR` | 确认码存放目录 |

## 接入 Cursor / Claude Code

先在 nblane 仓库里 `.venv/bin/pip install -e .`。

当前工作区就是 nblane 仓库时，仓库自带 `.cursor/mcp.json`（`command` 为 `${workspaceFolder}/.venv/bin/python`）。需要时加 `env.NBLANE_PROFILE`。

在别的工作区也要用时，配用户级 MCP，路径全部写绝对路径：

```json
{
  "mcpServers": {
    "nblane": {
      "command": "/path/to/nblane/.venv/bin/python",
      "args": ["-m", "nblane.mcp_server"],
      "env": {
        "NBLANE_PROFILE": "<profile>",
        "NBLANE_ROOT": "/path/to/nblane"
      }
    }
  }
}
```

SPA「设置 → 助手与备份」底部也给出本机的 MCP 配置片段。项目级和用户级只保留一处，或改名（如 `nblane-global`），避免重复注册。

自检：客户端里能看到 `profile://summary`、`profile://context`，读取 `profile://context` 应出现基于 SKILL.md 的 system prompt。

## 另见

- [AI 架构](../architecture/ai-architecture.md)
- [Agent Harness](agent-harness.md)
