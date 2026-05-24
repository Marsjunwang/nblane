---
status: active
owner: engineering
last_verified: 2026-05-15
source_of_truth: true
---

# Agent Harness 集成

nblane 不把 Codex/OpenCode 内嵌为业务库。它们有两类使用边界：在 Kanban
里，Codex 只作为可选只读 AI backend，替代原有看板 LLM 动作；在 CLI /
MCP handoff 里，Codex/OpenCode 才是外部高级执行器。

## 原则

```text
nblane = 长期数据、上下文、项目、研究、证据、公开层
Kanban 内 Codex = 可选只读 AI backend，替代看板原有 LLM 动作
Codex/OpenCode handoff = 多步执行、代码修改、测试、复杂 agent loop
MCP = 二者之间的上下文和工具协议
```

不推荐：

- 把 OpenCode 当成 `llm.chat()` 替代品。
- 让每个 UI 按钮都启动可改项目的 harness。
- 依赖 harness 内部 API。
- 让外部 agent 直接绕过 nblane 校验写 profile 文件。

推荐：

- UI 内短任务走 AI Gateway；Kanban 中的 Codex 只替代原有草稿生成动作。
- 复杂任务通过 MCP 交给 Codex/OpenCode。
- Harness 写回走 draft-first MCP tools。

## 角色

规划生成这些 agent role prompts：

| 角色 | 作用 |
|------|------|
| `researcher` | 读取 research sources，抽取 claim、open question、source gap |
| `synthesizer` | 从 sources/claims 生成 synthesis outline/draft |
| `reviewer` | 检查 privacy、unsupported claim、格式、发布风险 |
| `project_planner` | 从 roadmap/status/issues 拆任务和 milestone |
| `curator` | 将 evidence/blog/project/output 关联到公开层 |

## 配置生成

已实现 MVP 命令：

```bash
nblane sync-agent-harness --target codex
nblane sync-agent-harness --target opencode
nblane codex status
nblane codex install --print-command
```

默认打印配置片段；也可以通过 `--out <path>` 写入文件。生成内容：

- Codex `AGENTS.md` 或配置片段。
- OpenCode agents/subagents markdown。
- MCP server 配置片段。
- nblane role prompts。
- 写回规则：draft-first、通过 MCP tools、公开发布需人工确认。

## Agent Task Handoff

已实现 profile-scoped 任务文件：

```text
profiles/<name>/agent-tasks.yaml
```

示例：

```yaml
tasks:
  - id: agenttask_001
    harness: opencode
    role: researcher
    title: "分析 VLA 论文资料并生成 synthesis draft"
    input_refs:
      - research:src_rt2
      - research:src_openvla
    expected_outputs:
      - claims
      - synthesis_draft
    status: ready
    activity_item_id: act:ai:airun_001
```

交接命令：

```bash
nblane agent handoff agenttask_001 --target opencode --profile <name>
```

`--profile` 省略时会扫描现有 profiles 寻找任务 id。基础 handoff 仍然只生成
可复制给 Codex/OpenCode 的信息，不直接启动外部 runtime。

本机已安装 Codex CLI 时，可以让 nblane 在隔离 git worktree 中调用本地
`codex exec`，并把 diff 作为 Agent Activity 候选写回：

```bash
nblane codex local run agenttask_001 --profile <name>
```

这个本地 runner 是 CLI / agent task 能力，不出现在 Kanban 页面。Kanban
不会从卡片创建 patch handoff，也不会提供 “用本地 Codex 运行” 或 “提交到
Codex Cloud” 按钮。本地 runner 不直接修改主工作树；如果主工作树有未提交
改动，runner 会记录提示，说明它基于 clean `HEAD` worktree 执行。

如果配置了 `NBLANE_CODEX_CLOUD_ENV_ID`，可以把 Codex handoff 交给 Codex
Cloud：

```bash
nblane codex status --profile <name>
nblane codex cloud submit agenttask_001 --profile <name>
nblane codex cloud refresh agenttask_001 --profile <name>
nblane codex cloud refresh agenttask_001 --profile <name> --diff
```

`--diff` 会把 Codex Cloud diff 作为 candidate 写回 `agent-tasks.yaml` 和
Agent Activity；nblane 不会调用 `codex cloud apply`，不会自动修改本地工作树。

每个 profile 可用 `profiles/<name>/codex.yaml` 保存自己的 Codex Cloud env、
branch、attempts 和 model override。Web 中的侧边栏 **AI / LLM** 提供
**配置 Codex** 大弹窗，可编辑部署级 / 终端同款 Web Codex home 下的
`config.toml`，也可打开并编辑当前 profile 的 `codex.yaml`；profile 配置文件不保存
token 或 API key。API key/auth 由 Codex CLI 管理，Web 只通过
`codex login --with-api-key` 写入部署级 `auth.json`。云上建议用
`NBLANE_CODEX_HOME` 指向持久化 service-level Codex home。

Kanban 页面不再提供单独的 Codex 配置或 handoff 面板；侧边栏 **AI / LLM**
中的 **看板 AI 引擎** 选择器控制看板使用普通 LLM 还是 Codex。选择 `Codex`
时，原有看板 AI 动作会调用只读
`codex exec`：

- 输入：当前看板任务、profile prior、相关 evidence / skill / archive、当前 goal。
- 输出：Gap 节点路由、任务理解选项、`subtasks`，以及 Done -> evidence 所需的结构化 JSON。
- 写入：不会创建 `agent-tasks.yaml`，不会写 patch candidate，不会修改项目文件。
- 人工动作：用户可选择把返回的子任务草稿应用到当前卡片；Done -> evidence
  仍进入现有预览 / 审阅流程。

外部 agent handoff 仍可通过 CLI / MCP 创建。外部 agent 完成后必须通过 MCP
`submit_agent_task_candidate` 回传摘要、`changed_paths`、warnings 和 result
payload；结果保持在 Activity patch 候选态。

Codex Cloud 任务会在 agent task 上保存 `remote` metadata：

```yaml
remote:
  provider: codex_cloud
  cloud_task_id: task_xxx
  env_id: env_xxx
  branch: main
  attempts: 1
  submitted_at: "2026-05-17T00:00:00+00:00"
  status_raw: "..."
  diff: "..."
```

## 与 MCP 的关系

Harness 通过 MCP 读写：

```text
Resources:
  profile://context
  profile://kanban
  agent://tasks
  agent://task/{task_id}
  workspace://graph
  research://sources
  project://status
  blog://drafts

Tools:
  submit_agent_task_candidate
  update_agent_task_status
  create_kanban_task
  capture_research_source
  create_claim
  create_synthesis_draft
  export_synthesis_to_blog_draft
  log_task_evidence
```

MCP 是第一阶段核心协议。ACP 暂不作为核心依赖，除非 nblane 未来需要自建 agent client 或 agent-agent runtime。
