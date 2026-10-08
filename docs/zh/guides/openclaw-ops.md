---
status: active
owner: 王军
last_verified: 2026-10-08
source_of_truth: false
---

# OpenClaw 运维

本文写给维护服务器的人：OpenClaw 网关怎么装、怎么接 nblane、怎么升级和排障。使用者视角（助手页、三类写入、撤销、备份）见 [助手](assistant.md)。事实以 `src/nblane/core/openclaw_*.py`、`src/nblane/commands/openclaw.py` 和 `scripts/openclaw/` 为准。

## 分工

- OpenClaw：常驻网关、微信通道、模型路由、定时任务、自己的情景记忆（`USER.md`、`MEMORY.md`、daily notes）。
- nblane：成长档案。助手只通过 HTTP（`skills/bin/nblane_api` → `http://127.0.0.1:8504/api/v1`）读写，以 `openclaw` 服务账号登录，按账号权限和 `core/agent_policy.py` 检查。
- nblane 不给 OpenClaw 注册 MCP。「接入 nblane」发现旧的 `mcp.servers.nblane` 时会执行 `openclaw mcp unset nblane`。原因：本机 MCP 无登录无 ACL；且 OpenClaw 每开一个会话就起一个 `nblane-mcp`，默认不回收，心跳每小时一次会让进程一直累积。

## 前置条件

| 项 | 要求 |
|----|------|
| 系统 | Linux x64 / ARM64，glibc（Ubuntu 22.04 / 24.04 已用） |
| Node.js | `>=24.16.0 <25` 或 `>=26.1.0`（`node:sqlite` 要求）。22、23、25 不行 |
| 运行用户 | 普通用户，拥有 `~/.openclaw`。不要先用 root 装一遍 |
| linger | 无头主机必须 `sudo loginctl enable-linger "$USER"`，否则 SSH 断开后用户服务停止 |
| 端口 | 网关 `127.0.0.1:18789`，不对公网开放 |
| 内存 | 官方最低约 1 GB；本仓库路径（微信长连 + 模型会话 + 可选 Codex/Kimi 委派）建议 3 GB 以上 |
| 出站 | npm registry、模型供应商、微信插件后端 `https://ilinkai.weixin.qq.com` |
| 时区 | 建议 `Asia/Shanghai`，心跳 activeHours 和定时任务按它解释 |

不需要公网入站、回调 URL、数据库或 Docker。

`nblane openclaw doctor` 会检查 Node 版本、linger 和网关端口，见下文。

## 安装与接入

推荐在 SPA「设置 → 系统 → 助手与备份」点「一键安装 OpenClaw」，它会：

1. `npm install -g openclaw@<固定版本>`（用户目录，无 sudo）。固定版本见 `core/openclaw_setup.py` 的 `PINNED_VERSION`，可用 `NBLANE_OPENCLAW_VERSION` 覆盖。
2. `openclaw onboard --non-interactive`：网关绑 loopback、端口 18789、装 systemd 用户服务、工作区直接放 `/srv/agent-data/openclaw/workspace`。复用 nblane AI 连接时，Key 经子进程环境变量 `CUSTOM_API_KEY` 传入，不上命令行。
3. 自动执行「接入 nblane」：
   - 工作区 `git init` 并写 `.gitignore`。
   - 同步 `scripts/openclaw/skills/` 到工作区 `skills/`，生成 `skills/bin/nblane_api`（用 nblane 自己的 Python，不建技能 venv）。
   - 移除旧的 nblane MCP 注册；记录接入的 `NBLANE_ROOT`。
   - 渲染只读档案语料到工作区 `memory/nblane/`（`skill-tree.md`、`goals.md`、`kanban.md`、`profile-summary.md`），并加进 `memory.search.extraPaths`。
   - 已装微信插件但没装 weixin-task-bridge 时顺带装上。

命令行等价（在代码仓根目录，以运行网关的用户执行）：

```bash
nblane openclaw install --profile <name>          # 默认 dry-run，只打印计划
nblane openclaw install --profile <name> --apply  # 技能+语料、weixin-task-bridge 插件、配置 overlay
nblane openclaw doctor --profile <name>
```

`install` 三步：技能与语料（同 `sync`）；`openclaw plugins install scripts/openclaw/plugins/weixin-task-bridge --force --accept-capabilities`；profile 有 `assistant/openclaw.overlay.json5` 时经 `openclaw config patch --stdin` 应用（`${VAR}` 从环境替换，未设置即报错）。不碰定时任务，不注入 MCP。

`scripts/openclaw/install.sh` 是更早的手工脚本，会在 `skills/.venv` 建 venv。新装请用设置页或 `nblane openclaw install`；残留的 `skills/.venv` 会让 `openclaw backup create` 失败（venv 里有绝对路径软链）。

## 工作区布局

```text
/srv/agent-data/openclaw/workspace   OpenClaw 工作区（独立私有 git，每日快照）
  skills/nblane/SKILL.md             调用规则（唯一来源，从仓库同步）
  skills/bin/nblane_api              接入时生成的包装脚本
  skills/codex-dev/ kimi-dev/        本机 Codex / Kimi 委派技能
  memory/nblane/                     只读档案语料（生成物，勿手改）
~/.openclaw/workspace                指向上面的软链接
~/.openclaw/openclaw.json            网关配置（含 token、模型 key，不进任何仓库）
/srv/backups/agents/                 迁移前的整目录 tar 包（0600）
```

工作区不在 `/srv/agent-data` 时，设置页提供「迁移到统一数据目录」：先 tar 整个状态目录，停网关、移动、旧路径留软链、改配置、起网关，失败自动回滚。迁移任务跑在 8504 进程的后台线程里，服务重启会中断任务，此时按 `/srv/backups/agents/` 的 tar 包手工恢复。

接入记录的数据目录和当前 nblane 不一致时（例如开发环境连上了生产网关），卡片只读，接入、迁移、网关操作一律拒绝。

## 技能与语料同步

```bash
nblane openclaw sync [--profile <name>]           # 渲染语料 + 同步技能
nblane openclaw sync [--profile <name>] --check   # 只对账，有漂移退出码 1
```

- 技能同步会删除仓库里已经不存在的文件，但只在 nblane 纳管的顶层目录（`nblane/`、`codex-dev/`、`kimi-dev/`、`bin/`）内；其他技能树不碰。`bin/nblane_api` 是生成物，不算多余文件。
- 语料只删带生成头标记的旧文件，用户文件不动。
- 改了 `scripts/openclaw/skills/nblane/SKILL.md` 后跑一次 `sync`，或在设置页点「接入 nblane」。助手页「接入方式」会显示是否最新。
- 更新技能不需要重启网关；新建会话即可生效。

## 服务账号凭据

`nblane_api` 以 `openclaw` 服务账号访问 8504，优先用 API token：

1. `NBLANE_OPENCLAW_API_TOKEN`（推荐）：形如 `nbl_…`。每个请求带 `Authorization: Bearer`，不登录、不缓存 cookie；被撤销后请求直接失败，不会退回密码。
2. `NBLANE_OPENCLAW_API_PASSWORD`：没有 token 时用密码登录，会话 cookie 缓存在 `~/.cache/nblane/api-cookies.json`，过期后自动重登一次。

两者都按同样顺序读取：先环境变量，再 `api.env`（0600）。文件路径依次取 `NBLANE_OPENCLAW_API_ENV_FILE`、`$XDG_CONFIG_HOME/nblane/api.env`、`~/.config/nblane/api.env`。定时任务的沙箱不继承网关进程环境时靠这个文件。

### 一键配置（推荐）

「设置 → 助手与备份」的「服务账号凭据」卡片显示账号、token 状态（已配置 / 未配置 / 已失效 / 账号未标记为助手）和文件路径。点「生成并配置 token」，服务端会：

1. 给服务账号（`NBLANE_OPENCLAW_API_USERNAME`，默认 `openclaw`）生成名为 `assistant (auto)` 的 token；
2. 写进 `api.env`：只替换或追加 `NBLANE_OPENCLAW_API_TOKEN=` 这一行，密码行和注释原样保留；目录 0700、文件 0600、原子写入；
3. 重新读文件并校验 token 能认证到该账号。校验失败就恢复原文件、作废新 token，旧 token 继续可用。

nblane 服务和 OpenClaw 以同一个系统用户运行，所以明文只在服务端落盘，不经过浏览器。已配置时按钮变成「轮换 token」：新 token 校验通过后，自动撤销文件里原来那个 token（只撤销它，手动生成的其它 token 不动）。助手下一次调用就用新 token，不用重启网关。

前提：已开启登录（`NBLANE_AUTH_FILE`），账号存在且是助手账号。只能用管理员网页会话操作，助手账号自己调用会被 403 拒绝。

### 手动配置

在「设置 → 账号管理」助手账号那一行生成 token（明文只显示一次），再写入文件：

```bash
install -d -m 700 ~/.config/nblane
printf 'NBLANE_OPENCLAW_API_TOKEN=<nbl_…>\n' > ~/.config/nblane/api.env
chmod 600 ~/.config/nblane/api.env
```

也可以给网关进程用用户级 drop-in 注入：

```ini
# ~/.config/systemd/user/openclaw-gateway.service.d/nblane-api.conf
[Service]
Environment=NBLANE_OPENCLAW_API_TOKEN=<nbl_…>
```

改 drop-in 后 `systemctl --user daemon-reload && systemctl --user restart openclaw-gateway`；只改 `api.env` 不用重启。

手动换 token：先生成新的、写进 `api.env`、用 `nblane_api summary` 验证，再撤销旧的。注意：环境变量（如上面的 drop-in）优先于文件，用了 drop-in 时一键配置写的文件不会生效。

`users.yaml` 里该账号是 `member`、只授权本人档案，写 `agent: true`。`NBLANE_API_BASE` 可改 API 地址。

## 网关与 systemd

网关是用户级服务 `openclaw-gateway.service`。

```bash
systemctl --user status openclaw-gateway.service --no-pager
systemctl --user cat openclaw-gateway.service      # 看 PATH 和 ExecStart
journalctl --user -u openclaw-gateway -f
curl -fsS http://127.0.0.1:18789/readyz
openclaw gateway restart
openclaw gateway stop --force                      # 非交互停止要 --force
```

- unit 的 `PATH` 必须包含 `openclaw`、`codex`、`kimi` 所在目录（常见 `~/.local/npm-global/bin`、`~/.local/bin`）。只改 `~/.bashrc` 无效。
- SPA 后端 `nblane-web-api.service` 也要能找到 `openclaw`，否则助手页显示「本机未安装」。写法见 [部署](deployment-tencent-cloud.md#spa-后端8504)。
- 控制台：本机用 `ssh -L 18789:127.0.0.1:18789`；公网走 Caddy `/openclaw` 子路径（新标签打开，不能 iframe）。Caddy 两条匹配写在 [部署](deployment-tencent-cloud.md#https-反向代理)。网关侧还需四项，缺一不可：

  ```bash
  openclaw config patch --stdin --dry-run <<'JSON5'
  { "gateway": {
      "controlUi": { "basePath": "/openclaw",
                     "allowedOrigins": ["https://<域名>", "https://spa.<域名>"] },
      "publicOrigin": "https://<域名>",
      "trustedProxies": ["127.0.0.1", "::1"]
  } }
  JSON5
  # dry-run 通过后去掉 --dry-run 执行，再 openclaw gateway restart
  ```

  `publicOrigin` 是裸 origin，不带路径；缺 `trustedProxies` 会 403 `proxy_attribution_required`；缺 `allowedOrigins` 会在 WS 握手后拒绝来源。SPA 助手页的「打开控制台」地址来自 `NBLANE_OPENCLAW_CONSOLE_URL`。

## 微信通道

- 插件：`@tencent-weixin/openclaw-weixin`（需 OpenClaw ≥ 2026.3.22）。设置页「安装微信渠道」会以 `--pin` 安装并重启网关。
- 扫码登录：`openclaw channels login --channel openclaw-weixin`（在「车间」终端里跑）。登录态在 `~/.openclaw` 内，失效就重新扫码。
- Owner 路由 ID 形如 `<id>@im.wechat`，只放在私有配置里。心跳必须同时设 `target: "openclaw-weixin"` 和 `to: <Owner ID>`；只配 `commands.ownerAllowFrom` 时会 `heartbeat skipped: no-route`。

### weixin-task-bridge

源码在 `scripts/openclaw/plugins/weixin-task-bridge/`，不含 Owner ID 或密钥。提供 Owner 专用命令 `/taskctl list|show <ID>|cancel <ID>`（只作用于当前微信会话可见的任务），并把 Dashboard 等非微信入口发起的长任务进度以 `[后台任务]` 推到 Owner 微信。

安装后写插件配置（先 `--dry-run`）：

```text
plugins.entries.weixin-task-bridge.enabled = true
plugins.entries.weixin-task-bridge.hooks.allowConversationAccess = true
plugins.entries.weixin-task-bridge.config = {channel: "openclaw-weixin", ownerId: <Owner ID>, agentId: "main", longRunDelaySeconds: 30, progressIntervalSeconds: 60}
tools.message.crossContext = {allowAcrossProviders: true, marker: {enabled: true, prefix: "[后台任务] "}}
```

验证：`openclaw plugins inspect weixin-task-bridge --runtime --json` 应为 `status: "loaded"`、`activated: true`、`commands` 含 `taskctl`、`hookCount: 5`。

### 反向推送

`nblane notify <text> [--dry-run]` 经 OpenClaw 入站 webhook 推消息到微信。地址 `NBLANE_OPENCLAW_HOOK_URL`（默认 `http://127.0.0.1:18789/hooks/agent`），token 只从环境 / `.env` 的 `NBLANE_OPENCLAW_HOOK_TOKEN` 读取，须与网关 `cron.webhookToken` 一致。

## 定时任务

归 OpenClaw 管，用 `openclaw automations add|edit|list`（或控制台）建和改，nblane 不同步。提示词只写任务本身，调用规则在 nblane 技能里。每日复盘默认关闭。

`nblane openclaw automations sync <profile> [--apply] [--prune]` 是可选手动工具：想把 `profiles/<name>/assistant/automations.yaml` 当声明维护时才用，只处理 `nblane:` 前缀的任务，默认 dry-run。参数见 [CLI 参考](../reference/cli.md#openclaw)。

## 模型

- 新装默认复用 nblane 的 AI 连接（OpenAI 兼容自定义 provider `nblane`）。已有安装不改。
- 其他服务商在控制台或 `openclaw config set agents.defaults.model.*` 配置。会话里可发 `/model <ref>` 临时切换，`/model default -s` 清除覆盖，`/status` 查看。
- 中转站模型一律配成普通 OpenAI 兼容 provider，不要用 `openai/*` 引用走 Codex harness：后者强制用 Codex 内置 provider 走 WebSocket 直连 `api.openai.com`，表现为全部无回复、`codex app-server execution budget timed out`。
- 没有 embedding key 时记忆检索用 FTS-only：`openclaw config set memory.search.provider '"none"' --strict-json` 后 `openclaw memory status --index --fix --agent main --json`。此时 `embeddingProbe.ok: false` 是预期结果。
- Claude Pro/Max 订阅 OAuth 不要接第三方工具。

## 本机 Codex / Kimi 委派

`skills/codex-dev/`、`skills/kimi-dev/` 让你在微信里说「用 codex 做……」时委派本机 CLI。两者共用 `skills/bin/dev-delegate.sh`（文件输入、后台运行、目录锁、超时、日志）。要求：Linux、Python ≥ 3.11、Git，CLI 已登录且在网关 `PATH` 里。任务状态在 `~/.local/state/dev-delegate/`。

```bash
openclaw skills info codex-dev
python3 -m unittest discover -s scripts/openclaw/skills/bin/tests -v   # 不访问模型
```

## 体检

```bash
nblane openclaw doctor [--profile <name>]
```

只读检查：OpenClaw 版本、Node 版本、linger、`127.0.0.1:18789` 监听、openclaw-weixin 插件已启用、存在 OpenClaw 备份调度。任一 error 级失败退出码为 1。它不调用 `openclaw doctor`（那个会重启网关）。

## 升级

1. 看 [OpenClaw 发布说明](https://docs.openclaw.ai/)，确认 Node 版本要求没变。
2. `npm install -g openclaw@<新版本>`，或改 `NBLANE_OPENCLAW_VERSION` 后在设置页重装。
3. `openclaw gateway restart`，再跑 `nblane openclaw doctor` 和 `nblane openclaw sync --check`。
4. 微信里发一条消息、跑一次 `nblane_api summary` 确认链路。

## 排障

| 症状 | 先查 |
|------|------|
| 助手页「本机未安装 OpenClaw」 | `nblane-web-api.service` 的 `PATH` 是否含 `openclaw` |
| 助手说「nblane 服务账号凭据未配置」或 token 被拒 | `~/.config/nblane/api.env` 和网关 drop-in；token 被撤销就在「助手与备份」点「生成并配置 token」 |
| 助手说「nblane 暂不可达」 | `curl -fsS http://127.0.0.1:8504/api/v1/health`；`nblane-web-api` 状态 |
| 每条微信消息立即失败，日志有 `prepared model catalog owner config was replaced during the read` | 热更新后模型目录绑着旧配置；确认 `openclaw config validate --json` 正常、无运行中任务后完整 `openclaw gateway restart` |
| `gateway status` 报 protocol / token mismatch 或 exit 78 | 是否有 root 下的旧实例占着 18789（`ps aux \| grep -i openclaw`；root 用户服务要用 `XDG_RUNTIME_DIR=/run/user/0` 才看得到） |
| `openclaw doctor --fix` 后报 service ownership changed | 先 `systemctl --user cat openclaw-gateway.service` 核对 unit 和用户，没有重复实例再 `openclaw gateway start`，不要反复重启 |
| `openclaw backup create` 失败 | 工作区残留 `skills/.venv`，删掉即可（已 gitignore） |
| 每会话一个 `nblane-mcp` 进程 | 旧 MCP 注册还在：设置页点「接入 nblane」或 `openclaw mcp unset nblane` |

安全提示：`openclaw.json` 里的 token 和模型 key 是明文，可用 `openclaw secrets audit --check` 列出，再 `openclaw secrets configure` / `apply` 迁到 SecretRef；迁移前先备份 `openclaw.json`，验证通过前不要删可用认证。

## 隔离开发

`scripts/dev-web.sh --isolated` 设置独立 OpenClaw profile：`NBLANE_OPENCLAW_PROFILE=nblane-dev`（状态在 `~/.openclaw-nblane-dev`）、网关 19789、unit `openclaw-gateway-nblane-dev.service`、数据在 `.dev-data/agent-data` 和 `.dev-data/backup`、定时器 `nblane-backup-dev`，助手凭据文件 `NBLANE_OPENCLAW_API_ENV_FILE=.dev-data/agent-config/nblane/api.env`。不会碰生产网关、密钥和定时器。
