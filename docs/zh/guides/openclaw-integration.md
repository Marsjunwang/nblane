---
status: active
owner: 王军
last_verified: 2026-09-20
source_of_truth: src/nblane/mcp_server.py、src/nblane/core/mcp_client_config.py、src/nblane/core/agent_tasks.py、src/nblane/core/openclaw_automations.py、src/nblane/core/openclaw_ops.py、src/nblane/core/openclaw_corpus.py、src/nblane/core/git_backup.py、src/nblane/core/notify.py、src/nblane/commands/openclaw.py、profiles/template/assistant/、scripts/openclaw/skills/、scripts/openclaw/plugins/weixin-task-bridge/、scripts/openclaw/install.sh
---

# OpenClaw 接入指南

本文说明如何把 OpenClaw(常驻 AI agent gateway)接入 nblane,让外部
agent 在你的个人成长系统里"干活",同时保证上下文与审批闭环的主权留在
nblane。

## 定位:各层干什么

| 层 | 谁担当 | 说明 |
| --- | --- | --- |
| 模型(大脑) | 千问 API / ChatGPT / Kimi / Claude | 可替换,按成本与质量路由 |
| Agent runtime(手+嘴) | OpenClaw、Codex CLI、OpenCode | 可替换的执行与消息渠道层 |
| 上下文+记忆+闭环(神经) | **nblane** | `profiles/` 文件是唯一事实源,不自建 coding agent |

OpenClaw 装上来的第一天并不"懂你":它不知道你的技能树、primary goal、
未关联证据。接入的本质是让 OpenClaw 通过 MCP 读取 nblane 的上下文,
并把产出送回 nblane 的审批队列——换任何 runtime,记忆和闭环都不丢。

## 安装所需条件

官方通用安装见 [OpenClaw Install](https://docs.openclaw.ai/install) 与
[Node.js 兼容性](https://docs.openclaw.ai/install/node)。本节只整理**本仓库这条
Linux VPS + 微信日常助手 + nblane MCP** 路径真正依赖的条件,按能力分层,方便新机器对照。

密钥、微信 Owner ID、Gateway token 一律用占位符;迁移时从私有配置或新设备重新取得,
不要把真实值、`.env`、CLI 认证文件或整个 `~/.openclaw` 提交到 nblane。

### 先选目标,再对条件

| 你要达到的状态 | 必须满足的层 |
| --- | --- |
| Gateway 常驻、能对话、能开控制台 | A 最小可运行 |
| 手机微信当日常助手(扫码登录、心跳、计划/复盘) | A + B |
| OpenClaw 读写 nblane 上下文并走审批闭环 | A + C |
| 微信里说「用 Codex / Kimi 做……」并委派本机 CLI | A + D |
| 微信看后台任务进度、`/taskctl` 列出/取消 | A + B + E |

各层互不替代:Gateway 能对话不代表微信已登录,微信能聊不代表 MCP 已接入,
CLI 在交互式终端可用不代表 systemd 用户服务的 `PATH` 里看得到。

### A. 最小可运行 OpenClaw

#### 操作系统与运行时

- **OS**:Linux x64 或 ARM64、glibc(Ubuntu 22.04 / 24.04 已实测)。Alpine/musl 与其它架构需自行准备兼容 Node,官方安装器不会代装。
- **Node.js**:`>=24.16.0 <25` 或 `>=26.1.0`。Node 26 更省内存、启动更快;Linux 安装器在缺 Node 时默认装 **Node 24 LTS**。Node 22 / 23 / 25、以及 24.16 之前、26.1 之前均不支持(`node:sqlite` WAL 与 TEXT 解码要求)。
- **包管理**:`npm` 安装官方包(推荐);从源码构建才需要 `pnpm`。`git` 安装方式还需要 Git。
- **基础工具**:`bash`、`curl`(拉 `https://openclaw.ai/install.sh`)、系统 CA 证书(`/etc/ssl/certs/ca-certificates.crt`)。Gateway 单元建议设 `NODE_EXTRA_CA_CERTS` 指向该文件,避免企业/云镜像 HTTPS 校验失败。
- **进程监督**:`systemd --user`。无图形登录的云主机必须 `sudo loginctl enable-linger "$(whoami)"`,否则 SSH 断开后用户服务会停。
- **运行用户**:用普通用户安装并拥有 `~/.openclaw`。不要用 root 装一遍再切回普通用户;`openclaw doctor --fix` 改属主时可能先停掉 Gateway。

#### 资源与端口

- 官方 Linux 最低参考(树莓派文档):约 **1 GB RAM、1 核、500 MB 空闲磁盘**;推荐 **2 GB+ RAM**。2 GB 及以下建议加 swap。
- 本仓库这条路径还会跑模型会话、微信长连接、可选 Codex/Kimi 子进程。3 GB 级云主机可跑微信 + Flash,但并发委派开发任务时容易顶满;Gateway 托管单元会写 heap 上限(本机 `--max-old-space-size=2048`),手写 unit 不会自动带上。
- **端口 `18789`**:安装前确认空闲。安全默认绑定 `127.0.0.1`(及 `::1`),**不要**对公网开放。控制台用 SSH 隧道或 Tailscale,不要把 Gateway 当公网 HTTP 服务。
- 磁盘还会增长:`~/.openclaw`(配置、会话、插件、npm 缓存)、`~/.local/npm-global`、可选 `~/.local/state/dev-delegate/`。预留数 GB,不要只按 500 MB 规划。

#### 常驻服务与 PATH

用官方路径安装守护进程,不要手写残缺 unit:

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
openclaw onboard --install-daemon   # 或: openclaw gateway install
sudo loginctl enable-linger "$(whoami)"
```

systemd 用户单元里的 `PATH` 必须包含 `openclaw` 实际所在目录(常见为
`~/.local/npm-global/bin` 或 `~/.local/bin`),以及后续要给 Gateway 调的
`codex` / `kimi` / `nblane-mcp`。**只写进交互式 `~/.bashrc` 不够**,用户服务不会读它。

时区建议 `Asia/Shanghai`:心跳 `activeHours` 与每日 08:30 / 21:30 自动化按此时区解释。

#### 至少一条可用的模型凭据

Gateway 起来后仍需要模型才能回复。任选一条稳定路径即可,本机当前是「千问 Flash 主路径 + GPT 中转兜底」:

| 路径 | 需要的条件 | 备注 |
| --- | --- | --- |
| 千问 DashScope | 阿里云百炼 API Key,OpenClaw `qwen` / `alibaba` 插件可用 | 日常助手主模型;可复用 nblane `.env` 的配置思路,但写入 `~/.openclaw`,不进仓库 |
| OpenAI 兼容中转 | 中转 Base URL + API Key(本机 `rightcode/gpt-6-astra`) | 作 `agents.defaults.model.fallbacks` |
| OpenAI / Codex 订阅 | API Key,或 Plus 等订阅的 Codex OAuth | Plus 可用,长期在线 Gateway 官方更建议 API Key |
| Kimi 对话 | Moonshot 开放平台 API Key,或 Kimi Coding 套餐 | **Kimi Pro 网页会员不能**给 agent 用;编程套餐与开放平台 key 不通用 |

Claude Pro/Max 订阅 OAuth 接第三方工具违反 Anthropic 条款,不要用。

#### 控制台

- `gateway.auth.token`(或 password)已配置;浏览器打开 Control UI 时粘贴,不要写进 Git。
- 本机访问:`ssh -L 18789:127.0.0.1:18789 user@host`,再打开隧道后的本地端口。
- Control UI 是管理面(聊天、配置、exec 审批),与微信渠道不是同一入口。

#### 安装与更新时的出站网络

- `https://openclaw.ai`(安装脚本)
- npm registry(装 OpenClaw 与插件;国内网络可能需要镜像)
- 所选模型供应商 HTTPS 端点

**不需要**公网入站、公网回调 URL、独立数据库或独立应用服务器。OpenClaw 是本机文件 + 本机进程。

### B. 微信日常助手(渠道)

在 A 的基础上额外需要:

- **OpenClaw ≥ 2026.3.22**(腾讯微信插件 2.0.x;`latest` dist-tag)。本机核实版本为 **2026.9.4**。插件启动时会检查宿主版本,过旧会拒绝加载。
- 插件:`@tencent-weixin/openclaw-weixin`(一键 `npx -y @tencent-weixin/openclaw-weixin-cli install`,或 `openclaw plugins install "@tencent-weixin/openclaw-weixin"` 后 `plugins.entries.openclaw-weixin.enabled=true`)。
- **手机微信**可扫终端二维码:`openclaw channels login --channel openclaw-weixin`。登录态保存在本机,不进仓库。
- **出站 HTTPS** 到 `https://ilinkai.weixin.qq.com`(插件写死的后端)。微信走腾讯托管链路,**不需要**公网 IP、80/443 入站或自建回调。
- 扫码用的是**个人微信授权**,不是企业微信自定义回调机器人。
- Owner 路由 ID,形态为 `<id>@im.wechat`。文档与脚本只用占位符 `<WEIXIN_OWNER_ID>`。该 ID 用于 `commands.ownerAllowFrom`、心跳 `target=openclaw-weixin` + `to=...`;只配 `ownerAllowFrom`、心跳仍 `target: owner` 时,本机出现过 `heartbeat skipped: no-route`。
- 心跳与自动化还依赖:模型主路径可用、时区 `Asia/Shanghai`、Gateway 常驻。

微信侧能力的配置步骤见下文「微信日常助手、后台任务与自动化」。

### C. nblane MCP(上下文与审批闭环)

在 A 的基础上额外需要:

- **Python ≥ 3.11**(本机 3.12.3)、Git、nblane 仓库检出。
- 在仓库根目录 `python3 -m venv .venv && .venv/bin/pip install -e .`,得到 `nblane` 与 `nblane-mcp` 入口。MCP 依赖随包安装(`mcp`、`pyyaml`、`pydantic` 等),不另装数据库。
- **Gateway 必须解析到 `nblane-mcp`**:交互式 shell 里没有激活 `.venv` 时,`command -v nblane-mcp` 会失败。托管 Gateway 的 systemd `PATH` 默认也不含仓库 `.venv/bin`。生成配置时用 `nblane sync-agent-harness --target openclaw --profile <name>`,让 `mcp.servers.nblane.command` 写成**绝对路径**,或把该目录加进 Gateway unit 的 `PATH`。
- 环境变量:`NBLANE_ROOT` 指向 nblane 仓库根;`NBLANE_PROFILE` 在存在多个 profile 时**必须**设置。可选 `NBLANE_CONTEXT_MODE`、`NBLANE_GAP_USE_LLM`。
- 至少一个真实 profile 目录。`profiles/template/` 只是布局参考,不要拿它当生产事实源;真实 profile 默认 gitignore,不随仓库迁移。
- MCP 走 **stdio 本地子进程**,不新开端口。不要求 Streamlit(8503)或 Reader API(8502)已启动;审批写回在 Web UI 的 Agent Activity 页操作,那是人的处置面,不是 Gateway 启动前提。

### D. 本机 Codex / Kimi 委派

在 A 的基础上额外需要(详见下文「通过 OpenClaw 委派本机 Codex / Kimi 开发」):

- **仅 Linux**。wrapper 使用 `fcntl` 与 `/proc`,不能直接迁到 Windows / macOS。
- Bash、**Python ≥ 3.11**(标准库即可,不强制装 nblane 包)、Git。目标 Git 工作区建议已有至少一次提交,以便 diff / worktree。
- 对应 CLI 已安装并完成登录/provider 配置,且出现在 **Gateway 进程 PATH**(常见 `~/.local/bin`)。本机核对过 Codex **0.154.0**、Kimi **0.43.1**。
- Codex 沙箱可能用到 **bubblewrap**(`bwrap`);缺失时按 Codex 报错处理,不要把关沙箱或改 setuid 当成通用安装步骤。
- 仓库内 Skill 源码:`scripts/openclaw/skills/` 需同步到 `~/.openclaw/workspace/skills/`(两个 `SKILL.md` + `bin/` 共六个文件),运行时与仓库不同步。

### E. 微信任务桥(`/taskctl` 与 `[后台任务]`)

在 A + B 的基础上额外需要:

- 自定义插件 `weixin-task-bridge`(`package.json`、`openclaw.plugin.json`、`dist/index.js`)。源码已随仓库提供于 `scripts/openclaw/plugins/weixin-task-bridge/`,由 `scripts/openclaw/install.sh` 同步 skills 并完成插件安装;`~/.openclaw/workspace/plugins/` 下的运行副本不随 Git 迁移。
- 显式安装:`openclaw plugins install "$HOME/.openclaw/workspace/plugins/weixin-task-bridge" --force --accept-capabilities`。
- Owner 已在 `commands.ownerAllowFrom` 中;命令只作用于当前微信会话可见任务。
- `tools.message.crossContext` 允许跨渠道标记(本机前缀 `[后台任务]`)。

### 账号与密钥清单(全部私有,不入库)

| 项 | 占位写法 | 用途 |
| --- | --- | --- |
| 微信 Owner | `<WEIXIN_OWNER_ID>` | 心跳、owner 命令、`/taskctl` |
| 千问 API Key | 只写在 `~/.openclaw` / 插件凭据 | `qwen/qwen3.8-flash` |
| GPT 中转 Key + Base URL | 同上 | `rightcode/gpt-6-astra` 兜底 |
| Gateway token | `gateway.auth.token` | Control UI / 远程管理 |
| Codex / Kimi CLI 登录态 | 各 CLI 自己的认证文件 | 委派开发,与 Gateway 模型 key 分开 |
| nblane `.env` 的 `LLM_API_KEY` | 只在 nblane 本机 | 给 nblane Web/CLI 用,不会自动变成 OpenClaw 模型 |

安装器与 `openclaw onboard` 会在本机生成上述文件。备份只允许加密的私有副本。

### 明确不需要

- 公网 IP、把 `18789` 暴露到 `0.0.0.0`、自建 HTTPS 反向代理到 Gateway(除非你另做了 Tailscale/受信代理方案)
- 微信公众号 / 企业微信回调 URL、开放 80/443 入站
- 数据库、Redis、独立 Docker 编排(官方也支持容器,但本路径是 systemd 用户服务)
- Windows Hub / macOS 菜单栏伴侣(那是桌面安装路径;本指南是无头 Linux Gateway)
- 为 MCP 单独申请端口或公网证书

### 本机实测对照(2026-09-17,VM-0-5-ubuntu)

| 条件 | 本机值 |
| --- | --- |
| OS / 用户 | Ubuntu,用户 `ubuntu`,Linger=yes |
| Node / npm / OpenClaw | v24.21.0 / 11.19.0 / 2026.9.4 |
| Python / Git | 3.12.3 / 2.43.0 |
| 内存 / 磁盘 | 3.6 Gi RAM;根盘约 69G,剩余约 21G |
| Gateway | `127.0.0.1:18789` 监听;`openclaw-gateway.service` enabled+active;heap 2048 |
| 时区 | Asia/Shanghai |
| 微信插件 | `openclaw-weixin` enabled;登录走 `ilinkai.weixin.qq.com` |
| nblane-mcp | `/home/ubuntu/nblane/.venv/bin/nblane-mcp`(不在默认交互式 PATH) |
| 委派 CLI | `codex`、`kimi`、`bwrap` 均在 `/usr/bin` 或 `~/.local/bin` |

### 安装前自检

在目标机器上以**即将运行 Gateway 的同一用户**执行:

```bash
node -v                  # 需 v24.16+ 或 v26.1+
command -v npm curl git python3
python3 -c 'import sys; assert sys.version_info >= (3, 11)'
ss -ltn | awk '/18789/'  # 安装前应为空;安装后应为 127.0.0.1:18789
loginctl show-user "$(whoami)" -p Linger   # 无头主机应为 Linger=yes
timedatectl show -p Timezone --value       # 建议 Asia/Shanghai
test -f /etc/ssl/certs/ca-certificates.crt && echo ca-ok
```

装完后再核对:

```bash
openclaw --version
systemctl --user is-active openclaw-gateway.service
curl -fsS http://127.0.0.1:18789/readyz
command -v nblane-mcp || echo '把 nblane-mcp 绝对路径写入 mcp.servers'
command -v codex kimi bwrap || true
```

`nblane-mcp` / `codex` / `kimi` 若只在当前终端能找到,还要确认
`systemctl --user cat openclaw-gateway.service` 里的 `PATH=` 同样包含它们。

## 模型与订阅怎么选(2026-09 核实)

- **ChatGPT Plus**:可用。OpenClaw 支持 OpenAI 的 Codex 订阅 OAuth
  登录(Plus $20/月封顶),适合个人交互式使用;长期在线 gateway 官方
  建议 API key 更稳定。
- **千问(DashScope)**:可用。OpenClaw 支持任意 OpenAI 兼容端点,
  直接复用 nblane `.env` 里的 `LLM_BASE_URL` / `LLM_API_KEY` 配置思路即可。
- **Kimi**:充 Kimi Pro 网页会员**不能**给 agent 用。要用 Kimi,需
  Moonshot 开放平台 API key(按量)或 Kimi Coding 编程套餐(独立订阅,
  key 与端点均不通用)。
- 注意:Claude Pro/Max 订阅 OAuth 接第三方工具违反 Anthropic 服务条款,
  请勿使用。

## 实际部署:模型路由(2026-09-19 实测)

服务器(VM-0-5-ubuntu)上微信机器人当前的模型路由:**主对话仍用千问 3.8
Flash,短辅助/心跳/每日隔离任务用更便宜的 3.7 Flash,GPT 中转站兜底**。
3.7-flash / 3.8-flash 的图文能力和 `qwen3-vl-flash` 不在插件自带目录里,需要写进
`models.providers.qwen.models`(与 `qwen3-vl-plus` 并列,`models.mode` 保持
`merge`)。3.8-flash 必须标 `input: ["text","image"]`,否则微信入站图片会被当成
纯文本跳过。

```bash
openclaw config set agents.defaults.model.primary "qwen/qwen3.8-flash"
openclaw config set agents.defaults.model.fallbacks '["qwen/qwen3.7-flash","rightcode/gpt-6-astra"]'
openclaw config set agents.defaults.utilityModel "qwen/qwen3.7-flash"
openclaw config set agents.defaults.heartbeat.model "qwen/qwen3.7-flash"
openclaw config set agents.defaults.compaction.model "qwen/qwen3.7-flash"
openclaw config set agents.defaults.imageModel '{"primary":"qwen/qwen3-vl-flash","fallbacks":["qwen/qwen3-vl-plus"]}'
systemctl --user restart openclaw-gateway    # 已有会话里 /new 生效
```

- `qwen/qwen3.8-flash`:百炼 DashScope,主对话、每周主会话维护,以及主会话里的日常识图。
- `qwen/qwen3.7-flash`:同账号更便宜的上一代 Flash;用于 `utilityModel`
  (标题/审批分类)、心跳、compaction、每日计划/复盘(isolated)。
- `qwen/qwen3-vl-flash`:`imageModel` 兜底,只在当前会话模型被标成纯文本时看图。
- `qwen/qwen3-vl-plus`:识图 fallback,难图/UI/长视频再上场。
- `rightcode/gpt-6-astra`:rightcode 中转站,OpenAI 兼容接口,普通 provider,
  只作最后兜底。
- 会话级临时切换(微信里直接发):`/model rightcode/gpt-6-astra`、
  `/model qwen/qwen3.5-plus`、`/model default`;`/status` 查看当前模型。
- 已有会话可能保留 session override，不会因修改全局默认值而自动切换。使用
  `/model default -s` 清除当前会话覆盖，或 `/new` 后再核对 `/status`。

### API key 配置方法

- **百炼(qwen)**:`openclaw models auth login --provider qwen` 交互录入;
  `openclaw models auth list --provider qwen` 查看已有 profile。
  provider 端点 `https://dashscope.aliyuncs.com/compatible-mode/v1`,
  `api: "openai-completions"`。
- **rightcode 中转**:静态 API key,与 codex CLI 共用同一把
  (`~/.codex/auth.json` 的 `OPENAI_API_KEY`):

  ```bash
  openclaw config set models.providers.rightcode '{
    "baseUrl": "https://rightapi.ai/codex/v1",
    "api": "openai-completions",
    "apiKey": "<取自 ~/.codex/auth.json 的 OPENAI_API_KEY>",
    "models": [{"id":"gpt-6-astra","name":"gpt-6-astra","api":"openai-completions",
                "contextWindow":200000,"maxTokens":128000}]
  }'
  ```

  注意:baseUrl 必须带渠道前缀 `/codex/v1`(旧版 key 不认裸 `/v1`);
  自定义 provider 必须显式声明 `models` 数组,否则配置校验不过。

### 踩坑:中转站模型不能走 Codex harness

曾尝试让 OpenClaw 通过 Codex app-server harness 跑中转站模型
(模型引用 `openai/gpt-6-astra`),症状是微信/Dashboard 全部无回复、报
`codex app-server execution budget timed out`,但 `/codex status` 正常、
`codex exec` 也正常,极具迷惑性。根因链:

1. codex harness **只接受 `openai/*` 模型引用**(自定义 provider 报
   `provider is not one of: codex, openai`);
2. `openai/*` 会强制使用 codex **内置的 openai 提供商**(线程 rollout 文件
   `~/.codex/sessions/**/rollout-*.jsonl` 的 `session_meta.model_provider`
   可实锤),无视 `~/.codex/config.toml` 的 `model_provider`;
3. 新版 codex 内置提供商走 **WebSocket 直连 `api.openai.com`**,国内服务器
   无代理必挂;且本机 codex 登录是 rightcode 的 key,真 OpenAI 也不认。

弯路(不要再试):在 `config.toml` 重定义 `[model_providers.openai]` 会被
codex 拒绝(`reserved built-in provider IDs`,还会搞挂系统 codex CLI);
`OPENAI_BASE_URL` 只影响 HTTPS、不影响 WebSocket 硬编码域名。

**结论:中转站场景一律用普通 provider(上面的 rightcode 配置),
不要用 `openai/*` 引用。** codex harness 仅适合真实 ChatGPT 订阅 +
可直连/可代理 api.openai.com 的环境。

### 踩坑:root 残留旧实例抢端口

若 `openclaw gateway status` 报 `protocol mismatch` / `token mismatch` /
服务 exit 78:检查是否有 root 下的旧版 OpenClaw 占着 18789
(`ps aux | grep -i openclaw`)。本机曾残留 pnpm 装的 2026.3.8,由
**root 的 systemd 用户服务**守护(系统级 `systemctl` 看不到,需
`sudo env XDG_RUNTIME_DIR=/run/user/0 ... systemctl --user stop/disable`),
已于 2026-09-17 清理完毕,旧配置归档 `/root/.openclaw.bak-20260917`。

更多运维细节(验证三板斧、日志位置、杂项坑)见服务器上的
`~/.openclaw/config-notes.md`。

## 微信日常助手、后台任务与自动化（2026-09-17 实测）

安装前置见上文「安装所需条件」的 **A + B**(任务桥再加 **E**)。
本节记录 VM-0-5-ubuntu 上已经落地的日常助手配置、运行时文件、自动化和
验收结果，用于故障追溯与迁移。微信用户 ID 属于个人路由数据，本文只使用
`<WEIXIN_OWNER_ID>` 占位符；迁移时从私有配置或新设备重新取得，不要把真实 ID、
API key、Gateway token 或整个 `~/.openclaw` 提交到仓库。

### 当前能力与边界

- 微信普通回复显示 Token 用量，工具调用显示结构化开始/结果进度。
- Dashboard 或其他非微信入口发起的长任务，可向 Owner 微信发送
  `[后台任务]` 状态；普通 Dashboard 回合超过 30 秒才提示，后台子任务立即提示，
  有新工具进展时最多每 60 秒推送一次，结束时报告成功或失败。
- 微信提供 Owner 专用命令：`/taskctl list`、`/taskctl show <ID>`、
  `/taskctl cancel <ID>`。命令只操作**当前微信会话可见的任务**，不是无边界的
  全局管理员接口；全局排查仍使用终端 `openclaw tasks list`。
- OpenClaw 原生命令 `/tasks` 仍可查看当前会话任务；`停止` 用于中止当前主回合。
- 心跳使用 Flash，每小时一次，只在北京时间 08:00–23:00 运行，并固定投递到
  Owner 微信。无事项时遵守 `NO_REPLY`，不会每小时强制发一条消息。
- 每天 08:30 发送计划、21:30 发送复盘；每周日 20:00 向主会话注入记忆与项目
  整理事件。

### 一次性配置

先准备真实 Owner ID，但不要把它写进仓库：

```bash
export WEIXIN_OWNER_ID='<WEIXIN_OWNER_ID>'
```

使用批量更新保证相关配置一起通过校验。先 `--dry-run`，确认后去掉该参数执行：

```bash
batch_file=$(mktemp)
trap 'rm -f "$batch_file"' EXIT
python3 - "$WEIXIN_OWNER_ID" >"$batch_file" <<'PY'
import json
import sys

owner = sys.argv[1]
updates = [
    {"path": "agents.defaults.model.primary", "value": "qwen/qwen3.8-flash"},
    {
        "path": "agents.defaults.model.fallbacks",
        "value": ["qwen/qwen3.7-flash", "rightcode/gpt-6-astra"],
    },
    {"path": "agents.defaults.utilityModel", "value": "qwen/qwen3.7-flash"},
    {
        "path": "channels.openclaw-weixin.replyProgressMessages",
        "value": True,
    },
    {
        "path": "messages.responseUsage",
        "value": {"default": "off", "openclaw-weixin": "tokens"},
    },
    {
        "path": "commands.ownerAllowFrom",
        "value": [f"openclaw-weixin:{owner}"],
    },
    {
        "path": "tools.message.crossContext",
        "value": {
            "allowAcrossProviders": True,
            "marker": {"enabled": True, "prefix": "[后台任务] "},
        },
    },
    {
        "path": "agents.defaults.heartbeat",
        "value": {
            "every": "1h",
            "model": "qwen/qwen3.7-flash",
            "lightContext": True,
            "isolatedSession": True,
            "target": "openclaw-weixin",
            "to": owner,
            "directPolicy": "allow",
            "activeHours": {
                "start": "08:00",
                "end": "23:00",
                "timezone": "Asia/Shanghai",
            },
        },
    },
]
json.dump(updates, sys.stdout, ensure_ascii=False)
PY

openclaw config set --batch-file "$batch_file" --dry-run
# dry-run 成功后执行：
openclaw config set --batch-file "$batch_file"
```

心跳必须同时设置显式 `target` 和 `to`。只配置
`commands.ownerAllowFrom` 并保留 `target: "owner"` 时，本机腾讯微信插件曾显示
`waitingForRoute: true` / `heartbeat skipped: no-route`；显式路由后变为
`waitingForRoute: false`。

核对关键配置：

```bash
openclaw config get agents.defaults.model --json
openclaw config get agents.defaults.utilityModel --json
openclaw config get messages.responseUsage --json
openclaw config get tools.message.crossContext --json
openclaw config get agents.defaults.heartbeat --json
openclaw status --json
```

### 长任务与助手角色规则

运行机已把下列规则合并到 `~/.openclaw/workspace/AGENTS.md`。迁移时应合并到目标
workspace 的现有文件，不要覆盖其中其他约定：

```markdown
## Personal Assistant Role

- Capture durable decisions, commitments, deadlines, and follow-ups in the
  appropriate workspace files.
- Turn requests into a short, visible checklist when there are multiple steps.
- Organize incoming information into actionable summaries; separate facts,
  assumptions, decisions, and next actions.
- Proactively surface overdue work, blocked projects, upcoming deadlines, and
  decisions that need the owner's attention.
- Use scheduled automations for recurring reminders and reviews rather than
  relying on conversational memory.
- Confirm before external communications, purchases, destructive actions, or
  commitments made in the owner's name.
- Delegate substantial programming, terminal, and Git work to a tracked
  background task when appropriate; remain responsible for validation and the
  final summary.

## Long-running Tasks

- Work expected to exceed 30 seconds must run as a tracked background task.
- Immediately report the task name, task ID, current checklist, and how to
  cancel it.
- Use the `state_changes` notification policy unless the owner explicitly asks
  for silent or completion-only updates.
- For work started outside Weixin, mirror phase changes and meaningful
  milestones to the configured owner Weixin route. During active tool work,
  send a concise update at least every 60-90 seconds when there is new
  information.
- Report completed, failed, blocked, timed-out, and cancelled states. Never
  claim progress that was not observed.
- Keep the final update concise: outcome, verification performed, remaining
  risk, and the next action if one is needed.
- Never leave long work running only as an untracked interactive chat turn.
```

`MEMORY.md` 中也应记录已经验证的**事实**：主模型为 3.8 Flash、utility/心跳/
每日隔离任务为 3.7 Flash、Fallback 为 3.7 Flash 再 GPT-6 Astra，以及微信进
度/Token/Owner 路由已启用。不要把 Owner ID 或密钥写进长期记忆。

### Weixin Task Bridge 插件

本机自定义插件 ID 为 `weixin-task-bridge`，版本 `0.1.0`。源目录和安装目录分别为：

```text
~/.openclaw/workspace/plugins/weixin-task-bridge/
├── package.json
├── openclaw.plugin.json
└── dist/index.js

~/.openclaw/extensions/weixin-task-bridge/   # openclaw plugins install 的安装副本
```

插件源码已纳入 nblane Git（`scripts/openclaw/plugins/weixin-task-bridge/`），可由
`scripts/openclaw/install.sh` 幂等安装；其中不含 Owner ID 或密钥。
`~/.openclaw/workspace/plugins/` 下的副本仍是运行数据，不随仓库迁移。目标机器先审阅源码，
再显式接受本地插件能力：

```bash
openclaw plugins install \
  "$HOME/.openclaw/workspace/plugins/weixin-task-bridge" \
  --force --accept-capabilities
```

插件注册 5 个 typed hooks：`before_agent_reply`、`subagent_spawned`、
`after_tool_call`、`agent_end`、`subagent_progress`，以及一个 Owner 专用
`taskctl` 命令。它通过腾讯微信 channel adapter 的 `sendText` 发送通知，
不绕过 OpenClaw 的渠道配置。

安装后再写插件配置：

```bash
plugin_batch=$(mktemp)
trap 'rm -f "$plugin_batch"' EXIT
python3 - "$WEIXIN_OWNER_ID" >"$plugin_batch" <<'PY'
import json
import sys

owner = sys.argv[1]
json.dump(
    [
        {
            "path": "plugins.entries.weixin-task-bridge.enabled",
            "value": True,
        },
        {
            "path": "plugins.entries.weixin-task-bridge.hooks.allowConversationAccess",
            "value": True,
        },
        {
            "path": "plugins.entries.weixin-task-bridge.config",
            "value": {
                "channel": "openclaw-weixin",
                "ownerId": owner,
                "agentId": "main",
                "longRunDelaySeconds": 30,
                "progressIntervalSeconds": 60,
            },
        },
    ],
    sys.stdout,
    ensure_ascii=False,
)
PY
openclaw config set --batch-file "$plugin_batch" --dry-run
openclaw config set --batch-file "$plugin_batch"
```

插件采用双重命令门禁：消息必须来自 `openclaw-weixin`、通过 OpenClaw 授权，
且 `senderId`/`from` 必须精确匹配插件配置中的 Owner ID。迁移后验证：

```bash
openclaw plugins inspect weixin-task-bridge --runtime --json
```

预期：`status: "loaded"`、`activated: true`、`commands` 包含 `taskctl`、
`hookCount: 5`。然后在 Owner 微信中依次测试：

```text
/taskctl list
/taskctl show <实际任务 ID 或无歧义前缀>
/taskctl cancel <可取消的实际任务 ID 或无歧义前缀>
```

### 日常自动化

以下声明键用于识别任务，迁移前先运行 `openclaw automations list --all --json`
避免重复创建。命令中的 Owner ID 由 shell 展开，提示词不包含密钥：

```bash
openclaw automations add \
  --name personal-assistant-daily-plan \
  --display-name '每日计划' \
  --declaration-key personal-assistant:daily-plan \
  --cron '30 8 * * *' --tz Asia/Shanghai --exact \
  --agent main --session isolated \
  --model qwen/qwen3.7-flash --fallbacks rightcode/gpt-6-astra \
  --timeout-seconds 300 \
  --announce --best-effort-deliver \
  --channel openclaw-weixin --to "$WEIXIN_OWNER_ID" \
  --message '生成今天的执行计划。读取当前看板、项目记录、近期承诺和今天相关的工作区信息；不要臆测不存在的日历或任务。用中文简洁列出：今日最重要的 3 项、已知时间节点、阻塞/待决策事项、建议的第一步。如果没有有效信息，明确说明并给出一个整理建议。'

openclaw automations add \
  --name personal-assistant-daily-review \
  --display-name '每日复盘' \
  --declaration-key personal-assistant:daily-review \
  --cron '30 21 * * *' --tz Asia/Shanghai --exact \
  --agent main --session isolated \
  --model qwen/qwen3.7-flash --fallbacks rightcode/gpt-6-astra \
  --timeout-seconds 300 \
  --announce --best-effort-deliver \
  --channel openclaw-weixin --to "$WEIXIN_OWNER_ID" \
  --message '完成今日复盘。读取今天的日记、看板和活跃项目记录，只依据已记录的信息。必要时把可验证的进展和未完成事项写入今天的 daily memory。用中文简洁汇报：今日完成、尚未完成、阻塞与原因、明日优先事项、需要主人确认的决定。不要把未观察到的工作标为完成。'

openclaw automations add \
  --name personal-assistant-weekly-maintenance \
  --display-name '每周记忆与项目整理' \
  --declaration-key personal-assistant:weekly-maintenance \
  --cron '0 20 * * 0' --tz Asia/Shanghai --exact \
  --agent main --session main --wake now \
  --system-event '执行每周维护：审阅最近 7 天 daily memory、USER.md、MEMORY.md、看板和活跃项目/目标记录；遵守文件各自的访问与写入规则。把稳定偏好整理到 USER.md，把长期事实和决定整理到 MEMORY.md，移除或标记已过时且有证据支持的条目，保留不确定内容并注明。同步项目状态和下一步，最后向 Owner 微信汇报本周进展、未决事项、下周三项重点和实际修改过的文件。'
```

每周任务使用 `main + systemEvent`，因为普通 `agentTurn` 不能直接创建在 main
session；事件会唤醒主会话处理需要主会话权限的 `MEMORY.md`。两个每日任务使用
isolated session，避免污染长期主对话。

### 记忆索引修复

本机未给 memory embedding provider 配置 OpenAI API key。默认自动选择
`text-embedding-3-small` 时，状态曾为 `indexIdentity: mismatched`，强制重建报
`No API key found for provider "openai"`。为恢复可用检索，当前明确使用官方支持的
FTS-only 模式：

```bash
openclaw config set memory.search.provider '"none"' --strict-json
openclaw memory status --index --fix --agent main --json
```

验收状态应包含：`dirty: false`、`provider: "none"`、
`searchMode: "fts-only"`、`indexIdentity.status: "valid"`、`fts.available: true`。
该模式无需 embedding key，但只有关键词检索，没有语义向量检索。以后配置可用
embedding provider 后，应显式改回对应 provider 并重新 `--index`，不要把
`embeddingProbe.ok: false`（FTS-only 的预期结果）误判为关键词索引损坏。

### Gateway 重启、故障恢复与端到端验收

配置或插件安装完成后：

```bash
openclaw doctor --fix --non-interactive --yes
openclaw gateway restart
openclaw gateway status
```

Doctor 会在修复期间停止受管 Gateway。本机曾在 Doctor 收尾时报告
`Gateway service ownership or manager identity changed`，但 systemd unit 实际为
当前用户所有且干净退出。遇到该情况不要反复重启，先检查：

```bash
systemctl --user status openclaw-gateway.service --no-pager
systemctl --user cat openclaw-gateway.service
openclaw gateway status
```

确认 unit 路径、用户和 `ExecStart` 正确且没有重复实例后，再执行
`openclaw gateway start`。本机最终状态为 Gateway `running`、connectivity
`ok`，腾讯微信 monitor 已启动，插件列表包含 `weixin-task-bridge`。

另一种表象是 Gateway 和微信 monitor 都显示运行，但每条微信消息立即失败，日志反复出现：

```text
Embedded agent failed before reply:
prepared model catalog owner config was replaced during the read
```

这表示运行中的 prepared model catalog 仍绑定旧配置快照，常见于启动后继续热更新
心跳或模型相关配置。先确认 `openclaw config validate --json` 和
`openclaw models status --json` 正常、没有运行中或排队任务，再做一次完整
`openclaw gateway restart`。2026-09-17 本机重启后，Gateway-backed Flash 自检返回
`OK`，微信直接测试消息状态为 `sent`。不要因为进程仍是 `active` 就忽略消息处理日志。

完整验收：

```bash
openclaw plugins inspect weixin-task-bridge --runtime --json
openclaw automations list --all --json
openclaw memory status --agent main --json
openclaw status --json
```

可手动运行一次每日计划验证真实投递（会调用模型并消耗 Token）：

```bash
daily_plan_id='<从 automations list 取得的实际 ID>'
openclaw automations run "$daily_plan_id" \
  --wait --expect-final --wait-timeout 8m --json
```

2026-09-17 本机端到端结果：Flash 模型执行成功，运行约 130 秒，
`deliveryStatus: "delivered"`，解析到腾讯微信 account，Owner 手机收到“今日执行
计划”。这证明自动化到微信的投递链路可用；`/taskctl` 的入站权限和具体任务取消
仍应在迁移后的 Owner 微信中用实际任务单独验证。

### 已知但未在本次修改的安全提示

Doctor 还报告过以下既有问题，本次日常助手配置没有擅自修改：

- `openclaw.json` 中仍有明文 Gateway token 和 rightcode API key，应后续通过
  SecretRef 迁移并运行 `openclaw secrets audit --check`；迁移前不要删除可用认证。
- Browser Relay 仍允许 legacy authentication；应先升级所有浏览器扩展/CDP 客户端，
  再关闭兼容开关，避免把仍在使用的客户端直接断开。
- Gateway 绑定 `127.0.0.1` 是当前本地部署的预期安全边界，不应为了消除 Doctor
  提示直接改为公网监听。
- 尚未记录成功的 OpenClaw 配置备份；需要备份时使用 OpenClaw 的 backup 命令或
  私有、加密的配置备份，不要把认证数据提交到 nblane。

## 通过 OpenClaw 委派本机 Codex / Kimi 开发

这条路径使用 OpenClaw 的 exec 工具调用本机 CLI，与上文的模型 provider 路由、
Codex app-server harness 以及下文的 nblane MCP 接入分别配置。Gateway 能对话，
不代表本机 CLI 已安装或登录；CLI 正常也不代表 MCP 已接入。

保留两个独立 Skill：用户明确说“用 codex 做……”或“用 kimi 做……”时才调用，
没有指定执行者时不自动委派。两者共用一个安全 wrapper，负责文件输入、后台运行、
目录锁、超时、日志和最终状态，避免两套执行行为发生漂移。

### 随仓库提供的安装文件

可迁移源码位于 [`scripts/openclaw/skills/`](../../../scripts/openclaw/skills/)，
部署后保持下列相对目录结构；不要只复制两个 `SKILL.md`：

```text
~/.openclaw/workspace/skills/
├── codex-dev/SKILL.md
├── kimi-dev/SKILL.md
└── bin/
    ├── dev-delegate.sh          # 共用命令入口
    ├── dev_delegate.py          # Python 标准库实现
    ├── delegation.md            # 两个 Skill 引用的共用运行规则
    └── tests/test_dev_delegate.py
```

Skill 通过 `{baseDir}/../bin/dev-delegate.sh` 定位入口，不写死 `/home/ubuntu`。
以后修改仓库内源码，再按下面的安装步骤同步到实际 workspace；运行时文件与仓库
不是自动同步关系。非默认 workspace 应替换下面的 `delegate_skills`。

### 前置条件与安装

完整分层清单见上文「安装所需条件」**D 层**。此处只列委派路径的硬依赖:

- Linux、Bash、Python ≥ 3.11、Git；wrapper 使用 `fcntl` 和 `/proc`，不支持直接迁移到
  Windows/macOS。Python 部分只使用标准库，不要求安装 nblane 或额外 Python 包。
- 按各自官方安装说明安装 OpenClaw、Codex CLI、Kimi Code CLI，并在目标机器完成登录
  或 provider 配置。核对过的 CLI 版本为 Codex **0.154.0**、Kimi **0.43.1**；
  升级后重新核对帮助和测试，不假定所有历史版本参数一致。
- Git 工作区应已有至少一个提交，以便记录相对 `HEAD` 的 diff 或创建 worktree。
- CLI 必须出现在 **Gateway 进程的 PATH**，而不只是当前交互式终端的 PATH。

在 nblane 仓库根目录，用 Bash 执行以下安装命令。只覆盖列出的六个文件，覆盖前逐个
备份到 `~/.openclaw/skill-backups/`，保留 workspace 内其他 Skill 和文件：

```bash
(
  set -eu
  nblane_checkout="$PWD"
  delegate_source="$nblane_checkout/scripts/openclaw/skills"
  delegate_skills="$HOME/.openclaw/workspace/skills"
  delegate_files=(
    codex-dev/SKILL.md
    kimi-dev/SKILL.md
    bin/dev-delegate.sh
    bin/dev_delegate.py
    bin/delegation.md
    bin/tests/test_dev_delegate.py
  )
  # 先检查整个安装集合，避免源文件缺失时只更新一半。
  for relative in "${delegate_files[@]}"; do
    test -f "$delegate_source/$relative"
  done
  mkdir -p "$HOME/.openclaw/skill-backups"
  delegate_backup=$(mktemp -d "$HOME/.openclaw/skill-backups/dev-delegate.XXXXXXXX")
  for relative in "${delegate_files[@]}"; do
    destination="$delegate_skills/$relative"
    if [ -e "$destination" ] || [ -L "$destination" ]; then
      mkdir -p "$delegate_backup/$(dirname "$relative")"
      cp -a -- "$destination" "$delegate_backup/$relative"
    fi
    mkdir -p "$(dirname "$destination")"
    case "$relative" in
      bin/dev-delegate.sh|bin/dev_delegate.py) file_mode=755 ;;
      *) file_mode=644 ;;
    esac
    install -m "$file_mode" -- "$delegate_source/$relative" "$destination"
  done
  printf 'Installed: %s\nBackup: %s\n' "$delegate_skills" "$delegate_backup"
)
```

如有正在执行的委派，先让它完成或通过 `cancel` 正常结束，再更新 wrapper。
备份目录只含被替换的 Skill 文件，不是 OpenClaw 配置或会话的完整备份。

Kimi 安装在 `~/.kimi-code/bin/kimi` 而 Gateway PATH 不含该目录时，可创建稳定入口；
如果目标机器安装在别处，应先调整 `kimi_target`。以下命令不会覆盖已有入口：

```bash
(
  set -eu
  kimi_target="$HOME/.kimi-code/bin/kimi"
  test -x "$kimi_target"
  mkdir -p "$HOME/.local/bin"
  if [ ! -e "$HOME/.local/bin/kimi" ] && [ ! -L "$HOME/.local/bin/kimi" ]; then
    ln -s "$kimi_target" "$HOME/.local/bin/kimi"
  fi
  "$HOME/.local/bin/kimi" --version
)
```

确认 Gateway PATH 包含 `~/.local/bin`（运行时为展开后的绝对路径）。如果 Gateway
由 systemd 启动，修改 `.bashrc` 通常不能改变其环境：先检查现有 unit/drop-in，
按目标机器路径合并 PATH，保留已有配置。systemd `Environment=` 中不要依赖 shell
展开 `$HOME` 或 `$PATH`。只有服务环境确实改变时才需要 daemon-reload / 重启；
单纯更新 Skill 应新建 OpenClaw 会话或刷新技能快照，不必自动重启 Gateway。

### 依赖门禁与安装验收

两个 Skill 都声明运行条件，Codex 示例：

```yaml
metadata:
  openclaw:
    os: [linux]
    requires:
      bins: [bash, python3, git, codex]
```

Kimi 将最后一项换为 `kimi`。wrapper 用 Python 管理计时和信号，不依赖 `timeout`
或外部 `flock` 命令，因此不把它们列为安装条件。`Ready` 仅表示依赖门禁通过，
不保证登录有效、服务 PATH 一致或模型端请求成功。

```bash
codex --version
codex login status
kimi --version
kimi doctor
openclaw skills info codex-dev
openclaw skills info kimi-dev
python3 -m unittest discover -s scripts/openclaw/skills/bin/tests -v
```

预期两个 Skill 为 `Ready`，并列出对应 Binaries 与 Linux 条件。也要在 Gateway 所用
环境下检查依赖；终端中 `skills info` 的结果不能单独证明服务环境正确。
最后一条命令从仓库根目录运行，使用临时 Git 仓库和模拟 CLI，不访问模型 API、
不依赖账号或 LLM key，也不写入真实项目。

2026-09-17 修复版已通过 **15 项行为测试**，覆盖引号/命令替换等输入的原样传递、
会话恢复参数、日志分离、脏工作区保护、跨 CLI 锁、子目录/符号链接锁、worktree
隔离及其目录锁、超时清理、CLI 返回 124 与实际超时的区分、worker 意外退出等。
同时核对了本机 CLI 帮助和 OpenClaw 门禁；此次安全修复没有重新发起真实模型任务，
不能把这些测试描述为新版 wrapper 的模型端端到端验证。

新机器完成上述检查后，再用一个临时项目做真实只读任务验收，例如让指定 CLI
列出项目文件并说明结构、不修改文件。该步骤会使用目标 CLI 的模型服务。
核对真实日志、退出状态与会话 ID 后再用于开发任务。

### 执行、轮询、取消与恢复

先通过文件写入工具或编辑器把任务保存为 UTF-8 文件，明确目标、允许修改的文件、
需要保留的现有修改和验收方式。不要把任务原文拼到 shell 命令中，也不要用拼接的
`echo` 或未引用的 heredoc 创建 prompt。示例中的路径是占位值，需换成实际路径；
动态路径与 ID 同样要安全引用，支持 argv 的执行接口应优先使用 argv。

```bash
delegate_wrapper="$HOME/.openclaw/workspace/skills/bin/dev-delegate.sh"
"$delegate_wrapper" start codex /absolute/project /absolute/prompt.txt
# 使用 Kimi 时，将 codex 换成 kimi。
```

wrapper 自行后台运行，返回包含 `task_dir`、`pid`、`status_file`、`events`、`stderr`
的 JSON。后续使用实际返回的 `task_dir`，不要根据时间戳猜路径。不要额外包裹
`nohup`、`&`、`timeout` 或 `</dev/null`。

```bash
"$delegate_wrapper" poll /absolute/task_dir
# 需要停止任务时：提交请求后继续 poll，直到终态。
"$delegate_wrapper" cancel /absolute/task_dir
```

每 20–30 秒查看一次状态和日志，有实质进展时向用户汇报；无日志变化不等于卡死。
追问时将新任务写入另一个文件，使用原任务状态中的实际 `cwd` 和 `session_id`：

```bash
"$delegate_wrapper" start codex /previous/cwd /absolute/followup.txt ACTUAL_SESSION_ID
```

如果原任务已经产生未提交修改，先审阅后按下节规则加 `--allow-dirty`。
恢复 worktree 内的会话时使用记录的 `cwd`，不要再次加 `--worktree`。
不要用“最近一次会话”代替明确 ID，也不要自行添加 `session_` 前缀。

内部调用协议为：

| CLI | 首次执行 | 恢复与会话 ID |
| --- | --- | --- |
| Codex | `exec --sandbox workspace-write --json`，prompt 从 stdin 读取 | `exec --sandbox workspace-write resume --json`；从 `thread.started.thread_id` 获取 ID |
| Kimi | `--output-format stream-json --prompt`，prompt 作为单个 argv 元素传入 | 使用 `--session`，不用过时的 `-r`；读取结构化 `session_id` / `sessionId` 字段 |

Kimi 不额外添加 `--auto` / `-y`，也不沿用“这些参数必然与 `-p` 互斥”的旧断言。
若当前版本事件未提供支持的会话字段，状态保持空 ID，保留原始日志；可通过
`kimi session list --cwd /actual/cwd --json` 核对会话，不从自然语言尾注猜测。
恢复需要 CLI 自身仍保存该会话；复制 wrapper 的状态文件不能重建 CLI 会话。

### 工作区保护与高风险任务

执行前检查 `git status --short`；wrapper 也会在持有锁后检查。

| 选项 | 行为与使用条件 |
| --- | --- |
| 默认 | 拒绝已有修改，包括未跟踪文件；适合干净且已有提交的 Git 工作区 |
| `--allow-dirty` | 仅在已检查现有修改、确认任务范围后使用；保留原修改，不自动 stash/reset/clean |
| `--worktree` | 从干净源仓库 HEAD 创建 detached worktree；结果保留供审阅，不自动合并或删除 |
| `--allow-non-git` | 显式允许非 Git 目录；只有目录锁，没有 Git 快照或 worktree |
| `--timeout SECONDS --grace SECONDS` | 调整 CLI 运行时限及 TERM 后等待时间，默认分别为 600 和 15 秒 |

`--worktree` 不会复制未提交修改；即使同时传 `--allow-dirty`，脏源仓库仍会被拒绝。
如果任务依赖尚未提交的修改，应先明确采用原目录执行还是准备合适的隔离基线，
不要偷偷丢弃现有修改再创建 worktree。

两个 CLI 共用按规范化 Git 工作树根目录定位的 advisory lock，涵盖仓库子目录和
符号链接别名；新建 worktree 也有自己的锁。锁只约束遵守同一 wrapper 协议的任务，
不能阻止编辑器或其他工具写入。worktree 不是系统权限沙箱，Kimi 的工具权限仍由
其 CLI 决定；Codex 实际可写范围也受配置和受保护路径影响。

### 状态、日志与故障处理

任务保存在 `~/.local/state/dev-delegate/` 的唯一目录中，目录权限 0700，任务文件
默认 0600。可用 `DEV_DELEGATE_STATE_DIR` 调整位置，但同一工作区的所有调用必须
保持同一个状态根目录，否则会分离锁文件、失去共同互斥。

| 文件 | 用途 |
| --- | --- |
| `prompt.txt` | 启动时复制的任务输入；之后修改原文件不会改变本次任务 |
| `events.jsonl` | CLI stdout，供结构化事件解析 |
| `stderr.log` / `worker.log` | CLI 诊断 / wrapper 诊断；不与 JSONL 混合 |
| `status.json` / `launch.json` | 原子更新的任务状态 / worker 启动身份 |
| `before.json` / `after.json` | Git 状态及相对 HEAD 的 tracked diff；不是文件备份，不包含未跟踪文件内容 |
| `worktree/` | 仅 `--worktree` 模式创建，保留实际任务产物 |

`poll` 返回 `QUEUED`、`STARTING`、`RUNNING`、`SUCCEEDED`、`FAILED`、`TIMEOUT`、
`CANCELLED` 或 `EXITED_UNKNOWN`。`start` 返回 0 只表示启动成功；最终结果看 `poll`，
不能拿启动命令的退出码当成 CLI 的执行结果。

- 超时或取消时向 CLI 进程组发送 TERM，最多等待 15 秒后发送 KILL；因此默认时限
  加清理宽限约为 10 分 15 秒，不承诺整个安装/建 worktree/收尾过程严格在 10 分钟内。
- `TIMEOUT` 的 `exit_code=124`，`CANCELLED` 为 130；其他失败保留 CLI 退出码，
  信号退出转为 `128+signal`。`child_returncode` 保留 Python 原始返回值。
  CLI 自己返回 124 记为 `FAILED`，不能仅凭数字判断超时。
- worker 被外部强杀或机器重启可能无法收尾；`EXITED_UNKNOWN` 时检查日志和
  `child_pid`，不要假定整个任务已停止并直接重试。主动逃离进程组的子进程不在
  清理保证范围内。
- `SUCCEEDED` 只说明 CLI 正常结束，还要检查产物内容、前后变更、允许修改的范围
  以及测试证据。已有可靠验证不必重复跑；仅 `ls` 到文件不足以完成验收。
- Codex bwrap/沙箱错误先查 `stderr.log` 和目标机器配置；不要把修改 setuid、
  关闭沙箱或提权当成通用安装步骤。`--skip-git-repo-check` 只用于明确允许的非 Git
  目录，不解决项目信任、权限或沙箱错误。

### 迁移与回退

新机器安装：复制或检出 nblane 仓库，安装目标机器的 CLI 并重新认证，再执行本节
安装、PATH 检查和验收步骤。安装文件不包含旧机器的账号、密钥或 session store。
不要把 `.env`、CLI 认证文件或整个 `.openclaw` 目录打包提交到仓库。

仅迁移新任务能力时，无需复制 `~/.local/state/dev-delegate/`。如需保留旧任务供审阅，
把选定任务目录作为私有数据单独迁移；其中含 prompt、日志、绝对路径及可能的 worktree，
不是可以直接重新启动的队列。跨机器恢复还依赖 CLI 自身的会话迁移和工作目录，
不能只复制 `status.json` 后继续运行。

安装命令输出的 `Backup` 路径可用于恢复被覆盖的同名文件。回退前先结束活动任务，
按相同相对路径恢复匹配版本的两个 Skill 和共用文件，不要把旧 Skill 与新 wrapper
混搭；新建会话后重新检查 `skills info`。新增文件没有旧备份时，应在确认无需保留后
单独移走，不删除整个 workspace 或用户数据。

## 接入步骤

1. 先核对本页「安装所需条件」。满足 **A** 后再安装并初始化 OpenClaw(官方文档,
   `curl -fsSL https://openclaw.ai/install.sh | bash`,然后 `openclaw onboard --install-daemon`)。
   微信助手、MCP、Codex/Kimi 分别对应 **B / C / D**,缺哪层补哪层,不要假定一次 onboard 全部完成。
2. 生成 nblane 的 MCP 配置片段:

   ```bash
   nblane sync-agent-harness --target openclaw --profile 王军
   # 或写入文件:--out ~/.openclaw/nblane-mcp.json
   ```

   输出是一段可合并进 `~/.openclaw/openclaw.json` 的 `mcp.servers` 配置
   (command 自动解析本机 `nblane-mcp`,env 带 `NBLANE_ROOT` 与
   `NBLANE_PROFILE`)。也可以用 `openclaw mcp add` 交互式添加。
3. 验证:

   ```bash
   openclaw mcp list            # 能看到 nblane
   openclaw mcp probe nblane    # 能列出 submit_agent_task_candidate 等工具
   ```

4. 在 OpenClaw 里让 agent 先读 `profile://context`(完整 system prompt)
   或 `profile://summary`(摘要),再开始工作。

## 闭环工作流(重要)

OpenClaw 是执行层,**产出必须进审批队列,由人处置**:

1. agent 读 `agent://tasks` / `agent://task/{task_id}` 领取派单;
2. 执行(调研、写草稿、跑代码……);
3. 完成时调用 `submit_agent_task_candidate`(summary / changed_paths /
   warnings / result_payload);失败或阻塞调 `update_agent_task_status`;
4. 人在 Web UI 的 **Agent Activity** 页审批候选写回;看板任务完成后由人
   触发 crystallize,沉淀为证据。

安全边界(nblane-mcp 的设计保证):MCP 走 stdio 本地进程;工具只写
growth log、inline evidence、interaction 记录、方法草稿与审批队列,
**不能**直接改技能树状态、不能发布公开内容。OpenClaw 本身权限很大,
请只在本地运行,不要把 gateway 暴露到公网,`NBLANE_ROOT` 指向你的
nblane 仓库即可。

## 变更窗口：生产人工执行命令清单（2026-09-20）

以下五项涉及**生产 OpenClaw Gateway（承载活的微信通道）**的变更，按
[深度融合总体方案](../architecture/openclaw-deep-integration.md)的约定只能由人工
在变更窗口执行，AI 一律不得代跑。对应进度表的 L0.2 / L0.4 / L2 生产切换 /
L4 Step 1 / L6 SecretRef。

总则（每项都适用）：

- 所有 `openclaw config` 变更先 `--dry-run`，确认输出后再去掉该参数正式执行；
  OpenClaw config 自带 `.bak` 环，回滚以它兜底。
- 选微信低峰窗口；任何 `openclaw gateway restart` 都会造成秒级微信中断。
- **永不**在自动化或本清单中调 `openclaw doctor --fix`（它会停/重启 Gateway）。
- 下面命令里的只读项（`mcp list`、`automations list --all --json`、`curl /readyz`
  等）可随时执行；标注「执行」的步骤才占用变更窗口。
- 生产路径约定（L6 三树归一）：代码 `/srv/nblane-app/nblane`，数据
  `/srv/nblane-data`，profile 名以实际为准（下文用 `王军` 示例）。

### CW-1 L0.2 接通 nblane MCP（注册 nblane-mcp stdio server）

前置检查（只读）：

```bash
cd /srv/nblane-app/nblane && git status -sb        # 确认生产代码版本
ls -l /srv/nblane-app/nblane/.venv/bin/nblane-mcp  # entry point 必须存在
systemctl --user is-active openclaw-gateway.service
curl -fsS http://127.0.0.1:18789/readyz
openclaw mcp list                                   # 当前应不含 nblane
```

执行：

```bash
cd /srv/nblane-app/nblane
# 1. 生成并核对配置片段（command 必须是绝对路径，env 含 NBLANE_ROOT/NBLANE_PROFILE）
.venv/bin/nblane sync-agent-harness --target openclaw --profile 王军
#    command 形态取决于调用环境的 PATH：能找到 nblane-mcp 时输出其绝对路径，
#    否则回退为 "<venv>/bin/python3 -m nblane.mcp_server"；两种都可用，
#    关键是必须是生产机的绝对路径，NBLANE_ROOT 必须指向 /srv/nblane-data。
# 2. 用 config patch 注入（JSON5 递归合并），先 dry-run：
openclaw config patch --stdin --dry-run <<'JSON5'
{ "mcp": { "servers": { "nblane": {
  "command": "/srv/nblane-app/nblane/.venv/bin/nblane-mcp",
  "env": { "NBLANE_ROOT": "/srv/nblane-data", "NBLANE_PROFILE": "王军" }
} } } }
JSON5
# 3. dry-run 校验通过后，去掉 --dry-run 再执行同一补丁
```

验证（只读）：

```bash
openclaw mcp list                 # 应出现 nblane
openclaw mcp probe nblane         # 应列出 submit_agent_task_candidate 等工具
nblane openclaw doctor --profile 王军   # nblane_mcp_registered 应为 [OK]
```

注意：不要用 `openclaw mcp tools` 列工具——那是设置工具过滤器的命令
（`core/mcp_client_config.py` 的 snippet 已修正为 `mcp probe`）。随后在会话里让
agent 读 `profile://summary`，并在微信里问一个依赖 profile 数据的问题做端到端确认。

回滚：

```bash
openclaw config unset mcp.servers.nblane
```

停机/风险：无 Gateway 重启，`config patch` 热合并；若 patch 后 `mcp list` 仍不可见，
再做一次 `openclaw gateway restart`（秒级微信中断）。风险为 stdio 子进程拉起失败
导致 agent 侧工具不可用，不影响 Gateway 本身。

### CW-2 L0.4 备份调度（git 备份定时化）

nblane 侧**不需要 cron/自动化**：每次写入已由
`core/git_backup.py` 的 `record_change`（`NBLANE_DATA_GIT_AUTOCOMMIT=1` +
`NBLANE_DATA_GIT_AUTOPUSH=1`）写时触发 commit+push。本项要做的是确认这条链路生效，
并把 OpenClaw 侧的整目录备份定时化。

前置检查（只读）：

```bash
git -C /srv/nblane-data remote -v                                  # 应有私有远端
systemctl cat nblane nblane-reader | grep NBLANE_DATA_GIT          # 两个 unit 都应带 =1
git -C /srv/nblane-data log --oneline -3                           # 近期应有 nblane: 提交
openclaw automations list --all --json | grep -i backup            # 当前应无备份调度
```

执行：

```bash
# 1. 先手动验证一次完整备份能产出（归档落盘后移出 ~/.openclaw 到私有加密位置）
openclaw backup create
# 2. 开启 24h 调度（官方语义：重复执行是更新而非重复创建）
openclaw backup enable --every 24h
```

验证（只读）：

```bash
openclaw automations list --all --json | grep -i backup   # 应出现备份调度
nblane openclaw doctor --profile 王军                      # backup_schedule 应为 [OK]
# nblane 侧：在 Web UI 做一次保存，随后：
git -C /srv/nblane-data log --oneline -1                  # 应出现新 commit 且已 push
```

恢复演练（建议同窗口内做一次）：把备份 tar 解到临时目录 +
`openclaw backup verify` + 对数据目录跑 `nblane validate`，全部通过才算闭环。

回滚：备份调度本身无副作用、不产生数据风险，一般无需回滚；确需停用时以
`openclaw backup --help` 列出的停用子命令为准（本仓库未实测停用命令名，不要臆造）。
nblane 侧回滚为去掉 systemd unit 里两个 `NBLANE_DATA_GIT_*` 环境变量并重启服务。

停机/风险：无停机。风险仅为 push 失败——表现为 Web UI warning，不回滚已保存文件
（`core/git_backup.py` 语义），需人工处理远端。

### CW-3 L2 生产自动化切换（automations-as-code 接管）

目标：把 `profiles/王军/assistant/automations.yaml`（声明源）对账到生产 Gateway，
替换掉 prompt 里写死绝对路径的旧自动化。纳管语义（`core/openclaw_automations.py`）：

- nblane 只管理 `declarationKey` 以 `nblane:` 开头的任务；旧
  `personal-assistant:*` 属外部 key，一律 `skip_foreign`，**sync 永远不会碰它**。
- 模板声明的是新 `nblane:*` key，执行后与旧任务**并存**。二选一：
  - 方案 A（推荐，灰度）：新 `nblane:*` 与旧任务并行一个周期，验证后在 OpenClaw
    侧手工停用旧任务（`--prune` 不会删外部 key，删旧任务是独立的人工动作）。
  - 方案 B（原地纳管）：在 `automations.yaml` 用旧 key 声明并加 `adopt: true`，
    sync 以 edit 方式接管；这是逐条显式 opt-in，未标 adopt 的外部 key 会在加载时
    报错而不是被静默接管。

前置检查（只读；`${WEIXIN_OWNER_ID}` 未设置会导致声明加载报错，属预期保护）：

```bash
export WEIXIN_OWNER_ID='<WEIXIN_OWNER_ID>'   # 或确认已在 /srv/nblane-data 侧 .env
cd /srv/nblane-app/nblane
.venv/bin/nblane openclaw automations sync 王军        # 默认 dry-run，只打印计划
openclaw automations list --all --json                 # 记录现有任务快照（回滚依据）
```

执行序列：

```bash
cd /srv/nblane-app/nblane
# 1. 只读对账，三项（语料/技能/自动化）有漂移即非零退出
.venv/bin/nblane openclaw sync --check
# 2. 全量 dry-run：打印技能/语料差异、config patch（含 MCP 注入）全文、自动化计划
.venv/bin/nblane openclaw install --dry-run
#    ——人工逐项审阅输出。两个历史核对点已修复（2026-09-20），降级为常规确认：
#    a) config patch 里不应出现未替换的 ${...} 字面量：install 的 overlay 步骤
#       现在与 automations.yaml 加载器共用同一 ${VAR} 替换实现
#       （core/openclaw_automations.py 的 substitute_env_text），未设置的
#       变量会在 patch 前直接报错中止，不会把字面量写进配置；
#    b) 模板 openclaw.overlay.json5 的键层级已对齐本指南实测的
#       agents.defaults.* 路径（agents.defaults.model.primary、
#       agents.defaults.heartbeat 等），dry-run 补丁应落在这些路径上；
#       仍有单测（tests/test_openclaw_install.py）防止再次漂移。
# 3. 确认后应用（幂等，可重跑）
.venv/bin/nblane openclaw install --apply
```

或分步执行（等价）：

```bash
.venv/bin/nblane openclaw sync                          # 渲染语料+同步技能；自动化仍只出计划
.venv/bin/nblane openclaw automations sync 王军 --apply  # 应用自动化 add/edit（不含删除）
```

验证（只读 + 一次实跑）：

```bash
.venv/bin/nblane openclaw doctor --profile 王军          # automations_in_sync 应一致
openclaw automations list --all --json
# 手动实跑一次每日计划确认真实投递（消耗 Token）：
openclaw automations run <实际ID> --wait --expect-final --wait-timeout 8m --json
```

回滚：旧 `personal-assistant:*` 任务全程未被改动，即为天然回滚点——停用/删除新
`nblane:*` 任务即可恢复原状。确需删除已下线的 `nblane:` 任务：先从声明文件移除，
再 `nblane openclaw automations sync 王军 --apply --prune`（prune 只删 `nblane:`
前缀及已 adopt 的 key）。config overlay 的回滚用 `openclaw config unset <键>` 或
`.bak` 环。

停机/风险：无 Gateway 重启；`install --apply` 内的插件安装
（`openclaw plugins install --force`）与 `config patch` 均为热操作。主要风险是
overlay 键值与生产 schema 不符——务必在第 2 步审阅 dry-run 打印的补丁全文。

### CW-4 L4 Caddy `/openclaw` 反代（Control UI 子路径，新标签打开）

背景：iframe 内嵌已被上游明确否决（issue #47565 closed as not-planned，
`X-Frame-Options: DENY` + CSP `frame-ancestors 'none'` 无配置开关），本方案是
**同域子路径反代 + 新标签打开**，不剥离任何安全响应头。参照
[腾讯云部署文档](deployment-tencent-cloud.md)的既有 Caddy 写法（`handle`，不用
`handle_path`；WebSocket upgrade Caddy 自动处理）。

前置检查（只读）：

```bash
ss -ltn | grep 18789                       # 应只有 127.0.0.1:18789
curl -fsS http://127.0.0.1:18789/readyz
sudo caddy validate --config /etc/caddy/Caddyfile   # 变更前基线必须已通过
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak-$(date +%Y%m%d)
```

执行：

1. 编辑 `/etc/caddy/Caddyfile`，在兜底 `reverse_proxy 127.0.0.1:8501` 之前加：

   ```caddyfile
       handle /openclaw/* {
           reverse_proxy 127.0.0.1:18789
       }
   ```

2. 校验并生效：

   ```bash
   sudo caddy validate --config /etc/caddy/Caddyfile
   ```

3. Gateway 侧配置（走 `config patch`，先 dry-run）：

   ```bash
   openclaw config patch --stdin --dry-run <<'JSON5'
   { "gateway": { "controlUi": { "basePath": "/openclaw" },
                  "publicOrigin": "https://<域名>/openclaw" } }
   JSON5
   # dry-run 通过后去掉 --dry-run 再执行同一补丁
   ```

4. 生效：

   ```bash
   sudo systemctl reload caddy        # 优雅重载，无中断
   openclaw gateway restart           # basePath 改动需重启 Gateway（秒级微信中断）
   ```

验证（只读）：

```bash
curl -sI https://<域名>/openclaw/     # 期望 200 text/html
curl -fsS http://127.0.0.1:18789/readyz
```

随后桌面浏览器打开 `https://<域名>/openclaw/`，粘贴一次 token 完成 WS 握手登录，
确认控制台可用后再用手机访问；nblane SPA `/assistant` 页的「打开控制台」按钮
新标签指向同一地址。

回滚：

```bash
# 1. 从 Caddyfile 删除 handle /openclaw/* 块（或恢复 Caddyfile.bak-<date>）
sudo caddy validate --config /etc/caddy/Caddyfile && sudo systemctl reload caddy
# 2. 撤掉 Gateway 侧两个键并重启
openclaw config unset gateway.controlUi.basePath
openclaw config unset gateway.publicOrigin
openclaw gateway restart
```

停机/风险：Caddy reload 无中断；一次 Gateway restart 有秒级微信中断。风险为
basePath 配错导致 Control UI 静态资源 404——先桌面验证再上手机。

### CW-5 L6 密钥 SecretRef 迁移（openclaw.json 明文 → SecretRef）

现状（本指南「已知但未在本次修改的安全提示」已记录）：`openclaw.json` 中仍有明文
Gateway token 与 rightcode API key；notify 链路的 `cron.webhookToken` 同样如此。
nblane 侧 `NBLANE_OPENCLAW_HOOK_TOKEN` 只从 `/srv/nblane-data/.env` / 环境读取
（`core/notify.py`，0600 权限），**不在**本次 SecretRef 范围内，但取值必须与
迁移后的 Gateway 端保持一致。

前置检查（只读）：

```bash
openclaw secrets audit --check    # 列出当前明文项，作为迁移清单
openclaw config validate --json
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.pre-secretref
```

执行：

```bash
openclaw secrets configure    # 交互式配置 SecretRef provider（env provider 起步）
openclaw secrets apply        # 把明文项替换为 SecretRef 引用
openclaw gateway restart      # 秒级微信中断
```

验证（只读 + 一次真实推送）：

```bash
openclaw secrets audit --check    # 应无明文残留
openclaw status --json
/srv/nblane-app/nblane/.venv/bin/nblane notify --dry-run 'SecretRef 迁移验证'
# dry-run 通过后发一条真实 notify，确认 webhook token 链路在迁移后仍通
```

回滚：

```bash
cp ~/.openclaw/openclaw.json.pre-secretref ~/.openclaw/openclaw.json
openclaw gateway restart
```

迁移验证全部通过后再删除 `openclaw.json.pre-secretref`（或移入私有加密备份）；
在此之前**不要删除任何可用认证**。

停机/风险：一次 Gateway restart。主要风险是 SecretRef 引用写错导致 Gateway
认证失败、微信通道断连——因此必须先 `audit --check` 摸清明文项、保留回滚副本、
低峰执行。

## 相关文档

- OpenClaw 官方安装:[docs.openclaw.ai/install](https://docs.openclaw.ai/install)
- Node 版本与 SQLite 门槛:[docs.openclaw.ai/install/node](https://docs.openclaw.ai/install/node)
- 腾讯微信插件:[npm @tencent-weixin/openclaw-weixin](https://www.npmjs.com/package/@tencent-weixin/openclaw-weixin)
- nblane 安装与 LLM:`docs/zh/guides/setup.md`
- Agent Activity 审批页:`docs/zh/guides/agent-activity.md`
- 看板:`docs/zh/guides/kanban.md`
- MCP server 实现:`src/nblane/mcp_server.py`(资源与工具清单以源码为准)
