import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Shared URL helpers for the nblane browser e2e suite.
 *
 * Port convention (mirrors scripts/dev-web.sh):
 *   - default dev instance:  SPA http://127.0.0.1:8504, Reader API sidecar :8502
 *   - isolated dev instance: SPA http://127.0.0.1:18504, Reader API sidecar :18502
 *     (`scripts/dev-web.sh --isolated`, data under .dev-data/, assets under
 *     .dev-assets/)
 *
 * playwright.config.ts sets `use.baseURL` once (env NBLANE_E2E_BASE_URL,
 * default http://127.0.0.1:18504, the isolated SPA). The helpers below cover
 * the cases that need an absolute URL string (skip messages, cross-origin
 * sidecar calls, deep-link parameters).
 */

export const DEFAULT_SPA_BASE_URL = "http://127.0.0.1:18504";

/** Base URL of the SPA under test (same resolution as playwright.config.ts). */
export function spaBaseURL(): string {
  return (process.env.NBLANE_E2E_BASE_URL || DEFAULT_SPA_BASE_URL).replace(/\/+$/, "");
}

/** Absolute URL of an SPA route, e.g. spaPageURL("/research"). */
export function spaPageURL(path: string = "/"): string {
  return new URL(path, `${spaBaseURL()}/`).toString();
}

// SPA port -> Reader API sidecar port. Keep in sync with scripts/dev-web.sh.
const READER_PORT_BY_SPA_PORT: Record<string, string> = {
  "8504": "8502",
  "18504": "18502",
};

/**
 * Base URL of the Reader API sidecar (paper library, reader). Override with
 * NBLANE_E2E_READER_BASE; otherwise the sidecar port is derived from the SPA
 * baseURL via the mapping above, falling back to the same origin for unknown
 * ports (reverse-proxy setups).
 */
export function readerBaseURL(): string {
  const override = (process.env.NBLANE_E2E_READER_BASE || "").trim();
  if (override) {
    return override.replace(/\/+$/, "");
  }
  const url = new URL(`${spaBaseURL()}/`);
  const mapped = READER_PORT_BY_SPA_PORT[url.port];
  if (mapped) {
    url.port = mapped;
  }
  return url.origin;
}

/** Absolute URL of a sidecar page, e.g. readerPageURL("/paper-library"). */
export function readerPageURL(path: string = "/"): string {
  return new URL(path, `${readerBaseURL()}/`).toString();
}

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

/**
 * Data root (NBLANE_ROOT) of the instance under test. The isolated dev
 * instance serves .dev-data; the default instance serves the repo root.
 * Specs that write fixture profiles must write into the same tree the
 * server reads. Override with NBLANE_E2E_DATA_ROOT for a custom --root.
 */
export function e2eDataRoot(): string {
  const override = (process.env.NBLANE_E2E_DATA_ROOT || "").trim();
  if (override) {
    return override;
  }
  const port = new URL(`${spaBaseURL()}/`).port;
  return port === "18504" ? path.join(repoRoot, ".dev-data") : repoRoot;
}
