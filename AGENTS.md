# AGENTS.md — nblane (大佬之路)

Guidance for AI coding agents working in this repository. Code comments and
README are in English; the **canonical documentation is Chinese**
(`docs/zh/`), with English docs (`docs/README.md`, `docs/en/`) kept as
pointers/summaries.

## Project overview

nblane is a **Human + Agent + Team co-evolution system**: each user maintains
a profile directory with a `SKILL.md` (a living document that doubles as an
agent system prompt), a `skill-tree.yaml`, an `evidence-pool.yaml`, a
`kanban.md`, and more. Teams share a product pool under `teams/`.

Design principles that shape all changes:

- **File-first, no database, no server required**: YAML / Markdown files are
  the source of truth; Git is the backup mechanism (optional `git_backup.py`).
- Data lives in `profiles/<name>/`, `teams/<id>/`, `schemas/` — the Python
  package in `src/nblane/` is pure logic over those files.
- Mutation order matters: **pool → tree → validate → sync**
  (see `docs/zh/architecture/data-contracts.md`).
- `profiles/<name>/` is gitignored except `profiles/template/`, which is the
  reference layout. Real profiles (`alice/`, `王军/`) are user data — do not
  commit them or treat them as fixtures.

## Technology stack

- **Python ≥ 3.11**, packaged with setuptools (`pyproject.toml`), src layout.
  Install with `pip install -e .`. A `.venv/` at the repo root is the
  convention (`scripts/dev-web.sh` requires `.venv/bin/uvicorn` and
  `.venv/bin/streamlit`).
- **CLI**: `nblane` entry point (`nblane.cli:main`), plus `nblane-mcp` (MCP
  stdio server for Cursor integration).
- **Web UI**: Streamlit multi-page app — `app.py` + `pages/*.py`, theme in
  `.streamlit/config.toml`.
- **Reader API sidecar**: FastAPI + uvicorn (`nblane.web_reader_api:app`)
  serving the Research PDF reader / Paper Library. Local dev runs **both**
  Streamlit (8503) and Reader API (8502).
- **Streamlit custom components** with bundled frontends (Vite + React for
  newer ones, static HTML for older ones) under
  `src/nblane/*_component/frontend/`; built assets are declared in
  `pyproject.toml` `[tool.setuptools.package-data]`.
- **Node.js**: only for e2e tests (Playwright) and component frontend builds;
  root `package.json` has `@playwright/test` only.
- **LLM features**: OpenAI-compatible API via `src/nblane/core/llm.py`,
  configured in `.env` (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`; see
  `.env.example`). Optional: visual generation (DashScope/Wan), Codex
  CLI/Cloud integration, self-hosted GROBID for PDF structure extraction.
- Key deps: pyyaml, pydantic v2, streamlit, fastapi, openai, httpx, pandas,
  PyMuPDF, pypdf, mcp. Lockfile: `uv.lock` (uv) — `requirements.txt` mirrors
  `pyproject.toml` for pip users.

## Repository layout

- `src/nblane/` — the Python package:
  - `cli.py` + `commands/` — CLI entry and subcommand implementations
    (`profile`, `evidence`, `ingest`, `public`, `team`, `agent`, `codex`,
    `research`, `auth`, …).
  - `core/` — all business logic, one module per domain concern:
    `profile_io.py` / `schema_io.py` / `kanban_io.py` / `team_io.py` (domain
    file I/O; `io.py` is a compatibility facade), `models.py` (dataclasses +
    enums), `evidence_resolve.py`, `context.py` (system-prompt generation),
    `validate.py`, `sync.py` (rewrites the generated block in `SKILL.md`),
    `gap.py`, `profile_ingest*.py` + `ingest_*.py` (LLM resume/kanban
    ingest: parse → merge → preview → apply), `llm.py`, `public_site.py`,
    `research_workspace.py` + `research_papers/`, `ai/` (gateway, router,
    backends, structured output), `auth.py`, `file_state.py` (write-conflict
    detection), `git_backup.py`.
  - `mcp_server.py` — MCP resources/tools over stdio.
  - `web_*.py` — Streamlit helpers (shell, i18n, auth, cache, shared).
  - `*_component/` — Streamlit custom components with `frontend/` subprojects.
  - `i18n/{en,zh}/*.yaml` — UI copy, loaded lazily via `importlib.resources`.
- `app.py`, `pages/` — Streamlit app entry and pages (Skill Tree, Gap
  Analysis, Kanban, Team View, Profile Health, Output Studio, Research,
  Review, Agent Activity, Public Build, Project Board, Settings, …).
- `profiles/template/` — the only committed profile; copy template for
  `nblane init`.
- `schemas/` — domain skill-tree definitions (e.g. `robotics-engineer.yaml`)
  plus Python schema helpers; `schemas/.learned/` is local-only, gitignored.
- `teams/` — team data (`team.yaml`, `product-pool.yaml`); `_template/` +
  `example-team/`.
- `tests/` — pytest suite (~80 files, one per module) + `tests/e2e/`
  (Playwright, TypeScript).
- `scripts/dev-web.sh` — tmux dev launcher (see below).
- `docs/zh/` — canonical docs (product / project / architecture / guides /
  reference). Keep them in sync when you change documented behavior.

## Build and run commands

```bash
# Setup (Python 3.11+)
python3 -m venv .venv && .venv/bin/pip install -e .
cp .env.example .env          # fill LLM_API_KEY only if using AI features

# CLI smoke
nblane init yourname
nblane validate               # validate all profiles against schemas/
nblane status                 # skill tree summary

# Web dev (starts Reader API 8502 + Streamlit 8503 in tmux)
scripts/dev-web.sh            # start (default)
scripts/dev-web.sh --isolated # ports 18502/18503, data in .dev-data/, no prod writes
scripts/dev-web.sh status|stop

# Component frontend rebuild (only for *_component/frontend changes)
cd src/nblane/<name>_component/frontend && npm install && npm run build
```

Environment variables that matter: `NBLANE_ROOT` (data root; defaults to repo
root), `NBLANE_READER_API_BASE` (Streamlit → sidecar URL; if unreachable from
the browser, Reader/Paper Library iframes render blank),
`NBLANE_AUTH_FILE` (enables app-level login; empty disables),
`UI_LANG` (`en`/`zh` Streamlit copy), `LLM_REPLY_LANG` (model prompt/reply
language), `NBLANE_DISABLE_NETWORK_LOOKUPS` (set by tests).

## Testing instructions

```bash
# Unit tests (run from repo root; no pytest config file, plain pytest)
.venv/bin/pip install pytest
.venv/bin/pytest -q                    # full suite
.venv/bin/pytest tests/test_gap.py -q  # one file

# Browser e2e (requires a running dev server; baseURL from NBLANE_E2E_BASE_URL,
# default http://127.0.0.1:8510)
npm install
npm run test:e2e:install               # or npm run test:e2e:install:cn (China mirror)
npm run test:e2e
```

- `tests/conftest.py` puts the repo root on `sys.path` and sets
  `NBLANE_DISABLE_NETWORK_LOOKUPS=1` — tests must not hit the network or
  require LLM keys.
- Unit tests are plain pytest (some class-based), one `test_<module>.py` per
  core module; use `tmp_path`-style isolation and never write to real
  `profiles/`.
- CI (`.github/workflows/ci.yml`) runs: `pip install -e .`, `pytest -q`,
  `python -m nblane.cli validate`, `status`, and an import smoke of
  `nblane.kanban_ui` + `nblane.core.profile_ingest`. Keep all four green.

## Code style guidelines

- Python ≥ 3.11, `from __future__ import annotations` at the top of modules,
  dataclasses in `core/models.py`, type hints on public functions, English
  docstrings/comments.
- **I/O is centralized**: read/write profile files through the `*_io.py`
  modules and `core/file_write.py`; never scatter direct `open()`/`yaml.load`
  of profile data around the codebase. Use `yaml.safe_load` semantics.
- Compatibility facades exist (`core/io.py`, `core/profile_ingest.py`) —
  prefer the split modules (`ingest_parse/merge/preview/apply`) in new code.
- New UI strings go into `src/nblane/i18n/{en,zh}/<section>.yaml`, not inline;
  respect `UI_LANG` and the `NBLANE_UI_EMOJI=0` opt-out.
- New AI flows go through `core/ai/` (gateway/router/backends) and
  `core/llm.py`; do not call provider SDKs directly from pages.
- Docs discipline (from `docs/zh/README.md`): active docs keep front matter
  (`status`, `owner`, `last_verified`, `source_of_truth`); product status
  lives only in `docs/zh/project/status.md` and `milestones.md`; do not add
  long-lived `*-workplan.md` files.

## Security considerations

- **Never commit secrets**: `.env`, `.reader-token-secret` are gitignored;
  `.env.example` documents all keys. Do not read or echo the real `.env`.
- Personal data stays local: `profiles/*` (except `template/`) and
  `schemas/.learned/` are gitignored on purpose.
- Path safety: profile/team IDs are user input — go through `profile_io.py`
  path helpers rather than string-joining paths.
- Web auth is optional and off by default for single-user local runs; enabling
  `NBLANE_AUTH_FILE` turns on login, permissions, and file-conflict checks
  (see `docs/zh/guides/deployment-tencent-cloud.md`).
- Production deployment: systemd + Caddy, ports bound to `127.0.0.1`, never
  expose `8501`/`8502`/GROBID `8070` directly.
- `config.yaml` at repo root is a **mihomo proxy config** (local network
  tooling), not app configuration — do not confuse it with nblane settings.

## Deployment

- Local dev: `scripts/dev-web.sh` (tmux). SSH/IDE port forwarding must forward
  **both** the Streamlit port and the Reader API sidecar port.
- Production (small team / cloud): systemd + Caddy; see
  `docs/zh/guides/deployment-tencent-cloud.md` and
  `docs/zh/guides/mihomo-deployment.md`.
- Public static sites: `nblane public build <name> --out dist/public/<name>`.
