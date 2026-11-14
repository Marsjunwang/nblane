import { defineConfig } from "@playwright/test";
import fs from "node:fs";
import { DEFAULT_SPA_BASE_URL } from "./helpers";
import { SPA_ADMIN_STORAGE_STATE } from "./spa_auth_shared";

const systemChromium =
  process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ||
  (fs.existsSync("/snap/bin/chromium") ? "/snap/bin/chromium" : "");

// run.mjs starts fresh SPA and Reader services on allocated loopback ports.
// Direct Playwright execution is rejected by globalSetup's ownership check.
export default defineConfig({
  testDir: ".",
  // Verify both services belong to this run before setup or spec writes.
  globalSetup: "./global_setup.ts",
  workers: 1,
  outputDir: `../../test-results/e2e-${process.env.NBLANE_E2E_RUN_ID || "unowned"}`,
  timeout: 45_000,
  expect: {
    timeout: 8_000,
  },
  use: {
    // The launcher supplies the actual temporary SPA origin.
    baseURL: process.env.NBLANE_E2E_BASE_URL || DEFAULT_SPA_BASE_URL,
    launchOptions: {
      ...(systemChromium ? { executablePath: systemChromium } : {}),
      args: ["--no-sandbox"],
    },
    trace: "retain-on-failure",
    viewport: { width: 1440, height: 1000 },
  },
  projects: [
    {
      // Bake a session for the generated admin into this run's temp root.
      name: "spa-auth-setup",
      testMatch: /spa_auth\.setup\.ts/,
    },
    {
      name: "chromium",
      testIgnore: [/content-image-editor\.spec\.ts/, /spa_auth\.setup\.ts/, /spa_auth\.spec\.ts/],
      dependencies: ["spa-auth-setup"],
      use: {
        // Both fixture services share auth configuration and session secrets.
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
