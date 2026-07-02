---
status: active
owner: engineering
last_verified: 2026-05-08
source_of_truth: true
---

# 腾讯云小团队部署

本文面向 nblane 的 Streamlit Web UI：公网入口用域名 + HTTPS，应用内账号登录，数据继续放在纯文件 + 私有 Git 仓库中。

## 目录布局

推荐把代码和私有数据分开：

```text
/srv/nblane-app       # 本仓库代码，运行 Streamlit
/srv/nblane-data      # 私有数据仓库，含 profiles/ schemas/ teams/ auth/
/srv/nblane-assets    # 大文件资产，不进 Git，含 Research PDF
```

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
NBLANE_RESEARCH_PDF_BACKEND=pymupdf
NBLANE_GROBID_URL=http://127.0.0.1:8070
NBLANE_RESEARCH_STRUCTURE_BACKEND=grobid
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

生产环境升级代码后，先同步 Python 依赖，再重启两个服务。尤其是使用
`ALL_PROXY=socks5://...`、`HTTPS_PROXY=socks5://...` 或 mihomo/clash SOCKS
出口时，必须安装 `httpx[socks]`，否则 LLM / Reader / Research 的外部请求会报：

```text
Using SOCKS proxy, but the 'socksio' package is not installed.
```

本仓库已把 `httpx[socks]` 写入 `pyproject.toml` 和 `requirements.txt`。生产更新时执行：

```bash
cd /srv/nblane-app
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python - <<'PY'
import socksio
print("socksio ok")
PY
sudo systemctl restart nblane-reader nblane
```

如果使用 `uv sync` 管理虚拟环境，也要在重启前完成 sync；不要只复制代码而跳过依赖同步。

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
Environment=NBLANE_RESEARCH_PDF_BACKEND=pymupdf
Environment=NBLANE_GROBID_URL=http://127.0.0.1:8070
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
Environment=NBLANE_RESEARCH_PDF_BACKEND=pymupdf
Environment=NBLANE_GROBID_URL=http://127.0.0.1:8070
EnvironmentFile=-/srv/nblane-data/.env
ExecStart=/srv/nblane-app/.venv/bin/uvicorn nblane.web_reader_api:app --host 127.0.0.1 --port 8502 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Reader sidecar 不会继承 Streamlit service 的语言变量；`UI_LANG` 必须同时配置在
`nblane.service` 和 `nblane-reader.service`，否则 Reader payload 里的按钮和提示会回到
英文默认值。

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nblane-reader
sudo systemctl status nblane-reader
```

Reader sidecar 是生产 PDF Reader 的唯一主路径；不要依赖旧的 Streamlit 静态组件路径。
普通部署也不要开启 overlay 调试开关，只有排查 legacy PDF 贴图渲染时才临时设置
`NBLANE_READER_DEBUG_OVERLAY=1`。

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

    reverse_proxy 127.0.0.1:8501
}
```

这里必须使用 `handle /reader/*`，不要使用 `handle_path /reader/*`；后者会剥掉
FastAPI 需要的 `/reader` 路由前缀。同理 `/dashboard*`、`/api/dashboard/*`、
`/paper-library*`、`/auth/*` 都必须用 `handle`（不是 `handle_path`），否则
FastAPI 侧的路由前缀会被剥掉，`/dashboard?profile=...` 会 404 或路由到错误的
处理函数。`/auth/*` 承载 8501/8503 → 8502 的登录态 handoff，缺失这条会导致
生产环境下打开 `/dashboard` 返回 401。

Streamlit 只监听 `127.0.0.1:8501`，Reader API 只监听 `127.0.0.1:8502`，
不要在腾讯云安全组开放 `8501` 或 `8502`。

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
NBLANE_RESEARCH_STRUCTURE_BACKEND=grobid
```

维护命令：

```bash
sudo docker ps --filter name=nblane-grobid
sudo docker logs -f nblane-grobid
sudo docker restart nblane-grobid
sudo docker stop nblane-grobid
```

如果不部署 GROBID，可暂时删除或留空 `NBLANE_GROBID_URL`；Reader 仍能使用已抽取的 page text、
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
