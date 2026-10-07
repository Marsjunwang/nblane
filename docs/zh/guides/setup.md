---
status: active
owner: engineering
last_verified: 2026-10-07
source_of_truth: true
---

# 本机安装与 AI 配置

本文讲在一台机器上把 nblane 跑起来。上服务器见 [腾讯云部署](deployment-tencent-cloud.md)，换机器见 [整机迁移](migration.md)。

## 环境要求

- Python ≥ 3.11、Git。
- tmux：`scripts/dev-web.sh` 用它托管开发服务。
- Node.js 与 npm：只在重新构建 SPA 前端或跑浏览器 e2e 时需要。

## 安装

```bash
git clone <repo-url>
cd nblane
python3 -m venv .venv
.venv/bin/pip install -e .
cp .env.example .env      # 只在使用 AI 功能时填 LLM_API_KEY
```

依赖以 `pyproject.toml` 为准（`uv.lock` 锁定版本，`requirements.txt` 给 pip 用户镜像一份）。走 SOCKS 代理访问外部服务时需要 `httpx[socks]`，已包含在依赖里。

CLI 自检：

```bash
.venv/bin/nblane init <name>
.venv/bin/nblane validate
.venv/bin/nblane status
```

命令全集见 [CLI 参考](../reference/cli.md)。

## 启动 Web

```bash
scripts/dev-web.sh              # 启动（默认）
scripts/dev-web.sh status       # 查看会话和健康检查地址
scripts/dev-web.sh stop
```

默认在 tmux 里起两个服务：

| 服务 | 端口 | 作用 |
|------|------|------|
| SPA 后端 `nblane.web_api` | 8504 | 同一进程提供 SPA 页面和 `/api/v1` |
| Reader API `nblane.web_reader_api` | 8502 | 论文库、阅读器（SPA 用 iframe 嵌入）、登录态交接 `/auth/session` |

浏览器打开 `http://127.0.0.1:8504`。远程开发时两个端口都要转发，否则论文库和阅读器 iframe 空白。

常用参数：

- `--isolated`：端口改为 18502 / 18504，数据放 `.dev-data/`、资产放 `.dev-assets/`，首次自动 `nblane init dev`。助手、备份、GROBID 也换成独立的 dev 实例，不碰真实数据和生产服务。
- `--reload`：uvicorn 热重载 `src/`。默认不开，改了 Python 代码要重新 `start`。
- `--auth-file PATH`：给 8504 开启登录（`NBLANE_AUTH_FILE`）。`--isolated` 下会自动使用 `.dev-data/auth/users.yaml`（存在时）。
- `--grobid`：把结构化抽取指向本机 18070 的 dev GROBID。
- `--root PATH` / `--asset-root PATH` / `--env-file PATH`：改数据根、资产根和 env 文件。

完整参数见 `scripts/dev-web.sh --help`。

## SPA 前端（可选）

构建产物 `src/nblane/web_ui/static/` 已随仓库提交，只用不改时不需要 Node。改了 `src/nblane/web_ui/frontend/` 后：

```bash
cd src/nblane/web_ui/frontend
npm install
npm test
npm run build              # 输出到 src/nblane/web_ui/static/，产物一起提交
```

改了后端接口后，先跑 `scripts/dump-openapi.sh` 更新 `openapi.json`，再 `npm run gen:api` 生成 `src/api/schema.d.ts`。

前端热更新开发用 `npm run dev`（Vite，5173），它把 API 代理到后端，目标用 `VITE_API_PROXY_TARGET` 指定。

## 浏览器 e2e（可选）

```bash
npm install
npm run test:e2e:install     # 国内网络用 npm run test:e2e:install:cn
npm run test:e2e             # 需要已运行的服务，地址 NBLANE_E2E_BASE_URL
```

`test:e2e:install:cn` 面向 Linux x64，从 npmmirror 下载浏览器；内网缓存可设 `NBLANE_CHROME_FOR_TESTING_MIRROR` 和 `NBLANE_PLAYWRIGHT_BINARY_MIRROR`。

## AI 配置

AI 是可选的。不配 Key 时 CLI 和基于规则的功能照常可用，页面上的 AI 动作会提示未配置。

### 设置 → AI 服务（系统级，仅管理员）

- AI 连接：Base URL、默认模型、API Key，可「测试连接」。保存后写入 `.env`（`LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY`）并立即生效，另一个服务进程检测到文件变化后自动重新加载。
- 输出上限：普通调用 `LLM_MAX_TOKENS`（默认 8192）和论文分析 `LLM_ANALYSIS_MAX_TOKENS`（默认 16384）。不能超过模型本身的最大输出。输出被截断时「AI 异常」里会提示调高。
- Codex CLI：显示是否安装、是否登录，并给出安装和 `codex login` 命令。页面不读取也不显示任何 Key 或 auth.json。

### 设置 → AI 路由（档案级）

- 工作流 AI：看板、项目、首页和证据里的每个 AI 动作（任务对齐、子任务拆分、项目引用建议、目标与技能匹配、每日简报、证据结晶等）选「兼容 API」或「Codex」，并可单独指定模型。研究相关的在「研究与阅读」里，见 [研究台](research.md)。
- Codex 运行参数：默认模型、超时、Codex 路径、Cloud 环境 ID、分支名。留空跟随 Codex CLI 默认，保存在 `profiles/<name>/codex.yaml`。

选了 Codex 的动作调用只读 `codex exec`，不会改项目文件。

### 用 `.env` 配置

也可以直接编辑仓库根目录的 `.env`（已 gitignore；`NBLANE_ENV_FILE` 可改路径）。所有键见 `.env.example`，常用的：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_API_KEY` | 空 | 开启 AI 功能的必要条件 |
| `LLM_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 任何 OpenAI 兼容地址 |
| `LLM_MODEL` | `qwen3.6-plus` | 默认模型 |
| `LLM_MAX_TOKENS` / `LLM_ANALYSIS_MAX_TOKENS` | 8192 / 16384 | 输出上限 |
| `LLM_REPLY_LANG` | `en` | 模型回复语言；档案级可在「设置 → 通用」覆盖 |
| `VISUAL_API_KEY` 等 `VISUAL_*` | 空 | 封面、图片、视频生成；为空时依次用 `DASHSCOPE_API_KEY`、`LLM_API_KEY` |
| `NBLANE_CODEX_BIN` / `NBLANE_CODEX_HOME` | `codex` / `~/.codex` | Codex CLI 路径和 home |
| `NBLANE_CODEX_CLOUD_ENV_ID` | 空 | 配置后可把 agent task 提交到 Codex Cloud |

其他 OpenAI 兼容服务示例：

```bash
# DeepSeek
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 本地 Ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3
```

### Codex CLI（可选）

Codex 是外部执行器，不是 Python 依赖。

```bash
nblane codex status
nblane codex install --print-command   # 只打印 npm 命令
nblane codex install                   # npm i -g @openai/codex
codex login
```

外部 agent 任务的交接见 [Agent Harness](../reference/agent-harness.md)。

## 其他可选组件

- GROBID 结构化抽取、本地翻译模型：服务跑起来后在「设置 → 本地服务」一键安装，见 [研究台](research.md)。
- 代理：国内机器下载 GitHub、Hugging Face、arXiv 慢时，见 [Mihomo 代理部署](mihomo-deployment.md)。
- 助手（OpenClaw）：见 [助手](assistant.md)。

## 登录

本机单人使用默认不登录。需要登录时准备 `auth/users.yaml`（示例 `auth/users.example.yaml`），密码哈希用 `nblane auth hash-password`，再用 `NBLANE_AUTH_FILE` 指向它。账号分本人（member）、助手服务账号（`agent: true`）和管理员（admin）。
