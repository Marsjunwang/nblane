import { expect, test, type Page } from "@playwright/test";
import { SPA_BASE_URL, SPA_E2E_PROFILE } from "./spa_auth_shared";

/**
 * Real-browser journey for the 公开站点 console (route /p/:name/public-build),
 * against the isolated sandbox (`scripts/dev-web.sh --isolated`, profile=dev).
 *
 * The sandbox "live" directory is `.dev-data/dist/public/dev` — nothing is
 * served from it, so deploying there is safe. Every test restores what it
 * changes (switches, works list, visibility) through the API in `finally`.
 */

const PROFILE = SPA_E2E_PROFILE;
const API = `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/public-site`;

function spa(path: string): string {
  return `${SPA_BASE_URL}/p/${encodeURIComponent(PROFILE)}/${path}`;
}

async function overview(page: Page) {
  const res = await page.request.get(API);
  expect(res.status()).toBe(200);
  return res.json();
}

async function patchSettings(page: Page, body: Record<string, unknown>) {
  const res = await page.request.patch(`${API}/settings`, { data: body });
  expect(res.status()).toBe(200);
}

test.describe("SPA 公开站点", () => {
  test("console renders intro, posts, works, live diff and a real preview", async ({ page }) => {
    await page.goto(spa("public-build"));
    await expect(page.getByRole("link", { name: "公开站点", exact: true })).toBeVisible();
    await expect(page.getByTestId("public-site-page")).toBeVisible();
    await expect(page.getByTestId("intro-card")).toBeVisible();
    await expect(page.getByTestId("posts-section")).toBeVisible();
    await expect(page.getByTestId("works-editor")).toBeVisible();
    await expect(page.getByTestId("live-summary")).not.toBeEmpty();

    // The preview iframe serves the live-content site (no drafts) by default.
    const frame = page.getByTestId("preview-frame");
    await expect(frame).toBeVisible();
    const src = await frame.getAttribute("src");
    expect(src).toContain("/public-site/preview/page");
    expect(src).toContain("include_drafts=0");
    const preview = await page.request.get(new URL(src!, SPA_BASE_URL).toString());
    expect(preview.status()).toBe(200);
    const html = await preview.text();
    expect(html).toContain("<html");
    // Projects are off by default: no 项目 nav entry on the site.
    expect(html).not.toContain('href="/projects/"');

    await page.getByTestId("preview-include-drafts").click();
    await expect(frame).toHaveAttribute("src", /include_drafts=1/);
  });

  test("display switch round-trips to public-profile.yaml", async ({ page }) => {
    const before = (await overview(page)).settings.show_email;
    try {
      await page.goto(spa("public-build"));
      const toggle = page.getByTestId("setting-show_email");
      const patched = page.waitForResponse(
        (res) => res.url().endsWith("/public-site/settings") && res.request().method() === "PATCH",
      );
      await toggle.click();
      expect((await patched).status()).toBe(200);
      await expect(toggle).toBeChecked({ checked: !before });
      expect((await overview(page)).settings.show_email).toBe(!before);
    } finally {
      await patchSettings(page, { show_email: before });
    }
  });

  test("adds a work with an embeddable video, saves, and removes it", async ({ page }) => {
    const original = await overview(page);
    const title = `作品验收 ${Date.now()}`;
    try {
      await page.goto(spa("public-build"));
      const count = original.works.length;
      await page.getByTestId("works-add").click();
      const card = page.getByTestId(`work-${count}`);
      await card.getByTestId(`work-${count}-title`).fill(title);
      await card.getByTestId(`work-${count}-video`).fill("https://www.bilibili.com/video/BV1xx411c7mD");
      await expect(card.getByTestId(`work-${count}-video-hint`)).toContainText("内嵌播放");
      await card.getByTestId(`work-${count}-add-link`).click();
      await card.getByTestId(`work-${count}-link-url-0`).fill("https://arxiv.org/abs/2401.00001");
      await card.getByTestId(`work-${count}-published`).click();

      const saved = page.waitForResponse(
        (res) => res.url().endsWith("/public-site/works") && res.request().method() === "PUT",
      );
      await page.getByTestId("works-save").click();
      expect((await saved).status()).toBe(200);
      await expect(page.getByTestId("works-save")).toHaveText("已保存");

      const after = await overview(page);
      const work = after.works.find((row: { title: string }) => row.title === title);
      expect(work).toBeTruthy();
      expect(work.video_mode).toBe("embed");
      expect(work.links).toEqual([{ label: "https://arxiv.org/abs/2401.00001", url: "https://arxiv.org/abs/2401.00001" }]);

      // The works page of the preview embeds the Bilibili player.
      const worksPage = await page.request.get(`${API}/preview/page?path=outputs/index.html&include_drafts=0`);
      expect(await worksPage.text()).toContain("player.bilibili.com/player.html?bvid=BV1xx411c7mD");
    } finally {
      const current = await overview(page);
      const kept = current.works.filter((row: { title: string }) => row.title !== title);
      await page.request.put(`${API}/works`, {
        data: { works: kept },
        headers: { "If-Match": current.works_etag },
      });
    }
  });

  test("private site blocks deploy; public site deploys and rolls back", async ({ page }) => {
    const original = await overview(page);
    try {
      await patchSettings(page, { visibility: "private" });
      await page.goto(spa("public-build"));
      await expect(page.getByTestId("site-errors")).toContainText("网站公开");
      await expect(page.getByTestId("deploy-button")).toBeDisabled();

      // Flip the site public in the UI, then deploy through the confirmation.
      await page.getByTestId("setting-visibility").click();
      await expect(page.getByTestId("site-errors")).toHaveCount(0);
      const deployButton = page.getByTestId("deploy-button");
      if (await deployButton.isEnabled()) {
        await deployButton.click();
        await expect(page.getByTestId("live-confirm")).toBeVisible();
        const deployed = page.waitForResponse(
          (res) => res.url().endsWith("/public-site/deploy") && res.request().method() === "POST",
        );
        await page.getByTestId("live-confirm-button").click();
        expect((await deployed).status()).toBe(200);
      }
      await expect(page.getByTestId("live-summary")).toHaveText("线上已是最新。");
      await expect(deployButton).toBeDisabled();

      // Rollback is offered once a previous build exists.
      const rollback = page.getByTestId("rollback-button");
      if (await rollback.isVisible()) {
        await rollback.click();
        const rolled = page.waitForResponse(
          (res) => res.url().endsWith("/public-site/rollback") && res.request().method() === "POST",
        );
        await page.getByTestId("live-confirm-button").click();
        expect((await rolled).status()).toBe(200);
      }
    } finally {
      await patchSettings(page, { visibility: original.visibility });
    }
  });
});
