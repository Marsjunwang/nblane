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
  const searchInput = page.locator(".paper-workspace-controls input");
  await searchInput.fill("超长中文论文标题");
  await searchInput.press("Enter");
  await expect.poll(async () => new URL(page.url()).searchParams.get("query") || "").toBe("超长中文论文标题");
  await expect(paperCard(page, "source:e2e:no-pdf")).toBeVisible();
  await expect(page.locator(".paper-list-card")).toHaveCount(1);
  await searchInput.fill("");
  await searchInput.press("Enter");
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
