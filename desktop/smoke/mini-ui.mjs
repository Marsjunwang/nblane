import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdir, mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { _electron, expect as baseExpect } from '@playwright/test';
import { fixtureCredentials, startMiniFixture } from './mini-fixture.mjs';
import { createNativeInput } from './native-input.mjs';

const expect = baseExpect.configure({ timeout: 15_000 });
const desktop = fileURLToPath(new URL('../', import.meta.url));
const options = process.argv.slice(2);
if (options.length > 1 || (options.length === 1 && !options[0].startsWith('--app='))) {
  throw new Error('Usage: node desktop/smoke/mini-ui.mjs [--app=/absolute/path/to/App.app]');
}
const packagedApp = options[0]?.slice('--app='.length);
let executablePath = path.join(desktop, 'node_modules/.bin/electron');
if (packagedApp !== undefined) {
  if (process.platform !== 'darwin' || !path.isAbsolute(packagedApp) || !packagedApp.endsWith('.app')) {
    throw new Error('--app requires an absolute macOS .app path on macOS.');
  }
  const executable = execFileSync('/usr/libexec/PlistBuddy', [
    '-c', 'Print :CFBundleExecutable', path.join(packagedApp, 'Contents/Info.plist'),
  ], { encoding: 'utf8' }).trim();
  assert.ok(executable && path.basename(executable) === executable, 'Invalid CFBundleExecutable');
  executablePath = path.join(packagedApp, 'Contents/MacOS', executable);
}
const args = packagedApp === undefined ? [desktop] : [];
if (process.platform === 'linux' && process.env.NBLANE_STICKER_SMOKE_XVFB === '1') {
  // Only this disposable fixture process uses these flags.
  args.unshift('--no-sandbox', '--disable-gpu');
}
const data = await mkdtemp(path.join(tmpdir(), 'nblane-sticker-mini-ui-'));
const fixture = await startMiniFixture();
const screenshots = process.env.NBLANE_STICKER_SCREENSHOT_DIR;
const pageErrors = [];
let application;
let toolbar;
let controls;
let remote;
const deadline = setTimeout(() => {
  application?.process().kill('SIGKILL');
  fixture.server.closeAllConnections();
}, 180_000);

const getState = () => toolbar.evaluate(() => window.nblaneSticker.invoke('get-state'));
const windowBounds = () => application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].getBounds());
const windowHeight = async () => (await windowBounds()).height;
const controlsVisible = () => application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0]
  .contentView.children.find((view) => view.webContents?.getURL().includes('?controls=1')).getVisible());

async function findPage(predicate) {
  let found;
  await expect.poll(() => {
    found = application.windows().find((page) => {
      // A newly created remote view briefly has an empty URL during refresh.
      // Keep polling until navigation begins instead of failing the smoke.
      const url = page.url();
      return !page.isClosed() && URL.canParse(url) && predicate(new URL(url), page);
    });
    return Boolean(found);
  }).toBe(true);
  found.setDefaultTimeout(15_000);
  found.on('pageerror', (error) => pageErrors.push(error.message));
  return found;
}

async function waitForMini(previous) {
  remote = await findPage((url, page) => page !== previous && url.origin === fixture.origin && url.pathname.endsWith('/mini'));
  await expect(remote.locator('[data-sticker-root]')).toBeVisible();
  await expect.poll(async () => (await getState()).integratedContent).toBe(true);
  await expect.poll(async () => Number(await remote.locator('[data-sticker-root]').getAttribute('data-sticker-height'))).toBeGreaterThan(0);
}

async function nativeMenuAction(label) {
  await controls.getByRole('button', { name: '更多操作', exact: true }).click();
  await application.evaluate((_, text) => {
    const item = globalThis.__miniSmokeMenu.items.find((entry) => entry.label === text);
    if (!item) throw new Error(`Missing native menu action: ${text}`);
    item.click();
  }, label);
}

async function reloadFixture() {
  const previous = remote;
  await nativeMenuAction('刷新任务');
  await waitForMini(previous);
}

async function capture(name) {
  if (!screenshots) return;
  await mkdir(screenshots, { recursive: true });
  // WebContents captures exclude native vibrancy and are intentionally separate.
  await remote.screenshot({ path: path.join(screenshots, `${name}-remote.png`), omitBackground: true });
  if (await controlsVisible()) await controls.screenshot({ path: path.join(screenshots, `${name}-controls.png`), omitBackground: true });
  if (process.platform === 'linux' && process.env.NBLANE_STICKER_SMOKE_XVFB === '1') {
    const bounds = await windowBounds();
    try {
      // Optional X11 capture includes the actual child-view composition. The
      // Linux opaque fallback does not demonstrate macOS native vibrancy.
      execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-f', 'x11grab',
        '-video_size', `${bounds.width}x${bounds.height}`,
        '-i', `${process.env.DISPLAY}+${bounds.x},${bounds.y}`, '-frames:v', '1', '-y',
        path.join(screenshots, `${name}-window.png`)], { timeout: 8_000, stdio: 'pipe' });
    } catch (error) {
      console.warn(`Optional X11 composite capture unavailable (${error.code ?? 'capture failed'}).`);
    }
  }
}

try {
  application = await _electron.launch({
    executablePath, args, env: { ...process.env, NBLANE_STICKER_USER_DATA: data }, timeout: 30_000,
  });
  if (packagedApp !== undefined) assert.equal(await application.evaluate(({ app }) => app.isPackaged), true);
  toolbar = await findPage((url) => url.protocol === 'file:' && url.pathname.endsWith('/renderer/index.html') && !url.search);
  await toolbar.locator('#server-url').fill(fixture.origin);
  await toolbar.locator('#profile').fill('demo');
  await toolbar.locator('#save-settings').click();

  remote = await findPage((url) => url.origin === fixture.origin);
  await expect(remote).toHaveURL(`${fixture.origin}/login`);
  await expect(remote.getByRole('heading', { name: 'nblane 登录' })).toBeVisible();
  await expect.poll(async () => (await getState()).loading).toBe(false);
  assert.equal((await getState()).integratedContent, false, 'Login must not be treated as the compact task page');
  assert.equal(fixture.state.loginCount, 0, 'The fixture must begin unauthenticated');
  await remote.getByLabel(/^用户名/).fill(fixtureCredentials.username);
  await remote.getByLabel(/^密码/).fill(fixtureCredentials.password);
  await remote.getByRole('button', { name: '登录', exact: true }).click();
  await expect(remote).toHaveURL(`${fixture.origin}/p/demo/mini?sticker=1&toolbar=full&refresh=60`);
  await waitForMini();
  assert.equal(fixture.state.loginCount, 1, 'The real SPA login mutation must succeed');
  controls = await findPage((url) => url.protocol === 'file:' && url.searchParams.get('controls') === '1');

  await expect(remote.locator('.mini-toolbar')).toHaveCount(1);
  await expect(toolbar.locator('.toolbar')).toBeHidden();
  await expect(controls.locator('.toolbar button:visible')).toHaveCount(6);
  await expect(remote.getByRole('button', { name: '刷新', exact: true })).toHaveCount(0);
  await expect(remote.getByRole('link', { name: '在完整页面打开' })).toHaveCount(0);
  await expect(remote.getByRole('button', { name: '打卡：阅读', exact: true })).toBeVisible();
  await expect(remote.getByRole('button', { name: '打卡：日课', exact: true })).toBeVisible();
  await expect(remote.getByText('进行中 · 1', { exact: true })).toBeVisible();
  await expect(remote.getByText('接下来 · 0', { exact: true })).toBeVisible();
  assert.equal(/\b(?:Queue|Doing)\b/.test(await remote.locator('body').innerText()), false);
  const header = await remote.locator('.mini-toolbar').evaluate((element) => ({
    height: element.getBoundingClientRect().height,
    reserved: innerWidth - element.getBoundingClientRect().right,
  }));
  assert.deepEqual(header, { height: 44, reserved: 216 });
  await expect.poll(windowHeight).toBeLessThanOrEqual(200);
  const compactHeight = await windowHeight();
  assert.ok(compactHeight >= 156);
  const naturalHeight = Number(await remote.locator('[data-sticker-root]').getAttribute('data-sticker-height'));
  assert.equal(compactHeight, Math.max(156, naturalHeight));
  await capture('mini-compact');

  await remote.getByRole('button', { name: '展开清单：探索 ai native 的工作方式', exact: true }).click();
  await expect(remote.getByRole('checkbox', { name: '记录下一步尝试' })).toBeVisible();
  await expect.poll(windowHeight).toBeGreaterThan(compactHeight);
  await capture('mini-expanded');
  await remote.getByRole('button', { name: '收起清单：探索 ai native 的工作方式', exact: true }).click();
  await expect.poll(windowHeight).toBe(compactHeight);

  // CDP clicks target a renderer directly and miss sibling-view drag-region
  // interception. Exercise the actual OS pointer and real popup first.
  const nativeInput = createNativeInput(data);
  const clickNativeControl = async (selector) => {
    const button = await controls.locator(selector).boundingBox();
    assert.ok(button);
    const bounds = await application.evaluate(({ app, BrowserWindow }) => {
      const window = BrowserWindow.getAllWindows()[0];
      app.focus({ steal: true });
      window.focus();
      const view = window.contentView.children.find((child) => child.webContents?.getURL().includes("?controls=1"));
      return { window: window.getContentBounds(), view: view.getBounds() };
    });
    nativeInput.click(bounds.window.x + bounds.view.x + button.x + button.width / 2,
      bounds.window.y + bounds.view.y + button.y + button.height / 2);
  };
  const pinned = (await getState()).settings.alwaysOnTop;
  await clickNativeControl('#pin-button');
  await expect.poll(async () => (await getState()).settings.alwaysOnTop).toBe(!pinned);
  await clickNativeControl('#pin-button');
  await expect.poll(async () => (await getState()).settings.alwaysOnTop).toBe(pinned);

  await application.evaluate(({ Menu }) => {
    const originalPopup = Menu.prototype.popup;
    globalThis.__nativeMenuLifecycle = { shown: 0, closed: 0 };
    Menu.prototype.popup = function (options) {
      this.once('menu-will-show', () => { globalThis.__nativeMenuLifecycle.shown += 1; });
      this.once('menu-will-close', () => { globalThis.__nativeMenuLifecycle.closed += 1; });
      return originalPopup.call(this, options);
    };
  });
  for (let opening = 1; opening <= 2; opening += 1) {
    await clickNativeControl('#more-button');
    await expect.poll(async () => (await getState()).menuOpen).toBe(true);
    await expect.poll(() => application.evaluate(() => globalThis.__nativeMenuLifecycle.shown)).toBe(opening);
    nativeInput.escape();
    await expect.poll(async () => (await getState()).menuOpen).toBe(false);
    await expect.poll(() => application.evaluate(() => globalThis.__nativeMenuLifecycle.closed)).toBe(opening);
  }

  await clickNativeControl('#opacity-button');
  await expect.poll(async () => (await getState()).opacityEditor).toBe(true);
  await expect(controls.locator('#toolbar-opacity-range')).toBeVisible();
  await controls.locator('#toolbar-opacity-range').evaluate((input) => {
    input.value = '10';
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await expect.poll(async () => (await getState()).settings.opacity).toBe(0.1);
  nativeInput.escape();
  await expect.poll(async () => (await getState()).opacityEditor).toBe(false);
  await expect(controls.locator('#toolbar-opacity-range')).toBeHidden();
  await clickNativeControl(90);
  await expect(toolbar.locator('#settings-screen')).toBeVisible();
  await expect(toolbar.locator('#settings-opacity-range')).toHaveValue('10');
  await expect(toolbar.locator('#refresh-button')).toBeDisabled();
  await toolbar.locator('#opacity-button').click();
  await expect.poll(async () => (await getState()).opacityEditor).toBe(true);
  await expect(controls.locator('#toolbar-opacity-range')).toBeVisible();
  await expect(toolbar.locator('#toolbar-opacity-range')).toBeHidden();
  await toolbar.locator('#profile').click();
  await expect.poll(async () => (await getState()).opacityEditor).toBe(false);
  await toolbar.locator('#refresh-interval').selectOption('30');
  const beforeSettingsSave = remote;
  await toolbar.locator('#save-settings').click();
  await waitForMini(beforeSettingsSave);
  assert.equal((await getState()).settings.refreshIntervalSeconds, 30);
  assert.equal(new URL(remote.url()).searchParams.get('refresh'), '30');
  const beforeRefresh = remote;
  await clickNativeControl(162);
  await waitForMini(beforeRefresh);

  await application.evaluate(({ Menu, shell }) => {
    // Native presentation was tested above. Inspect later actions without
    // depending on platform-specific menu row positions or fonts.
    Menu.prototype.popup = function (options) {
      globalThis.__miniSmokeMenu = this;
      options?.callback?.();
    };
    shell.openExternal = async (url) => { globalThis.__miniSmokeExternal = url; };
  });
  await nativeMenuAction('在浏览器打开');
  assert.equal(await application.evaluate(() => globalThis.__miniSmokeExternal), `${fixture.origin}/p/demo/projects`);
  await nativeMenuAction('贴纸设置…');
  await toolbar.locator('#settings-opacity-range').evaluate((input) => {
    input.value = '65';
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await expect.poll(async () => (await getState()).settings.opacity).toBe(0.65);
  const material = await getState();
  assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].getOpacity()), 1);
  assert.equal(material.effectiveOpacity, material.nativeTransparency && !material.reducedTransparency ? 0.65 : 1);
  const hostAlpha = await toolbar.locator('body').evaluate(() => {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    context.fillStyle = getComputedStyle(document.body).backgroundColor;
    context.fillRect(0, 0, 1, 1);
    return context.getImageData(0, 0, 1, 1).data[3] / 255;
  });
  assert.ok(Math.abs(hostAlpha - material.effectiveOpacity) < 0.01, 'Only the painted host background receives alpha');
  await toolbar.locator('#cancel-settings').click();
  await expect.poll(async () => (await getState()).integratedContent).toBe(true);
  const textStyle = await remote.locator('.mini-task-title').first().evaluate((title) => {
    const style = getComputedStyle(title);
    const opacities = [];
    for (let node = title; node; node = node.parentElement) opacities.push(getComputedStyle(node).opacity);
    return { font: style.fontFamily, size: style.fontSize, weight: style.fontWeight, opacities,
      backgrounds: [document.documentElement, document.body, document.getElementById('root')]
        .map((element) => getComputedStyle(element).backgroundColor) };
  });
  assert.match(textStyle.font, /-apple-system|BlinkMacSystemFont|PingFang/);
  assert.equal(textStyle.size, '14px');
  assert.equal(textStyle.weight, '500');
  assert.ok(textStyle.opacities.every((opacity) => opacity === '1'), 'Every task text ancestor must remain opaque');
  assert.ok(textStyle.backgrounds.every((color) => color === 'rgba(0, 0, 0, 0)'), 'The remote page must expose the native background');

  await remote.getByRole('button', { name: '打卡：日课', exact: true }).click();
  await expect(remote.getByRole('menuitem', { name: '日课计划二', exact: true })).toBeVisible();
  await expect.poll(controlsVisible).toBe(false);
  await expect.poll(windowHeight).toBeGreaterThanOrEqual(420);
  await remote.getByRole('menuitem', { name: '日课计划二', exact: true }).click();
  await expect.poll(() => fixture.state.checkins.length).toBe(1);
  assert.equal(fixture.state.checkins[0].plan_id, 'p2');
  assert.equal(fixture.state.checkins[0].habit, 'exercise');
  await expect(remote.getByRole('button', { name: '已打卡：日课', exact: true })).toBeVisible();
  await expect.poll(controlsVisible).toBe(true);
  await expect.poll(windowHeight).toBe(compactHeight);

  fixture.state.exceptionCount = 1;
  await reloadFixture();
  await remote.getByRole('button', { name: 'AI 异常 1 条', exact: true }).click();
  await expect(remote.getByRole('dialog')).toBeVisible();
  await expect.poll(controlsVisible).toBe(false);
  await expect.poll(windowHeight).toBeGreaterThanOrEqual(420);
  await remote.locator('.mantine-Drawer-close').click();
  await expect(remote.getByRole('dialog')).toBeHidden();
  await expect.poll(controlsVisible).toBe(true);
  await expect.poll(windowHeight).toBe(compactHeight);

  fixture.state.exceptionCount = 0;
  fixture.state.taskCount = 20;
  await reloadFixture();
  await expect(remote.locator('.mini-task-title')).toHaveCount(20);
  await expect.poll(windowHeight).toBeGreaterThan(compactHeight);
  assert.ok(await windowHeight() <= 560);
  const scroll = remote.locator('[data-sticker-scroll]');
  assert.equal(await scroll.evaluate((element) => element.scrollHeight > element.clientHeight), true);
  await scroll.evaluate((element) => { element.scrollTop = element.scrollHeight; });
  assert.ok(await scroll.evaluate((element) => element.scrollTop) > 0, 'Long content must actually scroll');
  await expect(remote.getByText('记录下一项任务 20', { exact: true })).toBeInViewport();

  fixture.state.taskCount = 1;
  fixture.state.longTitle = true;
  await reloadFixture();
  await application.evaluate(({ BrowserWindow }) => {
    const window = BrowserWindow.getAllWindows()[0];
    window.setSize(280, window.getBounds().height);
  });
  await expect.poll(async () => (await windowBounds()).width).toBe(280);
  const geometry = await remote.locator('.mini-row').first().evaluate((row) => {
    const title = row.querySelector('.mini-task-title');
    const progress = row.querySelector('.mini-progress').getBoundingClientRect();
    const complete = row.querySelector('.mini-complete').getBoundingClientRect();
    return {
      pageOverflow: document.documentElement.scrollWidth > innerWidth,
      rowOverflow: row.scrollWidth > row.clientWidth,
      titleHeight: title.getBoundingClientRect().height, titleLineHeight: parseFloat(getComputedStyle(title).lineHeight),
      progressGap: complete.left - progress.right,
      centerOffset: Math.abs((complete.top + complete.bottom - progress.top - progress.bottom) / 2),
      completionRight: complete.right, width: innerWidth,
      headerWrap: getComputedStyle(document.querySelector('.mini-toolbar')).flexWrap,
    };
  });
  assert.equal(geometry.pageOverflow, false);
  assert.equal(geometry.rowOverflow, false);
  assert.equal(geometry.headerWrap, 'nowrap');
  assert.ok(geometry.titleHeight > geometry.titleLineHeight, 'Long task titles must wrap at 280px');
  assert.ok(geometry.progressGap >= 0 && geometry.progressGap <= 8, 'Progress must sit next to completion');
  assert.ok(geometry.centerOffset <= 1, 'Progress and completion must align vertically');
  assert.ok(geometry.completionRight <= geometry.width);
  await capture('mini-narrow');

  const security = await application.evaluate(async ({ webContents }, origin) => {
    const view = webContents.getAllWebContents().find((contents) => contents.getURL().startsWith(origin));
    const preferences = view.getLastWebPreferences();
    return {
      nodeIntegration: preferences.nodeIntegration, contextIsolation: preferences.contextIsolation, sandbox: preferences.sandbox,
      globals: await view.executeJavaScript('({ bridge: typeof window.nblaneSticker, node: typeof require })'),
    };
  }, fixture.origin);
  assert.deepEqual(security, {
    nodeIntegration: false, contextIsolation: true, sandbox: true,
    globals: { bridge: 'undefined', node: 'undefined' },
  });
  await remote.emulateMedia({ reducedMotion: 'reduce' });
  assert.equal(await remote.locator('.mini-row').first().evaluate((element) => getComputedStyle(element).transitionDuration), '0s');
  assert.deepEqual(pageErrors, []);
  console.log('Actual SPA + Electron smoke passed: native pointer pin/More clicks, real popup open/Escape/reopen, fresh login preserves sticker mode, single toolbar, adaptive height, opaque system text, background alpha, scroll, plan menu, drawer, narrow layout and remote isolation.');
} catch (error) {
  console.error('Mini UI smoke diagnostic:', {
    remoteUrl: remote?.url(), pageErrors,
    host: toolbar && !toolbar.isClosed() ? await getState().catch(() => null) : null,
    page: remote && !remote.isClosed() ? await remote.locator('body').innerText({ timeout: 1_000 }).catch(() => '') : '',
  });
  throw error;
} finally {
  clearTimeout(deadline);
  if (application) await application.close().catch(() => {});
  await fixture.close();
  await rm(data, { recursive: true, force: true });
}
