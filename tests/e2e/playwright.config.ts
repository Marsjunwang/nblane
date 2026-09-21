import { defineConfig } from "@playwright/test";
import fs from "node:fs";
import { DEFAULT_STREAMLIT_BASE_URL } from "./helpers";
import { SPA_ADMIN_STORAGE_STATE } from "./spa_auth_shared";

const systemChromium =
  process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ||
  (fs.existsSync("/snap/bin/chromium") ? "/snap/bin/chromium" : "");

// Port convention (details in tests/e2e/README.md):
//   default dev  (`scripts/dev-web.sh`):            Streamlit 8503 + sidecar 8502
//   isolated dev (`scripts/dev-web.sh --isolated`): Streamlit 18503 + sidecar 18502
// Every spec derives its URLs from use.baseURL: page.goto("/Some_Page") hits
// the Streamlit UI; specs that talk to the Reader API sidecar directly use
// readerBaseURL() from helpers.ts (override via NBLANE_E2E_READER_BASE).
export default defineConfig({
  testDir: ".",
  timeout: 45_000,
  expect: {
    timeout: 8_000,
  },
  use: {
    // Default matches the isolated dev instance so a bare `npm run test:e2e`
    // never collides with a developer's live dev server on 8503.
    baseURL: process.env.NBLANE_E2E_BASE_URL || DEFAULT_STREAMLIT_BASE_URL,
    launchOptions: {
      ...(systemChromium ? { executablePath: systemChromium } : {}),
      args: ["--no-sandbox"],
    },
    trace: "retain-on-failure",
    viewport: { width: 1440, height: 1000 },
  },
  projects: [
    {
      // Logs into the SPA backend (18504) once and bakes the admin session
      // cookie into tests/e2e/.auth/; a no-op empty bake when auth is off.
      name: "spa-auth-setup",
      testMatch: /spa_auth\.setup\.ts/,
    },
    {
      name: "chromium",
      testIgnore: [/spa_auth\.setup\.ts/, /spa_auth\.spec\.ts/],
      dependencies: ["spa-auth-setup"],
      use: {
        // The SPA backend may run with NBLANE_AUTH_FILE (isolated stack does
        // since 2026-09-21): pre-existing specs get the baked admin session.
        // Harmless on auth-less Streamlit/sidecar origins — they ignore the
        // cookie.
        storageState: SPA_ADMIN_STORAGE_STATE,
      },
    },
    {
      // The login journey itself runs with fresh, session-less contexts.
      name: "spa-auth",
      testMatch: /spa_auth\.spec\.ts/,
    },
  ],
});
