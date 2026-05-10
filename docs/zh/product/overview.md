---
status: active
owner: product
last_verified: 2026-05-08
source_of_truth: true
---

# 产品总览

nblane 是一个 **Human + Agent + Team 共进化系统**。它不是单纯的博客、看板、简历生成器或聊天工具，而是把个人能力、Agent 上下文、项目执行、研究资料、证据、团队共享池和公开输出连接起来的本地优先工作台。

## 一句话定义

> nblane 让一个人的能力、项目、证据、研究资料和公开输出变成 Agent 可读、可写回、可复用的长期结构化资产。

最小单元不是一个人，也不是一个 Agent，而是：

```text
Human + Agent = 一个长期共进化单元
多个单元 + 共享产品池 = 一个长期复利团队
```

## 核心对象

| 对象 | 文件 / 模块 | 作用 |
|------|-------------|------|
| Profile | `profiles/<name>/` | 个人工作区和长期上下文边界 |
| SKILL.md | `profiles/<name>/SKILL.md` | 人类叙事、研究品味、Agent system prompt 的人写部分 |
| Skill Tree | `skill-tree.yaml` + `schemas/*.yaml` | 能力状态和领域能力图 |
| Evidence Pool | `evidence-pool.yaml` | 技能、项目、公开输出可引用的证据目录 |
| Kanban | `kanban.md` | 当前执行面和 Done -> Evidence 的来源 |
| Public Surface | `public-profile.yaml`、`blog/`、`projects.yaml`、`outputs.yaml` | 可公开发布的个人网站和作品层 |
| Research Workspace | `research/`（规划中） | 论文、资料、source chunk、claim、synthesis draft |
| Project Board | `project-board.yaml`（规划中） | 内部项目、milestone、任务、证据和决策 |
| Team Pool | `teams/<id>/product-pool.yaml` | 团队共享问题、项目、证据、方法和决策 |
| MCP Server | `nblane-mcp` | 外部 Agent 读取上下文、调用写回工具的协议层 |

## 产品原则

- **文件优先**：YAML/Markdown 是事实源，Git diff 是历史。
- **证据优先**：能力状态、公开项目和博客结论都应尽量追到 evidence/source。
- **任务优先于聊天**：真正沉淀能力的是项目、任务、证据和复盘，不是散落聊天记录。
- **默认私有，按块公开**：公开层只读取经过人工整理和确认的字段。
- **Agent 写回必须可审查**：AI/Agent 可以生成草稿和补丁，但关键发布和能力状态由人确认。
- **Harness 可替换**：Codex/OpenCode 是外部执行器，不是 nblane 的核心数据模型。

## 不是什么

- 不是托管型社交网络。
- 不是只追求 UI 漂亮的博客系统。
- 不是把所有数据立即迁移进数据库的 SaaS。
- 不是让 Agent 一键代劳的黑盒系统。
- 不是依赖某个 coding agent 内部 API 的插件。

## 当前产品重心

当前阶段的重心是把已经可用的功能组织成统一工作台：

```text
文件事实源
  -> 属性化对象
  -> 结构化索引 / typed graph
  -> 多视图 UI
  -> AI Gateway
  -> MCP-first Agent 集成
  -> 研究资料和博客生成闭环
```

详细开发顺序见 [路线图](roadmap.md) 和 [里程碑](../project/milestones.md)。
