# Architecture & Design Principles

## Relationship to product vision (v0.2)

The full product definition—Human OS vs Agent OS, co-evolution engine, agent
roles (Skill Mirror, Task Reasoner, etc.), MVP tiers, and minimum demos—is in
[product.md](product.md). **Phased implementation and milestones** are in
[design.md](design.md). **This file describes what the repository implements
today** and the engineering rules behind it.

**Rough mapping:**

- **Current code:** Profile data layer + rules layer + thin CLI (**13 commands**)
  + full Web UI; all groundwork before Demo 1 is done (M0–M3), plus **Demo 1
  Phase 1 — Skill Provenance**: inline `evidence`, profile-level
  **`evidence-pool.yaml`**, node **`evidence_refs`**, materialization in
  `evidence_resolve.py`, and CLI / Web editing. Rules-based `gap` and `context`
  use **resolved** evidence counts and summaries. See [design.md §5](design.md)
  and [evidence.md](evidence.md). **Profile ingest** (resume + kanban Done →
  LLM JSON patch → merge pool → tree → `validate` + `sync`) is shipped as an
  application layer on top of the same files; see [design.md §5.4](design.md)
  and [profile-documents-relationship.md](profile-documents-relationship.md).
- **Demo 1 (initial delivery):** MCP **read resources** + **write tools** on
  stdio (`mcp_server.py`, `nblane-mcp`); **`crystallize`** and **`sync-cursor`**
  CLIs; deeper LLM crystallization and human-confirm flows remain incremental.
  See [design.md §6–9](design.md) and [mcp.md](mcp.md).
- **Still roadmap:** Full productization of `sync_team_pool` /
  `route_to_best_owner`, public export, and hosted services.

If a capability appears only in [product.md](product.md) and not here, treat it
as **intent** until code lands.

## Current implementation snapshot (Demo 1 baseline)

| Capability | Status | Location |
|------------|--------|----------|
| Profile layout (SKILL.md / skill-tree / **evidence-pool** / kanban / agent-profile) | Shipped | `profiles/`, `core/models.py`, `core/io.py` |
| Domain schema graph | Shipped | `schemas/*.yaml`, `core/models.py` |
| `init` / `context` / `status` / `log` / `sync` / **`evidence`** / **`ingest-resume`** / **`ingest-kanban`** / **`health`** / **`sync-cursor`** / **`crystallize`** | Shipped | `cli.py`, `commands/`, `core/context.py`, `core/status.py`, `core/sync.py`, `core/profile_ingest.py`, `core/profile_ingest_llm.py`, `core/profile_health.py`, `core/cursor_rule.py`, `core/crystallize.py` |
| `validate` (skill-tree + evidence + **evidence_refs → pool**) | Shipped | `core/validate.py` |
| `gap` (rules task gaps; **materialized evidence counts**) | Shipped | `core/gap.py`, `core/evidence_resolve.py` |
| `team` (pool summary) | Shipped | `core/team.py` |
| `agent-profile.yaml` merged into `context` | Shipped | `core/context.py` |
| **Skill Provenance** — `Evidence` / `EvidenceRecord` / `EvidencePool`, inline + pool + refs | Shipped | `core/models.py`, `core/evidence_resolve.py`, `core/evidence_pool_id.py`, `core/io.py` |
| `teams/` shared pool (team.yaml + product-pool.yaml) | Shipped | `teams/`, `core/io.py`, `core/team.py` |
| Web UI (Skill Tree / Gap / Kanban / Team View / Profile Health / SKILL.md) | Shipped | `app.py`, `pages/` (5 pages); Skill Tree includes **pool + multiselect refs**; Home **resume ingest**; Kanban **Done → evidence ingest**; Profile Health is read-only |
| Web UI i18n (en / zh, single switch) | Shipped | `core/llm.py` (`LLM_REPLY_LANG`), `web_i18n.py` |
| Gap analysis (rules + optional LLM router + learned keywords) | Shipped | `core/gap.py`, `core/gap_llm_router.py`, `core/learned_keywords.py`, `pages/2_Gap_Analysis.py` |
| LLM coach + follow-up chat (optional) | Shipped | `core/llm.py`, `pages/2_Gap_Analysis.py` |
| Profile ingest (merge + validate + sync; resume / kanban prompts) | Shipped | `core/profile_ingest.py`, `core/ingest_*.py`, `core/profile_ingest_llm.py`, `core/jsonutil.py` |
| Profile Health / Growth Review (validate + sync + evidence + kanban checks) | Shipped | `core/profile_health.py`, `commands/health.py`, `pages/5_Profile_Health.py` |
| MCP Server (Read + Write) | **Initial version shipped** | `mcp_server.py` (stdio); `nblane-mcp` entry point |
| Interaction logs + crystallization | **Initial version shipped** | `core/interaction.py`, `core/crystallize.py`; MCP tools + `crystallize` CLI |
| Cursor Skill integration | **Initial version shipped** | `nblane sync-cursor` → `.cursor/rules/nblane-context.mdc` |
| Public export, hosted service | **Not shipped** | Roadmap M5+ |

## Core idea

nblane rests on one claim: **a person’s knowledge, taste, and growth path can be
represented as structured text that both humans and AI can read**.

That text is `SKILL.md`—your system prompt.

## Layers

```
profiles/{name}/
├── SKILL.md             <- Prior (read by agents)
├── skill-tree.yaml      <- Structured progress (status, notes, evidence, evidence_refs)
├── evidence-pool.yaml   <- Shared evidence catalog (ids referenced from skill-tree)
├── kanban.md            <- Current work
├── agent-profile.yaml   <- Agent’s structured model of the user
├── papers/              <- Research notes
├── projects/            <- Project records
└── log.md               <- Optional overflow log
```

`schemas/` holds domain skill-tree definitions—the **full map** of nodes that
can exist in the domain. Each person’s `skill-tree.yaml` is a personal overlay
on that map.

`src/nblane/` is a small, clear Python package; **data** is the product, not the
software.

## Module inventory

```
src/nblane/
├── __init__.py         # Version
├── cli.py              # CLI entry (13 subcommands)
├── mcp_server.py       # MCP stdio: resources + write tools
├── web_shared.py       # Streamlit shared helpers (profile picker, LLM gate, emoji toggle)
├── web_i18n.py         # UI strings (en/zh) keyed by LLM_REPLY_LANG
└── core/
    ├── models.py       # SkillNode / SkillTree / Evidence / EvidencePool / Schema / GapResult
    ├── io.py           # Compatibility facade for file I/O
    ├── profile_io.py   # Profiles, SKILL.md, skill-tree, evidence-pool
    ├── schema_io.py    # Schema loading and raw schema helpers
    ├── kanban_io.py    # Kanban parse/render/save/archive
    ├── team_io.py      # team.yaml and product-pool.yaml
    ├── paths.py        # Repo path constants
    ├── growth_log.py   # Append Growth Log rows in SKILL.md (shared with CLI / MCP)
    ├── skill_evidence_inline.py  # Append inline evidence (shared with CLI / MCP)
    ├── interaction.py  # Append JSONL under profiles/.../interactions/
    ├── crystallize.py  # Method draft files under profiles/.../methods/
    ├── cursor_rule.py  # Generate .cursor/rules/nblane-context.mdc
    ├── evidence_resolve.py  # Merge pool refs + inline evidence for gap/context
    ├── evidence_pool_id.py  # Auto ids + fingerprint helpers (CLI)
    ├── gap.py          # Task–skill match + prerequisite closure + gaps
    ├── gap_llm_router.py  # LLM: task → schema node ids (+ keywords JSON)
    ├── jsonutil.py       # Extract JSON object from LLM text (shared)
    ├── learned_keywords.py # Per-schema learned keywords (schemas/.learned/)
    ├── context.py      # System prompt generation
    ├── validate.py     # Skill-tree + evidence + evidence_refs validation
    ├── sync.py         # SKILL.md generated-block sync
    ├── status.py       # Skill-tree summary stats
    ├── team.py         # Team aggregation
    ├── profile_ingest.py   # Compatibility facade for ingest APIs
    ├── ingest_models.py    # Ingest dataclasses
    ├── ingest_parse.py     # Parse/filter ingest patches
    ├── ingest_merge.py     # Merge ingest patches into pool + tree
    ├── ingest_preview.py   # Preview deltas and prompt summaries
    ├── ingest_apply.py     # Validate + sync + rollback
    ├── profile_health.py   # Read-only growth review checks
    ├── profile_ingest_llm.py  # Resume + kanban Done → structured JSON (en/zh)
    └── llm.py          # OpenAI-compatible LLM client + reply language
```

```
pages/
├── 1_Skill_Tree.py     # Skill tree + inline evidence + evidence pool + ref multiselect
├── 2_Gap_Analysis.py   # Rules + optional LLM router + AI coach + write-back
├── 3_Kanban.py         # Kanban editing + Done → evidence ingest expander
├── 4_Team_View.py      # Team + product pool editing
└── 5_Profile_Health.py # Read-only health / growth review
```

## Web UI language (en / zh)

All Streamlit copy is centralized in **`web_i18n.py`**. The active locale is
**not** a separate Streamlit widget: it follows **`LLM_REPLY_LANG`** in
`.env` (`en` default, or `zh`), exposed as `llm.reply_language()` and read
by `home_ui()`, `gap_ui()`, `skill_tree_ui()`, `kanban_ui()`, `team_ui()`, and
`common_ui()`. Gap Analysis and the **LLM router** use **language-matched
system prompts** (English vs Chinese) so the UI and model behavior stay
aligned.

**Layout:** Every page calls **`select_profile()`** before the main **`st.title`**
so the active profile is clear first. **Team View** adds a caption that team
data lives under **`teams/`** and is not filtered by the sidebar profile.
Optional **`NBLANE_UI_EMOJI=0`** (or `false` / `no` / `off`) removes emoji
prefixes from metrics and status rows. For IA and journeys see
[web-ui-product.md](web-ui-product.md) and the operator guide
[web-ui.md](web-ui.md).

## Evidence materialization (current)

For each skill-tree node, **inline `evidence`** and **`evidence_refs`** (into
`profiles/<name>/evidence-pool.yaml`) are merged by `evidence_resolve.py`:
refs first (deduped by id), then inline rows. **`nblane gap`** and
**`nblane context`** consume this resolved list for counts and prompt text.
**`nblane validate`** errors on unknown ref ids when the pool file is present.

## Profile ingest pipeline (current)

Optional **LLM** turns **resume text** (`ingest-resume`, Home expander) or
**kanban Done tasks** (`ingest-kanban`, Kanban expander) into a single JSON
patch (`evidence_entries` + `node_updates`). **`profile_ingest.merge_ingest_patch`**
applies **pool first, then tree**; **`run_ingest_patch`** writes YAML, runs
**`validate_one`**, then **`write_generated_blocks`** on `SKILL.md`, restoring
files if validation or sync fails. **Status** fields from the model are applied
only when **`--allow-status-change`** or the Web checkbox is set. **`--dry-run`**
merges in memory and prints YAML only. See [design.md §5.4](design.md).

## Gap analysis pipeline (current)

1. **Roots:** Optional **rule overlap** (`tokenize` + synonym expansion,
   including Chinese runs) and/or **LLM routing** (`gap_llm_router.route_task_to_nodes`
   → JSON `node_ids` + `keywords`, validated against the schema index). Roots
   can also be set **manually** (single schema node). Rule scoring can use
   **learned keywords** loaded per schema.
2. **Closure:** Prerequisite closure (`requires_closure`) in deterministic
   topological order, then status-aware **gap** detection vs the profile’s
   skill tree.
3. **Persistence:** Router and coach outputs can merge **bilingual keyword
   phrases** into `schemas/.learned/<schema>.yaml` via `learned_keywords`
   (caps per node), improving later rule-based matches without extra API calls.
4. **UI:** `pages/2_Gap_Analysis.py` exposes toggles, metrics, closure list,
   optional **AI coach** (first reply + **follow-up** via `chat_messages`),
   and a **write-back** panel to update `skill-tree.yaml`.

## Design rules (avoid over-engineering early)

1. **Plain text first.** SKILL.md is Markdown; skill-tree.yaml is YAML; no
   custom formats.
2. **Git is the database.** Each update is a commit; diff is growth history.
3. **Agent integration is one command.** `nblane context <name>` prints the
   system prompt. Done.
4. **Schemas are optional.** SKILL.md alone, without skill-tree.yaml, still
   works.
5. **No forced SKILL.md structure.** Sections are convention, not validation;
   write what is true.
6. **Module cohesion.** One file, one job under `core/`; add new files for new
   capabilities instead of bloating existing modules.

## Co-evolution model

```
You update SKILL.md
        |
nblane context -> system prompt
        |
Agent calibrates to new prior
        |
Agent helps at your current level
        |
You grow; SKILL.md lags; you update again
        |
        (loop for years)
```

The diff between today’s SKILL.md and last year’s is a machine-readable growth
record—that is the artifact.

## Multi-person design

Each profile is independent; there is no shared database. The README “crew”
table is hand-maintained for now—a future dashboard might generate it from
profiles.

Team-level artifacts live under `teams/<team_id>/` (`team.yaml` +
`product-pool.yaml`); visibility is still a team convention—no central service.
Summary command: `nblane team <team_id>`.

Social behavior emerges: skill trees visible in the repo surface parallels and
gaps. No gamification in phase zero.

The product vision later includes **agent-augmented** connection and IP flows;
this repo does **not** ship a full social product—only plain-text profiles and
an optional crew table.

## What this is NOT

- Not a hosted social network (future ideas in [product.md](product.md); scope
  stays local / Git-based files)
- Not a task manager
- Not a resume generator (though data can feed one)
- Not a course platform

It is a **structured personal knowledge base meant for agents to read**.
