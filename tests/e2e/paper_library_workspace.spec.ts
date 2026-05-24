import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

function findRepoRoot(): string {
  let current = process.cwd();
  for (let index = 0; index < 8; index += 1) {
    if (
      fs.existsSync(path.join(current, "profiles")) &&
      fs.existsSync(path.join(current, "tests", "e2e"))
    ) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      break;
    }
    current = parent;
  }
  return process.cwd();
}

const repoRoot = findRepoRoot();
const profileName = process.env.NBLANE_PAPER_LIBRARY_E2E_PROFILE || "paper-library-e2e";
const e2eBaseUrl =
  process.env.NBLANE_PAPER_LIBRARY_E2E_BASE_URL ||
  process.env.NBLANE_E2E_BASE_URL ||
  "http://127.0.0.1:8502";

const profileDir = path.join(repoRoot, "profiles", profileName);
const researchDir = path.join(profileDir, "research");

function yamlString(value: string): string {
  return JSON.stringify(value);
}

function resetFixtureProfile() {
  fs.rmSync(profileDir, { recursive: true, force: true });
  fs.mkdirSync(researchDir, { recursive: true });
  fs.writeFileSync(
    path.join(researchDir, "library-tree.yaml"),
    `# Paper library tree for ${profileName}

schema_version: "1.0"
profile: ${yamlString(profileName)}
updated: "2026-05-22"
nodes:
  - id: paper-node:e2e-fixture
    title: Fixture Collection
    parent_id: ""
    description: Papers used by the 8502 Playwright fixture.
    color: teal
    order: 10
    status: active
    created_by: test
  - id: paper-node:e2e-empty
    title: Empty Collection
    parent_id: ""
    description: Empty collection for screenshot and filter checks.
    color: gray
    order: 20
    status: active
    created_by: test
`,
    "utf-8",
  );
  fs.writeFileSync(
    path.join(researchDir, "sources.yaml"),
    `schema_version: "1.0"
profile: ${yamlString(profileName)}
updated: "2026-05-22"
sources:
  - id: source:e2e:pdf-ready
    kind: paper
    title: "Extremely Long English Paper Title for Responsive Paper Library Workspace Validation Across Desktop Laptop And Narrow Layouts"
    status: reading
    visibility: private
    origin: manual
    authors:
      - Ada Lovelace
      - Grace Hopper
    published: "2026"
    tags:
      - robot-memory
      - benchmark
    library_node_refs:
      - paper-node:e2e-fixture
    summary: "PDF ready paper used to verify Open Reader actions, long title wrapping, and detail metrics."
    metadata:
      pdf_asset_ref: papers/e2e-ready.pdf
      page_count: 18
      last_read_at: "2026-05-22T09:30:00+08:00"
      last_read_page: 7
      structured_extracted_at: "2026-05-22T09:35:00+08:00"
  - id: source:e2e:no-pdf
    kind: paper
    title: "超长中文论文标题用于验证论文库工作台在窄屏和详情面板中不会溢出并保持可读"
    status: inbox
    visibility: private
    origin: manual
    tags:
      - 中文标题
      - no-pdf
    summary: "No PDF paper used for missing PDF badges and Chinese title screenshots."
    metadata:
      pdf_download_status: failed
      year: "2025"
  - id: source:e2e:many-badges-a
    kind: paper
    title: "Badge Saturation Paper"
    status: candidate_ready
    visibility: private
    origin: manual
    tags:
      - duplicate
      - stale
    summary: "First duplicate-title row used to create many badges."
    metadata:
      pdf_download_status: failed
  - id: source:e2e:many-badges-b
    kind: paper
    title: "Badge Saturation Paper"
    status: reading
    visibility: private
    origin: manual
    tags:
      - duplicate
      - review
    summary: "Second duplicate-title row used to create duplicate-risk badges."
    metadata:
      pdf_download_status: failed
  - id: source:e2e:discarded
    kind: paper
    title: "Discarded Paper Safe Delete Preview"
    status: discarded
    visibility: private
    origin: manual
    summary: "Discarded paper with no blocking refs; used only to open delete preview."
    metadata:
      pdf_asset_ref: papers/discarded-preview.pdf
      page_count: 3
`,
    "utf-8",
  );
}

function cleanupFixtureProfile() {
  fs.rmSync(profileDir, { recursive: true, force: true });
}

function paperLibraryUrl(params: Record<string, string> = {}): string {
  const url = new URL("/paper-library", e2eBaseUrl);
  url.searchParams.set("profile", profileName);
  for (const [key, value] of Object.entries(params)) {
    if (value) {
      url.searchParams.set(key, value);
    }
  }
  return url.toString();
}

async function openPaperLibrary(page, params: Record<string, string> = {}) {
  let response;
  try {
    response = await page.goto(paperLibraryUrl(params), {
      waitUntil: "domcontentloaded",
      timeout: 20_000,
    });
  } catch {
    test.skip(true, "Run the 8502 Reader API sidecar or set NBLANE_PAPER_LIBRARY_E2E_BASE_URL.");
  }
  if (!response || response.status() >= 400) {
    test.skip(true, "Paper Library workspace is not available at the configured 8502 URL.");
  }
  await expect(page.locator(".paper-tree-shell.is-standalone")).toBeVisible();
  await expect(page.locator(".paper-workbench")).toBeVisible();
  await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => {});
}

function treeRow(page, title: string) {
  return page.locator(".paper-tree-row").filter({ hasText: title }).first();
}

function paperCard(page, sourceId: string) {
  return page.locator(`.paper-list-card[data-paper-id="${sourceId}"]`).first();
}

async function saveDialog(page) {
  await page.locator(".paper-tree-dialog").last().getByRole("button", { name: "Save" }).click();
}

async function createTopCollection(page, title: string) {
  await page.locator(".paper-tree-section.is-collections .paper-tree-head-action").click();
  const dialog = page.locator(".paper-tree-dialog").last();
  await expect(dialog).toBeVisible();
  await dialog.locator("input").fill(title);
  await saveDialog(page);
  await expect(treeRow(page, title)).toBeVisible();
}

async function openRowMenu(page, title: string) {
  const row = treeRow(page, title);
  await expect(row).toBeVisible();
  await row.locator(".paper-tree-more").click();
  await expect(page.locator(".paper-tree-menu")).toBeVisible();
}

async function dragInto(page, source, target) {
  const sourceBox = await source.boundingBox();
  const targetBox = await target.boundingBox();
  if (!sourceBox || !targetBox) {
    test.skip(true, "Drag source or target is not measurable in this browser.");
  }
  await page.mouse.move(sourceBox.x + sourceBox.width / 2, sourceBox.y + sourceBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(targetBox.x + targetBox.width / 2, targetBox.y + targetBox.height / 2, {
    steps: 10,
  });
  await expect(target).toHaveClass(/is-drop-into/);
  await page.mouse.up();
}

test.describe.configure({ mode: "serial" });
test.setTimeout(90_000);

test.beforeEach(() => {
  resetFixtureProfile();
});

test.afterAll(() => {
  cleanupFixtureProfile();
});

test("8502 standalone Paper Library completes core workspace actions", async ({ page }) => {
  await openPaperLibrary(page);
  await expect(page.locator(".paper-reading-card")).toContainText("Abstract Preview");
  await expect(page.locator(".paper-reading-card")).toContainText("PDF ready paper used to verify Open Reader actions");

  await createTopCollection(page, "E2E Created Collection");
  await openRowMenu(page, "E2E Created Collection");
  await page.locator(".paper-tree-menu").getByRole("button", { name: "Rename" }).click();
  await page.locator(".paper-tree-dialog input").fill("E2E Renamed Collection");
  await saveDialog(page);
  await expect(treeRow(page, "E2E Renamed Collection")).toBeVisible();

  await openRowMenu(page, "E2E Renamed Collection");
  await page.locator(".paper-tree-menu").getByRole("button", { name: "New subcollection" }).click();
  await page.locator(".paper-tree-dialog input").fill("E2E Child Collection");
  await saveDialog(page);
  await expect(treeRow(page, "E2E Child Collection")).toBeVisible();

  await dragInto(page, treeRow(page, "E2E Child Collection"), treeRow(page, "Empty Collection"));
  await expect(treeRow(page, "E2E Child Collection")).toBeVisible();

  await paperCard(page, "source:e2e:pdf-ready").dragTo(treeRow(page, "E2E Renamed Collection"));
  await treeRow(page, "E2E Renamed Collection").locator(".paper-tree-main").click();
  await expect(paperCard(page, "source:e2e:pdf-ready")).toBeVisible();

  await treeRow(page, "All Papers").locator(".paper-tree-main").click();
  await expect(paperCard(page, "source:e2e:no-pdf")).toBeVisible();
  await paperCard(page, "source:e2e:no-pdf").click({ button: "right" });
  await page.locator(".paper-tree-menu").getByRole("button", { name: "Add to collection" }).click();
  const locationDialog = page.locator(".paper-tree-dialog").last();
  await locationDialog.locator("select").selectOption({ label: "E2E Renamed Collection" });
  await saveDialog(page);
  await treeRow(page, "E2E Renamed Collection").locator(".paper-tree-main").click();
  await expect(paperCard(page, "source:e2e:no-pdf")).toBeVisible();

  await treeRow(page, "All Papers").locator(".paper-tree-main").click();
  await expect.poll(async () => {
    const url = new URL(page.url());
    return `${url.searchParams.get("view") || ""}:${url.searchParams.get("node_id") || ""}`;
  }).toBe("all:");
  const searchInput = page.locator(".paper-workspace-controls input");
  const applySearch = page.locator(".paper-workspace-controls").getByRole("button", { name: "Apply" });
  await searchInput.fill("超长中文论文标题");
  await searchInput.press("Enter");
  await applySearch.click();
  await expect.poll(async () => new URL(page.url()).searchParams.get("query") || "").toBe("超长中文论文标题");
  await expect(paperCard(page, "source:e2e:no-pdf")).toBeVisible();
  await expect(page.locator(".paper-list-card")).toHaveCount(1);
  await searchInput.fill("");
  await searchInput.press("Enter");
  await applySearch.click();
  await expect.poll(async () => new URL(page.url()).searchParams.get("query") || "").toBe("");
  await expect(paperCard(page, "source:e2e:pdf-ready")).toBeVisible();

  await createTopCollection(page, "E2E Trash Candidate");
  await openRowMenu(page, "E2E Trash Candidate");
  await page.locator(".paper-tree-menu").getByRole("button", { name: "Delete collection" }).click();
  await page.locator(".paper-tree-dialog").getByRole("button", { name: "Delete collection" }).click();
  await expect.poll(async () => (await treeRow(page, "E2E Trash Candidate").getAttribute("class")) || "")
    .toContain("is-collection_trash");
  await openRowMenu(page, "E2E Trash Candidate");
  await expect(page.locator(".paper-tree-menu").getByRole("button", { name: "Restore collection" })).toBeVisible();
  await page.locator(".paper-tree-menu").getByRole("button", { name: "Restore collection" }).click();
  await expect.poll(async () => (await treeRow(page, "E2E Trash Candidate").getAttribute("class")) || "")
    .not.toContain("is-collection_trash");
  await expect(treeRow(page, "E2E Trash Candidate")).toBeVisible();
  await openRowMenu(page, "E2E Trash Candidate");
  await page.locator(".paper-tree-menu").getByRole("button", { name: "Delete collection" }).click();
  await page.locator(".paper-tree-dialog").getByRole("button", { name: "Delete collection" }).click();
  await expect.poll(async () => (await treeRow(page, "E2E Trash Candidate").getAttribute("class")) || "")
    .toContain("is-collection_trash");
  await openRowMenu(page, "E2E Trash Candidate");
  await page.locator(".paper-tree-menu").getByRole("button", { name: "Purge forever" }).click();
  await page.locator(".paper-tree-dialog").getByRole("button", { name: "Purge forever" }).click();
  await expect(treeRow(page, "E2E Trash Candidate")).toHaveCount(0);

  await treeRow(page, "Discarded").locator(".paper-tree-main").click();
  await expect(paperCard(page, "source:e2e:discarded")).toBeVisible();
  await paperCard(page, "source:e2e:discarded").locator(".paper-card-body").click();
  await expect(page.locator(".paper-detail-source")).toHaveText("source:e2e:discarded");
  await page.locator(".paper-detail-danger").getByRole("button", { name: "Delete paper..." }).click();
  const deleteDialog = page.locator(".paper-delete-dialog");
  await expect(deleteDialog).toBeVisible();
  await expect(deleteDialog).toContainText("PDF asset");
  await expect(deleteDialog).toContainText("papers/discarded-preview.pdf");
  await expect(
    deleteDialog.locator(".paper-delete-check").filter({ hasText: "Delete PDF asset" }).locator("input"),
  ).not.toBeChecked();
});

test("8502 Paper Library consumes Overview deep links", async ({ page }) => {
  await openPaperLibrary(page, {
    view: "needs_extraction",
    detail_id: "source:e2e:pdf-ready",
    focus: "artifacts",
    action: "run_extraction",
    return_to: "overview",
    return_url: "http://127.0.0.1:8503/Research",
  });

  const url = new URL(page.url());
  expect(url.searchParams.get("view")).toBe("needs_extraction");
  expect(url.searchParams.get("detail_id")).toBe("source:e2e:pdf-ready");
  expect(url.searchParams.get("focus")).toBe("artifacts");
  expect(url.searchParams.get("action")).toBe("run_extraction");
  expect(url.searchParams.get("return_to")).toBe("overview");
  expect(url.searchParams.get("return_url")).toBe("http://127.0.0.1:8503/Research");

  await expect(paperCard(page, "source:e2e:pdf-ready")).toBeVisible();
  await expect(paperCard(page, "source:e2e:pdf-ready")).toHaveClass(/is-deep-linked/);
  await expect(page.locator('[data-focus-section="artifacts"]')).toHaveClass(/is-focused/);
  await expect(page.locator('[data-deep-link-action="run_extraction"]')).toContainText("Run extraction");
  await expect(page.locator(".paper-detail-actions button.is-suggested").filter({ hasText: "Run extraction" })).toBeVisible();
  await expect(page.locator(".paper-return-link")).toContainText("Back to Overview");
  await expect(page.locator(".paper-return-link")).toHaveAttribute("href", "http://127.0.0.1:8503/Research");

  await openPaperLibrary(page, {
    view: "all",
    detail_id: "source:e2e:pdf-ready",
    focus: "translations",
    action: "retry_translation",
    return_to: "overview",
    return_url: "http://127.0.0.1:8503/Research",
  });
  await expect(page.locator('[data-focus-section="translations"]')).toHaveClass(/is-focused/);
  await expect(page.locator('[data-deep-link-action="retry_translation"]')).toContainText("Retry translation");
  await expect(page.locator(".paper-detail-actions button.is-suggested").filter({ hasText: "Retry translation" })).toBeVisible();
});

test("8502 Paper Library shows retry translation job progress", async ({ page }) => {
  const sourceId = "source:e2e:pdf-ready";
  await openPaperLibrary(page, {
    view: "all",
    detail_id: sourceId,
    focus: "translations",
    action: "retry_translation",
  });

  await expect(page.locator(".paper-detail-title")).toContainText("Extremely Long English Paper Title");
  const apiPayload = await page.evaluate(async ({ profileName, sourceId }) => {
    const response = await fetch(
      `/api/research/${encodeURIComponent(profileName)}/paper-library?view=all&detail_id=${encodeURIComponent(sourceId)}&focus=translations`,
      { credentials: "same-origin" },
    );
    const data = await response.json();
    return data.payload;
  }, { profileName, sourceId });

  let pollCount = 0;
  await page.route("**/api/research/**/paper-library/events/jobs", async (route) => {
    if (route.request().method() !== "POST") {
      await route.fallback();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        job_id: "mock-translation-job",
        job: {
          job_id: "mock-translation-job",
          status: "running",
          phase: "translation",
          message: "Starting full-paper translation.",
          elapsed_ms: 100,
          batches: 3,
          batches_completed: 0,
          segments_selected: 6,
          segments_processed: 0,
          updated: 0,
          warning_count: 0,
          source_id: sourceId,
          scope: "structure",
        },
      }),
    });
  });
  await page.route("**/api/research/**/paper-library/events/jobs/mock-translation-job", async (route) => {
    pollCount += 1;
    const done = pollCount >= 2;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        job: {
          job_id: "mock-translation-job",
          status: done ? "done" : "running",
          phase: done ? "done" : "translation",
          message: done ? "Mock translation finished." : "Translating batch 1/3.",
          elapsed_ms: done ? 2600 : 1300,
          batches: 3,
          batches_completed: done ? 3 : 1,
          segments_selected: 6,
          segments_processed: done ? 6 : 2,
          updated: done ? 3 : 1,
          warning_count: 0,
          source_id: sourceId,
          scope: "structure",
        },
        result: done
          ? {
              ok: true,
              result: {
                ok: true,
                message: "Mock translation finished.",
                changed: { sources: [sourceId], translations: [sourceId] },
                next: { detail_id: sourceId, focus: "translations", action: "" },
                warnings: [],
                data: { translation_summaries: [{ updated: 3, stale: 0, missing: 0, failed: 0 }] },
              },
              payload: apiPayload,
            }
          : null,
      }),
    });
  });

  const retryButton = page.locator(".paper-detail-actions").getByRole("button", { name: "Retry translation" });
  await expect(retryButton).toBeEnabled();
  await retryButton.click();

  await expect(page.locator(".paper-workspace-task-progress")).toContainText("Starting full-paper translation.");
  await expect(page.locator(".paper-workspace-task-progress")).toContainText("0/3 batches");
  await expect(page.locator(".paper-workspace-task-progress")).toContainText("0/6 units");
  await expect(page.locator(".paper-workspace-task-progress")).toContainText("Translating batch 1/3.", { timeout: 6_000 });
  await expect(page.locator(".paper-workspace-task-progress")).toContainText("1/3 batches");
  await expect(page.locator(".paper-workspace-task-progress")).toContainText("2/6 units");
  await expect(page.locator(".paper-workspace-notice")).toContainText("Mock translation finished.", { timeout: 8_000 });
  await expect(page.locator(".paper-workspace-task-progress")).toContainText("3/3 batches");
  await expect(page.locator(".paper-workspace-task-progress")).toContainText("6/6 units");
  await expect(page.locator(".paper-workspace-task-progress")).toContainText("3 updated");
  await expect(page.locator(".paper-detail-title")).toContainText("Extremely Long English Paper Title");
  await expect(page.locator(".paper-workbench")).toBeVisible();
  await expect.poll(async () => page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )).toBeLessThanOrEqual(2);
});

test("8502 Paper Library shows run extraction fallback-ready progress", async ({ page }) => {
  const sourceId = "source:e2e:pdf-ready";
  await openPaperLibrary(page, {
    view: "all",
    detail_id: sourceId,
    focus: "artifacts",
    action: "run_extraction",
  });

  const apiPayload = await page.evaluate(async ({ profileName, sourceId }) => {
    const response = await fetch(
      `/api/research/${encodeURIComponent(profileName)}/paper-library?view=all&detail_id=${encodeURIComponent(sourceId)}&focus=artifacts`,
      { credentials: "same-origin" },
    );
    const data = await response.json();
    return data.payload;
  }, { profileName, sourceId });

  let pollCount = 0;
  await page.route("**/api/research/**/paper-library/events/jobs", async (route) => {
    if (route.request().method() !== "POST") {
      await route.fallback();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        job_id: "mock-extraction-job",
        job: {
          job_id: "mock-extraction-job",
          status: "running",
          phase: "fallback_ready",
          message: "Using current fallback text; recent GROBID failure was not retried.",
          elapsed_ms: 120,
          step_current: 2,
          step_total: 3,
          saved: 18,
          source_id: sourceId,
        },
      }),
    });
  });
  await page.route("**/api/research/**/paper-library/events/jobs/mock-extraction-job", async (route) => {
    pollCount += 1;
    const done = pollCount >= 2;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        job: {
          job_id: "mock-extraction-job",
          status: done ? "done" : "running",
          phase: done ? "done" : "fallback_ready",
          message: done ? "Fallback text ready: 18 page(s), 18 segment(s)." : "Using current fallback text; recent GROBID failure was not retried.",
          elapsed_ms: done ? 1400 : 600,
          step_current: done ? 3 : 2,
          step_total: 3,
          saved: 18,
          source_id: sourceId,
        },
        result: done
          ? {
              ok: true,
              result: {
                ok: true,
                message: "Fallback text ready: 18 page(s), 18 segment(s).",
                changed: { sources: [sourceId] },
                next: { detail_id: sourceId, focus: "artifacts", action: "" },
                warnings: [],
                data: { extraction_summaries: [{ ready: true, status: "fallback", pages: 18, segments: 18 }] },
              },
              payload: apiPayload,
            }
          : null,
      }),
    });
  });

  const runButton = page.locator(".paper-detail-actions").getByRole("button", { name: "Run extraction" });
  await expect(runButton).toBeEnabled();
  await runButton.click();

  await expect(page.locator(".paper-workspace-task-progress")).toContainText("Using current fallback text");
  await expect(page.locator(".paper-workspace-task-progress")).toContainText("2/3 steps");
  await expect(page.locator(".paper-workspace-task-progress")).toContainText("18 saved");
  await expect(page.locator(".paper-workspace-notice")).toContainText("Fallback text ready", { timeout: 8_000 });
  await expect(page.locator(".paper-workspace-task-progress")).toContainText("3/3 steps");
  await expect(page.locator(".paper-detail-title")).toContainText("Extremely Long English Paper Title");
  await expect(page.locator(".paper-workbench")).toBeVisible();
});

test("8502 Paper Library force GROBID upgrade sends explicit override", async ({ page }) => {
  const sourceId = "source:e2e:pdf-ready";
  await openPaperLibrary(page, {
    view: "all",
    detail_id: sourceId,
    focus: "artifacts",
  });

  const apiPayload = await page.evaluate(async ({ profileName, sourceId }) => {
    const response = await fetch(
      `/api/research/${encodeURIComponent(profileName)}/paper-library?view=all&detail_id=${encodeURIComponent(sourceId)}&focus=artifacts`,
      { credentials: "same-origin" },
    );
    const data = await response.json();
    return data.payload;
  }, { profileName, sourceId });

  let sawForceOverride = false;
  await page.route("**/api/research/**/paper-library/events/jobs", async (route) => {
    if (route.request().method() !== "POST") {
      await route.fallback();
      return;
    }
    const body = route.request().postDataJSON();
    sawForceOverride = Boolean(body?.payload?.force_grobid);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        job_id: "mock-grobid-upgrade-job",
        job: {
          job_id: "mock-grobid-upgrade-job",
          status: "running",
          phase: "running_grobid",
          message: "Running GROBID...",
          elapsed_ms: 120,
          step_current: 2,
          step_total: 3,
          source_id: sourceId,
        },
      }),
    });
  });
  await page.route("**/api/research/**/paper-library/events/jobs/mock-grobid-upgrade-job", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        job: {
          job_id: "mock-grobid-upgrade-job",
          status: "done",
          phase: "done",
          message: "Extraction ready: 18 page(s), 18 segment(s).",
          elapsed_ms: 1600,
          step_current: 3,
          step_total: 3,
          saved: 18,
          source_id: sourceId,
        },
        result: {
          ok: true,
          result: {
            ok: true,
            message: "Extraction ready: 18 page(s), 18 segment(s).",
            changed: { sources: [sourceId] },
            next: { detail_id: sourceId, focus: "artifacts", action: "" },
            warnings: [],
            data: { extraction_summaries: [{ ready: true, status: "ready", pages: 18, segments: 18 }] },
          },
          payload: apiPayload,
        },
      }),
    });
  });

  const forceButton = page.locator(".paper-detail-actions").getByRole("button", { name: "Force GROBID upgrade" });
  await expect(forceButton).toBeEnabled();
  await forceButton.click();

  await expect(page.locator(".paper-workspace-task-progress")).toContainText("Running GROBID...");
  await expect(page.locator(".paper-workspace-notice")).toContainText("Extraction ready", { timeout: 8_000 });
  expect(sawForceOverride).toBe(true);
});

test("8502 Paper Library screenshot smoke covers desktop laptop and narrow layouts", async ({ page }, testInfo) => {
  const cases = [
    {
      name: "desktop-pdf-ready",
      viewport: { width: 1440, height: 1000 },
      params: { detail_id: "source:e2e:pdf-ready" },
      sourceId: "source:e2e:pdf-ready",
    },
    {
      name: "laptop-chinese-no-pdf",
      viewport: { width: 1280, height: 800 },
      params: { query: "中文标题", detail_id: "source:e2e:no-pdf" },
      sourceId: "source:e2e:no-pdf",
    },
    {
      name: "mobile-many-badges",
      viewport: { width: 390, height: 844 },
      params: { query: "Badge Saturation", detail_id: "source:e2e:many-badges-a" },
      sourceId: "source:e2e:many-badges-a",
    },
    {
      name: "empty-collection",
      viewport: { width: 1440, height: 1000 },
      params: { node_id: "paper-node:e2e-empty" },
      empty: true,
    },
  ];

  for (const item of cases) {
    await page.setViewportSize(item.viewport);
    await openPaperLibrary(page, item.params);
    if (item.empty) {
      await expect(page.locator(".paper-list-empty")).toBeVisible();
    } else if (item.sourceId) {
      await expect(paperCard(page, item.sourceId)).toBeVisible();
      await expect(page.locator(".paper-detail-pane")).toBeVisible();
    }
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(2);
    await page.screenshot({
      path: testInfo.outputPath(`paper-library-${item.name}.png`),
      fullPage: true,
    });
  }
});
