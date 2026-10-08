# AGENTS.md — nblane (大佬之路)

Guidance for AI coding agents working in this repository. Code comments and
README are in English; the **canonical documentation is Chinese**
(`docs/zh/`), with English docs (`docs/README.md`, `docs/en/`) kept as
pointers/summaries.

## Project overview

nblane is a **Human + Agent co-evolution system** for one person and their
own agent. Each user maintains a profile directory with a `SKILL.md` (a
living document that doubles as an agent system prompt; `core/sync.py`
rewrites its generated block, `core/context.py` builds the prompt), a
`skill-tree.yaml`, an `evidence-pool.yaml`, a `kanban.md`, goals, projects,
research and public-layer files.

Design principles that shape all changes:

- **File-first, no database**: YAML / Markdown files are the source of truth;
  Git is the backup mechanism (`core/git_backup.py`). There are services
  (SPA + API on 8504, Reader API on 8502), but they hold no state of their
  own beyond the files.
- Data lives in `profiles/<name>/` and `schemas/`; the Python package in
  `src/nblane/` is logic over those files.
- Mutation order matters: **pool → tree → validate → sync**
  (see `docs/zh/architecture/data-contracts.md`).
- Agents reach nblane over HTTP with a service account; their writes are
  direct and undoable, important ones need a chat confirmation
  (`core/agent_policy.py`, see `docs/zh/guides/assistant.md`).
- Public output is private by default and published only after human
  confirmation.
- `profiles/<name>/` is gitignored except `profiles/template/`, which is the
  reference layout. Real profiles (`alice/`, `王军/`) are user data — do not
  commit them or treat them as fixtures.

## Technology stack

- **Python ≥ 3.11**, packaged with setuptools (`pyproject.toml`), src layout.
  Install with `pip install -e .`. A `.venv/` at the repo root is the
  convention (`scripts/dev-web.sh` requires `.venv/bin/uvicorn`).
- **CLI**: `nblane` entry point (`nblane.cli:main`).
- **Web UI = SPA**: `src/nblane/web_ui/frontend` — Vite + React 18 +
  TypeScript + Mantine 8 + TanStack Query + React Router; BlockNote for the
  content editor, three.js for the home star map. Theme tokens live in
  `src/theme.ts` (dark only). Build output `src/nblane/web_ui/static/` is
  **committed** and shipped via `pyproject.toml` package-data, so installs
  serve the SPA without Node.
- **SPA backend** `nblane.web_api:app` (FastAPI, port **8504**): one process
  serves both the built SPA and `/api/v1/*` (cookie session auth, ETag /
  `If-Match` → 412 conflicts, jobs + SSE for long AI tasks, agent write
  guard).
- **Reader API** `nblane.web_reader_api:app` (FastAPI, port **8502**): paper
  library and PDF reader pages that the SPA embeds via iframe, plus the
  `/auth/session` login handoff.
- **API contract**: FastAPI OpenAPI → `src/nblane/web_ui/frontend/openapi.json`
  (committed snapshot) → `openapi-typescript` → `src/api/schema.d.ts`.
- **MCP**: `nblane-mcp` (stdio) is for local Cursor / Claude Code only; no
  login, no profile ACL. Not the assistant channel; expansion is paused.
- **Node.js**: SPA and component frontend builds, vitest, Playwright e2e
  (root `package.json` has `@playwright/test` only).
- **LLM features**: OpenAI-compatible API via `src/nblane/core/llm.py` and
  the AI Gateway in `src/nblane/core/ai/`, configured in `.env`
  (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`; see `.env.example`).
  Optional: local translation models (llama.cpp), self-hosted GROBID,
  Codex CLI, visual generation.
- Key deps: pyyaml, pydantic v2, fastapi, uvicorn, openai, httpx, PyMuPDF,
  pypdf, mcp. Lockfile: `uv.lock` (uv) — `requirements.txt` mirrors
  `pyproject.toml` for pip users.

## Repository layout

- `src/nblane/` — the Python package:
  - `cli.py` + `commands/` — CLI entry and subcommands (`profile`,
    `evidence`, `ingest`, `public`, `agent`, `codex`, `research`, `health`,
    `backup`, `openclaw`, …).
  - `core/` — all business logic, one module per domain concern:
    `profile_io.py` / `schema_io.py` / `kanban_io.py` (domain file I/O;
    `io.py` is a compatibility facade), `models.py`, `evidence_*.py`,
    `crystallize.py`, `goals.py`, `north_star.py`, `projects_board.py` /
    `project_board*.py`, `activity_log.py`, `context.py`, `validate.py`,
    `sync.py`, `ingest_*.py`, `content_workspace.py`, `career_workspace.py`,
    `public_site.py`, `research_workspace.py` + `research_papers/`, `ai/`
    (gateway, router, backends, structured output, runs), agent write policy
    (`agent_policy.py`, `agent_ops.py`, `agent_journal.py`), `openclaw_*.py`,
    `auth.py`, `file_state.py`, `file_lock.py`, `file_write.py`,
    `git_backup.py`, `backup_targets.py`, `grobid_service.py`,
    `workshop_service.py`.
  - `web_api/` — SPA backend: `routes_v1.py` (most `/api/v1` routes),
    `auth.py`, `agent_guard.py`, `assistant.py`, `agents_setup.py`,
    `research*.py`, `workshop*.py`, `local_models.py`, `grobid.py`,
    `jobs.py`, `schemas.py` (pydantic models), `spa.py` (static mount).
  - `web_reader_api/` — Reader API (paper library, reader, auth handoff).
  - `web_ui/frontend/` — SPA source (`src/pages`, `src/components`,
    `src/starmap`, `src/api`); `web_ui/static/` — committed build output.
  - `mcp_server.py` — local MCP stdio server.
  - `paper_library_component/frontend/` — Paper Library frontend (Vite +
    React); its committed `static/` build is served by the Reader API.
  - `i18n/{en,zh}/paper_library.yaml` — Paper Library copy (Reader API).
- `profiles/template/` — the only committed profile; copied by `nblane init`.
- `schemas/` — domain skill-tree definitions; `schemas/.learned/` is
  local-only, gitignored.
- `scripts/` — `dev-web.sh` (tmux dev launcher), `dump-openapi.sh`,
  `openclaw/` (assistant skill `skills/nblane/SKILL.md`, HTTP client
  `skills/bin/nblane_api.py`, installer).
- `tests/` — pytest suite + `tests/e2e/` (Playwright, TypeScript).
- `docs/zh/` — canonical docs. Keep them in sync when you change documented
  behavior.

## Build and run commands

```bash
# Setup (Python 3.11+)
python3 -m venv .venv && .venv/bin/pip install -e .
cp .env.example .env          # fill LLM_API_KEY only if using AI features

# CLI smoke
nblane init yourname
nblane validate               # validate all profiles against schemas/
nblane status                 # skill tree summary

# Web dev: Reader API 8502 + SPA backend 8504 in tmux
scripts/dev-web.sh            # start (default command)
scripts/dev-web.sh --reload   # uvicorn --reload --reload-dir src
scripts/dev-web.sh --isolated # ports 18502/18504, data in .dev-data/ + .dev-assets/,
                              # auth from .dev-data/auth/users.yaml if present
scripts/dev-web.sh status|stop
# Other options: --reader-port N, --web-api-port N, --no-web-api,
# --profile NAME, --root PATH, --asset-root PATH, --grobid [--grobid-port N],
# --env-file PATH, --auth-file PATH. Run with --help for the full list.

# SPA frontend (only for web_ui/frontend changes)
cd src/nblane/web_ui/frontend
npm install
npm run dev                   # Vite on 5173, proxies /api to 8511
                              # (VITE_API_PROXY_TARGET to override)
npm run build                 # tsc + vite build into ../static — commit it
npm run test                  # vitest

# API contract changed? Regenerate types, then test + build
scripts/dump-openapi.sh       # from repo root: updates openapi.json
cd src/nblane/web_ui/frontend && npm run gen:api

# Paper Library frontend (served by the Reader API; built by CI)
cd src/nblane/paper_library_component/frontend && npm install && npm run build
```

Environment variables that matter: `NBLANE_ROOT` (data root; defaults to repo
root), `NBLANE_AUTH_FILE` (enables login; empty = synthetic local admin),
`NBLANE_READER_API_BASE` (SPA → Reader API origin; `0` means same origin
behind Caddy; if unreachable from the browser the library/reader iframes are
blank), `LLM_REPLY_LANG` (model reply language),
`NBLANE_DISABLE_NETWORK_LOOKUPS` (set by tests).

## Testing instructions

```bash
# Unit tests (run from repo root; no pytest config file, plain pytest)
.venv/bin/pip install pytest
.venv/bin/pytest -q                    # full suite
.venv/bin/pytest tests/test_gap.py -q  # one file

# SPA unit tests
cd src/nblane/web_ui/frontend && npm run test

# Browser e2e (requires a running dev stack; SPA specs default to
# http://127.0.0.1:18504 via NBLANE_E2E_SPA_BASE_URL)
npm install
npm run test:e2e:install               # or npm run test:e2e:install:cn (China mirror)
npm run test:e2e                       # all specs
npm run test:e2e:spa                   # SPA smoke only
```

- `tests/conftest.py` puts the repo root on `sys.path` and sets
  `NBLANE_DISABLE_NETWORK_LOOKUPS=1` — tests must not hit the network or
  require LLM keys.
- Unit tests are plain pytest (some class-based), one `test_<module>.py` per
  module; use `tmp_path`-style isolation and never write to real
  `profiles/`.
- `tests/test_web_api_openapi_snapshot.py` fails when `openapi.json` drifts
  from the live app.
- CI (`.github/workflows/ci.yml`) runs `pip install -e .`, `pytest -q`,
  `python -m nblane.cli validate`, `status`, an import smoke, and the
  `frontend-artifacts` job (rebuilds the SPA and component frontends and
  fails if committed build output is stale). Keep them green.

## Design workflow

See [`docs/zh/product/design-language.md`](docs/zh/product/design-language.md)
(binding for all agents).

## Code style guidelines

- Python ≥ 3.11, `from __future__ import annotations` at the top of modules,
  dataclasses in `core/models.py`, type hints on public functions, English
  docstrings/comments.
- **I/O is centralized**: read/write profile files through the `*_io.py`
  modules and `core/file_write.py`; never scatter direct `open()`/`yaml.load`
  of profile data around the codebase. Use `yaml.safe_load` semantics.
- Compatibility facades exist (`core/io.py`, `core/profile_ingest.py`) —
  prefer the split modules (`ingest_parse/merge/preview/apply`) in new code.
- SPA copy lives in the frontend source (Chinese). Python-rendered UI copy
  (Reader API pages) goes into `src/nblane/i18n/{en,zh}/<section>.yaml`, not
  inline; respect `UI_LANG`.
- New AI flows go through `core/ai/` (gateway/router/backends) and
  `core/llm.py`; do not call provider SDKs directly from routes or pages.
- New mutating `/api/v1` routes must get an entry in
  `web_api/agent_guard.py` `ROUTE_ACTIONS` (unmapped routes default to T2
  for agent accounts) and, if journaled, an entity kind in
  `core/agent_journal.py`.
- Backend contract changes: run `scripts/dump-openapi.sh`, then
  `npm run gen:api` in the SPA frontend; never hand-edit `schema.d.ts`.
- Docs discipline (from `docs/zh/README.md`): active docs keep front matter
  (`status`, `owner`, `last_verified`, `source_of_truth`); product status
  lives only in `docs/zh/project/status.md` and `milestones.md`; do not add
  long-lived `*-workplan.md` files.

## Security considerations

- **Never commit secrets**: `.env`, `.reader-token-secret` are gitignored;
  `.env.example` documents all keys. Do not read or echo the real `.env`.
- Personal data stays local: `profiles/*` (except `template/`) and
  `schemas/.learned/` are gitignored on purpose.
- Path safety: profile IDs are user input — go through `profile_io.py`
  path helpers rather than string-joining paths.
- Web auth is optional and off by default for single-user local runs; setting
  `NBLANE_AUTH_FILE` turns on login. `auth/users.yaml` is written only through
  `core/auth_store.py` (lock + atomic write, 0600) and never committed to the
  data repo's git; sessions carry a `session_version` so password changes,
  disabling and "logout all" revoke them; machine clients use revocable
  `nbl_…` Bearer tokens. Roles are `admin` and `member` (member
  sees only its own profiles); an account with `agent: true` is an agent
  service account whose writes go through `web_api/agent_guard.py`
  (journal + undo, 428 chat confirmation, 403 for web-only actions).
- MCP stdio has no login and no ACL; keep it local.
- Production: systemd + Caddy, ports bound to `127.0.0.1`; never expose
  `8502`/`8504`/GROBID `8070` directly.
- `config.yaml` at repo root is a **mihomo proxy config** (local network
  tooling), not app configuration — do not confuse it with nblane settings.

## Deployment

- Local dev: `scripts/dev-web.sh` (tmux). With SSH/IDE port forwarding,
  forward **both** the SPA backend port (8504 / 18504) and the Reader API
  port (8502 / 18502).
- Production: systemd units `nblane-web-api.service` (8504) and
  `nblane-reader.service` (8502) behind Caddy; code in
  `/srv/nblane-app/nblane`, data in `/srv/nblane-data` (`NBLANE_ROOT`).
  See `docs/zh/guides/deployment-tencent-cloud.md` and
  `docs/zh/guides/mihomo-deployment.md`.
- Public static sites: `nblane public build <name> --out dist/public/<name>`
  or the 公开站点 page.
