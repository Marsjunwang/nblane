import fs from "node:fs";
import path from "node:path";

export const IDENTITY_PATH = "/__nblane_e2e__/identity";

/** Refuse shared development/production servers before any test can mutate them. */
export async function assertOwnedStack(env = process.env, request = fetch) {
  const root = env.NBLANE_E2E_DATA_ROOT;
  const runId = env.NBLANE_E2E_RUN_ID;
  if (!root || !runId) {
    throw new Error("Use npm run test:e2e: the suite requires its own temporary servers and fixtures.");
  }
  const marker = JSON.parse(fs.readFileSync(path.join(root, ".nblane-e2e.json"), "utf8"));
  if (marker.run_id !== runId || marker.root !== path.resolve(root)) {
    throw new Error("E2E data-root ownership mismatch; refusing to run.");
  }
  const bases = [env.NBLANE_E2E_BASE_URL, env.NBLANE_E2E_SPA_BASE_URL, env.NBLANE_E2E_READER_BASE];
  for (const base of new Set(bases)) {
    if (!base || new URL(base).hostname !== "127.0.0.1") {
      throw new Error("E2E servers must be owned loopback services.");
    }
    const response = await request(new URL(IDENTITY_PATH, base), { signal: AbortSignal.timeout(5000) });
    if (!response.ok) throw new Error(`Refusing non-test service at ${base}.`);
    const identity = await response.json();
    if (identity.run_id !== runId || identity.root !== marker.root) {
      throw new Error(`E2E server ownership mismatch at ${base}.`);
    }
  }
}
