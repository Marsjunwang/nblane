---
status: active
owner: engineering
last_verified: 2026-10-07
source_of_truth: true
---

# 架构总览

nblane 是文件优先的单人系统：两个 FastAPI 进程读写 `profiles/<name>/` 下的 YAML / Markdown，React SPA 是唯一 Web 界面，CLI 和 Agent 共用同一套 `core/` 逻辑。没有数据库，Git 负责备份。

## 进程与端口

```text
浏览器 / 手机                    个人助手 OpenClaw（18789）
   │ HTTPS                          │ HTTP + 服务账号（nblane_api.py）
   ▼                                ▼
Caddy ─────────────────────────────────────────────
   │ 默认路由                        │ /reader/* /paper-library* /api/research/* /auth/*
   ▼                                ▼
web_api :8504                   web_reader_api :8502
  SPA 静态产物 + /api/v1/*         论文库、阅读器（SPA iframe 嵌入）
  /terminal/*（车间 ttyd 代理）     /auth/session 登录态交接
   │                                │
   └──────────────┬─────────────────┘
                  ▼
           src/nblane/core/
                  ▼
   NBLANE_ROOT：profiles/  schemas/  auth/users.yaml
                  ▼
           git_backup → 私有远端

本机：nblane CLI、nblane-mcp（stdio，只给 Cursor / Claude Code）直接调用 core/
可选：GROBID :8070（Podman）、本地翻译 llama-server、ttyd
```

| 进程 | 入口 | 端口（dev / isolated） | 职责 |
|------|------|------------------------|------|
| SPA 后端 | `nblane.web_api:app` | 8504 / 18504 | 单进程同时出 SPA（`web_api/spa.py`）与 `/api/v1/*`；jobs + SSE 长任务；Agent 写入守卫 |
| Reader API | `nblane.web_reader_api:app` | 8502 / 18502 | 论文库、PDF 阅读器、阅读器内 AI 任务、`/auth/session` |
| CLI | `nblane.cli:main` | — | init、validate、sync、context、evidence、ingest、public、openclaw、backup 等 |
| MCP | `nblane.mcp_server:main` | stdio | 本机编辑器接入；无登录、无 ACL，暂停扩展 |

两个 uvicorn 都以 `--workers 1` 运行：jobs、确认码、缓存都在进程内存里。开发用 `scripts/dev-web.sh` 在 tmux 里起两者；生产是 systemd `nblane-web-api.service` 与 `nblane-reader.service`，端口只绑 `127.0.0.1`，由 Caddy 对外。

## 请求链路

一次 SPA 写请求：

```text
SPA (TanStack Query, fetch credentials: include)
  → /api/v1/profiles/{name}/...        带 If-Match（ETag = 文件 sha256 指纹）
  → GitActorMiddleware                 本次请求的 git 提交 actor = 当前用户
  → agent_write_guard                  人类账号直接放行
  → require_profile_access             profile 作用域，先于 404
  → routes_v1 handler → core/*         file_lock 加锁、锁内复核快照、atomic write
  → git_backup.record_change           NBLANE_DATA_GIT_AUTOCOMMIT / AUTOPUSH
  ← 200 新 ETag | 412 冲突 | 422 校验失败 {code, message}
```

- 冲突语义：快照不一致返回 412，前端提示重新加载；看板走三方合并（见 [数据契约](data-contracts.md)）。
- 长任务（LLM 分析、结晶草稿、JD 定制等）：`POST /profiles/{name}/jobs` 返回 202，`jobs/{id}/stream` 推 SSE 进度。
- 论文库与阅读器：SPA 路由 `research/library`、`papers/:id/read` 用 iframe 嵌 8502 页面。鉴权开启时，`GET /research` 返回短时 handoff token，iframe 先经 `/auth/session` 换取 Reader 会话 cookie。`NBLANE_READER_API_BASE=0` 表示同源（Caddy 分流），否则填浏览器可达的 8502 地址。
- API 契约：pydantic 模型 → OpenAPI 快照 `web_ui/frontend/openapi.json` → `npm run gen:api` 生成 TS 类型；CI 比对快照漂移。

## 鉴权与身份

- 未设置 `NBLANE_AUTH_FILE`：关闭登录，所有请求以合成本地管理员运行（单机自用）。
- 设置后读取 `auth/users.yaml`（按文件 mtime 缓存），浏览器登录拿 httpOnly cookie `nblane_auth_session`（HMAC 签名，登录限流）。
- 会话令牌带用户的 `session_version`。改密码、重置密码、停用、「登出所有设备」都会把版本号加一，旧会话随即失效；停用账号的任何会话和 token 都被拒绝。
- 机器访问用 API token `nbl_<id>_<secret>`，`Authorization: Bearer` 传递，`users.yaml` 只存 sha256，可单独撤销。
- `users.yaml` 只经 `core/auth_store.py` 写（加锁、原子写、保持 0600），写入时不自动提交；每日备份把它提交进私有数据仓库。
- 身份只有三类：

| 身份 | users.yaml | 能力 |
|------|------------|------|
| 管理员 | `role: admin` | 所有 profile；系统级设置（AI 服务、本地服务、车间、助手与备份） |
| 本人 | `role: member`，`profile` / `profiles` | 只访问自己的 profile |
| 助手服务账号 | `role: member` + `agent: true` | 同本人的 profile 范围，写入受 Agent 策略约束 |

旧部署里 id 为 `openclaw` 的账号也按 Agent 处理（`agent_policy.LEGACY_AGENT_ID`）。

## Agent 写入守卫

`create_app` 给所有路由挂一个应用级依赖 `web_api/agent_guard.py::agent_write_guard`，只对 Agent 账号的写请求生效：

1. 路由模板 + 方法映射为动作（`ROUTE_ACTIONS`）；未映射的 profile 路由按 T2，系统 / 设置 / 权限前缀按 T3。
2. 动作分级查 `core/agent_policy.py`：T0 只读放行；T1 直写；T2 需聊天确认；T3 返回 403 `agent_forbidden`。
3. T2 首次请求返回 428 + `confirm_id` 和人话摘要；助手转述，用户同意后带 `X-Nblane-Confirm` 重发同一请求。确认码一次性、10 分钟有效、绑定调用者与 method + path + body 指纹。
4. T1 / T2 执行前后对相关实体做快照，diff 写入 `agent-journal.yaml`（`core/agent_journal.py`），可在助手页撤销；没有实际变化的请求不留记录并退还确认码。

共享流程在 `core/agent_ops.py`，MCP 也复用它。分级细节和用户侧说明见 [个人助手](../guides/assistant.md)；撤销日志语义见 [数据契约](data-contracts.md#agent-journal-撤销日志)。

## 核心层

`src/nblane/core/` 与 UI 无关，按领域一个模块。所有 profile 文件读写走 `*_io.py`、`file_write.py`（原子写）、`file_lock.py`（flock 边车锁）、`file_state.py`（快照比对）。写入顺序固定为 pool → tree → validate → sync。模块清单见 [模块地图](module-map.md)，AI 调用见 [AI 架构](ai-architecture.md)。

## 生产布局与备份

| 位置 | 角色 |
|------|------|
| `/srv/nblane-data` | 唯一数据根（`NBLANE_ROOT`）：profiles、schemas、auth、`.env`；私有 git，每次写入自动提交 |
| `/srv/nblane-app/nblane` | 生产代码，只读部署 |
| `/srv/agent-data/openclaw/workspace` | 助手 workspace（情景记忆），独立私有 git；`~/.openclaw/workspace` 为软链 |
| `/home/ubuntu/nblane` | 开发仓库；只跑 `dev-web.sh --isolated`（`.dev-data/`），不写真实 profile |

备份统一、仓库不统一：设置 → 助手与备份管理两个仓库的私有远端，每日 03:30 由 `nblane-backup.timer` 推送（`core/backup_targets.py`）。nblane 数据仓只推送（应用已逐次提交），助手 workspace 先 `git add -A` 再推。新代码解析助手 workspace 用 `openclaw config get agents.defaults.workspace`，不写死路径。

部署细节见 [腾讯云部署](../guides/deployment-tencent-cloud.md)，搬机见 [整机迁移](../guides/migration.md)。

## 架构规则

- 文件优先，不引入数据库；存储边界见 [存储](storage.md)。
- `core/` 不依赖 Web 框架；路由只做鉴权、校验、序列化。
- 新的写端点必须在 `agent_guard.ROUTE_ACTIONS` 登记动作，否则 Agent 调用默认需要确认。
- 公开产物默认私有，发布只在 Web 端由人触发（T3）。
- 密钥不进仓库、不进 `profiles/`；Web 偏好文件不存 key / token。
