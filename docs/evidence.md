# Skill evidence (provenance)

Structured proof attached to **skill-tree nodes** so gap analysis and the
agent system prompt can reflect how well each skill is backed by real work.

There are two complementary mechanisms:

1. **Inline `evidence`** — rows stored directly on a node (legacy-friendly).
2. **Evidence pool + `evidence_refs`** — one catalogued record in
   `evidence-pool.yaml`, referenced by stable **ids** from any number of
   nodes (one project, many skills).

Downstream code **materializes** both into a single list: refs first
(deduplicated by id), then inline rows.

## Files

| File | Role |
|------|------|
| `profiles/<name>/skill-tree.yaml` | Per-node `evidence` and/or `evidence_refs` |
| `profiles/<name>/evidence-pool.yaml` | Shared `evidence_entries` with unique `id` |

New profiles from `nblane init` include an empty `evidence-pool.yaml`
template.

## Inline shape (`skill-tree.yaml`)

Under each node in `nodes:` you may add an `evidence` list. Each item is a
mapping:

| Field | Required | Notes |
|-------|----------|--------|
| `type` | Yes | One of: `project`, `paper`, `course`, `practice` |
| `title` | Yes | Short label (non-empty) |
| `date` | No | Free string, e.g. `2026-02` |
| `url` | No | Link |
| `summary` | No | One-line or short description |

Example:

```yaml
nodes:
  - id: pose_estimation
    status: solid
    evidence:
      - type: project
        title: "Hand-eye calibration on Piper"
        date: "2026-02"
        summary: "Error under 2 mm"
```

## Pool + references

**Pool record** (`evidence-pool.yaml`):

```yaml
profile: "yourname"
updated: "2026-03-22"
evidence_entries:
  - id: piper_demo_2026
    type: project
    title: "Piper manipulation milestone"
    date: "2026-03"
    summary: "End-to-end pick on real arm"
    deprecated: false   # optional; soft-retire without breaking refs
    replaced_by: ""      # optional; another pool id
```

**Node references** (`skill-tree.yaml`):

```yaml
nodes:
  - id: manipulation
    status: solid
    evidence_refs:
      - piper_demo_2026
```

You may use **only** refs, **only** inline `evidence`, or **both** on the same
node. Duplicate ref ids in YAML are normalized to a single occurrence.

## CLI

**Inline append** (unchanged; creates the node as `learning` if missing):

```bash
nblane evidence <profile> <skill_id> add \
  --type project \
  --title "Bringup demo on real arm" \
  --date "2026-03" \
  --url "https://example.com" \
  --summary "Optional longer note"
```

**Create a pool record** (prints or reuses the id; same type + title + date
as an existing row **upserts** to that id):

```bash
nblane evidence <profile> pool add \
  --type project \
  --title "Shared project title" \
  --date "2026-03" \
  --id my_custom_id
```

**Link a pool id to a skill** (appends to `evidence_refs`):

```bash
nblane evidence <profile> link <skill_id> <evidence_id>
```

**Unlink** (remove that pool id from one node’s `evidence_refs` only):

```bash
nblane evidence <profile> unlink <skill_id> <evidence_id>
```

**Remove a pool row** — fails if any node still references the id unless you
pass `--prune-refs` (strips the id from every node’s `evidence_refs`, then
deletes the row). Writes YAML, validates, syncs generated SKILL.md blocks
(rollback on validate error).

```bash
nblane evidence <profile> pool remove <evidence_id>
nblane evidence <profile> pool remove <evidence_id> --prune-refs
```

**Soft-retire a pool row** (id stays valid for validate; materialized evidence
for context / gap **omits** deprecated rows):

```bash
nblane evidence <profile> pool deprecate <evidence_id>
nblane evidence <profile> pool deprecate <evidence_id> --replaced-by NEW_ID
```

## Web UI

On **Skill Tree**:

- Expand **Evidence pool** to add catalogued rows, list existing rows, and
  **Delete row** (optionally remove the id from all skills’ refs first via the
  checkbox). Click **Save** to persist.
- On each skill card, use **From pool (refs)** multiselect plus inline
  evidence rows as before.
- **Save skill-tree.yaml** writes both YAML files when a pool file already
  exists or the pool has entries.

## Downstream behavior

- **`nblane context <profile>`** — For `solid` / `expert` nodes, materialized
  evidence drives **Skill evidence (solid / expert)**.
- **`nblane gap`** — Counts use materialized totals, e.g. `solid (4 evidence)`.
  Optional: count `type: project` rows separately if you want that metric in
  custom tooling.
- **`nblane validate [profile]`** — Unknown inline `type` or empty inline
  `title` → **warning**. Unknown `evidence_refs` id (or refs with no
  `evidence-pool.yaml`) → **error**. Pool rows marked `deprecated: true` still
  satisfy refs but do not appear in materialized evidence lists.

## Migration notes

- Existing trees with **only** inline `evidence` behave as before.
- To deduplicate repeated inline rows across nodes: add each distinct item
  to `evidence-pool.yaml`, replace copies with `evidence_refs`, and run
  `nblane validate`.

See also: [Design manual §5](design.md#5-demo-1-phase-1-skill-provenance-evidence).
