---
status: active
owner: engineering
last_verified: 2026-05-08
source_of_truth: true
---

# 架构总览

nblane 当前是 Python/Streamlit 主体、文件优先的数据系统。

```text
CLI / Streamlit / MCP
        |
        v
src/nblane/core/
        |
        v
profiles/ + teams/ + schemas/
```

## 运行入口

| 入口 | 文件 | 说明 |
|------|------|------|
| CLI | `src/nblane/cli.py`、`src/nblane/commands/` | profile、context、sync、validate、gap、evidence、ingest、public、team、auth |
| Web UI | `app.py`、`pages/` | Streamlit 多页面应用 |
| MCP | `src/nblane/mcp_server.py` | stdio MCP resources/tools |
| Public Blog Editor | `src/nblane/public_blog_editor_component/` | Streamlit custom component + bundled frontend |
| Kanban Board | `src/nblane/kanban_board_component/` | Streamlit custom component + bundled frontend |

## 核心模块

| 模块 | 作用 |
|------|------|
| `profile_io.py` | profile 路径、安全加载、初始化、skill/evidence 读写 |
| `schema_io.py` | schema 加载和索引 |
| `kanban_io.py` | `kanban.md` parse/render/save/archive |
| `kanban_ai.py` | 看板任务理解、gap、子任务建议 |
| `evidence_resolve.py` | inline evidence + pool refs 物化 |
| `profile_ingest.py` / `ingest_*` | LLM patch 合并、预览、应用 |
| `public_site.py` | public layer、blog、resume、static build |
| `public_curation.py` | evidence 到 public project/output 的整理 |
| `llm.py` | 当前 OpenAI-compatible LLM 薄封装 |
| `file_state.py` | Streamlit 文件快照和冲突检测 |
| `git_backup.py` | 可选写入后 Git 备份 |

## 当前数据边界

```text
profiles/<name>/
  SKILL.md
  skill-tree.yaml
  evidence-pool.yaml
  kanban.md
  agent-profile.yaml
  activity-log.yaml
  learning-log.yaml
  inbox.yaml
  public-profile.yaml
  resume-source.yaml
  projects.yaml
  outputs.yaml
  public-library.yaml
  blog/
  media/

teams/<team>/
  team.yaml
  product-pool.yaml

schemas/
  *.yaml
```

## 下一阶段架构增量

```text
src/nblane/core/ai/
  AI Gateway, model routing, structured output, run logs

src/nblane/core/workspace_index.py
  文件事实源上的 typed graph / read model

profiles/<name>/project-board.yaml
  内部 project/milestone/task refs

profiles/<name>/research/
  sources, chunks, claims, drafts

src/nblane/core/agent_harness.py
  Codex/OpenCode 配置生成和 handoff task
```

详细关系见 [模块总览图](module-map.md)，AI 分层见 [AI 架构](ai-architecture.md)，文件不变量见 [数据契约](data-contracts.md)。
