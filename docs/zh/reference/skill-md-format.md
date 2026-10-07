---
status: active
owner: docs
last_verified: 2026-10-08
source_of_truth: true
---

# SKILL.md 格式说明

## 为何重要

`SKILL.md` 既是档案，也是 Agent 的系统提示。`nblane context`、MCP `profile://context` 和助手的只读语料都从它生成。写得越诚实、越具体，Agent 的帮助越有用。

模板见 `profiles/template/SKILL.md`。

## 章节

### Identity（身份）

你是谁、领域、去向：

```markdown
- **Name**: alice
- **Domain**: Robotics (Manipulation, Embodied AI)
- **Journey**: Year 1 of 5
- **Current Role**: PhD student
- **North Star**: First-author paper at ICRA 2028, open-source project with 500+ stars
- **North Star Brief**: 一句能放在首页的短版本
- **North Star Visibility**: private
```

- 北极星具体到你能判断是否达成。
- `North Star Visibility` 只有 `public` / `private` 两档，只控制公开站等公开产物；Agent 始终能看到全文。
- 首页星表编辑北极星时，只改写这三行（`core/north_star.py`），其余内容不动。

### Core Competencies（核心能力）

技能域与诚实状态表，用来校准 Agent：已会的不过度讲解，没宣称的熟练度不默认你已掌握。状态取值 `locked` | `learning` | `solid` | `expert`。

### Skill Tree（技能树）

生成块，不要手改：

```markdown
<!-- BEGIN GENERATED:skill_tree -->
- [x] ROS2 Basics (`ros2_basics`): completed 2025-09
- [ ] MoveIt2 (`moveit2`)
<!-- END GENERATED:skill_tree -->
```

由 `skill-tree.yaml` 渲染：`solid` / `expert` 为 `[x]`，`learning` 为 `[ ]`，`locked` 为 `[~]`。完整内容在 YAML，见 [技能树 Schema](skill-tree-schema.md)。

### Research Fingerprint（研究指纹）

共进化里最重要的一节，你的品味在这里。读过它的 Agent 可以像你一样找论文薄弱点、用你认得出的风格写作、优先排你真正关心的问题。

要具体。「我在意干净消融」可以；「我不信不展示真机失败案例的操作论文」更好。

### Current Focus（当前焦点）

生成块，从 `kanban.md` 渲染：Doing 列为 Active，Queue 列为 Queued，带 `blocked_by` 的任务进 Blocked。不要手改。

### Thinking & Communication Style（思维与表达）

你怎么讲、怎么写、用什么语言。`--mode write` 时用来贴近你的声音。

### Growth Log（成长日志）

按时间追加的表，只增不删。追加方式：`nblane log <name> "事件"`，或助手的 `nblane_api growth "<一句话进展>"`（可撤销）。

### Influence & Output（影响与产出）

论文、项目等对外产出的简表。公开站的结构化产出在 `outputs.yaml` / `projects.yaml`。

## 生成块与同步

只有 `skill_tree` 和 `current_focus` 两个生成块（`core/sync.py`）。改了 `skill-tree.yaml` 或 `kanban.md` 后：

```bash
nblane sync <name> --check    # 有漂移退出码 1
nblane sync <name> --write
```

SPA 里改技能点和证据关联时会自动重写生成块；只改看板时 Current Focus 不会自动更新，需要跑 `sync --write`。`nblane validate` 会把生成块漂移报为 warning。

## agent-profile.yaml（可选）

与 `SKILL.md` 并列，结构化描述 Agent 对你强项、弱项与协作风格的建模。存在时，`nblane context` 会追加 **Agent profile (structured)** 区块（只渲染白名单字段）。助手不会改这个文件；它在每周巩固的周报里列出建议，由你自己决定是否修改。模板见 `profiles/template/agent-profile.yaml`，不需要可删除。

## 更新节奏

- 每周：`nblane sync --write` 刷新 Current Focus。
- 每月：Skill Tree、Core Competencies。
- 里程碑：Growth Log、Influence & Output。
- 每季：Research Fingerprint、Identity。

## 诚实原则

`SKILL.md` 不是简历，是先验。夸大会让 Agent 假设错误，帮助变差。该锁就标 `locked`，日志用来证明你何时点亮了节点。
