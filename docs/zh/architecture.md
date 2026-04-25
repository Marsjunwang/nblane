# 架构与设计原则

## 与产品愿景（v0.2）的关系

完整产品定义——Human OS 与 Agent OS、共进化引擎、Agent 角色（技能镜像、
任务推理等）、MVP 分层与最小 Demo——见 [product.md](product.md)。**分阶段实现
与里程碑**见 [设计手册](design.md)。**本文描述当前仓库已实现的内容**及其工程原则。

**大致对应：**

- **当前代码：** Profile 数据层 + 规则层 + 薄 CLI（**13 条子命令**）+ 完整 Web UI；
  已完成 Demo 1 之前的全部地基工作（M0–M3），包括 `gap` 规则层分析、
  `context` 系统提示生成（含 agent-profile 拼入）、Streamlit 四页交互界面、
  团队共享池目录约定；**Skill Provenance**（证据池、引用、物化）已落地；
  **Profile 摄入**（简历 / 看板 Done → LLM JSON → 合并池与树 → `validate` + `sync`）
  已作为应用层交付。详见 [设计手册 §5–5.4](design.md)、
  [Profile 文档关系](../profile-documents-relationship.md)。
- **下一步（Demo 1）：** MCP 已提供 **Read（resources）+ Write（tools）** 初版，
  `crystallize` / `sync-cursor` CLI 已接好；可按 [设计手册 §6–9](design.md) 继续加深。
- **仍属路线图：** `sync_team_pool` / `route_to_best_owner` 的完整产品化、
  公开页导出与托管服务。

若某能力只出现在 [product.md](product.md) 而本文未写，在代码落地前视为
**意图**。

## 当前实现速览（Demo 1 基线）

| 能力 | 状态 | 实现位置 |
|------|------|----------|
| Profile 结构 (SKILL.md / skill-tree / **evidence-pool** / kanban / agent-profile) | 已实现 | `profiles/`, `core/models.py`, `core/io.py` |
| 领域关卡图 (Schema) | 已实现 | `schemas/*.yaml`, `core/models.py` |
| `init` / `context` / `status` / `log` / `sync` / **`evidence`** / **`ingest-resume`** / **`ingest-kanban`** / **`health`** / **`sync-cursor`** / **`crystallize`** | 已实现 | `cli.py`, `commands/`, `core/context.py`, `core/status.py`, `core/sync.py`, `core/profile_ingest.py`, `core/profile_ingest_llm.py`, `core/profile_health.py`, `core/cursor_rule.py`, `core/crystallize.py` |
| `validate`（skill-tree 校验） | 已实现 | `core/validate.py` |
| `gap`（规则层任务缺口） | 已实现 | `core/gap.py` |
| `team`（团队池汇总） | 已实现 | `core/team.py` |
| `agent-profile.yaml` 拼入 `context` | 已实现 | `core/context.py` |
| `teams/` 共享池 (team.yaml + product-pool.yaml) | 已实现 | `teams/`, `core/io.py`, `core/team.py` |
| Web UI (Skill Tree / Gap / Kanban / Team View / Profile Health / SKILL.md) | 已实现 | `app.py`, `pages/`（5 页）；Home **简历摄入**；Kanban **已完成→证据摄入**；Profile Health 只读 |
| Web UI 中英文（单一开关） | 已实现 | `core/llm.py`（`LLM_REPLY_LANG`）、`web_i18n.py` |
| Gap 分析（规则 + 可选 LLM 路由 + 学习关键词） | 已实现 | `core/gap.py`、`core/gap_llm_router.py`、`core/learned_keywords.py`、`pages/2_Gap_Analysis.py` |
| LLM 教练与追问（可选） | 已实现 | `core/llm.py`、`pages/2_Gap_Analysis.py` |
| Skill Provenance（内联 + 池 + `evidence_refs` + 物化） | 已实现 | `core/models.py`、`core/evidence_resolve.py`、`core/evidence_pool_id.py` 等 |
| Profile 摄入（合并 + 校验 + sync；简历/看板提示） | 已实现 | `core/profile_ingest.py`、`core/ingest_*.py`、`core/profile_ingest_llm.py`、`core/jsonutil.py` |
| Profile Health / Growth Review（校验 + sync + 证据 + 看板检查） | 已实现 | `core/profile_health.py`、`commands/health.py`、`pages/5_Profile_Health.py` |
| MCP Server (Read + Write) | **初版已实现** | `mcp_server.py`（stdio）；可执行 `nblane-mcp` |
| 交互日志 + 方法结晶 | **初版已实现** | `core/interaction.py`、`core/crystallize.py`；MCP tool + `crystallize` CLI |
| Cursor Skill 集成 | **初版已实现** | `nblane sync-cursor` → `.cursor/rules/nblane-context.mdc` |
| 公开页导出、托管服务 | **未实现** | 路线图 M5+ |

## 核心想法

nblane 基于一个判断：**一个人的知识、品味与成长轨迹，可以表示成人类与
AI 都能读的结构化文本**。

这份文本就是 `SKILL.md`，即你的系统提示（system prompt）。

## 分层

```
profiles/{name}/
├── SKILL.md          <- 先验（Agent 读取）
├── skill-tree.yaml   <- 结构化进度（含 evidence / evidence_refs）
├── evidence-pool.yaml <- 共享证据目录（稳定 id）
├── kanban.md         <- 当前在做什么
├── agent-profile.yaml <- Agent 对用户的结构化理解
├── papers/           <- 研究笔记
├── projects/         <- 项目记录
└── log.md            <- 可选溢出日志
```

`schemas/` 存放领域技能树定义，可理解为「关卡全图」——该领域可能出现的全部
节点。每个人的 `skill-tree.yaml` 是在其上的个人叠加层。

`src/nblane/` 为 Python 包，保持薄而清晰；**数据**是产品，软件不是。

## 模块清单

```
src/nblane/
├── __init__.py         # 版本号
├── cli.py              # CLI 入口（解析与分发）
├── commands/           # CLI 命令实现
├── mcp_server.py       # MCP stdio：resources + write tools
├── web_shared.py       # Streamlit 共享工具（profile 选择器）
├── web_i18n.py         # 界面文案（en/zh），由 LLM_REPLY_LANG 决定
└── core/
    ├── models.py       # SkillNode / SkillTree / Schema / GapResult 等数据类
    ├── io.py           # 文件 I/O 兼容 facade
    ├── profile_io.py   # Profile / SKILL.md / skill-tree / evidence-pool
    ├── schema_io.py    # Schema 加载与原始 schema helper
    ├── kanban_io.py    # Kanban parse/render/save/archive
    ├── team_io.py      # team.yaml 与 product-pool.yaml
    ├── paths.py        # 仓库路径常量
    ├── gap.py          # 任务-技能匹配 + 前置闭包 + 缺口检测
    ├── gap_llm_router.py  # LLM：任务 → schema 节点 id（+ keywords JSON）
    ├── jsonutil.py     # 从模型输出中提取 JSON 对象（与路由等共享）
    ├── learned_keywords.py # 按 schema 持久化的学习关键词（schemas/.learned/）
    ├── context.py      # system prompt 生成
    ├── validate.py     # skill-tree 校验
    ├── sync.py         # SKILL.md 生成块同步
    ├── status.py       # 技能树摘要统计
    ├── team.py         # 团队汇总
    ├── profile_ingest.py   # 摄入 API 兼容 facade
    ├── ingest_*.py         # 摄入 parse / merge / preview / apply
    ├── profile_health.py   # 只读成长体检
    ├── profile_ingest_llm.py  # 简历 / 看板 Done → 结构化 JSON（中/英）
    └── llm.py          # OpenAI 兼容 LLM 客户端 + 回复语言
```

```
pages/
├── 1_Skill_Tree.py     # 技能树可视化编辑 + 证据池与引用
├── 2_Gap_Analysis.py   # 规则 + 可选 LLM 首轮路由 + AI 教练 + 写回
├── 3_Kanban.py         # 看板编辑 + 已完成→证据摄入
├── 4_Team_View.py      # 团队与产品池编辑
└── 5_Profile_Health.py # 只读成长体检
```

## Web 界面语言（中 / 英）

Streamlit 文案集中在 **`web_i18n.py`**。当前语言**不是**页面内单独控件切换，
而是与 **`.env` 中的 `LLM_REPLY_LANG`**（默认 `en`，或 `zh`）一致，经
`llm.reply_language()` 供 `home_ui()`、`gap_ui()`、`skill_tree_ui()`、
`kanban_ui()`、`team_ui()`、`common_ui()` 使用。差距分析与 **LLM 路由**
使用对应语言的 system prompt，保证界面语言与模型行为一致。

**布局约定：** 各页在 `select_profile()` 之后再渲染主标题；团队页说明侧栏档案与
`teams/` 数据的关系。可选 **`NBLANE_UI_EMOJI=0`** 关闭指标与状态行前的 emoji。
信息架构与动线见 [web-ui-product.md](web-ui-product.md)；使用步骤见 [web-ui.md](web-ui.md)。

## Profile 摄入管线（当前实现）

可选 **LLM** 将 **简历文本**（`ingest-resume`、Home 折叠区）或 **看板 Done 任务**
（`ingest-kanban`、看板折叠区）转为单一 JSON 补丁（`evidence_entries` +
`node_updates`）。**`profile_ingest.merge_ingest_patch`** 按 **先池后树** 合并；
**`run_ingest_patch`** 写 YAML、执行 **`validate_one`**、再 **`write_generated_blocks`**，
校验或同步失败则恢复文件。模型中的 **`status`** 仅在 CLI **`--allow-status-change`**
或 Web 勾选时写入。**`--dry-run`** 仅在内存中合并并打印 YAML。详见 [设计手册 §5.4](design.md)。

## Gap 分析管线（当前实现）

1. **根节点：** 可选 **规则重叠**（`tokenize` + 同义词扩展，含中文连续字）
与/或 **LLM 路由**（`gap_llm_router.route_task_to_nodes` → JSON
`node_ids` + `keywords`，经 schema 索引校验）。也可 **手动** 指定单个
schema 节点。规则打分可叠加按 schema 加载的 **学习关键词**。
2. **闭包：** 依赖闭包（`requires_closure`）按确定性拓扑序展开，再相对
当前 profile 技能树做 **缺口** 判定。
3. **持久化：** 路由与教练回复中的 **双语关键词** 可合并入
`schemas/.learned/<schema>.yaml`（`learned_keywords`，每节点有上限），
后续规则匹配可受益而无需额外调用 API。
4. **界面：** `pages/2_Gap_Analysis.py` 提供开关、指标、闭包列表、可选
**AI 教练**（首轮 + **`chat_messages` 追问**）以及 **写回** 面板更新
`skill-tree.yaml`。

## 设计规则（早期勿过度工程）

1. **纯文本优先。** `SKILL.md` 用 Markdown，`skill-tree.yaml` 用 YAML，无自造格式。
2. **Git 即数据库。** 每次更新是一次提交，diff 即成长史。
3. **Agent 集成一条命令。** `nblane context <name>` 打印系统提示，结束。
4. **Schema 可选。** 只有 `SKILL.md`、没有 `skill-tree.yaml` 也能用。
5. **不强制 SKILL.md 结构。** 各节是约定而非校验；写真实内容即可。
6. **模块内聚。** `core/` 下一个文件一个职责；新增能力新建文件，不膨胀已有模块。

## 共进化模型

```
你更新 SKILL.md
        |
nblane context -> 系统提示
        |
Agent 按新先验校准
        |
Agent 按你当前水平协助工作
        |
你成长，SKILL.md 略滞后，你再更新
        |
        （循环数年）
```

今天的 `SKILL.md` 与一年前的差分，是可机读的成长记录，这就是产物。

## 多人设计

每个 profile 独立，无共享数据库。README 里的「crew」表目前手写维护——未来可
用 dashboard 从 profile 生成。

团队级共享对象见 `teams/<team_id>/`（`team.yaml` + `product-pool.yaml`），
由团队自行约定可见范围；仍无中心化服务。汇总命令：`nblane team <team_id>`。

社交是涌现的：仓库里能看到彼此技能树，自然发现平行或缺口。0 阶段不需要
游戏化。

产品愿景里后续包含 **Agent 增强**的连接与 IP 流程；本仓库**不**实现完整
社交产品——只有纯文本 profile 与可选 crew 表。

## 这不是什么

- 不是托管型社交网络（未来设想见 [product.md](product.md)；当前范围仍是
  本地/基于 Git 的文件）
- 不是任务管理器
- 不是简历生成器（但数据可反哺简历）
- 不是课程平台

它是**面向 Agent 可读的结构化个人知识库**。
