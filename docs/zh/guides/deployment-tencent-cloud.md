---
status: active
owner: engineering
last_verified: 2026-09-20
source_of_truth: true
---

# 腾讯云小团队部署

本文面向 nblane 的 Streamlit Web UI：公网入口用域名 + HTTPS，应用内账号登录，数据继续放在纯文件 + 私有 Git 仓库中。

## 目录布局

推荐把代码和私有数据分开：

```text
/srv/nblane-app       # 本仓库代码（git clone，运行 Streamlit）
/srv/nblane-data      # 私有数据仓库，含 profiles/ schemas/ teams/ auth/
/srv/nblane-assets    # 大文件资产，不进 Git，含 Research PDF
```

代码目录用 git 部署，不用 rsync / scp 裸拷贝：

```bash
sudo -u nblane git clone https://github.com/<org>/nblane.git /srv/nblane-app
```

git 部署的好处：`git log` 能精确确认线上版本，`git status` 能发现线上手工改动
造成的漂移，回滚是 `git checkout <旧 commit>` + 重启。仓库的 `.gitignore` 已覆盖
`.env`、`.venv`、`profiles/*`、`dist/`、`node_modules` 等本地产物，git 工作区与
这些文件共存无冲突。生产本地若有无须入库的目录（如 `.deploy-backups/`），写进
`.git/info/exclude`，不要为此改仓库的 `.gitignore`。

`/srv/nblane-data` 中至少包含：

```text
profiles/
schemas/
teams/
auth/users.yaml
```

Paper Reading Studio 的 PDF 原件不会写进 `profiles/` Git 仓库。生产部署建议额外创建资产目录：

```bash
sudo mkdir -p /srv/nblane-assets/research
sudo chown -R nblane:nblane /srv/nblane-assets
```

并在服务环境中设置：

```bash
NBLANE_RESEARCH_ASSET_ROOT=/srv/nblane-assets/research
NBLANE_RESEARCH_PDF_BACKEND=auto
NBLANE_GROBID_URL=http://127.0.0.1:8070
```

迁移服务器时需要同步 `/srv/nblane-data` 和 `/srv/nblane-assets`；profile 文件中只保存
`papers/<sha>-name.pdf` 这样的相对 asset ref，不保存绝对路径。

`auth/users.yaml` 可参考仓库内的 `auth/users.example.yaml`。密码哈希用：

```bash
nblane auth hash-password
```

成员配置规则：

- `role: admin`：可访问所有 profile 和 team，可创建新 profile。
- `role: member`：只能访问自己的 `profile`，以及 `teams` 列表中允许的团队。
- `teams: ["*"]`：允许访问所有团队。

## 更新代码与依赖

生产更新以 git 为准（首次部署见上文"目录布局"的 git clone）：

```bash
cd /srv/nblane-app
sudo -u nblane git fetch origin
sudo -u nblane git status -sb          # 应显示与 origin/main 同步；有本地改动先排查漂移
sudo -u nblane git pull --ff-only      # 只快进；失败说明线上有脏改动，不要强拉
.venv/bin/python -m pip install -e .   # 重装 nblane 包本身，只 git pull 不重装时
.venv/bin/python -m pip install -r requirements.txt   # 非 editable 安装下改动不生效
.venv/bin/python - <<'PY'
import socksio
print("socksio ok")
PY
sudo systemctl restart nblane-reader nblane
```

尤其是使用 `ALL_PROXY=socks5://...`、`HTTPS_PROXY=socks5://...` 或 mihomo/clash
SOCKS 出口时，必须安装 `httpx[socks]`（本仓库已写入 `pyproject.toml` 和
`requirements.txt`），否则 LLM / Reader / Research 的外部请求会报：

```text
Using SOCKS proxy, but the 'socksio' package is not installed.
```

回滚：`sudo -u nblane git checkout <旧 commit>` 后重跑上面的 pip + restart；
回到最新用 `git checkout main && git pull --ff-only`。

如果使用 `uv sync` 管理虚拟环境，也要在重启前完成 sync；不要只拉代码而跳过依赖同步。

## 更新前端组件（Dashboard / Reader / Paper Library / Blog 编辑器）

`src/nblane/**/frontend/` 下的 React/Vite 组件是**预构建**的：编译产物提交在
`frontend/static/assets/home-dashboard.<hash>.js|css`，生产运行时直接 serve 这些静态文件，
**不在生产机上跑构建**。因此只改前端源码（`frontend/src/*.jsx`、`*.js`、`*.css`）而不重新构建，
生产**看不到任何变化**——运行的仍是旧 bundle。

改动任一前端组件后，必须在能联网的机器（本地或生产均可）重新构建，并把新产物一起提交：

```bash
cd src/nblane/home_dashboard_component/frontend
# 生产机通常没有 node_modules（被 .gitignore 忽略）。首次构建先装依赖，
# 走代理时显式带上，否则拉包失败：
HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 npm ci
npm test          # 组件单测，应全绿
npm run build     # 产出内容哈希文件名 home-dashboard.<hash>.js/css
```

构建要点：

- Vite 用**内容哈希**命名产物。每次源码变化，`.js`/`.css` 文件名的 hash 都会变，旧哈希文件被删、
  新哈希文件新增、`static/index.html` 自动更新引用。sidecar 用 `HOME_DASHBOARD_ASSET_DIR.glob("*.js")`
  运行时扫目录拾取新哈希，无需改代码。
- **新旧产物都要纳入提交**：`git add` 时把被删的旧 `home-dashboard.*.js|css`、新增的新哈希文件、
  以及改动的 `index.html` 一起提交。漏提交任何一个都会导致生产资产 404 / 加载旧版。
- `node_modules/` 已在 `.gitignore`，不要提交。

**重启哪个服务（这一步最容易漏）：** dashboard 全屏页 `/dashboard` 由 **8502（reader）** serve，
主应用首页 3D hero 由 **8501（streamlit）** serve，两者共用同一份 `home_dashboard_component` bundle。
改了这个组件后，**两个服务都要重启**，只重启 8501 会让 8502 继续用旧 bundle（页面卡死、按钮点不动等）：

```bash
sudo systemctl restart nblane-reader nblane
```

**浏览器缓存：** 前端发版后，浏览器可能仍缓存旧 bundle。验证时先 `Ctrl+Shift+R` 硬刷新；
若 `target="_blank"` 打开的 8502 全屏页仍是旧版，用 DevTools → Network 勾 Disable cache 再刷，
或开无痕窗口。用 DevTools Network 里实际加载的 `home-dashboard.<hash>.js` 文件名对比生产产物，
可确认浏览器是否拿到新版。

**同源模式与 Dashboard Canvas 入口：** 生产用 `NBLANE_READER_API_BASE=0`（同源哨兵值，
sidecar 走 Caddy 反代而非绝对 URL）。主应用首页「打开全屏星系」入口的 `canvas_base` 会把 `=0`
解析成同源域名；健康检查命中 auth-gated sidecar 返回 401/403 时应视为“可达但需登录”，不是不可达。
若入口不显示，先确认这两点。

Reader 全文翻译依赖长时间 LLM 调用。生产环境如通过 SOCKS 代理访问模型，建议保留默认的
`NBLANE_STREAM_PAPER_TRANSLATION=1`，让 `research.paper_translate` 用流式响应收完整 JSON，
避免长非流式响应在代理层一直无结果。大论文还应给 Reader 后台任务更长预算，例如在
`nblane-reader.service` 的 drop-in 中设置：

```ini
[Service]
Environment=NBLANE_READER_TASK_TIMEOUT_SECONDS=3600
Environment=NBLANE_PAPER_TRANSLATION_MODEL_TIMEOUT_SECONDS=300
```

修改 systemd drop-in 后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart nblane-reader
```

端口职责保持固定：

- `8501`：Streamlit 主应用，负责 Dashboard、Evidence Review、Research、Output Studio、Blog 编辑等可写页面。
- `8502`：FastAPI sidecar，负责 Reader、Paper Library standalone、Dashboard Canvas/Paper Library iframe 等长任务和只读/半只读前端。
- `8504`：SPA 后端（`nblane.web_api`），`/api/v1/*` + SPA 静态产物；部署方式见下文「SPA 后端（8504，nblane.web_api）」。

因此 Blog 侧边栏、Dashboard 添加目标、Evidence Review 保存等写入操作仍应发生在 `8501`
主应用中；`8502` 只提供 sidecar 能力，不应作为这些页面的独立写入口。

## systemd

示例服务文件 `/etc/systemd/system/nblane.service`：

```ini
[Unit]
Description=nblane Streamlit Web UI
After=network.target

[Service]
Type=simple
User=nblane
WorkingDirectory=/srv/nblane-app
Environment=NBLANE_ROOT=/srv/nblane-data
Environment=NBLANE_AUTH_FILE=/srv/nblane-data/auth/users.yaml
Environment=UI_LANG=zh
Environment=LLM_REPLY_LANG=zh
Environment=NBLANE_DATA_GIT_AUTOCOMMIT=1
Environment=NBLANE_DATA_GIT_AUTOPUSH=1
Environment=NBLANE_RESEARCH_ASSET_ROOT=/srv/nblane-assets/research
Environment=NBLANE_RESEARCH_PDF_BACKEND=auto
Environment=NBLANE_GROBID_URL=http://127.0.0.1:8070
Environment=NBLANE_READER_API_BASE=0
EnvironmentFile=-/srv/nblane-data/.env
ExecStart=/srv/nblane-app/.venv/bin/streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --server.headless=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

`UI_LANG` 控制 Streamlit 界面文案；`LLM_REPLY_LANG` 控制模型输出和 AI
prompt 语言。需要时二者可以分别设置。

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nblane
sudo systemctl status nblane
```

Research PDF Reader 由独立 FastAPI sidecar 提供，避免 PDF 滚动触发 Streamlit
整页 rerun。先生成共享 token secret，并写入两个 service 都会读取的
`/srv/nblane-data/.env`：

```bash
printf 'NBLANE_READER_TOKEN_SECRET=%s\n' "$(openssl rand -hex 32)" | sudo tee -a /srv/nblane-data/.env
sudo chown nblane:nblane /srv/nblane-data/.env
sudo chmod 600 /srv/nblane-data/.env
```

示例服务文件 `/etc/systemd/system/nblane-reader.service`：

```ini
[Unit]
Description=nblane Paper Reader API
After=network.target

[Service]
Type=simple
User=nblane
WorkingDirectory=/srv/nblane-app
Environment=NBLANE_ROOT=/srv/nblane-data
Environment=NBLANE_AUTH_FILE=/srv/nblane-data/auth/users.yaml
Environment=UI_LANG=zh
Environment=LLM_REPLY_LANG=zh
Environment=NBLANE_RESEARCH_ASSET_ROOT=/srv/nblane-assets/research
Environment=NBLANE_CODEX_BIN=/home/nblane/.local/bin/codex
Environment=NBLANE_CODEX_HOME=/home/nblane/.codex
Environment=NBLANE_RESEARCH_PDF_BACKEND=auto
Environment=NBLANE_GROBID_URL=http://127.0.0.1:8070
Environment=NBLANE_READER_API_BASE=0
EnvironmentFile=-/srv/nblane-data/.env
# 任务状态（搜索 / 翻译 / AI 流）保存在单进程内存中，禁止多 worker。
ExecStart=/srv/nblane-app/.venv/bin/uvicorn nblane.web_reader_api:app --host 127.0.0.1 --port 8502 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Reader sidecar 不会继承 Streamlit service 的语言变量；`UI_LANG` 必须同时配置在
`nblane.service` 和 `nblane-reader.service`，否则 Reader payload 里的按钮和提示会回到
英文默认值。

`--workers` 必须保持 `1`：论文搜索、全文翻译、blog AI 流等任务状态全部保存在
sidecar 的单进程内存中；多 worker 下 start 与 poll / SSE / cancel 请求会被分发到不同
进程，约半数请求报 404（如 "search job not found"）。需要扩容时先把任务表换成
文件 / Redis 等外部存储后端，再考虑多 worker。

两个 service 都设了 `NBLANE_READER_API_BASE=0`（同源哨兵）：Streamlit 页面生成的
iframe / 链接 URL 不含 host，浏览器走同源相对路径，由 Caddy 按路径分流到 8502。
漏配时会回退硬编码的 `http://127.0.0.1:8502`，公网浏览器无法访问该地址，
Paper Library / Reader iframe 会整片空白。

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nblane-reader
sudo systemctl status nblane-reader
```

Reader sidecar 是生产 PDF Reader 的唯一主路径；不要依赖旧的 Streamlit 静态组件路径。
普通部署也不要开启 overlay 调试开关，只有排查 legacy PDF 贴图渲染时才临时设置
`NBLANE_READER_DEBUG_OVERLAY=1`。

## SPA 后端（8504，nblane.web_api）

新版 SPA（`web_ui`）由独立 FastAPI 进程承载：同一进程服务 `/api/v1/*` JSON
接口和 `src/nblane/web_ui/static/` 构建产物（客户端路由回退 `index.html`）。
它是完整写路径——看板、Inbox、证据评审、周回顾、Studio 的全部 mutation 都走
这里，生产必须和 8501 一样配置认证与 Git 备份变量。

示例服务文件 `/etc/systemd/system/nblane-web-api.service`（沿用前两个 unit 的写法）：

```ini
[Unit]
Description=nblane Web API (SPA backend)
After=network.target

[Service]
Type=simple
User=nblane
WorkingDirectory=/srv/nblane-app
Environment=NBLANE_ROOT=/srv/nblane-data
Environment=NBLANE_AUTH_FILE=/srv/nblane-data/auth/users.yaml
Environment=UI_LANG=zh
Environment=LLM_REPLY_LANG=zh
Environment=NBLANE_DATA_GIT_AUTOCOMMIT=1
Environment=NBLANE_DATA_GIT_AUTOPUSH=1
Environment=NBLANE_RESEARCH_ASSET_ROOT=/srv/nblane-assets/research
Environment=NBLANE_READER_API_BASE=0
Environment=NBLANE_TRUST_PROXY_HEADERS=1
EnvironmentFile=-/srv/nblane-data/.env
# 登录限流是单进程内存实现，禁止多 worker。
ExecStart=/srv/nblane-app/.venv/bin/uvicorn nblane.web_api:app --host 127.0.0.1 --port 8504 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

三点不能漏：

- **Git 备份变量**：`NBLANE_DATA_GIT_AUTOCOMMIT=1` / `NBLANE_DATA_GIT_AUTOPUSH=1`
  必须和 `nblane.service` 一样配置——SPA 的写操作直接改 `profiles/` 下的文件，
  漏配后 SPA 保存不会产生备份提交。CW-2 变更窗口的备份检查需覆盖这第三个 unit。
- **`--workers 1`**：登录限流（`LoginRateLimiter`）是单进程内存实现；多 worker
  会把失败计数分散到不同进程，限流形同虚设。
- **`NBLANE_TRUST_PROXY_HEADERS=1`**：见下文「HTTPS 反向代理」的限流说明；
  不要改用 uvicorn `--proxy-headers`（应用自己读取 X-Forwarded-For）。

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nblane-web-api
sudo systemctl status nblane-web-api
```

如果 Paper Library 的 Codex 搜索需要走 `local_codex_readonly`，生产 systemd service
必须能找到 Codex CLI。很多机器把 Codex 安装到 `~/.local/bin/codex`，但 systemd 默认
`PATH` 通常不包含 `~/.local/bin`，会导致页面 trace 出现
`codex_not_found: install Codex CLI first`。建议在 `nblane.service` 和
`nblane-reader.service` 都显式配置：

```ini
Environment=NBLANE_CODEX_BIN=/home/nblane/.local/bin/codex
Environment=NBLANE_CODEX_HOME=/home/nblane/.codex
```

实际路径按运行 service 的 Linux 用户调整。配置后可用同一用户检查：

```bash
sudo -u nblane /home/nblane/.local/bin/codex --version
sudo -u nblane CODEX_HOME=/home/nblane/.codex /home/nblane/.local/bin/codex login status
```

## HTTPS 反向代理

推荐 Caddy。示例 `/etc/caddy/Caddyfile`：

```caddyfile
your-domain.com {
    handle /reader/* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /paper-library* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /dashboard* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /api/dashboard/* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /api/research/* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /auth/* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /blog-editor* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /api/blog/* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /api/site/* {
        reverse_proxy 127.0.0.1:8502
    }

    reverse_proxy 127.0.0.1:8501
}
```

这里必须使用 `handle /reader/*`，不要使用 `handle_path /reader/*`；后者会剥掉
FastAPI 需要的 `/reader` 路由前缀。同理 `/dashboard*`、`/api/dashboard/*`、
`/paper-library*`、`/auth/*`、`/blog-editor*`、`/api/blog/*`、`/api/site/*`
都必须用 `handle`（不是 `handle_path`），否则
FastAPI 侧的路由前缀会被剥掉，`/dashboard?profile=...` 会 404 或路由到错误的
处理函数。`/auth/*` 承载 8501/8503 → 8502 的登录态 handoff，缺失这条会导致
生产环境下打开 `/dashboard` 返回 401。`/blog-editor*`、`/api/blog/*`、`/api/site/*`
承载 Output Studio 的完整 Blog 编辑器、AI 流接口与公开站点构建接口，缺失时编辑器
404、发布不可达。

Streamlit 只监听 `127.0.0.1:8501`，Reader API 只监听 `127.0.0.1:8502`，
SPA 后端只监听 `127.0.0.1:8504`，不要在腾讯云安全组开放 `8501`、`8502` 或 `8504`。

SPA 后端建议挂独立子域名（根路径与 Streamlit 主站点冲突，不宜同域按路径分流）。
SPA 内嵌的 sidecar iframe（Paper Library / 3D dashboard）和 handoff 换票都走同源
相对路径，所以子域名站点要复制主站点的全部 8502 `handle` 块，catch-all 指向 8504：

```caddyfile
spa.your-domain.com {
    # 与主站点一致的 sidecar 分流（handle，不是 handle_path）。
    handle /reader/* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /paper-library* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /dashboard* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /api/dashboard/* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /api/research/* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /auth/* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /blog-editor* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /api/blog/* {
        reverse_proxy 127.0.0.1:8502
    }

    handle /api/site/* {
        reverse_proxy 127.0.0.1:8502
    }

    # 其余全部（/api/v1/* + SPA 静态产物）走 8504。
    reverse_proxy 127.0.0.1:8504
}
```

SPA 的 `handoff_token` 由此与 sidecar 同源，设 cookie 无跨域问题；漏配
`/auth/*` 分流时 iframe 引导返回 404/401，Paper Library 整片空白。

HTTPS 生产环境把 `NBLANE_AUTH_COOKIE_SECURE=1` 写入 `/srv/nblane-data/.env`，
登录 cookie 会带 `Secure` 标记、只经 HTTPS 传输；默认关闭，仅用于无 HTTPS 的
本地调试。该文件被三个 service 共享（`EnvironmentFile`），8504 同样生效。

8504 应用层已实现登录限流：同一「客户端 IP + 用户名」60 秒内失败 5 次即 429。
反代拓扑下所有请求的对端地址都是 Caddy 的 `127.0.0.1`，必须给
`nblane-web-api.service` 配置 `NBLANE_TRUST_PROXY_HEADERS=1`，应用才会取
`X-Forwarded-For` 首跳（Caddy `reverse_proxy` 默认重写该头）作为客户端 IP。
**仅当 8504 不直接可达（安全组只放 80/443）且反代会覆盖该头部时才能开启**；
直连可达时开启等于允许客户端伪造限流身份、绕过限流。不开启时所有代理客户端
共享一个 IP 桶，但用户名维度仍能防止单个账号失败把其他账号一起锁死。
8501/8502 的登录面（Streamlit 登录、sidecar handoff）应用层没有限流，
仍建议在反代层兜底，例如给 Caddy 装 `rate_limit` 插件限制 `/auth/*` 的尝试
频率，或用 fail2ban 盯访问日志中的登录 401。

注意：SPA 与 Streamlit 现在都通过隐藏表单 **POST** 向 sidecar 换取登录 cookie
（handoff token 有效期 60 秒），但 sidecar 仍兼容 URL query 形式的 handoff，
且 reader token 仍以 URL query 传递（iframe 场景的现实约束）——这些会进入
Caddy 访问日志和浏览器历史。确保访问日志权限受控、定期轮转，不要送进公网可达的
日志聚合服务。handoff 改为一次性 POST 换票是 sidecar 侧的后续项。

## Paper Reading PDF 后端

Paper Reading Studio 默认使用 PyMuPDF 做本地 PDF 读取、页数统计、文本抽取和坐标 fallback。
PyMuPDF 采用 AGPL / commercial dual licensing；闭源或商业生产部署需要确认 AGPL 义务，
或使用其 commercial license。这个依赖不应被当作“无许可成本”的普通库处理。

结构化学术 PDF 抽取推荐部署 GROBID。GROBID 服务不可用时，上传和 metadata 导入仍会成功，
页面会显示结构化抽取降级 warning，并退回 PyMuPDF / lightweight fallback。

GROBID 是自托管 REST 服务，不是默认云服务；nblane 只需要能访问
`/api/isalive` 和 `/api/processFulltextDocument`。生产部署建议把 GROBID 只绑定到
本机回环地址，避免把未公开论文 PDF 发送到不可信服务。

安装 Docker：

```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable --now docker
```

国内环境如 Docker Hub 连接不稳定，可配置 registry mirror 后重启 Docker：

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json >/dev/null <<'JSON'
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.nju.edu.cn"
  ]
}
JSON
sudo systemctl restart docker
```

本机启动 GROBID 示例：

```bash
sudo docker run -d --name nblane-grobid --restart unless-stopped \
  -p 127.0.0.1:8070:8070 \
  grobid/grobid:0.9.0-crf
```

验证：

```bash
curl http://127.0.0.1:8070/api/isalive
```

返回 `true` 后，设置服务环境：

```bash
NBLANE_GROBID_URL=http://127.0.0.1:8070
NBLANE_RESEARCH_PDF_BACKEND=grobid
```

`NBLANE_RESEARCH_PDF_BACKEND` 取值 `pymupdf|grobid|auto`（默认 `auto`）：`auto`
会按 `NBLANE_GROBID_URL` 探测 GROBID、不可达时回退 PyMuPDF；部署了 GROBID 时显式
设为 `grobid` 只是更明确。

维护命令：

```bash
sudo docker ps --filter name=nblane-grobid
sudo docker logs -f nblane-grobid
sudo docker restart nblane-grobid
sudo docker stop nblane-grobid
```

如果不部署 GROBID，设置 `NBLANE_RESEARCH_PDF_BACKEND=pymupdf`（或把 `NBLANE_GROBID_URL`
显式设为 `off`）关闭探测；仅删除或留空 `NBLANE_GROBID_URL` 不会禁用——空值会回退默认
地址 `http://127.0.0.1:8070` 继续探测。Reader 仍能使用已抽取的 page text、
手工 annotations、chunks、claims、citations 和导出功能。

## 腾讯云安全组与备案

安全组只开放必要端口：

- `TCP:80,443`：公网 Web。
- `TCP:22`：仅允许管理员固定 IP。
- 不开放 `8501`、数据库端口或全端口。

腾讯云官方文档：

- [安全组概述](https://cloud.tencent.com/document/product/213/112610)
- [添加安全组规则](https://cloud.tencent.com/document/product/213/112614)

如果使用中国大陆地域 CVM + 域名访问，需要按腾讯云要求完成备案或接入备案：

- [接入备案](https://cloud.tencent.com/document/product/243/97669)
- [备案域名要求](https://cloud.tencent.com/document/product/243/18905)

## 私有 Git 备份

在 `/srv/nblane-data` 初始化私有 Git 远端并配置 deploy key。Web 保存成功后，若启用：

```bash
NBLANE_DATA_GIT_AUTOCOMMIT=1
NBLANE_DATA_GIT_AUTOPUSH=1
```

nblane 会自动 `git add`、`git commit`，并尝试 `git push`。如果 push 失败，页面会提示 warning，但不会回滚用户已经保存的文件。

## 验收

- `https://your-domain.com` 显示登录页。
- 未登录访问 Home 或任意 `pages/*.py` 都会被登录页拦住。
- member 账号只能看到自己的 profile；admin 可看到全部 profile。
- 修改 `kanban.md` 或 `skill-tree.yaml` 后，`/srv/nblane-data` 产生 Git commit。
- 上传论文 PDF 后，`/srv/nblane-assets/research/profiles/<profile>/papers/` 出现 PDF，
  而 `/srv/nblane-data/profiles/<profile>/research/sources.yaml` 只记录 asset ref / hash / 页数。
- 两个浏览器同时编辑同一文件时，后保存的一方会收到刷新提示，不会静默覆盖。
