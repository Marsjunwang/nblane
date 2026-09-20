---
status: active
owner: 王军
last_verified: 2026-09-20
source_of_truth: app.py、pages/、src/nblane/web_*.py、src/nblane/web_reader_api/、src/nblane/web_api/、src/nblane/web_ui/、src/nblane/*_component/、tests/e2e/
---

# 前端 SPA 迁移方案（Streamlit → React + FastAPI）

> 本文是[深度融合总体方案](openclaw-deep-integration.md) L5 层的完整展开，
> 可独立实施。目标终态：**完全退役 Streamlit**，替换为交互更强壮、视觉更
> 优美的 React SPA + FastAPI 后端；过程中双轨运行，逐页 parity 验收。

## 实施进度（2026-09-20）

| 里程碑 | 状态 | 说明 |
|--------|------|------|
| M0 spike | ✅ 已完成 | `src/nblane/web_api/`（create_app、4 个只读端点、OpenAPI 契约测试） |
| M1 底座 | ✅ 已完成 | 后端：cookie 认证（复用 core/auth HMAC、登录限流）、profile 作用域 403、只读端点 6 个、activity apply/dismiss（ETag + If-Match，409/412）。前端：`src/nblane/web_ui/frontend` 脚手架（Vite+React18+TS+Mantine8+TanStack Query）+ 登录/档案列表/健康页 + **Agent Activity 审批页**（列表+抽屉+应用/驳回+412 自动刷新流），build 与 vitest 全绿 |
| SPA 打包（L5 收尾） | ✅ 已完成 | 构建产物 `src/nblane/web_ui/static/` 提交入库并声明进 `pyproject.toml` package-data（`nblane.web_ui` = `static/index.html` + `static/assets/*`，与各 `*_component` 同一惯例）；`mount_spa` 以 `__file__` 相对定位包内目录，editable / wheel 安装均无需 Node 即可服务 SPA；CI `frontend-artifacts` job 扩展覆盖 SPA（重建 + 产物新鲜度比对）；`tests/test_web_api_spa.py` 增补打包契约测试 |
| M2 高频页 | 🔨 大部分完成 | 已实现页面：看板（原生 Mantine：只读列 + 快建卡 + 移动/完成 + 3-way merge 冲突语义，API `POST /kanban/cards*`）、技能树（schema label 标题、`requires` 边推导层级、证据计数、状态汇总 chips + 折叠树 + 筛选）、目标（North Star 卡 + 目标卡）、证据（搜索/状态过滤/详情模态）、Gap Analysis（规则版）；OpenAPI 契约快照进 CI（`tests/test_web_api_openapi_snapshot.py`）+ TS client 代码生成（`npm run gen:api`）；`spa_smoke.spec.ts` e2e 4/4 通过。剩余：Gap Analysis 的 LLM 异步任务（需 SSE 任务基建）、拖拽与组件拆库复用（策 B） |
| M3–M5 | 🔨 进行中 | Evidence Review 首切片已完成（API `GET /evidence-review` + `POST /evidence-review/bulk` 批量接受/打标 + `POST /evidence-review/deprecate` 拒绝/恢复，ETag + If-Match 412；SPA `/p/:name/evidence-review` 原生 Mantine 批量处置页，策 B 未直接复用 evidence_editor 组件——其为 Streamlit postMessage 协议 + 无导出组件的独立 bundle，详见策略 B 节）。Review 周回顾切片已完成（API `GET /review` 窗口聚合 + `POST /review/save` 存候选到 Agent Activity + `POST /review/apply` 证据/下一步/公开草稿写回，五源文件弱 ETag + If-Match 412，逐候选结果不报整单失败；纯规则聚合，无 LLM 依赖；SPA `/p/:name/review` 预设/自定义窗口 + 四类候选 Tab + 勾选批量处置）。Project Board 子切片已完成（API `GET /project-board` 案例+概览计数+引用选项，七源文件弱 ETag + If-Match 412；`POST /project-board/cases` 创建、`cases/{id}/save|archive` 基本信息保存/归档、`cases/{id}/milestones*` 里程碑增改删（重复 id 422）、`cases/{id}/tasks` 建项目任务、`tasks/{id}/move` 按任务 id 挪看板列（复用 kanban 3-way merge + 板级回同步）；AI 建议引用 `POST cases/{id}/suggest-refs` 走 `project.suggest_refs` 网关动作（require_review 落 Agent Activity），LLM 不可用降级 422 `project_suggest_refs_failed`，建议仅做 confirm-not-fill 提示不落盘；SPA `/p/:name/project-board` 原生 Mantine：概览 chips + 状态 Tab 案例列表 + 详情三 Tab（基本信息/里程碑/任务）+ AI 建议卡片，策 B 未直接复用 project_board/project_timeline 组件——同 evidence_editor：JSX + 自有 CSS + events.js postMessage 桥、无可导入导出，多项目时间轴视图留待后续切片）。Output Studio（M4）首切片已完成（API `GET /studio` 博客列表+状态计数+候选源选项、公开层六文件+blog 目录弱 ETag + If-Match 412；`POST /studio/init` 初始化公开层（幂等）、`studio/blog` 建草稿、`blog/{slug}/save|check|publish` 编辑/发布前检查/发布门控（校验失败 422 `blog_publish_blocked` 不落盘）、`candidates/preview|create` 证据/断言候选生成与草稿创建（规则模板兜底、无 LLM 依赖，写回落 Agent Activity）、`jd-match` JD 匹配分析——LLM 未配置降级 422 `studio_jd_match_unavailable`；SPA `/p/:name/studio` 原生 Mantine 三 Tab（博客列表+Markdown 编辑器+状态流转 / 从证据生成两段式预览-确认 / JD 匹配降级卡片）；BlockNote 本切片不引入，理由见策略 B 节评估记录，编辑器留待「博客编辑器」子切片）。Research 切片已完成（M4，策 C 内聚）：API `GET /research` 返回来源收件箱计数（状态/类型/active）、research 断言与引用计数、最近来源列表 + sidecar 坐标（`SidecarInfoModel`：base 解析自 `NBLANE_READER_API_BASE`，同源哨兵 `0/false/off/none` → 相对路径，auth 开启时带 120s handoff token 供 `/auth/session` cookie 引导）；SPA `/p/:name/research` = 摘要卡 + 最近来源表 + Paper Library 工作台入口（新标签 / iframe 嵌入，`SidecarFrame` 复刻 Streamlit 的 form-POST handoff 引导），PDF 阅读器与论文库不重写。Home 切片已完成（M4，策 C 落地，策 B 评估见下）：API `GET /home` 复用 `core.home_dashboard` 的只读子聚合（skills/kanban/pending_evidence/source/project/claim/health/agent_activity + 目标进度推导），不含 payload 构建器的快照写副作用（纯读 GET）；SPA `/p/:name/home` = 北极星条 + 当前目标（进度条/停滞标记）+ 技能 RingProgress 降级可视化 + 看板/证据/研究/项目/健康/代理活动概览卡 + 快捷入口 + 3D 仪表盘 iframe 内嵌（sidecar `/dashboard?embed=1` standalone 模式）。剩余：Public Build、Output Studio 站点预览与博客编辑器子切片、Home 目标编辑器/命令条 |

## 0. 为什么换、凭什么敢换

**换的理由**：Streamlit 的 rerun 模型在重交互页面（看板拖拽、批量处置、
编辑器）已显疲态——`@st.fragment(run_every=1)` 轮询、`st.query_params`
深层链接、`components.html` 滚动 hack（`pages/9_Agent_Activity.py:183`）
都是在绕框架限制；移动端布局与主题能力有限。

**敢换的依据**（均为本仓库已验证事实）：

1. `src/nblane/core/` 已是 UI 无关层——CLI、MCP、FastAPI sidecar 都在消费
   它，业务逻辑零重写。
2. FastAPI sidecar（`web_reader_api/`，2872 行）**已经在生产跑着 3 个独立
   React 应用**（`/dashboard`、`/paper-library`、`/blog-editor`）加 1 个手写
   vanilla-JS/pdf.js 阅读器（`/reader`）+ 56 条 HTTP 路由（含 SSE），并已
   解决：cookie+handoff 认证、同源反代、i18n 注入、SSE 任务流。它就是
   新后端的核。
3. 10 个组件包声明进 `pyproject.toml`
   `[tool.setuptools.package-data]`：6 个 Vite+React、2 个免打包
   `build.mjs`（kanban_board/project_board）、2 个纯静态 HTML——SPA 的
   重交互件大半已存在。
4. 15 个 Playwright e2e spec（`tests/e2e/`，2829 行）中已有直接测 sidecar
   独立页的套件（dashboard_canvas、paper_library 等；另有若干 spec 测
   Streamlit UI 本身，需随迁移重写）——SPA 的 e2e 骨架现成。

## 1. 现状盘点（迁移范围的真实规模）

渲染层合计约 **36k 行 Python**（app.py 2725 + pages/ 10620 +
`web_output_studio.py` 7080 + `evidence_editor_host.py` 2733 +
`web_shared.py` 2162 + `kanban_ui/` 2684 + `research_ui/` 8204）。

Streamlit 耦合点统计：`session_state|cache_data|cache_resource|rerun|query_params`
命中 1036 处、39 个文件（app.py + pages/ + src/nblane/）；`pages/` 13 个
页面文件中 11 个直接 import streamlit（加 app.py 共 12 个），`src/nblane/`
下共 44 个文件 import streamlit。但 `web_cache.py`（mtime 键缓存）有运行时外
优雅降级，是最容易替换的一层。

页面盘点（复杂度按 LOC 与交互密度评级）：

| 页面 | LOC | 复杂度 | 重交互件 | 迁移策略（§3） |
|------|-----|--------|----------|----------------|
| `pages/5_Profile_Health.py` | 82 | 低 | 无 | 重写（首选试点） |
| `pages/12_Settings.py` | 58 | 低 | 无 | 重写 |
| `pages/4_Team_View.py` | 334 | 低 | 表单表格 | 重写 |
| `pages/9_Agent_Activity.py` | 871 | 中 | 队列+diff 预览 | 重写（L1 闭环的审批面，优先） |
| `pages/8_Review.py` | 366 | 中 | 表单+YAML 预览 | 重写 |
| `pages/2_Gap_Analysis.py` | 733 | 中 | 表单+LLM 任务 | 重写 |
| `pages/10_Public_Build.py` | 5+~300 | 中 | 站点预览 iframe | 重写 |
| `pages/1_Skill_Tree.py` | 718 | 中 | data_editor 式表格 | 重写 |
| `pages/3_Kanban.py` | 2608 | 高 | kanban_board、checkin_calendar 组件 + AI 轮询 | 组件复用为库 |
| `pages/11_Project_Board.py` | 2060 | 高 | project_board、project_timeline 组件 | 组件复用为库 |
| `pages/2_Evidence_Review.py` | 2624+2733 | 高 | evidence_editor（React） | 组件复用为库 |
| `web_output_studio.py` | 7080 | 极高 | BlockNote 编辑器、站点预览 | 组件复用 + 分块重写 |
| `pages/7_Research.py` + `research_ui/` | 156+~8.2k | 极高 | reader（vanilla-JS/pdf.js）与 paper-library（React），均已独立部署 | iframe → 路由内聚 |
| `app.py`（Home） | 2725 | 极高 | home_dashboard（three.js 3D） | iframe → 概览卡重写（策 B 评估后落策 C，见评估记录） |

## 2. 目标架构

```
浏览器（React SPA）
   │  HTTPS，同一域名同一端口
   ▼
FastAPI（src/nblane/web_api/，由 web_reader_api 演进而来，单进程 workers=1）
   ├── /api/v1/*        REST，OpenAPI 契约
   ├── /api/v1/*/stream SSE（任务进度，沿用 reader 既有模式）
   ├── /ws/*            WebSocket（L4 助手面板代理等）
   ├── /*               SPA 静态资源（vite build 产物，hash 缓存）
   └── 现有 /reader/* /paper-library /dashboard /blog-editor 路由原样并入
   ▼
src/nblane/core/*（零改动原则）
```

- **前端栈**：Vite + React 18 + TypeScript + **Mantine 8** + TanStack Query
  + React Router + BlockNote（富文本）。依据：Docmost 同款组合（总体方案
  §8.7），且 Mantine/BlockNote 已是 `public_blog_editor_component` 的现栈，
  组件复用零障碍；图表/3D 沿用现有组件依赖（three.js 等）。
- **API 契约**：FastAPI 自动 OpenAPI → `openapi-typescript` 生成 TS client
  （Immich 模式），契约快照进 CI（schema diff 不过即红）。
- **认证**：沿用 `core/auth.py` 的 HMAC 体系——浏览器用 httpOnly
  `nblane_auth_session` cookie（SameSite=Lax）；agent/CLI 用 scoped
  API key（`Authorization: Bearer`，Immich 双认证模式）。handoff iframe
  机制随 Streamlit 一起退役（SPA 与 API 同源，不再需要）。
- **文件冲突**：把 `core/file_state.py` 的 sha256 快照映射为 HTTP 语义：
  GET 响应带 `ETag: <sha256>`，写请求带 `If-Match`；冲突 →
  `412 Precondition Failed` + 最新内容，前端弹"他人/agent 已修改"
  对比对话框。这比 Streamlit 的 session 快照更强（跨会话、跨客户端一致）。
- **缓存**：`web_cache.py` 的 mtime 键逻辑平移为后端进程内 TTL 缓存
  （单进程 workers=1 前提下安全）。

## 3. 组件复用三策

| 策 | 适用 | 做法 |
|----|------|------|
| A. 纯重写 | 表单/表格类页面（Health/Settings/Team/Activity/Review/Gap/Skill Tree） | Mantine 组件直接实现，通常比原 Streamlit 代码短得多 |
| B. 组件拆库 | kanban_board、project_board、project_timeline、evidence_editor、home_dashboard、goal_presence、checkin_calendar | 把各 `*_component/frontend` 的 React 源码抽进 SPA 工程的 `packages/`，Streamlit 适配层（`streamlit-component-lib`）剥离为薄 wrapper；迁移期 wrapper 与 SPA 共用同一份源码，避免双份漂移 |
| C. iframe 过渡 | reader、paper-library、dashboard 独立页 | SPA 先 iframe 指向 sidecar 既有独立页（同源，无 hack），M4 再内聚为 SPA 路由 |

策 B 复用评估记录（实际切片结论）：
- **evidence_editor**（M3 Evidence Review）：不可直接复用——无对外 export 的
  独立 bundle、JSX + 自有 CSS、事件流绑定 `streamlit-component-lib`
  postMessage 桥；已抽取 Mantine 原生最小批量处置 UI。
- **project_board / project_timeline**（M3 Project Board）：同构结论——
  `project_board_component/frontend/src` 为 `main.jsx` + `events.js`
  （postMessage）+ `style.css`，无可导入模块边界；`project_timeline_component`
  同样。已抽取 Mantine 原生最小 UI（表单/手风琴/表格 + NativeSelect 挪列）；
  多项目时间轴画布留待后续切片，届时若拆库再评估。
- **public_blog_editor（BlockNote）**（M4 Output Studio 首切片）：本切片不引入
  BlockNote——博客正文以 Markdown 为 source of truth，含 `::video[]` 指令、
  `<!-- nblane:visual_block -->` 注释块与 LaTeX 公式，BlockNote 的
  markdown→blocks 往返会静默丢弃这些自定义结构（Streamlit 侧为此已有
  math-safe/组件不可用时的 Markdown 降级路径）。首切片因此采用 Markdown
  源码编辑器 + 公式提示（parity Streamlit 降级态）；`schemas/blocknote_doc.py`
  的 `*.blocknote.json` sidecar 契约与 blocks 保留逻辑（`save_blog_post`
  `blocks_json=None` 时保留既有 blocks）保证了后续「博客编辑器」子切片可无损
  接入 `@blocknote/react`（届时直接 npm 安装，与组件同栈，见 §2 前端栈）。
- **home_dashboard（three.js 3D 星系）**（M4 Home）：结论同 evidence_editor——
  组件前端是 `main.jsx` + `galaxy_scene.js`（three.js/UnrealBloomPass）+
  `events.js`（streamlit-component-lib postMessage 桥），无可导入导出边界，
  不能作为库 import 进 SPA。但该 bundle 自带 sidecar standalone 模式
  （`/dashboard?profile=X&embed=1`，自行拉取 `/api/dashboard/payload`），
  因此落到策 C 而非策 B：SPA Home 以 Mantine 概览卡片为 MVP（数据来自
  `GET /api/v1/profiles/{name}/home`，复用 `core.home_dashboard` 只读子聚合，
  技能分布用 RingProgress 做降级静态可视化），3D 星系经 `SidecarFrame` iframe
  内嵌 sidecar 独立页（auth 开启时由响应内 handoff token 先引导 sidecar
  cookie，复刻 `research_ui._render_authenticated_iframe` 的 form-POST 流程）。
  目标编辑器/命令条重写留待 Home 后续切片。
- 其余组件（kanban_board、home_dashboard 等）迁移到对应切片时逐一验证后再决策。

死代码清理（迁移顺手做）：`research_paper_reader_component` 的**组件前端**
（assets 为空、`available()` 返回 False 的死路径；注意其 `events` 模块仍被
`web_reader_api`/`core/reader_*` 引用，删除范围仅限组件前端与注册）、
`kanban_drag_component`（无调用方）。

## 4. 迁移顺序（strangler，未达标不切流）

排序逻辑：**先用只读/低复杂度页打穿"API 底座 + 设计系统 + 应用壳"**，
再按"审批闭环价值 > 日常使用频率 > 重写工作量"推进，巨无霸最后。

| 里程碑 | 内容 | 验收门 |
|--------|------|--------|
| **M0 spike（3–5 天）** | `web_api/` 骨架 + cookie 认证 + OpenAPI→TS client + Vite 壳 + Profile Health 页端到端 | Go/No-Go：构建链、认证、契约生成全通 |
| **M1 底座（8–10 天）** | 应用壳（导航/Profile 选择器/目标条/语言切换）、设计系统（Mantine 主题对齐品牌色 `#21685b`）、API：profiles/goals/activity/health/settings；页面：Health、**Agent Activity（含 apply/dismiss）**、Settings | 三页 parity + 审批闭环在 SPA 全通（服务 L1） |
| **M2 高频页（8–10 天）** | Kanban（策 B）+ Skill Tree + Gap Analysis；SSE 替代 AI 轮询 | 看板拖拽/AI 任务/打卡日历 parity |
| **M3 处置面（8–10 天）** | Evidence Review（策 B）+ Review + **新 Inbox 页**（总体方案 §4.3 微信捕获的处置面，SPA 原生实现）+ Project Board（策 B）+ Public Build | 批量处置/深链/时间轴 parity |
| **M4 巨无霸（12–15 天）** | Output Studio（BlockNote 复用 + 7080 行分块重写）+ Research（iframe→路由内聚）+ Home（3D dashboard 复用 + 目标编辑器/命令条重写） | 博客编辑/论文阅读/仪表盘 parity |
| **M5 切流退役（3–5 天）** | Caddy 默认路由 8501→8502（SPA）；Streamlit 保留一个版本只读应急；观察期后删除 streamlit 依赖与 pages/ | 全量 e2e 绿 + 一周无回退 |

**M5 之后 backlog**：「助手」内嵌实时面板（总体方案 §6.2 Step 3，经 `/ws/*`
代理 Gateway 协议）依赖其 WS spike 的 Go/No-Go 判定，不占用 M0–M5 的关键路径。

**切流后端口归一**：生产只剩 8502 一个应用端口（+18789 OpenClaw 经
`/openclaw` 反代，见总体方案 §6），Caddy 路由表从"按路径劈两半"简化为
"默认全量 + `/openclaw`"。

## 5. API 设计原则

- 资源布局 `/api/v1/profiles/{p}/...`：profile 作用域与 core 一致；
  例：`/kanban`、`/skill-tree`、`/evidence-pool`、`/inbox`、`/activity`、
  `/goals`、`/agent-tasks`、`/automations`（读 L3 的 yaml + 触发 sync）。
- 全部响应模型用 pydantic v2 声明（core 已是 dataclass，适配层薄转换）。
- 写端点语义化动词子资源：`POST /inbox/{id}/clarify`、`POST /activity/{id}/
  apply|dismiss`，与 `core/review_actions` 的动作一一对应。
- 长任务一律 SSE（reader 的 `jobs/{id}/stream` 模式原样复用）；禁用
  前端轮询模拟实时。
- 契约测试：`httpx.ASGITransport` 直打 FastAPI app（不起服务），
  每端点至少一正一负。

## 6. i18n、主题与移动端

- i18n：`src/nblane/i18n/{en,zh}/*.yaml` 仍是唯一文案源；构建期脚本转
  JSON bundle 给前端（key 不变），后端错误消息沿用同一套 key。
- 主题：Mantine CSS variables 落地 `.streamlit/config.toml` 的品牌色
  （primary `#21685b`）与浅色系；暗色模式顺势支持（Mantine 原生能力）。
- 移动端：底部 tab + 抽屉导航（Mantine AppShell）——这是 Streamlit 做不到
  而手机场景（总体方案 §6）需要的。
- 可达性：Mantine 组件自带 ARIA；键盘导航进 parity checklist。

## 7. 测试策略

| 层 | 内容 |
|----|------|
| 契约 | OpenAPI schema 快照（CI）；`httpx.ASGITransport` 端点测试随 API 增长 |
| 单元 | 核心 hooks/stores 用 vitest；策 B 拆出的 packages/ 沿用各组件已有 `node --test` |
| E2E | 现有 15 个 Playwright spec 逐页移植/重写（sidecar 独立页的 spec 几乎可直接复用；测 Streamlit UI 的需重写）；每页迁移完成 = 对应 spec 全绿 |
| Parity checklist | 每页一份功能矩阵（字段级）：增删改查、校验、冲突处理、深链、i18n、移动端断点；全绿才可宣布该页完成 |
| 视觉回归 | 可选：Playwright screenshot 对比（M2 起对看板/仪表盘启用） |

## 8. 工作量与排期（1 人全栈粗估）

M0 3–5 天；M1 8–10 天；M2 8–10 天；M3 8–10 天；M4 12–15 天；M5 3–5 天。
**合计 42–55 个工作日**（约 2.5–3 个月），与总体方案 L0–L4（约 4 周）并行，
总窗口约 3–4 个月。人力若加 1 名前端，M2–M4 可压缩约 40%。

诚实声明：36k 行渲染层的迁移不可能"没 bug"；本方案的控制手段是
**双轨运行 + 页面级 parity 门 + e2e 绿灯才切流**，Streamlit 在观察期内
随时可切回（Caddy 改一条路由的事）。

## 9. 风险

| 风险 | 缓解 |
|------|------|
| 双轨期两前端功能漂移 | 迁移期内新功能默认只进 SPA；Streamlit 冻结新特性（bugfix 除外），并在其首页明示 |
| Output Studio 7080 行重写失控 | M4 再拆子里程碑：配置编辑 → 站点预览 → 博客编辑器；BlockNote 组件是现成的最大保底 |
| 组件拆库破坏 Streamlit 侧 | 策 B 的 wrapper 保持原 Python 签名不变；组件已有 e2e spec 护航 |
| 认证回归 | M0/M1 即覆盖：cookie 12h 过期、登出、`NBLANE_AUTH_FILE` 关闭时的 synthetic admin 路径都进契约测试 |
| SSE/WS 经 Caddy 长连接被掐 | M0 spike 即验证 SSE 经 Caddy 的稳定性（flush/超时配置）；reader 现有 SSE 已是证据 |
