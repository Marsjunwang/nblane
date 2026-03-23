# MCP server (Cursor & other clients)

The nblane package exposes an MCP server (`python -m nblane.mcp_server` or
`nblane-mcp`) over **stdio**. Clients read **resources** (e.g.
`profile://context`) and may call **tools** that write profile files.

## Scope (for integrators and other agents)

### What is implemented

| Aspect | Detail |
|--------|--------|
| Transport | **stdio** (client spawns a subprocess) |
| MCP primitives | **Resources** (read) + **Tools** (write / suggest) |
| Reads | `profile://summary`, `profile://kanban`, `profile://context`, `profile://gap/{task}` |
| Writes (tools) | `append_growth_log`, `log_skill_evidence`, `log_interaction`, `suggest_skill_upgrade` (text-only suggestion), `crystallize_method_draft` |

### Feature matrix (MCP vs CLI)

| Feature | MCP | Notes |
|---------|-----|------|
| Tree-ish summary + agent-profile focus + Doing | `profile://summary` | Not identical to `nblane status` output format |
| Full system prompt | `profile://context` | Matches **`nblane context`** (kanban included; mode via `NBLANE_CONTEXT_MODE`) |
| Kanban file | `profile://kanban` | Raw `kanban.md` |
| **Gap analysis** | `profile://gap/{task}` | Natural-language task, same core as **`nblane gap <name> "<task>"`** |

### Gap analysis: supported, with differences from CLI

- **Yes —** read **`profile://gap/{task}`** (URL-encoded path segment) runs `gap.analyze` and returns **`format_text`** output.
- **Not exposed in MCP:** `nblane gap ... --node <id>` (explicit node). MCP always uses a **natural-language task** only — use **CLI** for `--node`.
- **Fixed in MCP:** rule matching is **on** (no `--no-rule` equivalent).
- **LLM router:** controlled by **`NBLANE_GAP_USE_LLM`**. MCP sets **`persist_router_keywords=False`** so router keywords are not persisted (CLI may persist by default).

### Not exposed over MCP (use CLI or Web)

- `ingest-resume` / `ingest-kanban`, full `evidence` subcommands, `team`, `sync`,
  `validate`, and kanban **editing** — use **CLI** or **Streamlit** (see
  [web-ui.md](web-ui.md)).
- `profile://context` always includes kanban (no `--no-kanban` switch).

## API reference (how to call each resource)

Use MCP **ReadResource** with these URIs. Except for `gap`, URIs are fixed (no path parameters).

| URI | Parameters | Returns | Notes |
|-----|------------|---------|-------|
| `profile://summary` | none | Markdown | |
| `profile://kanban` | none | Markdown | Placeholder line if file missing |
| `profile://context` | none | Plain text | Large; mode from `NBLANE_CONTEXT_MODE` |
| `profile://gap/{task}` | last path segment **`task`** | Plain text | **Percent-encode** the task (e.g. spaces → `%20`). Server applies `urllib.parse.unquote` before analysis |

**Profile selection (all resources):** `NBLANE_PROFILE` / `NBLANE_MCP_PROFILE` if set and valid; else the single profile under `profiles/` if exactly one; else error body `ERROR [profile://…]: …`.

**Example (gap):** task `OpenVLA robot control` → URI `profile://gap/OpenVLA%20robot%20control`.

## Prerequisites

- Install the repo in the Python environment you use for MCP, for example:

  ```bash
  cd /home/narwal/workspace/nblane
  pip install -e .
  ```

  Use your own clone path if different.

  This pulls in the `mcp` dependency and registers the `nblane` package.

- If you have **more than one** profile under `profiles/`, set **`NBLANE_PROFILE`** (see below).

## Using it in Cursor (what you do, what you get)

**What it is:** MCP exposes your nblane profile as **resources** (URIs) and
optional **tools** that write selected artifacts. Once Cursor connects, the
agent can **read** context on demand—similar to pasting `nblane context`—and
**invoke tools** only when you ask it to.

**Steps:**

1. Configure MCP (Option A or B below), then restart Cursor or reload MCP.
2. **Cursor → Settings → MCP** — confirm **nblane** is connected (no error state).
3. Use **MCP Inspector** (or equivalent) to list resources and **read** `profile://context` once as a smoke test.
4. In **Agent / Chat**, **name the resource** when it matters, e.g. “Read `profile://context` first, then refactor this file” or “Use `profile://summary` for skill focus before suggesting a plan.” Behavior varies by Cursor version; explicit instructions are the reliable approach.

**Typical uses:** `profile://context` for full prompt-style context; `profile://summary` for a quick tree + focus snapshot; `profile://kanban` for the board; `profile://gap/{task}` (URL-encoded) before a large task—same idea as `nblane gap`.

**Note:** **Tools** change files under `profiles/` (growth log, skill-tree
evidence, `interactions/*.jsonl`, method drafts). Prefer explicit agent
instructions before calling them. Heavy edits (ingest, full evidence CLI, team
pool) stay on **CLI** or **Streamlit**.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `NBLANE_PROFILE` or `NBLANE_MCP_PROFILE` | Default profile name. Required when several profiles exist. |
| `NBLANE_ROOT` | Override repository root (directory that contains `profiles/`). Optional if resolution from the installed package finds your clone. |
| `NBLANE_CONTEXT_MODE` | `chat` · `review` · `write` · `plan` — affects `profile://context` only. Default: `chat`. |
| `NBLANE_GAP_USE_LLM` | If `1` / `true`, enable LLM routing for gap analysis (needs API key). Default: off. |

## Option A — MCP only when this repo is the workspace

The repo ships **`.cursor/mcp.json`**. It uses:

- `command`: `${workspaceFolder}/.venv/bin/python`
- `cwd`: `${workspaceFolder}`

So **`${workspaceFolder}` must be the nblane repo root**. That works when you open the nblane project in Cursor.

Adjust `env` if needed, for example:

```json
"env": {
  "PYTHONPATH": "src",
  "NBLANE_PROFILE": "yourname"
}
```

(If you rely on `pip install -e .`, you can often omit `PYTHONPATH`.)

## Option B — Use nblane MCP from **any** project on the same machine

When the active window is **not** the nblane repository, `${workspaceFolder}` points at **another** directory. The bundled `.cursor/mcp.json` in nblane will **not** apply unless that other project has its own MCP config.

Do one of the following:

### 1. User-level MCP config (recommended)

Add the server in **Cursor → Settings → MCP** (or edit the user MCP JSON file Cursor uses on your OS — often under `~/.cursor/`). Register one server entry with **absolute paths** to your nblane checkout and interpreter.

Example for a clone at `/home/narwal/workspace/nblane` (change `NBLANE_PROFILE` to your profile):

```json
{
  "mcpServers": {
    "nblane": {
      "command": "/home/narwal/workspace/nblane/.venv/bin/python",
      "args": ["-m", "nblane.mcp_server"],
      "env": {
        "NBLANE_PROFILE": "yourname",
        "NBLANE_ROOT": "/home/narwal/workspace/nblane"
      }
    }
  }
}
```

Notes:

- **`command`**: full path to the Python binary that has `nblane` installed (`pip install -e .` in that env).
- **`NBLANE_ROOT`**: optional but **recommended** for clarity when the workspace is unrelated; it must be the directory that contains `profiles/` and `schemas/`.
- You usually **do not** need `PYTHONPATH` if you installed with `pip install -e .`.
- **`cwd`** is optional here; if omitted, Cursor may use the current workspace. The server still resolves data via `NBLANE_ROOT` / package location.

### 2. Per-project stub in another repo

In *each* other project where you want MCP, add `.cursor/mcp.json` with the same **absolute** `command` and `env` as above (still pointing at the nblane repo via `NBLANE_ROOT`). Duplicated config is harder to maintain; prefer user-level MCP if you use many workspaces.

### Avoid duplicate server names

If both the nblane workspace and the user config define a server named `nblane`, disable one or rename one entry (e.g. `nblane-global`).

## Verify

- In Cursor, open **MCP** / inspector and confirm resources list includes `profile://summary`, `profile://context`, etc.
- Read `profile://context` once; you should see your `SKILL.md`-based system prompt.

## See also

- Design: [design.md](design.md) (Demo 1 Phase 2–5 — MCP + Cursor)
- CLI parity: `nblane context`, `nblane gap`
- Streamlit UI: [web-ui.md](web-ui.md)
