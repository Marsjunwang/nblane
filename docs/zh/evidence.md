# 技能证据（Skill evidence）

在 **skill-tree** 节点上挂载结构化证明，用于差距分析、校验与 agent
system prompt 展示「能力是否有据可查」。

支持两种方式：

1. **内联 `evidence`** — 直接写在节点上（与旧版兼容）。
2. **证据池 + `evidence_refs`** — 在 `evidence-pool.yaml` 中录入一次，用稳定
   **id** 在多个技能上引用（一项目多技能）。

下游会**物化**为一条列表：先解析引用（按 id 去重），再追加内联条目。

## 文件

| 文件 | 作用 |
|------|------|
| `profiles/<name>/skill-tree.yaml` | 每节点的 `evidence` 与/或 `evidence_refs` |
| `profiles/<name>/evidence-pool.yaml` | 共享的 `evidence_entries`，`id` 唯一 |

`nblane init` 的新 profile 会带空的 `evidence-pool.yaml` 模板。

## 内联格式（`skill-tree.yaml`）

在 `nodes:` 下可为每个节点增加 `evidence` 列表，每项为字典：

| 字段 | 必填 | 说明 |
|------|------|------|
| `type` | 是 | `project` \| `paper` \| `course` \| `practice` |
| `title` | 是 | 短标题（非空） |
| `date` | 否 | 如 `2026-02` |
| `url` | 否 | 链接 |
| `summary` | 否 | 摘要 |

无 `evidence` 的旧文件完全兼容，视为空列表。

## 证据池与引用

**池条目**（`evidence-pool.yaml`）含 `id`、`type`、`title` 等；节点上
`evidence_refs: [id, …]` 引用池 id。可与内联 `evidence` 混用；YAML 中重复的
引用 id 会规范为一条。

## 命令行

**内联追加**（与原先一致）：

```bash
nblane evidence <profile> <skill_id> add \
  --type project \
  --title "真机 bringup 演示" \
  ...
```

**在池中新增一条**（同 type + title + date 会复用已有 id）：

```bash
nblane evidence <profile> pool add --type project --title "共享项目" \
  --id my_id
```

**把池 id 挂到技能**（追加 `evidence_refs`）：

```bash
nblane evidence <profile> link <skill_id> <evidence_id>
```

## Web

在 **Skill Tree**：展开 **证据池** 可新增池条目；技能卡片上 **来自证据池（引用）**
多选 + 内联证据行；保存时若已有池文件或池非空，会一并写入
`evidence-pool.yaml`。

## 与其它功能的关系

- **`nblane context`** — 物化后的证据用于 **Skill evidence (solid / expert)**。
- **`nblane gap`** — 显示如 `solid (4 evidence)`（内联 + 引用合计）。
- **`nblane validate`** — 内联非法 type / 空 title → **WARN**；未知
  `evidence_refs` id 或缺池文件却写了引用 → **ERROR**。

**迁移：** 仅内联的旧数据行为不变；若要把重复条目迁入池，先写入
`evidence-pool.yaml`，再把节点改为 `evidence_refs`，最后跑 `nblane validate`。

更完整说明见 [设计手册 §5](../design.md#5-demo-1-phase-1-skill-provenance-evidence)
（英文锚点）与 [Skill evidence（英文）](../evidence.md)。
