---
status: active
owner: 王军
last_verified: 2026-10-07
source_of_truth: src/nblane/web_ui/、src/nblane/web_api/、src/nblane/web_reader_api/、tests/e2e/
---

# SPA 现状总账

Streamlit 已退役（ad87958，2026-10-06）。React SPA 是唯一 Web 界面，由 `nblane.web_api` 在 8504 同进程服务；论文库与阅读器留在 Reader API（8502），SPA 用 iframe 嵌入。本文记录 SPA 的技术栈、工程约定和页面现状；功能用法见 [Web 总览](../guides/web-ui.md)，进程与鉴权见 [架构总览](overview.md)。

## 技术栈

- 前端：`src/nblane/web_ui/frontend`，Vite + React 18 + TypeScript + Mantine 8 + TanStack Query + React Router；BlockNote（内容工作台）、three.js + troika（首页星图）、mermaid / KaTeX（渲染）。
- 主题：`src/theme.ts`，深色锁定。设计约定见 [设计语言](../product/design-language.md)。
- 后端：FastAPI `nblane.web_api:app`，`/api/v1/*` + SPA 静态资源，单进程 `--workers 1`。
- 认证：httpOnly cookie `nblane_auth_session`（复用 `core/auth.py` HMAC）；未配置 `NBLANE_AUTH_FILE` 时为合成本地管理员。
- 并发：GET 带 ETag（文件指纹），写请求带 `If-Match`，冲突 412；看板三方合并。
- 长任务：`POST /profiles/{name}/jobs` 202 + `jobs/{id}/stream` SSE，不做前端轮询。

## 工程约定

| 项 | 约定 |
|----|------|
| 构建产物 | `npm run build` 输出到 `src/nblane/web_ui/static/`，提交进 git，并在 `pyproject.toml` package-data 声明；安装后无需 Node 即可服务 |
| 产物新鲜度 | CI `frontend-artifacts` job 重建 SPA 与组件前端并比对，过期即红 |
| API 契约 | `scripts/dump-openapi.sh` 生成 `openapi.json` 快照；`npm run gen:api` 生成 `src/api/schema.d.ts`（不手改）；页面只从 `src/api/types.ts` 引类型；`tests/test_web_api_openapi_snapshot.py` 守护漂移 |
| 本地开发 | `npm run dev`（5173，`/api` 代理到 8511，可用 `VITE_API_PROXY_TARGET` 改） |
| 测试 | 单元：vitest + testing-library（`npm run test`）；端点：`httpx.ASGITransport` 直打 app；E2E：Playwright，SPA 用例默认指向 isolated 18504 |
| Agent 写入 | 新写端点在 `web_api/agent_guard.py` 登记动作分级 |

## 页面现状

| 区域 | 路由 | 现状 |
|------|------|------|
| 档案列表 / 登录 | `/`、`/login` | 已完成 |
| 首页 | `/p/:name/home` | 全屏星图、星表（含目标管理）、占卜、习惯印、铭文卡 |
| 项目 | `/p/:name/projects` | 看板 + 项目板合并；`view=kanban\|timeline\|story`，`group=goal\|activity`；习惯阶段计划、Someday |
| 技能树 | `/p/:name/skill-tree` | 已完成 |
| 证据 | `/p/:name/evidence` | 五阶段（含审阅队列、待补强）、结晶 |
| 研究台 | `/p/:name/research/*` | 概览、`library` 论文库（iframe）、`papers/:id` 概览、`papers/:id/read` 阅读器（iframe）、`sources` |
| 内容工作台 | `/p/:name/content/*` | BlockNote 编辑器 |
| 求职工作台 | `/p/:name/career/*` | 简历、目标岗位、导入简历、JD 定制 |
| 公开站点 | `/p/:name/public-build` | 构建、预览、发布 |
| 车间 | `/workshop` | xterm 网页终端，经 `/terminal/*` 认证反代 ttyd |
| 助手 | `/assistant` | OpenClaw 状态、接入方式、撤销日志 |
| 设置 | `/settings/:section` | 系统级：AI 服务、本地服务、车间终端、助手与备份；档案级：通用、研究与阅读、AI 路由 |

旧路由重定向：`health`、`evidence-review` → 证据；`kanban`、`project-board` → 项目；`goals` → 首页；旧 Streamlit URL（`/Skill_Tree`、`/pages/*.py`）由 `LegacyStreamlitRedirect` 处理。

## 已移除

Team、Gap Analysis、Agent Activity 审批页、Inbox 页、Studio 页不再出现在导航里。`ActivityPage`、`InboxPage`、`StudioPage` 的路由和代码仍在，待删。

## 收尾待办

- 删除 Streamlit 遗留代码与依赖（清单见 [模块地图](module-map.md#待删遗留)）。删前要先迁走 Reader API 对 `web_i18n.py`、`research_paper_reader_component.events`、`paper_library_component` 产物的引用，并替换 CI import smoke 里的 `kanban_ui`。
- 删除上述孤儿页面的路由、页面、测试和仅供它们使用的 API。
- E2E 中只测 Streamlit 的用例（默认 base URL 仍为 18503）随之删除或改指 SPA。
- 缺口与优先级以 [当前状态](../project/status.md) 为准。
