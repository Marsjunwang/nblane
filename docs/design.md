# nblane · Design Manual & Milestones

This document explains **how to implement** the product vision. Unlike
[product.md](product.md) (why / what) and [architecture.md](architecture.md)
(current implementation boundary), it focuses on **iteration order, data
contracts, and acceptance criteria**.

| Item | Current value |
|------|---------------|
| Document version | `v0.2.0` |
| Status | Active |
| Last updated | `2026-03-23` |

---

## 1. Document roles

| Document | Role |
|----------|------|
| [product.md](product.md) | Product definition, users, Team OS, roadmap, repo vocabulary |
| [architecture.md](architecture.md) | What the repo **actually** implements today, engineering rules, module list |
| **design.md (this file)** | Phased milestones, file formats, CLI capabilities, how to accept |

---

## 2. Implementation principles

1. **Plain text first** — new capabilities land in Markdown / YAML first; no
   custom binary formats.
2. **Git as database** — collaboration and history rely on version control;
   validation and export are repeatable commands.
3. **Private by default** — team directories and shared pools remain
   visibility-by-convention inside the repo; public surface is explicit export.
4. **Progressive enhancement** — explainable rules first; stronger reasoning
   later; each step usable independently.
5. **Do not break the thin CLI** — existing commands stay backward compatible;
   new capabilities are additive.
6. **Module cohesion** — one file, one responsibility under `core/`; add new
   files for new capabilities.

---

## 3. Shipped baseline inventory (v0.2.0)

Everything below is implemented and usable as of this version — all groundwork
before Demo 1 in the product manual.

### 3.1 Data layer

| Component | Description | Location |
|-----------|-------------|----------|
| Profile layout | SKILL.md / skill-tree.yaml / evidence-pool.yaml / kanban.md / agent-profile.yaml | `profiles/` |
| Profile template | `init` scaffolds and replaces `{Name}` | `profiles/template/` |
| Domain schema | Node id / label / level / category / requires / keywords | `schemas/robotics-engineer.yaml` |
| Team shared pool | team.yaml + product-pool.yaml (problem / project / evidence / method / decision) | `teams/` |
| Data model | SkillNode / SkillTree / Evidence / EvidenceRecord / EvidencePool / Schema / … | `core/models.py` |
| Unified I/O | skill-tree + evidence-pool + teams, one module | `core/io.py` |

### 3.2 Rules layer

| Capability | Description | Location |
|------------|-------------|----------|
| Gap analysis | Token match + domain synonym expansion + BFS prerequisite closure + gap detection + next-step hints | `core/gap.py` |
| Context generation | SKILL.md + agent-profile.yaml + kanban.md → system prompt (four modes) | `core/context.py` |
| Skill-tree validation | Node ID / status / prerequisite consistency | `core/validate.py` |
| SKILL.md sync | Generated blocks + drift detection + auto rewrite | `core/sync.py` |
| Status summary | Counts by status + coverage | `core/status.py` |
| Team summary | Read team.yaml + product-pool → summary | `core/team.py` |

### 3.3 CLI (13 commands)

| Command | Status | Description |
|---------|--------|-------------|
| `init` | Shipped | Create profile |
| `context` | Shipped | System prompt (includes agent-profile + kanban) |
| `status` | Shipped | Skill tree summary |
| `log` | Shipped | Append Growth Log |
| `sync` | Shipped | Check / rewrite SKILL.md generated blocks |
| `validate` | Shipped | Validate skill-tree vs schema |
| `gap` | Shipped | Task → skill match and gaps |
| `team` | Shipped | Team pool summary |
| `evidence` | Shipped | Inline / pool / link skill evidence (see §5) |
| `ingest-resume` | Shipped | LLM: resume or long text → pool + tree patch (`--dry-run`, `--allow-status-change`) |
| `ingest-kanban` | Shipped | LLM: kanban **Done** column → pool + tree patch (same flags) |
| `sync-cursor` | Shipped | Write `.cursor/rules/nblane-context.mdc` from profile summary |
| `crystallize` | Shipped | Write `profiles/.../methods/*_draft.md` (`--file` / `--stdin`) |

### 3.4 Web UI (Streamlit)

| Page | Function | File |
|------|----------|------|
| Home | SKILL.md overview + structured edit + raw edit + **resume / long-text AI ingest** (draft → apply) | `app.py` |
| Skill Tree | Category tabs + level view + status + notes + inline evidence + evidence pool + refs + save/sync | `pages/1_Skill_Tree.py` |
| Gap Analysis | Task text + rules analysis + AI analysis + write-back panel | `pages/2_Gap_Analysis.py` |
| Kanban | Four-column board + task CRUD/move + **Done → evidence** AI ingest (multi-select, draft → apply) | `pages/3_Kanban.py` |
| Team View | Team metadata edit + product pool CRUD | `pages/4_Team_View.py` |

Sidebar order `pages/1_`–`4_` matches the recommended journey (Skill Tree → Gap
→ Kanban → Team). UX copy and layout rules:
[web-ui-product.md](web-ui-product.md); operator steps: [web-ui.md](web-ui.md).

### 3.5 AI layer

| Capability | Description | File |
|------------|-------------|------|
| LLM client | OpenAI-compatible, env config, optional | `core/llm.py` |
| AI gap analysis | Rules output + skill summary → LLM learning suggestions | `pages/2_Gap_Analysis.py` |
| Profile ingest | LLM → JSON patch; **merge pool → tree**; `validate` + `sync` (rollback on failure); en/zh prompts (`LLM_REPLY_LANG`) | `core/profile_ingest.py`, `core/profile_ingest_llm.py`, `core/jsonutil.py` |

---

## 4. Current state: Demo 1 · where we are

The project **has finished all groundwork before Demo 1** and **Demo 1 Phase 1
(Skill Provenance)** — evidence inline, shared pool, and node refs are shipped.

```
[Done] M0 Stable foundation · validate, schema checks
[Done] M1 Personal task loop · gap rules + CLI + Web UI
[Done] M2 Agent profile · agent-profile.yaml + context merge
[Done] M3 Team shared pool · teams/ + team command + Web UI
[Done] Demo 1 Phase 1: Skill Provenance (evidence + evidence-pool + evidence_refs)
[Done] App-layer: Profile ingest (resume + kanban Done → YAML, same validate/sync path)
                 |
                 v   <-- you are here
[Initial delivery] Demo 1 Phase 2: MCP Server — Read Path (resources + stdio)
[Initial delivery] Demo 1 Phase 3: MCP Server — Write Path (tools: log, growth, …)
[Initial delivery] Demo 1 Phase 4: Method crystallization (draft files + MCP tool; LLM TBD)
[Initial delivery] Demo 1 Phase 5: Cursor Skill integration (`sync-cursor` → rule file)
```

Phase dependencies:

```
Phase 1 (Skill Provenance)
  -> Phase 2 (MCP Read) -> Phase 3 (MCP Write) -> Phase 4 (Crystallize)
  -> Phase 5 (Cursor Skill)  (also depends on Phase 1 + 2)
```

---

## 5. Demo 1 Phase 1: Skill Provenance (evidence)

**Goal:** Skill-tree nodes carry structured evidence so gap analysis and context
generation can reflect evidence depth, with an optional **shared pool** so one
project is recorded once and linked from many skills.

### 5.1 Data contract

**Inline evidence** (`skill-tree.yaml` → `nodes[].evidence`) — same as before:

```yaml
# Example node extension in skill-tree.yaml
nodes:
  - id: pose_estimation
    status: solid
    note: "3D pose from depth + RGB"
    evidence:
      - type: project          # project | paper | course | practice
        title: "Piper hand-eye calibration"
        date: "2026-02"
        url: ""                 # optional
        summary: "Completed eye-in-hand calibration, error < 2mm"
      - type: paper
        title: "FoundationPose reproduction"
        date: "2026-01"
        summary: "Reproduced AP 92.3% on YCB"
```

**Evidence pool** (`profiles/<name>/evidence-pool.yaml`) — catalogued rows with
stable ids:

```yaml
profile: "alice"
updated: "2026-03-22"
evidence_entries:
  - id: piper_vla_2026
    type: project
    title: "Piper + VLA integration"
    date: "2026-03"
    url: ""
    summary: "One stack, real-robot demos"
    deprecated: false      # optional
    replaced_by: ""        # optional successor id
```

**Node references** (`skill-tree.yaml` → `nodes[].evidence_refs`) — list of
pool ids (optional; coexists with inline `evidence`):

```yaml
nodes:
  - id: vlm_robot
    status: solid
    evidence_refs:
      - piper_vla_2026
```

**Core types** (`core/models.py`):

- `Evidence` — inline row fields.
- `EvidenceRecord` — pool row: `Evidence` fields plus required `id`, optional
  `deprecated` / `replaced_by`.
- `EvidencePool` — `evidence_entries: list[EvidenceRecord]`.
- `SkillNode` — `evidence: list[Evidence]`, `evidence_refs: list[str]` (defaults
  empty).

**Materialization** (`core/evidence_resolve.py`): `resolve_node_evidence_dict`
merges refs (resolved from the pool, **deduped by id**) then appends inline
`evidence` rows. Gap counts, context prompts, and validation consume this
resolved list or equivalent logic.

### 5.2 Task breakdown

| # | Task | Files | Acceptance |
|---|------|-------|------------|
| 1 | `Evidence` + `EvidenceRecord` + pool types; `SkillNode.evidence_refs` | `core/models.py` | Round-trip YAML; dedupe ref ids on load |
| 2 | `load_evidence_pool` / `save_evidence_pool`; template file | `core/io.py`, `profiles/template/` | Pool read/write |
| 3 | `resolve_*` wired into gap / context | `core/evidence_resolve.py`, `gap.py`, `context.py` | Counts and prompts use materialized evidence |
| 4 | `validate`: ref ids exist in pool; pool required if refs used | `core/validate.py` | Bad ref → error |
| 5 | CLI `pool add`, `link`; inline `add` preserved | `cli.py` | Updates YAML |
| 6 | Skill Tree: pool editor + per-skill multiselect | `pages/1_Skill_Tree.py` | Saves pool + tree |
| 7 | Docs | `docs/evidence.md`, this section | Describes pool + migration |

### 5.3 Acceptance criteria

- `nblane gap Alice "reproduce VLA"` shows materialized counts, e.g.
  `solid (4 evidence)` when refs + inline resolve to four rows.
- `nblane context Alice` includes resolved evidence for solid/expert nodes.
- Web UI: inline rows + pool multiselect; pool expander for new records.
- Legacy skill-tree **without** `evidence` or `evidence_refs` unchanged.
- **Migration:** optional — move duplicated inline rows into
  `evidence-pool.yaml`, replace with `evidence_refs`, run `nblane validate`.

### 5.4 Profile ingest (LLM-assisted)

**Goal:** Turn **resume / long text** or **kanban Done tasks** into structured
updates to `evidence-pool.yaml` and `skill-tree.yaml`, then refresh SKILL.md
generated blocks — without bypassing validation.

**Contract:** LLM returns JSON with `evidence_entries` (pool rows) and
`node_updates` (per-node `evidence_refs`, optional inline `evidence`, optional
`note`, optional `status`). **Merge order:** pool first, then tree; **SKILL.md**
only via existing `sync` (`write_generated_blocks`). **Default:** node
`status` from the model is **not** applied unless the user passes
`--allow-status-change` (CLI) or enables the checkbox (Web).

**Implementation:** `core/profile_ingest.py` (`merge_ingest_patch`, `run_ingest_patch`,
`apply_merged_profile`); prompts + `llm.chat` in `core/profile_ingest_llm.py`;
JSON extraction shared with gap routing via `core/jsonutil.py`. CLI:
`nblane ingest-resume`, `nblane ingest-kanban`. Web: Home (Overview) and Kanban
expanders. Narrative and invariants: [profile-documents-relationship.md](profile-documents-relationship.md).

**Acceptance:** `--dry-run` prints merged YAML without writing; successful apply
passes `nblane validate` and updates generated SKILL.md blocks when `SKILL.md`
exists.

---

## 6. Demo 1 Phase 2: MCP Server — Read Path

**Goal:** Cursor can pull nblane context via MCP.

**Prerequisite:** Phase 1 done (context includes evidence summaries).

### 6.1 Technology choices

- **SDK:** Official Python `mcp` SDK
- **Transport:** stdio (Cursor spawns `python -m nblane.mcp_server`)
- **Protocol:** MCP resources (read-only exposure)

### 6.2 Task breakdown

| # | Task | Files | Acceptance |
|---|------|-------|------------|
| 1 | MCP server skeleton (stdio + FastMCP) | New `src/nblane/mcp_server.py` | `python -m nblane.mcp_server` starts |
| 2 | Resource: `profile://summary` | `mcp_server.py` | Returns tree summary + focus + prefs |
| 3 | Resource: `profile://kanban` | `mcp_server.py` | Returns current board |
| 4 | Resource: `profile://gap/{task}` | `mcp_server.py` | Gap analysis for task |
| 5 | Resource: `profile://context` | `mcp_server.py` | Full system prompt |
| 6 | Cursor config | New `.cursor/mcp.json` | Cursor discovers server |
| 7 | Profile discovery (auto or config) | `mcp_server.py` | Default profile via env or file |

### 6.3 Acceptance criteria

- New Cursor session: agent knows user, skill state, current work without manual
  backstory.
- MCP resources visible in Cursor inspector.

---

## 7. Demo 1 Phase 3: MCP Server — Write Path

**Goal:** External tools can write back into nblane.

**Prerequisite:** Phase 2 done.

### 7.1 Task breakdown

| # | Task | Files | Acceptance |
|---|------|-------|------------|
| 1 | Tool: `log_skill_evidence` | `mcp_server.py` + `core/io.py` | Updates skill-tree evidence |
| 2 | Tool: `append_growth_log` | `mcp_server.py` | Updates SKILL.md Growth Log |
| 3 | Tool: `log_interaction` | `mcp_server.py` + new `core/interaction.py` | Files under `interactions/` |
| 4 | Tool: `suggest_skill_upgrade` (confirm first) | `mcp_server.py` | Suggestion only until human confirms |
| 5 | Interaction log directory | `core/io.py` + `core/interaction.py` | `profiles/{name}/interactions/` by date |
| 6 | Interaction model | `core/models.py` + `core/interaction.py` | question / answer / skill_ids / timestamp |

### 7.2 Acceptance criteria

- After solving a problem in Cursor, agent can call `log_skill_evidence`.
- Corresponding YAML evidence list updates.
- Interaction logs under `profiles/{name}/interactions/`.
- All writes are visible and reviewable.

---

## 8. Demo 1 Phase 4: Method crystallization

**Goal:** At project end, compress work into reusable methods.

**Prerequisite:** Phase 3 (interaction logs exist).

### 8.1 Task breakdown

| # | Task | Files | Acceptance |
|---|------|-------|------------|
| 1 | Tool: `crystallize_method` | `mcp_server.py` + new `core/crystallize.py` | Logs + manual log → LLM playbook |
| 2 | Playbook storage | `core/io.py` | `profiles/{name}/methods/` YAML/Markdown |
| 3 | Evidence write-back | `core/crystallize.py` | Q/A pairs → skill evidence |
| 4 | Human confirm | `mcp_server.py` | Draft `_draft.md` first, then promote |
| 5 | CLI `nblane crystallize <name> <project>` | `cli.py` | CLI can trigger |

### 8.2 Acceptance criteria

- After reproducing a VLA stack, `crystallize_method` yields a playbook such as
  “How to reproduce PI0.5 on Piper arm”.
- Playbook includes Q/A pairs (self vs agent labeled).
- Related skill evidence updates automatically.

---

## 9. Demo 1 Phase 5: Cursor Skill integration

**Goal:** nblane context loads automatically in Cursor.

**Prerequisite:** Phase 1 + Phase 2.

### 9.1 Task breakdown

| # | Task | Files | Acceptance |
|---|------|-------|------------|
| 1 | Cursor Rule template | `.cursor/rules/nblane-context.mdc` | Contains nblane context summary |
| 2 | `nblane sync-cursor <name>` | `cli.py` | Generate/refresh rule from profile |
| 3 | MCP + Rule together | Docs + config | Rule static, MCP dynamic |

### 9.2 Acceptance criteria

- Open Cursor: agent already has capability overview without manual steps.
- “Help me reproduce VLA” replies consider strengths and gaps.

---

## 10. Development plan (sprint level)

### Sprint 1: Phase 1 — Skill Provenance (est. 3–4 days) — **done**

| Day | Task | Output |
|-----|------|--------|
| D1 | Evidence model + io.py + unit tests | `core/models.py`, `core/io.py`, `tests/test_evidence.py` |
| D2 | gap.py + context.py + `evidence_resolve.py` | `core/gap.py`, `core/context.py`, `core/evidence_resolve.py` |
| D3 | CLI `evidence` (inline + pool + link) + validate | `cli.py`, `core/validate.py` |
| D4 | Web UI: pool + multiselect refs + inline rows | `pages/1_Skill_Tree.py` |

### Sprint 2: Phase 2 — MCP Read (est. 2–3 days)

| Day | Task | Output |
|-----|------|--------|
| D1 | MCP skeleton + profile://summary + profile://context | New `mcp_server.py` |
| D2 | Remaining resources + Cursor config + E2E | `mcp_server.py`, `.cursor/mcp.json` |

### Sprint 3: Phase 5 — Cursor Skill (est. 1–2 days)

| Day | Task | Output |
|-----|------|--------|
| D1 | `sync-cursor` + rule template | `cli.py`, `.cursor/rules/nblane-context.mdc` |
| D2 | MCP + Rule joint testing | Config docs |

Phase 5 is scheduled before Phase 3/4 because it only needs Phase 1 + 2 — faster
read-path closure in Cursor.

### Sprint 4: Phase 3 — MCP Write (est. 3–4 days)

| Day | Task | Output |
|-----|------|--------|
| D1 | `log_skill_evidence` + `append_growth_log` | `mcp_server.py` |
| D2 | Interaction model + storage + `log_interaction` | `core/interaction.py`, `core/models.py` |
| D3 | `suggest_skill_upgrade` + human confirm | `mcp_server.py` |
| D4 | E2E write-back from Cursor | Tests |

### Sprint 5: Phase 4 — Crystallization (est. 2–3 days)

| Day | Task | Output |
|-----|------|--------|
| D1 | `core/crystallize.py` + methods storage | `core/crystallize.py`, `core/io.py` |
| D2 | MCP tool + confirm + CLI | `mcp_server.py`, `cli.py` |
| D3 | Full Demo 1 E2E + doc updates | Tests, docs |

### Total: about 12–16 days for all five Demo 1 phases

---

## 11. Command reference (planned vs shipped)

| Command | Status | Sprint | Description |
|---------|--------|--------|-------------|
| `init` | Shipped | — | Create profile |
| `context` | Shipped | S1 update | System prompt; includes evidence summaries after S1 |
| `status` | Shipped | — | Skill tree summary |
| `log` | Shipped | — | Growth Log append |
| `sync` | Shipped | — | Check / rewrite SKILL.md blocks |
| `validate` | Shipped | S1 update | Skill-tree validation; evidence checks after S1 |
| `gap` | Shipped | S1 update | Task gaps; evidence in output after S1 |
| `team` | Shipped | — | Team pool summary |
| `evidence` | Shipped | S1 | Inline + `pool add` + `link` (see §5) |
| `sync-cursor` | **Shipped** | S3 | Refresh Cursor rule |
| `crystallize` | **Shipped** | S5 | Write methods draft |

---

## 12. Implementation vs product (quick map)

| Product concept | Implementation | Status |
|-----------------|----------------|--------|
| `can_solve` / `detect_gap` | `core/gap.py`, `nblane gap` | Shipped |
| Data validation | `core/validate.py`, `nblane validate` | Shipped |
| Agent profile | `profiles/*/agent-profile.yaml`, `context` merge | Shipped |
| Team OS / shared pool | `teams/{id}/team.yaml`, `product-pool.yaml` | Shipped |
| Web UI | `app.py` + `pages/` | Shipped |
| LLM-enhanced gap | `core/llm.py` + Gap Analysis page | Shipped |
| Skill Provenance (evidence + pool + refs) | `core/models.py`, `evidence_resolve.py`, `io.py`, `cli.py`, Skill Tree | Shipped |
| MCP Server (Read) | `mcp_server.py` | **Initial delivery** |
| Cursor Skill integration | `.cursor/rules/` + `sync-cursor` | **Initial delivery** |
| MCP Server (Write) | `mcp_server.py` + `core/interaction.py` | **Initial delivery** |
| Method crystallization | `core/crystallize.py` | **Initial delivery** (draft files; LLM later) |
| `sync_team_pool` / `route_to_best_owner` | Not implemented | Roadmap |
| Public page export | Not implemented | Roadmap |

---

## 13. Technical constraints (Demo 1 overall)

- **Transport:** stdio (local subprocess, no network)
- **MCP SDK:** Official Python `mcp`
- **LLM:** Required only for Phase 4 crystallization; other phases are rules-first
- **Storage:** Files only (YAML + Markdown + JSON), no database
- **Security:** All writes visible; skill upgrades need human confirmation
- **Compatibility:** Phase 1 `evidence` defaults to empty list; existing YAML
  unchanged

---

## 14. Version history

| Doc version | Notes |
|-------------|-------|
| `v0.1.0` | First design manual; M0–M3 shipped and M4–M5 roadmap |
| `v0.2.0` | Rewrite: baseline inventory; Demo 1 five phases; sprint-level plan |
