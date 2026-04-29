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
# Full setup and LLM config: docs/setup.md
# Rebuilding bundled frontend components also needs Node.js/npm; see docs/setup.md
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

# Skill evidence — inline on a node, or shared pool + refs (see docs/evidence.md)
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
```

### MCP (Cursor)

**Resources** over stdio: `profile://context`, `profile://summary`,
`profile://kanban`, `profile://gap/{task}` (URL-encode the task segment).
**Tools** can append growth log rows, inline evidence, interaction JSONL, and
method drafts (see [docs/mcp.md](docs/mcp.md) · [中文](docs/zh/mcp.md)).
Ingest and full evidence editing remain **CLI / Web**.

### Web UI

```bash
streamlit run app.py
```

Seven surfaces: **Home**, **Skill Tree**, **Gap Analysis**, **Kanban**, **Team
View**, **Profile Health**, and **Public Site**. Step-by-step usage:
[docs/web-ui.md](docs/web-ui.md) · [中文](docs/zh/web-ui.md). Product IA and backlog:
[docs/web-ui-product.md](docs/web-ui-product.md).

Small-team / cloud deployment adds app-level login, profile/team permissions,
lightweight file conflict checks, and optional Git backup. Configure
`NBLANE_AUTH_FILE` and see [docs/deploy-tencent-cloud.md](docs/deploy-tencent-cloud.md)
· [中文](docs/zh/tencent-cloud-deploy.md).

---

## Typical workflow (cold start → plan → skills)

End state: `skill-tree.yaml` and `evidence-pool.yaml` stay truthful, `SKILL.md`
generated blocks match the tree (`nblane sync`), and `nblane context` exports a
fresh system prompt. Order matters: **pool → tree → validate → sync** (see
[Profile documents relationship](docs/profile-documents-relationship.md)).

1. **Bootstrap** — `pip install -e .`, configure `LLM_API_KEY` if you use AI
   features ([setup](docs/setup.md)). `nblane init yourname`, pick a
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
   scriptable edits ([evidence](docs/evidence.md)).

7. **Check gaps before big tasks** — `nblane gap yourname "…"` (optional
   `--llm-router`) to see prerequisites and missing depth.

8. **Ship checks** — `nblane validate yourname`, then
   `nblane sync yourname --write` if anything drifted. Refresh the agent with
   `nblane context yourname` and paste into your tool of choice.

**中文说明：** 上述步骤与 [中文文档索引](docs/zh/README.md)、[Profile 文档关系与闭环](docs/profile-documents-relationship.md) 中的「简历摄入 / 看板闭环」一致；命令与页面名以英文界面为准，`LLM_REPLY_LANG=zh` 时提示与 Streamlit 文案为中文。

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

- [中文文档](docs/zh/README.md)
- [Documentation index (English)](docs/README.md)
- [Installation & LLM Configuration](docs/setup.md)
- [Product Design (v0.2)](docs/product.md)
- [Web experience design (Streamlit)](docs/web-ui-product.md) · [中文](docs/zh/web-ui-product.md)
- [Web UI user guide](docs/web-ui.md) · [中文](docs/zh/web-ui.md)
- [Public Site, Blog, and Resume](docs/public-site.md) · [中文](docs/zh/public-site.md)
- Kanban user guide · [中文](docs/zh/kanban.md)
- [Design Manual & Milestones](docs/design.md) · [中文](docs/zh/design.md)
- [Architecture & Design Principles](docs/architecture.md)
- [SKILL.md Format Reference](docs/profile-format.md)
- [Skill Tree Schema Guide](docs/skill-tree-schema.md)
- [Skill evidence (CLI, YAML, Web)](docs/evidence.md) · [中文](docs/zh/evidence.md)
- [Profile documents relationship](docs/profile-documents-relationship.md)
- [MCP server (Cursor, any workspace)](docs/mcp.md) · [中文](docs/zh/mcp.md)

---

## Philosophy

> "Your SKILL.md is your system prompt. The agent that loads it is not a tool — it's a prior."

The format is intentionally plain text. No database. No server. Git is the source of truth. The complexity is in what you write, not in the infrastructure.
