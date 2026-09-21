---
status: draft
owner: docs
last_verified: 2026-09-16
---

# Dashboard 使用说明

Dashboard 是 nblane 的日常工作台。它不是完整 `SKILL.md` 编辑器，也不是页面导航清单，而是把当前 profile 的成长图谱投影成一组可操作入口。

核心链路：

```text
North Star
  -> Goal
  -> Work / Research / Agent Runs
  -> Source
  -> Evidence
  -> Claim
  -> Skill / Gap / Output
  -> Feedback
```

## 首屏怎么读

- **North Star**：长期方向，来自 `SKILL.md` 的 Profile Context。private 模式下不会把明文送入 Dashboard payload。
- **Primary Goal**：当前阶段目标，来自 `goals.yaml`。Dashboard 用它决定优先展示哪些任务、source、skill gap 和输出机会。
- **Active Goals**：当前还在推进的目标。主应用（8501）内嵌的 3D hero 里这里只做上下文展示；点击编辑 / 切换只在主应用可用。
- **Daily Brief（今日简报）**：Context Header 与 Graph Hero 之间的全宽简报条。启发式部分由 `core/daily_brief.py` 从 payload 已有数据派生（今日焦点 = 主目标 + Doing 顶部任务；待你决策 = 待审 evidence 数 + agent-activity pending 数；风险 = health errors/warnings + 停滞超过 14 天的 Doing 任务；研究动态 = source 收件箱 / 活跃数），搭 `dashboard_payload` 的 mtime 指纹缓存，不引入额外每次 rerun 的重读。配置了 `dashboard.daily_brief` AI 动作时，会用启发式快照作 grounding 经 AI gateway 生成一段话简报（按 payload revision + 日期 + backend/model + 语言缓存，失败也缓存），未配置 / 出错 / `NBLANE_DISABLE_NETWORK_LOOKUPS` 时静默回退为纯启发式简报。每条目都带可点击的 action chip，跳转对应页面。
- **Context Canvas**：Growth Graph 的可视化投影。主应用首屏内嵌渲染 3D hero，并提供“打开全屏星系”入口跳到独立 `/dashboard` 全屏页；独立全屏页默认进入 3D Graph，只读，适合大图探索。
- **Inspector**：点击节点后的详情区。真实节点应提供 owner page 或直接动作；placeholder 节点只表示系统还没有对应事实源或记录。
- **行动队列 / 待你决策**：Graph Hero 右栏顶部的决策队列覆盖待审 evidence（跳 Evidence Review）、agent-activity pending writebacks（跳 Agent Activity）和 health errors/warnings（跳 Profile Health）；每个条目都是可点击跳转的按钮，不是纯数字。原有统计卡（技能进度、Health、Research）保留在队列下方。

## Command Bar（命令栏）

Context Header 底部（次目标 rail 之下、操作按钮之上）有一行命令输入栏，只在主应用可编辑模式下渲染（standalone / embed 只读模式不显示；`payload.command_bar.enabled` 缺省即隐藏）。

输入一行自然语言后回车或点「执行」，前端发 `command_bar_submit {text}` 事件；`app.py` 用 `core/intent.py` 的离线启发式解析器 `parse_intent` 路由：

- **写类意图**（`kanban.add`、`evidence.capture`）**先确认后写入**：submit 只把解析结果（动作类型 / 标题 / 列 / 截止日期 / 标签）存为 pending intent，下一帧命令栏下方出现确认卡；点「确认写入」发 `command_bar_confirm {intent_id}` 才真正执行，点「放弃」发 `command_bar_discard {intent_id}` 清掉 pending。
  - `kanban.add` 确认时从磁盘现取 kanban（`parse_kanban`）→ 追加任务（Doing 落 `started_on=今天`；due 以 `due: <iso>` 存进 task details；tags 逗号连接）→ `ensure_kanban_task_ids` → `core/kanban_merge.save_kanban_with_merge(profile, sections, base=None)`（冲突时 union 合并）保存 → 刷新文件快照 + toast。
  - `evidence.capture` 确认时复用首页 capture inbox 的既有写入通道（Research Source Inbox，`capture_event="command_bar"` 标记来源），保持单一写入路径。
- **只读意图直接执行**：`navigate`（如「打开看板」）跳对应页面；`review.weekly_summary`（如「这周做了什么」）跳 `pages/8_Review.py`。
- **未识别**（`unknown`）不写任何数据，下一帧在命令栏下方显示一行示例命令帮助（单帧一次性）。

命令栏事件只影响当前 profile；pending intent 按 profile 存在 session state 里，confirm 时校验 `intent_id` 匹配才执行。

## 图谱元素

Dashboard 遵守 `docs/zh/product/growth-graph.md` 的对象边界：

| 元素 | 含义 | 典型事实源 |
|------|------|------------|
| Source | 原始材料、观察、网页、论文、repo、反馈、旧简历导入 | `research/sources.yaml`、`inbox.yaml` |
| Evidence | 经过审阅、可作为证明的事实 | `evidence-pool.yaml` |
| Claim | 对 evidence 的解释和断言，供 skill / output 复用 | `claims.yaml` |
| Skill | 能力状态，不等于自评文案 | `skill-tree.yaml` |
| Output | 博客、简历 bullet、公开项目、项目更新 | `blog/`、`outputs.yaml`、`projects.yaml` |

不要把 Source、Evidence、Claim、Skill、Output 混成一个字段。AI 可以生成候选，但不能静默把来源提升为证据，也不能静默修改 skill status。

## 常见动作

- **Capture source**：把临时想法、网页、论文、repo 或观察先放入 Research source inbox。默认 private，不直接生成 evidence。
- **Review evidence**：进入 Evidence Review，处理 Done 未结晶、unlinked evidence、needs review 和 status risk。
- **Link goal to skills**：在 goal inspector 中运行规则匹配或 AI 匹配；候选需要勾选确认后才写入 `goals.yaml`。
- **Open Gap**：用当前 goal 或 task 作为上下文进入 Gap Analysis。
- **Open Output**：进入 Output Studio，把 accepted claim / reviewed evidence 整理成 blog、project update、resume bullet 或 public candidate。
- **Open Health**：检查 private leak、断链、unsupported claim 和同步漂移。

## 按钮交互原则

Dashboard 的按钮不能只是“看起来可点”。每个可见按钮点击后至少要满足下面一种反馈：

- **页面跳转**：例如 Evidence Review、Gap Analysis、Output Studio、Open 8503。
- **视图切换**：例如 Focus Path、2D Canvas、Attention、3D Graph，必须有 active 状态和主视图区变化。
- **节点选择**：Focus Path node、Attention chip、Explore list node 点击后，必须更新 Inspector 或选中态。
- **表单出现**：添加目标、编辑目标这类按钮只有在 inspector 会显示表单时才出现。
- **写入反馈**：Capture source、Save goal、Archive、Confirm links 必须显示成功 / 失败，并在 rerun 后看到计数或状态变化。

独立 `/dashboard` standalone / embed 当前按**只读 Canvas**处理：不显示 Capture、Save goal、Archive、Set primary、Skill match 这类写入控件。需要写入时从 `/dashboard` 跳回主应用（生产为 8501），由 Streamlit 负责 profile 选择、快照、确认和错误反馈。

## AI 设置

Dashboard 顶部 **本页 AI 设置** 只配置 Dashboard 页面自己的 AI 动作。它会写入当前 profile 的
`web-preferences.yaml`，只保存非密钥偏好，不会改变 Research、Kanban、Evidence Review 等其他页面的
页面级 AI 设置。

- 顶部状态：显示当前 LLM 是否配置、默认模型，以及部署级 Codex 是否安装 / 登录 / 默认模型。
- backend：应用默认 / LLM / Codex。选择“使用默认”时，会按动作默认 backend 运行。
- LLM model：可选应用默认、建议模型或自定义模型；默认值来自侧栏 / 环境变量。
- Codex model：可选 Codex 默认、建议模型或自定义模型；默认值来自侧栏 / 环境变量 / 当前 profile 的 Codex 非密钥偏好。
- Test model：每个 Dashboard AI 动作都有独立测试按钮，测试当前行的 backend / model 组合，不需要先保存。

当前 Dashboard 至少覆盖：

- `dashboard.goal_skill_match`：为 goal 生成 skill link 候选。
- `dashboard.daily_brief`：用启发式简报快照作 grounding 生成一段话今日简报；只读，不写文件，未配置时首页回退为启发式简报。

Research 里的论文搜索、翻译、Reader 和 DeepRead 使用 Research 页右上角的 **Research AI 配置**；
看板的拆任务、gap 路由、任务理解和 Done -> evidence 使用侧栏里的 **看板 AI 引擎** 或对应页面配置。
侧栏 LLM / Codex 仍是默认运行时配置，页面级设置只在对应页面动作上覆盖它。

API key、token、cookie、authorization 不会写入 profile 文件。未配置模型时，Dashboard 应显示统一的未配置提示，并保留规则匹配和手动操作。

## 主应用与 `/dashboard` 全屏页

端口口径：生产是 `8501`（Streamlit 主应用）+ `8502`（FastAPI sidecar）；普通本机开发用
`8503`（Streamlit）+ `8502`；与生产同机并行的隔离开发用 `18503` + `18502`。`8503`
只是本机开发端口，不会出现在生产环境里，任何用户可见文案或链接都不应硬编码它。

- **主应用（生产 8501）**：负责 profile 选择、安全写入、全局导航、AI 设置、fallback 和审阅流程。首屏内嵌渲染 3D hero（Graph Hero），并提供“打开全屏星系”入口。
- **FastAPI sidecar（8502）**：负责高交互 Reader、Paper Library，以及只读的独立全屏 `/dashboard` 页。

`/dashboard` 全屏页支持这些 URL 形态：

```text
/dashboard?profile=<profile>
/dashboard?profile=<profile>&view=focus
/dashboard?profile=<profile>&view=canvas
/dashboard?profile=<profile>&view=attention
/dashboard?profile=<profile>&view=3d
/dashboard?profile=<profile>&view=3d&node=<node_id>
```

嵌入形态（`&embed=1`，SPA 首页星系 hero 与 Streamlit 健康检查使用）额外支持
`&compact=1`：紧凑模式把检查器从常驻右栏改为点选节点才弹出的抽屉（星系吃满
嵌入宽）、隐藏与宿主页指标重复的 Attention 条、3D 画布高度下限 560→480，
适配 hero 尺寸的 iframe；不带 compact 的 embed、standalone 全屏页与 Streamlit
组件内嵌行为不变。SPA 后端 `GET /home` / `GET /research` 返回的
`sidecar.dashboard_url` 已统一带 `embed=1&view=3d&compact=1`。

生产环境下 Caddy 把 `/dashboard*` 反代到 8502，浏览器可以直接访问
`https://<domain>/dashboard?profile=<profile>`；本地直连时映射为
`http://127.0.0.1:8502/dashboard?profile=<profile>`。

主应用首屏 3D hero 右上角有“打开全屏星系”overlay 入口（`data-action="open-fullscreen-galaxy"`），新标签页打开全屏页，并带上当前选中节点（`view=3d&node=<node_id>`）。全屏页选中 / 聚焦节点时会用 `history.replaceState` 更新地址栏的 `node` 参数，方便复制分享当前视图。

全屏页顶部有“返回主应用”链接，默认同源指向 `/`；生产同源部署下无需额外配置，本地开发由
`NBLANE_STREAMLIT_BASE_URL` 显式指定对应端口。

本地开发建议同时启动：

```bash
PYTHONPATH=src .venv/bin/uvicorn nblane.web_reader_api:app \
  --host 127.0.0.1 --port 8502 --reload --reload-dir src

NBLANE_READER_API_BASE=http://127.0.0.1:8502 \
NBLANE_STREAMLIT_BASE_URL=http://127.0.0.1:8503 \
PYTHONPATH=src .venv/bin/streamlit run app.py \
  --server.address=127.0.0.1 --server.port=8503 --server.headless=true
```

8502 不可达时，主应用首屏“打开全屏星系”入口应隐藏（而不是链接到一个 404），继续显示本地内嵌 3D hero。

## 缩放与响应式策略

主应用（生产 8501，本机开发 8503）里的 Dashboard React 组件运行在 Streamlit component iframe 里，所以浏览器窗口宽度不等于组件实际可用宽度。开启 Streamlit 侧栏、浏览器放大、IDE port forwarding 页面外壳变窄时，`1440px` 浏览器宽度可能只给 Dashboard 约 `980px` 的有效宽度，`1280px` 可能只剩约 `820px`，再窄时会落到约 `720px`。

因此响应式断点要按**组件有效宽度**设计，而不是按浏览器 viewport 设计：

- 首页 Graph Hero 在约 `720-980px` 有效宽度下仍保持“左侧图谱、右侧行动面板”的双列结构，避免图谱首屏被挤成一千多像素高的纵向堆叠。
- Graph Hero 只在约 `640px` 以下进入单列移动布局；这是手机窄屏或极高浏览器缩放时的预期降级。
- Context Header / Goal rail 使用 `minmax(0, fr)` 这类可收缩网格，长文本用 ellipsis 或 line clamp，避免某个 chip、按钮或标题把整个 iframe 撑出横向滚动。
- 初始首页只渲染本地 Graph Hero preview，不默认创建 8502 iframe；8502 不可达时仍保留首屏图谱，只隐藏按需加载内嵌画布的入口。

缩放类问题的修复必须进入 Chrome 自测：至少检查 `1440 x 1000`、`1280 x 900`、`1024 x 900` 下无页面级横向滚动，Graph Hero canvas 非空，并确认 `1280 x 900` 时右侧行动面板仍在图谱右侧而不是提前掉到下一行。

## Chrome 可视化验收

Dashboard 的交互验收以 Chrome / Playwright 为准，不能只看 Python read model。建议本地开发每轮至少检查：

```bash
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
npx playwright test tests/e2e/dashboard_canvas_8502.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line

PLAYWRIGHT_CHROMIUM_EXECUTABLE=/snap/bin/chromium \
NBLANE_DASHBOARD_8503_BASE_URL=http://127.0.0.1:8503 \
npx playwright test tests/e2e/dashboard_8503.spec.ts \
  --config=tests/e2e/playwright.config.ts --reporter=line
```

`tests/e2e/dashboard_8503.spec.ts` 文件名里的 `8503` 只是历史命名，测试本身跑在
`NBLANE_DASHBOARD_8503_BASE_URL` 指定的 Streamlit 端口上（生产语义上对应 8501）。

重点看四类结果：

- **非空可视化**：3D canvas 的像素统计不能是白屏；Focus Path 节点数应大于 3。
- **响应式**：`1440 x 1000`、`1280 x 900`、`1024 x 900`、`390 x 820` 下无页面级横向滚动；主应用首屏 Graph Hero 在中等有效宽度下不能过早单列堆叠。
- **按钮反馈**：每个按钮要有跳转、active 状态、Inspector 更新、表单出现或写入提示。
- **折叠控件**：`More filters`、`更多字段` closed 状态下内部 input / button 不占布局、不可聚焦。

临时开发计划和按钮矩阵详见仓库根目录 [Dashboard 临时开发计划](../../../dashboard.md)。稳定后再把其中的长期内容合并回 `docs/zh/product/web-experience.md` 和本使用说明。
