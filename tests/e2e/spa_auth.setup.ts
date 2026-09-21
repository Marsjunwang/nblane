import { expect, request, test as setup } from "@playwright/test";

import {
  SPA_ADMIN_STORAGE_STATE,
  SPA_BASE_URL,
  SPA_ADMIN_USER,
  SPA_ADMIN_PASSWORD,
} from "./spa_auth_shared";

/**
 * Playwright setup project: bake the SPA admin session into a storageState
 * file that the main "chromium" project loads, so the pre-existing specs
 * (spa_smoke / spa_home / spa_mutations / spa_kanban_dnd, which assume an
 * authenticated or auth-less backend) keep passing now that the isolated
 * SPA backend runs with NBLANE_AUTH_FILE set.
 *
 * Auth-off stacks (no users.yaml) are still supported: /auth/me answers the
 * synthetic admin, so an empty state is baked and every spec behaves exactly
 * as before. An unreachable SPA backend likewise degrades to an empty state
 * so the Streamlit-only specs are not held hostage by a missing 18504.
 */

setup("bake SPA admin session storageState", async () => {
  const context = await request.newContext({ baseURL: SPA_BASE_URL });
  try {
    let me;
    try {
      me = await context.get("/api/v1/auth/me");
    } catch {
      console.warn(`spa_auth.setup: SPA backend unreachable at ${SPA_BASE_URL}; baking empty state`);
      await context.storageState({ path: SPA_ADMIN_STORAGE_STATE });
      return;
    }
    if (me.ok()) {
      const body = (await me.json()) as { auth_enabled?: boolean };
      if (!body.auth_enabled) {
        // Auth off: every request already runs as the synthetic local admin.
        await context.storageState({ path: SPA_ADMIN_STORAGE_STATE });
        return;
      }
    }
    // Auth on (me answers 401 without a cookie): log in once as admin.
    const login = await context.post("/api/v1/auth/login", {
      data: { username: SPA_ADMIN_USER, password: SPA_ADMIN_PASSWORD },
    });
    expect(
      login.status(),
      `SPA admin login failed with ${login.status()}: ${await login.text()}\n` +
        `Check the auth users file (default .dev-data/auth/users.yaml) and ` +
        `NBLANE_E2E_ADMIN_USER / NBLANE_E2E_ADMIN_PASSWORD.`,
    ).toBe(200);
    await context.storageState({ path: SPA_ADMIN_STORAGE_STATE });
  } finally {
    await context.dispose();
  }
});
