---
status: active
owner: engineering
last_verified: 2026-10-07
source_of_truth: true
---

# 整机迁移 Runbook

本文讲「把整套 nblane（代码 + 数据 + 助手）从旧服务器迁到新服务器」，按执行顺序列出每一步和验证方法。模板不在这里重复：

- systemd、Caddy、端口与服务表：[腾讯云部署](deployment-tencent-cloud.md)
- OpenClaw 网关、微信、服务账号凭据：[OpenClaw 运维](openclaw-ops.md)
- 代理：[Mihomo 代理部署](mihomo-deployment.md)

密钥、域名、Owner ID 一律用占位符，真实值只放新机的私有文件里。

## 1. 迁移总览

```text
┌─ 代码仓（GitHub，git clone）        /srv/nblane-app/nblane
│    └ 前端产物随仓库提交，生产不跑 npm build
├─ 数据仓（私有 Git，git clone）      /srv/nblane-data
│    └ profiles/ schemas/ auth/users.yaml；.env(0600) 不进 git
├─ 大资产（不进 Git，rsync）          /srv/nblane-assets
├─ 助手工作区（私有 Git，git clone）  /srv/agent-data/openclaw/workspace
├─ OpenClaw 状态（tar 整目录）        ~/.openclaw（配置、token、模型 key、插件、微信登录态、定时任务）
└─ 系统层（按模板重建，不拷贝）
     ├ 系统 unit：nblane-reader(8502) / nblane-web-api(8504)
     ├ 用户 unit：openclaw-gateway、nblane-grobid、nblane-workshop、nblane-backup.timer
     └ Caddy：主站（可选 spa 子域名）
```

三条原则：

- 数据仓是事实源：`NBLANE_ROOT=/srv/nblane-data`。不要从旧机代码仓里拷 `profiles/`。
- 凭证不靠 git：清单见第 9 节。
- 旧机先不下线：DNS 切换后保留 48 小时观察，见第 11 节。

## 2. 新机准备

- Python ≥ 3.11、Git、rsync、tmux；创建 `nblane` 运行用户并开启 linger：`sudo loginctl enable-linger <服务用户>`。
- Caddy：安全组只放 80/443（22 仅管理员 IP）。
- Podman（用 GROBID 时）、Node（用助手时，版本要求见 [OpenClaw 运维](openclaw-ops.md#前置条件)）。
- 需要出站代理时先装 mihomo，否则 clone 和 pip 可能卡住。

```bash
python3 -c 'import sys; assert sys.version_info >= (3, 11)'
command -v git rsync tmux caddy
ss -ltn | awk '/8502|8504|8070|18789/'   # 装机前应为空
```

## 3. 代码仓

```bash
sudo -u nblane git clone https://github.com/<org>/nblane.git /srv/nblane-app/nblane
cd /srv/nblane-app/nblane
sudo -u nblane python3 -m venv .venv
sudo -u nblane .venv/bin/pip install -e .
```

- 代理 + 国内 pip 镜像：shell 全局挂着 `http_proxy` 时，把镜像域名加进 `no_proxy` / `NO_PROXY`。
- 不要在新机跑 `npm run build`，以仓库里的产物为准。

```bash
.venv/bin/nblane --help >/dev/null && echo cli-ok
.venv/bin/python -c 'import socksio; print("socksio ok")'
```

## 4. 数据仓

```bash
sudo -u nblane git clone <私有 nblane-data 仓地址> /srv/nblane-data
sudo -u nblane NBLANE_ROOT=/srv/nblane-data /srv/nblane-app/nblane/.venv/bin/nblane validate
```

`.env` 在第 9 节单独重建。

## 5. 大资产

```bash
sudo rsync -aH --info=progress2 <旧机用户>@<旧机地址>:/srv/nblane-assets/ /srv/nblane-assets/
sudo chown -R nblane:nblane /srv/nblane-assets
sha256sum /srv/nblane-assets/research/profiles/<profile>/papers/<某个.pdf>   # 新旧机各算一次对比
```

## 6. systemd 系统 unit

按 [腾讯云部署「systemd」](deployment-tencent-cloud.md#systemd) 的模板落 `nblane-reader` 和 `nblane-web-api` 两个 unit，代码路径与本机检出一致。不要迁 `nblane.service`（Streamlit 已删除）。

两个 unit 都不能漏：`NBLANE_ROOT`、`NBLANE_AUTH_FILE`、`NBLANE_READER_API_BASE=0`、`EnvironmentFile=-/srv/nblane-data/.env`。8504 还要 `NBLANE_DATA_GIT_AUTOCOMMIT=1` / `NBLANE_DATA_GIT_AUTOPUSH=1`，以及 drop-in 三件（代理、`PATH` 含 openclaw、`NBLANE_TRUST_PROXY_HEADERS=1`，最后一项等 Caddy 就位后再开）。

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nblane-reader nblane-web-api
systemctl is-active nblane-reader nblane-web-api
curl -fsS http://127.0.0.1:8504/api/v1/health
```

## 7. Caddy

按 [腾讯云部署「HTTPS 反向代理」](deployment-tencent-cloud.md#https-反向代理) 写站点块：8502 只承接 `/reader/*`、`/paper-library*`、`/api/research/*`、`/auth/session*`，`/openclaw` 两条（精确 + 通配）到 18789，其余全部到 8504。

- DNS：为域名建 A 记录指向新机。DNS 未生效时证书申请会退避，就位后 `sudo systemctl restart caddy` 可立即重试。
- 网关侧 `/openclaw` 的四项配置随 `~/.openclaw` 一起迁来；域名变了要按 [OpenClaw 运维](openclaw-ops.md#网关与-systemd) 重配。

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
curl -sI https://<域名>/              # 200（SPA）
curl -sI https://<域名>/openclaw/     # 200 text/html（用助手时）
```

## 8. 助手（OpenClaw）

以运行网关的同一用户执行。

1. OpenClaw 状态整目录迁移（含 token、模型 key、微信登录态、插件、定时任务）：

   ```bash
   # 旧机
   tar czf /tmp/openclaw-state.tgz -C ~ .openclaw
   # 经私有渠道传到新机后
   tar xzf /tmp/openclaw-state.tgz -C ~
   ```

   不要把该目录或打包件提交到任何仓库。

2. 工作区：从私有远端 clone 到 `/srv/agent-data/openclaw/workspace`，并让 `~/.openclaw/workspace` 软链到它；或从旧机 rsync。确认 `openclaw.json` 里的 `agents.defaults.workspace` 指向新路径。
3. 安装同版本 OpenClaw 并装网关用户服务（`openclaw onboard --install-daemon` 或 `openclaw gateway install`）。
4. 服务账号凭据：`~/.config/nblane/api.env`（或网关 drop-in），写法见 [OpenClaw 运维 · 服务账号凭据](openclaw-ops.md#服务账号凭据)。
5. 接入：在设置页「助手与备份」点「接入 nblane」，或 `nblane openclaw install --profile <name> --apply`。它同步技能、生成 `nblane_api`、渲染语料、装 weixin-task-bridge；不注册 MCP，发现旧的 MCP 注册会移除。
6. 定时任务：归 OpenClaw 管，随 `~/.openclaw` 一起走。这里只核对，不做同步：

   ```bash
   openclaw automations list --all --json
   openclaw config get agents.defaults.model --json
   openclaw models status --json      # 模型 key 随状态迁来，但供应商可用性要重新确认
   ```

   每日复盘默认关闭，迁完不要误开。

7. 备份定时器：在「数据备份」卡片重新安装 `nblane-backup.timer`，确认两个目标都有远端。

```bash
systemctl --user is-active openclaw-gateway.service
curl -fsS http://127.0.0.1:18789/readyz
openclaw plugins inspect weixin-task-bridge --runtime --json   # loaded + activated
~/.openclaw/workspace/skills/bin/nblane_api summary
nblane openclaw doctor --profile <name>
```

## 9. 凭证重建清单

| 凭证 | 存放位置 | 迁移方式 |
|------|---------|---------|
| `LLM_API_KEY` 等 AI 连接 | `/srv/nblane-data/.env`（0600） | 参照 `.env.example` 重写，或在「设置 → AI 服务」重新填 |
| `NBLANE_READER_TOKEN_SECRET` | 同上 | 沿用旧值或重新生成；8502 和 8504 读同一个文件 |
| `NBLANE_AUTH_COOKIE_SECURE=1` | 同上 | HTTPS 环境必须 |
| `NBLANE_OPENCLAW_HOOK_TOKEN` | 同上 | 须与网关 `cron.webhookToken` 一致 |
| `auth/users.yaml`（账号、密码哈希、助手 token 哈希） | `/srv/nblane-data/auth/`，不进 git | 从整机备份拷贝，保持 0600 |
| `NBLANE_OPENCLAW_API_TOKEN`（或旧的 `_PASSWORD`） | `~/.config/nblane/api.env` 或网关 drop-in | 明文不在任何仓库；拷贝该文件，或在账号管理里重新生成 token |
| 网关 token、模型 key | `~/.openclaw/openclaw.json` | 随状态目录迁移 |
| 微信登录态 | `~/.openclaw` 内 | 随状态目录；失效则 `openclaw channels login --channel openclaw-weixin` 重新扫码 |
| 备份部署密钥 | `~/.ssh/nblane_backup_<目标>_ed25519` | 拷贝，或在设置页重新生成并更新仓库 Deploy keys |
| Codex 登录态 | `NBLANE_CODEX_HOME`（默认 `~/.codex`） | 新机重新 `codex login` |

```bash
sudo chown nblane:nblane /srv/nblane-data/.env
sudo chmod 600 /srv/nblane-data/.env
```

## 10. 验收清单

- [ ] `nblane validate` 全绿；`nblane openclaw doctor --profile <name>` 无失败项（用助手时）。
- [ ] `systemctl is-active nblane-reader nblane-web-api` 两个 active。
- [ ] `https://<域名>/` 显示登录页，登录后首页星图正常。
- [ ] 研究台的论文库和阅读器 iframe 不空白。
- [ ] 做一次真实打卡，`git -C /srv/nblane-data log --oneline -1` 出现新提交且已推送。
- [ ] 在微信里让助手打一次卡，助手页「最近操作」出现记录并能撤销。
- [ ] 手动触发一次每日计划，确认微信收到（消耗 Token）。
- [ ] 控制台 `https://<域名>/openclaw/` 粘贴 token 后可用。

## 11. 旧机下线顺序

1. DNS 切到新机，新机 Caddy 完成证书签发。
2. 观察 48 小时：旧机服务保持运行但不写入；确认新机验收全部通过、推送正常、定时任务按时投递。
3. 旧机停服务：

   ```bash
   sudo systemctl disable --now nblane-reader nblane-web-api
   systemctl --user disable --now openclaw-gateway nblane-backup.timer
   ```

   停网关会断开微信，确认新机已接管后再执行。
4. 旧机数据仓保留为只读历史，不再推送。

## 外部依赖登记

`pip install -e .` 之外的一切依赖在这里登记。新增系统级依赖、端口或服务时同步更新本表和 [端口与服务](deployment-tencent-cloud.md#端口与服务)。

| 依赖 | 用途 | 安装方式 | 位置 |
|------|------|---------|------|
| Node.js / npm | 前端构建、e2e、OpenClaw | 系统包或 nvm | `src/nblane/web_ui/frontend/package.json`、根 `package.json` |
| tmux | dev 服务、车间终端会话 | apt | — |
| ttyd 1.7.7（静态二进制） | 车间网页终端 | 设置 → 车间终端一键安装（GitHub release，sha256 固定） | `~/.local/share/nblane/workshop/bin` |
| Podman | 无 root 运行 GROBID | apt | `~/.config/containers/systemd/` |
| GROBID 0.9.0-crf | PDF 结构化抽取 | 设置 → 本地服务一键安装 | Podman 镜像 |
| llama.cpp 运行时 + GGUF | 本地翻译模型 | 设置 → 本地服务一键安装 | `~/.local/share/nblane/local-models/` |
| OpenClaw（固定版本） | 助手网关 | 设置 → 助手与备份，或 npm 全局 | `core/openclaw_setup.py` `PINNED_VERSION` |
| `@tencent-weixin/openclaw-weixin` | 微信通道 | 设置 → 安装微信渠道 | OpenClaw 插件 |
| Codex CLI | 可选 AI 执行器 | `nblane codex install` | npm 全局 |
| mihomo | 出站代理（本机网络工具，不是 nblane 配置） | 见 mihomo-deployment.md | 根目录 `config.yaml` |
| 星图字体（思源宋体、文楷、一点明体、IM Fell） | 星图标签 | 子集化后入库 | `src/nblane/web_ui/frontend/src/starmap/assets/` |
| 星官数据 `asterisms.json` | 首页星图星官形状 | 已入库；拓扑取自 Stellarium skycultures/chinese（CC BY-SA 4.0），星位取自 Hipparcos（CDS I/239） | `src/nblane/web_ui/frontend/src/starmap/data/`（含 README） |

打包纪律：安装动作优先写成幂等脚本或设置页一键操作；个人数据（非 template 的 `profiles/`、`.env`、密钥）永不进包。
