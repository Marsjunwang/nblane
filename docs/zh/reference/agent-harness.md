---
status: active
owner: engineering
last_verified: 2026-10-07
source_of_truth: true
---

# Agent Harness 集成

nblane 不内嵌 Codex / OpenCode。它们有两种用法：

- 只读 AI backend：在「设置 → AI 路由」里给某个工作流动作（任务对齐、子任务拆分、证据结晶等）选 Codex，调用只读 `codex exec`，不改项目文件。见 [本机安装 · AI 配置](../guides/setup.md#ai-配置)。
- 外部执行器：多步、可改代码的任务通过 CLI handoff 交给 Codex / OpenCode，结果作为候选写回任务文件，由人审阅后自己合并。

```text
nblane = 长期数据、上下文、项目、研究、证据、公开层
工作流里的 Codex = 可选只读 backend
Codex / OpenCode handoff = 多步执行、代码修改、测试
```

不做：把 harness 当 `llm.chat()` 替代品；让页面按钮启动能改项目的 harness；依赖 harness 内部 API；让外部 agent 绕过 nblane 校验直接写档案文件。

助手（OpenClaw）不在本文范围，见 [助手](../guides/assistant.md)。

## 任务文件

外部 agent 任务存在 `profiles/<name>/agent-tasks.yaml`：

```yaml
tasks:
  - id: agenttask_001
    harness: codex            # codex | opencode
    role: researcher          # researcher | resume_strategist | remote_dev | reviewer
    title: "分析 VLA 论文资料并生成 synthesis draft"
    input_refs:
      - research:src_rt2
    expected_outputs:
      - synthesis_draft
    status: ready
```

状态：`draft`、`ready`、`handed_off`、`running`、`candidate_ready`、`applied`、`failed`、`cancelled`。实现见 `core/agent_tasks.py`。

## 配置片段

```bash
nblane sync-agent-harness --target codex|opencode [--out PATH]
```

打印 Codex `AGENTS.md` 或 OpenCode agent 配置片段：角色提示词、handoff 命令、可读的 MCP 资源（`profile://context`、`profile://kanban`、`agent://tasks`、`agent://task/{task_id}`）、回传工具（`submit_agent_task_candidate`、`update_agent_task_status`）和权限约定（不发布、不删档案事实）。

## Handoff

```bash
nblane agent handoff <task_id> --target codex|opencode [--profile <name>]
```

只生成可复制给外部 agent 的任务包，不启动任何进程。省略 `--profile` 时扫描所有档案找任务 id。外部 agent 完成后通过 MCP `submit_agent_task_candidate` 回传摘要、`changed_paths`、warnings 和 result payload，任务变为 `candidate_ready`；失败或阻塞用 `update_agent_task_status`。见 [MCP 参考](mcp.md)。

## 本地 Codex runner

```bash
nblane codex local run <task_id> --profile <name>
```

在临时 git worktree 里从干净的 `HEAD` 跑 `codex exec`，收集 diff 写回任务的 `result_payload`，状态变为 `candidate_ready`。不改主工作树；主工作树有未提交改动时只记一条提示。不由页面触发。

## Codex Cloud

配置 `NBLANE_CODEX_CLOUD_ENV_ID`（或档案 `codex.yaml` 里的 Cloud 环境 ID）后：

```bash
nblane codex status --profile <name>
nblane codex cloud submit <task_id> --profile <name>
nblane codex cloud refresh <task_id> --profile <name> [--diff]
```

任务上保存 `remote` 元数据（`provider: codex_cloud`、`cloud_task_id`、`env_id`、`branch`、`attempts`、`status_raw`）。`--diff` 把 Cloud diff 作为候选写回任务。nblane 不调用 `codex cloud apply`，不自动改本地工作树。

## Codex 配置

- 部署级：`NBLANE_CODEX_BIN`、`NBLANE_CODEX_HOME`（默认 `~/.codex`）、`NBLANE_CODEX_TIMEOUT_SECONDS` 等，见 `.env.example`。
- 档案级：`profiles/<name>/codex.yaml`，在「设置 → AI 路由 → Codex 运行参数」编辑（默认模型、超时、Codex 路径、Cloud 环境 ID、分支名）。不保存 token。
- 认证由 Codex CLI 自己管理（`codex login`）。「设置 → AI 服务」只显示是否安装和登录。

实现见 `core/codex_adapter.py`。

## 审阅

候选结果只在 `agent-tasks.yaml` 和 runner 保留的 worktree / diff 里，SPA 没有审批页。审阅后自己在仓库里应用 diff，再用 MCP `update_agent_task_status` 把任务标为 `applied`。
