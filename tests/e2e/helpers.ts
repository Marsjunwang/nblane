import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Shared URL helpers for the nblane browser e2e suite.
 *
 * Port convention (mirrors scripts/dev-web.sh and src/nblane/web_auth.py):
 *   - default dev instance:  Streamlit http://127.0.0.1:8503, sidecar :8502
 *   - isolated dev instance: Streamlit http://127.0.0.1:18503, sidecar :18502
 *     (`scripts/dev-web.sh --isolated`, data under .dev-data/, assets under
 *     .dev-assets/)
 *
 * The whole suite targets ONE Streamlit instance, configured once in
 * playwright.config.ts via `use.baseURL` (env NBLANE_E2E_BASE_URL, default
 * http://127.0.0.1:18503). Specs navigate with relative paths
 * (page.goto("/Kanban")) so Playwright resolves them against that baseURL;
 * the helpers below cover the cases that need an absolute URL string
 * (skip messages, cross-origin sidecar calls, deep-link parameters).
 */

export const DEFAULT_STREAMLIT_BASE_URL = "http://127.0.0.1:18503";

/** Base URL of the Streamlit UI under test (same resolution as playwright.config.ts). */
export function streamlitBaseURL(): string {
  return (process.env.NBLANE_E2E_BASE_URL || DEFAULT_STREAMLIT_BASE_URL).replace(/\/+$/, "");
}

/** Absolute URL of a Streamlit app page, e.g. streamlitPageURL("/Kanban"). */
export function streamlitPageURL(path: string = "/"): string {
  return new URL(path, `${streamlitBaseURL()}/`).toString();
}

// Streamlit port -> Reader API sidecar port. Keep in sync with
// src/nblane/web_auth.py `_sidecar_base_for_same_origin_mode`.
const READER_PORT_BY_STREAMLIT_PORT: Record<string, string> = {
  "8501": "8502",
  "8503": "8502",
  "8510": "8502",
  "18503": "18502",
};

/**
 * Base URL of the Reader API sidecar (paper library, dashboard canvas,
 * blog editor, reader). Override with NBLANE_E2E_READER_BASE; otherwise the
 * sidecar port is derived from the Streamlit baseURL via the mapping above,
 * falling back to the same origin for unknown ports (reverse-proxy setups).
 */
export function readerBaseURL(): string {
  const override = (process.env.NBLANE_E2E_READER_BASE || "").trim();
  if (override) {
    return override.replace(/\/+$/, "");
  }
  const url = new URL(`${streamlitBaseURL()}/`);
  const mapped = READER_PORT_BY_STREAMLIT_PORT[url.port];
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
  const port = new URL(`${streamlitBaseURL()}/`).port;
  return port === "18503" ? path.join(repoRoot, ".dev-data") : repoRoot;
}
