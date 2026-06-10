# Blog 写作发布迁移到 18502 式独立页面 —— 实施计划

## 核心发现（决定了整个方案的形态）

1. **blog 编辑器已经是一个完整的 React 应用**：`src/nblane/public_blog_editor_component/frontend/`
   里已经有 `library/`（列表/分类/媒体树）、`ai/`（AI 候选）、`blocks/`（BlockNote 块）。
   它**不是只有正文框**，整个 blog tab 的交互几乎都在 React 里。
2. **它和 Streamlit 是 props-in / events-out 通信，零 `fetch`**。React 把用户操作打成
   ~40 种 `{action, payload}` 事件（白名单见 `web_output_studio.py:2005-2042`，schema 见
   `schemas/editor_events.py`），Streamlit 收到后调用 `public_site.py` 的纯函数完成持久化。
3. **dashboard 组件已经验证了 dual-mode 模式**：同一份构建产物，既能作为 Streamlit 组件嵌入，
   也能作为 8502/18502 上的独立页面运行 —— 靠 `window.__NBLANE_DASHBOARD_STANDALONE__` 注入配置，
   见 `dashboard.html` 模板 + `home_dashboard/main.jsx:199 standaloneConfig()`。

**结论**：整个 blog tab 搬到 18502 = ①给 React app 加 standalone 引导分支（fetch 替代 Streamlit 桥），
②在 Reader API 把那 ~40 个事件包成 REST 端点（内部仍调现有 `public_site.py` 函数）。
后端业务逻辑基本不重写，主要是搭接口和前端引导。

---

## 阶段 0 ——「一键发布」（与 UI 形态无关，最先做，最快见效）

**痛点**：发布 = 改 frontmatter status → 手动 `nblane public build` → 手动部署。

注意：仓库当前**没有**任何部署目标实现（无 rsync/gh-pages/vercel 等），`dist/public/<profile>/` 是终点。
所以「一键」第一版定义为 **publish + build 合一**，部署目标作为可配置钩子留接口。

### 0.1 Reader API 新增端点
文件：`src/nblane/web_reader_api/__init__.py`
- `POST /api/blog/{profile}/publish` —— 调 `publish_blog_text(...)`（含发布前校验
  `validate_blog_text_for_publish`），返回校验结果 + 新 status。
- `POST /api/site/{profile}/build` —— 调 `build_public_site(name, include_drafts=...)`，
  返回 `PublicBuildResult`（页数、产物路径、warnings）。
- （可选）`POST /api/site/{profile}/deploy` —— 读取 profile 里的 `deploy_target` 配置；
  无配置时返回「未配置部署目标」而非报错。第一版可仅占位。
- 鉴权/CORS 复用现有 `_request_context` + `paper_library_embed_cors` 中间件，profile 目录
  解析复用 `_paper_library_profile_dir` 同款校验。

### 0.2 Streamlit 侧接一个按钮（立刻可用，不等前端迁移）
文件：`pages/10_Public_Build.py`（目前几乎是空壳）
- 加「发布并构建」按钮，串 `publish_blog_text` → `build_public_site`，展示校验/构建结果。
- 这步让「发布繁琐」痛点在阶段 1/2 之前就被解决。

**阶段 0 验收**：一个动作完成 publish→build，校验失败时清楚展示阻塞原因。

---

## 阶段 1 —— 正文编辑器独立成 18502 全屏页（消灭「写作手感差」）

复刻 dashboard 的 dual-mode 套路，让现有 React app 能脱离 Streamlit iframe 跑。

### 1.1 后端：模板 + 引导路由
文件：`src/nblane/web_reader_api/`
- 新增模板 `templates/blog_editor.html`（仿 `dashboard.html`）：注入
  `window.__NBLANE_BLOG_STANDALONE__ = { profile, slug, apiBase, streamlitBase }`。
- 新增路由 `GET /blog-editor`（仿 `paper_library_view`），用 `_blog_editor_assets()`
  扫描构建产物（仿 `_home_dashboard_assets`，资产目录指向
  `public_blog_editor_component/frontend/static/assets`）。
- 新增静态资产路由 `GET /blog-editor/assets/{file_name}`（仿 `dashboard_asset`）。

### 1.2 后端：把事件契约包成 REST（核心工作量）
在 Reader API 实现一组端点，覆盖编辑器**编辑态**所需的事件，内部调用 `public_site.py`：
- `GET  /api/blog/{profile}/posts` —— `load_blog_posts`（列表 + 分类树 + 媒体）
- `GET  /api/blog/{profile}/posts/{slug}` —— `load_blog_post`（正文 + blocks + meta）
- `PUT  /api/blog/{profile}/posts/{slug}` —— `save_blog_post`（save_post 事件）
- `POST /api/blog/{profile}/posts` —— `create_blog_draft_in_library`（create_post）
- `POST /api/blog/{profile}/posts/{slug}/check` —— `validate_blog_text_for_publish`（run_check）
- `POST /api/blog/{profile}/posts/{slug}/publish` —— 复用阶段 0 端点
- `POST /api/blog/{profile}/media` —— 媒体上传（upload_media / library_upload_media）
- AI 相关（generate_ai_candidate / ai_inline_action / ai_stream_poll …）——
  复用 paper-library 已有的**异步 job + SSE**模式（`.../search/jobs` + `/stream`），
  保证长任务不阻塞、可取消。
- **建议**：抽一个 `blog_event_dispatch(profile, event) -> result` 纯函数，让 Streamlit
  和 Reader API **共用同一套事件→`public_site.py`** 的映射，避免两份分发逻辑漂移。
  这是降低长期维护成本的关键一步。

### 1.3 前端：standalone 引导分支
文件：`src/nblane/public_blog_editor_component/frontend/src/main.jsx`
- 当前结尾是 `Streamlit.setComponentReady()` + RENDER 事件桥（`main.jsx:6678`）。
- 仿 dashboard 加 `standaloneConfig()` 分支：检测到 `window.__NBLANE_BLOG_STANDALONE__`
  时，用 `fetch` 拉初始数据、把 events 走 REST，而非 `Streamlit.setComponentValue`。
- 抽一个 `transport` 层（streamlit / http 两种实现），React 组件本身不感知运行宿主。

### 1.4 Streamlit 接入口
文件：`src/nblane/web_output_studio.py`
- blog tab 的文章项加「在新窗口编辑」按钮，跳转
  `${reader_base}/blog-editor?profile=...&slug=...`（reader_base 已有
  `NBLANE_READER_API_BASE` env，见 `web-ui.md`）。

**阶段 1 验收**：在 18502 独立页打开一篇文章，自动保存/滚动/快捷键顺滑，保存/发布回写正确。

---

## 阶段 2 —— 列表/分类/媒体库/AI/来源链全部迁入同一 SPA（达成「整个 blog tab 都搬」）

React app 本来就含这些模块，主要是把剩余事件接到 REST + 在 standalone 下渲染完整外壳。
- 补齐剩余事件端点：library_*（folder/move/reorder/trash/restore/purge）、
  draft_from_evidence / draft_from_done、visual/cover 生成、preview_post 等。
  全部复用 `public_site.py` + `create_blog_draft_in_library` 等现有函数。
- standalone 模式渲染完整 blog 外壳（列表 + 编辑 + 媒体 + 发布），路由用 query/hash。
- 逐块迁移：搬一块 → 删 `web_output_studio.py` 里对应的 Streamlit 块 → 验证。
- 终态：`pages/6_Output_Studio.py` 的 blog tab 仅保留一个「打开 Blog 工作台」入口。

**阶段 2 验收**：blog 全流程在 18502 完成，Streamlit 仅剩跳转入口；旧的 iframe 嵌入路径移除。

---

## 端口/部署衔接
- 复用现有约定：生产 8502/8503，同机隔离开发 18502/18503（`scripts/dev-web.sh`、`web-ui.md`）。
- `dev-web.sh` 已转发 reader 端口，新页面自动可达，无需改启动脚本。
- 新增前端资产需 `cd .../public_blog_editor_component/frontend && npm run build`（vite），
  产物落到 `frontend/static/assets`，Reader API 自动扫描。

## 风险与缓解
- **事件契约漂移**（最大风险）：用 1.2 的共享 `blog_event_dispatch` + 现有
  `schemas/editor_events.py` 校验，前后端单一事实源。
- **增量可用**：每阶段都留有可工作版本，Streamlit 旧路径在阶段 2 完成前不删除。
- **AI 长任务**：直接复用 paper-library 验证过的 job+SSE 框架，不另起炉灶。
- **鉴权**：所有新端点走现有 `_request_context` / reader-token，禁止裸开放。

## 建议起点
先做**阶段 0**（一键发布，独立见效、零前端依赖），再做**阶段 1**（编辑器独立 + 共享事件分发层），
阶段 2 在 1 的接口基础上纯增量铺开。
