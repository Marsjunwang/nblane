import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Shared knobs for the SPA auth e2e: the storageState setup project
 * (spa_auth.setup.ts), the login journey spec (spa_auth.spec.ts), and
 * playwright.config.ts (which wires the baked state into the main project).
 */

export const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(
  /\/+$/,
  "",
);

// Sandbox credentials from .dev-data/auth/users.yaml (test passwords only,
// overridable for other stacks). Defaults match scripts/dev-web.sh --isolated.
export const SPA_ADMIN_USER = process.env.NBLANE_E2E_ADMIN_USER || "admin";
export const SPA_ADMIN_PASSWORD = process.env.NBLANE_E2E_ADMIN_PASSWORD || "test1234";
export const SPA_MEMBER_USER = process.env.NBLANE_E2E_MEMBER_USER || "member";
export const SPA_MEMBER_PASSWORD = process.env.NBLANE_E2E_MEMBER_PASSWORD || "test1234";
export const SPA_E2E_PROFILE = process.env.NBLANE_E2E_PROFILE || "dev";

const configDir = path.dirname(fileURLToPath(import.meta.url));

/** Baked admin session (cookies) for the main chromium project. Gitignored. */
export const SPA_ADMIN_STORAGE_STATE = path.join(configDir, ".auth", "spa-admin.json");
