# 技能树 Schema 指南

## 概览

Schema 定义某领域技能树的**全部可能节点**，相当于完整关卡图。每个人的
`skill-tree.yaml` 是个人叠加层，记录点亮了哪些节点。

Schema 放在 `schemas/`。当前示例为 `schemas/robotics-engineer.yaml`。

## Schema 结构

```yaml
schema_version: "1.0"
domain: "Robotics Engineer"

nodes:
  - id: ros2_basics          # 唯一 ID，在 skill-tree.yaml 中引用
    label: ROS2 Basics       # 人类可读名称
    level: 1                 # 1=基础 2=进阶 3=高级 4=专家
    category: middleware     # 分组，便于可视化
    requires: [linux_basics] # 前置节点 ID（可选）
```

## 个人 skill-tree.yaml 结构

```yaml
profile: "alice"
schema: "robotics-engineer"
updated: "2026-03-21"

nodes:
  - id: ros2_basics
    status: solid
    note: "completed 2025-09"

  - id: moveit2
    status: learning
    note: "working through manipulation tutorial"

  - id: sim2real
    status: locked
    note: "planned Q3 2026"
```

**只需列出你要跟踪的节点。** 未列出的节点隐式为 `locked`。

## 状态取值

| Status | 含义 | 图标 |
|--------|------|------|
| `expert` | 可迁移的深度掌握 | ★ |
| `solid` | 真实工作中可靠使用 | ● |
| `learning` | 正在学 | ◐ |
| `locked` | 未开始 | ○ |

## 新增领域 Schema

以 `schemas/robotics-engineer.yaml` 为模板复制。节点组织成 DAG：基础在
level 1，`requires` 指向前置。

建议：

- 节点 ID 用小写加下划线
- 一个节点代表可在约 1–8 周内达到 `solid` 的连贯技能
- 不要过度拆分——约 40–80 个节点较合适
- `requires` 用于可视化建议；完整 DAG 强校验仍非目标

## 校验（已实现）

`python nblane.py validate` 会检查 `skill-tree.yaml` 中的节点 ID 是否属于所选
schema、状态是否合法，并在「节点已为 solid/expert 但前置仍为 locked/learning」
时给出 **WARN**。

## 可视化（未来）

计划中的 `tools/visualize.py` 将输出静态 SVG：

- solid/expert 节点着色
- 进行中节点部分填充
- locked 灰色
- 依赖边

目前用 `python tools/status.py` 看文本摘要。
