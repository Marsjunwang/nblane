# nblane Web UI(SPA 迁移)

新一代单页应用(SPA)前端,用于替代 Streamlit 界面。技术栈:Vite + React 18 +
TypeScript + Mantine 8 + TanStack Query + React Router。对应设计文档:
`docs/zh/architecture/frontend-spa-migration.md` §2。

后端是已落地的 FastAPI 应用 `nblane.web_api:app`(cookie 会话认证)。

## 本地开发

```bash
# 1. 启动 API 后端(仓库根目录,任选端口,默认代理指向 8511)
.venv/bin/uvicorn nblane.web_api:app --port 8511

# 2. 启动前端开发服务器
cd src/nblane/web_ui/frontend
npm install
npm run dev        # http://127.0.0.1:5173,/api 自动代理到 8511
```

- 代理目标可通过环境变量覆盖:`VITE_API_PROXY_TARGET=http://127.0.0.1:9000 npm run dev`
- 未设置 `NBLANE_AUTH_FILE` 时后端认证关闭,`/auth/me` 返回
  `auth_enabled=false` 的合成管理员,前端会跳过登录页;设置了认证文件则
  出现登录墙(cookie:`nblane_auth_session`)。

## 构建与打包

```bash
npm run build      # tsc 类型检查 + Vite 构建,输出到 ../static(带哈希资产)
npm run test       # vitest + testing-library 冒烟测试
npm run preview    # 本地预览构建产物
```

**打包决策(已定)**:`../static`(即 `src/nblane/web_ui/static/`)的构建产物
**提交进 git**,并在 `pyproject.toml` `[tool.setuptools.package-data]` 中声明
(`nblane.web_ui` = `static/index.html` + `static/assets/*`)——与各
`*_component` 前端同一惯例。`nblane.web_api.spa.mount_spa` 以 `__file__`
相对路径定位该目录,因此 `pip install -e .` 与 wheel 安装后均无需 Node 即可
服务 SPA。改前端代码后必须重新 `npm run build` 并连同 `static/` 一起提交;
CI 的 `frontend-artifacts` job 会重建并比对,产物过期即红。

## 当前进度

- 应用外壳:Mantine AppShell,头部含应用名、当前档案指示、退出登录按钮。
- 路由:`/login` 登录页(401 显示后端错误)、`/` 档案卡片列表、
  `/p/:name/health` 健康检查页(严重级别徽章 + 按类别分组的问题)、404 页;
  `RequireAuth` 守卫在 `/auth/me` 返回 401 时跳转登录页。
- API 层:`src/api/client.ts`(fetch 封装,`credentials: 'include'`,统一
  `ApiError`,兼容 `{code,message}` 与 `{detail}` 两种错误体)、
  `src/api/types.ts`(类型别名层)、`src/api/hooks.ts`(TanStack Query)。
- 主题:品牌主色 `#21685b`,默认亮色。
- 测试:client 错误映射、登录表单渲染、健康页渲染(mock fetch)。

## API 类型生成(Immich 模式 OpenAPI codegen)

前端 API 类型由后端 OpenAPI 契约生成,不再手写:

- `openapi.json` — **已提交**的契约快照(仓库根 `scripts/dump-openapi.sh`
  生成,`sort_keys` 保证 diff 稳定)。CI 中
  `tests/test_web_api_openapi_snapshot.py` 会比对快照与实时 app schema,
  漂移即红。
- `src/api/schema.d.ts` — `openapi-typescript`(v7)从快照生成的原始类型,
  已提交,不要手改。
- `src/api/types.ts` — 稳定导出面:对 `schema.d.ts` 组件类型的别名
  (如 `ActivityItem = components['schemas']['ActivityItemModel']`),
  外加少量纯前端复合类型(ETag 包装、clarify 动作枚举)。页面/hooks 只
  从这里 import。

后端契约变更后的再生成流程:

```bash
scripts/dump-openapi.sh                          # 1. 更新契约快照(仓库根)
cd src/nblane/web_ui/frontend
npm run gen:api                                  # 2. 重新生成 schema.d.ts
npm run test && npm run build                    # 3. 类型漂移会在 tsc 暴露
```

## 待办 / 开放问题

- **页面覆盖**:16 个页面已实现——登录、档案列表,以及 profile 下的
  health、activity、kanban、inbox、skill-tree、gap(规则版)、goals、
  evidence、evidence-review、review、project-board、studio、research、
  home、assistant。逐里程碑进度与剩余子切片(Public Build、Studio 站点
  预览/博客编辑器、Home 目标编辑器/命令条等)见
  `docs/zh/architecture/frontend-spa-migration.md` 实施进度表。
