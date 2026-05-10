---
status: active
owner: engineering
last_verified: 2026-05-08
source_of_truth: true
---

# 问题与风险

## 当前问题

| 问题 | 影响 | 处理方向 |
|------|------|----------|
| 文档曾经扁平且重复 | 用户和开发者难判断哪个文档是事实源 | M0 重构，旧过程文档合并后删除 |
| AI 调用散落 | 难做模型路由、重试、审计和结构化输出 | M1 AI Gateway |
| 没有统一对象索引 | 任务、证据、博客、项目、source 无法跨文件查询 | M2 Workspace Index |
| Kanban 是任务面但不是项目面 | 缺 project/milestone/roadmap 结构 | M3 Project Board |
| Public projects 与内部项目混用风险 | 私有项目管理和公开展示字段目标不同 | 内部 `project-board.yaml` 与公开 `projects.yaml` 分离 |
| Blog AI 没有 source provenance | 论文/资料分析生成缺出处链 | M4/M5 Research + Source-aware Blog |
| Team product pool 结构弱 | 团队问题、项目、证据、决策不能稳定互链 | M3 后升级 team pool schema |
| OpenCode/Codex 未接入 | 复杂 agent 工作仍靠复制 prompt | M6/M7 MCP + Harness adapter |

## 风险

- **一次重构过大**：文档、AI、索引、研究、Agent 集成都很大。应按 milestone 切片，不在一个 PR 里实现所有功能。
- **文件格式膨胀**：新增字段必须保持旧 profile 可读，未知字段不应破坏 parser。
- **AI 写回越权**：MCP/harness tools 必须 draft-first，并复用 validate/sync。
- **公开层泄露私有信息**：Public Site 只读取公开层文件，Research Source 默认 private。
- **索引误当事实源**：Workspace Index 是 read model，可重建，不手动编辑。
- **模型供应商变化**：AI Gateway 应保持 OpenAI-compatible provider 抽象，避免把业务逻辑写死到某个 provider。

## 待观察

- 是否需要 SQLite 作为索引缓存。
- 是否需要独立 Research Workspace 页面，而不是扩展 Public Site 页面。
- OpenCode 与 Codex 的配置生成差异是否需要分 target 模板。
- ACP 是否在自建 agent client 后进入架构。
