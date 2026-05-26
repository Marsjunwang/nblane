import { expect, test } from "@playwright/test";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const e2eDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(e2eDir, "../..");
const profileName = process.env.NBLANE_E2E_8502_PROFILE || "e2e-paper-library";
let tempRoot = "";
let server: ChildProcessWithoutNullStreams | null = null;
let baseUrl = process.env.NBLANE_E2E_8502_BASE_URL?.replace(/\/$/, "") || "";
let serverOutput = "";

function writeFixtureProfile(root: string) {
  const profileRoot = path.join(root, "profiles", profileName);
  const researchRoot = path.join(profileRoot, "research");
  fs.mkdirSync(researchRoot, { recursive: true });
  fs.writeFileSync(
    path.join(researchRoot, "sources.yaml"),
    JSON.stringify(
      {
        schema_version: "1.0",
        profile: profileName,
        updated: "2026-05-22",
        sources: [
          {
            id: "source:paper:e2e-alpha",
            kind: "paper",
            title: "E2E Alpha Methods",
            status: "reading",
            visibility: "private",
            origin: "manual",
            authors: ["Ada Lovelace", "Grace Hopper"],
            published: "2026",
            tags: ["e2e", "workspace"],
            summary: "A deterministic paper used by the 8502 Paper Library browser test.",
            notes: "Should move into a collection without a Streamlit rerun.",
          },
          {
            id: "source:paper:e2e-beta",
            kind: "paper",
            title: "E2E Beta Cleanup",
            status: "inbox",
            visibility: "private",
            origin: "manual",
            authors: ["Katherine Johnson"],
            published: "2025",
            tags: ["e2e", "delete"],
            summary: "A disposable paper used to verify delete preview and confirmation.",
          },
        ],
      },
      null,
      2,
    ),
  );
}

function freePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const socket = net.createServer();
    socket.once("error", reject);
    socket.listen(0, "127.0.0.1", () => {
      const address = socket.address();
      socket.close(() => {
        if (address && typeof address === "object") {
          resolve(address.port);
        } else {
          reject(new Error("Could not allocate an e2e server port."));
        }
      });
    });
  });
}

async function waitForHttp(url: string, timeoutMs = 20_000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = "";
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
      lastError = `${response.status} ${response.statusText}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Timed out waiting for ${url}: ${lastError}\n${serverOutput}`);
}

async function startIsolated8502() {
  tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "nblane-paper-library-8502-"));
  writeFixtureProfile(tempRoot);
  const port = await freePort();
  baseUrl = `http://127.0.0.1:${port}`;
  const venvPython = path.join(repoRoot, ".venv", "bin", "python");
  const python = process.env.NBLANE_E2E_PYTHON || (fs.existsSync(venvPython) ? venvPython : "python3");
  server = spawn(
    python,
    ["-m", "uvicorn", "nblane.web_reader_api:app", "--host", "127.0.0.1", "--port", String(port)],
    {
      cwd: repoRoot,
      env: {
        ...process.env,
        NBLANE_ROOT: tempRoot,
        NBLANE_READER_TOKEN_SECRET: "paper-library-e2e-secret",
        NBLANE_RESEARCH_ASSET_ROOT: path.join(tempRoot, "assets"),
        PYTHONPATH: path.join(repoRoot, "src"),
      },
    },
  );
  server.stdout.on("data", (chunk) => {
    serverOutput += chunk.toString();
  });
  server.stderr.on("data", (chunk) => {
    serverOutput += chunk.toString();
  });
  await waitForHttp(`${baseUrl}/paper-library?profile=${encodeURIComponent(profileName)}`);
}

async function stableScreenshot(page, name: string, testInfo) {
  await page.locator(".paper-workspace-loading").waitFor({ state: "detached", timeout: 8000 }).catch(() => {});
  const body = await page.screenshot({ fullPage: true });
  await testInfo.attach(name, { body, contentType: "image/png" });
  expect(body.byteLength).toBeGreaterThan(30_000);
}

test.beforeAll(async () => {
  if (!baseUrl) {
    await startIsolated8502();
  }
});

test.afterAll(async () => {
  if (server) {
    server.kill("SIGTERM");
  }
  if (tempRoot) {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
});

test("8502 standalone Paper Library covers collection, delete preview, and screenshots", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${baseUrl}/paper-library?profile=${encodeURIComponent(profileName)}`, {
    waitUntil: "domcontentloaded",
    timeout: 20_000,
  });

  await expect(page.locator(".paper-tree-shell.is-standalone")).toBeVisible();
  await expect(page.locator(".paper-workbench")).toBeVisible();
  await expect(page.locator('[data-paper-id="source:paper:e2e-alpha"]')).toBeVisible();
  await expect(page.locator('[data-paper-id="source:paper:e2e-beta"]')).toBeVisible();
  await expect(page.locator(".paper-detail-pane")).toContainText("E2E Alpha Methods");

  const desktopLayout = await page.locator(".paper-workbench").evaluate(() => {
    const rectOf = (selector: string) => {
      const element = document.querySelector(selector);
      const rect = element?.getBoundingClientRect();
      return rect ? { left: rect.left, right: rect.right, width: rect.width, height: rect.height } : null;
    };
    return {
      tree: rectOf(".paper-tree-pane"),
      list: rectOf(".paper-list-pane"),
      detail: rectOf(".paper-detail-pane"),
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    };
  });
  expect(desktopLayout.tree?.width).toBeGreaterThan(220);
  expect(desktopLayout.list?.width).toBeGreaterThan(360);
  expect(desktopLayout.detail?.width).toBeGreaterThan(280);
  expect(desktopLayout.tree!.right).toBeLessThanOrEqual(desktopLayout.list!.left + 2);
  expect(desktopLayout.list!.right).toBeLessThanOrEqual(desktopLayout.detail!.left + 2);
  expect(desktopLayout.scrollWidth).toBeLessThanOrEqual(desktopLayout.viewportWidth + 4);
  await stableScreenshot(page, "paper-library-8502-desktop", testInfo);

  await page.getByRole("button", { name: "New collection" }).first().click();
  const createDialog = page.getByRole("dialog");
  await expect(createDialog).toBeVisible();
  await createDialog.getByLabel("Collection title").fill("E2E Workspace");
  await createDialog.getByRole("button", { name: "Save" }).click();
  await expect(page.locator(".paper-tree-row").filter({ hasText: "E2E Workspace" })).toBeVisible();

  await page.locator('[data-paper-id="source:paper:e2e-alpha"]').click({ button: "right" });
  await expect(page.getByRole("menu")).toBeVisible();
  await page.getByRole("menu").getByRole("button", { name: "Move to collection" }).click();
  const moveDialog = page.getByRole("dialog");
  await moveDialog.locator("select").selectOption({ label: "E2E Workspace" });
  await moveDialog.getByRole("button", { name: "Save" }).click();

  await page.locator(".paper-tree-row").filter({ hasText: "E2E Workspace" }).locator(".paper-tree-main").click();
  await expect(page.locator('[data-paper-id="source:paper:e2e-alpha"]')).toBeVisible();
  await expect(page.locator('[data-paper-id="source:paper:e2e-beta"]')).toHaveCount(0);

  await page.locator(".paper-tree-row.is-view").filter({ hasText: "All Papers" }).locator(".paper-tree-main").click();
  await page.locator('[data-paper-id="source:paper:e2e-beta"] .paper-card-body').click();
  await expect(page.locator(".paper-detail-pane")).toContainText("E2E Beta Cleanup");
  await page.locator(".paper-detail-danger").getByRole("button", { name: "Delete paper..." }).click();

  const deleteDialog = page.locator(".paper-delete-dialog");
  await expect(deleteDialog).toBeVisible();
  await expect(deleteDialog).toContainText("source:paper:e2e-beta");
  await expect(deleteDialog.locator(".paper-delete-grid")).toBeVisible();
  await expect(deleteDialog).toContainText("Active annotations");
  await deleteDialog.getByLabel("Type the source id to confirm deletion.").fill("source:paper:e2e-beta");
  await expect(deleteDialog.getByRole("button", { name: "Delete paper..." })).toBeEnabled();
  await deleteDialog.getByRole("button", { name: "Delete paper..." }).click();
  await expect(deleteDialog).toHaveCount(0);
  await expect(page.locator('[data-paper-id="source:paper:e2e-beta"]')).toHaveCount(0);

  const apiResponse = await page.request.get(`${baseUrl}/api/research/${encodeURIComponent(profileName)}/paper-library`);
  expect(apiResponse.ok()).toBeTruthy();
  const apiPayload = await apiResponse.json();
  expect(apiPayload.payload.metrics.papers).toBe(1);

  await page.setViewportSize({ width: 390, height: 820 });
  await page.goto(`${baseUrl}/paper-library?profile=${encodeURIComponent(profileName)}`, {
    waitUntil: "domcontentloaded",
    timeout: 20_000,
  });
  await expect(page.locator(".paper-tree-shell.is-standalone")).toBeVisible();
  await expect(page.locator('[data-paper-id="source:paper:e2e-alpha"]')).toBeVisible();
  const mobileLayout = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    viewportWidth: window.innerWidth,
    hasDetail: Boolean(document.querySelector(".paper-detail-pane")),
  }));
  expect(mobileLayout.hasDetail).toBeTruthy();
  expect(mobileLayout.scrollWidth).toBeLessThanOrEqual(mobileLayout.viewportWidth + 4);
  await stableScreenshot(page, "paper-library-8502-mobile", testInfo);
});
