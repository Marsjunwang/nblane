---
status: active
owner: engineering
last_verified: 2026-05-13
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
| `evidence-pool.yaml` | 稳定 evidence id、摘要和 accepted claim bridge | 共享证据目录；P2 claim 桥接事实源 |
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

### Evidence -> Claim Bridge

```text
selected evidence
  -> claim candidates
  -> human selection
  -> evidence-pool.yaml claims[]
  -> Output Studio related_claims / provenance
```

P2 不新增独立 `claims.yaml`。Web 中的 Claim 先作为 Evidence Review 和
Output Studio 的桥接层：生成态候选只保存在会话预览中；只有用户点击应用后，
才写入 `evidence-pool.yaml` 顶层 `claims` 列表，且状态固定为 `accepted`。

`evidence-pool.yaml` 允许的最小形态：

```yaml
evidence_entries:
  - id: ev_demo
    title: Demo
    summary: Built and shipped a demo.

claims:
  - id: claim:demo-shipped
    status: accepted
    type: achievement
    text: Built and shipped a robotics demo.
    evidence_refs: [ev_demo]
    skill_refs: [robotics]
    project_refs: []
    experience_refs: []
    source_refs: []
    output_refs: []
    public_readiness: draftable
    confidence: medium
    rationale: Derived from reviewed evidence.
    warnings: []
    generated_by: rule:evidence_review
    created: 2026-05-13
```

不变量：

- Claim `type` 只能是 `achievement`、`skill`、`impact`、`role`、`learning`、`project`。
- 持久化 claim 只保存 `accepted`；不保存 rejected 候选，避免早期审阅队列膨胀。
- Claim 去重键是 `normalized(text) + evidence_refs + skill_refs`；重复应用时更新已有 claim metadata，不追加重复行。
- Claim 可以引用多条 evidence；因此它放在 `evidence-pool.yaml.claims` 顶层，不嵌入单条 evidence row。
- 写入 claim 不自动修改 `skill-tree.yaml`，也不自动提升 skill status。
- `evidence_refs` 必须存在；未知 evidence ref 不能静默写入。未知 skill ref 必须报 warning 或被拒绝 / 丢弃后提示。
- Evidence pool 的编辑、压缩和保存路径必须保留未知顶层字段，尤其不能丢弃 `claims`。

### Kanban Done -> Evidence

```text
kanban Done task
  -> AI JSON patch (LLM or read-only Codex from Kanban)
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
- Blog front matter 可保存 `related_claims`、`related_sources`、`related_research_claims`、`related_citations`；发布校验会检查 accepted claim、research source visibility、promoted research claim 与 citation/chunk 断链。
- Project update 草稿和 resume bullet 候选也可从 accepted claims 生成，并保留 `related_claims` / `evidence_refs` provenance；resume bullet 第一版只返回候选预览，不自动写入 `resume-source.yaml`。
- 公开输出不直接渲染 claim/source/citation id；这些 refs 只用于 provenance、候选生成和发布前检查。

### Agent Activity / Writeback Review

```text
Review / owner page candidate
  -> agent-activity.yaml items[]
  -> pending / applied / failed / dismissed / superseded
  -> owner page or Activity apply
```

`agent-activity.yaml` 是内部候选、patch 和写回审阅队列，不参与 public build。
旧 profile 没有该文件时按空队列读取，首次写入时创建。

最小形态：

```yaml
schema_version: "1.0"
profile: 王军
updated: "2026-05-14"
items:
  - id: act:review:evidence:abc123
    kind: candidate
    candidate_type: evidence
    source_page: Review
    source_ref: review:2026-05-11:2026-05-14
    target_owner: evidence_pool
    status: pending
    title: Ship demo
    summary: demo shipped
    refs:
      task_refs: [done-demo]
      evidence_refs: []
      claim_refs: []
      files: [profiles/王军/evidence-pool.yaml]
    payload: {}
    preview: ""
    warnings: []
    error: ""
    changed_paths: []
    created: "2026-05-14T00:00:00+00:00"
    updated: "2026-05-14T00:00:00+00:00"
    applied_at: ""
```

不变量：

- `status` 只能是 `pending`、`applied`、`failed`、`dismissed`、`superseded`。
- `payload` 保存结构化候选或 patch，`preview` 保存短 YAML / diff / Markdown 摘要；不保存完整私密文件快照。
- `applied` 必须记录 `changed_paths` 和 `applied_at`；`failed` 必须记录 `error`。
- 第一版只有 Review 来源且 owner 为 evidence / kanban / public site 的 pending item 可在 Activity 页直接应用；其他 patch 只审查和跳转 owner 页面。
- 看板内 Codex 只读 AI backend 失败时，`source_page` 为 `Kanban`、`source_ref`
  为 `kanban:<task_id>`，并返回 `activity_item_id` 给看板错误卡片用于跳转。

### Web Preferences and Profile Codex Home

`profiles/<name>/web-preferences.yaml` 只保存非密钥使用习惯：

```yaml
schema_version: "1.0"
profile: 王军
updated: "2026-05-19T00:00:00+00:00"
ai:
  llm:
    provider: OpenAI
    base_url: https://api.openai.com/v1
    model: gpt-4o
    custom_model: ""
    ui_lang: zh
    reply_lang: en
  kanban_backend: codex
kanban:
  subtask_granularity: milestone
  subtask_style_hint: 带验证点的里程碑
```

不变量：

- `web-preferences.yaml` 不保存 API key、token、secret、password、authorization、cookie、`auth.json` 内容或 `config.toml` 原文。
- `profiles/<name>/codex.yaml` 只保存 nblane 的非密钥 Codex 参数，例如 `bin_path`、`cloud_env_id`、`model`、`attempts`、`branch`、`timeout_seconds`。
- Web 页面中的 Codex 使用 profile 专属 `CODEX_HOME`，默认根目录为 `~/.nblane/codex/profiles/`，目录名为 `<safe-profile>-<sha12>`；可用 `NBLANE_CODEX_HOME_ROOT` 覆盖根目录。
- Web Codex 的 `auth.json` 和 `config.toml` 位于该 profile 专属 `CODEX_HOME` 下，不放入 `profiles/<name>/`，不会影响终端默认 `~/.codex`。

## 新增 / 规划中的契约

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

### Research Workspace（已落地 P4 v1）

```text
research/sources.yaml
research/chunks/<source_id>.jsonl
research/claims.yaml
research/citations.yaml
research/drafts.yaml
research/drafts/<draft_id>.md
research/connectors.yaml
```

不变量：

- Research 默认 private。
- Claim 必须引用 source/chunk，或标记为 human note。
- `research/claims.yaml` 是 source-aware research claim store；`evidence-pool.yaml.claims` 仍是 accepted claim bridge，两者不合并。
- Citation 必须绑定 claim，并至少引用 source 或 chunk；quote 不能泄露本地 profile 路径、secret、token、cookie 等敏感内容。
- Research draft 可生成 blog candidate，但写入公开层仍是 draft；发布前必须检查 private source 和未 promoted research claim。
- `research/connectors.yaml` 只保存 provider、query、cursor、last_run、rate_limit、status 和 sanitized options；token、cookie、API key 不得写入 profile。
- X/Twitter 与小红书第一版以手动导入 / 官方授权为边界，不做 cookie 抓取。

### AI Run

```text
ai-runs/YYYY-MM-DD.jsonl
```

不变量：

- 默认不保存完整私密 prompt。
- 保存 task、model、input refs、output refs、status、warnings、accepted 状态。
- 用于审计和调试，不是业务事实源。
