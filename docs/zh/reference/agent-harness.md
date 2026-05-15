---
status: active
owner: engineering
last_verified: 2026-05-15
source_of_truth: true
---

# Agent Harness 集成

nblane 不把 Codex/OpenCode 内嵌为业务库。它们是外部高级执行器，通过 MCP、生成的 agent 指令和 CLI adapter 连接 nblane。

## 原则

```text
nblane = 长期数据、上下文、项目、研究、证据、公开层
Codex/OpenCode = 多步执行、代码修改、测试、复杂 agent loop
MCP = 二者之间的上下文和工具协议
```

不推荐：

- 把 OpenCode 当成 `llm.chat()` 替代品。
- 让每个 UI 按钮都启动 harness。
- 依赖 harness 内部 API。
- 让外部 agent 直接绕过 nblane 校验写 profile 文件。

推荐：

- UI 内短任务走 AI Gateway。
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
```

交接命令：

```bash
nblane agent handoff agenttask_001 --target opencode --profile <name>
```

`--profile` 省略时会扫描现有 profiles 寻找任务 id。MVP 只生成可复制给
Codex/OpenCode 的 handoff 信息，不启动外部 runtime。

## 与 MCP 的关系

Harness 通过 MCP 读写：

```text
Resources:
  profile://context
  workspace://graph
  research://sources
  project://status
  blog://drafts

Tools:
  create_kanban_task
  capture_research_source
  create_claim
  create_synthesis_draft
  export_synthesis_to_blog_draft
  log_task_evidence
```

MCP 是第一阶段核心协议。ACP 暂不作为核心依赖，除非 nblane 未来需要自建 agent client 或 agent-agent runtime。
