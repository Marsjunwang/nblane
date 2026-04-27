# Installation & LLM Configuration

## Requirements

- Python >= 3.11
- Git

## Install

```bash
git clone <repo-url>
cd nblane
pip install -e .
```

This installs all dependencies declared in `pyproject.toml`:

| Package | Role |
|---------|------|
| `pyyaml` | Profile / schema / team YAML parsing |
| `streamlit` | Web UI |
| `openai` | LLM client (OpenAI-compatible) |
| `python-dotenv` | `.env` file loading |
| `pandas` | Data handling in Web UI |

If you only need the CLI (no Web UI, no AI features), the minimal install is still `pip install -e .`—all packages are lightweight.

## LLM Configuration

AI features (Gap Analysis AI mode in the Web UI) are **optional**. The CLI and all rule-based features work without any API key.

nblane reads these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | *(empty)* | API key — **required** to enable AI features |
| `LLM_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | API base URL |
| `LLM_MODEL` | `qwen3.6-plus` | Model name |
| `UI_LANG` | `en` | Streamlit interface language: `en` or `zh`. If unset, falls back to `LLM_REPLY_LANG` for compatibility. |
| `LLM_REPLY_LANG` | `en` | Model reply language: `en` or `zh`. Controls AI prompts/output only. |
| `NBLANE_AUTH_FILE` | *(empty)* | Streamlit Web login config. Empty keeps local development mode; public deployments should point at private `auth/users.yaml`. |
| `NBLANE_DATA_GIT_AUTOCOMMIT` | *(empty)* | Set to `1` to commit data-file writes automatically. |
| `NBLANE_DATA_GIT_AUTOPUSH` | *(empty)* | Set to `1` to push after automatic commits. |

`UI_LANG` controls the Streamlit UI (home `app.py`, sidebar Profile, Skill Tree, Gap Analysis, Kanban, Team View, etc.). `LLM_REPLY_LANG` controls model output and AI prompt language, so the interface and model replies can be configured independently.

### Option A — `.env` file (recommended)

Create a `.env` file at the repo root (already in `.gitignore`):

```bash
LLM_API_KEY=sk-...
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.6-plus
UI_LANG=zh
LLM_REPLY_LANG=en
```

nblane loads this file automatically on startup via `python-dotenv`.

### Option B — shell environment variables

```bash
export LLM_API_KEY=sk-...
export LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export LLM_MODEL=qwen3.6-plus
export UI_LANG=zh
export LLM_REPLY_LANG=en
streamlit run app.py
```

### Using a non-OpenAI provider

Any OpenAI-compatible endpoint works. Set `LLM_BASE_URL` to the provider's base URL:

```bash
# Alibaba DashScope (阿里云百炼)
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-xxx        # your DASHSCOPE_API_KEY
LLM_MODEL=qwen3.6-plus    # model list: https://help.aliyun.com/model-studio/getting-started/models

# DeepSeek
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=<your-key>
LLM_MODEL=deepseek-chat

# Local Ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3
```

### Verify configuration

When AI is configured, the Gap Analysis page shows the active model in the sidebar. When `LLM_API_KEY` is not set, AI mode is disabled and a notice is displayed—all rule-based gap analysis still works normally.

## Web Login And Deployment

For public deployment, configure `NBLANE_AUTH_FILE`. See `auth/users.example.yaml`
for the YAML shape and generate password hashes with:

```bash
nblane auth hash-password
```

Tencent Cloud deployment notes: [deploy-tencent-cloud.md](deploy-tencent-cloud.md).
