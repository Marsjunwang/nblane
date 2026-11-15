import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { _electron, expect } from '@playwright/test';

const desktop = fileURLToPath(new URL('../', import.meta.url));
const options = process.argv.slice(2);
if (options.length > 1 || (options.length === 1 && !options[0].startsWith('--app='))) {
  throw new Error('Usage: npm run test:smoke -- [--app=/absolute/path/to/App.app]');
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
const data = await mkdtemp(path.join(tmpdir(), 'nblane-sticker-smoke-'));
const pendingResponses = new Set();
const server = createServer((request, response) => {
  if (request.url === '/pending-image' || request.url.startsWith('/p/no-response/')) {
    pendingResponses.add(response);
    response.on('close', () => pendingResponses.delete(response));
    return;
  }
  if (request.url.startsWith('/p/blocked-redirect/')) {
    response.writeHead(302, { Location: 'https://example.invalid/' });
    response.end();
    return;
  }
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  response.end('<!doctype html><title>Isolated sticker fixture</title><style>html,body{background:transparent;color:#f2ede0;margin:0;font:14px system-ui}header{height:44px;padding-right:88px}</style><main data-sticker-root data-sticker-height=180><header>演示档案</header><p>任务测试页面</p></main>'
    + (request.url.startsWith('/p/slow-image/') ? '<img src="/pending-image" alt="Pending image">' : ''));
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const args = packagedApp === undefined ? [desktop] : [];
if (process.platform === 'linux' && process.env.NBLANE_STICKER_SMOKE_XVFB === '1') {
  // Only the disposable fixture process uses these flags; the app never sets them.
  args.unshift('--no-sandbox', '--disable-gpu');
}
let application;

async function launch() {
  application = await _electron.launch({
    executablePath, args,
    env: { ...process.env, NBLANE_STICKER_USER_DATA: data }, timeout: 30_000,
  });
  if (packagedApp !== undefined) {
    assert.equal(await application.evaluate(({ app }) => app.isPackaged), true, 'Smoke must run the packaged app');
  }
  // The remote WebContentsView can appear before the local toolbar on relaunch.
  let toolbar;
  await expect.poll(() => {
    toolbar = application.windows().find((page) => {
      try {
        const url = new URL(page.url());
        return url.protocol === 'file:' && url.pathname.endsWith('/renderer/index.html') && !url.search;
      } catch {
        return false;
      }
    });
    return Boolean(toolbar);
  }, { message: 'The local sticker toolbar must load', timeout: 30_000 }).toBe(true);
  return toolbar;
}

async function getState(toolbar) {
  return toolbar.evaluate(() => window.nblaneSticker.invoke('get-state'));
}

try {
  let toolbar = await launch();
  await expect(toolbar.locator('#settings-screen')).toBeVisible();
  await expect(toolbar.getByRole('switch', { name: '始终置顶' })).toBeChecked();
  await expect(toolbar.getByRole('button', { name: '始终置顶', exact: true })).toHaveAttribute('aria-pressed', 'true');
  if (process.platform === 'darwin') {
    assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].isAlwaysOnTop()), true);
  }
  await toolbar.locator('#server-url').fill(origin);
  await toolbar.locator('#profile').fill('smoke-profile');
  await toolbar.locator('#refresh-interval').selectOption('30');
  await toolbar.locator('#save-settings').click();
  await expect.poll(async () => (await getState(toolbar)).loading).toBe(false);
  assert.equal((await getState(toolbar)).error, null);
  assert.equal((await getState(toolbar)).screen, 'content');
  const remoteSecurity = await application.evaluate(async ({ webContents }, expectedOrigin) => {
    const remote = webContents.getAllWebContents().find((contents) => contents.getURL().startsWith(expectedOrigin));
    if (!remote) throw new Error('Remote fixture did not load');
    const preferences = remote.getLastWebPreferences();
    return {
      preferences: { nodeIntegration: preferences.nodeIntegration, contextIsolation: preferences.contextIsolation, sandbox: preferences.sandbox },
      bridge: await remote.executeJavaScript('({bridge: typeof window.nblaneSticker, node: typeof require})'),
    };
  }, origin);
  assert.deepEqual(remoteSecurity.bridge, { bridge: 'undefined', node: 'undefined' });
  assert.equal(remoteSecurity.preferences.nodeIntegration, false);
  assert.equal(remoteSecurity.preferences.contextIsolation, true);
  assert.equal(remoteSecurity.preferences.sandbox, true);

  await expect.poll(async () => (await getState(toolbar)).integratedContent).toBe(true);
  const controls = application.windows().find((page) => new URL(page.url()).searchParams.get('controls') === '1');
  assert.ok(controls, 'The compact trusted controls must exist');
  await expect(controls.getByRole('button', { name: '始终置顶', exact: true })).toBeVisible();
  await expect(controls.getByRole('button', { name: '更多操作', exact: true })).toBeVisible();
  assert.equal(await controls.locator('.toolbar button:visible').count(), 5, 'Refresh, opacity, settings, pin and more share the compact toolbar');
  const remotePage = application.windows().find((page) => page.url().startsWith(origin));
  assert.ok(remotePage);
  const height = () => application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].getBounds().height);
  await expect.poll(height).toBe(180);
  if (process.platform === 'darwin') assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].hasShadow()), false);
  await remotePage.locator('[data-sticker-root]').evaluate((root) => root.setAttribute('data-sticker-height', '900'));
  await expect.poll(height).toBeGreaterThan(180);
  assert.ok(await height() <= 560, 'Long content must stop growing at its cap');
  await remotePage.locator('[data-sticker-root]').evaluate((root) => root.setAttribute('data-sticker-height', '180'));
  await expect.poll(height).toBe(180);
  await remotePage.locator('[data-sticker-root]').evaluate((root) => root.setAttribute('data-sticker-overlay', 'true'));
  await expect.poll(height).toBeGreaterThanOrEqual(420);
  assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].contentView.children.find((view) => view.webContents?.getURL().includes('?controls=1')).getVisible()), false, 'Native controls must not cover web overlay close buttons');
  await remotePage.locator('[data-sticker-root]').evaluate((root) => root.removeAttribute('data-sticker-overlay'));
  await expect.poll(height).toBe(180);

  await expect.poll(() => application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].contentView.children.find((view) => view.webContents?.getURL().includes('?controls=1')).getVisible())).toBe(true);

  // A real native menu opens from the compact view. Intercept only the OS
  // presentation in this disposable test so its actions are deterministic.
  await application.evaluate(({ Menu, shell }) => {
    Menu.prototype.popup = function (options) {
      globalThis.__stickerSmokeMenu = this;
      options?.callback?.();
    };
    shell.openExternal = async (url) => { globalThis.__stickerSmokeExternal = url; };
  });
  await controls.getByRole('button', { name: '更多操作', exact: true }).click();
  const menuLabels = await application.evaluate(() => globalThis.__stickerSmokeMenu.items.map((item) => item.label));
  for (const pattern of [/刷新/, /背景不透明度/, /设置/, /在浏览器打开/]) {
    assert.ok(menuLabels.some((label) => pattern.test(label)), `Missing menu item: ${pattern}`);
  }
  await application.evaluate(() => globalThis.__stickerSmokeMenu.items.find((item) => /在浏览器打开/.test(item.label)).click());
  await expect.poll(() => application.evaluate(() => globalThis.__stickerSmokeExternal)).toBe(`${origin}/p/smoke-profile/projects`);

  // Login is a SPA transition: it must remain visible, without compact
  // controls over the form or a stale connection mask.
  await remotePage.evaluate(() => history.pushState({}, '', '/login'));
  await expect.poll(async () => (await getState(toolbar)).integratedContent).toBe(false);
  assert.equal((await getState(toolbar)).loading, false);
  assert.equal((await getState(toolbar)).error, null);
  await expect.poll(height).toBeGreaterThanOrEqual(420);
  await remotePage.evaluate(() => history.pushState({}, '', '/p/smoke-profile/mini?sticker=1'));
  await expect.poll(async () => (await getState(toolbar)).integratedContent).toBe(true);
  await expect.poll(height).toBe(180);

  await controls.locator('#pin-button').click();
  assert.equal((await getState(toolbar)).settings.alwaysOnTop, false);
  if (process.platform === 'darwin') {
    assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].isAlwaysOnTop()), false);
  }
  await controls.getByRole('button', { name: '更多操作', exact: true }).click();
  await application.evaluate(() => globalThis.__stickerSmokeMenu.items.find((item) => /设置/.test(item.label)).click());
  await expect(toolbar.getByRole('switch', { name: '始终置顶' })).not.toBeChecked();
  if (process.platform === 'darwin') assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].hasShadow()), true);
  await toolbar.locator('#settings-opacity-range').evaluate((input) => {
    input.value = '65';
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await expect.poll(async () => (await getState(toolbar)).settings.opacity).toBe(0.65);
  assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].getOpacity()), 1, 'Text must never use native whole-window transparency');
  const surface = await getState(toolbar);
  assert.equal(surface.effectiveOpacity, surface.nativeTransparency && !surface.reducedTransparency ? 0.65 : 1);
  await expect.poll(() => toolbar.locator('h1').first().evaluate((heading) => {
    for (let element = heading; element; element = element.parentElement) {
      if (getComputedStyle(element).opacity !== '1') return false;
    }
    return true;
  }), { message: 'Text must remain opaque after the short entry transition' }).toBe(true);
  await toolbar.locator('#profile').fill('unsaved-draft');
  await toolbar.getByRole('switch', { name: '始终置顶' }).check();
  await expect(toolbar.locator('#pin-button')).toHaveAttribute('aria-pressed', 'true');
  await expect(toolbar.locator('#profile')).toHaveValue('unsaved-draft');
  if (process.platform === 'darwin') {
    assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].isAlwaysOnTop()), true);
  }
  // An explicit setting must reject coercion and leave the last good state intact.
  assert.equal(await toolbar.evaluate(async () => {
    try { await window.nblaneSticker.invoke('set-pin', 'false'); return false; }
    catch { return true; }
  }), true);
  assert.equal((await getState(toolbar)).settings.alwaysOnTop, true);
  await toolbar.getByRole('switch', { name: '始终置顶' }).uncheck();
  await expect(toolbar.locator('#pin-button')).toHaveAttribute('aria-pressed', 'false');
  await expect(toolbar.locator('#profile')).toHaveValue('unsaved-draft');
  await toolbar.emulateMedia({ reducedMotion: 'reduce' });
  const motion = await toolbar.locator('#pin-button').evaluate((button) => ({
    transition: getComputedStyle(button).transitionDuration,
    settingsAnimation: getComputedStyle(document.getElementById('settings-screen')).animationName,
  }));
  assert.deepEqual(motion, { transition: '0s', settingsAnimation: 'none' });
  await toolbar.emulateMedia({ reducedMotion: 'no-preference' });
  await toolbar.locator('#cancel-settings').click();
  assert.equal((await getState(toolbar)).settings.profile, 'smoke-profile');
  await application.close();
  application = null;
  const saved = JSON.parse(await readFile(path.join(data, 'sticker-settings.json'), 'utf8'));
  assert.equal(saved.settings.opacity, 0.65);
  assert.equal(saved.settings.profile, 'smoke-profile');
  assert.equal(saved.settings.refreshIntervalSeconds, 30);
  assert.equal(saved.settings.alwaysOnTop, false);

  toolbar = await launch();
  await expect.poll(async () => (await getState(toolbar)).screen).toBe('content');
  assert.equal((await getState(toolbar)).settings.opacity, 0.65);
  assert.equal((await getState(toolbar)).settings.refreshIntervalSeconds, 30);
  assert.equal((await getState(toolbar)).settings.alwaysOnTop, false);
  await expect(toolbar.locator('#pin-button')).toHaveAttribute('aria-pressed', 'false');
  assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].getOpacity()), 1);
  await expect.poll(async () => (await getState(toolbar)).integratedContent).toBe(true);
  await expect.poll(() => application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].getBounds().height)).toBe(180);
  if (process.platform === 'darwin') {
    assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].isAlwaysOnTop()), false);
  }

  async function connectProfile(profile) {
    await toolbar.evaluate((value) => window.nblaneSticker.invoke('save-settings', value), {
      serverUrl: origin, profile, launchAtLogin: false,
    });
  }
  // An optional image must not hide an otherwise interactive page.
  await connectProfile('slow-image');
  await expect.poll(async () => (await getState(toolbar)).loading).toBe(false);
  assert.equal((await getState(toolbar)).error, null);
  assert.equal(await application.evaluate(({ BrowserWindow }, expectedOrigin) => BrowserWindow.getAllWindows()[0].contentView.children.find((view) => view.webContents?.getURL().startsWith(expectedOrigin)).getVisible(), origin), true);
  assert.ok(pendingResponses.size > 0, 'The image request must still be pending');

  await connectProfile('blocked-redirect');
  await expect.poll(async () => Boolean((await getState(toolbar)).error)).toBe(true);
  assert.equal((await getState(toolbar)).loading, false);
  await expect(toolbar.locator('#status-settings-button')).toBeVisible();

  // A server that never sends headers must time out, then allow a clean retry.
  await connectProfile('no-response');
  await expect.poll(async () => Boolean((await getState(toolbar)).error), { timeout: 25_000 }).toBe(true);
  assert.equal((await getState(toolbar)).loading, false);
  await expect(toolbar.locator('#retry-button')).toBeVisible();
  await connectProfile('smoke-profile');
  await expect.poll(async () => (await getState(toolbar)).loading).toBe(false);
  assert.equal((await getState(toolbar)).error, null);
  // Connection errors must leave the trusted controls usable.
  await new Promise((resolve) => server.close(resolve));
  await toolbar.evaluate(() => window.nblaneSticker.invoke('retry'));
  await expect.poll(async () => Boolean((await getState(toolbar)).error)).toBe(true);
  await expect(toolbar.locator('#status-settings-button')).toBeVisible();
  await toolbar.locator('#status-settings-button').click();
  await expect(toolbar.locator('#settings-screen')).toBeVisible();
  console.log('Desktop smoke passed: merged toolbar/menu, adaptive height, background-only opacity, SPA login navigation, pending resources, redirects, timeout recovery, remote isolation, pin persistence and reduced motion.');
} finally {
  if (application) await application.close().catch(() => {});
  for (const response of pendingResponses) response.destroy();
  server.close();
  await rm(data, { recursive: true, force: true });
}
