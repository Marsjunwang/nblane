---

## status: active

owner: product
last_verified: 2026-05-12
source_of_truth: true

# Web 体验设计（Streamlit）

本文定义 nblane Web UI 的 **功能划分、页面职责、用户动线和交互边界**。它不是完整视觉规范，也不是操作手册；具体运行与操作见 [Web 使用手册](../guides/web-ui.md)。


| 项目   | 说明                                                                                         |
| ---- | ------------------------------------------------------------------------------------------ |
| 范围   | 本地 Streamlit：`app.py`、`pages/*.py`、自定义编辑组件                                                 |
| 产品对齐 | [产品总览](overview.md) 中的 `目标 -> 捕获 -> 执行 -> 证据 -> 技能图谱 -> 差距分析 -> 下一步行动 -> 公开输出 -> Agent 复用` |
| 非目标  | 替换 Streamlit 框架、设计完整 CSS 组件库、把 Web 做成托管公开站点                                                |


## 1. Web 的产品角色

Web 不是文件浏览器，也不是所有 YAML/Markdown 的可视化表单。它应该是用户每天打开的 **成长工作台**，帮助用户完成三件事：

1. 看清当前阶段目标、正在推进的任务、能力证据和短板。
2. 把日常输入、Done 任务、学习记录和项目进展低摩擦转成可审查 evidence。
3. 把可信 evidence 转成博客、项目页、简历、个人网站和 Agent 可复用上下文。

因此 UI 设计应遵守以下边界：

- **流程优先于文件名**：页面按用户任务组织，不按底层文件平均分配入口。
- **一个页面一个主对象**：每页有明确 owner，避免同一字段在多个页面都能随意写。
- **目标常驻**：当前 profile 和当前阶段 goal 应在主要工作流中可见。
- **AI 草稿优先**：AI 生成候选、补丁和建议；用户确认后才写事实源或公开发布。
- **公开层隔离**：Public Surface 只处理确认公开的字段，不直接暴露 private skill、kanban、research source。
- **源码可达但不喧宾夺主**：Raw YAML/Markdown 是高级入口，不应占据新用户首屏。

## 2. 功能域划分

UI 应围绕成长闭环拆成以下功能域。每个功能域只负责自己的主对象和写入边界。


| 功能域               | 主对象 / 文件                                                                                   | 用户任务                                                          | 页面归属                             |
| ----------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------- | -------------------------------- |
| Dashboard         | 只读聚合，读取 profile / goal / kanban / evidence / public                                        | 60 秒内知道当前状态和下一步                                               | 首页                               |
| Goal & Plan       | 规划中：`goals.yaml` 或 project refs                                                            | 设定 4-8 周阶段目标、目标技能、目标输出和验收证据                                   | 新 Goal 页；短期可放首页                  |
| Profile Context   | `SKILL.md`，读取 goal / skill-tree / kanban generated blocks                                  | 维护长期自我画像、North Star、研究品味和 Agent 可复用上下文                        | 首页高级区；未来 Profile Context 页       |
| Capture Inbox     | `inbox.yaml`、`learning-log.yaml`、`activity-log.yaml`、Done tasks                            | 捕获链接、笔记、学习、打卡、项目进展，等待整理                                       | 全局入口 / 首页 / 看板；未来独立 Inbox        |
| Execution         | `kanban.md`、规划中：`project-board.yaml`                                                       | 管理本周任务、子任务、阻塞、完成记录和 check-in                                  | 看板                               |
| Evidence          | `evidence-pool.yaml`、`skill-tree.yaml` 的 `evidence_refs`                                   | 审核 evidence、判断强弱、关联 skill、准备公开输出                              | 技能树；未来独立 Evidence 页              |
| Skill Map         | `skill-tree.yaml`、`schemas/*.yaml`                                                         | 浏览和编辑能力状态、备注、证据引用                                             | 技能树                              |
| Gap & Next Action | gap result、AI candidate，不直接作为事实源                                                           | 用目标/任务对照 skill tree，生成短板解释和下一步行动                              | 差距分析                             |
| Agent Activity    | context preview、MCP 状态、agent runs、AI/Agent candidates、writeback queue                      | 审阅 Codex / Claude Code / OpenCode 等 Agent 的远程执行、patch、写回和越权风险 | 未来 Agent Activity；短期分散在各页面审阅区    |
| Research          | 规划中：`research/sources.yaml`、chunks、claims、drafts、connectors                                | 搜集外部资料、收藏、最新论文、repo，支持阅读、翻译、claim/citation/synthesis          | 未来 Research 页                    |
| Output Studio     | `public-profile.yaml`、`resume-source.yaml`、`blog/`、`projects.yaml`、`outputs.yaml`、`media/` | 从 evidence 生成博客、简历、项目页、公开站                                    | Public Site                      |
| Team Pool         | `teams/<id>/team.yaml`、`product-pool.yaml`                                                 | 团队共享问题、项目、证据、方法、决策                                            | 团队视图                             |
| Profile Health    | 校验报告、sync drift、上下文发布风险                                                                    | 检查缺证据、Done 未结晶、公开层风险、上下文可用性                                   | Profile Health                   |
| Review            | weekly / monthly / stage review candidates                                                 | 从复盘生成 evidence candidate、next action、public candidate         | 未来 Review；短期可与 Profile Health 合页 |


核心规则：**跨域写入必须显式进入候选/预览**。例如 Done -> evidence 可以在看板发起，但应展示将写入哪些 evidence row、哪些 skill refs、是否允许 status change。

## 3. 推荐导航

当前 Streamlit 通过 `app.py` + `pages/` 自动形成导航。目标信息架构应按用户心智分组：

```text
Home
  - Dashboard
  - Current Goal
  - Pending Evidence
  - Profile Context

Work
  - Kanban
  - Inbox / Check-in
  - Project Board
  - Agent Runs

Growth
  - Skill Tree
  - Gap Analysis
  - Agent Activity
  - Review / Health
  - Research Workspace

Output
  - Public Site
  - Blog
  - Resume
  - Projects

Team
  - Team Pool
```

这是目标信息架构，不代表原生 Streamlit `pages/` 自动导航已经支持二级分组。短期不一定新增所有页面，可继续用 `pages/` 文件编号近似排序；长期可考虑 `st.navigation` 或自建导航，以支持 Home / Work / Growth / Output / Team 分组。

短期导航顺序应逐步从“文件模型顺序”调整为“成长闭环顺序”：

```text
首页 -> 看板 / Capture -> 待整理证据 -> 技能树 -> 差距分析 -> 公开输出 -> Research -> Agent Activity -> 团队视图 -> Profile Health
```

原因：多数日常会话先判断当前目标，再进入执行、捕获、证据整理、能力判断和公开输出。技能树是能力事实源，不应成为所有新用户的唯一入口；`Claim` 也不应过早独立成页面，而应先内嵌在 Evidence Review 和 Output Studio 中。

`Current Goal` 不应只是 Home 下的普通 tab。它是全局上下文，应在 Dashboard、Kanban、Skill Tree、Gap Analysis、Evidence、Output 等主要工作流中可见；短期可在侧栏 profile 选择器附近或页面顶部 status strip 展示当前 goal 摘要。Goal 常驻指上下文常驻，不等于目标标题和细节必须明文常驻。

`SKILL.md` 不应消失，但也不应作为首页首屏主对象。它是 Agent Context 的叙事出口和长期自我画像，短期可放在首页高级区，长期可独立为 Profile Context 页面。

## 4. 页面职责

### 4.0 贯穿全局的交互约束

以下约束跨越具体页面，不属于单一页面的局部职责：

- **当前 Goal 常驻但可隐藏**：当前阶段目标是所有推荐、gap、证据优先级和输出建议的锚点；除 Home 外，主要工作流也应能感知当前 goal。但“常驻”不等于明文常驻。用户可以按 goal 设置 UI 展示级别：`visible` 显示完整标题和细节，`discreet` 显示替代标签和状态，`hidden` 只显示“目标已设置”，`private` 默认不显示且不进入 Agent context。UI visibility、Agent context visibility、Public output visibility 必须分开控制。
- **全局 Capture 入口**：捕获一条链接、笔记、学习记录或想法不应要求用户先找到正确页面；短期可从首页轻量 capture bar 起步，长期应成为全局入口。
- **外部信息默认进入 Research / Capture**：小红书、X/Twitter 收藏、arXiv、Semantic Scholar、GitHub、网页、RSS 等外部资料先进入 Source Inbox 或 Capture Inbox；收藏、翻译和摘要不直接写 skill status、evidence 或 public output。
- **Agent 写回审阅入口**：跨页面 AI/Agent 生成的候选、patch、状态更新和写回结果应有统一可审查入口，避免用户只能在各页面分散追踪。
- **远程 Agent 执行默认进入审阅队列**：Codex、Claude Code、OpenCode、Cursor 等外部 Agent 可以协助完善项目，但其运行记录、触达文件、diff、候选写回必须进入 Agent Activity / Writeback Review；不能静默改事实源或公开层。
- **Team scope 硬提示**：Team View 的写入目标必须以 scope strip、色带或写入路径提示明确标出；个人 profile 只能作为 view-as / filter 上下文，不能被误解为团队数据 owner。

### 4.1 首页：Daily Dashboard

首页应该回答「我现在该做什么」，而不是承担完整 `SKILL.md` 编辑器职责。

首屏建议：

- 当前档案、North Star 摘要、当前阶段目标、AI 配置状态、文件健康状态。
- 本周正在推进的 3-5 个任务。
- 待整理 evidence：Done 任务、learning log、activity log、inbox。
- 待读 / 待处理 research sources：最新论文、收藏、repo、网页、社交资料。
- 待审阅 Agent activity：远程执行、patch、失败写回、审批队列。
- skill gap 摘要：与当前 goal 相关的缺口，而不是全量 skill tree。
- 输出机会：哪些 evidence 可转成博客、项目更新、简历 bullet。

主操作：

- 添加一条 capture。
- 打开当前 goal。
- 打开看板。
- 整理 Done -> evidence。
- 从 evidence 生成输出草稿。
- 打开 Research Inbox / Reading Room。
- 打开 Agent Activity 审阅候选 patch。
- 打开 Profile Context 高级区。

短期调整：

- 现有 `SKILL.md` 章节编辑保留，但应降级为「Profile Context / SKILL.md」高级区。
- capture 应是首页最轻的输入路径：标题 / 链接 / 简短备注即可进入 inbox，后续再整理。
- 长篇 `home_nav` 不应占据首屏；改为紧凑链接或放入折叠区。
- 简历/长文本摄入可以留在首页，但应定位为「批量导入 profile evidence」而不是首页主任务。
- 首页只展示 `SKILL.md` 的 North Star / Agent Context 状态摘要；完整编辑不进入首屏。

### 4.2 Goal：阶段目标

Goal 是当前 UI 的最大缺口。没有 goal，差距分析、热点筛选、证据优先级和输出建议都会变散。

目标页应支持：

- 标题：例如「8 周内完成一个 Agent 项目并写 3 篇文章」。
- 时间：start / target date。
- 目标领域和目标技能。
- 成功标准：需要哪些 evidence、artifact、公开输出。
- 当前 focus：本周最重要的 1-3 个行动。
- 关联任务、证据、博客、项目和简历条目。

短期实现可以先不新增 `goals.yaml`，在首页或看板中以轻量字段承载 current goal；长期应成为一等对象。

North Star 与 Goal 的关系：

- North Star 是 3-5 年整体方向，适合留在 `SKILL.md` 的 Identity / Profile Context 中。
- Goal 是 4-8 周阶段目标，必须有 success criteria、target skills、evidence / artifact / public output 验收。
- Kanban task 是本周执行项，应能指向当前 goal，但不替代 goal。
- Evidence 反向证明某个 goal 推进了 North Star。

Goal privacy：

- `ui_visibility` 控制 Web UI 是否明文展示 goal：`visible` 完整显示，`discreet` 显示替代标签，`hidden` 只显示“目标已设置”，`private` 默认不显示。
- `include_in_agent_context` 控制 `nblane context`、MCP 和 AI prompt 是否可读取 goal；`private` goal 默认不进入 Agent context，除非用户显式解锁。
- `include_in_public_output` 控制公开输出是否允许引用 goal；默认应为 `false`，公开层不能因为 UI 可见就自动读取 goal。
- 隐私模式下，全局 goal 条默认使用 `discreet` 或 `hidden` 展示；内部排序和推荐仍可使用 goal，除非该 goal 标记为 `private`。
- UI 隐藏不等于删除 goal，也不等于停止用 goal 做 Dashboard 排序、gap、evidence 优先级和输出建议。

### 4.3 Profile Context / SKILL.md

`SKILL.md` 是 Agent Context 的叙事出口，不是所有事实源的主编辑器。

页面职责：

- 编辑 Identity、North Star、North Star pillars、Research Fingerprint、Thinking & Communication Style、Growth Log。
- 预览由 `skill-tree.yaml`、`kanban.md`、未来 `goals.yaml` 生成的上下文摘要。
- 显示 generated block drift、sync 状态和 Agent Context 是否可发布。
- 提供高级 Raw Markdown 编辑入口。

推荐编辑模式：

- **结构化编辑**：Identity、Domain、Journey、Current Role、North Star 等短字段用表单。
- **章节编辑**：Research Fingerprint、Thinking Style、Growth Log 等长期叙事用 Markdown section 编辑。
- **生成块只读**：`BEGIN GENERATED:skill_tree`、`BEGIN GENERATED:current_focus` 等块只读；修改入口跳转到 owner 页面。
- **原文编辑**：保留 Raw Markdown，但默认折叠，并提示可能造成 generated block drift。

边界：

- 不直接编辑 skill status；去技能树页修改 `skill-tree.yaml`。
- 不直接编辑 current focus；去看板页修改 `kanban.md`。
- 不直接编辑 evidence refs；去技能树或未来 Evidence 页修改。
- 不承载 4-8 周阶段目标事实源；阶段目标进入 Current Goal / `goals.yaml`。
- 不直接编辑 public profile、resume 或 blog 正文。

`SKILL.md` 在 Agent 中的作用：

- 让外部 Agent 理解用户是谁、长期想成为什么、当前上下文是什么。
- 提供研究品味、沟通风格、判断标准和已同步的能力摘要。
- 作为 `nblane context` / MCP profile resource 的人类可读上下文层。

### 4.4 看板：Execution Workspace

看板负责执行，不负责长期能力建模。

页面职责：

- 管理 Doing / Queue / Done / Someday。
- 维护任务背景、阻塞、子任务、开始/完成日期。
- 支持 learning/exercise/check-in 等日常记录。
- 支持 AI 生成子任务、任务对齐、gap preview。
- 支持 Done -> evidence 的候选生成、审阅和应用。

边界：

- 看板可以发起 evidence 候选，但不能静默升级 skill status。
- 看板不直接编辑 public profile、resume 或 blog 正文。
- 执行记录应尽量转成 evidence 或 archive，避免 Done 长期堆积。

### 4.5 技能树：Skill Map + Evidence Linking

技能树页负责能力状态和证据引用。

页面职责：

- 按 schema 分类展示 skill。
- 编辑 status、note、inline evidence。
- 维护 evidence pool 和 `evidence_refs`。
- 显示每个 skill 的证据数量、证据类型和引用状态。
- 提示 solid/expert 但缺 evidence 的节点。

边界：

- skill status 是强判断，必须人工确认。
- AI 只能生成候选状态变更。
- 复杂 evidence triage 未来应迁到独立 Evidence 页，避免技能树页过重。

未来 Evidence 页可以承载：

- evidence inbox。
- evidence strength：弱证据 / 中证据 / 强证据 / 高可信证据。
- public readiness：私有、可整理、可公开、已发布。
- evidence -> skill / project / output 的批量关联。

### 4.6 差距分析：Gap & Next Action

差距分析页是 Agent OS 的主要交互面。它不只是“输入任务跑分析”，而应服务当前 goal。

页面职责：

- 输入当前任务或从 goal / kanban task 选择上下文。
- 将任务路由到相关 skill nodes。
- 展示 matched skills、gap skills、依赖闭包和优先级。
- 生成下一步行动：学习、实现、复盘、写作、公开输出。
- 生成 skill status 更新候选。
- 与 AI 教练对话，但结论应能回到 task/evidence/action。

边界：

- 默认只读分析；写回 skill-tree 必须用户勾选确认。
- 不做泛泛聊天；回答应绑定 goal、task、skill 或 evidence。
- 未配置 AI 时仍提供规则分析和清晰空状态。

### 4.7 Agent Activity / Writeback Review

Agent Activity 是 Agent OS 的透明度和审阅入口，不是新的泛聊天页。

页面职责：

- 展示当前 profile / goal 的 context 预览状态。
- 展示 MCP 连接、可用 resources / tools、最近外部 Agent 访问概况。
- 汇总看板、差距分析、技能树、Public Site 等页面产生的 AI/Agent candidates。
- 审阅 Codex / Claude Code / OpenCode / Cursor 等外部 Agent 的 run：任务、状态、触达文件、diff、日志摘要、关联 goal / kanban task。
- 审阅最近的 AI patch、候选写回、失败写回和审批队列。
- 支持远程完善项目的最小闭环：从 Project Board / Kanban 领取任务，Agent 执行，用户审阅 patch，合并后回到 Done -> evidence。
- 帮助用户判断 Agent 最近做了什么、准备写什么、是否越权。

边界：

- Agent Activity 默认不直接生成新的业务内容；它负责透明度、审阅和跳转。
- 所有写回仍由各 owner 页面执行，或通过统一候选 / 预览 / 确认流程执行。
- Agent run 的输出不能绕过 git diff / preview / 人工确认，尤其是代码、profile、evidence、public 文件。
- 不做泛泛聊天；对话型能力应绑定 goal、task、evidence、output 或具体 patch。

### 4.8 Research Workspace

Research Workspace 支撑 source-aware 阅读、论文分析和研究写作。

页面职责：

- **Discovery**：按 current goal 搜集最新论文、repo、网页、社交收藏和外部热点。
- **Source Inbox**：接收小红书、X/Twitter、arXiv、Semantic Scholar、Papers With Code、GitHub、RSS、手动粘贴链接等来源。
- **Reading Room**：支持论文 / 网页阅读、中文翻译、摘要、术语解释、方法梳理、贡献与局限分析。
- 管理 sources：论文、网页、书、repo、访谈、内部资料等来源。
- 管理 chunks：可引用的摘录、段落、图表、实验设定和数据片段。
- 管理 claims：从 source / chunk 提炼出的事实、观点、假设和待验证判断。
- 管理 citations：claim 与 source / chunk 的引用关系。
- 管理 synthesis drafts：围绕当前 goal 或写作主题形成的综合草稿。
- 管理 connectors：外部平台连接状态、授权方式、手动导入 fallback 和数据隐私提示。

边界：

- Research 不直接发布博客、简历或公开项目页。
- Research 产物进入 Output Studio 时必须是候选 / 预览态，并保留 citation / source 线索。
- 未形成 claim 或 evidence 的阅读记录仍属于 capture / learning log，不应提前污染 skill status。
- 收藏、翻译、摘要和阅读笔记默认不是强 evidence；复现、实验、项目使用、公开复盘等经过确认后才进入 evidence。
- 外部平台 connector 不应把 cookie / token 明文写入 profile；导入内容默认 private。

### 4.9 Public Site：Output Studio

Public Site 页应被理解为 Output Studio：把可信 evidence 变成公开表达。

页面职责：

- Profile：公开姓名、headline、简介、联系方式、头像。
- Blog：草稿、正文、媒体、AI patch、发布检查、预览。
- Resume：`resume-source.yaml`、定制简历草稿、Markdown 预览。
- Projects / Known Info：把 evidence 聚合成公开项目和成果。
- Build：校验并构建静态站。

边界：

- 只读取显式公开层文件和经过用户选择的 evidence refs。
- 发布前检查 private source、缺 evidence、unsupported claim。
- Blog AI 和视觉候选必须是候选态，接受后才写正文或 media。

长期可拆分：

- `Output Studio`：博客、项目、简历内容生产。
- `Public Site Build`：导航、主题、SEO、构建和部署。

### 4.10 Team View：Team Pool

团队视图负责 `teams/`，不是当前 profile 的子页面。

页面职责：

- 编辑团队 mission、members、shared rules、priorities。
- 维护 problem/project/evidence/method/decision pools。
- 支持把个人 evidence 或方法沉淀到团队共享池。

边界：

- 侧栏 profile 只表示当前个人上下文；团队数据不应被误解为按 profile 过滤或写入。
- 页面首屏必须用 scope strip、色带或写入路径提示明确当前写入的是 `teams/<id>/`。
- 如果未来需要按成员过滤，应显式使用 profile 作为 view-as / filter，而不是隐式影响数据 owner。
- 团队写回也必须遵守候选 / 预览 / 确认流程，尤其是从个人 evidence 沉淀到团队共享池时。

### 4.11 Profile Health

Profile Health 是只读体检页，负责判断当前 profile 是否健康、可信、适合提供给 Agent。

页面职责：

- 检查 YAML/Markdown 健康、生成块漂移、缺 evidence、Done 未结晶。
- 展示 context 是否适合提供给 Agent。
- 提示 public layer 是否有泄露、缺字段或 unsupported claim 风险。
- 将修复动作跳转到 owner 页面。

边界：

- 默认只读，不直接承担复杂编辑。
- 不生成新的 evidence；只提示缺口和风险。
- 不替代 Review 的阶段复盘职责。

### 4.12 Review

Review 是阶段 / 周 / 月复盘入口，负责把完成记录整理成候选，而不是只做健康检查。

页面职责：

- 聚合 Done 任务、learning log、activity log、inbox、public output 和 health findings。
- 生成 evidence candidates、next action candidates、public candidates 和 method notes。
- 支持 weekly / monthly / stage review。
- 帮助用户判断哪些完成记录值得结晶、归档、公开或继续行动。

边界：

- Review 生成候选，不静默写入 `evidence-pool.yaml`、`skill-tree.yaml` 或 public 文件。
- 采用与 Done -> evidence 一致的候选 / 预览 / 确认流程。
- 短期可以与 Profile Health 合页实现，但文档职责应保持拆分。

## 5. 首屏和交互规则

### 5.1 页面首屏统一结构

每个页面首屏应包含：

- `title`：功能名，不混入文件名。
- `caption`：一句话说明该页属于 Private OS、Agent OS、Team OS 或 Public Surface。
- `scope`：当前 profile / team / goal。
- `primary action`：一个最重要的操作按钮或输入。
- `status strip`：AI 配置、文件冲突、未保存、健康风险等必要状态。

不要在每页首屏堆长说明。详细解释放到帮助文档、折叠区或页面底部。

全局入口：

- 当前 goal 摘要应在侧栏或页面顶部可感知，不能只藏在 Home；敏感 goal 可用替代标签或“目标已设置”展示。
- capture 入口应跨页面可达；短期可以只落在首页首屏，但交互上应足够轻。
- Agent 写回审阅入口应能汇总跨页面候选和最近 patch。
- Team 页面必须显示当前写入路径和团队 scope。

### 5.2 写入流程

所有会改变事实源的操作按同一模式：

```text
输入 -> 生成候选 -> 预览 diff / YAML -> 人工确认 -> 写入 -> git backup -> rerun
```

适用场景：

- resume / long text -> evidence。
- Done -> evidence。
- gap -> skill status update。
- Agent candidate -> owner page patch。
- evidence -> blog / resume / project draft。
- AI patch -> blog body。
- public profile private -> public。
- Profile Context section edit -> `SKILL.md`。

生成块写入规则：

- `SKILL.md` 中 generated block 默认只读，由 owner 页面或 sync 流程更新。
- `skill_tree` 生成块的 owner 是技能树 / sync。
- `current_focus` 生成块的 owner 是看板 / sync。
- 未来 goal 摘要生成块的 owner 是 Current Goal / sync。
- Raw Markdown 编辑可以保留，但保存后必须提示 drift 风险，并由 Profile Health 检查。

### 5.3 空状态

需要统一的空状态：

- 无 profile：引导创建 profile。
- 无 goal：引导创建阶段目标。
- 无 evidence：引导从 Done、learning log、inbox 或手动新增。
- 未配置 AI：说明规则模式仍可用，以及如何开启 AI。
- 无 public layer：引导初始化公开层。
- 有文件冲突：提示 reload / review，不覆盖磁盘变更。

### 5.4 命名

中文界面应优先使用用户能理解的结果名：


| 不推荐             | 推荐         |
| --------------- | ---------- |
| Raw             | 原文 / 源码    |
| Ingest          | 导入并生成证据    |
| Public Surface  | 公开输出       |
| Gap Analysis    | 差距分析       |
| Profile         | 档案 / 个人上下文 |
| Profile Context | 个人上下文      |
| Evidence Pool   | 证据池        |
| Team Pool       | 团队共享池      |


底层文件名可以作为辅助说明出现，例如「写入 `evidence-pool.yaml`」，但不应作为主要按钮文案。

## 6. UI 开发优先级与实施顺序

Web UI 的开发顺序不应按当前页面编号，也不应按“哪个页面最显眼”来排，而应按成长模型的对象依赖来排：

```text
Goal
  -> Activity / Source capture
  -> Evidence review
  -> Claim
  -> Skill / Gap
  -> Output
  -> Governance / Research / Team scale
```

原因很直接：

- `Evidence` 是成长模型的核心沉淀层，应早于复杂 Research、Public Site 拆分或 Team 协作优化。
- `Claim` 介于 Evidence 与 Skill / Output 之间，短期应先做成审阅流里的候选卡片，而不是急着做独立页面。
- `Research`、`Agent Activity`、`Team View` 属于 source specialization 或 governance scale，应该复用前面已经打通的候选 / 预览 / 确认机制。

### 6.1 推荐阶段顺序

| 阶段 | 核心对象 | 优先开发 | 为什么先做 |
|------|----------|----------|------------|
| P0 | Goal + Dashboard + Capture + Execution | 增加 current goal 常驻入口；Goal 隐私展示；首页改成 Dashboard；全局 capture 入口；Done -> evidence 统一入口；统一页面顶部 profile / scope strip | 没有目标锚点、输入入口和执行闭环，后面的 evidence、gap 和 output 都会发散 |
| P1 | Evidence Core | 独立 Pending Evidence / Evidence Review 入口；技能树页突出 evidence strength / missing evidence；统一 review preview / apply 流；最小 project / experience refs | `Evidence` 是成长模型中心层，必须先把证据变成一等对象，而不是继续藏在技能树细节里 |
| P2 | Claim + Skill + Gap + Review | 在 Evidence Review 中生成 claim candidates；差距分析支持从 goal / task 带入上下文；Review 候选入口与 Health 拆责；技能状态与 claim / evidence 更明确联动 | `Claim` 把“发生了什么”翻译成“证明了什么”，它是 Skill 和 Output 可复用的桥 |
| P3 | Output Studio | Public Site 强化“从 evidence / claim 生成输出”；Resume / Blog / Project 草稿显式显示 provenance；Profile Context 保持高级区定位 | 公开输出应建立在可追溯 evidence / claim 上，而不是先做内容 CMS 再回头补来源 |
| P4 | Research / Agent / Team / Connectors | Research Source Inbox 与 Reading Room；Agent Activity / Writeback Review；Team View scope hardening；外部 connector 自动化；Output Studio 与 Build 拆分 | 这些能力要么是 source specialization，要么是治理与扩展层，应该建立在通用审阅框架已经稳定之后 |

### 6.2 具体调整建议

| 新优先级 | 调整 | 目标 |
|----------|------|------|
| P0 | 增加 current goal 常驻入口或轻量 goal 模块 | 让 gap、evidence、output 有共同方向 |
| P0 | Goal 隐私展示：visible / discreet / hidden / private | 保留目标上下文价值，同时避免敏感目标在投屏、录屏或旁人可见时泄露 |
| P0 | 首页改成 Dashboard，降低 `SKILL.md` 编辑权重 | 新用户快速知道当前状态和下一步 |
| P0 | Profile Context 高级区：结构化编辑长期画像，生成块只读 | 保留 Agent Context 价值，同时避免首页变成 Markdown 编辑器 |
| P0 | 全局 capture 入口或首页轻量 capture bar | 让日常输入不依赖用户先找到正确页面 |
| P0 | Done -> evidence 审阅体验统一 | 打穿最小成长闭环 |
| P0 | `st.title` / `select_profile` / scope strip 顺序统一 | 先解决“当前是谁、当前目标是什么、写入哪里”这三个认知问题 |
| P1 | 独立 Pending Evidence / Evidence Review 页 | 提升 evidence 在 UI 中的地位，降低技能树页复杂度 |
| P1 | 技能树页突出 evidence strength / missing evidence | 避免 status 变成主观自评 |
| P1 | 最小 project / experience refs 编辑入口（已落地） | 为 Composite Evidence、Resume 和 Project Case 聚合打基础 |
| P1 | Research Source Inbox 最小入口（已落地） | 让外部资料先进入 source inbox，不直接污染 evidence |
| P2 | 在 Evidence Review / Output Studio 中生成 claim candidates | 先让 claim 成为桥接层，而不是先做 claims 独立页面 |
| P2 | 差距分析支持从 goal / kanban task 带入上下文 | 减少重复输入，提高行动建议质量 |
| P2 | Review 候选生成入口，与 Profile Health 职责拆开 | 让复盘成为 evidence / next action / public output 的来源 |
| P2 | Agent Activity / Writeback Review 骨架 | 让跨页面 Agent 候选、patch 和写回状态可审查 |
| P3 | Public Site 强化“从 evidence / claim 生成输出”入口 | 让公开站不是独立内容 CMS |
| P3 | Research Reading Room：翻译、摘要、claim 提取 | 把论文和网页从“收藏”推进到可引用的 claim / citation / synthesis |
| P3 | Team View scope hardening | 用硬性 scope 标识避免用户误解数据写入位置 |
| P4 | Research Workspace 完整页面 | 支撑 source-aware blog、研究写作、source / chunk / claim / citation 全链路 |
| P4 | 外部 connector 自动化：X/Twitter、小红书、arXiv、Semantic Scholar、GitHub 等 | 在权限、速率限制和隐私边界明确后，再做自动导入和订阅 |
| P4 | Output Studio 与 Build 拆分 | 降低 Public Site 单页复杂度 |

### 6.3 不建议先做的事

- 不建议先做完整 Research Workspace，再回头补通用 Evidence Review。研究资料也是 source，应该先复用统一候选流。
- 不建议先把 Public Site 做成复杂 CMS，再回头补 provenance。输出必须能追溯 evidence / claim。
- 不建议先做 claims 独立页面。短期 claim 更适合作为 Evidence Review 和 Output Studio 的中间层对象。
- 不建议把 Agent Activity 放到最前面。治理层应建立在核心成长闭环已经可用之后。

### 6.4 P1 当前落地状态

以下 P1 已有最小可用实现：

- `project-board.yaml`：内部 Project Case 事实源，用于承载私有项目上下文，不替代公开层 `projects.yaml`。
- `experience.yaml`：内部 Experience Case 事实源，用于承载组织、角色、时间段和求职视角上下文，不替代 `resume-source.yaml`。
- `research/sources.yaml`：Research Source Inbox 事实源；首页 capture 与 Research 页写入这里，不直接写 evidence、skill status 或 public output。
- Evidence Review 已支持编辑 evidence row 的 `project_refs`、`experience_refs`、`source_refs`，并提供最小 Project / Experience case 编辑入口。
- Dashboard / Workspace Graph 已能读取 research source 和 project case；私密 project title 不进入 graph payload。
- Profile Health 已对内部 workspace refs 做 dangling warning，不阻断 context 发布。


## 7. 已知摩擦与 backlog


| 项                                | 说明                                                                       | 标签         |
| -------------------------------- | ------------------------------------------------------------------------ | ---------- |
| 首页偏 `SKILL.md` 编辑                | 与 Dashboard 角色冲突，应把编辑降级为 Profile Context 高级区                             | 需改代码       |
| `SKILL.md` 角色不清                  | 应明确为 Agent Context 叙事出口，而非 skill / evidence / task / goal 的事实源           | 需文档 / 需改代码 |
| generated block 编辑边界             | `skill_tree`、`current_focus` 应只读并跳转 owner 页面，Raw 保存后提示 drift             | 需改代码       |
| 缺少 Goal 对象入口                     | 当前 UI 无阶段目标，导致推荐和 gap 缺少锚点；Goal 应全局常驻而非普通 Home tab                       | 需设计 / 需改代码 |
| Goal 明文常驻有隐私风险                   | 目标应支持 UI 隐藏、Agent context 隐藏和 public output 隔离，常驻上下文不等于明文展示              | 需设计 / 需改代码 |
| Capture 入口偏弱                     | 捕获应跨页面低摩擦进入 inbox，而不是只作为首页普通操作                                           | 需设计 / 需改代码 |
| 外部研究资料入口缺失                       | 最小 Research Source Inbox 已落地；后续仍需 connector、Reading Room、claim / citation 链路         | 已有最小实现 / 后续增强 |
| 论文阅读与翻译链路缺失                      | 需要 Reading Room 承载翻译、摘要、术语解释、claim 提取和 citation，而不是塞进 Public Site        | 需设计 / 需改代码 |
| Agent 写回审阅分散                     | AI/Agent candidates 分散在看板、差距、技能树、Public Site，缺统一审阅入口                     | 需设计 / 需改代码 |
| 远程 Agent 执行缺少项目闭环                | Codex / Claude Code 等远程改项目应关联 Project Board / Kanban task，并进入 patch 审阅   | 需设计 / 需改代码 |
| 外部 connector 隐私和授权边界             | X/Twitter、小红书等平台应支持手动导入 fallback，cookie / token 不得明文写入 profile           | 需设计 / 需改代码 |
| Team View + Profile              | `select_profile()` 已显示但团队数据写入 `teams/`，需用硬性 scope 标识区分 view-as 与写入 owner | 需改代码       |
| `st.title` / `select_profile` 顺序 | 页面顺序不一致，影响「当前是谁的上下文」认知                                                   | 需改代码       |
| 首页标签 `NBL` vs `nblane`           | 品牌串需要统一                                                                  | 需改代码       |
| 中文导航纯净度                          | `home_nav` 等文案中仍有英文页名                                                    | 需改代码       |
| 未配置 AI 的提示                       | 应统一成共享空状态组件或同一组 i18n key                                                 | 需改代码       |
| Emoji 密度                         | 可选无 emoji 模式已有基础，但页面使用还需收敛                                               | 需改代码       |
| Health / Review 职责混合             | Health 应默认只读，Review 应生成候选；短期可合页但职责需拆清                                    | 需设计 / 需改代码 |
| Public Site 单页过重                 | Blog / Resume / Projects / Build 功能密度高                                   | 后续拆分       |
| 推荐动线 vs 页面编号                     | 当前 `1_`-`6_` 顺序偏文件模型，可逐步按日常动线重排                                          | 需改代码       |


## 8. 相关文档

- [产品总览](overview.md) — nblane 的用户、核心闭环和产品分层
- [核心闭环](core-loop.md) — 捕获、执行、证据、输出、Agent 复用流程
- [路线图](roadmap.md) — 阶段交付顺序
- [当前状态](../project/status.md) — 已实现能力和主要缺口
- [Web 使用手册](../guides/web-ui.md) — 运行方式、页面操作和 CLI 对照
- [公开站点指南](../guides/public-site.md) — Public Surface 细节
