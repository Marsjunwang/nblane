import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { assertOwnedStack } from "./runtime.mjs";

test("unowned and mismatched servers are rejected before tests can write", async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "nblane-harness-test-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const marker = { root, run_id: "owned-run" };
  fs.writeFileSync(path.join(root, ".nblane-e2e.json"), JSON.stringify(marker));
  const env = {
    NBLANE_E2E_DATA_ROOT: root,
    NBLANE_E2E_RUN_ID: marker.run_id,
    NBLANE_E2E_BASE_URL: "http://127.0.0.1:12345",
    NBLANE_E2E_SPA_BASE_URL: "http://127.0.0.1:12345",
    NBLANE_E2E_READER_BASE: "http://127.0.0.1:12346",
  };
  const response = (identity) => async () => ({ ok: true, json: async () => identity });
  await assert.rejects(assertOwnedStack({}, response(marker)), /temporary servers/);
  await assert.rejects(assertOwnedStack({ ...env, NBLANE_E2E_RUN_ID: "another-run" }, response(marker)), /ownership mismatch/);
  await assert.rejects(assertOwnedStack(env, response({ ...marker, run_id: "another-run" })), /ownership mismatch/);
  await assert.rejects(assertOwnedStack({ ...env, NBLANE_E2E_READER_BASE: "https://example.com" }, response(marker)), /loopback/);
  await assert.rejects(assertOwnedStack(env, async () => ({ ok: false })), /non-test service/);
  await assertOwnedStack(env, response(marker));
});
