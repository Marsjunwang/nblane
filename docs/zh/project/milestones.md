---
status: active
owner: engineering
last_verified: 2026-05-08
source_of_truth: true
---

# 里程碑

## M0 · 文档与项目管理事实源重构

目标：把产品定义、项目状态、架构边界、路线图和指南拆清楚。

交付：

- 新 `docs/zh` 信息架构。
- `project/status.md`、`project/milestones.md`、`project/issues.md`、`project/decisions.md`。
- `architecture/ai-architecture.md`、`architecture/module-map.md`、`architecture/data-contracts.md`。
- `reference/agent-harness.md`。
- 删除被吸收的旧过程文档。

验收：

- `docs/zh/README.md` 可按读者路径导航。
- 旧 `design.md` / `initial-loop.md` / `public-site-workplan.md` 不再作为主入口。
- README、代码注释、文档链接不再引用已删除旧路径。

## M1 · AI Gateway

目标：把 API key 直连模型升级为任务化 AI 调用层。

交付：

- `src/nblane/core/ai/` 模块。
- task-based `run_text` / `run_json`。
- 任务类型、prompt registry、结构化输出校验、模型路由。
- AI run 日志。
- `llm.py` 兼容旧调用。

验收：

- 旧功能继续工作。
- 新 AI 功能不直接调用 `llm.chat()`。
- JSON 任务有 schema 校验和 typed error。
- 未配置新模型路由时回退到现有 `LLM_MODEL`。

## M2 · Workspace Index

目标：在 YAML/Markdown 文件上建立只读 typed graph。

交付：

- `workspace_index.py`。
- 节点、边、warning 数据结构。
- 覆盖 profile、kanban、evidence、skill、blog、team、activity、learning、inbox。
- 总览 UI 初版。

验收：

- 不改变现有存储格式。
- 缺文件/坏 YAML 不崩。
- dangling refs 生成 warning。
- 输出 deterministic。

## M3 · Internal Project Board

目标：让内部项目成为一等实体。

交付：

- `project-board.yaml`。
- Project/Milestone loader/saver/validator。
- Kanban task 支持 `project_id` / `milestone_id`。
- Workspace Index 展示 project -> task -> evidence。

验收：

- 旧 `kanban.md` 兼容。
- 归档和拖拽保留 project metadata。
- Public `projects.yaml` 不受内部 project 影响。

## M4 · Research Workspace

目标：建立论文/资料/source/claim/synthesis 的私有研究层。

交付：

- `research/sources.yaml`。
- `research/chunks/*.jsonl`。
- `research/claims.yaml`。
- `research/drafts.yaml`。
- metadata ingest 和 claim extraction 初版。

验收：

- source id/hash 稳定。
- claim 可回指 source/chunk，或显式标记 human note。
- Research 默认 private。

## M5 · Source-aware Blog AI

目标：让博客草稿、AI patch、Reviewer 具备出处意识。

交付：

- Blog front matter 支持 `related_sources` / `related_claims`。
- AI patch 支持 source/chunk/claim refs。
- Reviewer 支持 unsupported claim 检查。
- Synthesis draft 可导出 blog draft。

验收：

- 发布前能提示缺出处和 private source。
- 现有 Blog Editor、BlockNote sidecar、static build 不回退。

## M6 · MCP 扩展

目标：让外部 Agent 能读取 workspace/research/project/blog，并安全写回草稿。

交付：

- `workspace://graph`、`research://sources`、`project://status`、`blog://drafts` 等 resources。
- `capture_research_source`、`create_claim`、`create_synthesis_draft`、`export_synthesis_to_blog_draft` 等 tools。

验收：

- tools draft-first。
- 写入复用路径安全、冲突检查、atomic write、git backup。
- missing profile 有明确错误。

## M7 · Codex/OpenCode Harness Adapter

目标：把 Codex/OpenCode 作为外部高级执行器接入。

交付：

- `nblane sync-agent-harness --target codex|opencode`。
- agent role prompts。
- MCP config snippets。
- `agent-tasks.yaml` 与 handoff CLI。

验收：

- nblane 不依赖 harness 内部 API。
- harness 通过 MCP 读取/写回 nblane。
- 写回默认草稿，人确认后进入事实源或公开发布。

## M8 · Obsidian-like Views

目标：基于 Workspace Index 提供属性过滤、多视图和 typed graph。

交付：

- Table view。
- Board view。
- Graph view。
- Project view。
- Research matrix。
- Evidence/publication readiness view。

验收：

- 同一对象可在不同视图里出现。
- 视图不成为新的事实源。
- 断链、缺 source、unsupported claim 可见。
