---
status: active
owner: product
last_verified: 2026-05-08
source_of_truth: true
---

# 路线图

本路线图替代旧 `product.md`、`design.md`、`initial-loop.md` 中分散的 Demo Phase 和 Sprint 计划。具体开发状态以 [项目状态](../project/status.md) 和 [里程碑](../project/milestones.md) 为准。

## 已落地基线

- Profile 文件层：`SKILL.md`、`skill-tree.yaml`、`evidence-pool.yaml`、`kanban.md`、`agent-profile.yaml`。
- CLI：profile、context、sync、validate、gap、evidence、ingest、health、team、public、auth 等。
- Web UI：Home、Skill Tree、Gap Analysis、Kanban、Team View、Profile Health、Public Site。
- Skill Provenance：内联 evidence、pool evidence、`evidence_refs`、物化解析。
- Profile 摄入：简历/长文本、Kanban Done -> LLM JSON patch -> validate/sync。
- MCP 初版：profile summary/context/kanban/gap resources，以及增长日志、evidence、interaction、method draft 等 tools。
- Public Surface v1：公开资料、简历、博客、项目、成果、静态站构建。
- Blog Editor：BlockNote sidecar、AI patch、视觉候选、Reviewer、Public Library。
- Personal Workspace 雏形：activity-log learning/exercise check-in。

## 下一阶段路线

| 阶段 | 目标 | 关键交付 |
|------|------|----------|
| M0 | 文档与项目管理事实源重构 | 新 `docs/zh` IA、项目状态、里程碑、AI 架构、模块图 |
| M1 | AI Gateway | 任务化模型调用、结构化输出、模型路由、AI run 日志 |
| M2 | Workspace Index | 文件事实源上的 typed graph、对象索引、总览视图 |
| M3 | Internal Project Board | 内部项目/milestone 模型、Kanban task project refs |
| M4 | Research Workspace | source、chunk、claim、citation、synthesis draft |
| M5 | Source-aware Blog AI | blog draft 与 source/claim 绑定、unsupported claim reviewer |
| M6 | MCP 扩展 | workspace/research/project/blog resources 与 draft-first tools |
| M7 | Codex/OpenCode Adapter | harness 配置生成、agent roles、handoff task |
| M8 | Obsidian-like Views | table/board/graph/project/research 多视图 |

## 暂不做

- 立刻迁移到 SQLite/Postgres 主存储。
- 把 Codex/OpenCode 内嵌为 nblane 的业务库。
- 让 AI/Agent 直接发布公开内容。
- 把 Research Workspace 塞进 Public Site 页面。
- 做托管型社交网络。

## 升级判断标准

每个阶段都必须满足：

- 旧 profile 能继续读取。
- 文件仍可人工编辑。
- 写入有校验或至少 warning。
- AI/Agent 产物先进入草稿或候选。
- Public Surface 不泄露 private 文件。
