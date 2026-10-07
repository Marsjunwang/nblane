---
status: active
owner: engineering
last_verified: 2026-10-07
source_of_truth: true
---

# 文件存储演进

本文说明 nblane「文件 + YAML/Markdown + Git 备份」数据方案的边界：公开层、媒体、规模演进，以及什么时候才需要数据库。公开层文件、静态站构建和 Git 备份已落地；对象存储与数据库仍是演进选项。

| 项 | 值 |
|----|----|
| 状态 | 文件优先已落地；数据库未采用 |
| 范围 | `profiles/`、公开层、媒体、文件到数据库演进 |

---

## 1. 背景与结论

nblane 的核心优势是 **plain text first**：目标、技能树、证据、项目、看板、研究和公开层都落在 Markdown / YAML 文件中，由 Git 记录历史。服务进程（8504 SPA + API、8502 Reader）不持有自己的状态。这种模型透明、可 diff、可被 Agent 直接读取，也容易备份。

结论：

- **个人网站继续文件优先**，通过独立的 **public data layer** 发布，不把内部 `SKILL.md`、`kanban.md`、`skill-tree.yaml` 原样公开。
- **少量账号继续用 `profiles/<name>/` 目录隔离**，配合登录、profile 权限、文件快照比对（ETag / 412）、文件锁和 Git backup。
- **媒体和高并发是文件方案的边界**：图片可先放本地 `media/`，视频优先外链或对象存储；大量用户、高频写入、搜索和公开站点托管最终需要数据库与对象存储。
- **真正 SaaS 多租户阶段应迁移到数据库**，文件系统退化为 export / backup，而不是主存储。

---

## 2. 当前文件模型

profile 主要数据（完整清单见 [数据契约](data-contracts.md)）：

```text
profiles/<name>/
  SKILL.md
  agent-profile.yaml
  skill-tree.yaml
  evidence-pool.yaml
  kanban.md
  kanban-archive.md
  goals.yaml
  project-board.yaml
  activity-log.yaml
  chronicle.yaml
  agent-journal.yaml
  research/
```

全局数据：

```text
schemas/*.yaml
auth/users.yaml
```

生产通过 `NBLANE_ROOT` 把数据目录独立到 `/srv/nblane-data`。每次写入可由 `NBLANE_DATA_GIT_AUTOCOMMIT` / `NBLANE_DATA_GIT_AUTOPUSH` 自动提交 / 推送；设置 → 助手与备份另有每日推送到私有远端。Web API 用文件指纹 ETag + `If-Match`（412）做并发保护，写入持有 flock 边车锁。

### 2.1 文件职责

| 文件 | 当前职责 | 是否适合直接公开 |
|------|----------|------------------|
| `SKILL.md` | Agent/persona prompt、身份叙事、研究 taste、生成块 | 否。包含内部成长、短板、agent 校准信息 |
| `skill-tree.yaml` | 技能节点状态、证据引用、学习进度 | 否。它是能力状态源，不是公开简历 |
| `evidence-pool.yaml` | 证据事实库，供 skill tree 引用 | 部分。可作为公开成果事实源，但需要白名单和扩展字段 |
| `kanban.md` | 当前工作计划、Doing / Queue / Done | 否。计划不应原样公开 |
| `kanban-archive.md` | 已归档 Done 历史 | 否。可作为内部回顾源 |
| `agent-profile.yaml` | Agent 侧结构化先验 | 否 |
| `agent-journal.yaml` | Agent 写入撤销日志 | 否 |
| `auth/users.yaml` | 账号、角色、profile 权限、Agent 标志 | 否 |

### 2.2 当前方案擅长什么

- 人和 agent 都能直接读写。
- Git diff 能显示成长轨迹与数据变更。
- 小规模数据容易备份、恢复、迁移。
- CLI、SPA、Agent（HTTP）、本机 MCP 共享同一事实来源。
- 适合「AI 出候选、人确认后写入」和「Agent 直写、可撤销」两种写入方式。

### 2.3 当前方案不擅长什么

- 大文件、视频、频繁上传的媒体。
- 高频并发写入。
- 多用户同时编辑同一个对象。
- 全站搜索、复杂筛选、分页、统计。
- 公开发布状态、SEO、站点构建缓存。
- 严格 SaaS 多租户隔离、审计和计费。

---

## 3. 个人网站功能覆盖评估

| 功能 | 当前原样 | 文件扩展后 | 需要数据库的信号 |
|------|----------|------------|------------------|
| 姓名、简介、联系方式 | 部分在 `SKILL.md` | `public-profile.yaml` | 多站点、多语言、多模板 |
| 头像、照片 | 不满足 | `media/avatar.*` | 大量媒体、裁剪、CDN |
| 在线简历预览 | 不满足 | `resume-source.yaml` + generated HTML | 复杂版本、协作编辑、搜索 |
| 简历下载 | 不满足 | Markdown / HTML 可先做，PDF 后续 | 批量生成、任务队列 |
| 岗位定制简历 | 不满足 | 基于结构化事实库生成 | 多用户并发生成、审计 |
| 博客写作 | v1 已支持 | `blog/**/*.md` + front matter | 评论、搜索、多人协作 |
| 博客图片 | v1 已支持 | `media/blog/<slug-or-route>/` | 大量图片、CDN |
| 博客视频 | 部分支持 | 优先外链；小型 `mp4` / `webm` 可本地 | 视频上传、转码、播放统计 |
| 项目链接 | 部分在 evidence | `projects.yaml` 引用 evidence | 项目多、复杂筛选 |
| 论文 / 专利 | 部分在 evidence | `outputs.yaml`，扩展 `patent` 等类型 | 引用统计、同步外部平台 |
| 工作计划结合 | Done -> evidence（结晶） | 公开发布管线 | 任务状态复杂 |
| 少量账号 | 已有登录与 profile 权限 | profile 目录隔离可继续 | 高并发、多实例部署 |

---

## 4. 推荐新增 public layer

公开网站不应直接读取完整内部文件。推荐新增只面向 public surface 的白名单数据。

```text
profiles/<name>/
  public-profile.yaml
  resume-source.yaml
  projects.yaml
  outputs.yaml
  blog/
    2026-04-26-vla-memory.md
  media/
    avatar.jpg
    blog/2026-04-26-vla-memory/cover.jpg
  resumes/
    generated/
      2026-04-26-vla-engineer.md
      2026-04-26-vla-engineer.html
```

### 4.1 `public-profile.yaml`

公开身份与联系方式。它是个人网站首页的主要来源。

```yaml
profile: 王军
visibility: public
public_name: 王军
english_name: Jun Wang
headline: Embodied AI / Robotics Perception Engineer
avatar: media/avatar.jpg
bio_short: >
  具身智能与机器人感知算法工程师，关注 VLA、6D pose 和真实系统落地。
contacts:
  email: ""
  wechat: ""
  github: ""
  google_scholar: ""
  linkedin: ""
  zhihu: ""
featured:
  projects: []
  outputs: []
  posts: []
```

### 4.2 `resume-source.yaml`

结构化简历事实库。AI 只能选择、压缩、重写其中已有事实，不能编造经历、指标、论文或链接。

```yaml
profile: 王军
basics:
  name: 王军
  title: 具身算法工程师
experiences:
  - id: cloudmile_embodied
    company: CloudMile
    role: 具身算法工程师
    start: "2025-04"
    end: present
    bullets: []
    tags: [embodied_ai, robotics, vla]
projects: []
outputs: []
```

### 4.3 `projects.yaml` 和 `outputs.yaml`

`evidence-pool.yaml` 是事实证据库，但不是公开 CMS。公开项目和成果应显式列出，并引用可公开的 evidence id。

```yaml
projects:
  - id: piper_pi05
    title: PI0.5 Reproduction on Piper Arm
    status: published
    featured: true
    evidence_refs: [ev_piper_repro]
    links:
      github: ""
      demo: ""
      blog: ""
```

```yaml
outputs:
  - id: iup_pose
    type: paper
    title: "IUP-Pose: ..."
    year: "2025"
    status: published
    evidence_refs: [ev_pose_paper]
    links:
      paper: ""
      code: ""
```

### 4.4 `blog/*.md`

博客使用 Markdown + front matter。公开站只展示 `status: published`。

```markdown
---
title: VLA Memory 模块调研笔记
date: 2026-04-26
status: draft
tags: [VLA, robotics, memory]
cover: media/blog/2026-04-26-vla-memory/cover.jpg
related_kanban:
  - VLA memory模块
related_evidence:
  - ev_spatial_forcing_vggt
---

正文...
```

### 4.5 `media/`

小图片、头像、项目封面可以先放本地 `media/`。视频优先使用外链或对象存储 URL；不建议把大量 mp4 放进 Git backup。

---

## 5. 公开发布边界

公开网站只读 public layer：

```text
public-profile.yaml
resume-source.yaml
projects.yaml
outputs.yaml
blog/*.md where status=published
media/
resumes/generated/
```

公开网站不应直接展示：

```text
SKILL.md
skill-tree.yaml
kanban.md
kanban-archive.md
agent-profile.yaml
auth/users.yaml
```

每个公开对象默认都应是 private / draft，只有显式 `status: published` 或 `visibility: public` 才发布。

Kanban 和 public surface 的关系应是转换关系：

```text
Kanban Done
  -> evidence
  -> blog draft
  -> resume bullet
  -> project update
  -> public website
```

不建议把 Doing / Queue 直接公开。当前计划可以人工写成公开摘要，但不应原样展示内部任务。

---

## 6. 多用户能力边界

### 6.1 小规模多用户

适合继续文件优先：

```text
本人 + 自己的 Agent，少量账号
每人一个 profile
低并发编辑
SPA 工作台（单进程 API）
Git backup 审计
```

需要保持的约束：

- 用户只能读写授权 profile。
- 上传路径必须限制在自己的 `profiles/<name>/media/` 下。
- 保存时继续使用 file snapshot。
- Git commit actor 记录当前用户。
- 公开站只读当前 profile 的 public layer。

### 6.2 中等规模

当出现以下情况，应开始拆分媒体与构建产物：

- 多人频繁上传图片 / 视频。
- Git 仓库体积明显增长。
- Git autopush 成为保存延迟来源。
- 公开站点需要更快构建和缓存。

建议：

- YAML / Markdown 继续作为源数据。
- 大媒体迁移到对象存储。
- `media/` 中只保留轻量图片或远程 URL。
- public site build 输出不纳入 profile 源数据。

### 6.3 SaaS 多租户

当目标变成公开注册、多人协作、计费、可扩展托管时，应迁移：

```text
profiles / documents -> Postgres 或 SQLite
media -> object storage
generation jobs -> task queue
Git -> export / backup / audit snapshot
```

此时文件系统不再是主存储，而是可读导出和备份格式。

---

## 7. 演进路线

| 阶段 | 存储策略 | 目标 |
|------|----------|------|
| v0 | `profiles/` 文件模型（已落地） | Private、Agent 层 |
| v1 | public layer 文件（已落地） | 公开站、简历、博客、项目、成果 |
| v2 | 公开站控制台与构建清单 | 导航、精选内容、上线开关 |
| v3 | 媒体外置 | 图片 / 视频规模增长，减少 Git 大文件 |
| v4 | 数据库主存储 | SaaS 多租户、高并发、搜索、审计、任务队列 |

---

## 8. 决策表

| 决策 | 当前建议 |
|------|----------|
| 是否立刻上数据库 | 否 |
| 是否继续文件优先 | 是 |
| 是否直接公开 `SKILL.md` | 否 |
| 是否直接公开 `kanban.md` | 否 |
| 是否把 evidence 当公开 CMS | 否，它是事实源，公开展示需白名单 |
| 视频是否放 Git | 默认否，优先外链 / 对象存储 |
| 小规模多用户是否可继续当前模型 | 是 |
| SaaS 多租户是否继续纯文件 | 否 |

---

## 9. 后续演进信号

1. 媒体或 Git 仓库体积明显增长时，先把视频和大图迁到对象存储。
2. 出现多实例部署或高频并发写时，再评估数据库主存储；在此之前保持单进程 + 文件锁。

## 10. 相关文档

- [数据契约](data-contracts.md)
- [产品总览](../product/overview.md)
- [架构总览](overview.md)
- [公开站点](../guides/public-site.md)
- [技能证据 Skill evidence](../reference/evidence.md)
