---
status: active
owner: engineering
last_verified: 2026-10-07
source_of_truth: true
---

# 技能树 Schema 指南

## 概览

Schema 定义某领域技能树的全部节点，相当于完整关卡图。每个人的 `skill-tree.yaml` 是个人叠加层，记录点亮了哪些节点。

Schema 放在 `schemas/`，当前只有 `schemas/robotics-engineer.yaml`（82 个节点）。`schemas/.learned/` 存放从 LLM 反馈学到的关键词，只在本机，不进 Git。

## Schema 结构

```yaml
schema_version: "1.0"
domain: "Robotics Engineer / 机器人与具身智能工程师"
description: >
  ...

nodes:
  - id: ros2_basics          # 唯一 ID，ASCII snake_case
    label: ROS2 Basics       # 英文或中英双语，便于关键词匹配
    level: 1                 # 1=基础 2=进阶 3=高级 4=专家/前沿
    category: middleware     # 分组，技能树页按它分类目星官
    requires: [linux_basics] # 前置节点（可选）
    keywords: [ros, 机器人中间件]  # 额外匹配词（可选）
```

## 个人 skill-tree.yaml

```yaml
profile: "alice"
schema: "robotics-engineer"
updated: "2026-03-21"

nodes:
  - id: ros2_basics
    status: solid
    note: "completed 2025-09"
    evidence_refs: [ev_20250901_bringup]   # 指向 evidence-pool.yaml 的 id

  - id: moveit2
    status: learning
    note: "working through manipulation tutorial"
```

- 只列要跟踪的节点，未列出的隐式为 `locked`。
- 证据优先用 `evidence_refs` 引用证据池；节点上的内联 `evidence` 列表仍兼容。字段见 [证据参考](evidence.md)。
- 写入顺序是证据池 → 技能树 → validate → sync。SPA 技能树页和 CLI 都走这条路径。

## 状态取值

| Status | 含义 | SKILL.md 生成块 |
|--------|------|----------------|
| `expert` | 可迁移的深度掌握 | `[x]` |
| `solid` | 真实工作中可靠使用 | `[x]` |
| `learning` | 正在学 | `[ ]` |
| `locked` | 未开始 | `[~]` |

## 进阶提示

`GET /api/v1/profiles/{name}/skill-tree` 给每个节点附带 `progress`，技能树页据此提示「可以升一级」。规则在 `core/skill_progression.py`：

- 节点下每条未弃用的证据按强度计分：弱 1、中 10、强 100；带 `breakthrough: true` 的再加 1000。
- 升到下一级的门槛：locked→learning 10，learning→solid 30，solid→expert 100。
- 分数达标或有一条 breakthrough 即提示。只是建议，状态仍由人改；改技能点对助手是需要聊天确认的重要操作。

## 新增领域 Schema

以 `schemas/robotics-engineer.yaml` 为模板复制。节点组织成 DAG：基础在 level 1，`requires` 指向前置。

- 节点 ID 用小写加下划线。
- 一个节点代表约 1–8 周能到 `solid` 的连贯技能。
- 不要过度拆分，40–80 个节点较合适。
- `requires` 用于提示和可视化，不做完整 DAG 强校验。

## 校验

`nblane validate [name]` 检查：

- 节点 ID 属于所选 schema，状态合法。
- 节点为 solid / expert 但前置仍为 locked / learning 时给 WARN。
- `evidence_refs` 是字符串列表且都能在 `evidence-pool.yaml` 找到。
- 内联 `evidence` 的类型合法、标题非空。
- SKILL.md 生成块是否漂移（WARN）。

## 可视化

SPA 的技能树页（`/p/<name>/skill-tree`）和首页星图展示技能树，见 [技能树使用说明](../guides/skill-tree.md)。命令行用 `nblane status` 看文本摘要。
