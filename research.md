# Research 模块临时开发文档

> 日期：2026-05-23  
> 范围：`8503 /Research` Streamlit 主工作台、`8502` FastAPI sidecar、Paper Library standalone、Reader API、论文搜索与导入闭环。  
> 目标：从交互体验、按钮可用性、功能完整性和端口联动角度，梳理 Research 模块下一轮优化项。

## 0. 修复记录

### 2026-05-23：8503 -> 8502 URL Resolver

- 已在 `pages/7_Research.py` 增加统一 sidecar base resolver：
  - 优先使用 `NBLANE_READER_API_BASE`
  - 其次使用 `NBLANE_PAPER_LIBRARY_BASE`
  - 缺省自动指向 `http://127.0.0.1:8502`
  - 可通过 `0/false/off/none` 显式关闭 sidecar link base
- 已将 Research 页面中的 Paper Library / Reader 链接、iframe、组件 payload 的 `reader_base` 统一改为 resolver 输出。
- 已在 `8503 /Research` 顶部显示 sidecar 状态，例如：`Paper Library sidecar: auto-detected · http://127.0.0.1:8502`。
- 已将 Research 中的 Paper Library / Reader iframe wrapper 切到 `st.iframe` 优先，旧版本 Streamlit fallback 到 `st.components.v1.iframe`。
- 闭环验证：
  - `compileall` 通过。
  - 3 个相关单测通过。
  - Playwright DOM 走查确认 Overview 链接、Reader 链接和 Paper Library iframe 均指向 `http://127.0.0.1:8502`。

### 2026-05-23：Overview 可读性与界面语言修复

- 已将 Overview 的文字、空态、badge、disabled button 和队列 tile 对比度提高，避免截图中整页“发白、像不可用”的问题。
- 已将 `Work queues` 从“摘要 chip + 单独按钮”合并为单一 queue tile：非 0 队列可直接点击进入 Paper Library deep link，0 队列保留清楚的禁用空态。
- 已给 `Needs extraction`、`PDF missing`、`Stale translations`、`Private sources` 等队列补明确动作文案，例如运行解析、补 PDF、刷新翻译、检查可见性。
- `Ready to review` 为空时，已增加“准备断言候选”的下一步入口，引导用户回到 Paper Library / Reader 先做解析和 claim candidate。
- Overview 的标题、队列、动作、badge、风险、connector 状态等新增文案已接入 `src/nblane/web_i18n.py`，随侧边栏 `Interface language` 在中文/英文之间切换。
- 已让 `build_research_overview_payload()` 的 `next_actions` 输出真实 `count`，避免 UI 为本地化动作标题时只能使用被截断的 refs 数量。
- 闭环验证：
  - `python3 -m compileall pages/7_Research.py src/nblane/web_i18n.py src/nblane/core/research_workspace.py` 通过。
  - `uv run pytest tests/test_research_workspace.py -q` 通过，9 个用例全绿。
  - `uv run python` smoke check 确认 Overview 关键文案会按 `ui_lang=en/zh` 返回不同语言。

## 1. 当前端口实测

### 1.1 运行状态

- `8502`：FastAPI sidecar 正在运行，`/paper-library?profile=王军` 返回 `200`，静态资源加载正常。
- `8503`：Streamlit UI 正在运行，`/Research` 可打开。
- 当前 tmux session：
  - `nblane-reader-api`
  - `nblane-streamlit-ui`
  - 另有旧的 `nblane-streamlit-8501`

### 1.2 8502 API 实测结果

| 检查项 | 结果 | 备注 |
|---|---:|---|
| `GET /paper-library?profile=王军` | `200`, `0.006s` | 只验证 HTML shell。 |
| `GET /api/research/王军/paper-library?view=all&sort=recent` | `200`, `4.576s` | curl 端到端耗时；浏览器资源计时约 `1.832s`。 |
| `GET /api/dashboard/payload?profile=王军` | `200`, `4.577s` | payload 约 `164KB`。 |
| Provider 搜索 `vla memory`, `year_from=2025`, `limit=3` | `200`, `21.129s`, `2` 条 | arXiv HTML 部分超时，预算耗尽。 |
| Codex 搜索 `vla memory`, `codex_timeout_seconds=1`, `limit=2` | `200`, `21.132s`, `2` 条 | Codex 1s 超时后 fallback 到 arXiv HTML。 |

Paper Library payload 当前概况：

- `papers`: 5
- `reading`: 3
- `no_pdf`: 2
- `needs_extraction`: 3
- `claims_need_review`: 0
- `diagnostics`: []

搜索 `vla memory` 返回的可下载 PDF 候选示例：

- `ReMem-VLA: Empowering Vision-Language-Action Model with Memory via Dual-Level Recurrent Queries`
  - `https://arxiv.org/pdf/2603.12942`
- `MemoryVLA: Perceptual-Cognitive Memory in Vision-Language-Action Models for Robotic Manipulation`
  - `https://arxiv.org/pdf/2508.19236`

搜索 trace 暴露的问题：

- `arxiv_html MemoryVLA` 成功，但单步耗时约 `3-5s`。
- 后续 query variant 可能等待到 `6s` 超时。
- 当前 provider 搜索是串行感强，用户会感到“卡住”。
- Codex / Model 首选的体验容易被 timeout 混淆：用户以为是模型慢，实际上很多时间花在 fallback provider。

### 1.3 8503 与 8502 联动风险

当前 `8503` Streamlit 进程环境里没有看到 `NBLANE_READER_API_BASE=http://127.0.0.1:8502`。Playwright 看到 `/Research` 中的 iframe 和部分按钮链接解析到：

- `http://127.0.0.1:8503/paper-library?...`
- `/reader/view/...`

这意味着：

- 在 8503 页面点击 Paper Library / Reader 相关按钮时，如果没有显式 base URL，可能落到 8503，而不是 8502。
- `8503/paper-library` 会被 Streamlit 接管，返回 Streamlit HTML shell，不是真正的 8502 Paper Library。
- 用户会看到“按钮能点”，但实际跳错端口，是 Research 体验里最优先的联动问题。

建议 P0 修复：

- `8503` 启动时强制带上 `NBLANE_READER_API_BASE=http://127.0.0.1:8502`。
- 代码层增加兜底：如果 env 缺失，但 `127.0.0.1:8502/paper-library` 可达，则自动使用 8502 作为 sidecar base。
- 在 Research 顶部显示 sidecar 状态：`8502 connected / unavailable / env missing`。
- 所有 Reader / Paper Library link 都应使用同一 URL resolver，避免一部分是相对路径、一部分是绝对路径。

### 1.4 日志风险

`nblane-streamlit-ui` tmux 历史日志出现过：

- `StreamlitDuplicateElementId`
- `st.components.v1.iframe` 将在 `2026-06-01` 后移除的 deprecation warning
- `use_container_width` 在 `2025-12-31` 后移除的 deprecation warning

其中 `StreamlitDuplicateElementId` 会导致页面执行中断，应纳入 P0/P1 排查。当前代码中 Reading Room 的 `create_evidence_candidate` 已带 key，但日志可能来自旧进程或其他重复按钮；需要在重启后复测 Advanced Connectors / Reading Room 全路径。

## 2. 模块结构

### 2.1 8503 Streamlit Research 页面

入口文件：

- `pages/7_Research.py`

主要 tab：

- `Overview`
- `Paper Library`
- `断言与引用 Claims`
- `Synthesis / Export`
- `Advanced Connectors`

页面顶部还有：

- 当前 profile / goal context
- `AI` popover，用于配置 paper search、translation、review、source guide、Q&A、claim extraction、deep read、paper compare 等动作的 backend/model。

### 2.2 8502 FastAPI sidecar

入口文件：

- `src/nblane/web_reader_api/__init__.py`

主要路由：

- `GET /paper-library`
- `GET /dashboard`
- `GET /api/dashboard/payload`
- `GET /api/research/{profile}/paper-library`
- `POST /api/research/{profile}/paper-library/events`
- `POST /api/research/{profile}/paper-library/search`
- `POST /api/research/{profile}/paper-library/import`
- `GET /api/research/{profile}/papers/{source_id}`
- `POST /api/research/{profile}/papers/{source_id}/reader-token`
- `GET /reader/view/{source_id}`
- `GET /reader/api/{source_id}/pdf`
- `GET /reader/api/{source_id}/payload`
- `GET /reader/api/{source_id}/page-preview/{page}`
- `GET /reader/api/{source_id}/page-text-layer/{page}`
- `POST /reader/api/{source_id}/tasks`
- `POST /reader/api/{source_id}/annotation`
- `POST /reader/api/{source_id}/translate`
- `POST /reader/api/{source_id}/explain`
- `POST /reader/api/{source_id}/ask`
- `POST /reader/api/{source_id}/chunk`
- `POST /reader/api/{source_id}/citation`
- `POST /reader/api/{source_id}/progress`
- `POST /reader/api/{source_id}/review`
- `POST /reader/api/{source_id}/analyze`
- `POST /reader/api/{source_id}/action/{action}`

## 3. 交互按钮与功能矩阵

### 3.1 Research Overview

当前功能：

| 区域 | 交互 | 当前体验 | 优化建议 |
|---|---|---|---|
| Work queues | `Reading`, `Needs extraction`, `PDF missing`, `Stale translations`, `Private`, `Recent` 等链接 | 有数量时可点击跳 Paper Library 深链；数量为 0 时禁用。 | 确保链接绝对指向 8502；深链进入后应高亮对应 paper/detail/action。 |
| Next actions | `Open Reader`, `Open in Library`, `Focus ready claims`, `Focus quote warnings`, `Focus export gate`, `Connector inbox` | 能把用户导向 Reader、Paper Library、Claims、Export、Connector。 | 当前多处 action 是“设置 session_state 后 rerun”，反馈偏轻；建议统一 toast/notice，并在目标 tab 自动聚焦。 |
| Recent work | 每篇论文有 `Open Reader`, `Open in Library`, `Claims` | 最近阅读链路清晰。 | `Claims` 为 0 时禁用合理，但可增加“暂无 claims，先 run extraction / extract claims”引导。 |
| Ready to review | `Review claim` | 可聚焦到 Claims review。 | 如果没有 ready claims，当前空态可再给一个“从 Reader / Paper Library 生成 claim candidates”的行动入口。 |
| Risk queue | `Focus export gate` | 有 risk 时进入 export gate。 | 建议风险卡直接给出 blocker 类型、paper、修复入口，减少用户去 Export 后再找。 |

核心问题：

- Overview 是很好的中控，但依赖 Paper Library / Reader 深链。如果 8502 base 缺失，Overview 的大部分 CTA 会跳错端口。
- Overview 里注入了大量 CSS，Playwright 文本抓取会看到 CSS 内容；视觉上未必影响，但可维护性和调试体验差。
- 2026-05-23 截图走查显示 Overview 的信息架构基本成立，但视觉可读性不足：正文、说明、小标签、空态和 disabled button 颜色过浅，用户会误以为整页不可用。
- 上方 summary chip 与下方真正可点击按钮分离，用户不容易判断哪些数字只是状态、哪些入口能带自己进入下一步。
- `Stale translations` 等高数量风险只出现在 safety badge / queue 中，缺少明确的“去修复”主动作，容易被当成普通统计而不是待处理工作。
- 中英文标签混杂，例如 `Research Command Center`, `Claims ready`, `Open Reader`, `Private / public` 与中文说明并存，会增加新用户理解成本。

截图读法与使用路径：

1. 先看 `Research Command Center` 的 6 个漏斗数字：`Sources` 是资料总数，`Reading` 是正在读的论文，`Extracted` 是已有 chunk/annotation 的论文，`Claims ready` 是可进入人工审阅的 research claim，`Citations` 是引用数量与 warning，`Drafts` 是综合/导出草稿。
2. 再看 `Integrity & Publish Safety`：`Private / public` 表示私有/公开来源比例，`Citation broken` 是引用或 chunk/source ref 断裂风险，`Private publish risk` 是私有来源被带入公开输出的风险，`Stale translations` 是需要刷新翻译的段落或页面。
3. 然后看 `Work queues`：这是按工作类型分流的入口。非 0 队列应该能跳到 Paper Library 对应视图，例如 `Reading` 继续读，`Needs extraction` 做解析，`PDF missing` 补 PDF，`Stale translations` 刷新翻译。
4. `Next actions` 是系统认为最该做的一件或几件事。当前截图里的主动作是继续阅读 3 个 source，可直接 `Open Reader` 或 `Open in Library`。
5. `Discovery updates` 显示 arxiv / semantic scholar / github / x_twitter / xiaohongshu 等 connector 的导入状态，主要用于判断自动发现来源是否在工作。
6. `Recent work` 是最近打开或读过的论文；每张卡可以继续 Reader、进 Paper Library 详情，或在有 claim/citation 时进入 Claims。
7. `Ready to review` 是待人工审阅的 research claim。为空表示还没有 claim 进入 ready 队列，应先在 Reader/Paper Library 做 extraction / claim generation。
8. `Risk queue` 是发布前 blocker。为空表示当前没有 private publish / broken citation 这类硬阻塞，但不代表没有普通维护任务，例如 stale translations 仍应从 work queue 处理。

建议新增专项改造：

- Overview visual clarity pass：
  - 提高 `.ro-muted`、`.ro-copy`、`.ro-card-meta`、`.ro-empty`、disabled button 的对比度，至少满足普通正文 4.5:1、小标签 3:1 的可读性目标。
  - 区分“可点击入口”“只读统计”“禁用空态”：非 0 队列用一致的 link/button 样式，0 队列保持低优先级但文字仍清楚。
  - 给 `Stale translations`、`Needs extraction`、`PDF missing` 这类非阻塞维护项补明确 action 文案和 deep link focus，避免只显示数字。
  - 将 Overview 的关键标签中文化，保留必要英文术语但避免同一卡片内中英文混排。
  - 减少 summary chip 与按钮区的信息重复；优先考虑让 `Work queues` 的 chip 本身可点击，或把 chip 与对应按钮合并成一个稳定的 queue tile。
  - 增加桌面 1440px 与移动 390px 的 Playwright 截图验收，确保 Overview 没有发白、重叠、横向溢出或按钮文字截断。

### 3.2 Paper Library：8503 Wrapper

当前功能：

- `Open Paper Library Workspace` link button。
- 可根据 runtime 选择：
  - `fastapi_iframe`
  - `streamlit_component`
  - fallback Streamlit implementation
- 可健康检查 8502 是否可达。

问题：

- 8503 进程当前缺 `NBLANE_READER_API_BASE`，导致 iframe src 可能是 `8503/paper-library`。
- `_paper_library_workspace_status()` 用 GET 健康检查是可以的，但之前 8502 日志里出现过 `HEAD /dashboard` 为 `405`；如果后续统一做健康检查，应避免 HEAD 误判。
- fallback 与 standalone 两套 UI 并存，用户不知道当前用的是哪一个 runtime。

建议：

- 在 Paper Library tab 顶部显示 runtime badge：
  - `8502 workspace`
  - `Streamlit component`
  - `Fallback`
- 如果当前是 fallback，应明确提示哪些功能不可用，例如 standalone 删除预览、右键菜单、拖拽体验。
- 所有环境问题给出可复制的启动命令，或者提供 “Restart sidecar” 运维入口。

### 3.3 Paper Library：8502 Standalone

#### Discovery Panel

实测可见按钮与控件：

- 折叠按钮：`Find and import papers`
- 模式切换：`Codex`, `Model`, `Provider`
- 输入：`Query`, `Providers`（Provider 模式才显示）, `Limit`, `Year from`, `Year to`
- 主按钮：`Search PDFs`
- 状态：`PDF required`
- 结果区：candidate checkbox、`Import selected`
- 导入选项：collection、status、visibility、`Download PDF`
- 链接：`PDF`, `Paper page`, `DOI`
- diagnostics：query variants、trace、warnings

当前体验优点：

- Search mode 已经很清楚。
- 强制 PDF-ready 与用户“只要有 PDF 能下载就行”的目标一致。
- trace 已能展示中间过程，便于解释“慢在哪里”。
- candidate 默认选中 PDF-ready 且未导入项，导入路径短。

问题：

- 搜索仍然是阻塞式：按钮变成 `Searching...`，但用户要等 20s 左右才看到结果。
- `Codex` 与 `Model` 的 policy 文案都显示 `Model-first + arXiv web fallback`，不够准确。
- 没有显式 `use_profile_context` 开关。虽然后端已默认不使用 profile context，但 UI 没告诉用户“这是纯检索”。
- Provider 模式的 providers 是自由文本，容易输入错；Streamlit fallback 是 multiselect，standalone 可以改成 chips/checkbox。
- 搜索结果只保存在当前页面 state，刷新或切换后会丢。
- 没有取消搜索 / 重试单个 provider / 只看已成功来源。

建议：

- 搜索策略改为“两阶段”：
  - 第 1 阶段：provider/arXiv 快速返回 PDF-ready 候选，目标 3-8s 内有结果。
  - 第 2 阶段：Codex/Model 异步补充摘要、相关性解释、explainer links。
- 增加 `Personalize with profile` toggle，默认 off。说明：off = 纯检索；on = 仅用于 rerank/解释，不限制检索。
- trace 做成 timeline：
  - `queued`
  - `searching provider`
  - `found N raw`
  - `kept M PDF-ready`
  - `fallback`
  - `done`
- 当找到足够 `limit` 条 PDF-ready 结果时提前停止后续 provider/query variant。
- 增加短期缓存：query + filters + provider 的结果缓存 5-30 分钟，减少重复 20s 等待。

#### Workspace Header

控件：

- metrics：`Papers`, `Reading`, `PDF missing`, `Needs extraction`, `Claims review`
- library search input
- sort select：`Recently read`, `Recently added`, `Title`, `Status`, `Research claims`
- `Apply`

问题：

- 初始加载时会短暂显示 metrics 为 0 和 `Loading...`，容易让用户以为库空了。
- `Apply` 对用户不自然；输入回车和 sort 已自动应用，按钮价值不明显。

建议：

- 用 skeleton 或 `Loading library...` 替代 0 metrics。
- `Apply` 改为 icon button 或自动 debounce，不占主要视觉。
- 搜索输入加清除按钮。

#### Tree / Collection Pane

控件：

- `Search collections`
- `Expand all`
- `Collapse all`
- section 折叠：Library / Collections / Technical Taxonomy / Work Queue / System
- collection `+`
- row toggle
- row main select
- `...` context menu
- drag/drop collection
- drag/drop papers into collection

实测右键 paper menu：

- `Open Reader`
- `Show details`
- `Move to collection`
- `Add to collection`
- `Remove from current collection`
- `Mark as reading`
- `Archive`
- `Mark as discarded`
- `Run extraction`

问题：

- 图标现在是字母 `V/L/C/T` 和 `...`，可用但不够专业。
- Technical Taxonomy 目前 `Topics/Methods/Datasets/Benchmarks` 为 0 且可点，但实际没有强交互，容易误导。
- 移动/加入 collection 的区别需要更强提示，尤其是 paper 可多归类还是单归类的问题。
- 在移动端，tree、list、detail 顺序堆叠，页面高度接近 4000px，找到 detail 成本高。

建议：

- 用明确图标替换字母：
  - view: list/filter icon
  - collection root: library icon
  - collection: folder icon
  - taxonomy: tag icon
  - trash: trash icon
- Technical Taxonomy 如果未实现，应禁用或隐藏；若要保留，应支持真正的 tag/facet filter。
- 移动端改成 segmented view：
  - `Search`
  - `Collections`
  - `Papers`
  - `Detail`
  - 或 tree/detail drawer。
- 当前选中 paper 后，在移动端应自动 scroll 到 detail 或底部出现 sticky action bar。

#### Paper List

控件：

- `Bulk select` / `Clear`
- paper checkbox
- paper card click
- paper card drag
- paper card right-click menu

优点：

- 桌面三栏布局合理，1440px 下无横向溢出。
- 390px 移动端无横向溢出。

问题：

- card 中 badge 过多时信息噪声较大。
- 论文标题很长时列表高度膨胀明显。
- 多选后的批量动作隐藏在 tree context/drop 里，新用户不容易发现。

建议：

- 批量选择后显示明确 action bar：
  - Move
  - Add to
  - Mark reading
  - Archive
  - Run extraction
- 长标题最多 2-3 行，详情里展示完整标题。

#### Detail Pane

控件：

- `Open Reader`
- `Run extraction`
- `Auto chunk`
- source link
- artifact summary
- `Delete paper...`

优点：

- 详情区有主要动作，逻辑清楚。
- delete 有 preview 和输入 source id 的确认机制，安全性较好。

问题：

- `Run extraction` 和 `Auto chunk` 的区别不够直观。
- 对无 PDF 的 paper，应该更强引导 `Attach PDF` 或 `Search PDF`。
- `Auto chunk` 在无 extraction 时的预期不清楚。

建议：

- 把 detail action 按流程分组：
  - Read: Open Reader
  - Prepare: Run extraction
  - Structure: Auto chunk / Extract claims
  - Review: Claims / Citations
  - Safety: Visibility / Delete
- 每个 action 有状态 badge：ready / needs PDF / running / last run。

### 3.4 Reader

当前入口：

- 8502 `/reader/view/{source_id}`
- 8503 Research Reader tab/fallback
- Paper Library detail 和 Overview 都能打开 Reader。

主要 API：

- PDF payload / text layer / page preview
- annotation create/update/delete
- translate
- explain
- ask
- chunk
- citation
- progress
- review / analyze / deep read

问题：

- Reader 强依赖 8502 base，当前 8503 env 缺失时最容易跳错。
- 8503 的 text-mode Reader 与 8502 PDF Reader 有重叠，用户会困惑哪个是主入口。
- Reader AI result 目前多以 YAML 展示，适合开发者，不适合长期阅读体验。

建议：

- 明确产品原则：有 PDF 时只走 8502 Reader；8503 text-mode Reader 标为 Legacy / fallback。
- Reader actions 返回结果应有结构化 UI：
  - summary card
  - claims candidates
  - citations
  - warnings
  - accept/save buttons
- progress / annotation / translation 任务使用统一任务栏，避免用户不知道后台是否在跑。

### 3.5 Claims & Citations

控件：

- source select
- claim status filter
- queue filter
- bulk select claims
- `Verify selected quotes`
- `Mark selected ready`
- `Promote preview`
- duplicate merge form
- claim patch form
- save claim links
- create citation from chunk
- request citation
- mark ready
- promote
- dismiss
- citation inspector locate source
- manual chunk / claim / citation editors

优点：

- Claim -> Citation -> Evidence 的边界是清楚的。
- Quote warning / missing citation / duplicate claims 有 review board。
- Promote 前能 preview evidence candidate。

问题：

- 页面密度高，开发者友好，普通使用者会觉得“像后台管理系统”。
- 单个 claim card 内表单太多，容易误操作。
- `Promote preview` 在 bulk 区是 popover，但单 claim 区是 expander，交互不统一。
- `Dismiss` 需要 note，这很好，但输入框和按钮紧邻，移动端可能拥挤。

建议：

- Claim Review 做成任务队列：
  - Missing citation
  - Quote warning
  - Ready to promote
  - Duplicates
- 每张 claim card 默认只显示：
  - claim text
  - evidence source
  - citation status
  - primary action
- 编辑、链接、citation request 放进 `Edit` drawer。
- 批量操作增加确认摘要，避免一次性改错多个 claim。

### 3.6 Synthesis / Export

控件：

- Export scope：collection / goals / source statuses / claim statuses / tags / manual sources
- Export citations：citation multiselect、format radio、download、save
- Manifest：sources / claims / citations / YAML
- Blocker actions：review visibility、fix citation、promote claim
- Reading note export：source / claims / chunks / citations select、download、save
- Synthesis draft create
- Output candidates：blog / project update / resume bullet

优点：

- 已经有 export manifest 和 blocker 概念，适合防止 private/broken citation 误发布。
- Reading note export 是有价值的中间产物。

问题：

- Export Scope 很强，但用户不一定理解 scope 与 manifest 的关系。
- `Save export` 与 `Download export` 并列，没解释保存到哪里。
- Blocker 修复入口有的跳 Paper Library，有的只设置 Claims filter 并显示 info，跨 tab 跳转不够一体化。

建议：

- Export 顶部先显示 publish readiness：
  - Safe to publish
  - Needs citation repair
  - Contains private sources
  - Has unpromoted claims
- Scope 的选择即时显示“将导出 N sources / M claims / K citations”。
- Blocker action 都应能一键进入目标 tab 或 8502 deep link。
- 保存后给出文件路径和“Open / copy path”动作。

### 3.7 Advanced Connectors / Source Inbox / Reading Room

控件：

- Source queue：按 status 展开、编辑 source form
- Add source form
- Candidate preview
- Reading Room legacy flow：generate reading draft、save reading annotations、create evidence candidate
- Connector provider cards
- Manual connector import：preview、candidate picker、import selected
- Connector config：provider、id、query、enabled、privacy、options
- Connector run：dry run、run now、import selected
- Import next actions：open in paper library、review imported、open reader、run extraction、dismiss

优点：

- 导入后 next actions 很好，能把用户拉到后续工作流。
- Manual connector import 是自动化不可用时的好兜底。

问题：

- Advanced tab 内容过多，Source Inbox、Legacy Reading Room、Connectors 混在一起。
- Reading Room 与 Paper Library / Reader 功能重叠，应降级为 fallback。
- Connector provider status 很适合提升到 Overview 的 discovery area，不应只藏在 Advanced。
- Manual import preview 与 Paper Search Discovery 功能相似，但 UI 不统一。

建议：

- Advanced 拆成：
  - Source Inbox
  - Connectors
  - Legacy Tools
- Connector import 与 Paper Library import 使用同一种候选卡片设计。
- 导入后 next actions 保持，但应写入统一 notice 区并支持“稍后处理”。

## 4. UI 完整性评估

### 4.1 已经不错的地方

- 8502 standalone Paper Library 是当前体验最完整的 surface：
  - discovery
  - metrics
  - tree
  - paper list
  - detail
  - context menu
  - deletion preview
  - responsive 无横向 overflow
- Overview 已经能把 research 工作流串起来：
  - source
  - reading
  - extraction
  - claims
  - citation
  - export safety
- 搜索 trace 已经能解释中间过程，是之前“Failed to fetch / 为什么慢”的关键补丁。
- Delete paper 的交互安全性比普通 CRUD 好。

### 4.2 主要短板

1. 端口联动脆弱  
   `8503 -> 8502` 的 URL base 不能只依赖 env，当前进程已经出现 env 缺失。

2. 搜索慢且阻塞  
   搜索能搜到，但 20s 级等待会被用户理解为“坏了”。需要渐进式返回、缓存和提前停止。

3. 用户不知道当前 surface  
   同一个 Paper Library 可以是 8502 standalone、8503 iframe、Streamlit component、fallback，界面没有清楚告知。

4. 中文/英文混杂  
   Research 是中文页面，但 standalone Paper Library 大量英文按钮仍未本地化。

5. 移动端可用但不高效  
   没有横向溢出是好事，但 390px 下页面太长，tree/list/detail 串行堆叠，操作成本高。

6. 高级功能太密  
   Claims、Export、Connectors 功能强，但需要任务导向的渐进显示。

7. 过多 YAML / raw metadata 暴露  
   适合调试，不适合日常 research workflow。应将 YAML 放到 details/debug 区。

## 5. 优化优先级

### P0：先让按钮一定跳对、页面不中断

1. 修复 8503 sidecar base
   - `NBLANE_READER_API_BASE` 缺失时自动探测 `http://127.0.0.1:8502`。
   - `_reader_view_url()` 和 `_paper_library_workspace_url()` 必须输出绝对 8502 URL。
   - Research 顶部显示 sidecar 状态。

2. 检查 StreamlitDuplicateElementId
   - 打开 `/Research` 的所有 tab，尤其 Advanced Connectors / Reading Room。
   - 所有循环内 `st.button` / `st.form_submit_button` 都补稳定 key。

3. 搜索交互防卡死
   - 搜索请求加前端 timeout / cancel。
   - trace 在请求运行中也能显示，或至少显示当前阶段。
   - 后端找到足够 PDF-ready 候选后提前返回。

4. 8502 健康检查
   - 增加 `/api/health` 或 `/healthz`。
   - 避免用不支持的 HEAD 造成误判。

### P1：把 Paper Library 变成主入口

1. 让 8503 Paper Library tab 默认迁入/嵌入 8502 standalone，并清楚显示 runtime。
2. Overview visual clarity pass：
   - 提高文本、空态、disabled button、badge 的可读性对比度。
   - 合并或弱化重复的 summary chip / queue button，明确非 0 队列可点击。
   - 为 `Stale translations`、`Needs extraction`、`PDF missing` 增加明确修复动作和 deep link focus。
   - 中文化 Overview 关键标签，并保留 Playwright 桌面/移动截图验收。
3. Discovery Panel 增加：
   - profile context toggle，默认 off
   - cache 命中提示
   - retry failed provider
   - `Fast search` / `Enrich with Codex` 分层按钮
4. 移动端改成 segmented panes 或 drawer。
5. 图标体系替换字母与 `...`，补充 aria label / tooltip。
6. 完整中文 i18n。

### P2：让 Claims / Export 更像工作流，而不是后台表单

1. Claims Review 改为队列式：
   - Missing citation
   - Quote warning
   - Ready to promote
   - Duplicates
2. Claim card 默认折叠编辑项。
3. Export 顶部做 publish readiness gate。
4. Blocker action 统一为可跳转 deep link。

### P3：整理 Legacy 与高级能力

1. Reading Room 标记为 legacy/fallback，减少与 Reader 重叠。
2. Connectors 与 Paper Search 候选卡片统一。
3. Connector provider 状态提升到 Overview。
4. YAML/debug 默认折叠到 developer diagnostics。

## 6. 建议的闭环验收清单

### 6.1 端口与链接

- `curl http://127.0.0.1:8502/paper-library?profile=王军` 返回 200。
- `curl http://127.0.0.1:8502/api/research/王军/paper-library` 返回 `ok: true`。
- `8503 /Research` 中：
  - Paper Library iframe src 必须以 `http://127.0.0.1:8502/paper-library` 开头。
  - Overview 的 `Open Reader` href 必须以 `http://127.0.0.1:8502/reader/view` 开头。
  - Overview 的 `Open in Library` href 必须以 `http://127.0.0.1:8502/paper-library` 开头。

### 6.2 Paper Library

- 1440px 桌面：
  - workbench 三栏可见。
  - 无横向 overflow。
  - paper context menu 可打开。
  - create / rename / move / delete collection 可用。
- 390px 移动：
  - 无横向 overflow。
  - 搜索、tree、list、detail 都可触达。
  - 选中 paper 后有明显下一步入口。

### 6.3 搜索

- `vla memory`, `year_from=2025`, `require_pdf=true` 至少返回 2 条 PDF-ready 候选。
- response 包含：
  - `warnings`
  - `search_trace`
  - `query_variants`
  - `debug.profile_context_used=false`
- UI 显示：
  - query variants
  - 每个 provider/backend 的耗时
  - timeout / fallback 原因
- 若启用 `use_profile_context=true`，UI 必须明确提示“profile 只用于 rerank/解释，不用于限制检索”。

### 6.4 Claims / Export

- Claim status filter 和 queue filter 能改变 review board。
- `Verify selected quotes` 有结果反馈。
- `Mark ready` / `Promote` / `Dismiss` 都有明确 toast，并写入文件。
- Export manifest 能显示 blockers，并给出可跳转修复入口。
- 保存 export 后显示保存路径。

### 6.5 Advanced / Connectors

- 打开 Advanced 不出现 `StreamlitDuplicateElementId`。
- Manual connector preview -> import selected -> next actions 可跑通。
- Import next actions 中：
  - `Open in Paper Library`
  - `Review imported`
  - `Open Reader`
  - `Run extraction`
  - `Dismiss`
  状态与 imported source 类型一致。

## 7. 推荐下一步开发任务

### Task A：修复 8503 -> 8502 URL Resolver

涉及文件：

- `pages/7_Research.py`
- `app.py`
- `src/nblane/web_reader_api/__init__.py`

验收：

- 当前 tmux 即使没有 `NBLANE_READER_API_BASE`，Research 也能检测 8502 并输出正确绝对 URL。
- UI 顶部显示 sidecar status。
- Playwright 验证链接不会落到 8503。

### Task B：搜索体验两阶段化

涉及文件：

- `src/nblane/core/research_papers.py`
- `src/nblane/web_reader_api/__init__.py`
- `src/nblane/paper_library_component/frontend/src/main.jsx`
- `src/nblane/paper_library_component/frontend/src/style.css`

验收：

- 3-8s 内先返回 provider PDF-ready 候选。
- Codex/Model enrichment 可后续补充，不阻塞初始候选。
- UI trace 在运行中可见。

### Task C：Paper Library UI polish

涉及文件：

- `src/nblane/paper_library_component/frontend/src/main.jsx`
- `src/nblane/paper_library_component/frontend/src/style.css`
- `src/nblane/web_i18n.py`

验收：

- 中文化完成。
- 图标替换字母。
- mobile 使用 drawer/segmented panes。
- Technical Taxonomy 要么可用，要么隐藏/禁用。

### Task D：Claims / Export 工作流化

涉及文件：

- `pages/7_Research.py`
- `src/nblane/core/research_workspace.py`

验收：

- Claim review board 按队列呈现。
- Export readiness 一眼可见。
- Blocker 修复能一键跳转目标 surface。

### Task E：Overview 可读性与操作信号改造

涉及文件：

- `pages/7_Research.py`
- `src/nblane/core/research_workspace.py`
- `src/nblane/core/research_papers.py`
- `src/nblane/web_i18n.py`
- `tests/test_research_workspace.py`
- `tests/e2e/paper_library_workspace.spec.ts`

验收：

- 1440px 桌面截图中，Overview 的正文、meta、badge、空态和 disabled button 不再发白，普通正文对比度达到 4.5:1，小标签至少达到 3:1。
- 用户能一眼区分只读统计、可点击队列、禁用空态；非 0 的 `Work queues` 入口都有稳定 deep link。
- `Stale translations`、`Needs extraction`、`PDF missing` 从 Overview 点击后能进入 Paper Library 对应 view/detail/focus/action。
- `Ready to review` 为空时给出面向生成 claim candidates 的行动入口，而不是只有“暂无”。
- Overview 关键标签完成中文化；保留英文术语时有一致译名，例如 `Research claim`、`Evidence claim`。
- Playwright 覆盖 `8503 /Research` Overview 的桌面 1440px 与移动 390px 截图检查，无重叠、无横向溢出、按钮文字不截断。

## 8. 本次走查使用的命令摘要

```bash
curl -sS --max-time 12 \
  'http://127.0.0.1:8502/paper-library?profile=%E7%8E%8B%E5%86%9B'

curl -sS --max-time 15 \
  'http://127.0.0.1:8502/api/research/%E7%8E%8B%E5%86%9B/paper-library?view=all&sort=recent'

curl -sS --max-time 40 \
  -X POST 'http://127.0.0.1:8502/api/research/%E7%8E%8B%E5%86%9B/paper-library/search' \
  -H 'Origin: null' \
  -H 'Content-Type: application/json' \
  --data '{"mode":"provider","query":"vla memory","limit":3,"year_from":"2025","require_pdf":true}'
```

Playwright 走查内容：

- `8502 /paper-library?profile=王军`
  - desktop 1440x1000
  - mobile 390x820
  - Discovery mode 切换
  - paper context menu
  - layout overflow
- `8503 /Research`
  - tabs
  - Overview links
  - iframe src
  - visible buttons
  - current process env / tmux logs
