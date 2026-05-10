---
status: active
owner: engineering
last_verified: 2026-05-08
source_of_truth: true
---

# 数据契约

本文是 profile、看板、证据、公开层、研究层的数据真源和不变量。它吸收了旧 `profile-documents-relationship.md` 中的 Profile 闭环说明。

## 事实源原则

- YAML/Markdown 是事实源。
- Workspace Index 是派生 read model，不手动编辑。
- `SKILL.md` 人写区由用户维护，生成块由 `sync` 写入。
- AI/Agent 产物默认是草稿或候选。
- Public Surface 只读取显式公开层文件。

## Profile 文件职责

| 文件 | 职责 | 真源属性 |
|------|------|----------|
| `SKILL.md` | 身份、研究品味、工作风格、生成块 | 人写章节是事实源；生成块是派生 |
| `skill-tree.yaml` | 节点 `status/note/evidence/evidence_refs` | 技能状态事实源 |
| `evidence-pool.yaml` | 稳定 evidence id 和摘要 | 共享证据目录 |
| `kanban.md` | 当前任务、Done、Queue、Someday | 当前执行事实源 |
| `kanban-archive.md` | 从 Done 归档出去的历史任务 | 历史备份，不参与默认上下文 |
| `agent-profile.yaml` | Agent 对用户的结构化 prior | Agent prior 事实源 |
| `activity-log.yaml` | habit、checkin、weekly summary | 活动记录事实源 |
| `learning-log.yaml` | paper/article/book/repo/course 等资源 | 学习资源事实源 |
| `inbox.yaml` | 捕获、澄清、归档的输入项 | 捕获入口事实源 |
| `public-profile.yaml` | 公开姓名、简介、联系方式 | 公开 profile 事实源 |
| `resume-source.yaml` | 可公开简历事实 | 简历事实源 |
| `projects.yaml` | 公开项目展示 | Public Surface 项目，不是内部项目管理 |
| `outputs.yaml` | 公开成果展示 | Public Surface 成果 |
| `public-library.yaml` | Public Site 后台文件树 | 编辑器组织层 |
| `blog/*.md` | 公开博客 Markdown | 博客正文和 front matter |
| `blog/*.blocknote.json` | BlockNote sidecar | 编辑器块状态，保存时可重建 Markdown |

## 更新顺序

### Evidence / Skill Tree / SKILL.md

```text
evidence-pool.yaml
  -> skill-tree.yaml
  -> validate
  -> sync SKILL.md generated blocks
```

不变量：

- `evidence_refs` 只能引用已存在的 pool id。
- `status` 提升需要人确认。
- `SKILL.md` 生成块不要手改。

### Kanban Done -> Evidence

```text
kanban Done task
  -> LLM JSON patch
  -> human selection
  -> evidence-pool.yaml
  -> skill-tree.yaml
  -> validate/sync
  -> optional crystallized marker
```

不变量：

- 未被采纳的 evidence 不能产生悬空 node ref。
- `crystallized: true` 只表示 Done 任务已被处理，不等于公开发布。

### Public Surface

```text
private profile facts
  -> human curation
  -> public-profile / resume-source / projects / outputs / blog
  -> validate_public_layer
  -> build_public_site
```

不变量：

- 公开站不读取 private `skill-tree.yaml`、`kanban.md`、`agent-profile.yaml`、auth 文件。
- Blog draft 必须显式 `status: published` 才进入正式输出。
- Media 只复制被公开对象引用的文件。

## 规划中的新增契约

### Internal Project

```text
project-board.yaml
  projects[]
    id
    title
    status
    milestones
    task_refs
    evidence_refs
    decision_refs
    research_source_refs
```

不变量：

- 不替代 public `projects.yaml`。
- `KanbanTask.project_id` 引用内部 project。
- Workspace Index 负责发现断链。

### Research Workspace

```text
research/sources.yaml
research/chunks/<source_id>.jsonl
research/claims.yaml
research/drafts.yaml
```

不变量：

- Research 默认 private。
- Claim 必须引用 source/chunk，或标记为 human note。
- Blog 可引用 source/claim，但公开发布前必须检查 private source 和 unsupported claim。

### AI Run

```text
ai-runs/YYYY-MM-DD.jsonl
```

不变量：

- 默认不保存完整私密 prompt。
- 保存 task、model、input refs、output refs、status、warnings、accepted 状态。
- 用于审计和调试，不是业务事实源。
