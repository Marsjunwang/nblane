# Growth Starmap Playground

Interactive prototype for the "growth starmap" home concept: a Suzhou-stele-style
planisphere that morphs into a deep-space scene. Purely additive — none of the
production component code is touched.

## Run

```bash
# regenerate the data snapshot from a local profile (READ-ONLY on profiles/)
../../../.venv/bin/python playground/tools/export_snapshot.py   # writes playground/data/snapshot.json (gitignored)

npx vite            # dev server, then open /playground.html
```

## URL params

- `?state=planisphere|deepspace` — initial world state
- `?stars=legacy` — legacy star rendering (pre three-state shapes)
- `?title=v1` — legacy five-character title plaque
- `?fx=1` — force the composer (bloom) path even on software GL
- `?panel=0` — hide the debug panel
