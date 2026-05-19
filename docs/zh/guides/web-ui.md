---
status: active
owner: docs
last_verified: 2026-05-13
source_of_truth: true
---

# Web 使用手册（Streamlit）

本文说明如何**运行与操作**本地 Streamlit 界面。信息架构、首屏原则与 backlog 见
[Web 体验设计](../product/web-experience.md)；页面清单与文件映射见
[当前状态](../project/status.md)。

| 项目 | 说明 |
|------|------|
| 入口 | 在仓库根目录执行 `streamlit run app.py` |
| 范围 | `app.py` + `pages/*.py`；这是文件驱动的私有工作台。Public Site 页面会构建静态公开产物，但 Streamlit 应用本身**不是**托管公开站点 |

---

## 1. 前置条件

1. 安装：`pip install -e .`（见 [安装与 LLM 配置](setup.md)）。
2. 至少一个 `profiles/` 下的档案（`nblane init <名称>`）。
3. 可选 **LLM**：在 `.env` 配置 `LLM_API_KEY` 等，以使用差距页 AI 教练、首页简历摄入、看板「已完成→证据」。看板页也可选择本地 **Codex** 作为只读 AI backend，替代看板内的 LLM 动作。未配置时仍可使用规则差距分析与全部非 AI 编辑。

---

## 2. 语言与显示

- **`.env` 中的 `UI_LANG`**：`en`（默认）或 `zh`。控制 `web_i18n.py`
  提供的 **Streamlit 界面文案**，不受 `LLM_REPLY_LANG` 影响。
- **`.env` 中的 `LLM_REPLY_LANG`**：`en`（默认）或 `zh`。控制模型回复语言，
  以及差距分析、摄入等 AI 路径使用的 **LLM 系统提示语言**。它可以和
  `UI_LANG` 不同，例如中文界面配英文模型输出。
- **`NBLANE_UI_EMOJI`**：设为 `0`、`false`、`no` 或 `off` 时，关闭首页指标、
  技能状态行、看板列标题、团队池 tab 等处的 emoji 前缀（见
  [架构总览](../architecture/overview.md)）。
- **`NBLANE_ROOT`**：若自动解析到的仓库不对，设为包含 `profiles/` 的目录。

---

## 3. 侧栏：当前档案

- **当前档案** — 决定加载哪一份 `profiles/<名称>/` 数据。
- **新建档案** — 展开区效果同 `nblane init`。
- 在页面间切换时，选择会通过会话状态保持。

在 **团队视图** 中，读写始终针对 **`teams/`**。页面说明侧栏档案用于首页、
技能树、差距、看板；**团队数据不按档案过滤**。

### 3.1 侧栏 AI / LLM

- **看板 AI 引擎** — 按当前档案选择看板 AI 动作使用普通 LLM 还是本地只读
  Codex。第一版只影响看板的 gap、拆子任务、任务理解和 Done -> evidence。
- **LLM 设置** — provider、base URL、模型、API key、界面语言和模型回复语言仍按
  当前会话生效，不写入磁盘。
- **Codex 状态与配置** — 侧栏显示安装 / 登录状态和配置文件路径；点击
  **配置 Codex** 打开大弹窗，编辑 `~/.codex/config.toml`、通过 Codex CLI 写入
  API key/auth，并编辑当前 profile 的 `profiles/<name>/codex.yaml`。

---

## 4. 推荐动线（首次）

1. 侧栏选定档案。
2. 打开 **技能树** — 看状态、备注、内联证据、证据池与引用；点 **保存**
   写入 `skill-tree.yaml`、`evidence-pool.yaml` 并尽量同步 SKILL.md 生成块。
3. 打开 **Evidence Review** — 审阅 Done 任务摄入、编辑证据引用，并从已确认 evidence 生成 claim candidates。
4. 大任务前打开 **差距分析** — 手动输入，或直接选择 current goal / Kanban task 作为上下文；若已配置 LLM 可开 AI 教练。
5. **看板** 管理日常推进；**已完成** 任务可通过折叠区 **摄入为证据**。
6. 协作编辑共享池时用 **团队视图**。
7. 导出上下文前或阶段复盘时打开 **Profile Health**。
8. 资料阅读和研究写作用 **Research Workspace**；整理公开资料、博客、简历、项目/成果草稿时打开 **Output Studio**，校验和构建静态站时打开 **Public Build**。

中文界面的侧栏采用双语标签：中文任务名在前，英文对象名在后，例如
**研究工作台 Research**、**输出工作台 Studio**、**公开构建 Build**。
英文别名用于对照文档、文件名和 CLI，不代表需要在中文界面里用英文理解页面职责。

产品层地图见 [Web 体验设计](../product/web-experience.md)。

---

## 5. 分页面说明

### 5.1 首页（`app.py`）

- **标题与说明** — 浏览器标签与子页统一为「功能 · nblane」风格；标题下
- **首屏摘要** — 首页先用原生 Streamlit 渲染 Scope strip、当前目标、本周执行、
  待整理证据与主操作，避免 React 图谱加载时出现“空首页”。
- **上下文画布** — React Dashboard / Context Canvas 下移到稳定摘要之后，用来浏览
  `Source -> Evidence -> Claim -> Skill / Output` 的当前投影。
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

### 5.3 Evidence Review（`pages/2_Evidence_Review.py`）

- **审阅队列** — 承接看板 Done -> Evidence 的候选流，人工选择后才写入
  `evidence-pool.yaml` 和必要的 `skill-tree.yaml` 引用。
- **Claim Candidates** — 选择 1-N 条 evidence 后生成 claim candidates；候选只在
  当前会话预览中存在，点击 **应用所选** 后才写入 `evidence-pool.yaml` 顶层
  `claims` 列表。
- Claim card 会展示文本、类型、支撑 evidence、关联 skill、公开准备度、置信度
  和 warning。应用 claim 不会自动改 `skill-tree.yaml` status，也不会创建独立
  `claims.yaml`。
- **证据池 / 链接 / 引用 / 风险** — 继续维护 evidence row、skill/project/
  experience/source refs 和断链提示；保存路径会保留已有 `claims`。

### 5.4 差距分析（`pages/2_Gap_Analysis.py`）

- 选择上下文来源：**手动输入**、**Current goal**、**Kanban task**。页面会优先复用
  上次选择；否则优先选择 Doing / Queue task，再选择允许进入 Agent context 的
  current goal，最后回退手动输入。
- 选择 Kanban task 时，任务正文会自动带入 title、context、why、outcome、
  blocked_by、dates、subtasks、details，不需要重复手输任务描述。
- private goal 或 `include_in_agent_context=false` 的 goal 不会出现在 Current goal
  选项中。手动输入和 Kanban task 默认可附加 privacy-safe current goal context；
  Current goal source 本身不会重复追加 goal context。
- 点击 **分析** 后执行规则匹配；可选 AI 首轮路由或手动选节点。
- 展示匹配、依赖闭包、建议下一步。
- 结果会显示来源 provenance，例如 manual / current goal / kanban task，以及是否使用了 current goal context。
- **AI 分析** 区 — 已配置 LLM 时为教练与追问；未配置时统一 **未配置 AI**
  提示（与首页、看板一致）。
- **写回** — 勾选缺口节点并选择新状态，写回 `skill-tree.yaml`。

### 5.5 看板（`pages/3_Kanban.py`）

**详细步骤与 FAQ：** [看板使用手册](kanban.md)。

- 工具栏 **从文件重新加载** / **保存** — 对应 `kanban.md`。
- 四列：进行中、队列、已完成、也许/将来（显示名随 `UI_LANG` 切换）。
- 新建与编辑任务时，**按列只突出主字段**（如进行中：背景 + 开始日；队列：原因 + 阻塞；已完成：结果 + 背景）；其余在 **「更多字段」** 折叠中填写（详见 [看板使用手册 · §4](kanban.md)）。
- 任务下可维护 **子任务（勾选）** 与自由备注。
- **移动列** 用列名 **按钮**（非「完成状态」菜单）；可选 **自动填写开始/结束日期**（移入进行中/已完成时）。
- **「已完成」列整理** — 多选后 **归档所选**（写入 `kanban-archive.md`）或 **删除所选**；说明见 [看板使用手册](kanban.md)。
- **已完成 → 证据** 折叠区 — 多选 Done 任务生成草案后，可按条勾选 **采纳** 证据行与节点更新，**应用所选条目**（或 **应用完整草案**）；可选 **应用后标记已结晶**。流程对齐 `nblane ingest-kanban`，Web 侧重分项审阅。
- 侧栏 **AI / LLM** 中的 **看板 AI 引擎** 可在普通 LLM 与本地 Codex 间切换；选择 Codex 时，Gap 节点路由、拆任务、任务理解和 Done → evidence 使用只读 `codex exec`，不需要看板内额外配置，也不会创建 patch handoff。
- Kanban 卡片上的 **Gap** 预览会带入 privacy-safe current goal context，与
  差距分析页选择 Kanban task 时的上下文一致；不会自动写回 goal、kanban 或
  skill-tree。
- **本轮看板优化方向**：`kanban.md` 使用稳定 task id（保留 `id` meta 行；
  无 id 的旧任务会生成兼容 id），并明确拖拽方向：纵向指针位置决定插入
  `to_index`；拖入另一列会映射为 `to_section`，再沿用手动移动的 done flag /
  自动日期规则。页面级拖拽逐步接入期间，显式移动控件仍是可靠 fallback。

### 5.6 团队视图（`pages/4_Team_View.py`）

- 选择 **团队**（`teams/` 下目录名）。
- 编辑团队字段与各 **产品池** tab，保存 `team.yaml` 与
  `product-pool.yaml`。

### 5.7 Profile Health（`pages/5_Profile_Health.py`）

- 只读报告，与 `nblane health <名称>` 同源。
- 检查校验结果、生成块 drift、solid/expert 节点缺证据、Done 任务未结晶。
- 不写入 profile 文件；阶段 / 周复盘候选已拆到独立 **Review** 页面。

### 5.8 Review（`pages/8_Review.py`）

- 从周 / 阶段窗口生成 `evidence`、`next_action`、`public_draft` 候选，以及只读
  `method_note`。
- 生成候选只读；保存所选会写入 `agent-activity.yaml` 的 pending 队列。
- Evidence 候选可直接写入 `evidence-pool.yaml`，并可把来源 Done task 标记为
  `crystallized`；不会自动提升 skill status。
- Next action 候选可追加到 `kanban.md` 的 Queue。
- Public draft 候选只创建 draft blog，不发布。

### 5.9 Agent Activity（`pages/9_Agent_Activity.py`）

- 读取 `agent-activity.yaml`，按 status、kind、candidate type、source page 和 owner
  过滤跨页面候选、patch 和写回结果。
- pending Review 候选可以在 Activity 页应用；其他来源的 patch 第一版只审查并跳转
  owner 页面。
- `dismissed` / `failed` 条目可以 reopen，便于重新审阅。
- Codex 配置不在本页编辑；统一使用侧栏 **AI / LLM -> 配置 Codex**。

### 5.10 Research Workspace（`pages/7_Research.py`）

- **Source Inbox** 继续接收网页、论文、repo、书籍、手动链接和 Home capture；写入
  `research/sources.yaml`，不会直接写 evidence、skill status 或公开输出。
- **Reading Room** 对单个 source 生成翻译、摘要、claim candidates 和 citations；保存后仍停留在 source-scoped annotations。
- **Claims & Citations** 可把 source 切成 `research/chunks/*.jsonl`，创建
  `research/claims.yaml` research claim，并用 `research/citations.yaml` 绑定
  claim 到 source/chunk。Research claim 生成 evidence 时仍是 `needs_review` 候选。
- **Synthesis Drafts** 从 research claims 生成 `research/drafts.yaml` 与
  `research/drafts/*.md`，并可创建带 `related_sources` /
  `related_research_claims` / `related_citations` 的博客草稿。
- **Connectors** 管理 `research/connectors.yaml`，支持 arXiv、Semantic Scholar、
  GitHub 自动导入；X/Twitter 与小红书第一版走手动导入或官方授权边界。配置文件不保存 token、cookie 或 API key。

### 5.11 Output Studio（`pages/6_Output_Studio.py`）

- 为当前档案初始化缺失的公开层文件。
- **Generate** 从 reviewed evidence 或 accepted claims 生成 blog draft、resume bullet preview、project update draft。
- **Profile** 编辑公开姓名、headline、简介、联系方式、头像、原始 YAML，并提供实时整站预览。
- **Blog** 通过 React / BlockNote 编辑器 shell 管理 draft / published 文章，支持 front matter、媒体、AI 候选、发布检查和公开页预览。
- Blog 支持 `related_claims` 与 research provenance refs；发布校验会检查 accepted claim、promoted research claim、source visibility 和 citation/chunk 断链。
- **Resume** 编辑 `resume-source.yaml`，预览 Markdown，并生成定制简历草稿；从 accepted claims 生成的 bullet 候选不会自动写回。
- **Known Info** 将选中的 evidence 整理成 draft 公开项目。

### 5.12 Public Build（`pages/10_Public_Build.py`）

- 只负责静态站校验、预览和构建，不编辑 Blog / Resume / Known Info。
- 默认构建到 `dist/public/<profile>`；可选择是否包含 draft/private 预览内容，并填写生产 `Base URL` 生成 SEO 与子路径部署链接。

### 5.13 Public Site 兼容入口（`pages/6_Public_Site.py`）

- 旧入口保留为跳转页，指向 **Output Studio** 与 **Public Build**，避免旧链接失效。

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

详见 [数据契约](../architecture/data-contracts.md)、
[Evidence 参考](../reference/evidence.md)、[公开站点](public-site.md)。

---

## 7. 相关文档

- [Web 体验设计（Streamlit）](../product/web-experience.md) — 信息架构、品牌、backlog
- [当前状态](../project/status.md) — 已交付页面表
- [架构总览](../architecture/overview.md)
- [公开个人网站、博客与简历](public-site.md) — Public Surface v1
- [MCP 服务器](../reference/mcp.md) — Cursor / 外部 Agent 集成
