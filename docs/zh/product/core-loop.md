---
status: active
owner: product
last_verified: 2026-05-08
source_of_truth: true
---

# 核心闭环

nblane 的价值来自闭环，而不是单点功能。当前最小闭环是：

```text
捕获 -> 计划 -> 执行 -> 证据 -> 能力更新 -> 研究/写作 -> 公开输出 -> Agent 复用
```

## 1. 捕获

输入可以来自：

- 手动写入 `kanban.md`。
- `inbox.yaml` 中的想法、资料、问题。
- `learning-log.yaml` 中的论文、文章、课程、repo。
- `activity-log.yaml` 中的学习/锻炼/实践记录。
- 未来 `research/sources.yaml` 中的论文、URL、PDF、Markdown note。

捕获阶段默认不改变技能树，也不公开。

## 2. 计划

计划面目前由 `kanban.md` 承担：

- Doing：本周正在推进。
- Queue：近期准备做。
- Done：已完成，可进入证据整理。
- Someday / Maybe：低承诺想法。

后续 `project-board.yaml` 会把项目、milestone、任务、证据、决策连成更稳定的内部项目视图。

## 3. 执行

执行阶段可以由人、nblane Web UI、CLI、MCP 工具或外部 harness 协作完成。

短交互 AI 走 nblane AI Gateway，例如：

- gap 解释。
- kanban 子任务建议。
- blog inline patch。
- Done -> evidence patch。

复杂多步任务交给 Codex/OpenCode 等外部 harness，例如：

- 分析整个代码库。
- 实现 milestone。
- 处理一批研究资料。
- 生成 source-aware synthesis draft。

## 4. 证据

Done 任务、学习记录、项目成果、论文/代码/实验输出可以升格为 evidence：

```text
kanban Done -> LLM JSON patch -> evidence-pool.yaml -> skill-tree.yaml -> validate -> sync SKILL.md
```

不变量：

- 先写 `evidence-pool.yaml`，再在 `skill-tree.yaml` 中引用。
- `status` 提升必须人工确认。
- `SKILL.md` 生成块只通过 sync 更新。

## 5. 研究与写作

当前 Blog 编辑器可以生成、修改、审阅和发布博客草稿。下一阶段 Research Workspace 会引入：

- `ResearchSource`
- `SourceChunk`
- `Claim`
- `Citation`
- `SynthesisDraft`

目标是让博客草稿能追溯到 source/chunk/claim，而不是只有自由文本。

## 6. 公开输出

Public Surface 只处理显式公开层：

- `public-profile.yaml`
- `resume-source.yaml`
- `projects.yaml`
- `outputs.yaml`
- `blog/*.md`
- `media/`

它不会直接发布私有 skill-tree、kanban、agent-profile、research source 或 auth 文件。

## 7. Agent 复用

`nblane context` 和 `nblane-mcp` 把当前 profile、任务、证据和项目上下文提供给外部 Agent。

当前路径：

```text
nblane files -> context/MCP resources -> Codex/OpenCode/Cursor/Claude -> MCP tools -> draft/writeback
```

Agent 写回原则：

- 默认 draft-first。
- 写 evidence/skill/project 要校验。
- 公开发布要人确认。
- 不绕过 nblane 的文件安全和冲突检查。
