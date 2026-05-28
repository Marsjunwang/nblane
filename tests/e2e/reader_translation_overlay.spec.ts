import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const readerTemplatePath = path.resolve(process.cwd(), "src/nblane/web_reader_api/templates/index.html");
const sourceId = "source:reader:geometry";

function readerHtml() {
  return fs
    .readFileSync(readerTemplatePath, "utf-8")
    .replace("{{ source_id_json|safe }}", JSON.stringify(sourceId))
    .replace("{{ reader_prefix_json|safe }}", JSON.stringify("/reader"))
    .replace("{{ reader_token_json|safe }}", JSON.stringify(""));
}

const previewDataUrl =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='100' viewBox='0 0 200 100'%3E%3Crect width='200' height='100' fill='white'/%3E%3Ctext x='20' y='32' font-size='12' fill='black'%3ESource PDF page%3C/text%3E%3C/svg%3E";

function readerPayload(withPreview = false) {
  return {
    source: { id: "source:reader:geometry", title: "Reader Geometry", metadata: { page_count: 2 } },
    settings: {
      reader_mode: "translation",
      scale_mode: "fit-width",
      initial_page: 1,
      page_count: 2,
      target_lang: "zh",
      translation_layout: "overlay",
      debug_overlay_enabled: true,
      translation_overflow_policy: "fixed-expand",
      overscan_pages: 0,
      side_panel_default: "collapsed",
    },
    compare_split_ratio: 50,
    panel_width: 340,
    page_models: [
      { page: 1, width: 200, height: 100, rotation: 0 },
      { page: 2, width: 200, height: 100, rotation: 0 },
    ],
    page_previews: withPreview
      ? [{ page: 1, width: 200, height: 100, data_url: previewDataUrl }]
      : [],
    pages: [
      { page: 1, text: "Page one source", text_hash: "page-one" },
      { page: 2, text: "Page two source", text_hash: "page-two" },
    ],
    translation_units: [
      {
        unit_id: "layout:v2:1:00001:main",
        anchor_id: "layout:v2:1:00001:main",
        scope_type: "layout",
        scope_ref: "layout:v2:1:00001:main",
        page: 1,
        order: 1,
        kind: "paragraph",
        source_text: "Main positioned text",
        source_hash: "main-hash",
        translated_text: "主译文块",
        status: "translated",
        translatable: true,
        font_size: 10,
        line_count: 1,
        rects: [{ x_pct: 0.1, y_pct: 0.2, w_pct: 0.5, h_pct: 0.3, page_width: 200, page_height: 100 }],
      },
      {
        unit_id: "layout:v2:1:00002:long",
        anchor_id: "layout:v2:1:00002:long",
        scope_type: "layout",
        scope_ref: "layout:v2:1:00002:long",
        page: 1,
        order: 2,
        kind: "paragraph",
        source_text: "Long positioned text",
        source_hash: "long-hash",
        translated_text: "这是一个非常非常长的中文译文块用于触发溢出状态并打开全文查看入口",
        status: "translated",
        translatable: true,
        font_size: 8,
        line_count: 1,
        rects: [{ x: 20, y: 68, w: 24, h: 7, page_width: 200, page_height: 100 }],
      },
      {
        unit_id: "layout:v2:1:00003:figure-label",
        anchor_id: "layout:v2:1:00003:figure-label",
        scope_type: "layout",
        scope_ref: "layout:v2:1:00003:figure-label",
        page: 1,
        order: 3,
        kind: "figure_label",
        source_text: "AXIS LABEL",
        source_hash: "axis-hash",
        translated_text: "旧图内译文不应覆盖",
        status: "translated",
        translatable: false,
        display_source: false,
        rects: [{ x_pct: 0.7, y_pct: 0.5, w_pct: 0.2, h_pct: 0.1, page_width: 200, page_height: 100 }],
      },
      {
        unit_id: "segment:page-one-flow",
        anchor_id: "segment:page-one-flow",
        scope_type: "segment",
        scope_ref: "page-one-flow",
        segment_id: "page-one-flow",
        page: 1,
        order: 4,
        kind: "paragraph",
        source_text: "Fallback source paragraph",
        source_hash: "flow-hash",
        translated_text: "普通译文流",
        status: "translated",
        rects: [],
      },
      {
        unit_id: "layout:v2:2:00001:second",
        anchor_id: "layout:v2:2:00001:second",
        scope_type: "layout",
        scope_ref: "layout:v2:2:00001:second",
        page: 2,
        order: 1,
        kind: "paragraph",
        source_text: "Second page text",
        source_hash: "second-hash",
        translated_text: "第二页译文",
        status: "translated",
        translatable: true,
        rects: [{ x_pct: 0.1, y_pct: 0.1, w_pct: 0.5, h_pct: 0.2, page_width: 200, page_height: 100 }],
      },
    ],
    context_window: { pages: [1, 2], total_pages: 2 },
    translations: [],
    annotations: [],
    chunks: [],
    citations: [],
    claims: [],
    analysis: {},
  };
}

async function renderReader(page, payload) {
  await page.route("**/reader/api/**/payload**", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify(payload) });
  });
  await page.route("**/reader/api/**/page-preview/**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ page: 1, width: 200, height: 100, data_url: previewDataUrl }),
    });
  });
  await page.route("**/reader/api/**/page-text-layer/**", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify({ spans: [] }) });
  });
  await page.route("**/reader/api/**/progress**", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify({ ok: true }) });
  });
  await page.route("**/reader/assets/pdf.min.js", async (route) => {
    await route.fulfill({ contentType: "application/javascript", body: "" });
  });
  await page.setContent(readerHtml(), { waitUntil: "domcontentloaded" });
  await expect(page.locator(".pr-translation-page")).toBeVisible();
  await expect(page.locator('.pr-translation-block.placed[data-anchor-id="layout:v2:1:00001:main"]')).toBeVisible();
}

async function measuredBox(page, selector) {
  let latest = null;
  await expect
    .poll(async () => {
      const box = await page.locator(selector).first().boundingBox();
      if (box && box.width > 0 && box.height > 0) latest = box;
      return latest ? "ready" : "";
    })
    .toBe("ready");
  if (!latest) throw new Error(`No visible box for ${selector}`);
  return latest;
}

test("debug translation overlay uses stable page geometry", async ({ page }) => {
  await page.setViewportSize({ width: 1000, height: 760 });
  await renderReader(page, readerPayload(false));

  await expect(page.locator(".pr-translation-page")).toHaveCount(1);
  await expect(page.locator('[data-anchor-id="layout:v2:2:00001:second"]')).toHaveCount(0);
  await expect(page.locator('[data-anchor-id="layout:v2:1:00003:figure-label"]')).toHaveCount(0);
  await expect(page.locator(".pr-translation-fallback")).toContainText("普通译文流");

  const bodyScroll = await page.locator(".pr-translation-body").evaluate((element) => ({
    clientWidth: element.clientWidth,
    scrollWidth: element.scrollWidth,
  }));
  expect(bodyScroll.scrollWidth).toBeLessThanOrEqual(bodyScroll.clientWidth + 1);

  const pageBox = await measuredBox(page, ".pr-translation-page");
  const blockBox = await measuredBox(page, '.pr-translation-block.placed[data-anchor-id="layout:v2:1:00001:main"]');

  expect(Math.abs(blockBox.x - (pageBox.x + pageBox.width * 0.1))).toBeLessThanOrEqual(3);
  expect(Math.abs(blockBox.y - (pageBox.y + pageBox.height * 0.2))).toBeLessThanOrEqual(3);
  expect(Math.abs(blockBox.width - pageBox.width * 0.5)).toBeLessThanOrEqual(3);
  expect(Math.abs(blockBox.height - pageBox.height * 0.3)).toBeLessThanOrEqual(3);

  await expect(page.locator('.pr-translation-block.placed[data-anchor-id="layout:v2:1:00002:long"]')).toHaveClass(
    /overflowing/,
  );
});

test("late page preview does not move placed overlay blocks", async ({ page }) => {
  await page.setViewportSize({ width: 1000, height: 760 });
  await renderReader(page, readerPayload(false));
  const before = await measuredBox(page, '.pr-translation-block.placed[data-anchor-id="layout:v2:1:00001:main"]');

  await page.evaluate((args) => {
    return (window as any).onRender({ data: { args } });
  }, readerPayload(true));
  await expect(page.locator(".pr-translation-page-preview")).toBeVisible();

  const after = await measuredBox(page, '.pr-translation-block.placed[data-anchor-id="layout:v2:1:00001:main"]');

  expect(Math.abs(after.x - before.x)).toBeLessThanOrEqual(1);
  expect(Math.abs(after.y - before.y)).toBeLessThanOrEqual(1);
  expect(Math.abs(after.width - before.width)).toBeLessThanOrEqual(1);
  expect(Math.abs(after.height - before.height)).toBeLessThanOrEqual(1);
});

test("side panel resize rail matches compare divider and spans workspace", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 900 });
  const payload = readerPayload(false);
  payload.settings = { ...payload.settings, reader_mode: "compare", side_panel_default: "open" };
  await renderReader(page, payload);

  const workspaceBox = await measuredBox(page, ".pr-workspace");
  const compareBox = await measuredBox(page, "#compareDivider");
  const panelBox = await measuredBox(page, "#panelResize");

  expect(Math.abs(compareBox.height - workspaceBox.height)).toBeLessThanOrEqual(1);
  expect(Math.abs(panelBox.height - workspaceBox.height)).toBeLessThanOrEqual(1);
  expect(panelBox.width).toBeGreaterThanOrEqual(7);
  expect(panelBox.width).toBeLessThanOrEqual(9);

  const panelStyle = await page.locator("#panelResize").evaluate((element) => {
    const style = window.getComputedStyle(element);
    return {
      backgroundImage: style.backgroundImage,
      cursor: style.cursor,
      touchAction: style.touchAction,
    };
  });
  expect(panelStyle.backgroundImage).toContain("linear-gradient");
  expect(panelStyle.cursor).toBe("col-resize");
  expect(panelStyle.touchAction).toBe("none");
});

test("pdf reader creates a bounded page window on first render", async ({ page }) => {
  const payload = readerPayload(false);
  payload.settings.reader_mode = "pdf";
  payload.settings.translation_layout = "flow";
  payload.settings.debug_overlay_enabled = false;
  payload.settings.overscan_pages = 1;
  payload.settings.page_count = 36;
  payload.source.metadata.page_count = 36;
  payload.context_window = { pages: [1, 2], total_pages: 36 };

  await page.setViewportSize({ width: 1200, height: 760 });
  await page.route("**/reader/api/**/payload**", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify(payload) });
  });
  await page.route("**/reader/api/**/page-preview/**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ page: 1, width: 200, height: 100, data_url: previewDataUrl }),
    });
  });
  await page.route("**/reader/api/**/page-text-layer/**", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify({ spans: [] }) });
  });
  await page.route("**/reader/assets/pdf.min.js", async (route) => {
    await route.fulfill({ contentType: "application/javascript", body: "" });
  });
  await page.setContent(readerHtml(), { waitUntil: "domcontentloaded" });

  await expect(page.locator(".pr-page-container")).toHaveCount(3);
  await expect(page.locator('[data-spacer="after"]')).toBeVisible();
  await expect(page.locator("canvas")).toHaveCount(3);
});

test("translation progress bar reflects actionState and fades out", async ({ page }) => {
  await page.setViewportSize({ width: 1200, height: 760 });
  await renderReader(page, readerPayload(false));

  await page.evaluate(() => {
    (window as any).setActionState("translate_full_paper", "pending", "Translating", {
      progress: { batches: 4, batches_completed: 1 },
    });
  });
  await expect(page.locator("#translationProgressShell")).toHaveClass(/visible/);
  await expect(page.locator("#translationProgressLabel")).toHaveText("25%");

  await page.evaluate(() => {
    (window as any).setActionState("translate_full_paper", "pending", "Translating", {
      progress: { batches: 4, batches_completed: 4 },
    });
  });
  await expect(page.locator("#translationProgressLabel")).toHaveText("100%");

  await page.evaluate(() => {
    (window as any).setActionState("translate_full_paper", "done", "", {
      progress: { batches: 4, batches_completed: 4 },
    });
  });
  await expect(page.locator("#translationProgressShell")).toHaveClass(/fading/);
});

test("bulk translations endpoint hydrates overlay across all pages", async ({ page }) => {
  const payload = readerPayload(false);
  payload.settings.reader_mode = "compare";
  payload.settings.translation_layout = "overlay";
  payload.settings.debug_overlay_enabled = true;
  payload.context_window = { pages: [1], total_pages: 2 };

  await page.setViewportSize({ width: 1200, height: 760 });

  let bulkHits = 0;
  await page.route("**/reader/api/**/translations/bulk**", async (route) => {
    bulkHits += 1;
    await route.fulfill({
      contentType: "application/json",
      headers: { ETag: 'W/"abc123"' },
      body: JSON.stringify({
        paper_id: "source:reader:geometry",
        target_lang: "zh",
        content_hash: "abc123",
        total_pages: 2,
        segment_count: 2,
        generated_at: "2026-05-26T00:00:00Z",
        segments: [
          {
            id: "tr:1",
            page: 1,
            anchor_id: "layout:v2:1:00001:main",
            scope_type: "layout",
            scope_ref: "layout:v2:1:00001:main",
            translated_text: "全文译文一",
            source_text: "Main positioned text",
            status: "translated",
            target_lang: "zh",
            font_size: 10,
            rects: [{ x: 0.1, y: 0.2, w: 0.5, h: 0.3, page: 1 }],
          },
          {
            id: "tr:2",
            page: 2,
            anchor_id: "layout:v2:2:00001:second",
            scope_type: "layout",
            scope_ref: "layout:v2:2:00001:second",
            translated_text: "全文译文二",
            source_text: "Second page text",
            status: "translated",
            target_lang: "zh",
            font_size: 10,
            rects: [{ x: 0.1, y: 0.1, w: 0.5, h: 0.2, page: 2 }],
          },
        ],
      }),
    });
  });
  await renderReader(page, payload);

  await expect.poll(() => bulkHits, { timeout: 4000 }).toBeGreaterThanOrEqual(1);
  await page.evaluate(() => (window as any).fetchTranslationsBulk({ force: true }));
  await expect(page.locator(".pr-translation-page-shell")).toHaveCount(2);
  await expect(
    page.locator('.pr-translation-page-shell[data-page-shell="2"]'),
  ).toHaveCount(1);
});
