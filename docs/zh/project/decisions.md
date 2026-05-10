---
status: active
owner: product
last_verified: 2026-05-08
source_of_truth: true
---

# 决策记录

## D1 · 中文文档为事实源

结论：`docs/zh/` 是主维护目录。英文只保留入口和关键摘要。

理由：

- 当前中文文档更完整。
- 项目主要讨论和产品规划使用中文。
- 中英完整镜像维护成本过高。

## D2 · 旧过程文档合并后删除

结论：`initial-loop.md`、`public-site-workplan.md`、`public-site-blog-editor-design.md` 等过程文档被吸收到新事实源后删除，不长期归档。

理由：

- 过程文档继续存在会制造过期入口。
- 项目管理信息应集中在 `project/`。
- 历史仍可通过 Git 找回。

## D3 · 文件优先，不立刻上数据库

结论：YAML/Markdown 继续作为事实源。SQLite/Postgres 只作为后续索引缓存或 SaaS 规模化选项。

理由：

- 当前产品价值来自可读、可 diff、可人工编辑的文件。
- 现有 CLI/Web/MCP 已围绕文件工作。
- Obsidian-like 体验可以先通过属性、索引、视图实现。

## D4 · AI Gateway 先于 Harness 集成

结论：先把内部模型调用从 `llm.chat()` 升级为任务化 AI Gateway，再接 OpenCode/Codex。

理由：

- UI 内短任务需要低延迟、结构化输出和可控错误。
- OpenCode/Codex 更适合复杂多步任务，不适合替代所有按钮级模型调用。
- AI Gateway 是未来模型路由、审计、prompt registry 的基础。

## D5 · MCP-first，ACP 后评估

结论：MCP 是 nblane 第一阶段的核心集成协议。ACP 暂不进入核心架构。

理由：

- nblane 当前需要让外部 Agent 读上下文、调用工具写回。
- Codex/OpenCode 都支持 MCP。
- ACP 更偏 agent client 或 agent-agent 通信，当前不是主要瓶颈。

## D6 · Codex/OpenCode 不内嵌为业务库

结论：Codex/OpenCode 是外部高级执行器，通过 MCP、生成指令和 CLI adapter 集成。

理由：

- 避免绑定某个 harness 的内部 API。
- 保持 nblane 数据模型独立。
- 方便未来同时支持 Cursor、Claude Code、OpenAI Agents SDK 或其他工具。

## D7 · Public Site 与 Research Workspace 分离

结论：Public Site 继续负责公开发布；Research Workspace 负责 source、chunk、claim、citation、synthesis draft。

理由：

- Public Site 页面已经很重。
- 研究资料默认私有，公开发布必须显式导出。
- 博客需要 source-aware，但不应把私有研究层直接变成公开层。
