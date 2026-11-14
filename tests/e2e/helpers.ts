/**
 * Shared URL helpers for the nblane browser e2e suite.
 *
 * run.mjs supplies fresh loopback ports and a temporary data root. Global
 * setup checks both server identities before any spec can mutate files.
 * The fallback URL only permits Playwright to collect specs outside a run;
 * the ownership check rejects execution without the generated environment.
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

/** Data root owned by run.mjs; never fall back to personal/dev profiles. */
export function e2eDataRoot(): string {
  const override = (process.env.NBLANE_E2E_DATA_ROOT || "").trim();
  if (override && process.env.NBLANE_E2E_RUN_ID) {
    return override;
  }
  throw new Error("Use npm run test:e2e to create owned temporary fixtures.");
}

/** Confine configurable fixture names to one directory below profiles/. */
export function fixtureProfileName(fallback: string): string {
  const name = process.env.NBLANE_PAPER_LIBRARY_E2E_PROFILE || fallback;
  if (!name.trim() || name === "." || name === ".." || /[\\/\0]/.test(name)) {
    throw new Error("Invalid E2E fixture profile name.");
  }
  return name;
}
