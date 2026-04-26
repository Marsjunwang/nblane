# Public Site, Blog, and Resume

This guide describes the implemented public layer for personal websites,
blogs, and resumes. The public site is generated from profile-scoped
YAML/Markdown files and never renders private profile files directly.

Chinese version: [zh/public-site.md](zh/public-site.md).

## Data Layer

Run this once for an existing profile:

```bash
nblane public init <profile>
```

New profiles already include the same files through `profiles/template/`:

```text
profiles/<name>/
  public-profile.yaml
  resume-source.yaml
  projects.yaml
  outputs.yaml
  blog/
  media/
  resumes/generated/
```

Public files are private or draft by default. Publishing is explicit:

- `public-profile.yaml`: set `visibility: public` before a normal public
  build.
- `resume-source.yaml`: set `visibility: public` to include the online
  resume in the site.
- `blog/*.md`, `projects.yaml`, `outputs.yaml`: set `status: published` to
  include objects in the normal build.
- Use `--include-drafts` only for local preview builds.

The generator does not render these private files:

```text
SKILL.md
skill-tree.yaml
kanban.md
kanban-archive.md
agent-profile.yaml
auth/users.yaml
```

Evidence may be referenced by public objects through `evidence_refs`, but the
whole `evidence-pool.yaml` is not rendered as a public CMS.

Public projects are curated aggregation views over evidence. Keep
`evidence-pool.yaml` as atomic work traces; group multiple evidence ids into
`projects.yaml` only after review.

## CLI

Validate the public layer:

```bash
nblane public validate <profile>
nblane public validate <profile> --include-drafts
```

Build the static site:

```bash
nblane public build <profile>
nblane public build <profile> --out dist/public/<profile>
nblane public build <profile> --include-drafts
```

Generate resume HTML and Markdown:

```bash
nblane public resume <profile>
nblane public resume <profile> --out profiles/<profile>/resumes/generated/default.html
```

Create draft public outputs:

```bash
nblane public draft-blog <profile> --from-evidence <evidence_id>
nblane public draft-blog <profile> --from-kanban-done
nblane public draft-resume <profile> --target "VLA robotics engineer"
nblane public draft-project-update <profile> --project <project_id>
```

Draft commands use the configured LLM when `LLM_API_KEY` is available and fall
back to conservative templates otherwise. They always write draft content and
never publish automatically.

Write and publish blog posts:

```bash
nblane public blog list <profile> --include-drafts
nblane public blog new <profile> --title "My post" --tag robotics
nblane public blog new <profile> --title "My post" --stdin
nblane public blog media <profile> <slug> \
  --file ./cover.png \
  --kind image \
  --alt "Cover image" \
  --cover \
  --append
nblane public blog media <profile> <slug> \
  --file ./demo.mp4 \
  --kind video \
  --caption "Short demo" \
  --append
nblane public blog publish <profile> <slug>
```

Blog bodies remain Markdown. Images should use normal Markdown syntax:

```markdown
![Alt text](media/blog/<slug>/image.png)
```

Short videos use the nblane video directive:

```markdown
::video[Short demo](media/blog/<slug>/demo.mp4)
::video[External demo](https://example.com/demo.mp4)
```

Local blog media lives under `profiles/<name>/media/blog/<slug>/`. Images may
be `png`, `jpg`, `jpeg`, `webp`, or `gif` up to 10 MB. Local short videos may
be `mp4` or `webm` up to 25 MB. Larger videos should use an external URL or
object storage.

Curate known information into public drafts:

```bash
nblane public suggest-groups <profile> --dry-run
nblane public group <profile> \
  --id piper-home-robot \
  --title "Piper / Home Robot Project" \
  --evidence ev_piper_repro \
  --evidence ev_piper_demo_fix
nblane public hydrate <profile> --dry-run
nblane public hydrate <profile> --write-drafts
```

`suggest-groups` is read-only. `group` writes a `status: draft` project to
`projects.yaml` without changing evidence or skill files. `hydrate` only creates
obvious one-to-one paper/patent output drafts in `outputs.yaml`.

## Streamlit

The generated homepage is a compact content index. It shows the public name,
headline, bio, contacts, and entry points for Blog, Projects, Outputs, and
Resume. Each section shows only a title/count or recent items; clicking through
opens the full list, full post, full project/output list, or full resume.

The Web UI includes a **Public Site** page:

- **Profile** provides structured controls for the public name, headline,
  short bio, contacts, and avatar. Saving uploads the avatar into `media/` and
  updates the `avatar` path in `public-profile.yaml`. The right side shows a
  live full-site preview, including unsaved text and newly uploaded avatars; raw
  YAML remains available in an expander.
- **Blog** creates, edits, previews, drafts, and publishes blog posts.
  The editor keeps front matter in structured fields, edits the body as rich
  Markdown when `streamlit-crepe` is installed, falls back to a Markdown text
  area otherwise, extracts pasted base64 images into `media/blog/<slug>/`, and
  inserts uploaded images, short videos, or video URLs at the
  `<!-- nblane:insert -->` marker or the end of the post.
- **Resume** edits `resume-source.yaml`, previews the generated resume, and
  creates targeted resume drafts.
- **Known Info** shows evidence context, suggested groups, and lets you create
  draft projects from manually selected evidence refs.
- **Build** validates and builds the static site, and can draft project updates.

The page uses the existing profile selector, file snapshot conflict checks,
cache clearing, and optional Git backup.

## Deployment

Recommended split:

```text
app.nblane.cloud  -> protected Streamlit workspace
www.nblane.cloud  -> static files from dist/public/<profile>
```

Caddy example:

```caddyfile
www.example.com {
    root * /srv/nblane-app/dist/public/alice
    file_server
}

app.example.com {
    reverse_proxy 127.0.0.1:8501
}
```

The builder validates first and writes to a temporary directory before replacing
the target output directory. If validation or rendering fails, the previous
published directory is left in place.

## Boundaries

Current implementation intentionally does not include:

- PDF resume generation
- comments
- full-text search
- multi-theme marketplace
- database-backed storage
- object-storage media uploads

Small images can live under `profiles/<name>/media/`. Videos should use
external URLs or object storage by default; small `mp4` / `webm` clips can be
kept under `media/blog/<slug>/` for v1 posts.
