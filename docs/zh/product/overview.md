---
status: active
owner: product
last_verified: 2026-10-07
source_of_truth: true
---

# 产品总览

nblane 是一个 Human + Agent 共进化系统：面向 AI-native 研究者和开发者的本地优先个人成长工作台。它把阅读、写作、项目、代码、学习记录和外部反馈沉淀为可审查的 evidence，并映射到目标、技能树、研究资料、公开作品和 Agent 上下文中。

它不是传统知识库，也不是让 AI 代替人决定方向的黑盒系统。nblane 的核心目标是帮助用户持续回答五个问题：

- 我想在什么方向上成长？
- 我已经做过什么，能证明这件事？
- 我的能力图谱里哪些地方证据充分，哪些地方只是自我感觉？
- 下一步最值得补什么？
- 哪些经历可以转化为博客、项目、简历和个人网站？

## 目标用户

nblane 当前优先服务的用户是：

- 已经对 LLM、大模型应用和 AI 工具有基本认知的研究者、开发者和技术写作者。
- 正在使用 ChatGPT、Claude、Codex、Cursor、OpenCode 等工具协助学习、开发、研究或写作的人。
- 希望在 3 到 5 年内成长为某个领域或多个交叉领域专家的人。
- 愿意通过阅读、项目、写作、实验、复盘和公开输出积累长期可信证据的人。
- 重视本地文件、Git 历史、可撤销的 AI 写入和个人数据主权的人。

长期愿景是陪伴用户完成多年成长；当前产品落点必须更短：围绕 4 到 8 周的阶段目标，把日常输入转化为 evidence、skill gap、next action 和可公开输出。

## 一句话定义

> nblane 让一个人的目标、能力、项目、研究、证据和公开输出变成自己的 Agent 可读、可写、可撤销、可展示的长期结构化资产。

`SKILL.md` 同时是档案和 Agent 系统提示词：人写叙事部分，`core/sync.py` 重写其中的生成块，`core/context.py` 据此生成给 Agent 的上下文。

最小单元：

```text
Human + Agent = 一个长期共进化成长单元
Goal + Skill + Evidence = 一张可审查的能力图谱
```

## 产品分层

| 层级 | 说明 | 关键问题 |
|------|------|----------|
| Private | 目标、技能、证据、项目、研究的本地事实源 | 我在做什么？我有什么证据？ |
| Agent | 上下文生成、HTTP 接口、直写可撤销、重要操作确认、页面专属操作 | Agent 如何理解我、帮我做事、但不越权？ |
| Public | 人确认后发布的公开表达层 | 哪些能力可以被外部可信地看到？ |

三层共享同一个判断：先有事实源和 evidence，再有 AI 生成、图谱展示和公开发布。

账号只区分三种：本人、助手服务账号（`users.yaml` 中 `agent: true`）、管理员。

## 核心对象

| 对象 | 文件 / 模块 | 作用 |
|------|-------------|------|
| Profile | `profiles/<name>/` | 个人工作区和长期上下文边界 |
| SKILL.md | `profiles/<name>/SKILL.md` | 北极星、身份叙事和 Agent 系统提示词 |
| Goal | `goals.yaml` | 阶段目标，首页星图上的恒星 |
| Skill Tree | `skill-tree.yaml` + `schemas/*.yaml` | 能力状态、领域能力图和 evidence 引用 |
| Evidence Pool | `evidence-pool.yaml` | 技能、项目、公开输出可引用的证据目录 |
| Project Board | `project-board.yaml` | 项目、里程碑、习惯计划与任务归属 |
| Kanban | `kanban.md` + `kanban-archive.md` | 当前执行面，Done 结晶为证据的主要来源 |
| Activity Log | `activity-log.yaml` | 习惯打卡和日常活动 |
| Research | `research/` | 论文库、来源、阅读笔记、翻译与结构化提取 |
| Public Surface | `public-profile.yaml`、`resume-source.yaml`、`blog/`、`projects.yaml`、`outputs.yaml` | 个人网站、简历、写作和作品 |
| AI Gateway | `core/ai/` | 任务化模型调用、结构化输出、模型路由和 AI 异常 |
| Agent 接口 | HTTP `/api/v1` + `nblane_api`；本机 `nblane-mcp` | 助手（OpenClaw）只走 HTTP，带登录与 profile 权限；MCP 只给本机 Cursor / Claude Code |
| 撤销日志 | `agent-journal.yaml` | 助手写入的前后快照，可在助手页撤销 |

## 产品原则

- 目标优先：AI 推荐、技能图谱和研究都服务当前目标，不制造信息噪音。
- 证据优先：能力状态、公开项目、文章结论和简历表达都应追到 evidence / source。
- 文件优先：YAML / Markdown 是事实源，不上数据库，Git 做备份。服务只是读写这些文件的入口（8504 SPA + API，8502 Reader）。
- 写入顺序：pool → tree → validate → sync，见 [数据契约](../architecture/data-contracts.md)。
- 任务优先于聊天：沉淀能力的是项目、任务、证据、复盘和输出，不是聊天记录。
- 低摩擦捕获：AI 负责初步结构化，人负责关键确认。
- 默认私有，按块公开：公开层只读取人确认过的字段，发布只能由人在网页上完成。
- Agent 直写可撤销：日常操作直接写入并记日志，可撤销；删除、批量、改目标 / 北极星 / 技能点、证据评审等重要操作先在聊天里确认；发布、权限、系统设置只能在页面上做。规则见 [Agent Harness](../reference/agent-harness.md)。
- Harness 外部化：OpenClaw、Codex、Cursor、Claude Code 是外部执行器，不内嵌为 nblane 的业务库。
- Research 与 Public 分离：研究资料默认私有，公开需显式导出。
- 输出驱动成长：阅读和收藏是弱证据；项目、复盘、公开文章、开源贡献和真实反馈才是强证据。

## 产品独特性

nblane 与 Notion、Obsidian 或普通 AI 笔记工具的核心差异，不是“也接入了 AI”，而是对象模型不同。

传统知识库主要管理 information：

```text
note -> folder/tag -> search
```

nblane 管理的是成长证据链：

```text
goal -> evidence -> skill -> gap -> action -> artifact -> public proof
```

这意味着系统不只回答“我记录了什么”，还要回答：

- 哪些记录能证明某项能力？
- 哪些技能缺少强证据？
- 哪些弱证据值得升级为项目、文章或公开作品？
- 哪些外部热点和资料与当前目标真的相关？
- 哪些经历可以进入个人网站、作品集和简历？

## 不是什么

- 不是托管型社交网络。
- 不是只追求 UI 漂亮的博客系统。
- 不是把所有数据立即迁移进数据库的 SaaS。
- 不是“AI 自动规划人生”的黑盒系统。
- 不是把所有材料都自动公开的个人品牌工具。
- 不是泛泛推送热点资讯的信息流产品。
- 不是依赖某个 coding agent 内部 API 的插件。
- 不是要求用户每天手工维护复杂知识图谱的重型 PKM。

## 当前产品重心

单人加自己的 Agent。当前重心是让第一条数据闭环全程在 SPA 里完成，不手改 YAML：

```text
北极星 -> 目标 -> 项目 -> 看板 -> 证据结晶 -> 技能树 -> 公开输出
```

助手（OpenClaw）在这条闭环上做日常推进：打卡、加任务、写成长日志、提醒。各区现状见 [项目状态](../project/status.md)，往后方向见 [路线图](roadmap.md)。
