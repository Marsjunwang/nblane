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
| `LLM_BASE_URL` | `https://api.openai.com/v1` | API base URL |
| `LLM_MODEL` | `gpt-4o` | Model name |
| `LLM_REPLY_LANG` | `en` | Reply language: `en` or `zh`. Also switches **Gap Analysis** UI copy and the AI system prompt (use `en` for international demos). |

`LLM_REPLY_LANG` controls the Streamlit UI (home `app.py`, sidebar Profile, Skill Tree, Gap Analysis, Kanban, Team View, etc.) and model output; no separate UI locale is required.

### Option A — `.env` file (recommended)

Create a `.env` file at the repo root (already in `.gitignore`):

```bash
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

nblane loads this file automatically on startup via `python-dotenv`.

### Option B — shell environment variables

```bash
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-4o
streamlit run app.py
```

### Using a non-OpenAI provider

Any OpenAI-compatible endpoint works. Set `LLM_BASE_URL` to the provider's base URL:

```bash
# Alibaba DashScope (阿里云百炼)
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-xxx        # your DASHSCOPE_API_KEY
LLM_MODEL=qwen-plus       # model list: https://help.aliyun.com/model-studio/getting-started/models

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
