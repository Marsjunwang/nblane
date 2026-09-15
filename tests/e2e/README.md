# Browser e2e tests (Playwright)

TypeScript specs driven by `@playwright/test` against a running nblane dev
instance. **Not run in CI** (they need live servers); run them locally.

## Port convention

| instance  | command                          | Streamlit | Reader API sidecar | data root   |
| --------- | -------------------------------- | --------- | ------------------ | ----------- |
| isolated  | `scripts/dev-web.sh --isolated`  | 18503     | 18502              | `.dev-data` |
| default   | `scripts/dev-web.sh`             | 8503      | 8502               | repo root   |

Every spec derives its URLs from `use.baseURL` in `playwright.config.ts`
(env `NBLANE_E2E_BASE_URL`, **default `http://127.0.0.1:18503`** — the
isolated instance, so a bare run never collides with a live dev server on
8503). Streamlit pages use relative `page.goto("/Kanban")`; specs that talk
to the Reader API sidecar directly (`/paper-library`, `/dashboard`,
`/blog-editor`) use `readerBaseURL()` from `helpers.ts`, which maps the
Streamlit port to its sidecar port (same mapping as
`src/nblane/web_auth.py`).

## Run

```bash
scripts/dev-web.sh --isolated start     # serve 18502/18503 with .dev-data
npm install                             # once, installs @playwright/test
npm run test:e2e:install                # once, installs the chromium build
npm run test:e2e                        # full suite against 18503
scripts/dev-web.sh --isolated stop
```

Useful variations:

```bash
# target the default dev instance instead
NBLANE_E2E_BASE_URL=http://127.0.0.1:8503 npm run test:e2e

# one spec / headed debugging
npx playwright test -c tests/e2e/playwright.config.ts kanban_toolbar --headed
```

## Environment variables

- `NBLANE_E2E_BASE_URL` — Streamlit UI base URL (sets `use.baseURL`).
- `NBLANE_E2E_READER_BASE` — override the sidecar base URL when it does not
  follow the port mapping (e.g. behind a reverse proxy).
- `NBLANE_E2E_DATA_ROOT` — data root of the instance under test, for specs
  that write fixture profiles (`paper_library_workspace`). Defaults to
  `.dev-data` when baseURL port is 18503, else the repo root.
- `NBLANE_PAPER_LIBRARY_E2E_PROFILE`, `NBLANE_DASHBOARD_E2E_PROFILE` —
  profile names used by the paper-library / dashboard specs.
- `READER_URL` — full reader document URL for `_walkthrough.spec.ts`, a
  manual diagnostic dump (skips when unset).
- `PLAYWRIGHT_CHROMIUM_EXECUTABLE` — use a system chromium instead of the
  downloaded build (auto-detects `/snap/bin/chromium`).

`paper_library.spec.ts` is hermetic: it spawns its own isolated sidecar on a
free port with a temp fixture profile, unless `NBLANE_E2E_READER_BASE` is set.
