import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { _electron, expect as baseExpect } from '@playwright/test';
import { startMiniFixture } from './mini-fixture.mjs';

const expect = baseExpect.configure({ timeout: 15_000 });
const desktop = fileURLToPath(new URL('../', import.meta.url));
if (process.platform !== 'darwin') throw new Error('Compositor smoke requires a real macOS desktop.');
const options = process.argv.slice(2);
if (options.length > 1 || (options.length === 1 && !options[0].startsWith('--app='))) {
  throw new Error('Usage: node desktop/smoke/material.mjs [--app=/absolute/path/to/App.app]');
}
const packagedApp = options[0]?.slice('--app='.length);
let executablePath = path.join(desktop, 'node_modules/.bin/electron');
if (packagedApp !== undefined) {
  assert.ok(path.isAbsolute(packagedApp) && packagedApp.endsWith('.app'));
  const executable = execFileSync('/usr/libexec/PlistBuddy', [
    '-c', 'Print :CFBundleExecutable', path.join(packagedApp, 'Contents/Info.plist'),
  ], { encoding: 'utf8' }).trim();
  assert.ok(executable && path.basename(executable) === executable);
  executablePath = path.join(packagedApp, 'Contents/MacOS', executable);
}
const data = await mkdtemp(path.join(tmpdir(), 'nblane-material-smoke-'));
const fixture = await startMiniFixture();
fixture.state.signedIn = true;
let application;
let toolbar;
let remote;
const deadline = setTimeout(() => {
  application?.process().kill('SIGKILL');
  fixture.server.closeAllConnections();
}, 180_000);
const evidenceDirectory = process.env.NBLANE_STICKER_SCREENSHOT_DIR;
const nativeHelper = path.join(data, 'native-material');
const getState = () => toolbar.evaluate(() => window.nblaneSticker.invoke('get-state'));
const bounds = () => application.evaluate(({ BrowserWindow }) =>
  BrowserWindow.fromId(globalThis.__materialStickerId).getContentBounds());
const command = (...args) => execFileSync(nativeHelper, args, { timeout: 10_000, stdio: 'pipe' });

async function setOpacity(opacity) {
  await toolbar.evaluate((value) => window.nblaneSticker.invoke('set-opacity', value), opacity);
  await expect.poll(async () => (await getState()).effectiveOpacity).toBe(opacity);
  assert.equal(await application.evaluate(({ BrowserWindow }) =>
    BrowserWindow.fromId(globalThis.__materialStickerId).getOpacity()), 1);
}

async function setBackdrop(color) {
  await application.evaluate(async (_, background) => {
    globalThis.__materialBackdrop.setBackgroundColor(background);
    await globalThis.__materialBackdrop.webContents.executeJavaScript(
      `document.body.style.backgroundColor = ${JSON.stringify(background)}`);
  }, color);
  // Wait for native composition, not only DOM mutation acknowledgement.
  await new Promise((resolve) => setTimeout(resolve, 300));
}

async function capture(name, titleRect) {
  const rectangle = await bounds();
  const filename = path.join(data, `${name}.png`);
  // Capture only the fixture-covered rectangle through WindowServer. Renderer
  // capturePage/screenshot cannot establish translucency over another window.
  execFileSync('/usr/sbin/screencapture', ['-x', '-R',
    `${rectangle.x},${rectangle.y},${rectangle.width},${rectangle.height}`, filename],
  { timeout: 15_000, stdio: 'pipe' });
  const pixels = await application.evaluate(({ nativeImage }, { filename, rectangle, titleRect }) => {
    const image = nativeImage.createFromPath(filename);
    if (image.isEmpty()) throw new Error('WindowServer capture was empty');
    const size = image.getSize();
    const bytes = image.toBitmap();
    const scaleX = size.width / rectangle.width;
    const scaleY = size.height / rectangle.height;
    const rgb = (x, y) => {
      const offset = (Math.floor(y * scaleY) * size.width + Math.floor(x * scaleX)) * 4;
      return [bytes[offset + 2], bytes[offset + 1], bytes[offset]];
    };
    const surface = rgb(30, rectangle.height - 10);
    const glyphs = [];
    for (let y = Math.ceil(titleRect.y); y < Math.floor(titleRect.y + titleRect.height); y += 1) {
      for (let x = Math.ceil(titleRect.x); x < Math.floor(titleRect.x + titleRect.width); x += 1) {
        glyphs.push(rgb(x, y));
      }
    }
    return { surface, glyphs };
  }, { filename, rectangle, titleRect });
  if (evidenceDirectory) {
    await mkdir(evidenceDirectory, { recursive: true });
    const { copyFile } = await import('node:fs/promises');
    await copyFile(filename, path.join(evidenceDirectory, `${name}.png`));
  }
  return pixels;
}

const maximumDifference = (left, right) => Math.max(...left.map((channel, index) => Math.abs(channel - right[index])));
const distance = (left, right) => left.reduce((total, channel, index) => total + Math.abs(channel - right[index]), 0) / 3;

try {
  execFileSync('/usr/bin/xcrun', ['swiftc', path.join(desktop, 'smoke/native-material.swift'),
    '-module-cache-path', path.join(data, 'swift-cache'), '-o', nativeHelper],
  { timeout: 60_000, stdio: 'pipe' });
  command('capture-access');
  await writeFile(path.join(data, 'sticker-settings.json'), JSON.stringify({
    settings: { serverUrl: fixture.origin, profile: 'demo', opacity: 0.4,
      backgroundBlur: false, alwaysOnTop: true, launchAtLogin: false },
    bounds: { x: 120, y: 120, width: 360, height: 220 },
  }));
  application = await _electron.launch({ executablePath,
    args: packagedApp === undefined ? [desktop] : [],
    env: { ...process.env, NBLANE_STICKER_USER_DATA: data }, timeout: 30_000 });
  await expect.poll(() => {
    toolbar = application.windows().find((page) => page.url().startsWith('file:') && !new URL(page.url()).search);
    remote = application.windows().find((page) => page.url().startsWith(fixture.origin));
    return Boolean(toolbar && remote);
  }).toBe(true);
  await expect(remote.locator('.mini-task-title').first()).toBeVisible();
  await expect.poll(async () => (await getState()).integratedContent).toBe(true);
  assert.equal((await getState()).reducedTransparency, false, 'CI must allow transparency for the compositor test');
  assert.equal((await getState()).nativeBlur, false);
  await application.evaluate(async ({ BrowserWindow, screen }) => {
    const sticker = BrowserWindow.getAllWindows()[0];
    globalThis.__materialStickerId = sticker.id;
    const area = screen.getPrimaryDisplay().workArea;
    sticker.setPosition(area.x + 120, area.y + 100);
    const rectangle = sticker.getBounds();
    const backdrop = new BrowserWindow({
      x: rectangle.x - 40, y: rectangle.y - 40,
      width: rectangle.width + 160, height: rectangle.height + 120,
      frame: false, show: false, backgroundColor: '#ffffff',
      webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false },
    });
    globalThis.__materialBackdrop = backdrop;
    await backdrop.loadURL('data:text/html,<body style="margin:0;background:white"></body>');
    backdrop.showInactive();
    sticker.moveTop();
    sticker.focus();
  });
  const titleRect = await remote.locator('.mini-task-title').first().evaluate((element) => {
    const rectangle = element.getBoundingClientRect();
    return { x: rectangle.x, y: rectangle.y, width: rectangle.width, height: rectangle.height };
  });
  const captures = new Map();
  for (const opacity of [1, 0.4, 0.1]) {
    await setOpacity(opacity);
    for (const [name, color] of [['light', '#ffffff'], ['dark', '#000000']]) {
      await setBackdrop(color);
      captures.set(`${opacity}-${name}`, await capture(`material-${Math.round(opacity * 100)}-${name}`, titleRect));
    }
  }
  const opaque = captures.get('1-light');
  assert.ok(maximumDifference(opaque.surface, captures.get('1-dark').surface) <= 4,
    '100% tint must hide the backing window');
  const contrast40 = distance(captures.get('0.4-light').surface, captures.get('0.4-dark').surface);
  const contrast10 = distance(captures.get('0.1-light').surface, captures.get('0.1-dark').surface);
  assert.ok(contrast40 > 80, `40% tint must visibly transmit the backing window, measured contrast ${contrast40}`);
  assert.ok(contrast10 > 170 && contrast10 > contrast40 + 25,
    `10% tint must expose substantially more background, measured contrast ${contrast10} versus ${contrast40}`);
  const moonwhite = [242, 237, 224];
  const glyphMask = opaque.glyphs.flatMap((pixel, index) => maximumDifference(pixel, moonwhite) <= 10 ? [index] : []);
  assert.ok(glyphMask.length >= 8, 'The native capture must contain opaque task glyphs');
  for (const capture of captures.values()) {
    const stable = glyphMask.filter((index) => maximumDifference(capture.glyphs[index], opaque.glyphs[index]) <= 10);
    assert.ok(stable.length / glyphMask.length >= 0.85, 'Task glyphs must remain opaque over light and dark backdrops');
  }

  await toolbar.evaluate(() => window.nblaneSticker.invoke('set-background-blur', true));
  await expect.poll(async () => (await getState()).nativeBlur).toBe(true);
  // Give the native effect view a composition frame before removing it again.
  await new Promise((resolve) => setTimeout(resolve, 300));
  await toolbar.evaluate(() => window.nblaneSticker.invoke('set-background-blur', false));
  await expect.poll(async () => (await getState()).nativeBlur).toBe(false);
  await setOpacity(0.1);
  const restored = new Map();
  for (const [name, color] of [['light', '#ffffff'], ['dark', '#000000']]) {
    await setBackdrop(color);
    const pixels = await capture(`material-10-blur-disabled-${name}`, titleRect);
    restored.set(name, pixels);
    assert.ok(maximumDifference(pixels.surface, captures.get(`0.1-${name}`).surface) <= 10,
      'Disabling blur must restore the clear surface without a lingering material tint');
    const stable = glyphMask.filter((index) => maximumDifference(pixels.glyphs[index], opaque.glyphs[index]) <= 10);
    assert.ok(stable.length / glyphMask.length >= 0.85,
      'Task glyphs must remain opaque after toggling background blur');
  }
  const restoredContrast10 = distance(restored.get('light').surface, restored.get('dark').surface);
  assert.ok(restoredContrast10 > 170,
    `Disabling blur must restore background transmission, measured contrast ${restoredContrast10}`);

  const before = await bounds();
  assert.equal(await application.evaluate(({ BrowserWindow }) =>
    BrowserWindow.fromId(globalThis.__materialStickerId).isResizable()), true);
  command('drag', String(before.x + before.width - 1), String(before.y + Math.round(before.height / 2)),
    String(before.x + before.width + 47), String(before.y + Math.round(before.height / 2)));
  await expect.poll(async () => (await bounds()).width, { message: 'Transparent Mac window must resize using its native edge' })
    .toBeGreaterThan(before.width + 20);
  await setBackdrop('#ffffff');
  const resized = await capture('material-10-resized', titleRect);
  assert.ok(resized.surface.every((channel) => channel > 170), 'Native resizing must preserve the translucent surface');
  console.log(JSON.stringify({ verification: 'macOS WindowServer compositor + native edge resize',
    contrast40, contrast10, restoredContrast10, opaqueGlyphPixels: glyphMask.length,
    widthBefore: before.width, widthAfter: (await bounds()).width }));
} finally {
  clearTimeout(deadline);
  if (application) {
    await application.evaluate(() => globalThis.__materialBackdrop?.destroy()).catch(() => {});
    await application.close().catch(() => {});
  }
  await fixture.close();
  await rm(data, { recursive: true, force: true });
}
