import { test, expect } from "@playwright/test";

const READER_URL = process.env.READER_URL || "";

test.setTimeout(120_000);

async function dumpDiagnostics(page, label: string) {
  const data = await page.evaluate(() => {
    const root = document.getElementById("root");
    return {
      rootBytes: root?.innerHTML.length || 0,
      shellPresent: !!document.querySelector(".pr-shell"),
      pageContainerCount: document.querySelectorAll(".pr-page-container").length,
      canvasCount: document.querySelectorAll("canvas").length,
      translationPageCount: document.querySelectorAll(".pr-translation-page").length,
      translationBlockCount: document.querySelectorAll(".pr-translation-block").length,
      translationUnitCount: document.querySelectorAll(".pr-translation-unit").length,
      readerMode: (document.querySelector(".pr-mode .active") as HTMLElement)?.textContent || "?",
      activeLeftTab: (document.querySelector(".pr-left-rail-tab.active") as HTMLElement)?.textContent || "?",
      visibleErrorBoxes: document.querySelectorAll(".pr-error").length,
      progressBarVisible: document.querySelector("#translationProgressShell")?.classList.contains("visible") || false,
      bulkLoaded: !!(window as any).bulkTranslations?.segments?.length,
      payloadEtag: (window as any).payloadEtag || "",
      sidePanelTabs: Array.from(document.querySelectorAll(".pr-side-tab")).map((t) => (t as HTMLElement).textContent),
    };
  });
  console.log(`[${label}]`, JSON.stringify(data, null, 2));
}

test("walkthrough", async ({ page }) => {
  if (!READER_URL) test.skip();

  const errors: string[] = [];
  const networkSummary: { url: string; status: number; type: string }[] = [];
  page.on("pageerror", (err) => errors.push(`pageerror: ${err.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(`console.error: ${msg.text()}`);
  });
  page.on("response", (resp) => {
    const url = resp.url();
    if (/\/reader\/api\/.+\/(payload|translations\/bulk|page-preview|page-text-layer|tasks)/.test(url)) {
      networkSummary.push({ url: url.replace(/[?&]reader_token=[^&]+/, ""), status: resp.status(), type: resp.request().method() });
    }
  });

  // 1) Initial load (PDF mode default)
  await page.goto(READER_URL, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(
    () => (document.getElementById("root")?.innerHTML?.length || 0) > 5000,
    { timeout: 20000 },
  );
  await page.waitForTimeout(3000);  // let bulk + first 1-2 page renders settle
  await page.screenshot({ path: "/tmp/walkthrough-1-pdf-mode.png", fullPage: false });
  await dumpDiagnostics(page, "PDF mode after load");

  // 2) Switch to compare mode
  const compareBtn = page.locator('.pr-mode [data-mode="compare"]');
  if (await compareBtn.count() > 0) {
    await compareBtn.click();
    await page.waitForTimeout(2500);
    await page.screenshot({ path: "/tmp/walkthrough-2-compare-mode.png", fullPage: false });
    await dumpDiagnostics(page, "Compare mode");
  }

  // 3) Switch to translation-only mode
  const transBtn = page.locator('.pr-mode [data-mode="translation"]');
  if (await transBtn.count() > 0) {
    await transBtn.click();
    await page.waitForTimeout(2500);
    await page.screenshot({ path: "/tmp/walkthrough-3-translation-mode.png", fullPage: false });
    await dumpDiagnostics(page, "Translation-only mode");
  }

  // 4) Scroll the translation view a few pages
  await page.evaluate(() => {
    const scrollEl = document.getElementById("translationReader") || document.querySelector(".pr-translation-body");
    if (scrollEl) (scrollEl as HTMLElement).scrollBy(0, 1500);
  });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "/tmp/walkthrough-4-translation-scrolled.png", fullPage: false });

  // 5) Back to PDF mode and try the side panel "review" tab to see analyze/deep_read output
  const pdfBtn = page.locator('.pr-mode [data-mode="pdf"]');
  if (await pdfBtn.count() > 0) {
    await pdfBtn.click();
    await page.waitForTimeout(1500);
  }
  // Open side panel if collapsed
  const sideBtn = page.locator('[data-action="togglePanel"]').first();
  if (await sideBtn.count() > 0) {
    await sideBtn.click();
    await page.waitForTimeout(500);
  }
  // Click the "review" / "Analyze Paper" tab
  const reviewTab = page.locator('.pr-side-tab').filter({ hasText: /review|analy|分析/i }).first();
  if (await reviewTab.count() > 0) {
    await reviewTab.click();
    await page.waitForTimeout(800);
    await page.screenshot({ path: "/tmp/walkthrough-5-review-panel.png", fullPage: false });
    await dumpDiagnostics(page, "Review panel");
  }

  console.log("\n=== Network summary (de-tokenized) ===");
  console.log(`Total relevant requests: ${networkSummary.length}`);
  const byEndpoint: Record<string, { count: number; statuses: Record<number, number> }> = {};
  for (const r of networkSummary) {
    const key = r.url.replace(/\/api\/[^/]+\//, "/api/{src}/").replace(/\/\d+($|\?)/, "/{n}");
    byEndpoint[key] = byEndpoint[key] || { count: 0, statuses: {} };
    byEndpoint[key].count++;
    byEndpoint[key].statuses[r.status] = (byEndpoint[key].statuses[r.status] || 0) + 1;
  }
  for (const [endpoint, info] of Object.entries(byEndpoint)) {
    console.log(`  ${endpoint}: ${info.count} hits, statuses: ${JSON.stringify(info.statuses)}`);
  }
  console.log("\n=== JS errors ===");
  for (const e of errors) console.log(e);

  // Don't fail on aesthetic issues — this is a walk-through dump
  expect(errors.filter(e => !/PDF\.js|pdf\.worker/i.test(e))).toHaveLength(0);
});
