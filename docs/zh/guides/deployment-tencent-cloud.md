---
status: active
owner: engineering
last_verified: 2026-10-07
source_of_truth: true
---

# 腾讯云部署

公网入口是域名 + HTTPS（Caddy），应用内账号登录，数据仍是纯文件 + 私有 Git 仓库。本机开发见 [本机安装](setup.md)，换机器见 [整机迁移](migration.md)。

## 端口与服务

本表是端口与服务的唯一登记处，其他文档链接到这里。所有服务只监听 `127.0.0.1`，公网只经 Caddy 的 80/443。

| 端口 | 服务 | 托管方式 | 作用 |
|------|------|----------|------|
| 443 / 80 | Caddy | 系统 unit `caddy` | HTTPS 入口，按路径分流 |
| 8504 | `nblane-web-api.service`（`uvicorn nblane.web_api:app`） | 系统 unit | SPA 页面 + `/api/v1`；同时反代车间终端 `/terminal/` |
| 8502 | `nblane-reader.service`（`uvicorn nblane.web_reader_api:app`） | 系统 unit | 论文库、阅读器（SPA iframe 嵌入）、登录态交接 `/auth/session` |
| 8070 | GROBID `nblane-grobid` | 用户级 Podman Quadlet | PDF 结构化抽取（可选） |
| 8505 | `llama-server` | 8502 / 8504 按需拉起 | 本地翻译模型（可选），空闲 300 秒释放 |
| 7668 | ttyd `nblane-workshop` | 用户级 unit | 车间网页终端（可选），只经 8504 `/terminal/` 访问，需管理员登录 |
| 18789 | OpenClaw 网关 `openclaw-gateway` | 用户级 unit | 助手（可选），控制台经 Caddy `/openclaw` |
| — | `nblane-backup.timer` | 用户级 timer | 每天 03:30 `nblane backup run` |

端口来源：`scripts/dev-web.sh`、`core/grobid_service.py`、`core/ai/local_models.py`、`core/workshop_service.py`、`core/openclaw_setup.py`、`core/backup_targets.py`。开发隔离端口（18502 / 18504 / 18070 / 19789）见 [本机安装](setup.md)。

用户级服务都要求服务用户开启 linger：`sudo loginctl enable-linger <服务用户>`。

## 目录布局

```text
/srv/nblane-app/nblane   代码（git clone，editable 安装）
/srv/nblane-data         私有数据仓库：profiles/ schemas/ auth/users.yaml .env(0600)
/srv/nblane-assets       大文件资产，不进 Git，如 research/ 下的论文 PDF
/srv/agent-data          助手工作区（独立私有 git），见 OpenClaw 运维
```

代码用 git 部署，不用 rsync / scp 裸拷贝：

```bash
sudo -u nblane git clone https://github.com/<org>/nblane.git /srv/nblane-app/nblane
cd /srv/nblane-app/nblane
sudo -u nblane python3 -m venv .venv
sudo -u nblane .venv/bin/pip install -e .
```

`git log` 能确认线上版本，`git status` 能发现线上手工改动。生产本地无须入库的目录写进 `.git/info/exclude`，不要改仓库的 `.gitignore`。

论文 PDF 原件不进 `profiles/`。profile 里只存 `papers/<sha>-name.pdf` 这样的相对 asset ref，迁移时整体平移 `/srv/nblane-assets` 即可。

```bash
sudo mkdir -p /srv/nblane-assets/research
sudo chown -R nblane:nblane /srv/nblane-assets
```

### 账号

第一个管理员手写 `auth/users.yaml`（参考 `auth/users.example.yaml`，密码哈希用 `nblane auth hash-password`），之后的加人、改密码、停用都在「设置 → 账号管理 / 我的账号」里做。

`auth/` 不进数据仓库 git：在 `/srv/nblane-data/.gitignore` 里写 `auth/`，文件保持 0600，靠整机备份保存。网页写账号时也不会触发自动提交。

- `role: admin`：管理员，可访问所有档案和系统设置。
- `role: member` + `profile: <name>`：本人，只能访问自己的档案。
- `agent: true`：助手服务账号（如 `openclaw`），写入按 [助手](assistant.md) 的规则处理。

## 更新代码

```bash
cd /srv/nblane-app/nblane
sudo -u nblane git fetch origin
sudo -u nblane git status -sb          # 应与 origin/main 同步；有本地改动先排查
sudo -u nblane git pull --ff-only      # 只快进
sudo systemctl restart nblane-reader nblane-web-api
```

- editable 安装下只改代码不用重装；依赖变了再跑 `.venv/bin/pip install -e .`。用 `uv sync` 时同样要在重启前完成。
- 走 SOCKS 代理时必须有 `httpx[socks]`（已在依赖里），否则外部请求报 `Using SOCKS proxy, but the 'socksio' package is not installed.`。
- 回滚：`git checkout <旧 commit>` 后重启两个服务。

### 前端产物

前端是预构建的，生产不跑 `npm run build`。SPA（`src/nblane/web_ui/static/`）和论文库组件（`src/nblane/paper_library_component/frontend/static/`）的产物都随仓库提交。只改源码不重新构建，生产看不到变化。

- Vite 用内容哈希命名产物。提交时把删掉的旧哈希文件、新文件和 `index.html` 一起提交，漏一个就会 404 或加载旧版。
- 改了 SPA 重启 `nblane-web-api`；改了论文库组件重启 `nblane-reader`。
- 验证时先硬刷新，或用 DevTools Network 对比实际加载的哈希文件名。

## systemd

两个系统 unit 共用 `/srv/nblane-data/.env`（0600）。先生成 Reader token secret：

```bash
printf 'NBLANE_READER_TOKEN_SECRET=%s\n' "$(openssl rand -hex 32)" | sudo tee -a /srv/nblane-data/.env
sudo chown nblane:nblane /srv/nblane-data/.env
sudo chmod 600 /srv/nblane-data/.env
```

HTTPS 生产环境在同一文件里加 `NBLANE_AUTH_COOKIE_SECURE=1`。

### Reader API（8502）

`/etc/systemd/system/nblane-reader.service`：

```ini
[Unit]
Description=nblane Paper Reader API
After=network.target

[Service]
Type=simple
User=nblane
WorkingDirectory=/srv/nblane-app/nblane
Environment=NBLANE_ROOT=/srv/nblane-data
Environment=NBLANE_AUTH_FILE=/srv/nblane-data/auth/users.yaml
Environment=UI_LANG=zh
Environment=LLM_REPLY_LANG=zh
Environment=NBLANE_RESEARCH_ASSET_ROOT=/srv/nblane-assets/research
Environment=NBLANE_GROBID_URL=http://127.0.0.1:8070
Environment=NBLANE_CODEX_BIN=/home/nblane/.local/bin/codex
Environment=NBLANE_CODEX_HOME=/home/nblane/.codex
Environment=NBLANE_READER_API_BASE=0
EnvironmentFile=-/srv/nblane-data/.env
# 任务状态（搜索 / 翻译 / AI 流）在单进程内存中，禁止多 worker。
ExecStart=/srv/nblane-app/nblane/.venv/bin/uvicorn nblane.web_reader_api:app --host 127.0.0.1 --port 8502 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- `--workers 1`：多 worker 下 start 与 poll / SSE / cancel 会落到不同进程，约半数请求 404（如 `search job not found`）。
- `NBLANE_READER_API_BASE=0`：同源哨兵。SPA 拿到的 iframe 地址不含 host，浏览器走同源相对路径，由 Caddy 分流到 8502。漏配会回退 `http://127.0.0.1:8502`，公网浏览器访问不到，论文库和阅读器整片空白。
- Reader 不继承 8504 的语言变量，`UI_LANG` / `LLM_REPLY_LANG` 两个 unit 都要写。
- 论文库的 Codex 搜索需要能找到 Codex CLI。systemd 默认 `PATH` 通常不含 `~/.local/bin`，用 `NBLANE_CODEX_BIN` / `NBLANE_CODEX_HOME` 写绝对路径；否则 trace 里出现 `codex_not_found`。
- 大论文全文翻译可放宽预算（drop-in）：`NBLANE_READER_TASK_TIMEOUT_SECONDS=3600`、`NBLANE_PAPER_TRANSLATION_MODEL_TIMEOUT_SECONDS=300`。走 SOCKS 代理时保留默认的 `NBLANE_STREAM_PAPER_TRANSLATION=1`。

### SPA 后端（8504）

`/etc/systemd/system/nblane-web-api.service`：

```ini
[Unit]
Description=nblane Web API (SPA backend)
After=network.target nblane-reader.service

[Service]
Type=simple
User=nblane
WorkingDirectory=/srv/nblane-app/nblane
Environment=NBLANE_ROOT=/srv/nblane-data
Environment=NBLANE_AUTH_FILE=/srv/nblane-data/auth/users.yaml
Environment=UI_LANG=zh
Environment=LLM_REPLY_LANG=zh
Environment=NBLANE_DATA_GIT_AUTOCOMMIT=1
Environment=NBLANE_DATA_GIT_AUTOPUSH=1
Environment=NBLANE_RESEARCH_ASSET_ROOT=/srv/nblane-assets/research
Environment=NBLANE_GROBID_URL=http://127.0.0.1:8070
Environment=NBLANE_READER_API_BASE=0
EnvironmentFile=-/srv/nblane-data/.env
# 登录限流是单进程内存实现，禁止多 worker。
ExecStart=/srv/nblane-app/nblane/.venv/bin/uvicorn nblane.web_api:app --host 127.0.0.1 --port 8504 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- 8504 是完整写路径，必须配 `NBLANE_DATA_GIT_AUTOCOMMIT=1` / `NBLANE_DATA_GIT_AUTOPUSH=1`，否则保存不产生备份提交。
- `--workers 1`：多 worker 会把登录失败计数分散到不同进程，限流失效。

运行期修正建议放 drop-in（`/etc/systemd/system/nblane-web-api.service.d/`），不改 unit 主体：

```bash
sudo install -d /etc/systemd/system/nblane-web-api.service.d

# 出站代理（如需）：见 mihomo-deployment.md「让生产 systemd 服务走代理」，含成对的 no_proxy/NO_PROXY。

# PATH：助手页要在服务端调用 openclaw，它通常装在用户级 npm-global。
# systemd Environment= 不做 shell 展开，写绝对路径。漏配时助手页显示「本机未安装」。
sudo tee /etc/systemd/system/nblane-web-api.service.d/20-path.conf >/dev/null <<'EOF'
[Service]
Environment=PATH=/home/nblane/.local/npm-global/bin:/home/nblane/.local/bin:/usr/local/bin:/usr/bin:/bin
EOF

# 信任反代头：只在 Caddy 就位、安全组只放 80/443 之后开启。
sudo tee /etc/systemd/system/nblane-web-api.service.d/30-trust-proxy.conf >/dev/null <<'EOF'
[Service]
Environment=NBLANE_TRUST_PROXY_HEADERS=1
EOF
```

`NBLANE_TRUST_PROXY_HEADERS=1` 让应用取 `X-Forwarded-For` 首跳作为登录限流的客户端 IP（同一 IP + 用户名 60 秒内失败 5 次即 429）。8504 直接可达时开启等于允许伪造限流身份。不要改用 uvicorn `--proxy-headers`。

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nblane-reader nblane-web-api
systemctl is-active nblane-reader nblane-web-api
curl -fsS http://127.0.0.1:8504/api/v1/health
```

## HTTPS 反向代理

Caddy。8502 只承接 SPA 实际用到的三组路径，其余全部（SPA 页面、`/api/v1/*`、`/terminal/*`）走 8504：

```caddyfile
(nblane_routes) {
    # 阅读器页面与其 API（/reader/view、/reader/assets、/reader/api/...）
    handle /reader/* {
        reverse_proxy 127.0.0.1:8502
    }

    # 论文库页面、静态资源与 API
    handle /paper-library* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /api/research/* {
        reverse_proxy 127.0.0.1:8502
    }

    # 登录态交接：SPA 用隐藏表单 POST /auth/session，再跳 /auth/session-ok
    handle /auth/session* {
        reverse_proxy 127.0.0.1:8502
    }

    # OpenClaw 控制台（可选）。精确匹配与通配两条都要写，
    # 只写通配时无尾斜杠的 /openclaw 会落到 8504，WebSocket 握手失败。
    handle /openclaw {
        reverse_proxy 127.0.0.1:18789
    }

    handle /openclaw/* {
        reverse_proxy 127.0.0.1:18789
    }

    # SPA + /api/v1 + /terminal/
    reverse_proxy 127.0.0.1:8504
}

your-domain.com {
    import nblane_routes
}

spa.your-domain.com {
    import nblane_routes
}
```

- 一律用 `handle`，不要用 `handle_path`：后者会剥掉 FastAPI 需要的 `/reader`、`/paper-library` 等前缀。
- 漏了 `/auth/session*`，iframe 引导返回 404/401，论文库整片空白。
- `/openclaw` 还需要网关侧四项配置，见 [OpenClaw 运维](openclaw-ops.md#网关与-systemd)。
- 车间终端 `/terminal/*` 由 8504 鉴权后反代到 ttyd，Caddy 不需要单独配置，也不要再加 basic_auth。
- 第二个站点只在你用两个域名时需要；单域名删掉即可。

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

日志注意：Reader token 和兼容形式的 handoff 仍可能出现在 URL query 里，会进入 Caddy 访问日志和浏览器历史。访问日志权限要受控、定期轮转，不要送进公网可达的日志服务。Reader 的登录面应用层没有限流，可在 Caddy 给 `/auth/*` 加 `rate_limit` 插件或用 fail2ban 兜底。

## GROBID（可选）

管理员在「设置 → 系统 → 本地服务」的 GROBID 卡片点「安装并启动」。nblane 用服务用户自己的 Podman 拉取固定镜像 `docker.io/grobid/grobid:0.9.0-crf`，写 Quadlet `~/.config/containers/systemd/nblane-grobid.container`，交给 `systemd --user` 运行，只监听 `127.0.0.1:8070`。同一张卡片可启停、看日志和内存，并切换「PDF 结构后端」（自动 / GROBID / 仅 PyMuPDF）。

一次性准备（需要 sudo）：

```bash
sudo apt-get install -y podman
sudo loginctl enable-linger <服务用户>
grep <服务用户> /etc/subuid /etc/subgid      # 无 root 容器需要的 ID 映射
```

- 镜像约 1.7 GB，走服务的 `https_proxy` 拉取。
- 「PDF 结构后端」写在 `~/.local/share/nblane/grobid/settings.json`，优先于 unit 里的 `NBLANE_RESEARCH_PDF_BACKEND`，所以 8502 和 8504 总是一致。
- 运行约占 1.3–2.7 GB 内存，首次启动 30–60 秒。不导入论文时可以停掉。
- 维护：`systemctl --user status nblane-grobid`、`journalctl --user -u nblane-grobid -f`、`podman ps`。
- 不部署 GROBID 时设 `NBLANE_RESEARCH_PDF_BACKEND=pymupdf`（或 `NBLANE_GROBID_URL=off`）。只留空 `NBLANE_GROBID_URL` 不会禁用，会回退默认地址继续探测。

PyMuPDF 是默认本地 PDF 后端，采用 AGPL / 商业双许可。闭源或商业部署要确认 AGPL 义务。

## 本地翻译模型（可选）

管理员在「设置 → 系统 → 本地服务」安装和启用，不用改 systemd 或 `.env`。用户侧说明见 [研究台](research.md)。

- 下载固定版本的 llama.cpp 运行时（GitHub）和 GGUF（Hugging Face），校验 SHA-256，支持续传。走服务的 `https_proxy`；没有代理时可设 `NBLANE_HF_ENDPOINT=https://hf-mirror.com`。安装进度只在 8504 内存里，重启丢进度条，重新点「安装」会续传。
- 文件默认在 `~/.local/share/nblane/local-models/`，`NBLANE_LOCAL_MODELS_DIR` 可改；8502 和 8504 必须看到同一目录。
- 运行：首次翻译时拉起 `llama-server`，监听 `127.0.0.1:8505`（`NBLANE_LOCAL_MT_PORT`），空闲 300 秒（`NBLANE_LOCAL_MT_IDLE_SECONDS`）后释放。1.8B 约占 2.1 GB 内存。

## 车间终端与助手（可选）

- 车间终端：「设置 → 系统 → 车间终端」一键安装 ttyd，用独立 tmux socket，unit `nblane-workshop`。说明见 [车间](workshop.md)。
- 助手：OpenClaw 网关、微信通道、服务账号凭据见 [OpenClaw 运维](openclaw-ops.md)。

## 腾讯云安全组与备案

- 只开放 `TCP:80,443`；`TCP:22` 仅允许管理员固定 IP。
- 不开放上表中的任何本机端口（8502、8504、8505、8070、7668、18789）。
- 中国大陆地域 + 域名访问需要备案：[接入备案](https://cloud.tencent.com/document/product/243/97669)、[备案域名要求](https://cloud.tencent.com/document/product/243/18905)。安全组规则见 [安全组概述](https://cloud.tencent.com/document/product/213/112610)。

## 私有 Git 备份

`/srv/nblane-data` 配私有远端和 deploy key。8504 配了 `NBLANE_DATA_GIT_AUTOCOMMIT=1` / `NBLANE_DATA_GIT_AUTOPUSH=1` 后，每次保存都会 commit 并尝试 push。push 失败时页面提示 warning，不回滚已保存的文件。

数据仓库和助手工作区的远端向导、每日定时备份见 [助手 · 数据备份](assistant.md#数据备份)。

## 验收

- `https://your-domain.com` 显示登录页；未登录访问任何页面都会跳到登录。
- member 账号只能看到自己的档案；admin 能看到全部和系统设置。
- 在页面上改一张任务卡后，`git -C /srv/nblane-data log --oneline -1` 出现新提交且已推送。
- 研究台的论文库和阅读器 iframe 正常显示，不空白。
- 上传论文 PDF 后，`/srv/nblane-assets/research/profiles/<profile>/papers/` 出现 PDF，而 `research/sources.yaml` 只记录 asset ref、hash、页数。
- 两个浏览器同时编辑同一文件时，后保存的一方收到刷新提示，不会静默覆盖。
