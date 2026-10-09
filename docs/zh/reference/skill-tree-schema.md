---
status: active
owner: engineering
last_verified: 2026-10-09
source_of_truth: true
---

# 技能树 Schema 指南

## 概览

Schema 定义某领域技能树的全部节点，相当于完整关卡图。每个人的 `skill-tree.yaml` 是个人叠加层，记录点亮了哪些节点。

内置两个领域，随代码发布（`schemas/` 包）：

| 名称 | 领域 | 节点数 | 类目 |
|------|------|--------|------|
| `robotics-engineer` | 机器人与具身智能工程师（模板默认） | 82 | 14 |
| `autonomous-driving` | 自动驾驶工程师 | 82 | 13（新增规划、安全；无操作、运动、中间件） |

两个领域在基础、研究、影响力、领导力、战略里用同一批节点 ID，换领域时这部分技能点可以保留。`schemas/.learned/` 存放从 LLM 反馈学到的关键词，只在本机，不进 Git。

## 查找顺序

按名字找 `<name>.yaml`，先数据目录 `<NBLANE_ROOT>/schemas/`，再内置 schema，用第一个找到的（`core/schema_io.schema_path`）。所以数据目录里的同名文件会覆盖内置版本。名字只允许小写字母、数字、`-` 和 `_`，不合法的名字一律当作不存在。可用列表是两处的并集，`GET /api/v1/schemas` 返回每个领域的名称、domain、描述、节点数和来源（`data` / `builtin`）。

## Schema 结构

```yaml
schema_version: "1.0"
domain: "Robotics Engineer / 机器人与具身智能工程师"
description: >
  ...

categories:                  # 类目 id → 中文名（可选，推荐）
  foundations: 基础
  middleware: 中间件

nodes:
  - id: ros2_basics          # 唯一 ID，ASCII snake_case
    label: ROS2 Basics       # 英文或中英双语，便于关键词匹配
    level: 1                 # 1=基础 2=进阶 3=高级 4=专家/前沿
    category: middleware     # 分组，技能树页按它分类目星官
    requires: [linux_basics] # 前置节点（可选）
    keywords: [ros, 机器人中间件]  # 额外匹配词（可选）
```

`categories` 给每个类目起中文名，技能树页横幅和首页星图扇区都用它；没写时退回内置对照表（`core/starmap_snapshot.CATEGORY_ZH`），再没有就显示类目 id。SPA 按中文名匹配星官（`starmap/layout.ts` 的 `SECTOR_ASTERISM`），目前认识：基础、感知、导航、规划、控制、学习力、仿真、系统、安全、研究、影响力、领导力、战略、操作、运动、中间件。其他名字照常显示，只是用通用星形。

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

- 新建档案（`nblane init`、设置页「新建用户」）会把所选领域的全部节点写进来，状态都是 `locked`，技能树页一进来就是完整的树。
- 手写或旧档案可以只列要跟踪的节点，未列出的隐式为 `locked`，但只有列出的节点能在技能树页改状态。
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

- 节点下每条未弃用、已审阅的证据按强度计分（待审阅的 AI 预填不计）：弱 1、中 10、强 100；带 `breakthrough: true` 的再加 1000。
- 升到下一级的门槛：locked→learning 10，learning→solid 30，solid→expert 100。
- 分数达标或有一条 breakthrough 即提示。只是建议，状态仍由人改；改技能点对助手是需要聊天确认的重要操作。

## 新增领域 Schema

管理员手动加领域不用改代码：复制一份内置 YAML 改好，放到 `<NBLANE_ROOT>/schemas/<name>.yaml`。不用重启，设置页「新建用户」的领域选项和 `nblane init --schema` 立即能选到。节点组织成 DAG：基础在 level 1，`requires` 指向同一文件里的前置。

- 文件名就是领域名，只用小写字母、数字、`-`、`_`。
- 节点 ID 用小写加下划线；通用能力尽量沿用内置 ID。
- 写上 `categories`，中文名尽量用上面星官认识的那些。
- 一个节点代表约 1–8 周能到 `solid` 的连贯技能。
- 不要过度拆分，40–80 个节点较合适。
- `requires` 用于提示和可视化，不做完整 DAG 强校验。

## 选择与更换领域

- 新建档案时选：`nblane init <name> --schema autonomous-driving`，或在「新建用户」里勾选建档案后选领域。会改写 `skill-tree.yaml` 的 `schema:` 和 SKILL.md 的 `- **Domain**:` 行；不选就是模板默认的 `robotics-engineer`。
- 已有档案换领域：直接改 `skill-tree.yaml` 里的 `schema:`。新领域里没有的节点 ID 会让 `nblane validate` 报错，要删掉或换成新领域的 ID。

## 校验

`nblane validate [name]` 检查：

- 节点 ID 属于所选 schema，状态合法。
- 节点为 solid / expert 但前置仍为 locked / learning 时给 WARN。
- `evidence_refs` 是字符串列表且都能在 `evidence-pool.yaml` 找到。
- 内联 `evidence` 的类型合法、标题非空。
- SKILL.md 生成块是否漂移（WARN）。

## 可视化

SPA 的技能树页（`/p/<name>/skill-tree`）和首页星图展示技能树，见 [技能树使用说明](../guides/skill-tree.md)。命令行用 `nblane status` 看文本摘要。
