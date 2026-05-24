# Dashboard 临时开发计划

> 临时工作文档。用于把 Home Dashboard 从“能显示的骨架”推进到“真正可用的成长工作台”。稳定后再合并进 `docs/zh/product/web-experience.md`、`docs/zh/guides/web-ui.md` 和对应架构文档。

> 生成日期：2026-05-22
> 最近更新：2026-05-23
> 对照来源：`app.py`、`src/nblane/core/home_dashboard.py`、`src/nblane/core/workspace_graph.py`、`src/nblane/home_dashboard_component/frontend/src/*`、`docs/zh/product/growth-graph.md`、`docs/zh/guides/web-ui.md`。

## 实施状态（2026-05-22）

本轮已按 P0 路线落地到可自测状态：

- **P0.1 说明入口**：8503 Dashboard 标题行右上角提供 `使用说明`，内容解释首屏、Source / Evidence / Claim / Skill / Output、AI 设置和 8502 Canvas；底部旧 Page Map 已移除。
- **P0.2 Growth Graph contract**：`docs/zh/product/growth-graph.md` 增加 `growth_graph_contract` YAML 区块，`workspace_graph` 从 contract 读取 layer / node / edge 定义，并在 payload 中输出 `graph.contract`。
- **P0.3 Graph 可用性**：Dashboard payload 升级为 `schema_version: "1.1"`，增加 `focus_path`、`attention`、node `summary/description/primary_action/secondary_actions`；React 默认进入 Focus Path，并提供 Attention Queue 和 Inspector 动作。
- **P0.4 Dashboard AI 设置**：新增 `dashboard.goal_skill_match`、`dashboard.graph_insights` action preference，8503 右上角 `AI 设置` 支持 backend / LLM model / Codex model / Test model，并只保存非密钥偏好。
- **P0.5 8502 Canvas**：8502 增加 `/dashboard?profile=<profile>` 和 `/api/dashboard/payload?profile=<profile>`，8503 在配置 `NBLANE_DASHBOARD_CANVAS_BASE` 或 `NBLANE_READER_API_BASE` 后显示 `打开 8502 Canvas`。
- **自测固定化**：新增 `tests/e2e/dashboard_canvas_8502.spec.ts` 与 `tests/e2e/dashboard_8503.spec.ts`，覆盖 8502 非空 Focus Path / Inspector / payload contract，以及 8503 顶部说明、AI 设置、8502 Canvas 入口。

本文件后续章节保留为设计依据和 P1 backlog。P0 后续只允许补测试、修边界和替换 placeholder，不再改变事实源边界。

## P1.0 实施状态（2026-05-22）

本轮已完成 **Dashboard Usability Pass** 的第一段：首屏、Canvas 默认视图、Workbench 和缩放闭环。

- **首屏重排**：8503 React Dashboard 顶部增加 Today Focus Bar，把 Evidence Review、Current Focus、Gap / Next Action、Output / Feedback 作为默认行动信号展示。
- **主路径 Canvas**：`主路径 / Focus Path` 不再默认使用 ReactFlow 缩放全图，而是使用专门的可读主路径节点条；2D Canvas / Attention / 3D Graph 仍保留为探索视图。
- **过滤降级**：Layer filter 收进 `更多过滤`，默认不再抢占阅读心智。
- **Inspector 默认更实用**：默认选中优先 attention 节点，而不是总是落到 North Star；点击主路径节点后右侧直接显示 owner/action。
- **Workbench 重排**：`Current Focus`、`Evidence Review`、`Gap / Next Action`、`Output / Feedback` 上移；`Skill Progress` 下移为长期状态；新增 `Action queue`。
- **Quick Capture**：Capture source 改为紧凑捕捉，标题、类型、Capture 按钮默认可见，URL / note / tags 放入 `更多字段`。
- **缩放修复**：8503 右上角操作在 1024px 宽度下不再逐字断行；8502 Dashboard Canvas 在 390px 移动宽度下改为纵向 Focus Path，无页面级横向溢出。
- **探索图可用化**：8503 `探索图` 不再依赖 3D force graph。已替换为确定性的上下文 lane map：方向、工作 / 来源、证据 / 断言、能力 / 缺口、输出 / 反馈；节点固定铺开，边以 SVG 曲线连接，右侧保留上下文 / 上游 / 下游节点级探索列表。
- **探索图自测增强**：Playwright 不再只断言“存在 canvas”，而是检查探索图节点数、边数、节点铺开宽高、节点列表和无横向溢出，防止再次退化成大色块或中心小线段。
- **截图闭环**：生成并人工检查了 `/tmp/nblane-dashboard-screenshots/dashboard-8503-focus.png`、`dashboard-8503-explore.png`、`dashboard-8503-explore-canvas.png`、`dashboard-8503-explore-1024.png`、`dashboard-8502-mobile.png`。

## P0.6 实施状态（2026-05-23）

本轮把 2026-05-23 端口交互审计里的高风险按钮和默认视图问题先收掉，目标是让 Chrome 里看到的每个可点控件都有可见反馈，且 8502 / 8503 边界不再误导用户。

- **8503 内嵌画布默认 Focus Path**：8503 生成的 iframe URL 增加 `view=focus`；React standalone 也支持 `?view=focus|canvas|attention|3d`。独立 8502 `/dashboard` 仍默认 `3D Graph`，保留大图探索心智。
- **隐藏无反馈 goal 交互**：当 8503 使用 `canvas_embed` 时，Active Goal pill 改为静态上下文展示，`添加目标` 不再显示，避免点击后只更新不可见 React state。
- **8502 只读边界**：8502 standalone / embed 视为只读 canvas；Goal save / edit / archive / set primary / skill match / capture source 等 mutation 控件不再展示。`Open 8503`、owner page navigate、Profile Context 跳转仍保留。
- **折叠控件修复**：`More filters`、`更多字段` 和 inspector advanced details 在 closed 状态下内部 input / button 不再占布局、不可见、不可聚焦。
- **文案统一**：`+ Active Goal` 改成 `Add goal / 添加目标`；`Plane Graph / 平面图` 统一为 `2D Canvas / 2D 画布`；`Embedded 3D graph` 改成 `Embedded canvas / 内嵌画布`。
- **E2E 方向更新**：8503 E2E 先断言嵌入画布默认 Focus Path，再切到 3D Graph 做 canvas pixel / drag / zoom 检查；8502 E2E 增加“只读画布不出现 mutation 按钮”的断言。

已跑验证：

```bash
cd src/nblane/home_dashboard_component/frontend
npm test
npm run build

PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_home_dashboard.py \
  tests/test_workspace_graph.py \
  tests/test_growth_graph_contract.py

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
npx playwright test tests/e2e/dashboard_canvas_8502.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
NBLANE_DASHBOARD_8503_BASE_URL=http://127.0.0.1:8503 \
npx playwright test tests/e2e/dashboard_8503.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line
```

结果：

- Home Dashboard frontend unit：`5 passed`。
- Vite build：通过，已刷新 `static/assets/home-dashboard.css` 与 `static/assets/home-dashboard.js`。
- Python read-model / graph contract：`15 passed`。
- 8502 Dashboard Canvas Chrome E2E：`1 passed`。
- 8503 Streamlit Dashboard Chrome E2E：`1 passed`。

## P0.7 / P0.8 实施状态（2026-05-23）

本轮继续按 “Chrome 可视化与按钮交互计划” 往前推进，完成 sidecar 可达性保护和按钮矩阵可测化。

- **P0.7 Sidecar reachability**：8503 在注入 `canvas_embed` 前会对 `8502 /dashboard?embed=1&view=focus` 做短超时健康检查，并把结果缓存在 `st.session_state` 15 秒。8502 不可达时不再渲染大 iframe，而是使用 React 本地 Context Canvas fallback。
- **顶部入口降级**：`打开 8502 Canvas` 在 sidecar 不可达时变为 disabled，并显示“启动或转发 8502 sidecar”的 help / caption；可达时仍保留 standalone 链接。
- **P0.8 Button instrumentation**：React Dashboard 关键按钮补充 `data-action`、`data-view`、`data-target`、`data-node-id`、`data-goal-id` 等稳定属性，覆盖 navigate、view toggle、filter、select node、goal form、capture、graph fit/focus。
- **P1.2 起步：消费 graph.actions**：Inspector 现在会把 `payload.graph.actions` 合并到当前 node action 列表，并优先展示 graph-level 的具体动作标签，减少只有 `Open` 的泛化按钮。
- **E2E 增强**：8503 E2E 检查内嵌 iframe 的默认 Focus Path、`data-action` view toggle、navigate 按钮矩阵和 goal 无反馈按钮隐藏；8502 E2E 检查只读 canvas 不出现 capture / archive / save mutation 控件，并检查 `select-node` 标记。

新增自测：

```bash
NBLANE_DASHBOARD_CANVAS_BASE=http://127.0.0.1:9 \
PYTHONPATH=src .venv/bin/streamlit run app.py \
  --server.address=127.0.0.1 --server.port=8513 --server.headless=true

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium node <sidecar-fallback-probe>
```

结果：

- `sidecar-fallback-ok`：8502 不可达时，8503 页面显示不可达提示，不出现 `.hd-canvas-embed`，本地 `.hd-canvas-panel` / Focus Path fallback 正常渲染。

## P1.3 实施状态（2026-05-23）

本轮完成 **Workbench 首屏收拢**，把 8503 从“先加载大图”推进到“先处理今日动作，再按需展开画布”。

- **首屏顺序**：8503 非 standalone 路径改成 `Context Header / Today Focus -> Workbench -> Canvas summary`。8502 standalone 仍保持 `Canvas -> Workbench`，不破坏大图探索入口。
- **Workbench 优先级**：Quick Capture 与 Action Queue 上移到 Workbench 第一列；Current Focus / Evidence / Gap / Output 保留在右侧信号区。
- **Canvas summary**：有 8502 sidecar 时，8503 默认显示 Focus Path 摘要、attention / node 计数和 `Open 8502 Canvas`，不再立即加载大 iframe。
- **按需 iframe**：新增 `加载内嵌画布` 折叠开关；展开后才创建 8502 iframe，并继续支持 Focus Path -> 3D Graph 的 Chrome 交互测试。
- **Quick entries 降噪**：Quick entries 收进折叠 details，减少与侧边栏重复抢首屏。
- **Health 上浮规则**：Health 只有 error / warning > 0 时上浮到 Workbench 第一列；否则保留在后续区域。
- **E2E 更新**：8503 Chrome 测试现在断言 Today Focus、Workbench、Canvas summary 的垂直顺序，确认初始无 iframe，再点击 `加载内嵌画布` 进入原 8502 iframe / 3D 检查。

已跑验证：

```bash
cd src/nblane/home_dashboard_component/frontend
npm test
npm run build

PYTHONPATH=src .venv/bin/python -m py_compile app.py

PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_home_dashboard.py \
  tests/test_workspace_graph.py \
  tests/test_growth_graph_contract.py

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
npx playwright test tests/e2e/dashboard_canvas_8502.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
NBLANE_DASHBOARD_8503_BASE_URL=http://127.0.0.1:8503 \
npx playwright test tests/e2e/dashboard_8503.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line
```

结果：

- Home Dashboard frontend unit：`5 passed`。
- Vite build：通过，已刷新 `static/assets/home-dashboard.css` 与 `static/assets/home-dashboard.js`。
- `app.py` py_compile：通过。
- Python read-model / graph contract：`15 passed`。
- 8502 Dashboard Canvas Chrome E2E：`1 passed`。
- 8503 Streamlit Dashboard Chrome E2E：`1 passed`。
- 8502 不可达 fallback probe：`sidecar-fallback-ok`。

## P1.4 实施状态（2026-05-23）

本轮继续完成 **8502 大图探索收口**，让 8502 从“能看 3D 图”推进到“能定位、搜索、分组和从 8503 摘要深链进入”。

- **8502 node deep link**：standalone Dashboard 支持 `?view=3d&node=<node_id>`，初始选中对应节点并让 Inspector 显示该节点。
- **8503 Canvas summary 深链**：Focus Path 摘要节点从静态卡片升级为 `open-8502-node` 链接，自动带 `view=3d&node=`，可直接打开 8502 大图对应节点。
- **Explore list 搜索**：8502 3D Graph 右侧列表新增搜索框，可按 node id、label、type、layer、status、summary 过滤。
- **按 layer 分组**：Explore list 按 Growth Graph layer 分组显示，减少大图节点列表的扫读成本。
- **placeholder 开关**：新增 `Hide placeholders / 隐藏占位节点`，可临时隐藏 planned / scaffold 节点，保留真实节点探索。
- **Action Queue 解释**：Workbench action card 增加“为何推荐”和 filter context，不只显示数字。
- **Source inbox action**：`source:inbox` primary action 改成 `Capture source / Review source`，secondary action 为 `Open Research`，减少只有 `Open` 的泛化按钮。

已跑验证：

```bash
cd src/nblane/home_dashboard_component/frontend
npm test
npm run build

PYTHONPATH=src .venv/bin/python -m py_compile app.py

PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_home_dashboard.py \
  tests/test_workspace_graph.py \
  tests/test_growth_graph_contract.py

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
npx playwright test tests/e2e/dashboard_canvas_8502.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
NBLANE_DASHBOARD_8503_BASE_URL=http://127.0.0.1:8503 \
npx playwright test tests/e2e/dashboard_8503.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line
```

结果：

- Home Dashboard frontend unit：`5 passed`。
- Vite build：通过，已刷新 `static/assets/home-dashboard.css` 与 `static/assets/home-dashboard.js`。
- `app.py` py_compile：通过。
- Python read-model / graph contract：`15 passed`。
- 8502 Dashboard Canvas Chrome E2E：`1 passed`，覆盖 search、layer grouping、hide placeholders、`?node=source:inbox` deep link。
- 8503 Streamlit Dashboard Chrome E2E：`1 passed`，覆盖 Canvas summary node link、lazy iframe、内嵌 8502 Focus / 3D 交互。

## P1.5 UI 调整状态（2026-05-23）

本轮按视觉反馈修正 P1.3 过度收拢的问题：8503 首页重新保留“酷一点的图谱首屏”，但仍不默认加载 8502 iframe。

- **Graph Hero 回到首页**：8503 在 Context Header 后直接显示本地 3D Graph preview，使用当前 Dashboard payload 渲染，不依赖 iframe。
- **首屏顺序调整**：8503 非 standalone 路径改为 `Context Header -> Graph Hero -> Workbench`，让图谱成为第一屏核心信号。
- **Hero 行动区**：Graph Hero 右侧显示 `Start here / 从这里开始` 主动作、四个紧凑信号 chip、当前选中节点和 `Open selected in 8502` deep link。
- **Workbench 降噪**：Action Queue 改成双列紧凑布局，隐藏直接展示的 filter context，减少长卡片把页面拖长。
- **仍保持轻量边界**：初始不创建 `.hd-canvas-embed`；用户点击 `加载内嵌画布` 后才加载 8502 iframe。
- **缩放断点修正**：Chrome 放大或 Streamlit 侧栏存在时，组件 iframe 的有效宽度会明显小于浏览器宽度。Graph Hero 不再在 `1180px` 有效宽度过早折成单列，而是保持双列到约 `640px` 以下；Context Header 改用 `minmax(0, fr)` 网格，避免 720-980px 有效宽度下横向溢出。
- **Sidecar 不可达仍有图**：8503 日常首页总是渲染本地 Graph Hero preview；8502 embed URL 不可用时只隐藏 lazy iframe 入口，不退回旧的大块 Context Canvas。
- **顶部入口与 AI 边界清晰化**：8503 顶部 `使用说明` / `本页 AI 设置` 改为并排紧凑入口；Dashboard AI 文案明确只影响 Dashboard 的 goal-skill match / graph insights，Research 的论文搜索、翻译、Reader、DeepRead 使用 Research AI 配置。
- **Dashboard AI 功能对齐 Research**：`本页 AI 设置` 增加 LLM / Codex runtime 状态、默认 / 建议 / 自定义模型选择，以及逐动作 `Test model`；测试当前行配置，不需要先保存，也不写入文件。
- **Quick actions 重叠修复**：Workbench 在有 urgent health 信号时，Quick actions 与 Health panel 不再共用同一个 grid cell；标题也去掉“快捷操作 / 快捷操作 +”的重复显示。

已跑验证：

```bash
cd src/nblane/home_dashboard_component/frontend
npm test
npm run build

PYTHONPATH=src .venv/bin/python -m py_compile app.py src/nblane/web_i18n.py

PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_home_dashboard.py \
  tests/test_workspace_graph.py \
  tests/test_growth_graph_contract.py

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
NBLANE_DASHBOARD_8503_BASE_URL=http://127.0.0.1:8503 \
npx playwright test tests/e2e/dashboard_8503.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
npx playwright test tests/e2e/dashboard_canvas_8502.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line
```

结果：

- Home Dashboard frontend unit：`5 passed`。
- Vite build：通过，已刷新 `static/assets/home-dashboard.css` 与 `static/assets/home-dashboard.js`。
- `app.py` / `web_i18n.py` py_compile：通过。
- Python read-model / graph contract：`15 passed`。
- 8503 Streamlit Dashboard Chrome E2E：`1 passed`，覆盖首页 Graph Hero canvas 非空像素、首屏顺序、`1280 x 900` / `1024 x 900` 缩放压力、Quick actions / Health 无重叠、lazy iframe、内嵌 8502 3D 交互。
- 8502 Dashboard Canvas Chrome E2E：`1 passed`。

## Chrome 可视化与按钮交互计划

下一轮不再只看“页面能打开”，而是把 Chrome 中真实可见的视觉状态和按钮反馈纳入完成定义。

### A. Chrome 视觉矩阵

每轮 Dashboard UI 改动至少覆盖这些视口：

| 场景 | 视口 | 重点 |
|---|---:|---|
| 8503 daily desktop | `1440 x 1000` | 顶部说明 / AI / 8502 入口、Today Focus、默认 Focus Path、Workbench 顺序 |
| 8503 narrow desktop | `1024 x 900` | 顶部按钮不逐字断行，iframe / Workbench 不横向溢出 |
| 8502 canvas desktop | `1440 x 1000` | 3D canvas 非空、可拖拽/缩放，Inspector 与 node list 可读 |
| 8502 mobile | `390 x 820` | 无页面级横向滚动，Focus Path / 3D fallback 不挤压按钮 |

截图产物建议固定到：

```text
/tmp/nblane-dashboard-screenshots/
  dashboard-8503-focus.png
  dashboard-8503-1024.png
  dashboard-8502-3d.png
  dashboard-8502-mobile.png
```

视觉验收必须同时检查：

- 页面 `scrollWidth <= viewportWidth + 8`。
- 3D canvas pixel stats 非空：alpha、colored、unique color bucket 都超过阈值。
- Focus Path 节点数大于 3，节点文字不互相覆盖。
- `details:not([open])` 内部控件没有 layout rect。
- 关键按钮文字在 390px / 1024px 下不溢出父容器。

### B. 按钮交互契约

每个可见按钮都必须归类，并满足对应反馈：

| 类型 | 示例 | 必须反馈 |
|---|---|---|
| `navigate` | Evidence Review、Gap Analysis、Output Studio、Open 8503 | URL / Streamlit page 变化，或 iframe top-level 跳转 |
| `external_link` | 打开 8502 Canvas | 新窗口 / 新 tab 可打开，并在 8502 不可达时不给空白承诺 |
| `view_toggle` | Focus Path、2D Canvas、Attention、3D Graph | active 状态变化，主视图区内容变化 |
| `filter_toggle` | More filters layer chips | chip active 状态变化，node / edge 数量或空状态变化 |
| `select_node` | Focus Path node、Attention chip、Explore list node | Inspector 文本变化，选中态可见 |
| `form_open` | 添加目标、Goal edit | 表单出现；若当前模式不会渲染表单，按钮必须隐藏 |
| `mutation` | Save goal、Archive、Confirm links、Capture source | 写入成功 / 失败提示和 rerun 后计数变化；8502 只读 canvas 不展示 |

新增或改动按钮前必须回答三个问题：

1. 用户点击后会看到什么变化？
2. 这个变化发生在 8503、8502 iframe、还是新页面？
3. 如果动作会写文件，是否仍走 8503 的 profile / snapshot / review 边界？

### C. Playwright 场景补强

下一轮测试要从“存在性”升级为“交互闭环”：

- **8503**：打开首页 -> 使用说明 -> AI 设置 -> iframe 默认 Focus Path -> 点击 3D Graph -> canvas pixel / drag / zoom -> Workbench action queue navigation。
- **8503 goal 控件**：当 `canvas_embed` 存在时，`添加目标` 不可见，Active Goal 不作为 button；当 fallback 本地 canvas 渲染时，点击 `添加目标` 必须出现 Goal form。
- **8502**：默认 3D Graph -> 切 Focus Path / Attention / 2D Canvas -> 点击 node 更新 Inspector -> 不出现 Save / Archive / Capture 等 mutation 按钮。
- **details**：closed 状态下 `More filters` / `更多字段` 的内部 button / input 数量可以存在于 DOM，但 computed display 必须不可见且没有 layout rect。
- **sidecar 不可达**：只启动 8503 时不出现空白大 iframe，显示明确提示或回退本地 component。

### D. 下一轮实现顺序

1. **P0.7 Sidecar reachability**：`_dashboard_canvas_base()` 不再默认假设 8502 可达；8503 渲染 iframe 前做轻量健康检查，失败则显示 fallback。
2. **P0.8 Button instrumentation**：给关键按钮补稳定 `data-action` / `aria-label`，方便 Playwright 做按钮矩阵扫描。
3. **P1.2 Graph action 统一**：消费 `payload.graph.actions`，把 graph-level action 合并进 Inspector 与 Action Queue。
4. **P1.3 Workbench 首屏收拢**：8503 默认顺序进一步改成 `Today Focus -> Action Queue / Quick Capture -> Canvas summary`。
5. **P1.4 8502 大图体验**：给 Explore list 增加搜索、按 layer 分组、隐藏 placeholder 开关，并支持 `?node=` deep link。

## 2026-05-23 端口交互审计基线（P0.6 修复前）

本节保留 P0.6 修复前的端口交互审计，用于说明本轮为什么优先处理默认视图、只读边界和无反馈按钮。P0.6 的最新落地状态见上方“P0.6 实施状态（2026-05-23）”。结论来自代码阅读、8502 / 8503 实跑、非破坏性 Playwright 控件扫描和现有测试，不包含会写入 profile 的点击动作。

### 0. 审计范围

运行端口：

```text
8502: FastAPI sidecar / Dashboard Canvas / Reader API
8503: Streamlit Web UI / Daily Dashboard
```

本轮检查对象：

- `app.py`：Dashboard payload、AI 设置、顶部按钮、React event handler、8502 canvas embed 配置。
- `src/nblane/core/home_dashboard.py`：Dashboard 聚合 read model。
- `src/nblane/core/workspace_graph.py`：Growth Graph nodes / edges / actions / attention / focus_path。
- `src/nblane/home_dashboard_component/frontend/src/main.jsx`：8502 / 8503 React Dashboard 交互。
- `src/nblane/home_dashboard_component/frontend/src/payload.js`、`events.js`：payload normalize 和前端事件契约。
- `src/nblane/home_dashboard_component/frontend/src/style.css`：布局、details、响应式和溢出控制。
- `src/nblane/web_reader_api/__init__.py`、`templates/dashboard.html`：8502 `/dashboard` 与 `/api/dashboard/payload`。
- `tests/e2e/dashboard_8503.spec.ts`、`tests/e2e/dashboard_canvas_8502.spec.ts`：端口级回归检查。

已跑验证：

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_home_dashboard.py \
  tests/test_workspace_graph.py \
  tests/test_growth_graph_contract.py

cd src/nblane/home_dashboard_component/frontend && npm test

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
npx playwright test tests/e2e/dashboard_canvas_8502.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
NBLANE_DASHBOARD_8503_BASE_URL=http://127.0.0.1:8503 \
npx playwright test tests/e2e/dashboard_8503.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line
```

结果：

- Python read-model / graph contract：`15 passed`。
- Home Dashboard frontend unit：`5 passed`。
- 8502 Dashboard Canvas E2E：`1 passed`。
- 8503 Streamlit Dashboard E2E：`1 passed`。

### 1. 当前端口快照

8502 `template` payload 快照：

```text
schema_version: 1.1
layers: 11
nodes: 19
edges: 33
focus_path: 10
attention:
  evidence_pending: 1
  health_risks: 2
```

8502 `template` 当前可见状态：

- North Star 已设置，Primary Goal 未设置，Active Goals 为 0。
- Graph 默认进入 `3D Graph`，不是 `Focus Path`。
- Inspector 默认选中 `evidence_candidate:pending`，可点击 `Open` 进入 Evidence Review。
- 390px 移动宽度下无页面级横向溢出。

8503 当前可见状态：

- 顶部存在 `使用说明`、`AI 设置`、`打开 8502 Canvas`。
- Streamlit 主体中 React Dashboard 使用 `canvas_embed`，8503 组件本体只显示 Context Header、Today Focus、内嵌 8502 Canvas、Workbench。
- 8503 嵌入的 8502 iframe 内部默认也是 `3D Graph`，并有 view tabs、More filters、Attention chips、Explore list、Inspector。
- 当前真实 profile 数据更丰富，嵌入 canvas 可出现数十个 explore nodes；这不作为稳定基线，稳定基线仍应以 `template` 和测试 fixture 为准。

### 2. 点击与功能交互清单

| 区域 | 控件 | 当前行为 | 完成度 | 优化建议 |
|---|---|---|---|---|
| 8503 顶部 | `使用说明` | Streamlit popover，展示 Dashboard 使用说明和完整文档链接 | 可用 | 补端口/故障说明：8502 未启动时如何降级 |
| 8503 顶部 | `本页 AI 设置` | Streamlit popover + form，可保存 Dashboard action backend/model，并按 action 测试当前行模型 | 可用 | 后续可继续把测试结果持久化到 profile 诊断记录，而不是只保存在本次 session |
| 8503 顶部 | `打开 8502 Canvas` | 跳转到 `8502 /dashboard?profile=...` | 可用 | 需要在 8502 不可达时不显示或显示明确错误 |
| 8503 Context Header | Active Goal pills | 代码会更新 `selectedNodeId` | **有阻塞** | 当 `canvas_embed` 存在时 8503 不渲染本地 Inspector，点击 pill 没有可见反馈；应把选中状态同步给 iframe、打开 8502 对应 node，或在 8503 显示轻量 Inspector |
| 8503 Context Header | `+ Active Goal` | 代码设置 `goalEditor={mode:create}` | **有阻塞** | 当 `canvas_embed` 存在时没有 InspectorPanel，点击后不出现表单；应改为 Streamlit event、弹出 8503 表单，或隐藏该按钮 |
| 8503 Context Header | `编辑 Profile Context` | 发 `set_north_star_display_open_profile_context`，Streamlit 展开 Profile Context | 可用 | 中文文案已经混合：按钮可用，但需要保证不会把用户带到过长页面底部 |
| 8503 Today Focus | Evidence / Current Focus / Gap / Output 四个按钮 | 发 `navigate`，由 Streamlit `st.switch_page()` 处理 | 可用 | 与 Workbench Action Queue 重复；建议 Today Focus 只保留最高优先级主动作，Action Queue 保留完整列表 |
| 8503 Canvas Embed | iframe loading / link | 加载 8502 `/dashboard?embed=1`；另有独立打开链接 | 可用但偏重 | 760px 以上的内嵌画布会把 Workbench 推到后面；8503 日常工作台建议默认显示 Focus summary 或折叠大图 |
| 8503 Workbench | Capture source | 在 8503 Streamlit component 中发 `capture_inbox_submit`，后端写入 Research source inbox | 可用 | `更多字段` 当前 CSS 使 closed details 内容仍参与布局，表单比预期更重 |
| 8503 Workbench | Action Queue | Evidence / Focus / Gap / Output 按钮发 `navigate` | 可用 | 每张 action card 应补“为何推荐”的更短说明和 filter context |
| 8503 Workbench | Quick entries | 7 个 quick link 按钮发 `navigate` | 可用 | 与侧边栏重复；可压缩到 overflow menu 或只保留 Dashboard 主链路 |
| 8502 standalone | `Open 8503` | 普通 anchor 到 Streamlit base | 可用 | 如果由 8502 节点 action 跳 8503，最好转换成 Streamlit pretty route 或带 query intent |
| 8502 Canvas | `Focus Path` | 切到主路径卡片，`template` 有 10 个 focus nodes | 可用 | 代码默认不是此视图；建议 8503 embed / mobile 默认 Focus Path |
| 8502 Canvas | `Plane Graph` / `2D Canvas` | ReactFlow 平面图，`template` 约 30 个 flow nodes / 33 edges | 可用 | 文档、代码 fallback、英文 UI 命名不一致，应统一为 `2D Canvas` 或 `Plane Graph` |
| 8502 Canvas | `Attention` | 展示 attention cards | 可用 | Attention chip 当前显示 node id 较多，可优先显示人类短标签 |
| 8502 Canvas | `3D Graph` | ForceGraph3D 渲染，可拖拽/缩放，Fit/Focus 可用 | 可用 | 不适合作为 8503 日常默认；适合 8502 大图探索 |
| 8502 Canvas | `More filters` | details 控制 layer filter | **有 UI bug** | details closed 时内部 layer buttons 仍有布局/可见性痕迹；需要 CSS 显式隐藏 `details:not([open]) > :not(summary)` |
| 8502 Canvas | Attention chips | 点击后选中节点并刷新 Inspector | 可用 | 应增加当前选中态可见性，并允许从 chip 直接执行主动作 |
| 8502 Canvas | Explore scope `All / Context / Upstream / Downstream` | 过滤右侧 explore list | 可用 | 需要解释 scope 含义，否则新用户不清楚 Upstream / Downstream 是什么 |
| 8502 Canvas | Explore list node buttons | 点击后更新 Inspector 和 3D focus | 可用 | 长列表真实 profile 可达 80+，需要搜索/分组/隐藏 placeholder |
| 8502 Inspector | `Open` | 对 navigate 动作跳 8503 页面 | 可用 | 8502 standalone 内的非 navigate 写入动作会静默 no-op，必须处理 |
| 8502 Inspector | Goal edit / archive / set primary / skill match | standalone / embed 模式会显示，但 `emit()` 只处理 navigate 与 profile context | **有阻塞** | 这些写入按钮在 8502 里目前是静默无效；要么隐藏，要么 POST 受控 event API，要么跳回 8503 对应表单 |
| 8502 Workbench | Capture source | standalone 模式会显示表单并 reset | **有阻塞** | standalone `emit()` 忽略 `capture_inbox_submit`，用户以为已捕捉但不会写入；8502 应只读或实现受控写入 |

### 3. P0 级交互阻塞

1. **8503 有 `canvas_embed` 时，本地 Goal 交互变成无可见反馈。**
   `Dashboard()` 在 `canvasEmbed` 存在时只渲染 `EmbeddedCanvasFrame`，不渲染 `InspectorPanel`。因此 `+ Active Goal`、Active Goal pill 这类本应打开 Inspector 的按钮会更新 React state，但用户看不到任何变化。

2. **8502 standalone / 8503 embedded iframe 暴露写入按钮，但非 navigate event 会被静默忽略。**
   `emit()` 在 `args.standalone` 下只处理 `navigate` 和 `set_north_star_display_open_profile_context`。Goal form save、archive、set primary、goal-skill match、capture source 都不会写入，也没有错误提示。8502 如果定位为只读 canvas，就不应暴露这些写入控件；如果定位为可操作 canvas，就必须增加白名单 event API。

3. **`details` 折叠控件没有真正折叠内容。**
   实测 `.hd-capture-more.open === false`，但 `source/source_url/raw_text/tags` 输入框仍有 layout rect；`.hd-canvas-toolbar` 的 layer buttons 也有类似痕迹。这会让 Quick Capture 和 More filters 比预期更重，也会影响键盘/读屏交互。

4. **默认视图与文档目标不一致。**
   文档 P1.0 写的是“默认 Focus Path”，但当前 `useState("3d")`，8502 standalone 和 8503 embedded iframe 默认都是 3D Graph。3D 已通过渲染测试，但不适合作为日常工作台第一视图。

5. **`graph.actions` 已进入 payload，但前端没有消费。**
   `workspace_graph.py` 输出 `graph.actions`，`payload.js` normalize 后保存，但 `main.jsx` 没有读取 `payload.graph.actions`。实际按钮来自 node `primary_action` 或 Workbench queue，导致 `capture_source`、`review_claims` 等 graph-level actions 没有统一呈现。

6. **placeholder 节点缺少 node-level setup action。**
   `goal:missing`、`project_case:planned`、`composite_evidence:planned`、`claim:planned`、`feedback:planned`、`capacity:planned` 点击后多半只能看到 placeholder 说明，不能直接 setup。Canvas banner 有部分 setup action，但节点自身也应带 primary / secondary action。

7. **8502 可达性被默认假设。**
   `_dashboard_canvas_base()` 在未配置环境变量时仍返回 `http://127.0.0.1:8502`。如果只启动 8503，Dashboard 会生成 iframe URL，但没有 reachability check，也没有退回本地 component / native fallback 的明确策略。

### 4. UI 完整性优化点

首屏层级：

- 8503 当前先显示 Context Header，再显示大尺寸 embedded canvas，Workbench 在后面。对“每天扫一眼做什么”的目标来说，Workbench / Today Focus 应优先于完整 3D 图。
- Today Focus 与 Action Queue 功能重复。建议 Today Focus 只保留 1 个主动作 + 3 个状态摘要，Action Queue 保留完整 action list。
- `+ Active Goal` 在中文 UI 仍是英文，建议改成 `新增目标` 或 `添加目标`。

Canvas 可读性：

- 8502 大图模式可以默认 3D；8503 embed 和 mobile 建议默认 `Focus Path`。
- `Attention` 的按钮应显示 label + reason，node id 放到次要信息。
- Explore list 真实 profile 可达 80+，需要搜索、按 layer 分组、隐藏 placeholder / private item 的快速开关。
- Focus Path 多行换行时，节点 `::after` 连接线可能跨行显得不自然；需要按行隐藏尾部连接线或改为 SVG path。

表单体验：

- Quick Capture 的 `更多字段` 必须真正折叠，否则“轻量捕捉”会变回重表单。
- 8502 只读模式下不要显示 Capture / Goal Save / Archive / Skill Match 这类写入按钮。
- 8503 的 capture 成功后应在页面上明确反馈，并使 Source attention / source count 能在 rerun 后立即更新。

文案与一致性：

- `Plane Graph`、`2D Canvas`、`平面图` 三套命名需要统一。
- `Dashboard Canvas`、`Context Canvas`、`Embedded 3D graph` 的边界需要更清晰：8503 是日常工作台，8502 是大图探索。
- `Open` 作为 Inspector 主按钮太泛；应按节点类型显示 `打开证据审阅`、`打开研究工作台`、`查看技能地图`、`打开输出工作台`。

可访问性：

- details closed 但内部控件仍可见/可聚焦的问题需要修掉。
- canvas 节点按钮应补稳定 `aria-label`，尤其是 icon / color / placeholder 不应成为唯一信息。
- 3D canvas 的 Fit / Focus 应补 tooltip 或更明确按钮文案。

### 5. 下一轮建议优先级

#### P0.6 交互阻塞修复（已落地，后续只补回归）

文件：

```text
src/nblane/home_dashboard_component/frontend/src/main.jsx
src/nblane/home_dashboard_component/frontend/src/style.css
src/nblane/web_i18n.py
app.py
tests/e2e/dashboard_8503.spec.ts
tests/e2e/dashboard_canvas_8502.spec.ts
```

已落地：

- 当 `canvas_embed` 存在时，`添加目标` 隐藏，Active Goal pills 改为静态上下文展示。
- 8502 standalone / embed 下隐藏写入按钮；只保留 navigate / Profile Context 跳转。
- 修复 `details:not([open])` 内容仍显示、占布局、可聚焦的问题。
- 8503 embedded canvas 默认切到 `Focus Path`，8502 standalone 继续默认 `3D Graph`。
- E2E 已更新：8503 先验 Focus Path 再切 3D；8502 断言只读 canvas 不出现 Goal mutation 按钮。

后续回归：

- 补 fallback 本地 canvas 场景：点击 `添加目标` 后必须出现表单。
- 扩展只读断言到 capture / archive / skill-match 全部 mutation 控件。

#### P0.7 Canvas event 边界（只读路线已落地）

文件：

```text
src/nblane/web_reader_api/__init__.py
src/nblane/home_dashboard_component/frontend/src/main.jsx
app.py
tests/e2e/dashboard_canvas_8502.spec.ts
```

已落地：

- 当前路线明确为 **8502 只读 canvas**。
- standalone / embed 隐藏 mutation controls，只保留 navigate / Profile Context 跳转。
- 8503 注入 iframe 前做 sidecar reachability check，不可达时回退本地 component。

后续如果要改成可写 canvas，再新增 `POST /api/dashboard/event`，只接收白名单 action，复用 core 写入函数，并保留 auth / snapshot / conflict guard。

#### P1.2 Graph action 统一（Inspector 消费已起步）

文件：

```text
src/nblane/core/workspace_graph.py
src/nblane/home_dashboard_component/frontend/src/main.jsx
src/nblane/home_dashboard_component/frontend/src/payload.js
tests/test_workspace_graph.py
src/nblane/home_dashboard_component/frontend/src/payload.test.mjs
```

已落地：

- 前端消费 `payload.graph.actions`，并按 `node_id` 合并到 Inspector action row。
- graph-level action 优先于默认 owner `Open`，让 Evidence / Claim / Output 等节点更容易显示具体动作。

待补：

- `source:inbox` primary action 改为 `Capture / Review source`，secondary action 为 `Open Research`。
- placeholder 节点都要有 setup action 或隐藏在默认主路径之外。

#### P1.3 Workbench 信息架构（已落地）

文件：

```text
src/nblane/home_dashboard_component/frontend/src/main.jsx
src/nblane/home_dashboard_component/frontend/src/style.css
src/nblane/core/home_dashboard.py
```

已落地：

- 8503 首屏顺序改为 `Today Focus -> Workbench -> Canvas summary / Open 8502`。
- Embedded canvas 默认只显示 Focus Path 摘要，点击 `加载内嵌画布` 后才加载 iframe。
- Quick entries 收进折叠 details，减少与侧边栏重复。
- Health 只有 error / warning 时上浮，否则留在后续区域。

P1.4 已继续收口：

- Action Queue 已增加更短的“为何推荐”文案和 filter context。
- Canvas summary 的 Focus Path 摘要节点已变成 `open-8502-node` 链接，打开 8502 时携带 `?view=3d&node=`。

### 6. 更新后的验收清单

- 8503 中每个可见按钮点击后必须满足：有页面跳转、有表单出现、有选中态变化、有提示反馈，四者至少一个成立。
- 8502 standalone 中不得出现静默无效的写入按钮。
- `details` 折叠态下内部 input / button 不可见、不可聚焦、不占布局。
- 8503 embed 不可用时不会出现空白大 iframe；要么隐藏入口，要么显示 sidecar 未启动提示，要么回退本地 component。
- `Focus Path`、`Attention`、`3D Graph`、`Plane/2D Graph` 四个视图至少各有一条 E2E 断言。
- `graph.actions` 要么被前端使用，要么从 payload 移除，不能保持“看似有契约、实际没人消费”的状态。
- 中英文 UI 文案一致：`+ Active Goal`、`Plane Graph`、`Open` 这类关键按钮需要按语言和对象类型明确化。

## 下一轮页面规划（基于当前 8503 实际截图）

当前页面已经跑通，但从截图看，下一步不应优先继续加 graph 节点，而应先把页面从“功能拼装完成”收拢成“每天能扫一眼就知道该做什么”的工作台。

### A. 当前截图暴露的问题

1. **首屏的视觉重心分散**
   顶部有 North Star、Primary Goal、Active Goals，右侧又有三个长按钮；信息都在，但没有一个明确的“今天先做这个”的主入口。

2. **Context Canvas 仍然像调试面板**
   图谱可见，但节点很小、画布大片留白、右侧 Inspector 占了很大空间却只显示单个节点说明。用户会知道“图存在”，但仍不容易从图上得到下一步行动。

3. **Layer filter 抢了默认心智**
   Direction / Objective / Work Context / Activity 等层标签适合高级探索，不适合每日默认视图。默认界面应该先强调 Source / Evidence / Claim / Skill / Output 的主链路。

4. **Workbench 信息顺序不符合日常行动**
   `Lit skills` 占据很大面积，但它是长期状态，不是今天最紧急动作。`Current Focus`、`Evidence Review`、`Gap / Next Action`、`Output / Feedback` 更应该上移。

5. **Capture source 表单太重**
   Capture 很重要，但默认整张大表单占右侧首屏，会把注意力从“今日待处理队列”吸走。更好的形态是默认轻量捕捉，展开后再显示完整字段。

6. **Quick actions 太像页面链接列表**
   现在是按钮网格，可以用，但缺少“为什么点它”的上下文。下一轮应把它改成 action queue：Review evidence、Open current doing、Resolve gap、Draft output。

7. **8502 与 8503 分工还不够明显**
   8503 应是每日操作台，8502 应是大画布探索。截图里 8503 仍试图承载完整 canvas，导致主工作区略拥挤。

### B. 下一步优先级

下一轮建议命名为 **P1.0 Dashboard Usability Pass**，目标是“同样的数据，更可读、更可点、更像工作台”。

#### P1.0.1 首屏重排：Today Focus Bar

把顶部区域收敛成两层：

```text
Header:
  Home · nblane / profile / guide / AI / 8502 Canvas

Today Focus Bar:
  Primary goal
  Current doing
  Evidence pending
  Gap next action
  Output opportunity
```

具体调整：

- 右上角三个按钮改成紧凑操作组，避免每个按钮占满整行。
- North Star 只作为方向状态，不再和今日动作抢视觉中心。
- Primary Goal 保留，但旁边直接显示“下一步”：Doing / Evidence / Gap / Output 中最高优先级的一项。
- Active Goals 改为横向小 pills 或二级详情，不占主流程。

验收：

- 1440px 宽屏下，不滚动就能看见当前目标、待处理 evidence、gap、output、capture 入口。
- 顶部不再出现三条等宽长按钮。

#### P1.0.2 Context Canvas 默认改为主路径摘要

8503 默认不再把完整 2D graph 当成首要画面，而是展示一个可读的主路径：

```text
North Star -> Goal -> Doing/Project -> Source Inbox -> Evidence Review -> Claim -> Skill/Gap -> Output
```

具体调整：

- 默认视图仍叫 `主路径`，但节点要放大，减少画布留白。
- Layer filter 收进 `更多过滤`，默认只显示 Source / Evidence / Claim / Skill / Output 的解释型 legend。
- Inspector 默认显示“今日建议动作”，而不是只等用户点节点。
- 点击 Source / Evidence / Claim / Skill / Output 后，Inspector 第一屏必须出现一个主按钮。
- 完整 2D/3D 探索继续保留，但弱化为高级视图；大图探索优先引导到 8502。

验收：

- 截图里主路径节点可读，不需要放大才能看清。
- Inspector 空态不再浪费大面积空间。
- 每个主链路节点都能解释“它是什么、现在有多少、下一步点哪里”。

#### P1.0.3 Workbench 改为 Action Queue

Workbench 的顺序建议改为：

```text
左侧 / 中间:
  1. Current Focus
  2. Evidence Review
  3. Gap / Next Action
  4. Output / Feedback

右侧:
  Quick Capture
  Action Queue

下方:
  Skill Progress
  Health
```

具体调整：

- `Lit skills` 降到第二屏或压缩成横条指标，因为它是长期健康，不是每日入口。
- `Capture source` 默认改成单行 quick capture：标题 + 类型 + Capture；展开后再显示 URL、备注、tags、goal。
- Quick actions 改成带计数和原因的 queue，例如：
  - `Review 19 evidence items`
  - `Open 3 current focus tasks`
  - `Resolve 8 gap risks`
  - `Draft from 1 output opportunity`
- Health 保留在底部，除非 error > 0 才上浮。

验收：

- 用户进入页面后，第一眼能看到“今天处理 evidence / gap / output 哪个更急”。
- Capture 不再压过待处理队列。
- Skill progress 仍可见，但不再支配首屏。

#### P1.0.4 8502 Canvas 做成真正的大图模式

8502 `/dashboard` 下一步应承担“大画布探索”，8503 只放入口和摘要。

具体调整：

- 8502 Canvas 增加：
  - 左侧 layer / view control。
  - 中间大 Focus Path / graph。
  - 右侧 Inspector。
  - 顶部 profile 和返回 8503。
- 8503 的 `打开 8502 Canvas` 明确标注为“展开大图”。
- 8502 支持 query：
  - `?profile=...&view=focus`
  - `?profile=...&node=evidence_candidate:pending`
  - `?profile=...&queue=attention`

验收：

- 8502 适合 1440px 以上的大屏探索。
- 8503 即使不嵌大图，也能完成日常动作闭环。

#### P1.0.5 真实节点替换 placeholder

等页面结构收拢后，再补数据真实性：

- `claim:planned` 替换为 accepted / draft / unsupported / needs_refresh 计数。
- `output` 显示可生成草稿、已发布、blocker。
- `agent_run` 显示 pending writeback、failed、recent applied。
- `feedback` 读取 usage / feedback source，没有事实源时弱化，不占默认主路径。

验收：

- 默认主路径里 planned 节点不超过 1 个。
- Claim / Output / Agent 至少有一个真实计数或明确 owner action。

### C. 推荐执行顺序

1. **先做 P1.0.1 + P1.0.3：首屏和 Workbench 重排。**
   这是最影响实际使用感的部分，改动集中在 React component 和 CSS，不需要先改事实源。

2. **再做 P1.0.2：Canvas 默认主路径摘要。**
   解决截图里“图存在但读不动”的核心问题。

3. **随后做 P1.0.4：8502 大图模式。**
   把复杂探索从 8503 挪出去，避免 Streamlit 首页继续变重。

4. **最后做 P1.0.5：替换 placeholder。**
   数据真实性要跟页面动作一起补，不要为了补节点把页面再变乱。

### D. 本轮不建议做

- 不建议继续增加新的 Dashboard 顶部按钮。
- 不建议把 3D Graph 放到默认视图。
- 不建议把完整 Evidence Review 或 Skill Tree 搬进 Dashboard。
- 不建议让 AI 自动改 evidence、claim、skill status。
- 不建议优先做美化型重皮肤；先做信息层级和动作闭环。

## 0. 当前判断

Dashboard 已有基础：

- 8503 Streamlit 首页入口：`app.py::_render_home_page()`。
- React Home Dashboard 组件：`src/nblane/home_dashboard_component/frontend/src/main.jsx`。
- 2D canvas：`@xyflow/react`。
- 3D graph：`react-force-graph-3d`。
- Dashboard read model：`src/nblane/core/home_dashboard.py`。
- Growth graph payload：`src/nblane/core/workspace_graph.py`。
- Graph schema：`schemas/workspace_graph.py`。
- Research 已有较完整的 per-action AI backend / model 设置，可作为 Dashboard AI 设置的参照。

但当前还没有达到“真正可用”：

- 右下或页面底部的 `Page map (detail)` 像导航说明残留，不像产品化的使用说明；用户希望它成为右上角详细使用说明入口。
- Dashboard AI 只显示 configured / label，不像 Research 一样提供每个动作的 backend、模型、测试和保存。
- Growth graph 图谱虽然有节点和边，但仍有大量 planned / placeholder，且部分节点点击后不能完成真实动作。
- 2D graph 在当前布局下容易不可用：节点过宽、画布高度固定、层级跨度大、截图中局部关系线拥挤，用户无法稳定完成“看图 -> 点节点 -> 执行动作”的闭环。
- `growth-graph.md` 是元素定义源，但代码里的 layer / node type / edge type 是手写常量，缺少自动同步或漂移检测。
- 8502 目前主要服务 Research Reader / Paper Library。若 Dashboard 继续在 8503 内嵌复杂 canvas，会受 Streamlit rerun、iframe 高度和组件消息限制；需要预留 8502 自定义 canvas 路线。
- 8502 / 8503 的联调闭环没有被固定成验收脚本和 Playwright 场景。

一句话目标：

```text
Dashboard 应该让用户在一个首屏里知道：
当前目标是什么，今天该做什么，哪些 Source / Evidence / Claim / Skill / Output 需要处理，
并且可以直接进入对应动作，而不是只看到一张漂亮但不可操作的图。
```

## 1. 产品目标

### 1.1 Dashboard 的职责

Dashboard 不再是 `SKILL.md` 编辑器，也不是全页面导航列表。它是 Growth Graph 的日常投影：

```text
North Star
  -> Goals
  -> Projects / Tasks / Daily Work / Research / Agent Runs
  -> Sources and Observations
  -> Evidence Candidates
  -> Evidence Pool
  -> Claims
  -> Skill Tree / Gap / Next Action
  -> Output
  -> Feedback and Usage
  -> stronger Evidence
```

Dashboard 首屏必须回答四个问题：

1. **我现在在推进什么？** North Star、Primary Goal、Active Goals、Current Focus。
2. **今天最该处理什么？** Doing task、Source inbox、Evidence review、Gap next action、Agent activity。
3. **成长链路哪里断了？** Source 未审阅、Evidence 未链接、Claim 缺支撑、Skill status 风险、Output 有 blocker。
4. **点哪里能继续？** 每个重要节点都必须有 owner page、直接动作或明确的 setup action。

### 1.2 不做什么

- 不把 Dashboard 做成第二个完整 Research Workspace。
- 不把 Dashboard 做成完整 Skill Tree 编辑器。
- 不把图谱节点做成静态装饰。
- 不让 AI 静默提升 evidence、claim、skill status。
- 不把 8502 Dashboard canvas 变成新的事实源；它只能消费 core payload、发事件回 8503 或调用受控 API。

## 2. Growth Graph 元素同步目标

`docs/zh/product/growth-graph.md` 当前定义的层级、对象和边界必须成为 Dashboard 的元素契约。

### 2.1 当前必须覆盖的层级

Dashboard graph payload 必须稳定支持这些 layer：

```text
direction
objective
work_context
activity
source
evidence
claim
capability
output
feedback
governance
```

### 2.2 当前必须覆盖的 node type

```text
north_star
goal
project_case
task
daily_work
research
agent_run
source
evidence_candidate
atomic_evidence
composite_evidence
claim
skill
gap
next_action
output
feedback
capacity
health
```

### 2.3 当前必须覆盖的 edge type

```text
alignment
contains
generated_by
source_to_candidate
review
derives
supports
drives
produces
feedback
watches
```

### 2.4 自动同步方案

短期不要继续维护三份手写定义：

- `docs/zh/product/growth-graph.md`
- `src/nblane/core/workspace_graph.py`
- `schemas/workspace_graph.py`
- `src/nblane/home_dashboard_component/frontend/src/payload.js`

建议新增结构化契约：

```text
src/nblane/core/growth_graph_contract.py
docs/zh/product/growth-graph.md 中增加一个可解析 YAML block
tests/test_growth_graph_contract.py
```

推荐实现方式：

1. 在 `growth-graph.md` 增加机器可读区块，人工仍主要编辑文档：

   ````markdown
   ```yaml growth_graph_contract
   schema_version: "1.0"
   layers:
     - id: direction
       label_zh: 方向
     - id: objective
       label_zh: 目标
   node_types:
     - id: north_star
       layer: direction
     - id: goal
       layer: objective
   edge_types:
     - id: alignment
       from_layers: [direction]
       to_layers: [objective]
   ```
   ````

2. `growth_graph_contract.py` 解析该 block；如果 block 缺失，则使用当前 hard-coded fallback，但测试给 warning。
3. `workspace_graph_layers()`、`workspace_graph_node_types()`、`workspace_graph_edge_types()` 改为读取 contract。
4. `schemas/workspace_graph.py` 保持 Pydantic shape，但 Literal 类型不再作为唯一校验源；运行时用 contract validator 校验。
5. 前端 `GRAPH_LAYER_ORDER` 和 `GRAPH_TYPE_LAYER` 从 payload 的 `contract` 字段读取；缺失时再 fallback。
6. 增加漂移测试：

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest tests/test_growth_graph_contract.py tests/test_workspace_graph.py tests/test_home_dashboard.py
   ```

验收标准：

- 修改 `growth-graph.md` 的 contract block 后，Dashboard payload 和前端图层顺序无需手工同步。
- 如果 doc contract、Python payload、schema 或前端 fallback 不一致，测试失败并指出差异。
- Dashboard graph 节点里每个 `type` 都能反查到 layer、中文说明和 owner path 策略。

## 3. 右上角使用说明入口

### 3.1 现状问题

`Page map (detail)` 现在在 Dashboard 下方折叠展示，内容像旧导航说明：

```text
Page navigation (left sidebar):
- Skill Tree
- Gap Analysis
- Kanban
- Team View
```

这不符合 Dashboard 的首屏职责，也不能帮助用户理解图谱节点如何使用。

### 3.2 改造目标

把 `Page map (detail)` 改为右上角 **使用说明** 入口：

- 位置：Dashboard 标题行右侧。
- 形态：`st.popover()` 优先；低版本 Streamlit fallback 为 `st.expander()`。
- 文案：不是页面清单，而是 Dashboard 的操作手册。
- 内容来源：新增 `docs/zh/guides/dashboard.md` 或复用本临时文档稳定后的摘录。

### 3.3 使用说明内容结构

右上角 popover 应包含：

```text
Dashboard 使用说明

1. 首屏怎么读
   - North Star / Goal / Workbench / Canvas / Inspector 的含义

2. 图谱元素怎么读
   - Source 是材料
   - Evidence 是可审查事实
   - Claim 是解释和断言
   - Skill 是能力状态
   - Output 是表达和投影

3. 常见动作
   - Capture source
   - Review evidence candidate
   - Link goal to skills
   - Open Gap next action
   - Generate output candidate

4. AI 设置
   - Dashboard AI 不自动写事实源
   - per-action 模型只保存非密钥偏好

5. 8502 Canvas
   - 什么时候打开独立 canvas
   - 8502 / 8503 分别负责什么
```

### 3.4 文件级任务

- `app.py`
  - 新增 `_render_dashboard_help(profile: str) -> None`。
  - 在 `_render_home_page()` 的 title/caption 区域右侧渲染使用说明按钮。
  - 删除或降级底部 `home_nav_expander`，只保留“更多页面说明”链接。
- `src/nblane/web_i18n.py`
  - 新增 `dashboard_help_*` 文案。
- `docs/zh/guides/dashboard.md`
  - 正式使用说明文档。
- `docs/zh/guides/web-ui.md`
  - 首页章节链接到 `dashboard.md`。

验收：

- 进入 8503 首页，不滚动即可看到右上角使用说明。
- 说明文档能解释 screenshot 中的 canvas、inspector、AI 设置和 review 流程。
- 页面底部不再出现占首屏注意力的旧式 Page map。

## 4. Dashboard AI 设置

### 4.1 现状

Dashboard payload 只有：

```python
ai_payload = {
    "configured": llm_client.is_configured(),
    "label": llm_client.model_label() if llm_client.is_configured() else "",
}
```

Goal-skill AI match 走 `_run_goal_skill_ai_match()`，但用户不能像 Research 一样在 Dashboard 里选择 backend、模型、测试可用性。

### 4.2 目标

Dashboard AI 设置应复用 Research 的 per-action matrix，而不是新增一套偏好格式。

新增 action names：

```text
dashboard.goal_skill_match
dashboard.capture_to_source_summary
dashboard.source_to_evidence_candidates
dashboard.graph_insights
dashboard.output_opportunity
```

短期 P0 只落地：

```text
dashboard.goal_skill_match
dashboard.graph_insights
```

### 4.3 Web preferences 扩展

修改：

```text
src/nblane/core/web_preferences.py
```

把 `AI_ACTION_DEFAULT_BACKENDS` 扩展为：

```python
"dashboard.goal_skill_match": "llm",
"dashboard.graph_insights": "llm",
```

如果后续 canvas 需要 Codex 解释复杂 graph，也允许用户改成 `codex`。

### 4.4 UI 入口

Dashboard 顶部右侧增加 **AI 设置**：

- 形态：`st.popover("AI 设置")`。
- 内容：借鉴 `pages/7_Research.py::_render_ai_config_panel()`，但只显示 Dashboard 相关 actions。
- 字段：
  - Backend：默认 / LLM / Codex。
  - LLM model：默认 / 推荐项 / custom。
  - Codex model：默认 / 推荐项 / custom。
  - Test model：运行最小可用性测试。
  - Effective backend/model caption。
- 存储：`profiles/<profile>/web-preferences.yaml`。
- 不保存 API key、token、cookie、authorization。

### 4.5 后端接入

改造：

```text
src/nblane/core/goal_alignment.py
src/nblane/core/ai/gateway.py
app.py::_run_goal_skill_ai_match()
```

目标：

- `_run_goal_skill_ai_match()` 不直接调用固定 LLM 模型。
- 改为从 `web_preferences` 读取 `dashboard.goal_skill_match` 的 backend/model。
- LLM 路径传入 `model` override。
- Codex 路径用当前 profile 专属 Codex config，只读执行，不写文件。
- AI 候选仍只存 session state，用户确认后才写入 `goals.yaml`。

验收：

- Dashboard AI 设置能保存到 `web-preferences.yaml`。
- 保存后再次打开 Dashboard 能看到有效 backend/model。
- Test model 成功/失败都能显示人类可读结果。
- Goal-skill AI match 使用 Dashboard 里选择的模型。
- 未配置 API key 时，UI 显示统一未配置提示，不崩溃。

## 5. Graph 真正可用

### 5.1 当前不可用点

用户截图里 graph 的问题主要不是“有没有点和线”，而是：

- 关系线太密，横向跨度大，读不出主路径。
- 有些 planned 节点占据视觉中心，但不能执行真实动作。
- Source -> Evidence -> Claim -> Skill / Output 的核心链路没有突出。
- 2D / 3D 切换不解决“该点哪里”的问题。
- Inspector 对真实节点的动作不足；placeholder 说明有，但不够把用户带到 setup。

### 5.2 P0 图谱原则

Graph 必须按 `growth-graph.md` 的五层抽象解释：

```text
Source 是材料
Evidence 是可审查事实
Claim 是解释和断言
Skill 是能力状态
Output 是表达和投影
```

Graph 首屏只展示主干链路和当前 attention：

```text
North Star -> Goal -> Work -> Source -> Evidence -> Claim -> Skill / Output
```

其余节点默认折叠到 lane summary，用户点击后展开。

### 5.3 Read model 改造

修改：

```text
src/nblane/core/workspace_graph.py
src/nblane/core/home_dashboard.py
tests/test_workspace_graph.py
tests/test_home_dashboard.py
```

新增 payload 字段：

```yaml
graph:
  schema_version: "1.1"
  contract:
    layers: [...]
    node_types: [...]
    edge_types: [...]
  focus_path:
    - north_star
    - goal:<primary>
    - project:<active>
    - source:inbox
    - evidence_candidate:pending
    - atomic_evidence:pool
    - claim:accepted
    - skill:<attention>
    - output:opportunity
  attention:
    counts:
      sources_active: 3
      evidence_pending: 2
      claims_ready: 1
      skill_risks: 4
      output_opportunities: 1
    nodes:
      - id: evidence_candidate:pending
        reason: Done tasks need crystallization
        severity: warning
  actions:
    - id: review_evidence
      node_id: evidence_candidate:pending
      label: Review evidence
      event:
        action: navigate
        payload:
          path: pages/2_Evidence_Review.py
```

节点新增建议字段：

```yaml
summary: ""
description: ""
primary_action: {}
secondary_actions: []
doc_anchor: ""
```

验收：

- 每个非 placeholder 节点至少有一个 owner path 或 action。
- 每个 placeholder 节点必须有 setup action 或明确说明为什么尚未实现。
- Graph payload 里不能泄露 private North Star、private goal、private project title。
- 图谱主路径在空 profile、半配置 profile、真实 profile 下都能稳定渲染。

### 5.4 前端交互改造

修改：

```text
src/nblane/home_dashboard_component/frontend/src/main.jsx
src/nblane/home_dashboard_component/frontend/src/payload.js
src/nblane/home_dashboard_component/frontend/src/payload.test.mjs
src/nblane/home_dashboard_component/frontend/src/style.css
```

P0 交互：

- 默认视图：`Focus Path`，不是全量 graph。
- 提供切换：
  - Focus Path
  - All Layers
  - Attention Queue
  - 3D Explore
- 节点点击后 Inspector 显示：
  - 对象解释。
  - 当前计数 / 状态。
  - 主要动作按钮。
  - 次要动作按钮。
  - owner file / page。
  - related edges。
- Layer filter 保留，但不作为主要操作。
- 空状态必须给明确动作：
  - 没 North Star：编辑 Profile Context。
  - 没 Goal：创建 Goal。
  - 没 Source：Capture source。
  - 没 Evidence：去 Evidence Review。

P1 交互：

- 支持 “pin focus node”。
- 支持 “show upstream / downstream”。
- 支持 “hide planned placeholders” 默认开启。
- 支持 mini legend 解释 Source / Evidence / Claim / Skill / Output。

验收：

- 2D graph 不再需要横向滚动才能完成主路径阅读。
- 点击 `Source inbox` 可打开 Research 或 capture。
- 点击 `Evidence candidates` 可打开 Evidence Review。
- 点击 `Atomic evidence` 可打开 Evidence Review。
- 点击 `Claim` 可打开 Claim Studio 范围。
- 点击 `Skill` 可打开 Skill Tree 或 Gap。
- 点击 `Output` 可打开 Output Studio。
- Playwright 截图中 graph 非空，节点不互相遮挡，按钮文字不溢出。

## 6. 8502 自定义 Canvas

### 6.1 为什么需要 8502

8503 Streamlit 适合表单、导航和安全写入；复杂 graph canvas 更适合 8502 sidecar：

- 不受 Streamlit rerun 影响。
- 可以做更稳定的 React app routing。
- 可以给 Playwright 单独测 canvas。
- 可以和 Paper Library / Reader 共用 sidecar 静态服务能力。

### 6.2 路线选择

短期建议双路径：

```text
8503 Home Dashboard
  - 保留首屏 summary、help、AI 设置、轻量 capture、native fallback
  - 内嵌或链接 8502 canvas

8502 /dashboard
  - 自定义 Growth Graph Canvas
  - 消费同一个 dashboard payload
  - 不直接写事实源，写操作通过 8503 event 或受控 API
```

### 6.3 FastAPI 路由建议

新增或扩展：

```text
src/nblane/web_reader_api/__init__.py
src/nblane/dashboard_canvas_component/frontend/*
```

API：

```text
GET /dashboard?profile=<profile>
GET /api/dashboard/payload?profile=<profile>
POST /api/dashboard/event
```

P0 可先只做：

- `GET /dashboard?profile=...` 静态 React app。
- `GET /api/dashboard/payload?profile=...` 返回 `dashboard_payload(profile)` 的只读 JSON。
- 8503 中提供 `Open 8502 Canvas` 按钮。

P1 再做事件回传：

- `POST /api/dashboard/event` 只允许白名单动作：
  - navigate hint
  - capture source candidate
  - save UI preference
  - mark local canvas preference
- 涉及写入 `goals.yaml`、`research/sources.yaml`、`evidence-pool.yaml` 的动作仍优先回到 8503 或使用既有 core 写入函数加文件 snapshot / git backup。

### 6.4 8503 嵌入策略

环境变量：

```text
NBLANE_DASHBOARD_CANVAS_RUNTIME=streamlit_component | fastapi_link | fastapi_iframe
NBLANE_DASHBOARD_CANVAS_BASE=http://127.0.0.1:8502
```

默认：

- 本地开发：`fastapi_link`，稳定优先。
- iframe 调试：`fastapi_iframe`。
- sidecar 不可用：fallback 到当前 Streamlit component。

验收：

- 只启动 8503 时，Dashboard 不白屏，有 Streamlit component 或 native fallback。
- 同时启动 8502 / 8503 时，Dashboard 显示 8502 Canvas 入口。
- `fastapi_iframe` 下 graph 可见、可点击、非空。
- 8502 不可达时，8503 明确提示并保留可用 fallback。

## 7. Dashboard 工作台补全

### 7.1 Capture

现有 `Capture source` 已写入 `research/sources.yaml`。P0 需要补齐：

- capture 成功后 graph attention 立即体现 Source inbox +1。
- capture 表单里 goal 默认绑定 primary goal。
- 支持选择 project case。
- source 类型和 origin 写入保持 privacy-safe。
- 不直接生成 evidence。

### 7.2 Evidence

Dashboard 只做入口和状态，不做完整 Evidence Review：

- 展示 Done not crystallized、unlinked atomic rows、needs review、status risks。
- `Review evidence` 打开 `pages/2_Evidence_Review.py`。
- P1 支持带 filter 的 session state，例如 `queue=done_uncrystallized`。

### 7.3 Claims

当前 `claim:planned` 需要变为真实节点：

- 读取 `claims.yaml` accepted / draft / needs_refresh / unsupported counts。
- 从 Evidence Review read model 复用 claim index。
- `Claim` 节点 owner path 指向 Evidence Review。
- 点击后打开 Claim Studio。
- 不新增顶层 Claims 页面。

### 7.4 Skill / Gap

当前 graph 已支持 skill links。补齐：

- Skill 节点优先显示与 primary goal 相关的 target skills、risk nodes。
- Gap 节点显示与 current goal / Doing task 相关的 next action count。
- 点击 Skill 打开 Skill Tree。
- 点击 Gap 打开 Gap Analysis，并尽可能带入 current goal context。

### 7.5 Output / Feedback

当前 output 较弱。补齐：

- Output 节点读取 Output Studio / public summary：
  - draft blog count
  - accepted claim 可生成 output count
  - public blocker count
- Feedback 节点读取 usage / feedback source count；没有事实源时保持 planned，但不要占主视觉中心。
- 点击 Output 打开 Output Studio。

### 7.6 Agent Activity

Dashboard 首屏应显示 Agent activity attention：

- pending writeback count
- failed run count
- applied recent count
- owner path `pages/9_Agent_Activity.py`

点击进入 Agent Activity。

## 8. 文件级实施顺序

### P0.1 说明入口和旧 Page Map 降级

文件：

```text
app.py
src/nblane/web_i18n.py
docs/zh/guides/dashboard.md
docs/zh/guides/web-ui.md
```

任务：

- 标题行右侧增加 `使用说明`。
- 说明文档覆盖 Dashboard 操作手册。
- 底部 `home_nav_expander` 改为更轻的“更多页面说明”链接。

测试：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_home_dashboard.py
```

### P0.2 Growth Graph contract 同步

文件：

```text
docs/zh/product/growth-graph.md
src/nblane/core/growth_graph_contract.py
src/nblane/core/workspace_graph.py
schemas/workspace_graph.py
tests/test_growth_graph_contract.py
tests/test_workspace_graph.py
tests/test_home_dashboard.py
```

任务：

- 增加可解析 contract block。
- workspace graph 从 contract 读取 layer / node / edge 定义。
- payload 输出 `graph.contract`。
- 测试防漂移。

测试：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_growth_graph_contract.py tests/test_workspace_graph.py tests/test_home_dashboard.py
```

### P0.3 Graph 可用性修复

文件：

```text
src/nblane/core/workspace_graph.py
src/nblane/core/home_dashboard.py
src/nblane/home_dashboard_component/frontend/src/main.jsx
src/nblane/home_dashboard_component/frontend/src/payload.js
src/nblane/home_dashboard_component/frontend/src/payload.test.mjs
src/nblane/home_dashboard_component/frontend/src/style.css
```

任务：

- 增加 focus path、attention、node actions。
- 默认隐藏 planned placeholders。
- Inspector 增加真实动作。
- 修复 2D canvas 布局，默认主路径可读。
- 3D graph 留作 explore，不作为默认可用路径。

测试：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_home_dashboard.py tests/test_workspace_graph.py
cd src/nblane/home_dashboard_component/frontend && npm test && npm run build
```

### P0.4 Dashboard AI 设置

文件：

```text
src/nblane/core/web_preferences.py
src/nblane/core/goal_alignment.py
src/nblane/core/ai/gateway.py
app.py
tests/test_web_preferences.py
tests/test_home_dashboard.py
```

任务：

- 增加 Dashboard AI actions。
- 首页右上角增加 AI 设置 popover。
- Goal-skill AI match 使用 action preference。
- 增加 model test。

测试：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_web_preferences.py tests/test_home_dashboard.py tests/test_goal_alignment.py
```

### P0.5 8502 Canvas 只读主路径

文件：

```text
src/nblane/web_reader_api/__init__.py
src/nblane/dashboard_canvas_component/frontend/*
app.py
tests/test_home_dashboard.py
tests/e2e/dashboard_canvas.spec.ts
```

任务：

- 8502 新增 `/dashboard?profile=<profile>`。
- 8502 新增 `/api/dashboard/payload?profile=<profile>`。
- 8503 增加打开 8502 canvas 的入口。
- 8502 不可达时 8503 显示 fallback。

测试：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_home_dashboard.py
cd src/nblane/dashboard_canvas_component/frontend && npm test && npm run build
```

### P1.1 Claims / Output / Agent 真实节点

文件：

```text
src/nblane/core/home_dashboard.py
src/nblane/core/workspace_graph.py
src/nblane/core/evidence_review.py
src/nblane/core/agent_activity.py
tests/test_home_dashboard.py
tests/test_workspace_graph.py
```

任务：

- `claim:planned` 替换为真实 claim summary。
- `output` 节点加入 output opportunity / blockers。
- `agent_run` 和 `health` 节点加入 pending / failed attention。

## 9. 8502 / 8503 自测闭环

### 9.1 启动命令

从仓库根目录启动：

```bash
tmux kill-session -t nblane-reader-api 2>/dev/null || true
tmux kill-session -t nblane-streamlit-ui 2>/dev/null || true

tmux new-session -d -s nblane-reader-api -c "$PWD" \
  'PYTHONPATH=src .venv/bin/uvicorn nblane.web_reader_api:app \
    --host 127.0.0.1 --port 8502 --reload --reload-dir src'

tmux new-session -d -s nblane-streamlit-ui -c "$PWD" \
  'NBLANE_READER_API_BASE=http://127.0.0.1:8502 \
   NBLANE_DASHBOARD_CANVAS_BASE=http://127.0.0.1:8502 \
   PYTHONPATH=src .venv/bin/streamlit run app.py \
    --server.address=127.0.0.1 --server.port=8503 --server.headless=true'
```

### 9.2 基础健康检查

```bash
curl -fsS http://127.0.0.1:8502/paper-library?profile=template >/dev/null
curl -fsS http://127.0.0.1:8502/dashboard?profile=template >/dev/null
curl -fsS 'http://127.0.0.1:8502/api/dashboard/payload?profile=template' | head
curl -fsS http://127.0.0.1:8503 >/dev/null
```

如果 `/dashboard` 尚未落地，P0.5 前允许该检查标记为 expected fail，但最终验收必须通过。

### 9.3 Playwright 验收场景

新增：

```text
tests/e2e/dashboard_8503.spec.ts
tests/e2e/dashboard_canvas_8502.spec.ts
```

8503 场景：

- 打开 `http://127.0.0.1:8503`。
- 选择 profile。
- 首屏出现 Dashboard title、使用说明、AI 设置。
- Graph fallback 或 component 非空。
- 点击 `使用说明`，看到 Source / Evidence / Claim / Skill / Output 解释。
- 打开 AI 设置，能看到 Dashboard action rows。
- 点击 Capture source，写入后 Source inbox count 更新。
- 点击 Evidence candidates，能导航到 Evidence Review。

8502 场景：

- 打开 `http://127.0.0.1:8502/dashboard?profile=<profile>`。
- `/api/dashboard/payload` 返回 nodes / edges / contract。
- Canvas 非空。
- 默认 Focus Path 可见。
- 点击 Source / Evidence / Skill / Output 节点，Inspector 更新。
- 截图检查节点文字不重叠，canvas 不是空白。

建议命令：

```bash
npx playwright test tests/e2e/dashboard_8503.spec.ts tests/e2e/dashboard_canvas_8502.spec.ts
```

### 9.4 Python / frontend 单元测试闭环

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_home_dashboard.py \
  tests/test_workspace_graph.py \
  tests/test_web_preferences.py \
  tests/test_growth_graph_contract.py

cd src/nblane/home_dashboard_component/frontend
npm test
npm run build
```

### 9.5 手工验收清单

- 8503 首页不白屏。
- 8503 首屏不用滚动即可看到：
  - 当前 profile。
  - North Star / Goal。
  - Workbench signals。
  - Graph / Canvas 或明确 fallback。
  - 使用说明入口。
  - AI 设置入口。
- 8502 sidecar 启动后，Dashboard canvas 可以独立打开。
- 8502 不启动时，8503 不崩溃，不出现误导性的空 iframe。
- Graph 点击每个真实节点都有下一步动作。
- Planned 节点不会压过真实 attention。
- Private goal / private North Star / private project title 不进入 payload 或截图。
- AI 设置保存后只写非密钥偏好。
- Capture source 不直接生成 evidence 或修改 skill status。

## 10. 风险与约束

### 10.1 隐私

Dashboard payload 是最容易被截图、投屏和复制的对象。必须继续遵守：

- private North Star 不进入 payload。
- private goal 不进入 editor fields。
- private project title 不进入 graph label。
- raw source body 不进入 Dashboard summary。
- API key、token、cookie、authorization 不进入 `web-preferences.yaml`。

### 10.2 事实源边界

Dashboard 只聚合，不取代 owner：

| 对象 | Owner |
|------|-------|
| North Star / Profile Context | `SKILL.md` |
| Goal | `goals.yaml` |
| Project Case | `project-board.yaml` |
| Task | `kanban.md` |
| Source | `research/sources.yaml` |
| Evidence | `evidence-pool.yaml` |
| Claim | `claims.yaml` |
| Skill | `skill-tree.yaml` |
| Output | `blog/`、`outputs.yaml`、`projects.yaml` |
| Governance | health / agent derived reports |

### 10.3 AI 写入边界

AI 在 Dashboard 里只能做：

- 候选 skill link。
- graph insight summary。
- source summary draft。
- output opportunity suggestion。

AI 不允许直接：

- 把 source 提升为 evidence。
- 把 claim 标为 accepted。
- 修改 skill status。
- 发布 output。
- 应用 Agent patch。

### 10.4 8502 / 8503 边界

- 8503 是安全写入、profile 选择、全局导航和 fallback。
- 8502 是高交互 canvas、Reader、Paper Library。
- 8502 不应绕过已有 file snapshot / git backup / review 机制。
- 8502 写操作必须白名单化，并优先复用 core service。

## 11. 最小完成定义

P0 完成后，Dashboard 才能称为“真正可用”：

1. 右上角有可用的详细使用说明。
2. AI 设置可选择 backend/model、测试并保存，至少覆盖 goal-skill match。
3. Graph 默认展示可读的 Focus Path，而不是不可操作的全量毛线团。
4. Graph 的 layer / node / edge 定义与 `growth-graph.md` 自动同步或有漂移测试保护。
5. `claim`、`source`、`evidence`、`skill`、`output` 至少都有真实 owner action。
6. 8503 单独启动可用；8502 + 8503 同时启动时 canvas 闭环可用。
7. Playwright 能验证 8502 / 8503 非空、可点击、可导航。
8. 所有写入仍保留人工确认和事实源边界。

## 12. 建议下一步顺序

1. **先做右上角使用说明和 Page Map 降级**：立刻改善首屏心智，不触碰复杂数据。
2. **补 Growth Graph contract 漂移测试**：先把元素定义同步问题固定住。
3. **修 graph 默认视图**：Focus Path + Attention Queue，让图先能读、能点、能导航。
4. **补 Dashboard AI 设置**：复用 Research per-action model picker，避免 Dashboard AI 继续落后。
5. **补 8502 只读 Dashboard canvas**：先跑通 payload 和可视化，写操作后置。
6. **补 Claims / Output / Agent 真实节点**：把 planned 节点逐步替换为真实工作队列。
7. **做 8502 / 8503 Playwright 闭环**：把“不白屏、非空、可点、可导航”变成回归测试。
