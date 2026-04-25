# Web UI user guide (Streamlit)

This guide explains how to **run and use** the local Streamlit app. Product
information architecture, first-screen rules, and backlog live in
[web-ui-product.md](web-ui-product.md). Page inventory and file mapping:
[design.md §3.4](design.md).

| Item | Value |
|------|--------|
| Entry | `streamlit run app.py` (repo root) |
| Scope | `app.py` + `pages/*.py` — file-backed; **not** a hosted public app |

---

## 1. Prerequisites

1. Install the package: `pip install -e .` (see [setup.md](setup.md)).
2. At least one profile under `profiles/` (`nblane init <name>`).
3. Optional: **LLM** — set `LLM_API_KEY` (and related vars) in `.env` for
   AI gap coach, resume ingest, and kanban Done → evidence. Without it,
   rule-based gap analysis and all non-AI editing still work.

---

## 2. Language and display options

- **`LLM_REPLY_LANG`** in `.env`: `en` (default) or `zh`. Controls **all**
  Streamlit strings from `web_i18n.py` and the **language of LLM system
  prompts** used on Gap Analysis and ingest paths so UI and model stay
  aligned.
- **`NBLANE_UI_EMOJI`**: set to `0`, `false`, `no`, or `off` to drop emoji
  prefixes on home metrics, skill status rows, kanban column headers, and
  team pool tabs (see [architecture.md](architecture.md) Web UI section).
- **`NBLANE_ROOT`**: if the app resolves the wrong repo, point it at the
  directory that contains `profiles/`.

---

## 3. Sidebar: active profile

- **Current profile** — choose which `profiles/<name>/` tree the app loads.
- **New profile** — expander runs the same scaffold as `nblane init`.
- The selection persists while you navigate pages (session + internal key).

On **Team View**, data is always read/written under **`teams/`**. A caption
explains that the sidebar profile applies to Home, Skill Tree, Gap, and
Kanban — not to filtering team files.

---

## 4. Recommended journey

First-time flow (about one minute to orientation):

1. Pick a profile in the sidebar.
2. Open **Skill Tree** — see status, notes, evidence, pool, refs; **Save**
   writes `skill-tree.yaml`, `evidence-pool.yaml`, and syncs SKILL.md blocks.
3. Before a large task, use **Gap Analysis** — enter a task, run analysis,
   optionally enable AI coach if configured.
4. Use **Kanban** for day-to-day work; promote **Done** items to evidence via
   the expander when ready.
5. Use **Team View** when editing shared `team.yaml` / `product-pool.yaml`.
6. Open **Profile Health** before exporting context or after a work session.

See [web-ui-product.md §4](web-ui-product.md) for the product map.

---

## 5. Page reference

### 5.1 Home (`app.py`)

- **Title and captions** — browser tab uses the same naming pattern as other
  pages (`Home · nblane`). Lines under the title summarize the active profile
  and the **Private OS** role of this page.
- **Tabs**
  - **Overview** — skill metrics, per-category progress, optional **Resume /
    long text** ingest (expander). At the bottom: compact **sidebar hint**
    (`st.info`) and a **detailed page map** in a collapsed expander.
  - **Structured editor** — section-based edit of SKILL.md (generated blocks
    are marked auto-generated; saving overwrites only where allowed).
  - **Raw** — full SKILL.md source.
- **Resume ingest** — generate a draft → review merged YAML → **Apply** runs
  the same pipeline as `nblane ingest-resume` (validate + sync, rollback on
  failure). Optional checkbox to allow LLM-driven **status** changes (same
  semantics as CLI `--allow-status-change`).

### 5.2 Skill Tree (`pages/1_Skill_Tree.py`)

- **Save** is on the **title row** (primary pattern for this page).
- Category tabs, levels, per-node status / note / inline evidence.
- **Evidence pool** expander — shared catalog; nodes can **reference** pool
  ids. One **Save** persists tree + pool and syncs SKILL.md when possible.
- Docstring notes the intentional difference from Kanban’s toolbar Save.

### 5.3 Gap Analysis (`pages/2_Gap_Analysis.py`)

- Task description → **Analyze** (rules; optional LLM router and manual node).
- Results: matches, dependency closure, suggested next steps.
- **AI analysis** column — if LLM is configured, coach + follow-up chat; if
  not, a standard warning + `.env` hint (same component as other pages).
- **Write-back** — select gap nodes and new statuses to patch
  `skill-tree.yaml`.

### 5.4 Kanban (`pages/3_Kanban.py`)

- **Reload** / **Save** toolbar — loads or persists `kanban.md`.
- Four columns: Doing, Queue, Done, Someday / Maybe (display labels follow
  `LLM_REPLY_LANG`).
- **Done → evidence** expander — multi-select Done tasks, optional allow-status,
  same merge path as `nblane ingest-kanban`.

### 5.5 Team View (`pages/4_Team_View.py`)

- Select **team id** (directory under `teams/`).
- Edit team fields and **product pool** tabs; saves `team.yaml` and
  `product-pool.yaml`.

### 5.6 Profile Health (`pages/5_Profile_Health.py`)

- Read-only report built from `nblane health <name>`.
- Checks validation, generated block drift, solid/expert nodes without
  evidence, and Done tasks not yet crystallized.
- Does not write profile files.

---

## 6. CLI equivalence (quick map)

| Web action | CLI / command |
|------------|-----------------|
| Resume / long text ingest | `nblane ingest-resume <name> …` |
| Done → evidence | `nblane ingest-kanban <name> …` |
| Context text | `nblane context <name>` |
| Gap output | `nblane gap <name> "…"` |
| Validate after edits | `nblane validate <name>` |
| Profile health / growth review | `nblane health <name>` |
| SKILL.md generated blocks | `nblane sync <name> --write` |
| Evidence pool / inline | `nblane evidence <name> …` |

Details: [profile-documents-relationship.md](profile-documents-relationship.md),
[evidence.md](evidence.md).

---

## 7. Related docs

- [Web experience design (Streamlit)](web-ui-product.md) — IA, brand, backlog
- [Design manual §3.4](design.md) — shipped page list
- [Architecture — Web UI language](architecture.md)
- [MCP server](mcp.md) — Cursor integration (not the Streamlit UI)

**中文版：** [zh/web-ui.md](zh/web-ui.md)
