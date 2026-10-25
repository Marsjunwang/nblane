import { createServer } from "node:http";
import { createReadStream, existsSync, readFileSync, statSync } from "node:fs";
import { extname, resolve, sep } from "node:path";
import { expect, test } from "@playwright/test";

const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(
  /\/+$/,
  "",
);

function spaURL(path: string): string {
  return new URL(path, `${SPA_BASE_URL}/`).toString();
}

async function startPwaServer() {
  const staticRoot = resolve("src/nblane/web_ui/static");
  let workerSource = readFileSync(resolve(staticRoot, "sw.js"), "utf8");
  const types: Record<string, string> = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
    ".webmanifest": "application/manifest+json",
    ".json": "application/json",
    ".png": "image/png",
    ".svg": "image/svg+xml",
  };
  const server = createServer((request, response) => {
    const pathname = new URL(request.url ?? "/", "http://localhost").pathname;
    if (pathname === "/sw.js") {
      response.writeHead(200, { "Content-Type": "application/javascript", "Cache-Control": "no-cache" });
      response.end(workerSource);
      return;
    }
    let file = resolve(staticRoot, `.${pathname}`);
    if (!file.startsWith(`${staticRoot}${sep}`) || !existsSync(file) || !statSync(file).isFile()) {
      file = resolve(staticRoot, "index.html");
    }
    response.writeHead(200, {
      "Content-Type": types[extname(file)] ?? "application/octet-stream",
      "Cache-Control": "no-cache",
    });
    createReadStream(file).pipe(response);
  });
  await new Promise<void>((ready) => server.listen(0, "127.0.0.1", ready));
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("PWA test server has no port");
  return {
    origin: `http://127.0.0.1:${address.port}`,
    setWorkerSource(source: string) {
      workerSource = source;
    },
    close: () =>
      new Promise<void>((done, reject) => {
        server.close((error) => (error ? reject(error) : done()));
      }),
  };
}

test("PWA manifest and Android asset links are public JSON", async ({ request }) => {
  const manifestResponse = await request.get(spaURL("/manifest.webmanifest"));
  expect(manifestResponse.status()).toBe(200);
  expect(manifestResponse.headers()["content-type"]).toContain("application/manifest+json");
  expect(manifestResponse.headers()["cache-control"]).toContain("no-cache");
  const manifest = await manifestResponse.json();
  expect(manifest.start_url).toBe("/");
  expect(manifest.scope).toBe("/");
  expect(manifest.display).toBe("standalone");
  expect(manifest.icons.length).toBeGreaterThanOrEqual(3);

  const linksResponse = await request.get(spaURL("/.well-known/assetlinks.json"));
  expect(linksResponse.status()).toBe(200);
  expect(linksResponse.headers()["content-type"]).toContain("application/json");
  expect(linksResponse.headers()["cache-control"]).toContain("no-cache");
  const links = await linksResponse.json();
  expect(links[0].target.namespace).toBe("android_app");
  expect(links[0].target.package_name).toBe("cloud.nblane.app");
  expect(links[0].target.sha256_cert_fingerprints[0]).toMatch(/^([0-9A-F]{2}:){31}[0-9A-F]{2}$/);
});

test("PWA offline page never fakes business success and recovers online", async ({
  page,
  context,
}) => {
  await page.goto(spaURL("/"));
  await page.waitForFunction(
    () => navigator.serviceWorker.controller?.state === "activated",
    undefined,
    { timeout: 20_000 },
  );

  await context.setOffline(true);
  await page.goto(spaURL("/p/offline-check/home"), { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "当前处于离线状态" })).toBeVisible();
  const businessRequestFailed = await page.evaluate(async () => {
    try {
      await fetch("/api/v1/health");
      return false;
    } catch {
      return true;
    }
  });
  expect(businessRequestFailed).toBe(true);

  await context.setOffline(false);
  await page.goto(spaURL("/"));
  await expect(page.locator("#root")).toBeVisible();
  await expect(page.getByRole("heading", { name: "当前处于离线状态" })).toHaveCount(0);
});

test("PWA update cleans old caches only after confirmation and preserves drafts", async ({
  page,
}) => {
  const server = await startPwaServer();
  try {
    const workerResponse = await page.request.get(`${server.origin}/sw.js`);
    expect(workerResponse.status()).toBe(200);
    const originalWorker = await workerResponse.text();
    const updatedWorker = originalWorker.replace(
      /"revision":\s*"[^"]*"/,
      '"revision":"pwa-update-test"',
    );
    expect(updatedWorker).not.toBe(originalWorker);

    await page.goto(server.origin);
    await page.waitForFunction(() => navigator.serviceWorker.controller?.state === "activated");
    const assetUrl = await page.evaluate(() =>
      performance
        .getEntriesByType("resource")
        .map((entry) => entry.name)
        .find((name) => name.includes("/assets/") && name.includes("workbox-window")),
    );
    if (!assetUrl) throw new Error("The PWA registration asset did not load");
    const assetStatus = await page.evaluate(async (url) => {
      const response = await fetch(url);
      await response.arrayBuffer();
      return response.status;
    }, assetUrl);
    expect(assetStatus).toBe(200);
    await page.waitForFunction(async () => {
      const names = await caches.keys();
      return names.some((name) => name.startsWith("nblane-static-assets-"));
    });
    const oldCacheNames = await page.evaluate(() => caches.keys());
    expect(oldCacheNames.some((name) => name.startsWith("nblane-shell-"))).toBe(true);
    expect(oldCacheNames.some((name) => name.startsWith("nblane-static-assets-"))).toBe(true);
    await page.evaluate(() => localStorage.setItem("pwa-update-test-draft", "keep-this-draft"));

    server.setWorkerSource(updatedWorker);
    await page.evaluate(async () => {
      const registration = await navigator.serviceWorker.getRegistration();
      await registration?.update();
    });
    await expect(page.getByTestId("pwa-update-prompt")).toBeVisible({ timeout: 20_000 });
    await page.getByRole("button", { name: "立即更新" }).click();
    await page.waitForFunction(() => {
      const controller = navigator.serviceWorker.controller;
      return document.readyState === "complete" && controller?.state === "activated";
    });

    expect(await page.evaluate(() => localStorage.getItem("pwa-update-test-draft"))).toBe(
      "keep-this-draft",
    );
    const refreshedAssetStatus = await page.evaluate(async (url) => {
      const response = await fetch(url);
      await response.arrayBuffer();
      return response.status;
    }, assetUrl);
    expect(refreshedAssetStatus).toBe(200);
    await page.waitForFunction(async (previousNames) => {
      const names = await caches.keys();
      return previousNames.every((name) => !names.includes(name));
    }, oldCacheNames);
    const newCacheNames = await page.evaluate(() => caches.keys());
    expect(newCacheNames.some((name) => name.startsWith("nblane-shell-"))).toBe(true);
    expect(newCacheNames.some((name) => name.startsWith("nblane-static-assets-"))).toBe(true);
    for (const oldName of oldCacheNames) {
      expect(newCacheNames).not.toContain(oldName);
    }
  } finally {
    await server.close();
  }
});
