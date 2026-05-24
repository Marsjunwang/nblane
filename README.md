# nblane · 大佬之路

> **Human + Agent + Team**: human capability, agent capability, and team
> shared pools compound together—Human ↑, Agent ↑, synergy ↑↑, and
> `(Human + Agent) × Team` ↑↑↑.

Each person in nblane maintains a `SKILL.md` — a living document that is simultaneously a personal growth tracker and a system prompt. Load it into any agent framework and the agent becomes a projection of you: calibrated to your knowledge, your taste, your blind spots. Teams can share a **product pool** under `teams/` (`team.yaml` + `product-pool.yaml`).

As you update the files, the agent updates too. This is co-evolution.

---

## Crew

| Name | Domain | Year | Lit nodes |
|------|--------|------|-----------|
| *(add yourself)* | | | |

---

## Quick Start

```bash
# Full setup and LLM config: docs/zh/guides/setup.md
# Rebuilding bundled frontend components also needs Node.js/npm; see docs/zh/guides/setup.md
pip install -e .

# Create your profile
nblane init yourname

# Edit profiles/yourname/SKILL.md, skill-tree.yaml,
# evidence-pool.yaml (optional shared evidence catalog), kanban.md

# Generate an agent system prompt (default: chat mode)
nblane context yourname

# Choose a prompt mode: chat | review | write | plan
nblane context yourname --review

# Exclude kanban from the prompt
nblane context yourname --no-kanban

# Paste the output as a system prompt into Claude / GPT / any agent

# Check skill tree progress (all profiles, or one)
nblane status
nblane status yourname

# Log a growth event
nblane log yourname "finished first manipulation demo"

# Sync the generated section in SKILL.md from skill-tree.yaml
nblane sync yourname --check   # dry-run: show drift only
nblane sync yourname --write   # rewrite the generated block

# Validate skill-tree.yaml against schemas/ (all or one profile)
nblane validate
nblane validate yourname

# Read-only profile health / growth review
nblane health yourname

# Find skill gaps for a natural-language task
nblane gap yourname "OpenVLA robot control"
nblane gap yourname --node grasp_planning

# Show team + product pool summary
nblane team example-team

# Skill evidence — inline on a node, or shared pool + refs (see docs/zh/reference/evidence.md)
nblane evidence yourname ros2_basics add \
  --type project --title "Real robot bringup demo"
# Create a pool record once (prints id); link it from multiple skills
nblane evidence yourname pool add \
  --type project --title "Shared milestone demo"
nblane evidence yourname link ros2_basics <evidence_id>
nblane evidence yourname unlink ros2_basics <evidence_id>
nblane evidence yourname pool remove <evidence_id>
# With refs elsewhere: add --prune-refs to strip refs then remove row
nblane evidence yourname pool deprecate <evidence_id>

# LLM-assisted ingest (requires LLM_API_KEY in .env)
nblane ingest-resume yourname --file resume.txt
# nblane ingest-resume yourname --stdin --dry-run
# Optional: --allow-status-change (LLM solid/learning rubric), --no-bump-locked
nblane ingest-kanban yourname --dry-run

# Public surface: profile-scoped public files -> static website
nblane public init yourname
nblane public validate yourname
nblane public blog new yourname --title "My post"
nblane public build yourname --out dist/public/yourname --base-url https://www.example.com

# Optional Codex helpers
nblane codex status
nblane codex install --print-command
nblane codex local run <agent_task_id> --profile yourname
nblane codex cloud submit <agent_task_id> --profile yourname
nblane codex cloud refresh <agent_task_id> --profile yourname --diff
```

Kanban can use local Codex as a read-only AI backend for its existing task
understanding, subtask drafting, and Done-to-evidence actions. Patch-producing
Codex handoff remains an explicit CLI / Agent Activity review workflow.

### MCP (Cursor)

**Resources** over stdio: `profile://context`, `profile://summary`,
`profile://kanban`, `profile://gap/{task}` (URL-encode the task segment).
**Tools** can append growth log rows, inline evidence, interaction JSONL, and
method drafts (see [MCP reference](docs/zh/reference/mcp.md)).
Ingest and full evidence editing remain **CLI / Web**.

### Web UI

Run the Web UI from the repo root. The Research PDF Reader is served by the
FastAPI sidecar; local development needs both the Reader API and Streamlit.

Start the Reader API first, then start Streamlit with a browser-reachable
`NBLANE_READER_API_BASE`:

```bash
# Terminal 1
PYTHONPATH=src .venv/bin/uvicorn nblane.web_reader_api:app \
  --host 127.0.0.1 --port 8502 --reload

# Terminal 2
NBLANE_READER_API_BASE=http://127.0.0.1:8502 \
PYTHONPATH=src .venv/bin/streamlit run app.py \
  --server.address=127.0.0.1 --server.port=8503 --server.headless=true
```

When you view Streamlit through SSH / IDE port forwarding, forward both `8503`
and `8502`, and set `NBLANE_READER_API_BASE` to the URL your browser can reach
for port `8502`. If this variable is omitted without a reverse proxy, the
iframe uses `/reader/view/...`; plain Streamlit will serve its own shell at that
path, which looks like a blank Reader.

In production behind Caddy, leave `NBLANE_READER_API_BASE` unset and route
`/reader/*` to the FastAPI sidecar. Translation is shown as a semantic flow by
default; set `NBLANE_READER_DEBUG_OVERLAY=1` only when debugging the legacy PDF
overlay renderer.

Browser e2e tests use Playwright from the repo root. On a fresh machine, install
the Node dev dependency and Chromium browser binary before running them:

```bash
npm install
npm run test:e2e:install
npm run test:e2e
```

In mainland China, use npm and Playwright browser mirrors:

```bash
npm_config_registry=https://registry.npmmirror.com npm install
npm run test:e2e:install:cn
npm run test:e2e
```

The China mirror installer currently targets Linux x64 and downloads Chrome for
Testing from `cdn.npmmirror.com/binaries/chrome-for-testing`.

Core surfaces include **Home**, **Skill Tree**, **Gap Analysis**, **Kanban**,
**Research Workspace**, **Output Studio**, **Public Build**, **Team View**,
and **Profile Health**. Step-by-step usage:
[Web UI guide](docs/zh/guides/web-ui.md). Product IA and backlog:
[Web experience](docs/zh/product/web-experience.md).

Small-team / cloud deployment adds app-level login, profile/team permissions,
lightweight file conflict checks, and optional Git backup. Configure
`NBLANE_AUTH_FILE` and see
[Tencent Cloud deployment](docs/zh/guides/deployment-tencent-cloud.md).

---

## Typical workflow (cold start → plan → skills)

End state: `skill-tree.yaml` and `evidence-pool.yaml` stay truthful, `SKILL.md`
generated blocks match the tree (`nblane sync`), and `nblane context` exports a
fresh system prompt. Order matters: **pool → tree → validate → sync** (see
[Data contracts](docs/zh/architecture/data-contracts.md)).

1. **Bootstrap** — `pip install -e .`, configure `LLM_API_KEY` if you use AI
   features ([setup](docs/zh/guides/setup.md)). `nblane init yourname`, pick a
   `schema:` in `skill-tree.yaml`, and copy node ids you care about from
   `schemas/`.

2. **Identity & narrative** — Edit `profiles/yourname/SKILL.md` (identity,
   taste, goals). This is human-written; generated skill-tree blocks are
   overwritten by sync.

3. **Resume / long text (cold or bulk catch-up)** — With the LLM configured:
   - **CLI:** `nblane ingest-resume yourname --file resume.txt` (use
     `--dry-run` to preview merged YAML; add `--allow-status-change` only if
     you want the model to raise node `status`).
   - **Web:** Home → Overview → **Resume / long text** — generate a draft,
     review the YAML preview, then apply.
   Ingest updates `evidence-pool.yaml` and `skill-tree.yaml`, then runs
   validate + sync when apply succeeds.

4. **Plan the week** — Use **Kanban** (`kanban.md`) for Doing / Queue / Done.
   Nothing here changes the skill tree until you promote work into evidence.

5. **Turn finished work into evidence** — When tasks land in **Done**, either:
   - **Web:** Kanban page → **Done → evidence** — select tasks, generate draft,
     optionally allow status updates, apply; or
   - **CLI:** `nblane ingest-kanban yourname` (same flags as resume ingest).

6. **Adjust skills directly (anytime)** — **Skill Tree** page or YAML: set
   `status`, `note`, inline evidence, **Evidence pool** rows, and
   `evidence_refs` per node. Or use `nblane evidence` subcommands for
   scriptable edits ([evidence](docs/zh/reference/evidence.md)).

7. **Check gaps before big tasks** — `nblane gap yourname "…"` (optional
   `--llm-router`) to see prerequisites and missing depth.

8. **Ship checks** — `nblane validate yourname`, then
   `nblane sync yourname --write` if anything drifted. Refresh the agent with
   `nblane context yourname` and paste into your tool of choice.

**中文说明：** 上述步骤与 [中文文档索引](docs/zh/README.md)、[数据契约](docs/zh/architecture/data-contracts.md) 中的「简历摄入 / 看板闭环」一致；命令与页面名以英文界面为准。`UI_LANG=zh` 控制 Streamlit 界面文案，`LLM_REPLY_LANG=zh` 只控制模型提示与回复语言。

---

## Project Structure

```
nblane/
├── src/nblane/          # Python package (pip install -e .)
│   ├── cli.py           # CLI entry point
│   └── core/            # All business logic
│       ├── models.py    # Data classes
│       ├── io.py        # File I/O compatibility facade
│       ├── profile_io.py / schema_io.py / kanban_io.py / team_io.py
│       │                # Domain-specific file I/O
│       ├── gap.py       # Task → skill match & gap detection
│       ├── evidence_resolve.py  # Pool refs + inline → materialized evidence
│       ├── context.py   # Agent system prompt generation
│       ├── validate.py  # Skill-tree validation
│       ├── sync.py      # SKILL.md generated section sync
│       ├── status.py    # Skill tree summary
│       ├── team.py      # Team operations
│       ├── llm.py       # LLM client wrapper
│       ├── profile_ingest.py      # Ingest compatibility facade
│       ├── ingest_*.py            # Parse / merge / preview / apply ingest
│       ├── profile_health.py      # Read-only growth review
│       └── profile_ingest_llm.py  # Resume / kanban Done → JSON
├── app.py + pages/      # Streamlit Web UI
├── profiles/            # User data + public layer (SKILL.md, skill-tree, kanban, public-profile, blog, media)
├── schemas/             # Domain skill-tree definitions
├── teams/               # Team data (team.yaml, product-pool.yaml)
├── tests/               # Tests
└── docs/                # Documentation
```

---

## Docs

- [中文文档总览](docs/zh/README.md) — canonical project documentation.
- [English docs entry](docs/README.md) — short pointer to the canonical Chinese docs.
- [Product overview](docs/zh/product/overview.md)
- [Core loop](docs/zh/product/core-loop.md)
- [Roadmap](docs/zh/product/roadmap.md)
- [Current status](docs/zh/project/status.md)
- [Milestones](docs/zh/project/milestones.md)
- [Architecture overview](docs/zh/architecture/overview.md)
- [Module map](docs/zh/architecture/module-map.md)
- [AI architecture](docs/zh/architecture/ai-architecture.md)
- [Data contracts](docs/zh/architecture/data-contracts.md)
- [Setup](docs/zh/guides/setup.md)
- [Web UI guide](docs/zh/guides/web-ui.md)
- [Kanban guide](docs/zh/guides/kanban.md)
- [Public site guide](docs/zh/guides/public-site.md)
- [MCP reference](docs/zh/reference/mcp.md)
- [Agent harness strategy](docs/zh/reference/agent-harness.md)
- [Evidence reference](docs/zh/reference/evidence.md)

---

## Philosophy

> "Your SKILL.md is your system prompt. The agent that loads it is not a tool — it's a prior."

The format is intentionally plain text. No database. No server. Git is the source of truth. The complexity is in what you write, not in the infrastructure.
