# nblane · 大佬之路

> **Human + Agent co-evolution.** You and your own agent form one long-term
> growth unit; Goal + Skill + Evidence form one reviewable capability map.

Each person in nblane keeps a `SKILL.md`: a living document that is both a
growth record and an agent system prompt. Load it into any agent and the
agent works from your goals, skills and evidence. As you update the files,
the agent updates too.

Everything is plain files (YAML / Markdown) under `profiles/<name>/`, backed
up with Git. No database.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
cp .env.example .env            # only needed for AI features (LLM_API_KEY)

nblane init yourname            # create profiles/yourname/
nblane validate                 # check skill-tree.yaml against schemas/
nblane status yourname          # skill tree summary
nblane sync yourname --write    # refresh the generated block in SKILL.md
nblane context yourname         # print the agent system prompt
```

Web UI (React SPA + API on 8504, Reader API on 8502, started in tmux):

```bash
scripts/dev-web.sh              # open http://127.0.0.1:8504
scripts/dev-web.sh --isolated   # 18504/18502 with separate .dev-data/
scripts/dev-web.sh status|stop
```

The SPA covers home (star map and goals), projects, skill tree, evidence,
research (paper library and reader), content and career workspaces, and the
public site build.

## Docs

The Chinese docs under [`docs/zh/`](docs/zh/README.md) are the source of
truth. English entry: [`docs/README.md`](docs/README.md).

- [Product overview](docs/zh/product/overview.md)
- [Setup](docs/zh/guides/setup.md)
- [Web UI guide](docs/zh/guides/web-ui.md)
- [Architecture overview](docs/zh/architecture/overview.md)
- [CLI reference](docs/zh/reference/cli.md)
- [Deployment](docs/zh/guides/deployment-tencent-cloud.md)

Contributors and coding agents: see [AGENTS.md](AGENTS.md).
