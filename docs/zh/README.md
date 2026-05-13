---
status: active
owner: docs
last_verified: 2026-05-08
source_of_truth: true
---

# nblane 中文文档

中文文档是 nblane 的主事实源。英文文档只保留入口与关键摘要；产品定义、项目状态、架构边界、开发里程碑以本目录为准。

## 推荐阅读路径

| 读者 | 阅读顺序 |
|------|----------|
| 新用户 | [产品总览](product/overview.md) -> [安装与 LLM 配置](guides/setup.md) -> [Web 使用手册](guides/web-ui.md) -> [看板使用手册](guides/kanban.md) |
| 产品 / 项目管理 | [核心闭环](product/core-loop.md) -> [路线图](product/roadmap.md) -> [当前状态](project/status.md) -> [里程碑](project/milestones.md) -> [问题与风险](project/issues.md) |
| 开发者 | [架构总览](architecture/overview.md) -> [数据契约](architecture/data-contracts.md) -> [模块总览图](architecture/module-map.md) -> [CLI 参考](reference/cli.md) -> [MCP 参考](reference/mcp.md) |
| Agent / 集成方 | [AI 架构](architecture/ai-architecture.md) -> [Agent Harness 集成](reference/agent-harness.md) -> [MCP 参考](reference/mcp.md) |
| 运维 / 发布 | [腾讯云部署](guides/deployment-tencent-cloud.md) -> [存储演进](architecture/storage.md) -> [公开站点](guides/public-site.md) |

## 文档地图

### Product

| 文档 | 作用 |
|------|------|
| [overview.md](product/overview.md) | nblane 是什么、用户是谁、核心对象和非目标 |
| [core-loop.md](product/core-loop.md) | 当前最小闭环：捕获、计划、执行、证据、研究、发布、Agent 复用 |
| [growth-graph.md](product/growth-graph.md) | 成长关系图谱：事实沉淀为 evidence，evidence 支撑 skill，skill 构成 North Star 的能力地基 |
| [roadmap.md](product/roadmap.md) | 当前统一路线图，替代旧 `product.md` / `design.md` 中分散的 Demo Phase |
| [web-experience.md](product/web-experience.md) | Streamlit Web 体验设计和 backlog |

### Project

| 文档 | 作用 |
|------|------|
| [status.md](project/status.md) | 当前实现状态、已落地能力和缺口 |
| [milestones.md](project/milestones.md) | 开发里程碑总账 |
| [issues.md](project/issues.md) | 当前问题、风险与待处理项 |
| [decisions.md](project/decisions.md) | 关键产品/架构决策 |

### Architecture

| 文档 | 作用 |
|------|------|
| [overview.md](architecture/overview.md) | 当前代码、模块和运行时架构 |
| [data-contracts.md](architecture/data-contracts.md) | Profile、看板、证据、公开层、研究层的数据真源与不变量 |
| [module-map.md](architecture/module-map.md) | 模块化对象关系和总览图 |
| [ai-architecture.md](architecture/ai-architecture.md) | Direct API、AI Gateway、MCP、Codex/OpenCode、ACP 的分层 |
| [storage.md](architecture/storage.md) | 文件优先、Git、媒体、数据库演进边界 |

### Guides

| 文档 | 作用 |
|------|------|
| [setup.md](guides/setup.md) | 安装、依赖、LLM/Visual provider 配置 |
| [web-ui.md](guides/web-ui.md) | Streamlit 页面使用手册 |
| [kanban.md](guides/kanban.md) | 看板、Done 摄入、归档规则 |
| [public-site.md](guides/public-site.md) | 公开资料、博客、简历、项目、静态构建 |
| [blog-editor.md](guides/blog-editor.md) | Blog 编辑器、AI patch、视觉候选、发布检查 |
| [deployment-tencent-cloud.md](guides/deployment-tencent-cloud.md) | 腾讯云小团队部署 |

### Reference

| 文档 | 作用 |
|------|------|
| [cli.md](reference/cli.md) | CLI 命令总览 |
| [mcp.md](reference/mcp.md) | MCP resources/tools 与 Cursor/外部工程接入 |
| [evidence.md](reference/evidence.md) | Evidence 字段、CLI、Web、上下文解析 |
| [skill-tree-schema.md](reference/skill-tree-schema.md) | `schemas/` 与 `skill-tree.yaml` |
| [skill-md-format.md](reference/skill-md-format.md) | `SKILL.md` 人写区和生成区 |
| [agent-harness.md](reference/agent-harness.md) | Codex/OpenCode 集成策略与生成配置 |

## 维护规则

- Active 文档必须保留 front matter：`status`、`owner`、`last_verified`、`source_of_truth`。
- 产品状态只写在 `project/status.md` 和 `project/milestones.md`，不要在使用手册里重复维护路线图。
- 过程性工作计划合并后删除；不要再新增长期未维护的 `*-workplan.md`。
- 涉及公开发布、Agent 写回、研究资料引用的行为，以 [数据契约](architecture/data-contracts.md) 和 [AI 架构](architecture/ai-architecture.md) 为准。
