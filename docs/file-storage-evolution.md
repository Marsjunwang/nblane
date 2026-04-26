# File Storage Evolution

This document evaluates whether nblane's current file-first storage model can support a public personal website, resume generation, blogging, media, portfolio outputs, and future multi-user usage. It is a product and architecture decision note, not a statement that the public surface is already implemented.

Chinese full version: [zh/file-storage-evolution.md](zh/file-storage-evolution.md).

| Field | Value |
|-------|-------|
| Version | `v0.1.0` |
| Status | Proposed |
| Scope | `profiles/`, `teams/`, public personal sites, file-to-database evolution |

---

## 1. Summary

nblane should keep its current **plain-text-first** storage model for the next stage. Files are transparent, diffable, agent-readable, easy to back up with Git, and appropriate for a private operating system plus small-team workflows.

However, the current private files should not be exposed directly as a public website. The next stage needs a **public data layer** under each profile. Public pages should read only explicit public files, while `SKILL.md`, `skill-tree.yaml`, `kanban.md`, and agent calibration files remain private workspace data.

Recommended path:

1. Keep YAML/Markdown files as the source of truth for v0/v1.
2. Add profile-scoped public files for website content.
3. Keep small-team multi-user support through profile directory isolation and existing auth.
4. Move media to object storage when file size or upload volume grows.
5. Move to database-backed storage only for SaaS-scale multi-tenancy.

---

## 2. Current File Model

Profile data currently lives under:

```text
profiles/<name>/
  SKILL.md
  agent-profile.yaml
  skill-tree.yaml
  evidence-pool.yaml
  kanban.md
  kanban-archive.md
```

Related shared data:

```text
schemas/*.yaml
teams/<team>/team.yaml
teams/<team>/product-pool.yaml
auth/users.yaml
```

`NBLANE_ROOT` can point production services at a separate data repository such as `/srv/nblane-data`. Git backup can commit and push writes. Streamlit editors use file snapshots for lightweight concurrent edit detection.

| File | Current role | Directly public? |
|------|--------------|------------------|
| `SKILL.md` | Agent/persona prompt, identity narrative, generated blocks | No |
| `skill-tree.yaml` | Skill status and evidence refs | No |
| `evidence-pool.yaml` | Evidence fact library | Partially, only through a public whitelist |
| `kanban.md` | Current work plan | No |
| `kanban-archive.md` | Internal Done archive | No |
| `agent-profile.yaml` | Agent-side structured prior | No |
| `teams/*` | Team pools and rules | Partially, with a team public layer |
| `auth/users.yaml` | Users, roles, profile/team permissions | No |

---

## 3. Personal Website Coverage

| Capability | Current model | With file extension | Database trigger |
|------------|---------------|---------------------|------------------|
| Name, bio, contacts | Partly in `SKILL.md` | `public-profile.yaml` | Multi-site templates, localization |
| Avatar / photos | Missing | `media/avatar.*` | Cropping, CDN, heavy media |
| Online resume preview | Missing | `resume-source.yaml` + generated HTML | Collaborative editing, many versions |
| Resume download | Missing | Markdown / HTML first; PDF later | Batch generation, job queue |
| Job-targeted resume | Missing | Generate from structured facts only | Many users, audit, async jobs |
| Blog writing | v1 supported | `blog/*.md` + front matter | Search, comments, collaboration |
| Blog images | v1 supported | `media/blog/<slug>/` | CDN, image processing |
| Blog video | Partial | Prefer external URLs; small local `mp4` / `webm` allowed | Upload/transcode/analytics |
| Project links | Partly in evidence | `projects.yaml` referencing evidence | Complex filters/search |
| Papers / patents | Partly in evidence | `outputs.yaml`, type expansion | External sync, metrics |
| Work-plan integration | Done -> evidence exists | Publish pipeline | Multi-user publication workflow |
| Small-team multi-user | Partly available | Profile directory isolation | High concurrency, multiple app replicas |

---

## 4. Recommended Public Layer

Add explicit public files under each profile:

```text
profiles/<name>/
  public-profile.yaml
  resume-source.yaml
  projects.yaml
  outputs.yaml
  blog/
    2026-04-26-vla-memory.md
  media/
    avatar.jpg
    blog/2026-04-26-vla-memory/cover.jpg
  resumes/
    generated/
      2026-04-26-vla-engineer.md
      2026-04-26-vla-engineer.html
```

Public site generation should read only:

```text
public-profile.yaml
resume-source.yaml
projects.yaml
outputs.yaml
blog/*.md where status=published
media/
resumes/generated/
```

It should not directly render private workspace files:

```text
SKILL.md
skill-tree.yaml
kanban.md
kanban-archive.md
agent-profile.yaml
auth/users.yaml
```

Every public object should default to private or draft. Publish only explicit `status: published` or `visibility: public` content.

Kanban should feed the public surface through a conversion pipeline:

```text
Kanban Done
  -> evidence
  -> blog draft
  -> resume bullet
  -> project update
  -> public website
```

Do not expose Doing / Queue tasks directly. If current work is useful publicly, write a curated public summary.

---

## 5. Multi-User Boundary

### Small Team

The current model can support a small team:

```text
1-20 users
one profile per person
few teams
low concurrent editing
internal Streamlit workspace
Git backup for audit and rollback
```

Keep these constraints:

- Users can only read/write authorized profiles.
- Upload paths must stay under the user's own `profiles/<name>/media/`.
- File snapshot checks remain in place.
- Git commit actor records the current user.
- Public sites read only profile-scoped public data.

### Medium Scale

Start splitting storage when:

- Media uploads become frequent.
- Git repository size grows quickly.
- Git push latency affects save flows.
- Public site builds need caching or faster deploys.

At that point, keep YAML/Markdown for source data but move large media to object storage.

### SaaS Multi-Tenant

For public registration, billing, many hosted sites, high concurrency, or multi-instance deployment, move to:

```text
profile documents -> Postgres or SQLite
media -> object storage
generation jobs -> task queue
Git -> export / backup / audit snapshots
```

The filesystem becomes an export format rather than the primary database.

---

## 6. Evolution Path

| Stage | Storage strategy | Goal |
|-------|------------------|------|
| v0 | Current `profiles/` file model | Private OS, Agent OS, small-team workspace |
| v1 | Add public layer files | Personal website MVP, public resume, blog, projects, outputs |
| v2 | Add `public-site.yaml` manifest | Navigation, featured content, theme, domain, published resume |
| v3 | Move media out | Avoid Git large files and upload bottlenecks |
| v4 | Database-backed storage | SaaS multi-tenancy, search, audit, queues |

---

## 7. Decision Table

| Decision | Recommendation |
|----------|----------------|
| Add a database immediately | No |
| Continue file-first storage | Yes |
| Publish `SKILL.md` directly | No |
| Publish `kanban.md` directly | No |
| Treat `evidence-pool.yaml` as public CMS | No; use it as a fact source |
| Store videos in Git | No by default |
| Support small-team multi-user with current model | Yes |
| Use pure files for SaaS multi-tenancy | No |

---

## 8. Next Implementation Steps

1. Define minimal schemas for `public-profile.yaml`, `resume-source.yaml`, `projects.yaml`, `outputs.yaml`, and blog front matter.
2. Build a static public site generator that reads only the public layer.
3. Put the public site on `www.nblane.cloud` and keep the private Streamlit workspace on `app.nblane.cloud` or a protected path.
4. Add Streamlit editors for public profile, blog, and resume source.
5. Add a Kanban Done -> evidence / blog draft / resume bullet / project update publishing pipeline.
6. Revisit object storage and database-backed storage when media or user scale requires it.

---

## 9. Related Docs

- [Profile documents relationship](profile-documents-relationship.md)
- [Product design](product.md)
- [Architecture](architecture.md)
- [Web experience design](web-ui-product.md)
- [Skill evidence](evidence.md)
