---
status: active
owner: engineering
last_verified: 2026-05-15
source_of_truth: true
---

# AI 架构

当前 nblane 直接用 API key 调 OpenAI-compatible chat API。这个方式保留，但要从薄 `llm.chat()` 升级为任务化 AI Gateway；Codex/OpenCode 用于复杂多步 agent 工作，不替代 UI 内短模型调用。

## 分层

```text
Streamlit / CLI short AI task
    -> nblane AI Gateway
    -> Direct Model API

Codex / OpenCode / Cursor / Claude
    -> nblane MCP Server
    -> nblane resources/tools
    -> YAML/Markdown facts
```

## Direct API 适合什么

继续直接调模型的任务：

- Gap AI 解释和追问。
- Resume / Kanban Done -> evidence patch。
- Blog inline polish / expand / translate。
- Blog reviewer。
- Kanban task alignment / subtask generation。
- Visual caption prompt。
- Profile health summary。

这些任务短、局部、需要低延迟和结构化输出，不适合启动完整 harness。

## AI Gateway

已新增 MVP 模块边界：

```text
src/nblane/core/ai/
  gateway.py
  actions.py
  backends.py
  prompts.py
  structured.py
  runs.py
  router.py
```

职责：

- 任务化调用：`blog.inline_patch`、`profile.ingest_resume`、`kanban.subtasks`。
- 模型路由：fast、json、writing、reasoning、review。
- 结构化输出：JSON extraction + schema validation + typed error。
- Prompt registry：集中管理 prompt 版本。
- 重试和一次修复。
- Streaming。
- AI run 日志。
- Activity bridge：需要审阅的 action 自动进入 Agent Activity。
- ExternalAgentBackend：只创建 Codex/OpenCode handoff 任务，不执行外部 runtime。

兼容：

- `llm.py` 保留旧接口。
- 未配置新路由时回退到 `LLM_MODEL`。

第一批注册的 action：

- `research.reading_draft`
- `research.recommend_sources`
- `resume.bullets_from_claims`
- `resume.target_for_job`
- `output.blog_candidate`
- `output.inline_patch`
- `kanban.task_alignment`
- `kanban.subtasks`
- `work.remote_dev_task`

Kanban 的任务理解和子任务生成已经通过 `core/ai/` 调用；页面可以选择
`record_activity=True` 将候选写入 Agent Activity，也可以保持纯函数式预览。

Agent 闭环 v1 已打通：

- Kanban 页面可以从任务创建 `work.remote_dev_task` handoff。
- `ExternalAgentBackend` 创建 `agent-tasks.yaml` 记录和 Agent Activity patch item。
- 外部 harness 通过 MCP 读取 `agent://task/{task_id}`，完成后用
  `submit_agent_task_candidate` 写回候选结果。
- 写回只更新 `agent-tasks.yaml` 与 `agent-activity.yaml`，不直接修改事实源或发布内容。

## OpenCode / Codex 适合什么

外部 harness 负责复杂多步任务：

- 分析整个代码库。
- 实现 milestone。
- 跑测试并修 bug。
- 处理一批研究资料。
- 生成 source-aware synthesis。
- 多 agent review / researcher / writer 协作。

它们通过 MCP 访问 nblane，不作为 nblane 内部业务库。

## MCP-first

MCP 是当前阶段的一级集成接口：

- resources：给外部 agent 读 profile、workspace、research、project、blog draft。
- tools：让外部 agent draft-first 写回 task、claim、synthesis、evidence draft。
- agent handoff：`agent://tasks`、`agent://task/{task_id}` 以及
  `submit_agent_task_candidate` / `update_agent_task_status`，用于
  Codex/OpenCode 结果回到候选态审阅。

ACP 暂不进入核心架构。只有未来 nblane 自建 agent client、agent runtime 或 agent-agent 编排时再评估。

## 写回安全

- AI/Agent 默认写草稿。
- evidence/skill-tree 变更必须 validate/sync。
- Public publish 必须人工确认。
- MCP tools 复用路径安全、文件冲突检查、atomic write、Git backup。
- AI run 默认不保存完整私密 prompt。
