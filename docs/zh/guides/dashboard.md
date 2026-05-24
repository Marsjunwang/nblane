---
status: draft
owner: docs
last_verified: 2026-05-23
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
- **Active Goals**：当前还在推进的目标。8503 内嵌 8502 Canvas 时这里只做上下文展示；本地 fallback inspector 可见时才提供点击编辑 / 切换。
- **Context Canvas**：Growth Graph 的可视化投影。8503 首屏默认显示 Canvas summary 和 Focus Path 摘要，需要时再加载内嵌 8502 画布；本地 fallback 默认优先看 Focus Path / attention；独立 8502 Canvas 默认进入 3D Graph，适合大图探索。
- **Inspector**：点击节点后的详情区。真实节点应提供 owner page 或直接动作；placeholder 节点只表示系统还没有对应事实源或记录。
- **Workbench**：今日工作区，集中显示 capture、Doing、Evidence Review、Gap、Output 和 Health 信号。

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

8502 standalone / embed 当前按**只读 Canvas**处理：不显示 Capture、Save goal、Archive、Set primary、Skill match 这类写入控件。需要写入时从 8502 跳回 8503，由 Streamlit 负责 profile 选择、快照、确认和错误反馈。

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
- `dashboard.graph_insights`：为图谱风险和下一步生成摘要候选。

Research 里的论文搜索、翻译、Reader 和 DeepRead 使用 Research 页右上角的 **Research AI 配置**；
看板的拆任务、gap 路由、任务理解和 Done -> evidence 使用侧栏里的 **看板 AI 引擎** 或对应页面配置。
侧栏 LLM / Codex 仍是默认运行时配置，页面级设置只在对应页面动作上覆盖它。

API key、token、cookie、authorization 不会写入 profile 文件。未配置模型时，Dashboard 应显示统一的未配置提示，并保留规则匹配和手动操作。

## 8502 与 8503

- **8503 Streamlit**：负责 profile 选择、安全写入、全局导航、AI 设置、fallback 和审阅流程。
- **8502 FastAPI sidecar**：负责高交互 Reader、Paper Library，以及可选的独立 Dashboard canvas。

Dashboard Canvas 支持这些 URL 形态：

```text
http://127.0.0.1:8502/dashboard?profile=<profile>
http://127.0.0.1:8502/dashboard?profile=<profile>&view=focus
http://127.0.0.1:8502/dashboard?profile=<profile>&view=canvas
http://127.0.0.1:8502/dashboard?profile=<profile>&view=attention
http://127.0.0.1:8502/dashboard?profile=<profile>&view=3d
http://127.0.0.1:8502/dashboard?profile=<profile>&view=3d&node=<node_id>
```

8503 首页会先显示 Canvas summary：包括 Focus Path 预览、attention / node 数量和“打开 8502 Canvas”入口。用户点击“加载内嵌画布”后，才会按需加载 8502 iframe，并使用 `view=focus` 呈现可读主路径；需要旋转、缩放或探索完整关系时，再打开 8502 standalone 或切到 3D Graph。

Canvas summary 中的 Focus Path 节点会打开 8502 standalone，并携带 `view=3d&node=<node_id>`。8502 会初始选中对应节点，右侧 Explore list 支持搜索、按 layer 分组，以及隐藏 placeholder 节点，适合在大图中继续定位上下游关系。

8503 在注入 iframe 前会检查 8502 是否可达。8502 不可达时，顶部入口会禁用并显示提示，页面继续使用本地 React Dashboard fallback，不应出现空白大 iframe。

本地开发建议同时启动：

```bash
PYTHONPATH=src .venv/bin/uvicorn nblane.web_reader_api:app \
  --host 127.0.0.1 --port 8502 --reload --reload-dir src

NBLANE_READER_API_BASE=http://127.0.0.1:8502 \
PYTHONPATH=src .venv/bin/streamlit run app.py \
  --server.address=127.0.0.1 --server.port=8503 --server.headless=true
```

8502 未启动时，8503 Dashboard 不应白屏，应继续提供 Streamlit component 或 native fallback。

## 缩放与响应式策略

8503 的 Dashboard React 组件运行在 Streamlit component iframe 里，所以浏览器窗口宽度不等于组件实际可用宽度。开启 Streamlit 侧栏、浏览器放大、IDE port forwarding 页面外壳变窄时，`1440px` 浏览器宽度可能只给 Dashboard 约 `980px` 的有效宽度，`1280px` 可能只剩约 `820px`，再窄时会落到约 `720px`。

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

重点看四类结果：

- **非空可视化**：3D canvas 的像素统计不能是白屏；Focus Path 节点数应大于 3。
- **响应式**：`1440 x 1000`、`1280 x 900`、`1024 x 900`、`390 x 820` 下无页面级横向滚动；8503 首页 Graph Hero 在中等有效宽度下不能过早单列堆叠。
- **按钮反馈**：每个按钮要有跳转、active 状态、Inspector 更新、表单出现或写入提示。
- **折叠控件**：`More filters`、`更多字段` closed 状态下内部 input / button 不占布局、不可聚焦。

临时开发计划和按钮矩阵详见仓库根目录 [Dashboard 临时开发计划](../../../dashboard.md)。稳定后再把其中的长期内容合并回 `docs/zh/product/web-experience.md` 和本使用说明。
