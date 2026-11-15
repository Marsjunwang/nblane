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
  response.end('<!doctype html><title>Isolated sticker fixture</title><p>任务测试页面</p>'
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
        return url.protocol === 'file:' && url.pathname.endsWith('/renderer/index.html');
      } catch {
        return false;
      }
    });
    return Boolean(toolbar);
  }, { message: 'The local sticker toolbar must load', timeout: 30_000 }).toBe(true);
  await expect(toolbar.locator('#toolbar-default')).toBeVisible();
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

  // Login is a SPA transition: it must not cover the ready page with a spinner.
  await application.evaluate(async ({ webContents }, expectedOrigin) => {
    const contents = webContents.getAllWebContents().find((item) => item.getURL().startsWith(expectedOrigin));
    await contents.executeJavaScript("history.pushState({}, '', '/login');");
  }, origin);
  await new Promise((resolve) => setTimeout(resolve, 250));
  assert.equal((await getState(toolbar)).loading, false, 'SPA navigation must leave the login page visible');
  assert.equal((await getState(toolbar)).error, null);
  assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].contentView.children[0].getVisible()), true);

  await toolbar.locator('#opacity-button').click();
  await toolbar.locator('#toolbar-opacity-range').evaluate((input) => {
    input.value = '65';
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await expect.poll(async () => (await getState(toolbar)).settings.opacity).toBe(0.65);
  if (process.platform === 'darwin') {
    assert.ok(Math.abs(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].getOpacity()) - 0.65) < 0.01);
  }
  await toolbar.locator('#opacity-close').click();
  await toolbar.locator('#pin-button').click();
  assert.equal((await getState(toolbar)).settings.alwaysOnTop, false);
  await expect(toolbar.locator('#pin-label')).toHaveText('置顶');
  if (process.platform === 'darwin') {
    assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].isAlwaysOnTop()), false);
  }
  await toolbar.locator('#settings-button').click();
  await expect(toolbar.getByRole('switch', { name: '始终置顶' })).not.toBeChecked();
  await toolbar.locator('#profile').fill('unsaved-draft');
  await toolbar.getByRole('switch', { name: '始终置顶' }).check();
  await expect(toolbar.locator('#pin-label')).toHaveText('已置顶');
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
  assert.equal(saved.settings.alwaysOnTop, false);

  toolbar = await launch();
  await expect.poll(async () => (await getState(toolbar)).screen).toBe('content');
  assert.equal((await getState(toolbar)).settings.opacity, 0.65);
  assert.equal((await getState(toolbar)).settings.alwaysOnTop, false);
  await expect(toolbar.locator('#pin-button')).toHaveAttribute('aria-pressed', 'false');
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
  assert.equal(await application.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].contentView.children[0].getVisible()), true);
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
  console.log('Desktop smoke passed: SPA login navigation, pending resources, redirects, timeout recovery, remote isolation, opacity, always-on-top controls/persistence and reduced motion.');
} finally {
  if (application) await application.close().catch(() => {});
  for (const response of pendingResponses) response.destroy();
  server.close();
  await rm(data, { recursive: true, force: true });
}
