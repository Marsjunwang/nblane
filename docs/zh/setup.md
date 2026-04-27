# 安装与 LLM 配置

## 环境要求

- Python >= 3.11
- Git

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
| `python-dotenv` | `.env` 文件加载 |
| `pandas` | Web UI 数据处理 |

如果只使用 CLI（不需要 Web UI 和 AI 功能），同样执行 `pip install -e .` 即可，所有依赖都很轻量。

## LLM 配置

AI 功能（Web UI 中 Gap Analysis 的 AI 模式）是**可选的**。CLI 和所有基于规则的功能无需任何 API Key 即可正常使用。

nblane 读取以下环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_API_KEY` | *(空)* | API Key — **开启 AI 功能的必要条件** |
| `LLM_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | API 基础地址 |
| `LLM_MODEL` | `qwen3.6-plus` | 模型名称 |
| `LLM_REPLY_LANG` | `en` | 回复语言：`en` 或 `zh`。同时控制 **Gap Analysis** 页的界面文案与 AI 系统提示（国际演示可设为 `en`）。 |
| `NBLANE_AUTH_FILE` | *(空)* | Streamlit Web 登录用户配置。为空时保持本地开发模式；公网部署时应指向私有数据仓库中的 `auth/users.yaml`。 |
| `NBLANE_DATA_GIT_AUTOCOMMIT` | *(空)* | 设为 `1` 时，写入数据文件后自动生成 Git commit。 |
| `NBLANE_DATA_GIT_AUTOPUSH` | *(空)* | 设为 `1` 时，自动 commit 后继续尝试 `git push`。 |

`LLM_REPLY_LANG` 影响 **Streamlit 各页面**（含首页 `app.py`、侧边栏 Profile、Skill Tree、Gap Analysis、Kanban、Team View 等）的界面文案与 AI 输出语言；无需单独配置界面语言。

### 方式 A — `.env` 文件（推荐）

在仓库根目录创建 `.env` 文件（已在 `.gitignore` 中）：

```bash
LLM_API_KEY=sk-...
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.6-plus
```

nblane 启动时会通过 `python-dotenv` 自动加载该文件。

### 方式 B — Shell 环境变量

```bash
export LLM_API_KEY=sk-...
export LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export LLM_MODEL=qwen3.6-plus
streamlit run app.py
```

### 使用非 OpenAI 提供商

任何兼容 OpenAI 接口的服务均可使用，将 `LLM_BASE_URL` 设置为对应的基础地址即可：

```bash
# 阿里云百炼（DashScope）
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-xxx        # 阿里云百炼 API Key（即 DASHSCOPE_API_KEY）
LLM_MODEL=qwen3.6-plus    # 模型列表: https://help.aliyun.com/model-studio/getting-started/models

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

## Web 登录与小团队部署

公网部署时建议配置 `NBLANE_AUTH_FILE`。用户文件示例见
`auth/users.example.yaml`，密码哈希用：

```bash
nblane auth hash-password
```

腾讯云部署步骤见 [腾讯云小团队部署](tencent-cloud-deploy.md)。
