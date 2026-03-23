# nblane · 设计手册与里程碑

本文档说明**如何实现**产品愿景：与 [product.md](product.md)（为什么、是什么）和 [architecture.md](architecture.md)（当前实现边界）分工不同，这里聚焦**迭代顺序、数据契约、验收标准**。

| 项目 | 当前值 |
|------|--------|
| 文档版本 | `v0.2.0` |
| 状态 | Active |
| 最近更新 | `2026-03-22` |

---

## 1. 三份文档的职责

| 文档 | 职责 |
|------|------|
| [product.md](product.md) | 产品定义、用户、Team OS、路线图、与仓库的词汇映射 |
| [architecture.md](architecture.md) | 仓库**当前**已实现什么、工程原则、模块清单 |
| **design.md（本文）** | 分阶段里程碑、文件格式、CLI 能力、如何验收 |

---

## 2. 设计原则（实现侧）

1. **纯文本优先**：新能力优先落在 Markdown / YAML，不自造二进制格式。
2. **Git 即数据库**：协作与历史依赖版本控制；校验与导出是可重复命令。
3. **默认私有**：团队目录与共享池在仓库内仍由团队约定可见范围；公开面显式导出。
4. **渐进增强**：先规则层（可解释），再考虑更强推理；每步可独立使用。
5. **不破坏薄 CLI**：已有命令保持向后兼容；新能力增量添加。
6. **模块内聚**：`core/` 下一个文件一个职责；新增能力新建文件。

---

## 3. 已完成基线盘点（v0.2.0）

以下为截至本版本**已实现且可用**的能力，对应产品手册中 Demo 1 之前的全部地基，以及 **Demo 1 Phase 1（技能来源 / 证据）**。

### 3.1 数据层

| 组件 | 说明 | 位置 |
|------|------|------|
| Profile 结构 | SKILL.md / skill-tree.yaml / **evidence-pool.yaml** / kanban.md / agent-profile.yaml | `profiles/` |
| Profile 模板 | `init` 脚手架并替换 `{Name}` | `profiles/template/` |
| 领域 Schema | 节点 id / label / level / category / requires / keywords | `schemas/robotics-engineer.yaml` |
| 团队共享池 | team.yaml + product-pool.yaml（problem / project / evidence / method / decision） | `teams/` |
| 数据模型 | SkillNode / SkillTree / Evidence / **EvidenceRecord** / **EvidencePool** / Schema / … | `core/models.py` |
| 统一 I/O | skill-tree + **evidence-pool** + teams，单模块收敛 | `core/io.py` |

### 3.2 规则层

| 能力 | 说明 | 位置 |
|------|------|------|
| Gap 分析 | token 匹配 + 领域同义词扩展 + BFS 前置闭包 + 缺口检测 + 下一步建议；**证据条数按物化后计数** | `core/gap.py` |
| Context 生成 | SKILL.md + agent-profile.yaml + kanban.md → system prompt（四种 mode）；**solid/expert 证据为物化结果** | `core/context.py` |
| Skill-tree 校验 | 节点 ID / 状态 / 前置一致性；**evidence_refs 须在池中存在** | `core/validate.py` |
| SKILL.md 同步 | 生成块 + 漂移检测 + 自动回写 | `core/sync.py` |
| 状态摘要 | 按状态统计 + 点亮率 | `core/status.py` |
| 团队汇总 | team.yaml + product-pool → 摘要 | `core/team.py` |

### 3.3 CLI（11 条命令）

| 命令 | 状态 | 说明 |
|------|------|------|
| `init` | 已实现 | 创建 profile |
| `context` | 已实现 | 生成 system prompt（含 agent-profile + kanban） |
| `status` | 已实现 | 技能树摘要 |
| `log` | 已实现 | 追加 Growth Log |
| `sync` | 已实现 | 检查/回写 SKILL.md 生成块 |
| `validate` | 已实现 | 校验 skill-tree vs schema（含证据与引用） |
| `gap` | 已实现 | 任务 → 技能匹配与缺口（输出含物化证据计数） |
| `team` | 已实现 | 团队池汇总 |
| `evidence` | 已实现 | 内联 / `pool add` / `link`（见 §5） |
| `ingest-resume` | 已实现 | LLM：简历或长文本 → 池 + 树补丁（`--dry-run`、`--allow-status-change`） |
| `ingest-kanban` | 已实现 | LLM：看板 **Done** 列 → 池 + 树补丁（同上） |

### 3.4 Web UI（Streamlit）

| 页面 | 功能 | 文件 |
|------|------|------|
| Home | SKILL.md 概览 + 结构化编辑 + 原始编辑 + **简历/长文本 AI 摄入**（草案 → 写入） | `app.py` |
| Skill Tree | 分类标签页 + 分级展示 + 状态 + 笔记 + **内联证据 + 证据池 + 引用多选** + 保存同步 | `pages/1_Skill_Tree.py` |
| Gap Analysis | 任务文本 + 规则分析 + AI 分析 + 写回面板 | `pages/2_Gap_Analysis.py` |
| Kanban | 四列看板 + 任务增删移动 + **已完成 → 证据** AI 摄入（多选、草案 → 写入） | `pages/3_Kanban.py` |
| Team View | 团队信息 + 产品池 CRUD | `pages/4_Team_View.py` |

### 3.5 AI 层

| 能力 | 说明 | 文件 |
|------|------|------|
| LLM 客户端 | OpenAI 兼容，env 配置，可选 | `core/llm.py` |
| AI Gap 分析 | 规则结果 + 技能摘要 → LLM 学习建议 | `pages/2_Gap_Analysis.py` |
| Profile 摄入 | LLM → JSON 补丁；**先合并池再合并树**；`validate` + `sync`（失败回滚）；中/英提示（`LLM_REPLY_LANG`） | `core/profile_ingest.py`、`core/profile_ingest_llm.py`、`core/jsonutil.py` |

---

## 4. 当前状态：Demo 1 · 阶段定位

项目**已完成 Demo 1 之前的全部地基**，且 **Demo 1 Phase 1（Skill Provenance）** 已落地：支持**内联证据**、**共享证据池**（`evidence-pool.yaml`）与节点上的 **`evidence_refs` 引用**。

```
[已完成] M0 稳定地基 · validate、schema 校验
[已完成] M1 个人任务闭环 · gap 规则层 + CLI + Web UI
[已完成] M2 Agent profile · agent-profile.yaml + context 拼入
[已完成] M3 团队共享池 · teams/ + team 命令 + Web UI
[已完成] Demo 1 Phase 1：Skill Provenance（evidence + evidence-pool + evidence_refs）
[已完成] 应用层：Profile 摄入（简历 + 看板 Done → YAML，同一 validate/sync 路径）
                 |
                 v   <-- 你在这里
[未开始] Demo 1 Phase 2：MCP Server — Read Path
[未开始] Demo 1 Phase 3：MCP Server — Write Path
[未开始] Demo 1 Phase 4：方法结晶
[未开始] Demo 1 Phase 5：Cursor Skill 集成
```

阶段依赖：

```
Phase 1 (Skill Provenance)
  -> Phase 2 (MCP Read) -> Phase 3 (MCP Write) -> Phase 4 (Crystallize)
  -> Phase 5 (Cursor Skill)  （也依赖 Phase 1 + 2）
```

---

## 5. Demo 1 Phase 1：Skill Provenance（证据）

**目标**：技能树节点携带结构化证据，使 gap 与 context 能反映证据深度；可选 **共享证据池**，同一项目只录一次，多技能通过 id 引用。

### 5.1 数据契约

**内联证据**（`skill-tree.yaml` → `nodes[].evidence`）——与原先一致：

```yaml
# skill-tree.yaml 节点扩展示例
nodes:
  - id: pose_estimation
    status: solid
    note: "3D pose from depth + RGB"
    evidence:
      - type: project          # project | paper | course | practice
        title: "Piper 手眼标定"
        date: "2026-02"
        url: ""
        summary: "完成 eye-in-hand 标定，误差 < 2mm"
      - type: paper
        title: "FoundationPose 复现"
        date: "2026-01"
        summary: "在 YCB 上复现 AP 92.3%"
```

**证据池**（`profiles/<name>/evidence-pool.yaml`）——带稳定 id 的目录化条目：

```yaml
profile: "alice"
updated: "2026-03-22"
evidence_entries:
  - id: piper_vla_2026
    type: project
    title: "Piper + VLA 集成"
    date: "2026-03"
    url: ""
    summary: "单栈、真机 demo"
    deprecated: false      # 可选
    replaced_by: ""        # 可选后继 id
```

**节点引用**（`skill-tree.yaml` → `nodes[].evidence_refs`）——池 id 列表（可选；可与内联 `evidence` 共存）：

```yaml
nodes:
  - id: vlm_robot
    status: solid
    evidence_refs:
      - piper_vla_2026
```

**核心类型**（`core/models.py`）：

- `Evidence` — 内联行字段。
- `EvidenceRecord` — 池行：在 Evidence 字段基础上含必填 `id`，可选 `deprecated` / `replaced_by`。
- `EvidencePool` — `evidence_entries: list[EvidenceRecord]`。
- `SkillNode` — `evidence: list[Evidence]`，`evidence_refs: list[str]`（默认空）。

**物化**（`core/evidence_resolve.py`）：`resolve_node_evidence_dict` 将引用从池中解析（**按 id 去重**），再追加内联 `evidence`。gap 计数、context 摘要、validate 均基于该逻辑或等价实现。

### 5.2 任务分解

| # | 任务 | 文件 | 验收 |
|---|------|------|------|
| 1 | `Evidence` + `EvidenceRecord` + 池类型；`SkillNode.evidence_refs` | `core/models.py` | YAML 往返；加载时对 ref id 去重 |
| 2 | `load_evidence_pool` / `save_evidence_pool`；模板文件 | `core/io.py`、`profiles/template/` | 池读写 |
| 3 | `resolve_*` 接入 gap / context | `evidence_resolve.py`、`gap.py`、`context.py` | 计数与摘要用物化证据 |
| 4 | `validate`：引用 id 须在池中存在；有引用则须有池文件 | `validate.py` | 非法引用 → error |
| 5 | CLI：`pool add`、`link`；保留内联 `add` | `cli.py` | 更新 YAML |
| 6 | Skill Tree：池编辑器 + 每技能多选引用 | `pages/1_Skill_Tree.py` | 同时保存池与树 |
| 7 | 文档 | `docs/evidence.md`、本节 | 描述池与迁移 |

### 5.3 验收标准

- `nblane gap Alice "复现 VLA"` 中物化计数示例：`solid (4 evidence)`（引用 + 内联合计四条）。
- `nblane context Alice` 对 solid/expert 节点包含**物化后**的证据摘要。
- Web：内联行 + 池多选 + 池展开区新增记录。
- 旧 skill-tree **无** `evidence` / `evidence_refs` 行为不变。
- **迁移（可选）**：重复内联条目迁入 `evidence-pool.yaml`，节点改为 `evidence_refs`，再运行 `nblane validate`。

### 5.4 Profile 摄入（LLM 辅助）

**目标：** 将 **简历 / 长文本** 或 **看板「已完成」任务** 转为对 `evidence-pool.yaml`、`skill-tree.yaml` 的结构化更新，并刷新 SKILL.md 生成块，且**不绕过**校验。

**契约：** LLM 输出 JSON：`evidence_entries`（池行）与 `node_updates`（按节点的 `evidence_refs`、可选内联 `evidence`、可选 `note`、可选 `status`）。**合并顺序：** 先池后树；**SKILL.md** 仅通过既有 `sync`（`write_generated_blocks`）。**默认：** 模型给出的节点 `status` **不写入**，除非 CLI 使用 `--allow-status-change` 或 Web 勾选允许。

**实现：** `core/profile_ingest.py`（`merge_ingest_patch`、`run_ingest_patch`、`apply_merged_profile`）；提示词与 `llm.chat` 在 `core/profile_ingest_llm.py`；与 gap 路由共享的 JSON 解析在 `core/jsonutil.py`。CLI：`nblane ingest-resume`、`nblane ingest-kanban`。Web：Home（概览）与看板折叠区。叙事与不变量见 [profile-documents-relationship.md](../profile-documents-relationship.md)。

**验收：** `--dry-run` 仅打印合并后的 YAML；成功写入后 `nblane validate` 通过，且存在 `SKILL.md` 时更新其中生成块。

---

## 6. Demo 1 Phase 2：MCP Server — Read Path

**目标**：Cursor 通过 MCP 拉取 nblane 上下文。

**前置**：Phase 1 完成（context 含证据摘要；含池与引用物化）。

### 6.1 技术选型

- **SDK**：Python `mcp` 官方 SDK
- **传输**：stdio（Cursor 启动 `python -m nblane.mcp_server`）
- **协议**：MCP resources（只读）

### 6.2 任务分解

| # | 任务 | 文件 | 验收 |
|---|------|------|------|
| 1 | MCP 骨架（stdio + FastMCP） | 新建 `mcp_server.py` | `python -m nblane.mcp_server` 可启动 |
| 2 | Resource: `profile://summary` | `mcp_server.py` | 返回树摘要 + 焦点 + 偏好 |
| 3 | Resource: `profile://kanban` | `mcp_server.py` | 当前看板 |
| 4 | Resource: `profile://gap/{task}` | `mcp_server.py` | 指定任务的 gap |
| 5 | Resource: `profile://context` | `mcp_server.py` | 完整 system prompt |
| 6 | Cursor 配置 | `.cursor/mcp.json` | Cursor 发现服务 |
| 7 | Profile 发现（自动或配置） | `mcp_server.py` | 环境变量或文件指定默认 profile |

### 6.3 验收标准

- 新 Cursor 会话：Agent 知用户、技能状态、当前工作，无需手动补背景。
- MCP resources 在 Cursor inspector 中可见。

---

## 7. Demo 1 Phase 3：MCP Server — Write Path

**目标**：外部工具向 nblane 回写。

**前置**：Phase 2 完成。

### 7.1 任务分解

| # | 任务 | 文件 | 验收 |
|---|------|------|------|
| 1 | Tool: `log_skill_evidence` | `mcp_server.py` + `io.py` | 更新 skill-tree 证据 |
| 2 | Tool: `append_growth_log` | `mcp_server.py` | 更新 Growth Log |
| 3 | Tool: `log_interaction` | `mcp_server.py` + `interaction.py` | `interactions/` 下文件 |
| 4 | Tool: `suggest_skill_upgrade`（先确认） | `mcp_server.py` | 仅建议，人工确认后写入 |
| 5 | 交互日志目录 | `io.py` + `interaction.py` | `profiles/{name}/interactions/` |
| 6 | 交互模型 | `models.py` + `interaction.py` | question / answer / skill_ids / timestamp |

### 7.2 验收标准

- 在 Cursor 中解决问题后可调用 `log_skill_evidence`。
- 对应 YAML 证据列表更新。
- 交互日志可审查。

---

## 8. Demo 1 Phase 4：方法结晶

**目标**：项目结束时将工作压缩为可复用方法。

**前置**：Phase 3（交互日志存在）。

### 8.1 任务分解

| # | 任务 | 文件 | 验收 |
|---|------|------|------|
| 1 | Tool: `crystallize_method` | `mcp_server.py` + `crystallize.py` | 日志 → LLM playbook |
| 2 | Playbook 存储 | `io.py` | `profiles/{name}/methods/` |
| 3 | 证据回写 | `crystallize.py` | Q/A → skill evidence |
| 4 | Human 确认 | `mcp_server.py` | 先 `_draft.md` 再定稿 |
| 5 | CLI `nblane crystallize <name> <project>` | `cli.py` | CLI 可触发 |

### 8.2 验收标准

- 复现 VLA 后可产出 playbook；含 Q/A；相关技能 evidence 更新。

---

## 9. Demo 1 Phase 5：Cursor Skill 集成

**目标**：nblane 上下文在 Cursor 中自动加载。

**前置**：Phase 1 + Phase 2。

### 9.1 任务分解

| # | 任务 | 文件 | 验收 |
|---|------|------|------|
| 1 | Cursor Rule 模板 | `.cursor/rules/nblane-context.mdc` | 含上下文摘要 |
| 2 | `nblane sync-cursor <name>` | `cli.py` | 从 profile 生成/刷新 rule |
| 3 | MCP + Rule 协同 | 文档 + 配置 | Rule 静态、MCP 动态 |

### 9.2 验收标准

- 打开 Cursor 即有能力概览；“帮我复现 VLA” 会考虑长短板。

---

## 10. 开发计划（Sprint 级）

### Sprint 1：Phase 1 — Skill Provenance（预估 3–4 天）— **已落地**

| 天 | 任务 | 产出 |
|----|------|------|
| D1 | Evidence 模型 + io + 单元测试 | `models.py`、`io.py`、`tests/test_evidence.py` |
| D2 | gap / context 证据感知 + 测试 | `gap.py`、`context.py`、`evidence_resolve.py` |
| D3 | CLI `evidence` + validate 扩展 | `cli.py`、`validate.py` |
| D4 | Web Skill Tree 证据 + 池 + 多选 | `pages/1_Skill_Tree.py` |

### Sprint 2：Phase 2 — MCP Read（预估 2–3 天）

| 天 | 任务 | 产出 |
|----|------|------|
| D1 | MCP 骨架 + profile://summary + profile://context | `mcp_server.py` |
| D2 | 其余 resources + Cursor 配置 + E2E | `mcp_server.py`、`.cursor/mcp.json` |

### Sprint 3：Phase 5 — Cursor Skill（预估 1–2 天）

| 天 | 任务 | 产出 |
|----|------|------|
| D1 | `sync-cursor` + rule 模板 | `cli.py`、`.cursor/rules/nblane-context.mdc` |
| D2 | MCP + Rule 联调 | 配置文档 |

Phase 5 安排在 Sprint 3 因仅依赖 Phase 1 + 2，可先于 Phase 3/4 闭合 Cursor read-path。

### Sprint 4：Phase 3 — MCP Write（预估 3–4 天）

| 天 | 任务 | 产出 |
|----|------|------|
| D1 | `log_skill_evidence` + `append_growth_log` | `mcp_server.py` |
| D2 | Interaction 模型 + 存储 + `log_interaction` | `interaction.py`、`models.py` |
| D3 | `suggest_skill_upgrade` + 确认流 | `mcp_server.py` |
| D4 | Cursor 写回 E2E | 测试 |

### Sprint 5：Phase 4 — 结晶（预估 2–3 天）

| 天 | 任务 | 产出 |
|----|------|------|
| D1 | `crystallize.py` + methods 存储 | `crystallize.py`、`io.py` |
| D2 | MCP tool + 确认 + CLI | `mcp_server.py`、`cli.py` |
| D3 | Demo 1 全链路 E2E + 文档 | 测试、文档 |

### 合计：Demo 1 五阶段约 12–16 人天

---

## 11. 命令一览（规划与现状）

| 命令 | 状态 | Sprint | 说明 |
|------|------|--------|------|
| `init` | 已实现 | — | 创建 profile |
| `context` | 已实现 | S1 更新 | system prompt；含证据摘要（物化） |
| `status` | 已实现 | — | 技能树摘要 |
| `log` | 已实现 | — | Growth Log |
| `sync` | 已实现 | — | SKILL.md 生成块 |
| `validate` | 已实现 | S1 更新 | 含证据与 evidence_refs 校验 |
| `gap` | 已实现 | S1 更新 | 输出含物化证据计数 |
| `team` | 已实现 | — | 团队池 |
| `evidence` | **已实现** | S1 | 内联 + `pool add` + `link`（见 §5） |
| `sync-cursor` | Sprint 3 | S3 | 刷新 Cursor rule |
| `crystallize` | Sprint 5 | S5 | 触发结晶 |

---

## 12. 实现 vs 产品（快速映射）

| 产品概念 | 实现 | 状态 |
|----------|------|------|
| `can_solve` / `detect_gap` | `gap.py`、`nblane gap` | 已实现 |
| 数据校验 | `validate.py`、`nblane validate` | 已实现 |
| Agent profile | `agent-profile.yaml`、`context` | 已实现 |
| Team OS / 共享池 | `teams/…/team.yaml`、`product-pool.yaml` | 已实现 |
| Web UI | `app.py`、`pages/` | 已实现 |
| LLM 增强 gap | `llm.py`、Gap 页 | 已实现 |
| Skill Provenance（内联 + 池 + 引用） | `models.py`、`evidence_resolve.py`、`io.py`、`cli`、Skill Tree | **已实现** |
| MCP Server (Read) | `mcp_server.py` | Sprint 2 |
| Cursor Skill | `.cursor/rules/`、`sync-cursor` | Sprint 3 |
| MCP Server (Write) | `mcp_server.py`、`interaction.py` | Sprint 4 |
| 方法结晶 | `crystallize.py` | Sprint 5 |
| `sync_team_pool` / `route_to_best_owner` | 未实现 | 路线图 |
| 公开页导出 | 未实现 | 路线图 |

---

## 13. 技术约束（Demo 1 整体）

- **传输**：stdio（本地子进程，无网络服务）
- **MCP SDK**：Python `mcp` 官方包
- **LLM**：仅 Phase 4 结晶强依赖；其余以规则为主
- **存储**：纯文件（YAML + Markdown + JSON），无数据库
- **安全**：写入可见；技能升级需人工确认
- **兼容性**：`evidence` / `evidence_refs` 默认空；旧 YAML 无需改即可用

---

## 14. 版本历史

| 文档版本 | 说明 |
|----------|------|
| `v0.1.0` | 首版：M0–M3 落地与 M4–M5 路线 |
| `v0.2.0` | 重写：基线盘点；Demo 1 五阶段与 Sprint 计划 |
| （持续） | 对齐 Phase 1 证据池、引用与物化层实现 |
