---
status: active
owner: engineering
last_verified: 2026-09-24
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
| `plan-templates.yaml` | 习惯计划模板使用历史(按 template_id 去重) | 计划模板历史事实源 |
| `agent-profile.yaml` | Agent 对用户的结构化 prior | Agent prior 事实源 |
| `activity-log.yaml` | habit、checkin、weekly summary | 活动记录事实源 |
| `goals.yaml` | 阶段目标(title/status/target/summary/skill_links) | 目标事实源 |
| `chronicle.yaml` | append-only 叙事级事件 `{date, kind, ref, note}` | 大事记事实源;只由写端点追加,人不手改 |
| `learning-log.yaml` | paper/article/book/repo/course 等资源 | 学习资源事实源 |
| `inbox.yaml` | 捕获、澄清、归档的输入项 | 捕获入口事实源 |
| `public-profile.yaml` | 公开姓名、简介、联系方式 | 公开 profile 事实源 |
| `resume-source.yaml` | 可公开简历事实 | 简历事实源 |
| `projects.yaml` | 公开项目展示 | Public Surface 项目，不是内部项目管理 |
| `outputs.yaml` | 公开成果展示 | Public Surface 成果 |
| `public-library.yaml` | Public Site 后台文件树 | 编辑器组织层 |
| `blog/*.md` | 公开博客 Markdown | 博客正文和 front matter |
| `blog/*.blocknote.json` | BlockNote sidecar | 编辑器块状态，保存时可重建 Markdown |

## 北极星可见性(二元)与 SKILL.md 外科写入

自 2026-09-23(首页星图编辑设计 §1/§9)起,`SKILL.md` Identity 区的
`North Star Visibility` 是**二元**字段:

- 取值只有 `public` / `private`;读取侧
  `profile_context.normalize_north_star_visibility` 把旧四档映射进来:
  `visible` → `public`,`discreet` / `hidden` / 空 / 未知 → `private`。
- 语义:**只门控公开产物**(公开构建/拓片/分享)。本地 UI 与 agent
  上下文(openclaw、MCP、系统提示)永远看到全文——agent 看不到真实
  北极星就不可能给出真实计划。
- 写入只写 canonical 新值(`public`/`private`);`brief`
  保留为展示简称,不是隐私机制。

写入不变量(`core/north_star.py::update_north_star`):

- **外科手术式**:只改 `## Identity` 里 `- **North Star**` /
  `- **North Star Brief**` / `- **North Star Visibility**` 三行,
  文件其余部分逐字节不动,`sync.py` 生成块不受影响。
- 写路径持有 `SKILL.md` sidecar flock(与 sync.py / growth_log.py 同锁),
  支持 `expected_snapshot` 锁内复核,冲突抛 `FileConflictError`(API 412)。
- 值未变 = 完全 no-op:不写文件、不记 git backup、不追加 chronicle。
  visibility 按归一化后的二元值比较(存着旧 `discreet`、请求
  `private` 视为无变化)。

## 大事记 chronicle.yaml

append-only;每条 `{date, kind, ref, note}`。`core/chronicle.py` 的
`append_chronicle` 在锁内 reload → append → atomic write(追加天然可
合并),`expected_snapshot` 冲突时路由层用新快照重试一次。当前 kind:
`north_star.rewritten`、`goal.added`、`goal.completed`、`goal.renamed`、
`project.deleted`(2026-09-23 起,仅在删除项目时显式勾选「记入大事记」
才落笔,默认不记)、`habit.deleted`(2026-09-24,习惯删除同样默认不记,
`record_chronicle=true` 才落笔,ref = habit id,note = 习惯标题)、
`skill.lit`(2026-09-24,技能节点状态沿 locked→learning→solid→expert
升阶时自动落笔,降阶/no-op 不记,ref = 节点 id,note = schema 标签);
只在变化真实发生时落笔(重命名只在 title 变了时记,no-op 保存不记)。
消费者:首页简报行、拓片年度叙事、openclaw 复盘素材。

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

技能状态写端点（2026-09-24，G3）：
`PATCH /api/v1/profiles/{name}/skill-tree/nodes/{node_id}` 是 skill-tree.yaml 节点
状态的 UI 写路径。词汇表映射：UI/星图三态 `locked | learning | lit`，YAML 事实源
`locked | learning | solid | expert`（`core/profile_io.py STATUSES`）——端点把 `lit`
落为 `solid`;`expert`（精通）是评审授予的第四级，不可经此端点写入。写纪律与
skill-links 一致：`If-Match` 携带 skill-tree.yaml 弱 ETag（412 重试），写经
`profile_io.update_skill_tree` 的锁内快照复核；状态落盘后在 SKILL.md 存在时重写其
生成块（`write_generated_blocks`）。no-op patch 不写文件、不改 ETag。状态沿
`locked→learning→solid→expert` 真实升阶时追加 chronicle `skill.lit`
（降阶/no-op 不记;2026-09-24 起）。

技能进阶进度（同日落地,只读）:`GET /skill-tree` 每个节点带 `progress`
对象 `{score, next_rung, threshold_next, breakthrough_count, eligible}`,规则全部
集中在 `core/skill_progression.py`(唯一调参处,常量 + docstring):
节点非废弃 `evidence_refs` 逐条计分,分量 弱/中/强 = 1/10/100(`high_trust`
按强计,未评级按 1),`breakthrough: true` 的证据行额外 +1000;升阶阈值
locked→learning 10、learning→solid 30、solid→expert 100,expert 无下一阶
(`next_rung`/`threshold_next` 为 null);`eligible` = 存在下一阶 且
(score ≥ threshold_next 或 breakthrough_count ≥ 1)。eligible 只是升阶提示,
状态写入仍走上面的 PATCH 端点(三态词汇,`lit` 落 `solid`)。

证据按技能反查（同日）：`GET /api/v1/profiles/{name}/evidence?skill_id=<id>` 复用
`evidence_usage_index` 的反向映射（skill-tree.yaml `evidence_refs` 是唯一写侧），
与既有 `status/q/limit` 过滤正交组合；返回非废弃条目（默认 status 语义不变），
技能节点铭文卡的「关联证据」即读此过滤器。

### Evidence -> Claim Bridge

```text
reviewed evidence graph
  -> claim candidates
  -> human selection
  -> claims.yaml
  -> Output Studio related_claims / provenance
```

Web 中的通用 Evidence Claim 使用 profile 级 `claims.yaml` 作为事实源。
生成态候选只保存在会话预览中；只有用户点击应用后，才写入
`claims.yaml`。旧 `evidence-pool.yaml.claims` 只作为迁移前兼容读取和显式
迁移来源，新 claim 不再写回 evidence pool。

`claims.yaml` 允许的最小形态：

```yaml
schema_version: "1.0"
profile: alice
updated: 2026-05-19
claims:
  - id: claim:demo-shipped
    status: accepted
    refresh_status: current
    type: achievement
    text: Built and shipped a robotics demo.
    evidence_refs: [ev_demo]
    skill_refs: [robotics]
    project_refs: []
    goal_refs: []
    experience_refs: []
    source_refs: []
    output_refs: []
    public_readiness: draftable
    confidence: medium
    rationale: Derived from reviewed evidence.
    warnings: []
    generated_by: rule:evidence_review
    created: 2026-05-13
    updated: 2026-05-19
    last_reviewed: 2026-05-19
    supporting_evidence_signature: ""
    stale_reason: ""
    history: []
```

不变量：

- Claim `type` 只能是 `achievement`、`skill`、`impact`、`role`、`learning`、`project`。
- Claim `status` 使用 `draft`、`accepted`、`deprecated`、`dismissed`；Output Studio 默认只消费 `accepted`。
- Claim `refresh_status` 使用 `current`、`needs_refresh`；`accepted + needs_refresh` 可追溯，但生成输出时必须提示复核。
- Claim 去重键是 `normalized(text) + evidence_refs + skill_refs`；重复应用时更新已有 claim metadata，不追加重复行。
- Claim 可以引用多条 evidence；因此它放在 `claims.yaml` 顶层，不嵌入单条 evidence row。
- Claim 可以聚合 `project_refs` 与 `goal_refs`；`goal_refs` 可由 Project Case、Goal evidence refs 或 Research Source refs 派生，并允许人工修正。
- Accepted claim 不会因为新 evidence 静默改写；signature 变化只标记 `needs_refresh` 或生成 refresh proposal。
- 写入 claim 不自动修改 `skill-tree.yaml`，也不自动提升 skill status。
- `evidence_refs` 必须存在；未知 evidence ref 不能静默写入。未知 skill ref 必须报 warning 或被拒绝 / 丢弃后提示。
- Evidence pool 的编辑、压缩和保存路径必须兼容旧 `claims` 字段，迁移前不能意外丢弃；迁移后不再把新 claim 写回 evidence pool。

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

### Kanban 任务元数据字段

任务以 Markdown checkbox + 缩进 `key: value` 子弹存储于 `kanban.md`，唯一合法写路径是
`core/kanban_io.py`。除 `id/context/why/blocked by/outcome/tags/subtasks/todos` 外，日期类字段：

- `started_on` / `completed_on`：列移动习语自动维护（进 Doing 记 started_on，进 Done 记
  completed_on，离开 Done 清除）。
- `planned_start` / `planned_end`（2026-09-23 新增，可选）：**计划排期**，供 /projects 时间轴
  视图的拖拽改期；与列日期正交，不随列移动自动改写。写入经
  `POST /api/v1/profiles/{name}/kanban/cards/{card_ref}/schedule`（ISO `YYYY-MM-DD`，
  空串清除，两者皆设时 start ≤ end），随 kanban.md 正常 round-trip。
- `todos`（2026-09-24 新增，可选）：**任务内 TODO 清单**，每项一条 meta 子弹
  `- todo: [x] 已完成项` / `- todo: [ ] 待办项`（解析进 `KanbanTask.todos: list[KanbanTodo{text, done}]`，
  渲染在普通 meta 子弹之后、subtasks 嵌套 checkbox 之前）。与 `subtasks`（AI 起草的里程碑拆解）
  正交：todos 是用户自管的轻量清单。兼容规则：值不是 `[ ]`/`[x]` 开头的旧式 `- todo: 自由文本`
  行按 detail 处理（保存时走 `detail:` 转义，round-trip 稳定）。写入经
  `PATCH /api/v1/profiles/{name}/kanban/cards/{card_ref}` 的 `todos` 字段（**全量替换**，
  `[]` 清空，空文本项丢弃）；3-way merge 按 list 字段整体 diff/replay，随 kanban.md
  正常 round-trip，projects-board 聚合的 `todos` 供卡片进度（d/t）与详情卡清单使用。

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
- Web 页面中的 Codex 默认使用部署级 / 终端同款 `CODEX_HOME`（本地通常为 `~/.codex`，云上可用 `NBLANE_CODEX_HOME` 指向持久化目录）。
- Web Codex 的 `auth.json` 和 `config.toml` 位于部署级 Codex home 下，不放入 `profiles/<name>/`。旧 profile 隔离 Codex home 只在显式 `NBLANE_CODEX_HOME_POLICY=profile` 或请求体 profile policy 时用于诊断/复现。

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
- 里程碑 `status` 域为 `planned/active/completed/archived`，但真实数据目前全部停留在
  `planned`——没有「完成里程碑」的写路径；/projects 板的「过期 planned = 空心菱形」是
  展示层推导，不回写状态。
- /projects 聚合(`GET /api/v1/profiles/{name}/projects-board`，逻辑在
  `core/projects_board.py`)的泳道 Done 计数 = kanban.md Done + `kanban-archive.md`
  归档任务（按 `project_id`/`task_refs` 归属，任务侧为准）；`someday` 是徽章不是列；
  无 `project_id` 的任务进「未归属」泳道。
- 习惯打卡聚合(activity-log.yaml checkins)的 streak 口径：以今日结尾的连续打卡天数，
  今日未打卡则 streak = 0（与 Phase 2 概念稿 build_data.py 一致）。
- habit ↔ project 链接:**优先** project-board.yaml case 的显式 `habit_id` 字段
  (2026-09-23 新增,可选,case save/create API 可读写,空串清除);未设置时回落到
  「habit id/标题 归一化后等于 project 标题或 id 尾段」启发式。链接不上时 habit 仍以
  顶层 `habits[]` 输出,前端可自行配对。
- `kind` 域新增 `habit-plan`(2026-09-23):由习惯计划模板实例化产生(见下)。
- 习惯计划模板:内置模板随包发布(`core/data/habit_plan_templates.yaml`,
  `core/plan_templates.py` 加载);`POST .../plan-templates/instantiate` 实例化为
  `kind=habit-plan` 的 case(time_range = start + duration_days,里程碑日期 =
  start + offset_days,显式 habit_id 链接),缺 habit 时在 activity-log.yaml 创建,
  并写入 profile 的 `plan-templates.yaml` 使用历史(按 template_id 去重,最新在前)。
- 项目删除(2026-09-23,`DELETE .../project-board/cases/{case_id}`,
  phase2-projects-hci.md 裁决 3):
  - 请求体 `confirm_title` 必须与 case 标题逐字一致,否则 422
    `project_delete_confirm_mismatch`;`record_chronicle` 默认 false,
    为 true 时追加 `project.deleted`(note = 项目标题)。
  - 写入顺序 kanban.md → project-board.yaml(→ chronicle.yaml),两文件都在各自
    写锁内复核请求起始快照,冲突 412;走 `kanban_io.update_kanban` /
    `project_board.update_project_board`,不裸改文件。
  - 存活 kanban 任务的 `project_id` 清空回「未归属」;指向被删 case 里程碑的
    `milestone_id` 一并清空;`kanban-archive.md` 历史不动。
  - evidence-pool 的 `project_refs` **不清理**——墓碑机制负责展示;响应里的
    `evidence_refs_kept` 是池内仍引用该 case 的条目数,`tasks_unassigned`
    是被清空的存活任务数。删除前的后果预告由 projects-board 聚合自带数据
    支撑(每项目 `column_counts` + `evidence_ref_count`),无需独立预览端点。
- 习惯热力图(2026-09-23):projects-board 聚合的 `habits[]` 新增
  `recent_days`——近 90 天(今日含当日,窗口 = today-89..today)有打卡的
  `{date, count}` 列表,同日多行打卡 count 求和、按日期升序;`week` /
  `streak` / `total_checkins` 口径不变(total 仍数全历史去重天数)。
- 习惯生命周期(2026-09-24,activity-log.yaml):
  - `POST .../habits/{habit_id}/archive`(body `{archived: bool}`):可逆归档——
    habit 条目获得 `archived: true`(取消归档时键被移除),打卡历史原样保留;
    已归档习惯默认退出 projects-board `habits[]` 与 habit↔project 链接
    (`?include_archived=true` 可带回,行上标 `archived: true`)。与当前状态
    一致的请求是 no-op(`changed=false`,不写文件)。ETag/412 纪律同 checkins。
  - `DELETE .../habits/{habit_id}`(body `{confirm_title, record_chronicle=false}`):
    破坏性删除,裁决同项目删除——`confirm_title` 必须与习惯标题逐字一致,
    否则 422 `habit_delete_confirm_mismatch` 且不写任何内容;删除移除 habit
    条目及所有引用它的 checkin 行(响应 `{ok, deleted_id, checkins_removed}`),
    其他 habit 的行不动;`record_chronicle=true` 时追加 `habit.deleted`
    (默认不记)。核心实现 `core/activity_log.py` 的
    `set_habit_archived` / `delete_habit`,均走写锁 + 锁内快照复核。
- 证据 `breakthrough` 字段(2026-09-24,evidence-pool.yaml):可选 bool,
  默认 false(为 true 时才落盘),标记里程碑级证据;`EvidenceRecord`
  解析模型与 raw 路径(`load_evidence_pool_raw` / `update_evidence_pool`)
  双路 round-trip;可经单条编辑端点 `POST .../evidence/{id}/edit` 的
  `fields.breakthrough`("true"/"false",空串清除)读写,列表/详情 API
  投影均携带。计分作用见上文「技能进阶进度」。

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
- `research/claims.yaml` 是 source-aware research claim store；profile 根目录 `claims.yaml` 是通用 Evidence Claim store，两者不合并。
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
