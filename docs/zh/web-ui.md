# Web 使用手册（Streamlit）

本文说明如何**运行与操作**本地 Streamlit 界面。信息架构、首屏原则与 backlog 见
[web-ui-product.md](web-ui-product.md)；页面清单与文件映射见
[design.md §3.4](design.md)。

| 项目 | 说明 |
|------|------|
| 入口 | 在仓库根目录执行 `streamlit run app.py` |
| 范围 | `app.py` + `pages/*.py`；数据为本地文件，**非**托管公开站点 |

---

## 1. 前置条件

1. 安装：`pip install -e .`（见 [setup.md](setup.md)）。
2. 至少一个 `profiles/` 下的档案（`nblane init <名称>`）。
3. 可选 **LLM**：在 `.env` 配置 `LLM_API_KEY` 等，以使用差距页 AI 教练、首页简历摄入、看板「已完成→证据」。未配置时仍可使用规则差距分析与全部非 AI 编辑。

---

## 2. 语言与显示

- **`.env` 中的 `LLM_REPLY_LANG`**：`en`（默认）或 `zh`。控制 `web_i18n.py`
  提供的**整站界面文案**，以及差距分析、摄入相关 **LLM 系统提示语言**，
  使界面与模型行为一致。
- **`NBLANE_UI_EMOJI`**：设为 `0`、`false`、`no` 或 `off` 时，关闭首页指标、
  技能状态行、看板列标题、团队池 tab 等处的 emoji 前缀（见
  [architecture.md](architecture.md)「Web 界面语言」）。
- **`NBLANE_ROOT`**：若自动解析到的仓库不对，设为包含 `profiles/` 的目录。

---

## 3. 侧栏：当前档案

- **当前档案** — 决定加载哪一份 `profiles/<名称>/` 数据。
- **新建档案** — 展开区效果同 `nblane init`。
- 在页面间切换时，选择会通过会话状态保持。

在 **团队视图** 中，读写始终针对 **`teams/`**。页面说明侧栏档案用于首页、
技能树、差距、看板；**团队数据不按档案过滤**。

---

## 4. 推荐动线（首次）

1. 侧栏选定档案。
2. 打开 **技能树** — 看状态、备注、内联证据、证据池与引用；点 **保存**
   写入 `skill-tree.yaml`、`evidence-pool.yaml` 并尽量同步 SKILL.md 生成块。
3. 大任务前打开 **差距分析** — 填写任务、分析；若已配置 LLM 可开 AI 教练。
4. **看板** 管理日常推进；**已完成** 任务可通过折叠区 **摄入为证据**。
5. 协作编辑共享池时用 **团队视图**。

产品层地图见 [web-ui-product.md §4](web-ui-product.md)。

---

## 5. 分页面说明

### 5.1 首页（`app.py`）

- **标题与说明** — 浏览器标签与子页统一为「功能 · nblane」风格；标题下
  caption 标明当前档案与 **私人操作系统** 叙事。
- **标签页**
  - **概览** — 技能指标、分类进度；**简历 / 长文本** 摄入在折叠区内。
    底部为紧凑 **侧栏导航提示**（`st.info`）与 **详细页面说明**（可折叠）。
  - **结构化编辑** — 按 SKILL.md 章节编辑（生成块有自动覆盖提示）。
  - **原文** — 整份 SKILL.md 源码。
- **简历摄入** — 生成草案 → 预览合并 YAML → **写入** 与
  `nblane ingest-resume` 同一路径（校验 + 同步，失败回滚）。可选勾选允许
  LLM 更新 **status**（语义同 CLI `--allow-status-change`）。

### 5.2 技能树（`pages/1_Skill_Tree.py`）

- **保存** 在**标题行右侧**（与本页约定一致，区别于看板工具栏）。
- 按分类标签、等级浏览；每节点可改状态、备注、内联证据。
- **证据池** 折叠区维护共享目录；节点可多选 **引用** 池 id。**保存** 一次
  落盘树 + 池并尝试同步 SKILL.md。

### 5.3 差距分析（`pages/2_Gap_Analysis.py`）

- 输入任务 → **分析**（规则匹配；可选 AI 首轮路由或手动选节点）。
- 展示匹配、依赖闭包、建议下一步。
- **AI 分析** 区 — 已配置 LLM 时为教练与追问；未配置时统一 **未配置 AI**
  提示（与首页、看板一致）。
- **写回** — 勾选缺口节点并选择新状态，写回 `skill-tree.yaml`。

### 5.4 看板（`pages/3_Kanban.py`）

**详细步骤与 FAQ：** [看板使用手册](kanban.md)。

- 工具栏 **从文件重新加载** / **保存** — 对应 `kanban.md`。
- 四列：进行中、队列、已完成、也许/将来（显示名随语言切换）。
- 新建与编辑任务时，**按列只突出主字段**（如进行中：背景 + 开始日；队列：原因 + 阻塞；已完成：结果 + 背景）；其余在 **「更多字段」** 折叠中填写（详见 [看板使用手册 · §4](kanban.md)）。
- 任务下可维护 **子任务（勾选）** 与自由备注。
- **移动列** 用列名 **按钮**（非「完成状态」菜单）；可选 **自动填写开始/结束日期**（移入进行中/已完成时）。
- **「已完成」列整理** — 多选后 **归档所选**（写入 `kanban-archive.md`）或 **删除所选**；说明见 [kanban-archive.md](kanban-archive.md)。
- **已完成 → 证据** 折叠区 — 多选 Done 任务生成草案后，可按条勾选 **采纳** 证据行与节点更新，**应用所选条目**（或 **应用完整草案**）；可选 **应用后标记已结晶**。流程对齐 `nblane ingest-kanban`，Web 侧重分项审阅。

### 5.5 团队视图（`pages/4_Team_View.py`）

- 选择 **团队**（`teams/` 下目录名）。
- 编辑团队字段与各 **产品池** tab，保存 `team.yaml` 与
  `product-pool.yaml`。

---

## 6. 与 CLI 的对照

| Web 操作 | CLI |
|----------|-----|
| 简历 / 长文本摄入 | `nblane ingest-resume <名称> …` |
| 已完成 → 证据 | `nblane ingest-kanban <名称> …` |
| 导出上下文 | `nblane context <名称>` |
| 差距结果 | `nblane gap <名称> "…"` |
| 编辑后检查 | `nblane validate <名称>` |
| SKILL.md 生成块 | `nblane sync <名称> --write` |
| 证据池 / 内联 | `nblane evidence <名称> …` |

详见 [profile-documents-relationship.md](../profile-documents-relationship.md)、
[evidence.md](evidence.md)。

---

## 7. 相关文档

- [Web 体验设计（Streamlit）](web-ui-product.md) — 信息架构、品牌、backlog
- [设计手册 §3.4](design.md) — 已交付页面表
- [架构 — Web 界面语言](architecture.md)
- [MCP 服务器](mcp.md) — Cursor 集成（非 Streamlit）

**English:** [../web-ui.md](../web-ui.md)
