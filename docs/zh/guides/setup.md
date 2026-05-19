---
status: active
owner: engineering
last_verified: 2026-05-08
source_of_truth: true
---

# 安装与 LLM 配置

## 环境要求

- Python >= 3.11
- Git
- Node.js >= 18 与 npm >= 9 仅在重新构建内置 Streamlit 前端组件时需要，
  例如 Kanban 看板组件；如果要通过 nblane 安装 Codex CLI，也需要 npm。

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
| `Pillow` | 博客 / 视觉预览的图片缩略图生成 |
| `python-dotenv` | `.env` 文件加载 |
| `pandas` | Web UI 数据处理 |

如果只使用 CLI（不需要 Web UI 和 AI 功能），同样执行 `pip install -e .` 即可，所有依赖都很轻量。

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

这些 `NBLANE_CODEX_*` 是全局默认值。每个 profile 也可以有自己的
`profiles/<name>/codex.yaml`。Web 中可在侧边栏 **AI / LLM** 展开
**配置 Codex** 大弹窗，编辑全局 Codex CLI 的 `~/.codex/config.toml`、通过
Codex CLI 写入 API key/auth，并编辑当前 profile 的 `codex.yaml`。读取优先级为：

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
```

nblane 启动时会通过 `python-dotenv` 自动加载该文件。

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
