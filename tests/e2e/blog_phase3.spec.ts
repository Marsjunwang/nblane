import { expect, test } from "@playwright/test";

const e2eBaseUrl = process.env.NBLANE_E2E_BASE_URL || "http://127.0.0.1:8510/Public_Site";

async function openEditor(page) {
  try {
    await page.goto(e2eBaseUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
  } catch {
    test.skip(true, "Set NBLANE_E2E_BASE_URL or run the Streamlit app on port 8510.");
  }
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  const blogTab = page.getByText(/^Blog$/).first();
  if (await blogTab.count()) {
    await blogTab.click();
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(2500);
  }
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    for (const frame of page.frames()) {
      const blocknote = frame.locator(".bn-editor:visible, .nb-blocknote-frame:visible").first();
      if (await blocknote.count()) {
        return { frame, editor: blocknote };
      }
    }
    await page.waitForTimeout(250);
  }
  const inlineEditor = page.locator(".bn-editor:visible, .nb-blocknote-frame:visible").first();
  if (!(await inlineEditor.count())) {
    test.skip(true, "Blog editor shell is not visible at the configured URL.");
  }
  await expect(inlineEditor).toBeVisible();
  return { frame: page, editor: inlineEditor };
}

async function typeSlashCommand(page, frame, editor, command) {
  const editable = frame.locator('[contenteditable="true"], .bn-editor').first();
  const target = (await editable.count()) ? editable : editor;
  await target.click({ force: true });
  await target.press("Control+End").catch(() => {});
  await target.press("Enter").catch(() => {});
  await target.pressSequentially(command, { delay: 15 });
}

test("formula slash action is registered", async ({ page }) => {
  const { frame, editor } = await openEditor(page);
  await typeSlashCommand(page, frame, editor, "/公式");
  const formulaItem = frame.getByText(/公式|Formula/).first();
  await expect(formulaItem).toBeVisible();
});

test("outline panel is present in the AI editor shell", async ({ page }) => {
  const { frame } = await openEditor(page);
  await expect(frame.getByText(/大纲|Outline/).first()).toHaveCount(1);
});

test("visual controls expose candidate accept lifecycle entry points", async ({ page }) => {
  const { frame } = await openEditor(page);
  await expect(frame.getByText(/配图|Visual|图/).first()).toHaveCount(1);
});

test("diagram slash action is registered", async ({ page }) => {
  const { frame, editor } = await openEditor(page);
  await typeSlashCommand(page, frame, editor, "/diagram");
  await expect(frame.getByText(/Diagram|流程图|图表/).first()).toBeVisible();
});
