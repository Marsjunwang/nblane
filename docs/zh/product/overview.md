---
status: active
owner: product
last_verified: 2026-09-28
source_of_truth: true
---

# 产品总览

nblane 是面向 **AI-native 研究者和开发者** 的本地优先个人成长工作台。它把阅读、写作、项目、代码、学习记录和外部反馈沉淀为可审查的 evidence，并映射到目标、技能树、研究资料、公开作品和 Agent 上下文中。

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
- 重视本地文件、Git 历史、可审查 AI 写回和个人数据主权的人。

长期愿景是陪伴用户完成多年成长；当前产品落点必须更短：围绕 4 到 8 周的阶段目标，把日常输入转化为 evidence、skill gap、next action 和可公开输出。

## 一句话定义

> nblane 让一个人的目标、能力、项目、研究、证据和公开输出变成 Agent 可读、可写回、可复用、可展示的长期结构化资产。

最小单元不是一个人，也不是一个 Agent，而是：

```text
Human + Agent = 一个长期共进化成长单元
Goal + Skill + Evidence = 一张可审查的能力图谱
多个成长单元 + 共享产品池 = 一个长期复利团队
```

## 当前实现闭环

当前 SPA 首个数据闭环及其验收口径，以[全局 Phase 计划](../dev/phase-plan.md)为准；页面与 API 的实现状态见 [SPA 迁移总账](../architecture/frontend-spa-migration.md)。本页不再维护另一套流程定义。

## 产品分层

| 层级 | 说明 | 关键问题 |
|------|------|----------|
| Private OS | 个人目标、技能、证据、项目、研究和日志的本地事实源 | 我是谁？我在做什么？我有什么证据？ |
| Agent OS | 面向 AI/Agent 的上下文、工具、写回协议和审查机制 | Agent 如何理解我、帮助我、但不越权？ |
| Team OS | 多个个人成长单元之间的共享问题、项目、证据、方法和决策池 | 团队如何复用个人积累并形成复利？ |
| Public Surface | 从私有证据中人工确认并发布的公开表达层 | 哪些能力可以被外部可信地看到？ |

这四层共享同一个基本判断：**先有事实源和 evidence，再有 AI 生成、图谱展示和公开发布**。

## 核心对象

| 对象 | 文件 / 模块 | 作用 |
|------|-------------|------|
| Profile | `profiles/<name>/` | 个人工作区和长期上下文边界 |
| Goal | 规划中：`goals.yaml` / project refs | 阶段性成长目标和评估边界 |
| SKILL.md | `profiles/<name>/SKILL.md` | 人类叙事、研究品味和 Agent system prompt 的人写部分 |
| Skill Tree | `skill-tree.yaml` + `schemas/*.yaml` | 能力状态、领域能力图和 evidence 引用 |
| Evidence Pool | `evidence-pool.yaml` | 技能、项目、公开输出可引用的证据目录 |
| Kanban | `kanban.md` | 当前执行面和 Done -> Evidence 的主要来源 |
| Research Workspace | `research/`（规划中） | 论文、资料、source chunk、claim、citation、synthesis draft |
| Project Board | `project-board.yaml`（规划中） | 内部项目、milestone、任务、证据和决策 |
| Public Surface | `public-profile.yaml`、`resume-source.yaml`、`blog/`、`projects.yaml`、`outputs.yaml` | 可公开发布的个人网站、简历、博客和作品层 |
| Team Pool | `teams/<id>/product-pool.yaml` | 团队共享问题、项目、证据、方法和决策 |
| AI Gateway | 规划中 | 任务化模型调用、结构化输出、模型路由和 AI run 日志 |
| MCP Server | `nblane-mcp` | 外部 Agent 读取上下文、调用草稿优先写回工具的协议层 |

## 产品原则

- **目标优先**：AI 推荐、技能图谱和研究热点都要服务于用户当前目标，而不是制造信息噪音。
- **证据优先**：能力状态、公开项目、博客结论和简历表达都应尽量追到 evidence/source。
- **文件优先**：YAML/Markdown 是事实源，Git diff 是历史，数据库和索引只是加速层。
- **任务优先于聊天**：真正沉淀能力的是项目、任务、证据、复盘和输出，不是散落聊天记录。
- **低摩擦捕获**：用户不应该被迫维护复杂系统；AI 负责初步结构化，人负责关键确认。
- **默认私有，按块公开**：公开层只读取经过人工整理和确认的字段。
- **Agent 写回必须可审查**：AI/Agent 可以生成草稿、补丁和候选状态，但关键发布、能力升级和长期路线由人确认。
- **Harness 可替换**：Codex/OpenCode/Cursor/Claude 是外部执行器，不是 nblane 的核心数据模型。
- **输出驱动成长**：阅读和收藏只是弱证据；项目、复盘、公开文章、开源贡献和真实反馈才是更强证据。

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

当前阶段的重心是把已经可用的功能组织成统一工作台：

```text
文件事实源
  -> 属性化对象
  -> 结构化索引 / typed graph
  -> 多视图 UI
  -> AI Gateway
  -> MCP-first Agent 集成
  -> 研究资料、证据图谱和公开输出闭环
```

具体开发顺序见[全局 Phase 计划](../dev/phase-plan.md)、[路线图](roadmap.md)和[里程碑](../project/milestones.md)。
