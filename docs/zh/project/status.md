---
status: active
owner: engineering
last_verified: 2026-05-08
source_of_truth: true
---

# 当前状态

## 总体判断

nblane 当前功能可用，但产品结构还没有完全收束。主要问题不是缺少单点能力，而是：

- 文档和项目管理状态过于分散。
- 看板、博客、证据、学习、公开输出之间缺少统一索引。
- AI 调用层仍是薄 `llm.chat()` wrapper。
- 博客 AI 缺少 source/claim/citation provenance。
- Team product pool 结构偏弱。
- Codex/OpenCode 等高级 harness 还没有作为外部执行器接入。

## 已实现能力

| 模块 | 状态 | 说明 |
|------|------|------|
| Profile 数据层 | 已实现 | `profiles/<name>/` 下的核心 YAML/Markdown 文件 |
| Skill Tree / Schema | 已实现 | schema 校验、状态统计、sync 生成块 |
| Evidence Pool | 已实现 | pool row、refs、物化解析、CLI/Web 编辑 |
| Kanban | 已实现 | Markdown parser/render、拖拽、子任务、归档、Done -> evidence |
| Profile Ingest | 已实现 | resume/kanban Done -> LLM JSON patch -> validate/sync |
| Web UI | 已实现 | Streamlit 多页应用 |
| Public Site | 已实现 | profile/blog/resume/project/output 静态构建 |
| Blog Editor | 已实现 | BlockNote、sidecar、AI patch、visual、Reviewer |
| MCP Server | 初版已实现 | profile resources + write tools |
| Cursor Skill | 初版已实现 | `sync-cursor` 生成规则文件 |
| Team View | 初版已实现 | team.yaml / product-pool.yaml 编辑 |
| Activity / Learning / Inbox helpers | 部分实现 | core helper 和测试存在，UI 未完全统一 |

## 主要缺口

| 缺口 | 影响 | 对应里程碑 |
|------|------|------------|
| 文档事实源混乱 | 新开发和产品判断容易重复/过期 | M0 |
| AI 调用不可任务化 | 模型路由、结构化输出、审计困难 | M1 |
| 缺少统一索引 | 无法像 Obsidian Bases 一样跨文件查询/视图 | M2 |
| 项目不是一等实体 | task/evidence/public project/team project 难关联 | M3 |
| 缺少研究 source/claim 层 | 博客和论文分析缺乏出处链 | M4/M5 |
| MCP 覆盖面不足 | OpenCode/Codex 不能自然读写 nblane | M6 |
| Harness 集成缺失 | 复杂多步任务仍只能靠人工复制 prompt | M7 |

## 当前技术边界

- 主存储仍是文件，不是数据库。
- LLM 通过 OpenAI-compatible API key 调用。
- Streamlit 是主要 UI shell。
- 前端组件已内置静态 bundle，只有改组件时才需要 Node 构建。
- 公开站构建不会读取 private profile 文件。

## 近期优先级

1. 完成文档 IA 重构，清掉旧过程文档。
2. 设计并落地 AI Gateway 兼容层。
3. 做只读 Workspace Index，先不要改存储格式。
4. 扩展 MCP resources/tools，为 OpenCode/Codex 接入做基础。
