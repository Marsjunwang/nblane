# Web 使用手册（Streamlit）

本文说明如何**运行与操作**本地 Streamlit 界面。信息架构、首屏原则与 backlog 见
[web-ui-product.md](web-ui-product.md)；页面清单与文件映射见
[design.md §3.4](design.md)。

| 项目 | 说明 |
|------|------|
| 入口 | 在仓库根目录执行 `streamlit run app.py` |
| 范围 | `app.py` + `pages/*.py`；这是文件驱动的私有工作台。Public Site 页面会构建静态公开产物，但 Streamlit 应用本身**不是**托管公开站点 |

---

## 1. 前置条件

1. 安装：`pip install -e .`（见 [setup.md](setup.md)）。
2. 至少一个 `profiles/` 下的档案（`nblane init <名称>`）。
3. 可选 **LLM**：在 `.env` 配置 `LLM_API_KEY` 等，以使用差距页 AI 教练、首页简历摄入、看板「已完成→证据」。未配置时仍可使用规则差距分析与全部非 AI 编辑。

---

## 2. 语言与显示

- **`.env` 中的 `UI_LANG`**：`en`（默认）或 `zh`。控制 `web_i18n.py`
  提供的 **Streamlit 界面文案**。若未设置，为兼容旧部署，会回退到
  `LLM_REPLY_LANG`。
- **`.env` 中的 `LLM_REPLY_LANG`**：`en`（默认）或 `zh`。控制模型回复语言，
  以及差距分析、摄入等 AI 路径使用的 **LLM 系统提示语言**。它可以和
  `UI_LANG` 不同，例如中文界面配英文模型输出。
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
6. 导出上下文前或阶段复盘时打开 **Profile Health**。
7. 整理公开资料、博客、简历、项目/成果草稿或构建静态站时打开 **Public Site**。

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
- 四列：进行中、队列、已完成、也许/将来（显示名随 `UI_LANG` 切换）。
- 新建与编辑任务时，**按列只突出主字段**（如进行中：背景 + 开始日；队列：原因 + 阻塞；已完成：结果 + 背景）；其余在 **「更多字段」** 折叠中填写（详见 [看板使用手册 · §4](kanban.md)）。
- 任务下可维护 **子任务（勾选）** 与自由备注。
- **移动列** 用列名 **按钮**（非「完成状态」菜单）；可选 **自动填写开始/结束日期**（移入进行中/已完成时）。
- **「已完成」列整理** — 多选后 **归档所选**（写入 `kanban-archive.md`）或 **删除所选**；说明见 [kanban-archive.md](kanban-archive.md)。
- **已完成 → 证据** 折叠区 — 多选 Done 任务生成草案后，可按条勾选 **采纳** 证据行与节点更新，**应用所选条目**（或 **应用完整草案**）；可选 **应用后标记已结晶**。流程对齐 `nblane ingest-kanban`，Web 侧重分项审阅。
- **本轮看板优化方向**：`kanban.md` 使用稳定 task id（保留 `id` meta 行；
  无 id 的旧任务会生成兼容 id），并明确拖拽方向：纵向指针位置决定插入
  `to_index`；拖入另一列会映射为 `to_section`，再沿用手动移动的 done flag /
  自动日期规则。页面级拖拽逐步接入期间，显式移动控件仍是可靠 fallback。

### 5.5 团队视图（`pages/4_Team_View.py`）

- 选择 **团队**（`teams/` 下目录名）。
- 编辑团队字段与各 **产品池** tab，保存 `team.yaml` 与
  `product-pool.yaml`。

### 5.6 Profile Health（`pages/5_Profile_Health.py`）

- 只读报告，与 `nblane health <名称>` 同源。
- 检查校验结果、生成块 drift、solid/expert 节点缺证据、Done 任务未结晶。
- 不写入 profile 文件。

### 5.7 Public Site（`pages/6_Public_Site.py`）

- 为当前档案初始化缺失的公开层文件。
- **Profile** 编辑公开姓名、headline、简介、联系方式、头像、原始 YAML，并提供
  实时整站预览。
- **Blog** 通过 React / BlockNote 编辑器 shell 管理 draft / published 文章，
  支持结构化 front matter、媒体插入、AI 候选、发布检查、公开页预览，以及
  Streamlit 承接的新建/上传辅助工具。
- **Resume** 编辑 `resume-source.yaml`，预览生成 Markdown，并生成定制简历草稿。
- **Known Info** 将选中的 evidence 整理成 draft 公开项目。
- **Build** 校验并写出静态站，默认到 `dist/public/<profile>`，也可指定输出目录；
  可填写生产 `Base URL` 以生成 SEO 与子路径部署链接。

---

## 6. 与 CLI 的对照

| Web 操作 | CLI |
|----------|-----|
| 简历 / 长文本摄入 | `nblane ingest-resume <名称> …` |
| 已完成 → 证据 | `nblane ingest-kanban <名称> …` |
| 导出上下文 | `nblane context <名称>` |
| 差距结果 | `nblane gap <名称> "…"` |
| 编辑后检查 | `nblane validate <名称>` |
| 成长体检 / Profile Health | `nblane health <名称>` |
| SKILL.md 生成块 | `nblane sync <名称> --write` |
| 证据池 / 内联 | `nblane evidence <名称> …` |
| 公开站校验 / 构建 | `nblane public validate <名称>` / `nblane public build <名称>` |
| 博客与简历草稿 | `nblane public blog …`、`nblane public draft-blog …`、`nblane public draft-resume …` |

详见 [profile-documents-relationship.md](../profile-documents-relationship.md)、
[evidence.md](evidence.md)、[public-site.md](public-site.md)。

---

## 7. 相关文档

- [Web 体验设计（Streamlit）](web-ui-product.md) — 信息架构、品牌、backlog
- [设计手册 §3.4](design.md) — 已交付页面表
- [架构 — Web 界面语言](architecture.md)
- [公开个人网站、博客与简历](public-site.md) — Public Surface v1
- [MCP 服务器](mcp.md) — Cursor 集成（非 Streamlit）

**English:** [../web-ui.md](../web-ui.md)
