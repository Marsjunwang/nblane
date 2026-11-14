# Browser e2e tests (Playwright)

`npm run test:e2e` creates synthetic profiles and starts its own SPA and Reader
services on temporary loopback ports. It never uses the running development
stack, `.dev-data`, personal profiles, or the repository `.env`.

## Run

```bash
uv sync --locked --group dev
npm ci
npm run test:e2e:install       # or test:e2e:install:cn for the China mirror
npm run test:e2e              # full suite
npm run test:e2e:spa          # SPA smoke
npm run test:e2e -- spa_mutations --headed
npm run test:e2e:harness      # ownership checks, no browser/server needed
```

The repository's committed SPA and Paper Library bundles are served. Rebuild
the affected frontend before testing source changes.

## Isolated data and server ownership

`run.mjs` creates a unique `nblane-browser-e2e-*` directory in the system temp
directory. `seed.py` uses normal domain writers to generate profiles `dev` and
`other`, goals, tasks, project history, and habits. Both services load the same
generated auth store; the admin sees all profiles and the member sees only
`dev`. No AI key is needed.

Before Playwright setup or specs can write, `global_setup.ts` verifies a unique
run marker on disk and the identity endpoint of both services. These endpoints
exist only in `fixture_server.py`, not the production application. Direct
execution against an ordinary server is rejected. URL/data-root environment
overrides are replaced by the launcher.

After each run, the launcher stops its child processes and removes the temporary
directory. On failure, server logs and browser traces remain in unique
directories under `test-results/`. To inspect generated data after shutdown:

```bash
NBLANE_E2E_KEEP_DATA=1 npm run test:e2e -- spa_mutations
```

Useful environment overrides:

- `NBLANE_E2E_PYTHON`: Python executable; defaults to `.venv/bin/python`, then
  `python3`.
- `PLAYWRIGHT_CHROMIUM_EXECUTABLE`: system Chromium executable instead of the
  downloaded build; `/snap/bin/chromium` is detected automatically.
- `NBLANE_PAPER_LIBRARY_E2E_PROFILE`: alternate synthetic paper fixture name;
  must be a single directory name.

## Authentication projects

- `spa-auth-setup` logs in as the generated admin and saves its session inside
  this run's temporary directory.
- `chromium` loads that session for UI and Reader tests.
- `spa-auth` tests unauthenticated redirects, login/logout, member access, and
  rate limiting with fresh browser contexts.

CI runs the ownership harness checks and isolated login/navigation/task-mutation
smoke tests. The `frontend-artifacts` job runs frontend unit tests, verifies
generated API types, rebuilds committed bundles, and checks the SPA entry's
260 KiB gzip budget (`npm run check:spa-budget`). Python CI and Ubuntu
packaging both use `uv.lock`.

## Retry policy

Fix product races rather than hiding them with retries. There is no global
retry setting. A describe-scoped retry requires evidence of resource-contention
jitter, a comment explaining the cause, and a narrow scope. The login
redirect-back case currently retains one retry for low-spec software-rendering
hosts.
