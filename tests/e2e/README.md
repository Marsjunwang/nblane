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

## SPA backend auth (login journey)

The isolated stack enables app-level auth on the **SPA backend** (web-api,
18504) whenever `.dev-data/auth/users.yaml` exists — `scripts/dev-web.sh
--isolated` auto-detects it (override with `--auth-file PATH` or
`NBLANE_DEV_AUTH_FILE`). The Streamlit UI and Reader sidecar stay auth-less.
Sandbox accounts (test passwords only): `admin`/`test1234` (all profiles),
`member`/`test1234` (dev profile only).

Playwright is split into three projects:

- `spa-auth-setup` (`spa_auth.setup.ts`) — logs into the SPA backend once as
  admin and bakes `tests/e2e/.auth/spa-admin.json` (gitignored). On auth-less
  stacks it bakes an empty state, so behavior there is unchanged.
- `chromium` — every pre-existing spec; loads the baked file as
  `storageState`, so SPA specs (spa_smoke/spa_home/spa_mutations/
  spa_kanban_dnd/spa_pages/spa_llm_jobs) keep passing with auth on, and
  Streamlit/sidecar specs are unaffected (they ignore the extra cookie).
- `spa-auth` (`spa_auth.spec.ts`) — the login journey itself (deep-link
  bounce, generic wrong-password error, redirect-back after login, logout,
  member profile scoping, rate limiting) on fresh session-less contexts;
  skips wholesale when the backend has auth off.

SPA-targeting env vars: `NBLANE_E2E_SPA_BASE_URL` (default
`http://127.0.0.1:18504`), `NBLANE_E2E_ADMIN_USER` /
`NBLANE_E2E_ADMIN_PASSWORD`, `NBLANE_E2E_MEMBER_USER` /
`NBLANE_E2E_MEMBER_PASSWORD`, `NBLANE_E2E_PROFILE` (default `dev`).

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

## 已知负载型抖动与 retry 约定

On this 2-vCPU/3.75GB sandbox the tail of a full-suite run accumulates
Streamlit sessions and software-GL canvases, so a handful of timing-sensitive
specs (WebGL mounts, Streamlit `networkidle` navigation, the SPA login
redirect-back chain) can sporadically outrun their locator/navigation budgets.
Each passes standalone and on retry, and the failure point does not repeat
across runs — resource-contention jitter, not a product race. The convention:

- real root causes get fixed in product code, never papered over with
  retries;
- the remaining jitter cases carry a **describe-scoped**
  `test.describe.configure({ retries: 1 })` with a comment stating the cause
  (low-spec resource contention), the standalone-stable evidence, and a "do
  not widen" note — currently `startree_check`, `dashboard`,
  `dashboard_canvas`, `dashboard_fix_plan`, `evidence_editor`, and case c of
  `spa_auth`;
- **no global `retries` in `playwright.config.ts`** — a retry must always be
  a deliberate, per-spec exception.
