# Dashboard 优化计划

## 背景

本项目的 Dashboard 已经从普通首页逐步演进成 Growth Graph 的日常入口。当前它同时承担两件事：

- 在主应用里帮助用户快速判断今天该做什么。
- 在独立图谱页里展示个人成长、目标、任务、证据和技能之间的关系。

这两个目标容易互相拉扯。主页面需要克制、可操作、快速决策；独立图谱页可以更沉浸、更视觉化、更适合探索。因此后续优化应明确分层：主页面保持实用，全屏 `/dashboard` 做成更完整、更酷、更清晰的成长星系。

当前生产环境需要按实际端口理解：

- `8501`：Streamlit 主应用。
- `8502`：FastAPI sidecar。
- Caddy 已将 `/dashboard`、`/dashboard/*`、`/api/dashboard/*` 反代到 `8502`。
- `8503` 主要是普通本机开发端口，不应作为生产默认入口写进用户可见路径。
- 同机隔离开发通常使用 `18503` 和 `18502`。

## 产品目标

本轮及后续 Dashboard 优化的目标是形成“主页面实用、独立页惊艳”的双层体验。

主页面目标：

- 保持现有“图谱 + 行动面板”布局。
- 帮助用户快速看清当前目标、行动队列、证据队列、gap 和输出机会。
- 不把主页面改成纯视觉展示页。
- 提供清晰入口打开全屏成长星系。

独立 `/dashboard` 目标：

- 成为生产可见的全屏成长星系入口。
- 默认进入沉浸式 3D 图谱。
- 只读探索，不承担写入。
- 视觉方向为“深空但清晰”：酷、有层次、有生命感，但不牺牲可读性。

核心图谱链路：

```text
North Star
  -> Goal
  -> Project / Work / Research
  -> Task / Source
  -> Evidence
  -> Claim
  -> Skill / Gap / Output
  -> Feedback
```

## 入口与部署（已实现）

### 生产入口

主应用 3D hero（`GraphHeroPanel`）右上角已恢复轻量 overlay 入口：

- 中文文案：`打开全屏星系`（i18n key `dashboard_open_fullscreen_galaxy`）
- 英文文案：`Open Fullscreen Galaxy`
- `Open 8502 Canvas` / `打开 8502 画布` 文案与 key 已删除。
- `target="_blank"` 新标签打开，`data-action="open-fullscreen-galaxy"`，携带当前选中节点（`view=3d&node=<id>`）。

URL：

```text
/dashboard?profile=<profile>
```

`app.py::dashboard_payload()` 通过 `_dashboard_canvas_base()` 推导 sidecar base（`NBLANE_DASHBOARD_CANVAS_BASE` → `NBLANE_READER_API_BASE` → 默认 `http://127.0.0.1:8502`），写入 `payload.canvas_embed.standalone_url`；前端 `dashboardCanvasEmbed()` 据此渲染入口，sidecar 不可达时自动隐藏（不再链接到一个不可达地址）。

不引入 iframe embed；主页面只保留跳转到全屏页的入口。

### 返回主应用（已实现）

`/dashboard` 页面里的“返回主应用”（`data-action="open-main-app"`，i18n key `dashboard_open_main_app`）：

- `NBLANE_STREAMLIT_BASE_URL` 显式配置时使用该值。
- 未配置时默认同源 `/`（`main.jsx` 与 `web_reader_api/__init__.py` 均已移除 `127.0.0.1:8503` 硬编码兜底）。
- 生产环境同源部署下天然不落到 8503；`8503` 只是本机开发端口，`scripts/dev-web.sh` 会显式注入该变量。

### Auth（已有基础 + 已补测试）

`8501` 打开 `8502 /dashboard` 时沿用既有 sidecar auth handoff / cookie 机制（`web_auth.py` 登录后 POST `/auth/session`，`_auth_user_from_request` 校验 cookie / handoff token）。这条链路本身早已存在；本轮新增的是**验证**：

- `tests/test_web_reader_api.py::test_dashboard_payload_requires_auth_cookie_when_auth_configured` — 未配置 cookie/handoff 时 `/dashboard` 与 `/api/dashboard/payload` 均返回 401。
- `tests/test_web_reader_api.py::test_dashboard_payload_auth_handoff_sets_cookie_and_checks_profile_access` — handoff 后 200 且写入 cookie；跨 profile 请求返回 403。

验收点（已通过 pytest 覆盖）：

- 主应用已登录时，打开 `/dashboard` 不应 401。
- profile access 仍受权限控制。
- 未授权 profile 不能通过 `/api/dashboard/payload` 读取。

## 主页面优化边界

主页面不做结构性重排。

保留：

- 现有 Graph Hero + 行动面板结构。
- Workbench 的日常行动入口。
- Evidence Review、Current Focus、Gap、Output、Health 等日常信号。

只做轻量增强：

- 恢复“打开全屏星系”入口。
- 修正文案和 i18n。
- 共享 3D 视觉修正，例如光照、材质、图例、微光提示。
- 保证中等宽度下无横向溢出。

主页面应继续突出 active goals。归档、暂停、完成目标可以在图谱中存在，但不要抢主页面日常行动心智。

## 全屏 `/dashboard` 设计

### 默认视图（已实现）

`/dashboard?profile=<profile>` standalone 非 embed 模式默认进入 `3d` 视图（`initialDashboardViewMode`，早已存在）。

支持深链：

```text
/dashboard?profile=<profile>&view=3d
/dashboard?profile=<profile>&view=3d&node=<node_id>
```

带 `node` 时：

- 初始选中该节点（已有）。
- 镜头/Inspector 聚焦到对应节点（已有）。
- 右侧抽屉展示节点详情（本轮新增，见下）。

深链写回（本轮新增）：`handleSelectNode` 在 standalone 下用 `history.replaceState`（非 `pushState`）把当前选中节点写回 `?node=`，回总览时移除该参数——地址栏始终可复制分享当前视图，且浏览器 Back 键仍能干净退回主应用而不是逐节点回退。

### 布局（本轮实现：全屏 + 按需抽屉）

`Dashboard()` 新增了独立的 standalone 渲染分支（`args.standalone && !args.embed`），不再复用原有两栏 `hd-canvas-workbench`：

```text
┌──────────────────────────────────────────────┐
│ hd-standalone-top: profile / 返回主应用       │
├──────────────────────────────────────────────┤
│ [view switcher overlay]                      │
│                                              │
│              full-bleed 3D galaxy            │
│                                              │
│                            [archived toggle] │
└──────────────────────────────────────────────┘
        node 选中时 → 右侧 HdDrawer 滑出 InspectorPanel
```

已落地：

- `ContextCanvas` 新增 `fullBleed` prop：无 header/toolbar/AttentionSummary chrome，3D stage 占满 `100vh`（`.hd-canvas-panel-fullbleed`）。
- 视图切换器（Focus/2D/Attention/3D）在 `fullBleed` 下渡化为左上角贴边 overlay（`.hd-segmented-overlay`），仍可点击、仍响应 `?view=` 深链。
- `InspectorPanel` 从常驻列改为 `HdDrawer`（复用既有 `drawer.jsx`，resume/profile 已在用的同一套滑出面板）；`open={Boolean(selectedNodeId)}`，点空白 / 关闭按钮回到 `selectedNodeId=""`。
- 修复了一个隐藏坑：原有 `preferredNode` 自动选中 effect 会在任何页面加载时自动选一个节点并触发抽屉——已改为 standalone 下跳过自动选中（除非带 `?node=` 深链），保证默认状态星系不被面板挡住。
- 搜索、图例仍是原有的贴边 overlay，不受本次改动影响。

### 只读边界

`/dashboard` 是只读探索页。

允许：

- 浏览图谱。
- 搜索节点。
- 点击节点。
- 聚焦 goal。
- 查看 Inspector。
- 打开主应用相关页面。

不允许：

- Capture source。
- Save goal。
- Archive goal。
- Set primary goal。
- Confirm skill links。
- 修改 skill status。
- 静默把 source 提升为 evidence。
- 静默生成 claim 或 output。

如果动作需要写入，应跳回 `8501` 主应用，由 Streamlit 负责 profile 选择、安全写入、反馈和 rerun 后状态确认。

## 成长星系视觉语义

采用“成长星系”隐喻，不改成普通关系网络。

推荐语义：

- North Star：中心引力源。
- Goal：主要天体。
- Project：围绕 goal 的较大轨道体。
- Task / Output：围绕 project 的较小轨道体。
- Evidence：总览态为微光提示，聚焦态为绕 task 的彗星。
- Claim：证据与能力之间的解释性星座。
- Skill：外围星群或星座。
- Gap / Health：弱化但可被 Inspector 解释的治理信号。

### 历史目标（视觉已有基础，默认态本轮修正）

归档、暂停、完成目标不应从成长星系中消失。它们代表成长历史。

视觉表现（已有实现，`galaxy_scene.js::_addOrb`）：

- `active`：正常发光，使用目标主色。
- `completed`：冷白、稳定、低动效，表示已完成成果。
- `archived` / `paused`：灰白、熄灭、低亮度、低透明度，且冻结轨道运动。

默认可见性（本轮修正）：`ContextCanvas` 新增 `defaultShowArchived` prop——仅 standalone 全屏页把 `showArchived` 默认值设为 `true`（历史目标默认弱化可见）；embed 与 goal rail 保持原有默认 `false` 不变。用户在任一入口手动切换过 toggle 后，`localStorage`（`nblane.context.goalRail.showArchived`）里的选择会覆盖这个默认值。主页面 Graph Hero（日常首页）本身不受影响：它一直不过滤归档目标，只是靠 `nodeVisualWeight` 弱化显示，从未走这条 toggle 逻辑。

### Evidence

采用“总览微光 + 聚焦彗星”方案。

总览态：

- 不全局显示所有高速 evidence 彗星。
- 对已经产生 evidence 的 task / project 添加静态微光、halo 或轻微脉冲。
- 让用户能一眼看出哪些工作已有成果支撑。

聚焦 goal 后：

- task-generated evidence 绕 task 运动。
- 使用小而亮的 evidence moon / comet。
- 彗尾表示该 task 已产出证据。
- project-only evidence 可放在 project 外层 evidence orbit，避免和 task 混在一起。

## 交互设计

### 搜索（已有实现）

搜索作为轻量 overlay（`.hd-graph3d-search`，右上角），而不是大筛选面板。

支持匹配 node label / id（`Graph3DView` 内 `searchMatches`）。

搜索结果点击后：

- 选中节点。
- 打开 Inspector / 右侧抽屉（standalone 下即本轮新增的 `HdDrawer`）。
- `scene.focus(node)` 聚焦。

### 图例（默认折叠已满足，无需改动）

核查结论：`Graph3DLegend` 的「编码说明」子面板（`hd-graph3d-encoding`）持久化状态 `getItem(...) === "0"` 在首次访问（无 localStorage 记录）时求值为 `false` → 默认折叠。代码已经满足这条要求，本轮未做改动。

展开后（已有实现）：

- 可滚动（`.hd-graph3d-legend` 有 `overflow-y: auto`）。
- 滚轮事件不能被 OrbitControls 吃掉（`onWheel={(e) => e.stopPropagation()}`）。
- 不应遮挡主视觉（左下角贴边，`max-height: calc(100% - 24px)`）。
- 文案已走 i18n（zh/en `home.yaml` 均已覆盖全部 `dashboard_graph_legend_*` key）。

图例应解释：

- size
- brightness
- progress arc
- grey / frozen
- comet trail
- placeholder / octahedron

### Inspector（本轮实现：右侧按需抽屉）

全屏页 Inspector 是右侧按需抽屉：`InspectorPanel` 复用既有 `HdDrawer`（`drawer.jsx`），选中节点时打开，点击空白 / 关闭按钮回到总览态。`.hd-drawer-body .hd-inspector` 去掉了重复的卡片背景/边框/阴影（drawer 面板本身已有）。

Inspector 内容优先级维持既有实现（节点标题/类型/状态 → 摘要 → 关系 → 只读 metadata → 可跳转动作），未做结构调整。

`/dashboard` Inspector 中不提供直接写入按钮——`readOnlyCanvas = Boolean(args.standalone)` 已经把所有写入类 action（archive/save/set-primary/confirm-skill 等）挡在 `READ_ONLY_ACTIONS` 白名单之外，这是早已存在的机制。

## 视觉与动效

美术方向：深空但清晰。

要求：

- 深色宇宙背景。
- 柔和 bloom。
- Goal 不过曝。
- 暗面不能死黑。
- North Star 有中心感。
- Project / Task / Evidence 层级清楚。
- Evidence 微光可见但不抢主目标。
- 默认 auto rotate 很慢。
- 聚焦动画明确但不过度。
- 长时间观看不晕。

避免：

- 高频粒子雨。
- 强闪烁。
- 大面积霓虹污染。
- 整颗 goal 糊成白球。
- 控件遮住星系主体。

## 已有实现基础

以下均已核实为现有实现，本轮未重建：

- `all_goals` payload 已出现，可支持历史目标显示。
- goal rail / graph 里已有 show archived 的部分状态（本轮修正了 standalone 下的默认值，见「历史目标」）。
- 3D 图已有 North Star、Goal、Project、Task、Evidence、Skill 的星系布局（`growthGalaxyLayout`）。
- task ring 已有自适应几何公式雏形（`placeConcentric`，`asin` 环容量公式）。
- Evidence moon / comet trail 机制仍在（`_addCometTrail`，按 strength/review/recency 分级）。
- `hasEvidence` 微光标记已出现（总览态 task 静态 halo）。
- 光照参数已有较新一版：较低 AmbientLight、HemisphereLight、较高 bloom threshold、goal emissive 降低。
- 图例 pointer-events 和默认折叠已有部分修复（核实：默认折叠已满足，见「图例」）。

后续优化应优先收口这些已有能力，而不是另起一套 Dashboard。

## Task / Project 碰撞验收（先验证、按需加固）

策略：不预先重写 `placeConcentric` 几何。先在 e2e / 截图验收里驱动下列压力场景；只有实际出现重叠时才补「溢出到外环 + dev-log 告警」的显式降级。

关键场景：

- 单个 project 下 20-30 个 task。
- 8 个左右 project 同时围绕一个 goal。
- task 不插进 project 球体。
- 同环 task 不重叠。
- 环间 task 不互相蹭。
- project 之间的 task disk 不明显撞在一起。

如果几何预算超出，应显式降级或在开发日志中提示，不要静默重叠。

## i18n（核实：绝大多数已齐全；本轮补齐真实缺口）

核查结论：zh/en `home.yaml` 已有 489/489 key 对齐，图例、onboarding、search、skill progress、archived toggle 文案早已双语齐全。真实缺口只有两处，本轮已补：

- `goal_status_active` / `_draft` / `_archived` / `_completed` / `_paused`（此前缺失，中文界面会直接显示原始英文 `active`/`archived` 等）。
- `dashboard_open_fullscreen_galaxy`（替换 `dashboard_open_8502_canvas`）与 `dashboard_open_main_app`（替换 `dashboard_open_8503`）。

范围限定：**不做** `label(ui, key, "English fallback")` 203 处调用的全量剥离扫荡——zh 覆盖率已经是 489/489，收益小、风险高，本轮只保证新增/改名的 key 双语可解析。

已修改文件：

```text
src/nblane/i18n/zh/home.yaml
src/nblane/i18n/en/home.yaml
```

## 主要文件范围

可能涉及：

```text
app.py
src/nblane/web_reader_api/__init__.py
src/nblane/web_reader_api/templates/dashboard.html
src/nblane/home_dashboard_component/frontend/src/main.jsx
src/nblane/home_dashboard_component/frontend/src/galaxy_scene.js
src/nblane/home_dashboard_component/frontend/src/style.css
src/nblane/home_dashboard_component/frontend/src/payload.js
src/nblane/i18n/zh/home.yaml
src/nblane/i18n/en/home.yaml
tests/e2e/dashboard_canvas_8502.spec.ts
tests/e2e/dashboard_8503.spec.ts
tests/test_web_reader_api.py
tests/test_home_dashboard.py
docs/zh/guides/dashboard.md
docs/zh/guides/web-ui.md
```

注意：测试文件名里的 `8503` 可以暂时保留，但测试逻辑和文档应明确生产是 `8501 + 8502`。

## 测试计划

### 前端

```bash
cd src/nblane/home_dashboard_component/frontend
npm test
npm run build
```

检查（已跑通，`npm test` 7/7 通过，`npm run build` 产出内容哈希文件名）：

- payload normalize 不破坏 `allGoals`。
- archived / paused / completed goal status 可被前端识别。
- standalone 全屏页能加载 payload。
- static assets 被刷新（Vite 输出 `home-dashboard.<hash>.js/css`，sidecar 按目录 glob 自动拾取新哈希名，旧哈希无害 404）。

### Python

```bash
PYTHONPATH=src .venv/bin/python -m py_compile \
  app.py \
  src/nblane/web_reader_api/__init__.py \
  src/nblane/web_i18n.py
```

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_home_dashboard.py \
  tests/test_workspace_graph.py \
  tests/test_web_reader_api.py
```

已跑通：51 passed（含本轮新增的 2 个 dashboard 鉴权测试）。

重点验证：

- `/dashboard?profile=<profile>` 可返回 HTML。
- `/api/dashboard/payload?profile=<profile>` 可返回 payload。
- profile access 仍受 auth 限制（`test_dashboard_payload_requires_auth_cookie_when_auth_configured`：无 cookie 401；`test_dashboard_payload_auth_handoff_sets_cookie_and_checks_profile_access`：handoff 200 + 跨 profile 403）。
- `all_goals`、active goals、graph nodes 不回退。

### E2E / 可视化

全屏 `/dashboard`：

```bash
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
npx playwright test tests/e2e/dashboard_canvas_8502.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line
```

主应用：

```bash
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
NBLANE_DASHBOARD_8503_BASE_URL=http://127.0.0.1:18503 \
npx playwright test tests/e2e/dashboard_8503.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line
```

决定：文件名和 `NBLANE_DASHBOARD_8503_BASE_URL` 环境变量名暂时保留（测试文件名可以滞后于生产端口语义），但测试断言已更新为匹配新文案——`dashboard_8503.spec.ts` 现在断言 `打开全屏星系|Open Fullscreen Galaxy` 而不是旧的 `打开 8502 Canvas`。

### 截图验收

大屏优先：

- `1920 x 1080`
- `1440 x 1000`

基本回归：

- `1280 x 900`

验收点（代码侧改动已就位，尚需人工截图核验）：

- `/dashboard` 首屏是全幅 3D 星系（无常驻两栏 workbench）。
- Canvas 非空。
- 搜索框可用。
- 图例默认折叠。
- 图例展开后可滚动。
- 点击 goal 可聚焦。
- 点击空白可回总览（并清空抽屉 + `?node=` 参数）。
- archived / paused / completed goals 默认弱化可见（standalone `defaultShowArchived=true`）。
- mutation 按钮不存在。
- 返回主应用不指向 `8503`（同源 `/` 或 `NBLANE_STREAMLIT_BASE_URL`）。
- 页面没有明显横向溢出。
- 视图切换器渡化为左上角小型 overlay，不是显眼分段条。
- 选中节点后地址栏 `?node=` 更新，可复制分享。

### 生产 smoke

生产部署后检查：

```text
https://www.nblane.cloud/dashboard?profile=<profile>
https://www.nblane.cloud/api/dashboard/payload?profile=<profile>
```

确认：

- 通过 Caddy 命中 `8502`。
- 登录态正常。
- 返回主应用链接正常。
- 主应用 `8501` 首页有“打开全屏星系”入口。
- `/dashboard` 不出现写入按钮。
- `/dashboard` 没有白屏或资产 404。

## 文档更新（已完成）

已同步更新：

```text
docs/zh/guides/dashboard.md
docs/zh/guides/web-ui.md（核实：已正确记录生产 8501/8502，无需改动）
docs/zh/guides/deployment-tencent-cloud.md（Caddyfile 示例补齐 /dashboard*、/api/dashboard/*、/paper-library*、/auth/* 反代）
```

已落地的关键修正：

- 生产端口：`8501 + 8502`；普通本机开发：`8503 + 8502`；同机隔离开发：`18503 + 18502`。
- `/dashboard` 是生产可见全屏成长星系入口；`dashboard.md` 的「8502 与 8503」章节改写为「主应用与 `/dashboard` 全屏页」，不再把 8503 当作生产 Streamlit 描述。
- `/dashboard` 是只读探索页。
- 写入回主应用完成。
- 不再把用户可见文案写成「8502 Canvas」——`dashboard.md` 全文替换为「全屏星系」措辞。
- 部署文档 Caddyfile 示例此前只反代 `/reader/*`；`/dashboard*` 缺失会导致生产环境打开全屏页 404 或落到 Streamlit 主应用，`/auth/*` 缺失会导致 8501→8502 的登录 handoff 失败（表现为打开 `/dashboard` 时 401）。本轮已补全六条 `handle` 块。

## 非目标

本轮不做：

- 不重构整个 Dashboard 数据模型。
- 不把 `/dashboard` 做成完整编辑器。
- 不在 `/dashboard` 内实现 capture / save / archive。
- 不新增端口。
- 不把主页面改成全屏。
- 不引入强闪烁、高频粒子雨或过度霓虹风格。
- 不把 Source / Evidence / Claim / Skill / Output 混成一个字段。
- 不让 AI 静默提升 evidence、修改 skill status 或写入 goal links。

## 完成定义

- [x] `8501` 主页面布局保持不变，但有明确的“打开全屏星系”入口（`GraphHeroPanel` overlay，新标签打开）。
- [x] `/dashboard?profile=...` 在生产路径可见（部署文档 Caddyfile 已补 `/dashboard*` 反代；代码侧路由早已存在）。
- [x] `/dashboard` 默认进入全幅 3D 成长星系（`fullBleed` 布局 + 视图切换器降级为 overlay）。
- [x] `/dashboard` 只读，没有 mutation 控件（早已由 `READ_ONLY_ACTIONS` 保证）。
- [x] 历史目标默认弱化可见（standalone `defaultShowArchived=true`）。
- [x] Evidence 总览有微光，聚焦有彗星（早已实现，未改动）。
- [x] 图例可折叠、可滚动、不抢交互（核实早已满足）。
- [x] 返回主应用不再默认指向 `8503`（同源 `/` 兜底）。
- [x] 中英文关键文案补齐（`goal_status_*`、`dashboard_open_fullscreen_galaxy`、`dashboard_open_main_app`）。
- [x] 深链选中节点后可写回 `history.replaceState`，地址栏可复制分享。
- [x] 构建产物内容哈希命名，避免部署后缓存陈旧包。
- [x] `/api/dashboard/payload` 鉴权补齐单测（401 / 403 / 200）。
- [x] 前端 build（`npm run build`）、前端单测（`npm test` 7/7）、Python `py_compile` + `pytest`（51/51）全部通过。
- [ ] Dashboard E2E（`dashboard_canvas_8502.spec.ts` / `dashboard_8503.spec.ts`）和大屏截图验收——需要实际起 8501/8502/8503 服务后人工跑一遍 Playwright + Chrome 视觉核对，本轮未在此环境执行（无运行中的服务）。
- [ ] Task/Project 碰撞压力场景（20-30 task / 8 project）——留给上面的 E2E/截图验收一并核对，未发现问题则不需要额外加固几何。
