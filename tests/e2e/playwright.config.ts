import { defineConfig } from "@playwright/test";
import fs from "node:fs";

const systemChromium =
  process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ||
  (fs.existsSync("/snap/bin/chromium") ? "/snap/bin/chromium" : "");

export default defineConfig({
  testDir: ".",
  timeout: 45_000,
  expect: {
    timeout: 8_000,
  },
  use: {
    baseURL: process.env.NBLANE_E2E_BASE_URL || "http://127.0.0.1:8510",
    launchOptions: {
      ...(systemChromium ? { executablePath: systemChromium } : {}),
      args: ["--no-sandbox"],
    },
    trace: "retain-on-failure",
    viewport: { width: 1440, height: 1000 },
  },
});
