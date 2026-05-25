---
status: active
owner: engineering
last_verified: 2026-05-24
source_of_truth: true
---

# 安装与 LLM 配置

## 环境要求

- Python >= 3.11
- Git
- Node.js >= 18 与 npm >= 9 仅在重新构建内置 Streamlit 前端组件、运行
  Playwright 浏览器 e2e、或通过 nblane 安装 Codex CLI 时需要。

## 安装

```bash
git clone <repo-url>
cd nblane
pip install -e .
```

该命令会安装 `pyproject.toml` 中声明的所有依赖：

| 包 | 用途 |
|----|------|
| `pyyaml` | Profile / Schema / Team YAML 解析 |
| `streamlit` | Web UI |
| `openai` | LLM 客户端（兼容 OpenAI 接口） |
| `httpx[socks]` | LLM / Reader / Research 通过 SOCKS 代理访问外部服务时需要；会安装 `socksio` |
| `Pillow` | 博客 / 视觉预览的图片缩略图生成 |
| `python-dotenv` | `.env` 文件加载 |
| `pandas` | Web UI 数据处理 |

如果只使用 CLI（不需要 Web UI 和 AI 功能），同样执行 `pip install -e .` 即可，所有依赖都很轻量。

### 可选：浏览器 e2e 依赖

仓库根目录的 `tests/e2e` 使用 Playwright。第一次运行浏览器 e2e 前，先安装
Node 依赖和 Chromium 浏览器二进制：

```bash
npm install
npm run test:e2e:install
```

国内网络环境建议改用镜像源。`npm` 包和 Playwright 浏览器二进制是两条下载链路，
需要分别指定：

```bash
npm_config_registry=https://registry.npmmirror.com npm install
npm run test:e2e:install:cn
```

`test:e2e:install:cn` 当前面向 Linux x64 开发机，会从
`cdn.npmmirror.com/binaries/chrome-for-testing` 下载 Chrome for Testing /
Headless Shell，并从 `cdn.npmmirror.com/binaries/playwright` 下载 ffmpeg。
如需改成内网缓存地址，可设置 `NBLANE_CHROME_FOR_TESTING_MIRROR` 和
`NBLANE_PLAYWRIGHT_BINARY_MIRROR`。

安装完成后可运行：

```bash
npm run test:e2e
```

该步骤会把 Chromium 下载到本机 Playwright 缓存中，不会写入仓库。CI、全新机器
或清空 `~/.cache/ms-playwright` 后都需要重新执行 `npm run test:e2e:install`
或国内镜像版 `npm run test:e2e:install:cn`。

### 重新构建内置前端组件

普通 Python 包使用只需要仓库中已提交的 `src/nblane/*/frontend/static/`
静态资源。只有在修改内置前端组件、需要重新生成静态资源时，才需要安装
Node.js/npm。

Ubuntu 环境可执行：

```bash
sudo apt-get update
sudo apt-get install -y nodejs npm
```

Kanban 看板组件的构建命令：

```bash
cd src/nblane/kanban_board_component/frontend
npm install
npm run build
```

### 可选：安装 Codex CLI

Codex 是外部高级执行器，不是 nblane 的 Python 依赖。未安装 Codex 时，
nblane 的 CLI、Web、LLM 和规则功能都可正常使用。

检查当前环境：

```bash
nblane codex status
```

安装或升级 Codex CLI：

```bash
nblane codex install --print-command  # 只打印 npm 命令
nblane codex install                  # 执行 npm i -g @openai/codex
nblane codex install --upgrade        # 执行 npm i -g @openai/codex@latest
```

首次使用 Codex 仍需按 Codex CLI 的方式登录：

```bash
codex login
```

### 可选：安装 mihomo 代理

国内服务器在下载 GitHub release、arXiv PDF、Playwright 浏览器或访问部分海外
LLM / 论文源时可能很慢。可以安装
[MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo/releases) 作为本机代理，
再让终端和生产 systemd 服务走 `127.0.0.1:7890`。

订阅地址通常包含 token，应按密钥处理，不要写进公开仓库、截图或提交记录。下面用
`<SUB_URL>` 表示你的订阅 URL。

#### 1. 安装 mihomo core

到 mihomo Releases 选择当前系统架构对应的包。下面是 Ubuntu/Linux x86_64 示例；
版本号可按 Releases 页面替换成最新稳定版：

```bash
cd /tmp
curl -LO https://github.com/MetaCubeX/mihomo/releases/download/v1.19.25/mihomo-linux-amd64-v1.19.25.gz
gzip -d mihomo-linux-amd64-v1.19.25.gz
chmod +x mihomo-linux-amd64-v1.19.25
sudo mv mihomo-linux-amd64-v1.19.25 /usr/local/bin/mihomo
mihomo -v
```

如果 GitHub 直连不可用，可以先在本地下载对应资产，再上传到服务器；只要最终
`/usr/local/bin/mihomo` 可执行即可。

#### 2. 写入 mihomo 配置

```bash
mkdir -p ~/.config/mihomo
nano ~/.config/mihomo/config.yaml
```

基础配置：

```yaml
mixed-port: 7890
allow-lan: false
bind-address: 127.0.0.1

mode: rule
log-level: info
ipv6: true

external-controller: 127.0.0.1:9090
secret: "change-this-secret"
external-ui: ui
external-ui-name: metacubexd
external-ui-url: "https://github.com/MetaCubeX/metacubexd/archive/refs/heads/gh-pages.zip"

profile:
  store-selected: true
  store-fake-ip: true

unified-delay: true
tcp-concurrent: true

proxy-providers:
  subscription:
    type: http
    url: "<SUB_URL>"
    path: ./proxy_providers/subscription.yaml
    proxy: DIRECT
    header:
      User-Agent:
        - clash.meta
    interval: 3600
    health-check:
      enable: true
      url: https://www.gstatic.com/generate_204
      interval: 300
      timeout: 5000
      lazy: true
      expected-status: 204

proxy-groups:
  - name: PROXY
    type: select
    use:
      - subscription
    proxies:
      - AUTO
      - DIRECT

  - name: AUTO
    type: url-test
    use:
      - subscription
    url: https://www.gstatic.com/generate_204
    interval: 300
    timeout: 5000

  - name: GLOBAL
    type: select
    proxies:
      - PROXY
      - AUTO
      - DIRECT

rules:
  - DOMAIN-SUFFIX,localhost,DIRECT
  - DOMAIN-SUFFIX,local,DIRECT
  - IP-CIDR,127.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,172.16.0.0/12,DIRECT,no-resolve
  - IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
  - GEOIP,CN,DIRECT
  - MATCH,PROXY
```

如果订阅站返回“网络环境存在风险，请关闭网络代理后再获取订阅配置”一类提示，可在
`header` 下临时增加订阅站要求的头，例如：

```yaml
    header:
      User-Agent:
        - clash.meta
      X-Forwarded-For:
        - 114.114.114.114
```

这是订阅站自己的风控兼容项；只有确认需要时再加。

#### 3. 准备 GeoIP 数据库

上面的 `GEOIP,CN,DIRECT` 需要 `Country.mmdb`。如果服务器直连 GitHub 很慢，可先
启动不含 `GEOIP,CN,DIRECT` 的配置，让代理跑起来，再通过代理下载：

```bash
curl --fail -L -x http://127.0.0.1:7890 \
  https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/country.mmdb \
  -o ~/.config/mihomo/Country.mmdb
```

没有 `Country.mmdb` 时，mihomo 可能会在启动或校验阶段尝试下载数据库并卡住。
可以先删掉 `GEOIP,CN,DIRECT`，等数据库放好后再恢复。

#### 4. 用 systemd 启动 mihomo

用户级 systemd 服务示例：

```bash
mkdir -p ~/.config/systemd/user
nano ~/.config/systemd/user/mihomo.service
```

```ini
[Unit]
Description=mihomo proxy service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/mihomo -d %h/.config/mihomo
Restart=on-failure
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=default.target
```

启用并检查：

```bash
systemctl --user daemon-reload
systemctl --user enable --now mihomo.service
systemctl --user status mihomo.service
ss -ltnp | grep -E ':(7890|9090)\b'
```

如果希望用户退出 SSH 后服务仍继续运行：

```bash
sudo loginctl enable-linger "$USER"
```

#### 5. 配置终端代理

把下面内容追加到 `~/.bashrc`，新开的 shell 会自动使用 mihomo：

```bash
# mihomo proxy
export http_proxy="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"
export all_proxy="socks5://127.0.0.1:7890"
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$https_proxy"
export ALL_PROXY="$all_proxy"
export no_proxy="localhost,127.0.0.1,::1,*.local"
export NO_PROXY="$no_proxy"
```

当前 shell 立刻生效：

```bash
source ~/.bashrc
```

验证：

```bash
curl -x http://127.0.0.1:7890 https://www.gstatic.com/generate_204 -I
curl -x http://127.0.0.1:7890 https://github.com -I
curl -x http://127.0.0.1:7890 https://api.ipify.org
```

注意：`ping` 使用 ICMP，不会走 `http_proxy` / `https_proxy` / SOCKS 代理。
因此 `curl https://www.google.com` 能通而 `ping www.google.com` 不通是正常的，
不代表 mihomo 没工作。

#### 6. 让生产 systemd 服务走代理

终端 `.bashrc` 只影响交互式 shell，已经运行的 `nblane.service` 和
`nblane-reader.service` 不会自动继承这些变量。生产部署需要给 systemd service
添加 drop-in：

```bash
sudo install -d /etc/systemd/system/nblane.service.d
sudo install -d /etc/systemd/system/nblane-reader.service.d
sudo tee /etc/systemd/system/nblane.service.d/10-proxy.conf >/dev/null <<'EOF'
[Service]
Environment="http_proxy=http://127.0.0.1:7890"
Environment="https_proxy=http://127.0.0.1:7890"
Environment="all_proxy=socks5://127.0.0.1:7890"
Environment="HTTP_PROXY=http://127.0.0.1:7890"
Environment="HTTPS_PROXY=http://127.0.0.1:7890"
Environment="ALL_PROXY=socks5://127.0.0.1:7890"
Environment="no_proxy=localhost,127.0.0.1,::1,*.local"
Environment="NO_PROXY=localhost,127.0.0.1,::1,*.local"
EOF
sudo cp /etc/systemd/system/nblane.service.d/10-proxy.conf \
  /etc/systemd/system/nblane-reader.service.d/10-proxy.conf
sudo systemctl daemon-reload
sudo systemctl restart nblane-reader.service nblane.service
```

确认新进程已拿到代理环境：

```bash
pid=$(systemctl show -p MainPID --value nblane-reader.service)
sudo sh -c "tr '\0' '\n' < /proc/$pid/environ" | grep -i proxy
```

如果 Paper Reading Studio 下载 arXiv PDF 很慢，优先检查生产进程环境，而不是只刷新
浏览器页面。页面刷新只能重拉前端状态；PDF 下载实际发生在后端服务进程里。

#### 7. 让 Streamlit 与 Reader 使用同一界面语言

`UI_LANG` / `LLM_REPLY_LANG` 不会从 `nblane.service` 自动继承到
`nblane-reader.service`。如果只给 Streamlit 配置中文，Reader payload 里的“Full
translation”等按钮仍会使用英文默认值。生产环境建议给两个服务都配置同一组语言变量：

```bash
sudo install -d /etc/systemd/system/nblane.service.d
sudo install -d /etc/systemd/system/nblane-reader.service.d
sudo tee /etc/systemd/system/nblane.service.d/20-lang.conf >/dev/null <<'EOF'
[Service]
Environment=UI_LANG=zh
Environment=LLM_REPLY_LANG=zh
EOF
sudo cp /etc/systemd/system/nblane.service.d/20-lang.conf \
  /etc/systemd/system/nblane-reader.service.d/20-lang.conf
sudo systemctl daemon-reload
sudo systemctl restart nblane-reader.service nblane.service
```

验证 Reader 进程已经拿到语言变量：

```bash
pid=$(systemctl show -p MainPID --value nblane-reader.service)
sudo sh -c "tr '\0' '\n' < /proc/$pid/environ" | grep -E 'UI_LANG|LLM_REPLY_LANG'
```

## LLM 配置

AI 功能（Web UI 中 Gap Analysis 的 AI 模式）是**可选的**。CLI 和所有基于规则的功能无需任何 API Key 即可正常使用。

nblane 读取以下环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_API_KEY` | *(空)* | API Key — **开启 AI 功能的必要条件** |
| `LLM_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | API 基础地址 |
| `LLM_MODEL` | `qwen3.6-plus` | 模型名称 |
| `VISUAL_PROVIDER` | `dashscope_wan` | Blog 视觉生成 provider。其他 provider 预留给后续 adapter。 |
| `VISUAL_API_KEY` | *(空)* | 可选的图像 / 视频 Key。为空时依次尝试 `DASHSCOPE_API_KEY`、`LLM_API_KEY`。 |
| `DASHSCOPE_API_KEY` | *(空)* | 可选 DashScope Key；视觉生成会优先于 `LLM_API_KEY` 使用它。 |
| `VISUAL_BASE_URL` | *(空)* | 可选视觉任务 endpoint 覆盖。通常留空，使用 DashScope 视觉任务 API。 |
| `VISUAL_IMAGE_MODEL` | `wan2.7-image-pro` | Blog 图片 / 封面默认模型。 |
| `VISUAL_VIDEO_MODEL` | `wan2.7-videoedit` | Blog 视频编辑默认模型。 |
| `UI_LANG` | `en` | Streamlit 界面语言：`en` 或 `zh`。只控制界面文案。 |
| `LLM_REPLY_LANG` | `en` | 模型回复语言：`en` 或 `zh`。仅控制 AI prompt / 输出语言。 |
| `NBLANE_AUTH_FILE` | *(空)* | Streamlit Web 登录用户配置。为空时保持本地开发模式；公网部署时应指向私有数据仓库中的 `auth/users.yaml`。 |
| `NBLANE_DATA_GIT_AUTOCOMMIT` | *(空)* | 设为 `1` 时，写入数据文件后自动生成 Git commit。 |
| `NBLANE_DATA_GIT_AUTOPUSH` | *(空)* | 设为 `1` 时，自动 commit 后继续尝试 `git push`。 |
| `NBLANE_CODEX_BIN` | `codex` | 可选 Codex CLI binary 路径或命令名。 |
| `NBLANE_CODEX_CLOUD_ENV_ID` | *(空)* | 可选 Codex Cloud environment id；配置后 Web/CLI 可提交 agent task 到 Codex Cloud。 |
| `NBLANE_CODEX_MODEL` | *(空)* | 可选 Codex CLI `-c model=...` 覆盖；为空时使用 Codex 自己的默认配置。 |
| `NBLANE_CODEX_ATTEMPTS` | `1` | Codex Cloud `--attempts`。 |
| `NBLANE_CODEX_BRANCH` | *(空)* | Codex Cloud `--branch`；为空时使用当前/默认分支。 |
| `NBLANE_CODEX_TIMEOUT_SECONDS` | `180` | nblane 等待 Codex CLI 命令的超时时间。 |
| `NBLANE_CODEX_HOME` | `CODEX_HOME` 或 `~/.codex` | nblane 使用的部署级 Codex home；云上建议指向持久化目录。 |
| `NBLANE_CODEX_HOME_POLICY` | `default` | Codex home 策略。默认 `default` 使用部署级 / 终端同款 home；仅诊断时可设 `profile` 使用旧 profile 隔离 home。 |
| `NBLANE_CODEX_HOME_ROOT` | `~/.nblane/codex/profiles` | 旧 profile 隔离 Codex home 的根目录；只在 `NBLANE_CODEX_HOME_POLICY=profile` 或显式请求 profile policy 时使用。 |

这些 `NBLANE_CODEX_*` 是全局默认值。每个 profile 也可以有自己的
`profiles/<name>/codex.yaml`。Web 中可在侧边栏 **AI / LLM** 展开
**配置 Codex** 大弹窗，编辑部署级 Codex home 下的 `config.toml`、通过
`codex login --with-api-key` 写入该 home 下的 `auth.json`，并编辑当前
profile 的 `codex.yaml`。本地默认会复用终端/插件的 `~/.codex`；云上建议用
`NBLANE_CODEX_HOME` 指向一个持久化 service-level Codex home。profile 不是
Codex home 隔离边界；用户/profile 隔离由 nblane 的数据与权限层承担。读取优先级为：

```text
默认值 / .env -> profiles/<name>/codex.yaml -> 当前进程 runtime override
```

`UI_LANG` 影响 **Streamlit 各页面**（含首页 `app.py`、侧边栏 Profile、Skill Tree、Gap Analysis、Kanban、Team View 等）的界面文案；`LLM_REPLY_LANG` 只影响模型输出和 AI prompt 语言，因此界面语言与模型回复语言可以独立配置。

### 方式 A — `.env` 文件（推荐）

在仓库根目录创建 `.env` 文件（已在 `.gitignore` 中）：

```bash
LLM_API_KEY=sk-...
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.6-plus
UI_LANG=zh
LLM_REPLY_LANG=en

# 可选视觉生成覆盖项
VISUAL_IMAGE_MODEL=wan2.7-image-pro
VISUAL_VIDEO_MODEL=wan2.7-videoedit
VISUAL_API_KEY=

# 可选 Codex Cloud 集成（不存认证信息）
NBLANE_CODEX_BIN=codex
NBLANE_CODEX_CLOUD_ENV_ID=
NBLANE_CODEX_ATTEMPTS=1

# 可选 Paper Reading 结构化抽取
NBLANE_GROBID_URL=http://127.0.0.1:8070
NBLANE_RESEARCH_STRUCTURE_BACKEND=grobid
```

nblane 启动时会通过 `python-dotenv` 自动加载该文件。

### Paper Reading 结构化抽取（可选）

Paper Reading Studio 使用 PyMuPDF 作为默认本地 PDF 后端；如果需要章节、段落、
references 和 TEI 等学术结构化结果，可额外启动自托管 GROBID REST 服务。
GROBID 不是默认云 API，不需要 API key；nblane 只会访问你配置的
`NBLANE_GROBID_URL`。

推荐本机 Docker 启动：

```bash
sudo apt-get install -y docker.io
sudo systemctl enable --now docker
sudo docker run -d --name nblane-grobid --restart unless-stopped \
  -p 127.0.0.1:8070:8070 \
  grobid/grobid:0.9.0-crf
curl http://127.0.0.1:8070/api/isalive
```

返回 `true` 后，在 `.env` 中配置：

```bash
NBLANE_GROBID_URL=http://127.0.0.1:8070
NBLANE_RESEARCH_STRUCTURE_BACKEND=grobid
```

然后重启 Streamlit。若不启动 GROBID，Reader 仍可使用 PDF 阅读、高亮、
annotations、chunks、citations、翻译和导出；结构化抽取会回退到
PyMuPDF/page-text fallback，并在页面显示 warning。

### 方式 B — Shell 环境变量

```bash
export LLM_API_KEY=sk-...
export LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export LLM_MODEL=qwen3.6-plus
export UI_LANG=zh
export LLM_REPLY_LANG=en
streamlit run app.py
```

### 使用非 OpenAI 提供商

任何兼容 OpenAI 接口的服务均可使用，将 `LLM_BASE_URL` 设置为对应的基础地址即可：

```bash
# 阿里云百炼（DashScope）
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-xxx        # 阿里云百炼 API Key（即 DASHSCOPE_API_KEY）
LLM_MODEL=qwen3.6-plus    # 模型列表: https://help.aliyun.com/model-studio/getting-started/models

# Blog 封面、图片、视频生成默认复用同一个 LLM_API_KEY。
# 只有图像 / 视频任务使用不同凭据时才需要填写 VISUAL_API_KEY。
VISUAL_IMAGE_MODEL=wan2.7-image-pro
VISUAL_VIDEO_MODEL=wan2.7-videoedit
VISUAL_API_KEY=

# DeepSeek
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=<your-key>
LLM_MODEL=deepseek-chat

# 本地 Ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3
```

### 验证配置是否生效

配置完成后，Gap Analysis 页面的侧边栏会显示当前使用的模型名称。若 `LLM_API_KEY` 未设置，AI 模式会被禁用并显示提示——基于规则的 Gap 分析仍可正常使用。

### 验证 Codex 配置是否生效

如果本机已安装并登录 Codex，可在 Web 侧栏 **AI / LLM** 中将
**看板 AI 引擎** 切到 `Codex`，看板的 Gap、拆子任务、任务理解和 Done ->
evidence 会使用只读 `codex exec`。外部 agent patch/handoff 仍通过 CLI 在隔离
git worktree 中运行：

```bash
nblane codex local run <agent_task_id> --profile <profile>
```

本地 runner 会收集 diff 并写入 Agent Activity 候选，不会直接修改主工作树。

配置 `NBLANE_CODEX_CLOUD_ENV_ID` 后，也可以把同一个 handoff 提交到 Codex
Cloud；Agent Activity 页可以刷新状态并拉取 diff 候选。nblane 不会执行
`codex cloud apply`，也不会自动修改本地工作树。

如果使用 per-profile 配置，先检查当前 profile 的 Codex 状态：

```bash
nblane codex status --profile <profile>
```

CLI 等价流程：

```bash
nblane codex status
nblane agent handoff <agent_task_id> --target codex --profile <profile>
nblane codex local run <agent_task_id> --profile <profile>
nblane codex cloud submit <agent_task_id> --profile <profile>
nblane codex cloud refresh <agent_task_id> --profile <profile> --diff
```

## Web 登录与小团队部署

公网部署时建议配置 `NBLANE_AUTH_FILE`。用户文件示例见
`auth/users.example.yaml`，密码哈希用：

```bash
nblane auth hash-password
```

腾讯云部署步骤见 [腾讯云小团队部署](deployment-tencent-cloud.md)。
